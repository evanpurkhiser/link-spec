import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
LAB = ROOT.parent
SUITES = ROOT / "suites"
TARGET = SUITES / "generated/render-numeric-fields.json"
STATIC = LAB / "data/static-analysis/render-numeric-fields.json"
DISASSEMBLY = LAB / "data/static-analysis/render-numeric-fields.disasm.txt"
BINARY = (
    LAB.parent
    / "artifacts/rekordbox/7.2.19/extracted/app-root/rekordbox.app/Contents/MacOS/rekordbox"
)
CONTROL = [0, 8, 12, 1, 0]


class RenderNumericFieldTests(unittest.TestCase):
    def test_historical_suites_never_varied_render_arguments_four_or_five(self) -> None:
        argument_4 = set()
        argument_5 = set()
        for path in sorted(SUITES.rglob("*.json")):
            if path in {
                TARGET,
                SUITES / "generated/render-override-controls.json",
            } or path.is_relative_to(
                SUITES / "generated/render-argument-types"
            ):
                continue

            suite = json.loads(path.read_text())
            default = suite["defaults"]["render_arguments"]
            for case in suite["cases"]:
                if case.get("request_kind") == "0x3000":
                    continue
                tail = case.get("render_arguments", default)
                if len(tail) >= 1:
                    argument_4.add(json.dumps(tail[0], sort_keys=True))
                if len(tail) >= 2:
                    argument_5.add(json.dumps(tail[1], sort_keys=True))

        self.assertEqual({"0"}, argument_4)
        self.assertEqual({'"$total"'}, argument_5)

    def test_suite_covers_seek_total_and_category_equivalence_ranges(self) -> None:
        suite = json.loads(TARGET.read_text())
        self.assertEqual("track-render-numeric-fields", suite["name"])
        self.assertEqual(42, len(suite["cases"]))
        ids = [case["id"] for case in suite["cases"]]
        self.assertEqual("control", ids[0])
        self.assertEqual(15, sum(value.startswith("first-row-seek-") for value in ids))
        self.assertEqual(6, sum(value.startswith("client-total-") for value in ids))
        self.assertEqual(20, sum(value.startswith("category-id-") for value in ids))

        category_values = {
            case["render_arguments"][2]
            for case in suite["cases"]
            if case["id"].startswith("category-id-")
        }
        self.assertEqual(
            {
                0, 1, 7, 15, 20, 24, 25, 29, 30, 32, 33, 39, 40, 49,
                50, 51, 52, "0x0000ffff", "0x0001000c", "0xffffffff",
            },
            category_values,
        )

    def test_each_case_changes_exactly_one_normal_field(self) -> None:
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
                else:
                    expected = (
                        4
                        if case["id"].startswith("first-row-seek-")
                        else 5
                        if case["id"].startswith("client-total-")
                        else 6
                    )
                    self.assertEqual([expected], differences)

    def test_static_audit_pins_widths_roles_and_complete_category_map(self) -> None:
        report = json.loads(STATIC.read_text())
        self.assertEqual(
            hashlib.sha256(BINARY.read_bytes()).hexdigest(),
            report["executable_sha256"],
        )
        self.assertEqual(30, report["validated_instruction_count"])
        fields = report["render_argument_fields"]
        self.assertEqual(16, fields["4"]["read_width_bits"])
        self.assertEqual("first-row character seek key", fields["4"]["role"])
        self.assertEqual(0, fields["5"]["read_width_bits"])
        self.assertIn("unread", fields["5"]["role"])
        self.assertEqual(16, fields["6"]["read_width_bits"])
        self.assertIn("DBCommon_GetCateKind", fields["6"]["role"])

        expected = {
            **{str(value): value for value in range(1, 25)},
            **{str(value): 0 for value in range(25, 30)},
            **{str(value): value for value in range(30, 33)},
            **{str(value): 0 for value in range(33, 40)},
            "40": 40,
            **{str(value): 0 for value in range(41, 50)},
            "50": 50,
            "51": 51,
        }
        self.assertEqual(expected, report["category_kind_map"])
        self.assertTrue(report["findings"]["argument_5_has_no_read_in_get_list_buffer_contents"])
        self.assertTrue(report["findings"]["argument_4_and_6_ignore_high_16_bits"])

        disassembly = DISASSEMBLY.read_text()
        self.assertIn("PSvDBMain16GetListBuf1stRow", disassembly)
        self.assertIn("PSvDBMain18GetListBufContents", disassembly)
        self.assertIn("DBCommon_GetCateKind", disassembly)
        self.assertIn("cmp       dx, 0x55", disassembly)

    def test_docs_name_correct_fields_and_pending_authority(self) -> None:
        documents = {
            "docs/PROTOCOL_REFERENCE.md": "Track render numeric fields",
            "docs/CONFORMANCE_COVERAGE.md": "Track render numeric fields",
            "docs/REKORDBOX_RESEARCH_GAPS.md": "render-numeric-fields",
            "docs/SOURCES.md": "Track render numeric fields",
            "docs/SECONDARY_COLUMNS.md": "first-row character seek key",
            "docs/ROW_LAYOUT.md": "client-reported total",
            "docs/CLEANUP.md": "render-numeric-fields",
        }
        for name, fragment in documents.items():
            text = " ".join((LAB / name).read_text().split())
            with self.subTest(document=name):
                self.assertIn(fragment, text)


if __name__ == "__main__":
    unittest.main()
