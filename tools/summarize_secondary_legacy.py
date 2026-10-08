#!/usr/bin/env python3
"""Validate persisted secondary columns across extended and legacy row widths."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CONFORMANCE = ROOT / "conformance"
sys.path.insert(0, str(ROOT / "tools"))

from summarize_search_oracle import validate


VARIANTS = (
    "artist",
    "album",
    "bpm",
    "rating",
    "genre",
    "comment",
    "time",
    "remixer",
    "label",
    "original-artist",
    "key",
    "bitrate",
    "color",
    "play-count",
    "date-added",
)
IDENTITY = CONFORMANCE / "runs/xdj-rx3-player-11.json"
GOLDENS = CONFORMANCE / "goldens/rekordbox-7.2.19/xdj-rx3"
EVIDENCE = ROOT / "data/experiments/secondary-column-legacy"
REPEATS = EVIDENCE / "repeats"
OUTPUT = EVIDENCE / "summary.json"
PARTIAL_OUTPUT = EVIDENCE / "summary.partial.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assert_legacy_prefix(
    extended: dict[str, object], legacy: dict[str, object]
) -> None:
    assert legacy["outcome"] == extended["outcome"]
    assert legacy["total"] == extended["total"]
    assert len(legacy["rows"]) == len(extended["rows"])
    for extended_row, legacy_row in zip(
        extended["rows"], legacy["rows"], strict=True
    ):
        assert legacy_row["kind"] == extended_row["kind"]
        assert len(extended_row["arguments"]) == 16
        assert len(legacy_row["arguments"]) == 12
        assert legacy_row["arguments"] == extended_row["arguments"][:12]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-partial", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    results = []
    pending = []
    for variant in VARIANTS:
        fixture = CONFORMANCE / f"fixtures/generated/secondary-{variant}/manifest.json"
        extended_suite = CONFORMANCE / f"suites/generated/secondary-{variant}.json"
        legacy_suite = CONFORMANCE / f"suites/generated/secondary-{variant}-legacy.json"
        extended_golden = GOLDENS / f"secondary-{variant}.json"
        legacy_golden = GOLDENS / f"secondary-{variant}-legacy.json"
        receipt_path = REPEATS / f"secondary-{variant}-legacy.json"
        if not legacy_golden.is_file() or not receipt_path.is_file():
            pending.append(variant)
            if args.allow_partial:
                continue
            raise FileNotFoundError(
                legacy_golden if not legacy_golden.is_file() else receipt_path
            )

        extended = validate(extended_suite, extended_golden, fixture)
        legacy = validate(legacy_suite, legacy_golden, fixture)
        assert extended.keys() == legacy.keys() == {"sort-menu", "track-rows"}
        for case_id in extended:
            assert_legacy_prefix(extended[case_id], legacy[case_id])

        receipt = json.loads(receipt_path.read_text())
        assert receipt["format"] == 1
        assert receipt["id"] == f"secondary-{variant}-legacy"
        assert receipt["repeat_verified"] is True
        assert receipt["suite_sha256"] == sha256(legacy_suite)
        assert receipt["fixture_manifest_sha256"] == sha256(fixture)
        assert receipt["identity_sha256"] == sha256(IDENTITY)
        assert receipt["golden_sha256"] == sha256(legacy_golden)

        track = legacy["track-rows"]
        first = track["rows"][0]["arguments"]
        results.append(
            {
                "variant": variant,
                "cases": 2,
                "rows": sum(len(case["rows"]) for case in legacy.values()),
                "exact_12_field_prefix": True,
                "first_track_argument_0": first[0],
                "first_track_argument_5": first[5],
                "first_track_argument_6": first[6],
                "fixture_manifest_sha256": sha256(fixture),
                "extended_golden_sha256": sha256(extended_golden),
                "legacy_golden_sha256": sha256(legacy_golden),
                "repeat_receipt_sha256": sha256(receipt_path),
            }
        )

    document = {
        "scope": "real Rekordbox 7.2.19 only; backend comparison is deferred",
        "model": "XDJ-RX3",
        "player": 11,
        "extended_argument_count": 16,
        "legacy_argument_count": 12,
        "declared_variants": len(VARIANTS),
        "completed_variants": len(results),
        "repeat_verified_variants": len(results),
        "pending": pending,
        "all_rows_exact_prefixes": len(results) == len(VARIANTS),
        "results": results,
        "sha256": {
            "identity": sha256(IDENTITY),
            "recorder": sha256(CONFORMANCE / "record_secondary_legacy_matrix.sh"),
        },
    }
    output = PARTIAL_OUTPUT if args.allow_partial else OUTPUT
    if not args.allow_partial:
        assert not pending
        assert len(results) == len(VARIANTS)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n")
    print(f"validated {len(results)} persisted secondary legacy variants; wrote {output}")


if __name__ == "__main__":
    main()
