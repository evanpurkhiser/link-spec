#!/usr/bin/env python3
"""Cross defined track types over Hot Cue Bank tree and track modes."""

from __future__ import annotations

import json
from pathlib import Path


OUTPUT = Path(__file__).resolve().parent / "suites/context-hot-cue-track-types.json"
TRACK_TYPES = range(0x07)


def context(track_type: int) -> str:
    return f"0x010103{track_type:02x}"


def case(
    name: str,
    description: str,
    arguments: list[dict[str, object]],
    track_type: int,
) -> dict[str, object]:
    packed_context = context(track_type)

    return {
        "id": f"type-{track_type:02x}--{name}",
        "description": f"Track type 0x{track_type:02x}: {description}",
        "request_kind": "0x2001",
        "arguments": [{"number": packed_context}, *arguments],
        "render_context": packed_context,
        "fresh_connection": True,
        "expect": {"outcome": "any"},
    }


def main() -> None:
    templates = (
        (
            "tree-root",
            "Hot Cue Bank root in folder-list mode",
            [{"number": 0}, {"number": 1}, {"number": 0}],
        ),
        (
            "alpha-tracks",
            "populated Alpha Bank in track-list mode",
            [
                {"number": "$fixture.hotcue.bank.alpha"},
                {"number": 0},
                {"number": 8},
            ],
        ),
        (
            "empty-tracks",
            "empty bank in track-list mode",
            [
                {"number": "$fixture.hotcue.bank.empty"},
                {"number": 0},
                {"number": 8},
            ],
        ),
    )
    suite = {
        "name": "context-hot-cue-track-types",
        "fixture_profile": "hot-cue-banks",
        "fixture_version": 1,
        "repeat_strategy": "reset-and-restart",
        "defaults": {
            "device": 1,
            "context": context(1),
            "sort": 0,
            "root_capabilities": "0x05cfffff",
            "setup": "extended",
            "page_size": 32,
            "render_arguments": [0, "$total", 12, 1, 0],
        },
        "cases": [
            case(name, description, arguments, track_type)
            for track_type in TRACK_TYPES
            for name, description, arguments in templates
        ],
    }

    OUTPUT.write_text(json.dumps(suite, indent=2) + "\n")


if __name__ == "__main__":
    main()
