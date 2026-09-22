#!/usr/bin/env python3
"""Sanity checks for the 7.3 Kai'Sa on-hit page."""

import unittest

from simulate_kaisa_onhit import (
    AS_CAP,
    PAGE,
    PATHS,
    PATH_LABEL,
    ITEMS,
    gold_at_minute,
    level_at_minute,
    owned_at_gold,
    evolves,
    legendaries,
    skill_rank,
    snapshot,
    score_path,
    simulate_fight,
    squishy,
    tank,
    first_item_ready,
)


class TestKaisaOnhit(unittest.TestCase):
    def test_six_slot_page(self):
        self.assertEqual(len(PAGE["page"]), 6)
        for item in (
            "Kraken Slayer",
            "Berserker's Greaves",
            "Guinsoo's Rageblade",
            "Terminus",
            "Nashor's Tooth",
            "Zhonya's Hourglass",
        ):
            self.assertIn(item, PAGE["page"])

    def test_buy_starts_long_sword_kraken(self):
        self.assertEqual(PAGE["buy"][0], "Long Sword")
        self.assertEqual(PAGE["buy"][2], "Kraken Slayer")
        self.assertEqual(PATHS["kraken"][2], "kraken_slayer")

    def test_evolve_on_legendary_complete(self):
        path = PATHS["kraken"]
        owned = owned_at_gold(path, gold_at_minute(8))
        self.assertGreaterEqual(len(legendaries(owned)), 1)
        self.assertTrue(evolves(owned)["Q"])
        self.assertFalse(evolves(owned)["E"])
        owned = owned_at_gold(path, gold_at_minute(12))
        self.assertTrue(evolves(owned)["E"])
        owned = owned_at_gold(path, gold_at_minute(16))
        self.assertTrue(evolves(owned)["W"])

    def test_kraken_first_ready_by_8(self):
        self.assertEqual(first_item_ready("kraken"), 8)
        self.assertGreater(first_item_ready("statikk"), first_item_ready("kraken"))
        self.assertGreater(first_item_ready("botrk"), first_item_ready("kraken"))

    def test_one_v_one_winner_is_kraken(self):
        scores = {k: score_path(k) for k in ("kraken", "statikk", "botrk")}
        self.assertEqual(max(scores, key=scores.get), "kraken")

    def test_statikk_wins_teamfight_splash(self):
        shiv = snapshot("statikk", 16, 2)
        krak = snapshot("kraken", 16, 2)
        self.assertGreater(shiv["splash"], 0)
        self.assertEqual(krak["splash"], 0)
        self.assertGreater(shiv["squishy"] + shiv["splash"], krak["squishy"] + krak["splash"])

    def test_nashor_fourth_beats_botrk_dps(self):
        nash = snapshot("kraken", 20, 0)
        bork = snapshot("kraken_bork4", 20, 0)
        self.assertIn("Nashor's Tooth", nash["owned"])
        self.assertGreaterEqual(nash["tank"], bork["tank"])
        self.assertGreaterEqual(nash["squishy"], bork["squishy"])

    def test_as_cap(self):
        owned = owned_at_gold(PATHS["kraken"], gold_at_minute(24))
        r = simulate_fight(owned, 24, squishy(24))
        self.assertLessEqual(r.as_peak, AS_CAP + 1e-6)
        self.assertLessEqual(r.as_avg, AS_CAP + 1e-6)

    def test_plasma_pops(self):
        owned = owned_at_gold(PATHS["kraken"], gold_at_minute(12))
        r = simulate_fight(owned, 12, tank(12))
        self.assertGreaterEqual(r.plasma_pops, 1)
        self.assertGreater(r.autos, 4)

    def test_skill_order_q_then_e(self):
        self.assertGreater(skill_rank(7, "Q"), skill_rank(7, "E"))
        self.assertGreater(skill_rank(8, "E"), skill_rank(8, "W"))
        self.assertEqual(skill_rank(5, "R"), 1)
        self.assertIn("Q > E > W", PAGE["skill"])
        self.assertIn("Q rồi E rồi W", PAGE["evolve"])

    def test_runes_spells_pad(self):
        self.assertEqual(PAGE["runes"][0], "Lethal Tempo")
        self.assertIn("Legend: Bloodline", PAGE["runes"])
        self.assertEqual(PAGE["spells"], "Flash + Ghost")
        for key in ("L1", "L2", "L3", "L4", "A"):
            self.assertIn(key, PAGE["pad"])
        self.assertIn("GIỮ", PAGE["pad"]["L3"])

    def test_full_build_by_24(self):
        owned = owned_at_gold(PATHS["kraken"], gold_at_minute(24))
        names = [ITEMS[i]["name"] for i in owned]
        self.assertIn("Zhonya's Hourglass", names)
        self.assertEqual(len(legendaries(owned)), 5)

    def test_labels_cover_paths(self):
        for k in PATHS:
            self.assertIn(k, PATH_LABEL)
        self.assertEqual(level_at_minute(20), 15)


if __name__ == "__main__":
    unittest.main()
