from __future__ import annotations

import json
import unittest
from pathlib import Path

import protocol_runner
from remote_db import MENU_HEADER, SETUP, SETUP_TXID, Argument, Message, is_setup_reply


ROOT = Path(__file__).resolve().parent


class RemoteDatabaseCodecTest(unittest.TestCase):
    def test_message_round_trip_preserves_argument_types(self) -> None:
        message = Message(
            7,
            0x4101,
            (
                Argument.number(0xFFFFFFFF),
                Argument.string("A🙂"),
                Argument.blob(b"\x00\xff"),
            ),
        )

        decoded, used = Message.decode(message.encode())

        self.assertEqual(message, decoded)
        self.assertEqual(len(message.encode()), used)

    def test_decode_all_retains_a_partial_trailing_message(self) -> None:
        first = Message(1, 0x4000, (Argument.number(2),)).encode()
        second = Message(2, 0x4001, (Argument.number(3),)).encode()

        messages, used = Message.decode_all(first + second[:-2])

        self.assertEqual([1], [message.transaction for message in messages])
        self.assertEqual(len(first), used)

    def test_empty_blob_is_declared_without_a_field(self) -> None:
        message = Message(
            1, 0x4002, (Argument.number(0), Argument.blob(b""))
        )

        decoded, _ = Message.decode(message.encode())

        self.assertEqual(message, decoded)

    def test_fixed_tag_slots_round_trip(self) -> None:
        message = Message(1, 0x1000, (Argument.number(1),))

        decoded, used = Message.decode(message.encode(tag_slots=12))

        self.assertEqual(message, decoded)
        self.assertEqual(len(message.encode(tag_slots=12)), used)

    def test_setup_reply_shapes_cover_both_sessions(self) -> None:
        extended = Message(
            SETUP_TXID, SETUP, (Argument.number(17), Argument.number(20))
        )
        legacy = Message(
            SETUP_TXID,
            MENU_HEADER,
            (Argument.number(0), Argument.number(17)),
        )

        self.assertTrue(is_setup_reply("extended", extended))
        self.assertTrue(is_setup_reply("legacy", legacy))
        self.assertFalse(is_setup_reply("extended", legacy))


class ProtocolRunnerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.defaults = {
            "device": 1,
            "context": "0x01010301",
            "sort": 0,
            "root_capabilities": "0x05cfffff",
            "setup": "extended",
            "page_size": 64,
            "render_arguments": [0, "$total", 12, 1, 0],
        }
        self.manifest = {
            "fixture_version": 1,
            "profile": "full",
            "database_sha256": "abc",
            "ids": {"key.am": 5001},
        }

    def test_checked_in_suites_validate(self) -> None:
        paths = sorted((ROOT / "suites").rglob("*.json"))
        self.assertTrue(paths)

        for path in paths:
            protocol_runner.validate_suite(json.loads(path.read_text()), path)

    def test_symbols_resolve_from_defaults_manifest_and_total(self) -> None:
        self.assertEqual(
            0x01010301,
            protocol_runner.resolve_number(
                "$context", self.defaults, self.manifest
            ),
        )
        self.assertEqual(
            5001,
            protocol_runner.resolve_number(
                "$fixture.key.am", self.defaults, self.manifest
            ),
        )
        self.assertEqual(
            8,
            protocol_runner.resolve_number(
                "$total", self.defaults, self.manifest, 8
            ),
        )

    def test_utf16_byte_length_includes_nul(self) -> None:
        argument = protocol_runner.resolve_argument(
            {"utf16_bytes": "A🙂"}, self.defaults, self.manifest, {}
        )

        self.assertEqual(8, argument.value)

    def test_case_item_reads_a_prior_row_argument(self) -> None:
        prior = {
            "root": {
                "rows": [
                    {
                        "arguments": [
                            {"type": "number", "value": 0},
                            {"type": "number", "value": 99},
                        ]
                    }
                ]
            }
        }

        argument = protocol_runner.resolve_argument(
            {"case_item": {"case": "root"}},
            self.defaults,
            self.manifest,
            prior,
        )

        self.assertEqual(Argument.number(99), argument)

    def test_render_pages_are_bounded_by_page_size(self) -> None:
        requests = protocol_runner.render_requests(
            {"id": "tracks"}, self.defaults, self.manifest, 130
        )

        self.assertEqual([(0, 64), (64, 64), (128, 2)], requests)

    def test_maximum_menu_count_is_unavailable(self) -> None:
        case = {"id": "x", "expect": {"outcome": "error"}}
        rows: list[dict[str, object]] = []

        protocol_runner.assert_expectations(
            case, "error", 0xFFFFFFFF, rows, self.manifest, self.defaults
        )

    def test_semantic_differences_name_nested_fields(self) -> None:
        output: list[str] = []

        protocol_runner.collect_value_differences(
            {"rows": [{"arguments": [{"value": 7}]}]},
            {"rows": [{"arguments": [{"value": 8}]}]},
            "case[tracks]",
            output,
        )

        self.assertEqual(
            ["case[tracks].rows[0].arguments[0].value: expected 7, actual 8"],
            output,
        )

    def test_parallel_canonicalization_ignores_worker_order(self) -> None:
        first = {"id": "one", "description": "first", "outcome": "menu"}
        second = {
            "id": "two",
            "description": "second",
            "outcome": "connection_timeout",
        }

        self.assertEqual(
            protocol_runner.canonical_parallel_cases([first, second]),
            protocol_runner.canonical_parallel_cases([second, first]),
        )

    def test_case_item_selectors_are_canonicalized(self) -> None:
        suite = {
            "cases": [
                {"arguments": []},
                {
                    "arguments": [
                        {
                            "case_item": {
                                "case": "root",
                                "canonicalize": True,
                            }
                        }
                    ]
                },
            ]
        }
        dynamic = 4_143_798_526
        cases = [
            {
                "id": "root",
                "rows": [
                    {
                        "arguments": [
                            {"type": "number", "value": 0},
                            {"type": "number", "value": dynamic},
                        ]
                    }
                ],
            },
            {
                "id": "tracks",
                "request": {
                    "arguments": [{"type": "number", "value": dynamic}]
                },
                "rows": [],
            },
        ]

        normalizers = protocol_runner.canonicalize_case_item_selectors(
            suite, cases, True
        )

        self.assertEqual(0xCA5E0000, cases[0]["rows"][0]["arguments"][1]["value"])
        self.assertEqual(0xCA5E0000, cases[1]["request"]["arguments"][0]["value"])
        self.assertEqual("root", normalizers[0]["source_case"])

    def test_row_argument_expectations_accept_exact_and_allowed_values(self) -> None:
        case = {
            "id": "fields",
            "expect": {
                "outcome": "menu",
                "row_argument_values": {"12": ["$fixture.key.am", 5002]},
                "row_argument_any_of": {"10": [256, 257]},
            },
        }
        rows = []
        for key, item_type in ((5001, 256), (5002, 257)):
            arguments = [{"type": "number", "value": 0} for _ in range(13)]
            arguments[10]["value"] = item_type
            arguments[12]["value"] = key
            rows.append({"arguments": arguments})

        protocol_runner.assert_expectations(
            case, "menu", 2, rows, self.manifest, self.defaults
        )


if __name__ == "__main__":
    unittest.main()
