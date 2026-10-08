import json
import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.summarize_adjacent_payload_fileless import (
    EXPECTED_MESSAGES,
    EXPECTED_TIMEOUT_IDS,
    EXPECTED_WIRE_BYTES,
    normalized_kind,
    summarize,
)
from tools.summarize_adjacent_payload_missing_files import summarize_missing_files
from tools.summarize_adjacent_payload_malformed import (
    event_signature,
    health_signature,
)


GENERATED = ROOT / "data/static-analysis/adjacent-payload-services.json"
GENERATOR = ROOT / "tools/generate_adjacent_payload_service_map.py"
SUITE_GENERATOR = ROOT / "conformance/generate_adjacent_payload_suite.py"
SUITE = ROOT / "conformance/suites/adjacent-payload-fileless.json"
MALFORMED_GENERATOR = ROOT / "conformance/generate_adjacent_payload_malformed_suite.py"
MALFORMED_MATRIX = ROOT / "conformance/data/adjacent-payload-malformed-matrix.json"
MALFORMED_SUITES = ROOT / "conformance/suites/generated/adjacent-payload-malformed"
MALFORMED_SUMMARY = (
    ROOT / "data/experiments/adjacent-payload/malformed/summary.json"
)
MALFORMED_RESULT_MATRIX = (
    ROOT / "data/experiments/adjacent-payload/malformed/matrix.csv"
)
MALFORMED_FINALIZATION = (
    ROOT / "data/experiments/adjacent-payload/malformed/finalization.json"
)
MISSING_FILE_GENERATOR = (
    ROOT / "conformance/generate_adjacent_payload_missing_file_suite.py"
)
MISSING_FILE_SUITE = ROOT / "conformance/suites/adjacent-payload-missing-files.json"
MISSING_FILE_SUMMARY = (
    ROOT / "data/experiments/adjacent-payload/missing-files/summary.json"
)
MISSING_FILE_RESULT_MATRIX = (
    ROOT / "data/experiments/adjacent-payload/missing-files/matrix.csv"
)
MISSING_FILE_FINALIZATION = (
    ROOT / "data/experiments/adjacent-payload/missing-files/finalization.json"
)
MANIFEST = ROOT / "conformance/fixtures/generated/full/manifest.json"
MISSING_FILE_MANIFEST = (
    ROOT / "conformance/fixtures/generated/payload-paths/manifest.json"
)
RECORDER = ROOT / "conformance/record_adjacent_payload_fileless.sh"
MALFORMED_RECORDER = ROOT / "conformance/record_adjacent_payload_malformed.sh"
MISSING_FILE_RECORDER = (
    ROOT / "conformance/record_adjacent_payload_missing_files.sh"
)


class AdjacentPayloadServiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = json.loads(GENERATED.read_text())
        cls.services = {row["kind"]: row for row in cls.document["services"]}

    def test_generation_is_byte_identical(self):
        with tempfile.TemporaryDirectory() as directory:
            candidate = Path(directory) / "services.json"
            subprocess.run(
                [str(ROOT / ".venv/bin/python"), str(GENERATOR), "--output", str(candidate)],
                check=True,
            )
            self.assertEqual(GENERATED.read_bytes(), candidate.read_bytes())

    def test_complete_image_and_analysis_dispatch_domain(self):
        self.assertEqual(
            set(self.services),
            {"2003", "2103", *(f"{value:02x}04" for value in range(0x20, 0x2E))},
        )

    def test_atom_gate_is_described_in_correct_direction(self):
        for kind in ("2c04", "2d04"):
            notes = " ".join(self.services[kind]["notes"])
            self.assertIn("short-circuited to an empty 4f02", notes)
            self.assertIn("all other atom tags reach MstLoadAtomInfo", notes)

    def test_appsync_artwork_path_is_not_djmd_image(self):
        direct = self.services["2003"]["database"]
        by_content = self.services["2103"]["database"]
        self.assertIn("djmdContent", direct)
        self.assertIn("djmdPlaylist", direct)
        self.assertIn("AppSync", by_content)
        self.assertIn("Master fallback", by_content)

    def test_only_cue_services_are_file_independent(self):
        file_independent = {
            kind
            for kind, row in self.services.items()
            if row["filesystem"] is None and row["reply_kind"] is not None
        }
        self.assertEqual(file_independent, {"2104", "2b04"})

    def test_live_declaration_is_byte_identical(self):
        before = SUITE.read_bytes()
        subprocess.run([str(ROOT / ".venv/bin/python"), str(SUITE_GENERATOR)], check=True)
        self.assertEqual(before, SUITE.read_bytes())

    def test_live_declaration_covers_static_domain_and_axes(self):
        suite = json.loads(SUITE.read_text())
        cases = suite["cases"]
        kinds = {case["request_kind"][2:].casefold() for case in cases}
        self.assertEqual(kinds, set(self.services))
        self.assertEqual(len(cases), 196)

        ids = {case["id"] for case in cases}
        for kind in self.services:
            for track_type in range(7):
                self.assertIn(f"kind-{kind}--type-{track_type:02x}", ids)
            if kind in {"2304", "2404", "2604", "2704"}:
                self.assertIn(f"kind-{kind}--context-zero", ids)
                self.assertIn(f"kind-{kind}--context-maximum", ids)
            else:
                self.assertIn(f"kind-{kind}--id-zero", ids)
                self.assertIn(f"kind-{kind}--id-maximum", ids)

    def test_log_only_arms_are_context_only(self):
        suite = json.loads(SUITE.read_text())
        cases = {case["id"]: case for case in suite["cases"]}
        ids = set(cases)
        for kind in ("2304", "2404", "2604", "2704"):
            with self.subTest(kind=kind):
                self.assertEqual(self.services[kind]["arguments"], ["packed-context"])
                self.assertEqual(len(cases[f"kind-{kind}--type-01"]["arguments"]), 1)

        for kind in ("2c04", "2d04"):
            for gate in ("pcp2", "pcpt", "pmai"):
                self.assertIn(f"kind-{kind}--atom-{gate}-ext-short-circuit", ids)

    def test_malformed_declaration_is_byte_identical_and_complete(self):
        matrix = json.loads(MALFORMED_MATRIX.read_text())
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory) / "suites"
            candidate_matrix = Path(directory) / "matrix.json"
            subprocess.run(
                [
                    str(ROOT / ".venv/bin/python"),
                    str(MALFORMED_GENERATOR),
                    "--output-dir",
                    str(output_dir),
                    "--matrix",
                    str(candidate_matrix),
                ],
                check=True,
            )
            self.assertEqual(MALFORMED_MATRIX.read_bytes(), candidate_matrix.read_bytes())
            for entry in matrix["cases"]:
                name = f"{entry['id']}.json"
                self.assertEqual(
                    (MALFORMED_SUITES / name).read_bytes(),
                    (output_dir / name).read_bytes(),
                )

        cases = [
            json.loads((ROOT / "conformance" / entry["suite"]).read_text())["cases"][0]
            for entry in matrix["cases"]
        ]
        self.assertEqual(len(cases), 96)
        self.assertEqual(len({case["id"] for case in cases}), 96)
        self.assertEqual(
            {case["request_kind"][2:].casefold() for case in cases},
            set(self.services),
        )
        counts = {}
        for case in cases:
            kind = case["request_kind"][2:].casefold()
            counts[kind] = counts.get(kind, 0) + 1
            self.assertTrue(case["direct_response"])
            self.assertTrue(case["fresh_connection"])
            self.assertFalse(case["render"])
        self.assertEqual(set(counts.values()), {6})

    def test_missing_file_declaration_is_byte_identical_and_complete(self):
        with tempfile.TemporaryDirectory() as directory:
            candidate = Path(directory) / "suite.json"
            subprocess.run(
                [
                    str(ROOT / ".venv/bin/python"),
                    str(MISSING_FILE_GENERATOR),
                    "--output",
                    str(candidate),
                ],
                check=True,
            )
            self.assertEqual(MISSING_FILE_SUITE.read_bytes(), candidate.read_bytes())

        suite = json.loads(MISSING_FILE_SUITE.read_text())
        cases = suite["cases"]
        expected_kinds = {
            "2003", "2103", "2004", "2204", "2504",
            "2804", "2904", "2a04", "2c04", "2d04",
        }
        self.assertEqual(suite["fixture_profile"], "payload-paths")
        self.assertEqual(len(cases), 31)
        self.assertEqual(
            {case["request_kind"][2:].casefold() for case in cases},
            expected_kinds,
        )
        ids = {case["id"] for case in cases}
        for kind in expected_kinds:
            for state in ("nonempty-missing", "empty", "null"):
                self.assertIn(f"kind-{kind}--path-{state}", ids)
        self.assertIn("kind-2003--path-playlist-nonempty-missing", ids)
        self.assertTrue(all(case["direct_response"] for case in cases))
        self.assertTrue(all(case["fresh_connection"] for case in cases))
        self.assertTrue(all(not case["render"] for case in cases))
        self.assertEqual(
            {case.get("fixed_tag_slots") for case in cases if case["request_kind"] == "0x2004"},
            {5},
        )

        manifest = json.loads(MISSING_FILE_MANIFEST.read_text())
        self.assertEqual(manifest["profile"], "payload-paths")
        self.assertEqual(manifest["integrity"], "ok")
        self.assertEqual(
            manifest["database_sha256"],
            "e76d36efea45461623049798b48f61a17fc436201a192bcf15ebca6e399516ef",
        )
        self.assertEqual(
            manifest["fixture_fingerprint"],
            "cd963cfacdc6197dcf347df8c5bfebf0400eaf48d1a3f1b0d0bfcc1d234e6fb8",
        )

    def test_fileless_recorder_uses_cold_repeat_health_and_receipt(self):
        recorder = RECORDER.read_text()
        self.assertNotIn("rbxport", recorder.lower())
        self.assertIn("run_phase record", recorder)
        self.assertIn("run_phase repeat", recorder)
        self.assertGreaterEqual(recorder.count("activate_fixture.sh"), 2)
        self.assertIn("start_oracle_ui.sh", recorder)
        self.assertIn("record-health-before.json", recorder)
        self.assertIn("repeat-health-after.json", recorder)
        self.assertIn("exact_repeat:true", recorder)
        self.assertLess(recorder.index("run_phase repeat"), recorder.index('mv "$candidate" "$golden"'))

    def test_malformed_recorder_is_case_isolated_and_resumable(self):
        recorder = MALFORMED_RECORDER.read_text()
        self.assertNotIn("rbxport", recorder.lower())
        self.assertIn("adjacent-payload-malformed-matrix.json", recorder)
        self.assertIn("resuming complete record-side candidate", recorder)
        self.assertIn("incomplete record-side evidence", recorder)
        self.assertIn('run_phase_with_retry "$id" "$suite" "$candidate" "$evidence" record', recorder)
        self.assertIn('run_phase_with_retry "$id" "$suite" "$candidate" "$evidence" repeat', recorder)
        self.assertIn("case_count:1, exact_repeat:true", recorder)
        self.assertIn("mapfile -t declarations", recorder)
        self.assertIn('for declaration in "${declarations[@]}"', recorder)
        self.assertNotIn("done < <(jq", recorder)
        self.assertIn("run_phase_with_retry", recorder)
        self.assertIn("quarantined failed", recorder)
        self.assertIn("(set -euo pipefail; run_phase", recorder)
        self.assertIn('for attempt in 1 2 3', recorder)
        self.assertLess(
            recorder.index('run_phase_with_retry "$id" "$suite" "$candidate" "$evidence" repeat'),
            recorder.index('mv "$candidate" "$golden"'),
        )
        summarizer = (ROOT / "tools/summarize_adjacent_payload_malformed.py").read_text()
        self.assertIn("enforce_expected_oracle=False", summarizer)

    def test_malformed_health_signature_normalizes_volatile_event_fields(self):
        event = {
            "provider": "Application Error",
            "event_id": 1000,
            "level": "Error",
            "record_id": 1234,
            "time_created_utc": "2026-10-03T00:00:00Z",
            "message": (
                "Faulting application name: rekordbox.exe, version: 7.2.19.0\r\n"
                "Faulting module name: ntdll.dll, version: 10.0\r\n"
                "Exception code: 0xc0000374\r\n"
                "Fault offset: 0x00000000001176e5\r\n"
                "Faulting process id: 0x1234"
            ),
        }
        self.assertEqual(
            event_signature(event),
            {
                "provider": "Application Error",
                "event_id": 1000,
                "level": "Error",
                "application": "rekordbox.exe",
                "module": "ntdll.dll",
                "exception_code": "0xc0000374",
                "fault_offset": "0x00000000001176e5",
            },
        )

    def test_malformed_health_signature_requires_schema_two_and_exact_count(self):
        document = {
            "schema_version": 2,
            "rekordbox_process_count": 1,
            "rekordbox_processes": [{"responding": True}],
            "application_events": [],
        }
        self.assertEqual(
            health_signature(document),
            {"process_count": 1, "responding_count": 1, "application_events": []},
        )
        with self.assertRaisesRegex(ValueError, "schema 2"):
            health_signature({**document, "schema_version": 1})
        with self.assertRaisesRegex(ValueError, "process count"):
            health_signature({**document, "rekordbox_process_count": 0})

    def test_malformed_real_rekordbox_evidence_is_complete_and_bound(self):
        summary = json.loads(MALFORMED_SUMMARY.read_text())
        receipt = json.loads(MALFORMED_FINALIZATION.read_text())

        self.assertEqual(summary["case_count"], 96)
        self.assertEqual(summary["service_count"], 16)
        self.assertEqual(summary["outcome_counts"], {"raw_reply": 80, "timeout": 16})
        self.assertEqual(
            {row["kind"] for row in summary["services"]},
            set(self.services),
        )
        self.assertTrue(all(row["case_count"] == 6 for row in summary["services"]))
        self.assertTrue(
            all(
                row["outcomes"] == {"raw_reply": 5, "timeout": 1}
                for row in summary["services"]
            )
        )

        self.assertEqual(receipt["case_count"], 96)
        self.assertEqual(receipt["service_count"], 16)
        self.assertTrue(receipt["focused_tests_passed"])
        self.assertFalse(receipt["synthetic_identity_units_active"])
        self.assertTrue(receipt["isolated_vm_stopped"])
        self.assertEqual(
            receipt["summary_sha256"],
            hashlib.sha256(MALFORMED_SUMMARY.read_bytes()).hexdigest(),
        )
        self.assertEqual(
            receipt["matrix_sha256"],
            hashlib.sha256(MALFORMED_RESULT_MATRIX.read_bytes()).hexdigest(),
        )

    def test_missing_file_recorder_uses_cold_repeat_health_and_receipt(self):
        recorder = MISSING_FILE_RECORDER.read_text()
        self.assertNotIn("rbxport", recorder.lower())
        self.assertIn("run_phase record", recorder)
        self.assertIn("run_phase repeat", recorder)
        self.assertGreaterEqual(recorder.count("activate_fixture.sh"), 2)
        self.assertIn("record-health-before.json", recorder)
        self.assertIn("repeat-health-after.json", recorder)
        self.assertIn("case_count:31, service_count:10, exact_repeat:true", recorder)
        self.assertLess(
            recorder.index("run_phase repeat"),
            recorder.index('mv "$candidate" "$golden"'),
        )

        success = (ROOT / "tools/summarize_adjacent_payload_success.py").read_text()
        self.assertIn("enforce_expected_oracle=False", success)

    def test_missing_file_real_rekordbox_evidence_is_complete_and_bound(self):
        summary = json.loads(MISSING_FILE_SUMMARY.read_text())
        receipt = json.loads(MISSING_FILE_FINALIZATION.read_text())

        self.assertEqual(summary["case_count"], 31)
        self.assertEqual(summary["service_count"], 10)
        self.assertEqual(summary["outcome_counts"], {"raw_reply": 31})
        self.assertEqual(
            summary["path_state_counts"],
            {
                "empty": 10,
                "nonempty-missing": 10,
                "null": 10,
                "playlist-nonempty-missing": 1,
            },
        )
        self.assertEqual(
            summary["post_request_health"],
            {"process_count": 1, "responding_count": 1, "application_events": []},
        )

        self.assertEqual(receipt["case_count"], 31)
        self.assertEqual(receipt["service_count"], 10)
        self.assertTrue(receipt["focused_tests_passed"])
        self.assertFalse(receipt["synthetic_identity_units_active"])
        self.assertTrue(receipt["isolated_vm_stopped"])
        self.assertEqual(
            receipt["summary_sha256"],
            hashlib.sha256(MISSING_FILE_SUMMARY.read_bytes()).hexdigest(),
        )
        self.assertEqual(
            receipt["matrix_sha256"],
            hashlib.sha256(MISSING_FILE_RESULT_MATRIX.read_bytes()).hexdigest(),
        )

    def test_fileless_summary_validates_the_complete_direct_response_matrix(self):
        suite = json.loads(SUITE.read_text())
        manifest = json.loads(MANIFEST.read_text())
        cases = []
        for declaration in suite["cases"]:
            identifier = declaration["id"]
            kind = normalized_kind(declaration["request_kind"])
            outcome = "timeout" if identifier in EXPECTED_TIMEOUT_IDS else "raw_reply"
            raw_bytes = 0 if outcome == "timeout" else EXPECTED_WIRE_BYTES[kind]
            cases.append(
                {
                    "id": identifier,
                    "description": declaration["description"],
                    "request": {
                        "kind": int(declaration["request_kind"], 16),
                        "arguments": [],
                        "fixed_tag_slots": declaration.get("fixed_tag_slots"),
                    },
                    "outcome": outcome,
                    "raw_response": {
                        "outcome": outcome,
                        "raw_hex": "00" * raw_bytes,
                        "decoded_bytes": raw_bytes if outcome == "raw_reply" else None,
                        "messages": [] if outcome == "timeout" else [EXPECTED_MESSAGES[kind]],
                        "error_kind": "WouldBlock" if outcome == "timeout" else None,
                    },
                    "total": None,
                    "header": [],
                    "pages": [],
                    "rows": [],
                }
            )

        fake = {
            "format": 2,
            "provenance": {
                "backend": "rekordbox",
                "backend_version": "7.2.19",
                "suite_sha256": hashlib.sha256(SUITE.read_bytes()).hexdigest(),
                "fixture_database_sha256": manifest["database_sha256"],
                "fixture_fingerprint": manifest["fixture_fingerprint"],
            },
            "behavior": {
                "suite": suite["name"],
                "fixture": {
                    "profile": suite["fixture_profile"],
                    "fingerprint": manifest["fixture_fingerprint"],
                    "version": manifest["fixture_version"],
                },
                "cases": cases,
            },
        }
        with tempfile.TemporaryDirectory() as directory:
            golden = Path(directory) / "golden.json"
            golden.write_text(json.dumps(fake))
            summary, matrix = summarize(SUITE, MANIFEST, golden)

        self.assertEqual(summary["case_count"], 196)
        self.assertEqual(summary["service_count"], 16)
        self.assertTrue(summary["expected_oracle_asserted"])
        self.assertEqual(summary["outcome_counts"], {"raw_reply": 176, "timeout": 20})
        self.assertEqual(len(matrix), 196)

    def test_missing_file_summary_validates_path_state_matrix(self):
        suite = json.loads(MISSING_FILE_SUITE.read_text())
        manifest = json.loads(MISSING_FILE_MANIFEST.read_text())
        cases = []
        for declaration in suite["cases"]:
            cases.append(
                {
                    "id": declaration["id"],
                    "description": declaration["description"],
                    "request": {
                        "kind": int(declaration["request_kind"], 16),
                        "arguments": [],
                        "fixed_tag_slots": declaration.get("fixed_tag_slots"),
                    },
                    "outcome": "raw_reply",
                    "raw_response": {
                        "outcome": "raw_reply",
                        "raw_hex": "",
                        "decoded_bytes": 0,
                        "messages": [],
                        "error_kind": None,
                    },
                    "total": None,
                    "header": [],
                    "pages": [],
                    "rows": [],
                }
            )

        fake = {
            "format": 2,
            "provenance": {
                "backend": "rekordbox",
                "backend_version": "7.2.19",
                "suite_sha256": hashlib.sha256(MISSING_FILE_SUITE.read_bytes()).hexdigest(),
                "fixture_database_sha256": manifest["database_sha256"],
                "fixture_fingerprint": manifest["fixture_fingerprint"],
            },
            "behavior": {
                "suite": suite["name"],
                "fixture": {
                    "profile": suite["fixture_profile"],
                    "fingerprint": manifest["fixture_fingerprint"],
                    "version": manifest["fixture_version"],
                },
                "cases": cases,
            },
        }
        with tempfile.TemporaryDirectory() as directory:
            golden = Path(directory) / "golden.json"
            golden.write_text(json.dumps(fake))
            summary, matrix = summarize_missing_files(
                MISSING_FILE_SUITE,
                MISSING_FILE_MANIFEST,
                golden,
            )

        self.assertEqual(summary["case_count"], 31)
        self.assertEqual(summary["service_count"], 10)
        self.assertEqual(
            summary["path_state_counts"],
            {
                "empty": 10,
                "nonempty-missing": 10,
                "null": 10,
                "playlist-nonempty-missing": 1,
            },
        )
        self.assertEqual(len(matrix), 31)


if __name__ == "__main__":
    unittest.main()
