import json
import hashlib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
TARGET = ROOT / "suites/generated/render-arity-underflow.json"
TARGET_GOLDEN = (
    ROOT / "goldens/rekordbox-7.2.19/xdj-rx3/render-arity-underflow.json"
)
GOLDENS = ROOT / "goldens"
LAB = ROOT.parent
STATIC = LAB / "data/static-analysis/render-arity-underflow-parser.json"
DISASSEMBLY = LAB / "data/static-analysis/render-arity-underflow-parser.disasm.txt"
BINARY = (
    LAB.parent
    / "artifacts/rekordbox/7.2.19/extracted/app-root/rekordbox.app/Contents/MacOS/rekordbox"
)


class RenderArityUnderflowTests(unittest.TestCase):
    def test_existing_goldens_do_not_cover_warmed_render_arities_zero_to_two(self) -> None:
        matches = []
        for path in sorted(GOLDENS.rglob("*.json")):
            if path == TARGET_GOLDEN:
                continue

            cases = json.loads(path.read_text()).get("behavior", {}).get("cases", [])
            for previous, case in zip(cases, cases[1:]):
                request = case.get("request", {})
                if request.get("kind") != 0x3000:
                    continue
                if len(request.get("arguments", [])) > 2:
                    continue
                if previous.get("request", {}).get("kind") == 0x1004:
                    matches.append((str(path.relative_to(ROOT)), case["id"]))

        self.assertEqual([], matches)

    def test_suite_covers_zero_one_and_two_after_valid_track_lists(self) -> None:
        suite = json.loads(TARGET.read_text())
        self.assertEqual("track-render-arity-underflow", suite["name"])
        self.assertEqual(9, len(suite["cases"]))

        for arity in range(3):
            warm, probe, health = suite["cases"][arity * 3 : arity * 3 + 3]
            self.assertEqual(f"warm-list-arity-{arity}", warm["id"])
            self.assertTrue(warm["fresh_connection"])
            self.assertFalse(warm["render"])
            self.assertEqual("0x1004", warm["request_kind"])
            self.assertEqual(8, warm["expect"]["total"])

            self.assertEqual(f"render-arity-{arity}", probe["id"])
            self.assertEqual("0x3000", probe["request_kind"])
            self.assertEqual(arity, len(probe["arguments"]))
            self.assertTrue(probe["direct_response"])
            self.assertEqual("any", probe["expect"]["outcome"])
            self.assertNotIn("fresh_connection", probe)

            self.assertEqual(f"health-after-arity-{arity}", health["id"])
            self.assertTrue(health["fresh_connection"])
            self.assertEqual("0x1004", health["request_kind"])
            self.assertEqual(8, health["expect"]["total"])

    def test_static_decoder_audit_proves_missing_slots_are_zero(self) -> None:
        report = json.loads(STATIC.read_text())
        self.assertEqual(
            hashlib.sha256(BINARY.read_bytes()).hexdigest(),
            report["executable_sha256"],
        )
        self.assertEqual(22, report["validated_instruction_count"])
        findings = report["findings"]
        self.assertEqual(0x98, findings["command_allocation_bytes"])
        self.assertTrue(findings["command_allocation_is_zero_initialized"])
        self.assertTrue(findings["zero_argument_count_skips_field_loop"])
        self.assertTrue(
            findings["render_mandatory_slot_reads_precede_first_count_guard"]
        )
        self.assertEqual(0, findings["missing_slot_value"])
        self.assertEqual(
            {
                "0": [0, 0, 0],
                "1": ["argument_1", 0, 0],
                "2": ["argument_1", "argument_2", 0],
            },
            findings["underflow_projection"],
        )

        disassembly = DISASSEMBLY.read_text()
        self.assertIn("PSvDBConnection14ReceiveCommand", disassembly)
        self.assertIn("PSvDBMain18GetListBufContents", disassembly)
        self.assertIn("mov       edi, 0x98", disassembly)
        self.assertIn("cmp       byte ptr [r14 + 7], 6", disassembly)

    def test_docs_preserve_pending_authority_boundary(self) -> None:
        documents = {
            "PROTOCOL_REFERENCE.md": "Track render arity underflow",
            "CONFORMANCE_COVERAGE.md": "Track render arities 0 through 2",
            "REKORDBOX_RESEARCH_GAPS.md": "render-arity-underflow",
            "SOURCES.md": "Track render arity underflow",
        }
        for name, fragment in documents.items():
            text = " ".join((ROOT.parent / name).read_text().split())
            with self.subTest(document=name):
                self.assertIn(fragment, text)


if __name__ == "__main__":
    unittest.main()
