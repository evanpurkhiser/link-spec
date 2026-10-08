#!/usr/bin/env python3
"""Validate Hot Cue Bank list-buffer lifetime across device disconnect."""

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


FIXTURE = CONFORMANCE / "fixtures/generated/hot-cue-banks/manifest.json"
WARMUP_SUITE = CONFORMANCE / "suites/hot-cue-bank-buffer-disconnect-warmup.json"
POST_SUITE = CONFORMANCE / "suites/hot-cue-bank-buffer-disconnect-post.json"
EVIDENCE = ROOT / "data/experiments/hot-cue-bank/buffer-disconnect"
OUTPUT = EVIDENCE / "summary.json"
PARTIAL_OUTPUT = EVIDENCE / "summary.partial.json"
MODES = ("control", "rejoin")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def item_ids(case: dict[str, object]) -> list[int]:
    return [row["arguments"][1]["value"] for row in case["rows"]]


def stale_classification(case: dict[str, object]) -> str:
    if case["outcome"] == "menu" and case["total"] == 1 and item_ids(case) == [9002]:
        return "persisted"
    if (
        case["outcome"] == "render_timeout"
        and case["total"] == 1
        and not case["rows"]
    ):
        return "cleared"
    raise AssertionError(
        f"unexpected stale-buffer shape: outcome={case['outcome']!r}, "
        f"total={case['total']!r}, item_ids={item_ids(case)!r}"
    )


def parse_run(mode: str, run: int) -> dict[str, object] | None:
    warmup_path = EVIDENCE / f"{mode}-run-{run}-warmup.json"
    post_path = EVIDENCE / f"{mode}-run-{run}-post.json"
    if not warmup_path.is_file() or not post_path.is_file():
        return None

    warmup = validate(WARMUP_SUITE, warmup_path, FIXTURE)
    post = validate(POST_SUITE, post_path, FIXTURE)
    assert set(warmup) == {"prime-location-1-root"}
    assert set(post) == {
        "beta-header-render-old-location-1",
        "beta-header-render-current-location-2",
    }
    root = warmup["prime-location-1-root"]
    stale = post["beta-header-render-old-location-1"]
    current = post["beta-header-render-current-location-2"]
    assert root["outcome"] == "menu" and root["total"] == 3
    assert item_ids(root) == [9002, 9001, 9003]
    assert current["outcome"] == "menu" and current["total"] == 1
    assert item_ids(current) == [9032]
    return {
        "run": run,
        "old_location_state": stale_classification(stale),
        "old_location_outcome": stale["outcome"],
        "old_location_item_ids": item_ids(stale),
        "current_location_outcome": current["outcome"],
        "current_location_item_ids": item_ids(current),
        "behavior_signature": digest(
            {
                "warmup": warmup,
                "post": post,
            }
        ),
        "warmup_sha256": sha256(warmup_path),
        "post_sha256": sha256(post_path),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-partial", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    results = []
    pending = []
    for mode in MODES:
        runs = [parse_run(mode, run) for run in (1, 2)]
        if any(run is None for run in runs):
            pending.append(mode)
            if args.allow_partial:
                continue
            raise FileNotFoundError(f"incomplete buffer-disconnect mode: {mode}")
        first, second = runs
        assert first is not None and second is not None
        assert first["behavior_signature"] == second["behavior_signature"]
        results.append(
            {
                "mode": mode,
                "old_location_state": first["old_location_state"],
                "repeat_verified": True,
                "runs": runs,
            }
        )

    by_mode = {result["mode"]: result for result in results}
    if "control" in by_mode:
        assert by_mode["control"]["old_location_state"] == "persisted"

    fixture = json.loads(FIXTURE.read_text())
    summary = {
        "scope": "real Rekordbox 7.2.19 only; backend comparison is deferred",
        "fixture": {
            "profile": fixture["profile"],
            "database_sha256": fixture["database_sha256"],
            "fixture_fingerprint": fixture["fixture_fingerprint"],
        },
        "absence_seconds": 40,
        "completed_modes": len(results),
        "pending_modes": pending,
        "results": results,
        "sha256": {
            "fixture_manifest": sha256(FIXTURE),
            "warmup_suite": sha256(WARMUP_SUITE),
            "post_suite": sha256(POST_SUITE),
            "recorder": sha256(
                CONFORMANCE / "record_hot_cue_bank_buffer_disconnect.sh"
            ),
        },
    }
    output = PARTIAL_OUTPUT if args.allow_partial else OUTPUT
    if not args.allow_partial:
        assert not pending and len(results) == len(MODES)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(f"validated {len(results)} modes; wrote {output}")


if __name__ == "__main__":
    main()
