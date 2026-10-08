#!/usr/bin/env python3
"""Generate deterministic Rekordbox played-state preference fixtures."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/experiments/key-notation/preferences/baseline/rekordbox3.settings"
OUTPUT = ROOT / "data/experiments/played-track-state/settings"
SETTINGS = ("PlayedTrackOption", "LinkPlayedTrackOption")
STATES = {
    "reset": {"PlayedTrackOption": "1", "LinkPlayedTrackOption": "1"},
    "link-persist": {"PlayedTrackOption": "1", "LinkPlayedTrackOption": "0"},
    "ordinary-persist": {"PlayedTrackOption": "0", "LinkPlayedTrackOption": "1"},
    "persist": {"PlayedTrackOption": "0", "LinkPlayedTrackOption": "0"},
}


def set_value(document: bytes, name: str, value: str) -> bytes:
    pattern = rb'(<VALUE name="' + name.encode() + rb'" val=")([^"]+)("/>)'
    rendered, count = re.subn(pattern, rb"\g<1>" + value.encode() + rb"\g<3>", document)
    if count == 1:
        return rendered
    if count:
        raise ValueError(f"expected at most one {name}, found {count}")

    closing = b"</PROPERTIES>"
    if document.count(closing) != 1:
        raise ValueError("expected one PROPERTIES closing tag")
    line_ending = b"\r\n" if b"\r\n" in document else b"\n"
    addition = b'  <VALUE name="' + name.encode() + b'" val="' + value.encode() + b'"/>'
    return document.replace(closing, addition + line_ending + closing)


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    baseline = SOURCE.read_bytes()
    ET.fromstring(baseline)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "baseline.settings").write_bytes(baseline)

    variants = []
    for state, values in STATES.items():
        rendered = baseline
        for name, value in values.items():
            rendered = set_value(rendered, name, value)
        ET.fromstring(rendered)

        path = args.output / f"{state}.settings"
        path.write_bytes(rendered)
        variants.append(
            {
                "state": state,
                "file": path.name,
                "sha256": sha256(rendered),
                "values": {name: int(value) for name, value in values.items()},
            }
        )

    manifest = {
        "format": 1,
        "source": str(SOURCE.relative_to(ROOT)),
        "source_sha256": sha256(baseline),
        "baseline_file": "baseline.settings",
        "variants": variants,
    }
    (args.output / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n"
    )


if __name__ == "__main__":
    main()
