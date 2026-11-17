#!/usr/bin/env python3
"""
Wild Rift Tryndamere Jungle — Farm, then Split
Patch 7.3 / 7.3b snapshot (live through 7.3f, Nov 2026).

Playstyle: full-clear the jungle, catch the side wave, do not force ganks.
Win condition: Undying Rage the champion who answers, then take the turret.

Question: which build wins that 1v1 AND cracks the tower on a farm gold curve?

Metric (weights applied so they hold at the 18:00 median):
  50% sidelane duel during the 5s Undying Rage window
  35% turret damage over the push
  15% how fast the side wave crashes
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from statistics import median
from typing import Dict, List, Optional, Tuple
import json

GAME_MINUTES = 26
R_WINDOW = 5.0
EARLY_WINDOW = 2.5

# 50% duel / 35% tower / 15% wave, calibrated at minute 18.
DUEL_W = 0.50
TOWER_W = 0.35
WAVE_W = 0.15


# ---------------------------------------------------------------------------
# Economy — powerfarm camps, then tax the side wave. Few early kills.
# Tuned so Yun Tal lands ~8:00 and a 16.3k six-slot build finishes ~26:00.
# ---------------------------------------------------------------------------


def gold_at_minute(m: int) -> int:
    if m <= 0:
        return 500
    total = 500  # Long Sword
    for t in range(1, m + 1):
        if t <= 4:
            total += 430
        elif t <= 8:
            total += 520
        elif t <= 13:
            total += 540
        elif t <= 18:
            total += 700
        elif t <= 22:
            total += 775
        else:
            total += 800
    return total


def level_at_minute(m: int) -> int:
    # Full clear: R at ~4:00, Q max (level 7) just before first item.
    table = {
        1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7, 7: 7, 8: 8,
        9: 9, 10: 10, 11: 10, 12: 11, 13: 11, 14: 12,
        15: 12, 16: 13, 17: 13, 18: 14, 19: 14, 20: 14,
        21: 15, 22: 15, 23: 15, 24: 15, 25: 15, 26: 15,
    }
    return table.get(m, min(15, 1 + m))


def skill_rank(level: int, skill: str) -> int:
    """Q max → E → W. R at 5 / 9 / 13. Q max is the duel; E still clears."""
    if skill == "R":
        if level < 5:
            return 0
        if level < 9:
            return 1
        if level < 13:
            return 2
        return 3
    q_levels = [1, 3, 6, 7]
    e_levels = [2, 8, 10, 11]
    w_levels = [4, 12, 14, 15]
    mapping = {"Q": q_levels, "E": e_levels, "W": w_levels}
    return sum(1 for lv in mapping[skill] if level >= lv)


def alacrity(m: int) -> float:
    # Camps and waves stack Legend: Alacrity. Cap 21% (3% + 18%).
    return min(0.21, 0.03 + 0.015 * m)


# ---------------------------------------------------------------------------
# Items — Wild Rift 7.3 shop (Yun Tal cost/AS after 7.3a–7.3b)
# ---------------------------------------------------------------------------


@dataclass
class Item:
    name: str
    cost: int
    ad: float = 0
    ap: float = 0
    ah: float = 0
    hp: float = 0
    as_pct: float = 0
    crit: float = 0
    armor: float = 0
    mr: float = 0
    lifesteal: float = 0
    pct_apen: float = 0
    flat_apen: float = 0
    spellblade: str = ""  # trinity | er | sheen
    botrk: bool = False
    yuntal: bool = False
    navori: bool = False
    ie: bool = False
    hull: bool = False
    kraken: bool = False
    guinsoo: bool = False
    storm: bool = False
    ldr: bool = False
    grievous: bool = False
    terminus: bool = False
    wit: bool = False
    dd: bool = False
    ga: bool = False


ITEMS: Dict[str, Item] = {
    "Long Sword": Item("Long Sword", 500, ad=12),
    "Dagger": Item("Dagger", 400, as_pct=0.12),
    "Brawler's Gloves": Item("Brawler's Gloves", 500, crit=0.10),
    "Ruby Crystal": Item("Ruby Crystal", 500, hp=200),
    "Boots": Item("Boots", 500),
    "Pickaxe": Item("Pickaxe", 800, ad=20),
    "Kircheis Shard": Item("Kircheis Shard", 800, as_pct=0.20),
    "Sheen": Item("Sheen", 800, ah=10, spellblade="sheen"),
    "Executioner's Calling": Item("Executioner's Calling", 800, ad=15, grievous=True),
    "Recurve Bow": Item("Recurve Bow", 900, as_pct=0.20),
    "Chain Vest": Item("Chain Vest", 900, armor=40),
    "Negatron Cloak": Item("Negatron Cloak", 900, mr=40),
    "Amplifying Tome": Item("Amplifying Tome", 500, ap=20),
    "Phage": Item("Phage", 1000, ad=15, hp=150),
    "Caulfield's Warhammer": Item("Caulfield's Warhammer", 1200, ad=25, ah=10),
    "Vampiric Scepter": Item("Vampiric Scepter", 1200, ad=20, lifesteal=0.08),
    "Last Whisper": Item("Last Whisper", 1200, ad=15, pct_apen=0.15),
    "Hearthbound Axe": Item("Hearthbound Axe", 1200, ad=20, as_pct=0.15),
    "Jaurim's Fist": Item("Jaurim's Fist", 1200, ad=15, hp=200),
    "Noonquiver": Item("Noonquiver", 1300, ad=20, crit=0.15),
    "Zeal": Item("Zeal", 1400, as_pct=0.15, crit=0.15),
    "BF Sword": Item("BF Sword", 1500, ad=40),
    "Berserker's Greaves": Item("Berserker's Greaves", 1200, as_pct=0.35),
    "Yun Tal Wildarrows": Item(
        "Yun Tal Wildarrows", 3000, ad=50, as_pct=0.35, yuntal=True
    ),
    "Navori Quickblades": Item(
        "Navori Quickblades", 2650, as_pct=0.40, crit=0.25, navori=True
    ),
    "Infinity Edge": Item("Infinity Edge", 3400, ad=75, crit=0.25, ie=True),
    "Blade of the Ruined King": Item(
        "Blade of the Ruined King",
        3100,
        ad=40,
        as_pct=0.30,
        lifesteal=0.12,
        botrk=True,
    ),
    "Mortal Reminder": Item(
        "Mortal Reminder",
        3000,
        ad=35,
        crit=0.25,
        pct_apen=0.30,
        grievous=True,
    ),
    "Lord Dominik's Regards": Item(
        "Lord Dominik's Regards",
        3300,
        ad=35,
        crit=0.25,
        pct_apen=0.35,
        ldr=True,
    ),
    "Hullbreaker": Item("Hullbreaker", 3100, ad=50, hp=400, hull=True),
    "Stormrazor": Item(
        "Stormrazor", 3000, ad=50, as_pct=0.20, crit=0.25, storm=True
    ),
    "Essence Reaver": Item(
        "Essence Reaver",
        3000,
        ad=55,
        crit=0.25,
        ah=20,
        spellblade="er",
    ),
    "Bloodthirster": Item("Bloodthirster", 3200, ad=75, lifesteal=0.15),
    "Kraken Slayer": Item(
        "Kraken Slayer", 2900, ad=45, as_pct=0.35, kraken=True
    ),
    "Guinsoo's Rageblade": Item(
        "Guinsoo's Rageblade", 3000, ad=35, ap=30, as_pct=0.30, guinsoo=True
    ),
    "Terminus": Item(
        "Terminus", 3000, ad=35, as_pct=0.35, pct_apen=0.20, terminus=True
    ),
    "Wit's End": Item("Wit's End", 2800, as_pct=0.50, mr=45, wit=True),
    "Trinity Force": Item(
        "Trinity Force",
        3333,
        ad=36,
        hp=333,
        as_pct=0.30,
        ah=15,
        spellblade="trinity",
    ),
    "Death's Dance": Item(
        "Death's Dance", 3300, ad=50, armor=45, ah=15, dd=True
    ),
    "Guardian Angel": Item("Guardian Angel", 3200, ad=45, armor=40, ga=True),
}


UPGRADE_COMPONENTS: Dict[str, Tuple[str, ...]] = {
    "Pickaxe": ("Long Sword",),
    "Kircheis Shard": ("Dagger", "Dagger"),
    "Recurve Bow": ("Dagger",),
    "Caulfield's Warhammer": ("Long Sword",),
    "Vampiric Scepter": ("Long Sword",),
    "Last Whisper": ("Long Sword",),
    "Hearthbound Axe": ("Long Sword", "Dagger"),
    "Jaurim's Fist": ("Long Sword", "Ruby Crystal"),
    "Noonquiver": ("Long Sword", "Brawler's Gloves"),
    "Zeal": ("Brawler's Gloves", "Dagger"),
    "BF Sword": ("Long Sword", "Long Sword", "Long Sword"),
    "Phage": ("Long Sword", "Ruby Crystal"),
    "Berserker's Greaves": ("Boots",),
    "Yun Tal Wildarrows": ("BF Sword", "Kircheis Shard"),
    "Navori Quickblades": ("Zeal", "Dagger", "Dagger"),
    "Infinity Edge": ("BF Sword", "Pickaxe", "Brawler's Gloves"),
    "Blade of the Ruined King": ("Vampiric Scepter", "Pickaxe", "Recurve Bow"),
    "Mortal Reminder": ("Last Whisper", "Executioner's Calling", "Brawler's Gloves"),
    "Lord Dominik's Regards": ("Last Whisper", "Noonquiver"),
    "Hullbreaker": ("Jaurim's Fist", "Jaurim's Fist"),
    "Stormrazor": ("BF Sword", "Kircheis Shard", "Brawler's Gloves"),
    "Essence Reaver": ("Sheen", "Caulfield's Warhammer", "Brawler's Gloves"),
    "Bloodthirster": ("Vampiric Scepter", "BF Sword"),
    "Kraken Slayer": ("Recurve Bow", "Hearthbound Axe", "Long Sword"),
    "Guinsoo's Rageblade": ("Amplifying Tome", "Recurve Bow", "Pickaxe"),
    "Terminus": ("Recurve Bow", "Hearthbound Axe"),
    "Wit's End": ("Recurve Bow", "Negatron Cloak", "Dagger"),
    "Trinity Force": ("Sheen", "Phage", "Hearthbound Axe"),
    "Death's Dance": ("Caulfield's Warhammer", "Chain Vest", "Pickaxe"),
    "Guardian Angel": ("BF Sword", "Chain Vest"),
}

DUPLICATES = {
    "Long Sword",
    "Dagger",
    "Ruby Crystal",
    "Jaurim's Fist",
    "Pickaxe",
    "Brawler's Gloves",
}

LEGENDARIES = {
    "Yun Tal Wildarrows",
    "Navori Quickblades",
    "Infinity Edge",
    "Blade of the Ruined King",
    "Mortal Reminder",
    "Lord Dominik's Regards",
    "Hullbreaker",
    "Stormrazor",
    "Essence Reaver",
    "Bloodthirster",
    "Kraken Slayer",
    "Guinsoo's Rageblade",
    "Terminus",
    "Wit's End",
    "Trinity Force",
    "Death's Dance",
    "Guardian Angel",
    "Berserker's Greaves",
}


# Farm-and-split paths. Same Q-max rune page on every row (Lethal Tempo,
# Last Stand, Alacrity, Demolish) so the items are the only difference.
BUILD_PATHS: Dict[str, List[str]] = {
    # WildriftAlpha / sheet crit
    "Yun → Navori → IE → BotRK → Mortal": [
        "Long Sword",
        "BF Sword",
        "Dagger",
        "Kircheis Shard",
        "Yun Tal Wildarrows",
        "Boots",
        "Berserker's Greaves",
        "Brawler's Gloves",
        "Zeal",
        "Dagger",
        "Dagger",
        "Navori Quickblades",
        "Pickaxe",
        "Brawler's Gloves",
        "Infinity Edge",
        "Vampiric Scepter",
        "Recurve Bow",
        "Blade of the Ruined King",
        "Last Whisper",
        "Executioner's Calling",
        "Mortal Reminder",
    ],
    # Tower item second — the push is the win condition
    "Yun → Hull → IE → Navori → LDR": [
        "Long Sword",
        "BF Sword",
        "Dagger",
        "Kircheis Shard",
        "Yun Tal Wildarrows",
        "Boots",
        "Berserker's Greaves",
        "Ruby Crystal",
        "Jaurim's Fist",
        "Long Sword",
        "Ruby Crystal",
        "Jaurim's Fist",
        "Hullbreaker",
        "Pickaxe",
        "Brawler's Gloves",
        "Infinity Edge",
        "Brawler's Gloves",
        "Zeal",
        "Dagger",
        "Navori Quickblades",
        "Last Whisper",
        "Noonquiver",
        "Lord Dominik's Regards",
    ],
    # Capstone second: each auto hits before the tower item
    "Yun → IE → Navori → Hull → BotRK": [
        "Long Sword",
        "BF Sword",
        "Dagger",
        "Kircheis Shard",
        "Yun Tal Wildarrows",
        "Boots",
        "Berserker's Greaves",
        "Pickaxe",
        "Brawler's Gloves",
        "Infinity Edge",
        "Zeal",
        "Dagger",
        "Dagger",
        "Navori Quickblades",
        "Ruby Crystal",
        "Jaurim's Fist",
        "Long Sword",
        "Ruby Crystal",
        "Jaurim's Fist",
        "Hullbreaker",
        "Vampiric Scepter",
        "Recurve Bow",
        "Blade of the Ruined King",
    ],
    # Guide "ahead" line: BotRK into the duelist who matches you
    "Yun → BotRK → IE → Hull → LDR": [
        "Long Sword",
        "BF Sword",
        "Dagger",
        "Kircheis Shard",
        "Yun Tal Wildarrows",
        "Boots",
        "Berserker's Greaves",
        "Vampiric Scepter",
        "Recurve Bow",
        "Pickaxe",
        "Blade of the Ruined King",
        "Brawler's Gloves",
        "Infinity Edge",
        "Ruby Crystal",
        "Jaurim's Fist",
        "Long Sword",
        "Ruby Crystal",
        "Jaurim's Fist",
        "Hullbreaker",
        "Last Whisper",
        "Noonquiver",
        "Lord Dominik's Regards",
    ],
    # Immediate crit instead of waiting on Practice Makes Perfect
    "Yun → Storm → IE → Hull → Navori": [
        "Long Sword",
        "BF Sword",
        "Dagger",
        "Kircheis Shard",
        "Yun Tal Wildarrows",
        "Boots",
        "Berserker's Greaves",
        "BF Sword",
        "Brawler's Gloves",
        "Kircheis Shard",
        "Stormrazor",
        "Pickaxe",
        "Infinity Edge",
        "Ruby Crystal",
        "Jaurim's Fist",
        "Long Sword",
        "Ruby Crystal",
        "Jaurim's Fist",
        "Hullbreaker",
        "Zeal",
        "Dagger",
        "Navori Quickblades",
    ],
    # Spellblade spins: sheen on the tower, no Yun Tal ramp
    "ER → Navori → IE → Hull → BT": [
        "Long Sword",
        "Sheen",
        "Caulfield's Warhammer",
        "Brawler's Gloves",
        "Essence Reaver",
        "Boots",
        "Berserker's Greaves",
        "Zeal",
        "Dagger",
        "Dagger",
        "Navori Quickblades",
        "BF Sword",
        "Pickaxe",
        "Infinity Edge",
        "Ruby Crystal",
        "Jaurim's Fist",
        "Long Sword",
        "Ruby Crystal",
        "Jaurim's Fist",
        "Hullbreaker",
        "Vampiric Scepter",
        "Bloodthirster",
    ],
    # On-hit. Ignores the 7.3 crit buffs on purpose.
    "Kraken → Guinsoo → BotRK → Term → Wit": [
        "Long Sword",
        "Dagger",
        "Recurve Bow",
        "Hearthbound Axe",
        "Kraken Slayer",
        "Boots",
        "Berserker's Greaves",
        "Amplifying Tome",
        "Pickaxe",
        "Guinsoo's Rageblade",
        "Vampiric Scepter",
        "Blade of the Ruined King",
        "Terminus",
        "Negatron Cloak",
        "Wit's End",
    ],
    # Bruiser split: live the collapse, spellblade the turret
    "TF → Hull → DD → BotRK → GA": [
        "Long Sword",
        "Sheen",
        "Phage",
        "Hearthbound Axe",
        "Trinity Force",
        "Boots",
        "Berserker's Greaves",
        "Ruby Crystal",
        "Jaurim's Fist",
        "Long Sword",
        "Ruby Crystal",
        "Jaurim's Fist",
        "Hullbreaker",
        "Caulfield's Warhammer",
        "Chain Vest",
        "Pickaxe",
        "Death's Dance",
        "Vampiric Scepter",
        "Recurve Bow",
        "Blade of the Ruined King",
        "BF Sword",
        "Guardian Angel",
    ],
}


# ---------------------------------------------------------------------------
# Inventory
# ---------------------------------------------------------------------------


def resolve_inventory(path: List[str], gold: int) -> List[Item]:
    owned: List[str] = []
    pool = gold

    def missing_parts(name: str) -> List[str]:
        temp = owned[:]
        missing: List[str] = []
        for comp in UPGRADE_COMPONENTS.get(name, ()):
            if comp in temp:
                temp.remove(comp)
            else:
                missing.append(comp)
        return missing

    def afford_and_buy(name: str) -> bool:
        nonlocal pool
        if name in owned and name not in DUPLICATES:
            return False
        parts = UPGRADE_COMPONENTS.get(name, ())
        temp = owned[:]
        remove: List[str] = []
        credit = 0
        for comp in parts:
            if comp in temp:
                temp.remove(comp)
                remove.append(comp)
                credit += ITEMS[comp].cost
        pay = ITEMS[name].cost - credit
        if pay < 0 or pay > pool:
            return False
        pool -= pay
        for comp in remove:
            owned.remove(comp)
        owned.append(name)
        return True

    def buy_one_missing(name: str, depth: int = 0) -> bool:
        if depth > 5:
            return False
        missing = missing_parts(name)
        if not missing:
            return False
        part = missing[0]
        if afford_and_buy(part):
            return True
        return buy_one_missing(part, depth + 1)

    index = 0
    while index < len(path):
        step = path[index]
        if step in owned and step not in DUPLICATES:
            index += 1
            continue
        if afford_and_buy(step):
            index += 1
            continue
        if not buy_one_missing(step):
            break
    return [ITEMS[n] for n in owned]


# ---------------------------------------------------------------------------
# Champion + target state
# ---------------------------------------------------------------------------


def attack_speed(level: int, item_as: float, minute: int, extra: float) -> float:
    bonus = 0.10 + 0.025 * (level - 1) + item_as + alacrity(minute) + extra
    return min(3.0, 0.725 * (1.0 + bonus))


def q_ratio(level: int) -> float:
    rank = skill_rank(level, "Q")
    if rank <= 0:
        return 0.0
    return [0.0, 0.30, 0.50, 0.70, 0.90][rank]


def e_base(level: int) -> float:
    rank = skill_rank(level, "E")
    if rank <= 0:
        return 0.0
    return [0, 80, 130, 180, 230][rank]


def e_cd(level: int, haste: float) -> float:
    rank = skill_rank(level, "E")
    if rank <= 0:
        return 99.0
    base = [0, 11.0, 10.0, 9.0, 8.0][rank]
    return base * (100.0 / (100.0 + haste))


def phys_mult(armor: float, pct_pen: float, flat_pen: float) -> float:
    eff = max(0.0, armor * (1.0 - pct_pen) - flat_pen)
    return 100.0 / (100.0 + eff)


def magic_mult(mr: float) -> float:
    return 100.0 / (100.0 + max(0.0, mr))


@dataclass
class Foe:
    kind: str
    hp: float
    armor: float
    mr: float
    heal: float


def foes_at(minute: int, level: int) -> List[Foe]:
    """Who walks to the side lane to answer the split."""
    extra_hp = max(0, minute - 6)
    return [
        # Fighter who matches the split. Armor is steelcaps + a cloth item,
        # not a full tank. Heal is a vamp scepter / Conqueror, not a drain tank.
        Foe(
            "bruiser",
            hp=740 + 108 * level + 68 * extra_hp,
            armor=34 + 3.1 * level + min(60.0, 5.5 * max(0, minute - 9)),
            mr=32 + 1.5 * level + (16.0 if minute >= 14 else 0.0),
            heal=0.10,
        ),
        # Frontline sent when the fighter loses. Needs pen or %HP.
        Foe(
            "tank",
            hp=980 + 140 * level + 110 * max(0, minute - 5),
            armor=52 + 4.4 * level + min(165.0, 11.0 * max(0, minute - 7)),
            mr=36 + 2.1 * level + min(75.0, 5.5 * max(0, minute - 10)),
            heal=0.07,
        ),
        Foe(
            "squishy",
            hp=600 + 88 * level + 16 * minute,
            armor=26 + 2.3 * level + (12.0 if minute >= 16 else 0.0),
            mr=30 + 1.2 * level + (10.0 if minute >= 16 else 0.0),
            heal=0.04,
        ),
    ]


def effective_hp(hp: float, heal: float, grievous: bool) -> float:
    rate = heal * (0.5 if grievous else 1.0)
    return hp / max(0.55, 1.0 - rate)


def duel_value(dmg: float, ehp: float) -> float:
    """Killing the answer matters. Overkill barely does. A lost 1v1 is discounted."""
    if ehp <= 0:
        return 0.0
    ratio = dmg / ehp
    if ratio >= 1.0:
        return ehp * (1.0 + 0.12 * min(1.5, ratio - 1.0))
    return ehp * (ratio ** 1.35)


@dataclass
class Stats:
    names: List[str]
    ad: float
    bonus_ad: float
    ap: float
    hp: float
    ah: float
    as_pct: float
    crit: float
    armor: float
    mr: float
    lifesteal: float
    pct_apen: float
    base_ad: float
    yuntal: bool = False
    navori: bool = False
    ie: bool = False
    hull: bool = False
    botrk: bool = False
    kraken: bool = False
    guinsoo: bool = False
    storm: bool = False
    ldr: bool = False
    grievous: bool = False
    terminus: bool = False
    wit: bool = False
    spellblade: str = ""
    dd: bool = False
    ga: bool = False


def sum_stats(inv: List[Item], level: int, yuntal_crit: float) -> Stats:
    st = Stats(
        names=[it.name for it in inv],
        ad=0,
        bonus_ad=0,
        ap=0,
        hp=0,
        ah=0,
        as_pct=0,
        crit=0,
        armor=0,
        mr=0,
        lifesteal=0,
        pct_apen=0,
        base_ad=64 + 5 * (level - 1),
    )
    for it in inv:
        st.ad += it.ad
        st.ap += it.ap
        st.hp += it.hp
        st.ah += it.ah
        st.as_pct += it.as_pct
        st.crit += it.crit
        st.armor += it.armor
        st.mr += it.mr
        st.lifesteal += it.lifesteal
        st.pct_apen += it.pct_apen
        st.yuntal = st.yuntal or it.yuntal
        st.navori = st.navori or it.navori
        st.ie = st.ie or it.ie
        st.hull = st.hull or it.hull
        st.botrk = st.botrk or it.botrk
        st.kraken = st.kraken or it.kraken
        st.guinsoo = st.guinsoo or it.guinsoo
        st.storm = st.storm or it.storm
        st.ldr = st.ldr or it.ldr
        st.grievous = st.grievous or it.grievous
        st.terminus = st.terminus or it.terminus
        st.wit = st.wit or it.wit
        st.dd = st.dd or it.dd
        st.ga = st.ga or it.ga
        if it.spellblade == "trinity":
            st.spellblade = "trinity"
        elif it.spellblade == "er" and st.spellblade != "trinity":
            st.spellblade = "er"
        elif it.spellblade == "sheen" and not st.spellblade:
            st.spellblade = "sheen"
    st.crit += yuntal_crit
    st.bonus_ad = st.ad
    st.ad = st.base_ad + st.bonus_ad
    st.hp = 690 + 128 * (level - 1) + st.hp
    st.armor = 46 + 4.5 * (level - 1) + st.armor
    st.mr = 38 + 2 * (level - 1) + st.mr
    if st.terminus:
        st.armor += 12
        st.mr += 12
    return st


def crit_package(st: Stats, fury_crit: float) -> Tuple[float, float, float]:
    """Return (crit chance capped at 1, crit damage, overflow AD)."""
    total = st.crit + fury_crit
    chance = min(1.0, total)
    damage = 2.30 if st.ie else 2.00
    overflow = max(0.0, total - 1.0) * 100.0
    return chance, damage, overflow


def yuntal_crit_at(minute: int, bought_at: Optional[int]) -> float:
    if bought_at is None or minute < bought_at:
        return 0.0
    # ~16 attacks a minute on camps and waves, 0.4% crit each, cap 25%.
    attacks = 16.0 * (minute - bought_at + 0.4)
    return min(0.25, attacks * 0.004)


def first_minute(path: List[str], item_name: str) -> Optional[int]:
    for minute in range(1, GAME_MINUTES + 1):
        inv = resolve_inventory(path, gold_at_minute(minute))
        if any(it.name == item_name for it in inv):
            return minute
    return None


# ---------------------------------------------------------------------------
# Combat
# ---------------------------------------------------------------------------


def spellblade_bonus(st: Stats, crit_chance: float) -> float:
    if st.spellblade == "trinity":
        return 2.0 * st.base_ad
    if st.spellblade == "er":
        return 1.35 * st.base_ad + 80.0 * crit_chance
    if st.spellblade == "sheen":
        return 1.0 * st.base_ad
    return 0.0


def giant_slayer(st: Stats, foe_hp: float, level: int) -> float:
    if not st.ldr:
        return 1.0
    bonus_hp = max(0.0, foe_hp - (640 + 105 * (level - 1)))
    return 1.0 + min(0.12, 0.12 * bonus_hp / 1200.0)


def fight_duel(
    st: Stats, level: int, minute: int, foe: Foe
) -> Tuple[float, int, int]:
    """Damage dealt in the all-in. Returns (damage, autos, spins)."""
    r_rank = skill_rank(level, "R")
    if r_rank > 0:
        duration = R_WINDOW
        missing = 90.0  # R all-in, capped at 10% HP left
        fury_crit = 0.50  # R tops the bar
        last_stand = 1.11
    else:
        duration = EARLY_WINDOW
        missing = 35.0
        fury_crit = 0.30
        last_stand = 1.04

    crit_p, crit_d, overflow = crit_package(st, fury_crit)
    q_ad = q_ratio(level) * missing
    bonus_ad = st.bonus_ad + overflow + q_ad
    ad = st.base_ad + bonus_ad
    aa_mult = 1.0 + crit_p * (crit_d - 1.0)
    e_ratio_dmg = e_base(level) + 1.10 * bonus_ad
    e_base_cd = e_cd(level, st.ah)
    p_mult = phys_mult(foe.armor, st.pct_apen, 0.0)
    m_mult = magic_mult(foe.mr)
    slayer = giant_slayer(st, foe.hp, level)
    bullet = 9.0 + (30.0 - 9.0) * (level - 1) / 14.0
    kraken_hit = 150.0 + 60.0 * (level - 1) / 14.0

    t = 0.0
    dt = 0.05
    e_left = 0.0
    since_e = 10.0
    aa_left = 0.25
    spins = 0
    autos = 0
    lt = 0
    guinsoo_stacks = 0
    guinsoo_count = 0
    kraken_count = 0
    hull_count = 0
    blade_ready = False
    blade_cd = 0.0
    hp = foe.hp
    dealt = 0.0

    def extra_as() -> float:
        extra = 0.08 * lt
        extra += 0.08 * guinsoo_stacks
        if st.yuntal:
            extra += 0.35  # Flurry, first champion hit
        return extra

    while t < duration and hp > 0:
        aspd = attack_speed(level, st.as_pct, minute, extra_as())
        bonus_as = (
            0.10
            + 0.025 * (level - 1)
            + st.as_pct
            + alacrity(minute)
            + extra_as()
        )
        t += dt
        e_left -= dt
        since_e += dt
        aa_left -= dt
        blade_cd -= dt

        if e_left <= 0 and since_e >= 0.90 and skill_rank(level, "E") > 0:
            raw = e_ratio_dmg * last_stand * slayer * p_mult
            hp -= raw
            dealt += raw
            e_left = e_base_cd
            since_e = 0.0
            spins += 1
            blade_ready = True
            if hp <= 0:
                break

        if aa_left <= 0:
            aa_left += 1.0 / aspd
            autos += 1
            # Champion crit refunds 2s. Navori cuts whatever is left.
            e_left = max(0.0, e_left - 2.0 * crit_p)
            if st.navori:
                e_left *= 0.85
            if lt < 6:
                lt += 1
            phantom = False
            if st.guinsoo:
                if guinsoo_stacks < 4:
                    guinsoo_stacks += 1
                else:
                    guinsoo_count += 1
                    phantom = guinsoo_count % 3 == 0

            on_hit_phys = 0.0
            on_hit_magic = 0.0
            curr = max(0.0, hp)
            if st.botrk:
                on_hit_phys += max(15.0, 0.08 * curr)
            if st.wit:
                on_hit_magic += 40.0
            if st.guinsoo:
                on_hit_magic += 30.0
            if st.terminus:
                on_hit_magic += 30.0
            if phantom:
                on_hit_phys *= 2.0
                on_hit_magic *= 2.0

            kraken_count += 1
            kraken_bonus = 0.0
            if st.kraken and kraken_count % 3 == 0:
                missing_pct = 100.0 * (1.0 - curr / foe.hp)
                kraken_bonus = kraken_hit * (1.0 + min(0.75, 0.0075 * missing_pct))

            hull_count += 1
            hull_bonus = 0.0
            if st.hull and hull_count % 4 == 0:
                hull_bonus = 1.60 * st.base_ad + 0.05 * st.hp

            blade_bonus = 0.0
            if blade_ready and st.spellblade:
                blade_bonus = spellblade_bonus(st, crit_p)
                blade_ready = False
                blade_cd = 1.5

            brutal = 5.0 + 0.06 * bonus_ad + 0.03 * st.ap
            phys = (ad * aa_mult) + on_hit_phys + kraken_bonus + hull_bonus + blade_bonus + brutal
            if lt >= 6:
                phys += bullet * (1.0 + bonus_as)
            phys *= last_stand * slayer * p_mult
            magic = on_hit_magic * last_stand * slayer * m_mult
            hp -= phys + magic
            dealt += phys + magic

    if st.storm and dealt > 0:
        bolt = 120.0 * last_stand * m_mult
        dealt += bolt
    return dealt, autos, spins


def fight_tower(st: Stats, level: int, minute: int) -> float:
    """Turret damage for one crash. No crit. Melee turrets take +20%."""
    fury_crit = 0.35  # fury brought from the wave; tower hits do not crit
    crit_p, _, overflow = crit_package(st, fury_crit)
    ad = st.base_ad + st.bonus_ad + overflow
    window = 8.0 + (1.0 if st.hull else 0.0)
    # The crashed wave only lives a few seconds. After that, tower autos
    # do not crit minions, so Spinning Slash stops refunding and Spellblade
    # stops being primed every 1.5s.
    wave_alive = 3.2
    armor = 65.0
    p_mult = phys_mult(armor, st.pct_apen, 0.0) * 1.20
    e_base_cd = e_cd(level, st.ah)

    t = 0.0
    dt = 0.05
    e_left = 0.0
    since_e = 10.0
    aa_left = 0.2
    hull_count = 0
    blade_ready = True  # the spin that crashed the wave
    blade_cd = 0.0
    demolish_used = False
    dealt = 0.0
    guinsoo_stacks = 0

    while t < window:
        extra = 0.08 * guinsoo_stacks
        aspd = attack_speed(level, st.as_pct, minute, extra)
        t += dt
        e_left -= dt
        since_e += dt
        aa_left -= dt
        blade_cd -= dt

        if (
            t <= wave_alive
            and e_left <= 0
            and since_e >= 0.90
            and skill_rank(level, "E") > 0
        ):
            e_left = e_base_cd
            since_e = 0.0
            blade_ready = True

        if aa_left <= 0:
            aa_left += 1.0 / aspd
            if t <= wave_alive:
                e_left = max(0.0, e_left - 1.0 * crit_p)
                if st.navori:
                    e_left *= 0.85
            if st.guinsoo and guinsoo_stacks < 4:
                guinsoo_stacks += 1
            hull_count += 1
            bonus = 0.0
            if st.hull and hull_count % 4 == 0:
                bonus += 2.40 * st.base_ad + 0.09 * st.hp
            if blade_ready and st.spellblade and blade_cd <= 0:
                bonus += spellblade_bonus(st, crit_p)
                blade_ready = False
                blade_cd = 1.5
            if hull_count == 3 and not demolish_used:
                bonus += 85.0 + 0.28 * st.hp  # Demolish, split rune
                demolish_used = True
            dealt += (ad + bonus) * p_mult
    return dealt


def wave_clear_seconds(st: Stats, level: int, minute: int) -> float:
    fury_crit = 0.25
    crit_p, crit_d, overflow = crit_package(st, fury_crit)
    bonus_ad = st.bonus_ad + overflow
    ad = st.base_ad + bonus_ad
    aa_mult = 1.0 + crit_p * (crit_d - 1.0)
    e_dmg = e_base(level) + 1.10 * bonus_ad
    e_base_cd = e_cd(level, st.ah)
    melee_hp = 480 + 22 * minute
    caster_hp = 300 + 14 * minute
    minions = [melee_hp, melee_hp, melee_hp, caster_hp, caster_hp, caster_hp]
    if minute >= 10:
        minions.append(780 + 30 * minute)

    t = 0.0
    dt = 0.05
    e_left = 0.0
    since_e = 10.0
    aa_left = 0.15
    target = 0
    while t < 14.0 and any(hp > 0 for hp in minions):
        aspd = attack_speed(level, st.as_pct, minute, 0.0)
        t += dt
        e_left -= dt
        since_e += dt
        aa_left -= dt
        if e_left <= 0 and since_e >= 0.90 and skill_rank(level, "E") > 0:
            for i, hp in enumerate(minions):
                if hp > 0:
                    minions[i] = hp - e_dmg
            e_left = e_base_cd
            since_e = 0.0
        if aa_left <= 0:
            aa_left += 1.0 / aspd
            while target < len(minions) and minions[target] <= 0:
                target += 1
            if target >= len(minions):
                break
            hit = ad * aa_mult
            if st.botrk:
                hit += min(100.0, max(15.0, 0.08 * minions[target]))
            minions[target] -= hit
            e_left = max(0.0, e_left - 1.0 * crit_p)
            if st.navori:
                e_left *= 0.85
    return t


# ---------------------------------------------------------------------------
# Snapshots
# ---------------------------------------------------------------------------


@dataclass
class Snapshot:
    minute: int
    build_name: str
    items: List[str]
    gold: int
    level: int
    ad: float
    attack_speed: float
    crit: float
    hp: float
    dmg_bruiser: float
    dmg_tank: float
    dmg_squishy: float
    ehp_bruiser: float
    ehp_tank: float
    ehp_squishy: float
    duel_mix: float
    tower: float
    wave_sec: float
    spins: int
    split_power: float = 0.0
    notes: str = ""
    has_yuntal: bool = False
    has_ie: bool = False
    has_hull: bool = False
    has_botrk: bool = False
    has_navori: bool = False
    has_ldr: bool = False

    def kills(self, kind: str) -> bool:
        return {
            "bruiser": self.dmg_bruiser >= self.ehp_bruiser,
            "tank": self.dmg_tank >= self.ehp_tank,
            "squishy": self.dmg_squishy >= self.ehp_squishy,
        }[kind]


def compute_snapshot(
    build_name: str,
    path: List[str],
    minute: int,
    yuntal_at: Optional[int],
) -> Snapshot:
    level = level_at_minute(minute)
    gold = gold_at_minute(minute)
    inv = resolve_inventory(path, gold)
    stacks = yuntal_crit_at(minute, yuntal_at)
    st = sum_stats(inv, level, stacks)
    # Duel fury is full once R is up; show that crit in the snapshot.
    fury = 0.50 if skill_rank(level, "R") else 0.30
    crit_p, _, overflow = crit_package(st, fury)
    missing = 90.0 if skill_rank(level, "R") else 35.0
    duel_ad = st.base_ad + st.bonus_ad + overflow + q_ratio(level) * missing
    aspd = attack_speed(
        level,
        st.as_pct,
        minute,
        (0.35 if st.yuntal else 0.0) + (0.48 if skill_rank(level, "R") else 0.24),
    )

    duel_parts = []
    dmgs = {}
    ehps = {}
    spins = 0
    for foe in foes_at(minute, level):
        dmg, _autos, foe_spins = fight_duel(st, level, minute, foe)
        if foe.kind == "bruiser":
            spins = foe_spins
        ehp = effective_hp(foe.hp, foe.heal, st.grievous)
        dmgs[foe.kind] = dmg
        ehps[foe.kind] = ehp
        weight = {"bruiser": 0.45, "tank": 0.35, "squishy": 0.20}[foe.kind]
        duel_parts.append(weight * duel_value(dmg, ehp))
    duel_mix = sum(duel_parts)
    # Lifesteal lets him stay for the next wave instead of recalling. Small.
    duel_mix *= 1.0 + min(0.08, st.lifesteal * 0.45)
    tower = fight_tower(st, level, minute)
    wave_sec = wave_clear_seconds(st, level, minute)

    notes = []
    if st.yuntal:
        notes.append(f"Yun {stacks * 100:.0f}%")
    if st.ie:
        notes.append("IE 230%")
    if st.navori:
        notes.append(f"{spins} spins")
    if st.hull:
        notes.append("Hull")
    if st.botrk:
        notes.append("BotRK")
    if st.ldr:
        notes.append("LDR")
    if st.grievous and not st.ldr:
        notes.append("grievous")
    if st.spellblade:
        notes.append(st.spellblade)
    if skill_rank(level, "R") == 0:
        notes.append("no R")
    n_leg = sum(1 for n in st.names if n in LEGENDARIES and n != "Berserker's Greaves")
    if n_leg == 0:
        notes.append("components")

    return Snapshot(
        minute=minute,
        build_name=build_name,
        items=st.names,
        gold=gold,
        level=level,
        ad=round(duel_ad, 1),
        attack_speed=round(aspd, 2),
        crit=round(crit_p, 3),
        hp=round(st.hp, 1),
        dmg_bruiser=round(dmgs["bruiser"], 1),
        dmg_tank=round(dmgs["tank"], 1),
        dmg_squishy=round(dmgs["squishy"], 1),
        ehp_bruiser=round(ehps["bruiser"], 1),
        ehp_tank=round(ehps["tank"], 1),
        ehp_squishy=round(ehps["squishy"], 1),
        duel_mix=round(duel_mix, 1),
        tower=round(tower, 1),
        wave_sec=round(wave_sec, 2),
        spins=spins,
        notes=", ".join(notes) if notes else "-",
        has_yuntal=st.yuntal,
        has_ie=st.ie,
        has_hull=st.hull,
        has_botrk=st.botrk,
        has_navori=st.navori,
        has_ldr=st.ldr,
    )


def apply_split_scores(results: Dict[str, List[Snapshot]]) -> Tuple[float, float]:
    """Scale tower and wave so 50/35/15 is true at the minute-18 median."""
    mid = [snaps[17] for snaps in results.values()]
    med_d = median(s.duel_mix for s in mid)
    med_t = median(s.tower for s in mid) or 1.0
    med_w = median(8.0 / s.wave_sec for s in mid) or 1.0
    scale_t = med_d / med_t
    scale_w = med_d / med_w
    for snaps in results.values():
        for s in snaps:
            wave_score = 8.0 / max(0.5, s.wave_sec)
            s.split_power = round(
                DUEL_W * s.duel_mix
                + TOWER_W * s.tower * scale_t
                + WAVE_W * wave_score * scale_w,
                1,
            )
    return scale_t, scale_w


def run_all() -> Tuple[Dict[str, List[Snapshot]], List[dict], Tuple[float, float]]:
    yuntal_at = {
        name: first_minute(path, "Yun Tal Wildarrows")
        for name, path in BUILD_PATHS.items()
    }
    results: Dict[str, List[Snapshot]] = {}
    for name, path in BUILD_PATHS.items():
        results[name] = [
            compute_snapshot(name, path, minute, yuntal_at[name])
            for minute in range(1, GAME_MINUTES + 1)
        ]
    scales = apply_split_scores(results)

    timeline = []
    for minute in range(1, GAME_MINUTES + 1):
        best = max(results.values(), key=lambda snaps: snaps[minute - 1].split_power)
        snap = best[minute - 1]
        timeline.append(
            {
                "minute": minute,
                "winner": snap.build_name,
                "split_power": snap.split_power,
                "duel_mix": snap.duel_mix,
                "tower": snap.tower,
                "wave_sec": snap.wave_sec,
                "bruiser_pct": round(100.0 * snap.dmg_bruiser / snap.ehp_bruiser, 1),
                "tank_pct": round(100.0 * snap.dmg_tank / snap.ehp_tank, 1),
                "squishy_pct": round(100.0 * snap.dmg_squishy / snap.ehp_squishy, 1),
                "items": snap.items,
                "notes": snap.notes,
            }
        )
    return results, timeline, scales


def legendary_times(snaps: List[Snapshot]) -> List[Tuple[int, str]]:
    seen = set()
    out = []
    for snap in snaps:
        for name in snap.items:
            if name in LEGENDARIES and name not in seen:
                seen.add(name)
                out.append((snap.minute, name))
    return out


def pct(a: float, b: float) -> float:
    if b == 0:
        return 0.0
    return 100.0 * (a / b - 1.0)


def summarize(results, timeline, scales) -> str:
    scale_t, scale_w = scales
    lines: List[str] = []
    lines.append("=" * 88)
    lines.append("TRYNDAMERE JUNGLE — FARM, THEN SPLIT  (Wild Rift 7.3 / 7.3b, live 7.3f)")
    lines.append("Playstyle: full clear → side wave → R the answer → take the turret")
    lines.append(
        "Score: 50% duel (5s Undying Rage) + 35% turret + 15% wave crash"
    )
    lines.append(
        f"Scaled at the 18:00 median so those weights are real "
        f"(tower x{scale_t:.3f}, wave x{scale_w:.1f})"
    )
    lines.append("=" * 88)
    lines.append("")
    lines.append("GOLD / LEVEL  (powerfarm, not a gank curve)")
    lines.append(f"  {'Min':>3}  {'Gold':>6}  {'Lvl':>3}  {'Q':>2}  {'E':>2}  {'R':>2}")
    for minute in (1, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26):
        level = level_at_minute(minute)
        lines.append(
            f"  {minute:>3}  {gold_at_minute(minute):>6}  {level:>3}  "
            f"{skill_rank(level, 'Q'):>2}  {skill_rank(level, 'E'):>2}  "
            f"{skill_rank(level, 'R'):>2}"
        )

    lines.append("")
    lines.append("-" * 88)
    lines.append("MINUTE-BY-MINUTE BEST SPLIT SCORE")
    lines.append("-" * 88)
    for row in timeline:
        minute = row["minute"]
        if minute not in (4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26) and minute % 2:
            continue
        if minute < 4:
            continue
        kill_txt = (
            f"B{row['bruiser_pct']:.0f}/T{row['tank_pct']:.0f}/S{row['squishy_pct']:.0f}"
        )
        item_short = " › ".join(row["items"][:4])
        if len(row["items"]) > 4:
            item_short += " › …"
        lines.append(
            f"  {minute:>2}:00 | score {row['split_power']:>7.0f} | "
            f"duel {row['duel_mix']:>7.0f} | tower {row['tower']:>6.0f} | "
            f"wave {row['wave_sec']:>4.1f}s | {kill_txt:<16} | {row['winner']}"
        )
        lines.append(f"         {item_short}")
        lines.append(f"         {row['notes']}")

    lines.append("")
    lines.append("-" * 88)
    lines.append("BUILD COMPARISON — SPLIT SCORE")
    lines.append("-" * 88)
    lines.append(
        f"  {'Build':<42} {'8:00':>7} {'14:00':>7} {'18:00':>7} "
        f"{'22:00':>7} {'26:00':>7} {'Late':>7}"
    )
    ranking = []
    for name, snaps in results.items():
        def at(minute: int) -> Snapshot:
            return snaps[minute - 1]

        late = 0.0
        weight_sum = 0.0
        for snap in snaps:
            weight = 0.75 if snap.minute < 8 else (1.15 if snap.minute < 16 else 1.40)
            late += snap.split_power * weight
            weight_sum += weight
        late /= weight_sum
        ranking.append((late, name, snaps))
        lines.append(
            f"  {name:<42} {at(8).split_power:>7.0f} {at(14).split_power:>7.0f} "
            f"{at(18).split_power:>7.0f} {at(22).split_power:>7.0f} "
            f"{at(26).split_power:>7.0f} {late:>7.0f}"
        )
    ranking.sort(key=lambda row: row[0], reverse=True)

    def section(title: str, attr: str, minutes=(14, 18, 22, 26), digits=0) -> None:
        lines.append("")
        lines.append("-" * 88)
        lines.append(title)
        lines.append("-" * 88)
        fmt = f"{{:>7.{digits}f}}"
        for _late, name, snaps in ranking:
            vals = " ".join(fmt.format(getattr(snaps[m - 1], attr)) for m in minutes)
            lines.append(f"  {name:<42} {vals}")

    section("DUEL VALUE (kill credit vs bruiser 45% / tank 35% / squishy 20%)", "duel_mix")
    section("TURRET DAMAGE over one crash (melee +20%, Demolish, Hull window)", "tower")
    section("WAVE CLEAR seconds (lower is faster)", "wave_sec", digits=1)

    lines.append("")
    lines.append("-" * 88)
    lines.append("PERCENT OF THEIR EFFECTIVE HP REMOVED DURING R  (100 = they die)")
    lines.append("Order inside each cell: bruiser / tank / squishy")
    lines.append("-" * 88)
    lines.append(
        f"  {'Build':<42} {'18:00':>14} {'22:00':>14} {'26:00':>14}"
    )
    for _late, name, snaps in ranking:
        cells = []
        for minute in (18, 22, 26):
            snap = snaps[minute - 1]
            cells.append(
                f"{100 * snap.dmg_bruiser / snap.ehp_bruiser:3.0f}/"
                f"{100 * snap.dmg_tank / snap.ehp_tank:3.0f}/"
                f"{100 * snap.dmg_squishy / snap.ehp_squishy:3.0f}"
            )
        lines.append(f"  {name:<42} {cells[0]:>14} {cells[1]:>14} {cells[2]:>14}")

    winner_late, winner_name, winner = ranking[0]
    sheet_name = "Yun → Navori → IE → BotRK → Mortal"
    onhit_name = "Kraken → Guinsoo → BotRK → Term → Wit"
    bruiser_name = "TF → Hull → DD → BotRK → GA"
    sheet = results[sheet_name]
    onhit = results[onhit_name]
    bruiser = results[bruiser_name]

    lines.append("")
    lines.append("-" * 88)
    lines.append("VERDICT")
    lines.append("-" * 88)
    lines.append(f"  Best farm → split path: {winner_name}")
    lines.append(f"  Late-weighted split score: {winner_late:.0f}")
    lines.append("  Item spikes:")
    for minute, item in legendary_times(winner):
        if item == "Berserker's Greaves":
            lines.append(f"    ~{minute:>2}:00  Berserker's Greaves")
        else:
            lines.append(f"    ~{minute:>2}:00  {item}")

    w22 = winner[21]
    lines.append("")
    lines.append("  At 22:00 (four-item region of a farm game):")
    lines.append(
        f"    Duel {w22.duel_mix:.0f} | tower {w22.tower:.0f} | "
        f"wave {w22.wave_sec:.1f}s | crit {w22.crit:.0%} | {w22.spins} spins"
    )
    lines.append(
        f"    Bruiser {w22.dmg_bruiser:.0f} / {w22.ehp_bruiser:.0f} EHP "
        f"({'kill' if w22.kills('bruiser') else 'lives'})"
    )
    lines.append(
        f"    Tank    {w22.dmg_tank:.0f} / {w22.ehp_tank:.0f} EHP "
        f"({'kill' if w22.kills('tank') else 'lives'})"
    )
    lines.append(
        f"    Squishy {w22.dmg_squishy:.0f} / {w22.ehp_squishy:.0f} EHP "
        f"({'kill' if w22.kills('squishy') else 'lives'})"
    )
    lines.append("")
    lines.append(f"  vs sheet crit ({sheet_name}):")
    lines.append(
        f"    22:00 score {w22.split_power:.0f} vs {sheet[21].split_power:.0f} "
        f"({pct(w22.split_power, sheet[21].split_power):+.0f}%) | "
        f"tower {w22.tower:.0f} vs {sheet[21].tower:.0f}"
    )
    lines.append(f"  vs on-hit ({onhit_name}):")
    lines.append(
        f"    22:00 score {w22.split_power:.0f} vs {onhit[21].split_power:.0f} "
        f"({pct(w22.split_power, onhit[21].split_power):+.0f}%) | "
        f"duel {w22.duel_mix:.0f} vs {onhit[21].duel_mix:.0f}"
    )
    lines.append(f"  vs bruiser ({bruiser_name}):")
    lines.append(
        f"    22:00 score {w22.split_power:.0f} vs {bruiser[21].split_power:.0f} "
        f"({pct(w22.split_power, bruiser[21].split_power):+.0f}%) | "
        f"tower {w22.tower:.0f} vs {bruiser[21].tower:.0f}"
    )
    runner_late, runner_name, runner = ranking[1]
    lines.append("")
    lines.append(
        f"  Runner-up ({runner_name}) late score {runner_late:.0f} "
        f"vs {winner_late:.0f}."
    )
    lines.append(
        f"    22:00 duel {runner[21].duel_mix:.0f} vs {w22.duel_mix:.0f}, "
        f"tower {runner[21].tower:.0f} vs {w22.tower:.0f}."
    )
    if onhit[21].duel_mix > w22.duel_mix and w22.tower > onhit[21].tower:
        lines.append(
            "  On-hit wins the bare 1v1 and still loses the split: "
            "the turret gap is larger than the duel gap, and the wave is slower."
        )
    lines.append(
        "  100% of their EHP means they die inside R. The high 90s means"
    )
    lines.append(
        "  they live if a summoner spell or a minion hits them. Mortal Reminder"
    )
    lines.append(
        "  is the swap when that answer heals — Grievous is what flips the kill,"
    )
    lines.append("  Lord Dominik's is what flips the tank.")
    lines.append("")
    lines.append("  WHY THIS PLAYSTYLE ITEMIZES THIS WAY")
    lines.append("  • 7.3b: every Fury point is 0.5% crit from level 1. Full bar")
    lines.append("    is 50% crit before items. R fills the bar. Overflow crit")
    lines.append("    becomes 1 AD per 1% — IE's old Limit Break is gone, this is")
    lines.append("    the champion passive, so a third crit item still pays.")
    lines.append("  • Base crits are 200%. Infinity Edge makes them 230%. Trynd")
    lines.append("    was buffed because he was not getting enough from that.")
    lines.append("  • Spinning Slash crit-refunds on monsters (7.3) and on the")
    lines.append("    champion (2s). Navori then cuts 15% of the remaining CD per")
    lines.append("    auto, so the all-in is several spins, not one.")
    lines.append("  • Q max, not E max. The refund already dumps E's cooldown.")
    lines.append("    Bloodlust at rank 4 is +0.9 AD per 1% missing HP (+81 AD at")
    lines.append("    the R threshold) and that AD crits and scales the spin.")
    lines.append("  • Hullbreaker Skipper is 240% base AD + 9% max HP on turrets")
    lines.append("    every 4th auto, and 7.3 turrets take 20% more from melee.")
    lines.append("    BotRK does not hit structures. The duel item and the tower")
    lines.append("    item are different slots.")
    lines.append("  • Yun Tal is the farm item: 0 AD-crit until you auto, 0.4%")
    lines.append("    per hit, cap 25%. A jungler who only farms caps it. Flurry")
    lines.append("    is +35% AS once the duel starts. It does nothing to turrets.")
    lines.append("  • Demolish over Nimbus. Ghost still gets you to the wave;")
    lines.append("    Demolish is the plate. 85 + 28% max HP after 3 autos.")
    lines.append("")
    lines.append("  MACRO")
    lines.append("  • Full clear to level 5. E refunds on camp crits — that is")
    lines.append("    the 7.3 farm buff. First back finishes item 1. Do not gank")
    lines.append("    for a component.")
    lines.append("  • Then catch the side wave on the half of the map your")
    lines.append("    team is not fighting. Crash it, R whoever matches,")
    lines.append("    auto the turret, leave when the second champion shows.")
    lines.append("  • Press R before the CC, not at 1 HP. Q when R ends, not")
    lines.append("    during it — spending Fury drops the crit you are hitting with.")
    lines.append("  • You do not win the 1v2. Two answers = spin over the wall.")
    lines.append("=" * 88)
    return "\n".join(lines)


def export_json(results, timeline, scales, path: Path) -> None:
    scale_t, scale_w = scales
    payload = {
        "meta": {
            "champion": "Tryndamere",
            "role": "Jungle",
            "patch": "7.3/7.3b (live 7.3f)",
            "game_minutes": GAME_MINUTES,
            "playstyle": "full clear, side-lane split",
            "metric": "50% R-window duel + 35% turret + 15% wave",
            "scale_tower": round(scale_t, 4),
            "scale_wave": round(scale_w, 4),
            "question": "best farm-and-split build: win the 1v1 and take the tower",
        },
        "timeline": timeline,
        "builds": {
            name: [
                {
                    "minute": s.minute,
                    "items": s.items,
                    "gold": s.gold,
                    "level": s.level,
                    "ad": s.ad,
                    "attack_speed": s.attack_speed,
                    "crit": s.crit,
                    "hp": s.hp,
                    "dmg_bruiser": s.dmg_bruiser,
                    "dmg_tank": s.dmg_tank,
                    "dmg_squishy": s.dmg_squishy,
                    "ehp_bruiser": s.ehp_bruiser,
                    "ehp_tank": s.ehp_tank,
                    "ehp_squishy": s.ehp_squishy,
                    "duel_mix": s.duel_mix,
                    "tower": s.tower,
                    "wave_sec": s.wave_sec,
                    "spins": s.spins,
                    "split_power": s.split_power,
                    "notes": s.notes,
                }
                for s in snaps
            ]
            for name, snaps in results.items()
        },
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def self_check(results: Dict[str, List[Snapshot]]) -> None:
    sheet = results["Yun → Navori → IE → BotRK → Mortal"]
    hull = results["Yun → Hull → IE → Navori → LDR"]
    assert any(s.has_yuntal for s in sheet if s.minute <= 10), "Yun Tal should be online by 10:00"
    assert hull[25].tower > sheet[25].tower, (hull[25].tower, sheet[25].tower)
    assert sheet[25].has_ie and sheet[25].crit >= 0.99
    assert sheet[21].spins >= 2
    assert sheet[21].spins <= 8
    scores = [snaps[21].split_power for snaps in results.values()]
    assert max(scores) > min(scores) * 1.05
    for snaps in results.values():
        assert snaps[25].duel_mix > 0
        assert snaps[25].tower > 0
        assert 1.0 <= snaps[25].wave_sec <= 14.0
    # Farm curve reaches the documented 6-slot sheet cost near the end.
    assert gold_at_minute(8) >= 3000
    assert gold_at_minute(26) >= 16000


def main() -> None:
    results, timeline, scales = run_all()
    self_check(results)
    report = summarize(results, timeline, scales)
    print(report)
    out_dir = Path(__file__).resolve().parent
    (out_dir / "report.txt").write_text(report + "\n", encoding="utf-8")
    export_json(results, timeline, scales, out_dir / "results.json")
    print(f"\nWrote {out_dir / 'report.txt'} and {out_dir / 'results.json'}")


if __name__ == "__main__":
    main()
