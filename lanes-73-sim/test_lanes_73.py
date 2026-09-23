#!/usr/bin/env python3
import unittest

from simulate_lanes_73 import PAGES, rank_role, CHAMPS


class TestLanes73(unittest.TestCase):
    def test_five_per_role(self):
        for role in ("jungle", "mid", "adc"):
            top = rank_role(role)[:5]
            self.assertEqual(len(top), 5, role)
            for c in top:
                self.assertIn(c.key, PAGES)
                self.assertEqual(len(PAGES[c.key].page), 6)

    def test_adc_winners(self):
        names = [c.name for c in rank_role("adc")[:5]]
        self.assertEqual(names, ["Caitlyn", "Ashe", "Xayah", "Lucian", "Jinx"])
        self.assertGreater(rank_role("adc")[0].patch_score, rank_role("adc")[4].patch_score)

    def test_mid_winners(self):
        names = [c.name for c in rank_role("mid")[:5]]
        self.assertEqual(names[0], "Hwei")
        self.assertIn("Syndra", names)
        self.assertIn("Ahri", names)
        self.assertIn("Sylas", names)

    def test_jungle_winners(self):
        names = [c.name for c in rank_role("jungle")[:5]]
        self.assertEqual(names[0], "Rek'Sai")
        self.assertIn("Vi", names)
        self.assertIn("Nidalee", names)

    def test_jhin_not_adc_top(self):
        names = [c.name for c in rank_role("adc")[:5]]
        self.assertNotIn("Jhin", names)
        self.assertNotIn("Miss Fortune", names)

    def test_skipped_have_reason(self):
        skipped = [c for c in CHAMPS if c.skip_why]
        self.assertGreaterEqual(len(skipped), 4)


if __name__ == "__main__":
    unittest.main()
