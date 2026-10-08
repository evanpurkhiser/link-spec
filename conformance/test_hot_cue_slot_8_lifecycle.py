import json
import unittest
from pathlib import Path

import generate_hot_cue_slot_8_lifecycle_suites as lifecycle


ROOT = Path(__file__).resolve().parent
RECORDER = ROOT / "record_hot_cue_slot_8_lifecycle.sh"


class HotCueSlot8LifecycleTests(unittest.TestCase):
    def test_declarations_preserve_unknown_lifecycle_outcomes(self) -> None:
        observation = lifecycle.observation_suite()
        restart = lifecycle.restart_getter_suite()

        self.assertEqual(3, observation["lifecycle_probe"]["replicates"])
        self.assertEqual(
            ["setter", "database-read-after-setter"],
            [case["id"] for case in observation["cases"]],
        )
        self.assertEqual("any", observation["cases"][0]["expect"]["outcome"])
        self.assertEqual("any", observation["cases"][1]["expect"]["outcome"])
        self.assertEqual(
            ["database-read-after-process-restart"],
            [case["id"] for case in restart["cases"]],
        )
        self.assertEqual("any", restart["cases"][0]["expect"]["outcome"])

    def test_checked_in_declarations_match_generator(self) -> None:
        matrix = json.loads(lifecycle.MATRIX.read_text())
        self.assertEqual(lifecycle.matrix(), matrix)

        for key, expected in (
            ("observation_suite", lifecycle.observation_suite()),
            ("restart_getter_suite", lifecycle.restart_getter_suite()),
        ):
            path = ROOT / matrix[key]
            self.assertEqual(expected, json.loads(path.read_text()))

    def test_recorder_retains_health_database_and_restart_provenance(self) -> None:
        recorder = RECORDER.read_text()

        self.assertNotIn("rbxport", recorder.lower())
        self.assertIn("capture_rekordbox_health.ps1", recorder)
        self.assertIn("snapshot_hot_cue_mutation.py", recorder)
        self.assertIn("snapshot-after-observation.json", recorder)
        self.assertIn("snapshot-after-restart.json", recorder)
        self.assertIn("restart-getter.json", recorder)
        self.assertIn("complete.json", recorder)
        self.assertIn("Stop-Process -Force", recorder)
        self.assertIn("same-database restart", recorder)


if __name__ == "__main__":
    unittest.main()
