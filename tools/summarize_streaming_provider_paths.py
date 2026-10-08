#!/usr/bin/env python3
"""Reduce production-shaped provider-path authority without replacing it."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from summarize_search_oracle import load, validate


ROOT = Path(__file__).resolve().parent.parent
CONFORMANCE = ROOT / "conformance"
SUITE = CONFORMANCE / "suites/generated/streaming-provider-paths.json"
FIXTURE = CONFORMANCE / "fixtures/generated/streaming-provider-paths/manifest.json"
GOLDEN = (
    CONFORMANCE
    / "goldens/rekordbox-7.2.19/xdj-rx3/streaming-provider-paths.json"
)
STATIC = ROOT / "data/static-analysis/streaming-provider-registry.json"
EVIDENCE = ROOT / "data/experiments/streaming-provider-paths"
SUMMARY = EVIDENCE / "summary.json"
MATRIX = EVIDENCE / "matrix.csv"

ORDINARY_CASES = (
    "collection-default",
    "collection-key-sort",
    "file-name",
    "ordinary-playlist",
    "smart-playlist",
    "search",
)
STATIC_VISIBLE = (11001, 11005, 11006, 11007, 11008, 11009, 11010)
STATIC_FILTERED = (11002, 11003, 11004)
ALL = tuple(range(11001, 11011))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def content_ids(case: dict[str, object]) -> tuple[int, ...]:
    return tuple(int(row["arguments"][1]["value"]) for row in case["rows"])


def main() -> None:
    cases = validate(SUITE, GOLDEN, FIXTURE)
    observed = {case_id: content_ids(cases[case_id]) for case_id in cases}
    conflicts = []
    for case_id in ORDINARY_CASES:
        if set(observed[case_id]) != set(STATIC_VISIBLE):
            conflicts.append(
                {
                    "case": case_id,
                    "prediction": list(STATIC_VISIBLE),
                    "observed": list(observed[case_id]),
                }
            )
    if observed["history"] != ALL:
        conflicts.append(
            {
                "case": "history",
                "prediction": list(ALL),
                "observed": list(observed["history"]),
            }
        )

    manifest = load(FIXTURE)
    static = load(STATIC)
    report = {
        "format": "rekordbox-streaming-provider-paths-v1",
        "oracle": {
            "backend": "rekordbox",
            "version": "7.2.19",
            "case_count": len(cases),
            "restart_repeat_verified": True,
        },
        "fixture": {
            "profile": manifest["profile"],
            "version": manifest["fixture_version"],
            "track_count": manifest["track_count"],
            "database_sha256": manifest["database_sha256"],
            "fixture_fingerprint": manifest["fixture_fingerprint"],
            "manifest_sha256": sha256(FIXTURE),
        },
        "observed_content_ids": {
            case_id: list(content_ids_) for case_id, content_ids_ in observed.items()
        },
        "static_prediction": {
            "visible_content_ids": list(STATIC_VISIBLE),
            "filtered_content_ids": list(STATIC_FILTERED),
            "history_content_ids": list(ALL),
            "provider_registry_sha256": sha256(STATIC),
            "beatport_predicate": static["beatport_path_predicate"],
        },
        "static_prediction_conflicts": conflicts,
        "artifacts": {
            "suite_sha256": sha256(SUITE),
            "golden_sha256": sha256(GOLDEN),
        },
    }
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    SUMMARY.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    with MATRIX.open("w", newline="") as output:
        writer = csv.writer(output)
        writer.writerow(("case", "ordinal", "content_id"))
        for case_id, content_ids_ in observed.items():
            for ordinal, content_id in enumerate(content_ids_, start=1):
                writer.writerow((case_id, ordinal, content_id))
    print(SUMMARY)
    print(MATRIX)


if __name__ == "__main__":
    main()
