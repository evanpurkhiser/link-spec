import hashlib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "data/static-analysis"
BINARY = (
    ROOT.parent
    / "artifacts/rekordbox/7.2.19/extracted/app-root/rekordbox.app/Contents/MacOS/rekordbox"
)
EXPECTED_BINARY_SHA256 = (
    "07dcecbaf304f777e435539c83c7dcc02e41de1eaf2e0a75e8a9852e4411a244"
)


class SongInfoMalformedTransactionTests(unittest.TestCase):
    def test_static_evidence_is_bound_to_rekordbox_7_2_19(self) -> None:
        self.assertEqual(
            EXPECTED_BINARY_SHA256,
            hashlib.sha256(BINARY.read_bytes()).hexdigest(),
        )
        self.assertEqual(
            "63f1a9ac373ced1438fa1c063388a9c90aabf7b82f50cb072e1b103898e5b5e4",
            hashlib.sha256(
                (STATIC / "listbuf-transaction-state.disasm.txt").read_bytes()
            ).hexdigest(),
        )

    def test_delivery_declares_two_numeric_arguments(self) -> None:
        parser = (STATIC / "dbserver-command-parser.disasm.txt").read_text()
        self.assertIn("0x010049d6bd  cmp       eax, 0x2602", parser)
        self.assertIn("0x010049d6c2  je        0x10049d155", parser)
        self.assertIn("0x010049d155  mov       word ptr [rdi + 7], 0x602", parser)
        self.assertIn("0x010049d15b  mov       byte ptr [rdi + 9], 6", parser)

    def test_delivery_wrapper_reads_slot_two_without_a_tag_check(self) -> None:
        siblings = (STATIC / "song-info-siblings.disasm.txt").read_text()
        wrapper = siblings.split(
            "## __ZN9PSvDBMain14GetDeliveryInfEP16_struct_dbsm_msgjPm |", 1
        )[1].split("## ", 1)[0]
        self.assertIn("mov       eax, dword ptr [rcx + 8]", wrapper)
        self.assertIn("call      qword ptr [rcx + 0x220]", wrapper)
        self.assertNotIn("cmp       byte ptr [rcx", wrapper)

    def test_failed_lookup_skips_transaction_finalization(self) -> None:
        siblings = (STATIC / "song-info-siblings.disasm.txt").read_text()
        builder = siblings.split("## __ZN9PSvDBMain16GetDeliveryInfDBEjj |", 1)[
            1
        ].split("## ", 1)[0]
        self.assertIn("xor       esi, esi", builder)
        self.assertIn("call      0x10249cf40  ; __Z17DsqlListBuf_Clearji", builder)
        self.assertIn("call      0x102255ce0  ; __Z22DsqlContent_GetSongInf", builder)
        self.assertIn("0x0101ab878e  jmp       0x101ab8eda", builder)
        self.assertIn("call      0x10249cfc0  ; __Z18DsqlListBuf_InsEndi", builder)
        self.assertLess(builder.index("0x0101ab878e"), builder.index("0x0101ab8ecb"))

    def test_ins_end_one_commits_and_restores_autocommit(self) -> None:
        transaction = (STATIC / "listbuf-transaction-state.disasm.txt").read_text()
        change = transaction.split(
            "## __Z28DsqlCmn_ChangeAutoCommitStati |", 1
        )[1].split("## ", 1)[0]
        ins_end = transaction.split("## __Z18DsqlListBuf_InsEndi |", 1)[1]
        self.assertIn("call      0x10325eaa0  ; _edb_dyn_CommitTransaction", change)
        self.assertIn("call      0x10325ec20  ; _edb_dyn_SetAutoCommitState", change)
        self.assertIn("call      0x101e1a960  ; __Z28DsqlCmn_ChangeAutoCommitStati", ins_end)
        self.assertIn("call      0x10325ecf0  ; _edb_dyn_OpenIndex", ins_end)


if __name__ == "__main__":
    unittest.main()
