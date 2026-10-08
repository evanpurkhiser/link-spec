import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DISPATCH = ROOT / "data/static-analysis/link-export-dispatch-tables.json"
VOCABULARY = ROOT / "data/static-analysis/link-export-request-vocabulary.json"
NAVIGATION = ROOT / "data/static-analysis/xdj-rr-client-navigation.json"
HANDLERS = ROOT / "data/static-analysis/source-only-client-handlers.disasm.txt"
DB_EFFECTS = ROOT / "data/static-analysis/source-only-client-db-effects.disasm.txt"
DISPATCH_EXTRACTOR = ROOT / "tools/extract_link_export_dispatch_tables.py"
VOCABULARY_GENERATOR = ROOT / "tools/generate_link_export_request_vocabulary.py"


class SourceOnlyClientHandlerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dispatch = json.loads(DISPATCH.read_text())
        cls.vocabulary = json.loads(VOCABULARY.read_text())
        cls.commands = {
            command["kind"]: command for command in cls.vocabulary["commands"]
        }
        cls.navigation = json.loads(NAVIGATION.read_text())
        cls.handlers = HANDLERS.read_text()
        cls.db_effects = DB_EFFECTS.read_text()

    def test_every_direct_xdj_rr_kind_has_terminal_rekordbox_evidence(self):
        direct_kinds = {
            call["request_kind"] for call in self.navigation["call_sites"]
        }
        unresolved = {
            kind
            for kind in direct_kinds
            if self.commands[kind]["coverage"] == "source-vocabulary-only"
        }
        self.assertEqual(unresolved, set())
        self.assertEqual(len(direct_kinds), 102)

    def test_key_and_cue_track_routes_are_exact(self):
        expected = {
            "100B": (
                "rekordbox-static-dispatch",
                "PSvAppSyncDBIF::getKey_Root via database-interface vtable +0xE8",
                "4000",
            ),
            "110B": (
                "rekordbox-static-dispatch",
                "PSvAppSyncDBIF::getTrack_Key via database-interface vtable +0xF0",
                "4000",
            ),
            "130C": (
                "rekordbox-recognized-log-only",
                "recognized-log-only",
                None,
            ),
        }
        for kind, result in expected.items():
            with self.subTest(kind=kind):
                command = self.commands[kind]
                self.assertEqual(
                    (command["coverage"], command["rekordbox_target"], command["reply_kind"]),
                    result,
                )

        for anchor in (
            "0x0101d2d2f5  cmp       eax, 0x110b",
            "0x0101d2d2fc  cmp       eax, 0x100b",
            "0x0101d2d356  call      qword ptr [rcx + 0xe8]",
            "0x0101d2d3dd  call      qword ptr [rbx + 0xf0]",
            "0x0101d2bd12  cmp       eax, 0x130c",
            "0x0101d2bd51  jmp       0x101d2be84",
        ):
            self.assertIn(anchor, self.handlers)

    def test_write_dispatch_is_complete(self):
        expected = {
            "2005": ("PSvDBMain::SavWave", None),
            "2105": ("PSvDBMain::SavUsbCue", "4702"),
            "2205": ("PSvDBMain::SavVbrInf (constant-success stub)", None),
            "2305": ("recognized-log-only", None),
            "2405": ("recognized-log-only", None),
            "2505": ("recognized-log-only", None),
            "2605": ("PSvDBMain::SavQtzOfs", "4000"),
            "2705": ("PSvDBMain::SavUsbCueExt", "4E02"),
            "2805": ("PSvDBMain::SaveSpecifiedAtomInfo", "4000"),
            "2905": ("PSvDBMain::UpdateSpecifiedAtomInfo", "4000"),
        }
        for kind, result in expected.items():
            with self.subTest(kind=kind):
                command = self.commands[kind]
                self.assertEqual(
                    (command["rekordbox_target"], command["reply_kind"]), result
                )
                self.assertNotEqual(command["coverage"], "source-vocabulary-only")

        self.assertIn(
            "0x0101aba314  mov       eax, 1",
            self.handlers,
        )
        for kind in ("2305", "2405", "2505"):
            self.assertIn(f"mov       r12d, 0x{kind.lower()}", self.handlers)

    def test_database_modification_dispatch_and_effects_are_exact(self):
        rate = self.commands["2107"]
        self.assertEqual(rate["reply_kind"], "4000")
        self.assertIn("modTrackRate", rate["rekordbox_target"])
        self.assertEqual(rate["dependencies"]["database"], ["djmdContent.Rating"])

        bpm = self.commands["2507"]
        self.assertEqual(bpm["reply_kind"], "4000")
        self.assertIn("modTrackBPM", bpm["rekordbox_target"])
        self.assertEqual(bpm["dependencies"]["database"], ["djmdContent.BPM"])

        rejected = self.commands["2207"]
        self.assertEqual(rejected["coverage"], "rekordbox-static-rejected")
        self.assertIn("recognizes only 2107, 2507", rejected["rejection_reason"])

        for anchor in (
            "select Rating from djmdContent where rb_local_deleted = 0 and ID = %lu",
            "select Bpm from djmdContent where rb_local_deleted = 0 and ID = %lu",
            "__ZNK2db13CloudAgentAPI6CrudIF10updateByIdEjRKN4juce3varE",
        ):
            self.assertIn(anchor, self.db_effects)

    def test_filesystem_writers_and_key_queries_are_anchored(self):
        for anchor in (
            "select * from djmdKey where rb_local_deleted = 0",
            "MstStoreLoudWave",
            "MstStoreDotWave",
            "MstSaveQtzOffset",
            "MstSaveAtomData",
            "MstUpdateAtomData",
            "RetNewCueToClient",
        ):
            evidence = self.handlers + self.db_effects
            self.assertIn(anchor, evidence)

    def test_generated_ledgers_are_byte_identical(self):
        with tempfile.TemporaryDirectory() as directory:
            dispatch = Path(directory) / DISPATCH.name
            vocabulary = Path(directory) / VOCABULARY.name
            subprocess.run(
                ["python3", str(DISPATCH_EXTRACTOR), "--output", str(dispatch)],
                cwd=ROOT,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                [
                    "python3",
                    str(VOCABULARY_GENERATOR),
                    "--output",
                    str(vocabulary),
                ],
                cwd=ROOT,
                check=True,
                capture_output=True,
            )
            self.assertEqual(dispatch.read_bytes(), DISPATCH.read_bytes())
            self.assertEqual(vocabulary.read_bytes(), VOCABULARY.read_bytes())


if __name__ == "__main__":
    unittest.main()
