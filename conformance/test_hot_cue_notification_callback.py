import hashlib
import struct
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
BINARY = (
    ROOT.parent
    / "artifacts/rekordbox/7.2.19/extracted/app-root/rekordbox.app/Contents/MacOS/rekordbox"
)
TOOL = ROOT / "tools/disassemble_symbols.py"
GENERATED_TRACE = ROOT / "data/static-analysis/hot-cue-bank-notifications.disasm.txt"
FOCUSED_TRACE = (
    ROOT / "data/static-analysis/hot-cue-bank-notification-callback.disasm.txt"
)
PATTERN = (
    r"PSvDBMain(16DeliverCueUpdate|20DeliverTagListUpdate|"
    r"19DeliverHCBankUpdate|21DeliverPlaylistUpdate|19DeliverRatingUpdate|"
    r"16DeliverBpmUpdate|21DeliverGetHotCueEvent)"
)
EXPECTED_BINARY_SHA256 = (
    "07dcecbaf304f777e435539c83c7dcc02e41de1eaf2e0a75e8a9852e4411a244"
)
EXPECTED_GENERATED_TRACE_SHA256 = (
    "ba966e5ef304dc2ee647e86959cb6776bdbd8fe4305e57f58ef94176070970ac"
)
EXPECTED_FOCUSED_TRACE_SHA256 = (
    "80782047c29dc1344cf6b03a8e0edb4e54c3552f48409048d5377d975db746ad"
)
CALLBACK_CLASS_TABLE = 0x1017B4EC0
CPU_TYPE_X86_64 = 0x01000007
LC_SEGMENT_64 = 0x19


def read_virtual_bytes(path: Path, address: int, size: int) -> bytes:
    data = path.read_bytes()
    magic, architecture_count = struct.unpack_from(">II", data)
    if magic != 0xCAFEBABE:
        raise ValueError("expected a universal Mach-O binary")

    slice_offset = None
    for index in range(architecture_count):
        cpu_type, _, offset, _, _ = struct.unpack_from(
            ">IIIII", data, 8 + index * 20
        )
        if cpu_type == CPU_TYPE_X86_64:
            slice_offset = offset
            break
    if slice_offset is None:
        raise ValueError("x86-64 Mach-O slice is missing")

    magic, _, _, _, command_count, _, _, _ = struct.unpack_from(
        "<IIIIIIII", data, slice_offset
    )
    if magic != 0xFEEDFACF:
        raise ValueError("expected a 64-bit little-endian Mach-O slice")

    command_offset = slice_offset + 32
    for _ in range(command_count):
        command, command_size = struct.unpack_from("<II", data, command_offset)
        if command == LC_SEGMENT_64:
            vm_address, _, file_offset, file_size = struct.unpack_from(
                "<QQQQ", data, command_offset + 24
            )
            if vm_address <= address and address + size <= vm_address + file_size:
                start = slice_offset + file_offset + address - vm_address
                return data[start : start + size]
        command_offset += command_size

    raise ValueError(f"virtual address {address:#x} is not file-backed")


class HotCueNotificationCallbackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.focused_trace = FOCUSED_TRACE.read_text()
        cls.class_table = read_virtual_bytes(BINARY, CALLBACK_CLASS_TABLE, 7 * 4)

    def class_target(self, update_class: int) -> int:
        entry = update_class * 4
        relative = struct.unpack("<i", self.class_table[entry : entry + 4])[0]
        return CALLBACK_CLASS_TABLE + relative

    def test_sources_and_reviewed_trace_are_pinned(self) -> None:
        self.assertEqual(
            EXPECTED_BINARY_SHA256,
            hashlib.sha256(BINARY.read_bytes()).hexdigest(),
        )
        self.assertEqual(
            EXPECTED_GENERATED_TRACE_SHA256,
            hashlib.sha256(GENERATED_TRACE.read_bytes()).hexdigest(),
        )
        self.assertEqual(
            EXPECTED_FOCUSED_TRACE_SHA256,
            hashlib.sha256(FOCUSED_TRACE.read_bytes()).hexdigest(),
        )

    def test_callback_installation_and_delivery_are_exact(self) -> None:
        for fragment in (
            "0x1017b30ae  lea  rdx, [r13 + 0x18]",
            "call 0x101c5afe0 ; PSvDBServer::Initialize",
            "call 0x10251fc60 ; PSvDBMain::SetCallback",
            "mov  qword ptr [rdi + 0x5c0], rsi",
            "0x102521014  test byte ptr [rdi + 0x5c8], 2",
            "mov  rax, qword ptr [rax + 0x30]",
            "mov  esi, 3",
        ):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, self.focused_trace)

    def test_callback_class_three_maps_to_hot_cue_database_update(self) -> None:
        self.assertEqual(
            [
                0x1017B4E9A,
                0x1017B4E5C,
                0x1017B4E67,
                0x1017B4E74,
                0x1017B4E7E,
                0x1017B4E88,
                0x1017B4E92,
            ],
            [self.class_target(update_class) for update_class in range(7)],
        )
        for fragment in (
            "0x1017b4e74  xor  r15d, r15d",
            "0x1017b4e77  mov  ebx, 0x1e",
            "0x1017b4ebb  jmp  0x102357a20 ; db::DatabaseIF::notifyDBUpdated",
            "DatabaseIF::notifyDBUpdated(0x1e, CueID, 0)",
        ):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, self.focused_trace)

    def test_generated_delivery_trace_is_byte_identical(self) -> None:
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
            self.assertEqual(output.read_bytes(), GENERATED_TRACE.read_bytes())

    def test_oracles_keep_the_protocol_boundary_explicit(self) -> None:
        hot_cue_oracle = (ROOT / "HOT_CUE_BANK_ORACLE.md").read_text()
        gap_matrix = (ROOT / "GAP_MATRIX.md").read_text()

        self.assertRegex(hot_cue_oracle, r"with no\s+Link Export packet")
        self.assertIn("statically closed in-process setter callback", gap_matrix)


if __name__ == "__main__":
    unittest.main()
