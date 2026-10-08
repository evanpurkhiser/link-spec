import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
REFERENCE = ROOT / "PROTOCOL_REFERENCE.md"
HISTORY_GOLDEN = (
    ROOT / "conformance/goldens/rekordbox-7.2.19/xdj-rx3/history-lifecycle.json"
)
TRACK_TYPE_GOLDEN = (
    ROOT
    / "conformance/goldens/rekordbox-7.2.19/xdj-rx3/context-track-type-families.json"
)


def cases(path: Path) -> dict[str, dict]:
    golden = json.loads(path.read_text())
    return {case["id"]: case for case in golden["behavior"]["cases"]}


class ProtocolRequestSignatureTests(unittest.TestCase):
    def test_history_track_signature_is_live_observed(self) -> None:
        history = cases(HISTORY_GOLDEN)
        tracks = history["tracks-after-second"]

        self.assertEqual(tracks["outcome"], "menu")
        self.assertEqual(tracks["total"], 2)
        self.assertEqual(
            [row["arguments"][6]["value"] for row in tracks["rows"]],
            [0x0F04, 0x0F04],
        )

        reference = REFERENCE.read_text()
        self.assertIn(
            "| `1112` | `C,S,history` | track `0f04` in insertion order |",
            reference,
        )

    def test_original_artist_child_signatures_are_live_observed(self) -> None:
        track_types = cases(TRACK_TYPE_GOLDEN)
        albums = track_types["type-01--original-artist-albums"]
        tracks = track_types["type-01--original-artist-tracks"]

        self.assertEqual(albums["outcome"], "menu")
        self.assertEqual(albums["total"], 4)
        self.assertEqual(
            [row["arguments"][6]["value"] for row in albums["rows"]],
            [0xA0, 0x02, 0x02, 0x02],
        )
        self.assertEqual(tracks["outcome"], "menu")
        self.assertEqual(tracks["total"], 3)
        self.assertEqual(
            [row["arguments"][6]["value"] for row in tracks["rows"]],
            [0x0F04, 0x0F04, 0x0F04],
        )

        reference = REFERENCE.read_text()
        self.assertIn(
            "| `1402` | `C,S,original_artist` | album `02` / ALL `a0` |",
            reference,
        )
        self.assertIn(
            "| `1502` | `C,S,original_artist,album` | track `0f04` |",
            reference,
        )

    def test_no_live_signature_is_still_marked_unexercised(self) -> None:
        reference = REFERENCE.read_text()

        self.assertNotIn("track; not exercised", reference)
        self.assertNotIn("album; not exercised", reference)


if __name__ == "__main__":
    unittest.main()
