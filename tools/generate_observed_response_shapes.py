#!/usr/bin/env python3
"""Index response shapes observed in canonical real-Rekordbox goldens."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
GOLDENS = ROOT / "conformance/goldens/rekordbox-7.2.19"
SUITES = ROOT / "conformance/suites"
NAVIGATION = ROOT / "data/static-analysis/link-export-navigation-graph.json"
JSON_OUTPUT = ROOT / "data/observed-response-shapes.json"
MARKDOWN_OUTPUT = ROOT / "OBSERVED_RESPONSE_SHAPES.md"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hex_kind(value: int) -> str:
    return f"0x{value:04X}"


def signature(message: dict) -> tuple[int, tuple[str, ...]]:
    return (
        message["kind"],
        tuple(argument["type"] for argument in message.get("arguments", [])),
    )


def signature_record(
    key: tuple[int, tuple[str, ...]], count: int
) -> dict[str, object]:
    kind, argument_types = key
    return {
        "kind": hex_kind(kind),
        "argument_count": len(argument_types),
        "argument_types": list(argument_types),
        "message_count": count,
    }


def corpus_snapshot() -> list[tuple[Path, bytes]]:
    paths = [
        path
        for path in GOLDENS.rglob("*.json")
        if not path.name.endswith(".actual.json")
        and "attempts" not in path.parts
        and "failed-attempts" not in path.parts
    ]
    return [(path, path.read_bytes()) for path in sorted(paths)]


def corpus_hash(snapshot: list[tuple[Path, bytes]]) -> str:
    digest = hashlib.sha256()
    for path, data in snapshot:
        digest.update(path.relative_to(ROOT).as_posix().encode())
        digest.update(b"\0")
        digest.update(data)
    return digest.hexdigest()


def suite_snapshot() -> list[tuple[Path, bytes]]:
    return [(path, path.read_bytes()) for path in sorted(SUITES.rglob("*.json"))]


def collect_suite_declarations(
    snapshot: list[tuple[Path, bytes]],
) -> dict[int, dict[str, object]]:
    declarations: dict[int, dict[str, object]] = {}
    for path, data in snapshot:
        document = json.loads(data)
        relative = path.relative_to(ROOT).as_posix()
        for case in document.get("cases", []):
            value = case["request_kind"]
            kind = int(value, 16) if isinstance(value, str) else int(value)
            entry = declarations.setdefault(kind, {"case_count": 0, "suite_files": set()})
            entry["case_count"] += 1
            entry["suite_files"].add(relative)

    return declarations


def collect(
    snapshot: list[tuple[Path, bytes]],
    declaration_snapshot: list[tuple[Path, bytes]],
) -> dict[str, object]:
    requests: dict[int, dict[str, object]] = {}
    identity_profiles: dict[str, dict[str, object]] = {}
    setup = {
        "observation_count": 0,
        "origins": Counter(),
        "request_kinds": Counter(),
        "request_signatures": Counter(),
        "reply_signatures": Counter(),
        "evidence_files": set(),
        "identity_profile_ids": set(),
        "setup_modes": set(),
    }
    drains = {
        "observation_count": 0,
        "outcomes": Counter(),
        "message_signatures": Counter(),
        "nonempty_raw_count": 0,
        "evidence_files": set(),
        "identity_profile_ids": set(),
        "setup_modes": set(),
    }
    render = {
        "page_count": 0,
        "source_request_kinds": Counter(),
        "request_signatures": Counter(),
        "outcomes": Counter(),
        "reply_signatures": Counter(),
        "row_item_types": Counter(),
        "evidence_files": set(),
        "identity_profile_ids": set(),
        "setup_modes": set(),
    }
    case_count = 0

    for path, data in snapshot:
        document = json.loads(data)
        relative = path.relative_to(ROOT).as_posix()
        identity = document["provenance"]["identity"]
        profile = {
            "model": identity["model"],
            "player": identity["player"],
            "device_type": identity["device_type"],
            "generation": identity["generation"],
            "presence": identity["presence"],
            "model_code": identity["model_code"],
            "keepalive_packet_sha256": identity["packet_sha256"],
            "status_backed": "status_packet_sha256" in identity,
            "status_packet_sha256": identity.get("status_packet_sha256"),
            "status_template": identity.get("status_template"),
        }
        profile_payload = json.dumps(
            profile, sort_keys=True, separators=(",", ":")
        ).encode()
        profile_id = f"identity-{sha256(profile_payload)[:12]}"
        identity_profiles.setdefault(profile_id, {"id": profile_id, **profile})
        setup_mode = document["behavior"].get("setup")

        setup_exchanges = []
        document_setup = document["behavior"].get("setup_exchange")
        if isinstance(document_setup, dict):
            setup_exchanges.append(("golden-setup", document_setup))

        for case in document["behavior"].get("cases", []):
            connection_setup = case.get("connection_setup_exchange")
            if isinstance(connection_setup, dict):
                setup_exchanges.append(("case-connection-setup", connection_setup))

            drain = case.get("pre_request_drain")
            if isinstance(drain, dict):
                drains["observation_count"] += 1
                drains["outcomes"][drain["outcome"]] += 1
                drains["evidence_files"].add(relative)
                drains["identity_profile_ids"].add(profile_id)
                if setup_mode:
                    drains["setup_modes"].add(setup_mode)
                if drain.get("raw_hex"):
                    drains["nonempty_raw_count"] += 1
                for message in drain.get("messages", []):
                    drains["message_signatures"][signature(message)] += 1

        for origin, exchange in setup_exchanges:
            setup_request = exchange["request"]
            setup["observation_count"] += 1
            setup["origins"][origin] += 1
            setup["request_kinds"][setup_request["kind"]] += 1
            setup["request_signatures"][
                tuple(argument["type"] for argument in setup_request.get("arguments", []))
            ] += 1
            setup["evidence_files"].add(relative)
            setup["identity_profile_ids"].add(profile_id)
            if setup_mode:
                setup["setup_modes"].add(setup_mode)
            for message in exchange.get("response", []):
                setup["reply_signatures"][signature(message)] += 1

        for case in document["behavior"].get("cases", []):
            request = case.get("request")
            if not isinstance(request, dict) or "kind" not in request:
                continue

            case_count += 1
            request_kind = request["kind"]
            entry = requests.setdefault(
                request_kind,
                {
                    "case_count": 0,
                    "outcomes": Counter(),
                    "request_signatures": Counter(),
                    "immediate_reply_signatures": Counter(),
                    "evidence_files": set(),
                    "render_page_count": 0,
                    "render_outcomes": Counter(),
                    "render_reply_signatures": Counter(),
                    "render_row_item_types": Counter(),
                    "identity_profile_ids": set(),
                    "setup_modes": set(),
                },
            )
            entry["case_count"] += 1
            entry["outcomes"][case["outcome"]] += 1
            entry["request_signatures"][
                tuple(argument["type"] for argument in request.get("arguments", []))
            ] += 1
            entry["evidence_files"].add(relative)
            entry["identity_profile_ids"].add(profile_id)
            if setup_mode:
                entry["setup_modes"].add(setup_mode)

            immediate_messages = list(case.get("header", []))
            raw_response = case.get("raw_response")
            if isinstance(raw_response, dict):
                immediate_messages.extend(raw_response.get("messages", []))
            for message in immediate_messages:
                entry["immediate_reply_signatures"][signature(message)] += 1

            for page in case.get("pages", []):
                page_outcome = page.get("outcome", "reply")
                page_signature = tuple(
                    argument["type"] for argument in page.get("arguments", [])
                )
                entry["render_page_count"] += 1
                entry["render_outcomes"][page_outcome] += 1
                render["page_count"] += 1
                render["source_request_kinds"][request_kind] += 1
                render["request_signatures"][page_signature] += 1
                render["outcomes"][page_outcome] += 1
                render["evidence_files"].add(relative)
                render["identity_profile_ids"].add(profile_id)
                if setup_mode:
                    render["setup_modes"].add(setup_mode)

                for message in page.get("messages", []):
                    reply_signature = signature(message)
                    entry["render_reply_signatures"][reply_signature] += 1
                    render["reply_signatures"][reply_signature] += 1
                    if message["kind"] == 0x4101 and len(message["arguments"]) > 6:
                        item_type = message["arguments"][6]["value"]
                        entry["render_row_item_types"][item_type] += 1
                        render["row_item_types"][item_type] += 1

    request_records = []
    for kind, entry in sorted(requests.items()):
        request_records.append(
            {
                "kind": hex_kind(kind),
                "case_count": entry["case_count"],
                "outcomes": dict(sorted(entry["outcomes"].items())),
                "request_signatures": [
                    {
                        "argument_count": len(types),
                        "argument_types": list(types),
                        "case_count": count,
                    }
                    for types, count in sorted(
                        entry["request_signatures"].items(),
                        key=lambda item: (len(item[0]), item[0]),
                    )
                ],
                "immediate_reply_signatures": [
                    signature_record(key, count)
                    for key, count in sorted(entry["immediate_reply_signatures"].items())
                ],
                "render": {
                    "page_count": entry["render_page_count"],
                    "outcomes": dict(sorted(entry["render_outcomes"].items())),
                    "reply_signatures": [
                        signature_record(key, count)
                        for key, count in sorted(entry["render_reply_signatures"].items())
                    ],
                    "row_item_types": [
                        {"value": value, "hex": hex_kind(value), "row_count": count}
                        for value, count in sorted(entry["render_row_item_types"].items())
                    ],
                },
                "device_coverage": {
                    "identity_profile_ids": sorted(entry["identity_profile_ids"]),
                    "setup_modes": sorted(entry["setup_modes"]),
                },
                "evidence_files": sorted(entry["evidence_files"]),
            }
        )

    render_record = {
        "kind": "0x3000",
        "page_count": render["page_count"],
        "source_request_kinds": [
            {"kind": hex_kind(kind), "page_count": count}
            for kind, count in sorted(render["source_request_kinds"].items())
        ],
        "request_signatures": [
            {
                "argument_count": len(types),
                "argument_types": list(types),
                "page_count": count,
            }
            for types, count in sorted(
                render["request_signatures"].items(),
                key=lambda item: (len(item[0]), item[0]),
            )
        ],
        "outcomes": dict(sorted(render["outcomes"].items())),
        "reply_signatures": [
            signature_record(key, count)
            for key, count in sorted(render["reply_signatures"].items())
        ],
        "row_item_types": [
            {"value": value, "hex": hex_kind(value), "row_count": count}
            for value, count in sorted(render["row_item_types"].items())
        ],
        "device_coverage": {
            "identity_profile_ids": sorted(render["identity_profile_ids"]),
            "setup_modes": sorted(render["setup_modes"]),
        },
        "evidence_files": sorted(render["evidence_files"]),
    }

    setup_record = {
        "observation_count": setup["observation_count"],
        "origins": dict(sorted(setup["origins"].items())),
        "request_kinds": [
            {"kind": hex_kind(kind), "observation_count": count}
            for kind, count in sorted(setup["request_kinds"].items())
        ],
        "request_signatures": [
            {
                "argument_count": len(types),
                "argument_types": list(types),
                "observation_count": count,
            }
            for types, count in sorted(
                setup["request_signatures"].items(),
                key=lambda item: (len(item[0]), item[0]),
            )
        ],
        "reply_signatures": [
            signature_record(key, count)
            for key, count in sorted(setup["reply_signatures"].items())
        ],
        "device_coverage": {
            "identity_profile_ids": sorted(setup["identity_profile_ids"]),
            "setup_modes": sorted(setup["setup_modes"]),
        },
        "evidence_files": sorted(setup["evidence_files"]),
    }

    drain_record = {
        "observation_count": drains["observation_count"],
        "outcomes": dict(sorted(drains["outcomes"].items())),
        "nonempty_raw_count": drains["nonempty_raw_count"],
        "message_signatures": [
            signature_record(key, count)
            for key, count in sorted(drains["message_signatures"].items())
        ],
        "device_coverage": {
            "identity_profile_ids": sorted(drains["identity_profile_ids"]),
            "setup_modes": sorted(drains["setup_modes"]),
        },
        "evidence_files": sorted(drains["evidence_files"]),
        "attribution": "asynchronous; not assigned to the following request",
    }

    navigation_data = NAVIGATION.read_bytes()
    navigation = json.loads(navigation_data)
    classified_kinds = {
        int(request["kind"], 16)
        for family in navigation["families"]
        for request in family["requests"]
    }
    observed_kinds = set(requests) | set(setup["request_kinds"])
    declarations = collect_suite_declarations(declaration_snapshot)
    missing_kinds = sorted(classified_kinds - observed_kinds)

    return {
        "format": 1,
        "scope": "Canonical Rekordbox 7.2.19 response shapes observed by the conformance lab.",
        "golden_corpus": {
            "path": "conformance/goldens/rekordbox-7.2.19",
            "selection": (
                "final .json files excluding .actual.json and files beneath "
                "attempts or failed-attempts directories"
            ),
            "hash_algorithm": "sha256(relative_path + NUL + file_bytes, sorted by path)",
            "sha256": corpus_hash(snapshot),
            "file_count": len(snapshot),
            "case_count": case_count,
        },
        "suite_declaration_corpus": {
            "path": "conformance/suites",
            "selection": "all final .json suite declarations",
            "hash_algorithm": "sha256(relative_path + NUL + file_bytes, sorted by path)",
            "sha256": corpus_hash(declaration_snapshot),
            "file_count": len(declaration_snapshot),
        },
        "attribution_rule": (
            "header and raw_response messages belong to the declared request; "
            "page messages belong to the separate implicit 0x3000 render request"
        ),
        "identity_profiles": [
            identity_profiles[profile_id] for profile_id in sorted(identity_profiles)
        ],
        "classified_request_coverage": {
            "source": NAVIGATION.relative_to(ROOT).as_posix(),
            "source_sha256": sha256(navigation_data),
            "classified_request_kind_count": len(classified_kinds),
            "observed_request_kind_count": len(observed_kinds),
            "classified_without_canonical_response": [
                hex_kind(kind) for kind in missing_kinds
            ],
            "classified_without_canonical_response_details": [
                {
                    "kind": hex_kind(kind),
                    "declared_case_count": declarations.get(kind, {}).get(
                        "case_count", 0
                    ),
                    "suite_files": sorted(
                        declarations.get(kind, {}).get("suite_files", set())
                    ),
                }
                for kind in missing_kinds
            ],
            "observed_outside_classification": [
                hex_kind(kind) for kind in sorted(observed_kinds - classified_kinds)
            ],
        },
        "requests": request_records,
        "setup_exchange": setup_record,
        "asynchronous_pre_request_drains": drain_record,
        "render_request": render_record,
        "summary": {
            "case_request_kind_count": len(request_records),
            "observed_request_kind_count": len(observed_kinds),
            "request_kinds_with_immediate_replies": sum(
                bool(record["immediate_reply_signatures"]) for record in request_records
            ),
            "request_kinds_with_rendered_pages": sum(
                record["render"]["page_count"] > 0 for record in request_records
            ),
            "immediate_reply_kind_count": len(
                {
                    signature["kind"]
                    for record in request_records
                    for signature in record["immediate_reply_signatures"]
                }
            ),
            "render_reply_kind_count": len(
                {signature["kind"] for signature in render_record["reply_signatures"]}
            ),
            "render_row_item_type_count": len(render_record["row_item_types"]),
            "identity_profile_count": len(identity_profiles),
        },
    }


def compact_outcomes(outcomes: dict[str, int]) -> str:
    return ", ".join(f"{name} {count}" for name, count in outcomes.items()) or "none"


def compact_replies(signatures: list[dict[str, object]]) -> str:
    grouped: dict[str, set[int]] = defaultdict(set)
    for signature in signatures:
        grouped[signature["kind"]].add(signature["argument_count"])
    if not grouped:
        return "none"
    return "; ".join(
        f"`{kind}` ({'/'.join(str(value) for value in sorted(counts))} args)"
        for kind, counts in sorted(grouped.items())
    )


def device_coverage_summary(
    coverage: dict[str, object], profiles: dict[str, dict[str, object]]
) -> dict[str, object]:
    selected = [profiles[profile_id] for profile_id in coverage["identity_profile_ids"]]
    status_count = sum(bool(profile["status_backed"]) for profile in selected)

    return {
        "profile_count": len(selected),
        "model_count": len({profile["model"] for profile in selected}),
        "status_boundary": f"{status_count}/{len(selected)} status-backed",
        "setup_modes": "/".join(coverage["setup_modes"]) or "none",
    }


def render_markdown(document: dict[str, object]) -> str:
    corpus = document["golden_corpus"]
    coverage = document["classified_request_coverage"]
    summary = document["summary"]
    profiles = {
        profile["id"]: profile for profile in document["identity_profiles"]
    }
    setup_device = device_coverage_summary(
        document["setup_exchange"]["device_coverage"], profiles
    )
    drain_device = device_coverage_summary(
        document["asynchronous_pre_request_drains"]["device_coverage"], profiles
    )
    lines = [
        "# Observed Link Export response shapes",
        "",
        "This chapter is the inverse of `REQUEST_SHAPES.md`: it indexes what",
        "canonical Rekordbox 7.2.19 goldens actually returned for every observed",
        "request kind. It is generated from complete typed messages, not inferred",
        "from another backend or from request declarations.",
        "",
        "The initial request and the later page request are separate protocol",
        "transactions. `header` and `raw_response` messages are attributed to the",
        "declared request. Messages inside `pages` are attributed to `0x3000`.",
        "Pre-request drain messages are asynchronous lifecycle evidence and are not",
        "assigned to the following request.",
        "",
        "The machine-readable authority is `data/observed-response-shapes.json`.",
        f"It covers {corpus['file_count']} canonical golden files, "
        f"{corpus['case_count']} cases, and {summary['observed_request_kind_count']} "
        "observed protocol request kinds across setup and ordinary cases. It is bound to corpus SHA-256",
        f"`{corpus['sha256']}`.",
        "",
        "The ledger also defines "
        f"{summary['identity_profile_count']} exact identity profiles. Each request",
        "links to the keepalive/status packet identity and setup widths under which",
        "its response was observed. Profiles retain model, player, class, generation,",
        "presence, model code, packet hashes, and status provenance; model text alone",
        "is never treated as proof of status-backed behavior.",
        "",
        "## Identity profiles",
        "",
        "Each row is an exact observed protocol identity, not a product-name alias.",
        "Two rows with the same model remain distinct when player number, class,",
        "generation, presence, model code, keepalive packet, or status packet differs.",
        "The full packet hashes and status-template provenance are retained in the",
        "machine ledger.",
        "",
        "| Profile | Model | Player | Class | Generation | Presence | Model code | Status-backed |",
        "| --- | --- | ---: | --- | ---: | ---: | ---: | --- |",
    ]
    for profile in document["identity_profiles"]:
        lines.append(
            "| {profile_id} | {model} | {player} | {device_type} | {generation} | {presence} | {model_code} | {status} |".format(
                profile_id=f"`{profile['id']}`",
                model=profile["model"],
                player=profile["player"],
                device_type=profile["device_type"],
                generation=profile["generation"],
                presence=profile["presence"],
                model_code=profile["model_code"],
                status="yes" if profile["status_backed"] else "no",
            )
        )

    lines.extend(
        [
        "",
        "## Classified coverage",
        "",
        f"The navigation graph classifies {coverage['classified_request_kind_count']} request kinds; "
        f"{coverage['observed_request_kind_count']} currently have canonical response evidence.",
        "The following classified kinds have no canonical response recording:",
        "",
        "| Request | Declared cases | Suite files |",
        "| ---: | ---: | ---: |",
        ]
    )
    for gap in coverage["classified_without_canonical_response_details"]:
        lines.append(
            f"| `{gap['kind']}` | {gap['declared_case_count']} | {len(gap['suite_files'])} |"
        )

    lines.extend(
        [
        "",
        "This is an evidence boundary, not an unsupported-command claim. These",
        "kinds have declarations but remain queued authority work. Exact suite paths",
        "are retained in the machine ledger, which is bound to declaration corpus",
        f"SHA-256 `{document['suite_declaration_corpus']['sha256']}`. The",
        "generator also requires that no observed kind fall outside the classified",
        "namespace.",
        "",
        "## Setup exchange",
        "",
        f"The corpus contains {document['setup_exchange']['observation_count']} typed setup exchanges "
        "from golden-level session setup and lifecycle cases that open independent",
        "connections. Setup is indexed separately because it precedes ordinary",
        "request dispatch. Exact request and reply signatures and every source file",
        "are retained in the machine ledger.",
        "Setup coverage spans "
        f"{setup_device['profile_count']} exact identity "
        f"{'profile' if setup_device['profile_count'] == 1 else 'profiles'}, "
        f"{setup_device['model_count']} model "
        f"{'string' if setup_device['model_count'] == 1 else 'strings'}, "
        f"{setup_device['status_boundary']} identities, and "
        f"{setup_device['setup_modes']} setup widths.",
        "",
        "## Asynchronous drains",
        "",
        f"The corpus contains {document['asynchronous_pre_request_drains']['observation_count']} "
        "pre-request drain observations. "
        f"{document['asynchronous_pre_request_drains']['nonempty_raw_count']} retained bytes before "
        "the declared request was sent. Their outcomes, exact message signatures,",
        "and source files are indexed separately in the machine ledger. These frames",
        "belong to prior asynchronous work and are never counted as the following",
        "request's immediate reply.",
        "Drain provenance spans "
        f"{drain_device['profile_count']} exact identity "
        f"{'profile' if drain_device['profile_count'] == 1 else 'profiles'}, "
        f"{drain_device['model_count']} model "
        f"{'string' if drain_device['model_count'] == 1 else 'strings'}, "
        f"{drain_device['status_boundary']} identities, and "
        f"{drain_device['setup_modes']} setup widths.",
        "",
        "## Request index",
        "",
        "Reply argument counts below are part of the signature. Exact ordered type",
        "vectors, occurrence counts, render outcomes, item types, and every source",
        "golden are retained in the JSON ledger.",
        "",
        "The identity columns count exact profiles and distinct model strings. Status",
        "coverage reports `status-backed/total` for those profiles. Setup lists every observed",
        "setup width for the request.",
        "",
        "| Request | Cases | Outcomes | Immediate replies | Render pages | Render replies | Item types | Identities | Models | Status coverage | Setup | Evidence files |",
        "| ---: | ---: | --- | --- | ---: | --- | ---: | ---: | ---: | --- | --- | ---: |",
        ]
    )
    for record in document["requests"]:
        device = device_coverage_summary(record["device_coverage"], profiles)
        lines.append(
            "| {kind} | {cases} | {outcomes} | {immediate} | {pages} | {render_replies} | {types} | {profiles} | {models} | {status} | {setup} | {files} |".format(
                kind=f"`{record['kind']}`",
                cases=record["case_count"],
                outcomes=compact_outcomes(record["outcomes"]),
                immediate=compact_replies(record["immediate_reply_signatures"]),
                pages=record["render"]["page_count"],
                render_replies=compact_replies(record["render"]["reply_signatures"]),
                types=len(record["render"]["row_item_types"]),
                profiles=device["profile_count"],
                models=device["model_count"],
                status=device["status_boundary"],
                setup=device["setup_modes"],
                files=len(record["evidence_files"]),
            )
        )

    render = document["render_request"]
    render_device = device_coverage_summary(render["device_coverage"], profiles)
    lines.extend(
        [
            "",
            "## Render index",
            "",
            f"The corpus contains {render['page_count']} explicit `0x3000` page",
            f"transactions following {len(render['source_request_kinds'])} distinct",
            "menu-selection kinds. The exact render request type signatures are:",
            "",
            "| Arguments | Wire types | Pages |",
            "| ---: | --- | ---: |",
        ]
    )
    for signature in render["request_signatures"]:
        wire_types = ", ".join(f"`{value}`" for value in signature["argument_types"])
        lines.append(
            f"| {signature['argument_count']} | {wire_types or 'empty'} | {signature['page_count']} |"
        )
    lines.extend(
        [
            "",
            f"Observed render outcomes: {compact_outcomes(render['outcomes'])}.",
            f"Observed render reply signatures: {compact_replies(render['reply_signatures'])}.",
            "Render coverage spans "
            f"{render_device['profile_count']} exact identity "
            f"{'profile' if render_device['profile_count'] == 1 else 'profiles'}, "
            f"{render_device['model_count']} model "
            f"{'string' if render_device['model_count'] == 1 else 'strings'}, "
            f"{render_device['status_boundary']} identities, and "
            f"{render_device['setup_modes']} setup widths.",
            f"The `0x4101` rows contain {len(render['row_item_types'])} distinct composite item types.",
            "Their exact values and counts are in the JSON ledger and the semantic",
            "definitions remain in `ITEM_TYPE_REFERENCE.md`.",
            "",
            "## Reproduction",
            "",
            "```sh",
            "python3 tools/generate_observed_response_shapes.py",
            "python3 -m unittest conformance/test_observed_response_shapes.py",
            "```",
            "",
            "Regenerate this index after promoting or modifying a canonical",
            "Rekordbox golden. Do not update it from `.next`, failed-attempt, or",
            "backend-replay artifacts.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    document = collect(corpus_snapshot(), suite_snapshot())
    json_data = (json.dumps(document, indent=2) + "\n").encode()
    markdown_data = render_markdown(document).encode()

    if args.check:
        if JSON_OUTPUT.read_bytes() != json_data:
            raise SystemExit(f"stale generated artifact: {JSON_OUTPUT}")
        if MARKDOWN_OUTPUT.read_bytes() != markdown_data:
            raise SystemExit(f"stale generated artifact: {MARKDOWN_OUTPUT}")
        return

    JSON_OUTPUT.write_bytes(json_data)
    MARKDOWN_OUTPUT.write_bytes(markdown_data)


if __name__ == "__main__":
    main()
