import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
TOOL = ROOT / "tools/inventory_device_status_sources.py"
CANONICAL = ROOT / "data/static-analysis/device-status-source-inventory.json"


class DeviceStatusSourceInventoryTest(unittest.TestCase):
    def test_canonical_inventory_has_explicit_provenance_tiers(self) -> None:
        inventory = json.loads(CANONICAL.read_text())

        self.assertEqual(inventory["dysentery"]["capture_count"], 18)
        self.assertEqual(
            inventory["dysentery"]["fixed_width_device_models"],
            ["CDJ", "CDJ-2000nexus", "DJM-2000nexus"],
        )
        self.assertEqual(
            inventory["counts"],
            {
                "captured_verbatim": 2,
                "corroborating_fixture": 3,
                "corroborating_identity": 1,
                "rx3_template_derived": 10,
            },
        )
        captured = {
            (item["model"], item["player"])
            for item in inventory["lab_status_identities"]
            if item["status_source"] == "captured-verbatim"
        }
        self.assertEqual(captured, {("XDJ-RX3", 11), ("CDJ-2000nexus", 1)})

        fixtures = inventory["corroborating_status_fixtures"]
        self.assertEqual(3, len(fixtures))
        self.assertEqual(
            ["CDJ-2000nexus", "XDJ-XZ", "XDJ-XZ"],
            [fixture["model"] for fixture in fixtures],
        )
        self.assertEqual(
            {
                "42a45b82ea4965e1effc327167141ffa1f60983c3fdba1889b60a98a2b52c0aa",
                "8eadeb284e6c0ed167cd1573ba0ed976d5c1abd85694de1299224b54519ff90f",
                "f596f7ed8e34b5b9ca16e3fc9a50c5d59118308f8055a9514e4562474051ff7b",
            },
            {fixture["sha256"] for fixture in fixtures},
        )
        xdj_fixtures = [fixture for fixture in fixtures if fixture["model"] == "XDJ-XZ"]
        self.assertTrue(all(fixture["capture_date"] == "2026-04-22" for fixture in xdj_fixtures))
        self.assertTrue(all("firmware version" in fixture["missing_provenance"] for fixture in xdj_fixtures))

        xdj_identity = next(
            item
            for item in inventory["lab_status_identities"]
            if item["path"].endswith("xdj-xz-player-1-corroborating-status.json")
        )
        self.assertEqual("corroborating-fixture", xdj_identity["status_source"])

    def test_regeneration_is_byte_identical(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "inventory.json"
            subprocess.run(
                ["python3", str(TOOL), "--output", str(output)],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertEqual(output.read_bytes(), CANONICAL.read_bytes())


if __name__ == "__main__":
    unittest.main()
