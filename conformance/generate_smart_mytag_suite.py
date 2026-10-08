#!/usr/bin/env python3
"""Generate the exploratory SmartList My Tag conformance suite."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from build_fixture import SMART_MYTAG_MATRIX_NAMES


ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT = ROOT / "suites/smart-mytag-matrix.json"
TRACKS = (
    "tag_one",
    "tag_int32_max",
    "tag_high_bit",
    "tag_uint32_max",
    "tag_zero",
    "tag_one_high_bit",
    "tag_high_bit_uint32_max",
    "untagged",
)
ONE = ("tag_one", "tag_one_high_bit")
INT32_MAX = ("tag_int32_max",)
HIGH_BIT = ("tag_high_bit", "tag_one_high_bit", "tag_high_bit_uint32_max")
UINT32_MAX = ("tag_uint32_max", "tag_high_bit_uint32_max")
ZERO = ("tag_zero",)


def complement(names: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(name for name in TRACKS if name not in names)


EXPECTED_TRACKS = {
    **{f"operator_{operator:02}": () for operator in (*range(1, 8), 10, 11)},
    "operator_08": ONE,
    "operator_09": complement(ONE),
    "zero_operator_08": ZERO,
    "zero_operator_09": complement(ZERO),
    "int32_max_operator_08": INT32_MAX,
    "int32_max_operator_09": complement(INT32_MAX),
    "high_bit_raw_operator_08": INT32_MAX,
    "high_bit_raw_operator_09": complement(INT32_MAX),
    "uint32_max_operator_08": INT32_MAX,
    "uint32_max_operator_09": complement(INT32_MAX),
    "minus_one_operator_08": UINT32_MAX,
    "minus_one_operator_09": complement(UINT32_MAX),
    "int32_min_operator_08": HIGH_BIT,
    "int32_min_operator_09": complement(HIGH_BIT),
    "uint32_overflow_operator_08": INT32_MAX,
    "uint32_overflow_operator_09": complement(INT32_MAX),
    "negative_overflow_operator_08": HIGH_BIT,
    "negative_overflow_operator_09": complement(HIGH_BIT),
    "blank_operator_08": (),
    "blank_operator_09": (),
    "invalid_operator_08": ZERO,
    "invalid_operator_09": complement(ZERO),
    "leading_zero_one_operator_08": ONE,
    "leading_zero_one_operator_09": complement(ONE),
    "plus_one_operator_08": ONE,
    "plus_one_operator_09": complement(ONE),
    "spaced_one_operator_08": ONE,
    "spaced_one_operator_09": complement(ONE),
    "hex_one_operator_08": ZERO,
    "hex_one_operator_09": complement(ZERO),
    "comma_pair_operator_08": ONE,
    "comma_pair_operator_09": complement(ONE),
    "value_right_ignored": ONE,
    "value_unit_ignored": ONE,
    "all_contains_one_high_bit": (),
    "any_contains_one_high_bit": ("tag_one", "tag_int32_max", "tag_one_high_bit"),
    "all_not_contains_one_high_bit": (
        "tag_high_bit",
        "tag_uint32_max",
        "tag_zero",
        "tag_high_bit_uint32_max",
        "untagged",
    ),
    "any_not_contains_one_high_bit": TRACKS,
    "all_contains_one_not_high_bit": ONE,
    "any_contains_one_not_high_bit": (
        "tag_one",
        "tag_high_bit",
        "tag_uint32_max",
        "tag_zero",
        "tag_one_high_bit",
        "tag_high_bit_uint32_max",
        "untagged",
    ),
}


def number(value: int | str) -> dict[str, int | str]:
    return {"number": value}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--loose", action="store_true")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    cases = []
    for name in SMART_MYTAG_MATRIX_NAMES:
        expectation: dict[str, object] = {"outcome": "menu"}
        if not args.loose:
            expected = EXPECTED_TRACKS[name]
            expectation.update(
                total=len(expected),
                row_count=len(expected),
                item_ids=[
                    f"$fixture.track.smart_mytag.{track}" for track in expected
                ],
            )
        cases.append({
            "id": name.replace("_", "-"),
            "description": f"SmartList My Tag probe: {name.replace('_', ' ')}",
            "request_kind": "0x1105",
            "arguments": [
                number("$context"),
                number("$sort"),
                number(f"$fixture.playlist.smart_mytag.{name}"),
                number(0),
            ],
            "expect": expectation,
        })
    assert set(EXPECTED_TRACKS) == set(SMART_MYTAG_MATRIX_NAMES)
    suite = {
        "name": "smart-mytag-matrix",
        "fixture_profile": "smart-mytag-matrix",
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
