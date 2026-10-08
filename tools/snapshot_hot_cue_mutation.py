#!/usr/bin/env python3
"""Capture the durable database state for the Hot Cue Bank mutation fixture."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "conformance"))

from build_fixture import connect, key_from_options


BANK_ID = "9060"
MUTATION_COLUMNS = (
    "ID",
    "HotCueBanklistID",
    "ContentID",
    "TrackNo",
    "CueID",
    "InMsec",
    "InFrame",
    "InMpegFrame",
    "InMpegAbs",
    "OutMsec",
    "OutFrame",
    "OutMpegFrame",
    "OutMpegAbs",
    "Color",
    "ColorTableIndex",
    "ActiveLoop",
    "Comment",
    "BeatLoopSize",
    "CueMicrosec",
    "InPointSeekInfo",
    "OutPointSeekInfo",
    "rb_data_status",
    "rb_local_data_status",
    "rb_local_deleted",
    "rb_local_synced",
    "usn",
    "rb_local_usn",
    "created_at",
    "updated_at",
)
CUE_COLUMNS = (
    "ID",
    "ContentID",
    "InMsec",
    "InFrame",
    "InMpegFrame",
    "InMpegAbs",
    "OutMsec",
    "OutFrame",
    "OutMpegFrame",
    "OutMpegAbs",
    "Kind",
    "Color",
    "ColorTableIndex",
    "ActiveLoop",
    "Comment",
    "BeatLoopSize",
    "CueMicrosec",
    "InPointSeekInfo",
    "OutPointSeekInfo",
    "rb_data_status",
    "rb_local_data_status",
    "rb_local_deleted",
    "rb_local_synced",
    "usn",
    "rb_local_usn",
    "created_at",
    "updated_at",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def decode_database_text(value: bytes) -> str | dict[str, str]:
    try:
        return value.decode("utf-8")
    except UnicodeDecodeError:
        return {"encoding": "invalid-utf8", "hex": value.hex()}


def row(connection, table: str, columns: tuple[str, ...], where: str, value: str):
    selected = ", ".join(columns)
    result = connection.execute(
        f"SELECT {selected} FROM {table} WHERE {where} = ?", (value,)
    ).fetchall()
    return [dict(zip(columns, values)) for values in result]


def snapshot(database: Path, options: Path) -> dict[str, object]:
    sidecars = {
        suffix.removeprefix("-"): {
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        }
        for suffix in ("-wal", "-shm")
        if (path := Path(f"{database}{suffix}")).exists()
    }
    connection = connect(database, key_from_options(options), readonly=True)
    connection.text_factory = decode_database_text
    integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
    memberships = row(
        connection,
        "djmdSongHotCueBanklist",
        MUTATION_COLUMNS,
        "HotCueBanklistID",
        BANK_ID,
    )
    cue_ids = [str(membership["CueID"]) for membership in memberships]
    cues = [
        cue
        for cue_id in cue_ids
        for cue in row(connection, "djmdCue", CUE_COLUMNS, "ID", cue_id)
    ]
    connection.close()

    return {
        "database_sha256": sha256(database),
        "sidecars": sidecars,
        "integrity": integrity,
        "bank_id": int(BANK_ID),
        "membership_count": len(memberships),
        "memberships": memberships,
        "cues": cues,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("database", type=Path)
    parser.add_argument("options", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(snapshot(args.database, args.options), indent=2) + "\n")
    print(args.output)


if __name__ == "__main__":
    main()
