import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from build_hot_cue_mutation_record import build_record


EXPECTED_HEX = (
    "7c000000010002000000e80355f8060052aa0800000000000800000000000000"
    "ffffffff0403020114131211242322213433323142000000000006000d0c0b0a"
    "000034127856000000002c000000000000000000000000000000000000000000"
    "00000000000000000000000000000000000000000000000000000000"
)


class HotCueMutationRecordTests(unittest.TestCase):
    def test_canonical_record_is_stable(self) -> None:
        record = build_record()

        self.assertEqual(124, len(record))
        self.assertEqual(EXPECTED_HEX, record.hex())


if __name__ == "__main__":
    unittest.main()
