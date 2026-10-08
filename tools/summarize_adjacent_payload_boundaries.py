#!/usr/bin/env python3
"""Validate and reduce the real-Rekordbox payload parser-boundary matrix."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

try:
    from .summarize_adjacent_payload_fileless import summarize, write_json
except ImportError:
    from summarize_adjacent_payload_fileless import summarize, write_json
try:
    from .rekordbox_health import validate_health_pair
except ImportError:
    from rekordbox_health import validate_health_pair


ROOT = Path(__file__).resolve().parent.parent
CONFORMANCE = ROOT / "conformance"
INDEX = CONFORMANCE / "data/adjacent-payload-boundary-matrix.json"
FIXTURE = CONFORMANCE / "fixtures/generated/payload-valid/manifest.json"
GOLDENS = CONFORMANCE / "goldens/rekordbox-7.2.19/xdj-rx3/adjacent-payload-boundaries"
EVIDENCE = ROOT / "data/experiments/adjacent-payload/boundaries"
OUTPUT = EVIDENCE / "summary.json"
CSV_OUTPUT = EVIDENCE / "matrix.csv"
SCOPE = "real Rekordbox 7.2.19 adjacent payload parser boundaries"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path):
    return json.loads(path.read_text())


def validate_asset_capture(path: Path, manifest: dict) -> None:
    observed = sorted(load(path), key=lambda item: item["path"])
    expected = sorted(manifest["assets"], key=lambda item: item["path"])
    if observed != expected:
        raise ValueError(f"{path}: guest asset capture differs from manifest")


def validate_receipt(
    receipt_path: Path,
    entry: dict,
    suite_path: Path,
    asset_manifest_path: Path,
    golden_path: Path,
) -> None:
    receipt = load(receipt_path)
    evidence = receipt_path.parent
    expected = {
        "scope": SCOPE,
        "variant": entry["name"],
        "suite_sha256": sha256(suite_path),
        "fixture_manifest_sha256": sha256(FIXTURE),
        "asset_manifest_sha256": sha256(asset_manifest_path),
        "identity_sha256": sha256(CONFORMANCE / "runs/xdj-rx3-player-11.json"),
        "golden_sha256": sha256(golden_path),
        "case_count": entry["case_count"],
        "service_count": entry["service_count"],
        "exact_repeat": True,
    }
    for key, value in expected.items():
        if receipt.get(key) != value:
            raise ValueError(f"{receipt_path}: {key} differs from expected value")

    bound_files = {
        "staged_assets_sha256": "staged-assets.json",
        "record_assets_sha256": "record-assets.json",
        "repeat_assets_sha256": "repeat-assets.json",
        "record_health_before_sha256": "record-health-before.json",
        "record_health_after_sha256": "record-health-after.json",
        "repeat_health_before_sha256": "repeat-health-before.json",
        "repeat_health_after_sha256": "repeat-health-after.json",
    }
    for field, name in bound_files.items():
        path = evidence / name
        if receipt.get(field) != sha256(path):
            raise ValueError(f"{receipt_path}: {field} does not bind {name}")

    asset_manifest = load(asset_manifest_path)
    for name in ("staged-assets.json", "record-assets.json", "repeat-assets.json"):
        validate_asset_capture(evidence / name, asset_manifest)
    validate_health_pair(
        evidence,
        receipt,
        f"adjacent-payload-success-{entry['name']}",
        sha256,
    )


def response_details(case: dict) -> dict:
    raw = case["raw_response"]
    messages = raw.get("messages", [])
    blobs = [
        argument.get("hex", "")
        for message in messages
        for argument in message.get("arguments", [])
        if argument.get("type") == "blob"
    ]
    numbers = [
        argument.get("value")
        for message in messages
        for argument in message.get("arguments", [])
        if argument.get("type") == "number"
    ]
    signature = {
        "outcome": case["outcome"],
        "error_kind": raw.get("error_kind"),
        "messages": messages,
    }
    return {
        "message_kinds": " ".join(f"{message['kind']:04x}" for message in messages),
        "blob_count": len(blobs),
        "blob_bytes": sum(len(value) // 2 for value in blobs),
        "numbers": " ".join(str(value) for value in numbers),
        "response_sha256": hashlib.sha256(
            json.dumps(signature, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
    }


def summarize_boundaries() -> tuple[dict, list[dict]]:
    index = load(INDEX)
    if index["format"] != 1 or index["variant_count"] != len(index["variants"]):
        raise ValueError("boundary declaration index is inconsistent")

    matrix = []
    family_counts = Counter()
    axis_signatures: dict[str, set[str]] = defaultdict(set)
    for entry in index["variants"]:
        variant = entry["name"]
        suite_path = CONFORMANCE / entry["suite"]
        asset_manifest_path = CONFORMANCE / entry["asset_manifest"]
        golden_path = GOLDENS / f"{variant}.json"
        receipt_path = EVIDENCE / "variants" / variant / "receipt.json"

        if sha256(suite_path) != entry["suite_sha256"]:
            raise ValueError(f"{variant}: suite hash differs from declaration index")
        if sha256(asset_manifest_path) != entry["asset_manifest_sha256"]:
            raise ValueError(f"{variant}: asset hash differs from declaration index")

        _summary, rows = summarize(
            suite_path,
            FIXTURE,
            golden_path,
            expected_case_count=entry["case_count"],
            expected_service_count=entry["service_count"],
            scope=SCOPE,
            enforce_expected_oracle=False,
        )
        validate_receipt(receipt_path, entry, suite_path, asset_manifest_path, golden_path)
        golden = load(golden_path)
        observed = {case["id"]: case for case in golden["behavior"]["cases"]}

        family_counts[entry["family"]] += len(rows)
        for row in rows:
            details = response_details(observed[row["id"]])
            combined = {
                "variant": variant,
                "family": entry["family"],
                "axis": entry["axis"],
                "value": entry["value"],
                **row,
                **details,
            }
            matrix.append(combined)
            axis_signatures[entry["axis"]].add(details["response_sha256"])

    expected_cases = sum(entry["case_count"] for entry in index["variants"])
    if len(matrix) != expected_cases:
        raise ValueError("reduced boundary case count differs from declaration index")

    outcome_counts = Counter(row["outcome"] for row in matrix)
    summary = {
        "format": 1,
        "scope": SCOPE,
        "index_sha256": sha256(INDEX),
        "fixture_manifest_sha256": sha256(FIXTURE),
        "variant_count": len(index["variants"]),
        "case_count": len(matrix),
        "family_case_counts": dict(sorted(family_counts.items())),
        "outcome_counts": dict(sorted(outcome_counts.items())),
        "axis_distinct_response_counts": {
            axis: len(signatures) for axis, signatures in sorted(axis_signatures.items())
        },
        "independently_repeated_variants": len(index["variants"]),
    }
    return summary, matrix


def write_csv(path: Path, matrix: list[dict]) -> None:
    fields = (
        "variant", "family", "axis", "value", "id", "kind", "outcome",
        "raw_bytes", "decoded_bytes", "message_kinds", "error_kind",
        "blob_count", "blob_bytes", "numbers", "response_sha256",
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    candidate = path.with_name(f"{path.name}.next")
    with candidate.open("w", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        writer.writerows({field: row.get(field) for field in fields} for row in matrix)
    candidate.replace(path)


def main() -> None:
    summary, matrix = summarize_boundaries()
    write_json(OUTPUT, summary)
    write_csv(CSV_OUTPUT, matrix)
    print(f"wrote {OUTPUT} and {CSV_OUTPUT}: {len(matrix)} cases")


if __name__ == "__main__":
    main()
