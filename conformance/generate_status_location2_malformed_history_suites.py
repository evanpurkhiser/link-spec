#!/usr/bin/env python3
import copy
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "suites/generated/song-info-sibling-errors.json"
SUITE_ROOT = ROOT / "suites/generated/song-info-location2-malformed-history"
MATRIX = ROOT / "data/song-info-location2-malformed-history-matrix.json"
LOCATION2_CONTEXT = "0x0b020301"
DELIVERY_BLOB_SETTLE_MS = 3000


def number(value: int | str) -> dict:
    return {"number": value}


def precursors() -> list[dict]:
    source = json.loads(SOURCE.read_text())
    return [
        case
        for case in source["cases"]
        if case["id"] != "delivery-alternate-location"
    ]


def sequence_case(source: dict, position: str) -> dict:
    case = copy.deepcopy(source)
    case["id"] = f"{position}--{source['id']}"
    case["description"] = f"{position.title()} malformed precursor: {source['description']}"
    case["render"] = False
    case["fresh_connection"] = True
    case["capture_connection_setup"] = True
    case["drain_before_request_ms"] = 1200
    case["expect"] = {"outcome": "any"}
    if source["id"] == "play-alternate-location":
        case["arguments"][0] = number(LOCATION2_CONTEXT)
    return case


def delivery_probe() -> dict:
    return {
        "id": "delivery-probe",
        "description": "Matched RX3 location-2 Delivery after both malformed precursors",
        "request_kind": "0x2602",
        "arguments": [number(LOCATION2_CONTEXT), number("$fixture.track.first")],
        "render": False,
        "fresh_connection": True,
        "capture_connection_setup": True,
        "drain_before_request_ms": 1200,
        "expect": {"outcome": "any"},
    }


def settle_after_delivery_blob(previous: dict, following: dict) -> dict:
    if previous["id"] != "delivery-blob-content":
        return following

    following["delay_before_connection_ms"] = DELIVERY_BLOB_SETTLE_MS
    return following


def generate() -> tuple[dict, dict[str, dict]]:
    source_cases = precursors()
    suites = {}
    entries = []
    for first in source_cases:
        for second in source_cases:
            pair_id = f"{first['id']}__then__{second['id']}"
            suite_name = f"song-info-location2-malformed-history-lifecycle--{pair_id}"
            first_case = sequence_case(first, "first")
            second_case = settle_after_delivery_blob(
                first,
                sequence_case(second, "second"),
            )
            probe_case = settle_after_delivery_blob(second, delivery_probe())
            suite = {
                "name": suite_name,
                "fixture_profile": "full",
                "fixture_version": 1,
                "repeat_strategy": "fixture-reset-and-cold-process",
                "defaults": {
                    "device": 11,
                    "context": "0x0b010301",
                    "sort": 0,
                    "root_capabilities": "0x05cfffff",
                    "setup": "extended",
                    "page_size": 3,
                    "render_arguments": [0, "$total", 12, 1, 0],
                    "read_timeout_ms": 10_000,
                },
                "cases": [first_case, second_case, probe_case],
            }
            suites[pair_id] = suite
            entries.append(
                {
                    "id": pair_id,
                    "first": first["id"],
                    "second": second["id"],
                    "suite": str((SUITE_ROOT / f"{pair_id}.json").relative_to(ROOT)),
                }
            )

    matrix = {
        "format": 1,
        "experiment": "song-info-location2-malformed-history-lifecycle",
        "status_identity": "authentic XDJ-RX3 player 11",
        "location2_context": LOCATION2_CONTEXT,
        "precursor_count": len(source_cases),
        "ordered_pair_count": len(entries),
        "cases_per_pair": 3,
        "pre_request_drain_ms": 1200,
        "delivery_blob_settle_ms": DELIVERY_BLOB_SETTLE_MS,
        "precursors": [case["id"] for case in source_cases],
        "pairs": entries,
    }
    return matrix, suites


def main() -> None:
    matrix, suites = generate()
    SUITE_ROOT.mkdir(parents=True, exist_ok=True)
    for stale in SUITE_ROOT.glob("*.json"):
        stale.unlink()
    for pair_id, suite in suites.items():
        (SUITE_ROOT / f"{pair_id}.json").write_text(
            json.dumps(suite, indent=2) + "\n"
        )
    MATRIX.write_text(json.dumps(matrix, indent=2) + "\n")
    print(f"wrote {len(suites)} suites and {len(suites) * 3} cases")


if __name__ == "__main__":
    main()
