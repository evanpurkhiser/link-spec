#!/usr/bin/env python3
"""Replay canonical Rekordbox expectations against the rbxport backend."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import json
import platform
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import IO

import conformance_backend
from replay_catalog import *  # noqa: F403


ROOT = Path(__file__).resolve().parent
RESEARCH = ROOT.parent
WORKSPACE = RESEARCH.parent
DEFAULT_RBXPORT = WORKSPACE.parent / "rbxport"
DEFAULT_OPTIONS = Path("/mnt/documents/multimedia/djing/rekordbox/options.json")
DEFAULT_SERVER_BINARY = DEFAULT_RBXPORT / "target/debug/rbl-conformance-server"
RELEVANT_RBXPORT_PATHS = (
    "Cargo.toml",
    "Cargo.lock",
    "crates/rbl-anlz",
    "crates/rbl-core",
    "crates/rbl-db",
    "crates/rbl-dbserver",
    "crates/rbl-index",
    "crates/rbl-link",
    "crates/rbl-nfs",
    "crates/rbl-prolink",
)
LAB_SOURCE_PATHS = (
    "conformance_backend.py",
    "protocol_runner.py",
    "remote_db.py",
    "replay_catalog.py",
    "replay_rbxport.py",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--enable-rbxport-replay",
        action="store_true",
        help="explicitly opt into the backend comparison",
    )
    parser.add_argument("--rbxport", type=Path, default=DEFAULT_RBXPORT)
    parser.add_argument("--server-binary", type=Path, default=DEFAULT_SERVER_BINARY)
    parser.add_argument("--options", type=Path, default=DEFAULT_OPTIONS)
    parser.add_argument("--result-root", type=Path)
    parser.add_argument("--no-build", action="store_true")
    parser.add_argument(
        "--suite",
        action="append",
        default=[],
        metavar="[MODEL/]SUITE",
        help="replay only a named suite; may be repeated",
    )
    return parser.parse_args()


def require_deferred_phase_opt_in(enabled: bool) -> None:
    if enabled:
        return

    raise SystemExit(
        "rbxport replay requires an explicit opt-in; pass "
        "--enable-rbxport-replay when intentionally comparing the backend"
    )


def git(rbxport: Path, *arguments: str) -> str:
    command = [
        "git",
        "-c",
        "core.fsmonitor=false",
        "-C",
        str(rbxport),
        *arguments,
    ]
    return subprocess.check_output(command, text=True).strip()


def source_provenance(rbxport: Path, server_binary: Path) -> dict[str, object]:
    listed = git(
        rbxport,
        "ls-files",
        "-co",
        "--exclude-standard",
        "--",
        *RELEVANT_RBXPORT_PATHS,
    ).splitlines()
    entries = []
    aggregate = hashlib.sha256()
    for relative in sorted(set(listed)):
        path = rbxport / relative
        if not path.is_file():
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        entries.append({"path": relative, "sha256": digest, "bytes": path.stat().st_size})
        aggregate.update(relative.encode())
        aggregate.update(b"\0")
        aggregate.update(digest.encode())
        aggregate.update(b"\n")

    lab_entries = []
    lab_aggregate = hashlib.sha256()
    for relative in LAB_SOURCE_PATHS:
        path = ROOT / relative
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        lab_entries.append({"path": relative, "sha256": digest, "bytes": path.stat().st_size})
        lab_aggregate.update(relative.encode())
        lab_aggregate.update(b"\0")
        lab_aggregate.update(digest.encode())
        lab_aggregate.update(b"\n")

    return {
        "repository": str(rbxport.resolve()),
        "commit": git(rbxport, "rev-parse", "HEAD"),
        "commit_short": git(rbxport, "rev-parse", "--short", "HEAD"),
        "branch": git(rbxport, "rev-parse", "--abbrev-ref", "HEAD"),
        "dirty": bool(git(rbxport, "status", "--short", "--", *RELEVANT_RBXPORT_PATHS)),
        "recorded_unix_seconds": int(time.time()),
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "server_binary": str(server_binary),
        "server_binary_sha256": hashlib.sha256(server_binary.read_bytes()).hexdigest(),
        "scope": list(RELEVANT_RBXPORT_PATHS),
        "tree_sha256": aggregate.hexdigest(),
        "files": entries,
        "lab_tree_sha256": lab_aggregate.hexdigest(),
        "lab_files": lab_entries,
    }


def drain(process: subprocess.Popen[str], log: IO[str], first_line: str) -> None:
    log.write(first_line)
    log.flush()
    assert process.stdout is not None
    for line in process.stdout:
        log.write(line)
        log.flush()


def start_server(
    server_binary: Path,
    fixture: str,
    second_column: str,
    sorts: str | None,
    options: Path,
    result_root: Path,
) -> tuple[subprocess.Popen[str], IO[str], threading.Thread, int]:
    share = result_root / "share"
    share.mkdir(parents=True, exist_ok=True)
    log = (result_root / f"server-{fixture}.log").open("w")
    command = [
        str(server_binary),
        "--options",
        str(options),
        "--database",
        str(ROOT / f"fixtures/generated/{fixture}/master.db"),
        "--share-root",
        str(share),
        "--second-column",
        second_column,
        "--query-port",
        "0",
        "--alphabetical-keys",
    ]
    if sorts is not None:
        command.extend(("--sorts", sorts))
    process = subprocess.Popen(
        command,
        cwd=RESEARCH,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    assert process.stdout is not None
    first_line = process.stdout.readline()
    if not first_line:
        raise RuntimeError(f"rbxport server exited before readiness: {process.wait()}")
    try:
        ready = json.loads(first_line)
    except json.JSONDecodeError as error:
        raise RuntimeError(f"rbxport server produced invalid readiness: {first_line!r}") from error
    if ready.get("status") != "ready" or ready.get("listen_address") != "127.0.0.1":
        raise RuntimeError(f"unsafe or incomplete rbxport readiness: {ready}")

    thread = threading.Thread(target=drain, args=(process, log, first_line), daemon=True)
    thread.start()
    return process, log, thread, int(ready["query_port"])


def stop_server(
    process: subprocess.Popen[str],
    log: IO[str],
    thread: threading.Thread,
) -> None:
    if process.poll() is None:
        process.send_signal(signal.SIGTERM)
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
    thread.join(timeout=2)
    log.close()


class RbxportAdapter:
    name = "rbxport"
    reuse_server_across_suites = True

    def __init__(self, repository: Path, options: Path, server_binary: Path) -> None:
        self.repository = repository
        self.options = options
        self.server_binary = server_binary

    def prepare(self) -> None:
        if not self.server_binary.is_file():
            raise RuntimeError(
                "rbxport must provide its conformance server executable at "
                f"{self.server_binary}; override it with --server-binary"
            )

    def source_provenance(self) -> dict[str, object]:
        return source_provenance(self.repository, self.server_binary)

    def version(self, provenance: dict[str, object]) -> str:
        return (
            f"{provenance['commit_short']}+"
            f"tree.{str(provenance['tree_sha256'])[:12]}"
        )

    @contextmanager
    def server(
        self,
        fixture: str,
        second_column: str,
        sorts: str | None,
        result_root: Path,
    ):
        process, log, thread, query_port = start_server(
            self.server_binary,
            fixture,
            second_column,
            sorts,
            self.options,
            result_root,
        )
        try:
            yield query_port
        finally:
            stop_server(process, log, thread)

    def summary_notes(self) -> tuple[str, ...]:
        return (
            "Each replay uses the secondary column and visible sort order recorded by its",
            "fixture. The no-selection replay uses Comment as a runnable rbxport control",
            "because rbxport does not yet represent an absent secondary column.",
        )


def main() -> None:
    args = parse_args()
    require_deferred_phase_opt_in(args.enable_rbxport_replay)
    rbxport = args.rbxport.resolve()
    server_binary = args.server_binary.resolve()
    options = args.options.resolve()
    if not options.is_file():
        raise SystemExit(f"options file does not exist: {options}")
    replays = select_replays(REPLAYS, args.suite)
    result_root = conformance_backend.run(
        RbxportAdapter(rbxport, options, server_binary),
        replays,
        args.result_root,
        args.no_build,
    )
    print(result_root)


if __name__ == "__main__":
    main()
