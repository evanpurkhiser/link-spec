import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "data/device-behavior-matrix.json"
GENERATOR = ROOT / "tools/generate_device_behavior_matrix.py"


class DeviceBehaviorMatrixTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matrix = json.loads(MATRIX.read_text())

    def test_ordinary_identity_and_suite_domains_are_complete(self):
        ordinary = self.matrix["ordinary_identity_matrix"]
        self.assertEqual(8, len(ordinary["identities"]))
        self.assertEqual(
            {"full", "legacy", "device-capabilities", "compatibility"},
            {item["suite"] for item in ordinary["suite_equivalence"]},
        )
        self.assertTrue(all(item["behavior_equal"] for item in ordinary["suite_equivalence"]))
        for identity in ordinary["identities"]:
            self.assertEqual(
                {"full", "legacy", "device-capabilities", "compatibility"},
                set(identity["suites"]),
            )

    def test_only_display_has_a_status_backed_identity_difference(self):
        surfaces = {
            item["surface"]: item["classification"]
            for item in self.matrix["status_backed_surfaces"]
        }
        self.assertEqual("different", surfaces.pop("display-song-info"))
        self.assertEqual(
            {"equal-after-context-normalization"},
            set(surfaces.values()),
        )
        self.assertEqual(
            {
                "play-song-info",
                "delivery-and-no-builder",
                "hot-cue-bank-catalog",
                "hot-cue-bank-getters",
                "hot-cue-bank-extended-setter",
                "hot-cue-bank-legacy-setter",
            },
            set(surfaces),
        )

    def test_serving_dimensions_remain_independent(self):
        dimensions = {item["id"]: item for item in self.matrix["serving_dimensions"]}
        self.assertEqual(
            {
                "keepalive-identity",
                "setup-width",
                "requester-player",
                "menu-location",
                "packed-track-type",
                "status-model-classification",
                "root-capability-mask",
                "content-compatibility",
            },
            set(dimensions),
        )
        self.assertIn("12 or 16 arguments", dimensions["setup-width"]["effect"])
        self.assertIn("compatibility-failure bit 0", dimensions["content-compatibility"]["effect"])
        self.assertIn("not a value inferred from model identity", dimensions["root-capability-mask"]["boundary"])

    def test_static_boundary_names_three_serving_decisions(self):
        decisions = self.matrix["static_predicate_boundary"]["decisions"]
        self.assertEqual(
            {
                "PSvDBMain::isAIO(player)",
                "PSvDBMain::clearAIOMap(player)",
                "DsqlContent_GetNewCDJSupported(content_id)",
            },
            {decision["predicate"] for decision in decisions},
        )

    def test_genuine_cdj_2000nexus_matrix_is_repeat_complete(self):
        matrix = self.matrix["genuine_cdj_2000nexus"]["matrix"]
        self.assertEqual(13, matrix["completed_variants"])
        self.assertEqual(13, matrix["repeat_verified_variants"])
        self.assertEqual(13, matrix["semantic_reference_matches"])

    def test_documents_expose_surface_and_dimension_boundaries(self):
        oracle = (ROOT / "docs/DEVICE_MATRIX_ORACLE.md").read_text()
        compatibility = (ROOT / "docs/DEVICE_COMPATIBILITY.md").read_text()
        gaps = " ".join((ROOT / "docs/REKORDBOX_RESEARCH_GAPS.md").read_text().split())
        self.assertIn("## Serving dimensions", oracle)
        self.assertIn("seven completed status-backed surfaces", oracle)
        self.assertIn("packed Hot Cue extended setter", compatibility)
        self.assertIn("packed Hot Cue legacy setter", compatibility)
        self.assertIn("seven status-backed serving surfaces", gaps)
        self.assertIn("eight separate serving dimensions", gaps)

    def test_regeneration_is_byte_identical(self):
        runtime = ROOT / "conformance/runtime"
        runtime.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=runtime) as directory:
            output = Path(directory) / MATRIX.name
            subprocess.run(
                [str(ROOT / ".venv/bin/python"), str(GENERATOR), "--output", str(output)],
                cwd=ROOT,
                check=True,
                capture_output=True,
            )
            self.assertEqual(output.read_bytes(), MATRIX.read_bytes())


if __name__ == "__main__":
    unittest.main()
