#!/usr/bin/env python3
"""Generate the SmartList numeric database-boundary suite."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from build_fixture import SMART_NUMERIC_BOUNDARY_NAMES, SMART_NUMERIC_BOUNDARY_TRACKS


ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT = ROOT / "suites/smart-numeric-boundaries.json"
TRACK_SYMBOLS = {
    35_001 + index: f"$fixture.track.smart_numeric_boundary.{name}"
    for index, (name, _value) in enumerate(SMART_NUMERIC_BOUNDARY_TRACKS)
}


def number(value: int | str) -> dict[str, int | str]:
    return {"number": value}


def load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text())


def oracle_expectations(path: Path) -> dict[str, dict[str, object]]:
    golden = load(path)
    expectations = {}
    for case in golden["behavior"]["cases"]:
        expected = {"outcome": case["outcome"]}
        if case["outcome"] == "menu":
            rows = case["rows"]
            expected.update(
                total=case["total"],
                row_count=len(rows),
                item_ids=[
                    TRACK_SYMBOLS.get(
                        row["arguments"][1]["value"],
                        row["arguments"][1]["value"],
                    )
                    for row in rows
                ],
            )
        expectations[case["id"]] = expected

    return expectations


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--oracle", type=Path)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    observed = oracle_expectations(args.oracle) if args.oracle else {}
    cases = []
    for name in SMART_NUMERIC_BOUNDARY_NAMES:
        case_id = name.replace("_", "-")
        cases.append(
            {
                "id": case_id,
                "description": (
                    "SmartList numeric database boundary: "
                    f"{name.replace('_', ' ')}"
                ),
                "request_kind": "0x1105",
                "arguments": [
                    number("$context"),
                    number("$sort"),
                    number(f"$fixture.playlist.smart_numeric_boundary.{name}"),
                    number(0),
                ],
                "expect": observed.get(case_id, {"outcome": "any"}),
            }
        )

    if observed:
        assert set(observed) == {case["id"] for case in cases}

    suite = {
        "name": "smart-numeric-boundaries",
        "fixture_profile": "smart-numeric-boundaries",
        "fixture_version": 1,
        "defaults": {
            "device": 1,
            "context": "0x01010301",
            "sort": 0,
            "root_capabilities": "0x05cfffff",
            "setup": "extended",
            "page_size": 20,
            "render_arguments": [0, "$total", 12, 1, 0],
        },
        "cases": cases,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(suite, indent=2) + "\n")
    print(args.output)


if __name__ == "__main__":
    main()
