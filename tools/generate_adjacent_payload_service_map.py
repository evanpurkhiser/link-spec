#!/usr/bin/env python3
"""Generate the static contract for Link Export artwork and analysis services."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DISPATCH = ROOT / "data/static-analysis/adjacent-link-export-dispatch.disasm.txt"
LOADERS = ROOT / "data/static-analysis/adjacent-payload-loaders.disasm.txt"
PARSER_LOADERS = (
    ROOT / "data/static-analysis/adjacent-payload-parser-loaders.disasm.txt"
)
VOCABULARY = ROOT / "data/static-analysis/link-export-request-vocabulary.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def service(
    kind: str,
    arguments: list[str],
    *,
    reply: str | None,
    target: str,
    database: str,
    filesystem: str | None,
    response: str,
    live_state: str = "declared",
    notes: list[str] | None = None,
) -> dict[str, object]:
    return {
        "kind": kind,
        "arguments": arguments,
        "reply_kind": reply,
        "target": target,
        "database": database,
        "filesystem": filesystem,
        "response": response,
        "live_state": live_state,
        "notes": notes or [],
    }


SERVICES = [
    service(
        "2003",
        ["packed-context", "image-id"],
        reply="4002",
        target="database-interface +0x190 (getDBImgData)",
        database=(
            "AppSync: select ImagePath from undeleted djmdContent by ID, then "
            "undeleted djmdPlaylist by ID; Master fallback: resolve djmdImage path by image ID"
        ),
        filesystem="JPEG file, at most 1 MiB, accepted by CheckImgSize_XYE",
        response="4002 binary reply; failures also emit an empty 4002 after an error",
        notes=[
            "track type 1 calls the database interface",
            "track types 3 and 4 return image error 1",
            "track type 2 and other non-1 types return image error 2",
        ],
    ),
    service(
        "2103",
        ["packed-context", "content-id"],
        reply="4002",
        target="database-interface +0x198 (getDBImgDataByContentID)",
        database=(
            "AppSync: thin call to the same ImagePath lookup using content ID; "
            "Master fallback: DsqlContent_GetImageID then djmdImage path"
        ),
        filesystem="same common JPEG loader as 2003",
        response="4002 binary reply; failures also emit an empty 4002 after an error",
        notes=["only track type 1 is accepted; every other type returns image error 3"],
    ),
    service(
        "2004",
        ["packed-context", "constant-4", "content-id", "zero", "declared-missing-blob"],
        reply="4402",
        target="PSvDBMain::GetWave",
        database="database-interface +0x180 analysis-path lookup by content ID",
        filesystem="sequential DAT PWAV/PWV2 readers in MstLoadLoudWave/MstLoadDotWave",
        response="fixed 904-byte payload: 800-byte loud preview plus 100-byte dot preview and framing",
        notes=["wire header declares five tags although the final zero-length blob is omitted"],
    ),
    service(
        "2104",
        ["packed-context", "content-id"],
        reply="4702",
        target="PSvDBMain::GetUsbCue",
        database="AppSync cue callback or undeleted djmdCue rows filtered by ContentID",
        filesystem=None,
        response="legacy fixed-width cue/loop blob with counts and auxiliary blob",
    ),
    service(
        "2204",
        ["packed-context", "content-id"],
        reply="4602",
        target="PSvDBMain::GetQtzInf",
        database="database-interface +0x180 analysis-path lookup by content ID",
        filesystem="DAT PQTZ through MstLoadBeatGrid and MstLoadBeatGridWithHeader",
        response="20-byte header plus 16 bytes per beat; more than 6,248 beats is rejected",
    ),
    service(
        "2304",
        ["packed-context"],
        reply=None,
        target="recognized log-only arm",
        database="none recovered",
        filesystem=None,
        response="logs the request and returns internal -2 without a payload builder",
        notes=["only the packed context track-type byte is read"],
    ),
    service(
        "2404",
        ["packed-context"],
        reply=None,
        target="recognized log-only arm",
        database="none recovered",
        filesystem=None,
        response="logs the request and returns internal -2 without a payload builder",
        notes=["only the packed context track-type byte is read"],
    ),
    service(
        "2504",
        ["packed-context", "content-id"],
        reply="4502",
        target="PSvDBMain::GetVbrInf",
        database="database-interface +0x180 analysis-path lookup by content ID",
        filesystem="DAT PVBR through MstLoadVBR",
        response="fixed 1,604-byte binary payload; failure emits an empty 4502",
    ),
    service(
        "2604",
        ["packed-context"],
        reply=None,
        target="recognized log-only arm",
        database="none recovered",
        filesystem=None,
        response="logs the request and returns internal -2 without a payload builder",
        notes=["only the packed context track-type byte is read"],
    ),
    service(
        "2704",
        ["packed-context"],
        reply=None,
        target="recognized log-only arm",
        database="none recovered",
        filesystem=None,
        response="logs the request and returns internal -2 without a payload builder",
        notes=["only the packed context track-type byte is read"],
    ),
    service(
        "2804",
        ["packed-context", "content-id"],
        reply="4000",
        target="PSvDBMain::GetQtzInf",
        database="same beat-grid analysis-path lookup as 2204",
        filesystem="same DAT PQTZ parser as 2204",
        response="single four-byte quantize value rather than the beat-grid blob",
    ),
    service(
        "2904",
        ["packed-context", "content-id", "zero"],
        reply="4a02",
        target="PSvDBMain::LoadParWav",
        database="database-interface +0x180 analysis-path lookup by content ID",
        filesystem="replace the analysis filename with its EXT sibling, then scan for PWV3",
        response="20-byte header plus one packed height/color byte per 1/150-second segment",
    ),
    service(
        "2a04",
        ["packed-context", "content-id"],
        reply="4c02",
        target="PSvDBMain::LoadKeyInf",
        database="database-interface +0x180 analysis-path lookup by content ID",
        filesystem="replace the analysis filename with its EXT sibling, then scan for PKEY",
        response="24-byte header plus 12 bytes per segmented-key entry",
    ),
    service(
        "2b04",
        ["packed-context", "content-id", "zero"],
        reply="4e02",
        target="PSvDBMain::GetUsbCueExt",
        database="AppSync callback or djmdCue plus cue-option lookups by ContentID",
        filesystem=None,
        response="variable-width extended cue records and entry count",
        notes=["a separate shared-content builder exists for callback-owned cue data"],
    ),
    service(
        "2c04",
        ["packed-context", "content-id", "atom-tag", "analysis-extension"],
        reply="4f02",
        target="PSvDBMain::GetSpecifiedAtomInfo",
        database="database-interface +0x180 analysis-path lookup by content ID",
        filesystem="replace analysis extension with uppercased EXT or 2EX, then MstLoadAtomInfo",
        response="concatenated length-prefixed matching atoms plus trailing numeric zero",
        notes=[
            "extensions other than EXT and 2EX return an empty 4f02",
            "PCP2, PCPT, and PMAI are explicitly short-circuited to an empty 4f02",
            "all other atom tags reach MstLoadAtomInfo",
        ],
    ),
    service(
        "2d04",
        ["packed-context", "content-id", "atom-tag", "analysis-extension"],
        reply="4f02",
        target="PSvDBMain::GetSpecifiedAtomInfo",
        database="same path as 2c04",
        filesystem="same path as 2c04",
        response="exact handler alias of 2c04 with the original request kind echoed",
        notes=[
            "extensions other than EXT and 2EX return an empty 4f02",
            "PCP2, PCPT, and PMAI are explicitly short-circuited to an empty 4f02",
            "all other atom tags reach MstLoadAtomInfo",
        ],
    ),
]


REQUIRED_NEEDLES = {
    DISPATCH: [
        "__ZN9PSvDBMain8OnImgCmdEP16_struct_dbsm_msg",
        "__ZN9PSvDBMain13OnSongAnlzCmdEP16_struct_dbsm_msg",
        "__ZN9PSvDBMain20GetSpecifiedAtomInfoEP16_struct_dbsm_msgPm",
        "cmp       r13, 0x1868",
        "mov       r14d, 0x2404",
        "mov       r14d, 0x2604",
        "mov       r14d, 0x2704",
        "mov       ebx, 0xfffffffe",
    ],
    LOADERS: [
        "select ImagePath from __TABLE_NAME__ where rb_local_deleted = 0 and ID = %lu",
        "'djmdContent'",
        "'djmdPlaylist'",
        "__Z22DsqlContent_GetImageID9RbDBIndexjPj",
        "__Z15DsqlImg_GetPath9RbDBIndexjPPt",
        "cmp       r14, 0x100001",
        "__ZN8analyzer15MstLoadZoomWave",
        "__ZN8analyzer19MstLoadSegmentedKey",
        "__ZN9PSvDBMain12GetUsbCueExt",
    ],
    PARSER_LOADERS: [
        "__ZN8analyzer15MstLoadLoudWave",
        "__ZN8analyzer14MstLoadDotWave",
        "__ZN8analyzer15MstLoadBeatGrid",
        "__ZN8analyzer10MstLoadVBR",
        "__ZN8analyzer15MstLoadZoomWave",
        "__ZN8analyzer19MstLoadSegmentedKey",
        "__ZN8analyzer25MstLoadBeatGridWithHeader",
        "__ZN8analyzer15MstLoadAtomInfo",
        "__ZN9PSvDBMain15CheckImgSize_XYE",
        "cmp       dword ptr [rcx + rdx], 0x33565750",
        "cmp       dword ptr [rcx + rdx], 0x59454b50",
        "cmp       esi, 0x320",
        "cmp       edx, 0x320",
    ],
}


def build() -> dict[str, object]:
    for path, needles in REQUIRED_NEEDLES.items():
        text = path.read_text()
        missing = [needle for needle in needles if needle not in text]
        if missing:
            raise SystemExit(f"{path}: missing static evidence: {missing}")

    vocabulary = json.loads(VOCABULARY.read_text())
    commands = {command["kind"].casefold(): command for command in vocabulary["commands"]}
    for entry in SERVICES:
        command = commands.get(entry["kind"])
        if command is None:
            raise SystemExit(f"vocabulary has no {entry['kind']}")
        vocabulary_reply = command["reply_kind"]
        service_reply = entry["reply_kind"]
        if (vocabulary_reply or "").casefold() != (service_reply or "").casefold():
            raise SystemExit(
                f"{entry['kind']}: reply mismatch: "
                f"{vocabulary_reply} != {service_reply}"
            )
        entry["name"] = command["name"]
        entry["coverage"] = command["coverage"]

    return {
        "format": 1,
        "rekordbox_version": "7.2.19",
        "scope": "server-side artwork and song-analysis request class",
        "evidence": {
            str(DISPATCH.relative_to(ROOT)): sha256(DISPATCH),
            str(LOADERS.relative_to(ROOT)): sha256(LOADERS),
            str(PARSER_LOADERS.relative_to(ROOT)): sha256(PARSER_LOADERS),
            str(VOCABULARY.relative_to(ROOT)): sha256(VOCABULARY),
        },
        "services": SERVICES,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data/static-analysis/adjacent-payload-services.json",
    )
    args = parser.parse_args()
    args.output.write_text(json.dumps(build(), indent=2) + "\n")


if __name__ == "__main__":
    main()
