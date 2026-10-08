#!/usr/bin/env python3
"""Validate and summarize FolderPath-based Link Export visibility."""

from __future__ import annotations

import json
from pathlib import Path

from summarize_search_oracle import load, sha256, validate


ROOT = Path(__file__).resolve().parent.parent
CONFORMANCE = ROOT / "conformance"
SUITE = CONFORMANCE / "suites/generated/link-visibility.json"
FIXTURE = CONFORMANCE / "fixtures/generated/link-visibility/manifest.json"
GOLDEN = (
    CONFORMANCE
    / "goldens/rekordbox-7.2.19/xdj-rx3/link-visibility.json"
)
REPLAY = (
    CONFORMANCE
    / "results/rbxport/c144f19+tree.80e87ec8aace/summary.json"
)
VISIBLE = (10001, 10003, 10004, 10008, 10009, 10010, 10011, 10012, 10013, 10014)
FILTERED = (10002, 10005, 10006, 10007)
ALL = tuple(range(10001, 10015))
SAME_MEMBERSHIP_CASES = (
    "collection-default",
    "collection-key-sort",
    "file-name",
    "ordinary-playlist",
    "smart-playlist",
    "search",
)


def content_ids(case: dict[str, object]) -> tuple[int, ...]:
    return tuple(
        int(row["arguments"][1]["value"])
        for row in case["rows"]
    )


def main() -> None:
    cases = validate(SUITE, GOLDEN, FIXTURE)
    for case_id in SAME_MEMBERSHIP_CASES:
        assert set(content_ids(cases[case_id])) == set(VISIBLE), case_id
    for case_id in (
        "collection-default",
        "file-name",
        "ordinary-playlist",
        "smart-playlist",
        "search",
    ):
        assert content_ids(cases[case_id]) == VISIBLE, case_id
    assert content_ids(cases["history"]) == ALL

    replay = load(REPLAY)
    replay_result = next(
        result for result in replay["suites"] if result["suite"] == "link-visibility"
    )
    assert replay_result["cases"] == 7
    manifest = load(FIXTURE)
    report = {
        "format": "rekordbox-link-export-visibility-v1",
        "oracle": {
            "backend": "rekordbox",
            "version": "7.2.19",
            "cases": 7,
            "restart_repeat_verified": True,
        },
        "fixture": {
            "profile": manifest["profile"],
            "version": manifest["fixture_version"],
            "database_sha256": manifest["database_sha256"],
            "fixture_fingerprint": manifest["fixture_fingerprint"],
            "manifest_sha256": sha256(FIXTURE),
            "track_count": manifest["track_count"],
        },
        "behavior": {
            "visible_content_ids": VISIBLE,
            "filtered_content_ids": FILTERED,
            "filtered_paths": {
                "10002": "soundcloud:tracks:fixture-2",
                "10005": "tidal:tracks:fixture-5",
                "10006": "spotify:track:fixture-6",
                "10007": "apple-music:tracks:fixture-7",
            },
            "nonmatching_provider_syntax_controls": {
                "10003": "beatport:tracks:fixture-3",
                "10004": "beatsource:tracks:fixture-4",
            },
            "false_positive_controls_visible": {
                "10008": "unknown:tracks:fixture-8",
                "10009": "SOUNDCLOUD:TRACKS:fixture-9",
                "10010": "Z:/tracks/soundcloud:tracks:fixture-10.wav",
                "10011": "soundcloudish:tracks:fixture-11",
                "10012": "",
                "10013": None,
            },
            "same_filtered_membership_cases": SAME_MEMBERSHIP_CASES,
            "history_content_ids": ALL,
        },
        "static_evidence": {
            "predicate_disassembly": "data/static-analysis/link-export-visibility.disasm.txt",
            "predicate_disassembly_sha256": sha256(
                ROOT / "data/static-analysis/link-export-visibility.disasm.txt"
            ),
            "direct_xrefs": "data/static-analysis/link-export-visibility-xrefs.txt",
            "direct_xrefs_sha256": sha256(
                ROOT / "data/static-analysis/link-export-visibility-xrefs.txt"
            ),
            "provider_registry": "data/static-analysis/streaming-provider-registry.json",
            "provider_registry_sha256": sha256(
                ROOT / "data/static-analysis/streaming-provider-registry.json"
            ),
        },
        "artifacts": {
            "suite_sha256": sha256(SUITE),
            "golden_sha256": sha256(GOLDEN),
            "diagnostic_invalid_smart_golden_sha256": sha256(
                ROOT
                / "data/experiments/link-visibility/diagnostic-v1-invalid-smart/golden.json"
            ),
        },
        "rbxport": {
            "version": replay["backend_version"],
            "exact": len(replay_result["exact_cases"]),
            "same_outcome_total_row_count": len(
                replay_result["same_outcome_total_row_count_cases"]
            ),
            "different": len(replay_result["different_cases"]),
        },
    }
    output = ROOT / "data/experiments/link-visibility/summary.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(output)


if __name__ == "__main__":
    main()
