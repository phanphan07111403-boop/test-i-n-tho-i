#!/usr/bin/env python3
"""
Wild Rift 7.3b — the Diadem / Helia / Harmonic support build with Liandry removed.

Question: which champion uses this build, and can a tank wear it?

Items: Black Mist Scythe, Ionian Boots, Whispering Circlet → Diadem of Songs,
Echoes of Helia, Harmonic Echo. No Liandry's Torment.

The items give ability power, mana, haste, heal/shield power, and some health.
They give no armor and no magic resist. A tank's resists have to come from
the champion, not from the shop list.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))

from compare_brand_zyra import brand_utility, zyra_utility  # noqa: E402
from optimize_component_path import walk_priority  # noqa: E402
from simulate_brand_support import (  # noqa: E402
    BASE_MANA,
    FIGHT_S,
    FIGHTERS,
    Fight,
    ability_ranks,
    carry_stats,
    evaluate,
    front_stats,
    gold_at_minute,
    helia_cap,
    helia_stored,
    level_at_minute,
    mitigate,
    ncast,
    rank_value,
    scythe_stacks,
    stats_from_names,
)

# Liandry's pieces are gone. Same early Circlet → Kindlegem → Helia order,
# then Harmonic, then Ionian in the gaps.
ORDER = (
    "ruby_c", "tear", "idol", "circlet",
    "ruby_kh", "kg_h",
    "tome_bh", "ring_bh", "bg_h", "helia",
    "tome_br", "ring_br", "ruby_kr", "kg_r", "bg_r", "harmonic",
    "ring_i", "boots", "ionian",
)

# hp, hp growth, armor, armor growth, mr, mr growth.
# Enchanter and mage lines match the rest of this folder.
# Tank lines are the champion bases used for the resist comparison.
BODY = {
    "Brand": (630, 120, 34, 4.5, 36, 1.2),
    "Zyra": (600, 120, 37, 4.5, 36, 1.5),
    "Soraka": (560, 78, 32, 4.2, 30, 1.25),
    "Nami": (560, 88, 29, 4.5, 30, 1.25),
    "Sona": (540, 80, 28, 4.0, 30, 1.25),
    "Seraphine": (570, 90, 25, 4.0, 30, 1.25),
    "Yuumi": (500, 70, 25, 3.5, 25, 1.0),
    "Rakan": (580, 105, 36, 4.4, 32, 1.5),
    "Taric": (620, 110, 40, 4.6, 32, 2.0),
    "Alistar": (670, 120, 44, 4.7, 32, 2.05),
    "Braum": (610, 112, 47, 5.0, 32, 2.0),
    "Leona": (600, 110, 47, 4.8, 32, 2.05),
    "Nautilus": (646, 104, 39, 4.5, 32, 2.05),
    "Thresh": (590, 104, 28, 0.0, 30, 1.25),
    "Galio": (600, 126, 24, 4.5, 32, 2.05),
    "Amumu": (615, 95, 33, 4.2, 32, 2.05),
}

BASE_MANA.update({
    "Rakan": (280, 40),
    "Taric": (300, 60),
    "Alistar": (350, 40),
    "Braum": (311, 45),
    "Leona": (302, 40),
    "Nautilus": (400, 47),
    "Thresh": (274, 44),
    "Galio": (500, 40),
    "Amumu": (288, 40),
})

ROLE = {
    "Soraka": "enchanter",
    "Nami": "enchanter",
    "Sona": "enchanter",
    "Seraphine": "enchanter",
    "Yuumi": "enchanter",
    "Brand": "mage",
    "Zyra": "mage",
    "Rakan": "tank",
    "Taric": "tank",
    "Alistar": "tank",
    "Braum": "tank",
    "Leona": "tank",
    "Nautilus": "tank",
    "Thresh": "tank",
    "Galio": "tank",
    "Amumu": "tank",
}

# A normal tank-support finish (Locket, Vow, defensive boots) for the
# comparison row. Not part of the Diadem build.
TANK_ITEM_HP = 900
TANK_ITEM_ARMOR = 80
TANK_ITEM_MR = 45


def leona_fight(st, front, carry) -> Fight:
    """Eclipse maxed. W is a self resist steroid, not an ally shield."""
    ranks = ability_ranks(st.level, "WQE")
    ap = st.ap
    q = rank_value([0, 30, 60, 90, 120], ranks["Q"]) + 0.30 * ap
    w = rank_value([0, 40, 80, 120, 160], ranks["W"]) + 0.40 * ap
    e = rank_value([0, 50, 90, 130, 170], ranks["E"]) + 0.40 * ap
    r = rank_value([0, 100, 175, 250], ranks["R"]) + 0.80 * ap if ranks["R"] else 0
    p_q, p_e, p_w, p_r = 0.90, 0.70, 0.80, (0.75 if ranks["R"] else 0)
    # Q and E are single-target. W and R hit the pair.
    pre_c = p_q * q + p_e * e + p_w * w + p_r * r
    pre_f = p_w * w * 0.85 + p_r * r * 0.80
    return _hit(st, pre_c, pre_f, front, carry, 0, 0, 0, "no ally heal")


def nautilus_fight(st, front, carry) -> Fight:
    """W shields Nautilus only, so it does not spend Helia."""
    ranks = ability_ranks(st.level, "WQE")
    ap = st.ap
    passive = 15 + (80 - 15) * (st.level - 1) / 14 + 0.40 * ap
    q = rank_value([0, 80, 120, 160, 200], ranks["Q"]) + 0.75 * ap
    e = rank_value([0, 55, 85, 115, 145], ranks["E"]) + 0.30 * ap
    r = rank_value([0, 150, 200, 250], ranks["R"]) + 0.80 * ap if ranks["R"] else 0
    p_q, p_r = 0.65, (0.90 if ranks["R"] else 0)
    pre_c = 0.85 * passive + p_q * q + 0.85 * e * 2 + p_r * r
    pre_f = 0.70 * passive + 0.85 * e * 2 + p_r * r * 0.35
    return _hit(st, pre_c, pre_f, front, carry, 0, 0, 0, "self shield only")


def alistar_fight(st, front, carry) -> Fight:
    """Passive roar heals nearby allies when he lands a stun."""
    ranks = ability_ranks(st.level, "QWE")
    ap = st.ap
    q = rank_value([0, 60, 105, 150, 195], ranks["Q"]) + 0.50 * ap
    w = rank_value([0, 55, 110, 165, 220], ranks["W"]) + 0.70 * ap
    e = rank_value([0, 10, 16, 22, 28], ranks["E"]) + 0.04 * ap
    p_q, p_w, p_stun = 0.85, 0.80, 0.70
    pre_c = p_q * q * 0.7 + p_w * w + p_stun * e * 6
    pre_f = p_q * q * 0.7 + p_stun * e * 6
    roar = rank_value([0, 40, 70, 100, 130], max(ranks["Q"], 1)) + 0.40 * ap
    # One ally gets the roar when the knockup lands. He himself is not counted.
    kit = p_q * roar
    return _hit(st, pre_c, pre_f, front, carry, kit, 0, 1 if p_q else 0, "passive roar")


def braum_fight(st, front, carry) -> Fight:
    """E is a wall, not an ally shield, so Helia waits for Diadem."""
    ranks = ability_ranks(st.level, "QWE")
    ap = st.ap
    q = rank_value([0, 80, 125, 170, 215], ranks["Q"]) + 0.025 * st.hp
    r = rank_value([0, 150, 250, 350], ranks["R"]) + 0.60 * ap if ranks["R"] else 0
    p_q, p_r = 0.72, (0.75 if ranks["R"] else 0)
    pre_c = p_q * q + p_r * r
    pre_f = p_r * r * 0.80
    return _hit(st, pre_c, pre_f, front, carry, 0, 0, 0, "no ally heal")


def rakan_fight(st, front, carry) -> Fight:
    """Q heals an ally, E shields an ally. Both spend Helia."""
    ranks = ability_ranks(st.level, "EWQ")
    ap = st.ap
    q = rank_value([0, 70, 115, 160, 205], ranks["Q"]) + 0.60 * ap
    heal = rank_value([0, 40, 70, 100, 130], ranks["Q"]) + 0.50 * ap
    shield = rank_value([0, 50, 90, 130, 170], ranks["E"]) + 0.70 * ap
    w = rank_value([0, 70, 115, 160, 205], ranks["W"]) + 0.70 * ap
    r = rank_value([0, 100, 200, 300], ranks["R"]) + 0.50 * ap if ranks["R"] else 0
    p_q, p_w, p_r = 0.70, 0.75, (0.80 if ranks["R"] else 0)
    pre_c = p_q * q + p_w * w + p_r * r
    pre_f = p_w * w * 0.85 + p_r * r * 0.75
    kit_heal = p_q * heal if ranks["Q"] else 0
    # One guaranteed shield on the carry, half a second dash onto the other ally.
    kit_shield = (1.5 * shield) if ranks["E"] else 0
    dumps = (1 if ranks["Q"] else 0) + (1 if ranks["E"] else 0)
    return _hit(st, pre_c, pre_f, front, carry, kit_heal, kit_shield, dumps, "q heal, e shield")


def taric_fight(st, front, carry) -> Fight:
    """Q heals, W shields. Bastion shares bonus armor; this build has none."""
    ranks = ability_ranks(st.level, "QWE")
    ap = st.ap
    heal = rank_value([0, 60, 100, 140, 180], ranks["Q"]) + 0.30 * ap + 0.02 * (st.hp + 600)
    shield = rank_value([0, 60, 100, 140, 180], ranks["W"]) + 0.30 * ap
    e = rank_value([0, 80, 120, 160, 200], ranks["E"]) + 0.40 * ap
    p_e = 0.75
    casts_q = ncast(15, FIGHT_S, st.ah, cap=1) if ranks["Q"] else 0
    pre_c = p_e * e
    pre_f = p_e * e * 0.5
    return _hit(st, pre_c, pre_f, front, carry, casts_q * heal, shield if ranks["W"] else 0,
                casts_q + (1 if ranks["W"] else 0), "q heal, w shield")


def thresh_fight(st, front, carry) -> Fight:
    """Lantern is an ally shield. Souls are his armor; the items do not add them."""
    ranks = ability_ranks(st.level, "QWE")
    ap = st.ap
    souls = thresh_souls(st.minute)
    q = rank_value([0, 80, 130, 180, 230], ranks["Q"]) + 0.50 * ap
    e = rank_value([0, 65, 110, 155, 200], ranks["E"]) + 0.40 * ap
    r = rank_value([0, 250, 400, 550], ranks["R"]) + 1.00 * ap if ranks["R"] else 0
    shield = rank_value([0, 60, 100, 140, 180], ranks["W"]) + 0.40 * ap + 2.0 * souls
    p_q, p_e, p_r = 0.62, 0.75, (0.70 if ranks["R"] else 0)
    pre_c = p_q * q + p_e * e + p_r * r
    pre_f = p_e * e * 0.8 + p_r * r * 0.6
    return _hit(st, pre_c, pre_f, front, carry, 0, shield if ranks["W"] else 0,
                1 if ranks["W"] else 0, "lantern shield")


def galio_fight(st, front, carry) -> Fight:
    """W shields Galio, not an ally. His damage is what fills Helia after Diadem."""
    ranks = ability_ranks(st.level, "WQEQ")
    ap = st.ap
    q = rank_value([0, 70, 110, 150, 190], ranks["Q"]) + 0.70 * ap
    e = rank_value([0, 90, 130, 170, 210], ranks["E"]) + 0.90 * ap
    r = rank_value([0, 150, 250, 350], ranks["R"]) + 0.70 * ap if ranks["R"] else 0
    p_q, p_e, p_r = 0.75, 0.70, (0.75 if ranks["R"] else 0)
    pre_c = p_q * q + p_e * e + p_r * r
    pre_f = p_q * q * 0.65 + p_r * r * 0.80
    return _hit(st, pre_c, pre_f, front, carry, 0, 0, 0, "self shield only")


def amumu_fight(st, front, carry) -> Fight:
    """Support order QEW. No ally heal or shield.

    Tantrum reduces physical damage he takes. It does not spend Helia.
    Cursed Touch adds true damage on the target he bandages and autos.
    """
    ranks = ability_ranks(st.level, "QEW")
    ap = st.ap
    q = rank_value([0, 80, 130, 180, 230], ranks["Q"]) + 0.70 * ap
    q_cd = rank_value([0, 14, 13, 12, 11], ranks["Q"]) or 14
    nq = ncast(q_cd, FIGHT_S, st.ah, cap=2) if ranks["Q"] else 0
    # First bandage is the engage. A second one in the same fight is a bonus.
    q_hits = (0.70 + (0.35 if nq >= 2 else 0.0)) if ranks["Q"] else 0.0
    w_flat = rank_value([0, 10, 15, 20, 25], ranks["W"])
    w_pct = rank_value([0, 0.010, 0.0125, 0.015, 0.0175], ranks["W"])
    e = rank_value([0, 75, 100, 125, 150], ranks["E"]) + 0.50 * ap
    e_cd = rank_value([0, 8, 7.5, 7, 6.5], ranks["E"]) or 8
    ne = ncast(e_cd, FIGHT_S, st.ah, cap=2) if ranks["E"] else 0
    r = (rank_value([0, 150, 250, 350], ranks["R"]) + 0.80 * ap) if ranks["R"] else 0.0
    # Bandage in, ultimate holds them. He is not standing on both the whole fight.
    aura_c, aura_f = 3.0, 1.5

    def aura(hp: float, seconds: float) -> float:
        if not ranks["W"] or seconds <= 0:
            return 0.0
        pct = w_pct + 0.005 * ap / 100.0
        return seconds * (w_flat + pct * hp)

    magic_c = q_hits * q + aura(carry[0], aura_c) + ne * 0.80 * e
    magic_f = aura(front[0], aura_f) + ne * 0.55 * e
    if ranks["R"]:
        magic_c += 0.80 * r
        magic_f += 0.55 * r
    # Curse sticks to the bandaged target. The frontliner is only partly tagged.
    true_c = 0.10 * magic_c
    true_f = 0.05 * magic_f
    post_c = mitigate(magic_c, carry[1], st) + true_c
    post_f = mitigate(magic_f, front[1], st) + true_f
    pre = magic_c + true_c + magic_f + true_f
    return Fight(pre, post_f, post_c, 0, 0, 0, "no ally heal")


def _hit(st, pre_c, pre_f, front, carry, heal, shield, dumps, note) -> Fight:
    return Fight(
        pre_c + pre_f,
        mitigate(pre_f, front[1], st),
        mitigate(pre_c, carry[1], st),
        heal, shield, dumps, note,
    )


FIGHTERS.update({
    "Leona": leona_fight,
    "Nautilus": nautilus_fight,
    "Alistar": alistar_fight,
    "Braum": braum_fight,
    "Rakan": rakan_fight,
    "Taric": taric_fight,
    "Thresh": thresh_fight,
    "Galio": galio_fight,
    "Amumu": amumu_fight,
})


def thresh_souls(minute: int) -> int:
    return min(80, max(0, minute - 2) * 3)


def leona_w_resists(level: int) -> Tuple[float, float]:
    ranks = ability_ranks(level, "WQE")
    bonus = rank_value([0, 25, 35, 45, 55], ranks["W"])
    return bonus, bonus


def alistar_dr(level: int) -> float:
    """Fraction of the 8s fight spent in Unbreakable Will, times the reduction."""
    ranks = ability_ranks(level, "QWE")
    if not ranks["R"]:
        return 0.0
    reduction = rank_value([0, 0.50, 0.60, 0.70], ranks["R"])
    return reduction * (7.0 / FIGHT_S)


def amumu_e_flat(level: int) -> float:
    """Tantrum's flat physical reduction per hit. Not a percent reduction."""
    ranks = ability_ranks(level, "QEW")
    return rank_value([0, 5, 10, 15, 20], ranks["E"])


