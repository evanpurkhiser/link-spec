#!/usr/bin/env python3
"""Validate and summarize relative-date SmartList behavior."""

from __future__ import annotations

import json
from pathlib import Path

from summarize_search_oracle import load, sha256, validate


ROOT = Path(__file__).resolve().parent.parent
CONFORMANCE = ROOT / "conformance"
SUITE = CONFORMANCE / "suites/smart-relative-date-matrix.json"
GOLDEN = (
    CONFORMANCE
    / "goldens/rekordbox-7.2.19/xdj-rx3/smart-relative-date-matrix.json"
)
MANIFEST = (
    CONFORMANCE / "fixtures/generated/smart-relative-date-matrix/manifest.json"
)
CLOCK_LOG = ROOT / "data/experiments/smart-relative-date-matrix/clock.log"
DISASSEMBLY = ROOT / "data/static-analysis/smart-condition-evaluator.disasm.txt"
RESULT = CONFORMANCE / "results/rbxport/c144f19+tree.80e87ec8aace/summary.json"


def item_ids(case: dict[str, object]) -> list[int]:
    return [row["arguments"][1]["value"] for row in case["rows"]]


def add_pair(
    expected: dict[str, list[int]],
    prefix: str,
    recent: list[int],
    older: list[int],
) -> None:
    expected[f"{prefix}-operator-06"] = recent
    expected[f"{prefix}-operator-07"] = older


def expected_cases() -> dict[str, list[int]]:
    today = [10001, 10008]
    before_today = [10002, 10003, 10004, 10005, 10006, 10007]
    month = [10001, 10002, 10003, 10004, 10008]
    before_month = [10005, 10006, 10007]
    expected: dict[str, list[int]] = {}

    for property_name in ("stock-date", "date-created", "date-released"):
        for unit in ("day", "week", "year"):
            add_pair(expected, f"{property_name}-{unit}", today, before_today)
        add_pair(expected, f"{property_name}-month", month, before_month)

    for unit in ("days", "weeks", "months", "years", "empty", "unknown"):
        add_pair(expected, f"stock-date-unit-{unit}", today, before_today)
    add_pair(
        expected,
        "stock-date-unit-uppercase-month",
        month,
        before_month,
    )

    for count in ("zero", "negative", "blank", "invalid", "fractional"):
        add_pair(expected, f"stock-date-count-{count}", today, before_today)
    add_pair(
        expected,
        "stock-date-count-two",
        [10001, 10002, 10008],
        [10003, 10004, 10005, 10006, 10007],
    )
    add_pair(
        expected,
        "stock-date-count-thirty-one",
        [10001, 10002, 10003, 10008],
        [10004, 10005, 10006, 10007],
    )
    add_pair(
        expected,
        "stock-date-month-count-two",
        [10001, 10002, 10003, 10004, 10005, 10008],
        [10006, 10007],
    )
    add_pair(expected, "stock-date-right-31", today, before_today)

    return expected


def main() -> None:
    cases = validate(SUITE, GOLDEN, MANIFEST)
    manifest = load(MANIFEST)
    expected = expected_cases()
    assert set(cases) == set(expected)
    for case_id, ids in expected.items():
        assert item_ids(cases[case_id]) == ids

    clock_log = CLOCK_LOG.read_text()
    assert "2032-03-31T12:00:00" in clock_log
    assert "=== restore host clock ===" in clock_log
    assert "fixtures/generated/play-paths" in clock_log

    replay = load(RESULT)
    relative = next(
        suite
        for suite in replay["suites"]
        if suite["suite"] == "smart-relative-date-matrix"
    )
    assert relative["cases"] == 56
    assert relative["exact_cases"] == []
    assert relative["same_outcome_total_row_count_cases"] == []
    assert set(relative["different_cases"]) == set(expected)

    report = {
        "format": "rekordbox-link-export-smart-relative-date-matrix-v1",
        "oracle": {
            "cases": len(expected),
            "anchor": "2032-03-31T12:00:00-04:00",
            "golden_sha256": sha256(GOLDEN),
            "suite_sha256": sha256(SUITE),
            "clock_log_sha256": sha256(CLOCK_LOG),
            "immediate_repeat_verified": True,
        },
        "fixture": {
            "profile": "smart-relative-date-matrix",
            "database_sha256": manifest["database_sha256"],
            "fingerprint": manifest["fixture_fingerprint"],
            "tracks": 10,
            "smart_playlists": 56,
        },
        "static_evidence": {
            "path": str(DISASSEMBLY.relative_to(ROOT)),
            "sha256": sha256(DISASSEMBLY),
        },
        "behavior": {
            "properties": ["stockDate", "dateCreated", "dateReleased"],
            "operators": {"6": "after_lower_boundary", "7": "before_lower_boundary"},
            "case_item_ids": expected,
            "month_is_the_only_special_unit": True,
            "month_unit_is_case_insensitive": True,
            "other_units_use_day_arithmetic": True,
            "value_right_is_ignored": True,
            "future_dates_match_operator_6": True,
            "blank_and_malformed_track_dates_match_neither_operator": True,
            "zero_like_counts": [
                "zero",
                "negative",
                "blank",
                "invalid",
                "fractional",
            ],
        },
        "rbxport": {
            "version": replay["backend_version"],
            "cases": relative["cases"],
            "exact": 0,
            "same_outcome_total_row_count": 0,
            "different_cases": relative["different_cases"],
        },
    }
    output = ROOT / "data/experiments/smart-relative-date-matrix/summary.json"
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(output)


if __name__ == "__main__":
    main()
