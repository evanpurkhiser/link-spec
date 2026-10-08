import hashlib
import json
import unittest
from pathlib import Path

import replay_rbxport


ROOT = Path(__file__).resolve().parent
ACTIVE_QUEUE_SCRIPTS = (
    "record_hot_cue_declared_length_ffffffff_lifecycle.sh",
    "record_hot_cue_slot_8_lifecycle.sh",
    "record_hot_cue_extended_setter_parser_matrix.sh",
    "record_hot_cue_legacy_setter_parser_matrix.sh",
    "record_hot_cue_bank_buffer_disconnect.sh",
    "record_cdj_2000nexus_status_matrix.sh",
    "record_secondary_legacy_matrix.sh",
    "record_bpm_tolerance_boundaries.sh",
    "record_hot_cue_extended_setter_field_matrix.sh",
    "record_hot_cue_extended_setter_seek_matrix.sh",
    "run_remaining_real_rekordbox_queue.sh",
    "run_after_setter_fields.sh",
    "finalize_real_rekordbox_queue.sh",
    "record_hot_cue_legacy_identical_request_history.sh",
    "run_identical_history_after_queue.sh",
    "run_track_compatibility_after_queue.sh",
    "record_status_location2_malformed_history_matrix.sh",
    "run_status_location2_malformed_history_after_compatibility.sh",
    "record_adjacent_payload_fileless.sh",
    "run_adjacent_payload_after_queue.sh",
    "record_adjacent_payload_malformed.sh",
    "run_adjacent_payload_malformed_after_fileless.sh",
    "record_adjacent_payload_missing_files.sh",
    "run_adjacent_payload_missing_files_after_malformed.sh",
    "record_adjacent_payload_success.sh",
    "run_adjacent_payload_success_after_missing_files.sh",
    "record_adjacent_payload_success_status_cross.sh",
    "run_adjacent_payload_success_status_after_history.sh",
    "record_adjacent_payload_boundary_matrix.sh",
    "run_adjacent_payload_boundaries_after_status.sh",
    "record_adjacent_payload_cue_matrix.sh",
    "run_adjacent_payload_cues_after_boundaries.sh",
    "record_xdj_rr_location9_matrix.sh",
    "run_xdj_rr_location9_after_cues.sh",
    "record_xdj_rr_old_key_matrix.sh",
    "run_xdj_rr_old_key_after_location9.sh",
    "record_xdj_xz_corroborating_status_matrix.sh",
    "run_xdj_xz_corroborating_status_after_old_key.sh",
    "record_hot_cue_bank_buffer_link_toggle.sh",
    "run_hot_cue_buffer_link_toggle_after_xdj_xz.sh",
    "record_sort_secondary_render_5.sh",
    "run_sort_secondary_render_5_after_multiplayer.sh",
    "record_sort_secondary_render_7.sh",
    "run_sort_secondary_render_7_after_render_5.sh",
    "record_render_arity_boundaries.sh",
    "run_render_arity_boundaries_after_render_7.sh",
    "record_render_arity_underflow.sh",
    "run_render_arity_underflow_after_boundaries.sh",
    "record_render_argument_type_matrix.sh",
    "run_render_argument_type_matrix_after_underflow.sh",
    "record_render_numeric_fields.sh",
    "run_render_numeric_fields_after_argument_types.sh",
    "record_render_override_controls.sh",
    "run_render_override_controls_after_numeric_fields.sh",
    "record_status_location2_malformed_history_timing.sh",
    "run_status_location2_malformed_history_timing.sh",
    "arm_post_lifecycle_queue.sh",
    "record_physical_rx3_session_envelope.sh",
    "run_physical_rx3_session_envelope_after_cloud_sync.sh",
)


