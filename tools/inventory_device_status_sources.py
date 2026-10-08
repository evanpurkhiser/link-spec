#!/usr/bin/env python3
"""Inventory captured device models and lab player-status provenance."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
WORKSPACE = ROOT.parent
DYSENTERY_ASSETS = WORKSPACE / "dysentery/doc/assets"
RUNS = ROOT / "conformance/runs"
OUTPUT = ROOT / "data/static-analysis/device-status-source-inventory.json"
RX3_CAPTURE = WORKSPACE / "captures/rx3-rekordbox-working-ap-20260927.pcap"
CORROBORATING_STATUS_FIXTURES = (
    {
        "path": (
            ROOT
            / "conformance/status-packets/"
            "cdj-2000nexus-player-3-firmware-1.43.hex"
        ),
        "model": "CDJ-2000nexus",
        "firmware": "1.43",
        "player": 3,
        "source_repository": "https://github.com/chrisle/alphatheta-connect",
        "source_commit": "ec8b012642bf366f495e0cdd498dc5084057af85",
        "missing_provenance": [
            "parent capture",
            "packet timestamp",
            "source and destination addresses and ports",
            "paired keepalive",
        ],
    },
    {
        "path": (
            ROOT
            / "conformance/status-packets/"
            "xdj-xz-player-1-analyzed-status-20260422.hex"
        ),
        "model": "XDJ-XZ",
        "firmware": None,
        "player": 1,
        "capture_date": "2026-04-22",
        "track_state": "analyzed rekordbox track; master",
        "source_repository": "https://github.com/cinderblock/netBeat",
        "source_commit": "399583fff849bddd8c8abd744d1d25e1656ba009",
        "missing_provenance": [
            "parent capture",
            "packet timestamp",
            "source and destination addresses and ports",
            "paired keepalive",
            "firmware version",
        ],
    },
    {
        "path": (
            ROOT
            / "conformance/status-packets/"
            "xdj-xz-player-1-unanalyzed-status-20260422.hex"
        ),
        "model": "XDJ-XZ",
        "firmware": None,
        "player": 1,
        "capture_date": "2026-04-22",
        "track_state": "unanalyzed track; non-master",
        "source_repository": "https://github.com/cinderblock/netBeat",
        "source_commit": "399583fff849bddd8c8abd744d1d25e1656ba009",
        "missing_provenance": [
            "parent capture",
            "packet timestamp",
            "source and destination addresses and ports",
            "paired keepalive",
            "firmware version",
        ],
    },
)
MODEL = re.compile(rb"(?:CDJ|XDJ|DJM|OPUS|OMNIS)[A-Za-z0-9 -]{0,19}\x00")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path: Path) -> str:
    return str(path.relative_to(WORKSPACE))


def captured_models(path: Path) -> list[str]:
    matches = {
        match.group(0)[:-1].rstrip(b" ").decode("ascii")
        for match in MODEL.finditer(path.read_bytes())
    }
    return sorted(matches)


def hex_packet(path: Path) -> bytes:
    return bytes.fromhex(path.read_text())


def corroborating_fixture_entry(fixture: dict[str, object]) -> dict[str, object]:
    packet = hex_packet(fixture["path"])

    result = {
        "path": relative(fixture["path"]),
        "bytes": len(packet),
        "sha256": hashlib.sha256(packet).hexdigest(),
        "model": fixture["model"],
        "firmware": fixture["firmware"],
        "player": fixture["player"],
        "provenance_tier": "corroborating-fixture",
        "source_repository": fixture["source_repository"],
        "source_commit": fixture["source_commit"],
        "missing_provenance": fixture["missing_provenance"],
    }
    for key in ("capture_date", "track_state"):
        if key in fixture:
            result[key] = fixture[key]
    return result


def corroborating_fixture_inventory() -> list[dict[str, object]]:
    return [
        corroborating_fixture_entry(fixture)
        for fixture in CORROBORATING_STATUS_FIXTURES
    ]


def capture_inventory() -> list[dict[str, object]]:
    paths = sorted(
        path
        for path in DYSENTERY_ASSETS.rglob("*")
        if path.is_file() and path.suffix in {".pcap", ".pcapng"}
    )
    return [
        {
            "path": relative(path),
            "sha256": sha256(path),
            "bytes": path.stat().st_size,
            "fixed_width_device_models": captured_models(path),
        }
        for path in paths
    ]


def identity_tier(identity: dict[str, object]) -> str:
    if identity.get("status_provenance"):
        return str(identity["status_provenance"])
    if identity.get("status_packet_hex_path"):
        return "captured-verbatim"
    if identity["model"] == "XDJ-RX3" and identity["player"] == 11:
        return "captured-verbatim"
    return "rx3-template-derived"


def identity_inventory() -> list[dict[str, object]]:
    results = []
    for path in sorted(RUNS.glob("*-status.json")):
        identity = json.loads(path.read_text())
        status_packet_bytes = identity.get("status_packet_bytes")
        if status_packet_bytes is None and identity.get("status_template") == "rx3-captured":
            status_packet_bytes = 0x124
        results.append(
            {
                "path": relative(path),
                "model": identity["model"],
                "player": identity["player"],
                "device_type": identity["device_type"],
                "generation": identity["generation"],
                "status_packet_bytes": status_packet_bytes,
                "status_packet_sha256": identity["status_packet_sha256"],
                "status_source": identity_tier(identity),
                "status_template": identity.get("status_template"),
                "status_packet_hex_path": identity.get("status_packet_hex_path"),
            }
        )
    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    captures = capture_inventory()
    identities = identity_inventory()
    corroborating_fixtures = corroborating_fixture_inventory()
    dysentery_models = sorted(
        {
            model
            for capture in captures
            for model in capture["fixed_width_device_models"]
        }
    )
    captured_identities = [
        item for item in identities if item["status_source"] == "captured-verbatim"
    ]
    corroborating_identities = [
        item
        for item in identities
        if item["status_source"] == "corroborating-fixture"
    ]
    derived_identities = [
        item for item in identities if item["status_source"] == "rx3-template-derived"
    ]
    document = {
        "format": 1,
        "scope": "device-status source provenance; no backend execution",
        "dysentery": {
            "asset_root": relative(DYSENTERY_ASSETS),
            "capture_count": len(captures),
            "fixed_width_device_models": dysentery_models,
            "captures": captures,
        },
        "physical_rx3_capture": {
            "path": relative(RX3_CAPTURE),
            "sha256": sha256(RX3_CAPTURE),
            "status_payload_sha256": (
                "49d262852bc10cbed30f9cd1f40283047b2423d4865ec5d1b240ae5fe6e20987"
            ),
        },
        "corroborating_status_fixtures": corroborating_fixtures,
        "lab_status_identities": identities,
        "counts": {
            "captured_verbatim": len(captured_identities),
            "corroborating_fixture": len(corroborating_fixtures),
            "corroborating_identity": len(corroborating_identities),
            "rx3_template_derived": len(derived_identities),
        },
        "boundary": (
            "A derived identity tests Rekordbox model/player parsing against the "
            "captured RX3 packet shape; it is not evidence of that model's native "
            "status layout. A corroborating fixture preserves hardware bytes but "
            "is not replay-ready captured-verbatim evidence without its missing "
            "capture context."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n")
    print(
        f"wrote {args.output}: {len(captures)} captures, "
        f"{len(captured_identities)} captured identities, "
        f"{len(corroborating_fixtures)} corroborating fixtures, "
        f"{len(corroborating_identities)} corroborating identities, "
        f"{len(derived_identities)} derived identities"
    )


if __name__ == "__main__":
    main()
