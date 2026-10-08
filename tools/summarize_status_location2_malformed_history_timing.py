#!/usr/bin/env python3
"""Validate and summarize the focused malformed-history timing study."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

from rekordbox_health import health_signature


ROOT = Path(__file__).resolve().parent.parent
CONFORMANCE = ROOT / "conformance"
SUITE_ROOT = CONFORMANCE / "suites/generated/song-info-location2-malformed-history-timing"
FIXTURE = CONFORMANCE / "fixtures/generated/full/manifest.json"
IDENTITY = CONFORMANCE / "runs/xdj-rx3-player-11-status.json"
EVIDENCE = ROOT / "data/experiments/song-info-status-location2/malformed-history-timing"
SUMMARY = EVIDENCE / "summary.json"
CSV_OUTPUT = EVIDENCE / "observations.csv"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    manifest = json.loads(FIXTURE.read_text())
    rows = []
    partitions: dict[int, Counter[str]] = {}

    for suite_path in sorted(SUITE_ROOT.glob("*.json")):
        suite = json.loads(suite_path.read_text())
        assert suite["defaults"]["device"] == 11
        assert suite["defaults"]["context"] == "0x0b010301"
        assert [case["arguments"][0]["number"] for case in suite["cases"]] == [
            "$context",
            "$context",
            "0x0b020301",
        ]
        delay = suite["cases"][-1]["delay_before_connection_ms"]
        variant = suite_path.stem
        evidence = EVIDENCE / variant
        counter: Counter[str] = Counter()

        for observation in range(1, 5):
            output_path = evidence / f"observation-{observation}.json"
            receipt_path = evidence / f"observation-{observation}.receipt.json"
            output = json.loads(output_path.read_text())
            receipt = json.loads(receipt_path.read_text())

            assert receipt["format"] == 1
            assert receipt["variant"] == variant
            assert receipt["observation"] == observation
            assert receipt["suite_sha256"] == sha256(suite_path)
            assert receipt["fixture_manifest_sha256"] == sha256(FIXTURE)
            assert receipt["identity_sha256"] == sha256(IDENTITY)
            assert receipt["observation_sha256"] == sha256(output_path)
            health_documents = {}
            for position in ("before", "after"):
                health_path = evidence / f"observation-{observation}-health-{position}.json"
                assert receipt[f"health_{position}_sha256"] == sha256(health_path)
                document = json.loads(health_path.read_text())
                assert document["label"] == (
                    f"location2-malformed-history-timing-{variant}-{observation}-{position}"
                )
                health_documents[position] = health_signature(document)
            before = health_documents["before"]
            assert before["process_count"] == 1
            assert before["responding_count"] == 1
            assert before["application_events"] == []
            health = health_documents["after"]

            provenance = output["provenance"]
            assert provenance["backend"] == "rekordbox"
            assert provenance["backend_version"] == "7.2.19"
            assert provenance["suite_sha256"] == sha256(suite_path)
            assert provenance["fixture_database_sha256"] == manifest["database_sha256"]
            assert provenance["fixture_fingerprint"] == manifest["fixture_fingerprint"]
            cases = output["behavior"]["cases"]
            assert [case["id"] for case in cases] == [
                "first--play-extra-argument",
                "second--delivery-blob-content",
                "delivery-probe",
            ]
            assert [case["request"]["arguments"][0]["value"] for case in cases] == [
                0x0B010301,
                0x0B010301,
                0x0B020301,
            ]
            probe = cases[-1]
            result = f"{probe['outcome']}:{probe.get('total')}"
            counter[result] += 1
            rows.append(
                {
                    "delay_before_connection_ms": delay,
                    "observation": observation,
                    "first_outcome": cases[0]["outcome"],
                    "first_total": cases[0].get("total"),
                    "second_outcome": cases[1]["outcome"],
                    "second_total": cases[1].get("total"),
                    "probe_outcome": probe["outcome"],
                    "probe_total": probe.get("total"),
                    "process_count": health["process_count"],
                    "responding_count": health["responding_count"],
                    "application_event_count": len(health["application_events"]),
                    "observation_sha256": sha256(output_path),
                    "receipt_sha256": sha256(receipt_path),
                }
            )
        partitions[delay] = counter

    assert len(rows) == 28
    summary = {
        "format": 1,
        "scope": "real Rekordbox 7.2.19 RX3 malformed-history timing",
        "fixture_database_sha256": manifest["database_sha256"],
        "fixture_fingerprint": manifest["fixture_fingerprint"],
        "delay_values_ms": sorted(partitions),
        "observations_per_delay": 4,
        "observation_count": len(rows),
        "partitions_by_delay": {
            str(delay): dict(sorted(counter.items()))
            for delay, counter in sorted(partitions.items())
        },
        "rows": rows,
    }
    SUMMARY.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    with CSV_OUTPUT.open("w", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=tuple(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"validated {len(rows)} malformed-history timing observations")


if __name__ == "__main__":
    main()
