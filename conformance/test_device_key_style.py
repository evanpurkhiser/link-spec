from __future__ import annotations

import binascii
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import mutate_device_setting as device_setting  # noqa: E402


class DeviceKeyStyleTest(unittest.TestCase):
    def test_baseline_and_generated_variants(self) -> None:
        root = ROOT / "data/experiments/key-notation/device-settings"
        baseline = (root / "baseline/DEVSETTING.DAT").read_bytes()
        self.assertEqual("classic", device_setting.validate(baseline)["key_style"])

        for style, value in device_setting.STYLES.items():
            generated = (root / f"generated/{style}.DAT").read_bytes()
            metadata = device_setting.validate(generated)
            self.assertEqual(style, metadata["key_style"])
            self.assertEqual(value, generated[device_setting.KEY_STYLE_OFFSET])
            self.assertEqual(
                binascii.crc_hqx(
                    generated[
                        device_setting.PAYLOAD_OFFSET :
                        device_setting.PAYLOAD_OFFSET + device_setting.PAYLOAD_SIZE
                    ],
                    0,
                ),
                metadata["crc"],
            )

    def test_generated_suites_cover_all_key_surfaces(self) -> None:
        expected = {
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
        }
        for style in device_setting.STYLES:
            path = ROOT / f"conformance/suites/generated/key-device-setting-{style}.json"
            suite = json.loads(path.read_text())
            self.assertEqual("key-notation", suite["fixture_profile"])
            self.assertEqual(expected, {case["id"] for case in suite["cases"]})

    def test_persisted_bpm_suites(self) -> None:
        expected = {
            "device-key-style-alphanumeric-secondary-bpm": (
                "settings",
                {"sort-menu", "track-rows"},
            ),
            "device-key-style-alphanumeric-smart-secondary-bpm": (
                "smart-settings",
                {"tracks"},
            ),
        }
        for name, (profile, cases) in expected.items():
            path = ROOT / f"conformance/suites/generated/{name}.json"
            suite = json.loads(path.read_text())
            self.assertEqual(profile, suite["fixture_profile"])
            self.assertEqual(cases, {case["id"] for case in suite["cases"]})
            self.assertEqual(
                "fixture-reset-device-setting-reset-and-restart",
                suite["repeat_strategy"],
            )


if __name__ == "__main__":
    unittest.main()
