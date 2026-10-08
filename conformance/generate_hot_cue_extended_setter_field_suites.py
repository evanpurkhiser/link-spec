#!/usr/bin/env python3
"""Generate isolated mutable-field probes for extended Hot Cue setter 0x2401."""

from __future__ import annotations

import json
import struct
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "tools"))

from build_hot_cue_mutation_record import build_record


SIGNED_VALUES = (0, 1, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF)
BYTE_VALUES = (0, 1, 0x7F, 0x80, 0xFF)


@dataclass(frozen=True)
class Variant:
    id: str
    axis: str
    value: int | str
    record: bytes


def numeric_variant(axis: str, offset: int, value: int, encoding: str = "<I") -> Variant:
    record = bytearray(build_record())
    struct.pack_into(encoding, record, offset, value)
    return Variant(f"{axis}-{value:08x}", axis, value, bytes(record))


def beat_loop_variant(value: int) -> Variant:
    record = bytearray(build_record())
    struct.pack_into("<HH", record, 0x42, value >> 16, value & 0xFFFF)
    return Variant(f"beat-loop-size-{value:08x}", "beat-loop-size", value, bytes(record))


def comment_record(comment: bytes) -> bytes:
    if len(comment) > 0xFFFF:
        raise ValueError("comment byte length exceeds the uint16 wire field")

    baseline = build_record()
    record = bytearray(baseline[:0x4A] + comment + baseline[0x4A:])
    struct.pack_into("<I", record, 0x00, len(record))
    struct.pack_into("<I", record, 0x34, 66 + len(comment))
    struct.pack_into("<H", record, 0x48, len(comment))
    return bytes(record)


def variants() -> tuple[Variant, ...]:
    fixed_axes = {
        "in-msec": 0x0C,
        "out-msec": 0x10,
        "in-mpeg-frame": 0x24,
        "out-mpeg-frame": 0x28,
        "in-mpeg-absolute": 0x2C,
        "out-mpeg-absolute": 0x30,
    }
    fixed = [
        numeric_variant(axis, offset, value)
        for axis, offset in fixed_axes.items()
        for value in SIGNED_VALUES
    ]
    color = [
        numeric_variant("color-wire", 0x3A, value, "<B")
        for value in (0, 1, 8, 9, 0xFF)
    ]
    color_table = [
        numeric_variant("color-table-index", 0x3B, value, "<B")
        for value in BYTE_VALUES
    ]
    microseconds = [
        numeric_variant("cue-microseconds", 0x3C, value)
        for value in SIGNED_VALUES
    ]
    beat_loop = [beat_loop_variant(value) for value in SIGNED_VALUES]
    comments = {
        "empty": b"",
        "ascii": "A\0".encode("utf-16le"),
        "unicode": "\u00e9\U0001f642\0".encode("utf-16le"),
        "embedded-nul": "A\0B\0".encode("utf-16le"),
        "lone-high-surrogate": b"\x00\xd8\x00\x00",
        "maximum-even-length": b"A\x00" * 32766 + b"\x00\x00",
    }
    comment_variants = [
        Variant(f"comment-{name}", "comment", name, comment_record(value))
        for name, value in comments.items()
    ]
    return tuple(fixed + color + color_table + microseconds + beat_loop + comment_variants)


def suite(variant: Variant) -> dict[str, object]:
    name = f"hot-cue-setter-field-{variant.id}"
    return {
        "name": name,
        "fixture_profile": "hot-cue-bank-mutation",
        "fixture_version": 1,
        "repeat_strategy": "fixture-reset-and-restart",
        "mutable_field_probe": {
            "axis": variant.axis,
            "value": variant.value,
            "record_length": len(variant.record),
            "fixture_variant": "duplicate-slot",
        },
        "defaults": {
            "device": 11,
            "context": "0x0b010301",
            "sort": 0,
            "root_capabilities": "0x05cfffff",
            "setup": "extended",
            "page_size": 32,
            "read_timeout_ms": 5000,
            "render_arguments": [0, "$total", 12, 1, 0],
        },
        "cases": [
            {
                "id": "setter",
                "description": f"Extended setter mutable field {variant.id}",
                "request_kind": "0x2401",
                "arguments": [
                    {"number": "0x0b010301"},
                    {"number": "$fixture.hotcue.bank.mutation"},
                    {"number": 1},
                    {"number": len(variant.record)},
                    {"blob_hex": variant.record.hex()},
                    {"number": 1},
                ],
                "direct_response": True,
                "render": False,
                "fresh_connection": True,
                "expect": {"outcome": "any"},
            },
            {
                "id": "database-read-after-setter",
                "description": "Database-backed getter after isolated setter probe",
                "request_kind": "0x2301",
                "arguments": [
                    {"number": "0x0b010301"},
                    {"number": "$fixture.hotcue.bank.mutation"},
                    {"number": 1},
                ],
                "direct_response": True,
                "render": False,
                "fresh_connection": True,
                "expect": {"outcome": "raw_reply"},
            },
        ],
    }


def main() -> None:
    output_dir = ROOT / "suites/generated/hot-cue-setter-fields"
    output_dir.mkdir(parents=True, exist_ok=True)
    entries = []
    for variant in variants():
        document = suite(variant)
        relative_suite = f"suites/generated/hot-cue-setter-fields/{document['name']}.json"
        (ROOT / relative_suite).write_text(json.dumps(document, indent=2) + "\n")
        entries.append({
            "id": variant.id,
            "axis": variant.axis,
            "value": variant.value,
            "record_length": len(variant.record),
            "suite": relative_suite,
            "golden": (
                "goldens/rekordbox-7.2.19/xdj-rx3-status/"
                f"{document['name']}.json"
            ),
        })

    (ROOT / "data/hot-cue-setter-field-matrix.json").write_text(
        json.dumps({"format": 1, "variants": entries}, indent=2) + "\n"
    )


if __name__ == "__main__":
    main()
