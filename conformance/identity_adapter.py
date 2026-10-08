#!/usr/bin/env python3
"""Emit a configurable PRO DJ LINK keepalive on the isolated lab network."""

from __future__ import annotations

import argparse
import hashlib
import json
import socket
import time
from ipaddress import IPv4Address
from pathlib import Path


MAGIC = bytes.fromhex("5173707431576d4a4f4c")
KEEPALIVE_LENGTH = 0x36
NAME_LENGTH = 20
PLAYER_STATUS_LENGTHS = frozenset((0x11C, 0x124))
RX3_PLAYER_STATUS_LENGTH = 0x124
PLAYER_STATUS_KIND = 0x0A
# First player-11 datagram from captures/rx3-rekordbox-working-ap-20260927.pcap.
# SHA-256: 49d262852bc10cbed30f9cd1f40283047b2423d4865ec5d1b240ae5fe6e20987
RX3_PLAYER_STATUS = bytes.fromhex(
    "5173707431576d4a4f4c0a58444a2d5258330000000000000000000000000001050b01000b0001000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001000000000000000000000400000000000000000000000000000000000000000080009e001000007fffffff8000ffff00000000000000ffffffffff01ff00000000000000000000000000000000010000000000000000000000000000000000000000001f010000123456780000000101010101010100000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
)
DEVICE_TYPES = {
    "cdj": 1,
    "mixer": 2,
    "djm": 3,
    "type7": 7,
}


def parse_mac(value: str) -> bytes:
    try:
        result = bytes.fromhex(value.replace(":", "").replace("-", ""))
    except ValueError as error:
        raise argparse.ArgumentTypeError(str(error)) from error
    if len(result) != 6:
        raise argparse.ArgumentTypeError("MAC address must contain six bytes")
    return result


def keepalive(
    *,
    model: str,
    player: int,
    device_type: int,
    mac: bytes,
    address: IPv4Address,
    peers: int,
    generation: int,
    presence: int = 1,
    model_code: int = 0x64,
) -> bytes:
    encoded_name = model.encode("ascii")
    if len(encoded_name) > NAME_LENGTH:
        raise ValueError(f"model name exceeds {NAME_LENGTH} ASCII bytes")

    packet = bytearray(MAGIC)
    packet.extend((0x06, 0x00))
    packet.extend(encoded_name.ljust(NAME_LENGTH, b"\0"))
    packet.extend((0x01, generation))
    packet.extend(KEEPALIVE_LENGTH.to_bytes(2, "big"))
    packet.extend((player, presence))
    packet.extend(mac)
    packet.extend(address.packed)
    packet.extend((peers, 0x00, 0x00, 0x00, device_type, model_code))
    if len(packet) != KEEPALIVE_LENGTH:
        raise AssertionError(f"keepalive is {len(packet)} bytes")
    return bytes(packet)


def player_status(*, model: str, player: int) -> bytes:
    encoded_name = model.encode("ascii")
    if len(encoded_name) > NAME_LENGTH:
        raise ValueError(f"model name exceeds {NAME_LENGTH} ASCII bytes")

    packet = bytearray(RX3_PLAYER_STATUS)
    packet[0x0B : 0x0B + NAME_LENGTH] = encoded_name.ljust(NAME_LENGTH, b"\0")
    packet[0x21] = player
    packet[0x24] = player
    if len(packet) != RX3_PLAYER_STATUS_LENGTH:
        raise AssertionError(f"player status is {len(packet)} bytes")
    return bytes(packet)


