import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT.parent / "dysentery"
INVENTORY = ROOT / "data/external/dysentery-docs.json"
GENERATOR = ROOT / "tools/inventory_dysentery_docs.py"
CROSSWALK = ROOT / "DYSENTERY_CROSSWALK.md"


class DysenteryCrosswalkTests(unittest.TestCase):
    def test_inventory_regenerates_byte_identically(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "inventory.json"
            subprocess.run(
                ["python3", GENERATOR, "--source", SOURCE, "--output", output],
                cwd=ROOT,
                check=True,
            )
            self.assertEqual(INVENTORY.read_bytes(), output.read_bytes())

    def test_inventory_covers_every_current_guide_document(self) -> None:
        inventory = json.loads(INVENTORY.read_text())
        actual = {item["path"] for item in inventory["documents"]}
        docs_root = SOURCE / "doc/modules/ROOT"
        expected = {
            str(path.relative_to(SOURCE))
            for path in (docs_root / "nav.adoc", *(docs_root / "pages").glob("*.adoc"))
        }

        self.assertEqual("f62a24ba947f9db4c1553bb2dc3ba76de1fecbb4", inventory["source"]["commit"])
        self.assertEqual(14, inventory["document_count"])
        self.assertEqual(expected, actual)
        for document in inventory["documents"]:
            path = SOURCE / document["path"]
            self.assertEqual(document["size"], path.stat().st_size)
            self.assertEqual(document["sha256"], hashlib.sha256(path.read_bytes()).hexdigest())
            if document["path"].endswith(".adoc") and "/pages/" in document["path"]:
                self.assertTrue(document["headings"])

    def test_crosswalk_references_only_real_pinned_paths_and_covers_all_pages(self) -> None:
        inventory = json.loads(INVENTORY.read_text())
        crosswalk = CROSSWALK.read_text()
        for document in inventory["documents"]:
            self.assertIn(f'`{document["path"]}`', crosswalk)
            self.assertTrue((SOURCE / document["path"]).is_file())

        self.assertNotIn("pages/dbserver/", crosswalk)
        self.assertIn("Primary Link Export", crosswalk)
        self.assertIn("Separate protocol", crosswalk)
        self.assertIn("data/external/dysentery-docs.json", crosswalk)


if __name__ == "__main__":
    unittest.main()
