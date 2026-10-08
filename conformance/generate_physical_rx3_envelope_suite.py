#!/usr/bin/env python3
"""Declare the physical RX3 setup/context/mask envelope for Rekordbox 7.2.19."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "suites/generated/physical-rx3-session-envelope.json"


def number(value):
    return {"number": value}


document = {
    "name": "physical-rx3-session-envelope",
    "fixture_profile": "full",
    "fixture_version": 1,
    "repeat_strategy": "fixture-reset-and-restart",
    "defaults": {
        "device": 11,
        "context": "0x0b010401",
        "sort": 0,
        "root_capabilities": "0x05fdffff",
        "setup": "legacy",
        "page_size": 19,
        "render_arguments": [0, "$total", 0],
    },
    "cases": [
        {
            "id": "physical-root-envelope",
            "description": (
                "Physical RX3 player-11 legacy setup, main-menu location 1, "
                "rekordbox slot 4, and "
                "0x05fdffff root mask"
            ),
            "request_kind": "0x1000",
            "arguments": [
                number("$context"),
                number("$sort"),
                number("0x05fdffff"),
            ],
            "fresh_connection": True,
            "expect": {"outcome": "any"},
        },
        {
            "id": "physical-default-track-render",
            "description": (
                "Physical RX3 player-11 Default track request followed by its "
                "six-argument main-menu render"
            ),
            "request_kind": "0x1004",
            "arguments": [number("$context"), number(0)],
            "render_arguments": [0, "$total", 12],
            "fresh_connection": True,
            "expect": {"outcome": "any"},
        },
    ],
}

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(json.dumps(document, indent=2) + "\n")
print(OUTPUT)
