#!/usr/bin/env python3
"""Generate packed-context crosses for status-backed Hot Cue Bank getters."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
TRACK_TYPES = range(0x07)


def context(player: int, track_type: int) -> str:
    return f"0x{player:02x}0103{track_type:02x}"


def getter_case(
    player: int,
    track_type: int,
    request_kind: int,
    label: str,
    selector: str,
    count: int | None = None,
) -> dict[str, object]:
    arguments: list[dict[str, object]] = [
        {"number": context(player, track_type)},
        {"number": selector},
    ]
    if count is not None:
        arguments.append({"number": count})

    return {
        "id": f"type-{track_type:02x}--{label}",
        "description": (
            f"Track type 0x{track_type:02x}: player-{player} status-backed "
            f"Hot Cue Bank {label.replace('-', ' ')}"
        ),
        "request_kind": f"0x{request_kind:04x}",
        "arguments": arguments,
        "direct_response": True,
        "render": False,
        "fresh_connection": True,
        "expect": {"outcome": "any"},
    }


def suite(setup: str, player: int) -> dict[str, object]:
    name = f"context-hot-cue-getter-status-player-{player}-{setup}"
    cases = []
    for track_type in TRACK_TYPES:
        cases.extend(
            (
                getter_case(
                    player,
                    track_type,
                    0x2101,
                    "legacy-populated",
                    "$fixture.hotcue.bank.alpha",
                ),
                getter_case(
                    player,
                    track_type,
                    0x2101,
                    "legacy-empty",
                    "$fixture.hotcue.bank.empty",
                ),
                getter_case(
                    player,
                    track_type,
                    0x2301,
                    "extended-populated",
                    "$fixture.hotcue.bank.alpha",
                    3,
                ),
                getter_case(
                    player,
                    track_type,
                    0x2301,
                    "extended-empty",
                    "$fixture.hotcue.bank.empty",
                    3,
                ),
            )
        )

    return {
        "name": name,
        "fixture_profile": "hot-cue-banks",
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
