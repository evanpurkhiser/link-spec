#!/usr/bin/env python3
"""Generate the Link Export database schema and field-evidence reference."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "conformance"))

from build_fixture import connect, key_from_options  # noqa: E402


DEFAULT_DATABASE = ROOT / "conformance/fixtures/generated/full/master.db"
DEFAULT_OPTIONS = Path("/mnt/documents/multimedia/djing/rekordbox/options.json")
QUERY_MAP = ROOT / "data/static-analysis/menu-database-query-map.json"
SQL_INDEX = ROOT / "data/static-analysis/sql-literal-index.json"
JSON_OUTPUT = ROOT / "data/database/link-export-schema.json"
MARKDOWN_OUTPUT = ROOT / "DATABASE_FIELD_REFERENCE.md"

NON_PHYSICAL = {
    "djmdLeftBuf": {
        "kind": "runtime-materialized-table",
        "explanation": (
            "Process-local context-keyed list buffer populated after a menu query and "
            "consumed by 0x3000 rendering."
        ),
    },
    "djmdTrackSort": {
        "kind": "runtime-materialized-table",
        "explanation": (
            "Intermediate track rowset used by djdsqlFlexSort before rows enter "
            "djmdLeftBuf."
        ),
    },
    "djmdImage": {
        "kind": "alternate-master-interface-table",
        "explanation": (
            "Master-interface artwork lookup named by recovered code; the active "
            "AppSync fixture instead stores ImagePath on djmdContent and djmdPlaylist."
        ),
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def word_present(text: str, word: str) -> bool:
    return re.search(rf"(?<![A-Za-z0-9_]){re.escape(word)}(?![A-Za-z0-9_])", text, re.I) is not None


def family_text(family: dict[str, object]) -> str:
    return " ".join(
        str(family[key]) for key in ("predicate", "ordering", "result")
    )


def request_kinds(families: list[dict[str, object]]) -> list[str]:
    return sorted(
        {request.upper() for family in families for request in family["requests"]},
        key=lambda value: int(value, 16),
    )


def schema_columns(connection, table: str) -> list[dict[str, object]]:
    rows = connection.execute(f'PRAGMA table_info("{table}")').fetchall()
    return [
        {
            "ordinal": row[0],
            "name": row[1],
            "declared_type": row[2],
            "not_null": bool(row[3]),
            "default": row[4],
            "primary_key_position": row[5],
        }
        for row in rows
    ]


def build_document(database: Path, options: Path) -> dict[str, object]:
    query_map = json.loads(QUERY_MAP.read_text())
    sql_index = json.loads(SQL_INDEX.read_text())
    families = query_map["families"]
    logical_tables = sorted({table for family in families for table in family["tables"]})

    connection = connect(database, key_from_options(options), readonly=True)
    physical_names = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )
    }

    tables = []
    for table in logical_tables:
        table_families = [family for family in families if table in family["tables"]]
        if table not in physical_names:
            classification = NON_PHYSICAL.get(
                table,
                {
                    "kind": "absent-from-appsync-fixture",
                    "explanation": "Named by the query map but absent from this AppSync fixture schema.",
                },
            )
            tables.append(
                {
                    "name": table,
                    "physical_in_appsync_fixture": False,
                    **classification,
                    "request_families": [family["id"] for family in table_families],
                    "request_kinds": request_kinds(table_families),
                    "columns": [],
                }
            )
            continue

        literals = [
            literal
            for literal in sql_index["literals"]
            if word_present(literal["literal"], table)
        ]
        columns = schema_columns(connection, table)
        semantic_text = " ".join(family_text(family) for family in table_families)
        for column in columns:
            explicit_literals = [
                literal["literal"]
                for literal in literals
                if word_present(literal["literal"], column["name"])
            ]
            semantic_families = [
                family["id"]
                for family in table_families
                if word_present(family_text(family), column["name"])
            ]
            semantic_family_rows = [
                family
                for family in table_families
                if family["id"] in semantic_families
            ]
            column["evidence"] = {
                "returned_by_exact_select_star": any(
                    re.search(rf"select\s+\*\s+from\s+{re.escape(table)}\b", literal["literal"], re.I)
                    for literal in literals
                ),
                "exact_sql_literals": explicit_literals,
                "semantic_query_families": semantic_families,
                "semantic_request_kinds": request_kinds(semantic_family_rows),
                "schema_only": not explicit_literals
                and not semantic_families
                and not word_present(semantic_text, column["name"]),
            }

        tables.append(
            {
                "name": table,
                "physical_in_appsync_fixture": True,
                "kind": "appsync-fixture-table",
                "request_families": [family["id"] for family in table_families],
                "request_kinds": request_kinds(table_families),
                "exact_sql_literals": [literal["literal"] for literal in literals],
                "columns": columns,
            }
        )

    connection.close()
    request_index = []
    for family in families:
        semantic_fields = sorted(
            f"{table['name']}.{column['name']}"
            for table in tables
            for column in table["columns"]
            if family["id"] in column["evidence"]["semantic_query_families"]
        )
        for request in family["requests"]:
            request_index.append(
                {
                    "kind": request.upper(),
                    "family": family["id"],
                    "operation": family["operation"],
                    "tables": family["tables"],
                    "family_semantic_fields": semantic_fields,
                    "evidence": family["evidence"],
                }
            )
    request_index.sort(key=lambda item: int(item["kind"], 16))

    return {
        "format": 1,
        "product": "rekordbox 7.2.19",
        "scope": (
            "Schema and field-level evidence for every table-like name in the "
            "Link Export request-to-database map."
        ),
        "authority_rules": {
            "schema": "PRAGMA table_info from the deterministic encrypted full AppSync fixture.",
            "exact_sql": "Literal SQL retained in disassembly evidence; SELECT * proves row retrieval, not downstream field use.",
            "semantic_query_family": "A field named explicitly in the reconstructed family predicate, ordering, or result description.",
            "schema_only": "The field exists, but this index makes no Link Export read/use claim for it.",
        },
        "sources": {
            "database": {
                "path": database.relative_to(ROOT).as_posix(),
                "sha256": sha256(database),
                "key_handling": "Decoded from the project options file in memory; neither key nor options contents are retained.",
            },
            "query_map": {
                "path": QUERY_MAP.relative_to(ROOT).as_posix(),
                "sha256": sha256(QUERY_MAP),
            },
            "sql_literal_index": {
                "path": SQL_INDEX.relative_to(ROOT).as_posix(),
                "sha256": sha256(SQL_INDEX),
            },
        },
        "summary": {
            "logical_table_names": len(logical_tables),
            "mapped_request_kinds": len(request_index),
            "physical_appsync_tables": sum(table in physical_names for table in logical_tables),
            "non_physical_or_alternate_names": sum(table not in physical_names for table in logical_tables),
            "physical_columns": sum(len(item["columns"]) for item in tables),
        },
        "requests": request_index,
        "tables": tables,
    }


def markdown(document: dict[str, object]) -> str:
    summary = document["summary"]
    lines = [
        "# Database field reference",
        "",
        "This generated reference enumerates the database fields behind the Link",
        "Export request map for Rekordbox 7.2.19. It keeps four claims distinct:",
        "the field exists in the deterministic AppSync fixture, literal SQL retrieves",
        "or names it, the reconstructed request-family description names it, or the",
        "field is schema-only and has no Link Export use claim here.",
        "",
        "A recovered `SELECT *` proves that Rekordbox retrieves the complete database",
        "row. It does not prove that every returned field affects a response. The exact",
        "SQL evidence remains in `SQL_LITERAL_INDEX.md`; logical pipelines remain in",
        "`DATABASE_QUERIES.md`.",
        "",
        f"The index covers {summary['logical_table_names']} table-like names:",
        f"{summary['physical_appsync_tables']} physical AppSync fixture tables and",
        f"{summary['non_physical_or_alternate_names']} runtime or alternate-interface names,",
        f"with {summary['physical_columns']} physical columns.",
        f"It directly joins those names to {summary['mapped_request_kinds']} wire request kinds.",
        "",
        "The machine-readable authority is",
        "`data/database/link-export-schema.json`. The SQLCipher key is decoded only in",
        "memory and is never written to either generated artifact.",
        "",
        "## Evidence legend",
        "",
        "- **STAR**: at least one retained exact SQL literal selects the complete row.",
        "- **SQL**: an exact SQL literal names this field.",
        "- **SEM**: a request-family predicate, ordering, or result description names it.",
        "- **SCHEMA**: presence only; no field-use claim is made.",
        "",
        "## Request-kind index",
        "",
        "This inverse index maps every classified wire request to its database-path",
        "family, operation, table set, and fields explicitly named by that family's",
        "reconstructed predicate, ordering, or result description. The field list is",
        "family-level evidence: a multi-stage family can name a field used by only one",
        "stage, so membership does not assert that every request in that family reads",
        "every listed field.",
        "",
        "| Request | Family | Operation | Tables | Family-named fields | Evidence |",
        "|---:|---|---|---|---|---|",
    ]
    for request in document["requests"]:
        tables = ", ".join(f"`{name}`" for name in request["tables"]) or "none"
        fields = (
            ", ".join(f"`{name}`" for name in request["family_semantic_fields"])
            or "none named"
        )
        evidence = ", ".join(request["evidence"])
        lines.append(
            f"| `0x{request['kind'].lower()}` | `{request['family']}` | "
            f"`{request['operation']}` | {tables} | {fields} | {evidence} |"
        )

    lines.extend(
        [
        "",
        "## Runtime and alternate-interface names",
        "",
        ]
    )
    for table in document["tables"]:
        if table["physical_in_appsync_fixture"]:
            continue
        lines.extend(
            [
                f"### `{table['name']}`",
                "",
                f"Classification: `{table['kind']}`.",
                "",
                table["explanation"],
                "",
                "Request families: " + ", ".join(f"`{name}`" for name in table["request_families"]) + ".",
                "",
                "Request kinds: " + ", ".join(f"`0x{kind.lower()}`" for kind in table["request_kinds"]) + ".",
                "",
            ]
        )

    lines.extend(["## Physical AppSync tables", ""])
    for table in document["tables"]:
        if not table["physical_in_appsync_fixture"]:
            continue
        lines.extend(
            [
                f"### `{table['name']}`",
                "",
                "Request families: " + ", ".join(f"`{name}`" for name in table["request_families"]) + ".",
                "",
                "Request kinds: " + ", ".join(f"`0x{kind.lower()}`" for kind in table["request_kinds"]) + ".",
                "",
                "| Column | Declared type | Evidence | Family or exact-SQL detail |",
                "|---|---|---|---|",
            ]
        )
        for column in table["columns"]:
            evidence = column["evidence"]
            labels = []
            if evidence["returned_by_exact_select_star"]:
                labels.append("STAR")
            if evidence["exact_sql_literals"]:
                labels.append("SQL")
            if evidence["semantic_query_families"]:
                labels.append("SEM")
            if not labels:
                labels.append("SCHEMA")
            details = []
            if evidence["semantic_query_families"]:
                details.append("families " + ", ".join(f"`{name}`" for name in evidence["semantic_query_families"]))
                details.append(
                    "requests "
                    + ", ".join(
                        f"`0x{kind.lower()}`"
                        for kind in evidence["semantic_request_kinds"]
                    )
                )
            if evidence["exact_sql_literals"]:
                details.append(f"named by {len(evidence['exact_sql_literals'])} literal(s)")
            lines.append(
                f"| `{column['name']}` | `{column['declared_type'] or 'untyped'}` | "
                f"{', '.join(labels)} | {'; '.join(details) or 'presence only'} |"
            )
        lines.append("")

    lines.extend(
        [
            "## Reproduce",
            "",
            "```bash",
            ".venv/bin/python tools/generate_database_field_reference.py \\",
            "  --database conformance/fixtures/generated/full/master.db \\",
            "  --options /mnt/documents/multimedia/djing/rekordbox/options.json",
            "```",
            "",
            "Regeneration reads schema metadata only. It does not export library rows or",
            "persist the database key.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    parser.add_argument("--options", type=Path, default=DEFAULT_OPTIONS)
    parser.add_argument("--json-output", type=Path, default=JSON_OUTPUT)
    parser.add_argument("--markdown-output", type=Path, default=MARKDOWN_OUTPUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    document = build_document(args.database.resolve(), args.options.resolve())
    args.json_output.write_text(json.dumps(document, indent=2) + "\n")
    args.markdown_output.write_text(markdown(document))


if __name__ == "__main__":
    main()
