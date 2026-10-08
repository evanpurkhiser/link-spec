#!/usr/bin/env python3
"""Validate and summarize the genuine CDJ-2000nexus status matrix."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CONFORMANCE = ROOT / "conformance"
sys.path.insert(0, str(ROOT / "tools"))

from summarize_search_oracle import validate


MATRIX = CONFORMANCE / "data/cdj-2000nexus-status-matrix.json"
IDENTITY = CONFORMANCE / "runs/cdj-2000nexus-player-1-genuine-status.json"
RECORDER = CONFORMANCE / "record_cdj_2000nexus_status_matrix.sh"
OUTPUT = ROOT / "data/experiments/device-status/cdj-2000nexus/summary.json"
PARTIAL_OUTPUT = OUTPUT.with_name("summary.partial.json")
REPEATS = OUTPUT.parent / "repeats"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def signature(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def semantic_behavior(behavior: dict[str, object]) -> list[dict[str, object]]:
    return [
        {
            key: case[key]
            for key in ("id", "outcome", "total", "header", "rows")
        }
        for case in behavior["cases"]
    ]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-partial", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    matrix = json.loads(MATRIX.read_text())
    identity = json.loads(IDENTITY.read_text())
    results = []

    for variant in matrix["variants"]:
        suite = CONFORMANCE / variant["suite"]
        golden = CONFORMANCE / variant["golden"]
        reference = CONFORMANCE / variant["reference_golden"]
        fixture = CONFORMANCE / f"fixtures/generated/{variant['fixture']}/manifest.json"
        receipt_path = REPEATS / f"{variant['id']}.json"
        if not golden.is_file() or not receipt_path.is_file():
            if args.allow_partial:
                continue
            raise FileNotFoundError(
                golden if not golden.is_file() else receipt_path
            )

        cases = validate(suite, golden, fixture)
        receipt = json.loads(receipt_path.read_text())
        assert receipt["format"] == 1
        assert receipt["id"] == variant["id"]
        assert receipt["repeat_verified"] is True
        assert receipt["suite_sha256"] == sha256(suite)
        assert receipt["fixture_manifest_sha256"] == sha256(fixture)
        assert receipt["identity_sha256"] == sha256(IDENTITY)
        assert receipt["golden_sha256"] == sha256(golden)
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
                "reference_semantic_behavior_sha256": signature(
                    expected_semantic
                ),
                "semantic_reference_match": (
                    actual_semantic == expected_semantic
                ),
                "repeat_verified": True,
                "repeat_receipt_sha256": sha256(receipt_path),
                "suite_sha256": sha256(suite),
                "golden_sha256": sha256(golden),
                "reference_golden_sha256": sha256(reference),
            }
        )

    summary = {
        "scope": matrix["scope"],
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
    output = PARTIAL_OUTPUT if args.allow_partial else OUTPUT
    if not args.allow_partial:
        assert len(results) == len(matrix["variants"])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(
        f"validated {len(results)} variants / "
        f"{summary['matrix']['completed_cases']} cases; wrote {output}"
    )


if __name__ == "__main__":
    main()
