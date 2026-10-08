#!/usr/bin/env python3
"""Generate SmartList serving-path crosses from the shared track matrices."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT = ROOT / "suites/smart-serving-crosses.json"
PLAYLIST = "$fixture.playlist.smart_matrix.logic_any"
SOURCES = (
    ("", ROOT / "suites/generated/sort-ids.json"),
    ("render", ROOT / "suites/generated/render-secondary-controls.json"),
    ("page", ROOT / "suites/pagination.json"),
    ("context", ROOT / "suites/generated/contexts.json"),
)
TRACK_NAMES = (
    "first",
    "second",
    "third",
    "fourth",
    "fifth",
    "sixth",
    "seventh",
    "eighth",
)
TRACK_SYMBOLS = {
    10001 + index: f"$fixture.track.{name}"
    for index, name in enumerate(TRACK_NAMES)
}


def number(value: int | str) -> dict[str, int | str]:
    return {"number": value}


def load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text())


def transform_case(prefix: str, source: dict[str, object]) -> dict[str, object]:
    case = copy.deepcopy(source)
    arguments = case["arguments"]
    case["id"] = f"{prefix}-{case['id']}" if prefix else case["id"]
    case["description"] = (
        f"SmartList serving cross: {case['description'][0].lower()}"
        f"{case['description'][1:]}"
    )
    case["request_kind"] = "0x1105"
    case["arguments"] = [*arguments[:2], number(PLAYLIST), number(0)]
    case["expect"] = {"outcome": "any"}
    return case


def expectation(case: dict[str, object]) -> dict[str, object]:
    expected: dict[str, object] = {"outcome": case["outcome"]}
    total = case.get("total")
    rows = case.get("rows", [])
    if total is not None:
        expected["total"] = total
    if case["outcome"] == "menu":
        expected["row_count"] = len(rows)
        expected["item_ids"] = [
            TRACK_SYMBOLS.get(row["arguments"][1]["value"], row["arguments"][1]["value"])
            for row in rows
        ]
        argument_counts = {len(row["arguments"]) for row in rows}
        if len(argument_counts) == 1:
            expected["argument_count"] = argument_counts.pop()
    return expected


def apply_oracle(
    cases: list[dict[str, object]], oracle_path: Path
) -> list[dict[str, object]]:
    oracle = load(oracle_path)
    observed = {case["id"]: case for case in oracle["behavior"]["cases"]}
    expected_ids = {case["id"] for case in cases}
    if set(observed) != expected_ids:
        observed = {
            case_id.removeprefix("sort-"): case
            if case_id.startswith("sort-sort-")
            else case
            for case_id, case in observed.items()
        }
    assert set(observed) == expected_ids
    for case in cases:
        case["expect"] = expectation(observed[case["id"]])
    return cases


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--oracle", type=Path)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--legacy-output", type=Path)
    args = parser.parse_args()

    cases = [
        transform_case(prefix, case)
        for prefix, path in SOURCES
        for case in load(path)["cases"]
    ]
    assert len(cases) == 65
    if args.oracle is not None:
        cases = apply_oracle(cases, args.oracle)

    suite = {
        "name": "smart-serving-crosses",
        "fixture_profile": "smart-rule-matrix",
        "fixture_version": 1,
        "defaults": {
            "device": 1,
            "context": "0x01010301",
            "sort": 0,
            "root_capabilities": "0x05cfffff",
            "setup": "extended",
            "page_size": 3,
            "render_arguments": [0, "$total", 12, 1, 0],
        },
        "cases": cases,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(suite, indent=2) + "\n")
    print(args.output)

    if args.legacy_output is not None:
        legacy = copy.deepcopy(suite)
        legacy["name"] = "smart-serving-legacy"
        legacy["defaults"]["setup"] = "legacy"
        legacy["cases"] = [{
            "id": "tracks",
            "description": "SmartList result through the legacy 12-field serializer",
            "request_kind": "0x1105",
            "arguments": [
                number("$context"),
                number("$sort"),
                number(PLAYLIST),
                number(0),
            ],
            "expect": {
                "outcome": "menu",
                "total": 8,
                "row_count": 8,
                "argument_count": 12,
                "item_ids": [
                    f"$fixture.track.{name}" for name in TRACK_NAMES
                ],
            },
        }]
        args.legacy_output.parent.mkdir(parents=True, exist_ok=True)
        args.legacy_output.write_text(json.dumps(legacy, indent=2) + "\n")
        print(args.legacy_output)


if __name__ == "__main__":
    main()
