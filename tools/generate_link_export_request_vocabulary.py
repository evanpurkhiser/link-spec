#!/usr/bin/env python3
"""Generate the complete known Link Export command vocabulary and coverage ledger."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
ALPHA_SOURCE = (
    ROOT.parent
    / "alphatheta-docs/devices/cdj-3000/application/remote-database-client.md"
)
QUERY_MAP = ROOT / "data/static-analysis/menu-database-query-map.json"
DISPATCH = ROOT / "data/static-analysis/link-export-dispatch-tables.json"
PHYSICAL_RX3 = (
    ROOT
    / "data/experiments/sort-secondary-render-6/"
    "source-rx3-rekordbox-working-ap-20260927.pcap"
)
OUTPUT = ROOT / "data/static-analysis/link-export-request-vocabulary.json"
ALPHA_SOURCE_SHA256 = "d3563dc35962b21ba224906f2307f8e7f872368d4b16cdd93c9ee24d9104fa95"
ALPHA_COMMIT = "a70aeefb202ffddd2900e7b40e339a47ac077057"
DYSENTERY_COMMIT = "f62a24ba947f9db4c1553bb2dc3ba76de1fecbb4"
RX3_DECOMP_COMMIT = "a70aeefb202ffddd2900e7b40e339a47ac077057"
RX3_RECV_SOURCE = (
    ROOT.parent
    / "alphatheta-docs/devices/xdj-rx3/application/assets/"
    "decompiled-readable/_unattributed/chunk_0025.c"
)
RX3_RECV_SOURCE_SHA256 = (
    "179f437b7779bdbfb7d0c44d025082417d5e5cd03767a2b4287004d4844cdabd"
)
PHYSICAL_RX3_SHA256 = (
    "bee17ddfa72b093479a68c1590953ddc79629cdf43905769761c656a5149aa2b"
)
ROW = re.compile(r"^\| `([0-9a-fA-F]{4})` \| `([^`]+)` \|$")

PHYSICAL_CLIENT_CONTROLS = [
    {
        "kind": "0001",
        "name": "cancel request (Dysentery: invalid data)",
        "direction": "client-control",
        "menu_family": None,
        "coverage": "physical-client-control",
        "evidence": ["CAP", "DYS", "RX3DEC"],
        "rekordbox_dispatcher": None,
        "rekordbox_route": [],
        "rekordbox_target": None,
        "static_table": None,
        "rejection_reason": None,
        "reply_kind": None,
        "dependencies": None,
        "observation": (
            "The physical RX3 sent five zero-argument cancellation commands "
            "while artwork requests were outstanding, preserving each artwork "
            "transaction ID. RX3 RecvFromCommTask constructs kind 0x0001 when "
            "CheckCanceledRequest reports a GUI cancellation. Three commands "
            "followed a captured 0x4002 reply and two had no correlated captured "
            "reply; packet order therefore does not identify whether the reply "
            "had already reached the client task."
        ),
    }
]


ANALYSIS_REPLIES = {
    "2004": "4402",
    "2104": "4702",
    "2204": "4602",
    "2504": "4502",
    "2804": "4000",
    "2904": "4A02",
    "2A04": "4C02",
    "2B04": "4E02",
    "2C04": "4F02",
    "2D04": "4F02",
}

LOW_BYTE_TABLES = {
    0x1: "list-low-byte",
    0x2: "analysis-class-low-byte",
    0x3: "other-client-low-byte",
}

BOUNDED_HANDLER_TABLES = {
    "PSvDBMain::OnOtherListCmd": "other-list-high-byte",
    "PSvDBMain::OnYearListCmd": "year-high-byte",
    "PSvDBMain::OnSongAnlzCmd": "song-analysis-high-byte",
    "PSvDBMain::OnHistoryCmd": "history-high-byte",
    "PSvDBMain::OnPrepareCmd": "prepare-high-byte",
    "PSvDBMain::OnOtherCmd": "other-command-high-byte",
    "PSvDBMain::OnFilterCmd": "filter-high-byte",
}

DIRECT_ONLY_HANDLERS = {
    "PSvDBMain::OnImgCmd": {"2003", "2103"},
    "PSvDBMain::OnListBuffCmd": {"3000", "3100"},
    "special-0x3104-only": {"3104"},
    "PSvDBMain::OnUserCmd": {"3006"},
    "PSvDBMain::OnOther2Cmd": {"3008"},
    "PSvDBMain::OnWriteCmd": {
        "2005",
        "2105",
        "2205",
        "2305",
        "2405",
        "2505",
        "2605",
        "2705",
        "2805",
        "2905",
    },
    "PSvDBMain::OnDbModCmd": {"2107", "2507"},
}

DEPENDENCIES = {
    "100B": {
        "database": ["djmdKey live rows"],
        "filesystem": "No filesystem access is visible; AppSync materializes the key root into the location-keyed list buffer.",
    },
    "110B": {
        "database": ["djmdContent", "djmdKey", "sort-dependent lookup tables"],
        "filesystem": "No filesystem access is visible; AppSync builds ordinary track rows selected by KeyID.",
    },
    "130C": {
        "database": [],
        "filesystem": "Rekordbox recognizes and logs this XDJ-RR cue-track root kind but returns before any builder or reply.",
    },
    "2003": {
        "database": ["AppSync djmdContent.ImagePath", "AppSync djmdPlaylist.ImagePath", "Master djmdImage path"],
        "filesystem": "The active AppSync path reads ImagePath directly; the Master fallback resolves an image ID. Both use the common JPEG loader.",
    },
    "2103": {
        "database": ["AppSync djmdContent.ImagePath", "AppSync djmdPlaylist.ImagePath", "Master djmdContent.ImageID", "Master djmdImage path"],
        "filesystem": "AppSync treats the content ID as the direct ImagePath row ID; the Master fallback resolves Content.ImageID first.",
    },
    "2004": {
        "database": ["content analysis-path lookup"],
        "filesystem": "ANLZ path is parsed by MstLoadLoudWave and MstLoadDotWave.",
    },
    "2104": {
        "database": ["djmdCue"],
        "filesystem": "No audio decoding is visible in the recovered database cue path.",
    },
    "2204": {
        "database": ["content analysis-path lookup"],
        "filesystem": "ANLZ path is parsed by MstLoadBeatGrid and MstLoadBeatGridWithHeader.",
    },
    "2504": {
        "database": ["content analysis-path lookup"],
        "filesystem": "ANLZ path is parsed by MstLoadVBR.",
    },
    "2804": {
        "database": ["content analysis-path lookup"],
        "filesystem": "The quantize loader returns an offset through a 4000 numeric reply.",
    },
    "2904": {
        "database": ["content analysis-path lookup"],
        "filesystem": "Detailed waveform data is loaded from the analysis file.",
    },
    "2A04": {
        "database": ["content analysis-path lookup"],
        "filesystem": "Key-analysis data is loaded from the analysis file.",
    },
    "2B04": {
        "database": ["djmdCue and cue-option lookups or AppSync cue callback"],
        "filesystem": "No analysis-file or audio read is visible in either recovered extended-cue builder.",
    },
    "2C04": {
        "database": ["content analysis-path lookup"],
        "filesystem": "EXT and 2EX reach MstLoadAtomInfo except PCP2, PCPT, and PMAI, which are explicitly returned empty.",
    },
    "2D04": {
        "database": ["content analysis-path lookup"],
        "filesystem": "Alias of the specified-atom loader in Rekordbox 7.2.19.",
    },
    "2005": {
        "database": ["djmdContent.AnalysisDataPath"],
        "filesystem": "SavWave resolves the analysis path and writes 400 loud-wave samples plus 100 dot-wave bytes through MstStoreLoudWave and MstStoreDotWave.",
    },
    "2105": {
        "database": ["djmdCue and cue-option rows"],
        "filesystem": "No audio decoding is visible; the legacy cue writer mutates cue records and returns the resulting 4702 cue set.",
    },
    "2107": {
        "database": ["djmdContent.Rating"],
        "filesystem": "No filesystem access is visible; modTrackRate reads the current Rating and updates it by content ID only when the byte value changes.",
    },
    "2205": {
        "database": [],
        "filesystem": "SavVbrInf is a constant-success stub in Rekordbox 7.2.19 and does not inspect its message.",
    },
    "2305": {
        "database": [],
        "filesystem": "Rekordbox recognizes and logs this disc-cue write kind but invokes no writer and sends no reply.",
    },
    "2405": {
        "database": [],
        "filesystem": "Rekordbox recognizes and logs this delete-all-disc-cue kind but invokes no writer and sends no reply.",
    },
    "2505": {
        "database": [],
        "filesystem": "Rekordbox recognizes and logs this disc-ID registration kind but invokes no writer and sends no reply.",
    },
    "2507": {
        "database": ["djmdContent.BPM"],
        "filesystem": "No filesystem access is visible; modTrackBPM reads the current BPM and updates it by content ID only when the value changes.",
    },
    "2605": {
        "database": ["djmdContent.AnalysisDataPath", "djmdContent.ContentLink"],
        "filesystem": "SavQtzOfs writes the quantize offset to the analysis path, then mirrors its nonzero state into ContentLink bit zero.",
    },
    "2705": {
        "database": ["djmdCue and cue-option rows"],
        "filesystem": "No audio decoding is visible; SavUsbCueExt applies the extended cue mutation and replies through RetNewCueToClient (4E02).",
    },
    "2805": {
        "database": ["djmdContent.AnalysisDataPath"],
        "filesystem": "SaveSpecifiedAtomInfo validates the atom and extension, derives a sibling analysis file, and writes it through MstSaveAtomData.",
    },
    "2905": {
        "database": ["djmdContent.AnalysisDataPath"],
        "filesystem": "UpdateSpecifiedAtomInfo accepts PQT2 only, derives a sibling analysis file, and updates it through MstUpdateAtomData.",
    },
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_alpha_commands(path: Path) -> list[dict[str, str]]:
    data = path.read_bytes()
    actual_sha256 = sha256(data)
    if actual_sha256 != ALPHA_SOURCE_SHA256:
        raise ValueError(
            f"AlphaTheta command source SHA-256 {actual_sha256} does not match "
            f"{ALPHA_SOURCE_SHA256}"
        )

    section = None
    commands = []
    for line in data.decode("utf-8").splitlines():
        if line == "### Requests":
            section = "request"
            continue
        if line == "### Replies":
            section = "reply"
            continue
        if section is None:
            continue

        match = ROW.match(line)
        if match:
            commands.append(
                {
                    "kind": match.group(1).upper(),
                    "name": match.group(2),
                    "direction": section,
                }
            )

    kinds = [command["kind"] for command in commands]
    if len(kinds) != len(set(kinds)):
        raise ValueError("AlphaTheta request/reply vocabulary contains duplicate kinds")
    if not commands:
        raise ValueError("AlphaTheta request/reply vocabulary is empty")

    return commands


def query_families(path: Path) -> dict[str, dict[str, object]]:
    document = json.loads(path.read_text())
    return {
        request: family
        for family in document["families"]
        for request in family["requests"]
    }


def table_by_id(document: dict[str, object]) -> dict[str, dict[str, object]]:
    return {table["id"]: table for table in document["tables"]}


def dispatch_entries(path: Path) -> tuple[dict[str, dict[str, str]], dict[str, object]]:
    document = json.loads(path.read_text())
    entries = {
        entry["request_kind"]: {
            "dispatcher": entry["owner"],
            "target": entry["target"],
            "reply_kind": entry["reply_kind"],
        }
        for entry in document["direct_dispatch"]
    }

    for table in document["tables"]:
        for entry in table["entries"]:
            kind = entry["key"]
            if len(kind) != 4:
                continue

            entries[kind] = {
                "dispatcher": table["owner"],
                "table": table["id"],
                "target": entry["target"],
                "target_address": entry["target_address"],
                "reply_kind": ANALYSIS_REPLIES.get(kind),
            }

    return entries, document


def static_route(kind: str, dispatch_document: dict[str, object]) -> dict[str, object]:
    numeric_kind = int(kind, 16)
    command_class = numeric_kind >> 12
    table_id = LOW_BYTE_TABLES.get(command_class)
    if table_id is None:
        top_level = dispatch_document["top_level"]
        default_target = top_level["default_target"]
        return {
            "dispatcher": default_target,
            "rejected": True,
            "route": [top_level["owner"], default_target],
            "reason": (
                f"request class 0x{command_class:x} is outside the top-level "
                "1xxx/2xxx/3xxx dispatch"
            ),
            "reply_kind": top_level["default_reply_kind"],
        }

    tables = table_by_id(dispatch_document)
    table = tables[table_id]
    low_byte = f"{numeric_kind & 0xFF:02X}"
    entry = next(
        (candidate for candidate in table["entries"] if candidate["key"] == low_byte),
        None,
    )
    route = [table["owner"]]
    if entry is None:
        return {
            "dispatcher": table["owner"],
            "rejected": True,
            "route": [*route, dispatch_document["top_level"]["default_target"]],
            "reason": f"low byte 0x{low_byte} is outside {table_id}",
            "reply_kind": dispatch_document["top_level"]["default_reply_kind"],
        }

    handler = entry["target"]
    route.append(handler)
    if handler.startswith("unsupported-"):
        return {
            "dispatcher": table["owner"],
            "rejected": True,
            "route": [*route, dispatch_document["top_level"]["default_target"]],
            "reason": f"{table_id} routes low byte 0x{low_byte} to {handler}",
            "reply_kind": dispatch_document["top_level"]["default_reply_kind"],
        }

    bounded_table_id = BOUNDED_HANDLER_TABLES.get(handler)
    if bounded_table_id is not None:
        bounded_entry = next(
            (
                candidate
                for candidate in tables[bounded_table_id]["entries"]
                if candidate["key"] == kind
            ),
            None,
        )
        if bounded_entry is None:
            return {
                "dispatcher": handler,
                "rejected": True,
                "route": [*route, dispatch_document["top_level"]["default_target"]],
                "reason": f"{kind} is outside {bounded_table_id}",
                "reply_kind": dispatch_document["top_level"]["default_reply_kind"],
            }
        if bounded_entry["target"].startswith("unsupported-"):
            return {
                "dispatcher": handler,
                "rejected": True,
                "route": [*route, dispatch_document["top_level"]["default_target"]],
                "reason": (
                    f"{bounded_table_id} routes {kind} to "
                    f"{bounded_entry['target']}"
                ),
                "reply_kind": dispatch_document["top_level"]["default_reply_kind"],
            }

    accepted = DIRECT_ONLY_HANDLERS.get(handler)
    if accepted is not None and kind not in accepted:
        return {
            "dispatcher": handler,
            "rejected": True,
            "route": [*route, dispatch_document["top_level"]["default_target"]],
            "reason": f"{handler} recognizes only {', '.join(sorted(accepted))}",
            "reply_kind": dispatch_document["top_level"]["default_reply_kind"],
        }

    return {"dispatcher": handler, "rejected": False, "route": route}


def classify(
    command: dict[str, str],
    families: dict[str, dict[str, object]],
    exact_dispatch: dict[str, dict[str, str]],
    dispatch_document: dict[str, object],
) -> dict[str, object]:
    kind = command["kind"]
    direction = command["direction"]
    family = families.get(kind)
    result: dict[str, object] = {
        **command,
        "menu_family": family["id"] if family else None,
        "coverage": "source-vocabulary-only",
        "evidence": ["ALPHA"],
        "rekordbox_dispatcher": None,
        "rekordbox_route": [],
        "rekordbox_target": None,
        "static_table": None,
        "rejection_reason": None,
        "reply_kind": None,
        "dependencies": DEPENDENCIES.get(kind),
    }

    if direction == "reply":
        result["coverage"] = "reply-vocabulary"
        return result

    route = static_route(kind, dispatch_document)
    result["rekordbox_dispatcher"] = route["dispatcher"]
    result["rekordbox_route"] = route["route"]
    if route["rejected"]:
        result["rejection_reason"] = route["reason"]

    if family and "OBS" in family["evidence"]:
        result["coverage"] = "real-rekordbox-menu-oracle"
        result["evidence"] = ["ALPHA", "OBS", "DB", "DEC"]
        if kind in exact_dispatch:
            dispatch = exact_dispatch[kind]
            result["rekordbox_target"] = dispatch["target"]
            result["static_table"] = dispatch.get("table")
            result["reply_kind"] = dispatch.get("reply_kind")
            result["rekordbox_route"] = [
                *result["rekordbox_route"],
                dispatch["target"],
            ]
        return result

    if kind in exact_dispatch:
        dispatch = exact_dispatch[kind]
        target = dispatch["target"]
        if target in {"recognized-log-only"}:
            result["coverage"] = "rekordbox-recognized-log-only"
        elif target.startswith("unsupported-"):
            result["coverage"] = "rekordbox-static-rejected"
            result["rejection_reason"] = route.get("reason", target)
            result["evidence"] = ["ALPHA", "DEC"]
            result["rekordbox_dispatcher"] = dispatch["dispatcher"]
            result["rekordbox_route"] = route["route"]
            result["rekordbox_target"] = target
            result["static_table"] = dispatch.get("table")
            result["reply_kind"] = route.get("reply_kind")
            return result
        else:
            result["coverage"] = "rekordbox-static-dispatch"
        result["evidence"] = ["ALPHA", "DEC"]
        result["rekordbox_dispatcher"] = dispatch["dispatcher"]
        result["rekordbox_route"] = [*route["route"], target]
        result["rekordbox_target"] = target
        result["static_table"] = dispatch.get("table")
        result["reply_kind"] = dispatch.get("reply_kind")
        return result

    if route["rejected"]:
        result["coverage"] = "rekordbox-static-rejected"
        result["evidence"] = ["ALPHA", "DEC"]
        result["rejection_reason"] = route["reason"]
        result["reply_kind"] = route["reply_kind"]
        if kind == "2006":
            result["evidence"].append("DYS")
    return result


def classify_static_only(
    kind: str,
    dispatch: dict[str, str],
    dispatch_document: dict[str, object],
) -> dict[str, object]:
    target = dispatch["target"]
    coverage = "rekordbox-static-dispatch"
    rejection_reason = None
    if target == "recognized-log-only":
        coverage = "rekordbox-recognized-log-only"
    elif target.startswith("unsupported-"):
        coverage = "rekordbox-static-rejected"
        rejection_reason = target

    route = static_route(kind, dispatch_document)["route"]
    return {
        "kind": kind,
        "name": f"REKORDBOX_STATIC_{target.upper().replace('-', '_')}",
        "direction": "request",
        "menu_family": None,
        "coverage": coverage,
        "evidence": ["DEC"],
        "rekordbox_dispatcher": dispatch["dispatcher"],
        "rekordbox_route": [*route, target] if route else [dispatch["dispatcher"], target],
        "rekordbox_target": target,
        "static_table": dispatch.get("table"),
        "rejection_reason": rejection_reason,
        "reply_kind": dispatch.get("reply_kind"),
        "dependencies": DEPENDENCIES.get(kind),
    }


def build(alpha_source: Path, query_map: Path, dispatch_path: Path) -> dict[str, object]:
    physical_sha256 = sha256(PHYSICAL_RX3.read_bytes())
    if physical_sha256 != PHYSICAL_RX3_SHA256:
        raise ValueError(
            f"physical RX3 PCAP SHA-256 {physical_sha256} does not match "
            f"{PHYSICAL_RX3_SHA256}"
        )

    rx3_recv_sha256 = sha256(RX3_RECV_SOURCE.read_bytes())
    if rx3_recv_sha256 != RX3_RECV_SOURCE_SHA256:
        raise ValueError(
            f"RX3 receive source SHA-256 {rx3_recv_sha256} does not match "
            f"{RX3_RECV_SOURCE_SHA256}"
        )

    commands = parse_alpha_commands(alpha_source)
    families = query_families(query_map)
    exact_dispatch, dispatch_document = dispatch_entries(dispatch_path)
    classified = [
        classify(command, families, exact_dispatch, dispatch_document)
        for command in commands
    ]
    classified.extend(PHYSICAL_CLIENT_CONTROLS)
    alpha_kinds = {command["kind"] for command in commands}

    for kind in sorted(families, key=lambda value: int(value, 16)):
        if kind in alpha_kinds:
            continue
        classified.append(
            classify(
                {
                    "kind": kind,
                    "name": "conformance-only malformed/guessed request",
                    "direction": "probe",
                },
                families,
                exact_dispatch,
                dispatch_document,
            )
        )

    known_kinds = {command["kind"] for command in classified}
    for kind, dispatch in exact_dispatch.items():
        if kind in known_kinds:
            continue

        classified.append(classify_static_only(kind, dispatch, dispatch_document))

    classified.sort(key=lambda command: int(command["kind"], 16))
    coverage_counts: dict[str, int] = {}
    direction_counts: dict[str, int] = {}
    for command in classified:
        coverage = str(command["coverage"])
        direction = str(command["direction"])
        coverage_counts[coverage] = coverage_counts.get(coverage, 0) + 1
        direction_counts[direction] = direction_counts.get(direction, 0) + 1

    return {
        "format": 2,
        "scope": (
            "Complete known Link Export command vocabulary from CDJ-3000 firmware, "
            "the retained physical RX3 session, conformance probes, and Rekordbox "
            "7.2.19 dispatch evidence. A client command proves client vocabulary, "
            "not Rekordbox server support."
        ),
        "sources": [
            {
                "id": "ALPHA",
                "path": str(alpha_source.resolve()),
                "commit": ALPHA_COMMIT,
                "sha256": ALPHA_SOURCE_SHA256,
            },
            {
                "id": "DYS",
                "path": str((ROOT.parent / "dysentery").resolve()),
                "commit": DYSENTERY_COMMIT,
            },
            {
                "id": "CAP",
                "path": str(PHYSICAL_RX3.relative_to(ROOT)),
                "sha256": PHYSICAL_RX3_SHA256,
            },
            {
                "id": "RX3DEC",
                "path": str(RX3_RECV_SOURCE.resolve()),
                "commit": RX3_DECOMP_COMMIT,
                "sha256": RX3_RECV_SOURCE_SHA256,
                "functions": {"RecvFromCommTask": "0x0025fc94"},
            },
            {
                "id": "DEC",
                "path": str(dispatch_path.relative_to(ROOT)),
                "rekordbox_sha256": dispatch_document["source"]["sha256"],
            },
            {
                "id": "OBS",
                "path": "conformance/goldens/rekordbox-7.2.19",
            },
            {
                "id": "DB",
                "path": "data/static-analysis/menu-database-query-map.json",
            },
        ],
        "summary": {
            "command_count": len(classified),
            "alpha_command_count": len(commands),
            "menu_corpus_request_count": sum(
                "OBS" in family["evidence"] for family in families.values()
            ),
            "direction_counts": direction_counts,
            "coverage_counts": coverage_counts,
        },
        "commands": classified,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--alpha-source", type=Path, default=ALPHA_SOURCE)
    parser.add_argument("--query-map", type=Path, default=QUERY_MAP)
    parser.add_argument("--dispatch", type=Path, default=DISPATCH)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()

    document = build(args.alpha_source, args.query_map, args.dispatch)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(document, indent=2) + "\n")


if __name__ == "__main__":
    main()
