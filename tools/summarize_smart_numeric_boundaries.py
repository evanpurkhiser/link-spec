#!/usr/bin/env python3
"""Validate and summarize SmartList numeric database conversion boundaries."""

from __future__ import annotations

import json
from pathlib import Path

from summarize_search_oracle import load, sha256, validate


ROOT = Path(__file__).resolve().parent.parent
CONFORMANCE = ROOT / "conformance"
SUITE = CONFORMANCE / "suites/smart-numeric-boundaries.json"
GOLDEN = CONFORMANCE / "goldens/rekordbox-7.2.19/xdj-rx3/smart-numeric-boundaries.json"
MANIFEST = CONFORMANCE / "fixtures/generated/smart-numeric-boundaries/manifest.json"
RESULT = CONFORMANCE / "results/rbxport/c144f19+tree.80e87ec8aace/summary.json"
PROPERTIES = ("bpm", "rating", "play-count", "duration", "year")
TRACKS = {
    35_001: "null",
    35_002: "zero",
    35_003: "half",
    35_004: "one_half",
    35_005: "minus_half",
    35_006: "minus_one",
    35_007: "int32_max",
    35_008: "int32_plus_one",
    35_009: "uint32_max",
    35_010: "uint32_plus_one",
}


def item_names(case: dict[str, object]) -> list[str]:
    return [TRACKS[row["arguments"][1]["value"]] for row in case["rows"]]


def main() -> None:
    cases = validate(SUITE, GOLDEN, MANIFEST)
    manifest = load(MANIFEST)
    observed = {
        property_name: {
            case_id.removeprefix(f"{property_name}-"): item_names(case)
            for case_id, case in cases.items()
            if case_id.startswith(f"{property_name}-")
        }
        for property_name in PROPERTIES
    }
    assert all(len(results) == 20 for results in observed.values())

    for results in observed.values():
        assert results["equal-half"] == results["equal-zero"]
        assert results["not-equal-half"] == results["not-equal-zero"]
        assert results["greater-half"] == results["greater-zero"]
        assert results["less-half"] == results["less-zero"]
        assert results["missing-left-equal"] == results["equal-zero"]
        assert results["missing-left-not-equal"] == results["not-equal-zero"]
        assert results["range-both-missing"] == results["equal-zero"]

    assert observed["bpm"]["equal-zero"] == [
        "null", "zero", "half", "minus_half", "uint32_plus_one"
    ]
    assert observed["bpm"]["not-equal-zero"] == ["one_half", "int32_max"]
    assert observed["bpm"]["equal-int32-max"] == ["int32_max"]
    for variant in (
        "equal-int32-plus-one",
        "equal-uint32-max",
        "equal-uint32-plus-one",
    ):
        assert observed["bpm"][variant] == ["int32_max"]

    assert observed["rating"]["equal-zero"] == [
        "null", "zero", "half", "minus_half", "int32_plus_one", "uint32_plus_one"
    ]
    assert observed["rating"]["greater-zero"] == ["one_half"]
    assert observed["rating"]["less-zero"] == [
        "minus_one", "int32_max", "uint32_max"
    ]

    unsigned_zero = [
        "null", "zero", "half", "minus_half", "int32_plus_one", "uint32_plus_one"
    ]
    unsigned_positive = ["one_half", "minus_one", "int32_max", "uint32_max"]
    for property_name in ("play-count", "duration", "year"):
        assert observed[property_name]["equal-zero"] == unsigned_zero
        assert observed[property_name]["greater-zero"] == unsigned_positive
        assert observed[property_name]["less-zero"] == []

    replay = load(RESULT)
    result = next(
        entry for entry in replay["suites"]
        if entry["suite"] == "smart-numeric-boundaries"
    )
    assert result["cases"] == 100
    assert len(result["exact_cases"]) == 29
    assert len(result["same_outcome_total_row_count_cases"]) == 29

    report = {
        "format": "rekordbox-link-export-smart-numeric-boundaries-v1",
        "oracle": {
            "cases": len(cases),
            "golden_sha256": sha256(GOLDEN),
            "suite_sha256": sha256(SUITE),
            "immediate_repeat_verified": True,
        },
        "fixture": {
            "profile": manifest["profile"],
            "database_sha256": manifest["database_sha256"],
            "fingerprint": manifest["fixture_fingerprint"],
            "tracks": manifest["track_count"],
            "sqlite_storage_values": {
                "null": None,
                "zero": 0,
                "half": 0.5,
                "one_half": 1.5,
                "minus_half": -0.5,
                "minus_one": -1,
                "int32_max": 2_147_483_647,
                "int32_plus_one": 2_147_483_648,
                "uint32_max": 4_294_967_295,
                "uint32_plus_one": 4_294_967_296,
            },
        },
        "behavior": {
            "rule_fractional_half_coerces_to_zero": True,
            "missing_value_left_coerces_to_zero": True,
            "missing_range_endpoint_coerces_to_zero": True,
            "property_results": observed,
            "conversion_domains": {
                "bpm": "signed integer with negative-domain row exclusion",
                "rating": "signed low-byte behavior",
                "play_count_duration_year": "shared unsigned-like behavior",
            },
        },
        "rbxport": {
            "version": replay["backend_version"],
            "cases": result["cases"],
            "exact": len(result["exact_cases"]),
            "same_outcome_total_row_count": len(
                result["same_outcome_total_row_count_cases"]
            ),
            "different": len(result["different_cases"]),
        },
    }
    output = ROOT / "data/experiments/smart-numeric-boundaries/summary.json"
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(output)


if __name__ == "__main__":
    main()
