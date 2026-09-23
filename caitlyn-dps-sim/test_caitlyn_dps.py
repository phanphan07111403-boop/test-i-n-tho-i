#!/usr/bin/env python3
"""Sanity checks for the 7.3 Caitlyn highest-damage buy order."""

import unittest

from simulate_caitlyn_dps import (
    AS_CAP,
    PAGE,
    PATHS,
    ITEMS,
    gold_at_minute,
    owned_at_gold,
    snapshot,
    score_path,
    simulate_fight,
    squishy,
    first_item_ready,
    COMPARE,
    skill_rank,
    headshot_bonus,
    CRIT_BASE,
)


class TestCaitlynDps(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scores = {k: score_path(k) for k in COMPARE}
        cls.winner = max(cls.scores, key=cls.scores.get)

    def test_six_slot_page(self):
        self.assertEqual(len(PAGE["page"]), 6)
        self.assertEqual(PAGE["page"][0], "Hexoptics C44")
        self.assertIn("Infinity Edge", PAGE["page"])
        self.assertIn("Bloodthirster", PAGE["page"])
        self.assertIn("Lord Dominik's Regards", PAGE["page"])

    def test_buy_order(self):
        self.assertEqual(PAGE["buy"][0], "Long Sword")
        self.assertEqual(PAGE["buy"][2], "Hexoptics C44")
        self.assertEqual(PAGE["buy"][3], "The Collector")
        self.assertEqual(PAGE["buy"][4], "Infinity Edge")
        ie = PAGE["buy"].index("Infinity Edge")
        self.assertGreater(ie, PAGE["buy"].index("Hexoptics C44"))

    def test_winner_is_hex_collector_ie(self):
        self.assertEqual(self.winner, "hex_col_ie_ldr_bt")

    def test_hex_first_ready_by_8(self):
        self.assertEqual(first_item_ready("hex_col_ie_ldr_bt"), 8)
        self.assertEqual(first_item_ready("wrf"), 8)

    def test_collector_second_beats_ie_hole_at_12(self):
        col = snapshot("hex_col_ie_ldr_bt", 12)
        ie = snapshot("wrf", 12)
        self.assertIn("The Collector", col["owned"])
        self.assertNotIn("Infinity Edge", ie["owned"])
        self.assertGreater(col["sq_dps"], ie["sq_dps"])
        self.assertGreaterEqual(col["crit"], 50)

    def test_full_build_100_crit_by_24(self):
        s = snapshot("hex_col_ie_ldr_bt", 24)
        self.assertEqual(s["crit"], 100)
        self.assertEqual(s["crit_dmg"], 230)
        self.assertIn("Bloodthirster", s["owned"])
        self.assertEqual(len([i for i in s["ids"] if ITEMS[i]["tier"] == "legendary"]), 5)

    def test_yun_tal_not_highest(self):
        self.assertLess(self.scores["yun_ie_rfc_ldr_bt"], self.scores[self.winner])
        self.assertLess(self.scores["col_ie_rfc_ldr_bt"], self.scores["wrf"])

    def test_overcap_collector_sixth_loses(self):
        self.assertLess(
            self.scores["hex_ie_rfc_ldr_col"],
            self.scores["wrf"],
        )

    def test_headshot_scales_ie(self):
        ad = 200.0
        no_ie = headshot_bonus(ad, 1.0, CRIT_BASE, 15)
        with_ie = headshot_bonus(ad, 1.0, 2.3, 15)
        self.assertGreater(with_ie, no_ie)

    def test_as_cap(self):
        owned = owned_at_gold(PATHS["wrf"], gold_at_minute(24))
        r = simulate_fight(owned, 24, squishy(24))
        self.assertLessEqual(r.as_peak, AS_CAP + 1e-6)

    def test_skill_q_then_w(self):
        self.assertGreater(skill_rank(7, "Q"), skill_rank(7, "W"))
        self.assertIn("Q > W > E", PAGE["skill"])

    def test_runes_spells_pad(self):
        self.assertEqual(PAGE["runes"][0], "Lethal Tempo")
        self.assertEqual(PAGE["spells"], "Flash + Ghost")
        for key in ("L1", "L2", "L3", "L4", "A"):
            self.assertIn(key, PAGE["pad"])

    def test_gold_20_matches_adc_curve(self):
        self.assertGreaterEqual(gold_at_minute(20), 13000)
        self.assertLess(gold_at_minute(20), 14000)

    def test_lt_wins_extended_teamfight(self):
        from simulate_caitlyn_dps import score_keystone, KEYSTONES
        ext = {k: score_keystone(k, "hex_col_ie_ldr_bt", False) for k in KEYSTONES}
        self.assertEqual(max(ext, key=ext.get), "lt")
        self.assertGreater(ext["lt"], ext["conqueror"])
        self.assertGreater(ext["lt"], ext["dark_harvest"])

    def test_first_strike_wins_3s_poke(self):
        lt = snapshot("hex_col_ie_ldr_bt", 12, "lt", True)
        fs = snapshot("hex_col_ie_ldr_bt", 12, "first_strike", True)
        self.assertGreater(fs["sq_3s"], lt["sq_3s"])

    def test_youmuu_first_then_crit_loses(self):
        y = snapshot("youmuu_hex_ie_rfc_ldr", 8)
        h = snapshot("hex_col_ie_ldr_bt", 8)
        self.assertEqual(y["crit"], 0)
        self.assertGreaterEqual(h["crit"], 25)
        self.assertIn("Youmuu's Ghostblade", y["owned"])
        self.assertLess(self.scores["youmuu_hex_ie_rfc_ldr"], self.scores[self.winner])
        s24 = snapshot("youmuu_hex_ie_rfc_ldr", 24)
        self.assertEqual(s24["crit"], 100)
        self.assertGreaterEqual(s24["lethality"], 15)


if __name__ == "__main__":
    unittest.main()
