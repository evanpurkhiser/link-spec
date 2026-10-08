import json
import struct
import unittest
from collections import Counter
from pathlib import Path

import generate_hot_cue_legacy_setter_parser_suites as parser_suites


class HotCueLegacySetterParserSuiteTests(unittest.TestCase):
    def test_oracle_describes_completed_process_isolated_matrix(self) -> None:
        oracle = (
            Path(__file__).resolve().parent.parent / "HOT_CUE_BANK_ORACLE.md"
        ).read_text()

        self.assertIn("completed live boundary matrix", oracle)
        self.assertIn("All 57 variants repeat", oracle)
        self.assertNotIn("live boundary matrix therefore needs", oracle)

    def test_static_setter_fixed_word_map_matches_documented_offsets(self) -> None:
        root = Path(__file__).resolve().parent.parent
        disassembly = (
            root / "data/static-analysis/hot-cue-bank-legacy-setter.disasm.txt"
        ).read_text()
        setter = disassembly.split("\n## ", 1)[0]
        properties = {
            0x0C: "InFrame",
            0x10: "OutFrame",
            0x14: "InMpegFrame",
            0x18: "OutMpegFrame",
            0x1C: "InMpegAbs",
            0x20: "OutMpegAbs",
        }

        self.assertIn("mov       esi, dword ptr [r15 + 4]", setter)
        self.assertNotIn("dword ptr [r15 + 8]", setter)
        for offset, property_name in properties.items():
            with self.subTest(word=offset // 4, property=property_name):
                self.assertIn(f"; '{property_name}'", setter)
                self.assertIn(
                    f"mov       esi, dword ptr [r15 + 0x{offset:x}]",
                    setter,
                )

        self.assertIn("mov       esi, 0xffffffff", setter)
        self.assertIn("; 'Color'", setter)

    def test_identical_request_history_declaration(self) -> None:
        conformance = Path(__file__).resolve().parent
        declaration = json.loads(
            (
                conformance
                / "data/hot-cue-legacy-identical-request-history.json"
            ).read_text()
        )
        request_phases = [
            phase for phase in declaration["phases"] if phase["action"] == "request"
        ]
        canonical = [
            phase for phase in request_phases if "canonical" in phase["id"]
        ]

        self.assertEqual(2, declaration["cycles"])
        self.assertEqual(6, len(request_phases))
        self.assertEqual(4, len(canonical))
        self.assertEqual(
            1,
            sum(
                phase["action"] == "isolated-vm-restart"
                for phase in declaration["phases"]
            ),
        )
        self.assertTrue(
            all((conformance / phase["suite"]).is_file() for phase in request_phases)
        )

    def test_matrix_covers_all_declared_boundaries(self) -> None:
        variants = parser_suites.variants()
        counts = Counter(variant.axis for variant in variants)

        self.assertEqual(57, len(variants))
        self.assertEqual(
            {
                "actual-cue-length": 9,
                "declared-cue-length": 6,
                "flag": 12,
                "actual-extension-length": 6,
                "declared-extension-length": 6,
                "content-id": 4,
                "fixed-word": 14,
            },
            counts,
        )
        self.assertEqual(len(variants), len({variant.id for variant in variants}))

    def test_every_suite_is_a_single_process_isolated_setter(self) -> None:
        for variant in parser_suites.variants():
            with self.subTest(variant=variant.id):
                suite = parser_suites.suite(variant)
                probe = suite["parser_probe"]
                self.assertEqual("fixture-reset-and-restart", suite["repeat_strategy"])
                self.assertTrue(probe["process_isolation_required"])
                self.assertTrue(probe["post_survival_getter_required"])
                self.assertTrue(probe["live_database_capture_required"])
                self.assertEqual(1, len(suite["cases"]))
                self.assertEqual("0x2201", suite["cases"][0]["request_kind"])
                self.assertEqual("any", suite["cases"][0]["expect"]["outcome"])

    def test_length_axes_change_only_the_intended_lengths(self) -> None:
        for variant in parser_suites.variants():
            if "length" not in variant.axis:
                continue
            with self.subTest(variant=variant.id):
                suite = parser_suites.suite(variant)
                probe = suite["parser_probe"]
                arguments = suite["cases"][0]["arguments"]
                self.assertEqual(probe["declared_cue_length"], arguments[2]["number"])
                self.assertEqual(probe["actual_cue_length"], len(bytes.fromhex(arguments[3]["blob_hex"])))
                self.assertEqual(probe["declared_extension_length"], arguments[4]["number"])
                self.assertEqual(probe["actual_extension_length"], len(bytes.fromhex(arguments[5]["blob_hex"])))

    def test_flag_axis_covers_exact_static_interval_boundaries(self) -> None:
        values = [
            variant.value
            for variant in parser_suites.variants()
            if variant.axis == "flag"
        ]
        self.assertEqual(
            [
                0,
                0x0003FFFF,
                0x00040000,
                0x00040001,
                0x00040100,
                0x0004FFFF,
                0x00050000,
                0x0005FFFF,
                0x00060000,
                0x0006FFFF,
                0x00070000,
                0xFFFFFFFF,
            ],
            values,
        )

    def test_fixed_word_probes_preserve_other_words(self) -> None:
        canonical = parser_suites.payloads(
            parser_suites.Variant("control", "content-id", 10001)
        )[0]
        canonical_words = struct.unpack("<9I", canonical)
        for variant in parser_suites.variants():
            if variant.axis != "fixed-word":
                continue
            with self.subTest(variant=variant.id):
                cue, extension = parser_suites.payloads(variant)
                words = struct.unpack("<9I", cue)
                self.assertEqual(8, len(extension))
                self.assertEqual(variant.value, words[variant.word])
                for index in range(9):
                    if index != variant.word:
                        self.assertEqual(canonical_words[index], words[index])

    def test_generated_manifest_matches_generator(self) -> None:
        parser_suites.main()
        matrix = json.loads(
            (parser_suites.ROOT / "data/hot-cue-legacy-setter-parser-matrix.json").read_text()
        )
        self.assertEqual(1, matrix["format"])
        self.assertEqual(57, len(matrix["variants"]))
        for item, variant in zip(
            matrix["variants"], parser_suites.variants(), strict=True
        ):
            self.assertEqual(variant.id, item["id"])
            self.assertTrue((parser_suites.ROOT / item["suite"]).is_file())

    def test_post_survival_getter_reads_all_mutable_slots(self) -> None:
        suite = parser_suites.getter_suite()
        self.assertEqual(1, len(suite["cases"]))
        case = suite["cases"][0]
        self.assertEqual("0x2301", case["request_kind"])
        self.assertEqual(6, case["arguments"][2]["number"])
        self.assertEqual("any", case["expect"]["outcome"])


if __name__ == "__main__":
    unittest.main()
