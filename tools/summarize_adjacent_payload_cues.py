#!/usr/bin/env python3
"""Validate and decode the real-Rekordbox adjacent cue-payload oracle."""

from __future__ import annotations

import csv
import hashlib
import json
import struct
from collections import Counter, defaultdict
from pathlib import Path

try:
    from .rekordbox_health import validate_health_pair
except ImportError:
    from rekordbox_health import validate_health_pair

try:
    from .summarize_adjacent_payload_fileless import summarize, write_json
except ImportError:
    from summarize_adjacent_payload_fileless import summarize, write_json


ROOT = Path(__file__).resolve().parent.parent
CONFORMANCE = ROOT / "conformance"
INDEX = CONFORMANCE / "data/adjacent-payload-cue-matrix.json"
FIXTURE = CONFORMANCE / "fixtures/generated/adjacent-payload-cues/manifest.json"
GOLDEN_ROOT = CONFORMANCE / "goldens/rekordbox-7.2.19"
EVIDENCE = ROOT / "data/experiments/adjacent-payload/cues"
OUTPUT = EVIDENCE / "summary.json"
CSV_OUTPUT = EVIDENCE / "matrix.csv"
SCOPE = "real Rekordbox 7.2.19 adjacent cue payload matrix"
EXPECTED_COUNTS = {
    "zero": 0,
    "one": 1,
    "three": 3,
    "count-255": 255,
    "count-256": 256,
    "timing": 1,
    "color": 1,
    "comment-empty": 1,
    "comment-ascii": 1,
    "comment-unicode": 1,
    "comment-nul": 1,
    "beat-loop": 1,
    "microseconds": 1,
    "null-options": 1,
    "seek-in": 1,
    "seek-out-only": 1,
    "seek-malformed": 1,
    "deleted-only": 0,
    "mixed-deleted": 1,
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path):
    return json.loads(path.read_text())


def content_axis(identifier: str) -> str:
    if "--content-" in identifier:
        return identifier.split("--content-", 1)[1]
    return "one"


