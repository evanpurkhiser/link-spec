#!/usr/bin/env python3
"""Render the generated Link Export navigation graph as a readable reference."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
GRAPH = ROOT / "data/static-analysis/link-export-navigation-graph.json"
OUTPUT = ROOT / "REQUEST_SHAPES.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    return parser.parse_args()


def cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def position_evidence(signature: dict[str, object]) -> str:
    parts = []
    for position in signature["positions"]:
        values = list(position["symbols"]) + list(position["literal_examples"])
        omitted = position["literal_value_count"] - len(position["literal_examples"])
        rendered = ", ".join(f"`{cell(value)}`" for value in values) or "unobserved"
        if omitted:
            rendered += f", +{omitted} literal(s)"
        parts.append(f"{position['index'] + 1}: {rendered}")
    return "; ".join(parts) or "none"


def render() -> str:
    graph = json.loads(GRAPH.read_text())
    summary = graph["summary"]
    corpus = graph["suite_corpus"]
    lines = [
        "# Link Export request shapes",
        "",
        "This reference is generated from the backend-neutral conformance declarations",
        "and the Rekordbox 7.2.19 database-path map. It describes the requests the lab",
        "can issue; a declaration is not promoted real-Rekordbox behavior unless its",
        "family evidence includes `OBS`. Response semantics and live outcomes remain in",
        "the named oracle chapters and canonical goldens.",
        "",
        "## Corpus",
        "",
        f"- Families: {summary['family_count']}",
        f"- Unique request kinds: {summary['request_kind_count']}",
        f"- Distinct argument-count/type signatures: {summary['declared_signature_count']}",
        f"- Suite files: {corpus['suite_file_count']}",
        f"- Cases: {corpus['case_count']}",
        f"- Suite-corpus SHA-256: `{corpus['sha256']}`",
        "- Wire types: `number`, `string`, and `blob`",
        "- `utf16_bytes` helpers and prior-row selectors resolve to numeric arguments",
        "- Position evidence retains exact suite symbols and bounded literal examples;",
        "  it does not assign semantic names to literal-only positions",
        "",
        "List-buffer requests materialize one packed-context/location-keyed menu and",
        "are paged with `0x3000`. Direct requests return their own reply family. Error or",
        "no-reply paths are recognized dispatch arms without a serving list builder.",
        "",
    ]

    for family in graph["families"]:
        lines.extend(
            [
                f"## `{family['id']}`",
                "",
                f"Operation: `{family['operation']}`. Response mode: "
                f"`{family['response_mode']}`. Render request: "
                f"`{family['render_with'] or 'none'}`. Recursive: "
                f"`{str(family['recursive']).lower()}`. Evidence: "
                f"`{' '.join(family['evidence'])}`.",
                "",
                "Tables: " + (
                    ", ".join(f"`{table}`" for table in family["tables"])
                    if family["tables"]
                    else "none; this is an explicit non-database path"
                ) + ".",
                "",
            ]
        )
        if family["edges"]:
            lines.extend(["Transitions:", "", "| From | Selection | To |", "| --- | --- | --- |"])
            for edge in family["edges"]:
                lines.append(
                    f"| `0x{edge['from']}` | {cell(edge['selection'])} | `0x{edge['to']}` |"
                )
            lines.append("")

        lines.extend(
            [
                "| Kind | Stage | Count | Wire types | Position evidence | Declarations | Origin | Examples |",
                "| --- | --- | ---: | --- | --- | ---: | --- | --- |",
            ]
        )
        for request in family["requests"]:
            for signature in request["declared_signatures"]:
                types = ", ".join(signature["wire_types"]) or "empty"
                examples = "; ".join(
                    f"`{example['suite']}#{example['case']}`"
                    for example in signature["examples"]
                )
                lines.append(
                    f"| `0x{request['kind']}` | {cell(request['stage'])} | "
                    f"{signature['argument_count']} | `{types}` | "
                    f"{position_evidence(signature)} | "
                    f"{signature['declaration_count']} | "
                    f"`{', '.join(signature['origins'])}` | {examples} |"
                )
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    args.output.write_text(render())
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
