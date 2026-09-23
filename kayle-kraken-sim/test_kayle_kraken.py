#!/usr/bin/env python3
"""Sanity checks: 7.3 Kayle — Kraken first vs WRF AP."""

import unittest

from simulate_kayle_kraken import (
    AS_CAP,
    PAGE,
    PATHS,
    PATH_LABEL,
    ITEMS,
    gold_at_minute,
    owned_at_gold,
    first_item_ready,
    legendaries,
    skill_rank,
    snapshot,
    score_path,
    simulate_fight,
    squishy,
    tank,
    level_at_minute,
)


class TestKayleKraken(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scores = {k: score_path(k) for k in PATHS}
        cls.winner = max(cls.scores, key=cls.scores.get)

    def test_six_slot_ap_page(self):
        self.assertEqual(len(PAGE["page"]), 6)
        self.assertEqual(PAGE["page"][0], "Nashor's Tooth")
        self.assertIn("Dusk and Dawn", PAGE["page"])
        self.assertIn("Rabadon's Deathcap", PAGE["page"])
        self.assertNotIn("Kraken Slayer", PAGE["page"])

    def test_buy_starts_tome_nashor(self):
        self.assertEqual(PAGE["buy"][0], "Amplifying Tome")
        self.assertEqual(PAGE["buy"][2], "Nashor's Tooth")
        self.assertEqual(PAGE["buy"][3], "Dusk and Dawn")

    def test_winner_is_ap(self):
        self.assertEqual(self.winner, "ap")
        self.assertGreater(self.scores["ap"], self.scores["kraken"])
        self.assertGreater(self.scores["ap"], self.scores["nashor_kraken"])
        self.assertGreater(self.scores["ap"], self.scores["kraken_ap"])

    def test_nashor_ready_by_8(self):
        self.assertLessEqual(first_item_ready("ap"), 8)
        owned = owned_at_gold(PATHS["ap"], gold_at_minute(8))
        self.assertIn("nashors_tooth", owned)
        self.assertNotIn("amplifying_tome", owned)

    def test_kraken_first_also_ready_by_8(self):
        self.assertLessEqual(first_item_ready("kraken"), 8)
        owned = owned_at_gold(PATHS["kraken"], gold_at_minute(8))
        self.assertIn("kraken_slayer", owned)

    def test_kraken_wins_midgame_8s_then_ap_overtakes(self):
        k8 = snapshot("kraken", 8)
        a8 = snapshot("ap", 8)
        self.assertGreater(k8["sq_dps"], a8["sq_dps"])
        k24 = snapshot("kraken", 24)
        a24 = snapshot("ap", 24)
        self.assertGreater(a24["sq_dps"], k24["sq_dps"])
        self.assertGreater(a24["tk_dps"], k24["tk_dps"])
        self.assertIn("Infinity Orb", a24["owned"])
        self.assertIn("Rabadon's Deathcap", a24["owned"])

    def test_dusk_ready_by_12(self):
        s = snapshot("ap", 12)
        self.assertIn("Dusk and Dawn", s["owned"])
        self.assertIn("Nashor's Tooth", s["owned"])

    def test_deathcap_ready_by_16(self):
        s = snapshot("ap", 16)
        self.assertIn("Rabadon's Deathcap", s["owned"])
        self.assertGreaterEqual(s["ap"], 250)

    def test_kraken_second_loses_to_kraken_rush(self):
        self.assertLess(self.scores["nashor_kraken"], self.scores["kraken"])

    def test_hybrid_loses_to_ap(self):
        self.assertLess(self.scores["kraken_ap"], self.scores["ap"])

    def test_ranged_from_level_5(self):
        self.assertFalse(level_at_minute(3) >= 5)
        self.assertTrue(level_at_minute(4) >= 5)
        s = snapshot("ap", 8)
        self.assertTrue(s["ranged"])

    def test_as_cap(self):
        owned = owned_at_gold(PATHS["kraken"], gold_at_minute(24))
        r = simulate_fight(owned, 24, squishy(24), False)
        self.assertLessEqual(r.as_peak, AS_CAP + 1e-6)
        self.assertLessEqual(r.as_avg, AS_CAP + 1e-6)

    def test_skill_e_then_q(self):
        self.assertGreater(skill_rank(7, "E"), skill_rank(7, "Q"))
        self.assertGreater(skill_rank(8, "Q"), skill_rank(8, "W"))
        self.assertEqual(skill_rank(5, "R"), 1)
        self.assertIn("E > Q > W", PAGE["skill"])

    def test_runes_spells_pad(self):
        self.assertEqual(PAGE["runes"][0], "Conqueror")
        self.assertEqual(PAGE["spells"], "Flash + Barrier")
        for key in ("L1", "L2", "L3", "L4", "A"):
            self.assertIn(key, PAGE["pad"])
        self.assertIn("heal", PAGE["pad"]["L2"].lower())
        self.assertIn("Q", PAGE["pad"]["L1"])

    def test_full_ap_by_24(self):
        owned = owned_at_gold(PATHS["ap"], gold_at_minute(24))
        self.assertEqual(len(legendaries(owned)), 5)
        names = [ITEMS[i]["name"] for i in owned]
        self.assertIn("Infinity Orb", names)
        self.assertIn("Void Staff", names)

    def test_labels_cover_paths(self):
        for k in PATHS:
            self.assertIn(k, PATH_LABEL)

    def test_gold_20_solo_curve(self):
        self.assertGreaterEqual(gold_at_minute(20), 12000)
        self.assertLess(gold_at_minute(20), 14500)

    def test_q_shred_helps_physical(self):
        owned = owned_at_gold(PATHS["kraken"], gold_at_minute(16))
        r = simulate_fight(owned, 16, tank(16), False)
        self.assertGreater(r.physical, 0)
        self.assertGreater(r.autos, 4)


if __name__ == "__main__":
    unittest.main()
