#!/usr/bin/env python3
"""Consolidate canonical Link Export device/model behavior evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
GOLDENS = ROOT / "conformance/goldens/rekordbox-7.2.19"
OUTPUT = ROOT / "data/device-behavior-matrix.json"

ORDINARY_IDENTITIES = (
    "cdj-3000", "cdj-2000nxs2", "xdj-xz", "xdj-az", "xdj-1000mk2",
    "unknown-mixer", "unknown-djm", "xdj-rx3",
)
ORDINARY_SUITES = ("full", "legacy", "device-capabilities", "compatibility")

STATUS_SURFACES = {
    "display-song-info": (
        "data/experiments/packed-context/display-status-cross/summary.json",
        "different",
        "Matched RX3 uses XDJ-prefix AIO order; matched CDJ uses ordinary order. Classification is keyed by the requester player.",
    ),
    "play-song-info": (
        "data/experiments/packed-context/play-status-cross/summary.json",
        "equal-after-context-normalization",
        "RX3 and CDJ rows are identical within each setup after requester normalization.",
    ),
    "delivery-and-no-builder": (
        "data/experiments/packed-context/class2-status-cross/summary.json",
        "equal-after-context-normalization",
        "Delivery and recognized no-builder outcomes are identical within each setup.",
    ),
    "hot-cue-bank-catalog": (
        "data/experiments/packed-context/hot-cue-catalog-status-cross/summary.json",
        "equal-after-context-normalization",
        "Catalog and track membership behavior is identity-invariant; only type 1 is admitted.",
    ),
    "hot-cue-bank-getters": (
        "data/experiments/packed-context/hot-cue-getter-status-cross/summary.json",
        "equal-after-context-normalization",
        "Legacy and extended direct getters are identity-invariant; rejected types return status 50.",
    ),
    "hot-cue-bank-extended-setter": (
        "data/experiments/packed-context/hot-cue-setter-status-cross/summary.json",
        "equal-after-context-normalization",
        "Extended setter replies, accepted mutation, and rejected no-op database state are identity- and setup-invariant.",
    ),
    "hot-cue-bank-legacy-setter": (
        "data/experiments/packed-context/hot-cue-legacy-setter-status-cross/summary.json",
        "equal-after-context-normalization",
        "Legacy setter replies, accepted slot-4 mutation, and rejected pristine state are identity- and setup-invariant.",
    ),
}

SERVING_DIMENSIONS = (
    {
        "id": "keepalive-identity",
        "input": "Discovery model text, device class, generation, presence, model code, and player number.",
        "effect": "No field difference across the fixed ordinary menu, capability, compatibility, and setup envelopes.",
        "boundary": "Keepalive text alone does not populate the status-backed AIO map.",
        "source": None,
    },
    {
        "id": "setup-width",
        "input": "Client-selected legacy or extended setup handshake.",
        "effect": "Track and metadata rows contain 12 or 16 arguments; legacy rows are exact prefixes of extended rows.",
        "boundary": "Model identity does not force setup width, and direct blob replies do not acquire row suffixes.",
        "source": "data/experiments/packed-context/device-setup-cross/summary.json",
    },
    {
        "id": "requester-player",
        "input": "Player byte in the packed request context.",
        "effect": "Selects requester-keyed list-buffer state and the status-backed Display Song Info AIO classification.",
        "boundary": "RX3 status for player 11 yields AIO Display order only for requester 11; requester 1 remains ordinary.",
        "source": "data/experiments/packed-context/display-status-cross/summary.json",
    },
    {
        "id": "menu-location",
        "input": "Location byte in the packed request context.",
        "effect": "Participates in list-buffer identity and routes location-sensitive service state.",
        "boundary": "Generic locations 1 through 8 are exhausted; the XDJ-RR source-defined Delivery location 9 matrix remains queued.",
        "source": "data/static-analysis/list-buffer-location.disasm.txt",
    },
    {
        "id": "packed-track-type",
        "input": "Final byte in the packed request context.",
        "effect": "Types 3 and 4 time out before ordinary 1xxx dispatch; type 1 populates Root/Search, enables HotCueAutoLoad bit 0x100, and is the admitted local-library type for Song Info and Hot Cue Bank. Hierarchy leaves can copy the type into row argument 7 high byte.",
        "boundary": "This byte is independent of advertised model and per-track compatibility.",
        "source": "data/experiments/packed-context/family-cross/summary.json",
    },
    {
        "id": "status-model-classification",
        "input": "Requester-keyed model state learned from player status packets.",
        "effect": "The recovered isAIO branch changes Display Song Info property order for XDJ-prefix models.",
        "boundary": "Play, Delivery/no-builder, Hot Cue catalog/getters/setters, root, sort, pagination, and ordinary row serialization show no matched RX3/CDJ difference in completed crosses.",
        "source": "data/experiments/packed-context/display-status-cross/summary.json",
    },
    {
        "id": "root-capability-mask",
        "input": "Mask supplied as the final Root request argument.",
        "effect": "Controls configured root-category admission, including Date Added remapping and the exact legacy Hot Cue synthesis branch.",
        "boundary": "The mask is a request field, not a value inferred from model identity by the server.",
        "source": "data/configuration-behavior-map.json",
    },
    {
        "id": "content-compatibility",
        "input": "Per-track FileType low byte and, for types 11/12, SampleRate.",
        "effect": "Sets row argument 10 compatibility-failure bit 0; BitDepth is unread on recovered paths.",
        "boundary": "All 382 tracks remain in Track and File Name menus; this is presentation metadata, not peer-model classification or membership filtering.",
        "source": "data/experiments/track-compatibility-exhaustive/summary.json",
    },
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def behavior_sha256(document: dict[str, object]) -> str:
    payload = json.dumps(
        document["behavior"], sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ) + "\n"
    return hashlib.sha256(payload.encode()).hexdigest()


def ordinary_matrix() -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    identities = []
    suite_hashes: dict[str, list[str]] = {suite: [] for suite in ORDINARY_SUITES}
    for identity in ORDINARY_IDENTITIES:
        suites = {}
        identity_fields = None
        for suite in ORDINARY_SUITES:
            path = GOLDENS / identity / f"{suite}.json"
            document = json.loads(path.read_text())
            current_identity = document["provenance"]["identity"]
            if identity_fields is None:
                identity_fields = current_identity
            elif current_identity != identity_fields:
                raise ValueError(f"identity drift within {identity}")
            behavior_hash = behavior_sha256(document)
            suite_hashes[suite].append(behavior_hash)
            suites[suite] = {
                "golden": path.relative_to(ROOT).as_posix(),
                "golden_sha256": sha256(path),
                "behavior_sha256": behavior_hash,
                "case_count": len(document["behavior"]["cases"]),
            }
        identities.append(
            {
                "id": identity,
                "provenance_tier": "synthetic-keepalive-identity",
                "identity": identity_fields,
                "suites": suites,
            }
        )

    equivalence = []
    for suite, hashes in suite_hashes.items():
        unique = sorted(set(hashes))
        if len(unique) != 1:
            raise ValueError(f"ordinary identity behavior differs for {suite}: {unique}")
        equivalence.append(
            {
                "suite": suite,
                "identity_count": len(hashes),
                "behavior_equal": True,
                "behavior_sha256": unique[0],
            }
        )
    return identities, equivalence


def status_surfaces() -> list[dict[str, object]]:
    result = []
    for surface, (relative, classification, conclusion) in STATUS_SURFACES.items():
        path = ROOT / relative
        document = json.loads(path.read_text())
        result.append(
            {
                "surface": surface,
                "comparison": "captured RX3 status versus RX3-template-derived CDJ-3000 status",
                "provenance_tiers": ["captured-verbatim", "template-derived-control"],
                "classification": classification,
                "conclusion": conclusion,
                "source": relative,
                "source_sha256": sha256(path),
                "observed": document.get("observed", document.get("observations")),
            }
        )
    return result


def serving_dimensions() -> list[dict[str, object]]:
    result = []
    for dimension in SERVING_DIMENSIONS:
        item = dict(dimension)
        source = item.get("source")
        if source:
            item["source_sha256"] = sha256(ROOT / source)
        result.append(item)
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    identities, equivalence = ordinary_matrix()
    cdj2000_path = ROOT / "data/experiments/device-status/cdj-2000nexus/summary.json"
    cdj2000 = json.loads(cdj2000_path.read_text())
    x86_path = ROOT / "data/static-analysis/device-predicate-audit.json"
    arm_path = ROOT / "data/static-analysis/device-predicate-audit-arm64.json"
    windows_path = ROOT / "data/static-analysis/windows/device-semantic-audit.json"

    document = {
        "format": 1,
        "product": "rekordbox 7.2.19",
        "scope": "Device, model, status, setup, and requester dimensions that can alter Link Export serving.",
        "ordinary_identity_matrix": {
            "identities": identities,
            "suite_equivalence": equivalence,
            "conclusion": "For the fixed request envelopes, all eight keepalive identities are byte-identical within each suite.",
        },
        "status_backed_surfaces": status_surfaces(),
        "serving_dimensions": serving_dimensions(),
        "genuine_cdj_2000nexus": {
            "provenance_tier": "captured-verbatim-external",
            "source": cdj2000_path.relative_to(ROOT).as_posix(),
            "source_sha256": sha256(cdj2000_path),
            "identity": cdj2000["identity"],
            "matrix": cdj2000["matrix"],
            "conclusion": "All 13 semantic envelopes match the derived CDJ-3000 controls; 12 raw envelopes match exactly.",
        },
        "static_predicate_boundary": {
            "decisions": [
                {"predicate": "PSvDBMain::isAIO(player)", "serving_effect": "Display Song Info property order"},
                {"predicate": "PSvDBMain::clearAIOMap(player)", "serving_effect": "Invalidate requester-keyed Display classification on disconnect"},
                {"predicate": "DsqlContent_GetNewCDJSupported(content_id)", "serving_effect": "Content FileType/SampleRate compatibility bit; not a peer-model predicate"},
            ],
            "x86_64": {"source": x86_path.relative_to(ROOT).as_posix(), "source_sha256": sha256(x86_path), "summary": json.loads(x86_path.read_text())["summary"]},
            "arm64": {"source": arm_path.relative_to(ROOT).as_posix(), "source_sha256": sha256(arm_path), "summary": json.loads(arm_path.read_text())["summary"]},
            "windows": {"source": windows_path.relative_to(ROOT).as_posix(), "source_sha256": sha256(windows_path)},
            "negative_result": "No audited peer-model predicate reaches root, sort, ordinary list insertion, pagination, or ordinary row serialization.",
        },
        "provenance_boundary": {
            "captured_verbatim": ["XDJ-RX3", "CDJ-2000nexus"],
            "template_derived_control": ["CDJ-3000"],
            "corroborating_incomplete_parent_capture": ["XDJ-XZ"],
            "pending_native_status": ["XDJ-AZ", "XDJ-1000MK2", "XDJ-RR", "XDJ-RX2", "OPUS-QUAD", "CDJ-3000"],
            "rule": "Keepalive model text alone cannot establish status-backed AIO behavior or native packet provenance.",
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(document, indent=2) + "\n")
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
