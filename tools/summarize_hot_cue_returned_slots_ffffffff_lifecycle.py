#!/usr/bin/env python3
"""Validate the returned-slot UINT32_MAX setter lifecycle experiment."""

from pathlib import Path

import summarize_hot_cue_slot_8_lifecycle as lifecycle


ROOT = Path(__file__).resolve().parent.parent
lifecycle.MATRIX = (
    ROOT / "conformance/data/hot-cue-returned-slots-ffffffff-lifecycle-matrix.json"
)
lifecycle.EVIDENCE = (
    ROOT
    / "data/experiments/hot-cue-bank/extended-setter-parser/"
    "returned-slots-ffffffff-lifecycle"
)
lifecycle.OBSERVATIONS = lifecycle.EVIDENCE / "observations"
lifecycle.BASELINE_SNAPSHOT = lifecycle.EVIDENCE / "baseline-snapshot.json"
lifecycle.OUTPUT = lifecycle.EVIDENCE / "summary.json"
lifecycle.PARTIAL_OUTPUT = lifecycle.EVIDENCE / "summary.partial.json"


if __name__ == "__main__":
    lifecycle.main()
