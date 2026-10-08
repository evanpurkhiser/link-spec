import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent


class HotCueBufferDisconnectTests(unittest.TestCase):
    def load(self, name: str) -> dict[str, object]:
        return json.loads((ROOT / f"suites/{name}.json").read_text())

    def test_warmup_populates_location_one_root(self) -> None:
        suite = self.load("hot-cue-bank-buffer-disconnect-warmup")
        self.assertEqual(1, len(suite["cases"]))
        case = suite["cases"][0]
        self.assertEqual("0x2001", case["request_kind"])
        self.assertEqual("0x01010101", case["arguments"][0]["number"])
        self.assertEqual("0x01010101", case["render_context"])
        self.assertEqual(3, case["expect"]["total"])

    def test_post_phase_reads_old_then_current_location(self) -> None:
        suite = self.load("hot-cue-bank-buffer-disconnect-post")
        self.assertEqual(2, len(suite["cases"]))
        stale, current = suite["cases"]
        for case in (stale, current):
            self.assertEqual("0x01010201", case["arguments"][0]["number"])
            self.assertEqual(
                "$fixture.hotcue.folder.beta", case["arguments"][1]["number"]
            )
        self.assertEqual("0x01010101", stale["render_context"])
        self.assertEqual("any", stale["expect"]["outcome"])
        self.assertEqual("0x01010201", current["render_context"])
        self.assertEqual("menu", current["expect"]["outcome"])
        self.assertEqual(
            ["$fixture.hotcue.bank.beta"], current["expect"]["item_ids"]
        )

    def test_control_matches_existing_stale_buffer_probe(self) -> None:
        existing = self.load("hot-cue-bank-location-state")
        old_case = next(
            case
            for case in existing["cases"]
            if case["id"] == "location-2-beta-render-location-1"
        )
        post = self.load("hot-cue-bank-buffer-disconnect-post")["cases"][0]
        self.assertEqual(old_case["request_kind"], post["request_kind"])
        self.assertEqual(old_case["arguments"], post["arguments"])
        self.assertEqual(old_case["render_context"], post["render_context"])


if __name__ == "__main__":
    unittest.main()
