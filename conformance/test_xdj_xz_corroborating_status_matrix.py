import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MATRIX = ROOT / "data/xdj-xz-corroborating-status-matrix.json"
ANALYZED_SHA256 = "8eadeb284e6c0ed167cd1573ba0ed976d5c1abd85694de1299224b54519ff90f"
UNANALYZED_SHA256 = "f596f7ed8e34b5b9ca16e3fc9a50c5d59118308f8055a9514e4562474051ff7b"


class XdjXzCorroboratingStatusMatrixTests(unittest.TestCase):
    def test_source_packets_and_identity_are_exact_but_corroborating(self) -> None:
        matrix = json.loads(MATRIX.read_text())
        identity = json.loads((ROOT / matrix["identity"]).read_text())

        packets = (
            (matrix["status_packet"], ANALYZED_SHA256),
            (
                "status-packets/xdj-xz-player-1-unanalyzed-status-20260422.hex",
                UNANALYZED_SHA256,
            ),
        )
        for relative, expected in packets:
            packet = bytes.fromhex("".join((ROOT / relative).read_text().split()))
            self.assertEqual(292, len(packet))
            self.assertEqual(expected, hashlib.sha256(packet).hexdigest())
            self.assertEqual(0x0A, packet[0x0A])
            self.assertEqual(b"XDJ-XZ", packet[0x0B:0x11])
            self.assertEqual(1, packet[0x21])

        self.assertEqual("XDJ-XZ", identity["model"])
        self.assertEqual(1, identity["player"])
        self.assertEqual("cdj", identity["device_type"])
        self.assertEqual(2, identity["generation"])
        self.assertEqual(100, identity["model_code"])
        self.assertEqual(292, identity["status_packet_bytes"])
        self.assertEqual(ANALYZED_SHA256, identity["status_packet_sha256"])
        self.assertEqual("corroborating-fixture", identity["status_provenance"])

    def test_matrix_declares_complete_status_cross(self) -> None:
        matrix = json.loads(MATRIX.read_text())
        self.assertEqual(13, len(matrix["variants"]))
        self.assertIn("corroborating XDJ-XZ", matrix["scope"])

        total_cases = 0
        goldens = []
        for variant in matrix["variants"]:
            suite = json.loads((ROOT / variant["suite"]).read_text())
            manifest = ROOT / f"fixtures/generated/{variant['fixture']}/manifest.json"
            self.assertTrue(manifest.is_file(), variant["fixture"])
            self.assertEqual(variant["fixture"], suite["fixture_profile"])
            total_cases += len(suite["cases"])
            goldens.append(variant["golden"])

        self.assertEqual(249, total_cases)
        self.assertEqual(len(goldens), len(set(goldens)))
        for golden in goldens:
            self.assertTrue(
                golden.startswith(
                    "goldens/rekordbox-7.2.19/xdj-xz-corroborating-status/"
                )
            )

    def test_declaration_never_claims_captured_verbatim_provenance(self) -> None:
        declaration = MATRIX.read_text()
        identity = (ROOT / "runs/xdj-xz-player-1-corroborating-status.json").read_text()
        self.assertNotIn("captured-verbatim", declaration)
        self.assertNotIn("captured-verbatim", identity)


if __name__ == "__main__":
    unittest.main()
