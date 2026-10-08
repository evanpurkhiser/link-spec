#!/usr/bin/env python3
"""Validate and summarize SmartList My Tag behavior."""

from __future__ import annotations

import json
from pathlib import Path

from summarize_search_oracle import load, sha256, validate


ROOT = Path(__file__).resolve().parent.parent
CONFORMANCE = ROOT / "conformance"
SUITE = CONFORMANCE / "suites/smart-mytag-matrix.json"
GOLDEN = CONFORMANCE / "goldens/rekordbox-7.2.19/xdj-rx3/smart-mytag-matrix.json"
MANIFEST = CONFORMANCE / "fixtures/generated/smart-mytag-matrix/manifest.json"
DISASSEMBLY = ROOT / "data/static-analysis/smart-condition-evaluator.disasm.txt"
RESULT = CONFORMANCE / "results/rbxport/c144f19+tree.80e87ec8aace/summary.json"


def item_ids(case: dict[str, object]) -> list[int]:
    return [row["arguments"][1]["value"] for row in case["rows"]]


def expected_cases(
    suite: dict[str, object], manifest: dict[str, object]
) -> dict[str, list[int]]:
    ids = manifest["ids"]
    return {
        case["id"]: [
            ids[value.removeprefix("$fixture.")]
            for value in case["expect"]["item_ids"]
        ]
        for case in suite["cases"]
    }


def main() -> None:
    cases = validate(SUITE, GOLDEN, MANIFEST)
    suite = load(SUITE)
    manifest = load(MANIFEST)
    expected = expected_cases(suite, manifest)
    assert set(cases) == set(expected)
    for case_id, ids in expected.items():
        assert item_ids(cases[case_id]) == ids

    all_tracks = list(range(19001, 19009))
    complements = lambda selected: [track for track in all_tracks if track not in selected]
    membership = {
        "one": [19001, 19006],
        "zero": [19005],
        "int32_max": [19002],
        "high_bit": [19003, 19006, 19007],
        "uint32_max": [19004, 19007],
    }

    for operator in (*range(1, 8), 10, 11):
        assert expected[f"operator-{operator:02d}"] == []
    assert expected["operator-08"] == membership["one"]
    assert expected["operator-09"] == complements(membership["one"])

    boundary_values = {
        "zero": membership["zero"],
        "int32-max": membership["int32_max"],
        "high-bit-raw": membership["int32_max"],
        "uint32-max": membership["int32_max"],
        "minus-one": membership["uint32_max"],
        "int32-min": membership["high_bit"],
        "uint32-overflow": membership["int32_max"],
        "negative-overflow": membership["high_bit"],
        "blank": [],
        "invalid": membership["zero"],
        "leading-zero-one": membership["one"],
        "plus-one": membership["one"],
        "spaced-one": membership["one"],
        "hex-one": membership["zero"],
        "comma-pair": membership["one"],
    }
    for name, selected in boundary_values.items():
        assert expected[f"{name}-operator-08"] == selected
        excluded = [] if name == "blank" else complements(selected)
        assert expected[f"{name}-operator-09"] == excluded

    assert expected["value-right-ignored"] == membership["one"]
    assert expected["value-unit-ignored"] == membership["one"]
    assert expected["all-contains-one-high-bit"] == []
    assert expected["any-contains-one-high-bit"] == [19001, 19002, 19006]
    assert expected["all-not-contains-one-high-bit"] == [
        19003,
        19004,
        19005,
        19007,
        19008,
    ]
    assert expected["any-not-contains-one-high-bit"] == all_tracks
    assert expected["all-contains-one-not-high-bit"] == membership["one"]
    assert expected["any-contains-one-not-high-bit"] == [
        19001,
        19003,
        19004,
        19005,
        19006,
        19007,
        19008,
    ]

    disassembly = DISASSEMBLY.read_text()
    for evidence in (
        "address=0x1023354a0",
        "0x01023354ab  cmp       rcx, 0x40",
        "0x01023356f4  cmp       eax, 8",
        "0x01023356f9  mov       r8d, dword ptr [rdi + 0x44c]",
        "0x0102335708  mov       rsi, qword ptr [rdi + 0x440]",
        "0x0102336623  lea       rsi, [rip + 0x3016e6d]  ; 'myTag'",
        "0x01023366ad  call      0x1027d9810  ; __ZNK4juce10XmlElement15getIntAttribute",
        "0x01023366b4  mov       ecx, 0x40",
    ):
        assert evidence in disassembly

    replay = load(RESULT)
    result = next(
        item for item in replay["suites"] if item["suite"] == "smart-mytag-matrix"
    )
    empty_controls = [case_id for case_id, ids in expected.items() if not ids]
    nonempty = [case_id for case_id, ids in expected.items() if ids]
    assert result["cases"] == 49
    assert result["exact_cases"] == empty_controls
    assert result["same_outcome_total_row_count_cases"] == empty_controls
    assert result["different_cases"] == nonempty

    report = {
        "format": "rekordbox-link-export-smart-mytag-matrix-v1",
        "oracle": {
            "cases": len(expected),
            "golden_sha256": sha256(GOLDEN),
            "suite_sha256": sha256(SUITE),
            "immediate_repeat_verified": True,
        },
        "fixture": {
            "profile": "smart-mytag-matrix",
            "database_sha256": manifest["database_sha256"],
            "fingerprint": manifest["fixture_fingerprint"],
            "tracks": manifest["track_count"],
            "smart_playlists": len(expected),
        },
        "static_evidence": {
            "path": str(DISASSEMBLY.relative_to(ROOT)),
            "sha256": sha256(DISASSEMBLY),
            "evaluator": "db::operate(RowDataTrack const*, SmartlistCondition const&)",
            "evaluator_address": "0x1023354a0",
            "parser_address": "0x102336623",
            "property_type": "0x40",
            "track_tag_array_offset": "0x440",
            "track_tag_count_offset": "0x44c",
        },
        "behavior": {
            "operators": {"8": "contains", "9": "not_contains"},
            "other_operators_return_empty": True,
            "value_right_ignored": True,
            "value_unit_ignored": True,
            "positive_overflow_saturates_to_int32_max": True,
            "negative_overflow_saturates_to_int32_min": True,
            "negative_values_compare_by_uint32_bit_pattern": True,
            "blank_value_returns_empty_for_both_operators": True,
            "invalid_value_coerces_to_zero": True,
            "decimal_prefix_parsing": True,
            "hex_prefix_is_not_recognized": True,
            "membership": membership,
            "case_item_ids": expected,
        },
        "rbxport": {
            "version": replay["backend_version"],
            "cases": result["cases"],
            "exact": len(result["exact_cases"]),
            "same_outcome_total_row_count": len(
                result["same_outcome_total_row_count_cases"]
            ),
            "exact_empty_controls": result["exact_cases"],
            "nonempty_oracle_cases_returned_empty": nonempty,
        },
    }
    output = ROOT / "data/experiments/smart-mytag-matrix/summary.json"
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(output)


if __name__ == "__main__":
    main()
