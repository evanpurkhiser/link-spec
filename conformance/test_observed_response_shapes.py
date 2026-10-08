import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
LEDGER = ROOT / "data/observed-response-shapes.json"


class ObservedResponseShapesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.document = json.loads(LEDGER.read_text())

    def test_generated_artifacts_are_current(self) -> None:
        subprocess.run(
            [
                str(ROOT / ".venv/bin/python"),
                str(ROOT / "tools/generate_observed_response_shapes.py"),
                "--check",
            ],
            check=True,
            cwd=ROOT,
        )

    def test_corpus_selection_excludes_noncanonical_attempts(self) -> None:
        selection = self.document["golden_corpus"]["selection"]
        self.assertIn("excluding .actual.json", selection)
        self.assertIn("attempts", selection)

    def test_every_request_has_cases_signatures_and_evidence(self) -> None:
        profile_ids = {
            profile["id"] for profile in self.document["identity_profiles"]
        }
        for request in self.document["requests"]:
            self.assertGreater(request["case_count"], 0, request["kind"])
            self.assertTrue(request["request_signatures"], request["kind"])
            self.assertTrue(request["evidence_files"], request["kind"])
            self.assertTrue(
                set(request["device_coverage"]["identity_profile_ids"]).issubset(
                    profile_ids
                ),
                request["kind"],
            )
            self.assertEqual(
                request["case_count"],
                sum(request["outcomes"].values()),
                request["kind"],
            )
            self.assertTrue(
                all(
                    not path.endswith(".actual.json")
                    and "/attempts/" not in path
                    and "/failed-attempts/" not in path
                    for path in request["evidence_files"]
                ),
                request["kind"],
            )

    def test_menu_and_render_protocol_signatures_are_present(self) -> None:
        requests = {request["kind"]: request for request in self.document["requests"]}
        self.assertIn("0x1004", requests)
        self.assertIn("0x2002", requests)
        self.assertIn("0x2C04", requests)

        track = requests["0x1004"]
        self.assertTrue(
            any(reply["kind"] == "0x4000" for reply in track["immediate_reply_signatures"])
        )
        self.assertTrue(
            any(reply["kind"] == "0x4101" for reply in track["render"]["reply_signatures"])
        )

        render = self.document["render_request"]
        self.assertEqual("0x3000", render["kind"])
        self.assertTrue(
            {"0x4001", "0x4101", "0x4201"}.issubset(
                {reply["kind"] for reply in render["reply_signatures"]}
            )
        )
        self.assertGreater(len(render["row_item_types"]), 0)

    def test_asynchronous_drains_are_not_attributed_as_replies(self) -> None:
        drains = self.document["asynchronous_pre_request_drains"]
        self.assertGreater(drains["observation_count"], 0)
        self.assertGreater(drains["nonempty_raw_count"], 0)
        self.assertIn(
            "0x4000", {reply["kind"] for reply in drains["message_signatures"]}
        )
        self.assertEqual(
            "asynchronous; not assigned to the following request",
            drains["attribution"],
        )
        self.assertTrue(
            all(not path.endswith(".actual.json") for path in drains["evidence_files"])
        )
        profile_ids = {
            profile["id"] for profile in self.document["identity_profiles"]
        }
        self.assertTrue(drains["device_coverage"]["identity_profile_ids"])
        self.assertTrue(
            set(drains["device_coverage"]["identity_profile_ids"]).issubset(
                profile_ids
            )
        )
        for request in self.document["requests"]:
            for reply in request["immediate_reply_signatures"]:
                self.assertNotEqual("pre_request_drain", reply.get("origin"))

    def test_summary_is_derived_from_records(self) -> None:
        summary = self.document["summary"]
        requests = self.document["requests"]
        self.assertEqual(len(requests), summary["case_request_kind_count"])
        self.assertEqual(
            len(requests) + 1, summary["observed_request_kind_count"]
        )
        self.assertEqual(
            sum(bool(request["immediate_reply_signatures"]) for request in requests),
            summary["request_kinds_with_immediate_replies"],
        )
        self.assertEqual(
            sum(request["render"]["page_count"] > 0 for request in requests),
            summary["request_kinds_with_rendered_pages"],
        )

    def test_classified_request_gaps_are_explicit(self) -> None:
        coverage = self.document["classified_request_coverage"]
        self.assertEqual(95, coverage["classified_request_kind_count"])
        self.assertEqual(
            ["0x100B", "0x110B", "0x130C", "0x3006", "0x3B03"],
            coverage["classified_without_canonical_response"],
        )
        self.assertEqual([], coverage["observed_outside_classification"])
        details = coverage["classified_without_canonical_response_details"]
        self.assertEqual(
            coverage["classified_without_canonical_response"],
            [detail["kind"] for detail in details],
        )
        for detail in details:
            self.assertGreater(detail["declared_case_count"], 0, detail["kind"])
            self.assertTrue(detail["suite_files"], detail["kind"])
            self.assertTrue(
                all(path.startswith("conformance/suites/") for path in detail["suite_files"]),
                detail["kind"],
            )

    def test_setup_exchange_is_indexed_separately(self) -> None:
        setup = self.document["setup_exchange"]
        self.assertGreater(setup["observation_count"], 0)
        self.assertEqual(["0x0000"], [item["kind"] for item in setup["request_kinds"]])
        self.assertTrue(
            any(reply["kind"] == "0x0000" for reply in setup["reply_signatures"])
        )

    def test_per_request_device_coverage_preserves_status_boundary(self) -> None:
        profiles = {
            profile["id"]: profile for profile in self.document["identity_profiles"]
        }
        requests = {request["kind"]: request for request in self.document["requests"]}

        track_profiles = {
            profiles[profile_id]["model"]
            for profile_id in requests["0x1004"]["device_coverage"]["identity_profile_ids"]
        }
        self.assertTrue({"XDJ-RX3", "CDJ-3000", "CDJ-2000nexus"}.issubset(track_profiles))

        display_profiles = [
            profiles[profile_id]
            for profile_id in requests["0x2002"]["device_coverage"]["identity_profile_ids"]
        ]
        self.assertTrue(any(profile["status_backed"] for profile in display_profiles))
        self.assertTrue(any(not profile["status_backed"] for profile in display_profiles))
        self.assertEqual(
            {"extended", "legacy"},
            set(requests["0x2002"]["device_coverage"]["setup_modes"]),
        )

    def test_markdown_exposes_identity_and_per_request_device_coverage(self) -> None:
        markdown = (ROOT / "docs/OBSERVED_RESPONSE_SHAPES.md").read_text()
        self.assertIn("## Identity profiles", markdown)
        self.assertIn("| Profile | Model | Player | Class |", markdown)
        self.assertIn("| Identities | Models | Status coverage | Setup |", markdown)

        profiles = {
            profile["id"]: profile for profile in self.document["identity_profiles"]
        }
        requests = {request["kind"]: request for request in self.document["requests"]}
        track = requests["0x1004"]
        track_profiles = [
            profiles[profile_id]
            for profile_id in track["device_coverage"]["identity_profile_ids"]
        ]
        expected = (
            f"| `0x1004` | {track['case_count']} |"
        )
        self.assertIn(expected, markdown)
        status_count = sum(profile["status_backed"] for profile in track_profiles)
        self.assertIn(
            f"| {len(track_profiles)} | "
            f"{len({profile['model'] for profile in track_profiles})} | "
            f"{status_count}/{len(track_profiles)} status-backed |",
            markdown,
        )


if __name__ == "__main__":
    unittest.main()
