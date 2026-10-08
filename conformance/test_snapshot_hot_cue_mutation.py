import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from snapshot_hot_cue_mutation import decode_database_text


class SnapshotHotCueMutationTest(unittest.TestCase):
    def test_valid_utf8_remains_plain_text(self):
        self.assertEqual(decode_database_text("fixture é".encode()), "fixture é")

    def test_surrogate_utf8_is_preserved_as_explicit_bytes(self):
        value = decode_database_text(bytes.fromhex("eda080"))

        self.assertEqual(value, {"encoding": "invalid-utf8", "hex": "eda080"})
        self.assertEqual(
            json.loads(json.dumps(value)),
            {"encoding": "invalid-utf8", "hex": "eda080"},
        )


if __name__ == "__main__":
    unittest.main()
