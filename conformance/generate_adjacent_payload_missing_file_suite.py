#!/usr/bin/env python3
"""Generate null, empty, and missing-file payload-path controls."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from generate_adjacent_payload_suite import arguments


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "suites/adjacent-payload-missing-files.json"
FILE_BACKED_KINDS = (
    "2003", "2103", "2004", "2204", "2504", "2804", "2904", "2a04", "2c04", "2d04",
)
PATH_STATES = (
    ("nonempty-missing", "$fixture.track.first"),
    ("empty", "$fixture.track.second"),
    ("null", "$fixture.track.third"),
)


def payload_case(kind: str, state: str, identifier: str) -> dict:
    location = 8 if kind in {"2003", "2103", "2004", "2204", "2504", "2804"} else 1
    result = {
        "id": f"kind-{kind}--path-{state}",
        "description": f"0x{kind} with {state.replace('-', ' ')} database payload path",
        "request_kind": f"0x{kind}",
        "arguments": arguments(kind, location, 1, identifier),
        "direct_response": True,
        "render": False,
        "fresh_connection": True,
        "expect": {"outcome": "any"},
    }
    if kind == "2004":
        result["fixed_tag_slots"] = 5
    return result


def build_cases() -> list[dict]:
    cases = [
        payload_case(kind, state, identifier)
        for kind in FILE_BACKED_KINDS
        for state, identifier in PATH_STATES
    ]
    cases.append(
        payload_case("2003", "playlist-nonempty-missing", "$fixture.playlist.primary")
    )
    return cases


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()

    suite = {
        "name": "Rekordbox adjacent payload null, empty, and missing file paths",
        "fixture_profile": "payload-paths",
        "fixture_version": 1,
        "defaults": {
            "device": 1,
            "context": "0x01010301",
            "sort": 0,
            "root_capabilities": "0x05cfffff",
            "setup": "extended",
            "page_size": 32,
            "read_timeout_ms": 3000,
            "render_arguments": [],
        },
        "cases": build_cases(),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(suite, indent=2) + "\n")


if __name__ == "__main__":
    main()
