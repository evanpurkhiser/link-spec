#!/usr/bin/env python3
"""Generate the fileless artwork/analysis direct-response matrix."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "suites/adjacent-payload-fileless.json"
TRACK_TYPES = range(7)
LOCATIONS = (0, 1, 2, 3, 7, 8, 0xFF)
KINDS = (
    "2003",
    "2103",
    *(f"{value:02x}04" for value in range(0x20, 0x2E)),
)
LOG_ONLY_KINDS = {"2304", "2404", "2604", "2704"}


def number(value: int | str) -> dict[str, int | str]:
    return {"number": value}


def context(location: int, track_type: int) -> int:
    return (1 << 24) | (location << 16) | (3 << 8) | track_type


def arguments(kind: str, location: int, track_type: int, content: int | str) -> list[dict]:
    packed = number(context(location, track_type))
    identifier = number(content)

    if kind in LOG_ONLY_KINDS:
        return [packed]

    if kind in {"2003", "2103", "2104", "2204", "2304", "2404", "2504", "2604", "2704", "2804", "2a04"}:
        return [packed, identifier]
    if kind == "2004":
        return [packed, number(4), identifier, number(0)]
    if kind in {"2904", "2b04"}:
        return [packed, identifier, number(0)]
    if kind in {"2c04", "2d04"}:
        return [packed, identifier, number("0x34565750"), number("0x00545845")]

    raise ValueError(f"unsupported kind {kind}")


def case(
    case_id: str,
    description: str,
    kind: str,
    args: list[dict],
    *,
    fixed_tag_slots: int | None = None,
) -> dict:
    result = {
        "id": case_id,
        "description": description,
        "request_kind": f"0x{kind}",
        "arguments": args,
        "direct_response": True,
        "render": False,
        "fresh_connection": True,
        "expect": {"outcome": "any"},
    }
    if fixed_tag_slots is not None:
        result["fixed_tag_slots"] = fixed_tag_slots
    return result


def build_cases() -> list[dict]:
    cases = []

    for kind in KINDS:
        location = 8 if kind in {"2003", "2103", "2004", "2104", "2204", "2304", "2404", "2504", "2604", "2704", "2804", "2b04"} else 1
        for track_type in TRACK_TYPES:
            cases.append(
                case(
                    f"kind-{kind}--type-{track_type:02x}",
                    f"0x{kind} with packed track type 0x{track_type:02x}",
                    kind,
                    arguments(kind, location, track_type, "$fixture.track.first"),
                    fixed_tag_slots=5 if kind == "2004" else None,
                )
            )

    for kind in KINDS:
        location = 8 if kind in {"2003", "2103", "2004", "2104", "2204", "2304", "2404", "2504", "2604", "2704", "2804", "2b04"} else 1
        if kind in LOG_ONLY_KINDS:
            boundaries = (("context-zero", 0), ("context-maximum", "0xffffffff"))
        else:
            boundaries = (("id-zero", 0), ("id-maximum", "0xffffffff"))
        for label, identifier in boundaries:
            args = (
                [number(identifier)]
                if kind in LOG_ONLY_KINDS
                else arguments(kind, location, 1, identifier)
            )
            cases.append(
                case(
                    f"kind-{kind}--{label}",
                    f"0x{kind} with {label.replace('-', ' ')}",
                    kind,
                    args,
                    fixed_tag_slots=5 if kind == "2004" else None,
                )
            )

    for kind in ("2003", "2004", "2104", "2c04"):
        for location in LOCATIONS:
            cases.append(
                case(
                    f"kind-{kind}--location-{location:02x}",
                    f"0x{kind} with menu location 0x{location:02x}",
                    kind,
                    arguments(kind, location, 1, "$fixture.track.first"),
                    fixed_tag_slots=5 if kind == "2004" else None,
                )
            )

    atom_cases = (
        ("pwv4-ext", "0x34565750", "0x00545845"),
        ("pwv5-ext", "0x35565750", "0x00545845"),
        ("pwv6-2ex", "0x36565750", "0x00584532"),
        ("pssi-ext", "0x49535350", "0x00545845"),
        ("pcp2-ext-short-circuit", "0x32504350", "0x00545845"),
        ("pcpt-ext-short-circuit", "0x54504350", "0x00545845"),
        ("pmai-ext-short-circuit", "0x49414d50", "0x00545845"),
        ("pwv4-dat-rejected", "0x34565750", "0x00544144"),
        ("pwv4-empty-extension", "0x34565750", 0),
        ("empty-tag-ext", 0, "0x00545845"),
        ("maximum-tag-ext", "0xffffffff", "0x00545845"),
        ("pwv4-maximum-extension", "0x34565750", "0xffffffff"),
    )
    for kind in ("2c04", "2d04"):
        for label, tag, extension in atom_cases:
            args = [
                number(context(1, 1)),
                number("$fixture.track.first"),
                number(tag),
                number(extension),
            ]
            cases.append(
                case(
                    f"kind-{kind}--atom-{label}",
                    f"0x{kind} atom control {label}",
                    kind,
                    args,
                )
            )

    return cases


def main() -> None:
    suite = {
        "name": "Rekordbox adjacent payload services with fileless fixture",
        "fixture_profile": "full",
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
    OUTPUT.write_text(json.dumps(suite, indent=2) + "\n")


if __name__ == "__main__":
    main()
