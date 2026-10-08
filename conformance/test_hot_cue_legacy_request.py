import json
import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from build_hot_cue_legacy_request import build_cue, build_extension


class HotCueLegacyRequestTests(unittest.TestCase):
    def test_canonical_blobs_are_stable(self) -> None:
        self.assertEqual(
            "000104001127000000000000111111112222222233333333444444445555555566666666",
            build_cue(10001).hex(),
        )
        self.assertEqual("7777777788888888", build_extension().hex())

    def test_content_id_is_the_only_variable_word(self) -> None:
        known = build_cue(10001)
        unknown = build_cue(999999)

        self.assertEqual(known[:4], unknown[:4])
        self.assertNotEqual(known[4:8], unknown[4:8])
        self.assertEqual(known[8:], unknown[8:])

    def test_d_e_f_ordinals_change_only_the_flag_high_word(self) -> None:
        records = [build_cue(10001, ordinal) for ordinal in (4, 5, 6)]

        self.assertEqual(
            ["00010400", "00010500", "00010600"],
            [record[:4].hex() for record in records],
        )
        self.assertEqual(records[0][4:], records[1][4:])
        self.assertEqual(records[1][4:], records[2][4:])

    def test_accepts_complete_wire_ordinal_range(self) -> None:
        self.assertEqual("00010000", build_cue(10001, 0)[:4].hex())
        self.assertEqual("0001ffff", build_cue(10001, 0xFFFF)[:4].hex())

    def test_rejects_ordinals_outside_wire_range(self) -> None:
        for ordinal in (-1, 0x1_0000):
            with self.subTest(ordinal=ordinal):
                with self.assertRaises(ValueError):
                    build_cue(10001, ordinal)

    def test_boundary_suite_blobs_match_the_builder(self) -> None:
        suite_path = (
            Path(__file__).resolve().parent
            / "suites/hot-cue-bank-legacy-ordinal-boundaries.json"
        )
        suite = json.loads(suite_path.read_text())
        expected = (
            (0, 10001),
            (1, 10002),
            (2, 10003),
            (3, 10004),
            (7, 10005),
            (8, 10006),
            (255, 10007),
            (256, 10008),
            (32_767, 10001),
            (32_768, 10002),
            (65_535, 10003),
        )

        self.assertEqual(len(expected), len(suite["cases"]))
        for case, (ordinal, content_id) in zip(suite["cases"], expected, strict=True):
            with self.subTest(case=case["id"]):
                self.assertEqual(
                    build_cue(content_id, ordinal).hex(),
                    case["arguments"][3]["blob_hex"],
                )
                self.assertEqual(
                    build_extension().hex(),
                    case["arguments"][5]["blob_hex"],
                )


if __name__ == "__main__":
    unittest.main()
