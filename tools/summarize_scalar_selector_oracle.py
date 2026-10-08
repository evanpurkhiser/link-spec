#!/usr/bin/env python3
"""Validate and summarize Rating, Bitrate, and Color selector behavior."""

from __future__ import annotations

import json
from pathlib import Path

from summarize_search_oracle import load, labels, sha256, validate


ROOT = Path(__file__).resolve().parent.parent
CONFORMANCE = ROOT / "conformance"
GOLDENS = CONFORMANCE / "goldens/rekordbox-7.2.19/xdj-rx3"
RESULT = CONFORMANCE / "results/rbxport/c144f19+tree.80e87ec8aace/summary.json"


def selectors(case: dict[str, object]) -> list[int]:
    return [row["arguments"][1]["value"] for row in case["rows"]]


def main() -> None:
    drilldowns = validate(
        CONFORMANCE / "suites/scalar-selector-drilldowns.json",
        GOLDENS / "scalar-selector-drilldowns.json",
        CONFORMANCE / "fixtures/generated/full/manifest.json",
    )
    boundaries = validate(
        CONFORMANCE / "suites/scalar-selector-boundaries.json",
        GOLDENS / "scalar-selector-boundaries.json",
        CONFORMANCE / "fixtures/generated/scalar-boundaries/manifest.json",
    )

    expected_ratings = {
        0: ["Alpha One", "Unknown Album"],
        1: ["Alpha Two", "Maximum Ordinary"],
        2: ["Beta One"],
        3: ["Boundary Fifty Nine"],
        4: ["Boundary Sixty"],
        5: ["Unicode Ω Search"],
    }
    for value, expected in expected_ratings.items():
        assert labels(drilldowns[f"rating-{value}"]) == expected
    for case_id in ("rating-6", "rating-99", "rating-u32-max"):
        assert drilldowns[case_id]["total"] == 0

    expected_bitrates = {
        0: "Alpha One",
        32: "Alpha Two",
        128: "Beta One",
        160: "Boundary Fifty Nine",
        192: "Boundary Sixty",
        256: "Unicode Ω Search",
        320: "Unknown Album",
        1411: "Maximum Ordinary",
    }
    for value, expected in expected_bitrates.items():
        assert labels(drilldowns[f"bitrate-{value}"]) == [expected]
    for case_id in ("bitrate-1", "bitrate-i32-max", "bitrate-u32-max"):
        assert drilldowns[case_id]["total"] == 0

    for value, expected in enumerate(
        (
            "Alpha One",
            "Alpha Two",
            "Beta One",
            "Boundary Fifty Nine",
            "Boundary Sixty",
            "Unicode Ω Search",
            "Unknown Album",
            "Maximum Ordinary",
        ),
        start=1,
    ):
        assert labels(drilldowns[f"color-{value}"]) == [expected]
    for case_id in ("color-0", "color-9", "color-999999", "color-u32-max"):
        assert drilldowns[case_id]["total"] == 0

    assert selectors(boundaries["rating-root"]) == [5, 4, 3, 1, 0]
    assert labels(boundaries["rating-99"]) == ["Beta One"]
    assert selectors(boundaries["bitrate-root"]) == [1411, 320, 256, 192, 128, 32, 0]
    assert boundaries["bitrate-i32-max"]["total"] == 0
    assert selectors(boundaries["color-root"]) == list(range(1, 9))
    assert labels(boundaries["color-0"]) == ["Alpha One"]
    assert boundaries["color-999999"]["total"] == 0

    replay = load(RESULT)
    replay_suites = {
        suite["suite"]: suite
        for suite in replay["suites"]
        if suite["suite"].startswith("scalar-selector")
    }
    assert replay_suites.keys() == {
        "scalar-selector-drilldowns",
        "scalar-selector-boundaries",
    }
    assert sum(suite["cases"] for suite in replay_suites.values()) == 39

    report = {
        "format": "rekordbox-link-export-scalar-selectors-v1",
        "oracle": {
            "goldens": 2,
            "cases": 39,
            "drilldowns_sha256": sha256(
                GOLDENS / "scalar-selector-drilldowns.json"
            ),
            "boundaries_sha256": sha256(
                GOLDENS / "scalar-selector-boundaries.json"
            ),
        },
        "behavior": {
            "rating_advertised_domain": [0, 1, 2, 3, 4, 5],
            "rating_direct_out_of_domain_matches": 99,
            "bitrate_zero_is_selectable": True,
            "bitrate_i32_max_matches_database_row": False,
            "color_advertised_domain": list(range(1, 9)),
            "color_zero_directly_selects_unassigned": True,
            "dangling_color_directly_selects": False,
        },
        "fixture": {
            "profile": "scalar-boundaries",
            "fingerprint": load(
                CONFORMANCE / "fixtures/generated/scalar-boundaries/manifest.json"
            )["fixture_fingerprint"],
        },
        "rbxport": {
            "version": replay["backend_version"],
            "cases": 39,
            "exact": sum(len(suite["exact_cases"]) for suite in replay_suites.values()),
            "same_outcome_total_row_count": sum(
                len(suite["same_outcome_total_row_count_cases"])
                for suite in replay_suites.values()
            ),
        },
    }
    output = ROOT / "data/experiments/scalar-selectors/summary.json"
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(output)


if __name__ == "__main__":
    main()
