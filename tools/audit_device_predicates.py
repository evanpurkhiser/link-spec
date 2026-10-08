#!/usr/bin/env python3
"""Inventory direct callers of Link Export device-identity predicates."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from bisect import bisect_right
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import lief
from capstone import CS_ARCH_ARM64, CS_ARCH_X86, CS_MODE_64, CS_MODE_ARM, Cs
from capstone.arm64 import ARM64_OP_IMM
from capstone.x86 import X86_OP_IMM


EXPECTED_SHA256 = "07dcecbaf304f777e435539c83c7dcc02e41de1eaf2e0a75e8a9852e4411a244"


@dataclass(frozen=True)
class Target:
    name: str
    symbol: str
    group: str
    relevance: str


TARGETS = (
    Target(
        "receive-link-member-inner",
        "__ZN12InnerLinkAPI17receiveLinkMemberEjPKv",
        "identity-ingress",
        "Parses the link-member payload before notifying ProDJLink.",
    ),
    Target(
        "detect-link-device-inner",
        "__ZN12InnerLinkAPI16detectLinkDeviceEh",
        "identity-ingress",
        "Notifies the application that a link device is available.",
    ),
    Target(
        "receive-link-member",
        "__ZN9prodjlink9ProDJLink17receiveLinkMemberEjN13PSvLinkCommon17PSvLinkDeviceTypeEb",
        "identity-ingress",
        "Carries the decoded device type into LinkDeviceManager.",
    ),
    Target(
        "add-link-device",
        "__ZN9prodjlink17LinkDeviceManager13addLinkDeviceEjN13PSvLinkCommon"
        "17PSvLinkDeviceTypeEbNS1_13PSvLinkTimeSCEPKhS5_S5_",
        "identity-ingress",
        "Stores device type and presence state for a discovered peer.",
    ),
    Target(
        "get-member-info-inner",
        "__ZN12InnerLinkAPI13getMemberInfoEjRN13PSvLinkCommon13PSvLinkTimeSCEPhS3_",
        "identity-accessor",
        "Network-layer member timing and flag accessor.",
    ),
    Target(
        "get-member-info-proxy",
        "__ZN9prodjlink9LinkProxy13getMemberInfoEjRN13PSvLinkCommon13PSvLinkTimeSCEPhS4_",
        "identity-accessor",
        "Proxy member-state accessor used during link-member receipt.",
    ),
    Target(
        "get-model-name-inner",
        "__ZN12InnerLinkAPI12getModelNameEj",
        "model-accessor",
        "Network-layer model-name accessor.",
    ),
    Target(
        "get-model-name-inner-buffer",
        "__ZN12InnerLinkAPI12getModelNameEjPcj",
        "model-accessor",
        "Network-layer buffer model-name accessor.",
    ),
    Target(
        "get-model-name-network",
        "__ZN20PSvLinkNetworkAccess12getModelNameEj",
        "model-accessor",
        "Link-network model-name wrapper.",
    ),
    Target(
        "get-model-name-network-buffer",
        "__ZN20PSvLinkNetworkAccess12getModelNameEjPcj",
        "model-accessor",
        "Link-network buffer model-name wrapper.",
    ),
    Target(
        "get-model-name-interval",
        "__ZN21PSvLinkNormalInterval12getModelNameEj",
        "model-accessor",
        "Keepalive-state model-name accessor.",
    ),
    Target(
        "get-model-name-interval-buffer",
        "__ZN21PSvLinkNormalInterval12getModelNameEjPcj",
        "model-accessor",
        "Keepalive-state buffer model-name accessor.",
    ),
    Target(
        "get-model-name",
        "__ZN9prodjlink9ProDJLink12getModelNameEi",
        "model-accessor",
        "Application-facing model-name accessor.",
    ),
    Target(
        "get-model-names",
        "__ZN9prodjlink9ProDJLink13getModelNamesERN4juce11StringArrayE",
        "model-accessor",
        "Enumerates model names for application UI.",
    ),
    Target(
        "is-specific-model",
        "__ZN9prodjlink9ProDJLink15isSpecificModelEiPKc",
        "model-predicate",
        "Compares one player's model name with a literal model.",
    ),
    Target(
        "is-cdj-network",
        "__ZN9prodjlink9ProDJLink12isCDJNetworkEv",
        "model-predicate",
        "Reports whether the connected network has a CDJ-class peer.",
    ),
    Target(
        "is-aio",
        "__ZN9PSvDBMain5isAIOEh",
        "database-serving-predicate",
        "Caches an XDJ-prefix classification used by Display Song Info.",
    ),
    Target(
        "clear-aio-map",
        "__ZN9PSvDBMain11clearAIOMapEh",
        "database-serving-lifecycle",
        "Clears a player's cached AIO classification on disconnect.",
    ),
    Target(
        "new-cdj-supported",
        "__Z30DsqlContent_GetNewCDJSupportedj",
        "row-compatibility-predicate",
        "Computes per-track compatibility state consumed by track rows.",
    ),
    Target(
        "support-my-setting",
        "__ZN21PSvLinkNormalInterval18isSupportMysettingEh",
        "device-setting-predicate",
        "Gates My Settings network messages.",
    ),
    Target(
        "support-duplication-v2",
        "__ZN21PSvLinkNormalInterval22isSupportDuplicationv2Eh",
        "device-setting-predicate",
        "Gates My Settings duplication version 2.",
    ),
    Target(
        "support-device-setting",
        "__ZN21PSvLinkNormalInterval22isSupportDeviceSettingEh",
        "device-setting-predicate",
        "Gates device-setting network messages.",
    ),
    Target(
        "set-deck-aio",
        "__ZN23PSvLinkDDIndicationInfo10setDeckAIOEj",
        "drag-drop-output",
        "Serializes the AIO deck form for drag-and-drop play.",
    ),
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def owner_scope(symbol: str) -> str:
    if any(marker in symbol for marker in ("PSvDBMain", "PSvAppSyncDBIF", "PSvMasterDBIF", "Dsql", "dsql")):
        return "database-serving"
    if any(marker in symbol for marker in ("InnerLinkAPI", "PSvLink", "prodjlink", "LinkDeviceManager")):
        return "link-plumbing"
    ui_markers = (
        "djplay",
        "browse",
        "UiProDJLink",
        "Widget",
        "RemoteSetting",
        "DJSystemRemote",
    )
    if any(marker in symbol for marker in ui_markers):
        return "application-ui"
    return "other"


def x86_branch_candidates(content: bytes, base: int, targets: set[int]):
    for opcode, mnemonic in ((0xE8, "call"), (0xE9, "jmp")):
        cursor = 0
        while (offset := content.find(bytes((opcode,)), cursor)) != -1:
            cursor = offset + 1
            if offset + 5 > len(content):
                continue
            displacement = struct.unpack_from("<i", content, offset + 1)[0]
            address = base + offset
            target = address + 5 + displacement
            if target in targets:
                yield address, mnemonic, target, offset


def arm64_branch_candidates(content: bytes, base: int, targets: set[int]):
    for offset in range(0, len(content) - 3, 4):
        instruction = struct.unpack_from("<I", content, offset)[0]
        opcode = instruction & 0xFC000000
        if opcode not in (0x14000000, 0x94000000):
            continue

        immediate = instruction & 0x03FFFFFF
        if immediate & 0x02000000:
            immediate -= 0x04000000
        address = base + offset
        target = address + immediate * 4
        if target in targets:
            yield address, "bl" if opcode == 0x94000000 else "b", target, offset


def is_instruction(
    disassembler: Cs,
    content: bytes,
    base: int,
    owner: int,
    offset: int,
    mnemonic: str,
    target: int,
    immediate_type: int,
) -> bool:
    owner_offset = owner - base
    instructions = disassembler.disasm(content[owner_offset:min(offset + 15, len(content))], owner)
    instruction = next((item for item in instructions if item.address == base + offset), None)
    return bool(
        instruction
        and instruction.mnemonic == mnemonic
        and instruction.operands
        and instruction.operands[0].type == immediate_type
        and instruction.operands[0].imm == target
    )


def audit(binary_path: Path, architecture: str = "x86_64") -> dict[str, object]:
    binary_path = binary_path.resolve(strict=True)
    binary_hash = sha256(binary_path)
    if binary_hash != EXPECTED_SHA256:
        raise SystemExit(f"unexpected binary SHA-256: {binary_hash}")

    fat = lief.MachO.parse(str(binary_path))
    cpu_type = {
        "x86_64": lief.MachO.Header.CPU_TYPE.X86_64,
        "arm64": lief.MachO.Header.CPU_TYPE.ARM64,
    }[architecture]
    binary = next(item for item in fat if item.header.cpu_type == cpu_type)
    section = binary.get_section("__text")
    if section is None:
        raise SystemExit("binary has no __text section")

    content = bytes(section.content)
    start = section.virtual_address
    end = start + len(content)
    names: dict[int, list[str]] = defaultdict(list)
    symbol_addresses: dict[str, int] = {}
    for symbol in binary.symbols:
        if symbol.value and symbol.name:
            symbol_addresses.setdefault(symbol.name, symbol.value)
            if start <= symbol.value < end and symbol.name not in names[symbol.value]:
                names[symbol.value].append(symbol.name)

    missing = [target.symbol for target in TARGETS if target.symbol not in symbol_addresses]
    if missing:
        raise SystemExit("missing target symbols: " + ", ".join(missing))

    by_address = {symbol_addresses[target.symbol]: target for target in TARGETS}
    addresses = sorted(names)
    disassembler = {
        "x86_64": Cs(CS_ARCH_X86, CS_MODE_64),
        "arm64": Cs(CS_ARCH_ARM64, CS_MODE_ARM),
    }[architecture]
    disassembler.detail = True
    candidates = {
        "x86_64": x86_branch_candidates,
        "arm64": arm64_branch_candidates,
    }[architecture]
    immediate_type = {
        "x86_64": X86_OP_IMM,
        "arm64": ARM64_OP_IMM,
    }[architecture]
    xrefs: dict[int, list[dict[str, object]]] = defaultdict(list)
    for address, mnemonic, destination, offset in sorted(candidates(content, start, set(by_address))):
        index = bisect_right(addresses, address) - 1
        owner_address = addresses[index] if index >= 0 else 0
        valid = owner_address and is_instruction(
            disassembler,
            content,
            start,
            owner_address,
            offset,
            mnemonic,
            destination,
            immediate_type,
        )
        if not valid:
            continue
        owner_names = names.get(owner_address, ["<unknown>"])
        xrefs[destination].append({
            "address": f"{address:#x}",
            "branch": mnemonic,
            "owner_address": f"{owner_address:#x}",
            "owner_symbols": owner_names,
            "owner_scope": owner_scope(" ".join(owner_names)),
        })

    targets = []
    for target in TARGETS:
        address = symbol_addresses[target.symbol]
        callers = xrefs.get(address, [])
        targets.append({
            "id": target.name,
            "address": f"{address:#x}",
            "symbol": target.symbol,
            "group": target.group,
            "relevance": target.relevance,
            "direct_reference_count": len(callers),
            "direct_references": callers,
            "database_serving_reference_count": sum(item["owner_scope"] == "database-serving" for item in callers),
        })

    direct_reference_count = sum(item["direct_reference_count"] for item in targets)
    database_reference_count = sum(
        item["database_serving_reference_count"] for item in targets
    )

    return {
        "format": "rekordbox-link-export-device-predicate-audit-v1",
        "binary": {"path": str(binary_path), "sha256": binary_hash, "architecture": architecture},
        "method": {
            "branch_kinds": {
                "x86_64": ["direct rel32 call", "direct rel32 jump"],
                "arm64": ["direct BL immediate", "direct B immediate"],
            }[architecture],
            "instruction_validation": "linear disassembly from owning symbol",
            "limits": [
                "indirect calls",
                "vtables",
                "function pointers",
                "inlined predicates",
                {
                    "x86_64": "arm64-only behavior",
                    "arm64": "x86_64-only behavior",
                }[architecture],
            ],
        },
        "excluded_symbol_families": [
            "djplay::DeviceDefs audio/HID/MIDI controller classification",
            "removable-storage and database-device classification",
            "rendering and audio-device type predicates",
        ],
        "summary": {
            "target_count": len(targets),
            "direct_reference_count": direct_reference_count,
            "database_serving_reference_count": database_reference_count,
        },
        "targets": targets,
    }


def render_markdown(report: dict[str, object]) -> str:
    targets = report["targets"]
    architecture = {
        "x86_64": "x86-64",
        "arm64": "ARM64",
    }[report["binary"]["architecture"]]
    lines = [
        "# Device predicate direct-reference audit",
        "",
        f"This generated report inventories direct {architecture} callers of every selected",
        "Pro DJ Link identity, model, capability, and row-compatibility helper that",
        "can plausibly affect Link Export. The JSON companion preserves every call site.",
        "",
        f"Binary SHA-256: `{report['binary']['sha256']}`.",
        f"Targets: {report['summary']['target_count']}; validated direct references: "
        f"{report['summary']['direct_reference_count']}; database-serving references: "
        f"{report['summary']['database_serving_reference_count']}.",
        "",
        "| Helper | Group | Direct refs | DB-serving refs |",
        "| --- | --- | ---: | ---: |",
    ]
    for item in targets:
        lines.append(
            f"| `{item['id']}` (`{item['address']}`) | {item['group']} | "
            f"{item['direct_reference_count']} | {item['database_serving_reference_count']} |"
        )

    lines.extend(["", "## Database-serving references", ""])
    database_refs = [
        (item, reference)
        for item in targets
        for reference in item["direct_references"]
        if reference["owner_scope"] == "database-serving"
    ]
    for item, reference in database_refs:
        owners = "`, `".join(reference["owner_symbols"])
        lines.append(
            f"- `{item['id']}` <- `{owners}` at `{reference['address']}` "
            f"({reference['branch']})."
        )
    if not database_refs:
        lines.append("No direct database-serving references were found.")

    lines.extend(["", "## Caller scopes", ""])
    for item in targets:
        counts: dict[str, int] = defaultdict(int)
        for reference in item["direct_references"]:
            counts[reference["owner_scope"]] += 1
        rendered = ", ".join(f"{scope}={count}" for scope, count in sorted(counts.items())) or "none"
        lines.append(f"- `{item['id']}`: {rendered}. {item['relevance']}")

    lines.extend([
        "",
        "## Boundary",
        "",
        f"This scan proves direct references in the pinned {architecture} text slice. It does",
        "not exclude indirect calls, vtables, function pointers, inlining, cached state",
        "written by another path, or architecture-specific behavior. Audio/HID/MIDI",
        "controller classification and removable-storage classification are separate",
        "subsystems and are excluded from this Link Export peer-identity inventory.",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("binary", type=Path)
    parser.add_argument("--architecture", choices=("x86_64", "arm64"), default="x86_64")
    parser.add_argument("--json", type=Path, required=True)
    parser.add_argument("--markdown", type=Path, required=True)
    args = parser.parse_args()

    report = audit(args.binary, args.architecture)
    args.json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    args.markdown.write_text(render_markdown(report))
    print(
        f"audited {report['summary']['target_count']} device predicates/accessors; "
        f"validated {report['summary']['direct_reference_count']} direct references"
    )


if __name__ == "__main__":
    main()
