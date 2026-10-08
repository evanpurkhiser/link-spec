import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SUITES = ROOT / "suites"
TARGET = SUITES / "generated/sort-secondary-render-5.json"
GOLDENS = ROOT / "goldens"
TARGET_GOLDEN = (
    GOLDENS / "rekordbox-7.2.19/xdj-rx3/sort-secondary-render-5.json"
)
SORTS = (
    (0, "00-default"),
    (1, "01-alphabet"),
    (2, "02-artist"),
    (3, "03-album"),
    (4, "04-bpm"),
    (5, "05-rating"),
    (6, "06-genre"),
    (10, "10-label"),
    (12, "12-key"),
    (17, "17-date-added"),
    (16, "16-dj-play-count"),
)


def effective_render_arguments(suite: dict, case: dict) -> list:
    return case.get("render_arguments", suite["defaults"]["render_arguments"])


class SortSecondaryRender5Tests(unittest.TestCase):
    def test_historical_corpus_has_no_nondefault_sort_render_5_cross(self) -> None:
        matches = []
        for path in sorted(SUITES.rglob("*.json")):
            if path == TARGET:
                continue

            suite = json.loads(path.read_text())
            for case in suite["cases"]:
                if case["request_kind"] != "0x1004":
                    continue
                if len(effective_render_arguments(suite, case)) != 2:
                    continue

                sort = case["arguments"][1]["number"]
                if sort == "$sort":
                    sort = suite["defaults"]["sort"]
                if sort != 0:
                    matches.append((str(path.relative_to(ROOT)), case["id"], sort))

        self.assertEqual([], matches)

    def test_historical_goldens_have_no_nondefault_sort_render_5_cross(self) -> None:
        matches = []
        for path in sorted(GOLDENS.rglob("*.json")):
            if path == TARGET_GOLDEN:
                continue

            golden = json.loads(path.read_text())
            for case in golden.get("behavior", {}).get("cases", []):
                request = case.get("request", {})
                arguments = request.get("arguments", [])
                if request.get("kind") != 0x1004 or len(arguments) < 2:
                    continue
                if arguments[1]["value"] == 0:
                    continue
                if any(len(page.get("arguments", [])) == 5 for page in case.get("pages", [])):
                    matches.append(
                        (
                            str(path.relative_to(ROOT)),
                            case["id"],
                            arguments[1]["value"],
                        )
                    )

        self.assertEqual([], matches)

    def test_suite_crosses_every_visible_rx3_sort_with_render_5(self) -> None:
        suite = json.loads(TARGET.read_text())
        self.assertEqual("rx3-track-sort-secondary-render-5", suite["name"])
        self.assertEqual("0x01010301", suite["defaults"]["context"])
        self.assertEqual([0, "$total"], suite["defaults"]["render_arguments"])
        self.assertEqual(
            list(SORTS),
            [
                (case["arguments"][1]["number"], case["id"])
                for case in suite["cases"]
            ],
        )
        for case in suite["cases"]:
            self.assertTrue(case["fresh_connection"])
            self.assertEqual(16, case["expect"]["argument_count"])

    def test_declaration_is_documented_as_pending_real_rekordbox_evidence(self) -> None:
        coverage = " ".join((ROOT.parent / "CONFORMANCE_COVERAGE.md").read_text().split())
        gaps = " ".join((ROOT.parent / "REKORDBOX_RESEARCH_GAPS.md").read_text().split())
        secondary = " ".join((ROOT.parent / "SECONDARY_COLUMNS.md").read_text().split())
        self.assertIn("active sort x five-argument track render", coverage)
        self.assertIn("sort-secondary-render-5", gaps)
        self.assertIn("five-argument active-sort cross is declared", secondary)
        protocol = " ".join((ROOT.parent / "PROTOCOL_REFERENCE.md").read_text().split())
        row_layout = " ".join((ROOT.parent / "ROW_LAYOUT.md").read_text().split())
        sources = " ".join((ROOT.parent / "SOURCES.md").read_text().split())
        self.assertIn("queued declaration, not yet an observed rule", protocol)
        self.assertIn("five-argument active-sort matrix is declared", row_layout)
        self.assertIn("Five-argument active-sort rendering", sources)


if __name__ == "__main__":
    unittest.main()
