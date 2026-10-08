#!/usr/bin/env python3
"""Validate and summarize the local CDJ key-style Link Export oracle."""

from __future__ import annotations

import binascii
import hashlib
import json
import re
import struct
from pathlib import Path

from summarize_search_oracle import load, sha256, validate


ROOT = Path(__file__).resolve().parent.parent
CONFORMANCE = ROOT / "conformance"
GOLDENS = CONFORMANCE / "goldens/rekordbox-7.2.19/xdj-rx3"
SETTINGS = ROOT / "data/experiments/key-notation/device-settings"
STATES = ("classic", "alphanumeric")
STYLE = {"classic": 1, "alphanumeric": 2}
ROOT_LABELS = {
    "classic": (
        "Abm", "B", "Ebm", "F#", "Bbm", "Db", "Fm", "Ab", "Cm", "Eb",
        "Gm", "Bb", "Dm", "F", "Am", "C", "Em", "G", "Bm", "D", "F#m",
        "A", "Dbm", "E",
    ),
    "alphanumeric": tuple(
        f"{number}{letter}"
        for number in range(1, 13)
        for letter in ("A", "B")
    ),
}


def validate_setting(path: Path, style: int) -> dict[str, object]:
    data = path.read_bytes()
    assert len(data) == 0x8C
    assert struct.unpack_from("<I", data, 0)[0] == 0x60
    assert struct.unpack_from("<I", data, 0x64)[0] == 0x20
    assert struct.unpack_from("<I", data, 0x68)[0] == 0x12345678
    assert data[0x74] == style
    stored_crc = struct.unpack_from("<I", data, 0x88)[0]
    calculated_crc = binascii.crc_hqx(data[0x68:0x88], 0)
    assert stored_crc == calculated_crc
    return {
        "sha256": hashlib.sha256(data).hexdigest(),
        "bytes": len(data),
        "style_offset": "0x74",
        "style_value": style,
        "crc_offset": "0x88",
        "crc": f"0x{stored_crc:04x}",
    }


def cases_by_id(golden: dict[str, object]) -> dict[str, dict[str, object]]:
    behavior = golden["behavior"]
    assert isinstance(behavior, dict)
    cases = behavior["cases"]
    assert isinstance(cases, list)
    return {case["id"]: case for case in cases}


def values(row: dict[str, object]) -> list[object]:
    return [argument["value"] for argument in row["arguments"]]


def first_track(cases: dict[str, dict[str, object]], case_id: str) -> list[object]:
    return values(next(
        row for row in cases[case_id]["rows"]
        if row["arguments"][1]["value"] == 10001
    ))


def track_order(cases: dict[str, dict[str, object]], case_id: str) -> list[int]:
    return [row["arguments"][1]["value"] for row in cases[case_id]["rows"]]


def normalized_without_key_text(value: object) -> object:
    replacements = dict(zip(ROOT_LABELS["classic"], ROOT_LABELS["alphanumeric"]))
    key_pattern = re.compile(
        r"(?<![A-Za-z#])(" +
        "|".join(map(re.escape, sorted(replacements, key=len, reverse=True))) +
        r")(?![A-Za-z#])"
    )

    def replace(text: str) -> str:
        return key_pattern.sub(lambda match: replacements[match.group(1)], text)

    if isinstance(value, dict):
        normalized = {
            key: normalized_without_key_text(item) for key, item in value.items()
        }
        arguments = value.get("arguments")
        if isinstance(arguments, list):
            normalized_arguments = normalized["arguments"]
            assert isinstance(normalized_arguments, list)
            for index, argument in enumerate(arguments):
                if index == 0 or argument.get("type") != "string":
                    continue
                original = argument["value"]
                replacement = replace(original)
                previous = arguments[index - 1]
                if replacement == original or previous.get("type") != "number":
                    continue
                if previous["value"] == len(original.encode("utf-16-le")) + 2:
                    normalized_arguments[index - 1]["value"] = (
                        len(replacement.encode("utf-16-le")) + 2
                    )
        return normalized
    if isinstance(value, list):
        return [normalized_without_key_text(item) for item in value]
    if isinstance(value, str):
        return replace(value)
    return value


