import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
AUDIT = ROOT / "data/static-analysis/user-info-djid.json"
GENERATOR = ROOT / "tools/audit_user_info_djid.py"


class UserInfoDjidTests(unittest.TestCase):
    def setUp(self) -> None:
        self.audit = json.loads(AUDIT.read_text())

    def test_audit_regenerates_byte_identically(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "audit.json"
            subprocess.run(
                [sys.executable, GENERATOR, "--output", output],
                cwd=ROOT,
                check=True,
            )
            self.assertEqual(AUDIT.read_bytes(), output.read_bytes())

    def test_reply_shapes_and_blob_partition_are_explicit(self) -> None:
        contract = self.audit["wire_contract"]
        self.assertEqual("0x3006", contract["request"]["kind"])
        self.assertEqual("0x4d02", contract["success_reply"]["kind"])
        self.assertEqual(
            ["0x3006", 0, 160, "blob(160)"],
            contract["success_reply"]["arguments"],
        )
        self.assertIn("first 32 bytes", contract["success_reply"]["blob"])
        self.assertEqual(
            ["0x3006", 0, 0, "blob(0)"], contract["absent_reply"]["arguments"]
        )
        self.assertEqual("zero-length blob field", contract["absent_reply"]["blob"])

    def test_configuration_and_startup_path_are_bound(self) -> None:
        initialization = self.audit["static_initialization"]
        startup = self.audit["server_startup"]
        self.assertEqual("djprofile.nxs", initialization["filename"])
        self.assertEqual(160, startup["file_validation"]["exact_bytes"])
        checksum = startup["file_validation"]["checksum"]
        self.assertIn("big-endian u32 at offset 28", checksum)
        self.assertIn("little-endian u32 at offset 0", checksum)
        self.assertEqual(
            {
                "offset_0_vptr_slot_0x48": "0x1027add00",
                "offsets_4_8_12_28_vptr_slot_0x50": "0x1027add30",
            },
            startup["file_validation"]["checksum_reader_vtable_targets"],
        )
        self.assertIn("first 32", startup["loaded_state"])
        self.assertEqual(
            [1, 1, 2],
            [len(sites) for sites in startup["ui_call_sites"].values()],
        )

    def test_client_lifecycle_and_evidence_boundary_are_preserved(self) -> None:
        self.assertEqual(3, len(self.audit["cdj_3000_post_load_chain"]))
        failure = self.audit["client_failure_semantics"]
        self.assertIn("18 seconds", failure["missing_reply"])
        self.assertIn("two retries", failure["missing_reply"])
        self.assertIn("live 7.2.19 oracle remains required", self.audit["evidence_boundary"])

    def test_protocol_documents_link_the_generated_audit(self) -> None:
        for name in (
            "USER_INFO_DJID_ORACLE.md",
            "LINK_EXPORT_REQUEST_VOCABULARY.md",
            "PROTOCOL_REFERENCE.md",
            "REKORDBOX_RESEARCH_GAPS.md",
        ):
            text = (ROOT / name).read_text()
            self.assertIn("user-info-djid.json", text)
            self.assertIn("0x3006", text)
            self.assertIn("0x4d02", text)


if __name__ == "__main__":
    unittest.main()
