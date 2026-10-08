import json
import struct
import sys
import tempfile
import unittest
from pathlib import Path

import generate_adjacent_payload_cue_suites as generator

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.build_hot_cue_mutation_record import build_record
from tools.summarize_adjacent_payload_cues import decode


ROOT = Path(__file__).resolve().parent
INDEX = ROOT / "data/adjacent-payload-cue-matrix.json"
BASE_SUITE = ROOT / "suites/adjacent-payload-cue-success.json"
GENERATED = ROOT / "suites/generated/adjacent-payload-cues"
FIXTURE = ROOT / "fixtures/generated/adjacent-payload-cues/manifest.json"


def argument(kind: str, value) -> dict:
    return {"type": kind, "value": value} if kind == "number" else {"type": kind, "hex": value}


class AdjacentPayloadCueTests(unittest.TestCase):
    def test_reducer_requires_repeat_equivalent_process_health(self) -> None:
        reducer = (ROOT.parent / "tools/summarize_adjacent_payload_cues.py").read_text()
        self.assertIn("validate_health_pair(", reducer)

    def test_fixture_is_encrypted_fingerprinted_and_complete(self) -> None:
        manifest = json.loads(FIXTURE.read_text())
        self.assertEqual(manifest["profile"], "adjacent-payload-cues")
        self.assertEqual(manifest["integrity"], "ok")
        self.assertEqual(manifest["track_count"], 19)
        self.assertEqual(
            manifest["database_sha256"],
            "988d092d11e446a889a2e114aac902af2133dd7adba5b42e7e75feda1800a141",
        )
        self.assertEqual(
            manifest["fixture_fingerprint"],
            "61d5b3ec31ae5a970034c0cc4c2720ef0797c5ee3cdef130d0bf6bd5365ffe20",
        )
        cue_ids = {
            key: value for key, value in manifest["ids"].items()
            if key.startswith("track.cue_payload.")
        }
        self.assertEqual(len(cue_ids), 19)
        self.assertEqual(sorted(cue_ids.values()), list(range(11_001, 11_020)))

    def test_suite_generation_is_byte_identical_and_complete(self) -> None:
        expected = json.loads(INDEX.read_text())
        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory)
            base = temporary / "base.json"
            generated = temporary / "generated"
            index = temporary / "index.json"
            observed = generator.generate(base, generated, index)

            self.assertEqual(expected, observed)
            self.assertEqual(BASE_SUITE.read_bytes(), base.read_bytes())
            for path in sorted(GENERATED.glob("*.json")):
                self.assertEqual(path.read_bytes(), (generated / path.name).read_bytes())

        self.assertEqual(expected["variant_count"], 8)
        self.assertEqual(expected["case_count"], 114)
        self.assertEqual(expected["variants"][0]["case_count"], 63)
        self.assertEqual(
            [entry["case_count"] for entry in expected["variants"][1:4]],
            [1, 1, 1],
        )
        self.assertTrue(all(entry["case_count"] == 12 for entry in expected["variants"][4:]))

    def test_risky_seek_inputs_have_independent_process_suites(self) -> None:
        index = json.loads(INDEX.read_text())
        risks = index["variants"][1:4]
        self.assertEqual(
            [entry["risk"] for entry in risks],
            ["seek_in", "seek_out_only", "seek_malformed"],
        )
        for entry in risks:
            suite = json.loads((ROOT / entry["suite"]).read_text())
            self.assertEqual(len(suite["cases"]), 1)
            self.assertEqual(suite["cases"][0]["request_kind"], "0x2b04")
            self.assertTrue(suite["cases"][0]["fresh_connection"])

    def test_status_suites_use_requester_correct_contexts(self) -> None:
        index = json.loads(INDEX.read_text())
        for entry in index["variants"][4:]:
            suite = json.loads((ROOT / entry["suite"]).read_text())
            self.assertEqual(suite["defaults"]["device"], entry["player"])
            self.assertEqual(suite["defaults"]["setup"], entry["setup"])
            self.assertTrue(
                all(case["arguments"][0]["number"] >> 24 == entry["player"] for case in suite["cases"])
            )

    def test_legacy_and_extended_decoders_accept_canonical_records(self) -> None:
        legacy_record = struct.pack("<9I", 1, 11_002, 0, 150, 300, 10, 20, 30, 40)
        extension = struct.pack("<II", 1_000, 2_000)
        legacy = {
            "outcome": "raw_reply",
            "raw_response": {
                "error_kind": None,
                "messages": [
                    {
                        "kind": 0x4702,
                        "arguments": [
                            argument("number", 0x2104),
                            argument("number", 0),
                            argument("number", len(legacy_record)),
                            argument("blob", legacy_record.hex()),
                            argument("number", 36),
                            argument("number", 1),
                            argument("number", 0),
                            argument("number", len(extension)),
                            argument("blob", extension.hex()),
                        ],
                    }
                ],
            },
        }
        self.assertEqual(decode(legacy, "2104")[:2], (1, 44))

        record = build_record()
        extended = {
            "outcome": "raw_reply",
            "raw_response": {
                "error_kind": None,
                "messages": [
                    {
                        "kind": 0x4E02,
                        "arguments": [
                            argument("number", 0x2B04),
                            argument("number", 0),
                            argument("number", len(record)),
                            argument("blob", record.hex()),
                            argument("number", 1),
                        ],
                    }
                ],
            },
        }
        count, size, decoded = decode(extended, "2b04")
        self.assertEqual((count, size), (1, len(record)))
        self.assertEqual(json.loads(decoded)[0]["cue_microsec"], 0x0A0B0C0D)


if __name__ == "__main__":
    unittest.main()
