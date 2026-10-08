import json
import unittest
from pathlib import Path

import generate_hot_cue_returned_slots_ffffffff_lifecycle_suites as lifecycle


ROOT = Path(__file__).resolve().parent
RECORDER = ROOT / "record_hot_cue_returned_slots_ffffffff_lifecycle.sh"


class HotCueReturnedSlotsUint32LifecycleTests(unittest.TestCase):
    def test_declarations_preserve_unknown_lifecycle_outcomes(self):
        observation = lifecycle.observation_suite()
        restart = lifecycle.restart_getter_suite()

        self.assertEqual(3, observation["lifecycle_probe"]["replicates"])
        self.assertEqual(0xFFFFFFFF, observation["lifecycle_probe"]["value"])
        self.assertEqual(
            ["setter", "database-read-after-setter"],
            [case["id"] for case in observation["cases"]],
        )
        self.assertTrue(
            all(case["expect"] == {"outcome": "any"} for case in observation["cases"])
        )
        self.assertEqual("any", restart["cases"][0]["expect"]["outcome"])

    def test_checked_in_declarations_match_generator(self):
        matrix = json.loads(lifecycle.MATRIX.read_text())
        self.assertEqual(lifecycle.matrix(), matrix)
        for key, expected in (
            ("observation_suite", lifecycle.observation_suite()),
            ("restart_getter_suite", lifecycle.restart_getter_suite()),
        ):
            self.assertEqual(expected, json.loads((ROOT / matrix[key]).read_text()))

    def test_recorder_delegates_to_health_aware_lifecycle_runner(self):
        recorder = RECORDER.read_text()
        self.assertNotIn("rbxport", recorder.lower())
        self.assertIn("record_hot_cue_slot_8_lifecycle.sh", recorder)
        self.assertIn("returned-slots-ffffffff", recorder)


if __name__ == "__main__":
    unittest.main()
