#!/usr/bin/env python3
"""Validate and summarize correctly framed track renders with 0-2 arguments."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CONFORMANCE = ROOT / "conformance"
sys.path.insert(0, str(ROOT / "tools"))

from rekordbox_health import validate_health_pair
from summarize_search_oracle import validate


SUITE = CONFORMANCE / "suites/generated/render-arity-underflow.json"
FIXTURE = CONFORMANCE / "fixtures/generated/full/manifest.json"
IDENTITY = CONFORMANCE / "runs/xdj-rx3-player-11.json"
GOLDEN = CONFORMANCE / "goldens/rekordbox-7.2.19/xdj-rx3/render-arity-underflow.json"
EVIDENCE = ROOT / "data/experiments/render-arity-underflow"
RECEIPT = EVIDENCE / "receipt.json"
SUMMARY = EVIDENCE / "summary.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    suite = json.loads(SUITE.read_text())
    receipt = json.loads(RECEIPT.read_text())
    cases = validate(SUITE, GOLDEN, FIXTURE)

    assert receipt["format"] == 1
    assert receipt["scope"] == "real Rekordbox 7.2.19 track render arity underflow"
    assert receipt["variant"] == "render-arity-underflow"
    assert receipt["case_count"] == len(suite["cases"]) == 9
    assert receipt["service_count"] == 1
    assert receipt["exact_repeat"] is True
    assert receipt["suite_sha256"] == sha256(SUITE)
    assert receipt["fixture_manifest_sha256"] == sha256(FIXTURE)
    assert receipt["identity_sha256"] == sha256(IDENTITY)
    assert receipt["golden_sha256"] == sha256(GOLDEN)
    health = validate_health_pair(
        EVIDENCE, receipt, "adjacent-payload-render-arity-underflow", sha256
    )

    probes = []
    for arity in range(3):
        warm = cases[f"warm-list-arity-{arity}"]
        probe = cases[f"render-arity-{arity}"]
        post = cases[f"health-after-arity-{arity}"]

        assert warm["outcome"] == post["outcome"] == "menu"
        assert warm["total"] == post["total"] == 8
        assert len(probe["request"]["arguments"]) == arity
        assert probe["request"]["kind"] == 0x3000
        raw = probe["raw_response"]
        probes.append(
            {
                "render_argument_count": arity,
                "outcome": probe["outcome"],
                "raw_hex": raw.get("raw_hex", ""),
                "decoded_bytes": raw.get("decoded_bytes"),
                "messages": raw.get("messages", []),
                "error_kind": raw.get("error_kind"),
                "warm_total": warm["total"],
                "fresh_connection_health_total": post["total"],
            }
        )

    summary = {
        "scope": "real Rekordbox 7.2.19 only; backend comparison is deferred",
        "model": "XDJ-RX3",
        "player": 11,
        "fixture_profile": "full",
        "case_count": len(cases),
        "probe_count": len(probes),
        "exact_repeat": True,
        "post_request_health": health,
        "probes": probes,
        "sha256": {
            "suite": sha256(SUITE),
            "fixture_manifest": sha256(FIXTURE),
            "identity": sha256(IDENTITY),
            "golden": sha256(GOLDEN),
            "receipt": sha256(RECEIPT),
        },
    }
    SUMMARY.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print("validated three underlength render probes with fresh health checks")


if __name__ == "__main__":
    main()
