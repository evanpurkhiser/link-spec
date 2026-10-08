#!/usr/bin/env python3
"""Inventory the pinned local Dysentery guide used by this research."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE = ROOT.parent / "dysentery"
DEFAULT_OUTPUT = ROOT / "data/external/dysentery-docs.json"
EXPECTED_COMMIT = "f62a24ba947f9db4c1553bb2dc3ba76de1fecbb4"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def headings(path: Path) -> list[dict[str, object]]:
    result = []
    for line_number, line in enumerate(path.read_text().splitlines(), start=1):
        prefix = len(line) - len(line.lstrip("="))
        if prefix == 0 or prefix > 3 or not line[prefix:].startswith(" "):
            continue

        result.append(
            {
                "level": prefix,
                "line": line_number,
                "title": line[prefix + 1 :],
            }
        )

    return result


def build(source: Path) -> dict[str, object]:
    commit = subprocess.run(
        ["git", "-C", source, "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if commit != EXPECTED_COMMIT:
        raise SystemExit(f"unexpected Dysentery commit: {commit}")

    docs_root = source / "doc/modules/ROOT"
    paths = [docs_root / "nav.adoc", *sorted((docs_root / "pages").glob("*.adoc"))]
    return {
        "format": 1,
        "scope": "pinned local Dysentery guide",
        "source": {
            "repository": "../dysentery",
            "commit": commit,
            "docs_root": "doc/modules/ROOT",
        },
        "document_count": len(paths),
        "documents": [
            {
                "path": str(path.relative_to(source)),
                "size": path.stat().st_size,
                "sha256": sha256(path),
                "headings": headings(path),
            }
            for path in paths
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(build(args.source.resolve()), indent=2) + "\n")


if __name__ == "__main__":
    main()
