#!/usr/bin/env python3
"""Reduce the independently recorded adjacent-payload malformed matrix."""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

try:
    from .summarize_adjacent_payload_fileless import sha256, summarize, write_json
except ImportError:
    from summarize_adjacent_payload_fileless import sha256, summarize, write_json
try:
    from .rekordbox_health import event_signature, health_signature, validate_health_pair
except ImportError:
    from rekordbox_health import event_signature, health_signature, validate_health_pair


ROOT = Path(__file__).resolve().parent.parent
MATRIX = ROOT / "conformance/data/adjacent-payload-malformed-matrix.json"
EVIDENCE = ROOT / "data/experiments/adjacent-payload/malformed"
OUTPUT = EVIDENCE / "summary.json"
CSV_OUTPUT = EVIDENCE / "matrix.csv"
MANIFEST = ROOT / "conformance/fixtures/generated/full/manifest.json"
IDENTITY = ROOT / "conformance/runs/xdj-rx3-player-11.json"


def main() -> None:
    declaration = json.loads(MATRIX.read_text())
    if declaration["format"] != 1 or declaration["case_count"] != 96:
        raise ValueError("malformed matrix declaration is not the expected 96-case format")

    rows = []
    kind_outcomes: dict[str, Counter] = defaultdict(Counter)
    for entry in declaration["cases"]:
        suite = ROOT / "conformance" / entry["suite"]
        golden = ROOT / "conformance" / entry["golden"]
        receipt_path = EVIDENCE / "repeats" / entry["id"] / "receipt.json"
        receipt = json.loads(receipt_path.read_text())
        summary, matrix = summarize(
            suite,
            MANIFEST,
            golden,
            expected_case_count=1,
            expected_service_count=1,
            scope="real Rekordbox 7.2.19 malformed adjacent payload case",
            enforce_expected_oracle=False,
        )
        if matrix[0]["id"] != entry["id"]:
            raise ValueError(f"{entry['id']}: reduced case ID changed")
        if receipt.get("format") != 1 or receipt.get("exact_repeat") is not True:
            raise ValueError(f"{entry['id']}: receipt is not an exact repeat")
        if receipt.get("scope") != "real Rekordbox 7.2.19 malformed adjacent payload case":
            raise ValueError(f"{entry['id']}: receipt scope changed")
        if receipt.get("id") != entry["id"]:
            raise ValueError(f"{entry['id']}: receipt case ID changed")
        if receipt.get("case_count") != 1:
            raise ValueError(f"{entry['id']}: receipt case count is not one")
        for field, expected in (
            ("suite_sha256", sha256(suite)),
            ("fixture_manifest_sha256", sha256(MANIFEST)),
            ("identity_sha256", sha256(IDENTITY)),
            ("golden_sha256", sha256(golden)),
        ):
            if receipt.get(field) != expected:
                raise ValueError(f"{entry['id']}: receipt {field} does not match")

        health = validate_health_pair(receipt_path.parent, receipt, entry["id"], sha256)

        row = {
            **matrix[0],
            "process_count": health["process_count"],
            "responding_count": health["responding_count"],
            "application_event_count": len(health["application_events"]),
            "application_event_signature": json.dumps(
                health["application_events"], sort_keys=True, separators=(",", ":")
            ),
            "suite_sha256": summary["suite_sha256"],
            "golden_sha256": summary["golden_sha256"],
            "receipt_sha256": sha256(receipt_path),
        }
        rows.append(row)
        kind_outcomes[row["kind"]][row["outcome"]] += 1

    if len(rows) != 96 or len({row["id"] for row in rows}) != 96:
        raise ValueError("reduced malformed matrix is not 96 unique cases")
    if len(kind_outcomes) != 16 or {sum(value.values()) for value in kind_outcomes.values()} != {6}:
        raise ValueError("malformed matrix is not six cases for each of 16 services")

    outcome_counts = Counter(row["outcome"] for row in rows)
    health_counts = Counter(
        (
            row["process_count"],
            row["responding_count"],
            row["application_event_signature"],
        )
        for row in rows
    )
    summary = {
        "format": 1,
        "scope": "real Rekordbox 7.2.19 malformed adjacent payload matrix",
        "declaration_sha256": sha256(MATRIX),
        "fixture_manifest_sha256": sha256(MANIFEST),
        "case_count": len(rows),
        "service_count": len(kind_outcomes),
        "outcome_counts": dict(sorted(outcome_counts.items())),
        "health_classes": [
            {
                "process_count": process_count,
                "responding_count": responding_count,
                "application_events": json.loads(application_events),
                "case_count": count,
            }
            for (process_count, responding_count, application_events), count in sorted(
                health_counts.items()
            )
        ],
        "services": [
            {
                "kind": kind,
                "case_count": sum(kind_outcomes[kind].values()),
                "outcomes": dict(sorted(kind_outcomes[kind].items())),
            }
            for kind in sorted(kind_outcomes, key=lambda value: int(value, 16))
        ],
    }
    write_json(OUTPUT, summary)

    CSV_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    candidate = CSV_OUTPUT.with_name(f"{CSV_OUTPUT.name}.next")
    fields = (
        "id", "kind", "outcome", "raw_bytes", "decoded_bytes",
        "message_kinds", "error_kind", "process_count", "responding_count",
        "application_event_count", "application_event_signature", "suite_sha256",
        "golden_sha256", "receipt_sha256",
    )
    with candidate.open("w", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({**row, "message_kinds": " ".join(row["message_kinds"])})
    candidate.replace(CSV_OUTPUT)
    print(f"wrote {OUTPUT} and {CSV_OUTPUT}: {len(rows)} cases")


if __name__ == "__main__":
    main()
