#!/usr/bin/env python3
"""Sanity checks for the Wild Rift 7.3 Volibear W-spam heal/shield sim."""

from simulate_volibear_wspam import (
    FIGHT_S,
    ITEMS,
    PAGES,
    PATHS,
    extra_bite_ah_needed,
    fight_at,
    gold_at_minute,
    inventory_at_gold,
    level_at_minute,
    n_w_bites,
    path_by_name,
    skill_rank,
    w_cast_times,
    w_cooldown,
    weighted_identity,
    weighted_sustain,
)


def test_spirit_visage_removed():
    assert "Spirit Visage" not in ITEMS


def test_w_cadence_and_frenzy_bites():
    assert abs(w_cooldown(0) - 5.0) < 1e-9
    assert abs(w_cooldown(25) - 4.0) < 1e-9
    # 4th W / 3rd bite needs ~27.7 AH in a 12s window.
    assert 26.0 < extra_bite_ah_needed() < 29.0
    t0 = w_cast_times(0)
    t30 = w_cast_times(30)
    assert len(t0) == 3
    assert len(t30) == 4
    assert n_w_bites(3) == 2
    assert n_w_bites(4) == 3
    assert n_w_bites(1) == 0


def test_skill_order_w_max_r_at_five():
    assert skill_rank(1, "W") == 1
    assert skill_rank(4, "W") == 2
    assert skill_rank(4, "R") == 0
    assert skill_rank(5, "R") == 1
    assert skill_rank(9, "R") == 2
    assert skill_rank(13, "R") == 3
    assert level_at_minute(4) == 5


def test_baron_gold_curve():
    assert gold_at_minute(0) == 500
    assert gold_at_minute(10) < gold_at_minute(16) < gold_at_minute(22)
    assert 9000 < gold_at_minute(22) < 14000


def test_e_shield_is_percent_max_hp():
    path = path_by_name("Heart → Sterak → Despair")
    page = PAGES[0]
    f = fight_at(path, 14, page)
    # Stand-in-E shield is the bulk of pre-Sterak shielding.
    assert f.shield > 0.12 * f.hp
    assert "stand in E" in f.notes


def test_kindlegem_buys_the_extra_bite():
    path = path_by_name("Heart → Sterak → Despair")
    f8 = fight_at(path, 8, PAGES[0])
    f14 = fight_at(path, 14, PAGES[0])
    assert f8.w_casts == 3
    assert f14.w_casts == 4
    assert f14.w_bites == 3
    assert any("Kindlegem" in n or "Hỏa Ngọc" in n for n in f14.items)
    assert f14.ah >= 28


def test_kindlegem_is_hoa_ngoc_mid_tier():
    k = ITEMS["Kindlegem"]
    assert k.name == "Hỏa Ngọc (Kindlegem)"
    assert k.cost == 1000
    assert k.ah == 10
    assert k.hp == 175


def test_winner_is_heart_sterak_not_duelist_or_trinity():
    ranked = sorted(PATHS, key=weighted_identity, reverse=True)
    winner = ranked[0]
    assert winner.legendaries[0] == "Heartsteel"
    assert winner.legendaries[1] == "Sterak's Gage"
    assert "Trinity Force" not in winner.legendaries[:2]
    dusk = path_by_name("Dusk → Hull → Rift")
    assert weighted_sustain(winner) > weighted_sustain(dusk)
    f14w = fight_at(winner, 14, PAGES[0])
    f14d = fight_at(dusk, 14, PAGES[0])
    assert f14w.sustain > f14d.sustain
    f22w = fight_at(winner, 22, PAGES[0])
    f22d = fight_at(dusk, 22, PAGES[0])
    assert f22w.sustain > f22d.sustain
    assert f22w.w_bites >= 3


def test_runes_are_legal_73_pages():
    for page in PAGES:
        assert len(page.resolve) == 3
        assert page.secondary
        assert "Ingenious Hunter" not in page.resolve
        assert page.secondary != "Ingenious Hunter"
        assert page.keystone != "Aftershock"
        assert len(set(page.resolve)) == 3


def test_grasp_revitalize_beats_tempo_and_no_hsp():
    shop = path_by_name("Heart → Sterak → Despair")
    grasp = next(p for p in PAGES if p.name == "Grasp / Revitalize / Overgrowth")
    none = next(p for p in PAGES if p.name == "Grasp / no Revitalize")
    tempo = next(p for p in PAGES if p.keystone == "Lethal Tempo")
    assert weighted_sustain(shop, grasp) > weighted_sustain(shop, none)
    assert weighted_identity(shop, grasp) > weighted_identity(shop, tempo)
    g14 = fight_at(shop, 14, grasp)
    t14 = fight_at(shop, 14, tempo)
    assert g14.heal > t14.heal


def test_heartsteel_online_before_ten():
    path = path_by_name("Heart → Sterak → Despair")
    found = False
    for m in range(5, 10):
        names = [i.name for i in inventory_at_gold(path, gold_at_minute(m))]
        if "Heartsteel" in names:
            found = True
            break
    assert found


def test_despair_and_sterak_costs():
    assert ITEMS["Heartsteel"].cost == 2800
    assert ITEMS["Heartsteel"].hp == 700
    assert ITEMS["Unending Despair"].cost == 3000
    assert ITEMS["Unending Despair"].despair
    assert ITEMS["Sterak's Gage"].cost == 3200
    assert ITEMS["Sterak's Gage"].sterak
    assert ITEMS["Trinity Force"].cost == 3333
    assert ITEMS["Kindlegem"].ah == 10
    assert ITEMS["Kindlegem"].name.startswith("Hỏa Ngọc")


def test_fight_window():
    assert FIGHT_S == 12.0
    last = w_cast_times(30)[-1]
    assert last + 0.25 <= FIGHT_S + 1e-9


if __name__ == "__main__":
    tests = [v for k, v in globals().items() if k.startswith("test_")]
    for fn in tests:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"{len(tests)} passed")
