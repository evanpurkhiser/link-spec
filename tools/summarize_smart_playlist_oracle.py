#!/usr/bin/env python3
"""Validate and summarize smart-playlist Link Export behavior."""

from __future__ import annotations

import json
from pathlib import Path

from summarize_search_oracle import load, labels, sha256, validate


ROOT = Path(__file__).resolve().parent.parent
CONFORMANCE = ROOT / "conformance"
GOLDEN = CONFORMANCE / "goldens/rekordbox-7.2.19/xdj-rx3/smart-playlists.json"
MANIFEST = CONFORMANCE / "fixtures/generated/smart-playlists/manifest.json"
RESULT = CONFORMANCE / "results/rbxport/c144f19+tree.80e87ec8aace/summary.json"


def item_ids(case: dict[str, object]) -> list[int]:
    return [row["arguments"][1]["value"] for row in case["rows"]]


def main() -> None:
    cases = validate(
        CONFORMANCE / "suites/smart-playlists.json",
        GOLDEN,
        MANIFEST,
    )
    manifest = load(MANIFEST)
    ids = manifest["ids"]
    house = ["Alpha One", "Beta One", "Boundary Sixty", "Unknown Album"]

    assert item_ids(cases["root"]) == [
        ids["playlist.folder"],
        ids["playlist.cue_analysis"],
        ids["playlist.empty"],
        ids["playlist.smart_rule_only"],
        ids["playlist.smart_contradiction"],
        ids["playlist.smart_malformed"],
        ids["playlist.ordinary_with_rule"],
        ids["playlist.smart_without_rule"],
    ]
    assert [row["arguments"][6]["value"] for row in cases["root"]["rows"]] == [
        1,
        8,
        8,
        8,
        8,
        8,
        8,
        8,
    ]
    assert labels(cases["rule-only-tracks"]) == house
    assert labels(cases["contradiction-membership-order"]) == house
    assert labels(cases["contradiction-title-sort"]) == house
    for case_id in (
        "rule-only-children",
        "contradiction-children",
        "malformed-membership",
        "malformed-children",
        "ordinary-rule-only-tracks",
        "ordinary-rule-only-children",
        "smart-without-rule-membership",
        "smart-without-rule-children",
    ):
        assert cases[case_id]["total"] == 0

    post_startup = ROOT / "data/experiments/smart-playlists/post-startup-master.db"
    assert sha256(post_startup) == manifest["database_sha256"]

    replay = load(RESULT)
    smart = next(suite for suite in replay["suites"] if suite["suite"] == "smart-playlists")
    assert smart["cases"] == 12
    assert len(smart["exact_cases"]) == 6
    assert len(smart["same_outcome_total_row_count_cases"]) == 7

    report = {
        "format": "rekordbox-link-export-smart-playlists-v1",
        "oracle": {
            "cases": 12,
            "golden_sha256": sha256(GOLDEN),
            "suite_sha256": sha256(CONFORMANCE / "suites/smart-playlists.json"),
        },
        "fixture": {
            "profile": "smart-playlists",
            "database_sha256": manifest["database_sha256"],
            "fingerprint": manifest["fixture_fingerprint"],
            "post_startup_database_unchanged": True,
        },
        "behavior": {
            "attribute_4_uses_smart_list_rule": True,
            "attribute_4_ignores_materialized_membership": True,
            "malformed_rule_returns_empty": True,
            "missing_rule_returns_empty": True,
            "attribute_0_ignores_smart_list_rule": True,
            "root_row_type_matches_ordinary_playlist": True,
            "folder_flag_controls_child_vs_track_dispatch": True,
        },
        "rbxport": {
            "version": replay["backend_version"],
            "cases": smart["cases"],
            "exact": len(smart["exact_cases"]),
            "same_outcome_total_row_count": len(
                smart["same_outcome_total_row_count_cases"]
            ),
            "uses_materialized_membership_in_link_export": True,
        },
    }
    output = ROOT / "data/experiments/smart-playlists/summary.json"
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(output)


if __name__ == "__main__":
    main()
