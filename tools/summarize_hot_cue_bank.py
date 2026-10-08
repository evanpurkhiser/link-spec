#!/usr/bin/env python3
"""Validate and summarize the canonical Hot Cue Bank oracle."""

from __future__ import annotations

import json
import struct
from pathlib import Path

from summarize_search_oracle import load, sha256, validate


ROOT = Path(__file__).resolve().parent.parent
CONFORMANCE = ROOT / "conformance"
GOLDENS = CONFORMANCE / "goldens/rekordbox-7.2.19/xdj-rx3"
DISCOVERY_SUITE = CONFORMANCE / "suites/hot-cue-bank-discovery.json"
DISCOVERY_GOLDEN = GOLDENS / "hot-cue-bank-discovery.json"
FULL_MANIFEST = CONFORMANCE / "fixtures/generated/full/manifest.json"
MATRIX_SUITE = CONFORMANCE / "suites/hot-cue-bank-matrix.json"
MATRIX_GOLDEN = GOLDENS / "hot-cue-bank-matrix.json"
MATRIX_MANIFEST = CONFORMANCE / "fixtures/generated/hot-cue-banks/manifest.json"
LOCATION_RENDER_SUITE = CONFORMANCE / "suites/hot-cue-bank-location-renders.json"
LOCATION_RENDER_GOLDEN = GOLDENS / "hot-cue-bank-location-renders.json"
LOCATION_RENDER_EVIDENCE = ROOT / "data/experiments/hot-cue-bank/location-renders"
LOCATION_CROSS_SUITE = CONFORMANCE / "suites/hot-cue-bank-location-cross.json"
LOCATION_CROSS_GOLDEN = GOLDENS / "hot-cue-bank-location-cross.json"
LOCATION_CROSS_EVIDENCE = ROOT / "data/experiments/hot-cue-bank/location-cross"
LOCATION_STATE_SUITE = CONFORMANCE / "suites/hot-cue-bank-location-state.json"
LOCATION_STATE_GOLDEN = GOLDENS / "hot-cue-bank-location-state.json"
LOCATION_STATE_EVIDENCE = ROOT / "data/experiments/hot-cue-bank/location-state"
COUNT_BOUNDARY_SUITE = CONFORMANCE / "suites/hot-cue-bank-count-boundaries.json"
COUNT_BOUNDARY_GOLDEN = GOLDENS / "hot-cue-bank-count-boundaries.json"
COUNT_HAZARD_PROBES = {
    "int32-max": 2_147_483_647,
    "high-bit": 2_147_483_648,
    "uint32-max": 4_294_967_295,
}
COUNT_HAZARD_EVIDENCE = ROOT / "data/experiments/hot-cue-bank/count-hazards"
CUE_SUITE = CONFORMANCE / "suites/hot-cue-bank-cues.json"
CUE_GOLDEN = GOLDENS / "hot-cue-bank-cues.json"
CUE_STATUS_GOLDEN = GOLDENS / "hot-cue-bank-cues-status.json"
CUE_LEGACY_SUITE = CONFORMANCE / "suites/hot-cue-bank-cues-legacy.json"
CUE_LEGACY_GOLDEN = GOLDENS / "hot-cue-bank-cues-legacy.json"
CUE_SEQUENCE_SUITE = CONFORMANCE / "suites/hot-cue-bank-cues-sequence.json"
CUE_SEQUENCE_GOLDEN = GOLDENS / "hot-cue-bank-cues-sequence.json"
CUE_FIELDS_SUITE = CONFORMANCE / "suites/hot-cue-bank-cue-fields.json"
CUE_FIELDS_GOLDEN = GOLDENS / "hot-cue-bank-cue-fields.json"
CUE_FIELDS_MANIFEST = (
    CONFORMANCE / "fixtures/generated/hot-cue-bank-cue-fields/manifest.json"
)
EXTENDED_CUE_SUITE = CONFORMANCE / "suites/hot-cue-bank-cues-extended.json"
EXTENDED_CUE_GOLDEN = GOLDENS / "hot-cue-bank-cues-extended.json"
EXTENDED_FIELDS_SUITE = CONFORMANCE / "suites/hot-cue-bank-extended-fields.json"
EXTENDED_FIELDS_GOLDEN = GOLDENS / "hot-cue-bank-extended-fields.json"
EXTENDED_FIELDS_MANIFEST = (
    CONFORMANCE / "fixtures/generated/hot-cue-bank-extended-fields/manifest.json"
)
SET_EXTENDED_SUITE = CONFORMANCE / "suites/hot-cue-bank-set-extended.json"
SET_EXTENDED_GOLDEN = GOLDENS / "hot-cue-bank-set-extended.json"
SET_EXTENDED_MANIFEST = (
    CONFORMANCE
    / "fixtures/generated/hot-cue-bank-mutation-duplicate-slot/manifest.json"
)
SET_EXTENDED_EVIDENCE = ROOT / "data/experiments/hot-cue-bank/set-extended"
SET_EXTENDED_LIVE = SET_EXTENDED_EVIDENCE / "live-after.json"
SET_EXTENDED_STOPPED = SET_EXTENDED_EVIDENCE / "success-after.json"
SET_EXTENDED_REJECTED = SET_EXTENDED_EVIDENCE / "rejected-wire.json"
SET_EXTENDED_ALIGNED_REJECTED = (
    SET_EXTENDED_EVIDENCE / "aligned-rejected-wire.json"
)
SET_LEGACY_SUITE = CONFORMANCE / "suites/hot-cue-bank-legacy-track-cues.json"
SET_LEGACY_GOLDEN = GOLDENS / "hot-cue-bank-legacy-track-cues.json"
SET_LEGACY_MANIFEST = (
    CONFORMANCE / "fixtures/generated/hot-cue-bank-legacy-mutation/manifest.json"
)
SET_LEGACY_EVIDENCE = ROOT / "data/experiments/hot-cue-bank/legacy-setter"
SET_LEGACY_LIVE = SET_LEGACY_EVIDENCE / "live-after.json"
SET_LEGACY_SLOT_ONE_NEGATIVE = SET_LEGACY_EVIDENCE / "slot1-negative.json"
LEGACY_ORDINAL_SUITE = CONFORMANCE / "suites/hot-cue-bank-legacy-ordinals.json"
LEGACY_ORDINAL_GOLDEN = GOLDENS / "hot-cue-bank-legacy-ordinals.json"
LEGACY_ORDINAL_MANIFEST = (
    CONFORMANCE / "fixtures/generated/hot-cue-bank-legacy-ordinals/manifest.json"
)
LEGACY_ORDINAL_LIVE = (
    ROOT / "data/experiments/hot-cue-bank/legacy-ordinals/live-after.json"
)
LEGACY_ORDINAL_BOUNDARY_SUITE = (
    CONFORMANCE / "suites/hot-cue-bank-legacy-ordinal-boundaries.json"
)
LEGACY_ORDINAL_BOUNDARY_GOLDEN = (
    GOLDENS / "hot-cue-bank-legacy-ordinal-boundaries.json"
)
LEGACY_ORDINAL_BOUNDARY_MANIFEST = (
    CONFORMANCE
    / "fixtures/generated/hot-cue-bank-legacy-ordinal-boundaries/manifest.json"
)
LEGACY_ORDINAL_BOUNDARY_LIVE = (
    ROOT
    / "data/experiments/hot-cue-bank/legacy-ordinal-boundaries/live-after.json"
)
DELETED_BANK_MEMBER_SUITE = (
    CONFORMANCE / "suites/hot-cue-bank-deleted-bank-member.json"
)
DELETED_BANK_MEMBER_GOLDEN = GOLDENS / "hot-cue-bank-deleted-bank-member.json"
DELETED_BANK_MEMBER_MANIFEST = (
    CONFORMANCE
    / "fixtures/generated/hot-cue-bank-deleted-bank-member/manifest.json"
)
IN_SEEK_CRASH = ROOT / "data/experiments/hot-cue-bank/in-seek-crash.json"
OUT_SEEK_CAPTURE = ROOT / "data/experiments/hot-cue-bank/out-seek-control.json"
CUE_RR_GOLDEN = (
    CONFORMANCE
    / "goldens/rekordbox-7.2.19/xdj-rr/hot-cue-bank-cues-status.json"
)
STATIC = ROOT / "data/static-analysis/hot-cue-bank.disasm.txt"
MEMBERSHIP_RESOLVER_STATIC = (
    ROOT / "data/static-analysis/hot-cue-bank-membership-resolver.disasm.txt"
)
LEGACY_SETTER_STATIC = (
    ROOT / "data/static-analysis/hot-cue-bank-legacy-setter.disasm.txt"
)


