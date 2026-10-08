#!/usr/bin/env python3
"""Validate and summarize the canonical Search oracle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CONFORMANCE = ROOT / "conformance"
GOLDENS = CONFORMANCE / "goldens/rekordbox-7.2.19/xdj-rx3"
RESULT = CONFORMANCE / "results/rbxport/c144f19+tree.80e87ec8aace/summary.json"


def load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text())


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def labels(case: dict[str, object]) -> list[str]:
    return [row["arguments"][3]["value"] for row in case["rows"]]


def validate(
    suite_path: Path,
    golden_path: Path,
    manifest_path: Path,
) -> dict[str, dict[str, object]]:
    suite = load(suite_path)
    golden = load(golden_path)
    manifest = load(manifest_path)
    provenance = golden["provenance"]

    assert provenance["backend"] == "rekordbox"
    assert provenance["backend_version"] == "7.2.19"
    assert provenance["suite_sha256"] == sha256(suite_path)
    assert provenance["fixture_database_sha256"] == manifest["database_sha256"]
    assert provenance["fixture_fingerprint"] == manifest["fixture_fingerprint"]

    declarations = {case["id"]: case for case in suite["cases"]}
    cases = {case["id"]: case for case in golden["behavior"]["cases"]}
    assert declarations.keys() == cases.keys()

    for case_id, declaration in declarations.items():
        case = cases[case_id]
        expect = declaration["expect"]
        if expect["outcome"] != "any":
            assert case["outcome"] == expect["outcome"]
        if "total" in expect:
            assert case["total"] == expect["total"]
        if "row_count" in expect:
            assert len(case["rows"]) == expect["row_count"]

    return cases


def main() -> None:
    search = validate(
        CONFORMANCE / "suites/search.json",
        GOLDENS / "search.json",
        CONFORMANCE / "fixtures/generated/full/manifest.json",
    )
    category_cases = {}
    for category in ("02", "03", "04", "21"):
        name = f"search-category-{category}-disabled"
        category_cases[category] = validate(
            CONFORMANCE / f"suites/generated/{name}.json",
            GOLDENS / f"{name}.json",
            CONFORMANCE / f"fixtures/generated/category-{category}-disabled/manifest.json",
        )
    ceiling = validate(
        CONFORMANCE / "suites/search-ceiling.json",
        GOLDENS / "search-ceiling.json",
        CONFORMANCE / "fixtures/generated/search-ceiling/manifest.json",
    )
    ceiling_manifest = load(
        CONFORMANCE / "fixtures/generated/search-ceiling/manifest.json"
    )
    text_cases = validate(
        CONFORMANCE / "suites/search-text.json",
        GOLDENS / "search-text.json",
        CONFORMANCE / "fixtures/generated/search-text/manifest.json",
    )
    text_manifest = load(CONFORMANCE / "fixtures/generated/search-text/manifest.json")
    track_cases = validate(
        CONFORMANCE / "suites/search-track.json",
        GOLDENS / "search-track.json",
        CONFORMANCE / "fixtures/generated/search-text/manifest.json",
    )
    track_ceiling = validate(
        CONFORMANCE / "suites/search-track-ceiling.json",
        GOLDENS / "search-track-ceiling.json",
        CONFORMANCE / "fixtures/generated/search-track-ceiling/manifest.json",
    )
    track_ceiling_manifest = load(
        CONFORMANCE / "fixtures/generated/search-track-ceiling/manifest.json"
    )
    track_large = validate(
        CONFORMANCE / "suites/search-track-large-title-sort.json",
        GOLDENS / "search-track-large-title-sort.json",
        CONFORMANCE / "fixtures/generated/search-track-large-title/manifest.json",
    )
    track_large_manifest = load(
        CONFORMANCE / "fixtures/generated/search-track-large-title/manifest.json"
    )

    assert labels(search["fixture-upper"]) == labels(search["fixture-lower"])
    assert labels(search["fixture-upper"]) == labels(search["fixture-mixed"])
    assert labels(search["alpha"]) == ["Alpha Artist", "Alpha One", "Alpha Two"]
    assert labels(search["album"]) == [
        "Album One",
        "Album Two",
        "Album Three",
        "Unknown Album",
    ]
    assert labels(search["alpha-one"]) == ["Alpha One"]
    assert labels(search["one-alpha"]) == ["Alpha One"]
    assert labels(search["omega-symbol"]) == ["Unicode Ω Search"]
    assert search["omega-ascii"]["total"] == 0

    rejected_lengths = (
        "length-zero",
        "length-two",
        "length-short",
        "length-one",
        "length-fourteen",
        "length-fifteen",
    )
    accepted_lengths = (
        "length-long",
        "length-sixteen",
        "length-seventeen",
        "length-eighteen",
        "length-256",
    )
    assert all(case_id in search for case_id in rejected_lengths + accepted_lengths)
    assert all(search[case_id]["header"][0]["kind"] == 0x0100 for case_id in rejected_lengths)
    assert all(search[case_id]["total"] is None for case_id in rejected_lengths)
    assert all(search[case_id]["header"][0]["kind"] == 0x4000 for case_id in accepted_lengths)
    assert all(search[case_id]["total"] == 10 for case_id in accepted_lengths)

    expected_category_labels = {
        "02": {
            "alpha": ["Alpha One", "Alpha Two"],
            "album": ["Album One", "Album Two", "Album Three", "Unknown Album"],
            "fixture": [f"fixture-{index:02}.wav" for index in range(1, 9)],
            "beta-searchstr": ["Beta One"],
        },
        "03": {
            "alpha": ["Alpha Artist", "Alpha One", "Alpha Two"],
            "album": ["Unknown Album"],
            "fixture": ["Fixture Remixer", "Fixture Original"]
            + [f"fixture-{index:02}.wav" for index in range(1, 9)],
            "beta-searchstr": ["Beta Artist", "Beta One"],
        },
        "04": {
            "alpha": ["Alpha Artist"],
            "album": ["Album One", "Album Two", "Album Three"],
            "fixture": ["Fixture Remixer", "Fixture Original"]
            + [f"fixture-{index:02}.wav" for index in range(1, 9)],
            "beta-searchstr": ["Beta Artist"],
        },
        "21": {
            "alpha": ["Alpha Artist", "Alpha One", "Alpha Two"],
            "album": ["Album One", "Album Two", "Album Three", "Unknown Album"],
            "fixture": ["Fixture Remixer", "Fixture Original"],
            "beta-searchstr": ["Beta Artist", "Beta One"],
        },
    }
    for category, expected in expected_category_labels.items():
        assert {case_id: labels(case) for case_id, case in category_cases[category].items()} == expected

    assert ceiling_manifest["track_count"] == 1_005
    assert ceiling["ceiling-total"]["total"] == 1_000
    assert labels(ceiling["ceiling-full-default"]) == [
        f"Ceiling Match {index:04}" for index in range(1, 1_001)
    ]
    assert labels(ceiling["ceiling-zero-count-start"]) == ["Ceiling Match 0001"]
    assert labels(ceiling["ceiling-zero-count-at-cap"]) == ["Ceiling Match 1000"]
    assert labels(ceiling["ceiling-last-full-window"]) == [
        f"Ceiling Match {index:04}" for index in range(996, 1_001)
    ]
    for case_id in (
        "ceiling-overrun-one",
        "ceiling-cross-boundary",
        "ceiling-last-offset-window",
        "ceiling-at-cap-window",
    ):
        assert labels(ceiling[case_id]) == labels(
            ceiling["ceiling-last-full-window"]
        )
    for case_id in (
        "ceiling-offset-999",
        "ceiling-offset-1000",
        "ceiling-offset-1001",
    ):
        assert labels(ceiling[case_id]) == ["Ceiling Match 1000"]
    assert labels(ceiling["narrow-thousandth"]) == ["Ceiling Match 1000"]
    assert labels(ceiling["narrow-thousand-first"]) == ["Ceiling Match 1001"]
    assert labels(ceiling["narrow-last"]) == ["Ceiling Match 1005"]

    expected_text_labels = {
        "precomposed-upper": ["Precomposed Éclair"],
        "precomposed-lower": ["Precomposed éclair"],
        "combining-upper-base": ["Combining Éclair", "Combining éclair"],
        "combining-lower-base": ["Combining Éclair", "Combining éclair"],
        "precomposed-against-combining": [],
        "combining-against-precomposed": [],
        "emoji-smiling": [],
        "emoji-upside-down": [],
        "emoji-mixed-token": [],
        "emoji-scalar-length": [],
        "sharp-s-exact": ["Sharp ß Search"],
        "sharp-s-uppercase": [],
        "sharp-s-ascii-expansion": [],
        "dotted-i-exact": ["Dotted İ Search"],
        "dotted-i-ascii": [],
        "nul-only": [],
        "nul-suffix": ["Emoji 🙂 Search", "Emoji 🙃 Search"],
        "nul-middle": ["Emoji 🙂 Search", "Emoji 🙃 Search"],
        "nul-after-emoji": [],
    }
    assert text_manifest["track_count"] == 8
    assert {
        case_id: labels(case) for case_id, case in text_cases.items()
    } == expected_text_labels
    assert text_cases["emoji-smiling"]["request"]["arguments"][2]["value"] == 6
    assert text_cases["emoji-smiling"]["header"][0]["kind"] == 0x4000
    assert text_cases["emoji-scalar-length"]["request"]["arguments"][2]["value"] == 4
    assert text_cases["emoji-scalar-length"]["header"][0]["kind"] == 0x0100

    for case_id in ("mode-0", "mode-1", "mode-2", "mode-3"):
        assert labels(track_cases[case_id]) == [
            "Precomposed Éclair",
            "Precomposed éclair",
        ]
    for case_id in ("mode-127", "mode-128", "mode-255"):
        assert track_cases[case_id]["outcome"] == "error"
        assert track_cases[case_id]["total"] == 0xFFFFFFFF
    assert labels(track_cases["mode-256-low-byte-alias"]) == labels(
        track_cases["mode-0"]
    )
    assert labels(track_cases["mode-0-lowercase"]) == ["Precomposed éclair"]
    assert track_cases["mode-1-no-match"]["total"] == 0
    assert track_cases["mode-1-empty"]["total"] == 0
    assert all(track_cases[f"sort-{sort_id:02d}"]["total"] == 8 for sort_id in range(18))
    assert len(
        {
            tuple(labels(track_cases[f"sort-{sort_id:02d}"]))
            for sort_id in range(18)
        }
    ) == 8
    assert track_cases["declared-length-zero"]["header"][0]["kind"] == 0x0100
    assert track_cases["declared-length-short"]["header"][0]["kind"] == 0x0100
    assert track_cases["three-arguments"]["header"][0]["kind"] == 0x4000
    assert track_cases["three-arguments"]["total"] == 0
    assert track_cases["five-arguments"]["total"] == track_cases["mode-1"]["total"]

    assert track_ceiling_manifest["track_count"] == 5_005
    assert track_ceiling["ordinary-search-control"]["total"] == 1_000
    assert track_ceiling["search-track-total"]["total"] == 5_000
    assert track_ceiling["search-track-sort-17-total"]["total"] == 5_005
    assert labels(track_ceiling["search-track-first"]) == ["Ceiling Match 0001"]
    assert labels(track_ceiling["search-track-last-window"]) == [
        f"Ceiling Match {index:04d}" for index in range(4_996, 5_001)
    ]
    assert labels(track_ceiling["search-track-cross-boundary"]) == labels(
        track_ceiling["search-track-last-window"]
    )
    for case_id in ("search-track-at-cap", "search-track-beyond-cap"):
        assert labels(track_ceiling[case_id]) == ["Ceiling Match 5000"]
    assert len(track_ceiling["search-track-full"]["rows"]) == 5_000
    assert labels(track_ceiling["search-track-full"])[0] == "Ceiling Match 0001"
    assert labels(track_ceiling["search-track-full"])[-1] == "Ceiling Match 5000"
    assert labels(track_ceiling["narrow-five-thousand-first"]) == [
        "Ceiling Match 5001"
    ]
    assert labels(track_ceiling["narrow-last"]) == ["Ceiling Match 5005"]

    assert track_large_manifest["track_count"] == 10_005
    assert track_large["ordinary-control"]["total"] == 1_000
    assert track_large["sort-00"]["total"] == 5_000
    assert all(
        track_large[f"sort-{sort_id:02d}"]["total"] == 10_005
        for sort_id in range(1, 18)
    )

    replay = load(RESULT)
    replay_suites = [
        suite for suite in replay["suites"] if suite["suite"].startswith("search")
    ]
    assert len(replay_suites) == 10
    assert sum(suite["cases"] for suite in replay_suites) == 160
    exact = sum(len(suite["exact_cases"]) for suite in replay_suites)
    same_shape = sum(
        len(suite["same_outcome_total_row_count_cases"])
        for suite in replay_suites
    )

    report = {
        "format": "rekordbox-link-export-search-v4",
        "oracle": {
            "goldens": 10,
            "cases": 160,
            "search_sha256": sha256(GOLDENS / "search.json"),
            "ceiling_sha256": sha256(GOLDENS / "search-ceiling.json"),
            "text_sha256": sha256(GOLDENS / "search-text.json"),
            "track_sha256": sha256(GOLDENS / "search-track.json"),
            "track_ceiling_sha256": sha256(GOLDENS / "search-track-ceiling.json"),
            "track_large_title_sort_sha256": sha256(
                GOLDENS / "search-track-large-title-sort.json"
            ),
            "category_sha256": {
                category: sha256(GOLDENS / f"search-category-{category}-disabled.json")
                for category in category_cases
            },
        },
        "matching": {
            "ascii_case_equivalent": True,
            "token_order_independent": True,
            "omega_symbol_matches": True,
            "ascii_omega_matches": False,
        },
        "category_domains": {
            "02": "Artist",
            "03": "Album",
            "04": "Track title",
            "21": "File Name",
        },
        "lengths": {
            "rejected": list(rejected_lengths),
            "accepted": list(accepted_lengths),
        },
        "ceiling": {
            "fixture_tracks": ceiling_manifest["track_count"],
            "fixture_fingerprint": ceiling_manifest["fixture_fingerprint"],
            "broad_total": ceiling["ceiling-total"]["total"],
            "first": labels(ceiling["ceiling-first"])[0],
            "last": labels(ceiling["ceiling-offset-999"])[0],
            "first_beyond_cap": labels(ceiling["narrow-thousand-first"])[0],
            "final_source_row": labels(ceiling["narrow-last"])[0],
            "overrun_window": labels(ceiling["ceiling-cross-boundary"]),
        },
        "text": {
            "fixture_fingerprint": text_manifest["fixture_fingerprint"],
            "precomposed_case_sensitive": True,
            "combining_ascii_base_folded": True,
            "canonical_normalization": False,
            "supplementary_query_matches": False,
            "supplementary_utf16_bytes": 6,
            "sharp_s_expands": False,
            "dotted_i_ascii_equivalent": False,
            "nul_terminates_query": True,
        },
        "search_track": {
            "request_kind": "0x1500",
            "arguments": ["context", "sort", "utf16_byte_length", "string"],
            "sort_ids": list(range(18)),
            "distinct_small_fixture_orders": 8,
            "sort_is_signed_low_byte": True,
            "default_ceiling": track_ceiling["search-track-total"]["total"],
            "explicit_sort_5005_total": track_ceiling[
                "search-track-sort-17-total"
            ]["total"],
            "explicit_sort_10005_totals": {
                f"{sort_id:02d}": track_large[f"sort-{sort_id:02d}"]["total"]
                for sort_id in range(1, 18)
            },
            "ceiling_fixture_fingerprint": track_ceiling_manifest[
                "fixture_fingerprint"
            ],
            "large_fixture_fingerprint": track_large_manifest[
                "fixture_fingerprint"
            ],
        },
        "static_analysis": {
            "search_path": "data/static-analysis/search-query.disasm.txt",
            "search_sha256": sha256(ROOT / "data/static-analysis/search-query.disasm.txt"),
            "request_1500_path": "data/static-analysis/request-1500.disasm.txt",
            "request_1500_sha256": sha256(
                ROOT / "data/static-analysis/request-1500.disasm.txt"
            ),
            "request_1500_immediates_path": "data/static-analysis/request-1500-immediates.txt",
            "request_1500_immediates_sha256": sha256(
                ROOT / "data/static-analysis/request-1500-immediates.txt"
            ),
        },
        "rbxport": {
            "version": replay["backend_version"],
            "cases": 160,
            "exact": exact,
            "same_outcome_total_row_count": same_shape,
        },
    }
    output = ROOT / "data/experiments/search/summary.json"
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(output)


if __name__ == "__main__":
    main()
