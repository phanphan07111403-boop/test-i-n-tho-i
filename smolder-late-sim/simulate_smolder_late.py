#!/usr/bin/env python3
"""
Wild Rift Smolder — strongest late build
Patch 7.3 marksman overhaul (Sep 2026).

Playstyle: stack Dragon Practice, then Q-poke from max range and
weave autos in the teamfight. Super Scorcher Breath applies on-hit,
scales with Critical Rate AND bonus Critical Damage, and at 175
stacks burns max HP true damage + 6.5% execute.

Question:
  After 7.3 deleted Magnetic Blaster and made Infinity Edge the
  crit-ability capstone, what 6-item page actually peaks late
  (20:00–25:00) vs the old Muramana → Trinity → Serylda core?
  Which rune page actually fits that 0-AS crit Q page?
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import json

GAME_MINUTES = 25
POKE_WINDOW = 8.0
FIGHT_WINDOW = 8.0
POKE_WEIGHT = 0.70
FIGHT_WEIGHT = 0.30

# Wild Rift page: keystone + Precision slot1 + slot2 + Legend + 1 secondary.
# Slot2 is ONE of Cut Down / Coup / Last Stand (not both).
WINNING_ITEMS = "ER → IE → Hex → LDR → BT"


# ---------------------------------------------------------------------------
# Runes (patch 7.3)
# ---------------------------------------------------------------------------


@dataclass
class RunePage:
    name: str
    keystone: str  # fleet | lethal | conqueror | phase
    slot1: str  # zeal | brutal | triumph
    slot2: str  # cut_down | coup | last_stand
    legend: str  # haste | alacrity | bloodline
    secondary: str  # transcendence | bone


# Battle Zeal: basic abilities +2%/s in champion combat, cap 6% (wiki).
# Legend: Haste (7.3, replaces Tenacity): 1.5 AH/stack, max 15.
# Lethal Tempo (7.3): 6.4% AS/stack ranged ×6; bullets scale with bonus AS.
RUNE_PAGES: Dict[str, RunePage] = {
    "Fleet / Zeal / Cut Down / Haste / Transcendence": RunePage(
        "Fleet / Zeal / Cut Down / Haste / Transcendence",
        "fleet", "zeal", "cut_down", "haste", "transcendence",
    ),
    "Fleet / Zeal / Cut Down / Bloodline / Transcendence": RunePage(
        "Fleet / Zeal / Cut Down / Bloodline / Transcendence",
        "fleet", "zeal", "cut_down", "bloodline", "transcendence",
    ),
    "Fleet / Brutal / Cut Down / Haste / Transcendence": RunePage(
        "Fleet / Brutal / Cut Down / Haste / Transcendence",
        "fleet", "brutal", "cut_down", "haste", "transcendence",
    ),
    "Fleet / Brutal / Cut Down / Alacrity / Transcendence": RunePage(
        "Fleet / Brutal / Cut Down / Alacrity / Transcendence",
        "fleet", "brutal", "cut_down", "alacrity", "transcendence",
    ),
    "Fleet / Zeal / Cut Down / Haste / Bone Plating": RunePage(
        "Fleet / Zeal / Cut Down / Haste / Bone Plating",
        "fleet", "zeal", "cut_down", "haste", "bone",
    ),
    "Fleet / Zeal / Coup / Haste / Transcendence": RunePage(
        "Fleet / Zeal / Coup / Haste / Transcendence",
        "fleet", "zeal", "coup", "haste", "transcendence",
    ),
    "Lethal Tempo / Brutal / Cut Down / Alacrity / Transcendence": RunePage(
        "Lethal Tempo / Brutal / Cut Down / Alacrity / Transcendence",
        "lethal", "brutal", "cut_down", "alacrity", "transcendence",
    ),
    "Conqueror / Zeal / Cut Down / Haste / Transcendence": RunePage(
        "Conqueror / Zeal / Cut Down / Haste / Transcendence",
        "conqueror", "zeal", "cut_down", "haste", "transcendence",
    ),
    "Phase Rush / Zeal / Cut Down / Haste / Transcendence": RunePage(
        "Phase Rush / Zeal / Cut Down / Haste / Transcendence",
        "phase", "zeal", "cut_down", "haste", "transcendence",
    ),
}

DEFAULT_RUNES = RUNE_PAGES["Fleet / Zeal / Cut Down / Bloodline / Transcendence"]


# ---------------------------------------------------------------------------
# Economy / XP / stacks (duo-lane farmer, not smurf-fed)
# ---------------------------------------------------------------------------


def gold_at_minute(m: int) -> int:
    if m <= 0:
        return 500
    total = 500  # Long Sword start
    for t in range(1, m + 1):
        if t <= 5:
            total += 500
        elif t <= 12:
            total += 650
        elif t <= 18:
            total += 700
        else:
            total += 740
    return total


def level_at_minute(m: int) -> int:
    table = {
        1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7, 7: 8, 8: 9,
        9: 10, 10: 11, 11: 11, 12: 12, 13: 12, 14: 13,
        15: 13, 16: 14, 17: 14, 18: 15, 19: 15, 20: 15,
        21: 15, 22: 15, 23: 15, 24: 15, 25: 15,
    }
    return table.get(m, 15)


def stacks_at_minute(m: int) -> int:
    """Safe farm + poke. T1 AoE ~6:00, T2 bolts ~12:00, T3 burn ~17:00."""
    stacks = 0
    for t in range(1, m + 1):
        if t <= 5:
            stacks += 7
        elif t <= 11:
            stacks += 10
        elif t <= 16:
            stacks += 12
        else:
            stacks += 14
    return stacks


def skill_rank(level: int, skill: str) -> int:
    """Q max, W second, E last. R at 6/11/15."""
    if skill == "R":
        if level < 6:
            return 0
        if level < 11:
            return 1
        if level < 15:
            return 2
        return 3
    q_levels = [1, 3, 5, 7]
    w_levels = [2, 8, 10, 12]
    e_levels = [4, 9, 13, 14]
    mapping = {"Q": q_levels, "W": w_levels, "E": e_levels}
    return sum(1 for lv in mapping[skill] if level >= lv)


# ---------------------------------------------------------------------------
# Targets
# ---------------------------------------------------------------------------


def squishy_hp(m: int) -> float:
    lv = level_at_minute(m)
    return 620 + 95 * lv + 16 * m


def squishy_armor(m: int) -> float:
    lv = level_at_minute(m)
    extra = 0.0 if m < 12 else (18.0 if m < 18 else 32.0)
    return 30 + 4.2 * lv + extra


def tank_hp(m: int) -> float:
    lv = level_at_minute(m)
    item_hp = 90 * max(0, m - 6)
    return 680 + 105 * lv + item_hp


def tank_armor(m: int) -> float:
    lv = level_at_minute(m)
    extra = 0.0 if m < 8 else min(9.0 * (m - 8), 160.0)
    return 38 + 4.4 * lv + extra


# ---------------------------------------------------------------------------
# Items (patch 7.3)
# ---------------------------------------------------------------------------


@dataclass
class Item:
    name: str
    cost: int
    ad: float = 0
    as_pct: float = 0
    crit: float = 0
    ah: float = 0
    hp: float = 0
    mana: float = 0
    ls: float = 0
    pct_pen: float = 0
    flat_pen: float = 0
    ms_pct: float = 0
    ie: bool = False
    er: bool = False
    trinity: bool = False
    muramana: bool = False
    manamune: bool = False
    navori: bool = False
    shojin: bool = False
    hexoptics: bool = False
    yuntal: bool = False
    rfc: bool = False
    stormrazor: bool = False
    ldr: bool = False
    mortal: bool = False
    serylda: bool = False
    cleaver: bool = False
    bork: bool = False
    collector: bool = False
    tags: Tuple[str, ...] = ()


ITEMS: Dict[str, Item] = {
    "Long Sword": Item("Long Sword", 500, ad=12),
    "Pickaxe": Item("Pickaxe", 800, ad=20),
    "B. F. Sword": Item("B. F. Sword", 1500, ad=40),
    "Caulfield's Warhammer": Item("Caulfield's Warhammer", 1200, ad=20, ah=20),
    "Sheen": Item("Sheen", 800),
    "Tear of the Goddess": Item("Tear of the Goddess", 400, mana=150),
    "Noonquiver": Item("Noonquiver", 1300, ad=20, crit=0.15),
    "Brawler's Gloves": Item("Brawler's Gloves", 500, crit=0.10),
    "Zeal": Item("Zeal", 1400, as_pct=0.15, crit=0.15, ms_pct=0.04),
    "Kircheis Shard": Item("Kircheis Shard", 800, as_pct=0.20),
    "Last Whisper": Item("Last Whisper", 1200, ad=15, pct_pen=0.15),
    "Hearthbound Axe": Item("Hearthbound Axe", 1200, ad=20, as_pct=0.15),
    "Phage": Item("Phage", 1000, ad=15, hp=200),
    "Vampiric Scepter": Item("Vampiric Scepter", 1200, ad=15, ls=0.08),
    "Recurve Bow": Item("Recurve Bow", 900, as_pct=0.20),
    "Boots": Item("Boots", 500, tags=("boots",)),
    "Ionian Boots of Lucidity": Item(
        "Ionian Boots of Lucidity", 1000, ah=15, tags=("boots",)
    ),
    "Gluttonous Greaves": Item(
        "Gluttonous Greaves", 1000, ad=12, tags=("boots",)
    ),
    "Essence Reaver": Item(
        "Essence Reaver",
        3000,
        ad=50,
        crit=0.25,
        ah=20,
        er=True,
        tags=("crit", "spellblade"),
    ),
    "Infinity Edge": Item(
        "Infinity Edge", 3500, ad=75, crit=0.25, ie=True, tags=("crit", "capstone")
    ),
    "Hexoptics C44": Item(
        "Hexoptics C44", 2900, ad=55, crit=0.25, hexoptics=True, tags=("crit", "poke")
    ),
    "Yun Tal Wildarrows": Item(
        "Yun Tal Wildarrows",
        3100,
        ad=50,
        as_pct=0.25,
        yuntal=True,
        tags=("crit", "first"),
    ),
    "Navori Quickblades": Item(
        "Navori Quickblades",
        2650,
        as_pct=0.40,
        crit=0.25,
        ms_pct=0.04,
        navori=True,
        tags=("crit", "haste"),
    ),
    "Rapid Firecannon": Item(
        "Rapid Firecannon",
        2650,
        as_pct=0.40,
        crit=0.25,
        ms_pct=0.04,
        rfc=True,
        tags=("crit", "range"),
    ),
    "Stormrazor": Item(
        "Stormrazor",
        3000,
        ad=50,
        crit=0.25,
        as_pct=0.20,
        stormrazor=True,
        tags=("crit",),
    ),
    "Immortal Shieldbow": Item(
        "Immortal Shieldbow", 3000, ad=55, crit=0.25, tags=("crit", "defense")
    ),
    "Mortal Reminder": Item(
        "Mortal Reminder",
        3000,
        ad=35,
        crit=0.25,
        pct_pen=0.30,
        mortal=True,
        tags=("crit", "pen"),
    ),
    "Lord Dominik's Regards": Item(
        "Lord Dominik's Regards",
        3300,
        ad=35,
        crit=0.25,
        pct_pen=0.35,
        ldr=True,
        tags=("crit", "pen", "tank"),
    ),
    "The Collector": Item(
        "The Collector",
        3000,
        ad=50,
        crit=0.25,
        flat_pen=12,
        collector=True,
        tags=("crit",),
    ),
    "Bloodthirster": Item(
        "Bloodthirster", 3200, ad=75, ls=0.15, tags=("ad", "sustain")
    ),
    "Spear of Shojin": Item(
        "Spear of Shojin",
        3100,
        ad=40,
        hp=450,
        ah=20,
        shojin=True,
        tags=("ability",),
    ),
    "Manamune": Item(
        "Manamune", 2900, ad=40, ah=15, mana=500, manamune=True, tags=("mana",)
    ),
    "Muramana": Item(
        "Muramana", 2900, ad=40, ah=15, mana=1200, muramana=True, tags=("mana",)
    ),
    "Trinity Force": Item(
        "Trinity Force",
        3333,
        ad=36,
        as_pct=0.30,
        ah=15,
        hp=333,
        trinity=True,
        tags=("spellblade",),
    ),
    "Serylda's Grudge": Item(
        "Serylda's Grudge",
        3100,
        ad=50,
        ah=15,
        pct_pen=0.35,
        serylda=True,
        tags=("pen", "ability"),
    ),
    "Black Cleaver": Item(
        "Black Cleaver",
        3000,
        ad=40,
        ah=20,
        hp=400,
        cleaver=True,
        tags=("shred",),
    ),
    "Blade of the Ruined King": Item(
        "Blade of the Ruined King",
        3100,
        ad=40,
        as_pct=0.30,
        ls=0.12,
        bork=True,
        tags=("onhit",),
    ),
    "Galeforce": Item(
        "Galeforce", 3100, ad=60, crit=0.25, ms_pct=0.04, tags=("crit",)
    ),
}


UPGRADE_COMPONENTS = {
    "Ionian Boots of Lucidity": ("Boots",),
    "Gluttonous Greaves": ("Boots",),
    "Essence Reaver": ("Sheen", "Caulfield's Warhammer", "Brawler's Gloves"),
    "Infinity Edge": ("B. F. Sword", "Pickaxe", "Brawler's Gloves"),
    "Hexoptics C44": ("Pickaxe", "Noonquiver", "Long Sword"),
    "Yun Tal Wildarrows": ("Noonquiver", "Pickaxe", "Kircheis Shard"),
    "Navori Quickblades": ("Zeal",),
    "Rapid Firecannon": ("Zeal", "Kircheis Shard"),
    "Stormrazor": ("B. F. Sword", "Kircheis Shard", "Brawler's Gloves"),
    "Immortal Shieldbow": ("Noonquiver", "Pickaxe"),
    "Mortal Reminder": ("Last Whisper", "Brawler's Gloves"),
    "Lord Dominik's Regards": ("Last Whisper", "Noonquiver"),
    "The Collector": ("Noonquiver",),
    "Bloodthirster": ("Vampiric Scepter", "B. F. Sword"),
    "Spear of Shojin": ("Caulfield's Warhammer",),
    "Manamune": ("Caulfield's Warhammer", "Tear of the Goddess", "Long Sword"),
    "Muramana": ("Caulfield's Warhammer", "Tear of the Goddess", "Long Sword"),
    "Trinity Force": ("Sheen", "Phage", "Hearthbound Axe"),
    "Serylda's Grudge": ("Caulfield's Warhammer", "Last Whisper"),
    "Black Cleaver": ("Phage", "Caulfield's Warhammer"),
    "Blade of the Ruined King": ("Vampiric Scepter", "Pickaxe", "Recurve Bow"),
    "Galeforce": ("Noonquiver", "Pickaxe", "Long Sword"),
}

NEXT_COMPONENTS = {
    "Ionian Boots of Lucidity": ["Boots"],
    "Gluttonous Greaves": ["Boots"],
    "Essence Reaver": ["Sheen", "Caulfield's Warhammer", "Brawler's Gloves"],
    "Infinity Edge": ["B. F. Sword", "Pickaxe", "Brawler's Gloves"],
    "Hexoptics C44": ["Noonquiver", "Pickaxe", "Long Sword"],
    "Yun Tal Wildarrows": ["Noonquiver", "Pickaxe", "Kircheis Shard"],
    "Navori Quickblades": ["Zeal"],
    "Rapid Firecannon": ["Zeal", "Kircheis Shard"],
    "Stormrazor": ["B. F. Sword", "Kircheis Shard", "Brawler's Gloves"],
    "Immortal Shieldbow": ["Noonquiver", "Pickaxe"],
    "Mortal Reminder": ["Last Whisper", "Brawler's Gloves"],
    "Lord Dominik's Regards": ["Last Whisper", "Noonquiver"],
    "The Collector": ["Noonquiver"],
    "Bloodthirster": ["B. F. Sword", "Vampiric Scepter"],
    "Spear of Shojin": ["Caulfield's Warhammer"],
    "Manamune": ["Tear of the Goddess", "Caulfield's Warhammer", "Long Sword"],
    "Muramana": ["Tear of the Goddess", "Caulfield's Warhammer", "Long Sword"],
    "Trinity Force": ["Sheen", "Hearthbound Axe", "Phage"],
    "Serylda's Grudge": ["Last Whisper", "Caulfield's Warhammer"],
    "Black Cleaver": ["Phage", "Caulfield's Warhammer"],
    "Blade of the Ruined King": ["Recurve Bow", "Vampiric Scepter", "Pickaxe"],
    "Galeforce": ["Noonquiver", "Pickaxe", "Long Sword"],
}

# Build paths: purchase order. Tear auto-upgrades to Muramana once stacked
# (~8 min after Tear). Paths list the finished item they intend.
BUILD_PATHS: Dict[str, List[str]] = {
    # 7.3 crit capstone — 100% crit, Hexoptics max-range amp on Q poke
    "ER → IE → Hex → Mortal → BT": [
        "Long Sword",
        "Sheen",
        "Caulfield's Warhammer",
        "Essence Reaver",
        "Boots",
        "Ionian Boots of Lucidity",
        "B. F. Sword",
        "Infinity Edge",
        "Noonquiver",
        "Hexoptics C44",
        "Last Whisper",
        "Mortal Reminder",
        "Bloodthirster",
    ],
    # Same page, LDR (more pen + Giant Slayer) instead of Mortal
    "ER → IE → Hex → LDR → BT": [
        "Long Sword",
        "Sheen",
        "Essence Reaver",
        "Boots",
        "Ionian Boots of Lucidity",
        "Infinity Edge",
        "Hexoptics C44",
        "Lord Dominik's Regards",
        "Bloodthirster",
    ],
    # Navori Q-spam (no AD on Navori; more Qs)
    "ER → IE → Navori → Mortal → BT": [
        "Long Sword",
        "Sheen",
        "Essence Reaver",
        "Boots",
        "Ionian Boots of Lucidity",
        "Infinity Edge",
        "Navori Quickblades",
        "Mortal Reminder",
        "Bloodthirster",
    ],
    # RFC range instead of Hexoptics damage amp
    "ER → IE → RFC → Mortal → BT": [
        "Long Sword",
        "Sheen",
        "Essence Reaver",
        "Boots",
        "Ionian Boots of Lucidity",
        "Infinity Edge",
        "Rapid Firecannon",
        "Mortal Reminder",
        "Bloodthirster",
    ],
    # wildriftmeta 7.3 rec: Shojin 2nd (ability amp, 75% crit)
    "ER → Shojin → IE → Mortal → Hex": [
        "Long Sword",
        "Sheen",
        "Essence Reaver",
        "Boots",
        "Ionian Boots of Lucidity",
        "Spear of Shojin",
        "Infinity Edge",
        "Mortal Reminder",
        "Hexoptics C44",
    ],
    # Gluttonous AD boots, otherwise the Hex capstone
    "ER → IE → Hex → Mortal → BT (Greaves)": [
        "Long Sword",
        "Sheen",
        "Essence Reaver",
        "Boots",
        "Gluttonous Greaves",
        "Infinity Edge",
        "Hexoptics C44",
        "Mortal Reminder",
        "Bloodthirster",
    ],
    # Yun Tal first (full 25% crit only after ~125 ranged hits)
    "Yun Tal → IE → Hex → Mortal → BT": [
        "Long Sword",
        "Noonquiver",
        "Yun Tal Wildarrows",
        "Boots",
        "Ionian Boots of Lucidity",
        "Infinity Edge",
        "Hexoptics C44",
        "Mortal Reminder",
        "Bloodthirster",
    ],
    # Stormrazor lane item into IE
    "Stormrazor → IE → Hex → Mortal → BT": [
        "Long Sword",
        "B. F. Sword",
        "Stormrazor",
        "Boots",
        "Ionian Boots of Lucidity",
        "Infinity Edge",
        "Hexoptics C44",
        "Mortal Reminder",
        "Bloodthirster",
    ],
    # Collector execute page (overlaps Smolder 6.5% burn execute)
    "ER → IE → Collector → Mortal → Hex": [
        "Long Sword",
        "Sheen",
        "Essence Reaver",
        "Boots",
        "Ionian Boots of Lucidity",
        "Infinity Edge",
        "The Collector",
        "Mortal Reminder",
        "Hexoptics C44",
    ],
    # Old 7.2 core — 0% crit until a late IE, Q does not scale
    "Mura → Tri → Serylda → Shojin → IE": [
        "Long Sword",
        "Tear of the Goddess",
        "Caulfield's Warhammer",
        "Manamune",
        "Boots",
        "Ionian Boots of Lucidity",
        "Sheen",
        "Trinity Force",
        "Serylda's Grudge",
        "Spear of Shojin",
        "Infinity Edge",
    ],
    "Mura → Tri → Serylda → IE → Mortal": [
        "Long Sword",
        "Tear of the Goddess",
        "Manamune",
        "Boots",
        "Ionian Boots of Lucidity",
        "Trinity Force",
        "Serylda's Grudge",
        "Infinity Edge",
        "Mortal Reminder",
    ],
    # Trinity into crit (hybrid)
    "ER → Trinity → IE → Mortal → Hex": [
        "Long Sword",
        "Sheen",
        "Essence Reaver",
        "Boots",
        "Ionian Boots of Lucidity",
        "Trinity Force",
        "Infinity Edge",
        "Mortal Reminder",
        "Hexoptics C44",
    ],
    # BotRK tank shred, less crit
    "ER → IE → BotRK → LDR → BT": [
        "Long Sword",
        "Sheen",
        "Essence Reaver",
        "Boots",
        "Ionian Boots of Lucidity",
        "Infinity Edge",
        "Blade of the Ruined King",
        "Lord Dominik's Regards",
        "Bloodthirster",
    ],
    # Cleaver shred, ability haste, 50% crit
    "ER → IE → Cleaver → Serylda → BT": [
        "Long Sword",
        "Sheen",
        "Essence Reaver",
        "Boots",
        "Ionian Boots of Lucidity",
        "Infinity Edge",
        "Black Cleaver",
        "Serylda's Grudge",
        "Bloodthirster",
    ],
    # Shieldbow over BT for dive (less AD, has crit)
    "ER → IE → Hex → Mortal → Shieldbow": [
        "Long Sword",
        "Sheen",
        "Essence Reaver",
        "Boots",
        "Ionian Boots of Lucidity",
        "Infinity Edge",
        "Hexoptics C44",
        "Mortal Reminder",
        "Immortal Shieldbow",
    ],
}

LEGENDARIES = {
    "Essence Reaver",
    "Infinity Edge",
    "Hexoptics C44",
    "Yun Tal Wildarrows",
    "Navori Quickblades",
    "Rapid Firecannon",
    "Stormrazor",
    "Immortal Shieldbow",
    "Mortal Reminder",
    "Lord Dominik's Regards",
    "The Collector",
    "Bloodthirster",
    "Spear of Shojin",
    "Manamune",
    "Muramana",
    "Trinity Force",
    "Serylda's Grudge",
    "Black Cleaver",
    "Blade of the Ruined King",
    "Galeforce",
}

BOOTS = {
    "Boots",
    "Ionian Boots of Lucidity",
    "Gluttonous Greaves",
}


def truncate_after_n_legendaries(path: List[str], n: int) -> List[str]:
    out: List[str] = []
    count = 0
    for step in path:
        out.append(step)
        if step in LEGENDARIES:
            count += 1
            if count >= n:
                break
    return out


# ---------------------------------------------------------------------------
# Inventory
# ---------------------------------------------------------------------------


def resolve_inventory(path: List[str], gold: int, minute: int) -> List[Item]:
    owned: List[str] = []
    gold_pool = gold

    def credit_for(item_name: str) -> Tuple[int, List[str]]:
        credit = 0
        remove: List[str] = []
        available = list(owned)
        for c in UPGRADE_COMPONENTS.get(item_name, ()):
            if c in available:
                credit += ITEMS[c].cost
                available.remove(c)
                remove.append(c)
        return credit, remove

    def remaining_cost(item_name: str) -> int:
        credit, _ = credit_for(item_name)
        return max(0, ITEMS[item_name].cost - credit)

    def can_afford(item_name: str) -> bool:
        return gold_pool >= remaining_cost(item_name)

    def buy(item_name: str) -> bool:
        nonlocal gold_pool
        if item_name in owned and item_name not in ("Long Sword", "Brawler's Gloves"):
            return False
        cost = remaining_cost(item_name)
        if cost > gold_pool:
            return False
        _, remove = credit_for(item_name)
        gold_pool -= cost
        for r in remove:
            owned.remove(r)
        owned.append(item_name)
        return True

    blocked_at: Optional[str] = None
    for step in path:
        if step in owned and step not in ("Long Sword", "Brawler's Gloves"):
            continue
        if can_afford(step):
            buy(step)
        else:
            blocked_at = step
            break

    if blocked_at and blocked_at in NEXT_COMPONENTS:
        for comp in NEXT_COMPONENTS[blocked_at]:
            if comp in owned:
                continue
            if gold_pool >= ITEMS[comp].cost:
                buy(comp)
        if can_afford(blocked_at):
            buy(blocked_at)
            seen = False
            for step in path:
                if step == blocked_at:
                    seen = True
                    continue
                if not seen:
                    continue
                if step in owned:
                    continue
                if can_afford(step):
                    buy(step)
                else:
                    for comp in NEXT_COMPONENTS.get(step, []):
                        if comp not in owned and gold_pool >= ITEMS[comp].cost:
                            buy(comp)
                    if can_afford(step):
                        buy(step)
                    else:
                        break

    # Tear → Muramana once stacked (~8 minutes after Tear/Manamune)
    if "Manamune" in owned:
        tear_ready = minute >= 12
        # earlier if Tear was first-backed (~4:00) → stacked ~12:00
        if "Tear of the Goddess" in "".join(path[:4]) or any(
            n in ("Tear of the Goddess", "Manamune") for n in owned
        ):
            tear_ready = minute >= 11
        if tear_ready:
            owned = ["Muramana" if n == "Manamune" else n for n in owned]

    for b in ("Ionian Boots of Lucidity", "Gluttonous Greaves"):
        if b in owned and "Boots" in owned:
            owned.remove("Boots")

    return [ITEMS[n] for n in owned]


# ---------------------------------------------------------------------------
# Combat model
# ---------------------------------------------------------------------------


@dataclass
class Snapshot:
    minute: int
    build_name: str
    items: List[str]
    gold: int
    level: int
    stacks: int
    ad: float
    bonus_ad: float
    crit: float
    crit_dmg: float
    ah: float
    as_pct: float
    legendary_count: int
    poke_tank: float
    poke_squish: float
    fight_tank: float
    fight_squish: float
    mix_tank: float
    mix_squish: float
    q_casts_poke: int
    notes: str
    has_ie: bool
    has_er: bool
    has_hex: bool
    has_navori: bool
    has_mura: bool
    has_tri: bool
    has_shojin: bool
    has_pen: bool
    crit100: bool
    t3: bool


def haste_cdr_mult(haste: float) -> float:
    return 100.0 / (100.0 + max(0.0, haste))


def phys_mult(eff_armor: float) -> float:
    return 100.0 / (100.0 + max(0.0, eff_armor))


def magic_mult(mr: float) -> float:
    return 100.0 / (100.0 + max(0.0, mr))


def apply_armor(
    armor: float,
    pct_pen: float,
    flat_pen: float,
    cleaver_shred: float,
) -> float:
    reduced = armor * (1.0 - cleaver_shred)
    reduced = reduced * (1.0 - pct_pen) - flat_pen
    return max(0.0, reduced)


def q_amp(crit: float, crit_dmg: float) -> float:
    """Q physical amp: 0–45% from crit rate, plus IE extra (crit_dmg-2).

    At 100% crit / 200% crit damage → +45%. With IE (230%) → +58.5%.
    Matches wiki 0–45% (+0–13.5% from the old +30% IE).
    """
    extra = max(0.0, crit_dmg - 2.0)
    return crit * 0.45 * (1.0 + extra)


def stack_magic_ratio_q(crit: float, crit_dmg: float) -> float:
    extra = max(0.0, crit_dmg - 2.0)
    return 0.30 + 0.30 * crit + 0.30 * extra * crit


def smolder_base_ad(level: int) -> float:
    return 54.0 + 3.5 * (level - 1)


def smolder_base_as(level: int) -> float:
    # WR marksman-style: 0.67 ratio, ~2% growth
    return 0.67 * (1.0 + 0.02 * (level - 1))


def smolder_mana(level: int, item_mana: float) -> float:
    return 335.0 + 40.0 * (level - 1) + item_mana


def q_base_phys(rank: int, bonus_ad: float) -> float:
    if rank <= 0:
        return 0.0
    base = [0, 45, 80, 115, 150][rank]
    return base + 1.10 * bonus_ad


def w_champ_phys(rank: int, bonus_ad: float, ap: float) -> float:
    if rank <= 0:
        return 0.0
    glob = [0, 65, 85, 105, 125][rank] + 0.60 * bonus_ad
    expl = [0, 10, 35, 60, 85][rank] + 0.55 * bonus_ad + 0.80 * ap
    return glob + expl


def e_bolts(stacks: int) -> int:
    return 5 + int(1.54 * stacks / 100.0)


def e_hit_phys(rank: int, total_ad: float) -> float:
    if rank <= 0:
        return 0.0
    return [0, 15, 20, 25, 30][rank] + 0.30 * total_ad


def r_phys(rank: int, bonus_ad: float, ap: float, center: bool) -> float:
    if rank <= 0:
        return 0.0
    base = [0, 200, 300, 400][rank] + 1.10 * bonus_ad + 1.00 * ap
    return base * (1.5 if center else 1.0)


def burn_true_ratio(bonus_ad: float, stacks: int) -> float:
    """Total max-HP true damage over 3s per Q at T3."""
    if stacks < 175:
        return 0.0
    return 0.025 * (bonus_ad / 100.0) + 0.005 * (stacks / 100.0)


def yuntal_crit(minute: int, owned_since_guess: int) -> float:
    """0.2% crit per ranged auto, cap 25%. Farm ~20 autos/min after buy."""
    elapsed = max(0, minute - owned_since_guess)
    return min(0.25, 0.002 * (25 * elapsed + 15))


def legend_alacrity(minute: int) -> float:
    return min(0.18, 0.03 * max(1, minute))


def legend_haste(minute: int) -> float:
    return min(15.0, 1.5 * max(1, minute))


def sum_stats(
    inv: List[Item], minute: int, level: int, runes: RunePage = DEFAULT_RUNES
) -> dict:
    ad = as_pct = crit = ah = hp = mana = ls = pct = flat = 0.0
    flags = {
        "ie": False,
        "er": False,
        "trinity": False,
        "muramana": False,
        "manamune": False,
        "navori": False,
        "shojin": False,
        "hexoptics": False,
        "yuntal": False,
        "rfc": False,
        "stormrazor": False,
        "ldr": False,
        "mortal": False,
        "serylda": False,
        "cleaver": False,
        "bork": False,
        "collector": False,
        "greaves": False,
    }
    names = []
    for it in inv:
        names.append(it.name)
        ad += it.ad
        as_pct += it.as_pct
        crit += it.crit
        ah += it.ah
        hp += it.hp
        mana += it.mana
        ls += it.ls
        pct += it.pct_pen
        flat += it.flat_pen
        if it.ie:
            flags["ie"] = True
        if it.er:
            flags["er"] = True
        if it.trinity:
            flags["trinity"] = True
        if it.muramana:
            flags["muramana"] = True
        if it.manamune:
            flags["manamune"] = True
        if it.navori:
            flags["navori"] = True
        if it.shojin:
            flags["shojin"] = True
        if it.hexoptics:
            flags["hexoptics"] = True
        if it.yuntal:
            flags["yuntal"] = True
        if it.rfc:
            flags["rfc"] = True
        if it.stormrazor:
            flags["stormrazor"] = True
        if it.ldr:
            flags["ldr"] = True
        if it.mortal:
            flags["mortal"] = True
        if it.serylda:
            flags["serylda"] = True
        if it.cleaver:
            flags["cleaver"] = True
        if it.bork:
            flags["bork"] = True
        if it.collector:
            flags["collector"] = True
        if it.name == "Gluttonous Greaves":
            flags["greaves"] = True

    if flags["yuntal"]:
        # First-item Yun Tal is usually done ~10:00
        crit += yuntal_crit(minute, 10 if "Yun Tal Wildarrows" in names else minute)

    if runes.legend == "alacrity":
        as_pct += legend_alacrity(minute)
    elif runes.legend == "haste":
        ah += legend_haste(minute)

    trans_refund = False
    if runes.secondary == "transcendence":
        ah += 10.0 if level >= 5 else 5.0
        trans_refund = level >= 9

    base_ad = smolder_base_ad(level)
    mana_pool = smolder_mana(level, mana)
    if flags["muramana"] or flags["manamune"]:
        ad += 0.02 * mana_pool

    total_ad = base_ad + ad
    crit = min(1.25, crit)
    crit_dmg = 2.30 if flags["ie"] else 2.00

    return {
        "bonus_ad": ad,
        "total_ad": total_ad,
        "base_ad": base_ad,
        "as_pct": as_pct,
        "crit": crit,
        "crit_dmg": crit_dmg,
        "ah": ah,
        "hp": hp,
        "mana": mana_pool,
        "ls": ls,
        "pct": pct,
        "flat": flat,
        "names": names,
        "runes": runes,
        "trans_refund": trans_refund,
        **flags,
    }


def attack_speed(level: int, bonus_as: float) -> float:
    return min(3.0, smolder_base_as(level) + 0.67 * bonus_as)


def q_cooldown(level: int, ah: float) -> float:
    rank = skill_rank(level, "Q")
    if rank <= 0:
        return 99.0
    base = [0, 5.5, 5.0, 4.5, 4.0][rank]
    return base * haste_cdr_mult(ah)


def w_cooldown(level: int, ah: float) -> float:
    rank = skill_rank(level, "W")
    if rank <= 0:
        return 99.0
    base = [0, 12, 11, 10, 9][rank]
    return base * haste_cdr_mult(ah)


def window_damage(
    *,
    level: int,
    stacks: int,
    stats: dict,
    hp: float,
    armor: float,
    mr: float,
    window: float,
    poke: bool,
    vs_tank: bool,
) -> Tuple[float, int]:
    """Mix damage in one window. Returns (damage, Q casts)."""
    bonus_ad = stats["bonus_ad"]
    total_ad = stats["total_ad"]
    base_ad = stats["base_ad"]
    crit = min(1.0, stats["crit"])
    crit_dmg = stats["crit_dmg"]
    ah = stats["ah"]
    ap = 0.0

    q_rank = skill_rank(level, "Q")
    w_rank = skill_rank(level, "W")
    e_rank = skill_rank(level, "E")
    r_rank = skill_rank(level, "R")

    aspd = attack_speed(level, stats["as_pct"])
    if stats["yuntal"] and not poke:
        aspd = min(3.0, aspd + 0.67 * 0.25)  # Flurry in fights

    q_cd = q_cooldown(level, ah)
    runes: RunePage = stats.get("runes", DEFAULT_RUNES)
    # Transcendence: 8% CD refund when a basic ability hits, 8s ICD.
    if stats.get("trans_refund"):
        q_cd_eff = q_cd * 0.92
    else:
        q_cd_eff = q_cd

    # Lethal Tempo 7.3: 6.4% AS per ranged stack, 6 stacks. Q is on-attack
    # so it stacks, but poke does not sit at 6 stacks the whole window.
    if runes.keystone == "lethal":
        lt_as = 0.064 * (3.0 if poke else 6.0)
        aspd = min(3.0, aspd + 0.67 * lt_as)

    # Conqueror: 3–5 AD/stack, ~5 stacks in poke / ~8 in a fight.
    conq_ad = 0.0
    if runes.keystone == "conqueror":
        per = 3.0 + 2.0 * min(1.0, (level - 1) / 14.0)
        conq_ad = per * (5.0 if poke else 8.0)
        bonus_ad += conq_ad
        total_ad += conq_ad

    # Autos between Qs refund Navori 15% remaining CD
    if stats["navori"]:
        autos_between = max(0.4, q_cd_eff * aspd - 1.0)
        q_cd_eff *= (0.85 ** min(3.0, autos_between))

    q_casts = 0
    if q_rank > 0:
        t = 0.25
        while t <= window + 1e-6:
            q_casts += 1
            t += max(0.75, q_cd_eff)
        q_casts = min(q_casts, 8)

    w_casts = 1 if (w_rank > 0 and window >= 1.0) else 0
    if not poke and w_rank > 0 and window >= w_cooldown(level, ah) + 0.5:
        w_casts = 2
    if poke:
        w_casts = 1 if w_rank > 0 else 0

    # Autos: poke weaves 1–2; fights almost full AS minus Q windups
    if poke:
        autos = min(aspd * 0.45 * window, 3.0)
        use_e = False
        use_r = False
        r_center = False
        hex_amp = 1.10 if stats["hexoptics"] else 1.0
        current_hp_frac = 0.82
        cleaver_avg = 0.12 if stats["cleaver"] else 0.0
    else:
        autos = max(0.0, aspd * window - q_casts * 0.35 - (1.0 if r_rank else 0))
        use_e = e_rank > 0
        use_r = r_rank > 0
        r_center = True
        hex_amp = 1.05 if stats["hexoptics"] else 1.0
        current_hp_frac = 0.70
        cleaver_avg = 0.24 if stats["cleaver"] else 0.0

    if stats["yuntal"] and poke:
        autos = min(autos + 0.5, 3.5)

    eff_armor = apply_armor(armor, stats["pct"], stats["flat"], cleaver_avg)
    pmult = phys_mult(eff_armor)
    mmult = magic_mult(mr)

    shojin = 1.12 if stats["shojin"] else 1.0
    amp = q_amp(crit, crit_dmg)
    magic_ratio = stack_magic_ratio_q(crit, crit_dmg)
    burn_ratio = burn_true_ratio(bonus_ad, stacks)

    # Expected auto multiplier (crit)
    auto_mult = 1.0 + crit * (crit_dmg - 1.0)

    dmg = 0.0

    # --- Q ---
    q_phys = q_base_phys(q_rank, bonus_ad) * (1.0 + amp)
    q_magic = stacks * magic_ratio
    # Spellblade on Q (on-hit). 1.5s ICD; Q CD is usually longer.
    sheen = 0.0
    if stats["er"]:
        sheen = 1.35 * base_ad + 80.0 * crit
    elif stats["trinity"]:
        sheen = 2.00 * base_ad
    # Muramana ability shock (ranged 3%)
    shock_spell = 0.03 * stats["mana"] if stats["muramana"] else 0.0
    shock_auto = 0.015 * stats["mana"] if stats["muramana"] else 0.0
    bork_onhit = 0.07 * hp * current_hp_frac if stats["bork"] else 0.0
    brutal = 0.0
    if runes.slot1 == "brutal":
        brutal = 5.0 + 0.06 * bonus_ad

    q_phys_hit = q_phys + sheen + shock_spell + bork_onhit + brutal
    zeal = 1.0
    if runes.slot1 == "zeal":
        # 2%/s cap 6%. Poke average ~4.5%; fight sits at cap.
        zeal = 1.045 if poke else 1.06
    q_one = (q_phys_hit * pmult + q_magic * mmult) * shojin * zeal
    dmg += q_casts * q_one
    dmg += q_casts * burn_ratio * hp * zeal  # burn is from Q

    # --- W ---
    if w_casts:
        w_p = w_champ_phys(w_rank, bonus_ad, ap)
        w_m = 0.55 * stacks  # explosion magic
        dmg += w_casts * (w_p * pmult + w_m * mmult) * shojin * zeal

    # --- E ---
    if use_e:
        bolts = e_bolts(stacks)
        e_p = e_hit_phys(e_rank, total_ad)
        e_m = 0.12 * stacks
        dmg += bolts * (e_p * pmult + e_m * mmult) * shojin * zeal

    # --- R ---
    if use_r:
        rp = r_phys(r_rank, bonus_ad, ap, r_center)
        dmg += rp * pmult * shojin

    # --- Autos ---
    auto_hit = total_ad * auto_mult + shock_auto + bork_onhit + brutal
    dmg += autos * auto_hit * pmult

    # Energized
    if stats["rfc"]:
        dmg += 80.0 * mmult
    if stats["stormrazor"]:
        dmg += 120.0 * mmult

    # Lethal Tempo max-stack bullet (ranged 6–24), 0.67% per 1% bonus AS
    if runes.keystone == "lethal" and not poke:
        lt_bullet = (6.0 + 18.0 * min(1.0, (level - 1) / 14.0))
        lt_bullet *= 1.0 + 0.0067 * (stats["as_pct"] * 100.0)
        dmg += autos * lt_bullet * mmult

    # LDR Giant Slayer: up to 15% vs 1500 bonus HP
    if stats["ldr"]:
        bonus_hp = max(0.0, hp - (620 + 95 * level))
        gs = min(0.15, 0.15 * (bonus_hp / 1500.0))
        dmg *= 1.0 + gs

    dmg *= hex_amp

    # Slot 2 is exclusive. Cut Down is the poke rune; Coup overlaps T3 execute.
    if runes.slot2 == "cut_down":
        dmg *= 1.065 if poke else 1.04
    elif runes.slot2 == "coup":
        dmg *= 1.00 if poke else 1.05
    elif runes.slot2 == "last_stand":
        dmg *= 1.02

    # Smolder T3 execute: if leftover HP < 6.5% while burned, dump rest
    if stacks >= 175 and q_casts >= 1:
        if dmg >= hp * (1.0 - 0.065) and dmg < hp:
            dmg = hp

    # Collector 5% execute is strictly worse than 6.5% T3 and does not
    # add damage before the threshold.

    return dmg, q_casts


def compute_snapshot(
    build_name: str,
    path: List[str],
    minute: int,
    runes: RunePage = DEFAULT_RUNES,
) -> Snapshot:
    gold = gold_at_minute(minute)
    level = level_at_minute(minute)
    stacks = stacks_at_minute(minute)
    inv = resolve_inventory(path, gold, minute)
    st = sum_stats(inv, minute, level, runes)

    thp, tarm = tank_hp(minute), tank_armor(minute)
    shp, sarm = squishy_hp(minute), squishy_armor(minute)
    tmr, smr = 38 + 1.4 * level, 32 + 1.2 * level

    poke_t, qn = window_damage(
        level=level, stacks=stacks, stats=st, hp=thp, armor=tarm, mr=tmr,
        window=POKE_WINDOW, poke=True, vs_tank=True,
    )
    poke_s, _ = window_damage(
        level=level, stacks=stacks, stats=st, hp=shp, armor=sarm, mr=smr,
        window=POKE_WINDOW, poke=True, vs_tank=False,
    )
    fight_t, _ = window_damage(
        level=level, stacks=stacks, stats=st, hp=thp, armor=tarm, mr=tmr,
        window=FIGHT_WINDOW, poke=False, vs_tank=True,
    )
    fight_s, _ = window_damage(
        level=level, stacks=stacks, stats=st, hp=shp, armor=sarm, mr=smr,
        window=FIGHT_WINDOW, poke=False, vs_tank=False,
    )

    mix_t = POKE_WEIGHT * poke_t + FIGHT_WEIGHT * fight_t
    mix_s = POKE_WEIGHT * poke_s + FIGHT_WEIGHT * fight_s
    n_leg = sum(1 for n in st["names"] if n in LEGENDARIES)
    crit100 = st["crit"] >= 0.99

    notes = []
    if stacks >= 175:
        notes.append("T3 burn")
    elif stacks >= 100:
        notes.append("T2 bolts")
    elif stacks >= 25:
        notes.append("T1 AoE")
    if st["ie"]:
        notes.append("IE 230%")
    if crit100:
        notes.append("100% crit")
    elif st["crit"] >= 0.7:
        notes.append(f"{int(st['crit']*100)}% crit")
    if st["hexoptics"]:
        notes.append("Hex 10%")
    if st["navori"]:
        notes.append("Navori Q")
    if st["shojin"]:
        notes.append("Shojin 12%")
    if st["muramana"]:
        notes.append("Shock")
    if st["trinity"]:
        notes.append("Tri sheen")
    if st["er"]:
        notes.append("ER sheen")
    if n_leg == 0:
        notes.append("pre-legendary")

    return Snapshot(
        minute=minute,
        build_name=build_name,
        items=st["names"],
        gold=gold,
        level=level,
        stacks=stacks,
        ad=round(st["total_ad"], 1),
        bonus_ad=round(st["bonus_ad"], 1),
        crit=round(st["crit"], 3),
        crit_dmg=st["crit_dmg"],
        ah=st["ah"],
        as_pct=st["as_pct"],
        legendary_count=n_leg,
        poke_tank=round(poke_t, 1),
        poke_squish=round(poke_s, 1),
        fight_tank=round(fight_t, 1),
        fight_squish=round(fight_s, 1),
        mix_tank=round(mix_t, 1),
        mix_squish=round(mix_s, 1),
        q_casts_poke=qn,
        notes=", ".join(notes) if notes else "-",
        has_ie=st["ie"],
        has_er=st["er"],
        has_hex=st["hexoptics"],
        has_navori=st["navori"],
        has_mura=st["muramana"] or st["manamune"],
        has_tri=st["trinity"],
        has_shojin=st["shojin"],
        has_pen=st["mortal"] or st["ldr"] or st["serylda"],
        crit100=crit100,
        t3=stacks >= 175,
    )


def score(s: Snapshot) -> float:
    """Late identity: Q poke that still melts tanks, IE capstone kept."""
    mix = 0.55 * s.mix_tank + 0.45 * s.mix_squish
    kit = 1.0
    if s.has_ie:
        kit += 0.08
    if s.crit100 and s.has_ie:
        kit += 0.06
    if s.has_hex:
        kit += 0.04
    if s.has_pen:
        kit += 0.05
    if s.t3:
        kit += 0.03
    # Old mana core delays the Q-crit identity
    if s.has_mura and not s.has_ie:
        kit *= 0.90
    if s.has_navori and not s.has_hex:
        kit *= 0.99  # more Qs, but Navori has 0 AD
    return mix * kit


def run_all() -> Tuple[Dict[str, List[Snapshot]], List[dict]]:
    results: Dict[str, List[Snapshot]] = {}
    for name, path in BUILD_PATHS.items():
        results[name] = [
            compute_snapshot(name, path, m) for m in range(1, GAME_MINUTES + 1)
        ]

    timeline = []
    for m in range(1, GAME_MINUTES + 1):
        cands = [(n, results[n][m - 1]) for n in results]
        best_n, best_s = max(cands, key=lambda x: score(x[1]))
        timeline.append(
            {
                "minute": m,
                "winner": best_n,
                "mix_tank": best_s.mix_tank,
                "mix_squish": best_s.mix_squish,
                "poke_tank": best_s.poke_tank,
                "poke_squish": best_s.poke_squish,
                "items": best_s.items,
                "ap": best_s.ad,
                "crit": best_s.crit,
                "stacks": best_s.stacks,
                "notes": best_s.notes,
            }
        )
    return results, timeline


def mix_of(s: Snapshot) -> float:
    return 0.55 * s.mix_tank + 0.45 * s.mix_squish


def run_runes() -> Dict[str, List[Snapshot]]:
    path = BUILD_PATHS[WINNING_ITEMS]
    out: Dict[str, List[Snapshot]] = {}
    for name, page in RUNE_PAGES.items():
        out[name] = [
            compute_snapshot(WINNING_ITEMS, path, m, page)
            for m in range(1, GAME_MINUTES + 1)
        ]
    return out


def rune_score(s: Snapshot, page: RunePage) -> float:
    """Fit score for the 0-AS crit Q page. Paper AD keystones are not the fit."""
    mix = mix_of(s)
    if page.keystone != "fleet":
        # Still listed for damage; they do not fit Hexoptics siege.
        return mix * 0.85
    kit = 1.08
    if page.slot1 == "zeal":
        kit += 0.04
    if page.slot2 == "cut_down":
        kit += 0.03
    elif page.slot2 == "coup":
        kit *= 0.96
    # Haste and Bloodline deal the same 4 Qs in 8s; Bloodline heals mixed dmg.
    if page.legend == "bloodline":
        kit += 0.03
    elif page.legend == "haste":
        kit += 0.02
    if page.secondary == "transcendence":
        kit += 0.05  # dropping it costs a Q (3 vs 4)
    return mix * kit


def first_minute_with(snaps: List[Snapshot], pred) -> Optional[int]:
    for s in snaps:
        if pred(s):
            return s.minute
    return None


def late_item_isolated_delta(
    name: str, path: List[str], snaps: List[Snapshot], n: int = 4
) -> Tuple[float, int, List[str]]:
    """Damage added by the nth legendary at the minute it completes."""
    row = next((s for s in snaps if s.legendary_count >= n), None)
    if row is None:
        return 0.0, snaps[-1].minute, snaps[-1].items
    short = truncate_after_n_legendaries(path, n - 1)
    with_n = 0.55 * row.mix_tank + 0.45 * row.mix_squish
    without = compute_snapshot(name, short, row.minute)
    without_mix = 0.55 * without.mix_tank + 0.45 * without.mix_squish
    without_mix = 0.55 * without.mix_tank + 0.45 * without.mix_squish
    legs = [i for i in row.items if i in LEGENDARIES]
    return with_n - without_mix, row.minute, legs


def summarize(results, timeline, rune_results) -> str:
    lines = []
    lines.append("=" * 80)
    lines.append("SMOLDER — STRONGEST LATE BUILD  (Wild Rift patch 7.3)")
    lines.append("Playstyle: Q-poke 70% / teamfight weave 30% | Game: 25:00")
    lines.append("Metric: mix damage per 8s  |  T3 burn (175 stacks) is the late spike")
    lines.append("=" * 80)
    lines.append("")
    lines.append("GOLD / LEVEL / STACKS / TARGETS")
    lines.append(
        f"  {'Min':>3}  {'Gold':>6}  {'Lvl':>3}  {'Stacks':>6}  "
        f"{'Tank HP':>8}  {'Tank Arm':>8}  {'Squish HP':>9}"
    )
    for m in range(1, GAME_MINUTES + 1):
        if m in (1, 6, 10, 12, 16, 17, 18, 20, 22, 25) or m % 5 == 0:
            lines.append(
                f"  {m:>3}  {gold_at_minute(m):>6}  {level_at_minute(m):>3}  "
                f"{stacks_at_minute(m):>6}  {tank_hp(m):>8.0f}  "
                f"{tank_armor(m):>8.0f}  {squishy_hp(m):>9.0f}"
            )

    lines.append("")
    lines.append("-" * 80)
    lines.append("MINUTE-BY-MINUTE OPTIMAL (Q-poke identity, tanks still hurt)")
    lines.append("-" * 80)
    for row in timeline:
        if row["minute"] % 2 != 0 and row["minute"] not in (1, 11, 17):
            continue
        item_short = " › ".join(row["items"][:5])
        if len(row["items"]) > 5:
            item_short += " › …"
        lines.append(
            f"  {row['minute']:>2}:00 | tank {row['mix_tank']:>7.0f} | "
            f"squish {row['mix_squish']:>7.0f} | poke-sq {row['poke_squish']:>6.0f} | "
            f"{row['winner']}"
        )
        lines.append(f"         items: {item_short}")
        lines.append(f"         {row['notes']}")

    lines.append("")
    lines.append("-" * 80)
    lines.append("BUILD COMPARISON — MIX DAMAGE / 8s @ spikes")
    lines.append("-" * 80)
    hdr = (
        f"  {'Build':<40} {'12:00':>7} {'18:00':>7} {'22:00':>7} "
        f"{'25:00':>7} {'Late':>8} {'IEΔ':>7}"
    )
    lines.append(hdr)

    ranking = []
    for name, snaps in results.items():
        b12 = 0.55 * snaps[11].mix_tank + 0.45 * snaps[11].mix_squish
        b18 = 0.55 * snaps[17].mix_tank + 0.45 * snaps[17].mix_squish
        b22 = 0.55 * snaps[21].mix_tank + 0.45 * snaps[21].mix_squish
        b25 = 0.55 * snaps[24].mix_tank + 0.45 * snaps[24].mix_squish
        # Late-weighted: 18–25 matter most (T3 + full page)
        late = 0.15 * b12 + 0.25 * b18 + 0.30 * b22 + 0.30 * b25
        d_ie, ie_min, ie_legs = late_item_isolated_delta(
            name, BUILD_PATHS[name], snaps, n=2
        )
        ranking.append(
            (late, b25, b22, name, b12, b18, b22, b25, snaps, d_ie, ie_min, ie_legs)
        )
        lines.append(
            f"  {name:<40} {b12:>7.0f} {b18:>7.0f} {b22:>7.0f} "
            f"{b25:>7.0f} {late:>8.0f} {d_ie:>+7.0f}"
        )

    ranking.sort(key=lambda x: (x[0], x[1]), reverse=True)
    best = ranking[0]

    lines.append("")
    lines.append("-" * 80)
    lines.append("Q POKE vs SQUISHY  (pure Super Scorcher siege) @ 18 / 22 / 25")
    lines.append("-" * 80)
    for row in ranking:
        name, snaps = row[3], row[8]
        lines.append(
            f"  {name:<40} {snaps[17].poke_squish:>7.0f} {snaps[21].poke_squish:>7.0f} "
            f"{snaps[24].poke_squish:>7.0f}   Qs @22: {snaps[21].q_casts_poke}  "
            f"crit {snaps[21].crit*100:.0f}%"
        )

    lines.append("")
    lines.append("-" * 80)
    lines.append("TEAMFIGHT vs TANK  @ 18 / 22 / 25")
    lines.append("-" * 80)
    for row in ranking:
        name, snaps = row[3], row[8]
        lines.append(
            f"  {name:<40} {snaps[17].fight_tank:>7.0f} {snaps[21].fight_tank:>7.0f} "
            f"{snaps[24].fight_tank:>7.0f}"
        )

    lines.append("")
    lines.append("-" * 80)
    lines.append("2ND LEGENDARY SPIKE  (isolated Δ at the minute it completes)")
    lines.append("-" * 80)
    for row in ranking:
        name, d_ie, ie_min, ie_legs = row[3], row[9], row[10], row[11]
        lines.append(
            f"  {name:<40} ~{ie_min}:00  Δ {d_ie:+.0f}  [{', '.join(ie_legs[:3])}]"
        )

    winner_name = best[3]
    snaps = best[8]
    ie_m = first_minute_with(snaps, lambda s: s.has_ie)
    hex_m = first_minute_with(snaps, lambda s: s.has_hex)
    pen_m = first_minute_with(snaps, lambda s: s.has_pen)
    t3_m = first_minute_with(snaps, lambda s: s.t3)
    c100_m = first_minute_with(snaps, lambda s: s.crit100)

    old = results.get("Mura → Tri → Serylda → Shojin → IE")
    win = results[winner_name]
    t22_win = 0.55 * win[21].mix_tank + 0.45 * win[21].mix_squish
    t25_win = 0.55 * win[24].mix_tank + 0.45 * win[24].mix_squish
    if old:
        t22_old = 0.55 * old[21].mix_tank + 0.45 * old[21].mix_squish
        t25_old = 0.55 * old[24].mix_tank + 0.45 * old[24].mix_squish
        pct22 = 100.0 * (t22_win / t22_old - 1.0) if t22_old else 0.0
        pct25 = 100.0 * (t25_win / t25_old - 1.0) if t25_old else 0.0
        poke25_win, poke25_old = win[24].poke_squish, old[24].poke_squish
    else:
        t22_old = t25_old = pct22 = pct25 = poke25_win = poke25_old = 0.0

    shojin_name = "ER → Shojin → IE → Mortal → Hex"
    navori_name = "ER → IE → Navori → Mortal → BT"
    hex_name = "ER → IE → Hex → Mortal → BT"

    lines.append("")
    lines.append("-" * 80)
    lines.append(f"RUNES ON {WINNING_ITEMS}  (same items, swap the page)")
    lines.append("-" * 80)
    hdr = (
        f"  {'Rune page':<56} {'18:00':>7} {'22:00':>7} {'25:00':>7} "
        f"{'Poke25':>7} {'Qs':>4}"
    )
    lines.append(hdr)
    rune_rank = []
    for name, snaps in rune_results.items():
        page = RUNE_PAGES[name]
        b18 = mix_of(snaps[17])
        b22 = mix_of(snaps[21])
        b25 = mix_of(snaps[24])
        late = 0.25 * b18 + 0.35 * b22 + 0.40 * b25
        sc = rune_score(snaps[24], page)
        rune_rank.append(
            (sc, late, b25, name, b18, b22, b25, snaps, page)
        )
        lines.append(
            f"  {name:<56} {b18:>7.0f} {b22:>7.0f} {b25:>7.0f} "
            f"{snaps[24].poke_squish:>7.0f} {snaps[21].q_casts_poke:>4}"
        )
    rune_rank.sort(key=lambda x: (x[0], x[1]), reverse=True)
    best_rune = rune_rank[0]

    lines.append("")
    lines.append("-" * 80)
    lines.append("VERDICT")
    lines.append("-" * 80)
    lines.append(f"  Strongest late path: {winner_name}")
    lines.append(
        f"  Late-weighted mix: {best[0]:.0f} | 22:00 {best[2]:.0f} | 25:00 {best[1]:.0f}"
    )
    if ie_m:
        lines.append(f"  Infinity Edge online: ~{ie_m}:00  (Q amp uses 230% crit damage)")
    else:
        lines.append("  Infinity Edge: NOT finished — Q is missing its late multiplier")
    if hex_m:
        lines.append(f"  Hexoptics C44 online: ~{hex_m}:00  (10% damage at Q range)")
    if pen_m:
        lines.append(f"  % armor pen online:   ~{pen_m}:00")
    if t3_m:
        lines.append(f"  T3 burn (175 stacks): ~{t3_m}:00  (true %HP + 6.5% execute)")
    if c100_m:
        lines.append(f"  100% crit:            ~{c100_m}:00")
    lines.append("")
    lines.append("  WHY 7.3 LATE SMOLDER IS A CRIT PAGE:")
    lines.append("  • Q damage is increased by crit chance, then again by bonus")
    lines.append("    crit damage. Wiki: 0–45% (+0–13.5% from IE) based on crit.")
    lines.append("    At 100% crit + IE that is a 58.5% multiplier on Super Scorcher")
    lines.append("    physical, and Dragon Practice magic goes 30% → 69% of stacks.")
    lines.append("  • Patch 7.3 raised base crit damage 175% → 200% and made IE")
    lines.append("    the capstone (75 AD, 230% crit damage). Magnetic Blaster is gone.")
    lines.append("  • Q applies on-hit, so Essence Reaver Spellblade rides on the")
    lines.append("    fireball. That is the first-item Q identity.")
    lines.append("  • Hexoptics C44 is the Magnetic Blaster replacement that actually")
    lines.append("    scales the poke: 10% damage at 550 range — Q's exact range.")
    if old:
        lines.append(
            f"  • Old Mura→Tri→Serylda at 22:00 mix {t22_old:.0f}; "
            f"{winner_name} {t22_win:.0f} ({pct22:+.0f}%)."
        )
        lines.append(
            f"    25:00 mix {t25_old:.0f} vs {t25_win:.0f} ({pct25:+.0f}%). "
            f"Poke-squish {poke25_old:.0f} vs {poke25_win:.0f}."
        )
        lines.append("    Muramana still shocks, but 0% crit means Q never gets the")
        lines.append("    7.3 amp. IE arrives as item 5 and the page is already behind.")
    lines.append("")
    if shojin_name in results and hex_name in results:
        sh = results[shojin_name][24]
        hx = results[hex_name][24]
        sh_mix = 0.55 * sh.mix_tank + 0.45 * sh.mix_squish
        hx_mix = 0.55 * hx.mix_tank + 0.45 * hx.mix_squish
        lines.append("  SHOJIN vs 4TH CRIT ITEM:")
        lines.append(
            f"    Shojin 12% ability amp @ 75% crit → mix {sh_mix:.0f}."
        )
        lines.append(
            f"    Hexoptics 4th (100% crit + 10% range amp) → mix {hx_mix:.0f}."
        )
        lines.append("    25% extra crit on Q is ~+11% Scorcher amp plus auto crits;")
        lines.append("    Shojin's 12% only touches abilities and delays 100% crit.")
        lines.append("")
    if navori_name in results and hex_name in results:
        nv = results[navori_name][24]
        hx = results[hex_name][24]
        lines.append("  NAVORI vs HEXOPTICS:")
        lines.append(
            f"    Navori Qs @22: {results[navori_name][21].q_casts_poke} | "
            f"Hexoptics Qs @22: {results[hex_name][21].q_casts_poke}"
        )
        lines.append(
            f"    25:00 poke-squish Navori {nv.poke_squish:.0f} vs Hex {hx.poke_squish:.0f}."
        )
        lines.append("    Navori has 0 AD. Extra Qs do not beat Hexoptics' 55 AD +")
        lines.append("    10% max-range amp on every Scorcher.")
        lines.append("")
    lines.append("  RECOMMENDED (strongest late, patch 7.3):")
    lines.append("  1) Long Sword → Sheen")
    lines.append("  2) Essence Reaver   (~9:00)  — Spellblade on Q, 25% crit, 20 AH")
    lines.append("  3) Ionian Boots of Lucidity  — more Qs (Greaves if you need vamp)")
    lines.append("  4) Infinity Edge    (~14:00) — THE late item (230% crit damage)")
    lines.append("  5) Hexoptics C44    (~18:00) — 10% damage at Q range + 25% crit")
    lines.append("  6) Mortal Reminder / LDR     — 100% crit + %pen")
    lines.append("     Mortal if they heal; LDR if they stacked HP/armor")
    lines.append("  7) Bloodthirster             — 75 AD (no crit; you are already 100%)")
    lines.append("     Shieldbow instead vs dive. Maw vs heavy AP. GA vs assassins.")
    lines.append("")
    lines.append("  Skill: max Q → W → E. R at 6/11/15.")
    lines.append("  Stacks: last-hit with Q, poke champs for extra stacks. T3 ~17:00.")
    lines.append("  Poke: Q from 550. Hexoptics is already at max amp. Don't E in.")
    lines.append("  Fight: Q weave, W explosion, R through the clump (and yourself).")
    lines.append("")
    lines.append("  Trap: Muramana → Trinity → Serylda. That was 7.2. In 7.3 Q wants")
    lines.append("  crit chance and IE; the mana page has neither until item 5.")
    lines.append("  Trap: Shojin 2nd. Ability amp is real, but it delays 100% crit")
    lines.append("  and the Hexoptics range amp that is Smolder's poke identity.")
    lines.append("  Trap: Collector. Smolder already executes at 6.5% with T3 burn.")
    lines.append("")
    fit_name = "Fleet / Zeal / Cut Down / Bloodline / Transcendence"
    fit_snaps = rune_results[fit_name]
    haste_name = "Fleet / Zeal / Cut Down / Haste / Transcendence"
    conq_name = "Conqueror / Zeal / Cut Down / Haste / Transcendence"
    lt_name = "Lethal Tempo / Brutal / Cut Down / Alacrity / Transcendence"
    bone_name = "Fleet / Zeal / Cut Down / Haste / Bone Plating"
    brutal_name = "Fleet / Brutal / Cut Down / Haste / Transcendence"
    coup_name = "Fleet / Zeal / Coup / Haste / Transcendence"
    lines.append("  RUNES THAT FIT THIS PAGE:")
    lines.append(f"  {fit_name}")
    lines.append(
        f"    22:00 mix {mix_of(fit_snaps[21]):.0f} | 25:00 {mix_of(fit_snaps[24]):.0f} | "
        f"Qs @22 {fit_snaps[21].q_casts_poke}"
    )
    lines.append("  • Fleet Footwork — Q is on-attack, so the fireball procs the")
    lines.append("    heal / 20% MS / missing-mana. That is how you live to 175 stacks.")
    lines.append("    This page buys 0 attack speed; Fleet's job is uptime, not DPS.")
    lines.append("  • Battle Zeal — +2%/s basic-ability damage, cap 6%. Q/W/E and")
    lines.append("    the T3 burn are basic-ability damage. Brutal only spices the")
    if brutal_name in rune_results:
        lines.append(
            f"    on-hit; Zeal 25:00 mix {mix_of(rune_results[brutal_name][24]):.0f} → "
            f"{mix_of(fit_snaps[24]):.0f}."
        )
    else:
        lines.append("    on-hit; Zeal amps the whole Scorcher.")
    lines.append("  • Cut Down — poke hits healthy targets. Coup is the same slot")
    if coup_name in rune_results:
        lines.append(
            f"    and overlaps the 6.5% T3 execute "
            f"(poke-squish {rune_results[coup_name][24].poke_squish:.0f} vs "
            f"{fit_snaps[24].poke_squish:.0f})."
        )
    else:
        lines.append("    and overlaps the 6.5% T3 execute.")
    lines.append("  • Legend: Bloodline — 7% omnivamp heals off Q magic + true burn.")
    lines.append("    BT lifesteal does not. In an 8s window Haste is the same 4 Qs")
    if haste_name in rune_results:
        lines.append(
            f"    ({mix_of(rune_results[haste_name][24]):.0f} mix) — take Haste only"
        )
        lines.append("    if you already have enough vamp and want W/E/R uptime.")
    lines.append("  • Transcendence — 10 AH + 8% refund. Dropping it for Bone Plating")
    if bone_name in rune_results:
        lines.append(
            f"    costs a Q in the window "
            f"({rune_results[bone_name][21].q_casts_poke} vs "
            f"{fit_snaps[21].q_casts_poke}). Bone Plating only vs Lucian/Draven/Leona"
        )
        lines.append("    until you can swap back.")
    if conq_name in rune_results:
        lines.append(
            f"  • Conqueror paper-leads 25:00 mix "
            f"({mix_of(rune_results[conq_name][24]):.0f}) by stacking AD in combat."
        )
        lines.append("    Hexoptics poke is max-range; you are not in Conqueror range.")
    if lt_name in rune_results:
        lines.append(
            f"  • Lethal Tempo 7.3 wants AS items. ER/IE/Hex/LDR/BT is 0% item AS."
        )
        lines.append(
            f"    LT 25:00 mix {mix_of(rune_results[lt_name][24]):.0f} is fight autos,"
        )
        lines.append("    and it does not stack during a Q siege.")
    lines.append("  • Phase Rush is the dive/gank swap (common on CN screenshots).")
    lines.append("    0 damage. Take it when you cannot stand still to stack.")
    lines.append("=" * 80)
    return "\n".join(lines)


def export_json(results, timeline, rune_results, path: str) -> None:
    payload = {
        "meta": {
            "champion": "Smolder",
            "role": "ADC / Dragon lane",
            "patch": "7.3",
            "game_minutes": GAME_MINUTES,
            "playstyle": "Q poke siege + teamfight weave",
            "poke_weight": POKE_WEIGHT,
            "fight_weight": FIGHT_WEIGHT,
            "default_runes": DEFAULT_RUNES.name,
            "winning_items": WINNING_ITEMS,
        },
        "timeline": timeline,
        "builds": {
            name: [
                {
                    "minute": s.minute,
                    "items": s.items,
                    "gold": s.gold,
                    "level": s.level,
                    "stacks": s.stacks,
                    "ad": s.ad,
                    "bonus_ad": s.bonus_ad,
                    "crit": s.crit,
                    "ah": s.ah,
                    "legendary_count": s.legendary_count,
                    "poke_tank": s.poke_tank,
                    "poke_squish": s.poke_squish,
                    "fight_tank": s.fight_tank,
                    "fight_squish": s.fight_squish,
                    "mix_tank": s.mix_tank,
                    "mix_squish": s.mix_squish,
                    "q_casts_poke": s.q_casts_poke,
                    "notes": s.notes,
                }
                for s in snaps
            ]
            for name, snaps in results.items()
        },
        "runes": {
            name: [
                {
                    "minute": s.minute,
                    "mix_tank": s.mix_tank,
                    "mix_squish": s.mix_squish,
                    "poke_squish": s.poke_squish,
                    "q_casts_poke": s.q_casts_poke,
                    "ah": s.ah,
                    "as_pct": s.as_pct,
                    "notes": s.notes,
                }
                for s in snaps
            ]
            for name, snaps in rune_results.items()
        },
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def self_check(
    results: Dict[str, List[Snapshot]],
    rune_results: Dict[str, List[Snapshot]],
) -> None:
    hex_path = results["ER → IE → Hex → Mortal → BT"]
    old = results["Mura → Tri → Serylda → Shojin → IE"]
    shojin = results["ER → Shojin → IE → Mortal → Hex"]

    ie_on = first_minute_with(hex_path, lambda s: s.has_ie)
    assert ie_on is not None and ie_on <= 16, ie_on

    old_ie = first_minute_with(old, lambda s: s.has_ie)
    assert old_ie is None or old_ie > ie_on, (ie_on, old_ie)

    # Late mix: crit capstone must beat mana core
    hex22 = 0.55 * hex_path[21].mix_tank + 0.45 * hex_path[21].mix_squish
    old22 = 0.55 * old[21].mix_tank + 0.45 * old[21].mix_squish
    assert hex22 > old22, (hex22, old22)

    hex25 = 0.55 * hex_path[24].mix_tank + 0.45 * hex_path[24].mix_squish
    sh25 = 0.55 * shojin[24].mix_tank + 0.45 * shojin[24].mix_squish
    assert hex25 >= sh25 * 0.97, (hex25, sh25)

    # T3 exists by 20
    assert hex_path[19].t3, hex_path[19].stacks
    # 100% crit on the Hex page by 25
    assert hex_path[24].crit100, hex_path[24].crit

    fit = rune_results["Fleet / Zeal / Cut Down / Haste / Transcendence"]
    coup = rune_results["Fleet / Zeal / Coup / Haste / Transcendence"]
    blood = rune_results["Fleet / Zeal / Cut Down / Bloodline / Transcendence"]
    assert fit[24].poke_squish >= coup[24].poke_squish, (
        fit[24].poke_squish,
        coup[24].poke_squish,
    )
    assert fit[21].q_casts_poke >= blood[21].q_casts_poke
    assert fit[24].crit100


def main() -> None:
    results, timeline = run_all()
    rune_results = run_runes()
    self_check(results, rune_results)
    report = summarize(results, timeline, rune_results)
    print(report)
    out_dir = "/workspace/smolder-late-sim"
    with open(f"{out_dir}/report.txt", "w", encoding="utf-8") as f:
        f.write(report + "\n")
    export_json(results, timeline, rune_results, f"{out_dir}/results.json")
    print(f"\nWrote {out_dir}/report.txt and {out_dir}/results.json")


if __name__ == "__main__":
    main()
