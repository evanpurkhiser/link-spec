#!/usr/bin/env python3
"""Pin numeric field extraction for the Link Export render request."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

import lief
from capstone import CS_ARCH_X86, CS_MODE_64, Cs


EXPECTED_SHA256 = "07dcecbaf304f777e435539c83c7dcc02e41de1eaf2e0a75e8a9852e4411a244"
RENDER = "__ZN9PSvDBMain18GetListBufContentsEP16_struct_dbsm_msg"
FIRST_ROW = "__ZN9PSvDBMain16GetListBuf1stRowEPvPjjt"
CATEGORY = "__Z20DBCommon_GetCateKindt"
CATEGORY_TABLE = 0x103BCB854
EXPECTED_CATEGORY_MAP = {
    **{value: value for value in range(1, 25)},
    **{value: 0 for value in range(25, 30)},
    **{value: value for value in range(30, 33)},
    **{value: 0 for value in range(33, 40)},
    40: 40,
    **{value: 0 for value in range(41, 50)},
    50: 50,
    51: 51,
}
EXPECTED = {
    RENDER: {
        0x100FA112B: ("mov", "r15, qword ptr [r14 + 0x18]"),
        0x100FA112F: ("mov", "r12, qword ptr [r14 + 0x20]"),
        0x100FA1133: ("mov", "eax, dword ptr [r14 + 0x28]"),
        0x100FA1140: ("movzx", "eax, word ptr [r14 + 0x30]"),
        0x100FA115A: ("movzx", "edi, word ptr [r14 + 0x40]"),
        0x100FA115F: ("call", "0x101d627c0"),
        0x100FA116D: ("cmp", "dword ptr [r14 + 0x48], 0"),
        0x100FA1175: ("mov", "ecx, dword ptr [r14 + 0x50]"),
        0x100FA1268: ("movzx", "r8d, word ptr [rbp - 0x50]"),
        0x100FA1283: ("call", "0x100f9fa90"),
    },
    FIRST_ROW: {
        0x100F9FAA1: ("mov", "qword ptr [rbp - 0x68], r8"),
        0x100F9FB58: ("inc", "eax"),
        0x100F9FB5A: ("cmp", "ax, 2"),
        0x100F9FC5D: ("mov", "eax, ebx"),
        0x100F9FC5F: ("and", "eax, 1"),
        0x100F9FC67: ("movzx", "eax, word ptr [rbx]"),
        0x100F9FC6C: ("add", "ecx, -0x61"),
        0x100F9FC7D: ("lea", "esi, [rax - 0x20]"),
        0x100F9FC9F: ("cmp", "si, dx"),
        0x100F9FCA4: ("cmp", "dx, 0x55"),
        0x100F9FD65: ("lea", "ecx, [rax + 0xdf]"),
        0x100F9FD71: ("lea", "esi, [rax + 0x120]"),
        0x100F9FDCB: ("mov", "rdi, r14"),
        0x100F9FDD1: ("call", "0x1000d2e50"),
    },
    CATEGORY: {
        0x101D627C0: ("dec", "edi"),
        0x101D627C2: ("xor", "eax, eax"),
        0x101D627C4: ("cmp", "di, 0x32"),
        0x101D627C8: ("ja", "0x101d627dd"),
        0x101D627D2: ("lea", "rcx, [rip + 0x1e6907b]"),
        0x101D627D9: ("mov", "eax, dword ptr [rcx + rax*4]"),
    },
}


def instructions(
    binary: lief.MachO.Binary, start: int, size: int
) -> dict[int, tuple[str, str]]:
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    content = bytes(binary.get_content_from_virtual_address(start, size))
    return {
        instruction.address: (instruction.mnemonic, instruction.op_str)
        for instruction in decoder.disasm(content, start)
    }


def file_bytes(binary: lief.MachO.Binary, path: Path, address: int, size: int) -> bytes:
    segment = next(
        segment
        for segment in binary.segments
        if segment.virtual_address <= address < segment.virtual_address + segment.virtual_size
    )
    offset = (
        binary.fat_offset
        + segment.file_offset
        + address
        - segment.virtual_address
    )
    with path.open("rb") as source:
        source.seek(offset)
        value = source.read(size)
    if len(value) != size:
        raise SystemExit(f"short read at virtual address {address:#x}")
    return value


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("binary", type=Path)
    parser.add_argument("--json", type=Path, required=True)
    parser.add_argument("--markdown", type=Path, required=True)
    args = parser.parse_args()

    digest = hashlib.sha256(args.binary.read_bytes()).hexdigest()
    if digest != EXPECTED_SHA256:
        raise SystemExit(f"unexpected executable SHA-256: {digest}")

    fat = lief.MachO.parse(str(args.binary))
    binary = next(
        item
        for item in fat
        if item.header.cpu_type == lief.MachO.Header.CPU_TYPE.X86_64
    )
    symbols = {symbol.name: symbol.value for symbol in binary.symbols if symbol.value}

    validated = []
    decoded_functions = {}
    for name, expected in EXPECTED.items():
        start = symbols.get(name)
        if start is None:
            raise SystemExit(f"missing symbol: {name}")
        decoded = instructions(binary, start, 0x1000)
        decoded_functions[name] = decoded
        for address, wanted in expected.items():
            actual = decoded.get(address)
            if actual != wanted:
                raise SystemExit(
                    f"{name} {address:#x}: expected {wanted!r}, found {actual!r}"
                )
            validated.append(
                {
                    "symbol": name,
                    "address": f"{address:#x}",
                    "mnemonic": actual[0],
                    "operands": actual[1],
                }
            )

    render_operands = [operands for _, operands in decoded_functions[RENDER].values()]
    if any("[r14 + 0x38]" in operands for operands in render_operands):
        raise SystemExit("render function unexpectedly reads argument-5 slot 0x38")

    table = struct.unpack(
        "<51I", file_bytes(binary, args.binary, CATEGORY_TABLE, 51 * 4)
    )
    category_map = {index: value for index, value in enumerate(table, start=1)}
    if category_map != EXPECTED_CATEGORY_MAP:
        raise SystemExit("DBCommon_GetCateKind table changed")

    report = {
        "format": 1,
        "executable_sha256": digest,
        "architecture": "x86_64",
        "functions": {
            "get_list_buffer_contents": {
                "symbol": RENDER,
                "address": f"{symbols[RENDER]:#x}",
            },
            "get_list_buffer_first_row": {
                "symbol": FIRST_ROW,
                "address": f"{symbols[FIRST_ROW]:#x}",
            },
            "get_category_kind": {
                "symbol": CATEGORY,
                "address": f"{symbols[CATEGORY]:#x}",
            },
        },
        "validated_instruction_count": len(validated),
        "validated_instructions": validated,
        "render_argument_fields": {
            "1": {"slot": "0x18", "read_width_bits": 64, "role": "context"},
            "2": {"slot": "0x20", "read_width_bits": 64, "role": "offset"},
            "3": {"slot": "0x28", "read_width_bits": 32, "role": "count"},
            "4": {
                "slot": "0x30",
                "read_width_bits": 16,
                "role": "first-row character seek key",
            },
            "5": {
                "slot": "0x38",
                "read_width_bits": 0,
                "role": "client-reported total; unread by renderer",
            },
            "6": {
                "slot": "0x40",
                "read_width_bits": 16,
                "role": "category ID mapped through DBCommon_GetCateKind",
            },
            "7": {
                "slot": "0x48",
                "read_width_bits": 32,
                "role": "override gate",
            },
            "8": {
                "slot": "0x50",
                "read_width_bits": 32,
                "role": "secondary selector override",
            },
        },
        "category_kind_table_address": f"{CATEGORY_TABLE:#x}",
        "category_kind_map": {str(key): value for key, value in category_map.items()},
        "findings": {
            "argument_4_zero_uses_normal_offset_path": True,
            "argument_4_ffff_wraps_increment_to_zero": True,
            "argument_4_nonzero_uses_normalized_first_character_search": True,
            "argument_4_ascii_lowercase_is_normalized_to_uppercase": True,
            "argument_4_unknown_has_special_handling": True,
            "argument_5_has_no_read_in_get_list_buffer_contents": True,
            "argument_6_out_of_range_maps_to_zero": True,
            "argument_4_and_6_ignore_high_16_bits": True,
        },
        "authority_boundary": (
            "Static decoding proves field reads, widths, and control flow. Real "
            "Rekordbox record/repeat determines returned rows and transport behavior."
        ),
    }
    args.json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    ranges = (
        "1-24 map identically; 25-29 map to zero; 30-32 map identically; "
        "33-39 map to zero; 40 maps identically; 41-49 map to zero; and "
        "50-51 map identically. Values outside 1-51 map to zero."
    )
    markdown = f"""# Track render numeric-field decoder audit

