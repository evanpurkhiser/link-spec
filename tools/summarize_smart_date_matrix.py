#!/usr/bin/env python3
"""Validate and summarize fixed-date SmartList behavior."""

from __future__ import annotations

import json
from pathlib import Path

from summarize_search_oracle import load, sha256, validate


ROOT = Path(__file__).resolve().parent.parent
CONFORMANCE = ROOT / "conformance"
SUITE = CONFORMANCE / "suites/smart-date-matrix.json"
GOLDEN = CONFORMANCE / "goldens/rekordbox-7.2.19/xdj-rx3/smart-date-matrix.json"
MANIFEST = CONFORMANCE / "fixtures/generated/smart-date-matrix/manifest.json"
RESULT = CONFORMANCE / "results/rbxport/c144f19+tree.80e87ec8aace/summary.json"


def item_ids(case: dict[str, object]) -> list[int]:
    return [row["arguments"][1]["value"] for row in case["rows"]]


def main() -> None:
    cases = validate(SUITE, GOLDEN, MANIFEST)
    manifest = load(MANIFEST)
    properties = ("stock-date", "date-created", "date-released")
    suffixes = {
        "operator-01": [10004],
        "operator-02": [10001, 10002, 10003, 10005, 10006],
        "operator-03": [10005, 10006],
        "operator-04": [10001, 10002, 10003],
        "operator-05": [10002, 10003, 10004, 10005],
        "reversed-range": [],
        "blank-equal": [],
        "blank-not-equal": [10001, 10002, 10003, 10004, 10005, 10006],
        "invalid-equal": [],
        "invalid-not-equal": [10001, 10002, 10003, 10004, 10005, 10006],
    }
    expected = {
        f"{property_name}-{suffix}": ids
        for property_name in properties
        for suffix, ids in suffixes.items()
    }
    assert set(cases) == set(expected)
    for case_id, ids in expected.items():
        assert item_ids(cases[case_id]) == ids

    replay = load(RESULT)
    date = next(
        suite for suite in replay["suites"] if suite["suite"] == "smart-date-matrix"
    )
    empty_controls = [case_id for case_id, ids in expected.items() if not ids]
    nonempty = [case_id for case_id, ids in expected.items() if ids]
    assert date["cases"] == 30
    assert date["exact_cases"] == empty_controls
    assert date["same_outcome_total_row_count_cases"] == empty_controls
    assert date["different_cases"] == nonempty

    report = {
        "format": "rekordbox-link-export-smart-date-matrix-v1",
        "oracle": {
            "cases": len(expected),
            "golden_sha256": sha256(GOLDEN),
            "suite_sha256": sha256(SUITE),
            "immediate_repeat_verified": True,
        },
        "fixture": {
            "profile": "smart-date-matrix",
            "database_sha256": manifest["database_sha256"],
            "fingerprint": manifest["fixture_fingerprint"],
            "tracks": 8,
            "smart_playlists": 30,
        },
        "behavior": {
            "properties": list(properties),
            "operators_1_through_5": {
                "1": "equal",
                "2": "not_equal",
                "3": "greater_than_exclusive",
                "4": "less_than_exclusive",
                "5": "inclusive_ordered_range",
            },
            "case_item_ids": expected,
            "reversed_ranges_return_empty": True,
            "blank_track_dates_are_excluded_from_equal_and_not_equal": True,
            "malformed_track_dates_are_excluded_from_equal_and_not_equal": True,
        },
        "rbxport": {
            "version": replay["backend_version"],
            "cases": date["cases"],
            "exact": len(date["exact_cases"]),
            "same_outcome_total_row_count": len(
                date["same_outcome_total_row_count_cases"]
            ),
            "exact_cases": date["exact_cases"],
            "nonempty_oracle_cases_returned_empty": nonempty,
        },
    }
    output = ROOT / "data/experiments/smart-date-matrix/summary.json"
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(output)


if __name__ == "__main__":
    main()
