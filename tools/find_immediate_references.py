#!/usr/bin/env python3
"""Find decoded x86-64 instructions that reference an immediate value."""

from __future__ import annotations

import argparse
from bisect import bisect_right
from collections import defaultdict
from pathlib import Path

import lief
from capstone import CS_ARCH_X86, CS_MODE_64, Cs
from capstone.x86 import X86_OP_IMM


def immediate_candidates(content: bytes, value: int) -> set[int]:
    """Return byte offsets where a plausible little-endian immediate begins."""
    widths = (1, 2, 4, 8)
    offsets: set[int] = set()

    for width in widths:
        if value >= 1 << (width * 8):
            continue

        needle = value.to_bytes(width, "little")
        cursor = 0
        while (offset := content.find(needle, cursor)) != -1:
            offsets.add(offset)
            cursor = offset + 1

    return offsets


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("binary", type=Path)
    parser.add_argument("immediate", type=lambda value: int(value, 0))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    fat = lief.MachO.parse(str(args.binary))
    binary = next(
        item
        for item in fat
        if item.header.cpu_type == lief.MachO.Header.CPU_TYPE.X86_64
    )
    section = binary.get_section("__text")
    if section is None:
        raise SystemExit("binary has no __text section")

    names: dict[int, list[str]] = defaultdict(list)
    start = section.virtual_address
    end = start + len(section.content)
    for symbol in binary.symbols:
        if start <= symbol.value < end and symbol.name:
            names[symbol.value].append(symbol.name)
    addresses = sorted(names)

    content = bytes(section.content)
    candidate_owners: dict[int, int] = {}
    for offset in immediate_candidates(content, args.immediate):
        index = bisect_right(addresses, start + offset) - 1
        if index >= 0:
            candidate_owners[addresses[index]] = index

    disassembler = Cs(CS_ARCH_X86, CS_MODE_64)
    disassembler.detail = True
    disassembler.skipdata = True
    matches = []
    for owner, index in candidate_owners.items():
        owner_offset = owner - start
        owner_end = addresses[index + 1] if index + 1 < len(addresses) else end
        owner_content = content[owner_offset : owner_end - start]

        for instruction in disassembler.disasm(owner_content, owner):
            if instruction.id == 0:
                continue
            if not any(
                operand.type == X86_OP_IMM and operand.imm == args.immediate
                for operand in instruction.operands
            ):
                continue

            labels = " | ".join(names.get(owner, ["<unknown>"]))
            matches.append(
                (instruction.address, instruction.mnemonic, instruction.op_str, labels, owner)
            )

    lines = [
        f"{address:#x}\t{mnemonic}\t{operands}\t{labels}\t{owner:#x}"
        for address, mnemonic, operands, labels, owner in sorted(matches)
    ]
    rendered = "\n".join(lines) + ("\n" if lines else "")
    if args.output:
        args.output.write_text(rendered)
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
