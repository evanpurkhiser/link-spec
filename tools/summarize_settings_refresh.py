#!/usr/bin/env python3
"""Validate and summarize the same-process Category/Sort refresh evidence."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path

from Crypto.Cipher import Blowfish
from sqlcipher3 import dbapi2 as sqlite


ROOT_LABELS_WITHOUT_ALBUM = [
    "TRACK",
    "KEY",
    "BPM",
    "GENRE",
    "ARTIST",
    "MATCHING",
    "SEARCH",
    "PLAYLIST",
    "HISTORY",
    "BITRATE",
    "COLOR",
    "FILE NAME",
    "HOT CUE BANK",
    "LABEL",
    "ORIGINAL ARTIST",
    "RATING",
    "REMIXER",
    "TIME",
    "YEAR",
]
SORT_LABELS_WITH_COMMENTS = [
    "DEFAULT",
    "ALPHABET",
    "ARTIST",
    "ALBUM",
    "BPM",
    "RATING",
    "KEY",
    "LABEL",
    "GENRE",
    "DATE ADDED",
    "DJ PLAY COUNT",
    "COMMENTS",
]
SCREENSHOTS = (
    "category-album-before.png",
    "category-album-inactive.png",
    "sort-comments-before.png",
    "sort-comments-active.png",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha256(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def database_key(options_path: Path) -> str:
    options = dict(json.loads(options_path.read_text())["options"])
    encrypted = base64.b64decode(options["dp"])
    decrypted = Blowfish.new(b"ZOwUlUZYqe9Rdm6j", Blowfish.MODE_ECB).decrypt(encrypted)
    return decrypted.rstrip(b"\x00 \t\r\n").decode()


def connect(path: Path, key: str):
    connection = sqlite.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True)
    connection.execute("PRAGMA key = '" + key.replace("'", "''") + "'")
    connection.execute("PRAGMA cipher_compatibility = 4")
    connection.execute("SELECT count(*) FROM sqlite_master").fetchone()
    return connection


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text())


def row_labels(golden: dict[str, object]) -> list[str]:
    case = golden["behavior"]["cases"][0]
    messages = [
        message
        for page in case["pages"]
        for message in page["messages"]
        if message["kind"] == 0x4101
    ]
    return [message["arguments"][3]["value"].strip("\ufffa\ufffb") for message in messages]


def validate_golden(
    golden_path: Path,
    suite_path: Path,
    manifest: dict[str, object],
    labels: list[str],
) -> dict[str, object]:
    golden = load_json(golden_path)
    provenance = golden["provenance"]
    case = golden["behavior"]["cases"][0]

    assert provenance["backend"] == "rekordbox"
    assert provenance["backend_version"] == "7.2.19"
    assert provenance["suite_sha256"] == sha256(suite_path)
    assert provenance["fixture_database_sha256"] == manifest["database_sha256"]
    assert provenance["fixture_fingerprint"] == manifest["fixture_fingerprint"]
    assert case["outcome"] == "menu"
    assert case["total"] == len(labels)
    assert row_labels(golden) == labels

    return {
        "path": str(golden_path),
        "sha256": sha256(golden_path),
        "behavior_sha256": canonical_sha256(golden["behavior"]),
        "suite_sha256": provenance["suite_sha256"],
        "recorded_unix_seconds": provenance["recorded_unix_seconds"],
        "total": case["total"],
        "labels": labels,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--options", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    data = Path("data/session-refresh")
    manifest_path = Path("conformance/fixtures/generated/full/manifest.json")
    manifest = load_json(manifest_path)
    category_suite = data / "category-album-probe.json"
    sort_suite = data / "sort-comments-probe.json"
    category_golden = data / "category-album-same-process.json"
    sort_golden = data / "sort-comments-same-process.json"
    lifecycle = load_json(data / "settings-refresh-lifecycle.json")
    database = data / "settings-refresh-master.db"

    category = validate_golden(
        category_golden,
        category_suite,
        manifest,
        ROOT_LABELS_WITHOUT_ALBUM,
    )
    sort = validate_golden(
        sort_golden,
        sort_suite,
        manifest,
        SORT_LABELS_WITH_COMMENTS,
    )

    assert lifecycle["interactive_ready_unix_seconds"] < category["recorded_unix_seconds"]
    assert category["recorded_unix_seconds"] < sort["recorded_unix_seconds"]
    assert lifecycle["category_recorded_unix_seconds"] == category["recorded_unix_seconds"]
    assert lifecycle["sort_recorded_unix_seconds"] == sort["recorded_unix_seconds"]

    connection = connect(database, database_key(args.options))
    integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
    album = connection.execute(
        "SELECT ID, MenuItemID, Seq, Disable, InfoOrder FROM djmdCategory WHERE ID = '3'"
    ).fetchone()
    comments = connection.execute(
        "SELECT ID, MenuItemID, Seq, Disable FROM djmdSort WHERE ID = '7'"
    ).fetchone()
    connection.close()

    assert integrity == "ok"
    assert list(album) == ["3", "3", 0, 1, 3]
    assert list(comments) == ["7", "21", 12, 0]
    assert sha256(database) == manifest["database_sha256"]

    report = {
        "format": "rekordbox-link-export-settings-refresh-v1",
        "fixture": {
            "manifest": str(manifest_path),
            "database_sha256": manifest["database_sha256"],
            "fixture_fingerprint": manifest["fixture_fingerprint"],
        },
        "lifecycle": lifecycle,
        "database_snapshot": {
            "database_sha256": sha256(database),
            "wal_sha256": sha256(data / "settings-refresh-master.db-wal"),
            "shm_sha256": sha256(data / "settings-refresh-master.db-shm"),
            "integrity": integrity,
            "album_category": list(album),
            "comments_sort": list(comments),
        },
        "category_oracle": category,
        "sort_oracle": sort,
        "screenshots": {
            name: sha256(data / name)
            for name in SCREENSHOTS
        },
    }
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered)
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
