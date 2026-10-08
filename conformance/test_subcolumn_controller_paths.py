import hashlib
import struct
import subprocess
import tempfile
import unittest
from pathlib import Path

import lief


ROOT = Path(__file__).resolve().parent.parent
BINARY = (
    ROOT.parent
    / "artifacts/rekordbox/7.2.19/extracted/app-root/rekordbox.app/Contents/MacOS/rekordbox"
)
TOOL = ROOT / "tools/disassemble_symbols.py"
CANONICAL = ROOT / "data/static-analysis/subcolumn-controller-paths.disasm.txt"
PATTERN = (
    r"(DevSqliteDBController|AppSyncDBController|rekordboxDBController)"
    r"(14getSortSetting|14resetSubColumn|12setSubColumn)"
    r"|_(DEV|MAS)_MODULE6_(DEV|MST)(RESET|SET)SUBCOLUMN"
)
EXPECTED_BINARY_SHA256 = (
    "07dcecbaf304f777e435539c83c7dcc02e41de1eaf2e0a75e8a9852e4411a244"
)
APPSYNC_VTABLE = 0x1055D9000
APPSYNC_RESET_SUBCOLUMN = 0x100B4A890


class SubcolumnControllerPathsTests(unittest.TestCase):
    def test_trace_binds_every_reader_writer_and_exact_appsync_sql(self) -> None:
        trace = CANONICAL.read_text()

        self.assertEqual(
            EXPECTED_BINARY_SHA256,
            hashlib.sha256(BINARY.read_bytes()).hexdigest(),
        )
        for owner in (
            "DevSqliteDBController14getSortSetting",
            "DevSqliteDBController14resetSubColumn",
            "DevSqliteDBController12setSubColumn",
            "AppSyncDBController14getSortSetting",
            "AppSyncDBController14resetSubColumn",
            "AppSyncDBController12setSubColumn",
            "rekordboxDBController14getSortSetting",
            "rekordboxDBController14resetSubColumn",
            "rekordboxDBController12setSubColumn",
        ):
            with self.subTest(owner=owner):
                self.assertIn(owner, trace)

        for sql in (
            "select * from djmdSort where rb_local_deleted = 0 order by Seq",
            "Disable = (Disable & ~0x02)",
            "where rb_local_deleted = 0 and (Disable & 0x02)",
            "Disable = (Disable | 0x02)",
            "and ID = %lu",
            "where rb_local_deleted = 0 and ID != %lu",
        ):
            with self.subTest(sql=sql):
                self.assertIn(sql, trace)

        self.assertIn("ERROR Right Column multiply-selected", trace)
        self.assertIn("call      qword ptr [rax + 0xfe0]", trace)

    def test_appsync_setter_calls_reset_vtable_slot_before_setting(self) -> None:
        fat = lief.MachO.parse(str(BINARY))
        binary = next(
            item
            for item in fat
            if item.header.cpu_type == lief.MachO.Header.CPU_TYPE.X86_64
        )
        address = APPSYNC_VTABLE + 0x10 + 0xFE0
        raw = bytes(binary.get_content_from_virtual_address(address, 8))

        self.assertEqual(APPSYNC_RESET_SUBCOLUMN, struct.unpack("<Q", raw)[0])

    def test_documents_keep_preferences_and_renderer_ordering_distinct(self) -> None:
        documents = {
            name: (ROOT / name).read_text()
            for name in (
                "CONFIGURATION.md",
                "DATABASE_QUERIES.md",
                "PROTOCOL_REFERENCE.md",
                "SECONDARY_COLUMNS.md",
                "SECONDARY_COLUMN_ORACLE.md",
            )
        }

        self.assertIn(
            "first selected ID in `Seq` order", documents["CONFIGURATION.md"]
        )
        self.assertIn(
            "query has no `ORDER BY` and consumes row zero",
            documents["CONFIGURATION.md"],
        )
        self.assertIn(
            "do not share a selected-row", documents["SECONDARY_COLUMNS.md"]
        )
        for name in (
            "DATABASE_QUERIES.md",
            "PROTOCOL_REFERENCE.md",
            "SECONDARY_COLUMN_ORACLE.md",
        ):
            with self.subTest(document=name):
                self.assertIn("Preferences", documents[name])
                self.assertIn("multiple", documents[name])

    def test_regeneration_is_byte_identical(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "trace.txt"
            subprocess.run(
                [
                    str(ROOT / ".venv/bin/python"),
                    str(TOOL),
                    str(BINARY),
                    PATTERN,
                    "--output",
                    str(output),
                ],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertEqual(output.read_bytes(), CANONICAL.read_bytes())


if __name__ == "__main__":
    unittest.main()
