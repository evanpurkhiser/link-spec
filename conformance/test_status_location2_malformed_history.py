import hashlib
import json
import unittest
from pathlib import Path

import generate_status_location2_malformed_history_suites as generator


ROOT = Path(__file__).resolve().parent
MATRIX = ROOT / "data/song-info-location2-malformed-history-matrix.json"
SUITE_ROOT = ROOT / "suites/generated/song-info-location2-malformed-history"


class StatusLocation2MalformedHistoryTests(unittest.TestCase):
    def test_fixture_switch_retries_only_transient_windows_file_locks(self):
        switcher = (ROOT / "switch-fixture.ps1").read_text()

        self.assertIn("$maxAttempts = 15", switcher)
        self.assertIn("$win32Error = $_.Exception.HResult -band 0xffff", switcher)
        self.assertIn("$isTransientLock = $win32Error -in @(32, 33)", switcher)
        self.assertIn("if (-not $isTransientLock -or $attempt -eq $maxAttempts)", switcher)
        self.assertIn("Start-Sleep -Seconds 2", switcher)

    def test_complete_ordered_pair_domain(self) -> None:
        matrix = json.loads(MATRIX.read_text())

        self.assertEqual(matrix["precursor_count"], 16)
        self.assertEqual(matrix["ordered_pair_count"], 256)
        self.assertEqual(matrix["cases_per_pair"], 3)
        self.assertEqual(matrix["pre_request_drain_ms"], 1200)
        self.assertEqual(matrix["delivery_blob_settle_ms"], 3000)
        self.assertEqual(len(set(matrix["precursors"])), 16)
        self.assertEqual(
            {(pair["first"], pair["second"]) for pair in matrix["pairs"]},
            {
                (first, second)
                for first in matrix["precursors"]
                for second in matrix["precursors"]
            },
        )

    def test_checked_in_declarations_match_generator(self) -> None:
        expected_matrix, expected_suites = generator.generate()

        self.assertEqual(json.loads(MATRIX.read_text()), expected_matrix)
        self.assertEqual(
            {path.stem: json.loads(path.read_text()) for path in SUITE_ROOT.glob("*.json")},
            expected_suites,
        )

    def test_every_pair_is_a_three_connection_cold_process_suite(self) -> None:
        matrix = json.loads(MATRIX.read_text())

        for pair in matrix["pairs"]:
            suite = json.loads((SUITE_ROOT / f"{pair['id']}.json").read_text())
            self.assertEqual(suite["repeat_strategy"], "fixture-reset-and-cold-process")
            self.assertEqual(suite["defaults"]["device"], 11)
            self.assertEqual(len(suite["cases"]), 3)
            self.assertTrue(all(case["fresh_connection"] for case in suite["cases"]))
            self.assertTrue(
                all(case["capture_connection_setup"] for case in suite["cases"])
            )
            self.assertTrue(
                all(case["drain_before_request_ms"] == 1200 for case in suite["cases"])
            )
            self.assertFalse(any(case["render"] for case in suite["cases"]))
            self.assertEqual(suite["cases"][-1]["id"], "delivery-probe")
            self.assertEqual(
                suite["cases"][-1]["arguments"][0],
                {"number": "0x0b020301"},
            )
            for previous, following in zip(suite["cases"], suite["cases"][1:]):
                expected_delay = (
                    3000
                    if previous["id"].endswith("--delivery-blob-content")
                    else 0
                )
                self.assertEqual(
                    expected_delay,
                    following.get("delay_before_connection_ms", 0),
                )

    def test_recorder_is_real_rekordbox_only_and_restores_baseline(self) -> None:
        recorder = (ROOT / "record_status_location2_malformed_history_matrix.sh").read_text()

        self.assertNotIn("rbxport", recorder.lower())
        self.assertIn('fixtures/generated/play-paths', recorder)
        self.assertIn('xdj-rx3-player-11-status.json', recorder)
        self.assertIn('"$script_dir/activate_fixture.sh" "$baseline"', recorder)
        self.assertIn('capture_rekordbox_health.ps1', recorder)
        self.assertIn('record_health_before_sha256', recorder)
        self.assertIn('repeat_health_after_sha256', recorder)
        self.assertIn('independently_repeated:true', recorder)

    def test_handoff_requires_the_lifecycle_aware_pinned_runner(self) -> None:
        handoff = (
            ROOT / "run_status_location2_malformed_history_after_compatibility.sh"
        ).read_text()

        self.assertIn('readonly conformance_runner="$script_dir/pinned/link-export-conformance"', handoff)
        self.assertIn('.runner.sha256 "$pinned_manifest"', handoff)
        self.assertIn('conformance_runner_sha256:$conformance_runner_sha256', handoff)
        self.assertIn('if [[ -f $predecessor_receipt ]]', handoff)
        self.assertIn("batch_is_complete()", handoff)
        self.assertIn('expected=$(jq -er .golden_sha256 "$receipt")', handoff)
        self.assertIn("canonical receipts verified; skipping VM", handoff)
        self.assertLess(
            handoff.index('if batch_is_complete "${batch[@]}"'),
            handoff.index("start_isolated_vm", handoff.index("mapfile -t pairs")),
        )

    def test_lifecycle_aware_corpus_is_indexed_without_replacing_history(self) -> None:
        coverage = (ROOT.parent / "docs/CONFORMANCE_COVERAGE.md").read_text()
        sources = (ROOT.parent / "docs/SOURCES.md").read_text()
        cleanup = (ROOT.parent / "docs/CLEANUP.md").read_text()

        self.assertIn("lifecycle-aware ordered pairs", coverage)
        self.assertIn("256 suites / 768 declared requests", coverage)
        self.assertIn(
            "Historical RX3 location-2 malformed-history ordered pairs",
            coverage,
        )
        self.assertIn("47 pairs promoted; pair 48 retained", coverage)
        self.assertNotIn(
            "RX3 location-2 malformed-history ordered pairs | 16 malformed "
            "Play/Delivery precursor forms crossed as every ordered pair in "
            "256 cold-process suites, each followed by the matched location-2 "
            "Delivery probe (768 cases) | Yes | Pending real-Rekordbox execution",
            coverage,
        )
        self.assertIn("malformed-history-lifecycle", sources)
        self.assertIn("47 historical promoted pairs", sources)
        self.assertIn("Keep the earlier", cleanup)
        self.assertIn("pair-48 `.next`/`.actual.json` conflict captures", cleanup)

    def test_reducer_binds_fixture_backend_and_authentic_status_identity(self) -> None:
        reducer = (
            ROOT.parent / "tools/summarize_status_location2_malformed_history.py"
        ).read_text()

        self.assertIn('receipt["fixture_manifest_sha256"]', reducer)
        self.assertIn('receipt["identity_sha256"]', reducer)
        self.assertIn('validate_health_pair(', reducer)
        self.assertIn('"receipt_sha256": sha256(receipt_path)', reducer)
        self.assertIn('provenance["fixture_database_sha256"]', reducer)
        self.assertIn('provenance["fixture_fingerprint"]', reducer)
        self.assertIn('provenance["backend_version"] == "7.2.19"', reducer)
        self.assertIn('provenance["identity"]["player"] == 11', reducer)
        self.assertIn("da12196004059977cdbcd83b9e0ae22366a2daf50320ed1a7b033c1d7ab157d4", reducer)

    def test_partial_reducer_uses_only_promoted_receipt_pairs(self) -> None:
        reducer = (
            ROOT.parent / "tools/summarize_status_location2_malformed_history.py"
        ).read_text()

        self.assertIn('"--allow-partial"', reducer)
        self.assertIn(
            "if not golden_path.is_file() and not receipt_path.is_file()",
            reducer,
        )
        self.assertIn(
            'f"{pair_id}: promoted golden and receipt must exist together"',
            reducer,
        )
        self.assertIn('"summary.partial.json"', reducer)
        self.assertIn('"matrix.partial.csv"', reducer)
        self.assertIn('"next_pending_pair": pending[0] if pending else None', reducer)

    def test_delivery_blob_settle_pair_is_repeat_promoted(self) -> None:
        pair = "play-no-arguments__then__delivery-blob-content"
        suite = json.loads((SUITE_ROOT / f"{pair}.json").read_text())
        golden_path = (
            ROOT
            / "goldens/rekordbox-7.2.19/xdj-rx3-status"
            / "song-info-location2-malformed-history-lifecycle"
            / f"{pair}.json"
        )
        receipt_path = (
            ROOT.parent
            / "data/experiments/song-info-status-location2"
            / "malformed-history-lifecycle/repeats"
            / pair
            / "receipt.json"
        )
        golden = json.loads(golden_path.read_text())
        receipt = json.loads(receipt_path.read_text())

        self.assertEqual(3000, suite["cases"][2]["delay_before_connection_ms"])
        self.assertEqual(
            ["timeout", "timeout", "timeout"],
            [
                case["pre_request_drain"]["outcome"]
                for case in golden["behavior"]["cases"]
            ],
        )
        self.assertEqual(13, golden["behavior"]["cases"][2]["total"])
        self.assertEqual(
            hashlib.sha256((SUITE_ROOT / f"{pair}.json").read_bytes()).hexdigest(),
            receipt["suite_sha256"],
        )
        self.assertEqual(
            hashlib.sha256(golden_path.read_bytes()).hexdigest(),
            receipt["golden_sha256"],
        )

    def test_promoted_play_blob_block_proves_one_delayed_frame_per_blob(self) -> None:
        matrix = json.loads(MATRIX.read_text())
        golden_root = (
            ROOT
            / "goldens/rekordbox-7.2.19/xdj-rx3-status"
            / "song-info-location2-malformed-history-lifecycle"
        )
        repeat_root = (
            ROOT.parent
            / "data/experiments/song-info-status-location2"
            / "malformed-history-lifecycle/repeats"
        )

        for second in matrix["precursors"]:
            pair = f"play-blob-content__then__{second}"
            golden_path = golden_root / f"{pair}.json"
            receipt = json.loads((repeat_root / pair / "receipt.json").read_text())
            golden = json.loads(golden_path.read_text())
            cases = {case["id"]: case for case in golden["behavior"]["cases"]}

            second_drain = cases[f"second--{second}"]["pre_request_drain"]
            self.assertEqual("raw_reply", second_drain["outcome"], pair)
            self.assertEqual(1, len(second_drain["messages"]), pair)
            self.assertEqual(0x4000, second_drain["messages"][0]["kind"], pair)
            self.assertEqual(
                [0x2102, 0],
                [argument["value"] for argument in second_drain["messages"][0]["arguments"]],
                pair,
            )

            probe = cases["delivery-probe"]
            expected_probe_drain = (
                "raw_reply" if second == "play-blob-content" else "timeout"
            )
            self.assertEqual(
                expected_probe_drain,
                probe["pre_request_drain"]["outcome"],
                pair,
            )
            self.assertEqual(13, probe["total"], pair)
            self.assertEqual(
                hashlib.sha256(golden_path.read_bytes()).hexdigest(),
                receipt["golden_sha256"],
                pair,
            )

        protocol = (ROOT.parent / "docs/PROTOCOL_REFERENCE.md").read_text()
        oracle = (ROOT.parent / "docs/SONG_INFO_SIBLINGS_ORACLE.md").read_text()
        self.assertIn("all 16 promoted pairs", protocol)
        self.assertIn("one player-routed delayed header per", protocol)
        self.assertIn("all 16 successors after blob-valued Play", oracle)
        self.assertIn("the other 15 health drains time out", oracle)

    def test_pair_111_race_is_hash_bound_and_not_promoted(self) -> None:
        pair = "play-blob-content__then__delivery-string-content"
        attempt = (
            ROOT.parent
            / "data/experiments/song-info-status-location2"
            / "malformed-history-lifecycle/attempts"
            / "delayed-frame-race-pair111-20261004T152613Z"
        )
        manifest = json.loads((attempt / "manifest.json").read_text())
        record = json.loads((attempt / "record.json").read_text())
        repeat = json.loads((attempt / "repeat.json").read_text())

        self.assertEqual(pair, manifest["pair"])
        self.assertEqual("quarantined-unpromoted", manifest["authority_status"])
        for name, expected in manifest["sha256"].items():
            path = attempt / f"{name.replace('_', '-')}.json"
            if name == "record_health_before":
                path = attempt / "record-health-before.json"
            elif name == "record_health_after":
                path = attempt / "record-health-after.json"
            elif name == "repeat_health_before":
                path = attempt / "repeat-health-before.json"
            elif name == "repeat_runner_output":
                path = attempt / "repeat-runner-output.json"
            self.assertEqual(expected, hashlib.sha256(path.read_bytes()).hexdigest())

        recovery_paths = {
            "candidate_after_z33": "candidate-after-z33.json",
            "z33_repeat": "recovery-z33-repeat.json",
            "z33_repeat_health_before": "recovery-z33-repeat-health-before.json",
        }
        for name, expected in manifest["recovery_sha256"].items():
            path = attempt / recovery_paths[name]
            self.assertEqual(expected, hashlib.sha256(path.read_bytes()).hexdigest())

        z33_repeat = json.loads((attempt / "recovery-z33-repeat.json").read_text())
        z33_cases = {
            case["id"]: case for case in z33_repeat["behavior"]["cases"]
        }
        self.assertEqual(
            "timeout",
            z33_cases["second--delivery-string-content"]["pre_request_drain"][
                "outcome"
            ],
        )
        self.assertEqual(0, z33_cases["second--delivery-string-content"]["total"])
        self.assertEqual(13, z33_cases["delivery-probe"]["total"])

        record_cases = {case["id"]: case for case in record["behavior"]["cases"]}
        repeat_cases = {case["id"]: case for case in repeat["behavior"]["cases"]}
        case_id = "second--delivery-string-content"
        self.assertEqual(
            "raw_reply", record_cases[case_id]["pre_request_drain"]["outcome"]
        )
        self.assertEqual(
            "timeout", repeat_cases[case_id]["pre_request_drain"]["outcome"]
        )
        self.assertEqual(0, record_cases[case_id]["total"])
        self.assertEqual(0, repeat_cases[case_id]["total"])
        self.assertEqual(13, record_cases["delivery-probe"]["total"])
        self.assertEqual(13, repeat_cases["delivery-probe"]["total"])

        record_cases[case_id].pop("pre_request_drain")
        repeat_cases[case_id].pop("pre_request_drain")
        self.assertEqual(record_cases, repeat_cases)

        canonical = manifest["recovery"]["z34"]
        golden = (
            ROOT
            / "goldens/rekordbox-7.2.19/xdj-rx3-status"
            / "song-info-location2-malformed-history-lifecycle"
            / f"{pair}.json"
        )
        receipt = (
            ROOT.parent
            / "data/experiments/song-info-status-location2"
            / "malformed-history-lifecycle/repeats"
            / pair
            / "receipt.json"
        )
        self.assertEqual(
            canonical["canonical_golden_sha256"],
            hashlib.sha256(golden.read_bytes()).hexdigest(),
        )
        self.assertEqual(
            canonical["canonical_receipt_sha256"],
            hashlib.sha256(receipt.read_bytes()).hexdigest(),
        )

    def test_pair_135_race_is_hash_bound_and_not_promoted(self) -> None:
        attempt = (
            ROOT.parent
            / "data/experiments/song-info-status-location2"
            / "malformed-history-lifecycle/attempts"
            / "delayed-frame-race-pair135-20261004T215947Z"
        )
        manifest = json.loads((attempt / "manifest.json").read_text())
        paths = {
            "suite": SUITE_ROOT / f"{manifest['pair']}.json",
            "record": attempt / "record.json",
            "repeat_actual": attempt / "repeat.actual.json",
            "record_health_before": attempt / "record-health-before.json",
            "record_health_after": attempt / "record-health-after.json",
            "repeat_health_before": attempt / "repeat-health-before.json",
        }

        self.assertEqual(
            "play-alternate-location__then__play-blob-content", manifest["pair"]
        )
        self.assertEqual("quarantined-unpromoted", manifest["authority_status"])
        for name, path in paths.items():
            self.assertEqual(
                manifest["sha256"][name], hashlib.sha256(path.read_bytes()).hexdigest()
            )

        record = json.loads(paths["record"].read_text())["behavior"]["cases"]
        repeat = json.loads(paths["repeat_actual"].read_text())["behavior"]["cases"]
        self.assertEqual("timeout", record[2]["pre_request_drain"]["outcome"])
        self.assertEqual("raw_reply", repeat[2]["pre_request_drain"]["outcome"])
        message = repeat[2]["pre_request_drain"]["messages"][0]
        self.assertEqual(0x4000, message["kind"])
        self.assertEqual(
            [0x2102, 0], [argument["value"] for argument in message["arguments"]]
        )
        self.assertEqual(13, record[2]["total"])
        self.assertEqual(13, repeat[2]["total"])

        record[2].pop("pre_request_drain")
        repeat[2].pop("pre_request_drain")
        self.assertEqual(record, repeat)

        canonical = manifest["recovery"]
        golden = (
            ROOT
            / "goldens/rekordbox-7.2.19/xdj-rx3-status"
            / "song-info-location2-malformed-history-lifecycle"
            / f"{manifest['pair']}.json"
        )
        receipt = (
            ROOT.parent
            / "data/experiments/song-info-status-location2"
            / "malformed-history-lifecycle/repeats"
            / manifest["pair"]
            / "receipt.json"
        )
        self.assertEqual(
            canonical["canonical_golden_sha256"],
            hashlib.sha256(golden.read_bytes()).hexdigest(),
        )
        self.assertEqual(
            canonical["canonical_receipt_sha256"],
            hashlib.sha256(receipt.read_bytes()).hexdigest(),
        )

    def test_pair_199_race_is_hash_bound_and_not_promoted(self) -> None:
        attempt = (
            ROOT.parent
            / "data/experiments/song-info-status-location2"
            / "malformed-history-lifecycle/attempts"
            / "delayed-frame-race-pair199-20261005T040132Z"
        )
        manifest = json.loads((attempt / "manifest.json").read_text())

        self.assertEqual(
            "delivery-string-context__then__play-blob-content", manifest["pair"]
        )
        self.assertEqual("repeat-protocol-comparison", manifest["phase"])
        self.assertEqual("quarantined-unpromoted", manifest["authority_status"])
        self.assertTrue(manifest["cleanup"]["live_pair_work_slot_empty"])
        self.assertEqual(
            manifest["cleanup"]["active_guest_manifest_sha256"],
            manifest["cleanup"]["baseline_manifest_sha256"],
        )
        self.assertEqual(
            manifest["cleanup"]["active_guest_database_sha256"],
            manifest["cleanup"]["baseline_database_sha256"],
        )
        self.assertFalse(manifest["cleanup"]["synthetic_identity_units_active"])
        self.assertFalse(manifest["cleanup"]["isolated_vm_containers_active"])

        for name, expected in manifest["artifacts"].items():
            path = attempt / name
            self.assertEqual(expected["bytes"], path.stat().st_size)
            self.assertEqual(
                expected["sha256"], hashlib.sha256(path.read_bytes()).hexdigest()
            )

        suite = SUITE_ROOT / f"{manifest['pair']}.json"
        self.assertEqual(
            manifest["suite_sha256"], hashlib.sha256(suite.read_bytes()).hexdigest()
        )

        record = json.loads((attempt / "record.json").read_text())["behavior"][
            "cases"
        ]
        repeat = json.loads((attempt / "repeat.actual.json").read_text())[
            "behavior"
        ]["cases"]
        self.assertEqual("raw_reply", record[2]["pre_request_drain"]["outcome"])
        self.assertEqual("timeout", repeat[2]["pre_request_drain"]["outcome"])
        message = record[2]["pre_request_drain"]["messages"][0]
        self.assertEqual(0x4000, message["kind"])
        self.assertEqual(
            [0x2102, 0], [argument["value"] for argument in message["arguments"]]
        )
        self.assertEqual(13, record[2]["total"])
        self.assertEqual(13, repeat[2]["total"])

        record[2].pop("pre_request_drain")
        repeat[2].pop("pre_request_drain")
        self.assertEqual(record, repeat)

        journal = (attempt / "service-journal.txt").read_text()
        self.assertIn("case 2 (delivery-probe) differs", journal)
        self.assertIn(
            "Main process exited, code=exited, status=1/FAILURE", journal
        )

        canonical = manifest["recovery"]
        golden = (
            ROOT
            / "goldens/rekordbox-7.2.19/xdj-rx3-status"
            / "song-info-location2-malformed-history-lifecycle"
            / f"{manifest['pair']}.json"
        )
        receipt = (
            ROOT.parent
            / "data/experiments/song-info-status-location2"
            / "malformed-history-lifecycle/repeats"
            / manifest["pair"]
            / "receipt.json"
        )
        self.assertEqual(
            canonical["canonical_golden_sha256"],
            hashlib.sha256(golden.read_bytes()).hexdigest(),
        )
        self.assertEqual(
            canonical["canonical_receipt_sha256"],
            hashlib.sha256(receipt.read_bytes()).hexdigest(),
        )

    def test_pair_215_race_is_hash_bound_and_not_promoted(self) -> None:
        attempt = (
            ROOT.parent
            / "data/experiments/song-info-status-location2"
            / "malformed-history-lifecycle/attempts"
            / "delayed-frame-race-pair215-20261005T052641Z"
        )
        manifest = json.loads((attempt / "manifest.json").read_text())

        self.assertEqual(
            "delivery-blob-context__then__play-blob-content", manifest["pair"]
        )
        self.assertEqual("repeat-protocol-comparison", manifest["phase"])
        self.assertEqual("quarantined-unpromoted", manifest["authority_status"])
        self.assertTrue(manifest["cleanup"]["live_pair_work_slot_empty"])
        self.assertEqual(
            manifest["cleanup"]["active_guest_manifest_sha256"],
            manifest["cleanup"]["baseline_manifest_sha256"],
        )
        self.assertEqual(
            manifest["cleanup"]["active_guest_database_sha256"],
            manifest["cleanup"]["baseline_database_sha256"],
        )
        self.assertFalse(manifest["cleanup"]["synthetic_identity_units_active"])
        self.assertFalse(manifest["cleanup"]["isolated_vm_containers_active"])

        for name, expected in manifest["artifacts"].items():
            path = attempt / name
            self.assertEqual(expected["bytes"], path.stat().st_size)
            self.assertEqual(
                expected["sha256"], hashlib.sha256(path.read_bytes()).hexdigest()
            )

        suite = SUITE_ROOT / f"{manifest['pair']}.json"
        self.assertEqual(
            manifest["suite_sha256"], hashlib.sha256(suite.read_bytes()).hexdigest()
        )

        record = json.loads((attempt / "record.json").read_text())["behavior"][
            "cases"
        ]
        repeat = json.loads((attempt / "repeat.actual.json").read_text())[
            "behavior"
        ]["cases"]
        self.assertEqual("timeout", record[2]["pre_request_drain"]["outcome"])
        self.assertEqual("raw_reply", repeat[2]["pre_request_drain"]["outcome"])
        message = repeat[2]["pre_request_drain"]["messages"][0]
        self.assertEqual(0x4000, message["kind"])
        self.assertEqual(
            [0x2102, 0], [argument["value"] for argument in message["arguments"]]
        )
        self.assertEqual(13, record[2]["total"])
        self.assertEqual(13, repeat[2]["total"])

        record[2].pop("pre_request_drain")
        repeat[2].pop("pre_request_drain")
        self.assertEqual(record, repeat)

        journal = (attempt / "service-journal.txt").read_text()
        self.assertIn("case 2 (delivery-probe) differs", journal)
        self.assertIn(
            "Main process exited, code=exited, status=1/FAILURE", journal
        )

    def test_pair_215_reverse_race_is_hash_bound_and_not_promoted(self) -> None:
        attempt = (
            ROOT.parent
            / "data/experiments/song-info-status-location2"
            / "malformed-history-lifecycle/attempts"
            / "delayed-frame-reverse-race-pair215-20261005T134949Z"
        )
        manifest = json.loads((attempt / "manifest.json").read_text())

        self.assertEqual(
            "delivery-blob-context__then__play-blob-content", manifest["pair"]
        )
        self.assertEqual("quarantined-unpromoted", manifest["authority_status"])
        self.assertTrue(manifest["cleanup"]["live_pair_work_slot_empty"])
        self.assertEqual(
            manifest["cleanup"]["active_guest_database_sha256"],
            manifest["cleanup"]["baseline_database_sha256"],
        )
        for name, expected in manifest["artifacts"].items():
            path = attempt / name
            self.assertEqual(expected["bytes"], path.stat().st_size)
            self.assertEqual(
                expected["sha256"], hashlib.sha256(path.read_bytes()).hexdigest()
            )

        record = json.loads((attempt / "record.json").read_text())["behavior"][
            "cases"
        ]
        repeat = json.loads((attempt / "repeat.actual.json").read_text())[
            "behavior"
        ]["cases"]
        self.assertEqual("raw_reply", record[2]["pre_request_drain"]["outcome"])
        self.assertEqual("timeout", repeat[2]["pre_request_drain"]["outcome"])
        message = record[2]["pre_request_drain"]["messages"][0]
        self.assertEqual(0x4000, message["kind"])
        self.assertEqual(
            [0x2102, 0], [argument["value"] for argument in message["arguments"]]
        )
        self.assertEqual(13, record[2]["total"])
        self.assertEqual(13, repeat[2]["total"])

        record[2].pop("pre_request_drain")
        repeat[2].pop("pre_request_drain")
        self.assertEqual(record, repeat)

        journal = (attempt / "service-journal.txt").read_text()
        self.assertIn("case 2 (delivery-probe) differs", journal)
        self.assertIn(
            "Main process exited, code=exited, status=1/FAILURE", journal
        )

    def test_pair_215_third_race_is_hash_bound_and_not_promoted(self) -> None:
        attempt = (
            ROOT.parent
            / "data/experiments/song-info-status-location2"
            / "malformed-history-lifecycle/attempts"
            / "delayed-frame-repeat-timeout-pair215-20261005T135600Z"
        )
        manifest = json.loads((attempt / "manifest.json").read_text())

        self.assertEqual(
            "delivery-blob-context__then__play-blob-content", manifest["pair"]
        )
        self.assertEqual("quarantined-unpromoted", manifest["authority_status"])
        for name, expected in manifest["artifacts"].items():
            path = attempt / name
            self.assertEqual(expected["bytes"], path.stat().st_size)
            self.assertEqual(
                expected["sha256"], hashlib.sha256(path.read_bytes()).hexdigest()
            )

        record = json.loads((attempt / "record.json").read_text())["behavior"][
            "cases"
        ]
        repeat = json.loads((attempt / "repeat.actual.json").read_text())[
            "behavior"
        ]["cases"]
        self.assertEqual("raw_reply", record[2]["pre_request_drain"]["outcome"])
        self.assertEqual("timeout", repeat[2]["pre_request_drain"]["outcome"])
        self.assertEqual(13, record[2]["total"])
        self.assertEqual(13, repeat[2]["total"])
        record[2].pop("pre_request_drain")
        repeat[2].pop("pre_request_drain")
        self.assertEqual(record, repeat)

        journal = (attempt / "service-journal.txt").read_text()
        self.assertIn("case 2 (delivery-probe) differs", journal)
        self.assertIn(
            "Main process exited, code=exited, status=1/FAILURE", journal
        )

    def test_pair_141_link_activation_failure_is_hash_bound(self) -> None:
        attempt = (
            ROOT.parent
            / "data/experiments/song-info-status-location2"
            / "malformed-history-lifecycle/attempts"
            / "link-activation-failure-pair141-20261004T224720Z"
        )
        manifest = json.loads((attempt / "manifest.json").read_text())

        self.assertEqual(
            "play-alternate-location__then__delivery-string-context",
            manifest["pair"],
        )
        self.assertEqual("record-link-activation", manifest["phase"])
        self.assertEqual(10, manifest["activation_attempts"])
        self.assertFalse(manifest["protocol_candidate_created"])
        self.assertFalse(manifest["repeat_started"])
        self.assertEqual(
            manifest["cleanup"]["active_guest_manifest_sha256"],
            manifest["cleanup"]["baseline_manifest_sha256"],
        )
        self.assertFalse(manifest["cleanup"]["synthetic_identity_units_active"])
        self.assertFalse(manifest["cleanup"]["isolated_vm_containers_active"])

        for name, expected in manifest["artifacts"].items():
            path = attempt / name
            self.assertEqual(expected["bytes"], path.stat().st_size)
            self.assertEqual(
                expected["sha256"], hashlib.sha256(path.read_bytes()).hexdigest()
            )

        journal = (attempt / "service-journal.txt").read_text()
        self.assertIn("retrying activation (10/10)", journal)
        self.assertIn("Main process exited, code=exited, status=1/FAILURE", journal)

    def test_pair_141_guest_readiness_timeout_is_hash_bound(self) -> None:
        attempt = (
            ROOT.parent
            / "data/experiments/song-info-status-location2"
            / "malformed-history-lifecycle/attempts"
            / "guest-readiness-timeout-pair141-20261004T225522Z"
        )
        manifest = json.loads((attempt / "manifest.json").read_text())

        self.assertEqual(
            "play-alternate-location__then__delivery-string-context",
            manifest["pair"],
        )
        self.assertEqual("third-batch-vm-start", manifest["phase"])
        self.assertEqual(300, manifest["guest_wait_seconds"])
        self.assertFalse(manifest["protocol_candidate_created"])
        self.assertFalse(manifest["repeat_started"])
        self.assertEqual([], manifest["pair_artifacts_created"])
        self.assertEqual(
            manifest["cleanup"]["active_guest_manifest_sha256"],
            manifest["cleanup"]["baseline_manifest_sha256"],
        )

        for name, expected in manifest["artifacts"].items():
            path = attempt / name
            self.assertEqual(expected["bytes"], path.stat().st_size)
            self.assertEqual(
                expected["sha256"], hashlib.sha256(path.read_bytes()).hexdigest()
            )

        wrapper = ROOT / "run_status_location2_malformed_history_after_compatibility.sh"
        self.assertEqual(
            manifest["recovery"]["updated_wrapper_sha256"],
            hashlib.sha256(wrapper.read_bytes()).hexdigest(),
        )
        journal = (attempt / "service-journal.txt").read_text()
        self.assertIn("Main process exited, code=exited, status=1/FAILURE", journal)

    def test_pair_141_stale_work_slot_guard_is_hash_bound(self) -> None:
        attempt = (
            ROOT.parent
            / "data/experiments/song-info-status-location2"
            / "malformed-history-lifecycle/attempts"
            / "stale-work-slot-pair141-20261004T230030Z"
        )
        manifest = json.loads((attempt / "manifest.json").read_text())

        self.assertEqual("record-resume-guard", manifest["phase"])
        self.assertEqual("incomplete record-side evidence", manifest["guard"])
        self.assertFalse(manifest["protocol_candidate_created"])
        self.assertFalse(manifest["repeat_started"])
        self.assertTrue(manifest["cleanup"]["work_slot_empty"])

        for name, expected in manifest["artifacts"].items():
            path = attempt / name
            self.assertEqual(expected["bytes"], path.stat().st_size)
            self.assertEqual(
                expected["sha256"], hashlib.sha256(path.read_bytes()).hexdigest()
            )

        journal = (attempt / "service-journal.txt").read_text()
        self.assertIn("incomplete record-side evidence", journal)
        self.assertIn("status=1/FAILURE", journal)

    def test_pair_194_repeat_link_activation_failure_is_hash_bound(self) -> None:
        attempt = (
            ROOT.parent
            / "data/experiments/song-info-status-location2"
            / "malformed-history-lifecycle/attempts"
            / "link-activation-failure-pair194-20261005T033128Z"
        )
        manifest = json.loads((attempt / "manifest.json").read_text())

        self.assertEqual(
            "delivery-string-context__then__play-missing-content",
            manifest["pair"],
        )
        self.assertEqual("repeat-link-activation", manifest["phase"])
        self.assertEqual("quarantined-unpromoted", manifest["authority_status"])
        self.assertEqual(10, manifest["activation_attempts"])
        self.assertTrue(manifest["protocol_record_candidate_created"])
        self.assertFalse(manifest["repeat_protocol_candidate_created"])
        self.assertEqual(
            manifest["cleanup"]["active_guest_manifest_sha256"],
            manifest["cleanup"]["baseline_manifest_sha256"],
        )
        self.assertEqual(
            manifest["cleanup"]["active_guest_database_sha256"],
            manifest["cleanup"]["baseline_database_sha256"],
        )
        self.assertFalse(manifest["cleanup"]["synthetic_identity_units_active"])
        self.assertFalse(manifest["cleanup"]["isolated_vm_containers_active"])

        for name, expected in manifest["artifacts"].items():
            path = attempt / name
            self.assertEqual(expected["bytes"], path.stat().st_size)
            self.assertEqual(
                expected["sha256"], hashlib.sha256(path.read_bytes()).hexdigest()
            )

        journal = (attempt / "service-journal.txt").read_text()
        self.assertIn("retrying activation (10/10)", journal)
        self.assertIn("Main process exited, code=exited, status=1/FAILURE", journal)

    def test_zero_context_precursor_is_silent_and_health_preserving(self) -> None:
        expectations = {
            "play-no-arguments": ("timeout", None),
            "play-missing-content": ("menu", 0),
            "play-extra-argument": ("menu", 7),
            "play-string-context": ("menu", None),
            "play-blob-context": ("menu", None),
            "play-string-content": ("menu", 0),
            "play-blob-content": ("menu", None),
            "play-zero-context": ("timeout", None),
            "play-alternate-location": ("menu", 7),
            "delivery-no-arguments": ("timeout", None),
            "delivery-missing-content": ("menu", 0),
            "delivery-extra-argument": ("menu", 13),
            "delivery-string-context": ("menu", None),
            "delivery-blob-context": ("menu", None),
            "delivery-string-content": ("menu", 0),
            "delivery-blob-content": ("menu", None),
        }
        golden_root = (
            ROOT
            / "goldens/rekordbox-7.2.19/xdj-rx3-status"
            / "song-info-location2-malformed-history-lifecycle"
        )
        repeat_root = (
            ROOT.parent
            / "data/experiments/song-info-status-location2"
            / "malformed-history-lifecycle/repeats"
        )
        self.assertEqual(
            set(json.loads(MATRIX.read_text())["precursors"]),
            set(expectations) | {"play-blob-content"},
        )

        for successor, expected in expectations.items():
            pair = f"play-zero-context__then__{successor}"
            golden_path = golden_root / f"{pair}.json"
            receipt = json.loads((repeat_root / pair / "receipt.json").read_text())
            cases = json.loads(golden_path.read_text())["behavior"]["cases"]

            self.assertEqual("timeout", cases[0]["outcome"], pair)
            self.assertEqual(expected, (cases[1]["outcome"], cases[1]["total"]), pair)
            expected_drains = (
                ["timeout", "timeout", "raw_reply"]
                if successor == "play-blob-content"
                else ["timeout", "timeout", "timeout"]
            )
            self.assertEqual(
                expected_drains,
                [case["pre_request_drain"]["outcome"] for case in cases],
                pair,
            )
            if successor == "play-blob-content":
                message = cases[2]["pre_request_drain"]["messages"][0]
                self.assertEqual(0x4000, message["kind"], pair)
                self.assertEqual(
                    [0x2102, 0],
                    [argument["value"] for argument in message["arguments"]],
                    pair,
                )
            self.assertEqual(13, cases[2]["total"], pair)
            self.assertEqual(
                receipt["golden_sha256"],
                hashlib.sha256(golden_path.read_bytes()).hexdigest(),
                pair,
            )

    def test_second_blob_play_queues_its_own_health_drain_reply(self) -> None:
        pair = "play-zero-context__then__play-blob-content"
        golden_path = (
            ROOT
            / "goldens/rekordbox-7.2.19/xdj-rx3-status"
            / "song-info-location2-malformed-history-lifecycle"
            / f"{pair}.json"
        )
        receipt_path = (
            ROOT.parent
            / "data/experiments/song-info-status-location2"
            / "malformed-history-lifecycle/repeats"
            / pair
            / "receipt.json"
        )
        cases = json.loads(golden_path.read_text())["behavior"]["cases"]
        receipt = json.loads(receipt_path.read_text())

        self.assertEqual(
            ["timeout", "timeout", "raw_reply"],
            [case["pre_request_drain"]["outcome"] for case in cases],
        )
        message = cases[2]["pre_request_drain"]["messages"][0]
        self.assertEqual(0x4000, message["kind"])
        self.assertEqual(
            [0x2102, 0], [argument["value"] for argument in message["arguments"]]
        )
        self.assertEqual(13, cases[2]["total"])
        self.assertEqual(
            receipt["golden_sha256"], hashlib.sha256(golden_path.read_bytes()).hexdigest()
        )

    def test_alternate_location_precursor_preserves_successor_and_health(self) -> None:
        expectations = {
            "play-no-arguments": ("timeout", None),
            "play-missing-content": ("menu", 0),
            "play-extra-argument": ("menu", 7),
            "play-string-context": ("menu", None),
            "play-blob-context": ("menu", None),
            "play-string-content": ("menu", 0),
            "play-zero-context": ("timeout", None),
            "play-alternate-location": ("menu", 7),
            "delivery-no-arguments": ("timeout", None),
            "delivery-missing-content": ("menu", 0),
            "delivery-extra-argument": ("menu", 13),
            "delivery-string-context": ("menu", None),
            "delivery-blob-context": ("menu", None),
            "delivery-string-content": ("menu", 0),
            "delivery-blob-content": ("menu", None),
        }
        golden_root = (
            ROOT
            / "goldens/rekordbox-7.2.19/xdj-rx3-status"
            / "song-info-location2-malformed-history-lifecycle"
        )
        repeat_root = (
            ROOT.parent
            / "data/experiments/song-info-status-location2"
            / "malformed-history-lifecycle/repeats"
        )
        self.assertEqual(
            set(json.loads(MATRIX.read_text())["precursors"]),
            set(expectations) | {"play-blob-content"},
        )

        for successor, expected in expectations.items():
            pair = f"play-alternate-location__then__{successor}"
            golden_path = golden_root / f"{pair}.json"
            receipt = json.loads((repeat_root / pair / "receipt.json").read_text())
            cases = json.loads(golden_path.read_text())["behavior"]["cases"]

            self.assertEqual(("menu", 7), (cases[0]["outcome"], cases[0]["total"]))
            self.assertEqual(expected, (cases[1]["outcome"], cases[1]["total"]))
            self.assertEqual(
                ["timeout", "timeout", "timeout"],
                [case["pre_request_drain"]["outcome"] for case in cases],
            )
            self.assertEqual(13, cases[2]["total"])
            self.assertEqual(
                receipt["golden_sha256"],
                hashlib.sha256(golden_path.read_bytes()).hexdigest(),
            )

        blob_pair = "play-alternate-location__then__play-blob-content"
        blob_path = golden_root / f"{blob_pair}.json"
        blob_cases = json.loads(blob_path.read_text())["behavior"]["cases"]
        blob_receipt = json.loads((repeat_root / blob_pair / "receipt.json").read_text())
        self.assertEqual(("menu", 7), (blob_cases[0]["outcome"], blob_cases[0]["total"]))
        self.assertEqual(("menu", None), (blob_cases[1]["outcome"], blob_cases[1]["total"]))
        self.assertEqual(
            ["timeout", "timeout", "raw_reply"],
            [case["pre_request_drain"]["outcome"] for case in blob_cases],
        )
        message = blob_cases[2]["pre_request_drain"]["messages"][0]
        self.assertEqual(0x4000, message["kind"])
        self.assertEqual(
            [0x2102, 0], [argument["value"] for argument in message["arguments"]]
        )
        self.assertEqual(13, blob_cases[2]["total"])
        self.assertEqual(
            blob_receipt["golden_sha256"], hashlib.sha256(blob_path.read_bytes()).hexdigest()
        )

    def test_argumentless_delivery_precursor_is_silent_and_health_preserving(self) -> None:
        expectations = {
            "play-no-arguments": ("timeout", None),
            "play-missing-content": ("menu", 0),
            "play-extra-argument": ("menu", 7),
            "play-string-context": ("menu", None),
            "play-blob-context": ("menu", None),
            "play-string-content": ("menu", 0),
            "play-blob-content": ("menu", None),
            "play-zero-context": ("timeout", None),
            "play-alternate-location": ("menu", 7),
            "delivery-no-arguments": ("timeout", None),
            "delivery-missing-content": ("menu", 0),
            "delivery-extra-argument": ("menu", 13),
            "delivery-string-context": ("menu", None),
            "delivery-blob-context": ("menu", None),
            "delivery-string-content": ("menu", 0),
            "delivery-blob-content": ("menu", None),
        }
        golden_root = (
            ROOT
            / "goldens/rekordbox-7.2.19/xdj-rx3-status"
            / "song-info-location2-malformed-history-lifecycle"
        )
        repeat_root = (
            ROOT.parent
            / "data/experiments/song-info-status-location2"
            / "malformed-history-lifecycle/repeats"
        )

        for successor, expected in expectations.items():
            pair = f"delivery-no-arguments__then__{successor}"
            golden_path = golden_root / f"{pair}.json"
            receipt = json.loads((repeat_root / pair / "receipt.json").read_text())
            cases = json.loads(golden_path.read_text())["behavior"]["cases"]

            self.assertEqual("timeout", cases[0]["outcome"], pair)
            self.assertEqual(expected, (cases[1]["outcome"], cases[1]["total"]), pair)
            expected_drains = (
                ["timeout", "timeout", "raw_reply"]
                if successor == "play-blob-content"
                else ["timeout", "timeout", "timeout"]
            )
            self.assertEqual(
                expected_drains,
                [case["pre_request_drain"]["outcome"] for case in cases],
                pair,
            )
            if successor == "play-blob-content":
                message = cases[2]["pre_request_drain"]["messages"][0]
                self.assertEqual(0x4000, message["kind"], pair)
                self.assertEqual(
                    [0x2102, 0],
                    [argument["value"] for argument in message["arguments"]],
                    pair,
                )
            self.assertEqual(13, cases[2]["total"], pair)
            self.assertEqual(
                receipt["golden_sha256"],
                hashlib.sha256(golden_path.read_bytes()).hexdigest(),
                pair,
            )

    def test_missing_content_delivery_precursor_preserves_successor_and_health(self) -> None:
        expectations = {
            "play-no-arguments": ("timeout", None),
            "play-missing-content": ("menu", 0),
            "play-extra-argument": ("menu", 7),
            "play-string-context": ("menu", None),
            "play-blob-context": ("menu", None),
            "play-string-content": ("menu", 0),
            "play-blob-content": ("menu", None),
            "play-zero-context": ("timeout", None),
            "play-alternate-location": ("menu", 7),
            "delivery-no-arguments": ("timeout", None),
            "delivery-missing-content": ("menu", 0),
            "delivery-extra-argument": ("menu", 13),
            "delivery-string-context": ("menu", None),
            "delivery-blob-context": ("menu", None),
            "delivery-string-content": ("menu", 0),
            "delivery-blob-content": ("menu", None),
        }
        golden_root = (
            ROOT
            / "goldens/rekordbox-7.2.19/xdj-rx3-status"
            / "song-info-location2-malformed-history-lifecycle"
        )
        repeat_root = (
            ROOT.parent
            / "data/experiments/song-info-status-location2"
            / "malformed-history-lifecycle/repeats"
        )

        for successor, expected in expectations.items():
            pair = f"delivery-missing-content__then__{successor}"
            golden_path = golden_root / f"{pair}.json"
            receipt = json.loads((repeat_root / pair / "receipt.json").read_text())
            cases = json.loads(golden_path.read_text())["behavior"]["cases"]

            self.assertEqual(("menu", 0), (cases[0]["outcome"], cases[0]["total"]))
            self.assertEqual(expected, (cases[1]["outcome"], cases[1]["total"]), pair)
            expected_drains = (
                ["timeout", "timeout", "raw_reply"]
                if successor == "play-blob-content"
                else ["timeout", "timeout", "timeout"]
            )
            self.assertEqual(
                expected_drains,
                [case["pre_request_drain"]["outcome"] for case in cases],
                pair,
            )
            if successor == "play-blob-content":
                message = cases[2]["pre_request_drain"]["messages"][0]
                self.assertEqual(0x4000, message["kind"], pair)
                self.assertEqual(
                    [0x2102, 0],
                    [argument["value"] for argument in message["arguments"]],
                    pair,
                )
            self.assertEqual(13, cases[2]["total"], pair)
            self.assertEqual(
                receipt["golden_sha256"],
                hashlib.sha256(golden_path.read_bytes()).hexdigest(),
                pair,
            )

    def test_extra_argument_delivery_precursor_preserves_successor_and_health(self) -> None:
        expectations = {
            "play-no-arguments": ("timeout", None),
            "play-missing-content": ("menu", 0),
            "play-extra-argument": ("menu", 7),
            "play-string-context": ("menu", None),
            "play-blob-context": ("menu", None),
            "play-string-content": ("menu", 0),
            "play-blob-content": ("menu", None),
            "play-zero-context": ("timeout", None),
            "play-alternate-location": ("menu", 7),
            "delivery-no-arguments": ("timeout", None),
            "delivery-missing-content": ("menu", 0),
            "delivery-extra-argument": ("menu", 13),
            "delivery-string-context": ("menu", None),
            "delivery-blob-context": ("menu", None),
            "delivery-string-content": ("menu", 0),
            "delivery-blob-content": ("menu", None),
        }
        golden_root = (
            ROOT
            / "goldens/rekordbox-7.2.19/xdj-rx3-status"
            / "song-info-location2-malformed-history-lifecycle"
        )
        repeat_root = (
            ROOT.parent
            / "data/experiments/song-info-status-location2"
            / "malformed-history-lifecycle/repeats"
        )

        for successor, expected in expectations.items():
            pair = f"delivery-extra-argument__then__{successor}"
            golden_path = golden_root / f"{pair}.json"
            receipt = json.loads((repeat_root / pair / "receipt.json").read_text())
            cases = json.loads(golden_path.read_text())["behavior"]["cases"]

            self.assertEqual(("menu", 13), (cases[0]["outcome"], cases[0]["total"]))
            self.assertEqual(expected, (cases[1]["outcome"], cases[1]["total"]), pair)
            expected_drains = (
                ["timeout", "timeout", "raw_reply"]
                if successor == "play-blob-content"
                else ["timeout", "timeout", "timeout"]
            )
            self.assertEqual(
                expected_drains,
                [case["pre_request_drain"]["outcome"] for case in cases],
                pair,
            )
            if successor == "play-blob-content":
                message = cases[2]["pre_request_drain"]["messages"][0]
                self.assertEqual(0x4000, message["kind"], pair)
                self.assertEqual(
                    [0x2102, 0],
                    [argument["value"] for argument in message["arguments"]],
                    pair,
                )
            self.assertEqual(13, cases[2]["total"], pair)
            self.assertEqual(
                receipt["golden_sha256"],
                hashlib.sha256(golden_path.read_bytes()).hexdigest(),
                pair,
            )

    def test_string_context_delivery_precursor_preserves_successor_and_health(self) -> None:
        expectations = {
            "play-no-arguments": ("timeout", None),
            "play-missing-content": ("menu", 0),
            "play-extra-argument": ("menu", 7),
            "play-string-context": ("menu", None),
            "play-blob-context": ("menu", None),
            "play-string-content": ("menu", 0),
            "play-blob-content": ("menu", None),
            "play-zero-context": ("timeout", None),
            "play-alternate-location": ("menu", 7),
            "delivery-no-arguments": ("timeout", None),
            "delivery-missing-content": ("menu", 0),
            "delivery-extra-argument": ("menu", 13),
            "delivery-string-context": ("menu", None),
            "delivery-blob-context": ("menu", None),
            "delivery-string-content": ("menu", 0),
            "delivery-blob-content": ("menu", None),
        }
        golden_root = (
            ROOT
            / "goldens/rekordbox-7.2.19/xdj-rx3-status"
            / "song-info-location2-malformed-history-lifecycle"
        )
        repeat_root = (
            ROOT.parent
            / "data/experiments/song-info-status-location2"
            / "malformed-history-lifecycle/repeats"
        )

        for successor, expected in expectations.items():
            pair = f"delivery-string-context__then__{successor}"
            golden_path = golden_root / f"{pair}.json"
            receipt = json.loads((repeat_root / pair / "receipt.json").read_text())
            cases = json.loads(golden_path.read_text())["behavior"]["cases"]

            self.assertEqual(("menu", None), (cases[0]["outcome"], cases[0]["total"]))
            self.assertEqual(expected, (cases[1]["outcome"], cases[1]["total"]), pair)
            expected_drains = (
                ["timeout", "timeout", "raw_reply"]
                if successor == "play-blob-content"
                else ["timeout", "timeout", "timeout"]
            )
            self.assertEqual(
                expected_drains,
                [case["pre_request_drain"]["outcome"] for case in cases],
                pair,
            )
            if successor == "play-blob-content":
                message = cases[2]["pre_request_drain"]["messages"][0]
                self.assertEqual(0x4000, message["kind"], pair)
                self.assertEqual(
                    [0x2102, 0],
                    [argument["value"] for argument in message["arguments"]],
                    pair,
                )
            self.assertEqual(13, cases[2]["total"], pair)
            self.assertEqual(
                receipt["golden_sha256"],
                hashlib.sha256(golden_path.read_bytes()).hexdigest(),
                pair,
            )

    def test_blob_context_delivery_precursor_preserves_successor_and_health(self) -> None:
        expectations = {
            "play-no-arguments": ("timeout", None),
            "play-missing-content": ("menu", 0),
            "play-extra-argument": ("menu", 7),
            "play-string-context": ("menu", None),
            "play-blob-context": ("menu", None),
            "play-string-content": ("menu", 0),
            "play-blob-content": ("menu", None),
            "play-zero-context": ("timeout", None),
            "play-alternate-location": ("menu", 7),
            "delivery-no-arguments": ("timeout", None),
            "delivery-missing-content": ("menu", 0),
            "delivery-extra-argument": ("menu", 13),
            "delivery-string-context": ("menu", None),
            "delivery-blob-context": ("menu", None),
            "delivery-string-content": ("menu", 0),
            "delivery-blob-content": ("menu", None),
        }
        golden_root = (
            ROOT
            / "goldens/rekordbox-7.2.19/xdj-rx3-status"
            / "song-info-location2-malformed-history-lifecycle"
        )
        repeat_root = (
            ROOT.parent
            / "data/experiments/song-info-status-location2"
            / "malformed-history-lifecycle/repeats"
        )

        for successor, expected in expectations.items():
            pair = f"delivery-blob-context__then__{successor}"
            golden_path = golden_root / f"{pair}.json"
            receipt = json.loads((repeat_root / pair / "receipt.json").read_text())
            cases = json.loads(golden_path.read_text())["behavior"]["cases"]

            self.assertEqual(("menu", None), (cases[0]["outcome"], cases[0]["total"]))
            self.assertEqual(expected, (cases[1]["outcome"], cases[1]["total"]), pair)
            expected_drains = (
                ["timeout", "timeout", "raw_reply"]
                if successor == "play-blob-content"
                else ["timeout", "timeout", "timeout"]
            )
            self.assertEqual(
                expected_drains,
                [case["pre_request_drain"]["outcome"] for case in cases],
                pair,
            )
            if successor == "play-blob-content":
                message = cases[2]["pre_request_drain"]["messages"][0]
                self.assertEqual(0x4000, message["kind"], pair)
                self.assertEqual(
                    [0x2102, 0],
                    [argument["value"] for argument in message["arguments"]],
                    pair,
                )
            self.assertEqual(13, cases[2]["total"], pair)
            self.assertEqual(
                receipt["golden_sha256"],
                hashlib.sha256(golden_path.read_bytes()).hexdigest(),
                pair,
            )

    def test_string_content_delivery_precursor_preserves_successor_and_health(self) -> None:
        expectations = {
            "play-no-arguments": ("timeout", None),
            "play-missing-content": ("menu", 0),
            "play-extra-argument": ("menu", 7),
            "play-string-context": ("menu", None),
        }
        golden_root = (
            ROOT
            / "goldens/rekordbox-7.2.19/xdj-rx3-status"
            / "song-info-location2-malformed-history-lifecycle"
        )
        repeat_root = (
            ROOT.parent
            / "data/experiments/song-info-status-location2"
            / "malformed-history-lifecycle/repeats"
        )

        for successor, expected in expectations.items():
            pair = f"delivery-string-content__then__{successor}"
            golden_path = golden_root / f"{pair}.json"
            receipt = json.loads((repeat_root / pair / "receipt.json").read_text())
            cases = json.loads(golden_path.read_text())["behavior"]["cases"]

            self.assertEqual(("menu", 0), (cases[0]["outcome"], cases[0]["total"]))
            self.assertEqual(expected, (cases[1]["outcome"], cases[1]["total"]), pair)
            self.assertEqual(
                ["timeout", "timeout", "timeout"],
                [case["pre_request_drain"]["outcome"] for case in cases],
                pair,
            )
            self.assertEqual(13, cases[2]["total"], pair)
            self.assertEqual(
                receipt["golden_sha256"],
                hashlib.sha256(golden_path.read_bytes()).hexdigest(),
                pair,
            )


if __name__ == "__main__":
    unittest.main()
