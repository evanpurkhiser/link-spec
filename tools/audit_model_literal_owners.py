#!/usr/bin/env python3
"""Classify exact XDJ model-literal owners in the symbol-rich Rekordbox slice."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import subprocess
from bisect import bisect_right
from collections import defaultdict
from pathlib import Path

import lief
from capstone import CS_ARCH_X86, CS_MODE_64, Cs


EXPECTED_MACHO_SHA256 = "07dcecbaf304f777e435539c83c7dcc02e41de1eaf2e0a75e8a9852e4411a244"
LITERALS = (b"XDJ\0", b"XDJ-AZ\0")
ROOT = Path(__file__).resolve().parent.parent


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def demangle(names: list[str]) -> dict[str, str]:
    inputs = [name[1:] if name.startswith("__Z") else name for name in names]
    process = subprocess.run(
        ["c++filt"],
        input="\n".join(inputs) + "\n",
        capture_output=True,
        check=True,
        text=True,
    )
    return dict(zip(names, process.stdout.splitlines(), strict=True))


def scope(symbols: list[str]) -> str:
    joined = " ".join(symbols)
    if any(marker in joined for marker in ("PSvDBMain", "PSvAppSyncDBIF", "PSvMasterDBIF", "Dsql")):
        return "database-serving"
    if any(marker in joined for marker in ("Audio", "ASIO", "WASAPI", "DeviceDefs")):
        return "audio-device"
    if any(marker in joined for marker in ("HID", "Hid", "Midi", "MIDI", "Control")):
        return "controller-mapping"
    if any(marker in joined for marker in ("Widget", "Dialog", "Component", "Preferences", "Export")):
        return "application-ui"
    if any(marker in joined for marker in ("PSvLink", "ProDJLink", "LinkDevice")):
        return "link-plumbing"
    return "other"


def literal_addresses(binary: lief.MachO.Binary) -> dict[str, list[int]]:
    result: dict[str, list[int]] = defaultdict(list)
    for section in binary.sections:
        content = bytes(section.content)
        for literal in LITERALS:
            cursor = 0
            while (offset := content.find(literal, cursor)) != -1:
                cursor = offset + 1
                result[literal[:-1].decode()].append(section.virtual_address + offset)

    return {literal[:-1].decode(): sorted(result[literal[:-1].decode()]) for literal in LITERALS}


def audit(macho: Path, windows_audit: Path) -> dict[str, object]:
    digest = sha256(macho)
    if digest != EXPECTED_MACHO_SHA256:
        raise SystemExit(f"unexpected Rekordbox Mach-O hash: {digest}")

    fat = lief.MachO.parse(str(macho))
    binary = next(
        item
        for item in fat
        if item.header.cpu_type == lief.MachO.Header.CPU_TYPE.X86_64
    )
    text = binary.get_section("__text")
    if text is None:
        raise SystemExit("Mach-O has no __text section")

    names: dict[int, list[str]] = defaultdict(list)
    for symbol in binary.symbols:
        if (
            symbol.value
            and symbol.name
            and text.virtual_address <= symbol.value < text.virtual_address + len(text.content)
            and symbol.name not in names[symbol.value]
        ):
            names[symbol.value].append(symbol.name)
    symbol_addresses = sorted(names)
    demangled = demangle(sorted({name for values in names.values() for name in values}))

    literals = literal_addresses(binary)
    address_to_literal = {
        address: literal
        for literal, addresses in literals.items()
        for address in addresses
    }
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    content = bytes(text.content)
    references = []
    for offset in range(len(content) - 7):
        if not 0x48 <= content[offset] <= 0x4F or content[offset + 1] != 0x8D:
            continue
        if content[offset + 2] & 0xC7 != 0x05:
            continue
        displacement = struct.unpack_from("<i", content, offset + 3)[0]
        address = text.virtual_address + offset
        target = address + 7 + displacement
        if target not in address_to_literal:
            continue

        index = bisect_right(symbol_addresses, address) - 1
        owner_address = symbol_addresses[index]
        owner_names = names[owner_address]
        instruction = next(decoder.disasm(content[offset : offset + 7], address))
        rendered_names = [demangled[name] for name in owner_names]
        references.append(
            {
                "literal": address_to_literal[target],
                "literal_address": f"0x{target:x}",
                "address": f"0x{address:x}",
                "owner_address": f"0x{owner_address:x}",
                "owner_symbols": owner_names,
                "owner_demangled": rendered_names,
                "owner_scope": scope(rendered_names),
                "mnemonic": instruction.mnemonic,
                "operands": instruction.op_str,
            }
        )

    windows = json.loads(windows_audit.read_text())
    windows_references = windows["model_literal_references"]
    return {
        "format": 1,
        "scope": "exact XDJ and XDJ-AZ literal ownership across pinned Rekordbox 7.2.19 slices",
        "macho": {
            "sha256": digest,
            "architecture": "x86_64",
            "model_literals": {
                name: [f"0x{address:x}" for address in addresses]
                for name, addresses in literals.items()
            },
            "references": references,
            "scope_counts": {
                category: sum(reference["owner_scope"] == category for reference in references)
                for category in sorted({reference["owner_scope"] for reference in references})
            },
        },
        "windows": {
            "audit_path": str(windows_audit.resolve().relative_to(ROOT)),
            "sha256": windows["source"]["sha256"],
            "reference_count": len(windows_references),
            "bare_xdj_reference_count": sum(
                reference["literal"] == "XDJ" for reference in windows_references
            ),
            "xdj_az_reference_count": sum(
                reference["literal"] == "XDJ-AZ" for reference in windows_references
            ),
        },
        "boundary": (
            "Exact-literal ownership classifies direct RIP-relative LEA uses. It does not "
            "equate function addresses between platforms or cover dynamically constructed "
            "model strings, indirect literal loads, or predicates with other spellings."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("macho", type=Path)
    parser.add_argument("windows_audit", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    args.output.write_text(json.dumps(audit(args.macho, args.windows_audit), indent=2) + "\n")


if __name__ == "__main__":
    main()
