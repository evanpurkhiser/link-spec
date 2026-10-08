import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
GOLDENS = ROOT / "conformance/goldens/rekordbox-7.2.19/xdj-rx3"
STATIC_EVIDENCE = (
    ROOT / "data/static-analysis/category-configuration-fields.disasm.txt"
)


def case(golden: Path, case_id: str) -> dict:
    document = json.loads(golden.read_text())

    return next(
        item for item in document["behavior"]["cases"] if item["id"] == case_id
    )


def menu_total(item: dict) -> int:
    return item["header"][0]["arguments"][1]["value"]


class CategoryConfigurationSemanticsTest(unittest.TestCase):
    def test_empty_library_keeps_enabled_root_categories(self) -> None:
        root = case(GOLDENS / "empty.json", "root")
        items = [
            message
            for page in root["pages"]
            for message in page["messages"]
            if message["kind"] == 0x4101
        ]

        self.assertEqual(menu_total(root), 20)
        self.assertEqual(len(items), 20)

    def test_disabling_each_visible_category_removes_one_root_row(self) -> None:
        fixtures = sorted(GOLDENS.glob("category-*-disabled.json"))

        self.assertEqual(len(fixtures), 21)
        for golden in fixtures:
            expected = 20 if golden.name == "category-17-disabled.json" else 19
            with self.subTest(golden=golden.name):
                self.assertEqual(menu_total(case(golden, "root")), expected)

    def test_static_trace_separates_info_order_from_serving_fields(self) -> None:
        evidence = STATIC_EVIDENCE.read_text()

        for field in ("ID", "MenuItemID", "Seq", "Disable", "InfoOrder"):
            self.assertIn(field, evidence)
        self.assertIn("InfoOrder`, column 4, is never read", evidence)
        self.assertIn("content-table emptiness does not suppress", evidence)


if __name__ == "__main__":
    unittest.main()
