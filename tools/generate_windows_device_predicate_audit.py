#!/usr/bin/env python3
"""Generate the Windows device-predicate and compatibility ownership audit."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from analyze_windows_pe import (
    PeImage,
    find_absolute_pointers,
    find_direct_control_xrefs,
    render_code,
    render_function,
)


ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "data/static-analysis/windows"
EXPECTED_SHA256 = "c9ed23e974c51c75e2ec069fbd2679a3dbe606be9e79e9cbbd13d6418ab11c37"

FUNCTIONS = {
    "standalone_content_compatibility": 0x14227E200,
    "disconnect_with_inlined_aio_clear": 0x142380930,
    "display_is_aio": 0x1423815C0,
    "map_only_aio_clear_helper": 0x142381700,
    "get_list_buf_row_content": 0x14238C720,
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def hexadecimal(value: int | None) -> str | None:
    return f"0x{value:x}" if value is not None else None


def normalized_xrefs(image: PeImage) -> list[dict[str, str | None]]:
    xrefs = find_direct_control_xrefs(image, set(FUNCTIONS.values()))
    return [
        {
            "address": hexadecimal(item["address"]),
            "owner_start": hexadecimal(item["function_start"]),
            "owner_end": hexadecimal(item["function_end"]),
            "mnemonic": str(item["mnemonic"]),
            "target": hexadecimal(item["target"]),
        }
        for item in xrefs
    ]


def require_fragments(text: str, fragments: tuple[str, ...], label: str) -> None:
    missing = [fragment for fragment in fragments if fragment not in text]
    if missing:
        raise SystemExit(f"{label} no longer contains expected fragments: {missing}")


def build(binary: Path, output: Path) -> None:
    image = PeImage(binary)
    binary_hash = sha256(binary)
    if binary_hash != EXPECTED_SHA256:
        raise SystemExit(
            f"unexpected Rekordbox PE hash: {binary_hash}; expected {EXPECTED_SHA256}"
        )

    disconnect = render_function(image, FUNCTIONS["disconnect_with_inlined_aio_clear"])
    clear_helper = render_function(image, FUNCTIONS["map_only_aio_clear_helper"])
    standalone_compatibility = render_code(image, 0x14227E200, 0x14227E308)
    row_compatibility = "\n".join(
        (
            "## AppSync inline compatibility path",
            render_code(image, 0x14238CA79, 0x14238CB96).rstrip(),
            "",
            "## Master-interface standalone call",
            render_code(image, 0x14238D06C, 0x14238D07D).rstrip(),
            "",
        )
    )

    require_fragments(
        disconnect,
        (
            "call      0x14238b8a0",
            "lea       rcx, [rdi + 0x7a0]",
            "mov       r9, qword ptr [rdi + 0x790]",
            "call      0x1423832a0",
            "jmp       0x14237d670",
        ),
        "disconnect",
    )
    require_fragments(
        clear_helper,
        (
            "add       rcx, 0x7a0",
            "mov       r9, qword ptr [rbx + 0x790]",
            "call      0x1423832a0",
            "lea       rcx, [rbx + 0x7a0]",
        ),
        "map-only AIO clear helper",
    )
    require_fragments(
        standalone_compatibility,
        (
            "'idxMasContent'",
            "'djmdContent'",
            "mov       edx, 0xe",
            "mov       edx, 0x21",
            "cmp       edx, 0xac44",
            "cmp       edx, 0xbb80",
        ),
        "standalone compatibility predicate",
    )
    require_fragments(
        row_compatibility,
        (
            "'select FileType, SampleRate from djmdContent where rb_local_deleted = 0'",
            "'FileType'",
            "'SampleRate'",
            "cmp       eax, 0xac44",
            "cmp       eax, 0xbb80",
            "call      0x14227e200",
        ),
        "row compatibility paths",
    )

    output.mkdir(parents=True, exist_ok=True)
    artifacts = {
        "disconnect-aio-cache.disasm.txt": disconnect,
        "clear-aio-map.disasm.txt": clear_helper,
        "content-compatibility.disasm.txt": standalone_compatibility,
        "get-list-row-content-compatibility.disasm.txt": row_compatibility,
    }
    for name, content in artifacts.items():
        (output / name).write_text(content)

    xrefs = normalized_xrefs(image)
    absolute_pointer_references = find_absolute_pointers(
        image, set(FUNCTIONS.values())
    )
    if absolute_pointer_references:
        raise SystemExit(
            "unexpected absolute pointers to Windows predicates: "
            f"{absolute_pointer_references}"
        )

    counts = {
        name: sum(item["target"] == hexadecimal(address) for item in xrefs)
        for name, address in FUNCTIONS.items()
    }
    expected_counts = {
        "standalone_content_compatibility": 1,
        "disconnect_with_inlined_aio_clear": 1,
        "display_is_aio": 1,
        "map_only_aio_clear_helper": 0,
        "get_list_buf_row_content": 3,
    }
    if counts != expected_counts:
        raise SystemExit(f"unexpected Windows predicate xref counts: {counts}")

    report = {
        "format": 1,
        "scope": "Rekordbox 7.2.19 Windows Link Export device predicates",
        "source": {
            "sha256": binary_hash,
            "size": len(image.raw),
            "machine": str(image.binary.header.machine),
        },
        "functions": {
            name: {"address": hexadecimal(address), "direct_control_xrefs": counts[name]}
            for name, address in FUNCTIONS.items()
        },
        "direct_control_xrefs": xrefs,
        "absolute_pointer_references": absolute_pointer_references,
        "conclusions": {
            "display_classifier": "isAIO is called once by the AppSync Display formatter",
            "disconnect_cache_clear": (
                "Disconnect contains the player-keyed AIO-map erase inline; the separate "
                "map-only helper has no direct call or jump"
            ),
            "track_compatibility": (
                "AppSync GetListBufRowContent inlines the FileType/SampleRate predicate; "
                "its Master-interface branch calls the standalone predicate once"
            ),
            "bit_depth_read": False,
            "absolute_pointer_storage": (
                "no little-endian 64-bit image pointer targets any recovered function"
            ),
        },
        "artifacts": {
            name: hashlib.sha256(content.encode()).hexdigest()
            for name, content in artifacts.items()
        },
    }
    (output / "device-predicate-audit.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )

    markdown = f"""# Windows device-predicate audit

