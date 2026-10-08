#!/usr/bin/env python3
"""Generate successful deterministic artwork and analysis payload requests."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from generate_adjacent_payload_suite import arguments, case, number


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "suites/adjacent-payload-success.json"


def packed_context(player: int, location: int, track_type: int) -> int:
    return (player << 24) | (location << 16) | (3 << 8) | track_type


def request_arguments(
    kind: str,
    location: int,
    track_type: int,
    content: int | str,
    player: int,
) -> list[dict]:
    result = arguments(kind, location, track_type, content)
    result[0] = number(packed_context(player, location, track_type))
    return result


def build_cases(player: int = 1) -> list[dict]:
    cases = [
        case(
            "kind-2003--content-artwork",
            "0x2003 returns deterministic content artwork",
            "2003",
            request_arguments("2003", 8, 1, "$fixture.track.first", player),
        ),
        case(
            "kind-2003--playlist-artwork",
            "0x2003 returns deterministic playlist artwork",
            "2003",
            request_arguments("2003", 8, 1, "$fixture.playlist.primary", player),
        ),
        case(
            "kind-2103--content-artwork",
            "0x2103 returns deterministic content artwork",
            "2103",
            request_arguments("2103", 8, 1, "$fixture.track.first", player),
        ),
    ]

    for kind in ("2004", "2204", "2504", "2804", "2904", "2a04"):
        location = 8 if kind in {"2004", "2204", "2504", "2804"} else 1
        cases.append(
            case(
                f"kind-{kind}--deterministic-analysis",
                f"0x{kind} returns deterministic generated analysis data",
                kind,
                request_arguments(kind, location, 1, "$fixture.track.first", player),
                fixed_tag_slots=5 if kind == "2004" else None,
            )
        )

    atoms = (
        ("pwv3-ext", "0x33565750", "0x00545845"),
        ("pkey-ext", "0x59454b50", "0x00545845"),
        ("pwv7-2ex", "0x37565750", "0x00584532"),
    )
    for kind in ("2c04", "2d04"):
        for label, tag, extension in atoms:
            cases.append(
                case(
                    f"kind-{kind}--atom-{label}",
                    f"0x{kind} returns the generated {label} atom",
                    kind,
                    [
                        number(packed_context(player, 1, 1)),
                        number("$fixture.track.first"),
                        number(tag),
                        number(extension),
                    ],
                )
            )

    return cases


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    suite = {
        "name": "Rekordbox adjacent payload successful generated assets",
        "fixture_profile": "payload-valid",
        "fixture_version": 1,
        "defaults": {
            "device": 1,
            "context": "0x01010301",
            "sort": 0,
            "root_capabilities": "0x05cfffff",
            "setup": "extended",
            "page_size": 32,
            "read_timeout_ms": 5000,
            "render_arguments": [],
        },
        "cases": build_cases(),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(suite, indent=2) + "\n")


if __name__ == "__main__":
    main()
