#!/usr/bin/env python3
"""Audit provider ownership behind Link Export streaming-path filtering."""

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
OUTPUT = ROOT / "data/static-analysis/streaming-provider-registry.json"
DISASSEMBLY = ROOT / "data/static-analysis/streaming-provider-registry.disasm.txt"
EXPECTED_SHA256 = "07dcecbaf304f777e435539c83c7dcc02e41de1eaf2e0a75e8a9852e4411a244"

SYMBOLS = {
    "manager_constructor": "__ZN9streaming16StreamingManagerC2Ev",
    "manager_get_service": "__ZN9streaming16StreamingManager19getStreamingServiceENS_13StreamingTypeE",
    "manager_classify": "__ZN9streaming16StreamingManager19isStreamingProtocolERKN4juce6StringE",
    "global_classify": "__ZN9streaming19isStreamingProtocolERKN4juce6StringE",
    "manager_logged_in": "__ZN9streaming16StreamingManager19isStreamingLoggedInENS_13StreamingTypeE",
    "beatsource_classify": "__ZN9streaming20isBeatsourceProtocolERKN4juce6StringE",
    "soundcloud_constructor": "__ZN9streaming17SoundCloudServiceC1Ev",
    "beatport_constructor": "__ZN9streaming15BeatportServiceC1Ev",
    "tidal_constructor": "__ZN9streaming5tidal7ServiceC1Ev",
    "spotify_constructor": "__ZN9streaming7spotify7ServiceC1Ev",
    "apple_music_constructor": "__ZN9streaming11apple_music7ServiceC1Ev",
    "beatport_vtable": "__ZTVN9streaming15BeatportServiceE",
    "string_contains": "__ZNK4juce6String8containsENS_9StringRefE",
}

