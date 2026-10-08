import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
AUDIT = ROOT / "data/secondary-column-semantics.json"
GENERATOR = ROOT / "tools/generate_secondary_column_semantics.py"


class SecondaryColumnSemanticsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.audit = json.loads(AUDIT.read_text())

    def test_audit_regenerates_byte_identically(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "semantics.json"
            subprocess.run(
                [sys.executable, GENERATOR, "--output", output],
                cwd=ROOT,
                check=True,
            )
            self.assertEqual(AUDIT.read_bytes(), output.read_bytes())

    def test_profile_domains_are_complete(self) -> None:
        profiles = self.audit["profiles"]
        self.assertEqual(15, len(profiles["persisted_default"]))
        self.assertEqual(11, len(profiles["active_sort_render_6"]))
        self.assertEqual(19, len(profiles["explicit_render_8"]))
        self.assertEqual(
            18, len(profiles["active_sort_render_8_persisted_fallback"])
        )
        self.assertEqual(
            504,
            sum(
                len(profile["all_track_fields"])
                for group in profiles.values()
                for profile in group
            ),
        )
        self.assertTrue(
            all(
                len(profile["all_track_fields"]) == 8
                for group in profiles.values()
                for profile in group
            )
        )
        self.assertEqual(
            set(range(2, 14)) | {15, 16, 17},
            {item["selector"] for item in profiles["persisted_default"]},
        )
        self.assertEqual(
            {0, 1, 2, 3, 4, 5, 6, 10, 12, 16, 17},
            {item["selector"] for item in profiles["active_sort_render_6"]},
        )
        self.assertEqual(
            set(range(18)),
            {
                item["selector"]
                for item in profiles["active_sort_render_8_persisted_fallback"]
            },
        )

    def test_all_profiles_preserve_tertiary_key_and_bpm_metadata(self) -> None:
        for profiles in self.audit["profiles"].values():
            for profile in profiles:
                self.assertEqual(
                    {"12": 5001, "13": 6, "14": "Am", "15": 12000},
                    {
                        index: profile["field_values"][index]
                        for index in ("12", "13", "14", "15")
                    },
                )

    def test_cached_composites_and_dynamic_bpm_are_exact(self) -> None:
        profiles = self.audit["profiles"]
        persisted = {item["name"]: item for item in profiles["persisted_default"]}
        active = {item["name"]: item for item in profiles["active_sort_render_6"]}
        explicit = {item["case_id"]: item for item in profiles["explicit_render_8"]}

        for source in (persisted, active):
            self.assertEqual("bpm-key", source["bpm"]["text_shape"])
            self.assertEqual("key-bpm", source["key"]["text_shape"])
        self.assertEqual("empty", explicit["override-04"]["text_shape"])
        self.assertEqual("key-bpm", explicit["override-12"]["text_shape"])

        comparisons = self.audit["comparisons"]["persisted_vs_explicit_override"]
        self.assertEqual(
            [("bpm", [5])],
            [
                (item["name"], item["differing_fields"])
                for item in comparisons
                if item["differing_fields"]
            ],
        )
        bpm = next(item for item in comparisons if item["name"] == "bpm")
        self.assertEqual(
            {str(content_id): [5] for content_id in range(10001, 10009)},
            bpm["all_track_differences"],
        )
        self.assertTrue(
            all(
                not item["all_track_differences"]
                for item in comparisons
                if item["name"] != "bpm"
            )
        )

    def test_active_sort_argument_zero_is_path_dependent(self) -> None:
        comparisons = self.audit["comparisons"]["persisted_vs_active_sort_render_6"]
        self.assertEqual(
            {"artist", "album", "genre", "label", "key", "date-added"},
            {
                item["name"]
                for item in comparisons
                if item["differing_fields"] == [0]
            },
        )
        self.assertTrue(
            all(item["differing_fields"] in ([], [0]) for item in comparisons)
        )
        self.assertTrue(
            all(
                fields == [0]
                for item in comparisons
                for fields in item["all_track_differences"].values()
            )
        )
        album = next(item for item in comparisons if item["name"] == "album")
        self.assertNotIn("10007", album["all_track_differences"])

    def test_eight_argument_persisted_fallback_reconciles_cached_type(self) -> None:
        fallback = {
            item["selector"]: item
            for item in self.audit["profiles"][
                "active_sort_render_8_persisted_fallback"
            ]
        }

        self.assertEqual("key-bpm", fallback[0]["text_shape"])
        self.assertEqual("key-bpm", fallback[12]["text_shape"])
        self.assertTrue(
            all(
                profile["text_shape"] == "single"
                for selector, profile in fallback.items()
                if selector not in {0, 12}
            )
        )
        self.assertTrue(
            all(
                profile["field_values"]["6"] == 0x0F04
                for profile in fallback.values()
            )
        )
        self.assertEqual(5001, fallback[0]["field_values"]["0"])
        self.assertEqual(14, fallback[12]["field_values"]["0"])
        self.assertTrue(
            all(
                profile["field_values"]["0"] == 5001
                for selector, profile in fallback.items()
                if selector not in {0, 12}
            )
        )

        comparisons = self.audit["comparisons"][
            "active_render_6_vs_render_8_persisted_fallback"
        ]
        self.assertEqual(
            {"default", "key"},
            {
                item["name"]
                for item in comparisons
                if not item["all_track_differences"]
            },
        )
        self.assertTrue(
            all(
                item["differing_fields"] == [0, 5, 6]
                for item in comparisons
                if item["name"] not in {"default", "key"}
            )
        )
        self.assertTrue(
            all(
                fields == [0, 5, 6]
                for item in comparisons
                if item["name"] not in {"default", "key"}
                for fields in item["all_track_differences"].values()
            )
        )

    def test_documentation_links_the_joined_authority(self) -> None:
        for name in (
            "docs/SECONDARY_COLUMNS.md",
            "docs/SECONDARY_COLUMN_ORACLE.md",
            "docs/PROTOCOL_REFERENCE.md",
        ):
            document = (ROOT / name).read_text()
            self.assertIn("secondary-column-semantics.json", document)
            self.assertIn("63", document)
            self.assertIn("504", document)
            self.assertIn("BPM alone", document)


if __name__ == "__main__":
    unittest.main()
