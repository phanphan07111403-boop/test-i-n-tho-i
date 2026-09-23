#!/usr/bin/env python3
"""Sanity checks for the Wild Rift 7.3 Sona buff gold-efficiency sim."""

from __future__ import annotations

import unittest

from simulate_sona_73 import (
    CRIT_73,
    GAME_MINUTES,
    ITEMS,
    LEGENDARIES,
    MAX_SLOTS,
    RUNE_PAGES,
    SCYTHE_SELL,
    adc_base,
    auto_dps,
    compare_runes,
    evaluate,
    finished_legendaries,
    flags_from,
    gold_at_minute,
    harmony_hsp,
    isolated_item_ge,
    search,
    search_full,
    simulate_core,
    support_level,
    transcendence_ah,
)


class TestPatch73Items(unittest.TestCase):
    def test_ardent_cost_and_stats(self) -> None:
        a = ITEMS["Ardent Censer"]
        self.assertEqual(a.cost, 2400)
        self.assertEqual(a.ap, 50)
        self.assertEqual(a.hsp, 0.08)
        self.assertEqual(a.ah, 0)  # 7.3 removed AH / HP

    def test_helia_and_circlet_are_new(self) -> None:
        self.assertEqual(ITEMS["Echoes of Helia"].cost, 2400)
        self.assertEqual(ITEMS["Echoes of Helia"].ah, 20)
        self.assertEqual(ITEMS["Whispering Circlet"].cost, 2400)
        self.assertEqual(ITEMS["Diadem of Songs"].mana, 1200)

    def test_forbidden_idol_specialized(self) -> None:
        idol = ITEMS["Forbidden Idol"]
        self.assertEqual(idol.cost, 700)
        self.assertEqual(idol.hsp, 0.06)
        self.assertEqual(idol.ah, 0)
        self.assertEqual(idol.hp, 0)

    def test_harmony_hsp(self) -> None:
        self.assertAlmostEqual(harmony_hsp(500), 0.025, places=4)
        self.assertAlmostEqual(harmony_hsp(1200), 0.06, places=4)


class TestEconomy(unittest.TestCase):
    def test_gold_monotonic(self) -> None:
        prev = gold_at_minute(0)
        for m in range(1, GAME_MINUTES + 1):
            g = gold_at_minute(m)
            self.assertGreater(g, prev)
            prev = g
        self.assertGreater(gold_at_minute(20), 9000)
        self.assertGreater(gold_at_minute(28), 13000)

    def test_support_level_curve(self) -> None:
        self.assertEqual(support_level(1), 2)
        self.assertEqual(support_level(6), 7)
        self.assertLessEqual(support_level(20), 15)
        self.assertLessEqual(support_level(28), 17)


class TestShop(unittest.TestCase):
    def test_sickle_bought_minute_one(self) -> None:
        snaps = simulate_core(
            ["Ardent Censer", "Echoes of Helia", "Imperial Mandate"]
        )
        self.assertIn("Spectral Sickle", snaps[0].items)
        self.assertGreaterEqual(snaps[0].spent, 400)

    def test_spent_never_exceeds_gold(self) -> None:
        snaps = simulate_core(
            ["Ardent Censer", "Echoes of Helia", "Harmonic Echo"]
        )
        for s in snaps:
            self.assertLessEqual(s.spent, s.gold + 50)  # rounding / quest

    def test_ardent_comes_online_in_lane(self) -> None:
        snaps = simulate_core(
            ["Ardent Censer", "Echoes of Helia", "Imperial Mandate"]
        )
        ardent_m = next(s.minute for s in snaps if "Ardent Censer" in s.items)
        self.assertLessEqual(ardent_m, 10)

    def test_scythe_quest_at_five(self) -> None:
        snaps = simulate_core(
            ["Ardent Censer", "Echoes of Helia", "Imperial Mandate"]
        )
        self.assertIn("Black Mist Scythe", snaps[4].items)


