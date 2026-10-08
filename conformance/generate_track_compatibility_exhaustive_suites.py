#!/usr/bin/env python3
import json
from pathlib import Path

from track_compatibility_matrix import compatibility_exhaustive_cases


ROOT = Path(__file__).resolve().parent
MATRIX = ROOT / "data/track-compatibility-exhaustive-matrix.json"
SUITE_ROOT = ROOT / "suites/generated/track-compatibility-exhaustive"


def matrix() -> dict[str, object]:
    cases = compatibility_exhaustive_cases()
    return {
        "format": 1,
        "fixture_profile": "compatibility-exhaustive",
        "row_count": len(cases),
        "axes": {
            axis: sum(case["axis"] == axis for case in cases)
            for axis in ("file-type-byte", "file-type-wide", "sample-rate", "bit-depth")
        },
        "rows": cases,
        "notes": [
            "FileType is read as a signed byte, so the expected predicate uses its low eight bits.",
            "SampleRate is read as a 32-bit word and matters only for FileType bytes 11 and 12.",
            "BitDepth is not read by DsqlContent_GetNewCDJSupported and is varied to prove invariance.",
        ],
    }


def suite(setup: str) -> dict[str, object]:
    row_count = len(compatibility_exhaustive_cases())
    argument_count = 16 if setup == "extended" else 12
    return {
        "name": f"track-compatibility-exhaustive-{setup}",
        "fixture_profile": "compatibility-exhaustive",
        "fixture_version": 1,
        "defaults": {
            "device": 1,
            "context": "0x01010301",
            "sort": 0,
            "root_capabilities": "0x05cfffff",
            "setup": setup,
            "page_size": 32,
            "render_arguments": [0, "$total", 12, 1, 0],
        },
        "cases": [
            {
                "id": "complete-track-row-matrix",
                "description": (
                    "Complete FileType byte domain, wide narrowing, sample-rate "
                    "boundaries, and BitDepth invariance"
                ),
                "request_kind": "0x1004",
                "arguments": [{"number": "$context"}, {"number": "$sort"}],
                "expect": {
                    "outcome": "menu",
                    "total": row_count,
                    "row_count": row_count,
                    "argument_count": argument_count,
                },
            }
        ],
    }


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n")


def main() -> None:
    write(MATRIX, matrix())
    write(SUITE_ROOT / "track-compatibility-exhaustive-extended.json", suite("extended"))
    write(SUITE_ROOT / "track-compatibility-exhaustive-legacy.json", suite("legacy"))


if __name__ == "__main__":
    main()
