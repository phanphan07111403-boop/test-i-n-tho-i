#!/usr/bin/env python3
"""
Wild Rift 7.3 — Caitlyn highest-damage buy order.

Cait 7.3: AD 54→60, AS given (ratio 0.625, growth 4%), Headshot + R
scale crit chance AND crit damage (200% + IE 230%). Mag Blaster gone.
Identity = AD/crit, not AS/on-hit.

Question: which 6-slot buy order deals the most 8s all-in damage
(trap Headshot → Q → net Headshot → autos → R).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import json
import os

PATCH = "7.3"
AS_CAP = 3.0
CRIT_BASE = 2.0
FIGHT_SECONDS = 8.0
MINUTES = (8, 12, 16, 20, 24)
AS_RATIO = 0.625
BASE_AS = 0.625
BASE_BONUS_AS = 0.28
AS_GROWTH = 0.04
BASE_AD = 60.0
AD_GROWTH = 4.2
HP_BASE = 600.0
HP_GROWTH = 128.0

LT_AS_STACK = 0.064
LT_MAX = 6
LT_BOLT = (6.0, 24.0)
LT_BOLT_AS_AMP = 0.0067
BRUTAL = 15.0
CUT_DOWN = 0.08


def gold_at_minute(m: int) -> int:
    if m <= 0:
        return 500
    total = 500
    for t in range(1, m + 1):
        if t <= 4:
            total += 380
        elif t <= 10:
            total += 620
        elif t <= 20:
            total += 740
        else:
            total += 1000
    return total


def level_at_minute(m: int) -> int:
    table = {
        1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7, 7: 8, 8: 9,
        9: 10, 10: 10, 11: 11, 12: 12, 13: 12, 14: 13,
        15: 13, 16: 14, 17: 14, 18: 15, 19: 15, 20: 15,
        21: 15, 22: 15, 23: 15, 24: 15,
    }
    return table.get(m, min(15, 1 + m))


def skill_rank(level: int, skill: str) -> int:
    """Q > W > E. R at 5 / 9 / 13."""
    if skill == "R":
        return (1 if level >= 5 else 0) + (1 if level >= 9 else 0) + (1 if level >= 13 else 0)
    mapping = {
        "Q": [1, 3, 6, 7],
        "W": [2, 8, 10, 11],
        "E": [4, 12, 14, 15],
    }
    return sum(1 for lv in mapping[skill] if level >= lv)


def lerp(lo: float, hi: float, level: int) -> float:
    t = (level - 1) / 14.0
    return lo + (hi - lo) * t


ITEMS: Dict[str, Dict] = {
    "long_sword": {
        "name": "Long Sword", "cost": 500, "tier": "start",
        "stats": {"ad": 12},
    },
    "berserkers_greaves": {
        "name": "Berserker's Greaves", "cost": 1200, "tier": "boots",
        "stats": {"ad": 10, "as": 0.35},
    },
    "hexoptics_c44": {
        "name": "Hexoptics C44", "cost": 2900, "tier": "legendary",
        "stats": {"ad": 55, "crit": 0.25},
        "credits": ["long_sword"],
    },
    "infinity_edge": {
        "name": "Infinity Edge", "cost": 3500, "tier": "legendary",
        "stats": {"ad": 75, "crit": 0.25, "crit_damage": 0.30},
    },
    "rapid_firecannon": {
        "name": "Rapid Firecannon", "cost": 2650, "tier": "legendary",
        "stats": {"crit": 0.25, "as": 0.40},
    },
    "lord_dominiks_regards": {
        "name": "Lord Dominik's Regards", "cost": 3300, "tier": "legendary",
        "stats": {"ad": 35, "crit": 0.25, "armor_pen": 0.35},
    },
    "bloodthirster": {
        "name": "Bloodthirster", "cost": 3200, "tier": "legendary",
        "stats": {"ad": 75, "lifesteal": 0.15},
    },
    "the_collector": {
        "name": "The Collector", "cost": 3000, "tier": "legendary",
        "stats": {"ad": 50, "crit": 0.25, "lethality": 12},
    },
    "stormrazor": {
        "name": "Stormrazor", "cost": 3000, "tier": "legendary",
        "stats": {"ad": 50, "crit": 0.25, "as": 0.20},
    },
    "yun_tal_wildarrows": {
        "name": "Yun Tal Wildarrows", "cost": 3100, "tier": "legendary",
        "stats": {"ad": 50, "as": 0.25},
    },
    "galeforce": {
        "name": "Galeforce", "cost": 3100, "tier": "legendary",
        "stats": {"ad": 60, "crit": 0.25},
        "credits": ["long_sword"],
    },
    "essence_reaver": {
        "name": "Essence Reaver", "cost": 3000, "tier": "legendary",
        "stats": {"ad": 50, "crit": 0.25, "ah": 20},
    },
    "mortal_reminder": {
        "name": "Mortal Reminder", "cost": 3000, "tier": "legendary",
        "stats": {"ad": 35, "crit": 0.25, "armor_pen": 0.30},
    },
    "immortal_shieldbow": {
        "name": "Immortal Shieldbow", "cost": 3000, "tier": "legendary",
        "stats": {"ad": 55, "crit": 0.25},
    },
}


def item_name(iid: str) -> str:
    return ITEMS[iid]["name"]


PATHS: Dict[str, List[str]] = {
    # WRF 7.3 — Hex → IE → RFC → LDR → BT (100% crit, AD capstone)
    "wrf": [
        "long_sword", "berserkers_greaves", "hexoptics_c44",
        "infinity_edge", "rapid_firecannon", "lord_dominiks_regards",
        "bloodthirster",
    ],
    # Collector 3rd instead of RFC (50 AD, skip range)
    "hex_ie_col_ldr_bt": [
        "long_sword", "berserkers_greaves", "hexoptics_c44",
        "infinity_edge", "the_collector", "lord_dominiks_regards",
        "bloodthirster",
    ],
    # Collector 2nd so minute 12 is not an IE hole
    "hex_col_ie_ldr_bt": [
        "long_sword", "berserkers_greaves", "hexoptics_c44",
        "the_collector", "infinity_edge", "lord_dominiks_regards",
        "bloodthirster",
    ],
    # RFC 3rd then Collector 4th (skip LDR)
    "hex_ie_rfc_col_bt": [
        "long_sword", "berserkers_greaves", "hexoptics_c44",
        "infinity_edge", "rapid_firecannon", "the_collector",
        "bloodthirster",
    ],
    # 5th Collector overcaps 125% crit
    "hex_ie_rfc_ldr_col": [
        "long_sword", "berserkers_greaves", "hexoptics_c44",
        "infinity_edge", "rapid_firecannon", "lord_dominiks_regards",
        "the_collector",
    ],
    "storm_ie_rfc_ldr_bt": [
        "long_sword", "berserkers_greaves", "stormrazor",
        "infinity_edge", "rapid_firecannon", "lord_dominiks_regards",
        "bloodthirster",
    ],
    "col_ie_rfc_ldr_bt": [
        "long_sword", "berserkers_greaves", "the_collector",
        "infinity_edge", "rapid_firecannon", "lord_dominiks_regards",
        "bloodthirster",
    ],
    "yun_ie_rfc_ldr_bt": [
        "long_sword", "berserkers_greaves", "yun_tal_wildarrows",
        "infinity_edge", "rapid_firecannon", "lord_dominiks_regards",
        "bloodthirster",
    ],
    "gale_ie_rfc_ldr_bt": [
        "long_sword", "berserkers_greaves", "galeforce",
        "infinity_edge", "rapid_firecannon", "lord_dominiks_regards",
        "bloodthirster",
    ],
    "hex_rfc_ie_ldr_bt": [
        "long_sword", "berserkers_greaves", "hexoptics_c44",
        "rapid_firecannon", "infinity_edge", "lord_dominiks_regards",
        "bloodthirster",
    ],
}

PATH_LABEL = {
    "wrf": "Hex → IE → RFC → LDR → BT",
    "hex_ie_col_ldr_bt": "Hex → IE → Collector → LDR → BT",
    "hex_col_ie_ldr_bt": "Hex → Collector → IE → LDR → BT",
    "hex_ie_rfc_col_bt": "Hex → IE → RFC → Collector → BT",
    "hex_ie_rfc_ldr_col": "Hex → IE → RFC → LDR → Collector",
    "storm_ie_rfc_ldr_bt": "Stormrazor → IE → RFC → LDR → BT",
    "col_ie_rfc_ldr_bt": "Collector → IE → RFC → LDR → BT",
    "yun_ie_rfc_ldr_bt": "Yun Tal → IE → RFC → LDR → BT",
    "gale_ie_rfc_ldr_bt": "Galeforce → IE → RFC → LDR → BT",
    "hex_rfc_ie_ldr_bt": "Hex → RFC → IE → LDR → BT",
}

COMPARE = [
    "wrf",
    "hex_ie_col_ldr_bt",
    "hex_col_ie_ldr_bt",
    "hex_ie_rfc_col_bt",
    "hex_ie_rfc_ldr_col",
    "storm_ie_rfc_ldr_bt",
    "col_ie_rfc_ldr_bt",
    "yun_ie_rfc_ldr_bt",
    "gale_ie_rfc_ldr_bt",
    "hex_rfc_ie_ldr_bt",
]


@dataclass
class Target:
    name: str
    hp: float
    armor: float
    mr: float


def squishy(m: int) -> Target:
    lv = level_at_minute(m)
    hp = 580 + 95 * lv + 28 * m
    armor = 32 + 4.2 * lv + 3.5 * m
    mr = 30 + 1.4 * lv + 1.5 * m
    if m >= 12:
        armor += 25
    return Target("squishy", hp, armor, mr)


def tank(m: int) -> Target:
    lv = level_at_minute(m)
    hp = 720 + 125 * lv + 90 * m
    armor = 42 + 5.0 * lv + 14 * m
    mr = 32 + 2.0 * lv + 9 * m
    return Target("tank", hp, armor, mr)


def phys_mult(armor: float, lethality: float, pct_pen: float) -> float:
    a = max(0.0, (armor - lethality) * (1.0 - pct_pen))
    return 100.0 / (100.0 + a)


def mag_mult(mr: float) -> float:
    return 100.0 / (100.0 + max(0.0, mr))


def owned_at_gold(path: List[str], gold: int) -> List[str]:
    owned: List[str] = []
    spent = 0
    for iid in path:
        it = ITEMS[iid]
        cost = int(it["cost"])
        for cred in it.get("credits", []):
            if cred in owned:
                spent -= int(ITEMS[cred]["cost"])
                owned.remove(cred)
                break
        if spent + cost <= gold:
            spent += cost
            owned.append(iid)
        else:
            break
    return owned


def minutes_owned(path: List[str], iid: str, minute: int) -> int:
    for m in range(0, minute + 1):
        if iid in owned_at_gold(path, gold_at_minute(m)):
            return minute - m
    return 0


@dataclass
class Stats:
    ad: float = 0.0
    bonus_as: float = 0.0
    crit: float = 0.0
    crit_dmg: float = CRIT_BASE
    lethality: float = 0.0
    armor_pen: float = 0.0
    lifesteal: float = 0.0
    items: List[str] = field(default_factory=list)


def aggregate(owned: List[str], yun_crit: float) -> Stats:
    st = Stats(items=list(owned))
    for iid in owned:
        s = ITEMS[iid]["stats"]
        st.ad += s.get("ad", 0.0)
        st.bonus_as += s.get("as", 0.0)
        st.crit += s.get("crit", 0.0)
        st.crit_dmg += s.get("crit_damage", 0.0)
        st.lethality += s.get("lethality", 0.0)
        st.armor_pen += s.get("armor_pen", 0.0)
        st.lifesteal += s.get("lifesteal", 0.0)
    if "yun_tal_wildarrows" in owned:
        st.crit += yun_crit
        st.bonus_as += 0.25  # Flurry up for the all-in
    st.crit = min(1.0, st.crit)
    return st


def champ_ad(level: int) -> float:
    return BASE_AD + AD_GROWTH * (level - 1)


def champ_hp(level: int) -> float:
    return HP_BASE + HP_GROWTH * (level - 1)


@dataclass
class FightResult:
    damage: float = 0.0
    physical: float = 0.0
    magic: float = 0.0
    autos: int = 0
    headshots: int = 0
    ttk: Optional[float] = None
    as_avg: float = 0.0
    as_peak: float = 0.0
    ad: float = 0.0
    crit: float = 0.0
    crit_dmg: float = CRIT_BASE
    items: List[str] = field(default_factory=list)


def headshot_bonus(ad: float, crit: float, crit_dmg: float, level: int) -> float:
    """7.3: (60–100%) AD + crit×AD + (crit_dmg−2)×crit×AD."""
    ratio = lerp(0.60, 1.00, level)
    return ratio * ad + crit * ad * (crit_dmg - 1.0)


def simulate_fight(
    owned: List[str],
    minute: int,
    target: Target,
    yun_crit: float = 0.0,
) -> FightResult:
    level = level_at_minute(minute)
    st = aggregate(owned, yun_crit)
    has = set(owned)
    hexopt = "hexoptics_c44" in has
    rfc = "rapid_firecannon" in has
    storm = "stormrazor" in has
    ldr = "lord_dominiks_regards" in has
    collector = "the_collector" in has
    er = "essence_reaver" in has

    q_rank = skill_rank(level, "Q")
    w_rank = skill_rank(level, "W")
    e_rank = skill_rank(level, "E")
    r_rank = skill_rank(level, "R")

    base_ad = champ_ad(level)
    cait_hp = champ_hp(level)
    level_as = BASE_BONUS_AS + AS_GROWTH * (level - 1)
    alacrity = min(0.15, max(0.0, (minute - 2) / 8.0 * 0.15))

    hp = target.hp
    armor = target.armor
    mr = target.mr
    hs_stacks = 0
    lt_stacks = 0
    energized = 55.0
    energized_per_auto = 12
    q_used = False
    e_used = False
    r_used = False
    trap_hs_done = False
    t = 0.0
    dt = 0.05
    next_auto = 0.25
    res = FightResult(items=list(owned), crit=st.crit, crit_dmg=st.crit_dmg)
    as_sum = 0.0
    as_n = 0
    killed_at: Optional[float] = None
    execute_pct = 0.05 if collector else 0.0

    def total_ad() -> float:
        return base_ad + st.ad

    def bonus_as() -> float:
        return level_as + st.bonus_as + alacrity + LT_AS_STACK * lt_stacks

    def current_as() -> float:
        return min(AS_CAP, BASE_AS + bonus_as() * AS_RATIO)

    def hex_amp() -> float:
        # Max-range kite. RFC extra range → always full Magnification.
        if not hexopt:
            return 0.0
        return 0.10 if rfc else 0.08

    def deal(amount: float, kind: str, basic: bool = False) -> None:
        nonlocal hp, killed_at
        if amount <= 0:
            return
        if kind == "phys":
            amount *= phys_mult(armor, st.lethality, st.armor_pen)
            res.physical += amount
        else:
            amount *= mag_mult(mr)
            res.magic += amount
        if basic:
            amount *= 1.0 + hex_amp()
            if ldr and target.hp > cait_hp:
                amount *= 1.0 + min(0.25, (target.hp - cait_hp) / 2000.0 * 0.25)
            if target.name == "tank":
                amount *= 1.0 + CUT_DOWN
        else:
            if target.name == "tank":
                amount *= 1.0 + CUT_DOWN
            if ldr and target.hp > cait_hp and kind == "phys":
                amount *= 1.0 + min(0.25, (target.hp - cait_hp) / 2000.0 * 0.25)
        res.damage += amount
        hp -= amount
        if collector and hp > 0 and hp / target.hp <= execute_pct:
            res.damage += hp
            hp = 0
        if killed_at is None and hp <= 0:
            killed_at = t

    def expected_auto(ad: float) -> float:
        c = st.crit
        return ad * (1.0 + c * (st.crit_dmg - 1.0))

    def do_headshot(trap: bool) -> None:
        ad = total_ad()
        deal(expected_auto(ad), "phys", basic=True)
        deal(headshot_bonus(ad, st.crit, st.crit_dmg, level), "phys", basic=True)
        if trap and w_rank:
            trap_b = [40.0, 90.0, 140.0, 190.0][w_rank - 1] + 0.30 * st.ad
            deal(trap_b, "phys", basic=True)
        deal(BRUTAL, "phys", basic=True)
        res.autos += 1
        res.headshots += 1

    def fire_q() -> None:
        if q_rank <= 0:
            return
        bases = [50.0, 100.0, 150.0, 200.0]
        ratios = [1.25, 1.45, 1.65, 1.85]
        deal(bases[q_rank - 1] + ratios[q_rank - 1] * total_ad(), "phys")
        if er:
            # Spellblade: 1.35×base AD + 0.8 per 1% crit (up to 80)
            deal(1.35 * base_ad + 80.0 * st.crit, "phys")

    def fire_r() -> None:
        if r_rank <= 0:
            return
        bases = [250.0, 450.0, 650.0]
        missing = max(0.0, target.hp - max(hp, 0.0))
        raw = bases[r_rank - 1] + 1.00 * st.ad + 0.20 * missing
        mult = 1.0 + st.crit * 0.30 * (st.crit_dmg - 1.0)
        deal(raw * mult, "phys")

    def auto_attack() -> None:
        nonlocal hs_stacks, lt_stacks, energized
        ad = total_ad()
        hs_stacks += 1
        if hs_stacks >= 6:
            hs_stacks = 0
            do_headshot(False)
        else:
            deal(expected_auto(ad), "phys", basic=True)
            deal(BRUTAL, "phys", basic=True)
            res.autos += 1
        lt_stacks = min(LT_MAX, lt_stacks + 1)
        if lt_stacks >= LT_MAX:
            bolt = lerp(LT_BOLT[0], LT_BOLT[1], level)
            bolt *= 1.0 + bonus_as() * 100.0 * LT_BOLT_AS_AMP
            deal(bolt, "phys")
        energized += energized_per_auto
        if energized >= 100 and (rfc or storm):
            energized = 0.0
            deal(80.0 if rfc else 120.0, "magic")

    # Max-damage combo: trap HS → Q → net HS → autos → R
    while t < FIGHT_SECONDS and (killed_at is None or t < killed_at + 0.01):
        as_sum += current_as()
        as_n += 1
        res.as_peak = max(res.as_peak, current_as())
        if (not trap_hs_done) and t >= 0.15:
            do_headshot(True)
            trap_hs_done = True
            hs_stacks = 0
            next_auto = t + 1.0 / max(0.40, current_as())
        if (not q_used) and q_rank and t >= 0.40:
            fire_q()
            q_used = True
        if (not e_used) and e_rank and t >= 0.70:
            do_headshot(False)  # net guaranteed Headshot
            e_used = True
            hs_stacks = 0
            next_auto = t + 1.0 / max(0.40, current_as())
        if (not r_used) and r_rank and t >= 1.55:
            fire_r()
            r_used = True
        if trap_hs_done and t + 1e-9 >= next_auto:
            auto_attack()
            next_auto = t + 1.0 / max(0.40, current_as())
        energized += 20.0 * dt
        t += dt

    res.ttk = killed_at
    res.as_avg = as_sum / max(1, as_n)
    res.ad = total_ad()
    res.crit = st.crit
    res.crit_dmg = st.crit_dmg
    return res


PAGE = {
    "champ": "Caitlyn",
    "role": "ADC",
    "wrf": "B→up",
    "page": [
        "Hexoptics C44",
        "Berserker's Greaves",
        "The Collector",
        "Infinity Edge",
        "Lord Dominik's Regards",
        "Bloodthirster",
    ],
    "buy": [
        "Long Sword",
        "Berserker's Greaves",
        "Hexoptics C44",
        "The Collector",
        "Infinity Edge",
        "Lord Dominik's Regards",
        "Bloodthirster",
    ],
    "skill": "Q > W > E   (R mọi cấp)",
    "spells": "Flash + Ghost",
    "runes": [
        "Lethal Tempo",
        "Brutal",
        "Cut Down",
        "Legend: Alacrity",
        "Bone Plating",
    ],
    "pad": {
        "L1": "Q Peacemaker (xả)",
        "L2": "W Trap (tap gần địch)",
        "L3": "E Net (lùi analog)",
        "L4": "R Ace (lock)",
        "A": "AA — Headshot từ bụi / trap",
    },
    "combo": (
        "L2 trap → A Headshot → L1 Q full → L3 net Headshot → A kite max tầm. "
        "L4 R khi thiếu máu (scale crit + IE)."
    ),
    "sit": [
        "RFC 3rd thay Collector nếu cần range (WRF; late squish DPS cao hơn một chút)",
        "Hex → IE thẳng nếu farm đủ 3500g trước 12:00 (bỏ lỗ Collector)",
        "Mortal thay LDR vs heal",
        "Shieldbow / GA ô 6 vs burst (mất 75 AD BT)",
        "Galeforce dash — không phải max damage",
        "Đừng Yun Tal: Headshot/R cần crit ngay, Yun stack 125 AA",
        "Đừng 5 item crit — IE 7.3 bỏ excess-crit→crit dmg. Ô 6 = BT",
    ],
    "pad_score": 78,
    "pad_note": "Trap tap gần. RFC/Hexoptics kite analog. R lock.",
}


def yun_crit_at(path_key: str, minute: int) -> float:
    path = PATHS[path_key]
    if "yun_tal_wildarrows" not in path:
        return 0.0
    held = minutes_owned(path, "yun_tal_wildarrows", minute)
    # Ranged 0.2% crit / auto, ~10 champion+cs autos / min while holding.
    return min(0.25, held * 10 * 0.002)


def snapshot(path_key: str, minute: int) -> Dict:
    path = PATHS[path_key]
    gold = gold_at_minute(minute)
    owned = owned_at_gold(path, gold)
    yc = yun_crit_at(path_key, minute)
    sq = simulate_fight(owned, minute, squishy(minute), yc)
    tk = simulate_fight(owned, minute, tank(minute), yc)
    st = aggregate(owned, yc)
    return {
        "minute": minute,
        "level": level_at_minute(minute),
        "gold": gold,
        "owned": [item_name(i) for i in owned],
        "ids": owned,
        "squishy": round(sq.damage),
        "tank": round(tk.damage),
        "sq_ttk": None if sq.ttk is None else round(sq.ttk, 2),
        "tk_ttk": None if tk.ttk is None else round(tk.ttk, 2),
        "sq_dps": round(sq.damage / (sq.ttk if sq.ttk else FIGHT_SECONDS)),
        "tk_dps": round(tk.damage / (tk.ttk if tk.ttk else FIGHT_SECONDS)),
        "autos": sq.autos,
        "headshots": sq.headshots,
        "as_avg": round(sq.as_avg, 2),
        "ad": round(sq.ad, 1),
        "crit": round(100 * st.crit),
        "crit_dmg": round(100 * st.crit_dmg),
    }


def first_item_ready(path_key: str) -> int:
    path = PATHS[path_key]
    first_leg = next(i for i in path if ITEMS[i]["tier"] == "legendary")
    for m in range(1, 25):
        if first_leg in owned_at_gold(path, gold_at_minute(m)):
            return m
    return 24


def score_path(path_key: str) -> float:
    """Highest damage: squishy DPS 70% (delete ADC) + tank DPS 30%."""
    total = 0.0
    weights = {8: 0.9, 12: 1.3, 16: 1.4, 20: 1.2, 24: 1.1}
    for m, w in weights.items():
        s = snapshot(path_key, m)
        total += w * (0.70 * s["sq_dps"] + 0.30 * s["tk_dps"])
    return total


def six_slot(owned: List[str]) -> List[str]:
    """First legendary, boots, remaining legendaries."""
    boots = [i for i in owned if ITEMS[i]["tier"] == "boots"]
    legs = [i for i in owned if ITEMS[i]["tier"] == "legendary"]
    ordered = legs[:1] + boots + legs[1:]
    return [item_name(i) for i in ordered[:6]]


def write_report(path: str) -> Dict:
    lines: List[str] = []
    a = lines.append
    scores = {k: score_path(k) for k in COMPARE}
    winner = max(scores, key=scores.get)
    ranked = sorted(COMPARE, key=lambda k: scores[k], reverse=True)

    a("=" * 78)
    a("TỐC CHIẾN 7.3 — CAITLYN HIGHEST DAMAGE BUY ORDER")
    a("Headshot + R scale crit chance VÀ crit damage (200% / IE 230%).")
    a("8s all-in: trap Headshot → Q full → net Headshot → autos → R.")
    a("=" * 78)
    a("")

    win_path = PATHS[winner]
    win_owned = owned_at_gold(win_path, gold_at_minute(24))
    page6 = six_slot(win_owned)
    buy = [item_name(i) for i in win_path]

    # Keep PAGE in sync with the sim winner so README/tests match.
    PAGE["page"] = page6
    PAGE["buy"] = buy

    a("PLAY THIS  (highest 8s damage)")
    a(f"  Path   {PATH_LABEL[winner]}")
    a(f"  Ô:     {' › '.join(page6)}")
    a(f"  Mua:   {' › '.join(buy)}")
    a(f"  Max    {PAGE['skill']}")
    a(f"  Spell  {PAGE['spells']}")
    a(f"  Runes  {' · '.join(PAGE['runes'])}")
    a(f"  Pad    L1 {PAGE['pad']['L1']}")
    a(f"         L2 {PAGE['pad']['L2']}")
    a(f"         L3 {PAGE['pad']['L3']}")
    a(f"         L4 {PAGE['pad']['L4']}")
    a(f"         A  {PAGE['pad']['A']}")
    a(f"  Combo  {PAGE['combo']}")
    a("")
    a("  Swap:")
    for s in PAGE["sit"]:
        a(f"    · {s}")
    a("")

    a("-" * 78)
    a("BUY ORDER (vì sao thứ tự này)")
    a("-" * 78)
    a("  1. Long Sword — component Hexoptics.")
    a("  2. Berserkers — 35% AS. Cait ratio 0.625: boots AS đủ, đừng AS-item first.")
    a("  3. Hexoptics C44 (55 AD / 25% crit / +10% dmg tầm xa) ~8:00. Headshot bắt đầu scale crit.")
    a("  4. Collector (50 AD / 25% crit / 12 leth / execute) — đan lỗ IE 3500g @12.")
    a("     50% crit sớm. Yun Tal / Stormrazor / Collector-first thua Hex.")
    a("  5. Infinity Edge (75 AD / 25% crit / 230% crit dmg) ~17:00. Headshot + R nổ.")
    a("  6. LDR (35 AD / 25% crit / 35% pen) — cap 100% crit. Pen thắng Collector 4th vs giáp.")
    a("  7. Bloodthirster (75 AD, 0% crit) — ô 6. Không mua crit item thứ 5.")
    a("")

    a("-" * 78)
    a("BẢNG PATH  (squishy DPS = damage / TTK)")
    a("-" * 78)
    a(f"  {'#':<3}{'Path':<42}{'8':>7}{'12':>7}{'16':>7}{'20':>7}{'24':>7}  score")
    table = []
    for i, key in enumerate(ranked, 1):
        cells = []
        row = {"key": key, "label": PATH_LABEL[key], "score": round(scores[key])}
        for m in MINUTES:
            s = snapshot(key, m)
            row[str(m)] = s
            cells.append(f"{s['sq_dps']:>7}")
        mark = " <<" if key == winner else ""
        a(f"  {i:<3}{PATH_LABEL[key]:<42}{''.join(cells)}  {row['score']}{mark}")
        table.append(row)
    a("")
    a("  Tank DPS @12 / @16 / @20 / @24")
    for key in ranked[:5]:
        bits = [str(snapshot(key, m)["tk_dps"]) for m in (12, 16, 20, 24)]
        a(f"    {PATH_LABEL[key]:<42}  {' / '.join(bits)}")
    a("")

    a("-" * 78)
    a("SPIKE MUA ĐỒ  (path thắng)")
    a("-" * 78)
    for m in MINUTES:
        s = snapshot(winner, m)
        ttk = s["sq_ttk"] if s["sq_ttk"] is not None else "live"
        a(
            f"  {m:02d}:00  lv{s['level']:<2}  {s['gold']:>5}g  "
            f"crit {s['crit']:>3}%/{s['crit_dmg']}%  AS {s['as_avg']:.2f}  "
            f"AD {s['ad']:<5}  dps {s['sq_dps']}/{s['tk_dps']}  "
            f"ttk {ttk}  squish {s['squishy']}"
        )
        a(f"         { ' › '.join(s['owned']) }")
    a("")

    wrf_s = snapshot("wrf", 24)
    win_s = snapshot(winner, 24)
    a("-" * 78)
    a("GHI CHÚ 7.3")
    a("-" * 78)
    a("  • Hexoptics first, không Yun Tal — Headshot/R cần crit ngay, không stack 125 AA.")
    a("  • Collector second đan lỗ IE 3500g @12. IE third ~17:00.")
    a("  • RFC 3rd (WRF) = late squish DPS cao hơn, mất 50 AD Collector.")
    a("  • 4 item crit = 100%. Ô 6 = BT 75 AD, không Collector/Galeforce (overcap).")
    a("  • Trap Headshot +40–190 (+30% bAD) mới 7.3. Combo trap→AA→Q.")
    a(f"  • WRF RFC-page @24 dps {wrf_s['sq_dps']}/{wrf_s['tk_dps']}.")
    a(f"  • Winner @24 dps {win_s['sq_dps']}/{win_s['tk_dps']}  "
      f"squish {win_s['squishy']} tank {win_s['tank']}.")
    a("=" * 78)

    payload = {
        "patch": PATCH,
        "champ": "Caitlyn",
        "winner": winner,
        "winner_label": PATH_LABEL[winner],
        "scores": {k: round(v) for k, v in scores.items()},
        "ranked": [PATH_LABEL[k] for k in ranked],
        "page": PAGE,
        "by_path": {
            k: {
                "ready": first_item_ready(k),
                "label": PATH_LABEL[k],
                "score": round(scores[k]),
                "by_minute": {str(m): snapshot(k, m) for m in MINUTES},
            }
            for k in COMPARE
        },
        "winner_spikes": [snapshot(winner, m) for m in MINUTES],
    }
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return payload


def main() -> None:
    here = os.path.dirname(os.path.abspath(__file__))
    payload = write_report(os.path.join(here, "report.txt"))
    with open(os.path.join(here, "results.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print("Winner:", payload["winner_label"])
    print("Page:", " › ".join(PAGE["page"]))
    print("Buy: ", " › ".join(PAGE["buy"]))
    for s in payload["winner_spikes"]:
        print(
            f"  {s['minute']:02d}:00 crit {s['crit']}%  "
            f"squish {s['squishy']} tank {s['tank']}  "
            f"{' › '.join(s['owned'])}"
        )
    print("Wrote report.txt and results.json")


if __name__ == "__main__":
    main()
