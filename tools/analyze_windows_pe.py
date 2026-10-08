#!/usr/bin/env python3
"""Inspect the stripped x86-64 Windows Rekordbox executable reproducibly."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from bisect import bisect_right
from pathlib import Path

import lief
from capstone import CS_ARCH_X86, CS_MODE_64, Cs
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_REG_RIP


def parse_integer(value: str) -> int:
    return int(value, 0)


class PeImage:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.raw = path.read_bytes()
        self.binary = lief.PE.parse(str(path))
        if self.binary is None:
            raise SystemExit(f"not a PE image: {path}")

        self.base = self.binary.optional_header.imagebase
        self.sections = {section.name: section for section in self.binary.sections}
        self.text = self.require_section(".text")
        self.text_bytes = bytes(self.text.content)
        self.text_start = self.base + self.text.virtual_address
        self.text_end = self.text_start + len(self.text_bytes)
        self.functions = self.parse_runtime_functions()
        self.function_starts = [start for start, _ in self.functions]

    def require_section(self, name: str) -> lief.PE.Section:
        try:
            return self.sections[name]
        except KeyError as error:
            raise SystemExit(f"PE image has no {name} section") from error

    def parse_runtime_functions(self) -> list[tuple[int, int]]:
        pdata = bytes(self.require_section(".pdata").content)
        functions = set()
        for offset in range(0, len(pdata) - 11, 12):
            begin, end, _unwind = struct.unpack_from("<III", pdata, offset)
            if begin and begin < end:
                functions.add((self.base + begin, self.base + end))

        return sorted(functions)

    def owner(self, address: int) -> tuple[int, int] | None:
        index = bisect_right(self.function_starts, address) - 1
        if index < 0:
            return None

        function = self.functions[index]
        return function if address < function[1] else None

    def virtual_address(self, file_offset: int) -> int | None:
        for section in self.binary.sections:
            start = section.pointerto_raw_data
            end = start + section.sizeof_raw_data
            if start <= file_offset < end:
                return self.base + section.virtual_address + file_offset - start

        return None

    def file_offset(self, address: int) -> int | None:
        relative = address - self.base
        for section in self.binary.sections:
            start = section.virtual_address
            end = start + section.sizeof_raw_data
            if start <= relative < end:
                return section.pointerto_raw_data + relative - start

        return None

    def content(self, start: int, end: int) -> bytes:
        return bytes(self.binary.get_content_from_virtual_address(start - self.base, end - start))

    def code_content(self, start: int, end: int) -> bytes:
        if self.text_start <= start <= end <= self.text_end:
            offset = start - self.text_start
            return self.text_bytes[offset : offset + end - start]

        return self.content(start, end)

    def printable_string(self, address: int) -> str | None:
        if self.file_offset(address) is None:
            return None

        try:
            raw = bytes(self.binary.get_content_from_virtual_address(address - self.base, 256))
        except (SystemError, TypeError, ValueError):
            return None

        value = raw.split(b"\0", 1)[0]
        if len(value) < 4 or any(byte < 0x20 or byte >= 0x7F for byte in value):
            return None

        return value.decode("ascii")

    def find_all(self, needle: bytes) -> list[int]:
        offsets = []
        cursor = 0
        while (offset := self.raw.find(needle, cursor)) != -1:
            offsets.append(offset)
            cursor = offset + 1

        return offsets


def disassembler() -> Cs:
    result = Cs(CS_ARCH_X86, CS_MODE_64)
    result.detail = True
    result.skipdata = True
    return result


def immediate_candidates(content: bytes, value: int) -> set[int]:
    offsets = set()
    for width in (1, 2, 4, 8):
        if value < 0 or value >= 1 << (width * 8):
            continue

        needle = value.to_bytes(width, "little")
        cursor = 0
        while (offset := content.find(needle, cursor)) != -1:
            offsets.add(offset)
            cursor = offset + 1

    return offsets


def find_immediate(image: PeImage, value: int) -> list[dict[str, int | str]]:
    owners = set()
    for offset in immediate_candidates(image.text_bytes, value):
        owner = image.owner(image.text_start + offset)
        if owner is not None:
            owners.add(owner)

    matches = []
    decoder = disassembler()
    for start, end in sorted(owners):
        for instruction in decoder.disasm(image.code_content(start, end), start):
            if instruction.id == 0:
                continue
            if not any(
                operand.type == X86_OP_IMM and operand.imm == value
                for operand in instruction.operands
            ):
                continue

            matches.append(
                {
                    "address": instruction.address,
                    "function_start": start,
                    "function_end": end,
                    "mnemonic": instruction.mnemonic,
                    "operands": instruction.op_str,
                }
            )

    return matches


def find_immediate_signature(
    image: PeImage, values: list[int]
) -> list[dict[str, object]]:
    candidate_owners: set[tuple[int, int]] | None = None
    for value in values:
        owners = {
            owner
            for offset in immediate_candidates(image.text_bytes, value)
            if (owner := image.owner(image.text_start + offset)) is not None
        }
        candidate_owners = owners if candidate_owners is None else candidate_owners & owners

    matches = []
    decoder = disassembler()
    for start, end in sorted(candidate_owners or set()):
        instructions = []
        observed = set()
        for instruction in decoder.disasm(image.code_content(start, end), start):
            if instruction.id == 0:
                continue

            instruction_values = sorted(
                {
                    operand.imm
                    for operand in instruction.operands
                    if operand.type == X86_OP_IMM and operand.imm in values
                }
            )
            if not instruction_values:
                continue

            observed.update(instruction_values)
            instructions.append(
                {
                    "address": instruction.address,
                    "mnemonic": instruction.mnemonic,
                    "operands": instruction.op_str,
                    "values": instruction_values,
                }
            )

        if observed == set(values):
            matches.append(
                {
                    "function_start": start,
                    "function_end": end,
                    "values": values,
                    "instructions": instructions,
                }
            )

    return matches


def find_displacement_signature(
    image: PeImage, values: list[int]
) -> list[dict[str, object]]:
    candidate_owners: set[tuple[int, int]] | None = None
    for value in values:
        needle = struct.pack("<i", value)
        owners = set()
        cursor = 0
        while (offset := image.text_bytes.find(needle, cursor)) != -1:
            cursor = offset + 1
            owner = image.owner(image.text_start + offset)
            if owner is not None:
                owners.add(owner)

        candidate_owners = owners if candidate_owners is None else candidate_owners & owners

    matches = []
    decoder = disassembler()
    for start, end in sorted(candidate_owners or set()):
        instructions = []
        observed = set()
        for instruction in decoder.disasm(image.code_content(start, end), start):
            if instruction.id == 0:
                continue

            instruction_values = sorted(
                {
                    operand.mem.disp
                    for operand in instruction.operands
                    if operand.type == X86_OP_MEM and operand.mem.disp in values
                }
            )
            if not instruction_values:
                continue

            observed.update(instruction_values)
            instructions.append(
                {
                    "address": instruction.address,
                    "mnemonic": instruction.mnemonic,
                    "operands": instruction.op_str,
                    "values": instruction_values,
                }
            )

        if observed == set(values):
            matches.append(
                {
                    "function_start": start,
                    "function_end": end,
                    "values": values,
                    "instructions": instructions,
                }
            )

    return matches


def find_xrefs(image: PeImage, targets: set[int]) -> list[dict[str, int | str]]:
    matches = []
    decoder = disassembler()
    for start, end in image.functions:
        for instruction in decoder.disasm(image.code_content(start, end), start):
            if instruction.id == 0:
                continue

            referenced = set()
            for operand in instruction.operands:
                if operand.type == X86_OP_IMM and operand.imm in targets:
                    referenced.add(operand.imm)
                elif operand.type == X86_OP_MEM and operand.mem.base == X86_REG_RIP:
                    target = instruction.address + instruction.size + operand.mem.disp
                    if target in targets:
                        referenced.add(target)

            for target in sorted(referenced):
                matches.append(
                    {
                        "address": instruction.address,
                        "function_start": start,
                        "function_end": end,
                        "mnemonic": instruction.mnemonic,
                        "operands": instruction.op_str,
                        "target": target,
                    }
                )

    return matches


def find_direct_control_xrefs(
    image: PeImage, targets: set[int]
) -> list[dict[str, int | str]]:
    candidate_owners = set()
    for opcode in (b"\xe8", b"\xe9"):
        cursor = 0
        while (offset := image.text_bytes.find(opcode, cursor)) != -1:
            cursor = offset + 1
            if offset + 5 > len(image.text_bytes):
                continue

            displacement = struct.unpack_from("<i", image.text_bytes, offset + 1)[0]
            address = image.text_start + offset
            if address + 5 + displacement not in targets:
                continue

            owner = image.owner(address)
            if owner is not None:
                candidate_owners.add(owner)

    matches = []
    decoder = disassembler()
    for start, end in sorted(candidate_owners):
        for instruction in decoder.disasm(image.code_content(start, end), start):
            if instruction.id == 0 or not instruction.mnemonic.startswith(("call", "j")):
                continue

            referenced = {
                operand.imm
                for operand in instruction.operands
                if operand.type == X86_OP_IMM and operand.imm in targets
            }
            for target in sorted(referenced):
                matches.append(
                    {
                        "address": instruction.address,
                        "function_start": start,
                        "function_end": end,
                        "mnemonic": instruction.mnemonic,
                        "operands": instruction.op_str,
                        "target": target,
                    }
                )

    return matches


def find_absolute_pointers(
    image: PeImage, targets: set[int]
) -> list[dict[str, int | str | None]]:
    matches = []
    for target in sorted(targets):
        for file_offset in image.find_all(struct.pack("<Q", target)):
            address = image.virtual_address(file_offset)
            owner = image.owner(address) if address is not None else None
            section = next(
                (
                    item.name
                    for item in image.binary.sections
                    if item.pointerto_raw_data
                    <= file_offset
                    < item.pointerto_raw_data + item.sizeof_raw_data
                ),
                None,
            )
            matches.append(
                {
                    "file_offset": file_offset,
                    "address": address,
                    "section": section,
                    "function_start": owner[0] if owner else None,
                    "function_end": owner[1] if owner else None,
                    "target": target,
                }
            )

    return matches


def render_code(image: PeImage, start: int, end: int) -> str:
    lines = [f"address={start:#x} size={end - start:#x}"]
    decoder = disassembler()
    for instruction in decoder.disasm(image.code_content(start, end), start):
        if instruction.id == 0:
            lines.append(f"{instruction.address:#012x}  .byte     {instruction.op_str}")
            continue

        annotations = []
        for operand in instruction.operands:
            if operand.type == X86_OP_IMM and instruction.mnemonic.startswith(("call", "j")):
                target = operand.imm
                target_owner = image.owner(target)
                if target_owner is not None:
                    annotations.append(f"function {target_owner[0]:#x}")
            elif operand.type == X86_OP_MEM and operand.mem.base == X86_REG_RIP:
                target = instruction.address + instruction.size + operand.mem.disp
                value = image.printable_string(target)
                if value:
                    annotations.append(repr(value))

        suffix = f"  ; {'; '.join(dict.fromkeys(annotations))}" if annotations else ""
        lines.append(
            f"{instruction.address:#012x}  {instruction.mnemonic:<9} "
            f"{instruction.op_str}{suffix}".rstrip()
        )

    return "\n".join(lines) + "\n"


def render_function(image: PeImage, address: int) -> str:
    if address < image.base:
        address += image.base
    owner = image.owner(address)
    if owner is None:
        raise SystemExit(f"address is not covered by .pdata: {address:#x}")

    return render_code(image, *owner)


def metadata(image: PeImage) -> dict[str, object]:
    return {
        "path": str(image.path),
        "size": len(image.raw),
        "sha256": hashlib.sha256(image.raw).hexdigest(),
        "image_base": image.base,
        "entrypoint": image.base + image.binary.optional_header.addressof_entrypoint,
        "machine": str(image.binary.header.machine),
        "runtime_function_count": len(image.functions),
        "sections": [
            {
                "name": section.name,
                "virtual_address": image.base + section.virtual_address,
                "virtual_size": section.virtual_size,
                "file_offset": section.pointerto_raw_data,
                "file_size": section.sizeof_raw_data,
            }
            for section in image.binary.sections
        ],
    }


def class_vtables(
    image: PeImage, class_name: str, start_offset: int, end_offset: int
) -> list[dict[str, object]]:
    decorated = f".?AV{class_name}@@".encode("ascii") + b"\0"
    descriptors = []
    for name_offset in image.find_all(decorated):
        descriptor_offset = name_offset - 16
        descriptor_address = image.virtual_address(descriptor_offset)
        if descriptor_address is not None:
            descriptors.append((descriptor_offset, descriptor_address))

    results = []
    for descriptor_offset, descriptor_address in descriptors:
        descriptor_rva = descriptor_address - image.base
        for reference in image.find_all(struct.pack("<I", descriptor_rva)):
            locator_offset = reference - 12
            locator_address = image.virtual_address(locator_offset)
            if locator_address is None or locator_offset < 0:
                continue

            signature, object_offset, constructor_offset, type_rva, hierarchy_rva, self_rva = (
                struct.unpack_from("<6I", image.raw, locator_offset)
            )
            if signature != 1 or type_rva != descriptor_rva:
                continue
            if self_rva != locator_address - image.base:
                continue

            locator_pointer = struct.pack("<Q", locator_address)
            for pointer_offset in image.find_all(locator_pointer):
                vtable_address = image.virtual_address(pointer_offset + 8)
                if vtable_address is None:
                    continue

                entries = []
                for offset in range(start_offset, end_offset, 8):
                    entry_offset = pointer_offset + 8 + offset
                    if entry_offset + 8 > len(image.raw):
                        break
                    target = struct.unpack_from("<Q", image.raw, entry_offset)[0]
                    owner = image.owner(target)
                    entries.append(
                        {
                            "offset": offset,
                            "target": target,
                            "function_start": owner[0] if owner else None,
                            "function_end": owner[1] if owner else None,
                        }
                    )

                results.append(
                    {
                        "class": class_name,
                        "type_descriptor_file_offset": descriptor_offset,
                        "type_descriptor_address": descriptor_address,
                        "complete_object_locator_file_offset": locator_offset,
                        "complete_object_locator_address": locator_address,
                        "object_offset": object_offset,
                        "constructor_offset": constructor_offset,
                        "class_hierarchy_rva": hierarchy_rva,
                        "vtable_address": vtable_address,
                        "entries": entries,
                    }
                )

    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("binary", type=Path)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("metadata")
    immediate = subparsers.add_parser("immediate")
    immediate.add_argument("value", type=parse_integer)
    signature = subparsers.add_parser("signature")
    signature.add_argument("values", type=parse_integer, nargs="+")
    displacement_signature = subparsers.add_parser("displacement-signature")
    displacement_signature.add_argument("values", type=parse_integer, nargs="+")
    function = subparsers.add_parser("function")
    function.add_argument("address", type=parse_integer)
    code_range = subparsers.add_parser("range")
    code_range.add_argument("start", type=parse_integer)
    code_range.add_argument("end", type=parse_integer)
    xrefs = subparsers.add_parser("xrefs")
    xrefs.add_argument("addresses", type=parse_integer, nargs="+")
    direct_xrefs = subparsers.add_parser("direct-xrefs")
    direct_xrefs.add_argument("addresses", type=parse_integer, nargs="+")
    pointers = subparsers.add_parser("pointers")
    pointers.add_argument("addresses", type=parse_integer, nargs="+")
    vtable = subparsers.add_parser("vtable")
    vtable.add_argument("class_name")
    vtable.add_argument("--start", type=parse_integer, default=0)
    vtable.add_argument("--end", type=parse_integer, default=0x100)
    args = parser.parse_args()

    image = PeImage(args.binary)
    if args.command == "metadata":
        print(json.dumps(metadata(image), indent=2, sort_keys=True))
    elif args.command == "immediate":
        print(json.dumps(find_immediate(image, args.value), indent=2, sort_keys=True))
    elif args.command == "signature":
        print(
            json.dumps(
                find_immediate_signature(image, args.values),
                indent=2,
                sort_keys=True,
            )
        )
    elif args.command == "displacement-signature":
        print(
            json.dumps(
                find_displacement_signature(image, args.values),
                indent=2,
                sort_keys=True,
            )
        )
    elif args.command == "function":
        print(render_function(image, args.address), end="")
    elif args.command == "range":
        start = args.start if args.start >= image.base else image.base + args.start
        end = args.end if args.end >= image.base else image.base + args.end
        if not image.text_start <= start < end <= image.text_end:
            raise SystemExit(f"range is outside .text: {start:#x}..{end:#x}")
        print(render_code(image, start, end), end="")
    elif args.command == "xrefs":
        print(
            json.dumps(
                find_xrefs(image, set(args.addresses)),
                indent=2,
                sort_keys=True,
            )
        )
    elif args.command == "direct-xrefs":
        print(
            json.dumps(
                find_direct_control_xrefs(image, set(args.addresses)),
                indent=2,
                sort_keys=True,
            )
        )
    elif args.command == "pointers":
        print(
            json.dumps(
                find_absolute_pointers(image, set(args.addresses)),
                indent=2,
                sort_keys=True,
            )
        )
    elif args.command == "vtable":
        print(
            json.dumps(
                class_vtables(image, args.class_name, args.start, args.end),
                indent=2,
                sort_keys=True,
            )
        )


if __name__ == "__main__":
    main()
