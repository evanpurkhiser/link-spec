import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SUITE = ROOT / "suites/bpm-tolerance-boundaries.json"
MANIFEST = ROOT / "fixtures/generated/bpm-tolerance-boundaries/manifest.json"
RECORDER = ROOT / "record_bpm_tolerance_boundaries.sh"
SUMMARIZER = ROOT.parent / "tools/summarize_bpm_tolerance_boundaries.py"


class BpmToleranceBoundarySuiteTests(unittest.TestCase):
    def test_suite_declares_every_advertised_tolerance(self) -> None:
        suite = json.loads(SUITE.read_text())
        cases = suite["cases"]

        self.assertEqual("bpm-tolerance-boundaries", suite["fixture_profile"])
        self.assertEqual("fixture-reset-and-restart", suite["repeat_strategy"])
        self.assertEqual(
            [f"tolerance-{value}" for value in range(7)],
            [case["id"] for case in cases],
        )
        self.assertTrue(all(case["request_kind"] == "0x1206" for case in cases))
        self.assertEqual(
            list(range(7)),
            [case["arguments"][3]["number"] for case in cases],
        )
        self.assertTrue(
            all(case["arguments"][2]["number"] == 12_000 for case in cases)
        )

    def test_fixture_and_real_rekordbox_tools_are_bound_to_the_suite(self) -> None:
        manifest = json.loads(MANIFEST.read_text())
        track_ids = {
            name: value
            for name, value in manifest["ids"].items()
            if name.startswith("track.bpm_")
        }

        self.assertEqual("bpm-tolerance-boundaries", manifest["profile"])
        self.assertEqual(43, manifest["track_count"])
        self.assertEqual(43, len(track_ids))
        self.assertEqual(
            "daffd7ce05f2b995a26d6320b577e0f2418eaf15a6199d0668c7bfd30ca55e32",
            manifest["fixture_fingerprint"],
        )
        self.assertIn("bpm-tolerance-boundaries.json", RECORDER.read_text())
        self.assertNotIn("rbxport", RECORDER.read_text().lower())
        self.assertIn("bpm-tolerance-boundaries.json", SUMMARIZER.read_text())

    def test_protocol_reference_does_not_leave_completed_capture_pending(self) -> None:
        protocol = (ROOT.parent / "PROTOCOL_REFERENCE.md").read_text()

        self.assertNotIn("Wire-verify the ±0–6% BPM boundaries", protocol)
        self.assertIn("119.50..120.49", protocol)


if __name__ == "__main__":
    unittest.main()
