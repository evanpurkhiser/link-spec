#!/usr/bin/env python3
"""Generate health-aware seek-descriptor probes for extended setter 0x2401."""

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
    value: int | str
    record: bytes


def truncated_variant(length: int) -> Variant:
    record = bytearray(build_record())
    struct.pack_into("<I", record, 0x00, length)
    struct.pack_into("<I", record, 0x34, max(0, length - 56))
    return Variant(f"actual-length-{length:08x}", "actual-length", length, bytes(record[:length]))


def descriptor_length_variant(length: int) -> Variant:
    record = bytearray(build_record())
    struct.pack_into("<I", record, 0x4A, length)
    return Variant(f"descriptor-length-{length:08x}", "descriptor-length", length, bytes(record))


def seek_values_variant(name: str, inbound_validity: int, outbound_validity: int) -> Variant:
    record = bytearray(build_record())
    struct.pack_into(
        ">QQQQII",
        record,
        0x52,
        1,
        2,
        3,
        4,
        inbound_validity,
        outbound_validity,
    )
    return Variant(name, "seek-values", name, bytes(record))


def variants() -> tuple[Variant, ...]:
    actual_lengths = (74, 81, 82, 121, 122, 123, 124)
    descriptor_lengths = (0, 1, 43, 44, 45, 0xFFFFFFFF)
    return tuple(
        [truncated_variant(value) for value in actual_lengths]
        + [descriptor_length_variant(value) for value in descriptor_lengths]
        + [
            seek_values_variant("inbound-validity-00000000", 0, 0),
            seek_values_variant("inbound-validity-00000001", 1, 0),
            seek_values_variant("inbound-validity-ffffffff", 0xFFFFFFFF, 0),
            seek_values_variant("outbound-only-valid", 0, 1),
        ]
    )


def suite(variant: Variant) -> dict[str, object]:
    name = f"hot-cue-setter-seek-{variant.id}"
    return {
        "name": name,
        "fixture_profile": "hot-cue-bank-mutation",
        "fixture_version": 1,
        "repeat_strategy": "two-cold-process-health-captures",
        "seek_descriptor_probe": {
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
                "description": f"Extended setter seek descriptor {variant.id}",
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
            }
        ],
    }


def main() -> None:
    output_dir = ROOT / "suites/generated/hot-cue-setter-seek"
    output_dir.mkdir(parents=True, exist_ok=True)
    entries = []
    for variant in variants():
        document = suite(variant)
        relative = f"suites/generated/hot-cue-setter-seek/{document['name']}.json"
        (ROOT / relative).write_text(json.dumps(document, indent=2) + "\n")
        entries.append({
            "id": variant.id,
            "axis": variant.axis,
            "value": variant.value,
            "record_length": len(variant.record),
            "suite": relative,
        })

    (ROOT / "data/hot-cue-setter-seek-matrix.json").write_text(
        json.dumps({"format": 1, "variants": entries}, indent=2) + "\n"
    )


if __name__ == "__main__":
    main()
