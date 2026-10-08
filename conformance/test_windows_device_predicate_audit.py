import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
WINDOWS = ROOT / "data/static-analysis/windows"
AUDIT = WINDOWS / "device-predicate-audit.json"


class WindowsDevicePredicateAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.audit = json.loads(AUDIT.read_text())

    def test_exact_functions_and_direct_reference_counts(self) -> None:
        self.assertEqual(
            {
                "standalone_content_compatibility": {
                    "address": "0x14227e200",
                    "direct_control_xrefs": 1,
                },
                "disconnect_with_inlined_aio_clear": {
                    "address": "0x142380930",
                    "direct_control_xrefs": 1,
                },
                "display_is_aio": {
                    "address": "0x1423815c0",
                    "direct_control_xrefs": 1,
                },
                "map_only_aio_clear_helper": {
                    "address": "0x142381700",
                    "direct_control_xrefs": 0,
                },
                "get_list_buf_row_content": {
                    "address": "0x14238c720",
                    "direct_control_xrefs": 3,
                },
            },
            self.audit["functions"],
        )
        self.assertEqual(6, len(self.audit["direct_control_xrefs"]))
        self.assertEqual([], self.audit["absolute_pointer_references"])

    def test_inline_platform_differences_are_explicit(self) -> None:
        conclusions = self.audit["conclusions"]
        self.assertIn("contains", conclusions["disconnect_cache_clear"])
        self.assertIn("inlines", conclusions["track_compatibility"])
        self.assertIn("no little-endian", conclusions["absolute_pointer_storage"])
        self.assertFalse(conclusions["bit_depth_read"])

    def test_bound_disassembly_hashes(self) -> None:
        for name, expected in self.audit["artifacts"].items():
            actual = hashlib.sha256((WINDOWS / name).read_bytes()).hexdigest()
            self.assertEqual(expected, actual, name)

    def test_documentation_replaces_the_old_windows_gap(self) -> None:
        predicate_doc = (ROOT / "docs/DEVICE_PREDICATE_AUDIT.md").read_text()
        compatibility_doc = (ROOT / "docs/DEVICE_COMPATIBILITY.md").read_text()
        queries_doc = (ROOT / "docs/DATABASE_QUERIES.md").read_text()
        row_layout = (ROOT / "docs/ROW_LAYOUT.md").read_text()
        gaps = (ROOT / "docs/REKORDBOX_RESEARCH_GAPS.md").read_text()

        for document in (predicate_doc, compatibility_doc, gaps):
            self.assertIn("0x142380930", document)
            self.assertIn("0x14227e200", document)

        self.assertNotIn(
            "Windows `DsqlContent_GetNewCDJSupported` address and call count are not yet recovered",
            predicate_doc,
        )
        self.assertIn("active Windows AppSync branch queries", queries_doc)
        self.assertIn("depends only on content metadata", queries_doc)
        self.assertNotIn("two players may navigate", queries_doc)
        self.assertIn("peer model, class,", row_layout)
        self.assertNotIn("per-player compatibility flags", row_layout)
        self.assertIn("zero absolute pointer references", predicate_doc)
        self.assertIn("zero absolute pointers", gaps)


if __name__ == "__main__":
    unittest.main()
