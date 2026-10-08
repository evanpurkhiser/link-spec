#!/usr/bin/env python3
"""Validate packed Hot Cue Bank getters under genuine status identities."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from summarize_search_oracle import load, sha256, validate


ROOT = Path(__file__).resolve().parent.parent
CONFORMANCE = ROOT / "conformance"
MANIFEST = CONFORMANCE / "fixtures/generated/hot-cue-banks/manifest.json"
OUTPUT = ROOT / "data/experiments/packed-context/hot-cue-getter-status-cross/summary.json"
MODELS = {
    "xdj-rx3-status": (11, "xdj-rx3-player-11-status.json"),
    "cdj-3000-status": (1, "cdj-3000-player-1-status.json"),
}
SETUPS = ("extended", "legacy")
FAMILIES = (
    "legacy-populated",
    "legacy-empty",
    "extended-populated",
    "extended-empty",
)


def decoded_messages(case: dict[str, object]) -> list[dict[str, object]]:
    response = case["raw_response"]
    assert isinstance(response, dict)
    messages = response["messages"]
    assert isinstance(messages, list)
    return messages


def normalized_behavior_hash(path: Path) -> str:
    behavior = load(path)["behavior"]
    normalized = {
        "cases": [
            {
                "id": case["id"],
                "outcome": case["outcome"],
                "messages": decoded_messages(case),
            }
            for case in behavior["cases"]
        ]
    }
    encoded = json.dumps(normalized, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def message_values(case: dict[str, object]) -> tuple[int, list[object]]:
    messages = decoded_messages(case)
    assert len(messages) == 1
    message = messages[0]
    return message["kind"], [argument.get("value", argument.get("hex")) for argument in message["arguments"]]


def main() -> None:
    all_cases: dict[str, dict[str, dict[str, dict[str, object]]]] = {}
    golden_hashes: dict[str, dict[str, str]] = {}
    behavior_hashes: dict[str, dict[str, str]] = {}

    for setup in SETUPS:
        all_cases[setup] = {}
        golden_hashes[setup] = {}
        behavior_hashes[setup] = {}

        for model, (player, identity_name) in MODELS.items():
            suite = CONFORMANCE / f"suites/context-hot-cue-getter-status-player-{player}-{setup}.json"
            golden = (
                CONFORMANCE
                / f"goldens/rekordbox-7.2.19/{model}/context-hot-cue-getter-status-{setup}.json"
            )
            cases = validate(suite, golden, MANIFEST)
            assert len(cases) == 28
            all_cases[setup][model] = cases
            golden_hashes[setup][model] = sha256(golden)
            behavior_hashes[setup][model] = normalized_behavior_hash(golden)

            identity = load(CONFORMANCE / f"runs/{identity_name}")
            assert identity["player"] == player
            assert identity["status_template"] != "none"

            for track_type in range(0x07):
                for family in FAMILIES:
                    case = cases[f"type-{track_type:02x}--{family}"]
                    assert case["outcome"] == "raw_reply"
                    kind, values = message_values(case)

                    if family.startswith("legacy"):
                        assert kind == 0x4702
                        assert values[0] == 0x2101
                        if track_type == 0x01:
                            assert values[1] == 0
                            assert values[5] == (
                                3 if family.endswith("populated") else 0
                            )
                        else:
                            assert values[1] == 50
                            assert values[2] == 0
                            assert values[5] == 0
                        continue

                    assert kind == 0x4E02
                    assert values[0] == 0x2301
                    if track_type == 0x01:
                        assert values[1] == (
                            0 if family.endswith("populated") else 1
                        )
                        assert values[4] == (
                            3 if family.endswith("populated") else 0
                        )
                    else:
                        assert values[1] == 50
                        assert values[2] == 0
                        assert values[4] == 0

            for family in FAMILIES:
                baseline = decoded_messages(cases[f"type-00--{family}"])
                for track_type in (0x02, 0x03, 0x04, 0x05, 0x06):
                    assert (
                        decoded_messages(cases[f"type-{track_type:02x}--{family}"])
                        == baseline
                    )

        assert len(set(behavior_hashes[setup].values())) == 1

    for model in MODELS:
        extended = all_cases["extended"][model]
        legacy = all_cases["legacy"][model]
        for case_id in extended:
            assert decoded_messages(extended[case_id]) == decoded_messages(legacy[case_id])

    report = {
        "schema_version": 1,
        "product": "rekordbox 7.2.19",
        "models": list(MODELS),
        "setups": list(SETUPS),
        "observed": {
            "goldens": 4,
            "cases_per_golden": 28,
            "case_executions": 112,
            "immediate_repeat_executions": 112,
            "track_types": [f"0x{track_type:02x}" for track_type in range(0x07)],
            "request_kinds": ["0x2101", "0x2301"],
            "families": list(FAMILIES),
            "successful_track_type": "0x01",
            "rejected_track_types": [
                "0x00",
                "0x02",
                "0x03",
                "0x04",
                "0x05",
                "0x06",
            ],
            "rejected_status": 50,
            "all_rejected_track_types_equal_within_family": True,
            "normalized_identity_behavior_equal_within_setup": True,
            "setup_behavior_equal_within_identity": True,
        },
        "artifacts": {
            "generator_sha256": sha256(
                CONFORMANCE / "generate_context_hot_cue_getter_status_suites.py"
            ),
            "recorder_sha256": sha256(
                CONFORMANCE / "record_context_hot_cue_getter_status_matrix.sh"
            ),
            "fixture_fingerprint": load(MANIFEST)["fixture_fingerprint"],
            "golden_sha256": golden_hashes,
            "normalized_behavior_sha256": behavior_hashes,
        },
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(OUTPUT)


if __name__ == "__main__":
    main()
