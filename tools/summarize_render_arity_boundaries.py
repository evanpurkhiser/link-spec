#!/usr/bin/env python3
"""Validate and summarize track-render argument-count boundaries."""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CONFORMANCE = ROOT / "conformance"
sys.path.insert(0, str(ROOT / "tools"))

from rekordbox_health import validate_health_pair
from summarize_search_oracle import validate


SUITE = CONFORMANCE / "suites/generated/render-arity-boundaries.json"
FIXTURE = CONFORMANCE / "fixtures/generated/full/manifest.json"
IDENTITY = CONFORMANCE / "runs/xdj-rx3-player-11.json"
GOLDEN = CONFORMANCE / "goldens/rekordbox-7.2.19/xdj-rx3/render-arity-boundaries.json"
EVIDENCE = ROOT / "data/experiments/render-arity-boundaries"
RECEIPT = EVIDENCE / "receipt.json"
SUMMARY = EVIDENCE / "summary.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def page_outcomes(case: dict) -> list[str]:
    return [page.get("outcome", "menu") for page in case.get("pages", [])]


def main() -> None:
    suite = json.loads(SUITE.read_text())
    receipt = json.loads(RECEIPT.read_text())
    cases = validate(SUITE, GOLDEN, FIXTURE)
    declarations = {case["id"]: case for case in suite["cases"]}

    assert receipt["format"] == 1
    assert receipt["scope"] == "real Rekordbox 7.2.19 track render arity boundaries"
    assert receipt["variant"] == "render-arity-boundaries"
    assert receipt["case_count"] == len(suite["cases"]) == 70
    assert receipt["service_count"] == 1
    assert receipt["exact_repeat"] is True
    assert receipt["suite_sha256"] == sha256(SUITE)
    assert receipt["fixture_manifest_sha256"] == sha256(FIXTURE)
    assert receipt["identity_sha256"] == sha256(IDENTITY)
    assert receipt["golden_sha256"] == sha256(GOLDEN)
    health = validate_health_pair(
        EVIDENCE, receipt, "adjacent-payload-render-arity-boundaries", sha256
    )

    summaries = []
    outcomes = Counter()
    arity_outcomes: dict[int, Counter] = defaultdict(Counter)
    row_count = 0
    for case_id, case in cases.items():
        declaration = declarations[case_id]
        arity = 3 + len(declaration["render_arguments"])
        sort_id = declaration["arguments"][1]["number"]
        pages = case.get("pages", [])
        for page in pages:
            assert len(page["arguments"]) == arity

        observed_page_outcomes = page_outcomes(case)
        outcome = case["outcome"]
        outcomes[outcome] += 1
        arity_outcomes[arity][outcome] += 1
        row_count += len(case.get("rows", []))
        summaries.append(
            {
                "id": case_id,
                "sort_id": sort_id,
                "render_argument_count": arity,
                "outcome": outcome,
                "total": case.get("total"),
                "row_count": len(case.get("rows", [])),
                "page_outcomes": observed_page_outcomes,
                "page_argument_counts": [
                    len(page["arguments"]) for page in pages
                ],
            }
        )

    summary = {
        "scope": "real Rekordbox 7.2.19 only; backend comparison is deferred",
        "model": "XDJ-RX3",
        "player": 11,
        "fixture_profile": "full",
        "case_count": len(summaries),
        "row_count": row_count,
        "exact_repeat": True,
        "post_request_health": health,
        "outcomes": dict(sorted(outcomes.items())),
        "outcomes_by_arity": {
            str(arity): dict(sorted(counts.items()))
            for arity, counts in sorted(arity_outcomes.items())
        },
        "cases": summaries,
        "sha256": {
            "suite": sha256(SUITE),
            "fixture_manifest": sha256(FIXTURE),
            "identity": sha256(IDENTITY),
            "golden": sha256(GOLDEN),
            "receipt": sha256(RECEIPT),
        },
    }
    SUMMARY.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(f"validated {len(summaries)} cases and {row_count} rows")


if __name__ == "__main__":
    main()
