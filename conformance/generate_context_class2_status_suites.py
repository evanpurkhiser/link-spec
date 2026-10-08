#!/usr/bin/env python3
"""Generate genuine-status packed crosses for remaining class-2 builders."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
TRACK_TYPES = range(0x07)
REQUESTS = (
    (0x2202, "recognized-22"),
    (0x2302, "recognized-23"),
    (0x2402, "recognized-24"),
    (0x2502, "recognized-25"),
    (0x2602, "delivery"),
)


def context(player: int, track_type: int) -> str:
    return f"0x{player:02x}0103{track_type:02x}"


def case(player: int, track_type: int, request_kind: int, label: str) -> dict[str, object]:
    return {
        "id": f"type-{track_type:02x}--{label}",
        "description": (
            f"Track type 0x{track_type:02x}: player-{player} status-backed "
            f"class-2 request 0x{request_kind:04x}"
        ),
        "request_kind": f"0x{request_kind:04x}",
        "arguments": [
            {"number": context(player, track_type)},
            {"number": "$fixture.track.first"},
        ],
        "render_context": context(player, track_type),
        "fresh_connection": True,
        "expect": {"outcome": "any"},
    }


def suite(setup: str, player: int) -> dict[str, object]:
    name = f"context-class2-status-player-{player}-{setup}"
    return {
        "name": name,
        "fixture_profile": "full",
        "fixture_version": 1,
        "repeat_strategy": "immediate",
        "defaults": {
            "device": player,
            "context": context(player, 1),
            "sort": 0,
            "root_capabilities": "0x05cfffff",
            "setup": setup,
            "page_size": 32,
            "render_arguments": [0, "$total", 12, 1, 0],
        },
        "cases": [
            case(player, track_type, request_kind, label)
            for track_type in TRACK_TYPES
            for request_kind, label in REQUESTS
        ],
    }


def main() -> None:
    for player in (1, 11):
        for setup in ("extended", "legacy"):
            document = suite(setup, player)
            output = ROOT / f"suites/{document['name']}.json"
            output.write_text(json.dumps(document, indent=2) + "\n")


if __name__ == "__main__":
    main()
