import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
LAB = ROOT.parent
SUITES = ROOT / "suites"
TARGET = SUITES / "generated/render-override-controls.json"
STATIC = LAB / "data/static-analysis/render-override-controls.json"
DISASSEMBLY = LAB / "data/static-analysis/render-override-controls.disasm.txt"
BINARY = (
    LAB.parent
    / "artifacts/rekordbox/7.2.19/extracted/app-root/rekordbox.app/Contents/MacOS/rekordbox"
)
CONTROL = [0, 8, 12, 1, 2]


class RenderOverrideControlTests(unittest.TestCase):
    def test_historical_suites_omit_override_numeric_boundaries(self) -> None:
        gates = set()
        selectors = set()
        for path in sorted(SUITES.rglob("*.json")):
            if path == TARGET or path.is_relative_to(
                SUITES / "generated/render-argument-types"
            ):
                continue

            suite = json.loads(path.read_text())
            default = suite["defaults"].get("render_arguments", [])
            for case in suite["cases"]:
                tail = case.get("render_arguments", default)
                if len(tail) != 5:
                    continue
                gates.add(json.dumps(tail[3], sort_keys=True))
                selectors.add(json.dumps(tail[4], sort_keys=True))

        self.assertLessEqual(gates, {"0", "1"})
        self.assertNotIn("1", selectors)
        self.assertNotIn("18", selectors)
        self.assertNotIn('"0x00010002"', selectors)
        self.assertNotIn('"0xffffffff"', selectors)

    def test_suite_covers_gate_and_selector_width_boundaries(self) -> None:
        suite = json.loads(TARGET.read_text())
        self.assertEqual("track-render-override-controls", suite["name"])
        self.assertEqual(17, len(suite["cases"]))
        self.assertEqual(
            {
                0,
                1,
                2,
                "0x7fffffff",
                "0x80000000",
                "0xffffffff",
            },
            {
                case["render_arguments"][3]
                for case in suite["cases"]
                if case["id"] == "control" or case["id"].startswith("override-gate-")
            },
        )
        self.assertEqual(
            {
                0,
                1,
                2,
                14,
                17,
                18,
                "0x000000ff",
                "0x00000100",
                "0x00010002",
                "0x7fffffff",
                "0x80000000",
                "0xffffffff",
            },
            {
                case["render_arguments"][4]
                for case in suite["cases"]
                if case["id"] == "control"
                or case["id"].startswith("override-selector-")
            },
        )

    def test_each_case_changes_exactly_one_control_field(self) -> None:
        suite = json.loads(TARGET.read_text())
        for case in suite["cases"]:
            with self.subTest(case=case["id"]):
                self.assertEqual("0x1004", case["request_kind"])
                self.assertTrue(case["fresh_connection"])
                self.assertEqual(8, case["page_size"])
                self.assertEqual({"outcome": "any"}, case["expect"])
                self.assertEqual(5, len(case["render_arguments"]))
                differences = [
                    index
                    for index, (actual, normal) in enumerate(
                        zip(case["render_arguments"], CONTROL), start=4
                    )
                    if actual != normal
                ]
                if case["id"] == "control":
                    self.assertEqual([], differences)
                elif case["id"].startswith("override-gate-"):
                    self.assertEqual([7], differences)
                else:
                    self.assertEqual([8], differences)

    def test_static_audit_pins_split_selector_width(self) -> None:
        report = json.loads(STATIC.read_text())
        self.assertEqual(
            hashlib.sha256(BINARY.read_bytes()).hexdigest(),
            report["executable_sha256"],
        )
        self.assertEqual(24, report["validated_instruction_count"])
        findings = report["findings"]
        self.assertEqual(32, findings["argument_7_read_width_bits"])
        self.assertTrue(findings["argument_7_canonicalized_to_boolean"])
        self.assertEqual(32, findings["argument_8_read_width_bits"])
        self.assertTrue(findings["icon_dispatch_uses_low_8_bits"])
        self.assertTrue(findings["subcategory_dispatch_uses_full_32_bits"])
        self.assertEqual([2, 17], findings["subcategory_valid_interval_inclusive"])

        disassembly = DISASSEMBLY.read_text()
        self.assertIn("setne     dl", disassembly)
        self.assertIn("movsx     edi, r14b", disassembly)
        self.assertIn("mov       edi, r14d", disassembly)
        self.assertIn("cmp       ebx, 0xf", disassembly)

    def test_docs_name_override_boundary_and_authority_status(self) -> None:
        documents = {
            "docs/PROTOCOL_REFERENCE.md": "Track render override controls",
            "docs/CONFORMANCE_COVERAGE.md": "Track render override controls",
            "docs/REKORDBOX_RESEARCH_GAPS.md": "render-override-controls",
            "docs/SOURCES.md": "Track render override controls",
            "docs/SECONDARY_COLUMNS.md": "high-word Artist lookalike",
            "docs/CLEANUP.md": "render-override-controls",
        }
        for name, fragment in documents.items():
            text = " ".join((LAB / name).read_text().split())
            with self.subTest(document=name):
                self.assertIn(fragment, text)


if __name__ == "__main__":
    unittest.main()