class TestCombat(unittest.TestCase):
    def test_ardent_beats_staff_buff_ge_vs_crit_adc(self) -> None:
        iso = {r["item"]: r for r in isolated_item_ge(12)}
        self.assertGreater(iso["Ardent Censer"]["buff_ge"], iso["Staff of Flowing Waters"]["buff_ge"])
        self.assertGreater(iso["Ardent Censer"]["total_ge"], iso["Echoes of Helia"]["total_ge"])

    def test_crit_200_raises_ardent_value(self) -> None:
        owned = ["Black Mist Scythe", "Ionian Boots of Lucidity", "Ardent Censer"]
        snap = evaluate(owned, 14, 3700)
        self.assertGreater(snap.ardent_dps, 0)
        self.assertGreater(snap.extra_adc_dps, snap.extra_adc_dps_72)

    def test_helia_stores_damage(self) -> None:
        owned = ["Black Mist Scythe", "Ionian Boots of Lucidity", "Echoes of Helia"]
        snap = evaluate(owned, 12, 3700)
        self.assertGreater(snap.helia_hps, 10)
        f = flags_from(owned)
        self.assertTrue(f["helia"])

    def test_adc_yun_tal_then_ie(self) -> None:
        ad, aspd, crit, crit_dmg, items = adc_base(16)
        self.assertIn("Yun Tal Wildarrows", items)
        self.assertGreaterEqual(crit_dmg, CRIT_73)
        self.assertGreater(auto_dps(ad, aspd, crit, 0, crit_dmg, 3.0), 100)


