import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SETTER_DISASSEMBLY = ROOT / "data/static-analysis/hot-cue-bank-mutations.disasm.txt"
RESOLVER_DISASSEMBLY = (
    ROOT / "data/static-analysis/hot-cue-bank-membership-resolver.disasm.txt"
)
STATIC_ANALYSIS = ROOT / "docs/STATIC_ANALYSIS.md"
HOT_CUE_ORACLE = ROOT / "docs/HOT_CUE_BANK_ORACLE.md"
DATABASE_QUERIES = ROOT / "docs/DATABASE_QUERIES.md"


class HotCueSlot8StaticAnalysisTests(unittest.TestCase):
    def test_setter_gate_admits_exactly_slots_one_through_eight(self) -> None:
        artifact = SETTER_DISASSEMBLY.read_text()
        gate = self._address_range(artifact, "0x01016d3fbd", "0x01016d3fc9")

        self.assertIn("word ptr [r14 + 4]", gate)
        self.assertIn("[rsi - 9]", gate)
        self.assertIn("cmp       ax, -8", gate)
        self.assertIn("jb", gate)

    def test_resolver_rejects_exactly_one_then_indexes_row_zero(self) -> None:
        artifact = RESOLVER_DISASSEMBLY.read_text()
        branch = self._address_range(artifact, "0x01016d2e11", "0x01016d2e29")

        self.assertIn("var4sizeEv", branch)
        self.assertIn("cmp       eax, 1", branch)
        self.assertIn("je", branch)
        self.assertIn("xor       esi, esi", branch)
        self.assertIn("varixEi", branch)

    def test_documents_preserve_static_dynamic_evidence_boundary(self) -> None:
        for path in (STATIC_ANALYSIS, HOT_CUE_ORACLE, DATABASE_QUERIES):
            document = path.read_text()
            normalized = " ".join(document.split())

            with self.subTest(path=path.name):
                self.assertIn("1 through 8", normalized)
                self.assertIn("pristine", normalized)
                self.assertIn("124-byte", normalized)
                self.assertIn("inference", normalized)

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
