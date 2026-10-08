#!/usr/bin/env python3
"""Reduce real-Rekordbox 0x3006 goldens without importing expected outcomes."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
MATRIX = ROOT / "conformance/data/user-info-djid-matrix.json"
PROFILE_MANIFEST = ROOT / "conformance/user-info-djid-profiles/manifest.json"
EVIDENCE = ROOT / "data/experiments/user-info-djid"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def argument_value(argument: dict | None, expected_type: str):
    if not argument or argument.get("type") != expected_type:
        return None
    return argument.get("value") if expected_type == "number" else argument.get("hex")


def classify(case: dict) -> dict[str, object]:
    response = case.get("raw_response", {})
    messages = response.get("messages", [])
    result: dict[str, object] = {
        "outcome": case.get("outcome"),
        "message_count": len(messages),
        "reply_kind": None,
        "reply_argument_count": None,
        "echoed_kind": None,
        "declared_length": None,
        "blob_length": None,
        "blob_sha256": None,
        "blob_first_32_sha256": None,
        "blob_tail_all_zero": None,
        "classification": case.get("outcome", "unknown"),
    }
    if len(messages) != 1:
        return result

    message = messages[0]
    arguments = message.get("arguments", [])
    result["reply_kind"] = message.get("kind")
    result["reply_argument_count"] = len(arguments)
    result["echoed_kind"] = argument_value(arguments[0] if arguments else None, "number")
    result["declared_length"] = argument_value(
        arguments[2] if len(arguments) > 2 else None, "number"
    )
    blob_hex = argument_value(arguments[3] if len(arguments) > 3 else None, "blob")
    if blob_hex is not None:
        blob = bytes.fromhex(blob_hex)
        result["blob_length"] = len(blob)
        result["blob_sha256"] = sha256_bytes(blob)
        result["blob_first_32_sha256"] = sha256_bytes(blob[:32])
        result["blob_tail_all_zero"] = all(value == 0 for value in blob[32:])

    if (
        message.get("kind") == 0x4D02
        and len(arguments) == 4
        and result["echoed_kind"] == 0x3006
        and result["declared_length"] == 0
        and result["blob_length"] == 0
    ):
        result["classification"] = "empty-4d02"
    elif (
        message.get("kind") == 0x4D02
        and len(arguments) == 4
        and result["echoed_kind"] == 0x3006
        and result["declared_length"] == 160
        and result["blob_length"] == 160
    ):
        result["classification"] = "blob-160-4d02"
    else:
        result["classification"] = "other-reply"

    return result


def expected_classification(profile: str) -> str:
    if profile in ("valid-zero-tail", "valid-pattern-tail"):
        return "blob-160-4d02"
    return "empty-4d02"


def validate_health(path: Path) -> None:
    health = json.loads(path.read_text())
    assert health["rekordbox_process_count"] == 1, path
    assert len(health["rekordbox_processes"]) == 1, path
    assert health["rekordbox_processes"][0]["responding"] is True, path
    assert health["application_events"] == [], path


def reduce(allow_partial: bool) -> tuple[dict, list[dict]]:
    matrix = json.loads(MATRIX.read_text())
    profile_manifest = json.loads(PROFILE_MANIFEST.read_text())
    profile_rows = {profile["id"]: profile for profile in profile_manifest["profiles"]}
    observations = []
    missing = []

    for execution in matrix["executions"]:
        golden = ROOT / "conformance" / execution["golden"]
        receipt_path = EVIDENCE / execution["id"] / "receipt.json"
        if not golden.exists() or not receipt_path.exists():
            missing.append(execution["id"])
            continue

        receipt = json.loads(receipt_path.read_text())
        assert receipt["exact_repeat"] is True
        assert receipt["golden_sha256"] == sha256_bytes(golden.read_bytes())
        evidence = receipt_path.parent
        for phase in ("record", "repeat"):
            for point in ("before", "after"):
                validate_health(evidence / f"{phase}-health-{point}.json")

        payload = json.loads(golden.read_text())
        cases = payload["behavior"]["cases"]
        assert len(cases) == execution["case_count"]
        for case in cases:
            row = {
                "execution": execution["id"],
                "profile": execution["profile"],
                "identity": execution["identity"],
                "case": case["id"],
                "request_argument_count": len(case["request"]["arguments"]),
                **classify(case),
            }
            expected = expected_classification(execution["profile"])
            row["static_prediction"] = expected
            row["static_prediction_matches"] = row["classification"] == expected
            profile = profile_rows.get(execution["profile"])
            row["input_first_32_sha256"] = (
                profile["first_32_sha256"] if profile is not None else None
            )
            row["reply_first_32_matches_input"] = (
                row["blob_first_32_sha256"] == row["input_first_32_sha256"]
                if row["blob_first_32_sha256"] is not None
                and row["input_first_32_sha256"] is not None
                else None
            )
            observations.append(row)

    if missing and not allow_partial:
        raise SystemExit(f"missing canonical user-info executions: {', '.join(missing)}")

    classifications = Counter(row["classification"] for row in observations)
    conflicts = [
        {
            "execution": row["execution"],
            "profile": row["profile"],
            "case": row["case"],
            "predicted": row["static_prediction"],
            "observed": row["classification"],
        }
        for row in observations
        if not row["static_prediction_matches"]
    ]
    valid_rows = {
        row["profile"]: row
        for row in observations
        if row["profile"] in ("valid-zero-tail", "valid-pattern-tail")
    }
    valid_tail_input_invariance = None
    if len(valid_rows) == 2:
        zero = valid_rows["valid-zero-tail"]
        pattern = valid_rows["valid-pattern-tail"]
        valid_tail_input_invariance = {
            "same_reply_blob_sha256": zero["blob_sha256"] == pattern["blob_sha256"],
            "zero_tail_reply_all_zero": zero["blob_tail_all_zero"],
            "pattern_tail_reply_all_zero": pattern["blob_tail_all_zero"],
        }

    summary = {
        "format": 1,
        "scope": "real Rekordbox 7.2.19 user-info/DJ-ID authority",
        "complete": not missing,
        "declared_execution_count": matrix["execution_count"],
        "recorded_execution_count": matrix["execution_count"] - len(missing),
        "declared_case_count": matrix["case_count"],
        "recorded_case_count": len(observations),
        "record_repeat_execution_count": 2 * len(observations),
        "missing_executions": missing,
        "classifications": dict(sorted(classifications.items())),
        "static_prediction_conflicts": conflicts,
        "valid_tail_input_invariance": valid_tail_input_invariance,
        "matrix_sha256": sha256_bytes(MATRIX.read_bytes()),
        "profile_manifest_sha256": sha256_bytes(PROFILE_MANIFEST.read_bytes()),
    }
    return summary, observations


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--allow-partial", action="store_true")
    args = parser.parse_args()
    summary, observations = reduce(args.allow_partial)
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    summary_name = "summary.json" if summary["complete"] else "summary.partial.json"
    matrix_name = "matrix.csv" if summary["complete"] else "matrix.partial.csv"
    (EVIDENCE / summary_name).write_text(json.dumps(summary, indent=2) + "\n")
    fieldnames = [
        "execution",
        "profile",
        "identity",
        "case",
        "request_argument_count",
        "outcome",
        "message_count",
        "reply_kind",
        "reply_argument_count",
        "echoed_kind",
        "declared_length",
        "blob_length",
        "blob_sha256",
        "blob_first_32_sha256",
        "blob_tail_all_zero",
        "classification",
        "static_prediction",
        "static_prediction_matches",
        "input_first_32_sha256",
        "reply_first_32_matches_input",
    ]
    with (EVIDENCE / matrix_name).open("w", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(observations)
    print(EVIDENCE / summary_name)
    print(EVIDENCE / matrix_name)


if __name__ == "__main__":
    main()
