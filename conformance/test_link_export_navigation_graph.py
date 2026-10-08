import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GRAPH = ROOT / "data/static-analysis/link-export-navigation-graph.json"
QUERY_MAP = ROOT / "data/static-analysis/menu-database-query-map.json"
GENERATOR = ROOT / "tools/generate_link_export_navigation_graph.py"


class LinkExportNavigationGraphTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.graph = json.loads(GRAPH.read_text())
        cls.query_map = json.loads(QUERY_MAP.read_text())

    def test_every_database_path_family_and_request_is_present_once(self):
        expected = {
            family["id"]: family["requests"]
            for family in self.query_map["families"]
        }
        actual = {
            family["id"]: [request["kind"] for request in family["requests"]]
            for family in self.graph["families"]
        }
        self.assertEqual(expected, actual)

        kinds = [kind for requests in actual.values() for kind in requests]
        self.assertEqual(len(kinds), len(set(kinds)))
        self.assertEqual(95, len(kinds))

    def test_every_family_has_a_terminal_response_class(self):
        valid = {"list-buffer", "render", "direct", "error-or-no-reply"}
        for family in self.graph["families"]:
            with self.subTest(family=family["id"]):
                self.assertIn(family["response_mode"], valid)
                self.assertEqual(
                    "3000" if family["response_mode"] == "list-buffer" else None,
                    family["render_with"],
                )
                self.assertTrue(family["evidence"])

    def test_every_request_has_typed_declaration_signatures(self):
        valid_types = {"number", "string", "blob"}
        signatures = []
        for family in self.graph["families"]:
            for request in family["requests"]:
                self.assertTrue(request["declared_signatures"], request["kind"])
                for signature in request["declared_signatures"]:
                    with self.subTest(kind=request["kind"], signature=signature):
                        self.assertEqual(
                            signature["argument_count"],
                            len(signature["wire_types"]),
                        )
                        self.assertTrue(set(signature["wire_types"]) <= valid_types)
                        self.assertGreater(signature["declaration_count"], 0)
                        self.assertTrue(signature["origins"])
                        self.assertTrue(signature["examples"])
                        self.assertEqual(
                            signature["argument_count"],
                            len(signature["positions"]),
                        )
                        for index, position in enumerate(signature["positions"]):
                            self.assertEqual(index, position["index"])
                            self.assertGreaterEqual(position["literal_value_count"], 0)
                            self.assertLessEqual(
                                len(position["literal_examples"]),
                                position["literal_value_count"],
                            )
                        signatures.append(signature)

        self.assertEqual(
            self.graph["summary"]["declared_signature_count"],
            len(signatures),
        )

    def test_symbolic_position_evidence_is_preserved_without_literal_inference(self):
        requests = {
            request["kind"]: request
            for family in self.graph["families"]
            for request in family["requests"]
        }
        genre_root = requests["1001"]["declared_signatures"][0]
        self.assertEqual(["number:$context"], genre_root["positions"][0]["symbols"])
        self.assertEqual(["number:$sort"], genre_root["positions"][1]["symbols"])

        genre_tracks = requests["1301"]["declared_signatures"][0]
        self.assertIn("number:$fixture.genre.house", genre_tracks["positions"][2]["symbols"])
        self.assertIn(
            'case_item:{"case":"genres","row":0}',
            genre_tracks["positions"][2]["symbols"],
        )
        self.assertGreater(genre_tracks["positions"][3]["literal_value_count"], 0)

        render = requests["3000"]
        six = next(signature for signature in render["declared_signatures"] if signature["argument_count"] == 6)
        self.assertEqual(["number:$page_offset"], six["positions"][1]["symbols"])
        self.assertEqual(["number:$page_count"], six["positions"][2]["symbols"])

    def test_render_signatures_cover_arity_and_every_wrong_type_position(self):
        render = next(
            request
            for family in self.graph["families"]
            for request in family["requests"]
            if request["kind"] == "3000"
        )
        signatures = render["declared_signatures"]
        numeric_counts = {
            signature["argument_count"]
            for signature in signatures
            if set(signature["wire_types"]) <= {"number"}
        }
        self.assertEqual(set(range(33)), numeric_counts)

        for wire_type in ("string", "blob"):
            positions = {
                signature["wire_types"].index(wire_type)
                for signature in signatures
                if signature["argument_count"] == 8
                and signature["wire_types"].count(wire_type) == 1
            }
            self.assertEqual(set(range(8)), positions)

    def test_suite_corpus_fingerprint_matches_documented_domain(self):
        corpus = self.graph["suite_corpus"]
        coverage = (ROOT / "CONFORMANCE_COVERAGE.md").read_text()
        self.assertIn(
            f"{corpus['case_count']:,} case declarations in "
            f"{corpus['suite_file_count']} suite files",
            coverage,
        )
        self.assertRegex(corpus["sha256"], r"^[0-9a-f]{64}$")

    def test_every_edge_references_requests_in_its_family(self):
        for family in self.graph["families"]:
            requests = {request["kind"] for request in family["requests"]}
            for edge in family["edges"]:
                with self.subTest(family=family["id"], edge=edge):
                    self.assertIn(edge["from"], requests)
                    self.assertIn(edge["to"], requests)
                    self.assertTrue(edge["selection"])

    def test_configured_root_is_complete_and_targets_list_families(self):
        root = self.graph["configured_root"]
        self.assertEqual(list(range(1, 21)), [item["position"] for item in root])
        self.assertEqual(20, len({item["label"] for item in root}))
        list_requests = {
            request["kind"]
            for family in self.graph["families"]
            if family["response_mode"] == "list-buffer"
            for request in family["requests"]
        }
        self.assertTrue({item["request"] for item in root} <= list_requests)

    def test_recursive_families_have_self_edges(self):
        recursive = [family for family in self.graph["families"] if family["recursive"]]
        self.assertEqual(
            {"playlist", "hot_cue_bank_catalog"},
            {family["id"] for family in recursive},
        )
        for family in recursive:
            self.assertTrue(
                any(edge["from"] == edge["to"] for edge in family["edges"])
            )

    def test_regeneration_is_byte_identical(self):
        runtime = ROOT / "conformance/runtime"
        runtime.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=runtime) as directory:
            output = Path(directory) / GRAPH.name
            subprocess.run(
                [
                    str(ROOT / ".venv/bin/python"),
                    str(GENERATOR),
                    "--output",
                    str(output),
                ],
                cwd=ROOT,
                check=True,
                capture_output=True,
            )
            self.assertEqual(output.read_bytes(), GRAPH.read_bytes())

    def test_documented_counts_match_generated_authority(self):
        summary = self.graph["summary"]
        for name in ("CONFORMANCE_COVERAGE.md", "REKORDBOX_RESEARCH_GAPS.md"):
            text = (ROOT / name).read_text()
            with self.subTest(document=name):
                self.assertIn(
                    f"{summary['request_kind_count']} distinct request kinds"
                    if name == "CONFORMANCE_COVERAGE.md"
                    else f"all {summary['request_kind_count']} declared request kinds",
                    text,
                )
                self.assertIn(
                    f"across {summary['family_count']} database-path families",
                    text,
                )


if __name__ == "__main__":
    unittest.main()
