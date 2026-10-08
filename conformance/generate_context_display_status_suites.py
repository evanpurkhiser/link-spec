#!/usr/bin/env python3
"""Generate packed track-type crosses for status-backed Display Song Info."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
TRACK_TYPES = range(0x07)


def context(player: int, track_type: int) -> str:
    return f"0x{player:02x}0103{track_type:02x}"


def suite(setup: str, player: int, name: str) -> dict[str, object]:
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
                "id": f"type-{track_type:02x}--display",
                "description": (
                    f"Track type 0x{track_type:02x}: status-backed Display Song Info"
                    if player == 1
                    else f"Track type 0x{track_type:02x}: player-{player} "
                    "status-backed Display Song Info"
                ),
                "request_kind": "0x2002",
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
    for setup in ("extended", "legacy"):
        player_1_name = f"context-display-status-{setup}"
        player_1_output = ROOT / f"suites/{player_1_name}.json"
        player_1_output.write_text(
            json.dumps(suite(setup, 1, player_1_name), indent=2) + "\n"
        )

        player_11_name = f"context-display-status-player-11-{setup}"
        player_11_output = ROOT / f"suites/{player_11_name}.json"
        player_11_output.write_text(
            json.dumps(suite(setup, 11, player_11_name), indent=2) + "\n"
        )


if __name__ == "__main__":
    main()
