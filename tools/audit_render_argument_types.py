#!/usr/bin/env python3
"""Pin variable-width argument decoding before track-render dispatch."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

import lief
from capstone import CS_ARCH_X86, CS_MODE_64, Cs


EXPECTED_SHA256 = "07dcecbaf304f777e435539c83c7dcc02e41de1eaf2e0a75e8a9852e4411a244"
RECEIVE = "__ZN15PSvDBConnection14ReceiveCommandEPP19_struct_db_comm_cmdb"
RENDER = "__ZN9PSvDBMain18GetListBufContentsEP16_struct_dbsm_msg"
JUMP_TABLE = 0x10143BB40
EXPECTED_JUMP_TARGETS = {
    1: 0x10143B826,
    2: 0x10143B86D,
    3: 0x10143B8A8,
    4: 0x10143B7FA,
    5: 0x10143B7FA,
    6: 0x10143B7FA,
}
EXPECTED = {
    RECEIVE: {
        0x10143B7D5: ("movzx", "eax, byte ptr [r12 + r13 + 8]"),
        0x10143B7DE: ("cmp", "cl, 5"),
        0x10143B7FA: ("lea", "rdx, [r12 + rbx]"),
        0x10143B80B: ("call", "0x10143c3d0"),
        0x10143B86D: ("test", "r13, r13"),
        0x10143B872: ("mov", "rax, qword ptr [r12 + r13*8 + 0x10]"),
        0x10143B877: ("cmp", "rax, 0x201"),
        0x10143B899: ("mov", "rax, qword ptr [r12 + r13*8 + 0x10]"),
        0x10143B942: ("mov", "ecx, 4"),
        0x10143B961: ("mov", "qword ptr [r12 + r13*8 + 0x18], rax"),
        0x10143B966: ("mov", "rax, qword ptr [r12 + rbx*8 + 0x18]"),
        0x10143B96B: ("shr", "rax, 1"),
        0x10143B99C: ("mov", "rcx, qword ptr [r15 + 8]"),
        0x10143B9A0: ("mov", "edi, 0x26"),
        0x10143B9AD: ("call", "0x10328c640"),
        0x10143B8A8: ("test", "r13, r13"),
        0x10143B8AD: ("mov", "rax, qword ptr [r12 + r13*8 + 0x10]"),
        0x10143B8B2: ("cmp", "rax, 0x500000"),
        0x10143B9B6: ("test", "rax, rax"),
        0x10143B9CF: ("mov", "qword ptr [r12 + r13*8 + 0x18], rax"),
        0x10143B9D4: ("mov", "rax, qword ptr [rbp - 0x38]"),
        0x10143B921: ("mov", "rdx, qword ptr [r15 + 8]"),
        0x10143B92D: ("call", "0x10328e020"),
    },
    RENDER: {
        0x100FA112B: ("mov", "r15, qword ptr [r14 + 0x18]"),
        0x100FA112F: ("mov", "r12, qword ptr [r14 + 0x20]"),
        0x100FA1133: ("mov", "eax, dword ptr [r14 + 0x28]"),
        0x100FA113B: ("cmp", "byte ptr [r14 + 7], 6"),
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
    for name, expected in EXPECTED.items():
        start = symbols.get(name)
        if start is None:
            raise SystemExit(f"missing symbol: {name}")
        decoded = instructions(binary, start, 0x1000)
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

    table = bytes(binary.get_content_from_virtual_address(JUMP_TABLE, 24))
    offsets = struct.unpack("<6i", table)
    targets = {
        tag: JUMP_TABLE + offset for tag, offset in enumerate(offsets, start=1)
    }
    if targets != EXPECTED_JUMP_TARGETS:
        raise SystemExit(f"unexpected ReceiveCommand tag dispatch: {targets!r}")

    report = {
        "format": 1,
        "executable_sha256": digest,
        "architecture": "x86_64",
        "functions": {
            "receive_command": {
                "symbol": RECEIVE,
                "address": f"{symbols[RECEIVE]:#x}",
            },
            "get_list_buffer_contents": {
                "symbol": RENDER,
                "address": f"{symbols[RENDER]:#x}",
            },
        },
        "validated_instruction_count": len(validated),
        "validated_instructions": validated,
        "tag_dispatch": {str(tag): f"{target:#x}" for tag, target in targets.items()},
        "findings": {
            "argument_tag_string": 2,
            "argument_tag_blob": 3,
            "argument_tag_number": 6,
            "string_requires_preceding_length_slot": True,
            "string_preceding_length_exclusive_maximum": "0x201",
            "string_allocation_multiplier": 4,
            "string_receive_element_tag": "0x26",
            "blob_requires_preceding_length_slot": True,
            "blob_preceding_length_exclusive_maximum": "0x500000",
            "variable_width_argument_one_is_rejected_before_dispatch": True,
            "decoded_variable_width_slot_contains_allocation_pointer": True,
            "render_reads_value_slots_without_semantic_tag_checks": True,
        },
        "authority_boundary": (
            "Static decoding proves parser storage and dependencies only; real "
            "Rekordbox record/repeat determines each response and process outcome."
        ),
    }
    args.json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    markdown = f"""# Track render argument-type decoder audit

This generated audit is pinned to Rekordbox 7.2.19 x86-64 executable SHA-256
`{digest}` and validates {len(validated)} exact instructions plus the six-entry
`PSvDBConnection::ReceiveCommand` argument-tag jump table.

The command decoder accepts variable-width tag `2` as a UTF-16 array and tag
`3` as a byte blob. Both paths require an earlier argument: its decoded numeric
slot supplies the allocation/read length. A string length must be below
`0x201`; a blob length must be below `0x500000`. Position one therefore cannot
carry either variable-width type through this decoder because it has no
preceding length slot.

Successful string and blob decoding stores the allocation pointer in the same
eight-byte value-slot array used by numeric arguments. `GetListBufContents`
reads those slots directly and does not inspect their tags. A wrong-typed
render may consequently fail in framing/decoding, reach dispatch with a pointer
interpreted numerically, time out, disconnect, or affect process health.

The declared live matrix preserves all normal numeric neighbors and changes
exactly one tag/value. That deliberately measures the combined real parser and
render behavior; it does not rewrite a preceding argument to make the
variable-width value parser-admissible. The live oracle, not this static
projection, determines every response and process outcome.
"""
    args.markdown.write_text(markdown)


if __name__ == "__main__":
    main()
