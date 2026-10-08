import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.summarize_streaming_provider_paths import (
    ALL,
    ORDINARY_CASES,
    STATIC_FILTERED,
    STATIC_VISIBLE,
)


GENERATOR = ROOT / "conformance/generate_streaming_provider_paths_suite.py"
SUITE = ROOT / "conformance/suites/generated/streaming-provider-paths.json"
FIXTURE = ROOT / "conformance/fixtures/generated/streaming-provider-paths/manifest.json"
RECORDER = ROOT / "conformance/record_streaming_provider_paths.sh"
FINALIZER = ROOT / "conformance/run_streaming_provider_paths_after_user_info.sh"


class StreamingProviderPathTests(unittest.TestCase):
    def test_suite_regenerates_byte_identically(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "suite.json"
            source = GENERATOR.read_text().replace(
                'OUTPUT = ROOT / "suites/generated/streaming-provider-paths.json"',
                f'OUTPUT = Path({str(output)!r})',
            )
            candidate = Path(directory) / "generator.py"
            candidate.write_text(source)
            subprocess.run([sys.executable, candidate], check=True, capture_output=True)
            self.assertEqual(SUITE.read_bytes(), output.read_bytes())

    def test_fixture_and_suite_cover_the_authority_matrix(self):
        fixture = json.loads(FIXTURE.read_text())
        suite = json.loads(SUITE.read_text())
        self.assertEqual("streaming-provider-paths", fixture["profile"])
        self.assertEqual(10, fixture["track_count"])
        self.assertEqual(7, len(suite["cases"]))
        self.assertEqual(set((*ORDINARY_CASES, "history")), {case["id"] for case in suite["cases"]})
        self.assertTrue(all(case["expect"] == {"outcome": "menu"} for case in suite["cases"]))

    def test_static_prediction_partitions_every_track(self):
        self.assertEqual(set(ALL), set(STATIC_VISIBLE) | set(STATIC_FILTERED))
        self.assertFalse(set(STATIC_VISIBLE) & set(STATIC_FILTERED))
        self.assertEqual((11002, 11003, 11004), STATIC_FILTERED)

    def test_recorder_is_real_rekordbox_only(self):
        recorder = RECORDER.read_text()
        self.assertIn("record_adjacent_payload_fileless.sh", recorder)
        self.assertIn("streaming-provider-paths", recorder)
        self.assertNotIn("rbxport", recorder.lower())

    def test_finalizer_preserves_the_authority_phase_boundary(self):
        finalizer = FINALIZER.read_text()
        self.assertIn("codex-rekordbox-user-info-djid-20261004as18.service", finalizer)
        self.assertIn("record_streaming_provider_paths.sh", finalizer)
        self.assertIn("summarize_streaming_provider_paths.py", finalizer)
        self.assertIn("test_real_rekordbox_phase_boundary", finalizer)
        self.assertIn('"$vm/vmctl" isolated-stop', finalizer)
        self.assertNotIn("rbxport", finalizer.lower())


if __name__ == "__main__":
    unittest.main()
