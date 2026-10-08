import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VOCABULARY = ROOT / "data/static-analysis/link-export-request-vocabulary.json"
INDEX = ROOT / "data/static-analysis/control-mutation-command-map.json"
REFERENCE = ROOT / "docs/CONTROL_AND_MUTATION_REFERENCE.md"
GENERATOR = ROOT / "tools/generate_control_mutation_reference.py"


def in_scope(command):
    if command["direction"] != "request":
        return False
    kind = int(command["kind"], 16)
    return 0x3000 <= kind <= 0x3FFF or (
        0x2000 <= kind <= 0x2FFF and kind & 0xFF in {0x05, 0x07}
    )


class ControlMutationReferenceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = json.loads(INDEX.read_text())
        cls.vocabulary = json.loads(VOCABULARY.read_text())

    def test_domain_exactly_matches_the_vocabulary(self):
        expected = {
            command["kind"] for command in self.vocabulary["commands"] if in_scope(command)
        }
        actual = {command["kind"] for command in self.document["commands"]}
        self.assertEqual(expected, actual)
        self.assertEqual(len(actual), self.document["summary"]["command_count"])

    def test_every_command_preserves_server_route_and_client_provenance(self):
        for command in self.document["commands"]:
            self.assertTrue(command["server"]["dispatcher"])
            self.assertTrue(command["effect_class"])
            client = command["xdj_rr_client"]
            self.assertEqual(len(client["call_sites"]), client["direct_call_site_count"])
            for site in client["call_sites"]:
                self.assertTrue((ROOT.parent / site["source"]).is_file())
                self.assertGreater(site["line"], 0)

    def test_known_database_mutations_are_explicit(self):
        commands = {command["kind"]: command for command in self.document["commands"]}
        self.assertEqual(
            ["djmdContent.Rating"], commands["2107"]["server"]["dependencies"]["database"]
        )
        self.assertEqual(
            ["djmdContent.BPM"], commands["2507"]["server"]["dependencies"]["database"]
        )
        self.assertEqual("4000", commands["2605"]["server"]["reply_kind"])
        self.assertEqual("rejected", commands["2207"]["effect_class"])
        self.assertEqual("mutation-or-state-write", commands["3207"]["effect_class"])
        self.assertEqual("recognized-static-route", commands["2205"]["effect_class"])

    def test_rejected_and_log_only_commands_are_not_described_as_mutations(self):
        for command in self.document["commands"]:
            if command["coverage"] == "rekordbox-static-rejected":
                self.assertEqual("rejected", command["effect_class"])
                self.assertTrue(command["server"]["rejection_reason"])
            if command["coverage"] == "rekordbox-recognized-log-only":
                self.assertEqual("recognized-log-only", command["effect_class"])

    def test_primary_documents_link_the_reference_and_live_boundary(self):
        expected = {
            "docs/README.md": "CONTROL_AND_MUTATION_REFERENCE.md",
            "docs/PROTOCOL_REFERENCE.md": "complete adjacent control plane",
            "docs/STATIC_ANALYSIS.md": "control-mutation-command-map.json",
            "docs/SOURCES.md": "Complete generated join for 54 control/mutation commands",
            "docs/CLEANUP.md": "require no cleanup",
        }
        for name, fragment in expected.items():
            with self.subTest(document=name):
                self.assertIn(fragment, (ROOT / name).read_text())

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
