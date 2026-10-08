import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCUMENT = ROOT / "docs/REQUEST_SHAPES.md"
GENERATOR = ROOT / "tools/generate_link_export_request_shapes.py"


class LinkExportRequestShapesTest(unittest.TestCase):
    def test_document_is_generated_byte_identically(self):
        runtime = ROOT / "conformance/runtime"
        runtime.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=runtime) as directory:
            output = Path(directory) / DOCUMENT.name
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
            self.assertEqual(output.read_bytes(), DOCUMENT.read_bytes())

    def test_document_contains_every_family_and_signature(self):
        import json

        graph = json.loads(
            (ROOT / "data/static-analysis/link-export-navigation-graph.json").read_text()
        )
        text = DOCUMENT.read_text()
        self.assertEqual(
            graph["summary"]["family_count"],
            sum(text.count(f"## `{family['id']}`") for family in graph["families"]),
        )
        self.assertEqual(
            graph["summary"]["declared_signature_count"],
            sum(
                len(request["declared_signatures"])
                for family in graph["families"]
                for request in family["requests"]
            ),
        )
        for family in graph["families"]:
            self.assertIn(f"## `{family['id']}`", text)
            for request in family["requests"]:
                self.assertIn(f"`0x{request['kind']}`", text)
        self.assertIn("Position evidence", text)
        self.assertIn("number:$context", text)
        self.assertIn("does not assign semantic names to literal-only positions", text)


if __name__ == "__main__":
    unittest.main()
