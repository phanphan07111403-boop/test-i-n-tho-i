#!/usr/bin/env python3
"""Sanity checks for the Wild Rift 7.3 Braum support full-build + rune sim."""

from simulate_braum_73 import (
    BUILD_PATHS,
    ITEMS,
    PAGES,
    ROW1,
    ROW2,
    ROW3,
    UPGRADE_COMPONENTS,
    compute_snapshot,
    gold_at_minute,
    level_at_minute,
    resolve_inventory,
    skill_rank,
    yordle_procs,
)


def test_yordle_catcher_on_q_slow():
    assert yordle_procs(True, 1, False)
    assert yordle_procs(True, 0, True)
    assert not yordle_procs(True, 0, False)
    assert not yordle_procs(False, 3, True)


def test_aftershock_gone_and_pages_legal():
    keys = {p.keystone for p in PAGES}
    assert "Aftershock" not in keys
    assert "Guardian" in keys
    assert "Ice Overlord" in keys
    assert "Grasp" in keys
    for page in PAGES:
        assert len(page.runes) == 3
        assert page.secondary
        assert page.primary == "Resolve"
        assert "Ingenious Hunter" not in page.runes
        assert page.secondary != "Ingenious Hunter"
        assert page.runes[0] in ROW1
        assert page.runes[1] in ROW2
        assert page.runes[2] in ROW3
        assert len(set(page.runes)) == 3


def test_73_item_costs_and_carts():
    assert ITEMS["Knight's Vow"].cost == 2450
    assert ITEMS["Yordle Trap"].cost == 2400
    assert ITEMS["Zeke's Convergence"].cost == 2400
    assert ITEMS["Locket of the Iron Solari"].cost == 2600
    assert ITEMS["Radiant Virtue"].cost == 2650
    assert ITEMS["Frozen Heart"].cost == 2550
    assert ITEMS["Redemption"].cost == 2450
    assert ITEMS["Plated Steelcaps"].cost == 1200
    assert ITEMS["Plated Steelcaps"].aa_red == 0.10
    assert ITEMS["Plated Steelcaps"].hp == 150
    # Virtue split from Vow's Kindlegem + Vest cart.
    assert "Kindlegem" not in UPGRADE_COMPONENTS["Radiant Virtue"]
    assert set(UPGRADE_COMPONENTS["Radiant Virtue"]) == {
        "Cloth Armor",
        "Null-Magic Mantle",
        "Giant's Belt",
    }
    # Locket / Zeke / Yordle share Kindlegem + Cloth + Null.
    shared = ("Kindlegem", "Cloth Armor", "Null-Magic Mantle")
    for name in ("Locket of the Iron Solari", "Zeke's Convergence", "Yordle Trap"):
        assert UPGRADE_COMPONENTS[name] == shared


def test_wr_ult_at_five():
    assert level_at_minute(4) == 5
    assert skill_rank(5, "R") == 1
    assert skill_rank(4, "R") == 0
    assert skill_rank(9, "R") == 2
    assert skill_rank(13, "R") == 3
    assert skill_rank(7, "Q") == 4


def test_support_gold_curve():
    assert 8500 < gold_at_minute(20) < 11500
    assert gold_at_minute(10) < gold_at_minute(16) < gold_at_minute(20)


def test_yordle_online_catcher_without_needing_r_in_notes():
    path = BUILD_PATHS["Yordle → Vow → FH"]
    page = PAGES[0]
    found = False
    for m in range(8, 16):
        s = compute_snapshot("y", path, m, page)
        if s.has_yordle:
            assert s.catcher_this_fight
            assert "Catcher on Q" in s.notes
            found = True
            break
    assert found


def test_frozen_heart_aura_not_r_gated():
    path = BUILD_PATHS["FH → Vow → Locket"]
    page = PAGES[0]
    s = compute_snapshot("fh", path, 12, page)
    assert s.has_fh
    assert "FH 25% AS" in s.notes


def test_single_boot_and_bulwark_quest():
    names = resolve_inventory(
        BUILD_PATHS["Locket → Vow → FH"],
        gold_at_minute(11),
        11,
    )
    assert "Bulwark of the Mountain" in names
    assert "Relic Shield" not in names
    boots = [n for n in names if n in (
        "Boots of Speed", "Plated Steelcaps", "Mercury's Treads", "Armored Advance"
    )]
    assert len(boots) <= 1


def test_guardian_beats_grasp_on_peel():
    path = BUILD_PATHS["Locket → Vow → FH"]
    g = next(p for p in PAGES if p.keystone == "Guardian")
    grasp = next(p for p in PAGES if p.keystone == "Grasp")
    sg = compute_snapshot("g", path, 12, g)
    sgr = compute_snapshot("gr", path, 12, grasp)
    assert sg.peel_score > sgr.peel_score


def test_vow_redirect_lowers_adc_taken():
    path_vow = BUILD_PATHS["Vow → Locket → FH"]
    path_y = BUILD_PATHS["Yordle → Locket → Vow"]
    page = PAGES[0]
    v = compute_snapshot("v", path_vow, 12, page)
    y = compute_snapshot("y", path_y, 12, page)
    # At 12:00 Vow rush should have Vow; Yordle rush often does not.
    if v.has_vow and not y.has_vow:
        assert v.adc_taken < y.adc_taken


if __name__ == "__main__":
    tests = [v for k, v in globals().items() if k.startswith("test_")]
    for fn in tests:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"{len(tests)} passed")
