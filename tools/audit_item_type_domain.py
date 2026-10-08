#!/usr/bin/env python3
"""Audit the complete represented 0x4101 item-type domain in canonical goldens."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_GOLDENS = ROOT / "conformance/goldens/rekordbox-7.2.19"
DEFAULT_OUTPUT = ROOT / "data/static-analysis/item-type-domain.json"


def item_types(value: object):
    if isinstance(value, dict):
        arguments = value.get("arguments")
        if value.get("kind") == 0x4101 and isinstance(arguments, list) and len(arguments) > 6:
            argument = arguments[6]
            if isinstance(argument, dict) and argument.get("type") == "number":
                yield argument["value"]

        for child in value.values():
            yield from item_types(child)
    elif isinstance(value, list):
        for child in value:
            yield from item_types(child)


def build(goldens: Path) -> dict[str, object]:
    paths = sorted(goldens.rglob("*.json"))
    counts: Counter[int] = Counter()
    files_with_rows = 0
    for path in paths:
        values = list(item_types(json.loads(path.read_text())))
        if values:
            files_with_rows += 1
            counts.update(values)

    types = [
        {
            "value": value,
            "hex": f"0x{value:08x}",
            "upper_16": value >> 16,
            "lower_16": value & 0xFFFF,
            "occurrences": counts[value],
        }
        for value in sorted(counts)
    ]
    return {
        "format": 2,
        "scope": "represented 0x4101 item types in row-bearing canonical Rekordbox 7.2.19 goldens",
        "golden_root": str(goldens.relative_to(ROOT)),
        "row_bearing_golden_file_count": files_with_rows,
        "representation_occurrence_count": sum(counts.values()),
        "unique_type_count": len(types),
        "maximum_value": max(counts),
        "maximum_hex": f"0x{max(counts):08x}",
        "nonzero_upper_16_type_count": sum(item["upper_16"] != 0 for item in types),
        "types": types,
        "counting_note": (
            "Only files containing a represented 0x4101 row contribute to the stable file count. "
            "The canonical JSON retains page messages and normalized aggregate rows; this is a "
            "representation-occurrence count, not a distinct wire-packet count."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--goldens", type=Path, default=DEFAULT_GOLDENS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(build(args.goldens.resolve()), indent=2) + "\n")


if __name__ == "__main__":
    main()
