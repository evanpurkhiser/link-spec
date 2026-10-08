#!/usr/bin/env python3
"""Export non-secret Link Export configuration from an encrypted master.db."""

from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import json
from pathlib import Path

from Crypto.Cipher import Blowfish
from sqlcipher3 import dbapi2 as sqlite


TABLE_COLUMNS = {
    "djmdMenuItems": ("ID", "Class", "Name"),
    "djmdCategory": ("ID", "MenuItemID", "Seq", "Disable", "InfoOrder"),
    "djmdSort": ("ID", "MenuItemID", "Seq", "Disable"),
    "djmdColor": ("ID", "ColorCode", "SortKey", "Commnt"),
}


def database_key(options_path: Path) -> str:
    options = dict(json.loads(options_path.read_text())["options"])
    encrypted = base64.b64decode(options["dp"])
    decrypted = Blowfish.new(b"ZOwUlUZYqe9Rdm6j", Blowfish.MODE_ECB).decrypt(encrypted)
    return decrypted.rstrip(b"\x00 \t\r\n").decode()


def connect(path: Path, key: str):
    connection = sqlite.connect(f"{path.as_uri()}?mode=ro", uri=True)
    connection.execute("PRAGMA key = '" + key.replace("'", "''") + "'")
    connection.execute("PRAGMA cipher_compatibility = 4")
    connection.execute("SELECT count(*) FROM sqlite_master").fetchone()
    return connection


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def export_table(connection, output: Path, table: str, columns: tuple[str, ...]) -> int:
    rows = connection.execute(
        f"SELECT {', '.join(columns)} FROM {table} "
        "WHERE rb_local_deleted = 0 ORDER BY CAST(ID AS INTEGER)"
    ).fetchall()

    with (output / f"{table}.csv").open("w", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(columns)
        writer.writerows(rows)

    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("database", type=Path)
    parser.add_argument("options", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)
    connection = connect(args.database.resolve(), database_key(args.options))

    counts = {
        table: export_table(connection, args.output, table, columns)
        for table, columns in TABLE_COLUMNS.items()
    }
    schemas = {
        table: connection.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = ?", (table,)
        ).fetchone()[0]
        for table in TABLE_COLUMNS
    }
    selected = [
        row[0]
        for row in connection.execute(
            "SELECT ID FROM djmdSort "
            "WHERE rb_local_deleted = 0 AND (Disable & 2) = 2 "
            "ORDER BY CAST(ID AS INTEGER)"
        )
    ]
    connection.close()

    metadata = {
        "database": str(args.database),
        "database_sha256": sha256(args.database),
        "rows": counts,
        "schemas": schemas,
        "selected_secondary_sort_ids": selected,
    }
    (args.output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")


if __name__ == "__main__":
    main()
