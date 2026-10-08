#!/usr/bin/env python3
"""Summarize retained Delivery row-order experiments."""

from __future__ import annotations

import hashlib
import json
import string
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
EXPERIMENTS = ROOT / "data/experiments/song-info-delivery-order"
MENU_ITEM = 0x4101


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def behavior_bytes(document: dict) -> bytes:
    canonical = json.dumps(
        document["behavior"], sort_keys=True, separators=(",", ":")
    )
    return f"{canonical}\n".encode()


def behavior_digest(document: dict) -> str:
    return hashlib.sha256(behavior_bytes(document)).hexdigest()


def item_types(case: dict) -> tuple[int, ...]:
    values = (
        int(message["arguments"][6]["value"])
        for page in case.get("pages", [])
        for message in page.get("messages", [])
        if message.get("kind") == MENU_ITEM
    )
    return tuple(0x0F04 if value & 0xFF == 0x04 else value for value in values)


def header_total(case: dict) -> int | None:
    for message in case.get("header", []):
        arguments = message.get("arguments", [])
        if len(arguments) > 1:
            return int(arguments[1]["value"])

    return None


def register_patterns(
    cases: list[dict], patterns: dict[tuple[int, ...], str]
) -> None:
    for case in cases:
        order = item_types(case)
        if order and order not in patterns:
            patterns[order] = string.ascii_uppercase[len(patterns)]


def paired_runs(stem: str) -> tuple[dict, dict]:
    return (
        load(EXPERIMENTS / f"{stem}-run-1.json"),
        load(EXPERIMENTS / f"{stem}-run-2.json"),
    )


def main() -> None:
    patterns: dict[tuple[int, ...], str] = {}
    repeated, repeated_copy = paired_runs("repeated-identical")
    register_patterns(repeated["behavior"]["cases"], patterns)

    assert behavior_bytes(repeated) == behavior_bytes(repeated_copy)

    print(
        "| Precursor | Connection | Probe pattern | Precursor result | "
        "Cases vs reconnect | Behavior SHA-256 |"
    )
    print("| --- | --- | --- | --- | --- | --- |")

    for first_path in sorted(EXPERIMENTS.glob("family-*-run-1.json")):
        stem = first_path.name.removesuffix("-run-1.json")
        first, second = paired_runs(stem)
        assert behavior_bytes(first) == behavior_bytes(second)

        cases = first["behavior"]["cases"]
        probes = [case for case in cases if case["id"].endswith("delivery-probe")]
        precursors = [case for case in cases if case not in probes]
        register_patterns(probes, patterns)

        probe_sequence = "".join(patterns[item_types(case)] for case in probes)
        outcomes = {
            (case["outcome"], header_total(case), len(item_types(case)))
            for case in precursors
        }
        assert len(outcomes) == 1
        outcome, total, rows = outcomes.pop()
        total_text = "-" if total is None else str(total)
        precursor = stem.removeprefix("family-")
        connection = "same socket" if precursor.endswith("-same-connection") else "reconnect"
        precursor = precursor.removesuffix("-same-connection")
        comparison = "baseline"
        if connection == "same socket":
            reconnect = load(
                EXPERIMENTS / f"family-{precursor}-run-1.json"
            )["behavior"]["cases"]
            assert cases == reconnect
            comparison = "exact"
        result = f"{outcome}; total {total_text}; {rows} rows"
        print(
            f"| `{precursor}` | {connection} | `{probe_sequence}` | {result} | "
            f"{comparison} | `{behavior_digest(first)}` |"
        )

    print("\nIdentity lifecycle:")
    print(
        "| Lifecycle | Warm-up | Post-rejoin | Recorded gap | "
        "Repeat | Warm-up SHA-256 | Post SHA-256 |"
    )
    print("| --- | --- | --- | ---: | --- | --- | --- |")
    lifecycle_cases: dict[tuple[str, str], list[dict]] = {}
    for mode in ("same-rejoin", "cdj-replacement"):
        documents = {
            (run, phase): load(
                EXPERIMENTS / f"identity-{mode}-run-{run}-{phase}.json"
            )
            for run in (1, 2)
            for phase in ("warmup", "post")
        }
        for phase in ("warmup", "post"):
            assert behavior_bytes(documents[(1, phase)]) == behavior_bytes(
                documents[(2, phase)]
            )

        sequences = {}
        for phase in ("warmup", "post"):
            cases = documents[(1, phase)]["behavior"]["cases"]
            lifecycle_cases[(mode, phase)] = cases
            sequences[phase] = "".join(patterns[item_types(case)] for case in cases)

        gap = (
            documents[(1, "post")]["provenance"]["recorded_unix_seconds"]
            - documents[(1, "warmup")]["provenance"]["recorded_unix_seconds"]
        )
        print(
            f"| `{mode}` | `{sequences['warmup']}` | `{sequences['post']}` | "
            f"{gap} s | exact | `{behavior_digest(documents[(1, 'warmup')])}` | "
            f"`{behavior_digest(documents[(1, 'post')])}` |"
        )

    for phase in ("warmup", "post"):
        assert lifecycle_cases[("same-rejoin", phase)] == lifecycle_cases[
            ("cdj-replacement", phase)
        ]

    print("\nPatterns (selector-specific composite types normalized to `0x0f04`):")
    for order, name in patterns.items():
        print(f"{name} " + " ".join(f"{value:04x}" for value in order))


if __name__ == "__main__":
    main()
