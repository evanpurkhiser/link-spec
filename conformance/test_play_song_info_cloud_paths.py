import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "tools/audit_play_song_info_cloud_paths.py"
OUTPUT = ROOT / "data/static-analysis/play-song-info-cloud-paths.json"
DISASSEMBLY = ROOT / "data/static-analysis/play-song-info-cloud-paths.disasm.txt"
GENERATOR = ROOT / "conformance/generate_cloud_sync_zero_suite.py"
SUITE = ROOT / "conformance/suites/generated/song-info-cloud-sync-zero.json"
FIXTURE = ROOT / "conformance/fixtures/generated/cloud-sync-zero/manifest.json"
RECORDER = ROOT / "conformance/record_play_song_info_cloud_sync_zero.sh"
REDUCER = ROOT / "tools/summarize_play_song_info_cloud_sync_zero.py"
FINALIZER = ROOT / "conformance/run_play_song_info_cloud_sync_zero_after_provider_paths.sh"


class PlaySongInfoCloudPathTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = json.loads(OUTPUT.read_text())

    def test_generation_is_byte_identical(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "audit.json"
            disassembly = Path(directory) / "audit.disasm.txt"
            subprocess.run(
                [
                    str(ROOT / ".venv/bin/python"),
                    str(AUDIT),
                    "--output",
                    str(output),
                    "--disassembly-output",
                    str(disassembly),
                ],
                check=True,
                capture_output=True,
            )
            self.assertEqual(OUTPUT.read_bytes(), output.read_bytes())
            self.assertEqual(DISASSEMBLY.read_bytes(), disassembly.read_bytes())

    def test_sync_method_has_only_two_link_export_classes(self):
        method = self.document["sync_method"]
        self.assertEqual(1, method["default"])
        self.assertEqual(
            [
                {
                    "address": "0x1016c1a79",
                    "owner": "PSvAppSyncDBIF::getPlaySongInf",
                }
            ],
            method["binary_direct_call_sites"],
        )
        self.assertEqual(
            "the complete x86-64 __TEXT,__text section",
            method["direct_call_scope"],
        )
        self.assertEqual("zero versus nonzero", method["decision"])
        self.assertEqual(
            ["zero", "nonzero"],
            [item["name"] for item in method["equivalence_classes"]],
        )
        self.assertFalse(self.document["live_oracle_boundary"]["other_integer_values_needed"])

    def test_branches_use_distinct_filesystem_roots_and_predicates(self):
        self.assertIn("regular file", self.document["nonzero_branch"]["first_preference"])
        self.assertEqual(0, self.document["nonzero_branch"]["download_folder_path_calls"])
        self.assertIn("any filesystem object", self.document["zero_branch"]["first_preference"])
        self.assertEqual(
            3,
            len(self.document["zero_branch"]["download_folder_path_call_sites"]),
        )

    def test_service_domains_are_explicit(self):
        domains = self.document["service_domains"]
        share = domains["share_path"]
        self.assertEqual("0 through 4", share["switch_domain"])
        self.assertEqual(
            [
                "empty string",
                "current master-database directory + /share",
                "Dropbox local public path + /rekordbox",
                "Google Drive local public path + /rekordbox",
                "OneDrive local public path + /rekordbox",
            ],
            [item["root"] for item in share["service_ids"]],
        )
        self.assertEqual(
            "36ffffffdbfdffff24feffff7bfeffffcffeffff",
            share["jump_table_bytes"],
        )
        self.assertEqual([0, 2, 3, 4, 5], domains["download_folder_path"]["accepted_service_ids"])
        self.assertEqual("MovedFromCloudDir", domains["download_folder_path"]["setting"])
        self.assertEqual(
            "PioneerDJ/Moved from Cloud",
            domains["download_folder_path"]["default"]["child_path"],
        )

    def test_protocol_docs_state_the_exact_remaining_live_class(self):
        path_oracle = (ROOT / "PLAY_SONG_INFO_PATH_ORACLE.md").read_text()
        protocol = (ROOT / "PROTOCOL_REFERENCE.md").read_text()
        gaps = (ROOT / "REKORDBOX_RESEARCH_GAPS.md").read_text()
        for document in (path_oracle, protocol, gaps):
            self.assertIn("CLSSyncMethod=0", document)
        for fragment in (
            "Current master-database directory plus `/share`",
            "Dropbox local public path plus `/rekordbox`",
            "Google Drive local public path plus `/rekordbox`",
            "OneDrive local public path plus `/rekordbox`",
        ):
            self.assertIn(fragment, path_oracle)
        self.assertNotIn(
            "A follow-up stored-scale numeric profile is required",
            (ROOT / "EXPERIMENTS.md").read_text(),
        )

    def test_live_suite_regenerates_byte_identically(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "suite.json"
            source = GENERATOR.read_text().replace(
                'OUTPUT = ROOT / "suites/generated/song-info-cloud-sync-zero.json"',
                f'OUTPUT = Path({str(output)!r})',
            )
            candidate = Path(directory) / "generator.py"
            candidate.write_text(source)
            subprocess.run(
                [str(ROOT / ".venv/bin/python"), candidate],
                check=True,
                capture_output=True,
            )
            self.assertEqual(SUITE.read_bytes(), output.read_bytes())

    def test_live_suite_covers_every_fixture_track_without_predictions(self):
        fixture = json.loads(FIXTURE.read_text())
        suite = json.loads(SUITE.read_text())
        self.assertEqual("cloud-sync-zero", fixture["profile"])
        self.assertEqual(10, fixture["track_count"])
        self.assertEqual(10, len(suite["cases"]))
        self.assertTrue(
            all(case["expect"] == {"outcome": "any"} for case in suite["cases"])
        )

    def test_recorder_owns_and_restores_the_two_guest_settings(self):
        recorder = RECORDER.read_text()
        self.assertIn("CLSSyncMethod", recorder)
        self.assertIn("MovedFromCloudDir", recorder)
        self.assertIn("snapshot_settings", recorder)
        self.assertIn("restore_settings", recorder)
        self.assertIn("record repeat", recorder)
        self.assertNotIn("rbxport", recorder.lower())

    def test_reducer_is_authority_first(self):
        reducer = REDUCER.read_text()
        self.assertIn("observed rows are canonical", reducer)
        self.assertIn("static evidence classifies but does not replace them", reducer)
        self.assertNotIn("rbxport", reducer.lower())

    def test_finalizer_waits_for_provider_paths_and_stops_the_vm(self):
        finalizer = FINALIZER.read_text()
        self.assertIn("codex-rekordbox-streaming-provider-paths-20261004at18.service", finalizer)
        self.assertIn("record_play_song_info_cloud_sync_zero.sh", finalizer)
        self.assertIn("summarize_play_song_info_cloud_sync_zero.py", finalizer)
        self.assertIn("test_real_rekordbox_phase_boundary", finalizer)
        self.assertIn('"$vm/vmctl" isolated-stop', finalizer)
        self.assertNotIn("rbxport", finalizer.lower())


if __name__ == "__main__":
    unittest.main()
