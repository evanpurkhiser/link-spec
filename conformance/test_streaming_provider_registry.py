import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "tools/audit_streaming_provider_registry.py"
OUTPUT = ROOT / "data/static-analysis/streaming-provider-registry.json"
DISASSEMBLY = ROOT / "data/static-analysis/streaming-provider-registry.disasm.txt"


class StreamingProviderRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = json.loads(OUTPUT.read_text())
        cls.providers = {
            provider["name"]: provider
            for provider in cls.document["manager"]["providers"]
        }

    def test_generation_is_byte_identical(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "audit.json"
            disassembly = Path(directory) / "audit.disasm.txt"
            subprocess.run(
                [
                    str(ROOT / ".venv/bin/python"),
                    str(AUDIT),
                    "--output",
                    str(output),
                    "--disassembly-output",
                    str(disassembly),
                ],
                check=True,
                capture_output=True,
            )
            self.assertEqual(OUTPUT.read_bytes(), output.read_bytes())
            self.assertEqual(DISASSEMBLY.read_bytes(), disassembly.read_bytes())

    def test_provider_slots_distinguish_beatport_and_beatsource(self):
        self.assertTrue(self.providers["Beatport"]["constructed"])
        self.assertTrue(self.providers["Beatport"]["used_by_generic_path_classifier"])
        self.assertFalse(self.providers["Beatsource"]["constructed"])
        self.assertFalse(self.providers["Beatsource"]["used_by_generic_path_classifier"])

    def test_beatport_uses_catalog_path_without_login_state(self):
        predicate = self.document["beatport_path_predicate"]
        self.assertEqual("/v4/catalog/tracks/", predicate["substring"])
        self.assertEqual("juce::String::contains", predicate["operation"])
        self.assertFalse(predicate["login_state_read"])
        self.assertFalse(predicate["fixture_scheme_beatport_tracks_matches"])

    def test_beatsource_is_constant_false_in_this_build(self):
        predicate = self.document["beatsource_path_predicate"]
        self.assertFalse(predicate["service_constructed"])
        self.assertFalse(predicate["standalone_result"])


if __name__ == "__main__":
    unittest.main()
