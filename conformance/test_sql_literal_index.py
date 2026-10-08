import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "data/static-analysis/sql-literal-index.json"
REFERENCE = ROOT / "docs/SQL_LITERAL_INDEX.md"
GENERATOR = ROOT / "tools/generate_sql_literal_index.py"


class SqlLiteralIndexTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = json.loads(INDEX.read_text())

    def test_summary_matches_index(self):
        summary = self.document["summary"]
        literals = self.document["literals"]
        self.assertEqual(len(literals), summary["unique_literal_count"])
        self.assertEqual(
            sum(item["occurrence_count"] for item in literals),
            summary["occurrence_count"],
        )
        self.assertEqual(
            len(list((ROOT / "data/static-analysis").rglob("*.disasm.txt"))),
            summary["scanned_source_count"],
        )

    def test_every_occurrence_is_source_bound(self):
        source_hashes = {
            source["path"]: source["sha256"]
            for source in self.document["scanned_sources"]
        }
        for literal in self.document["literals"]:
            self.assertEqual(len(literal["occurrences"]), literal["occurrence_count"])
            for occurrence in literal["occurrences"]:
                path = ROOT / occurrence["source"]
                self.assertIn(occurrence["source"], source_hashes)
                self.assertTrue(path.is_file())
                self.assertGreater(occurrence["line"], 0)
                self.assertRegex(occurrence["address"], r"^0x[0-9a-f]+$")
                self.assertTrue(occurrence["function"])

    def test_required_link_export_literals_are_present(self):
        literals = {item["literal"] for item in self.document["literals"]}
        expected = {
            "select ID from djmdSort where rb_local_deleted = 0 and (Disable & 2) = 2",
            "select MenuItemID, Disable from djmdCategory where rb_local_deleted = 0",
            "select * from djmdContent where rb_local_deleted = 0 and ID = %lu",
            "select FileType, SampleRate from djmdContent where rb_local_deleted = 0",
            "select * from djmdHotCueBankList where rb_local_deleted = 0",
        }
        self.assertTrue(expected.issubset(literals))
        self.assertFalse(any("ERROR" in literal for literal in literals))

    def test_fragments_are_not_presented_as_complete_queries(self):
        fragments = {
            item["literal"]
            for item in self.document["literals"]
            if item["classification"] == "fragment"
        }
        self.assertIn("select", {fragment.lower() for fragment in fragments})
        self.assertIn("Interpretation boundary", REFERENCE.read_text())

    def test_regeneration_is_byte_identical(self):
        runtime = ROOT / "conformance/runtime"
        runtime.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=runtime) as directory:
            json_output = Path(directory) / INDEX.name
            markdown_output = Path(directory) / REFERENCE.name
            subprocess.run(
                [
                    str(ROOT / ".venv/bin/python"),
                    str(GENERATOR),
                    "--json-output",
                    str(json_output),
                    "--markdown-output",
                    str(markdown_output),
                ],
                cwd=ROOT,
                check=True,
                capture_output=True,
            )
            self.assertEqual(json_output.read_bytes(), INDEX.read_bytes())
            self.assertEqual(markdown_output.read_bytes(), REFERENCE.read_bytes())


if __name__ == "__main__":
    unittest.main()
