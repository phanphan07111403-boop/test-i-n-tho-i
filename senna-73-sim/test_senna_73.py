#!/usr/bin/env python3
"""Sanity checks for the Wild Rift 7.3 Senna ADC/support sim."""

import unittest

from simulate_senna_73 import (
    ADC_PATHS,
    AS_RATIO,
    BASE_AD,
    BASE_HP,
    BASE_AS,
    ITEMS,
    MIST_CRIT,
    REMOVED_7_3,
    SENNA_CRIT_FACTOR,
    SUP_PATHS,
    area,
    first_legendary_minute,
    mist_at,
    owned_at_gold,
    q_damage,
    senna_as,
    snapshot,
    support_gold,
    adc_gold,
    scoreboard,
)


class TestSenna73(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.adc_rank = scoreboard("adc")
        cls.sup_rank = scoreboard("support")
        cls.adc_win = cls.adc_rank[0][0]
        cls.sup_win = cls.sup_rank[0][0]

    def test_magnetic_and_cloak_are_gone(self):
        names = {it["name"] for it in ITEMS.values()}
        for banned in REMOVED_7_3:
            self.assertNotIn(banned, names)
        blob = " ".join(names).lower()
        self.assertNotIn("magnetic", blob)
        self.assertNotIn("cloak of agility", blob)

    def test_7_3_kit_numbers(self):
        self.assertEqual(AS_RATIO, 0.40)
        self.assertEqual(BASE_AS, 0.40)
        self.assertEqual(BASE_AD, 50.0)
        self.assertEqual(BASE_HP, 570.0)
        self.assertEqual(MIST_CRIT, 0.10)
        self.assertEqual(SENNA_CRIT_FACTOR, 0.90)
        self.assertEqual(q_damage(1, 0.0), 50.0)
        self.assertEqual(q_damage(4, 0.0), 140.0)

    def test_as_ratio_actually_converts(self):
        # Old ratio ~0.125 made 35% Berserkers into +0.04 AS. 0.4 ratio → +0.14.
        bare = senna_as(1, 0.0)
        with_boot = senna_as(1, 0.35)
        self.assertAlmostEqual(bare, 0.64, places=2)
        self.assertGreater(with_boot - bare, 0.12)

    def test_auto_crit_is_90_percent_of_200(self):
        self.assertAlmostEqual(SENNA_CRIT_FACTOR * 2.0, 1.80, places=2)
        self.assertAlmostEqual(SENNA_CRIT_FACTOR * 2.30, 2.07, places=2)

    def test_adc_winner_is_youmuu_then_hex(self):
        self.assertEqual(self.adc_win, "youmuu_col_hex_ie_ldr")
        s8 = snapshot("adc", self.adc_win, 8)
        s16 = snapshot("adc", self.adc_win, 16)
        s24 = snapshot("adc", self.adc_win, 24)
        self.assertIn("Youmuu's Ghostblade", s8["owned"])
        self.assertNotIn("Hexoptics C44", s8["owned"])
        self.assertIn("The Collector", snapshot("adc", self.adc_win, 12)["owned"])
        self.assertIn("Hexoptics C44", s16["owned"])
        self.assertIn("Infinity Edge", s24["owned"])
        self.assertIn("Boots of Dynamism", s24["owned"])

    def test_support_winner_is_hex_then_mortal_or_er(self):
        self.assertIn(self.sup_win, ("hex_mortal_rfc", "hex_er_rfc"))
        s12 = snapshot("support", self.sup_win, 12)
        s20 = snapshot("support", self.sup_win, 20)
        self.assertIn("Hexoptics C44", s12["owned"])
        self.assertIn("Black Mist Scythe", s20["owned"])
        self.assertTrue(
            "Mortal Reminder" in s20["owned"] or "Essence Reaver" in s20["owned"]
        )
        self.assertLessEqual(s20["legendaries"], 2)

    def test_hex_first_loses_on_adc(self):
        scores = dict(self.adc_rank)
        self.assertGreater(scores[self.adc_win], scores["hex_col_ie_ldr_bt"])
        self.assertGreater(scores[self.adc_win], scores["hex_ie_rfc_ldr_bt"])

    def test_yun_tal_and_statikk_rfc_are_traps(self):
        scores = dict(self.adc_rank)
        self.assertLess(scores["yun_ie_rfc_ldr_bt"] / scores[self.adc_win], 0.90)
        self.assertLess(scores["statikk_rfc_ie_ldr"] / scores[self.adc_win], 0.90)
        self.assertLess(scores["storm_ie_rfc_ldr_bt"] / scores[self.adc_win], 0.90)

    def test_ie_second_is_a_hole(self):
        scores = dict(self.adc_rank)
        self.assertLess(scores["hex_ie_rfc_ldr_bt"], scores["hex_col_ie_ldr_bt"])
        ie = snapshot("adc", "hex_ie_rfc_ldr_bt", 12)
        col = snapshot("adc", "hex_col_ie_ldr_bt", 12)
        self.assertNotIn("Infinity Edge", ie["owned"])
        self.assertIn("The Collector", col["owned"])
        self.assertGreater(col["sq_dmg"], ie["sq_dmg"])

    def test_buy_order_does_not_skip_holes(self):
        # IE is before RFC. At 16:00 IE does not fit, so RFC must not sneak in.
        owned = owned_at_gold(
            ADC_PATHS["youmuu_hex_ie_rfc_ldr"], adc_gold(16), 16, "adc"
        )
        names = [ITEMS[i]["name"] for i in owned]
        self.assertNotIn("Infinity Edge", names)
        self.assertNotIn("Rapid Firecannon", names)

    def test_mist_crit_is_10_not_15(self):
        self.assertEqual(int(mist_at(8, "adc") // 20) * 10, 10)
        self.assertLess(mist_at(24, "adc"), 180.0)
        self.assertLess(mist_at(20, "support"), 85.0)

    def test_support_gold_cannot_triple_legendary(self):
        self.assertLess(support_gold(20), 11000)
        self.assertGreater(adc_gold(24), support_gold(20))
        s = snapshot("support", self.sup_win, 20)
        self.assertLessEqual(s["legendaries"], 2)

    def test_first_legendary_timing(self):
        self.assertLessEqual(first_legendary_minute("adc", self.adc_win), 8)
        self.assertLessEqual(first_legendary_minute("support", self.sup_win), 11)

    def test_no_path_buys_removed_items(self):
        for paths in (ADC_PATHS, SUP_PATHS):
            for steps in paths.values():
                for iid in steps:
                    self.assertIn(iid, ITEMS)
                    self.assertNotIn("magnetic", iid)


if __name__ == "__main__":
    unittest.main()
