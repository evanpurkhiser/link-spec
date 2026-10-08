#!/usr/bin/env python3
"""Generate the exploratory SmartList XML parser conformance suite."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from build_fixture import SMART_XML_MATRIX_NAMES


ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT = ROOT / "suites/smart-xml-matrix.json"
TRACKS = (
    "first",
    "second",
    "third",
    "fourth",
    "fifth",
    "sixth",
    "seventh",
    "eighth",
)
HOUSE = ("first", "third", "fifth", "seventh")
TECHNO = ("second", "fourth", "sixth", "eighth")
ALL = TRACKS
HOUSE_CASES = {
    "canonical_house",
    "lowercase_elements",
    "mixedcase_elements",
    "xml_declaration",
    "xml_declaration_encoding",
    "leading_comment",
    "leading_processing_instruction",
    "trailing_comment",
    "surrounding_whitespace",
    "reordered_attributes",
    "single_quoted_attributes",
    "decimal_character_reference",
    "hex_character_reference",
    "mismatched_close",
    "nested_then_direct_house",
    "direct_house_then_nested_techno",
    "two_roots_house_then_techno",
    "valid_root_trailing_text",
    "uppercase_property_value",
    "plus_one_operator",
    "spaced_one_operator",
    "leading_zero_operator",
    "duplicate_operator_one_then_two",
    "duplicate_value_house_then_techno",
    "extra_condition_attributes",
    "condition_with_text_content",
    "valid_root_then_nul_junk",
}
TECHNO_CASES = {
    "duplicate_operator_two_then_one",
    "duplicate_value_techno_then_house",
}
ALL_CASES = {
    "two_direct_any",
    "plus_two_logical_operator",
    "spaced_two_logical_operator",
    "duplicate_logical_two_then_one",
}
EXPECTED_TRACKS = {
    name: (
        HOUSE
        if name in HOUSE_CASES
        else TECHNO
        if name in TECHNO_CASES
        else ALL
        if name in ALL_CASES
        else ()
    )
    for name in SMART_XML_MATRIX_NAMES
}


def number(value: int | str) -> dict[str, int | str]:
    return {"number": value}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--loose", action="store_true")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    cases = []
    for name in SMART_XML_MATRIX_NAMES:
        expectation: dict[str, object] = {"outcome": "menu"}
        if not args.loose:
            expected = EXPECTED_TRACKS[name]
            expectation.update(
                total=len(expected),
                row_count=len(expected),
                item_ids=[f"$fixture.track.{track}" for track in expected],
            )
        cases.append({
            "id": name.replace("_", "-"),
            "description": f"SmartList XML parser probe: {name.replace('_', ' ')}",
            "request_kind": "0x1105",
            "arguments": [
                number("$context"),
                number("$sort"),
                number(f"$fixture.playlist.smart_xml.{name}"),
                number(0),
            ],
            "expect": expectation,
        })
    assert set(EXPECTED_TRACKS) == set(SMART_XML_MATRIX_NAMES)
    suite = {
        "name": "smart-xml-matrix",
        "fixture_profile": "smart-xml-matrix",
        "fixture_version": 1,
        "defaults": {
            "device": 1,
            "context": "0x01010301",
            "sort": 0,
            "root_capabilities": "0x05cfffff",
            "setup": "extended",
            "page_size": 10,
            "render_arguments": [0, "$total", 12, 1, 0],
        },
        "cases": cases,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(suite, indent=2) + "\n")
    print(args.output)


if __name__ == "__main__":
    main()
