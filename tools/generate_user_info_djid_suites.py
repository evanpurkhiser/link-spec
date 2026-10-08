#!/usr/bin/env python3
"""Generate authority-only 0x3006 suites and their execution matrix."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SUITES = ROOT / "conformance/suites/generated"
MATRIX = ROOT / "conformance/data/user-info-djid-matrix.json"


IDENTITIES = (
    {
        "id": "xdj-rx3-player-11",
        "identity": "runs/xdj-rx3-player-11.json",
        "golden_directory": "xdj-rx3",
        "context": "0x0b010301",
    },
    {
        "id": "xdj-rx3-status-player-11",
        "identity": "runs/xdj-rx3-player-11-status.json",
        "golden_directory": "xdj-rx3-status",
        "context": "0x0b010301",
    },
    {
        "id": "cdj-3000-status-player-1",
        "identity": "runs/cdj-3000-player-1-status.json",
        "golden_directory": "cdj-3000-status",
        "context": "0x01010301",
    },
)

PROFILE_IDS = (
    "absent",
    "valid-zero-tail",
    "valid-pattern-tail",
    "checksum-invalid",
    "short-159",
    "long-161",
    "alternate-extension-only",
    "directory-at-target",
)


def argument(number: int | str) -> dict[str, int | str]:
    return {"number": number}


def direct_case(case_id: str, description: str, arguments: list[dict]) -> dict:
    return {
        "id": case_id,
        "description": description,
        "request_kind": "0x3006",
        "arguments": arguments,
        "direct_response": True,
        "render": False,
        "fresh_connection": True,
        "expect": {"outcome": "any"},
    }


def boundary_cases(context: str) -> list[dict]:
    cases = []
    for count in range(33):
        arguments = [] if count == 0 else [argument(context)]
        arguments.extend(argument(0xA5000000 + index) for index in range(1, count))
        cases.append(
            direct_case(
                f"argument-count-{count:02d}",
                f"0x3006 with {count} numeric arguments",
                arguments,
            )
        )

    cases.extend(
        (
            direct_case(
                "context-string",
                "0x3006 with one string argument",
                [{"string": "wrong-type"}],
            ),
            direct_case(
                "context-blob",
                "0x3006 with one blob argument",
                [{"blob_hex": "01020304"}],
            ),
            direct_case(
                "all-string-32",
                "0x3006 with 32 string arguments",
                [{"string": f"arg-{index:02d}"} for index in range(32)],
            ),
            direct_case(
                "all-blob-32",
                "0x3006 with 32 blob arguments",
                [{"blob_hex": f"{index:02x}"} for index in range(32)],
            ),
        )
    )
    for name, value in (
        ("zero", 0),
        ("uint32-max", "0xffffffff"),
        ("location-1", context),
        ("location-2", hex((int(context, 0) & 0xFF00FFFF) | 0x00020000)),
        ("track-type-0", hex(int(context, 0) & 0xFFFFFF00)),
        ("track-type-4", hex((int(context, 0) & 0xFFFFFF00) | 4)),
        ("other-player-1", hex((int(context, 0) & 0x00FFFFFF) | 0x01000000)),
        ("other-player-11", hex((int(context, 0) & 0x00FFFFFF) | 0x0B000000)),
    ):
        cases.append(
            direct_case(
                f"context-{name}",
                f"0x3006 with packed-context boundary {name}",
                [argument(value)],
            )
        )

    return cases


def suite(name: str, context: str, cases: list[dict]) -> dict:
    return {
        "name": name,
        "fixture_profile": "full",
        "fixture_version": 1,
        "repeat_strategy": "fixture-reset-and-cold-process",
        "defaults": {
            "device": int(context, 0) >> 24,
            "context": context,
            "sort": 0,
            "root_capabilities": "0x05cfffff",
            "setup": "extended",
            "page_size": 32,
            "read_timeout_ms": 5000,
            "render_arguments": [],
        },
        "cases": cases,
    }


def generate(suites: Path, matrix_path: Path) -> None:
    suites.mkdir(parents=True, exist_ok=True)
    matrix_path.parent.mkdir(parents=True, exist_ok=True)
    executions = []

    for identity in IDENTITIES:
        suite_id = f"user-info-djid-absent-{identity['id']}"
        suite_path = suites / f"{suite_id}.json"
        suite_path.write_text(
            json.dumps(
                suite(suite_id, identity["context"], boundary_cases(identity["context"])),
                indent=2,
            )
            + "\n"
        )
        executions.append(
            {
                "id": suite_id,
                "profile": "absent",
                "identity": identity["identity"],
                "suite": f"suites/generated/{suite_path.name}",
                "golden": (
                    "goldens/rekordbox-7.2.19/"
                    f"{identity['golden_directory']}/{suite_path.name}"
                ),
                "case_count": len(boundary_cases(identity["context"])),
            }
        )

    profile_context = IDENTITIES[0]["context"]
    for profile in PROFILE_IDS[1:]:
        suite_id = f"user-info-djid-profile-{profile}"
        suite_path = suites / f"{suite_id}.json"
        suite_path.write_text(
            json.dumps(
                suite(
                    suite_id,
                    profile_context,
                    [
                        direct_case(
                            "canonical-context",
                            f"0x3006 canonical request under {profile} profile state",
                            [argument(profile_context)],
                        )
                    ],
                ),
                indent=2,
            )
            + "\n"
        )
        executions.append(
            {
                "id": suite_id,
                "profile": profile,
                "identity": IDENTITIES[0]["identity"],
                "suite": f"suites/generated/{suite_path.name}",
                "golden": f"goldens/rekordbox-7.2.19/xdj-rx3/{suite_path.name}",
                "case_count": 1,
            }
        )

    matrix = {
        "format": 1,
        "scope": "real Rekordbox 7.2.19 0x3006/0x4d02 user-info authority matrix",
        "fixture_profile": "full",
        "profiles": list(PROFILE_IDS),
        "executions": executions,
        "execution_count": len(executions),
        "case_count": sum(execution["case_count"] for execution in executions),
        "record_repeat_execution_count": 2
        * sum(execution["case_count"] for execution in executions),
    }
    matrix_path.write_text(json.dumps(matrix, indent=2) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite-dir", type=Path, default=SUITES)
    parser.add_argument("--matrix", type=Path, default=MATRIX)
    args = parser.parse_args()
    generate(args.suite_dir, args.matrix)


if __name__ == "__main__":
    main()
