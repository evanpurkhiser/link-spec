#!/usr/bin/env python3
"""Generate timing/topology probes for the 0x2401 UINT32_MAX length edge."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "tools"))

from build_hot_cue_mutation_record import build_record


@dataclass(frozen=True)
class Variant:
    id: str
    topology: str
    delay_ms: int


DELAYS = (50, 100, 250, 500, 1000, 3000)


def variants() -> tuple[Variant, ...]:
    return (
        Variant("fresh-immediate", "after-reconnect", 0),
        *(Variant(f"same-connection-{delay:04d}ms", "same-connection", delay) for delay in (0, *DELAYS)),
        *(Variant(f"before-reconnect-{delay:04d}ms", "before-reconnect", delay) for delay in DELAYS),
        *(Variant(f"after-reconnect-{delay:04d}ms", "after-reconnect", delay) for delay in DELAYS),
    )


def setter_case() -> dict[str, object]:
    record = build_record()
    return {
        "id": "setter",
        "description": "Extended setter with declared length UINT32_MAX",
        "request_kind": "0x2401",
        "arguments": [
            {"number": "0x0b010301"},
            {"number": "$fixture.hotcue.bank.mutation"},
            {"number": 1},
            {"number": 0xFFFFFFFF},
            {"blob_hex": record.hex()},
            {"number": 1},
        ],
        "direct_response": True,
        "render": False,
        "fresh_connection": True,
        "expect": {"outcome": "any"},
    }


def observation_case(variant: Variant) -> dict[str, object]:
    case: dict[str, object] = {
        "id": "late-response-observation",
        "description": (
            "Read without sending after the UINT32_MAX setter using "
            f"{variant.topology} at {variant.delay_ms} ms"
        ),
        "request_kind": 0,
        "arguments": [],
        "raw_hex": "",
        "raw_read_ms": 1200,
        "render": False,
        "fresh_connection": variant.topology != "same-connection",
        "expect": {"outcome": "any"},
    }
    if variant.topology == "before-reconnect":
        case["delay_before_connection_ms"] = variant.delay_ms
    else:
        case["delay_before_request_ms"] = variant.delay_ms
    return case


def getter_case(case_id: str, description: str, *, final: bool) -> dict[str, object]:
    case: dict[str, object] = {
        "id": case_id,
        "description": description,
        "request_kind": "0x2301",
        "arguments": [
            {"number": "0x0b010301"},
            {"number": "$fixture.hotcue.bank.mutation"},
            {"number": 1},
        ],
        "direct_response": True,
        "render": False,
        "fresh_connection": final,
        "delay_before_request_ms": 50,
        "expect": {"outcome": "any"},
    }
    if final:
        case["delay_before_connection_ms"] = 1000
    return case


def suite(variant: Variant) -> dict[str, object]:
    name = f"hot-cue-declared-length-ffffffff-lifecycle-{variant.id}"
    return {
        "name": name,
        "fixture_profile": "hot-cue-bank-mutation",
        "fixture_version": 1,
        "repeat_strategy": "independent-observations",
        "lifecycle_probe": {
            "declared_length": 0xFFFFFFFF,
            "fixture_variant": "duplicate-slot",
            "topology": variant.topology,
            "delay_ms": variant.delay_ms,
            "observation_read_ms": 1200,
            "replicates": 3,
        },
        "defaults": {
            "device": 11,
            "context": "0x0b010301",
            "sort": 0,
            "root_capabilities": "0x05cfffff",
            "setup": "extended",
            "page_size": 32,
            "read_timeout_ms": 5000,
            "render_arguments": [0, "$total", 12, 1, 0],
        },
        "cases": [
            setter_case(),
            observation_case(variant),
            getter_case(
                "database-read-after-observation",
                "Type-1 getter on the observation connection",
                final=False,
            ),
            getter_case(
                "database-read-final",
                "Type-1 getter after a one-second wait and fresh connection",
                final=True,
            ),
        ],
    }


def main() -> None:
    output_dir = ROOT / "suites/generated/hot-cue-declared-length-ffffffff-lifecycle"
    output_dir.mkdir(parents=True, exist_ok=True)
    matrix = []
    for variant in variants():
        document = suite(variant)
        output = output_dir / f"{document['name']}.json"
        output.write_text(json.dumps(document, indent=2) + "\n")
        matrix.append(
            {
                "id": variant.id,
                "topology": variant.topology,
                "delay_ms": variant.delay_ms,
                "suite": str(output.relative_to(ROOT)),
            }
        )
    (ROOT / "data/hot-cue-declared-length-ffffffff-lifecycle-matrix.json").write_text(
        json.dumps({"format": 1, "replicates": 3, "variants": matrix}, indent=2)
        + "\n"
    )


if __name__ == "__main__":
    main()
