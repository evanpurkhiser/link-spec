#!/usr/bin/env python3
"""Backend-neutral runner for the Rekordbox Link Export golden corpus."""

from __future__ import annotations

import json
import subprocess
import sys
from contextlib import AbstractContextManager
from pathlib import Path
from typing import Any, Mapping, Protocol, Sequence


ROOT = Path(__file__).resolve().parent
RESEARCH = ROOT.parent
DEFAULT_SORTS = (
    "default",
    "track-name",
    "artist",
    "album",
    "bpm",
    "rating",
    "key",
    "label",
    "genre",
    "date-added",
    "dj-play-count",
)


class ReplaySpec(Protocol):
    model: str
    identity: str
    suite: str
    fixture: str
    suite_path: str | None
    second_column: str
    sorts: str | None


class BackendAdapter(Protocol):
    """Owns only the lifecycle and fixture translation for one backend."""

    name: str
    reuse_server_across_suites: bool

    def prepare(self) -> None: ...

    def source_provenance(self) -> dict[str, object]: ...

    def version(self, provenance: Mapping[str, object]) -> str: ...

    def server(
        self,
        fixture: str,
        second_column: str,
        sorts: str | None,
        result_root: Path,
    ) -> AbstractContextManager[int]: ...

    def summary_notes(self) -> Sequence[str]: ...


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def verify_replay(
    adapter: BackendAdapter,
    replay: ReplaySpec,
    version: str,
    result_root: Path,
    query_port: int,
) -> str | None:
    destination = result_root / replay.model
    destination.mkdir(parents=True, exist_ok=True)
    actual = destination / f"{replay.suite}.actual.json"
    diff = destination / f"{replay.suite}.diff.txt"
    golden = ROOT / f"goldens/rekordbox-7.2.19/{replay.model}/{replay.suite}.json"
    command = [
        sys.executable,
        str(ROOT / "protocol_runner.py"),
        "verify",
        "--host",
        "127.0.0.1",
        "--query-port",
        str(query_port),
        "--suite",
        str(ROOT / f"suites/{replay.suite_path or replay.suite}.json"),
        "--manifest",
        str(ROOT / f"fixtures/generated/{replay.fixture}/manifest.json"),
        "--golden",
        str(golden),
        "--backend",
        adapter.name,
        "--backend-version",
        version,
        "--identity",
        str(ROOT / f"runs/{replay.identity}"),
        "--expectations",
        "compare",
        "--actual",
        str(actual),
        "--diff",
        str(diff),
    ]
    completed = subprocess.run(command, cwd=RESEARCH, text=True, capture_output=True)
    (destination / f"{replay.suite}.run.log").write_text(
        completed.stdout + completed.stderr
    )
    expected_mismatch = (
        completed.returncode == 1 and "conformance mismatch" in completed.stderr
    )
    if completed.returncode == 0 or (expected_mismatch and actual.is_file()):
        return None

    output = (completed.stderr or completed.stdout).strip().splitlines()
    detail = output[-1] if output else "no diagnostic output"
    return f"exit {completed.returncode}: {detail}"


def case_shape(case: dict[str, object]) -> tuple[object, object, int]:
    rows = case.get("rows")
    return case.get("outcome"), case.get("total"), len(rows) if isinstance(rows, list) else 0


def aggregate_suites(suites: Sequence[Mapping[str, Any]]) -> dict[str, int | float]:
    cases = sum(int(suite["cases"]) for suite in suites)
    exact_cases = sum(len(suite["exact_cases"]) for suite in suites)
    same_shape_cases = sum(
        len(suite["same_outcome_total_row_count_cases"]) for suite in suites
    )
    return {
        "suites": len(suites),
        "completed_suites": sum(suite["run_error"] is None for suite in suites),
        "errored_suites": sum(suite["run_error"] is not None for suite in suites),
        "exact_suites": sum(bool(suite["behavior_matches"]) for suite in suites),
        "cases": cases,
        "exact_cases": exact_cases,
        "same_outcome_total_row_count_cases": same_shape_cases,
        "exact_case_rate": exact_cases / cases if cases else 0.0,
        "same_outcome_total_row_count_rate": same_shape_cases / cases if cases else 0.0,
    }


