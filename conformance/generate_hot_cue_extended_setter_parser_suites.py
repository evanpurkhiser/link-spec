#!/usr/bin/env python3
"""Generate fixture-isolated structural probes for extended setter 0x2401."""

from __future__ import annotations

import json
import struct
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "tools"))

from build_hot_cue_mutation_record import build_record


@dataclass(frozen=True)
class Variant:
    id: str
    axis: str
    value: int


def variants() -> tuple[Variant, ...]:
    axes = {
        "record-count": (0, 1, 2, 0xFFFFFFFF),
        "actual-length": (0, 1, 55, 56, 123, 124, 125),
        "declared-length": (0, 55, 56, 123, 124, 125, 0xFFFFFFFF),
        "record-size": (0, 55, 56, 123, 124, 125, 0xFFFFFFFF),
        "slot": (0, 1, 8, 9, 0xFFFF),
        "cue-type": (0, 1, 2, 3, 0xFF),
        "time-unit": (0, 74, 75, 76, 149, 150, 151, 999, 1000, 1001, 0xFFFF),
        "option-length": (0, 1, 65, 66, 67, 0xFFFFFFFF),
        "returned-slots": (0, 1, 2, 8, 0xFFFFFFFF),
    }
    return tuple(
        Variant(f"{axis}-{value:08x}", axis, value)
        for axis, values in axes.items()
        for value in values
    )


def record_for(variant: Variant) -> bytes:
    record = bytearray(build_record())
    if variant.axis == "actual-length":
        length = variant.value
        if length <= len(record):
            return bytes(record[:length])
        return bytes(record) + bytes(length - len(record))
    if variant.axis == "record-size":
        struct.pack_into("<I", record, 0x00, variant.value)
    elif variant.axis == "slot":
        struct.pack_into("<H", record, 0x04, variant.value)
    elif variant.axis == "cue-type":
        record[0x06] = variant.value
    elif variant.axis == "time-unit":
        struct.pack_into("<H", record, 0x0A, variant.value)
    elif variant.axis == "option-length":
        struct.pack_into("<I", record, 0x34, variant.value)
    return bytes(record)


def setter_case(variant: Variant, record: bytes) -> dict[str, object]:
    declared_length = (
        variant.value if variant.axis == "declared-length" else len(record)
    )
    record_count = variant.value if variant.axis == "record-count" else 1
    returned_slots = variant.value if variant.axis == "returned-slots" else 1
    return {
        "id": "setter",
        "description": (
            f"Extended Hot Cue setter parser axis {variant.axis} value "
            f"0x{variant.value:08x}"
        ),
        "request_kind": "0x2401",
        "arguments": [
            {"number": "0x0b010301"},
            {"number": "$fixture.hotcue.bank.mutation"},
            {"number": record_count},
            {"number": declared_length},
            {"blob_hex": record.hex()},
            {"number": returned_slots},
        ],
        "direct_response": True,
        "render": False,
        "fresh_connection": True,
        "expect": {"outcome": "any"},
    }


def getter_case() -> dict[str, object]:
    return {
        "id": "database-read-after-setter",
        "description": "Canonical type-1 getter after the isolated setter probe",
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
    }


def suite(variant: Variant) -> dict[str, object]:
    name = f"hot-cue-setter-parser-{variant.id}"
    record = record_for(variant)
    return {
        "name": name,
        "fixture_profile": "hot-cue-bank-mutation",
        "fixture_version": 1,
        "repeat_strategy": "fixture-reset-and-restart",
        "parser_probe": {
            "axis": variant.axis,
            "value": variant.value,
            "actual_blob_length": len(record),
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
        "cases": [setter_case(variant, record), getter_case()],
    }


def matrix_entry(variant: Variant) -> dict[str, object]:
    entry: dict[str, object] = {
        "id": variant.id,
        "axis": variant.axis,
        "value": variant.value,
        "suite": (
            "suites/generated/hot-cue-setter-parser/"
            f"hot-cue-setter-parser-{variant.id}.json"
        ),
    }
    if variant.id == "declared-length-ffffffff":
        return {
            **entry,
            "record_mode": "lifecycle",
            "evidence": (
                "data/experiments/hot-cue-bank/extended-setter-parser/"
                "declared-length-ffffffff-lifecycle/summary.json"
            ),
        }
    if variant.id == "slot-00000008":
        return {
            **entry,
            "record_mode": "lifecycle",
            "evidence": (
                "data/experiments/hot-cue-bank/extended-setter-parser/"
                "slot-00000008-lifecycle/summary.json"
            ),
        }
    if variant.id == "returned-slots-ffffffff":
        return {
            **entry,
            "record_mode": "lifecycle",
            "evidence": (
                "data/experiments/hot-cue-bank/extended-setter-parser/"
                "returned-slots-ffffffff-lifecycle/summary.json"
            ),
        }

    return {
        **entry,
        "record_mode": "golden",
        "golden": (
            "goldens/rekordbox-7.2.19/xdj-rx3-status/"
            f"hot-cue-setter-parser-{variant.id}.json"
        ),
    }


def matrix() -> dict[str, object]:
    return {
        "format": 2,
        "variants": [matrix_entry(variant) for variant in variants()],
    }


def main() -> None:
    output_dir = ROOT / "suites/generated/hot-cue-setter-parser"
    output_dir.mkdir(parents=True, exist_ok=True)
    for variant in variants():
        document = suite(variant)
        output = output_dir / f"{document['name']}.json"
        output.write_text(json.dumps(document, indent=2) + "\n")
    (ROOT / "data/hot-cue-setter-parser-matrix.json").write_text(
        json.dumps(matrix(), indent=2) + "\n"
    )


if __name__ == "__main__":
    main()
