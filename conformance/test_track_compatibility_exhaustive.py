import hashlib
import json
import re
import unittest
from pathlib import Path

import generate_track_compatibility_exhaustive_suites as generator
from track_compatibility_matrix import compatibility_exhaustive_cases


ROOT = Path(__file__).resolve().parent
LAB = ROOT.parent
MATRIX = ROOT / "data/track-compatibility-exhaustive-matrix.json"
FIXTURE = ROOT / "fixtures/generated/compatibility-exhaustive"
DISASSEMBLY = LAB / "data/static-analysis/device-predicate-bodies.disasm.txt"


class TrackCompatibilityExhaustiveTests(unittest.TestCase):
    def test_matrix_exhausts_byte_domain_and_declared_axes(self) -> None:
        matrix = generator.matrix()
        rows = matrix["rows"]

        self.assertEqual(382, len(rows))
        self.assertEqual(
            list(range(256)),
            [row["file_type"] for row in rows if row["axis"] == "file-type-byte"],
        )
        self.assertEqual(
            {
                "file-type-byte": 256,
                "file-type-wide": 14,
                "sample-rate": 56,
                "bit-depth": 56,
            },
            matrix["axes"],
        )
        self.assertEqual(298, sum(bool(row["supported"]) for row in rows))
        self.assertEqual(84, sum(not row["supported"] for row in rows))

    def test_checked_in_declarations_match_generators(self) -> None:
        self.assertEqual(generator.matrix(), json.loads(MATRIX.read_text()))
        for setup in ("extended", "legacy"):
            path = (
                ROOT
                / "suites/generated/track-compatibility-exhaustive"
                / f"track-compatibility-exhaustive-{setup}.json"
            )
            self.assertEqual(generator.suite(setup), json.loads(path.read_text()))

    def test_fixture_is_fingerprint_bound_and_contains_every_declared_row(self) -> None:
        manifest = json.loads((FIXTURE / "manifest.json").read_text())

        self.assertEqual("compatibility-exhaustive", manifest["profile"])
        self.assertEqual(382, manifest["track_count"])
        self.assertEqual(
            manifest["database_sha256"],
            hashlib.sha256((FIXTURE / "master.db").read_bytes()).hexdigest(),
        )
        for index, case in enumerate(compatibility_exhaustive_cases(), start=1):
            self.assertEqual(
                case["id"],
                manifest["ids"][f"track.compatibility_exhaustive.{index:03}"],
            )

    def test_static_predicate_reads_file_type_and_sample_rate_only(self) -> None:
        artifact = DISASSEMBLY.read_text()
        function = self._address_range(artifact, "0x0102256b20", "0x0102256bff")

        self.assertIn("mov       esi, 0xe", function)
        self.assertIn("mov       esi, 0x21", function)
        self.assertNotIn("esi, 0x22", function)
        self.assertIn("lea       ecx, [rbx - 0xb]", function)
        self.assertIn("add       ebx, -5", function)
        self.assertIn("cmp       eax, 0xbb80", function)
        self.assertIn("cmp       eax, 0xac44", function)

    def test_recorder_is_real_rekordbox_only_and_restores_baseline(self) -> None:
        recorder = (ROOT / "record_track_compatibility_exhaustive.sh").read_text()

        self.assertNotIn("rbxport", recorder.lower())
        self.assertIn("activate_fixture.sh", recorder)
        self.assertIn("fixtures/generated/play-paths", recorder)
        self.assertIn("oracle_record.sh", recorder)
        self.assertIn("capture_rekordbox_health.ps1", recorder)
        self.assertIn("record_health_before_sha256", recorder)
        self.assertIn("repeat_health_after_sha256", recorder)
        self.assertIn("repeat", recorder)

        reducer = (LAB / "tools/summarize_track_compatibility_exhaustive.py").read_text()
        self.assertIn('golden["format"] == 2', reducer)
        self.assertIn('provenance["backend_version"] == "7.2.19"', reducer)
        self.assertIn('provenance["suite_sha256"]', reducer)
        self.assertIn('receipt_sha256', reducer)
        self.assertIn('validate_health_pair(', reducer)

    def test_documents_describe_the_completed_live_oracle(self) -> None:
        documents = (
            LAB / "docs/DEVICE_PREDICATE_AUDIT.md",
            LAB / "docs/STATIC_ANALYSIS.md",
            LAB / "docs/BOUNDARY_INVALID_LIFECYCLE_ORACLE.md",
        )

        for path in documents:
            text = " ".join(path.read_text().split())
            with self.subTest(document=path.name):
                self.assertIn("382-row", text)
                self.assertIn("298", text)
                self.assertIn("84", text)
                self.assertNotIn("382-row extended/legacy oracle declares", text)

    @staticmethod
    def _address_range(artifact: str, start: str, end: str) -> str:
        match = re.search(
            rf"^{re.escape(start)} .*?^{re.escape(end)} .*?$",
            artifact,
            flags=re.MULTILINE | re.DOTALL,
        )

        if match is None:
            raise AssertionError(f"missing disassembly range {start}..{end}")

        return match.group(0)


if __name__ == "__main__":
    unittest.main()