This generated audit is pinned to Rekordbox 7.2.19 x86-64 executable SHA-256
`{digest}` and validates {len(validated)} exact instructions plus the complete
51-entry `DBCommon_GetCateKind` table.

The normal eight render positions are consumed as follows:

| Position | Width read | Role |
| ---: | ---: | --- |
| 1 | 64 | packed list-buffer context |
| 2 | 64 | requested offset, narrowed downstream |
| 3 | 32 | requested count |
| 4 | 16 | first-row character seek key |
| 5 | 0 | client-reported total; unread by `GetListBufContents` |
| 6 | 16 | category ID passed through `DBCommon_GetCateKind` |
| 7 | 32 | nonzero secondary-override gate |
| 8 | 32 | secondary selector override |

Argument 4 is therefore not reserved. Zero follows ordinary offset pagination.
A nonzero low word enters `GetListBuf1stRow`'s normalized first-character scan;
ASCII lowercase is promoted to uppercase and `U`/`Unknown` has a dedicated
path. Low word `0xffff` wraps the internal increment and rejoins the ordinary
path. High 16 bits are never read.

Argument 5 is sent by clients as the menu total but has no read in the complete
renderer body. Argument 6 is also truncated to its low word. Its exact category
map is: {ranges}

The checked-in live matrix tests representative character classes, wrap and
high-word aliases, client-total boundaries, and every category-map range. The
static findings constrain interpretation but do not predict returned rows;
the queued real-Rekordbox record/repeat remains authoritative.
"""
    args.markdown.write_text(markdown)


if __name__ == "__main__":
    main()
