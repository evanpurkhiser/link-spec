#!/usr/bin/env python3
"""Validate and summarize SmartList fixed-date parsing behavior."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CONFORMANCE = ROOT / "conformance"
from summarize_search_oracle import load, sha256, validate


JAN_31_EQUIVALENTS = (
    "canonical_jan_31",
    "separator_slash",
    "separator_dot",
    "separator_space",
    "separator_letters",
    "separator_unicode",
    "separator_newline",
)
OTHER_PARSEABLE_VALUES = (
    "canonical_leap_day",
    "nonleap_feb_29",
    "leap_feb_30",
    "nonleap_feb_30",
    "nonleap_feb_31",
    "april_31",
    "month_zero",
    "month_13",
    "day_zero",
    "day_32",
    "month_99",
    "day_99",
    "letter_in_year",
)


SUITE = CONFORMANCE / "suites/smart-date-format-matrix.json"
GOLDEN = (
    CONFORMANCE
    / "goldens/rekordbox-7.2.19/xdj-rx3/smart-date-format-matrix.json"
)
MANIFEST = (
    CONFORMANCE / "fixtures/generated/smart-date-format-matrix/manifest.json"
)
DISASSEMBLY = ROOT / "data/static-analysis/smart-date-conversion.disasm.txt"
RESULT = CONFORMANCE / "results/rbxport/c144f19+tree.80e87ec8aace/summary.json"
BEFORE_SCREENSHOT = ROOT / "data/experiments/ui-debug/link-before-click.png"
AFTER_SCREENSHOT = ROOT / "data/experiments/ui-debug/link-after-click.png"
BLOCKED_SCREENSHOT = ROOT / "data/experiments/ui-debug/link-loop-live.png"


def item_ids(case: dict[str, object]) -> list[int]:
    return [row["arguments"][1]["value"] for row in case["rows"]]


def expected_cases(manifest: dict[str, object]) -> dict[str, list[int]]:
    ids = manifest["ids"]
    equivalent_ids = [
        ids[f"track.date_format.{name}"] for name in JAN_31_EQUIVALENTS
    ]
    other_ids = [
        ids[f"track.date_format.{name}"] for name in OTHER_PARSEABLE_VALUES
    ]
    properties = ("stock-date", "date-created", "date-released")
    values = (
        "canonical_jan_31",
        "canonical_leap_day",
        "canonical_epoch",
        "pre_epoch",
        "year_zero",
        "year_9999",
        "separator_slash",
        "separator_dot",
        "separator_space",
        "separator_letters",
        "separator_unicode",
        "separator_newline",
        "nonleap_feb_29",
        "leap_feb_30",
        "nonleap_feb_30",
        "nonleap_feb_31",
        "april_31",
        "month_zero",
        "month_13",
        "day_zero",
        "day_32",
        "month_99",
        "day_99",
        "single_digit_month",
        "single_digit_day",
        "five_digit_year",
        "timestamp_t",
        "timestamp_space",
        "leading_space",
        "trailing_space",
        "not_a_date",
        "ascii_letters",
        "zero_digits",
        "letter_in_year",
        "plus_year",
        "minus_year",
        "fullwidth_digits",
        "empty",
    )
    expected: dict[str, list[int]] = {}

    for property_name in properties:
        for value_name in values:
            if value_name in JAN_31_EQUIVALENTS:
                matches = equivalent_ids
            elif value_name in OTHER_PARSEABLE_VALUES:
                matches = [ids[f"track.date_format.{value_name}"]]
            else:
                matches = []

            case_id = f"{property_name}-{value_name.replace('_', '-')}-equal"
            expected[case_id] = matches

        expected[f"{property_name}-canonical-not-equal"] = other_ids

    return expected


def main() -> None:
    cases = validate(SUITE, GOLDEN, MANIFEST)
    manifest = load(MANIFEST)
    expected = expected_cases(manifest)
    assert set(cases) == set(expected)
    for case_id, ids in expected.items():
        assert item_ids(cases[case_id]) == ids

    by_suffix: dict[str, list[list[int]]] = {}
    for case_id, ids in expected.items():
        suffix = case_id.split("-", 2)[2] if case_id.startswith("stock-") else case_id
        if case_id.startswith("date-created-"):
            suffix = case_id.removeprefix("date-created-")
        elif case_id.startswith("date-released-"):
            suffix = case_id.removeprefix("date-released-")
        elif case_id.startswith("stock-date-"):
            suffix = case_id.removeprefix("stock-date-")
        by_suffix.setdefault(suffix, []).append(ids)
    assert all(len(values) == 3 for values in by_suffix.values())
    assert all(values[0] == values[1] == values[2] for values in by_suffix.values())

    replay = load(RESULT)
    date_format = next(
        suite
        for suite in replay["suites"]
        if suite["suite"] == "smart-date-format-matrix"
    )
    empty_controls = [case_id for case_id, ids in expected.items() if not ids]
    nonempty = [case_id for case_id, ids in expected.items() if ids]
    assert date_format["cases"] == 117
    assert date_format["exact_cases"] == empty_controls
    assert date_format["same_outcome_total_row_count_cases"] == empty_controls
    assert date_format["different_cases"] == nonempty

    report = {
        "format": "rekordbox-link-export-smart-date-format-matrix-v1",
        "oracle": {
            "cases": len(expected),
            "golden_sha256": sha256(GOLDEN),
            "suite_sha256": sha256(SUITE),
            "immediate_repeat_verified": True,
        },
        "fixture": {
            "profile": "smart-date-format-matrix",
            "database_sha256": manifest["database_sha256"],
            "fingerprint": manifest["fixture_fingerprint"],
            "tracks": manifest["track_count"],
            "smart_playlists": len(expected),
        },
        "static_evidence": {
            "path": str(DISASSEMBLY.relative_to(ROOT)),
            "sha256": sha256(DISASSEMBLY),
            "date_to_day_address": "0x102335b20",
            "past_month_to_day_address": "0x102336ba0",
            "past_day_to_day_address": "0x102336c60",
        },
        "ui_evidence": {
            "before_link_activation_sha256": sha256(BEFORE_SCREENSHOT),
            "after_link_activation_sha256": sha256(AFTER_SCREENSHOT),
            "mobile_library_sync_modal_sha256": sha256(BLOCKED_SCREENSHOT),
            "successful_player_number": 1,
        },
        "behavior": {
            "properties": ["stockDate", "dateCreated", "dateReleased"],
            "properties_are_identical": True,
            "accepted_input_length": 10,
            "delimiter_positions_are_ignored": [4, 7],
            "jan_31_equivalents": list(JAN_31_EQUIVALENTS),
            "other_parseable_values": list(OTHER_PARSEABLE_VALUES),
            "parseable_tracks": len(JAN_31_EQUIVALENTS)
            + len(OTHER_PARSEABLE_VALUES),
            "case_item_ids": expected,
            "nul_and_sql_null_track_values_match_neither_operator": True,
        },
        "rbxport": {
            "version": replay["backend_version"],
            "cases": date_format["cases"],
            "exact": len(date_format["exact_cases"]),
            "same_outcome_total_row_count": len(
                date_format["same_outcome_total_row_count_cases"]
            ),
            "exact_empty_controls": date_format["exact_cases"],
            "nonempty_oracle_cases_returned_empty": nonempty,
        },
    }
    output = ROOT / "data/experiments/smart-date-format-matrix/summary.json"
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(output)


if __name__ == "__main__":
    main()
