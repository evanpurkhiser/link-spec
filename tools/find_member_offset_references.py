#!/usr/bin/env python3
"""Find x86-64 memory operands using selected object-member displacements."""

from __future__ import annotations

import argparse
import re
from collections import defaultdict
from pathlib import Path

import lief
from capstone import CS_ARCH_X86, CS_MODE_64, Cs
from capstone.x86 import X86_OP_MEM, X86_REG_RBP, X86_REG_RIP, X86_REG_RSP


def parse_offset(value: str) -> int:
    return int(value, 0)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("binary", type=Path)
    parser.add_argument("offset", nargs="+", type=parse_offset)
    parser.add_argument(
        "--symbol-pattern",
        default=".*",
        help="regular expression matched against the owning symbol",
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    fat = lief.MachO.parse(str(args.binary))
    binary = next(
        item
        for item in fat
        if item.header.cpu_type == lief.MachO.Header.CPU_TYPE.X86_64
    )

    names: dict[int, list[str]] = defaultdict(list)
    for symbol in binary.symbols:
        if symbol.value and symbol.name and symbol.name not in names[symbol.value]:
            names[symbol.value].append(symbol.name)

    addresses = sorted(names)
    expression = re.compile(args.symbol_pattern)
    selected = {
        address
        for address, symbol_names in names.items()
        if any(expression.search(name) for name in symbol_names)
    }
    offsets = set(args.offset)
    disassembler = Cs(CS_ARCH_X86, CS_MODE_64)
    disassembler.detail = True
    matches: list[tuple[int, int, list[str], str]] = []

    for index, start in enumerate(addresses):
        if start not in selected or index + 1 == len(addresses):
            continue

        size = addresses[index + 1] - start
        if size <= 0 or size > 0x100000:
            continue

        try:
            data = bytes(binary.get_content_from_virtual_address(start, size))
        except (SystemError, TypeError, ValueError):
            continue

        for instruction in disassembler.disasm(data, start):
            for operand in instruction.operands:
                if operand.type != X86_OP_MEM or operand.mem.disp not in offsets:
                    continue
                if operand.mem.base in (X86_REG_RIP, X86_REG_RSP, X86_REG_RBP):
                    continue

                rendered_instruction = (
                    instruction.mnemonic + " " + instruction.op_str
                )
                matches.append(
                    (
                        operand.mem.disp,
                        instruction.address,
                        names[start],
                        rendered_instruction,
                    )
                )
                break

    lines = [
        "# binary=" + str(args.binary),
        "# offsets=" + ",".join(f"{offset:#x}" for offset in sorted(offsets)),
        "# symbol_pattern=" + args.symbol_pattern,
    ]
    for offset, address, symbol_names, instruction in sorted(matches):
        lines.append(
            f"{offset:#x}\t{address:#x}\t{' | '.join(symbol_names)}\t{instruction}"
        )

    rendered = "\n".join(lines) + "\n"
    if args.output:
        args.output.write_text(rendered)
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
