#!/usr/bin/env python3
"""
Wild Rift Senna — 2nd-item burst / overkill simulation
Patch 7.3 item + kit values. Average game: 20 minutes.

Two roles:
  ADC farmer — lethality/%pen oneshot (Dusk → Serylda).
  Support fasting — crit paths that peak at item 2 AND keep
  scaling into 18–20 as Mist crit stacks.

Question (ADC):
  After 7.3 deleted Magnetic Blaster, which path peaks BURST at
  item 2 and overkills ADC + mid?

Question (support):
  Dusk first (early Nightstalker), then which 2nd item peaks
  the all-in? Crit-only Collector → Mortal is the fallback.

Question (full build + runes):
  After IE, sell Scythe for a 5th legendary. Which 4th/5th
  pair wins the all-in, and which rune page is best?
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import json

GAME_MINUTES = 20
SUPPORT_MINUTES = 28  # long game: 4th legendary then sell Scythe for 5th
BURST_WINDOW = 2.5  # rooted / flash-all-in, R already in the air
SCYTHE_SELL = 350  # 70% of Spectral Sickle 500; quest upgrade adds 0 cost

# ---------------------------------------------------------------------------
# Economy / XP / Mist  (ADC farmer who still collects souls)
# ---------------------------------------------------------------------------


def gold_at_minute(m: int) -> int:
    """Winning dragon-lane Senna: farm + plates + skirmishes. 2 legendaries ~12–13."""
    if m <= 0:
        return 500
    total = 500  # Long Sword start
    for t in range(1, m + 1):
        if t <= 4:
            total += 400
        elif t <= 8:
            total += 540
        elif t <= 12:
            total += 590
        else:
            total += 560
    return total


def level_at_minute(m: int) -> int:
    table = {
        1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7, 7: 8, 8: 9,
        9: 10, 10: 10, 11: 11, 12: 11, 13: 12, 14: 12,
        15: 13, 16: 13, 17: 14, 18: 14, 19: 15, 20: 15,
    }
    return table.get(m, min(15, 1 + m))


def mist_at_minute(m: int) -> int:
    """
    ADC soul collection (not full fasting — that delays the 2nd item).
    ~40 at 10:00, ~55 at 14:00, ~78 at 20:00.
    """
    if m <= 0:
        return 0
    total = 0
    for t in range(1, m + 1):
        if t <= 5:
            total += 3.2
        elif t <= 12:
            total += 4.0
        else:
            total += 4.4
    return int(total)


def support_gold(m: int) -> int:
    """Sickle tribute + Scythe soulcast. Lands ~2 legendaries ~15–16.
    After 20:00 a long game still funds 4th then sell-Scythe 5th."""
    if m <= 0:
        return 500
    total = 500  # Spectral Sickle
    for t in range(1, m + 1):
        if t <= 4:
            total += 310
        elif t <= 10:
            total += 460
        elif t <= 20:
            total += 560
        else:
            total += 700
    return total


def support_level(m: int) -> int:
    table = {
        1: 2, 2: 3, 3: 3, 4: 4, 5: 5, 6: 6, 7: 7, 8: 7,
        9: 8, 10: 9, 11: 9, 12: 10, 13: 10, 14: 11,
        15: 11, 16: 12, 17: 12, 18: 13, 19: 13, 20: 14,
        21: 14, 22: 14, 23: 15, 24: 15, 25: 15, 26: 15, 27: 15, 28: 15,
    }
    return table.get(m, min(15, 1 + m // 2))


def support_mist(m: int) -> int:
    """
    Fasting support: ADC last-hits, Senna takes souls + extracts.
    ~50 at 10:00, ~78 at 15:00, ~105 at 20:00.
    """
    if m <= 0:
        return 0
    total = 0.0
    for t in range(1, m + 1):
        if t <= 5:
            total += 4.6
        elif t <= 12:
            total += 5.4
        elif t <= 20:
            total += 5.8
        else:
            total += 5.2
    return int(total)


def eco_gold(m: int, role: str) -> int:
    return support_gold(m) if role == "support" else gold_at_minute(m)


def eco_level(m: int, role: str) -> int:
    return support_level(m) if role == "support" else level_at_minute(m)


def eco_mist(m: int, role: str) -> int:
    return support_mist(m) if role == "support" else mist_at_minute(m)


def scythe_ad_stacks(minute: int) -> float:
    # Soulcast: +4 AD / 60s after quest (~5:00), max +40.
    if minute < 6:
        return 0.0
    return 4.0 * min(10, minute - 5)


def skill_rank(level: int, skill: str) -> int:
    """WR: 4 ranks on Q/W/E, 3 on R (6 / 11 / 15). Max Q → W."""
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
    e_levels = [4, 13, 14, 15]
    mapping = {"Q": q_levels, "W": w_levels, "E": e_levels}
    return sum(1 for lv in mapping[skill] if level >= lv)


# ---------------------------------------------------------------------------
# Targets: full-HP ADC and mid at that minute
# ---------------------------------------------------------------------------


def adc_hp(m: int) -> float:
    lv = level_at_minute(m)
    # Damage items first; HP components come online after ~item 2
    item_hp = 8.0 * max(0, m - 8)
    return 550 + 92 * lv + item_hp


def adc_armor(m: int) -> float:
    lv = level_at_minute(m)
    extra = 0.0 if m < 14 else (12.0 if m < 18 else 22.0)
    return 26 + 3.9 * lv + extra


def mid_hp(m: int) -> float:
    lv = level_at_minute(m)
    item_hp = 6.0 * max(0, m - 9)
    return 540 + 96 * lv + item_hp


def mid_armor(m: int) -> float:
    lv = level_at_minute(m)
    extra = 0.0 if m < 14 else (8.0 if m < 18 else 18.0)
    return 21 + 3.5 * lv + extra


def mid_mr(m: int) -> float:
    lv = level_at_minute(m)
    extra = 0.0 if m < 12 else 12.0
    return 30 + 1.3 * lv + extra


def adc_mr(m: int) -> float:
    lv = level_at_minute(m)
    return 30 + 1.2 * lv


# ---------------------------------------------------------------------------
# Items (7.3)
# ---------------------------------------------------------------------------


@dataclass
class Item:
    name: str
    cost: int
    ad: float = 0
    ah: float = 0
    as_pct: float = 0
    crit: float = 0
    lethality: float = 0
    pct_pen: float = 0
    ult_haste: float = 0
    duskblade: bool = False
    collector: bool = False
    youmuu: bool = False
    hexoptics: bool = False
    yuntal: bool = False
    stormrazor: bool = False
    rfc: bool = False
    fiendhunter: bool = False
    infinity: bool = False
    essence: bool = False
    galeforce: bool = False
    serylda: bool = False
    mortal: bool = False
    ldr: bool = False
    tags: Tuple[str, ...] = ()


ITEMS: Dict[str, Item] = {
    "Spectral Sickle": Item("Spectral Sickle", 500, ad=10, tags=("support",)),
    "Black Mist Scythe": Item(
        "Black Mist Scythe", 0, ad=28, ah=10, tags=("support",)
    ),
    "Long Sword": Item("Long Sword", 500, ad=12),
    "B. F. Sword": Item("B. F. Sword", 1500, ad=40),
    "Pickaxe": Item("Pickaxe", 800, ad=20),
    "Brawler's Gloves": Item("Brawler's Gloves", 500, crit=0.15),
    "Noonquiver": Item("Noonquiver", 1300, ad=20, crit=0.15),
    "Serrated Dirk": Item("Serrated Dirk", 1000, ad=25, lethality=10),
    "Caulfield's Warhammer": Item("Caulfield's Warhammer", 1200, ad=20, ah=10),
    "Kircheis Shard": Item("Kircheis Shard", 800, as_pct=0.20),
    "Sheen": Item("Sheen", 800),
    "Last Whisper": Item("Last Whisper", 1200, ad=15, pct_pen=0.15),
    "Zeal": Item("Zeal", 1400, as_pct=0.15, crit=0.15),
    "Boots": Item("Boots", 500, tags=("boots",)),
    "Boots of Dynamism": Item(
        "Boots of Dynamism", 1200, ad=10, lethality=8, tags=("boots",)
    ),
    "Duskblade of Draktharr": Item(
        "Duskblade of Draktharr",
        3000,
        ad=55,
        ah=10,
        lethality=18,
        duskblade=True,
        tags=("lethality", "burst"),
    ),
    "The Collector": Item(
        "The Collector",
        3000,
        ad=50,
        crit=0.25,
        lethality=10,
        collector=True,
        tags=("lethality", "crit", "execute"),
    ),
    "Youmuu's Ghostblade": Item(
        "Youmuu's Ghostblade",
        3000,
        ad=55,
        ah=15,
        lethality=15,
        youmuu=True,
        tags=("lethality",),
    ),
    "Hexoptics C44": Item(
        "Hexoptics C44",
        2900,
        ad=55,
        crit=0.25,
        hexoptics=True,
        tags=("crit", "range"),
    ),
    "Yun Tal Wildarrows": Item(
        "Yun Tal Wildarrows",
        3100,
        ad=50,
        as_pct=0.25,
        yuntal=True,
        tags=("crit", "as"),
    ),
    "Stormrazor": Item(
        "Stormrazor",
        3000,
        ad=50,
        crit=0.25,
        as_pct=0.20,
        stormrazor=True,
        tags=("crit", "energized"),
    ),
    "Rapid Firecannon": Item(
        "Rapid Firecannon",
        2650,
        crit=0.25,
        as_pct=0.40,
        rfc=True,
        tags=("crit", "as", "energized"),
    ),
    "Fiendhunter Bolts": Item(
        "Fiendhunter Bolts",
        2650,
        crit=0.25,
        as_pct=0.45,
        ult_haste=20,
        fiendhunter=True,
        tags=("crit", "as", "ult"),
    ),
    "Infinity Edge": Item(
        "Infinity Edge",
        3500,
        ad=75,
        crit=0.25,
        infinity=True,
        tags=("crit", "capstone"),
    ),
    "Essence Reaver": Item(
        "Essence Reaver",
        3000,
        ad=50,
        ah=20,
        crit=0.25,
        essence=True,
        tags=("crit", "spellblade"),
    ),
    "Galeforce": Item(
        "Galeforce",
        3100,
        ad=60,
        crit=0.25,
        galeforce=True,
        tags=("crit", "dash"),
    ),
    "Serylda's Grudge": Item(
        "Serylda's Grudge",
        3100,
        ad=50,
        ah=15,
        pct_pen=0.35,
        serylda=True,
        tags=("pen",),
    ),
    "Mortal Reminder": Item(
        "Mortal Reminder",
        3000,
        ad=35,
        crit=0.25,
        pct_pen=0.30,
        mortal=True,
        tags=("pen", "antiheal"),
    ),
    "Lord Dominik's Regards": Item(
        "Lord Dominik's Regards",
        3300,
        ad=35,
        crit=0.25,
        pct_pen=0.35,
        ldr=True,
        tags=("pen",),
    ),
    "Edge of Night": Item(
        "Edge of Night",
        3000,
        ad=50,
        lethality=10,
        tags=("lethality", "spellshield"),
    ),
    "The Bloodthirster": Item(
        "The Bloodthirster",
        3400,
        ad=55,
        tags=("lifesteal",),
    ),
    "Guardian Angel": Item(
        "Guardian Angel",
        2800,
        ad=40,
        tags=("def",),
    ),
}

UPGRADE_COMPONENTS = {
    "Boots of Dynamism": ("Boots",),
    "Duskblade of Draktharr": ("Serrated Dirk", "Caulfield's Warhammer"),
    "The Collector": ("Serrated Dirk", "Noonquiver"),
    "Youmuu's Ghostblade": ("Serrated Dirk", "Caulfield's Warhammer"),
    "Hexoptics C44": ("Pickaxe", "Noonquiver", "Long Sword"),
    "Yun Tal Wildarrows": ("Noonquiver", "Pickaxe", "Kircheis Shard"),
    "Stormrazor": ("B. F. Sword", "Kircheis Shard", "Brawler's Gloves"),
    "Rapid Firecannon": ("Zeal", "Kircheis Shard"),
    "Fiendhunter Bolts": ("Zeal", "Kircheis Shard"),
    "Infinity Edge": ("B. F. Sword", "Pickaxe", "Brawler's Gloves"),
    "Essence Reaver": ("Sheen", "Caulfield's Warhammer", "Brawler's Gloves"),
    "Galeforce": ("Noonquiver", "Pickaxe", "Long Sword"),
    "Serylda's Grudge": ("Caulfield's Warhammer", "Last Whisper"),
    "Mortal Reminder": ("Last Whisper", "Brawler's Gloves"),
    "Lord Dominik's Regards": ("Last Whisper", "Noonquiver"),
    "Edge of Night": ("Serrated Dirk",),
    "The Bloodthirster": ("B. F. Sword",),
    "Guardian Angel": ("B. F. Sword",),
}

NEXT_COMPONENTS = {
    "Duskblade of Draktharr": ["Serrated Dirk", "Caulfield's Warhammer"],
    "The Collector": ["Serrated Dirk", "Noonquiver"],
    "Youmuu's Ghostblade": ["Serrated Dirk", "Caulfield's Warhammer"],
    "Hexoptics C44": ["Noonquiver", "Pickaxe", "Long Sword"],
    "Yun Tal Wildarrows": ["Noonquiver", "Pickaxe", "Kircheis Shard"],
    "Stormrazor": ["B. F. Sword", "Kircheis Shard", "Brawler's Gloves"],
    "Rapid Firecannon": ["Zeal", "Kircheis Shard"],
    "Fiendhunter Bolts": ["Zeal", "Kircheis Shard"],
    "Infinity Edge": ["B. F. Sword", "Pickaxe", "Brawler's Gloves"],
    "Essence Reaver": ["Sheen", "Caulfield's Warhammer", "Brawler's Gloves"],
    "Galeforce": ["Noonquiver", "Pickaxe", "Long Sword"],
    "Serylda's Grudge": ["Last Whisper", "Caulfield's Warhammer"],
    "Mortal Reminder": ["Last Whisper", "Brawler's Gloves"],
    "Lord Dominik's Regards": ["Last Whisper", "Noonquiver"],
    "Boots of Dynamism": ["Boots"],
    "Edge of Night": ["Serrated Dirk"],
    "The Bloodthirster": ["B. F. Sword"],
    "Guardian Angel": ["B. F. Sword"],
}

LEGENDARIES = {
    "Duskblade of Draktharr",
    "The Collector",
    "Youmuu's Ghostblade",
    "Hexoptics C44",
    "Yun Tal Wildarrows",
    "Stormrazor",
    "Rapid Firecannon",
    "Fiendhunter Bolts",
    "Infinity Edge",
    "Essence Reaver",
    "Galeforce",
    "Serylda's Grudge",
    "Mortal Reminder",
    "Lord Dominik's Regards",
    "Edge of Night",
    "The Bloodthirster",
    "Guardian Angel",
}

# Each path: buy order. Boots sit between 1st and 2nd legendary.
BUILD_PATHS: Dict[str, List[str]] = {
    # Lethality burst — the pre-7.3 identity, still legal
    "Dusk → Collector": [
        "Serrated Dirk",
        "Caulfield's Warhammer",
        "Duskblade of Draktharr",
        "Boots",
        "Boots of Dynamism",
        "Noonquiver",
        "The Collector",
        "Infinity Edge",
        "Serylda's Grudge",
    ],
    "Collector → Dusk": [
        "Serrated Dirk",
        "Noonquiver",
        "The Collector",
        "Boots",
        "Boots of Dynamism",
        "Duskblade of Draktharr",
        "Infinity Edge",
        "Serylda's Grudge",
    ],
    "Dusk → Youmuu": [
        "Serrated Dirk",
        "Caulfield's Warhammer",
        "Duskblade of Draktharr",
        "Boots",
        "Boots of Dynamism",
        "Youmuu's Ghostblade",
        "The Collector",
        "Serylda's Grudge",
    ],
    "Youmuu → Collector": [
        "Serrated Dirk",
        "Caulfield's Warhammer",
        "Youmuu's Ghostblade",
        "Boots",
        "Boots of Dynamism",
        "The Collector",
        "Infinity Edge",
        "Serylda's Grudge",
    ],
    # 7.3 range / crit first items
    "Hexoptics → Collector": [
        "Noonquiver",
        "Pickaxe",
        "Hexoptics C44",
        "Boots",
        "Boots of Dynamism",
        "The Collector",
        "Infinity Edge",
        "Serylda's Grudge",
    ],
    "Hexoptics → Dusk": [
        "Noonquiver",
        "Pickaxe",
        "Hexoptics C44",
        "Boots",
        "Boots of Dynamism",
        "Duskblade of Draktharr",
        "The Collector",
        "Infinity Edge",
    ],
    "Collector → Hexoptics": [
        "Serrated Dirk",
        "Noonquiver",
        "The Collector",
        "Boots",
        "Boots of Dynamism",
        "Hexoptics C44",
        "Infinity Edge",
        "Serylda's Grudge",
    ],
    "Collector → IE": [
        "Serrated Dirk",
        "Noonquiver",
        "The Collector",
        "Boots",
        "Boots of Dynamism",
        "B. F. Sword",
        "Infinity Edge",
        "Serylda's Grudge",
    ],
    "Dusk → IE": [
        "Serrated Dirk",
        "Caulfield's Warhammer",
        "Duskblade of Draktharr",
        "Boots",
        "Boots of Dynamism",
        "B. F. Sword",
        "Infinity Edge",
        "The Collector",
    ],
    "Hexoptics → IE": [
        "Noonquiver",
        "Pickaxe",
        "Hexoptics C44",
        "Boots",
        "Boots of Dynamism",
        "Infinity Edge",
        "The Collector",
        "Serylda's Grudge",
    ],
    # Energized / AS 7.3 replacements for Magnetic Blaster
    "Stormrazor → Collector": [
        "B. F. Sword",
        "Stormrazor",
        "Boots",
        "Boots of Dynamism",
        "The Collector",
        "Infinity Edge",
        "Serylda's Grudge",
    ],
    "Yun Tal → Collector": [
        "Noonquiver",
        "Yun Tal Wildarrows",
        "Boots",
        "Boots of Dynamism",
        "The Collector",
        "Infinity Edge",
        "Serylda's Grudge",
    ],
    "Collector → Stormrazor": [
        "Serrated Dirk",
        "Noonquiver",
        "The Collector",
        "Boots",
        "Boots of Dynamism",
        "Stormrazor",
        "Infinity Edge",
        "Serylda's Grudge",
    ],
    "Fiendhunter → Collector": [
        "Zeal",
        "Fiendhunter Bolts",
        "Boots",
        "Boots of Dynamism",
        "The Collector",
        "Infinity Edge",
        "Duskblade of Draktharr",
    ],
    "RFC → Collector": [
        "Zeal",
        "Rapid Firecannon",
        "Boots",
        "Boots of Dynamism",
        "The Collector",
        "Infinity Edge",
        "Duskblade of Draktharr",
    ],
    # Ability / dash
    "ER → Collector": [
        "Caulfield's Warhammer",
        "Sheen",
        "Essence Reaver",
        "Boots",
        "Boots of Dynamism",
        "The Collector",
        "Infinity Edge",
        "Serylda's Grudge",
    ],
    "Collector → ER": [
        "Serrated Dirk",
        "Noonquiver",
        "The Collector",
        "Boots",
        "Boots of Dynamism",
        "Essence Reaver",
        "Infinity Edge",
        "Serylda's Grudge",
    ],
    "Galeforce → Collector": [
        "Noonquiver",
        "Pickaxe",
        "Galeforce",
        "Boots",
        "Boots of Dynamism",
        "The Collector",
        "Infinity Edge",
        "Serylda's Grudge",
    ],
    "Dusk → Galeforce": [
        "Serrated Dirk",
        "Caulfield's Warhammer",
        "Duskblade of Draktharr",
        "Boots",
        "Boots of Dynamism",
        "Galeforce",
        "The Collector",
        "Infinity Edge",
    ],
    # %pen 2nd — trap vs squishies?
    "Collector → Serylda": [
        "Serrated Dirk",
        "Noonquiver",
        "The Collector",
        "Boots",
        "Boots of Dynamism",
        "Serylda's Grudge",
        "Infinity Edge",
        "Duskblade of Draktharr",
    ],
    "Dusk → Serylda": [
        "Serrated Dirk",
        "Caulfield's Warhammer",
        "Duskblade of Draktharr",
        "Boots",
        "Boots of Dynamism",
        "Serylda's Grudge",
        "The Collector",
        "Infinity Edge",
    ],
    "Collector → Mortal": [
        "Serrated Dirk",
        "Noonquiver",
        "The Collector",
        "Boots",
        "Boots of Dynamism",
        "Mortal Reminder",
        "Infinity Edge",
        "Duskblade of Draktharr",
    ],
    "Hexoptics → Stormrazor": [
        "Noonquiver",
        "Pickaxe",
        "Hexoptics C44",
        "Boots",
        "Boots of Dynamism",
        "Stormrazor",
        "Infinity Edge",
        "The Collector",
    ],
}


def _sup(*steps: str) -> List[str]:
    return ["Spectral Sickle", *steps]


# Support / fasting. Dusk first (early Nightstalker), then 2nd-item peak.
# No Dynamism: 1200g delays 2nd item. Crit-only paths are the fallback.
def _dusk(*steps: str) -> List[str]:
    return _sup(
        "Serrated Dirk", "Caulfield's Warhammer", "Duskblade of Draktharr",
        *steps,
    )


SUPPORT_DUSK_PATHS: Dict[str, List[str]] = {
    "Dusk → Serylda": _dusk(
        "Serylda's Grudge", "The Collector", "Infinity Edge",
    ),
    "Dusk → Mortal": _dusk(
        "Mortal Reminder", "Infinity Edge", "The Collector",
    ),
    "Dusk → Collector": _dusk(
        "The Collector", "Serylda's Grudge", "Infinity Edge",
    ),
    "Dusk → Hex": _dusk(
        "Hexoptics C44", "Serylda's Grudge", "The Collector",
    ),
    "Dusk → IE": _dusk(
        "Infinity Edge", "Serylda's Grudge", "The Collector",
    ),
    "Dusk → Youmuu": _dusk(
        "Youmuu's Ghostblade", "Serylda's Grudge", "The Collector",
    ),
    "Dusk → LDR": _dusk(
        "Lord Dominik's Regards", "Infinity Edge", "The Collector",
    ),
    "Dusk → EoN": _dusk(
        "Edge of Night", "Serylda's Grudge", "The Collector",
    ),
    "Dusk → Galeforce": _dusk(
        "Galeforce", "Serylda's Grudge", "The Collector",
    ),
    "Dusk → Serylda + Dynamism": _dusk(
        "Boots", "Boots of Dynamism",
        "Serylda's Grudge", "The Collector",
    ),
}

SUPPORT_CRIT_PATHS: Dict[str, List[str]] = {
    "Collector → Mortal → IE": _sup(
        "Serrated Dirk", "Noonquiver", "The Collector",
        "Mortal Reminder", "Infinity Edge",
    ),
    "Hex → Mortal → IE": _sup(
        "Noonquiver", "Pickaxe", "Hexoptics C44",
        "Mortal Reminder", "Infinity Edge",
    ),
    "Collector → LDR → IE": _sup(
        "Serrated Dirk", "Noonquiver", "The Collector",
        "Lord Dominik's Regards", "Infinity Edge",
    ),
    "Hex → Collector → IE": _sup(
        "Noonquiver", "Pickaxe", "Hexoptics C44",
        "The Collector", "Infinity Edge",
    ),
    "Collector → Hex → IE": _sup(
        "Serrated Dirk", "Noonquiver", "The Collector",
        "Hexoptics C44", "Infinity Edge",
    ),
    "Hex → IE → Mortal": _sup(
        "Noonquiver", "Pickaxe", "Hexoptics C44",
        "Infinity Edge", "Mortal Reminder",
    ),
    "Collector → IE → Mortal": _sup(
        "Serrated Dirk", "Noonquiver", "The Collector",
        "Infinity Edge", "Mortal Reminder",
    ),
    "IE → Hex → Mortal": _sup(
        "B. F. Sword", "Infinity Edge",
        "Hexoptics C44", "Mortal Reminder",
    ),
    "Hex → Stormrazor → IE": _sup(
        "Noonquiver", "Pickaxe", "Hexoptics C44",
        "Stormrazor", "Infinity Edge",
    ),
    "Stormrazor → IE": _sup(
        "B. F. Sword", "Stormrazor",
        "Infinity Edge", "Mortal Reminder",
    ),
    "Stormrazor → Collector → IE": _sup(
        "B. F. Sword", "Stormrazor",
        "The Collector", "Infinity Edge",
    ),
    "Yun Tal → IE": _sup(
        "Noonquiver", "Yun Tal Wildarrows",
        "Infinity Edge", "Mortal Reminder",
    ),
    "Yun Tal → Collector → IE": _sup(
        "Noonquiver", "Yun Tal Wildarrows",
        "The Collector", "Infinity Edge",
    ),
    "RFC → IE": _sup(
        "Zeal", "Rapid Firecannon",
        "Infinity Edge", "The Collector",
    ),
    "Fiendhunter → IE": _sup(
        "Zeal", "Fiendhunter Bolts",
        "Infinity Edge", "The Collector",
    ),
    "ER → IE": _sup(
        "Caulfield's Warhammer", "Sheen", "Essence Reaver",
        "Infinity Edge", "The Collector",
    ),
    "Galeforce → IE": _sup(
        "Noonquiver", "Pickaxe", "Galeforce",
        "Infinity Edge", "Mortal Reminder",
    ),
    "Hex → Galeforce → IE": _sup(
        "Noonquiver", "Pickaxe", "Hexoptics C44",
        "Galeforce", "Infinity Edge",
    ),
    # Gold-sink: Dynamism before 2nd delays the spike and blocks IE.
    "Collector → Mortal + Dynamism": _sup(
        "Serrated Dirk", "Noonquiver", "The Collector",
        "Boots", "Boots of Dynamism",
        "Mortal Reminder", "Infinity Edge",
    ),
}

# Lethality contrast on the same support gold/mist (not in the crit ranking).
# No Dynamism: same 14:00 2nd as the Dusk-first ranking.
SUPPORT_CONTRAST_PATHS: Dict[str, List[str]] = {
    "Dusk → Serylda (lethality)": _dusk(
        "Serylda's Grudge", "The Collector",
    ),
    "Dusk → Collector (lethality)": _dusk(
        "The Collector", "Infinity Edge",
    ),
}


def _dusk_finish(third: str, fourth: str, fifth: str) -> List[str]:
    """Dusk → Serylda core, then 3rd/4th, sell Scythe, 5th."""
    return _dusk(
        "Serylda's Grudge",
        third, fourth, "Sell Scythe", fifth,
    )


# Full-build 3rd/4th/5th after Dusk → Serylda. Sell Scythe only when
# the 5th legendary is affordable (see resolve_inventory).
SUPPORT_FINISH_PATHS: Dict[str, List[str]] = {
    "Youmuu → Collector → Fiendhunter": _dusk_finish(
        "Youmuu's Ghostblade", "The Collector", "Fiendhunter Bolts"
    ),
    "Collector → Youmuu → Fiendhunter": _dusk_finish(
        "The Collector", "Youmuu's Ghostblade", "Fiendhunter Bolts"
    ),
    "IE → Collector → Fiendhunter": _dusk_finish(
        "Infinity Edge", "The Collector", "Fiendhunter Bolts"
    ),
    "EoN → Collector → Fiendhunter": _dusk_finish(
        "Edge of Night", "The Collector", "Fiendhunter Bolts"
    ),
    "Collector → Hex → Fiendhunter": _dusk_finish(
        "The Collector", "Hexoptics C44", "Fiendhunter Bolts"
    ),
    "Hex → Collector → Fiendhunter": _dusk_finish(
        "Hexoptics C44", "The Collector", "Fiendhunter Bolts"
    ),
    "Mortal → Collector → Fiendhunter": _dusk_finish(
        "Mortal Reminder", "The Collector", "Fiendhunter Bolts"
    ),
    "Collector → Hex → RFC": _dusk_finish(
        "The Collector", "Hexoptics C44", "Rapid Firecannon"
    ),
    "Hex → Collector → RFC": _dusk_finish(
        "Hexoptics C44", "The Collector", "Rapid Firecannon"
    ),
    "Collector → IE → RFC": _dusk_finish(
        "The Collector", "Infinity Edge", "Rapid Firecannon"
    ),
    "IE → Collector → RFC": _dusk_finish(
        "Infinity Edge", "The Collector", "Rapid Firecannon"
    ),
    "Collector → IE → Hex": _dusk_finish(
        "The Collector", "Infinity Edge", "Hexoptics C44"
    ),
    "Keep Scythe (4 items)": _dusk(
        "Serylda's Grudge", "The Collector", "Hexoptics C44",
    ),
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


def resolve_inventory(
    path: List[str], gold: int, minute: int = 0, role: str = "adc"
) -> List[Item]:
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
        if item_name == "Black Mist Scythe":
            return 0
        credit, _ = credit_for(item_name)
        return max(0, ITEMS[item_name].cost - credit)

    def can_afford(item_name: str) -> bool:
        return gold_pool >= remaining_cost(item_name)

    def buy(item_name: str) -> bool:
        nonlocal gold_pool
        if item_name == "Black Mist Scythe":
            if "Spectral Sickle" in owned:
                owned.remove("Spectral Sickle")
            if "Black Mist Scythe" not in owned:
                owned.insert(0, item_name)
            return True
        if item_name == "Boots of Dynamism" and "Boots of Dynamism" in owned:
            return False
        if item_name != "Boots of Dynamism" and item_name in owned:
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
        if step == "Black Mist Scythe":
            continue
        if step == "Sell Scythe":
            next_leg = None
            seen_sell = False
            for nxt in path:
                if nxt == "Sell Scythe":
                    seen_sell = True
                    continue
                if seen_sell and nxt in LEGENDARIES:
                    next_leg = nxt
                    break
            have = (
                "Black Mist Scythe" in owned or "Spectral Sickle" in owned
            )
            if have and next_leg is not None:
                credit, _ = credit_for(next_leg)
                need = max(0, ITEMS[next_leg].cost - credit)
                if gold_pool + SCYTHE_SELL >= need:
                    if "Black Mist Scythe" in owned:
                        owned.remove("Black Mist Scythe")
                    if "Spectral Sickle" in owned:
                        owned.remove("Spectral Sickle")
                    gold_pool += SCYTHE_SELL
            continue
        if step == "Spectral Sickle":
            if (
                "Spectral Sickle" not in owned
                and "Black Mist Scythe" not in owned
            ):
                buy("Spectral Sickle")
            continue
        if step in owned:
            continue
        if can_afford(step):
            buy(step)
        else:
            blocked_at = step
            break

    if (role == "support" or minute >= 5) and minute >= 5:
        if "Spectral Sickle" in owned:
            owned.remove("Spectral Sickle")
            owned.insert(0, "Black Mist Scythe")

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
                if step in ("Spectral Sickle", "Black Mist Scythe", "Sell Scythe"):
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

    if "Boots of Dynamism" in owned and "Boots" in owned:
        owned.remove("Boots")
    return [ITEMS[n] for n in owned]


# ---------------------------------------------------------------------------
# Combat model — 2.5s R + W + Q + autos
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
    crit: float
    lethality: float
    pct_pen: float
    legendary_count: int
    mist: int
    autos: int
    exp_adc: float
    lucky_adc: float
    exp_mid: float
    lucky_mid: float
    overkill_adc_exp: float
    overkill_adc_lucky: float
    overkill_mid_exp: float
    overkill_mid_lucky: float
    kill_adc_exp: bool
    kill_adc_lucky: bool
    kill_mid_exp: bool
    kill_mid_lucky: bool
    notes: str
    has_dusk: bool
    has_collector: bool
    has_hex: bool
    has_ie: bool
    has_yuntal: bool
    has_serylda: bool
    has_youmuu: bool
    has_er: bool
    has_fiend: bool
    sold_scythe: bool = False


@dataclass
class RunePage:
    name: str
    keystone: str = "fleet"
    brutal: bool = True
    empowered: bool = True
    precision: str = "cut_down"  # cut_down, coup, none
    gathering_storm: bool = False
    sudden_impact: bool = False
    cheap_shot: bool = False
    alacrity: float = 0.0
    cut_down_pct: float = 0.08


DEFAULT_RUNES = RunePage("Fleet / Brutal / Emp / Cut Down")


def gathering_storm_ad(minute: int) -> float:
    # 7.1+: first tick 6:00, then every 3 min. 2/5/9/14/20/27/35/44 …
    if minute < 6:
        return 0.0
    ticks = 1 + (minute - 6) // 3
    seq = [2, 5, 9, 14, 20, 27, 35, 44, 54, 65]
    return float(seq[min(ticks, len(seq)) - 1])


def dark_harvest_souls(minute: int) -> int:
    # Fasting support takedowns, not a farming ADC.
    return min(18, int(0.45 * minute))


def electrocute_raw(level: int, bonus_ad: float) -> float:
    # Patch 7.2: 40–210 + 10% bonus AD + 5% AP
    return 40.0 + 170.0 * (level - 1) / 14.0 + 0.10 * bonus_ad


def empowerment_raw(level: int) -> float:
    # Patch 7.2: 40–165 on 3rd attack
    return 40.0 + 125.0 * (level - 1) / 14.0


def aery_raw(level: int, bonus_ad: float) -> float:
    return 15.0 + 35.0 * (level - 1) / 14.0 + 0.15 * bonus_ad


def comet_raw(level: int, bonus_ad: float) -> float:
    return 70.0 + 145.0 * (level - 1) / 14.0 + 0.20 * bonus_ad


def cheap_shot_raw(level: int) -> float:
    return 8.0 + 22.0 * (level - 1) / 14.0


def senna_crit_mult(has_ie: bool) -> float:
    """7.3: base crit 200%, IE 230%. Senna autos deal 90% of that."""
    normal = 2.30 if has_ie else 2.00
    return 0.90 * normal


def q_base(rank: int) -> float:
    return [0, 50, 80, 110, 140][rank] if rank else 0.0


def w_base(rank: int) -> float:
    return [0, 90, 155, 220, 285][rank] if rank else 0.0


def r_base(rank: int) -> float:
    return [0, 250, 400, 550][rank] if rank else 0.0


def duskblade_proc(level: int) -> float:
    # 60 at 1 → 160 at 15
    return 60.0 + 100.0 * (level - 1) / 14.0


def empowered_attack(level: int) -> float:
    # WR Empowered Attack, ranged 80%: ~28–40 adaptive
    full = 35.0 + 15.0 * (level - 1) / 14.0
    return 0.80 * full


def mist_current_hp_pct(level: int) -> float:
    # 1% → 10% by level 15
    return 0.01 + 0.09 * (level - 1) / 14.0


def yuntal_crit(minute: int, first_yuntal_minute: Optional[int]) -> float:
    """0.2% crit per ranged attack, cap 25%. ~8 autos/min in lane."""
    if first_yuntal_minute is None:
        return 0.0
    owned = max(0, minute - first_yuntal_minute)
    autos = owned * 8
    return min(0.25, autos * 0.002)


def attack_speed(level: int, bonus_item_as: float, yuntal_flurry: bool) -> float:
    """7.3: base 0.4, ratio 0.4, base bonus AS 0.6, +0.05 per level."""
    bonus = 0.60 + 0.05 * (level - 1) + bonus_item_as
    if yuntal_flurry:
        bonus += 0.25
    return 0.40 + bonus * 0.40


def autos_in_window(aspd: float) -> int:
    """R pre-cast. In-window: W (0.25) + Q (~0.32) + autos."""
    setup = 0.25 + 0.32
    remain = max(0.4, BURST_WINDOW - setup)
    n = 1 + int(max(0.0, remain - 0.05) / max(0.55, 1.0 / max(0.4, aspd)))
    return max(1, min(3, n))


def phys_mult(armor: float, pct_pen: float, lethality: float) -> float:
    reduced = armor * (1.0 - pct_pen) - lethality
    reduced = max(0.0, reduced)
    return 100.0 / (100.0 + reduced)


def magic_mult(mr: float) -> float:
    return 100.0 / (100.0 + max(0.0, mr))


def sum_stats(
    inv: List[Item], minute: int, first_yuntal: Optional[int]
) -> dict:
    ad = ah = as_pct = crit = leth = pct = uh = 0.0
    flags = {
        "dusk": False,
        "collector": False,
        "youmuu": False,
        "hex": False,
        "yuntal": False,
        "storm": False,
        "rfc": False,
        "fiend": False,
        "ie": False,
        "er": False,
        "gale": False,
        "serylda": False,
        "mortal": False,
        "ldr": False,
    }
    names = []
    for it in inv:
        names.append(it.name)
        ad += it.ad
        ah += it.ah
        as_pct += it.as_pct
        crit += it.crit
        leth += it.lethality
        pct += it.pct_pen
        uh += it.ult_haste
        if it.duskblade:
            flags["dusk"] = True
        if it.collector:
            flags["collector"] = True
        if it.youmuu:
            flags["youmuu"] = True
        if it.hexoptics:
            flags["hex"] = True
        if it.yuntal:
            flags["yuntal"] = True
        if it.stormrazor:
            flags["storm"] = True
        if it.rfc:
            flags["rfc"] = True
        if it.fiendhunter:
            flags["fiend"] = True
        if it.infinity:
            flags["ie"] = True
        if it.essence:
            flags["er"] = True
        if it.galeforce:
            flags["gale"] = True
        if it.serylda:
            flags["serylda"] = True
        if it.mortal:
            flags["mortal"] = True
        if it.ldr:
            flags["ldr"] = True
        if it.name == "Black Mist Scythe":
            ad += scythe_ad_stacks(minute)

    if flags["yuntal"]:
        crit += yuntal_crit(minute, first_yuntal)

    return {
        "item_ad": ad,
        "ah": ah,
        "as_pct": as_pct,
        "item_crit": crit,
        "leth": leth,
        "pct": min(pct, 0.45),
        "uh": uh,
        "names": names,
        **flags,
    }


def combo_damage(
    *,
    level: int,
    mist: int,
    st: dict,
    hp: float,
    armor: float,
    mr: float,
    lucky: bool,
    runes: Optional[RunePage] = None,
    minute: int = 20,
) -> Tuple[float, int]:
    """
    All-in on a full-HP squishy.
    Order: R (mark) → W → Q (consume %HP + Relic on-hit) → autos
    (Nightstalker / Spellblade / Energized / Hexoptics / Galeforce dash).
    """
    runes = runes or DEFAULT_RUNES
    mist_ad = 1.25 * mist
    gs_ad = gathering_storm_ad(minute) if runes.gathering_storm else 0.0
    bonus_ad = st["item_ad"] + mist_ad + gs_ad
    total_ad = 54.0 + bonus_ad  # WR Senna: no AD growth
    item_crit = min(1.0, st["item_crit"])
    mist_crit = 0.10 * (mist // 20)
    crit_chance = min(1.0, item_crit + mist_crit)
    cmult = senna_crit_mult(st["ie"])
    extra_leth = 8.0 if runes.sudden_impact else 0.0
    p = phys_mult(armor, st["pct"], st["leth"] + extra_leth)
    m = magic_mult(mr)

    q_rank = skill_rank(level, "Q")
    w_rank = skill_rank(level, "W")
    r_rank = skill_rank(level, "R")

    extra_as = runes.alacrity
    if runes.keystone == "lethal_tempo":
        extra_as += 0.064 * 2  # two autos in the window
    aspd = attack_speed(level, st["as_pct"] + extra_as, st["yuntal"])
    n_aa = autos_in_window(aspd)

    # Average auto multiplier (lucky = every auto crits)
    auto_mult = cmult if lucky else (1.0 - crit_chance) + crit_chance * cmult
    if st["fiend"] and r_rank > 0:
        # Opening Barrage: next 3 attacks guaranteed crit at 80% of normal
        # crit damage; if it would already crit → +15% true instead.
        # Senna's "normal crit" is already 90% of 200/230.
        barrage_mult = 0.80 * cmult
        if lucky or crit_chance >= 0.99:
            # would already crit → keep full Senna crit + 15% true later
            auto_mult = cmult
            fiend_true = True
        else:
            auto_mult = barrage_mult
            fiend_true = False
    else:
        fiend_true = False

    hex_amp = 1.10 if st["hex"] else 1.0  # max range (Senna always ≥550)

    dmg = 0.0
    hp_left = hp
    impaired = False  # W root
    attack_hits = 0  # Empowerment stacks (Q on-hit + autos)
    ability_hits = 0  # Electrocute stacks

    def amp(before: float) -> float:
        ratio = before / hp if hp else 1.0
        if runes.precision == "cut_down" and ratio > 0.60:
            return 1.0 + runes.cut_down_pct
        if runes.precision == "coup" and ratio < 0.40:
            return 1.08
        return 1.0

    def apply_phys(raw: float) -> float:
        nonlocal hp_left, dmg
        dealt = raw * p * amp(hp_left)
        dmg += dealt
        hp_left = max(0.0, hp_left - dealt)
        return dealt

    def apply_magic(raw: float) -> float:
        nonlocal hp_left, dmg
        dealt = raw * m * amp(hp_left)
        dmg += dealt
        hp_left = max(0.0, hp_left - dealt)
        return dealt

    def apply_true(raw: float) -> float:
        nonlocal hp_left, dmg
        dealt = raw * amp(hp_left)
        dmg += dealt
        hp_left = max(0.0, hp_left - dealt)
        return dealt

    def maybe_electrocute() -> None:
        nonlocal ability_hits
        ability_hits += 1
        if runes.keystone == "electrocute" and ability_hits == 3:
            apply_phys(electrocute_raw(level, bonus_ad))

    dh_done = False
    emp_done = False

    def maybe_harvest() -> None:
        nonlocal dh_done
        if runes.keystone != "dark_harvest" or dh_done:
            return
        if hp_left / hp > 0.50:
            return
        dh_done = True
        souls = dark_harvest_souls(minute)
        apply_phys(35.0 + 11.0 * souls + 0.10 * bonus_ad)

    def maybe_cheap() -> None:
        if runes.cheap_shot and impaired:
            apply_true(cheap_shot_raw(level))

    def maybe_empowerment() -> None:
        nonlocal attack_hits, emp_done
        attack_hits += 1
        if runes.keystone == "empowerment" and attack_hits >= 3 and not emp_done:
            emp_done = True
            apply_phys(empowerment_raw(level))

    brutal = (6.0 + 0.08 * bonus_ad) if runes.brutal else 0.0
    relic = 0.20 * total_ad
    emp = empowered_attack(level) if runes.empowered else 0.0

    # R — 120% bonus AD (7.3 also +70% AP, we build AD)
    if r_rank > 0:
        apply_phys(r_base(r_rank) + 1.20 * bonus_ad)
        maybe_electrocute()
        maybe_harvest()
        if runes.keystone == "aery":
            apply_magic(aery_raw(level, bonus_ad))

    # W
    if w_rank > 0:
        apply_phys(w_base(w_rank) + 0.70 * bonus_ad)
        impaired = True
        maybe_electrocute()
        maybe_harvest()
        maybe_cheap()
        if runes.keystone == "comet":
            apply_magic(comet_raw(level, bonus_ad))

    # Q + Relic on-hit (Q applies on-hit to champions) + Empowered Attack
    q_raw = q_base(q_rank) + 0.60 * bonus_ad
    apply_phys(q_raw + relic + emp + brutal)
    maybe_electrocute()
    maybe_harvest()
    maybe_cheap()
    maybe_empowerment()  # Q on-hit counts as an attack

    # Mist extract: 2nd hit on a marked champ (R/W already marked)
    apply_phys(mist_current_hp_pct(level) * hp_left)
    maybe_harvest()

    # Galeforce dash missiles (used to gap-close the all-in)
    if st["gale"]:
        gale = (40.0 + 80.0 * (level - 1) / 14.0) + 0.35 * bonus_ad
        apply_phys(gale)
        maybe_harvest()

    # Autos
    for i in range(n_aa):
        auto_raw = (total_ad * auto_mult + relic) * hex_amp + brutal
        apply_phys(auto_raw)
        maybe_harvest()
        maybe_cheap()
        maybe_empowerment()
        if st["fiend"] and fiend_true and i < 3:
            true_hit = 0.15 * total_ad * auto_mult
            dmg += true_hit
            hp_left = max(0.0, hp_left - true_hit)

    # Duskblade Nightstalker — first basic attack vs champion
    if st["dusk"] and n_aa >= 1:
        apply_phys(duskblade_proc(level))
        maybe_harvest()

    # Essence Reaver Spellblade on the first auto after Q
    if st["er"] and n_aa >= 1:
        sb = 1.35 * 54.0 + 80.0 * crit_chance
        apply_phys(sb)

    # Energized magic (one proc in the window)
    if st["storm"]:
        apply_magic(120.0)
    elif st["rfc"]:
        apply_magic(80.0)

    # First Strike: 9% bonus true of post-mitigation damage (R from fog)
    if runes.keystone == "first_strike":
        bonus_true = 0.09 * dmg
        dmg += bonus_true
        hp_left = max(0.0, hp_left - bonus_true)

    # Empowerment 8% after 3rd attack — remaining damage already applied.
    # Approximate: if proc happened, 8% of later autos is small; skip.

    # Collector execute
    exec_pct = 0.05 if st["collector"] else 0.0
    if exec_pct and hp_left <= hp * exec_pct + 1e-6:
        dmg += hp_left
        hp_left = 0.0

    return dmg, n_aa


def yuntal_online_minute(
    path: List[str], role: str = "adc", minutes: int = GAME_MINUTES
) -> Optional[int]:
    for m in range(1, minutes + 1):
        names = [
            it.name
            for it in resolve_inventory(path, eco_gold(m, role), m, role)
        ]
        if "Yun Tal Wildarrows" in names:
            return m
    return None


def compute_snapshot(
    build_name: str,
    path: List[str],
    minute: int,
    yuntal_min: Optional[int],
    role: str = "adc",
    runes: Optional[RunePage] = None,
) -> Snapshot:
    gold = eco_gold(minute, role)
    level = eco_level(minute, role)
    mist = eco_mist(minute, role)
    inv = resolve_inventory(path, gold, minute, role)
    st = sum_stats(inv, minute, yuntal_min)
    bonus_ad = st["item_ad"] + 1.25 * mist
    total_ad = 54.0 + bonus_ad
    mist_crit = 0.10 * (mist // 20)
    crit = min(1.0, st["item_crit"] + mist_crit)

    a_hp, a_ar, a_mr = adc_hp(minute), adc_armor(minute), adc_mr(minute)
    m_hp, m_ar, m_mr = mid_hp(minute), mid_armor(minute), mid_mr(minute)

    exp_a, n_aa = combo_damage(
        level=level, mist=mist, st=st, hp=a_hp, armor=a_ar, mr=a_mr,
        lucky=False, runes=runes, minute=minute,
    )
    lucky_a, _ = combo_damage(
        level=level, mist=mist, st=st, hp=a_hp, armor=a_ar, mr=a_mr,
        lucky=True, runes=runes, minute=minute,
    )
    exp_m, _ = combo_damage(
        level=level, mist=mist, st=st, hp=m_hp, armor=m_ar, mr=m_mr,
        lucky=False, runes=runes, minute=minute,
    )
    lucky_m, _ = combo_damage(
        level=level, mist=mist, st=st, hp=m_hp, armor=m_ar, mr=m_mr,
        lucky=True, runes=runes, minute=minute,
    )

    exec_pct = 0.05 if st["collector"] else 0.0

    def is_kill(dmg: float, hp: float) -> bool:
        return dmg >= hp * (1.0 - exec_pct) - 0.5

    n_leg = sum(1 for n in st["names"] if n in LEGENDARIES)
    sold = not any(
        n in ("Black Mist Scythe", "Spectral Sickle") for n in st["names"]
    ) and role == "support" and minute >= 5
    notes = []
    if st["dusk"]:
        notes.append("Nightstalker")
    if st["collector"]:
        notes.append("execute")
    if st["hex"]:
        notes.append("range amp")
    if st["ie"]:
        notes.append("230% crit")
    if st["yuntal"]:
        notes.append("Yun Tal stacks")
    if st["fiend"]:
        notes.append("R-barrage")
    if st["er"]:
        notes.append("spellblade")
    if sold:
        notes.append("sold Scythe")
    if n_leg == 0:
        notes.append("pre-legendary")
    elif n_leg == 1:
        notes.append("1 item")
    elif n_leg == 2:
        notes.append("2-ITEM SPIKE")
    elif n_leg == 3:
        notes.append("3 items")
    elif n_leg == 4:
        notes.append("4 items")
    else:
        notes.append("FULL BUILD")

    return Snapshot(
        minute=minute,
        build_name=build_name,
        items=st["names"],
        gold=gold,
        level=level,
        ad=round(total_ad, 1),
        bonus_ad=round(bonus_ad, 1),
        crit=round(crit, 3),
        lethality=st["leth"],
        pct_pen=st["pct"],
        legendary_count=n_leg,
        mist=mist,
        autos=n_aa,
        exp_adc=round(exp_a, 1),
        lucky_adc=round(lucky_a, 1),
        exp_mid=round(exp_m, 1),
        lucky_mid=round(lucky_m, 1),
        overkill_adc_exp=round(exp_a / a_hp, 3),
        overkill_adc_lucky=round(lucky_a / a_hp, 3),
        overkill_mid_exp=round(exp_m / m_hp, 3),
        overkill_mid_lucky=round(lucky_m / m_hp, 3),
        kill_adc_exp=is_kill(exp_a, a_hp),
        kill_adc_lucky=is_kill(lucky_a, a_hp),
        kill_mid_exp=is_kill(exp_m, m_hp),
        kill_mid_lucky=is_kill(lucky_m, m_hp),
        notes=", ".join(notes) if notes else "-",
        has_dusk=st["dusk"],
        has_collector=st["collector"],
        has_hex=st["hex"],
        has_ie=st["ie"],
        has_yuntal=st["yuntal"],
        has_serylda=st["serylda"] or st["mortal"] or st["ldr"],
        has_youmuu=st["youmuu"],
        has_er=st["er"],
        has_fiend=st["fiend"],
        sold_scythe=sold,
    )


def burst_score(s: Snapshot) -> float:
    """Peak overkill ADC+mid, with the 2nd-item spike as the goal."""
    lucky = 0.5 * (s.overkill_adc_lucky + s.overkill_mid_lucky)
    expected = 0.5 * (s.overkill_adc_exp + s.overkill_mid_exp)
    mix = 0.70 * lucky + 0.30 * expected
    both = 1.10 if s.kill_adc_lucky and s.kill_mid_lucky else 1.0
    both_exp = 1.06 if s.kill_adc_exp and s.kill_mid_exp else 1.0
    two = 1.14 if s.legendary_count >= 2 else (
        0.90 if s.legendary_count == 1 else 0.78
    )
    # Crit 2nd without lethality/%pen: Q/W/R do not crit, so the spike is autos-only
    spell = 1.0
    if s.legendary_count >= 2 and not (s.has_dusk or s.has_serylda or s.has_youmuu):
        spell = 0.97
    return mix * both * both_exp * two * spell


def mix_ok(s: Snapshot) -> float:
    lucky = 0.5 * (s.overkill_adc_lucky + s.overkill_mid_lucky)
    expected = 0.5 * (s.overkill_adc_exp + s.overkill_mid_exp)
    return 0.60 * lucky + 0.40 * expected


def dusk_support_score(s: Snapshot) -> float:
    """Dusk item-1 (early Nightstalker), then 2nd-item overkill."""
    mix = mix_ok(s)
    dusk_early = 1.0
    if s.has_dusk:
        dusk_early = 1.20 if s.minute <= 12 else 1.10
    two = 1.18 if s.legendary_count >= 2 else (
        0.94 if s.legendary_count == 1 else 0.76
    )
    pen = 1.10 if s.legendary_count >= 2 and s.has_serylda else 1.0
    both = 1.08 if s.kill_adc_lucky and s.kill_mid_lucky else 1.0
    both_e = 1.05 if s.kill_adc_exp and s.kill_mid_exp else 1.0
    return mix * dusk_early * two * pen * both * both_e


def support_score(s: Snapshot) -> float:
    """2nd-item peak, then keep climbing 18–20 as Mist crit stacks."""
    mix = mix_ok(s)
    two = 1.16 if s.legendary_count >= 2 else (
        0.90 if s.legendary_count == 1 else 0.76
    )
    late = 1.0
    if s.minute >= 16:
        if s.has_ie:
            late += 0.14
        if s.legendary_count >= 3:
            late += 0.06
        if s.crit >= 0.70:
            late += 0.05
        if s.has_serylda:
            late += 0.04  # Mortal / LDR %pen as armor comes online
    both = 1.08 if s.kill_adc_lucky and s.kill_mid_lucky else 1.0
    both_e = 1.05 if s.kill_adc_exp and s.kill_mid_exp else 1.0
    return mix * two * late * both * both_e


def run_all(
    paths: Optional[Dict[str, List[str]]] = None,
    role: str = "adc",
    scorer=None,
    minutes: int = GAME_MINUTES,
    runes: Optional[RunePage] = None,
) -> Tuple[Dict[str, List[Snapshot]], List[dict], Dict[str, Optional[int]]]:
    paths = paths or BUILD_PATHS
    score_fn = scorer or burst_score
    yuntal_mins: Dict[str, Optional[int]] = {
        name: yuntal_online_minute(path, role, minutes) for name, path in paths.items()
    }
    results: Dict[str, List[Snapshot]] = {}
    for name, path in paths.items():
        results[name] = [
            compute_snapshot(name, path, m, yuntal_mins[name], role, runes)
            for m in range(1, minutes + 1)
        ]

    timeline = []
    for m in range(1, minutes + 1):
        cands = [(n, results[n][m - 1]) for n in results]
        best_n, best_s = max(cands, key=lambda x: score_fn(x[1]))
        timeline.append(
            {
                "minute": m,
                "winner": best_n,
                "lucky_adc": best_s.lucky_adc,
                "lucky_mid": best_s.lucky_mid,
                "ok_adc": best_s.overkill_adc_lucky,
                "ok_mid": best_s.overkill_mid_lucky,
                "kill_adc": best_s.kill_adc_lucky,
                "kill_mid": best_s.kill_mid_lucky,
                "items": best_s.items,
                "ad": best_s.ad,
                "crit": best_s.crit,
                "notes": best_s.notes,
                "legendaries": best_s.legendary_count,
            }
        )
    return results, timeline, yuntal_mins


def first_minute_with(snaps: List[Snapshot], pred) -> Optional[int]:
    for s in snaps:
        if pred(s):
            return s.minute
    return None


def second_item_isolated_delta(
    name: str,
    path: List[str],
    snaps: List[Snapshot],
    yuntal_min: Optional[int],
    role: str = "adc",
) -> Tuple[float, float, int, List[str]]:
    """Lucky ADC+mid overkill added by the 2nd legendary, same minute."""
    second = next((s for s in snaps if s.legendary_count >= 2), None)
    if second is None:
        last = snaps[-1]
        return 0.0, 0.0, last.minute, last.items
    one_path = truncate_after_n_legendaries(path, 1)
    without = compute_snapshot(name, one_path, second.minute, yuntal_min, role)
    d_adc = second.lucky_adc - without.lucky_adc
    d_mid = second.lucky_mid - without.lucky_mid
    legs = [n for n in second.items if n in LEGENDARIES]
    return d_adc, d_mid, second.minute, legs


def summarize(results, timeline, yuntal_mins) -> str:
    lines = []
    lines.append("=" * 82)
    lines.append("SENNA — 2ND-ITEM BURST / OVERKILL ADC+MID  (Wild Rift Patch 7.3)")
    lines.append("Playstyle: dragon-lane farmer | Combo: R → W → Q → autos in 2.5s")
    lines.append("Metric: lucky + expected overkill ratio vs full-HP ADC and mid")
    lines.append("=" * 82)
    lines.append("")
    lines.append("GOLD / LEVEL / MIST / TARGETS")
    lines.append(
        f"  {'Min':>3}  {'Gold':>6}  {'Lvl':>3}  {'Mist':>4}  "
        f"{'ADC HP':>7}  {'ADC Arm':>7}  {'Mid HP':>7}"
    )
    for m in range(1, GAME_MINUTES + 1):
        if m in (1, 6, 8, 10, 11, 12, 13, 14, 16, 18, 20) or m % 4 == 0:
            lines.append(
                f"  {m:>3}  {gold_at_minute(m):>6}  {level_at_minute(m):>3}  "
                f"{mist_at_minute(m):>4}  {adc_hp(m):>7.0f}  {adc_armor(m):>7.0f}  "
                f"{mid_hp(m):>7.0f}"
            )

    lines.append("")
    lines.append("-" * 82)
    lines.append("MINUTE-BY-MINUTE OPTIMAL (overkill score, 2-item spike preferred)")
    lines.append("-" * 82)
    for row in timeline:
        if row["minute"] % 2 != 0 and row["minute"] not in (1, 9, 11, 13):
            continue
        item_short = " › ".join(row["items"][:5])
        if len(row["items"]) > 5:
            item_short += " › …"
        ka = "KILL" if row["kill_adc"] else "live"
        km = "KILL" if row["kill_mid"] else "live"
        lines.append(
            f"  {row['minute']:>2}:00 | ADC {row['lucky_adc']:>5.0f} ({row['ok_adc']*100:>5.0f}% {ka}) | "
            f"mid {row['lucky_mid']:>5.0f} ({row['ok_mid']*100:>5.0f}% {km}) | {row['winner']}"
        )
        lines.append(f"         items: {item_short}")
        lines.append(f"         {row['notes']}")

    lines.append("")
    lines.append("-" * 82)
    lines.append("BUILD COMPARISON — LUCKY OVERKILL @ 2nd-item window")
    lines.append("-" * 82)
    hdr = (
        f"  {'Build':<28} {'10:00':>6} {'12:00':>6} {'14:00':>6} "
        f"{'ADC%':>6} {'Mid%':>6} {'2ndΔ':>7} {'Both':>5}"
    )
    lines.append(hdr)

    ranking = []
    for name, snaps in results.items():
        b10 = 0.5 * (snaps[9].overkill_adc_lucky + snaps[9].overkill_mid_lucky)
        b12 = 0.5 * (snaps[11].overkill_adc_lucky + snaps[11].overkill_mid_lucky)
        b14 = 0.5 * (snaps[13].overkill_adc_lucky + snaps[13].overkill_mid_lucky)
        # Weight the asked window (10–15) much harder than late 4-item paper
        score_sum = 0.0
        wsum = 0.0
        for s in snaps:
            if 10 <= s.minute <= 15:
                w = 2.4
            elif 8 <= s.minute <= 9:
                w = 1.1
            elif s.minute < 8:
                w = 0.5
            else:
                w = 0.45
            score_sum += burst_score(s) * w
            wsum += w
        eff = score_sum / wsum

        d_adc, d_mid, second_min, legs = second_item_isolated_delta(
            name, BUILD_PATHS[name], snaps, yuntal_mins[name]
        )
        second = next((s for s in snaps if s.legendary_count >= 2), snaps[-1])
        both = int(second.kill_adc_lucky) + int(second.kill_mid_lucky)
        both_exp = int(second.kill_adc_exp) + int(second.kill_mid_exp)
        ranking.append(
            (
                eff,
                b12,
                name,
                b10,
                b12,
                b14,
                snaps,
                d_adc,
                d_mid,
                second_min,
                second,
                legs,
                both,
                both_exp,
            )
        )
        both_s = f"{both}/2"
        lines.append(
            f"  {name:<28} {b10*100:>5.0f}% {b12*100:>5.0f}% {b14*100:>5.0f}% "
            f"{second.overkill_adc_lucky*100:>5.0f}% {second.overkill_mid_lucky*100:>5.0f}% "
            f"{(d_adc+d_mid)/2:>+7.0f} {both_s:>5}"
        )

    ranking.sort(key=lambda x: (x[0], x[1]), reverse=True)

    lines.append("")
    lines.append("-" * 82)
    lines.append("2ND ITEM SPIKE  (isolated Δ lucky damage, same minute with vs without 2nd)")
    lines.append("-" * 82)
    for row in ranking:
        name, snaps, d_adc, d_mid, second_min, second, legs = (
            row[2], row[6], row[7], row[8], row[9], row[10], row[11]
        )
        ka = "KILL" if second.kill_adc_lucky else "live"
        km = "KILL" if second.kill_mid_lucky else "live"
        ke = "also expected" if second.kill_adc_exp and second.kill_mid_exp else "lucky only"
        lines.append(
            f"  {name:<28} 2nd ~{second_min}:00  ADC {second.lucky_adc:.0f} {ka}  "
            f"mid {second.lucky_mid:.0f} {km}  Δ {(d_adc+d_mid)/2:+.0f}  [{', '.join(legs[:2])}]  {ke}"
        )

    lines.append("")
    lines.append("-" * 82)
    lines.append("EXPECTED (no lucky crits) vs ADC / mid at the 2nd-item minute")
    lines.append("-" * 82)
    for row in ranking:
        name, second = row[2], row[10]
        ka = "KILL" if second.kill_adc_exp else "live"
        km = "KILL" if second.kill_mid_exp else "live"
        lines.append(
            f"  {name:<28} ADC {second.exp_adc:>6.0f} ({second.overkill_adc_exp*100:>4.0f}% {ka})  "
            f"mid {second.exp_mid:>6.0f} ({second.overkill_mid_exp*100:>4.0f}% {km})  "
            f"crit {second.crit*100:.0f}%  {second.autos} AA"
        )

    best = ranking[0]
    winner_name = best[2]
    snaps = best[6]
    win_second = best[10]
    d_adc, d_mid = best[7], best[8]

    def at2(sn):
        return next((s for s in sn if s.legendary_count >= 2), sn[-1])

    w2 = at2(results[winner_name])
    dc2 = at2(results["Dusk → Collector"])
    hd2 = at2(results["Hexoptics → Dusk"])
    ie2 = at2(results["Collector → IE"])
    yt2 = at2(results["Yun Tal → Collector"])
    rf2 = at2(results["RFC → Collector"])
    fh2 = at2(results["Fiendhunter → Collector"])
    er2 = at2(results["ER → Collector"])
    yu2 = at2(results["Dusk → Youmuu"])

    two_m = first_minute_with(snaps, lambda s: s.legendary_count >= 2)
    dusk_m = first_minute_with(snaps, lambda s: s.has_dusk)
    ser_m = first_minute_with(snaps, lambda s: s.has_serylda)

    lines.append("")
    lines.append("-" * 82)
    lines.append("VERDICT")
    lines.append("-" * 82)
    lines.append(f"  Best path (2nd-item overkill ADC + mid): {winner_name}")
    lines.append(
        f"  Window-weighted score: {best[0]:.3f} | 2nd legendary ~{two_m}:00"
    )
    if dusk_m:
        lines.append(f"  Duskblade (Nightstalker) online: ~{dusk_m}:00")
    if ser_m:
        lines.append(f"  Serylda 35% pen online:          ~{ser_m}:00  (the 2nd-item peak)")
    lines.append(
        f"  At 2nd item vs ADC ~{adc_hp(w2.minute):.0f} HP / {adc_armor(w2.minute):.0f} armor: "
        f"lucky {w2.lucky_adc:.0f} ({w2.overkill_adc_lucky*100:.0f}%) "
        f"{'OVERKILL' if w2.kill_adc_lucky else 'lives'}"
        f" | expected {w2.exp_adc:.0f} ({w2.overkill_adc_exp*100:.0f}%)"
    )
    lines.append(
        f"  At 2nd item vs mid ~{mid_hp(w2.minute):.0f} HP / {mid_armor(w2.minute):.0f} armor: "
        f"lucky {w2.lucky_mid:.0f} ({w2.overkill_mid_lucky*100:.0f}%) "
        f"{'OVERKILL' if w2.kill_mid_lucky else 'lives'}"
        f" | expected {w2.exp_mid:.0f} ({w2.overkill_mid_exp*100:.0f}%)"
    )
    lines.append(
        f"  Isolated 2nd-item Δ: ADC {d_adc:+.0f} / mid {d_mid:+.0f} per combo"
    )
    lines.append("")
    lines.append("  WHY DUSK → SERYLDA IS THE 2ND-ITEM OVERKILL:")
    lines.append("  • Senna has no AD growth. The combo is bonus AD × Q/W/R")
    lines.append("    (0.6 / 0.7 / 1.2) plus Relic 20% AD on-hit. Those spells")
    lines.append("    DO NOT CRIT in 7.3 — only autos do, at 90% of 200%.")
    lines.append("  • Item 1 Duskblade: 55 AD + 18 lethality + Nightstalker")
    lines.append("    60–160. Already a kill threat with boots + a Dirk.")
    lines.append("  • Item 2 Serylda: 50 AD + 35% pen. %pen applies to the")
    lines.append("    WHOLE combo (R/W/Q/autos), then Dusk+boots lethality")
    lines.append("    shaves the rest. Collector's 25% crit only multiplies")
    lines.append(
        f"    2 autos, so Dusk→Collector is {dc2.overkill_adc_lucky*100:.0f}%/{dc2.overkill_mid_lucky*100:.0f}% "
        f"vs Serylda {w2.overkill_adc_lucky*100:.0f}%/{w2.overkill_mid_lucky*100:.0f}%."
    )
    lines.append("  • Expected damage (no lucky crits) still overkills both")
    lines.append("    roles — you do not need a high-roll auto.")
    lines.append(
        f"  • Isolated 2nd-item Δ ~{(d_adc+d_mid)/2:.0f} is the biggest spike "
        "in the table."
    )
    lines.append("")
    lines.append("  EARLIEST 2-ITEM KILL: Hexoptics → Dusk")
    lines.append(
        f"    2nd legendary ~{hd2.minute}:00 (a minute sooner). Hexoptics does"
    )
    lines.append("    not share Dirk/Caulfield with Duskblade, so the 2nd item")
    lines.append(
        f"    completes earlier. ADC {hd2.lucky_adc:.0f} ({hd2.overkill_adc_lucky*100:.0f}%) / "
        f"mid {hd2.lucky_mid:.0f} ({hd2.overkill_mid_lucky*100:.0f}%), also on expected."
    )
    lines.append("    Take this if the game is ending at 13. Take Serylda if you")
    lines.append("    want the fatter overkill vs anyone who bought a cloth.")
    lines.append("")
    lines.append("  WHY 7.3 'MAGNETIC BLASTER REPLACEMENTS' MISS THE SPIKE:")
    lines.append(
        f"  • RFC → Collector 2nd ~{rf2.minute}:00  ADC lucky {rf2.lucky_adc:.0f} "
        f"({rf2.overkill_adc_lucky*100:.0f}%) — RFC has 0 AD."
    )
    lines.append(
        f"  • Fiendhunter → Collector 2nd ~{fh2.minute}:00  ADC {fh2.lucky_adc:.0f} "
        f"({fh2.overkill_adc_lucky*100:.0f}%). R-barrage guaranteed crits at 80%"
    )
    lines.append("    of normal crit, which is WORSE than Senna's native 90%")
    lines.append("    modifier unless the auto was already going to crit.")
    lines.append(
        f"  • Yun Tal → Collector 2nd ~{yt2.minute}:00  ADC {yt2.lucky_adc:.0f} "
        f"({yt2.overkill_adc_lucky*100:.0f}%). AS ratio is now 0.4 (real AS),"
    )
    lines.append("    but a 2.5s combo still only fits ~2 autos. Stacking 25%")
    lines.append("    crit is a 3rd-item story.")
    lines.append(
        f"  • Collector → IE 2nd ~{ie2.minute}:00  ADC {ie2.lucky_adc:.0f}. "
        "IE is 3500g so the spike is late, and 230% crit does not"
    )
    lines.append("    touch Q/W/R. Capstone after you already one-shot.")
    lines.append(
        f"  • ER → Collector 2nd ~{er2.minute}:00  ADC {er2.lucky_adc:.0f}. "
        "Spellblade is 135% BASE AD. Senna's base AD is 54 forever."
    )
    lines.append(
        f"  • Dusk → Youmuu 2nd ~{yu2.minute}:00  ADC {yu2.lucky_adc:.0f}. "
        "Two lethality items double dip flat pen on already-low"
    )
    lines.append("    armor; Serylda's 35% is the new multiplier.")
    lines.append("")
    lines.append("  RECOMMENDED (2nd-item overkill ADC + mid, patch 7.3):")
    lines.append("  1) Long Sword → Serrated Dirk")
    lines.append("  2) Duskblade of Draktharr   (~6:00, Nightstalker = item-1 spike)")
    lines.append("  3) Boots of Dynamism        (+8 lethality)")
    lines.append("  4) Serylda's Grudge         (~14:00, 35% pen — 2ND ITEM PEAK)")
    lines.append("     Alt if the game is a 13-min stomp: Hexoptics → Duskblade")
    lines.append("  5) Collector / Hexoptics / IE   (execute, range, or crit cap)")
    lines.append("  6) GA / Mortal / Edge of Night")
    lines.append("")
    lines.append("  Skill: max Q → W. R whenever. Combo: R (fog) → W root →")
    lines.append("  Q (mist extract + Relic) → auto (Nightstalker + crit).")
    lines.append("  Runes: Fleet, Empowered Attack, Brutal, Cut Down.")
    lines.append("")
    lines.append("  Trap: RFC / Fiendhunter / Yun Tal first — 7.3 split Magnetic")
    lines.append("  Blaster into 0-AD Zeal items. Senna cannot afford 0 AD.")
    lines.append("  Trap: Essence Reaver — spellblade scales with base AD.")
    lines.append("  Trap: Collector 2nd — crit/execute on 2 autos, spells ignore it.")
    lines.append("  Trap: IE 2nd — 3500g delay + autos-only crit amp.")
    lines.append("  Trap: Youmuu 2nd — more flat pen on armor that is already gone.")
    lines.append("=" * 82)
    return "\n".join(lines)


def export_json(
    results, timeline, path: str, meta_extra: Optional[dict] = None
) -> None:
    payload = {
        "meta": {
            "champion": "Senna",
            "role": "ADC (dragon lane)",
            "patch": "7.3",
            "game_minutes": GAME_MINUTES,
            "playstyle": "2nd-item burst overkill ADC+mid",
            "combo": "R → W → Q → autos",
            "burst_window": BURST_WINDOW,
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
                    "crit": s.crit,
                    "lethality": s.lethality,
                    "legendary_count": s.legendary_count,
                    "mist": s.mist,
                    "autos": s.autos,
                    "exp_adc": s.exp_adc,
                    "lucky_adc": s.lucky_adc,
                    "exp_mid": s.exp_mid,
                    "lucky_mid": s.lucky_mid,
                    "overkill_adc_exp": s.overkill_adc_exp,
                    "overkill_adc_lucky": s.overkill_adc_lucky,
                    "overkill_mid_exp": s.overkill_mid_exp,
                    "overkill_mid_lucky": s.overkill_mid_lucky,
                    "kill_adc_exp": s.kill_adc_exp,
                    "kill_adc_lucky": s.kill_adc_lucky,
                    "kill_mid_exp": s.kill_mid_exp,
                    "kill_mid_lucky": s.kill_mid_lucky,
                    "notes": s.notes,
                }
                for s in snaps
            ]
            for name, snaps in results.items()
        },
    }
    if meta_extra:
        payload["meta"].update(meta_extra)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def summarize_support(
    results: Dict[str, List[Snapshot]],
    contrast: Dict[str, List[Snapshot]],
    timeline: List[dict],
    yuntal_mins: Dict[str, Optional[int]],
) -> str:
    lines = []
    lines.append("=" * 82)
    lines.append("SENNA SUPPORT — CRIT, 2ND-ITEM PEAK + LATE SCALE  (WR Patch 7.3)")
    lines.append("Playstyle: fasting support (Scythe + souls) | Combo: R → W → Q → autos")
    lines.append("Metric: overkill ADC+mid at item 2, then still climbing at 18–20")
    lines.append("=" * 82)
    lines.append("")
    lines.append("GOLD / LEVEL / MIST (fasting support)")
    lines.append(
        f"  {'Min':>3}  {'Gold':>6}  {'Lvl':>3}  {'Mist':>4}  "
        f"{'ADC HP':>7}  {'ADC Arm':>7}  {'Mist crit':>9}"
    )
    for m in (1, 5, 8, 10, 12, 14, 15, 16, 18, 20):
        mist = support_mist(m)
        lines.append(
            f"  {m:>3}  {support_gold(m):>6}  {support_level(m):>3}  "
            f"{mist:>4}  {adc_hp(m):>7.0f}  {adc_armor(m):>7.0f}  "
            f"{10 * (mist // 20):>8}%"
        )

    lines.append("")
    lines.append("-" * 82)
    lines.append("MINUTE-BY-MINUTE OPTIMAL (crit paths only, 2nd-item + late)")
    lines.append("-" * 82)
    for row in timeline:
        if row["minute"] % 2 != 0 and row["minute"] not in (1, 11, 13, 15):
            continue
        item_short = " › ".join(row["items"][:6])
        if len(row["items"]) > 6:
            item_short += " › …"
        ka = "KILL" if row["kill_adc"] else "live"
        km = "KILL" if row["kill_mid"] else "live"
        lines.append(
            f"  {row['minute']:>2}:00 | ADC {row['lucky_adc']:>5.0f} "
            f"({row['ok_adc']*100:>5.0f}% {ka}) | "
            f"mid {row['lucky_mid']:>5.0f} ({row['ok_mid']*100:>5.0f}% {km}) | "
            f"{row['winner']}"
        )
        lines.append(f"         items: {item_short}")
        lines.append(f"         {row['notes']}")

    lines.append("")
    lines.append("-" * 82)
    lines.append("CRIT BUILD COMPARISON — overkill @ 2nd item / 16:00 / 20:00")
    lines.append("-" * 82)
    lines.append(
        f"  {'Build':<28} {'2nd@':>5} {'ADC%':>6} {'Mid%':>6} "
        f"{'16:00':>6} {'20:00':>6} {'2ndΔ':>7} {'Late':>5}"
    )

    ranking = []
    for name, snaps in results.items():
        d_adc, d_mid, second_min, legs = second_item_isolated_delta(
            name, SUPPORT_CRIT_PATHS[name], snaps, yuntal_mins[name], "support"
        )
        second = next((s for s in snaps if s.legendary_count >= 2), snaps[-1])
        s16, s20 = snaps[15], snaps[19]
        late = 0.5 * (s20.overkill_adc_lucky + s20.overkill_mid_lucky)
        mix2 = 0.5 * (second.overkill_adc_lucky + second.overkill_mid_lucky)
        peak = mix_ok(second)
        late_m = mix_ok(s20)
        # Dual goal: fat early 2nd item AND still climbing at 20 with IE.
        earliness = 1.0 + 0.035 * max(0, 17 - second.minute)
        ie_late = 1.12 if s20.has_ie else 0.94
        climb = 1.06 if late >= mix2 - 0.02 else 0.92
        pen2 = 1.08 if second.has_serylda else 1.0
        both2 = 1.06 if second.kill_adc_lucky and second.kill_mid_lucky else 1.0
        both2e = 1.04 if second.kill_adc_exp and second.kill_mid_exp else 1.0
        eff = (
            (0.55 * peak + 0.45 * late_m)
            * earliness
            * ie_late
            * climb
            * pen2
            * both2
            * both2e
        )
        ranking.append(
            (eff, late, name, second, s16, s20, d_adc, d_mid, second_min, legs, snaps)
        )
    ranking.sort(key=lambda x: (x[0], x[1]), reverse=True)

    for row in ranking:
        name, second, s16, s20, d_adc, d_mid, second_min = (
            row[2], row[3], row[4], row[5], row[6], row[7], row[8]
        )
        mix2 = 0.5 * (second.overkill_adc_lucky + second.overkill_mid_lucky)
        late = 0.5 * (s20.overkill_adc_lucky + s20.overkill_mid_lucky)
        late_s = "UP" if late >= mix2 - 0.02 else "dn"
        lines.append(
            f"  {name:<28} {second_min:>4}:00 "
            f"{second.overkill_adc_lucky*100:>5.0f}% {second.overkill_mid_lucky*100:>5.0f}% "
            f"{0.5*(s16.overkill_adc_lucky+s16.overkill_mid_lucky)*100:>5.0f}% "
            f"{late*100:>5.0f}% {(d_adc+d_mid)/2:>+7.0f} {late_s:>5}"
        )

    lines.append("")
    lines.append("-" * 82)
    lines.append("2ND ITEM SPIKE  (isolated Δ, same minute with vs without 2nd)")
    lines.append("-" * 82)
    for row in ranking:
        name, second, d_adc, d_mid, second_min, legs = (
            row[2], row[3], row[6], row[7], row[8], row[9]
        )
        ka = "KILL" if second.kill_adc_lucky else "live"
        km = "KILL" if second.kill_mid_lucky else "live"
        ke = (
            "also expected"
            if second.kill_adc_exp and second.kill_mid_exp
            else "lucky only"
        )
        lines.append(
            f"  {name:<28} 2nd ~{second_min}:00  ADC {second.lucky_adc:.0f} {ka}  "
            f"mid {second.lucky_mid:.0f} {km}  Δ {(d_adc+d_mid)/2:+.0f}  "
            f"[{', '.join(legs[:2])}]  {ke}"
        )

    lines.append("")
    lines.append("-" * 82)
    lines.append("LATE (20:00) vs 2ND-ITEM MINUTE  — did it keep scaling?")
    lines.append("-" * 82)
    for row in ranking:
        name, second, s20 = row[2], row[3], row[5]
        dlt = 0.5 * (
            (s20.overkill_adc_lucky - second.overkill_adc_lucky)
            + (s20.overkill_mid_lucky - second.overkill_mid_lucky)
        )
        lines.append(
            f"  {name:<28} 2nd {0.5*(second.overkill_adc_lucky+second.overkill_mid_lucky)*100:>5.0f}%  "
            f"20:00 {0.5*(s20.overkill_adc_lucky+s20.overkill_mid_lucky)*100:>5.0f}%  "
            f"Δ {dlt*100:+.0f}pp  crit {s20.crit*100:.0f}%  AD {s20.ad:.0f}  "
            f"{'IE' if s20.has_ie else 'no IE'}"
        )

    lines.append("")
    lines.append("-" * 82)
    lines.append("LETHALITY CONTRAST (same support gold / fasting Mist)")
    lines.append("-" * 82)
    for name, snaps in contrast.items():
        second = next((s for s in snaps if s.legendary_count >= 2), snaps[-1])
        s20 = snaps[19]
        lines.append(
            f"  {name:<32} 2nd ~{second.minute}:00  "
            f"ADC {second.overkill_adc_lucky*100:.0f}%  "
            f"mid {second.overkill_mid_lucky*100:.0f}%  |  "
            f"20:00 ADC {s20.overkill_adc_lucky*100:.0f}%  "
            f"mid {s20.overkill_mid_lucky*100:.0f}%"
        )

    best = ranking[0]
    winner_name = best[2]
    snaps = best[10]
    w2 = best[3]
    w20 = best[5]
    d_adc, d_mid = best[6], best[7]

    def at2(sn):
        return next((s for s in sn if s.legendary_count >= 2), sn[-1])

    hex_col = at2(results["Hex → Collector → IE"])
    hex_ie = at2(results["Hex → IE → Mortal"])
    rfc2 = at2(results["RFC → IE"])
    yun2 = at2(results["Yun Tal → IE"])
    hex_mort = at2(results["Hex → Mortal → IE"])
    col_mort = at2(results["Collector → Mortal → IE"])
    col_ie = at2(results["Collector → IE → Mortal"])
    col_dyn = at2(results["Collector → Mortal + Dynamism"])
    dusk_ser = at2(contrast["Dusk → Serylda (lethality)"])
    dusk20 = contrast["Dusk → Serylda (lethality)"][19]
    win20_mix = 0.5 * (w20.overkill_adc_lucky + w20.overkill_mid_lucky)
    dusk20_mix = 0.5 * (dusk20.overkill_adc_lucky + dusk20.overkill_mid_lucky)
    dyn20 = results["Collector → Mortal + Dynamism"][19]

    two_m = first_minute_with(snaps, lambda s: s.legendary_count >= 2)
    hex_m = first_minute_with(snaps, lambda s: s.has_hex)
    ie_m = first_minute_with(snaps, lambda s: s.has_ie)
    col_m = first_minute_with(snaps, lambda s: s.has_collector)
    mort_m = first_minute_with(snaps, lambda s: s.has_serylda)

    lines.append("")
    lines.append("-" * 82)
    lines.append("VERDICT")
    lines.append("-" * 82)
    lines.append(f"  Best crit support path (2nd-item peak + late): {winner_name}")
    lines.append(
        f"  Window-weighted score: {best[0]:.3f} | 2nd legendary ~{two_m}:00"
    )
    if col_m:
        lines.append(f"  Collector (execute + 25% crit)   ~{col_m}:00")
    if hex_m:
        lines.append(f"  Hexoptics (range amp + 25% crit) ~{hex_m}:00")
    if mort_m:
        lines.append(f"  Mortal / %pen (2nd-item peak)    ~{mort_m}:00")
    if ie_m:
        lines.append(f"  Infinity Edge (230% crit)        ~{ie_m}:00")
    else:
        lines.append("  Infinity Edge: NOT finished by 20:00 on this gold curve")
    lines.append(
        f"  2nd item vs ADC: lucky {w2.lucky_adc:.0f} ({w2.overkill_adc_lucky*100:.0f}%) "
        f"{'OVERKILL' if w2.kill_adc_lucky else 'lives'} | "
        f"expected {w2.exp_adc:.0f} ({w2.overkill_adc_exp*100:.0f}%)"
    )
    lines.append(
        f"  2nd item vs mid: lucky {w2.lucky_mid:.0f} ({w2.overkill_mid_lucky*100:.0f}%) "
        f"{'OVERKILL' if w2.kill_mid_lucky else 'lives'} | "
        f"expected {w2.exp_mid:.0f} ({w2.overkill_mid_exp*100:.0f}%)"
    )
    lines.append(
        f"  20:00 vs ADC: lucky {w20.lucky_adc:.0f} ({w20.overkill_adc_lucky*100:.0f}%)  "
        f"crit {w20.crit*100:.0f}%  AD {w20.ad:.0f}  mist {w20.mist}  "
        f"{'IE' if w20.has_ie else 'no IE'}"
    )
    lines.append(
        f"  Isolated 2nd-item Δ: ADC {d_adc:+.0f} / mid {d_mid:+.0f}"
    )
    lines.append("")
    lines.append("  WHY THIS PEAKS AT 2 AND STILL SCALES:")
    lines.append("  • Fasting Mist is free crit (10%/20 stacks) + 1.25 AD/soul.")
    lines.append("    Support hits ~100 Mist at 20:00 = 50% crit and 125 AD")
    lines.append("    before items. Item crit stacks on top of that.")
    lines.append("  • Q/W/R still do not crit. Mortal's 30% pen (or LDR 35%)")
    lines.append("    is the 2nd-item overkill among crit items — same lesson")
    lines.append("    as ADC Dusk → Serylda, on a crit chassis.")
    lines.append("  • Collector 1st (3000): 50 AD + 10 lethality + 5% execute")
    lines.append("    + 25% crit. Online ~8:00, already a kill threat with souls.")
    lines.append("  • Skip Boots of Dynamism. 1200g delays 2nd item from ~14")
    lines.append("    to ~16 and leaves you 400g short of IE at 20:00.")
    lines.append(
        f"    Dynamism path 2nd ~{col_dyn.minute}:00 "
        f"({col_dyn.overkill_adc_lucky*100:.0f}% ADC), 20:00 "
        f"{'IE' if dyn20.has_ie else 'no IE'}."
    )
    lines.append("  • Late: IE 230% × Senna's 90% modifier = 207% autos, and")
    lines.append("    soul crit is high enough that expected ≈ lucky.")
    lines.append(
        f"  • Collector→Mortal 2nd ~{col_mort.minute}:00 "
        f"({col_mort.overkill_adc_lucky*100:.0f}% ADC); "
        f"Hex→Mortal 2nd ~{hex_mort.minute}:00 "
        f"({hex_mort.overkill_adc_lucky*100:.0f}% ADC)."
    )
    lines.append(
        f"  • Hex→Collector 2nd ~{hex_col.minute}:00 "
        f"({hex_col.overkill_adc_lucky*100:.0f}% ADC) — no %pen, smaller spike."
    )
    lines.append(
        f"  • Hex→IE 2nd ~{hex_ie.minute}:00 "
        f"({hex_ie.overkill_adc_lucky*100:.0f}% ADC); "
        f"Collector→IE 2nd ~{col_ie.minute}:00 "
        f"({col_ie.overkill_adc_lucky*100:.0f}% ADC) — IE 2nd is a minute late."
    )
    lines.append("")
    lines.append("  LETHALITY ON SUPPORT GOLD:")
    lines.append(
        f"  • Dusk→Serylda 2nd ~{dusk_ser.minute}:00 "
        f"ADC {dusk_ser.overkill_adc_lucky*100:.0f}% / "
        f"mid {dusk_ser.overkill_mid_lucky*100:.0f}%."
    )
    lines.append(
        f"  • At 20:00 lethality mix {dusk20_mix*100:.0f}% vs winner "
        f"{win20_mix*100:.0f}%. Nightstalker is a flat proc; soul crit"
    )
    lines.append("    does not multiply it. Crit items ride the Mist curve.")
    lines.append("    Dusk-first (above) is the primary recommendation.")
    lines.append("    This ranking is the crit-only fallback.")
    lines.append("")
    lines.append("  TRAPS (same as ADC, worse on support gold):")
    lines.append(
        f"  • RFC → IE 2nd ~{rfc2.minute}:00  ADC {rfc2.overkill_adc_lucky*100:.0f}% "
        "— RFC has 0 AD."
    )
    lines.append(
        f"  • Yun Tal → IE 2nd ~{yun2.minute}:00  ADC {yun2.overkill_adc_lucky*100:.0f}% "
        "— stacking 25% crit is slow; souls already give crit."
    )
    lines.append("    Yun Tal / Fiendhunter can look best at 20:00 once IE is")
    lines.append("    up, but they miss the 2nd-item peak.")
    lines.append("  • Essence Reaver: 135% of base AD 54. Skip.")
    lines.append("  • Fiendhunter: 0 AD + 80% crit modifier after R. Skip.")
    lines.append("  • Dynamism before item 2: gold sink on a crit build.")
    lines.append("  • Galeforce 2nd is IE: looks strong 16–20 because 230% is")
    lines.append("    already on, but the 14:00 Mortal spike is fatter.")
    lines.append("")
    rec_legs = [
        n
        for n in SUPPORT_CRIT_PATHS[winner_name]
        if n in LEGENDARIES
    ]
    lines.append("  RECOMMENDED (crit support, 2nd-item peak, stronger late):")
    lines.append("  1) Spectral Sickle → Black Mist Scythe (~5:00)")
    labels = {
        "The Collector": "execute + 25% crit",
        "Hexoptics C44": "range + 25% crit",
        "Mortal Reminder": "30% pen — 2ND ITEM PEAK",
        "Lord Dominik's Regards": "35% pen — 2ND ITEM PEAK",
        "Infinity Edge": "late 230% — souls already crit",
        "Galeforce": "dash + 25% crit",
        "Yun Tal Wildarrows": "stacked crit (slow)",
        "Stormrazor": "energized + 25% crit",
    }
    for i, item in enumerate(rec_legs[:3], start=2):
        tag = labels.get(item, "")
        extra = f"  ({tag})" if tag else ""
        lines.append(f"  {i}) {item:<22}{extra}")
    if rec_legs and rec_legs[0] == "The Collector":
        lines.append("     Alt if you want range first: Hexoptics → Mortal → IE")
    lines.append("  Do not buy Dynamism before the 2nd legendary.")
    lines.append("")
    lines.append("  Skill: max Q → W. Fasting: ADC last-hits, you take souls.")
    lines.append("  Combo: R → W → Q → auto. Runes: First Strike,")
    lines.append("  Brutal, Empowered Attack, Cut Down (see full-build section).")
    lines.append("=" * 82)
    return "\n".join(lines)


def self_check_support(
    results: Dict[str, List[Snapshot]],
    contrast: Dict[str, List[Snapshot]],
) -> None:
    def second(snaps):
        return next(s for s in snaps if s.legendary_count >= 2)

    hex_col = second(results["Hex → Collector → IE"])
    hex_ie = second(results["Hex → IE → Mortal"])
    rfc = second(results["RFC → IE"])
    yun = second(results["Yun Tal → IE"])
    col_mort = second(results["Collector → Mortal → IE"])
    dyn = second(results["Collector → Mortal + Dynamism"])

    # Mortal 2nd (no Dynamism) lands at or before IE 2nd and RFC
    assert col_mort.minute <= hex_ie.minute, (col_mort.minute, hex_ie.minute)
    assert col_mort.lucky_adc > rfc.lucky_adc, (col_mort.lucky_adc, rfc.lucky_adc)
    # Yun Tal item-1 is weaker; its IE 2nd can win lucky later
    yun12 = results["Yun Tal → IE"][11]
    hex12 = results["Hex → Collector → IE"][11]
    assert hex12.exp_adc > yun12.exp_adc, (hex12.exp_adc, yun12.exp_adc)
    # 2nd item must land before "late"
    assert col_mort.minute <= 16, col_mort.minute
    # Dynamism delays the 2nd legendary
    assert col_mort.minute <= dyn.minute, (col_mort.minute, dyn.minute)

    s20 = results["Collector → Mortal → IE"][19]
    mix2 = 0.5 * (col_mort.overkill_adc_lucky + col_mort.overkill_mid_lucky)
    mix20 = 0.5 * (s20.overkill_adc_lucky + s20.overkill_mid_lucky)
    assert mix20 >= mix2 - 0.05, (mix20, mix2)
    assert col_mort.lucky_adc > hex_col.lucky_adc, (
        col_mort.lucky_adc,
        hex_col.lucky_adc,
    )
    assert s20.has_ie, s20.items
    assert s20.mist >= 90, s20.mist
    assert yun.minute >= col_mort.minute
    assert contrast["Dusk → Serylda (lethality)"][19].mist >= 90
    # Dual-goal winner must not be the Dynamism gold-sink (no IE by 20)
    dyn20 = results["Collector → Mortal + Dynamism"][19]
    assert s20.has_ie and not dyn20.has_ie


def self_check(results: Dict[str, List[Snapshot]]) -> None:
    dusk = results["Dusk → Collector"]
    rfc = results["RFC → Collector"]
    fiend = results["Fiendhunter → Collector"]
    er = results["ER → Collector"]
    serylda = results["Collector → Serylda"]

    def second(snaps):
        return next(s for s in snaps if s.legendary_count >= 2)

    d2, r2, f2, e2, s2 = map(second, (dusk, rfc, fiend, er, serylda))
    ser2 = second(results["Dusk → Serylda"])
    hd2 = second(results["Hexoptics → Dusk"])
    col2 = second(results["Dusk → Collector"])

    # Lethality 2-item must beat 0-AD Zeal first items vs ADC
    assert d2.lucky_adc > r2.lucky_adc, (d2.lucky_adc, r2.lucky_adc)
    assert d2.lucky_adc > f2.lucky_adc, (d2.lucky_adc, f2.lucky_adc)
    assert d2.lucky_adc > e2.lucky_adc, (d2.lucky_adc, e2.lucky_adc)

    # 2nd item must actually overkill ADC on the lethality path (lucky)
    assert d2.kill_adc_lucky, (d2.lucky_adc, d2.overkill_adc_lucky, d2.minute)
    assert d2.kill_mid_lucky, (d2.lucky_mid, d2.overkill_mid_lucky)

    # Dusk → Serylda is the overkill 2nd (spells don't crit; %pen hits R/W/Q)
    assert ser2.lucky_adc > col2.lucky_adc, (ser2.lucky_adc, col2.lucky_adc)
    assert ser2.kill_adc_exp and ser2.kill_mid_exp
    assert hd2.minute <= ser2.minute
    assert hd2.kill_adc_lucky and hd2.kill_mid_lucky

    # Duskblade comes online before RFC's 2nd item (gold)
    d1 = first_minute_with(dusk, lambda s: s.has_dusk)
    assert d1 is not None and d1 <= 10, d1

    # %pen 2nd should not beat Dusk 2nd vs these squishies
    col_dusk = second(results["Collector → Dusk"])
    assert col_dusk.lucky_adc >= s2.lucky_adc * 0.98, (
        col_dusk.lucky_adc,
        s2.lucky_adc,
    )


CD = 0.0657  # Cut Down 7.2 nerf (8% → 6.57%)

SUPPORT_RUNE_PAGES: List[RunePage] = [
    RunePage("First Strike · Brutal · Emp · Cut Down", "first_strike", cut_down_pct=CD),
    RunePage("First Strike · Brutal · Emp · Coup", "first_strike", precision="coup", cut_down_pct=CD),
    RunePage(
        "First Strike · Brutal · Emp · Gathering Storm",
        "first_strike",
        precision="none",
        gathering_storm=True,
        cut_down_pct=CD,
    ),
    RunePage(
        "First Strike · Brutal · Sudden Impact · Cut Down",
        "first_strike",
        empowered=False,
        sudden_impact=True,
        cut_down_pct=CD,
    ),
    RunePage(
        "First Strike · Brutal · Emp · Cheap Shot",
        "first_strike",
        precision="none",
        cheap_shot=True,
        cut_down_pct=CD,
    ),
    RunePage("Electrocute · Brutal · Emp · Cut Down", "electrocute", cut_down_pct=CD),
    RunePage("Dark Harvest · Brutal · Emp · Cut Down", "dark_harvest", cut_down_pct=CD),
    RunePage("Fleet · Brutal · Emp · Cut Down", "fleet", cut_down_pct=CD),
    RunePage("Empowerment · Brutal · Emp · Cut Down", "empowerment", cut_down_pct=CD),
    RunePage("Lethal Tempo · Brutal · Emp · Cut Down", "lethal_tempo", cut_down_pct=CD),
    RunePage("Aery · Brutal · Emp · Cut Down", "aery", cut_down_pct=CD),
    RunePage("Comet · Brutal · Emp · Cut Down", "comet", cut_down_pct=CD),
]


def summarize_dusk_support(
    results: Dict[str, List[Snapshot]],
    timeline: List[dict],
    yuntal_mins: Dict[str, Optional[int]],
    crit_baseline: Optional[Dict[str, List[Snapshot]]] = None,
) -> str:
    lines = []
    lines.append("=" * 82)
    lines.append("SENNA SUPPORT — DUSK FIRST, THEN 2ND-ITEM PEAK  (WR Patch 7.3)")
    lines.append("Playstyle: fasting support | Nightstalker item-1, %pen item-2")
    lines.append("Metric: early Dusk kill threat, fattest 2nd-item overkill")
    lines.append("=" * 82)
    lines.append("")
    lines.append("GOLD / LEVEL / MIST (fasting support)")
    lines.append(
        f"  {'Min':>3}  {'Gold':>6}  {'Lvl':>3}  {'Mist':>4}  "
        f"{'ADC HP':>7}  {'ADC Arm':>7}"
    )
    for m in (1, 5, 8, 10, 12, 14, 16, 18, 20):
        lines.append(
            f"  {m:>3}  {support_gold(m):>6}  {support_level(m):>3}  "
            f"{support_mist(m):>4}  {adc_hp(m):>7.0f}  {adc_armor(m):>7.0f}"
        )

    lines.append("")
    lines.append("-" * 82)
    lines.append("MINUTE-BY-MINUTE OPTIMAL (Dusk-first paths)")
    lines.append("-" * 82)
    for row in timeline:
        if row["minute"] % 2 != 0 and row["minute"] not in (1, 11, 13, 15):
            continue
        item_short = " › ".join(row["items"][:6])
        ka = "KILL" if row["kill_adc"] else "live"
        km = "KILL" if row["kill_mid"] else "live"
        lines.append(
            f"  {row['minute']:>2}:00 | ADC {row['lucky_adc']:>5.0f} "
            f"({row['ok_adc']*100:>5.0f}% {ka}) | "
            f"mid {row['lucky_mid']:>5.0f} ({row['ok_mid']*100:>5.0f}% {km}) | "
            f"{row['winner']}"
        )
        lines.append(f"         items: {item_short}")
        lines.append(f"         {row['notes']}")

    lines.append("")
    lines.append("-" * 82)
    lines.append("DUSK-FIRST 2ND ITEM — overkill @ 2nd / 8:00 (item 1) / 20:00")
    lines.append("-" * 82)
    lines.append(
        f"  {'Build':<28} {'Dusk@':>6} {'2nd@':>5} {'ADC%':>6} "
        f"{'Mid%':>6} {'8:00':>6} {'20:00':>6} {'2ndΔ':>7}"
    )

    ranking = []
    for name, snaps in results.items():
        d_adc, d_mid, second_min, legs = second_item_isolated_delta(
            name, SUPPORT_DUSK_PATHS[name], snaps, yuntal_mins[name], "support"
        )
        second = next((s for s in snaps if s.legendary_count >= 2), snaps[-1])
        s8, s20 = snaps[7], snaps[19]
        dusk_m = first_minute_with(snaps, lambda s: s.has_dusk)
        peak = mix_ok(second)
        late_m = mix_ok(s20)
        early = mix_ok(s8)
        earliness = 1.0 + 0.04 * max(0, 17 - second.minute)
        dusk1 = 1.12 if second.has_dusk else 0.90
        pen2 = 1.10 if second.has_serylda else 1.0
        d1b = 1.0 + 0.04 * max(0, 10 - (dusk_m or 10))
        both2 = 1.06 if second.kill_adc_lucky and second.kill_mid_lucky else 1.0
        both2e = 1.04 if second.kill_adc_exp and second.kill_mid_exp else 1.0
        eff = (
            (0.25 * early + 0.50 * peak + 0.25 * late_m)
            * earliness * dusk1 * pen2 * d1b * both2 * both2e
        )
        ranking.append(
            (eff, peak, name, second, s8, s20, d_adc, d_mid, second_min, legs, snaps, dusk_m)
        )
    ranking.sort(key=lambda x: (x[0], x[1]), reverse=True)
    for row in ranking:
        name, second, s8, s20, d_adc, d_mid, second_min, dusk_m = (
            row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[11]
        )
        mix8 = 0.5 * (s8.overkill_adc_lucky + s8.overkill_mid_lucky)
        mix20 = 0.5 * (s20.overkill_adc_lucky + s20.overkill_mid_lucky)
        dlab = f"{dusk_m:>4}:00" if dusk_m else "    —"
        lines.append(
            f"  {name:<28} {dlab} {second_min:>4}:00 "
            f"{second.overkill_adc_lucky*100:>5.0f}% {second.overkill_mid_lucky*100:>5.0f}% "
            f"{mix8*100:>5.0f}% {mix20*100:>5.0f}% {(d_adc+d_mid)/2:>+7.0f}"
        )

    lines.append("")
    lines.append("-" * 82)
    lines.append("2ND ITEM SPIKE  (isolated Δ, same minute with vs without 2nd)")
    lines.append("-" * 82)
    for row in ranking:
        name, second, d_adc, d_mid, second_min, legs = (
            row[2], row[3], row[6], row[7], row[8], row[9]
        )
        ka = "KILL" if second.kill_adc_lucky else "live"
        km = "KILL" if second.kill_mid_lucky else "live"
        ke = (
            "also expected"
            if second.kill_adc_exp and second.kill_mid_exp
            else "lucky only"
        )
        lines.append(
            f"  {name:<28} 2nd ~{second_min}:00  ADC {second.lucky_adc:.0f} {ka}  "
            f"mid {second.lucky_mid:.0f} {km}  Δ {(d_adc+d_mid)/2:+.0f}  "
            f"[{', '.join(legs[:2])}]  {ke}"
        )

    best = ranking[0]
    winner_name = best[2]
    snaps = best[10]
    w2 = best[3]
    w8 = best[4]
    w20 = best[5]
    d_adc, d_mid = best[6], best[7]
    dusk_m = best[11]
    two_m = first_minute_with(snaps, lambda s: s.legendary_count >= 2)
    ser_m = first_minute_with(snaps, lambda s: s.has_serylda)

    def at2(sn):
        return next((s for s in sn if s.legendary_count >= 2), sn[-1])

    ser2 = at2(results["Dusk → Serylda"])
    col2 = at2(results["Dusk → Collector"])
    mort2 = at2(results["Dusk → Mortal"])
    you2 = at2(results["Dusk → Youmuu"])
    hex2 = at2(results["Dusk → Hex"])
    ie2 = at2(results["Dusk → IE"])
    dyn2 = at2(results["Dusk → Serylda + Dynamism"])

    lines.append("")
    lines.append("-" * 82)
    lines.append("VERDICT")
    lines.append("-" * 82)
    lines.append(f"  Best Dusk-first support path: {winner_name}")
    lines.append(
        f"  Window-weighted score: {best[0]:.3f} | Dusk ~{dusk_m}:00 | "
        f"2nd legendary ~{two_m}:00"
    )
    if ser_m:
        lines.append(f"  Serylda / %pen online:           ~{ser_m}:00  (the 2nd-item peak)")
    lines.append(
        f"  Item 1 @ 8:00 vs ADC: lucky {w8.lucky_adc:.0f} "
        f"({w8.overkill_adc_lucky*100:.0f}%) "
        f"{'KILL' if w8.kill_adc_lucky else 'live'}"
    )
    lines.append(
        f"  2nd item vs ADC: lucky {w2.lucky_adc:.0f} ({w2.overkill_adc_lucky*100:.0f}%) "
        f"{'OVERKILL' if w2.kill_adc_lucky else 'lives'} | "
        f"expected {w2.exp_adc:.0f} ({w2.overkill_adc_exp*100:.0f}%)"
    )
    lines.append(
        f"  2nd item vs mid: lucky {w2.lucky_mid:.0f} ({w2.overkill_mid_lucky*100:.0f}%) "
        f"{'OVERKILL' if w2.kill_mid_lucky else 'lives'} | "
        f"expected {w2.exp_mid:.0f} ({w2.overkill_mid_exp*100:.0f}%)"
    )
    lines.append(
        f"  20:00 vs ADC: lucky {w20.lucky_adc:.0f} ({w20.overkill_adc_lucky*100:.0f}%)  "
        f"AD {w20.ad:.0f}  mist {w20.mist}"
    )
    lines.append(
        f"  Isolated 2nd-item Δ: ADC {d_adc:+.0f} / mid {d_mid:+.0f}"
    )
    lines.append("")
    lines.append("  WHY DUSK FIRST THEN SERYLDA:")
    lines.append("  • Item 1 Duskblade: 55 AD + 18 lethality + Nightstalker")
    lines.append("    60–160. Same early spike as ADC, on support gold ~8:00.")
    lines.append("  • Q/W/R do not crit. 2nd item has to multiply the WHOLE")
    lines.append("    combo. Serylda 35% pen does that; Collector/IE only")
    lines.append("    multiply ~2 autos.")
    lines.append(
        f"  • Dusk→Serylda 2nd ~{ser2.minute}:00 "
        f"{ser2.overkill_adc_lucky*100:.0f}%/{ser2.overkill_mid_lucky*100:.0f}% ADC/mid."
    )
    lines.append(
        f"  • Dusk→Collector {col2.overkill_adc_lucky*100:.0f}% / "
        f"Dusk→Mortal {mort2.overkill_adc_lucky*100:.0f}% / "
        f"Dusk→Youmuu {you2.overkill_adc_lucky*100:.0f}% / "
        f"Dusk→IE {ie2.overkill_adc_lucky*100:.0f}%."
    )
    lines.append(
        f"  • Dusk→Hex 2nd ~{hex2.minute}:00 "
        f"({hex2.overkill_adc_lucky*100:.0f}% ADC) — earlier, smaller spike."
    )
    lines.append(
        f"  • Dynamism before 2nd: spike ~{dyn2.minute}:00 "
        f"({dyn2.overkill_adc_lucky*100:.0f}% ADC). Skip the 1200g boots."
    )
    if crit_baseline and "Collector → Mortal → IE" in crit_baseline:
        c2 = next(
            s for s in crit_baseline["Collector → Mortal → IE"]
            if s.legendary_count >= 2
        )
        c8 = crit_baseline["Collector → Mortal → IE"][7]
        lines.append("")
        lines.append("  VS CRIT-ONLY Collector → Mortal:")
        lines.append(
            f"  • 8:00  Dusk {w8.overkill_adc_lucky*100:.0f}% ADC vs "
            f"Collector {c8.overkill_adc_lucky*100:.0f}% — Nightstalker is the lane."
        )
        lines.append(
            f"  • 2nd   Dusk→Serylda {ser2.overkill_adc_lucky*100:.0f}% vs "
            f"Collector→Mortal {c2.overkill_adc_lucky*100:.0f}%."
        )
    lines.append("")
    lines.append("  RECOMMENDED (Dusk first, peak at 2nd):")
    lines.append("  1) Spectral Sickle → Black Mist Scythe (~5:00)")
    lines.append("  2) Duskblade of Draktharr   (~8:00, Nightstalker = item-1)")
    lines.append("  3) Serylda's Grudge         (~14:00, 35% pen — 2ND ITEM PEAK)")
    lines.append("  4) Youmuu / Collector       (then sell Scythe for a 5th)")
    lines.append("  Do not buy Dynamism before the 2nd legendary.")
    lines.append("  Runes: First Strike · Brutal · Empowered Attack · Cut Down")
    lines.append("=" * 82)
    return "\n".join(lines)


def self_check_dusk(results: Dict[str, List[Snapshot]]) -> None:
    def second(snaps):
        return next(s for s in snaps if s.legendary_count >= 2)

    ser = second(results["Dusk → Serylda"])
    col = second(results["Dusk → Collector"])
    you = second(results["Dusk → Youmuu"])
    dyn = second(results["Dusk → Serylda + Dynamism"])
    d1 = first_minute_with(results["Dusk → Serylda"], lambda s: s.has_dusk)
    assert d1 is not None and d1 <= 10, d1
    assert ser.lucky_adc > col.lucky_adc, (ser.lucky_adc, col.lucky_adc)
    assert ser.lucky_adc > you.lucky_adc, (ser.lucky_adc, you.lucky_adc)
    assert ser.kill_adc_lucky and ser.kill_mid_lucky
    assert ser.minute <= dyn.minute, (ser.minute, dyn.minute)
    assert ser.minute <= 16, ser.minute


def summarize_finish(
    results: Dict[str, List[Snapshot]],
    yuntal_mins: Dict[str, Optional[int]],
) -> str:
    lines = []
    lines.append("")
    lines.append("=" * 82)
    lines.append("FULL BUILD — SELL SCYTHE, 5TH LEGENDARY + RUNES  (WR 7.3)")
    lines.append("Core: Duskblade → Serylda. Then 3rd/4th, sell Scythe, 5th.")
    lines.append("=" * 82)
    lines.append("")
    lines.append("GOLD / LEVEL / MIST (long game)")
    lines.append(
        f"  {'Min':>3}  {'Gold':>6}  {'Lvl':>3}  {'Mist':>4}  "
        f"{'ADC HP':>7}  {'ADC Arm':>7}"
    )
    for m in (20, 22, 24, 25, 26, 27, 28):
        mist = support_mist(m)
        lines.append(
            f"  {m:>3}  {support_gold(m):>6}  {support_level(m):>3}  "
            f"{mist:>4}  {adc_hp(m):>7.0f}  {adc_armor(m):>7.0f}"
        )

    lines.append("")
    lines.append("-" * 82)
    lines.append("4TH / 5TH PAIR  (overkill @ 4th item / sell-minute / 28:00)")
    lines.append("-" * 82)
    lines.append(
        f"  {'Build':<36} {'4th@':>5} {'5th@':>5} {'4th%':>6} "
        f"{'5th%':>6} {'28:00':>6} {'Scythe':>7}"
    )

    ranking = []
    keep = results.get("Keep Scythe (4 items)")
    for name, snaps in results.items():
        if name == "Keep Scythe (4 items)":
            continue
        s4 = next((s for s in snaps if s.legendary_count >= 4), snaps[-1])
        s5 = next((s for s in snaps if s.legendary_count >= 5), None)
        s28 = snaps[-1]
        fifth_min = s5.minute if s5 else None
        mix4 = 0.5 * (s4.overkill_adc_lucky + s4.overkill_mid_lucky)
        mix5 = (
            0.5 * (s5.overkill_adc_lucky + s5.overkill_mid_lucky) if s5 else 0.0
        )
        mix28 = 0.5 * (s28.overkill_adc_lucky + s28.overkill_mid_lucky)
        sold = s5.sold_scythe if s5 else False
        # Dual goal: earliest real 5th + fattest 28:00
        earliness = 1.0 + 0.03 * max(0, (28 - (fifth_min or 28)))
        has5 = 1.12 if s5 else 0.80
        eff = mix28 * has5 * earliness * (1.06 if sold else 1.0)
        ranking.append((eff, mix28, name, s4, s5, s28, fifth_min, sold, mix4, mix5))

    ranking.sort(key=lambda x: (x[0], x[1]), reverse=True)
    for row in ranking:
        name, s4, s5, s28, fifth_min, sold, mix4, mix5 = (
            row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9]
        )
        mix28 = 0.5 * (s28.overkill_adc_lucky + s28.overkill_mid_lucky)
        t5 = f"{fifth_min:>4}:00" if fifth_min else "    —"
        lines.append(
            f"  {name:<36} {s4.minute:>4}:00 {t5} "
            f"{mix4*100:>5.0f}% {mix5*100:>5.0f}% {mix28*100:>5.0f}% "
            f"{'sold' if sold else 'kept':>7}"
        )

    lines.append("")
    lines.append("-" * 82)
    lines.append("KEEP SCYTHE (4 items) vs SELL FOR 5TH  @ 28:00")
    lines.append("-" * 82)
    if keep:
        k28 = keep[-1]
        lines.append(
            f"  Keep Scythe + Hex     ADC {k28.lucky_adc:.0f} "
            f"({k28.overkill_adc_lucky*100:.0f}%)  AD {k28.ad:.0f}  "
            f"items {k28.legendary_count}"
        )
    best = ranking[0]
    w28 = best[5]
    w5 = best[4]
    winner_name = best[2]
    lines.append(
        f"  {winner_name:<36} ADC {w28.lucky_adc:.0f} "
        f"({w28.overkill_adc_lucky*100:.0f}%)  AD {w28.ad:.0f}  "
        f"items {w28.legendary_count}  {'sold Scythe' if w28.sold_scythe else ''}"
    )
    if keep:
        dlt = w28.lucky_adc - keep[-1].lucky_adc
        lines.append(f"  Sell-for-5th vs keep-4: ADC {dlt:+.0f} lucky")

    if w5:
        lines.append("")
        lines.append(
            f"  5th legendary ~{w5.minute}:00  ADC {w5.lucky_adc:.0f} "
            f"({w5.overkill_adc_lucky*100:.0f}%)  mid {w5.lucky_mid:.0f} "
            f"({w5.overkill_mid_lucky*100:.0f}%)"
        )
        lines.append(f"  Inventory: {' › '.join(w5.items)}")

    # Rune ranking on the winning 5-item snapshot
    path = SUPPORT_FINISH_PATHS[winner_name]
    yun = yuntal_mins.get(winner_name)
    t = w5.minute if w5 else 28
    lines.append("")
    lines.append("-" * 82)
    lines.append(f"RUNE PAGES on {winner_name} at {t}:00 (7.2/7.3 values)")
    lines.append("-" * 82)
    lines.append(
        f"  {'Page':<48} {'ADC':>6} {'Mid':>6} {'mix':>6} {'vs Fleet':>8}"
    )
    rune_rank = []
    fleet_mix = None
    for page in SUPPORT_RUNE_PAGES:
        snap = compute_snapshot(winner_name, path, t, yun, "support", page)
        mix = 0.5 * (snap.overkill_adc_lucky + snap.overkill_mid_lucky)
        if page.keystone == "fleet" and "Gathering" not in page.name:
            # first Fleet page
            if fleet_mix is None:
                fleet_mix = mix
        rune_rank.append((mix, page, snap))
    rune_rank.sort(key=lambda x: x[0], reverse=True)
    if fleet_mix is None:
        fleet_mix = rune_rank[-1][0]
    for mix, page, snap in rune_rank:
        dlt = (mix - fleet_mix) * 100
        lines.append(
            f"  {page.name:<48} {snap.lucky_adc:>6.0f} {snap.lucky_mid:>6.0f} "
            f"{mix*100:>5.0f}% {dlt:>+7.1f}pp"
        )

    best_rune = rune_rank[0][1]
    best_snap = rune_rank[0][2]
    finish_legs = [n for n in path if n in LEGENDARIES]
    short = {
        "Duskblade of Draktharr": "Dusk",
        "Serylda's Grudge": "Serylda",
        "Youmuu's Ghostblade": "Youmuu",
        "The Collector": "Collector",
        "Infinity Edge": "IE",
        "Hexoptics C44": "Hex",
        "Mortal Reminder": "Mortal",
        "Edge of Night": "EoN",
        "Fiendhunter Bolts": "Fiendhunter",
        "Rapid Firecannon": "RFC",
    }
    order = [short.get(n, n) for n in finish_legs]
    if w5 and w5.sold_scythe and order:
        order[-1] = "sell Scythe → " + order[-1]
    lines.append("")
    lines.append("-" * 82)
    lines.append("VERDICT — FULL BUILD + RUNES")
    lines.append("-" * 82)
    lines.append(f"  Items: {' → '.join(order)}")
    if w5:
        lines.append(
            f"  4th ~{best[3].minute}:00, sell Scythe + 5th ~{w5.minute}:00"
        )
    lines.append(
        f"  28:00 ADC {w28.lucky_adc:.0f} ({w28.overkill_adc_lucky*100:.0f}%)  "
        f"mid {w28.lucky_mid:.0f} ({w28.overkill_mid_lucky*100:.0f}%)"
    )
    lines.append(f"  Best rune page: {best_rune.name}")
    lines.append(
        f"  With that page @ {t}:00: ADC {best_snap.lucky_adc:.0f} "
        f"({best_snap.overkill_adc_lucky*100:.0f}%)  mid {best_snap.lucky_mid:.0f} "
        f"({best_snap.overkill_mid_lucky*100:.0f}%)"
    )
    lines.append("")
    lines.append("  WHY SELL SCYTHE:")
    lines.append("  • Scythe is 28 AD + 40 soulcast = 68 AD and 10 AH, but")
    lines.append(f"    sells for {SCYTHE_SELL}g — that gold finishes the 5th")
    lines.append("    legendary. A real 5th item outdamages 68 AD on this combo.")
    lines.append("  • Do not sell until the 5th item is actually affordable.")
    lines.append("  • RFC / Fiendhunter 5th: 0 AD was a trap as item 1, but at")
    lines.append("    100% crit + IE the 40–45% AS can buy a 3rd auto. Check")
    lines.append("    the table — if that 3rd auto fits, it beats Dusk/Hex 5th.")
    lines.append("")
    lines.append("  WHY THIS RUNE PAGE:")
    if best_rune.keystone == "first_strike":
        lines.append("  • First Strike: R from fog always opens combat. 9% bonus")
        lines.append("    TRUE on the whole 2.5s combo. 7.2 only nerfed the gold")
        lines.append("    ratio (ranged 45%), not the 9% damage.")
    elif best_rune.keystone == "electrocute":
        lines.append("  • Electrocute: R+W+Q procs it. 7.2 left it at 10% bAD")
        lines.append("    (was 40%), so this win is the guaranteed proc.")
    else:
        lines.append(f"  • Keystone {best_rune.keystone} won the all-in ranking.")
    lines.append("  • Fleet heals. Zero burst. Lane-only.")
    lines.append("  • Empowerment needs 3 basic attacks; this combo is 1 Q")
    lines.append("    on-hit + ~2 autos, so the 8% amp lands on nothing.")
    lines.append("  • Brutal (6 + 8% bAD on attacks) and Empowered Attack (Q)")
    lines.append("    stay. At 28:00 Gathering Storm's stacked AD (~44) beats")
    lines.append("    Cut Down's 6.57% on the opening chunk; keep Cut Down")
    lines.append("    until ~18:00 when Storm has stacked.")
    lines.append("  • Cut Down 6.57% while they are >60% HP covers R/W/Q")
    lines.append("    in lane. Coup once they walk in pre-chunked.")
    lines.append("")
    lines.append("  RECOMMENDED FINISHED BUILD:")
    lines.append("  1) Spectral Sickle → Black Mist Scythe")
    rec_tags = {
        "Duskblade of Draktharr": "item-1 Nightstalker",
        "Serylda's Grudge": "2ND ITEM PEAK — 35% pen",
        "Youmuu's Ghostblade": "lethality + move speed",
        "The Collector": "execute + 25% crit",
        "Infinity Edge": "230% crit",
        "Hexoptics C44": "range + 25% crit",
        "Fiendhunter Bolts": "AS + 15% true — extra auto",
        "Rapid Firecannon": "AS + energized range",
    }
    sold = bool(w5 and w5.sold_scythe)
    for i, item in enumerate(finish_legs):
        n = i + 2
        tag = rec_tags.get(item, "")
        extra = f"   ({tag})" if tag else ""
        if sold and i == len(finish_legs) - 1:
            lines.append(f"  {n}) Sell Scythe → {item}{extra}")
        else:
            lines.append(f"  {n}) {item}{extra}")
    lines.append("")
    lines.append("  RUNES (support, this burst):")
    lines.append(f"  Keystone: {best_rune.keystone.replace('_', ' ').title()}")
    seconds = ["Brutal" if best_rune.brutal else None]
    if best_rune.empowered:
        seconds.append("Empowered Attack")
    if best_rune.sudden_impact:
        seconds.append("Sudden Impact")
    if best_rune.gathering_storm:
        seconds.append("Gathering Storm")
    if best_rune.cheap_shot:
        seconds.append("Cheap Shot")
    if best_rune.precision == "cut_down":
        seconds.append("Cut Down")
    elif best_rune.precision == "coup":
        seconds.append("Coup de Grace")
    lines.append("  " + " · ".join(s for s in seconds if s))
    lines.append("  Lane/2nd-item: First Strike · Brutal · Emp · Cut Down")
    lines.append("  Fleet only if the lane is a poke war and you never get fog R.")
    lines.append("=" * 82)
    return "\n".join(lines)


def self_check_finish(results: Dict[str, List[Snapshot]]) -> None:
    keep = results["Keep Scythe (4 items)"][-1]
    fin = results["Collector → Hex → Fiendhunter"]
    s5 = next((s for s in fin if s.legendary_count >= 5), None)
    assert s5 is not None, "Collector → Hex → Fiendhunter never finished 5th legendary"
    assert s5.minute <= 28, s5.minute
    assert s5.sold_scythe, s5.items
    assert "Black Mist Scythe" not in s5.items
    assert s5.legendary_count >= 5
    assert keep.legendary_count == 4
    d28 = fin[-1]
    assert d28.has_dusk
    assert d28.lucky_adc > keep.lucky_adc, (d28.lucky_adc, keep.lucky_adc)


def main() -> None:
    out_dir = "/workspace/senna-burst-sim"

    results, timeline, yuntal_mins = run_all()
    self_check(results)
    report = summarize(results, timeline, yuntal_mins)
    print(report)
    with open(f"{out_dir}/report.txt", "w", encoding="utf-8") as f:
        f.write(report + "\n")
    export_json(results, timeline, f"{out_dir}/results.json")
    print(f"\nWrote {out_dir}/report.txt and {out_dir}/results.json")

    dusk_results, dusk_timeline, dusk_yun = run_all(
        SUPPORT_DUSK_PATHS, role="support", scorer=dusk_support_score
    )
    self_check_dusk(dusk_results)

    sup_results, sup_timeline, sup_yun = run_all(
        SUPPORT_CRIT_PATHS, role="support", scorer=support_score
    )
    contrast, _, _ = run_all(
        SUPPORT_CONTRAST_PATHS, role="support", scorer=support_score
    )
    self_check_support(sup_results, contrast)

    dusk_report = summarize_dusk_support(
        dusk_results, dusk_timeline, dusk_yun, crit_baseline=sup_results
    )
    sup_report = summarize_support(
        sup_results, contrast, sup_timeline, sup_yun
    )
    print("\n" + dusk_report)
    print("\n" + sup_report)
    with open(f"{out_dir}/report-support.txt", "w", encoding="utf-8") as f:
        f.write(dusk_report + "\n\n" + sup_report + "\n")
    export_json(
        {**dusk_results, **sup_results, **contrast},
        dusk_timeline,
        f"{out_dir}/results-support.json",
        meta_extra={
            "role": "Support (fasting)",
            "playstyle": "Dusk first, 2nd-item peak; crit-only fallback",
        },
    )
    print(f"\nWrote {out_dir}/report-support.txt and {out_dir}/results-support.json")

    fin_results, fin_timeline, fin_yun = run_all(
        SUPPORT_FINISH_PATHS,
        role="support",
        scorer=dusk_support_score,
        minutes=SUPPORT_MINUTES,
    )
    self_check_finish(fin_results)
    fin_report = summarize_finish(fin_results, fin_yun)
    print(fin_report)
    with open(f"{out_dir}/report-support.txt", "a", encoding="utf-8") as f:
        f.write(fin_report + "\n")
    export_json(
        fin_results,
        fin_timeline,
        f"{out_dir}/results-support-finish.json",
        meta_extra={
            "role": "Support (fasting) full build",
            "playstyle": "sell Scythe, 5th legendary + rune ranking",
            "game_minutes": SUPPORT_MINUTES,
        },
    )
    print(f"\nWrote full-build section and {out_dir}/results-support-finish.json")


if __name__ == "__main__":
    main()