class TestSearch(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.scored, cls.results = search()

    def test_searches_all_three_item_orders(self) -> None:
        self.assertEqual(len(self.scored), 210)

    def test_winner_rushes_ardent(self) -> None:
        winner = self.scored[0]
        self.assertEqual(winner["core"][0], "Ardent Censer")
        self.assertEqual(winner["core"][1], "Echoes of Helia")

    def test_winner_beats_staff_first(self) -> None:
        winner = self.scored[0]
        staff_first = next(r for r in self.scored if r["core"][0] == "Staff of Flowing Waters")
        self.assertGreater(winner["combined"], staff_first["combined"])
        self.assertGreater(winner["tw_ge"], staff_first["tw_ge"])

    def test_mandate_first_is_a_trap(self) -> None:
        winner = self.scored[0]
        mandate_first = next(r for r in self.scored if r["core"][0] == "Imperial Mandate")
        rank = next(i for i, r in enumerate(self.scored, 1) if r is mandate_first)
        self.assertGreaterEqual(rank, 20)
        self.assertGreater(winner["tw_impact"], mandate_first["tw_impact"])

    def test_top_paths_share_ardent_helia(self) -> None:
        winner = self.scored[0]
        self.assertEqual(tuple(winner["core"][:2]), ("Ardent Censer", "Echoes of Helia"))
        top = [tuple(r["core"][:2]) for r in self.scored[:2]]
        self.assertTrue(all(p[0] == "Ardent Censer" for p in top))

    def test_legendaries_pool(self) -> None:
        self.assertEqual(len(LEGENDARIES), 7)


class TestFullPage(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.snaps = simulate_core(
            [
                "Ardent Censer",
                "Echoes of Helia",
                "Imperial Mandate",
                "Harmonic Echo",
                "Redemption",
            ]
        )
        cls.scored, _ = search_full(["Ardent Censer", "Echoes of Helia"])

    def test_never_exceeds_six_slots(self) -> None:
        for s in self.snaps:
            self.assertLessEqual(len(s.items), MAX_SLOTS, s.items)

    def test_fourth_legendary_completes(self) -> None:
        fourth_m = next(
            (s.minute for s in self.snaps if finished_legendaries(s.items) >= 4),
            None,
        )
        self.assertIsNotNone(fourth_m)
        self.assertLessEqual(fourth_m, 26)

    def test_sells_scythe_for_fifth(self) -> None:
        sold = next((s for s in self.snaps if "sold Scythe" in s.notes), None)
        self.assertIsNotNone(sold)
        self.assertNotIn("Black Mist Scythe", sold.items)
        self.assertGreaterEqual(finished_legendaries(self.snaps[-1].items), 5)

    def test_scythe_sell_value(self) -> None:
        self.assertEqual(SCYTHE_SELL, 280)

    def test_full_search_locks_ardent_helia(self) -> None:
        winner = self.scored[0]
        self.assertEqual(winner["core"][0], "Ardent Censer")
        self.assertEqual(winner["core"][1], "Echoes of Helia")
        self.assertEqual(len(winner["core"]), 5)
        self.assertTrue(winner["sold"])
        self.assertEqual(winner["n_leg"], 5)

    def test_full_search_size(self) -> None:
        self.assertEqual(len(self.scored), 60)


class TestRunes(unittest.TestCase):
    """Rune pages ranked on the winning item path, not a generic Sona template."""

    WIN_CORE = [
        "Ardent Censer",
        "Echoes of Helia",
        "Imperial Mandate",
        "Harmonic Echo",
        "Staff of Flowing Waters",
    ]

    @classmethod
    def setUpClass(cls) -> None:
        cls.ranked = compare_runes(cls.WIN_CORE)

    def test_compares_every_page(self) -> None:
        self.assertEqual(len(self.ranked), len(RUNE_PAGES))
        self.assertEqual(len(RUNE_PAGES), 9)

    def test_aery_beats_guardian_comet_fleet(self) -> None:
        winner = self.ranked[0]
        self.assertEqual(winner["keystone"], "Aery")
        for ks in ("Guardian", "Arcane Comet", "Fleet Footwork"):
            other = next(r for r in self.ranked if r["keystone"] == ks)
            self.assertGreater(
                winner["combined"],
                other["combined"],
                f"{winner['name']} should beat {other['name']}",
            )

    def test_winner_has_revitalize_and_transcendence(self) -> None:
        winner = self.ranked[0]
        self.assertTrue(winner["revitalize"])
        self.assertTrue(winner["transcendence"])
        self.assertIn("Revitalize", winner["slots"])
        self.assertIn("Transcendence", winner["slots"])

    def test_transcendence_beats_legend_haste(self) -> None:
        trans = next(
            r
            for r in self.ranked
            if r["name"] == "Aery / FoL / Bone / Revitalize / Transcendence"
        )
        legend = next(
            r
            for r in self.ranked
            if r["name"] == "Aery / FoL / Bone / Revitalize / Legend: Haste"
        )
        self.assertGreater(trans["combined"], legend["combined"])
        self.assertGreater(trans["tw_ge"], legend["tw_ge"])

    def test_revitalize_beats_dropping_it(self) -> None:
        with_r = next(
            r
            for r in self.ranked
            if r["name"] == "Aery / FoL / Bone / Revitalize / Transcendence"
        )
        without = next(
            r
            for r in self.ranked
            if r["name"] == "Aery / FoL / Bone / Transcendence / Manaflow"
        )
        self.assertGreater(with_r["combined"], without["combined"])

    def test_transcendence_adds_ah(self) -> None:
        trans = next(p for p in RUNE_PAGES if p.transcendence and p.revitalize)
        mana = next(
            p
            for p in RUNE_PAGES
            if p.manaflow and p.revitalize and not p.transcendence and not p.legend_haste
        )
        owned = ["Black Mist Scythe", "Ionian Boots of Lucidity", "Ardent Censer"]
        s_t = evaluate(owned, 12, 3700, trans)
        s_m = evaluate(owned, 12, 3700, mana)
        self.assertGreater(s_t.ah, s_m.ah)
        self.assertGreaterEqual(s_t.hsp, 0.05)
        self.assertEqual(transcendence_ah(11), 20.0)


if __name__ == "__main__":
    unittest.main()
