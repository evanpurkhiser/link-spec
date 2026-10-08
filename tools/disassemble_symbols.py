#!/usr/bin/env python3
"""Extract annotated x86-64 functions from the rekordbox Mach-O by symbol."""

from __future__ import annotations

import argparse
import re
from collections import defaultdict
from pathlib import Path

import lief
from capstone import CS_ARCH_X86, CS_MODE_64, Cs
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_REG_RIP


def printable_string(binary: lief.MachO.Binary, address: int) -> str | None:
    try:
        raw = bytes(binary.get_content_from_virtual_address(address, 256))
    except (SystemError, TypeError, ValueError):
        return None
    value = raw.split(b"\0", 1)[0]
    if len(value) < 4 or any(byte < 0x20 or byte >= 0x7f for byte in value):
        return None
    return value.decode("ascii")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("binary", type=Path)
    parser.add_argument("pattern", help="regular expression matched against symbols")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--max-bytes", type=lambda value: int(value, 0), default=0x10000)
    args = parser.parse_args()

    fat = lief.MachO.parse(str(args.binary))
    binary = next(item for item in fat if item.header.cpu_type == lief.MachO.Header.CPU_TYPE.X86_64)

    names: dict[int, list[str]] = defaultdict(list)
    for symbol in binary.symbols:
        if symbol.value and symbol.name not in names[symbol.value]:
            names[symbol.value].append(symbol.name)
    addresses = sorted(names)
    selected = [address for address in addresses if any(re.search(args.pattern, name) for name in names[address])]
    if not selected:
        raise SystemExit(f"no symbols match {args.pattern!r}")

    disassembler = Cs(CS_ARCH_X86, CS_MODE_64)
    disassembler.detail = True
    output: list[str] = []

    for start in selected:
        next_address = next((address for address in addresses if address > start), start + args.max_bytes)
        size = min(next_address - start, args.max_bytes)
        output.append(f"## {' | '.join(names[start])}")
        output.append(f"address={start:#x} size={size:#x}")

        try:
            data = bytes(binary.get_content_from_virtual_address(start, size))
        except (SystemError, TypeError, ValueError) as error:
            output.append(f"unmapped-or-non-code-symbol: {type(error).__name__}")
            output.append("")
            continue

        for instruction in disassembler.disasm(data, start):
            annotations: list[str] = []
            for operand in instruction.operands:
                if operand.type == X86_OP_IMM and instruction.mnemonic.startswith(("call", "j")):
                    target = operand.imm
                    if target in names:
                        annotations.append(" | ".join(names[target]))
                elif operand.type == X86_OP_MEM and operand.mem.base == X86_REG_RIP:
                    target = instruction.address + instruction.size + operand.mem.disp
                    if target in names:
                        annotations.append(" | ".join(names[target]))
                    string = printable_string(binary, target)
                    if string:
                        annotations.append(repr(string))
            suffix = f"  ; {'; '.join(dict.fromkeys(annotations))}" if annotations else ""
            output.append(
                f"{instruction.address:#012x}  {instruction.mnemonic:<9} {instruction.op_str}{suffix}".rstrip()
            )
        output.append("")

    rendered = "\n".join(output) + "\n"
    if args.output:
        args.output.write_text(rendered)
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
