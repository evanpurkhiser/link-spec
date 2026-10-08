import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DISASSEMBLY = ROOT / "data/static-analysis/bpm-tolerance-boundaries.disasm.txt"
STATIC_ANALYSIS = ROOT / "docs/STATIC_ANALYSIS.md"
DATABASE_QUERIES = ROOT / "docs/DATABASE_QUERIES.md"


class BpmToleranceStaticAnalysisTests(unittest.TestCase):
    def test_artifact_is_bound_to_the_pinned_binary_and_functions(self) -> None:
        artifact = DISASSEMBLY.read_text()

        self.assertIn(
            "07dcecbaf304f777e435539c83c7dcc02e41de1eaf2e0a75e8a9852e4411a244",
            artifact,
        )
        self.assertIn("## __Z15getRowset_Track9RbDBIndexajiiii", artifact)
        self.assertIn("address=0x100487c20 size=0x740", artifact)
        self.assertIn("## __Z23wherefuncGetRowset_ValsPvS_", artifact)
        self.assertIn("address=0x100489300 size=0x90", artifact)

    def test_artifact_contains_every_instruction_boundary_used_by_the_claim(self) -> None:
        artifact = DISASSEMBLY.read_text()

        for address in (
            "0x0100487d70",
            "0x0100487dc2",
            "0x01004880fb",
            "0x010048812e",
            "0x0100489356",
            "0x0100489363",
        ):
            with self.subTest(address=address):
                self.assertIn(address, artifact)

        nonzero_branch = self._address_range(
            artifact, "0x0100487d70", "0x0100487dc2"
        )
        zero_branch = self._address_range(
            artifact, "0x01004880fb", "0x010048812e"
        )
        predicate = self._address_range(
            artifact, "0x0100489356", "0x0100489363"
        )

        self.assertIn("imul", nonzero_branch)
        self.assertIn("0x64", nonzero_branch)
        self.assertIn("0x51eb851f", nonzero_branch)
        self.assertIn("0x32", zero_branch)
        self.assertIn("0x31", zero_branch)
        self.assertEqual(2, predicate.count("setle"))

    def test_interpretation_documents_static_and_dynamic_evidence_boundaries(self) -> None:
        static = STATIC_ANALYSIS.read_text()
        queries = DATABASE_QUERIES.read_text()

        for document in (static, queries):
            with self.subTest(document=document[:30]):
                self.assertIn("(100 - p) *", document)
                self.assertIn("(100 + p) *", document)
                self.assertIn("[rounded - 50, rounded + 49]", document)
                self.assertIn("lower <= BPM && BPM <= upper", document)

        self.assertIn("**[DEC]**", static)
        self.assertIn("**[OBS, DB]**", static)

    @staticmethod
    def _address_range(artifact: str, start: str, end: str) -> str:
        match = re.search(
            rf"^{re.escape(start)} .*?^{re.escape(end)} .*?$",
            artifact,
            flags=re.MULTILINE | re.DOTALL,
        )

        if match is None:
            raise AssertionError(f"missing disassembly range {start}..{end}")

        return match.group(0)


if __name__ == "__main__":
    unittest.main()
