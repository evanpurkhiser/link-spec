#!/usr/bin/env python3
"""Generate packed-context crosses for legacy Hot Cue change operation 0x2201."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REJECTED_TYPES = (0x00, 0x02, 0x03, 0x04, 0x05, 0x06)
LEGACY_CUE_RECORD = (
    "0001040011270000000000001111111122222222333333334444444455555555"
    "66666666"
)
MSEC_EXTENSION = "7777777788888888"


def context(player: int, track_type: int) -> str:
    return f"0x{player:02x}0103{track_type:02x}"


def setter_case(player: int, track_type: int, label: str) -> dict[str, object]:
    return {
        "id": f"type-{track_type:02x}--set-{label}",
        "description": (
            f"Track type 0x{track_type:02x}: player-{player} status-backed "
            "legacy D Hot Cue Bank mutation"
        ),
        "request_kind": "0x2201",
        "arguments": [
            {"number": context(player, track_type)},
            {"number": "$fixture.hotcue.bank.mutation"},
            {"number": 36},
            {"blob_hex": LEGACY_CUE_RECORD},
            {"number": 8},
            {"blob_hex": MSEC_EXTENSION},
        ],
        "direct_response": True,
        "render": False,
        "fresh_connection": True,
        "expect": {"outcome": "any"},
    }


def getter_case(player: int, track_type: int, label: str) -> dict[str, object]:
    return {
        "id": f"type-{track_type:02x}--read-after-{label}",
        "description": (
            f"Type-1 six-slot membership read after player-{player} type "
            f"0x{track_type:02x} {label.replace('-', ' ')}"
        ),
        "request_kind": "0x2301",
        "arguments": [
            {"number": context(player, 0x01)},
            {"number": "$fixture.hotcue.bank.mutation"},
            {"number": 6},
        ],
        "direct_response": True,
        "render": False,
        "fresh_connection": True,
        "expect": {"outcome": "raw_reply"},
    }


def suite(setup: str, player: int) -> dict[str, object]:
    name = f"context-hot-cue-legacy-setter-status-player-{player}-{setup}"
    cases = []
    for track_type in REJECTED_TYPES:
        cases.extend(
            (
                setter_case(player, track_type, "rejected"),
                getter_case(player, track_type, "rejected-setter"),
            )
        )
    cases.extend(
        (
            setter_case(player, 0x01, "accepted"),
            getter_case(player, 0x01, "accepted-setter"),
        )
    )

    return {
        "name": name,
        "fixture_profile": "hot-cue-bank-legacy-ordinals",
        "fixture_version": 1,
        "repeat_strategy": "fixture-reset-and-restart",
        "defaults": {
            "device": player,
            "context": context(player, 1),
            "sort": 0,
            "root_capabilities": "0x05cfffff",
            "setup": setup,
            "page_size": 32,
            "read_timeout_ms": 5000,
            "render_arguments": [0, "$total", 12, 1, 0],
        },
        "cases": cases,
    }


def main() -> None:
    for player in (1, 11):
        for setup in ("extended", "legacy"):
            document = suite(setup, player)
            output = ROOT / f"suites/{document['name']}.json"
            output.write_text(json.dumps(document, indent=2) + "\n")


if __name__ == "__main__":
    main()
