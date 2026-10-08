#!/usr/bin/env python3
"""Reduce the Play Song Info CLSSyncMethod=0 authority recording."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
GOLDEN = ROOT / "conformance/goldens/rekordbox-7.2.19/xdj-rx3/song-info-cloud-sync-zero.json"
FIXTURE = ROOT / "conformance/fixtures/generated/cloud-sync-zero/manifest.json"
STATIC = ROOT / "data/static-analysis/play-song-info-cloud-paths.json"
OUTPUT = ROOT / "data/experiments/song-info-cloud-sync-zero/summary.json"
MATRIX = ROOT / "data/experiments/song-info-cloud-sync-zero/matrix.csv"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def argument_values(row: dict) -> list[object]:
    return [argument["value"] for argument in row["arguments"]]


def main() -> None:
    golden = json.loads(GOLDEN.read_text())
    fixture = json.loads(FIXTURE.read_text())
    static = json.loads(STATIC.read_text())
    cases = golden["behavior"]["cases"]
    assert fixture["profile"] == "cloud-sync-zero"
    assert fixture["track_count"] == 10
    assert static["live_oracle_boundary"]["missing_equivalence_class"].startswith("zero")
    assert len(cases) == 10

    rows = []
    for case in cases:
        path_row = None
        if case["outcome"] == "menu" and case["total"] == 7:
            assert len(case["rows"]) == 7
            values = argument_values(case["rows"][4])
            path_row = {"raw": values[0], "text": values[3], "type": values[6]}
        rows.append(
            {
                "case": case["id"],
                "outcome": case["outcome"],
                "total": case.get("total"),
                "path_raw": None if path_row is None else path_row["raw"],
                "path_text": None if path_row is None else path_row["text"],
                "path_type": None if path_row is None else path_row["type"],
            }
        )

    document = {
        "format": 1,
        "scope": "real Rekordbox 7.2.19 Play Song Info CLSSyncMethod zero",
        "authority": "observed rows are canonical; static evidence classifies but does not replace them",
        "golden_sha256": sha256(GOLDEN),
        "fixture_database_sha256": fixture["database_sha256"],
        "fixture_fingerprint": fixture["fixture_fingerprint"],
        "static_audit_sha256": sha256(STATIC),
        "case_count": len(cases),
        "rows": rows,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(document, indent=2) + "\n")
    with MATRIX.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=tuple(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
