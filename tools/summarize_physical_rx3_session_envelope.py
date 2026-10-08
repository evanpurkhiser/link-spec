#!/usr/bin/env python3
"""Validate the live 7.2.19 replay of the physical RX3 session envelope."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CONFORMANCE = ROOT / "conformance"
sys.path.insert(0, str(ROOT / "tools"))

from rekordbox_health import validate_health_pair
from summarize_search_oracle import validate


PHYSICAL = ROOT / "data/experiments/physical-rx3-session/session-envelope.json"
SUITE = CONFORMANCE / "suites/generated/physical-rx3-session-envelope.json"
FIXTURE = CONFORMANCE / "fixtures/generated/full/manifest.json"
IDENTITY = CONFORMANCE / "runs/xdj-rx3-player-11-status.json"
GOLDEN = (
    CONFORMANCE
    / "goldens/rekordbox-7.2.19/xdj-rx3-status/physical-rx3-session-envelope.json"
)
EVIDENCE = ROOT / "data/experiments/physical-rx3-session-envelope"
RECEIPT = EVIDENCE / "receipt.json"
SUMMARY = EVIDENCE / "summary.json"
MATRIX = EVIDENCE / "matrix.csv"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def values(arguments: list[dict[str, object]]) -> list[object]:
    return [argument.get("value", argument.get("hex")) for argument in arguments]


def row_values(case: dict[str, object]) -> list[list[object]]:
    return [values(row["arguments"]) for row in case.get("rows", [])]


def main() -> None:
    physical = json.loads(PHYSICAL.read_text())
    suite = json.loads(SUITE.read_text())
    receipt = json.loads(RECEIPT.read_text())
    golden = json.loads(GOLDEN.read_text())
    cases = validate(SUITE, GOLDEN, FIXTURE)

    provenance = golden["provenance"]
    if provenance["backend"] != "rekordbox" or provenance["backend_version"] != "7.2.19":
        raise ValueError("golden is not a real Rekordbox 7.2.19 recording")
    identity = provenance["identity"]
    if identity["model"] != "XDJ-RX3" or identity["player"] != 11:
        raise ValueError("golden identity is not the captured RX3/player-11 control")
    if golden["behavior"]["setup"] != "legacy":
        raise ValueError("golden did not use legacy setup")

    for field, expected in (
        ("suite_sha256", sha256(SUITE)),
        ("fixture_manifest_sha256", sha256(FIXTURE)),
        ("identity_sha256", sha256(IDENTITY)),
        ("golden_sha256", sha256(GOLDEN)),
    ):
        if receipt.get(field) != expected:
            raise ValueError(f"capture receipt {field} changed")
    if receipt.get("format") != 1 or receipt.get("exact_repeat") is not True:
        raise ValueError("capture receipt is not an exact repeat")
    if receipt.get("scope") != "real Rekordbox 7.2.19 physical RX3 session envelope":
        raise ValueError("capture receipt scope changed")
    if receipt.get("case_count") != 2 or receipt.get("service_count") != 2:
        raise ValueError("capture receipt counts changed")
    health = validate_health_pair(
        EVIDENCE, receipt, "adjacent-payload-physical-rx3-session-envelope", sha256
    )

    root = cases["physical-root-envelope"]
    track = cases["physical-default-track-render"]
    physical_root = physical["root"]["request"]["arguments"]
    if values(root["request"]["arguments"]) != physical_root:
        raise ValueError("live root request differs from retained physical request")
    if values(track["request"]["arguments"]) != [0x0B010401, 0]:
        raise ValueError("live track request differs from retained physical request")

    physical_renders = [
        pair["render"]["arguments"]
        for pair in physical["default_track_sort_render_pairs"]
    ]
    if {tuple(render) for render in physical_renders} != {
        (0x0B010401, 0, 12, 0, 4342, 12)
    }:
        raise ValueError("retained physical render shape changed")

    page_rows = []
    for case_id, case, final_argument in (
        ("physical-root-envelope", root, 0),
        ("physical-default-track-render", track, 12),
    ):
        for page in case.get("pages", []):
            render = values(page["arguments"])
            if len(render) != 6 or render[0] != 0x0B010401:
                raise ValueError(f"{case_id}: live render is not the physical six-argument shape")
            if render[3] != 0 or render[4] != case["total"] or render[5] != final_argument:
                raise ValueError(f"{case_id}: live render suffix changed")
            page_rows.append(
                {
                    "case": case_id,
                    "offset": page["offset"],
                    "requested": page["requested"],
                    "received": page["received"],
                    "total": case["total"],
                    "render_argument_count": len(render),
                    "render_final_argument": render[5],
                }
            )

    root_rows = row_values(root)
    track_rows = row_values(track)
    summary = {
        "format": 1,
        "scope": "real Rekordbox 7.2.19 replay of the physical RX3 request envelope",
        "authority": {
            "requests": "retained physical XDJ-RX3 packet capture",
            "responses": "fresh and independently repeated Rekordbox 7.2.19 oracle",
            "physical_rekordbox_version": physical["source"]["rekordbox_version"],
        },
        "identity": {"model": "XDJ-RX3", "player": 11, "status_backed": True},
        "setup": {
            "request_arguments": physical["setup"]["request"]["arguments"],
            "physical_response_arguments": physical["setup"]["response"]["arguments"],
            "live_setup_form": golden["behavior"]["setup"],
            "note": "the golden format records setup width, not the live setup reply fields",
        },
        "root": {
            "request_arguments": values(root["request"]["arguments"]),
            "outcome": root["outcome"],
            "total": root.get("total"),
            "row_count": len(root_rows),
            "row_item_types": [row[6] for row in root_rows if len(row) > 6],
            "row_labels": [row[3] for row in root_rows if len(row) > 3],
            "physical_total": physical["root"]["total"],
        },
        "default_track": {
            "request_arguments": values(track["request"]["arguments"]),
            "outcome": track["outcome"],
            "total": track.get("total"),
            "row_count": len(track_rows),
            "render_final_argument": 12,
            "first_row_arguments": track_rows[0] if track_rows else None,
        },
        "post_request_health": health,
        "exact_repeat": True,
        "sha256": {
            "physical_artifact": sha256(PHYSICAL),
            "source_pcap": physical["source"]["sha256"],
            "suite": sha256(SUITE),
            "fixture_manifest": sha256(FIXTURE),
            "identity": sha256(IDENTITY),
            "golden": sha256(GOLDEN),
            "capture_receipt": sha256(RECEIPT),
        },
    }

    candidate = SUMMARY.with_name(f"{SUMMARY.name}.next")
    candidate.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    candidate.replace(SUMMARY)

    candidate = MATRIX.with_name(f"{MATRIX.name}.next")
    with candidate.open("w", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=tuple(page_rows[0]))
        writer.writeheader()
        writer.writerows(page_rows)
    candidate.replace(MATRIX)
    print("validated the physical RX3 envelope against real Rekordbox 7.2.19")


if __name__ == "__main__":
    main()
