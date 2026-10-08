import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
AUDIT = ROOT / "data/experiments/source-library-count-audit.json"


class SourceLibraryCountAuditTests(unittest.TestCase):
    def test_source_and_relocated_database_populations_are_accounted_for(self) -> None:
        audit = json.loads(AUDIT.read_text())

        self.assertEqual(audit["format"], 1)
        self.assertTrue(audit["content_ids_equal"])
        self.assertTrue(audit["content_link_partitions_equal"])
        self.assertEqual(audit["relocation"], {
            "mapped": 4274,
            "tracks": 4342,
            "unresolved": 68,
        })

        for name in ("source", "relocated"):
            database = audit[name]
            self.assertEqual(database["integrity_check"], "ok")
            self.assertEqual(database["total_rows"], 4342)
            self.assertEqual(database["live_rows"], 4342)
            self.assertEqual(
                database["deleted_partitions"],
                [{"count": 4342, "value": 0}],
            )


if __name__ == "__main__":
    unittest.main()
