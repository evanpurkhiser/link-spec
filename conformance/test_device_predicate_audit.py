import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
TOOL = ROOT / "tools/audit_device_predicates.py"
BINARY = (
    ROOT.parent
    / "artifacts/rekordbox/7.2.19/extracted/app-root/rekordbox.app"
    / "Contents/MacOS/rekordbox"
)
REPORT = ROOT / "data/static-analysis/device-predicate-audit.json"
MARKDOWN = ROOT / "data/static-analysis/device-predicate-audit.md"
ARM64_REPORT = ROOT / "data/static-analysis/device-predicate-audit-arm64.json"
ARM64_MARKDOWN = ROOT / "data/static-analysis/device-predicate-audit-arm64.md"
PYTHON = ROOT / ".venv/bin/python"


class DevicePredicateAuditTests(unittest.TestCase):
    def test_checked_report_has_the_complete_pinned_inventory(self) -> None:
        report = json.loads(REPORT.read_text())

        self.assertEqual(23, report["summary"]["target_count"])
        self.assertEqual(67, report["summary"]["direct_reference_count"])
        self.assertEqual(5, report["summary"]["database_serving_reference_count"])
        self.assertEqual(str(BINARY), report["binary"]["path"])

        arm64 = json.loads(ARM64_REPORT.read_text())
        self.assertEqual(23, arm64["summary"]["target_count"])
        self.assertEqual(68, arm64["summary"]["direct_reference_count"])
        self.assertEqual(6, arm64["summary"]["database_serving_reference_count"])
        self.assertEqual("arm64", arm64["binary"]["architecture"])
        self.assertEqual(str(BINARY), arm64["binary"]["path"])
        self.assertIn("x86_64-only behavior", arm64["method"]["limits"])
        self.assertIn("direct ARM64 callers", ARM64_MARKDOWN.read_text())
        self.assertIn("pinned ARM64 text slice", ARM64_MARKDOWN.read_text())

        deltas = [
            (x86["id"], x86["direct_reference_count"], arm["direct_reference_count"])
            for x86, arm in zip(report["targets"], arm64["targets"])
            if x86["direct_reference_count"] != arm["direct_reference_count"]
            or x86["database_serving_reference_count"]
            != arm["database_serving_reference_count"]
        ]
        self.assertEqual([("new-cdj-supported", 1, 2)], deltas)

    def test_relative_reproduction_is_byte_identical(self) -> None:
        relative_binary = BINARY.relative_to(ROOT.parent)
        with tempfile.TemporaryDirectory() as directory:
            generated_json = Path(directory) / "audit.json"
            generated_markdown = Path(directory) / "audit.md"
            subprocess.run(
                [
                    PYTHON,
                    TOOL,
                    relative_binary,
                    "--json",
                    generated_json,
                    "--markdown",
                    generated_markdown,
                ],
                cwd=ROOT.parent,
                check=True,
                capture_output=True,
                text=True,
            )

            self.assertEqual(REPORT.read_bytes(), generated_json.read_bytes())
            self.assertEqual(MARKDOWN.read_bytes(), generated_markdown.read_bytes())

    def test_arm64_reproduction_is_byte_identical(self) -> None:
        relative_binary = BINARY.relative_to(ROOT.parent)
        with tempfile.TemporaryDirectory() as directory:
            generated_json = Path(directory) / "audit-arm64.json"
            generated_markdown = Path(directory) / "audit-arm64.md"
            subprocess.run(
                [
                    PYTHON,
                    TOOL,
                    relative_binary,
                    "--architecture",
                    "arm64",
                    "--json",
                    generated_json,
                    "--markdown",
                    generated_markdown,
                ],
                cwd=ROOT.parent,
                check=True,
                capture_output=True,
                text=True,
            )

            self.assertEqual(ARM64_REPORT.read_bytes(), generated_json.read_bytes())
            self.assertEqual(
                ARM64_MARKDOWN.read_bytes(),
                generated_markdown.read_bytes(),
            )

    def test_documentation_states_the_reproducibility_contract(self) -> None:
        document = (ROOT / "DEVICE_PREDICATE_AUDIT.md").read_text()
        sources = (ROOT / "SOURCES.md").read_text()
        gaps = (ROOT / "REKORDBOX_RESEARCH_GAPS.md").read_text()

        self.assertIn("relative invocation", document)
        self.assertIn("compares them byte for byte", document)
        self.assertIn("five database-serving references", document)
        self.assertIn("Windows PE evidence boundary", document)
        self.assertIn("No Mach-O address or call count is transferred to the PE", document)
        self.assertIn("complete 382-row Windows oracle", document)
        self.assertIn("byte-reproducible dual-slice inventory", sources)
        self.assertIn("duplicate ARM64 compatibility call", sources)
        self.assertIn("Windows static device-predicate ownership", gaps)
        self.assertIn("bounded static gap", gaps)


if __name__ == "__main__":
    unittest.main()
