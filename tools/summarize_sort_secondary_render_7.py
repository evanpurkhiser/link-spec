#!/usr/bin/env python3
"""Validate and summarize the RX3 sort plus seven-argument render oracle."""

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


SUITE = CONFORMANCE / "suites/generated/sort-secondary-render-7.json"
FIXTURE = CONFORMANCE / "fixtures/generated/full/manifest.json"
IDENTITY = CONFORMANCE / "runs/xdj-rx3-player-11.json"
GOLDEN = CONFORMANCE / "goldens/rekordbox-7.2.19/xdj-rx3/sort-secondary-render-7.json"
RENDER_6_GOLDEN = (
    CONFORMANCE
    / "goldens/rekordbox-7.2.19/xdj-rx3/sort-secondary-render-6.json"
)
EVIDENCE = ROOT / "data/experiments/sort-secondary-render-7"
RECEIPT = EVIDENCE / "receipt.json"
SUMMARY = EVIDENCE / "summary.json"
MATRIX = EVIDENCE / "rows.csv"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def values(arguments: list[dict]) -> list[object]:
    return [argument["value"] for argument in arguments]


def normalized_rows(case: dict) -> list[list[object]]:
    return [values(row["arguments"]) for row in case["rows"]]


def main() -> None:
    suite = json.loads(SUITE.read_text())
    receipt = json.loads(RECEIPT.read_text())
    cases = validate(SUITE, GOLDEN, FIXTURE)
    render_6_cases = {
        case["id"]: case
        for case in json.loads(RENDER_6_GOLDEN.read_text())["behavior"]["cases"]
    }

    assert receipt["format"] == 1
    assert receipt["scope"] == (
        "real Rekordbox 7.2.19 RX3 sort and seven-argument render cross"
    )
    assert receipt["variant"] == "sort-secondary-render-7"
    assert receipt["case_count"] == len(suite["cases"]) == 33
    assert receipt["service_count"] == 1
    assert receipt["exact_repeat"] is True
    assert receipt["suite_sha256"] == sha256(SUITE)
    assert receipt["fixture_manifest_sha256"] == sha256(FIXTURE)
    assert receipt["identity_sha256"] == sha256(IDENTITY)
    assert receipt["golden_sha256"] == sha256(GOLDEN)
    health = validate_health_pair(
        EVIDENCE, receipt, "adjacent-payload-sort-secondary-render-7", sha256
    )

    declarations = {case["id"]: case for case in suite["cases"]}
    rows = []
    summaries = []
    for case_id, case in cases.items():
        declaration = declarations[case_id]
        sort_id = declaration["arguments"][1]["number"]
        gate = declaration["render_arguments"][3]
        base_case_id = "-".join(case_id.split("-")[:-2])
        render_6_case = render_6_cases[base_case_id]
        expected_gate = int(gate, 0) if isinstance(gate, str) else gate

        for page in case["pages"]:
            render = values(page["arguments"])
            assert len(render) == 7
            assert render[3:6] == [0, case["total"], 12]
            assert render[6] == expected_gate

        selected = []
        for index, row in enumerate(case["rows"]):
            arguments = values(row["arguments"])
            assert row["kind"] == 0x4101
            assert len(arguments) == 16
            selected_row = {
                "case": case_id,
                "sort_id": sort_id,
                "gate": gate,
                "row": index,
                "title": arguments[3],
                "argument_0": arguments[0],
                "argument_5": arguments[5],
                "argument_6": arguments[6],
                "argument_12": arguments[12],
                "argument_13": arguments[13],
                "argument_14": arguments[14],
                "argument_15": arguments[15],
            }
            selected.append(selected_row)
            rows.append(selected_row)

        summaries.append(
            {
                "id": case_id,
                "base_case_id": base_case_id,
                "sort_id": sort_id,
                "seventh_argument": gate,
                "request_kind": "0x1004",
                "render_argument_count": 7,
                "row_count": len(selected),
                "item_types": sorted({row["argument_6"] for row in selected}),
                "first_row": selected[0],
                "same_total_as_render_6": case["total"] == render_6_case["total"],
                "same_rows_as_render_6": normalized_rows(case)
                == normalized_rows(render_6_case),
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
        "case_count": len(summaries),
        "row_count": len(rows),
        "exact_repeat": True,
        "post_request_health": health,
        "render_7_equals_render_6_for_every_case": all(
            case["same_total_as_render_6"] and case["same_rows_as_render_6"]
            for case in summaries
        ),
        "cases": summaries,
        "sha256": {
            "suite": sha256(SUITE),
            "fixture_manifest": sha256(FIXTURE),
            "identity": sha256(IDENTITY),
            "golden": sha256(GOLDEN),
            "render_6_golden": sha256(RENDER_6_GOLDEN),
            "receipt": sha256(RECEIPT),
        },
    }
    SUMMARY.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(f"validated {len(summaries)} cases and {len(rows)} rows")


if __name__ == "__main__":
    main()
