#!/usr/bin/env python3
"""Validate and summarize the real-Rekordbox BPM tolerance edge oracle."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CONFORMANCE = ROOT / "conformance"
sys.path.insert(0, str(ROOT / "tools"))

from summarize_search_oracle import validate


FIXTURE = CONFORMANCE / "fixtures/generated/bpm-tolerance-boundaries/manifest.json"
SUITE = CONFORMANCE / "suites/bpm-tolerance-boundaries.json"
GOLDEN = (
    CONFORMANCE
    / "goldens/rekordbox-7.2.19/xdj-rx3/bpm-tolerance-boundaries.json"
)
OUTPUT = ROOT / "data/experiments/bpm-tolerance-boundaries/summary.json"
SELECTED_BPM = 12_000


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def case_item_ids(case: dict[str, object]) -> list[int]:
    return [row["arguments"][1]["value"] for row in case["rows"]]


def edge_points(percent: int) -> dict[str, int]:
    if percent == 0:
        rounded_bpm = (SELECTED_BPM + 50) // 100 * 100
        return {
            "lower_minus_one": rounded_bpm - 51,
            "lower_exact": rounded_bpm - 50,
            "lower_plus_one": rounded_bpm - 49,
            "selected": SELECTED_BPM,
            "upper_minus_one": rounded_bpm + 48,
            "upper_exact": rounded_bpm + 49,
            "upper_plus_one": rounded_bpm + 50,
        }

    lower = SELECTED_BPM * (100 - percent) // 100
    upper = SELECTED_BPM * (100 + percent) // 100
    return {
        "lower_minus_one": lower - 1,
        "lower_exact": lower,
        "lower_plus_one": lower + 1,
        "upper_minus_one": upper - 1,
        "upper_exact": upper,
        "upper_plus_one": upper + 1,
    }


def main() -> None:
    fixture = json.loads(FIXTURE.read_text())
    cases = validate(SUITE, GOLDEN, FIXTURE)
    id_to_bpm = {
        int(track_id): int(name.removeprefix("track.bpm_"))
        for name, track_id in fixture["ids"].items()
        if name.startswith("track.bpm_")
    }
    assert fixture["profile"] == "bpm-tolerance-boundaries"
    assert fixture["track_count"] == 43
    assert len(id_to_bpm) == 43
    assert set(cases) == {f"tolerance-{percent}" for percent in range(7)}

    results = []
    previous_ids: set[int] = set()
    for percent in range(7):
        case = cases[f"tolerance-{percent}"]
        item_ids = case_item_ids(case)
        assert case["outcome"] == "menu"
        assert case["total"] == len(item_ids)
        assert len(item_ids) == len(set(item_ids))
        assert set(item_ids).issubset(id_to_bpm)
        assert previous_ids.issubset(item_ids)

        bpms = [id_to_bpm[item_id] for item_id in item_ids]
        points = edge_points(percent)
        results.append(
            {
                "percent": percent,
                "total": len(item_ids),
                "item_ids": item_ids,
                "bpms": bpms,
                "edge_inclusion": {
                    name: {"bpm": bpm, "included": bpm in bpms}
                    for name, bpm in points.items()
                },
            }
        )
        previous_ids = set(item_ids)

    summary = {
        "format": 1,
        "scope": "real Rekordbox 7.2.19 only; backend comparison is deferred",
        "selected_bpm": SELECTED_BPM,
        "fixture": {
            "profile": fixture["profile"],
            "track_count": fixture["track_count"],
            "database_sha256": fixture["database_sha256"],
            "fixture_fingerprint": fixture["fixture_fingerprint"],
        },
        "cases": len(results),
        "nested_result_sets": True,
        "results": results,
        "sha256": {
            "fixture_manifest": sha256(FIXTURE),
            "suite": sha256(SUITE),
            "golden": sha256(GOLDEN),
            "recorder": sha256(
                CONFORMANCE / "record_bpm_tolerance_boundaries.sh"
            ),
        },
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    candidate = OUTPUT.with_suffix(".json.next")
    candidate.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    candidate.replace(OUTPUT)
    print(f"validated {len(results)} BPM tolerance cases; wrote {OUTPUT}")


if __name__ == "__main__":
    main()
