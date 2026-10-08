#!/usr/bin/env python3
import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

try:
    from .rekordbox_health import validate_health_pair
except ImportError:
    from rekordbox_health import validate_health_pair


ROOT = Path(__file__).resolve().parent.parent
CONFORMANCE = ROOT / "conformance"
MATRIX = CONFORMANCE / "data/song-info-location2-malformed-history-matrix.json"
MANIFEST = CONFORMANCE / "fixtures/generated/full/manifest.json"
SUITE_ROOT = CONFORMANCE / "suites/generated/song-info-location2-malformed-history"
GOLDEN_ROOT = CONFORMANCE / "goldens/rekordbox-7.2.19/xdj-rx3-status/song-info-location2-malformed-history-lifecycle"
RECEIPT_ROOT = ROOT / "data/experiments/song-info-status-location2/malformed-history-lifecycle/repeats"
IDENTITY = CONFORMANCE / "runs/xdj-rx3-player-11-status.json"
OUTPUT_ROOT = ROOT / "data/experiments/song-info-status-location2/malformed-history-lifecycle"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--allow-partial",
        action="store_true",
        help="summarize only pairs with promoted goldens and valid receipts",
    )
    return parser.parse_args()


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def outcome(case: dict) -> dict:
    return {
        "outcome": case["outcome"],
        "total": case.get("total"),
        "response_kind": case.get("response_kind"),
    }


def main() -> None:
    args = parse_args()
    matrix = load(MATRIX)
    manifest = load(MANIFEST)
    assert matrix["precursor_count"] == 16
    assert matrix["ordered_pair_count"] == 256
    assert matrix["cases_per_pair"] == 3
    assert matrix["pre_request_drain_ms"] == 1200

    rows = []
    pending = []
    partitions = Counter()
    for pair in matrix["pairs"]:
        pair_id = pair["id"]
        suite_path = SUITE_ROOT / f"{pair_id}.json"
        golden_path = GOLDEN_ROOT / f"{pair_id}.json"
        evidence = RECEIPT_ROOT / pair_id
        receipt_path = evidence / "receipt.json"
        if not golden_path.is_file() and not receipt_path.is_file():
            pending.append(pair_id)
            continue
        if not golden_path.is_file() or not receipt_path.is_file():
            raise FileNotFoundError(
                f"{pair_id}: promoted golden and receipt must exist together"
            )
        suite = load(suite_path)
        golden = load(golden_path)
        receipt = load(receipt_path)

        assert receipt["pair"] == pair_id
        assert receipt["independently_repeated"] is True
        assert receipt["suite_sha256"] == sha256(suite_path)
        assert receipt["fixture_manifest_sha256"] == sha256(MANIFEST)
        assert receipt["identity_sha256"] == sha256(IDENTITY)
        assert receipt["golden_sha256"] == sha256(golden_path)
        health = validate_health_pair(
            evidence,
            receipt,
            f"location2-malformed-history-{pair_id}",
            sha256,
        )
        provenance = golden["provenance"]
        assert provenance["backend"] == "rekordbox"
        assert provenance["backend_version"] == "7.2.19"
        assert provenance["suite_sha256"] == sha256(suite_path)
        assert provenance["fixture_database_sha256"] == manifest["database_sha256"]
        assert provenance["fixture_fingerprint"] == manifest["fixture_fingerprint"]
        assert provenance["identity"]["model"] == "XDJ-RX3"
        assert provenance["identity"]["player"] == 11
        assert provenance["identity"]["packet_sha256"] == (
            "da12196004059977cdbcd83b9e0ae22366a2daf50320ed1a7b033c1d7ab157d4"
        )

        cases = golden["behavior"]["cases"]
        assert [case["id"] for case in cases] == [
            f"first--{pair['first']}",
            f"second--{pair['second']}",
            "delivery-probe",
        ]
        first, second, probe = map(outcome, cases)
        drains = [case["pre_request_drain"] for case in cases]
        setups = [case["connection_setup_exchange"] for case in cases]
        assert all(
            setup["response"]
            == [{"transaction": 0xFFFFFFFE, "kind": 0, "arguments": [
                {"type": "number", "value": 17},
                {"type": "number", "value": 20},
            ]}]
            for setup in setups
        )
        partition = (
            f"{first['outcome']}:{first['total']}|"
            f"{second['outcome']}:{second['total']}|"
            f"{probe['outcome']}:{probe['total']}"
        )
        partitions[partition] += 1
        rows.append(
            {
                "pair": pair_id,
                "first": pair["first"],
                "second": pair["second"],
                "first_outcome": first["outcome"],
                "first_total": first["total"],
                "second_outcome": second["outcome"],
                "second_total": second["total"],
                "probe_outcome": probe["outcome"],
                "probe_total": probe["total"],
                "first_drain_outcome": drains[0]["outcome"],
                "second_drain_outcome": drains[1]["outcome"],
                "probe_drain_outcome": drains[2]["outcome"],
                "drain_raw_reply_count": sum(
                    drain["outcome"] == "raw_reply" for drain in drains
                ),
                "drain_raw_hex": "|".join(
                    drain["raw_hex"]
                    for drain in drains
                    if drain["outcome"] == "raw_reply"
                ),
                "process_count": health["process_count"],
                "responding_count": health["responding_count"],
                "application_event_count": len(health["application_events"]),
                "golden_sha256": sha256(golden_path),
                "receipt_sha256": sha256(receipt_path),
            }
        )

    if pending and not args.allow_partial:
        raise FileNotFoundError(
            f"malformed-history matrix has {len(pending)} pending pairs"
        )
    assert rows

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    summary = {
        "format": 1,
        "experiment": matrix["experiment"],
        "matrix_sha256": sha256(MATRIX),
        "fixture_database_sha256": manifest["database_sha256"],
        "fixture_fingerprint": manifest["fixture_fingerprint"],
        "ordered_pairs": len(rows),
        "case_executions": len(rows) * 3,
        "independent_repeat_receipts": len(rows),
        "complete": not pending,
        "pending_ordered_pairs": len(pending),
        "next_pending_pair": pending[0] if pending else None,
        "partitions": dict(sorted(partitions.items())),
        "rows": rows,
    }
    summary_path = OUTPUT_ROOT / (
        "summary.partial.json" if args.allow_partial else "summary.json"
    )
    matrix_path = OUTPUT_ROOT / (
        "matrix.partial.csv" if args.allow_partial else "matrix.csv"
    )
    summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n"
    )

    with matrix_path.open("w", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(summary_path)
    print(matrix_path)


if __name__ == "__main__":
    main()
