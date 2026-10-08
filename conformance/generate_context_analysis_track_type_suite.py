#!/usr/bin/env python3
"""Cross defined track types over populated 0x2xxx Song Info requests."""

from __future__ import annotations

import json
from pathlib import Path


OUTPUT = Path(__file__).resolve().parent / "suites/context-analysis-track-types.json"
TRACK_TYPES = range(0x07)
REQUESTS = (
    ("display", "0x2002"),
    ("play", "0x2102"),
    ("recognized-22", "0x2202"),
    ("recognized-23", "0x2302"),
    ("recognized-24", "0x2402"),
    ("recognized-25", "0x2502"),
    ("delivery", "0x2602"),
)


def context(track_type: int) -> str:
    return f"0x010103{track_type:02x}"


def case(name: str, request_kind: str, track_type: int) -> dict[str, object]:
    packed_context = context(track_type)

    return {
        "id": f"type-{track_type:02x}--{name}",
        "description": (
            f"Track type 0x{track_type:02x}: populated {request_kind} {name}"
        ),
        "request_kind": request_kind,
        "arguments": [
            {"number": packed_context},
            {"number": "$fixture.track.first"},
        ],
        "render_context": packed_context,
        "fresh_connection": True,
        "expect": {"outcome": "any"},
    }


def main() -> None:
    suite = {
        "name": "context-analysis-track-types",
        "fixture_profile": "full",
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
            case(name, request_kind, track_type)
            for track_type in TRACK_TYPES
            for name, request_kind in REQUESTS
        ],
    }

    OUTPUT.write_text(json.dumps(suite, indent=2) + "\n")


if __name__ == "__main__":
    main()
