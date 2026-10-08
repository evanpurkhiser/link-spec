#!/usr/bin/env python3
"""Inventory SmartList XML structure without retaining user condition values."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "conformance"))

from build_fixture import connect, key_from_options  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("database", type=Path)
    parser.add_argument("options", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    connection = connect(args.database, key_from_options(args.options), readonly=True)
    rows = connection.execute(
        "SELECT SmartList FROM djmdPlaylist "
        "WHERE rb_local_deleted = 0 AND SmartList IS NOT NULL AND SmartList != ''"
    ).fetchall()
    connection.close()

    properties = Counter()
    operators = Counter()
    units = Counter()
    pairs = Counter()
    logical_operators = Counter()
    automatic_updates = Counter()
    root_attributes = Counter()
    condition_attributes = Counter()
    condition_counts = Counter()
    node_counts = Counter()
    property_operators: dict[str, Counter[str]] = defaultdict(Counter)
    parse_errors = 0

    for (xml,) in rows:
        try:
            root = ET.fromstring(xml)
        except (ET.ParseError, TypeError):
            parse_errors += 1
            continue

        roots = [root] if root.tag == "NODE" else list(root.iter("NODE"))
        nodes = list(root.iter("NODE"))
        conditions = list(root.iter("CONDITION"))
        node_counts[len(nodes)] += 1
        condition_counts[len(conditions)] += 1
        for node in roots[:1]:
            root_attributes.update(node.attrib.keys())
            logical_operators[node.attrib.get("LogicalOperator", "<missing>")] += 1
            automatic_updates[node.attrib.get("AutomaticUpdate", "<missing>")] += 1
        for condition in conditions:
            condition_attributes.update(condition.attrib.keys())
            property_name = condition.attrib.get("PropertyName", "<missing>")
            operator = condition.attrib.get("Operator", "<missing>")
            unit = condition.attrib.get("ValueUnit", "<missing>")
            properties[property_name] += 1
            operators[operator] += 1
            units[unit or "<empty>"] += 1
            pairs[f"{property_name}:{operator}"] += 1
            property_operators[property_name][operator] += 1

    report = {
        "format": "rekordbox-smart-list-structure-inventory-v1",
        "source": {
            "database_sha256": sha256(args.database),
            "values_retained": False,
            "playlist_names_retained": False,
        },
        "counts": {
            "smart_lists": len(rows),
            "parsed": len(rows) - parse_errors,
            "parse_errors": parse_errors,
            "conditions": sum(properties.values()),
        },
        "root": {
            "attribute_occurrences": dict(sorted(root_attributes.items())),
            "logical_operators": dict(sorted(logical_operators.items())),
            "automatic_updates": dict(sorted(automatic_updates.items())),
            "node_count_histogram": numeric_keys(node_counts),
            "condition_count_histogram": numeric_keys(condition_counts),
        },
        "conditions": {
            "attribute_occurrences": dict(sorted(condition_attributes.items())),
            "properties": dict(sorted(properties.items())),
            "operators": dict(sorted(operators.items())),
            "units": dict(sorted(units.items())),
            "property_operator_pairs": dict(sorted(pairs.items())),
            "operators_by_property": {
                name: dict(sorted(values.items()))
                for name, values in sorted(property_operators.items())
            },
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(args.output)


def numeric_keys(counter: Counter[int]) -> dict[str, int]:
    return {str(key): counter[key] for key in sorted(counter)}


def sha256(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


if __name__ == "__main__":
    main()
