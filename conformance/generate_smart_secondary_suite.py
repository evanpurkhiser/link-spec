#!/usr/bin/env python3
"""Generate one persisted-secondary-column SmartList suite."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
TRACK_NAMES = (
    "first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth"
)
TRACK_SYMBOLS = {
    10_001 + index: f"$fixture.track.{name}"
    for index, name in enumerate(TRACK_NAMES)
}


def number(value: int | str) -> dict[str, int | str]:
    return {"number": value}


def expectation(path: Path | None) -> dict[str, object]:
    if path is None:
        return {"outcome": "any"}

    golden = json.loads(path.read_text())
    case = golden["behavior"]["cases"][0]
    rows = case["rows"]
    return {
        "outcome": case["outcome"],
        "total": case["total"],
        "row_count": len(rows),
        "item_ids": [
            TRACK_SYMBOLS.get(row["arguments"][1]["value"], row["arguments"][1]["value"])
            for row in rows
        ],
        "argument_count": 16,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("variant")
    parser.add_argument("--oracle", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    if not (
        args.variant.startswith("secondary-")
        or args.variant in {"no-secondary-selection", "multiple-secondary-selections"}
    ):
        raise SystemExit(f"unsupported secondary variant: {args.variant}")

    name = f"smart-{args.variant}"
    output = args.output or ROOT / f"suites/generated/{name}.json"
    suite = {
        "name": name,
        "fixture_profile": "smart-settings",
        "fixture_version": 1,
        "fixture_variant": args.variant,
        "defaults": {
            "device": 1,
            "context": "0x01010301",
            "sort": 0,
            "root_capabilities": "0x05cfffff",
            "setup": "extended",
            "page_size": 10,
            "render_arguments": [0, "$total", 12, 1, 0],
        },
        "cases": [
            {
                "id": "tracks",
                "description": (
                    "Rule-selected tracks with persisted secondary state "
                    f"{args.variant}"
                ),
                "request_kind": "0x1105",
                "arguments": [
                    number("$context"),
                    number("$sort"),
                    number("$fixture.playlist.smart_matrix.logic_any"),
                    number(0),
                ],
                "expect": expectation(args.oracle),
            }
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(suite, indent=2) + "\n")
    print(output)


if __name__ == "__main__":
    main()
