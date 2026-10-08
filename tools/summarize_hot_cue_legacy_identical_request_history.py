#!/usr/bin/env python3
"""Validate the interleaved legacy setter request-history experiment."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import summarize_hot_cue_legacy_setter_parser as legacy


ROOT = Path(__file__).resolve().parent.parent
CONFORMANCE = ROOT / "conformance"
DECLARATION = CONFORMANCE / "data/hot-cue-legacy-identical-request-history.json"
FIXTURE = CONFORMANCE / "fixtures/generated/hot-cue-bank-legacy-ordinals/manifest.json"
EVIDENCE = ROOT / "data/experiments/hot-cue-bank/legacy-identical-request-history"
BASELINE = ROOT / "data/experiments/hot-cue-bank/legacy-setter-parser/baseline.json"
OUTPUT = EVIDENCE / "summary.json"
PARTIAL_OUTPUT = EVIDENCE / "summary.partial.json"


def sha256(path: Path) -> str:
    return legacy.sha256(path)


def load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text())


def request_signature(phase: dict[str, object]) -> str:
    return legacy.request_signature({"suite": phase["suite"]})


def unavailable_getter(
    directory: Path, health: dict[str, object]
) -> dict[str, object]:
    skipped_path = directory / "getter-skipped.json"
    assert skipped_path.is_file()
    skipped = load(skipped_path)
    outcome = str(skipped.get("outcome", "process-exited"))
    assert outcome in {
        "process-exited",
        "dbserver-connect-timeout",
        "port-query-timeout",
    }
    unavailable_health = health
    if outcome != "process-exited":
        assert skipped["getter_log_sha256"] == sha256(directory / "getter.log")
        unavailable_path = directory / "health-after-getter-unavailable.json"
        assert skipped["health_sha256"] == sha256(unavailable_path)
        unavailable_health = load(unavailable_path)

    return {
        "getter_outcome": f"skipped-{outcome}",
        "getter_effect": f"unavailable-{outcome}",
        "getter_record_count": None,
        "getter_record_lengths": None,
        "getter_blob_bytes": None,
        "getter_blob_sha256": None,
        "getter_unavailable_process_state": (
            "alive" if unavailable_health["rekordbox_process_count"] else "exited"
        ),
        "getter_unavailable_application_error_signatures": [
            legacy.application_error_signature(event)
            for event in unavailable_health["application_events"]
        ],
    }


def parse_request_phase(
    cycle: int,
    index: int,
    phase: dict[str, object],
    baseline: dict[str, object],
) -> dict[str, object] | None:
    directory = EVIDENCE / f"cycle-{cycle}" / f"{index:02d}-{phase['id']}"
    receipt_path = directory / "complete.json"
    if not receipt_path.is_file():
        return None

    suite = CONFORMANCE / str(phase["suite"])
    cases = legacy.validate(suite, directory / "setter.json", FIXTURE)
    assert set(cases) == {"setter"}
    setter = legacy.parse_setter(cases["setter"])
    health = load(directory / "health.json")
    assert health["schema_version"] >= 2
    assert isinstance(health["helper_processes"], list)
    assert isinstance(health["tcp_listeners"], list)
    snapshot_path = directory / "database/snapshot.json"
    effect, changed_ids = legacy.database_effect(baseline, load(snapshot_path))
    result = {
        "cycle": cycle,
        "phase": phase["id"],
        "request_signature": request_signature(phase),
        **setter,
        "process_state": (
            "alive" if health["rekordbox_process_count"] else "exited"
        ),
        "process_count": health["rekordbox_process_count"],
        "helper_process_count": health["helper_process_count"],
        "tcp_listeners": health["tcp_listeners"],
        "application_error_signatures": [
            legacy.application_error_signature(event)
            for event in health["application_events"]
        ],
        "database_effect": effect,
        "changed_membership_ids": changed_ids,
        "setter_sha256": sha256(directory / "setter.json"),
        "health_sha256": sha256(directory / "health.json"),
        "database_snapshot_sha256": sha256(snapshot_path),
    }

    getter_path = directory / "getter.json"
    if getter_path.is_file():
        result.update(legacy.parse_getter(getter_path))
        result["getter_unavailable_process_state"] = None
        result["getter_unavailable_application_error_signatures"] = None
    else:
        result.update(unavailable_getter(directory, health))

    restart_path = directory / "restart-getter.json"
    if restart_path.is_file():
        restart = legacy.parse_getter(restart_path)
        restart_health_path = directory / "health-after-restart.json"
        restart_health = load(restart_health_path)
        assert restart_health["schema_version"] >= 2
        restart_snapshot_path = directory / "database-after-restart/snapshot.json"
        restart_effect, restart_changed_ids = legacy.database_effect(
            baseline, load(restart_snapshot_path)
        )
        result.update(
            {
                "restart_getter_outcome": restart["getter_outcome"],
                "restart_getter_effect": restart["getter_effect"],
                "restart_getter_blob_sha256": restart["getter_blob_sha256"],
                "restart_process_state": (
                    "alive"
                    if restart_health["rekordbox_process_count"]
                    else "exited"
                ),
                "restart_database_effect": restart_effect,
                "restart_changed_membership_ids": restart_changed_ids,
                "restart_getter_sha256": sha256(restart_path),
                "restart_health_sha256": sha256(restart_health_path),
                "restart_database_snapshot_sha256": sha256(
                    restart_snapshot_path
                ),
            }
        )
    else:
        assert (directory / "restart-skipped.json").is_file()
        result.update(
            {
                "restart_getter_outcome": "skipped-immediate-raw-reply",
                "restart_getter_effect": None,
                "restart_getter_blob_sha256": None,
                "restart_process_state": None,
                "restart_database_effect": None,
                "restart_changed_membership_ids": None,
                "restart_getter_sha256": None,
                "restart_health_sha256": None,
                "restart_database_snapshot_sha256": None,
            }
        )

    receipt = load(receipt_path)
    assert receipt["action"] == "request"
    assert receipt["cycle"] == cycle
    assert receipt["phase"] == phase["id"]
    assert receipt["suite_sha256"] == sha256(suite)
    assert receipt["setter_sha256"] == result["setter_sha256"]
    assert receipt["health_sha256"] == result["health_sha256"]
    assert receipt["database_snapshot_sha256"] == result["database_snapshot_sha256"]
    assert receipt["getter_sha256"] == sha256(
        directory / receipt["getter_artifact"]
    )
    assert receipt["restart_sha256"] == sha256(
        directory / receipt["restart_artifact"]
    )
    assert receipt["restart_health_sha256"] == result["restart_health_sha256"]
    assert (
        receipt["restart_database_snapshot_sha256"]
        == result["restart_database_snapshot_sha256"]
    )
    result["receipt_sha256"] = sha256(receipt_path)
    return result


def validate_restart_receipt(
    cycle: int, path: Path, expected_phase: str
) -> dict[str, object]:
    document = load(path)
    assert document == {
        **document,
        "format": 1,
        "action": "isolated-vm-restart",
        "cycle": cycle,
        "phase": expected_phase,
        "isolated_service_state": "active",
        "isolation_gate": "passed",
    }
    return {
        "phase": expected_phase,
        "started_at": document["started_at"],
        "completed_at": document["completed_at"],
        "sha256": sha256(path),
    }


def durable_signature(result: dict[str, object]) -> dict[str, object]:
    return {
        key: result[key]
        for key in (
            "database_effect",
            "changed_membership_ids",
            "restart_getter_outcome",
            "restart_getter_effect",
            "restart_getter_blob_sha256",
            "restart_database_effect",
            "restart_changed_membership_ids",
        )
    }


def lifecycle_signature(result: dict[str, object]) -> dict[str, object]:
    return {
        key: result[key]
        for key in (
            "outcome",
            "response_kind",
            "status",
            "process_state",
            "getter_outcome",
            "getter_effect",
            "getter_unavailable_process_state",
            "application_error_signatures",
        )
    }


def group_signatures(
    observations: list[dict[str, object]],
    signature,
) -> list[dict[str, object]]:
    groups: dict[str, dict[str, object]] = {}
    for observation in observations:
        fields = signature(observation)
        fingerprint = legacy.digest(fields)
        group = groups.setdefault(
            fingerprint,
            {
                "signature": fingerprint,
                "fields": fields,
                "observations": [],
            },
        )
        group["observations"].append(
            {
                "cycle": observation["cycle"],
                "phase": observation["phase"],
            }
        )

    return [groups[fingerprint] for fingerprint in sorted(groups)]


def validate_cycle_receipt(cycle: int, directory: Path) -> None:
    receipt = load(directory / "complete.json")
    assert receipt["format"] == 1
    assert receipt["cycle"] == cycle
    assert receipt["declaration_sha256"] == sha256(DECLARATION)
    for group in ("phase_receipts", "restart_receipts"):
        for artifact in receipt[group]:
            assert artifact["sha256"] == sha256(directory / artifact["path"])


def summarize(allow_partial: bool) -> dict[str, object]:
    declaration = load(DECLARATION)
    baseline = load(BASELINE)
    request_phases = [
        (index, phase)
        for index, phase in enumerate(declaration["phases"], start=1)
        if phase["action"] == "request"
    ]
    explicit_restart = next(
        (index, phase)
        for index, phase in enumerate(declaration["phases"], start=1)
        if phase["action"] == "isolated-vm-restart"
    )
    results: list[dict[str, object]] = []
    restarts: list[dict[str, object]] = []
    completed_cycles = []

    for cycle in range(1, declaration["cycles"] + 1):
        directory = EVIDENCE / f"cycle-{cycle}"
        if not (directory / "complete.json").is_file():
            continue
        validate_cycle_receipt(cycle, directory)
        first_index, first_phase = request_phases[0]
        restarts.append(
            validate_restart_receipt(
                cycle,
                directory
                / f"{first_index:02d}-{first_phase['id']}-before-isolated-vm-restart.json",
                f"{first_phase['id']}-before",
            )
        )
        restart_index, restart_phase = explicit_restart
        restarts.append(
            validate_restart_receipt(
                cycle,
                directory
                / f"{restart_index:02d}-{restart_phase['id']}-isolated-vm-restart.json",
                restart_phase["id"],
            )
        )
        for index, phase in request_phases:
            result = parse_request_phase(cycle, index, phase, baseline)
            assert result is not None
            results.append(result)
        completed_cycles.append(cycle)

    if not allow_partial:
        assert completed_cycles == list(range(1, declaration["cycles"] + 1))

    canonical = [result for result in results if "canonical" in result["phase"]]
    for result in canonical:
        assert result["request_signature"] == declaration["canonical_request_signature"]

    by_phase: dict[str, list[dict[str, object]]] = defaultdict(list)
    for result in results:
        by_phase[str(result["phase"])].append(result)
    phase_repeat = []
    for phase, observations in by_phase.items():
        durable_groups = group_signatures(observations, durable_signature)
        lifecycle_groups = group_signatures(observations, lifecycle_signature)
        complete = len(observations) == declaration["cycles"]
        phase_repeat.append(
            {
                "phase": phase,
                "observations": len(observations),
                "durable_repeat_verified": complete and len(durable_groups) == 1,
                "lifecycle_repeat_exact": complete and len(lifecycle_groups) == 1,
                "durable_groups": durable_groups,
                "lifecycle_groups": lifecycle_groups,
            }
        )

    lifecycle_groups: dict[str, list[dict[str, object]]] = defaultdict(list)
    for result in canonical:
        signature = legacy.digest(lifecycle_signature(result))
        lifecycle_groups[signature].append(
            {"cycle": result["cycle"], "phase": result["phase"]}
        )

    return {
        "scope": declaration["scope"],
        "fixture": {
            "profile": declaration["fixture_profile"],
            "database_sha256": load(FIXTURE)["database_sha256"],
        },
        "matrix": {
            "declared_cycles": declaration["cycles"],
            "completed_cycles": completed_cycles,
            "declared_request_observations": (
                declaration["cycles"] * len(request_phases)
            ),
            "completed_request_observations": len(results),
            "declared_vm_restarts": declaration["cycles"] * 2,
            "completed_vm_restarts": len(restarts),
        },
        "canonical_request_signature": declaration["canonical_request_signature"],
        "canonical_lifecycle_groups": [
            {"signature": signature, "observations": observations}
            for signature, observations in sorted(lifecycle_groups.items())
        ],
        "phase_repeat": sorted(phase_repeat, key=lambda item: item["phase"]),
        "vm_restarts": restarts,
        "results": results,
        "sha256": {
            "declaration": sha256(DECLARATION),
            "fixture_manifest": sha256(FIXTURE),
            "recorder": sha256(
                CONFORMANCE
                / "record_hot_cue_legacy_identical_request_history.sh"
            ),
            "health_capture": sha256(CONFORMANCE / "capture_rekordbox_health.ps1"),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--allow-partial", action="store_true")
    args = parser.parse_args()
    document = summarize(args.allow_partial)
    output = PARTIAL_OUTPUT if args.allow_partial else OUTPUT
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n")
    print(
        f"validated {document['matrix']['completed_request_observations']} request "
        f"observations; wrote {output}"
    )


if __name__ == "__main__":
    main()
