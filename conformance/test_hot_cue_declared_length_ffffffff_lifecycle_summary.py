import unittest

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import summarize_hot_cue_declared_length_ffffffff_lifecycle as summary


class HotCueDeclaredLengthFFFFFFFFLifecycleSummaryTests(unittest.TestCase):
    def test_baseline_record_is_the_pristine_124_byte_getter(self) -> None:
        self.assertEqual(
            "94bf967af4316fbeb78e3862ce09de2cfc57c616ed09ca882abd7c339b2589d0",
            summary.baseline_record_sha256(),
        )

    def test_message_signatures_preserve_echo_and_status(self) -> None:
        self.assertEqual(
            "0100",
            summary.message_signature({"kind": 0x0100, "arguments": []}),
        )
        self.assertEqual(
            "4e02-echo-2401-status-50-count-0",
            summary.message_signature(
                {
                    "kind": 0x4E02,
                    "arguments": [
                        {"type": "number", "value": 0x2401},
                        {"type": "number", "value": 50},
                        {"type": "number", "value": 0},
                        {"type": "blob", "hex": ""},
                        {"type": "number", "value": 0},
                    ],
                }
            ),
        )

    def test_getter_record_ignores_delayed_setter_reply(self) -> None:
        case = {
            "raw_response": {
                "messages": [
                    {
                        "kind": 0x4E02,
                        "arguments": [
                            {"type": "number", "value": 0x2401},
                            {"type": "number", "value": 50},
                            {"type": "number", "value": 0},
                            {"type": "blob", "hex": ""},
                            {"type": "number", "value": 0},
                        ],
                    }
                ]
            }
        }
        self.assertIsNone(summary.getter_record(case))

    def test_case_signature_distinguishes_immediate_status_reply(self) -> None:
        case = {
            "outcome": "raw_reply",
            "raw_response": {
                "messages": [
                    {
                        "kind": 0x4E02,
                        "arguments": [
                            {"type": "number", "value": 0x2401},
                            {"type": "number", "value": 50},
                            {"type": "number", "value": 0},
                            {"type": "blob", "hex": ""},
                            {"type": "number", "value": 0},
                        ],
                    }
                ]
            },
        }
        self.assertEqual(
            "4e02-echo-2401-status-50-count-0",
            summary.case_signature(case),
        )

    def test_raw_transaction_distinguishes_generic_and_correlated_replies(self) -> None:
        self.assertEqual(
            0xFFFFFFFE,
            summary.first_transaction(
                {
                    "raw_response": {
                        "raw_hex": "11872349ae11fffffffe1001000f001400000000"
                    }
                }
            ),
        )
        self.assertEqual(
            1,
            summary.first_transaction(
                {
                    "raw_response": {
                        "raw_hex": "11872349ae1100000001104e020f051400000005"
                    }
                }
            ),
        )


if __name__ == "__main__":
    unittest.main()