class RealRekordboxPhaseBoundaryTest(unittest.TestCase):
    def test_rx3_sort_secondary_oracle_is_not_registered_for_backend_replay(self) -> None:
        identity = ("xdj-rx3", "sort-secondary-render-6")
        self.assertNotIn(
            identity,
            {(replay.model, replay.suite) for replay in replay_rbxport.REPLAYS},
        )
        self.assertIn(identity, replay_rbxport.DEFERRED_REPLAYS)
        self.assertFalse(
            any(
                path.is_file()
                for path in (ROOT / "results/rbxport").glob(
                    "*/xdj-rx3/sort-secondary-render-6.json"
                )
            )
        )

    def test_post_lifecycle_queue_arms_every_successor_once(self) -> None:
        launcher_path = ROOT / "arm_post_lifecycle_queue.sh"
        launcher = launcher_path.read_text()
        receipt = json.loads(
            (ROOT.parent / "data/experiments/post-lifecycle-queue-arming.json").read_text()
        )

        self.assertTrue(launcher_path.stat().st_mode & 0o100)
        self.assertIn(
            "codex-rekordbox-song-info-malformed-history-lifecycle-20261004z27.service",
            launcher,
        )
        self.assertEqual(18, launcher.count(".service|"))
        self.assertEqual(1, launcher.count("systemd-run --user --collect"))
        self.assertIn('RuntimeMaxSec=$runtime', launcher)
        self.assertIn('!= not-found', launcher)
        self.assertIn('!= active', launcher)
        self.assertIn('record-active', launcher)
        self.assertIn('post-lifecycle-queue-arming.json', launcher)
        self.assertIn('stage_count:18,all_active:true', launcher)
        self.assertNotIn("rbxport", launcher.lower())

        expected_units = [
            line.split("|", 1)[0]
            for line in launcher.splitlines()
            if line.startswith("codex-rekordbox-") and ".service|" in line
        ]
        self.assertEqual(1, receipt["format"])
        self.assertEqual(18, receipt["stage_count"])
        self.assertTrue(receipt["all_active"])
        self.assertEqual(
            hashlib.sha256(launcher_path.read_bytes()).hexdigest(),
            receipt["launcher_sha256"],
        )
        self.assertEqual(expected_units, [stage["unit"] for stage in receipt["stages"]])
        self.assertEqual(18, len({stage["invocation_id"] for stage in receipt["stages"]}))
        self.assertTrue(all(stage["active"] for stage in receipt["stages"]))

    def test_post_lifecycle_chain_defaults_are_one_current_generation(self) -> None:
        predecessors = {
            "run_adjacent_payload_success_status_after_history.sh":
                "codex-rekordbox-song-info-malformed-history-lifecycle-20261004z27.service",
            "run_adjacent_payload_boundaries_after_status.sh":
                "codex-rekordbox-adjacent-success-status-20261003aa18.service",
            "run_adjacent_payload_cues_after_boundaries.sh":
                "codex-rekordbox-adjacent-boundaries-20261003ab18.service",
            "run_xdj_rr_location9_after_cues.sh":
                "codex-rekordbox-adjacent-cues-20261003ac18.service",
            "run_xdj_rr_old_key_after_location9.sh":
                "codex-rekordbox-xdj-rr-location9-20261003ad18.service",
            "run_xdj_xz_corroborating_status_after_old_key.sh":
                "codex-rekordbox-xdj-rr-old-key-20261003ae18.service",
            "run_hot_cue_buffer_link_toggle_after_xdj_xz.sh":
                "codex-rekordbox-xdj-xz-corroborating-20261003af18.service",
            "run_link_played_state_after_buffer_toggle.sh":
                "codex-rekordbox-hot-cue-buffer-link-toggle-20261003ag18.service",
            "run_link_played_persistence_after_transition.sh":
                "codex-rekordbox-link-played-state-20261003ah18.service",
            "run_link_played_link_toggle_after_persistence.sh":
                "codex-rekordbox-link-played-persistence-20261003ai18.service",
            "run_link_played_multiplayer_after_link_toggle.sh":
                "codex-rekordbox-link-played-link-toggle-20261003aj18.service",
            "run_sort_secondary_render_5_after_multiplayer.sh":
                "codex-rekordbox-link-played-multiplayer-20261003ak18.service",
            "run_sort_secondary_render_7_after_render_5.sh":
                "codex-rekordbox-sort-secondary-render-5-20261003al18.service",
            "run_render_arity_boundaries_after_render_7.sh":
                "codex-rekordbox-sort-secondary-render-7-20261003am18.service",
            "run_render_arity_underflow_after_boundaries.sh":
                "codex-rekordbox-render-arity-boundaries-20261003an18.service",
            "run_render_argument_type_matrix_after_underflow.sh":
                "codex-rekordbox-render-arity-underflow-20261003ao18.service",
            "run_render_numeric_fields_after_argument_types.sh":
                "codex-rekordbox-render-argument-types-20261003ap18.service",
            "run_render_override_controls_after_numeric_fields.sh":
                "codex-rekordbox-render-numeric-fields-20261003aq18.service",
        }

        for script, predecessor in predecessors.items():
            with self.subTest(script=script):
                self.assertIn(predecessor, (ROOT / script).read_text())

    def test_physical_rx3_envelope_waits_for_cloud_sync_authority(self) -> None:
        handoff_path = ROOT / "run_physical_rx3_session_envelope_after_cloud_sync.sh"
        handoff = handoff_path.read_text()

        self.assertTrue(handoff_path.stat().st_mode & 0o100)
        self.assertNotIn("rbxport", handoff.lower())
        self.assertNotIn("cargo test", handoff)
        self.assertIn(
            "codex-rekordbox-play-cloud-sync-zero-20261004au18.service",
            handoff,
        )
        self.assertIn("song-info-cloud-sync-zero/finalization.json", handoff)
        self.assertIn("original_settings_restored == true", handoff)
        self.assertIn("record_physical_rx3_session_envelope.sh", handoff)
        self.assertIn("summarize_physical_rx3_session_envelope.py", handoff)

    def test_early_post_lifecycle_handoffs_restore_and_stop_on_failure(self) -> None:
        scripts = (
            "run_adjacent_payload_success_status_after_history.sh",
            "run_adjacent_payload_boundaries_after_status.sh",
            "run_adjacent_payload_cues_after_boundaries.sh",
            "run_xdj_rr_location9_after_cues.sh",
            "run_xdj_rr_old_key_after_location9.sh",
            "run_xdj_xz_corroborating_status_after_old_key.sh",
            "run_hot_cue_buffer_link_toggle_after_xdj_xz.sh",
        )

        for script in scripts:
            source = (ROOT / script).read_text()
            with self.subTest(script=script):
                self.assertIn("cleanup() {", source)
                self.assertIn("trap cleanup EXIT", source)
                self.assertIn("completed=false", source)
                self.assertIn("vm_started=false", source)
                self.assertIn('activate_fixture.sh" "$script_dir/fixtures/generated/play-paths', source)
                self.assertIn('"$vm/vmctl" isolated-stop', source)
                self.assertLess(
                    source.index("trap cleanup EXIT"),
                    source.index('"$vm/vmctl" isolated-start'),
                )
                self.assertLess(
                    source.index('"$vm/vmctl" isolated-start'),
                    source.index("vm_started=true"),
                )
                self.assertLess(
                    source.rindex("vm_started=false"),
                    source.rindex("completed=true"),
                )

    def test_nested_matrix_recorders_materialize_declarations_before_guest_commands(self) -> None:
        for name in (
            "record_adjacent_payload_malformed.sh",
            "record_hot_cue_legacy_identical_request_history.sh",
            "record_adjacent_payload_boundary_matrix.sh",
            "record_adjacent_payload_cue_matrix.sh",
            "record_xdj_rr_location9_matrix.sh",
            "record_xdj_rr_old_key_matrix.sh",
            "record_xdj_xz_corroborating_status_matrix.sh",
        ):
            source = (ROOT / name).read_text()
            with self.subTest(name=name):
                self.assertIn(
                    "mapfile -t phases"
                    if name == "record_hot_cue_legacy_identical_request_history.sh"
                    else "mapfile -t declarations",
                    source,
                )
                self.assertNotIn("done < <(", source)

    def test_render_argument_type_handoff_is_real_only_and_guarded(self) -> None:
        handoff_path = ROOT / "run_render_argument_type_matrix_after_underflow.sh"
        recorder_path = ROOT / "record_render_argument_type_matrix.sh"
        handoff = handoff_path.read_text()
        recorder = recorder_path.read_text()

        self.assertTrue(handoff_path.stat().st_mode & 0o100)
        self.assertTrue(recorder_path.stat().st_mode & 0o100)
        self.assertNotIn("rbxport", handoff.lower())
        self.assertNotIn("cargo test", handoff)
        self.assertNotIn("update_checksums.py", handoff)
        self.assertNotIn("test_corpus_documentation", handoff)
        self.assertIn("REKORDBOX_RENDER_UNDERFLOW_UNIT", handoff)
        self.assertIn("predecessor_observed_active == true", handoff)
        self.assertIn("render-arity-underflow/finalization.json", handoff)
        self.assertIn("record_render_argument_type_matrix.sh", handoff)
        self.assertIn("summarize_render_argument_type_matrix.py", handoff)
        self.assertIn('"$vm/vmctl" isolation-check', handoff)
        self.assertIn('"$conformance_test_runner"', handoff)
        self.assertIn("mapfile -t probes", recorder)
        self.assertNotIn("done < <(", recorder)
        self.assertLess(
            handoff.index("require_successful_predecessor"),
            handoff.index('"$vm/vmctl" isolated-start'),
        )
        self.assertLess(
            handoff.rindex("\nrequire_clean_baseline\n"),
            handoff.rindex('\n"$vm/vmctl" isolated-stop\n'),
        )
        self.assertLess(
            handoff.rindex('\n"$vm/vmctl" isolated-stop\n'),
            handoff.rindex("\nwrite_receipt\n"),
        )

    def test_render_numeric_field_handoff_is_real_only_and_guarded(self) -> None:
        handoff_path = ROOT / "run_render_numeric_fields_after_argument_types.sh"
        recorder_path = ROOT / "record_render_numeric_fields.sh"
        handoff = handoff_path.read_text()

        self.assertTrue(handoff_path.stat().st_mode & 0o100)
        self.assertTrue(recorder_path.stat().st_mode & 0o100)
        self.assertNotIn("rbxport", handoff.lower())
        self.assertNotIn("cargo test", handoff)
        self.assertNotIn("update_checksums.py", handoff)
        self.assertNotIn("test_corpus_documentation", handoff)
        self.assertIn("REKORDBOX_RENDER_TYPES_UNIT", handoff)
        self.assertIn("predecessor_observed_active == true", handoff)
        self.assertIn("render-argument-types/finalization.json", handoff)
        self.assertIn("record_render_numeric_fields.sh", handoff)
        self.assertIn("summarize_render_numeric_fields.py", handoff)
        self.assertIn('"$vm/vmctl" isolation-check', handoff)
        self.assertIn('"$conformance_test_runner"', handoff)
        self.assertLess(
            handoff.index("require_successful_predecessor"),
            handoff.index('"$vm/vmctl" isolated-start'),
        )
        self.assertLess(
            handoff.rindex("\nrequire_clean_baseline\n"),
            handoff.rindex('\n"$vm/vmctl" isolated-stop\n'),
        )
        self.assertLess(
            handoff.rindex('\n"$vm/vmctl" isolated-stop\n'),
            handoff.rindex("\nwrite_receipt\n"),
        )

    def test_render_override_control_handoff_is_real_only_and_guarded(self) -> None:
        handoff_path = ROOT / "run_render_override_controls_after_numeric_fields.sh"
        recorder_path = ROOT / "record_render_override_controls.sh"
        handoff = handoff_path.read_text()

        self.assertTrue(handoff_path.stat().st_mode & 0o100)
        self.assertTrue(recorder_path.stat().st_mode & 0o100)
        self.assertNotIn("rbxport", handoff.lower())
        self.assertNotIn("cargo test", handoff)
        self.assertNotIn("update_checksums.py", handoff)
        self.assertNotIn("test_corpus_documentation", handoff)
        self.assertIn("REKORDBOX_RENDER_NUMERIC_UNIT", handoff)
        self.assertIn("predecessor_observed_active == true", handoff)
        self.assertIn("render-numeric-fields/finalization.json", handoff)
        self.assertIn("record_render_override_controls.sh", handoff)
        self.assertIn("summarize_render_override_controls.py", handoff)
        self.assertIn('"$vm/vmctl" isolation-check', handoff)
        self.assertIn('"$conformance_test_runner"', handoff)
        self.assertLess(
            handoff.index("require_successful_predecessor"),
            handoff.index('"$vm/vmctl" isolated-start'),
        )
        self.assertLess(
            handoff.rindex("\nrequire_clean_baseline\n"),
            handoff.rindex('\n"$vm/vmctl" isolated-stop\n'),
        )
        self.assertLess(
            handoff.rindex('\n"$vm/vmctl" isolated-stop\n'),
            handoff.rindex("\nwrite_receipt\n"),
        )

    def test_xdj_xz_handoff_preserves_provenance_and_waits_for_old_key(self) -> None:
        handoff = (
            ROOT / "run_xdj_xz_corroborating_status_after_old_key.sh"
        ).read_text()

        self.assertNotIn("rbxport", handoff.lower())
        self.assertNotIn("cargo test", handoff)
        self.assertIn("REKORDBOX_OLD_KEY_UNIT", handoff)
        self.assertIn("predecessor_observed_active == true", handoff)
        self.assertIn("xdj-rr-client-navigation/old-key/finalization.json", handoff)
        self.assertIn('status_provenance:"corroborating-fixture"', handoff)
        self.assertIn('"$vm/vmctl" isolation-check', handoff)
        self.assertIn("record_xdj_xz_corroborating_status_matrix.sh", handoff)
        self.assertIn("summarize_xdj_xz_corroborating_status_matrix.py", handoff)
        self.assertIn('"$conformance_test_runner"', handoff)
        self.assertLess(
            handoff.index("require_successful_predecessor"),
            handoff.index('"$vm/vmctl" isolated-start'),
        )
        self.assertLess(
            handoff.rindex("\nrequire_clean_baseline\n"),
            handoff.rindex('\n"$vm/vmctl" isolated-stop\n'),
        )
        self.assertLess(
            handoff.rindex('\n"$vm/vmctl" isolated-stop\n'),
            handoff.rindex("\nwrite_receipt\n"),
        )

    def test_link_toggle_handoff_is_real_only_and_guarded(self) -> None:
        handoff = (
            ROOT / "run_hot_cue_buffer_link_toggle_after_xdj_xz.sh"
        ).read_text()

        self.assertNotIn("rbxport", handoff.lower())
        self.assertNotIn("cargo test", handoff)
        self.assertIn("REKORDBOX_XDJ_XZ_UNIT", handoff)
        self.assertIn("predecessor_observed_active == true", handoff)
        self.assertIn("device-status/xdj-xz-corroborating/finalization.json", handoff)
        self.assertIn("record_hot_cue_bank_buffer_link_toggle.sh", handoff)
        self.assertIn("summarize_hot_cue_buffer_link_toggle.py", handoff)
        self.assertIn('"$conformance_test_runner"', handoff)
        self.assertLess(
            handoff.index("require_successful_predecessor"),
            handoff.index('"$vm/vmctl" isolated-start'),
        )
        self.assertLess(
            handoff.rindex("\nrequire_clean_baseline\n"),
            handoff.rindex('\n"$vm/vmctl" isolated-stop\n'),
        )
        self.assertLess(
            handoff.rindex('\n"$vm/vmctl" isolated-stop\n'),
            handoff.rindex("\nwrite_receipt\n"),
        )

    def test_sort_render_5_handoff_is_real_only_and_guarded(self) -> None:
        handoff_path = ROOT / "run_sort_secondary_render_5_after_multiplayer.sh"
        recorder_path = ROOT / "record_sort_secondary_render_5.sh"
        handoff = handoff_path.read_text()

        self.assertTrue(handoff_path.stat().st_mode & 0o100)
        self.assertTrue(recorder_path.stat().st_mode & 0o100)
        self.assertNotIn("rbxport", handoff.lower())
        self.assertNotIn("cargo test", handoff)
        self.assertIn("REKORDBOX_PLAYED_MULTIPLAYER_UNIT", handoff)
        self.assertIn("predecessor_observed_active == true", handoff)
        self.assertIn("played-track-state/multiplayer/finalization.json", handoff)
        self.assertIn("record_sort_secondary_render_5.sh", handoff)
        self.assertIn("summarize_sort_secondary_render_5.py", handoff)
        self.assertIn('"$vm/vmctl" isolation-check', handoff)
        self.assertIn('"$conformance_test_runner"', handoff)
        self.assertNotIn("update_checksums.py", handoff)
        self.assertNotIn("test_corpus_documentation", handoff)
        self.assertLess(
            handoff.index("require_successful_predecessor"),
            handoff.index('"$vm/vmctl" isolated-start'),
        )
        self.assertLess(
            handoff.rindex("\nrequire_clean_baseline\n"),
            handoff.rindex('\n"$vm/vmctl" isolated-stop\n'),
        )
        self.assertLess(
            handoff.rindex('\n"$vm/vmctl" isolated-stop\n'),
            handoff.rindex("\nwrite_receipt\n"),
        )

    def test_sort_render_7_handoff_is_real_only_and_guarded(self) -> None:
        handoff_path = ROOT / "run_sort_secondary_render_7_after_render_5.sh"
        recorder_path = ROOT / "record_sort_secondary_render_7.sh"
        handoff = handoff_path.read_text()

        self.assertTrue(handoff_path.stat().st_mode & 0o100)
        self.assertTrue(recorder_path.stat().st_mode & 0o100)
        self.assertNotIn("rbxport", handoff.lower())
        self.assertNotIn("cargo test", handoff)
        self.assertIn("REKORDBOX_SORT_RENDER_5_UNIT", handoff)
        self.assertIn("predecessor_observed_active == true", handoff)
        self.assertIn("sort-secondary-render-5/finalization.json", handoff)
        self.assertIn("record_sort_secondary_render_7.sh", handoff)
        self.assertIn("summarize_sort_secondary_render_7.py", handoff)
        self.assertIn('"$vm/vmctl" isolation-check', handoff)
        self.assertIn('"$conformance_test_runner"', handoff)
        self.assertNotIn("update_checksums.py", handoff)
        self.assertNotIn("test_corpus_documentation", handoff)
        self.assertLess(
            handoff.index("require_successful_predecessor"),
            handoff.index('"$vm/vmctl" isolated-start'),
        )
        self.assertLess(
            handoff.rindex("\nrequire_clean_baseline\n"),
            handoff.rindex('\n"$vm/vmctl" isolated-stop\n'),
        )
        self.assertLess(
            handoff.rindex('\n"$vm/vmctl" isolated-stop\n'),
            handoff.rindex("\nwrite_receipt\n"),
        )

    def test_render_arity_boundary_handoff_is_real_only_and_guarded(self) -> None:
        handoff_path = ROOT / "run_render_arity_boundaries_after_render_7.sh"
        recorder_path = ROOT / "record_render_arity_boundaries.sh"
        handoff = handoff_path.read_text()

        self.assertTrue(handoff_path.stat().st_mode & 0o100)
        self.assertTrue(recorder_path.stat().st_mode & 0o100)
        self.assertNotIn("rbxport", handoff.lower())
        self.assertNotIn("cargo test", handoff)
        self.assertNotIn("update_checksums.py", handoff)
        self.assertNotIn("test_corpus_documentation", handoff)
        self.assertIn("REKORDBOX_SORT_RENDER_7_UNIT", handoff)
        self.assertIn("predecessor_observed_active == true", handoff)
        self.assertIn("sort-secondary-render-7/finalization.json", handoff)
        self.assertIn("record_render_arity_boundaries.sh", handoff)
        self.assertIn("summarize_render_arity_boundaries.py", handoff)
        self.assertIn('"$vm/vmctl" isolation-check', handoff)
        self.assertIn('"$conformance_test_runner"', handoff)
        self.assertLess(
            handoff.index("require_successful_predecessor"),
            handoff.index('"$vm/vmctl" isolated-start'),
        )
        self.assertLess(
            handoff.rindex("\nrequire_clean_baseline\n"),
            handoff.rindex('\n"$vm/vmctl" isolated-stop\n'),
        )
        self.assertLess(
            handoff.rindex('\n"$vm/vmctl" isolated-stop\n'),
            handoff.rindex("\nwrite_receipt\n"),
        )

    def test_render_arity_underflow_handoff_is_real_only_and_guarded(self) -> None:
        handoff_path = ROOT / "run_render_arity_underflow_after_boundaries.sh"
        recorder_path = ROOT / "record_render_arity_underflow.sh"
        handoff = handoff_path.read_text()

        self.assertTrue(handoff_path.stat().st_mode & 0o100)
        self.assertTrue(recorder_path.stat().st_mode & 0o100)
        self.assertNotIn("rbxport", handoff.lower())
        self.assertNotIn("cargo test", handoff)
        self.assertNotIn("update_checksums.py", handoff)
        self.assertNotIn("test_corpus_documentation", handoff)
        self.assertIn("REKORDBOX_RENDER_ARITY_UNIT", handoff)
        self.assertIn("predecessor_observed_active == true", handoff)
        self.assertIn("render-arity-boundaries/finalization.json", handoff)
        self.assertIn("record_render_arity_underflow.sh", handoff)
        self.assertIn("summarize_render_arity_underflow.py", handoff)
        self.assertIn('"$vm/vmctl" isolation-check', handoff)
        self.assertIn('"$conformance_test_runner"', handoff)
        self.assertLess(
            handoff.index("require_successful_predecessor"),
            handoff.index('"$vm/vmctl" isolated-start'),
        )
        self.assertLess(
            handoff.rindex("\nrequire_clean_baseline\n"),
            handoff.rindex('\n"$vm/vmctl" isolated-stop\n'),
        )
        self.assertLess(
            handoff.rindex('\n"$vm/vmctl" isolated-stop\n'),
            handoff.rindex("\nwrite_receipt\n"),
        )

    def test_active_queue_contains_no_rbxport_invocation(self) -> None:
        for name in ACTIVE_QUEUE_SCRIPTS:
            path = ROOT / name
            self.assertTrue(path.is_file(), name)
            self.assertNotIn("rbxport", path.read_text().lower(), name)

    def test_active_queue_never_builds_at_runtime(self) -> None:
        forbidden = ("cargo run", "cargo test", "cargo build", "target/release")

        for name in ACTIVE_QUEUE_SCRIPTS:
            text = (ROOT / name).read_text()
            for command in forbidden:
                self.assertNotIn(command, text, f"{name}: {command}")

    def test_finalizer_stops_the_vm_only_after_successful_validation(self) -> None:
        finalizer_path = ROOT / "finalize_real_rekordbox_queue.sh"
        finalizer = finalizer_path.read_text()

        self.assertTrue(finalizer_path.stat().st_mode & 0o100)
        self.assertNotIn("trap stop_vm EXIT", finalizer)
        self.assertNotIn("cargo test", finalizer)
        self.assertIn('"$conformance_test_runner"', finalizer)
        self.assertIn("conformance_runner_sha256", finalizer)
        self.assertIn("conformance_test_runner_sha256", finalizer)
        self.assertIn("pinned_manifest_sha256", finalizer)
        self.assertIn("expected_runner_sha256", finalizer)
        self.assertIn("expected_test_runner_sha256", finalizer)
        self.assertLess(
            finalizer.index('"$conformance_test_runner"'),
            finalizer.index('"$vm/vmctl" isolated-stop'),
        )

    def test_remaining_queue_is_strictly_serial(self) -> None:
        queue = (ROOT / "run_remaining_real_rekordbox_queue.sh").read_text()
        stages = (
            "extended-setter-parser",
            "legacy-setter-parser",
            "hot-cue-buffer-disconnect",
            "cdj-2000nexus-status",
            "secondary-columns-legacy",
            "extended-setter-fields",
            "extended-setter-seek",
            "bpm-tolerance-boundaries",
        )

        positions = [queue.index(stage) for stage in stages]
        self.assertEqual(sorted(positions), positions)
        self.assertLess(
            queue.index("summarize_hot_cue_slot_8_lifecycle.py"),
            queue.index("extended-setter-parser"),
        )
        self.assertLess(
            queue.index("bpm-tolerance-boundaries"),
            queue.index("finalize_real_rekordbox_queue.sh"),
        )

    def test_oracle_record_retries_transient_port_query_failures(self) -> None:
        recorder = (ROOT / "oracle_record.sh").read_text()

        self.assertIn("link_is_unavailable", recorder)
        self.assertIn("Resource temporarily unavailable", recorder)
        self.assertIn("dbserver connection .* failed: connection timed out", recorder)
        self.assertIn("REKORDBOX_LINK_MAX_ATTEMPTS", recorder)
        self.assertEqual(2, recorder.count('if ! link_is_unavailable "$record_log"'))

        legacy = (ROOT / "record_hot_cue_legacy_setter_parser_matrix.sh").read_text()
        self.assertIn("REKORDBOX_LINK_MAX_ATTEMPTS=1", legacy)
        self.assertIn("health-after-getter-unavailable.json", legacy)
        self.assertIn("dbserver-connect-timeout", legacy)
        self.assertIn("port-query-timeout", legacy)

    def test_rfb_activation_retries_transient_module_fetch_failures(self) -> None:
        for name in (
            "oracle_record.sh",
            "record_hot_cue_bank_buffer_disconnect.sh",
            "record_hot_cue_bank_buffer_link_toggle.sh",
        ):
            source = (ROOT / name).read_text()
            with self.subTest(name=name):
                self.assertIn("for attempt in 1 2 3", source)
                self.assertIn("((attempt < 3)) || return 1", source)
                self.assertIn(
                    'agent-browser --session rekordbox-windows open "$console_url"',
                    source,
                )

    def test_malformed_history_handoff_can_resume_from_verified_receipt(self) -> None:
        handoff = (
            ROOT / "run_status_location2_malformed_history_after_compatibility.sh"
        ).read_text()

        self.assertIn(
            "predecessor_observed_active == true || -f $predecessor_receipt",
            handoff,
        )
        self.assertIn(
            'scope == "real Rekordbox 7.2.19 track compatibility only"',
            handoff,
        )
        self.assertLess(
            handoff.index("require_successful_predecessor"),
            handoff.index("start_isolated_vm"),
        )

    def test_oracle_record_uses_pinned_binary_without_runtime_rebuild(self) -> None:
        recorder = (ROOT / "oracle_record.sh").read_text()
        self.assertIn("LINK_EXPORT_CONFORMANCE_BIN", recorder)
        self.assertIn(
            "$conformance/pinned/link-export-conformance",
            recorder,
        )
        self.assertIn('runner_sha256=$(sha256sum "$runner"', recorder)
        self.assertNotIn("cargo run", recorder)

    def test_oracle_record_closes_browser_after_rfb_activation(self) -> None:
        recorder = (ROOT / "oracle_record.sh").read_text()

        self.assertIn("close_browser()", recorder)
        self.assertIn(
            "agent-browser --session rekordbox-windows close",
            recorder,
        )
        self.assertGreaterEqual(recorder.count("close_browser"), 3)
        self.assertLess(
            recorder.index("agent-browser --session rekordbox-windows wait 8000"),
            recorder.index("\n  close_browser\n", recorder.index("click_link()")),
        )

    def test_pinned_executables_match_their_manifest(self) -> None:
        pinned = ROOT / "pinned"
        manifest = json.loads((pinned / "manifest.json").read_text())

        self.assertEqual(1, manifest["format"])
        for key in ("runner", "test_runner"):
            artifact = pinned / manifest[key]["path"]
            self.assertTrue(artifact.is_file())
            self.assertEqual(manifest[key]["size"], artifact.stat().st_size)
            self.assertEqual(
                manifest[key]["sha256"],
                hashlib.sha256(artifact.read_bytes()).hexdigest(),
            )

    def test_setter_field_recorder_resumes_atomic_record_candidate(self) -> None:
        recorder = (
            ROOT / "record_hot_cue_extended_setter_field_matrix.sh"
        ).read_text()
        self.assertIn("resuming recorded candidate and database proof", recorder)
        self.assertIn('-f $candidate && -f $evidence/record-snapshot.json', recorder)

    def test_setter_field_handoff_requires_complete_evidence(self) -> None:
        handoff = (ROOT / "run_after_setter_fields.sh").read_text()

        self.assertNotIn("rbxport", handoff.lower())
        self.assertIn("predecessor_observed_active == true", handoff)
        self.assertIn("setter_fields_complete", handoff)
        self.assertIn("summarize_hot_cue_extended_setter_fields.py", handoff)
        self.assertIn("record_hot_cue_extended_setter_seek_matrix.sh", handoff)
        self.assertIn("record_bpm_tolerance_boundaries.sh", handoff)
        self.assertIn("finalize_real_rekordbox_queue.sh", handoff)
        self.assertLess(
            handoff.index("require_successful_predecessor"),
            handoff.index('"$script_dir/record_hot_cue_extended_setter_seek_matrix.sh"'),
        )
        self.assertLess(
            handoff.index('"$script_dir/record_bpm_tolerance_boundaries.sh"'),
            handoff.index('"$script_dir/finalize_real_rekordbox_queue.sh"'),
        )

    def test_post_history_compatibility_handoff_is_real_only_and_guarded(self) -> None:
        handoff = (ROOT / "run_track_compatibility_after_queue.sh").read_text()

        self.assertNotIn("rbxport", handoff.lower())
        self.assertIn("REKORDBOX_HISTORY_UNIT", handoff)
        self.assertIn("require_successful_history", handoff)
        self.assertIn("legacy-identical-request-history/finalization.json", handoff)
        self.assertIn(
            "history_observed_active == true || -f $history_receipt",
            handoff,
        )
        self.assertIn("cycle_receipt_sha256", handoff)
        self.assertIn("extended_receipt_sha256", handoff)
        self.assertIn("legacy_receipt_sha256", handoff)
        self.assertIn("disappeared without a finalization receipt", handoff)
        self.assertLess(
            handoff.index('"$vm/vmctl" isolation-check'),
            handoff.index('"$script_dir/record_track_compatibility_exhaustive.sh"'),
        )
        self.assertLess(
            handoff.rindex("\nrequire_clean_baseline\n"),
            handoff.rindex('\n"$vm/vmctl" isolated-stop\n'),
        )
        self.assertLess(
            handoff.rindex('\n"$vm/vmctl" isolated-stop\n'),
            handoff.rindex("\nwrite_receipt\n"),
        )

    def test_identical_history_handoff_is_real_only_and_guarded(self) -> None:
        handoff = (ROOT / "run_identical_history_after_queue.sh").read_text()

        self.assertNotIn("rbxport", handoff.lower())
        self.assertIn("queue_observed_active=false", handoff)
        self.assertIn("queue_observed_active == true", handoff)
        self.assertIn("disappeared without a finalization receipt", handoff)
        self.assertIn("real-rekordbox-queue-finalization.json", handoff)
        self.assertIn("REKORDBOX_QUEUE_RECEIPT", handoff)
        self.assertIn("REKORDBOX_QUEUE_SCOPE", handoff)
        self.assertIn('.scope == $queue_scope', handoff)
        self.assertLess(
            handoff.index("jq -e"),
            handoff.index('"$script_dir/record_hot_cue_legacy_identical_request_history.sh"'),
        )
        self.assertLess(
            handoff.rindex('\n"$vm/vmctl" isolated-stop\n'),
            handoff.rindex('\nmv "$receipt.next" "$receipt"\n'),
        )

    def test_malformed_history_handoff_is_guarded_and_renews_vm_lease(self) -> None:
        handoff = (
            ROOT / "run_status_location2_malformed_history_after_compatibility.sh"
        ).read_text()

        self.assertNotIn("rbxport", handoff.lower())
        self.assertNotIn("cargo test", handoff)
        self.assertIn("REKORDBOX_COMPATIBILITY_UNIT", handoff)
        self.assertIn("predecessor_observed_active == true", handoff)
        self.assertIn("track-compatibility-exhaustive/finalization.json", handoff)
        self.assertIn('"$conformance_test_runner"', handoff)
        self.assertIn("conformance_test_runner_sha256", handoff)
        self.assertIn("pinned_manifest_sha256", handoff)
        self.assertIn("readonly batch_size=64", handoff)
        self.assertIn('"$vm/vmctl" isolation-check', handoff)
        self.assertLess(
            handoff.index("require_successful_predecessor"),
            handoff.index("mapfile -t pairs"),
        )
        self.assertLess(
            handoff.rindex("\nrequire_clean_baseline\n"),
            handoff.rindex('\n"$vm/vmctl" isolated-stop\n'),
        )
        self.assertLess(
            handoff.rindex('\n"$vm/vmctl" isolated-stop\n'),
            handoff.rindex("\nwrite_receipt\n"),
        )

    def test_payload_boundary_handoff_is_real_only_and_guarded(self) -> None:
        handoff = (ROOT / "run_adjacent_payload_boundaries_after_status.sh").read_text()

        self.assertNotIn("rbxport", handoff.lower())
        self.assertNotIn("cargo test", handoff)
        self.assertIn("REKORDBOX_PAYLOAD_STATUS_UNIT", handoff)
        self.assertIn("predecessor_observed_active == true", handoff)
        self.assertIn("adjacent-payload/success-status/finalization.json", handoff)
        self.assertIn('"$vm/vmctl" isolation-check', handoff)
        self.assertIn("record_adjacent_payload_boundary_matrix.sh", handoff)
        self.assertIn("summarize_adjacent_payload_boundaries.py", handoff)
        self.assertIn('"$conformance_test_runner"', handoff)
        self.assertLess(
            handoff.index("require_successful_predecessor"),
            handoff.index('"$vm/vmctl" isolated-start'),
        )
        self.assertLess(
            handoff.rindex("\nrequire_clean_baseline\n"),
            handoff.rindex('\n"$vm/vmctl" isolated-stop\n'),
        )
        self.assertLess(
            handoff.rindex('\n"$vm/vmctl" isolated-stop\n'),
            handoff.rindex("\nwrite_receipt\n"),
        )

    def test_cue_payload_handoff_is_real_only_and_guarded(self) -> None:
        handoff = (ROOT / "run_adjacent_payload_cues_after_boundaries.sh").read_text()

        self.assertNotIn("rbxport", handoff.lower())
        self.assertNotIn("cargo test", handoff)
        self.assertIn("REKORDBOX_PAYLOAD_BOUNDARY_UNIT", handoff)
        self.assertIn("predecessor_observed_active == true", handoff)
        self.assertIn("adjacent-payload/boundaries/finalization.json", handoff)
        self.assertIn('"$vm/vmctl" isolation-check', handoff)
        self.assertIn("record_adjacent_payload_cue_matrix.sh", handoff)
        self.assertIn("summarize_adjacent_payload_cues.py", handoff)
        self.assertIn('"$conformance_test_runner"', handoff)
        self.assertLess(
            handoff.index("require_successful_predecessor"),
            handoff.index('"$vm/vmctl" isolated-start'),
        )
        self.assertLess(
            handoff.rindex("\nrequire_clean_baseline\n"),
            handoff.rindex('\n"$vm/vmctl" isolated-stop\n'),
        )
        self.assertLess(
            handoff.rindex('\n"$vm/vmctl" isolated-stop\n'),
            handoff.rindex("\nwrite_receipt\n"),
        )

    def test_xdj_rr_location9_handoff_is_real_only_and_guarded(self) -> None:
        handoff = (ROOT / "run_xdj_rr_location9_after_cues.sh").read_text()

        self.assertNotIn("rbxport", handoff.lower())
        self.assertNotIn("cargo test", handoff)
        self.assertIn("REKORDBOX_CUE_PAYLOAD_UNIT", handoff)
        self.assertIn("predecessor_observed_active == true", handoff)
        self.assertIn("adjacent-payload/cues/finalization.json", handoff)
        self.assertIn('"$vm/vmctl" isolation-check', handoff)
        self.assertIn("record_xdj_rr_location9_matrix.sh", handoff)
        self.assertIn("summarize_xdj_rr_location9.py", handoff)
        self.assertIn('"$conformance_test_runner"', handoff)
        self.assertLess(
            handoff.index("require_successful_predecessor"),
            handoff.index('"$vm/vmctl" isolated-start'),
        )
        self.assertLess(
            handoff.rindex("\nrequire_clean_baseline\n"),
            handoff.rindex('\n"$vm/vmctl" isolated-stop\n'),
        )
        self.assertLess(
            handoff.rindex('\n"$vm/vmctl" isolated-stop\n'),
            handoff.rindex("\nwrite_receipt\n"),
        )

    def test_xdj_rr_old_key_handoff_is_real_only_and_guarded(self) -> None:
        handoff = (ROOT / "run_xdj_rr_old_key_after_location9.sh").read_text()

        self.assertNotIn("rbxport", handoff.lower())
        self.assertNotIn("cargo test", handoff)
        self.assertIn("REKORDBOX_LOCATION9_UNIT", handoff)
        self.assertIn("predecessor_observed_active == true", handoff)
        self.assertIn("xdj-rr-client-navigation/location9/finalization.json", handoff)
        self.assertIn('"$vm/vmctl" isolation-check', handoff)
        self.assertIn("record_xdj_rr_old_key_matrix.sh", handoff)
        self.assertIn("summarize_xdj_rr_old_key.py", handoff)
        self.assertIn('"$conformance_test_runner"', handoff)
        self.assertLess(
            handoff.index("require_successful_predecessor"),
            handoff.index('"$vm/vmctl" isolated-start'),
        )
        self.assertLess(
            handoff.rindex("\nrequire_clean_baseline\n"),
            handoff.rindex('\n"$vm/vmctl" isolated-stop\n'),
        )
        self.assertLess(
            handoff.rindex('\n"$vm/vmctl" isolated-stop\n'),
            handoff.rindex("\nwrite_receipt\n"),
        )

    def test_adjacent_payload_handoff_is_real_only_and_guarded(self) -> None:
        handoff = (ROOT / "run_adjacent_payload_after_queue.sh").read_text()

        self.assertNotIn("rbxport", handoff.lower())
        self.assertNotIn("cargo test", handoff)
        self.assertIn("REKORDBOX_QUEUE_UNIT", handoff)
        self.assertIn("predecessor_observed_active == true", handoff)
        self.assertIn("real-rekordbox-queue-finalization.json", handoff)
        self.assertIn('"$vm/vmctl" isolation-check', handoff)
        self.assertIn("record_adjacent_payload_fileless.sh", handoff)
        self.assertIn("summarize_adjacent_payload_fileless.py", handoff)
        self.assertLess(
            handoff.index("require_successful_predecessor"),
            handoff.index('"$vm/vmctl" isolated-start'),
        )
        self.assertLess(
            handoff.rindex("\nrequire_clean_baseline\n"),
            handoff.rindex('\n"$vm/vmctl" isolated-stop\n'),
        )
        self.assertLess(
            handoff.rindex('\n"$vm/vmctl" isolated-stop\n'),
            handoff.rindex("\nwrite_receipt\n"),
        )

    def test_malformed_payload_handoff_is_real_only_and_guarded(self) -> None:
        handoff = (
            ROOT / "run_adjacent_payload_malformed_after_fileless.sh"
        ).read_text()

        self.assertNotIn("rbxport", handoff.lower())
        self.assertNotIn("cargo test", handoff)
        self.assertIn("REKORDBOX_PAYLOAD_UNIT", handoff)
        self.assertIn("predecessor_observed_active == true", handoff)
        self.assertIn('[[ -f $predecessor_receipt ]]', handoff)
        self.assertIn("adjacent-payload/fileless/finalization.json", handoff)
        self.assertIn('"$vm/vmctl" isolation-check', handoff)
        self.assertIn("record_adjacent_payload_malformed.sh", handoff)
        self.assertIn("summarize_adjacent_payload_malformed.py", handoff)
        self.assertLess(
            handoff.index("require_successful_predecessor"),
            handoff.index('"$vm/vmctl" isolated-start'),
        )
        self.assertLess(
            handoff.rindex("\nrequire_clean_baseline\n"),
            handoff.rindex('\n"$vm/vmctl" isolated-stop\n'),
        )
        self.assertLess(
            handoff.rindex('\n"$vm/vmctl" isolated-stop\n'),
            handoff.rindex("\nwrite_receipt\n"),
        )

    def test_missing_file_payload_handoff_is_real_only_and_guarded(self) -> None:
        handoff = (
            ROOT / "run_adjacent_payload_missing_files_after_malformed.sh"
        ).read_text()

        self.assertNotIn("rbxport", handoff.lower())
        self.assertNotIn("cargo test", handoff)
        self.assertIn("REKORDBOX_MALFORMED_PAYLOAD_UNIT", handoff)
        self.assertIn("predecessor_observed_active == true", handoff)
        self.assertIn("adjacent-payload/malformed/finalization.json", handoff)
        self.assertIn('"$vm/vmctl" isolation-check', handoff)
        self.assertIn("record_adjacent_payload_missing_files.sh", handoff)
        self.assertIn("summarize_adjacent_payload_missing_files.py", handoff)
        self.assertLess(
            handoff.index("require_successful_predecessor"),
            handoff.index('"$vm/vmctl" isolated-start'),
        )
        self.assertLess(
            handoff.rindex("\nrequire_clean_baseline\n"),
            handoff.rindex('\n"$vm/vmctl" isolated-stop\n'),
        )
        self.assertLess(
            handoff.rindex('\n"$vm/vmctl" isolated-stop\n'),
            handoff.rindex("\nwrite_receipt\n"),
        )

    def test_success_payload_handoff_is_real_only_guarded_and_cleans_assets(self) -> None:
        handoff = (
            ROOT / "run_adjacent_payload_success_after_missing_files.sh"
        ).read_text()
        recorder = (ROOT / "record_adjacent_payload_success.sh").read_text()

        self.assertNotIn("rbxport", handoff.lower())
        self.assertNotIn("cargo test", handoff)
        self.assertIn("REKORDBOX_MISSING_PAYLOAD_UNIT", handoff)
        self.assertIn("predecessor_observed_active == true", handoff)
        self.assertIn("adjacent-payload/missing-files/finalization.json", handoff)
        self.assertIn('"$vm/vmctl" isolation-check', handoff)
        self.assertIn("record_adjacent_payload_success.sh", handoff)
        self.assertIn("summarize_adjacent_payload_success.py", handoff)
        self.assertIn("deterministic_guest_assets_removed:true", handoff)
        self.assertIn("staged_by_this_run=false", recorder)
        self.assertIn("capture_guest_assets", recorder)
        self.assertIn("record-assets.json", recorder)
        self.assertIn("repeat-assets.json", recorder)
        self.assertIn("remove_assets", recorder)
        self.assertIn('remove_assets || cleanup_status=$?', recorder)
        self.assertIn('exit "$cleanup_status"', recorder)
        self.assertLess(
            handoff.index("require_successful_predecessor"),
            handoff.index('"$vm/vmctl" isolated-start'),
        )
        self.assertLess(
            handoff.rindex("\nrequire_clean_baseline\n"),
            handoff.rindex('\n"$vm/vmctl" isolated-stop\n'),
        )
        self.assertLess(
            handoff.rindex('\n"$vm/vmctl" isolated-stop\n'),
            handoff.rindex("\nwrite_receipt\n"),
        )

    def test_success_payload_status_handoff_is_guarded_and_cleans_assets(self) -> None:
        handoff = (
            ROOT / "run_adjacent_payload_success_status_after_history.sh"
        ).read_text()
        recorder = (
            ROOT / "record_adjacent_payload_success_status_cross.sh"
        ).read_text()

        self.assertNotIn("rbxport", handoff.lower())
        self.assertNotIn("cargo test", handoff)
        self.assertIn("REKORDBOX_MALFORMED_HISTORY_UNIT", handoff)
        self.assertIn(
            "codex-rekordbox-song-info-malformed-history-lifecycle-20261004z27.service",
            handoff,
        )
        self.assertIn("predecessor_observed_active == true", handoff)
        self.assertIn("malformed-history-lifecycle/finalization.json", handoff)
        self.assertIn("malformed-history lifecycle", handoff)
        self.assertIn('"$vm/vmctl" isolation-check', handoff)
        self.assertIn("record_adjacent_payload_success_status_cross.sh", handoff)
        self.assertIn("summarize_adjacent_payload_success_status.py", handoff)
        self.assertIn("deterministic_guest_assets_removed:true", handoff)
        self.assertEqual(recorder.count("record_variant "), 4)
        self.assertIn("cdj-3000-player-1-status.json", recorder)
        self.assertIn("xdj-rx3-player-11-status.json", recorder)
        self.assertLess(
            handoff.index("require_successful_predecessor"),
            handoff.index('"$vm/vmctl" isolated-start'),
        )
        self.assertLess(
            handoff.rindex("\nrequire_clean_baseline\n"),
            handoff.rindex('\n"$vm/vmctl" isolated-stop\n'),
        )
        self.assertLess(
            handoff.rindex('\n"$vm/vmctl" isolated-stop\n'),
            handoff.rindex("\nwrite_receipt\n"),
        )

    def test_song_info_delayed_reply_routing_is_real_only_and_guarded(self) -> None:
        handoff = (ROOT / "run_song_info_delayed_reply_routing.sh").read_text()

        self.assertNotIn("rbxport", handoff.lower())
        self.assertNotIn("cargo test", handoff)
        self.assertIn("malformed-history-timing/finalization.json", handoff)
        self.assertIn("require_timing_authority", handoff)
        self.assertIn("require_pinned_runners", handoff)
        self.assertIn('"$vm/vmctl" isolation-check', handoff)
        self.assertIn("record_song_info_delayed_reply_routing.sh", handoff)
        self.assertIn("summarize_song_info_delayed_reply_routing.py", handoff)
        self.assertLess(
            handoff.rindex("\nrequire_timing_authority\n"),
            handoff.index('"$lab/.venv/bin/python" "$script_dir/generate_matrices.py"'),
        )
        self.assertLess(
            handoff.rindex("\nrequire_pinned_runners\n"),
            handoff.index('"$vm/vmctl" isolated-start'),
        )
        self.assertLess(
            handoff.rindex("\nrequire_clean_baseline\n"),
            handoff.rindex('\n"$vm/vmctl" isolated-stop\n'),
        )
        self.assertLess(
            handoff.rindex('\n"$vm/vmctl" isolated-stop\n'),
            handoff.rindex("\nwrite_receipt\n"),
        )


if __name__ == "__main__":
    unittest.main()
