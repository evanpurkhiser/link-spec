#!/usr/bin/env python3
"""Validate the status/setup packed-context cross for Hot Cue setter 0x2401."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CONFORMANCE = ROOT / "conformance"
sys.path.insert(0, str(CONFORMANCE))
sys.path.insert(0, str(ROOT / "tools"))

from build_hot_cue_mutation_record import build_record
from summarize_search_oracle import validate


FIXTURE = CONFORMANCE / "fixtures/generated/hot-cue-bank-mutation-duplicate-slot/manifest.json"
GENERATOR = CONFORMANCE / "generate_context_hot_cue_setter_status_suites.py"
RECORDER = CONFORMANCE / "record_context_hot_cue_setter_status_matrix.sh"
OUTPUT = (
    ROOT
    / "data/experiments/packed-context/hot-cue-setter-status-cross/summary.json"
)
REJECTED_TYPES = (0x00, 0x02, 0x03, 0x04, 0x05, 0x06)
CONFIGURATIONS = (
    ("xdj-rx3-status", 11, "extended"),
    ("xdj-rx3-status", 11, "legacy"),
    ("cdj-3000-status", 1, "extended"),
    ("cdj-3000-status", 1, "legacy"),
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def message(case: dict[str, object]) -> dict[str, object]:
    messages = case["raw_response"]["messages"]
    assert len(messages) == 1
    return messages[0]


def number(argument: dict[str, object]) -> int:
    assert argument["type"] == "number"
    return argument["value"]


def blob(argument: dict[str, object]) -> str:
    assert argument["type"] == "blob"
    return argument["hex"]


def response_signature(cases: dict[str, dict[str, object]]) -> str:
    responses = [
        {"id": case_id, "messages": cases[case_id]["raw_response"]["messages"]}
        for case_id in sorted(cases)
    ]
    encoded = json.dumps(responses, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def main() -> None:
    target_blob = build_record().hex()
    results = {}
    shared_signature = None
    shared_baseline = None

    for model, player, setup in CONFIGURATIONS:
        suite = CONFORMANCE / f"suites/context-hot-cue-setter-status-player-{player}-{setup}.json"
        golden = (
            CONFORMANCE
            / f"goldens/rekordbox-7.2.19/{model}/context-hot-cue-setter-status-{setup}.json"
        )
        cases = validate(suite, golden, FIXTURE)
        assert len(cases) == 14

        baseline_blobs = []
        for track_type in REJECTED_TYPES:
            setter = message(cases[f"type-{track_type:02x}--set-rejected"])
            assert setter["kind"] == 0x4E02
            setter_arguments = setter["arguments"]
            assert [number(setter_arguments[index]) for index in (0, 1, 2, 4)] == [
                0x2401,
                50,
                0,
                0,
            ]
            assert blob(setter_arguments[3]) == ""

            getter = message(
                cases[f"type-{track_type:02x}--read-after-rejected-setter"]
            )
            assert getter["kind"] == 0x4E02
            getter_arguments = getter["arguments"]
            assert [number(getter_arguments[index]) for index in (0, 1, 2, 4)] == [
                0x2301,
                0,
                124,
                1,
            ]
            baseline_blobs.append(blob(getter_arguments[3]))

        assert len(set(baseline_blobs)) == 1
        baseline = baseline_blobs[0]
        assert baseline != target_blob

        accepted = message(cases["type-01--set-accepted"])
        accepted_arguments = accepted["arguments"]
        assert accepted["kind"] == 0x4E02
        assert [number(accepted_arguments[index]) for index in (0, 1, 2, 4)] == [
            0x2401,
            0,
            124,
            1,
        ]
        assert blob(accepted_arguments[3]) == target_blob

        after = message(cases["type-01--read-after-accepted-setter"])
        after_arguments = after["arguments"]
        assert after["kind"] == 0x4E02
        assert [number(after_arguments[index]) for index in (0, 1, 2, 4)] == [
            0x2301,
            0,
            124,
            1,
        ]
        assert blob(after_arguments[3]) == target_blob

        signature = response_signature(cases)
        if shared_signature is None:
            shared_signature = signature
            shared_baseline = baseline
        assert signature == shared_signature
        assert baseline == shared_baseline

        results[f"{model}/{setup}"] = {
            "suite_sha256": sha256(suite),
            "golden_sha256": sha256(golden),
            "case_count": len(cases),
            "response_signature": signature,
        }

    manifest = json.loads(FIXTURE.read_text())
    summary = {
        "scope": "real Rekordbox 7.2.19 only; backend comparison is deferred",
        "fixture": {
            "profile": "hot-cue-bank-mutation",
            "database_sha256": manifest["database_sha256"],
            "fixture_fingerprint": manifest["fixture_fingerprint"],
            "bank_id": manifest["ids"]["hotcue.bank.mutation"],
        },
        "matrix": {
            "models": ["XDJ-RX3", "CDJ-3000"],
            "players": [11, 1],
            "setups": ["extended", "legacy"],
            "packed_types": [0, 1, 2, 3, 4, 5, 6],
            "goldens": 4,
            "cases": 56,
            "immediate_database_checks_after_rejected_setters": 24,
            "independent_fixture_reset_repeats": 4,
        },
        "observations": {
            "accepted_type": 1,
            "rejected_types": list(REJECTED_TYPES),
            "rejected_reply": "4e02 [2401, 50, 0, empty_blob, 0]",
            "rejected_database_effect": "none; every following type-1 getter returned the shared baseline record",
            "accepted_reply": "4e02 [2401, 0, 124, canonical_record, 1]",
            "accepted_database_effect": "the following type-1 getter returned the canonical mutated record",
            "identity_and_setup_effect": "none in the complete decoded response sequence",
            "shared_response_signature": shared_signature,
            "baseline_record_sha256": hashlib.sha256(bytes.fromhex(shared_baseline)).hexdigest(),
            "mutated_record_sha256": hashlib.sha256(bytes.fromhex(target_blob)).hexdigest(),
        },
        "artifacts": results,
        "sha256": {
            "generator": sha256(GENERATOR),
            "recorder": sha256(RECORDER),
            "fixture_manifest": sha256(FIXTURE),
        },
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(f"validated 4 goldens / 56 cases; wrote {OUTPUT}")


if __name__ == "__main__":
    main()
