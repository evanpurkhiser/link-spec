import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
GOLDEN = ROOT / "conformance/goldens/rekordbox-7.2.19/xdj-rx3/history-lifecycle.json"
REFERENCE = ROOT / "PROTOCOL_REFERENCE.md"


def number(row: dict, index: int) -> int:
    argument = row["arguments"][index]
    assert argument["type"] == "number"
    return int(argument["value"])


class HistoryLifecycleDocumentationTests(unittest.TestCase):
    def test_documented_lifecycle_matches_canonical_golden(self) -> None:
        golden = json.loads(GOLDEN.read_text())
        cases = {case["id"]: case for case in golden["behavior"]["cases"]}

        expected_totals = {
            "initial-root": 0,
            "root-after-first": 1,
            "tracks-after-first": 1,
            "tracks-after-second": 2,
            "remove-first": 0,
            "tracks-after-remove": 1,
            "final-root": 0,
        }
        self.assertEqual(
            {case_id: cases[case_id]["total"] for case_id in expected_totals},
            expected_totals,
        )

        root = cases["root-after-first"]["rows"][0]
        self.assertEqual(root["arguments"][3]["value"], "LINK HISTORY 2026-09-30")
        self.assertEqual(number(root, 6), 0x24)
        self.assertEqual(
            [number(row, 1) for row in cases["tracks-after-second"]["rows"]],
            [10001, 10002],
        )
        self.assertEqual(
            [number(row, 9) for row in cases["tracks-after-second"]["rows"]],
            [1, 2],
        )
        remaining = cases["tracks-after-remove"]["rows"][0]
        self.assertEqual(number(remaining, 1), 10002)
        self.assertEqual(number(remaining, 9), 1)

    def test_reference_preserves_the_remaining_boundary(self) -> None:
        reference = REFERENCE.read_text()

        self.assertIn("Cross-day rollover", reference)
        self.assertIn("restart without first deleting", reference)
        self.assertIn("simultaneous", reference)
        self.assertIn("multi-player ownership", reference)
        self.assertNotIn(
            "Unknown:** exact rollover, naming, persistence, flag value, and multi-player/session rules",
            reference,
        )


if __name__ == "__main__":
    unittest.main()
