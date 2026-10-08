import json
import hashlib
import subprocess
import struct
import sys
import tempfile
import unittest
from pathlib import Path

import generate_payload_assets
import generate_payload_boundary_assets
import generate_adjacent_payload_boundary_suites

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.summarize_adjacent_payload_success import REPLIES, summarize_success
from tools import summarize_adjacent_payload_success_status as status_summary
from tools import summarize_adjacent_payload_boundaries as boundary_summary


ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "payload-assets/generated"
MANIFEST = ASSETS / "manifest.json"
SUITE = ROOT / "suites/adjacent-payload-success.json"
SUITE_GENERATOR = ROOT / "generate_adjacent_payload_success_suite.py"
STATUS_SUITE_GENERATOR = (
    ROOT / "generate_adjacent_payload_success_status_suites.py"
)
STATUS_SUITES = ROOT / "suites/generated/adjacent-payload-success-status"
FIXTURE_MANIFEST = ROOT / "fixtures/generated/payload-valid/manifest.json"
SUCCESS_EVIDENCE = ROOT.parent / "data/experiments/adjacent-payload/success"
BOUNDARY_ASSETS = ROOT / "payload-assets/boundaries"
BOUNDARY_SUITES = ROOT / "suites/generated/adjacent-payload-boundaries"
BOUNDARY_INDEX = ROOT / "data/adjacent-payload-boundary-matrix.json"


def sections(path: Path) -> list[tuple[bytes, int, bytes]]:
    data = path.read_bytes()
    magic, header_length, file_length = struct.unpack_from(">4sII", data)
    if magic != b"PMAI" or file_length != len(data):
        raise ValueError(f"{path}: invalid PMAI header")

    result = []
    offset = header_length
    while offset < len(data):
        name, section_header, section_length = struct.unpack_from(">4sII", data, offset)
        if not 12 <= section_header <= section_length <= len(data) - offset:
            raise ValueError(f"{path}: invalid section at {offset}")
        result.append((name, section_header, data[offset : offset + section_length]))
        offset += section_length
    if offset != len(data):
        raise ValueError(f"{path}: trailing partial section")
    return result


