#!/usr/bin/env python3
"""Validate and summarize RX3 status menu-location-2 experiments."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
EXPERIMENTS = ROOT / "data/experiments/song-info-status-location2"
FAMILIES = {
    "delivery-only-header": None,
    "play-zero": ("timeout", None),
    "play-primary": ("menu", 7),
    "play-location2": ("menu", 7),
    "display-primary": ("menu", 16),
    "display-location2": ("menu", 16),
    "delivery-primary": ("menu", 13),
}


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def behavior_bytes(document: dict) -> bytes:
    value = json.dumps(
        document["behavior"], sort_keys=True, separators=(",", ":")
    )
    return f"{value}\n".encode()


def digest(document: dict) -> str:
    return hashlib.sha256(behavior_bytes(document)).hexdigest()


def validate_suite_hash(document: dict) -> None:
    path = Path(document["provenance"]["suite_path"])
    assert path.is_file(), path
    assert hashlib.sha256(path.read_bytes()).hexdigest() == document["provenance"][
        "suite_sha256"
    ]


def paired(family: str) -> tuple[dict, dict]:
    documents = tuple(
        load(EXPERIMENTS / f"{family}-run-{run}.json") for run in (1, 2)
    )
    for document in documents:
        validate_suite_hash(document)
    assert behavior_bytes(documents[0]) == behavior_bytes(documents[1])

    return documents


def same_connection_pair(family: str) -> tuple[dict, dict]:
    return paired(f"{family}-same-connection")


def assert_same_results(reconnect: dict, persistent: dict) -> None:
    for key in ("cases", "fixture", "setup", "setup_exchange"):
        assert reconnect["behavior"][key] == persistent["behavior"][key], key


def validate_connection_failure_logs() -> None:
    expected_cases = [
        "play-no-arguments-precursor",
        "play-no-arguments-precursor-delivery-probe",
        "play-missing-content-precursor",
        "play-missing-content-precursor-delivery-probe",
        "play-extra-argument-precursor",
        "play-extra-argument-precursor-delivery-probe",
        "play-string-context-precursor",
        "play-string-context-precursor-delivery-probe",
    ]

    for run in (1, 2):
        text = (
            EXPERIMENTS
            / f"malformed-prefix-same-connection-run-{run}.log"
        ).read_text()
        positions = [text.index(f"running case {case}") for case in expected_cases]
        assert positions == sorted(positions)
        assert text.count("dbserver closed the connection") == 1
        assert positions[-1] < text.index("dbserver closed the connection")
        assert "running case play-blob-context-precursor" not in text


def result(case: dict) -> tuple[str, int | None]:
    return case["outcome"], case["total"]


def main() -> None:
    print("Header-only precursor matrix:")
    print("| Family | Cases/run | Precursor | Location-2 Delivery | Behavior SHA-256 |")
    print("| --- | ---: | --- | --- | --- |")
    for family, expected_precursor in FAMILIES.items():
        document, _ = paired(family)
        persistent, _ = same_connection_pair(family)
        assert_same_results(document, persistent)
        cases = document["behavior"]["cases"]
        probes = [case for case in cases if case["id"].endswith("delivery-probe")]
        precursors = [case for case in cases if case not in probes]

        assert {result(case) for case in probes} == {("menu", 13)}
        if expected_precursor is None:
            assert not precursors
            precursor_text = "none"
        else:
            assert {result(case) for case in precursors} == {expected_precursor}
            precursor_text = f"{expected_precursor[0]} / {expected_precursor[1]}"
        print(
            f"| `{family}` | {len(cases)} | {precursor_text} | menu / 13 | "
            f"`{digest(document)}` |"
        )

    print("\nPersistent connection cross:")
    print("- 208 case executions across fourteen recordings")
    print("- every case, setup exchange, and fixture equals its reconnect control")
    print("- zero-context Play timeouts leave the shared socket usable")

    malformed, _ = paired("malformed-prefix")
    cases = malformed["behavior"]["cases"]
    empty_after = []
    for precursor, probe in zip(cases[::2], cases[1::2], strict=True):
        assert probe["id"] == f"{precursor['id']}-delivery-probe"
        if precursor["id"] in {
            "play-blob-content-precursor",
            "delivery-blob-content-precursor",
        }:
            assert result(probe) == ("menu", 0)
            empty_after.append(precursor["id"])
        else:
            assert result(probe) == ("menu", 13)

    print("\nMalformed prefix bisection:")
    print(f"- cases/run: {len(cases)}")
    print(f"- behavior SHA-256: `{digest(malformed)}`")
    print("- empty Delivery after: " + ", ".join(f"`{item}`" for item in empty_after))
    print("- Delivery total after every other precursor: 13")

    validate_connection_failure_logs()
    print("\nMalformed persistent-connection cutoff:")
    print("- reproduced in two independent cold processes")
    print("- the wrong-typed Play context is followed by a dbserver socket close")
    print("- the immediately following Delivery probe cannot complete")

    rendered, _ = paired("delivery-only")
    rendered_cases = rendered["behavior"]["cases"]
    assert {result(case) for case in rendered_cases} == {("render_timeout", 13)}
    print("\nRender-location control:")
    print("- eight location-2 menus advertise total 13")
    print("- rendering with the default location-1 context times out eight times")
    print(f"- behavior SHA-256: `{digest(rendered)}`")


if __name__ == "__main__":
    main()
