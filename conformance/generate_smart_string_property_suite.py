#!/usr/bin/env python3
"""Generate the cross-property SmartList string conformance suite."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from build_fixture import (
    SMART_STRING_PROPERTIES,
    SMART_STRING_PROPERTY_MATRIX_NAMES,
    SMART_STRING_PROPERTY_RULES,
)


ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT = ROOT / "suites/smart-string-property-matrix.json"
TRACKS = (
    "alpha_upper",
    "alpha_lower",
    "alpha_acute_precomposed",
    "alpha_acute_decomposed",
    "fullwidth",
    "alpha_prefix",
    "alpha_suffix",
    "beta",
    "empty",
    "null",
)
NONEMPTY = TRACKS[:-2]
ALPHA_EQUAL = TRACKS[:5]
ALPHA_CONTAINS = TRACKS[:7]
EXPECTED_BY_RULE = {
    "alpha_equal": ALPHA_EQUAL,
    "alpha_not_equal": tuple(name for name in TRACKS if name not in ALPHA_EQUAL),
    "alpha_contains": ALPHA_CONTAINS,
    "alpha_not_contains": ("beta",),
    "alpha_starts": (*TRACKS[:5], "alpha_prefix"),
    "alpha_ends": (*TRACKS[:5], "alpha_suffix"),
    "empty_equal": ("empty", "null"),
    "empty_not_equal": NONEMPTY,
}


def number(value: int | str) -> dict[str, int | str]:
    return {"number": value}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--loose", action="store_true")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    cases = []
    for property_name in SMART_STRING_PROPERTIES:
        for rule_name, _operator, _value in SMART_STRING_PROPERTY_RULES:
            name = f"{property_name}_{rule_name}"
            expected = EXPECTED_BY_RULE[rule_name]
            expectation: dict[str, object] = {"outcome": "menu"}
            if not args.loose:
                expectation.update(
                    total=len(expected),
                    row_count=len(expected),
                    item_ids=[
                        f"$fixture.track.smart_string_property.{track}"
                        for track in expected
                    ],
                )
            cases.append(
                {
                    "id": name.replace("_", "-"),
                    "description": (
                        f"SmartList {property_name} string probe: "
                        f"{rule_name.replace('_', ' ')}"
                    ),
                    "request_kind": "0x1105",
                    "arguments": [
                        number("$context"),
                        number("$sort"),
                        number(f"$fixture.playlist.smart_string_property.{name}"),
                        number(0),
                    ],
                    "expect": expectation,
                }
            )

    assert [case["id"].replace("-", "_") for case in cases] == list(
        SMART_STRING_PROPERTY_MATRIX_NAMES
    )
    suite = {
        "name": "smart-string-property-matrix",
        "fixture_profile": "smart-string-property-matrix",
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
    args.output.write_text(json.dumps(suite, indent=2, ensure_ascii=False) + "\n")
    print(args.output)


if __name__ == "__main__":
    main()