class PayloadAssetTests(unittest.TestCase):
    def test_real_baseline_success_evidence_is_complete_and_bound(self) -> None:
        summary_path = SUCCESS_EVIDENCE / "summary.json"
        matrix_path = SUCCESS_EVIDENCE / "matrix.csv"
        receipt_path = SUCCESS_EVIDENCE / "finalization.json"
        summary = json.loads(summary_path.read_text())
        receipt = json.loads(receipt_path.read_text())

        self.assertEqual(summary["case_count"], 15)
        self.assertEqual(summary["service_count"], 10)
        self.assertEqual(summary["successful_reply_count"], 15)
        self.assertEqual(summary["payload_bearing_reply_count"], 12)
        self.assertEqual(summary["empty_payload_reply_count"], 3)
        self.assertEqual(
            {
                case_id
                for case_id, byte_count in summary["payload_bytes_by_case"].items()
                if byte_count == 0
            },
            {
                "kind-2204--deterministic-analysis",
                "kind-2504--deterministic-analysis",
                "kind-2804--deterministic-analysis",
            },
        )
        self.assertEqual(
            summary["post_request_health"],
            {"process_count": 1, "responding_count": 1, "application_events": []},
        )

        self.assertEqual(receipt["case_count"], 15)
        self.assertEqual(receipt["service_count"], 10)
        self.assertTrue(receipt["focused_tests_passed"])
        self.assertFalse(receipt["synthetic_identity_units_active"])
        self.assertTrue(receipt["deterministic_guest_assets_removed"])
        self.assertTrue(receipt["isolated_vm_stopped"])
        self.assertEqual(
            receipt["summary_sha256"],
            hashlib.sha256(summary_path.read_bytes()).hexdigest(),
        )
        self.assertEqual(
            receipt["matrix_sha256"],
            hashlib.sha256(matrix_path.read_bytes()).hexdigest(),
        )

    def test_boundary_generation_is_byte_identical_and_complete(self) -> None:
        expected_index = json.loads((BOUNDARY_ASSETS / "manifest.json").read_text())
        declaration_index = json.loads(BOUNDARY_INDEX.read_text())
        self.assertEqual(expected_index["variant_count"], 30)
        self.assertEqual(declaration_index["variant_count"], 30)
        self.assertEqual(declaration_index["case_count"], 57)

        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory)
            assets = temporary / "assets"
            suites = temporary / "suites"
            index = temporary / "matrix.json"
            observed = generate_payload_boundary_assets.generate(assets)

            original_assets = generate_adjacent_payload_boundary_suites.ASSETS
            try:
                generate_adjacent_payload_boundary_suites.ASSETS = assets
                generated = generate_adjacent_payload_boundary_suites.generate(suites, index)
            finally:
                generate_adjacent_payload_boundary_suites.ASSETS = original_assets

            self.assertEqual(expected_index, observed)
            self.assertEqual(declaration_index, generated)
            for expected in sorted(BOUNDARY_ASSETS.rglob("*")):
                if expected.is_file():
                    self.assertEqual(
                        expected.read_bytes(),
                        (assets / expected.relative_to(BOUNDARY_ASSETS)).read_bytes(),
                    )
            for expected in sorted(BOUNDARY_SUITES.glob("*.json")):
                self.assertEqual(expected.read_bytes(), (suites / expected.name).read_bytes())

    def test_boundary_assets_encode_exact_parser_axes(self) -> None:
        def asset(variant: str, suffix: str) -> Path:
            return BOUNDARY_ASSETS / variant / "PIONEER/USBANLZ/000/deterministic" / suffix

        for count in (6248, 6249):
            pqtz = next(
                data for name, _header, data in sections(asset(f"pqtz-count-{count}", "ANLZ0000.DAT"))
                if name == b"PQTZ"
            )
            self.assertEqual(struct.unpack_from(">I", pqtz, 20)[0], count)
            self.assertEqual(len(pqtz) - 24, count * 8)

        for count in (399, 400, 401):
            pvbr = next(
                data for name, _header, data in sections(asset(f"pvbr-words-{count}", "ANLZ0000.DAT"))
                if name == b"PVBR"
            )
            self.assertEqual((len(pvbr) - 16) // 4, count)

        for count in (0, 1, 65535):
            pwv3 = next(
                data for name, _header, data in sections(asset(f"pwv3-count-{count}", "ANLZ0000.EXT"))
                if name == b"PWV3"
            )
            pkey = next(
                data for name, _header, data in sections(asset(f"pkey-count-{count}", "ANLZ0000.EXT"))
                if name == b"PKEY"
            )
            self.assertEqual(struct.unpack_from(">I", pwv3, 16)[0], count)
            self.assertEqual(struct.unpack_from(">H", pkey, 16)[0], count)

        for layout, remainder in (("aligned", 0), ("unaligned", 1)):
            atoms = [
                data for name, _header, data in sections(asset(f"atom-duplicate-{layout}", "ANLZ0000.2EX"))
                if name == b"PWV7"
            ]
            self.assertEqual(len(atoms), 2)
            self.assertEqual(len(atoms[0]) % 4, remainder)

    def test_boundary_jpeg_limits_are_exact(self) -> None:
        artwork = Path("PIONEER/Artwork/000/deterministic/artwork.jpg")
        for size in (1_048_576, 1_048_577):
            path = BOUNDARY_ASSETS / f"jpeg-bytes-{size}" / artwork
            self.assertEqual(path.stat().st_size, size)

        for axis, dimensions in (
            ("width", ((800, 8), (801, 8))),
            ("height", ((8, 800), (8, 801))),
        ):
            for value, expected in zip((800, 801), dimensions, strict=True):
                data = (BOUNDARY_ASSETS / f"jpeg-{axis}-{value}" / artwork).read_bytes()
                marker = data.index(b"\xff\xc0")
                height, width = struct.unpack_from(">HH", data, marker + 5)
                self.assertEqual((width, height), expected)

    def test_boundary_reducer_validates_complete_hash_bound_matrix(self) -> None:
        index = json.loads(BOUNDARY_INDEX.read_text())
        fixture = json.loads(FIXTURE_MANIFEST.read_text())

        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory)
            goldens = temporary / "goldens"
            evidence = temporary / "evidence"
            goldens.mkdir()

            for entry in index["variants"]:
                suite_path = ROOT / entry["suite"]
                asset_manifest_path = ROOT / entry["asset_manifest"]
                suite = json.loads(suite_path.read_text())
                asset_manifest = json.loads(asset_manifest_path.read_text())
                cases = []
                for declaration in suite["cases"]:
                    kind = int(declaration["request_kind"], 16)
                    reply = REPLIES[f"{kind:04x}"]
                    response_arguments = (
                        [{"type": "number", "value": 1}]
                        if kind == 0x2804
                        else [{"type": "blob", "hex": "00"}]
                    )
                    cases.append(
                        {
                            "id": declaration["id"],
                            "description": declaration["description"],
                            "request": {
                                "kind": kind,
                                "arguments": [],
                                "fixed_tag_slots": declaration.get("fixed_tag_slots"),
                            },
                            "outcome": "raw_reply",
                            "raw_response": {
                                "outcome": "raw_reply",
                                "raw_hex": "",
                                "decoded_bytes": 0,
                                "messages": [{"kind": reply, "arguments": response_arguments}],
                                "error_kind": None,
                            },
                            "total": None,
                            "header": [],
                            "pages": [],
                            "rows": [],
                        }
                    )

                golden = {
                    "format": 2,
                    "provenance": {
                        "backend": "rekordbox",
                        "backend_version": "7.2.19",
                        "suite_sha256": hashlib.sha256(suite_path.read_bytes()).hexdigest(),
                        "fixture_database_sha256": fixture["database_sha256"],
                        "fixture_fingerprint": fixture["fixture_fingerprint"],
                    },
                    "behavior": {
                        "suite": suite["name"],
                        "fixture": {
                            "profile": suite["fixture_profile"],
                            "fingerprint": fixture["fixture_fingerprint"],
                            "version": fixture["fixture_version"],
                        },
                        "cases": cases,
                    },
                }
                golden_path = goldens / f"{entry['name']}.json"
                golden_path.write_text(json.dumps(golden))

                variant_evidence = evidence / "variants" / entry["name"]
                variant_evidence.mkdir(parents=True)
                for name in ("staged-assets.json", "record-assets.json", "repeat-assets.json"):
                    (variant_evidence / name).write_text(json.dumps(asset_manifest["assets"]))
                for phase in ("record", "repeat"):
                    for position in ("before", "after"):
                        name = f"{phase}-health-{position}.json"
                        health = {
                            "schema_version": 2,
                            "label": (
                                f"adjacent-payload-success-{entry['name']}-"
                                f"{phase}-{position}"
                            ),
                            "rekordbox_process_count": 1,
                            "rekordbox_processes": [{"responding": True}],
                            "application_events": [],
                        }
                        (variant_evidence / name).write_text(json.dumps(health))

                file_hash = lambda name: hashlib.sha256((variant_evidence / name).read_bytes()).hexdigest()
                receipt = {
                    "format": 1,
                    "scope": boundary_summary.SCOPE,
                    "variant": entry["name"],
                    "suite_sha256": hashlib.sha256(suite_path.read_bytes()).hexdigest(),
                    "fixture_manifest_sha256": hashlib.sha256(FIXTURE_MANIFEST.read_bytes()).hexdigest(),
                    "asset_manifest_sha256": hashlib.sha256(asset_manifest_path.read_bytes()).hexdigest(),
                    "staged_assets_sha256": file_hash("staged-assets.json"),
                    "record_assets_sha256": file_hash("record-assets.json"),
                    "repeat_assets_sha256": file_hash("repeat-assets.json"),
                    "identity_sha256": hashlib.sha256((ROOT / "runs/xdj-rx3-player-11.json").read_bytes()).hexdigest(),
                    "golden_sha256": hashlib.sha256(golden_path.read_bytes()).hexdigest(),
                    "record_health_before_sha256": file_hash("record-health-before.json"),
                    "record_health_after_sha256": file_hash("record-health-after.json"),
                    "repeat_health_before_sha256": file_hash("repeat-health-before.json"),
                    "repeat_health_after_sha256": file_hash("repeat-health-after.json"),
                    "case_count": entry["case_count"],
                    "service_count": entry["service_count"],
                    "exact_repeat": True,
                }
                (variant_evidence / "receipt.json").write_text(json.dumps(receipt))

            original_goldens = boundary_summary.GOLDENS
            original_evidence = boundary_summary.EVIDENCE
            try:
                boundary_summary.GOLDENS = goldens
                boundary_summary.EVIDENCE = evidence
                summary, matrix = boundary_summary.summarize_boundaries()
            finally:
                boundary_summary.GOLDENS = original_goldens
                boundary_summary.EVIDENCE = original_evidence

        self.assertEqual(summary["variant_count"], 30)
        self.assertEqual(summary["case_count"], 57)
        self.assertEqual(len(matrix), 57)

    def test_generation_is_byte_identical(self) -> None:
        expected = json.loads(MANIFEST.read_text())
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "generated"
            observed = generate_payload_assets.generate(output)
            self.assertEqual(expected, observed)
            for asset in expected["assets"]:
                relative = Path(asset["path"])
                self.assertEqual(
                    (ASSETS / relative).read_bytes(),
                    (output / relative).read_bytes(),
                )

    def test_dat_contains_controlled_sequential_loader_sections(self) -> None:
        rows = sections(
            ASSETS / "PIONEER/USBANLZ/000/deterministic/ANLZ0000.DAT"
        )
        self.assertEqual(
            [name for name, _header, _data in rows],
            [b"PPTH", b"PVBR", b"PQTZ", b"PWAV", b"PWV2"],
        )
        by_name = {name: (header, data) for name, header, data in rows}
        self.assertEqual(len(by_name[b"PVBR"][1]), 1620)
        self.assertEqual(len(by_name[b"PQTZ"][1]), 56)
        self.assertEqual(len(by_name[b"PWAV"][1]), 420)
        self.assertEqual(len(by_name[b"PWV2"][1]), 120)
        self.assertEqual(struct.unpack_from(">I", by_name[b"PQTZ"][1], 20)[0], 4)

    def test_ext_contains_detailed_waveform_and_segmented_keys(self) -> None:
        rows = sections(
            ASSETS / "PIONEER/USBANLZ/000/deterministic/ANLZ0000.EXT"
        )
        self.assertEqual(
            [name for name, _header, _data in rows],
            [b"PPTH", b"PWV3", b"PKEY"],
        )
        pkey = next(data for name, _header, data in rows if name == b"PKEY")
        self.assertEqual(struct.unpack_from(">HH", pkey, 14), (12, 2))
        self.assertEqual(len(pkey), 44)

    def test_two_ex_contains_one_controlled_atom(self) -> None:
        rows = sections(
            ASSETS / "PIONEER/USBANLZ/000/deterministic/ANLZ0000.2EX"
        )
        self.assertEqual(
            [name for name, _header, _data in rows],
            [b"PPTH", b"PWV7"],
        )
        wave = rows[1][2]
        self.assertEqual(struct.unpack_from(">II", wave, 12), (3, 15))
        self.assertEqual(len(wave), 69)

    def test_jpeg_is_baseline_eight_by_eight(self) -> None:
        data = (
            ASSETS / "PIONEER/Artwork/000/deterministic/artwork.jpg"
        ).read_bytes()
        self.assertEqual(data[:2], b"\xff\xd8")
        marker = data.index(b"\xff\xc0")
        height, width = struct.unpack_from(">HH", data, marker + 5)
        self.assertEqual((width, height), (8, 8))

    def test_success_suite_is_byte_identical_and_complete(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            candidate = Path(directory) / "suite.json"
            subprocess.run(
                [sys.executable, SUITE_GENERATOR, "--output", candidate],
                check=True,
            )
            self.assertEqual(SUITE.read_bytes(), candidate.read_bytes())

        suite = json.loads(SUITE.read_text())
        cases = suite["cases"]
        self.assertEqual(suite["fixture_profile"], "payload-valid")
        self.assertEqual(len(cases), 15)
        self.assertEqual(
            {case["request_kind"] for case in cases},
            {
                "0x2003", "0x2103", "0x2004", "0x2204", "0x2504",
                "0x2804", "0x2904", "0x2a04", "0x2c04", "0x2d04",
            },
        )
        self.assertTrue(all(case["direct_response"] for case in cases))
        self.assertTrue(all(case["fresh_connection"] for case in cases))
        self.assertTrue(all(not case["render"] for case in cases))

        fixture = json.loads(FIXTURE_MANIFEST.read_text())
        self.assertEqual(fixture["profile"], "payload-valid")
        self.assertEqual(fixture["integrity"], "ok")
        self.assertEqual(
            fixture["database_sha256"],
            "c66100041113db7c6ca41d739f6766a3f09c44377e6f3e16c8df7e222d5abf2a",
        )
        self.assertEqual(
            fixture["fixture_fingerprint"],
            "b8c22f232e17d6157c25fc25c65af29eb77bebef4aede6027c7407cc22461dfa",
        )

    def test_success_status_cross_is_byte_identical_and_complete(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "suites"
            subprocess.run(
                [
                    sys.executable,
                    STATUS_SUITE_GENERATOR,
                    "--output-dir",
                    output,
                ],
                check=True,
            )
            for path in sorted(STATUS_SUITES.glob("*.json")):
                self.assertEqual(path.read_bytes(), (output / path.name).read_bytes())

        suites = [json.loads(path.read_text()) for path in sorted(STATUS_SUITES.glob("*.json"))]
        self.assertEqual(len(suites), 4)
        self.assertEqual(sum(len(suite["cases"]) for suite in suites), 60)
        self.assertEqual({suite["defaults"]["device"] for suite in suites}, {1, 11})
        self.assertEqual(
            {suite["defaults"]["setup"] for suite in suites},
            {"extended", "legacy"},
        )
        for suite in suites:
            player = suite["defaults"]["device"]
            self.assertEqual(len(suite["cases"]), 15)
            self.assertTrue(all(case["fresh_connection"] for case in suite["cases"]))
            self.assertTrue(all(case["direct_response"] for case in suite["cases"]))
            for case in suite["cases"]:
                packed = case["arguments"][0]["number"]
                self.assertEqual(packed >> 24, player)

    def test_success_summary_requires_one_typed_direct_reply_per_case(self) -> None:
        suite = json.loads(SUITE.read_text())
        fixture = json.loads(FIXTURE_MANIFEST.read_text())
        cases = []
        for declaration in suite["cases"]:
            kind = int(declaration["request_kind"], 16)
            arguments = [{"type": "number", "value": 1}]
            if kind != 0x2804:
                arguments.append({"type": "blob", "hex": "00"})
            cases.append(
                {
                    "id": declaration["id"],
                    "description": declaration["description"],
                    "request": {
                        "kind": kind,
                        "arguments": [],
                        "fixed_tag_slots": declaration.get("fixed_tag_slots"),
                    },
                    "outcome": "raw_reply",
                    "raw_response": {
                        "outcome": "raw_reply",
                        "raw_hex": "",
                        "decoded_bytes": 0,
                        "messages": [
                            {
                                "kind": REPLIES[declaration["request_kind"][2:]],
                                "arguments": arguments,
                            }
                        ],
                        "error_kind": None,
                    },
                    "total": None,
                    "header": [],
                    "pages": [],
                    "rows": [],
                }
            )

        fake = {
            "format": 2,
            "provenance": {
                "backend": "rekordbox",
                "backend_version": "7.2.19",
                "suite_sha256": hashlib.sha256(SUITE.read_bytes()).hexdigest(),
                "fixture_database_sha256": fixture["database_sha256"],
                "fixture_fingerprint": fixture["fixture_fingerprint"],
            },
            "behavior": {
                "suite": suite["name"],
                "fixture": {
                    "profile": suite["fixture_profile"],
                    "fingerprint": fixture["fixture_fingerprint"],
                    "version": fixture["fixture_version"],
                },
                "cases": cases,
            },
        }
        with tempfile.TemporaryDirectory() as directory:
            golden = Path(directory) / "golden.json"
            golden.write_text(json.dumps(fake))
            summary, matrix = summarize_success(
                SUITE,
                FIXTURE_MANIFEST,
                golden,
                MANIFEST,
            )

        self.assertEqual(summary["case_count"], 15)
        self.assertEqual(summary["service_count"], 10)
        self.assertEqual(summary["successful_reply_count"], 15)
        self.assertEqual(summary["payload_bearing_reply_count"], 14)
        self.assertEqual(summary["empty_payload_reply_count"], 1)
        self.assertEqual(
            summary["asset_manifest_sha256"],
            hashlib.sha256(MANIFEST.read_bytes()).hexdigest(),
        )
        self.assertEqual(len(matrix), 15)

    def test_success_status_summary_preserves_observed_differences(self) -> None:
        fixture = json.loads(FIXTURE_MANIFEST.read_text())
        with tempfile.TemporaryDirectory() as directory:
            golden_root = Path(directory) / "goldens"
            for variant, model, player, setup in status_summary.VARIANTS:
                suite_path = STATUS_SUITES / f"player-{player}-{setup}.json"
                suite = json.loads(suite_path.read_text())
                cases = []
                for declaration in suite["cases"]:
                    kind = int(declaration["request_kind"], 16)
                    blob = "01" if variant == "xdj-rx3-player-11-legacy" else "00"
                    arguments = [{"type": "number", "value": 1}]
                    if kind != 0x2804:
                        arguments.append({"type": "blob", "hex": blob})
                    cases.append(
                        {
                            "id": declaration["id"],
                            "description": declaration["description"],
                            "request": {
                                "kind": kind,
                                "arguments": [],
                                "fixed_tag_slots": declaration.get("fixed_tag_slots"),
                            },
                            "outcome": "raw_reply",
                            "raw_response": {
                                "outcome": "raw_reply",
                                "raw_hex": "",
                                "decoded_bytes": 0,
                                "messages": [
                                    {
                                        "kind": REPLIES[declaration["request_kind"][2:]],
                                        "arguments": arguments,
                                    }
                                ],
                                "error_kind": None,
                            },
                            "total": None,
                            "header": [],
                            "pages": [],
                            "rows": [],
                        }
                    )

                fake = {
                    "format": 2,
                    "provenance": {
                        "backend": "rekordbox",
                        "backend_version": "7.2.19",
                        "suite_sha256": hashlib.sha256(suite_path.read_bytes()).hexdigest(),
                        "fixture_database_sha256": fixture["database_sha256"],
                        "fixture_fingerprint": fixture["fixture_fingerprint"],
                    },
                    "behavior": {
                        "suite": suite["name"],
                        "fixture": {
                            "profile": suite["fixture_profile"],
                            "fingerprint": fixture["fixture_fingerprint"],
                            "version": fixture["fixture_version"],
                        },
                        "cases": cases,
                    },
                }
                golden = golden_root / model / f"adjacent-payload-success-{setup}.json"
                golden.parent.mkdir(parents=True, exist_ok=True)
                golden.write_text(json.dumps(fake))

            original_root = status_summary.GOLDEN_ROOT
            try:
                status_summary.GOLDEN_ROOT = golden_root
                summary, matrix = status_summary.summarize_status_cross(
                    validate_evidence=False
                )
            finally:
                status_summary.GOLDEN_ROOT = original_root

        self.assertEqual(summary["variant_count"], 4)
        self.assertEqual(summary["logical_case_count"], 15)
        self.assertEqual(summary["case_count"], 60)
        self.assertFalse(summary["all_responses_invariant"])
        self.assertEqual(len(matrix), 60)


if __name__ == "__main__":
    unittest.main()
