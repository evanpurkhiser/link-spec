import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SUITES = ROOT / "suites"
TARGET = SUITES / "generated/sort-secondary-render-7.json"
ARITY_TARGET = SUITES / "generated/render-arity-boundaries.json"
GOLDENS = ROOT / "goldens"
TARGET_GOLDEN = (
    GOLDENS / "rekordbox-7.2.19/xdj-rx3/sort-secondary-render-7.json"
)
ARITY_TARGET_GOLDEN = (
    GOLDENS / "rekordbox-7.2.19/xdj-rx3/render-arity-boundaries.json"
)
SORT_IDS = (0, 1, 2, 3, 4, 5, 6, 10, 12, 17, 16)
GATES = (0, 1, "0xffffffff")


def effective_render_arguments(suite: dict, case: dict) -> list:
    return case.get("render_arguments", suite["defaults"]["render_arguments"])


class SortSecondaryRender7Tests(unittest.TestCase):
    def test_historical_corpus_has_no_track_render_7(self) -> None:
        matches = []
        for path in sorted(SUITES.rglob("*.json")):
            if path in (TARGET, ARITY_TARGET):
                continue

            suite = json.loads(path.read_text())
            for case in suite["cases"]:
                if case["request_kind"] != "0x1004":
                    continue
                if len(effective_render_arguments(suite, case)) == 4:
                    matches.append((str(path.relative_to(ROOT)), case["id"]))

        self.assertEqual([], matches)

    def test_historical_goldens_have_no_track_render_7(self) -> None:
        matches = []
        for path in sorted(GOLDENS.rglob("*.json")):
            if path in (TARGET_GOLDEN, ARITY_TARGET_GOLDEN):
                continue

            golden = json.loads(path.read_text())
            for case in golden.get("behavior", {}).get("cases", []):
                request = case.get("request", {})
                if request.get("kind") != 0x1004:
                    continue
                if any(len(page.get("arguments", [])) == 7 for page in case.get("pages", [])):
                    matches.append((str(path.relative_to(ROOT)), case["id"]))

        self.assertEqual([], matches)

    def test_suite_crosses_sorts_and_seventh_argument_values(self) -> None:
        suite = json.loads(TARGET.read_text())
        self.assertEqual("rx3-track-sort-secondary-render-7", suite["name"])
        self.assertEqual(33, len(suite["cases"]))
        observed = []
        for case in suite["cases"]:
            self.assertTrue(case["fresh_connection"])
            self.assertEqual(16, case["expect"]["argument_count"])
            self.assertEqual([0, "$total", 12], case["render_arguments"][:3])
            observed.append(
                (case["arguments"][1]["number"], case["render_arguments"][3])
            )

        self.assertEqual(
            [(sort_id, gate) for gate in GATES for sort_id in SORT_IDS],
            observed,
        )

    def test_static_decoder_reads_gate_only_at_eight_arguments(self) -> None:
        disassembly = (
            ROOT.parent / "data/static-analysis/client-and-render.disasm.txt"
        ).read_text()
        body = disassembly.split(
            "## __ZN9PSvDBMain18GetListBufContentsEP16_struct_dbsm_msg |", 1
        )[1].split("\n## ", 1)[0]
        self.assertIn("cmp       byte ptr [r14 + 7], 6", body)
        self.assertIn("movzx     edi, word ptr [r14 + 0x40]", body)
        self.assertIn("call      0x101d627c0", body)
        self.assertIn("cmp       byte ptr [r14 + 7], 8", body)
        self.assertIn("cmp       dword ptr [r14 + 0x48], 0", body)
        self.assertIn("mov       ecx, dword ptr [r14 + 0x50]", body)

    def test_declaration_is_documented_as_pending_evidence(self) -> None:
        documents = {
            "SECONDARY_COLUMNS.md": "seven-argument active-sort matrix",
            "PROTOCOL_REFERENCE.md": "Seven-argument rendering is accepted",
            "REKORDBOX_RESEARCH_GAPS.md": "sort-secondary-render-7",
            "CONFORMANCE_COVERAGE.md": "active sort x seven-argument track render",
            "SOURCES.md": "Seven-argument active-sort rendering",
        }
        for name, fragment in documents.items():
            text = " ".join((ROOT.parent / name).read_text().split())
            with self.subTest(document=name):
                self.assertIn(fragment, text)

        coverage = " ".join((ROOT.parent / "CONFORMANCE_COVERAGE.md").read_text().split())
        self.assertIn("three common render arities", coverage)
        self.assertIn("fourth parser-accepted shape", coverage)


if __name__ == "__main__":
    unittest.main()