def load_status_packet(path: Path, *, model: str, player: int) -> bytes:
    try:
        packet = bytes.fromhex("".join(path.read_text().split()))
    except (OSError, ValueError) as error:
        raise ValueError(f"cannot load status packet {path}: {error}") from error

    if len(packet) not in PLAYER_STATUS_LENGTHS:
        raise ValueError(
            f"status packet is {len(packet)} bytes, expected one of "
            f"{sorted(PLAYER_STATUS_LENGTHS)}"
        )
    if packet[: len(MAGIC)] != MAGIC or packet[0x0A] != PLAYER_STATUS_KIND:
        raise ValueError("status packet does not have a player-status header")

    packet_model = packet[0x0B : 0x0B + NAME_LENGTH].split(b"\0", 1)[0]
    try:
        packet_model_name = packet_model.decode("ascii")
    except UnicodeDecodeError as error:
        raise ValueError("status packet model is not ASCII") from error
    if packet_model_name != model:
        raise ValueError(
            f"status packet model {packet_model_name!r} does not match {model!r}"
        )

    packet_players = (packet[0x21], packet[0x24])
    if packet_players != (player, player):
        raise ValueError(
            f"status packet player fields {packet_players} do not match {player}"
        )

    return packet


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser()
    value.add_argument("--model", required=True)
    value.add_argument("--player", type=int, default=1, choices=range(1, 256))
    value.add_argument("--device-type", choices=DEVICE_TYPES, default="cdj")
    value.add_argument("--generation", type=int, default=3, choices=range(256))
    value.add_argument("--mac", type=parse_mac, default=parse_mac("02:00:00:60:00:01"))
    value.add_argument("--address", type=IPv4Address, default=IPv4Address("172.31.96.50"))
    value.add_argument("--broadcast", type=IPv4Address, default=IPv4Address("172.31.96.255"))
    value.add_argument("--peer-address", type=IPv4Address)
    value.add_argument("--port", type=int, default=50000)
    value.add_argument("--status-port", type=int, default=50002)
    value.add_argument("--source-port", type=int, default=0)
    value.add_argument("--peers", type=int, default=0, choices=range(256))
    value.add_argument("--presence", type=int, default=1, choices=range(256))
    value.add_argument("--model-code", type=int, default=0x64, choices=range(256))
    value.add_argument("--interval", type=float, default=1.5)
    value.add_argument("--status-interval", type=float, default=0.2)
    status = value.add_mutually_exclusive_group()
    status.add_argument(
        "--status-template", choices=("none", "rx3-captured"), default="none"
    )
    status.add_argument("--status-packet-hex", type=Path)
    value.add_argument("--count", type=int, default=0, help="zero sends until interrupted")
    value.add_argument("--manifest", type=Path)
    value.add_argument("--manifest-only", action="store_true")
    value.add_argument("--packet-hex", action="store_true")
    return value


def main() -> None:
    args = parser().parse_args()
    packet = keepalive(
        model=args.model,
        player=args.player,
        device_type=DEVICE_TYPES[args.device_type],
        mac=args.mac,
        address=args.address,
        peers=args.peers,
        generation=args.generation,
        presence=args.presence,
        model_code=args.model_code,
    )
    if args.status_packet_hex is not None:
        status = load_status_packet(
            args.status_packet_hex,
            model=args.model,
            player=args.player,
        )
    elif args.status_template == "rx3-captured":
        status = player_status(model=args.model, player=args.player)
    else:
        status = None
    if args.packet_hex:
        print(packet.hex())
        return

    identity = {
        "model": args.model,
        "player": args.player,
        "device_type": args.device_type,
        "generation": args.generation,
        "mac": args.mac.hex(":"),
        "address": str(args.address),
        "broadcast": str(args.broadcast),
        "peer_address": str(args.peer_address) if args.peer_address else None,
        "port": args.port,
        "source_port": args.source_port,
        "status_port": args.status_port,
        "status_template": args.status_template,
        "status_packet_hex_path": (
            str(args.status_packet_hex) if args.status_packet_hex is not None else None
        ),
        "status_packet_bytes": len(status) if status else None,
        "status_packet_sha256": hashlib.sha256(status).hexdigest() if status else None,
        "peers": args.peers,
        "presence": args.presence,
        "model_code": args.model_code,
        "packet_sha256": hashlib.sha256(packet).hexdigest(),
    }
    if args.manifest is not None:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(json.dumps(identity, indent=2, sort_keys=True) + "\n")
    if args.manifest_only:
        if args.manifest is None:
            raise SystemExit("--manifest-only requires --manifest")
        return
    print(json.dumps(identity, sort_keys=True), flush=True)

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as output, socket.socket(
        socket.AF_INET, socket.SOCK_DGRAM
    ) as status_output:
        output.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        output.bind((str(args.address), args.source_port))
        status_output.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        status_output.bind((str(args.address), 0))
        destinations = [args.broadcast]
        if args.peer_address is not None:
            destinations.append(args.peer_address)
        sent = 0
        next_keepalive = time.monotonic()
        next_status = time.monotonic()
        while args.count == 0 or sent < args.count:
            now = time.monotonic()
            if now >= next_keepalive:
                for destination in destinations:
                    output.sendto(packet, (str(destination), args.port))
                sent += 1
                next_keepalive = now + args.interval

            if status is not None and now >= next_status:
                status_destinations = (
                    [args.peer_address] if args.peer_address else [args.broadcast]
                )
                for destination in status_destinations:
                    status_output.sendto(status, (str(destination), args.status_port))
                next_status = now + args.status_interval

            if args.count == 0 or sent < args.count:
                deadlines = [next_keepalive]
                if status is not None:
                    deadlines.append(next_status)
                time.sleep(max(0, min(deadlines) - time.monotonic()))


if __name__ == "__main__":
    main()
