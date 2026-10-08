#!/usr/bin/env python3
"""Validate and summarize the real-Rekordbox smart-rule matrix."""

from __future__ import annotations

import json
from pathlib import Path

from summarize_search_oracle import load, sha256, validate


ROOT = Path(__file__).resolve().parent.parent
CONFORMANCE = ROOT / "conformance"
SUITE = CONFORMANCE / "suites/smart-rule-matrix.json"
GOLDEN = CONFORMANCE / "goldens/rekordbox-7.2.19/xdj-rx3/smart-rule-matrix.json"
MANIFEST = CONFORMANCE / "fixtures/generated/smart-rule-matrix/manifest.json"
RESULT = CONFORMANCE / "results/rbxport/c144f19+tree.80e87ec8aace/summary.json"


def item_ids(case: dict[str, object]) -> list[int]:
    return [row["arguments"][1]["value"] for row in case["rows"]]


def main() -> None:
    cases = validate(SUITE, GOLDEN, MANIFEST)
    manifest = load(MANIFEST)
    tracks = manifest["ids"]
    all_tracks = [tracks[f"track.{name}"] for name in (
        "first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth"
    )]
    house = all_tracks[::2]
    techno = all_tracks[1::2]

    genre_expected = {
        1: house,
        2: techno,
        3: [],
        4: [],
        5: [],
        6: [],
        7: [],
        8: house,
        9: techno,
        10: all_tracks,
        11: techno,
    }
    bpm_decimal_expected = {
        1: [],
        2: all_tracks,
        3: all_tracks,
        4: [],
        5: [],
        6: [],
        7: [],
        8: [],
        9: [],
        10: [],
        11: [],
    }
    for operator, expected in genre_expected.items():
        assert item_ids(cases[f"genre-operator-{operator:02}"]) == expected
    for operator, expected in bpm_decimal_expected.items():
        assert item_ids(cases[f"bpm-operator-{operator:02}"]) == expected

    assert item_ids(cases["logic-all"]) == house
    assert item_ids(cases["logic-any"]) == all_tracks
    assert item_ids(cases["nested-all"]) == all_tracks[3:6]
    assert item_ids(cases["nested-any"]) == all_tracks
    for case_id in (
        "empty-all",
        "empty-any",
        "unknown-operator",
        "unknown-property",
        "condition-outside-node",
    ):
        assert item_ids(cases[case_id]) == []
    for case_id in (
        "two-roots",
        "missing-logical-operator",
        "logical-operator-zero",
        "logical-operator-three",
        "automatic-update-zero",
        "missing-automatic-update",
        "mismatched-id",
        "missing-id",
    ):
        assert item_ids(cases[case_id]) == house

    replay = load(RESULT)
    smart = next(suite for suite in replay["suites"] if suite["suite"] == "smart-rule-matrix")
    assert smart["cases"] == 39
    assert len(smart["exact_cases"]) == 19
    assert len(smart["same_outcome_total_row_count_cases"]) == 19

    report = {
        "format": "rekordbox-link-export-smart-rule-matrix-v1",
        "oracle": {
            "cases": 39,
            "golden_sha256": sha256(GOLDEN),
            "suite_sha256": sha256(SUITE),
            "immediate_repeat_verified": True,
        },
        "fixture": {
            "profile": "smart-rule-matrix",
            "database_sha256": manifest["database_sha256"],
            "fingerprint": manifest["fixture_fingerprint"],
            "tracks": 8,
            "smart_playlists": 39,
        },
        "behavior": {
            "text_operator_results": {
                str(operator): expected for operator, expected in genre_expected.items()
            },
            "decimal_bpm_operator_results": {
                str(operator): expected
                for operator, expected in bpm_decimal_expected.items()
            },
            "bpm_uses_stored_integer_scale": True,
            "nested_nodes_are_ignored": True,
            "nested_case_results_come_from_direct_siblings": True,
            "empty_all_and_any_return_empty": True,
            "unknown_operator_and_property_return_empty": True,
            "condition_outside_root_returns_empty": True,
            "second_root_is_ignored": True,
            "missing_or_unknown_root_logic_defaults_to_all": True,
            "automatic_update_does_not_change_results": True,
            "root_id_does_not_change_results": True,
        },
        "rbxport": {
            "version": replay["backend_version"],
            "cases": smart["cases"],
            "exact": len(smart["exact_cases"]),
            "same_outcome_total_row_count": len(
                smart["same_outcome_total_row_count_cases"]
            ),
            "exact_cases_are_empty_result_controls": True,
        },
    }
    output = ROOT / "data/experiments/smart-rule-matrix/summary.json"
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(output)


if __name__ == "__main__":
    main()
