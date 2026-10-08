#!/usr/bin/env python3
"""Reduce successful generated-asset payload responses from real Rekordbox."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

try:
    from .summarize_adjacent_payload_fileless import summarize, write_csv, write_json
except ImportError:
    from summarize_adjacent_payload_fileless import summarize, write_csv, write_json
try:
    from .rekordbox_health import validate_health_pair
except ImportError:
    from rekordbox_health import validate_health_pair


ROOT = Path(__file__).resolve().parent.parent
SUITE = ROOT / "conformance/suites/adjacent-payload-success.json"
MANIFEST = ROOT / "conformance/fixtures/generated/payload-valid/manifest.json"
ASSET_MANIFEST = ROOT / "conformance/payload-assets/generated/manifest.json"
GOLDEN = (
    ROOT
    / "conformance/goldens/rekordbox-7.2.19/xdj-rx3/adjacent-payload-success.json"
)
EVIDENCE = ROOT / "data/experiments/adjacent-payload/success"
OUTPUT = EVIDENCE / "summary.json"
CSV_OUTPUT = EVIDENCE / "matrix.csv"
REPLIES = {
    "2003": 0x4002,
    "2103": 0x4002,
    "2004": 0x4402,
    "2204": 0x4602,
    "2504": 0x4502,
    "2804": 0x4000,
    "2904": 0x4A02,
    "2a04": 0x4C02,
    "2c04": 0x4F02,
    "2d04": 0x4F02,
}


def sha256(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


def summarize_success(
    suite_path: Path = SUITE,
    manifest_path: Path = MANIFEST,
    golden_path: Path = GOLDEN,
    asset_manifest_path: Path = ASSET_MANIFEST,
    evidence_path: Path | None = None,
    variant: str = "baseline",
    scope: str = "real Rekordbox 7.2.19 generated adjacent payload success",
    identity_path: Path = ROOT / "conformance/runs/xdj-rx3-player-11.json",
) -> tuple[dict, list[dict]]:
    summary, matrix = summarize(
        suite_path,
        manifest_path,
        golden_path,
        expected_case_count=15,
        expected_service_count=10,
        scope="real Rekordbox 7.2.19 generated adjacent payload success",
        enforce_expected_oracle=False,
    )
    golden = json.loads(golden_path.read_text())
    observed = golden["behavior"]["cases"]
    kinds = Counter()
    payload_bytes_by_case = {}

    for case in observed:
        kind = f"{case['request']['kind']:04x}"
        kinds[kind] += 1
        messages = case["raw_response"]["messages"]
        if case["outcome"] != "raw_reply" or len(messages) != 1:
            raise ValueError(f"{case['id']}: success must contain one direct reply")
        if messages[0]["kind"] != REPLIES[kind]:
            raise ValueError(f"{case['id']}: unexpected success reply kind")
        payload_bytes_by_case[case["id"]] = sum(
            len(argument.get("hex", "")) // 2
            for argument in messages[0]["arguments"]
            if argument.get("type") == "blob"
        )

    if kinds["2003"] != 2 or kinds["2c04"] != 3 or kinds["2d04"] != 3:
        raise ValueError(f"unexpected success service matrix: {dict(kinds)}")
    if set(kinds) != set(REPLIES):
        raise ValueError(f"success service domain changed: {sorted(kinds)}")

    summary["asset_manifest_sha256"] = sha256(asset_manifest_path)
    summary["successful_reply_count"] = len(observed)
    summary["payload_bearing_reply_count"] = sum(
        byte_count > 0 for byte_count in payload_bytes_by_case.values()
    )
    summary["empty_payload_reply_count"] = sum(
        byte_count == 0 for byte_count in payload_bytes_by_case.values()
    )
    summary["payload_bytes_by_case"] = payload_bytes_by_case
    if evidence_path is not None:
        receipt_path = evidence_path / "receipt.json"
        receipt = json.loads(receipt_path.read_text())
        expected = {
            "format": 1,
            "scope": scope,
            "variant": variant,
            "suite_sha256": sha256(suite_path),
            "fixture_manifest_sha256": sha256(manifest_path),
            "asset_manifest_sha256": sha256(asset_manifest_path),
            "identity_sha256": sha256(identity_path),
            "golden_sha256": sha256(golden_path),
            "case_count": 15,
            "service_count": 10,
            "exact_repeat": True,
        }
        for field, value in expected.items():
            if receipt.get(field) != value:
                raise ValueError(f"{variant}: receipt {field} differs")
        asset_manifest = json.loads(asset_manifest_path.read_text())["assets"]
        expected_assets = sorted(asset_manifest, key=lambda item: item["path"])
        for name in ("staged-assets.json", "record-assets.json", "repeat-assets.json"):
            path = evidence_path / name
            field = name.replace("-", "_").replace(".json", "_sha256")
            if receipt.get(field) != sha256(path):
                raise ValueError(f"{variant}: receipt does not bind {name}")
            if sorted(json.loads(path.read_text()), key=lambda item: item["path"]) != expected_assets:
                raise ValueError(f"{variant}: {name} differs from asset manifest")
        summary["post_request_health"] = validate_health_pair(
            evidence_path,
            receipt,
            f"adjacent-payload-success-{variant}",
            sha256,
        )
        summary["receipt_sha256"] = sha256(receipt_path)
    return summary, matrix


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", type=Path, default=SUITE)
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    parser.add_argument("--golden", type=Path, default=GOLDEN)
    parser.add_argument("--asset-manifest", type=Path, default=ASSET_MANIFEST)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--csv", type=Path, default=CSV_OUTPUT)
    args = parser.parse_args()

    summary, matrix = summarize_success(
        args.suite,
        args.manifest,
        args.golden,
        args.asset_manifest,
        EVIDENCE,
    )
    write_json(args.output, summary)
    write_csv(args.csv, matrix)
    print(
        f"wrote {args.output} and {args.csv}: "
        f"{len(matrix)} successful replies"
    )


if __name__ == "__main__":
    main()
