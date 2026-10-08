#!/usr/bin/env python3
"""Generate the complete Hot Cue Bank header/render location cross-product."""

from __future__ import annotations

import json
from pathlib import Path


LOCATIONS = (1, 2, 3, 7)
CONTEXT = {location: f"0x0101{location:02x}01" for location in LOCATIONS}
OUTPUT = Path(__file__).resolve().parent / "suites/hot-cue-bank-location-cross.json"


def case(header_location: int, render_location: int, width: str) -> dict[str, object]:
    declaration: dict[str, object] = {
        "id": (
            f"header-location-{header_location}-render-location-"
            f"{render_location}-{width}"
        ),
        "description": (
            f"Location {header_location} root followed by a location "
            f"{render_location} {width} render"
        ),
        "request_kind": "0x2001",
        "arguments": [
            {"number": CONTEXT[header_location]},
            {"number": 0},
            {"number": 1},
            {"number": 0},
        ],
        "render_context": CONTEXT[render_location],
        "fresh_connection": True,
        "expect": {"outcome": "any"},
    }
    if width == "legacy":
        declaration["render_arguments"] = [0, "$total", 0]

    return declaration


def main() -> None:
    suite = {
        "name": "hot-cue-bank-location-cross",
        "fixture_profile": "hot-cue-banks",
        "fixture_version": 1,
        "repeat_strategy": "reset-and-restart",
        "defaults": {
            "device": 1,
            "context": CONTEXT[3],
            "sort": 0,
            "root_capabilities": "0x05cfffff",
            "setup": "extended",
            "page_size": 32,
            "render_arguments": [0, "$total", 12, 1, 0],
        },
        "cases": [
            case(header_location, render_location, width)
            for header_location in LOCATIONS
            for render_location in LOCATIONS
            for width in ("legacy", "extended")
        ],
    }
    OUTPUT.write_text(json.dumps(suite, indent=2) + "\n")


if __name__ == "__main__":
    main()
