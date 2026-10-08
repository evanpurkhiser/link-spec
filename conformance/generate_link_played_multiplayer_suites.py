#!/usr/bin/env python3
"""Generate the two-player Link-played ownership sequence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT = ROOT / "suites"
DEFAULT_INDEX = ROOT / "data/link-played-multiplayer.json"


def scalar(identifier: str, track: str, description: str, fresh: bool = False) -> dict:
    case = {
        "id": identifier,
        "description": description,
        "request_kind": "0x3b03",
        "arguments": [{"number": f"$fixture.track.{track}"}],
        "render": False,
        "direct_response": True,
        "expect": {"outcome": "raw_reply"},
    }
    if fresh:
        case["fresh_connection"] = True
        case["delay_before_connection_ms"] = 500
    return case


def tracks(identifier: str, description: str) -> dict:
    return {
        "id": identifier,
        "description": description,
        "request_kind": "0x1004",
        "arguments": [{"number": "$context"}, {"number": "$sort"}],
        "expect": {
            "outcome": "menu",
            "total": 8,
            "row_count": 8,
            "argument_count": 16,
        },
    }


def mutation(action: str, track: str) -> dict:
    insertion = action == "insert"
    return {
        "id": f"{action}-{track}",
        "description": f"Player {action}s the {track} track in Link history",
        "request_kind": "0x3001" if insertion else "0x3401",
        "arguments": [{"number": "$context"}, {"number": f"$fixture.track.{track}"}],
        "render": False,
        **({"send_only": True} if insertion else {}),
        "expect": (
            {"outcome": "sent"}
            if insertion
            else {"outcome": "menu", "total": 0, "row_count": 0}
        ),
    }


def suite(name: str, player: int, action: str, track: str) -> dict:
    verb = "insertion" if action == "insert" else "removal"
    document = {
        "name": name,
        "fixture_profile": "full",
        "fixture_version": 1,
        "repeat_strategy": "fresh-fixture-process-two-simultaneous-identities",
        "defaults": {
            "device": player,
            "context": f"0x{player:02x}010301",
            "sort": 0,
            "root_capabilities": "0x05cfffff",
            "setup": "extended",
            "page_size": 8,
            "render_arguments": [0, "$total", 12, 1, 0],
            "read_timeout_ms": 3000,
        },
        "cases": [
            scalar("first-state-before", "first", f"First-track scalar before player-{player} {verb}"),
            scalar("second-state-before", "second", f"Second-track scalar before player-{player} {verb}"),
            tracks("tracks-before", f"Track rows before player-{player} {verb}"),
            mutation(action, track),
            scalar("first-state-after", "first", f"First-track scalar after player-{player} {verb}", True),
            scalar("second-state-after", "second", f"Second-track scalar after player-{player} {verb}"),
            tracks("tracks-after", f"Track rows after player-{player} {verb}"),
        ],
    }
    if player == 2:
        for case in document["cases"]:
            case["fresh_connection"] = True
            case["delay_before_connection_ms"] = 250
            if not case.get("send_only"):
                case["expect"] = {"outcome": "any"}
    return document


def documents() -> list[tuple[str, dict]]:
    return [
        ("link-played-multiplayer-player-1-prime", suite("link-played-multiplayer-player-1-prime", 1, "insert", "first")),
        ("link-played-multiplayer-player-2-insert", suite("link-played-multiplayer-player-2-insert", 2, "insert", "second")),
        ("link-played-multiplayer-player-1-remove", suite("link-played-multiplayer-player-1-remove", 1, "remove", "first")),
        ("link-played-multiplayer-player-2-remove", suite("link-played-multiplayer-player-2-remove", 2, "remove", "second")),
    ]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    entries = []
    for identifier, document in documents():
        path = args.output / f"{identifier}.json"
        path.write_text(json.dumps(document, indent=2) + "\n")
        entries.append(
            {
                "id": identifier,
                "suite": f"suites/{path.name}",
                "player": document["defaults"]["device"],
                "context": document["defaults"]["context"],
                "case_count": len(document["cases"]),
            }
        )
    index = {
        "format": 1,
        "experiment": "link-played-multiplayer-ownership",
        "identities": [
            "runs/xdj-rx3-player-1.json",
            "runs/xdj-rx3-player-2.json",
        ],
        "sequence": entries,
        "suite_count": len(entries),
        "case_count": sum(entry["case_count"] for entry in entries),
    }
    args.index.parent.mkdir(parents=True, exist_ok=True)
    args.index.write_text(json.dumps(index, indent=2) + "\n")


if __name__ == "__main__":
    main()
