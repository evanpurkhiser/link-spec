#!/usr/bin/env python3
"""Reduce independently repeated wrong-typed track-render arguments."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CONFORMANCE = ROOT / "conformance"
sys.path.insert(0, str(ROOT / "tools"))

from rekordbox_health import validate_health_pair
from summarize_search_oracle import validate


DECLARATION = CONFORMANCE / "data/render-argument-type-matrix.json"
FIXTURE = CONFORMANCE / "fixtures/generated/full/manifest.json"
IDENTITY = CONFORMANCE / "runs/xdj-rx3-player-11.json"
EVIDENCE = ROOT / "data/experiments/render-argument-types"
SUMMARY = EVIDENCE / "summary.json"
CSV_OUTPUT = EVIDENCE / "matrix.csv"
ALLOWED_OUTCOMES = {"raw_reply", "timeout", "disconnect"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    declaration = json.loads(DECLARATION.read_text())
    if (
        declaration.get("format") != 1
        or declaration.get("position_count") != 8
        or declaration.get("wire_types") != ["string", "blob"]
        or declaration.get("probe_count") != 16
        or declaration.get("case_count") != 32
    ):
        raise ValueError("render argument-type declaration has changed shape")

    rows = []
    for entry in declaration["probes"]:
        suite = CONFORMANCE / entry["suite"]
        golden = CONFORMANCE / entry["golden"]
        probe_evidence = EVIDENCE / "probes" / entry["id"]
        receipt_path = probe_evidence / "receipt.json"
        receipt = json.loads(receipt_path.read_text())
        cases = validate(suite, golden, FIXTURE)

        if receipt.get("format") != 1 or receipt.get("exact_repeat") is not True:
            raise ValueError(f"{entry['id']}: receipt is not an exact repeat")
        if receipt.get("scope") != "real Rekordbox 7.2.19 track render argument-type probe":
            raise ValueError(f"{entry['id']}: receipt scope changed")
        if receipt.get("id") != entry["id"] or receipt.get("case_count") != 2:
            raise ValueError(f"{entry['id']}: receipt identity/count changed")
        for field, expected in (
            ("suite_sha256", sha256(suite)),
            ("fixture_manifest_sha256", sha256(FIXTURE)),
            ("identity_sha256", sha256(IDENTITY)),
            ("golden_sha256", sha256(golden)),
        ):
            if receipt.get(field) != expected:
                raise ValueError(f"{entry['id']}: receipt {field} does not match")

        warm = cases["warm-track-list"]
        probe = cases[entry["id"]]
        if warm["outcome"] != "menu" or warm["total"] != 8:
            raise ValueError(f"{entry['id']}: warm Track list changed")
        if probe["request"]["kind"] != 0x3000:
            raise ValueError(f"{entry['id']}: probe request kind changed")
        if len(probe["request"]["arguments"]) != 8:
            raise ValueError(f"{entry['id']}: probe is not an eight-argument render")
        if probe["outcome"] not in ALLOWED_OUTCOMES:
            raise ValueError(f"{entry['id']}: unexpected outcome {probe['outcome']}")
        if probe["raw_response"]["outcome"] != probe["outcome"]:
            raise ValueError(f"{entry['id']}: outer/raw outcomes differ")

        health = validate_health_pair(probe_evidence, receipt, entry["id"], sha256)
        raw = probe["raw_response"]
        raw_hex = raw.get("raw_hex", "")
        row = {
            "id": entry["id"],
            "position": entry["position"],
            "argument": entry["argument"],
            "wire_type": entry["wire_type"],
            "outcome": probe["outcome"],
            "raw_bytes": len(raw_hex) // 2,
            "decoded_bytes": raw.get("decoded_bytes"),
            "message_kinds": " ".join(
                f"{message['kind']:04x}" for message in raw.get("messages", [])
            ),
            "error_kind": raw.get("error_kind"),
            "process_count": health["process_count"],
            "responding_count": health["responding_count"],
            "application_events": json.dumps(
                health["application_events"], sort_keys=True, separators=(",", ":")
            ),
            "suite_sha256": sha256(suite),
            "golden_sha256": sha256(golden),
            "receipt_sha256": sha256(receipt_path),
        }
        rows.append(row)

    if len(rows) != 16 or len({row["id"] for row in rows}) != 16:
        raise ValueError("render argument-type reduction is not 16 unique probes")

    outcome_counts = Counter(row["outcome"] for row in rows)
    health_counts = Counter(
        (
            row["process_count"],
            row["responding_count"],
            row["application_events"],
        )
        for row in rows
    )
    summary = {
        "format": 1,
        "scope": "real Rekordbox 7.2.19 track render argument-type matrix",
        "declaration_sha256": sha256(DECLARATION),
        "fixture_manifest_sha256": sha256(FIXTURE),
        "identity_sha256": sha256(IDENTITY),
        "position_count": 8,
        "wire_types": ["string", "blob"],
        "probe_count": len(rows),
        "case_count": 32,
        "exact_repeat": True,
        "outcome_counts": dict(sorted(outcome_counts.items())),
        "health_classes": [
            {
                "process_count": process_count,
                "responding_count": responding_count,
                "application_events": json.loads(events),
                "probe_count": count,
            }
            for (process_count, responding_count, events), count in sorted(
                health_counts.items()
            )
        ],
        "probes": rows,
    }
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    candidate = SUMMARY.with_name(f"{SUMMARY.name}.next")
    candidate.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    candidate.replace(SUMMARY)

    fields = tuple(rows[0])
    candidate = CSV_OUTPUT.with_name(f"{CSV_OUTPUT.name}.next")
    with candidate.open("w", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    candidate.replace(CSV_OUTPUT)
    print(f"wrote {SUMMARY} and {CSV_OUTPUT}: {len(rows)} probes")


if __name__ == "__main__":
    main()
