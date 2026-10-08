import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAP = ROOT / "data/configuration-behavior-map.json"
GENERATOR = ROOT / "tools/generate_configuration_behavior_map.py"


class ConfigurationBehaviorMapTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = json.loads(MAP.read_text())

    def test_source_domains_are_complete(self):
        sources = self.document["sources"]
        self.assertEqual(27, sources["djmdMenuItems"]["row_count"])
        self.assertEqual(21, sources["djmdCategory"]["row_count"])
        self.assertEqual(17, sources["djmdSort"]["row_count"])
        self.assertEqual(8, sources["djmdColor"]["row_count"])

    def test_controlled_root_has_twenty_rows_and_suppresses_folder(self):
        visible = [
            row
            for row in self.document["categories"]
            if row["visible_in_controlled_root"]
        ]
        self.assertEqual(20, len(visible))
        folder = next(
            row for row in self.document["categories"] if row["Name"] == "FOLDER"
        )
        self.assertTrue(folder["visible_before_folder_suppression"])
        self.assertFalse(folder["visible_in_controlled_root"])

    def test_sort_visibility_and_column_selection_are_independent(self):
        sorts = self.document["sorts"]
        self.assertEqual(11, sum(row["visible_in_sort_menu"] for row in sorts))
        selected = [row for row in sorts if row["selected_as_persisted_column"]]
        self.assertEqual([12], [row["ID"] for row in selected])
        self.assertTrue(selected[0]["visible_in_sort_menu"])

    def test_six_argument_cross_is_complete_and_keeps_final_value_twelve(self):
        observations = self.document["six_argument_active_sort_observations"]
        self.assertEqual(
            {0, 1, 2, 3, 4, 5, 6, 10, 12, 16, 17},
            {row["sort_id"] for row in observations},
        )
        self.assertEqual({6}, {row["render_argument_count"] for row in observations})
        self.assertEqual({12}, {row["render_argument_6"] for row in observations})
        self.assertEqual({8}, {row["row_count"] for row in observations})

    def test_key_and_bpm_composite_orientation(self):
        observations = {
            row["sort_id"]: row
            for row in self.document["six_argument_active_sort_observations"]
        }
        self.assertEqual(
            "Am - 120.0 bpm",
            observations[12]["first_row"]["argument_5_secondary_text"],
        )
        self.assertEqual(
            "120.0 bpm - Am",
            observations[4]["first_row"]["argument_5_secondary_text"],
        )
        self.assertEqual(
            "Alpha Artist",
            observations[2]["first_row"]["argument_5_secondary_text"],
        )
        self.assertEqual(
            "Album One",
            observations[3]["first_row"]["argument_5_secondary_text"],
        )

    def test_extended_key_and_bpm_metadata_survives_every_active_sort(self):
        for observation in self.document["six_argument_active_sort_observations"]:
            row = observation["first_row"]
            self.assertIn("argument_12_original_key_id", row)
            self.assertIn(
                "argument_13_key_text_utf16_byte_length_including_nul", row
            )
            self.assertIn("argument_14_key_text", row)
            self.assertIn("argument_15_bpm_x100", row)

    def test_regeneration_is_byte_identical(self):
        runtime = ROOT / "conformance/runtime"
        runtime.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=runtime) as directory:
            output = Path(directory) / MAP.name
            subprocess.run(
                [str(ROOT / ".venv/bin/python"), str(GENERATOR), "--output", str(output)],
                cwd=ROOT,
                check=True,
                capture_output=True,
            )
            self.assertEqual(output.read_bytes(), MAP.read_bytes())


if __name__ == "__main__":
    unittest.main()
