#!/usr/bin/env python3
"""Validate and summarize the real-Rekordbox delayed Song Info reply oracle."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from itertools import product
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CONFORMANCE = ROOT / "conformance"
MATRIX = CONFORMANCE / "data/song-info-delayed-reply-routing-matrix.json"
SUITES = CONFORMANCE / "suites/generated/song-info-delayed-reply-routing"
EVIDENCE = ROOT / "data/experiments/song-info-status-location2/delayed-reply-routing"
SUMMARY = EVIDENCE / "summary.json"
ROWS = EVIDENCE / "observations.csv"


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def number_values(case: dict) -> list[int]:
    request = case.get("request") or {}
    return [
        argument["value"]
        for argument in request.get("arguments", [])
        if argument.get("type") == "number"
    ]


def validate_health(path: Path) -> None:
    health = load(path)
    processes = health["rekordbox_processes"]
    assert health["rekordbox_process_count"] == 1
    assert len(processes) == 1 and processes[0]["responding"] is True
    assert health["application_events"] == []


def raw_messages(case: dict) -> list[dict]:
    return case.get("raw_response", {}).get("messages", [])


def main() -> None:
    matrix = load(MATRIX)
    assert matrix["format"] == 1
    assert matrix["observations_per_variant"] == 4
    dimensions = matrix["dimensions"]
    variants = [
        f"{precursor}--{delay:04}ms"
        for precursor, delay in product(
            dimensions["second_precursor"],
            dimensions["delay_before_replacement_connection_ms"],
        )
    ]
    assert len(variants) == 6

    rows = []
    setup_message_shapes: Counter[str] = Counter()
    no_send_outcomes: Counter[str] = Counter()
    message_shapes: Counter[str] = Counter()
    observation_probe_totals: Counter[str] = Counter()
    health_probe_totals: Counter[str] = Counter()

    for variant in variants:
        suite_path = SUITES / f"{variant}.json"
        suite = load(suite_path)
        assert suite["defaults"]["device"] == 11
        assert suite["defaults"]["context"] == "0x0b010301"
        assert len(suite["cases"]) == 5

        for observation in range(1, 5):
            root = EVIDENCE / variant
            output = root / f"observation-{observation}.json"
            receipt_path = root / f"observation-{observation}.receipt.json"
            before = root / f"observation-{observation}-health-before.json"
            after = root / f"observation-{observation}-health-after.json"
            receipt = load(receipt_path)
            assert receipt["variant"] == variant
            assert receipt["observation"] == observation
            assert receipt["suite_sha256"] == digest(suite_path)
            assert receipt["observation_sha256"] == digest(output)
            assert receipt["health_before_sha256"] == digest(before)
            assert receipt["health_after_sha256"] == digest(after)
            validate_health(before)
            validate_health(after)

            cases = load(output)["behavior"]["cases"]
            assert [case["id"] for case in cases] == [
                "first--play-extra-argument",
                f"second--{variant.rsplit('--', 1)[0]}",
                "replacement-no-send",
                "delivery-probe-observation-connection",
                "delivery-probe-fresh-health",
            ]
            assert number_values(cases[0])[0] == 0x0B010301
            assert number_values(cases[1])[0] == 0x0B010301
            assert number_values(cases[3])[0] == 0x0B020301
            assert number_values(cases[4])[0] == 0x0B020301

            no_send = cases[2]
            setup_messages = no_send["connection_setup_exchange"]["response"]
            setup_shape = json.dumps(
                [
                    {
                        "kind": message["kind"],
                        "arguments": message.get("arguments", []),
                    }
                    for message in setup_messages
                ],
                sort_keys=True,
                separators=(",", ":"),
            )
            messages = raw_messages(no_send)
            shape = json.dumps(
                [
                    {
                        "kind": message["kind"],
                        "arguments": message.get("arguments", []),
                    }
                    for message in messages
                ],
                sort_keys=True,
                separators=(",", ":"),
            )
            setup_message_shapes[setup_shape] += 1
            no_send_outcomes[no_send["outcome"]] += 1
            message_shapes[shape] += 1
            observation_total = cases[3]["total"]
            health_total = cases[4]["total"]
            observation_probe_totals[str(observation_total)] += 1
            health_probe_totals[str(health_total)] += 1
            rows.append(
                {
                    "variant": variant,
                    "observation": observation,
                    "replacement_setup_messages": setup_shape,
                    "no_send_outcome": no_send["outcome"],
                    "no_send_messages": shape,
                    "observation_probe_total": observation_total,
                    "health_probe_total": health_total,
                    "observation_sha256": digest(output),
                }
            )

    assert len(rows) == 24
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    with ROWS.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    summary = {
        "format": 1,
        "scope": matrix["scope"],
        "authority": "real Rekordbox 7.2.19 only",
        "variant_count": 6,
        "observation_count": 24,
        "replacement_setup_message_shapes": dict(sorted(setup_message_shapes.items())),
        "no_send_outcomes": dict(sorted(no_send_outcomes.items())),
        "no_send_message_shapes": dict(sorted(message_shapes.items())),
        "observation_probe_totals": dict(sorted(observation_probe_totals.items())),
        "health_probe_totals": dict(sorted(health_probe_totals.items())),
        "matrix_sha256": digest(MATRIX),
    }
    SUMMARY.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
