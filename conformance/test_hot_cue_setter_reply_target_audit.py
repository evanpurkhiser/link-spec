import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "data/static-analysis/hot-cue-setter-reply-target.json"
TOOL = ROOT / "tools/audit_hot_cue_setter_reply_target.py"
BINARY = (
    ROOT.parent
    / "artifacts/rekordbox/7.2.19/extracted/app-root/rekordbox.app/Contents/MacOS/rekordbox"
)


class HotCueSetterReplyTargetAuditTest(unittest.TestCase):
    def test_vtable_target_and_ordering_are_pinned(self):
        document = json.loads(AUDIT.read_text())
        vtable = document["appsync_vtable"]
        success = document["setter_calls"]["successful_mutation_path"]

        self.assertEqual("0x288", vtable["method_offset"])
        self.assertEqual("0x1016d2f20", vtable["target_address"])
        self.assertIn("getHCBnkCuePointExt", vtable["target_symbol"])
        self.assertLess(
            int(success["last_database_update_call"], 16),
            int(success["getter_call"], 16),
        )

    def test_checked_in_audit_regenerates_byte_identically(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "audit.json"
            subprocess.run(
                [str(ROOT / ".venv/bin/python"), str(TOOL), str(BINARY), "--output", str(output)],
                check=True,
            )
            self.assertEqual(AUDIT.read_bytes(), output.read_bytes())


if __name__ == "__main__":
    unittest.main()
