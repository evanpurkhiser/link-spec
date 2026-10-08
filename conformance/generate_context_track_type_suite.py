#!/usr/bin/env python3
"""Generate an exhaustive ordinary-Track sweep of the packed track-type byte."""

from __future__ import annotations

import json
from pathlib import Path


OUTPUT = Path(__file__).resolve().parent / "suites/context-track-types.json"


def context(track_type: int) -> str:
    return f"0x010103{track_type:02x}"


def case(track_type: int) -> dict[str, object]:
    packed_context = context(track_type)

    return {
        "id": f"track-type-{track_type:02x}",
        "description": f"Packed track-type byte 0x{track_type:02x}",
        "request_kind": "0x1004",
        "arguments": [
            {"number": packed_context},
            {"number": "$sort"},
        ],
        "render_context": packed_context,
        "fresh_connection": True,
        "expect": {"outcome": "any"},
    }


def main() -> None:
    suite = {
        "name": "context-track-types",
        "fixture_profile": "full",
        "fixture_version": 1,
        "repeat_strategy": "reset-and-restart",
        "defaults": {
            "device": 1,
            "context": context(1),
            "sort": 0,
            "root_capabilities": "0x05cfffff",
            "setup": "extended",
            "page_size": 16,
            "render_arguments": [0, "$total", 12, 1, 0],
        },
        "cases": [case(track_type) for track_type in range(0x100)],
    }

    OUTPUT.write_text(json.dumps(suite, indent=2) + "\n")


if __name__ == "__main__":
    main()
