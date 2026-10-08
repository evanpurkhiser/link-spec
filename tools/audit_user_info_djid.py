#!/usr/bin/env python3
"""Generate the pinned Rekordbox 0x3006/0x4d02 DJ-ID audit."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

import lief


ROOT = Path(__file__).resolve().parent.parent
MACHO = (
    ROOT.parent
    / "artifacts/rekordbox/7.2.19/extracted/app-root/rekordbox.app/Contents/MacOS/rekordbox"
)
CLIENT_SOURCE = (
    ROOT.parent
    / "alphatheta-docs/devices/cdj-3000/application/remote-database-client.md"
)
DISASSEMBLY = ROOT / "data/static-analysis/user-info-djid.disasm.txt"
COMMAND_PARSER = ROOT / "data/static-analysis/dbserver-command-parser.disasm.txt"

EXPECTED_MACHO_SHA256 = "07dcecbaf304f777e435539c83c7dcc02e41de1eaf2e0a75e8a9852e4411a244"
EXPECTED_CLIENT_SOURCE_SHA256 = "d3563dc35962b21ba224906f2307f8e7f872368d4b16cdd93c9ee24d9104fa95"

SYMBOLS = {
    "common::PropertyPath": "__ZN6common12PropertyPathEv",
    "KuvoService::isValid": "__ZN11KuvoService7isValidERKN4juce4FileE",
    "KuvoService::nxsFile": "__ZN11KuvoService7nxsFileEv",
    "KuvoService::nxsName": "__ZN11KuvoService7nxsNameE",
    "Kuvo static initializer": "__GLOBAL__sub_I_Kuvo.cpp",
    "juce::FileInputStream vtable": "__ZTVN4juce15FileInputStreamE",
    "juce::InputStream::readInt": "__ZN4juce11InputStream7readIntEv",
    "juce::InputStream::readIntBigEndian": "__ZN4juce11InputStream16readIntBigEndianEv",
    "PSvDBMain::OnUserCmd": "__ZN9PSvDBMain9OnUserCmdEP16_struct_dbsm_msg",
    "PSvDBMain::Start": "__ZN9PSvDBMain5StartEPKh",
    "PSvDBMain::GetDJID": "__ZN9PSvDBMain7GetDJIDEPh",
    "PSvDBServer::Start": "__ZN11PSvDBServer5StartEPKhPKNS_12SharedDBInfoE",
    "UiProDJLink::run": "__ZN6djplay11UiProDJLink3runEv",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT.parent.resolve()))


def symbol_addresses(binary: lief.MachO.Binary) -> dict[str, int]:
    by_name = {symbol.name: symbol.value for symbol in binary.symbols if symbol.value}
    missing = [symbol for symbol in SYMBOLS.values() if symbol not in by_name]
    if missing:
        raise SystemExit(f"missing symbols: {', '.join(missing)}")

    return {label: by_name[symbol] for label, symbol in SYMBOLS.items()}


def literal_address(binary: lief.MachO.Binary, literal: bytes) -> int:
    matches = []
    for section in binary.sections:
        content = bytes(section.content)
        cursor = 0
        while (offset := content.find(literal, cursor)) != -1:
            cursor = offset + 1
            matches.append(section.virtual_address + offset)
    if len(matches) != 1:
        raise SystemExit(f"expected one {literal!r} literal, found {len(matches)}")

    return matches[0]


def direct_call_addresses(
    text: lief.MachO.Section,
    owner_start: int,
    owner_end: int,
    target: int,
) -> list[int]:
    content = bytes(text.content)
    section_start = text.virtual_address
    start = owner_start - section_start
    end = owner_end - section_start
    matches = []
    for offset in range(start, end - 4):
        if content[offset] != 0xE8:
            continue
        displacement = struct.unpack_from("<i", content, offset + 1)[0]
        address = section_start + offset
        if address + 5 + displacement == target:
            matches.append(address)

    return matches


def rip_lea_addresses(
    text: lief.MachO.Section,
    owner_start: int,
    owner_end: int,
    target: int,
) -> list[int]:
    content = bytes(text.content)
    section_start = text.virtual_address
    start = owner_start - section_start
    end = owner_end - section_start
    matches = []
    for offset in range(start, end - 6):
        if not 0x40 <= content[offset] <= 0x4F or content[offset + 1] != 0x8D:
            continue
        if content[offset + 2] & 0xC7 != 0x05:
            continue
        displacement = struct.unpack_from("<i", content, offset + 3)[0]
        address = section_start + offset
        if address + 7 + displacement == target:
            matches.append(address)

    return matches


def require_markers(text: str, markers: tuple[str, ...], source: Path) -> None:
    missing = [marker for marker in markers if marker not in text]
    if missing:
        raise SystemExit(f"{source} is missing markers: {missing}")


def read_u64(binary: lief.MachO.Binary, address: int) -> int:
    for section in binary.sections:
        start = section.virtual_address
        if start <= address and address + 8 <= start + section.size:
            offset = address - start
            return struct.unpack_from("<Q", bytes(section.content), offset)[0]
    raise SystemExit(f"address 0x{address:x} is not backed by section data")


def audit() -> dict[str, object]:
    macho_sha256 = sha256(MACHO)
    if macho_sha256 != EXPECTED_MACHO_SHA256:
        raise SystemExit(f"unexpected Rekordbox Mach-O hash: {macho_sha256}")
    source_sha256 = sha256(CLIENT_SOURCE)
    if source_sha256 != EXPECTED_CLIENT_SOURCE_SHA256:
        raise SystemExit(f"unexpected CDJ-3000 source hash: {source_sha256}")

    fat = lief.MachO.parse(str(MACHO))
    binary = next(
        item
        for item in fat
        if item.header.cpu_type == lief.MachO.Header.CPU_TYPE.X86_64
    )
    text = binary.get_section("__text")
    if text is None:
        raise SystemExit("binary has no __text section")
    addresses = symbol_addresses(binary)
    all_text_symbols = sorted(
        symbol.value
        for symbol in binary.symbols
        if text.virtual_address <= symbol.value < text.virtual_address + text.size
    )

    def symbol_end(label: str) -> int:
        start = addresses[label]
        return next(address for address in all_text_symbols if address > start)

    name_literal = literal_address(binary, b"djprofile.nxs\0")
    ui_start = addresses["UiProDJLink::run"]
    ui_end = symbol_end("UiProDJLink::run")
    init_start = addresses["Kuvo static initializer"]
    init_end = symbol_end("Kuvo static initializer")
    calls = {
        label: direct_call_addresses(text, ui_start, ui_end, addresses[label])
        for label in (
            "KuvoService::nxsFile",
            "KuvoService::isValid",
            "PSvDBServer::Start",
        )
    }
    if [len(calls[label]) for label in calls] != [1, 1, 2]:
        raise SystemExit(f"unexpected UiProDJLink call counts: {calls}")
    initializer_refs = {
        "nxs_name_object": rip_lea_addresses(
            text, init_start, init_end, addresses["KuvoService::nxsName"]
        ),
        "djprofile_nxs_literal": rip_lea_addresses(
            text, init_start, init_end, name_literal
        ),
    }
    if [len(value) for value in initializer_refs.values()] != [1, 1]:
        raise SystemExit(f"unexpected Kuvo initializer references: {initializer_refs}")
    vptr = addresses["juce::FileInputStream vtable"] + 0x10
    checksum_readers = {
        "offset_0_vptr_slot_0x48": read_u64(binary, vptr + 0x48),
        "offsets_4_8_12_28_vptr_slot_0x50": read_u64(binary, vptr + 0x50),
    }
    expected_readers = {
        "offset_0_vptr_slot_0x48": addresses["juce::InputStream::readInt"],
        "offsets_4_8_12_28_vptr_slot_0x50": addresses[
            "juce::InputStream::readIntBigEndian"
        ],
    }
    if checksum_readers != expected_readers:
        raise SystemExit(f"unexpected checksum readers: {checksum_readers}")

    disassembly = DISASSEMBLY.read_text()
    require_markers(
        disassembly,
        (
            "cmp       eax, 0x3006",
            "mov       edx, 0x4d02",
            "mov       edi, 0xa0",
            "mov       r8d, 0xa0",
            "mov       qword ptr [rbx + 0x5e8], rax",
            "vmovups   ymmword ptr [rax], ymm0",
            "Application Support/Pioneer",
            "rekordbox6",
            "cmp       rax, 0xa0",
        ),
        DISASSEMBLY,
    )
    command_parser = COMMAND_PARSER.read_text()
    require_markers(
        command_parser,
        (
            "cmp       eax, 0x4d02",
            "mov       dword ptr [rdi + 7], 0x6060604",
            "mov       byte ptr [rdi + 0xb], 3",
            "mov       eax, 4",
        ),
        COMMAND_PARSER,
    )
    client_text = CLIENT_SOURCE.read_text()
    require_markers(
        client_text,
        (
            "3006 CMD_GET_USER_INFO [context]",
            "4d02 CMD_RET_USER_INFO [3006, 0, 0xa0, blob(160)]",
            "2602 CMD_GET_DELIVERY_INFO [context, track id]",
            "retried twice",
            "about eighteen seconds",
        ),
        CLIENT_SOURCE,
    )

    return {
        "format": 1,
        "scope": "Rekordbox 7.2.19 user-info/DJ-ID server path and CDJ-3000 post-load client chain",
        "sources": {
            "rekordbox_macho": {
                "path": relative(MACHO),
                "sha256": macho_sha256,
                "architecture": "x86_64",
            },
            "rekordbox_disassembly": {
                "path": relative(DISASSEMBLY),
                "sha256": sha256(DISASSEMBLY),
            },
            "command_format_disassembly": {
                "path": relative(COMMAND_PARSER),
                "sha256": sha256(COMMAND_PARSER),
            },
            "cdj_3000_client": {
                "path": relative(CLIENT_SOURCE),
                "sha256": source_sha256,
                "firmware": "3.20 build 14970",
                "rekordbox_capture_version": "7.2.11",
            },
        },
        "symbols": {label: f"0x{address:x}" for label, address in addresses.items()},
        "static_initialization": {
            "filename": "djprofile.nxs",
            "filename_literal_address": f"0x{name_literal:x}",
            "initializer_references": {
                label: [f"0x{address:x}" for address in values]
                for label, values in initializer_refs.items()
            },
            "macos_path": "<user Application Support>/Pioneer/rekordbox6/djprofile.nxs",
        },
        "server_startup": {
            "ui_call_sites": {
                label: [f"0x{address:x}" for address in values]
                for label, values in calls.items()
            },
            "file_validation": {
                "exists_as_file": True,
                "case_folded_extension": ".nxs",
                "exact_bytes": 160,
                "checksum": (
                    "big-endian u32 at offset 28 equals the modulo-2^32 sum of "
                    "little-endian u32 at offset 0 and big-endian u32 values at "
                    "offsets 4, 8, and 12"
                ),
                "checksum_reader_vtable_targets": {
                    label: f"0x{address:x}"
                    for label, address in checksum_readers.items()
                },
            },
            "loaded_state": "first 32 file bytes copied into PSvDBMain member +0x5e8",
            "absent_or_invalid_state": "PSvDBMain member +0x5e8 remains null",
        },
        "wire_contract": {
            "request": {
                "kind": "0x3006",
                "name": "CMD_GET_USER_INFO",
                "arguments_from_cdj_3000": ["context"],
            },
            "success_reply": {
                "kind": "0x4d02",
                "name": "CMD_RET_USER_INFO",
                "arguments": ["0x3006", 0, 160, "blob(160)"],
                "blob": "first 32 bytes are the DJ ID; remaining 128 bytes are zero",
            },
            "absent_reply": {
                "kind": "0x4d02",
                "name": "CMD_RET_USER_INFO",
                "arguments": ["0x3006", 0, 0, "blob(0)"],
                "blob": "zero-length blob field",
            },
            "unknown_user_command_result": "0xfffffffe",
        },
        "cdj_3000_post_load_chain": [
            "0x3006 user info -> 0x4d02",
            "0x2602 delivery info -> 0x4000 count",
            "0x3000 render -> 0x4001/0x4101*/0x4201",
        ],
        "client_failure_semantics": {
            "missing_reply": "about 18 seconds to first timeout, then two retries; later browsing can be serialized behind the ticket",
            "unsupported_reply_0x4003": "finishes the ticket cleanly",
            "short_or_length_mismatched_0x4d02": "logs a parameter error and continues to delivery info",
        },
        "evidence_boundary": (
            "The server construction and configuration path are static Rekordbox 7.2.19 "
            "evidence. The request shape and player lifecycle are CDJ-3000 firmware evidence "
            "cross-checked there against Rekordbox 7.2.11. A live 7.2.19 oracle remains required "
            "for actual reply serialization, argument-boundary behavior, and controlled valid/invalid "
            "djprofile.nxs states."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.write_text(json.dumps(audit(), indent=2) + "\n")


if __name__ == "__main__":
    main()
