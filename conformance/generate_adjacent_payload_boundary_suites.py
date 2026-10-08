#!/usr/bin/env python3
"""Generate focused suites for every deterministic payload boundary profile."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from generate_adjacent_payload_suite import arguments, case, number
from generate_payload_boundary_assets import OUTPUT as ASSETS, VARIANTS


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "suites/generated/adjacent-payload-boundaries"
INDEX = ROOT / "data/adjacent-payload-boundary-matrix.json"
CANONICAL_ASSETS = ROOT / "payload-assets/boundaries"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def packed_context(location: int) -> int:
    return (1 << 24) | (location << 16) | (3 << 8) | 1


def request(kind: str, *, fixed_tag_slots: int | None = None) -> dict:
    location = 8 if kind in {"2003", "2103", "2004", "2204", "2504", "2804"} else 1
    return case(
        f"kind-{kind}",
        f"0x{kind} observes the selected payload boundary profile",
        kind,
        arguments(kind, location, 1, "$fixture.track.first"),
        fixed_tag_slots=fixed_tag_slots,
    )


def artwork_cases() -> list[dict]:
    content = request("2003")
    content["id"] = "kind-2003--content-artwork"
    playlist = request("2003")
    playlist["id"] = "kind-2003--playlist-artwork"
    playlist["arguments"][1] = number("$fixture.playlist.primary")
    return [content, playlist, request("2103")]


def atom_request(kind: str, tag: str, extension: str) -> dict:
    return case(
        f"kind-{kind}--specified-atom",
        f"0x{kind} observes repeated or aligned specified atoms",
        kind,
        [
            number(packed_context(1)),
            number("$fixture.track.first"),
            number(tag),
            number(extension),
        ],
    )


def cases_for(family: str) -> list[dict]:
    if family == "artwork":
        return artwork_cases()
    if family == "pqtz":
        return [request("2204"), request("2804")]
    if family == "preview":
        return [request("2004", fixed_tag_slots=5)]
    if family == "pvbr":
        return [request("2504")]
    if family == "pwv3":
        return [request("2904"), atom_request("2c04", "0x33565750", "0x00545845")]
    if family == "pkey":
        return [request("2a04"), atom_request("2c04", "0x59454b50", "0x00545845")]
    if family == "atom":
        return [
            atom_request("2c04", "0x37565750", "0x00584532"),
            atom_request("2d04", "0x37565750", "0x00584532"),
        ]
    raise ValueError(f"unhandled payload boundary family: {family}")


def generate(output: Path, index_path: Path) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    expected_names = {f"{specification['name']}.json" for specification in VARIANTS}
    for stale in output.glob("*.json"):
        if stale.name not in expected_names:
            stale.unlink()

    entries = []
    for specification in VARIANTS:
        cases = cases_for(specification["family"])
        suite = {
            "name": f"Rekordbox adjacent payload boundary: {specification['name']}",
            "fixture_profile": "payload-valid",
            "fixture_version": 1,
            "defaults": {
                "device": 1,
                "context": "0x01010301",
                "sort": 0,
                "root_capabilities": "0x05cfffff",
                "setup": "extended",
                "page_size": 32,
                "read_timeout_ms": 5000,
                "render_arguments": [],
            },
            "cases": cases,
        }
        path = output / f"{specification['name']}.json"
        path.write_text(json.dumps(suite, indent=2) + "\n")
        manifest = ASSETS / specification["name"] / "manifest.json"
        entries.append(
            {
                **specification,
                "suite": (OUTPUT / path.name).relative_to(ROOT).as_posix(),
                "suite_sha256": sha256(path),
                "asset_manifest": (CANONICAL_ASSETS / specification["name"] / "manifest.json").relative_to(ROOT).as_posix(),
                "asset_manifest_sha256": sha256(manifest),
                "case_count": len(cases),
                "service_count": len({item["request_kind"] for item in cases}),
            }
        )

    index = {
        "format": 1,
        "scope": "Rekordbox 7.2.19 adjacent payload parser boundary declarations",
        "asset_index_sha256": sha256(ASSETS / "manifest.json"),
        "variant_count": len(entries),
        "case_count": sum(entry["case_count"] for entry in entries),
        "variants": entries,
    }
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps(index, indent=2) + "\n")
    return index


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT)
    parser.add_argument("--index", type=Path, default=INDEX)
    args = parser.parse_args()
    index = generate(args.output_dir, args.index)
    print(
        f"wrote {index['variant_count']} suites and {index['case_count']} cases "
        f"beneath {args.output_dir}"
    )


if __name__ == "__main__":
    main()
