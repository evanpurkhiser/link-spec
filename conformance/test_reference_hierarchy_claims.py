import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
GOLDENS = ROOT / "conformance/goldens/rekordbox-7.2.19/xdj-rx3"


def cases(golden: str) -> dict[str, dict]:
    document = json.loads((GOLDENS / golden).read_text())

    return {case["id"]: case for case in document["behavior"]["cases"]}


def menu_total(case: dict) -> int:
    return case["header"][0]["arguments"][1]["value"]


def row_values(case: dict) -> list[list]:
    return [
        [argument["value"] for argument in message["arguments"]]
        for page in case["pages"]
        for message in page["messages"]
        if message["kind"] == 0x4101
    ]


class ReferenceHierarchyClaimsTest(unittest.TestCase):
    def test_full_fixture_proves_original_artist_and_remixer_hierarchies(self) -> None:
        full = cases("full.json")

        expected = {
            "original-artists": (1, [1004]),
            "original-artist-albums": (4, [0xFFFFFFFF, 2001, 2003, 2002]),
            "original-artist-tracks": (3, [10001, 10003, 10004]),
            "remixers": (1, [1003]),
            "remixer-albums": (4, [0xFFFFFFFF, 2001, 2003, 2002]),
            "remixer-tracks": (3, [10001, 10003, 10004]),
        }

        for case_id, (total, identifiers) in expected.items():
            with self.subTest(case=case_id):
                case = full[case_id]
                rows = row_values(case)

                self.assertEqual(menu_total(case), total)
                self.assertEqual([row[1] for row in rows], identifiers)

    def test_empty_fixture_proves_both_roots_are_valid_empty_menus(self) -> None:
        empty = cases("empty.json")

        for case_id in ("original-artists", "remixers"):
            with self.subTest(case=case_id):
                case = empty[case_id]

                self.assertEqual(menu_total(case), 0)
                self.assertEqual(row_values(case), [])


if __name__ == "__main__":
    unittest.main()