def nautilus_self_shield(st) -> float:
    ranks = ability_ranks(st.level, "WQE")
    if not ranks["W"]:
        return 0.0
    return rank_value([0, 80, 120, 160, 200], ranks["W"]) + 0.12 * (600 + st.hp)


def body_of(champ: str, level: int, bonus_hp: float, minute: int, steroid: bool) -> dict:
    hp0, hpg, ar0, arg, mr0, mrg = BODY[champ]
    hp = hp0 + hpg * (level - 1) + bonus_hp
    armor = ar0 + arg * (level - 1)
    mr = mr0 + mrg * (level - 1)
    note = ""
    if champ == "Thresh":
        souls = thresh_souls(minute)
        armor += souls * 1.0
        note = f"{souls} souls"
    dr = 0.0
    if steroid and champ == "Leona":
        a, m = leona_w_resists(level)
        armor += a
        mr += m
        note = "W up"
    if steroid and champ == "Alistar":
        dr = alistar_dr(level)
        note = "R up"
    if steroid and champ == "Nautilus":
        # Shield is applied as extra HP on the physical/magic EHP below.
        note = "W shield"
    taken = 1.0 - dr
    ehp_p = hp * (1 + armor / 100) / taken
    ehp_m = hp * (1 + mr / 100) / taken
    return {
        "hp": round(hp),
        "armor": round(armor),
        "mr": round(mr, 1),
        "ehp_phys": round(ehp_p),
        "ehp_magic": round(ehp_m),
        "note": note,
    }


