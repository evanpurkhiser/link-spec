#!/usr/bin/env python3
"""Validate and summarize the exhaustive packed track-type-byte oracle."""

from __future__ import annotations

import json
from pathlib import Path

from summarize_search_oracle import load, sha256, validate


ROOT = Path(__file__).resolve().parent.parent
CONFORMANCE = ROOT / "conformance"
SUITE = CONFORMANCE / "suites/context-track-types.json"
GOLDEN = (
    CONFORMANCE
    / "goldens/rekordbox-7.2.19/xdj-rx3/context-track-types.json"
)
MANIFEST = CONFORMANCE / "fixtures/generated/full/manifest.json"
EVIDENCE = ROOT / "data/experiments/packed-context/track-types"
STATIC = ROOT / "data/static-analysis/context-track-type.disasm.txt"
OUTPUT = EVIDENCE / "summary.json"

KNOWN_TYPES = {
    0x00: "no track",
    0x01: "rekordbox track",
    0x02: "unanalyzed track",
    0x05: "audio CD track",
    0x06: "streaming track",
}
TIMEOUT_TYPES = {0x03, 0x04}


def row_values(case: dict[str, object]) -> list[list[object]]:
    return [
        [argument["value"] for argument in row["arguments"]]
        for row in case["rows"]
    ]


def assert_health(phase: str) -> dict[str, object]:
    before_path = EVIDENCE / f"{phase}-before.json"
    after_path = EVIDENCE / f"{phase}-after.json"
    before = load(before_path)
    after = load(after_path)

    assert before["rekordbox_process_count"] == 1
    assert after["rekordbox_process_count"] == 1
    assert len(before["application_events"]) == 0
    assert len(after["application_events"]) == 0
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
    assert len(cases) == 0x100
    assert set(cases) == {f"track-type-{value:02x}" for value in range(0x100)}

    successful: list[int] = []
    timed_out: list[int] = []
    baseline_rows: list[list[object]] | None = None

    for track_type in range(0x100):
        case = cases[f"track-type-{track_type:02x}"]
        context = 0x01010300 | track_type
        assert case["request"]["arguments"][0]["value"] == context

        if track_type in TIMEOUT_TYPES:
            assert case["outcome"] == "timeout"
            assert case["transport_error_kind"] == "WouldBlock"
            assert case["header"] == []
            assert case["pages"] == []
            assert case["rows"] == []
            assert case["total"] is None
            timed_out.append(track_type)
            continue

        assert case["outcome"] == "menu"
        assert case["total"] == 8
        assert len(case["rows"]) == 8
        assert len(case["pages"]) == 1
        assert case["pages"][0]["arguments"][0]["value"] == context
        successful.append(track_type)

        rows = row_values(case)
        flags = [row[10] for row in rows]
        if track_type == 0x01:
            assert flags == [0x100] * 8
            continue

        assert flags == [0] * 8
        if baseline_rows is None:
            baseline_rows = rows
        else:
            assert rows == baseline_rows

    assert successful == [value for value in range(0x100) if value not in TIMEOUT_TYPES]
    assert timed_out == sorted(TIMEOUT_TYPES)
    assert baseline_rows is not None

    type_one_rows = row_values(cases["track-type-01"])
    for ordinary, rekordbox in zip(baseline_rows, type_one_rows, strict=True):
        changed = [index for index, pair in enumerate(zip(ordinary, rekordbox, strict=True)) if pair[0] != pair[1]]
        assert changed == [10]
        assert ordinary[10] == 0
        assert rekordbox[10] == 0x100

    report = {
        "schema_version": 1,
        "product": "rekordbox 7.2.19",
        "request_kind": "0x1004",
        "context_bytes": {
            "requester": "0x01",
            "menu_location": "0x01",
            "media_slot": "0x03",
            "track_type_domain": "0x00..0xff",
        },
        "known_client_meanings": {
            f"0x{value:02x}": meaning for value, meaning in KNOWN_TYPES.items()
        },
        "observed": {
            "cases": len(cases),
            "successful_menus": len(successful),
            "timeouts": [f"0x{value:02x}" for value in timed_out],
            "successful_total": 8,
            "successful_row_count": 8,
            "track_type_01_argument_10": "0x00000100",
            "other_successful_argument_10": "0x00000000",
            "all_other_row_fields_identical": True,
        },
        "static_analysis": {
            "path": str(STATIC.relative_to(ROOT)),
            "sha256": sha256(STATIC),
            "track_handler": "0x101d2c6c0",
            "appsync_track_root": "0x1016bc8e0",
            "row_renderer": "0x100f9fe40",
            "render_dispatch": "0x100fa1110",
        },
        "health": {
            "record": assert_health("record"),
            "repeat": assert_health("repeat"),
        },
        "artifacts": {
            "generator_sha256": sha256(
                CONFORMANCE / "generate_context_track_type_suite.py"
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
