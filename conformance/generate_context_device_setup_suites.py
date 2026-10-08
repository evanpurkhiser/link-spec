#!/usr/bin/env python3
"""Generate compact packed-context crosses for device identity and setup width."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
TRACK_TYPES = range(0x07)
DISPATCHED_TYPES = (0x00, 0x01, 0x02, 0x05, 0x06)


def context(track_type: int) -> str:
    return f"0x010103{track_type:02x}"


def case(
    case_id: str,
    description: str,
    request_kind: str,
    arguments: list[dict[str, object]],
    track_type: int,
) -> dict[str, object]:
    packed_context = context(track_type)

    return {
        "id": f"type-{track_type:02x}--{case_id}",
        "description": f"Track type 0x{track_type:02x}: {description}",
        "request_kind": request_kind,
        "arguments": arguments,
        "render_context": packed_context,
        "fresh_connection": True,
        "expect": {"outcome": "any"},
    }


def cases() -> list[dict[str, object]]:
    declarations = [
        case(
            "tracks",
            "ordinary Track membership and row enrichment",
            "0x1004",
            [{"number": context(track_type)}, {"number": 0}],
            track_type,
        )
        for track_type in TRACK_TYPES
    ]
    declarations.extend(
        case(
            "genre-tracks-all",
            "hierarchy Track leaf and argument-7 propagation",
            "0x1301",
            [
                {"number": context(track_type)},
                {"number": 0},
                {"number": "$fixture.genre.house"},
                {"number": "0xffffffff"},
                {"number": "0xffffffff"},
            ],
            track_type,
        )
        for track_type in DISPATCHED_TYPES
    )
    declarations.extend(
        case(
            "root",
            "Root admission",
            "0x1000",
            [
                {"number": context(track_type)},
                {"number": 0},
                {"number": "0x05cfffff"},
            ],
            track_type,
        )
        for track_type in (0x00, 0x01)
    )
    declarations.extend(
        case(
            "search",
            "Search admission",
            "0x1300",
            [
                {"number": context(track_type)},
                {"number": 0},
                {"utf16_bytes": "FIXTURE"},
                {"string": "FIXTURE"},
                {"number": 0},
            ],
            track_type,
        )
        for track_type in (0x00, 0x01)
    )

    return declarations


def suite(setup: str) -> dict[str, object]:
    return {
        "name": f"context-device-setup-{setup}",
        "fixture_profile": "full",
        "fixture_version": 1,
        "repeat_strategy": "immediate",
        "defaults": {
            "device": 1,
            "context": context(1),
            "sort": 0,
            "root_capabilities": "0x05cfffff",
            "setup": setup,
            "page_size": 32,
            "render_arguments": [0, "$total", 12, 1, 0],
        },
        "cases": cases(),
    }


def main() -> None:
    for setup in ("extended", "legacy"):
        output = ROOT / f"suites/context-device-setup-{setup}.json"
        output.write_text(json.dumps(suite(setup), indent=2) + "\n")


if __name__ == "__main__":
    main()
