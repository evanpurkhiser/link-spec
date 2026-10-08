import json
import hashlib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SUITES = ROOT / "suites"
TARGET = SUITES / "generated/sort-secondary-render-6.json"
EVIDENCE = ROOT.parent / "data/experiments/sort-secondary-render-6"
GOLDEN = ROOT / "goldens/rekordbox-7.2.19/xdj-rx3/sort-secondary-render-6.json"
GOLDENS = ROOT / "goldens"
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


class SortSecondaryRender6Tests(unittest.TestCase):
    def test_historical_corpus_had_no_nondefault_sort_render_6_cross(self) -> None:
        matches = []
        for path in sorted(SUITES.rglob("*.json")):
            if path == TARGET:
                continue

            suite = json.loads(path.read_text())
            for case in suite["cases"]:
                if case["request_kind"] != "0x1004":
                    continue
                if len(effective_render_arguments(suite, case)) != 3:
                    continue

                sort = case["arguments"][1]["number"]
                if sort == "$sort":
                    sort = suite["defaults"]["sort"]
                if sort != 0:
                    matches.append((str(path.relative_to(ROOT)), case["id"], sort))

        self.assertEqual([], matches)

    def test_historical_goldens_had_no_nondefault_sort_render_6_cross(self) -> None:
        matches = []
        for path in sorted(GOLDENS.rglob("*.json")):
            if path == GOLDEN:
                continue

            golden = json.loads(path.read_text())
            for case in golden.get("behavior", {}).get("cases", []):
                request = case.get("request", {})
                arguments = request.get("arguments", [])
                if request.get("kind") != 0x1004 or len(arguments) < 2:
                    continue
                if arguments[1]["value"] == 0:
                    continue

                for page in case.get("pages", []):
                    if len(page.get("arguments", [])) == 6:
                        matches.append(
                            (
                                str(path.relative_to(ROOT)),
                                case["id"],
                                arguments[1]["value"],
                            )
                        )

        self.assertEqual([], matches)

    def test_focused_suite_crosses_every_visible_rx3_sort_with_render_6(self) -> None:
        suite = json.loads(TARGET.read_text())
        self.assertEqual("rx3-track-sort-secondary-render-6", suite["name"])
        self.assertEqual("0x01010301", suite["defaults"]["context"])
        self.assertEqual([0, "$total", 12], suite["defaults"]["render_arguments"])
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

    def test_retained_physical_rx3_track_renders_use_six_arguments_and_selector_12(self) -> None:
        pcap = EVIDENCE / "source-rx3-rekordbox-working-ap-20260927.pcap"
        self.assertEqual(
            "bee17ddfa72b093479a68c1590953ddc79629cdf43905769761c656a5149aa2b",
            hashlib.sha256(pcap.read_bytes()).hexdigest(),
        )
        messages = json.loads(
            (EVIDENCE / "physical-rx3-requests.json").read_text()
        )
        pairs = []
        for index, message in enumerate(messages[:-1]):
            if message["kind"] != 0x1004:
                continue
            if message["arguments"] != [0x0B010401, 0]:
                continue
            render = messages[index + 1]
            self.assertEqual(0x3000, render["kind"])
            pairs.append(render["arguments"])

        self.assertEqual(3, len(pairs))
        self.assertTrue(
            all(arguments == [0x0B010401, 0, 12, 0, 4342, 12] for arguments in pairs)
        )

    def test_real_rekordbox_rows_follow_active_sort_under_render_6(self) -> None:
        expected = {
            "00-default": (5001, "Am - 120.0 bpm", 0x0F04),
            "01-alphabet": (0, "Alpha One", 0x0404),
            "02-artist": (0, "Alpha Artist", 0x0704),
            "03-album": (0, "Album One", 0x0204),
            "04-bpm": (12000, "120.0 bpm - Am", 0x0D04),
            "05-rating": (0, "", 0x0A04),
            "06-genre": (0, "Fixture House", 0x0604),
            "10-label": (0, "Fixture Label One", 0x0E04),
            "12-key": (14, "Am - 120.0 bpm", 0x0F04),
            "17-date-added": (0, "2021-02-02", 0x2E04),
            "16-dj-play-count": (0, "", 0x2A04),
        }
        golden = json.loads(GOLDEN.read_text())
        cases = {case["id"]: case for case in golden["behavior"]["cases"]}
        self.assertEqual(expected.keys(), cases.keys())

        for case_id, expected_secondary in expected.items():
            case = cases[case_id]
            for page in case["pages"]:
                self.assertEqual(
                    [0, case["total"], 12],
                    [argument["value"] for argument in page["arguments"]][3:],
                )
            row = next(
                row
                for row in case["rows"]
                if row["arguments"][3]["value"] == "Alpha One"
            )
            arguments = [argument["value"] for argument in row["arguments"]]
            self.assertEqual(expected_secondary, (arguments[0], arguments[5], arguments[6]))
            self.assertEqual((5001, 6, "Am", 12000), tuple(arguments[12:16]))

        receipt = json.loads((EVIDENCE / "finalization.json").read_text())
        self.assertEqual(11, receipt["case_count"])
        self.assertEqual(88, receipt["row_count"])
        self.assertEqual(22, receipt["record_repeat_execution_count"])
        self.assertTrue(receipt["focused_tests_passed"])
        self.assertTrue(receipt["isolated_vm_stopped"])

    def test_protocol_documents_keep_the_four_column_inputs_distinct(self) -> None:
        documents = {
            "docs/SECONDARY_COLUMNS.md": (
                "not the active track sort",
                "active sort's materialized column",
                "8 arguments",
            ),
            "docs/SECONDARY_COLUMN_ORACLE.md": (
                "Active sort with RX3 six-argument rendering",
                "Arguments 12-15 remain independent content metadata",
                "physical RX3 PCAP",
            ),
            "docs/ROW_LAYOUT.md": (
                "Six-argument rendering exposes the active sort's cached right-column value",
                "eight-argument render supplies an override gate",
            ),
            "docs/SORT_AND_COLOR_ORACLE.md": (
                "Sort affects RX3 track-row presentation",
                "final argument `12`",
            ),
            "docs/KEY_NOTATION_ORACLE.md": (
                "active Key sort",
                "active BPM sort",
                "composites are preserved cached list-builder output",
            ),
            "docs/PROTOCOL_REFERENCE.md": (
                "Six-argument RX3 rendering instead preserves",
                "final value `12` does not select Key",
            ),
            "docs/LINK_EXPORT_NAVIGATION.md": (
                "Track sorting is a separate presentation input",
                "final value `12` does not select Key",
            ),
        }

        for name, fragments in documents.items():
            text = " ".join((ROOT.parent / name).read_text().split())
            for fragment in fragments:
                with self.subTest(document=name, fragment=fragment):
                    self.assertIn(fragment, text)


if __name__ == "__main__":
    unittest.main()
