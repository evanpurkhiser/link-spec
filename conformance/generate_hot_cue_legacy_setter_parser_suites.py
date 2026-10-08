#!/usr/bin/env python3
"""Generate process-isolated structural probes for legacy setter 0x2201."""

from __future__ import annotations

import json
import struct
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "tools"))

from build_hot_cue_legacy_request import build_cue, build_extension


@dataclass(frozen=True)
class Variant:
    id: str
    axis: str
    value: int
    word: int | None = None


def variants() -> tuple[Variant, ...]:
    axes = {
        "actual-cue-length": (0, 1, 3, 4, 7, 8, 35, 36, 37),
        "declared-cue-length": (0, 1, 35, 36, 37, 0xFFFFFFFF),
        "flag": (
            0,
            0x0003FFFF,
            0x00040000,
            0x00040001,
            0x00040100,
            0x0004FFFF,
            0x00050000,
            0x0005FFFF,
            0x00060000,
            0x0006FFFF,
            0x00070000,
            0xFFFFFFFF,
        ),
        "actual-extension-length": (0, 1, 7, 8, 9, 16),
        "declared-extension-length": (0, 1, 7, 8, 9, 0xFFFFFFFF),
        "content-id": (0, 10001, 999999, 0xFFFFFFFF),
    }
    ordinary = tuple(
        Variant(f"{axis}-{value:08x}", axis, value)
        for axis, values in axes.items()
        for value in values
    )
    fixed_words = tuple(
        Variant(f"fixed-word-{word}-{value:08x}", "fixed-word", value, word)
        for word in range(2, 9)
        for value in (0, 0xFFFFFFFF)
    )
    return ordinary + fixed_words


def resize(payload: bytes, length: int) -> bytes:
    if length <= len(payload):
        return payload[:length]
    return payload + bytes(length - len(payload))


def payloads(variant: Variant) -> tuple[bytes, bytes]:
    cue = bytearray(build_cue(10001, 4))
    extension = build_extension()

    if variant.axis == "actual-cue-length":
        cue = bytearray(resize(cue, variant.value))
    elif variant.axis == "flag":
        struct.pack_into("<I", cue, 0, variant.value)
    elif variant.axis == "content-id":
        struct.pack_into("<I", cue, 4, variant.value)
    elif variant.axis == "fixed-word":
        assert variant.word is not None
        struct.pack_into("<I", cue, variant.word * 4, variant.value)
    elif variant.axis == "actual-extension-length":
        extension = resize(extension, variant.value)

    return bytes(cue), extension


def suite(variant: Variant) -> dict[str, object]:
    cue, extension = payloads(variant)
    cue_length = (
        variant.value if variant.axis == "declared-cue-length" else len(cue)
    )
    extension_length = (
        variant.value
        if variant.axis == "declared-extension-length"
        else len(extension)
    )
    name = f"hot-cue-legacy-setter-parser-{variant.id}"
    return {
        "name": name,
        "fixture_profile": "hot-cue-bank-legacy-ordinals",
        "fixture_version": 1,
        "repeat_strategy": "fixture-reset-and-restart",
        "parser_probe": {
            "axis": variant.axis,
            "value": variant.value,
            "word": variant.word,
            "actual_cue_length": len(cue),
            "declared_cue_length": cue_length,
            "actual_extension_length": len(extension),
            "declared_extension_length": extension_length,
            "process_isolation_required": True,
            "post_survival_getter_required": True,
            "live_database_capture_required": True,
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
                "description": (
                    f"Legacy Hot Cue setter parser axis {variant.axis} value "
                    f"0x{variant.value:08x}"
                ),
                "request_kind": "0x2201",
                "arguments": [
                    {"number": "0x0b010301"},
                    {"number": "$fixture.hotcue.bank.mutation"},
                    {"number": cue_length},
                    {"blob_hex": cue.hex()},
                    {"number": extension_length},
                    {"blob_hex": extension.hex()},
                ],
                "direct_response": True,
                "render": False,
                "fresh_connection": True,
                "expect": {"outcome": "any"},
            }
        ],
    }


def getter_suite() -> dict[str, object]:
    return {
        "name": "hot-cue-legacy-setter-parser-read-after",
        "fixture_profile": "hot-cue-bank-legacy-ordinals",
        "fixture_version": 1,
        "repeat_strategy": "fixture-reset-and-restart",
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
                "id": "database-read-after-setter",
                "description": (
                    "Six-slot extended getter after a surviving isolated legacy "
                    "setter probe"
                ),
                "request_kind": "0x2301",
                "arguments": [
                    {"number": "0x0b010301"},
                    {"number": "$fixture.hotcue.bank.mutation"},
                    {"number": 6},
                ],
                "direct_response": True,
                "render": False,
                "fresh_connection": True,
                "expect": {"outcome": "any"},
            }
        ],
    }


def main() -> None:
    output_dir = ROOT / "suites/generated/hot-cue-legacy-setter-parser"
    output_dir.mkdir(parents=True, exist_ok=True)
    matrix = []
    for variant in variants():
        document = suite(variant)
        output = output_dir / f"{document['name']}.json"
        output.write_text(json.dumps(document, indent=2) + "\n")
        matrix.append(
            {
                "id": variant.id,
                "axis": variant.axis,
                "value": variant.value,
                "word": variant.word,
                "suite": str(output.relative_to(ROOT)),
                "experiment": (
                    "../data/experiments/hot-cue-bank/legacy-setter-parser/"
                    f"{variant.id}"
                ),
            }
        )
    (ROOT / "data/hot-cue-legacy-setter-parser-matrix.json").write_text(
        json.dumps({"format": 1, "variants": matrix}, indent=2) + "\n"
    )
    (output_dir / "hot-cue-legacy-setter-parser-read-after.json").write_text(
        json.dumps(getter_suite(), indent=2) + "\n"
    )


if __name__ == "__main__":
    main()
