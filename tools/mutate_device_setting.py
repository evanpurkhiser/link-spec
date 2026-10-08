#!/usr/bin/env python3
"""Validate and mutate Rekordbox's local DEVSETTING.DAT key style."""

from __future__ import annotations

import argparse
import binascii
import hashlib
import json
import struct
from pathlib import Path


FILE_SIZE = 0x8C
HEADER_SIZE_OFFSET = 0x00
PAYLOAD_SIZE_OFFSET = 0x64
PAYLOAD_OFFSET = 0x68
PAYLOAD_SIZE = 0x20
MAGIC = 0x12345678
KEY_STYLE_OFFSET = 0x74
CRC_OFFSET = 0x88
STYLES = {"classic": 1, "alphanumeric": 2}


def validate(data: bytes) -> dict[str, object]:
    if len(data) != FILE_SIZE:
        raise ValueError(f"expected {FILE_SIZE} bytes, got {len(data)}")
    if struct.unpack_from("<I", data, HEADER_SIZE_OFFSET)[0] != 0x60:
        raise ValueError("invalid DEVSETTING header size")
    if struct.unpack_from("<I", data, PAYLOAD_SIZE_OFFSET)[0] != PAYLOAD_SIZE:
        raise ValueError("invalid DEVSETTING payload size")
    if struct.unpack_from("<I", data, PAYLOAD_OFFSET)[0] != MAGIC:
        raise ValueError("invalid DEVSETTING payload magic")

    stored_crc = struct.unpack_from("<I", data, CRC_OFFSET)[0]
    calculated_crc = binascii.crc_hqx(
        data[PAYLOAD_OFFSET : PAYLOAD_OFFSET + PAYLOAD_SIZE], 0
    )
    if stored_crc != calculated_crc:
        raise ValueError(
            f"invalid DEVSETTING CRC: stored {stored_crc:#06x}, "
            f"calculated {calculated_crc:#06x}"
        )

    style_value = data[KEY_STYLE_OFFSET]
    style_name = next(
        (name for name, value in STYLES.items() if value == style_value),
        "unknown",
    )
    return {
        "sha256": hashlib.sha256(data).hexdigest(),
        "size": len(data),
        "payload_offset": PAYLOAD_OFFSET,
        "payload_size": PAYLOAD_SIZE,
        "key_style_offset": KEY_STYLE_OFFSET,
        "key_style_value": style_value,
        "key_style": style_name,
        "crc_offset": CRC_OFFSET,
        "crc": calculated_crc,
    }


def mutate(data: bytes, style: str) -> bytes:
    validate(data)
    result = bytearray(data)
    result[KEY_STYLE_OFFSET] = STYLES[style]
    crc = binascii.crc_hqx(
        result[PAYLOAD_OFFSET : PAYLOAD_OFFSET + PAYLOAD_SIZE], 0
    )
    struct.pack_into("<I", result, CRC_OFFSET, crc)
    validate(result)
    return bytes(result)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--style", choices=STYLES, required=True)
    args = parser.parse_args()

    result = mutate(args.source.read_bytes(), args.style)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(result)
    print(json.dumps(validate(result), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
