#!/usr/bin/env python3
import argparse
import base64
import hashlib
import json
from pathlib import Path

from Crypto.Cipher import Blowfish
from sqlcipher3 import dbapi2 as sqlite


PASSPHRASE_KEY = b"ZOwUlUZYqe9Rdm6j"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def database_key(options_path: Path) -> str:
    options = dict(json.loads(options_path.read_text())["options"])
    encrypted = base64.b64decode(options["dp"])
    return (
        Blowfish.new(PASSPHRASE_KEY, Blowfish.MODE_ECB)
        .decrypt(encrypted)
        .rstrip(b"\x00 \t\r\n")
        .decode()
    )


def grouped_counts(connection, column: str) -> list[dict]:
    rows = connection.execute(
        f"SELECT {column}, count(*) FROM djmdContent "
        f"GROUP BY {column} ORDER BY {column}"
    ).fetchall()
    return [{"value": value, "count": count} for value, count in rows]


def audit_database(path: Path, key: str) -> dict:
    connection = sqlite.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True)
    connection.execute("PRAGMA key = '" + key.replace("'", "''") + "'")
    connection.execute("PRAGMA cipher_compatibility = 4")

    ids = [str(row[0]) for row in connection.execute("SELECT ID FROM djmdContent ORDER BY ID")]
    total = connection.execute("SELECT count(*) FROM djmdContent").fetchone()[0]
    live = connection.execute(
        "SELECT count(*) FROM djmdContent WHERE rb_local_deleted = 0"
    ).fetchone()[0]
    integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
    deleted = grouped_counts(connection, "rb_local_deleted")
    content_links = grouped_counts(connection, "ContentLink")
    connection.close()

    return {
        "path": str(path.resolve()),
        "database_sha256": sha256(path),
        "integrity_check": integrity,
        "total_rows": total,
        "live_rows": live,
        "deleted_partitions": deleted,
        "content_link_partitions": content_links,
        "ordered_content_id_sha256": hashlib.sha256(
            ("\n".join(ids) + "\n").encode()
        ).hexdigest(),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--options", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--relocated", type=Path, required=True)
    parser.add_argument("--relocation-report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    key = database_key(args.options)
    source = audit_database(args.source, key)
    relocated = audit_database(args.relocated, key)
    relocation = json.loads(args.relocation_report.read_text())

    assert source["total_rows"] == relocated["total_rows"]
    assert source["ordered_content_id_sha256"] == relocated["ordered_content_id_sha256"]
    assert relocation["tracks"] == relocated["total_rows"]
    assert relocation["mapped"] + len(relocation["unresolved"]) == relocation["tracks"]

    result = {
        "format": 1,
        "scope": "2026-09-29 source and relocated database copies",
        "options_sha256": sha256(args.options),
        "relocation_report_sha256": sha256(args.relocation_report),
        "relocation": {
            "tracks": relocation["tracks"],
            "mapped": relocation["mapped"],
            "unresolved": len(relocation["unresolved"]),
        },
        "source": source,
        "relocated": relocated,
        "content_ids_equal": True,
        "content_link_partitions_equal": (
            source["content_link_partitions"] == relocated["content_link_partitions"]
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(args.output)


if __name__ == "__main__":
    main()
