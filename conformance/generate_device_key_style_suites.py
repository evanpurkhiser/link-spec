#!/usr/bin/env python3
"""Generate suites for the local CDJ device-setting key-style cross."""

from __future__ import annotations

import json
from pathlib import Path

from generate_key_notation_suites import OUTPUT, cases


STYLES = ("classic", "alphanumeric")


def write(suite: dict[str, object]) -> None:
    output = OUTPUT / f"{suite['name']}.json"
    output.write_text(json.dumps(suite, indent=2) + "\n")
    print(output)


def derived_suite(source: Path, name: str, description: str) -> dict[str, object]:
    suite = json.loads(source.read_text())
    suite["name"] = name
    suite["description"] = description
    suite["repeat_strategy"] = "fixture-reset-device-setting-reset-and-restart"
    for case in suite["cases"]:
        case["description"] = f"Alphanumeric local CDJ style: {case['description']}"
    return suite


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for style in STYLES:
        name = f"key-device-setting-{style}"
        suite = {
            "name": name,
            "description": (
                "Link Export key display and menu behavior under the local CDJ "
                f"device-setting {style} state"
            ),
            "fixture_profile": "key-notation",
            "fixture_version": 1,
            "repeat_strategy": "fixture-reset-device-setting-reset-and-restart",
            "defaults": {
                "device": 1,
                "context": "0x01010301",
                "sort": 0,
                "root_capabilities": "0x05cfffff",
                "setup": "extended",
                "page_size": 10,
                "render_arguments": [0, "$total", 12, 1, 0],
            },
            "cases": cases(style, "Local CDJ device key style"),
        }
        write(suite)

    write(derived_suite(
        OUTPUT / "secondary-bpm.json",
        "device-key-style-alphanumeric-secondary-bpm",
        "Persisted BPM secondary column under the Alphanumeric local CDJ style",
    ))
    write(derived_suite(
        OUTPUT / "smart-secondary-bpm.json",
        "device-key-style-alphanumeric-smart-secondary-bpm",
        "Persisted Smart BPM secondary column under the Alphanumeric local CDJ style",
    ))


if __name__ == "__main__":
    main()
