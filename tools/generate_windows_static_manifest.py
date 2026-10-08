#!/usr/bin/env python3
"""Generate provenance for every retained Windows Rekordbox static extract."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
WINDOWS = ROOT / "data/static-analysis/windows"
ANALYZER = ROOT / "tools/analyze_windows_pe.py"
DEVICE_AUDITOR = ROOT / "tools/generate_windows_device_predicate_audit.py"
SEMANTIC_AUDITOR = ROOT / "tools/audit_windows_device_semantics.py"
OUTPUT = WINDOWS / "manifest.json"
INSTALLER = ROOT.parent / "rekordbox-windows/shared/Install_rekordbox_x64_7_2_19.exe"
INSTALLER_REFERENCE = "../rekordbox-windows/shared/Install_rekordbox_x64_7_2_19.exe"

ARTIFACTS = (
    ("rekordbox-metadata.json", ANALYZER, ["metadata"]),
    ("request-1112-immediates.json", ANALYZER, ["immediate", "0x1112"]),
    ("request-1112-dispatch.disasm.txt", ANALYZER, ["function", "0x142385970"]),
    (
        "appsync-history-vtable.json",
        ANALYZER,
        ["vtable", "PSvAppSyncDBIF", "--start", "0x200", "--end", "0x248"],
    ),
    ("appsync-history.disasm.txt", ANALYZER, ["function", "0x14236c690"]),
    ("request-2002-immediates.json", ANALYZER, ["immediate", "0x2002"]),
    ("song-info-dispatch.disasm.txt", ANALYZER, ["function", "0x142386ad0"]),
    ("display-song-info-wrapper.disasm.txt", ANALYZER, ["function", "0x14238e3e0"]),
    (
        "appsync-display-vtable.json",
        ANALYZER,
        ["vtable", "PSvAppSyncDBIF", "--start", "0x140", "--end", "0x190"],
    ),
    ("appsync-display-song-info.disasm.txt", ANALYZER, ["function", "0x142361f30"]),
    ("is-aio.disasm.txt", ANALYZER, ["function", "0x1423815c0"]),
    ("exchange-key-name.disasm.txt", ANALYZER, ["function", "0x14235e5e0"]),
    ("local-key-style.disasm.txt", ANALYZER, ["function", "0x141c5f780"]),
    ("device-predicate-audit.json", DEVICE_AUDITOR, ["<rekordbox.exe>"]),
    ("device-predicate-audit.md", DEVICE_AUDITOR, ["<rekordbox.exe>"]),
    ("disconnect-aio-cache.disasm.txt", DEVICE_AUDITOR, ["<rekordbox.exe>"]),
    ("clear-aio-map.disasm.txt", DEVICE_AUDITOR, ["<rekordbox.exe>"]),
    ("content-compatibility.disasm.txt", DEVICE_AUDITOR, ["<rekordbox.exe>"]),
    (
        "get-list-row-content-compatibility.disasm.txt",
        DEVICE_AUDITOR,
        ["<rekordbox.exe>"],
    ),
    ("device-semantic-audit.json", SEMANTIC_AUDITOR, ["<rekordbox.exe>"]),
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build() -> dict[str, object]:
    metadata = json.loads((WINDOWS / "rekordbox-metadata.json").read_text())
    artifacts = []
    for name, producer, arguments in ARTIFACTS:
        path = WINDOWS / name
        if not path.is_file():
            raise SystemExit(f"missing Windows static artifact: {path}")
        artifacts.append(
            {
                "path": str(path.relative_to(ROOT)),
                "sha256": sha256(path),
                "producer": str(producer.relative_to(ROOT)),
                "producer_arguments": arguments,
            }
        )

    return {
        "format": 3,
        "scope": "Rekordbox 7.2.19 Windows PE static extracts",
        "source": {
            "guest_path": "C:/Program Files/rekordbox/rekordbox 7.2.19/rekordbox.exe",
            "temporary_host_path": "/tmp/rekordbox-7.2.19-windows.exe",
            "sha256": metadata["sha256"],
            "size": metadata["size"],
            "machine": metadata["machine"],
            "installer_path": INSTALLER_REFERENCE,
            "installer_sha256": sha256(INSTALLER),
            "installer_member": "rekordbox.exe",
            "installer_format": "NSIS-3 Unicode, LZMA:23 solid archive",
        },
        "producers": {
            str(path.relative_to(ROOT)): sha256(path)
            for path in (ANALYZER, DEVICE_AUDITOR, SEMANTIC_AUDITOR)
        },
        "artifacts": artifacts,
        "cleanup": {
            "temporary_host_copy_retained": False,
            "canonical_copy": "retained installer member and installed guest disk",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()

    args.output.write_text(json.dumps(build(), indent=2) + "\n")


if __name__ == "__main__":
    main()
