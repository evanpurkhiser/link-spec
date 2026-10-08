import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
RECORDER = ROOT / "record_hot_cue_bank_buffer_link_toggle.sh"
REDUCER = ROOT.parent / "tools/summarize_hot_cue_buffer_link_toggle.py"


class HotCueBufferLinkToggleTests(unittest.TestCase):
    def test_recorder_uses_existing_distinguishable_location_suites(self) -> None:
        source = RECORDER.read_text()

        self.assertIn("hot-cue-bank-buffer-disconnect-warmup.json", source)
        self.assertIn("hot-cue-bank-buffer-disconnect-post.json", source)
        self.assertIn('modes=(control toggle)', source)
        self.assertIn('for run in 1 2', source)

    def test_toggle_proves_dbserver_absence_and_same_process_health(self) -> None:
        source = RECORDER.read_text()

        self.assertIn('wait_for_dbserver absent', source)
        self.assertIn('wait_for_dbserver present', source)
        self.assertIn('capture_rekordbox_health.ps1', source)
        self.assertIn('inactive-health.json', source)
        self.assertIn('reactivated-health.json', source)
        self.assertNotIn("rbxport", source.lower())

    def test_every_run_uses_fresh_fixture_process_and_hash_receipt(self) -> None:
        source = RECORDER.read_text()

        activate = source.index('"$script_dir/activate_fixture.sh" "$fixture"')
        launch = source.index('"$script_dir/start_oracle_ui.sh"', activate)
        identity = source.index('start_identity "$unit"', launch)
        warmup = source.index('record_suite "$warmup_suite"', identity)
        post = source.index('record_suite "$post_suite"', warmup)
        receipt = source.index('write_receipt "$id"', post)
        self.assertLess(activate, launch)
        self.assertLess(launch, identity)
        self.assertLess(identity, warmup)
        self.assertLess(warmup, post)
        self.assertLess(post, receipt)
        self.assertIn('transition_sha256', source)
        self.assertIn('health_sha256', source)

    def test_reducer_requires_repeat_and_classifies_only_known_shapes(self) -> None:
        source = REDUCER.read_text()

        self.assertIn('MODES = ("control", "toggle")', source)
        self.assertIn('RUNS = (1, 2)', source)
        self.assertIn('len(process_ids) == 1', source)
        self.assertIn('listeners["inactive-health.json"] == 0', source)
        self.assertIn('stale_classification(stale)', source)
        self.assertIn('runs[0]["behavior_signature"] == runs[1]["behavior_signature"]', source)
        self.assertIn('by_mode["control"]["old_location_state"] == "persisted"', source)
        self.assertIn(
            'by_mode["toggle"]["old_location_state"] in {"persisted", "cleared"}',
            source,
        )


if __name__ == "__main__":
    unittest.main()
