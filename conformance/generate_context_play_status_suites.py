#!/usr/bin/env python3
"""Generate packed track-type crosses for status-backed Play Song Info."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
TRACK_TYPES = range(0x07)


def context(player: int, track_type: int) -> str:
    return f"0x{player:02x}0103{track_type:02x}"


def suite(setup: str, player: int) -> dict[str, object]:
    name = f"context-play-status-player-{player}-{setup}"
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
            {
                "id": f"type-{track_type:02x}--play",
                "description": (
                    f"Track type 0x{track_type:02x}: player-{player} "
                    "status-backed Play Song Info"
                ),
                "request_kind": "0x2102",
                "arguments": [
                    {"number": context(player, track_type)},
                    {"number": "$fixture.track.first"},
                ],
                "render_context": context(player, track_type),
                "fresh_connection": True,
                "expect": {"outcome": "any"},
            }
            for track_type in TRACK_TYPES
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