def response_sha256(case: dict) -> str:
    document = {
        "outcome": case["outcome"],
        "error_kind": case["raw_response"].get("error_kind"),
        "messages": case["raw_response"].get("messages", []),
    }
    return hashlib.sha256(
        json.dumps(document, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def message_arguments(case: dict, reply_kind: int) -> list[dict]:
    response = case["raw_response"]
    messages = response.get("messages", [])
    if response.get("error_kind") is not None or len(messages) != 1:
        raise ValueError("cue success must contain one error-free direct reply")
    if messages[0]["kind"] != reply_kind:
        raise ValueError(f"unexpected cue reply kind: {messages[0]['kind']:04x}")
    return messages[0]["arguments"]


def legacy_records(case: dict) -> tuple[list[tuple[int, ...]], list[tuple[int, int]]]:
    arguments = message_arguments(case, 0x4702)
    values = [argument.get("value") for argument in arguments]
    cue_blob = bytes.fromhex(arguments[3]["hex"])
    extension_blob = bytes.fromhex(arguments[8]["hex"])
    expected = [0x2104, 0, len(cue_blob), None, 36, len(cue_blob) // 36, 0, len(extension_blob), None]
    if values != expected or len(cue_blob) % 36 or len(extension_blob) != len(cue_blob) // 36 * 8:
        raise ValueError("legacy cue reply framing is inconsistent")
    records = [
        struct.unpack("<9I", cue_blob[offset : offset + 36])
        for offset in range(0, len(cue_blob), 36)
    ]
    extensions = [
        struct.unpack("<II", extension_blob[offset : offset + 8])
        for offset in range(0, len(extension_blob), 8)
    ]
    return records, extensions


def extended_records(case: dict) -> list[dict]:
    arguments = message_arguments(case, 0x4E02)
    values = [argument.get("value") for argument in arguments]
    blob = bytes.fromhex(arguments[3]["hex"])
    if values[:4] != [0x2B04, int(not blob), len(blob), None]:
        raise ValueError("extended cue reply framing is inconsistent")

    records = []
    offset = 0
    while offset < len(blob):
        if len(blob) - offset < 74:
            raise ValueError("extended cue record is shorter than its fixed fields")
        size = struct.unpack_from("<I", blob, offset)[0]
        record = blob[offset : offset + size]
        if len(record) != size:
            raise ValueError("extended cue record exceeds the reply blob")
        option_bytes = struct.unpack_from("<I", record, 52)[0]
        if size != (56 + option_bytes + 3) & ~3:
            raise ValueError("extended cue option length does not match record size")

        comment_bytes = struct.unpack_from("<H", record, 72)[0]
        comment_end = 74 + comment_bytes
        if comment_end > len(record):
            raise ValueError("extended cue comment exceeds its record")
        comment = record[74:comment_end].decode("utf-16-le").rstrip("\0")
        seek = (0, 0, 0, 0, 0, 0)
        if option_bytes > 18 + comment_bytes:
            if comment_end + 44 > len(record) or struct.unpack_from("<Q", record, comment_end)[0] != 44:
                raise ValueError("extended cue seek block is malformed")
            seek = struct.unpack_from(">QQQQII", record, comment_end + 8)

        records.append(
            {
                "size": size,
                "slot": struct.unpack_from("<H", record, 4)[0],
                "cue_type": record[6],
                "time_unit": struct.unpack_from("<H", record, 10)[0],
                "in_msec": struct.unpack_from("<i", record, 12)[0],
                "out_msec": struct.unpack_from("<i", record, 16)[0],
                "marker": struct.unpack_from("<I", record, 24)[0],
                "sentinel": struct.unpack_from("<i", record, 32)[0],
                "in_mpeg_frame": struct.unpack_from("<i", record, 36)[0],
                "out_mpeg_frame": struct.unpack_from("<i", record, 40)[0],
                "in_mpeg_abs": struct.unpack_from("<i", record, 44)[0],
                "out_mpeg_abs": struct.unpack_from("<i", record, 48)[0],
                "option_bytes": option_bytes,
                "color_plus_one": record[58],
                "cue_microsec": struct.unpack_from("<I", record, 60)[0],
                "beat_loop_words": struct.unpack_from("<HH", record, 66),
                "comment_bytes": comment_bytes,
                "comment": comment,
                "seek": seek,
            }
        )
        offset += size

    if offset != len(blob) or len(records) != values[4]:
        raise ValueError("extended cue record count differs from reply framing")
    return records


def decode(case: dict, kind: str) -> tuple[int | None, int, str]:
    if case["outcome"] != "raw_reply":
        return None, 0, ""

    if kind == "2104":
        records, extensions = legacy_records(case)
        return len(records), len(records) * 44, json.dumps(
            {"records": records, "extensions": extensions},
            separators=(",", ":"),
        )

    records = extended_records(case)
    return len(records), sum(record["size"] for record in records), json.dumps(
        records,
        ensure_ascii=False,
        separators=(",", ":"),
    )


def validate_receipt(entry: dict, suite: Path, golden: Path) -> None:
    evidence = EVIDENCE / "variants" / entry["variant"]
    receipt_path = evidence / "receipt.json"
    receipt = load(receipt_path)
    identity = CONFORMANCE / entry["identity"]
    expected = {
        "scope": SCOPE,
        "variant": f"cue-{entry['variant']}",
        "suite_sha256": sha256(suite),
        "fixture_manifest_sha256": sha256(FIXTURE),
        "identity_sha256": sha256(identity),
        "golden_sha256": sha256(golden),
        "case_count": entry["case_count"],
        "service_count": entry["service_count"],
        "exact_repeat": True,
    }
    for field, value in expected.items():
        if receipt.get(field) != value:
            raise ValueError(f"{receipt_path}: {field} differs from expected value")

    validate_health_pair(
        evidence,
        receipt,
        f"adjacent-payload-cue-{entry['variant']}",
        sha256,
    )


def summarize_cues() -> tuple[dict, list[dict]]:
    index = load(INDEX)
    if index["format"] != 1 or index["variant_count"] != 8 or index["case_count"] != 114:
        raise ValueError("adjacent cue declaration index changed")
    if index["fixture_manifest_sha256"] != sha256(FIXTURE):
        raise ValueError("adjacent cue fixture hash differs from declaration index")

    matrix = []
    variant_signatures: dict[str, dict[str, str]] = defaultdict(dict)
    for entry in index["variants"]:
        suite = CONFORMANCE / entry["suite"]
        golden = GOLDEN_ROOT / entry["golden_model"] / entry["golden"]
        if entry["suite_sha256"] != sha256(suite):
            raise ValueError(f"{entry['variant']}: suite hash differs from declaration index")

        _summary, rows = summarize(
            suite,
            FIXTURE,
            golden,
            expected_case_count=entry["case_count"],
            expected_service_count=entry["service_count"],
            scope=SCOPE,
            enforce_expected_oracle=False,
        )
        validate_receipt(entry, suite, golden)
        observed = {case["id"]: case for case in load(golden)["behavior"]["cases"]}

        for row in rows:
            case = observed[row["id"]]
            content = content_axis(row["id"])
            count, payload_bytes, decoded = decode(case, row["kind"])
            if entry["risk"] == "none":
                if case["outcome"] != "raw_reply":
                    raise ValueError(f"{entry['variant']}/{row['id']}: safe cue case did not reply")
                if count != EXPECTED_COUNTS[content]:
                    raise ValueError(
                        f"{entry['variant']}/{row['id']}: expected {EXPECTED_COUNTS[content]} records, got {count}"
                    )

            signature = response_sha256(case)
            variant_signatures[entry["variant"]][row["id"]] = signature
            matrix.append(
                {
                    "variant": entry["variant"],
                    "model": entry["golden_model"],
                    "player": entry["player"],
                    "setup": entry["setup"],
                    "risk": entry["risk"],
                    "id": row["id"],
                    "kind": row["kind"],
                    "content": content,
                    "outcome": row["outcome"],
                    "error_kind": row["error_kind"],
                    "record_count": count,
                    "payload_bytes": payload_bytes,
                    "response_sha256": signature,
                    "decoded": decoded,
                }
            )

    baseline = variant_signatures["baseline"]
    for kind in ("2104", "2b04"):
        context_ids = [
            identifier for identifier in baseline
            if identifier.startswith(f"kind-{kind}--type-")
            or identifier.startswith(f"kind-{kind}--location-")
        ]
        if len({baseline[identifier] for identifier in context_ids}) != 1:
            raise ValueError(f"0x{kind} changed across track-type or location controls")

    outcome_counts = Counter(row["outcome"] for row in matrix)
    summary = {
        "format": 1,
        "scope": SCOPE,
        "index_sha256": sha256(INDEX),
        "fixture_manifest_sha256": sha256(FIXTURE),
        "fixture_database_sha256": load(FIXTURE)["database_sha256"],
        "fixture_fingerprint": load(FIXTURE)["fixture_fingerprint"],
        "variant_count": index["variant_count"],
        "case_count": len(matrix),
        "outcome_counts": dict(sorted(outcome_counts.items())),
        "independently_repeated_variants": index["variant_count"],
        "context_invariant_kinds": ["2104", "2b04"],
        "status_setup_comparison": {
            variant: signatures
            for variant, signatures in sorted(variant_signatures.items())
            if "status" in variant
        },
    }
    return summary, matrix


def write_csv(path: Path, matrix: list[dict]) -> None:
    fields = (
        "variant", "model", "player", "setup", "risk", "id", "kind",
        "content", "outcome", "error_kind", "record_count", "payload_bytes",
        "response_sha256", "decoded",
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    candidate = path.with_name(f"{path.name}.next")
    with candidate.open("w", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        writer.writerows(matrix)
    candidate.replace(path)


def main() -> None:
    summary, matrix = summarize_cues()
    write_json(OUTPUT, summary)
    write_csv(CSV_OUTPUT, matrix)
    print(f"wrote {OUTPUT} and {CSV_OUTPUT}: {len(matrix)} cases")


if __name__ == "__main__":
    main()
