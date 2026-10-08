#!/usr/bin/env python3
"""Validate and summarize the real-Rekordbox Hot Cue Bank pagination oracle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from summarize_search_oracle import validate


ROOT = Path(__file__).resolve().parent.parent
CONFORMANCE = ROOT / "conformance"
SUITE = CONFORMANCE / "suites/hot-cue-bank-pagination.json"
GOLDEN = (
    CONFORMANCE
    / "goldens/rekordbox-7.2.19/xdj-rx3/hot-cue-bank-pagination.json"
)
FIXTURE = CONFORMANCE / "fixtures/generated/hot-cue-bank-pagination/manifest.json"
BUILDER = CONFORMANCE / "build_fixture.py"
RECORDER = CONFORMANCE / "record_hot_cue_bank_pagination.sh"
OUTPUT = ROOT / "data/experiments/hot-cue-bank/pagination/summary.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def content_ids(case: dict[str, object]) -> list[int]:
    return [row["arguments"][1]["value"] for row in case["rows"]]


def main() -> None:
    cases = validate(SUITE, GOLDEN, FIXTURE)
    expected = list(range(40001, 40071))

    for case_id in (
        "one-row-pages",
        "automatic-32-row-pages",
        "explicit-three-pages",
    ):
        assert content_ids(cases[case_id]) == expected

    expected_windows = {
        "first-page": expected[:32],
        "first-boundary-cross": expected[31:33],
        "second-page": expected[32:64],
        "second-boundary-cross": expected[63:65],
        "tail-page": expected[64:],
        "final-row": expected[-1:],
        "zero-count": expected[:1],
        "at-end": expected[-1:],
        "past-end": expected[-1:],
        "overrun": expected[-10:],
        "overlap": expected[:3] + expected[2:5],
    }
    for case_id, window in expected_windows.items():
        assert content_ids(cases[case_id]) == window

    assert cases["maximum-offset"]["outcome"] == "render_timeout"
    assert cases["maximum-offset"]["total"] == 70
    assert content_ids(cases["maximum-offset"]) == []

    manifest = json.loads(FIXTURE.read_text())
    summary = {
        "scope": "real Rekordbox 7.2.19 only; backend comparison is deferred",
        "fixture": {
            "profile": "hot-cue-bank-pagination",
            "database_sha256": manifest["database_sha256"],
            "fixture_fingerprint": manifest["fixture_fingerprint"],
            "track_count": manifest["track_count"],
            "bank_id": manifest["ids"]["hotcue.bank.large"],
        },
        "capture": {
            "model": "XDJ-RX3",
            "player": 11,
            "case_count": len(cases),
            "immediate_repeat": "exact",
        },
        "observations": {
            "catalog_total": 70,
            "complete_walks": {
                "page_sizes": [1, 32],
                "explicit_windows": [[0, 32], [32, 32], [64, 6]],
                "content_ids": expected,
            },
            "boundary_windows": {
                case_id: content_ids(cases[case_id])
                for case_id in expected_windows
            },
            "zero_count": "coerced to one row at offset zero",
            "end_and_past_end": "clamped to the final row",
            "overrun": "right-aligned to the final requested-count rows",
            "overlap": "shared rows are emitted once per requested window",
            "maximum_unsigned_offset": "render timeout with catalog total retained",
        },
        "sha256": {
            "builder": sha256(BUILDER),
            "suite": sha256(SUITE),
            "recorder": sha256(RECORDER),
            "golden": sha256(GOLDEN),
            "fixture_manifest": sha256(FIXTURE),
        },
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(f"validated {len(cases)} real-Rekordbox cases; wrote {OUTPUT}")


if __name__ == "__main__":
    main()
