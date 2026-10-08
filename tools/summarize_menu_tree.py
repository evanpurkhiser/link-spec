#!/usr/bin/env python3
"""Create compact, reviewable indexes for a captured Link Export menu tree."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def value(argument: dict[str, Any] | None) -> Any:
    if not argument:
        return None
    return argument.get("value")


def row_field(row: list[dict[str, Any]], index: int) -> Any:
    return value(row[index]) if index < len(row) else None


def request_signature(menu: dict[str, Any]) -> str:
    request = menu["request"]
    kinds = []
    for argument in request.get("arguments", []):
        if isinstance(argument, int):
            kinds.append("number")
        elif isinstance(argument, str):
            kinds.append("string")
        elif isinstance(argument, dict):
            kinds.append(str(argument.get("type", "object")))
        else:
            kinds.append(type(argument).__name__)
    return f'{request["kind_hex"]}({", ".join(kinds)})'


def clean_label(label: Any) -> str:
    if not isinstance(label, str):
        return ""
    return label.removeprefix("\ufffa").removesuffix("\ufffb")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("capture", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    raw = args.capture.read_bytes()
    capture = json.loads(raw)
    args.output.mkdir(parents=True, exist_ok=True)

    node_rows: list[dict[str, Any]] = []
    signatures: dict[tuple[int, str, str], dict[str, Any]] = {}
    item_types: dict[int, dict[str, Any]] = defaultdict(
        lambda: {"rows": 0, "menus": set(), "labels": Counter()}
    )

    for index, menu in enumerate(capture["menus"]):
        request = menu["request"]
        path = " > ".join(menu.get("path", []))
        signature = request_signature(menu)
        response_headers = menu.get("response_header", [])
        response_arguments = response_headers[0].get("arguments", []) if response_headers else []
        response_count = value(response_arguments[1]) if len(response_arguments) > 1 else None
        node_rows.append(
            {
                "index": index,
                "depth": menu.get("depth"),
                "path": path,
                "request_name": request.get("name"),
                "request_kind": request.get("kind_hex"),
                "signature": signature,
                "arguments_json": json.dumps(request.get("arguments", []), ensure_ascii=False),
                "available_rows": response_count,
                "captured_rows": menu.get("captured_rows"),
                "pages": len(menu.get("pages", [])),
            }
        )

        signature_key = (request["kind"], request.get("name", ""), signature)
        entry = signatures.setdefault(
            signature_key,
            {
                "request_kind": request["kind_hex"],
                "request_name": request.get("name", ""),
                "signature": signature,
                "menu_count": 0,
                "available_rows": 0,
                "captured_rows": 0,
                "example_path": path,
                "example_arguments": json.dumps(request.get("arguments", []), ensure_ascii=False),
            },
        )
        entry["menu_count"] += 1
        entry["available_rows"] += response_count or 0
        entry["captured_rows"] += menu.get("captured_rows", 0)

        for row in menu.get("rows", []):
            item_type = row_field(row, 6)
            if not isinstance(item_type, int):
                continue
            type_entry = item_types[item_type]
            type_entry["rows"] += 1
            type_entry["menus"].add(path)
            label = clean_label(row_field(row, 3))
            if label:
                type_entry["labels"][label] += 1

    with (args.output / "menu-nodes.csv").open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=node_rows[0].keys())
        writer.writeheader()
        writer.writerows(node_rows)

    signature_rows = sorted(signatures.values(), key=lambda row: (row["request_kind"], row["signature"]))
    with (args.output / "request-signatures.csv").open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=signature_rows[0].keys())
        writer.writeheader()
        writer.writerows(signature_rows)

    type_rows = []
    for item_type, details in sorted(item_types.items()):
        type_rows.append(
            {
                "item_type": f"0x{item_type:04x}",
                "rows": details["rows"],
                "menu_count": len(details["menus"]),
                "example_labels": " | ".join(label for label, _ in details["labels"].most_common(8)),
                "example_path": sorted(details["menus"])[0],
            }
        )
    with (args.output / "item-types.csv").open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=type_rows[0].keys())
        writer.writeheader()
        writer.writerows(type_rows)

    summary = {
        "source": str(args.capture),
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "context": capture.get("context"),
        "database_port": capture.get("database_port"),
        "device": capture.get("device"),
        "host": capture.get("host"),
        "limits": capture.get("limits"),
        "menu_limit_reached": capture.get("menu_limit_reached"),
        "menu_nodes": len(node_rows),
        "request_signatures": len(signature_rows),
        "item_types": len(type_rows),
        "unsupported_root_items": capture.get("unsupported_root_items", []),
    }
    (args.output / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
