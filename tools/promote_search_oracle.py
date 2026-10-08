#!/usr/bin/env python3
"""Promote repeated Search probes into exact canonical suite declarations."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
EXPERIMENT = ROOT / "data/experiments/search"
SUITES = ROOT / "conformance/suites"


def load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text())


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def exact_suite(
    suite_path: Path,
    record_path: Path,
    name: str,
) -> dict[str, object]:
    suite = load(suite_path)
    record = load(record_path)
    behavior = record["behavior"]
    provenance = record["provenance"]

    assert provenance["suite_sha256"] == sha256(suite_path)
    assert len(suite["cases"]) == len(behavior["cases"])

    observed = {case["id"]: case for case in behavior["cases"]}
    promoted = []
    for declaration in suite["cases"]:
        case = observed[declaration["id"]]
        expect = {"outcome": case["outcome"]}
        if case.get("total") is not None:
            expect["total"] = case["total"]
        if declaration.get("render", True):
            expect["row_count"] = len(case["rows"])
        promoted.append({**declaration, "expect": expect})

    return {**suite, "name": name, "cases": promoted}


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def main() -> None:
    broad = exact_suite(
        EXPERIMENT / "search-probe.json",
        EXPERIMENT / "search-probe-record.json",
        "search-conformance",
    )
    boundary = exact_suite(
        EXPERIMENT / "search-boundary-probe.json",
        EXPERIMENT / "search-boundary-probe-record.json",
        "search-conformance",
    )
    broad["cases"].extend(boundary["cases"])
    write(SUITES / "search.json", broad)

    ceiling = exact_suite(
        EXPERIMENT / "search-ceiling-probe.json",
        EXPERIMENT / "search-ceiling-probe-record.json",
        "search-ceiling-conformance",
    )
    write(SUITES / "search-ceiling.json", ceiling)

    text = exact_suite(
        EXPERIMENT / "search-text-probe.json",
        EXPERIMENT / "search-text-probe-record.json",
        "search-text-conformance",
    )
    write(SUITES / "search-text.json", text)

    search_track = exact_suite(
        EXPERIMENT / "search-track-probe.json",
        EXPERIMENT / "search-track-probe-record.json",
        "search-track-conformance",
    )
    write(SUITES / "search-track.json", search_track)

    search_track_ceiling = exact_suite(
        EXPERIMENT / "search-track-ceiling-probe.json",
        EXPERIMENT / "search-track-ceiling-probe-record.json",
        "search-track-ceiling-conformance",
    )
    write(SUITES / "search-track-ceiling.json", search_track_ceiling)

    search_track_large_title = exact_suite(
        EXPERIMENT / "search-track-large-title-sort-probe.json",
        EXPERIMENT / "search-track-large-title-sort-probe-record.json",
        "search-track-large-title-sort-conformance",
    )
    write(
        SUITES / "search-track-large-title-sort.json",
        search_track_large_title,
    )

    for category in ("02", "03", "04", "21"):
        name = f"search-category-{category}-disabled"
        suite = exact_suite(
            EXPERIMENT / "search-category-domain-probe.json",
            EXPERIMENT / f"category-{category}-disabled-record.json",
            name,
        )
        write(SUITES / f"generated/{name}.json", suite)


if __name__ == "__main__":
    main()