def hard_cc(champ: str, level: int) -> float:
    if champ == "Brand":
        return brand_utility(level)["hard_cc"]
    if champ == "Zyra":
        return zyra_utility(level)["hard_cc"]
    if champ == "Leona":
        ranks = ability_ranks(level, "WQE")
        root = 0.50 * 0.70
        stun = rank_value([0, 1.0, 1.1, 1.2, 1.25], ranks["Q"]) * 0.90
        solar = (1.25 * 0.75 * 1.6) if ranks["R"] else 0
        return root + stun + solar
    if champ == "Nautilus":
        ranks = ability_ranks(level, "WQE")
        hook = 1.0 * 0.65
        root = 0.50 * 1.5
        knock = (1.0 * 0.90 * 1.35) if ranks["R"] else 0
        return hook + root + knock
    if champ == "Alistar":
        return 1.0 * 0.85 * 1.7 + 0.5 * 0.70
    if champ == "Braum":
        ranks = ability_ranks(level, "QWE")
        knock = (1.25 * 0.75 * 1.6) if ranks["R"] else 0
        return 0.25 * 0.72 + knock
    if champ == "Rakan":
        ranks = ability_ranks(level, "EWQ")
        knock = 1.0 * 0.75 * 1.6
        charm = (1.5 * 0.80 * 1.5) if ranks["R"] else 0
        return knock + charm
    if champ == "Taric":
        return 1.25 * 0.75 * 1.4
    if champ == "Thresh":
        ranks = ability_ranks(level, "QWE")
        hook = 1.5 * 0.62
        flay = 0.5 * 0.75
        box = (1.5 * 0.70) if ranks["R"] else 0
        return hook + flay + box
    if champ == "Galio":
        ranks = ability_ranks(level, "WQEQ")
        taunt = rank_value([0, 1.0, 1.25, 1.5, 1.75], ranks["W"]) * 0.80 * 1.6
        knock = (0.75 * 0.75 * 1.5) if ranks["R"] else 0
        return taunt + knock
    if champ == "Amumu":
        ranks = ability_ranks(level, "QEW")
        bandage = 1.0 * 0.70
        # A maxed bandage is short enough that a second toss can land.
        second = 1.0 * 0.35 if ranks["Q"] >= 4 else 0.0
        entangle = (2.0 * 0.80 * 1.6) if ranks["R"] else 0.0
        return bandage + second + entangle
    if champ == "Nami":
        return 1.25 * 0.62 + (1.5 * 0.75 if level >= 5 else 0)
    if champ == "Seraphine":
        return (1.25 * 0.70 if level >= 5 else 0)
    return 0.0


