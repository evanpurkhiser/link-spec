import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import summarize_hot_cue_legacy_setter_parser as summary


class HotCueLegacySetterSummaryTests(unittest.TestCase):
    def test_readable_row_preserves_lifecycle_fields(self) -> None:
        variant = {
            "id": "actual-cue-length-00000000",
            "axis": "actual-cue-length",
            "value": 0,
            "word": None,
        }
        run = {
            "outcome": "timeout",
            "response_kind": None,
            "response_argument_count": None,
            "status": None,
            "response_record_count": None,
            "process_state": "alive",
            "application_event_count": 0,
            "database_effect": "pristine",
            "getter_outcome": "timeout",
            "getter_effect": "unavailable-timeout",
            "getter_record_count": None,
            "getter_record_lengths": None,
            "getter_blob_bytes": None,
            "restart_getter_outcome": "raw_reply",
            "restart_getter_effect": "pristine",
            "restart_getter_record_lengths": [124, 124, 124],
            "restart_getter_blob_bytes": 372,
            "restart_database_effect": "pristine",
        }
        row = summary.readable_row(
            variant,
            {"runs": [run, run], "repeat_verified": True},
        )

        self.assertEqual("complete", row["state"])
        self.assertEqual("", row["word"])
        self.assertEqual("", row["run1_response_kind"])
        self.assertEqual("timeout", row["run1_getter_outcome"])
        self.assertEqual("raw_reply", row["run2_restart_getter_outcome"])
        self.assertEqual("124/124/124", row["run1_restart_getter_record_lengths"])
        self.assertEqual(372, row["run2_restart_getter_blob_bytes"])
        self.assertTrue(row["repeat_verified"])

    def test_pending_row_has_stable_empty_columns(self) -> None:
        variant = {
            "id": "flag-00000000",
            "axis": "flag",
            "value": 0,
            "word": None,
        }
        row = summary.readable_row(variant, None)

        self.assertEqual("pending", row["state"])
        self.assertEqual("", row["run1_outcome"])
        self.assertFalse(row["repeat_verified"])


if __name__ == "__main__":
    unittest.main()
