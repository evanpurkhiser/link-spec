import json
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent
TARGET = ROOT / "suites/generated/render-arity-boundaries.json"
TARGET_GOLDEN = (
    ROOT
    / "goldens/rekordbox-7.2.19/xdj-rx3/render-arity-boundaries.json"
)
GOLDENS = ROOT / "goldens"
VISIBLE_SORTS = (0, 1, 2, 3, 4, 5, 6, 10, 12, 17, 16)


class RenderArityBoundaryTests(unittest.TestCase):
    def test_existing_track_goldens_do_not_cover_boundary_arities(self) -> None:
        counts = Counter()
        for path in sorted(GOLDENS.rglob("*.json")):
            if path == TARGET_GOLDEN:
                continue

            golden = json.loads(path.read_text())
            for case in golden.get("behavior", {}).get("cases", []):
                if case.get("request", {}).get("kind") != 0x1004:
                    continue
                for page in case.get("pages", []):
                    counts[len(page.get("arguments", []))] += 1

        self.assertTrue(counts)
        self.assertTrue(set(counts).issubset({5, 6, 7, 8}))
        self.assertFalse(set(counts) & ({3, 4} | set(range(9, 33))))

    def test_suite_exhausts_meaningful_argument_counts_through_wire_limit(self) -> None:
        suite = json.loads(TARGET.read_text())
        self.assertEqual("track-render-arity-boundaries", suite["name"])
        self.assertEqual(70, len(suite["cases"]))

        default_arities = []
        boundary_pairs = []
        for case in suite["cases"]:
            self.assertTrue(case["fresh_connection"])
            self.assertEqual(8, case["page_size"])
            self.assertEqual("any", case["expect"]["outcome"])
            arity = 3 + len(case["render_arguments"])
            sort_id = case["arguments"][1]["number"]
            self.assertGreaterEqual(arity, 3)
            self.assertLessEqual(arity, 32)
            if sort_id == 0:
                default_arities.append(arity)
            else:
                boundary_pairs.append((arity, sort_id))

        self.assertEqual(list(range(3, 33)), default_arities)
        self.assertEqual(
            [(arity, sort_id) for arity in (3, 4, 9, 32) for sort_id in VISIBLE_SORTS[1:]],
            boundary_pairs,
        )

    def test_overlong_arguments_are_distinct_sentinels(self) -> None:
        suite = json.loads(TARGET.read_text())
        cases = {case["id"]: case for case in suite["cases"]}
        arity_32 = cases["default-arity-32"]["render_arguments"]
        self.assertEqual([0, "$total", 12, 1, 0], arity_32[:5])
        self.assertEqual("0x90000009", arity_32[5])
        self.assertEqual("0x90000020", arity_32[-1])
        self.assertEqual(29, len(arity_32))

    def test_docs_preserve_pending_authority_boundary(self) -> None:
        documents = {
            "PROTOCOL_REFERENCE.md": "Track render arity boundary sweep",
            "SECONDARY_COLUMNS.md": "render-arity-boundaries.json",
            "CONFORMANCE_COVERAGE.md": "Track render arities 3 through 32",
            "REKORDBOX_RESEARCH_GAPS.md": "render-arity-boundaries",
            "SOURCES.md": "Track render arity boundaries",
        }
        for name, fragment in documents.items():
            text = " ".join((ROOT.parent / name).read_text().split())
            with self.subTest(document=name):
                self.assertIn(fragment, text)


if __name__ == "__main__":
    unittest.main()
