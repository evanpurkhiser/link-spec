#!/usr/bin/env python3
"""Validate and summarize the real-Rekordbox Link-played transition oracle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CONFORMANCE = ROOT / "conformance"
SUITE = CONFORMANCE / "suites/link-played-state.json"
MANIFEST = CONFORMANCE / "fixtures/generated/full/manifest.json"
IDENTITY = CONFORMANCE / "runs/xdj-rx3-player-1.json"
GOLDEN = CONFORMANCE / "goldens/rekordbox-7.2.19/xdj-rx3/link-played-state.json"
EVIDENCE = ROOT / "data/experiments/played-track-state/transition-reset"
RECEIPT = EVIDENCE / "receipt.json"
OUTPUT = EVIDENCE / "summary.json"

SCALAR_CASES = (
    "baseline-first-state",
    "baseline-second-state",
    "first-state-after-insert",
    "first-state-after-second-insert",
    "second-state-after-insert",
    "first-state-after-remove",
    "second-state-after-first-remove",
    "second-state-after-history-delete",
)
ROW_CASES = (
    "baseline-tracks",
    "tracks-after-first",
    "tracks-after-second",
    "tracks-after-first-remove",
    "tracks-after-history-delete",
)


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def scalar(case: dict) -> int:
    assert case["outcome"] == "raw_reply"
    messages = case["raw_response"]["messages"]
    assert len(messages) == 1
    message = messages[0]
    assert message["kind"] == 0x4000
    assert len(message["arguments"]) == 2
    assert all(argument["type"] == "number" for argument in message["arguments"])
    return message["arguments"][1]["value"]


def row_state(case: dict, track_ids: tuple[int, int]) -> dict[str, object]:
    assert case["outcome"] == "menu"
    assert case["total"] == 8
    assert len(case["rows"]) == 8
    rows = {}
    for row in case["rows"]:
        assert row["kind"] == 0x4101
        assert len(row["arguments"]) == 16
        track_id = row["arguments"][1]["value"]
        if track_id in track_ids:
            flags = row["arguments"][7]["value"]
            rows[str(track_id)] = {
                "flags": flags,
                "link_played_bit": bool(flags & 0x100),
            }
    assert set(rows) == {str(track_id) for track_id in track_ids}
    return rows


def main() -> None:
    suite = load(SUITE)
    manifest = load(MANIFEST)
    identity = load(IDENTITY)
    golden = load(GOLDEN)
    receipt = load(RECEIPT)

    assert suite["name"] == "link-played-state"
    assert receipt["format"] == 1
    assert receipt["case_count"] == 19
    assert receipt["process_count"] == 2
    assert receipt["exact_repeat"] is True
    assert receipt["guest_state_restored"] is True
    assert receipt["suite_sha256"] == sha256(SUITE)
    assert receipt["fixture_manifest_sha256"] == sha256(MANIFEST)
    assert receipt["identity_sha256"] == sha256(IDENTITY)
    assert receipt["golden_sha256"] == sha256(GOLDEN)

    provenance = golden["provenance"]
    assert provenance["backend"] == "rekordbox"
    assert provenance["backend_version"] == "7.2.19"
    assert provenance["suite_sha256"] == sha256(SUITE)
    assert provenance["fixture_database_sha256"] == manifest["database_sha256"]
    assert provenance["fixture_fingerprint"] == manifest["fixture_fingerprint"]
    assert provenance["identity"]["model"] == "XDJ-RX3"
    assert provenance["identity"]["player"] == identity["player"]

    declarations = {case["id"]: case for case in suite["cases"]}
    cases = {case["id"]: case for case in golden["behavior"]["cases"]}
    assert declarations.keys() == cases.keys()
    assert set(SCALAR_CASES) == {
        case_id
        for case_id, declaration in declarations.items()
        if declaration["request_kind"] == "0x3b03"
    }
    assert set(ROW_CASES) == {
        case_id
        for case_id, declaration in declarations.items()
        if declaration["request_kind"] == "0x1004"
    }

    track_ids = (manifest["ids"]["track.first"], manifest["ids"]["track.second"])
    observations = {
        "scalar_0x3b03": {
            case_id: scalar(cases[case_id]) for case_id in SCALAR_CASES
        },
        "row_0x4101_argument_7": {
            case_id: row_state(cases[case_id], track_ids) for case_id in ROW_CASES
        },
        "history_root_totals": {
            case_id: cases[case_id]["total"]
            for case_id in ("root-after-first", "final-root")
        },
    }

    summary = {
        "format": 1,
        "scope": "real Rekordbox 7.2.19 Link-played transition under reset options",
        "fixture_profile": manifest["profile"],
        "fixture_database_sha256": manifest["database_sha256"],
        "fixture_fingerprint": manifest["fixture_fingerprint"],
        "identity": {"model": identity["model"], "player": identity["player"]},
        "record_repeat_verified": True,
        "guest_state_restored": True,
        "observations": observations,
        "sha256": {
            "suite": sha256(SUITE),
            "fixture_manifest": sha256(MANIFEST),
            "identity": sha256(IDENTITY),
            "golden": sha256(GOLDEN),
            "capture_receipt": sha256(RECEIPT),
        },
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(OUTPUT)


if __name__ == "__main__":
    main()
