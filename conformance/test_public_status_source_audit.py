import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "data/static-analysis/public-status-source-audit.json"
PACKET_PATH = (
    ROOT
    / "conformance/status-packets/cdj-2000nexus-player-3-firmware-1.43.hex"
)
OPUS_PACKET_PATH = (
    ROOT / "conformance/status-packets/opus-quad-first-50002.hex"
)
XDJ_XZ_PACKET_PATHS = (
    ROOT / "conformance/status-packets/xdj-xz-player-1-analyzed-status-20260422.hex",
    ROOT / "conformance/status-packets/xdj-xz-player-1-unanalyzed-status-20260422.hex",
)


class PublicStatusSourceAuditTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit = json.loads(AUDIT_PATH.read_text())
        cls.repositories = {
            repository["name"]: repository
            for repository in cls.audit["repositories"]
        }

    def test_every_audited_repository_is_pinned_and_classified(self):
        self.assertEqual(
            set(self.repositories),
            {
                "prodjlink-rs",
                "alphatheta-connect",
                "prolink-cpp",
                "usr-ein/prolink",
                "beat-link",
                "SuperTimecodeConverter",
                "opus-quad-pro-dj-link-analysis",
                "Conduction",
                "netBeat",
            },
        )

        for repository in self.repositories.values():
            self.assertRegex(repository["commit"], r"^[0-9a-f]{40}$")
            self.assertTrue(repository["classification"])
            self.assertTrue(repository["evidence"])

    def test_modeled_and_constructed_sources_are_not_eligible(self):
        for name in ("prodjlink-rs", "prolink-cpp"):
            self.assertEqual(self.repositories[name]["eligible_payloads"], 0)

    def test_corroborating_packet_matches_declared_bytes_and_identity(self):
        retained = self.repositories["alphatheta-connect"]["retained_payload"]
        packet = bytes.fromhex(PACKET_PATH.read_text())

        self.assertEqual(len(packet), retained["bytes"])
        self.assertEqual(hashlib.sha256(packet).hexdigest(), retained["sha256"])
        self.assertEqual(packet[0x0B:0x1F].rstrip(b"\0"), b"CDJ-2000nexus")
        self.assertEqual(packet[0x21], retained["player"])
        self.assertIn(retained["firmware"].encode(), packet)
        self.assertEqual(retained["provenance_tier"], "corroborating_fixture")

    def test_unresolved_set_does_not_claim_modeled_fixtures(self):
        self.assertEqual(self.audit["result"]["new_modern_native_payloads"], 0)
        self.assertEqual(self.audit["result"]["modern_capture_leads"], 1)
        self.assertEqual(
            set(self.audit["result"]["unresolved_models"]),
            {
                "XDJ-XZ",
                "XDJ-AZ",
                "XDJ-1000MK2",
                "XDJ-RR",
                "XDJ-RX2",
                "OPUS-QUAD",
                "CDJ-3000",
            },
        )

    def test_xdj_xz_lead_is_not_promoted_without_local_bytes(self):
        repository = self.repositories["SuperTimecodeConverter"]
        lead = repository["acquisition_lead"]

        self.assertEqual(repository["eligible_payloads"], 0)
        self.assertEqual(lead["model"], "XDJ-XZ")
        self.assertEqual(lead["provenance_tier"], "source-lead-only")
        self.assertIn("requires Google sign-in", lead["access_state"])

    def test_opus_quad_packet_is_retained_but_not_promoted_as_status(self):
        repository = self.repositories["opus-quad-pro-dj-link-analysis"]
        retained = repository["retained_nonstatus_payload"]
        packet = bytes.fromhex(OPUS_PACKET_PATH.read_text())

        self.assertEqual(repository["eligible_payloads"], 0)
        self.assertEqual(len(packet), retained["bytes"])
        self.assertEqual(hashlib.sha256(packet).hexdigest(), retained["sha256"])
        self.assertEqual(packet[:10], b"Qspt1WmJOL")
        self.assertEqual(packet[10], 0x10)
        self.assertEqual(packet[11:31].rstrip(b"\0"), b"OPUS-QUAD")
        self.assertFalse(retained["status_matrix_eligible"])
        self.assertEqual(self.audit["result"]["modern_nonstatus_payloads"], 1)

    def test_conduction_does_not_relabel_reference_vectors_as_captures(self):
        repository = self.repositories["Conduction"]

        self.assertEqual(repository["eligible_payloads"], 0)
        self.assertIn("provenance", repository["classification"])
        self.assertTrue(
            any("transcribed references" in item for item in repository["evidence"])
        )

    def test_xdj_xz_hardware_status_fixtures_are_retained_but_not_overpromoted(self):
        repository = self.repositories["netBeat"]
        retained = repository["retained_payloads"]

        self.assertEqual(repository["eligible_payloads"], 0)
        self.assertEqual(2, len(retained))
        self.assertEqual(2, self.audit["result"]["modern_status_fixtures"])
        self.assertEqual(3, self.audit["result"]["new_corroborating_payloads"])

        for path, declaration in zip(XDJ_XZ_PACKET_PATHS, retained, strict=True):
            packet = bytes.fromhex(path.read_text())
            self.assertEqual(292, len(packet))
            self.assertEqual(0x0A, packet[10])
            self.assertEqual(b"XDJ-XZ", packet[11:31].rstrip(b"\0"))
            self.assertEqual(1, packet[0x21])
            self.assertEqual(declaration["sha256"], hashlib.sha256(packet).hexdigest())
            self.assertEqual("corroborating-fixture", declaration["provenance_tier"])

    def test_stagehand_capture_lead_is_kept_out_of_status_evidence(self):
        leads = self.audit["reviewed_nonqualifying_leads"]
        self.assertEqual(len(leads), 1)

        lead = leads[0]
        self.assertEqual(lead["model"], "CDJ-3000")
        self.assertEqual(lead["firmware"], "3.18")
        self.assertRegex(lead["commit"], r"^[0-9a-f]{40}$")
        self.assertEqual(lead["eligible_payloads"], 0)
        self.assertFalse(lead["retained_capture_bytes"])
        self.assertIn("Stagehand", lead["protocol_plane"])
        self.assertIn("outside", lead["classification"])


if __name__ == "__main__":
    unittest.main()
