import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "data/database/link-export-schema.json"
REFERENCE = ROOT / "DATABASE_FIELD_REFERENCE.md"
GENERATOR = ROOT / "tools/generate_database_field_reference.py"
OPTIONS = Path("/mnt/documents/multimedia/djing/rekordbox/options.json")


class DatabaseFieldReferenceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = json.loads(SCHEMA.read_text())
        cls.tables = {table["name"]: table for table in cls.document["tables"]}
        cls.requests = {request["kind"]: request for request in cls.document["requests"]}

    def test_every_query_map_table_name_is_classified(self):
        query_map = json.loads(
            (ROOT / "data/static-analysis/menu-database-query-map.json").read_text()
        )
        expected = {
            table for family in query_map["families"] for table in family["tables"]
        }
        self.assertEqual(expected, set(self.tables))

    def test_runtime_and_alternate_names_are_explicit(self):
        self.assertEqual(
            {"djmdImage", "djmdLeftBuf", "djmdTrackSort"},
            {
                name
                for name, table in self.tables.items()
                if not table["physical_in_appsync_fixture"]
            },
        )

    def test_track_fields_needed_by_link_export_are_present(self):
        columns = {column["name"] for column in self.tables["djmdContent"]["columns"]}
        self.assertTrue(
            {
                "ID", "FolderPath", "FileNameL", "Title", "ArtistID", "AlbumID",
                "GenreID", "BPM", "Length", "TrackNo", "BitRate", "BitDepth",
                "Commnt", "FileType", "Rating", "ReleaseYear", "RemixerID",
                "LabelID", "OrgArtistID", "KeyID", "StockDate", "ColorID",
                "DJPlayCount", "AnalysisDataPath", "SampleRate", "ContentLink",
                "HotCueAutoLoad", "ServiceID",
            }.issubset(columns)
        )

    def test_tables_and_semantic_fields_link_to_concrete_request_kinds(self):
        self.assertEqual(["1000"], self.tables["djmdCategory"]["request_kinds"][:1])
        self.assertIn("3000", self.tables["djmdLeftBuf"]["request_kinds"])

        content = {
            column["name"]: column
            for column in self.tables["djmdContent"]["columns"]
        }
        self.assertEqual(
            ["1006", "1106", "1206"],
            content["BPM"]["evidence"]["semantic_request_kinds"],
        )
        self.assertEqual(
            ["1004", "1012", "1112", "2102"],
            content["FolderPath"]["evidence"]["semantic_request_kinds"],
        )
        self.assertEqual([], content["UUID"]["evidence"]["semantic_request_kinds"])

    def test_request_index_is_complete_unique_and_family_scoped(self):
        query_map = json.loads(
            (ROOT / "data/static-analysis/menu-database-query-map.json").read_text()
        )
        expected = {
            request.upper(): family["id"]
            for family in query_map["families"]
            for request in family["requests"]
        }
        self.assertEqual(95, len(self.document["requests"]))
        self.assertEqual(expected, {kind: row["family"] for kind, row in self.requests.items()})

        root = self.requests["1000"]
        self.assertEqual(["djmdCategory", "djmdMenuItems"], root["tables"])
        self.assertEqual(
            ["djmdCategory.Disable", "djmdCategory.Seq"],
            root["family_semantic_fields"],
        )

        genre = self.requests["1301"]
        self.assertEqual("genre_hierarchy", genre["family"])
        self.assertTrue(
            {"djmdContent.AlbumID", "djmdContent.ArtistID", "djmdContent.GenreID"}
            .issubset(genre["family_semantic_fields"])
        )

    def test_select_star_is_not_misrepresented_as_field_use(self):
        artist = self.tables["djmdArtist"]
        uuid = next(column for column in artist["columns"] if column["name"] == "UUID")
        self.assertTrue(uuid["evidence"]["returned_by_exact_select_star"])
        self.assertTrue(uuid["evidence"]["schema_only"])

    def test_secret_material_is_not_retained(self):
        source = self.document["sources"]["database"]
        self.assertNotIn("key", source)
        self.assertNotIn("options_sha256", source)
        self.assertNotIn(str(OPTIONS), SCHEMA.read_text())

    def test_primary_documentation_links_the_inverse_index(self):
        text = REFERENCE.read_text()
        self.assertIn("## Request-kind index", text)
        self.assertIn("family-level evidence", text)
        self.assertIn("95-row inverse request-kind index", (ROOT / "README.md").read_text())
        navigation = (ROOT / "LINK_EXPORT_NAVIGATION.md").read_text()
        self.assertIn("inverse database lookup", navigation)
        self.assertIn("family-level evidence", navigation)

    def test_regeneration_is_byte_identical(self):
        runtime = ROOT / "conformance/runtime"
        runtime.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=runtime) as directory:
            json_output = Path(directory) / SCHEMA.name
            markdown_output = Path(directory) / REFERENCE.name
            subprocess.run(
                [
                    str(ROOT / ".venv/bin/python"), str(GENERATOR),
                    "--options", str(OPTIONS),
                    "--json-output", str(json_output),
                    "--markdown-output", str(markdown_output),
                ],
                cwd=ROOT,
                check=True,
                capture_output=True,
            )
            self.assertEqual(SCHEMA.read_bytes(), json_output.read_bytes())
            self.assertEqual(REFERENCE.read_bytes(), markdown_output.read_bytes())


if __name__ == "__main__":
    unittest.main()
