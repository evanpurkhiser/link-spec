#!/usr/bin/env python3
"""Validate and summarize the real-Rekordbox Play path/cloud oracle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
GOLDEN = (
    ROOT
    / "conformance/goldens/rekordbox-7.2.19/xdj-rx3/song-info-play-paths.json"
)
EXPECTED_BEHAVIOR_SHA256 = "46f735e9d060f3d00b1280384d8bf8c12126c9f7039667e7b3bc54020ee46108"


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def row_values(case: dict, index: int) -> list[object]:
    return [argument["value"] for argument in case["rows"][index]["arguments"]]


def main() -> None:
    document = load(GOLDEN)
    behavior_bytes = (
        json.dumps(document["behavior"], sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode()
    assert hashlib.sha256(behavior_bytes).hexdigest() == EXPECTED_BEHAVIOR_SHA256
    provenance = document["provenance"]
    suite = Path(provenance["suite_path"])
    manifest = Path(provenance["manifest_path"])
    assert suite.is_file()
    assert manifest.is_file()
    assert hashlib.sha256(suite.read_bytes()).hexdigest() == provenance["suite_sha256"]

    fixture = load(manifest)
    assert fixture["profile"] == "play-paths"
    assert fixture["database_sha256"] == provenance["fixture_database_sha256"]
    assert fixture["fixture_fingerprint"] == provenance["fixture_fingerprint"]
    assert fixture["track_count"] == 14

    cases = document["behavior"]["cases"]
    assert [case["id"] for case in cases] == [
        f"track-{index:02}" for index in range(1, 15)
    ]
    assert [case["total"] for case in cases] == [
        7,
        0,
        7,
        7,
        7,
        7,
        7,
        7,
        7,
        0,
        7,
        7,
        7,
        7,
    ]

    base = "C:/Users/Research/link-export-conformance/play-paths"
    expected = {
        "track-01": (8864, f"{base}/local-control.wav", 1),
        "track-03": (0xFFFFFFFF, f"{base}/local-high-bit.wav", 0),
        "track-04": (0x7FFFFFFF, f"{base}/local-high-bits.wav", 1),
        "track-05": (1, f"{base}/org-existing.bin", 1),
        "track-06": (
            2,
            "C:/Users/Research/AppData/Roaming/Pioneer"
            f"{base}/cloud-mismatch-directory.wav",
            1,
        ),
        "track-07": (0xFFFFFFFF, f"{base}/cloud-match-missing.wav", 1),
        "track-08": (0, f"{base}/cloud-null-master-unicode-Ω.wav", 1),
        "track-09": (0, f"{base}/local-empty-hotcue.wav", 0),
        "track-11": (
            4,
            "C:/Users/Research/AppData/Roaming/Pioneer"
            f"{base}/cloud-match-existing-directory.wav",
            1,
        ),
        "track-12": (5, f"{base}/org-zero-byte.bin", 1),
        "track-13": (6, f"{base}/content-link-pair.wav", 1),
        "track-14": (6, f"{base}/content-link-pair.wav", 1),
    }

    print("| Case | Total | File size | Returned path | Hot-cue flag |")
    print("| --- | ---: | ---: | --- | ---: |")
    for case in cases:
        if case["total"] == 0:
            print(f"| `{case['id']}` | 0 | - | - | - |")
            continue

        assert len(case["rows"]) == 7
        path = row_values(case, 4)
        hotcue = row_values(case, 5)
        observed = (path[0], path[3], hotcue[1])
        assert observed == expected[case["id"]]
        assert path[2] == len(path[3].encode("utf-16-le")) + 2
        print(
            f"| `{case['id']}` | 7 | `{path[0]}` | `{path[3]}` | "
            f"`{hotcue[1]}` |"
        )

    content_link_zero = row_values(cases[12], 4)
    content_link_high = row_values(cases[13], 4)
    assert content_link_zero[:1] == content_link_high[:1]
    assert content_link_zero[2:] == content_link_high[2:]
    print("\nValidated facts:")
    print("- null and empty FolderPath produce a zero-row menu")
    print("- FileSize is serialized modulo 2^32")
    print("- empty and null HotCueAutoLoad produce 0; every nonempty value produces 1")
    print("- a matching cloud DB selects an existing regular OrgFolderPath")
    print("- an existing directory fails the regular-file test; a zero-byte file passes")
    print("- ContentLink 0 and 0x80 path fields are exact after content-ID normalization")
    print(f"- complete behavior SHA-256: `{EXPECTED_BEHAVIOR_SHA256}`")


if __name__ == "__main__":
    main()
