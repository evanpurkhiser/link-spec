#!/usr/bin/env python3
"""Generate deterministic djprofile.nxs validation profiles."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "conformance/user-info-djid-profiles"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def valid_prefix() -> bytes:
    prefix = bytearray(32)
    prefix[0:4] = (0x01020304).to_bytes(4, "little")
    prefix[4:8] = (0x11121314).to_bytes(4, "big")
    prefix[8:12] = (0x21222324).to_bytes(4, "big")
    prefix[12:16] = (0x31323334).to_bytes(4, "big")
    prefix[16:28] = bytes(range(0xA0, 0xAC))
    checksum = sum((0x01020304, 0x11121314, 0x21222324, 0x31323334))
    prefix[28:32] = (checksum & 0xFFFFFFFF).to_bytes(4, "big")
    return bytes(prefix)


def profiles() -> dict[str, tuple[bytes, str]]:
    prefix = valid_prefix()
    zero_tail = prefix + bytes(128)
    pattern_tail = prefix + bytes((index * 37 + 11) & 0xFF for index in range(128))
    invalid_checksum = bytearray(zero_tail)
    invalid_checksum[31] ^= 0x01

    return {
        "valid-zero-tail": (zero_tail, "valid"),
        "valid-pattern-tail": (pattern_tail, "valid"),
        "checksum-invalid": (bytes(invalid_checksum), "invalid-checksum"),
        "short-159": (zero_tail[:-1], "invalid-length"),
        "long-161": (zero_tail + b"\x5a", "invalid-length"),
        "alternate-extension-only": (zero_tail, "ignored-alternate-path"),
    }


def generate(output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    entries = []
    for name, (payload, static_classification) in profiles().items():
        filename = f"{name}.nxs"
        path = output / filename
        path.write_bytes(payload)
        entries.append(
            {
                "id": name,
                "filename": filename,
                "size": len(payload),
                "sha256": sha256(payload),
                "first_32_sha256": sha256(payload[:32]),
                "static_classification": static_classification,
                "guest_target": (
                    "djprofile.bin"
                    if name == "alternate-extension-only"
                    else "djprofile.nxs"
                ),
            }
        )

    manifest = {
        "format": 1,
        "scope": "self-authored deterministic Rekordbox user-info/DJ-ID profiles",
        "checksum": {
            "offset_0": {"byte_order": "little", "value": "0x01020304"},
            "offset_4": {"byte_order": "big", "value": "0x11121314"},
            "offset_8": {"byte_order": "big", "value": "0x21222324"},
            "offset_12": {"byte_order": "big", "value": "0x31323334"},
            "offset_28": {"byte_order": "big", "value": "0x64686c70"},
        },
        "profiles": entries,
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    generate(args.output)


if __name__ == "__main__":
    main()
