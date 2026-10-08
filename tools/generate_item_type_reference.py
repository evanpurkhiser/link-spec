#!/usr/bin/env python3
"""Generate the complete represented Rekordbox 0x4101 item-type reference."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
GOLDENS = ROOT / "conformance/goldens/rekordbox-7.2.19"
DOMAIN = ROOT / "data/static-analysis/item-type-domain.json"
JSON_OUTPUT = ROOT / "data/item-type-reference.json"
MARKDOWN_OUTPUT = ROOT / "ITEM_TYPE_REFERENCE.md"

MEANINGS = {
    0x00: "zero type; path or explicitly untyped row",
    0x01: "folder",
    0x02: "album",
    0x04: "title or track",
    0x06: "genre",
    0x07: "artist",
    0x08: "playlist or SmartList",
    0x0A: "rating",
    0x0B: "duration",
    0x0D: "BPM",
    0x0E: "label",
    0x0F: "key",
    0x10: "bitrate",
    0x11: "release year",
    0x12: "file type",
    0x14: "color 1 / Pink",
    0x15: "color 2 / Red",
    0x16: "color 3 / Orange",
    0x17: "color 4 / Yellow",
    0x18: "color 5 / Green",
    0x19: "color 6 / Aqua",
    0x1A: "color 7 / Blue",
    0x1B: "color 8 / Purple",
    0x23: "comment or DeliveryComment",
    0x24: "history",
    0x28: "original artist",
    0x29: "remixer",
    0x2A: "DJ play count",
    0x2B: "Hot Cue Bank",
    0x2E: "Stock Date / Date Added",
    0x2F: "HotCueAutoLoad",
    0x36: "composer artist lookup",
    0x37: "lyricist",
    0x4A: "My Tag group or leaf",
    0x4F: "DeliveryControl and ISRC",
    0x52: "invalid ColorID-derived type (0x13 + low byte)",
    0x80: "menu choice: Genre",
    0x81: "menu choice: Artist",
    0x82: "menu choice: Album",
    0x83: "menu choice: Track",
    0x84: "menu choice: Playlist",
    0x85: "menu choice: BPM",
    0x86: "menu choice: Rating",
    0x87: "menu choice: Year",
    0x88: "menu choice: Remixer",
    0x89: "menu choice: Label",
    0x8A: "menu choice: Original Artist",
    0x8B: "menu choice: Key",
    0x8C: "menu choice: Date Added",
    0x8E: "menu choice: Color",
    0x91: "menu choice: Search",
    0x92: "menu choice: Time",
    0x93: "menu choice: Bitrate",
    0x94: "menu choice: File Name",
    0x95: "menu choice: History",
    0x96: "menu choice: Comments",
    0x97: "menu choice: DJ Play Count",
    0x98: "menu choice: Hot Cue Bank",
    0xA0: "synthetic ALL selector",
    0xA1: "sort choice: Default",
    0xA2: "sort choice: Alphabet",
    0xAA: "menu choice: Matching",
}


def display_value(argument: object) -> object:
    if not isinstance(argument, dict):
        return None
    if "value" in argument:
        value = argument["value"]
        if isinstance(value, str) and len(value) > 48:
            return value[:47] + "..."
        return value
    if "hex" in argument:
        return f"blob:{len(argument['hex']) // 2}"
    return None


def classify(value: int) -> tuple[str, str]:
    secondary = value >> 8
    primary = value & 0xFF
    if secondary:
        return (
            "composite-track",
            f"{MEANINGS[secondary]} secondary over {MEANINGS[primary]} primary",
        )
    if 0x80 <= value <= 0x9F or value == 0xAA:
        return "menu-row", MEANINGS[value]
    if value in (0xA0, 0xA1, 0xA2):
        return "synthetic-or-sort-row", MEANINGS[value]
    return "simple-row", MEANINGS[value]


def collect() -> tuple[Counter[int], dict[int, set[str]], dict[int, set[int]], dict[int, list[dict[str, object]]]]:
    counts: Counter[int] = Counter()
    sources: dict[int, set[str]] = defaultdict(set)
    requests: dict[int, set[int]] = defaultdict(set)
    samples: dict[int, list[dict[str, object]]] = defaultdict(list)

    def walk(value: object, source: str, case_id: str | None, request_kind: int | None) -> None:
        if isinstance(value, dict):
            current_case = case_id
            current_request = request_kind
            request = value.get("request")
            if "id" in value and isinstance(request, dict):
                current_case = str(value["id"])
                kind = request.get("kind")
                if isinstance(kind, int):
                    current_request = kind

            arguments = value.get("arguments")
            if value.get("kind") == 0x4101 and isinstance(arguments, list) and len(arguments) > 6:
                type_argument = arguments[6]
                if isinstance(type_argument, dict) and type_argument.get("type") == "number":
                    item_type = type_argument["value"]
                    counts[item_type] += 1
                    sources[item_type].add(source)
                    if current_request is not None:
                        requests[item_type].add(current_request)
                    sample = {
                        "source": source,
                        "case": current_case,
                        "request_kind": current_request,
                        "argument_0": display_value(arguments[0]),
                        "argument_1": display_value(arguments[1]),
                        "primary_text": display_value(arguments[3]),
                        "secondary_text": display_value(arguments[5]),
                        "argument_count": len(arguments),
                    }
                    signature = json.dumps(sample, sort_keys=True, ensure_ascii=False)
                    existing = {
                        json.dumps(item, sort_keys=True, ensure_ascii=False)
                        for item in samples[item_type]
                    }
                    if signature not in existing:
                        if len(samples[item_type]) < 5:
                            samples[item_type].append(sample)
                        elif (
                            " - " in str(sample["secondary_text"])
                            and not any(
                                " - " in str(item["secondary_text"])
                                for item in samples[item_type]
                            )
                        ):
                            samples[item_type].append(sample)

            for child in value.values():
                walk(child, source, current_case, current_request)
        elif isinstance(value, list):
            for child in value:
                walk(child, source, case_id, request_kind)

    for path in sorted(GOLDENS.rglob("*.json")):
        source = path.relative_to(ROOT).as_posix()
        walk(json.loads(path.read_text()), source, None, None)

    return counts, sources, requests, samples


def build() -> dict[str, object]:
    domain = json.loads(DOMAIN.read_text())
    counts, sources, requests, samples = collect()
    expected = {item["value"]: item["occurrences"] for item in domain["types"]}
    assert counts == Counter(expected)

    types = []
    for value in sorted(counts):
        row_class, meaning = classify(value)
        types.append(
            {
                "value": value,
                "hex": f"0x{value:04x}",
                "class": row_class,
                "meaning": meaning,
                "primary_type": value & 0xFF,
                "secondary_type": value >> 8,
                "occurrences": counts[value],
                "request_kinds": [f"0x{kind:04x}" for kind in sorted(requests[value])],
                "source_file_count": len(sources[value]),
                "source_files": sorted(sources[value]),
                "samples": samples[value],
            }
        )

    return {
        "format": 1,
        "product": "rekordbox 7.2.19",
        "scope": "Every represented 0x4101 argument-6 item type in the canonical golden corpus, with producing requests and raw samples.",
        "authority": (
            "Meanings are joined from real-Rekordbox row or menu labels and the documented "
            "Display, Delivery, category, sort, My Tag, Hot Cue Bank, and secondary-column oracles."
        ),
        "source_domain": "data/static-analysis/item-type-domain.json",
        "summary": {
            "row_bearing_golden_file_count": domain["row_bearing_golden_file_count"],
            "representation_occurrence_count": sum(counts.values()),
            "unique_type_count": len(types),
            "simple_type_count": sum(item["secondary_type"] == 0 for item in types),
            "composite_type_count": sum(item["secondary_type"] != 0 for item in types),
            "unresolved_type_count": sum("unresolved" in item["meaning"] for item in types),
        },
        "encoding": {
            "simple": "Low byte is the row role and the high byte is zero.",
            "track_composite": "(secondary role << 8) | 0x04; low byte 0x04 is the title/track primary role.",
            "upper_16": "Zero for every represented Rekordbox 7.2.19 value in this corpus.",
        },
        "types": types,
    }


def escape(value: object) -> str:
    if value is None or value == "":
        return "empty"
    return str(value).replace("|", "\\|").replace("\n", " ")


def markdown(document: dict[str, object]) -> str:
    summary = document["summary"]
    lines = [
        "# Item type reference",
        "",
        "This generated reference catalogs every represented numeric item type in",
        "argument 6 of a `0x4101` row across the canonical Rekordbox 7.2.19",
        "goldens. It expands the original bounded-capture `data/item-types.csv`",
        "inventory to the complete retained conformance corpus.",
        "",
        f"The corpus contains {summary['unique_type_count']} types across",
        f"{summary['representation_occurrence_count']:,} represented row occurrences",
        f"in {summary['row_bearing_golden_file_count']} row-bearing golden files:",
        f"{summary['simple_type_count']} simple/menu values and",
        f"{summary['composite_type_count']} secondary-over-title composites.",
        "Every represented meaning is resolved; no type is labeled from backend",
        "behavior. Raw samples and every source file remain in",
        "`data/item-type-reference.json`.",
        "",
        "## Encoding",
        "",
        "Simple rows place their role in the low byte. Track composites use",
        "`(secondary_role << 8) | 0x04`, where `0x04` is the title/track primary",
        "role. All represented values fit in the low 16 bits; this is a versioned",
        "corpus fact rather than a cross-version wire restriction.",
        "",
        "## Complete domain",
        "",
        "| Type | Class | Meaning | Occurrences | Producing requests | Representative text |",
        "|---:|---|---|---:|---|---|",
    ]
    for item in document["types"]:
        requests = ", ".join(f"`{kind}`" for kind in item["request_kinds"]) or "context unavailable"
        secondary_samples = [
            sample for sample in item["samples"] if sample["secondary_text"]
        ]
        composite_samples = [
            sample for sample in secondary_samples if " - " in sample["secondary_text"]
        ]
        sample = max(
            composite_samples or secondary_samples or item["samples"],
            key=lambda value: len(str(value["secondary_text"] or value["primary_text"] or "")),
        )
        text = sample["secondary_text"] or sample["primary_text"]
        lines.append(
            f"| `{item['hex']}` | {item['class']} | {item['meaning']} | "
            f"{item['occurrences']:,} | {requests} | {escape(text)} |"
        )

    lines.extend(
        [
            "",
            "## Interpretation boundaries",
            "",
            "- The same numeric type can occur in several request families with",
            "  request-specific argument ownership. Type identifies presentation role;",
            "  it does not make every argument position universal.",
            "- `0x0052` is retained because an invalid ColorID produces it through",
            "  `0x13 + low_byte(ColorID)`; it is evidence of arithmetic type construction,",
            "  not a configured ninth color.",
            "- Root, sort-choice, synthetic ALL, Song Info, and ordinary browse rows",
            "  share the same `0x4101` envelope but have distinct layouts.",
            "- Composite text is server-authored cached presentation. A matching Key or",
            "  BPM materialization can contain two components, while a dynamic override",
            "  of the same nominal type may contain only one or an empty string.",
            "",
            "## Reproduce",
            "",
            "```bash",
            ".venv/bin/python tools/audit_item_type_domain.py",
            ".venv/bin/python tools/generate_item_type_reference.py",
            ".venv/bin/python -m unittest conformance.test_item_type_reference",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-output", type=Path, default=JSON_OUTPUT)
    parser.add_argument("--markdown-output", type=Path, default=MARKDOWN_OUTPUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    document = build()
    args.json_output.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n")
    args.markdown_output.write_text(markdown(document))


if __name__ == "__main__":
    main()
