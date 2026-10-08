#!/usr/bin/env python3
"""Validate and summarize the health-aware 0x2401 seek-descriptor matrix."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CONFORMANCE = ROOT / "conformance"
MATRIX = CONFORMANCE / "data/hot-cue-setter-seek-matrix.json"
EVIDENCE = ROOT / "data/experiments/hot-cue-bank/extended-setter-seek"
OUTPUT = EVIDENCE / "summary.json"
UNINITIALIZED_DESCRIPTOR_VARIANT = "actual-length-00000052"
CRASH_VARIANTS = {
    UNINITIALIZED_DESCRIPTOR_VARIANT,
    "inbound-validity-00000001",
    "inbound-validity-ffffffff",
}
EXPECTED_SEEK_VALUES = {
    "inbound-validity-00000001": ("1,3,1", "2,4,0"),
    "inbound-validity-ffffffff": ("1,3,4294967295", "2,4,0"),
}
SEMANTIC_FIELDS = (
    "ID", "HotCueBanklistID", "ContentID", "TrackNo", "CueID",
    "InMsec", "InFrame", "InMpegFrame", "InMpegAbs",
    "OutMsec", "OutFrame", "OutMpegFrame", "OutMpegAbs",
    "Color", "ColorTableIndex", "ActiveLoop", "Comment",
    "BeatLoopSize", "CueMicrosec", "InPointSeekInfo", "OutPointSeekInfo",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def semantic_snapshot(document: dict[str, object]) -> list[dict[str, object]]:
    return [
        {field: row[field] for field in SEMANTIC_FIELDS}
        for row in document["memberships"]
    ]


def seek_string_signature(value: str) -> dict[str, object]:
    if value == "":
        return {"shape": "empty"}

    components = value.split(",")
    assert len(components) == 3
    assert all(component.isascii() and component.isdecimal() for component in components)
    assert all(0 <= int(component) <= 0xFFFFFFFFFFFFFFFF for component in components[:2])
    assert 0 <= int(components[2]) <= 0xFFFFFFFF
    return {
        "shape": "unsigned-decimal-triplet",
        "component_count": len(components),
    }


def database_signature(
    variant_id: str,
    memberships: list[dict[str, object]],
) -> list[dict[str, object]]:
    if variant_id != UNINITIALIZED_DESCRIPTOR_VARIANT:
        return memberships

    return [
        {
            **row,
            "InPointSeekInfo": seek_string_signature(row["InPointSeekInfo"]),
            "OutPointSeekInfo": seek_string_signature(row["OutPointSeekInfo"]),
        }
        for row in memberships
    ]


def setter_signature(document: dict[str, object]) -> dict[str, object]:
    case = document["behavior"]["cases"][0]
    return {
        "outcome": case["outcome"],
        "error_kind": case.get("raw_response", {}).get("error_kind"),
        "messages": case.get("raw_response", {}).get("messages", []),
    }


def process_state(process_count: int) -> str:
    states = {
        0: "exited",
        1: "alive",
        2: "replacement-overlap",
    }
    assert process_count in states
    return states[process_count]


def assert_expected_result(
    variant_id: str,
    setter: dict[str, object],
    state: str,
    memberships: list[dict[str, object]],
) -> None:
    primary = memberships[0]
    secondary = memberships[1]
    assert secondary["InPointSeekInfo"] == ""
    assert secondary["OutPointSeekInfo"] == ""

    if variant_id in CRASH_VARIANTS:
        assert setter == {
            "outcome": "timeout",
            "error_kind": "WouldBlock",
            "messages": [],
        }
        assert state == "replacement-overlap"
    else:
        assert setter["outcome"] == "raw_reply"
        assert setter["error_kind"] is None
        assert state == "alive"
        assert len(setter["messages"]) == 1
        message = setter["messages"][0]
        assert message["kind"] == 0x4E02
        assert message["arguments"][0] == {"type": "number", "value": 0x2401}
        assert message["arguments"][1] == {"type": "number", "value": 0}
        assert message["arguments"][2] == {"type": "number", "value": 124}
        assert message["arguments"][4] == {"type": "number", "value": 1}
        assert len(bytes.fromhex(message["arguments"][3]["hex"])) == 124

    if variant_id == UNINITIALIZED_DESCRIPTOR_VARIANT:
        assert seek_string_signature(primary["InPointSeekInfo"])["shape"] == "unsigned-decimal-triplet"
        assert seek_string_signature(primary["OutPointSeekInfo"])["shape"] == "unsigned-decimal-triplet"
        return

    expected = EXPECTED_SEEK_VALUES.get(variant_id, ("", ""))
    assert (primary["InPointSeekInfo"], primary["OutPointSeekInfo"]) == expected


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-partial", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    matrix = json.loads(MATRIX.read_text())
    results = []
    axis_counts: dict[str, Counter[str]] = defaultdict(Counter)

    for variant in matrix["variants"]:
        runs = []
        complete = True
        for run in (1, 2):
            directory = EVIDENCE / variant["id"] / f"run-{run}"
            paths = {
                "setter": directory / "setter.json",
                "health": directory / "health.json",
                "snapshot": directory / "database-snapshot.json",
                "complete": directory / "complete.json",
            }
            if not all(path.is_file() for path in paths.values()):
                complete = False
                break

            receipt = json.loads(paths["complete"].read_text())
            suite = CONFORMANCE / variant["suite"]
            assert receipt["variant"] == variant["id"] and receipt["run"] == run
            assert receipt["suite_sha256"] == sha256(suite)
            assert receipt["setter_sha256"] == sha256(paths["setter"])
            assert receipt["health_sha256"] == sha256(paths["health"])
            assert receipt["database_snapshot_sha256"] == sha256(paths["snapshot"])

            setter = json.loads(paths["setter"].read_text())
            health = json.loads(paths["health"].read_text())
            snapshot = json.loads(paths["snapshot"].read_text())
            assert snapshot["integrity"] == "ok"
            memberships = semantic_snapshot(snapshot)
            runs.append({
                "setter_signature": setter_signature(setter),
                "process_count": health["rekordbox_process_count"],
                "application_events": health["application_events"],
                "database_memberships": memberships,
                "database_signature": database_signature(variant["id"], memberships),
                "setter_sha256": sha256(paths["setter"]),
                "health_sha256": sha256(paths["health"]),
                "database_snapshot_sha256": sha256(paths["snapshot"]),
                "complete_sha256": sha256(paths["complete"]),
            })

        if not complete:
            if args.allow_partial:
                continue
            raise FileNotFoundError(f"incomplete evidence for {variant['id']}")

        assert runs[0]["setter_signature"] == runs[1]["setter_signature"]
        assert runs[0]["process_count"] == runs[1]["process_count"]
        assert runs[0]["database_signature"] == runs[1]["database_signature"]
        state = process_state(runs[0]["process_count"])
        for run in runs:
            assert_expected_result(
                variant["id"],
                run["setter_signature"],
                state,
                run["database_memberships"],
            )
        axis_counts[variant["axis"]][state] += 1
        results.append({**variant, "process_state": state, "runs": runs})

    complete = len(results) == len(matrix["variants"])
    if not args.allow_partial:
        assert complete

    document = {
        "format": 1,
        "experiment": "hot-cue-extended-setter-seek",
        "complete": complete,
        "declared_variants": len(matrix["variants"]),
        "completed_variants": len(results),
        "run_count": len(results) * 2,
        "matrix_sha256": sha256(MATRIX),
        "axis_counts": {axis: dict(sorted(counts.items())) for axis, counts in sorted(axis_counts.items())},
        "results": results,
    }
    output = OUTPUT if complete else OUTPUT.with_name("summary.partial.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n")
    print(f"validated {len(results)}/{len(matrix['variants'])} seek variants")


if __name__ == "__main__":
    main()
