import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
VARIANTS = (
    "artist",
    "album",
    "bpm",
    "rating",
    "genre",
    "comment",
    "time",
    "remixer",
    "label",
    "original-artist",
    "key",
    "bitrate",
    "color",
    "play-count",
    "date-added",
)


class SecondaryLegacyMatrixTests(unittest.TestCase):
    def test_every_persisted_secondary_has_a_legacy_declaration(self) -> None:
        for variant in VARIANTS:
            extended = json.loads(
                (ROOT / f"suites/generated/secondary-{variant}.json").read_text()
            )
            legacy = json.loads(
                (ROOT / f"suites/generated/secondary-{variant}-legacy.json").read_text()
            )
            self.assertEqual("extended", extended["defaults"]["setup"])
            self.assertEqual("legacy", legacy["defaults"]["setup"])
            self.assertEqual(extended["fixture_variant"], legacy["fixture_variant"])
            self.assertEqual(
                [case["id"] for case in extended["cases"]],
                [case["id"] for case in legacy["cases"]],
            )
            track = next(case for case in legacy["cases"] if case["id"] == "track-rows")
            self.assertEqual(12, track["expect"]["argument_count"])
            self.assertTrue(
                all(
                    int(index) < 12
                    for index in track["expect"]["row_argument_any_of"]
                )
            )

    def test_all_legacy_output_paths_are_unique(self) -> None:
        paths = [
            ROOT
            / "goldens/rekordbox-7.2.19/xdj-rx3"
            / f"secondary-{variant}-legacy.json"
            for variant in VARIANTS
        ]
        self.assertEqual(len(paths), len(set(paths)))
        self.assertTrue(all(path.name.endswith("-legacy.json") for path in paths))

    def test_complete_matrix_is_promoted_across_secondary_ledgers(self) -> None:
        summary = json.loads(
            (
                ROOT.parent
                / "data/experiments/secondary-column-legacy/summary.json"
            ).read_text()
        )
        self.assertEqual(15, summary["completed_variants"])
        self.assertEqual(15, summary["repeat_verified_variants"])
        self.assertEqual([], summary["pending"])
        self.assertTrue(summary["all_rows_exact_prefixes"])

        documents = (
            "docs/SECONDARY_COLUMN_ORACLE.md",
            "docs/SECONDARY_COLUMNS.md",
            "docs/EXPERIMENTS.md",
            "docs/REKORDBOX_RESEARCH_GAPS.md",
            "docs/CONFORMANCE_COVERAGE.md",
            "docs/SOURCES.md",
        )
        corpus = "\n".join((ROOT.parent / path).read_text() for path in documents)
        for stale_claim in (
            "legacy recording queued",
            "legacy repeat queued",
            "partial summary reports zero completed variants",
            "No legacy result is claimed",
        ):
            self.assertNotIn(stale_claim, corpus)


if __name__ == "__main__":
    unittest.main()
