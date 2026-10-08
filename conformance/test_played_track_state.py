import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BINARY_RELATIVE = (
    "../artifacts/rekordbox/7.2.19/extracted/app-root/rekordbox.app/"
    "Contents/MacOS/rekordbox"
)
BINARY = ROOT / BINARY_RELATIVE
XREFS = ROOT / "data/static-analysis/played-track-cache-member-xrefs.txt"
DISASSEMBLY = ROOT / "data/static-analysis/played-track-cache.disasm.txt"
PRODUCERS = ROOT / "data/static-analysis/played-track-producers.disasm.txt"
NAVIGATION = ROOT / "data/static-analysis/xdj-rr-client-navigation.json"
SUITE = ROOT / "conformance/suites/link-played-state.json"
SETTINGS_GENERATOR = ROOT / "conformance/generate_played_state_settings.py"
SETTINGS = ROOT / "data/experiments/played-track-state/settings"
RECORDER = ROOT / "conformance/record_link_played_state.sh"
REDUCER = ROOT / "tools/summarize_link_played_state.py"
PERSISTENCE_PRIME_SUITE = ROOT / "conformance/suites/link-played-persistence-prime.json"
PERSISTENCE_RESTART_SUITE = ROOT / "conformance/suites/link-played-persistence-restart.json"
PERSISTENCE_RECORDER = ROOT / "conformance/record_link_played_persistence_restart.sh"
PERSISTENCE_REDUCER = ROOT / "tools/summarize_link_played_persistence_restart.py"
PERSISTENCE_HANDOFF = ROOT / "conformance/run_link_played_persistence_after_transition.sh"
LINK_TOGGLE_SUITE = ROOT / "conformance/suites/link-played-link-toggle-post.json"
LINK_TOGGLE_RECORDER = ROOT / "conformance/record_link_played_link_toggle.sh"
LINK_TOGGLE_REDUCER = ROOT / "tools/summarize_link_played_link_toggle.py"
LINK_TOGGLE_HANDOFF = ROOT / "conformance/run_link_played_link_toggle_after_persistence.sh"
MULTIPLAYER_GENERATOR = ROOT / "conformance/generate_link_played_multiplayer_suites.py"
MULTIPLAYER_INDEX = ROOT / "conformance/data/link-played-multiplayer.json"
MULTIPLAYER_IDENTITY_2 = ROOT / "conformance/runs/xdj-rx3-player-2.json"
MULTIPLAYER_RECORDER = ROOT / "conformance/record_link_played_multiplayer.sh"
MULTIPLAYER_REDUCER = ROOT / "tools/summarize_link_played_multiplayer.py"
MULTIPLAYER_HANDOFF = ROOT / "conformance/run_link_played_multiplayer_after_link_toggle.sh"
GOLDEN = ROOT / "conformance/goldens/rekordbox-7.2.19/xdj-rx3/link-played-state.json"
HARDWARE_OBSERVATION = ROOT.parent / "alphatheta-docs/platform/prodjlink/track-metadata.md"
MEMBER_SCANNER = ROOT / "tools/find_member_offset_references.py"
DISASSEMBLER = ROOT / "tools/disassemble_symbols.py"
XREF_SCANNER = ROOT / "tools/find_direct_xrefs.py"
SYMBOL_PATTERN = (
    "PSvDB(Main26NotifyLibraryUpdatedPlayed|Server26NotifyLibraryUpdatedPlayed)"
    "|Database(IF16getAllLinkPlayed|Mediator16getAllLinkPlayed)"
    "|rekordboxDBController(19getAllLinkPlayedIDs|18updatePlayedStatus|"
    "24clearAllLinkPlayedStatus|22setInitialPlayedStatus)"
    "|PlayedSettingFile(20get_prop_file_option|15getPlayedTracks|"
    "16savePlayedTracks)"
    "|SettingIF(22getCurrentPlayedOption|26getCurrentLinkPlayedOption)"
)
PRODUCER_PATTERN = (
    "DatabaseMediator(21addTrackToPlayHistory|22notifyDBUpdatedHistory|"
    "17deleteLinkHistory|15notifyDBUpdated|16notifyToDBServer|D2Ev)"
    "|DatabaseIF(15notifyDBUpdated|17deleteLinkHistory|"
    "21addTrackToPlayHistory|24clearAllLinkPlayedStatus)"
    "|UiProDJLink(18ReceiveUpdateEvent|23ReceiveDeleteHisotryCmd)"
    "|PlayHistoryManager13timerCallback"
    "|ViewBrowsePlayedColorComponent13buttonClicked"
)


class PlayedTrackStateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.disassembly = DISASSEMBLY.read_text()
        cls.producers = PRODUCERS.read_text()
        cls.navigation = json.loads(NAVIGATION.read_text())
        cls.suite = json.loads(SUITE.read_text())

    def test_binary_and_member_reference_set_are_pinned(self) -> None:
        self.assertEqual(
            "07dcecbaf304f777e435539c83c7dcc02e41de1eaf2e0a75e8a9852e4411a244",
            hashlib.sha256(BINARY.read_bytes()).hexdigest(),
        )
        rows = [
            line.split("\t")
            for line in XREFS.read_text().splitlines()
            if not line.startswith("#")
        ]
        self.assertEqual({"0x698", "0x6d8", "0x6e4"}, {row[0] for row in rows})
        self.assertEqual(19, len(rows))
        self.assertEqual(
            {"0x698": 6, "0x6d8": 7, "0x6e4": 6},
            {
                offset: sum(row[0] == offset for row in rows)
                for offset in {row[0] for row in rows}
            },
        )
        self.assertEqual(
            {
                "__ZN9PSvDBMain20GetListBufRowContentEhh17ENUM_CATEGORYKINDPvPmbjP18RetListBufParamExt",
                "__ZN9PSvDBMain10OnOtherCmdEP16_struct_dbsm_msg",
                "__ZN9PSvDBMainC2Ev",
                "__ZN9PSvDBMainD2Ev",
                "__ZN9PSvDBMain26NotifyLibraryUpdatedPlayedERN4juce5ArrayIjNS0_15CriticalSectionELi0EEE",
            },
            {row[2] for row in rows},
        )

    def test_link_played_state_pipeline_is_exact(self) -> None:
        fragments = (
            "'PlayedTrackOption'",
            "'LinkPlayedTrackOption'",
            "'AnotherHistories'",
            "test      byte ptr [r12 + 0x3f8], 0x10",
            "mov       esi, dword ptr [r12 + 8]",
            "or        dword ptr [rax + 0x3f8], 8",
            "or        dword ptr [rax + 0x3f8], 0x10",
            "__ZN2db10DatabaseIF16getAllLinkPlayed",
            "__ZN11PSvDBServer26NotifyLibraryUpdatedPlayed",
            "__ZN9PSvDBMain26NotifyLibraryUpdatedPlayed",
        )
        for fragment in fragments:
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, self.disassembly)

    def test_ui_refresh_has_exactly_two_direct_callers(self) -> None:
        result = subprocess.run(
            [sys.executable, str(XREF_SCANNER), str(BINARY), "0x101c5b240"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            {
                (
                    "0x102270326",
                    "__ZN6djplay11UiProDJLink17handleSwitchEventENS_10eMessageIDENS_9eSwitchIDENS_10eOperateIDEi",
                ),
                ("0x102275407", "__ZN6djplay11UiProDJLink3runEv"),
            },
            {
                (fields[1], fields[3])
                for line in result.stdout.splitlines()
                for fields in [line.split("\t")]
            },
        )

    def test_played_state_producers_and_clearers_are_exact(self) -> None:
        fragments = (
            "__ZN2db16DatabaseMediator21addTrackToPlayHistoryEj",
            "mov       edx, 1\n0x0100d4ac0b  xor       ecx, ecx\n"
            "0x0100d4ac0d  call      0x1019de6b0",
            "mov       edx, 1\n0x010209cff1  mov       ecx, 1\n"
            "0x010209cff6  call      0x1019de6b0",
            "xor       edx, edx\n0x010209d05b  mov       ecx, 1\n"
            "0x010209d060  call      0x1019de6b0",
            "mov       qword ptr [rbx + 0x40], 0x12",
            "__ZN2db21rekordboxDBController17clearPlayedStatus",
            "__ZN2db21rekordboxDBController24clearAllLinkPlayedStatusEv",
            "__ZN2db10DatabaseIF24clearAllLinkPlayedStatusEv",
        )
        for fragment in fragments:
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, self.producers)

        result = subprocess.run(
            [sys.executable, str(XREF_SCANNER), str(BINARY), "0x1019de6b0"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            {
                (
                    "0x100d4ac0d",
                    "__ZN2db16DatabaseMediator21addTrackToPlayHistoryEj",
                ),
                (
                    "0x10209cff6",
                    "__ZN2db16DatabaseMediator22notifyDBUpdatedHistoryEjj",
                ),
                (
                    "0x10209d060",
                    "__ZN2db16DatabaseMediator22notifyDBUpdatedHistoryEjj",
                ),
            },
            {
                (fields[1], fields[3])
                for line in result.stdout.splitlines()
                for fields in [line.split("\t")]
            },
        )

    def test_physical_cdj_3000_observation_is_pinned(self) -> None:
        self.assertEqual(
            "779a833d1074292e68cefe70a14c8df05df5235573eedf2231f3e4f040eab9d6",
            hashlib.sha256(HARDWARE_OBSERVATION.read_bytes()).hexdigest(),
        )
        text = " ".join(HARDWARE_OBSERVATION.read_text().split())
        self.assertIn("rekordbox 7.2.11 serving a CDJ-3000", text)
        self.assertIn("2026-09-12 capture, 854 track rows", text)
        self.assertIn("every row of the link-history list", text)

    def test_live_transition_suite_is_declared_without_inferred_expectations(self) -> None:
        self.assertEqual("link-played-state", self.suite["name"])
        self.assertEqual("full", self.suite["fixture_profile"])
        if GOLDEN.exists():
            golden = json.loads(GOLDEN.read_text())
            self.assertEqual("rekordbox", golden["provenance"]["backend"])
            self.assertEqual("7.2.19", golden["provenance"]["backend_version"])
            self.assertEqual(
                hashlib.sha256(SUITE.read_bytes()).hexdigest(),
                golden["provenance"]["suite_sha256"],
            )

        cases = {case["id"]: case for case in self.suite["cases"]}
        self.assertEqual(19, len(cases))
        self.assertEqual(
            {"0x3001", "0x3401", "0x3101"},
            {
                cases[case_id]["request_kind"]
                for case_id in ("insert-first", "insert-second", "remove-first", "delete-history")
            },
        )
        scalar_cases = [
            case for case in cases.values() if case["request_kind"] == "0x3b03"
        ]
        self.assertEqual(8, len(scalar_cases))
        self.assertTrue(all(case["direct_response"] for case in scalar_cases))
        self.assertTrue(all(not case["render"] for case in scalar_cases))
        row_cases = [
            case for case in cases.values() if case["request_kind"] == "0x1004"
        ]
        self.assertEqual(5, len(row_cases))
        self.assertTrue(
            all(case["expect"]["argument_count"] == 16 for case in row_cases)
        )

    def test_played_option_settings_are_deterministic(self) -> None:
        manifest = json.loads((SETTINGS / "manifest.json").read_text())
        source = ROOT / manifest["source"]
        self.assertEqual(
            manifest["source_sha256"], hashlib.sha256(source.read_bytes()).hexdigest()
        )
        self.assertEqual(
            source.read_bytes(), (SETTINGS / manifest["baseline_file"]).read_bytes()
        )
        self.assertEqual(
            {"reset", "link-persist", "ordinary-persist", "persist"},
            {item["state"] for item in manifest["variants"]},
        )

        for item in manifest["variants"]:
            data = (SETTINGS / item["file"]).read_bytes()
            self.assertEqual(item["sha256"], hashlib.sha256(data).hexdigest())
            for name in ("PlayedTrackOption", "LinkPlayedTrackOption"):
                self.assertEqual(1, data.count(f'<VALUE name="{name}"'.encode()))
                expected = item["values"][name]
                self.assertIn(f'<VALUE name="{name}" val="{expected}"/>'.encode(), data)

        with tempfile.TemporaryDirectory() as directory:
            generated = Path(directory) / "settings"
            subprocess.run(
                [sys.executable, str(SETTINGS_GENERATOR), "--output", str(generated)],
                cwd=ROOT,
                check=True,
                capture_output=True,
            )
            for path in SETTINGS.iterdir():
                self.assertEqual(path.read_bytes(), (generated / path.name).read_bytes())

    def test_live_recorder_owns_guest_state_and_has_no_backend_replay(self) -> None:
        recorder = RECORDER.read_text()
        subprocess.run(["bash", "-n", str(RECORDER)], cwd=ROOT, check=True)
        self.assertTrue(RECORDER.stat().st_mode & 0o111)
        fragments = (
            "rekordbox6/rekordbox3.settings",
            "rekordbox6/AnotherHistories.xml",
            "snapshot_guest_file",
            "restore_guest_file",
            "PlayedTrackOption",
            "LinkPlayedTrackOption",
            "all(.[]; .val == 1)",
            '"$script_dir/activate_fixture.sh" "$baseline"',
            "guest_state_restored:true",
            "case_count:19,process_count:2,exact_repeat:true",
        )
        for fragment in fragments:
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, recorder)
        self.assertNotIn("rbxport", recorder.lower())

    def test_reducer_preserves_both_observation_channels(self) -> None:
        subprocess.run(
            [sys.executable, "-m", "py_compile", str(REDUCER)],
            cwd=ROOT,
            check=True,
        )
        reducer = REDUCER.read_text()
        for fragment in (
            'message["kind"] == 0x4000',
            'message["arguments"][1]["value"]',
            'row["kind"] == 0x4101',
            'row["arguments"][7]["value"]',
            'bool(flags & 0x100)',
            '"record_repeat_verified": True',
            '"guest_state_restored": True',
        ):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, reducer)

    def test_persistence_restart_matrix_is_fully_declared(self) -> None:
        prime = json.loads(PERSISTENCE_PRIME_SUITE.read_text())
        restart = json.loads(PERSISTENCE_RESTART_SUITE.read_text())
        self.assertEqual("link-played-persistence-prime", prime["name"])
        self.assertEqual("link-played-persistence-restart", restart["name"])
        self.assertEqual(7, len(prime["cases"]))
        self.assertEqual(3, len(restart["cases"]))
        self.assertEqual(
            {"0x1004", "0x3001", "0x3b03"},
            {case["request_kind"] for case in prime["cases"]},
        )
        self.assertEqual(
            {"0x1004", "0x3b03"},
            {case["request_kind"] for case in restart["cases"]},
        )
        for case in prime["cases"] + restart["cases"]:
            if case["request_kind"] == "0x1004":
                self.assertEqual(16, case["expect"]["argument_count"])

    def test_persistence_recorder_owns_process_and_guest_state(self) -> None:
        recorder = PERSISTENCE_RECORDER.read_text()
        subprocess.run(["bash", "-n", str(PERSISTENCE_RECORDER)], cwd=ROOT, check=True)
        self.assertTrue(PERSISTENCE_RECORDER.stat().st_mode & 0o111)
        for fragment in (
            "reset link-persist ordinary-persist persist",
            "CloseMainWindow()",
            "forced_rekordbox_termination=\\$false",
            "same_database_restart:true,clean_shutdowns:2",
            "variant_count:4,run_count:8,suite_execution_count:16",
            "clean_shutdown_count:16,exact_repeat:true",
            "guest_state_restored:true",
        ):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, recorder)
        self.assertNotIn("rbxport", recorder.lower())

    def test_persistence_reducer_preserves_files_scalars_and_row_bits(self) -> None:
        subprocess.run(
            [sys.executable, "-m", "py_compile", str(PERSISTENCE_REDUCER)],
            cwd=ROOT,
            check=True,
        )
        reducer = PERSISTENCE_REDUCER.read_text()
        for fragment in (
            "ET.parse(file_path).getroot()",
            '"scalar_0x3b03"',
            '"row_0x4101_argument_7"',
            'prime_health["process_id"] != restart_health["process_id"]',
            'capture["variant_count"] == 4',
            'capture["clean_shutdown_count"] == 16',
        ):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, reducer)

    def test_persistence_handoff_is_guarded_and_cleans_up(self) -> None:
        handoff = PERSISTENCE_HANDOFF.read_text()
        subprocess.run(["bash", "-n", str(PERSISTENCE_HANDOFF)], cwd=ROOT, check=True)
        self.assertTrue(PERSISTENCE_HANDOFF.stat().st_mode & 0o111)
        for fragment in (
            "codex-rekordbox-link-played-state-20261003ah18.service",
            'wait_for_predecessor',
            'require_successful_predecessor',
            '"$vm/vmctl" isolation-check',
            '"$recorder"',
            '"$lab/.venv/bin/python" "$reducer"',
            'require_clean_baseline',
            '"$vm/vmctl" isolated-stop',
            "variant_count:4,run_count:8,suite_execution_count:16",
            "isolated_vm_stopped:true",
        ):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, handoff)

    def test_same_process_link_toggle_is_declared_without_inferred_state(self) -> None:
        suite = json.loads(LINK_TOGGLE_SUITE.read_text())
        self.assertEqual("link-played-link-toggle-post", suite["name"])
        self.assertEqual("same-process-link-toggle", suite["repeat_strategy"])
        self.assertEqual(3, len(suite["cases"]))
        self.assertEqual(
            {"0x1004", "0x3b03"},
            {case["request_kind"] for case in suite["cases"]},
        )
        for case in suite["cases"]:
            self.assertNotIn("row_argument_values", case.get("expect", {}))

    def test_link_toggle_recorder_keeps_one_process_and_has_control_arm(self) -> None:
        recorder = LINK_TOGGLE_RECORDER.read_text()
        subprocess.run(["bash", "-n", str(LINK_TOGGLE_RECORDER)], cwd=ROOT, check=True)
        self.assertTrue(LINK_TOGGLE_RECORDER.stat().st_mode & 0o111)
        for fragment in (
            "for mode in control toggle",
            "wait_for_dbserver absent",
            "wait_for_dbserver present",
            "inactive-health.json",
            "reactivated-health.json",
            "control-boundary-health.json",
            "same_process:true",
            "same_process_per_run:true",
            "guest_state_restored:true",
        ):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, recorder)
        self.assertNotIn("rbxport", recorder.lower())

    def test_link_toggle_reducer_preserves_both_state_channels(self) -> None:
        subprocess.run(
            [sys.executable, "-m", "py_compile", str(LINK_TOGGLE_REDUCER)],
            cwd=ROOT,
            check=True,
        )
        reducer = LINK_TOGGLE_REDUCER.read_text()
        for fragment in (
            '"scalar_0x3b03"',
            '"row_0x4101_argument_7"',
            'len(process_ids) == 1',
            'listeners["inactive-health.json"] == 0',
            '"post_boundary_observations"',
            'capture["same_process_per_run"] is True',
        ):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, reducer)

    def test_link_toggle_handoff_is_serialized_and_bounded(self) -> None:
        handoff = LINK_TOGGLE_HANDOFF.read_text()
        subprocess.run(["bash", "-n", str(LINK_TOGGLE_HANDOFF)], cwd=ROOT, check=True)
        self.assertTrue(LINK_TOGGLE_HANDOFF.stat().st_mode & 0o111)
        for fragment in (
            "codex-rekordbox-link-played-persistence-20261003ai18.service",
            "played-option persistence/restart matrix",
            '"$vm/vmctl" isolation-check',
            '"$recorder"',
            '"$lab/.venv/bin/python" "$reducer"',
            "same_process_per_run:true",
            "isolated_vm_stopped:true",
        ):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, handoff)

    def test_multiplayer_sequence_is_generated_and_player_correct(self) -> None:
        declaration = json.loads(MULTIPLAYER_INDEX.read_text())
        self.assertEqual(4, declaration["suite_count"])
        self.assertEqual(28, declaration["case_count"])
        self.assertEqual([1, 2, 1, 2], [item["player"] for item in declaration["sequence"]])
        self.assertEqual(
            ["0x01010301", "0x02010301", "0x01010301", "0x02010301"],
            [item["context"] for item in declaration["sequence"]],
        )
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "suites"
            index = Path(directory) / "index.json"
            subprocess.run(
                [
                    sys.executable,
                    str(MULTIPLAYER_GENERATOR),
                    "--output",
                    str(output),
                    "--index",
                    str(index),
                ],
                cwd=ROOT,
                check=True,
            )
            generated_index = json.loads(index.read_text())
            generated_index["sequence"] = [
                item | {"suite": f"suites/{Path(item['suite']).name}"}
                for item in generated_index["sequence"]
            ]
            self.assertEqual(declaration, generated_index)
            for item in declaration["sequence"]:
                expected = ROOT / "conformance" / item["suite"]
                self.assertEqual(expected.read_bytes(), (output / expected.name).read_bytes())

    def test_player_two_identity_packet_is_reproducible(self) -> None:
        identity = json.loads(MULTIPLAYER_IDENTITY_2.read_text())
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "conformance/identity_adapter.py"),
                "--model",
                identity["model"],
                "--player",
                str(identity["player"]),
                "--device-type",
                identity["device_type"],
                "--generation",
                str(identity["generation"]),
                "--mac",
                identity["mac"],
                "--address",
                identity["address"],
                "--broadcast",
                identity["broadcast"],
                "--peers",
                str(identity["peers"]),
                "--presence",
                str(identity["presence"]),
                "--model-code",
                str(identity["model_code"]),
                "--packet-hex",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        packet = bytes.fromhex(result.stdout.strip())
        self.assertEqual(identity["packet_sha256"], hashlib.sha256(packet).hexdigest())
        self.assertEqual(2, packet[0x24])

    def test_multiplayer_recorder_proves_both_identities_remain_live(self) -> None:
        recorder = MULTIPLAYER_RECORDER.read_text()
        subprocess.run(["bash", "-n", str(MULTIPLAYER_RECORDER)], cwd=ROOT, check=True)
        self.assertTrue(MULTIPLAYER_RECORDER.stat().st_mode & 0o111)
        for fragment in (
            "xdj-rx3-player-1.json",
            "xdj-rx3-player-2.json",
            "simultaneous_identity_count:2",
            "capture_identities before",
            "capture_identities \"after-$phase\"",
            "same_rekordbox_process:true",
            "identity_count:2,phase_count:4,case_count:28,run_count:2",
            "guest_state_restored:true",
        ):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, recorder)
        self.assertNotIn("rbxport", recorder.lower())

    def test_multiplayer_reducer_preserves_the_complete_timeline(self) -> None:
        subprocess.run(
            [sys.executable, "-m", "py_compile", str(MULTIPLAYER_REDUCER)],
            cwd=ROOT,
            check=True,
        )
        reducer = MULTIPLAYER_REDUCER.read_text()
        for fragment in (
            'assert [entry["player"] for entry in entries] == [1, 2, 1, 2]',
            '"scalar_0x3b03"',
            '"row_0x4101_argument_7"',
            'len(health_paths) == 5',
            'len(checkpoint_paths) == 5',
            'all(len(values) == 1 for values in identity_pids.values())',
            '"timeline": timeline',
        ):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, reducer)

    def test_multiplayer_handoff_is_serialized_and_restores_baseline(self) -> None:
        handoff = MULTIPLAYER_HANDOFF.read_text()
        subprocess.run(["bash", "-n", str(MULTIPLAYER_HANDOFF)], cwd=ROOT, check=True)
        self.assertTrue(MULTIPLAYER_HANDOFF.stat().st_mode & 0o111)
        for fragment in (
            "codex-rekordbox-link-played-link-toggle-20261003aj18.service",
            "Link-played LINK-toggle lifecycle",
            '"$vm/vmctl" isolation-check',
            '"$recorder"',
            '"$lab/.venv/bin/python" "$reducer"',
            "identity_count:2,phase_count:4,case_count:28,run_count:2",
            "require_clean_baseline",
            "isolated_vm_stopped:true",
        ):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, handoff)

    def test_xdj_rr_get_play_state_is_location_one(self) -> None:
        wrapper = next(
            item
            for item in self.navigation["wrappers"]
            if item["request_kind"] == "3B03"
        )
        self.assertEqual("dbcl_GetTrackPlayState", wrapper["name"])
        self.assertEqual(1, wrapper["fixed_location"])
        sites = [
            item
            for item in self.navigation["call_sites"]
            if item["request_kind"] == "3B03"
        ]
        self.assertEqual(1, len(sites))
        self.assertEqual("SendBrowseMenu", sites[0]["caller"])
        self.assertEqual(1, sites[0]["literal_location"])

    def test_generated_evidence_is_byte_reproducible(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            xrefs = Path(directory) / XREFS.name
            disassembly = Path(directory) / DISASSEMBLY.name
            producers = Path(directory) / PRODUCERS.name
            subprocess.run(
                [
                    sys.executable,
                    str(MEMBER_SCANNER),
                    BINARY_RELATIVE,
                    "0x698",
                    "0x6d8",
                    "0x6e4",
                    "--symbol-pattern",
                    "PSvDBMain",
                    "--output",
                    str(xrefs),
                ],
                cwd=ROOT,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                [
                    sys.executable,
                    str(DISASSEMBLER),
                    str(BINARY),
                    SYMBOL_PATTERN,
                    "--max-bytes",
                    "0x10000",
                    "--output",
                    str(disassembly),
                ],
                cwd=ROOT,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                [
                    sys.executable,
                    str(DISASSEMBLER),
                    str(BINARY),
                    PRODUCER_PATTERN,
                    "--max-bytes",
                    "0x10000",
                    "--output",
                    str(producers),
                ],
                cwd=ROOT,
                check=True,
                capture_output=True,
            )
            self.assertEqual(XREFS.read_bytes(), xrefs.read_bytes())
            self.assertEqual(DISASSEMBLY.read_bytes(), disassembly.read_bytes())
            self.assertEqual(PRODUCERS.read_bytes(), producers.read_bytes())

    def test_documents_distinguish_static_ownership_from_live_gap(self) -> None:
        documents = {
            "ROW_LAYOUT.md": (
                "Link-played content-ID cache",
                "returns scalar value `2`",
            ),
            "CONFIGURATION.md": (
                "Played-track presentation state",
                "AnotherHistories",
            ),
            "PROTOCOL_REFERENCE.md": (
                "Bit 8 is the Link-played marker",
                "Expected transitions remain unset",
            ),
            "LINK_EXPORT_REQUEST_VOCABULARY.md": (
                "`0x3b03` has a fully recovered scalar contract",
                "argument-7 bit `0x100`",
            ),
            "XDJ_RR_CLIENT_NAVIGATION.md": (
                "The location-1 play-state path is concrete",
                "Played versus Unplayed row action",
            ),
            "REKORDBOX_RESEARCH_GAPS.md": (
                "Link-played row state",
                "`ah18` records mutation timing",
            ),
            "CLEANUP.md": (
                "Played-state follow-up boundary",
                "snapshots the exact guest `rekordbox3.settings`",
            ),
            "SOURCES.md": (
                "Played-track state",
                "independent physical CDJ-3000 observation",
                "two-requester ownership/admission oracle",
            ),
            "DEVICE_COMPATIBILITY.md": (
                "advertised only player 1",
                "shared-versus-partitioned Link-played state",
            ),
        }
        for name, fragments in documents.items():
            text = " ".join((ROOT / name).read_text().split())
            for fragment in fragments:
                with self.subTest(document=name, fragment=fragment):
                    self.assertIn(fragment, text)

    def test_active_played_state_generations_are_current_in_documentation(self) -> None:
        documents = (
            "CONFIGURATION.md",
            "CONFORMANCE_COVERAGE.md",
            "DEVICE_COMPATIBILITY.md",
            "EXPERIMENTS.md",
            "HOT_CUE_BANK_ORACLE.md",
            "PROTOCOL_REFERENCE.md",
            "REKORDBOX_RESEARCH_GAPS.md",
        )
        superseded = ("ag17", "ah17", "ai17", "aj17", "ak17")

        for name in documents:
            source = (ROOT / name).read_text()
            for generation in superseded:
                with self.subTest(document=name, generation=generation):
                    self.assertNotIn(f"`{generation}`", source)


if __name__ == "__main__":
    unittest.main()
