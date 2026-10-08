#!/usr/bin/env python3
"""Validate Hot Cue list-buffer lifetime across a same-process LINK toggle."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CONFORMANCE = ROOT / "conformance"
sys.path.insert(0, str(ROOT / "tools"))

from rekordbox_health import health_signature
from summarize_hot_cue_buffer_disconnect import stale_classification
from summarize_search_oracle import validate


FIXTURE = CONFORMANCE / "fixtures/generated/hot-cue-banks/manifest.json"
IDENTITY = CONFORMANCE / "runs/xdj-rx3-player-1.json"
WARMUP_SUITE = CONFORMANCE / "suites/hot-cue-bank-buffer-disconnect-warmup.json"
POST_SUITE = CONFORMANCE / "suites/hot-cue-bank-buffer-disconnect-post.json"
EVIDENCE = ROOT / "data/experiments/hot-cue-bank/buffer-link-toggle"
REPEATS = EVIDENCE / "repeats"
OUTPUT = EVIDENCE / "summary.json"
MODES = ("control", "toggle")
RUNS = (1, 2)


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def item_ids(case: dict) -> list[int]:
    return [row["arguments"][1]["value"] for row in case["rows"]]


def validate_provenance(document: dict, suite: Path, manifest: dict) -> None:
    provenance = document["provenance"]
    assert provenance["backend"] == "rekordbox"
    assert provenance["backend_version"] == "7.2.19"
    assert provenance["suite_sha256"] == sha256(suite)
    assert provenance["fixture_database_sha256"] == manifest["database_sha256"]
    assert provenance["fixture_fingerprint"] == manifest["fixture_fingerprint"]
    assert provenance["identity"]["model"] == "XDJ-RX3"
    assert provenance["identity"]["player"] == 1


def validate_health(run_dir: Path, receipt: dict, mode: str, run: int) -> dict:
    receipt_hashes = {
        entry["name"]: entry["sha256"] for entry in receipt["health_sha256"]
    }
    paths = sorted(run_dir.glob("*-health.json"))
    assert len(paths) == 5
    assert receipt_hashes == {path.name: sha256(path) for path in paths}

    documents = {path.name: load(path) for path in paths}
    expected_labels = {
        "before-health.json": f"hot-cue-buffer-link-toggle-{mode}-run-{run}-before",
        "after-warmup-health.json": (
            f"hot-cue-buffer-link-toggle-{mode}-run-{run}-after-warmup"
        ),
        "after-post-health.json": (
            f"hot-cue-buffer-link-toggle-{mode}-run-{run}-after-post"
        ),
    }
    if mode == "toggle":
        expected_labels |= {
            "inactive-health.json": (
                f"hot-cue-buffer-link-toggle-{mode}-run-{run}-inactive"
            ),
            "reactivated-health.json": (
                f"hot-cue-buffer-link-toggle-{mode}-run-{run}-reactivated"
            ),
        }
    else:
        expected_labels |= {
            "control-boundary-health.json": (
                f"hot-cue-buffer-link-toggle-{mode}-run-{run}-control-boundary"
            ),
            "control-ready-health.json": (
                f"hot-cue-buffer-link-toggle-{mode}-run-{run}-control-ready"
            ),
        }
    assert set(documents) == set(expected_labels)

    process_ids = set()
    signatures = {}
    listeners = {}
    for name, document in documents.items():
        assert document["label"] == expected_labels[name]
        signature = health_signature(document)
        assert signature["process_count"] == 1
        assert signature["responding_count"] == 1
        assert signature["application_events"] == []
        signatures[name] = signature
        process_ids.add(document["rekordbox_processes"][0]["id"])
        listeners[name] = sum(
            listener["local_port"] == 12523
            for listener in document["tcp_listeners"]
        )

    assert len(process_ids) == 1
    if mode == "toggle":
        assert listeners["inactive-health.json"] == 0
        assert listeners["reactivated-health.json"] >= 1
    else:
        assert listeners["control-boundary-health.json"] >= 1
        assert listeners["control-ready-health.json"] >= 1

    return {
        "rekordbox_process_id": next(iter(process_ids)),
        "health_signature": signatures["after-post-health.json"],
        "listener_counts": dict(sorted(listeners.items())),
    }


def validate_run(mode: str, run: int, manifest: dict) -> dict:
    run_id = f"{mode}-run-{run}"
    run_dir = REPEATS / run_id
    receipt_path = run_dir / "receipt.json"
    receipt = load(receipt_path)
    warmup_path = run_dir / "warmup.json"
    post_path = run_dir / "post.json"
    transition_path = run_dir / "transition.json"
    transition = load(transition_path)

    assert receipt["format"] == 1
    assert receipt["id"] == run_id
    assert receipt["mode"] == mode
    assert receipt["fixture_manifest_sha256"] == sha256(FIXTURE)
    assert receipt["identity_sha256"] == sha256(IDENTITY)
    assert receipt["warmup_suite_sha256"] == sha256(WARMUP_SUITE)
    assert receipt["post_suite_sha256"] == sha256(POST_SUITE)
    assert receipt["warmup_sha256"] == sha256(warmup_path)
    assert receipt["post_sha256"] == sha256(post_path)
    assert receipt["transition_sha256"] == sha256(transition_path)

    warmup_document = load(warmup_path)
    post_document = load(post_path)
    validate_provenance(warmup_document, WARMUP_SUITE, manifest)
    validate_provenance(post_document, POST_SUITE, manifest)
    warmup = validate(WARMUP_SUITE, warmup_path, FIXTURE)
    post = validate(POST_SUITE, post_path, FIXTURE)
    root = warmup["prime-location-1-root"]
    stale = post["beta-header-render-old-location-1"]
    current = post["beta-header-render-current-location-2"]
    assert root["outcome"] == "menu" and root["total"] == 3
    assert item_ids(root) == [9002, 9001, 9003]
    assert current["outcome"] == "menu" and current["total"] == 1
    assert item_ids(current) == [9032]

    assert transition["format"] == 1
    assert transition["mode"] == mode
    first_count = transition["transition_checkpoint_listener_count"]
    ready_count = transition["ready_listener_count"]
    if mode == "toggle":
        assert first_count == 0
    else:
        assert first_count >= 1
    assert ready_count >= 1

    health = validate_health(run_dir, receipt, mode, run)
    behavior = {
        "warmup": warmup,
        "post": post,
        "old_location_state": stale_classification(stale),
        "transition": transition,
        "health_signature": health["health_signature"],
    }
    return {
        "run": run,
        "old_location_state": behavior["old_location_state"],
        "rekordbox_process_id": health["rekordbox_process_id"],
        "listener_counts": health["listener_counts"],
        "behavior_signature": digest(behavior),
        "warmup_sha256": sha256(warmup_path),
        "post_sha256": sha256(post_path),
        "receipt_sha256": sha256(receipt_path),
    }


def main() -> None:
    manifest = load(FIXTURE)
    results = []
    for mode in MODES:
        runs = [validate_run(mode, run, manifest) for run in RUNS]
        assert runs[0]["behavior_signature"] == runs[1]["behavior_signature"]
        results.append(
            {
                "mode": mode,
                "old_location_state": runs[0]["old_location_state"],
                "repeat_verified": True,
                "runs": runs,
            }
        )

    by_mode = {result["mode"]: result for result in results}
    assert by_mode["control"]["old_location_state"] == "persisted"
    assert by_mode["toggle"]["old_location_state"] in {"persisted", "cleared"}

    summary = {
        "format": 1,
        "scope": "real Rekordbox 7.2.19 Hot Cue buffer LINK-toggle lifecycle",
        "fixture_profile": manifest["profile"],
        "fixture_database_sha256": manifest["database_sha256"],
        "fixture_fingerprint": manifest["fixture_fingerprint"],
        "same_process_per_run": True,
        "results": results,
        "sha256": {
            "fixture_manifest": sha256(FIXTURE),
            "identity": sha256(IDENTITY),
            "warmup_suite": sha256(WARMUP_SUITE),
            "post_suite": sha256(POST_SUITE),
            "recorder": sha256(
                CONFORMANCE / "record_hot_cue_bank_buffer_link_toggle.sh"
            ),
        },
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(OUTPUT)


if __name__ == "__main__":
    main()
