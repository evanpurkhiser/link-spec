#!/usr/bin/env python3
"""Validate and summarize SmartList text-collation behavior."""

from __future__ import annotations

import json
from pathlib import Path

from summarize_search_oracle import load, sha256, validate


ROOT = Path(__file__).resolve().parent.parent
CONFORMANCE = ROOT / "conformance"
SUITE = CONFORMANCE / "suites/smart-text-matrix.json"
GOLDEN = CONFORMANCE / "goldens/rekordbox-7.2.19/xdj-rx3/smart-text-matrix.json"
MANIFEST = CONFORMANCE / "fixtures/generated/smart-text-matrix/manifest.json"
DISASSEMBLY = ROOT / "data/static-analysis/smart-collation.disasm.txt"
RESULT = CONFORMANCE / "results/rbxport/c144f19+tree.80e87ec8aace/summary.json"


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

    alpha = [12001, 12002, 12003, 12004, 12005, 12012, 12021, 12038, 12039, 12040]
    assert expected["alpha-operator-01"] == alpha
    assert expected["alpha-lower-equal"] == alpha
    assert expected["alpha-acute-precomposed-equal"] == alpha
    assert expected["alpha-acute-decomposed-equal"] == []
    assert expected["alpha-trailing-combining-equal"] == []
    assert expected["sharp-s-equal"] == [12017, 12018]
    assert expected["sharp-s-expanded-equal"] == [12018]
    assert expected["ligature-equal"] == [12019, 12020]
    assert expected["ligature-expanded-equal"] == [12020]
    assert expected["turkish-ascii-equal"] == [12022, 12023]
    assert expected["turkish-dotless-equal"] == [12024]
    assert expected["greek-upper-equal"] == [12025, 12026, 12027]
    assert expected["katakana-equal"] == [12028, 12029]
    assert expected["empty-operator-01"] == [12010, 12011]
    assert expected["empty-operator-02"] == [
        value for value in range(12001, 12044) if value not in (12010, 12011)
    ]

    disassembly = DISASSEMBLY.read_text()
    assert "Locale5getUSEv" in disassembly
    assert "StringSearchC1" in disassembly
    assert "CollationRule6equals" in disassembly
    assert "CollationRule8contains" in disassembly
    assert "CollationRule10startsWith" in disassembly
    assert "CollationRule8endsWith" in disassembly

    replay = load(RESULT)
    text = next(
        item for item in replay["suites"] if item["suite"] == "smart-text-matrix"
    )
    empty_controls = [case_id for case_id, ids in expected.items() if not ids]
    nonempty = [case_id for case_id, ids in expected.items() if ids]
    assert text["cases"] == 55
    assert text["exact_cases"] == empty_controls
    assert text["same_outcome_total_row_count_cases"] == empty_controls
    assert text["different_cases"] == nonempty

    report = {
        "format": "rekordbox-link-export-smart-text-matrix-v1",
        "oracle": {
            "cases": len(expected),
            "golden_sha256": sha256(GOLDEN),
            "suite_sha256": sha256(SUITE),
            "immediate_repeat_verified": True,
        },
        "fixture": {
            "profile": "smart-text-matrix",
            "database_sha256": manifest["database_sha256"],
            "fingerprint": manifest["fixture_fingerprint"],
            "tracks": manifest["track_count"],
            "smart_playlists": len(expected),
        },
        "static_evidence": {
            "path": str(DISASSEMBLY.relative_to(ROOT)),
            "sha256": sha256(DISASSEMBLY),
            "locale": "en_US",
            "collator_strength": 0,
            "addresses": {
                "equals": "0x102333de0",
                "contains": "0x102334110",
                "starts_with": "0x102334430",
                "ends_with": "0x102334720",
                "constructor": "0x102335310",
                "operator_dispatch": "0x1023359e0",
            },
        },
        "behavior": {
            "property": "comments",
            "operators": {
                "1": "equals",
                "2": "not_equal",
                "8": "contains",
                "9": "not_contains",
                "10": "starts_with",
                "11": "ends_with",
            },
            "case_item_ids": expected,
            "ascii_case_insensitive": True,
            "precomposed_accent_insensitive": True,
            "width_insensitive": True,
            "kana_insensitive": True,
            "greek_sigma_forms_equal": True,
            "turkish_dotless_i_is_distinct": True,
            "decomposed_rule_values_match_nothing": True,
            "candidate_decomposed_values_match_precomposed_rules": True,
            "expansion_matching_is_pattern_direction_dependent": True,
            "punctuation_and_whitespace_are_significant": True,
            "embedded_nul_truncates_candidate_utf8": True,
            "sql_null_and_empty_are_equal_for_operator_1": True,
            "empty_rule_operators_8_through_11_match_nothing": True,
            "xml_entities_are_decoded": True,
            "confusable_scripts_are_distinct": True,
        },
        "rbxport": {
            "version": replay["backend_version"],
            "cases": text["cases"],
            "exact": len(text["exact_cases"]),
            "same_outcome_total_row_count": len(
                text["same_outcome_total_row_count_cases"]
            ),
            "exact_empty_controls": text["exact_cases"],
            "nonempty_oracle_cases_returned_empty": nonempty,
        },
    }
    output = ROOT / "data/experiments/smart-text-matrix/summary.json"
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(output)


if __name__ == "__main__":
    main()
