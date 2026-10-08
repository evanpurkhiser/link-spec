import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "data/item-type-reference.json"
MARKDOWN = ROOT / "docs/ITEM_TYPE_REFERENCE.md"
DOMAIN = ROOT / "data/static-analysis/item-type-domain.json"
GENERATOR = ROOT / "tools/generate_item_type_reference.py"


class ItemTypeReferenceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reference = json.loads(REFERENCE.read_text())
        cls.types = {item["value"]: item for item in cls.reference["types"]}

    def test_reference_exactly_matches_the_audited_domain(self):
        domain = json.loads(DOMAIN.read_text())
        expected = {item["value"]: item["occurrences"] for item in domain["types"]}
        actual = {value: item["occurrences"] for value, item in self.types.items()}
        self.assertEqual(expected, actual)
        self.assertEqual(85, len(actual))
        self.assertEqual(51148, sum(actual.values()))

    def test_every_represented_type_has_resolved_semantics_and_provenance(self):
        self.assertEqual(0, self.reference["summary"]["unresolved_type_count"])
        for item in self.types.values():
            self.assertTrue(item["meaning"])
            self.assertGreater(item["source_file_count"], 0)
            self.assertTrue(item["source_files"])
            self.assertTrue(item["samples"])

    def test_track_composites_are_secondary_over_title(self):
        composites = [item for item in self.types.values() if item["secondary_type"]]
        self.assertEqual(23, len(composites))
        self.assertTrue(all(item["primary_type"] == 4 for item in composites))
        self.assertEqual("key secondary over title or track primary", self.types[0x0F04]["meaning"])
        self.assertEqual("BPM secondary over title or track primary", self.types[0x0D04]["meaning"])
        for item_type in (0x0D04, 0x0F04):
            self.assertTrue(
                any(" - " in sample["secondary_text"] for sample in self.types[item_type]["samples"])
            )

    def test_special_and_modelled_types_are_named(self):
        expected = {
            0x36: "composer artist lookup",
            0x37: "lyricist",
            0x4A: "My Tag group or leaf",
            0x4F: "DeliveryControl and ISRC",
            0x8C: "menu choice: Date Added",
            0x96: "menu choice: Comments",
            0x97: "menu choice: DJ Play Count",
            0xA1: "sort choice: Default",
            0xA2: "sort choice: Alphabet",
        }
        self.assertEqual(expected, {value: self.types[value]["meaning"] for value in expected})

    def test_primary_indexes_link_the_reference(self):
        references = {
            ROOT / "README.md": "docs/ITEM_TYPE_REFERENCE.md",
            ROOT / "docs/ROW_LAYOUT.md": "ITEM_TYPE_REFERENCE.md",
            ROOT / "docs/SOURCES.md": "ITEM_TYPE_REFERENCE.md",
        }

        for path, reference in references.items():
            self.assertIn(reference, path.read_text())

    def test_regeneration_is_byte_identical(self):
        runtime = ROOT / "conformance/runtime"
        runtime.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=runtime) as directory:
            json_output = Path(directory) / REFERENCE.name
            markdown_output = Path(directory) / MARKDOWN.name
            subprocess.run(
                [
                    str(ROOT / ".venv/bin/python"),
                    str(GENERATOR),
                    "--json-output", str(json_output),
                    "--markdown-output", str(markdown_output),
                ],
                cwd=ROOT,
                check=True,
                capture_output=True,
            )
            self.assertEqual(REFERENCE.read_bytes(), json_output.read_bytes())
            self.assertEqual(MARKDOWN.read_bytes(), markdown_output.read_bytes())


if __name__ == "__main__":
    unittest.main()
