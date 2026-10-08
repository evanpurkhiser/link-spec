#!/usr/bin/env python3
"""Resolve the AppSync extended-setter reply target from the pinned binary."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

import lief


ROOT = Path(__file__).resolve().parent.parent
DISASSEMBLY = ROOT / "data/static-analysis/hot-cue-bank-mutations.disasm.txt"
EXPECTED_BINARY_SHA256 = (
    "07dcecbaf304f777e435539c83c7dcc02e41de1eaf2e0a75e8a9852e4411a244"
)
VTABLE_SYMBOL = "__ZTV14PSvAppSyncDBIF"
TARGET_SYMBOL = "__ZN14PSvAppSyncDBIF19getHCBnkCuePointExtEP16_struct_dbsm_msgjj"
OBJECT_VPTR_OFFSET = 0x10
METHOD_OFFSET = 0x288


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(binary_path: Path) -> dict[str, object]:
    binary_path = binary_path.resolve()
    binary_sha256 = sha256(binary_path)
    if binary_sha256 != EXPECTED_BINARY_SHA256:
        raise SystemExit(f"unexpected binary SHA-256: {binary_sha256}")

    fat = lief.MachO.parse(str(binary_path))
    binary = next(
        item
        for item in fat
        if item.header.cpu_type == lief.MachO.Header.CPU_TYPE.X86_64
    )
    symbols: dict[str, int] = {}
    for symbol in binary.symbols:
        if symbol.name and symbol.value:
            symbols.setdefault(symbol.name, symbol.value)
    vtable_address = symbols[VTABLE_SYMBOL]
    entry_address = vtable_address + OBJECT_VPTR_OFFSET + METHOD_OFFSET
    raw_entry = bytes(binary.get_content_from_virtual_address(entry_address, 8))
    target_address = struct.unpack("<Q", raw_entry)[0]
    if symbols[TARGET_SYMBOL] != target_address:
        raise AssertionError(
            f"vtable target {target_address:#x} does not match {TARGET_SYMBOL}"
        )

    disassembly = DISASSEMBLY.read_text()
    required_lines = {
        "rejection_count_load": "0x01016d4068  mov       ecx, dword ptr [rbx + 0x28]",
        "rejection_call": "0x01016d4074  call      qword ptr [rax + 0x288]",
        "success_update": "0x01016d4c18  call      0x100b09f50",
        "success_bank_load": "0x01016d4c76  mov       edx, dword ptr [rbx + 8]",
        "success_count_load": "0x01016d4c79  mov       ecx, dword ptr [rbx + 0x28]",
        "success_call": "0x01016d4c85  call      qword ptr [rax + 0x288]",
    }
    for label, line in required_lines.items():
        if line not in disassembly:
            raise AssertionError(f"missing {label}: {line}")

    return {
        "format": "rekordbox-hot-cue-setter-reply-target-v1",
        "binary": {
            "path": str(binary_path),
            "sha256": binary_sha256,
            "architecture": "x86_64",
        },
        "appsync_vtable": {
            "symbol": VTABLE_SYMBOL,
            "address": f"{vtable_address:#x}",
            "object_vptr_offset": f"{OBJECT_VPTR_OFFSET:#x}",
            "method_offset": f"{METHOD_OFFSET:#x}",
            "entry_address": f"{entry_address:#x}",
            "entry_bytes_little_endian": raw_entry.hex(),
            "target_address": f"{target_address:#x}",
            "target_symbol": TARGET_SYMBOL,
        },
        "setter_calls": {
            "rejection_path": {
                "count_load": "0x1016d4068",
                "call": "0x1016d4074",
            },
            "successful_mutation_path": {
                "last_database_update_call": "0x1016d4c18",
                "bank_id_load": "0x1016d4c76",
                "returned_slot_count_load": "0x1016d4c79",
                "getter_call": "0x1016d4c85",
            },
        },
        "conclusion": (
            "The successful extended setter updates the database before invoking "
            "getHCBnkCuePointExt with the request bank ID and returned-slot count "
            "to construct its reply."
        ),
        "limits": [
            "Pinned Rekordbox 7.2.19 x86-64 binary only",
            "The static target does not by itself characterize extreme-count runtime behavior",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("binary", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    document = json.dumps(audit(args.binary), indent=2) + "\n"
    if args.output is None:
        print(document, end="")
        return
    args.output.write_text(document)


if __name__ == "__main__":
    main()
