#!/usr/bin/env python3
"""Validate Display Song Info packed-context behavior for status identities."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from summarize_search_oracle import load, sha256, validate


ROOT = Path(__file__).resolve().parent.parent
CONFORMANCE = ROOT / "conformance"
MANIFEST = CONFORMANCE / "fixtures/generated/full/manifest.json"
OUTPUT = ROOT / "data/experiments/packed-context/display-status-cross/summary.json"
MODELS = {
    "xdj-rx3-status": "xdj-rx3-player-11-status.json",
    "cdj-3000-status": "cdj-3000-player-1-status.json",
}
SETUPS = {"extended": 16, "legacy": 12}
PROPERTY_ORDER = [3844, 7, 2, 11, 13, 15, 10, 20, 6, 46, 35, 16, 17, 14, 40, 41]
AIO_PROPERTY_ORDER = [3844, 7, 2, 11, 13, 35, 15, 10, 20, 6, 46, 16, 17, 14, 40, 41]


def behavior_hash(path: Path) -> str:
    behavior = load(path)["behavior"]
    encoded = json.dumps(behavior, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def values(row: dict[str, object]) -> list[object]:
    return [argument["value"] for argument in row["arguments"]]


def main() -> None:
    cases_by_setup: dict[str, dict[str, dict[str, object]]] = {}
    golden_hashes: dict[str, dict[str, str]] = {}
    behavior_hashes: dict[str, dict[str, str]] = {}
    identity_hashes: dict[str, str] = {}
    mismatch_hashes: dict[str, str] = {}

    for setup, width in SETUPS.items():
        cases_by_setup[setup] = {}
        golden_hashes[setup] = {}
        behavior_hashes[setup] = {}

        for model, identity_name in MODELS.items():
            suite_name = (
                f"context-display-status-player-11-{setup}"
                if model == "xdj-rx3-status"
                else f"context-display-status-{setup}"
            )
            suite = CONFORMANCE / f"suites/{suite_name}.json"
            identity = CONFORMANCE / f"runs/{identity_name}"
            golden = (
                CONFORMANCE
                / f"goldens/rekordbox-7.2.19/{model}/context-display-status-{setup}.json"
            )
            cases = validate(suite, golden, MANIFEST)
            assert len(cases) == 7
            cases_by_setup[setup][model] = cases
            golden_hashes[setup][model] = sha256(golden)
            behavior_hashes[setup][model] = behavior_hash(golden)
            identity_hashes[model] = sha256(identity)

            identity_document = load(identity)
            assert identity_document["status_template"] != "none"

            for track_type in range(0x07):
                case = cases[f"type-{track_type:02x}--display"]
                if track_type == 0x01:
                    assert case["outcome"] == "menu"
                    assert case["total"] == 16
                    assert len(case["rows"]) == 16
                    assert {len(row["arguments"]) for row in case["rows"]} == {
                        width
                    }
                    observed_order = [
                        row["arguments"][6]["value"] for row in case["rows"]
                    ]
                    expected_order = (
                        AIO_PROPERTY_ORDER
                        if model == "xdj-rx3-status"
                        else PROPERTY_ORDER
                    )
                    assert observed_order == expected_order
                    continue

                assert case["outcome"] == "error"
                assert case["total"] == 0xFFFFFFFF
                assert case["rows"] == []
                assert len(case["header"]) == 1

        mismatch = (
            CONFORMANCE
            / "goldens/rekordbox-7.2.19/xdj-rx3-status"
            / f"context-display-status-requester-1-{setup}.json"
        )
        mismatch_cases = validate(
            CONFORMANCE / f"suites/context-display-status-{setup}.json",
            mismatch,
            MANIFEST,
        )
        mismatch_order = [
            row["arguments"][6]["value"]
            for row in mismatch_cases["type-01--display"]["rows"]
        ]
        assert mismatch_order == PROPERTY_ORDER
        mismatch_hashes[setup] = sha256(mismatch)

    for model in MODELS:
        extended = cases_by_setup["extended"][model]
        legacy = cases_by_setup["legacy"][model]
        for case_id, extended_case in extended.items():
            legacy_case = legacy[case_id]
            assert legacy_case["outcome"] == extended_case["outcome"]
            assert legacy_case["total"] == extended_case["total"]
            assert len(legacy_case["rows"]) == len(extended_case["rows"])

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
            "goldens": len(MODELS) * len(SETUPS),
            "cases_per_golden": 7,
            "case_executions": len(MODELS) * len(SETUPS) * 7,
            "immediate_repeat_executions": len(MODELS) * len(SETUPS) * 7,
            "successful_track_type": "0x01",
            "successful_total": 16,
            "error_track_types": ["0x00", "0x02", "0x03", "0x04", "0x05", "0x06"],
            "error_total": "0xffffffff",
            "property_order": PROPERTY_ORDER,
            "aio_property_order": AIO_PROPERTY_ORDER,
            "requester_1_rx3_status_uses_non_aio_order": True,
            "aio_classification_is_keyed_by_requester_player": True,
            "legacy_rows_are_extended_prefix": True,
            "extended_behavior_sha256": next(
                iter(behavior_hashes["extended"].values())
            ),
            "legacy_behavior_sha256": next(iter(behavior_hashes["legacy"].values())),
        },
        "artifacts": {
            "generator_sha256": sha256(
                CONFORMANCE / "generate_context_display_status_suites.py"
            ),
            "recorder_sha256": sha256(
                CONFORMANCE / "record_context_display_status_matrix.sh"
            ),
            "suite_sha256": {
                setup: {
                    "player_1": sha256(
                        CONFORMANCE / f"suites/context-display-status-{setup}.json"
                    ),
                    "player_11": sha256(
                        CONFORMANCE
                        / f"suites/context-display-status-player-11-{setup}.json"
                    ),
                }
                for setup in SETUPS
            },
            "identity_sha256": identity_hashes,
            "fixture_fingerprint": load(MANIFEST)["fixture_fingerprint"],
            "golden_sha256": golden_hashes,
            "requester_1_rx3_mismatch_golden_sha256": mismatch_hashes,
            "behavior_sha256": behavior_hashes,
        },
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(OUTPUT)


if __name__ == "__main__":
    main()
