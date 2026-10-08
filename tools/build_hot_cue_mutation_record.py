#!/usr/bin/env python3
"""Build the canonical safe 0x2401 Hot Cue Bank mutation record."""

from __future__ import annotations

import struct


RECORD_SIZE = 124
OPTION_BYTES = 66


def build_record() -> bytes:
    record = bytearray(RECORD_SIZE)
    struct.pack_into("<I", record, 0x00, RECORD_SIZE)
    struct.pack_into("<H", record, 0x04, 1)  # bank slot
    record[0x06] = 2  # loop
    struct.pack_into("<H", record, 0x0A, 1000)  # milliseconds
    struct.pack_into("<i", record, 0x0C, 456_789)
    struct.pack_into("<i", record, 0x10, 567_890)
    struct.pack_into("<I", record, 0x18, 8)
    struct.pack_into("<i", record, 0x20, -1)
    struct.pack_into("<i", record, 0x24, 0x01020304)
    struct.pack_into("<i", record, 0x28, 0x11121314)
    struct.pack_into("<i", record, 0x2C, 0x21222324)
    struct.pack_into("<i", record, 0x30, 0x31323334)
    struct.pack_into("<I", record, 0x34, OPTION_BYTES)

    record[0x3A] = 6  # Color 5 plus one
    struct.pack_into("<I", record, 0x3C, 0x0A0B0C0D)
    struct.pack_into("<HH", record, 0x42, 0x1234, 0x5678)
    struct.pack_into("<H", record, 0x48, 0)  # empty UTF-16 comment
    struct.pack_into("<Q", record, 0x4A, 44)  # empty seek option block
    return bytes(record)


def main() -> None:
    print(build_record().hex())


if __name__ == "__main__":
    main()
