#!/usr/bin/env python3
"""Generate genuine-status/setup crosses for Hot Cue Bank catalog 0x2001."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
TRACK_TYPES = range(0x07)
TEMPLATES = (
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


def context(player: int, track_type: int) -> str:
    return f"0x{player:02x}0103{track_type:02x}"


def case(
    player: int,
    track_type: int,
    name: str,
    description: str,
    arguments: list[dict[str, object]],
) -> dict[str, object]:
    packed_context = context(player, track_type)
    return {
        "id": f"type-{track_type:02x}--{name}",
        "description": (
            f"Track type 0x{track_type:02x}: player-{player} status-backed "
            f"{description}"
        ),
        "request_kind": "0x2001",
        "arguments": [{"number": packed_context}, *arguments],
        "render_context": packed_context,
        "fresh_connection": True,
        "expect": {"outcome": "any"},
    }


def suite(setup: str, player: int) -> dict[str, object]:
    name = f"context-hot-cue-catalog-status-player-{player}-{setup}"
    return {
        "name": name,
        "fixture_profile": "hot-cue-banks",
        "fixture_version": 1,
        "repeat_strategy": "fixture-reset-and-restart",
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
            case(player, track_type, name, description, arguments)
            for track_type in TRACK_TYPES
            for name, description, arguments in TEMPLATES
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
