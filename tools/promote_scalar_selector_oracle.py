#!/usr/bin/env python3
"""Promote repeated scalar-selector probes into canonical suites."""

from pathlib import Path

from promote_search_oracle import exact_suite, write


ROOT = Path(__file__).resolve().parent.parent
EXPERIMENT = ROOT / "data/experiments/scalar-selectors"
SUITES = ROOT / "conformance/suites"


def main() -> None:
    drilldowns = exact_suite(
        EXPERIMENT / "probe.json",
        EXPERIMENT / "record.json",
        "scalar-selector-drilldowns",
    )
    write(SUITES / "scalar-selector-drilldowns.json", drilldowns)

    boundaries = exact_suite(
        EXPERIMENT / "boundary-probe.json",
        EXPERIMENT / "boundary-record.json",
        "scalar-selector-boundaries",
    )
    write(SUITES / "scalar-selector-boundaries.json", boundaries)


if __name__ == "__main__":
    main()