def kit_lane_per_min(st) -> float:
    """Ally healing from the kit over a minute, before heal/shield power."""
    ap = st.ap
    if st.champ == "Alistar":
        ranks = ability_ranks(st.level, "QWE")
        roar = rank_value([0, 40, 70, 100, 130], max(ranks["Q"], 1)) + 0.40 * ap
        return 4.0 * 0.70 * roar
    if st.champ == "Rakan":
        ranks = ability_ranks(st.level, "EWQ")
        if not ranks["Q"]:
            return 0.0
        heal = rank_value([0, 40, 70, 100, 130], ranks["Q"]) + 0.50 * ap
        cd = 11 * 100 / (100 + st.ah)
        return (60 / cd) * 0.55 * heal
    if st.champ == "Taric":
        ranks = ability_ranks(st.level, "QWE")
        if not ranks["Q"]:
            return 0.0
        heal = rank_value([0, 60, 100, 140, 180], ranks["Q"]) + 0.30 * ap + 0.02 * (st.hp + 600)
        cd = 15 * 100 / (100 + st.ah)
        return (60 / cd) * 0.70 * heal
    from simulate_brand_support import lane_kit_heal_per_min
    return lane_kit_heal_per_min(st)


def row_for(champ: str, snap: dict, minute: int) -> dict:
    st = stats_from_names(
        champ, snap["names"], level_at_minute(minute), minute,
        snap["charges"], gold_at_minute(minute), scythe_stacks(minute),
    )
    front = front_stats(st.level, minute)
    carry = carry_stats(st.level, minute)
    raw = FIGHTERS[champ](st, front, carry)
    fight = evaluate(st)
    bare = body_of(champ, st.level, st.hp, minute, steroid=False)
    geared = body_of(champ, st.level, st.hp, minute, steroid=True)
    if champ == "Nautilus":
        shield = nautilus_self_shield(st)
        geared = dict(geared)
        geared["ehp_phys"] = round(geared["ehp_phys"] + shield * (1 + geared["armor"] / 100))
        geared["ehp_magic"] = round(geared["ehp_magic"] + shield * (1 + geared["mr"] / 100))
        geared["note"] = f"W shield {round(shield)}"
    if champ == "Amumu":
        flat = amumu_e_flat(st.level)
        geared = dict(geared)
        # About six physical hits in the fight, each reduced by the flat amount.
        geared["ehp_phys"] = round(geared["ehp_phys"] + 6 * flat)
        geared["note"] = f"E tantrum {round(flat)}"
    hsp = st.hsp
    diadem = 0.0
    helia = 0.0
    if st.diadem:
        diadem = 0.008 * st.mana * FIGHT_S * 0.92 * hsp
    if st.helia and (st.diadem or raw.kit_dumps):
        every = st.diadem
        helia = helia_stored(raw.pre, st.level, FIGHT_S, every, raw.kit_dumps) * hsp
    if st.harmonic:
        diadem *= 1.30
        helia *= 1.30
    kit = kit_lane_per_min(st) * hsp * (1.30 if st.harmonic else 1)
    combat_s = 60 * 0.25
    lane_diadem = (0.008 * st.mana * combat_s * 0.92 * hsp) if st.diadem else 0
    if st.harmonic and st.diadem:
        lane_diadem *= 1.30
    return {
        "champ": champ,
        "role": ROLE[champ],
        "minute": minute,
        "level": st.level,
        "ap": round(st.ap),
        "ah": round(st.ah),
        "mana": round(st.mana),
        "hsp": round((st.hsp - 1) * 100, 1),
        "bonus_hp": round(st.hp),
        "damage": round(fight.post_front + fight.post_carry),
        "heal": round(fight.heal),
        "shield": round(fight.shield),
        "kit_heal": round(raw.heal),
        "kit_shield": round(raw.shield),
        "diadem_heal": round(diadem),
        "helia_heal": round(helia),
        "lane_heal": round(kit + lane_diadem),
        "hard_cc": round(hard_cc(champ, st.level), 2),
        "hp": bare["hp"],
        "armor": bare["armor"],
        "mr": bare["mr"],
        "ehp_phys": bare["ehp_phys"],
        "ehp_magic": bare["ehp_magic"],
        "ehp_phys_steroid": geared["ehp_phys"],
        "ehp_magic_steroid": geared["ehp_magic"],
        "steroid": geared["note"],
        "pre": round(raw.pre),
        "helia_cap": round(helia_cap(st.level) * FIGHT_S),
    }


