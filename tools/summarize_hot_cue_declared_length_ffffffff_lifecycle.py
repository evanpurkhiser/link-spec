#!/usr/bin/env python3
"""Validate and summarize the 0x2401 UINT32_MAX response lifecycle matrix."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from summarize_search_oracle import validate


ROOT = Path(__file__).resolve().parent.parent
CONFORMANCE = ROOT / "conformance"
MATRIX = CONFORMANCE / "data/hot-cue-declared-length-ffffffff-lifecycle-matrix.json"
FIXTURE = CONFORMANCE / "fixtures/generated/hot-cue-bank-mutation-duplicate-slot/manifest.json"
BASELINE_GOLDEN = (
    CONFORMANCE
    / "goldens/rekordbox-7.2.19/xdj-rx3-status/"
    "context-hot-cue-setter-status-extended.json"
)
EVIDENCE = (
    ROOT
    / "data/experiments/hot-cue-bank/extended-setter-parser/"
    "declared-length-ffffffff-lifecycle"
)
OBSERVATIONS = EVIDENCE / "observations"
OUTPUT = EVIDENCE / "summary.json"
PARTIAL_OUTPUT = EVIDENCE / "summary.partial.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def number(argument: dict[str, object]) -> int:
    assert argument["type"] == "number"
    return argument["value"]


def message_signature(message: dict[str, object]) -> str:
    kind = message["kind"]
    arguments = message["arguments"]
    if kind == 0x0100:
        assert arguments == []
        return "0100"
    if kind != 0x4E02 or not arguments:
        return f"{kind:04x}"

    echo = number(arguments[0])
    status = number(arguments[1]) if len(arguments) > 1 else None
    count = number(arguments[4]) if len(arguments) > 4 else None
    return f"4e02-echo-{echo:04x}-status-{status}-count-{count}"


def case_signature(case: dict[str, object]) -> str:
    response = case.get("raw_response")
    if not response:
        return case["outcome"]
    messages = response.get("messages", [])
    if not messages:
        return response["outcome"]
    return "+".join(message_signature(message) for message in messages)


def first_transaction(case: dict[str, object]) -> int | None:
    raw_hex = case.get("raw_response", {}).get("raw_hex", "")
    raw = bytes.fromhex(raw_hex)
    if len(raw) < 10 or raw[:5] != bytes.fromhex("11872349ae") or raw[5] != 0x11:
        return None
    return int.from_bytes(raw[6:10], "big")


def getter_record(case: dict[str, object]) -> dict[str, object] | None:
    for message in case.get("raw_response", {}).get("messages", []):
        if message["kind"] != 0x4E02 or len(message["arguments"]) != 5:
            continue
        arguments = message["arguments"]
        if number(arguments[0]) != 0x2301:
            continue
        blob = arguments[3]
        assert blob["type"] == "blob"
        raw = bytes.fromhex(blob["hex"])
        assert number(arguments[2]) == len(raw)
        return {
            "status": number(arguments[1]),
            "record_count": number(arguments[4]),
            "record_length": len(raw),
            "record_sha256": hashlib.sha256(raw).hexdigest(),
        }
    return None


def baseline_record_sha256() -> str:
    golden = json.loads(BASELINE_GOLDEN.read_text())
    case = next(
        case
        for case in golden["behavior"]["cases"]
        if case["id"] == "type-00--read-after-rejected-setter"
    )
    record = getter_record(case)
    assert record is not None
    assert record["status"] == 0
    assert record["record_count"] == 1
    assert record["record_length"] == 124
    return str(record["record_sha256"])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-partial", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    matrix = json.loads(MATRIX.read_text())
    fixture = json.loads(FIXTURE.read_text())
    baseline_sha256 = baseline_record_sha256()
    results = []
    counts: dict[str, Counter[str]] = defaultdict(Counter)

    for variant in matrix["variants"]:
        suite = CONFORMANCE / variant["suite"]
        for run in range(1, matrix["replicates"] + 1):
            observation = OBSERVATIONS / f"{variant['id']}-run-{run}.json"
            if not observation.is_file():
                if args.allow_partial:
                    continue
                raise FileNotFoundError(observation)

            cases = validate(suite, observation, FIXTURE)
            signatures = {
                case_id: case_signature(case) for case_id, case in cases.items()
            }
            transactions = {
                case_id: first_transaction(case) for case_id, case in cases.items()
            }
            setter = signatures["setter"]
            assert setter in {
                "0100",
                "4e02-echo-2401-status-50-count-0",
            }
            late = signatures["late-response-observation"]
            if setter == "0100":
                assert transactions["setter"] == 0xFFFFFFFE
                if late == "4e02-echo-2401-status-50-count-0":
                    assert transactions["late-response-observation"] == 1
                else:
                    assert late in {"disconnect", "timeout"}
                    assert transactions["late-response-observation"] is None
            else:
                assert transactions["setter"] == 1
            first_getter = getter_record(cases["database-read-after-observation"])
            final_getter = getter_record(cases["database-read-final"])
            key = f"{variant['topology']}:{variant['delay_ms']}ms"
            counts[key][f"setter:{setter}"] += 1
            counts[key][f"late:{late}"] += 1
            counts[key][
                "first_getter:2301" if first_getter else "first_getter:no-2301"
            ] += 1
            counts[key][
                "final_getter:2301" if final_getter else "final_getter:no-2301"
            ] += 1

            for getter in (first_getter, final_getter):
                if getter is not None:
                    assert getter["status"] == 0
                    assert getter["record_count"] == 1
                    assert getter["record_length"] == 124
                    assert getter["record_sha256"] == baseline_sha256

            results.append(
                {
                    **variant,
                    "run": run,
                    "signatures": signatures,
                    "first_transactions": transactions,
                    "first_getter": first_getter,
                    "final_getter": final_getter,
                    "suite_sha256": sha256(suite),
                    "observation_sha256": sha256(observation),
                }
            )

    declared = len(matrix["variants"]) * matrix["replicates"]
    complete = len(results) == declared
    if not complete and not args.allow_partial:
        raise AssertionError(f"only {len(results)} of {declared} observations exist")

    document = {
        "format": 1,
        "experiment": "hot-cue-declared-length-ffffffff-lifecycle",
        "complete": complete,
        "declared_observations": declared,
        "completed_observations": len(results),
        "fixture_database_sha256": fixture["database_sha256"],
        "baseline_record_sha256": baseline_sha256,
        "matrix_sha256": sha256(MATRIX),
        "counts": {key: dict(sorted(value.items())) for key, value in sorted(counts.items())},
        "results": results,
    }
    destination = OUTPUT if complete else PARTIAL_OUTPUT
    destination.write_text(json.dumps(document, indent=2) + "\n")
    print(destination)


if __name__ == "__main__":
    main()
