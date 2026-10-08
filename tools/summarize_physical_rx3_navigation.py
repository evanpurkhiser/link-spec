#!/usr/bin/env python3
"""Reduce the complete retained physical RX3 RemoteDBServer transaction trace."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from extract_dbserver_pcap import (  # noqa: E402
    messages,
    packet_records,
    streams,
    tcp_segment,
)
from summarize_physical_rx3_session import (  # noqa: E402
    EXPECTED_SHA256,
    PCAP,
    PLAYER,
    REKORDBOX,
    unpack_context,
)


OUTPUT = ROOT / "data/experiments/physical-rx3-session/navigation-transcript.json"
REQUEST_NAMES = {
    0x0000: "setup",
    0x0001: "cancel request (Dysentery: invalid data)",
    0x1000: "root menu",
    0x1004: "track menu",
    0x2002: "Display Song Info",
    0x2003: "artwork",
    0x2004: "preview waveform",
    0x2102: "Play Song Info",
    0x2103: "content artwork",
    0x2204: "beat grid",
    0x2504: "VBR information",
    0x2B04: "extended cue information",
    0x2C04: "specified analysis atom",
    0x2D04: "specified analysis atom alternate",
    0x3000: "render list buffer",
    0x3100: "list-buffer offset",
}
RESPONSE_NAMES = {
    0x0100: "connection close",
    0x4000: "menu/setup header",
    0x4001: "render header",
    0x4002: "image response",
    0x4101: "menu row",
    0x4201: "render footer",
    0x4402: "preview waveform response",
    0x4502: "VBR response",
    0x4602: "beat-grid response",
    0x4E02: "cue response",
    0x4F02: "specified-atom response",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def argument_type(message: dict[str, object], index: int) -> int | None:
    raw = str(message["argument_types"])
    start = index * 2
    if start + 2 > len(raw):
        return None
    return int(raw[start : start + 2], 16)


def summarize_argument(
    message: dict[str, object], index: int, value: object
) -> object:
    tag = argument_type(message, index)
    if tag != 3 or not isinstance(value, str):
        return value

    payload = bytes.fromhex(value)
    return {
        "blob_bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "prefix_hex": payload[:16].hex(),
    }


def summarize_message(message: dict[str, object]) -> dict[str, object]:
    return {
        "kind": f"0x{message['kind']:04x}",
        "name": RESPONSE_NAMES.get(message["kind"], "unknown"),
        "arguments": [
            summarize_argument(message, index, value)
            for index, value in enumerate(message["arguments"])
        ],
    }


def decode() -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    requests = []
    responses = []
    for stream, data in streams(PCAP):
        source, source_port, destination, destination_port = stream
        for message in messages(data):
            item = {
                "source": source,
                "source_port": source_port,
                "destination": destination,
                "destination_port": destination_port,
                **message,
            }
            if source == PLAYER and destination == REKORDBOX:
                requests.append(item)
            elif source == REKORDBOX and destination == PLAYER:
                responses.append(item)
    return requests, responses


def timed_message_events() -> list[dict[str, object]]:
    segments = defaultdict(dict)
    for timestamp_us, frame in packet_records(PCAP):
        segment = tcp_segment(frame)
        if segment is None:
            continue
        stream, sequence, payload = segment
        current = segments[stream].get(sequence)
        if current is None or len(payload) > len(current[1]):
            segments[stream][sequence] = (timestamp_us, payload)
        elif len(payload) == len(current[1]) and timestamp_us < current[0]:
            segments[stream][sequence] = (timestamp_us, payload)

    events = []
    for stream, data in streams(PCAP):
        ordered = sorted(segments[stream].items())
        start_sequence = ordered[0][0]
        for message in messages(data):
            message_sequence = start_sequence + message["stream_offset"]
            timestamp_us = min(
                timestamp
                for sequence, (timestamp, payload) in ordered
                if sequence <= message_sequence < sequence + len(payload)
            )
            source, _, destination, _ = stream
            events.append(
                {
                    "timestamp_us": timestamp_us,
                    "source": source,
                    "destination": destination,
                    "transaction": message["transaction"],
                    "kind": message["kind"],
                }
            )
    return sorted(events, key=lambda event: event["timestamp_us"])


def cancellation_commands() -> list[dict[str, object]]:
    events = timed_message_events()
    reports = [
        event
        for event in events
        if event["source"] == PLAYER and event["kind"] == 0x0001
    ]
    result = []
    for report in reports:
        transaction = report["transaction"]
        artwork = next(
            event
            for event in events
            if event["source"] == PLAYER
            and event["transaction"] == transaction
            and event["kind"] == 0x2003
        )
        responses = [
            event
            for event in events
            if event["source"] == REKORDBOX
            and event["transaction"] == transaction
        ]
        result.append(
            {
                "transaction": transaction,
                "transaction_hex": f"0x{transaction:08x}",
                "artwork_request_timestamp_us": artwork["timestamp_us"],
                "report_timestamp_us": report["timestamp_us"],
                "delay_after_artwork_request_us": (
                    report["timestamp_us"] - artwork["timestamp_us"]
                ),
                "responses_before_report": [
                    f"0x{event['kind']:04x}"
                    for event in responses
                    if event["timestamp_us"] < report["timestamp_us"]
                ],
                "responses_after_report": [
                    f"0x{event['kind']:04x}"
                    for event in responses
                    if event["timestamp_us"] > report["timestamp_us"]
                ],
            }
        )
    return result


def exchange(
    transaction: int,
    request_messages: list[dict[str, object]],
    response_messages: list[dict[str, object]],
) -> dict[str, object]:
    rows = [message for message in response_messages if message["kind"] == 0x4101]
    other_responses = [
        summarize_message(message)
        for message in response_messages
        if message["kind"] != 0x4101
    ]
    request_rows = []
    for message in request_messages:
        arguments = message["arguments"]
        row = {
            "kind": f"0x{message['kind']:04x}",
            "name": REQUEST_NAMES.get(message["kind"], "unknown"),
            "arguments": arguments,
        }
        if (
            arguments
            and isinstance(arguments[0], int)
            and arguments[0] >> 24 == 11
        ):
            row["context"] = unpack_context(arguments[0])
        request_rows.append(row)

    return {
        "transaction": transaction,
        "transaction_hex": f"0x{transaction:08x}",
        "requests": request_rows,
        "response_message_count": len(response_messages),
        "response_kinds": {
            f"0x{kind:04x}": count
            for kind, count in sorted(
                Counter(message["kind"] for message in response_messages).items()
            )
        },
        "responses_except_rows": other_responses,
        "row_count": len(rows),
        "row_projections": [
            {
                "argument_0": row["arguments"][0],
                "argument_1": row["arguments"][1],
                "argument_3": row["arguments"][3],
                "argument_5": row["arguments"][5],
                "argument_6": row["arguments"][6],
            }
            for row in rows
        ],
    }


def summarize() -> dict[str, object]:
    if sha256(PCAP) != EXPECTED_SHA256:
        raise SystemExit("unexpected physical RX3 PCAP hash")

    requests, responses = decode()
    requests_by_transaction = defaultdict(list)
    responses_by_transaction = defaultdict(list)
    for message in requests:
        requests_by_transaction[message["transaction"]].append(message)
    for message in responses:
        responses_by_transaction[message["transaction"]].append(message)

    transactions = sorted(
        requests_by_transaction,
        key=lambda value: (-1 if value == 0xFFFFFFFE else value),
    )
    exchanges = [
        exchange(
            transaction,
            requests_by_transaction[transaction],
            responses_by_transaction.get(transaction, []),
        )
        for transaction in transactions
    ]
    contexts = sorted(
        {
            message["arguments"][0]
            for message in requests
            if message["arguments"]
            and isinstance(message["arguments"][0], int)
            and message["arguments"][0] >> 24 == 11
        }
    )
    duplicate_transactions = [
        {
            "transaction": transaction,
            "request_kinds": [
                f"0x{message['kind']:04x}"
                for message in requests_by_transaction[transaction]
            ],
        }
        for transaction in transactions
        if len(requests_by_transaction[transaction]) > 1
    ]

    return {
        "format": 1,
        "scope": "complete retained physical XDJ-RX3 RemoteDBServer transaction trace",
        "source": {
            "path": str(PCAP.relative_to(ROOT)),
            "sha256": EXPECTED_SHA256,
            "rekordbox_version": "not established by this packet capture",
        },
        "stream": {
            "player_address": PLAYER,
            "rekordbox_address": REKORDBOX,
        },
        "counts": {
            "request_messages": len(requests),
            "request_transactions": len(requests_by_transaction),
            "response_messages": len(responses),
            "response_transactions": len(responses_by_transaction),
            "menu_rows": sum(
                message["kind"] == 0x4101 for message in responses
            ),
        },
        "request_kinds": [
            {
                "kind": f"0x{kind:04x}",
                "name": REQUEST_NAMES.get(kind, "unknown"),
                "count": count,
            }
            for kind, count in sorted(
                Counter(message["kind"] for message in requests).items()
            )
        ],
        "response_kinds": [
            {
                "kind": f"0x{kind:04x}",
                "name": RESPONSE_NAMES.get(kind, "unknown"),
                "count": count,
            }
            for kind, count in sorted(
                Counter(message["kind"] for message in responses).items()
            )
        ],
        "contexts": [unpack_context(value) for value in contexts],
        "duplicate_request_transactions": duplicate_transactions,
        "cancellation_commands": cancellation_commands(),
        "exchanges": exchanges,
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
