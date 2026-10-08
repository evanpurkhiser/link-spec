#!/usr/bin/env python3
"""Generate the health-aware lifecycle declarations for extended setter slot 8."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import generate_hot_cue_extended_setter_parser_suites as parser


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "suites/generated/hot-cue-slot-8-lifecycle"
MATRIX = ROOT / "data/hot-cue-slot-8-lifecycle-matrix.json"
REPLICATES = 3


def slot_variant() -> parser.Variant:
    return next(variant for variant in parser.variants() if variant.id == "slot-00000008")


def observation_suite() -> dict[str, object]:
    document = copy.deepcopy(parser.suite(slot_variant()))
    document["name"] = "hot-cue-slot-8-lifecycle-observation"
    document["lifecycle_probe"] = {
        "axis": "slot",
        "value": 8,
        "replicates": REPLICATES,
        "process_topology": "setter-and-getter-then-process-restart",
    }
    document["cases"][1]["expect"] = {"outcome": "any"}
    return document


def restart_getter_suite() -> dict[str, object]:
    getter = parser.getter_case()
    getter["id"] = "database-read-after-process-restart"
    getter["description"] = (
        "Canonical type-1 getter after restarting Rekordbox against the same database"
    )
    getter["expect"] = {"outcome": "any"}

    return {
        "name": "hot-cue-slot-8-lifecycle-restart-getter",
        "fixture_profile": "hot-cue-bank-mutation",
        "fixture_version": 1,
        "repeat_strategy": "three-independent-cold-process-observations",
        "lifecycle_probe": {
            "axis": "slot",
            "value": 8,
            "phase": "post-process-restart",
        },
        "defaults": observation_suite()["defaults"],
        "cases": [getter],
    }


def matrix() -> dict[str, object]:
    return {
        "format": 1,
        "experiment": "hot-cue-slot-8-lifecycle",
        "replicates": REPLICATES,
        "observation_suite": (
            "suites/generated/hot-cue-slot-8-lifecycle/"
            "hot-cue-slot-8-lifecycle-observation.json"
        ),
        "restart_getter_suite": (
            "suites/generated/hot-cue-slot-8-lifecycle/"
            "hot-cue-slot-8-lifecycle-restart-getter.json"
        ),
    }


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    documents = (observation_suite(), restart_getter_suite())
    for document in documents:
        (OUTPUT / f"{document['name']}.json").write_text(
            json.dumps(document, indent=2) + "\n"
        )
    MATRIX.write_text(json.dumps(matrix(), indent=2) + "\n")


if __name__ == "__main__":
    main()
