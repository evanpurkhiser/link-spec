#!/usr/bin/env python3
"""Generate matched-status/setup crosses for successful payload services."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from generate_adjacent_payload_success_suite import build_cases, packed_context


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "suites/generated/adjacent-payload-success-status"


def suite(player: int, setup: str) -> dict:
    return {
        "name": f"adjacent-payload-success-status-player-{player}-{setup}",
        "fixture_profile": "payload-valid",
        "fixture_version": 1,
        "defaults": {
            "device": player,
            "context": f"0x{packed_context(player, 1, 1):08x}",
            "sort": 0,
            "root_capabilities": "0x05cfffff",
            "setup": setup,
            "page_size": 32,
            "read_timeout_ms": 5000,
            "render_arguments": [],
        },
        "cases": build_cases(player),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    for player in (1, 11):
        for setup in ("extended", "legacy"):
            document = suite(player, setup)
            output = args.output_dir / f"player-{player}-{setup}.json"
            output.write_text(json.dumps(document, indent=2) + "\n")


if __name__ == "__main__":
    main()
