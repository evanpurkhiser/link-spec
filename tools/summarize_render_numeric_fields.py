#!/usr/bin/env python3
"""Validate and summarize numeric fields 4-6 of track rendering."""

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


SUITE = CONFORMANCE / "suites/generated/render-numeric-fields.json"
FIXTURE = CONFORMANCE / "fixtures/generated/full/manifest.json"
IDENTITY = CONFORMANCE / "runs/xdj-rx3-player-11.json"
GOLDEN = CONFORMANCE / "goldens/rekordbox-7.2.19/xdj-rx3/render-numeric-fields.json"
EVIDENCE = ROOT / "data/experiments/render-numeric-fields"
RECEIPT = EVIDENCE / "receipt.json"
SUMMARY = EVIDENCE / "summary.json"
CSV_OUTPUT = EVIDENCE / "matrix.csv"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_rows(case: dict) -> list[list[object]]:
    return [
        [argument.get("value", argument.get("hex")) for argument in row["arguments"]]
        for row in case.get("rows", [])
    ]


def request_values(case: dict) -> list[object]:
    page = case.get("pages", [{}])[0]
    return [
        argument.get("value", argument.get("hex"))
        for argument in page.get("arguments", [])
    ]


def main() -> None:
    suite = json.loads(SUITE.read_text())
    receipt = json.loads(RECEIPT.read_text())
    cases = validate(SUITE, GOLDEN, FIXTURE)

    if receipt.get("format") != 1 or receipt.get("exact_repeat") is not True:
        raise ValueError("render numeric-field receipt is not an exact repeat")
    if receipt.get("scope") != "real Rekordbox 7.2.19 track render numeric fields":
        raise ValueError("render numeric-field receipt scope changed")
    if receipt.get("variant") != "render-numeric-fields":
        raise ValueError("render numeric-field receipt variant changed")
    if receipt.get("case_count") != len(suite["cases"]) or len(cases) != 42:
        raise ValueError("render numeric-field case count changed")
    if receipt.get("service_count") != 1:
        raise ValueError("render numeric-field service count changed")
    for field, expected in (
        ("suite_sha256", sha256(SUITE)),
        ("fixture_manifest_sha256", sha256(FIXTURE)),
        ("identity_sha256", sha256(IDENTITY)),
        ("golden_sha256", sha256(GOLDEN)),
    ):
        if receipt.get(field) != expected:
            raise ValueError(f"receipt {field} does not match")
    health = validate_health_pair(
        EVIDENCE, receipt, "adjacent-payload-render-numeric-fields", sha256
    )

    control = cases["control"]
    control_rows = canonical_rows(control)
    rows = []
    for declaration in suite["cases"]:
        case = cases[declaration["id"]]
        render = request_values(case)
        if case["request"]["kind"] != 0x1004:
            raise ValueError(f"{declaration['id']}: request kind changed")
        if case.get("pages") and len(render) != 8:
            raise ValueError(f"{declaration['id']}: render is not eight arguments")

        observed_rows = canonical_rows(case)
        rows.append(
            {
                "id": declaration["id"],
                "argument_4": render[3] if render else None,
                "argument_5": render[4] if render else None,
                "argument_6": render[5] if render else None,
                "outcome": case["outcome"],
                "total": case.get("total"),
                "row_count": len(observed_rows),
                "item_ids": " ".join(
                    str(row[1]) for row in observed_rows if len(row) > 1
                ),
                "titles": " | ".join(
                    str(row[3]) for row in observed_rows if len(row) > 3
                ),
                "rows_equal_control": observed_rows == control_rows,
            }
        )

    summary = {
        "format": 1,
        "scope": "real Rekordbox 7.2.19 track render numeric fields",
        "model": "XDJ-RX3",
        "player": 11,
        "fixture_profile": "full",
        "case_count": len(rows),
        "exact_repeat": True,
        "post_request_health": health,
        "control": rows[0],
        "first_row_seek": [row for row in rows if row["id"].startswith("first-row-seek-")],
        "client_total": [row for row in rows if row["id"].startswith("client-total-")],
        "category_id": [row for row in rows if row["id"].startswith("category-id-")],
        "sha256": {
            "suite": sha256(SUITE),
            "fixture_manifest": sha256(FIXTURE),
            "identity": sha256(IDENTITY),
            "golden": sha256(GOLDEN),
            "receipt": sha256(RECEIPT),
        },
    }
    candidate = SUMMARY.with_name(f"{SUMMARY.name}.next")
    candidate.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    candidate.replace(SUMMARY)

    candidate = CSV_OUTPUT.with_name(f"{CSV_OUTPUT.name}.next")
    with candidate.open("w", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=tuple(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    candidate.replace(CSV_OUTPUT)
    print(f"validated {len(rows)} render numeric-field cases")


if __name__ == "__main__":
    main()
