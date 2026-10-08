#!/usr/bin/env python3
"""Generate the SmartList date-format conformance suite."""

from __future__ import annotations

import json
from pathlib import Path

from build_fixture import (
    SMART_DATE_FORMAT_PROPERTIES,
    SMART_DATE_FORMAT_RULE_VALUES,
)


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "suites/smart-date-format-matrix.json"

JAN_31_EQUIVALENTS = (
    "canonical_jan_31",
    "separator_slash",
    "separator_dot",
    "separator_space",
    "separator_letters",
    "separator_unicode",
    "separator_newline",
)
OTHER_PARSEABLE_VALUES = (
    "canonical_leap_day",
    "nonleap_feb_29",
    "leap_feb_30",
    "nonleap_feb_30",
    "nonleap_feb_31",
    "april_31",
    "month_zero",
    "month_13",
    "day_zero",
    "day_32",
    "month_99",
    "day_99",
    "letter_in_year",
)


def number(value: int | str) -> dict[str, int | str]:
    return {"number": value}


def expected_tracks(value_name: str) -> list[str]:
    if value_name in JAN_31_EQUIVALENTS:
        names = JAN_31_EQUIVALENTS
    elif value_name in OTHER_PARSEABLE_VALUES:
        names = (value_name,)
    else:
        names = ()

    return [f"$fixture.track.date_format.{name}" for name in names]


def case(name: str, description: str, item_ids: list[str]) -> dict[str, object]:
    return {
        "id": name.replace("_", "-"),
        "description": description,
        "request_kind": "0x1105",
        "arguments": [
            number("$context"),
            number("$sort"),
            number(f"$fixture.playlist.smart_date_format.{name}"),
            number(0),
        ],
        "expect": {
            "outcome": "menu",
            "total": len(item_ids),
            "row_count": len(item_ids),
            "item_ids": item_ids,
        },
    }


def main() -> None:
    cases = []
    for property_name in SMART_DATE_FORMAT_PROPERTIES:
        for value_name, _ in SMART_DATE_FORMAT_RULE_VALUES:
            name = f"{property_name}_{value_name}_equal"
            cases.append(case(name, name.replace("_", " "), expected_tracks(value_name)))

        name = f"{property_name}_canonical_not_equal"
        not_equal = [
            f"$fixture.track.date_format.{value_name}"
            for value_name in OTHER_PARSEABLE_VALUES
        ]
        cases.append(case(name, name.replace("_", " "), not_equal))

    suite = {
        "name": "smart-rule-date-format-matrix",
        "fixture_profile": "smart-date-format-matrix",
        "fixture_version": 1,
        "defaults": {
            "device": 1,
            "context": "0x01010301",
            "sort": 0,
            "root_capabilities": "0x05cfffff",
            "setup": "extended",
            "page_size": 7,
            "render_arguments": [0, "$total", 12, 1, 0],
        },
        "cases": cases,
    }
    OUTPUT.write_text(json.dumps(suite, indent=2, ensure_ascii=False) + "\n")
    print(OUTPUT)


if __name__ == "__main__":
    main()
