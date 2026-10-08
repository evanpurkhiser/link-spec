import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VOCABULARY = ROOT / "data/static-analysis/link-export-request-vocabulary.json"
DISPATCH = ROOT / "data/static-analysis/link-export-dispatch-tables.json"
QUERY_MAP = ROOT / "data/static-analysis/menu-database-query-map.json"
PHYSICAL_TRANSCRIPT = (
    ROOT / "data/experiments/physical-rx3-session/navigation-transcript.json"
)
ALPHA_SOURCE = (
    ROOT.parent
    / "alphatheta-docs/devices/cdj-3000/application/remote-database-client.md"
)
VOCABULARY_GENERATOR = ROOT / "tools/generate_link_export_request_vocabulary.py"
DISPATCH_EXTRACTOR = ROOT / "tools/extract_link_export_dispatch_tables.py"
DISASSEMBLER = ROOT / "tools/disassemble_symbols.py"
YEAR_HANDLER = ROOT / "data/static-analysis/year-list-handler.disasm.txt"
BINARY = (
    ROOT.parent
    / "artifacts/rekordbox/7.2.19/extracted/app-root/rekordbox.app/Contents/MacOS/rekordbox"
)


def alpha_kinds():
    section = None
    kinds = []
    for line in ALPHA_SOURCE.read_text().splitlines():
        if line == "### Requests":
            section = "request"
            continue
        if line == "### Replies":
            section = "reply"
            continue
        if section is None or not line.startswith("| `"):
            continue

        fields = line.split("`")
        if len(fields) >= 4 and len(fields[1]) == 4:
            kinds.append(fields[1].upper())

    return kinds


class LinkExportRequestVocabularyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = json.loads(VOCABULARY.read_text())
        cls.commands = cls.document["commands"]
        cls.by_kind = {command["kind"]: command for command in cls.commands}
        cls.dispatch = json.loads(DISPATCH.read_text())

    def test_command_kinds_are_unique(self):
        self.assertEqual(len(self.commands), len(self.by_kind))

    def test_documented_coverage_counts_match_the_generated_ledger(self):
        protocol = (ROOT / "LINK_EXPORT_REQUEST_VOCABULARY.md").read_text()
        counts = self.document["summary"]["coverage_counts"]
        for coverage, count in counts.items():
            with self.subTest(coverage=coverage):
                self.assertIn(f"| `{coverage}` |", protocol)
                row = next(
                    line
                    for line in protocol.splitlines()
                    if line.startswith(f"| `{coverage}` |")
                )
                self.assertTrue(row.endswith(f"| {count} |"), row)

        self.assertEqual(
            self.document["summary"]["command_count"],
            sum(counts.values()),
        )

    def test_every_alpha_command_is_present_once(self):
        kinds = alpha_kinds()
        self.assertEqual(len(kinds), len(set(kinds)))
        self.assertEqual(set(kinds), set(kinds) & self.by_kind.keys())

    def test_every_physical_rx3_request_kind_is_accounted_for(self):
        transcript = json.loads(PHYSICAL_TRANSCRIPT.read_text())
        physical_kinds = {
            item["kind"].removeprefix("0x").upper()
            for item in transcript["request_kinds"]
        }
        self.assertEqual(physical_kinds, physical_kinds & self.by_kind.keys())

        report = self.by_kind["0001"]
        self.assertEqual("client-control", report["direction"])
        self.assertEqual("physical-client-control", report["coverage"])
        self.assertEqual(["CAP", "DYS", "RX3DEC"], report["evidence"])
        self.assertIn("cancel request", report["name"])
        self.assertIn("RecvFromCommTask", report["observation"])
        self.assertEqual([], report["rekordbox_route"])
        self.assertIsNone(report["reply_kind"])

    def test_every_menu_corpus_kind_is_present_once(self):
        query_map = json.loads(QUERY_MAP.read_text())
        entries = [
            (kind, family["id"], "OBS" in family["evidence"])
            for family in query_map["families"]
            for kind in family["requests"]
        ]
        kinds = [kind for kind, _, _ in entries]
        self.assertEqual(len(kinds), len(set(kinds)))
        for kind, family, observed in entries:
            with self.subTest(kind=kind):
                command = self.by_kind[kind]
                self.assertEqual(command["menu_family"], family)
                if observed:
                    self.assertEqual(
                        command["coverage"],
                        "real-rekordbox-menu-oracle",
                    )
                else:
                    self.assertNotEqual(
                        command["coverage"],
                        "real-rekordbox-menu-oracle",
                    )

    def test_every_exact_static_kind_is_present_once(self):
        kinds = {
            entry["request_kind"]
            for entry in self.dispatch["direct_dispatch"]
        }
        kinds.update(
            entry["key"]
            for table in self.dispatch["tables"]
            for entry in table["entries"]
            if len(entry["key"]) == 4
        )
        self.assertEqual(kinds, kinds & self.by_kind.keys())

    def test_top_level_routing_rejections_are_explicit(self):
        for kind in ("2006", "2106", "2206", "3E03", "3F03"):
            with self.subTest(kind=kind):
                command = self.by_kind[kind]
                self.assertEqual(command["coverage"], "rekordbox-static-rejected")
                self.assertTrue(command["rejection_reason"])

        self.assertEqual(
            self.by_kind["2006"]["rekordbox_route"],
            [
                "PSvDBMain::OnMAnlzClientCmd",
                "unsupported-low-byte",
                "PSvDBMain::OnUnknownClientCmd",
            ],
        )
        self.assertEqual(
            self.by_kind["3E03"]["rekordbox_route"],
            [
                "PSvDBMain::OnOtherClientCmd",
                "PSvDBMain::OnOtherCmd",
                "PSvDBMain::OnUnknownClientCmd",
            ],
        )

    def test_every_named_request_has_terminal_rekordbox_evidence(self):
        source_only = {
            command["kind"]
            for command in self.commands
            if command["coverage"] == "source-vocabulary-only"
        }

        self.assertEqual(source_only, set())

    def test_unknown_top_level_classes_return_4003(self):
        for kind in (
            "0100",
            "5000",
            "5001",
            "5002",
            "5003",
            "5100",
            "5101",
            "5102",
            "5103",
            "5202",
            "6100",
        ):
            with self.subTest(kind=kind):
                command = self.by_kind[kind]
                self.assertEqual(command["coverage"], "rekordbox-static-rejected")
                self.assertEqual(
                    command["rekordbox_route"],
                    ["PSvDBMain::OnClientReq", "PSvDBMain::OnUnknownClientCmd"],
                )
                self.assertEqual(command["reply_kind"], "4003")

    def test_stock_date_requests_share_the_year_handler_rejection(self):
        year_table = next(
            table for table in self.dispatch["tables"] if table["id"] == "year-high-byte"
        )
        self.assertEqual(
            [entry["key"] for entry in year_table["entries"]],
            [f"{0x1008 + index * 0x100:04X}" for index in range(11)],
        )

        for kind in ("1308", "1408", "1508", "1608"):
            with self.subTest(kind=kind):
                command = self.by_kind[kind]
                self.assertEqual(command["coverage"], "rekordbox-static-rejected")
                self.assertEqual(
                    command["rekordbox_route"],
                    [
                        "PSvDBMain::OnListClientCmd",
                        "PSvDBMain::OnYearListCmd",
                        "PSvDBMain::OnUnknownClientCmd",
                    ],
                )
                self.assertEqual(command["reply_kind"], "4003")

    def test_year_handler_disassembly_is_byte_reproducible(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / YEAR_HANDLER.name
            subprocess.run(
                [
                    sys.executable,
                    str(DISASSEMBLER),
                    str(BINARY),
                    "OnYearListCmd",
                    "--output",
                    str(output),
                ],
                cwd=ROOT,
                check=True,
                capture_output=True,
            )
            self.assertEqual(output.read_bytes(), YEAR_HANDLER.read_bytes())

    def test_protocol_docs_distinguish_rejected_commands_from_live_queries(self):
        protocol = (ROOT / "PROTOCOL_REFERENCE.md").read_text()
        queries = (ROOT / "DATABASE_QUERIES.md").read_text()
        gaps = (ROOT / "REKORDBOX_RESEARCH_GAPS.md").read_text()

        for fragment in (
            "supported `StockDate` browser is exclusively `1708..1a08`",
            "all nine `5000..5202`",
            "Provider-backed rows can",
            "admission is independent of login state",
        ):
            self.assertIn(fragment, protocol)
        self.assertIn("Stock Year client names `1308..1608`", queries)
        self.assertIn("Provider browsers `5000..5202`; 64-bit track ID `6100`", queries)
        self.assertIn("Production-shaped path matrix", gaps)

    def test_live_menu_commands_retain_static_routes(self):
        self.assertEqual(
            self.by_kind["1011"]["rekordbox_route"],
            ["PSvDBMain::OnListClientCmd", "PSvDBMain::OnBitrateListCmd"],
        )
        self.assertEqual(
            self.by_kind["2001"]["rekordbox_route"],
            ["PSvDBMain::OnMAnlzClientCmd", "PSvDBMain::OnCueBnkCmd"],
        )
        self.assertEqual(
            self.by_kind["3000"]["rekordbox_route"],
            [
                "PSvDBMain::OnOtherClientCmd",
                "PSvDBMain::OnListBuffCmd",
                "PSvDBMain::GetListBufContents",
            ],
        )
        self.assertIn("outside list-low-byte", self.by_kind["1018"]["rejection_reason"])

    def test_analysis_dispatch_and_replies_are_exact(self):
        expected = {
            "2004": ("PSvDBMain::GetWave", "4402"),
            "2104": ("PSvDBMain::GetUsbCue", "4702"),
            "2204": ("PSvDBMain::GetQtzInf", "4602"),
            "2504": ("PSvDBMain::GetVbrInf", "4502"),
            "2804": ("PSvDBMain::GetQtzInf", "4000"),
            "2904": ("PSvDBMain::LoadParWav", "4A02"),
            "2A04": ("PSvDBMain::LoadKeyInf", "4C02"),
            "2B04": ("PSvDBMain::GetUsbCueExt", "4E02"),
            "2C04": ("PSvDBMain::GetSpecifiedAtomInfo", "4F02"),
            "2D04": ("PSvDBMain::GetSpecifiedAtomInfo", "4F02"),
        }
        for kind, (target, reply) in expected.items():
            with self.subTest(kind=kind):
                command = self.by_kind[kind]
                self.assertEqual(command["rekordbox_target"], target)
                self.assertEqual(command["reply_kind"], reply)

        self.assertEqual(
            self.by_kind["2003"]["rekordbox_route"],
            [
                "PSvDBMain::OnMAnlzClientCmd",
                "PSvDBMain::OnImgCmd",
                "database-interface vtable +0x190",
            ],
        )

    def test_bitrate_root_is_not_mislabeled_as_folder(self):
        command = self.by_kind["1011"]
        self.assertEqual(command["name"], "CMD_BITRATE_ROOT")
        self.assertNotIn("folder", command["name"].lower())

    def test_summary_counts_match_commands(self):
        summary = self.document["summary"]
        self.assertEqual(summary["command_count"], len(self.commands))
        self.assertEqual(summary["alpha_command_count"], len(alpha_kinds()))
        for field in ("direction_counts", "coverage_counts"):
            key = field.removesuffix("_counts")
            actual = {}
            for command in self.commands:
                value = command[key]
                actual[value] = actual.get(value, 0) + 1
            self.assertEqual(summary[field], actual)

    def test_vocabulary_regeneration_is_byte_identical(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / VOCABULARY.name
            subprocess.run(
                ["python3", str(VOCABULARY_GENERATOR), "--output", str(output)],
                cwd=ROOT,
                check=True,
                capture_output=True,
            )
            self.assertEqual(output.read_bytes(), VOCABULARY.read_bytes())

    def test_dispatch_regeneration_is_byte_identical(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / DISPATCH.name
            subprocess.run(
                ["python3", str(DISPATCH_EXTRACTOR), "--output", str(output)],
                cwd=ROOT,
                check=True,
                capture_output=True,
            )
            self.assertEqual(output.read_bytes(), DISPATCH.read_bytes())


if __name__ == "__main__":
    unittest.main()
