#!/usr/bin/env python3
"""Pin eight-argument track-render override decoding and dispatch."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import lief
from capstone import CS_ARCH_X86, CS_MODE_64, Cs


EXPECTED_SHA256 = "07dcecbaf304f777e435539c83c7dcc02e41de1eaf2e0a75e8a9852e4411a244"
CONTENTS = "__ZN9PSvDBMain18GetListBufContentsEP16_struct_dbsm_msg"
ROW = "__ZN9PSvDBMain20GetListBufRowContentEhh17ENUM_CATEGORYKINDPvPmbjP18RetListBufParamExt"
SUBCATEGORY = "__Z20Get_SubCategoryValuejN4juce3varERhRjPPt"
EXPECTED = {
    CONTENTS: {
        0x100FA116D: ("cmp", "dword ptr [r14 + 0x48], 0"),
        0x100FA1172: ("setne", "dl"),
        0x100FA1175: ("mov", "ecx, dword ptr [r14 + 0x50]"),
        0x100FA1181: ("mov", "dword ptr [rbp - 0x2c], edx"),
        0x100FA1188: ("mov", "qword ptr [rbp - 0x78], rcx"),
        0x100FA131F: ("movzx", "ecx, byte ptr [rbp - 0x2c]"),
        0x100FA133F: ("push", "qword ptr [rbp - 0x78]"),
        0x100FA1342: ("push", "r12"),
        0x100FA1347: ("call", "0x100f9fe40"),
    },
    ROW: {
        0x100FA093A: ("mov", "r12d, dword ptr [rbp + 0x18]"),
        0x100FA093E: ("mov", "r13b, byte ptr [rbp + 0x10]"),
        0x100FA0945: ("test", "r12d, r12d"),
        0x100FA094A: ("test", "r13b, r13b"),
        0x100FA09C9: ("test", "r13b, r13b"),
        0x100FA09D2: ("test", "r12d, r12d"),
        0x100FA09D5: ("cmovne", "r14d, r12d"),
        0x100FA09D9: ("movsx", "edi, r14b"),
        0x100FA09DD: ("call", "0x1004dbb90"),
        0x100FA09E2: ("test", "r14d, r14d"),
        0x100FA0A85: ("mov", "edi, r14d"),
        0x100FA0A88: ("call", "0x1016b7bc0"),
    },
    SUBCATEGORY: {
        0x1016B7BEC: ("add", "ebx, -2"),
        0x1016B7BEF: ("cmp", "ebx, 0xf"),
        0x1016B7BF2: ("ja", "0x1016b80fc"),
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
    parser.add_argument("--disassembly", type=Path, required=True)
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
    disassembly = []
    for name, expected in EXPECTED.items():
        start = symbols.get(name)
        if start is None:
            raise SystemExit(f"missing symbol: {name}")
        decoded = instructions(binary, start, 0x1400)
        disassembly.extend((name, address, *decoded[address]) for address in expected)
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
        "validated_instruction_count": len(validated),
        "validated_instructions": validated,
        "findings": {
            "argument_7_read_width_bits": 32,
            "argument_7_canonicalized_to_boolean": True,
            "argument_8_read_width_bits": 32,
            "argument_8_zero_uses_persisted_selection": True,
            "argument_8_nonzero_replaces_persisted_selection": True,
            "icon_dispatch_uses_low_8_bits": True,
            "subcategory_dispatch_uses_full_32_bits": True,
            "subcategory_valid_interval_inclusive": [2, 17],
        },
        "authority_boundary": (
            "Static decoding proves widths and dispatch inputs. Real Rekordbox "
            "record/repeat determines serialized row fields and transport behavior."
        ),
    }
    args.json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    args.markdown.write_text(
        f"""# Track render override-control decoder audit

This generated audit is pinned to Rekordbox 7.2.19 x86-64 executable SHA-256
`{digest}` and validates {len(validated)} exact instructions across the render,
row-builder, and secondary-extractor functions.

Eight-argument rendering reads argument 7 as a 32-bit value and immediately
canonicalizes it with `setne`; every nonzero bit pattern reaches the row builder
as the same one-byte true value. Argument 8 remains a full 32-bit value. When
the gate is true, selector zero retains the database-selected column and a
nonzero selector replaces it.

The effective selector has two widths downstream. `ReturnIconID` receives its
signed low byte, while `Get_SubCategoryValue` receives all 32 bits. The latter
subtracts two and admits only the unsigned interval 2 through 17. Consequently,
a high-word value whose low byte resembles a valid selector is not statically
equivalent to that selector: icon comparison and value extraction can disagree.

The live matrix crosses boolean-boundary gate values, selector zero and one,
the reserved 14 hole, the upper valid selector, the first out-of-range value,
low-byte wrap cases, a high-word Artist lookalike, and signed/unsigned 32-bit
boundaries. Returned `0x4101` rows remain authority observations rather than
predictions from this decoder audit.
"""
    )

    lines = []
    current = None
    for name, address, mnemonic, operands in disassembly:
        if name != current:
            if lines:
                lines.append("")
            lines.append(f"## {name}")
            current = name
        lines.append(f"{address:#013x}  {mnemonic:<9} {operands}")
    args.disassembly.write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
