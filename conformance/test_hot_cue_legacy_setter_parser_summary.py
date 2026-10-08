import json
import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import summarize_hot_cue_legacy_setter_parser as summary


def live_summary_path() -> Path | None:
    for path in (summary.OUTPUT, summary.PARTIAL_OUTPUT):
        if path.is_file():
            return path

    return None


class HotCueLegacySetterParserSummaryTests(unittest.TestCase):
    def test_canonical_control_variants_have_one_request_signature(self) -> None:
        variants = (
            "actual-cue-length-00000024",
            "declared-cue-length-00000024",
            "flag-00040100",
            "actual-extension-length-00000008",
            "declared-extension-length-00000008",
            "content-id-00002711",
            "fixed-word-2-00000000",
        )
        signatures = {
            summary.request_signature(
                {
                    "suite": (
                        "suites/generated/hot-cue-legacy-setter-parser/"
                        f"hot-cue-legacy-setter-parser-{variant}.json"
                    )
                }
            )
            for variant in variants
        }

        self.assertEqual(1, len(signatures))

    def test_equivalent_request_group_exposes_lifecycle_conflict(self) -> None:
        path = live_summary_path()
        if path is None:
            self.skipTest("live summary is not recorded")

        document = json.loads(path.read_text())
        group = next(
            group
            for group in document.get("equivalent_request_groups", [])
            if "declared-extension-length-00000008" in group["variants"]
        )

        self.assertFalse(group["lifecycle_consistent"])
        self.assertEqual(2, len(group["lifecycle_groups"]))
        self.assertEqual(
            {
                "actual-cue-length-00000024",
                "declared-cue-length-00000024",
                "flag-00040100",
                "actual-extension-length-00000008",
                "declared-extension-length-00000008",
                "content-id-00002711",
                "fixed-word-2-00000000",
            },
            set(group["variants"]),
        )

    def test_application_error_signature_ignores_process_specific_tail(self) -> None:
        common = (
            "Faulting application name: rekordbox.exe, version: 7.2.19.0\r\n"
            "Faulting module name: ntdll.dll, version: 10.0.26100.7920\r\n"
            "Exception code: 0xc0000374\r\n"
            "Fault offset: 0x00000000001176e5\r\n"
        )
        first = {
            "provider": "Application Error",
            "event_id": 1000,
            "level": "Error",
            "message": common + "Faulting process id: 0x17B0\r\nReport Id: first",
        }
        second = {
            **first,
            "message": common + "Faulting process id: 0x1F84\r\nReport Id: second",
        }

        self.assertEqual(
            summary.application_error_signature(first),
            summary.application_error_signature(second),
        )

    def test_restart_recovery_normalizes_only_volatile_transport_state(self) -> None:
        shared = {
            "response_kind": None,
            "response_argument_count": None,
            "status": None,
            "response_record_count": None,
            "database_effect": "changed",
            "changed_membership_ids": ["94201"],
            "getter_record_count": None,
            "getter_record_lengths": None,
            "getter_blob_bytes": None,
            "getter_blob_sha256": None,
            "restart_getter_outcome": "raw_reply",
            "restart_getter_effect": "changed",
            "restart_getter_record_count": 3,
            "restart_getter_record_lengths": [56, 124, 124],
            "restart_getter_blob_bytes": 304,
            "restart_getter_blob_sha256": "restart-blob",
            "restart_process_state": "alive",
            "restart_database_effect": "changed",
            "restart_changed_membership_ids": ["94201"],
            "application_error_signatures": ["same-crash"],
            "getter_unavailable_process_state": "exited",
            "getter_unavailable_application_event_count": 1,
            "getter_unavailable_application_error_signatures": ["same-crash"],
        }
        disconnected = {
            **shared,
            "outcome": "disconnect",
            "response_signature": "disconnect-response",
            "process_state": "exited",
            "getter_outcome": "skipped-process-exited",
            "getter_effect": "unavailable-process-exited",
        }
        stale_port = {
            **shared,
            "outcome": "timeout",
            "response_signature": "timeout-response",
            "process_state": "alive",
            "getter_outcome": "skipped-dbserver-connect-timeout",
            "getter_effect": "unavailable-dbserver-connect-timeout",
        }

        self.assertEqual(
            summary.repeat_signature(disconnected),
            summary.repeat_signature(stale_port),
        )
        self.assertNotEqual(
            summary.transport_signature(disconnected),
            summary.transport_signature(stale_port),
        )

    def test_baseline_getter_contains_three_extended_records(self) -> None:
        payload = bytes.fromhex(summary.baseline_getter_blob())
        self.assertEqual(372, len(payload))
        self.assertEqual([124, 124, 124], summary.record_lengths(payload))
        self.assertEqual([4, 5, 6], [payload[offset + 4] for offset in (0, 124, 248)])

    def test_mutated_getter_preserves_each_record_boundary(self) -> None:
        path = (
            summary.EVIDENCE
            / "actual-cue-length-00000024/run-1/getter.json"
        )
        if not path.is_file():
            self.skipTest("exact-length live evidence is not recorded")

        parsed = summary.parse_getter(path)
        self.assertEqual("changed", parsed["getter_effect"])
        self.assertEqual(3, parsed["getter_record_count"])
        self.assertEqual([56, 124, 124], parsed["getter_record_lengths"])
        self.assertEqual(304, parsed["getter_blob_bytes"])

    def test_declared_exact_length_mutates_in_both_runs(self) -> None:
        variant = {
            "id": "declared-cue-length-00000024",
            "suite": (
                "suites/generated/hot-cue-legacy-setter-parser/"
                "hot-cue-legacy-setter-parser-declared-cue-length-00000024.json"
            ),
        }
        baseline = json.loads(summary.BASELINE_DATABASE.read_text())
        evidence = summary.EVIDENCE / variant["id"]
        if not (evidence / "run-2/complete.json").is_file():
            self.skipTest("declared exact-length live evidence is not recorded")

        runs = [summary.parse_run(variant, run, baseline) for run in (1, 2)]
        for run in runs:
            assert run is not None
            self.assertEqual(0x4702, run["response_kind"])
            self.assertEqual("changed", run["database_effect"])
            self.assertEqual(["94201"], run["changed_membership_ids"])
            self.assertEqual([56, 124, 124], run["getter_record_lengths"])

    def test_declared_uint32_max_recovers_only_after_restart(self) -> None:
        variant = {
            "id": "declared-cue-length-ffffffff",
            "suite": (
                "suites/generated/hot-cue-legacy-setter-parser/"
                "hot-cue-legacy-setter-parser-declared-cue-length-ffffffff.json"
            ),
        }
        baseline = json.loads(summary.BASELINE_DATABASE.read_text())
        evidence = summary.EVIDENCE / variant["id"]
        if not (evidence / "run-2/complete.json").is_file():
            self.skipTest("declared UINT32_MAX live evidence is not recorded")

        runs = [summary.parse_run(variant, run, baseline) for run in (1, 2)]
        for run in runs:
            assert run is not None
            self.assertEqual(0x0100, run["response_kind"])
            self.assertEqual("pristine", run["database_effect"])
            self.assertEqual("timeout", run["getter_outcome"])
            self.assertEqual("raw_reply", run["restart_getter_outcome"])
            self.assertEqual("pristine", run["restart_getter_effect"])
            self.assertEqual([124, 124, 124], run["restart_getter_record_lengths"])
            self.assertEqual("pristine", run["restart_database_effect"])

    def test_content_id_uint32_max_persists_before_empty_lookup(self) -> None:
        variant = {
            "id": "content-id-ffffffff",
            "suite": (
                "suites/generated/hot-cue-legacy-setter-parser/"
                "hot-cue-legacy-setter-parser-content-id-ffffffff.json"
            ),
        }
        baseline = json.loads(summary.BASELINE_DATABASE.read_text())
        evidence = summary.EVIDENCE / variant["id"]
        if not (evidence / "run-2/complete.json").is_file():
            self.skipTest("ContentID UINT32_MAX live evidence is not recorded")

        runs = [summary.parse_run(variant, run, baseline) for run in (1, 2)]
        for run_number, run in enumerate(runs, start=1):
            assert run is not None
            self.assertEqual(0x4702, run["response_kind"])
            self.assertEqual(1, run["status"])
            self.assertEqual(0, run["response_record_count"])
            self.assertEqual("changed", run["database_effect"])
            self.assertEqual(["94201"], run["changed_membership_ids"])
            self.assertEqual("skipped-port-query-timeout", run["getter_outcome"])
            self.assertEqual("alive", run["getter_unavailable_process_state"])
            self.assertEqual("raw_reply", run["restart_getter_outcome"])
            self.assertEqual([56, 124, 124], run["restart_getter_record_lengths"])
            self.assertEqual("changed", run["restart_database_effect"])

            snapshot = json.loads(
                (evidence / f"run-{run_number}/database/snapshot.json").read_text()
            )
            self.assertEqual(
                str(0xFFFFFFFF),
                summary.membership_rows(snapshot)["94201"]["ContentID"],
            )

    def test_fixed_word_two_is_dynamically_ignored(self) -> None:
        baseline = json.loads(summary.BASELINE_DATABASE.read_text())
        variants = [
            {
                "id": f"fixed-word-2-{value}",
                "suite": (
                    "suites/generated/hot-cue-legacy-setter-parser/"
                    f"hot-cue-legacy-setter-parser-fixed-word-2-{value}.json"
                ),
            }
            for value in ("00000000", "ffffffff")
        ]
        if not all(
            (summary.EVIDENCE / variant["id"] / "run-2/complete.json").is_file()
            for variant in variants
        ):
            self.skipTest("fixed-word-2 live pairs are not recorded")

        parsed = [
            summary.parse_run(variant, run, baseline)
            for variant in variants
            for run in (1, 2)
        ]
        self.assertTrue(all(run is not None for run in parsed))
        runs = [run for run in parsed if run is not None]

        self.assertEqual(1, len({run["response_signature"] for run in runs}))
        self.assertEqual(1, len({run["restart_getter_blob_sha256"] for run in runs}))
        self.assertTrue(all(run["status"] == 0 for run in runs))
        self.assertTrue(all(run["response_record_count"] == 2 for run in runs))
        self.assertTrue(all(run["database_effect"] == "changed" for run in runs))
        self.assertTrue(
            all(run["getter_outcome"] == "skipped-port-query-timeout" for run in runs)
        )

        semantic_rows = []
        ignored = {"updated_at", "rb_local_usn"}
        for variant in variants:
            for run in (1, 2):
                snapshot = json.loads(
                    (
                        summary.EVIDENCE
                        / variant["id"]
                        / f"run-{run}/database/snapshot.json"
                    ).read_text()
                )
                row = summary.membership_rows(snapshot)["94201"]
                semantic_rows.append(
                    {key: value for key, value in row.items() if key not in ignored}
                )

        self.assertTrue(all(row == semantic_rows[0] for row in semantic_rows))

    def test_fixed_word_analysis_closes_word_two_and_tracks_pending_pairs(self) -> None:
        path = live_summary_path()
        if path is None:
            self.skipTest("live summary is not recorded")

        document = json.loads(path.read_text())
        by_word = {item["word"]: item for item in document["fixed_word_analysis"]}
        self.assertEqual(set(range(2, 9)), set(by_word))
        self.assertEqual("complete", by_word[2]["state"])
        self.assertIsNone(by_word[2]["expected_field"])
        self.assertEqual([], by_word[2]["changed_fields"])
        self.assertEqual({"zero", "maximum"}, set(by_word[2]["completed_values"]))
        self.assertNotEqual(
            by_word[2]["request_signatures"]["zero"],
            by_word[2]["request_signatures"]["maximum"],
        )

        expected_fields = {
            3: "InFrame",
            4: "OutFrame",
            5: "InMpegFrame",
            6: "OutMpegFrame",
            7: "InMpegAbs",
            8: "OutMpegAbs",
        }
        for word, field in expected_fields.items():
            self.assertEqual(field, by_word[word]["expected_field"])
            if by_word[word]["state"] == "complete":
                self.assertEqual([field], by_word[word]["changed_fields"])
                self.assertEqual(
                    {"zero": 0, "maximum": 0xFFFFFFFF},
                    by_word[word]["stored_values"],
                )

    def test_complete_fixed_word_map_is_promoted_in_oracle(self) -> None:
        oracle = (summary.ROOT / "docs/HOT_CUE_BANK_ORACLE.md").read_text()
        self.assertNotIn("static; live pair pending", oracle)
        for field in ("OutMpegFrame", "InMpegAbs", "OutMpegAbs"):
            self.assertIn(
                f"`{field}` | zero/maximum repeat-verified; sole observed delta",
                oracle,
            )

    def test_flag_lower_edge_is_inclusive(self) -> None:
        baseline = json.loads(summary.BASELINE_DATABASE.read_text())
        controls = {
            "flag-00000000": "pristine",
            "flag-0003ffff": "pristine",
            "flag-00040000": "changed",
        }

        for variant_id, expected_effect in controls.items():
            evidence = summary.EVIDENCE / variant_id
            if not (evidence / "run-2/complete.json").is_file():
                self.skipTest("flag lower-edge live evidence is not recorded")
            variant = {
                "id": variant_id,
                "suite": (
                    "suites/generated/hot-cue-legacy-setter-parser/"
                    f"hot-cue-legacy-setter-parser-{variant_id}.json"
                ),
            }

            runs = [summary.parse_run(variant, run, baseline) for run in (1, 2)]
            for run in runs:
                assert run is not None
                self.assertEqual(0x4702, run["response_kind"])
                self.assertEqual(expected_effect, run["database_effect"])
                self.assertEqual(
                    ["94201"] if expected_effect == "changed" else [],
                    run["changed_membership_ids"],
                )

    def test_flag_low_byte_controls_out_msec_only(self) -> None:
        expected_out_msec = {
            "flag-00040000": 0xFFFFFFFF,
            "flag-00040001": 0x88888888,
            "flag-00040100": 0xFFFFFFFF,
            "flag-0004ffff": 0xFFFFFFFF,
        }
        normalized_rows = []

        for variant_id, expected in expected_out_msec.items():
            evidence = summary.EVIDENCE / variant_id
            if not (evidence / "run-2/complete.json").is_file():
                self.skipTest("flag low-byte live evidence is not recorded")

            for run in (1, 2):
                snapshot = json.loads(
                    (evidence / f"run-{run}/database/snapshot.json").read_text()
                )
                row = summary.membership_rows(snapshot)["94201"]
                self.assertEqual(expected, row["OutMsec"])
                normalized_rows.append(
                    {key: value for key, value in row.items() if key != "OutMsec"}
                )

        self.assertTrue(all(row == normalized_rows[0] for row in normalized_rows))

    def test_flag_high_word_routes_membership_and_getter_position(self) -> None:
        expected_routes = {
            "flag-00050000": ("94203", [124, 56, 124]),
            "flag-0005ffff": ("94203", [124, 56, 124]),
            "flag-00060000": ("94205", [124, 124, 56]),
            "flag-0006ffff": ("94205", [124, 124, 56]),
        }

        for variant_id, (membership_id, record_lengths) in expected_routes.items():
            evidence = summary.EVIDENCE / variant_id
            if not (evidence / "run-2/complete.json").is_file():
                self.skipTest("flag high-word routing evidence is not recorded")

            variant = {
                "id": variant_id,
                "suite": (
                    "suites/generated/hot-cue-legacy-setter-parser/"
                    f"hot-cue-legacy-setter-parser-{variant_id}.json"
                ),
            }
            baseline = json.loads(summary.BASELINE_DATABASE.read_text())

            for run_number in (1, 2):
                run = summary.parse_run(variant, run_number, baseline)
                assert run is not None
                self.assertEqual([membership_id], run["changed_membership_ids"])
                self.assertEqual(record_lengths, run["getter_record_lengths"])

                snapshot = json.loads(
                    (evidence / f"run-{run_number}/database/snapshot.json").read_text()
                )
                row = summary.membership_rows(snapshot)[membership_id]
                self.assertEqual(0xFFFFFFFF, row["OutMsec"])

    def test_flag_upper_edge_is_inclusive(self) -> None:
        baseline = json.loads(summary.BASELINE_DATABASE.read_text())
        controls = {
            "flag-0006ffff": ("changed", ["94205"], [124, 124, 56]),
            "flag-00070000": ("pristine", [], [124, 124, 124]),
            "flag-ffffffff": ("pristine", [], [124, 124, 124]),
        }

        for variant_id, (effect, changed_ids, record_lengths) in controls.items():
            evidence = summary.EVIDENCE / variant_id
            if not (evidence / "run-2/complete.json").is_file():
                self.skipTest("flag upper-edge live evidence is not recorded")

            variant = {
                "id": variant_id,
                "suite": (
                    "suites/generated/hot-cue-legacy-setter-parser/"
                    f"hot-cue-legacy-setter-parser-{variant_id}.json"
                ),
            }
            for run_number in (1, 2):
                run = summary.parse_run(variant, run_number, baseline)
                assert run is not None
                self.assertEqual(0x4702, run["response_kind"])
                self.assertEqual(0, run["status"])
                self.assertEqual(2, run["response_record_count"])
                self.assertEqual(effect, run["database_effect"])
                self.assertEqual(changed_ids, run["changed_membership_ids"])
                self.assertEqual(record_lengths, run["getter_record_lengths"])
                self.assertEqual("alive", run["process_state"])
                self.assertEqual(0, run["application_event_count"])

    def test_short_extension_is_zero_padded_little_endian(self) -> None:
        expected_in_msec = {
            "actual-extension-length-00000000": 0,
            "actual-extension-length-00000001": 0x77,
            "actual-extension-length-00000007": 0x77777777,
            "actual-extension-length-00000008": 0x77777777,
            "actual-extension-length-00000009": 0x77777777,
            "actual-extension-length-00000010": 0x77777777,
        }
        baseline = json.loads(summary.BASELINE_DATABASE.read_text())

        for variant_id, expected in expected_in_msec.items():
            evidence = summary.EVIDENCE / variant_id
            if not (evidence / "run-2/complete.json").is_file():
                self.skipTest("short-extension live evidence is not recorded")

            variant = {
                "id": variant_id,
                "suite": (
                    "suites/generated/hot-cue-legacy-setter-parser/"
                    f"hot-cue-legacy-setter-parser-{variant_id}.json"
                ),
            }

            for run_number in (1, 2):
                run = summary.parse_run(variant, run_number, baseline)
                assert run is not None
                self.assertEqual(["94201"], run["changed_membership_ids"])
                self.assertEqual([56, 124, 124], run["getter_record_lengths"])

                snapshot = json.loads(
                    (evidence / f"run-{run_number}/database/snapshot.json").read_text()
                )
                row = summary.membership_rows(snapshot)["94201"]
                self.assertEqual(expected, row["InMsec"])
                self.assertEqual(0xFFFFFFFF, row["OutMsec"])

    def test_extension_bytes_after_eight_are_ignored(self) -> None:
        variant_ids = (
            "actual-extension-length-00000008",
            "actual-extension-length-00000009",
            "actual-extension-length-00000010",
        )
        baseline = json.loads(summary.BASELINE_DATABASE.read_text())
        getter_hashes = set()
        response_signatures = set()

        for variant_id in variant_ids:
            evidence = summary.EVIDENCE / variant_id
            if not (evidence / "run-2/complete.json").is_file():
                self.skipTest("long-extension live evidence is not recorded")

            variant = {
                "id": variant_id,
                "suite": (
                    "suites/generated/hot-cue-legacy-setter-parser/"
                    f"hot-cue-legacy-setter-parser-{variant_id}.json"
                ),
            }
            for run_number in (1, 2):
                run = summary.parse_run(variant, run_number, baseline)
                assert run is not None
                getter_hashes.add(run["getter_blob_sha256"])
                response_signatures.add(run["response_signature"])

        self.assertEqual(1, len(getter_hashes))
        self.assertEqual(1, len(response_signatures))

    def test_declared_zero_extension_mutates_before_empty_reply(self) -> None:
        variant_id = "declared-extension-length-00000000"
        evidence = summary.EVIDENCE / variant_id
        if not (evidence / "run-2/complete.json").is_file():
            self.skipTest("declared-zero extension evidence is not recorded")

        variant = {
            "id": variant_id,
            "suite": (
                "suites/generated/hot-cue-legacy-setter-parser/"
                f"hot-cue-legacy-setter-parser-{variant_id}.json"
            ),
        }
        baseline = json.loads(summary.BASELINE_DATABASE.read_text())

        for run_number in (1, 2):
            run = summary.parse_run(variant, run_number, baseline)
            assert run is not None
            self.assertEqual(0x0100, run["response_kind"])
            self.assertEqual(0, run["response_argument_count"])
            self.assertEqual(["94201"], run["changed_membership_ids"])
            self.assertEqual([56, 124, 124], run["getter_record_lengths"])

            snapshot = json.loads(
                (evidence / f"run-{run_number}/database/snapshot.json").read_text()
            )
            row = summary.membership_rows(snapshot)["94201"]
            self.assertEqual(0, row["InMsec"])
            self.assertEqual(0xFFFFFFFF, row["OutMsec"])

    def test_declared_extension_crash_boundaries_share_stable_signature(self) -> None:
        baseline = json.loads(summary.BASELINE_DATABASE.read_text())
        expected_signature = None
        controls = {
            "declared-extension-length-00000001": (
                "disconnect",
                "skipped-process-exited",
                [1, 1],
            ),
            "declared-extension-length-00000007": (
                "timeout",
                "skipped-dbserver-connect-timeout",
                [0, 0],
            ),
        }

        for variant_id, (outcome, getter_outcome, initial_event_counts) in controls.items():
            evidence = summary.EVIDENCE / variant_id
            if not (evidence / "run-2/complete.json").is_file():
                self.skipTest(f"{variant_id} live evidence is not recorded")

            variant = {
                "id": variant_id,
                "suite": (
                    "suites/generated/hot-cue-legacy-setter-parser/"
                    f"hot-cue-legacy-setter-parser-{variant_id}.json"
                ),
            }
            runs = [summary.parse_run(variant, run, baseline) for run in (1, 2)]

            for run_number, run in enumerate(runs):
                assert run is not None
                self.assertEqual(outcome, run["outcome"])
                self.assertEqual(getter_outcome, run["getter_outcome"])
                self.assertEqual("pristine", run["database_effect"])
                self.assertEqual(initial_event_counts[run_number], run["application_event_count"])
                self.assertEqual("exited", run["getter_unavailable_process_state"])
                self.assertEqual(1, run["getter_unavailable_application_event_count"])
                self.assertEqual("raw_reply", run["restart_getter_outcome"])
                self.assertEqual("pristine", run["restart_getter_effect"])
                self.assertEqual([124, 124, 124], run["restart_getter_record_lengths"])
                self.assertEqual("pristine", run["restart_database_effect"])

                signatures = run["getter_unavailable_application_error_signatures"]
                self.assertEqual(1, len(signatures))
                if expected_signature is None:
                    expected_signature = signatures[0]
                self.assertEqual(expected_signature, signatures[0])

    def test_declared_extension_exact_and_overdeclared_lengths_are_identical(self) -> None:
        baseline = json.loads(summary.BASELINE_DATABASE.read_text())
        semantic_rows = set()
        response_signatures = set()
        restart_blob_hashes = set()

        for suffix in ("00000008", "00000009"):
            variant_id = f"declared-extension-length-{suffix}"
            evidence = summary.EVIDENCE / variant_id
            if not (evidence / "run-2/complete.json").is_file():
                self.skipTest(f"{variant_id} live evidence is not recorded")

            variant = {
                "id": variant_id,
                "suite": (
                    "suites/generated/hot-cue-legacy-setter-parser/"
                    f"hot-cue-legacy-setter-parser-{variant_id}.json"
                ),
            }
            for run_number in (1, 2):
                run = summary.parse_run(variant, run_number, baseline)
                assert run is not None
                self.assertEqual("raw_reply", run["outcome"])
                self.assertEqual(0x4702, run["response_kind"])
                self.assertEqual(0, run["status"])
                self.assertEqual(2, run["response_record_count"])
                self.assertEqual("changed", run["database_effect"])
                self.assertEqual(["94201"], run["changed_membership_ids"])
                self.assertEqual("skipped-port-query-timeout", run["getter_outcome"])
                self.assertEqual("alive", run["getter_unavailable_process_state"])
                self.assertEqual(0, run["getter_unavailable_application_event_count"])
                self.assertEqual("changed", run["restart_getter_effect"])
                self.assertEqual([56, 124, 124], run["restart_getter_record_lengths"])
                self.assertEqual("changed", run["restart_database_effect"])

                snapshot = json.loads(
                    (evidence / f"run-{run_number}/database/snapshot.json").read_text()
                )
                semantic_rows.add(summary.digest(summary.membership_rows(snapshot)["94201"]))
                response_signatures.add(run["response_signature"])
                restart_blob_hashes.add(run["restart_getter_blob_sha256"])

        self.assertEqual(1, len(semantic_rows))
        self.assertEqual(1, len(response_signatures))
        self.assertEqual(1, len(restart_blob_hashes))

    def test_declared_extension_uint32_max_recovers_pristine_after_restart(self) -> None:
        variant_id = "declared-extension-length-ffffffff"
        evidence = summary.EVIDENCE / variant_id
        if not (evidence / "run-2/complete.json").is_file():
            self.skipTest("declared extension UINT32_MAX evidence is not recorded")

        variant = {
            "id": variant_id,
            "suite": (
                "suites/generated/hot-cue-legacy-setter-parser/"
                f"hot-cue-legacy-setter-parser-{variant_id}.json"
            ),
        }
        baseline = json.loads(summary.BASELINE_DATABASE.read_text())

        for run_number in (1, 2):
            run = summary.parse_run(variant, run_number, baseline)
            assert run is not None
            self.assertEqual("raw_reply", run["outcome"])
            self.assertEqual(0x0100, run["response_kind"])
            self.assertEqual(0, run["response_argument_count"])
            self.assertEqual("pristine", run["database_effect"])
            self.assertEqual("timeout", run["getter_outcome"])
            self.assertEqual("alive", run["process_state"])
            self.assertEqual(0, run["application_event_count"])
            self.assertEqual("raw_reply", run["restart_getter_outcome"])
            self.assertEqual("pristine", run["restart_getter_effect"])
            self.assertEqual([124, 124, 124], run["restart_getter_record_lengths"])
            self.assertEqual("pristine", run["restart_database_effect"])

    def test_known_legacy_setter_reply_shape(self) -> None:
        golden = json.loads(
            (
                summary.CONFORMANCE
                / "goldens/rekordbox-7.2.19/xdj-rx3/"
                "hot-cue-bank-legacy-ordinals.json"
            ).read_text()
        )
        parsed = summary.parse_setter(golden["behavior"]["cases"][0])
        self.assertEqual("raw_reply", parsed["outcome"])
        self.assertEqual(0x4702, parsed["response_kind"])
        self.assertEqual(9, parsed["response_argument_count"])
        self.assertEqual(0, parsed["status"])
        self.assertEqual(2, parsed["response_record_count"])

    def test_declared_zero_returns_generic_empty_reply(self) -> None:
        path = summary.EVIDENCE / "declared-cue-length-00000000/run-1/setter.json"
        if not path.is_file():
            self.skipTest("declared-zero live evidence is not recorded")

        document = json.loads(path.read_text())
        parsed = summary.parse_setter(document["behavior"]["cases"][0])
        self.assertEqual("raw_reply", parsed["outcome"])
        self.assertEqual(0x0100, parsed["response_kind"])
        self.assertEqual(0, parsed["response_argument_count"])
        self.assertIsNone(parsed["status"])
        self.assertIsNone(parsed["response_record_count"])

    def test_database_diff_finds_only_mutated_first_rows(self) -> None:
        baseline = json.loads(summary.BASELINE_DATABASE.read_text())
        mutated = json.loads(
            (
                summary.ROOT
                / "data/experiments/hot-cue-bank/legacy-ordinals/live-after.json"
            ).read_text()
        )
        effect, changed = summary.database_effect(baseline, mutated)
        self.assertEqual("changed", effect)
        self.assertEqual(["94201", "94203", "94205"], changed)

    def test_audit_only_changes_do_not_count_as_membership_mutation(self) -> None:
        baseline = json.loads(summary.BASELINE_DATABASE.read_text())
        audit_only = json.loads(json.dumps(baseline))
        audit_only["memberships"][0]["updated_at"] = "2099-01-01"
        audit_only["memberships"][0]["rb_local_usn"] = 999999
        self.assertEqual(("pristine", []), summary.database_effect(baseline, audit_only))


if __name__ == "__main__":
    unittest.main()
