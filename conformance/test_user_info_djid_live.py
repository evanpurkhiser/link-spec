import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.summarize_user_info_djid_matrix import classify, expected_classification


PROFILE_ROOT = ROOT / "conformance/user-info-djid-profiles"
SUITE_ROOT = ROOT / "conformance/suites/generated"
MATRIX = ROOT / "conformance/data/user-info-djid-matrix.json"
PROFILE_GENERATOR = ROOT / "tools/generate_user_info_djid_profiles.py"
SUITE_GENERATOR = ROOT / "tools/generate_user_info_djid_suites.py"
RECORDER = ROOT / "conformance/record_user_info_djid_matrix.sh"
FINALIZER = ROOT / "conformance/run_user_info_djid_after_render_controls.sh"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class UserInfoDjidLiveTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = json.loads((PROFILE_ROOT / "manifest.json").read_text())
        self.matrix = json.loads(MATRIX.read_text())

    def test_profiles_regenerate_byte_identically(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            subprocess.run(
                [sys.executable, PROFILE_GENERATOR, "--output", output],
                cwd=ROOT,
                check=True,
            )
            for canonical in PROFILE_ROOT.iterdir():
                self.assertEqual(canonical.read_bytes(), (output / canonical.name).read_bytes())

    def test_suites_and_matrix_regenerate_byte_identically(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            suite_dir = output / "suites"
            matrix = output / "matrix.json"
            subprocess.run(
                [
                    sys.executable,
                    SUITE_GENERATOR,
                    "--suite-dir",
                    suite_dir,
                    "--matrix",
                    matrix,
                ],
                cwd=ROOT,
                check=True,
            )
            self.assertEqual(MATRIX.read_bytes(), matrix.read_bytes())
            for execution in self.matrix["executions"]:
                name = Path(execution["suite"]).name
                self.assertEqual(
                    (SUITE_ROOT / name).read_bytes(),
                    (suite_dir / name).read_bytes(),
                )

    def test_profile_hashes_sizes_and_mixed_endian_checksum(self) -> None:
        profiles = {profile["id"]: profile for profile in self.manifest["profiles"]}
        self.assertEqual(
            {
                "valid-zero-tail",
                "valid-pattern-tail",
                "checksum-invalid",
                "short-159",
                "long-161",
                "alternate-extension-only",
            },
            profiles.keys(),
        )
        for profile in profiles.values():
            path = PROFILE_ROOT / profile["filename"]
            payload = path.read_bytes()
            self.assertEqual(profile["size"], len(payload))
            self.assertEqual(profile["sha256"], sha256(path))
            self.assertEqual(
                profile["first_32_sha256"], hashlib.sha256(payload[:32]).hexdigest()
            )

        payload = (PROFILE_ROOT / profiles["valid-zero-tail"]["filename"]).read_bytes()
        checksum = (
            int.from_bytes(payload[0:4], "little")
            + int.from_bytes(payload[4:8], "big")
            + int.from_bytes(payload[8:12], "big")
            + int.from_bytes(payload[12:16], "big")
        ) & 0xFFFFFFFF
        self.assertEqual(checksum, int.from_bytes(payload[28:32], "big"))
        self.assertNotEqual(
            checksum,
            int.from_bytes(
                (PROFILE_ROOT / profiles["checksum-invalid"]["filename"]).read_bytes()[
                    28:32
                ],
                "big",
            ),
        )

    def test_absent_suites_exhaust_argument_and_identity_axes(self) -> None:
        absent = [
            execution
            for execution in self.matrix["executions"]
            if execution["profile"] == "absent"
        ]
        self.assertEqual(3, len(absent))
        self.assertEqual(135, sum(execution["case_count"] for execution in absent))
        for execution in absent:
            suite = json.loads((ROOT / "conformance" / execution["suite"]).read_text())
            cases = suite["cases"]
            counts = {
                len(case["arguments"])
                for case in cases
                if case["id"].startswith("argument-count-")
            }
            self.assertEqual(set(range(33)), counts)
            self.assertTrue(all(case["request_kind"] == "0x3006" for case in cases))
            self.assertTrue(all(case["direct_response"] for case in cases))
            self.assertTrue(all(case["expect"]["outcome"] == "any" for case in cases))

    def test_profile_matrix_is_authority_only_and_complete(self) -> None:
        self.assertEqual(8, len(self.matrix["profiles"]))
        self.assertEqual(10, self.matrix["execution_count"])
        self.assertEqual(142, self.matrix["case_count"])
        self.assertEqual(284, self.matrix["record_repeat_execution_count"])
        profile_executions = [
            execution
            for execution in self.matrix["executions"]
            if execution["profile"] != "absent"
        ]
        self.assertEqual(7, len(profile_executions))
        self.assertTrue(all(execution["case_count"] == 1 for execution in profile_executions))

    def test_reducer_distinguishes_zero_and_160_byte_blob_replies(self) -> None:
        def number(value: int) -> dict:
            return {"type": "number", "value": value}

        empty = classify(
            {
                "outcome": "raw_reply",
                "raw_response": {
                    "messages": [
                        {
                            "kind": 0x4D02,
                            "arguments": [
                                number(0x3006),
                                number(0),
                                number(0),
                                {"type": "blob", "hex": ""},
                            ],
                        }
                    ]
                },
            }
        )
        self.assertEqual("empty-4d02", empty["classification"])
        self.assertEqual(0, empty["blob_length"])

        payload = bytes(range(32)) + bytes(128)
        populated = classify(
            {
                "outcome": "raw_reply",
                "raw_response": {
                    "messages": [
                        {
                            "kind": 0x4D02,
                            "arguments": [
                                number(0x3006),
                                number(0),
                                number(160),
                                {"type": "blob", "hex": payload.hex()},
                            ],
                        }
                    ]
                },
            }
        )
        self.assertEqual("blob-160-4d02", populated["classification"])
        self.assertTrue(populated["blob_tail_all_zero"])
        self.assertEqual(hashlib.sha256(payload[:32]).hexdigest(), populated["blob_first_32_sha256"])
        self.assertEqual("blob-160-4d02", expected_classification("valid-zero-tail"))
        self.assertEqual("empty-4d02", expected_classification("checksum-invalid"))

    def test_recorder_owns_and_restores_profile_paths(self) -> None:
        recorder = RECORDER.read_text()
        for marker in (
            "djprofile.nxs.link-export-oracle-backup",
            "djprofile.bin.link-export-oracle-backup",
            "trap restore EXIT",
            "restore_original_profiles",
            "restored-profile-state.json",
            'activate_fixture.sh" "$baseline"',
        ):
            self.assertIn(marker, recorder)

    def test_finalizer_is_guarded_and_leaves_a_clean_lab(self) -> None:
        finalizer = FINALIZER.read_text()
        for marker in (
            "codex-rekordbox-render-override-controls-20261003ar18.service",
            "record_user_info_djid_matrix.sh",
            "summarize_user_info_djid_matrix.py",
            "test_real_rekordbox_phase_boundary",
            "original_profile_restored:true",
            "synthetic_identity_units_active:false",
            "isolated_vm_stopped:true",
        ):
            self.assertIn(marker, finalizer)
        self.assertNotIn("rbxport", finalizer.lower())


if __name__ == "__main__":
    unittest.main()
