#!/usr/bin/env python3
"""Validate and summarize stored-scale SmartList numeric behavior."""

from __future__ import annotations

import json
from pathlib import Path

from summarize_search_oracle import load, sha256, validate


ROOT = Path(__file__).resolve().parent.parent
CONFORMANCE = ROOT / "conformance"
SUITE = CONFORMANCE / "suites/smart-numeric-matrix.json"
GOLDEN = CONFORMANCE / "goldens/rekordbox-7.2.19/xdj-rx3/smart-numeric-matrix.json"
MANIFEST = CONFORMANCE / "fixtures/generated/smart-numeric-matrix/manifest.json"
RESULT = CONFORMANCE / "results/rbxport/c144f19+tree.80e87ec8aace/summary.json"


def item_ids(case: dict[str, object]) -> list[int]:
    return [row["arguments"][1]["value"] for row in case["rows"]]


def main() -> None:
    cases = validate(SUITE, GOLDEN, MANIFEST)
    manifest = load(MANIFEST)
    ids = manifest["ids"]
    all_tracks = [ids[f"track.{name}"] for name in (
        "first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth"
    )]

    expected = {
        "bpm": ([10004], [10005, 10006, 10007, 10008], [10001, 10002, 10003], [10002, 10003, 10004, 10005, 10006]),
        "rating": ([10004], [10005, 10006], [10001, 10002, 10003, 10007, 10008], [10002, 10003, 10004, 10005, 10008]),
        "play-count": ([10004], [10005, 10006, 10007, 10008], [10001, 10002, 10003], [10003, 10004, 10005, 10006]),
        "duration": ([10004], [10005, 10006, 10007, 10008], [10001, 10002, 10003], [10002, 10003, 10004, 10005, 10006]),
        "year": ([10004], [10005, 10006, 10007, 10008], [10001, 10002, 10003], [10002, 10003, 10004, 10005, 10006]),
    }
    for property_name, (equal, greater, less, in_range) in expected.items():
        assert item_ids(cases[f"{property_name}-operator-01"]) == equal
        assert item_ids(cases[f"{property_name}-operator-02"]) == [
            track for track in all_tracks if track not in equal
        ]
        assert item_ids(cases[f"{property_name}-operator-03"]) == greater
        assert item_ids(cases[f"{property_name}-operator-04"]) == less
        assert item_ids(cases[f"{property_name}-operator-05"]) == in_range
        assert item_ids(cases[f"{property_name}-reversed-range"]) == []

    zero_rows = {
        "bpm": [],
        "rating": [10001, 10007],
        "play-count": [10001],
        "duration": [],
        "year": [10001],
    }
    for property_name, zero in zero_rows.items():
        assert item_ids(cases[f"{property_name}-empty-equal"]) == zero
        assert item_ids(cases[f"{property_name}-invalid-equal"]) == zero
        complement = [track for track in all_tracks if track not in zero]
        assert item_ids(cases[f"{property_name}-empty-not-equal"]) == complement
        assert item_ids(cases[f"{property_name}-invalid-not-equal"]) == complement

    assert item_ids(cases["bpm-negative-equal"]) == []
    assert item_ids(cases["bpm-negative-not-equal"]) == all_tracks
    assert item_ids(cases["bpm-negative-greater"]) == all_tracks
    assert item_ids(cases["bpm-negative-less"]) == []
    assert item_ids(cases["bpm-negative-range"]) == []
    assert item_ids(cases["bpm-overflow-equal"]) == []
    assert item_ids(cases["bpm-overflow-not-equal"]) == all_tracks
    assert item_ids(cases["bpm-overflow-greater"]) == []
    assert item_ids(cases["bpm-overflow-less"]) == all_tracks
    assert item_ids(cases["bpm-overflow-range"]) == []

    replay = load(RESULT)
    numeric = next(
        suite for suite in replay["suites"] if suite["suite"] == "smart-numeric-matrix"
    )
    assert numeric["cases"] == 60
    assert len(numeric["exact_cases"]) == 15
    assert len(numeric["same_outcome_total_row_count_cases"]) == 15

    report = {
        "format": "rekordbox-link-export-smart-numeric-matrix-v1",
        "oracle": {
            "cases": 60,
            "golden_sha256": sha256(GOLDEN),
            "suite_sha256": sha256(SUITE),
            "immediate_repeat_verified": True,
        },
        "fixture": {
            "profile": "smart-numeric-matrix",
            "database_sha256": manifest["database_sha256"],
            "fingerprint": manifest["fixture_fingerprint"],
            "tracks": 8,
            "smart_playlists": 60,
        },
        "behavior": {
            "operators_1_through_5": {
                "1": "equal",
                "2": "not_equal",
                "3": "greater_than_exclusive",
                "4": "less_than_exclusive",
                "5": "inclusive_ordered_range",
            },
            "reversed_ranges_return_empty": True,
            "empty_numeric_text_coerces_to_zero": True,
            "invalid_numeric_text_coerces_to_zero": True,
            "negative_threshold_preserves_sign": True,
            "values_above_signed_32_bit_remain_positive": True,
            "zero_value_rows": zero_rows,
        },
        "rbxport": {
            "version": replay["backend_version"],
            "cases": numeric["cases"],
            "exact": len(numeric["exact_cases"]),
            "same_outcome_total_row_count": len(
                numeric["same_outcome_total_row_count_cases"]
            ),
            "exact_cases_are_empty_result_controls": True,
        },
    }
    output = ROOT / "data/experiments/smart-numeric-matrix/summary.json"
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(output)


if __name__ == "__main__":
    main()