def summarize(
    adapter: BackendAdapter,
    result_root: Path,
    provenance: Mapping[str, object],
    version: str,
    run_errors: Mapping[tuple[str, str], str],
    replays: Sequence[ReplaySpec],
) -> None:
    suites: list[dict[str, Any]] = []
    for replay in replays:
        expected_path = ROOT / f"goldens/rekordbox-7.2.19/{replay.model}/{replay.suite}.json"
        actual_path = result_root / replay.model / f"{replay.suite}.actual.json"
        expected = json.loads(expected_path.read_text())["behavior"]
        actual = (
            json.loads(actual_path.read_text())["behavior"]
            if actual_path.is_file()
            else {"cases": []}
        )
        expected_cases = expected["cases"]
        actual_cases = actual["cases"]
        actual_by_id = {case["id"]: case for case in actual_cases}
        exact: list[str] = []
        different: list[str] = []
        same_shape: list[str] = []
        for expected_case in expected_cases:
            case_id = expected_case["id"]
            actual_case = actual_by_id.get(case_id)
            if actual_case is None:
                different.append(case_id)
                continue
            (exact if expected_case == actual_case else different).append(case_id)
            if case_shape(expected_case) == case_shape(actual_case):
                same_shape.append(case_id)
        expected_ids = {case["id"] for case in expected_cases}
        extra = [case["id"] for case in actual_cases if case["id"] not in expected_ids]
        run_error = run_errors.get((replay.model, replay.suite))
        suites.append(
            {
                "model": replay.model,
                "suite": replay.suite,
                "fixture": replay.fixture,
                "second_column": replay.second_column,
                "sorts": replay.sorts or ",".join(DEFAULT_SORTS),
                "cases": len(expected_cases),
                "exact_cases": exact,
                "different_cases": different,
                "same_outcome_total_row_count_cases": same_shape,
                "extra_cases": extra,
                "behavior_matches": run_error is None and expected == actual,
                "run_error": run_error,
                "golden": str(expected_path),
                "actual": str(actual_path),
                "diff": str(result_root / replay.model / f"{replay.suite}.diff.txt"),
            }
        )

    totals = aggregate_suites(suites)
    summary = {
        "format": 1,
        "backend": adapter.name,
        "backend_version": version,
        "source_tree_sha256": provenance["tree_sha256"],
        "lab_tree_sha256": provenance["lab_tree_sha256"],
        "oracle": "rekordbox 7.2.19",
        "configuration": "per-suite",
        "totals": totals,
        "suites": suites,
    }
    write_json(result_root / "summary.json", summary)

    lines = [
        f"# {adapter.name} conformance summary",
        "",
        f"Backend source: `{version}`",
        "",
        *adapter.summary_notes(),
        "",
        f"Completed {totals['completed_suites']} of {totals['suites']} suites; "
        f"{totals['exact_cases']} of {totals['cases']} cases "
        f"({totals['exact_case_rate']:.1%}) match exactly. "
        f"{totals['same_outcome_total_row_count_cases']} cases "
        f"({totals['same_outcome_total_row_count_rate']:.1%}) match outcome, total, "
        "and row count.",
        "",
        "| Model | Suite | Cases | Exact | Same outcome/total/rows | Run |",
        "| --- | --- | ---: | ---: | ---: | --- |",
    ]
    for suite in suites:
        lines.append(
            f"| {suite['model']} | {suite['suite']} | {suite['cases']} | "
            f"{len(suite['exact_cases'])} | "
            f"{len(suite['same_outcome_total_row_count_cases'])} | "
            f"{'error' if suite['run_error'] else 'complete'} |"
        )
    lines.extend(["", "## Exact and differing cases", ""])
    for suite in suites:
        exact = ", ".join(f"`{case}`" for case in suite["exact_cases"]) or "None"
        different = ", ".join(f"`{case}`" for case in suite["different_cases"]) or "None"
        run_error = suite["run_error"] or "None"
        lines.extend(
            [
                f"### {suite['model']} / {suite['suite']}",
                "",
                f"Exact: {exact}",
                "",
                f"Different: {different}",
                "",
                f"Run error: {run_error}",
                "",
            ]
        )
    (result_root / "SUMMARY.md").write_text("\n".join(lines))


def run(
    adapter: BackendAdapter,
    replays: Sequence[ReplaySpec],
    result_root: Path | None,
    no_build: bool,
) -> Path:
    if not no_build:
        adapter.prepare()

    provenance = adapter.source_provenance()
    version = adapter.version(provenance)
    destination = (
        result_root.resolve()
        if result_root is not None
        else ROOT / "results" / adapter.name / version
    )
    destination.mkdir(parents=True, exist_ok=True)
    write_json(destination / f"{adapter.name}-source.json", provenance)

    groups: list[tuple[tuple[str, str, str | None], list[ReplaySpec]]]
    if adapter.reuse_server_across_suites:
        reusable: dict[tuple[str, str, str | None], list[ReplaySpec]] = {}
        for replay in replays:
            key = (replay.fixture, replay.second_column, replay.sorts)
            reusable.setdefault(key, []).append(replay)
        groups = list(reusable.items())
    else:
        groups = [
            ((replay.fixture, replay.second_column, replay.sorts), [replay])
            for replay in replays
        ]

    run_errors: dict[tuple[str, str], str] = {}
    for (fixture, second_column, sorts), grouped_replays in groups:
        try:
            with adapter.server(
                fixture, second_column, sorts, destination
            ) as query_port:
                for replay in grouped_replays:
                    error = verify_replay(
                        adapter, replay, version, destination, query_port
                    )
                    if error is not None:
                        run_errors[(replay.model, replay.suite)] = error
        except Exception as error:
            detail = f"{type(error).__name__}: {error}"
            for replay in grouped_replays:
                run_errors[(replay.model, replay.suite)] = detail

    summarize(adapter, destination, provenance, version, run_errors, replays)
    return destination
