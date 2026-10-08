#!/usr/bin/env python3
"""Regenerate the retained-artifact checksum ledger."""

from __future__ import annotations

import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
LEDGER = ROOT / "data/SHA256SUMS"
EXCLUDED_DIRECTORIES = (
    ROOT / ".git",
    ROOT / ".venv",
    ROOT / "conformance/__pycache__",
    ROOT / "conformance/fixtures/generated",
    ROOT / "conformance/runtime",
    ROOT / "conformance/target",
    ROOT / "conformance/results",
    ROOT / "guest-control/state",
    ROOT / "tools/__pycache__",
)


def excluded(path: Path) -> bool:
    return (
        path == LEDGER
        or path.name.endswith(".next")
        or any(path.is_relative_to(directory) for directory in EXCLUDED_DIRECTORIES)
    )


def main() -> None:
    entries = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or excluded(path):
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        relative = path.relative_to(ROOT)
        entries.append(f"{digest}  {relative}")
    LEDGER.write_text("\n".join(entries) + "\n")
    print(f"wrote {len(entries)} checksums to {LEDGER}")


if __name__ == "__main__":
    main()
