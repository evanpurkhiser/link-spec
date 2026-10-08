#!/usr/bin/env python3
"""Extract direct XDJ-RR remote-database call sites from decompiled firmware."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SOURCE_ROOT = (
    ROOT.parent
    / "alphatheta-docs/devices/xdj-rr/application/assets/decompiled"
)
VOCABULARY = ROOT / "data/static-analysis/link-export-request-vocabulary.json"
OUTPUT = ROOT / "data/static-analysis/xdj-rr-client-navigation.json"
ALPHATHETA_COMMIT = "a70aeefb202ffddd2900e7b40e339a47ac077057"

FUNCTION_MARKER = re.compile(
    r"/\* -+\n \* (0x[0-9a-f]+)\s+([A-Za-z0-9_.]+)\n \* -+ \*/",
    re.IGNORECASE,
)
DBCL_NAME = re.compile(r"\b(dbcl_[A-Za-z0-9_]+)\s*\(")
COMMAND_CONSTRUCTORS = {
    "SetHeader": (2, 3),
    "dbcl_GetRoot": (1, 2),
    "dbcl_GetULong": (1, 2),
    "dbcl_GetULong2": (1, 2),
    "dbcl_GetULong3": (1, 2),
}
COMMAND_CONSTANT = re.compile(r"^(?:0x|&DAT_0000)([0-9a-fA-F]{4})$")
LITERAL = re.compile(r"^(?:0x[0-9a-fA-F]+|[0-9]+)$")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def source_files() -> list[Path]:
    files = []
    for path in sorted(SOURCE_ROOT.rglob("*.c")):
        if "dbcl_" in path.read_text(errors="replace"):
            files.append(path)
    if not files:
        raise ValueError("no XDJ-RR decompiled sources contain dbcl_ symbols")
    return files


def functions(path: Path, text: str) -> list[dict[str, object]]:
    markers = list(FUNCTION_MARKER.finditer(text))
    result = []
    for index, marker in enumerate(markers):
        end = markers[index + 1].start() if index + 1 < len(markers) else len(text)
        result.append(
            {
                "address": marker.group(1).lower(),
                "name": marker.group(2),
                "body": text[marker.end() : end],
                "body_offset": marker.end(),
                "path": path,
                "text": text,
            }
        )
    return result


def request_kinds() -> set[str]:
    document = json.loads(VOCABULARY.read_text())
    return {
        command["kind"]
        for command in document["commands"]
        if command["direction"] in {"request", "probe"}
    }


def calls_named(text: str, name: str) -> list[list[str]]:
    calls = []
    pattern = re.compile(rf"\b{re.escape(name)}\s*\(")
    for match in pattern.finditer(text):
        arguments, _ = split_arguments(text, match.end() - 1)
        calls.append(arguments)
    return calls


def wrapper_kinds(blocks: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    known_requests = request_kinds()
    wrappers = {}
    ambiguous = {}
    for block in blocks:
        name = str(block["name"])
        if not name.startswith("dbcl_"):
            continue
        candidates = []
        for constructor, (kind_index, location_index) in COMMAND_CONSTRUCTORS.items():
            for arguments in calls_named(str(block["body"]), constructor):
                if len(arguments) <= max(kind_index, location_index):
                    continue
                match = COMMAND_CONSTANT.fullmatch(arguments[kind_index])
                if match is None:
                    continue
                kind = match.group(1).upper()
                if kind in known_requests:
                    candidates.append((kind, arguments[location_index]))
        unique = sorted(set(candidates))
        if len(unique) == 1:
            kind, location_expression = unique[0]
            parameter = re.fullmatch(r"param_([0-9]+)", location_expression)
            wrappers[name] = {
                "request_kind": kind,
                "location_expression": location_expression,
                "location_parameter": int(parameter.group(1)) if parameter else None,
                "fixed_location": (
                    int(location_expression, 0)
                    if LITERAL.fullmatch(location_expression)
                    else None
                ),
            }
        elif len(unique) > 1:
            ambiguous[name] = unique

    if ambiguous:
        details = ", ".join(f"{name}={values}" for name, values in ambiguous.items())
        raise ValueError(f"ambiguous dbcl request wrappers: {details}")
    return wrappers


def split_arguments(text: str, open_paren: int) -> tuple[list[str], int]:
    depth = 0
    start = open_paren + 1
    arguments = []
    for index in range(open_paren + 1, len(text)):
        char = text[index]
        if char == "(":
            depth += 1
        elif char == ")":
            if depth == 0:
                arguments.append(text[start:index].strip())
                return arguments, index
            depth -= 1
        elif char == "," and depth == 0:
            arguments.append(text[start:index].strip())
            start = index + 1
    raise ValueError("unterminated dbcl call")


def call_sites(
    blocks: list[dict[str, object]], wrappers: dict[str, dict[str, object]]
) -> list[dict[str, object]]:
    sites = []
    for block in blocks:
        caller = str(block["name"])
        if caller.startswith("dbcl_"):
            continue
        body = str(block["body"])
        for match in DBCL_NAME.finditer(body):
            wrapper = match.group(1)
            if wrapper not in wrappers:
                continue
            arguments, _ = split_arguments(body, match.end() - 1)
            wrapper_data = wrappers[wrapper]
            parameter = wrapper_data["location_parameter"]
            if wrapper_data["fixed_location"] is not None:
                location = str(wrapper_data["location_expression"])
                literal = int(wrapper_data["fixed_location"])
                location_source = "wrapper-fixed"
            elif parameter is not None and len(arguments) >= parameter:
                location = arguments[parameter - 1]
                literal = int(location, 0) if LITERAL.fullmatch(location) else None
                location_source = f"call-argument-{parameter}"
            else:
                location = str(wrapper_data["location_expression"])
                literal = None
                location_source = "wrapper-expression"
            absolute_offset = int(block["body_offset"]) + match.start()
            line = str(block["text"]).count("\n", 0, absolute_offset) + 1
            path = Path(block["path"])
            sites.append(
                {
                    "request_kind": wrapper_data["request_kind"],
                    "wrapper": wrapper,
                    "caller": caller,
                    "caller_address": block["address"],
                    "source": str(path.relative_to(ROOT.parent)),
                    "line": line,
                    "location_argument": location,
                    "location_source": location_source,
                    "literal_location": literal,
                }
            )
    return sorted(
        sites,
        key=lambda site: (
            site["request_kind"],
            site["source"],
            site["line"],
            site["caller"],
        ),
    )


def build_document() -> dict[str, object]:
    files = source_files()
    blocks = []
    sources = []
    for path in files:
        data = path.read_bytes()
        text = data.decode("utf-8", errors="replace")
        blocks.extend(functions(path, text))
        sources.append(
            {
                "path": str(path.relative_to(ROOT.parent)),
                "sha256": sha256(data),
            }
        )

    wrappers = wrapper_kinds(blocks)
    sites = call_sites(blocks, wrappers)
    kind_sites = {}
    for site in sites:
        kind_sites.setdefault(site["request_kind"], []).append(site)

    literal_locations = sorted(
        {
            site["literal_location"]
            for site in sites
            if site["literal_location"] is not None
        }
    )
    return {
        "format": 1,
        "scope": (
            "All direct named calls from non-dbcl functions to request-kind-bearing "
            "dbcl wrappers in the decompiled XDJ-RR application. Each wrapper's "
            "actual SetHeader/dbcl_GetRoot/dbcl_GetULong location expression is "
            "propagated to its callers; expressions are retained verbatim and only "
            "plain integer literals are classified."
        ),
        "limitations": [
            "Indirect calls through function pointers are outside this direct-call inventory.",
            "A client call site proves firmware reachability, not Rekordbox server support.",
            "Dynamic location expressions require caller-state analysis before assigning a value.",
        ],
        "source": {
            "repository": "alphatheta-docs",
            "commit": ALPHATHETA_COMMIT,
            "files": sources,
        },
        "summary": {
            "source_file_count": len(files),
            "request_wrapper_count": len(wrappers),
            "request_kind_count": len(
                {wrapper["request_kind"] for wrapper in wrappers.values()}
            ),
            "direct_call_site_count": len(sites),
            "direct_call_request_kind_count": len(kind_sites),
            "literal_locations": literal_locations,
            "dynamic_location_call_site_count": sum(
                site["literal_location"] is None for site in sites
            ),
        },
        "wrappers": [
            {"name": name, **data}
            for name, data in sorted(
                wrappers.items(),
                key=lambda item: (item[1]["request_kind"], item[0]),
            )
        ],
        "request_kinds": [
            {
                "request_kind": kind,
                "direct_call_site_count": len(kind_sites[kind]),
                "literal_locations": sorted(
                    {
                        site["literal_location"]
                        for site in kind_sites[kind]
                        if site["literal_location"] is not None
                    }
                ),
                "has_dynamic_location": any(
                    site["literal_location"] is None for site in kind_sites[kind]
                ),
            }
            for kind in sorted(kind_sites)
        ],
        "call_sites": sites,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()

    document = build_document()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(document, indent=2) + "\n")


if __name__ == "__main__":
    main()
