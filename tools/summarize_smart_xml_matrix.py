#!/usr/bin/env python3
"""Validate and summarize SmartList XML parser behavior."""

from __future__ import annotations

import json
from pathlib import Path

from summarize_search_oracle import load, sha256, validate


ROOT = Path(__file__).resolve().parent.parent
CONFORMANCE = ROOT / "conformance"
SUITE = CONFORMANCE / "suites/smart-xml-matrix.json"
GOLDEN = CONFORMANCE / "goldens/rekordbox-7.2.19/xdj-rx3/smart-xml-matrix.json"
MANIFEST = CONFORMANCE / "fixtures/generated/smart-xml-matrix/manifest.json"
DISASSEMBLY = ROOT / "data/static-analysis/smart-xml-parser.disasm.txt"
RESULT = CONFORMANCE / "results/rbxport/c144f19+tree.80e87ec8aace/summary.json"


HOUSE_CASES = {
    "canonical-house",
    "lowercase-elements",
    "mixedcase-elements",
    "xml-declaration",
    "xml-declaration-encoding",
    "leading-comment",
    "leading-processing-instruction",
    "trailing-comment",
    "surrounding-whitespace",
    "reordered-attributes",
    "single-quoted-attributes",
    "decimal-character-reference",
    "hex-character-reference",
    "mismatched-close",
    "nested-then-direct-house",
    "direct-house-then-nested-techno",
    "two-roots-house-then-techno",
    "valid-root-trailing-text",
    "uppercase-property-value",
    "plus-one-operator",
    "spaced-one-operator",
    "leading-zero-operator",
    "duplicate-operator-one-then-two",
    "duplicate-value-house-then-techno",
    "extra-condition-attributes",
    "condition-with-text-content",
    "valid-root-then-nul-junk",
}
TECHNO_CASES = {
    "duplicate-operator-two-then-one",
    "duplicate-value-techno-then-house",
}
ALL_CASES = {
    "two-direct-any",
    "plus-two-logical-operator",
    "spaced-two-logical-operator",
    "duplicate-logical-two-then-one",
}


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

    tracks = manifest["ids"]
    all_tracks = [tracks[f"track.{name}"] for name in (
        "first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth"
    )]
    house = all_tracks[::2]
    techno = all_tracks[1::2]
    empty_cases = set(expected) - HOUSE_CASES - TECHNO_CASES - ALL_CASES

    assert len(expected) == 73
    assert len(HOUSE_CASES) == 27
    assert len(TECHNO_CASES) == 2
    assert len(ALL_CASES) == 4
    assert len(empty_cases) == 40
    for case_id in HOUSE_CASES:
        assert expected[case_id] == house
    for case_id in TECHNO_CASES:
        assert expected[case_id] == techno
    for case_id in ALL_CASES:
        assert expected[case_id] == all_tracks
    for case_id in empty_cases:
        assert expected[case_id] == []

    disassembly = DISASSEMBLY.read_text()
    for evidence in (
        "address=0x102334b00",
        "0x0102334bf2  call      0x1027cf2f0  ; __ZN4juce11XmlDocument5parse",
        "0x0102334c04  call      0x102335130  ; __ZN2db16getSmartlistNode",
        "address=0x102335130",
        "0x0102335155  lea       rsi, [rip + 0x303bde0]  ; 'NODE'",
        "0x010233516c  call      0x1027b4b90  ; __ZNK4juce6String16equalsIgnoreCase",
        "0x0102335192  call      0x1027d9810  ; __ZNK4juce10XmlElement15getIntAttribute",
        "0x01023351aa  lea       r13, [rip + 0x30241d2]  ; 'CONDITION'",
        "0x0102335209  call      0x1027b4b90  ; __ZNK4juce6String16equalsIgnoreCase",
        "0x0102335259  call      0x102335ca0  ; __ZN2db21getSmartlistCondition",
        "0x01023352f3  mov       dword ptr [rdx], 1",
    ):
        assert evidence in disassembly

    replay = load(RESULT)
    result = next(
        item for item in replay["suites"] if item["suite"] == "smart-xml-matrix"
    )
    populated_cases = HOUSE_CASES | TECHNO_CASES | ALL_CASES
    assert result["cases"] == 73
    assert set(result["exact_cases"]) == empty_cases
    assert set(result["same_outcome_total_row_count_cases"]) == empty_cases
    assert set(result["different_cases"]) == populated_cases

    report = {
        "format": "rekordbox-link-export-smart-xml-matrix-v1",
        "oracle": {
            "cases": len(expected),
            "golden_sha256": sha256(GOLDEN),
            "suite_sha256": sha256(SUITE),
            "immediate_repeat_verified": True,
        },
        "fixture": {
            "profile": "smart-xml-matrix",
            "database_sha256": manifest["database_sha256"],
            "fingerprint": manifest["fixture_fingerprint"],
            "tracks": manifest["track_count"],
            "smart_playlists": len(expected),
        },
        "static_evidence": {
            "path": str(DISASSEMBLY.relative_to(ROOT)),
            "sha256": sha256(DISASSEMBLY),
            "content_loader_address": "0x102334b00",
            "node_parser_address": "0x102335130",
            "condition_parser_address": "0x102335ca0",
        },
        "behavior": {
            "element_names_are_case_insensitive": True,
            "attribute_names_are_case_sensitive": True,
            "property_values_are_case_insensitive": True,
            "only_direct_condition_children_are_used": True,
            "nested_nodes_are_ignored": True,
            "unknown_and_wrapping_elements_are_ignored": True,
            "zero_valid_conditions_returns_empty": True,
            "missing_blank_invalid_logic_defaults_to_all": True,
            "duplicate_attributes_use_first_value": True,
            "integer_attributes_accept_sign_whitespace_and_leading_zeroes": True,
            "first_document_root_is_used": True,
            "trailing_text_and_nul_are_accepted": True,
            "leading_text_nul_and_bom_are_rejected": True,
            "mismatched_root_close_is_accepted": True,
            "declarations_comments_and_processing_instructions_are_accepted": True,
            "numeric_character_references_are_decoded": True,
            "invalid_entities_are_rejected": True,
            "case_item_ids": expected,
            "house_cases": sorted(HOUSE_CASES),
            "techno_cases": sorted(TECHNO_CASES),
            "all_track_cases": sorted(ALL_CASES),
            "empty_cases": sorted(empty_cases),
        },
        "rbxport": {
            "version": replay["backend_version"],
            "cases": result["cases"],
            "exact": len(result["exact_cases"]),
            "same_outcome_total_row_count": len(
                result["same_outcome_total_row_count_cases"]
            ),
            "exact_empty_controls": sorted(empty_cases),
            "populated_oracle_cases_returned_empty": sorted(populated_cases),
        },
    }
    output = ROOT / "data/experiments/smart-xml-matrix/summary.json"
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(output)


if __name__ == "__main__":
    main()
