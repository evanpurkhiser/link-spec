#!/usr/bin/env python3
"""Validate and summarize XDJ-RR old-Key and silent CueTrack behavior."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

from summarize_search_oracle import load, sha256, validate
from rekordbox_health import validate_health_pair


ROOT = Path(__file__).resolve().parent.parent
CONFORMANCE = ROOT / "conformance"
DECLARATION = CONFORMANCE / "data/xdj-rr-old-key-matrix.json"
MANIFEST = CONFORMANCE / "fixtures/generated/full/manifest.json"
SOURCE = ROOT / "data/static-analysis/xdj-rr-client-navigation.json"
DISPATCH = ROOT / "data/static-analysis/link-export-dispatch-tables.json"
EVIDENCE = ROOT / "data/experiments/xdj-rr-client-navigation/old-key"
OUTPUT = EVIDENCE / "summary.json"
CSV_OUTPUT = EVIDENCE / "matrix.csv"
SCOPE = "real Rekordbox 7.2.19 XDJ-RR old-Key and CueTrack matrix"
WIDTHS = {"extended": 16, "legacy": 12}
ROOT_CASES = (
    "old-key-root-location-1",
    "old-key-root-location-2",
    "old-key-root-after-cue-location-1",
    "old-key-root-after-cue-location-2",
)
TRACK_CASES = (
    "old-key-am-tracks-location-1",
    "old-key-c-tracks-location-2",
)
CUE_CASES = ("cue-track-root-location-1", "cue-track-root-location-2")


def values(row: dict[str, object]) -> list[object]:
    return [argument["value"] for argument in row["arguments"]]


def rows(case: dict[str, object]) -> list[list[object]]:
    return [values(row) for row in case["rows"]]


def behavior(cases: dict[str, dict[str, object]]) -> dict[str, object]:
    return {
        case_id: {
            "outcome": case["outcome"],
            "total": case["total"],
            "rows": rows(case),
        }
        for case_id, case in cases.items()
    }


def behavior_sha256(cases: dict[str, dict[str, object]]) -> str:
    encoded = json.dumps(behavior(cases), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode()).hexdigest()


def validate_receipt(entry: dict[str, object], golden: Path) -> None:
    evidence = CONFORMANCE / str(entry["evidence"])
    receipt_path = evidence / "receipt.json"
    receipt = load(receipt_path)
    expected = {
        "format": 1,
        "scope": SCOPE,
        "variant": f"xdj-rr-old-key-{entry['id']}",
        "suite_sha256": sha256(CONFORMANCE / str(entry["suite"])),
        "fixture_manifest_sha256": sha256(MANIFEST),
        "identity_sha256": sha256(CONFORMANCE / str(entry["identity"])),
        "golden_sha256": sha256(golden),
        "case_count": 8,
        "service_count": 3,
        "exact_repeat": True,
    }
    for key, expected_value in expected.items():
        if receipt.get(key) != expected_value:
            raise ValueError(f"{receipt_path}: {key} differs from declaration")

    validate_health_pair(
        evidence,
        receipt,
        f"adjacent-payload-xdj-rr-old-key-{entry['id']}",
        sha256,
    )


def summarize() -> tuple[dict[str, object], list[dict[str, object]]]:
    declaration = load(DECLARATION)
    if declaration["format"] != 1 or len(declaration["variants"]) != 6:
        raise ValueError("old-Key declaration must contain six variants")

    source = load(SOURCE)
    wrappers = {item["request_kind"]: item for item in source["wrappers"]}
    if any(kind not in wrappers for kind in ("100B", "110B", "130C")):
        raise ValueError("XDJ-RR source no longer defines the old-Key/CueTrack wrappers")

    dispatch = {
        item["request_kind"]: item for item in load(DISPATCH)["direct_dispatch"]
    }
    if dispatch["130C"]["target"] != "recognized-log-only":
        raise ValueError("Rekordbox CueTrack terminal classification changed")

    cases_by_variant = {}
    matrix = []
    golden_hashes = {}
    behavior_hashes = {}
    for entry in declaration["variants"]:
        suite = CONFORMANCE / entry["suite"]
        golden = CONFORMANCE / entry["golden"]
        observed = validate(suite, golden, MANIFEST)
        validate_receipt(entry, golden)
        if len(observed) != 8:
            raise ValueError(f"{entry['id']}: expected eight cases")
        cases_by_variant[entry["id"]] = observed
        golden_hashes[entry["id"]] = sha256(golden)
        behavior_hashes[entry["id"]] = behavior_sha256(observed)

        width = WIDTHS[entry["setup"]]
        for case_id in ROOT_CASES:
            case = observed[case_id]
            if case["outcome"] != "menu" or case["total"] != 2 or len(case["rows"]) != 2:
                raise ValueError(f"{entry['id']}/{case_id}: old-Key root differs")
        for case_id in TRACK_CASES:
            case = observed[case_id]
            if case["outcome"] != "menu" or case["total"] != 4 or len(case["rows"]) != 4:
                raise ValueError(f"{entry['id']}/{case_id}: old-Key tracks differ")
        for case_id in ROOT_CASES + TRACK_CASES:
            if {len(row["arguments"]) for row in observed[case_id]["rows"]} != {width}:
                raise ValueError(f"{entry['id']}/{case_id}: row width differs")
        for case_id in CUE_CASES:
            case = observed[case_id]
            if case["outcome"] != "timeout" or case["header"] or case["rows"]:
                raise ValueError(f"{entry['id']}/{case_id}: CueTrack was not silent")

        if rows(observed[ROOT_CASES[0]]) != rows(observed[ROOT_CASES[2]]):
            raise ValueError(f"{entry['id']}: location-1 post-CueTrack health root differs")
        if rows(observed[ROOT_CASES[1]]) != rows(observed[ROOT_CASES[3]]):
            raise ValueError(f"{entry['id']}: location-2 post-CueTrack health root differs")

        for case_id, case in observed.items():
            matrix.append(
                {
                    "variant": entry["id"],
                    "model": entry["model"],
                    "setup": entry["setup"],
                    "case": case_id,
                    "outcome": case["outcome"],
                    "total": case["total"],
                    "row_count": len(case["rows"]),
                    "rows_sha256": hashlib.sha256(
                        json.dumps(rows(case), separators=(",", ":")).encode()
                    ).hexdigest(),
                }
            )

    legacy_prefix = True
    for model in ("xdj-rx3-ordinary", "xdj-rx3-status", "cdj-3000-status"):
        extended = cases_by_variant[f"{model}-extended"]
        legacy = cases_by_variant[f"{model}-legacy"]
        for case_id in ROOT_CASES + TRACK_CASES:
            if rows(legacy[case_id]) != [row[:12] for row in rows(extended[case_id])]:
                legacy_prefix = False

    identity_equal = {}
    for setup in WIDTHS:
        variants = [
            cases_by_variant[f"{model}-{setup}"]
            for model in ("xdj-rx3-ordinary", "xdj-rx3-status", "cdj-3000-status")
        ]
        identity_equal[setup] = all(
            behavior(variant) == behavior(variants[0]) for variant in variants[1:]
        )

    report = {
        "format": 1,
        "scope": SCOPE,
        "source_sha256": sha256(SOURCE),
        "dispatch_sha256": sha256(DISPATCH),
        "declaration_sha256": sha256(DECLARATION),
        "fixture_manifest_sha256": sha256(MANIFEST),
        "fixture_fingerprint": load(MANIFEST)["fixture_fingerprint"],
        "variant_count": 6,
        "case_count": 48,
        "record_repeat_execution_count": 96,
        "models": ["xdj-rx3-ordinary", "xdj-rx3-status", "cdj-3000-status"],
        "setups": WIDTHS,
        "observed": {
            "old_key_root_total": 2,
            "old_key_tracks_per_fixture_key": 4,
            "cue_track_silent_at_locations": [1, 2],
            "post_timeout_health_controls_succeeded": True,
            "identity_behavior_equal_within_setup": identity_equal,
            "legacy_rows_are_extended_prefix": legacy_prefix,
        },
        "behavior_sha256": behavior_hashes,
        "golden_sha256": golden_hashes,
    }
    return report, matrix


def main() -> None:
    report, matrix = summarize()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    with CSV_OUTPUT.open("w", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=matrix[0].keys())
        writer.writeheader()
        writer.writerows(matrix)
    print(f"wrote {OUTPUT} and {CSV_OUTPUT}: {len(matrix)} rows")


if __name__ == "__main__":
    main()
