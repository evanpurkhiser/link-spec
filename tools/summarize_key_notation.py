#!/usr/bin/env python3
"""Validate and summarize the Rekordbox key-notation preference matrix."""

from __future__ import annotations

import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path

from summarize_search_oracle import load, sha256, validate


ROOT = Path(__file__).resolve().parent.parent
CONFORMANCE = ROOT / "conformance"
GOLDENS = CONFORMANCE / "goldens/rekordbox-7.2.19/xdj-rx3"
RESULT = CONFORMANCE / "results/rbxport/c144f19+tree.80e87ec8aace/summary.json"
PREFERENCES = ROOT / "data/experiments/key-notation/preferences/generated"
STATES = (
    "classic-normalized",
    "classic-database",
    "alphanumeric-normalized",
    "alphanumeric-database",
)
EXPECTED_SETTINGS = {
    "classic-normalized": ("1", "0"),
    "classic-database": ("1", "1"),
    "alphanumeric-normalized": ("2", "0"),
    "alphanumeric-database": ("2", "1"),
}
CLASSIC_ROOT = (
    "Abm", "B", "Ebm", "F#", "Bbm", "Db", "Fm", "Ab", "Cm", "Eb", "Gm", "Bb",
    "Dm", "F", "Am", "C", "Em", "G", "Bm", "D", "F#m", "A", "Dbm", "E",
)


def preference_values(path: Path) -> dict[str, str]:
    root = ET.parse(path).getroot()
    return {
        element.attrib["name"]: element.attrib["val"]
        for element in root.findall("VALUE")
        if element.attrib.get("name") in {"KeyStringSetting", "ShowOriginalKey"}
    }


def wire_behavior(cases: dict[str, dict[str, object]]) -> list[dict[str, object]]:
    fields = ("id", "outcome", "total", "header", "rows", "pages")
    return [{field: case[field] for field in fields} for case in cases.values()]


def behavior_sha256(behavior: list[dict[str, object]]) -> str:
    encoded = json.dumps(behavior, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def first_track(cases: dict[str, dict[str, object]], case_id: str) -> list[object]:
    row = next(
        row
        for row in cases[case_id]["rows"]
        if row["arguments"][1]["value"] == 10001
    )
    return [argument["value"] for argument in row["arguments"]]


def main() -> None:
    replay = load(RESULT)
    manifest_path = CONFORMANCE / "fixtures/generated/key-notation/manifest.json"
    manifest = load(manifest_path)
    replay_by_suite = {entry["suite"]: entry for entry in replay["suites"]}
    observed = {}
    common_wire_hash = None

    for state in STATES:
        name = f"key-notation-{state}"
        suite = CONFORMANCE / f"suites/generated/{name}.json"
        golden = GOLDENS / f"{name}.json"
        settings = PREFERENCES / f"{state}.settings"
        cases = validate(suite, golden, manifest_path)

        expected_key_string, expected_show_original = EXPECTED_SETTINGS[state]
        values = preference_values(settings)
        assert values == {
            "KeyStringSetting": expected_key_string,
            "ShowOriginalKey": expected_show_original,
        }
        assert tuple(
            row["arguments"][3]["value"] for row in cases["key-root"]["rows"]
        ) == CLASSIC_ROOT

        for case_id in (
            "collection-key",
            "smart-key",
            "display-key",
            "delivery-key",
        ):
            row = first_track(cases, case_id)
            assert row[14] == "Am"
        assert first_track(cases, "collection-key")[5] == "Am - 120.0 bpm"
        assert first_track(cases, "smart-key")[5] == "Am - 120.0 bpm"
        assert first_track(cases, "display-key")[5] == "Am"
        assert first_track(cases, "delivery-key")[5] == "Am"

        wire_hash = behavior_sha256(wire_behavior(cases))
        if common_wire_hash is None:
            common_wire_hash = wire_hash
        assert wire_hash == common_wire_hash

        replay_result = replay_by_suite[name]
        assert replay_result["cases"] == 13
        observed[state] = {
            "KeyStringSetting": int(expected_key_string),
            "ShowOriginalKey": bool(int(expected_show_original)),
            "preference_sha256": sha256(settings),
            "suite_sha256": sha256(suite),
            "golden_sha256": sha256(golden),
            "wire_behavior_sha256": wire_hash,
            "restart_repeat_verified": True,
            "rbxport": {
                "exact": len(replay_result["exact_cases"]),
                "same_outcome_total_row_count": len(
                    replay_result["same_outcome_total_row_count_cases"]
                ),
                "different": len(replay_result["different_cases"]),
            },
        }

    report = {
        "format": "rekordbox-link-export-key-notation-v1",
        "oracle": {
            "backend": "rekordbox",
            "version": "7.2.19",
            "configurations": 4,
            "cases_per_configuration": 13,
            "all_restart_repeats_verified": True,
            "wire_behavior_sha256": common_wire_hash,
        },
        "fixture": {
            "profile": manifest["profile"],
            "version": manifest["fixture_version"],
            "database_sha256": manifest["database_sha256"],
            "fixture_fingerprint": manifest["fixture_fingerprint"],
            "database_scale_names": {"5001": "08A", "5002": "08B"},
            "manifest_sha256": sha256(manifest_path),
        },
        "behavior": {
            "all_four_preference_states_wire_identical": True,
            "key_root_labels": CLASSIC_ROOT,
            "first_track_classic_key": "Am",
            "first_track_key_secondary": "Am - 120.0 bpm",
            "configurations": observed,
        },
        "static_evidence": {
            "disassembly": "data/static-analysis/key-notation-settings.disasm.txt",
            "disassembly_sha256": sha256(
                ROOT / "data/static-analysis/key-notation-settings.disasm.txt"
            ),
        },
        "rbxport": {
            "version": replay["backend_version"],
            "configurations": {
                state: observed[state]["rbxport"] for state in STATES
            },
        },
    }
    output = ROOT / "data/experiments/key-notation/summary.json"
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(output)


if __name__ == "__main__":
    main()
