import json
import unittest

import generate_hot_cue_declared_length_ffffffff_lifecycle_suites as lifecycle


class HotCueDeclaredLengthFFFFFFFFLifecycleTests(unittest.TestCase):
    def test_matrix_crosses_connection_topology_and_delay(self) -> None:
        variants = lifecycle.variants()
        self.assertEqual(20, len(variants))
        self.assertEqual(20, len({variant.id for variant in variants}))
        self.assertEqual(
            {"same-connection", "before-reconnect", "after-reconnect"},
            {variant.topology for variant in variants},
        )

        by_topology = {
            topology: [
                variant.delay_ms
                for variant in variants
                if variant.topology == topology
            ]
            for topology in {variant.topology for variant in variants}
        }
        self.assertEqual([0, 50, 100, 250, 500, 1000, 3000], by_topology["same-connection"])
        self.assertEqual([50, 100, 250, 500, 1000, 3000], by_topology["before-reconnect"])
        self.assertEqual([0, 50, 100, 250, 500, 1000, 3000], by_topology["after-reconnect"])

    def test_observation_timing_has_unambiguous_socket_semantics(self) -> None:
        for variant in lifecycle.variants():
            document = lifecycle.suite(variant)
            self.assertEqual(
                "duplicate-slot", document["lifecycle_probe"]["fixture_variant"]
            )
            self.assertEqual(3, document["lifecycle_probe"]["replicates"])
            self.assertEqual(
                [
                    "setter",
                    "late-response-observation",
                    "database-read-after-observation",
                    "database-read-final",
                ],
                [case["id"] for case in document["cases"]],
            )
            observation = document["cases"][1]
            if variant.topology == "same-connection":
                self.assertFalse(observation["fresh_connection"])
                self.assertEqual(variant.delay_ms, observation["delay_before_request_ms"])
            elif variant.topology == "before-reconnect":
                self.assertTrue(observation["fresh_connection"])
                self.assertEqual(variant.delay_ms, observation["delay_before_connection_ms"])
                self.assertNotIn("delay_before_request_ms", observation)
            else:
                self.assertTrue(observation["fresh_connection"])
                self.assertEqual(variant.delay_ms, observation["delay_before_request_ms"])
                self.assertNotIn("delay_before_connection_ms", observation)

    def test_checked_in_suites_match_generator(self) -> None:
        matrix = json.loads(
            (
                lifecycle.ROOT
                / "data/hot-cue-declared-length-ffffffff-lifecycle-matrix.json"
            ).read_text()
        )
        self.assertEqual(3, matrix["replicates"])
        for variant, declaration in zip(lifecycle.variants(), matrix["variants"], strict=True):
            path = lifecycle.ROOT / declaration["suite"]
            self.assertEqual(lifecycle.suite(variant), json.loads(path.read_text()))


if __name__ == "__main__":
    unittest.main()
