import importlib.util
import json
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


settings = load_module(
    "generate_key_notation_settings",
    ROOT / "generate_key_notation_settings.py",
)
suites = load_module(
    "generate_key_notation_suites",
    ROOT / "generate_key_notation_suites.py",
)


class KeyNotationFixtureTests(unittest.TestCase):
    def test_preference_states_cover_the_complete_boolean_cross(self) -> None:
        self.assertEqual(
            {
                "classic-normalized": ("1", "0"),
                "classic-database": ("1", "1"),
                "alphanumeric-normalized": ("2", "0"),
                "alphanumeric-database": ("2", "1"),
            },
            settings.STATES,
        )

        for state, expected in settings.STATES.items():
            root = ET.parse(settings.OUTPUT / f"{state}.settings").getroot()
            values = {
                element.attrib["name"]: element.attrib["val"]
                for element in root.findall("VALUE")
                if "name" in element.attrib and "val" in element.attrib
            }
            self.assertEqual(expected[0], values["KeyStringSetting"])
            self.assertEqual(expected[1], values["ShowOriginalKey"])

    def test_suites_cover_all_notation_response_families(self) -> None:
        self.assertEqual(tuple(settings.STATES), suites.STATES)

        for state in suites.STATES:
            suite = json.loads(
                (suites.OUTPUT / f"key-notation-{state}.json").read_text()
            )
            self.assertEqual("key-notation", suite["fixture_profile"])
            self.assertEqual("fixture-reset-and-restart", suite["repeat_strategy"])
            self.assertEqual(13, len(suite["cases"]))
            self.assertEqual(
                {
                    "key-root",
                    "key-distances",
                    "key-tracks",
                    "collection-bpm",
                    "collection-key",
                    "collection-key-sort",
                    "smart-bpm",
                    "smart-key",
                    "smart-key-sort",
                    "display-bpm",
                    "display-key",
                    "delivery-bpm",
                    "delivery-key",
                },
                {case["id"] for case in suite["cases"]},
            )


if __name__ == "__main__":
    unittest.main()
