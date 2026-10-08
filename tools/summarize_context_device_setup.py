#!/usr/bin/env python3
"""Validate the packed-context cross over device identities and setup widths."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from summarize_search_oracle import load, sha256, validate


ROOT = Path(__file__).resolve().parent.parent
CONFORMANCE = ROOT / "conformance"
MANIFEST = CONFORMANCE / "fixtures/generated/full/manifest.json"
OUTPUT = ROOT / "data/experiments/packed-context/device-setup-cross/summary.json"
MODELS = (
    "xdj-rx3",
    "cdj-3000",
    "cdj-2000nxs2",
    "xdj-xz",
    "xdj-az",
    "xdj-1000mk2",
    "unknown-mixer",
    "unknown-djm",
)
SETUPS = {"extended": 16, "legacy": 12}
SUCCESS_TYPES = (0x00, 0x01, 0x02, 0x05, 0x06)


def behavior_hash(path: Path) -> str:
    behavior = load(path)["behavior"]
    encoded = json.dumps(behavior, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def row_values(case: dict[str, object]) -> list[list[object]]:
    return [
        [argument["value"] for argument in row["arguments"]]
        for row in case["rows"]
    ]


def main() -> None:
    by_setup: dict[str, dict[str, dict[str, object]]] = {}
    golden_hashes: dict[str, dict[str, str]] = {}
    behavior_hashes: dict[str, dict[str, str]] = {}

    for setup, width in SETUPS.items():
        suite = CONFORMANCE / f"suites/context-device-setup-{setup}.json"
        by_setup[setup] = {}
        golden_hashes[setup] = {}
        behavior_hashes[setup] = {}

        for model in MODELS:
            golden = (
                CONFORMANCE
                / f"goldens/rekordbox-7.2.19/{model}/context-device-setup-{setup}.json"
            )
            cases = validate(suite, golden, MANIFEST)
            assert len(cases) == 16
            by_setup[setup][model] = cases
            golden_hashes[setup][model] = sha256(golden)
            behavior_hashes[setup][model] = behavior_hash(golden)

            for track_type in range(0x07):
                case = cases[f"type-{track_type:02x}--tracks"]
                if track_type in (0x03, 0x04):
                    assert case["outcome"] == "timeout"
                    assert case["transport_error_kind"] == "WouldBlock"
                    assert case["header"] == []
                    assert case["rows"] == []
                    continue

                assert case["outcome"] == "menu"
                assert case["total"] == 8
                assert len(case["rows"]) == 8
                assert {len(row["arguments"]) for row in case["rows"]} == {width}
                expected = 0x100 if track_type == 0x01 else 0
                assert {row["arguments"][10]["value"] for row in case["rows"]} == {
                    expected
                }

            for track_type in SUCCESS_TYPES:
                case = cases[f"type-{track_type:02x}--genre-tracks-all"]
                assert case["outcome"] == "menu"
                assert case["total"] == 4
                assert len(case["rows"]) == 4
                assert {len(row["arguments"]) for row in case["rows"]} == {width}
                assert {
                    row["arguments"][7]["value"] >> 24 for row in case["rows"]
                } == {track_type}
                expected = 0x100 if track_type == 0x01 else 0
                assert {row["arguments"][10]["value"] for row in case["rows"]} == {
                    expected
                }

            for family, populated_total in (("root", 20), ("search", 10)):
                empty = cases[f"type-00--{family}"]
                populated = cases[f"type-01--{family}"]
                assert empty["outcome"] == "menu"
                assert empty["total"] == 0
                assert empty["rows"] == []
                assert populated["outcome"] == "menu"
                assert populated["total"] == populated_total
                assert len(populated["rows"]) == populated_total
                assert {len(row["arguments"]) for row in populated["rows"]} == {
                    width
                }

        assert len(set(behavior_hashes[setup].values())) == 1

    reference = MODELS[0]
    extended = by_setup["extended"][reference]
    legacy = by_setup["legacy"][reference]
    for case_id, extended_case in extended.items():
        legacy_case = legacy[case_id]
        assert legacy_case["outcome"] == extended_case["outcome"]
        assert legacy_case["total"] == extended_case["total"]
        assert len(legacy_case["rows"]) == len(extended_case["rows"])

        for legacy_row, extended_row in zip(
            row_values(legacy_case), row_values(extended_case), strict=True
        ):
            assert legacy_row == extended_row[:12]

    report = {
        "schema_version": 1,
        "product": "rekordbox 7.2.19",
        "models": list(MODELS),
        "setups": {setup: {"row_width": width} for setup, width in SETUPS.items()},
        "observed": {
            "goldens": len(MODELS) * len(SETUPS),
            "cases_per_golden": 16,
            "case_executions": len(MODELS) * len(SETUPS) * 16,
            "immediate_repeat_executions": len(MODELS) * len(SETUPS) * 16,
            "identical_behavior_within_each_setup": True,
            "legacy_rows_are_extended_prefix": True,
            "extended_behavior_sha256": next(
                iter(behavior_hashes["extended"].values())
            ),
            "legacy_behavior_sha256": next(iter(behavior_hashes["legacy"].values())),
            "pre_header_timeout_types": ["0x03", "0x04"],
            "root_search_populated_type": "0x01",
            "argument_7_high_byte": "track type on hierarchy leaf",
            "argument_10_hot_cue_auto_load_type": "0x01",
        },
        "artifacts": {
            "generator_sha256": sha256(
                CONFORMANCE / "generate_context_device_setup_suites.py"
            ),
            "recorder_sha256": sha256(
                CONFORMANCE / "record_context_device_setup_matrix.sh"
            ),
            "extended_suite_sha256": sha256(
                CONFORMANCE / "suites/context-device-setup-extended.json"
            ),
            "legacy_suite_sha256": sha256(
                CONFORMANCE / "suites/context-device-setup-legacy.json"
            ),
            "fixture_fingerprint": load(MANIFEST)["fixture_fingerprint"],
            "golden_sha256": golden_hashes,
            "behavior_sha256": behavior_hashes,
        },
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(OUTPUT)


if __name__ == "__main__":
    main()
