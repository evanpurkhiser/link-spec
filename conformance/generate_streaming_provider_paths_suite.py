#!/usr/bin/env python3
"""Generate the authority-only production-shaped streaming-path suite."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "suites/generated/streaming-provider-paths.json"


def number(value: object) -> dict[str, object]:
    return {"number": value}


def menu_case(
    case_id: str,
    description: str,
    request_kind: str,
    arguments: list[dict[str, object]],
) -> dict[str, object]:
    return {
        "id": case_id,
        "description": description,
        "request_kind": request_kind,
        "arguments": arguments,
        "expect": {"outcome": "menu"},
    }


def main() -> None:
    cases = [
        menu_case(
            "collection-default",
            "Collection authority for production-shaped Beatport path boundaries",
            "0x1004",
            [number("$context"), number(0)],
        ),
        menu_case(
            "collection-key-sort",
            "Explicit sorting preserves the same path-admission result",
            "0x1004",
            [number("$context"), number(12)],
        ),
        menu_case(
            "file-name",
            "File Name uses the shared track-insertion visibility gate",
            "0x1013",
            [number("$context"), number(0)],
        ),
        menu_case(
            "ordinary-playlist",
            "Ordinary playlist membership applies provider path visibility",
            "0x1105",
            [
                number("$context"),
                number(0),
                number("$fixture.playlist.primary"),
                number(0),
            ],
        ),
        menu_case(
            "smart-playlist",
            "Smart playlist rule candidates apply provider path visibility",
            "0x1105",
            [
                number("$context"),
                number(0),
                number("$fixture.playlist.visibility_smart"),
                number(0),
            ],
        ),
        menu_case(
            "search",
            "Search applies provider path visibility to matching tracks",
            "0x1300",
            [
                number("$context"),
                number(0),
                {"utf16_bytes": "PROVIDER PATH"},
                {"string": "PROVIDER PATH"},
                number(0),
            ],
        ),
        menu_case(
            "history",
            "Persisted History retains the Windows AppSync platform control",
            "0x1112",
            [
                number("$context"),
                number(0),
                number("$fixture.history.one"),
            ],
        ),
    ]
    suite = {
        "name": "streaming-provider-paths",
        "description": (
            "Real-Rekordbox authority for the Beatport catalog substring, "
            "case and near-match boundaries, scheme controls, and History split"
        ),
        "fixture_profile": "streaming-provider-paths",
        "fixture_version": 1,
        "repeat_strategy": "fixture-reset-and-restart",
        "defaults": {
            "device": 1,
            "context": "0x01010301",
            "sort": 0,
            "root_capabilities": "0x05cfffff",
            "setup": "extended",
            "page_size": 20,
            "render_arguments": [0, "$total", 20, 1, 0],
        },
        "cases": cases,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(suite, indent=2) + "\n")
    print(OUTPUT)


if __name__ == "__main__":
    main()
