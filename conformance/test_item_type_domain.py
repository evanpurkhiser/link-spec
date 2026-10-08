import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
AUDIT = ROOT / "data/static-analysis/item-type-domain.json"
GENERATOR = ROOT / "tools/audit_item_type_domain.py"
GOLDENS = ROOT / "conformance/goldens/rekordbox-7.2.19"


class ItemTypeDomainTests(unittest.TestCase):
    def test_audit_regenerates_byte_identically(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "item-types.json"
            subprocess.run(
                ["python3", GENERATOR, "--goldens", GOLDENS, "--output", output],
                cwd=ROOT,
                check=True,
            )
            self.assertEqual(AUDIT.read_bytes(), output.read_bytes())

    def test_current_corpus_has_no_item_type_bits_above_low_16(self) -> None:
        audit = json.loads(AUDIT.read_text())
        self.assertEqual(2, audit["format"])
        self.assertEqual(281, audit["row_bearing_golden_file_count"])
        self.assertEqual(0, audit["nonzero_upper_16_type_count"])
        self.assertEqual(85, audit["unique_type_count"])
        self.assertEqual(0x2E04, audit["maximum_value"])
        self.assertEqual(0x2E04, max(item["lower_16"] for item in audit["types"]))
        self.assertTrue(all(item["upper_16"] == 0 for item in audit["types"]))

    def test_documentation_resolves_the_versioned_dysentery_unknown(self) -> None:
        audit = json.loads(AUDIT.read_text())
        crosswalk = (ROOT / "DYSENTERY_CROSSWALK.md").read_text()
        row_layout = (ROOT / "ROW_LAYOUT.md").read_text()

        for document in (crosswalk, row_layout):
            self.assertIn("item-type-domain.json", document)
            self.assertIn(f'{audit["representation_occurrence_count"]:,}', document)
            self.assertIn(str(audit["unique_type_count"]), document)
            self.assertIn("upper 16 bits", document)


if __name__ == "__main__":
    unittest.main()
