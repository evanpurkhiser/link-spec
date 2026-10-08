#!/usr/bin/env python3
"""Generate the complete Rekordbox Link Export request/navigation graph."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
QUERY_MAP = ROOT / "data/static-analysis/menu-database-query-map.json"
OUTPUT = ROOT / "data/static-analysis/link-export-navigation-graph.json"
SUITES = ROOT / "conformance/suites"

ROOT_SELECTIONS = [
    ("Track", "1004"), ("Key", "1014"), ("BPM", "1006"),
    ("Genre", "1001"), ("Artist", "1002"), ("Album", "1003"),
    ("Matching", "1017"), ("Search", "1300"), ("Playlist", "1105"),
    ("History", "1012"), ("Bitrate", "1011"), ("Color", "100D"),
    ("File Name", "1013"), ("Hot Cue Bank", "2001"), ("Label", "100A"),
    ("Original Artist", "1302"), ("Rating", "1007"), ("Remixer", "1602"),
    ("Time", "1010"), ("Year", "1008"),
]

STAGES = {
    "root": {"1000": "configured root categories"},
    "genre_hierarchy": {"1001": "genres", "1101": "artists or ALL within genre", "1201": "albums or ALL within genre and artist", "1301": "tracks"},
    "artist_hierarchy": {"1002": "artists", "1102": "albums or ALL within artist", "1202": "tracks"},
    "album_hierarchy": {"1003": "albums", "1103": "tracks"},
    "collection_tracks": {"1004": "tracks"},
    "bpm": {"1006": "BPM values", "1106": "tolerance 0 through 6", "1206": "tracks"},
    "rating": {"1007": "rating values", "1107": "tracks"},
    "release_year": {"1008": "decades", "1108": "years or ALL", "1208": "tracks"},
    "label_hierarchy": {"100A": "labels", "110A": "artists or ALL within label", "120A": "albums or ALL within label and artist", "130A": "tracks"},
    "old_key": {"100B": "legacy key values", "110B": "tracks"},
    "color": {"100D": "color values", "110D": "tracks"},
    "dj_play_count": {"100E": "play-count values", "110E": "tracks"},
    "prepare": {"100F": "prepared tracks"},
    "duration": {"1010": "minute buckets", "1110": "tracks"},
    "bitrate": {"1011": "bitrate values", "1111": "tracks"},
    "history": {"1012": "history sessions", "1112": "tracks"},
    "file_name": {"1013": "tracks with filename primary text"},
    "key": {"1014": "normalized keys", "1114": "harmonic distance", "1214": "tracks"},
    "my_tag": {"1015": "tag groups or leaves", "1315": "tags assigned to one track"},
    "matching": {"1017": "tracks related to the seed"},
    "rejected_guessed_route": {"1018": "rejected guessed route"},
    "playlist": {"1105": "folders, playlists, or playlist tracks"},
    "search": {"1300": "mixed Artist, Album, Track, and File Name results"},
    "cue_track_root": {"130C": "recognized CueTrack arm without a builder"},
    "original_artist_hierarchy": {"1302": "original artists", "1402": "albums or ALL within original artist", "1502": "tracks"},
    "sort_menu": {"1400": "configured sort choices"},
    "search_tracks": {"1500": "track-only search results"},
    "remixer_hierarchy": {"1602": "remixers", "1702": "albums or ALL within remixer", "1802": "tracks"},
    "date_added": {"1708": "years", "1808": "months or ALL", "1908": "days or ALL", "1A08": "tracks"},
    "hot_cue_bank_catalog": {"2001": "folders, banks, or bank tracks"},
    "display_song_info": {"2002": "fixed Display Song Info rows"},
    "artwork_payload": {"2003": "artwork bytes", "2103": "content artwork bytes"},
    "analysis_payload": {"2004": "preview waveform", "2204": "beat grid", "2504": "VBR information", "2804": "waveform detail", "2904": "analysis payload", "2A04": "analysis payload", "2C04": "specified analysis atom", "2D04": "alternate specified analysis atom"},
    "analysis_log_only": {kind: "recognized log-only arm" for kind in ("2304", "2404", "2604", "2704")},
    "cue_payload": {"2104": "legacy cue bytes", "2B04": "extended cue bytes"},
    "hot_cue_bank_legacy_getter": {"2101": "legacy bank membership reply"},
    "play_song_info": {"2102": "fixed Play Song Info rows"},
    "hot_cue_bank_legacy_setter": {"2201": "membership mutation and cue reply"},
    "recognized_song_info_without_builder": {kind: "recognized Song Info request without a host builder" for kind in ("2202", "2302", "2402", "2502")},
    "hot_cue_bank_extended_getter": {"2301": "extended bank membership reply"},
    "hot_cue_bank_extended_setter": {"2401": "membership mutation and extended reply"},
    "delivery_song_info": {"2602": "fixed Delivery Info rows"},
    "render_buffer": {"3000": "render current location-keyed list buffer"},
    "user_info_djid": {"3006": "DJ ID profile reply"},
    "link_history_mutation": {"3001": "insert track into current Link history", "3101": "delete current Link history", "3401": "remove track from current Link history"},
    "play_state_snapshot": {"3B03": "Link-played scalar lookup"},
    "malformed_unknown_kind": {"0000": "malformed setup/unknown control", "FFFF": "unknown request"},
}

SEQUENCES = {
    "genre_hierarchy": ["1001", "1101", "1201", "1301"],
    "artist_hierarchy": ["1002", "1102", "1202"],
    "album_hierarchy": ["1003", "1103"],
    "bpm": ["1006", "1106", "1206"],
    "rating": ["1007", "1107"],
    "release_year": ["1008", "1108", "1208"],
    "label_hierarchy": ["100A", "110A", "120A", "130A"],
    "old_key": ["100B", "110B"],
    "color": ["100D", "110D"],
    "dj_play_count": ["100E", "110E"],
    "duration": ["1010", "1110"],
    "bitrate": ["1011", "1111"],
    "history": ["1012", "1112"],
    "key": ["1014", "1114", "1214"],
    "original_artist_hierarchy": ["1302", "1402", "1502"],
    "remixer_hierarchy": ["1602", "1702", "1802"],
    "date_added": ["1708", "1808", "1908", "1A08"],
}

LIST_FAMILIES = {
    "root", "genre_hierarchy", "artist_hierarchy", "album_hierarchy",
    "collection_tracks", "bpm", "rating", "release_year", "label_hierarchy",
    "old_key", "color", "dj_play_count", "prepare", "duration", "bitrate",
    "history", "file_name", "key", "my_tag", "matching", "playlist", "search",
    "original_artist_hierarchy", "sort_menu", "search_tracks", "remixer_hierarchy",
    "date_added", "hot_cue_bank_catalog", "display_song_info", "play_song_info",
    "delivery_song_info",
}
DIRECT_FAMILIES = {
    "artwork_payload", "analysis_payload", "cue_payload",
    "hot_cue_bank_legacy_getter", "hot_cue_bank_legacy_setter",
    "hot_cue_bank_extended_getter", "hot_cue_bank_extended_setter",
    "user_info_djid", "link_history_mutation", "play_state_snapshot",
}
NO_BUILDER_FAMILIES = {
    "rejected_guessed_route", "cue_track_root", "analysis_log_only",
    "recognized_song_info_without_builder", "malformed_unknown_kind",
}


def edges(identity: str) -> list[dict[str, str]]:
    sequence = SEQUENCES.get(identity, [])
    result = [
        {"from": source, "to": target, "selection": STAGES[identity][source]}
        for source, target in zip(sequence, sequence[1:])
    ]
    if identity == "playlist":
        result.append({"from": "1105", "to": "1105", "selection": "open folder recursively or open playlist as tracks"})
    if identity == "hot_cue_bank_catalog":
        result.append({"from": "2001", "to": "2001", "selection": "open folder recursively or open bank as tracks"})
    return result


def response_mode(identity: str) -> str:
    if identity in LIST_FAMILIES:
        return "list-buffer"
    if identity == "render_buffer":
        return "render"
    if identity in DIRECT_FAMILIES:
        return "direct"
    if identity in NO_BUILDER_FAMILIES:
        return "error-or-no-reply"
    raise ValueError(f"unclassified response mode: {identity}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    return parser.parse_args()


def normalize_kind(value: str | int) -> str:
    if isinstance(value, int):
        return f"{value:04X}"
    return value.removeprefix("0x").upper().zfill(4)


def wire_type(argument: dict[str, object]) -> str:
    keys = set(argument)
    if keys & {"number", "utf16_bytes", "case_item"}:
        return "number"
    if "string" in keys:
        return "string"
    if "blob_hex" in keys:
        return "blob"
    raise ValueError(f"unknown argument declaration: {argument}")


def declared_value(argument: dict[str, object]) -> tuple[str, str]:
    for key in ("number", "utf16_bytes", "case_item", "string", "blob_hex"):
        if key not in argument:
            continue
        value = argument[key]
        if isinstance(value, str) and value.startswith("$"):
            return "symbol", f"{key}:{value}"
        if key == "case_item":
            return "symbol", "case_item:" + json.dumps(
                value, sort_keys=True, separators=(",", ":")
            )
        if key == "blob_hex" and isinstance(value, str):
            return "literal", f"blob:{len(value) // 2} bytes"
        return "literal", f"{key}:{json.dumps(value, ensure_ascii=False)}"
    raise ValueError(f"unknown argument declaration: {argument}")


def request_shapes() -> tuple[dict[str, list[dict[str, object]]], dict[str, object]]:
    shapes: dict[str, dict[tuple[str, ...], dict[str, object]]] = defaultdict(dict)
    digest = hashlib.sha256()
    suite_count = 0
    case_count = 0

    def add(
        kind: str,
        types: tuple[str, ...],
        arguments: list[dict[str, object]],
        origin: str,
        suite: str,
        case: str,
    ) -> None:
        entry = shapes[kind].setdefault(
            types,
            {
                "argument_count": len(types),
                "wire_types": list(types),
                "declaration_count": 0,
                "origins": set(),
                "examples": [],
                "positions": [
                    {
                        "index": index,
                        "symbols": set(),
                        "literal_values": set(),
                    }
                    for index in range(len(types))
                ],
            },
        )
        entry["declaration_count"] += 1
        entry["origins"].add(origin)
        example = {"suite": suite, "case": case}
        if example not in entry["examples"] and len(entry["examples"]) < 3:
            entry["examples"].append(example)
        for position, argument in zip(entry["positions"], arguments):
            category, value = declared_value(argument)
            position[f"{category}s" if category == "symbol" else "literal_values"].add(value)

    for path in sorted(SUITES.rglob("*.json")):
        relative = path.relative_to(ROOT).as_posix()
        payload = path.read_bytes()
        digest.update(relative.encode())
        digest.update(b"\0")
        digest.update(payload)
        document = json.loads(payload)
        suite_count += 1
        defaults = document["defaults"]
        for case in document["cases"]:
            case_count += 1
            kind = normalize_kind(case["request_kind"])
            types = tuple(wire_type(argument) for argument in case["arguments"])
            add(kind, types, case["arguments"], "primary-request", relative, case["id"])

            if kind == "3000" or case.get("render") is False:
                continue
            if case.get("direct_response") or case.get("send_only"):
                continue
            tail = case.get("render_arguments", defaults["render_arguments"])
            render_types = ("number", "number", "number", *("number" for _ in tail))
            render_arguments = [
                {"number": "$context"},
                {"number": "$page_offset"},
                {"number": "$page_count"},
                *({"number": value} for value in tail),
            ]
            add("3000", render_types, render_arguments, "implicit-render", relative, case["id"])

    serializable = {}
    for kind, entries in shapes.items():
        serializable[kind] = []
        for _, entry in sorted(entries.items(), key=lambda item: (len(item[0]), item[0])):
            entry["origins"] = sorted(entry["origins"])
            for position in entry["positions"]:
                literals = sorted(position.pop("literal_values"))
                position["symbols"] = sorted(position["symbols"])
                position["literal_value_count"] = len(literals)
                position["literal_examples"] = literals[:5]
            serializable[kind].append(entry)

    return serializable, {
        "path": "conformance/suites",
        "hash_algorithm": "sha256(relative_path + NUL + file_bytes, sorted by path)",
        "sha256": digest.hexdigest(),
        "suite_file_count": suite_count,
        "case_count": case_count,
    }


def main() -> None:
    args = parse_args()
    query_map = json.loads(QUERY_MAP.read_text())
    shapes, suite_corpus = request_shapes()
    families = []
    for family in query_map["families"]:
        identity = family["id"]
        stages = STAGES[identity]
        if set(stages) != set(family["requests"]):
            raise ValueError(f"stage/request mismatch for {identity}")
        mode = response_mode(identity)
        families.append({
            "id": identity,
            "operation": family["operation"],
            "tables": family["tables"],
            "response_mode": mode,
            "render_with": "3000" if mode == "list-buffer" else None,
            "requests": [
                {
                    "kind": kind,
                    "stage": stages[kind],
                    "declared_signatures": shapes[kind],
                }
                for kind in family["requests"]
            ],
            "edges": edges(identity),
            "recursive": identity in {"playlist", "hot_cue_bank_catalog"},
            "evidence": family["evidence"],
        })

    document = {
        "format": 1,
        "scope": "Rekordbox 7.2.19 Link Export request and menu-transition graph.",
        "source": "data/static-analysis/menu-database-query-map.json",
        "suite_corpus": suite_corpus,
        "session_model": {
            "select": "A list-buffer request returns 4000 and materializes one location-keyed menu.",
            "render": "Request 3000 pages that menu as 4001, zero or more 4101 rows, and 4201.",
            "back": "Back is client-owned; Rekordbox receives a new request for the parent menu.",
        },
        "configured_root": [
            {"position": index, "label": label, "request": request}
            for index, (label, request) in enumerate(ROOT_SELECTIONS, 1)
        ],
        "implemented_direct_browse_not_in_captured_root": ["100E", "100F", "1015", "1315", "1500", "1708", "100B", "130C"],
        "families": families,
        "summary": {
            "family_count": len(families),
            "request_kind_count": sum(len(family["requests"]) for family in families),
            "declared_signature_count": sum(
                len(request["declared_signatures"])
                for family in families
                for request in family["requests"]
            ),
            "configured_root_count": len(ROOT_SELECTIONS),
            "list_buffer_family_count": sum(family["response_mode"] == "list-buffer" for family in families),
            "direct_family_count": sum(family["response_mode"] == "direct" for family in families),
            "no_builder_family_count": sum(family["response_mode"] == "error-or-no-reply" for family in families),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(document, indent=2) + "\n")
    print(f"wrote {args.output}: {len(families)} families")


if __name__ == "__main__":
    main()
