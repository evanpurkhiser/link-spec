#!/usr/bin/env python3
"""Validate and summarize persisted SmartList secondary-column behavior."""

from __future__ import annotations

import json
from pathlib import Path

from summarize_search_oracle import load, sha256, validate


ROOT = Path(__file__).resolve().parent.parent
CONFORMANCE = ROOT / "conformance"
GOLDENS = CONFORMANCE / "goldens/rekordbox-7.2.19/xdj-rx3"
RESULT = CONFORMANCE / "results/rbxport/c144f19+tree.80e87ec8aace/summary.json"
VARIANTS = (
    "multiple-secondary-selections",
    "no-secondary-selection",
    "secondary-album",
    "secondary-artist",
    "secondary-bitrate",
    "secondary-bpm",
    "secondary-color",
    "secondary-comment",
    "secondary-date-added",
    "secondary-genre",
    "secondary-key",
    "secondary-label",
    "secondary-original-artist",
    "secondary-play-count",
    "secondary-rating",
    "secondary-remixer",
    "secondary-time",
)
EXPECTED_FIRST_ROW = {
    "multiple-secondary-selections": (10001, "comment-1", 0x2304),
    "no-secondary-selection": (0, "", 0x0004),
    "secondary-album": (2001, "Album One", 0x0204),
    "secondary-artist": (1001, "Alpha Artist", 0x0704),
    "secondary-bitrate": (0, "", 0x1004),
    "secondary-bpm": (12000, "120.0 bpm - Am", 0x0D04),
    "secondary-color": (1, "Pink", 0x1404),
    "secondary-comment": (10001, "comment-1", 0x2304),
    "secondary-date-added": (10001, "2021-02-02", 0x2E04),
    "secondary-genre": (3001, "Fixture House", 0x0604),
    "secondary-key": (5001, "Am - 120.0 bpm", 0x0F04),
    "secondary-label": (4001, "Fixture Label One", 0x0E04),
    "secondary-original-artist": (1004, "Fixture Original", 0x2804),
    "secondary-play-count": (0, "", 0x2A04),
    "secondary-rating": (0, "", 0x0A04),
    "secondary-remixer": (1003, "Fixture Remixer", 0x2904),
    "secondary-time": (59, "", 0x0B04),
}


def row_values(row: dict[str, object]) -> list[object]:
    return [argument["value"] for argument in row["arguments"]]


def normalize_membership_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    normalized = json.loads(json.dumps(rows))

    for row in normalized:
        row["arguments"][9]["value"] = 0

    return sorted(normalized, key=lambda row: row["arguments"][1]["value"])


def main() -> None:
    replay = load(RESULT)
    replay_by_suite = {entry["suite"]: entry for entry in replay["suites"]}
    observed = {}

    for variant in VARIANTS:
        smart_name = f"smart-{variant}"
        smart_suite = CONFORMANCE / f"suites/generated/{smart_name}.json"
        smart_manifest = (
            CONFORMANCE / f"fixtures/generated/{smart_name}/manifest.json"
        )
        smart_golden = GOLDENS / f"{smart_name}.json"
        smart_cases = validate(smart_suite, smart_golden, smart_manifest)
        smart_case = smart_cases["tracks"]

        ordinary_cases = validate(
            CONFORMANCE / f"suites/generated/{variant}.json",
            GOLDENS / f"{variant}.json",
            CONFORMANCE / f"fixtures/generated/{variant}/manifest.json",
        )
        ordinary_case = ordinary_cases["track-rows"]

        assert smart_case["outcome"] == "menu"
        assert smart_case["total"] == 8
        assert len(smart_case["rows"]) == 8
        assert [row_values(row)[9] for row in smart_case["rows"]] == list(
            range(1, 9)
        )
        assert [row_values(row)[9] for row in ordinary_case["rows"]] == [0] * 8
        assert normalize_membership_rows(
            smart_case["rows"]
        ) == normalize_membership_rows(ordinary_case["rows"])

        first = row_values(smart_case["rows"][0])
        auxiliary, secondary, item_type = EXPECTED_FIRST_ROW[variant]
        assert (first[0], first[5], first[6]) == (
            auxiliary,
            secondary,
            item_type,
        )
        assert [row_values(row)[1] for row in smart_case["rows"]] == list(
            range(10001, 10009)
        )

        result = replay_by_suite[smart_name]
        assert result["cases"] == 1
        assert result["exact_cases"] == []
        assert result["same_outcome_total_row_count_cases"] == []
        assert result["different_cases"] == ["tracks"]

        manifest = load(smart_manifest)
        observed[variant] = {
            "auxiliary": auxiliary,
            "secondary": secondary,
            "item_type": f"0x{item_type:04x}",
            "rows_match_ordinary_collection_by_content_id_except_membership_sequence": True,
            "membership_sequence": list(range(1, 9)),
            "database_sha256": manifest["database_sha256"],
            "fixture_fingerprint": manifest["fixture_fingerprint"],
            "golden_sha256": sha256(smart_golden),
            "suite_sha256": sha256(smart_suite),
            "immediate_repeat_verified": True,
        }

    report = {
        "format": "rekordbox-link-export-smart-secondary-columns-v1",
        "oracle": {
            "configurations": len(VARIANTS),
            "cases": len(VARIANTS),
            "rows": len(VARIANTS) * 8,
            "all_immediate_repeats_verified": True,
        },
        "behavior": {
            "smart_rows_match_ordinary_collection_by_content_id_except_membership_sequence": True,
            "smart_membership_sequence": list(range(1, 9)),
            "ordinary_collection_membership_sequence": [0] * 8,
            "configurations": observed,
        },
        "rbxport": {
            "version": replay["backend_version"],
            "cases": len(VARIANTS),
            "exact": 0,
            "same_outcome_total_row_count": 0,
            "different": len(VARIANTS),
            "reason": "rbxport does not evaluate populated SmartList membership",
        },
    }
    output = ROOT / "data/experiments/smart-secondary-columns/summary.json"
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(output)


if __name__ == "__main__":
    main()
