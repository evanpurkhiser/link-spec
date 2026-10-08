import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools/summarize_physical_rx3_session.py"
ARTIFACT = ROOT / "data/experiments/physical-rx3-session/session-envelope.json"
NAVIGATION_TOOL = ROOT / "tools/summarize_physical_rx3_navigation.py"
NAVIGATION_ARTIFACT = (
    ROOT / "data/experiments/physical-rx3-session/navigation-transcript.json"
)
GENERATOR = ROOT / "conformance/generate_physical_rx3_envelope_suite.py"
SUITE = ROOT / "conformance/suites/generated/physical-rx3-session-envelope.json"
RECORDER = ROOT / "conformance/record_physical_rx3_session_envelope.sh"
REDUCER = ROOT / "tools/summarize_physical_rx3_session_envelope.py"
FINALIZER = ROOT / "conformance/run_physical_rx3_session_envelope_after_cloud_sync.sh"


class PhysicalRX3SessionEnvelopeTests(unittest.TestCase):
    def test_physical_artifact_regenerates_byte_identically(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "session.json"
            subprocess.run(
                [str(ROOT / ".venv/bin/python"), str(TOOL), "--output", str(output)],
                check=True,
                capture_output=True,
            )
            self.assertEqual(ARTIFACT.read_bytes(), output.read_bytes())

    def test_complete_navigation_transcript_regenerates_byte_identically(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "navigation.json"
            subprocess.run(
                [
                    str(ROOT / ".venv/bin/python"),
                    str(NAVIGATION_TOOL),
                    "--output",
                    str(output),
                ],
                check=True,
                capture_output=True,
            )
            self.assertEqual(NAVIGATION_ARTIFACT.read_bytes(), output.read_bytes())

    def test_complete_navigation_transcript_has_exact_native_vocabulary(self):
        artifact = json.loads(NAVIGATION_ARTIFACT.read_text())
        self.assertEqual(
            {
                "request_messages": 106,
                "request_transactions": 101,
                "response_messages": 268,
                "response_transactions": 93,
                "menu_rows": 144,
            },
            artifact["counts"],
        )
        self.assertEqual(
            {
                "0x0000": 1,
                "0x0001": 5,
                "0x1000": 1,
                "0x1004": 4,
                "0x2002": 22,
                "0x2003": 17,
                "0x2004": 1,
                "0x2102": 3,
                "0x2103": 1,
                "0x2204": 1,
                "0x2504": 1,
                "0x2b04": 1,
                "0x2c04": 16,
                "0x2d04": 1,
                "0x3000": 30,
                "0x3100": 1,
            },
            {item["kind"]: item["count"] for item in artifact["request_kinds"]},
        )
        self.assertEqual(
            {
                "0x0100": 1,
                "0x4000": 30,
                "0x4001": 30,
                "0x4002": 11,
                "0x4101": 144,
                "0x4201": 30,
                "0x4402": 1,
                "0x4502": 1,
                "0x4602": 1,
                "0x4e02": 1,
                "0x4f02": 18,
            },
            {item["kind"]: item["count"] for item in artifact["response_kinds"]},
        )
        self.assertEqual(
            [
                ("0x0b010401", 11, 1, 4, 1),
                ("0x0b030401", 11, 3, 4, 1),
                ("0x0b050401", 11, 5, 4, 1),
                ("0x0b080401", 11, 8, 4, 1),
            ],
            [
                (
                    item["hex"],
                    item["requester"],
                    item["menu_location"],
                    item["media_slot"],
                    item["track_type"],
                )
                for item in artifact["contexts"]
            ],
        )

    def test_complete_navigation_transcript_preserves_native_menu_shapes(self):
        artifact = json.loads(NAVIGATION_ARTIFACT.read_text())
        exchanges = artifact["exchanges"]
        root = next(
            exchange
            for exchange in exchanges
            if exchange["requests"][0]["kind"] == "0x1000"
        )
        self.assertEqual(
            [0x0B010401, 0, 0x05FDFFFF], root["requests"][0]["arguments"]
        )

        renders = [
            exchange
            for exchange in exchanges
            if exchange["requests"][0]["kind"] == "0x3000"
            and exchange["requests"][0]["arguments"]
            == [0x0B010401, 0, 12, 0, 4342, 12]
        ]
        self.assertEqual(3, len(renders))
        self.assertTrue(all(exchange["row_count"] == 12 for exchange in renders))
        self.assertEqual(
            "3A - 112.2 bpm", renders[0]["row_projections"][0]["argument_5"]
        )
        self.assertEqual(0x0F04, renders[0]["row_projections"][0]["argument_6"])

        blobs = [
            argument
            for exchange in exchanges
            for response in exchange["responses_except_rows"]
            for argument in response["arguments"]
            if isinstance(argument, dict) and "blob_bytes" in argument
        ]
        self.assertEqual(23, len(blobs))
        self.assertEqual(83_148, max(blob["blob_bytes"] for blob in blobs))
        self.assertTrue(
            all(
                set(blob) == {"blob_bytes", "sha256", "prefix_hex"}
                for blob in blobs
            )
        )
        self.assertLess(NAVIGATION_ARTIFACT.stat().st_size, 150_000)

        reports = artifact["cancellation_commands"]
        self.assertEqual(
            [199689, 207881, 208905, 209929, 210953],
            [report["transaction"] for report in reports],
        )
        self.assertEqual(
            [126329, 21333, 21098, 24043, 94015],
            [report["delay_after_artwork_request_us"] for report in reports],
        )
        self.assertEqual(
            [["0x4002"], ["0x4002"], [], ["0x4002"], []],
            [report["responses_before_report"] for report in reports],
        )
        self.assertTrue(
            all(not report["responses_after_report"] for report in reports)
        )

    def test_physical_setup_context_and_root_mask_are_exact(self):
        artifact = json.loads(ARTIFACT.read_text())
        self.assertEqual([11], artifact["setup"]["request"]["arguments"])
        self.assertEqual([0, 0x29], artifact["setup"]["response"]["arguments"])
        self.assertEqual("0x05fdffff", artifact["root"]["capability_mask"])
        self.assertEqual(19, artifact["root"]["total"])
        self.assertEqual(19, len(artifact["root"]["rows"]))
        self.assertEqual({11}, {item["requester"] for item in artifact["packed_contexts"]})
        self.assertEqual(
            {1, 3, 5, 8},
            {item["menu_location"] for item in artifact["packed_contexts"]},
        )
        self.assertEqual({4}, {item["media_slot"] for item in artifact["packed_contexts"]})
        self.assertEqual({1}, {item["track_type"] for item in artifact["packed_contexts"]})
        self.assertEqual(3, len(artifact["default_track_sort_render_pairs"]))
        for pair in artifact["default_track_sort_render_pairs"]:
            self.assertEqual(
                [0x0B010401, 0, 12, 0, 4342, 12],
                pair["render"]["arguments"],
            )

    def test_authority_suite_regenerates_byte_identically(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "suite.json"
            source = GENERATOR.read_text().replace(
                'OUTPUT = ROOT / "suites/generated/physical-rx3-session-envelope.json"',
                f"OUTPUT = Path({str(output)!r})",
            )
            candidate = Path(directory) / "generator.py"
            candidate.write_text(source)
            subprocess.run(
                [str(ROOT / ".venv/bin/python"), str(candidate)],
                check=True,
                capture_output=True,
            )
            self.assertEqual(SUITE.read_bytes(), output.read_bytes())

    def test_authority_suite_preserves_the_physical_envelope_without_predictions(self):
        suite = json.loads(SUITE.read_text())
        defaults = suite["defaults"]
        self.assertEqual(11, defaults["device"])
        self.assertEqual("0x0b010401", defaults["context"])
        self.assertEqual("0x05fdffff", defaults["root_capabilities"])
        self.assertEqual("legacy", defaults["setup"])
        self.assertEqual(2, len(suite["cases"]))
        self.assertTrue(
            all(case["expect"] == {"outcome": "any"} for case in suite["cases"])
        )
        self.assertEqual(
            [0, "$total", 12], suite["cases"][1]["render_arguments"]
        )

    def test_live_recording_chain_is_real_only_guarded_and_cleanup_aware(self):
        recorder = RECORDER.read_text()
        reducer = REDUCER.read_text()
        finalizer = FINALIZER.read_text()

        for source in (recorder, reducer, finalizer):
            self.assertNotIn("rbxport", source.lower())
        self.assertIn("xdj-rx3-player-11-status.json", recorder)
        self.assertIn(
            "codex-rekordbox-play-cloud-sync-zero-20261004au18.service",
            finalizer,
        )
        self.assertIn("predecessor_observed_active == true", finalizer)
        self.assertIn("record_physical_rx3_session_envelope.sh", finalizer)
        self.assertIn("summarize_physical_rx3_session_envelope.py", finalizer)
        self.assertIn('"$vm/vmctl" isolation-check', finalizer)
        self.assertIn('"$vm/vmctl" isolated-stop', finalizer)
        self.assertLess(
            finalizer.index("require_successful_predecessor"),
            finalizer.index('"$vm/vmctl" isolated-start'),
        )
        self.assertLess(
            finalizer.rindex("\nrequire_clean_baseline\n"),
            finalizer.rindex('\n"$vm/vmctl" isolated-stop\n'),
        )

    def test_protocol_docs_distinguish_physical_and_lab_envelopes(self):
        for name in (
            "docs/PROTOCOL_REFERENCE.md",
            "docs/CONFIGURATION.md",
            "docs/DEVICE_COMPATIBILITY.md",
            "docs/EXPERIMENTS.md",
        ):
            with self.subTest(name=name):
                self.assertIn("0x05fdffff", (ROOT / name).read_text())
        self.assertNotIn(
            "leaves physical-RX3 query-device behavior as an explicit matrix gap",
            (ROOT / "docs/EXPERIMENTS.md").read_text(),
        )
        physical = (ROOT / "docs/PHYSICAL_RX3_SESSION.md").read_text()
        self.assertIn("0x0b010401", physical)
        self.assertIn("| `0x0b010401` | 11 | 1 | 4 | 1 |", physical)
        self.assertIn("packet capture does not identify the serving", physical)
        self.assertNotIn("location 4, media slot 1", physical)

        adjacent = (ROOT / "docs/ADJACENT_PAYLOAD_SERVICES.md").read_text()
        self.assertIn("## Physical XDJ-RX3 request cadence", adjacent)
        self.assertIn("2c04 [0x0b010401, content_id, PWV4, EXT]", adjacent)
        self.assertIn("2003 [0x0b080401, content_id, 1]", adjacent)
        self.assertIn("83,148 bytes", adjacent)
        self.assertIn("21,098 to 126,329 microseconds", adjacent)

        vocabulary = (ROOT / "docs/LINK_EXPORT_REQUEST_VOCABULARY.md").read_text()
        self.assertIn("location 8 for artwork", vocabulary)
        self.assertIn("location 1 for specified atoms", vocabulary)
        self.assertIn("not its Rekordbox server version", vocabulary)
        self.assertIn("Client cancellation command (`0001`)", vocabulary)

        protocol = (ROOT / "docs/PROTOCOL_REFERENCE.md").read_text()
        self.assertIn("### Client cancellation `0001`", protocol)
        self.assertIn("21,098 to 126,329 microseconds", protocol)


if __name__ == "__main__":
    unittest.main()
