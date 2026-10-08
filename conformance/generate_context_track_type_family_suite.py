#!/usr/bin/env python3
"""Cross the defined packed track-type values over the full menu corpus."""

from __future__ import annotations

import copy
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "suites/full.json"
OUTPUT = ROOT / "suites/context-track-type-families.json"
TRACK_TYPES = range(0x07)


def context(track_type: int) -> str:
    return f"0x010103{track_type:02x}"


def replace_context(arguments: list[dict[str, object]], value: str) -> None:
    for argument in arguments:
        if argument.get("number") == "$context":
            argument["number"] = value


def case(source: dict[str, object], track_type: int) -> dict[str, object]:
    generated = copy.deepcopy(source)
    packed_context = context(track_type)

    generated["id"] = f"type-{track_type:02x}--{source['id']}"
    generated["description"] = (
        f"Track type 0x{track_type:02x}: {source['description']}"
    )
    replace_context(generated["arguments"], packed_context)
    generated["render_context"] = packed_context
    generated["fresh_connection"] = True
    generated["expect"] = {"outcome": "any"}

    return generated


def main() -> None:
    source = json.loads(SOURCE.read_text())
    cases = [
        case(source_case, track_type)
        for track_type in TRACK_TYPES
        for source_case in source["cases"]
    ]

    suite = {
        "name": "context-track-type-families",
        "fixture_profile": "full",
        "fixture_version": 1,
        "repeat_strategy": "reset-and-restart",
        "defaults": {
            **source["defaults"],
            "page_size": 32,
        },
        "cases": cases,
    }

    OUTPUT.write_text(json.dumps(suite, indent=2) + "\n")


if __name__ == "__main__":
    main()
