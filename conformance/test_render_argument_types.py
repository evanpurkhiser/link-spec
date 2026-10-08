import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
LAB = ROOT.parent
DECLARATION = ROOT / "data/render-argument-type-matrix.json"
SUITES = ROOT / "suites"
TARGET_ROOT = SUITES / "generated/render-argument-types"
GOLDEN_ROOT = ROOT / "goldens/rekordbox-7.2.19/xdj-rx3/render-argument-types"
STATIC = LAB / "data/static-analysis/render-argument-types-parser.json"
DISASSEMBLY = LAB / "data/static-analysis/render-argument-types-parser.disasm.txt"
BINARY = (
    LAB.parent
    / "artifacts/rekordbox/7.2.19/extracted/app-root/rekordbox.app/Contents/MacOS/rekordbox"
)
NAMES = (
    "context",
    "offset",
    "count",
    "reserved",
    "total",
    "category",
    "override-gate",
    "override-selector",
)
NORMAL = (
    {"number": "$context"},
    {"number": 0},
    {"number": 8},
    {"number": 0},
    {"number": 8},
    {"number": 12},
    {"number": 1},
    {"number": 0},
)


class RenderArgumentTypeTests(unittest.TestCase):
    def test_existing_suites_do_not_warm_tracks_then_send_wrong_typed_render(self) -> None:
        matches = []
        for path in sorted(SUITES.rglob("*.json")):
            if path.is_relative_to(TARGET_ROOT):
                continue

            cases = json.loads(path.read_text()).get("cases", [])
            for previous, case in zip(cases, cases[1:]):
                if case.get("request_kind") != "0x3000":
                    continue
                if previous.get("request_kind") != "0x1004":
                    continue
                arguments = case.get("arguments", [])
                if any("string" in value or "blob_hex" in value for value in arguments):
                    matches.append((str(path.relative_to(ROOT)), case["id"]))

        self.assertEqual([], matches)

    def test_matrix_crosses_every_position_with_both_variable_width_types(self) -> None:
        declaration = json.loads(DECLARATION.read_text())
        self.assertEqual(1, declaration["format"])
        self.assertEqual(8, declaration["position_count"])
        self.assertEqual(["string", "blob"], declaration["wire_types"])
        self.assertEqual(16, declaration["probe_count"])
        self.assertEqual(32, declaration["case_count"])
        self.assertEqual(
            [
                (position, name, wire_type)
                for position, name in enumerate(NAMES, start=1)
                for wire_type in ("string", "blob")
            ],
            [
                (probe["position"], probe["argument"], probe["wire_type"])
                for probe in declaration["probes"]
            ],
        )

    def test_each_probe_has_an_isolated_warm_list_and_one_substitution(self) -> None:
        declaration = json.loads(DECLARATION.read_text())
        for entry in declaration["probes"]:
            path = ROOT / entry["suite"]
            suite = json.loads(path.read_text())
            with self.subTest(probe=entry["id"]):
                self.assertEqual(2, len(suite["cases"]))
                warm, probe = suite["cases"]
                self.assertEqual("warm-track-list", warm["id"])
                self.assertEqual("0x1004", warm["request_kind"])
                self.assertTrue(warm["fresh_connection"])
                self.assertFalse(warm["render"])
                self.assertEqual({"outcome": "menu", "total": 8}, warm["expect"])

                self.assertEqual(entry["id"], probe["id"])
                self.assertEqual("0x3000", probe["request_kind"])
                self.assertFalse(probe["render"])
                self.assertTrue(probe["direct_response"])
                self.assertEqual(3000, probe["raw_read_ms"])
                self.assertEqual({"outcome": "any"}, probe["expect"])
                self.assertEqual(8, len(probe["arguments"]))

                differences = [
                    index
                    for index, (actual, normal) in enumerate(
                        zip(probe["arguments"], NORMAL), start=1
                    )
                    if actual != normal
                ]
                self.assertEqual([entry["position"]], differences)
                replacement = probe["arguments"][entry["position"] - 1]
                expected_key = "string" if entry["wire_type"] == "string" else "blob_hex"
                self.assertEqual([expected_key], list(replacement))
                self.assertEqual(
                    f"goldens/rekordbox-7.2.19/xdj-rx3/render-argument-types/{entry['id']}.json",
                    entry["golden"],
                )

    def test_static_decoder_audit_is_binary_pinned_and_covers_both_tags(self) -> None:
        report = json.loads(STATIC.read_text())
        self.assertEqual(
            hashlib.sha256(BINARY.read_bytes()).hexdigest(),
            report["executable_sha256"],
        )
        self.assertEqual(27, report["validated_instruction_count"])
        self.assertEqual(
            {
                "1": "0x10143b826",
                "2": "0x10143b86d",
                "3": "0x10143b8a8",
                "4": "0x10143b7fa",
                "5": "0x10143b7fa",
                "6": "0x10143b7fa",
            },
            report["tag_dispatch"],
        )
        findings = report["findings"]
        self.assertEqual(2, findings["argument_tag_string"])
        self.assertEqual(3, findings["argument_tag_blob"])
        self.assertEqual(6, findings["argument_tag_number"])
        self.assertTrue(findings["string_requires_preceding_length_slot"])
        self.assertTrue(findings["blob_requires_preceding_length_slot"])
        self.assertTrue(findings["variable_width_argument_one_is_rejected_before_dispatch"])
        self.assertTrue(findings["decoded_variable_width_slot_contains_allocation_pointer"])
        self.assertTrue(findings["render_reads_value_slots_without_semantic_tag_checks"])

        disassembly = DISASSEMBLY.read_text()
        self.assertIn("PSvDBConnection14ReceiveCommand", disassembly)
        self.assertIn("PSvDBMain18GetListBufContents", disassembly)
        self.assertIn("cmp       rax, 0x201", disassembly)
        self.assertIn("cmp       rax, 0x500000", disassembly)

    def test_docs_preserve_the_pending_real_authority_boundary(self) -> None:
        documents = {
            "PROTOCOL_REFERENCE.md": "Track render argument types",
            "CONFORMANCE_COVERAGE.md": "Track render argument types",
            "REKORDBOX_RESEARCH_GAPS.md": "render-argument-types",
            "SOURCES.md": "Track render argument types",
            "CLEANUP.md": "render-argument-types",
        }
        for name, fragment in documents.items():
            text = " ".join((LAB / name).read_text().split())
            with self.subTest(document=name):
                self.assertIn(fragment, text)


if __name__ == "__main__":
    unittest.main()
