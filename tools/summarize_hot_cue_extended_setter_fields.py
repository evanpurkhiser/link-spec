#!/usr/bin/env python3
"""Validate and summarize the 0x2401 mutable-field matrix."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from summarize_search_oracle import validate


ROOT = Path(__file__).resolve().parent.parent
CONFORMANCE = ROOT / "conformance"
MATRIX = CONFORMANCE / "data/hot-cue-setter-field-matrix.json"
FIXTURE = CONFORMANCE / "fixtures/generated/hot-cue-bank-mutation-duplicate-slot/manifest.json"
IDENTITY = CONFORMANCE / "runs/xdj-rx3-player-11-status.json"
OUTPUT = ROOT / "data/experiments/hot-cue-bank/extended-setter-fields/summary.json"
EVIDENCE = ROOT / "data/experiments/hot-cue-bank/extended-setter-fields/repeats"
MAXIMUM_COMMENT_VARIANT = "comment-maximum-even-length"
RAW_PROBE_READ_BYTES = 8192
MESSAGE_PREFIX = bytes.fromhex(
    "11872349ae"  # protocol magic
    "1100000001"  # transaction ID 1
    "104e02"      # response kind
    "0f05"        # five arguments
    "1400000005"  # argument-tag blob length
    "0606060306"  # number, number, number, blob, number
)
MUTATION_FIELDS = (
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
)


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


def blob(argument: dict[str, object]) -> bytes:
    assert argument["type"] == "blob"
    return bytes.fromhex(argument["hex"])


def truncated_raw_message(case: dict[str, object], request_kind: int) -> tuple[bytes, int]:
    """Validate the prefix retained when a single raw read cannot hold the message."""

    response = case["raw_response"]
    assert case["outcome"] == "raw_reply"
    assert response["outcome"] == "raw_reply"
    assert response["error_kind"] is None
    assert response["decoded_bytes"] == 0
    assert response["messages"] == []

    raw = bytes.fromhex(response["raw_hex"])
    assert len(raw) == RAW_PROBE_READ_BYTES
    assert raw.startswith(MESSAGE_PREFIX)
    assert raw[25:30] == b"\x11" + request_kind.to_bytes(4, "big")
    assert raw[30:35] == b"\x11\x00\x00\x00\x00"
    assert raw[35] == 0x11
    declared_record_length = int.from_bytes(raw[36:40], "big")
    assert raw[40] == 0x14
    assert int.from_bytes(raw[41:45], "big") == declared_record_length

    return raw, declared_record_length


def semantic_snapshot(document: dict[str, object]) -> list[dict[str, object]]:
    return [
        {field: row[field] for field in MUTATION_FIELDS}
        for row in document["memberships"]
    ]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-partial", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    matrix = json.loads(MATRIX.read_text())
    fixture = json.loads(FIXTURE.read_text())
    results = []
    axis_counts: dict[str, Counter[str]] = defaultdict(Counter)

    for variant in matrix["variants"]:
        suite = CONFORMANCE / variant["suite"]
        golden = CONFORMANCE / variant["golden"]
        evidence = EVIDENCE / variant["id"]
        receipt = evidence / "receipt.json"
        record_snapshot_path = evidence / "record-snapshot.json"
        repeat_snapshot_path = evidence / "repeat-snapshot.json"
        if not all(path.is_file() for path in (golden, receipt, record_snapshot_path, repeat_snapshot_path)):
            if args.allow_partial:
                continue
            raise FileNotFoundError(f"incomplete evidence for {variant['id']}")

        receipt_document = json.loads(receipt.read_text())
        assert receipt_document["variant"] == variant["id"]
        assert receipt_document["suite_sha256"] == sha256(suite)
        assert receipt_document["fixture_manifest_sha256"] == sha256(FIXTURE)
        assert receipt_document["identity_sha256"] == sha256(IDENTITY)
        assert receipt_document["golden_sha256"] == sha256(golden)
        assert receipt_document["record_snapshot_sha256"] == sha256(record_snapshot_path)
        assert receipt_document["repeat_snapshot_sha256"] == sha256(repeat_snapshot_path)
        record_snapshot = json.loads(record_snapshot_path.read_text())
        repeat_snapshot = json.loads(repeat_snapshot_path.read_text())
        assert record_snapshot["integrity"] == "ok"
        assert repeat_snapshot["integrity"] == "ok"
        record_state = semantic_snapshot(record_snapshot)
        assert record_state == semantic_snapshot(repeat_snapshot)

        cases = validate(suite, golden, FIXTURE)
        assert set(cases) == {"setter", "database-read-after-setter"}
        setter = one_message(cases["setter"])
        getter = one_message(cases["database-read-after-setter"])
        maximum_comment = variant["id"] == MAXIMUM_COMMENT_VARIANT

        if maximum_comment:
            setter_raw, setter_record_length = truncated_raw_message(cases["setter"], 0x2401)
            getter_raw, getter_record_length = truncated_raw_message(
                cases["database-read-after-setter"],
                0x2301,
            )
            request_record_length = json.loads(suite.read_text())["cases"][0]["arguments"][3]["number"]
            assert setter_record_length == getter_record_length == request_record_length - 2
            assert [row["Comment"] for row in record_state] == ["A" * 32766, ""]
            response_kind = 0x4E02
            status = 0
            response_count = None
            response_capture = "8192-byte-raw-prefix"
            setter_prefix_sha256 = hashlib.sha256(setter_raw).hexdigest()
            getter_prefix_sha256 = hashlib.sha256(getter_raw).hexdigest()
            getter_record_sha256 = None
            getter_record_complete = False
        else:
            assert getter is not None and getter["kind"] == 0x4E02
            getter_arguments = getter["arguments"]
            assert [number(getter_arguments[index]) for index in (0, 1, 4)] == [0x2301, 0, 1]
            getter_record = blob(getter_arguments[3])
            assert number(getter_arguments[2]) == len(getter_record)
            getter_record_length = len(getter_record)
            getter_record_sha256 = hashlib.sha256(getter_record).hexdigest()
            getter_record_complete = True
            response_capture = "decoded"
            setter_prefix_sha256 = None
            getter_prefix_sha256 = None

        if not maximum_comment:
            if setter is None:
                response_kind = None
                status = None
                response_count = None
            else:
                response_kind = setter["kind"]
                if response_kind == 0x4E02:
                    arguments = setter["arguments"]
                    assert number(arguments[0]) == 0x2401
                    status = number(arguments[1])
                    response_count = number(arguments[4])
                else:
                    assert response_kind == 0x0100 and setter["arguments"] == []
                    status = None
                    response_count = None

        outcome = f"status-{status}" if status is not None else "no-status"
        axis_counts[variant["axis"]][outcome] += 1
        results.append({
            **variant,
            "response_kind": response_kind,
            "status": status,
            "response_record_count": response_count,
            "response_capture": response_capture,
            "setter_prefix_sha256": setter_prefix_sha256,
            "getter_record_length": getter_record_length,
            "getter_record_sha256": getter_record_sha256,
            "getter_record_complete": getter_record_complete,
            "getter_prefix_sha256": getter_prefix_sha256,
            "database_memberships": record_state,
            "record_snapshot_sha256": sha256(record_snapshot_path),
            "repeat_snapshot_sha256": sha256(repeat_snapshot_path),
            "receipt_sha256": sha256(receipt),
            "suite_sha256": sha256(suite),
            "golden_sha256": sha256(golden),
            "case_executions": 2,
        })

    complete = len(results) == len(matrix["variants"])
    if not args.allow_partial:
        assert complete

    document = {
        "format": 1,
        "experiment": "hot-cue-extended-setter-fields",
        "complete": complete,
        "declared_variants": len(matrix["variants"]),
        "completed_variants": len(results),
        "case_executions": sum(result["case_executions"] for result in results),
        "fixture_database_sha256": fixture["database_sha256"],
        "matrix_sha256": sha256(MATRIX),
        "axis_counts": {axis: dict(sorted(counts.items())) for axis, counts in sorted(axis_counts.items())},
        "results": results,
    }
    output = OUTPUT if complete else OUTPUT.with_name("summary.partial.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n")
    print(f"validated {len(results)}/{len(matrix['variants'])} mutable-field variants")


if __name__ == "__main__":
    main()
