#!/usr/bin/env python3
"""Validate and summarize two-player Link-played ownership evidence."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CONFORMANCE = ROOT / "conformance"
sys.path.insert(0, str(ROOT / "tools"))

from rekordbox_health import health_signature
from summarize_link_played_state import row_state, scalar


FIXTURE = CONFORMANCE / "fixtures/generated/full/manifest.json"
INDEX = CONFORMANCE / "data/link-played-multiplayer.json"
IDENTITIES = {
    1: CONFORMANCE / "runs/xdj-rx3-player-1.json",
    2: CONFORMANCE / "runs/xdj-rx3-player-2.json",
}
GOLDENS = CONFORMANCE / "goldens/rekordbox-7.2.19/xdj-rx3"
SETTINGS = ROOT / "data/experiments/played-track-state/settings/manifest.json"
EVIDENCE = ROOT / "data/experiments/played-track-state/multiplayer"
CAPTURE_RECEIPT = EVIDENCE / "receipt.json"
OUTPUT = EVIDENCE / "summary.json"
RUNS = (1, 2)


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_document(path: Path, suite_path: Path, manifest: dict, player: int) -> dict[str, dict]:
    suite = load(suite_path)
    document = load(path)
    provenance = document["provenance"]
    assert provenance["backend"] == "rekordbox"
    assert provenance["backend_version"] == "7.2.19"
    assert provenance["suite_sha256"] == sha256(suite_path)
    assert provenance["fixture_database_sha256"] == manifest["database_sha256"]
    assert provenance["fixture_fingerprint"] == manifest["fixture_fingerprint"]
    assert provenance["identity"]["player"] == player
    assert suite["defaults"]["device"] == player
    assert suite["defaults"]["context"] == f"0x{player:02x}010301"
    declarations = {case["id"]: case for case in suite["cases"]}
    cases = {case["id"]: case for case in document["behavior"]["cases"]}
    assert declarations.keys() == cases.keys()
    return cases


def observations(cases: dict[str, dict], manifest: dict) -> dict:
    track_ids = (manifest["ids"]["track.first"], manifest["ids"]["track.second"])

    def scalar_observation(identifier: str) -> dict:
        case = cases[identifier]
        if case["outcome"] != "raw_reply":
            return {"outcome": case["outcome"]}
        return {"outcome": "raw_reply", "value": scalar(case)}

    def row_observation(identifier: str) -> dict:
        case = cases[identifier]
        if case["outcome"] != "menu":
            return {"outcome": case["outcome"], "total": case["total"]}
        return {
            "outcome": "menu",
            "tracks": row_state(case, track_ids),
        }

    return {
        "before": {
            "scalar_0x3b03": {
                "first": scalar_observation("first-state-before"),
                "second": scalar_observation("second-state-before"),
            },
            "row_0x4101_argument_7": row_observation("tracks-before"),
        },
        "after": {
            "scalar_0x3b03": {
                "first": scalar_observation("first-state-after"),
                "second": scalar_observation("second-state-after"),
            },
            "row_0x4101_argument_7": row_observation("tracks-after"),
        },
    }


def validate_run(run: int, entries: list[dict], manifest: dict) -> dict:
    run_dir = EVIDENCE / "repeats" / f"run-{run}"
    receipt_path = run_dir / "receipt.json"
    receipt = load(receipt_path)
    assert receipt["run"] == run
    assert receipt["simultaneous_identity_count"] == 2
    assert receipt["same_rekordbox_process"] is True
    assert receipt["options_sha256"] == sha256(run_dir / "options.json")
    options = {item["name"]: item["val"] for item in load(run_dir / "options.json")}
    assert options == {"PlayedTrackOption": 1, "LinkPlayedTrackOption": 1}

    live_manifests = {}
    for player in (1, 2):
        path = run_dir / f"player-{player}-live.json"
        assert receipt[f"player_{player}_manifest_sha256"] == sha256(path)
        live = load(path)
        configured = load(IDENTITIES[player])
        for field in (
            "model",
            "player",
            "device_type",
            "generation",
            "mac",
            "address",
            "packet_sha256",
        ):
            assert live[field] == configured[field]
        live_manifests[player] = live

    response_hashes = {item["id"]: item["sha256"] for item in receipt["responses"]}
    assert set(response_hashes) == {entry["id"] for entry in entries}
    for entry in entries:
        path = run_dir / f"{entry['id']}.json"
        assert response_hashes[entry["id"]] == sha256(path)
        suite_path = CONFORMANCE / entry["suite"]
        validate_document(path, suite_path, manifest, entry["player"])

    health_hashes = {item["name"]: item["sha256"] for item in receipt["health"]}
    health_paths = sorted(run_dir.glob("*-health.json"))
    assert len(health_paths) == 5
    assert health_hashes == {path.name: sha256(path) for path in health_paths}
    rekordbox_pids = set()
    for path in health_paths:
        document = load(path)
        signature = health_signature(document)
        assert signature["process_count"] == 1
        assert signature["responding_count"] == 1
        assert signature["application_events"] == []
        assert sum(item["local_port"] == 12523 for item in document["tcp_listeners"]) >= 1
        rekordbox_pids.add(document["rekordbox_processes"][0]["id"])
    assert len(rekordbox_pids) == 1

    checkpoint_hashes = {
        item["name"]: item["sha256"] for item in receipt["identity_checkpoints"]
    }
    checkpoint_paths = sorted(run_dir.glob("identities-*.json"))
    assert len(checkpoint_paths) == 5
    assert checkpoint_hashes == {path.name: sha256(path) for path in checkpoint_paths}
    identity_pids = {1: set(), 2: set()}
    for path in checkpoint_paths:
        checkpoint = load(path)
        assert len(checkpoint["players"]) == 2
        for player in checkpoint["players"]:
            number = player["player"]
            assert player["active_state"] == "active"
            assert player["host_process_id"] > 0
            assert player["live_manifest_sha256"] == sha256(
                run_dir / f"player-{number}-live.json"
            )
            identity_pids[number].add(player["host_process_id"])
    assert all(len(values) == 1 for values in identity_pids.values())
    assert identity_pids[1] != identity_pids[2]

    return {
        "run": run,
        "rekordbox_process_id": next(iter(rekordbox_pids)),
        "identity_process_ids": {
            str(player): next(iter(values)) for player, values in identity_pids.items()
        },
        "receipt_sha256": sha256(receipt_path),
    }


def main() -> None:
    manifest = load(FIXTURE)
    declaration = load(INDEX)
    capture = load(CAPTURE_RECEIPT)
    entries = declaration["sequence"]
    assert declaration["suite_count"] == 4
    assert declaration["case_count"] == 28
    assert [entry["player"] for entry in entries] == [1, 2, 1, 2]
    assert capture["format"] == 1
    assert capture["identity_count"] == 2
    assert capture["phase_count"] == 4
    assert capture["case_count"] == 28
    assert capture["run_count"] == 2
    assert capture["suite_execution_count"] == 8
    assert capture["exact_repeat"] is True
    assert capture["same_process_per_run"] is True
    assert capture["guest_state_restored"] is True
    assert capture["fixture_manifest_sha256"] == sha256(FIXTURE)
    assert capture["settings_manifest_sha256"] == sha256(SETTINGS)
    assert capture["declaration_index_sha256"] == sha256(INDEX)
    assert capture["identity_1_sha256"] == sha256(IDENTITIES[1])
    assert capture["identity_2_sha256"] == sha256(IDENTITIES[2])

    timeline = []
    for entry in entries:
        suite_path = CONFORMANCE / entry["suite"]
        golden_path = GOLDENS / f"{entry['id']}.json"
        cases = validate_document(golden_path, suite_path, manifest, entry["player"])
        timeline.append(
            {
                "phase": entry["id"],
                "player": entry["player"],
                "observations": observations(cases, manifest),
                "golden_sha256": sha256(golden_path),
            }
        )

    runs = [validate_run(run, entries, manifest) for run in RUNS]
    assert capture["run_1_receipt_sha256"] == runs[0]["receipt_sha256"]
    assert capture["run_2_receipt_sha256"] == runs[1]["receipt_sha256"]
    summary = {
        "format": 1,
        "scope": "real Rekordbox 7.2.19 two-player Link-played ownership",
        "fixture_profile": manifest["profile"],
        "fixture_database_sha256": manifest["database_sha256"],
        "fixture_fingerprint": manifest["fixture_fingerprint"],
        "identity_count": 2,
        "same_process_per_run": True,
        "timeline": timeline,
        "runs": runs,
        "sha256": {
            "fixture_manifest": sha256(FIXTURE),
            "settings_manifest": sha256(SETTINGS),
            "declaration_index": sha256(INDEX),
            "identity_1": sha256(IDENTITIES[1]),
            "identity_2": sha256(IDENTITIES[2]),
            "capture_receipt": sha256(CAPTURE_RECEIPT),
        },
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(OUTPUT)


if __name__ == "__main__":
    main()