def main() -> None:
    manifest_path = CONFORMANCE / "fixtures/generated/key-notation/manifest.json"
    manifest = load(manifest_path)
    observed = {}
    goldens = {}

    for state in STATES:
        name = f"key-device-setting-{state}"
        suite = CONFORMANCE / f"suites/generated/{name}.json"
        golden_path = GOLDENS / f"{name}.json"
        cases = validate(suite, golden_path, manifest_path)
        golden = load(golden_path)
        goldens[state] = golden

        assert tuple(
            row["arguments"][3]["value"] for row in cases["key-root"]["rows"]
        ) == ROOT_LABELS[state]
        first_key = "Am" if state == "classic" else "8A"
        for case_id in ("collection-bpm", "smart-bpm", "display-bpm", "delivery-bpm"):
            assert first_track(cases, case_id)[14] == first_key
        for case_id in ("collection-key", "smart-key"):
            row = first_track(cases, case_id)
            assert row[5] == f"{first_key} - 120.0 bpm"
            assert row[14] == first_key
        for case_id in ("display-key", "delivery-key"):
            row = first_track(cases, case_id)
            assert row[5] == first_key
            assert row[14] == first_key

        setting_path = SETTINGS / "generated" / f"{state}.DAT"
        observed[state] = {
            "device_setting": validate_setting(setting_path, STYLE[state]),
            "suite_sha256": sha256(suite),
            "golden_sha256": sha256(golden_path),
            "restart_repeat_verified": True,
            "key_root_labels": ROOT_LABELS[state],
            "first_track": {
                "key": first_key,
                "key_bpm_composite": f"{first_key} - 120.0 bpm",
                "bpm": 12000,
                "key_id": 5001,
            },
            "key_sort_orders": {
                case_id: track_order(cases, case_id)
                for case_id in ("collection-key-sort", "smart-key-sort")
            },
        }

    classic = normalized_without_key_text(goldens["classic"]["behavior"])
    alpha = goldens["alphanumeric"]["behavior"]
    classic["suite"] = alpha["suite"]
    for case in classic["cases"]:
        case["description"] = next(
            item["description"] for item in alpha["cases"] if item["id"] == case["id"]
        )
    assert classic == alpha

    persisted_bpm = {}
    for state, suite_name, fixture_name, golden_name in (
        ("classic", "secondary-bpm", "secondary-bpm", "secondary-bpm"),
        (
            "alphanumeric",
            "device-key-style-alphanumeric-secondary-bpm",
            "secondary-bpm",
            "device-key-style-alphanumeric-secondary-bpm",
        ),
        ("classic-smart", "smart-secondary-bpm", "smart-secondary-bpm", "smart-secondary-bpm"),
        (
            "alphanumeric-smart",
            "device-key-style-alphanumeric-smart-secondary-bpm",
            "smart-secondary-bpm",
            "device-key-style-alphanumeric-smart-secondary-bpm",
        ),
    ):
        suite_path = CONFORMANCE / f"suites/generated/{suite_name}.json"
        fixture_manifest = CONFORMANCE / f"fixtures/generated/{fixture_name}/manifest.json"
        golden_path = GOLDENS / f"{golden_name}.json"
        cases = validate(suite_path, golden_path, fixture_manifest)
        case_id = "tracks" if "smart" in state else "track-rows"
        row = values(cases[case_id]["rows"][0])
        expected_key = "8A" if state.startswith("alphanumeric") else "Am"
        assert row[0] == 12000
        assert row[5] == f"120.0 bpm - {expected_key}"
        assert row[14] == expected_key
        assert row[15] == 12000
        persisted_bpm[state] = {
            "fixture": fixture_name,
            "suite_sha256": sha256(suite_path),
            "golden_sha256": sha256(golden_path),
            "restart_repeat_verified": True,
            "first_track": {
                "primary_bpm": row[0],
                "composite": row[5],
                "tertiary_key": row[14],
                "bpm": row[15],
            },
        }

    report = {
        "format": "rekordbox-link-export-device-key-style-v1",
        "oracle": {
            "backend": "rekordbox",
            "version": "7.2.19",
            "configurations": 2,
            "cases_per_configuration": 13,
            "all_restart_repeats_verified": True,
            "only_key_strings_and_their_utf16_lengths_change": True,
        },
        "fixture": {
            "profile": manifest["profile"],
            "version": manifest["fixture_version"],
            "database_sha256": manifest["database_sha256"],
            "fixture_fingerprint": manifest["fixture_fingerprint"],
            "manifest_sha256": sha256(manifest_path),
        },
        "device_setting": {
            "guest_path": "C:/Users/Research/AppData/Roaming/Pioneer/rekordbox6/DEVSETTING.DAT",
            "baseline_sha256": sha256(SETTINGS / "baseline/DEVSETTING.DAT"),
            "payload_offset": "0x68",
            "payload_bytes": 0x20,
            "style_offset": "0x74",
            "crc_offset": "0x88",
            "crc_algorithm": "CRC-CCITT via crc_hqx(payload, 0)",
        },
        "behavior": observed,
        "persisted_bpm_secondary": persisted_bpm,
        "static_evidence": {
            path: sha256(ROOT / path)
            for path in (
                "data/static-analysis/windows/exchange-key-name.disasm.txt",
                "data/static-analysis/windows/local-key-style.disasm.txt",
                "data/static-analysis/device-key-style.disasm.txt",
            )
        },
    }
    output = ROOT / "data/experiments/key-notation/device-setting-summary.json"
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(output)


if __name__ == "__main__":
    main()
