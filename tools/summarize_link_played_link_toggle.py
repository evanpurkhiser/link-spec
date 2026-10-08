#!/usr/bin/env python3
"""Validate Link-played state across a same-process LINK toggle."""

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
IDENTITY = CONFORMANCE / "runs/xdj-rx3-player-1.json"
PRIME_SUITE = CONFORMANCE / "suites/link-played-persistence-prime.json"
POST_SUITE = CONFORMANCE / "suites/link-played-link-toggle-post.json"
GOLDENS = CONFORMANCE / "goldens/rekordbox-7.2.19/xdj-rx3"
SETTINGS = ROOT / "data/experiments/played-track-state/settings/manifest.json"
EVIDENCE = ROOT / "data/experiments/played-track-state/link-toggle"
CAPTURE_RECEIPT = EVIDENCE / "receipt.json"
OUTPUT = EVIDENCE / "summary.json"
MODES = ("control", "toggle")
RUNS = (1, 2)


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_document(path: Path, suite_path: Path, manifest: dict) -> dict[str, dict]:
    suite = load(suite_path)
    document = load(path)
    provenance = document["provenance"]
    assert provenance["backend"] == "rekordbox"
    assert provenance["backend_version"] == "7.2.19"
    assert provenance["suite_sha256"] == sha256(suite_path)
    assert provenance["fixture_database_sha256"] == manifest["database_sha256"]
    assert provenance["fixture_fingerprint"] == manifest["fixture_fingerprint"]
    declarations = {case["id"]: case for case in suite["cases"]}
    cases = {case["id"]: case for case in document["behavior"]["cases"]}
    assert declarations.keys() == cases.keys()
    return cases


def observations(cases: dict[str, dict], manifest: dict, prime: bool) -> dict:
    track_ids = (manifest["ids"]["track.first"], manifest["ids"]["track.second"])
    if prime:
        scalar_ids = (
            "baseline-first-state",
            "baseline-second-state",
            "first-state-after-insert",
            "second-state-after-insert",
        )
        row_ids = ("baseline-tracks", "tracks-after-insert")
    else:
        scalar_ids = ("first-state-after-boundary", "second-state-after-boundary")
        row_ids = ("tracks-after-boundary",)
    return {
        "scalar_0x3b03": {case_id: scalar(cases[case_id]) for case_id in scalar_ids},
        "row_0x4101_argument_7": {
            case_id: row_state(cases[case_id], track_ids) for case_id in row_ids
        },
    }


def validate_health(run_dir: Path, receipt: dict, mode: str, run: int) -> dict:
    hashes = {item["name"]: item["sha256"] for item in receipt["health_sha256"]}
    paths = sorted(run_dir.glob("*-health.json"))
    assert len(paths) == 5
    assert hashes == {path.name: sha256(path) for path in paths}
    process_ids = set()
    listeners = {}
    for path in paths:
        document = load(path)
        signature = health_signature(document)
        assert signature["process_count"] == 1
        assert signature["responding_count"] == 1
        assert signature["application_events"] == []
        process_ids.add(document["rekordbox_processes"][0]["id"])
        listeners[path.name] = sum(
            listener["local_port"] == 12523 for listener in document["tcp_listeners"]
        )
    assert len(process_ids) == 1
    if mode == "toggle":
        assert listeners["inactive-health.json"] == 0
        assert listeners["reactivated-health.json"] >= 1
    else:
        assert listeners["control-boundary-health.json"] >= 1
        assert listeners["control-ready-health.json"] >= 1
    return {"process_id": next(iter(process_ids)), "listener_counts": listeners}


def main() -> None:
    manifest = load(FIXTURE)
    capture = load(CAPTURE_RECEIPT)
    assert capture["format"] == 1
    assert capture["mode_count"] == 2
    assert capture["run_count"] == 4
    assert capture["suite_execution_count"] == 8
    assert capture["exact_repeat"] is True
    assert capture["same_process_per_run"] is True
    assert capture["guest_state_restored"] is True
    assert capture["fixture_manifest_sha256"] == sha256(FIXTURE)
    assert capture["settings_manifest_sha256"] == sha256(SETTINGS)
    assert capture["prime_suite_sha256"] == sha256(PRIME_SUITE)
    assert capture["post_suite_sha256"] == sha256(POST_SUITE)
    assert capture["identity_sha256"] == sha256(IDENTITY)

    results = []
    for mode in MODES:
        prime_golden = GOLDENS / f"link-played-link-toggle-{mode}-prime.json"
        post_golden = GOLDENS / f"link-played-link-toggle-{mode}-post.json"
        prime_cases = validate_document(prime_golden, PRIME_SUITE, manifest)
        post_cases = validate_document(post_golden, POST_SUITE, manifest)
        runs = []
        for run in RUNS:
            run_dir = EVIDENCE / "repeats" / f"{mode}-run-{run}"
            receipt = load(run_dir / "receipt.json")
            assert receipt["id"] == f"{mode}-run-{run}"
            assert receipt["mode"] == mode and receipt["run"] == run
            assert receipt["same_process"] is True
            assert receipt["prime_sha256"] == sha256(run_dir / "prime.json")
            assert receipt["post_sha256"] == sha256(run_dir / "post.json")
            assert receipt["transition_sha256"] == sha256(run_dir / "transition.json")
            assert receipt["options_sha256"] == sha256(run_dir / "options.json")
            options = {item["name"]: item["val"] for item in load(run_dir / "options.json")}
            assert options == {"PlayedTrackOption": 1, "LinkPlayedTrackOption": 1}
            validate_document(run_dir / "prime.json", PRIME_SUITE, manifest)
            validate_document(run_dir / "post.json", POST_SUITE, manifest)
            transition = load(run_dir / "transition.json")
            assert transition["mode"] == mode
            if mode == "toggle":
                assert transition["transition_checkpoint_listener_count"] == 0
            else:
                assert transition["transition_checkpoint_listener_count"] >= 1
            assert transition["ready_listener_count"] >= 1
            health = validate_health(run_dir, receipt, mode, run)
            runs.append(
                {
                    "run": run,
                    "rekordbox_process_id": health["process_id"],
                    "listener_counts": dict(sorted(health["listener_counts"].items())),
                    "receipt_sha256": sha256(run_dir / "receipt.json"),
                }
            )
        results.append(
            {
                "mode": mode,
                "prime_observations": observations(prime_cases, manifest, True),
                "post_boundary_observations": observations(post_cases, manifest, False),
                "record_repeat_verified": True,
                "runs": runs,
                "sha256": {
                    "prime_golden": sha256(prime_golden),
                    "post_golden": sha256(post_golden),
                },
            }
        )

    summary = {
        "format": 1,
        "scope": "real Rekordbox 7.2.19 Link-played LINK-toggle lifecycle",
        "fixture_profile": manifest["profile"],
        "fixture_database_sha256": manifest["database_sha256"],
        "fixture_fingerprint": manifest["fixture_fingerprint"],
        "same_process_per_run": True,
        "results": results,
        "sha256": {
            "fixture_manifest": sha256(FIXTURE),
            "settings_manifest": sha256(SETTINGS),
            "prime_suite": sha256(PRIME_SUITE),
            "post_suite": sha256(POST_SUITE),
            "identity": sha256(IDENTITY),
            "capture_receipt": sha256(CAPTURE_RECEIPT),
        },
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(OUTPUT)


if __name__ == "__main__":
    main()
