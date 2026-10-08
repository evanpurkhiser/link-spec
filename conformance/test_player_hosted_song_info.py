import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
AUDIT = ROOT / "data/static-analysis/player-hosted-song-info.json"
GENERATOR = ROOT / "tools/audit_player_hosted_song_info.py"


class PlayerHostedSongInfoTests(unittest.TestCase):
    def setUp(self) -> None:
        self.audit = json.loads(AUDIT.read_text())

    def test_audit_regenerates_byte_identically(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "audit.json"
            subprocess.run(
                [sys.executable, GENERATOR, "--output", output],
                cwd=ROOT,
                check=True,
            )
            self.assertEqual(AUDIT.read_bytes(), output.read_bytes())

    def test_all_four_role_specific_requests_are_distinguished(self) -> None:
        requests = {item["kind"]: item for item in self.audit["requests"]}
        self.assertEqual({"0x2202", "0x2302", "0x2402", "0x2502"}, requests.keys())
        self.assertIn("types 2 and 5", requests["0x2202"]["player_server"])
        self.assertIn("six rows", requests["0x2302"]["player_server"])
        self.assertEqual("0x4802 with a scalar plus length/blob outputs", requests["0x2402"]["client_reply"])
        self.assertIsNone(requests["0x2502"]["client_reply"])
        self.assertTrue(
            all("0x4003" in item["rekordbox_7_2_19"] for item in requests.values())
        )

    def test_decode_and_length_contracts_are_cross_generation(self) -> None:
        matrix = self.audit["generation_matrix"]
        self.assertEqual(
            ["XDJ-RX", "XDJ-RR", "XDJ-RX2", "XDJ-XZ", "XDJ-RX3"],
            [row["device"] for row in matrix],
        )
        for row in matrix:
            self.assertIn("0x4802", row["0x2402_client"])
            self.assertIn("unsupported stub", row["0x2402_server"])
            self.assertIn("one-way", row["0x2502_client"])
            self.assertIn("unsupported stub", row["0x2502_server"])

    def test_newer_generations_remain_vocabulary_only(self) -> None:
        matrix = self.audit["vocabulary_only_matrix"]
        self.assertEqual(
            ["CDJ-3000", "XDJ-AZ", "OMNIS-DUO", "CDJ-1500X"],
            [row["device"] for row in matrix],
        )
        for row in matrix:
            self.assertEqual(
                ["0x2402", "0x2502", "0x4802"], row["format_table_kinds"]
            )
            self.assertIn("computed or omitted", row["boundary"])

    def test_newer_generation_whole_tree_literal_boundary_is_explicit(self) -> None:
        audits = self.audit["newer_literal_audit"]
        self.assertEqual(
            {
                "CDJ-3000": (3289, 8),
                "XDJ-AZ": (7857, 8),
                "OMNIS-DUO": (7236, 7),
                "CDJ-1500X": (8480, 6),
            },
            {
                row["device"]: (
                    row["c_source_count"],
                    sum(
                        len(entries)
                        for entries in row["exact_literal_occurrences"].values()
                    ),
                )
                for row in audits
            },
        )
        for row in audits:
            self.assertEqual(
                {"0x2402": [6, 6], "0x2502": [6, 6, 6]},
                row["request_parameter_tags"],
            )
            self.assertEqual(
                {"command-name-table", "parameter-format-table"},
                set(row["occurrence_file_roles"].values()),
            )
            self.assertIn("no literal client caller", row["result"])
            self.assertIn("computed command values", row["boundary"])

    def test_protocol_documents_preserve_the_role_boundary(self) -> None:
        for name in (
            "SONG_INFO_SIBLINGS_ORACLE.md",
            "LINK_EXPORT_REQUEST_VOCABULARY.md",
            "REKORDBOX_RESEARCH_GAPS.md",
        ):
            text = (ROOT / name).read_text()
            self.assertIn("player-hosted-song-info.json", text)
            self.assertIn("0x4802", text)
            self.assertIn("register track length", text)


if __name__ == "__main__":
    unittest.main()
