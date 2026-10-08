#!/usr/bin/env python3
"""Validate and summarize the process-isolated 0x2201 parser matrix."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CONFORMANCE = ROOT / "conformance"
sys.path.insert(0, str(ROOT / "tools"))

from summarize_search_oracle import validate


MATRIX = CONFORMANCE / "data/hot-cue-legacy-setter-parser-matrix.json"
FIXTURE = CONFORMANCE / "fixtures/generated/hot-cue-bank-legacy-ordinals/manifest.json"
GETTER_SUITE = (
    CONFORMANCE
    / "suites/generated/hot-cue-legacy-setter-parser/"
    "hot-cue-legacy-setter-parser-read-after.json"
)
BASELINE_GOLDEN = (
    CONFORMANCE
    / "goldens/rekordbox-7.2.19/xdj-rx3-status/"
    "context-hot-cue-legacy-setter-status-extended.json"
)
EVIDENCE = ROOT / "data/experiments/hot-cue-bank/legacy-setter-parser"
BASELINE_DATABASE = EVIDENCE / "baseline.json"
OUTPUT = EVIDENCE / "summary.json"
PARTIAL_OUTPUT = EVIDENCE / "summary.partial.json"
MATRIX_OUTPUT = EVIDENCE / "matrix.csv"
PARTIAL_MATRIX_OUTPUT = EVIDENCE / "matrix.partial.csv"
MUTABLE_MEMBERSHIP_FIELDS = (
    "ID",
    "HotCueBanklistID",
    "ContentID",
    "TrackNo",
    "CueID",
    "InMsec",
    "InFrame",
    "InMpegFrame",
    "InMpegAbs",
    "OutMsec",
    "OutFrame",
    "OutMpegFrame",
    "OutMpegAbs",
    "Color",
    "ColorTableIndex",
    "ActiveLoop",
    "Comment",
    "BeatLoopSize",
    "CueMicrosec",
    "InPointSeekInfo",
    "OutPointSeekInfo",
    "rb_data_status",
    "rb_local_data_status",
    "rb_local_deleted",
    "rb_local_synced",
)
FIXED_WORD_FIELDS = {
    2: None,
    3: "InFrame",
    4: "OutFrame",
    5: "InMpegFrame",
    6: "OutMpegFrame",
    7: "InMpegAbs",
    8: "OutMpegAbs",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def request_signature(variant: dict[str, object]) -> str:
    suite = json.loads((CONFORMANCE / variant["suite"]).read_text())
    case = suite["cases"][0]
    return digest(
        {
            "request_kind": case["request_kind"],
            "arguments": case["arguments"],
        }
    )


def number(argument: dict[str, object]) -> int:
    assert argument["type"] == "number"
    return argument["value"]


def blob(argument: dict[str, object]) -> str:
    assert argument["type"] == "blob"
    return argument["hex"]


def only_case(document: dict[str, object]) -> dict[str, object]:
    cases = document["behavior"]["cases"]
    assert len(cases) == 1
    return cases[0]


def only_message(case: dict[str, object]) -> dict[str, object] | None:
    messages = case.get("raw_response", {}).get("messages", [])
    if not messages:
        return None
    assert len(messages) == 1
    return messages[0]


def baseline_getter_blob() -> str:
    golden = json.loads(BASELINE_GOLDEN.read_text())
    case = next(
        case
        for case in golden["behavior"]["cases"]
        if case["id"] == "type-00--read-after-rejected-setter"
    )
    message = only_message(case)
    assert message is not None and message["kind"] == 0x4E02
    return blob(message["arguments"][3])


def record_lengths(payload: bytes) -> list[int]:
    lengths = []
    offset = 0

    while offset < len(payload):
        assert offset + 4 <= len(payload)
        length = int.from_bytes(payload[offset : offset + 4], "little")
        assert length >= 4
        assert offset + length <= len(payload)
        lengths.append(length)
        offset += length

    assert offset == len(payload)
    return lengths


def membership_rows(snapshot: dict[str, object]) -> dict[str, dict[str, object]]:
    return {
        str(row["ID"]): {field: row.get(field) for field in MUTABLE_MEMBERSHIP_FIELDS}
        for row in snapshot["memberships"]
    }


def database_effect(
    baseline: dict[str, object], snapshot: dict[str, object]
) -> tuple[str, list[str]]:
    before = membership_rows(baseline)
    after = membership_rows(snapshot)
    changed = sorted(
        set(before) | set(after),
        key=int,
    )
    changed = [row_id for row_id in changed if before.get(row_id) != after.get(row_id)]
    return ("changed" if changed else "pristine", changed)


def parse_setter(case: dict[str, object]) -> dict[str, object]:
    message = only_message(case)
    if message is None:
        return {
            "outcome": case["outcome"],
            "response_kind": None,
            "response_argument_count": None,
            "status": None,
            "response_record_count": None,
            "response_signature": digest(
                {"outcome": case["outcome"], "raw_response": case.get("raw_response")}
            ),
        }

    arguments = message["arguments"]
    if message["kind"] == 0x0100:
        assert arguments == []
        return {
            "outcome": case["outcome"],
            "response_kind": message["kind"],
            "response_argument_count": 0,
            "status": None,
            "response_record_count": None,
            "response_signature": digest(
                {"outcome": case["outcome"], "raw_response": case.get("raw_response")}
            ),
        }

    assert message["kind"] == 0x4702
    assert number(arguments[0]) == 0x2201
    return {
        "outcome": case["outcome"],
        "response_kind": message["kind"],
        "response_argument_count": len(arguments),
        "status": number(arguments[1]),
        "response_record_count": number(arguments[5]),
        "response_signature": digest(
            {"outcome": case["outcome"], "raw_response": case.get("raw_response")}
        ),
    }


def parse_getter(path: Path) -> dict[str, object]:
    cases = validate(GETTER_SUITE, path, FIXTURE)
    assert set(cases) == {"database-read-after-setter"}
    case = cases["database-read-after-setter"]
    message = only_message(case)
    if message is None:
        return {
            "getter_outcome": case["outcome"],
            "getter_effect": f"unavailable-{case['outcome']}",
            "getter_record_count": None,
            "getter_record_lengths": None,
            "getter_blob_bytes": None,
            "getter_blob_sha256": None,
        }

    assert message["kind"] == 0x4E02
    arguments = message["arguments"]
    payload = blob(arguments[3])
    payload_bytes = bytes.fromhex(payload)
    lengths = record_lengths(payload_bytes)
    assert number(arguments[0]) == 0x2301
    assert number(arguments[1]) == 0
    assert number(arguments[2]) == len(payload_bytes)
    assert number(arguments[4]) == len(lengths)
    return {
        "getter_outcome": case["outcome"],
        "getter_effect": "pristine" if payload == baseline_getter_blob() else "changed",
        "getter_record_count": number(arguments[4]),
        "getter_record_lengths": lengths,
        "getter_blob_bytes": len(payload_bytes),
        "getter_blob_sha256": hashlib.sha256(payload_bytes).hexdigest(),
    }


def application_error_signature(event: dict[str, object]) -> str:
    stable_message = "\n".join(str(event.get("message", "")).splitlines()[:4])
    return digest(
        {
            "provider": event["provider"],
            "event_id": event["event_id"],
            "level": event["level"],
            "message": stable_message,
        }
    )


def parse_run(
    variant: dict[str, object], run: int, baseline: dict[str, object]
) -> dict[str, object] | None:
    directory = EVIDENCE / variant["id"] / f"run-{run}"
    if not (directory / "complete.json").is_file():
        return None

    cases = validate(CONFORMANCE / variant["suite"], directory / "setter.json", FIXTURE)
    assert set(cases) == {"setter"}
    setter = parse_setter(cases["setter"])
    health = json.loads((directory / "health.json").read_text())
    snapshot = json.loads((directory / "database/snapshot.json").read_text())
    effect, changed_ids = database_effect(baseline, snapshot)
    process_count = health["rekordbox_process_count"]
    result = {
        "run": run,
        **setter,
        "process_state": "alive" if process_count else "exited",
        "process_count": process_count,
        "application_event_count": len(health["application_events"]),
        "application_events": [
            {
                "provider": event["provider"],
                "event_id": event["event_id"],
                "level": event["level"],
            }
            for event in health["application_events"]
        ],
        "application_error_signatures": [
            application_error_signature(event)
            for event in health["application_events"]
        ],
        "database_effect": effect,
        "changed_membership_ids": changed_ids,
        "database_snapshot_sha256": sha256(directory / "database/snapshot.json"),
        "setter_sha256": sha256(directory / "setter.json"),
        "health_sha256": sha256(directory / "health.json"),
    }
    getter = directory / "getter.json"
    if getter.is_file():
        result.update(parse_getter(getter))
        result["getter_sha256"] = sha256(getter)
        result["getter_unavailable_process_state"] = None
        result["getter_unavailable_application_event_count"] = None
        result["getter_unavailable_application_error_signatures"] = None
    else:
        skipped_path = directory / "getter-skipped.json"
        assert skipped_path.is_file()
        skipped = json.loads(skipped_path.read_text())
        skipped_outcome = skipped.get("outcome", "process-exited")
        assert skipped_outcome in {
            "process-exited",
            "dbserver-connect-timeout",
            "port-query-timeout",
        }
        if skipped_outcome in {"dbserver-connect-timeout", "port-query-timeout"}:
            assert skipped["getter_log_sha256"] == sha256(directory / "getter.log")
            unavailable_health_path = directory / "health-after-getter-unavailable.json"
            assert skipped["health_sha256"] == sha256(unavailable_health_path)
            unavailable_health = json.loads(unavailable_health_path.read_text())
        else:
            unavailable_health = health
        result.update(
            {
                "getter_outcome": f"skipped-{skipped_outcome}",
                "getter_effect": f"unavailable-{skipped_outcome}",
                "getter_record_count": None,
                "getter_record_lengths": None,
                "getter_blob_bytes": None,
                "getter_blob_sha256": None,
                "getter_sha256": None,
                "getter_unavailable_process_state": (
                    "alive"
                    if unavailable_health["rekordbox_process_count"]
                    else "exited"
                ),
                "getter_unavailable_application_event_count": len(
                    unavailable_health["application_events"]
                ),
                "getter_unavailable_application_error_signatures": [
                    application_error_signature(event)
                    for event in unavailable_health["application_events"]
                ],
            }
        )

    restart_getter = directory / "restart-getter.json"
    if restart_getter.is_file():
        restart = parse_getter(restart_getter)
        restart_health = json.loads((directory / "health-after-restart.json").read_text())
        restart_snapshot_path = directory / "database-after-restart/snapshot.json"
        restart_snapshot = json.loads(restart_snapshot_path.read_text())
        restart_effect, restart_changed_ids = database_effect(baseline, restart_snapshot)
        result.update(
            {
                "restart_getter_outcome": restart["getter_outcome"],
                "restart_getter_effect": restart["getter_effect"],
                "restart_getter_record_count": restart["getter_record_count"],
                "restart_getter_record_lengths": restart["getter_record_lengths"],
                "restart_getter_blob_bytes": restart["getter_blob_bytes"],
                "restart_getter_blob_sha256": restart["getter_blob_sha256"],
                "restart_process_state": (
                    "alive" if restart_health["rekordbox_process_count"] else "exited"
                ),
                "restart_application_event_count": len(
                    restart_health["application_events"]
                ),
                "restart_database_effect": restart_effect,
                "restart_changed_membership_ids": restart_changed_ids,
                "restart_getter_sha256": sha256(restart_getter),
                "restart_health_sha256": sha256(
                    directory / "health-after-restart.json"
                ),
                "restart_database_snapshot_sha256": sha256(restart_snapshot_path),
            }
        )
    else:
        assert (directory / "restart-skipped.json").is_file()
        result.update(
            {
                "restart_getter_outcome": "skipped-immediate-raw-reply",
                "restart_getter_effect": None,
                "restart_getter_record_count": None,
                "restart_getter_record_lengths": None,
                "restart_getter_blob_bytes": None,
                "restart_getter_blob_sha256": None,
                "restart_process_state": None,
                "restart_application_event_count": None,
                "restart_database_effect": None,
                "restart_changed_membership_ids": None,
                "restart_getter_sha256": None,
                "restart_health_sha256": None,
                "restart_database_snapshot_sha256": None,
            }
        )

    receipt_path = directory / "complete.json"
    receipt = json.loads(receipt_path.read_text())
    assert receipt["variant"] == variant["id"]
    assert receipt["run"] == run
    assert receipt["suite_sha256"] == sha256(CONFORMANCE / variant["suite"])
    assert receipt["setter_sha256"] == result["setter_sha256"]
    assert receipt["health_sha256"] == result["health_sha256"]
    assert receipt["database_snapshot_sha256"] == result["database_snapshot_sha256"]
    assert receipt["getter_sha256"] == sha256(directory / receipt["getter_artifact"])
    assert receipt["restart_sha256"] == sha256(directory / receipt["restart_artifact"])
    assert receipt["restart_health_sha256"] == result["restart_health_sha256"]
    assert (
        receipt["restart_database_snapshot_sha256"]
        == result["restart_database_snapshot_sha256"]
    )
    result["receipt_sha256"] = sha256(receipt_path)
    return result


def repeat_signature(run: dict[str, object]) -> dict[str, object]:
    restart_recovered = (
        str(run["getter_effect"]).startswith("unavailable-")
        and run["restart_getter_outcome"] == "raw_reply"
    )
    return {
        **{
            key: run[key]
            for key in (
                "response_kind",
                "response_argument_count",
                "status",
                "response_record_count",
                "database_effect",
                "changed_membership_ids",
                "restart_getter_outcome",
                "restart_getter_effect",
                "restart_getter_record_count",
                "restart_getter_record_lengths",
                "restart_getter_blob_bytes",
                "restart_getter_blob_sha256",
                "restart_process_state",
                "restart_database_effect",
                "restart_changed_membership_ids",
                "application_error_signatures",
                "getter_unavailable_process_state",
                "getter_unavailable_application_event_count",
                "getter_unavailable_application_error_signatures",
            )
        },
        "outcome": "unavailable-before-restart" if restart_recovered else run["outcome"],
        "response_signature": (
            None if restart_recovered else run["response_signature"]
        ),
        "process_state": (
            "unavailable-before-restart" if restart_recovered else run["process_state"]
        ),
        "getter_outcome": (
            "unavailable-before-restart"
            if restart_recovered
            else run["getter_outcome"]
        ),
        "getter_effect": (
            "unavailable-before-restart"
            if restart_recovered
            else run["getter_effect"]
        ),
        **{
            key: None if restart_recovered else run[key]
            for key in (
                "getter_record_count",
                "getter_record_lengths",
                "getter_blob_bytes",
                "getter_blob_sha256",
            )
        },
    }


def transport_signature(run: dict[str, object]) -> dict[str, object]:
    return {
        key: run[key]
        for key in (
            "outcome",
            "response_kind",
            "response_argument_count",
            "status",
            "response_record_count",
            "response_signature",
            "process_state",
            "database_effect",
            "changed_membership_ids",
            "getter_outcome",
            "getter_effect",
            "getter_record_count",
            "getter_record_lengths",
            "getter_blob_bytes",
            "getter_blob_sha256",
            "restart_getter_outcome",
            "restart_getter_effect",
            "restart_getter_record_count",
            "restart_getter_record_lengths",
            "restart_getter_blob_bytes",
            "restart_getter_blob_sha256",
            "restart_process_state",
            "restart_database_effect",
            "restart_changed_membership_ids",
            "application_error_signatures",
            "getter_unavailable_process_state",
            "getter_unavailable_application_event_count",
            "getter_unavailable_application_error_signatures",
        )
    }


def equivalent_request_groups(
    results: list[dict[str, object]],
) -> list[dict[str, object]]:
    by_request: dict[str, list[dict[str, object]]] = defaultdict(list)
    for result in results:
        by_request[result["request_signature"]].append(result)

    groups = []
    for signature, members in sorted(by_request.items()):
        if len(members) < 2:
            continue

        by_lifecycle: dict[str, list[str]] = defaultdict(list)
        for member in members:
            lifecycle = digest(repeat_signature(member["runs"][0]))
            by_lifecycle[lifecycle].append(member["id"])

        groups.append(
            {
                "request_signature": signature,
                "variants": sorted(member["id"] for member in members),
                "lifecycle_consistent": len(by_lifecycle) == 1,
                "lifecycle_groups": [
                    {
                        "signature": lifecycle,
                        "variants": sorted(variants),
                    }
                    for lifecycle, variants in sorted(by_lifecycle.items())
                ],
            }
        )

    return groups


def fixed_word_analysis(
    results: list[dict[str, object]],
) -> list[dict[str, object]]:
    results_by_id = {result["id"]: result for result in results}
    analysis = []

    for word, expected_field in FIXED_WORD_FIELDS.items():
        variants = {
            label: results_by_id.get(f"fixed-word-{word}-{suffix}")
            for label, suffix in (("zero", "00000000"), ("maximum", "ffffffff"))
        }
        completed_values = [
            label for label, result in variants.items() if result is not None
        ]
        if len(completed_values) != 2:
            analysis.append(
                {
                    "word": word,
                    "byte_offset": word * 4,
                    "expected_field": expected_field,
                    "state": "pending",
                    "completed_values": completed_values,
                }
            )
            continue

        rows: dict[str, list[dict[str, object]]] = {}
        for label, result in variants.items():
            assert result is not None
            rows[label] = [
                membership_rows(
                    json.loads(
                        (
                            EVIDENCE
                            / result["id"]
                            / f"run-{run}/database/snapshot.json"
                        ).read_text()
                    )
                )["94201"]
                for run in (1, 2)
            ]
            assert rows[label][0] == rows[label][1]

        changed_fields = sorted(
            field
            for field in MUTABLE_MEMBERSHIP_FIELDS
            if rows["zero"][0][field] != rows["maximum"][0][field]
        )
        expected_changed_fields = [] if expected_field is None else [expected_field]
        assert changed_fields == expected_changed_fields

        complete_results = [result for result in variants.values() if result is not None]
        request_signatures = {result["request_signature"] for result in complete_results}
        response_signatures = {
            run["response_signature"]
            for result in complete_results
            for run in result["runs"]
        }
        assert len(request_signatures) == 2
        assert len(response_signatures) == 1

        analysis.append(
            {
                "word": word,
                "byte_offset": word * 4,
                "expected_field": expected_field,
                "state": "complete",
                "completed_values": completed_values,
                "changed_fields": changed_fields,
                "stored_values": {
                    label: None if expected_field is None else rows[label][0][expected_field]
                    for label in variants
                },
                "request_signatures": {
                    label: result["request_signature"]
                    for label, result in variants.items()
                    if result is not None
                },
                "response_signature": response_signatures.pop(),
                "semantic_row_sha256": {
                    label: digest(rows[label][0]) for label in variants
                },
            }
        )

    return analysis


def readable_run(prefix: str, run: dict[str, object] | None) -> dict[str, object]:
    fields = (
        "outcome",
        "response_kind",
        "response_argument_count",
        "status",
        "response_record_count",
        "process_state",
        "application_event_count",
        "database_effect",
        "getter_outcome",
        "getter_effect",
        "getter_record_count",
        "getter_record_lengths",
        "getter_blob_bytes",
        "getter_unavailable_process_state",
        "getter_unavailable_application_event_count",
        "restart_getter_outcome",
        "restart_getter_effect",
        "restart_getter_record_lengths",
        "restart_getter_blob_bytes",
        "restart_database_effect",
    )
    return {
        f"{prefix}_{field}": (
            ""
            if run is None or run.get(field) is None
            else "/".join(map(str, run.get(field)))
            if field.endswith("record_lengths")
            else run.get(field)
        )
        for field in fields
    }


def readable_row(
    variant: dict[str, object], result: dict[str, object] | None
) -> dict[str, object]:
    runs = result["runs"] if result is not None else [None, None]
    return {
        "variant": variant["id"],
        "axis": variant["axis"],
        "value": variant["value"],
        "word": "" if variant.get("word") is None else variant["word"],
        "state": "complete" if result is not None else "pending",
        **readable_run("run1", runs[0]),
        **readable_run("run2", runs[1]),
        "repeat_verified": result is not None and result["repeat_verified"],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-partial", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    matrix = json.loads(MATRIX.read_text())
    fixture = json.loads(FIXTURE.read_text())
    baseline = json.loads(BASELINE_DATABASE.read_text())
    results = []
    pending = []
    axis_counts: dict[str, Counter[str]] = defaultdict(Counter)

    for variant in matrix["variants"]:
        runs = [parse_run(variant, run, baseline) for run in (1, 2)]
        if any(run is None for run in runs):
            pending.append(variant["id"])
            if args.allow_partial:
                continue
            raise FileNotFoundError(f"incomplete variant: {variant['id']}")
        first, second = runs
        assert first is not None and second is not None
        assert repeat_signature(first) == repeat_signature(second)
        axis_counts[variant["axis"]][first["outcome"]] += 1
        axis_counts[variant["axis"]][first["process_state"]] += 1
        axis_counts[variant["axis"]][first["database_effect"]] += 1
        results.append(
            {
                **variant,
                "request_signature": request_signature(variant),
                "runs": runs,
                "repeat_verified": True,
                "transport_repeat_exact": (
                    transport_signature(first) == transport_signature(second)
                ),
            }
        )

    summary = {
        "scope": "real Rekordbox 7.2.19 only; backend comparison is deferred",
        "fixture": {
            "profile": fixture["profile"],
            "database_sha256": fixture["database_sha256"],
            "fixture_fingerprint": fixture["fixture_fingerprint"],
            "bank_id": fixture["ids"]["hotcue.bank.mutation"],
            "baseline_snapshot_sha256": sha256(BASELINE_DATABASE),
            "baseline_getter_blob_sha256": hashlib.sha256(
                bytes.fromhex(baseline_getter_blob())
            ).hexdigest(),
        },
        "matrix": {
            "model": "XDJ-RX3",
            "player": 11,
            "setup": "extended",
            "declared_variants": len(matrix["variants"]),
            "completed_variants": len(results),
            "independent_runs": len(results) * 2,
            "pending": pending,
            "axes": {
                axis: dict(sorted(counts.items()))
                for axis, counts in sorted(axis_counts.items())
            },
        },
        "equivalent_request_groups": equivalent_request_groups(results),
        "fixed_word_analysis": fixed_word_analysis(results),
        "results": results,
        "sha256": {
            "matrix": sha256(MATRIX),
            "fixture_manifest": sha256(FIXTURE),
            "getter_suite": sha256(GETTER_SUITE),
            "baseline_golden": sha256(BASELINE_GOLDEN),
            "generator": sha256(
                CONFORMANCE / "generate_hot_cue_legacy_setter_parser_suites.py"
            ),
            "recorder": sha256(
                CONFORMANCE / "record_hot_cue_legacy_setter_parser_matrix.sh"
            ),
        },
    }
    output = PARTIAL_OUTPUT if args.allow_partial else OUTPUT
    if not args.allow_partial:
        assert not pending
        assert len(results) == len(matrix["variants"])
    output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    results_by_id = {result["id"]: result for result in results}
    readable_rows = [
        readable_row(variant, results_by_id.get(variant["id"]))
        for variant in matrix["variants"]
    ]
    matrix_output = PARTIAL_MATRIX_OUTPUT if args.allow_partial else MATRIX_OUTPUT
    with matrix_output.open("w", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=readable_rows[0].keys(),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(readable_rows)
    if not args.allow_partial:
        PARTIAL_OUTPUT.unlink(missing_ok=True)
        PARTIAL_MATRIX_OUTPUT.unlink(missing_ok=True)
    print(
        f"validated {len(results)} repeat pairs / {len(results) * 2} runs; "
        f"wrote {output}"
    )
    print(matrix_output)


if __name__ == "__main__":
    main()
