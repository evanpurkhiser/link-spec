#!/usr/bin/env python3
"""Validate and summarize the Windows/macOS History implementation split."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "data/static-analysis"
WINDOWS = STATIC / "windows"
OUTPUT = ROOT / "data/experiments/link-visibility/windows-history-summary.json"
EXPECTED_PE_SHA256 = "c9ed23e974c51c75e2ec069fbd2679a3dbe606be9e79e9cbbd13d6418ab11c37"
EXPECTED_DISPATCH = 0x142385970
EXPECTED_VTABLE_OFFSET = 0x230
EXPECTED_HISTORY = 0x14236C690


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> object:
    return json.loads(path.read_text())


def main() -> None:
    metadata_path = WINDOWS / "rekordbox-metadata.json"
    immediates_path = WINDOWS / "request-1112-immediates.json"
    dispatch_path = WINDOWS / "request-1112-dispatch.disasm.txt"
    vtable_path = WINDOWS / "appsync-history-vtable.json"
    history_path = WINDOWS / "appsync-history.disasm.txt"
    mac_xrefs_path = STATIC / "link-export-visibility-xrefs.txt"

    metadata = load_json(metadata_path)
    assert isinstance(metadata, dict)
    assert metadata["sha256"] == EXPECTED_PE_SHA256
    assert metadata["size"] == 103_540_656
    assert metadata["machine"] == "MACHINE_TYPES.AMD64"

    immediates = load_json(immediates_path)
    assert isinstance(immediates, list)
    immediate_owners = {item["function_start"] for item in immediates}
    assert EXPECTED_DISPATCH in immediate_owners

    vtables = load_json(vtable_path)
    assert isinstance(vtables, list) and len(vtables) == 1
    vtable = vtables[0]
    assert vtable["class"] == "PSvAppSyncDBIF"
    entry = next(
        item for item in vtable["entries"] if item["offset"] == EXPECTED_VTABLE_OFFSET
    )
    assert entry["target"] == EXPECTED_HISTORY
    assert entry["function_start"] == EXPECTED_HISTORY

    dispatch = dispatch_path.read_text()
    assert f"address={EXPECTED_DISPATCH:#x}" in dispatch
    assert "cmp       ax, bx" in dispatch
    assert "mov       rdi, qword ptr [rax + 0x230]" in dispatch
    assert "call      rdi" in dispatch

    history = history_path.read_text()
    assert f"address={EXPECTED_HISTORY:#x}" in history
    assert "'TrackNo'" in history
    assert "'ContentID'" in history
    assert "'select * from djmdContent where rb_local_deleted = 0 and ID = %lu'" in history
    assert "FolderPath" not in history

    mac_xrefs = mac_xrefs_path.read_text()
    assert "0x1010c5e12  djeplGetTrack_History" in mac_xrefs
    assert "0x1010c5f20  djeplGetTrack_History" in mac_xrefs

    summary = {
        "format": "rekordbox-windows-history-static-cross-v1",
        "windows": {
            "product_version": "7.2.19.0",
            "binary_sha256": EXPECTED_PE_SHA256,
            "binary_size": metadata["size"],
            "request_kind": "0x1112",
            "dispatch_function": f"{EXPECTED_DISPATCH:#x}",
            "interface": "PSvAppSyncDBIF",
            "vtable_offset": f"{EXPECTED_VTABLE_OFFSET:#x}",
            "history_function": f"{EXPECTED_HISTORY:#x}",
            "content_query": "select * from djmdContent where rb_local_deleted = 0 and ID = %lu",
            "reads_folder_path": False,
            "explicit_streaming_visibility_gate": False,
        },
        "macos": {
            "product_version": "7.2.19",
            "binary_sha256": "07dcecbaf304f777e435539c83c7dcc02e41de1eaf2e0a75e8a9852e4411a244",
            "history_function": "djeplGetTrack_History(RbDBIndex,int,int,char)",
            "visibility_call_sites": ["0x1010c5e12", "0x1010c5f20"],
        },
        "conclusion": "Windows AppSync History bypasses the FolderPath streaming gate used by macOS History.",
        "artifacts": {
            path.relative_to(ROOT).as_posix(): sha256(path)
            for path in (
                metadata_path,
                immediates_path,
                dispatch_path,
                vtable_path,
                history_path,
                mac_xrefs_path,
            )
        },
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(OUTPUT)


if __name__ == "__main__":
    main()
