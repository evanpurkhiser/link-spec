#!/usr/bin/env python3
"""Extract typed RemoteDBServer messages from an IPv4 TCP PCAP."""

from __future__ import annotations

import argparse
import ipaddress
import json
import struct
from collections import defaultdict
from pathlib import Path


MARKER = b"\x11\x87\x23\x49\xae"


def packet_records(path: Path):
    data = path.read_bytes()
    magic = data[:4]
    if magic == b"\xa1\xb2\xc3\xd4":
        order = ">"
    elif magic == b"\xd4\xc3\xb2\xa1":
        order = "<"
    else:
        raise ValueError(f"unsupported PCAP magic {magic.hex()}")

    _, _, _, _, _, link_type = struct.unpack_from(f"{order}HHIIII", data, 4)
    if link_type != 113:
        raise ValueError(f"expected Linux cooked v1 link type 113, got {link_type}")

    offset = 24
    while offset < len(data):
        seconds, microseconds, captured, _ = struct.unpack_from(
            f"{order}IIII", data, offset
        )
        offset += 16
        yield seconds * 1_000_000 + microseconds, data[offset : offset + captured]
        offset += captured


def packets(path: Path):
    for _, frame in packet_records(path):
        yield frame


def tcp_segment(frame: bytes):
    if len(frame) < 56 or struct.unpack_from("!H", frame, 14)[0] != 0x0800:
        return None

    ip = frame[16:]
    header_length = (ip[0] & 0x0F) * 4
    if ip[9] != 6 or len(ip) < header_length + 20:
        return None

    total_length = struct.unpack_from("!H", ip, 2)[0]
    source = str(ipaddress.ip_address(ip[12:16]))
    destination = str(ipaddress.ip_address(ip[16:20]))
    tcp = ip[header_length:total_length]
    source_port, destination_port, sequence = struct.unpack_from("!HHI", tcp)
    tcp_header_length = (tcp[12] >> 4) * 4
    payload = tcp[tcp_header_length:]
    if not payload:
        return None

    return (source, source_port, destination, destination_port), sequence, payload


def streams(path: Path):
    segments = defaultdict(dict)
    for frame in packets(path):
        segment = tcp_segment(frame)
        if segment is None:
            continue
        stream, sequence, payload = segment
        previous = segments[stream].get(sequence)
        if previous is None or len(payload) > len(previous):
            segments[stream][sequence] = payload

    for stream, by_sequence in segments.items():
        ordered = sorted(by_sequence.items())
        start = ordered[0][0]
        output = bytearray()
        for sequence, payload in ordered:
            relative = sequence - start
            overlap = len(output) - relative
            if overlap < 0:
                output.extend(b"\x00" * -overlap)
                overlap = 0
            if overlap < len(payload):
                output.extend(payload[overlap:])
        yield stream, bytes(output)


def field(data: bytes, offset: int):
    tag = data[offset]
    if tag in (0x0F, 0x10, 0x11):
        length = {0x0F: 1, 0x10: 2, 0x11: 4}[tag]
        end = offset + 1 + length
        return int.from_bytes(data[offset + 1 : end], "big"), end
    if tag in (0x14, 0x26):
        length = int.from_bytes(data[offset + 1 : offset + 5], "big")
        byte_length = length if tag == 0x14 else length * 2
        end = offset + 5 + byte_length
        value = data[offset + 5 : end]
        if tag == 0x26:
            value = value[:-2].decode("utf-16-be", errors="surrogatepass")
        else:
            value = value.hex()
        return value, end
    raise ValueError(f"unknown field tag 0x{tag:02x}")


def messages(data: bytes):
    cursor = 0
    while (start := data.find(MARKER, cursor)) >= 0:
        try:
            transaction, offset = field(data, start + len(MARKER))
            kind, offset = field(data, offset)
            count, offset = field(data, offset)
            argument_types, offset = field(data, offset)
            arguments = []
            for _ in range(count):
                argument, offset = field(data, offset)
                arguments.append(argument)
        except (IndexError, UnicodeDecodeError, ValueError):
            cursor = start + 1
            continue

        yield {
            "stream_offset": start,
            "transaction": transaction,
            "kind": kind,
            "argument_types": argument_types,
            "arguments": arguments,
        }
        cursor = offset


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pcap", type=Path)
    parser.add_argument("--source")
    parser.add_argument("--destination")
    parser.add_argument("--kind", action="append", type=lambda value: int(value, 0))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    result = []
    for stream, data in streams(args.pcap):
        source, source_port, destination, destination_port = stream
        if args.source and source != args.source:
            continue
        if args.destination and destination != args.destination:
            continue
        for message in messages(data):
            if args.kind and message["kind"] not in args.kind:
                continue
            result.append(
                {
                    "source": source,
                    "source_port": source_port,
                    "destination": destination,
                    "destination_port": destination_port,
                    **message,
                }
            )

    document = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(document)
    else:
        print(document, end="")


if __name__ == "__main__":
    main()
