#!/usr/bin/env python3
"""Validate and summarize status-backed Song Info oracle evidence."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
GOLDENS = ROOT / "conformance/goldens/rekordbox-7.2.19"
EXPERIMENTS = ROOT / "data/experiments/song-info-sibling-errors"
SUITES = (
    "song-info-siblings",
    "song-info-sibling-render",
    "song-info-sibling-pagination",
    "song-info-sibling-errors",
    "song-info-sibling-legacy",
)
CONTEXT_MAP = {
    0x0B010301: 0x01010301,
    0x0B020301: 0x01020301,
}


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def cases(path: Path) -> list[dict]:
    return load(path)["behavior"]["cases"]


def normalize(value: object) -> object:
    if isinstance(value, dict):
        return {key: normalize(item) for key, item in value.items()}
    if isinstance(value, list):
        return [normalize(item) for item in value]
    if isinstance(value, int):
        return CONTEXT_MAP.get(value, value)

    return value


def digest(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def by_id(items: list[dict]) -> dict[str, dict]:
    return {item["id"]: item for item in items}


def total(items: list[dict], case_id: str) -> int | None:
    return by_id(items)[case_id]["total"]


def main() -> None:
    print("Stable status-backed suites:")
    print("| Suite | Cases | Normalized SHA-256 | Ordinary | RX3/CDJ |")
    print("| --- | ---: | --- | --- | --- |")
    for suite in SUITES:
        ordinary = cases(GOLDENS / "xdj-rx3" / f"{suite}.json")
        rx3 = cases(GOLDENS / "xdj-rx3-status" / f"{suite}.json")
        cdj = cases(GOLDENS / "cdj-3000-status" / f"{suite}.json")
        ids = {item["id"] for item in rx3}
        ordinary_subset = [item for item in ordinary if item["id"] in ids]
        normalized_rx3 = normalize(rx3)
        ordinary_differences = [
            status_case["id"]
            for status_case, ordinary_case in zip(
                normalized_rx3, ordinary_subset, strict=True
            )
            if status_case != ordinary_case
        ]

        assert normalized_rx3 == cdj
        if suite == "song-info-sibling-errors":
            assert ordinary_differences == ["delivery-no-arguments"]
            ordinary_result = "diff: `delivery-no-arguments`"
        else:
            assert not ordinary_differences
            ordinary_result = "exact"
        print(
            f"| `{suite}` | {len(rx3)} | `{digest(normalized_rx3)}` | "
            f"{ordinary_result} | exact |"
        )

    rx3_runs = [
        cases(EXPERIMENTS / f"status-rx3-matched-run-{run}.json")
        for run in (1, 2)
    ]
    cdj_runs = [
        cases(EXPERIMENTS / f"status-cdj-3000-run-{run}.json")
        for run in (1, 2)
    ]
    unstable_ids = {"play-zero-context", "delivery-alternate-location"}
    without_unstable = lambda items: [
        item for item in items if item["id"] not in unstable_ids
    ]
    normalized_rx3_runs = [normalize(without_unstable(items)) for items in rx3_runs]
    normalized_cdj_runs = [normalize(without_unstable(items)) for items in cdj_runs]

    assert normalized_rx3_runs[0] == normalized_rx3_runs[1]
    assert normalized_cdj_runs[0] == normalized_cdj_runs[1]
    assert normalized_rx3_runs[0] == normalized_cdj_runs[0]
    assert [total(items, "play-alternate-location") for items in rx3_runs] == [7, 7]
    assert [total(items, "delivery-alternate-location") for items in rx3_runs] == [13, 0]
    assert [total(items, "delivery-alternate-location") for items in cdj_runs] == [13, 13]

    zero_outcomes = [by_id(items)["play-zero-context"]["outcome"] for items in rx3_runs]
    assert zero_outcomes == ["timeout", "menu"]
    assert [total(items, "play-zero-context") for items in rx3_runs] == [None, 0]

    print("\nOrdered malformed experiments:")
    print("| Matrix | Repeat | Play zero context | Play location 2 | Delivery location 2 |")
    print("| --- | --- | --- | ---: | ---: |")
    print("| RX3 player 11, matched context | variable | timeout / empty menu | 7 / 7 | 13 / 0 |")
    print("| CDJ-3000 player 1 | exact | empty menu / empty menu | 7 | 13 |")


if __name__ == "__main__":
    main()
