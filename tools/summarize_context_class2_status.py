#!/usr/bin/env python3
"""Validate remaining class-2 packed-context behavior under genuine status."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from summarize_search_oracle import load, sha256, validate


ROOT = Path(__file__).resolve().parent.parent
CONFORMANCE = ROOT / "conformance"
MANIFEST = CONFORMANCE / "fixtures/generated/full/manifest.json"
OUTPUT = ROOT / "data/experiments/packed-context/class2-status-cross/summary.json"
MODELS = {
    "xdj-rx3-status": (11, "xdj-rx3-player-11-status.json"),
    "cdj-3000-status": (1, "cdj-3000-player-1-status.json"),
}
SETUPS = {"extended": 16, "legacy": 12}
NO_BUILDERS = {
    "recognized-22": 0x2202,
    "recognized-23": 0x2302,
    "recognized-24": 0x2402,
    "recognized-25": 0x2502,
}


def normalized_behavior_hash(path: Path) -> str:
    behavior = load(path)["behavior"]
    normalized = {
        "cases": [
            {
                "id": case["id"],
                "outcome": case["outcome"],
                "total": case["total"],
                "header": case["header"],
                "rows": case["rows"],
                "pages": [
                    {
                        **page,
                        "arguments": [
                            {"type": "number", "value": argument["value"] & 0x00FFFFFF}
                            if index == 0 and argument["type"] == "number"
                            else argument
                            for index, argument in enumerate(page["arguments"])
                        ],
                    }
                    for page in case["pages"]
                ],
            }
            for case in behavior["cases"]
        ],
        "setup": behavior["setup"],
    }
    encoded = json.dumps(normalized, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def values(row: dict[str, object]) -> list[object]:
    return [argument["value"] for argument in row["arguments"]]


def main() -> None:
    cases_by_setup: dict[str, dict[str, dict[str, object]]] = {}
    golden_hashes: dict[str, dict[str, str]] = {}
    behavior_hashes: dict[str, dict[str, str]] = {}

    for setup, width in SETUPS.items():
        cases_by_setup[setup] = {}
        golden_hashes[setup] = {}
        behavior_hashes[setup] = {}

        for model, (player, identity_name) in MODELS.items():
            suite = CONFORMANCE / f"suites/context-class2-status-player-{player}-{setup}.json"
            golden = (
                CONFORMANCE
                / f"goldens/rekordbox-7.2.19/{model}/context-class2-status-{setup}.json"
            )
            cases = validate(suite, golden, MANIFEST)
            assert len(cases) == 35
            cases_by_setup[setup][model] = cases
            golden_hashes[setup][model] = sha256(golden)
            behavior_hashes[setup][model] = normalized_behavior_hash(golden)

            identity = load(CONFORMANCE / f"runs/{identity_name}")
            assert identity["player"] == player
            assert identity["status_template"] != "none"

            for track_type in range(0x07):
                for label, request_kind in NO_BUILDERS.items():
                    case = cases[f"type-{track_type:02x}--{label}"]
                    assert case["outcome"] == "error"
                    assert case["total"] is None
                    assert case["rows"] == []
                    assert case["header"] == [
                        {
                            "kind": 0x4003,
                            "arguments": [{"type": "number", "value": request_kind}],
                        }
                    ]

                delivery = cases[f"type-{track_type:02x}--delivery"]
                if track_type == 0x01:
                    assert delivery["outcome"] == "menu"
                    assert delivery["total"] == 13
                    assert len(delivery["rows"]) == 13
                    assert {len(row["arguments"]) for row in delivery["rows"]} == {width}
                    continue

                assert delivery["outcome"] == "error"
                assert delivery["total"] == 0xFFFFFFFF
                assert delivery["rows"] == []

        assert len(set(behavior_hashes[setup].values())) == 1

    for model in MODELS:
        extended = cases_by_setup["extended"][model]
        legacy = cases_by_setup["legacy"][model]
        for case_id, extended_case in extended.items():
            legacy_case = legacy[case_id]
            assert legacy_case["outcome"] == extended_case["outcome"]
            assert legacy_case["total"] == extended_case["total"]
            for legacy_row, extended_row in zip(
                legacy_case["rows"], extended_case["rows"], strict=True
            ):
                assert values(legacy_row) == values(extended_row)[:12]

    report = {
        "schema_version": 1,
        "product": "rekordbox 7.2.19",
        "models": list(MODELS),
        "setups": {setup: {"row_width": width} for setup, width in SETUPS.items()},
        "observed": {
            "goldens": 4,
            "cases_per_golden": 35,
            "case_executions": 140,
            "immediate_repeat_executions": 140,
            "no_builder_request_kinds": [f"0x{kind:04x}" for kind in NO_BUILDERS.values()],
            "no_builder_response_kind": "0x4003",
            "delivery_successful_track_type": "0x01",
            "delivery_successful_total": 13,
            "delivery_error_track_types": [
                "0x00",
                "0x02",
                "0x03",
                "0x04",
                "0x05",
                "0x06",
            ],
            "delivery_error_total": "0xffffffff",
            "normalized_identity_behavior_equal_within_setup": True,
            "legacy_rows_are_extended_prefix": True,
        },
        "artifacts": {
            "generator_sha256": sha256(
                CONFORMANCE / "generate_context_class2_status_suites.py"
            ),
            "recorder_sha256": sha256(
                CONFORMANCE / "record_context_class2_status_matrix.sh"
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
