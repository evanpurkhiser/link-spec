#!/usr/bin/env python3
"""Audit the settings and helpers controlling Play Song Info cloud paths."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

import lief
from capstone import CS_ARCH_X86, CS_MODE_64, Cs
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_REG_RIP


ROOT = Path(__file__).resolve().parent.parent
MACHO = (
    ROOT.parent
    / "artifacts/rekordbox/7.2.19/extracted/app-root/rekordbox.app/Contents/MacOS/rekordbox"
)
OUTPUT = ROOT / "data/static-analysis/play-song-info-cloud-paths.json"
DISASSEMBLY = ROOT / "data/static-analysis/play-song-info-cloud-paths.disasm.txt"
EXPECTED_SHA256 = "07dcecbaf304f777e435539c83c7dcc02e41de1eaf2e0a75e8a9852e4411a244"

SYMBOLS = {
    "play": "__ZN14PSvAppSyncDBIF14getPlaySongInfEjj",
    "sync_method": "__ZN14RekordboxCloud16getCLSSyncMethodEv",
    "share_path": "__ZN14RekordboxCloud9sharePathEi",
    "shared_path": "__ZL18getCloudSharedPathN12CloudManager9ServiceIdE",
    "download_path": "__ZN14RekordboxCloud18downloadFolderPathEi",
    "current_master_directory": "__ZN6djplay9SettingIF27getCurrentMasterDbDirectoryEv",
    "dropbox_public_path": "__ZN7DropBox15localPublicPathEv",
    "google_drive_public_path": "__ZN11GoogleDrive15localPublicPathEv",
    "onedrive_public_path": "__ZN8OneDrive15localPublicPathEv",
    "get_int": "__ZN6common11SettingFile11getIntValueEN4juce9StringRefEib",
    "exists": "__ZNK4juce4File6existsEv",
    "exists_as_file": "__ZNK4juce4File12existsAsFileEv",
}
SIZES = {
    "play": 0xF30,
    "sync_method": 0x80,
    "share_path": 0x80,
    "shared_path": 0x280,
    "download_path": 0x150,
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def x86_binary() -> tuple[lief.MachO.FatBinary, lief.MachO.Binary]:
    if sha256(MACHO) != EXPECTED_SHA256:
        raise SystemExit("unexpected Rekordbox 7.2.19 Mach-O hash")

    fat = lief.MachO.parse(str(MACHO))
    binary = next(
        item
        for item in fat
        if item.header.cpu_type == lief.MachO.Header.CPU_TYPE.X86_64
    )
    return fat, binary


def symbols(binary: lief.MachO.Binary) -> dict[str, int]:
    by_name = {
        symbol.name: (symbol.value, symbol.size)
        for symbol in binary.symbols
        if symbol.value
    }
    missing = [name for name in SYMBOLS.values() if name not in by_name]
    if missing:
        raise SystemExit(f"missing symbols: {', '.join(missing)}")

    return {label: by_name[name][0] for label, name in SYMBOLS.items()}


def decode(binary: lief.MachO.Binary, start: int, size: int):
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    decoder.detail = True
    raw = bytes(binary.get_content_from_virtual_address(start, size))
    return list(decoder.disasm(raw, start))


def direct_call_addresses(instructions, target: int) -> list[int]:
    return [
        instruction.address
        for instruction in instructions
        if instruction.mnemonic == "call"
        and instruction.operands
        and instruction.operands[0].type == X86_OP_IMM
        and instruction.operands[0].imm == target
    ]


def direct_rel32_call_addresses(
    binary: lief.MachO.Binary, target: int
) -> list[int]:
    section = next(
        section
        for section in binary.sections
        if section.segment_name == "__TEXT" and section.name == "__text"
    )
    raw = bytes(section.content)
    matches = []
    offset = raw.find(b"\xe8")

    while offset >= 0 and offset + 5 <= len(raw):
        address = section.virtual_address + offset
        displacement = struct.unpack_from("<i", raw, offset + 1)[0]
        if address + 5 + displacement == target:
            instruction = decode(binary, address, 5)
            if direct_call_addresses(instruction, target) == [address]:
                matches.append(address)

        offset = raw.find(b"\xe8", offset + 1)

    return matches


def literal_addresses(binary: lief.MachO.Binary, value: bytes) -> list[int]:
    matches = []
    for section in binary.sections:
        content = bytes(section.content)
        cursor = 0
        while (offset := content.find(value, cursor)) != -1:
            matches.append(section.virtual_address + offset)
            cursor = offset + 1
    return matches


def rip_targets(instructions) -> set[int]:
    return {
        instruction.address + instruction.size + operand.mem.disp
        for instruction in instructions
        for operand in instruction.operands
        if operand.type == X86_OP_MEM and operand.mem.base == X86_REG_RIP
    }


def instruction_text(instructions) -> str:
    return "\n".join(
        f"{instruction.mnemonic} {instruction.op_str}" for instruction in instructions
    )


def render(groups, annotations: dict[int, str]) -> str:
    lines = [
        f"Pinned binary SHA-256: {EXPECTED_SHA256}",
        "Generated with tools/audit_play_song_info_cloud_paths.py.",
        "",
    ]
    for title, address, instructions in groups:
        lines.extend((f"## {title}", f"address={address:#x}"))
        for instruction in instructions:
            notes = []
            for operand in instruction.operands:
                target = None
                if operand.type == X86_OP_IMM and instruction.mnemonic.startswith(("call", "j")):
                    target = operand.imm
                elif operand.type == X86_OP_MEM and operand.mem.base == X86_REG_RIP:
                    target = instruction.address + instruction.size + operand.mem.disp
                if target in annotations:
                    notes.append(annotations[target])
            suffix = f"  ; {' | '.join(dict.fromkeys(notes))}" if notes else ""
            lines.append(
                f"{instruction.address:#012x}  {instruction.mnemonic:<9} "
                f"{instruction.op_str}{suffix}".rstrip()
            )
        lines.append("")
    return "\n".join(lines)


def audit() -> tuple[dict[str, object], str]:
    fat, binary = x86_binary()
    resolved = symbols(binary)

    decoded = {
        label: decode(binary, resolved[label], size)
        for label, size in SIZES.items()
    }
    play = decoded["play"]
    getter = decoded["sync_method"]
    share = decoded["share_path"]
    shared = decoded["shared_path"]
    download = decoded["download_path"]

    key_matches = literal_addresses(binary, b"CLSSyncMethod\0")
    if len(key_matches) != 1 or key_matches[0] not in rip_targets(getter):
        raise SystemExit("sync-method accessor is not bound to CLSSyncMethod")
    if len(direct_call_addresses(getter, resolved["get_int"])) != 1:
        raise SystemExit("sync-method accessor does not read one integer setting")
    getter_text = instruction_text(getter)
    if "mov edx, 1" not in getter_text or "mov ecx, 1" not in getter_text:
        raise SystemExit("sync-method accessor default/required flags changed")

    sync_calls = direct_call_addresses(play, resolved["sync_method"])
    if sync_calls != [0x1016C1A79]:
        raise SystemExit(f"unexpected Play sync-method calls: {sync_calls!r}")
    binary_sync_calls = direct_rel32_call_addresses(binary, resolved["sync_method"])
    if binary_sync_calls != sync_calls:
        raise SystemExit(
            f"unexpected binary-wide sync-method calls: {binary_sync_calls!r}"
        )
    call_index = next(i for i, item in enumerate(play) if item.address == sync_calls[0])
    branch = play[call_index + 1 : call_index + 3]
    if [(item.mnemonic, item.op_str) for item in branch] != [
        ("test", "eax, eax"),
        ("je", "0x1016c1dc3"),
    ]:
        raise SystemExit("Play sync-method decision is not the expected zero test")

    if direct_call_addresses(play, resolved["share_path"]) != [0x1016C1A74]:
        raise SystemExit("Play does not resolve one share path before the branch")
    if direct_call_addresses(play, resolved["download_path"]) != [
        0x1016C1E3E,
        0x1016C1E64,
        0x1016C1ECB,
    ]:
        raise SystemExit("Play download-path call sites changed")
    if not direct_call_addresses(play, resolved["exists"]):
        raise SystemExit("Play zero branch lacks a general existence check")
    if not direct_call_addresses(play, resolved["exists_as_file"]):
        raise SystemExit("Play nonzero branch lacks a regular-file check")

    shared_text = instruction_text(shared)
    if "cmp ebx, 4" not in shared_text or "ja 0x100fddf02" not in shared_text:
        raise SystemExit("cloud shared-path service domain changed")
    jump_table_instruction = next(
        item for item in shared if item.address == 0x100FDDD97
    )
    jump_table = next(
        jump_table_instruction.address
        + jump_table_instruction.size
        + operand.mem.disp
        for operand in jump_table_instruction.operands
        if operand.type == X86_OP_MEM and operand.mem.base == X86_REG_RIP
    )
    jump_table_bytes = bytes(binary.get_content_from_virtual_address(jump_table, 20))
    jump_targets = [
        jump_table + offset for offset in struct.unpack("<5i", jump_table_bytes)
    ]
    expected_jump_targets = [
        0x100FDDF02,
        0x100FDDDA7,
        0x100FDDDF0,
        0x100FDDE47,
        0x100FDDE9B,
    ]
    if jump_table != 0x100FDDFCC or jump_targets != expected_jump_targets:
        raise SystemExit("cloud shared-path jump table changed")
    root_calls = {
        1: ("current_master_directory", 0x100FDDDB3),
        2: ("dropbox_public_path", 0x100FDDDF4),
        3: ("google_drive_public_path", 0x100FDDE4B),
        4: ("onedrive_public_path", 0x100FDDE9F),
    }
    for service_id, (label, call_address) in root_calls.items():
        calls = direct_call_addresses(shared, resolved[label])
        if calls != [call_address]:
            raise SystemExit(f"share-root service {service_id} call target changed")
    download_text = instruction_text(download)
    for marker in ("lea eax, [rbx - 2]", "cmp eax, 4", "test ebx, ebx"):
        if marker not in download_text:
            raise SystemExit(f"download-path service domain lacks {marker!r}")
    moved_key = literal_addresses(binary, b"MovedFromCloudDir\0")
    moved_default = literal_addresses(binary, b"PioneerDJ/Moved from Cloud\0")
    download_targets = rip_targets(download)
    if len(moved_key) != 1 or moved_key[0] not in download_targets:
        raise SystemExit("download path is not bound to MovedFromCloudDir")
    if len(moved_default) != 1 or moved_default[0] not in download_targets:
        raise SystemExit("download path lacks its PioneerDJ default child path")

    annotations = {
        address: SYMBOLS[label]
        for label, address in resolved.items()
    }
    annotations[key_matches[0]] = "CLSSyncMethod"
    groups = [
        ("RekordboxCloud::getCLSSyncMethod", resolved["sync_method"], getter),
        ("PSvAppSyncDBIF::getPlaySongInf", resolved["play"], play),
        ("RekordboxCloud::sharePath", resolved["share_path"], share),
        ("getCloudSharedPath", resolved["shared_path"], shared),
        ("RekordboxCloud::downloadFolderPath", resolved["download_path"], download),
    ]
    document = {
        "format": 1,
        "scope": "Rekordbox 7.2.19 x86-64 Play Song Info cloud-path selection",
        "source": {
            "path": str(MACHO.resolve().relative_to(ROOT.parent.resolve())),
            "sha256": EXPECTED_SHA256,
            "architecture": "x86_64",
        },
        "sync_method": {
            "setting": "CLSSyncMethod",
            "default": 1,
            "raw_integer_returned": True,
            "play_call": "0x1016c1a79",
            "binary_direct_call_sites": [
                {
                    "address": "0x1016c1a79",
                    "owner": "PSvAppSyncDBIF::getPlaySongInf",
                }
            ],
            "direct_call_scope": "the complete x86-64 __TEXT,__text section",
            "decision": "zero versus nonzero",
            "zero_target": "0x1016c1dc3",
            "nonzero_target": "0x1016c1a86",
            "equivalence_classes": [
                {"name": "zero", "values": [0]},
                {"name": "nonzero", "values": "every integer other than zero"},
            ],
        },
        "nonzero_branch": {
            "first_preference": "OrgFolderPath when local DBID equals MasterDBID and it exists as a regular file",
            "fallback": "share-path reconstruction and file checks",
            "download_folder_path_calls": 0,
        },
        "zero_branch": {
            "first_preference": "OrgFolderPath when it exists as any filesystem object",
            "fallback": "downloadFolderPath(ServiceID) reconstruction and existence checks",
            "download_folder_path_call_sites": [
                "0x1016c1e3e",
                "0x1016c1e64",
                "0x1016c1ecb",
            ],
        },
        "service_domains": {
            "share_path": {
                "switch_domain": "0 through 4",
                "jump_table_address": "0x100fddfcc",
                "jump_table_bytes": jump_table_bytes.hex(),
                "service_ids": [
                    {
                        "id": 0,
                        "target": "0x100fddf02",
                        "root": "empty string",
                    },
                    {
                        "id": 1,
                        "target": "0x100fddda7",
                        "owner": "djplay::SettingIF::getCurrentMasterDbDirectory",
                        "root": "current master-database directory + /share",
                    },
                    {
                        "id": 2,
                        "target": "0x100fdddf0",
                        "owner": "DropBox::localPublicPath",
                        "root": "Dropbox local public path + /rekordbox",
                    },
                    {
                        "id": 3,
                        "target": "0x100fdde47",
                        "owner": "GoogleDrive::localPublicPath",
                        "root": "Google Drive local public path + /rekordbox",
                    },
                    {
                        "id": 4,
                        "target": "0x100fdde9b",
                        "owner": "OneDrive::localPublicPath",
                        "root": "OneDrive local public path + /rekordbox",
                    },
                ],
                "outside_domain": "empty string",
                "requires_absolute_nonempty_result": True,
            },
            "download_folder_path": {
                "accepted_service_ids": [0, 2, 3, 4, 5],
                "outside_domain": "empty string",
                "setting": "MovedFromCloudDir",
                "default": {
                    "special_location": 3,
                    "child_path": "PioneerDJ/Moved from Cloud",
                    "normalization": "tools::UnifiedFilePath::toUnifiedFilePath",
                },
            },
        },
        "live_oracle_boundary": {
            "completed_equivalence_class": "nonzero (CLSSyncMethod=1)",
            "missing_equivalence_class": "zero (CLSSyncMethod=0)",
            "other_integer_values_needed": False,
        },
    }
    # Keep the FatBinary owner alive while LIEF-backed slice data is in use.
    assert fat is not None
    return document, render(groups, annotations)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--disassembly-output", type=Path, default=DISASSEMBLY)
    args = parser.parse_args()

    document, disassembly = audit()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.disassembly_output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(document, indent=2) + "\n")
    args.disassembly_output.write_text(disassembly)


if __name__ == "__main__":
    main()
