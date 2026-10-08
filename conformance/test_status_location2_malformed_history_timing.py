import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
LAB = ROOT.parent
SUITE_ROOT = ROOT / "suites/generated/song-info-location2-malformed-history-timing"
CONFLICT_ROOT = (
    ROOT
    / "goldens/rekordbox-7.2.19/xdj-rx3-status/song-info-location2-malformed-history"
)


class StatusLocation2MalformedHistoryTimingTests(unittest.TestCase):
    def test_conflicting_cold_process_observations_are_preserved(self) -> None:
        record = json.loads(
            (CONFLICT_ROOT / "play-extra-argument__then__delivery-blob-content.json.next").read_text()
        )
        repeat = json.loads(
            (CONFLICT_ROOT / "play-extra-argument__then__delivery-blob-content.json.actual.json").read_text()
        )
        self.assertEqual("rekordbox", record["provenance"]["backend"])
        self.assertEqual("rekordbox-repeat", repeat["provenance"]["backend"])
        self.assertEqual(13, record["behavior"]["cases"][-1]["total"])
        self.assertEqual(0, repeat["behavior"]["cases"][-1]["total"])

    def test_timing_matrix_has_seven_delays_and_identical_semantics(self) -> None:
        paths = sorted(SUITE_ROOT.glob("*.json"))
        self.assertEqual(7, len(paths))
        delays = []
        for path in paths:
            suite = json.loads(path.read_text())
            self.assertEqual(3, len(suite["cases"]))
            self.assertEqual(11, suite["defaults"]["device"])
            self.assertEqual("0x0b010301", suite["defaults"]["context"])
            self.assertEqual(
                [
                    "first--play-extra-argument",
                    "second--delivery-blob-content",
                    "delivery-probe",
                ],
                [case["id"] for case in suite["cases"]],
            )
            self.assertTrue(all(case["fresh_connection"] for case in suite["cases"]))
            self.assertTrue(all(case["expect"] == {"outcome": "any"} for case in suite["cases"]))
            self.assertEqual(
                ["$context", "$context", "0x0b020301"],
                [case["arguments"][0]["number"] for case in suite["cases"]],
            )
            delays.append(suite["cases"][-1]["delay_before_connection_ms"])
        self.assertEqual([0, 50, 100, 250, 500, 1000, 3000], delays)

    def test_docs_preserve_conflict_and_timing_authority(self) -> None:
        documents = {
            "docs/REKORDBOX_RESEARCH_GAPS.md": "malformed-history timing",
            "docs/CONFORMANCE_COVERAGE.md": "pair-48 zero is an orphaned prior reply",
            "docs/EXPERIMENTS.md": "13-versus-zero",
            "docs/CLEANUP.md": "malformed-history-timing",
        }
        for name, fragment in documents.items():
            text = " ".join((LAB / name).read_text().split())
            with self.subTest(document=name):
                self.assertIn(fragment, text)


if __name__ == "__main__":
    unittest.main()
