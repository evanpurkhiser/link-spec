#!/usr/bin/env python3
"""Reduce the retained physical RX3 RemoteDBServer session envelope."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from extract_dbserver_pcap import messages, streams  # noqa: E402


PCAP = (
    ROOT
    / "data/experiments/sort-secondary-render-6/"
    "source-rx3-rekordbox-working-ap-20260927.pcap"
)
OUTPUT = ROOT / "data/experiments/physical-rx3-session/session-envelope.json"
EXPECTED_SHA256 = "bee17ddfa72b093479a68c1590953ddc79629cdf43905769761c656a5149aa2b"
PLAYER = "10.0.0.143"
REKORDBOX = "10.0.0.119"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def typed_message(message: dict) -> dict:
    return {
        "transaction": message["transaction"],
        "kind": message["kind"],
        "argument_types": message["argument_types"],
        "arguments": message["arguments"],
    }


def unpack_context(value: int) -> dict[str, object]:
    raw = value.to_bytes(4, "big")
    return {
        "value": value,
        "hex": f"0x{value:08x}",
        "requester": raw[0],
        "menu_location": raw[1],
        "media_slot": raw[2],
        "track_type": raw[3],
    }


def summarize() -> dict[str, object]:
    if sha256(PCAP) != EXPECTED_SHA256:
        raise SystemExit("unexpected physical RX3 PCAP hash")

    decoded = []
    for stream, data in streams(PCAP):
        source, source_port, destination, destination_port = stream
        for message in messages(data):
            decoded.append(
                {
                    "source": source,
                    "source_port": source_port,
                    "destination": destination,
                    "destination_port": destination_port,
                    **message,
                }
            )

    requests = [
        item
        for item in decoded
        if item["source"] == PLAYER and item["destination"] == REKORDBOX
    ]
    responses = [
        item
        for item in decoded
        if item["source"] == REKORDBOX and item["destination"] == PLAYER
    ]
    setup_request = [item for item in requests if item["kind"] == 0]
    setup_response = [
        item
        for item in responses
        if item["transaction"] == 0xFFFFFFFE and item["kind"] == 0x4000
    ]
    if len(setup_request) != 1 or len(setup_response) != 1:
        raise SystemExit("physical setup exchange is not unique")
    if setup_request[0]["arguments"] != [11]:
        raise SystemExit("physical setup requester changed")
    if setup_response[0]["arguments"] != [0, 0x29]:
        raise SystemExit("physical setup response changed")

    root_request = [item for item in requests if item["kind"] == 0x1000]
    if len(root_request) != 1 or root_request[0]["arguments"] != [
        0x0B010401,
        0,
        0x05FDFFFF,
    ]:
        raise SystemExit("physical root request changed")
    root_header = [
        item
        for item in responses
        if item["transaction"] == root_request[0]["transaction"]
    ]
    if len(root_header) != 1 or root_header[0]["arguments"] != [0x1000, 19]:
        raise SystemExit("physical root header changed")

    root_render = next(
        item
        for item in requests
        if item["kind"] == 0x3000
        and item["arguments"] == [0x0B010401, 0, 19, 0, 19, 0]
    )
    root_render_responses = [
        item
        for item in responses
        if item["transaction"] == root_render["transaction"]
    ]
    root_rows = [item for item in root_render_responses if item["kind"] == 0x4101]
    if len(root_rows) != 19:
        raise SystemExit("physical root row count changed")

    default_sort_pairs = []
    for index, request in enumerate(requests[:-1]):
        if request["kind"] != 0x1004 or request["arguments"] != [0x0B010401, 0]:
            continue
        render = requests[index + 1]
        if render["kind"] != 0x3000:
            raise SystemExit("physical default sort is not followed by render")
        default_sort_pairs.append(
            {
                "request": typed_message(request),
                "render": typed_message(render),
            }
        )
    if len(default_sort_pairs) != 3:
        raise SystemExit("physical default-sort pair count changed")

    contexts = sorted(
        {
            item["arguments"][0]
            for item in requests
            if item["arguments"]
            and isinstance(item["arguments"][0], int)
            and item["arguments"][0] >> 24 == 11
        }
    )
    context_rows = [unpack_context(value) for value in contexts]
    if {row["requester"] for row in context_rows} != {11}:
        raise SystemExit("physical context requester changed")

    request_kinds = Counter(item["kind"] for item in requests)
    return {
        "format": 1,
        "scope": "retained physical XDJ-RX3 RemoteDBServer session envelope",
        "source": {
            "path": str(PCAP.relative_to(ROOT)),
            "sha256": EXPECTED_SHA256,
            "rekordbox_version": "not established by this packet capture",
        },
        "stream": {
            "player_address": PLAYER,
            "player_port": setup_request[0]["source_port"],
            "rekordbox_address": REKORDBOX,
            "rekordbox_port": setup_request[0]["destination_port"],
        },
        "setup": {
            "form": "legacy one-argument",
            "request": typed_message(setup_request[0]),
            "response": typed_message(setup_response[0]),
            "requester_player": 11,
            "response_second_value": 0x29,
        },
        "root": {
            "request": typed_message(root_request[0]),
            "response": typed_message(root_header[0]),
            "render": typed_message(root_render),
            "rows": [typed_message(item) for item in root_rows],
            "capability_mask": "0x05fdffff",
            "total": 19,
        },
        "default_track_sort_render_pairs": default_sort_pairs,
        "packed_contexts": context_rows,
        "request_kind_counts": {
            f"0x{kind:04x}": count for kind, count in sorted(request_kinds.items())
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summarize(), indent=2) + "\n")
    print(args.output)


if __name__ == "__main__":
    main()
