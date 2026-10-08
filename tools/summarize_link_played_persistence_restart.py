#!/usr/bin/env python3
"""Validate and summarize played-option persistence across clean restarts."""

from __future__ import annotations

import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CONFORMANCE = ROOT / "conformance"
sys.path.insert(0, str(ROOT / "tools"))

from rekordbox_health import health_signature
from summarize_link_played_state import row_state, scalar


FIXTURE = CONFORMANCE / "fixtures/generated/full/manifest.json"
IDENTITY = CONFORMANCE / "runs/xdj-rx3-player-1.json"
PRIME_SUITE = CONFORMANCE / "suites/link-played-persistence-prime.json"
RESTART_SUITE = CONFORMANCE / "suites/link-played-persistence-restart.json"
GOLDENS = CONFORMANCE / "goldens/rekordbox-7.2.19/xdj-rx3"
SETTINGS = ROOT / "data/experiments/played-track-state/settings/manifest.json"
EVIDENCE = ROOT / "data/experiments/played-track-state/persistence-restart"
CAPTURE_RECEIPT = EVIDENCE / "receipt.json"
OUTPUT = EVIDENCE / "summary.json"
VARIANTS = ("reset", "link-persist", "ordinary-persist", "persist")
RUNS = (1, 2)


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_golden(path: Path, suite_path: Path, manifest: dict) -> dict[str, dict]:
    suite = load(suite_path)
    document = load(path)
    provenance = document["provenance"]
    assert provenance["backend"] == "rekordbox"
    assert provenance["backend_version"] == "7.2.19"
    assert provenance["suite_sha256"] == sha256(suite_path)
    assert provenance["fixture_database_sha256"] == manifest["database_sha256"]
    assert provenance["fixture_fingerprint"] == manifest["fixture_fingerprint"]
    assert provenance["identity"]["model"] == "XDJ-RX3"
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
        scalar_ids = ("first-state-after-restart", "second-state-after-restart")
        row_ids = ("tracks-after-restart",)
    return {
        "scalar_0x3b03": {case_id: scalar(cases[case_id]) for case_id in scalar_ids},
        "row_0x4101_argument_7": {
            case_id: row_state(cases[case_id], track_ids) for case_id in row_ids
        },
    }


def xml_node(element: ET.Element) -> dict:
    return {
        "tag": element.tag,
        "attributes": dict(sorted(element.attrib.items())),
        "text": (element.text or "").strip() or None,
        "children": [xml_node(child) for child in element],
    }


def played_file(run_dir: Path, stage: str, receipt: dict) -> dict:
    prefix = f"{stage}-shutdown-AnotherHistories"
    state_path = run_dir / f"{prefix}.state.json"
    file_path = run_dir / f"{prefix}.xml"
    state = load(state_path)
    assert state["format"] == 1
    assert receipt[f"{stage}_played_state_sha256"] == sha256(state_path)
    if state["exists"]:
        assert state["sha256"] == sha256(file_path)
        assert receipt[f"{stage}_played_sha256"] == sha256(file_path)
        tree = xml_node(ET.parse(file_path).getroot())
    else:
        assert state["sha256"] is None
        assert receipt[f"{stage}_played_sha256"] == "absent"
        assert not file_path.exists()
        tree = None
    return {"exists": state["exists"], "sha256": state["sha256"], "xml": tree}


def validate_health(run_dir: Path, stage: str, receipt: dict) -> dict:
    signatures = {}
    process_ids = set()
    for boundary in ("before", "after"):
        path = run_dir / f"{stage}-health-{boundary}.json"
        assert receipt[f"{stage}_health_{boundary}_sha256"] == sha256(path)
        document = load(path)
        signature = health_signature(document)
        assert signature["process_count"] == 1
        assert signature["responding_count"] == 1
        assert signature["application_events"] == []
        process_ids.add(document["rekordbox_processes"][0]["id"])
        signatures[boundary] = signature
    assert len(process_ids) == 1

    shutdown_path = run_dir / f"{stage}-shutdown.json"
    assert receipt[f"{stage}_shutdown_sha256"] == sha256(shutdown_path)
    shutdown = load(shutdown_path)
    assert shutdown["close_main_window_accepted"] is True
    assert shutdown["forced_rekordbox_termination"] is False
    assert shutdown["process_id"] == next(iter(process_ids))
    return {
        "process_id": shutdown["process_id"],
        "before": signatures["before"],
        "after": signatures["after"],
    }


