#!/usr/bin/env python3
"""Join Rekordbox configuration rows to observed Link Export behavior."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DATABASE = ROOT / "data/database"
OUTPUT = ROOT / "data/configuration-behavior-map.json"
SORT_RENDER_GOLDEN = (
    ROOT / "conformance/goldens/rekordbox-7.2.19/xdj-rx3/sort-secondary-render-6.json"
)
REFRESH_SUMMARY = ROOT / "data/session-refresh/settings-refresh-summary.json"
TABLES = ("djmdMenuItems", "djmdCategory", "djmdSort", "djmdColor")

SECONDARY_ROLES = {
    0: "persisted-column-fallback",
    1: "title",
    2: "artist",
    3: "album",
    4: "bpm-key-composite",
    5: "rating",
    6: "genre",
    7: "comments",
    8: "time",
    9: "remixer",
    10: "label",
    11: "original-artist",
    12: "key-bpm-composite",
    13: "bitrate",
    15: "color",
    16: "dj-play-count",
    17: "date-added",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(name: str) -> list[dict[str, object]]:
    path = DATABASE / f"{name}.csv"
    with path.open(newline="") as source:
        rows = list(csv.DictReader(source))

    return [
        {
            key: None
            if value == ""
            else int(value)
            if value.lstrip("-").isdigit()
            else value
            for key, value in row.items()
        }
        for row in rows
    ]


def category_hidden(menu_item_id: int, disable: int) -> bool:
    if menu_item_id == 27:
        return disable & 1 != 0
    if menu_item_id == 22:
        return disable == 1
    return disable != 0


def required_mask(menu_item_id: int) -> int:
    return 1 << (24 if menu_item_id == 22 else menu_item_id - 1)


def typed_values(arguments: list[dict[str, object]]) -> list[object]:
    return [argument["value"] for argument in arguments]


def render_observations() -> list[dict[str, object]]:
    document = json.loads(SORT_RENDER_GOLDEN.read_text())
    observations = []
    for case in document["behavior"]["cases"]:
        sort_id = case["request"]["arguments"][1]["value"]
        render_values = typed_values(case["pages"][0]["arguments"])
        row_values = typed_values(case["rows"][0]["arguments"])
        observations.append(
            {
                "case": case["id"],
                "sort_id": sort_id,
                "materialized_role": SECONDARY_ROLES[sort_id],
                "render_argument_count": len(render_values),
                "render_argument_6": render_values[5],
                "first_row": {
                    "argument_0_secondary_raw": row_values[0],
                    "argument_5_secondary_text": row_values[5],
                    "argument_6_composite_type": row_values[6],
                    "argument_12_original_key_id": row_values[12],
                    "argument_13_key_text_utf16_byte_length_including_nul": row_values[13],
                    "argument_14_key_text": row_values[14],
                    "argument_15_bpm_x100": row_values[15],
                },
                "row_count": len(case["rows"]),
            }
        )
    return observations


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    menu_rows = read_csv("djmdMenuItems")
    category_rows = read_csv("djmdCategory")
    sort_rows = read_csv("djmdSort")
    color_rows = read_csv("djmdColor")
    menu = {row["ID"]: row for row in menu_rows}
    controlled_mask = 0x05CFFFFF

    categories = []
    for row in sorted(category_rows, key=lambda item: item["Seq"]):
        menu_item_id = row["MenuItemID"]
        mask = required_mask(menu_item_id)
        visible_before_folder_suppression = (
            not category_hidden(menu_item_id, row["Disable"])
            and controlled_mask & mask != 0
        )
        categories.append(
            {
                **row,
                "Name": menu[menu_item_id]["Name"],
                "Class": menu[menu_item_id]["Class"],
                "required_capability_mask": f"0x{mask:08x}",
                "disable_predicate": (
                    "bit-0"
                    if menu_item_id == 27
                    else "equals-1"
                    if menu_item_id == 22
                    else "nonzero"
                ),
                "visible_before_folder_suppression": visible_before_folder_suppression,
                "visible_in_controlled_root": visible_before_folder_suppression
                and menu_item_id != 24,
            }
        )

    sorts = []
    for row in sorted(sort_rows, key=lambda item: (item["Seq"], item["ID"])):
        menu_item_id = row["MenuItemID"]
        sorts.append(
            {
                **row,
                "Name": menu[menu_item_id]["Name"],
                "Class": menu[menu_item_id]["Class"],
                "visible_in_sort_menu": row["Disable"] & 1 == 0,
                "selected_as_persisted_column": row["Disable"] & 2 != 0,
                "track_materialized_role": SECONDARY_ROLES[row["ID"]],
            }
        )

    sources = {}
    for table in TABLES:
        path = DATABASE / f"{table}.csv"
        sources[table] = {
            "path": path.relative_to(ROOT).as_posix(),
            "sha256": sha256(path),
            "row_count": len(read_csv(table)),
        }
    for name, path in (
        ("sort_secondary_render_6", SORT_RENDER_GOLDEN),
        ("settings_refresh", REFRESH_SUMMARY),
    ):
        sources[name] = {
            "path": path.relative_to(ROOT).as_posix(),
            "sha256": sha256(path),
        }

    document = {
        "format": 1,
        "product": "rekordbox 7.2.19",
        "scope": "Persisted Category, Sort, and Column configuration joined to Link Export root, sort-menu, and track-row rendering behavior.",
        "sources": sources,
        "capability_masks": {
            "controlled_lab": "0x05cfffff",
            "physical_xdj_rx3": "0x05fdffff",
            "legacy_exact": "0x00ffffff",
            "legacy_exact_special_case": "Append category ID 23 pointing to Hot Cue Bank when Hot Cue Bank was not otherwise returned.",
            "date_added_remap": "Menu item 22 requires bit 24, colliding with the ordinary bit for menu item 25.",
        },
        "field_ownership": {
            "djmdCategory.ID": ["root row selector returned to the client"],
            "djmdCategory.MenuItemID": [
                "label",
                "class",
                "capability bit",
                "Display Song Info enabled flag",
            ],
            "djmdCategory.Seq": ["root order", "Preferences Category order"],
            "djmdCategory.Disable": [
                "root visibility predicate",
                "Display Song Info enabled flag",
            ],
            "djmdCategory.InfoOrder": [
                "Preferences persistence only; not root or Display serving"
            ],
            "djmdSort.ID": ["track sort selector", "secondary-column selector"],
            "djmdSort.MenuItemID": ["sort label", "sort class"],
            "djmdSort.Seq": [
                "sort-menu order",
                "Preferences first-selected order",
            ],
            "djmdSort.Disable.bit0": ["sort-menu visibility"],
            "djmdSort.Disable.bit1": ["persisted Column selection"],
            "djmdColor.Commnt": ["Color root label", "Color secondary text"],
        },
        "categories": categories,
        "sorts": sorts,
        "colors": color_rows,
        "render_decision_table": [
            {
                "argument_count": 5,
                "behavior": "Uses the materialized list-buffer value in the captured Default case.",
                "authority_status": "Complete non-default active-sort cross queued for record/repeat.",
            },
            {
                "argument_count": 6,
                "behavior": "Argument 6 is a row-layout category. The active list sort controls the materialized right column; Default falls back to persisted Column selection.",
                "authority_status": "Eleven visible sorts captured and exactly repeated.",
            },
            {
                "argument_count": 7,
                "behavior": "Static decoder reads argument 6 but not argument 7; active-sort matrix is queued.",
                "authority_status": "Static prediction only pending record/repeat.",
            },
            {
                "argument_count": 8,
                "behavior": "Argument 7 gates reconciliation. With a nonzero gate, argument 8 selects a column or zero invokes persisted Column fallback; a zero gate ignores argument 8.",
                "authority_status": "Ordinary gate/selector behavior captured; width and boundary matrix queued.",
            },
        ],
        "six_argument_active_sort_observations": render_observations(),
        "render_invariants": {
            "argument_6_across_all_observed_sorts": 12,
            "key_metadata_arguments_12_through_15": "Always carry artist ID, key ID, key text, and BPM x100 independently of the visible secondary column.",
            "default_sort": "Uses persisted Column selection; base fixture selects Key and emits Key - BPM.",
            "bpm_sort": "Emits BPM - Key.",
            "key_sort": "Emits Key - BPM.",
            "other_observed_nondefault_sorts": "Emit the single active-sort value, including an empty string for numeric Rating and DJ Play Count rows.",
        },
        "refresh_boundary": {
            "rule": "Category, Sort, and Column controls are locked while LINK is active. Changes made while inactive are consumed by the next LINK activation in the same Rekordbox process.",
            "evidence": json.loads(REFRESH_SUMMARY.read_text())["lifecycle"],
        },
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(document, indent=2) + "\n")
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
