#!/usr/bin/env python3
"""Reduce the adjacent-payload missing, empty, and null path oracle."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

try:
    from .summarize_adjacent_payload_fileless import sha256, summarize, write_csv, write_json
except ImportError:
    from summarize_adjacent_payload_fileless import sha256, summarize, write_csv, write_json
try:
    from .rekordbox_health import validate_health_pair
except ImportError:
    from rekordbox_health import validate_health_pair


ROOT = Path(__file__).resolve().parent.parent
SUITE = ROOT / "conformance/suites/adjacent-payload-missing-files.json"
MANIFEST = ROOT / "conformance/fixtures/generated/payload-paths/manifest.json"
GOLDEN = (
    ROOT
    / "conformance/goldens/rekordbox-7.2.19/xdj-rx3/adjacent-payload-missing-files.json"
)
EVIDENCE = ROOT / "data/experiments/adjacent-payload/missing-files"
IDENTITY = ROOT / "conformance/runs/xdj-rx3-player-11.json"
OUTPUT = EVIDENCE / "summary.json"
CSV_OUTPUT = EVIDENCE / "matrix.csv"


def summarize_missing_files(
    suite_path: Path = SUITE,
    manifest_path: Path = MANIFEST,
    golden_path: Path = GOLDEN,
    evidence_path: Path | None = None,
) -> tuple[dict, list[dict]]:
    suite = json.loads(suite_path.read_text())
    summary, matrix = summarize(
        suite_path,
        manifest_path,
        golden_path,
        expected_case_count=31,
        expected_service_count=10,
        scope="real Rekordbox 7.2.19 adjacent payload missing files",
        enforce_expected_oracle=False,
    )

    declared = {case["id"]: case for case in suite["cases"]}
    states = Counter()
    kinds = Counter()
    for row in matrix:
        identifier = row["id"]
        declaration = declared[identifier]
        state = identifier.split("--path-", 1)[1]
        states[state] += 1
        kinds[row["kind"]] += 1

        if declaration["fresh_connection"] is not True:
            raise ValueError(f"{identifier}: request does not require a fresh connection")

    if states != Counter({"nonempty-missing": 10, "empty": 10, "null": 10,
                          "playlist-nonempty-missing": 1}):
        raise ValueError(f"unexpected path-state matrix: {dict(states)}")
    if kinds["2003"] != 4 or set(kinds.values()) != {3, 4}:
        raise ValueError(f"unexpected per-service matrix: {dict(kinds)}")

    summary["path_state_counts"] = dict(sorted(states.items()))
    if evidence_path is not None:
        receipt_path = evidence_path / "receipt.json"
        receipt = json.loads(receipt_path.read_text())
        expected = {
            "format": 1,
            "scope": "real Rekordbox 7.2.19 adjacent payload missing files",
            "suite_sha256": sha256(suite_path),
            "fixture_manifest_sha256": sha256(manifest_path),
            "identity_sha256": sha256(IDENTITY),
            "golden_sha256": sha256(golden_path),
            "case_count": 31,
            "service_count": 10,
            "exact_repeat": True,
        }
        for field, value in expected.items():
            if receipt.get(field) != value:
                raise ValueError(f"missing-file receipt {field} differs")
        summary["post_request_health"] = validate_health_pair(
            evidence_path,
            receipt,
            "adjacent-payload-missing-files",
            sha256,
        )
        summary["receipt_sha256"] = sha256(receipt_path)
    return summary, matrix


def main() -> None:
    summary, matrix = summarize_missing_files(evidence_path=EVIDENCE)
    write_json(OUTPUT, summary)
    write_csv(CSV_OUTPUT, matrix)
    print(f"wrote {OUTPUT} and {CSV_OUTPUT}: {len(matrix)} cases")


if __name__ == "__main__":
    main()
