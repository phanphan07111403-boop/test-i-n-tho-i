#!/usr/bin/env python3
"""Sanity checks for the 7.3 support + pad ranking sim."""

import unittest

from simulate_support_73 import (
    CRIT_72,
    CRIT_73,
    PAD_MIN,
    auto_dps,
    rank_all,
    snapshot,
    CHAMPS,
)


class TestSupport73(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = rank_all()
        cls.by_name = {r["name"]: r for r in cls.rows}
        cls.top5 = [r["name"] for r in cls.rows if r["pad_fit"]][:5]

    def test_top5_are_pad_fit(self):
        self.assertEqual(len(self.top5), 5)
        for name in self.top5:
            self.assertGreaterEqual(self.by_name[name]["pad_score"], PAD_MIN)

    def test_top5_order(self):
        self.assertEqual(self.top5, ["Lulu", "Leona", "Sona", "Milio", "Braum"])

    def test_nami_and_thresh_fail_pad(self):
        self.assertFalse(self.by_name["Nami"]["pad_fit"])
        self.assertFalse(self.by_name["Thresh"]["pad_fit"])
        self.assertNotIn("Nami", self.top5)
        self.assertNotIn("Thresh", self.top5)

    def test_lulu_has_biggest_adc_amp(self):
        self.assertGreater(self.by_name["Lulu"]["avg_extra_dps"], self.by_name["Sona"]["avg_extra_dps"])
        self.assertGreater(self.by_name["Lulu"]["avg_patch_delta"], 100)

    def test_sona_helia_online_by_12(self):
        snap = snapshot(next(c for c in CHAMPS if c.key == "sona"), 12)
        self.assertTrue(snap["helia"])
        self.assertGreater(snap["heal_hps"], 40)

    def test_leona_yordle_online_by_12(self):
        snap = snapshot(next(c for c in CHAMPS if c.key == "leona"), 12)
        self.assertTrue(snap["yordle"])

    def test_crit_73_beats_72(self):
        a = auto_dps(150, 1.2, 0.5, 20, CRIT_73, 3.0)
        b = auto_dps(150, 1.2, 0.5, 20, CRIT_72, 2.5)
        self.assertGreater(a, b)

    def test_ranking_deterministic(self):
        again = [r["name"] for r in rank_all() if r["pad_fit"]][:5]
        self.assertEqual(again, self.top5)

    def test_full_builds_six_slots(self):
        from simulate_support_73 import FULL_BUILDS
        for name in self.top5:
            fb = FULL_BUILDS[name.lower()]
            self.assertEqual(len(fb.page), 6, name)
            self.assertGreater(fb.gold, 8000)
            self.assertEqual(len(fb.runes), 5)
            self.assertIn("Flash", fb.spells)

    def test_full_build_patch_items(self):
        from simulate_support_73 import FULL_BUILDS
        self.assertIn("Ardent Censer", FULL_BUILDS["lulu"].page)
        self.assertIn("Yordle Trap", FULL_BUILDS["leona"].page)
        self.assertIn("Echoes of Helia", FULL_BUILDS["milio"].page)
        self.assertIn("Yordle Trap", FULL_BUILDS["braum"].page)
        self.assertIn("Diadem of Songs", FULL_BUILDS["sona"].page)
        self.assertIn("Echoes of Helia", FULL_BUILDS["sona"].page)


if __name__ == "__main__":
    unittest.main()
