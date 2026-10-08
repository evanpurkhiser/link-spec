#!/usr/bin/env python3
"""Audit code references that construct or select Rekordbox DB interfaces."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
from bisect import bisect_right
from collections import defaultdict
from pathlib import Path

import lief
from capstone import CS_ARCH_X86, CS_MODE_64, Cs
from capstone.x86 import X86_OP_MEM, X86_REG_RIP


EXPECTED_SHA256 = "07dcecbaf304f777e435539c83c7dcc02e41de1eaf2e0a75e8a9852e4411a244"
VTABLE_SYMBOLS = {
    "appsync": "__ZTV14PSvAppSyncDBIF",
    "master": "__ZTV13PSvMasterDBIF",
}
RIP_RELATIVE_LEA = re.compile(
    b"(?:[\\x40-\\x4f])?\\x8d[\\x05\\x0d\\x15\\x1d\\x25\\x2d\\x35\\x3d].{4}",
    re.DOTALL,
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def hexadecimal(value: int) -> str:
    return f"{value:#x}"


def audit(binary_path: Path) -> dict[str, object]:
    binary_hash = sha256(binary_path)
    if binary_hash != EXPECTED_SHA256:
        raise SystemExit(f"unexpected binary SHA-256: {binary_hash}")

    fat = lief.MachO.parse(str(binary_path))
    binary = next(item for item in fat if item.header.cpu_type == lief.MachO.Header.CPU_TYPE.X86_64)
    text = binary.get_section("__text")
    if text is None:
        raise SystemExit("binary has no __text section")

    symbols = sorted(
        (symbol.value, symbol.name)
        for symbol in binary.symbols
        if symbol.value and symbol.name
    )
    symbol_addresses: dict[str, int] = {}
    names: dict[int, list[str]] = defaultdict(list)
    for address, name in symbols:
        symbol_addresses.setdefault(name, address)
        if name not in names[address]:
            names[address].append(name)

    missing = [symbol for symbol in VTABLE_SYMBOLS.values() if symbol not in symbol_addresses]
    if missing:
        raise SystemExit("missing vtable symbols: " + ", ".join(missing))

    unique_symbol_addresses = sorted(names)
    tables: dict[str, dict[str, object]] = {}
    for interface, symbol in VTABLE_SYMBOLS.items():
        address = symbol_addresses[symbol]
        next_address = next(item for item in unique_symbol_addresses if item > address)
        tables[interface] = {
            "symbol": symbol,
            "address": hexadecimal(address),
            "object_vptr_address": hexadecimal(address + 0x10),
            "end_address_exclusive": hexadecimal(next_address),
            "size": next_address - address,
            "references": [],
        }

    text_start = text.virtual_address
    text_end = text_start + text.size
    code_addresses = [address for address in unique_symbol_addresses if text_start <= address < text_end]
    content = bytes(text.content)
    disassembler = Cs(CS_ARCH_X86, CS_MODE_64)
    disassembler.detail = True
    candidates = []
    table_ranges = [
        (int(table["address"], 16), int(table["end_address_exclusive"], 16))
        for table in tables.values()
    ]
    for match in RIP_RELATIVE_LEA.finditer(content):
        instruction_address = text_start + match.start()
        displacement = struct.unpack_from("<i", match.group(), len(match.group()) - 4)[0]
        target = instruction_address + len(match.group()) + displacement
        if not any(start <= target < end for start, end in table_ranges):
            continue

        instruction = next(disassembler.disasm(match.group(), text_start + match.start()), None)
        if instruction is None or instruction.size != len(match.group()) or instruction.mnemonic != "lea":
            continue
        candidates.append(instruction)

    for instruction in candidates:
        for operand in instruction.operands:
            if operand.type != X86_OP_MEM or operand.mem.base != X86_REG_RIP:
                continue

            target = instruction.address + instruction.size + operand.mem.disp
            for table in tables.values():
                table_start = int(table["address"], 16)
                table_end = int(table["end_address_exclusive"], 16)
                if not table_start <= target < table_end:
                    continue

                owner_index = bisect_right(code_addresses, instruction.address) - 1
                owner_address = code_addresses[owner_index] if owner_index >= 0 else 0
                table["references"].append({
                    "instruction_address": hexadecimal(instruction.address),
                    "instruction": f"{instruction.mnemonic} {instruction.op_str}".strip(),
                    "target_address": hexadecimal(target),
                    "vtable_offset": hexadecimal(target - table_start),
                    "owner_address": hexadecimal(owner_address),
                    "owner_symbols": names.get(owner_address, ["<unknown>"]),
                })

    for table in tables.values():
        table["reference_count"] = len(table["references"])
        table["vtable_base_reference_count"] = sum(
            item["vtable_offset"] == "0x0" for item in table["references"]
        )
        table["exact_object_vptr_reference_count"] = sum(
            item["vtable_offset"] == "0x10" for item in table["references"]
        )

    return {
        "format": "rekordbox-db-interface-selection-audit-v1",
        "binary": {
            "path": str(binary_path),
            "sha256": binary_hash,
            "architecture": "x86_64",
        },
        "method": {
            "reference_kind": "validated RIP-relative LEA operands in the complete __text section",
            "owner_attribution": "nearest preceding address-bearing symbol in __text",
            "object_vptr_offset": "Itanium ABI vtable + 0x10",
            "limits": [
                "computed addresses",
                "non-LEA references",
                "references originating outside __text",
                "arm64-only behavior",
                "runtime writes performed by external or dynamically loaded code",
            ],
        },
        "interfaces": tables,
    }


def render(report: dict[str, object]) -> str:
    lines = [
        "# Database-interface selection audit",
        "",
        "This generated report inventories constructor-style x86-64 `__text` LEA",
        "references into the complete `PSvAppSyncDBIF` and `PSvMasterDBIF` tables.",
        "Constructor-style object vptrs use the Itanium ABI table offset `+0x10`.",
        "",
        f"Binary SHA-256: `{report['binary']['sha256']}`.",
        "",
        "| Interface | Vtable | Bytes | LEA refs | Base refs | Exact `+0x10` refs |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name, table in report["interfaces"].items():
        lines.append(
            f"| `{name}` | `{table['address']}` | `{table['size']:#x}` | "
            f"{table['reference_count']} | {table['vtable_base_reference_count']} | "
            f"{table['exact_object_vptr_reference_count']} |"
        )

    for name, table in report["interfaces"].items():
        lines.extend(["", f"## {name}", ""])
        if not table["references"]:
            lines.append("No x86-64 `__text` references enter this vtable range.")
            continue

        for reference in table["references"]:
            owners = "`, `".join(reference["owner_symbols"])
            lines.append(
                f"- `{reference['instruction_address']}` in `{owners}`: "
                f"`{reference['instruction']}` -> vtable `{reference['vtable_offset']}`."
            )

    lines.extend([
        "",
        "## Boundary",
        "",
        "A reference to vtable offset zero followed by an add of `0x10` is also a",
        "constructor-style selection; inspect the attributed function disassembly.",
        "A zero reference count is a bounded negative result for RIP-relative LEA",
        "selection in the pinned x86-64 text slice. It does not exclude computed",
        "addresses, non-LEA or non-text initializers, arm64-only behavior, or",
        "construction by dynamically loaded code.",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("binary", type=Path)
    parser.add_argument("--json", type=Path, required=True)
    parser.add_argument("--markdown", type=Path, required=True)
    args = parser.parse_args()

    report = audit(args.binary)
    args.json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    args.markdown.write_text(render(report))
    print(
        ", ".join(
            f"{name}={table['reference_count']}"
            for name, table in report["interfaces"].items()
        )
    )


if __name__ == "__main__":
    main()