PROVIDERS = [
    (1, "SoundCloud", 0x08, "soundcloud_constructor"),
    (2, "Beatport", 0x10, "beatport_constructor"),
    (3, "Beatsource", 0x18, None),
    (4, "Tidal", 0x20, "tidal_constructor"),
    (5, "provider-5", 0x28, None),
    (6, "provider-6", 0x30, None),
    (7, "Spotify", 0x38, "spotify_constructor"),
    (8, "Apple Music", 0x40, "apple_music_constructor"),
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def x86_binary() -> tuple[lief.MachO.FatBinary, lief.MachO.Binary]:
    if sha256(MACHO) != EXPECTED_SHA256:
        raise SystemExit("unexpected Rekordbox 7.2.19 Mach-O hash")

    fat = lief.MachO.parse(str(MACHO))
    binary = next(
        binary
        for binary in fat
        if binary.header.cpu_type == lief.MachO.Header.CPU_TYPE.X86_64
    )
    return fat, binary


def addresses(binary: lief.MachO.Binary) -> dict[str, int]:
    by_name = {symbol.name: symbol.value for symbol in binary.symbols if symbol.value}
    missing = [symbol for symbol in SYMBOLS.values() if symbol not in by_name]
    if missing:
        raise SystemExit(f"missing symbols: {', '.join(missing)}")

    return {label: by_name[symbol] for label, symbol in SYMBOLS.items()}


def decode(binary: lief.MachO.Binary, start: int, size: int):
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    decoder.detail = True
    raw = bytes(binary.get_content_from_virtual_address(start, size))
    return list(decoder.disasm(raw, start))


def direct_calls(instructions) -> dict[int, list[int]]:
    calls: dict[int, list[int]] = {}
    for instruction in instructions:
        if instruction.mnemonic != "call" or not instruction.operands:
            continue
        operand = instruction.operands[0]
        if operand.type != X86_OP_IMM:
            continue
        calls.setdefault(operand.imm, []).append(instruction.address)
    return calls


def literal_addresses(binary: lief.MachO.Binary, value: bytes) -> list[int]:
    result = []
    for section in binary.sections:
        content = bytes(section.content)
        cursor = 0
        while (offset := content.find(value, cursor)) != -1:
            result.append(section.virtual_address + offset)
            cursor = offset + 1
    return result


def rip_targets(instructions) -> set[int]:
    result = set()
    for instruction in instructions:
        for operand in instruction.operands:
            if operand.type == X86_OP_MEM and operand.mem.base == X86_REG_RIP:
                result.add(instruction.address + instruction.size + operand.mem.disp)
    return result


def read_u64(binary: lief.MachO.Binary, address: int) -> int:
    raw = bytes(binary.get_content_from_virtual_address(address, 8))
    return struct.unpack("<Q", raw)[0]


def rendered_disassembly(
    groups: list[tuple[str, int, list]], by_address: dict[int, list[str]]
) -> str:
    output = [
        f"Pinned binary SHA-256: {EXPECTED_SHA256}",
        "Generated with tools/audit_streaming_provider_registry.py.",
        "",
    ]
    for label, start, instructions in groups:
        output.extend((f"## {label}", f"address={start:#x}"))
        for instruction in instructions:
            annotations = []
            for operand in instruction.operands:
                if operand.type == X86_OP_IMM and instruction.mnemonic.startswith(("call", "j")):
                    annotations.extend(by_address.get(operand.imm, []))
                elif operand.type == X86_OP_MEM and operand.mem.base == X86_REG_RIP:
                    target = instruction.address + instruction.size + operand.mem.disp
                    annotations.extend(by_address.get(target, []))
            suffix = f"  ; {' | '.join(dict.fromkeys(annotations))}" if annotations else ""
            output.append(
                f"{instruction.address:#012x}  {instruction.mnemonic:<9} "
                f"{instruction.op_str}{suffix}".rstrip()
            )
        output.append("")
    return "\n".join(output) + "\n"


def audit() -> tuple[dict[str, object], str]:
    fat, binary = x86_binary()
    resolved = addresses(binary)
    by_address: dict[int, list[str]] = {}
    for symbol in binary.symbols:
        if symbol.value and symbol.name:
            by_address.setdefault(symbol.value, []).append(symbol.name)

    constructor = decode(binary, resolved["manager_constructor"], 0x43A)
    constructor_calls = direct_calls(constructor)
    for _, _, _, constructor_label in PROVIDERS:
        if constructor_label is None:
            continue
        if len(constructor_calls.get(resolved[constructor_label], [])) != 1:
            raise SystemExit(f"unexpected {constructor_label} constructor call count")

    constructor_text = "\n".join(
        f"{instruction.mnemonic} {instruction.op_str}" for instruction in constructor
    )
    populated_slot_markers = {
        0x08: "qword ptr [r13], rbx",
        0x10: "qword ptr [r12 + 0x10], rbx",
        0x20: "qword ptr [r12 + 0x20], rbx",
        0x38: "qword ptr [r12 + 0x38], rbx",
        0x40: "qword ptr [r12 + 0x40], rbx",
    }
    for offset, marker in populated_slot_markers.items():
        if marker not in constructor_text:
            raise SystemExit(f"constructor does not populate provider slot {offset:#x}")
    for offset in (0x18, 0x28, 0x30):
        if f"qword ptr [r12 + {offset:#x}], rbx" in constructor_text:
            raise SystemExit(f"constructor unexpectedly populates provider slot {offset:#x}")

    manager_classify = decode(binary, resolved["manager_classify"], 0xA8)
    global_classify = decode(binary, resolved["global_classify"], 0xEE)
    manager_logged_in = decode(binary, resolved["manager_logged_in"], 0x7D)
    beatsource_classify = decode(binary, resolved["beatsource_classify"], 0x0F)

    beatport_vptr = resolved["beatport_vtable"] + 0x10
    beatport_protocol = read_u64(binary, beatport_vptr + 0x30)
    beatport_instructions = decode(binary, beatport_protocol, 0x2C)
    beatport_calls = direct_calls(beatport_instructions)
    if len(beatport_calls.get(resolved["string_contains"], [])) != 1:
        raise SystemExit("Beatport protocol predicate does not call String::contains once")
    prefix_matches = literal_addresses(binary, b"/v4/catalog/tracks/\0")
    if len(prefix_matches) != 1 or prefix_matches[0] not in rip_targets(beatport_instructions):
        raise SystemExit("Beatport protocol predicate is not bound to its catalog prefix")

    beatsource_text = [(item.mnemonic, item.op_str) for item in beatsource_classify]
    if ("xor", "eax, eax") not in beatsource_text or beatsource_text[-1][0] != "ret":
        raise SystemExit("Beatsource classifier is not the constant-false implementation")

    classified_offsets = (0x08, 0x10, 0x20, 0x38, 0x40)
    manager_text = "\n".join(item.op_str for item in manager_classify)
    for offset in classified_offsets:
        spelling = "8" if offset == 8 else f"{offset:#x}"
        if f"[r" not in manager_text or spelling not in manager_text:
            raise SystemExit(f"manager classifier lacks slot {offset:#x}")

    groups = [
        ("streaming::StreamingManager::StreamingManager", resolved["manager_constructor"], constructor),
        ("streaming::StreamingManager::isStreamingProtocol", resolved["manager_classify"], manager_classify),
        ("streaming::isStreamingProtocol", resolved["global_classify"], global_classify),
        ("streaming::StreamingManager::isStreamingLoggedIn", resolved["manager_logged_in"], manager_logged_in),
        ("streaming::isBeatsourceProtocol", resolved["beatsource_classify"], beatsource_classify),
        ("BeatportService protocol predicate", beatport_protocol, beatport_instructions),
    ]
    document = {
        "format": 1,
        "scope": "Rekordbox 7.2.19 x86-64 streaming-provider ownership used by Link Export row visibility",
        "source": {
            "path": str(MACHO.resolve().relative_to(ROOT.parent.resolve())),
            "sha256": EXPECTED_SHA256,
            "architecture": "x86_64",
        },
        "manager": {
            "constructor": f"{resolved['manager_constructor']:#x}",
            "get_service": f"{resolved['manager_get_service']:#x}",
            "path_classifier": f"{resolved['manager_classify']:#x}",
            "global_path_classifier": f"{resolved['global_classify']:#x}",
            "login_classifier": f"{resolved['manager_logged_in']:#x}",
            "providers": [
                {
                    "type": provider_type,
                    "name": name,
                    "slot": f"{offset:#x}",
                    "constructed": constructor_label is not None,
                    "constructor": (
                        f"{resolved[constructor_label]:#x}" if constructor_label else None
                    ),
                    "used_by_generic_path_classifier": offset in classified_offsets,
                }
                for provider_type, name, offset, constructor_label in PROVIDERS
            ],
        },
        "beatport_path_predicate": {
            "service_slot": "0x10",
            "method_vtable_offset": "0x30",
            "method_address": f"{beatport_protocol:#x}",
            "operation": "juce::String::contains",
            "substring": "/v4/catalog/tracks/",
            "login_state_read": False,
            "fixture_scheme_beatport_tracks_matches": False,
        },
        "beatsource_path_predicate": {
            "service_slot": "0x18",
            "service_constructed": False,
            "standalone_helper": f"{resolved['beatsource_classify']:#x}",
            "standalone_result": False,
            "fixture_scheme_beatsource_tracks_matches": False,
        },
        "link_export_implications": [
            "The generic path classifier and the login classifier are separate functions.",
            "Beatport is constructed unconditionally and tested by the generic path classifier.",
            "Beatport path recognition is a pure /v4/catalog/tracks/ substring test in this build.",
            "The beatport:tracks: fixture control does not exercise the production Beatport predicate.",
            "Beatsource has a reserved type/slot but no constructed service and its standalone helper returns false.",
            "Authenticating Beatport is not required to activate its Link Export path predicate.",
        ],
        "evidence_boundary": {
            "proven": "macOS x86-64 manager construction and predicates",
            "live_windows_follow_up": "Record ordinary serving with /v4/catalog/tracks/ and scheme controls",
            "not_claimed": "Account-conditioned root UI or behavior in other Rekordbox versions",
        },
    }
    return document, rendered_disassembly(groups, by_address)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--disassembly-output", type=Path, default=DISASSEMBLY)
    args = parser.parse_args()

    document, disassembly = audit()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(document, indent=2) + "\n")
    args.disassembly_output.write_text(disassembly)
    print(f"wrote {args.output} and {args.disassembly_output}")


if __name__ == "__main__":
    main()
