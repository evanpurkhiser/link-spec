import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFORMANCE = ROOT / "conformance"
GENERATOR = CONFORMANCE / "generate_xdj_rr_old_key_suites.py"
DECLARATION = CONFORMANCE / "data/xdj-rr-old-key-matrix.json"
SUITES = CONFORMANCE / "suites/generated/xdj-rr-old-key"
SOURCE = ROOT / "data/static-analysis/xdj-rr-client-navigation.json"
DISPATCH = ROOT / "data/static-analysis/link-export-dispatch-tables.json"


class XdjRrOldKeyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.declaration = json.loads(DECLARATION.read_text())

    def test_source_and_dispatch_define_exact_terminal_paths(self):
        source = json.loads(SOURCE.read_text())
        wrappers = {item["request_kind"]: item for item in source["wrappers"]}
        for kind in ("100B", "110B", "130C"):
            with self.subTest(kind=kind):
                self.assertIn(kind, wrappers)
                self.assertEqual(wrappers[kind]["location_parameter"], 2)

        dispatch = json.loads(DISPATCH.read_text())
        entries = {
            item["request_kind"]: item for item in dispatch["direct_dispatch"]
        }
        self.assertIn("getKey_Root", entries["100B"]["target"])
        self.assertIn("getTrack_Key", entries["110B"]["target"])
        self.assertEqual(entries["130C"]["target"], "recognized-log-only")

    def test_reducer_requires_repeat_equivalent_process_health(self):
        reducer = (ROOT / "tools/summarize_xdj_rr_old_key.py").read_text()
        self.assertIn("validate_health_pair(", reducer)

    def test_live_boundary_names_the_current_guarded_generation(self):
        for document in ("docs/XDJ_RR_ADJACENT_COMMANDS.md", "docs/XDJ_RR_CLIENT_NAVIGATION.md"):
            with self.subTest(document=document):
                source = (ROOT / document).read_text()
                self.assertIn("generation `ae18`", source)
                self.assertNotIn("generation `ae2`", source)

    def test_matrix_crosses_three_identities_and_both_setups(self):
        variants = self.declaration["variants"]
        self.assertEqual(len(variants), 6)
        self.assertEqual(self.declaration["cases_per_variant"], 8)
        self.assertEqual(
            {(entry["model"], entry["setup"]) for entry in variants},
            {
                (model, setup)
                for model in (
                    "xdj-rx3-ordinary",
                    "xdj-rx3-status",
                    "cdj-3000-status",
                )
                for setup in ("extended", "legacy")
            },
        )

    def test_each_silent_probe_has_a_fresh_health_control(self):
        expected_ids = [
            "old-key-root-location-1",
            "old-key-am-tracks-location-1",
            "old-key-root-location-2",
            "old-key-c-tracks-location-2",
            "cue-track-root-location-1",
            "old-key-root-after-cue-location-1",
            "cue-track-root-location-2",
            "old-key-root-after-cue-location-2",
        ]
        for entry in self.declaration["variants"]:
            suite = json.loads((CONFORMANCE / entry["suite"]).read_text())
            cases = suite["cases"]
            with self.subTest(variant=entry["id"]):
                self.assertEqual([case["id"] for case in cases], expected_ids)
                self.assertTrue(all(case["fresh_connection"] for case in cases))
                self.assertEqual(cases[4]["expect"], {"outcome": "timeout"})
                self.assertEqual(cases[6]["expect"], {"outcome": "timeout"})
                for index in (5, 7):
                    self.assertEqual(cases[index]["request_kind"], "0x100b")
                    self.assertEqual(cases[index]["expect"]["outcome"], "menu")

    def test_regeneration_is_byte_identical(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "suites"
            matrix = Path(directory) / "matrix.json"
            subprocess.run(
                [
                    "python3",
                    str(GENERATOR),
                    "--output",
                    str(output),
                    "--matrix",
                    str(matrix),
                ],
                cwd=ROOT,
                check=True,
                capture_output=True,
            )
            self.assertEqual(matrix.read_bytes(), DECLARATION.read_bytes())
            for suite in SUITES.glob("*.json"):
                self.assertEqual((output / suite.name).read_bytes(), suite.read_bytes())


if __name__ == "__main__":
    unittest.main()
