import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools/update_checksums.py"
SPEC = importlib.util.spec_from_file_location("update_checksums", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
UPDATE_CHECKSUMS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(UPDATE_CHECKSUMS)


class UpdateChecksumsTest(unittest.TestCase):
    def test_excludes_atomic_promotion_scratch_files(self):
        self.assertTrue(UPDATE_CHECKSUMS.excluded(ROOT / "result.json.next"))
        self.assertTrue(
            UPDATE_CHECKSUMS.excluded(ROOT / "data/experiments/result.json.next")
        )

    def test_retains_completed_artifacts(self):
        self.assertFalse(UPDATE_CHECKSUMS.excluded(ROOT / "result.json"))


if __name__ == "__main__":
    unittest.main()
