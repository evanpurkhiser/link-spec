#!/usr/bin/env python3
"""Generate mechanical capability, context, sort, render, and settings matrices."""

from __future__ import annotations

import copy
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SUITES = ROOT / "suites/generated"
SETTINGS = ROOT / "settings/generated"
EXPERIMENTS = ROOT.parent / "data/experiments/song-info-sibling-errors"
ORDER_EXPERIMENTS = ROOT.parent / "data/experiments/song-info-delivery-order"
STATUS_LOCATION_EXPERIMENTS = (
    ROOT.parent / "data/experiments/song-info-status-location2"
)

SECONDARIES = {
    2: "artist",
    3: "album",
    4: "bpm",
    5: "rating",
    6: "genre",
    7: "comment",
    8: "time",
    9: "remixer",
    10: "label",
    11: "original-artist",
    12: "key",
    13: "bitrate",
    15: "color",
    16: "play-count",
    17: "date-added",
}

SECONDARY_TYPE_BYTES = {
    2: 0x07,
    3: 0x02,
    4: 0x0D,
    5: 0x0A,
    6: 0x06,
    7: 0x23,
    8: 0x0B,
    9: 0x29,
    10: 0x0E,
    11: 0x28,
    12: 0x0F,
    13: 0x10,
    14: 0x00,
    16: 0x2A,
    17: 0x2E,
}

TRACK_ARGUMENT_VALUES = {
    2: ("$fixture.artist.alpha", "$fixture.artist.beta"),
    3: (0, "$fixture.album.one", "$fixture.album.two", "$fixture.album.three"),
    4: (12000, 12050, 12100, 12150, 12200, 12250, 12300, 12350),
    5: (0, 1, 2, 3, 4, 5),
    6: ("$fixture.genre.house", "$fixture.genre.techno"),
    7: tuple(f"$fixture.track.{name}" for name in (
        "first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth"
    )),
    8: (59, 60, 61, 599, 600, 601, 10799, 10800),
    9: ("$fixture.artist.remixer",),
    10: ("$fixture.label.one", "$fixture.label.two"),
    11: ("$fixture.artist.original",),
    12: ("$fixture.key.am", "$fixture.key.c"),
    13: (0, 32, 128, 160, 192, 256, 320, 1411),
    14: (0,),
    15: tuple(range(1, 9)),
    16: tuple(range(8)),
    17: tuple(f"$fixture.track.{name}" for name in (
        "first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth"
    )),
}

TRACK_KEY_IDS = ("$fixture.key.am", "$fixture.key.c")
TRACK_BPMS = (12000, 12050, 12100, 12150, 12200, 12250, 12300, 12350)

CATEGORY_IDS = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 15, 17, 18, 19, 20, 21, 22, 23, 26)
SORT_STATES = {
    0: True,
    1: True,
    2: True,
    3: True,
    4: True,
    5: True,
    6: True,
    7: False,
    8: False,
    9: False,
    10: True,
    11: False,
    12: True,
    13: False,
    15: False,
    16: True,
    17: True,
}

RX3_VISIBLE_SORTS = (
    (0, "default"),
    (1, "alphabet"),
    (2, "artist"),
    (3, "album"),
    (4, "bpm"),
    (5, "rating"),
    (6, "genre"),
    (10, "label"),
    (12, "key"),
    (17, "date-added"),
    (16, "dj-play-count"),
)


def number(value: int | str) -> dict[str, int | str]:
    return {"number": value}


def defaults(*, render_arguments=None) -> dict[str, object]:
    return {
        "device": 1,
        "context": "0x01010301",
        "sort": 0,
        "root_capabilities": "0x05cfffff",
        "setup": "extended",
        "page_size": 3,
        "render_arguments": render_arguments or [0, "$total", 12, 1, 0],
    }


def suite(name: str, cases: list[dict[str, object]], *, render_arguments=None) -> dict[str, object]:
    return {
        "name": name,
        "fixture_profile": "full",
        "fixture_version": 1,
        "defaults": defaults(render_arguments=render_arguments),
        "cases": cases,
    }


def root_case(name: str, mask: int) -> dict[str, object]:
    return {
        "id": name,
        "description": f"Root capability mask 0x{mask:08x}",
        "request_kind": "0x1000",
        "arguments": [number("$context"), number("$sort"), number(f"0x{mask:08x}")],
        "expect": {"outcome": "menu"},
    }


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n")


def settings_suite(name: str, case: dict[str, object]) -> dict[str, object]:
    value = suite(name, [case])
    value["fixture_profile"] = "settings"
    value["fixture_variant"] = name
    return value


