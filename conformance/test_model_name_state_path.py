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
CANONICAL = ROOT / "data/static-analysis/model-name-state-path.disasm.txt"
PATTERN = (
    r"(__ZN12InnerLinkAPI(8linkProcEv|12getModelNameEj|12getModelNameEjPcj|"
    r"21noticeModelNameUpdateEh|17receiveLinkMemberEjPKv)|"
    r"__ZN20PSvLinkNetworkAccess12getModelNameEj|"
    r"__ZN20PSvLinkNetworkAccess12getModelNameEjPcj|"
    r"__ZN21PSvLinkNormalInterval(12getModelNameEj|12getModelNameEjPcj|"
    r"15messageReceivedEPKhRKN4juce11MemoryBlockE)|"
    r"__ZN9prodjlink9ProDJLink(17receiveLinkMemberEjN13PSvLinkCommon17PSvLinkDeviceTypeEb|"
    r"12getModelNameEi|21noticeModelNameUpdateEh)|"
    r"__ZN9prodjlink9LinkProxy12getModelNameEjPcj|"
    r"__ZN9prodjlink17LinkDeviceManager13addLinkDevice|"
    r"__ZN6djplay11UiProDJLink21notifyModelNameUpdateEh|"
    r"__ZN9PSvDBMain(5isAIOEh|11clearAIOMapEh))"
)
EXPECTED_BINARY_SHA256 = (
    "07dcecbaf304f777e435539c83c7dcc02e41de1eaf2e0a75e8a9852e4411a244"
)
LINK_PROC_JUMP_TABLE = 0x1003DBD3C
PLAYER_PACKET_JUMP_TABLE = 0x100B785D8
CPU_TYPE_X86_64 = 0x01000007
LC_SEGMENT_64 = 0x19


def read_virtual_bytes(path: Path, address: int, size: int) -> bytes:
    data = path.read_bytes()
    magic, architecture_count = struct.unpack_from(">II", data)
    if magic != 0xCAFEBABE:
        raise ValueError("expected a universal Mach-O binary")

    slice_offset = None
    for index in range(architecture_count):
        cpu_type, _, offset, _, _ = struct.unpack_from(">IIIII", data, 8 + index * 20)
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


class ModelNameStatePathTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.link_jump_table = read_virtual_bytes(BINARY, LINK_PROC_JUMP_TABLE, 0x83 * 4)
        cls.player_jump_table = read_virtual_bytes(
            BINARY, PLAYER_PACKET_JUMP_TABLE, 0x2F * 4
        )

    def jump_target(self, message_type: int) -> int:
        entry = (message_type - 1) * 4
        raw = self.link_jump_table[entry : entry + 4]
        return LINK_PROC_JUMP_TABLE + struct.unpack("<i", raw)[0]

    def player_packet_target(self, packet_kind: int) -> int:
        entry = (packet_kind - 5) * 4
        raw = self.player_jump_table[entry : entry + 4]
        return PLAYER_PACKET_JUMP_TABLE + struct.unpack("<i", raw)[0]

    def test_status_record_owns_model_and_emits_change_notification(self) -> None:
        trace = CANONICAL.read_text()

        self.assertEqual(
            EXPECTED_BINARY_SHA256,
            hashlib.sha256(BINARY.read_bytes()).hexdigest(),
        )
        for fragment in (
            "PSvLinkNormalInterval15messageReceived",
            "PSvLinkPlayerLinkInfo7setData",
            "add       rsi, 0x233",
            "add       rsi, 0x7f3",
            "mov       esi, 0x6e",
            "PSvLinkMessageManager13appendMessage",
        ):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, trace)

        self.assertEqual(0x1003DB980, self.jump_target(0x6E))
        self.assertEqual(0x100B76F7D, self.player_packet_target(0x0A))
        self.assertIn(
            "call      0x1003dce20  ; __ZN12InnerLinkAPI21noticeModelNameUpdateEh",
            trace,
        )

    def test_membership_and_model_update_are_distinct_message_paths(self) -> None:
        trace = CANONICAL.read_text()

        self.assertEqual(0x1003DAE17, self.jump_target(0x04))
        self.assertIn(
            "call      0x1003dd5f0  ; __ZN12InnerLinkAPI17receiveLinkMemberEjPKv",
            trace,
        )
        self.assertIn(
            "call      0x100e39670  ; __ZN9prodjlink9LinkProxy12getModelNameEjPcj",
            trace,
        )

    def test_model_getter_reads_the_same_per_player_status_record(self) -> None:
        trace = CANONICAL.read_text()

        for fragment in (
            "imul      rax, rax, 0xb8",
            "add       rbx, 0x233",
            "add       rbx, 0x1093",
            "PSvLinkNetworkAccess12getModelNameEjPcj",
            "PSvLinkNormalInterval12getModelNameEjPcj",
            "ProDJLink12getModelNameEi",
            "PSvDBMain5isAIOEh",
        ):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, trace)

    def test_documents_state_the_status_ownership_and_cache_boundary(self) -> None:
        documents = {
            name: (ROOT / name).read_text()
            for name in (
                "DEVICE_COMPATIBILITY.md",
                "DEVICE_PREDICATE_AUDIT.md",
                "DEVICE_STATUS_PROVENANCE.md",
                "STATIC_ANALYSIS.md",
            )
        }

        for name, text in documents.items():
            with self.subTest(document=name):
                self.assertIn("message type `0x6e`", text)

        self.assertIn(
            "membership and model availability are separate state transitions",
            documents["DEVICE_COMPATIBILITY.md"],
        )
        self.assertIn(
            "does not itself populate the model buffer",
            documents["DEVICE_PREDICATE_AUDIT.md"],
        )
        self.assertIn(
            "status parser owns the model buffer",
            documents["DEVICE_STATUS_PROVENANCE.md"],
        )

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
