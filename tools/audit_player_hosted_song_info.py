#!/usr/bin/env python3
"""Generate the player-hosted role audit for Song Info kinds 0x2202-0x2502."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
WORKSPACE = ROOT.parent
DEFAULT_OUTPUT = ROOT / "data/static-analysis/player-hosted-song-info.json"

SOURCES = {
    "dysentery_messages": WORKSPACE / "dysentery/src/dysentery/dbserver.clj",
    "dysentery_protocol": WORKSPACE
    / "dysentery/doc/modules/ROOT/pages/track_metadata.adoc",
    "alphatheta_types": WORKSPACE
    / "alphatheta-connect/src/remotedb/message/types.ts",
    "alphatheta_queries": WORKSPACE
    / "alphatheta-connect/src/remotedb/queries.ts",
    "xdj_rx_server": WORKSPACE
    / "alphatheta-docs/devices/xdj-rx/application/assets/decompiled-readable/_unattributed/chunk_000f.c",
    "xdj_rx_format": WORKSPACE
    / "alphatheta-docs/devices/xdj-rx/application/assets/decompiled-readable/_unattributed/chunk_0018.c",
    "xdj_rx_client": WORKSPACE
    / "alphatheta-docs/devices/xdj-rx/application/assets/decompiled-readable/_unattributed/chunk_001d.c",
    "xdj_rr_server": WORKSPACE
    / "alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_0011.c",
    "xdj_rr_client": WORKSPACE
    / "alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_0020.c",
    "xdj_rx2_server": WORKSPACE
    / "alphatheta-docs/devices/xdj-rx2/application/assets/decompiled/_unattributed/chunk_0012.c",
    "xdj_rx2_client": WORKSPACE
    / "alphatheta-docs/devices/xdj-rx2/application/assets/decompiled/_unattributed/chunk_0022.c",
    "xdj_rx3_server": WORKSPACE
    / "alphatheta-docs/devices/xdj-rx3/application/assets/decompiled-readable/_unattributed/chunk_0015.c",
    "xdj_rx3_client": WORKSPACE
    / "alphatheta-docs/devices/xdj-rx3/application/assets/decompiled-readable/_unattributed/chunk_0026.c",
    "xdj_xz_server": WORKSPACE
    / "alphatheta-docs/devices/xdj-xz/application/assets/decompiled/_unattributed/chunk_0010.c",
    "xdj_xz_client": WORKSPACE
    / "alphatheta-docs/devices/xdj-xz/application/assets/decompiled/_unattributed/chunk_0020.c",
    "cdj_3000_names": WORKSPACE
    / "alphatheta-docs/devices/cdj-3000/application/decompiled/_unattributed/chunk_b3.c",
    "cdj_3000_format": WORKSPACE
    / "alphatheta-docs/devices/cdj-3000/application/decompiled/_unattributed/chunk_bf.c",
    "xdj_az_names": WORKSPACE
    / "alphatheta-docs/devices/xdj-az/application/assets/decompiled/_unattributed/chunk_0078.c",
    "xdj_az_format": WORKSPACE
    / "alphatheta-docs/devices/xdj-az/application/assets/decompiled/_unattributed/chunk_00e7.c",
    "omnis_duo_names": WORKSPACE
    / "alphatheta-docs/devices/omnis-duo/application/assets/decompiled/_unattributed/chunk_0061.c",
    "omnis_duo_format": WORKSPACE
    / "alphatheta-docs/devices/omnis-duo/application/assets/decompiled/_unattributed/chunk_00df.c",
    "cdj_1500x_names": WORKSPACE
    / "alphatheta-docs/devices/cdj-1500x/application/assets/decompiled/_unattributed/chunk_0069.c",
    "cdj_1500x_format": WORKSPACE
    / "alphatheta-docs/devices/cdj-1500x/application/assets/decompiled/_unattributed/chunk_00fa.c",
}

REQUIRED = {
    "dysentery_messages": (
        '0x2202 {:type      "request non-rekordbox track data"',
        "message-type (if (= 1 track-type) 0x2002 0x2202)",
    ),
    "dysentery_protocol": (
        "using the value `2202` (instead of `2002`)",
        "`02` for non-rekordbox tracks loaded from media slots",
        "`05` for CD audio tracks playing in the CD slot",
    ),
    "alphatheta_types": (
        "GetGenericMetadata = 0x2202",
    ),
    "alphatheta_queries": (
        "Lookup generic metadata for an unanalyzed track",
        "type: Request.GetGenericMetadata",
    ),
    "xdj_rx_server": (
        "Handles request 0x2202 for type 2 or 5 items",
        "if ((kind == 2) || (kind == 5))",
        "if (request_code == 0x2302)",
        "Builds a six-entry info list",
        "entry_kind = 4;",
        "entry_kind = 7;",
        "entry_kind = 2;",
        "entry_kind = 0xb;",
        "entry_kind = 0xd;",
        "entry_kind = 0xf;",
        "if (request_code == 0x2502)",
        "if (request_code != 0x2402)",
        "Logs an unsupported request and marks the message done.",
    ),
    "xdj_rx_format": (
        "if (command == (undefined1 *)0x2302)",
        "if (command != (undefined1 *)0x2402)",
        "if (command == (undefined1 *)0x2502)",
    ),
    "xdj_rx_client": (
        "Sends database request 0x2202",
        "Sends database request 0x2302",
        "Requests a track's decode information (command 0x2402)",
        "FUN_001d9ea4(req_id,0x4802",
        "Registers a track length (command 0x2502)",
    ),
    "xdj_rr_server": (
        "DBSMain_GetDecodeSongInf",
        "DBSMain_RegSongLength",
        "ErrHandle_Log(0xfffffffb,0,0);",
    ),
    "xdj_rr_client": (
        "dbcl_GetDecodeInfo",
        "dbcl_WaitBinary(uVar5,0x4802",
        "dbcl_RegTrackLength",
        "SetHeader(param_1,iVar1,0x2502,param_2);",
    ),
    "xdj_rx2_server": (
        "DBSMain_GetDecodeSongInf",
        "DBSMain_RegSongLength",
        "ErrHandle_Log(0xfffffffb,0,0);",
    ),
    "xdj_rx2_client": (
        "dbcl_GetDecodeInfo",
        "dbcl_WaitBinary(uVar5,0x4802",
        "dbcl_RegTrackLength",
        "SetHeader(param_1,iVar1,0x2502,param_2);",
    ),
    "xdj_rx3_server": (
        "DBSMain_GetDecodeSongInf",
        "Stub: no-op function for decode song info",
        "DBSMain_RegSongLength",
        "ErrHandle_Log(0xfffffffb, 0, 0);",
    ),
    "xdj_rx3_client": (
        "dbcl_GetDecodeInfo",
        "dbcl_WaitBinary(msg_id, 0x4802",
        "dbcl_RegTrackLength",
        "SetHeader(rmif, connection, 0x2502, track_id);",
    ),
    "xdj_xz_server": (
        "DBSMain_GetDecodeSongInf",
        "DBSMain_RegSongLength",
        "ErrHandle_Log(0xfffffffb,0,0);",
    ),
    "xdj_xz_client": (
        "dbcl_GetDecodeInfo",
        "dbcl_WaitBinary(uVar5,0x4802",
        "dbcl_RegTrackLength",
        "SetHeader(param_1,iVar1,0x2502,param_2);",
    ),
    "cdj_3000_names": ("CMD_GET_DECODE_INFO", "CMD_REG_TRK_LENGTH"),
    "cdj_3000_format": ("0x2402", "0x2502", "0x4802"),
    "xdj_az_names": ("CMD_GET_DECODE_INFO", "CMD_REG_TRK_LENGTH"),
    "xdj_az_format": ("0x2402", "0x2502", "0x4802"),
    "omnis_duo_names": ("CMD_GET_DECODE_INFO", "CMD_REG_TRK_LENGTH"),
    "omnis_duo_format": ("0x2402", "0x2502", "0x4802"),
    "cdj_1500x_names": ("CMD_GET_DECODE_INFO", "CMD_REG_TRK_LENGTH"),
    "cdj_1500x_format": ("0x2402", "0x2502", "0x4802"),
}

NEWER_TREES = {
    "CDJ-3000": {
        "root": WORKSPACE / "alphatheta-docs/devices/cdj-3000/application/decompiled",
        "name_source": SOURCES["cdj_3000_names"],
        "format_source": SOURCES["cdj_3000_format"],
    },
    "XDJ-AZ": {
        "root": WORKSPACE / "alphatheta-docs/devices/xdj-az/application/assets/decompiled",
        "name_source": SOURCES["xdj_az_names"],
        "format_source": SOURCES["xdj_az_format"],
    },
    "OMNIS-DUO": {
        "root": WORKSPACE / "alphatheta-docs/devices/omnis-duo/application/assets/decompiled",
        "name_source": SOURCES["omnis_duo_names"],
        "format_source": SOURCES["omnis_duo_format"],
    },
    "CDJ-1500X": {
        "root": WORKSPACE / "alphatheta-docs/devices/cdj-1500x/application/assets/decompiled",
        "name_source": SOURCES["cdj_1500x_names"],
        "format_source": SOURCES["cdj_1500x_format"],
    },
}

KINDS = ("0x2402", "0x2502", "0x4802")
KIND_PATTERNS = {
    kind: re.compile(rf"(?<![0-9a-fA-F]){re.escape(kind)}(?![0-9a-fA-F])")
    for kind in KINDS
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit_newer_tree(device: str, config: dict[str, Path]) -> dict[str, object]:
    root = config["root"]
    paths = sorted(root.rglob("*.c"))
    manifest = hashlib.sha256()
    occurrences: dict[str, list[dict[str, object]]] = {kind: [] for kind in KINDS}

    for path in paths:
        relative = path.relative_to(root).as_posix()
        data = path.read_bytes()
        manifest.update(relative.encode())
        manifest.update(b"\0")
        manifest.update(hashlib.sha256(data).digest())

        if not any(kind.encode() in data for kind in KINDS):
            continue

        text = data.decode(errors="replace")
        for line_number, line in enumerate(text.splitlines(), 1):
            for kind, pattern in KIND_PATTERNS.items():
                if pattern.search(line):
                    occurrences[kind].append(
                        {"path": relative, "line": line_number, "text": line.strip()}
                    )

    expected_files = {
        config["name_source"].relative_to(root).as_posix(): "command-name-table",
        config["format_source"].relative_to(root).as_posix(): "parameter-format-table",
    }
    occurrence_files = sorted(
        {entry["path"] for entries in occurrences.values() for entry in entries}
    )
    if set(occurrence_files) != set(expected_files):
        raise SystemExit(
            f"{device}: protocol literals escaped known name/format tables: "
            f"{occurrence_files}"
        )

    return {
        "device": device,
        "root": os.path.relpath(root, ROOT),
        "c_source_count": len(paths),
        "c_source_manifest_sha256": manifest.hexdigest(),
        "request_parameter_tags": {
            "0x2402": [6, 6],
            "0x2502": [6, 6, 6],
        },
        "occurrence_file_roles": expected_files,
        "exact_literal_occurrences": occurrences,
        "result": (
            "Every exact 0x2402/0x2502/0x4802 literal is confined to the "
            "command-name and parameter-format tables; no literal client caller, "
            "wait site, or server handler exists in the complete decompiled C tree."
        ),
        "boundary": (
            "This does not exclude computed command values, table-driven function "
            "pointers, or implementation omitted or misrecovered by decompilation."
        ),
    }


def build() -> dict[str, object]:
    for name, needles in REQUIRED.items():
        text = SOURCES[name].read_text()
        missing = [needle for needle in needles if needle not in text]
        if missing:
            raise SystemExit(f"{SOURCES[name]}: missing evidence: {missing}")

    newer_literal_audit = [
        audit_newer_tree(device, config)
        for device, config in NEWER_TREES.items()
    ]

    return {
        "format": 2,
        "scope": "player-hosted meanings of Song Info request kinds rejected by Rekordbox 7.2.19",
        "sources": {
            os.path.relpath(path, ROOT): sha256(path)
            for path in SOURCES.values()
        },
        "generation_matrix": [
            {
                "device": device,
                "0x2402_client": "request followed by wait for 0x4802",
                "0x2402_server": "unsupported stub logs 0xfffffffb and marks request complete",
                "0x2502_client": "one-way register track length request",
                "0x2502_server": "unsupported stub logs 0xfffffffb and marks request complete",
            }
            for device in ("XDJ-RX", "XDJ-RR", "XDJ-RX2", "XDJ-XZ", "XDJ-RX3")
        ],
        "newer_literal_audit": newer_literal_audit,
        "vocabulary_only_matrix": [
            {
                "device": device,
                "request_names": {
                    "0x2402": "CMD_GET_DECODE_INFO",
                    "0x2502": "CMD_REG_TRK_LENGTH",
                },
                "format_table_kinds": ["0x2402", "0x2502", "0x4802"],
                "boundary": (
                    "whole-tree exact-literal audit finds these kinds only in the "
                    "command-name and parameter-format tables; computed or omitted "
                    "implementations remain possible"
                ),
            }
            for device in ("CDJ-3000", "XDJ-AZ", "OMNIS-DUO", "CDJ-1500X")
        ],
        "requests": [
            {
                "kind": "0x2202",
                "name": "generic/non-Rekordbox track metadata",
                "client_arguments": ["packed context", "track number or player-reported ID"],
                "player_server": (
                    "XDJ-RX accepts packed track types 2 and 5; it returns an already "
                    "available metadata list or begins an asynchronous source fetch"
                ),
                "public_protocol": (
                    "Dysentery and alphatheta-connect independently construct this request "
                    "for unanalyzed media-slot or audio-CD tracks"
                ),
                "rekordbox_7_2_19": "recognized request with kind-specific 0x4003; no AppSync builder",
                "boundary": "successful serving belongs to a player-hosted database role",
            },
            {
                "kind": "0x2302",
                "name": "player unit/track summary root",
                "client_arguments": ["packed context"],
                "player_server": (
                    "XDJ-RX returns six rows with item kinds Title 0x04, Artist 0x07, "
                    "Album 0x02, Time 0x0b, BPM 0x0d, and Key 0x0f"
                ),
                "public_protocol": None,
                "rekordbox_7_2_19": "recognized request with kind-specific 0x4003; no AppSync builder",
                "boundary": "successful serving is statically proven in XDJ-RX firmware",
            },
            {
                "kind": "0x2402",
                "name": "track decode information",
                "client_arguments": ["packed context", "track ID"],
                "player_server": (
                    "XDJ-RX, XDJ-RR, XDJ-RX2, XDJ-XZ, and XDJ-RX3 all dispatch "
                    "to an unsupported stub that logs 0xfffffffb and completes"
                ),
                "client_reply": "0x4802 with a scalar plus length/blob outputs",
                "public_protocol": None,
                "rekordbox_7_2_19": "recognized request with kind-specific 0x4003; no AppSync builder",
                "boundary": (
                    "the client contract exists across all five recovered generations, but none "
                    "implements a successful local server"
                ),
            },
            {
                "kind": "0x2502",
                "name": "register track length",
                "client_arguments": ["packed context", "track ID", "length"],
                "player_server": (
                    "XDJ-RX, XDJ-RR, XDJ-RX2, XDJ-XZ, and XDJ-RX3 all dispatch "
                    "to an unsupported stub that logs 0xfffffffb and completes"
                ),
                "client_reply": None,
                "public_protocol": None,
                "rekordbox_7_2_19": "recognized request with kind-specific 0x4003; no AppSync builder",
                "boundary": "all five recovered clients emit it as a one-way registration",
            },
        ],
        "conclusion": (
            "Rekordbox rejection describes its serving role only. The four kinds are not "
            "one homogeneous unsupported family: 0x2202 and 0x2302 have successful "
            "player-hosted builders, while 0x2402 and 0x2502 have client contracts but "
            "unsupported server stubs in all five recovered XDJ generations. Four newer "
            "firmwares retain the command names and wire formats. Whole-tree exact-"
            "literal audits find no client caller, wait site, or server handler outside "
            "those tables, while computed or decompiler-omitted implementations remain "
            "an explicit boundary."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    args.output.write_text(json.dumps(build(), indent=2) + "\n")


if __name__ == "__main__":
    main()
