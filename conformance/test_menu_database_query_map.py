import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
QUERY_MAP = ROOT / "data/static-analysis/menu-database-query-map.json"
GENERATOR = ROOT / "tools/generate_menu_database_query_map.py"
SUITES = ROOT / "conformance/suites"


def declared_request_kinds():
    def normalize(value):
        if isinstance(value, int):
            return f"{value:04X}"

        return value.removeprefix("0x").upper()

    return {
        normalize(case["request_kind"])
        for path in SUITES.rglob("*.json")
        for case in json.loads(path.read_text())["cases"]
    }


class MenuDatabaseQueryMapTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = json.loads(QUERY_MAP.read_text())
        cls.families = cls.document["families"]

    def test_every_declared_request_kind_has_exactly_one_classification(self):
        classified = [
            request
            for family in self.families
            for request in family["requests"]
        ]

        self.assertEqual(len(classified), len(set(classified)))
        self.assertEqual(set(classified), declared_request_kinds())

    def test_every_family_has_query_semantics_and_evidence(self):
        for family in self.families:
            with self.subTest(family=family["id"]):
                self.assertTrue(family["operation"])
                self.assertTrue(family["predicate"])
                self.assertTrue(family["ordering"])
                self.assertTrue(family["result"])
                self.assertTrue(family["evidence"])

    def test_empty_table_sets_are_explicit_non_database_paths(self):
        for family in self.families:
            if family["tables"]:
                continue

            self.assertEqual(family["operation"], "no_database_builder")

    def test_database_paths_name_tables(self):
        for family in self.families:
            if family["operation"] == "no_database_builder":
                continue

            self.assertTrue(family["tables"], family["id"])

    def test_regeneration_is_byte_identical(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / QUERY_MAP.name
            subprocess.run(
                ["python3", str(GENERATOR), "--output", str(output)],
                cwd=ROOT,
                check=True,
                capture_output=True,
            )
            self.assertEqual(output.read_bytes(), QUERY_MAP.read_bytes())


if __name__ == "__main__":
    unittest.main()
