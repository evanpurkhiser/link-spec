#!/usr/bin/env python3
"""Validate and summarize the packed track-type Song Info oracle."""

from __future__ import annotations

import json
from pathlib import Path

from summarize_search_oracle import load, sha256, validate


ROOT = Path(__file__).resolve().parent.parent
CONFORMANCE = ROOT / "conformance"
SUITE = CONFORMANCE / "suites/context-analysis-track-types.json"
GOLDEN = (
    CONFORMANCE
    / "goldens/rekordbox-7.2.19/xdj-rx3/context-analysis-track-types.json"
)
MANIFEST = CONFORMANCE / "fixtures/generated/full/manifest.json"
EVIDENCE = ROOT / "data/experiments/packed-context/analysis-cross"
STATIC = ROOT / "data/static-analysis/context-track-type-routing.disasm.txt"
OUTPUT = EVIDENCE / "summary.json"

TRACK_TYPES = range(0x07)
SUPPORTED_TYPE = 0x01
REQUESTS = {
    "display": (0x2002, 16),
    "play": (0x2102, 7),
    "recognized-22": (0x2202, None),
    "recognized-23": (0x2302, None),
    "recognized-24": (0x2402, None),
    "recognized-25": (0x2502, None),
    "delivery": (0x2602, 13),
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
    assert len(cases) == len(tuple(TRACK_TYPES)) * len(REQUESTS) == 49

    results: list[dict[str, object]] = []
    for label, (request_kind, supported_total) in REQUESTS.items():
        per_type: dict[str, dict[str, object]] = {}
        for track_type in TRACK_TYPES:
            case = cases[f"type-{track_type:02x}--{label}"]
            assert case["request"]["kind"] == request_kind
            assert case["request"]["arguments"][0]["value"] == 0x01010300 | track_type

            if supported_total is None:
                assert case["outcome"] == "error"
                assert case["header"][0]["kind"] == 0x4003
                assert case["header"][0]["arguments"][0]["value"] == request_kind
                assert case["total"] is None
                assert case["pages"] == []
                assert case["rows"] == []
            elif track_type == SUPPORTED_TYPE:
                assert case["outcome"] == "menu"
                assert case["header"][0]["kind"] == 0x4000
                assert case["total"] == supported_total
                assert len(case["rows"]) == supported_total
                assert len(case["pages"]) == 1
            else:
                assert case["outcome"] == "error"
                assert case["header"][0]["kind"] == 0x4000
                assert case["total"] == 0xFFFFFFFF
                assert case["pages"] == []
                assert case["rows"] == []

            per_type[f"0x{track_type:02x}"] = {
                "outcome": case["outcome"],
                "header_kind": f"0x{case['header'][0]['kind']:04x}",
                "total": case["total"],
                "rows": len(case["rows"]),
            }

        results.append(
            {
                "name": label,
                "request_kind": f"0x{request_kind:04x}",
                "per_type": per_type,
            }
        )

    report = {
        "schema_version": 1,
        "product": "rekordbox 7.2.19",
        "request_class": "0x2xxx Song Info commands",
        "context_bytes": {
            "requester": "0x01",
            "menu_location": "0x01",
            "media_slot": "0x03",
            "track_types": [f"0x{value:02x}" for value in TRACK_TYPES],
        },
        "observed": {
            "cases": len(cases),
            "supported_track_type": "0x01",
            "display_play_delivery_other_type_total": "0xffffffff",
            "recognized_22_through_25_header": "0x4003",
            "no_pre_dispatch_timeouts": True,
            "request_results": results,
        },
        "static_analysis": {
            "path": str(STATIC.relative_to(ROOT)),
            "sha256": sha256(STATIC),
            "dispatcher": "PSvDBMain::OnClientReq",
            "address": "0x102521340",
            "analysis_dispatch": "PSvDBMain::OnMAnlzClientCmd",
        },
        "health": {
            "record": assert_health("record"),
            "repeat": assert_health("repeat"),
        },
        "artifacts": {
            "generator_sha256": sha256(
                CONFORMANCE / "generate_context_analysis_track_type_suite.py"
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