def leona_on_tank_items(level: int, minute: int) -> dict:
    """Same Leona, resist items instead of Diadem. No heal items."""
    bare_hp = BODY["Leona"][0] + BODY["Leona"][1] * (level - 1) + TANK_ITEM_HP
    armor = BODY["Leona"][2] + BODY["Leona"][3] * (level - 1) + TANK_ITEM_ARMOR
    mr = BODY["Leona"][4] + BODY["Leona"][5] * (level - 1) + TANK_ITEM_MR
    a, m = leona_w_resists(level)
    return {
        "hp": round(bare_hp),
        "armor": round(armor),
        "mr": round(mr, 1),
        "ehp_phys": round(bare_hp * (1 + armor / 100)),
        "ehp_magic": round(bare_hp * (1 + mr / 100)),
        "ehp_phys_w": round(bare_hp * (1 + (armor + a) / 100)),
        "ehp_magic_w": round(bare_hp * (1 + (mr + m) / 100)),
    }


CHAMPS = (
    "Soraka", "Seraphine", "Nami", "Sona", "Yuumi",
    "Brand", "Zyra",
    "Rakan", "Taric", "Alistar", "Thresh", "Galio",
    "Braum", "Leona", "Nautilus", "Amumu",
)


def run() -> Tuple[str, dict]:
    walk = walk_priority(ORDER, "no-liandry")
    assert "Liandry's Torment" not in walk.snaps[walk.legendary or 18]["names"]
    # legendary stays empty without Liandry. Ionian is the last buy.
    done = walk.ionian or walk.harmonic or 18
    minutes = []
    for m in (8, walk.transfer or 13, done, 22):
        if m not in minutes and m in walk.snaps:
            minutes.append(m)

    rows: List[dict] = []
    by = {}
    for minute in range(1, 24):
        for champ in CHAMPS:
            row = row_for(champ, walk.snaps[minute], minute)
            rows.append(row)
            by[(minute, champ)] = row

    lines: List[str] = []
    A = lines.append
    A("=" * 78)
    A("WHO USES DIADEM / HELIA / HARMONIC — LIANDRY REMOVED (Wild Rift 7.3b)")
    A("Scythe, Ionian, Circlet → Diadem, Helia, Harmonic Echo. No Liandry.")
    A("8-second fight, ultimate up, one frontline + one carry. No runes.")
    A("=" * 78)
    A("")
    A("THE ITEMS AFTER LIANDRY IS GONE")
    A("  Ability power, mana, haste, heal/shield power, and some health.")
    A("  No armor. No magic resist. Helia stores 30% of pre-mitigation damage")
    A("  and spends it when an ally is healed or shielded. Diadem is that heal")
    A("  for champions who have none. Harmonic copies 30% of a heal and 35% of")
    A("  a shield. Harmony is +0.25% of max mana as heal/shield power.")
    A("")
    A(f"  Circlet {walk.circlet}:00. Helia {walk.helia}:00. Diadem {walk.diadem}:00.")
    A(f"  Harmonic {walk.harmonic}:00. Ionian {walk.ionian}:00.")
    A(f"  First minute damage becomes a heal: {walk.transfer}:00.")
    A(f"  Gold at 18:00 is {gold_at_minute(18)}. Full spend is "
      f"{sum(ev.cost for ev in walk.events)}.")
    A("")
    A("PIECES, LIANDRY LEFT OUT")
    for ev in walk.events:
        A(f"  {ev.minute:>2}:00  {ev.cost:>4}g  left {ev.left:>4}  {ev.name}")
    A("")

    focus = done
    ranked = sorted((by[(focus, c)] for c in CHAMPS), key=lambda r: -(r["heal"] + r["shield"]))
    best = ranked[0]
    tanks = [r for r in ranked if r["role"] == "tank"]
    best_tank = tanks[0]
    tankiest = max(tanks, key=lambda r: r["ehp_phys_steroid"])

    A("-" * 78)
    A(f"FULL BUILD AT {focus}:00 — HEAL AND SHIELD THE ITEMS PAY FOR")
    A("Sorted by ally healing plus shielding. Kit is the heal before items.")
    A("-" * 78)
    A(f"  {'Champ':<12} {'Role':<9} {'Heal':>6} {'Shield':>6} {'KitH':>6} {'Helia':>6} "
      f"{'Dmg':>6} {'CC':>5} {'AP':>4}")
    for r in ranked:
        A(f"  {r['champ']:<12} {r['role']:<9} {r['heal']:>6} {r['shield']:>6} "
          f"{r['kit_heal']:>6} {r['helia_heal']:>6} {r['damage']:>6} "
          f"{r['hard_cc']:>5.1f} {r['ap']:>4}")
    A("")
    second = ranked[1]
    A(f"  Most healing on this item list: {best['champ']} "
      f"({best['heal']} heal, {best['shield']} shield).")
    A(f"  Next is {second['champ']}: {second['heal']} heal and {second['shield']} shield.")
    A(f"  Best healing tank: {best_tank['champ']} "
      f"({best_tank['heal']} heal, {best_tank['shield']} shield).")
    A("")

    A("-" * 78)
    A(f"TANKINESS AT {focus}:00 ON THESE ITEMS")
    A("EHP is health times resists. Steroid is Leona W, Alistar R, Nautilus W,")
    A("Thresh souls, or Amumu's flat physical reduction from Tantrum.")
    A("The shop list did not add any armor or magic resist.")
    A("-" * 78)
    A(f"  {'Champ':<12} {'HP':>6} {'Arm':>5} {'MR':>5} {'EHPphys':>8} {'EHPmag':>8} "
      f"{'With':>8}  Note")
    show = sorted((by[(focus, c)] for c in CHAMPS), key=lambda r: -r["ehp_phys_steroid"])
    for r in show:
        A(f"  {r['champ']:<12} {r['hp']:>6} {r['armor']:>5} {r['mr']:>5.0f} "
          f"{r['ehp_phys']:>8} {r['ehp_magic']:>8} {r['ehp_phys_steroid']:>8}  {r['steroid']}")
    ref_level = by[(focus, "Leona")]["level"]
    ref = leona_on_tank_items(ref_level, focus)
    A("")
    A(f"  Leona on a normal tank finish (+{TANK_ITEM_HP} HP, +{TANK_ITEM_ARMOR} armor, "
      f"+{TANK_ITEM_MR} MR), no Diadem:")
    A(f"    HP {ref['hp']}  armor {ref['armor']}  MR {ref['mr']:.0f}  "
      f"EHP physical {ref['ehp_phys']}  with W {ref['ehp_phys_w']}")
    leo = by[(focus, "Leona")]
    A(f"  Leona on this Diadem build: EHP physical {leo['ehp_phys']}, "
      f"with W {leo['ehp_phys_steroid']}.")
    A(f"  With the steroid down, Brand is {by[(focus, 'Brand')]['ehp_phys']} "
      f"and Leona is {leo['ehp_phys']}. The health on the items is what they share.")
    A("")

    A("-" * 78)
    A("SAME CAST AT THE CONVERSION MINUTE AND AT 22:00")
    A("-" * 78)
    for minute in minutes:
        A(f"  [{minute}:00]")
        order = sorted((by[(minute, c)] for c in CHAMPS), key=lambda r: -(r["heal"] + r["shield"]))
        A(f"  {'Champ':<12} {'Heal':>6} {'Shield':>6} {'Dmg':>6} {'EHPphys':>8}")
        for r in order:
            if r["role"] == "enchanter" and r["champ"] not in ("Soraka", "Nami", "Seraphine"):
                continue
            if r["champ"] in ("Zyra",):
                continue
            A(f"  {r['champ']:<12} {r['heal']:>6} {r['shield']:>6} {r['damage']:>6} "
              f"{r['ehp_phys_steroid']:>8}")
        A("")

    soraka = by[(focus, "Soraka")]
    rakan = by[(focus, "Rakan")]
    taric = by[(focus, "Taric")]
    ali = by[(focus, "Alistar")]
    brand = by[(focus, "Brand")]
    naut = by[(focus, "Nautilus")]
    galio = by[(focus, "Galio")]
    amumu = by[(focus, "Amumu")]

    A("-" * 78)
    A("WHICH CHAMPION")
    A("-" * 78)
    A(f"  {best['champ']} is the best user of this list. At {focus}:00 the fight")
    A(f"  heal is {soraka['heal']}. The items multiply a heal that already exists.")
    A(f"  Brand, with no Liandry and no kit heal, restores {brand['heal']}.")
    A(f"  Of that, Diadem is {brand['diadem_heal']} and Helia is {brand['helia_heal']}.")
    A("  Removing Liandry takes away the burn Helia was converting, and Brand")
    A("  still has nothing of his own for Harmonic to copy.")
    A("")
    A("  A tank can buy the items. The shop does not stop them. The items do")
    A("  not make them a tank.")
    A(f"  Leona's physical EHP on this build is {leo['ehp_phys_steroid']} with W up,")
    A(f"  against {ref['ehp_phys_w']} on a resist finish with the same W.")
    A(f"  Her fight heal is {leo['heal']}, all of it from Diadem and Helia")
    A(f"  ({leo['diadem_heal']} + {leo['helia_heal']}). She has no ally heal to copy.")
    A(f"  Nautilus is the same shape: self shield, heal {naut['heal']}, "
      f"EHP with W {naut['ehp_phys_steroid']}.")
    A(f"  Braum's wall is not an ally shield, so his heal is {by[(focus, 'Braum')]['heal']}.")
    A("")
    A("  Three tanks actually spend the passives:")
    A(f"  Rakan Q and E: heal {rakan['heal']}, shield {rakan['shield']}, "
      f"CC {rakan['hard_cc']:.1f}s, EHP {rakan['ehp_phys']}.")
    A(f"  Taric Q and W: heal {taric['heal']}, shield {taric['shield']}. "
      "His W shares bonus armor, and this build adds 0 armor, so Bastion")
    A("  does not make the carry tankier.")
    A(f"  Alistar's roar is a real ally heal ({ali['kit_heal']} before items, "
      f"{ali['heal']} after) and his ultimate is percent damage reduction,")
    A(f"  so his EHP during R is {ali['ehp_phys_steroid']} without a resist item.")
    A("  That is the tank who can frontline on this list, because the tank")
    A("  steroid is in the ultimate, not in Locket.")
    A(f"  Galio deals {galio['damage']} and heals {galio['heal']}. The W shield")
    A("  is his own, so Harmonic does not copy it.")
    A(f"  Thresh's lantern is a shield ({by[(focus, 'Thresh')]['shield']}) and his")
    A(f"  souls keep armor the items do not give (EHP {by[(focus, 'Thresh')]['ehp_phys']}).")
    A("")
    A(f"  Amumu support can buy the same list. At {focus}:00 his fight heal is")
    A(f"  {amumu['heal']}. Kit heal is {amumu['kit_heal']}. Diadem is "
      f"{amumu['diadem_heal']} and Helia is {amumu['helia_heal']}.")
    A(f"  Damage is {amumu['damage']} (Leona {leo['damage']}, Galio {galio['damage']}, "
      f"Brand {brand['damage']}).")
    A(f"  Hard CC is {amumu['hard_cc']:.1f}s (Leona {leo['hard_cc']:.1f}s, "
      f"Rakan {rakan['hard_cc']:.1f}s).")
    A(f"  Physical EHP is {amumu['ehp_phys']}, and Tantrum brings the fight to "
      f"{amumu['ehp_phys_steroid']}.")
    A(f"  Leona with W is {leo['ehp_phys_steroid']}. Alistar during R is "
      f"{ali['ehp_phys_steroid']}.")
    A("  Bandage and the ultimate are why he is picked. He has no ally heal and")
    A("  no ally shield, so Harmonic has nothing of his to copy and Helia opens")
    A("  only because Diadem ticks. Tantrum is a small flat reduction on himself.")
    A(f"  Soraka still heals {soraka['heal']}. Rakan still heals {rakan['heal']} "
      f"and shields {rakan['shield']}.")
    A("  Amumu is a niche engage pick on this build. He is not the champion the")
    A("  items are for, and the items do not make him a tank.")
    A("")
    A(f"  The tankiest body on the Diadem list, steroid included, is {tankiest['champ']} "
      f"at {tankiest['ehp_phys_steroid']} physical EHP.")
    A("  Suitability for the build is the heal column, not that EHP column.")
    A(f"  {best['champ']} uses the items. A pure engage tank buys them and")
    A("  gives up the resists that make the role work. Rakan is the engage")
    A("  champion whose kit is already a heal and a shield. Alistar is the")
    A("  one who stays hard to kill during his ultimate.")
    A("=" * 78)

    payload = {
        "meta": {
            "patch": "7.3b",
            "liandry": False,
            "conversion_minute": walk.transfer,
            "full_minute": done,
            "best_healer": best["champ"],
            "best_tank_healer": best_tank["champ"],
            "tankiest": tankiest["champ"],
            "build": [ev.name for ev in walk.events],
        },
        "purchases": [
            {"minute": ev.minute, "cost": ev.cost, "left": ev.left, "name": ev.name}
            for ev in walk.events
        ],
        "rows": [by[(m, c)] for m in minutes for c in CHAMPS],
        "leona_tank_items": ref,
    }
    return "\n".join(lines), payload


