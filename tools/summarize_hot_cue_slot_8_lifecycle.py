#!/usr/bin/env python3
"""Validate and summarize the extended 0x2401 slot-8 lifecycle experiment."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from summarize_hot_cue_declared_length_ffffffff_lifecycle import (
    case_signature,
    getter_record,
)
from summarize_search_oracle import validate


ROOT = Path(__file__).resolve().parent.parent
CONFORMANCE = ROOT / "conformance"
MATRIX = CONFORMANCE / "data/hot-cue-slot-8-lifecycle-matrix.json"
FIXTURE = CONFORMANCE / "fixtures/generated/hot-cue-bank-mutation-duplicate-slot/manifest.json"
EVIDENCE = (
    ROOT
    / "data/experiments/hot-cue-bank/extended-setter-parser/slot-00000008-lifecycle"
)
OBSERVATIONS = EVIDENCE / "observations"
BASELINE_SNAPSHOT = EVIDENCE / "baseline-snapshot.json"
OUTPUT = EVIDENCE / "summary.json"
PARTIAL_OUTPUT = EVIDENCE / "summary.partial.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def logical_state(snapshot: dict[str, object]) -> dict[str, object]:
    return {
        "membership_count": snapshot["membership_count"],
        "memberships": snapshot["memberships"],
        "cues": snapshot["cues"],
    }


def health_summary(document: dict[str, object]) -> dict[str, object]:
    processes = document["rekordbox_processes"]
    events = document["application_events"]

    return {
        "process_count": document["rekordbox_process_count"],
        "responding": [process["responding"] for process in processes],
        "main_window_handles": [process["main_window_handle"] for process in processes],
        "application_event_count": len(events),
        "application_events": events,
    }


def stable(values: list[object]) -> object:
    encoded = [json.dumps(value, sort_keys=True) for value in values]
    return values[0] if len(set(encoded)) == 1 else "varied"


def validate_receipt(receipt: dict[str, object], paths: dict[str, Path]) -> None:
    for key, path in paths.items():
        assert receipt[f"{key}_sha256"] == sha256(path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-partial", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    matrix = json.loads(MATRIX.read_text())
    fixture = json.loads(FIXTURE.read_text())
    baseline = json.loads(BASELINE_SNAPSHOT.read_text())
    baseline_state = logical_state(baseline)
    observation_suite = CONFORMANCE / matrix["observation_suite"]
    restart_suite = CONFORMANCE / matrix["restart_getter_suite"]
    results = []

    assert baseline["integrity"] == "ok"
    for run in range(1, matrix["replicates"] + 1):
        directory = OBSERVATIONS / f"run-{run}"
        receipt_path = directory / "complete.json"
        if not receipt_path.is_file():
            if args.allow_partial:
                continue
            raise FileNotFoundError(receipt_path)

        paths = {
            "observation_suite": observation_suite,
            "restart_suite": restart_suite,
            "observation": directory / "observation.json",
            "health_after_observation": directory / "health-after-observation.json",
            "snapshot_after_observation": directory / "snapshot-after-observation.json",
            "restart_getter": directory / "restart-getter.json",
            "health_after_restart": directory / "health-after-restart.json",
            "snapshot_after_restart": directory / "snapshot-after-restart.json",
        }
        receipt = json.loads(receipt_path.read_text())
        assert receipt["run"] == run
        validate_receipt(receipt, paths)

        observation = validate(observation_suite, paths["observation"], FIXTURE)
        restart = validate(restart_suite, paths["restart_getter"], FIXTURE)
        assert set(observation) == {"setter", "database-read-after-setter"}
        assert set(restart) == {"database-read-after-process-restart"}

        health_after_observation = json.loads(
            paths["health_after_observation"].read_text()
        )
        health_after_restart = json.loads(paths["health_after_restart"].read_text())
        snapshot_after_observation = json.loads(
            paths["snapshot_after_observation"].read_text()
        )
        snapshot_after_restart = json.loads(
            paths["snapshot_after_restart"].read_text()
        )
        assert snapshot_after_observation["integrity"] == "ok"
        assert snapshot_after_restart["integrity"] == "ok"

        immediate_case = observation["database-read-after-setter"]
        restart_case = restart["database-read-after-process-restart"]
        immediate_getter = getter_record(immediate_case)
        restarted_getter = getter_record(restart_case)
        observation_effect = (
            "pristine"
            if logical_state(snapshot_after_observation) == baseline_state
            else "changed"
        )
        restart_effect = (
            "pristine"
            if logical_state(snapshot_after_restart) == baseline_state
            else "changed"
        )

        results.append(
            {
                "run": run,
                "setter_signature": case_signature(observation["setter"]),
                "immediate_getter_signature": case_signature(immediate_case),
                "immediate_getter": immediate_getter,
                "restart_getter_signature": case_signature(restart_case),
                "restart_getter": restarted_getter,
                "database_effect_after_observation": observation_effect,
                "database_effect_after_restart": restart_effect,
                "health_after_observation": health_summary(health_after_observation),
                "health_after_restart": health_summary(health_after_restart),
                "snapshot_after_observation_sha256": sha256(
                    paths["snapshot_after_observation"]
                ),
                "snapshot_after_restart_sha256": sha256(
                    paths["snapshot_after_restart"]
                ),
                "receipt_sha256": sha256(receipt_path),
            }
        )

    declared = matrix["replicates"]
    complete = len(results) == declared
    if not complete and not args.allow_partial:
        raise AssertionError(f"only {len(results)} of {declared} observations exist")

    aggregate = {
        "setter_signatures": dict(Counter(result["setter_signature"] for result in results)),
        "immediate_getter_signatures": dict(
            Counter(result["immediate_getter_signature"] for result in results)
        ),
        "restart_getter_signatures": dict(
            Counter(result["restart_getter_signature"] for result in results)
        ),
        "database_effect_after_observation": stable(
            [result["database_effect_after_observation"] for result in results]
        ) if results else None,
        "database_effect_after_restart": stable(
            [result["database_effect_after_restart"] for result in results]
        ) if results else None,
        "immediate_getter": stable(
            [result["immediate_getter"] for result in results]
        ) if results else None,
        "restart_getter": stable([result["restart_getter"] for result in results])
        if results
        else None,
    }
    document = {
        "format": 1,
        "experiment": matrix["experiment"],
        "complete": complete,
        "declared_observations": declared,
        "completed_observations": len(results),
        "fixture_database_sha256": fixture["database_sha256"],
        "fixture_fingerprint": fixture["fixture_fingerprint"],
        "baseline_snapshot_sha256": sha256(BASELINE_SNAPSHOT),
        "matrix_sha256": sha256(MATRIX),
        "aggregate": aggregate,
        "results": results,
    }
    destination = OUTPUT if complete else PARTIAL_OUTPUT
    destination.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n")
    print(destination)


if __name__ == "__main__":
    main()
