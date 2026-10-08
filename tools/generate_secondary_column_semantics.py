#!/usr/bin/env python3
"""Join canonical secondary-column goldens into one exact semantic matrix."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
GOLDENS = ROOT / "conformance/goldens/rekordbox-7.2.19/xdj-rx3"
DEFAULT_OUTPUT = ROOT / "data/secondary-column-semantics.json"
TRACK_ID = 10001
FIELD_INDEXES = (0, 5, 6, 12, 13, 14, 15)

PERSISTED = (
    ("artist", 2),
    ("album", 3),
    ("bpm", 4),
    ("rating", 5),
    ("genre", 6),
    ("comment", 7),
    ("time", 8),
    ("remixer", 9),
    ("label", 10),
    ("original-artist", 11),
    ("key", 12),
    ("bitrate", 13),
    ("color", 15),
    ("play-count", 16),
    ("date-added", 17),
)

SORT_NAMES = {
    0: "default",
    1: "alphabet",
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
    14: "reserved",
    15: "color",
    16: "play-count",
    17: "date-added",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text())


def case_by_id(golden: dict[str, object], case_id: str) -> dict[str, object]:
    matches = [case for case in golden["behavior"]["cases"] if case["id"] == case_id]
    if len(matches) != 1:
        raise SystemExit(f"expected one case {case_id}, found {len(matches)}")
    return matches[0]


def track_rows(case: dict[str, object]) -> list[list[dict[str, object]]]:
    matches = [
        row["arguments"]
        for row in case["rows"]
        if row["kind"] == 0x4101
        and len(row["arguments"]) > 15
        and row["arguments"][1]["type"] == "number"
        and row["arguments"][1]["value"] >= 10000
    ]
    if len(matches) != 8:
        raise SystemExit(f"case {case['id']} has {len(matches)} content rows, expected 8")
    return sorted(matches, key=lambda arguments: arguments[1]["value"])


def track_row(case: dict[str, object]) -> list[dict[str, object]]:
    matches = [
        arguments
        for arguments in track_rows(case)
        if arguments[1]["value"] == TRACK_ID
    ]
    if len(matches) != 1:
        raise SystemExit(f"case {case['id']} has {len(matches)} rows for {TRACK_ID}")
    return matches[0]


def values(arguments: list[dict[str, object]]) -> dict[str, object]:
    return {str(index): arguments[index]["value"] for index in FIELD_INDEXES}


def composite_class(arguments: list[dict[str, object]]) -> str:
    text = arguments[5]["value"]
    if not text:
        return "empty"
    if " bpm - " in text:
        return "bpm-key"
    if text.endswith(" bpm") and " - " in text:
        return "key-bpm"
    return "single"


def profile(
    *,
    source: Path,
    case: dict[str, object],
    name: str,
    selector: int,
) -> dict[str, object]:
    arguments = track_row(case)
    all_rows = track_rows(case)
    render = case["pages"][0]["arguments"]
    return {
        "name": name,
        "selector": selector,
        "source": str(source.relative_to(ROOT)),
        "source_sha256": digest(source),
        "case_id": case["id"],
        "request": case["request"],
        "first_render_arguments": render,
        "fields": {
            str(index): arguments[index]
            for index in FIELD_INDEXES
        },
        "field_values": values(arguments),
        "item_type_hex": f"0x{arguments[6]['value']:04x}",
        "text_shape": composite_class(arguments),
        "all_track_fields": [
            {
                "content_id": row[1]["value"],
                "title": row[3]["value"],
                "field_values": values(row),
                "item_type_hex": f"0x{row[6]['value']:04x}",
                "text_shape": composite_class(row),
            }
            for row in all_rows
        ],
    }


def field_differences(left: dict[str, object], right: dict[str, object]) -> list[int]:
    return [
        index
        for index in FIELD_INDEXES
        if left["field_values"][str(index)] != right["field_values"][str(index)]
    ]


def all_track_differences(
    left: dict[str, object], right: dict[str, object]
) -> dict[str, list[int]]:
    left_rows = {row["content_id"]: row for row in left["all_track_fields"]}
    right_rows = {row["content_id"]: row for row in right["all_track_fields"]}
    if left_rows.keys() != right_rows.keys():
        raise SystemExit(
            f"content row mismatch for {left['name']} and {right['name']}: "
            f"{sorted(left_rows)} != {sorted(right_rows)}"
        )

    return {
        str(content_id): [
            index
            for index in FIELD_INDEXES
            if left_rows[content_id]["field_values"][str(index)]
            != right_rows[content_id]["field_values"][str(index)]
        ]
        for content_id in sorted(left_rows)
        if any(
            left_rows[content_id]["field_values"][str(index)]
            != right_rows[content_id]["field_values"][str(index)]
            for index in FIELD_INDEXES
        )
    }


def build() -> dict[str, object]:
    persisted = []
    for name, selector in PERSISTED:
        path = GOLDENS / f"secondary-{name}.json"
        persisted.append(
            profile(
                source=path,
                case=case_by_id(load(path), "track-rows"),
                name=name,
                selector=selector,
            )
        )

    active_path = GOLDENS / "sort-secondary-render-6.json"
    active = []
    for case in load(active_path)["behavior"]["cases"]:
        selector = case["request"]["arguments"][1]["value"]
        active.append(
            profile(
                source=active_path,
                case=case,
                name=SORT_NAMES[selector],
                selector=selector,
            )
        )

    explicit_path = GOLDENS / "render-secondary-controls.json"
    explicit_golden = load(explicit_path)
    explicit = []
    for case in explicit_golden["behavior"]["cases"]:
        override_suffix = case["id"].removeprefix("override-")
        if case["id"].startswith("override-") and override_suffix.isdigit():
            selector = int(override_suffix)
            name = next((name for name, value in PERSISTED if value == selector), "reserved")
        else:
            selector = case["pages"][0]["arguments"][7]["value"]
            name = case["id"]
        explicit.append(
            profile(
                source=explicit_path,
                case=case,
                name=name,
                selector=selector,
            )
        )

    fallback_path = GOLDENS / "sort-ids.json"
    fallback = []
    for case in load(fallback_path)["behavior"]["cases"]:
        selector = case["request"]["arguments"][1]["value"]
        fallback.append(
            profile(
                source=fallback_path,
                case=case,
                name=SORT_NAMES[selector],
                selector=selector,
            )
        )

    persisted_by_selector = {item["selector"]: item for item in persisted}
    active_by_selector = {item["selector"]: item for item in active}
    explicit_by_selector = {
        item["selector"]: item
        for item in explicit
        if item["case_id"].removeprefix("override-").isdigit()
    }
    fallback_by_selector = {item["selector"]: item for item in fallback}
    return {
        "format": 1,
        "authority": "real Rekordbox 7.2.19 canonical record/repeat goldens",
        "track": {"content_id": TRACK_ID, "title": "Alpha One"},
        "field_indexes": {
            "0": "secondary raw value or ID",
            "5": "secondary display text",
            "6": "composite item type",
            "12": "original KeyID",
            "13": "key display UTF-16 byte length including NUL",
            "14": "key display text",
            "15": "BPM x100",
        },
        "profiles": {
            "persisted_default": persisted,
            "active_sort_render_6": active,
            "explicit_render_8": explicit,
            "active_sort_render_8_persisted_fallback": fallback,
        },
        "comparisons": {
            "persisted_vs_explicit_override": [
                {
                    "name": persisted_by_selector[selector]["name"],
                    "selector": selector,
                    "differing_fields": field_differences(
                        persisted_by_selector[selector], explicit_by_selector[selector]
                    ),
                    "all_track_differences": all_track_differences(
                        persisted_by_selector[selector], explicit_by_selector[selector]
                    ),
                }
                for selector in sorted(explicit_by_selector.keys() & persisted_by_selector.keys())
            ],
            "persisted_vs_active_sort_render_6": [
                {
                    "name": persisted_by_selector[selector]["name"],
                    "selector": selector,
                    "differing_fields": field_differences(
                        persisted_by_selector[selector], active_by_selector[selector]
                    ),
                    "all_track_differences": all_track_differences(
                        persisted_by_selector[selector], active_by_selector[selector]
                    ),
                }
                for selector in sorted(active_by_selector.keys() & persisted_by_selector.keys())
            ],
            "active_render_6_vs_render_8_persisted_fallback": [
                {
                    "name": active_by_selector[selector]["name"],
                    "selector": selector,
                    "differing_fields": field_differences(
                        active_by_selector[selector], fallback_by_selector[selector]
                    ),
                    "all_track_differences": all_track_differences(
                        active_by_selector[selector], fallback_by_selector[selector]
                    ),
                }
                for selector in sorted(active_by_selector.keys() & fallback_by_selector.keys())
            ],
        },
        "counting_note": (
            "Each profile extracts one identical focus row plus all eight content rows keyed "
            "by ContentID, so ordering changes cannot be mistaken for secondary-column "
            "changes. Exact typed focus-row fields remain embedded."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    args.output.write_text(json.dumps(build(), indent=2) + "\n")


if __name__ == "__main__":
    main()
