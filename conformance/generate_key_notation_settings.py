#!/usr/bin/env python3
"""Generate byte-stable Rekordbox key-notation preference fixtures."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
BASELINE = (
    ROOT
    / "data/experiments/key-notation/preferences/baseline/rekordbox3.settings"
)
OUTPUT = ROOT / "data/experiments/key-notation/preferences/generated"
STATES = {
    "classic-normalized": ("1", "0"),
    "classic-database": ("1", "1"),
    "alphanumeric-normalized": ("2", "0"),
    "alphanumeric-database": ("2", "1"),
}


def replace_value(document: bytes, name: str, value: str) -> bytes:
    pattern = rb'(<VALUE name="' + name.encode() + rb'" val=")([^"]+)("/>)'
    replaced, count = re.subn(pattern, rb"\g<1>" + value.encode() + rb"\g<3>", document)
    if count != 1:
        raise ValueError(f"expected one {name} setting, found {count}")

    return replaced


def main() -> None:
    baseline = BASELINE.read_bytes()
    ET.fromstring(baseline)
    OUTPUT.mkdir(parents=True, exist_ok=True)

    for state, (key_string, show_original) in STATES.items():
        rendered = replace_value(baseline, "KeyStringSetting", key_string)
        rendered = replace_value(rendered, "ShowOriginalKey", show_original)
        ET.fromstring(rendered)

        path = OUTPUT / f"{state}.settings"
        path.write_bytes(rendered)
        print(path)


if __name__ == "__main__":
    main()
