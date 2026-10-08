import json
import unittest

import replay_rbxport


class ReplayConfigurationTests(unittest.TestCase):
    def test_replay_requires_explicit_opt_in(self) -> None:
        with self.assertRaisesRegex(SystemExit, "requires an explicit opt-in"):
            replay_rbxport.require_deferred_phase_opt_in(False)

        replay_rbxport.require_deferred_phase_opt_in(True)

    def test_replays_can_be_selected_by_suite_or_model(self) -> None:
        first = replay_rbxport.Replay("one", "one.json", "shared", "full")
        second = replay_rbxport.Replay("two", "two.json", "shared", "full")
        unique = replay_rbxport.Replay("two", "two.json", "unique", "full")
        replays = (first, second, unique)

        self.assertEqual((first, second), replay_rbxport.select_replays(replays, ["shared"]))
        self.assertEqual(
            (second,), replay_rbxport.select_replays(replays, ["two/shared"])
        )
        with self.assertRaisesRegex(SystemExit, "unknown replay suite: missing"):
            replay_rbxport.select_replays(replays, ["missing"])

    def test_every_oracle_golden_is_replayed_or_explicitly_deferred(self) -> None:
        declared = {
            (replay.model, replay.suite) for replay in replay_rbxport.REPLAYS
        }
        goldens = {
            (path.parent.name, path.stem)
            for path in (replay_rbxport.ROOT / "goldens/rekordbox-7.2.19").glob(
                "*/*.json"
            )
        }

        self.assertFalse(declared & replay_rbxport.DEFERRED_REPLAYS)
        self.assertEqual(
            goldens,
            declared | (goldens & replay_rbxport.DEFERRED_REPLAYS),
        )
        self.assertEqual(287, len(declared))
        self.assertEqual(149, len(replay_rbxport.DEFERRED_REPLAYS))

    def test_pending_extended_setter_parser_goldens_are_declared(self) -> None:
        matrix = json.loads(
            (
                replay_rbxport.ROOT
                / "data/hot-cue-setter-parser-matrix.json"
            ).read_text()
        )
        expected = {
            ("xdj-rx3-status", f"hot-cue-setter-parser-{variant['id']}")
            for variant in matrix["variants"]
        }
        self.assertEqual(57, len(expected))
        self.assertLessEqual(expected, replay_rbxport.DEFERRED_REPLAYS)

        for variant in matrix["variants"]:
            suite = replay_rbxport.ROOT / variant["suite"]
            self.assertTrue(suite.is_file(), variant["id"])

    def test_setter_field_goldens_are_explicitly_deferred(self) -> None:
        matrix = json.loads(
            (
                replay_rbxport.ROOT
                / "data/hot-cue-setter-field-matrix.json"
            ).read_text()
        )
        expected = {
            ("xdj-rx3-status", f"hot-cue-setter-field-{variant['id']}")
            for variant in matrix["variants"]
        }
        self.assertEqual(56, len(expected))
        self.assertLessEqual(expected, replay_rbxport.DEFERRED_REPLAYS)

    def test_link_visibility_replay_has_complete_artifacts(self) -> None:
        replay = next(
            replay
            for replay in replay_rbxport.REPLAYS
            if replay.suite == "link-visibility"
        )
        suite = replay_rbxport.ROOT / f"suites/{replay.suite_path}.json"
        manifest = (
            replay_rbxport.ROOT
            / f"fixtures/generated/{replay.fixture}/manifest.json"
        )
        golden = (
            replay_rbxport.ROOT
            / f"goldens/rekordbox-7.2.19/{replay.model}/{replay.suite}.json"
        )

        self.assertTrue(suite.is_file())
        self.assertTrue(manifest.is_file())
        self.assertTrue(golden.is_file())

    def test_device_capability_replays_cover_every_identity(self) -> None:
        self.assertEqual(8, len(replay_rbxport.DEVICE_CAPABILITY_REPLAYS))

        for replay in replay_rbxport.DEVICE_CAPABILITY_REPLAYS:
            suite = replay_rbxport.ROOT / "suites/device-capabilities.json"
            identity = replay_rbxport.ROOT / f"runs/{replay.identity}"
            golden = (
                replay_rbxport.ROOT
                / f"goldens/rekordbox-7.2.19/{replay.model}/device-capabilities.json"
            )

            self.assertTrue(suite.is_file())
            self.assertTrue(identity.is_file(), replay.identity)
            self.assertTrue(golden.is_file(), replay.model)

    def test_device_compatibility_replays_cover_every_identity(self) -> None:
        self.assertEqual(8, len(replay_rbxport.DEVICE_COMPATIBILITY_REPLAYS))

        for replay in replay_rbxport.DEVICE_COMPATIBILITY_REPLAYS:
            manifest = replay_rbxport.ROOT / "fixtures/generated/compatibility/manifest.json"
            identity = replay_rbxport.ROOT / f"runs/{replay.identity}"
            golden = (
                replay_rbxport.ROOT
                / f"goldens/rekordbox-7.2.19/{replay.model}/compatibility.json"
            )

            self.assertTrue(manifest.is_file())
            self.assertTrue(identity.is_file(), replay.identity)
            self.assertTrue(golden.is_file(), replay.model)

    def test_device_smart_replays_cover_every_identity(self) -> None:
        self.assertEqual(8, len(replay_rbxport.DEVICE_SMART_REPLAYS))

        for replay in replay_rbxport.DEVICE_SMART_REPLAYS:
            suite = replay_rbxport.ROOT / "suites/smart-device-cross.json"
            manifest = (
                replay_rbxport.ROOT
                / "fixtures/generated/smart-rule-matrix/manifest.json"
            )
            identity = replay_rbxport.ROOT / f"runs/{replay.identity}"
            golden = (
                replay_rbxport.ROOT
                / f"goldens/rekordbox-7.2.19/{replay.model}/smart-device-cross.json"
            )

            self.assertTrue(suite.is_file())
            self.assertTrue(manifest.is_file())
            self.assertTrue(identity.is_file(), replay.identity)
            self.assertTrue(golden.is_file(), replay.model)

    def test_device_reconnect_replays_cover_both_sides(self) -> None:
        self.assertEqual(2, len(replay_rbxport.DEVICE_RECONNECT_REPLAYS))

        for replay in replay_rbxport.DEVICE_RECONNECT_REPLAYS:
            suite = replay_rbxport.ROOT / "suites/device-reconnect.json"
            identity = replay_rbxport.ROOT / f"runs/{replay.identity}"
            golden = (
                replay_rbxport.ROOT
                / f"goldens/rekordbox-7.2.19/{replay.model}/device-reconnect.json"
            )

            self.assertTrue(suite.is_file())
            self.assertTrue(identity.is_file(), replay.identity)
            self.assertTrue(golden.is_file(), replay.model)

    def test_settings_replays_have_complete_artifacts(self) -> None:
        self.assertEqual(17, len(replay_rbxport.SETTINGS_REPLAYS))

        for replay in replay_rbxport.SETTINGS_REPLAYS:
            suite = replay_rbxport.ROOT / f"suites/{replay.suite_path}.json"
            manifest = (
                replay_rbxport.ROOT
                / f"fixtures/generated/{replay.fixture}/manifest.json"
            )
            golden = (
                replay_rbxport.ROOT
                / f"goldens/rekordbox-7.2.19/{replay.model}/{replay.suite}.json"
            )

            self.assertTrue(suite.is_file(), replay.suite)
            self.assertTrue(manifest.is_file(), replay.fixture)
            self.assertTrue(golden.is_file(), replay.suite)

    def test_legacy_settings_replays_have_complete_artifacts(self) -> None:
        self.assertEqual(15, len(replay_rbxport.LEGACY_SETTINGS_REPLAYS))

        for replay in replay_rbxport.LEGACY_SETTINGS_REPLAYS:
            suite = replay_rbxport.ROOT / f"suites/{replay.suite_path}.json"
            manifest = (
                replay_rbxport.ROOT
                / f"fixtures/generated/{replay.fixture}/manifest.json"
            )
            golden = (
                replay_rbxport.ROOT
                / f"goldens/rekordbox-7.2.19/{replay.model}/{replay.suite}.json"
            )

            self.assertTrue(suite.is_file(), replay.suite)
            self.assertTrue(manifest.is_file(), replay.fixture)
            self.assertTrue(golden.is_file(), replay.suite)

    def test_smart_settings_replays_have_complete_artifacts(self) -> None:
        self.assertEqual(17, len(replay_rbxport.SMART_SETTINGS_REPLAYS))

        for replay in replay_rbxport.SMART_SETTINGS_REPLAYS:
            suite = replay_rbxport.ROOT / f"suites/{replay.suite_path}.json"
            manifest = (
                replay_rbxport.ROOT
                / f"fixtures/generated/{replay.fixture}/manifest.json"
            )
            golden = (
                replay_rbxport.ROOT
                / f"goldens/rekordbox-7.2.19/{replay.model}/{replay.suite}.json"
            )

            self.assertTrue(suite.is_file(), replay.suite)
            self.assertTrue(manifest.is_file(), replay.fixture)
            self.assertTrue(golden.is_file(), replay.suite)

    def test_key_notation_replays_have_complete_artifacts(self) -> None:
        self.assertEqual(4, len(replay_rbxport.KEY_NOTATION_REPLAYS))

        for replay in replay_rbxport.KEY_NOTATION_REPLAYS:
            suite = replay_rbxport.ROOT / f"suites/{replay.suite_path}.json"
            manifest = (
                replay_rbxport.ROOT
                / "fixtures/generated/key-notation/manifest.json"
            )
            golden = (
                replay_rbxport.ROOT
                / f"goldens/rekordbox-7.2.19/{replay.model}/{replay.suite}.json"
            )

            self.assertTrue(suite.is_file(), replay.suite)
            self.assertTrue(manifest.is_file())
            self.assertTrue(golden.is_file(), replay.suite)

    def test_category_replays_have_complete_artifacts(self) -> None:
        self.assertEqual(23, len(replay_rbxport.CATEGORY_REPLAYS))

        for replay in replay_rbxport.CATEGORY_REPLAYS:
            suite = replay_rbxport.ROOT / f"suites/{replay.suite_path or replay.suite}.json"
            manifest = (
                replay_rbxport.ROOT
                / f"fixtures/generated/{replay.fixture}/manifest.json"
            )
            golden = (
                replay_rbxport.ROOT
                / f"goldens/rekordbox-7.2.19/{replay.model}/{replay.suite}.json"
            )

            self.assertTrue(suite.is_file(), replay.suite)
            self.assertTrue(manifest.is_file(), replay.fixture)
            self.assertTrue(golden.is_file(), replay.suite)

    def test_moved_sort_is_unique_and_last(self) -> None:
        configured = replay_rbxport.move_sort_last("album")
        self.assertIsNotNone(configured)
        sorts = configured.split(",")

        self.assertEqual(len(replay_rbxport.DEFAULT_SORTS), len(sorts))
        self.assertEqual(len(sorts), len(set(sorts)))
        self.assertEqual("album", sorts[-1])

    def test_search_replays_have_complete_artifacts(self) -> None:
        self.assertEqual(10, len(replay_rbxport.SEARCH_REPLAYS))

        for replay in replay_rbxport.SEARCH_REPLAYS:
            suite = replay_rbxport.ROOT / f"suites/{replay.suite_path or replay.suite}.json"
            manifest = (
                replay_rbxport.ROOT
                / f"fixtures/generated/{replay.fixture}/manifest.json"
            )
            golden = (
                replay_rbxport.ROOT
                / f"goldens/rekordbox-7.2.19/{replay.model}/{replay.suite}.json"
            )

            self.assertTrue(suite.is_file(), replay.suite)
            self.assertTrue(manifest.is_file(), replay.fixture)
            self.assertTrue(golden.is_file(), replay.suite)

    def test_sort_replays_have_complete_artifacts(self) -> None:
        self.assertEqual(20, len(replay_rbxport.SORT_REPLAYS))

        for replay in replay_rbxport.SORT_REPLAYS:
            suite = replay_rbxport.ROOT / f"suites/{replay.suite_path or replay.suite}.json"
            manifest = (
                replay_rbxport.ROOT
                / f"fixtures/generated/{replay.fixture}/manifest.json"
            )
            golden = (
                replay_rbxport.ROOT
                / f"goldens/rekordbox-7.2.19/{replay.model}/{replay.suite}.json"
            )

            self.assertTrue(suite.is_file(), replay.suite)
            self.assertTrue(manifest.is_file(), replay.fixture)
            self.assertTrue(golden.is_file(), replay.suite)

    def test_data_replays_have_complete_artifacts(self) -> None:
        self.assertEqual(27, len(replay_rbxport.DATA_REPLAYS))

        for replay in replay_rbxport.DATA_REPLAYS:
            suite = replay_rbxport.ROOT / f"suites/{replay.suite_path or replay.suite}.json"
            manifest = (
                replay_rbxport.ROOT
                / f"fixtures/generated/{replay.fixture}/manifest.json"
            )
            golden = (
                replay_rbxport.ROOT
                / f"goldens/rekordbox-7.2.19/{replay.model}/{replay.suite}.json"
            )

            self.assertTrue(suite.is_file(), replay.suite)
            self.assertTrue(manifest.is_file(), replay.fixture)
            self.assertTrue(golden.is_file(), replay.suite)

    def test_new_read_only_replays_have_complete_artifacts(self) -> None:
        replays = (
            replay_rbxport.CDJ_2000NEXUS_STATUS_REPLAYS
            + replay_rbxport.ADDITIONAL_READ_ONLY_REPLAYS
        )
        self.assertEqual(19, len(replays))

        for replay in replays:
            suite = (
                replay_rbxport.ROOT
                / f"suites/{replay.suite_path or replay.suite}.json"
            )
            manifest = (
                replay_rbxport.ROOT
                / f"fixtures/generated/{replay.fixture}/manifest.json"
            )
            identity = replay_rbxport.ROOT / f"runs/{replay.identity}"
            golden = (
                replay_rbxport.ROOT
                / f"goldens/rekordbox-7.2.19/{replay.model}/{replay.suite}.json"
            )

            self.assertTrue(suite.is_file(), replay.suite)
            self.assertTrue(manifest.is_file(), replay.fixture)
            self.assertTrue(identity.is_file(), replay.identity)
            self.assertTrue(golden.is_file(), replay.suite)

    def test_read_only_context_replays_have_complete_artifacts(self) -> None:
        self.assertEqual(42, len(replay_rbxport.READ_ONLY_CONTEXT_REPLAYS))

        for replay in replay_rbxport.READ_ONLY_CONTEXT_REPLAYS:
            suite = (
                replay_rbxport.ROOT
                / f"suites/{replay.suite_path or replay.suite}.json"
            )
            manifest = (
                replay_rbxport.ROOT
                / f"fixtures/generated/{replay.fixture}/manifest.json"
            )
            identity = replay_rbxport.ROOT / f"runs/{replay.identity}"
            golden = (
                replay_rbxport.ROOT
                / f"goldens/rekordbox-7.2.19/{replay.model}/{replay.suite}.json"
            )

            self.assertTrue(suite.is_file(), replay.suite)
            self.assertTrue(manifest.is_file(), replay.fixture)
            self.assertTrue(identity.is_file(), replay.identity)
            self.assertTrue(golden.is_file(), replay.suite)

    def test_invalid_selection_controls_are_explicit(self) -> None:
        by_suite = {
            replay.suite: replay for replay in replay_rbxport.SETTINGS_REPLAYS
        }

        self.assertEqual("comment", by_suite["no-secondary-selection"].second_column)
        self.assertEqual(
            "comment", by_suite["multiple-secondary-selections"].second_column
        )


if __name__ == "__main__":
    unittest.main()
