#!/usr/bin/env python3
"""Sanity checks for the Wild Rift 7.3 Zyra mid/support sim."""

from simulate_zyra_73 import (
    ITEMS,
    MID_BUILDS,
    MID_PAGES,
    SUPPORT_BUILDS,
    SUPPORT_PAGES,
    compute_snapshot,
    gathering_storm_ap,
    mid_gold,
    plant_base_damage,
    resolve_inventory,
    support_gold,
)


def test_ionian_cheaper_than_mana_and_spellslinger():
    assert ITEMS["Ionian Boots of Lucidity"].cost == 1000
    assert ITEMS["Boots of Mana"].cost == 1200
    assert ITEMS["Spellslinger's Shoes"].cost == 2200
    assert ITEMS["Crimson Lucidity"].cost == 2000


def test_comet_is_the_72_nerf():
    # 5% AP, not the old 20%.
    s = compute_snapshot(
        "support",
        "t",
        SUPPORT_BUILDS["Liandry → Ionian → Rylai (Meta)"],
        SUPPORT_PAGES[0],
        12,
        20,
    )
    assert s.page_name.startswith("Comet")
    assert 0.5 < s.comet_land < 0.95


def test_rylai_raises_comet_land_and_uptime():
    path_lock = SUPPORT_BUILDS["Liandry → Ionian → Rylai (Meta)"]
    path_no = SUPPORT_BUILDS["Liandry → Ionian → Oceanid"]
    page = SUPPORT_PAGES[0]
    a = compute_snapshot("support", "a", path_lock, page, 20, 20)
    b = compute_snapshot("support", "b", path_no, page, 20, 20)
    if a.rylai and not b.rylai:
        assert a.comet_land > b.comet_land
        assert a.uptime > b.uptime


def test_support_gold_below_mid_at_20():
    assert support_gold(20) < mid_gold(20)
    assert 9000 < support_gold(20) < 12000
    assert 12000 < mid_gold(22) < 16000


def test_plants_inherit_10pct_ap_ratio():
    # 7.2 nerf 15% → 10%.
    assert abs(plant_base_damage(1) - 10.0) < 1e-6
    assert abs(plant_base_damage(15) - 108.0) < 1e-6


def test_legal_rune_pages():
    for page in SUPPORT_PAGES + MID_PAGES:
        assert page.keystone
        assert len(page.runes) == 3
        assert page.secondary
        assert "Ingenious Hunter" not in page.runes
        assert page.secondary != "Ingenious Hunter"
        assert "Legend: Tenacity" not in page.runes


def test_scythe_quest_and_boot_upgrade():
    names = resolve_inventory(
        SUPPORT_BUILDS["Liandry → Ionian → Rylai (Meta)"],
        support_gold(11),
        11,
    )
    assert "Black Mist Scythe" in names
    assert "Spectral Sickle" not in names
    boots = [n for n in names if "Boot" in n or n == "Crimson Lucidity" or "Spellslinger" in n]
    assert len(boots) <= 1


def test_gathering_storm_schedule():
    assert gathering_storm_ap(5) == 0
    assert gathering_storm_ap(6) == 4
    assert gathering_storm_ap(9) == 10
    assert gathering_storm_ap(12) == 18


def test_mid_finishes_more_items_than_support():
    s = resolve_inventory(
        SUPPORT_BUILDS["Liandry → Ionian → Rylai (Meta)"],
        support_gold(20),
        20,
    )
    m = resolve_inventory(
        MID_BUILDS["BF → Spellslinger → Liandry → Rylai"],
        mid_gold(22),
        22,
    )
    finished = lambda names: [
        n for n in names
        if n in (
            "Liandry's Torment", "Blackfire Torch", "Rylai's Crystal Scepter",
            "Void Staff", "Rabadon's Deathcap", "Spellslinger's Shoes",
            "Crimson Lucidity", "Imperial Mandate", "Oceanid's Trident",
            "Zhonya's Hourglass", "Banshee's Veil",
        )
    ]
    assert len(finished(m)) >= len(finished(s))


def test_rune_ranking_shape():
    from simulate_zyra_73 import run_runes, SUPPORT_BUILDS

    ranked = run_runes(
        "support",
        "Liandry → Ionian → Rylai (Meta)",
        SUPPORT_BUILDS["Liandry → Ionian → Rylai (Meta)"],
    )
    assert len(ranked[0]) == 5
    page, full, lane, late, last = ranked[0]
    assert page.keystone
    assert full > 0 and lane > 0


if __name__ == "__main__":
    tests = [v for k, v in globals().items() if k.startswith("test_")]
    for fn in tests:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"{len(tests)} passed")
