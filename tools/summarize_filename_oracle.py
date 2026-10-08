#!/usr/bin/env python3
"""Validate and summarize File Name category boundary behavior."""

from __future__ import annotations

import json
from pathlib import Path

from summarize_search_oracle import load, sha256, validate


ROOT = Path(__file__).resolve().parent.parent
CONFORMANCE = ROOT / "conformance"
GOLDEN = CONFORMANCE / "goldens/rekordbox-7.2.19/xdj-rx3/filename-boundaries.json"
MANIFEST = CONFORMANCE / "fixtures/generated/filename-boundaries/manifest.json"
RESULT = CONFORMANCE / "results/rbxport/c144f19+tree.80e87ec8aace/summary.json"


def utf16_units(value: str) -> int:
    return len(value.encode("utf-16-le", errors="surrogatepass")) // 2


def rows_by_id(case: dict[str, object]) -> dict[int, dict[str, object]]:
    return {row["arguments"][1]["value"]: row for row in case["rows"]}


def label(row: dict[str, object]) -> str:
    return row["arguments"][3]["value"]


def main() -> None:
    cases = validate(
        CONFORMANCE / "suites/filename-boundaries.json",
        GOLDEN,
        MANIFEST,
    )
    default = cases["sort-00-default"]
    rows = rows_by_id(default)

    assert [row["arguments"][1]["value"] for row in default["rows"]] == [
        30003,
        30004,
        30013,
        30014,
        30010,
        30006,
        30008,
        30012,
        30007,
        30015,
        30016,
        30017,
        30005,
        30009,
        30011,
        30018,
        30019,
        30020,
        30001,
        30002,
    ]
    assert label(rows[30001]) == label(rows[30002]) == ""
    assert label(rows[30003]) == "A.wav"
    assert label(rows[30004]) == "a.WAV"
    assert label(rows[30005]) == ".hidden"
    assert label(rows[30006]) == "multi.part.name.flac"
    assert label(rows[30007]) == "trailing."
    assert label(rows[30008]) == "no-extension"
    assert label(rows[30009]) == "\u00e9.wav"
    assert label(rows[30010]) == "e\u0301.wav"
    assert label(rows[30011]) == "\U0001f642.wav"
    assert label(rows[30012]) == "nul"
    assert label(rows[30013]) == "C:\\embedded\\name.wav"
    assert label(rows[30014]) == "dir/name.wav"
    assert label(rows[30015]) == "x" * 254
    assert label(rows[30016]) == "x" * 255
    assert label(rows[30017]) == "x" * 255
    assert label(rows[30018]) == "\U0001f642" * 127
    assert label(rows[30019]) == ("\U0001f642" * 127) + "a"
    assert label(rows[30020]) == ("\U0001f642" * 127) + "\ufffd"

    for row in rows.values():
        assert row["arguments"][2]["value"] == 2 * (utf16_units(label(row)) + 1)

    canonical_labels = {item_id: label(row) for item_id, row in rows.items()}
    orders = []
    for case in cases.values():
        assert case["total"] == 20
        assert {item_id: label(row) for item_id, row in rows_by_id(case).items()} == canonical_labels
        orders.append(tuple(row["arguments"][1]["value"] for row in case["rows"]))
    assert len(set(orders)) == 9

    replay = load(RESULT)
    filename = next(
        suite for suite in replay["suites"] if suite["suite"] == "filename-boundaries"
    )
    assert filename["cases"] == 18
    assert len(filename["exact_cases"]) == 0
    assert len(filename["same_outcome_total_row_count_cases"]) == 18

    report = {
        "format": "rekordbox-link-export-filename-v1",
        "oracle": {
            "cases": 18,
            "golden_sha256": sha256(GOLDEN),
            "suite_sha256": sha256(CONFORMANCE / "suites/filename-boundaries.json"),
            "sort_order_classes": 9,
        },
        "fixture": {
            "profile": "filename-boundaries",
            "database_sha256": load(MANIFEST)["database_sha256"],
            "fingerprint": load(MANIFEST)["fixture_fingerprint"],
        },
        "behavior": {
            "source_column": "FileNameL",
            "path_separators_are_literal": True,
            "extension_is_preserved": True,
            "embedded_nul_truncates": True,
            "null_and_empty_render_empty": True,
            "maximum_output_utf16_units": 255,
            "split_surrogate_becomes_replacement_character": True,
            "all_sort_ids_preserve_filename_primary": True,
        },
        "rbxport": {
            "version": replay["backend_version"],
            "cases": filename["cases"],
            "exact": len(filename["exact_cases"]),
            "same_outcome_total_row_count": len(
                filename["same_outcome_total_row_count_cases"]
            ),
        },
    }
    output = ROOT / "data/experiments/filename/summary.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(output)


if __name__ == "__main__":
    main()
