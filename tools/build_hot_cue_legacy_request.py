#!/usr/bin/env python3
"""Build deterministic 0x2201 cue and millisecond-extension blobs."""

from __future__ import annotations

import argparse
import struct


CUE_FLAG_BASE = 0x00000100
CUE_SENTINELS = (
    0x11111111,
    0x22222222,
    0x33333333,
    0x44444444,
    0x55555555,
    0x66666666,
)
EXTENSION_SENTINELS = (0x77777777, 0x88888888)


def build_cue(content_id: int, ordinal: int = 4) -> bytes:
    if not 0 <= ordinal <= 0xFFFF:
        raise ValueError(f"legacy Hot Cue Bank ordinal must fit uint16: {ordinal}")

    return struct.pack(
        "<9I",
        CUE_FLAG_BASE | ordinal << 16,
        content_id,
        0,
        *CUE_SENTINELS,
    )


def build_extension() -> bytes:
    return struct.pack("<2I", *EXTENSION_SENTINELS)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--content-id", type=lambda value: int(value, 0), default=10001)
    parser.add_argument("--ordinal", type=lambda value: int(value, 0), default=4)
    args = parser.parse_args()

    print(f"cue={build_cue(args.content_id, args.ordinal).hex()}")
    print(f"extension={build_extension().hex()}")


if __name__ == "__main__":
    main()
