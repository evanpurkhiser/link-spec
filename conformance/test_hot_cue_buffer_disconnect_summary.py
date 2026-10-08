import json
import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import summarize_hot_cue_buffer_disconnect as summary


class HotCueBufferDisconnectSummaryTests(unittest.TestCase):
    def test_existing_stale_location_is_persisted(self) -> None:
        golden = json.loads(
            (
                summary.CONFORMANCE
                / "goldens/rekordbox-7.2.19/xdj-rx3/"
                "hot-cue-bank-location-state.json"
            ).read_text()
        )
        case = next(
            case
            for case in golden["behavior"]["cases"]
            if case["id"] == "location-2-beta-render-location-1"
        )
        self.assertEqual("persisted", summary.stale_classification(case))

    def test_existing_uninitialized_location_is_cleared_shape(self) -> None:
        golden = json.loads(
            (
                summary.CONFORMANCE
                / "goldens/rekordbox-7.2.19/xdj-rx3/"
                "hot-cue-bank-location-cross.json"
            ).read_text()
        )
        case = next(
            case
            for case in golden["behavior"]["cases"]
            if case["id"] == "header-location-1-render-location-2-extended"
        )
        case = {**case, "total": 1}
        self.assertEqual("cleared", summary.stale_classification(case))

    def test_any_other_shape_is_rejected(self) -> None:
        with self.assertRaises(AssertionError):
            summary.stale_classification(
                {"outcome": "menu", "total": 1, "rows": []}
            )

    def test_completed_capture_is_promoted_in_source_ledger(self) -> None:
        sources = (summary.ROOT / "SOURCES.md").read_text()
        self.assertIn("Repeat-verified control/rejoin experiment", sources)
        self.assertNotIn(
            "while real captures are pending",
            sources,
        )


if __name__ == "__main__":
    unittest.main()
