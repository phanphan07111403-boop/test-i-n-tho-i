#!/usr/bin/env python3
"""
Wild Rift 7.3 — Senna ADC + support: items, boots, runes.

7.3 deleted Magnetic Blaster, raised system crit 175%→200%, and rewrote
Senna's attack-speed sheet (ratio 0.4, base 0.4). Mist crit is 10% per
20 (was 15%). Autos crit for 90% of normal crit damage. Q base 50/80/
110/140.

Question:
  After Magnetic is gone and Senna actually converts attack speed, which
  legal 7.3 path peaks 8s poke/combat for ADC (24:00) and support (20:00)?
  Hexoptics (range amp), Statikk+RFC (energized AS), leftover lethality,
  or Yun Tal/Stormrazor like a normal crit ADC?

Rune loadout: 1 keystone + 3 primary + 1 secondary. Ingenious Hunter is
gone. Legend: Haste replaced Legend: Tenacity. Lethal Tempo is the 7.3
rewrite (built-AS stacks + bolt).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import json
import os

PATCH = "7.3"
OUT_DIR = os.path.dirname(os.path.abspath(__file__))
AS_CAP = 3.0
CRIT_BASE = 2.0
SENNA_CRIT_FACTOR = 0.90  # autos only
FIGHT = 8.0
ADC_MINUTES = (8, 12, 16, 20, 24)
SUP_MINUTES = (8, 12, 16, 20)
T3_MINUTE = 10
SCYTHE_MINUTE = 6
BASE_AD = 50.0
BASE_HP = 570.0
HP_GROWTH = 120.0
BASE_AS = 0.40
AS_RATIO = 0.40
BASE_BONUS_AS = 0.60
# 7.3 notes print "Attack Speed per Level: 0.05". WR growth is
# per_level * (0.7 + 0.03 * level) accumulated from level 2.
AS_GROWTH = 0.05
MIST_AD = 1.25
MIST_CRIT = 0.10  # per 20 stacks
MIST_RANGE = 15.0
EXCESS_VAMP = 0.35
RELIC = 0.20
BRUTAL = 15.0
CUT_DOWN = 0.08
LT_AS = 0.064
LT_MAX = 6
LT_BOLT = (6.0, 24.0)
ALACRITY_CAP = 0.15
DH_BASE = 35.0
DH_SOUL = 11.0
DH_AD = 0.10


def lerp(lo: float, hi: float, level: int) -> float:
    return lo + (hi - lo) * (level - 1) / 14.0


def ah_cd(base: float, ah: float) -> float:
    return base * 100.0 / (100.0 + max(0.0, ah))


def armor_mult(armor: float, lethality: float, pct_pen: float) -> float:
    effective = armor * (1.0 - min(0.45, pct_pen)) - lethality
    return 100.0 / (100.0 + max(0.0, effective))


def mag_mult(mr: float) -> float:
    return 100.0 / (100.0 + max(0.0, mr))


# ---------------------------------------------------------------------------
# Economy
# ---------------------------------------------------------------------------


def adc_gold(minute: int) -> int:
    """Dragon-lane farm. Same 24-min curve as the 7.3 Caitlyn sim."""
    if minute <= 0:
        return 500
    total = 500
    for t in range(1, minute + 1):
        if t <= 4:
            total += 380
        elif t <= 10:
            total += 620
        elif t <= 20:
            total += 740
        else:
            total += 1000
    return total


def support_gold(minute: int) -> int:
    """Sickle tribute + fights. Same curve as the Senna boots / Zyra support sims."""
    if minute <= 0:
        return 500
    total = 500
    for t in range(1, minute + 1):
        if t <= 4:
            total += 330
        elif t <= 10:
            total += 460
        else:
            total += 560
    return total


def gold_at(minute: int, role: str) -> int:
    return adc_gold(minute) if role == "adc" else support_gold(minute)


def level_at(minute: int, role: str) -> int:
    if role == "adc":
        table = {
            1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7, 7: 8, 8: 9,
            9: 10, 10: 10, 11: 11, 12: 12, 13: 12, 14: 13,
            15: 13, 16: 14, 17: 14, 18: 15, 19: 15, 20: 15,
            21: 15, 22: 15, 23: 15, 24: 15,
        }
    else:
        table = {
            1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7, 7: 8, 8: 8,
            9: 9, 10: 10, 11: 10, 12: 11, 13: 11, 14: 12,
            15: 12, 16: 13, 17: 13, 18: 14, 19: 14, 20: 15,
        }
    return table.get(minute, min(15, 1 + minute))


def mist_at(minute: int, role: str) -> float:
    """Soul curve. Support matches WRF '60–80 late'. ADC is faster CS
    + extracts, not the old DH-dive printer (that hit 190+ by 20:00)."""
    if role == "adc":
        stacks = 0.0
        for t in range(1, minute + 1):
            if t <= 4:
                stacks += 4.0
            elif t <= 10:
                stacks += 5.5
            else:
                stacks += 6.5
        return stacks
    return min(100.0, 8.0 + 3.5 * minute)


def skill_rank(level: int, skill: str) -> int:
    """Q max, W second, E last. R at 5/9/13 (WR rank cadence)."""
    if skill == "R":
        return (
            (1 if level >= 5 else 0)
            + (1 if level >= 9 else 0)
            + (1 if level >= 13 else 0)
        )
    mapping = {
        "Q": [1, 3, 5, 7, 9],
        "W": [2, 4, 8, 10, 12],
        "E": [6, 11, 14, 15],
    }
    return min(4, sum(1 for lv in mapping[skill] if level >= lv))


def senna_as(level: int, bonus_as: float) -> float:
    """7.3: base 0.4, ratio 0.4, base bonus 0.6, per-level 0.05."""
    level_as = 0.0
    for lv in range(2, level + 1):
        level_as += AS_GROWTH * (0.7 + 0.03 * lv)
    return min(AS_CAP, BASE_AS + AS_RATIO * (BASE_BONUS_AS + level_as + bonus_as))


def q_damage(rank: int, bonus_ad: float) -> float:
    if rank <= 0:
        return 0.0
    return [0, 50, 80, 110, 140][rank] + 0.60 * bonus_ad


def q_heal(rank: int, bonus_ad: float, ap: float) -> float:
    if rank <= 0:
        return 0.0
    return [0, 40, 70, 100, 130][rank] + 0.40 * bonus_ad + 0.25 * ap


def w_damage(rank: int, bonus_ad: float) -> float:
    if rank <= 0:
        return 0.0
    return [0, 90, 155, 220, 285][rank] + 0.70 * bonus_ad


def r_damage(rank: int, bonus_ad: float, ap: float) -> float:
    if rank <= 0:
        return 0.0
    return [0, 250, 400, 550][rank] + 1.20 * bonus_ad + 0.70 * ap


def r_shield(rank: int, ap: float, mist: float) -> float:
    if rank <= 0:
        return 0.0
    return [0, 120, 160, 200][rank] + 0.50 * ap + 2.0 * mist


def extraction_pct(level: int) -> float:
    return 0.01 + 0.09 * (level - 1) / 14.0


def nightstalker(level: int) -> float:
    return 60.0 + 100.0 * (level - 1) / 14.0


# ---------------------------------------------------------------------------
# Items — 7.3 live numbers. Lethality leftovers marked leftover=True.
# Magnetic Blaster / Cloak of Agility are intentionally absent.
# ---------------------------------------------------------------------------


ITEMS: Dict[str, Dict] = {
    "long_sword": {
        "name": "Long Sword", "cost": 500, "tier": "start",
        "stats": {"ad": 12},
    },
    "spectral_sickle": {
        "name": "Spectral Sickle", "cost": 500, "tier": "start",
        "stats": {"ad": 10}, "support": True,
    },
    "black_mist_scythe": {
        "name": "Black Mist Scythe", "cost": 0, "tier": "support",
        "stats": {"ad": 14, "ah": 10}, "support": True, "scythe": True,
    },
    "berserkers_greaves": {
        "name": "Berserker's Greaves", "cost": 1200, "tier": "boots",
        "stats": {"ad": 10, "as": 0.35},
    },
    "boots_of_dynamism": {
        "name": "Boots of Dynamism", "cost": 1200, "tier": "boots",
        "stats": {"ad": 15, "lethality": 10},
        "credits": ["long_sword"], "leftover": True,
    },
    "ionian_boots": {
        "name": "Ionian Boots of Lucidity", "cost": 1000, "tier": "boots",
        "stats": {"ah": 15}, "leftover": True,
    },
    "plated_steelcaps": {
        "name": "Plated Steelcaps", "cost": 900, "tier": "boots",
        "stats": {"armor": 15},
    },
    "armorcrusher": {
        "name": "Armorcrusher Boots", "cost": 2200, "tier": "boots",
        "stats": {"ad": 20, "lethality": 10, "armor_pen": 0.06},
        "credits": ["boots_of_dynamism"], "replaces": "boots_of_dynamism",
        "t3": True, "leftover": True,
    },
    "hexoptics_c44": {
        "name": "Hexoptics C44", "cost": 2900, "tier": "legendary",
        "stats": {"ad": 55, "crit": 0.25},
        "credits": ["long_sword"], "hex": True,
    },
    "the_collector": {
        "name": "The Collector", "cost": 3000, "tier": "legendary",
        "stats": {"ad": 50, "crit": 0.25, "lethality": 12},
        "credits": ["long_sword"], "collector": True,
    },
    "infinity_edge": {
        "name": "Infinity Edge", "cost": 3500, "tier": "legendary",
        "stats": {"ad": 75, "crit": 0.25, "crit_damage": 0.30},
        "ie": True,
    },
    "rapid_firecannon": {
        "name": "Rapid Firecannon", "cost": 2650, "tier": "legendary",
        "stats": {"crit": 0.25, "as": 0.40},
        "rfc": True, "energized": True,
    },
    "stormrazor": {
        "name": "Stormrazor", "cost": 3000, "tier": "legendary",
        "stats": {"ad": 50, "crit": 0.25, "as": 0.20},
        "storm": True, "energized": True,
    },
    "yun_tal_wildarrows": {
        "name": "Yun Tal Wildarrows", "cost": 3100, "tier": "legendary",
        "stats": {"ad": 50, "as": 0.25},
        "yun": True,
    },
    "statikk_shiv": {
        "name": "Statikk Shiv", "cost": 3000, "tier": "legendary",
        "stats": {"ad": 40, "ap": 40, "as": 0.30},
        "statikk": True, "energized": True,
    },
    "essence_reaver": {
        "name": "Essence Reaver", "cost": 3000, "tier": "legendary",
        "stats": {"ad": 50, "crit": 0.25, "ah": 20},
        "er": True,
    },
    "navori_quickblades": {
        "name": "Navori Quickblades", "cost": 2650, "tier": "legendary",
        "stats": {"as": 0.40, "crit": 0.25},
        "navori": True,
    },
    "galeforce": {
        "name": "Galeforce", "cost": 3100, "tier": "legendary",
        "stats": {"ad": 60, "crit": 0.25},
        "credits": ["long_sword"],
    },
    "lord_dominiks_regards": {
        "name": "Lord Dominik's Regards", "cost": 3300, "tier": "legendary",
        "stats": {"ad": 35, "crit": 0.25, "armor_pen": 0.35},
        "ldr": True,
    },
    "mortal_reminder": {
        "name": "Mortal Reminder", "cost": 3000, "tier": "legendary",
        "stats": {"ad": 35, "crit": 0.25, "armor_pen": 0.30},
    },
    "bloodthirster": {
        "name": "Bloodthirster", "cost": 3200, "tier": "legendary",
        "stats": {"ad": 75, "lifesteal": 0.15},
    },
    "immortal_shieldbow": {
        "name": "Immortal Shieldbow", "cost": 3000, "tier": "legendary",
        "stats": {"ad": 55, "crit": 0.25},
    },
    "fiendhunter_bolts": {
        "name": "Fiendhunter Bolts", "cost": 2650, "tier": "legendary",
        "stats": {"crit": 0.25, "as": 0.45},
        "fiend": True,
    },
    "youmuus_ghostblade": {
        "name": "Youmuu's Ghostblade", "cost": 3000, "tier": "legendary",
        "stats": {"ad": 55, "ah": 15, "lethality": 15},
        "credits": ["long_sword"], "leftover": True, "youmuu": True,
    },
    "duskblade": {
        "name": "Duskblade of Draktharr", "cost": 3000, "tier": "legendary",
        "stats": {"ad": 55, "ah": 10, "lethality": 18},
        "credits": ["long_sword"], "leftover": True, "drak": True,
    },
    "seryldas_grudge": {
        "name": "Serylda's Grudge", "cost": 3100, "tier": "legendary",
        "stats": {"ad": 50, "ah": 20, "armor_pen": 0.35},
    },
    "serpents_fang": {
        "name": "Serpent's Fang", "cost": 2800, "tier": "legendary",
        "stats": {"ad": 50, "ah": 10, "lethality": 15},
        "leftover": True,
    },
    "black_cleaver": {
        "name": "Black Cleaver", "cost": 3000, "tier": "legendary",
        "stats": {"ad": 40, "ah": 20, "hp": 400},
        "leftover": True, "cleaver": True,
    },
}


REMOVED_7_3 = ("Magnetic Blaster", "Cloak of Agility")


@dataclass
class Stats:
    ad: float = 0
    ap: float = 0
    ah: float = 0
    as_bonus: float = 0
    crit: float = 0
    lethality: float = 0
    armor_pen: float = 0
    crit_damage: float = CRIT_BASE
    names: List[str] = field(default_factory=list)
    hex: bool = False
    rfc: bool = False
    storm: bool = False
    statikk: bool = False
    collector: bool = False
    ie: bool = False
    er: bool = False
    navori: bool = False
    drak: bool = False
    youmuu: bool = False
    yun: bool = False
    ldr: bool = False
    fiend: bool = False
    cleaver: bool = False
    scythe: bool = False


def item_name(iid: str) -> str:
    return ITEMS[iid]["name"]


def aggregate(owned: List[str], mist: float, yun_crit: float, minute: int) -> Stats:
    st = Stats(names=[item_name(i) for i in owned])
    for iid in owned:
        it = ITEMS[iid]
        s = it["stats"]
        st.ad += s.get("ad", 0)
        st.ap += s.get("ap", 0)
        st.ah += s.get("ah", 0)
        st.as_bonus += s.get("as", 0)
        st.crit += s.get("crit", 0)
        st.lethality += s.get("lethality", 0)
        st.armor_pen = min(0.45, st.armor_pen + s.get("armor_pen", 0))
        if s.get("crit_damage"):
            st.crit_damage = CRIT_BASE + s["crit_damage"]
        st.hex = st.hex or it.get("hex", False)
        st.rfc = st.rfc or it.get("rfc", False)
        st.storm = st.storm or it.get("storm", False)
        st.statikk = st.statikk or it.get("statikk", False)
        st.collector = st.collector or it.get("collector", False)
        st.ie = st.ie or it.get("ie", False)
        st.er = st.er or it.get("er", False)
        st.navori = st.navori or it.get("navori", False)
        st.drak = st.drak or it.get("drak", False)
        st.youmuu = st.youmuu or it.get("youmuu", False)
        st.yun = st.yun or it.get("yun", False)
        st.ldr = st.ldr or it.get("ldr", False)
        st.fiend = st.fiend or it.get("fiend", False)
        st.cleaver = st.cleaver or it.get("cleaver", False)
        st.scythe = st.scythe or it.get("scythe", False)
    if st.scythe:
        # Soul Force: +2 AD / stack, max 10, after the quest completes.
        st.ad += 2.0 * min(10.0, max(0.0, minute - SCYTHE_MINUTE))
    st.ad += mist * MIST_AD
    st.crit += MIST_CRIT * (mist // 20.0)
    if st.yun:
        st.crit += yun_crit
    if st.crit > 1.0:
        # 35% of excess crit → physical vamp. Damage uses 100% crit.
        st.crit = 1.0
    if st.ie:
        st.crit_damage = 2.30
    return st


def remaining_cost(iid: str, owned: List[str]) -> Tuple[int, List[str]]:
    it = ITEMS[iid]
    cost = it["cost"]
    consumed: List[str] = []
    for c in it.get("credits", []):
        if c in owned:
            cost -= ITEMS[c]["cost"]
            consumed.append(c)
    return max(0, cost), consumed


def owned_at_gold(path: List[str], gold: int, minute: int, role: str) -> List[str]:
    """Buy in order. Do not skip a hole to grab a cheaper later item —
    that made RFC appear at 16:00 and vanish when IE completed at 20:00."""
    del role  # signature kept for call sites
    owned: List[str] = []
    spent = 0
    for iid in path:
        if iid == "spectral_sickle":
            owned.append(iid)
            spent += ITEMS[iid]["cost"]
            continue
        if iid == "black_mist_scythe":
            if minute >= SCYTHE_MINUTE:
                owned = [x for x in owned if x != "spectral_sickle"]
                owned.append(iid)
            continue
        it = ITEMS[iid]
        if it.get("t3") and minute < T3_MINUTE:
            break
        cost, consumed = remaining_cost(iid, owned)
        if spent + cost > gold:
            break
        for c in consumed:
            if c in owned:
                owned.remove(c)
        replaces = it.get("replaces")
        if replaces and replaces in owned:
            owned.remove(replaces)
        owned.append(iid)
        spent += cost
    return owned


def yun_crit_at(minute: int, role: str, has_yun: bool) -> float:
    if not has_yun:
        return 0.0
    # Ranged: 0.2% crit per auto, cap 25% (125 autos). Support autos less.
    if role == "adc":
        autos = 8 * minute  # farm + fights
    else:
        autos = 3 * minute
    return min(0.25, 0.002 * autos)


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ADC_PATHS: Dict[str, List[str]] = {
    # WRF 7.3 rec: Statikk identity after AS-ratio buff
    "statikk_rfc_ldr_ie": [
        "long_sword", "berserkers_greaves", "statikk_shiv",
        "rapid_firecannon", "lord_dominiks_regards", "infinity_edge",
        "galeforce",
    ],
    "statikk_rfc_ie_ldr": [
        "long_sword", "berserkers_greaves", "statikk_shiv",
        "rapid_firecannon", "infinity_edge", "lord_dominiks_regards",
        "bloodthirster",
    ],
    "statikk_hex_rfc_ldr": [
        "long_sword", "berserkers_greaves", "statikk_shiv",
        "hexoptics_c44", "rapid_firecannon", "lord_dominiks_regards",
        "infinity_edge",
    ],
    "statikk_rfc_hex_ie": [
        "long_sword", "berserkers_greaves", "statikk_shiv",
        "rapid_firecannon", "hexoptics_c44", "infinity_edge",
        "lord_dominiks_regards",
    ],
    # Hexoptics = Magnetic replacement (range amp + 55 AD / 25% crit)
    "hex_col_ie_rfc_ldr": [
        "long_sword", "berserkers_greaves", "hexoptics_c44",
        "the_collector", "infinity_edge", "rapid_firecannon",
        "lord_dominiks_regards",
    ],
    "hex_col_ie_ldr_bt": [
        "long_sword", "berserkers_greaves", "hexoptics_c44",
        "the_collector", "infinity_edge", "lord_dominiks_regards",
        "bloodthirster",
    ],
    "hex_col_rfc_ie_ldr": [
        "long_sword", "berserkers_greaves", "hexoptics_c44",
        "the_collector", "rapid_firecannon", "infinity_edge",
        "lord_dominiks_regards",
    ],
    "hex_rfc_ie_ldr_bt": [
        "long_sword", "berserkers_greaves", "hexoptics_c44",
        "rapid_firecannon", "infinity_edge", "lord_dominiks_regards",
        "bloodthirster",
    ],
    "hex_ie_rfc_ldr_bt": [
        "long_sword", "berserkers_greaves", "hexoptics_c44",
        "infinity_edge", "rapid_firecannon", "lord_dominiks_regards",
        "bloodthirster",
    ],
    "hex_er_rfc_ie_ldr": [
        "long_sword", "berserkers_greaves", "hexoptics_c44",
        "essence_reaver", "rapid_firecannon", "infinity_edge",
        "lord_dominiks_regards",
    ],
    "er_hex_rfc_ie_ldr": [
        "long_sword", "berserkers_greaves", "essence_reaver",
        "hexoptics_c44", "rapid_firecannon", "infinity_edge",
        "lord_dominiks_regards",
    ],
    "hex_navori_rfc_ie_ldr": [
        "long_sword", "berserkers_greaves", "hexoptics_c44",
        "navori_quickblades", "rapid_firecannon", "infinity_edge",
        "lord_dominiks_regards",
    ],
    # Instant-crit first items
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
    # 7.2 leftover lethality, Hexoptics instead of Magnetic
    "drak_col_hex_serylda": [
        "long_sword", "boots_of_dynamism", "duskblade",
        "the_collector", "hexoptics_c44", "seryldas_grudge",
        "armorcrusher",
    ],
    "youmuu_col_hex_ie_ldr": [
        "long_sword", "boots_of_dynamism", "youmuus_ghostblade",
        "the_collector", "hexoptics_c44", "infinity_edge",
        "lord_dominiks_regards",
    ],
    "youmuu_hex_ie_rfc_ldr": [
        "long_sword", "berserkers_greaves", "youmuus_ghostblade",
        "hexoptics_c44", "infinity_edge", "rapid_firecannon",
        "lord_dominiks_regards",
    ],
    # Dynamism on the Hex core (sword into boots, not Hex)
    "hex_col_ie_rfc_dyn": [
        "long_sword", "boots_of_dynamism", "hexoptics_c44",
        "the_collector", "infinity_edge", "rapid_firecannon",
        "lord_dominiks_regards",
    ],
    "fiend_hex_ie_rfc_ldr": [
        "long_sword", "berserkers_greaves", "hexoptics_c44",
        "fiendhunter_bolts", "infinity_edge", "rapid_firecannon",
        "lord_dominiks_regards",
    ],
}

ADC_LABEL = {
    "statikk_rfc_ldr_ie": "Statikk → RFC → LDR → IE → Galeforce",
    "statikk_rfc_ie_ldr": "Statikk → RFC → IE → LDR → BT",
    "statikk_hex_rfc_ldr": "Statikk → Hex → RFC → LDR → IE",
    "statikk_rfc_hex_ie": "Statikk → RFC → Hex → IE → LDR",
    "hex_col_ie_rfc_ldr": "Hex → Collector → IE → RFC → LDR",
    "hex_col_ie_ldr_bt": "Hex → Collector → IE → LDR → BT",
    "hex_col_rfc_ie_ldr": "Hex → Collector → RFC → IE → LDR",
    "hex_rfc_ie_ldr_bt": "Hex → RFC → IE → LDR → BT",
    "hex_ie_rfc_ldr_bt": "Hex → IE → RFC → LDR → BT",
    "hex_er_rfc_ie_ldr": "Hex → ER → RFC → IE → LDR",
    "er_hex_rfc_ie_ldr": "ER → Hex → RFC → IE → LDR",
    "hex_navori_rfc_ie_ldr": "Hex → Navori → RFC → IE → LDR",
    "storm_ie_rfc_ldr_bt": "Stormrazor → IE → RFC → LDR → BT",
    "col_ie_rfc_ldr_bt": "Collector → IE → RFC → LDR → BT",
    "yun_ie_rfc_ldr_bt": "Yun Tal → IE → RFC → LDR → BT",
    "gale_ie_rfc_ldr_bt": "Galeforce → IE → RFC → LDR → BT",
    "drak_col_hex_serylda": "Draktharr → Collector → Hex → Serylda",
    "youmuu_col_hex_ie_ldr": "Youmuu → Collector → Hex → IE → LDR",
    "youmuu_hex_ie_rfc_ldr": "Youmuu → Hex → IE → RFC → LDR",
    "hex_col_ie_rfc_dyn": "Dynamism Hex → Collector → IE → RFC → LDR",
    "fiend_hex_ie_rfc_ldr": "Hex → Fiendhunter → IE → RFC → LDR",
}

SUP_PATHS: Dict[str, List[str]] = {
    "statikk_rfc_ldr": [
        "spectral_sickle", "black_mist_scythe", "berserkers_greaves",
        "statikk_shiv", "rapid_firecannon", "lord_dominiks_regards",
        "infinity_edge",
    ],
    "statikk_hex_rfc": [
        "spectral_sickle", "black_mist_scythe", "berserkers_greaves",
        "statikk_shiv", "hexoptics_c44", "rapid_firecannon",
        "mortal_reminder",
    ],
    "hex_mortal_rfc": [
        "spectral_sickle", "black_mist_scythe", "berserkers_greaves",
        "hexoptics_c44", "mortal_reminder", "rapid_firecannon",
        "infinity_edge",
    ],
    "hex_col_rfc": [
        "spectral_sickle", "black_mist_scythe", "berserkers_greaves",
        "hexoptics_c44", "the_collector", "rapid_firecannon",
        "mortal_reminder",
    ],
    "hex_er_rfc": [
        "spectral_sickle", "black_mist_scythe", "berserkers_greaves",
        "hexoptics_c44", "essence_reaver", "rapid_firecannon",
        "mortal_reminder",
    ],
    "hex_rfc_mortal": [
        "spectral_sickle", "black_mist_scythe", "berserkers_greaves",
        "hexoptics_c44", "rapid_firecannon", "mortal_reminder",
        "infinity_edge",
    ],
    "dyn_hex_mortal": [
        "spectral_sickle", "black_mist_scythe", "boots_of_dynamism",
        "hexoptics_c44", "mortal_reminder", "the_collector",
        "armorcrusher",
    ],
    "dyn_statikk_rfc": [
        "spectral_sickle", "black_mist_scythe", "boots_of_dynamism",
        "statikk_shiv", "rapid_firecannon", "hexoptics_c44",
        "mortal_reminder",
    ],
    "dyn_drak_col": [
        "spectral_sickle", "black_mist_scythe", "boots_of_dynamism",
        "duskblade", "the_collector", "hexoptics_c44",
        "serpents_fang",
    ],
    "dyn_hex_serpent": [
        "spectral_sickle", "black_mist_scythe", "boots_of_dynamism",
        "hexoptics_c44", "serpents_fang", "mortal_reminder",
        "armorcrusher",
    ],
    "ionian_hex_er": [
        "spectral_sickle", "black_mist_scythe", "ionian_boots",
        "hexoptics_c44", "essence_reaver", "rapid_firecannon",
        "mortal_reminder",
    ],
    "statikk_cleaver_hex": [
        "spectral_sickle", "black_mist_scythe", "berserkers_greaves",
        "statikk_shiv", "black_cleaver", "hexoptics_c44",
        "rapid_firecannon",
    ],
    "steel_hex_mortal": [
        "spectral_sickle", "black_mist_scythe", "plated_steelcaps",
        "hexoptics_c44", "mortal_reminder", "rapid_firecannon",
        "serpents_fang",
    ],
}

SUP_LABEL = {
    "statikk_rfc_ldr": "Berserkers · Statikk → RFC → LDR",
    "statikk_hex_rfc": "Berserkers · Statikk → Hex → RFC",
    "hex_mortal_rfc": "Berserkers · Hex → Mortal → RFC",
    "hex_col_rfc": "Berserkers · Hex → Collector → RFC",
    "hex_er_rfc": "Berserkers · Hex → ER → RFC",
    "hex_rfc_mortal": "Berserkers · Hex → RFC → Mortal",
    "dyn_hex_mortal": "Dynamism · Hex → Mortal → Collector",
    "dyn_statikk_rfc": "Dynamism · Statikk → RFC → Hex",
    "dyn_drak_col": "Dynamism · Draktharr → Collector → Hex",
    "dyn_hex_serpent": "Dynamism · Hex → Serpent's → Mortal",
    "ionian_hex_er": "Ionian · Hex → ER → RFC",
    "statikk_cleaver_hex": "Berserkers · Statikk → Cleaver → Hex",
    "steel_hex_mortal": "Steelcaps · Hex → Mortal → RFC",
}


@dataclass
class Target:
    name: str
    hp: float
    armor: float
    mr: float


def squishy(minute: int, role: str) -> Target:
    lv = level_at(minute, role)
    return Target(
        "squishy",
        520.0 + 85.0 * lv + 15.0 * minute,
        28.0 + 3.2 * lv + (0.0 if minute < 12 else 20.0),
        30.0 + 1.2 * lv,
    )


def tank(minute: int, role: str) -> Target:
    lv = level_at(minute, role)
    return Target(
        "tank",
        900.0 + 140.0 * lv + 40.0 * minute,
        55.0 + 5.5 * lv + (0.0 if minute < 12 else 35.0),
        38.0 + 2.0 * lv,
    )


@dataclass
class Fight:
    damage: float = 0.0
    heal: float = 0.0
    shield: float = 0.0
    physical: float = 0.0
    magic: float = 0.0
    autos: float = 0.0
    q_casts: float = 0.0
    aspd: float = 0.0
    crit: float = 0.0
    crit_dmg: float = CRIT_BASE
    ad: float = 0.0
    notes: List[str] = field(default_factory=list)


def q_interval(ah: float, aspd: float, navori: bool) -> float:
    """15s Q. Each auto refunds 1s. Navori shaves 15% remaining per auto."""
    q_cd = max(4.5, ah_cd(15.0, ah))
    # Autos during the CD: aspd * q_cd, each -1s, floor so refunds cannot
    # zero the spell. Closed form from the Senna boots sim, then Navori.
    interval = max(3.2, (q_cd - 1.0) / (1.0 + aspd))
    if navori:
        interval *= 0.85
    return interval


def simulate_fight(
    owned: List[str],
    minute: int,
    role: str,
    target: Target,
    keystone: str = "fleet",
) -> Fight:
    level = level_at(minute, role)
    mist = mist_at(minute, role)
    yun = yun_crit_at(minute, role, "yun_tal_wildarrows" in owned)
    st = aggregate(owned, mist, yun, minute)

    alacrity = min(ALACRITY_CAP, max(0.0, (minute - 2) / 8.0 * ALACRITY_CAP))
    zombie = 0.0
    if role == "support":
        zombie = 3.0 * min(5.0, max(0.0, minute / 4.0))  # Zombie Ward AD
    bonus_as = st.as_bonus + alacrity
    lt_stacks = 0.0
    if keystone == "lt":
        lt_stacks = 4.0 if role == "adc" else 3.0
        bonus_as += LT_AS * lt_stacks
    if st.youmuu:
        bonus_as += 0.25 * (4.0 / FIGHT)  # Spectral Haste 4s of the window
    aspd = senna_as(level, bonus_as)

    qr, wr, rr = skill_rank(level, "Q"), skill_rank(level, "W"), skill_rank(level, "R")
    bonus_ad = st.ad  # includes mist; no AD/level
    total_ad = BASE_AD + bonus_ad + zombie
    ah = st.ah
    if keystone == "lt":
        pass
    interval = q_interval(ah, aspd, st.navori)
    q_casts = FIGHT / interval
    w_cd = max(4.0, ah_cd(11.0, ah))
    w_casts = FIGHT / w_cd * (0.55 if role == "adc" else 0.70)

    land = 0.88 if role == "adc" else 0.48
    q_land = 0.90 if role == "adc" else 0.82
    autos = aspd * FIGHT * land

    crit = st.crit
    # Autos: 90% of (200% / 230%). Relic on-hit does not crit.
    auto_crit_mult = SENNA_CRIT_FACTOR * st.crit_damage
    avg_auto = total_ad * (1.0 + crit * (auto_crit_mult - 1.0) + RELIC) + BRUTAL
    if keystone == "fleet":
        # Empowered auto once: +40% AS is already a small cadence bump;
        # damage is the same auto. Keep identity, no extra damage.
        pass

    hex_amp = 0.0
    if st.hex:
        # Senna already kites past 550. RFC extra range keeps the 10% lock.
        hex_amp = 0.10 if st.rfc else 0.09

    carve = 0.18 if st.cleaver else 0.0  # 3 Carve stacks on a ranged 8s poke
    pen = min(0.45, st.armor_pen + carve)

    def phys(amount: float, basic: bool = False) -> float:
        amt = amount * armor_mult(target.armor, st.lethality, pen)
        if basic:
            amt *= 1.0 + hex_amp
        if st.ldr and target.name == "tank":
            amt *= 1.12
        if target.name == "tank":
            amt *= 1.0 + CUT_DOWN
        return amt

    def mag(amount: float) -> float:
        amt = amount * mag_mult(target.mr)
        if target.name == "tank":
            amt *= 1.0 + CUT_DOWN
        return amt

    auto_dmg = phys(autos * avg_auto, basic=True)

    # Q crits as an ability (full 200%/230%), applies on-hit (Relic, Brutal,
    # Spellblade). 7.3 "90% crit" line is on basic attacks.
    q_base = q_damage(qr, bonus_ad)
    q_onhit = RELIC * total_ad + BRUTAL
    if st.er:
        q_onhit += 1.35 * BASE_AD + 0.80 * (crit * 100.0)
    q_hit = (q_base * (1.0 + crit * (st.crit_damage - 1.0)) + q_onhit)
    q_dmg = phys(q_casts * q_land * q_hit, basic=True)

    w_dmg = phys(w_casts * w_damage(wr, bonus_ad))

    r_dmg = 0.0
    if rr > 0:
        r_land = 0.70 if role == "adc" else 0.55
        r_dmg = phys(r_land * r_damage(rr, bonus_ad, st.ap))

    extract = phys(extraction_pct(level) * 0.70 * target.hp)  # AA→Q, HP still high

    energized_hits = autos + q_casts * q_land
    per_hit = 12.0 + (5.0 if st.statikk else 0.0)
    procs = 0.0
    if st.rfc or st.storm or st.statikk:
        procs = min(3.0, 1.0 + energized_hits * per_hit / 100.0 * 0.45)

    mag_on_proc = 0.0
    if st.rfc:
        mag_on_proc += 80.0
    if st.storm:
        mag_on_proc += 120.0
    if st.statikk:
        mag_on_proc += 60.0 + 0.15 * st.ap
    energ_dmg = mag(procs * mag_on_proc)

    extra = 0.0
    if st.drak:
        extra += phys(nightstalker(level))
    if st.collector:
        extra += 0.05 * target.hp * 0.45
    if st.fiend and rr > 0:
        # Opening Barrage empowers the next 3 autos (does not add autos).
        # Guaranteed crit at 80% of crit damage; if already critting, +15% true.
        barrage_mult = SENNA_CRIT_FACTOR * st.crit_damage * 0.80
        already = 1.0 + crit * (auto_crit_mult - 1.0)
        per_auto = max(0.0, total_ad * (barrage_mult - already))
        extra += phys(3.0 * 0.70 * per_auto, basic=True)
        if crit >= 0.90:
            extra += 3.0 * 0.70 * 0.15 * avg_auto

    dh = 0.0
    if keystone == "dark_harvest":
        souls = max(0.0, float(minute - 4) * (4.2 if role == "adc" else 1.6))
        dh = phys((DH_BASE + DH_SOUL * min(40.0, souls / 4.0) + DH_AD * bonus_ad) * 0.85)

    lt_bolt = 0.0
    if keystone == "lt":
        bolt = lerp(LT_BOLT[0], LT_BOLT[1], level)
        bolt *= 1.0 + 0.0067 * (st.as_bonus * 100.0)
        lt_bolt = mag(autos * 0.35 * bolt)

    emp = 0.0
    if keystone == "empowered":
        emp = phys(lerp(20.0, 60.0, level) * 0.80)

    total = auto_dmg + q_dmg + w_dmg + r_dmg + extract + energ_dmg + extra + dh + lt_bolt + emp
    heal = q_heal(qr, bonus_ad, st.ap) * q_casts * (1.55 if role == "support" else 0.40)
    if keystone == "fleet":
        heal += (lerp(15.0, 110.0, level) + 0.15 * bonus_ad) * min(2.0, autos / 4.0)
    shield = r_shield(rr, st.ap, mist) * (1.4 if role == "support" else 0.5)

    notes = []
    if st.hex:
        notes.append(f"Hex +{hex_amp:.0%} far")
    if st.statikk:
        notes.append("Statikk")
    if st.rfc:
        notes.append("RFC")
    if st.ie:
        notes.append("IE 230%")
    if st.drak:
        notes.append("Draktharr")
    if "Magnetic" in " ".join(st.names):
        notes.append("ILLEGAL Magnetic")

    return Fight(
        damage=total,
        heal=heal,
        shield=shield,
        physical=auto_dmg + q_dmg + w_dmg + r_dmg + extract + extra,
        magic=energ_dmg + lt_bolt,
        autos=autos,
        q_casts=q_casts,
        aspd=aspd,
        crit=crit,
        crit_dmg=st.crit_damage,
        ad=total_ad,
        notes=notes,
    )


def snapshot(role: str, path_key: str, minute: int, keystone: str = "fleet") -> Dict:
    paths = ADC_PATHS if role == "adc" else SUP_PATHS
    path = paths[path_key]
    gold = gold_at(minute, role)
    owned = owned_at_gold(path, gold, minute, role)
    mist = mist_at(minute, role)
    sq = simulate_fight(owned, minute, role, squishy(minute, role), keystone)
    tk = simulate_fight(owned, minute, role, tank(minute, role), keystone)
    legendaries = [i for i in owned if ITEMS[i]["tier"] == "legendary"]
    boots = [i for i in owned if ITEMS[i]["tier"] == "boots"]
    return {
        "role": role,
        "path": path_key,
        "label": (ADC_LABEL if role == "adc" else SUP_LABEL)[path_key],
        "minute": minute,
        "gold": gold,
        "level": level_at(minute, role),
        "mist": round(mist, 1),
        "owned": [item_name(i) for i in owned],
        "ids": owned,
        "legendaries": len(legendaries),
        "boots": [item_name(i) for i in boots],
        "ad": round(sq.ad, 1),
        "aspd": round(sq.aspd, 3),
        "crit": round(sq.crit * 100.0, 1),
        "crit_dmg": round(sq.crit_dmg * 100.0),
        "q_casts": round(sq.q_casts, 2),
        "sq_dmg": round(sq.damage, 1),
        "tk_dmg": round(tk.damage, 1),
        "heal": round(sq.heal, 1),
        "shield": round(sq.shield, 1),
        "impact": round(sq.damage + (0.65 * sq.heal if role == "support" else 0.0), 1),
        "notes": sq.notes,
        "keystone": keystone,
    }


def area(role: str, path_key: str, keystone: str = "fleet") -> float:
    minutes = ADC_MINUTES if role == "adc" else SUP_MINUTES
    total = 0.0
    for m in minutes:
        snap = snapshot(role, path_key, m, keystone)
        total += snap["impact"] if role == "support" else snap["sq_dmg"]
    return total


def first_legendary_minute(role: str, path_key: str) -> Optional[int]:
    paths = ADC_PATHS if role == "adc" else SUP_PATHS
    cap = 24 if role == "adc" else 20
    for m in range(1, cap + 1):
        owned = owned_at_gold(paths[path_key], gold_at(m, role), m, role)
        if any(ITEMS[i]["tier"] == "legendary" for i in owned):
            return m
    return None


def scoreboard(role: str) -> List[Tuple[str, float]]:
    paths = ADC_PATHS if role == "adc" else SUP_PATHS
    ranked = [(k, area(role, k)) for k in paths]
    ranked.sort(key=lambda kv: kv[1], reverse=True)
    return ranked


KEYSTONES = (
    ("fleet", "Fleet Footwork"),
    ("lt", "Lethal Tempo"),
    ("dark_harvest", "Dark Harvest"),
    ("empowered", "Empowered Attack (no keystone dmg)"),
)


ADC_PAGES = [
    {
        "name": "Lethal Tempo · Brutal · Cut Down · Alacrity · Bone Plating",
        "keystone": "lt",
        "primary": ["Brutal", "Cut Down", "Legend: Alacrity"],
        "secondary": "Bone Plating",
    },
    {
        "name": "Fleet · Brutal · Cut Down · Alacrity · Bone Plating",
        "keystone": "fleet",
        "primary": ["Brutal", "Cut Down", "Legend: Alacrity"],
        "secondary": "Bone Plating",
    },
    {
        "name": "Dark Harvest · Brutal · Coup de Grace · Alacrity · Bone Plating",
        "keystone": "dark_harvest",
        "primary": ["Brutal", "Coup de Grace", "Legend: Alacrity"],
        "secondary": "Bone Plating",
    },
]

SUP_PAGES = [
    {
        "name": "Fleet · Font of Life · Bone Plating · Perseverance · Brutal",
        "keystone": "fleet",
        "primary": ["Font of Life", "Bone Plating", "Perseverance"],
        "secondary": "Brutal",
    },
    {
        "name": "Fleet · Font of Life · Bone Plating · Perseverance · Zombie Ward",
        "keystone": "fleet",
        "primary": ["Font of Life", "Bone Plating", "Perseverance"],
        "secondary": "Zombie Ward",
    },
    {
        "name": "Lethal Tempo · Brutal · Cut Down · Alacrity · Bone Plating",
        "keystone": "lt",
        "primary": ["Brutal", "Cut Down", "Legend: Alacrity"],
        "secondary": "Bone Plating",
    },
    {
        "name": "Dark Harvest · Brutal · Coup de Grace · Zombie Ward · Bone Plating",
        "keystone": "dark_harvest",
        "primary": ["Brutal", "Coup de Grace", "Zombie Ward"],
        "secondary": "Bone Plating",
    },
]


def six_slot(owned: List[str]) -> List[str]:
    """Display order: legendaries + boots, scythe counts as the support slot."""
    ordered = []
    for iid in owned:
        if ITEMS[iid]["tier"] in ("legendary", "boots", "support"):
            ordered.append(item_name(iid))
    return ordered


def write_report() -> Dict:
    adc_rank = scoreboard("adc")
    sup_rank = scoreboard("support")
    adc_win, adc_score = adc_rank[0]
    sup_win, sup_score = sup_rank[0]

    adc_ks = [(ks, area("adc", adc_win, ks)) for ks, _ in KEYSTONES]
    adc_ks.sort(key=lambda kv: kv[1], reverse=True)
    sup_ks = [(ks, area("support", sup_win, ks)) for ks, _ in KEYSTONES]
    sup_ks.sort(key=lambda kv: kv[1], reverse=True)

    lines: List[str] = []
    def p(s: str = "") -> None:
        lines.append(s)

    p("=" * 72)
    p("Wild Rift 7.3 — Senna ADC + support build sim")
    p("=" * 72)
    p()
    p("Magnetic Blaster is gone. Crit 175%→200%, Senna autos at 90% of that.")
    p("Mist crit 15%→10% per 20. AS ratio 0.4 (was ~0.125). Q 50/80/110/140.")
    p("HP 600→570. Extraction 1%–10% current HP.")
    p()
    p("Illegal in this sim: Magnetic Blaster, Cloak of Agility, Ingenious Hunter.")
    p()

    p("-" * 72)
    p("ADC winner  (24:00, Flash + Barrier, Fleet for the item rank)")
    p("-" * 72)
    p(f"  {ADC_LABEL[adc_win]}")
    p(f"  area {adc_score:.0f}  (sum of 8s squishy windows at 8/12/16/20/24)")
    win_owned = owned_at_gold(ADC_PATHS[adc_win], adc_gold(24), 24, "adc")
    p(f"  6-slot: {' · '.join(six_slot(win_owned))}")
    p(f"  first legendary: ~{first_legendary_minute('adc', adc_win)}:00")
    p()
    p("  Skill order: Q → W → E. R at 5/9/13.")
    p("  Combo: AA → Q (mark then extract while HP is still high), weave autos")
    p("  for the 1s Q refund. W for the root, R through the line.")
    p()

    p("  Minute table")
    p(f"  {'min':>4} {'gold':>6} {'mist':>5} {'AD':>6} {'AS':>5} {'crit':>5} {'sq 8s':>8} {'tk 8s':>8}  items")
    for m in ADC_MINUTES:
        s = snapshot("adc", adc_win, m)
        items = " › ".join(s["owned"])
        p(f"  {m:>4} {s['gold']:>6} {s['mist']:>5.0f} {s['ad']:>6.0f} {s['aspd']:>5.2f} {s['crit']:>4.0f}% {s['sq_dmg']:>8.0f} {s['tk_dmg']:>8.0f}  {items}")
    p()

    p("  ADC path ranking (Fleet, squishy area)")
    for i, (k, sc) in enumerate(adc_rank, 1):
        delta = (sc / adc_score - 1.0) * 100.0
        ready = first_legendary_minute("adc", k)
        p(f"  {i:>2}. {ADC_LABEL[k]:<48} {sc:>8.0f}  {delta:+5.1f}%  1st @{ready}:00")
    p()

    p("  Keystones on the ADC winner")
    for ks, sc in adc_ks:
        label = dict(KEYSTONES)[ks]
        delta = (sc / adc_ks[0][1] - 1.0) * 100.0
        p(f"    {label:<42} {sc:>8.0f}  {delta:+5.1f}%")
    p()

    p("-" * 72)
    p("Support winner  (20:00, Flash + Heal, Fleet for the item rank)")
    p("-" * 72)
    p(f"  {SUP_LABEL[sup_win]}")
    p(f"  area {sup_score:.0f}  (8s poke + 0.65× Q heal at 8/12/16/20)")
    sup_owned = owned_at_gold(SUP_PATHS[sup_win], support_gold(20), 20, "support")
    p(f"  slots: {' · '.join(six_slot(sup_owned))}")
    p(f"  first legendary: ~{first_legendary_minute('support', sup_win)}:00")
    p()
    p("  Skill order: Q → W, E 1-point, R at 5/9/13.")
    p("  Combo: Q through the minion/ally into the enemy carry (damage + heal),")
    p("  then AA to extract. Do not last-hit — wraiths spawn from ally CS.")
    p()

    p("  Minute table")
    p(f"  {'min':>4} {'gold':>6} {'mist':>5} {'AD':>6} {'AS':>5} {'crit':>5} {'poke':>8} {'heal':>7}  items")
    for m in SUP_MINUTES:
        s = snapshot("support", sup_win, m)
        items = " › ".join(s["owned"])
        p(f"  {m:>4} {s['gold']:>6} {s['mist']:>5.0f} {s['ad']:>6.0f} {s['aspd']:>5.2f} {s['crit']:>4.0f}% {s['sq_dmg']:>8.0f} {s['heal']:>7.0f}  {items}")
    p()

    p("  Support path ranking (Fleet, poke+heal area)")
    for i, (k, sc) in enumerate(sup_rank, 1):
        delta = (sc / sup_score - 1.0) * 100.0
        ready = first_legendary_minute("support", k)
        p(f"  {i:>2}. {SUP_LABEL[k]:<48} {sc:>8.0f}  {delta:+5.1f}%  1st @{ready}:00")
    p()

    p("  Keystones on the support winner")
    for ks, sc in sup_ks:
        label = dict(KEYSTONES)[ks]
        delta = (sc / sup_ks[0][1] - 1.0) * 100.0
        p(f"    {label:<42} {sc:>8.0f}  {delta:+5.1f}%")
    p()

    p("-" * 72)
    p("Why 7.3 kept lethality first on ADC and moved support onto Hexoptics")
    p("-" * 72)
    p("  • Mist crit 10%/20. At 8:00 an ADC has ~40 souls = 10% crit. Hexoptics'")
    p("    25% crit is real, but Youmuu's 55 AD + 15 lethality + 15 AH punches")
    p("    a squishy harder while souls are still low. Caitlyn rushes Hex")
    p("    because Headshot scales with crit immediately. Senna does not.")
    p("  • Collector 2nd is the 12:00 fill: 25% crit + 12 leth + execute,")
    p("    3000g, so you are not sitting on Youmuu waiting for a 3500g IE.")
    p("  • Hexoptics 3rd is the Magnetic replacement — 55 AD, 25% crit, +9–10%")
    p("    at the range Senna already lives at. Completes ~16:00 on ADC gold.")
    p("  • IE is 4th/5th. 3500g is a hole at 16:00 (Youmuu+Col+Hex is ~8900g")
    p("    of the 10180; IE needs 3500 more). It lands with LDR at ~24:00.")
    p("  • Autos crit for 90% of 200% = 180% (207% with IE). IE is still the")
    p("    late spike, just not the opener.")
    p("  • AS ratio 0.4 means Berserkers/RFC/Fiendhunter actually convert.")
    p("    They still lose 8:00 and 12:00 to lethality because Statikk/Yun Tal")
    p("    /Stormrazor buy 0–25% crit and little lethality while mist is empty.")
    p("    RFC is a 4th-item range card, not a first.")
    p("  • Yun Tal starts at 0% crit and needs 125 autos. Senna already")
    p("    builds crit from mist — do not stack a second delayed engine.")
    p("  • Draktharr is the dive Youmuu. Nightstalker is one proc; Youmuu")
    p("    keeps 15 AH + Spectral Haste for the AA→Q kite. Poke Senna")
    p("    wants Youmuu. All-in DH Senna can still Drak.")
    p("  • Support cannot buy Youmuu at 8:00. Sickle gold finishes Hexoptics")
    p("    ~11:00. Second legendary is Mortal (pen + grievous) or Essence")
    p("    Reaver (Q spellblade + 20 AH) — they tie on 20:00 gold. RFC 2nd")
    p("    delays AD/pen and loses. Statikk 1st has 0% crit and loses.")
    p()
    p("Traps")
    p("  • Magnetic Blaster / Cloak of Agility — deleted.")
    p("  • Hexoptics first on ADC, copying Caitlyn. Youmuu first is +6–7%")
    p("    on the 24-min area. Hex is 3rd, after Collector.")
    p("  • Yun Tal / Stormrazor first — delayed or expensive crit, no leth.")
    p("  • Statikk → RFC as the WRF page. Lightning is waveclear/clump.")
    p("    1v1 poke wants AD + lethality + Hex, not 0% crit Shiv.")
    p("  • IE second — 3500g hole. Collector 3000g fills 12:00.")
    p("  • Support finishing IE/LDR — 20-min sickle gold completes two")
    p("    legendaries. Hex then Mortal/ER. Third is a maybe.")
    p("  • Enchanter (Ardent → Helia → Harmonic) is a different question;")
    p("    that sim already picked Mandate 4th. This file is damage Senna.")
    p("  • Gathering Storm / Ingenious Hunter / Legend: Tenacity — illegal or")
    p("    wrong identity. Legend: Haste is fine if you skip Transcendence.")
    p()
    p("Swaps")
    p("  • ADC Hex 2nd (Youmuu → Hex, skip Collector) if you need the range")
    p("    amp before 12:00. -2.8% area, Hex lands at 12 instead of Collector.")
    p("  • Draktharr first if you are the DH dive Senna, not the poke Senna.")
    p("  • Mortal Reminder over LDR vs heal comps. Support already prefers it.")
    p("  • Essence Reaver 2nd on support is a coin-flip with Mortal. Take ER")
    p("    when the lane is Q-heal, Mortal when they have a healer.")
    p("  • Serpent's Fang 3rd vs Lulu/Karma/Janna/sett shields.")
    p("  • Shieldbow or GA 6th vs burst. Mercurial vs Malz/WW.")
    p("  • Steelcaps into all-in AD supports (Leona/Naut/Rell). -5% poke.")
    p("  • Ionian on support is -0.1% vs Berserkers+Hex+ER. Take it when")
    p("    Q/Flash cadence matters more than the auto (enchanter split).")
    p("  • AP carry lane partner: this is still an AD Senna page. Do not")
    p("    force Ardent on a damage page — that is the enchanter file.")
    p()

    p("Runes (legal 7.3 page: 1 keystone + 3 primary + 1 secondary)")
    p("  ADC combat: Lethal Tempo · Brutal · Cut Down · Legend: Alacrity · Bone Plating")
    p("              LT is +9% area on the Youmuu core. 7.3 LT scales with built AS;")
    p("              Youmuu's Spectral Haste + Alacrity give it something to eat.")
    p("  ADC lane:   Fleet Footwork on the same tree if you need the heal/MS to")
    p("              collect souls. -8% 8s damage, better 2v2 sustain.")
    p("  Support:    Fleet Footwork · Font of Life · Bone Plating · Perseverance · Brutal")
    p("              LT is only +2.3% poke. Keep Fleet + Font of Life.")
    p("  Spells ADC:  Flash + Barrier (Ghost if they cannot walk up).")
    p("  Spells supp: Flash + Heal (Exhaust vs dive).")
    p()
    p("Sources: official 7.3 notes; wr-7.3-db item snapshot; Wild Rift wiki kit;")
    p("WildRiftFire / wildriftguides 7.3 pages (live recs, not copied blindly).")

    text = "\n".join(lines) + "\n"
    report_path = os.path.join(OUT_DIR, "report.txt")
    with open(report_path, "w", encoding="utf-8") as fh:
        fh.write(text)

    payload = {
        "patch": PATCH,
        "removed": list(REMOVED_7_3),
        "adc_winner": adc_win,
        "adc_label": ADC_LABEL[adc_win],
        "adc_score": adc_score,
        "adc_rank": [{"key": k, "label": ADC_LABEL[k], "area": sc} for k, sc in adc_rank],
        "adc_keystones": [{"key": k, "area": sc} for k, sc in adc_ks],
        "support_winner": sup_win,
        "support_label": SUP_LABEL[sup_win],
        "support_score": sup_score,
        "support_rank": [{"key": k, "label": SUP_LABEL[k], "area": sc} for k, sc in sup_rank],
        "support_keystones": [{"key": k, "area": sc} for k, sc in sup_ks],
        "adc_minutes": [snapshot("adc", adc_win, m) for m in ADC_MINUTES],
        "support_minutes": [snapshot("support", sup_win, m) for m in SUP_MINUTES],
        "adc_pages": ADC_PAGES,
        "support_pages": SUP_PAGES,
    }
    json_path = os.path.join(OUT_DIR, "results.json")
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
        fh.write("\n")
    return payload


def main() -> None:
    payload = write_report()
    print(f"ADC winner:      {payload['adc_label']}")
    print(f"Support winner:  {payload['support_label']}")
    print(f"wrote {os.path.join(OUT_DIR, 'report.txt')}")
    print(f"wrote {os.path.join(OUT_DIR, 'results.json')}")


if __name__ == "__main__":
    main()
