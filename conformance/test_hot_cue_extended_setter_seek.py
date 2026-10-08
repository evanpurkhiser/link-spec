import json
import struct
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MATRIX = ROOT / "data/hot-cue-setter-seek-matrix.json"
RECORDER = ROOT / "record_hot_cue_extended_setter_seek_matrix.sh"
TOOLS = ROOT.parent / "tools"
sys.path.insert(0, str(TOOLS))

from summarize_hot_cue_extended_setter_seek import (
    assert_expected_result,
    database_signature,
    process_state,
    seek_string_signature,
)


class HotCueExtendedSetterSeekTest(unittest.TestCase):
    def test_matrix_covers_seek_boundaries(self) -> None:
        variants = json.loads(MATRIX.read_text())["variants"]
        self.assertEqual(len(variants), 17)
        self.assertEqual(
            {item["axis"] for item in variants},
            {"actual-length", "descriptor-length", "seek-values"},
        )
        self.assertEqual(
            [item["value"] for item in variants if item["axis"] == "actual-length"],
            [74, 81, 82, 121, 122, 123, 124],
        )

    def test_suite_lengths_and_descriptor_fields(self) -> None:
        variants = json.loads(MATRIX.read_text())["variants"]
        for variant in variants:
            suite = json.loads((ROOT / variant["suite"]).read_text())
            self.assertEqual(len(suite["cases"]), 1)
            setter = suite["cases"][0]
            record = bytes.fromhex(setter["arguments"][4]["blob_hex"])
            self.assertEqual(len(record), variant["record_length"])
            self.assertEqual(setter["arguments"][3]["number"], len(record))
            self.assertEqual(struct.unpack_from("<I", record)[0], len(record))
            if variant["axis"] == "actual-length":
                self.assertEqual(struct.unpack_from("<I", record, 0x34)[0], len(record) - 56)

        descriptor_values = {
            item["value"] for item in variants if item["axis"] == "descriptor-length"
        }
        self.assertEqual(descriptor_values, {0, 1, 43, 44, 45, 0xFFFFFFFF})

        inbound = next(item for item in variants if item["id"] == "inbound-validity-00000001")
        suite = json.loads((ROOT / inbound["suite"]).read_text())
        record = bytes.fromhex(suite["cases"][0]["arguments"][4]["blob_hex"])
        self.assertEqual(struct.unpack_from(">QQQQII", record, 0x52), (1, 2, 3, 4, 1, 0))

    def test_recorder_preserves_and_retries_incomplete_cold_runs(self) -> None:
        recorder = RECORDER.read_text()

        self.assertIn('${destination}.${suffix}-$(date -u +%Y%m%dT%H%M%SZ)', recorder)
        self.assertIn("suffix=invalid-receipt", recorder)
        self.assertIn("for attempt in 1 2 3", recorder)
        self.assertIn("restarting the full cold cycle", recorder)
        self.assertIn('run_once "$variant" "$run" "$suite" &', recorder)
        self.assertIn('if wait "$attempt_pid"; then', recorder)
        self.assertIn("complete_run_valid", recorder)
        self.assertIn('[[ -s $destination/database-snapshot.json ]]', recorder)
        self.assertIn('run_with_retries "$variant" 1 "$suite"', recorder)
        self.assertIn('run_with_retries "$variant" 2 "$suite"', recorder)

    def test_uninitialized_descriptor_comparison_preserves_exact_evidence(self) -> None:
        first = [{"ID": "1", "InPointSeekInfo": "1,2,3", "OutPointSeekInfo": "4,5,6"}]
        second = [{"ID": "1", "InPointSeekInfo": "7,8,9", "OutPointSeekInfo": "10,11,12"}]

        self.assertNotEqual(first, second)
        self.assertEqual(
            database_signature("actual-length-00000052", first),
            database_signature("actual-length-00000052", second),
        )
        self.assertIs(database_signature("actual-length-00000051", first), first)

        self.assertEqual(seek_string_signature(""), {"shape": "empty"})
        with self.assertRaises(AssertionError):
            seek_string_signature("1,2")
        with self.assertRaises(AssertionError):
            seek_string_signature("1,2,-3")

    def test_health_state_distinguishes_replacement_overlap(self) -> None:
        self.assertEqual(process_state(0), "exited")
        self.assertEqual(process_state(1), "alive")
        self.assertEqual(process_state(2), "replacement-overlap")
        with self.assertRaises(AssertionError):
            process_state(3)

    def test_expected_seek_values_are_asserted(self) -> None:
        timeout = {
            "outcome": "timeout",
            "error_kind": "WouldBlock",
            "messages": [],
        }
        memberships = [
            {"InPointSeekInfo": "1,3,1", "OutPointSeekInfo": "2,4,0"},
            {"InPointSeekInfo": "", "OutPointSeekInfo": ""},
        ]
        assert_expected_result(
            "inbound-validity-00000001",
            timeout,
            "replacement-overlap",
            memberships,
        )

        memberships[0]["InPointSeekInfo"] = "1,3,2"
        with self.assertRaises(AssertionError):
            assert_expected_result(
                "inbound-validity-00000001",
                timeout,
                "replacement-overlap",
                memberships,
            )

    def test_database_query_document_promotes_completed_seek_matrix(self) -> None:
        document = (ROOT.parent / "docs/DATABASE_QUERIES.md").read_text()

        self.assertIn("completed 17-case health matrix", document)
        self.assertIn("Fourteen variants return the canonical status-zero", document)
        self.assertNotIn("declared 17-case health matrix", document)

        coverage = (ROOT.parent / "docs/CONFORMANCE_COVERAGE.md").read_text()
        self.assertIn(
            "adjacent extended-parser, mutable-field, seek-descriptor, "
            "legacy-parser, and identical-request lifecycle matrices",
            coverage,
        )
        self.assertNotIn(
            "Setter malformed-length/field-boundary matrices and inbound-seek "
            "fault localization remain",
            coverage,
        )


if __name__ == "__main__":
    unittest.main()
