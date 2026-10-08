#!/usr/bin/env python3
"""Find direct x86-64 call/jump references to a virtual address in a Mach-O."""

from __future__ import annotations

import argparse
import struct
from bisect import bisect_right
from collections import defaultdict
from pathlib import Path

import lief
from capstone import CS_ARCH_X86, CS_MODE_64, Cs
from capstone.x86 import X86_OP_IMM


REL32_OPCODES = {
    0xE8: "call",
    0xE9: "jmp",
}


def relative_branch_candidates(
    content: bytes,
    virtual_address: int,
    targets: set[int],
):
    """Yield rel32 branches whose computed destination is a requested target."""
    for opcode, mnemonic in REL32_OPCODES.items():
        cursor = 0
        needle = bytes((opcode,))

        while (offset := content.find(needle, cursor)) != -1:
            cursor = offset + 1
            if offset + 5 > len(content):
                continue

            displacement = struct.unpack_from("<i", content, offset + 1)[0]
            address = virtual_address + offset
            target = address + 5 + displacement
            if target in targets:
                yield address, mnemonic, target, offset


def is_instruction(
    disassembler: Cs,
    content: bytes,
    virtual_address: int,
    owner_address: int,
    offset: int,
    mnemonic: str,
    target: int,
) -> bool:
    """Confirm a candidate on a linear instruction boundary from its owner."""
    owner_offset = owner_address - virtual_address
    candidate_end = min(offset + 15, len(content))
    instructions = disassembler.disasm(
        content[owner_offset:candidate_end],
        owner_address,
    )
    instruction = next(
        (item for item in instructions if item.address == virtual_address + offset),
        None,
    )
    if instruction is None or instruction.mnemonic != mnemonic:
        return False
    if not instruction.operands or instruction.operands[0].type != X86_OP_IMM:
        return False

    return instruction.operands[0].imm == target


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("binary", type=Path)
    parser.add_argument("target", nargs="+", type=lambda value: int(value, 0))
    args = parser.parse_args()

    fat = lief.MachO.parse(str(args.binary))
    binary = next(item for item in fat if item.header.cpu_type == lief.MachO.Header.CPU_TYPE.X86_64)
    section = binary.get_section("__text")
    if section is None:
        raise SystemExit("binary has no __text section")

    content = bytes(section.content)
    start = section.virtual_address
    end = start + len(content)
    names: dict[int, list[str]] = defaultdict(list)
    for symbol in binary.symbols:
        if start <= symbol.value < end and symbol.name and symbol.name not in names[symbol.value]:
            names[symbol.value].append(symbol.name)
    addresses = sorted(names)

    disassembler = Cs(CS_ARCH_X86, CS_MODE_64)
    disassembler.detail = True
    targets = set(args.target)
    matches = relative_branch_candidates(content, start, targets)
    for address, mnemonic, target, offset in sorted(matches):
        index = bisect_right(addresses, address) - 1
        owner = addresses[index] if index >= 0 else 0
        if not owner or not is_instruction(
            disassembler,
            content,
            start,
            owner,
            offset,
            mnemonic,
            target,
        ):
            continue
        labels = " | ".join(names.get(owner, ["<unknown>"]))
        print(f"{target:#x}\t{address:#x}\t{mnemonic}\t{labels}\t{owner:#x}")


if __name__ == "__main__":
    main()
