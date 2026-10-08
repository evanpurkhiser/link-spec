#!/usr/bin/env python3
"""Validate and summarize SmartList downstream serving-path behavior."""

from __future__ import annotations

import json
from pathlib import Path

from summarize_search_oracle import load, sha256, validate


ROOT = Path(__file__).resolve().parent.parent
CONFORMANCE = ROOT / "conformance"
SUITE = CONFORMANCE / "suites/smart-serving-crosses.json"
GOLDEN = CONFORMANCE / "goldens/rekordbox-7.2.19/xdj-rx3/smart-serving-crosses.json"
LEGACY_SUITE = CONFORMANCE / "suites/smart-serving-legacy.json"
LEGACY_GOLDEN = CONFORMANCE / "goldens/rekordbox-7.2.19/xdj-rx3/smart-serving-legacy.json"
MANIFEST = CONFORMANCE / "fixtures/generated/smart-rule-matrix/manifest.json"
RESULT = CONFORMANCE / "results/rbxport/c144f19+tree.80e87ec8aace/summary.json"
DISASSEMBLY = ROOT / "data/static-analysis/smart-playlist-paths.disasm.txt"


def item_ids(case: dict[str, object]) -> list[int]:
    return [row["arguments"][1]["value"] for row in case["rows"]]


def main() -> None:
    cases = validate(SUITE, GOLDEN, MANIFEST)
    legacy = validate(LEGACY_SUITE, LEGACY_GOLDEN, MANIFEST)
    manifest = load(MANIFEST)

    sort_cases = {key: value for key, value in cases.items() if key.startswith("sort-")}
    render_cases = {key: value for key, value in cases.items() if key.startswith("render-")}
    page_cases = {key: value for key, value in cases.items() if key.startswith("page-")}
    context_cases = {key: value for key, value in cases.items() if key.startswith("context-")}
    assert [len(group) for group in (sort_cases, render_cases, page_cases, context_cases)] == [18, 19, 9, 19]

    all_tracks = list(range(10001, 10009))
    sort_orders = {case_id: item_ids(case) for case_id, case in sort_cases.items()}
    assert all(case["outcome"] == "menu" and case["total"] == 8 for case in sort_cases.values())
    assert all(sorted(order) == all_tracks for order in sort_orders.values())

    render_item_types = {
        case_id: case["rows"][0]["arguments"][6]["value"]
        for case_id, case in render_cases.items()
    }
    assert all(case["outcome"] == "menu" and item_ids(case) == all_tracks for case in render_cases.values())
    assert render_item_types == {
        "render-database-selection-zero-gate": 0x0F04,
        "render-override-disabled-with-zero-gate": 0x0F04,
        "render-database-selection": 0x0F04,
        **{f"render-override-{sort_id:02d}": item_type for sort_id, item_type in {
            2: 0x0704,
            3: 0x0204,
            4: 0x0D04,
            5: 0x0A04,
            6: 0x0604,
            7: 0x2304,
            8: 0x0B04,
            9: 0x2904,
            10: 0x0E04,
            11: 0x2804,
            12: 0x0F04,
            13: 0x1004,
            14: 0x0004,
            15: 0x1404,
            16: 0x2A04,
            17: 0x2E04,
        }.items()},
    }

    pagination = {
        case_id: {
            "outcome": case["outcome"],
            "total": case.get("total"),
            "item_ids": item_ids(case),
        }
        for case_id, case in page_cases.items()
    }
    assert pagination["page-zero-count"]["item_ids"] == [10001]
    assert pagination["page-at-end"]["item_ids"] == [10008]
    assert pagination["page-past-end"]["item_ids"] == [10008]
    assert pagination["page-overrun"]["item_ids"] == all_tracks
    assert pagination["page-overlap"]["item_ids"] == [10001, 10002, 10003, 10003, 10004, 10005]
    assert pagination["page-maximum-offset"]["outcome"] == "render_timeout"

    accepted_contexts = sorted(
        case_id for case_id, case in context_cases.items() if case["outcome"] == "menu"
    )
    timeout_contexts = sorted(
        case_id for case_id, case in context_cases.items() if case["outcome"] == "timeout"
    )
    assert timeout_contexts == [f"context-player-{player}" for player in range(2, 7)]
    assert len(accepted_contexts) == 14
    assert all(item_ids(context_cases[case_id]) == all_tracks for case_id in accepted_contexts)

    legacy_case = legacy["tracks"]
    assert legacy_case["outcome"] == "menu"
    assert item_ids(legacy_case) == all_tracks
    assert {len(row["arguments"]) for row in legacy_case["rows"]} == {12}
    assert {len(row["arguments"]) for case in sort_cases.values() for row in case["rows"]} == {16}

    disassembly = DISASSEMBLY.read_text()
    for evidence in (
        "address=0x100489470",
        "0x0100489eb9  call      0x1004dab10  ; __Z12SetTrackSort",
        "0x0100489ed6  lea       rsi, [rip + 0x4eb4e9c]  ; 'djmdTrackSort'",
        "0x0100489f0a  call      0x1004db980  ; __Z19Sort_SortTrackTable",
        "0x01019c3db7  call      0x102334b00  ; __ZN2db23getSmartlistContentData",
    ):
        assert evidence in disassembly

    replay = load(RESULT)
    replay_cases = {
        item["suite"]: item
        for item in replay["suites"]
        if item["suite"] in {"smart-serving-crosses", "smart-serving-legacy"}
    }
    assert set(replay_cases) == {"smart-serving-crosses", "smart-serving-legacy"}
    for suite_name, count in (("smart-serving-crosses", 65), ("smart-serving-legacy", 1)):
        result = replay_cases[suite_name]
        assert result["cases"] == count
        assert result["exact_cases"] == []
        assert result["same_outcome_total_row_count_cases"] == []
        assert len(result["different_cases"]) == count

    report = {
        "format": "rekordbox-link-export-smart-serving-crosses-v1",
        "oracle": {
            "extended_cases": len(cases),
            "legacy_cases": len(legacy),
            "golden_sha256": sha256(GOLDEN),
            "legacy_golden_sha256": sha256(LEGACY_GOLDEN),
            "suite_sha256": sha256(SUITE),
            "legacy_suite_sha256": sha256(LEGACY_SUITE),
            "immediate_repeat_verified": True,
        },
        "fixture": {
            "profile": "smart-rule-matrix",
            "database_sha256": manifest["database_sha256"],
            "fingerprint": manifest["fixture_fingerprint"],
            "playlist": manifest["ids"]["playlist.smart_matrix.logic_any"],
            "tracks": manifest["track_count"],
        },
        "behavior": {
            "sort_orders": sort_orders,
            "render_item_types": {
                case_id: f"0x{item_type:04x}"
                for case_id, item_type in render_item_types.items()
            },
            "pagination": pagination,
            "accepted_contexts": accepted_contexts,
            "timeout_contexts": timeout_contexts,
            "extended_argument_count": 16,
            "legacy_argument_count": 12,
            "rule_results_feed_shared_sort_render_pagination_and_context_paths": True,
        },
        "static_evidence": {
            "path": str(DISASSEMBLY.relative_to(ROOT)),
            "sha256": sha256(DISASSEMBLY),
            "playlist_rowset_address": "0x100489470",
            "smart_content_loader_address": "0x102334b00",
        },
        "rbxport": {
            "version": replay["backend_version"],
            "cases": 66,
            "exact": 0,
            "same_outcome_total_row_count": 0,
            "cause": "Link Export uses materialized membership instead of SmartList evaluation",
        },
    }
    output = ROOT / "data/experiments/smart-serving-crosses/summary.json"
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(output)


if __name__ == "__main__":
    main()
