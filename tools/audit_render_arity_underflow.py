#!/usr/bin/env python3
"""Pin the decoder/storage behavior for 0-2 argument track renders."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import lief
from capstone import CS_ARCH_X86, CS_MODE_64, Cs


EXPECTED_SHA256 = "07dcecbaf304f777e435539c83c7dcc02e41de1eaf2e0a75e8a9852e4411a244"
RECEIVE = "__ZN15PSvDBConnection14ReceiveCommandEPP19_struct_db_comm_cmdb"
RENDER = "__ZN9PSvDBMain18GetListBufContentsEP16_struct_dbsm_msg"

EXPECTED = {
    RECEIVE: {
        0x10143B44B: ("mov", "edi, 0x98"),
        0x10143B450: ("call", "0x1038c3cd4"),
        0x10143B458: ("vxorps", "xmm0, xmm0, xmm0"),
        0x10143B45C: ("vmovups", "ymmword ptr [rax], ymm0"),
        0x10143B460: ("vmovups", "ymmword ptr [rax + 0x20], ymm0"),
        0x10143B465: ("vmovups", "ymmword ptr [rax + 0x40], ymm0"),
        0x10143B46A: ("vmovups", "ymmword ptr [rax + 0x60], ymm0"),
        0x10143B46F: ("vmovups", "ymmword ptr [rax + 0x78], ymm0"),
        0x10143B7BB: ("cmp", "byte ptr [r12 + 7], 0"),
        0x10143B7C1: ("je", "0x10143bb2c"),
        0x10143B7C7: ("mov", "ebx, 0x18"),
        0x10143B7CC: ("xor", "r13d, r13d"),
        0x10143B7D5: ("movzx", "eax, byte ptr [r12 + r13 + 8]"),
        0x10143BA7F: ("inc", "r13"),
        0x10143BA82: ("add", "rbx, 8"),
        0x10143BA8A: ("movzx", "eax, byte ptr [rax]"),
        0x10143BA8D: ("cmp", "r13, rax"),
    },
    RENDER: {
        0x100FA1127: ("mov", "r14, qword ptr [rsi + 0x20]"),
        0x100FA112B: ("mov", "r15, qword ptr [r14 + 0x18]"),
        0x100FA112F: ("mov", "r12, qword ptr [r14 + 0x20]"),
        0x100FA1133: ("mov", "eax, dword ptr [r14 + 0x28]"),
        0x100FA113B: ("cmp", "byte ptr [r14 + 7], 6"),
    },
}


def instructions(binary: lief.MachO.Binary, start: int, size: int) -> dict[int, tuple[str, str]]:
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
        "findings": {
            "command_allocation_bytes": 0x98,
            "command_allocation_is_zero_initialized": True,
            "argument_count_offset": "0x07",
            "argument_tag_list_offset": "0x08",
            "argument_value_slot_offset": "0x18",
            "argument_value_slot_stride": 8,
            "zero_argument_count_skips_field_loop": True,
            "render_mandatory_slot_reads_precede_first_count_guard": True,
            "first_render_count_guard": 6,
            "missing_slot_value": 0,
            "underflow_projection": {
                "0": [0, 0, 0],
                "1": ["argument_1", 0, 0],
                "2": ["argument_1", "argument_2", 0],
            },
        },
        "authority_boundary": (
            "Static storage and control-flow prediction only; real Rekordbox "
            "record/repeat determines response and transport behavior."
        ),
    }
    args.json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    markdown = f"""# Track render arity-underflow decoder audit

This generated audit is pinned to Rekordbox 7.2.19 x86-64 executable SHA-256
`{digest}` and validates {len(validated)} exact instructions.

`PSvDBConnection::ReceiveCommand` allocates a `0x98`-byte command object and
zeroes the complete allocation before decoding the argument count, tag list,
or values. The zero-count branch skips the field loop. Each decoded value slot
starts at offset `0x18` and advances by eight bytes.

`PSvDBMain::GetListBufContents` reads offsets `0x18`, `0x20`, and `0x28`
before its first count comparison, which tests for six arguments. Missing
mandatory slots therefore contain zero rather than prior-message state.

The source-derived projection is:

| Total arguments | Context slot | Offset slot | Count slot |
| ---: | --- | --- | --- |
| 0 | `0` | `0` | `0` |
| 1 | supplied argument 1 | `0` | `0` |
| 2 | supplied argument 1 | supplied argument 2 | `0` |

This proves storage initialization and field projection, not the response
class or connection lifecycle. The queued real-Rekordbox oracle remains the
behavioral authority.
"""
    args.markdown.write_text(markdown)


if __name__ == "__main__":
    main()
