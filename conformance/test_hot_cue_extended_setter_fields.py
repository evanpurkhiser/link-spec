import json
import struct
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MATRIX = ROOT / "data/hot-cue-setter-field-matrix.json"
RECORDER = ROOT / "record_hot_cue_extended_setter_field_matrix.sh"
TOOLS = ROOT.parent / "tools"
sys.path.insert(0, str(TOOLS))

from summarize_hot_cue_extended_setter_fields import truncated_raw_message


class HotCueExtendedSetterFieldsTest(unittest.TestCase):
    def test_matrix_covers_every_declared_mutable_axis(self) -> None:
        matrix = json.loads(MATRIX.read_text())
        variants = matrix["variants"]
        axes = {variant["axis"] for variant in variants}

        self.assertEqual(len(variants), 56)
        self.assertEqual(
            axes,
            {
                "in-msec",
                "out-msec",
                "in-mpeg-frame",
                "out-mpeg-frame",
                "in-mpeg-absolute",
                "out-mpeg-absolute",
                "color-wire",
                "color-table-index",
                "cue-microseconds",
                "beat-loop-size",
                "comment",
            },
        )

    def test_every_suite_is_a_single_setter_and_database_read(self) -> None:
        matrix = json.loads(MATRIX.read_text())
        for variant in matrix["variants"]:
            suite = json.loads((ROOT / variant["suite"]).read_text())
            self.assertEqual(
                [case["id"] for case in suite["cases"]],
                ["setter", "database-read-after-setter"],
            )
            setter = suite["cases"][0]
            record = bytes.fromhex(setter["arguments"][4]["blob_hex"])
            self.assertEqual(setter["arguments"][3]["number"], len(record))
            self.assertEqual(struct.unpack_from("<I", record)[0], len(record))
            self.assertEqual(struct.unpack_from("<I", record, 0x34)[0], len(record) - 58)

    def test_maximum_comment_exhausts_even_uint16_length(self) -> None:
        matrix = json.loads(MATRIX.read_text())
        variant = next(item for item in matrix["variants"] if item["id"] == "comment-maximum-even-length")
        suite = json.loads((ROOT / variant["suite"]).read_text())
        record = bytes.fromhex(suite["cases"][0]["arguments"][4]["blob_hex"])

        self.assertEqual(struct.unpack_from("<H", record, 0x48)[0], 0xFFFE)
        self.assertEqual(len(record), 124 + 0xFFFE)

    def test_maximum_comment_has_strict_truncated_response_prefixes(self) -> None:
        golden = json.loads(
            (
                ROOT
                / "goldens/rekordbox-7.2.19/xdj-rx3-status"
                / "hot-cue-setter-field-comment-maximum-even-length.json"
            ).read_text()
        )
        cases = {case["id"]: case for case in golden["behavior"]["cases"]}

        setter_raw, setter_length = truncated_raw_message(cases["setter"], 0x2401)
        getter_raw, getter_length = truncated_raw_message(
            cases["database-read-after-setter"],
            0x2301,
        )

        self.assertEqual(len(setter_raw), 8192)
        self.assertEqual(len(getter_raw), 8192)
        self.assertEqual(setter_length, 0x10078)
        self.assertEqual(getter_length, 0x10078)

        truncated = json.loads(json.dumps(cases["setter"]))
        truncated["raw_response"]["raw_hex"] = truncated["raw_response"]["raw_hex"][:-2]
        with self.assertRaises(AssertionError):
            truncated_raw_message(truncated, 0x2401)

    def test_recorder_rejects_unbound_resume_halves(self) -> None:
        recorder = RECORDER.read_text()

        self.assertIn(
            "discarding candidate without its record database proof",
            recorder,
        )
        self.assertIn(
            "discarding record database proof without its candidate",
            recorder,
        )


if __name__ == "__main__":
    unittest.main()
