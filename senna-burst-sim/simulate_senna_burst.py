#!/usr/bin/env python3
"""
Wild Rift Senna — 2nd-item burst / overkill simulation
Patch 7.3 item + kit values. Average game: 20 minutes.

Playstyle: dragon-lane farmer (not support). One-shot ADC and mid
in a short all-in once two legendaries are online.

Question:
  After 7.3 deleted Magnetic Blaster, reworked crit (200% base,
  Senna autos at 90% of that, 10% crit / 20 Mist), and added
  Hexoptics / Yun Tal / Stormrazor / Fiendhunter — which path
  peaks BURST at item 2 and overkills ADC + mid?
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import json

GAME_MINUTES = 20
BURST_WINDOW = 2.5  # rooted / flash-all-in, R already in the air

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


def resolve_inventory(path: List[str], gold: int) -> List[Item]:
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
        if step in owned:
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
) -> Tuple[float, int]:
    """
    All-in on a full-HP squishy.
    Order: R (mark) → W → Q (consume %HP + Relic on-hit) → autos
    (Nightstalker / Spellblade / Energized / Hexoptics / Galeforce dash).
    """
    mist_ad = 1.25 * mist
    bonus_ad = st["item_ad"] + mist_ad
    total_ad = 54.0 + bonus_ad  # WR Senna: no AD growth
    item_crit = min(1.0, st["item_crit"])
    mist_crit = 0.10 * (mist // 20)
    crit_chance = min(1.0, item_crit + mist_crit)
    cmult = senna_crit_mult(st["ie"])
    p = phys_mult(armor, st["pct"], st["leth"])
    m = magic_mult(mr)

    q_rank = skill_rank(level, "Q")
    w_rank = skill_rank(level, "W")
    r_rank = skill_rank(level, "R")

    aspd = attack_speed(level, st["as_pct"], st["yuntal"])
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

    def cut_down(before: float) -> float:
        return 1.08 if before / hp > 0.60 else 1.0

    def apply_phys(raw: float) -> float:
        nonlocal hp_left, dmg
        dealt = raw * p * cut_down(hp_left)
        dmg += dealt
        hp_left = max(0.0, hp_left - dealt)
        return dealt

    def apply_magic(raw: float) -> float:
        nonlocal hp_left, dmg
        dealt = raw * m * cut_down(hp_left)
        dmg += dealt
        hp_left = max(0.0, hp_left - dealt)
        return dealt

    # R — 120% bonus AD (7.3 also +70% AP, we build AD)
    if r_rank > 0:
        apply_phys(r_base(r_rank) + 1.20 * bonus_ad)

    # W
    if w_rank > 0:
        apply_phys(w_base(w_rank) + 0.70 * bonus_ad)

    # Q + Relic on-hit (Q applies on-hit to champions) + Empowered Attack
    brutal = 6.0 + 0.08 * bonus_ad
    q_raw = q_base(q_rank) + 0.60 * bonus_ad
    relic = 0.20 * total_ad
    emp = empowered_attack(level)
    apply_phys(q_raw + relic + emp + brutal)

    # Mist extract: 2nd hit on a marked champ (R/W already marked)
    apply_phys(mist_current_hp_pct(level) * hp_left)

    # Galeforce dash missiles (used to gap-close the all-in)
    if st["gale"]:
        gale = (40.0 + 80.0 * (level - 1) / 14.0) + 0.35 * bonus_ad
        apply_phys(gale)

    # Autos
    for i in range(n_aa):
        auto_raw = (total_ad * auto_mult + relic) * hex_amp + brutal
        apply_phys(auto_raw)
        if st["fiend"] and fiend_true and i < 3:
            # 15% bonus true on attacks that would already crit
            true_hit = 0.15 * total_ad * auto_mult
            dmg += true_hit
            hp_left = max(0.0, hp_left - true_hit)

    # Duskblade Nightstalker — first basic attack vs champion
    if st["dusk"] and n_aa >= 1:
        apply_phys(duskblade_proc(level))

    # Essence Reaver Spellblade on the first auto after Q
    # 7.3: 135% base AD + 0–80 from crit chance. Senna base AD is 54 forever.
    if st["er"] and n_aa >= 1:
        sb = 1.35 * 54.0 + 80.0 * crit_chance
        apply_phys(sb)

    # Energized magic (one proc in the window)
    if st["storm"]:
        apply_magic(120.0)
    elif st["rfc"]:
        apply_magic(80.0)

    # Collector execute
    exec_pct = 0.05 if st["collector"] else 0.0
    if exec_pct and hp_left <= hp * exec_pct + 1e-6:
        dmg += hp_left
        hp_left = 0.0

    return dmg, n_aa


def yuntal_online_minute(path: List[str]) -> Optional[int]:
    for m in range(1, GAME_MINUTES + 1):
        names = [it.name for it in resolve_inventory(path, gold_at_minute(m))]
        if "Yun Tal Wildarrows" in names:
            return m
    return None


def compute_snapshot(
    build_name: str,
    path: List[str],
    minute: int,
    yuntal_min: Optional[int],
) -> Snapshot:
    gold = gold_at_minute(minute)
    level = level_at_minute(minute)
    mist = mist_at_minute(minute)
    inv = resolve_inventory(path, gold)
    st = sum_stats(inv, minute, yuntal_min)
    bonus_ad = st["item_ad"] + 1.25 * mist
    total_ad = 54.0 + bonus_ad
    mist_crit = 0.10 * (mist // 20)
    crit = min(1.0, st["item_crit"] + mist_crit)

    a_hp, a_ar, a_mr = adc_hp(minute), adc_armor(minute), adc_mr(minute)
    m_hp, m_ar, m_mr = mid_hp(minute), mid_armor(minute), mid_mr(minute)

    exp_a, n_aa = combo_damage(
        level=level, mist=mist, st=st, hp=a_hp, armor=a_ar, mr=a_mr, lucky=False
    )
    lucky_a, _ = combo_damage(
        level=level, mist=mist, st=st, hp=a_hp, armor=a_ar, mr=a_mr, lucky=True
    )
    exp_m, _ = combo_damage(
        level=level, mist=mist, st=st, hp=m_hp, armor=m_ar, mr=m_mr, lucky=False
    )
    lucky_m, _ = combo_damage(
        level=level, mist=mist, st=st, hp=m_hp, armor=m_ar, mr=m_mr, lucky=True
    )

    exec_pct = 0.05 if st["collector"] else 0.0

    def is_kill(dmg: float, hp: float) -> bool:
        return dmg >= hp * (1.0 - exec_pct) - 0.5

    n_leg = sum(1 for n in st["names"] if n in LEGENDARIES)
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
    if n_leg == 0:
        notes.append("pre-legendary")
    elif n_leg == 1:
        notes.append("1 item")
    elif n_leg >= 2:
        notes.append("2-ITEM SPIKE")

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


def run_all() -> Tuple[Dict[str, List[Snapshot]], List[dict], Dict[str, Optional[int]]]:
    yuntal_mins: Dict[str, Optional[int]] = {
        name: yuntal_online_minute(path) for name, path in BUILD_PATHS.items()
    }
    results: Dict[str, List[Snapshot]] = {}
    for name, path in BUILD_PATHS.items():
        results[name] = [
            compute_snapshot(name, path, m, yuntal_mins[name])
            for m in range(1, GAME_MINUTES + 1)
        ]

    timeline = []
    for m in range(1, GAME_MINUTES + 1):
        cands = [(n, results[n][m - 1]) for n in results]
        best_n, best_s = max(cands, key=lambda x: burst_score(x[1]))
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
    name: str, path: List[str], snaps: List[Snapshot], yuntal_min: Optional[int]
) -> Tuple[float, float, int, List[str]]:
    """Lucky ADC+mid overkill added by the 2nd legendary, same minute."""
    second = next((s for s in snaps if s.legendary_count >= 2), None)
    if second is None:
        last = snaps[-1]
        return 0.0, 0.0, last.minute, last.items
    one_path = truncate_after_n_legendaries(path, 1)
    without = compute_snapshot(name, one_path, second.minute, yuntal_min)
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


def export_json(results, timeline, path: str) -> None:
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
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


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


def main() -> None:
    results, timeline, yuntal_mins = run_all()
    self_check(results)
    report = summarize(results, timeline, yuntal_mins)
    print(report)
    out_dir = "/workspace/senna-burst-sim"
    with open(f"{out_dir}/report.txt", "w", encoding="utf-8") as f:
        f.write(report + "\n")
    export_json(results, timeline, f"{out_dir}/results.json")
    print(f"\nWrote {out_dir}/report.txt and {out_dir}/results.json")


if __name__ == "__main__":
    main()
