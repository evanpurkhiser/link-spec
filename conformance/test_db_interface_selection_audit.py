import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
BINARY = Path(
    "../artifacts/rekordbox/7.2.19/extracted/app-root/rekordbox.app/Contents/MacOS/rekordbox"
)
TOOL = ROOT / "tools/audit_db_interface_selection.py"
CANONICAL_JSON = ROOT / "data/static-analysis/db-interface-selection.json"
CANONICAL_MARKDOWN = ROOT / "data/static-analysis/db-interface-selection.md"


class DatabaseInterfaceSelectionAuditTest(unittest.TestCase):
    def test_canonical_selection_evidence(self) -> None:
        report = json.loads(CANONICAL_JSON.read_text())
        interfaces = report["interfaces"]

        self.assertEqual(interfaces["appsync"]["size"], 0x328)
        self.assertEqual(interfaces["master"]["size"], 0x328)
        self.assertEqual(interfaces["appsync"]["reference_count"], 6)
        self.assertEqual(interfaces["master"]["reference_count"], 3)
        self.assertTrue(
            any(
                "SetSharedDBInfo" in " ".join(reference["owner_symbols"])
                for reference in interfaces["appsync"]["references"]
            )
        )
        self.assertFalse(
            any(
                any(symbol.startswith("__ZN9PSvDBMain") for symbol in reference["owner_symbols"])
                for reference in interfaces["master"]["references"]
            )
        )
        self.assertEqual(
            {
                reference["owner_symbols"][0]
                for reference in interfaces["master"]["references"]
            },
            {
                "__ZN20FilterSettingManagerC2ERKN4juce6StringEP9PSvDBMain9RbDBIndex",
                "__ZN20FilterSettingManager10setDBIndexE9RbDBIndex",
                "__ZN11TrackFilterC2E9RbDBIndexRKN4juce10OwnedArrayI15FilterConditionNS1_20DummyCriticalSectionEEEP9PSvDBMain",
            },
        )

    def test_regeneration_is_byte_identical(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            subprocess.run(
                [
                    str(ROOT / ".venv/bin/python"),
                    str(TOOL),
                    str(BINARY),
                    "--json",
                    str(output / "report.json"),
                    "--markdown",
                    str(output / "report.md"),
                ],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertEqual((output / "report.json").read_bytes(), CANONICAL_JSON.read_bytes())
            self.assertEqual((output / "report.md").read_bytes(), CANONICAL_MARKDOWN.read_bytes())


if __name__ == "__main__":
    unittest.main()
