import json
import os
import sys
import unittest
from pathlib import Path


CONFORMANCE = Path(__file__).resolve().parent
ROOT = CONFORMANCE.parent
sys.path.insert(0, str(ROOT / "tools"))

import summarize_hot_cue_legacy_identical_request_history as history


class HotCueLegacyIdenticalRequestHistoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.declaration = json.loads(history.DECLARATION.read_text())

    def test_declaration_has_complete_interleaved_sequence(self) -> None:
        phases = self.declaration["phases"]
        request_phases = [phase for phase in phases if phase["action"] == "request"]

        self.assertEqual(2, self.declaration["cycles"])
        self.assertEqual(6, len(request_phases))
        self.assertEqual(
            [
                "fresh-vm-canonical",
                "crash-declared-extension-one",
                "after-crash-one-canonical",
                "crash-declared-extension-seven",
                "after-crash-seven-canonical",
                "restart-isolated-vm",
                "after-vm-restart-canonical",
            ],
            [phase["id"] for phase in phases],
        )
        self.assertIn("helper_processes", self.declaration["capture"])
        self.assertIn("tcp_listeners", self.declaration["capture"])

    def test_recorder_enforces_isolation_and_hash_bound_cycles(self) -> None:
        recorder = CONFORMANCE / "record_hot_cue_legacy_identical_request_history.sh"
        source = recorder.read_text()

        self.assertTrue(os.access(recorder, os.X_OK))
        self.assertIn('"$vm/vmctl" isolated-restart', source)
        self.assertIn('"$vm/vmctl" isolation-check', source)
        self.assertIn('"$guestctl" wait 180', source)
        self.assertIn("REKORDBOX_LINK_MAX_ATTEMPTS=1", source)
        self.assertIn("write_phase_receipt", source)
        self.assertIn("write_cycle_receipt", source)
        self.assertIn("phase_receipt_is_complete", source)
        self.assertIn("restart_receipt_is_complete", source)
        self.assertIn("resuming complete phase receipt", source)
        self.assertIn("quarantined incomplete evidence", source)
        self.assertIn(".interrupted-$(date -u +%Y%m%dT%H%M%SZ)", source)
        self.assertIn("Baseline restore encountered a live database handle", source)
        self.assertIn('"$script_dir/activate_fixture.sh" "$baseline"', source)
        self.assertNotIn("SSH_AUTH_SOCK", source)
        self.assertNotIn("rbxport", source.lower())

    def test_health_capture_includes_helpers_and_listeners(self) -> None:
        source = (CONFORMANCE / "capture_rekordbox_health.ps1").read_text()

        self.assertIn("schema_version = 2", source)
        self.assertIn("helper_processes = $helperProcesses", source)
        self.assertIn("helper_process_count = $helperProcesses.Count", source)
        self.assertIn("tcp_listeners = $tcpListeners", source)
        self.assertIn("Get-NetTCPConnection -State Listen", source)

    def test_partial_reducer_declares_every_observation(self) -> None:
        document = history.summarize(allow_partial=True)

        self.assertEqual(2, document["matrix"]["declared_cycles"])
        self.assertEqual(12, document["matrix"]["declared_request_observations"])
        self.assertEqual(4, document["matrix"]["declared_vm_restarts"])
        self.assertEqual(
            self.declaration["canonical_request_signature"],
            document["canonical_request_signature"],
        )

    def test_complete_evidence_preserves_durable_and_lifecycle_repeat_separately(self) -> None:
        document = history.summarize(allow_partial=False)
        phases = {item["phase"]: item for item in document["phase_repeat"]}

        self.assertEqual([1, 2], document["matrix"]["completed_cycles"])
        self.assertEqual(12, document["matrix"]["completed_request_observations"])
        self.assertEqual(4, document["matrix"]["completed_vm_restarts"])
        self.assertTrue(all(item["durable_repeat_verified"] for item in phases.values()))

        self.assertFalse(phases["crash-declared-extension-one"]["lifecycle_repeat_exact"])
        self.assertFalse(phases["crash-declared-extension-seven"]["lifecycle_repeat_exact"])
        self.assertEqual(
            2,
            len(phases["crash-declared-extension-one"]["lifecycle_groups"]),
        )
        self.assertEqual(
            2,
            len(phases["crash-declared-extension-seven"]["lifecycle_groups"]),
        )

        canonical = [
            item
            for phase, item in phases.items()
            if "canonical" in phase
        ]
        self.assertTrue(all(item["lifecycle_repeat_exact"] for item in canonical))
        self.assertEqual(1, len(document["canonical_lifecycle_groups"]))

    def test_every_canonical_phase_has_declared_signature(self) -> None:
        signatures = {
            history.request_signature(phase)
            for phase in self.declaration["phases"]
            if phase["action"] == "request" and "canonical" in phase["id"]
        }

        self.assertEqual({self.declaration["canonical_request_signature"]}, signatures)


if __name__ == "__main__":
    unittest.main()
