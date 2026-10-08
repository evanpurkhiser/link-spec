#!/usr/bin/env python3
"""Generate XDJ-RR source-defined location-9 Delivery Info suites."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "suites/generated/xdj-rr-location9"
MATRIX = ROOT / "data/xdj-rr-location9-matrix.json"
VARIANTS = (
    ("xdj-rx3-ordinary", 11, "xdj-rx3-player-11.json"),
    ("xdj-rx3-status", 11, "xdj-rx3-player-11-status.json"),
    ("cdj-3000-status", 1, "cdj-3000-player-1-status.json"),
)
SETUPS = ("extended", "legacy")


def context(player: int, location: int) -> str:
    return f"0x{player:02x}{location:02x}0301"


def delivery_case(
    case_id: str,
    description: str,
    player: int,
    request_location: int,
    content: str,
    render_location: int,
) -> dict[str, object]:
    return {
        "id": case_id,
        "description": description,
        "request_kind": "0x2602",
        "arguments": [
            {"number": context(player, request_location)},
            {"number": content},
        ],
        "render_context": context(player, render_location),
        "fresh_connection": True,
        "expect": {"outcome": "any", "total": 13},
    }


def suite(model: str, player: int, setup: str) -> dict[str, object]:
    return {
        "name": f"xdj-rr-location9-{model}-{setup}",
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
        },
        "cases": [
            delivery_case(
                "location-1-first-current",
                "Location 1 first-track Delivery Info rendered at location 1",
                player,
                1,
                "$fixture.track.first",
                1,
            ),
            delivery_case(
                "location-2-first-current",
                "Location 2 first-track Delivery Info rendered at location 2",
                player,
                2,
                "$fixture.track.first",
                2,
            ),
            delivery_case(
                "location-9-second-current",
                "Source-defined location 9 second-track Delivery Info rendered at location 9",
                player,
                9,
                "$fixture.track.second",
                9,
            ),
            delivery_case(
                "location-1-first-render-stale-9",
                "Populate location 1 with the first track and render the prior location-9 second track",
                player,
                1,
                "$fixture.track.first",
                9,
            ),
            delivery_case(
                "location-9-second-render-stale-1",
                "Populate location 9 with the second track and render the prior location-1 first track",
                player,
                9,
                "$fixture.track.second",
                1,
            ),
            delivery_case(
                "location-9-first-current",
                "Source-defined location 9 first-track Delivery Info rendered at location 9",
                player,
                9,
                "$fixture.track.first",
                9,
            ),
        ],
    }


def generate(output: Path, matrix_path: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    variants = []
    for model, player, identity in VARIANTS:
        for setup in SETUPS:
            document = suite(model, player, setup)
            relative_suite = Path("suites/generated/xdj-rr-location9") / (
                f"{model}-{setup}.json"
            )
            (output / f"{model}-{setup}.json").write_text(
                json.dumps(document, indent=2) + "\n"
            )
            variants.append(
                {
                    "id": f"{model}-{setup}",
                    "model": model,
                    "player": player,
                    "setup": setup,
                    "identity": f"runs/{identity}",
                    "suite": str(relative_suite),
                    "golden": (
                        f"goldens/rekordbox-7.2.19/{model}/"
                        f"xdj-rr-location9-{setup}.json"
                    ),
                    "evidence": (
                        f"../data/experiments/xdj-rr-client-navigation/location9/"
                        f"{model}-{setup}"
                    ),
                }
            )

    matrix = {
        "format": 1,
        "source": "data/static-analysis/xdj-rr-client-navigation.json",
        "fixture": "fixtures/generated/full",
        "baseline": "fixtures/generated/play-paths",
        "cases_per_variant": 6,
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
