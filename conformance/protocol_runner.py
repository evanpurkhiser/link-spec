#!/usr/bin/env python3
"""Record and verify Link Export suites against a remote database server."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
import threading
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from remote_db import (
    ERROR,
    MENU_FOOTER,
    MENU_HEADER,
    MENU_ITEM,
    RENDER,
    Argument,
    Client,
    Message,
    transport_outcome,
)


MAX_AUTOMATIC_RENDER_ROWS = 100_000
MAX_RENDER_MESSAGES = 100_000
MISSING = object()


class ExpectationError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("record", "verify"))
    parser.add_argument("--host", required=True)
    parser.add_argument("--query-port", type=int, default=12523)
    parser.add_argument("--suite", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--golden", type=Path, required=True)
    parser.add_argument("--backend", required=True)
    parser.add_argument("--backend-version", required=True)
    parser.add_argument("--identity", type=Path, required=True)
    parser.add_argument("--expectations", choices=("strict", "compare"), default="strict")
    parser.add_argument("--actual", type=Path)
    parser.add_argument("--diff", type=Path)
    return parser.parse_args()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text())


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=False) + "\n")


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value + "\n")


def validate_suite(suite: Mapping[str, Any], source: Path | None = None) -> None:
    required = ("name", "fixture_profile", "fixture_version", "defaults", "cases")
    missing = [field for field in required if field not in suite]
    if missing:
        location = f" in {source}" if source else ""
        raise ValueError(f"suite{location} is missing {', '.join(missing)}")
    if not suite["cases"]:
        raise ValueError(f"suite {source or suite['name']} has no cases")
    defaults = suite["defaults"]
    for field in (
        "device",
        "context",
        "sort",
        "root_capabilities",
        "setup",
        "page_size",
        "render_arguments",
    ):
        if field not in defaults:
            raise ValueError(f"suite {source or suite['name']} has no defaults.{field}")
    for case in suite["cases"]:
        for field in ("id", "description", "request_kind", "arguments", "expect"):
            if field not in case:
                raise ValueError(
                    f"suite {source or suite['name']} case is missing {field}"
                )


def validate_fixture(suite: Mapping[str, Any], manifest: Mapping[str, Any]) -> None:
    if (
        suite["fixture_profile"] != manifest["profile"]
        or suite["fixture_version"] != manifest["fixture_version"]
    ):
        raise ValueError(
            f"suite needs fixture {suite['fixture_profile']} v{suite['fixture_version']}, "
            f"manifest is {manifest['profile']} v{manifest['fixture_version']}"
        )
    expected = suite.get("fixture_variant")
    actual = (manifest.get("settings") or {}).get("name")
    if expected is not None and actual != expected:
        raise ValueError(
            f"suite needs fixture variant {expected!r}, manifest has {actual!r}"
        )


def resolve_number(
    value: int | str,
    defaults: Mapping[str, Any],
    manifest: Mapping[str, Any],
    total: int | None = None,
) -> int:
    if isinstance(value, int):
        return value & 0xFFFFFFFF
    if value == "$context":
        return resolve_number(defaults["context"], defaults, manifest, total)
    if value == "$sort":
        return resolve_number(defaults["sort"], defaults, manifest, total)
    if value == "$root_capabilities":
        return resolve_number(defaults["root_capabilities"], defaults, manifest, total)
    if value == "$total":
        if total is None:
            raise ValueError("$total used before menu header")
        return total
    if value.startswith("$fixture."):
        symbol = value.removeprefix("$fixture.")
        try:
            return int(manifest["ids"][symbol])
        except KeyError as error:
            raise ValueError(f"unknown fixture symbol {value}") from error
    return int(value, 16 if value.startswith("0x") else 10)


def resolve_argument(
    spec: Mapping[str, Any],
    defaults: Mapping[str, Any],
    manifest: Mapping[str, Any],
    prior: Mapping[str, Mapping[str, Any]],
    total: int | None = None,
) -> Argument:
    if "number" in spec:
        return Argument.number(
            resolve_number(spec["number"], defaults, manifest, total)
        )
    if "string" in spec:
        return Argument.string(spec["string"])
    if "utf16_bytes" in spec:
        encoded = spec["utf16_bytes"].encode("utf-16-be", "surrogatepass")
        return Argument.number(len(encoded) + 2)
    if "blob_hex" in spec:
        return Argument.blob(bytes.fromhex(spec["blob_hex"]))
    if "case_item" in spec:
        reference = spec["case_item"]
        row = reference.get("row", 0)
        argument = reference.get("argument", 1)
        try:
            value = prior[reference["case"]]["rows"][row]["arguments"][argument][
                "value"
            ]
        except (KeyError, IndexError, TypeError) as error:
            raise ValueError(
                f"case item {reference['case']} row {row} argument {argument} "
                "is unavailable"
            ) from error
        return Argument.number(int(value))
    raise ValueError(f"unknown argument specification {spec!r}")


def expectation_failure(strict: bool, message: str) -> None:
    if strict:
        raise ExpectationError(message)
    print(f"expectation mismatch: {message}", file=sys.stderr)


def base_result(case: Mapping[str, Any], **values: object) -> dict[str, object]:
    return {
        "id": case["id"],
        "description": case["description"],
        **values,
    }


def connection_failure_result(
    case: Mapping[str, Any], error: BaseException, strict: bool
) -> dict[str, object]:
    transport = transport_outcome(error)
    if transport is None:
        raise error
    kind, detail = transport
    outcome = f"connection_{kind}"
    expected = case["expect"]["outcome"]
    if expected not in ("any", outcome):
        expectation_failure(strict, f"{case['id']}: expected {expected}, got {outcome}")
    return base_result(
        case,
        request=None,
        outcome=outcome,
        transport_error_kind=detail,
        total=None,
        header=[],
        pages=[],
        rows=[],
    )


def receive_render(client: Client, arguments: list[Argument]) -> list[Message]:
    pending = client.request(RENDER, arguments)
    output: list[Message] = []
    while True:
        complete = any(message.kind in (MENU_FOOTER, ERROR) for message in pending)
        output.extend(pending)
        if len(output) > MAX_RENDER_MESSAGES:
            raise RuntimeError("render response exceeded message limit without a footer")
        if complete:
            return output
        pending = client.receive()


def render_requests(
    case: Mapping[str, Any], defaults: Mapping[str, Any], manifest: Mapping[str, Any], total: int
) -> list[tuple[int, int]]:
    if "render_pages" in case:
        return [
            (
                resolve_number(page["offset"], defaults, manifest, total),
                resolve_number(page["count"], defaults, manifest, total),
            )
            for page in case["render_pages"]
        ]
    if total > MAX_AUTOMATIC_RENDER_ROWS:
        raise RuntimeError(
            f"{case['id']} returned {total} rows; declare bounded render_pages above "
            f"{MAX_AUTOMATIC_RENDER_ROWS}"
        )
    page_size = case.get("page_size", defaults["page_size"])
    if page_size == 0:
        raise ValueError(f"{case['id']} has automatic page size 0")
    return [
        (offset, min(page_size, total - offset))
        for offset in range(0, total, page_size)
    ]


def numeric_row_arguments(
    case: Mapping[str, Any], rows: Sequence[Mapping[str, Any]], argument_index: int
) -> list[int]:
    output = []
    for row_index, row in enumerate(rows):
        try:
            argument = row["arguments"][argument_index]
            if argument["type"] != "number":
                raise TypeError
            output.append(int(argument["value"]))
        except (KeyError, IndexError, TypeError) as error:
            raise ExpectationError(
                f"{case['id']} row {row_index}: missing numeric argument {argument_index}"
            ) from error
    return output


def assert_item_types(
    case: Mapping[str, Any],
    rows: Sequence[Mapping[str, Any]],
    accepts: Callable[[int], bool],
    expected: str,
) -> None:
    for index, row in enumerate(rows):
        try:
            argument = row["arguments"][6]
            if argument["type"] != "number":
                raise TypeError
            actual = int(argument["value"])
        except (KeyError, IndexError, TypeError) as error:
            raise ExpectationError(
                f"{case['id']} row {index}: missing numeric item type"
            ) from error
        if not accepts(actual):
            raise ExpectationError(
                f"{case['id']} row {index}: expected item type {expected}, got {actual:#06x}"
            )


def assert_expectations(
    case: Mapping[str, Any],
    outcome: str,
    total: int | None,
    rows: Sequence[Mapping[str, Any]],
    manifest: Mapping[str, Any],
    defaults: Mapping[str, Any],
) -> None:
    expected = case["expect"]
    if expected["outcome"] not in ("any", outcome):
        raise ExpectationError(
            f"{case['id']}: expected {expected['outcome']}, got {outcome}"
        )
    if "total" in expected and total != expected["total"]:
        raise ExpectationError(
            f"{case['id']}: expected total {expected['total']}, got {total}"
        )
    if "row_count" in expected and len(rows) != expected["row_count"]:
        raise ExpectationError(
            f"{case['id']}: expected {expected['row_count']} rows, got {len(rows)}"
        )
    if "argument_count" in expected:
        for index, row in enumerate(rows):
            count = len(row.get("arguments", []))
            if count != expected["argument_count"]:
                raise ExpectationError(
                    f"{case['id']} row {index}: expected {expected['argument_count']} "
                    f"arguments, got {count}"
                )
    if "item_ids" in expected:
        wanted = [
            resolve_number(value, defaults, manifest, total)
            for value in expected["item_ids"]
        ]
        actual = [
            int(row["arguments"][1]["value"])
            for row in rows
            if len(row.get("arguments", [])) > 1
            and "value" in row["arguments"][1]
        ]
        if wanted != actual:
            raise ExpectationError(
                f"{case['id']}: expected item IDs {wanted}, got {actual}"
            )
    if "item_type" in expected:
        wanted = resolve_number(expected["item_type"], defaults, manifest, total)
        assert_item_types(case, rows, lambda actual: actual == wanted, f"{wanted:#06x}")
    if "item_type_low_byte" in expected:
        wanted = resolve_number(
            expected["item_type_low_byte"], defaults, manifest, total
        )
        assert_item_types(
            case, rows, lambda actual: actual & 0xFF == wanted, f"low byte {wanted:#04x}"
        )
    if "item_type_high_bytes" in expected:
        wanted = {
            resolve_number(value, defaults, manifest, total)
            for value in expected["item_type_high_bytes"]
        }
        assert_item_types(
            case,
            rows,
            lambda actual: actual >> 8 in wanted,
            f"high byte in {sorted(wanted)!r}",
        )
    for key, values in expected.get("row_argument_values", {}).items():
        index = int(key)
        wanted = [resolve_number(value, defaults, manifest, total) for value in values]
        actual = numeric_row_arguments(case, rows, index)
        if wanted != actual:
            raise ExpectationError(
                f"{case['id']}: expected argument {index} values {wanted}, got {actual}"
            )
    for key, values in expected.get("row_argument_any_of", {}).items():
        index = int(key)
        wanted = {
            resolve_number(value, defaults, manifest, total) for value in values
        }
        for row_index, actual in enumerate(numeric_row_arguments(case, rows, index)):
            if actual not in wanted:
                raise ExpectationError(
                    f"{case['id']} row {row_index}: expected argument {index} in "
                    f"{sorted(wanted)!r}, got {actual:#x}"
                )


def run_case(
    client: Client,
    defaults: Mapping[str, Any],
    manifest: Mapping[str, Any],
    case: Mapping[str, Any],
    prior: Mapping[str, Mapping[str, Any]],
    strict: bool,
) -> dict[str, object]:
    if "raw_hex" in case:
        response = client.raw_probe(bytes.fromhex(case["raw_hex"]), case.get("raw_read_ms", 500))
        outcome = str(response["outcome"])
        expected = case["expect"]["outcome"]
        if expected not in ("any", outcome):
            expectation_failure(strict, f"{case['id']}: expected {expected}, got {outcome}")
        return base_result(
            case,
            request={"raw_hex": case["raw_hex"], "read_ms": case.get("raw_read_ms", 500)},
            outcome=outcome,
            raw_response=response,
            total=None,
            header=[],
            pages=[],
            rows=[],
        )

    request_kind = resolve_number(case["request_kind"], defaults, manifest)
    try:
        arguments = [
            resolve_argument(spec, defaults, manifest, prior)
            for spec in case["arguments"]
        ]
    except ValueError as error:
        if strict:
            raise
        outcome = "dependency_unavailable"
        expectation_failure(
            False,
            f"{case['id']}: expected {case['expect']['outcome']}, got {outcome}: {error}",
        )
        return base_result(
            case,
            request={"kind": request_kind, "arguments": []},
            outcome=outcome,
            resolution_error=str(error),
            total=None,
            header=[],
            pages=[],
            rows=[],
        )

    request_json = [argument.as_json() for argument in arguments]
    if case.get("send_only", False):
        client.transaction = (client.transaction + 1) & 0xFFFFFFFF
        client.send(Message(client.transaction, request_kind, tuple(arguments)))
        expected = case["expect"]["outcome"]
        if expected not in ("any", "sent"):
            expectation_failure(strict, f"{case['id']}: expected {expected}, got sent")
        return base_result(
            case,
            request={"kind": request_kind, "arguments": request_json},
            outcome="sent",
            total=None,
            header=[],
            pages=[],
            rows=[],
        )

    if case.get("direct_response", False):
        response = client.request_raw(
            request_kind,
            arguments,
            defaults.get("read_timeout_ms", 3000),
            case.get("fixed_tag_slots"),
        )
        outcome = str(response["outcome"])
        expected = case["expect"]["outcome"]
        if expected not in ("any", outcome):
            expectation_failure(strict, f"{case['id']}: expected {expected}, got {outcome}")
        return base_result(
            case,
            request={
                "kind": request_kind,
                "arguments": request_json,
                "fixed_tag_slots": case.get("fixed_tag_slots"),
            },
            outcome=outcome,
            raw_response=response,
            total=None,
            header=[],
            pages=[],
            rows=[],
        )

    try:
        header = client.request(request_kind, arguments)
    except Exception as error:
        transport = transport_outcome(error)
        if transport is None:
            raise
        outcome, detail = transport
        expected = case["expect"]["outcome"]
        if expected not in ("any", outcome):
            expectation_failure(strict, f"{case['id']}: expected {expected}, got {outcome}")
        return base_result(
            case,
            request={"kind": request_kind, "arguments": request_json},
            outcome=outcome,
            transport_error_kind=detail,
            total=None,
            header=[],
            pages=[],
            rows=[],
        )

    total = next(
        (
            int(message.arguments[1].value)
            for message in header
            if message.kind == MENU_HEADER
            and len(message.arguments) > 1
            and message.arguments[1].type == "number"
        ),
        None,
    )
    unavailable = total == 0xFFFFFFFF or any(message.kind == ERROR for message in header)
    render = case.get("render", True)
    if render and not unavailable and total is None:
        message = "response has no menu total"
        expectation_failure(strict, f"{case['id']}: {message}")
        return base_result(
            case,
            request={"kind": request_kind, "arguments": request_json},
            outcome="protocol_error",
            protocol_error=message,
            total=total,
            header=[message.as_json() for message in header],
            pages=[],
            rows=[],
        )

    rows: list[dict[str, object]] = []
    pages: list[dict[str, object]] = []
    render_error = False
    render_transport: str | None = None
    if render and not unavailable:
        assert total is not None
        for offset, count in render_requests(case, defaults, manifest, total):
            context = case.get("render_context", defaults["context"])
            render_values = case.get("render_arguments", defaults["render_arguments"])
            render_arguments = [
                Argument.number(resolve_number(context, defaults, manifest, total)),
                Argument.number(offset),
                Argument.number(count),
                *(
                    Argument.number(resolve_number(value, defaults, manifest, total))
                    for value in render_values
                ),
            ]
            rendered_arguments = [argument.as_json() for argument in render_arguments]
            try:
                messages = receive_render(client, render_arguments)
            except Exception as error:
                transport = transport_outcome(error)
                if transport is None:
                    raise
                render_transport, detail = transport
                pages.append(
                    {
                        "offset": offset,
                        "requested": count,
                        "received": 0,
                        "arguments": rendered_arguments,
                        "messages": [],
                        "outcome": render_transport,
                        "transport_error_kind": detail,
                    }
                )
                break
            render_error = any(message.kind == ERROR for message in messages)
            page_rows = [message for message in messages if message.kind == MENU_ITEM]
            rows.extend(message.as_json() for message in page_rows)
            pages.append(
                {
                    "offset": offset,
                    "requested": count,
                    "received": len(page_rows),
                    "arguments": rendered_arguments,
                    "messages": [message.as_json() for message in messages],
                }
            )
            if render_error:
                break

    if render_transport:
        outcome = f"render_{render_transport}"
    elif unavailable:
        outcome = "error"
    elif render_error:
        outcome = "render_error"
    else:
        outcome = "menu"
    try:
        assert_expectations(case, outcome, total, rows, manifest, defaults)
    except ExpectationError as error:
        expectation_failure(strict, str(error))
    return base_result(
        case,
        request={"kind": request_kind, "arguments": request_json},
        outcome=outcome,
        total=total,
        header=[message.as_json() for message in header],
        pages=pages,
        rows=rows,
    )


def replace_typed_numbers(value: object, replacements: Mapping[int, int]) -> None:
    if isinstance(value, list):
        for item in value:
            replace_typed_numbers(item, replacements)
        return
    if not isinstance(value, dict):
        return
    if value.get("type") == "number" and value.get("value") in replacements:
        value["value"] = replacements[value["value"]]
    for item in value.values():
        replace_typed_numbers(item, replacements)


def canonicalize_case_item_selectors(
    suite: Mapping[str, Any], cases: list[dict[str, object]], strict: bool
) -> list[dict[str, object]]:
    references = sorted(
        {
            (
                spec["case_item"]["case"],
                spec["case_item"].get("row", 0),
                spec["case_item"].get("argument", 1),
            )
            for case in suite["cases"]
            for spec in case["arguments"]
            if "case_item" in spec and spec["case_item"].get("canonicalize", False)
        }
    )
    replacements: dict[int, int] = {}
    normalizers = []
    by_id = {case["id"]: case for case in cases}
    for index, (case_id, row, argument) in enumerate(references):
        canonical = 0xCA5E0000 + index
        try:
            actual = int(by_id[case_id]["rows"][row]["arguments"][argument]["value"])
        except (KeyError, IndexError, TypeError) as error:
            if strict:
                raise ValueError(
                    f"case item {case_id} row {row} argument {argument} is unavailable "
                    "for canonicalization"
                ) from error
        else:
            previous = replacements.get(actual)
            if previous is not None and previous != canonical:
                raise ValueError(
                    f"case item references resolve to duplicate value {actual} with "
                    "distinct canonical selectors"
                )
            replacements[actual] = canonical
        normalizers.append(
            {
                "kind": "case_item_selector",
                "source_case": case_id,
                "row": row,
                "argument": argument,
                "canonical_value": canonical,
            }
        )
    for case in cases:
        replace_typed_numbers(case, replacements)
    return normalizers


def canonical_parallel_cases(cases: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    canonical = []
    for case in cases:
        value = copy.deepcopy(case)
        value.pop("id", None)
        value.pop("description", None)
        canonical.append(value)
    canonical.sort(key=lambda value: json.dumps(value, separators=(",", ":"), sort_keys=True))
    for index, case in enumerate(canonical):
        case["id"] = f"parallel-{index:02}"
        case["description"] = "Canonical concurrent outcome"
    return canonical


def parallel_summary(cases: Sequence[Mapping[str, Any]]) -> dict[str, object]:
    outcomes = Counter(case.get("outcome") for case in cases if case.get("outcome"))
    return {"connections": len(cases), "outcomes": dict(sorted(outcomes.items()))}


def connect(args: argparse.Namespace, defaults: Mapping[str, Any], strict: bool) -> Client:
    return Client.connect(
        args.host,
        args.query_port,
        defaults["device"],
        defaults["setup"],
        defaults.get("read_timeout_ms", 3000),
        strict,
    )


def run_cases(
    args: argparse.Namespace,
    suite: Mapping[str, Any],
    manifest: Mapping[str, Any],
    strict: bool,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    defaults = suite["defaults"]
    initial = connect(args, defaults, strict)
    setup_exchange = initial.setup_exchange
    if suite.get("parallel_connections", False):
        initial.close()
        barrier = threading.Barrier(len(suite["cases"]))

        def worker(case: Mapping[str, Any]) -> dict[str, object]:
            barrier.wait()
            time.sleep(case.get("delay_before_connection_ms", 0) / 1000)
            try:
                client = connect(args, defaults, strict)
            except Exception as error:
                return connection_failure_result(case, error, strict)
            try:
                time.sleep(case.get("delay_before_request_ms", 0) / 1000)
                return run_case(client, defaults, manifest, case, {}, strict)
            finally:
                client.close()

        with ThreadPoolExecutor(max_workers=len(suite["cases"])) as executor:
            return list(executor.map(worker, suite["cases"])), setup_exchange

    client = initial
    prior: dict[str, Mapping[str, Any]] = {}
    results = []
    try:
        for case in suite["cases"]:
            time.sleep(case.get("delay_before_connection_ms", 0) / 1000)
            connection_setup = None
            if case.get("fresh_connection", False):
                client.close()
                client = connect(args, defaults, strict)
                if case.get("capture_connection_setup", False):
                    connection_setup = client.setup_exchange
            drain = None
            if case.get("drain_before_request_ms", 0) > 0:
                drain = client.raw_probe(b"", case["drain_before_request_ms"])
            time.sleep(case.get("delay_before_request_ms", 0) / 1000)
            print(f"running case {case['id']}", file=sys.stderr)
            result = run_case(client, defaults, manifest, case, prior, strict)
            if connection_setup is not None:
                result["connection_setup_exchange"] = connection_setup
            if drain is not None:
                result["pre_request_drain"] = drain
            prior[case["id"]] = result
            results.append(result)
    finally:
        client.close()
    return results, setup_exchange


def collect_value_differences(
    expected: object,
    actual: object,
    path: str,
    output: list[str],
    limit: int = 20,
) -> None:
    if expected == actual or len(output) >= limit:
        return
    if isinstance(expected, dict) and isinstance(actual, dict):
        for key in sorted(expected.keys() | actual.keys()):
            collect_value_differences(
                expected.get(key), actual.get(key), f"{path}.{key}", output, limit
            )
        return
    if isinstance(expected, list) and isinstance(actual, list):
        for index in range(max(len(expected), len(actual))):
            collect_value_differences(
                expected[index] if index < len(expected) else None,
                actual[index] if index < len(actual) else None,
                f"{path}[{index}]",
                output,
                limit,
            )
        return
    output.append(
        f"{path}: expected {compact_value(expected)}, actual {compact_value(actual)}"
    )


def compact_value(value: object) -> str:
    rendered = json.dumps(value, separators=(",", ":"), ensure_ascii=False)
    return rendered if len(rendered) <= 160 else rendered[:157] + "..."


def case_differences(
    expected: Mapping[str, Any], actual: Mapping[str, Any]
) -> list[str]:
    report: list[str] = []
    for field in ("format", "suite", "fixture", "setup", "setup_exchange"):
        collect_value_differences(expected.get(field), actual.get(field), field, report)
    expected_cases = expected.get("cases")
    actual_cases = actual.get("cases")
    if not isinstance(expected_cases, list) or not isinstance(actual_cases, list):
        return [*report, "golden/result envelope differs"]
    for index, (expected_case, actual_case) in enumerate(zip(expected_cases, actual_cases)):
        if expected_case == actual_case:
            continue
        case_id = actual_case.get("id", "unknown")
        report.append(f"case {index} ({case_id}) differs")
        details: list[str] = []
        collect_value_differences(
            expected_case, actual_case, f"case[{case_id}]", details
        )
        report.extend(f"  {detail}" for detail in details)
    if len(expected_cases) != len(actual_cases):
        report.append(
            f"case count differs: {len(expected_cases)} expected, {len(actual_cases)} actual"
        )
    return report


def run(args: argparse.Namespace) -> int:
    suite_source = args.suite.read_bytes()
    suite = json.loads(suite_source)
    manifest = read_json(args.manifest)
    identity = read_json(args.identity)
    validate_suite(suite, args.suite)
    validate_fixture(suite, manifest)
    strict = args.expectations == "strict"
    cases, setup_exchange = run_cases(args, suite, manifest, strict)

    raw_parallel = None
    if suite.get("canonicalize_parallel", False):
        raw_parallel = copy.deepcopy(cases)
        cases = canonical_parallel_cases(cases)
        normalizers: list[dict[str, object]] = []
    else:
        normalizers = canonicalize_case_item_selectors(suite, cases, strict)

    fingerprint = manifest.get("fixture_fingerprint") or manifest["database_sha256"]
    behavior: dict[str, object] = {
        "suite": suite["name"],
        "fixture": {
            "profile": manifest["profile"],
            "version": manifest["fixture_version"],
            "fingerprint": fingerprint,
        },
        "setup": suite["defaults"]["setup"],
        "setup_exchange": setup_exchange,
        "cases": cases,
    }
    if raw_parallel is not None:
        behavior["parallel_summary"] = parallel_summary(raw_parallel)
    if normalizers:
        behavior["normalizers"] = normalizers
    result: dict[str, object] = {
        "format": 2,
        "provenance": {
            "backend": args.backend,
            "backend_version": args.backend_version,
            "recorded_unix_seconds": int(time.time()),
            "suite_path": str(args.suite),
            "suite_sha256": hashlib.sha256(suite_source).hexdigest(),
            "manifest_path": str(args.manifest),
            "fixture_fingerprint": fingerprint,
            "fixture_database_sha256": manifest["database_sha256"],
            "identity_path": str(args.identity),
            "identity": identity,
        },
        "behavior": behavior,
    }
    if raw_parallel is not None:
        result["observations"] = {"parallel_cases": raw_parallel}

    if args.mode == "record":
        write_json(args.golden, result)
        print(f"recorded {len(suite['cases'])} cases to {args.golden}")
        return 0

    expected = read_json(args.golden)
    expected_behavior = expected.get("behavior")
    if expected_behavior == behavior:
        if args.actual:
            write_json(args.actual, result)
        if args.diff:
            write_text(args.diff, "")
        print(f"verified {len(suite['cases'])} cases against {args.golden}")
        return 0

    actual_path = args.actual or args.golden.with_suffix(".actual.json")
    write_json(actual_path, result)
    differences = case_differences(expected_behavior or {}, behavior)
    print("\n".join(differences), file=sys.stderr)
    if args.diff:
        write_text(args.diff, "\n".join(differences))
    print(
        f"conformance mismatch; actual response written to {actual_path}",
        file=sys.stderr,
    )
    return 1


def main() -> None:
    try:
        raise SystemExit(run(parse_args()))
    except (ExpectationError, OSError, RuntimeError, ValueError) as error:
        print(error, file=sys.stderr)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
