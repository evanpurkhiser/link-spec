import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFORMANCE = ROOT / "conformance"
GENERATOR = CONFORMANCE / "generate_xdj_rr_location9_suites.py"
DECLARATION = CONFORMANCE / "data/xdj-rr-location9-matrix.json"
SUITES = CONFORMANCE / "suites/generated/xdj-rr-location9"
SOURCE = ROOT / "data/static-analysis/xdj-rr-client-navigation.json"


class XdjRrLocation9Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.declaration = json.loads(DECLARATION.read_text())

    def test_source_defines_delivery_at_fixed_location_nine(self):
        source = json.loads(SOURCE.read_text())
        wrapper = next(
            item
            for item in source["wrappers"]
            if item["name"] == "dbcl_GetDeliverySongInfo"
        )
        self.assertEqual(wrapper["request_kind"], "2602")
        self.assertEqual(wrapper["fixed_location"], 9)
        self.assertFalse(
            any(site["request_kind"] == "2602" for site in source["call_sites"])
        )

    def test_reducer_requires_repeat_equivalent_process_health(self):
        reducer = (ROOT / "tools/summarize_xdj_rr_location9.py").read_text()
        self.assertIn("validate_health_pair(", reducer)

    def test_matrix_crosses_three_identities_and_both_setups(self):
        variants = self.declaration["variants"]
        self.assertEqual(len(variants), 6)
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

    def test_each_suite_has_current_and_stale_buffer_controls(self):
        expected_ids = [
            "location-1-first-current",
            "location-2-first-current",
            "location-9-second-current",
            "location-1-first-render-stale-9",
            "location-9-second-render-stale-1",
            "location-9-first-current",
        ]
        for entry in self.declaration["variants"]:
            suite = json.loads((CONFORMANCE / entry["suite"]).read_text())
            with self.subTest(variant=entry["id"]):
                self.assertEqual([case["id"] for case in suite["cases"]], expected_ids)
                self.assertTrue(all(case["request_kind"] == "0x2602" for case in suite["cases"]))
                self.assertTrue(all(case["fresh_connection"] for case in suite["cases"]))
                self.assertEqual(
                    [case["expect"] for case in suite["cases"]],
                    [{"outcome": "any", "total": 13}] * 6,
                )

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
