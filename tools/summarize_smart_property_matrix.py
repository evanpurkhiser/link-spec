#!/usr/bin/env python3
"""Validate and summarize the live SmartList property vocabulary oracle."""

from __future__ import annotations

import json
from pathlib import Path

from summarize_search_oracle import load, sha256, validate


ROOT = Path(__file__).resolve().parent.parent
CONFORMANCE = ROOT / "conformance"
SUITE = CONFORMANCE / "suites/smart-property-matrix.json"
GOLDEN = CONFORMANCE / "goldens/rekordbox-7.2.19/xdj-rx3/smart-property-matrix.json"
MANIFEST = CONFORMANCE / "fixtures/generated/smart-property-matrix/manifest.json"
RESULT = CONFORMANCE / "results/rbxport/c144f19+tree.80e87ec8aace/summary.json"


def item_ids(case: dict[str, object]) -> list[int]:
    return [row["arguments"][1]["value"] for row in case["rows"]]


def main() -> None:
    cases = validate(SUITE, GOLDEN, MANIFEST)
    manifest = load(MANIFEST)

    expected = {
        "artist": [10001, 10002, 10003, 10004, 10005],
        "album": [10001, 10003, 10004],
        "album-artist": [10001, 10002, 10003, 10004, 10005],
        "original-artist": list(range(10001, 10009)),
        "bpm": [10004],
        "grouping": [10004],
        "comments": [10004],
        "producer": [10001, 10003, 10005, 10007],
        "stock-date": [10004],
        "date-created-field": [10004],
        "date-created-audit": [],
        "counter": [10004],
        "file-name": [10004],
        "genre": [10001, 10003, 10005, 10007],
        "key": [10001, 10003, 10005, 10007],
        "label": [10001, 10003, 10005, 10007],
        "mix-name": [10004],
        "my-tag-warmup-raw": [10001, 10002],
        "my-tag-warmup-signed": [],
        "my-tag-vocal-raw": [10001, 10003],
        "my-tag-vocal-signed": [],
        "rating": [10004],
        "date-released": [10004],
        "remixed-by": list(range(10001, 10009)),
        "duration": [10004],
        "name": [10004],
        "year": [10004],
        "alias-title": [],
        "alias-color": [],
        "alias-play-count": [],
        "alias-remixer": [],
        "alias-composer": [],
        "alias-filename-lowercase": [10004],
    }
    assert set(cases) == set(expected)
    for case_id, ids in expected.items():
        assert item_ids(cases[case_id]) == ids

    replay = load(RESULT)
    prop = next(
        suite for suite in replay["suites"] if suite["suite"] == "smart-property-matrix"
    )
    empty_controls = [case_id for case_id, ids in expected.items() if not ids]
    nonempty = [case_id for case_id, ids in expected.items() if ids]
    assert prop["cases"] == 33
    assert prop["exact_cases"] == empty_controls
    assert prop["same_outcome_total_row_count_cases"] == empty_controls
    assert prop["different_cases"] == nonempty

    report = {
        "format": "rekordbox-link-export-smart-property-matrix-v1",
        "oracle": {
            "cases": len(expected),
            "golden_sha256": sha256(GOLDEN),
            "suite_sha256": sha256(SUITE),
            "immediate_repeat_verified": True,
        },
        "fixture": {
            "profile": "smart-property-matrix",
            "database_sha256": manifest["database_sha256"],
            "fingerprint": manifest["fixture_fingerprint"],
            "tracks": 8,
            "smart_playlists": 33,
        },
        "behavior": {
            "case_item_ids": expected,
            "date_created_uses_track_field": True,
            "date_created_uses_audit_created_at": False,
            "mix_name_uses_subtitle": True,
            "my_tag_raw_positive_id_matches": True,
            "my_tag_signed_32_bit_id_matches": False,
            "lowercase_filename_alias_matches": True,
            "unsupported_aliases": [
                "title",
                "color",
                "playCount",
                "remixer",
                "composer",
            ],
        },
        "rbxport": {
            "version": replay["backend_version"],
            "cases": prop["cases"],
            "exact": len(prop["exact_cases"]),
            "same_outcome_total_row_count": len(
                prop["same_outcome_total_row_count_cases"]
            ),
            "exact_cases": prop["exact_cases"],
            "nonempty_oracle_cases_returned_empty": nonempty,
        },
    }
    output = ROOT / "data/experiments/smart-property-matrix/summary.json"
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(output)


if __name__ == "__main__":
    main()