Source: Rekordbox 7.2.19 PE `{binary_hash}`.

| Role | Address | Direct calls/jumps | Result |
| --- | --- | ---: | --- |
| Display `isAIO` | `0x1423815c0` | 1 | Called by the AppSync Display formatter |
| Disconnect with inline AIO clear | `0x142380930` | 1 | Erases player key from the `0x790` map under the `0x7a0` lock |
| Map-only AIO clear helper | `0x142381700` | 0 | Same keyed erase, retained without a direct caller |
| Standalone content compatibility | `0x14227e200` | 1 | Called by the Master-interface row path |
| `GetListBufRowContent` | `0x14238c720` | 3 | AppSync path inlines the content predicate |

Windows therefore differs from the macOS call graph without differing in the
observed decisions. The active AppSync track-row path reads `FileType` and
`SampleRate` itself, rejects bytes 5 and 6, conditionally admits bytes 11 and
12 only at 44,100 or 48,000 Hz, and never reads BitDepth. Its alternate Master
path calls the standalone predicate at `0x14227e200`. Disconnect performs the
AIO-cache erase inline; it does not directly call the separately emitted
map-only helper.

The direct-reference count is exhaustive for x86-64 `call rel32` and `jmp
rel32` instructions targeting these five recovered functions. A full-image
search also finds zero little-endian 64-bit absolute pointers to any of the
five addresses, excluding ordinary PE pointer-table and vtable storage for
these exact functions. Computed pointers and semantically duplicated inline
code require separate proof; the two known inline decisions above are retained
as disassembly slices.
"""
    (output / "device-predicate-audit.md").write_text(markdown)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("binary", type=Path)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    build(args.binary, args.output)


if __name__ == "__main__":
    main()
