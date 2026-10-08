#!/usr/bin/env python3
"""Decode Link Export switch tables from the pinned rekordbox Mach-O."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
BINARY = (
    ROOT.parent
    / "artifacts/rekordbox/7.2.19/extracted/app-root/rekordbox.app"
    / "Contents/MacOS/rekordbox"
)
OUTPUT = ROOT / "data/static-analysis/link-export-dispatch-tables.json"
BINARY_SHA256 = "07dcecbaf304f777e435539c83c7dcc02e41de1eaf2e0a75e8a9852e4411a244"
CPU_TYPE_X86_64 = 0x01000007
LC_SEGMENT_64 = 0x19


TABLES = (
    {
        "id": "list-low-byte",
        "owner": "PSvDBMain::OnListClientCmd",
        "address": 0x101D2BE98,
        "keys": list(range(0x18)),
        "labels": {
            0x00: "PSvDBMain::OnOtherListCmd",
            0x01: "PSvDBMain::OnGenreListCmd",
            0x02: "PSvDBMain::OnArtistListCmd",
            0x03: "PSvDBMain::OnAlbumListCmd",
            0x04: "PSvDBMain::OnTrackListCmd",
            0x05: "PSvDBMain::OnPlaylistListCmd",
            0x06: "PSvDBMain::OnBpmListCmd",
            0x07: "PSvDBMain::OnRatingListCmd",
            0x08: "PSvDBMain::OnYearListCmd",
            0x09: "unsupported-low-byte",
            0x0A: "PSvDBMain::OnLabelListCmd",
            0x0B: "PSvDBMain::OnKeyListCmd",
            0x0C: "special-0x130c-or-unsupported",
            0x0D: "PSvDBMain::OnColorListCmd",
            0x0E: "PSvDBMain::OnPlayCntListCmd",
            0x0F: "PSvDBMain::OnPrepareListCmd",
            0x10: "PSvDBMain::OnLengthListCmd",
            0x11: "PSvDBMain::OnBitrateListCmd",
            0x12: "PSvDBMain::OnHistoryListCmd",
            0x13: "PSvDBMain::OnFileNameListCmd",
            0x14: "PSvDBMain::OnNewKeyListCmd",
            0x15: "PSvDBMain::OnMyTagListCmd",
            0x16: "unsupported-low-byte",
            0x17: "PSvDBMain::OnMatchingListCmd",
        },
        "key_format": "low byte of request kind",
    },
    {
        "id": "analysis-class-low-byte",
        "owner": "PSvDBMain::OnMAnlzClientCmd",
        "address": 0x101D2E710,
        "keys": list(range(1, 8)),
        "labels": {
            0x01: "PSvDBMain::OnCueBnkCmd",
            0x02: "PSvDBMain::OnSongInfCmd",
            0x03: "PSvDBMain::OnImgCmd",
            0x04: "PSvDBMain::OnSongAnlzCmd",
            0x05: "PSvDBMain::OnWriteCmd",
            0x06: "unsupported-low-byte",
            0x07: "PSvDBMain::OnDbModCmd",
        },
        "key_format": "low byte of request kind",
    },
    {
        "id": "other-list-high-byte",
        "owner": "PSvDBMain::OnOtherListCmd",
        "address": 0x101D2E690,
        "keys": [0x1000 + index * 0x100 for index in range(6)],
        "labels": {
            0x1000: "root",
            0x1100: "unsupported-other-list-kind",
            0x1200: "track-content",
            0x1300: "search",
            0x1400: "sort-menu",
            0x1500: "search-track",
        },
        "key_format": "request kind after subtract-0x1000 and rotate-right-8",
    },
    {
        "id": "song-analysis-high-byte",
        "owner": "PSvDBMain::OnSongAnlzCmd",
        "address": 0x101D2F690,
        "keys": [0x2004 + index * 0x100 for index in range(14)],
        "labels": {
            0x2004: "PSvDBMain::GetWave",
            0x2104: "PSvDBMain::GetUsbCue",
            0x2204: "PSvDBMain::GetQtzInf",
            0x2304: "recognized-log-only",
            0x2404: "recognized-log-only",
            0x2504: "PSvDBMain::GetVbrInf",
            0x2604: "recognized-log-only",
            0x2704: "recognized-log-only",
            0x2804: "PSvDBMain::GetQtzInf",
            0x2904: "PSvDBMain::LoadParWav",
            0x2A04: "PSvDBMain::LoadKeyInf",
            0x2B04: "PSvDBMain::GetUsbCueExt",
            0x2C04: "PSvDBMain::GetSpecifiedAtomInfo",
            0x2D04: "PSvDBMain::GetSpecifiedAtomInfo",
        },
        "key_format": "request kind after subtract-0x2004 and rotate-right-8",
    },
    {
        "id": "year-high-byte",
        "owner": "PSvDBMain::OnYearListCmd",
        "address": 0x101D2D020,
        "keys": [0x1008 + index * 0x100 for index in range(11)],
        "labels": {
            0x1008: "database-interface release-decade root via vtable +0xA0",
            0x1108: "database-interface release-year children via vtable +0xA8",
            0x1208: "database-interface release-year tracks via vtable +0xB0",
            0x1308: "unsupported-year-kind",
            0x1408: "unsupported-year-kind",
            0x1508: "unsupported-year-kind",
            0x1608: "unsupported-year-kind",
            0x1708: "database-interface date-added hierarchy via vtable +0xB8",
            0x1808: "database-interface date-added hierarchy via vtable +0xB8",
            0x1908: "database-interface date-added hierarchy via vtable +0xB8",
            0x1A08: "database-interface date-added tracks via vtable +0xC0",
        },
        "key_format": "request kind after subtract-0x1008 and rotate-right-8",
    },
    {
        "id": "other-client-low-byte",
        "owner": "PSvDBMain::OnOtherClientCmd",
        "address": 0x101D2FE90,
        "keys": list(range(9)),
        "labels": {
            0x00: "PSvDBMain::OnListBuffCmd",
            0x01: "PSvDBMain::OnHistoryCmd",
            0x02: "PSvDBMain::OnPrepareCmd",
            0x03: "PSvDBMain::OnOtherCmd",
            0x04: "special-0x3104-only",
            0x05: "unsupported-low-byte",
            0x06: "PSvDBMain::OnUserCmd",
            0x07: "PSvDBMain::OnFilterCmd",
            0x08: "PSvDBMain::OnOther2Cmd",
        },
        "key_format": "low byte of 3xxx request kind",
    },
    {
        "id": "history-high-byte",
        "owner": "PSvDBMain::OnHistoryCmd",
        "address": 0x101D30314,
        "keys": [0x3001 + index * 0x100 for index in range(5)],
        "labels": {
            0x3001: "insert-history",
            0x3101: "delete-history",
            0x3201: "set-onair",
            0x3301: "delete-history-reply",
            0x3401: "delete-history-track",
        },
        "key_format": "request kind after subtract-0x3001 and rotate-right-8",
    },
    {
        "id": "prepare-high-byte",
        "owner": "PSvDBMain::OnPrepareCmd",
        "address": 0x101D30654,
        "keys": [0x3002 + index * 0x100 for index in range(5)],
        "labels": {
            0x3002: "add-prepare",
            0x3102: "add-taglist-playlist",
            0x3202: "unlisted-static-arm",
            0x3302: "change-taglist-order",
            0x3402: "is-taglist-playlist",
        },
        "key_format": "request kind after subtract-0x3002 and rotate-right-8",
    },
    {
        "id": "other-command-high-byte",
        "owner": "PSvDBMain::OnOtherCmd",
        "address": 0x101D30AD8,
        "keys": [0x3003 + index * 0x100 for index in range(14)],
        "labels": {
            0x3003: "color-code",
            0x3103: "unlisted-static-arm",
            0x3203: "get-db-firmware-version",
            0x3303: "get-browse-type",
            0x3403: "unlisted-static-arm",
            0x3503: "info-unplayable",
            0x3603: "get-db-hierarchy",
            0x3703: "unlisted-static-arm",
            0x3803: "unlisted-static-arm",
            0x3903: "property-table",
            0x3A03: "translate-new-key",
            0x3B03: "get-play-state",
            0x3C03: "set-my-setting-flag",
            0x3D03: "get-new-key-id",
        },
        "key_format": "request kind after subtract-0x3003 and rotate-right-8",
    },
    {
        "id": "filter-high-byte",
        "owner": "PSvDBMain::OnFilterCmd",
        "address": 0x101D30E5C,
        "keys": [0x3007 + index * 0x100 for index in range(5)],
        "labels": {
            0x3007: "set-filter-onoff",
            0x3107: "get-filter-condition-property",
            0x3207: "set-filter-condition-property",
            0x3307: "set-filter-condition-mytag",
            0x3407: "add-filter-mytag-item",
        },
        "key_format": "request kind after subtract-0x3007 and rotate-right-8",
    },
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def x86_slice(data: bytes) -> tuple[int, bytes]:
    if data[:4] != b"\xca\xfe\xba\xbe":
        raise ValueError("expected a big-endian universal Mach-O")

    architecture_count = struct.unpack_from(">I", data, 4)[0]
    for index in range(architecture_count):
        offset = 8 + index * 20
        cpu_type, _, slice_offset, slice_size, _ = struct.unpack_from(">IIIII", data, offset)
        if cpu_type == CPU_TYPE_X86_64:
            return slice_offset, data[slice_offset : slice_offset + slice_size]

    raise ValueError("universal binary has no x86-64 slice")


def segments(slice_data: bytes) -> list[dict[str, int | str]]:
    magic, _, _, _, command_count, _, _, _ = struct.unpack_from("<IiiIIIII", slice_data, 0)
    if magic != 0xFEEDFACF:
        raise ValueError("expected a little-endian 64-bit Mach-O slice")

    result = []
    cursor = 32
    for _ in range(command_count):
        command, command_size = struct.unpack_from("<II", slice_data, cursor)
        if command == LC_SEGMENT_64:
            fields = struct.unpack_from("<II16sQQQQiiII", slice_data, cursor)
            result.append(
                {
                    "name": fields[2].split(b"\0", 1)[0].decode("ascii"),
                    "virtual_address": fields[3],
                    "virtual_size": fields[4],
                    "file_offset": fields[5],
                    "file_size": fields[6],
                }
            )
        cursor += command_size

    return result


def content_at(
    slice_data: bytes,
    mapped_segments: list[dict[str, int | str]],
    address: int,
    size: int,
) -> bytes:
    for segment in mapped_segments:
        virtual_address = int(segment["virtual_address"])
        file_size = int(segment["file_size"])
        if virtual_address <= address and address + size <= virtual_address + file_size:
            offset = int(segment["file_offset"]) + address - virtual_address
            return slice_data[offset : offset + size]

    raise ValueError(f"address range {address:#x}+{size:#x} is not file-backed")


def decode_table(
    slice_data: bytes,
    mapped_segments: list[dict[str, int | str]],
    spec: dict[str, object],
) -> dict[str, object]:
    address = int(spec["address"])
    keys = list(spec["keys"])
    labels = dict(spec["labels"])
    raw = content_at(slice_data, mapped_segments, address, len(keys) * 4)
    relative_targets = [value[0] for value in struct.iter_unpack("<i", raw)]

    entries = []
    for key, relative_target in zip(keys, relative_targets, strict=True):
        entries.append(
            {
                "key": f"{key:04X}" if key > 0xFF else f"{key:02X}",
                "relative_target": relative_target,
                "target_address": f"0x{address + relative_target:09x}",
                "target": labels[key],
            }
        )

    return {
        "id": spec["id"],
        "owner": spec["owner"],
        "table_address": f"0x{address:09x}",
        "key_format": spec["key_format"],
        "raw_sha256": sha256(raw),
        "entries": entries,
    }


def build(binary_path: Path) -> dict[str, object]:
    binary_data = binary_path.read_bytes()
    actual_sha256 = sha256(binary_data)
    if actual_sha256 != BINARY_SHA256:
        raise ValueError(
            f"rekordbox binary SHA-256 {actual_sha256} does not match {BINARY_SHA256}"
        )

    slice_offset, slice_data = x86_slice(binary_data)
    mapped_segments = segments(slice_data)
    return {
        "format": 1,
        "source": {
            "product": "rekordbox 7.2.19",
            "path": str(binary_path.resolve()),
            "sha256": actual_sha256,
            "slice": "x86-64",
            "slice_file_offset": slice_offset,
        },
        "top_level": {
            "owner": "PSvDBMain::OnClientReq",
            "key_format": "signed request kind shifted right by 12",
            "accepted_classes": {
                "1": "PSvDBMain::OnListClientCmd",
                "2": "PSvDBMain::OnMAnlzClientCmd",
                "3": "PSvDBMain::OnOtherClientCmd",
            },
            "default_target": "PSvDBMain::OnUnknownClientCmd",
            "default_reply_kind": "4003",
        },
        "tables": [decode_table(slice_data, mapped_segments, spec) for spec in TABLES],
        "direct_dispatch": [
            {
                "owner": "PSvDBMain::OnKeyListCmd",
                "request_kind": "100B",
                "target": "PSvAppSyncDBIF::getKey_Root via database-interface vtable +0xE8",
                "reply_kind": "4000",
            },
            {
                "owner": "PSvDBMain::OnKeyListCmd",
                "request_kind": "110B",
                "target": "PSvAppSyncDBIF::getTrack_Key via database-interface vtable +0xF0",
                "reply_kind": "4000",
            },
            {
                "owner": "PSvDBMain::OnListClientCmd",
                "request_kind": "130C",
                "target": "recognized-log-only",
                "reply_kind": None,
            },
            {
                "owner": "PSvDBMain::OnImgCmd",
                "request_kind": "2003",
                "target": "database-interface vtable +0x190",
                "reply_kind": "4002",
            },
            {
                "owner": "PSvDBMain::OnImgCmd",
                "request_kind": "2103",
                "target": "database-interface vtable +0x198",
                "reply_kind": "4002",
            },
            {
                "owner": "PSvDBMain::OnListBuffCmd",
                "request_kind": "3000",
                "target": "PSvDBMain::GetListBufContents",
                "reply_kind": "4001/4101/4201",
            },
            {
                "owner": "PSvDBMain::OnListBuffCmd",
                "request_kind": "3100",
                "target": "PSvDBMain::GetListBufOffset",
                "reply_kind": "4000",
            },
            {
                "owner": "PSvDBMain::OnOtherClientCmd",
                "request_kind": "3104",
                "target": "recognized zero-result special case",
                "reply_kind": "4000",
            },
            {
                "owner": "PSvDBMain::OnUserCmd",
                "request_kind": "3006",
                "target": "PSvDBMain::GetDJID",
                "reply_kind": "4D02",
            },
            {
                "owner": "PSvDBMain::OnOther2Cmd",
                "request_kind": "3008",
                "target": "database-interface vtable +0x228",
                "reply_kind": "4000",
            },
            {
                "owner": "PSvDBMain::OnWriteCmd",
                "request_kind": "2005",
                "target": "PSvDBMain::SavWave",
                "reply_kind": None,
            },
            {
                "owner": "PSvDBMain::OnWriteCmd",
                "request_kind": "2105",
                "target": "PSvDBMain::SavUsbCue",
                "reply_kind": "4702",
            },
            {
                "owner": "PSvDBMain::OnWriteCmd",
                "request_kind": "2205",
                "target": "PSvDBMain::SavVbrInf (constant-success stub)",
                "reply_kind": None,
            },
            {
                "owner": "PSvDBMain::OnWriteCmd",
                "request_kind": "2305",
                "target": "recognized-log-only",
                "reply_kind": None,
            },
            {
                "owner": "PSvDBMain::OnWriteCmd",
                "request_kind": "2405",
                "target": "recognized-log-only",
                "reply_kind": None,
            },
            {
                "owner": "PSvDBMain::OnWriteCmd",
                "request_kind": "2505",
                "target": "recognized-log-only",
                "reply_kind": None,
            },
            {
                "owner": "PSvDBMain::OnWriteCmd",
                "request_kind": "2605",
                "target": "PSvDBMain::SavQtzOfs",
                "reply_kind": "4000",
            },
            {
                "owner": "PSvDBMain::OnWriteCmd",
                "request_kind": "2705",
                "target": "PSvDBMain::SavUsbCueExt",
                "reply_kind": "4E02",
            },
            {
                "owner": "PSvDBMain::OnWriteCmd",
                "request_kind": "2805",
                "target": "PSvDBMain::SaveSpecifiedAtomInfo",
                "reply_kind": "4000",
            },
            {
                "owner": "PSvDBMain::OnWriteCmd",
                "request_kind": "2905",
                "target": "PSvDBMain::UpdateSpecifiedAtomInfo",
                "reply_kind": "4000",
            },
            {
                "owner": "PSvDBMain::OnDbModCmd",
                "request_kind": "2107",
                "target": "PSvAppSyncDBIF::modTrackRate via database-interface vtable +0x2A0",
                "reply_kind": "4000",
            },
            {
                "owner": "PSvDBMain::OnDbModCmd",
                "request_kind": "2507",
                "target": "PSvAppSyncDBIF::modTrackBPM via database-interface vtable +0x2A8",
                "reply_kind": "4000",
            },
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--binary", type=Path, default=BINARY)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()

    document = build(args.binary)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(document, indent=2) + "\n")


if __name__ == "__main__":
    main()