def release_year_case(
    case_id: str,
    description: str,
    year: int,
    secondary: int,
    expected_outcome: str,
) -> dict[str, object]:
    return {
        "id": case_id,
        "description": description,
        "request_kind": "0x1208",
        "arguments": [
            number("$context"),
            number("$sort"),
            number((year // 10) * 10),
            number(year),
        ],
        "render_arguments": [0, "$total", 12, 1, secondary],
        "fresh_connection": True,
        "expect": {
            "outcome": expected_outcome,
            "total": 1,
            "row_count": 1 if expected_outcome == "menu" else 0,
        },
    }


def song_info_delayed_reply_routing_suites() -> list[tuple[str, dict[str, object]]]:
    precursors = {
        "delivery-blob-content": [
            number("$context"),
            {"blob_hex": "01020304"},
        ],
        "delivery-extra-argument-control": [
            number("$context"),
            number("$fixture.track.first"),
            number("0xdeadbeef"),
        ],
    }
    documents = []
    for precursor_name, precursor_arguments in precursors.items():
        for delay_ms in (0, 50, 100):
            cases = [
                {
                    "id": "first--play-extra-argument",
                    "description": "First precursor: Play Song Info with an extra number",
                    "request_kind": "0x2102",
                    "arguments": [
                        number("$context"),
                        number("$fixture.track.first"),
                        number("0xdeadbeef"),
                    ],
                    "render": False,
                    "fresh_connection": True,
                    "expect": {"outcome": "any"},
                },
                {
                    "id": f"second--{precursor_name}",
                    "description": f"Second precursor: {precursor_name}",
                    "request_kind": "0x2602",
                    "arguments": precursor_arguments,
                    "render": False,
                    "fresh_connection": True,
                    "expect": {"outcome": "any"},
                },
                {
                    "id": "replacement-no-send",
                    "description": (
                        "Read without sending on a replacement connection after "
                        f"{delay_ms} ms"
                    ),
                    "request_kind": 0,
                    "arguments": [],
                    "raw_hex": "",
                    "raw_read_ms": 1200,
                    "render": False,
                    "fresh_connection": True,
                    "capture_connection_setup": True,
                    "delay_before_connection_ms": delay_ms,
                    "expect": {"outcome": "any"},
                },
                {
                    "id": "delivery-probe-observation-connection",
                    "description": "Valid location-2 Delivery on the no-send observation connection",
                    "request_kind": "0x2602",
                    "arguments": [number("0x0b020301"), number("$fixture.track.first")],
                    "render": False,
                    "fresh_connection": False,
                    "delay_before_request_ms": 50,
                    "expect": {"outcome": "any"},
                },
                {
                    "id": "delivery-probe-fresh-health",
                    "description": "Valid location-2 Delivery on an independent fresh connection",
                    "request_kind": "0x2602",
                    "arguments": [number("0x0b020301"), number("$fixture.track.first")],
                    "render": False,
                    "fresh_connection": True,
                    "delay_before_connection_ms": 250,
                    "expect": {"outcome": "any"},
                },
            ]
            document = suite(
                "song-info-delayed-reply-routing--"
                f"{precursor_name}--{delay_ms:04}ms",
                cases,
            )
            document["defaults"].update(
                {"device": 11, "context": "0x0b010301", "read_timeout_ms": 10_000}
            )
            documents.append((f"{precursor_name}--{delay_ms:04}ms.json", document))

    return documents


def track_argument_expectations(sort_id: int) -> dict[str, object]:
    return {
        "row_argument_any_of": {
            "0": TRACK_ARGUMENT_VALUES[sort_id],
            "10": ("0x00000100", "0x00000101"),
            "12": TRACK_KEY_IDS,
            "15": TRACK_BPMS,
        }
    }


def main() -> None:
    boundary_rows = (
        ("empty", 0, 0, "empty string"),
        ("ascii-126", 49, 9, "126 ASCII characters"),
        ("ascii-127", 50, 10, "127 ASCII characters"),
        ("ascii-128", 99, 1999, "128 ASCII characters"),
        ("ascii-254", 100, 2000, "254 ASCII characters"),
        ("ascii-255", 149, 2999, "255 ASCII characters"),
        ("ascii-256", 150, 3000, "256 ASCII characters"),
        ("supplementary-256", 49_949, 4000, "256 supplementary characters"),
    )
    boundary_cases = []
    for field, secondary in (("comment", 7), ("date-added", 17)):
        for suffix, bpm, year, value_description in boundary_rows:
            boundary_cases.append(
                release_year_case(
                    f"{field}-{suffix}",
                    f"Isolated {field} rendering with {value_description} (BPM {bpm})",
                    year,
                    secondary,
                    "render_timeout" if suffix == "supplementary-256" else "menu",
                )
            )
    boundary_suite = suite("secondary-string-threshold-isolation", boundary_cases)
    boundary_suite["fixture_profile"] = "boundaries"
    write(SUITES / "secondary-string-thresholds.json", boundary_suite)

    unicode_rows = (
        ("supplementary-126", 0, 252),
        ("supplementary-127", 9, 254),
        ("supplementary-127-plus-ascii", 10, 255),
        ("supplementary-128", 1999, 256),
        ("supplementary-128-plus-ascii", 2000, 257),
        ("supplementary-254", 2999, 508),
        ("supplementary-255", 3000, 510),
        ("supplementary-256", 4000, 512),
    )
    unicode_cases = []
    for field, secondary in (("comment", 7), ("date-added", 17)):
        for suffix, year, code_units in unicode_rows:
            unicode_cases.append(
                release_year_case(
                    f"{field}-{suffix}",
                    f"Isolated {field} rendering with {code_units} UTF-16 code units",
                    year,
                    secondary,
                    "menu" if code_units <= 255 else "render_timeout",
                )
            )
    unicode_suite = suite("secondary-unicode-threshold-isolation", unicode_cases)
    unicode_suite["fixture_profile"] = "unicode-boundaries"
    write(SUITES / "secondary-unicode-thresholds.json", unicode_suite)

    capability_cases = [root_case("none", 0)]
    for menu_item in range(1, 28):
        bit = 24 if menu_item == 22 else menu_item - 1
        capability_cases.append(root_case(f"menu-item-{menu_item:02}", 1 << bit))
    capability_cases.extend(
        (
            root_case("legacy-mask", 0x00FF_FFFF),
            root_case("captured-mask", 0x05CF_FFFF),
            root_case("all-bits", 0xFFFF_FFFF),
        )
    )
    write(SUITES / "root-capabilities.json", suite("root-capability-bit-sweep", capability_cases))

    sort_cases = []
    for sort_id in range(18):
        sort_cases.append(
            {
                "id": f"sort-{sort_id:02}",
                "description": f"Track root with requested sort ID {sort_id}",
                "request_kind": "0x1004",
                "arguments": [number("$context"), number(sort_id)],
                "expect": {"outcome": "any"},
            }
        )
    write(SUITES / "sort-ids.json", suite("track-sort-id-sweep", sort_cases))

    sort_render_cases = []
    for sort_id, name in RX3_VISIBLE_SORTS:
        sort_render_cases.append(
            {
                "id": f"{sort_id:02}-{name}",
                "description": (
                    f"RX3 {name.replace('-', ' ').title()} track sort followed by "
                    "active-sort rendering"
                ),
                "request_kind": "0x1004",
                "arguments": [number("$context"), number(sort_id)],
                "fresh_connection": True,
                "expect": {
                    "outcome": "menu",
                    "total": 8,
                    "row_count": 8,
                    "argument_count": 16,
                    "item_type_low_byte": "0x04",
                },
            }
        )
    sort_render_5_suite = suite(
        "rx3-track-sort-secondary-render-5",
        [
            {
                **case,
                "description": case["description"].replace(
                    "active-sort rendering", "five-argument rendering"
                ),
            }
            for case in sort_render_cases
        ],
        render_arguments=[0, "$total"],
    )
    write(SUITES / "sort-secondary-render-5.json", sort_render_5_suite)

    sort_render_6_suite = suite(
        "rx3-track-sort-secondary-render-6",
        [
            {
                **case,
                "description": case["description"].replace(
                    "active-sort rendering", "six-argument rendering"
                ),
            }
            for case in sort_render_cases
        ],
        render_arguments=[0, "$total", 12],
    )
    write(SUITES / "sort-secondary-render-6.json", sort_render_6_suite)

    sort_render_7_cases = []
    for gate, gate_name in (
        (0, "gate-zero"),
        (1, "gate-one"),
        ("0xffffffff", "gate-maximum"),
    ):
        for sort_id, name in RX3_VISIBLE_SORTS:
            sort_render_7_cases.append(
                {
                    "id": f"{sort_id:02}-{name}-{gate_name}",
                    "description": (
                        f"RX3 {name.replace('-', ' ').title()} track sort followed by "
                        f"seven-argument rendering with {gate_name.replace('-', ' ')}"
                    ),
                    "request_kind": "0x1004",
                    "arguments": [number("$context"), number(sort_id)],
                    "render_arguments": [0, "$total", 12, gate],
                    "fresh_connection": True,
                    "expect": {
                        "outcome": "menu",
                        "total": 8,
                        "row_count": 8,
                        "argument_count": 16,
                        "item_type_low_byte": "0x04",
                    },
                }
            )
    write(
        SUITES / "sort-secondary-render-7.json",
        suite("rx3-track-sort-secondary-render-7", sort_render_7_cases),
    )

    def render_arguments_for_arity(arity: int) -> list:
        arguments: list = []
        if arity >= 4:
            arguments.append(0)
        if arity >= 5:
            arguments.append("$total")
        if arity >= 6:
            arguments.append(12)
        if arity >= 7:
            arguments.append(1)
        if arity >= 8:
            arguments.append(0)
        arguments.extend(f"0x900000{index:02x}" for index in range(9, arity + 1))
        return arguments

    render_arity_boundary_cases = []
    for arity in range(3, 33):
        render_arity_boundary_cases.append(
            {
                "id": f"default-arity-{arity:02}",
                "description": (
                    f"Default track sort followed by a total-{arity}-argument render"
                ),
                "request_kind": "0x1004",
                "arguments": [number("$context"), number(0)],
                "render_arguments": render_arguments_for_arity(arity),
                "fresh_connection": True,
                "page_size": 8,
                "expect": {"outcome": "any"},
            }
        )
    for arity in (3, 4, 9, 32):
        for sort_id, name in RX3_VISIBLE_SORTS[1:]:
            render_arity_boundary_cases.append(
                {
                    "id": f"{sort_id:02}-{name}-arity-{arity:02}",
                    "description": (
                        f"RX3 {name.replace('-', ' ').title()} track sort followed by "
                        f"a total-{arity}-argument render"
                    ),
                    "request_kind": "0x1004",
                    "arguments": [number("$context"), number(sort_id)],
                    "render_arguments": render_arguments_for_arity(arity),
                    "fresh_connection": True,
                    "page_size": 8,
                    "expect": {"outcome": "any"},
                }
            )
    write(
        SUITES / "render-arity-boundaries.json",
        suite("track-render-arity-boundaries", render_arity_boundary_cases),
    )

    render_underflow_cases = []
    for arity in range(3):
        render_underflow_cases.extend(
            (
                {
                    "id": f"warm-list-arity-{arity}",
                    "description": (
                        f"Materialize the Default track list before the total-{arity}-"
                        "argument render probe"
                    ),
                    "request_kind": "0x1004",
                    "arguments": [number("$context"), number(0)],
                    "render": False,
                    "fresh_connection": True,
                    "expect": {"outcome": "menu", "total": 8},
                },
                {
                    "id": f"render-arity-{arity}",
                    "description": (
                        f"Correctly framed 0x3000 with {arity} arguments after a valid "
                        "Default track list on the same connection"
                    ),
                    "request_kind": "0x3000",
                    "arguments": [
                        number(value)
                        for value in ("$context", 0)[:arity]
                    ],
                    "render": False,
                    "direct_response": True,
                    "raw_read_ms": 3000,
                    "expect": {"outcome": "any"},
                },
                {
                    "id": f"health-after-arity-{arity}",
                    "description": (
                        f"Fresh-connection Track health after the total-{arity}-argument "
                        "render probe"
                    ),
                    "request_kind": "0x1004",
                    "arguments": [number("$context"), number(0)],
                    "render": False,
                    "fresh_connection": True,
                    "expect": {"outcome": "menu", "total": 8},
                },
            )
        )
    write(
        SUITES / "render-arity-underflow.json",
        suite("track-render-arity-underflow", render_underflow_cases),
    )

    render_argument_type_entries = []
    render_argument_names = (
        "context",
        "offset",
        "count",
        "reserved",
        "total",
        "category",
        "override-gate",
        "override-selector",
    )
    normal_render_arguments = (
        number("$context"),
        number(0),
        number(8),
        number(0),
        number(8),
        number(12),
        number(1),
        number(0),
    )
    wrong_types = (
        ("string", {"string": "wrong-type"}),
        ("blob", {"blob_hex": "01020304"}),
    )
    for position, argument_name in enumerate(render_argument_names, start=1):
        for type_name, replacement in wrong_types:
            probe_id = f"argument-{position:02}-{argument_name}--{type_name}"
            arguments = list(normal_render_arguments)
            arguments[position - 1] = replacement
            cases = [
                {
                    "id": "warm-track-list",
                    "description": (
                        "Materialize a valid Default track list before the isolated "
                        f"render argument {position} {type_name} probe"
                    ),
                    "request_kind": "0x1004",
                    "arguments": [number("$context"), number(0)],
                    "render": False,
                    "fresh_connection": True,
                    "expect": {"outcome": "menu", "total": 8},
                },
                {
                    "id": probe_id,
                    "description": (
                        f"Eight-argument 0x3000 with {type_name} in position "
                        f"{position} ({argument_name})"
                    ),
                    "request_kind": "0x3000",
                    "arguments": arguments,
                    "render": False,
                    "direct_response": True,
                    "raw_read_ms": 3000,
                    "expect": {"outcome": "any"},
                },
            ]
            relative_suite = f"render-argument-types/{probe_id}.json"
            relative_golden = (
                "rekordbox-7.2.19/xdj-rx3/render-argument-types/"
                f"{probe_id}.json"
            )
            write(
                SUITES / relative_suite,
                suite(f"track-render-{probe_id}", cases),
            )
            render_argument_type_entries.append(
                {
                    "id": probe_id,
                    "position": position,
                    "argument": argument_name,
                    "wire_type": type_name,
                    "suite": f"suites/generated/{relative_suite}",
                    "golden": f"goldens/{relative_golden}",
                }
            )
    write(
        ROOT / "data/render-argument-type-matrix.json",
        {
            "format": 1,
            "scope": "Rekordbox track render argument type matrix",
            "position_count": len(render_argument_names),
            "wire_types": [name for name, _ in wrong_types],
            "probe_count": len(render_argument_type_entries),
            "case_count": len(render_argument_type_entries) * 2,
            "probes": render_argument_type_entries,
        },
    )

    render_numeric_cases = [
        {
            "id": "control",
            "description": "Normal eight-argument Default Track render",
            "request_kind": "0x1004",
            "arguments": [number("$context"), number(0)],
            "render_arguments": [0, 8, 12, 1, 0],
            "fresh_connection": True,
            "page_size": 8,
            "expect": {"outcome": "any"},
        }
    ]
    first_row_seek_values = (
        ("one", 1),
        ("two", 2),
        ("space", "0x00000020"),
        ("digit-zero", "0x00000030"),
        ("before-a", "0x00000040"),
        ("a", "0x00000041"),
        ("b", "0x00000042"),
        ("m", "0x0000004d"),
        ("u", "0x00000055"),
        ("z", "0x0000005a"),
        ("lowercase-a", "0x00000061"),
        ("low-fffe", "0x0000fffe"),
        ("low-ffff", "0x0000ffff"),
        ("high-only", "0x00010000"),
        ("high-plus-a", "0x00010041"),
    )
    for name, value in first_row_seek_values:
        render_numeric_cases.append(
            {
                "id": f"first-row-seek-{name}",
                "description": f"Render first-row seek key {value}",
                "request_kind": "0x1004",
                "arguments": [number("$context"), number(0)],
                "render_arguments": [value, 8, 12, 1, 0],
                "fresh_connection": True,
                "page_size": 8,
                "expect": {"outcome": "any"},
            }
        )
    client_total_values = (0, 1, 7, 9, "0x0000ffff", "0xffffffff")
    for value in client_total_values:
        name = str(value).removeprefix("0x")
        render_numeric_cases.append(
            {
                "id": f"client-total-{name}",
                "description": f"Render client-reported total {value}",
                "request_kind": "0x1004",
                "arguments": [number("$context"), number(0)],
                "render_arguments": [0, value, 12, 1, 0],
                "fresh_connection": True,
                "page_size": 8,
                "expect": {"outcome": "any"},
            }
        )
    category_id_values = (
        0,
        1,
        7,
        15,
        20,
        24,
        25,
        29,
        30,
        32,
        33,
        39,
        40,
        49,
        50,
        51,
        52,
        "0x0000ffff",
        "0x0001000c",
        "0xffffffff",
    )
    for value in category_id_values:
        name = str(value).removeprefix("0x")
        render_numeric_cases.append(
            {
                "id": f"category-id-{name}",
                "description": f"Render category ID {value}",
                "request_kind": "0x1004",
                "arguments": [number("$context"), number(0)],
                "render_arguments": [0, 8, value, 1, 0],
                "fresh_connection": True,
                "page_size": 8,
                "expect": {"outcome": "any"},
            }
        )
    write(
        SUITES / "render-numeric-fields.json",
        suite("track-render-numeric-fields", render_numeric_cases),
    )

    render_override_cases = [
        {
            "id": "control",
            "description": "Normal eight-argument Artist override",
            "request_kind": "0x1004",
            "arguments": [number("$context"), number(0)],
            "render_arguments": [0, 8, 12, 1, 2],
            "fresh_connection": True,
            "page_size": 8,
            "expect": {"outcome": "any"},
        }
    ]
    override_gate_values = (
        ("zero", 0),
        ("two", 2),
        ("signed-max", "0x7fffffff"),
        ("high-bit", "0x80000000"),
        ("uint32-max", "0xffffffff"),
    )
    for name, value in override_gate_values:
        render_override_cases.append(
            {
                "id": f"override-gate-{name}",
                "description": f"Render secondary override gate {value}",
                "request_kind": "0x1004",
                "arguments": [number("$context"), number(0)],
                "render_arguments": [0, 8, 12, value, 2],
                "fresh_connection": True,
                "page_size": 8,
                "expect": {"outcome": "any"},
            }
        )
    override_selector_values = (
        ("zero", 0),
        ("one", 1),
        ("hole-14", 14),
        ("upper-valid-17", 17),
        ("first-outside-18", 18),
        ("low-byte-ff", "0x000000ff"),
        ("low-byte-wrap", "0x00000100"),
        ("high-word-artist", "0x00010002"),
        ("signed-max", "0x7fffffff"),
        ("high-bit", "0x80000000"),
        ("uint32-max", "0xffffffff"),
    )
    for name, value in override_selector_values:
        render_override_cases.append(
            {
                "id": f"override-selector-{name}",
                "description": f"Render secondary override selector {value}",
                "request_kind": "0x1004",
                "arguments": [number("$context"), number(0)],
                "render_arguments": [0, 8, 12, 1, value],
                "fresh_connection": True,
                "page_size": 8,
                "expect": {"outcome": "any"},
            }
        )
    write(
        SUITES / "render-override-controls.json",
        suite("track-render-override-controls", render_override_cases),
    )

    malformed_history_timing_root = SUITES / "song-info-location2-malformed-history-timing"
    for delay_ms in (0, 50, 100, 250, 500, 1000, 3000):
        cases = [
            {
                "id": "first--play-extra-argument",
                "description": "First malformed precursor: Play Song Info with an extra number",
                "request_kind": "0x2102",
                "arguments": [
                    number("$context"),
                    number("$fixture.track.first"),
                    number("0xdeadbeef"),
                ],
                "render": False,
                "fresh_connection": True,
                "expect": {"outcome": "any"},
            },
            {
                "id": "second--delivery-blob-content",
                "description": "Second malformed precursor: Delivery Song Info with blob content ID",
                "request_kind": "0x2602",
                "arguments": [number("$context"), {"blob_hex": "01020304"}],
                "render": False,
                "fresh_connection": True,
                "expect": {"outcome": "any"},
            },
            {
                "id": "delivery-probe",
                "description": (
                    "Matched RX3 location-2 Delivery after both malformed precursors "
                    f"and a {delay_ms} ms pre-connection delay"
                ),
                "request_kind": "0x2602",
                "arguments": [number("0x0b020301"), number("$fixture.track.first")],
                "render": False,
                "fresh_connection": True,
                "delay_before_connection_ms": delay_ms,
                "expect": {"outcome": "any"},
            },
        ]
        suite_document = suite(
            f"song-info-location2-malformed-history-timing--probe-delay-{delay_ms:04}ms",
            cases,
        )
        suite_document["defaults"]["device"] = 11
        suite_document["defaults"]["context"] = "0x0b010301"
        write(
            malformed_history_timing_root / f"probe-delay-{delay_ms:04}ms.json",
            suite_document,
        )

    delayed_reply_root = SUITES / "song-info-delayed-reply-routing"
    for filename, document in song_info_delayed_reply_routing_suites():
        write(delayed_reply_root / filename, document)

    context_cases = []
    for player in range(1, 7):
        context_cases.append(
            {
                "id": f"player-{player}",
                "description": f"Requester/player byte {player}",
                "request_kind": "0x1004",
                "arguments": [number(f"0x{player:02x}010301"), number("$sort")],
                "fresh_connection": True,
                "expect": {"outcome": "any"},
            }
        )
    for location in range(1, 9):
        context_cases.append(
            {
                "id": f"location-{location}",
                "description": f"Menu-location candidate byte {location}",
                "request_kind": "0x1004",
                "arguments": [number(f"0x01{location:02x}0301"), number("$sort")],
                "fresh_connection": True,
                "expect": {"outcome": "any"},
            }
        )
    for slot in range(0, 5):
        context_cases.append(
            {
                "id": f"slot-{slot}",
                "description": f"Media-slot candidate byte {slot}",
                "request_kind": "0x1004",
                "arguments": [number(f"0x0101{slot:02x}01"), number("$sort")],
                "fresh_connection": True,
                "expect": {"outcome": "any"},
            }
        )
    write(SUITES / "contexts.json", suite("packed-context-sweep", context_cases))

    for arity, tail in ((5, [0, "$total"]), (6, [0, "$total", 12]), (8, [0, "$total", 12, 1, 0])):
        case = {
            "id": f"render-{arity}",
            "description": f"Track rendering with {arity} request arguments",
            "request_kind": "0x1004",
            "arguments": [number("$context"), number("$sort")],
            "expect": {
                "outcome": "menu",
                "item_type": "0x0f04",
            },
        }
        write(SUITES / f"render-{arity}.json", suite(f"render-arity-{arity}", [case], render_arguments=tail))

    secondary_control_cases = [
        {
            "id": "database-selection-zero-gate",
            "description": "A zero override gate retains the database-selected secondary column",
            "request_kind": "0x1004",
            "arguments": [number("$context"), number("$sort")],
            "render_arguments": [0, "$total", 12, 0, 0],
            "expect": {"outcome": "menu", "item_type": "0x0f04"},
        },
        {
            "id": "override-disabled-with-zero-gate",
            "description": "A zero gate ignores a nonzero override and retains the database selection",
            "request_kind": "0x1004",
            "arguments": [number("$context"), number("$sort")],
            "render_arguments": [0, "$total", 12, 0, 7],
            "expect": {"outcome": "menu", "item_type": "0x0f04"},
        },
        {
            "id": "database-selection",
            "description": "Eight-argument render uses the database-selected Key column",
            "request_kind": "0x1004",
            "arguments": [number("$context"), number("$sort")],
            "render_arguments": [0, "$total", 12, 1, 0],
            "expect": {"outcome": "menu", "item_type": "0x0f04"},
        },
    ]
    for sort_id in range(2, 18):
        expected = {"outcome": "menu", "item_type_low_byte": "0x04"}
        expected.update(track_argument_expectations(sort_id))
        if sort_id == 15:
            expected["item_type_high_bytes"] = [f"0x{value:02x}" for value in range(0x13, 0x1C)]
        else:
            expected["item_type"] = f"0x{SECONDARY_TYPE_BYTES[sort_id]:02x}04"
        secondary_control_cases.append(
            {
                "id": f"override-{sort_id:02}",
                "description": f"Render argument 8 overrides the secondary selector with sort ID {sort_id}",
                "request_kind": "0x1004",
                "arguments": [number("$context"), number("$sort")],
                "render_arguments": [0, "$total", 12, 1, sort_id],
                "expect": expected,
            }
        )
    write(
        SUITES / "render-secondary-controls.json",
        suite("render-secondary-controls", secondary_control_cases),
    )

    selection_states = {
        "no-secondary-selection": {
            "selected": [],
            "expect": {"outcome": "menu", "item_type": "0x0004"},
        },
        "multiple-secondary-selections": {
            "selected": [7, 12],
            "expect": {
                "outcome": "menu",
                "item_type_low_byte": "0x04",
                "item_type_high_bytes": ["0x0f", "0x23"],
            },
        },
    }
    for name, state in selection_states.items():
        write(
            SETTINGS / f"{name}.json",
            {
                "name": name,
                "secondary_sorts": state["selected"],
            },
        )
        write(
            SUITES / f"{name}.json",
            settings_suite(
                name,
                {
                    "id": "track-rows",
                    "description": f"Database-selected secondary state: {name}",
                    "request_kind": "0x1004",
                    "arguments": [number("$context"), number("$sort")],
                    "expect": state["expect"],
                },
            ),
        )

    for sort_id, name in SECONDARIES.items():
        write(
            SETTINGS / f"secondary-{name}.json",
            {
                "name": f"secondary-{name}",
                "secondary_sort": sort_id,
                "sort": {str(sort_id): {"enabled": True, "seq": 20}},
            },
        )
        secondary_suite = suite(
            f"secondary-column-{name}",
            [
                {
                    "id": "sort-menu",
                    "description": f"Sort visibility with {name} selected as the secondary column",
                    "request_kind": "0x1400",
                    "arguments": [number("$context"), number(0), number(0)],
                    "expect": {"outcome": "any"},
                },
                {
                    "id": "track-rows",
                    "description": f"Complete track rendering with {name} secondary values",
                    "request_kind": "0x1004",
                    "arguments": [number("$context"), number("$sort")],
                    "expect": {
                        "outcome": "menu",
                        "total": 8,
                        "row_count": 8,
                        "argument_count": 16,
                        **track_argument_expectations(sort_id),
                    },
                },
            ],
        )
        secondary_suite["fixture_profile"] = "settings"
        secondary_suite["fixture_variant"] = f"secondary-{name}"
        write(SUITES / f"secondary-{name}.json", secondary_suite)

        legacy_suite = copy.deepcopy(secondary_suite)
        legacy_suite["name"] = f"secondary-column-{name}-legacy"
        legacy_suite["defaults"]["setup"] = "legacy"
        for case in legacy_suite["cases"]:
            if case["id"] == "track-rows":
                case["expect"]["argument_count"] = 12
                argument_expectations = case["expect"].get("row_argument_any_of", {})
                case["expect"]["row_argument_any_of"] = {
                    index: values
                    for index, values in argument_expectations.items()
                    if int(index) < 12
                }
        write(SUITES / f"secondary-{name}-legacy.json", legacy_suite)

    for category_id in CATEGORY_IDS:
        name = f"category-{category_id:02}-disabled"
        write(
            SETTINGS / f"{name}.json",
            {
                "name": name,
                "secondary_sort": 12,
                "category": {str(category_id): {"disable": 1}},
            },
        )
        category_suite = settings_suite(
            name,
            {
                "id": "root",
                "description": f"Root menu with persisted category row {category_id} disabled",
                "request_kind": "0x1000",
                "arguments": [
                    number("$context"),
                    number("$sort"),
                    number("$root_capabilities"),
                ],
                "expect": {"outcome": "menu"},
            },
        )
        category_suite["cases"].append(
            {
                "id": "display-song-info",
                "description": (
                    "Display Song Info with persisted category row "
                    f"{category_id} disabled"
                ),
                "request_kind": "0x2002",
                "arguments": [
                    number("$context"),
                    number("$fixture.track.first"),
                ],
                "expect": {"outcome": "menu"},
            }
        )
        write(SUITES / f"{name}.json", category_suite)

    category_order = {
        str(category_id): {"seq": seq}
        for seq, category_id in enumerate(reversed(CATEGORY_IDS), start=1)
    }
    write(
        SETTINGS / "category-order-reversed.json",
        {
            "name": "category-order-reversed",
            "secondary_sort": 12,
            "category": category_order,
        },
    )
    write(
        SUITES / "category-order-reversed.json",
        settings_suite(
            "category-order-reversed",
            {
                "id": "root",
                "description": "Root rows follow the complete reversed persisted category order",
                "request_kind": "0x1000",
                "arguments": [
                    number("$context"),
                    number("$sort"),
                    number("$root_capabilities"),
                ],
                "expect": {"outcome": "menu"},
            },
        ),
    )

    for sort_id, enabled in SORT_STATES.items():
        name = f"sort-{sort_id:02}-toggled"
        write(
            SETTINGS / f"{name}.json",
            {
                "name": name,
                "secondary_sort": 12,
                "sort": {str(sort_id): {"enabled": not enabled}},
            },
        )
        write(
            SUITES / f"{name}.json",
            settings_suite(
                name,
                {
                    "id": "sort-menu",
                    "description": f"Sort menu with persisted sort row {sort_id} visibility toggled",
                    "request_kind": "0x1400",
                    "arguments": [number("$context"), number(0), number(0)],
                    "expect": {"outcome": "menu"},
                },
            ),
        )

    sort_order = {
        str(sort_id): {"seq": seq}
        for seq, sort_id in enumerate(reversed(tuple(SORT_STATES)), start=1)
    }
    write(
        SETTINGS / "sort-order-reversed.json",
        {
            "name": "sort-order-reversed",
            "secondary_sort": 12,
            "sort": sort_order,
        },
    )
    write(
        SUITES / "sort-order-reversed.json",
        settings_suite(
            "sort-order-reversed",
            {
                "id": "sort-menu",
                "description": "Sort rows follow the complete reversed persisted order",
                "request_kind": "0x1400",
                "arguments": [number("$context"), number(0), number(0)],
                "expect": {"outcome": "menu"},
            },
        ),
    )

    display_arguments = [number("$context"), number("$fixture.track.first")]
    render_controls = [
        ("arity-5", "Five-argument render", [0, "$total"]),
        ("arity-6", "Six-argument render", [0, "$total", 12]),
        ("database-selection-zero-gate", "Zero gate with database selection", [0, "$total", 12, 0, 0]),
        ("override-disabled-with-zero-gate", "Zero gate with nonzero override", [0, "$total", 12, 0, 7]),
        ("database-selection", "Eight-argument render with database selection", [0, "$total", 12, 1, 0]),
    ]
    render_controls.extend(
        (
            f"override-{sort_id:02}",
            f"Render-time secondary selector override {sort_id}",
            [0, "$total", 12, 1, sort_id],
        )
        for sort_id in range(2, 18)
    )
    write(
        SUITES / "display-song-info-render.json",
        suite(
            "display-song-info-render",
            [
                {
                    "id": case_id,
                    "description": description,
                    "request_kind": "0x2002",
                    "arguments": display_arguments,
                    "render_arguments": render_arguments,
                    "expect": {
                        "outcome": "menu",
                        "total": 16,
                        "row_count": 16,
                        "argument_count": 16,
                    },
                }
                for case_id, description, render_arguments in render_controls
            ],
        ),
    )

    pagination_plans = (
        ("one-row-pages", "Complete display list one row at a time", None, 1),
        ("single-complete-page", "One exact-size display page", [{"offset": 0, "count": "$total"}], None),
        ("last-row", "Final valid display row", [{"offset": 15, "count": 1}], None),
        ("zero-count", "Zero-count display render", [{"offset": 0, "count": 0}], None),
        ("at-end", "Display render exactly at total", [{"offset": "$total", "count": 1}], None),
        ("past-end", "Display render beyond total", [{"offset": 17, "count": 1}], None),
        ("overrun", "Display render overruns from final row", [{"offset": 15, "count": 18}], None),
        ("overlap", "Overlapping display windows", [{"offset": 0, "count": 3}, {"offset": 2, "count": 3}], None),
        ("maximum-offset", "Maximum unsigned display offset", [{"offset": "0xffffffff", "count": 1}], None),
    )
    pagination_cases = []
    for case_id, description, render_pages, page_size in pagination_plans:
        case = {
            "id": case_id,
            "description": description,
            "request_kind": "0x2002",
            "arguments": display_arguments,
            "expect": {"outcome": "any", "total": 16},
        }
        if render_pages is not None:
            case["render_pages"] = render_pages
        if page_size is not None:
            case["page_size"] = page_size
        pagination_cases.append(case)
    write(
        SUITES / "display-song-info-pagination.json",
        suite("display-song-info-pagination", pagination_cases),
    )

    display_error_cases = [
        ("no-arguments", "Display request with no arguments", []),
        ("missing-content", "Display request with content ID omitted", [number("$context")]),
        ("extra-argument", "Display request with an extra number", display_arguments + [number("0xdeadbeef")]),
        ("string-context", "Display request with string context", [{"string": "wrong-type"}, number("$fixture.track.first")]),
        ("blob-context", "Display request with blob context", [{"blob_hex": "01020304"}, number("$fixture.track.first")]),
        ("string-content", "Display request with string content ID", [number("$context"), {"string": "wrong-type"}]),
        ("blob-content", "Display request with blob content ID", [number("$context"), {"blob_hex": "01020304"}]),
        ("zero-context", "Display request with zero context", [number(0), number("$fixture.track.first")]),
        ("alternate-location", "Display request at menu location 2", [number("0x01020301"), number("$fixture.track.first")]),
    ]
    write(
        SUITES / "display-song-info-errors.json",
        suite(
            "display-song-info-errors",
            [
                {
                    "id": case_id,
                    "description": description,
                    "request_kind": "0x2002",
                    "arguments": arguments,
                    "render": False,
                    "fresh_connection": True,
                    "expect": {"outcome": "any"},
                }
                for case_id, description, arguments in display_error_cases
            ],
        ),
    )

    display_legacy = suite(
        "display-song-info-legacy",
        [
            {
                "id": "populated-track",
                "description": "Legacy Display Song Info row width",
                "request_kind": "0x2002",
                "arguments": display_arguments,
                "expect": {
                    "outcome": "menu",
                    "total": 16,
                    "row_count": 16,
                    "argument_count": 12,
                },
            },
            {
                "id": "deleted-track",
                "description": "Legacy Display Song Info for deleted content",
                "request_kind": "0x2002",
                "arguments": [number("$context"), number("$fixture.track.deleted")],
                "expect": {"outcome": "menu", "total": 0, "row_count": 0},
            },
            {
                "id": "zero-content-id",
                "description": "Legacy Display Song Info for content ID zero",
                "request_kind": "0x2002",
                "arguments": [number("$context"), number(0)],
                "expect": {"outcome": "menu", "total": 0, "row_count": 0},
            },
            {
                "id": "unknown-content-id",
                "description": "Legacy Display Song Info for unknown content",
                "request_kind": "0x2002",
                "arguments": [number("$context"), number("0xfffffffe")],
                "expect": {"outcome": "menu", "total": 0, "row_count": 0},
            },
        ],
    )
    display_legacy["defaults"]["setup"] = "legacy"
    write(SUITES / "display-song-info-legacy.json", display_legacy)

    display_boundary_profiles = (
        (
            "display-song-info-boundaries",
            "boundaries",
            "numeric, lookup-string, Comment, and Date Added boundary",
        ),
        (
            "display-song-info-unicode-boundaries",
            "unicode-boundaries",
            "supplementary-Unicode Comment and Date Added boundary",
        ),
        (
            "display-song-info-invalid",
            "invalid",
            "null, empty, dangling, negative, and invalid-enum",
        ),
    )
    track_symbols = (
        "first",
        "second",
        "third",
        "fourth",
        "fifth",
        "sixth",
        "seventh",
        "eighth",
    )
    for name, profile, description in display_boundary_profiles:
        boundary_suite = suite(
            name,
            [
                {
                    "id": f"track-{index:02}",
                    "description": f"Display Song Info {description} track {index}",
                    "request_kind": "0x2002",
                    "arguments": [
                        number("$context"),
                        number(f"$fixture.track.{symbol}"),
                    ],
                    "fresh_connection": True,
                    "expect": {"outcome": "any"},
                }
                for index, symbol in enumerate(track_symbols, start=1)
            ],
        )
        boundary_suite["fixture_profile"] = profile
        write(SUITES / f"{name}.json", boundary_suite)

    display_string_profiles = (
        ("display-song-info-strings-254", "display-strings-254", "254 ASCII characters"),
        ("display-song-info-strings-255", "display-strings-255", "255 ASCII characters"),
        ("display-song-info-strings-256", "display-strings-256", "256 ASCII characters"),
        (
            "display-song-info-strings-unicode-256",
            "display-strings-unicode-256",
            "128 supplementary characters / 256 UTF-16 code units",
        ),
    )
    for name, profile, description in display_string_profiles:
        string_suite = suite(
            name,
            [
                {
                    "id": "track-01",
                    "description": f"Every Display Song Info string source at {description}",
                    "request_kind": "0x2002",
                    "arguments": display_arguments,
                    "fresh_connection": True,
                    "expect": {"outcome": "any"},
                }
            ],
        )
        string_suite["fixture_profile"] = profile
        write(SUITES / f"{name}.json", string_suite)

    display_status_identities = (
        ("xdj-xz", 11),
        ("xdj-az", 11),
        ("xdj-1000mk2", 11),
        ("unknown-mixer", 1),
        ("cdj-2000nexus", 1),
    )
    for model, player in display_status_identities:
        status_suite = suite(
            f"display-song-info-status-{model}",
            [
                {
                    "id": "populated-track",
                    "description": f"Display Song Info populated row order for {model}",
                    "request_kind": "0x2002",
                    "arguments": display_arguments,
                    "fresh_connection": True,
                    "expect": {"outcome": "any"},
                },
                {
                    "id": "deleted-track",
                    "description": f"Display Song Info deleted content for {model}",
                    "request_kind": "0x2002",
                    "arguments": [number("$context"), number("$fixture.track.deleted")],
                    "fresh_connection": True,
                    "expect": {"outcome": "any"},
                },
                {
                    "id": "zero-content-id",
                    "description": f"Display Song Info zero content ID for {model}",
                    "request_kind": "0x2002",
                    "arguments": [number("$context"), number(0)],
                    "fresh_connection": True,
                    "expect": {"outcome": "any"},
                },
                {
                    "id": "unknown-content-id",
                    "description": f"Display Song Info unknown content for {model}",
                    "request_kind": "0x2002",
                    "arguments": [number("$context"), number("0xfffffffe")],
                    "fresh_connection": True,
                    "expect": {"outcome": "any"},
                },
            ],
        )
        status_suite["defaults"]["context"] = f"0x{player:02x}010301"
        write(SUITES / f"display-song-info-status-{model}.json", status_suite)

    song_info_content_ids = (
        ("populated-track", "$fixture.track.first", "populated content"),
        ("deleted-track", "$fixture.track.deleted", "soft-deleted content"),
        ("zero-content-id", 0, "content ID zero"),
        ("unknown-content-id", "0xfffffffe", "unknown content ID"),
    )
    song_info_request_kinds = (
        ("play", "0x2102"),
        ("non-rekordbox", "0x2202"),
        ("recognized-23", "0x2302"),
        ("recognized-24", "0x2402"),
        ("recognized-25", "0x2502"),
        ("delivery", "0x2602"),
    )
    song_info_sibling_cases = []
    for kind_name, request_kind in song_info_request_kinds:
        for content_name, content_id, content_description in song_info_content_ids:
            song_info_sibling_cases.append(
                {
                    "id": f"{kind_name}-{content_name}",
                    "description": (
                        f"Song-information sibling {request_kind} with "
                        f"{content_description}"
                    ),
                    "request_kind": request_kind,
                    "arguments": [number("$context"), number(content_id)],
                    "fresh_connection": True,
                    "expect": {"outcome": "any"},
                }
            )
    song_info_siblings = suite("song-info-siblings", song_info_sibling_cases)
    write(SUITES / "song-info-siblings.json", song_info_siblings)

    play_path_descriptions = (
        "null link/cloud identifiers and missing original path",
        "zero link/cloud identifiers, empty path, zero size, and empty hot-cue flag",
        "ContentLink bit 7, negative service, negative size, null hot-cue flag, and existing original file",
        "ContentLink bits 7+0, maximum signed size, nonempty OFF hot-cue flag, and existing original directory",
        "cloud service 1, matching MasterDBID, and existing original file",
        "cloud service 1, mismatched MasterDBID, and existing original directory",
        "cloud service 2, matching MasterDBID, missing original path, and maximum unsigned size",
        "maximum signed cloud service, null MasterDBID, empty original path, Unicode filename, and 2^32 size",
        "local path, null file size, and empty hot-cue flag",
        "null local path with an existing original file",
        "cloud service 1, matching MasterDBID, and existing original directory",
        "cloud service 1, matching MasterDBID, and existing zero-byte original file",
        "ContentLink zero paired control",
        "ContentLink bit 7 paired control",
    )
    play_path_symbols = track_symbols + (
        "ninth",
        "tenth",
        "eleventh",
        "twelfth",
        "thirteenth",
        "fourteenth",
    )
    play_path_cases = [
        {
            "id": f"track-{index:02}",
            "description": f"Play Song Info path branch: {description}",
            "request_kind": "0x2102",
            "arguments": [
                number("$context"),
                number(f"$fixture.track.{symbol}"),
            ],
            "fresh_connection": True,
            "expect": {"outcome": "any"},
        }
        for index, (symbol, description) in enumerate(
            zip(play_path_symbols, play_path_descriptions, strict=True), start=1
        )
    ]
    play_paths = suite("song-info-play-paths", play_path_cases)
    play_paths["fixture_profile"] = "play-paths"
    play_paths["repeat_strategy"] = "fixture-reset-and-restart"
    write(SUITES / "song-info-play-paths.json", play_paths)

    delivery_boundary_descriptions = (
        "null Delivery-only fields",
        "empty Delivery-only fields",
        "126 ASCII characters and DeliveryControl OFF",
        "127 ASCII characters and DeliveryControl ON",
        "128 ASCII characters and lowercase DeliveryControl on",
        "126 UTF-16 units and mixed-case DeliveryControl Off",
        "127 UTF-16 units and dangling ComposerID",
        "128 UTF-16 units and DeliveryControl ON",
    )
    delivery_boundary_cases = [
        {
            "id": f"track-{index:02}",
            "description": f"Delivery Info with {description}",
            "request_kind": "0x2602",
            "arguments": [
                number("$context"),
                number(f"$fixture.track.{symbol}"),
            ],
            "fresh_connection": True,
            "expect": {"outcome": "any"},
        }
        for index, (symbol, description) in enumerate(
            zip(track_symbols, delivery_boundary_descriptions, strict=True), start=1
        )
    ]
    delivery_boundaries = suite(
        "song-info-delivery-boundaries", delivery_boundary_cases
    )
    delivery_boundaries["fixture_profile"] = "delivery-boundaries"
    delivery_boundaries["repeat_strategy"] = "fixture-reset-and-restart"
    write(SUITES / "song-info-delivery-boundaries.json", delivery_boundaries)

    delivery_wide_descriptions = (
        "254 ASCII characters",
        "255 ASCII characters",
        "256 ASCII characters",
        "252 UTF-16 units",
        "254 UTF-16 units",
        "255 UTF-16 units",
        "256 UTF-16 units",
        "257 UTF-16 units",
    )
    delivery_wide_cases = [
        {
            "id": f"track-{index:02}",
            "description": f"Delivery Info direct strings at {description}",
            "request_kind": "0x2602",
            "arguments": [
                number("$context"),
                number(f"$fixture.track.{symbol}"),
            ],
            "fresh_connection": True,
            "expect": {"outcome": "any"},
        }
        for index, (symbol, description) in enumerate(
            zip(track_symbols, delivery_wide_descriptions, strict=True), start=1
        )
    ]
    delivery_wide = suite("song-info-delivery-wide-strings", delivery_wide_cases)
    delivery_wide["fixture_profile"] = "delivery-wide-strings"
    delivery_wide["repeat_strategy"] = "fixture-reset-and-restart"
    write(SUITES / "song-info-delivery-wide-strings.json", delivery_wide)

    sibling_builders = (
        ("play", "0x2102", 7),
        ("delivery", "0x2602", 13),
    )
    sibling_render_cases = []
    for kind_name, request_kind, total in sibling_builders:
        for case_id, description, render_arguments in render_controls:
            sibling_render_cases.append(
                {
                    "id": f"{kind_name}-{case_id}",
                    "description": f"{kind_name.title()} Song Info: {description}",
                    "request_kind": request_kind,
                    "arguments": display_arguments,
                    "render_arguments": render_arguments,
                    "expect": {"outcome": "any", "total": total},
                }
            )
    write(
        SUITES / "song-info-sibling-render.json",
        suite("song-info-sibling-render", sibling_render_cases),
    )

    repeated_delivery_cases = [
        {
            "id": f"repeat-{index:02}",
            "description": f"Identical Delivery Info request at position {index}",
            "request_kind": "0x2602",
            "arguments": display_arguments,
            "fresh_connection": True,
            "expect": {"outcome": "any"},
        }
        for index in range(1, 17)
    ]
    write(
        ORDER_EXPERIMENTS / "repeated-identical-suite.json",
        suite("song-info-delivery-repeated-identical", repeated_delivery_cases),
    )

    def delivery_control_case(control) -> dict[str, object]:
        case_id, description, render_arguments = control
        return {
            "id": case_id,
            "description": f"Delivery-only order probe: {description}",
            "request_kind": "0x2602",
            "arguments": display_arguments,
            "render_arguments": render_arguments,
            "fresh_connection": True,
            "expect": {"outcome": "any"},
        }

    write(
        ORDER_EXPERIMENTS / "controls-forward-suite.json",
        suite(
            "song-info-delivery-controls-forward",
            [delivery_control_case(control) for control in render_controls],
        ),
    )
    write(
        ORDER_EXPERIMENTS / "controls-reversed-suite.json",
        suite(
            "song-info-delivery-controls-reversed",
            [delivery_control_case(control) for control in reversed(render_controls)],
        ),
    )

    family_precursors = (
        ("play-populated", "0x2102", "$fixture.track.first"),
        ("display-populated", "0x2002", "$fixture.track.first"),
        ("play-missing", "0x2102", "0xfffffffe"),
        ("display-missing", "0x2002", "0xfffffffe"),
        ("delivery-missing", "0x2602", "0xfffffffe"),
        ("recognized-error", "0x2202", "$fixture.track.first"),
    )
    for precursor_name, precursor_kind, precursor_content in family_precursors:
        for connection_name, fresh_connection in (
            ("", True),
            ("-same-connection", False),
        ):
            family_cases = []
            for iteration in range(1, 9):
                family_cases.extend(
                    (
                        {
                            "id": f"{iteration:02}-{precursor_name}",
                            "description": (
                                f"Iteration {iteration}: {precursor_name} precursor"
                            ),
                            "request_kind": precursor_kind,
                            "arguments": [
                                number("$context"),
                                number(precursor_content),
                            ],
                            "fresh_connection": fresh_connection,
                            "expect": {"outcome": "any"},
                        },
                        {
                            "id": f"{iteration:02}-delivery-probe",
                            "description": (
                                f"Iteration {iteration}: Delivery after {precursor_name}"
                            ),
                            "request_kind": "0x2602",
                            "arguments": display_arguments,
                            "fresh_connection": fresh_connection,
                            "expect": {"outcome": "any"},
                        },
                    )
                )
            write(
                ORDER_EXPERIMENTS
                / f"family-{precursor_name}{connection_name}-suite.json",
                suite(
                    f"song-info-delivery-family-{precursor_name}{connection_name}",
                    family_cases,
                ),
            )

    for lifecycle_name, case_count in (
        ("identity-warmup-six", 6),
        ("identity-post-rejoin-eight", 8),
    ):
        write(
            ORDER_EXPERIMENTS / f"{lifecycle_name}-suite.json",
            suite(
                f"song-info-delivery-{lifecycle_name}",
                [
                    {
                        "id": f"delivery-{index:02}",
                        "description": (
                            f"Delivery identity-lifecycle probe {index} of "
                            f"{case_count}"
                        ),
                        "request_kind": "0x2602",
                        "arguments": display_arguments,
                        "fresh_connection": True,
                        "expect": {"outcome": "any"},
                    }
                    for index in range(1, case_count + 1)
                ],
            ),
        )

    sibling_pagination_cases = []
    for kind_name, request_kind, total in sibling_builders:
        sibling_plans = (
            ("one-row-pages", None, 1),
            ("single-complete-page", [{"offset": 0, "count": "$total"}], None),
            ("last-row", [{"offset": total - 1, "count": 1}], None),
            ("zero-count", [{"offset": 0, "count": 0}], None),
            ("at-end", [{"offset": "$total", "count": 1}], None),
            ("past-end", [{"offset": total + 1, "count": 1}], None),
            ("overrun", [{"offset": total - 1, "count": total + 2}], None),
            ("overlap", [{"offset": 0, "count": 3}, {"offset": 2, "count": 3}], None),
            ("maximum-offset", [{"offset": "0xffffffff", "count": 1}], None),
        )
        for case_id, render_pages, page_size in sibling_plans:
            case = {
                "id": f"{kind_name}-{case_id}",
                "description": f"{kind_name.title()} Song Info pagination: {case_id}",
                "request_kind": request_kind,
                "arguments": display_arguments,
                "expect": {"outcome": "any", "total": total},
            }
            if render_pages is not None:
                case["render_pages"] = render_pages
            if page_size is not None:
                case["page_size"] = page_size
            sibling_pagination_cases.append(case)
    write(
        SUITES / "song-info-sibling-pagination.json",
        suite("song-info-sibling-pagination", sibling_pagination_cases),
    )

    sibling_error_cases = []
    for kind_name, request_kind, _ in sibling_builders:
        for case_id, description, arguments in display_error_cases:
            if kind_name == "delivery" and case_id == "zero-context":
                continue
            sibling_error_cases.append(
                {
                    "id": f"{kind_name}-{case_id}",
                    "description": f"{kind_name.title()} Song Info: {description}",
                    "request_kind": request_kind,
                    "arguments": arguments,
                    "render": False,
                    "fresh_connection": True,
                    "expect": {"outcome": "any"},
                }
            )
    write(
        SUITES / "song-info-sibling-errors.json",
        suite("song-info-sibling-errors", sibling_error_cases),
    )

    zero_context_audit_cases = []
    for iteration in range(1, 11):
        for kind_name, request_kind, _ in sibling_builders:
            zero_context_audit_cases.append(
                {
                    "id": f"{iteration:02}-{kind_name}-zero-context",
                    "description": (
                        f"Iteration {iteration}: {kind_name.title()} Song Info "
                        "with numeric zero context"
                    ),
                    "request_kind": request_kind,
                    "arguments": [number(0), number("$fixture.track.first")],
                    "render": False,
                    "fresh_connection": True,
                    "expect": {"outcome": "any"},
                }
            )
    write(
        EXPERIMENTS / "zero-context-audit-suite.json",
        suite("song-info-zero-context-audit", zero_context_audit_cases),
    )
    zero_context_sequence = (
        ("01-play-zero-cold", "0x2102", 0),
        ("02-delivery-zero-cold", "0x2602", 0),
        ("03-play-valid", "0x2102", "$context"),
        ("04-play-zero-after-play", "0x2102", 0),
        ("05-delivery-zero-after-play", "0x2602", 0),
        ("06-delivery-valid", "0x2602", "$context"),
        ("07-play-zero-after-delivery", "0x2102", 0),
        ("08-delivery-zero-after-delivery", "0x2602", 0),
        ("09-display-valid", "0x2002", "$context"),
        ("10-play-zero-after-display", "0x2102", 0),
        ("11-delivery-zero-after-display", "0x2602", 0),
    )
    write(
        EXPERIMENTS / "zero-context-sequence-suite.json",
        suite(
            "song-info-zero-context-sequence",
            [
                {
                    "id": case_id,
                    "description": f"Zero-context sequence step {case_id}",
                    "request_kind": request_kind,
                    "arguments": [number(context), number("$fixture.track.first")],
                    "render": False,
                    "fresh_connection": True,
                    "expect": {"outcome": "any"},
                }
                for case_id, request_kind, context in zero_context_sequence
            ],
        ),
    )
    zero_context_prefix_cases = []
    for kind_name, request_kind, _ in sibling_builders:
        prefix_shapes = (
            ("no-arguments", []),
            ("missing-content", [number("$context")]),
            ("extra-argument", display_arguments + [number("0xdeadbeef")]),
            ("string-context", [{"string": "wrong-type"}, number("$fixture.track.first")]),
            ("blob-context", [{"blob_hex": "01020304"}, number("$fixture.track.first")]),
            ("string-content", [number("$context"), {"string": "wrong-type"}]),
            ("blob-content", [number("$context"), {"blob_hex": "01020304"}]),
        )
        for step, (shape_name, arguments) in enumerate(prefix_shapes, start=1):
            zero_context_prefix_cases.extend(
                (
                    {
                        "id": f"{kind_name}-{step:02}-{shape_name}",
                        "description": f"{kind_name.title()} malformed prefix: {shape_name}",
                        "request_kind": request_kind,
                        "arguments": arguments,
                        "render": False,
                        "fresh_connection": True,
                        "expect": {"outcome": "any"},
                    },
                    {
                        "id": f"{kind_name}-{step:02}-zero-after-{shape_name}",
                        "description": (
                            f"{kind_name.title()} zero context after {shape_name}"
                        ),
                        "request_kind": request_kind,
                        "arguments": [number(0), number("$fixture.track.first")],
                        "render": False,
                        "fresh_connection": True,
                        "expect": {"outcome": "any"},
                    },
                )
            )
    write(
        EXPERIMENTS / "zero-context-prefix-suite.json",
        suite("song-info-zero-context-prefix", zero_context_prefix_cases),
    )

    sibling_legacy_cases = []
    for kind_name, request_kind, total in sibling_builders:
        for content_name, content_id, content_description in song_info_content_ids:
            sibling_legacy_cases.append(
                {
                    "id": f"{kind_name}-{content_name}",
                    "description": (
                        f"Legacy {kind_name.title()} Song Info with "
                        f"{content_description}"
                    ),
                    "request_kind": request_kind,
                    "arguments": [number("$context"), number(content_id)],
                    "fresh_connection": True,
                    "expect": {"outcome": "any"},
                }
            )
    sibling_legacy = suite("song-info-sibling-legacy", sibling_legacy_cases)
    sibling_legacy["defaults"]["setup"] = "legacy"
    write(SUITES / "song-info-sibling-legacy.json", sibling_legacy)

    status_sibling_suites = (
        "song-info-siblings",
        "song-info-sibling-render",
        "song-info-sibling-pagination",
        "song-info-sibling-errors",
        "song-info-sibling-legacy",
    )
    for status_name, device, context in (
        ("status-player-11", 11, "0x0b010301"),
        ("status-player-1", 1, "0x01010301"),
    ):
        for source_name in status_sibling_suites:
            status_sibling = json.loads((SUITES / f"{source_name}.json").read_text())
            status_sibling["name"] = f"{status_sibling['name']}-{status_name}"
            status_sibling["defaults"]["device"] = device
            status_sibling["defaults"]["context"] = context
            status_sibling["defaults"]["read_timeout_ms"] = 10_000
            for case in status_sibling["cases"]:
                if case["id"].endswith("alternate-location"):
                    case["arguments"][0] = number(f"0x{device:02x}020301")
            if source_name == "song-info-sibling-errors":
                status_sibling["cases"] = [
                    case
                    for case in status_sibling["cases"]
                    if case["id"] != "play-zero-context"
                    and not case["id"].endswith("alternate-location")
                ]
            write(SUITES / f"{source_name}-{status_name}.json", status_sibling)

        status_errors = json.loads(
            (SUITES / "song-info-sibling-errors.json").read_text()
        )
        status_errors["name"] = f"song-info-sibling-errors-{status_name}-ordered"
        status_errors["defaults"]["device"] = device
        status_errors["defaults"]["context"] = context
        status_errors["defaults"]["read_timeout_ms"] = 10_000
        write(EXPERIMENTS / f"status-errors-{status_name}-suite.json", status_errors)

        for case in status_errors["cases"]:
            if case["id"].endswith("alternate-location"):
                case["arguments"][0] = number(f"0x{device:02x}020301")
        write(
            EXPERIMENTS / f"status-errors-{status_name}-matched-suite.json",
            status_errors,
        )

    location2_context = "0x0b020301"
    status_location_precursors = (
        ("play-zero", "0x2102", "0x00000000"),
        ("play-primary", "0x2102", "0x0b010301"),
        ("play-location2", "0x2102", location2_context),
        ("display-primary", "0x2002", "0x0b010301"),
        ("display-location2", "0x2002", location2_context),
        ("delivery-primary", "0x2602", "0x0b010301"),
    )

    def status_location_case(
        case_id: str, description: str, kind: str, context: str
    ) -> dict[str, object]:
        return {
            "id": case_id,
            "description": description,
            "request_kind": kind,
            "arguments": [number(context), number("$fixture.track.first")],
            "render": False,
            "fresh_connection": True,
            "expect": {"outcome": "any"},
        }

    location2_header_cases = [
        status_location_case(
            f"{iteration:02}-delivery-probe",
            f"Iteration {iteration}: location-2 Delivery probe",
            "0x2602",
            location2_context,
        )
        for iteration in range(1, 9)
    ]
    location2_render_cases = json.loads(json.dumps(location2_header_cases))
    for case in location2_render_cases:
        case.pop("render")

    location2_render = suite(
        "song-info-status-location2-delivery-only", location2_render_cases
    )
    location2_render["defaults"].update(
        {"device": 11, "context": "0x0b010301", "read_timeout_ms": 10_000}
    )
    write(STATUS_LOCATION_EXPERIMENTS / "delivery-only-suite.json", location2_render)

    location2_header = suite(
        "song-info-status-location2-delivery-only-header",
        location2_header_cases,
    )
    location2_header["defaults"].update(
        {"device": 11, "context": "0x0b010301", "read_timeout_ms": 10_000}
    )
    write(
        STATUS_LOCATION_EXPERIMENTS / "delivery-only-header-suite.json",
        location2_header,
    )

    for precursor_name, precursor_kind, precursor_context in status_location_precursors:
        location_cases = []
        for iteration in range(1, 9):
            location_cases.extend(
                (
                    status_location_case(
                        f"{iteration:02}-{precursor_name}",
                        f"Iteration {iteration}: {precursor_name} precursor",
                        precursor_kind,
                        precursor_context,
                    ),
                    status_location_case(
                        f"{iteration:02}-delivery-probe",
                        (
                            f"Iteration {iteration}: location-2 Delivery after "
                            f"{precursor_name}"
                        ),
                        "0x2602",
                        location2_context,
                    ),
                )
            )
        location_suite = suite(
            f"song-info-status-location2-{precursor_name}", location_cases
        )
        location_suite["defaults"].update(
            {"device": 11, "context": "0x0b010301", "read_timeout_ms": 10_000}
        )
        write(
            STATUS_LOCATION_EXPERIMENTS / f"{precursor_name}-suite.json",
            location_suite,
        )

    malformed_source = json.loads(
        (SUITES / "song-info-sibling-errors.json").read_text()
    )
    malformed_location_cases = []
    for precursor in malformed_source["cases"]:
        if precursor["id"] == "delivery-alternate-location":
            continue

        precursor = json.loads(json.dumps(precursor))
        precursor["id"] = f"{precursor['id']}-precursor"
        precursor["description"] = (
            f"Location-2 prefix: {precursor['description']}"
        )
        precursor["render"] = False
        precursor["fresh_connection"] = True
        precursor["expect"] = {"outcome": "any"}
        if precursor["id"].startswith("play-alternate-location"):
            precursor["arguments"][0] = number(location2_context)
        malformed_location_cases.extend(
            (
                precursor,
                status_location_case(
                    f"{precursor['id']}-delivery-probe",
                    f"Location-2 Delivery after {precursor['id']}",
                    "0x2602",
                    location2_context,
                ),
            )
        )
    malformed_location_suite = suite(
        "song-info-status-location2-malformed-prefix",
        malformed_location_cases,
    )
    malformed_location_suite["defaults"].update(
        {"device": 11, "context": "0x0b010301", "read_timeout_ms": 10_000}
    )
    write(
        STATUS_LOCATION_EXPERIMENTS / "malformed-prefix-suite.json",
        malformed_location_suite,
    )

    for family in (
        "delivery-only-header",
        "play-zero",
        "play-primary",
        "play-location2",
        "display-primary",
        "display-location2",
        "delivery-primary",
        "malformed-prefix",
    ):
        persistent = json.loads(
            (STATUS_LOCATION_EXPERIMENTS / f"{family}-suite.json").read_text()
        )
        persistent["name"] = f"{persistent['name']}-same-connection"
        for case in persistent["cases"]:
            case["fresh_connection"] = False
        write(
            STATUS_LOCATION_EXPERIMENTS / f"{family}-same-connection-suite.json",
            persistent,
        )

    device_matrix = {
        "format": 1,
        "dimensions": {
            "model_name": [
                "CDJ-2000NXS2",
                "CDJ-3000",
                "XDJ-RX3",
                "XDJ-XZ",
                "XDJ-AZ",
                "XDJ-1000MK2",
                "UNKNOWN-FIXTURE",
            ],
            "player_number": [1, 2, 3, 4, 5, 6],
            "device_type": ["cdj", "mixer", "djm", "type7"],
            "generation": [0, 2, 3],
            "setup": ["legacy", "extended"],
            "root_capabilities": ["0x00ffffff", "0x05cfffff", "0xffffffff"],
            "render_arity": [5, 6, 8],
        },
        "pairwise_default": True,
        "full_cross_product_required_for": [
            "model_name x setup",
            "model_name x root_capabilities",
            "model_name x render_arity",
            "model_name x device_type",
            "model_name x generation",
        ],
        "notes": [
            "Model name is supplied by the discovery/keepalive identity, not the dbserver setup message.",
            "Device type and generation are independent keepalive fields and are varied even for synthetic combinations.",
            "Run model cases only on the isolated synthetic-player L2 segment.",
            "Record identical menu, sort, track-row, unsupported-command, and compatibility cases per identity.",
            "Record display-song-info item order: XDJ-prefixed AIO identities place Comment before Key; non-AIO identities place Comment after Stock Date.",
        ],
    }
    write(ROOT / "device-matrix.json", device_matrix)


if __name__ == "__main__":
    main()
