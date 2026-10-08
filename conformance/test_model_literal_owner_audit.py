import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
MACHO = (
    ROOT.parent
    / "artifacts/rekordbox/7.2.19/extracted/app-root/rekordbox.app/Contents/MacOS/rekordbox"
)
WINDOWS_AUDIT = ROOT / "data/static-analysis/windows/device-semantic-audit.json"
AUDIT = ROOT / "data/static-analysis/model-literal-owner-audit.json"
GENERATOR = ROOT / "tools/audit_model_literal_owners.py"


class ModelLiteralOwnerAuditTests(unittest.TestCase):
    def test_audit_regenerates_byte_identically(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "audit.json"
            subprocess.run(
                [
                    sys.executable,
                    GENERATOR,
                    MACHO,
                    WINDOWS_AUDIT,
                    "--output",
                    output,
                ],
                cwd=ROOT,
                check=True,
            )
            self.assertEqual(AUDIT.read_bytes(), output.read_bytes())

    def test_symbol_rich_slice_classifies_every_direct_literal_reference(self) -> None:
        audit = json.loads(AUDIT.read_text())
        references = audit["macho"]["references"]
        self.assertEqual(30, len(references))
        self.assertEqual(
            {
                "application-ui": 2,
                "audio-device": 19,
                "controller-mapping": 6,
                "database-serving": 2,
                "other": 1,
            },
            audit["macho"]["scope_counts"],
        )

        database = [
            reference
            for reference in references
            if reference["owner_scope"] == "database-serving"
        ]
        self.assertEqual(["XDJ", "XDJ-AZ"], [item["literal"] for item in database])
        self.assertEqual(
            {"PSvDBMain::isAIO(unsigned char)"},
            {name for item in database for name in item["owner_demangled"]},
        )

    def test_windows_companion_counts_are_bound(self) -> None:
        windows = json.loads(AUDIT.read_text())["windows"]
        self.assertEqual(37, windows["reference_count"])
        self.assertEqual(1, windows["bare_xdj_reference_count"])
        self.assertEqual(36, windows["xdj_az_reference_count"])

    def test_documentation_retains_result_and_boundary(self) -> None:
        predicate = (ROOT / "DEVICE_PREDICATE_AUDIT.md").read_text()
        gaps = (ROOT / "REKORDBOX_RESEARCH_GAPS.md").read_text()
        for document in (predicate, gaps):
            self.assertIn("model-literal-owner-audit.json", document)
            self.assertIn("19 audio-device", document)
            self.assertIn("6 controller", document)
            self.assertIn("exactly 2 database-serving", document)


if __name__ == "__main__":
    unittest.main()
