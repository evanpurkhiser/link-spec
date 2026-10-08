#!/usr/bin/env python3
"""Replay canonical Rekordbox expectations against the Vynull backend."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import signal
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path

import conformance_backend
from replay_catalog import REPLAYS, Replay, select_replays


ROOT = Path(__file__).resolve().parent
RESEARCH = ROOT.parent
WORKSPACE = RESEARCH.parent
DEFAULT_VYNULL = WORKSPACE / "vynull"
DEFAULT_OPTIONS = Path("/mnt/documents/multimedia/djing/rekordbox/options.json")
DEFAULT_PYTHON = WORKSPACE / "rekordbox-windows/.venv/bin/python"
HARNESS_BINARY = ROOT / "runtime/vynull/vynull-conformance-server"
VYNULL_SOURCE_PATHS = (
    "go.mod",
    "go.sum",
    "api",
    "dbserver",
    "device",
    "library",
    "proto",
    "cmd/conformance-server",
    "tools/rekordbox_dump.py",
)
LAB_SOURCE_PATHS = (
    "conformance_backend.py",
    "protocol_runner.py",
    "remote_db.py",
    "replay_catalog.py",
    "replay_rbxport.py",
    "replay_vynull.py",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--enable-vynull-replay",
        action="store_true",
        help="explicitly opt into the backend comparison",
    )
    parser.add_argument("--vynull", type=Path, default=DEFAULT_VYNULL)
    parser.add_argument("--options", type=Path, default=DEFAULT_OPTIONS)
    parser.add_argument("--python", type=Path, default=DEFAULT_PYTHON)
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


def require_opt_in(enabled: bool) -> None:
    if enabled:
        return
    raise SystemExit(
        "Vynull replay requires an explicit opt-in; pass "
        "--enable-vynull-replay when intentionally comparing the backend"
    )


def git(repository: Path, *arguments: str) -> str:
    command = [
        "git",
        "-c",
        "core.fsmonitor=false",
        "-C",
        str(repository),
        *arguments,
    ]
    return subprocess.check_output(command, text=True).strip()


def hash_paths(
    root: Path, paths: tuple[str, ...], *, tracked: bool
) -> tuple[str, list[dict[str, object]]]:
    if tracked:
        listed = git(
            root,
            "ls-files",
            "-co",
            "--exclude-standard",
            "--",
            *paths,
        ).splitlines()
    else:
        listed = list(paths)

    entries: list[dict[str, object]] = []
    aggregate = hashlib.sha256()
    for relative in sorted(set(listed)):
        path = root / relative
        if not path.is_file():
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        entries.append({"path": relative, "sha256": digest, "bytes": path.stat().st_size})
        aggregate.update(relative.encode())
        aggregate.update(b"\0")
        aggregate.update(digest.encode())
        aggregate.update(b"\n")
    return aggregate.hexdigest(), entries


class VynullAdapter:
    name = "vynull"
    reuse_server_across_suites = False

    def __init__(self, repository: Path, options: Path, python: Path) -> None:
        self.repository = repository
        self.options = options
        self.python = python
        self.server_number = 0

    def prepare(self) -> None:
        HARNESS_BINARY.parent.mkdir(parents=True, exist_ok=True)
        environment = os.environ.copy()
        environment["GOCACHE"] = str(HARNESS_BINARY.parent / "go-build")
        subprocess.run(
            [
                "go",
                "build",
                "-buildvcs=false",
                "-o",
                str(HARNESS_BINARY),
                "./cmd/conformance-server",
            ],
            cwd=self.repository,
            env=environment,
            check=True,
        )

    def source_provenance(self) -> dict[str, object]:
        tree_hash, files = hash_paths(self.repository, VYNULL_SOURCE_PATHS, tracked=True)
        lab_hash, lab_files = hash_paths(ROOT, LAB_SOURCE_PATHS, tracked=False)
        return {
            "repository": str(self.repository.resolve()),
            "commit": git(self.repository, "rev-parse", "HEAD"),
            "commit_short": git(self.repository, "rev-parse", "--short", "HEAD"),
            "branch": git(self.repository, "rev-parse", "--abbrev-ref", "HEAD"),
            "dirty": bool(
                git(self.repository, "status", "--short", "--", *VYNULL_SOURCE_PATHS)
            ),
            "recorded_unix_seconds": int(time.time()),
            "platform": platform.platform(),
            "python": sys.version.split()[0],
            "go": subprocess.check_output(["go", "version"], text=True).strip(),
            "scope": list(VYNULL_SOURCE_PATHS),
            "tree_sha256": tree_hash,
            "files": files,
            "lab_tree_sha256": lab_hash,
            "lab_files": lab_files,
        }

    def version(self, provenance: dict[str, object]) -> str:
        return (
            f"{provenance['commit_short']}+"
            f"tree.{str(provenance['tree_sha256'])[:12]}"
        )

    def fixture_dump(self, fixture: str, result_root: Path) -> Path:
        destination = result_root / "fixtures" / f"{fixture}.json"
        if destination.is_file() and destination.stat().st_size > 0:
            return destination
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(".json.tmp")
        database = ROOT / f"fixtures/generated/{fixture}/master.db"
        environment = os.environ.copy()
        environment["VYNULL_REKORDBOX_KEY"] = subprocess.check_output(
            [
                str(self.python),
                "-c",
                (
                    "import sys; sys.path.insert(0, sys.argv[1]); "
                    "from build_fixture import key_from_options; "
                    "print(key_from_options(__import__('pathlib').Path(sys.argv[2])))"
                ),
                str(ROOT),
                str(self.options),
            ],
            text=True,
        ).strip()
        try:
            with temporary.open("w") as output:
                subprocess.run(
                    [
                        str(self.python),
                        str(self.repository / "tools/rekordbox_dump.py"),
                        str(database),
                    ],
                    env=environment,
                    stdout=output,
                    check=True,
                    text=True,
                )
            temporary.replace(destination)
        finally:
            temporary.unlink(missing_ok=True)
        return destination

    @contextmanager
    def server(
        self,
        fixture: str,
        second_column: str,
        sorts: str | None,
        result_root: Path,
    ):
        dump = self.fixture_dump(fixture, result_root)
        self.server_number += 1
        group_id = hashlib.sha256(
            json.dumps(
                [self.server_number, fixture, second_column, sorts]
            ).encode()
        ).hexdigest()[:12]
        runtime = result_root / "runtime" / group_id
        runtime.mkdir(parents=True, exist_ok=True)
        log = (result_root / f"server-{fixture}-{group_id}.log").open("w")
        process = subprocess.Popen(
            [
                str(HARNESS_BINARY),
                "--fixture-json",
                str(dump),
                "--data-dir",
                str(runtime),
                "--second-column",
                second_column,
            ],
            cwd=self.repository,
            stdout=subprocess.PIPE,
            stderr=log,
            text=True,
            bufsize=1,
        )
        assert process.stdout is not None
        first_line = process.stdout.readline()
        if not first_line:
            log.close()
            raise RuntimeError(
                f"Vynull server exited before readiness: {process.wait()}"
            )
        try:
            ready = json.loads(first_line)
        except json.JSONDecodeError as error:
            process.terminate()
            process.wait(timeout=5)
            log.close()
            raise RuntimeError(
                f"Vynull server produced invalid readiness: {first_line!r}"
            ) from error
        if ready.get("status") != "ready" or ready.get("listen_address") != "127.0.0.1":
            process.terminate()
            process.wait(timeout=5)
            log.close()
            raise RuntimeError(f"unsafe or incomplete Vynull readiness: {ready}")
        try:
            yield int(ready["query_port"])
        finally:
            if process.poll() is None:
                process.send_signal(signal.SIGTERM)
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
            process.stdout.close()
            log.close()

    def summary_notes(self) -> tuple[str, ...]:
        return (
            "Each replay uses the canonical fixture IDs and the configured secondary column.",
            "Vynull selects and orders supported sorts from each request; fixture-level sort",
            "visibility is recorded in the report but is not a Vynull configuration surface.",
        )


def main() -> None:
    args = parse_args()
    require_opt_in(args.enable_vynull_replay)
    repository = args.vynull.resolve()
    options = args.options.resolve()
    python = args.python.expanduser().absolute()
    required_paths = (
        (repository, "Vynull repository"),
        (options, "options file"),
        (python, "Python interpreter"),
    )
    for path, label in required_paths:
        if not path.exists():
            raise SystemExit(f"{label} does not exist: {path}")

    replays: tuple[Replay, ...] = select_replays(REPLAYS, args.suite)
    result_root = conformance_backend.run(
        VynullAdapter(repository, options, python),
        replays,
        args.result_root,
        args.no_build,
    )
    print(result_root)


if __name__ == "__main__":
    main()
