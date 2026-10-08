#!/usr/bin/env python3
"""Validate and summarize source-defined XDJ-RR location-9 Delivery behavior."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

from summarize_search_oracle import load, sha256, validate
from rekordbox_health import validate_health_pair


ROOT = Path(__file__).resolve().parent.parent
CONFORMANCE = ROOT / "conformance"
DECLARATION = CONFORMANCE / "data/xdj-rr-location9-matrix.json"
MANIFEST = CONFORMANCE / "fixtures/generated/full/manifest.json"
SOURCE = ROOT / "data/static-analysis/xdj-rr-client-navigation.json"
EVIDENCE = ROOT / "data/experiments/xdj-rr-client-navigation/location9"
OUTPUT = EVIDENCE / "summary.json"
CSV_OUTPUT = EVIDENCE / "matrix.csv"
SCOPE = "real Rekordbox 7.2.19 XDJ-RR source-defined location-9 Delivery matrix"
WIDTHS = {"extended": 16, "legacy": 12}


def values(row: dict[str, object]) -> list[object]:
    return [argument["value"] for argument in row["arguments"]]


def rows(case: dict[str, object]) -> list[list[object]]:
    return [values(row) for row in case["rows"]]


def validate_receipt(entry: dict[str, object], golden: Path) -> None:
    evidence = CONFORMANCE / str(entry["evidence"])
    receipt_path = evidence / "receipt.json"
    receipt = load(receipt_path)
    expected = {
        "format": 1,
        "scope": SCOPE,
        "variant": f"xdj-rr-location9-{entry['id']}",
        "suite_sha256": sha256(CONFORMANCE / str(entry["suite"])),
        "fixture_manifest_sha256": sha256(MANIFEST),
        "identity_sha256": sha256(CONFORMANCE / str(entry["identity"])),
        "golden_sha256": sha256(golden),
        "case_count": 6,
        "service_count": 1,
        "exact_repeat": True,
    }
    for key, expected_value in expected.items():
        if receipt.get(key) != expected_value:
            raise ValueError(f"{receipt_path}: {key} differs from declaration")

    validate_health_pair(
        evidence,
        receipt,
        f"adjacent-payload-xdj-rr-location9-{entry['id']}",
        sha256,
    )


def summarize() -> tuple[dict[str, object], list[dict[str, object]]]:
    declaration = load(DECLARATION)
    source = load(SOURCE)
    if declaration["format"] != 1 or len(declaration["variants"]) != 6:
        raise ValueError("location-9 declaration must contain six variants")
    delivery_wrapper = next(
        wrapper
        for wrapper in source["wrappers"]
        if wrapper["name"] == "dbcl_GetDeliverySongInfo"
    )
    if delivery_wrapper["request_kind"] != "2602" or delivery_wrapper["fixed_location"] != 9:
        raise ValueError("XDJ-RR source no longer defines Delivery Info at location 9")

    cases_by_variant = {}
    matrix = []
    golden_hashes = {}
    for entry in declaration["variants"]:
        suite = CONFORMANCE / entry["suite"]
        golden = CONFORMANCE / entry["golden"]
        observed = validate(suite, golden, MANIFEST)
        validate_receipt(entry, golden)
        if len(observed) != 6:
            raise ValueError(f"{entry['id']}: expected six cases")
        cases_by_variant[entry["id"]] = observed
        golden_hashes[entry["id"]] = sha256(golden)

        width = WIDTHS[entry["setup"]]
        for case_id, case in observed.items():
            if case["outcome"] != "menu" or case["total"] != 13:
                raise ValueError(f"{entry['id']}/{case_id}: Delivery did not return 13 rows")
            if len(case["rows"]) != 13:
                raise ValueError(f"{entry['id']}/{case_id}: row count differs")
            if {len(row["arguments"]) for row in case["rows"]} != {width}:
                raise ValueError(f"{entry['id']}/{case_id}: row width differs")
            matrix.append(
                {
                    "variant": entry["id"],
                    "model": entry["model"],
                    "setup": entry["setup"],
                    "case": case_id,
                    "outcome": case["outcome"],
                    "total": case["total"],
                    "row_width": width,
                    "rows_sha256": hashlib.sha256(
                        json.dumps(rows(case), separators=(",", ":")).encode()
                    ).hexdigest(),
                }
            )

        first = rows(observed["location-1-first-current"])
        second = rows(observed["location-9-second-current"])
        if first == second:
            raise ValueError(f"{entry['id']}: fixture tracks do not distinguish buffers")
        if rows(observed["location-2-first-current"]) != first:
            raise ValueError(f"{entry['id']}: location 2 changes current first-track rows")
        if rows(observed["location-1-first-render-stale-9"]) != second:
            raise ValueError(f"{entry['id']}: location 9 did not retain its second-track buffer")
        if rows(observed["location-9-second-render-stale-1"]) != first:
            raise ValueError(f"{entry['id']}: location 1 did not retain its first-track buffer")
        if rows(observed["location-9-first-current"]) != first:
            raise ValueError(f"{entry['id']}: location 9 current first-track rows differ")

    for setup in WIDTHS:
        reference = cases_by_variant[f"xdj-rx3-ordinary-{setup}"]
        for model in ("xdj-rx3-status", "cdj-3000-status"):
            candidate = cases_by_variant[f"{model}-{setup}"]
            for case_id in reference:
                if rows(candidate[case_id]) != rows(reference[case_id]):
                    raise ValueError(f"{model}-{setup}/{case_id}: identity changes rows")

    for model in ("xdj-rx3-ordinary", "xdj-rx3-status", "cdj-3000-status"):
        extended = cases_by_variant[f"{model}-extended"]
        legacy = cases_by_variant[f"{model}-legacy"]
        for case_id in extended:
            expected = [row[:12] for row in rows(extended[case_id])]
            if rows(legacy[case_id]) != expected:
                raise ValueError(f"{model}/{case_id}: legacy rows are not extended prefixes")

    report = {
        "format": 1,
        "scope": SCOPE,
        "source_sha256": sha256(SOURCE),
        "declaration_sha256": sha256(DECLARATION),
        "fixture_manifest_sha256": sha256(MANIFEST),
        "fixture_fingerprint": load(MANIFEST)["fixture_fingerprint"],
        "variant_count": 6,
        "case_count": 36,
        "record_repeat_execution_count": 72,
        "models": ["xdj-rx3-ordinary", "xdj-rx3-status", "cdj-3000-status"],
        "setups": WIDTHS,
        "observed": {
            "location_9_delivery_success": True,
            "location_9_total": 13,
            "location_9_buffer_independent_from_location_1": True,
            "location_2_rows_equal_location_1": True,
            "identity_rows_equal_within_setup": True,
            "legacy_rows_are_extended_prefix": True,
        },
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