def validate_options(run_dir: Path, stage: str, expected: dict, receipt: dict) -> None:
    path = run_dir / f"{stage}-options.json"
    assert receipt[f"{stage}_options_sha256"] == sha256(path)
    observed = {item["name"]: item["val"] for item in load(path)}
    assert observed == expected


def main() -> None:
    manifest = load(FIXTURE)
    settings = load(SETTINGS)
    capture = load(CAPTURE_RECEIPT)
    assert capture["format"] == 1
    assert capture["variant_count"] == 4
    assert capture["run_count"] == 8
    assert capture["suite_execution_count"] == 16
    assert capture["clean_shutdown_count"] == 16
    assert capture["exact_repeat"] is True
    assert capture["guest_state_restored"] is True
    assert capture["fixture_manifest_sha256"] == sha256(FIXTURE)
    assert capture["settings_manifest_sha256"] == sha256(SETTINGS)
    assert capture["prime_suite_sha256"] == sha256(PRIME_SUITE)
    assert capture["restart_suite_sha256"] == sha256(RESTART_SUITE)
    assert capture["identity_sha256"] == sha256(IDENTITY)

    settings_by_variant = {
        item["state"]: item["values"] for item in settings["variants"]
    }
    assert tuple(settings_by_variant) == VARIANTS
    results = []
    for variant in VARIANTS:
        prime_path = GOLDENS / f"link-played-persistence-{variant}-prime.json"
        restart_path = GOLDENS / f"link-played-persistence-{variant}-restart.json"
        prime_cases = validate_golden(prime_path, PRIME_SUITE, manifest)
        restart_cases = validate_golden(restart_path, RESTART_SUITE, manifest)
        variant_dir = EVIDENCE / "repeats" / variant
        variant_receipt_path = variant_dir / "receipt.json"
        variant_receipt = load(variant_receipt_path)
        assert capture["variant_receipts"][variant] == sha256(variant_receipt_path)
        assert variant_receipt["variant"] == variant
        assert variant_receipt["prime_golden_sha256"] == sha256(prime_path)
        assert variant_receipt["restart_golden_sha256"] == sha256(restart_path)
        assert variant_receipt["exact_repeat"] is True

        runs = []
        for run in RUNS:
            run_dir = variant_dir / f"run-{run}"
            receipt_path = run_dir / "receipt.json"
            receipt = load(receipt_path)
            assert variant_receipt[f"run_{run}_receipt_sha256"] == sha256(receipt_path)
            assert receipt["variant"] == variant and receipt["run"] == run
            assert receipt["phase"] == ("record" if run == 1 else "repeat")
            assert receipt["prime_sha256"] == sha256(prime_path)
            assert receipt["restart_sha256"] == sha256(restart_path)
            validate_options(run_dir, "prime", settings_by_variant[variant], receipt)
            validate_options(run_dir, "restart", settings_by_variant[variant], receipt)
            prime_health = validate_health(run_dir, "prime", receipt)
            restart_health = validate_health(run_dir, "restart", receipt)
            assert prime_health["process_id"] != restart_health["process_id"]
            runs.append(
                {
                    "run": run,
                    "prime_process_id": prime_health["process_id"],
                    "restart_process_id": restart_health["process_id"],
                    "prime_shutdown_file": played_file(run_dir, "prime", receipt),
                    "restart_shutdown_file": played_file(run_dir, "restart", receipt),
                }
            )

        results.append(
            {
                "variant": variant,
                "settings": settings_by_variant[variant],
                "prime_observations": observations(prime_cases, manifest, True),
                "restart_observations": observations(restart_cases, manifest, False),
                "record_repeat_verified": True,
                "runs": runs,
                "sha256": {
                    "prime_golden": sha256(prime_path),
                    "restart_golden": sha256(restart_path),
                    "variant_receipt": sha256(variant_receipt_path),
                },
            }
        )

    summary = {
        "format": 1,
        "scope": "real Rekordbox 7.2.19 played-option persistence/restart matrix",
        "fixture_profile": manifest["profile"],
        "fixture_database_sha256": manifest["database_sha256"],
        "fixture_fingerprint": manifest["fixture_fingerprint"],
        "variant_count": 4,
        "run_count": 8,
        "suite_execution_count": 16,
        "clean_shutdown_count": 16,
        "results": results,
        "sha256": {
            "fixture_manifest": sha256(FIXTURE),
            "settings_manifest": sha256(SETTINGS),
            "prime_suite": sha256(PRIME_SUITE),
            "restart_suite": sha256(RESTART_SUITE),
            "identity": sha256(IDENTITY),
            "capture_receipt": sha256(CAPTURE_RECEIPT),
        },
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(OUTPUT)


if __name__ == "__main__":
    main()
