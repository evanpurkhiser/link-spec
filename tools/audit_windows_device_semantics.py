#!/usr/bin/env python3
"""Audit inlined Windows device decisions across the complete PE image."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

from capstone.x86 import X86_OP_IMM, X86_OP_REG

from analyze_windows_pe import PeImage, disassembler, immediate_candidates


EXPECTED_SHA256 = "c9ed23e974c51c75e2ec069fbd2679a3dbe606be9e79e9cbbd13d6418ab11c37"
MODEL_LITERALS = (b"XDJ\0", b"XDJ-AZ\0")


def hexadecimal(value: int) -> str:
    return f"0x{value:x}"


def literal_addresses(image: PeImage) -> dict[str, list[int]]:
    result = {}
    for literal in MODEL_LITERALS:
        addresses = []
        for offset in image.find_all(literal):
            address = image.virtual_address(offset)
            if address is not None:
                addresses.append(address)
        result[literal[:-1].decode()] = sorted(addresses)

    return result


def literal_references(
    image: PeImage, address_to_literal: dict[int, str]
) -> list[dict[str, str]]:
    matches = []
    decoder = disassembler()
    content = image.text_bytes
    for offset in range(len(content) - 7):
        if not 0x48 <= content[offset] <= 0x4F or content[offset + 1] != 0x8D:
            continue
        if content[offset + 2] & 0xC7 != 0x05:
            continue

        displacement = struct.unpack_from("<i", content, offset + 3)[0]
        address = image.text_start + offset
        target = address + 7 + displacement
        if target not in address_to_literal:
            continue

        instruction = next(decoder.disasm(content[offset : offset + 7], address), None)
        owner = image.owner(address)
        if instruction is None or owner is None:
            continue
        matches.append(
            {
                "literal": address_to_literal[target],
                "literal_address": hexadecimal(target),
                "address": hexadecimal(address),
                "function_start": hexadecimal(owner[0]),
                "function_end": hexadecimal(owner[1]),
                "mnemonic": instruction.mnemonic,
                "operands": instruction.op_str,
            }
        )

    return matches


def arithmetic_step(instruction) -> tuple[str, int, int] | None:
    if instruction.mnemonic not in {"sub", "cmp"} or len(instruction.operands) != 2:
        return None

    register, immediate = instruction.operands
    if register.type != X86_OP_REG or immediate.type != X86_OP_IMM:
        return None

    return instruction.mnemonic, register.reg, immediate.imm


def compatibility_matches(image: PeImage) -> list[dict[str, object]]:
    matches = []
    seen = set()
    decoder = disassembler()
    candidate_owners = None
    for value in (44100, 48000):
        owners = {
            owner
            for offset in immediate_candidates(image.text_bytes, value)
            if (owner := image.owner(image.text_start + offset)) is not None
        }
        candidate_owners = owners if candidate_owners is None else candidate_owners & owners

    function_indexes = {function: index for index, function in enumerate(image.functions)}
    for owner in sorted(candidate_owners or set()):
        index = function_indexes[owner]
        start = image.functions[index - 1][0] if index else owner[0]
        end = owner[1]
        instructions = [
            instruction
            for instruction in decoder.disasm(image.code_content(start, end), start)
            if instruction.id != 0
        ]
        steps = [
            (index, instruction, step)
            for index, instruction in enumerate(instructions)
            if (step := arithmetic_step(instruction)) is not None
        ]
        for position in range(len(steps) - 5):
            candidate = steps[position : position + 6]
            indices = [item[0] for item in candidate]
            values = [item[2] for item in candidate]
            register = values[0][1]
            if [value[0] for value in values] != ["sub", "sub", "sub", "cmp", "cmp", "cmp"]:
                continue
            if [value[1] for value in values[:4]] != [register] * 4:
                continue
            if [value[2] for value in values] != [5, 1, 5, 1, 44100, 48000]:
                continue
            if indices[-1] - indices[0] > 16:
                continue

            addresses = tuple(item[1].address for item in candidate)
            if addresses in seen:
                continue
            seen.add(addresses)

            matches.append(
                {
                    "scan_start": hexadecimal(start),
                    "scan_end": hexadecimal(end),
                    "runtime_function_starts": sorted(
                        {
                            hexadecimal(runtime_owner[0])
                            for item in candidate
                            if (runtime_owner := image.owner(item[1].address)) is not None
                        }
                    ),
                    "instruction_addresses": [
                        hexadecimal(address) for address in addresses
                    ],
                    "normalized_operations": [
                        f"{item[2][0]} reg,{item[2][2]}" for item in candidate
                    ],
                }
            )
            break

    return matches


def build(binary: Path) -> dict[str, object]:
    image = PeImage(binary)
    digest = hashlib.sha256(image.raw).hexdigest()
    if digest != EXPECTED_SHA256:
        raise SystemExit(f"unexpected Rekordbox PE hash: {digest}")

    literals = literal_addresses(image)
    address_to_literal = {
        address: literal
        for literal, addresses in literals.items()
        for address in addresses
    }
    references = literal_references(image, address_to_literal)
    result = {
        "format": 1,
        "scope": "whole-image Windows Rekordbox 7.2.19 inlined device decisions",
        "source": {
            "sha256": digest,
            "size": len(image.raw),
            "runtime_function_count": len(image.functions),
        },
        "model_literals": {
            literal: [hexadecimal(address) for address in addresses]
            for literal, addresses in literals.items()
        },
        "model_literal_references": references,
        "compatibility_semantic_signature": {
            "operations": [
                "sub reg,5",
                "sub reg,1",
                "sub reg,5",
                "cmp reg,1",
                "cmp sample_rate,44100",
                "cmp sample_rate,48000",
            ],
            "maximum_instruction_span": 16,
            "matches": compatibility_matches(image),
        },
        "boundary": (
            "The scan exhausts PE runtime functions containing both sample-rate constants "
            "for the normalized compatibility instruction sequence and every direct x86-64 "
            "RIP-relative LEA reference to exact ASCII XDJ and XDJ-AZ literals. Dynamically "
            "constructed strings and semantically different classifiers remain outside this "
            "signature."
        ),
    }

    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("binary", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    rendered = json.dumps(build(args.binary), indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered)
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
