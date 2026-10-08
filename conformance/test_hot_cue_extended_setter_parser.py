import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

import generate_hot_cue_extended_setter_parser_suites as parser_suites

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import summarize_hot_cue_extended_setter_parser as summarize


class HotCueExtendedSetterParserTests(unittest.TestCase):
    def test_matrix_covers_every_declared_boundary_once(self) -> None:
        variants = parser_suites.variants()
        by_axis = {}
        for variant in variants:
            by_axis.setdefault(variant.axis, []).append(variant.value)

        self.assertEqual(57, len(variants))
        self.assertEqual(57, len({variant.id for variant in variants}))
        self.assertEqual(
            {
                "record-count": [0, 1, 2, 0xFFFFFFFF],
                "actual-length": [0, 1, 55, 56, 123, 124, 125],
                "declared-length": [0, 55, 56, 123, 124, 125, 0xFFFFFFFF],
                "record-size": [0, 55, 56, 123, 124, 125, 0xFFFFFFFF],
                "slot": [0, 1, 8, 9, 0xFFFF],
                "cue-type": [0, 1, 2, 3, 0xFF],
                "time-unit": [0, 74, 75, 76, 149, 150, 151, 999, 1000, 1001, 0xFFFF],
                "option-length": [0, 1, 65, 66, 67, 0xFFFFFFFF],
                "returned-slots": [0, 1, 2, 8, 0xFFFFFFFF],
            },
            by_axis,
        )

    def test_each_suite_is_fixture_isolated_and_has_a_database_control(self) -> None:
        for variant in parser_suites.variants():
            suite = parser_suites.suite(variant)
            self.assertEqual("hot-cue-bank-mutation", suite["fixture_profile"])
            self.assertEqual(
                "duplicate-slot",
                suite["parser_probe"]["fixture_variant"],
            )
            self.assertEqual("fixture-reset-and-restart", suite["repeat_strategy"])
            self.assertEqual(
                ["setter", "database-read-after-setter"],
                [case["id"] for case in suite["cases"]],
            )
            setter = suite["cases"][0]
            getter = suite["cases"][1]
            self.assertEqual("0x2401", setter["request_kind"])
            self.assertEqual("0x2301", getter["request_kind"])
            self.assertTrue(setter["fresh_connection"])
            self.assertTrue(getter["fresh_connection"])

    def test_checked_in_suites_match_the_generator(self) -> None:
        for variant in parser_suites.variants():
            expected = parser_suites.suite(variant)
            path = (
                parser_suites.ROOT
                / "suites/generated/hot-cue-setter-parser"
                / f"hot-cue-setter-parser-{variant.id}.json"
            )
            self.assertEqual(expected, json.loads(path.read_text()))

    def test_matrix_delegates_discovered_lifecycle_boundaries(self) -> None:
        expected = parser_suites.matrix()
        actual = json.loads(
            (parser_suites.ROOT / "data/hot-cue-setter-parser-matrix.json").read_text()
        )
        self.assertEqual(expected, actual)

        lifecycle = [
            variant
            for variant in actual["variants"]
            if variant["record_mode"] == "lifecycle"
        ]
        self.assertEqual(
            [
                "declared-length-ffffffff",
                "slot-00000008",
                "returned-slots-ffffffff",
            ],
            [item["id"] for item in lifecycle],
        )
        self.assertTrue(all("golden" not in item for item in lifecycle))
        self.assertTrue(
            all(item["evidence"].endswith("/summary.json") for item in lifecycle)
        )
        self.assertEqual(
            54,
            sum(
                variant["record_mode"] == "golden"
                for variant in actual["variants"]
            ),
        )

    def test_lifecycle_promotion_requires_complete_pristine_evidence(self) -> None:
        baseline = bytes(range(124)).hex()
        baseline_sha256 = hashlib.sha256(bytes.fromhex(baseline)).hexdigest()
        observation = {
            "signatures": {"setter": "0100"},
            "final_getter": {
                "status": 0,
                "record_count": 1,
                "record_length": 124,
                "record_sha256": baseline_sha256,
            },
        }
        document = {
            "experiment": "hot-cue-declared-length-ffffffff-lifecycle",
            "complete": True,
            "completed_observations": 60,
            "declared_observations": 60,
            "fixture_database_sha256": "fixture-sha256",
            "results": [observation] * 60,
        }
        declared = next(
            variant
            for variant in parser_suites.matrix()["variants"]
            if variant["id"] == "declared-length-ffffffff"
        )

        with tempfile.TemporaryDirectory() as directory:
            evidence = Path(directory) / "summary.json"
            evidence.write_text(json.dumps(document))
            variant = {**declared, "evidence": str(evidence)}
            result = summarize.lifecycle_result(
                variant,
                "fixture-sha256",
                baseline,
            )

        self.assertIsNotNone(result)
        self.assertEqual("lifecycle", result["evidence_mode"])
        self.assertEqual(60, result["observations"])
        self.assertEqual(240, result["case_executions"])
        self.assertEqual("pristine", result["database_effect"])

    def test_lifecycle_promotion_rejects_incomplete_evidence(self) -> None:
        declared = next(
            variant
            for variant in parser_suites.matrix()["variants"]
            if variant["id"] == "declared-length-ffffffff"
        )
        document = {
            "experiment": "hot-cue-declared-length-ffffffff-lifecycle",
            "complete": False,
            "completed_observations": 59,
            "declared_observations": 60,
            "fixture_database_sha256": "fixture-sha256",
            "results": [],
        }

        with tempfile.TemporaryDirectory() as directory:
            evidence = Path(directory) / "summary.json"
            evidence.write_text(json.dumps(document))
            variant = {**declared, "evidence": str(evidence)}
            with self.assertRaises(AssertionError):
                summarize.lifecycle_result(variant, "fixture-sha256", "00" * 124)

    def test_returned_slots_lifecycle_preserves_durable_mutation(self) -> None:
        baseline = "00" * 124
        mutated_sha256 = hashlib.sha256(summarize.build_record()).hexdigest()
        declared = next(
            variant
            for variant in parser_suites.matrix()["variants"]
            if variant["id"] == "returned-slots-ffffffff"
        )
        document = {
            "experiment": "hot-cue-returned-slots-ffffffff-lifecycle",
            "complete": True,
            "completed_observations": 3,
            "declared_observations": 3,
            "fixture_database_sha256": "fixture-sha256",
            "aggregate": {
                "database_effect_after_restart": "changed",
                "restart_getter": {
                    "status": 0,
                    "record_count": 1,
                    "record_length": 124,
                    "record_sha256": mutated_sha256,
                },
            },
            "results": [{"run": run} for run in range(1, 4)],
        }

        with tempfile.TemporaryDirectory() as directory:
            evidence = Path(directory) / "summary.json"
            evidence.write_text(json.dumps(document))
            result = summarize.lifecycle_result(
                {**declared, "evidence": str(evidence)},
                "fixture-sha256",
                baseline,
            )

        self.assertIsNotNone(result)
        self.assertEqual("lifecycle", result["evidence_mode"])
        self.assertEqual("changed", result["database_effect"])
        self.assertEqual(124, result["database_record_length"])
        self.assertEqual(mutated_sha256, result["database_record_sha256"])
        self.assertEqual(3, result["observations"])
        self.assertEqual(9, result["case_executions"])


if __name__ == "__main__":
    unittest.main()