def main() -> None:
    report, payload = run()
    focus_rows = [r for r in payload["rows"] if r["minute"] == payload["meta"]["full_minute"]]
    soraka = next(r for r in focus_rows if r["champ"] == "Soraka")
    leona = next(r for r in focus_rows if r["champ"] == "Leona")
    brand = next(r for r in focus_rows if r["champ"] == "Brand")
    rakan = next(r for r in focus_rows if r["champ"] == "Rakan")
    amumu = next(r for r in focus_rows if r["champ"] == "Amumu")
    assert payload["meta"]["conversion_minute"] is not None
    assert payload["meta"]["conversion_minute"] <= 14
    assert soraka["heal"] > leona["heal"]
    assert soraka["heal"] > brand["heal"]
    assert leona["armor"] > brand["armor"]
    assert leona["kit_heal"] == 0
    assert rakan["kit_heal"] > 0 or rakan["kit_shield"] > 0
    assert amumu["kit_heal"] == 0
    assert amumu["heal"] > 0
    assert amumu["heal"] < soraka["heal"]
    assert amumu["shield"] == 0
    assert payload["leona_tank_items"]["ehp_phys_w"] > leona["ehp_phys_steroid"]
    assert "Liandry" not in "".join(payload["meta"]["build"])
    print(report)
    out = Path(__file__).resolve().parent
    (out / "no-liandry-report.txt").write_text(report + "\n", encoding="utf-8")
    (out / "no-liandry-results.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
