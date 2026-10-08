#!/usr/bin/env python3
"""Index exact SQL literals retained in Link Export disassembly evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "data/static-analysis"
JSON_OUTPUT = STATIC / "sql-literal-index.json"
MARKDOWN_OUTPUT = ROOT / "SQL_LITERAL_INDEX.md"
FUNCTION_RE = re.compile(r"^##\s+(.+?)(?:\s+\|\s*)?$")
ADDRESS_HEADER_RE = re.compile(r"^address=(?P<address>0x[0-9a-fA-F]+)\s+size=")
LITERAL_RE = re.compile(
    r"^(?P<address>0x[0-9a-fA-F]+).*?;\s*'(?P<literal>(?:[^']|'')*)'\s*$"
)
SQL_START_RE = re.compile(r"^\s*(select|update|insert|delete)(?:\s|$)")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalized_literal(value: str) -> str:
    return " ".join(value.split())


def classification(literal: str) -> str:
    lowered = literal.lower().strip()
    if lowered == "select":
        return "fragment"
    if lowered.startswith("select "):
        return "complete-statement" if " from " in lowered else "fragment"
    if lowered == "update":
        return "fragment"
    if lowered.startswith("update "):
        return "complete-statement" if " set " in lowered else "fragment"
    if lowered == "insert":
        return "fragment"
    if lowered.startswith("insert "):
        return "complete-statement" if " into " in lowered else "fragment"
    if lowered == "delete":
        return "fragment"
    if lowered.startswith("delete "):
        return "complete-statement" if " from " in lowered else "fragment"
    raise ValueError(f"not an indexed SQL literal: {literal}")


def scan() -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    occurrences: dict[str, list[dict[str, object]]] = defaultdict(list)
    scanned_sources = []
    for path in sorted(STATIC.rglob("*.disasm.txt")):
        relative = path.relative_to(ROOT).as_posix()
        lines = path.read_text(errors="replace").splitlines()
        current_function = None
        source_match_count = 0
        for line_number, line in enumerate(lines, start=1):
            function_match = FUNCTION_RE.match(line)
            if function_match:
                current_function = function_match.group(1).strip()
                continue

            address_header_match = ADDRESS_HEADER_RE.match(line)
            if address_header_match:
                current_function = f"function {address_header_match.group('address').lower()}"
                continue

            match = LITERAL_RE.match(line)
            if not match or not SQL_START_RE.match(match.group("literal")):
                continue

            literal = normalized_literal(match.group("literal"))
            occurrences[literal].append(
                {
                    "source": relative,
                    "line": line_number,
                    "address": match.group("address").lower(),
                    "function": current_function,
                    "platform": "windows-x86_64"
                    if "/windows/" in f"/{relative}"
                    else "macos-x86_64",
                }
            )
            source_match_count += 1

        scanned_sources.append(
            {
                "path": relative,
                "sha256": sha256(path),
                "literal_occurrence_count": source_match_count,
            }
        )

    literals = []
    for literal, literal_occurrences in sorted(
        occurrences.items(), key=lambda item: (classification(item[0]), item[0].lower())
    ):
        literals.append(
            {
                "literal": literal,
                "classification": classification(literal),
                "occurrence_count": len(literal_occurrences),
                "platforms": sorted(
                    {occurrence["platform"] for occurrence in literal_occurrences}
                ),
                "occurrences": literal_occurrences,
            }
        )
    return literals, scanned_sources


def markdown(document: dict[str, object]) -> str:
    summary = document["summary"]
    lines = [
        "# Exact SQL literal index",
        "",
        "This generated reference indexes SQL text that appears literally in the",
        "retained Rekordbox disassembly evidence. It is narrower than the logical",
        "query pipelines in `DATABASE_QUERIES.md`: runtime table selection, bound",
        "values, and dynamically concatenated clauses are not reconstructed here.",
        "",
        f"The scan covers {summary['scanned_source_count']} disassembly artifacts and",
        f"finds {summary['unique_literal_count']} unique SQL literals across",
        f"{summary['occurrence_count']} occurrences. Of those,",
        f"{summary['complete_statement_count']} contain the structural keywords of a",
        f"complete statement and {summary['fragment_count']} are explicit fragments.",
        "",
        "Every entry retains the source file, line, address, nearest function heading,",
        "and platform. `data/static-analysis/sql-literal-index.json` is the",
        "machine-readable authority.",
        "",
        "## Complete statements",
        "",
    ]
    for index, item in enumerate(
        (
            literal
            for literal in document["literals"]
            if literal["classification"] == "complete-statement"
        ),
        start=1,
    ):
        lines.extend(
            [
                f"### Statement {index}",
                "",
                "```sql",
                item["literal"],
                "```",
                "",
            ]
        )
        for occurrence in item["occurrences"]:
            owner = occurrence["function"] or "function heading unavailable"
            lines.append(
                f"- `{occurrence['source']}:{occurrence['line']}` at "
                f"`{occurrence['address']}` in `{owner}` ({occurrence['platform']})"
            )
        lines.append("")

    lines.extend(["## Fragments", ""])
    for index, item in enumerate(
        (
            literal
            for literal in document["literals"]
            if literal["classification"] == "fragment"
        ),
        start=1,
    ):
        lines.extend(
            [
                f"### Fragment {index}",
                "",
                "```sql",
                item["literal"],
                "```",
                "",
            ]
        )
        for occurrence in item["occurrences"]:
            owner = occurrence["function"] or "function heading unavailable"
            lines.append(
                f"- `{occurrence['source']}:{occurrence['line']}` at "
                f"`{occurrence['address']}` in `{owner}` ({occurrence['platform']})"
            )
        lines.append("")

    lines.extend(
        [
            "## Interpretation boundary",
            "",
            "A complete-statement label means the literal itself contains the expected",
            "SQL structural keywords. It does not prove that the string is the whole",
            "runtime query after placeholder substitution or concatenation. Fragments",
            "must be interpreted only with their owning disassembly and the corresponding",
            "pipeline in `DATABASE_QUERIES.md`.",
            "",
            "Regenerate both artifacts with:",
            "",
            "```sh",
            "./.venv/bin/python tools/generate_sql_literal_index.py",
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
    literals, scanned_sources = scan()
    complete_count = sum(
        literal["classification"] == "complete-statement" for literal in literals
    )
    document = {
        "format": 1,
        "product": "rekordbox 7.2.19",
        "scope": "Exact SQL literals beginning with SELECT, UPDATE, INSERT, or DELETE in retained Link Export disassembly evidence.",
        "summary": {
            "scanned_source_count": len(scanned_sources),
            "sources_with_literals": sum(
                source["literal_occurrence_count"] > 0 for source in scanned_sources
            ),
            "unique_literal_count": len(literals),
            "occurrence_count": sum(
                literal["occurrence_count"] for literal in literals
            ),
            "complete_statement_count": complete_count,
            "fragment_count": len(literals) - complete_count,
        },
        "literals": literals,
        "scanned_sources": scanned_sources,
    }
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(document, indent=2) + "\n")
    args.markdown_output.write_text(markdown(document))
    print(f"wrote {args.json_output}")
    print(f"wrote {args.markdown_output}")


if __name__ == "__main__":
    main()
