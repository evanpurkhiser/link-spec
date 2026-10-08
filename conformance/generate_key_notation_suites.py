#!/usr/bin/env python3
"""Generate the preference-state suites for the Link Export key-notation cross."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "suites/generated"
STATES = tuple(
    f"{notation}-{source}"
    for notation in ("classic", "alphanumeric")
    for source in ("normalized", "database")
)


def number(value: object) -> dict[str, object]:
    return {"number": value}


def track_case(
    case_id: str,
    description: str,
    request_kind: str,
    arguments: list[object],
    *,
    render_arguments: list[object] | None = None,
    total: int = 8,
) -> dict[str, object]:
    case = {
        "id": case_id,
        "description": description,
        "request_kind": request_kind,
        "arguments": [number(value) for value in arguments],
        "expect": {
            "outcome": "menu",
            "total": total,
            "row_count": total,
            "argument_count": 16,
        },
    }
    if render_arguments is not None:
        case["render_arguments"] = render_arguments
    return case


def cases(
    state: str, prefix_label: str = "Key-notation preference"
) -> list[dict[str, object]]:
    prefix = f"{prefix_label} {state}:"
    playlist = "$fixture.playlist.smart_matrix.logic_any"
    result = [
        {
            "id": "key-root",
            "description": f"{prefix} normalized key root",
            "request_kind": "0x1014",
            "arguments": [number("$context"), number("$sort")],
            "expect": {"outcome": "menu", "total": 24, "row_count": 24},
        },
        {
            "id": "key-distances",
            "description": f"{prefix} key-distance submenu",
            "request_kind": "0x1114",
            "arguments": [number("$context"), number("$sort"), number(1)],
            "expect": {"outcome": "menu", "total": 3, "row_count": 3},
        },
        {
            "id": "key-tracks",
            "description": f"{prefix} exact key-distance tracks",
            "request_kind": "0x1214",
            "arguments": [
                number("$context"),
                number("$sort"),
                number(1),
                number(0),
            ],
            "expect": {"outcome": "menu", "total": 8, "row_count": 8},
        },
        track_case(
            "collection-bpm",
            f"{prefix} collection rows with BPM secondary",
            "0x1004",
            ["$context", "$sort"],
            render_arguments=[0, "$total", 12, 1, 4],
        ),
        track_case(
            "collection-key",
            f"{prefix} collection rows with Key secondary",
            "0x1004",
            ["$context", "$sort"],
            render_arguments=[0, "$total", 12, 1, 12],
        ),
        track_case(
            "collection-key-sort",
            f"{prefix} collection rows sorted by Key",
            "0x1004",
            ["$context", 12],
            render_arguments=[0, "$total", 12, 1, 12],
        ),
        track_case(
            "smart-bpm",
            f"{prefix} SmartList rows with BPM secondary",
            "0x1105",
            ["$context", "$sort", playlist, 0],
            render_arguments=[0, "$total", 12, 1, 4],
        ),
        track_case(
            "smart-key",
            f"{prefix} SmartList rows with Key secondary",
            "0x1105",
            ["$context", "$sort", playlist, 0],
            render_arguments=[0, "$total", 12, 1, 12],
        ),
        track_case(
            "smart-key-sort",
            f"{prefix} SmartList rows sorted by Key",
            "0x1105",
            ["$context", 12, playlist, 0],
            render_arguments=[0, "$total", 12, 1, 12],
        ),
    ]

    for family, request_kind, total in (
        ("display", "0x2002", 16),
        ("delivery", "0x2602", 13),
    ):
        for selector, label in ((4, "bpm"), (12, "key")):
            result.append(
                track_case(
                    f"{family}-{label}",
                    f"{prefix} {family.title()} Song Info with {label.upper()} secondary",
                    request_kind,
                    ["$context", "$fixture.track.first"],
                    render_arguments=[0, "$total", 12, 1, selector],
                    total=total,
                )
            )

    return result


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for state in STATES:
        suite = {
            "name": f"key-notation-{state}",
            "description": (
                "Link Export key display and menu behavior under the "
                f"Rekordbox {state} preference state"
            ),
            "fixture_profile": "key-notation",
            "fixture_version": 1,
            "repeat_strategy": "fixture-reset-and-restart",
            "defaults": {
                "device": 1,
                "context": "0x01010301",
                "sort": 0,
                "root_capabilities": "0x05cfffff",
                "setup": "extended",
                "page_size": 10,
                "render_arguments": [0, "$total", 12, 1, 0],
            },
            "cases": cases(state),
        }
        output = OUTPUT / f"key-notation-{state}.json"
        output.write_text(json.dumps(suite, indent=2) + "\n")
        print(output)


if __name__ == "__main__":
    main()
