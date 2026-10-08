#!/usr/bin/env python3
"""Validate and summarize the packed track-type Hot Cue Bank oracle."""

from __future__ import annotations

import json
from pathlib import Path

from summarize_search_oracle import load, sha256, validate


ROOT = Path(__file__).resolve().parent.parent
CONFORMANCE = ROOT / "conformance"
SUITE = CONFORMANCE / "suites/context-hot-cue-track-types.json"
GOLDEN = (
    CONFORMANCE
    / "goldens/rekordbox-7.2.19/xdj-rx3/context-hot-cue-track-types.json"
)
MANIFEST = CONFORMANCE / "fixtures/generated/hot-cue-banks/manifest.json"
EVIDENCE = ROOT / "data/experiments/packed-context/hot-cue-cross"
OUTPUT = EVIDENCE / "summary.json"

TRACK_TYPES = range(0x07)
SUPPORTED_TYPE = 0x01
REQUESTS = {
    "tree-root": 3,
    "alpha-tracks": 8,
    "empty-tracks": 0,
}


def assert_health(phase: str) -> dict[str, object]:
    before_path = EVIDENCE / f"{phase}-before.json"
    after_path = EVIDENCE / f"{phase}-after.json"
    before = load(before_path)
    after = load(after_path)

    assert before["rekordbox_process_count"] == 1
    assert after["rekordbox_process_count"] == 1
    assert before["application_events"] == []
    assert after["application_events"] == []
    assert before["rekordbox_processes"][0]["responding"] is True
    assert after["rekordbox_processes"][0]["responding"] is True
    assert before["rekordbox_processes"][0]["id"] == after["rekordbox_processes"][0]["id"]

    return {
        "process_id": after["rekordbox_processes"][0]["id"],
        "responsive_before": True,
        "responsive_after": True,
        "application_events": 0,
        "before_sha256": sha256(before_path),
        "after_sha256": sha256(after_path),
    }


def main() -> None:
    cases = validate(SUITE, GOLDEN, MANIFEST)
    assert len(cases) == len(tuple(TRACK_TYPES)) * len(REQUESTS) == 21

    results: list[dict[str, object]] = []
    for label, supported_total in REQUESTS.items():
        per_type: dict[str, dict[str, object]] = {}
        for track_type in TRACK_TYPES:
            case = cases[f"type-{track_type:02x}--{label}"]
            assert case["request"]["kind"] == 0x2001
            assert case["request"]["arguments"][0]["value"] == 0x01010300 | track_type
            assert case["header"][0]["kind"] == 0x4000

            if track_type == SUPPORTED_TYPE:
                assert case["outcome"] == "menu"
                assert case["total"] == supported_total
                assert len(case["rows"]) == supported_total
                assert len(case["pages"]) == (1 if supported_total else 0)
            else:
                assert case["outcome"] == "render_timeout"
                assert case["total"] == 50
                assert case["rows"] == []
                assert len(case["pages"]) == 1
                page = case["pages"][0]
                assert page["outcome"] == "timeout"
                assert page["transport_error_kind"] == "WouldBlock"
                assert page["requested"] == 32
                assert page["received"] == 0
                assert page["messages"] == []

            per_type[f"0x{track_type:02x}"] = {
                "outcome": case["outcome"],
                "header_kind": "0x4000",
                "total": case["total"],
                "rows": len(case["rows"]),
            }

        results.append(
            {
                "name": label,
                "supported_total": supported_total,
                "per_type": per_type,
            }
        )

    report = {
        "schema_version": 1,
        "product": "rekordbox 7.2.19",
        "request_kind": "0x2001",
        "context_bytes": {
            "requester": "0x01",
            "menu_location": "0x01",
            "media_slot": "0x03",
            "track_types": [f"0x{value:02x}" for value in TRACK_TYPES],
        },
        "observed": {
            "cases": len(cases),
            "supported_track_type": "0x01",
            "other_type_header_total": 50,
            "other_type_render_requested": 32,
            "other_type_render_received": 0,
            "other_type_timeout_kind": "WouldBlock",
            "request_results": results,
        },
        "health": {
            "record": assert_health("record"),
            "repeat": assert_health("repeat"),
        },
        "artifacts": {
            "generator_sha256": sha256(
                CONFORMANCE / "generate_context_hot_cue_track_type_suite.py"
            ),
            "suite_sha256": sha256(SUITE),
            "golden_sha256": sha256(GOLDEN),
            "fixture_fingerprint": load(MANIFEST)["fixture_fingerprint"],
        },
    }

    OUTPUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(OUTPUT)


if __name__ == "__main__":
    main()
