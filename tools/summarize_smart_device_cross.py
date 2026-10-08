#!/usr/bin/env python3
"""Validate and summarize the SmartList device-identity cross."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from summarize_search_oracle import load, sha256, validate


ROOT = Path(__file__).resolve().parent.parent
CONFORMANCE = ROOT / "conformance"
SUITE = CONFORMANCE / "suites/smart-device-cross.json"
MANIFEST = CONFORMANCE / "fixtures/generated/smart-rule-matrix/manifest.json"
RESULT = CONFORMANCE / "results/rbxport/c144f19+tree.80e87ec8aace/summary.json"
MODELS = (
    "xdj-rx3",
    "cdj-3000",
    "cdj-2000nxs2",
    "xdj-xz",
    "xdj-az",
    "xdj-1000mk2",
    "unknown-mixer",
    "unknown-djm",
)


def canonical_sha256(value: object) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode() + b"\n"
    return hashlib.sha256(payload).hexdigest()


def item_ids(case: dict[str, object]) -> list[int]:
    return [row["arguments"][1]["value"] for row in case["rows"]]


def main() -> None:
    manifest = load(MANIFEST)
    replay = load(RESULT)
    replay_by_model = {
        entry["model"]: entry
        for entry in replay["suites"]
        if entry["suite"] == "smart-device-cross"
    }
    assert set(replay_by_model) == set(MODELS)

    identities = {}
    behavior_hashes = set()
    case_hashes = set()
    for model in MODELS:
        golden_path = (
            CONFORMANCE
            / "goldens/rekordbox-7.2.19"
            / model
            / "smart-device-cross.json"
        )
        cases = validate(SUITE, golden_path, MANIFEST)
        golden = load(golden_path)
        behavior_hash = canonical_sha256(golden["behavior"])
        behavior_hashes.add(behavior_hash)
        case_hash = canonical_sha256(golden["behavior"]["cases"])
        case_hashes.add(case_hash)

        assert item_ids(cases["populated"]) == list(range(10001, 10009))
        assert cases["populated"]["outcome"] == "menu"
        assert cases["populated"]["total"] == 8
        assert cases["empty"]["outcome"] == "menu"
        assert cases["empty"]["total"] == 0
        assert cases["empty"]["rows"] == []

        result = replay_by_model[model]
        assert result["cases"] == 2
        assert result["exact_cases"] == ["empty"]
        assert result["same_outcome_total_row_count_cases"] == ["empty"]
        assert result["different_cases"] == ["populated"]

        identity = golden["provenance"]["identity"]
        identities[model] = {
            "advertised_model": identity["model"],
            "device_type": identity["device_type"],
            "generation": identity["generation"],
            "player": identity["player"],
            "packet_sha256": identity["packet_sha256"],
            "golden_sha256": sha256(golden_path),
            "behavior_sha256": behavior_hash,
            "behavior_cases_sha256": case_hash,
            "immediate_repeat_verified": True,
        }

    assert len(behavior_hashes) == 1
    assert len(case_hashes) == 1

    report = {
        "format": "rekordbox-link-export-smart-device-cross-v1",
        "oracle": {
            "identity_count": len(MODELS),
            "cases_per_identity": 2,
            "canonical_cases": len(MODELS) * 2,
            "suite_sha256": sha256(SUITE),
            "behavior_sha256": behavior_hashes.pop(),
            "behavior_cases_sha256": case_hashes.pop(),
            "behavior_identical_across_identities": True,
            "identities": identities,
        },
        "fixture": {
            "profile": "smart-rule-matrix",
            "database_sha256": manifest["database_sha256"],
            "fingerprint": manifest["fixture_fingerprint"],
            "populated_playlist": manifest["ids"]["playlist.smart_matrix.logic_any"],
            "empty_playlist": manifest["ids"]["playlist.smart_matrix.empty_all"],
            "tracks": manifest["track_count"],
        },
        "behavior": {
            "populated_item_ids": list(range(10001, 10009)),
            "empty_item_ids": [],
            "device_identity_changes_smart_membership_or_rows": False,
        },
        "rbxport": {
            "version": replay["backend_version"],
            "cases": len(MODELS) * 2,
            "exact": len(MODELS),
            "same_outcome_total_row_count": len(MODELS),
            "different": len(MODELS),
            "exact_case_per_identity": "empty",
            "different_case_per_identity": "populated",
        },
    }
    output = ROOT / "data/experiments/smart-device-cross/summary.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(output)


if __name__ == "__main__":
    main()
