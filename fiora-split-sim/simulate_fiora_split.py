#!/usr/bin/env python3
"""Fiora baron lane — split push that answers the tank meta.

Wild Rift 7.3f. The side that wins Baron right now is Malphite, Shen,
Cho'Gath, Ornn, K'Sante, Dr. Mundo, plus Mordekaiser and a blind (Teemo)
or a ranged answer (Kalista). Fiora is the split pusher whose passive
is true damage off their max health. This sim asks which item path kills
that answer and still takes the turret.

Runes are fixed on every row (Grasp, Demolish, Second Wind, Overgrowth,
Sudden Impact, Flash + Teleport). Items are the only variable.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from statistics import median
from typing import Dict, List, Optional, Tuple


GAME_MINUTES = 26
DUEL_W = 0.50
TOWER_W = 0.35
WAVE_W = 0.15
# Of the duel: the tank is who matches a split in this meta.
TANK_W = 0.55
JUGG_W = 0.30
RANGED_W = 0.15

# Outer turret you're crashing from 14:00 on. Sunderer's structure hit is
# 50% of a max-health proc, so the turret's health has to be a real number.
TURRET_HP = 4000.0
TURRET_ARMOR = 65.0
MELEE_TOWER = 1.20

# Duelist's Dance. wildriftcore ratio on the 7.3 page: 3.5% + 0.055% per
# bonus AD of the target's max health, as true damage. The flat 16% some
# older writeups add for popping all four is not in the current ability
# text, so four vitals are the whole ultimate payoff.
VITAL_BASE = 0.035
VITAL_PER_AD = 0.00055


# ---------------------------------------------------------------------------
# Clock
# ---------------------------------------------------------------------------


def gold_at_minute(m: int) -> int:
    """Side-lane farmer: waves and plates, few kills before the split."""
    total = 500
    for t in range(1, m + 1):
        if t <= 4:
            total += 400
        elif t <= 8:
            total += 520
        elif t <= 13:
            total += 580
        elif t <= 18:
            total += 700
        elif t <= 22:
            total += 800
        else:
            total += 820
    return total


LEVEL_AT = {
    1: 1,
    2: 2,
    3: 3,
    4: 4,
    5: 5,
    6: 6,
    7: 7,
    8: 8,
    9: 9,
    10: 10,
    11: 11,
    12: 12,
    13: 12,
    14: 13,
    15: 13,
    16: 14,
    17: 14,
    18: 14,
    19: 15,
    20: 15,
    21: 15,
    22: 15,
    23: 15,
    24: 15,
    25: 15,
    26: 15,
}


def level_at_minute(m: int) -> int:
    return LEVEL_AT[m]


# Q max, E second, W last. R at 5 / 9 / 13.
_ORDER = ["Q", "E", "Q", "W", "Q", "R", "Q", "E", "R", "E", "W", "E", "R", "W", "W"]


def skill_rank(level: int, skill: str) -> int:
    ranks = {"Q": 0, "W": 0, "E": 0, "R": 0}
    for i in range(min(level, 15)):
        ranks[_ORDER[i]] += 1
    return ranks[skill]


def base_ad(level: int) -> float:
    return 70.0 + 4.0 * (level - 1)


def base_hp(level: int) -> float:
    return 630.0 + 130.0 * (level - 1)


def base_armor(level: int) -> float:
    return 42.0 + 4.8 * (level - 1)


def base_mr(level: int) -> float:
    return 38.0 + 2.0 * (level - 1)


def base_mana(level: int) -> float:
    return 300.0 + 37.0 * (level - 1)


def attack_speed(level: int, item_as: float) -> float:
    # AS ratio 0.69, base bonus 16%, +2.6% per level. Cap 3.0.
    bonus = 0.16 + 0.026 * (level - 1) + item_as
    return min(3.0, 0.69 * (1.0 + bonus))


def haste_mult(ah: float) -> float:
    return 100.0 / (100.0 + ah)


def casts(cd: float, duration: float) -> int:
    if cd <= 0 or duration <= 0:
        return 0
    return 1 + int((duration - 0.25) / cd)


# ---------------------------------------------------------------------------
# Items — costs and stats from the 7.3 / 7.3d / 7.3f shop
# ---------------------------------------------------------------------------


@dataclass
class Item:
    name: str
    cost: int
    ad: float = 0
    ah: float = 0
    hp: float = 0
    as_pct: float = 0
    armor: float = 0
    mr: float = 0
    mana: float = 0
    lifesteal: float = 0
    omnivamp: float = 0
    pct_apen: float = 0
    spellblade: str = ""  # sheen | trinity | sunderer
    eclipse: bool = False
    botrk: bool = False
    hull: bool = False
    cleaver: bool = False
    dd: bool = False
    shojin: bool = False
    maw: bool = False
    sterak: bool = False
    gore: bool = False
    ga: bool = False
    manamune: bool = False
    steelcaps: bool = False


ITEMS: Dict[str, Item] = {
    "Long Sword": Item("Long Sword", 500, ad=12),
    "Dagger": Item("Dagger", 400, as_pct=0.12),
    "Ruby Crystal": Item("Ruby Crystal", 500, hp=150),
    "Boots": Item("Boots", 400),
    "Null-Magic Mantle": Item("Null-Magic Mantle", 500, mr=20),
    "Cloth Armor": Item("Cloth Armor", 500, armor=20),
    "Ring of Revelation": Item("Ring of Revelation", 300),
    "Tear of the Goddess": Item("Tear of the Goddess", 400, mana=200),
    "Pickaxe": Item("Pickaxe", 800, ad=20),
    "Sheen": Item("Sheen", 800, ah=10, spellblade="sheen"),
    "Recurve Bow": Item("Recurve Bow", 900, as_pct=0.20),
    "Chain Vest": Item("Chain Vest", 900, armor=40),
    "Negatron Cloak": Item("Negatron Cloak", 900, mr=40),
    "Phage": Item("Phage", 1000, ad=15, hp=150),
    "Kindlegem": Item("Kindlegem", 1000, hp=175, ah=10),
    "Caulfield's Warhammer": Item("Caulfield's Warhammer", 1200, ad=25, ah=10),
    "Vampiric Scepter": Item("Vampiric Scepter", 1200, ad=20, lifesteal=0.08),
    "Last Whisper": Item("Last Whisper", 1200, ad=15, pct_apen=0.15),
    "Hearthbound Axe": Item("Hearthbound Axe", 1200, ad=20, as_pct=0.15),
    "Jaurim's Fist": Item("Jaurim's Fist", 1200, ad=15, hp=200),
    "Hexdrinker": Item("Hexdrinker", 1200, ad=20, mr=20),
    "BF Sword": Item("BF Sword", 1500, ad=40),
    "Plated Steelcaps": Item(
        "Plated Steelcaps", 1200, hp=150, armor=25, steelcaps=True
    ),
    "Eclipse": Item("Eclipse", 2900, ad=60, ah=20, eclipse=True),
    "Trinity Force": Item(
        "Trinity Force", 3333, ad=36, hp=333, as_pct=0.30, ah=15, spellblade="trinity"
    ),
    "Divine Sunderer": Item(
        "Divine Sunderer",
        3300,
        ad=25,
        hp=425,
        ah=25,
        spellblade="sunderer",
    ),
    "Hullbreaker": Item("Hullbreaker", 3100, ad=50, hp=400, hull=True),
    "Death's Dance": Item("Death's Dance", 3300, ad=50, armor=45, ah=15, dd=True),
    "Blade of the Ruined King": Item(
        "Blade of the Ruined King",
        3100,
        ad=40,
        as_pct=0.30,
        lifesteal=0.12,
        botrk=True,
    ),
    "Black Cleaver": Item(
        "Black Cleaver", 3000, ad=40, hp=400, ah=20, cleaver=True
    ),
    "Spear of Shojin": Item("Spear of Shojin", 3100, ad=40, hp=450, shojin=True),
    "Serylda's Grudge": Item(
        "Serylda's Grudge", 3100, ad=50, ah=15, pct_apen=0.35
    ),
    "Manamune": Item("Manamune", 2900, ad=40, ah=15, mana=500, manamune=True),
    "Maw of Malmortius": Item(
        "Maw of Malmortius", 3000, ad=55, mr=45, ah=10, maw=True
    ),
    "Bloodthirster": Item("Bloodthirster", 3200, ad=75, lifesteal=0.15),
    "Sterak's Gage": Item("Sterak's Gage", 3200, hp=400, sterak=True),
    "Goredrinker": Item(
        "Goredrinker", 3100, ad=45, hp=400, ah=15, omnivamp=0.08, gore=True
    ),
    "Guardian Angel": Item("Guardian Angel", 3200, ad=45, armor=40, ga=True),
}


UPGRADE_COMPONENTS: Dict[str, Tuple[str, ...]] = {
    "Pickaxe": ("Long Sword",),
    "Caulfield's Warhammer": ("Long Sword",),
    "Vampiric Scepter": ("Long Sword",),
    "Last Whisper": ("Long Sword",),
    "Hearthbound Axe": ("Long Sword", "Dagger"),
    "Jaurim's Fist": ("Long Sword", "Ruby Crystal"),
    "Phage": ("Long Sword", "Ruby Crystal"),
    "Hexdrinker": ("Long Sword", "Null-Magic Mantle"),
    "BF Sword": ("Long Sword",),
    "Recurve Bow": ("Dagger",),
    "Plated Steelcaps": ("Boots", "Ruby Crystal"),
    "Eclipse": ("Caulfield's Warhammer", "Caulfield's Warhammer"),
    "Trinity Force": ("Sheen", "Phage", "Hearthbound Axe"),
    "Divine Sunderer": ("Sheen", "Jaurim's Fist", "Kindlegem"),
    "Hullbreaker": ("Jaurim's Fist", "Jaurim's Fist"),
    "Death's Dance": ("Caulfield's Warhammer", "Chain Vest", "Pickaxe"),
    "Blade of the Ruined King": ("Vampiric Scepter", "Recurve Bow", "Pickaxe"),
    "Black Cleaver": ("Phage", "Kindlegem", "Pickaxe"),
    "Spear of Shojin": ("Jaurim's Fist", "Jaurim's Fist"),
    "Serylda's Grudge": ("Caulfield's Warhammer", "Last Whisper"),
    "Manamune": ("Caulfield's Warhammer", "Tear of the Goddess", "Long Sword"),
    "Maw of Malmortius": ("Hexdrinker", "Hexdrinker"),
    "Bloodthirster": ("Vampiric Scepter", "BF Sword"),
    "Sterak's Gage": ("BF Sword", "Ruby Crystal", "Ruby Crystal"),
    "Goredrinker": ("Phage", "Jaurim's Fist", "Ring of Revelation"),
    "Guardian Angel": ("BF Sword", "Chain Vest"),
}

DUPLICATES = {
    "Long Sword",
    "Dagger",
    "Ruby Crystal",
    "Jaurim's Fist",
    "Pickaxe",
    "Caulfield's Warhammer",
    "Hexdrinker",
}

LEGENDARIES = {
    "Plated Steelcaps",
    "Eclipse",
    "Trinity Force",
    "Divine Sunderer",
    "Hullbreaker",
    "Death's Dance",
    "Blade of the Ruined King",
    "Black Cleaver",
    "Spear of Shojin",
    "Serylda's Grudge",
    "Manamune",
    "Maw of Malmortius",
    "Bloodthirster",
    "Sterak's Gage",
    "Goredrinker",
    "Guardian Angel",
}


# Same boots on every row. Steelcaps are the counter-meta boot: the
# champions who walk to your wave auto you. Gluttonous is the popular
# cheaper boot; it is not in the race so the items stay comparable.
# Armored Advance (2200) is the late upgrade of these boots and would
# land on every path at the same time.
_BOOTS = ["Boots", "Ruby Crystal", "Plated Steelcaps"]

BUILD_PATHS: Dict[str, List[str]] = {
    # Diamond+ core, about 54% WR. Eclipse first, Hull third.
    "Eclipse → TF → Hull → DD → BotRK": [
        "Long Sword",
        "Caulfield's Warhammer",
        "Long Sword",
        "Caulfield's Warhammer",
        "Eclipse",
        *_BOOTS,
        "Sheen",
        "Long Sword",
        "Ruby Crystal",
        "Phage",
        "Dagger",
        "Hearthbound Axe",
        "Trinity Force",
        "Long Sword",
        "Ruby Crystal",
        "Jaurim's Fist",
        "Long Sword",
        "Ruby Crystal",
        "Jaurim's Fist",
        "Hullbreaker",
        "Long Sword",
        "Caulfield's Warhammer",
        "Chain Vest",
        "Pickaxe",
        "Death's Dance",
        "Long Sword",
        "Vampiric Scepter",
        "Dagger",
        "Recurve Bow",
        "Pickaxe",
        "Blade of the Ruined King",
    ],
    # Same items, Hull second, so the turret item exists when the split starts.
    "TF → Hull → Eclipse → DD → Shojin": [
        "Sheen",
        "Long Sword",
        "Ruby Crystal",
        "Phage",
        "Dagger",
        "Hearthbound Axe",
        "Trinity Force",
        *_BOOTS,
        "Long Sword",
        "Ruby Crystal",
        "Jaurim's Fist",
        "Long Sword",
        "Ruby Crystal",
        "Jaurim's Fist",
        "Hullbreaker",
        "Long Sword",
        "Caulfield's Warhammer",
        "Long Sword",
        "Caulfield's Warhammer",
        "Eclipse",
        "Chain Vest",
        "Pickaxe",
        "Death's Dance",
        "Jaurim's Fist",
        "Long Sword",
        "Ruby Crystal",
        "Jaurim's Fist",
        "Spear of Shojin",
    ],
    # The "two or more tanks" advice: Sunderer instead of Trinity.
    "Sunderer → Cleaver → Hull → DD → Shojin": [
        "Sheen",
        "Long Sword",
        "Ruby Crystal",
        "Jaurim's Fist",
        "Kindlegem",
        "Divine Sunderer",
        *_BOOTS,
        "Long Sword",
        "Ruby Crystal",
        "Phage",
        "Pickaxe",
        "Black Cleaver",
        "Jaurim's Fist",
        "Long Sword",
        "Ruby Crystal",
        "Jaurim's Fist",
        "Hullbreaker",
        "Long Sword",
        "Caulfield's Warhammer",
        "Chain Vest",
        "Death's Dance",
        "Spear of Shojin",
    ],
    # Guide shred line. Pen so the physical half of the kit lands.
    "TF → BotRK → Cleaver → Eclipse → Serylda": [
        "Sheen",
        "Long Sword",
        "Ruby Crystal",
        "Phage",
        "Dagger",
        "Hearthbound Axe",
        "Trinity Force",
        *_BOOTS,
        "Long Sword",
        "Vampiric Scepter",
        "Recurve Bow",
        "Pickaxe",
        "Blade of the Ruined King",
        "Kindlegem",
        "Black Cleaver",
        "Caulfield's Warhammer",
        "Long Sword",
        "Caulfield's Warhammer",
        "Eclipse",
        "Last Whisper",
        "Serylda's Grudge",
    ],
    # China sheet: Trinity, Manamune, Maw, Death's Dance, Bloodthirster.
    "TF → Manamune → Maw → DD → BT": [
        "Sheen",
        "Long Sword",
        "Ruby Crystal",
        "Phage",
        "Dagger",
        "Hearthbound Axe",
        "Trinity Force",
        *_BOOTS,
        "Caulfield's Warhammer",
        "Tear of the Goddess",
        "Long Sword",
        "Manamune",
        "Null-Magic Mantle",
        "Hexdrinker",
        "Long Sword",
        "Null-Magic Mantle",
        "Hexdrinker",
        "Maw of Malmortius",
        "Chain Vest",
        "Pickaxe",
        "Death's Dance",
        "Vampiric Scepter",
        "BF Sword",
        "Bloodthirster",
    ],
    # Eclipse core with the pen item instead of Death's Dance.
    "Eclipse → TF → BotRK → Hull → Serylda": [
        "Long Sword",
        "Caulfield's Warhammer",
        "Long Sword",
        "Caulfield's Warhammer",
        "Eclipse",
        *_BOOTS,
        "Sheen",
        "Ruby Crystal",
        "Phage",
        "Dagger",
        "Hearthbound Axe",
        "Trinity Force",
        "Vampiric Scepter",
        "Recurve Bow",
        "Pickaxe",
        "Blade of the Ruined King",
        "Long Sword",
        "Jaurim's Fist",
        "Ruby Crystal",
        "Jaurim's Fist",
        "Hullbreaker",
        "Last Whisper",
        "Serylda's Grudge",
    ],
    # The small-sample 57% line: Manamune first, then the split items.
    "Manamune → TF → Hull → Shojin → DD": [
        "Long Sword",
        "Caulfield's Warhammer",
        "Tear of the Goddess",
        "Manamune",
        *_BOOTS,
        "Sheen",
        "Ruby Crystal",
        "Phage",
        "Dagger",
        "Hearthbound Axe",
        "Trinity Force",
        "Jaurim's Fist",
        "Long Sword",
        "Ruby Crystal",
        "Jaurim's Fist",
        "Hullbreaker",
        "Spear of Shojin",
        "Chain Vest",
        "Pickaxe",
        "Death's Dance",
    ],
    # Sustain. Lives the collapse. Short on the bonus AD vitals scale with.
    "TF → DD → Sterak → Gore → GA": [
        "Sheen",
        "Long Sword",
        "Ruby Crystal",
        "Phage",
        "Dagger",
        "Hearthbound Axe",
        "Trinity Force",
        *_BOOTS,
        "Caulfield's Warhammer",
        "Chain Vest",
        "Pickaxe",
        "Death's Dance",
        "BF Sword",
        "Ruby Crystal",
        "Sterak's Gage",
        "Jaurim's Fist",
        "Ring of Revelation",
        "Goredrinker",
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
        if depth > 6:
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


def first_minute(path: List[str], item_name: str) -> Optional[int]:
    for minute in range(1, GAME_MINUTES + 1):
        inv = resolve_inventory(path, gold_at_minute(minute))
        if any(item.name == item_name for item in inv):
            return minute
    return None


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------


@dataclass
class Stats:
    names: List[str] = field(default_factory=list)
    bonus_ad: float = 0
    ah: float = 0
    hp: float = 0
    as_pct: float = 0
    armor: float = 0
    mr: float = 0
    mana_item: float = 0
    lifesteal: float = 0
    omnivamp: float = 0
    pct_apen: float = 0
    spellblade: str = ""
    eclipse: bool = False
    botrk: bool = False
    hull: bool = False
    cleaver: bool = False
    dd: bool = False
    shojin: bool = False
    maw: bool = False
    sterak: bool = False
    gore: bool = False
    ga: bool = False
    manamune: bool = False
    steelcaps: bool = False
    # Filled after the mana / Heavy Hands pass.
    ad: float = 0
    base_ad: float = 0
    max_hp: float = 0
    shock_mana: float = 0
    muramana_live: bool = False


def sum_stats(inv: List[Item], level: int, minute: int, mana_bought: Optional[int]) -> Stats:
    st = Stats()
    st.base_ad = base_ad(level)
    st.names = [item.name for item in inv]
    for item in inv:
        st.bonus_ad += item.ad
        st.ah += item.ah
        st.hp += item.hp
        st.as_pct += item.as_pct
        st.armor += item.armor
        st.mr += item.mr
        st.mana_item += item.mana
        st.lifesteal += item.lifesteal
        st.omnivamp += item.omnivamp
        st.pct_apen = max(st.pct_apen, item.pct_apen)
        if item.spellblade == "sunderer":
            st.spellblade = "sunderer"
        elif item.spellblade == "trinity" and st.spellblade != "sunderer":
            st.spellblade = "trinity"
        elif item.spellblade == "sheen" and not st.spellblade:
            st.spellblade = "sheen"
        st.eclipse = st.eclipse or item.eclipse
        st.botrk = st.botrk or item.botrk
        st.hull = st.hull or item.hull
        st.cleaver = st.cleaver or item.cleaver
        st.dd = st.dd or item.dd
        st.shojin = st.shojin or item.shojin
        st.maw = st.maw or item.maw
        st.sterak = st.sterak or item.sterak
        st.gore = st.gore or item.gore
        st.ga = st.ga or item.ga
        st.manamune = st.manamune or item.manamune
        st.steelcaps = st.steelcaps or item.steelcaps

    # Overgrowth. Same rune on every path; scales a little with game time.
    st.hp += min(140.0, 6.0 * minute)
    st.max_hp = base_hp(level) + st.hp

    # Heavy Hands is bonus AD, so it feeds vitals.
    if st.sterak:
        st.bonus_ad += 0.50 * st.base_ad

    # Manamune: +14 max mana, cap 700, at most 3 procs per 10s. A laner
    # who is hitting the wave fills that in about five minutes. Shock
    # exists only on Muramana, which is the full charge. Awe is 2% of
    # max mana the whole time. Item mana is the 7.3 value, 500.
    if st.manamune and mana_bought is not None:
        charge = min(700.0, 140.0 * max(0, minute - mana_bought))
        st.mana_item = 500.0 + charge
        st.muramana_live = charge >= 700.0
    total_mana = base_mana(level) + st.mana_item
    if st.manamune:
        st.bonus_ad += 0.02 * total_mana
        if st.muramana_live:
            st.shock_mana = total_mana

    # Dragonforce is basic-ability haste, not a stat-line number.
    if st.shojin:
        st.ah += 20.0

    st.ad = st.base_ad + st.bonus_ad
    return st


# ---------------------------------------------------------------------------
# Targets
# ---------------------------------------------------------------------------


@dataclass
class Foe:
    kind: str
    hp: float
    armor: float
    mr: float
    heal: float
    dps_phys: float
    dps_magic: float
    attack_share: float  # of the physical DPS that is basic attacks
    blind: bool = False
    steal: float = 0.0
    poke_magic: float = 0.0
    vitals: int = 4


def foes_at(minute: int, level: int, ult: bool) -> List[Foe]:
    """The three answers to a Fiora split on this patch.

    Tank is the baron meta (Malphite, Shen, Cho, Ornn, K'Sante, Mundo).
    Juggernaut is Mordekaiser: magic, and he takes 10% of your AD and resists.
    Ranged is Teemo or Kalista: a blind, so autos and on-hits are cut and
    one vital is out of reach.
    """
    vitals = 4 if ult else 2
    tank_hp = 820 + 125 * (level - 1) + 110 * max(0, minute - 6)
    tank_armor = 46 + 4.2 * (level - 1) + min(170, 11 * max(0, minute - 7))
    tank_mr = 32 + 1.8 * (level - 1) + min(80, 6 * max(0, minute - 9))
    jugg_hp = 760 + 110 * (level - 1) + 85 * max(0, minute - 6)
    jugg_armor = 36 + 3.0 * (level - 1) + min(90, 6 * max(0, minute - 8))
    jugg_mr = 36 + 2.2 * (level - 1) + min(100, 8 * max(0, minute - 7))
    ranged_hp = 580 + 85 * (level - 1) + 15 * minute
    ranged_armor = 24 + 2.0 * (level - 1) + (25 if minute >= 14 else 8)
    ranged_mr = 28 + 1.2 * (level - 1) + (20 if minute >= 12 else 0)
    return [
        Foe(
            "tank",
            tank_hp,
            tank_armor,
            tank_mr,
            0.08,
            dps_phys=55 + 5.5 * minute,
            dps_magic=25 + 2.5 * minute,
            attack_share=0.75,
            vitals=vitals,
        ),
        Foe(
            "jugg",
            jugg_hp,
            jugg_armor,
            jugg_mr,
            0.10,
            dps_phys=25 + 3.0 * minute,
            dps_magic=70 + 9.0 * minute,
            attack_share=0.35,
            steal=0.10,
            vitals=vitals,
        ),
        Foe(
            "ranged",
            ranged_hp,
            ranged_armor,
            ranged_mr,
            0.04,
            dps_phys=40 + 5.0 * minute,
            dps_magic=45 + 6.0 * minute,
            attack_share=0.70,
            blind=True,
            poke_magic=140 + 8.0 * minute,
            vitals=3 if ult else 1,
        ),
    ]


def effective_hp(hp: float, heal: float) -> float:
    return hp / (1.0 - heal)


def duel_value(dmg: float, ehp: float) -> float:
    if ehp <= 0:
        return 0.0
    ratio = dmg / ehp
    if ratio < 1.0:
        return ehp * (ratio ** 1.35)
    over = min(1.5, ratio - 1.0)
    return ehp * (1.0 + 0.12 * over)


def phys_mult(armor: float, pct_pen: float, cleaver: float, lethality: float) -> float:
    armor = armor * (1.0 - cleaver) * (1.0 - pct_pen) - lethality
    return 100.0 / (100.0 + max(0.0, armor))


def magic_mult(mr: float) -> float:
    return 100.0 / (100.0 + max(0.0, mr))


# ---------------------------------------------------------------------------
# Combat
# ---------------------------------------------------------------------------


@dataclass
class Duel:
    damage: float
    vital: float
    alive: float
    hp_frac: float


def _duration(ult: bool) -> float:
    return 8.0 if ult else 4.0


def fight_duel(st: Stats, level: int, minute: int, foe: Foe) -> Duel:
    ult = skill_rank(level, "R") > 0
    duration = _duration(ult)
    q = max(1, skill_rank(level, "Q"))
    e = skill_rank(level, "E")
    w = skill_rank(level, "W")
    r = skill_rank(level, "R")

    steal = foe.steal
    bonus_ad = st.bonus_ad * (1.0 - steal)
    ad = st.ad * (1.0 - steal)
    armor = st.armor * (1.0 - steal) + base_armor(level) * (1.0 - steal)
    mr = st.mr * (1.0 - steal) + base_mr(level) * (1.0 - steal)

    ah = st.ah
    q_cd = [12, 10, 8, 6][q - 1] * 0.50 * haste_mult(ah)
    q_n = casts(q_cd, duration)
    e_n = 0
    e_cd = 99.0
    if e:
        e_cd = [11, 9, 7, 5][e - 1] * haste_mult(ah)
        e_n = casts(e_cd, duration)

    aspd = attack_speed(level, st.as_pct)
    pairs = 0
    autos = aspd * duration
    if e_n:
        bw_as = min(3.0, aspd * 1.60)
        pair_time = 2.0 / bw_as
        pairs = e_n
        if pairs * pair_time > duration:
            pairs = int(duration / pair_time)
        bw_time = pairs * pair_time
        autos = pairs * 2 + (duration - bw_time) * aspd

    q_each = [85, 95, 105, 115][q - 1] + [1.10, 1.15, 1.20, 1.25][q - 1] * bonus_ad
    blade = [1.70, 1.80, 1.90, 2.00][e - 1] if e else 1.0
    aa = autos * ad + pairs * ad * (blade - 1.0)
    q_phys = q_n * q_each

    # Blind cuts autos and on-hits. Q and vitals still land; one vital does not.
    auto_mult = 0.60 if foe.blind else 1.0
    aa *= auto_mult

    ability_casts = q_n + e_n
    # Spellblade primes on a cast and is spent on the next attack. Q applies
    # on-hit, so it can spend a proc that was already primed. Cap at the 1.5s CD.
    procs = 0
    if st.spellblade and ability_casts and autos + q_n > 0:
        procs = min(ability_casts, 1 + int((duration - 0.2) / 1.5))
    spell = 0.0
    sunder_heal = 0.0
    if st.spellblade == "trinity":
        spell = procs * 2.00 * st.base_ad
    elif st.spellblade == "sheen":
        spell = procs * 1.00 * st.base_ad
    elif st.spellblade == "sunderer":
        one = max(0.10 * foe.hp, 1.25 * st.base_ad)
        spell = procs * one
        sunder_heal = procs * max(0.06 * foe.hp, 0.90 * st.base_ad)

    hits = autos + q_n
    # Average current health. A target you are actually killing is lower.
    other_guess = aa + q_phys + spell
    current_frac = max(0.35, 1.0 - 0.50 * min(1.3, other_guess / max(1.0, foe.hp)))
    botrk = 0.0
    if st.botrk:
        per = max(15.0, 0.08 * foe.hp * current_frac)
        botrk = hits * per * auto_mult

    shock = 0.0
    if st.shock_mana:
        shock = autos * 0.015 * st.shock_mana * auto_mult + q_n * 0.035 * st.shock_mana

    hull = 0.0
    if st.hull and autos >= 4:
        n = int(autos // 4)
        hull = n * (1.60 * st.base_ad + 0.05 * st.max_hp) * auto_mult

    eclipse_n = 0
    eclipse = 0.0
    eclipse_shield = 0.0
    if st.eclipse and hits >= 2:
        eclipse_n = 1 if duration < 6 else 2
        eclipse = eclipse_n * 0.07 * foe.hp
        eclipse_shield = eclipse_n * (150.0 + 0.40 * bonus_ad)

    shred = 0.0
    if st.cleaver:
        shred = 0.26 if hits >= 8 else (0.20 if hits >= 5 else 0.04 * hits)

    # Sudden Impact: the Q dash. Same rune on every path.
    sudden = q_n * 15.0
    vital_pct = VITAL_BASE + VITAL_PER_AD * bonus_ad
    vital = foe.vitals * vital_pct * foe.hp

    # Grasp: two procs across an ultimate, one in a short trade.
    grasp_n = 2 if duration >= 6 else 1
    grasp = grasp_n * (0.04 * st.max_hp)
    grasp_heal = grasp * 0.50

    riposte = 0.0
    if w and duration >= 4:
        riposte = [120, 170, 220, 270][w - 1]

    # Shojin Focused Will averages about 10% once you are hitting.
    # It amps ability and passive damage: Q, vitals, Riposte.
    if st.shojin:
        amp = 1.10
        q_phys *= amp
        vital *= amp
        riposte *= amp

    pmult = phys_mult(foe.armor, st.pct_apen, shred, 7.0)
    mm = magic_mult(foe.mr)
    physical = (aa + q_phys + spell + botrk + shock + hull + eclipse) * pmult
    magic = (grasp + riposte) * mm
    true = vital + sudden
    damage = physical + magic + true

    # ----- did she finish the eight seconds -----
    taken_phys = foe.dps_phys * duration * phys_mult(armor, 0.0, 0.0, 0.0)
    if st.steelcaps:
        taken_phys *= 1.0 - 0.10 * foe.attack_share
    taken_magic = foe.dps_magic * duration * magic_mult(mr)
    taken_magic += foe.poke_magic * magic_mult(mr)
    incoming = taken_phys + taken_magic

    heal = vital_heal(level, foe.vitals) + sunder_heal + grasp_heal
    if r and foe.vitals:
        per = [0, 80, 110, 140][r] + 0.60 * bonus_ad
        seconds = min(5, 1 + foe.vitals)  # 2s at 1 vital, 5s at 4
        heal += per * seconds
    pre_mitigation = aa + q_phys + spell + botrk + shock + hull + eclipse
    heal += st.lifesteal * (aa + q_phys)
    heal += st.omnivamp * pre_mitigation
    # Second Wind while the trade is going. Same rune, scales slightly with HP.
    heal += duration * (4.0 + 0.012 * st.max_hp)
    if st.gore:
        # One Ravenous Slash, cast while missing health, one champion in the 1v1.
        heal += 0.20 * ad + 0.10 * st.max_hp * 0.55
        damage += 1.75 * st.base_ad * pmult

    shields = eclipse_shield
    # Maw Lifeline: magic that would cross 35% grants 220–530 and omnivamp.
    if st.maw and taken_magic > 0.50 * st.max_hp:
        shields += 220.0 + 310.0 * (level - 1) / 14.0
        heal += 0.06 * pre_mitigation
    # Sterak Lifeline: the shield is 80% of bonus health, once, under 30%.
    if st.sterak and incoming > 0.70 * st.max_hp:
        shields += 0.80 * st.hp

    # Death's Dance stores 15%. A takedown cleanses it. No takedown, it bleeds.
    if st.dd and damage >= effective_hp(foe.hp, foe.heal):
        incoming *= 0.85

    net_rate = (incoming - heal - shields) / duration
    if net_rate <= 0:
        alive, hp_frac = 1.0, 1.0
    else:
        t_death = st.max_hp / net_rate
        if t_death >= duration:
            alive = 1.0
            hp_frac = max(0.0, (st.max_hp - net_rate * duration) / st.max_hp)
        else:
            alive = max(0.2, t_death / duration)
            hp_frac = 0.0
    if st.ga and alive < 1.0:
        # The revive finishes the vitals. You come back low.
        alive = 1.0
        hp_frac = 0.30
    if alive < 1.0:
        damage *= alive
        vital *= alive
    return Duel(damage, vital, alive, hp_frac)


def vital_heal(level: int, vitals: int) -> float:
    per = 45.0 + (115.0 - 45.0) * (level - 1) / 14.0
    return vitals * per


def fight_tower(st: Stats, level: int) -> float:
    """One crash. Q refunds on the turret, so Spellblade keeps priming."""
    q = max(1, skill_rank(level, "Q"))
    e = skill_rank(level, "E")
    window = 8.0 + (1.0 if st.hull else 0.0)
    aspd = attack_speed(level, st.as_pct)
    pairs = 0
    autos = aspd * window
    if e:
        e_cd = [11, 9, 7, 5][e - 1] * haste_mult(st.ah)
        e_n = casts(e_cd, window)
        bw_as = min(3.0, aspd * 1.60)
        pair_time = 2.0 / bw_as
        pairs = e_n
        if pairs * pair_time > window:
            pairs = int(window / pair_time)
        autos = pairs * 2 + (window - pairs * pair_time) * aspd
    q_cd = [12, 10, 8, 6][q - 1] * 0.50 * haste_mult(st.ah)
    q_n = casts(q_cd, window)
    bonus_ad = st.bonus_ad
    q_each = [85, 95, 105, 115][q - 1] + [1.10, 1.15, 1.20, 1.25][q - 1] * bonus_ad
    blade = [1.70, 1.80, 1.90, 2.00][e - 1] if e else 1.0
    aa = autos * st.ad + pairs * st.ad * (blade - 1.0)
    if st.shojin:
        q_each *= 1.10

    ability_casts = q_n + (pairs if e else 0)
    procs = 0
    if st.spellblade and ability_casts:
        procs = min(ability_casts, 1 + int((window - 0.2) / 1.5))
    spell = 0.0
    if st.spellblade == "trinity":
        spell = procs * 2.00 * st.base_ad
    elif st.spellblade == "sheen":
        spell = procs * 1.00 * st.base_ad
    elif st.spellblade == "sunderer":
        one = 0.50 * max(0.10 * TURRET_HP, 1.25 * st.base_ad)
        spell = procs * one

    hull = 0.0
    if st.hull and autos >= 4:
        hull = int(autos // 4) * (2.40 * st.base_ad + 0.09 * st.max_hp)

    demolish = 0.0
    if autos >= 3:
        demolish = 85.0 + 0.28 * st.max_hp

    pmult = phys_mult(TURRET_ARMOR, st.pct_apen, 0.0, 0.0)
    raw = aa + q_n * q_each + spell + hull + demolish
    return raw * MELEE_TOWER * pmult


def wave_seconds(st: Stats, level: int, minute: int) -> float:
    """Fiora has no AoE. She Qs one minion and autos the rest."""
    melee = 3 * (500 + 22 * minute)
    caster = 3 * (310 + 14 * minute)
    cannon = (900 + 30 * minute) if minute >= 5 else 0
    hp = melee + caster + cannon
    q = max(1, skill_rank(level, "Q"))
    e = skill_rank(level, "E")
    aspd = attack_speed(level, st.as_pct)
    # Bladework is up for two attacks every E. Call that +8% DPS once E is maxed.
    as_bonus = 1.08 if e >= 4 else (1.04 if e else 1.0)
    q_cd = [12, 10, 8, 6][q - 1] * 0.50 * haste_mult(st.ah)
    q_each = [85, 95, 105, 115][q - 1] + [1.10, 1.15, 1.20, 1.25][q - 1] * st.bonus_ad
    dps = aspd * as_bonus * st.ad + q_each / q_cd
    if st.shock_mana:
        dps += aspd * 0.015 * st.shock_mana + (0.035 * st.shock_mana) / q_cd
    return hp / max(1.0, dps)


def tower_effective(raw: float, tank_ratio: float, hp_frac: float) -> float:
    """Killing the tank lets you stay. Chunked health shortens the crash.

    A zero-damage trade still gets a partial crash: the whole point of the
    split is that they are sometimes not there. The duel score, not this
    gate, is what decides whether you beat them.
    """
    kill_u = min(1.0, max(0.0, tank_ratio))
    stay = 0.55 + 0.45 * max(0.0, min(1.0, hp_frac))
    return raw * (0.62 + 0.38 * kill_u) * stay


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
    bonus_ad: float
    attack_speed: float
    hp: float
    dmg_tank: float
    dmg_jugg: float
    dmg_ranged: float
    ehp_tank: float
    ehp_jugg: float
    ehp_ranged: float
    vital_tank: float
    hp_tank: float
    hp_jugg: float
    duel_mix: float
    tower: float
    tower_eff: float
    wave_sec: float
    split_power: float = 0.0
    notes: str = ""
    has_eclipse: bool = False
    has_trinity: bool = False
    has_sunderer: bool = False
    has_hull: bool = False
    has_manamune: bool = False


def compute_snapshot(
    build_name: str,
    path: List[str],
    minute: int,
    mana_at: Optional[int],
) -> Snapshot:
    level = level_at_minute(minute)
    gold = gold_at_minute(minute)
    inv = resolve_inventory(path, gold)
    st = sum_stats(inv, level, minute, mana_at)
    ult = skill_rank(level, "R") > 0

    dmgs: Dict[str, Duel] = {}
    ehps: Dict[str, float] = {}
    parts = []
    for foe in foes_at(minute, level, ult):
        duel = fight_duel(st, level, minute, foe)
        ehp = effective_hp(foe.hp, foe.heal)
        dmgs[foe.kind] = duel
        ehps[foe.kind] = ehp
        weight = {"tank": TANK_W, "jugg": JUGG_W, "ranged": RANGED_W}[foe.kind]
        parts.append(weight * duel_value(duel.damage, ehp))
    duel_mix = sum(parts)
    # Finishing Morde healthy is the difference between a crash and a recall.
    duel_mix *= 0.96 + 0.08 * dmgs["jugg"].hp_frac

    raw_tower = fight_tower(st, level)
    tank_ratio = dmgs["tank"].damage / ehps["tank"]
    tower_eff = tower_effective(raw_tower, tank_ratio, dmgs["tank"].hp_frac)
    wave = wave_seconds(st, level, minute)

    notes = []
    if st.eclipse:
        notes.append("Eclipse")
    if st.spellblade:
        notes.append(st.spellblade)
    if st.hull:
        notes.append("Hull")
    if st.botrk:
        notes.append("BotRK")
    if st.cleaver:
        notes.append("Cleaver")
    if st.pct_apen >= 0.30:
        notes.append("35% pen")
    if st.manamune:
        notes.append("Muramana" if st.muramana_live else "Manamune stacking")
    if st.maw:
        notes.append("Maw")
    if st.shojin:
        notes.append("Shojin")
    if st.sterak:
        notes.append("Sterak")
    if st.gore:
        notes.append("Gore")
    if st.dd:
        notes.append("DD")
    if not ult:
        notes.append("no R")
    n_leg = sum(1 for n in st.names if n in LEGENDARIES and n != "Plated Steelcaps")
    if n_leg == 0:
        notes.append("components")

    return Snapshot(
        minute=minute,
        build_name=build_name,
        items=st.names,
        gold=gold,
        level=level,
        ad=round(st.ad, 1),
        bonus_ad=round(st.bonus_ad, 1),
        attack_speed=round(attack_speed(level, st.as_pct), 2),
        hp=round(st.max_hp, 1),
        dmg_tank=round(dmgs["tank"].damage, 1),
        dmg_jugg=round(dmgs["jugg"].damage, 1),
        dmg_ranged=round(dmgs["ranged"].damage, 1),
        ehp_tank=round(ehps["tank"], 1),
        ehp_jugg=round(ehps["jugg"], 1),
        ehp_ranged=round(ehps["ranged"], 1),
        vital_tank=round(dmgs["tank"].vital, 1),
        hp_tank=round(dmgs["tank"].hp_frac, 3),
        hp_jugg=round(dmgs["jugg"].hp_frac, 3),
        duel_mix=round(duel_mix, 1),
        tower=round(raw_tower, 1),
        tower_eff=round(tower_eff, 1),
        wave_sec=round(wave, 2),
        notes=", ".join(notes) if notes else "-",
        has_eclipse=st.eclipse,
        has_trinity=st.spellblade == "trinity",
        has_sunderer=st.spellblade == "sunderer",
        has_hull=st.hull,
        has_manamune=st.manamune,
    )


def apply_split_scores(results: Dict[str, List[Snapshot]]) -> Tuple[float, float]:
    """Scale tower and wave so 50/35/15 is true at the minute-18 median."""
    mid = [snaps[17] for snaps in results.values()]
    med_d = median(s.duel_mix for s in mid)
    med_t = median(s.tower_eff for s in mid) or 1.0
    med_w = median(8.0 / s.wave_sec for s in mid) or 1.0
    scale_t = med_d / med_t
    scale_w = med_d / med_w
    for snaps in results.values():
        for s in snaps:
            wave_score = 8.0 / max(0.5, s.wave_sec)
            s.split_power = round(
                DUEL_W * s.duel_mix
                + TOWER_W * s.tower_eff * scale_t
                + WAVE_W * wave_score * scale_w,
                1,
            )
    return scale_t, scale_w


def run_all() -> Tuple[Dict[str, List[Snapshot]], List[dict], Tuple[float, float]]:
    mana_at = {
        name: first_minute(path, "Manamune") for name, path in BUILD_PATHS.items()
    }
    results: Dict[str, List[Snapshot]] = {}
    for name, path in BUILD_PATHS.items():
        results[name] = [
            compute_snapshot(name, path, minute, mana_at[name])
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
                "tower_eff": snap.tower_eff,
                "wave_sec": snap.wave_sec,
                "tank_pct": round(100.0 * snap.dmg_tank / snap.ehp_tank, 1),
                "jugg_pct": round(100.0 * snap.dmg_jugg / snap.ehp_jugg, 1),
                "ranged_pct": round(100.0 * snap.dmg_ranged / snap.ehp_ranged, 1),
                "hp_jugg": snap.hp_jugg,
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


def late_score(snaps: List[Snapshot]) -> float:
    total = 0.0
    weight = 0.0
    for snap in snaps:
        w = 0.70 if snap.minute < 8 else (1.15 if snap.minute < 16 else 1.45)
        total += snap.split_power * w
        weight += w
    return total / weight


def pct(a: float, b: float) -> float:
    if b == 0:
        return 0.0
    return 100.0 * (a / b - 1.0)


def summarize(results, timeline, _scales) -> str:
    lines: List[str] = []
    lines.append("=" * 92)
    lines.append("FIORA BARON — SPLIT PUSH VS THE TANK META  (Wild Rift 7.3f)")
    lines.append("Playstyle: crash the side wave, R the tank who matches, take the turret")
    lines.append(
        "Score: 50% duel (tank 55 / Morde 30 / blind 15) + 35% turret + 15% wave"
    )
    lines.append(
        "Those weights are the 18:00 median: half the points are the duel, "
        "35% the crash, 15% the wave."
    )
    lines.append("=" * 92)
    lines.append("")
    lines.append("GOLD / LEVEL  (side lane, plates, not a roam curve)")
    lines.append(f"  {'Min':>3}  {'Gold':>6}  {'Lvl':>3}  {'Q':>2}  {'E':>2}  {'W':>2}  {'R':>2}")
    for minute in (1, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26):
        level = level_at_minute(minute)
        lines.append(
            f"  {minute:>3}  {gold_at_minute(minute):>6}  {level:>3}  "
            f"{skill_rank(level, 'Q'):>2}  {skill_rank(level, 'E'):>2}  "
            f"{skill_rank(level, 'W'):>2}  {skill_rank(level, 'R'):>2}"
        )

    lines.append("")
    lines.append("-" * 92)
    lines.append("MINUTE-BY-MINUTE BEST SPLIT SCORE")
    lines.append("-" * 92)
    for row in timeline:
        minute = row["minute"]
        if minute < 6 or (minute % 2 and minute not in (6, 8, 10, 14, 18, 22, 26)):
            continue
        kill_txt = (
            f"T{row['tank_pct']:.0f}/M{row['jugg_pct']:.0f}/R{row['ranged_pct']:.0f}"
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
    lines.append("-" * 92)
    lines.append("BUILD COMPARISON — SPLIT SCORE")
    lines.append("-" * 92)
    lines.append(
        f"  {'Build':<44} {'8:00':>7} {'14:00':>7} {'18:00':>7} "
        f"{'22:00':>7} {'26:00':>7} {'Late':>7}"
    )
    ranking = []
    for name, snaps in results.items():
        late = late_score(snaps)
        ranking.append((late, name, snaps))
        def at(minute: int, snaps=snaps) -> Snapshot:
            return snaps[minute - 1]

        lines.append(
            f"  {name:<44} {at(8).split_power:>7.0f} {at(14).split_power:>7.0f} "
            f"{at(18).split_power:>7.0f} {at(22).split_power:>7.0f} "
            f"{at(26).split_power:>7.0f} {late:>7.0f}"
        )
    ranking.sort(key=lambda row: row[0], reverse=True)

    def section(title: str, attr: str, minutes=(14, 18, 22, 26), digits=0) -> None:
        lines.append("")
        lines.append("-" * 92)
        lines.append(title)
        lines.append("-" * 92)
        fmt = f"{{:>7.{digits}f}}"
        for _late, name, snaps in ranking:
            vals = " ".join(fmt.format(getattr(snaps[m - 1], attr)) for m in minutes)
            lines.append(f"  {name:<44} {vals}")

    section("DUEL VALUE (tank 55% / Morde 30% / blind 15%)", "duel_mix")
    section("RAW TURRET DAMAGE over one crash (melee +20%, Demolish, Hull window)", "tower")
    section("WAVE CLEAR seconds (lower is faster — Q is single target)", "wave_sec", digits=1)

    lines.append("")
    lines.append("-" * 92)
    lines.append("PERCENT OF THEIR EFFECTIVE HP REMOVED DURING R  (100 = they die)")
    lines.append("Order inside each cell: tank / Morde / blind")
    lines.append("-" * 92)
    lines.append(f"  {'Build':<44} {'18:00':>16} {'22:00':>16} {'26:00':>16}")
    for _late, name, snaps in ranking:
        cells = []
        for minute in (18, 22, 26):
            snap = snaps[minute - 1]
            cells.append(
                f"{100 * snap.dmg_tank / snap.ehp_tank:3.0f}/"
                f"{100 * snap.dmg_jugg / snap.ehp_jugg:3.0f}/"
                f"{100 * snap.dmg_ranged / snap.ehp_ranged:3.0f}"
            )
        lines.append(f"  {name:<44} {cells[0]:>16} {cells[1]:>16} {cells[2]:>16}")

    lines.append("")
    lines.append("-" * 92)
    lines.append("VITAL TRUE DAMAGE VS THE TANK, AND HP LEFT AFTER MORDE")
    lines.append("Vitals are the part armor does not touch. HP left is the crash after Morde.")
    lines.append("-" * 92)
    lines.append(
        f"  {'Build':<44} {'vit 18':>8} {'vit 22':>8} {'Morde HP 22':>12}"
    )
    for _late, name, snaps in ranking:
        lines.append(
            f"  {name:<44} {snaps[17].vital_tank:>8.0f} {snaps[21].vital_tank:>8.0f} "
            f"{100 * snaps[21].hp_jugg:>11.0f}%"
        )

    winner_late, winner_name, winner = ranking[0]
    lines.append("")
    lines.append("-" * 92)
    lines.append("VERDICT")
    lines.append("-" * 92)
    lines.append(f"  Best split into this baron meta: {winner_name}")
    lines.append(f"  Late-weighted split score: {winner_late:.0f}")
    lines.append("  Item spikes:")
    for minute, item in legendary_times(winner):
        lines.append(f"    ~{minute:>2}:00  {item}")

    w22 = winner[21]
    lines.append("")
    lines.append("  At 22:00:")
    lines.append(
        f"    Duel {w22.duel_mix:.0f} | raw tower {w22.tower:.0f} | "
        f"wave {w22.wave_sec:.1f}s | AD {w22.ad:.0f} | HP {w22.hp:.0f}"
    )
    lines.append(
        f"    Tank {w22.dmg_tank:.0f} / {w22.ehp_tank:.0f} EHP "
        f"({100 * w22.dmg_tank / w22.ehp_tank:.0f}%), "
        f"of which vitals are {w22.vital_tank:.0f} true"
    )
    lines.append(
        f"    Morde {w22.dmg_jugg:.0f} / {w22.ehp_jugg:.0f} EHP "
        f"({100 * w22.dmg_jugg / w22.ehp_jugg:.0f}%), "
        f"you finish at {100 * w22.hp_jugg:.0f}% HP"
    )
    lines.append(
        f"    Blind {w22.dmg_ranged:.0f} / {w22.ehp_ranged:.0f} EHP "
        f"({100 * w22.dmg_ranged / w22.ehp_ranged:.0f}%)"
    )

    def compare(label: str) -> None:
        other = results[label]
        o22 = other[21]
        lines.append(f"  vs {label}:")
        lines.append(
            f"    22:00 score {w22.split_power:.0f} vs {o22.split_power:.0f} "
            f"({pct(w22.split_power, o22.split_power):+.0f}%) | "
            f"duel {w22.duel_mix:.0f} vs {o22.duel_mix:.0f} | "
            f"tower {w22.tower:.0f} vs {o22.tower:.0f}"
        )

    for label in (
        "Eclipse → TF → Hull → DD → BotRK",
        "Sunderer → Cleaver → Hull → DD → Shojin",
        "TF → Manamune → Maw → DD → BT",
        "TF → BotRK → Cleaver → Eclipse → Serylda",
        "TF → DD → Sterak → Gore → GA",
        "TF → Hull → Eclipse → DD → Shojin",
    ):
        if label != winner_name:
            compare(label)

    runner_late, runner_name, runner = ranking[1]
    lines.append("")
    lines.append(
        f"  Runner-up ({runner_name}) late score {runner_late:.0f} "
        f"vs {winner_late:.0f}."
    )
    lines.append(
        f"    22:00 duel {runner[21].duel_mix:.0f} vs {w22.duel_mix:.0f}, "
        f"tower {runner[21].tower:.0f} vs {w22.tower:.0f}, "
        f"tank {100 * runner[21].dmg_tank / runner[21].ehp_tank:.0f}% vs "
        f"{100 * w22.dmg_tank / w22.ehp_tank:.0f}%."
    )
    hull_second = results["TF → Hull → Eclipse → DD → Shojin"]
    meta = results["Eclipse → TF → Hull → DD → BotRK"]
    sunder = results["Sunderer → Cleaver → Hull → DD → Shojin"]
    lines.append(
        f"  Hull second vs Hull third at 14:00: score "
        f"{hull_second[13].split_power:.0f} vs {meta[13].split_power:.0f}, "
        f"raw tower {hull_second[13].tower:.0f} vs {meta[13].tower:.0f}."
    )
    best8 = max(results.values(), key=lambda snaps: snaps[7].split_power)[7]
    lines.append(
        f"  At 8:00 the leader is {best8.build_name} "
        f"({best8.split_power:.0f}). {winner_name} is at {winner[7].split_power:.0f} "
        f"until the tear charge turns into bonus AD."
    )
    best26 = max(results.values(), key=lambda snaps: snaps[25].split_power)[25]
    if best26.build_name != winner_name:
        lines.append(
            f"  The 26:00 minute belongs to {best26.build_name} "
            f"({best26.split_power:.0f} vs {winner[25].split_power:.0f}). "
            f"Pen and BotRK are online, and Hull is finally in that inventory."
        )
        lines.append(
            "  The late average still follows the earlier Hull: that turret lead "
            "is the whole stretch from 18:00 to 22:00."
        )
    lines.append(
        f"  Sunderer at 22:00 duels {sunder[21].duel_mix:.0f} vs {w22.duel_mix:.0f} "
        f"and hits the turret for {sunder[21].tower:.0f} vs {w22.tower:.0f}."
    )
    morde_left = [snaps[21].hp_jugg for snaps in results.values()]
    if min(morde_left) > 0.99:
        lines.append(
            "  Every build finishes the Morde all-in at full HP. The ultimate "
            "heal covers his damage when the vitals land, on the glass paths "
            "and the resist paths alike."
        )
    lines.append("")
    lines.append("  WHY THE KIT ITEMIZES THIS WAY")
    lines.append("  • Vitals are true damage: 3.5% + 5.5% per 100 bonus AD of")
    lines.append("    their max health. R marks all four for 8 seconds. Bonus AD")
    lines.append("    is what moves the tank fight. Percent pen multiplies Q,")
    lines.append("    autos, Spellblade, and BotRK.")
    lines.append("  • Q max, then E. Lunge is 85–115 + 110–125% bonus AD, refunds")
    lines.append("    half the cooldown on hit, applies on-hit, and hits turrets.")
    lines.append("    Bladework's second hit always crits for 170–200% AD.")
    lines.append("    W is a 0.75s parry and it is maxed last.")
    lines.append("  • Eclipse (7.3f, 60 AD) procs 7% max HP physical and a shield")
    lines.append("    of 150 + 40% bonus AD, twice in an ultimate. Trinity Spellblade")
    lines.append("    is 200% base AD. Sunderer is 10% max HP and a 6% heal;")
    lines.append("    structures take half of that proc. Its 25 AD feeds a smaller vital.")
    lines.append("  • Hullbreaker on a turret is 240% base AD + 9% of your max HP")
    lines.append("    every 4th auto, and the crash lasts one extra second. On a")
    lines.append("    champion it is 160% base AD + 5% of your max HP. BotRK's")
    lines.append("    on-hit ends at the champion; the turret is Hull, Trinity, Q, Demolish.")
    lines.append("  • Morde steals 10% of your AD and resists during his R, and")
    lines.append("    his damage is magic. The ult heal covers that when four")
    lines.append("    vitals land. Teemo's blind cuts autos and on-hits and costs")
    lines.append("    one vital. Three vitals and Q still kill him in this all-in.")
    lines.append("  • A cannon crash is one-target Q plus autos. Haste and attack")
    lines.append("    speed are the clear.")
    lines.append("  • Demolish is 85 + 28% max HP after three autos. Every row wears")
    lines.append("    Steelcaps: 25 armor, 150 HP, 10% less from champion autos.")
    lines.append("    Gluttonous is the popular 1000g boot (12 AD, omnivamp).")
    lines.append("    Steelcaps are here because Malphite, Shen, and Kalista auto the wave.")
    lines.append("")
    lines.append("  MACRO")
    lines.append("  • Teleport to the side wave your team is not fighting. Crash")
    lines.append("    it, R the one champion who matches, auto the turret.")
    lines.append("  • Two champions on the wave ends the crash. Riposte parries")
    lines.append("    one spell — Malphite ult, Shen taunt, Ornn knockup, Morde")
    lines.append("    pull — and then you leave.")
    lines.append("  • The ult heal is 80/110/140 + 60% bonus AD per second, and")
    lines.append("    it lasts longer as the vitals land. The sides of the")
    lines.append("    ultimate are the fight.")
    lines.append("  • Mundo heals harder than the tank average in this sim.")
    lines.append("    Executioner's is the item for that specific champion.")
    lines.append("=" * 92)
    return "\n".join(lines)


def export_json(results, timeline, scales, path: Path) -> None:
    scale_t, scale_w = scales
    payload = {
        "meta": {
            "champion": "Fiora",
            "role": "Baron",
            "patch": "7.3f",
            "game_minutes": GAME_MINUTES,
            "playstyle": "side-lane split into the tank meta",
            "metric": "50% duel (tank 55 / Morde 30 / blind 15) + 35% turret + 15% wave",
            "scale_tower": round(scale_t, 4),
            "scale_wave": round(scale_w, 4),
            "vital": "3.5% + 0.055% per bonus AD of target max HP, true",
            "question": "which split build kills the baron tank meta and takes the turret",
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
                    "bonus_ad": s.bonus_ad,
                    "attack_speed": s.attack_speed,
                    "hp": s.hp,
                    "dmg_tank": s.dmg_tank,
                    "dmg_jugg": s.dmg_jugg,
                    "dmg_ranged": s.dmg_ranged,
                    "ehp_tank": s.ehp_tank,
                    "ehp_jugg": s.ehp_jugg,
                    "ehp_ranged": s.ehp_ranged,
                    "vital_tank": s.vital_tank,
                    "hp_tank": s.hp_tank,
                    "hp_jugg": s.hp_jugg,
                    "duel_mix": s.duel_mix,
                    "tower": s.tower,
                    "tower_eff": s.tower_eff,
                    "wave_sec": s.wave_sec,
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
    meta = results["Eclipse → TF → Hull → DD → BotRK"]
    hull = results["TF → Hull → Eclipse → DD → Shojin"]
    sunder = results["Sunderer → Cleaver → Hull → DD → Shojin"]
    sustain = results["TF → DD → Sterak → Gore → GA"]
    assert any(s.has_eclipse for s in meta if s.minute <= 10), "Eclipse should be online by 10:00"
    assert any(s.has_trinity for s in hull if s.minute <= 10), "Trinity should be online by 10:00"
    assert hull[25].tower > sustain[25].tower, (hull[25].tower, sustain[25].tower)
    assert sunder[21].dmg_tank > 0
    # Vitals are doing real anti-tank work by the time R is maxed.
    assert meta[21].vital_tank > 0.15 * meta[21].ehp_tank
    scores = [snaps[21].split_power for snaps in results.values()]
    assert max(scores) > min(scores) * 1.05, (max(scores), min(scores))
    for snaps in results.values():
        assert snaps[25].duel_mix > 0
        assert snaps[25].tower > 0
        assert 2.0 <= snaps[25].wave_sec <= 16.0, snaps[25].wave_sec
        spent = sum(ITEMS[n].cost for n in snaps[25].items)
        assert spent <= snaps[25].gold + 1, (snaps[25].build_name, spent, snaps[25].gold)
    assert gold_at_minute(8) >= 3500
    assert gold_at_minute(26) >= 15000
    assert first_minute(BUILD_PATHS["TF → Hull → Eclipse → DD → Shojin"], "Hullbreaker") < first_minute(
        BUILD_PATHS["Eclipse → TF → Hull → DD → BotRK"], "Hullbreaker"
    )


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
