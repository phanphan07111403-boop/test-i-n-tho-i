#!/usr/bin/env python3
"""
Wild Rift — AP Kog'Maw, spam Living Artillery.

Patch 7.3 items (mage pass from 7.2 / 7.2c, Luden echo from 7.3).
Living Artillery was retuned in 7.2c and was not touched in 7.3.

Playstyle: Q for the shred, then R on cooldown. No W, no E.
The limiter is mana. Each shell in a chain costs 50 more (50 → 500).
The chain falls off 8 seconds after the last cast.

Question:
  Which build lets you keep firing R — in a fight you started on half
  a bar because you were already poking, and across a longer siege —
  without the last shells becoming a 500-mana tax, and without the
  barrage falling off against a tank who stands in the shells?
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple
import json

GAME_MINUTES = 20
FIGHT_WINDOW = 12.0
SIEGE_WINDOW = 40.0
SIEGE_RESET = 8.0
DT = 0.05

# Already poking, so half a bar is the default. Full bar is the reset siege.
HALF_WEIGHT = 0.60
FULL_WEIGHT = 0.40
TANK_WEIGHT = 0.62
SQUISH_WEIGHT = 0.38
# 12s all-in vs a 40s siege where the tank walks back to full every 8s.
FIGHT_WEIGHT = 0.72
SIEGE_WEIGHT = 0.28
# Killing faster than the window is extra value on top of the health bar.
KILL_BONUS = 0.25

# Stop casting once the next shell would cost more than this.
COST_CAPS = (150, 200, 250, 300, 400, 500)

TIER3_BOOTS = {"Spellslinger's Shoes", "Crimson Lucidity"}
MULTI = {"Needlessly Large Rod", "Fiendish Codex", "Amplifying Tome"}


# ---------------------------------------------------------------------------
# Economy / XP — dragon-lane or mid farmer, same curve as the Kai'Sa WR sim
# ---------------------------------------------------------------------------


def gold_at_minute(m: int) -> int:
    if m <= 0:
        return 500
    total = 500
    for t in range(1, m + 1):
        if t <= 5:
            total += 360
        elif t <= 10:
            total += 480
        elif t <= 15:
            total += 560
        else:
            total += 620
    return total


def level_at_minute(m: int) -> int:
    table = {
        1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7, 7: 8, 8: 9,
        9: 10, 10: 11, 11: 11, 12: 12, 13: 12, 14: 13,
        15: 13, 16: 14, 17: 14, 18: 15, 19: 15, 20: 15,
    }
    return table.get(m, min(15, 1 + m))


def q_rank(level: int) -> int:
    """Spam R maxes Q. Points at levels 1, 3, 4, 6. E and W are not cast."""
    return sum(1 for lv in (1, 3, 4, 6) if level >= lv)


def r_rank(level: int) -> int:
    """Ult ranks at 5 / 9 / 13. Cooldowns 2 / 1 / 1."""
    if level < 5:
        return 0
    if level < 9:
        return 1
    if level < 13:
        return 2
    return 3


def base_mana(level: int) -> float:
    # Live sheet: 380 at level 1, 898 at level 15 → +37 per level.
    return 380.0 + 37.0 * (level - 1)


def base_mp5(level: int) -> float:
    # 14 at level 1, 28 at level 15.
    return 14.0 + 1.0 * (level - 1)


def gathering_ap(minute: int) -> float:
    """Gathering Storm adaptive AP: 4 / 10 / 18 / 28 / … from 6:00, every 3 min."""
    if minute < 6:
        return 0.0
    steps = 1 + (minute - 6) // 3
    ap = 0.0
    inc = 4.0
    for _ in range(steps):
        ap += inc
        inc += 2.0
    return ap


def transcendence_ah(level: int) -> float:
    if level >= 5:
        return 10.0
    if level >= 1:
        return 5.0
    return 0.0


def manaflow_bonus(minute: int) -> float:
    """+30 max mana per champion hit, cap 300. A poker finishes it by ~6:00."""
    return float(min(300, 60 * max(0, minute - 1)))


# ---------------------------------------------------------------------------
# Targets
# ---------------------------------------------------------------------------


def squishy_hp(m: int) -> float:
    lv = level_at_minute(m)
    return 620 + 95 * lv + 16 * m


def squishy_mr(m: int) -> float:
    lv = level_at_minute(m)
    extra = 0.0 if m < 12 else (10.0 if m < 17 else 22.0)
    return 30 + 1.3 * lv + extra


def tank_hp(m: int) -> float:
    lv = level_at_minute(m)
    return 680 + 108 * lv + 70 * max(0, m - 6)


def tank_mr(m: int) -> float:
    lv = level_at_minute(m)
    extra = 0.0 if m < 8 else min(7.5 * (m - 8), 120.0)
    return 32 + 1.8 * lv + extra


# ---------------------------------------------------------------------------
# Items — Wild Rift 7.2 mage pass, with 7.3 Luden / Tear / Infinity Orb
# ---------------------------------------------------------------------------


@dataclass
class Item:
    name: str
    cost: int
    ap: float = 0
    ah: float = 0
    hp: float = 0
    mana: float = 0
    flat_mpen: float = 0
    pct_mpen: float = 0
    regen: float = 0  # bonus mana regen fraction (0.75 = +75%)
    ult_haste: float = 0
    deathcap: bool = False
    luden: bool = False
    liandry: bool = False
    ashes: bool = False
    blackfire: bool = False
    malignance: bool = False
    horizon: bool = False
    orb: bool = False
    madness: bool = False  # +2% per second, cap 6%
    bloodletter: bool = False
    tear: bool = False
    archangel: bool = False
    roa: bool = False
    alternator: bool = False
    tags: Tuple[str, ...] = ()


ITEMS: Dict[str, Item] = {
    "Amplifying Tome": Item("Amplifying Tome", 500, ap=20),
    "Blasting Wand": Item("Blasting Wand", 800, ap=40),
    "Needlessly Large Rod": Item("Needlessly Large Rod", 1400, ap=65),
    "Lost Chapter": Item("Lost Chapter", 1200, ap=35, ah=10, mana=200),
    "Fiendish Codex": Item("Fiendish Codex", 900, ap=25, ah=10),
    "Hextech Alternator": Item("Hextech Alternator", 1100, ap=45, alternator=True),
    "Haunting Guise": Item("Haunting Guise", 1300, ap=30, hp=200, madness=True),
    "Fated Ashes": Item("Fated Ashes", 900, ap=40, ashes=True),
    "Aether Wisp": Item("Aether Wisp", 950, ap=35),
    "Void Amethyst": Item("Void Amethyst", 1000, ap=20, pct_mpen=0.10),
    "Ring of Revelation": Item("Ring of Revelation", 300, ah=5),
    "Kindlegem": Item("Kindlegem", 1000, hp=175, ah=10),
    "Giant's Belt": Item("Giant's Belt", 1000, hp=300),
    "Catalyst of Aeons": Item("Catalyst of Aeons", 1100, hp=200, mana=300),
    "Tear of the Goddess": Item("Tear of the Goddess", 400, tear=True),
    "Boots of Speed": Item("Boots of Speed", 400, tags=("boots",)),
    "Boots of Mana": Item(
        "Boots of Mana", 1200, ap=25, flat_mpen=8, regen=0.75, tags=("boots",)
    ),
    "Ionian Boots of Lucidity": Item(
        "Ionian Boots of Lucidity", 1000, ah=15, regen=0.50, tags=("boots",)
    ),
    "Spellslinger's Shoes": Item(
        "Spellslinger's Shoes",
        2200,
        ap=35,
        flat_mpen=18,
        pct_mpen=0.08,
        regen=1.00,
        tags=("boots",),
    ),
    "Crimson Lucidity": Item(
        "Crimson Lucidity", 2000, ah=25, regen=0.75, tags=("boots",)
    ),
    "Malignance": Item(
        "Malignance",
        2700,
        ap=90,
        ah=15,
        mana=500,
        ult_haste=20,
        malignance=True,
    ),
    "Luden's Echo": Item(
        "Luden's Echo", 2800, ap=100, ah=10, mana=500, luden=True
    ),
    "Blackfire Torch": Item(
        "Blackfire Torch",
        2800,
        ap=80,
        ah=20,
        mana=500,
        blackfire=True,
    ),
    "Liandry's Torment": Item(
        "Liandry's Torment", 3000, ap=70, hp=300, liandry=True, madness=True
    ),
    "Horizon Focus": Item("Horizon Focus", 2700, ap=80, ah=25, horizon=True),
    "Void Staff": Item("Void Staff", 3000, ap=95, pct_mpen=0.40),
    "Cryptbloom": Item("Cryptbloom", 3000, ap=75, ah=20, pct_mpen=0.30),
    "Rabadon's Deathcap": Item(
        "Rabadon's Deathcap", 3400, ap=130, deathcap=True
    ),
    "Infinity Orb": Item(
        "Infinity Orb", 3100, ap=110, flat_mpen=15, orb=True
    ),
    "Stormsurge": Item("Stormsurge", 2900, ap=90, flat_mpen=15),
    "Rod of Ages": Item("Rod of Ages", 2700, ap=50, hp=350, mana=400, roa=True),
    "Archangel's Staff": Item(
        "Archangel's Staff", 3000, ap=60, ah=25, archangel=True
    ),
    "Bloodletter's Curse": Item(
        "Bloodletter's Curse",
        2900,
        ap=65,
        hp=350,
        ah=15,
        bloodletter=True,
    ),
    "Cosmic Drive": Item("Cosmic Drive", 3000, ap=70, hp=300, ah=25),
    "Rylai's Crystal Scepter": Item(
        "Rylai's Crystal Scepter", 2700, ap=70, hp=350
    ),
}


COMPONENTS: Dict[str, Tuple[str, ...]] = {
    "Lost Chapter": ("Amplifying Tome", "Ring of Revelation"),
    "Boots of Mana": ("Boots of Speed",),
    "Ionian Boots of Lucidity": ("Boots of Speed", "Ring of Revelation"),
    "Spellslinger's Shoes": ("Boots of Mana",),
    "Crimson Lucidity": ("Ionian Boots of Lucidity",),
    "Malignance": ("Lost Chapter", "Blasting Wand"),
    "Luden's Echo": ("Lost Chapter", "Hextech Alternator"),
    "Blackfire Torch": ("Lost Chapter", "Fated Ashes"),
    "Liandry's Torment": ("Haunting Guise", "Fated Ashes"),
    "Horizon Focus": ("Fiendish Codex", "Fiendish Codex", "Amplifying Tome"),
    "Void Staff": ("Void Amethyst", "Needlessly Large Rod"),
    "Cryptbloom": ("Void Amethyst", "Fiendish Codex", "Amplifying Tome"),
    "Rabadon's Deathcap": ("Needlessly Large Rod", "Needlessly Large Rod"),
    "Infinity Orb": ("Hextech Alternator", "Needlessly Large Rod"),
    "Stormsurge": ("Hextech Alternator", "Aether Wisp"),
    "Rod of Ages": ("Catalyst of Aeons", "Blasting Wand"),
    "Archangel's Staff": ("Tear of the Goddess", "Lost Chapter", "Fiendish Codex"),
    "Bloodletter's Curse": ("Haunting Guise", "Fiendish Codex"),
    "Cosmic Drive": ("Aether Wisp", "Fiendish Codex", "Kindlegem"),
    "Rylai's Crystal Scepter": ("Giant's Belt", "Blasting Wand", "Amplifying Tome"),
}

LEGENDARIES = {
    "Malignance",
    "Luden's Echo",
    "Blackfire Torch",
    "Liandry's Torment",
    "Horizon Focus",
    "Void Staff",
    "Cryptbloom",
    "Rabadon's Deathcap",
    "Infinity Orb",
    "Stormsurge",
    "Rod of Ages",
    "Archangel's Staff",
    "Seraph's Embrace",
    "Bloodletter's Curse",
    "Cosmic Drive",
    "Rylai's Crystal Scepter",
}

BUILD_PATHS: Dict[str, List[str]] = {
    "Malig → Horizon → Void": [
        "Lost Chapter",
        "Blasting Wand",
        "Malignance",
        "Boots of Speed",
        "Boots of Mana",
        "Fiendish Codex",
        "Fiendish Codex",
        "Horizon Focus",
        "Void Amethyst",
        "Void Staff",
        "Rabadon's Deathcap",
    ],
    "Malig → Liandry → Void": [
        "Lost Chapter",
        "Blasting Wand",
        "Malignance",
        "Boots of Speed",
        "Boots of Mana",
        "Fated Ashes",
        "Haunting Guise",
        "Liandry's Torment",
        "Void Amethyst",
        "Void Staff",
        "Rabadon's Deathcap",
    ],
    "Luden → Horizon → Void": [
        "Lost Chapter",
        "Hextech Alternator",
        "Luden's Echo",
        "Boots of Speed",
        "Boots of Mana",
        "Fiendish Codex",
        "Fiendish Codex",
        "Horizon Focus",
        "Void Amethyst",
        "Void Staff",
        "Rabadon's Deathcap",
    ],
    "Luden → Liandry → Void": [
        "Lost Chapter",
        "Hextech Alternator",
        "Luden's Echo",
        "Boots of Speed",
        "Boots of Mana",
        "Fated Ashes",
        "Haunting Guise",
        "Liandry's Torment",
        "Void Amethyst",
        "Void Staff",
    ],
    "Tear → Seraph → Horizon": [
        "Tear of the Goddess",
        "Lost Chapter",
        "Fiendish Codex",
        "Archangel's Staff",
        "Boots of Speed",
        "Boots of Mana",
        "Horizon Focus",
        "Void Amethyst",
        "Void Staff",
        "Rabadon's Deathcap",
    ],
    "Tear → Seraph → Liandry": [
        "Tear of the Goddess",
        "Lost Chapter",
        "Fiendish Codex",
        "Archangel's Staff",
        "Boots of Speed",
        "Boots of Mana",
        "Fated Ashes",
        "Haunting Guise",
        "Liandry's Torment",
        "Void Staff",
    ],
    "RoA → Malig → Horizon": [
        "Catalyst of Aeons",
        "Blasting Wand",
        "Rod of Ages",
        "Boots of Speed",
        "Boots of Mana",
        "Lost Chapter",
        "Malignance",
        "Fiendish Codex",
        "Horizon Focus",
        "Void Staff",
    ],
    "BF → Malig → Liandry": [
        "Fated Ashes",
        "Lost Chapter",
        "Blackfire Torch",
        "Boots of Speed",
        "Boots of Mana",
        "Malignance",
        "Haunting Guise",
        "Liandry's Torment",
        "Void Staff",
    ],
    "Malig → Orb → Horizon": [
        "Lost Chapter",
        "Blasting Wand",
        "Malignance",
        "Boots of Speed",
        "Boots of Mana",
        "Hextech Alternator",
        "Needlessly Large Rod",
        "Infinity Orb",
        "Fiendish Codex",
        "Horizon Focus",
        "Void Staff",
    ],
    "Malig → Spellslinger → Liandry": [
        "Lost Chapter",
        "Blasting Wand",
        "Malignance",
        "Boots of Speed",
        "Boots of Mana",
        "Spellslinger's Shoes",
        "Fated Ashes",
        "Haunting Guise",
        "Liandry's Torment",
        "Void Amethyst",
        "Void Staff",
    ],
    "Malig → Spellslinger → Void": [
        "Lost Chapter",
        "Blasting Wand",
        "Malignance",
        "Boots of Speed",
        "Boots of Mana",
        "Spellslinger's Shoes",
        "Fiendish Codex",
        "Horizon Focus",
        "Void Amethyst",
        "Void Staff",
        "Rabadon's Deathcap",
    ],
    "Malig → Crimson → Horizon": [
        "Lost Chapter",
        "Blasting Wand",
        "Malignance",
        "Boots of Speed",
        "Ionian Boots of Lucidity",
        "Crimson Lucidity",
        "Fiendish Codex",
        "Horizon Focus",
        "Void Amethyst",
        "Void Staff",
    ],
    "Malig → Stormsurge → Horizon": [
        "Lost Chapter",
        "Blasting Wand",
        "Malignance",
        "Boots of Speed",
        "Boots of Mana",
        "Hextech Alternator",
        "Aether Wisp",
        "Stormsurge",
        "Fiendish Codex",
        "Horizon Focus",
        "Void Staff",
    ],
    "Malig → Bloodletter → Void": [
        "Lost Chapter",
        "Blasting Wand",
        "Malignance",
        "Boots of Speed",
        "Boots of Mana",
        "Haunting Guise",
        "Fiendish Codex",
        "Bloodletter's Curse",
        "Void Amethyst",
        "Void Staff",
        "Rabadon's Deathcap",
    ],
    "BF → Horizon → Void": [
        "Fated Ashes",
        "Lost Chapter",
        "Blackfire Torch",
        "Boots of Speed",
        "Boots of Mana",
        "Fiendish Codex",
        "Horizon Focus",
        "Void Amethyst",
        "Void Staff",
        "Rabadon's Deathcap",
    ],
    "Malig → Cryptbloom → Horizon": [
        "Lost Chapter",
        "Blasting Wand",
        "Malignance",
        "Boots of Speed",
        "Boots of Mana",
        "Void Amethyst",
        "Fiendish Codex",
        "Cryptbloom",
        "Horizon Focus",
        "Rabadon's Deathcap",
    ],
    "Malig → Cosmic → Void": [
        "Lost Chapter",
        "Blasting Wand",
        "Malignance",
        "Boots of Speed",
        "Boots of Mana",
        "Aether Wisp",
        "Kindlegem",
        "Cosmic Drive",
        "Void Amethyst",
        "Void Staff",
    ],
}


# ---------------------------------------------------------------------------
# Inventory
# ---------------------------------------------------------------------------


def remaining_cost(item_name: str, owned: Sequence[str]) -> int:
    need = list(COMPONENTS.get(item_name, ()))
    pool = list(owned)
    credit = 0
    for comp in need:
        if comp in pool:
            credit += ITEMS[comp].cost
            pool.remove(comp)
    return max(0, ITEMS[item_name].cost - credit)


def consume_components(item_name: str, owned: List[str]) -> None:
    for comp in COMPONENTS.get(item_name, ()):
        if comp in owned:
            owned.remove(comp)


def resolve_inventory(path: List[str], gold: int, minute: int) -> List[str]:
    owned: List[str] = []
    pool = gold

    def copies(name: str) -> int:
        return owned.count(name)

    def buy(name: str) -> bool:
        nonlocal pool
        if name in TIER3_BOOTS and minute < 10:
            return False
        cost = remaining_cost(name, owned)
        if cost > pool:
            return False
        pool -= cost
        consume_components(name, owned)
        owned.append(name)
        return True

    for step in path:
        if step in TIER3_BOOTS and minute < 10:
            continue
        if step not in MULTI and step in owned:
            continue
        if step in MULTI and copies(step) >= path.count(step):
            continue
        if buy(step):
            continue
        # Buy every missing component this upgrade still needs, in order,
        # then stop. Gold sits in components rather than skipping ahead.
        need = list(COMPONENTS.get(step, ()))
        held = list(owned)
        missing: List[str] = []
        for comp in need:
            if comp in held:
                held.remove(comp)
            else:
                missing.append(comp)
        for comp in missing:
            if pool < ITEMS[comp].cost:
                break
            pool -= ITEMS[comp].cost
            owned.append(comp)
        if not buy(step):
            break
    return owned


# ---------------------------------------------------------------------------
# Combat math
# ---------------------------------------------------------------------------


def haste_mult(haste: float) -> float:
    return 100.0 / (100.0 + max(0.0, haste))


def r_cooldown(rank: int, ah: float, ult_haste: float) -> float:
    base = (0.0, 2.0, 1.0, 1.0)[rank]
    return base * haste_mult(ah + ult_haste)


def r_mana_cost(stacks: int) -> float:
    """50, 100, … 500. Stacks 0..9."""
    return float(min(500, 50 * (stacks + 1)))


def r_raw(rank: int, ap: float, hp_frac: float) -> float:
    """Min damage 80/120/160 + 25% AP. Doubles below 40% HP.

    Between those, +0–50% for 0–60% missing health.
    Bonus AD ratio is 75%; this build has no bonus AD.
    """
    if rank <= 0:
        return 0.0
    base = (0.0, 80.0, 120.0, 160.0)[rank]
    raw = base + 0.25 * ap
    if hp_frac < 0.40:
        return raw * 2.0
    missing = 1.0 - hp_frac
    amp = min(0.50, missing / 0.60 * 0.50)
    return raw * (1.0 + amp)


def q_raw(level: int, ap: float) -> float:
    rank = q_rank(level)
    if rank <= 0:
        return 0.0
    base = (0.0, 90.0, 150.0, 210.0, 270.0)[rank]
    return base + 0.65 * ap


def q_shred(level: int) -> float:
    rank = q_rank(level)
    if rank <= 0:
        return 0.0
    return (0.0, 0.20, 0.24, 0.28, 0.32)[rank]


def q_cost_base() -> float:
    return 40.0


def effective_mr(
    mr: float,
    pct_shreds: Sequence[float],
    flat_red: float,
    pct_pens: Sequence[float],
    flat_pen: float,
) -> float:
    x = mr
    for shred in pct_shreds:
        x *= 1.0 - shred
    x = max(0.0, x - flat_red)
    for pen in pct_pens:
        x *= 1.0 - pen
    return max(0.0, x - flat_pen)


def magic_mult(mr: float) -> float:
    return 100.0 / (100.0 + mr)


def luden_raw(ap: float) -> float:
    """7.3 isolated echo: 75+8% AP, plus 20+1.2% AP for each of 5 missed bounces."""
    return 175.0 + 0.14 * ap


def comet_raw(level: int, ap: float, minute: int) -> float:
    base = 15.0 + (100.0 - 15.0) * (level - 1) / 14.0
    stacks = max(0, minute - 1)
    return base + 2.0 * stacks + 0.05 * ap


def comet_cd(level: int) -> float:
    return 16.0 - 8.0 * (level - 1) / 14.0


def alternator_raw(level: int) -> float:
    return 25.0 + (60.0 - 25.0) * (level - 1) / 14.0


def shell_sum(n: int) -> int:
    """Mana for the first n shells at full cost (no refund): 25 * n * (n+1)."""
    return 25 * n * (n + 1)


@dataclass
class Loadout:
    names: List[str]
    ap: float
    ah: float
    ult_haste: float
    max_mana: float
    refund: float
    regen_mult: float
    flat_pen: float
    pct_pens: Tuple[float, ...]
    malig: bool
    liandry: bool
    ashes: bool
    blackfire: bool
    horizon: bool
    luden: bool
    orb: bool
    madness: bool
    bloodletter: bool
    alternator: bool
    seraph: bool
    charge_room: float  # mana still chargeable during the fight
    charge_gain: float  # mana per in-fight proc
    level: int
    minute: int


@dataclass
class Prep:
    inventory: Dict[int, List[str]]
    tear_minute: Optional[int]
    arch_minute: Optional[int]
    roa_minute: Optional[int]


def first_owned(inv: Dict[int, List[str]], name: str) -> Optional[int]:
    for minute in range(1, GAME_MINUTES + 1):
        if name in inv[minute]:
            return minute
    return None


def prepare(path: List[str]) -> Prep:
    inv = {
        m: resolve_inventory(path, gold_at_minute(m), m)
        for m in range(1, GAME_MINUTES + 1)
    }
    return Prep(
        inventory=inv,
        tear_minute=first_owned(inv, "Tear of the Goddess"),
        arch_minute=first_owned(inv, "Archangel's Staff"),
        roa_minute=first_owned(inv, "Rod of Ages"),
    )


def tear_charge(minute: int, prep: Prep, owned: Sequence[str]) -> float:
    """Bonus mana from Mana Charge before this minute's fight.

    Poking spends often enough to hit ~80% of the 3-procs-per-10s cap.
    Tear procs are +5. Archangel procs are +14. Cap 700.
    """
    tear_m = prep.tear_minute
    arch_m = prep.arch_minute
    has_tear = "Tear of the Goddess" in owned
    has_arch = "Archangel's Staff" in owned
    if not has_tear and not has_arch:
        return 0.0
    bonus = 0.0
    if has_arch and arch_m is not None:
        if tear_m is not None and tear_m < arch_m:
            bonus += (arch_m - tear_m) * 60.0 * 1.2
        bonus += max(0, minute - arch_m) * 60.0 * 3.36
    elif has_tear and tear_m is not None:
        bonus += max(0, minute - tear_m) * 60.0 * 1.2
    return min(700.0, bonus)


def roa_stacks(minute: int, prep: Prep) -> int:
    if prep.roa_minute is None or minute < prep.roa_minute:
        return 0
    return min(10, int((minute - prep.roa_minute) * 60 / 35))


def loadout_at(prep: Prep, minute: int) -> Loadout:
    level = level_at_minute(minute)
    owned_names = list(prep.inventory[minute])
    owned = [ITEMS[n] for n in owned_names]
    charge = tear_charge(minute, prep, owned_names)
    stacks = roa_stacks(minute, prep)
    has_arch = "Archangel's Staff" in owned_names
    has_tear = "Tear of the Goddess" in owned_names
    seraph = has_arch and charge >= 700.0

    names: List[str] = []
    ap = ah = mana = regen = flat = uh = 0.0
    pcts: List[float] = []
    flags = {
        "malig": False,
        "liandry": False,
        "ashes": False,
        "bf": False,
        "horizon": False,
        "luden": False,
        "orb": False,
        "madness": False,
        "blood": False,
        "alt": False,
        "cap": False,
    }
    for it in owned:
        shown = it.name
        if it.archangel and seraph:
            shown = "Seraph's Embrace"
        names.append(shown)
        ap += it.ap
        ah += it.ah
        uh += it.ult_haste
        regen += it.regen
        flat += it.flat_mpen
        if it.pct_mpen:
            pcts.append(it.pct_mpen)
        if it.name not in ("Tear of the Goddess", "Archangel's Staff"):
            mana += it.mana
        if it.malignance:
            flags["malig"] = True
        if it.liandry:
            flags["liandry"] = True
        if it.ashes:
            flags["ashes"] = True
        if it.blackfire:
            flags["bf"] = True
        if it.horizon:
            flags["horizon"] = True
        if it.luden:
            flags["luden"] = True
        if it.orb:
            flags["orb"] = True
        if it.madness:
            flags["madness"] = True
        if it.bloodletter:
            flags["blood"] = True
        if it.alternator:
            flags["alt"] = True
        if it.deathcap:
            flags["cap"] = True
        if it.roa:
            ap += 4.0 * stacks
            mana += 30.0 * stacks

    refund = 0.0
    charge_gain = 0.0
    charge_room = 0.0
    if seraph:
        mana += 1200.0
        refund = 0.25
        charge_gain = 0.0
        charge_room = 0.0
    elif has_arch:
        mana += 500.0 + charge
        refund = 0.25
        charge_gain = 14.0
        charge_room = max(0.0, 700.0 - charge)
    elif has_tear:
        mana += 200.0 + charge
        refund = 0.10
        charge_gain = 5.0
        charge_room = max(0.0, 700.0 - charge)

    max_mana = base_mana(level) + manaflow_bonus(minute) + mana
    awe = 0.02 if seraph else (0.01 if has_arch else 0.0)
    ap += awe * max_mana
    ap += gathering_ap(minute)
    mult = 1.0
    if flags["bf"]:
        mult *= 1.04  # one burning champion
    if flags["cap"]:
        mult *= 1.30
    ap *= mult
    ah += transcendence_ah(level)

    return Loadout(
        names=names,
        ap=ap,
        ah=ah,
        ult_haste=uh,
        max_mana=max_mana,
        refund=refund,
        regen_mult=1.0 + regen,
        flat_pen=flat,
        pct_pens=tuple(pcts),
        malig=flags["malig"],
        liandry=flags["liandry"],
        ashes=flags["ashes"],
        blackfire=flags["bf"],
        horizon=flags["horizon"],
        luden=flags["luden"],
        orb=flags["orb"],
        madness=flags["madness"],
        bloodletter=flags["blood"],
        alternator=flags["alt"],
        seraph=seraph,
        charge_room=charge_room,
        charge_gain=charge_gain,
        level=level,
        minute=minute,
    )


@dataclass
class FightResult:
    damage: float
    shots: int
    kill_t: Optional[float]
    mana_left: float
    mana_spent: float
    trace: List[dict] = field(default_factory=list)


def fight_value(damage: float, max_hp: float, kill_t: Optional[float], window: float) -> float:
    capped = min(damage, max_hp)
    if kill_t is None:
        return capped
    return capped * (1.0 + KILL_BONUS * (window - kill_t) / window)


def simulate(
    ld: Loadout,
    *,
    max_hp: float,
    mr: float,
    window: float,
    start_frac: float,
    cost_cap: float,
    reset_every: float = 0.0,
    keep_trace: bool = False,
) -> FightResult:
    """Spam Q (to keep the shred up) and R (on cooldown) until mana or the window ends."""
    level = ld.level
    rank = r_rank(level)
    shred_pct = q_shred(level)
    ap = ld.ap
    horizon = 1.10 if ld.horizon else 1.0
    regen = base_mp5(level) / 5.0 * ld.regen_mult
    r_cd_stat = r_cooldown(rank, ld.ah, ld.ult_haste) if rank else 99.0
    q_cd_stat = 6.0 * haste_mult(ld.ah)

    t = 0.0
    max_mana = ld.max_mana
    mana = max_mana * start_frac
    mana_start = mana
    stacks = 0
    last_r = -99.0
    r_cd = 0.0
    q_cd = 0.0
    cast_lock = 0.0
    shred_until = -1.0
    fog_until = -1.0
    burn_until = -1.0
    luden_cd = 0.0
    comet_ready = 0.0
    trans_cd = 0.0
    alt_used = False
    bl_stacks = 0
    bl_until = -1.0
    charge_left = ld.charge_room
    recent_charges: List[float] = []
    hp = max_hp
    dealt = 0.0
    shots = 0
    kill_t: Optional[float] = None
    trace: List[dict] = []
    reset_steps = int(reset_every / DT) if reset_every else 0
    step = 0

    def mr_now() -> float:
        shreds = []
        if t < shred_until:
            shreds.append(shred_pct)
        if ld.bloodletter and t < bl_until and bl_stacks > 0:
            shreds.append(min(0.30, 0.075 * bl_stacks))
        flat_red = 10.0 if (ld.malig and t < fog_until) else 0.0
        return effective_mr(mr, shreds, flat_red, ld.pct_pens, ld.flat_pen)

    def madness() -> float:
        if not ld.madness:
            return 1.0
        return 1.0 + min(0.06, 0.02 * t)

    def apply_dmg(amount: float) -> float:
        nonlocal hp, dealt, kill_t
        if amount <= 0 or hp <= 0:
            return 0.0
        hit = min(hp, amount)
        hp -= hit
        dealt += hit
        if hp <= 0 and kill_t is None:
            kill_t = t
        return hit

    def mitigated(raw: float) -> float:
        return raw * magic_mult(mr_now()) * horizon * madness()

    def proc_item_hits(from_ability: bool) -> None:
        nonlocal luden_cd, comet_ready, alt_used
        if from_ability and ld.luden and luden_cd <= 0:
            apply_dmg(mitigated(luden_raw(ap)))
            luden_cd = 9.0
        if from_ability and comet_ready <= 0:
            apply_dmg(mitigated(comet_raw(level, ap, ld.minute)))
            comet_ready = comet_cd(level)
        if from_ability and ld.alternator and not alt_used:
            apply_dmg(mitigated(alternator_raw(level)))
            alt_used = True

    def spend(cost: float) -> None:
        nonlocal mana, charge_left, max_mana
        pay = cost * (1.0 - ld.refund)
        mana -= pay
        if charge_left <= 0 or ld.charge_gain <= 0:
            return
        recent_charges[:] = [x for x in recent_charges if t - x < 10.0]
        if len(recent_charges) >= 3:
            return
        recent_charges.append(t)
        gain = min(ld.charge_gain, charge_left)
        charge_left -= gain
        max_mana += gain
        mana += gain

    while t < window - 1e-9:
        if reset_steps and step > 0 and step % reset_steps == 0:
            hp = max_hp
        if hp <= 0:
            if not reset_steps:
                break
            t += DT
            step += 1
            continue
        if last_r >= 0 and t - last_r >= 8.0:
            stacks = 0
        if t >= bl_until:
            bl_stacks = 0

        mana = min(max_mana, mana + regen * DT)

        dps = 0.0
        if t < burn_until:
            if ld.liandry:
                dps += 0.02 * max_hp
            elif ld.ashes and not ld.blackfire:
                dps += 5.0  # 15 magic over 3 seconds
            if ld.blackfire:
                dps += 20.0 + 0.02 * ap
        if ld.malig and t < fog_until:
            dps += 60.0 + 0.05 * ap
        if dps > 0 and hp > 0:
            apply_dmg(mitigated(dps * DT))
        if hp <= 0:
            break

        if cast_lock <= 0:
            next_cost = r_mana_cost(stacks) if rank else 0.0
            r_pay = next_cost * (1.0 - ld.refund)
            q_pay = q_cost_base() * (1.0 - ld.refund)
            shred_down = t >= shred_until
            willing_r = rank > 0 and next_cost <= cost_cap + 1e-6
            if willing_r:
                can_q = q_cd <= 0 and shred_down and mana >= q_pay + r_pay
            else:
                can_q = q_cd <= 0 and shred_down and mana >= q_pay
            can_r = (
                willing_r
                and r_cd <= 0
                and mana >= r_pay - 1e-6
            )
            if can_q:
                spend(q_cost_base())
                raw = q_raw(level, ap)
                hit = apply_dmg(mitigated(raw))
                proc_item_hits(True)
                shred_until = t + 4.0
                burn_until = max(burn_until, t + 3.0)
                q_cd = max(0.25, q_cd_stat)
                if level >= 9 and trans_cd <= 0:
                    q_cd *= 0.92
                    trans_cd = 8.0
                cast_lock = 0.25
                if keep_trace:
                    trace.append(
                        {"t": round(t, 2), "kind": "Q", "cost": 40, "hit": round(hit, 1),
                         "hp": round(hp, 0)}
                    )
            elif can_r:
                spend(next_cost)
                frac = hp / max_hp if max_hp else 1.0
                raw = r_raw(rank, ap, frac)
                if ld.orb and frac < 0.40:
                    raw *= 1.20
                hit = apply_dmg(mitigated(raw))
                proc_item_hits(True)
                stacks = min(9, stacks + 1)
                last_r = t
                shots += 1
                fog_until = t + 3.0
                burn_until = max(burn_until, t + 3.0)
                if ld.bloodletter:
                    if t >= bl_until:
                        bl_stacks = 0
                    bl_stacks = min(4, bl_stacks + 1)
                    bl_until = t + 6.0
                r_cd = max(0.25, r_cd_stat)
                cast_lock = 0.25
                if keep_trace:
                    trace.append(
                        {
                            "t": round(t, 2),
                            "kind": "R",
                            "cost": int(next_cost),
                            "stacks": stacks,
                            "hit": round(hit, 1),
                            "hp": round(hp, 0),
                        }
                    )

        r_cd = max(0.0, r_cd - DT)
        q_cd = max(0.0, q_cd - DT)
        cast_lock = max(0.0, cast_lock - DT)
        luden_cd = max(0.0, luden_cd - DT)
        comet_ready = max(0.0, comet_ready - DT)
        trans_cd = max(0.0, trans_cd - DT)
        t += DT
        step += 1

    return FightResult(
        damage=dealt,
        shots=shots,
        kill_t=kill_t,
        mana_left=max(0.0, mana),
        mana_spent=mana_start - mana,
        trace=trace,
    )


# ---------------------------------------------------------------------------
# Snapshots
# ---------------------------------------------------------------------------


@dataclass
class Snapshot:
    minute: int
    build: str
    items: List[str]
    gold: int
    level: int
    ap: float
    ah: float
    ult_haste: float
    max_mana: float
    refund: float
    r_cd: float
    legendary_count: int
    seraph: bool
    half_tank: float
    half_tank_shots: int
    half_tank_kill: Optional[float]
    half_squish: float
    half_squish_kill: Optional[float]
    full_tank: float
    full_tank_shots: int
    full_tank_kill: Optional[float]
    full_squish: float
    siege_half: float
    siege_full: float
    cap_half: int
    cap_full: int
    score: float
    notes: str


def _note(ld: Loadout) -> str:
    bits = []
    if ld.malig:
        bits.append("Hatefog+UH")
    if ld.horizon:
        bits.append("Horizon")
    if ld.liandry:
        bits.append("%HP burn")
    if ld.blackfire:
        bits.append("Blackfire")
    if ld.luden:
        bits.append("Echo")
    if any(p >= 0.30 for p in ld.pct_pens):
        bits.append("%pen")
    if ld.orb:
        bits.append("Orb")
    if ld.bloodletter:
        bits.append("MR shred")
    if ld.seraph or ld.refund >= 0.25:
        bits.append("25% refund")
    elif ld.refund >= 0.10:
        bits.append("10% refund")
    if not any(n in LEGENDARIES for n in ld.names):
        bits.append("components")
    return ", ".join(bits) if bits else "-"


def best_cap(
    ld: Loadout,
    *,
    start_frac: float,
    tank_hp_v: float,
    tank_mr_v: float,
    squish_hp_v: float,
    squish_mr_v: float,
) -> Tuple[int, FightResult, FightResult]:
    best_key = -1.0
    best: Tuple[int, FightResult, FightResult] = (500, FightResult(0, 0, None, 0, 0), FightResult(0, 0, None, 0, 0))
    for cap in COST_CAPS:
        tank = simulate(
            ld, max_hp=tank_hp_v, mr=tank_mr_v, window=FIGHT_WINDOW,
            start_frac=start_frac, cost_cap=cap,
        )
        squish = simulate(
            ld, max_hp=squish_hp_v, mr=squish_mr_v, window=FIGHT_WINDOW,
            start_frac=start_frac, cost_cap=cap,
        )
        value = TANK_WEIGHT * fight_value(tank.damage, tank_hp_v, tank.kill_t, FIGHT_WINDOW)
        value += SQUISH_WEIGHT * fight_value(squish.damage, squish_hp_v, squish.kill_t, FIGHT_WINDOW)
        if value > best_key:
            best_key = value
            best = (cap, tank, squish)
    return best


def take_snapshot(build: str, prep: Prep, minute: int) -> Snapshot:
    ld = loadout_at(prep, minute)
    thp, tmr = tank_hp(minute), tank_mr(minute)
    shp, smr = squishy_hp(minute), squishy_mr(minute)
    cap_h, half_t, half_s = best_cap(
        ld, start_frac=0.50, tank_hp_v=thp, tank_mr_v=tmr, squish_hp_v=shp, squish_mr_v=smr,
    )
    cap_f, full_t, full_s = best_cap(
        ld, start_frac=1.00, tank_hp_v=thp, tank_mr_v=tmr, squish_hp_v=shp, squish_mr_v=smr,
    )
    siege_h = simulate(
        ld, max_hp=thp, mr=tmr, window=SIEGE_WINDOW, start_frac=0.50,
        cost_cap=cap_h, reset_every=SIEGE_RESET,
    )
    siege_f = simulate(
        ld, max_hp=thp, mr=tmr, window=SIEGE_WINDOW, start_frac=1.00,
        cost_cap=cap_f, reset_every=SIEGE_RESET,
    )
    fight = HALF_WEIGHT * (
        TANK_WEIGHT * fight_value(half_t.damage, thp, half_t.kill_t, FIGHT_WINDOW)
        + SQUISH_WEIGHT * fight_value(half_s.damage, shp, half_s.kill_t, FIGHT_WINDOW)
    )
    fight += FULL_WEIGHT * (
        TANK_WEIGHT * fight_value(full_t.damage, thp, full_t.kill_t, FIGHT_WINDOW)
        + SQUISH_WEIGHT * fight_value(full_s.damage, shp, full_s.kill_t, FIGHT_WINDOW)
    )
    siege = HALF_WEIGHT * siege_h.damage + FULL_WEIGHT * siege_f.damage
    # Per-second so the 40s siege does not drown the 12s fight.
    score = FIGHT_WEIGHT * (fight / FIGHT_WINDOW) + SIEGE_WEIGHT * (siege / SIEGE_WINDOW)
    rank = r_rank(ld.level)
    cd = r_cooldown(rank, ld.ah, ld.ult_haste) if rank else 0.0
    return Snapshot(
        minute=minute,
        build=build,
        items=ld.names,
        gold=gold_at_minute(minute),
        level=ld.level,
        ap=round(ld.ap, 1),
        ah=ld.ah,
        ult_haste=ld.ult_haste,
        max_mana=round(ld.max_mana, 0),
        refund=ld.refund,
        r_cd=round(cd, 2),
        legendary_count=sum(1 for n in ld.names if n in LEGENDARIES),
        seraph=ld.seraph,
        half_tank=round(half_t.damage, 1),
        half_tank_shots=half_t.shots,
        half_tank_kill=None if half_t.kill_t is None else round(half_t.kill_t, 2),
        half_squish=round(half_s.damage, 1),
        half_squish_kill=None if half_s.kill_t is None else round(half_s.kill_t, 2),
        full_tank=round(full_t.damage, 1),
        full_tank_shots=full_t.shots,
        full_tank_kill=None if full_t.kill_t is None else round(full_t.kill_t, 2),
        full_squish=round(full_s.damage, 1),
        siege_half=round(siege_h.damage, 1),
        siege_full=round(siege_f.damage, 1),
        cap_half=cap_h,
        cap_full=cap_f,
        score=round(score, 2),
        notes=_note(ld),
    )


def run_all() -> Tuple[Dict[str, List[Snapshot]], Dict[str, Prep]]:
    prepared = {name: prepare(path) for name, path in BUILD_PATHS.items()}
    results = {
        name: [take_snapshot(name, prep, m) for m in range(1, GAME_MINUTES + 1)]
        for name, prep in prepared.items()
    }
    return results, prepared


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------


def fmt_kill(kill: Optional[float], hp: float, dealt: float) -> str:
    if kill is None:
        pct = 100.0 * dealt / hp if hp else 0
        return f"{pct:.0f}%"
    return f"KILL {kill:.1f}s"


def item_line(items: List[str], limit: int = 6) -> str:
    shown = items[:limit]
    text = " › ".join(shown) if shown else "(nothing)"
    if len(items) > limit:
        text += " › …"
    return text


def avg_score(snaps: List[Snapshot]) -> float:
    window = [s for s in snaps if s.minute >= 6]
    return sum(s.score for s in window) / len(window)


def first_minute(snaps: List[Snapshot], pred) -> Optional[int]:
    for s in snaps:
        if pred(s):
            return s.minute
    return None


def summarize(results: Dict[str, List[Snapshot]], prepared: Dict[str, Prep]) -> str:
    ranking = sorted(results.items(), key=lambda kv: avg_score(kv[1]), reverse=True)
    winner, win_snaps = ranking[0]

    lines: List[str] = []
    lines.append("=" * 88)
    lines.append("AP KOG'MAW — SPAM R   (Wild Rift 7.3, Living Artillery from 7.2c)")
    lines.append("Playstyle: Q shred, then R on cooldown. No W, no E.")
    lines.append("R mana: 50 per shell + 50 per stack, cap 500. Stacks fall off after 8s.")
    lines.append("R rank 1/2/3 cooldown: 2s / 1s / 1s. Damage 80/120/160 + 25% AP, doubles below 40% HP.")
    lines.append("Score: 60% half-mana (already poking) + 40% full-mana.")
    lines.append("Inside a 12s fight: 62% tank / 38% squishy, damage stops at the health bar.")
    lines.append("Plus a 40s siege vs a tank who returns to full HP every 8s (mana sustain).")
    lines.append("The target stands in the shells. No heal, no shield, no sidestep. Real games are lower.")
    lines.append("Runes: Arcane Comet, Manaflow Band, Transcendence, Gathering Storm.")
    lines.append("=" * 88)
    lines.append("")
    lines.append("GOLD / LEVEL / TARGETS / BASE MANA")
    lines.append(
        f"  {'Min':>3}  {'Gold':>6}  {'Lvl':>3}  {'Tank HP':>8}  {'Tank MR':>7}  "
        f"{'Squish HP':>9}  {'Base MP':>7}"
    )
    for m in (1, 4, 6, 8, 10, 12, 14, 16, 18, 20):
        lv = level_at_minute(m)
        lines.append(
            f"  {m:>3}  {gold_at_minute(m):>6}  {lv:>3}  {tank_hp(m):>8.0f}  {tank_mr(m):>7.0f}  "
            f"{squishy_hp(m):>9.0f}  {base_mana(lv):>7.0f}"
        )

    lines.append("")
    lines.append("-" * 88)
    lines.append("MINUTE-BY-MINUTE BEST SPAM-R SCORE")
    lines.append("-" * 88)
    for m in range(1, GAME_MINUTES + 1):
        best_name, best_snaps = max(results.items(), key=lambda kv: kv[1][m - 1].score)
        s = best_snaps[m - 1]
        lines.append(
            f"  {m:>2}:00 | score {s.score:>7.1f} | half-tank {s.half_tank:>6.0f} "
            f"({s.half_tank_shots}R) | full-tank {s.full_tank:>6.0f} ({s.full_tank_shots}R) | {best_name}"
        )
        lines.append(
            f"         {item_line(s.items)}  |  {s.notes}  |  mana {s.max_mana:.0f}  |  cap {s.cap_half}/{s.cap_full}"
        )

    lines.append("")
    lines.append("-" * 88)
    lines.append("BUILD COMPARISON")
    lines.append("Avg = score from 6:00–20:00. ½T16 = half-mana tank damage in the 12s fight.")
    lines.append("Siege = 40s tank damage from full mana, target reset to full every 8s.")
    lines.append("-" * 88)
    lines.append(
        f"  {'Build':<32} {'Avg':>7} {'½T12':>7} {'½T16':>7} {'½R':>4} "
        f"{'FT16':>7} {'Sg16':>7} {'Mana':>6} {'Cap':>5}"
    )
    for name, snaps in ranking:
        s12, s16 = snaps[11], snaps[15]
        lines.append(
            f"  {name:<32} {avg_score(snaps):>7.1f} {s12.half_tank:>7.0f} {s16.half_tank:>7.0f} "
            f"{s16.half_tank_shots:>4} {s16.full_tank:>7.0f} {s16.siege_full:>7.0f} "
            f"{s16.max_mana:>6.0f} {s16.cap_half:>5}"
        )

    spike = first_minute(win_snaps, lambda s: s.legendary_count >= 3) or 16
    spike = min(20, max(12, spike))
    sp = win_snaps[spike - 1]
    thp, tmr = tank_hp(spike), tank_mr(spike)

    lines.append("")
    lines.append("-" * 88)
    lines.append(f"{spike}:00 DETAIL  (tank / squishy, half mana then full mana)")
    lines.append("-" * 88)
    for name, snaps in ranking:
        s = snaps[spike - 1]
        lines.append(
            f"  {name:<32} AP {s.ap:>6.0f}  AH {s.ah:>4.0f}  UH {s.ult_haste:>3.0f}  "
            f"R cd {s.r_cd:.2f}s  mana {s.max_mana:.0f}"
        )
        lines.append(
            f"    half  tank {s.half_tank:>6.0f} ({fmt_kill(s.half_tank_kill, thp, s.half_tank):>10})  "
            f"{s.half_tank_shots}R  cap {s.cap_half}   "
            f"squish {s.half_squish:>6.0f} ({fmt_kill(s.half_squish_kill, squishy_hp(spike), s.half_squish)})"
        )
        lines.append(
            f"    full  tank {s.full_tank:>6.0f} ({fmt_kill(s.full_tank_kill, thp, s.full_tank):>10})  "
            f"{s.full_tank_shots}R  cap {s.cap_full}   "
            f"siege40 {s.siege_full:>6.0f}"
        )
        lines.append(f"    items: {item_line(s.items, 8)}")

    # Cadence table for the winner, half-mana tank, at the spike.
    ld = loadout_at(prepared[winner], spike)
    lines.append("")
    lines.append("-" * 88)
    lines.append(
        f"HOW TO PRESS R  —  {winner} at {spike}:00, tank "
        f"({thp:.0f} HP / {tmr:.0f} MR)"
    )
    lines.append("Cap = stop when the next shell would cost more than this, then let the 8s timer fall off.")
    lines.append("-" * 88)
    lines.append(
        f"  {'Cap':>5}  {'½Tank':>7}  {'½Shots':>6}  {'½Kill':>10}  "
        f"{'Full':>7}  {'FShots':>6}  {'FKill':>10}"
    )
    best_cap_row = None
    best_cap_value = -1.0
    for cap in COST_CAPS:
        half_f = simulate(
            ld, max_hp=thp, mr=tmr, window=FIGHT_WINDOW,
            start_frac=0.50, cost_cap=cap,
        )
        full_f = simulate(
            ld, max_hp=thp, mr=tmr, window=FIGHT_WINDOW,
            start_frac=1.00, cost_cap=cap,
        )
        value = fight_value(half_f.damage, thp, half_f.kill_t, FIGHT_WINDOW)
        if value > best_cap_value:
            best_cap_value = value
            best_cap_row = cap
        half_k = "—" if half_f.kill_t is None else f"{half_f.kill_t:.1f}s"
        full_k = "—" if full_f.kill_t is None else f"{full_f.kill_t:.1f}s"
        lines.append(
            f"  {cap:>5}  {half_f.damage:>7.0f}  {half_f.shots:>6}  {half_k:>10}  "
            f"{full_f.damage:>7.0f}  {full_f.shots:>6}  {full_k:>10}"
        )

    traced = simulate(
        ld, max_hp=thp, mr=tmr, window=FIGHT_WINDOW,
        start_frac=0.50, cost_cap=float(sp.cap_half), keep_trace=True,
    )
    lines.append("")
    lines.append(
        f"Half-mana trace at the scored cap {sp.cap_half} "
        "(Q is the 40-mana shred, R is the shell):"
    )
    for ev in traced.trace:
        if ev["kind"] == "Q":
            lines.append(f"  {ev['t']:>5.2f}s  Q   cost  40   hit {ev['hit']:>6.0f}   hp {ev['hp']:>6.0f}")
        else:
            lines.append(
                f"  {ev['t']:>5.2f}s  R   cost {ev['cost']:>3}   hit {ev['hit']:>6.0f}   "
                f"hp {ev['hp']:>6.0f}   stack {ev['stacks']}"
            )
    if not traced.trace:
        lines.append("  (no casts)")

    def owns(name: str, snaps: List[Snapshot]) -> Optional[int]:
        for s in snaps:
            if name in s.items:
                return s.minute
        return None

    lines.append("")
    lines.append("-" * 88)
    lines.append("VERDICT")
    lines.append("-" * 88)
    lines.append(f"  Best spam-R path: {winner}")
    lines.append(f"  Avg score 6:00–20:00: {avg_score(win_snaps):.1f}")
    for label, item_name in (
        ("Malignance", "Malignance"),
        ("Luden's Echo", "Luden's Echo"),
        ("Archangel / Seraph", "Seraph's Embrace"),
        ("Horizon Focus", "Horizon Focus"),
        ("Liandry's Torment", "Liandry's Torment"),
        ("Void Staff", "Void Staff"),
        ("Infinity Orb", "Infinity Orb"),
        ("Spellslinger's Shoes", "Spellslinger's Shoes"),
        ("Rabadon's Deathcap", "Rabadon's Deathcap"),
        ("Blackfire Torch", "Blackfire Torch"),
        ("Rod of Ages", "Rod of Ages"),
    ):
        minute_on = owns(item_name, win_snaps)
        if item_name == "Seraph's Embrace" and minute_on is None:
            minute_on = owns("Archangel's Staff", win_snaps)
            if minute_on is not None:
                label = "Archangel's Staff"
        if minute_on is not None:
            lines.append(f"  {label} online: ~{minute_on}:00")

    s = sp
    kill_bit = (
        f"kills at {s.half_tank_kill:.1f}s"
        if s.half_tank_kill is not None
        else f"{100.0 * s.half_tank / thp:.0f}% of the bar, no kill"
    )
    lines.append("")
    lines.append(
        f"  At {spike}:00, half mana, this path puts {s.half_tank:.0f} into a "
        f"{thp:.0f} HP / {tmr:.0f} MR tank ({s.half_tank_shots} shells, {kill_bit})."
    )
    lines.append(
        f"  Full mana: {s.full_tank:.0f} in {s.full_tank_shots} shells. "
        f"40s siege from full mana: {s.siege_full:.0f}."
    )
    lines.append(
        f"  Pool is {s.max_mana:.0f} mana, R cooldown {s.r_cd:.2f}s. "
        f"Scored caps: {s.cap_half} on half mana, {s.cap_full} on a full bar. "
        f"Fastest tank kill in the table: cap {best_cap_row}."
    )
    lines.append(
        "  On a half bar, a 250-mana shell refreshes the stack timer and the tank lives. "
        "Let the 8s timer fall off. The second volley is the kill."
    )

    lines.append("")
    lines.append("  MANA LADDER (no refund):")
    lines.append("  Shells 1–4 cost 50+100+150+200 = 500. Shells 5–7 add 250+300+350 = 900.")
    lines.append("  Shells 8–10 add 400+450+500 = 1350. Damage per mana falls off immediately.")
    lines.append("  Archangel and Seraph refund 25% of that. Tear refunds 10%. Nothing else does.")
    lines.append("  Rank 2 R (level 9, ~8:00) is a 1.0s base cooldown. Malignance's 20")
    lines.append("  ultimate haste already puts that under a second. Further haste boots")
    lines.append("  add almost no shells. Mana is what adds shells.")
    lines.append("")
    lines.append("  WHY THESE ITEMS:")
    lines.append("  • Malignance is the artillery item: 500 mana, 20 ultimate haste, Hatefog")
    lines.append("    (60+5% AP per second and 10 MR shred while you keep casting).")
    lines.append("  • Horizon Focus is 10% damage on a hit from 600+ range. R is 1100/1300/1500.")
    lines.append("    The amp is on every shell and every burn.")
    lines.append("  • Liandry is 2% max HP per second, refreshed by R. It is the long tank fight.")
    lines.append("    It gives no mana and no haste.")
    lines.append("  • Void Staff is 40% magic pen. Spellslinger adds 18 flat and 8% more,")
    lines.append("    and it cannot be bought before 10:00.")
    lines.append("  • Infinity Orb's 20% bonus starts below 40% HP, the same line where R doubles.")
    lines.append("    A healthy tank never sees it.")
    lines.append("  • Luden's isolated echo (7.3) is 175+14% AP every 9 seconds. One or two procs.")
    lines.append("    It does not refund mana. Tier-3 mage items no longer grant 7% pen.")
    lines.append("  • Seraph refunds a quarter of every shell and holds 1200 mana, but the")
    lines.append("    charge takes minutes and the shells are still weak without pen and Horizon.")
    lines.append("  • Max Q. Caustic Spittle is 20–32% MR shred for 4 seconds and a 65% AP hit.")
    lines.append("    W is the on-hit build, which is a different sim.")
    lines.append("  • E stays uncast in this pattern. Its mana is another shell, and the")
    lines.append("    target in this sim already stands in the artillery.")
    lines.append("")
    seraph_key = "Tear → Seraph → Horizon"
    if seraph_key in results:
        ser = results[seraph_key][spike - 1]
        if ser.full_tank_kill is not None:
            full_bit = f"kills at {ser.full_tank_kill:.1f}s"
        else:
            full_bit = f"{ser.full_tank:.0f} on the bar"
        lines.append(
            f"  Seraph on this minute: half {ser.half_tank:.0f} ({ser.half_tank_shots}R), "
            f"full {full_bit} ({ser.full_tank_shots}R) from {ser.max_mana:.0f} mana. "
            "The refund buys shells. Hatefog plus the burn still clears more of a half bar."
        )
        lines.append("")
    late_name, late_snaps = max(results.items(), key=lambda kv: kv[1][-1].score)
    if late_name != winner:
        lines.append(
            f"  At 20:00 the highest single minute is {late_name} "
            f"({late_snaps[-1].score:.1f} vs {win_snaps[-1].score:.1f}). "
            f"From 6:00 to 20:00 this path still leads "
            f"({avg_score(win_snaps):.1f} vs {avg_score(ranking[1][1]):.1f} for {ranking[1][0]})."
        )
        lines.append("")
    lines.append("  SAME TARGET, OTHER PATHS at the spike (half-mana tank):")
    for name, snaps in ranking[1:6]:
        o = snaps[spike - 1]
        lines.append(
            f"  • {name}: {o.half_tank:.0f} ({o.half_tank_shots}R, cap {o.cap_half}), "
            f"full {o.full_tank:.0f}, siege {o.siege_full:.0f}, mana {o.max_mana:.0f}"
        )
    lines.append("")
    lines.append("  The target stands still. Real artillery misses. The order above is the part")
    lines.append("  that still holds when they do.")
    lines.append("  PC LoL spam-R is a different sim (40→400 mana, Malignance/Horizon/Void).")
    lines.append("=" * 88)
    return "\n".join(lines)


def export_json(results: Dict[str, List[Snapshot]], path: Path) -> None:
    payload = {
        "meta": {
            "champion": "Kog'Maw",
            "game": "Wild Rift",
            "patch": "7.3",
            "ult_patch": "7.2c",
            "game_minutes": GAME_MINUTES,
            "playstyle": "Q shred then Living Artillery on cooldown",
            "r_mana": "50 to 500 by stacks, 8s reset",
            "fight_window": FIGHT_WINDOW,
            "siege_window": SIEGE_WINDOW,
        },
        "builds": {
            name: [
                {
                    "minute": s.minute,
                    "items": s.items,
                    "gold": s.gold,
                    "level": s.level,
                    "ap": s.ap,
                    "ah": s.ah,
                    "ult_haste": s.ult_haste,
                    "max_mana": s.max_mana,
                    "refund": s.refund,
                    "r_cd": s.r_cd,
                    "legendary_count": s.legendary_count,
                    "seraph": s.seraph,
                    "half_tank": s.half_tank,
                    "half_tank_shots": s.half_tank_shots,
                    "half_tank_kill": s.half_tank_kill,
                    "half_squish": s.half_squish,
                    "full_tank": s.full_tank,
                    "full_tank_shots": s.full_tank_shots,
                    "full_squish": s.full_squish,
                    "siege_half": s.siege_half,
                    "siege_full": s.siege_full,
                    "cap_half": s.cap_half,
                    "cap_full": s.cap_full,
                    "score": s.score,
                    "notes": s.notes,
                }
                for s in snaps
            ]
            for name, snaps in results.items()
        },
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def self_check(results: Dict[str, List[Snapshot]], prepared: Dict[str, Prep]) -> None:
    assert r_mana_cost(0) == 50
    assert r_mana_cost(3) == 200
    assert r_mana_cost(9) == 500
    assert r_mana_cost(12) == 500
    assert shell_sum(4) == 500
    assert shell_sum(7) == 1400

    full = r_raw(3, 200, 1.0)
    low = r_raw(3, 200, 0.30)
    mid = r_raw(3, 200, 0.70)  # 30% missing → 25% amp
    assert abs(low / full - 2.0) < 1e-9
    assert abs(mid / full - 1.25) < 1e-9
    assert r_raw(3, 200, 0.40) / full == 1.5  # 60% missing caps the non-execute amp

    bare = effective_mr(100, [], 0, [], 0)
    shredded = effective_mr(100, [0.32], 10, [], 0)
    penned = effective_mr(100, [0.32], 10, [0.40, 0.08], 18)
    assert bare > shredded > penned >= 0

    malig = results["Malig → Horizon → Void"]
    seraph = results["Tear → Seraph → Horizon"]
    spell = results["Malig → Spellslinger → Void"]

    assert all(s.half_tank_shots == 0 for s in malig if s.minute <= 3), "R before level 5"
    assert malig[3].half_tank_shots >= 1  # minute 4, level 5

    assert all("Spellslinger's Shoes" not in s.items for s in spell if s.minute < 10)
    assert any("Spellslinger's Shoes" in s.items for s in spell)

    # Seraph's pool is the spam pool. It must pass Malignance once the charge finishes.
    assert seraph[15].max_mana > malig[15].max_mana, (seraph[15].max_mana, malig[15].max_mana)
    assert seraph[15].seraph or seraph[15].refund >= 0.25

    for snaps in results.values():
        for s in snaps:
            assert s.score == s.score  # not NaN
            assert s.half_tank < tank_hp(s.minute) * 1.01 + 1
            assert s.full_tank < tank_hp(s.minute) * 1.01 + 1
            assert s.ap >= 0

    # Same cadence: a full bar can copy the half-bar pattern and still have mana left.
    ld16 = loadout_at(prepared["Malig → Horizon → Void"], 16)
    thp16, tmr16 = tank_hp(16), tank_mr(16)
    full16 = simulate(
        ld16, max_hp=thp16, mr=tmr16, window=FIGHT_WINDOW, start_frac=1.0, cost_cap=500,
    )
    half16 = simulate(
        ld16, max_hp=thp16, mr=tmr16, window=FIGHT_WINDOW, start_frac=0.5, cost_cap=500,
    )
    assert full16.damage + 1 >= half16.damage, (full16.damage, half16.damage)
    assert full16.shots >= half16.shots

    done = malig[11]
    assert "Malignance" in done.items
    assert "Lost Chapter" not in done.items
    assert "Blasting Wand" not in done.items

    # Void actually increases tank damage versus the same fight with the pen stripped.
    void_minute = first_minute(malig, lambda s: "Void Staff" in s.items)
    assert void_minute is not None, [s.items for s in malig]
    ld = loadout_at(prepared["Malig → Horizon → Void"], void_minute)
    stripped = Loadout(**{**ld.__dict__, "pct_pens": tuple(p for p in ld.pct_pens if p < 0.40)})
    thp, tmr = tank_hp(void_minute), tank_mr(void_minute)
    with_void = simulate(ld, max_hp=thp, mr=tmr, window=FIGHT_WINDOW, start_frac=1.0, cost_cap=500)
    no_void = simulate(stripped, max_hp=thp, mr=tmr, window=FIGHT_WINDOW, start_frac=1.0, cost_cap=500)
    assert with_void.damage > no_void.damage, (with_void.damage, no_void.damage)


def main() -> None:
    results, prepared = run_all()
    self_check(results, prepared)
    report = summarize(results, prepared)
    print(report)
    out = Path(__file__).resolve().parent
    (out / "report.txt").write_text(report + "\n", encoding="utf-8")
    export_json(results, out / "results.json")
    print(f"\nWrote {out / 'report.txt'} and {out / 'results.json'}")


if __name__ == "__main__":
    main()
