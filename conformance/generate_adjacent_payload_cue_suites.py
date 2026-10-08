#!/usr/bin/env python3
"""Generate successful and boundary cue-payload service suites."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from generate_adjacent_payload_suite import case, number


ROOT = Path(__file__).resolve().parent
BASE_SUITE = ROOT / "suites/adjacent-payload-cue-success.json"
GENERATED = ROOT / "suites/generated/adjacent-payload-cues"
INDEX = ROOT / "data/adjacent-payload-cue-matrix.json"

SAFE_CONTENTS = (
    "zero",
    "one",
    "three",
    "count_255",
    "count_256",
    "timing",
    "color",
    "comment_empty",
    "comment_ascii",
    "comment_unicode",
    "comment_nul",
    "beat_loop",
    "microseconds",
    "null_options",
    "deleted_only",
    "mixed_deleted",
)
STATUS_CONTENTS = ("zero", "one", "three", "count_255", "count_256", "comment_unicode")
RISK_CONTENTS = ("seek_in", "seek_out_only", "seek_malformed")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def context(player: int, location: int, track_type: int) -> int:
    return (player << 24) | (location << 16) | (3 << 8) | track_type


def cue_case(
    identifier: str,
    kind: str,
    content: str,
    *,
    player: int,
    location: int = 8,
    track_type: int = 1,
) -> dict:
    arguments = [
        number(context(player, location, track_type)),
        number(f"$fixture.track.cue_payload.{content}"),
    ]
    if kind == "2b04":
        arguments.append(number(0))
    return case(
        identifier,
        f"0x{kind} cue payload for {content.replace('_', ' ')}",
        kind,
        arguments,
    )


def base_cases() -> list[dict]:
    cases = []
    for kind in ("2104", "2b04"):
        for track_type in range(7):
            cases.append(
                cue_case(
                    f"kind-{kind}--type-{track_type:02x}",
                    kind,
                    "one",
                    player=1,
                    track_type=track_type,
                )
            )
        for location in (0, 1, 2, 3, 7, 8, 0xFF):
            cases.append(
                cue_case(
                    f"kind-{kind}--location-{location:02x}",
                    kind,
                    "one",
                    player=1,
                    location=location,
                )
            )

    for kind in ("2104", "2b04"):
        contents = (*SAFE_CONTENTS, *RISK_CONTENTS) if kind == "2104" else SAFE_CONTENTS
        for content in contents:
            cases.append(
                cue_case(
                    f"kind-{kind}--content-{content.replace('_', '-')}",
                    kind,
                    content,
                    player=1,
                )
            )
    return cases


def status_cases(player: int) -> list[dict]:
    return [
        cue_case(
            f"kind-{kind}--content-{content.replace('_', '-')}",
            kind,
            content,
            player=player,
        )
        for kind in ("2104", "2b04")
        for content in STATUS_CONTENTS
    ]


def suite(name: str, player: int, setup: str, cases: list[dict]) -> dict:
    return {
        "name": name,
        "fixture_profile": "adjacent-payload-cues",
        "fixture_version": 1,
        "defaults": {
            "device": player,
            "context": f"0x{context(player, 1, 1):08x}",
            "sort": 0,
            "root_capabilities": "0x05cfffff",
            "setup": setup,
            "page_size": 32,
            "read_timeout_ms": 5000,
            "render_arguments": [],
        },
        "cases": cases,
    }


def write(path: Path, document: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, indent=2) + "\n")


def generate(base_path: Path, generated: Path, index_path: Path) -> dict:
    generated.mkdir(parents=True, exist_ok=True)
    entries = []

    base = suite("Rekordbox adjacent cue payload success matrix", 1, "extended", base_cases())
    write(base_path, base)
    entries.append(
        {
            "variant": "baseline",
            "suite": BASE_SUITE.relative_to(ROOT).as_posix(),
            "suite_sha256": sha256(base_path),
            "golden_model": "xdj-rx3",
            "golden": "adjacent-payload-cue-success.json",
            "identity": "runs/xdj-rx3-player-11.json",
            "player": 1,
            "setup": "extended",
            "risk": "none",
            "case_count": len(base["cases"]),
            "service_count": 2,
        }
    )

    for content in RISK_CONTENTS:
        name = f"extended-{content.replace('_', '-')}"
        path = generated / f"{name}.json"
        document = suite(
            f"Rekordbox adjacent extended cue payload: {content}",
            1,
            "extended",
            [cue_case(f"kind-2b04--content-{content.replace('_', '-')}", "2b04", content, player=1)],
        )
        write(path, document)
        entries.append(
            {
                "variant": name,
                "suite": (GENERATED / path.name).relative_to(ROOT).as_posix(),
                "suite_sha256": sha256(path),
                "golden_model": "xdj-rx3",
                "golden": f"adjacent-payload-cue-{content.replace('_', '-')}.json",
                "identity": "runs/xdj-rx3-player-11.json",
                "player": 1,
                "setup": "extended",
                "risk": content,
                "case_count": 1,
                "service_count": 1,
            }
        )

    for model, player in (("cdj-3000-status", 1), ("xdj-rx3-status", 11)):
        for setup in ("extended", "legacy"):
            name = f"{model}-player-{player}-{setup}"
            path = generated / f"{name}.json"
            document = suite(
                f"Rekordbox adjacent cue payload {model} player {player} {setup}",
                player,
                setup,
                status_cases(player),
            )
            write(path, document)
            entries.append(
                {
                    "variant": name,
                    "suite": (GENERATED / path.name).relative_to(ROOT).as_posix(),
                    "suite_sha256": sha256(path),
                    "golden_model": model,
                    "golden": f"adjacent-payload-cue-success-{setup}.json",
                    "identity": f"runs/{'cdj-3000-player-1-status' if player == 1 else 'xdj-rx3-player-11-status'}.json",
                    "player": player,
                    "setup": setup,
                    "risk": "none",
                    "case_count": len(document["cases"]),
                    "service_count": 2,
                }
            )

    index = {
        "format": 1,
        "scope": "Rekordbox 7.2.19 adjacent cue payload declarations",
        "fixture_manifest": "fixtures/generated/adjacent-payload-cues/manifest.json",
        "fixture_manifest_sha256": sha256(ROOT / "fixtures/generated/adjacent-payload-cues/manifest.json"),
        "variant_count": len(entries),
        "case_count": sum(entry["case_count"] for entry in entries),
        "variants": entries,
    }
    write(index_path, index)
    return index


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-suite", type=Path, default=BASE_SUITE)
    parser.add_argument("--generated-dir", type=Path, default=GENERATED)
    parser.add_argument("--index", type=Path, default=INDEX)
    args = parser.parse_args()
    index = generate(args.base_suite, args.generated_dir, args.index)
    print(f"wrote {index['variant_count']} suites and {index['case_count']} cases")


if __name__ == "__main__":
    main()
