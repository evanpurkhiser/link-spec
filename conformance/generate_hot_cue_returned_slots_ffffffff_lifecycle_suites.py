#!/usr/bin/env python3
"""Generate lifecycle declarations for returned-slot count UINT32_MAX."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import generate_hot_cue_extended_setter_parser_suites as parser


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "suites/generated/hot-cue-returned-slots-ffffffff-lifecycle"
MATRIX = ROOT / "data/hot-cue-returned-slots-ffffffff-lifecycle-matrix.json"
REPLICATES = 3


def variant() -> parser.Variant:
    return next(
        item for item in parser.variants() if item.id == "returned-slots-ffffffff"
    )


def observation_suite() -> dict[str, object]:
    document = copy.deepcopy(parser.suite(variant()))
    document["name"] = "hot-cue-returned-slots-ffffffff-lifecycle-observation"
    document["lifecycle_probe"] = {
        "axis": "returned-slots",
        "value": 0xFFFFFFFF,
        "replicates": REPLICATES,
        "process_topology": "setter-and-getter-then-process-restart",
    }
    for case in document["cases"]:
        case["expect"] = {"outcome": "any"}
    return document


def restart_getter_suite() -> dict[str, object]:
    getter = parser.getter_case()
    getter["id"] = "database-read-after-process-restart"
    getter["description"] = (
        "Canonical type-1 getter after restarting Rekordbox against the same database"
    )
    getter["expect"] = {"outcome": "any"}
    return {
        "name": "hot-cue-returned-slots-ffffffff-lifecycle-restart-getter",
        "fixture_profile": "hot-cue-bank-mutation",
        "fixture_version": 1,
        "repeat_strategy": "three-independent-cold-process-observations",
        "lifecycle_probe": {
            "axis": "returned-slots",
            "value": 0xFFFFFFFF,
            "phase": "post-process-restart",
        },
        "defaults": observation_suite()["defaults"],
        "cases": [getter],
    }


def matrix() -> dict[str, object]:
    return {
        "format": 1,
        "experiment": "hot-cue-returned-slots-ffffffff-lifecycle",
        "replicates": REPLICATES,
        "observation_suite": (
            "suites/generated/hot-cue-returned-slots-ffffffff-lifecycle/"
            "hot-cue-returned-slots-ffffffff-lifecycle-observation.json"
        ),
        "restart_getter_suite": (
            "suites/generated/hot-cue-returned-slots-ffffffff-lifecycle/"
            "hot-cue-returned-slots-ffffffff-lifecycle-restart-getter.json"
        ),
    }


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for document in (observation_suite(), restart_getter_suite()):
        (OUTPUT / f"{document['name']}.json").write_text(
            json.dumps(document, indent=2) + "\n"
        )
    MATRIX.write_text(json.dumps(matrix(), indent=2) + "\n")


if __name__ == "__main__":
    main()
