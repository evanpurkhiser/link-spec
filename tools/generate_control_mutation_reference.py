#!/usr/bin/env python3
"""Join Rekordbox control/mutation dispatch with XDJ-RR client call sites."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
VOCABULARY = ROOT / "data/static-analysis/link-export-request-vocabulary.json"
CLIENT = ROOT / "data/static-analysis/xdj-rr-client-navigation.json"
JSON_OUTPUT = ROOT / "data/static-analysis/control-mutation-command-map.json"
MARKDOWN_OUTPUT = ROOT / "CONTROL_AND_MUTATION_REFERENCE.md"

EFFECT_CLASSES = {
    "list-buffer-render": {"3000"},
    "state-query": {
        "3006", "3008", "3100", "3107", "3203", "3303", "3402", "3603",
        "3903", "3A03", "3B03", "3D03",
    },
    "mutation-or-state-write": {
        "2005", "2105", "2107", "2507", "2605", "2705", "2805", "2905",
        "3001", "3002", "3007", "3101", "3102", "3201", "3207", "3302",
        "3307", "3401", "3407", "3C03",
    },
    "recognized-static-route": {
        "2205", "3003", "3103", "3104", "3202", "3301", "3403", "3503",
        "3703", "3803",
    },
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def in_scope(command: dict[str, object]) -> bool:
    if command["direction"] != "request":
        return False

    kind = int(command["kind"], 16)
    return 0x3000 <= kind <= 0x3FFF or (
        0x2000 <= kind <= 0x2FFF and kind & 0xFF in {0x05, 0x07}
    )


def effect_class(command: dict[str, object]) -> str:
    coverage = command["coverage"]
    if coverage == "rekordbox-static-rejected":
        return "rejected"
    if coverage == "rekordbox-recognized-log-only":
        return "recognized-log-only"

    matches = [
        name for name, kinds in EFFECT_CLASSES.items() if command["kind"] in kinds
    ]
    if len(matches) != 1:
        raise ValueError(
            f"command {command['kind']} must have exactly one explicit effect class: {matches}"
        )
    return matches[0]


def build_document() -> dict[str, object]:
    vocabulary = json.loads(VOCABULARY.read_text())
    client = json.loads(CLIENT.read_text())
    client_kinds = {item["request_kind"]: item for item in client["request_kinds"]}
    call_sites: dict[str, list[dict[str, object]]] = defaultdict(list)
    for site in client["call_sites"]:
        call_sites[site["request_kind"]].append(site)

    commands = []
    for command in vocabulary["commands"]:
        if not in_scope(command):
            continue

        kind = command["kind"]
        sites = call_sites[kind]
        client_kind = client_kinds.get(kind)
        commands.append(
            {
                "kind": kind,
                "name": command["name"],
                "effect_class": effect_class(command),
                "coverage": command["coverage"],
                "evidence": command["evidence"],
                "server": {
                    "dispatcher": command.get("rekordbox_dispatcher"),
                    "route": command.get("rekordbox_route") or [],
                    "target": command.get("rekordbox_target"),
                    "reply_kind": command.get("reply_kind"),
                    "rejection_reason": command.get("rejection_reason"),
                    "dependencies": command.get("dependencies"),
                },
                "xdj_rr_client": {
                    "has_request_kind": client_kind is not None,
                    "direct_call_site_count": 0
                    if client_kind is None
                    else client_kind["direct_call_site_count"],
                    "literal_locations": []
                    if client_kind is None
                    else client_kind["literal_locations"],
                    "has_dynamic_location": False
                    if client_kind is None
                    else client_kind["has_dynamic_location"],
                    "wrappers": sorted({site["wrapper"] for site in sites}),
                    "callers": sorted({site["caller"] for site in sites}),
                    "call_sites": sites,
                },
            }
        )

    commands.sort(key=lambda command: int(command["kind"], 16))
    effects = Counter(command["effect_class"] for command in commands)
    coverages = Counter(command["coverage"] for command in commands)
    return {
        "format": 1,
        "product": "rekordbox 7.2.19",
        "scope": "Every request in the 0x2x05 write, 0x2x07 database-modification, and 0x3xxx control/state namespaces, joined to recovered XDJ-RR callers.",
        "sources": {
            "rekordbox_request_vocabulary": {
                "path": VOCABULARY.relative_to(ROOT).as_posix(),
                "sha256": sha256(VOCABULARY),
            },
            "xdj_rr_client_navigation": {
                "path": CLIENT.relative_to(ROOT).as_posix(),
                "sha256": sha256(CLIENT),
                "call_site_source_base": "parent workspace directory",
            },
        },
        "summary": {
            "command_count": len(commands),
            "effect_classes": dict(sorted(effects.items())),
            "coverage_classes": dict(sorted(coverages.items())),
            "commands_with_xdj_rr_direct_callers": sum(
                command["xdj_rr_client"]["direct_call_site_count"] > 0
                for command in commands
            ),
            "xdj_rr_direct_call_site_count": sum(
                command["xdj_rr_client"]["direct_call_site_count"]
                for command in commands
            ),
        },
        "commands": commands,
        "interpretation_boundary": {
            "rekordbox": "Server dispatch and effects come from the pinned Rekordbox vocabulary and its static/live evidence tiers.",
            "xdj_rr": "Client call sites describe the pinned XDJ-RR source only. No direct caller does not imply that other player models never emit the command.",
            "effect_class": "The coarse class aids navigation; route, target, dependencies, rejection reason, and evidence remain authoritative.",
        },
    }


def cell(value: object) -> str:
    if value is None or value == "" or value == []:
        return "-"
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    return str(value).replace("|", "\\|")


def markdown(document: dict[str, object]) -> str:
    summary = document["summary"]
    lines = [
        "# Link Export control and mutation commands",
        "",
        "This generated reference joins Rekordbox 7.2.19 server dispatch with the",
        "pinned XDJ-RR client call graph for every `0x2x05` write, `0x2x07` database",
        "modification, and `0x3xxx` control/state request. It complements the menu",
        "query graph by documenting commands that mutate state, read scalar state,",
        "write analysis data, or are recognized and rejected outside list browsing.",
        "",
        f"The domain contains {summary['command_count']} commands. XDJ-RR has direct",
        f"callers for {summary['commands_with_xdj_rr_direct_callers']} commands across",
        f"{summary['xdj_rr_direct_call_site_count']} call sites.",
        "",
        "## Command map",
        "",
        "| Kind | Name | Effect | Rekordbox dispatcher | Target | Reply | XDJ-RR callers | Locations |",
        "| ---: | --- | --- | --- | --- | ---: | ---: | --- |",
    ]
    for command in document["commands"]:
        server = command["server"]
        client = command["xdj_rr_client"]
        lines.append(
            "| "
            + " | ".join(
                (
                    f"`{command['kind']}`",
                    f"`{command['name']}`",
                    command["effect_class"],
                    cell(server["dispatcher"]),
                    cell(server["target"]),
                    cell(server["reply_kind"]),
                    str(client["direct_call_site_count"]),
                    cell(client["literal_locations"])
                    + (" + dynamic" if client["has_dynamic_location"] else ""),
                )
            )
            + " |"
        )

    lines.extend(["", "## Command details", ""])
    for command in document["commands"]:
        server = command["server"]
        client = command["xdj_rr_client"]
        lines.extend(
            [
                f"### `{command['kind']}` `{command['name']}`",
                "",
                f"- Classification: `{command['effect_class']}`; coverage `{command['coverage']}`; evidence {cell(command['evidence'])}.",
                f"- Rekordbox route: {cell(server['route'])}.",
                f"- Target: {cell(server['target'])}; reply: {cell(server['reply_kind'])}.",
            ]
        )
        if server["rejection_reason"]:
            lines.append(f"- Rejection: {server['rejection_reason']}.")
        dependencies = server["dependencies"]
        if dependencies:
            lines.append(
                f"- Database: {cell(dependencies.get('database'))}. Filesystem/effect: {dependencies.get('filesystem') or '-'}"
            )
        lines.append(
            f"- XDJ-RR: {client['direct_call_site_count']} direct call sites; wrappers {cell(client['wrappers'])}; callers {cell(client['callers'])}; literal locations {cell(client['literal_locations'])}{'; dynamic location also used' if client['has_dynamic_location'] else ''}."
        )
        for site in client["call_sites"]:
            lines.append(
                f"- Caller evidence: `{site['source']}:{site['line']}` "
                f"`{site['caller']}` -> `{site['wrapper']}` at `{site['caller_address']}`, "
                f"location `{site['location_argument']}` ({site['location_source']})."
            )
        lines.append("")

    lines.extend(
        [
            "## Interpretation boundary",
            "",
            "The Rekordbox side records server behavior at its stated evidence tier.",
            "The XDJ-RR side is a client-source inventory, not evidence that every other",
            "device uses the same call path. A missing XDJ-RR caller is preserved as zero",
            "rather than promoted to a cross-device negative conclusion.",
            "",
            "The coarse effect class is an index. Exact route, target, database and",
            "filesystem dependencies, replies, rejection reasons, and evidence labels are",
            "authoritative. Live outcome gaps remain in `REKORDBOX_RESEARCH_GAPS.md`.",
            "",
            "Regenerate both artifacts with:",
            "",
            "```sh",
            "./.venv/bin/python tools/generate_control_mutation_reference.py",
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
    document = build_document()
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(document, indent=2) + "\n")
    args.markdown_output.write_text(markdown(document))
    print(f"wrote {args.json_output}")
    print(f"wrote {args.markdown_output}")


if __name__ == "__main__":
    main()
