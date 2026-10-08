#!/usr/bin/env python3
"""Generate the Play Song Info CLSSyncMethod=0 authority suite."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "suites/generated/song-info-cloud-sync-zero.json"
SYMBOLS = (
    "first",
    "second",
    "third",
    "fourth",
    "fifth",
    "sixth",
    "seventh",
    "eighth",
    "ninth",
    "tenth",
)
DESCRIPTIONS = (
    "null service local-path control",
    "negative service local-path control",
    "zero service local-path control",
    "service 1 with mismatched DBID and existing original file",
    "service 1 with mismatched DBID and existing original directory",
    "service 2 with missing original and existing moved-root candidate",
    "service 2 with missing original and missing moved-root candidate",
    "service 1 outside the download-root helper domain",
    "service 5 with missing original and existing moved-root candidate",
    "service 6 outside the download-root helper domain",
)


def main() -> None:
    cases = [
        {
            "id": f"track-{index:02}",
            "description": f"CLSSyncMethod zero: {description}",
            "request_kind": "0x2102",
            "arguments": [
                {"number": "$context"},
                {"number": f"$fixture.track.{symbol}"},
            ],
            "fresh_connection": True,
            "expect": {"outcome": "any"},
        }
        for index, (symbol, description) in enumerate(
            zip(SYMBOLS, DESCRIPTIONS, strict=True), start=1
        )
    ]
    suite = {
        "name": "song-info-cloud-sync-zero",
        "description": (
            "Real-Rekordbox authority for the zero branch of Play Song Info's "
            "CLSSyncMethod decision"
        ),
        "fixture_profile": "cloud-sync-zero",
        "fixture_version": 1,
        "repeat_strategy": "fixture-settings-reset-and-restart",
        "defaults": {
            "device": 1,
            "context": "0x01010301",
            "sort": 0,
            "root_capabilities": "0x05cfffff",
            "setup": "extended",
            "page_size": 3,
            "render_arguments": [0, "$total", 12, 1, 0],
        },
        "cases": cases,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(suite, indent=2) + "\n")
    print(OUTPUT)


if __name__ == "__main__":
    main()
