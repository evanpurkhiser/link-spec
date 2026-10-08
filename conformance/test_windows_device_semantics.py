import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
AUDIT = ROOT / "data/static-analysis/windows/device-semantic-audit.json"


class WindowsDeviceSemanticTests(unittest.TestCase):
    def setUp(self) -> None:
        self.audit = json.loads(AUDIT.read_text())

    def test_source_and_complete_runtime_function_domain_are_pinned(self) -> None:
        self.assertEqual(1, self.audit["format"])
        self.assertEqual(
            "c9ed23e974c51c75e2ec069fbd2679a3dbe606be9e79e9cbbd13d6418ab11c37",
            self.audit["source"]["sha256"],
        )
        self.assertEqual(174813, self.audit["source"]["runtime_function_count"])

    def test_bare_xdj_prefix_has_one_direct_literal_reference(self) -> None:
        self.assertEqual(37, len(self.audit["model_literals"]["XDJ"]))
        self.assertEqual(34, len(self.audit["model_literals"]["XDJ-AZ"]))
        self.assertEqual(37, len(self.audit["model_literal_references"]))

        bare = [
            reference
            for reference in self.audit["model_literal_references"]
            if reference["literal"] == "XDJ"
        ]
        self.assertEqual(1, len(bare))
        self.assertEqual("0x142381659", bare[0]["address"])
        self.assertEqual("0x1423815c0", bare[0]["function_start"])

    def test_compatibility_signature_has_only_the_two_known_copies(self) -> None:
        matches = self.audit["compatibility_semantic_signature"]["matches"]
        self.assertEqual(2, len(matches))
        self.assertEqual(
            {
                (
                    "0x14227e2d2",
                    "0x14227e2d7",
                    "0x14227e2dc",
                    "0x14227e2e1",
                    "0x14227e2e6",
                    "0x14227e2ee",
                ),
                (
                    "0x14238cb54",
                    "0x14238cb59",
                    "0x14238cb5e",
                    "0x14238cb63",
                    "0x14238cb68",
                    "0x14238cb6f",
                ),
            },
            {tuple(match["instruction_addresses"]) for match in matches},
        )

    def test_documentation_states_result_and_boundary(self) -> None:
        predicate = (ROOT / "DEVICE_PREDICATE_AUDIT.md").read_text()
        gaps = (ROOT / "REKORDBOX_RESEARCH_GAPS.md").read_text()
        for document in (predicate, gaps):
            self.assertIn("device-semantic-audit.json", document)
            self.assertIn("174,813", document)
            self.assertIn("exactly twice", document)


if __name__ == "__main__":
    unittest.main()
