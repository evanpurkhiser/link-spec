#!/usr/bin/env python3
"""Validate and summarize the fileless adjacent-payload Rekordbox oracle."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

try:
    from .rekordbox_health import validate_health_pair
except ImportError:
    from rekordbox_health import validate_health_pair


ROOT = Path(__file__).resolve().parent.parent
SUITE = ROOT / "conformance/suites/adjacent-payload-fileless.json"
MANIFEST = ROOT / "conformance/fixtures/generated/full/manifest.json"
GOLDEN = (
    ROOT
    / "conformance/goldens/rekordbox-7.2.19/xdj-rx3/adjacent-payload-fileless.json"
)
OUTPUT = ROOT / "data/experiments/adjacent-payload/fileless/summary.json"
CSV_OUTPUT = ROOT / "data/experiments/adjacent-payload/fileless/matrix.csv"
EVIDENCE = ROOT / "data/experiments/adjacent-payload/fileless"
IDENTITY = ROOT / "conformance/runs/xdj-rx3-player-11.json"
ALLOWED_OUTCOMES = {"raw_reply", "timeout", "disconnect"}


def number(value: int) -> dict[str, object]:
    return {"type": "number", "value": value}


def blob(value: str = "") -> dict[str, object]:
    return {"hex": value, "type": "blob"}


EXPECTED_TIMEOUT_IDS = {
    *(
        f"kind-{kind}--type-{track_type:02x}"
        for kind in ("2003", "2103")
        for track_type in (0, 2, 3, 4, 5, 6)
    ),
    *(
        f"kind-{kind}--context-{value}"
        for kind in ("2304", "2404", "2604", "2704")
        for value in ("zero", "maximum")
    ),
}
EXPECTED_MESSAGES = {
    "2003": {"kind": 0x4002, "arguments": [number(0x2003), number(50), number(0), blob()]},
    "2103": {"kind": 0x4002, "arguments": [number(0x2103), number(50), number(0), blob()]},
    "2004": {"kind": 0x4402, "arguments": [number(0x2004), number(50), number(0), blob()]},
    "2104": {
        "kind": 0x4702,
        "arguments": [
            number(0x2104), number(1), number(0), blob(), number(36),
            number(0), number(0), number(0), blob(),
        ],
    },
    "2204": {"kind": 0x4602, "arguments": [number(0x2204), number(50), number(0), blob(), number(0)]},
    "2304": {"kind": 0x4003, "arguments": [number(0x2304)]},
    "2404": {"kind": 0x4003, "arguments": [number(0x2404)]},
    "2504": {"kind": 0x4502, "arguments": [number(0x2504), number(0), number(0), blob()]},
    "2604": {"kind": 0x4003, "arguments": [number(0x2604)]},
    "2704": {"kind": 0x4003, "arguments": [number(0x2704)]},
    "2804": {"kind": 0x4000, "arguments": [number(0x2804), number(0)]},
    "2904": {"kind": 0x4A02, "arguments": [number(0x2904), number(50), number(0), blob()]},
    "2a04": {"kind": 0x4C02, "arguments": [number(0x2A04), number(50), number(0), blob()]},
    "2b04": {"kind": 0x4E02, "arguments": [number(0x2B04), number(1), number(0), blob(), number(0)]},
    "2c04": {"kind": 0x4F02, "arguments": [number(0x2C04), number(50), number(0), blob(), number(0)]},
    "2d04": {"kind": 0x4F02, "arguments": [number(0x2D04), number(50), number(0), blob(), number(0)]},
}
EXPECTED_WIRE_BYTES = {
    "2003": 39, "2103": 39, "2004": 39, "2104": 64,
    "2204": 45, "2304": 26, "2404": 26, "2504": 39,
    "2604": 26, "2704": 26, "2804": 32, "2904": 39,
    "2a04": 39, "2b04": 45, "2c04": 45, "2d04": 45,
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalized_kind(value: str | int) -> str:
    if isinstance(value, int):
        return f"{value:04x}"

    return value.removeprefix("0x").casefold()


def summarize(
    suite_path: Path,
    manifest_path: Path,
    golden_path: Path,
    *,
    expected_case_count: int = 196,
    expected_service_count: int = 16,
    scope: str = "real Rekordbox 7.2.19 fileless adjacent payload services",
    enforce_expected_oracle: bool = True,
    evidence_path: Path | None = None,
    identity_path: Path = IDENTITY,
    variant: str = "fileless",
) -> tuple[dict, list[dict]]:
    suite = json.loads(suite_path.read_text())
    manifest = json.loads(manifest_path.read_text())
    golden = json.loads(golden_path.read_text())
    provenance = golden["provenance"]
    behavior = golden["behavior"]
    declared = suite["cases"]
    observed = behavior["cases"]

    if golden["format"] != 2:
        raise ValueError("direct-response golden format must be 2")
    if provenance["backend"] != "rekordbox" or provenance["backend_version"] != "7.2.19":
        raise ValueError("golden is not a Rekordbox 7.2.19 oracle")
    if provenance["suite_sha256"] != sha256(suite_path):
        raise ValueError("golden suite hash does not match the declaration")
    if provenance["fixture_database_sha256"] != manifest["database_sha256"]:
        raise ValueError("golden fixture database hash does not match the manifest")
    if provenance["fixture_fingerprint"] != manifest["fixture_fingerprint"]:
        raise ValueError("golden fixture fingerprint does not match the manifest")
    if behavior["suite"] != suite["name"]:
        raise ValueError("golden suite name does not match the declaration")
    behavior_fixture = behavior["fixture"]
    if not isinstance(behavior_fixture, dict):
        raise ValueError("format-2 golden fixture must be an object")
    if behavior_fixture.get("profile") != suite["fixture_profile"]:
        raise ValueError("golden fixture profile does not match the declaration")
    if behavior_fixture.get("fingerprint") != manifest["fixture_fingerprint"]:
        raise ValueError("golden behavior fixture fingerprint does not match manifest")
    if behavior_fixture.get("version") != manifest["fixture_version"]:
        raise ValueError("golden behavior fixture version does not match manifest")

    declared_ids = [case["id"] for case in declared]
    observed_ids = [case["id"] for case in observed]
    if len(declared_ids) != expected_case_count or len(set(declared_ids)) != expected_case_count:
        raise ValueError(f"declaration must contain {expected_case_count} unique cases")
    if observed_ids != declared_ids:
        raise ValueError("golden cases do not exactly preserve declaration order and IDs")

    declared_by_id = {case["id"]: case for case in declared}
    matrix = []
    kind_outcomes: dict[str, Counter] = defaultdict(Counter)

    for case in observed:
        declaration = declared_by_id[case["id"]]
        kind = normalized_kind(declaration["request_kind"])
        observed_kind = normalized_kind(case["request"]["kind"])
        if observed_kind != kind:
            raise ValueError(f"{case['id']}: request kind changed")
        if not declaration["direct_response"] or declaration["render"]:
            raise ValueError(f"{case['id']}: declaration is not a direct response")
        if case["request"].get("fixed_tag_slots") != declaration.get("fixed_tag_slots"):
            raise ValueError(f"{case['id']}: fixed tag-slot declaration changed")
        if case["outcome"] not in ALLOWED_OUTCOMES:
            raise ValueError(f"{case['id']}: unexpected outcome {case['outcome']}")
        if case["outcome"] != case["raw_response"]["outcome"]:
            raise ValueError(f"{case['id']}: outer and raw outcomes differ")
        if case["header"] or case["pages"] or case["rows"] or case["total"] is not None:
            raise ValueError(f"{case['id']}: direct response contains menu fields")

        raw_hex = case["raw_response"].get("raw_hex", "")
        if len(raw_hex) % 2:
            raise ValueError(f"{case['id']}: raw response has an odd hex length")
        if enforce_expected_oracle:
            expected_outcome = (
                "timeout" if case["id"] in EXPECTED_TIMEOUT_IDS else "raw_reply"
            )
            if case["outcome"] != expected_outcome:
                raise ValueError(
                    f"{case['id']}: expected {expected_outcome}, got {case['outcome']}"
                )
            if expected_outcome == "timeout":
                if case["raw_response"].get("error_kind") != "WouldBlock":
                    raise ValueError(f"{case['id']}: timeout is not WouldBlock")
                if raw_hex or case["raw_response"].get("messages", []):
                    raise ValueError(f"{case['id']}: timeout carried response bytes")
            else:
                expected_bytes = EXPECTED_WIRE_BYTES[kind]
                if len(raw_hex) // 2 != expected_bytes:
                    raise ValueError(f"{case['id']}: unexpected raw response length")
                if case["raw_response"].get("decoded_bytes") != expected_bytes:
                    raise ValueError(f"{case['id']}: unexpected decoded response length")
                if case["raw_response"].get("error_kind") is not None:
                    raise ValueError(f"{case['id']}: raw reply carries an error")
                if case["raw_response"].get("messages") != [EXPECTED_MESSAGES[kind]]:
                    raise ValueError(f"{case['id']}: response envelope changed")
        message_kinds = [
            f"{message['kind']:04x}"
            for message in case["raw_response"].get("messages", [])
        ]
        row = {
            "id": case["id"],
            "kind": kind,
            "outcome": case["outcome"],
            "raw_bytes": len(raw_hex) // 2,
            "decoded_bytes": case["raw_response"].get("decoded_bytes", 0),
            "message_kinds": message_kinds,
            "error_kind": case["raw_response"].get("error_kind"),
        }
        matrix.append(row)
        kind_outcomes[kind][case["outcome"]] += 1

    kinds = sorted(kind_outcomes, key=lambda value: int(value, 16))
    if len(kinds) != expected_service_count:
        raise ValueError(
            f"golden must cover all {expected_service_count} adjacent payload services"
        )

    outcome_counts = Counter(row["outcome"] for row in matrix)
    if enforce_expected_oracle:
        observed_timeout_ids = {
            row["id"] for row in matrix if row["outcome"] == "timeout"
        }
        if observed_timeout_ids != EXPECTED_TIMEOUT_IDS:
            raise ValueError("observed timeout set differs from the canonical oracle")
    summary = {
        "format": 1,
        "scope": scope,
        "suite_sha256": sha256(suite_path),
        "fixture_manifest_sha256": sha256(manifest_path),
        "fixture_database_sha256": manifest["database_sha256"],
        "fixture_fingerprint": manifest["fixture_fingerprint"],
        "golden_sha256": sha256(golden_path),
        "case_count": len(matrix),
        "service_count": len(kinds),
        "expected_oracle_asserted": enforce_expected_oracle,
        "outcome_counts": dict(sorted(outcome_counts.items())),
        "services": [
            {
                "kind": kind,
                "case_count": sum(kind_outcomes[kind].values()),
                "outcomes": dict(sorted(kind_outcomes[kind].items())),
            }
            for kind in kinds
        ],
    }
    if evidence_path is not None:
        receipt_path = evidence_path / "receipt.json"
        receipt = json.loads(receipt_path.read_text())
        expected = {
            "format": 1,
            "scope": scope,
            "variant": variant,
            "suite_sha256": sha256(suite_path),
            "fixture_manifest_sha256": sha256(manifest_path),
            "identity_sha256": sha256(identity_path),
            "golden_sha256": sha256(golden_path),
            "case_count": expected_case_count,
            "service_count": expected_service_count,
            "exact_repeat": True,
        }
        for field, value in expected.items():
            if receipt.get(field) != value:
                raise ValueError(f"{variant}: receipt {field} differs")
        summary["post_request_health"] = validate_health_pair(
            evidence_path,
            receipt,
            f"adjacent-payload-{variant}",
            sha256,
        )
        summary["receipt_sha256"] = sha256(receipt_path)
    return summary, matrix


def write_json(path: Path, document: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    candidate = path.with_name(f"{path.name}.next")
    candidate.write_text(json.dumps(document, indent=2) + "\n")
    candidate.replace(path)


def write_csv(path: Path, matrix: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    candidate = path.with_name(f"{path.name}.next")
    with candidate.open("w", newline="") as output:
        writer = csv.DictWriter(
            output,
            fieldnames=(
                "id",
                "kind",
                "outcome",
                "raw_bytes",
                "decoded_bytes",
                "message_kinds",
                "error_kind",
            ),
        )
        writer.writeheader()
        for row in matrix:
            writer.writerow({**row, "message_kinds": " ".join(row["message_kinds"])})
    candidate.replace(path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", type=Path, default=SUITE)
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    parser.add_argument("--golden", type=Path, default=GOLDEN)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--csv", type=Path, default=CSV_OUTPUT)
    parser.add_argument("--expected-cases", type=int, default=196)
    parser.add_argument("--expected-services", type=int, default=16)
    parser.add_argument(
        "--scope",
        default="real Rekordbox 7.2.19 fileless adjacent payload services",
    )
    args = parser.parse_args()

    summary, matrix = summarize(
        args.suite,
        args.manifest,
        args.golden,
        expected_case_count=args.expected_cases,
        expected_service_count=args.expected_services,
        scope=args.scope,
        evidence_path=EVIDENCE,
    )
    write_json(args.output, summary)
    write_csv(args.csv, matrix)
    print(f"wrote {args.output} and {args.csv}: {len(matrix)} cases")


if __name__ == "__main__":
    main()
