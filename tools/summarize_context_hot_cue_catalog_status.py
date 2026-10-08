#!/usr/bin/env python3
"""Validate Hot Cue catalog packed-context behavior for genuine status identities."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

from summarize_search_oracle import load, sha256, validate


ROOT = Path(__file__).resolve().parent.parent
CONFORMANCE = ROOT / "conformance"
MANIFEST = CONFORMANCE / "fixtures/generated/hot-cue-banks/manifest.json"
GENERATOR = CONFORMANCE / "generate_context_hot_cue_catalog_status_suites.py"
RECORDER = CONFORMANCE / "record_context_hot_cue_catalog_status_matrix.sh"
OUTPUT = (
    ROOT
    / "data/experiments/packed-context/hot-cue-catalog-status-cross/summary.json"
)
CONFIGURATIONS = (
    ("xdj-rx3-status", 11, "extended"),
    ("xdj-rx3-status", 11, "legacy"),
    ("cdj-3000-status", 1, "extended"),
    ("cdj-3000-status", 1, "legacy"),
)
SETUP_WIDTHS = {"extended": 16, "legacy": 12}
REQUEST_TOTALS = {"tree-root": 3, "alpha-tracks": 8, "empty-tracks": 0}


def values(row: dict[str, object]) -> list[object]:
    return [argument.get("value", argument.get("hex")) for argument in row["arguments"]]


def normalize_contexts(value: object) -> object:
    if isinstance(value, dict):
        normalized = {
            key: normalize_contexts(item)
            for key, item in value.items()
            if key != "description"
        }
        if normalized.get("type") == "number":
            number = normalized.get("value")
            if isinstance(number, int) and number & 0x00FFFF00 == 0x00010300:
                normalized["value"] = 0x01000000 | (number & 0x00FFFFFF)
        return normalized
    if isinstance(value, list):
        return [normalize_contexts(item) for item in value]
    return value


def normalized_hash(cases: dict[str, dict[str, object]]) -> str:
    canonical = normalize_contexts(
        [{"id": case_id, **copy.deepcopy(cases[case_id])} for case_id in sorted(cases)]
    )
    encoded = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def main() -> None:
    cases_by_model_setup = {}
    hashes_by_setup: dict[str, set[str]] = {setup: set() for setup in SETUP_WIDTHS}
    artifacts = {}

    for model, player, setup in CONFIGURATIONS:
        suite = (
            CONFORMANCE
            / f"suites/context-hot-cue-catalog-status-player-{player}-{setup}.json"
        )
        golden = (
            CONFORMANCE
            / f"goldens/rekordbox-7.2.19/{model}/context-hot-cue-catalog-status-{setup}.json"
        )
        cases = validate(suite, golden, MANIFEST)
        assert len(cases) == 21
        cases_by_model_setup[(model, setup)] = cases

        for track_type in range(0x07):
            for label, supported_total in REQUEST_TOTALS.items():
                case = cases[f"type-{track_type:02x}--{label}"]
                assert case["request"]["kind"] == 0x2001
                expected_context = player << 24 | 0x00010300 | track_type
                assert case["request"]["arguments"][0]["value"] == expected_context
                assert case["header"][0]["kind"] == 0x4000

                if track_type == 0x01:
                    assert case["outcome"] == "menu"
                    assert case["total"] == supported_total
                    assert len(case["rows"]) == supported_total
                    assert {len(row["arguments"]) for row in case["rows"]} in (
                        set(),
                        {SETUP_WIDTHS[setup]},
                    )
                    continue

                assert case["outcome"] == "render_timeout"
                assert case["total"] == 50
                assert case["rows"] == []
                assert len(case["pages"]) == 1
                page = case["pages"][0]
                assert page["outcome"] == "timeout"
                assert page["transport_error_kind"] == "WouldBlock"
                assert page["requested"] == 32
                assert page["received"] == 0
                assert page["messages"] == []

        behavior = normalized_hash(cases)
        hashes_by_setup[setup].add(behavior)
        artifacts[f"{model}/{setup}"] = {
            "suite_sha256": sha256(suite),
            "golden_sha256": sha256(golden),
            "normalized_behavior_sha256": behavior,
            "case_count": len(cases),
        }

    assert all(len(hashes) == 1 for hashes in hashes_by_setup.values())

    for model in ("xdj-rx3-status", "cdj-3000-status"):
        extended = cases_by_model_setup[(model, "extended")]
        legacy = cases_by_model_setup[(model, "legacy")]
        for case_id in extended:
            extended_case = extended[case_id]
            legacy_case = legacy[case_id]
            assert legacy_case["outcome"] == extended_case["outcome"]
            assert legacy_case["total"] == extended_case["total"]
            assert len(legacy_case["rows"]) == len(extended_case["rows"])
            for legacy_row, extended_row in zip(
                legacy_case["rows"], extended_case["rows"], strict=True
            ):
                assert values(legacy_row) == values(extended_row)[:12]

    manifest = load(MANIFEST)
    summary = {
        "scope": "real Rekordbox 7.2.19 only; backend comparison is deferred",
        "fixture": {
            "profile": "hot-cue-banks",
            "database_sha256": manifest["database_sha256"],
            "fixture_fingerprint": manifest["fixture_fingerprint"],
        },
        "matrix": {
            "models": ["XDJ-RX3", "CDJ-3000"],
            "players": [11, 1],
            "setups": list(SETUP_WIDTHS),
            "packed_types": list(range(0x07)),
            "queries_per_type": list(REQUEST_TOTALS),
            "goldens": 4,
            "cases": 84,
            "independent_fixture_reset_repeats": 4,
        },
        "observations": {
            "accepted_type": 1,
            "accepted_totals": REQUEST_TOTALS,
            "rejected_types": [0, 2, 3, 4, 5, 6],
            "rejected_header_total": 50,
            "rejected_render": "32 requested, zero received, WouldBlock",
            "identity_effect": "none after requester-context normalization",
            "setup_effect": "legacy rows are exact 12-field prefixes of extended rows",
            "normalized_behavior_sha256": {
                setup: next(iter(hashes)) for setup, hashes in hashes_by_setup.items()
            },
        },
        "artifacts": artifacts,
        "sha256": {
            "generator": sha256(GENERATOR),
            "recorder": sha256(RECORDER),
            "fixture_manifest": sha256(MANIFEST),
        },
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(f"validated 4 goldens / 84 cases; wrote {OUTPUT}")


if __name__ == "__main__":
    main()
