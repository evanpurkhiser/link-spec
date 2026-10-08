import json
import unittest
from itertools import product
from pathlib import Path

from conformance.generate_matrices import song_info_delayed_reply_routing_suites


ROOT = Path(__file__).resolve().parent
LAB = ROOT.parent
MATRIX = ROOT / "data/song-info-delayed-reply-routing-matrix.json"
EVIDENCE = LAB / "data/experiments/song-info-status-location2/delayed-reply-routing"


class SongInfoDelayedReplyRoutingTests(unittest.TestCase):
    def test_matrix_and_generated_declarations_cover_the_full_cross(self) -> None:
        matrix = json.loads(MATRIX.read_text())
        dimensions = matrix["dimensions"]
        expected = {
            f"{precursor}--{delay:04}ms.json"
            for precursor, delay in product(
                dimensions["second_precursor"],
                dimensions["delay_before_replacement_connection_ms"],
            )
        }
        documents = dict(song_info_delayed_reply_routing_suites())
        self.assertEqual(expected, documents.keys())
        self.assertEqual(6, len(documents))
        self.assertEqual(4, matrix["observations_per_variant"])
        self.assertEqual("unconstrained", matrix["authority"]["expected_outcomes"])
        self.assertFalse(matrix["static_prediction"]["prediction_is_expectation"])

    def test_each_suite_observes_before_sending_and_then_proves_health(self) -> None:
        for filename, suite in song_info_delayed_reply_routing_suites():
            with self.subTest(filename=filename):
                self.assertEqual(11, suite["defaults"]["device"])
                self.assertEqual("0x0b010301", suite["defaults"]["context"])
                self.assertEqual(10_000, suite["defaults"]["read_timeout_ms"])
                self.assertEqual(5, len(suite["cases"]))
                self.assertTrue(
                    all(case["expect"]["outcome"] == "any" for case in suite["cases"])
                )

                observation = suite["cases"][2]
                self.assertEqual("replacement-no-send", observation["id"])
                self.assertEqual("", observation["raw_hex"])
                self.assertEqual(1200, observation["raw_read_ms"])
                self.assertTrue(observation["fresh_connection"])
                self.assertTrue(observation["capture_connection_setup"])

                probe = suite["cases"][3]
                self.assertFalse(probe["fresh_connection"])
                self.assertEqual("0x0b020301", probe["arguments"][0]["number"])

                health = suite["cases"][4]
                self.assertTrue(health["fresh_connection"])
                self.assertEqual("0x0b020301", health["arguments"][0]["number"])

    def test_runner_delays_before_connecting_and_supports_no_send_reads(self) -> None:
        source = (ROOT / "protocol_runner.py").read_text()
        serial = source.split("    client = initial\n", 1)[1]
        connection_delay = serial.index(
            'time.sleep(case.get("delay_before_connection_ms", 0) / 1000)'
        )
        fresh_connect = serial.index('if case.get("fresh_connection", False):')
        request_delay = serial.index(
            'time.sleep(case.get("delay_before_request_ms", 0) / 1000)'
        )
        self.assertLess(connection_delay, fresh_connect)
        self.assertLess(fresh_connect, request_delay)
        self.assertIn('client.raw_probe(bytes.fromhex(case["raw_hex"])', source)
        self.assertIn('result["connection_setup_exchange"] = connection_setup', source)

    def test_recorder_and_reducer_remain_authority_only(self) -> None:
        recorder = (ROOT / "record_song_info_delayed_reply_routing.sh").read_text()
        reducer = (LAB / "tools/summarize_song_info_delayed_reply_routing.py").read_text()
        self.assertIn("[[ ${#suites[@]} == 6 ]]", recorder)
        self.assertIn("for observation in 1 2 3 4", recorder)
        self.assertNotIn("rbxport", recorder.lower())
        self.assertIn('"authority": "real Rekordbox 7.2.19 only"', reducer)
        self.assertIn('assert len(rows) == 24', reducer)
        self.assertNotIn('observation_total ==', reducer)
        self.assertNotIn('health_total ==', reducer)

    def test_runner_gates_on_timing_and_pinned_measurement_binaries(self) -> None:
        runner = (ROOT / "run_song_info_delayed_reply_routing.sh").read_text()
        gates = runner.index("\nrequire_timing_authority\nrequire_pinned_runners\n")
        generation = runner.index('"$lab/.venv/bin/python" "$script_dir/generate_matrices.py"')
        recording = runner.index('"$script_dir/record_song_info_delayed_reply_routing.sh"')

        self.assertLess(gates, generation)
        self.assertLess(generation, recording)
        self.assertIn('.runner.sha256 "$pinned_manifest"', runner)
        self.assertIn('.test_runner.sha256 "$pinned_manifest"', runner)
        self.assertIn("pinned_manifest_sha256:$pinned_manifest_sha256", runner)

    def test_completed_authority_result_is_pinned(self) -> None:
        summary = json.loads((EVIDENCE / "summary.json").read_text())
        self.assertEqual(24, summary["observation_count"])
        self.assertEqual({"raw_reply": 4, "timeout": 20}, summary["no_send_outcomes"])
        self.assertEqual({"13": 24}, summary["observation_probe_totals"])
        self.assertEqual({"13": 24}, summary["health_probe_totals"])

        immediate = sorted(
            (EVIDENCE / "delivery-blob-content--0000ms").glob("observation-[1-4].json")
        )
        raw_replies = [
            json.loads(path.read_text())["behavior"]["cases"][2]["raw_response"]
            for path in immediate
        ]
        self.assertEqual(4, len(raw_replies))
        self.assertTrue(all(result["outcome"] == "raw_reply" for result in raw_replies))
        self.assertEqual(
            {
                "11872349ae11000000011040000f021400000002060611000026021100000000"
            },
            {result["raw_hex"] for result in raw_replies},
        )

    def test_documents_distinguish_orphan_reply_from_probe_result(self) -> None:
        documents = {
            "SONG_INFO_SIBLINGS_ORACLE.md": (
                "late response from the malformed request",
                "not the response to the valid probe",
                "exact drop point remains an inference",
            ),
            "PROTOCOL_REFERENCE.md": (
                "A no-send drain exposes the orphan directly",
                "valid Delivery request returns 13",
            ),
            "CONFORMANCE_COVERAGE.md": (
                "24 observation receipts",
                "all 48 probes return 13",
            ),
            "STATIC_ANALYSIS.md": (
                "player byte and no originating socket",
                "can reach a replacement connection",
            ),
        }

        for name, fragments in documents.items():
            text = " ".join((LAB / name).read_text().split())
            for fragment in fragments:
                with self.subTest(document=name, fragment=fragment):
                    self.assertIn(fragment, text)


if __name__ == "__main__":
    unittest.main()
