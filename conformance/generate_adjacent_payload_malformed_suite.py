#!/usr/bin/env python3
"""Generate malformed arity and type probes for adjacent payload services."""

from __future__ import annotations

import json
import argparse
from pathlib import Path

from generate_adjacent_payload_suite import KINDS, LOG_ONLY_KINDS, arguments, number


ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "suites/generated/adjacent-payload-malformed"
MATRIX_OUTPUT = ROOT / "data/adjacent-payload-malformed-matrix.json"


def malformed_case(
    kind: str,
    label: str,
    description: str,
    args: list[dict],
    *,
    fixed_tag_slots: int | None = None,
) -> dict:
    result = {
        "id": f"kind-{kind}--{label}",
        "description": f"0x{kind} {description}",
        "request_kind": f"0x{kind}",
        "arguments": args,
        "direct_response": True,
        "render": False,
        "fresh_connection": True,
        "expect": {"outcome": "any"},
    }
    if fixed_tag_slots is not None:
        result["fixed_tag_slots"] = fixed_tag_slots
    return result


def build_cases() -> list[dict]:
    cases = []
    for kind in KINDS:
        valid = arguments(kind, 8, 1, "$fixture.track.first")
        if kind in LOG_ONLY_KINDS:
            variants = (
                ("no-arguments", "with every argument omitted", [], None),
                ("string-context", "with a string context", [{"string": "wrong-type"}], None),
                ("blob-context", "with a blob context", [{"blob_hex": "01020304"}], None),
                ("extra-number", "with an extra numeric argument", [*valid, number(0xDEADBEEF)], None),
                ("extra-string", "with an extra string argument", [*valid, {"string": "extra"}], None),
                ("thirty-two-tag-slots", "with one value but 32 declared tag slots", valid, 32),
            )
        else:
            identifier_index = 2 if kind == "2004" else 1
            string_context = [{"string": "wrong-type"}, *valid[1:]]
            blob_context = [{"blob_hex": "01020304"}, *valid[1:]]
            string_identifier = [*valid]
            string_identifier[identifier_index] = {"string": "wrong-type"}
            fixed_slots = 5 if kind == "2004" else None
            variants = (
                ("no-arguments", "with every argument omitted", [], None),
                ("context-only", "with only the packed context", valid[:1], fixed_slots),
                ("string-context", "with a string context", string_context, fixed_slots),
                ("blob-context", "with a blob context", blob_context, fixed_slots),
                ("string-identifier", "with a string content/image identifier", string_identifier, fixed_slots),
                ("extra-number", "with an extra numeric argument", [*valid, number(0xDEADBEEF)], 5 if kind == "2004" else None),
            )

        for label, description, args, fixed_tag_slots in variants:
            cases.append(
                malformed_case(
                    kind,
                    label,
                    description,
                    args,
                    fixed_tag_slots=fixed_tag_slots,
                )
            )

    return cases


def suite_for(case: dict) -> dict:
    return {
        "name": f"Rekordbox adjacent payload malformed {case['id']}",
        "fixture_profile": "full",
        "fixture_version": 1,
        "defaults": {
            "device": 1,
            "context": "0x01010301",
            "sort": 0,
            "root_capabilities": "0x05cfffff",
            "setup": "extended",
            "page_size": 32,
            "read_timeout_ms": 1500,
            "render_arguments": [],
        },
        "cases": [case],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--matrix", type=Path, default=MATRIX_OUTPUT)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    cases = build_cases()
    entries = []
    for case in cases:
        output = args.output_dir / f"{case['id']}.json"
        output.write_text(json.dumps(suite_for(case), indent=2) + "\n")
        entries.append(
            {
                "id": case["id"],
                "kind": case["request_kind"],
                "suite": f"suites/generated/adjacent-payload-malformed/{case['id']}.json",
                "golden": (
                    "goldens/rekordbox-7.2.19/xdj-rx3/"
                    f"adjacent-payload-malformed/{case['id']}.json"
                ),
            }
        )

    matrix = {
        "format": 1,
        "scope": "Rekordbox adjacent payload malformed arity and type matrix",
        "case_count": len(entries),
        "services": sorted({entry["kind"] for entry in entries}),
        "cases": entries,
    }
    args.matrix.parent.mkdir(parents=True, exist_ok=True)
    args.matrix.write_text(json.dumps(matrix, indent=2) + "\n")


if __name__ == "__main__":
    main()
