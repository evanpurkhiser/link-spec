#!/usr/bin/env python3
"""Validate and summarize the RX3 sort plus six-argument render oracle."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CONFORMANCE = ROOT / "conformance"
sys.path.insert(0, str(ROOT / "tools"))

from rekordbox_health import validate_health_pair
from summarize_search_oracle import validate


SUITE = CONFORMANCE / "suites/generated/sort-secondary-render-6.json"
FIXTURE = CONFORMANCE / "fixtures/generated/full/manifest.json"
IDENTITY = CONFORMANCE / "runs/xdj-rx3-player-11.json"
GOLDEN = CONFORMANCE / "goldens/rekordbox-7.2.19/xdj-rx3/sort-secondary-render-6.json"
EVIDENCE = ROOT / "data/experiments/sort-secondary-render-6"
RECEIPT = EVIDENCE / "receipt.json"
SUMMARY = EVIDENCE / "summary.json"
MATRIX = EVIDENCE / "rows.csv"
EXPECTED_ALPHA_ONE = {
    "00-default": (5001, "Am - 120.0 bpm", 0x0F04),
    "01-alphabet": (0, "Alpha One", 0x0404),
    "02-artist": (0, "Alpha Artist", 0x0704),
    "03-album": (0, "Album One", 0x0204),
    "04-bpm": (12000, "120.0 bpm - Am", 0x0D04),
    "05-rating": (0, "", 0x0A04),
    "06-genre": (0, "Fixture House", 0x0604),
    "10-label": (0, "Fixture Label One", 0x0E04),
    "12-key": (14, "Am - 120.0 bpm", 0x0F04),
    "17-date-added": (0, "2021-02-02", 0x2E04),
    "16-dj-play-count": (0, "", 0x2A04),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def value(argument: dict) -> object:
    return argument["value"]


def main() -> None:
    suite = json.loads(SUITE.read_text())
    receipt = json.loads(RECEIPT.read_text())
    cases = validate(SUITE, GOLDEN, FIXTURE)

    assert receipt["format"] == 1
    assert receipt["scope"] == "real Rekordbox 7.2.19 RX3 sort and six-argument render cross"
    assert receipt["variant"] == "sort-secondary-render-6"
    assert receipt["case_count"] == len(suite["cases"]) == 11
    assert receipt["service_count"] == 1
    assert receipt["exact_repeat"] is True
    assert receipt["suite_sha256"] == sha256(SUITE)
    assert receipt["fixture_manifest_sha256"] == sha256(FIXTURE)
    assert receipt["identity_sha256"] == sha256(IDENTITY)
    assert receipt["golden_sha256"] == sha256(GOLDEN)
    health = validate_health_pair(
        EVIDENCE, receipt, "adjacent-payload-sort-secondary-render-6", sha256
    )

    rows = []
    case_summaries = []
    declarations = {case["id"]: case for case in suite["cases"]}
    for case_id, case in cases.items():
        declaration = declarations[case_id]
        sort_id = declaration["arguments"][1]["number"]
        for page in case["pages"]:
            render = [value(argument) for argument in page["arguments"]]
            assert len(render) == 6
            assert render[3] == 0
            assert render[4] == case["total"]
            assert render[5] == 12

        selected = []
        for index, row in enumerate(case["rows"]):
            arguments = row["arguments"]
            assert row["kind"] == 0x4101
            assert len(arguments) == 16
            selected_row = {
                "case": case_id,
                "sort_id": sort_id,
                "row": index,
                "title": value(arguments[3]),
                "argument_0": value(arguments[0]),
                "argument_5": value(arguments[5]),
                "argument_6": value(arguments[6]),
                "argument_12": value(arguments[12]),
                "argument_13": value(arguments[13]),
                "argument_14": value(arguments[14]),
                "argument_15": value(arguments[15]),
            }
            selected.append(selected_row)
            rows.append(selected_row)

        alpha_one = next(row for row in selected if row["title"] == "Alpha One")
        assert (
            alpha_one["argument_0"],
            alpha_one["argument_5"],
            alpha_one["argument_6"],
        ) == EXPECTED_ALPHA_ONE[case_id]
        assert (
            alpha_one["argument_12"],
            alpha_one["argument_13"],
            alpha_one["argument_14"],
            alpha_one["argument_15"],
        ) == (5001, 6, "Am", 12000)

        case_summaries.append(
            {
                "id": case_id,
                "sort_id": sort_id,
                "request_kind": "0x1004",
                "render_argument_count": 6,
                "render_argument_6": 12,
                "row_count": len(selected),
                "item_types": sorted({row["argument_6"] for row in selected}),
                "first_row": selected[0],
            }
        )

    with MATRIX.open("w", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    summary = {
        "scope": "real Rekordbox 7.2.19 only; backend comparison is deferred",
        "model": "XDJ-RX3",
        "player": 11,
        "fixture_profile": "full",
        "case_count": len(case_summaries),
        "row_count": len(rows),
        "exact_repeat": True,
        "post_request_health": health,
        "cases": case_summaries,
        "sha256": {
            "suite": sha256(SUITE),
            "fixture_manifest": sha256(FIXTURE),
            "identity": sha256(IDENTITY),
            "golden": sha256(GOLDEN),
            "receipt": sha256(RECEIPT),
        },
    }
    SUMMARY.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(f"validated {len(case_summaries)} cases and {len(rows)} rows")


if __name__ == "__main__":
    main()
