#!/usr/bin/env python3
"""Validate and compare successful payload replies across status and setup."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

try:
    from .summarize_adjacent_payload_success import summarize_success
except ImportError:
    from summarize_adjacent_payload_success import summarize_success


ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "conformance/fixtures/generated/payload-valid/manifest.json"
ASSET_MANIFEST = ROOT / "conformance/payload-assets/generated/manifest.json"
SUITE_ROOT = ROOT / "conformance/suites/generated/adjacent-payload-success-status"
GOLDEN_ROOT = ROOT / "conformance/goldens/rekordbox-7.2.19"
EVIDENCE = ROOT / "data/experiments/adjacent-payload/success-status"
OUTPUT = EVIDENCE / "summary.json"
CSV_OUTPUT = EVIDENCE / "matrix.csv"
VARIANTS = (
    ("cdj-3000-player-1-extended", "cdj-3000-status", 1, "extended"),
    ("cdj-3000-player-1-legacy", "cdj-3000-status", 1, "legacy"),
    ("xdj-rx3-player-11-extended", "xdj-rx3-status", 11, "extended"),
    ("xdj-rx3-player-11-legacy", "xdj-rx3-status", 11, "legacy"),
)


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def digest_json(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return digest_bytes(encoded)


def variant_paths(model: str, player: int, setup: str) -> tuple[Path, Path]:
    suite = SUITE_ROOT / f"player-{player}-{setup}.json"
    golden = GOLDEN_ROOT / model / f"adjacent-payload-success-{setup}.json"
    return suite, golden


def normalized_response(case: dict) -> dict:
    return {
        "outcome": case["outcome"],
        "error_kind": case["raw_response"].get("error_kind"),
        "messages": [
            {
                "kind": message["kind"],
                "arguments": message["arguments"],
            }
            for message in case["raw_response"]["messages"]
        ],
    }


def summarize_status_cross(
    variants: tuple[tuple[str, str, int, str], ...] = VARIANTS,
    validate_evidence: bool = True,
) -> tuple[dict, list[dict]]:
    variant_summaries = []
    matrix = []
    hashes_by_case: dict[str, dict[str, str]] = defaultdict(dict)

    for variant, model, player, setup in variants:
        suite_path, golden_path = variant_paths(model, player, setup)
        summary, _ = summarize_success(
            suite_path,
            MANIFEST,
            golden_path,
            ASSET_MANIFEST,
            EVIDENCE / variant if validate_evidence else None,
            variant,
            "real Rekordbox 7.2.19 adjacent payload status/setup success",
            ROOT / "conformance/runs" / (
                "cdj-3000-player-1-status.json"
                if player == 1
                else "xdj-rx3-player-11-status.json"
            ),
        )
        suite = json.loads(suite_path.read_text())
        golden = json.loads(golden_path.read_text())
        if suite["defaults"]["device"] != player:
            raise ValueError(f"{variant}: suite device does not match player")
        if suite["defaults"]["setup"] != setup:
            raise ValueError(f"{variant}: suite setup does not match variant")

        normalized_cases = []
        for declaration, case in zip(suite["cases"], golden["behavior"]["cases"], strict=True):
            packed = declaration["arguments"][0]["number"]
            if not isinstance(packed, int) or packed >> 24 != player:
                raise ValueError(f"{variant}/{case['id']}: requester byte changed")
            response = normalized_response(case)
            response_sha256 = digest_json(response)
            hashes_by_case[case["id"]][variant] = response_sha256
            normalized_cases.append({"id": case["id"], "response": response})
            matrix.append(
                {
                    "variant": variant,
                    "model": model,
                    "player": player,
                    "setup": setup,
                    "id": case["id"],
                    "kind": f"{case['request']['kind']:04x}",
                    "outcome": case["outcome"],
                    "message_kinds": " ".join(
                        f"{message['kind']:04x}"
                        for message in case["raw_response"]["messages"]
                    ),
                    "response_sha256": response_sha256,
                }
            )

        variant_summaries.append(
            {
                "variant": variant,
                "model": model,
                "player": player,
                "setup": setup,
                "suite_sha256": digest_bytes(suite_path.read_bytes()),
                "golden_sha256": digest_bytes(golden_path.read_bytes()),
                "normalized_behavior_sha256": digest_json(normalized_cases),
                "case_count": summary["case_count"],
                "successful_reply_count": summary["successful_reply_count"],
            }
        )

    expected_variants = {variant for variant, _model, _player, _setup in variants}
    comparisons = []
    for case_id, hashes in sorted(hashes_by_case.items()):
        if set(hashes) != expected_variants:
            raise ValueError(f"{case_id}: incomplete variant domain")
        comparisons.append(
            {
                "id": case_id,
                "distinct_response_count": len(set(hashes.values())),
                "response_sha256_by_variant": dict(sorted(hashes.items())),
            }
        )

    summary = {
        "format": 1,
        "scope": "real Rekordbox 7.2.19 adjacent payload status/setup success cross",
        "fixture_manifest_sha256": digest_bytes(MANIFEST.read_bytes()),
        "asset_manifest_sha256": digest_bytes(ASSET_MANIFEST.read_bytes()),
        "variant_count": len(variants),
        "case_count": len(matrix),
        "logical_case_count": len(comparisons),
        "all_responses_invariant": all(
            comparison["distinct_response_count"] == 1
            for comparison in comparisons
        ),
        "variants": variant_summaries,
        "cases": comparisons,
    }
    return summary, matrix


def main() -> None:
    summary, matrix = summarize_status_cross()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(summary, indent=2) + "\n")
    with CSV_OUTPUT.open("w", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=matrix[0].keys())
        writer.writeheader()
        writer.writerows(matrix)
    print(f"wrote {OUTPUT} and {CSV_OUTPUT}: {len(matrix)} observations")


if __name__ == "__main__":
    main()
