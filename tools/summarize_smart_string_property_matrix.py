#!/usr/bin/env python3
"""Validate and summarize cross-property SmartList string behavior."""

from __future__ import annotations

import json
from pathlib import Path

from summarize_search_oracle import load, sha256, validate


ROOT = Path(__file__).resolve().parent.parent
CONFORMANCE = ROOT / "conformance"
SUITE = CONFORMANCE / "suites/smart-string-property-matrix.json"
GOLDEN = (
    CONFORMANCE
    / "goldens/rekordbox-7.2.19/xdj-rx3/smart-string-property-matrix.json"
)
MANIFEST = (
    CONFORMANCE / "fixtures/generated/smart-string-property-matrix/manifest.json"
)
RESULT = CONFORMANCE / "results/rbxport/c144f19+tree.80e87ec8aace/summary.json"
PROPERTIES = (
    "artist",
    "album",
    "album-artist",
    "original-artist",
    "producer",
    "genre",
    "key",
    "label",
    "remixed-by",
    "comments",
    "file-name",
    "mix-name",
    "name",
)
RULES = (
    "alpha-equal",
    "alpha-not-equal",
    "alpha-contains",
    "alpha-not-contains",
    "alpha-starts",
    "alpha-ends",
    "empty-equal",
    "empty-not-equal",
)


def item_ids(case: dict[str, object]) -> list[int]:
    return [row["arguments"][1]["value"] for row in case["rows"]]


def expected_cases(
    suite: dict[str, object], manifest: dict[str, object]
) -> dict[str, list[int]]:
    ids = manifest["ids"]
    return {
        case["id"]: [
            ids[value.removeprefix("$fixture.")]
            for value in case["expect"]["item_ids"]
        ]
        for case in suite["cases"]
    }


def main() -> None:
    cases = validate(SUITE, GOLDEN, MANIFEST)
    suite = load(SUITE)
    manifest = load(MANIFEST)
    expected = expected_cases(suite, manifest)
    assert set(cases) == set(expected)
    for case_id, ids in expected.items():
        assert item_ids(cases[case_id]) == ids

    reference = {rule: expected[f"comments-{rule}"] for rule in RULES}
    for property_name in PROPERTIES:
        for rule, ids in reference.items():
            assert expected[f"{property_name}-{rule}"] == ids

    assert reference == {
        "alpha-equal": [13001, 13002, 13003, 13004, 13005],
        "alpha-not-equal": [13006, 13007, 13008, 13009, 13010],
        "alpha-contains": [13001, 13002, 13003, 13004, 13005, 13006, 13007],
        "alpha-not-contains": [13008],
        "alpha-starts": [13001, 13002, 13003, 13004, 13005, 13006],
        "alpha-ends": [13001, 13002, 13003, 13004, 13005, 13007],
        "empty-equal": [13009, 13010],
        "empty-not-equal": [13001, 13002, 13003, 13004, 13005, 13006, 13007, 13008],
    }

    replay = load(RESULT)
    result = next(
        item
        for item in replay["suites"]
        if item["suite"] == "smart-string-property-matrix"
    )
    assert result["cases"] == 104
    assert result["exact_cases"] == []
    assert result["same_outcome_total_row_count_cases"] == []
    assert len(result["different_cases"]) == 104

    report = {
        "format": "rekordbox-link-export-smart-string-property-matrix-v1",
        "oracle": {
            "cases": len(expected),
            "golden_sha256": sha256(GOLDEN),
            "suite_sha256": sha256(SUITE),
            "immediate_repeat_verified": True,
        },
        "fixture": {
            "profile": "smart-string-property-matrix",
            "database_sha256": manifest["database_sha256"],
            "fingerprint": manifest["fixture_fingerprint"],
            "tracks": manifest["track_count"],
            "smart_playlists": len(expected),
        },
        "behavior": {
            "properties": list(PROPERTIES),
            "operators": {
                "1": "equals",
                "2": "not_equal",
                "8": "contains",
                "9": "not_contains",
                "10": "starts_with",
                "11": "ends_with",
            },
            "reference_case_item_ids": reference,
            "all_properties_match_reference": True,
            "empty_lookup_name_matches_empty_direct_string": True,
            "missing_lookup_matches_sql_null": True,
        },
        "rbxport": {
            "version": replay["backend_version"],
            "cases": result["cases"],
            "exact": 0,
            "same_outcome_total_row_count": 0,
            "different_cases": result["different_cases"],
        },
    }
    output = ROOT / "data/experiments/smart-string-property-matrix/summary.json"
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(output)


if __name__ == "__main__":
    main()
