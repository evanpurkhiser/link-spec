#!/usr/bin/env python3
"""Generate XDJ-RR old-Key and silent CueTrack real-Rekordbox suites."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "suites/generated/xdj-rr-old-key"
MATRIX = ROOT / "data/xdj-rr-old-key-matrix.json"
VARIANTS = (
    ("xdj-rx3-ordinary", 11, "xdj-rx3-player-11.json"),
    ("xdj-rx3-status", 11, "xdj-rx3-player-11-status.json"),
    ("cdj-3000-status", 1, "cdj-3000-player-1-status.json"),
)
SETUPS = ("extended", "legacy")


def context(player: int, location: int) -> str:
    return f"0x{player:02x}{location:02x}0301"


def root_case(case_id: str, description: str, player: int, location: int) -> dict:
    return {
        "id": case_id,
        "description": description,
        "request_kind": "0x100b",
        "arguments": [
            {"number": context(player, location)},
            {"number": "$sort"},
        ],
        "fresh_connection": True,
        "expect": {"outcome": "menu", "total": 2, "row_count": 2},
    }


def track_case(
    case_id: str,
    description: str,
    player: int,
    location: int,
    key: str,
) -> dict:
    return {
        "id": case_id,
        "description": description,
        "request_kind": "0x110b",
        "arguments": [
            {"number": context(player, location)},
            {"number": "$sort"},
            {"number": key},
        ],
        "fresh_connection": True,
        "expect": {"outcome": "menu", "total": 4, "row_count": 4},
    }


def cue_case(case_id: str, description: str, player: int, location: int) -> dict:
    return {
        "id": case_id,
        "description": description,
        "request_kind": "0x130c",
        "arguments": [
            {"number": context(player, location)},
            {"number": "$sort"},
        ],
        "render": False,
        "fresh_connection": True,
        "expect": {"outcome": "timeout"},
    }


def suite(model: str, player: int, setup: str) -> dict:
    return {
        "name": f"xdj-rr-old-key-{model}-{setup}",
        "fixture_profile": "full",
        "fixture_version": 1,
        "repeat_strategy": "reset-and-restart",
        "defaults": {
            "device": player,
            "context": context(player, 1),
            "sort": 0,
            "root_capabilities": "0x05cfffff",
            "setup": setup,
            "page_size": 32,
            "render_arguments": [0, "$total", 12, 1, 0],
            "read_timeout_ms": 3000,
        },
        "cases": [
            root_case(
                "old-key-root-location-1",
                "XDJ-RR old-Key root at the left-browser location",
                player,
                1,
            ),
            track_case(
                "old-key-am-tracks-location-1",
                "Tracks selected by the old-Key Am identifier at location 1",
                player,
                1,
                "$fixture.key.am",
            ),
            root_case(
                "old-key-root-location-2",
                "XDJ-RR old-Key root at the fixed right-browser location",
                player,
                2,
            ),
            track_case(
                "old-key-c-tracks-location-2",
                "Tracks selected by the old-Key C identifier at location 2",
                player,
                2,
                "$fixture.key.c",
            ),
            cue_case(
                "cue-track-root-location-1",
                "CueTrack root at location 1 has no Rekordbox reply",
                player,
                1,
            ),
            root_case(
                "old-key-root-after-cue-location-1",
                "Fresh old-Key root proves dbserver health after silent CueTrack location 1",
                player,
                1,
            ),
            cue_case(
                "cue-track-root-location-2",
                "CueTrack root at location 2 has no Rekordbox reply",
                player,
                2,
            ),
            root_case(
                "old-key-root-after-cue-location-2",
                "Fresh old-Key root proves dbserver health after silent CueTrack location 2",
                player,
                2,
            ),
        ],
    }


def generate(output: Path, matrix_path: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    variants = []
    for model, player, identity in VARIANTS:
        for setup in SETUPS:
            document = suite(model, player, setup)
            filename = f"{model}-{setup}.json"
            (output / filename).write_text(json.dumps(document, indent=2) + "\n")
            variants.append(
                {
                    "id": f"{model}-{setup}",
                    "model": model,
                    "player": player,
                    "setup": setup,
                    "identity": f"runs/{identity}",
                    "suite": f"suites/generated/xdj-rr-old-key/{filename}",
                    "golden": (
                        f"goldens/rekordbox-7.2.19/{model}/"
                        f"xdj-rr-old-key-{setup}.json"
                    ),
                    "evidence": (
                        "../data/experiments/xdj-rr-client-navigation/old-key/"
                        f"{model}-{setup}"
                    ),
                }
            )

    matrix = {
        "format": 1,
        "source": "data/static-analysis/xdj-rr-client-navigation.json",
        "dispatch": "data/static-analysis/link-export-dispatch-tables.json",
        "fixture": "fixtures/generated/full",
        "baseline": "fixtures/generated/play-paths",
        "cases_per_variant": 8,
        "variants": variants,
    }
    matrix_path.parent.mkdir(parents=True, exist_ok=True)
    matrix_path.write_text(json.dumps(matrix, indent=2) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--matrix", type=Path, default=MATRIX)
    args = parser.parse_args()
    generate(args.output, args.matrix)


if __name__ == "__main__":
    main()
