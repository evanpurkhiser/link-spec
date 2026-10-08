#!/usr/bin/env python3
"""Validate and summarize the corroborating XDJ-XZ status matrix."""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CONFORMANCE = ROOT / "conformance"
sys.path.insert(0, str(ROOT / "tools"))

from summarize_search_oracle import validate


MATRIX = CONFORMANCE / "data/xdj-xz-corroborating-status-matrix.json"
IDENTITY = CONFORMANCE / "runs/xdj-xz-player-1-corroborating-status.json"
RECORDER = CONFORMANCE / "record_xdj_xz_corroborating_status_matrix.sh"
OUTPUT = ROOT / "data/experiments/device-status/xdj-xz-corroborating/summary.json"
REPEATS = OUTPUT.parent / "repeats"
HEALTH_FIELDS = (
    "record_health_before_sha256",
    "record_health_after_sha256",
    "repeat_health_before_sha256",
    "repeat_health_after_sha256",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def signature(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def semantic_behavior(behavior: dict[str, object]) -> list[dict[str, object]]:
    return [
        {key: case[key] for key in ("id", "outcome", "total", "header", "rows")}
        for case in behavior["cases"]
    ]


def main() -> None:
    matrix = json.loads(MATRIX.read_text())
    identity = json.loads(IDENTITY.read_text())
    assert identity["status_provenance"] == "corroborating-fixture"
    results = []

    for variant in matrix["variants"]:
        suite = CONFORMANCE / variant["suite"]
        golden = CONFORMANCE / variant["golden"]
        reference = CONFORMANCE / variant["reference_golden"]
        fixture = CONFORMANCE / f"fixtures/generated/{variant['fixture']}/manifest.json"
        evidence = REPEATS / variant["id"]
        receipt_path = evidence / "receipt.json"

        cases = validate(suite, golden, fixture)
        receipt = json.loads(receipt_path.read_text())
        assert receipt["format"] == 1
        assert receipt["id"] == variant["id"]
        assert receipt["status_provenance"] == "corroborating-fixture"
        assert receipt["repeat_verified"] is True
        assert receipt["suite_sha256"] == sha256(suite)
        assert receipt["fixture_manifest_sha256"] == sha256(fixture)
        assert receipt["identity_sha256"] == sha256(IDENTITY)
        assert receipt["golden_sha256"] == sha256(golden)
        for field in HEALTH_FIELDS:
            health = evidence / f"{field.removesuffix('_sha256').replace('_', '-')}.json"
            assert receipt[field] == sha256(health)

        expected_behavior = json.loads(reference.read_text())["behavior"]
        actual_behavior = json.loads(golden.read_text())["behavior"]
        expected_semantic = semantic_behavior(expected_behavior)
        actual_semantic = semantic_behavior(actual_behavior)
        outcomes = Counter(case["outcome"] for case in cases.values())
        results.append(
            {
                **variant,
                "cases": len(cases),
                "outcomes": dict(sorted(outcomes.items())),
                "behavior_sha256": signature(actual_behavior),
                "reference_behavior_sha256": signature(expected_behavior),
                "exact_reference_match": actual_behavior == expected_behavior,
                "semantic_behavior_sha256": signature(actual_semantic),
                "reference_semantic_behavior_sha256": signature(expected_semantic),
                "semantic_reference_match": actual_semantic == expected_semantic,
                "repeat_verified": True,
                "repeat_receipt_sha256": sha256(receipt_path),
                "suite_sha256": sha256(suite),
                "golden_sha256": sha256(golden),
                "reference_golden_sha256": sha256(reference),
            }
        )

    summary = {
        "scope": matrix["scope"],
        "provenance_limit": (
            "The exact packet is retained from a physical XDJ-XZ parser fixture; "
            "the unpublished parent capture prevents captured-verbatim classification."
        ),
        "identity": identity,
        "matrix": {
            "declared_variants": len(matrix["variants"]),
            "completed_variants": len(results),
            "declared_cases": sum(
                len(json.loads((CONFORMANCE / item["suite"]).read_text())["cases"])
                for item in matrix["variants"]
            ),
            "completed_cases": sum(result["cases"] for result in results),
            "exact_reference_matches": sum(
                result["exact_reference_match"] for result in results
            ),
            "semantic_reference_matches": sum(
                result["semantic_reference_match"] for result in results
            ),
            "repeat_verified_variants": sum(
                result["repeat_verified"] for result in results
            ),
        },
        "results": results,
        "sha256": {
            "matrix": sha256(MATRIX),
            "identity": sha256(IDENTITY),
            "status_packet": identity["status_packet_sha256"],
            "recorder": sha256(RECORDER),
        },
    }
    assert len(results) == len(matrix["variants"])
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(f"validated {len(results)} variants / {summary['matrix']['completed_cases']} cases; wrote {OUTPUT}")


if __name__ == "__main__":
    main()
