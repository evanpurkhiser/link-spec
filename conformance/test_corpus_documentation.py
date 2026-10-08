import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SUITES = ROOT / "conformance/suites"
DOCUMENTS = (ROOT / "docs/CONFORMANCE.md", ROOT / "docs/CONFORMANCE_COVERAGE.md")


class CorpusDocumentationTests(unittest.TestCase):
    def test_readme_indexes_every_document_once(self) -> None:
        readme = (ROOT / "README.md").read_text()
        documents = readme.split("## Documents", 1)[1].split(
            "## Evidence labels", 1
        )[0]
        paths = [
            ROOT / "CONTRIBUTING.md",
            *sorted((ROOT / "docs").glob("*.md")),
        ]

        for path in paths:
            relative = path.relative_to(ROOT)
            with self.subTest(document=relative):
                self.assertEqual(1, documents.count(f"- `{relative}`"))

    def test_documented_totals_match_recursive_suite_inventory(self) -> None:
        suite_paths = sorted(SUITES.rglob("*.json"))
        case_count = 0

        for path in suite_paths:
            document = json.loads(path.read_text())
            cases = document.get("cases")

            self.assertIsInstance(cases, list, path)
            self.assertTrue(cases, path)
            case_count += len(cases)

        statements = (
            f"{case_count:,} declarations across {len(suite_paths):,} suite files",
            f"{case_count:,} case declarations in {len(suite_paths):,} suite files",
        )

        for path, statement in zip(DOCUMENTS, statements, strict=True):
            with self.subTest(document=path.name):
                self.assertIn(statement, path.read_text())

    def test_completed_experiments_are_not_described_as_pending(self) -> None:
        summaries = (
            ROOT / "data/experiments/hot-cue-bank/extended-setter-fields/summary.json",
            ROOT / "data/experiments/hot-cue-bank/extended-setter-seek/summary.json",
        )
        for path in summaries:
            with self.subTest(summary=path):
                self.assertTrue(json.loads(path.read_text())["complete"])

        sources = (ROOT / "docs/SOURCES.md").read_text()
        cdj_readme = (
            ROOT / "data/experiments/device-status/cdj-2000nexus/README.md"
        ).read_text()
        notification_readme = (
            ROOT
            / "data/experiments/hot-cue-bank/setter-notifications/README.md"
        ).read_text()

        self.assertNotIn("pending evidence is explicit", sources)
        self.assertNotIn("No live result is claimed yet", cdj_readme)
        self.assertNotIn("Pending wire capture", notification_readme)
        self.assertIn("13 variants and 249 cases", cdj_readme)
        self.assertIn("no Link Export serializer", notification_readme)

    def test_sources_rx3_golden_totals_match_recursive_inventory(self) -> None:
        root = ROOT / "conformance/goldens/rekordbox-7.2.19/xdj-rx3"
        paths = sorted(root.rglob("*.json"))
        case_count = sum(
            len(json.loads(path.read_text())["behavior"]["cases"])
            for path in paths
        )
        statement = (
            f"{len(paths):,} real XDJ-RX3 golden files containing "
            f"{case_count:,} cases"
        )

        self.assertIn(statement, (ROOT / "docs/SOURCES.md").read_text())


if __name__ == "__main__":
    unittest.main()
