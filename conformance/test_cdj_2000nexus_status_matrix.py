import hashlib
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "tools"))

import summarize_cdj_2000nexus_status_matrix as summary


MATRIX = ROOT / "data/cdj-2000nexus-status-matrix.json"
EXPECTED_STATUS_SHA256 = (
    "8e9c36049a85be2f31c989bfbff415d989bdb0f395987135eb35f53f1d8fb70b"
)


class Cdj2000NexusStatusMatrixTests(unittest.TestCase):
    def test_matrix_declares_complete_genuine_status_cross(self) -> None:
        matrix = json.loads(MATRIX.read_text())
        identity = json.loads((ROOT / matrix["identity"]).read_text())
        status_hex = "".join((ROOT / matrix["status_packet"]).read_text().split())
        status = bytes.fromhex(status_hex)

        self.assertEqual("CDJ-2000nexus", identity["model"])
        self.assertEqual(1, identity["player"])
        self.assertEqual("cdj", identity["device_type"])
        self.assertEqual(2, identity["generation"])
        self.assertEqual(284, identity["status_packet_bytes"])
        self.assertEqual(EXPECTED_STATUS_SHA256, identity["status_packet_sha256"])
        self.assertEqual(EXPECTED_STATUS_SHA256, hashlib.sha256(status).hexdigest())
        self.assertEqual(13, len(matrix["variants"]))

        total_cases = 0
        for variant in matrix["variants"]:
            suite = json.loads((ROOT / variant["suite"]).read_text())
            manifest = ROOT / f"fixtures/generated/{variant['fixture']}/manifest.json"
            self.assertTrue(manifest.is_file(), variant["fixture"])
            self.assertEqual(variant["fixture"], suite["fixture_profile"])
            total_cases += len(suite["cases"])

        self.assertEqual(249, total_cases)

    def test_output_paths_are_unique_and_scoped_to_the_genuine_identity(self) -> None:
        matrix = json.loads(MATRIX.read_text())
        goldens = [variant["golden"] for variant in matrix["variants"]]
        self.assertEqual(len(goldens), len(set(goldens)))
        for golden in goldens:
            self.assertTrue(
                golden.startswith(
                    "goldens/rekordbox-7.2.19/cdj-2000nexus-status/"
                )
            )

    def test_semantic_behavior_ignores_description_and_page_chunking(self) -> None:
        reference = json.loads(
            (
                ROOT
                / "goldens/rekordbox-7.2.19/cdj-3000-status/display-song-info.json"
            ).read_text()
        )["behavior"]
        actual = json.loads(
            (
                ROOT
                / "goldens/rekordbox-7.2.19/cdj-2000nexus-status/display-song-info.json"
            ).read_text()
        )["behavior"]

        self.assertNotEqual(reference, actual)
        self.assertEqual(
            summary.semantic_behavior(reference),
            summary.semantic_behavior(actual),
        )

    def test_completed_matrix_is_promoted_across_provenance_ledgers(self) -> None:
        completed = json.loads(
            (ROOT.parent / "data/experiments/device-status/cdj-2000nexus/summary.json").read_text()
        )
        self.assertEqual(249, completed["matrix"]["completed_cases"])
        self.assertEqual(13, completed["matrix"]["repeat_verified_variants"])
        self.assertEqual(13, completed["matrix"]["semantic_reference_matches"])

        documents = (
            "DEVICE_STATUS_PROVENANCE.md",
            "DEVICE_MATRIX_ORACLE.md",
            "EXPERIMENTS.md",
            "REKORDBOX_RESEARCH_GAPS.md",
            "CONFORMANCE_COVERAGE.md",
            "SOURCES.md",
            "CLEANUP.md",
            "GAP_MATRIX.md",
            "PROTOCOL_REFERENCE.md",
        )
        stale_claims = (
            "pending 249-case",
            "249-case real-Rekordbox matrix is queued",
            "matrix has not run against Rekordbox",
            "pending 249-case genuine-device declaration",
            "queued authentic CDJ-2000nexus matrix",
            "queued CDJ-2000nexus sources",
        )
        corpus = "\n".join((ROOT.parent / path).read_text() for path in documents)
        for claim in stale_claims:
            self.assertNotIn(claim, corpus)


if __name__ == "__main__":
    unittest.main()
