#!/usr/bin/env python3
"""Validate and summarize the fixture-isolated 0x2401 parser matrix."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

from summarize_search_oracle import validate


ROOT = Path(__file__).resolve().parent.parent
CONFORMANCE = ROOT / "conformance"
sys.path.insert(0, str(ROOT / "tools"))

from build_hot_cue_mutation_record import build_record

MATRIX = CONFORMANCE / "data/hot-cue-setter-parser-matrix.json"
FIXTURE = (
    CONFORMANCE
    / "fixtures/generated/hot-cue-bank-mutation-duplicate-slot/manifest.json"
)
BASELINE_GOLDEN = (
    CONFORMANCE
    / "goldens/rekordbox-7.2.19/xdj-rx3-status/"
    "context-hot-cue-setter-status-extended.json"
)
GENERATOR = CONFORMANCE / "generate_hot_cue_extended_setter_parser_suites.py"
RECORDER = CONFORMANCE / "record_hot_cue_extended_setter_parser_matrix.sh"
OUTPUT = (
    ROOT
    / "data/experiments/hot-cue-bank/extended-setter-parser/summary.json"
)
PARTIAL_OUTPUT = OUTPUT.with_name("summary.partial.json")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def one_message(case: dict[str, object]) -> dict[str, object] | None:
    messages = case.get("raw_response", {}).get("messages", [])
    if not messages:
        return None
    assert len(messages) == 1
    return messages[0]


def number(argument: dict[str, object]) -> int:
    assert argument["type"] == "number"
    return argument["value"]


def blob(argument: dict[str, object]) -> str:
    assert argument["type"] == "blob"
    return argument["hex"]


def baseline_blob() -> str:
    golden = json.loads(BASELINE_GOLDEN.read_text())
    case = next(
        case
        for case in golden["behavior"]["cases"]
        if case["id"] == "type-00--read-after-rejected-setter"
    )
    return blob(one_message(case)["arguments"][3])


def lifecycle_result(
    variant: dict[str, object],
    fixture_database_sha256: str,
    baseline: str,
) -> dict[str, object] | None:
    evidence = ROOT / str(variant["evidence"])
    if not evidence.is_file():
        return None

    document = json.loads(evidence.read_text())
    assert document["complete"] is True
    assert document["completed_observations"] == document["declared_observations"]
    assert document["fixture_database_sha256"] == fixture_database_sha256

    if document["experiment"] in {
        "hot-cue-slot-8-lifecycle",
        "hot-cue-returned-slots-ffffffff-lifecycle",
    }:
        assert document["declared_observations"] == 3
        assert len(document["results"]) == 3
        aggregate = document["aggregate"]
        restart_getter = aggregate["restart_getter"]
        if isinstance(restart_getter, dict):
            assert restart_getter["status"] == 0
            assert restart_getter["record_count"] == 1
            assert restart_getter["record_length"] == 124
            if document["experiment"] == "hot-cue-slot-8-lifecycle":
                expected_record_sha256 = hashlib.sha256(
                    bytes.fromhex(baseline)
                ).hexdigest()
                assert aggregate["database_effect_after_restart"] == "pristine"
            else:
                expected_record_sha256 = hashlib.sha256(build_record()).hexdigest()
                assert aggregate["database_effect_after_restart"] == "changed"
            assert restart_getter["record_sha256"] == expected_record_sha256

        suite = CONFORMANCE / str(variant["suite"])
        return {
            **variant,
            "evidence_mode": "lifecycle",
            "setter_outcome": "lifecycle-observed",
            "response_kind": None,
            "status": None,
            "response_record_count": None,
            "response_blob_sha256": None,
            "database_effect": aggregate["database_effect_after_restart"],
            "database_record_length": (
                restart_getter["record_length"]
                if isinstance(restart_getter, dict)
                else None
            ),
            "database_record_sha256": (
                restart_getter["record_sha256"]
                if isinstance(restart_getter, dict)
                else None
            ),
            "observations": 3,
            "case_executions": 9,
            "lifecycle_aggregate": aggregate,
            "suite_sha256": sha256(suite),
            "lifecycle_summary_sha256": sha256(evidence),
        }

    assert document["experiment"] == "hot-cue-declared-length-ffffffff-lifecycle"
    assert document["declared_observations"] == 60
    assert len(document["results"]) == 60

    baseline_sha256 = hashlib.sha256(bytes.fromhex(baseline)).hexdigest()
    for observation in document["results"]:
        assert observation["signatures"]["setter"] in {
            "0100",
            "4e02-echo-2401-status-50-count-0",
        }
        final_getter = observation["final_getter"]
        assert final_getter == {
            "status": 0,
            "record_count": 1,
            "record_length": 124,
            "record_sha256": baseline_sha256,
        }

    suite = CONFORMANCE / str(variant["suite"])
    return {
        **variant,
        "evidence_mode": "lifecycle",
        "setter_outcome": "timing-dependent",
        "response_kind": None,
        "status": 50,
        "response_record_count": 0,
        "response_blob_sha256": hashlib.sha256(b"").hexdigest(),
        "database_effect": "pristine",
        "database_record_length": 124,
        "database_record_sha256": baseline_sha256,
        "observations": 60,
        "case_executions": 240,
        "suite_sha256": sha256(suite),
        "lifecycle_summary_sha256": sha256(evidence),
    }


def response_signature(cases: dict[str, dict[str, object]]) -> str:
    responses = [
        {
            "id": case_id,
            "outcome": cases[case_id]["outcome"],
            "raw_response": cases[case_id].get("raw_response"),
        }
        for case_id in sorted(cases)
    ]
    encoded = json.dumps(responses, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--allow-partial",
        action="store_true",
        help="validate promoted goldens and write summary.partial.json",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    matrix = json.loads(MATRIX.read_text())
    fixture = json.loads(FIXTURE.read_text())
    baseline = baseline_blob()
    results = []
    axis_counts: dict[str, Counter[str]] = defaultdict(Counter)

    for variant in matrix["variants"]:
        if variant["record_mode"] == "lifecycle":
            result = lifecycle_result(
                variant,
                fixture["database_sha256"],
                baseline,
            )
            if result is None:
                if args.allow_partial:
                    continue
                raise FileNotFoundError(ROOT / variant["evidence"])
            axis_counts[variant["axis"]][f"status-{result['status']}"] += 1
            axis_counts[variant["axis"]][result["database_effect"]] += 1
            results.append(result)
            continue

        assert variant["record_mode"] == "golden"
        suite = CONFORMANCE / variant["suite"]
        golden = CONFORMANCE / variant["golden"]
        if not golden.is_file():
            if args.allow_partial:
                continue
            raise FileNotFoundError(golden)
        cases = validate(suite, golden, FIXTURE)
        assert set(cases) == {"setter", "database-read-after-setter"}

        setter_case = cases["setter"]
        setter = one_message(setter_case)
        if setter is None:
            response_kind = None
            status = None
            setter_count = None
            setter_blob_sha256 = None
        else:
            response_kind = setter["kind"]
            arguments = setter["arguments"]
            if response_kind == 0x4E02:
                assert len(arguments) == 5
                assert number(arguments[0]) == 0x2401
                status = number(arguments[1])
                setter_count = number(arguments[4])
                setter_blob_sha256 = hashlib.sha256(
                    bytes.fromhex(blob(arguments[3]))
                ).hexdigest()
            else:
                assert response_kind == 0x0100
                assert arguments == []
                status = None
                setter_count = None
                setter_blob_sha256 = None

        getter = one_message(cases["database-read-after-setter"])
        assert getter is not None and getter["kind"] == 0x4E02
        getter_arguments = getter["arguments"]
        assert [number(getter_arguments[index]) for index in (0, 1, 4)] == [
            0x2301,
            0,
            1,
        ]
        getter_blob = blob(getter_arguments[3])
        getter_record_length = number(getter_arguments[2])
        assert getter_record_length == len(bytes.fromhex(getter_blob))
        database_effect = "pristine" if getter_blob == baseline else "changed"
        axis_counts[variant["axis"]][f"status-{status}"] += 1
        axis_counts[variant["axis"]][database_effect] += 1

        results.append(
            {
                **variant,
                "evidence_mode": "golden",
                "setter_outcome": setter_case["outcome"],
                "response_kind": response_kind,
                "status": status,
                "response_record_count": setter_count,
                "response_blob_sha256": setter_blob_sha256,
                "database_effect": database_effect,
                "database_record_length": getter_record_length,
                "database_record_sha256": hashlib.sha256(
                    bytes.fromhex(getter_blob)
                ).hexdigest(),
                "response_signature": response_signature(cases),
                "case_executions": 2,
                "suite_sha256": sha256(suite),
                "golden_sha256": sha256(golden),
            }
        )

    by_id = {result["id"]: result for result in results}
    rejected_control = by_id.get("record-count-00000000")
    if rejected_control is not None:
        assert rejected_control["status"] == 50
        assert rejected_control["response_record_count"] == 0
        assert rejected_control["database_effect"] == "pristine"

    accepted_control = by_id.get("record-count-00000001")
    if accepted_control is not None:
        assert accepted_control["status"] == 0
        assert accepted_control["response_record_count"] == 1
        assert accepted_control["database_effect"] == "changed"
        assert accepted_control["database_record_sha256"] == hashlib.sha256(
            build_record()
        ).hexdigest()

    for variant_id in ("record-count-00000002", "record-count-ffffffff"):
        rejected_count = by_id.get(variant_id)
        if rejected_count is None:
            continue
        assert rejected_count["status"] == 50
        assert rejected_count["response_record_count"] == 0
        assert rejected_count["database_effect"] == "pristine"

    for variant_id in (
        "actual-length-00000000",
        "actual-length-00000001",
        "actual-length-00000037",
    ):
        short_record = by_id.get(variant_id)
        if short_record is None:
            continue
        assert short_record["status"] == 50
        assert short_record["response_record_count"] == 0
        assert short_record["database_effect"] == "pristine"
        assert short_record["database_record_length"] == 124

    fixed_only = by_id.get("actual-length-00000038")
    if fixed_only is not None:
        assert fixed_only["status"] == 0
        assert fixed_only["response_record_count"] == 1
        assert fixed_only["database_effect"] == "changed"
        assert fixed_only["database_record_length"] == 56

    for variant_id in (
        "actual-length-0000007b",
        "actual-length-0000007c",
        "actual-length-0000007d",
    ):
        option_record = by_id.get(variant_id)
        if option_record is None:
            continue
        assert option_record["status"] == 0
        assert option_record["response_record_count"] == 1
        assert option_record["database_effect"] == "changed"
        assert option_record["database_record_length"] == 124
        assert option_record["database_record_sha256"] == hashlib.sha256(
            build_record()
        ).hexdigest()

    for variant_id in (
        "declared-length-00000000",
        "declared-length-00000037",
        "declared-length-00000038",
        "declared-length-0000007b",
    ):
        short_declared_length = by_id.get(variant_id)
        if short_declared_length is None:
            continue
        assert short_declared_length["setter_outcome"] == "raw_reply"
        assert short_declared_length["response_kind"] == 0x0100
        assert short_declared_length["status"] is None
        assert short_declared_length["response_record_count"] is None
        assert short_declared_length["database_effect"] == "pristine"
        assert short_declared_length["database_record_length"] == 124

    for variant_id in (
        "declared-length-0000007c",
        "declared-length-0000007d",
    ):
        sufficient_declared_length = by_id.get(variant_id)
        if sufficient_declared_length is None:
            continue
        assert sufficient_declared_length["response_kind"] == 0x4E02
        assert sufficient_declared_length["status"] == 0
        assert sufficient_declared_length["response_record_count"] == 1
        assert sufficient_declared_length["database_effect"] == "changed"
        assert sufficient_declared_length["database_record_length"] == 124
        assert sufficient_declared_length[
            "database_record_sha256"
        ] == hashlib.sha256(build_record()).hexdigest()

    lifecycle_variants = [
        variant
        for variant in matrix["variants"]
        if variant["record_mode"] == "lifecycle"
    ]
    evidence_cases = sum(result["case_executions"] for result in results)
    summary = {
        "scope": "real Rekordbox 7.2.19 only; backend comparison is deferred",
        "fixture": {
            "profile": fixture["profile"],
            "database_sha256": fixture["database_sha256"],
            "fixture_fingerprint": fixture["fixture_fingerprint"],
            "bank_id": fixture["ids"]["hotcue.bank.mutation"],
            "baseline_record_sha256": hashlib.sha256(
                bytes.fromhex(baseline)
            ).hexdigest(),
        },
        "matrix": {
            "model": "XDJ-RX3",
            "player": 11,
            "setup": "extended",
            "declared_variants": len(matrix["variants"]),
            "completed_variants": len(results),
            "evidence_cases": evidence_cases,
            "canonical_golden_variants": sum(
                result["evidence_mode"] == "golden" for result in results
            ),
            "lifecycle_variants": sum(
                result["evidence_mode"] == "lifecycle" for result in results
            ),
            "fixture_reset_repeat_pairs": sum(
                result["evidence_mode"] == "golden" for result in results
            ),
            "independent_lifecycle_runs": sum(
                result.get("observations", 0) for result in results
            ),
            "axes": {
                axis: dict(sorted(counts.items()))
                for axis, counts in sorted(axis_counts.items())
            },
        },
        "results": results,
        "sha256": {
            "matrix": sha256(MATRIX),
            "fixture_manifest": sha256(FIXTURE),
            "baseline_golden": sha256(BASELINE_GOLDEN),
            "generator": sha256(GENERATOR),
            "recorder": sha256(RECORDER),
            "lifecycle_summaries": {
                variant["id"]: sha256(ROOT / variant["evidence"])
                if (ROOT / variant["evidence"]).is_file()
                else None
                for variant in lifecycle_variants
            },
        },
    }
    output = PARTIAL_OUTPUT if args.allow_partial else OUTPUT
    if not args.allow_partial:
        assert len(results) == len(matrix["variants"])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(
        f"validated {len(results)} variants / {evidence_cases} evidence cases; "
        f"wrote {output}"
    )


if __name__ == "__main__":
    main()
