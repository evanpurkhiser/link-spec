import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "data/static-analysis/xdj-rr-client-navigation.json"
VOCABULARY = ROOT / "data/static-analysis/link-export-request-vocabulary.json"
GENERATOR = ROOT / "tools/extract_xdj_rr_client_navigation.py"


class XdjRrClientNavigationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = json.loads(INVENTORY.read_text())
        cls.sites = cls.document["call_sites"]
        cls.wrappers = {
            wrapper["name"]: wrapper for wrapper in cls.document["wrappers"]
        }

    def test_summary_is_exact(self):
        self.assertEqual(self.document["source"]["commit"], "a70aeefb202ffddd2900e7b40e339a47ac077057")
        self.assertEqual(
            self.document["summary"],
            {
                "source_file_count": 6,
                "request_wrapper_count": 121,
                "request_kind_count": 116,
                "direct_call_site_count": 304,
                "direct_call_request_kind_count": 102,
                "literal_locations": list(range(1, 9)),
                "dynamic_location_call_site_count": 62,
            },
        )

    def test_every_request_kind_is_in_the_joined_vocabulary(self):
        vocabulary = json.loads(VOCABULARY.read_text())
        kinds = {command["kind"] for command in vocabulary["commands"]}
        self.assertTrue(
            {wrapper["request_kind"] for wrapper in self.wrappers.values()} <= kinds
        )

    def test_command_constructor_propagates_real_location_argument(self):
        self.assertEqual(self.wrappers["dbcl_GetImage"]["fixed_location"], 8)
        self.assertEqual(self.wrappers["dbcl_GetDeliverySongInfo"]["fixed_location"], 9)
        self.assertEqual(self.wrappers["dbcl_GetDJInfo"]["fixed_location"], 7)
        self.assertEqual(
            self.wrappers["dbcl_GetRootMenuItems"]["location_parameter"], 2
        )
        self.assertNotIn("dbcl_GetNextRecord", self.wrappers)

    def test_literal_location_roles_have_direct_call_evidence(self):
        roles = {
            4: {"GetLoadedMusicData", "GetListOfPlaying"},
            5: {"GetSortMenuList", "GetOneData_SongInfo"},
            6: {"GetPrepListFromDB", "AddPrepare", "DbReqTaglist2Playlist"},
            7: {"ReloadCateBrws", "DbReqCueBankDragDrop"},
            8: {"ReqLoadWave", "DbReqUsbSdCue_Ext"},
        }
        for location, expected_callers in roles.items():
            callers = {
                site["caller"]
                for site in self.sites
                if site["literal_location"] == location
            }
            with self.subTest(location=location):
                self.assertTrue(expected_callers & callers)

    def test_wrapper_and_call_site_locations_are_distinguished(self):
        delivery_sites = [
            site for site in self.sites if site["request_kind"] == "2602"
        ]
        self.assertEqual(delivery_sites, [])
        self.assertEqual(
            self.wrappers["dbcl_GetDeliverySongInfo"]["fixed_location"], 9
        )

    def test_regeneration_is_byte_identical(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / INVENTORY.name
            subprocess.run(
                ["python3", str(GENERATOR), "--output", str(output)],
                cwd=ROOT,
                check=True,
                capture_output=True,
            )
            self.assertEqual(output.read_bytes(), INVENTORY.read_bytes())


if __name__ == "__main__":
    unittest.main()
