#!/usr/bin/env python3
"""Validate and summarize the packed track-type list-family oracle."""

from __future__ import annotations

import json
from pathlib import Path

from summarize_search_oracle import load, sha256, validate


ROOT = Path(__file__).resolve().parent.parent
CONFORMANCE = ROOT / "conformance"
SOURCE = CONFORMANCE / "suites/full.json"
SUITE = CONFORMANCE / "suites/context-track-type-families.json"
GOLDEN = (
    CONFORMANCE
    / "goldens/rekordbox-7.2.19/xdj-rx3/context-track-type-families.json"
)
MANIFEST = CONFORMANCE / "fixtures/generated/full/manifest.json"
EVIDENCE = ROOT / "data/experiments/packed-context/family-cross"
STATIC = ROOT / "data/static-analysis/context-track-type-routing.disasm.txt"
OUTPUT = EVIDENCE / "summary.json"

TRACK_TYPES = range(0x07)
SUCCESS_TYPES = (0x00, 0x01, 0x02, 0x05, 0x06)
TIMEOUT_TYPES = (0x03, 0x04)


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
    source = load(SOURCE)
    source_cases = {case["id"]: case for case in source["cases"]}
    assert len(source_cases) == 47
    assert len(cases) == len(source_cases) * len(tuple(TRACK_TYPES)) == 329

    type_counts: dict[str, dict[str, int]] = {}
    for track_type in TRACK_TYPES:
        selected = [
            case
            for case_id, case in cases.items()
            if case_id.startswith(f"type-{track_type:02x}--")
        ]
        type_counts[f"0x{track_type:02x}"] = {
            "menus": sum(case["outcome"] == "menu" for case in selected),
            "errors": sum(case["outcome"] == "error" for case in selected),
            "timeouts": sum(case["outcome"] == "timeout" for case in selected),
        }

    family_results: list[dict[str, object]] = []
    argument_7_cases: set[str] = set()
    argument_7_rows: dict[str, int] = {}
    argument_10_cases: set[str] = set()
    argument_10_rows = 0
    shape_deltas: list[dict[str, object]] = []

    for family_id, declaration in source_cases.items():
        family = {
            track_type: cases[f"type-{track_type:02x}--{family_id}"]
            for track_type in TRACK_TYPES
        }

        for track_type in TIMEOUT_TYPES:
            case = family[track_type]
            assert case["outcome"] == "timeout"
            assert case["transport_error_kind"] == "WouldBlock"
            assert case["header"] == []
            assert case["pages"] == []
            assert case["rows"] == []
            assert case["total"] is None

        baseline = family[0x00]
        baseline_rows = row_values(baseline)
        per_type_deltas: dict[str, dict[str, int]] = {}

        for track_type in SUCCESS_TYPES:
            if track_type == 0:
                continue

            case = family[track_type]
            assert case["outcome"] == baseline["outcome"]
            rows = row_values(case)

            if case["total"] != baseline["total"]:
                assert track_type == 0x01
                assert family_id in ("root", "search")
                assert baseline["total"] == 0
                assert baseline_rows == []
                shape_deltas.append(
                    {
                        "id": family_id,
                        "other_successful_total": baseline["total"],
                        "type_01_total": case["total"],
                        "type_01_row_count": len(rows),
                    }
                )
                continue

            assert len(rows) == len(baseline_rows)
            argument_7_count = 0
            argument_10_count = 0
            for ordinary, observed in zip(baseline_rows, rows, strict=True):
                changed = [
                    index
                    for index, pair in enumerate(zip(ordinary, observed, strict=True))
                    if pair[0] != pair[1]
                ]
                assert set(changed) <= {7, 10}

                if 7 in changed:
                    assert ordinary[7] & 0xFF000000 == 0
                    assert observed[7] == ordinary[7] | (track_type << 24)
                    argument_7_count += 1

                if 10 in changed:
                    assert track_type == 0x01
                    assert ordinary[10] == 0
                    assert observed[10] == 0x100
                    argument_10_count += 1

            if argument_7_count:
                argument_7_cases.add(family_id)
                argument_7_rows[f"0x{track_type:02x}"] = (
                    argument_7_rows.get(f"0x{track_type:02x}", 0)
                    + argument_7_count
                )
            if argument_10_count:
                argument_10_cases.add(family_id)
                argument_10_rows += argument_10_count

            per_type_deltas[f"0x{track_type:02x}"] = {
                "argument_7_rows": argument_7_count,
                "argument_10_rows": argument_10_count,
            }

        if family_id in ("root", "search"):
            assert family_id in ("root", "search")
            family_results.append(
                {
                    "id": family_id,
                    "request_kind": declaration["request_kind"],
                    "outcome": baseline["outcome"],
                    "other_successful_total": baseline["total"],
                    "type_01_total": family[0x01]["total"],
                    "other_successful_row_count": len(baseline_rows),
                    "type_01_row_count": len(row_values(family[0x01])),
                    "per_type_row_deltas": per_type_deltas,
                }
            )
            continue

        family_results.append(
            {
                "id": family_id,
                "request_kind": declaration["request_kind"],
                "outcome": baseline["outcome"],
                "total": baseline["total"],
                "row_count": len(baseline_rows),
                "per_type_row_deltas": per_type_deltas,
            }
        )

    report = {
        "schema_version": 1,
        "product": "rekordbox 7.2.19",
        "request_class": "0x1xxx list commands",
        "context_bytes": {
            "requester": "0x01",
            "menu_location": "0x01",
            "media_slot": "0x03",
            "track_types": [f"0x{value:02x}" for value in TRACK_TYPES],
        },
        "observed": {
            "cases": len(cases),
            "menu_families": len(source_cases),
            "type_counts": type_counts,
            "successful_types": [f"0x{value:02x}" for value in SUCCESS_TYPES],
            "timeout_types": [f"0x{value:02x}" for value in TIMEOUT_TYPES],
            "argument_7_case_ids": sorted(argument_7_cases),
            "argument_7_changed_rows_by_type": argument_7_rows,
            "argument_10_case_ids": sorted(argument_10_cases),
            "type_01_argument_10_changed_rows": argument_10_rows,
            "type_01_shape_deltas": shape_deltas,
            "only_changed_row_arguments": [7, 10],
            "ordinary_argument_10": "0x00000000",
            "type_01_argument_10": "0x00000100",
            "family_results": family_results,
        },
        "static_analysis": {
            "path": str(STATIC.relative_to(ROOT)),
            "sha256": sha256(STATIC),
            "dispatcher": "PSvDBMain::OnClientReq",
            "address": "0x102521340",
            "list_dispatch": "PSvDBMain::OnListClientCmd",
            "list_dispatch_address": "0x101d2bb80",
        },
        "health": {
            "record": assert_health("record"),
            "repeat": assert_health("repeat"),
        },
        "artifacts": {
            "generator_sha256": sha256(
                CONFORMANCE / "generate_context_track_type_family_suite.py"
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