def row_values(case: dict[str, object]) -> list[list[object]]:
    return [
        [argument["value"] for argument in row["arguments"]]
        for row in case["rows"]
    ]


def content_positions(case: dict[str, object]) -> list[tuple[int, int]]:
    return [(int(row[1]), int(row[9])) for row in row_values(case)]


def cue_reply(
    case: dict[str, object], request_kind: int = 0x2101
) -> tuple[list[object], list[tuple[int, ...]], list[tuple[int, int]]]:
    assert case["outcome"] == "raw_reply"
    response = case["raw_response"]
    assert response["error_kind"] is None
    assert len(response["messages"]) == 1
    message = response["messages"][0]
    assert message["kind"] == 0x4702

    arguments = message["arguments"]
    values = [argument.get("value") for argument in arguments]
    cue_blob = bytes.fromhex(arguments[3]["hex"])
    extension_blob = bytes.fromhex(arguments[8]["hex"])
    assert values == [request_kind, 0, len(cue_blob), None, 36, len(cue_blob) // 36, 0, len(extension_blob), None]
    assert len(cue_blob) % 36 == 0
    assert len(extension_blob) == len(cue_blob) // 36 * 8

    records = [
        struct.unpack("<9I", cue_blob[offset : offset + 36])
        for offset in range(0, len(cue_blob), 36)
    ]
    extensions = [
        struct.unpack("<II", extension_blob[offset : offset + 8])
        for offset in range(0, len(extension_blob), 8)
    ]
    return values, records, extensions


def cue_message(case: dict[str, object]) -> dict[str, object]:
    cue_reply(case)
    return case["raw_response"]["messages"][0]


def new_cue_records(
    case: dict[str, object], request_kind: int = 0x2301
) -> list[dict[str, object]]:
    assert case["outcome"] == "raw_reply"
    response = case["raw_response"]
    assert response["error_kind"] is None
    assert len(response["messages"]) == 1
    message = response["messages"][0]
    assert message["kind"] == 0x4E02

    arguments = message["arguments"]
    blob = bytes.fromhex(arguments[3]["hex"])
    values = [argument.get("value") for argument in arguments]
    assert values[0] == request_kind
    assert values[1] == int(not blob)
    assert values[2] == len(blob)
    assert values[3] is None

    records = []
    offset = 0
    while offset < len(blob):
        size = struct.unpack_from("<I", blob, offset)[0]
        assert size >= 56
        record = blob[offset : offset + size]
        assert len(record) == size
        option_bytes = struct.unpack_from("<I", record, 52)[0]
        assert size == (56 + option_bytes + 3) & ~3

        comment_bytes = struct.unpack_from("<H", record, 72)[0]
        comment_data = record[74 : 74 + comment_bytes]
        comment = comment_data.decode("utf-16-le").rstrip("\0")
        seek_offset = 74 + comment_bytes
        seek = (0, 0, 0, 0, 0, 0)
        if option_bytes > 18 + comment_bytes:
            assert struct.unpack_from("<Q", record, seek_offset)[0] == 44
            seek = struct.unpack_from(">QQQQII", record, seek_offset + 8)

        records.append(
            {
                "size": size,
                "slot": struct.unpack_from("<H", record, 4)[0],
                "cue_type": record[6],
                "time_unit": struct.unpack_from("<H", record, 10)[0],
                "in_msec": struct.unpack_from("<i", record, 12)[0],
                "out_msec": struct.unpack_from("<i", record, 16)[0],
                "marker": struct.unpack_from("<I", record, 24)[0],
                "sentinel": struct.unpack_from("<i", record, 32)[0],
                "in_mpeg_frame": struct.unpack_from("<i", record, 36)[0],
                "out_mpeg_frame": struct.unpack_from("<i", record, 40)[0],
                "in_mpeg_abs": struct.unpack_from("<i", record, 44)[0],
                "out_mpeg_abs": struct.unpack_from("<i", record, 48)[0],
                "option_bytes": option_bytes,
                "color_plus_one": record[58],
                "cue_microsec": struct.unpack_from("<I", record, 60)[0],
                "beat_loop_words": struct.unpack_from("<HH", record, 66),
                "comment_bytes": comment_bytes,
                "comment": comment,
                "seek": seek,
            }
        )
        offset += size

    assert offset == len(blob)
    assert len(records) == values[4]
    return records


def cases(document: dict[str, object]) -> dict[str, dict[str, object]]:
    return {case["id"]: case for case in document["behavior"]["cases"]}


def reply_values(case: dict[str, object]) -> list[object]:
    message = case["raw_response"]["messages"][0]
    return [argument.get("value") for argument in message["arguments"]]


def main() -> None:
    discovery = validate(DISCOVERY_SUITE, DISCOVERY_GOLDEN, FULL_MANIFEST)
    matrix = validate(MATRIX_SUITE, MATRIX_GOLDEN, MATRIX_MANIFEST)
    location_renders = validate(
        LOCATION_RENDER_SUITE, LOCATION_RENDER_GOLDEN, MATRIX_MANIFEST
    )
    location_cross = validate(
        LOCATION_CROSS_SUITE, LOCATION_CROSS_GOLDEN, MATRIX_MANIFEST
    )
    location_state = validate(
        LOCATION_STATE_SUITE, LOCATION_STATE_GOLDEN, MATRIX_MANIFEST
    )
    count_boundaries = validate(
        COUNT_BOUNDARY_SUITE, COUNT_BOUNDARY_GOLDEN, MATRIX_MANIFEST
    )
    count_hazards = {
        name: validate(
            CONFORMANCE / f"suites/hot-cue-bank-count-{name}.json",
            GOLDENS / f"hot-cue-bank-count-{name}.json",
            MATRIX_MANIFEST,
        )
        for name in COUNT_HAZARD_PROBES
    }
    cues = validate(CUE_SUITE, CUE_GOLDEN, MATRIX_MANIFEST)
    cues_status = validate(CUE_SUITE, CUE_STATUS_GOLDEN, MATRIX_MANIFEST)
    cues_rr = validate(CUE_SUITE, CUE_RR_GOLDEN, MATRIX_MANIFEST)
    cues_legacy = validate(CUE_LEGACY_SUITE, CUE_LEGACY_GOLDEN, MATRIX_MANIFEST)
    cues_sequence = validate(
        CUE_SEQUENCE_SUITE, CUE_SEQUENCE_GOLDEN, MATRIX_MANIFEST
    )
    cue_fields = validate(CUE_FIELDS_SUITE, CUE_FIELDS_GOLDEN, CUE_FIELDS_MANIFEST)
    extended_cues = validate(
        EXTENDED_CUE_SUITE, EXTENDED_CUE_GOLDEN, MATRIX_MANIFEST
    )
    extended_fields = validate(
        EXTENDED_FIELDS_SUITE, EXTENDED_FIELDS_GOLDEN, EXTENDED_FIELDS_MANIFEST
    )
    set_extended = validate(
        SET_EXTENDED_SUITE, SET_EXTENDED_GOLDEN, SET_EXTENDED_MANIFEST
    )
    set_legacy = validate(
        SET_LEGACY_SUITE, SET_LEGACY_GOLDEN, SET_LEGACY_MANIFEST
    )
    legacy_ordinals = validate(
        LEGACY_ORDINAL_SUITE, LEGACY_ORDINAL_GOLDEN, LEGACY_ORDINAL_MANIFEST
    )
    legacy_ordinal_boundaries = validate(
        LEGACY_ORDINAL_BOUNDARY_SUITE,
        LEGACY_ORDINAL_BOUNDARY_GOLDEN,
        LEGACY_ORDINAL_BOUNDARY_MANIFEST,
    )
    deleted_bank_member = validate(
        DELETED_BANK_MEMBER_SUITE,
        DELETED_BANK_MEMBER_GOLDEN,
        DELETED_BANK_MEMBER_MANIFEST,
    )
    assert len(discovery) == 11
    assert len(matrix) == 31
    assert len(location_renders) == 10
    assert len(location_cross) == 32
    assert len(location_state) == 8
    assert len(count_boundaries) == 6
    assert all(len(cases) == 1 for cases in count_hazards.values())
    assert len(cues) == 10
    assert len(cues_status) == 10
    assert len(cues_rr) == 10
    assert len(cues_legacy) == 3
    assert len(cues_sequence) == 3
    assert len(cue_fields) == 4
    assert len(extended_cues) == 9
    assert len(extended_fields) == 8
    assert len(set_extended) == 3
    assert len(set_legacy) == 3
    assert len(legacy_ordinals) == 3
    assert len(legacy_ordinal_boundaries) == 11
    assert len(deleted_bank_member) == 4

    expected_counts = {
        "alpha-bank": 3,
        "root-bank": 2,
        "empty-bank": 0,
        "folder-selector": 0,
        "deleted-bank": 0,
        "root-selector-zero": 0,
        "unknown-selector": 0,
        "alpha-bank-fixed-tags": 3,
        "empty-bank-fixed-tags": 0,
        "unknown-selector-fixed-tags": 0,
    }
    for capture in (cues, cues_status, cues_rr):
        for case_id, case in capture.items():
            _, records, _ = cue_reply(case)
            assert len(records) == expected_counts[case_id]
    for case_id, case in cues_legacy.items():
        _, records, _ = cue_reply(case)
        assert len(records) == expected_counts[case_id]

    _, alpha_records, alpha_extensions = cue_reply(cues["alpha-bank"])
    _, root_records, root_extensions = cue_reply(cues["root-bank"])
    assert [record[1] for record in alpha_records] == [10008, 10001, 10006]
    assert [record[0] >> 16 for record in alpha_records] == [4, 5, 6]
    assert [record[1] for record in root_records] == [10002, 10001]
    assert [record[0] >> 16 for record in root_records] == [4, 5]

    for case_id in cues:
        assert cue_message(cues_status[case_id]) == cue_message(cues[case_id])
        assert cue_message(cues_rr[case_id]) == cue_message(cues[case_id])
    for case_id in cues_legacy:
        assert cue_message(cues_legacy[case_id]) == cue_message(cues[case_id])
    assert cue_message(cues["alpha-bank-fixed-tags"]) == cue_message(cues["alpha-bank"])
    assert cue_message(cues["empty-bank-fixed-tags"]) == cue_message(cues["empty-bank"])
    assert cue_message(cues["unknown-selector-fixed-tags"]) == cue_message(cues["unknown-selector"])
    assert cues_sequence["tree-root"]["total"] == 3
    assert cues_sequence["alpha-bank-tracks"]["total"] == 10
    assert cue_message(cues_sequence["alpha-bank-cues"]) == cue_message(cues["alpha-bank"])

    field_values, field_records, field_extensions = cue_reply(cue_fields["wire-fields"])
    assert field_values[5] == 3
    assert field_records == [
        (0x00040100, 10001, 0, 150, 0, 111113, 111114, 111115, 111116),
        (0x00050101, 10002, 0, 300, 599, 222213, 222214, 222215, 222216),
        (0x00060101, 10003, 0, 450, 0, 333313, 333314, 333315, 333316),
    ]
    assert field_extensions == [(1001, 0xFFFFFFFF), (2002, 4004), (3003, 1)]
    for case_id in ("ignored-fields", "wire-fields-fixed-tags", "ignored-fields-fixed-tags"):
        assert cue_message(cue_fields[case_id]) == cue_message(cue_fields["wire-fields"])

    extended_counts = {
        "count-zero": 0,
        "count-one": 1,
        "count-two": 2,
        "count-three": 3,
        "count-four": 4,
        "count-eight": 8,
        "count-three-fixed-tags": 3,
        "folder-selector": 0,
        "unknown-selector": 0,
    }
    for case_id, expected in extended_counts.items():
        assert len(new_cue_records(extended_cues[case_id])) == expected
    assert (
        extended_cues["count-three"]["raw_response"]["messages"]
        == extended_cues["count-three-fixed-tags"]["raw_response"]["messages"]
    )

    extended_records = {
        case_id: new_cue_records(case)[0]
        for case_id, case in extended_fields.items()
    }
    assert extended_records["baseline"]["size"] == 124
    assert extended_records["baseline"]["in_msec"] == 100_001
    assert extended_records["timing"]["size"] == 124
    assert extended_records["timing"]["cue_type"] == 1
    assert extended_records["timing"]["out_msec"] == -1
    assert [
        extended_records["timing"][name]
        for name in (
            "in_mpeg_frame",
            "out_mpeg_frame",
            "in_mpeg_abs",
            "out_mpeg_abs",
        )
    ] == [0x01020304, 0x21222324, 0x11121314, 0x31323334]
    assert extended_records["color"]["color_plus_one"] == 8
    assert extended_records["comment-ascii"]["comment"] == "A"
    assert extended_records["comment-ascii"]["comment_bytes"] == 4
    assert extended_records["comment-unicode"]["comment"] == "\u00e9\U0001f642"
    assert extended_records["comment-unicode"]["comment_bytes"] == 8
    assert extended_records["beat-loop"]["beat_loop_words"] == (0x1234, 0x5678)
    assert extended_records["microseconds"]["cue_microsec"] == 0x0A0B0C0D
    assert extended_records["out-seek"]["seek"] == (0, 0, 0, 0, 0, 0)

    mutation_before = new_cue_records(set_extended["before"])[0]
    mutation_set = new_cue_records(set_extended["set"], 0x2401)[0]
    mutation_after = new_cue_records(set_extended["after"])[0]
    assert mutation_before["in_msec"] == 100_001
    assert mutation_set == mutation_after
    assert mutation_set == {
        "size": 124,
        "slot": 1,
        "cue_type": 2,
        "time_unit": 1000,
        "in_msec": 456_789,
        "out_msec": 567_890,
        "marker": 8,
        "sentinel": -1,
        "in_mpeg_frame": 0x01020304,
        "out_mpeg_frame": 0x11121314,
        "in_mpeg_abs": 0x21222324,
        "out_mpeg_abs": 0x31323334,
        "option_bytes": 66,
        "color_plus_one": 6,
        "cue_microsec": 0x0A0B0C0D,
        "beat_loop_words": (0x1234, 0x5678),
        "comment_bytes": 0,
        "comment": "",
        "seek": (0, 0, 0, 0, 0, 0),
    }
    assert reply_values(set_extended["set"]) == [0x2401, 0, 124, None, 1]

    legacy_success = set_legacy["known-content-canonical-bank"]
    legacy_values, legacy_records, legacy_extensions = cue_reply(
        legacy_success, 0x2201
    )
    assert legacy_values == [0x2201, 0, 72, None, 36, 2, 0, 16, None]
    assert legacy_records == [
        (0x00010100, 0, 0, 15_000, 0, 0, 0, 0, 0),
        (0x00020100, 0, 0, 13_680, 0, 91_212, 0, 91_222, 0),
    ]
    assert legacy_extensions == [(100_001, 100_001), (91_202, 91_202)]

    legacy_request = legacy_success["request"]["arguments"]
    legacy_input_record = struct.unpack("<9I", bytes.fromhex(legacy_request[3]["hex"]))
    legacy_input_extension = struct.unpack(
        "<II", bytes.fromhex(legacy_request[5]["hex"])
    )
    assert legacy_input_record == (
        0x00040100,
        10_001,
        0,
        0x11111111,
        0x22222222,
        0x33333333,
        0x44444444,
        0x55555555,
        0x66666666,
    )
    assert legacy_input_extension == (0x77777777, 0x88888888)
    assert legacy_input_record not in legacy_records

    for case_id in (
        "known-content-unknown-bank",
        "unknown-content-canonical-bank",
    ):
        case = set_legacy[case_id]
        assert case["outcome"] == "timeout"
        assert case["raw_response"]["error_kind"] == "WouldBlock"

    legacy_slot_one = cases(load(SET_LEGACY_SLOT_ONE_NEGATIVE))
    assert set(legacy_slot_one) == set(set_legacy)
    for case in legacy_slot_one.values():
        assert case["outcome"] == "timeout"
        assert case["raw_response"]["error_kind"] == "WouldBlock"

    rejected_controls = [
        cases(load(SET_EXTENDED_REJECTED)),
        cases(load(SET_EXTENDED_ALIGNED_REJECTED)),
    ]
    for rejected in rejected_controls:
        assert reply_values(rejected["set"]) == [0x2401, 50, 0, None, 0]
        assert reply_values(rejected["before"]) == reply_values(rejected["after"])

    mutation_manifest = load(SET_EXTENDED_MANIFEST)
    live = load(SET_EXTENDED_LIVE)
    stopped = load(SET_EXTENDED_STOPPED)
    assert live["database_sha256"] == mutation_manifest["database_sha256"]
    assert live["sidecars"] == {
        "wal": {
            "bytes": 206_032,
            "sha256": "e96f074a2559f5efc8888f105cfaa10f39e735c174ebfb60f5195d653c944d16",
        },
        "shm": {
            "bytes": 32_768,
            "sha256": "d9f68f18cef3d530077249bf8b9ea2adc8ae890ae45a58fed1930ba2f630573c",
        },
    }
    assert stopped["database_sha256"] == mutation_manifest["database_sha256"]
    assert stopped["memberships"][0]["InMsec"] == 100_001

    live_memberships = {row["ID"]: row for row in live["memberships"]}
    updated = live_memberships["94001"]
    assert {
        key: updated[key]
        for key in (
            "InMsec",
            "InFrame",
            "InMpegFrame",
            "InMpegAbs",
            "OutMsec",
            "OutFrame",
            "OutMpegFrame",
            "OutMpegAbs",
            "Color",
            "BeatLoopSize",
            "CueMicrosec",
            "Comment",
            "InPointSeekInfo",
            "OutPointSeekInfo",
            "rb_local_usn",
            "updated_at",
        )
    } == {
        "InMsec": 456_789,
        "InFrame": 68_518,
        "InMpegFrame": 0x01020304,
        "InMpegAbs": 0x21222324,
        "OutMsec": 567_890,
        "OutFrame": 85_182,
        "OutMpegFrame": 0x11121314,
        "OutMpegAbs": 0x31323334,
        "Color": 5,
        "BeatLoopSize": 0x12345678,
        "CueMicrosec": 0x0A0B0C0D,
        "Comment": "",
        "InPointSeekInfo": "",
        "OutPointSeekInfo": "",
        "rb_local_usn": 145_190,
        "updated_at": "2026-10-02 02:00:15.668 +00:00",
    }
    assert live_memberships["94002"]["InMsec"] == 100_001
    assert all(cue["InMsec"] == 100_001 for cue in live["cues"])

    legacy_manifest = load(SET_LEGACY_MANIFEST)
    legacy_live = load(SET_LEGACY_LIVE)
    assert legacy_live["database_sha256"] == legacy_manifest["database_sha256"]
    assert legacy_live["sidecars"] == {
        "wal": {
            "bytes": 189_552,
            "sha256": "090547b2316c84e3b308072eae74d4654160b1bdfc796cfc580ac876e42fb337",
        },
        "shm": {
            "bytes": 32_768,
            "sha256": "6ef0e93d6ee4201c25350b64f27cdea0208b2756cb660aba5af69a5d6b03c514",
        },
    }
    legacy_memberships = {row["ID"]: row for row in legacy_live["memberships"]}
    legacy_updated = legacy_memberships["94101"]
    assert {
        key: legacy_updated[key]
        for key in (
            "ContentID",
            "TrackNo",
            "InMsec",
            "InFrame",
            "InMpegFrame",
            "InMpegAbs",
            "OutMsec",
            "OutFrame",
            "OutMpegFrame",
            "OutMpegAbs",
            "Color",
            "rb_local_usn",
            "updated_at",
        )
    } == {
        "ContentID": "10001",
        "TrackNo": 4,
        "InMsec": 0x77777777,
        "InFrame": 0x11111111,
        "InMpegFrame": 0x33333333,
        "InMpegAbs": 0x55555555,
        "OutMsec": 0xFFFFFFFF,
        "OutFrame": 0x22222222,
        "OutMpegFrame": 0x44444444,
        "OutMpegAbs": 0x66666666,
        "Color": -1,
        "rb_local_usn": 145_189,
        "updated_at": "2026-10-02 02:28:01.929 +00:00",
    }
    assert legacy_memberships["94102"]["InMsec"] == 100_001
    assert all(cue["InMsec"] == 100_001 for cue in legacy_live["cues"])

    ordinal_expected = {
        "ordinal-d": (
            [
                (0x00010100, 0, 0, 15_000, 0, 0, 0, 0, 0),
                (0x00020100, 0, 0, 13_680, 0, 91_212, 0, 91_222, 0),
            ],
            [(100_001, 100_001), (91_202, 91_202)],
        ),
        "ordinal-e": (
            [(0x00010100, 0, 0, 15_000, 0, 0, 0, 0, 0)],
            [(100_001, 100_001)],
        ),
        "ordinal-f": (
            [(0x00010100, 0, 0, 15_000, 0, 0, 0, 0, 0)],
            [(100_001, 100_001)],
        ),
    }
    for case_id, (expected_records, expected_extensions) in ordinal_expected.items():
        _, records, extensions = cue_reply(legacy_ordinals[case_id], 0x2201)
        assert records == expected_records
        assert extensions == expected_extensions

    ordinal_manifest = load(LEGACY_ORDINAL_MANIFEST)
    ordinal_live = load(LEGACY_ORDINAL_LIVE)
    assert ordinal_live["database_sha256"] == ordinal_manifest["database_sha256"]
    assert ordinal_live["sidecars"] == {
        "wal": {
            "bytes": 230_752,
            "sha256": "72bef4a855121f93e38de1fa1811214e59b99b1820657f4ee02b537a0a748224",
        },
        "shm": {
            "bytes": 32_768,
            "sha256": "bbf4c3826983ca34a981e6054866e221b80086582fb491507333ccdec9d948ee",
        },
    }
    ordinal_memberships = {
        row["ID"]: row for row in ordinal_live["memberships"]
    }
    for relation_id, track_no, content_id, local_usn in (
        ("94201", 4, "10001", 145_189),
        ("94203", 5, "10002", 145_190),
        ("94205", 6, "10003", 145_191),
    ):
        row = ordinal_memberships[relation_id]
        assert row["TrackNo"] == track_no
        assert row["ContentID"] == content_id
        assert row["InMsec"] == 0x77777777
        assert row["InFrame"] == 0x11111111
        assert row["OutFrame"] == 0x22222222
        assert row["InMpegFrame"] == 0x33333333
        assert row["OutMpegFrame"] == 0x44444444
        assert row["InMpegAbs"] == 0x55555555
        assert row["OutMpegAbs"] == 0x66666666
        assert row["OutMsec"] == 0xFFFFFFFF
        assert row["Color"] == -1
        assert row["rb_local_usn"] == local_usn
        assert row["updated_at"] != "2026-01-01 00:00:00.000 +00:00"
    for relation_id in ("94202", "94204", "94206"):
        row = ordinal_memberships[relation_id]
        assert row["InMsec"] == 100_001
        assert row["rb_local_usn"] is None
        assert row["updated_at"] == "2026-01-01 00:00:00.000 +00:00"
    assert len(ordinal_live["cues"]) == 6
    assert all(cue["InMsec"] == 100_001 for cue in ordinal_live["cues"])
    assert all(cue["rb_local_usn"] is None for cue in ordinal_live["cues"])

    boundary_ordinals = (0, 1, 2, 3, 7, 8, 255, 256, 32_767, 32_768, 65_535)
    boundary_reply_counts = (2, 1, 1, 1, 1, 2, 1, 1, 2, 1, 1)
    for case, expected_count in zip(
        legacy_ordinal_boundaries.values(), boundary_reply_counts, strict=True
    ):
        values, records, extensions = cue_reply(case, 0x2201)
        assert values[1] == 0
        assert len(records) == expected_count
        assert len(extensions) == expected_count

    boundary_manifest = load(LEGACY_ORDINAL_BOUNDARY_MANIFEST)
    boundary_live = load(LEGACY_ORDINAL_BOUNDARY_LIVE)
    assert boundary_live["database_sha256"] == boundary_manifest["database_sha256"]
    assert boundary_live["sidecars"] == {
        "wal": {
            "bytes": 168_952,
            "sha256": "d9be5defe53a37f2ce9243c08d695decd9681707fe00bec77db25398e0a6f161",
        },
        "shm": {
            "bytes": 32_768,
            "sha256": "c2b913ef8450a3b21305a8d6daa199186eab0b33b1671e611cbfb616e0f0cb11",
        },
    }
    assert boundary_live["membership_count"] == len(boundary_ordinals) * 2
    assert [row["TrackNo"] for row in boundary_live["memberships"]] == [
        ordinal for ordinal in boundary_ordinals for _ in range(2)
    ]
    for row in boundary_live["memberships"]:
        assert row["InMsec"] == 100_001
        assert row["InFrame"] is None
        assert row["OutMsec"] == 0
        assert row["InMpegFrame"] == 0
        assert row["OutMpegFrame"] == 0
        assert row["InMpegAbs"] == 0
        assert row["OutMpegAbs"] == 0
        assert row["Color"] == 0
        assert row["rb_local_usn"] is None
        assert row["updated_at"] == "2026-01-01 00:00:00.000 +00:00"
    assert len(boundary_live["cues"]) == len(boundary_ordinals) * 2
    assert all(cue["InMsec"] == 100_001 for cue in boundary_live["cues"])
    assert all(cue["rb_local_usn"] is None for cue in boundary_live["cues"])

    deleted_tree = deleted_bank_member["parent-tree"]
    assert deleted_tree["outcome"] == "menu"
    assert deleted_tree["total"] == 1
    assert [(row[1], row[3]) for row in row_values(deleted_tree)] == [
        (9_032, "Beta Bank")
    ]

    deleted_tracks = deleted_bank_member["direct-tracks"]
    assert deleted_tracks["outcome"] == "menu"
    assert deleted_tracks["total"] == 1
    assert content_positions(deleted_tracks) == [(10_005, 1)]

    deleted_cue_values, deleted_cue_records, deleted_cue_extensions = cue_reply(
        deleted_bank_member["legacy-cues"]
    )
    assert deleted_cue_values == [0x2101, 0, 36, None, 36, 1, 0, 8, None]
    assert deleted_cue_records == [
        (0x00040100, 10_005, 0, 13_717, 0, 91_460, 0xFFFFFFFF, 91_470, 0xFFFFFFFF)
    ]
    assert deleted_cue_extensions == [(91_450, 0xFFFFFFFF)]

    deleted_extended = new_cue_records(deleted_bank_member["extended-cues"])
    assert len(deleted_extended) == 1
    assert deleted_extended[0]["slot"] == 1
    assert deleted_extended[0]["in_msec"] == 91_450
    assert deleted_extended[0]["out_msec"] == -1
    assert deleted_extended[0]["in_mpeg_frame"] == 91_460
    assert deleted_extended[0]["in_mpeg_abs"] == 91_470

    in_seek_crash = load(IN_SEEK_CRASH)["behavior"]["cases"][0]
    assert in_seek_crash["outcome"] == "timeout"
    assert in_seek_crash["raw_response"]["error_kind"] == "WouldBlock"

    tree_expected = {
        "tree-root": [
            (9002, "Beta Folder", 1, 1),
            (9001, "Alpha Folder", 1, 2),
            (9003, "Root Bank", 43, 3),
        ],
        "tree-alpha-folder": [
            (9011, "Deep Folder", 1, 2),
            (9012, "Alpha Bank", 43, 1),
            (9013, "Empty Bank", 43, 3),
        ],
        "tree-beta-folder": [(9032, "Beta Bank", 43, 2)],
        "tree-deep-folder": [(9021, "Deep Bank", 43, 1)],
    }
    for case_id, expected in tree_expected.items():
        rows = row_values(matrix[case_id])
        assert [(row[1], row[3], row[6], row[9]) for row in rows] == expected

    for case_id in (
        "root-bank-as-folder",
        "alpha-bank-as-folder",
        "empty-bank-as-folder",
        "deep-bank-as-folder",
        "beta-bank-as-folder",
        "empty-bank-tracks",
        "deleted-bank-tracks",
        "zero-selector-tracks",
        "unknown-selector-folder",
        "unknown-selector-tracks",
        "mode-2",
        "mode-255",
    ):
        assert matrix[case_id]["outcome"] == "menu"
        assert matrix[case_id]["total"] == 0
        assert matrix[case_id]["rows"] == []

    limits = {0: 3, 1: 3, 2: 3, 3: 3, 4: 4, 5: 5, 8: 8, 16: 10}
    for requested, expected in limits.items():
        case = matrix[f"alpha-limit-{requested}"]
        assert case["total"] == expected
        assert len(case["rows"]) == expected

    safe_large_counts = (17, 255, 256, 65_535, 65_536, 1_048_576)
    assert [
        case["request"]["arguments"][3]["value"]
        for case in count_boundaries.values()
    ] == list(safe_large_counts)
    for case in count_boundaries.values():
        assert case["outcome"] == "menu"
        assert case["total"] == 10
        assert len(case["rows"]) == 10
        assert case["rows"] == matrix["alpha-limit-16"]["rows"]

    count_hazard_results = {}
    for name, requested in COUNT_HAZARD_PROBES.items():
        case = next(iter(count_hazards[name].values()))
        expected_total = 10 if name == "int32-max" else 0
        assert case["request"]["arguments"][3]["value"] == requested
        assert case["outcome"] == "menu"
        assert case["total"] == expected_total
        assert len(case["rows"]) == expected_total
        if expected_total:
            assert case["rows"] == matrix["alpha-limit-16"]["rows"]

        phase_health = {}
        for phase in ("record", "repeat"):
            before_path = COUNT_HAZARD_EVIDENCE / name / f"{phase}-before.json"
            after_path = COUNT_HAZARD_EVIDENCE / name / f"{phase}-after.json"
            before = load(before_path)
            after = load(after_path)
            assert before["rekordbox_process_count"] == 1
            assert after["rekordbox_process_count"] == 1
            assert before["rekordbox_processes"][0]["id"] == after["rekordbox_processes"][0]["id"]
            assert before["rekordbox_processes"][0]["responding"] is True
            assert after["rekordbox_processes"][0]["responding"] is True
            assert [event["record_id"] for event in before["application_events"]] == [
                event["record_id"] for event in after["application_events"]
            ]
            phase_health[phase] = {
                "process_id": before["rekordbox_processes"][0]["id"],
                "responding_after": after["rekordbox_processes"][0]["responding"],
                "new_application_event_count": 0,
                "working_set_delta_bytes": (
                    after["rekordbox_processes"][0]["working_set_bytes"]
                    - before["rekordbox_processes"][0]["working_set_bytes"]
                ),
                "private_memory_delta_bytes": (
                    after["rekordbox_processes"][0]["private_memory_bytes"]
                    - before["rekordbox_processes"][0]["private_memory_bytes"]
                ),
                "virtual_memory_delta_bytes": (
                    after["rekordbox_processes"][0]["virtual_memory_bytes"]
                    - before["rekordbox_processes"][0]["virtual_memory_bytes"]
                ),
            }
        count_hazard_results[str(requested)] = {
            "total": expected_total,
            "row_count": expected_total,
            "process_health": phase_health,
        }

    alpha_positions = content_positions(matrix["alpha-limit-16"])
    assert alpha_positions == [
        (10008, 1),
        (10001, 2),
        (10006, 3),
        (10003, 4),
        (10002, 5),
        (10007, 6),
        (10004, 7),
        (10005, 8),
        (10001, 9),
        (10002, 12),
    ]
    assert content_positions(matrix["root-bank-tracks"]) == [
        (10002, 1),
        (10001, 2),
    ]
    assert content_positions(matrix["deep-bank-tracks"]) == [
        (10004, 65535),
        (10003, 0),
    ]
    assert content_positions(matrix["beta-bank-tracks"]) == [(10007, 1)]

    for location in (1, 2, 3, 7):
        case = matrix[f"location-{location}-root"]
        assert case["outcome"] == "menu"
        assert case["total"] == 3
        assert case["rows"] == []

    location_rows = location_renders["location-1-legacy-render"]["rows"]
    assert len(location_rows) == 3
    location_render_results = {}
    for location in (1, 2, 3, 7):
        location_render_results[str(location)] = {}
        for width, argument_count in (("legacy", 6), ("extended", 8)):
            case = location_renders[f"location-{location}-{width}-render"]
            assert case["outcome"] == "menu"
            assert case["total"] == 3
            assert case["rows"] == location_rows
            assert len(case["pages"]) == 1
            arguments = case["pages"][0]["arguments"]
            assert len(arguments) == argument_count
            assert arguments[0]["value"] == 0x01010001 | (location << 8)
            location_render_results[str(location)][width] = {
                "argument_count": argument_count,
                "total": case["total"],
                "row_count": len(case["rows"]),
            }

    for request_location in (2, 7):
        case = location_renders[
            f"location-{request_location}-header-location-3-render"
        ]
        assert case["outcome"] == "menu"
        assert case["total"] == 3
        assert case["rows"] == location_rows
        assert case["pages"][0]["arguments"][0]["value"] == 0x01010301

    locations = (1, 2, 3, 7)
    location_cross_results = {}
    for header_index, header_location in enumerate(locations):
        location_cross_results[str(header_location)] = {}
        for render_index, render_location in enumerate(locations):
            expected_outcome = "menu" if render_index <= header_index else "render_timeout"
            location_cross_results[str(header_location)][str(render_location)] = {}
            for width, argument_count in (("legacy", 6), ("extended", 8)):
                case = location_cross[
                    f"header-location-{header_location}-render-location-"
                    f"{render_location}-{width}"
                ]
                assert case["outcome"] == expected_outcome
                assert case["total"] == 3
                assert len(case["pages"]) == 1
                assert len(case["pages"][0]["arguments"]) == argument_count
                assert case["pages"][0]["arguments"][0]["value"] == (
                    0x01010001 | (render_location << 8)
                )
                if expected_outcome == "menu":
                    assert case["rows"] == location_rows
                else:
                    assert case["rows"] == []
                    assert case["pages"][0]["outcome"] == "timeout"
                    assert case["pages"][0]["transport_error_kind"] == "WouldBlock"
                location_cross_results[str(header_location)][str(render_location)][
                    width
                ] = expected_outcome

    location_state_rows = {
        "prime-location-1-root": [9002, 9001, 9003],
        "location-2-beta-render-location-1": [9002],
        "location-2-beta-current": [9032],
        "location-3-alpha-render-location-2": [9032],
        "location-3-alpha-current": [9011, 9012, 9013],
        "location-7-deep-render-location-3": [9011],
        "location-7-deep-current": [9021],
        "location-7-beta-render-old-location-1": [9002],
    }
    for case_id, expected_ids in location_state_rows.items():
        case = location_state[case_id]
        assert case["outcome"] == "menu"
        assert [row[1] for row in row_values(case)] == expected_ids

    location_health = {}
    for experiment, evidence in (
        ("render", LOCATION_RENDER_EVIDENCE),
        ("cross", LOCATION_CROSS_EVIDENCE),
        ("state", LOCATION_STATE_EVIDENCE),
    ):
        location_health[experiment] = {}
        for phase in ("record", "repeat"):
            before = load(evidence / f"{phase}-before.json")
            after = load(evidence / f"{phase}-after.json")
            assert before["rekordbox_process_count"] == 1
            assert after["rekordbox_process_count"] == 1
            assert before["rekordbox_processes"][0]["id"] == after["rekordbox_processes"][0]["id"]
            assert before["rekordbox_processes"][0]["responding"] is True
            assert after["rekordbox_processes"][0]["responding"] is True
            assert [event["record_id"] for event in before["application_events"]] == [
                event["record_id"] for event in after["application_events"]
            ]
            location_health[experiment][phase] = {
                "process_id": before["rekordbox_processes"][0]["id"],
                "responding_after": True,
                "new_application_event_count": 0,
                "working_set_delta_bytes": (
                    after["rekordbox_processes"][0]["working_set_bytes"]
                    - before["rekordbox_processes"][0]["working_set_bytes"]
                ),
            }

    manifest = load(MATRIX_MANIFEST)
    golden = load(MATRIX_GOLDEN)
    report = {
        "format": "rekordbox-hot-cue-bank-oracle-v1",
        "oracle": {
            "backend": "rekordbox",
            "version": "7.2.19",
            "identity": golden["provenance"]["identity"],
            "case_observations": sum(
                map(
                    len,
                    (
                        discovery,
                        matrix,
                        location_renders,
                        location_cross,
                        location_state,
                        count_boundaries,
                        *count_hazards.values(),
                        cues,
                        cues_status,
                        cues_rr,
                        cues_legacy,
                        cues_sequence,
                        cue_fields,
                        extended_cues,
                        extended_fields,
                        set_extended,
                        set_legacy,
                        legacy_ordinals,
                        legacy_ordinal_boundaries,
                        deleted_bank_member,
                    ),
                )
            ),
            "discovery_cases": len(discovery),
            "matrix_cases": len(matrix),
            "location_render_cases": len(location_renders),
            "location_cross_cases": len(location_cross),
            "location_state_cases": len(location_state),
            "count_boundary_cases": len(count_boundaries),
            "count_signed_boundary_cases": len(count_hazards),
            "cue_info_declared_cases": len(cues),
            "cue_info_field_cases": len(cue_fields),
            "extended_cue_cases": len(extended_cues),
            "extended_field_cases": len(extended_fields),
            "extended_setter_cases": len(set_extended),
            "legacy_setter_cases": len(set_legacy),
            "legacy_ordinal_cases": len(legacy_ordinals),
            "legacy_ordinal_boundary_cases": len(legacy_ordinal_boundaries),
            "deleted_bank_member_cases": len(deleted_bank_member),
            "cue_info_capture_variants": 8,
            "immediate_repeat_verified": True,
            "rbxport_tested": False,
        },
        "request": {
            "kind": "0x2001",
            "arguments": ["context", "selector", "mode", "requested_track_count"],
            "tree_mode": 1,
            "track_mode": 0,
            "unsupported_modes": [2, 255],
            "accepted_locations": [1, 2, 3, 7],
            "location_render_results": location_render_results,
            "location_cross_results": location_cross_results,
            "location_state_row_ids": location_state_rows,
            "menu_buffers_keyed_by_location": True,
            "menu_buffers_persist_across_tcp_connections": True,
            "render_of_uninitialized_location_times_out": True,
            "render_of_initialized_foreign_location_returns_stale_rows": True,
            "render_width_changes_location_state_behavior": False,
            "location_process_health": location_health,
            "safe_large_track_counts": list(safe_large_counts),
            "safe_large_track_count_result": 10,
            "track_count_field_narrowed_to_8_or_16_bits": False,
            "active_appsync_count_limit_comparison": "signed_32_bit",
            "active_appsync_allocates_count_sized_candidate_arrays": False,
            "signed_boundary_results": count_hazard_results,
        },
        "cue_info_request": {
            "kind": "0x2101",
            "arguments": ["context", "bank_id"],
            "expected_reply_kind": "0x4702",
            "observed_outcome": "0x4702_direct_reply",
            "reply_arguments": [
                "request_kind",
                "status",
                "cue_blob_bytes",
                "cue_blob",
                "cue_record_bytes",
                "cue_count",
                "extension_status",
                "extension_blob_bytes",
                "extension_blob",
            ],
            "cue_record_bytes": 36,
            "extension_record_bytes": 8,
            "alpha_content_ids": [record[1] for record in alpha_records],
            "alpha_cue_flags": [record[0] for record in alpha_records],
            "alpha_extension_values": alpha_extensions,
            "root_content_ids": [record[1] for record in root_records],
            "root_cue_flags": [record[0] for record in root_records],
            "root_extension_values": root_extensions,
            "empty_reply_arguments": cue_reply(cues["empty-bank"])[0],
            "identity_and_framing_payloads_byte_identical": True,
            "active_database_path": "djmdSongHotCueBanklist",
            "cue_record_words": [
                "flags",
                "content_id",
                "zero",
                "cue_frame_150fps",
                "loop_frame_150fps",
                "in_mpeg_frame",
                "out_mpeg_frame",
                "in_mpeg_abs",
                "out_mpeg_abs",
            ],
            "extension_words": ["in_msec", "out_msec"],
            "cue_field_records": field_records,
            "cue_field_extensions": field_extensions,
            "referenced_djmd_cue_rows_ignored": True,
            "non_wire_membership_fields_ignored": True,
            "compact_and_fixed_12_tag_frames_tested": True,
            "extended_and_legacy_setup_tested": True,
            "keepalive_and_player_status_identities_tested": True,
            "xdj_rx3_and_xdj_rr_models_tested": True,
            "stateful_catalog_navigation_tested": True,
            "new_format_request_kind": "0x2301",
            "new_format_reply_kind": "0x4e02",
            "new_format_record_layout": extended_records,
            "nonempty_in_seek_exits_rekordbox": True,
            "out_seek_without_valid_in_seek_ignored": True,
            "extended_setter_request_kind": "0x2401",
            "extended_setter_reply_kind": "0x4e02",
            "extended_setter_record": mutation_set,
            "extended_setter_immediate_readback_matches": True,
            "extended_setter_wal_persisted": True,
            "extended_setter_updates_membership_not_cue": True,
            "extended_setter_one_row_status": 50,
            "extended_setter_duplicate_slot_required_by_observed_resolver": True,
            "legacy_setter_request_kind": "0x2201",
            "legacy_setter_reply_kind": "0x4702",
            "legacy_setter_reply_records": legacy_records,
            "legacy_setter_reply_extensions": legacy_extensions,
            "legacy_setter_returns_djmd_cue_rows": True,
            "legacy_setter_updates_membership_not_cue": True,
            "legacy_setter_wire_ordinal_used_as_track_no": True,
            "legacy_setter_duplicate_track_no_required_by_observed_resolver": True,
            "legacy_setter_unknown_bank_times_out": True,
            "legacy_setter_unknown_content_times_out": True,
            "legacy_setter_ordinals": {"D": 4, "E": 5, "F": 6},
            "legacy_setter_all_supported_ordinals_repeat_verified": True,
            "legacy_setter_mutating_ordinal_gate": [4, 5, 6],
            "legacy_setter_acknowledged_noop_ordinals": list(boundary_ordinals),
            "legacy_setter_noop_replies_use_content_cues": True,
            "legacy_setter_noop_rows_unchanged_in_live_wal": True,
            "deleted_bank_hidden_from_tree": True,
            "deleted_bank_direct_tracks_served": True,
            "deleted_bank_direct_legacy_cues_served": True,
            "deleted_bank_direct_extended_cues_served": True,
        },
        "fixture": {
            "profile": manifest["profile"],
            "version": manifest["fixture_version"],
            "database_sha256": manifest["database_sha256"],
            "fixture_fingerprint": manifest["fixture_fingerprint"],
            "manifest_sha256": sha256(MATRIX_MANIFEST),
            "track_count": manifest["track_count"],
        },
        "behavior": {
            "tree": tree_expected,
            "track_count_limits": {str(key): value for key, value in limits.items()},
            "alpha_content_positions": alpha_positions,
            "root_content_positions": content_positions(matrix["root-bank-tracks"]),
            "deep_content_positions": content_positions(matrix["deep-bank-tracks"]),
            "excluded_alpha_content_ids": [10999, 999999],
            "duplicate_content_id": 10001,
            "locally_deleted_membership_content_id": 10002,
        },
        "artifacts": {
            "discovery_suite_sha256": sha256(DISCOVERY_SUITE),
            "discovery_golden_sha256": sha256(DISCOVERY_GOLDEN),
            "matrix_suite_sha256": sha256(MATRIX_SUITE),
            "matrix_golden_sha256": sha256(MATRIX_GOLDEN),
            "location_render_suite_sha256": sha256(LOCATION_RENDER_SUITE),
            "location_render_golden_sha256": sha256(LOCATION_RENDER_GOLDEN),
            "location_render_health_sha256": {
                f"{phase}-{point}": sha256(
                    LOCATION_RENDER_EVIDENCE / f"{phase}-{point}.json"
                )
                for phase in ("record", "repeat")
                for point in ("before", "after")
            },
            "location_cross_suite_sha256": sha256(LOCATION_CROSS_SUITE),
            "location_cross_golden_sha256": sha256(LOCATION_CROSS_GOLDEN),
            "location_cross_health_sha256": {
                f"{phase}-{point}": sha256(
                    LOCATION_CROSS_EVIDENCE / f"{phase}-{point}.json"
                )
                for phase in ("record", "repeat")
                for point in ("before", "after")
            },
            "location_state_suite_sha256": sha256(LOCATION_STATE_SUITE),
            "location_state_golden_sha256": sha256(LOCATION_STATE_GOLDEN),
            "location_state_health_sha256": {
                f"{phase}-{point}": sha256(
                    LOCATION_STATE_EVIDENCE / f"{phase}-{point}.json"
                )
                for phase in ("record", "repeat")
                for point in ("before", "after")
            },
            "count_boundary_suite_sha256": sha256(COUNT_BOUNDARY_SUITE),
            "count_boundary_golden_sha256": sha256(COUNT_BOUNDARY_GOLDEN),
            "count_signed_boundary_artifacts": {
                name: {
                    "suite_sha256": sha256(
                        CONFORMANCE / f"suites/hot-cue-bank-count-{name}.json"
                    ),
                    "golden_sha256": sha256(
                        GOLDENS / f"hot-cue-bank-count-{name}.json"
                    ),
                    "health_sha256": {
                        f"{phase}-{point}": sha256(
                            COUNT_HAZARD_EVIDENCE
                            / name
                            / f"{phase}-{point}.json"
                        )
                        for phase in ("record", "repeat")
                        for point in ("before", "after")
                    },
                }
                for name in COUNT_HAZARD_PROBES
            },
            "cue_suite_sha256": sha256(CUE_SUITE),
            "cue_golden_sha256": sha256(CUE_GOLDEN),
            "cue_status_golden_sha256": sha256(CUE_STATUS_GOLDEN),
            "cue_rr_golden_sha256": sha256(CUE_RR_GOLDEN),
            "cue_legacy_golden_sha256": sha256(CUE_LEGACY_GOLDEN),
            "cue_sequence_golden_sha256": sha256(CUE_SEQUENCE_GOLDEN),
            "cue_fields_suite_sha256": sha256(CUE_FIELDS_SUITE),
            "cue_fields_golden_sha256": sha256(CUE_FIELDS_GOLDEN),
            "cue_fields_manifest_sha256": sha256(CUE_FIELDS_MANIFEST),
            "extended_cue_suite_sha256": sha256(EXTENDED_CUE_SUITE),
            "extended_cue_golden_sha256": sha256(EXTENDED_CUE_GOLDEN),
            "extended_fields_suite_sha256": sha256(EXTENDED_FIELDS_SUITE),
            "extended_fields_golden_sha256": sha256(EXTENDED_FIELDS_GOLDEN),
            "extended_fields_manifest_sha256": sha256(EXTENDED_FIELDS_MANIFEST),
            "set_extended_suite_sha256": sha256(SET_EXTENDED_SUITE),
            "set_extended_golden_sha256": sha256(SET_EXTENDED_GOLDEN),
            "set_extended_manifest_sha256": sha256(SET_EXTENDED_MANIFEST),
            "set_extended_live_snapshot_sha256": sha256(SET_EXTENDED_LIVE),
            "set_extended_stopped_snapshot_sha256": sha256(SET_EXTENDED_STOPPED),
            "set_extended_rejected_sha256": sha256(SET_EXTENDED_REJECTED),
            "set_extended_aligned_rejected_sha256": sha256(
                SET_EXTENDED_ALIGNED_REJECTED
            ),
            "set_legacy_suite_sha256": sha256(SET_LEGACY_SUITE),
            "set_legacy_golden_sha256": sha256(SET_LEGACY_GOLDEN),
            "set_legacy_manifest_sha256": sha256(SET_LEGACY_MANIFEST),
            "set_legacy_live_snapshot_sha256": sha256(SET_LEGACY_LIVE),
            "set_legacy_slot_one_negative_sha256": sha256(
                SET_LEGACY_SLOT_ONE_NEGATIVE
            ),
            "legacy_setter_disassembly_sha256": sha256(LEGACY_SETTER_STATIC),
            "legacy_ordinal_suite_sha256": sha256(LEGACY_ORDINAL_SUITE),
            "legacy_ordinal_golden_sha256": sha256(LEGACY_ORDINAL_GOLDEN),
            "legacy_ordinal_manifest_sha256": sha256(LEGACY_ORDINAL_MANIFEST),
            "legacy_ordinal_live_snapshot_sha256": sha256(LEGACY_ORDINAL_LIVE),
            "legacy_ordinal_boundary_suite_sha256": sha256(
                LEGACY_ORDINAL_BOUNDARY_SUITE
            ),
            "legacy_ordinal_boundary_golden_sha256": sha256(
                LEGACY_ORDINAL_BOUNDARY_GOLDEN
            ),
            "legacy_ordinal_boundary_manifest_sha256": sha256(
                LEGACY_ORDINAL_BOUNDARY_MANIFEST
            ),
            "legacy_ordinal_boundary_live_snapshot_sha256": sha256(
                LEGACY_ORDINAL_BOUNDARY_LIVE
            ),
            "deleted_bank_member_suite_sha256": sha256(DELETED_BANK_MEMBER_SUITE),
            "deleted_bank_member_golden_sha256": sha256(
                DELETED_BANK_MEMBER_GOLDEN
            ),
            "deleted_bank_member_manifest_sha256": sha256(
                DELETED_BANK_MEMBER_MANIFEST
            ),
            "membership_resolver_disassembly_sha256": sha256(
                MEMBERSHIP_RESOLVER_STATIC
            ),
            "in_seek_crash_sha256": sha256(IN_SEEK_CRASH),
            "out_seek_capture_sha256": sha256(OUT_SEEK_CAPTURE),
            "seek_parser_disassembly_sha256": sha256(
                ROOT / "data/static-analysis/cue-seek-value-parser.disasm.txt"
            ),
            "cue_time_conversion_disassembly_sha256": sha256(
                ROOT / "data/static-analysis/cue-time-conversion.disasm.txt"
            ),
            "static_disassembly_sha256": sha256(STATIC),
        },
    }
    output = ROOT / "data/experiments/hot-cue-bank/summary.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(output)


if __name__ == "__main__":
    main()
