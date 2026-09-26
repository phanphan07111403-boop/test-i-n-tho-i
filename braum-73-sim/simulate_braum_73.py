#!/usr/bin/env python3
"""
Wild Rift 7.3 — Braum support: full item path and rune page.

Playstyle: bodyguard ADC. W-dash onto the carry, E-block the projectile,
Q to start Concussive Blows. R is a knock-up / zone, not an item gate.

Question:
  On patch 7.3, which item path AND legal rune page peak peel for a
  20-minute Braum support? Yordle Trap was reworked to proc on slow
  (Winter's Bite now lights Catcher). Aftershock is gone (Ice Overlord).
  Guardian is the bodyguard keystone.

Rune loadout: 1 keystone + 3 primary (one per Resolve row) + 1 secondary
from a different path. Ingenious Hunter is gone. Aftershock is gone.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import json
import os

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
GAME_MINUTES = 20
FIGHT_WINDOW = 8.0
FIGHT_EVERY = 42.0


def lerp(lo: float, hi: float, level: int) -> float:
    return lo + (hi - lo) * (level - 1) / 14.0


def haste_cdr(ah: float) -> float:
    return 100.0 / (100.0 + max(0.0, ah))


def mit(stat: float) -> float:
    return 100.0 / (100.0 + max(0.0, stat))


# ---------------------------------------------------------------------------
# Economy / XP (tank support on a 20-minute WR curve)
# ---------------------------------------------------------------------------


def gold_at_minute(m: int) -> int:
    if m <= 0:
        return 500
    total = 500  # start + Relic Shield
    for t in range(1, m + 1):
        if t <= 4:
            total += 280
        elif t <= 10:
            total += 410
        else:
            total += 500
    return total


def level_at_minute(m: int) -> int:
    # WR cap 15. Ult ranks at 5 / 9 / 13.
    table = {
        1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7, 7: 8, 8: 8,
        9: 9, 10: 10, 11: 10, 12: 11, 13: 11, 14: 12,
        15: 12, 16: 13, 17: 13, 18: 14, 19: 14, 20: 15,
    }
    return table.get(m, min(15, 1 + m))


def skill_rank(level: int, skill: str) -> int:
    """Max Q, early W for the dash, then E. R at 5/9/13."""
    if skill == "R":
        if level < 5:
            return 0
        if level < 9:
            return 1
        if level < 13:
            return 2
        return 3
    q_levels = [1, 4, 6, 7]
    e_levels = [3, 8, 10, 11]
    w_levels = [2, 12, 14, 15]
    mapping = {"Q": q_levels, "E": e_levels, "W": w_levels}
    return sum(1 for lv in mapping[skill] if level >= lv)


def soulcast_stacks(minute: int) -> int:
    if minute < 6:
        return 0
    return min(10, minute - 5)


# ---------------------------------------------------------------------------
# Items (Wild Rift 7.3 listed stats)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Item:
    name: str
    cost: int
    hp: float = 0
    armor: float = 0
    mr: float = 0
    ah: float = 0
    ap: float = 0
    mana: float = 0
    hsp: float = 0
    aa_red: float = 0
    ult_haste: float = 0
    tenacity: float = 0
    locket: bool = False
    vow: bool = False
    frozen: bool = False
    yordle: bool = False
    virtue: bool = False
    warmog: bool = False
    thorn: bool = False
    fon: bool = False
    zeke: bool = False
    redemption: bool = False
    randuin: bool = False
    kaenic: bool = False
    amaranth: bool = False
    armored: bool = False
    tags: Tuple[str, ...] = ()


ITEMS: Dict[str, Item] = {
    "Relic Shield": Item("Relic Shield", 500, hp=125, tags=("support",)),
    "Bulwark of the Mountain": Item(
        "Bulwark of the Mountain", 0, hp=175, ah=10, tags=("support",)
    ),
    "Boots of Speed": Item("Boots of Speed", 400, tags=("boots",)),
    "Cloth Armor": Item("Cloth Armor", 500, armor=15),
    "Null-Magic Mantle": Item("Null-Magic Mantle", 500, mr=25),
    "Ruby Crystal": Item("Ruby Crystal", 500, hp=200),
    "Kindlegem": Item("Kindlegem", 1000, hp=200, ah=10),
    "Chain Vest": Item("Chain Vest", 900, armor=40),
    "Warden's Mail": Item("Warden's Mail", 1050, armor=40),
    "Glacial Shroud": Item("Glacial Shroud", 1000, armor=20, ah=10, mana=250),
    "Giant's Belt": Item("Giant's Belt", 1000, hp=350),
    "Bramble Vest": Item("Bramble Vest", 1000, armor=35, tags=("antiheal",)),
    "Spectre's Cowl": Item("Spectre's Cowl", 1100, hp=200, mr=35),
    "Negatron Cloak": Item("Negatron Cloak", 900, mr=40),
    "Winged Moonplate": Item("Winged Moonplate", 900, hp=150),
    "Fiendish Codex": Item("Fiendish Codex", 900, ap=35, ah=10),
    "Forbidden Idol": Item("Forbidden Idol", 700, hsp=0.08),
    "Plated Steelcaps": Item(
        "Plated Steelcaps",
        1200,
        hp=150,
        armor=25,
        aa_red=0.10,
        tags=("boots",),
    ),
    "Mercury's Treads": Item(
        "Mercury's Treads",
        1200,
        hp=150,
        mr=25,
        tenacity=0.30,
        tags=("boots",),
    ),
    "Armored Advance": Item(
        "Armored Advance",
        2200,
        hp=150,
        armor=30,
        aa_red=0.10,
        armored=True,
        tags=("boots",),
    ),
    # 7.3 rework: Catcher on slow OR immobilize. Q 70% slow procs it.
    # Same cart as Locket / Zeke (Kindlegem + Cloth + Null).
    "Yordle Trap": Item(
        "Yordle Trap",
        2400,
        hp=200,
        armor=20,
        mr=20,
        ah=15,
        yordle=True,
        tags=("catcher",),
    ),
    "Zeke's Convergence": Item(
        "Zeke's Convergence",
        2400,
        hp=300,
        armor=25,
        mr=25,
        ah=10,
        ult_haste=10,
        zeke=True,
        tags=("ult",),
    ),
    "Knight's Vow": Item(
        "Knight's Vow",
        2450,
        hp=200,
        armor=40,
        ah=10,
        vow=True,
        tags=("peel", "bodyguard"),
    ),
    "Redemption": Item(
        "Redemption",
        2450,
        ap=40,
        ah=10,
        hsp=0.08,
        redemption=True,
        tags=("active", "heal"),
    ),
    "Frozen Heart": Item(
        "Frozen Heart",
        2550,
        armor=80,
        ah=20,
        mana=400,
        frozen=True,
        tags=("peel", "anti-adc"),
    ),
    "Locket of the Iron Solari": Item(
        "Locket of the Iron Solari",
        2600,
        hp=200,
        armor=30,
        mr=30,
        ah=10,
        locket=True,
        tags=("peel", "active"),
    ),
    # 7.3 recipe: Cloth + Null + Giant's Belt (no longer Kindlegem + Vest).
    "Radiant Virtue": Item(
        "Radiant Virtue",
        2650,
        hp=300,
        armor=30,
        mr=30,
        ah=10,
        virtue=True,
        tags=("ult",),
    ),
    "Thornmail": Item(
        "Thornmail", 2700, hp=200, armor=75, thorn=True, tags=("antiheal",)
    ),
    "Force of Nature": Item(
        "Force of Nature", 2800, hp=400, mr=60, fon=True, tags=("mr",)
    ),
    "Randuin's Omen": Item(
        "Randuin's Omen", 2800, hp=400, armor=75, randuin=True, tags=("crit",)
    ),
    "Kaenic Rookern": Item(
        "Kaenic Rookern", 2800, hp=350, mr=80, kaenic=True, tags=("mr",)
    ),
    "Warmog's Armor": Item(
        "Warmog's Armor",
        2850,
        hp=700,
        ah=20,
        warmog=True,
        tags=("hp",),
    ),
    "Amaranth's Twinguard": Item(
        "Amaranth's Twinguard",
        3200,
        hp=300,
        armor=50,
        mr=50,
        amaranth=True,
        tags=("resist",),
    ),
}


UPGRADE_COMPONENTS = {
    "Kindlegem": ("Ruby Crystal",),
    "Chain Vest": ("Cloth Armor",),
    "Warden's Mail": ("Cloth Armor",),
    "Plated Steelcaps": ("Boots of Speed", "Ruby Crystal"),
    "Mercury's Treads": ("Boots of Speed", "Ruby Crystal"),
    "Armored Advance": ("Plated Steelcaps",),
    "Yordle Trap": ("Kindlegem", "Cloth Armor", "Null-Magic Mantle"),
    "Zeke's Convergence": ("Kindlegem", "Cloth Armor", "Null-Magic Mantle"),
    "Locket of the Iron Solari": ("Kindlegem", "Cloth Armor", "Null-Magic Mantle"),
    "Knight's Vow": ("Chain Vest", "Kindlegem"),
    "Radiant Virtue": ("Cloth Armor", "Null-Magic Mantle", "Giant's Belt"),
    "Frozen Heart": ("Warden's Mail", "Glacial Shroud"),
    "Warmog's Armor": ("Kindlegem", "Giant's Belt"),
    "Thornmail": ("Chain Vest", "Bramble Vest"),
    "Force of Nature": ("Spectre's Cowl", "Negatron Cloak", "Winged Moonplate"),
    "Randuin's Omen": ("Giant's Belt", "Warden's Mail"),
    "Kaenic Rookern": ("Negatron Cloak", "Spectre's Cowl"),
    "Redemption": ("Fiendish Codex", "Forbidden Idol"),
    "Amaranth's Twinguard": ("Chain Vest", "Negatron Cloak", "Giant's Belt"),
}

NEXT_COMPONENTS = {
    "Kindlegem": ["Ruby Crystal"],
    "Plated Steelcaps": ["Boots of Speed", "Ruby Crystal"],
    "Mercury's Treads": ["Boots of Speed", "Ruby Crystal"],
    "Armored Advance": ["Plated Steelcaps"],
    "Yordle Trap": ["Kindlegem", "Cloth Armor", "Null-Magic Mantle"],
    "Zeke's Convergence": ["Kindlegem", "Cloth Armor", "Null-Magic Mantle"],
    "Locket of the Iron Solari": ["Kindlegem", "Cloth Armor", "Null-Magic Mantle"],
    "Knight's Vow": ["Kindlegem", "Chain Vest"],
    "Radiant Virtue": ["Giant's Belt", "Cloth Armor", "Null-Magic Mantle"],
    "Frozen Heart": ["Warden's Mail", "Glacial Shroud"],
    "Warmog's Armor": ["Giant's Belt", "Kindlegem"],
    "Thornmail": ["Bramble Vest", "Chain Vest"],
    "Force of Nature": ["Spectre's Cowl", "Negatron Cloak"],
    "Randuin's Omen": ["Giant's Belt", "Warden's Mail"],
    "Kaenic Rookern": ["Spectre's Cowl", "Negatron Cloak"],
    "Redemption": ["Forbidden Idol", "Fiendish Codex"],
    "Amaranth's Twinguard": ["Giant's Belt", "Chain Vest", "Negatron Cloak"],
}

BOOT_TIERS = (
    "Armored Advance",
    "Plated Steelcaps",
    "Mercury's Treads",
    "Boots of Speed",
)

# Kindlegem + Cloth + Null cart: Locket / Zeke / Yordle.
# Kindlegem + Chain Vest cart: Vow.
# Cloth + Null + Giant's Belt cart: Virtue (7.3 split from Vow).
BUILD_PATHS: Dict[str, List[str]] = {
    # Live Diamond+ (~20% pick): Vow into Warmog
    "Vow → Warmog → Virtue": [
        "Relic Shield",
        "Boots of Speed",
        "Kindlegem",
        "Chain Vest",
        "Knight's Vow",
        "Plated Steelcaps",
        "Warmog's Armor",
        "Radiant Virtue",
        "Frozen Heart",
    ],
    "Vow → Warmog → FH": [
        "Relic Shield",
        "Boots of Speed",
        "Kindlegem",
        "Chain Vest",
        "Knight's Vow",
        "Plated Steelcaps",
        "Warmog's Armor",
        "Frozen Heart",
        "Radiant Virtue",
    ],
    # WRF 7.3 guide (Yordle now Q-legal)
    "Vow → Virtue → Yordle": [
        "Relic Shield",
        "Boots of Speed",
        "Kindlegem",
        "Chain Vest",
        "Knight's Vow",
        "Plated Steelcaps",
        "Radiant Virtue",
        "Yordle Trap",
        "Thornmail",
    ],
    # CN 7.3 standard
    "Virtue → Vow → Zeke": [
        "Relic Shield",
        "Boots of Speed",
        "Giant's Belt",
        "Cloth Armor",
        "Null-Magic Mantle",
        "Radiant Virtue",
        "Plated Steelcaps",
        "Knight's Vow",
        "Zeke's Convergence",
    ],
    # CN carry-protection
    "Locket → Vow → Yordle": [
        "Relic Shield",
        "Boots of Speed",
        "Kindlegem",
        "Cloth Armor",
        "Null-Magic Mantle",
        "Locket of the Iron Solari",
        "Plated Steelcaps",
        "Knight's Vow",
        "Yordle Trap",
    ],
    # 7.2 bodyguard core, 7.3 numbers
    "Locket → Vow → FH": [
        "Relic Shield",
        "Boots of Speed",
        "Kindlegem",
        "Cloth Armor",
        "Null-Magic Mantle",
        "Locket of the Iron Solari",
        "Plated Steelcaps",
        "Knight's Vow",
        "Frozen Heart",
    ],
    "Vow → Locket → FH": [
        "Relic Shield",
        "Boots of Speed",
        "Kindlegem",
        "Chain Vest",
        "Knight's Vow",
        "Plated Steelcaps",
        "Locket of the Iron Solari",
        "Frozen Heart",
        "Thornmail",
    ],
    "Vow → FH → Locket": [
        "Relic Shield",
        "Boots of Speed",
        "Kindlegem",
        "Chain Vest",
        "Knight's Vow",
        "Plated Steelcaps",
        "Frozen Heart",
        "Locket of the Iron Solari",
        "Thornmail",
    ],
    "Locket → Virtue → Vow": [
        "Relic Shield",
        "Boots of Speed",
        "Kindlegem",
        "Locket of the Iron Solari",
        "Plated Steelcaps",
        "Radiant Virtue",
        "Knight's Vow",
        "Frozen Heart",
    ],
    "Virtue → Locket → Vow": [
        "Relic Shield",
        "Boots of Speed",
        "Giant's Belt",
        "Radiant Virtue",
        "Plated Steelcaps",
        "Locket of the Iron Solari",
        "Knight's Vow",
        "Frozen Heart",
    ],
    "Virtue → Vow → FH": [
        "Relic Shield",
        "Boots of Speed",
        "Giant's Belt",
        "Cloth Armor",
        "Null-Magic Mantle",
        "Radiant Virtue",
        "Plated Steelcaps",
        "Knight's Vow",
        "Frozen Heart",
    ],
    "Vow → Virtue → FH": [
        "Relic Shield",
        "Boots of Speed",
        "Kindlegem",
        "Chain Vest",
        "Knight's Vow",
        "Plated Steelcaps",
        "Radiant Virtue",
        "Frozen Heart",
        "Thornmail",
    ],
    "Vow → Zeke → Virtue": [
        "Relic Shield",
        "Boots of Speed",
        "Kindlegem",
        "Chain Vest",
        "Knight's Vow",
        "Plated Steelcaps",
        "Zeke's Convergence",
        "Radiant Virtue",
        "Frozen Heart",
    ],
    # 7.3 Catcher rush — Q slow is enough
    "Yordle → Vow → FH": [
        "Relic Shield",
        "Boots of Speed",
        "Kindlegem",
        "Cloth Armor",
        "Null-Magic Mantle",
        "Yordle Trap",
        "Plated Steelcaps",
        "Knight's Vow",
        "Frozen Heart",
    ],
    "Yordle → Locket → Vow": [
        "Relic Shield",
        "Boots of Speed",
        "Kindlegem",
        "Yordle Trap",
        "Plated Steelcaps",
        "Locket of the Iron Solari",
        "Knight's Vow",
        "Frozen Heart",
    ],
    "Locket → Yordle → Vow": [
        "Relic Shield",
        "Boots of Speed",
        "Kindlegem",
        "Locket of the Iron Solari",
        "Plated Steelcaps",
        "Yordle Trap",
        "Knight's Vow",
        "Frozen Heart",
    ],
    "Redemption → Vow → Virtue": [
        "Relic Shield",
        "Boots of Speed",
        "Forbidden Idol",
        "Fiendish Codex",
        "Redemption",
        "Plated Steelcaps",
        "Knight's Vow",
        "Radiant Virtue",
        "Frozen Heart",
    ],
    "FH → Vow → Locket": [
        "Relic Shield",
        "Boots of Speed",
        "Warden's Mail",
        "Glacial Shroud",
        "Frozen Heart",
        "Plated Steelcaps",
        "Knight's Vow",
        "Locket of the Iron Solari",
    ],
    "Vow → Locket → Virtue": [
        "Relic Shield",
        "Boots of Speed",
        "Kindlegem",
        "Chain Vest",
        "Knight's Vow",
        "Plated Steelcaps",
        "Locket of the Iron Solari",
        "Radiant Virtue",
        "Frozen Heart",
    ],
    "Locket → Vow → Thorn": [
        "Relic Shield",
        "Boots of Speed",
        "Kindlegem",
        "Locket of the Iron Solari",
        "Plated Steelcaps",
        "Knight's Vow",
        "Thornmail",
        "Frozen Heart",
    ],
    "Locket → Vow → Randuin": [
        "Relic Shield",
        "Boots of Speed",
        "Kindlegem",
        "Locket of the Iron Solari",
        "Plated Steelcaps",
        "Knight's Vow",
        "Randuin's Omen",
        "Frozen Heart",
    ],
    "Virtue → Warmog → Vow": [
        "Relic Shield",
        "Boots of Speed",
        "Giant's Belt",
        "Radiant Virtue",
        "Plated Steelcaps",
        "Warmog's Armor",
        "Knight's Vow",
        "Frozen Heart",
    ],
}

LEGENDARIES = {
    "Yordle Trap",
    "Zeke's Convergence",
    "Knight's Vow",
    "Redemption",
    "Frozen Heart",
    "Locket of the Iron Solari",
    "Radiant Virtue",
    "Thornmail",
    "Force of Nature",
    "Randuin's Omen",
    "Kaenic Rookern",
    "Warmog's Armor",
    "Amaranth's Twinguard",
}


# ---------------------------------------------------------------------------
# Inventory
# ---------------------------------------------------------------------------


def resolve_inventory(path: List[str], gold: int, minute: int) -> List[str]:
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
        if item_name == "Bulwark of the Mountain":
            return 0
        credit, _ = credit_for(item_name)
        return max(0, ITEMS[item_name].cost - credit)

    def buy(item_name: str) -> bool:
        nonlocal gold_pool
        if item_name == "Bulwark of the Mountain":
            if "Relic Shield" in owned:
                owned.remove("Relic Shield")
            if "Bulwark of the Mountain" not in owned:
                owned.append(item_name)
            return True
        if item_name in owned:
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
        if step == "Bulwark of the Mountain":
            continue
        if step == "Relic Shield":
            if "Relic Shield" not in owned and "Bulwark of the Mountain" not in owned:
                buy("Relic Shield")
            continue
        if step in owned:
            continue
        if step == "Armored Advance" and minute < 10:
            blocked_at = step
            break
        if gold_pool >= remaining_cost(step):
            buy(step)
        else:
            blocked_at = step
            break

    if minute >= 5 and "Relic Shield" in owned:
        owned.remove("Relic Shield")
        owned.insert(0, "Bulwark of the Mountain")

    if blocked_at and blocked_at in NEXT_COMPONENTS:
        for comp in NEXT_COMPONENTS[blocked_at]:
            if comp in owned:
                continue
            if gold_pool >= ITEMS[comp].cost:
                buy(comp)
        if blocked_at != "Armored Advance" or minute >= 10:
            if gold_pool >= remaining_cost(blocked_at):
                buy(blocked_at)
                seen = False
                for step in path:
                    if step == blocked_at:
                        seen = True
                        continue
                    if not seen or step in ("Relic Shield", "Bulwark of the Mountain"):
                        continue
                    if step in owned:
                        continue
                    if step == "Armored Advance" and minute < 10:
                        break
                    if gold_pool >= remaining_cost(step):
                        buy(step)
                    else:
                        for comp in NEXT_COMPONENTS.get(step, []):
                            if comp not in owned and gold_pool >= ITEMS[comp].cost:
                                buy(comp)
                        if gold_pool >= remaining_cost(step):
                            buy(step)
                        else:
                            break

    present = [b for b in BOOT_TIERS if b in owned]
    if len(present) > 1:
        keep = present[0]
        for b in present[1:]:
            owned.remove(b)
        if keep not in owned:
            owned.append(keep)

    return owned


# ---------------------------------------------------------------------------
# Runes (Resolve primary — tank support)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Page:
    name: str
    keystone: str
    primary: str
    runes: Tuple[str, ...]
    secondary: str


def has_rune(page: Page, name: str) -> bool:
    return name in page.runes or page.secondary == name or page.keystone == name


# Row 1: Font of Life / Unshakeable
# Row 2: Second Wind / Bone Plating
# Row 3: Overgrowth / Perseverance
# Secondary: Transcendence (Sorcery) or Legend: Tenacity / Legend: Haste (Precision)
ROW1 = ("Font of Life", "Unshakeable")
ROW2 = ("Second Wind", "Bone Plating")
ROW3 = ("Overgrowth", "Perseverance")

PAGES = [
    Page(
        "Guardian / Font·SW·Pers / Trans",
        "Guardian",
        "Resolve",
        ("Font of Life", "Second Wind", "Perseverance"),
        "Transcendence",
    ),
    Page(
        "Guardian / Font·SW·Over / Trans",
        "Guardian",
        "Resolve",
        ("Font of Life", "Second Wind", "Overgrowth"),
        "Transcendence",
    ),
    Page(
        "Guardian / Font·Bone·Pers / Trans",
        "Guardian",
        "Resolve",
        ("Font of Life", "Bone Plating", "Perseverance"),
        "Transcendence",
    ),
    Page(
        "Guardian / Font·Bone·Over / Trans",
        "Guardian",
        "Resolve",
        ("Font of Life", "Bone Plating", "Overgrowth"),
        "Transcendence",
    ),
    Page(
        "Guardian / Font·SW·Pers / Tenacity",
        "Guardian",
        "Resolve",
        ("Font of Life", "Second Wind", "Perseverance"),
        "Legend: Tenacity",
    ),
    Page(
        "Guardian / Font·SW·Pers / Haste",
        "Guardian",
        "Resolve",
        ("Font of Life", "Second Wind", "Perseverance"),
        "Legend: Haste",
    ),
    Page(
        "Guardian / Unsh·SW·Over / Trans",
        "Guardian",
        "Resolve",
        ("Unshakeable", "Second Wind", "Overgrowth"),
        "Transcendence",
    ),
    Page(
        "Guardian / Unsh·SW·Pers / Trans",
        "Guardian",
        "Resolve",
        ("Unshakeable", "Second Wind", "Perseverance"),
        "Transcendence",
    ),
    Page(
        "Ice Overlord / Font·SW·Pers / Trans",
        "Ice Overlord",
        "Resolve",
        ("Font of Life", "Second Wind", "Perseverance"),
        "Transcendence",
    ),
    Page(
        "Ice Overlord / Unsh·SW·Pers / Trans",
        "Ice Overlord",
        "Resolve",
        ("Unshakeable", "Second Wind", "Perseverance"),
        "Transcendence",
    ),
    Page(
        "Grasp / Font·SW·Over / Trans",
        "Grasp",
        "Resolve",
        ("Font of Life", "Second Wind", "Overgrowth"),
        "Transcendence",
    ),
]

DEFAULT_PAGE = PAGES[0]


def overgrowth_hp(minute: int) -> float:
    # Nearby dying minions while bodyguarding the wave. ~1.6 stacks/min.
    stacks = max(0.0, minute * 1.6)
    hp = 3.0 * stacks
    if stacks >= 30:
        return hp  # 3% max HP applied later from total
    return hp


def overgrowth_pct(minute: int) -> float:
    return 0.03 if minute * 1.6 >= 30 else 0.0


def legend_haste_ah(minute: int) -> float:
    stacks = min(6, max(0, (minute - 4) // 3))
    return 1.5 * stacks


def legend_tenacity(minute: int) -> float:
    stacks = min(5, max(0, (minute - 6) // 3))
    return 0.05 + 0.015 * stacks


def guardian_cd(level: int) -> float:
    return lerp(55.0, 25.0, level)


def guardian_shield(level: int, bonus_hp: float, ap: float) -> float:
    return lerp(40.0, 165.0, level) + 0.06 * bonus_hp + 0.15 * ap


def ice_overlord_dmg(level: int, bonus_hp: float) -> float:
    return lerp(15.0, 100.0, level) + 0.05 * bonus_hp


def ice_overlord_slow(bonus_hp: float) -> float:
    return 0.15 + 0.01 * (bonus_hp / 100.0)


def locket_shield(level: int) -> float:
    return lerp(250.0, 370.0, level)


def redemption_heal(ally_level: int) -> float:
    return lerp(150.0, 350.0, ally_level)


def q_base_cd(rank: int) -> float:
    return [0, 9, 8, 7, 6][rank] if rank else 9.0


def e_base_cd(rank: int) -> float:
    return [0, 16, 14, 12, 10][rank] if rank else 16.0


def w_base_cd(rank: int) -> float:
    return [0, 11, 10, 9, 8][rank] if rank else 11.0


def r_base_cd(rank: int) -> float:
    return [0, 75, 70, 65][rank] if rank else 999.0


def e_dr(rank: int) -> float:
    return [0, 0.35, 0.40, 0.45, 0.50][rank] if rank else 0.30


def w_flat(rank: int) -> float:
    return [0, 10, 15, 20, 25][rank] if rank else 10.0


def w_ratio(rank: int) -> float:
    return [0, 0.10, 0.12, 0.14, 0.16][rank] if rank else 0.10


def stun_duration(level: int) -> float:
    return lerp(1.25, 1.75, level)


def r_knockup(rank: int) -> float:
    return [0, 1.0, 1.25, 1.5][rank]


def braum_base_hp(level: int) -> float:
    return 690 + 120 * (level - 1)


def braum_base_armor(level: int) -> float:
    return 52 + 4.4 * (level - 1)


def braum_base_mr(level: int) -> float:
    return 38 + 2.0 * (level - 1)


def yordle_procs(has_yordle: bool, q_casts: int, r_in_fight: bool) -> bool:
    """7.3 Catcher: slow OR immobilize. Q 70% slow is enough; R not required."""
    return bool(has_yordle and (q_casts >= 1 or r_in_fight))


# ---------------------------------------------------------------------------
# Combat / peel model (8s bodyguard window)
# ---------------------------------------------------------------------------


@dataclass
class Snapshot:
    minute: int
    build_name: str
    page_name: str
    items: List[str]
    gold: int
    level: int
    hp: float
    armor: float
    mr: float
    ah: float
    legendary_count: int
    adc_taken: float
    adc_prevented: float
    braum_ehp: float
    cc_seconds: float
    peel_score: float
    q_casts: int
    r_in_fight: bool
    catcher_this_fight: bool
    notes: str
    has_vow: bool
    has_locket: bool
    has_fh: bool
    has_yordle: bool
    has_virtue: bool
    has_zeke: bool
    has_redemption: bool
    guardian_up: bool
    ice_up: bool


def sum_stats(names: List[str], minute: int) -> dict:
    hp = armor = mr = ah = ap = mana = hsp = aa_red = ult_haste = tenacity = 0.0
    flags = {
        "vow": False,
        "locket": False,
        "fh": False,
        "yordle": False,
        "virtue": False,
        "warmog": False,
        "thorn": False,
        "fon": False,
        "zeke": False,
        "redemption": False,
        "randuin": False,
        "kaenic": False,
        "amaranth": False,
        "armored": False,
        "bulwark": False,
    }
    for n in names:
        it = ITEMS[n]
        hp += it.hp
        armor += it.armor
        mr += it.mr
        ah += it.ah
        ap += it.ap
        mana += it.mana
        hsp += it.hsp
        aa_red += it.aa_red
        ult_haste += it.ult_haste
        tenacity += it.tenacity
        if it.vow:
            flags["vow"] = True
        if it.locket:
            flags["locket"] = True
        if it.frozen:
            flags["fh"] = True
        if it.yordle:
            flags["yordle"] = True
        if it.virtue:
            flags["virtue"] = True
        if it.warmog:
            flags["warmog"] = True
        if it.thorn:
            flags["thorn"] = True
        if it.fon:
            flags["fon"] = True
        if it.zeke:
            flags["zeke"] = True
        if it.redemption:
            flags["redemption"] = True
        if it.randuin:
            flags["randuin"] = True
        if it.kaenic:
            flags["kaenic"] = True
        if it.amaranth:
            flags["amaranth"] = True
        if it.armored:
            flags["armored"] = True
        if n == "Bulwark of the Mountain":
            flags["bulwark"] = True
            hp += 25.0 * soulcast_stacks(minute)
    return {
        "hp": hp,
        "armor": armor,
        "mr": mr,
        "ah": ah,
        "ap": ap,
        "mana": mana,
        "hsp": min(hsp, 0.40),
        "aa_red": min(aa_red, 0.12),
        "ult_haste": ult_haste,
        "tenacity": min(tenacity, 0.55),
        "names": names,
        **flags,
    }


def window_threat(minute: int) -> Tuple[float, float, float, float]:
    enemy_ad = 72.0 + 7.5 * minute
    enemy_as = 0.72 + 0.024 * minute
    autos = enemy_as * FIGHT_WINDOW
    aa_raw = autos * enemy_ad
    spell_phys = 90.0 + 11.0 * minute
    spell_magic = 140.0 + 15.0 * minute
    return aa_raw, spell_phys, spell_magic, enemy_as


def adc_defenses(minute: int) -> Tuple[float, float, float, int]:
    lv = min(15, 2 + minute)
    hp = 620.0 + 96.0 * lv + 18.0 * minute
    armor = 28.0 + 4.0 * lv + (18.0 if minute >= 12 else 0.0)
    mr = 30.0 + 1.3 * lv + (12.0 if minute >= 14 else 0.0)
    return hp, armor, mr, lv


def compute_snapshot(
    build_name: str, path: List[str], minute: int, page: Page
) -> Snapshot:
    gold = gold_at_minute(minute)
    level = level_at_minute(minute)
    names = resolve_inventory(path, gold, minute)
    st = sum_stats(names, minute)

    bonus_hp = st["hp"]
    if has_rune(page, "Overgrowth"):
        bonus_hp += overgrowth_hp(minute)

    ah = st["ah"]
    ap = st["ap"]
    if has_rune(page, "Transcendence"):
        ah += 5.0
        if level >= 5:
            ah += 5.0
        if level >= 9:
            ah += 8.0
    if has_rune(page, "Legend: Haste"):
        ah += legend_haste_ah(minute)

    b_hp = braum_base_hp(level) + bonus_hp
    if has_rune(page, "Overgrowth"):
        b_hp *= 1.0 + overgrowth_pct(minute)
    b_armor = braum_base_armor(level) + st["armor"]
    b_mr = braum_base_mr(level) + st["mr"]

    unsh = 0.0
    if has_rune(page, "Unshakeable"):
        nearby = 2.4 if minute >= 12 else 1.7
        unsh = 0.03 + 0.02 * min(3.0, nearby)
        b_armor *= 1.0 + unsh
        b_mr *= 1.0 + unsh

    if has_rune(page, "Perseverance"):
        # Immobilized ~1.5s of the window: extra resists, 10% tenacity.
        b_armor += lerp(10.0, 15.0, level) * (1.5 / FIGHT_WINDOW)
        b_mr += lerp(10.0, 15.0, level) * (1.5 / FIGHT_WINDOW)

    q_rank = max(1, skill_rank(level, "Q"))
    e_rank = max(1, skill_rank(level, "E")) if level >= 3 else 1
    w_rank = skill_rank(level, "W")
    r_rank = skill_rank(level, "R")

    q_cd = q_base_cd(q_rank) * haste_cdr(ah)
    r_cd = r_base_cd(r_rank) * haste_cdr(ah + st["ult_haste"]) if r_rank else 999.0

    q_casts = 1 + int(max(0.0, FIGHT_WINDOW - 0.4) / max(0.8, q_cd))
    e_up = min(1.0, 4.0 / FIGHT_WINDOW)
    if has_rune(page, "Perseverance") or has_rune(page, "Legend: Tenacity"):
        e_up = min(1.0, e_up + 0.03)
    w_up = min(1.0, 3.0 / FIGHT_WINDOW) if w_rank else 0.0

    r_in_fight = bool(r_rank) and r_cd <= 70.0

    aa_raw, spell_phys, spell_magic, enemy_as = window_threat(minute)
    adc_hp, adc_armor, adc_mr, adc_lv = adc_defenses(minute)

    w_arm = w_flat(w_rank) + w_ratio(w_rank) * st["armor"]
    w_mr_b = w_flat(w_rank) + w_ratio(w_rank) * st["mr"]
    adc_armor_eff = adc_armor + w_arm * w_up
    adc_mr_eff = adc_mr + w_mr_b * w_up
    b_armor_eff = b_armor + w_arm * w_up
    b_mr_eff = b_mr + w_mr_b * w_up

    # Ice Overlord resist steroid, 2.5s, on immobilize (stun or R). Q slow does not count.
    ice_up = False
    if page.keystone == "Ice Overlord" and (q_casts >= 1 and level >= 3 or r_in_fight):
        # Passive stun needs 4 stacks: Q + autos. Reliable once W is up and ADC hits.
        ice_up = True
        ice_arm = 35.0 + 0.75 * st["armor"]
        ice_mr = 35.0 + 0.75 * st["mr"]
        frac = 2.5 / FIGHT_WINDOW
        b_armor_eff += ice_arm * frac
        b_mr_eff += ice_mr * frac

    # Frozen Heart 7.3: 25% AS aura in 650 range (always on while glued).
    as_mult = 0.75 if st["fh"] else 1.0
    if st["randuin"]:
        # 30% crit reduction. Mixed ADC crit share ~0.45 after mid.
        crit_share = 0.25 if minute < 12 else 0.45
        as_mult *= 1.0 - 0.30 * crit_share
    aa_raw *= as_mult

    intercept = 0.38 * e_up
    spell_phys_adc = spell_phys * (1.0 - intercept)
    spell_magic_adc = spell_magic * (1.0 - intercept * 0.75)

    incoming_phys = aa_raw + spell_phys_adc
    incoming_magic = spell_magic_adc

    redirect = 0.12 if st["vow"] else 0.0
    adc_phys = incoming_phys * (1.0 - redirect)
    adc_magic = incoming_magic * (1.0 - redirect)
    to_braum_phys = incoming_phys * redirect
    to_braum_magic = incoming_magic * redirect

    adc_post = adc_phys * mit(adc_armor_eff) + adc_magic * mit(adc_mr_eff)

    hsp_all = st["hsp"]
    hsp_self = hsp_all + (0.30 if st["warmog"] else 0.0)

    shield = locket_shield(level) * (1.0 + hsp_all) if st["locket"] else 0.0
    adc_post = max(0.0, adc_post - shield)
    braum_shield = shield * (1.0 + hsp_self) / (1.0 + hsp_all) if shield else 0.0

    # Guardian: both get a shield. CD 55→25; fights every 42s.
    guardian_up = False
    g_shield = 0.0
    if page.keystone == "Guardian":
        gcd = guardian_cd(level)
        rate = min(1.0, FIGHT_EVERY / max(gcd, 1.0))
        guardian_up = rate >= 0.85
        g_shield = guardian_shield(level, b_hp - braum_base_hp(level), ap) * rate
        adc_post = max(0.0, adc_post - g_shield * (1.0 + hsp_all))
        braum_shield += g_shield * (1.0 + hsp_self)

    virtue_adc = 0.0
    virtue_self = 0.0
    if st["virtue"] and r_in_fight:
        virt_hp = b_hp * 1.10
        virtue_adc = virt_hp * 0.025 * 6.0 * 0.50 * (1.0 + hsp_all)
        virtue_self = virt_hp * 0.025 * 6.0 * (1.0 + hsp_self)
        adc_post = max(0.0, adc_post - virtue_adc)

    if st["redemption"]:
        # 2.5s delay — land ~70% of the time in a real dive.
        red = redemption_heal(adc_lv) * 0.70 * (1.0 + hsp_all)
        adc_post = max(0.0, adc_post - red)
        braum_shield += redemption_heal(level) * 0.70 * (1.0 + hsp_self)

    font_adc = 0.0
    font_self = 0.0
    if has_rune(page, "Font of Life") and q_casts >= 1:
        # Melee 130%. One proc / fight (20s CD).
        font_adc = (0.015 * b_hp + 0.05 * ap) * 1.30
        font_self = (0.010 * b_hp + 0.05 * ap) * 1.30
        adc_post = max(0.0, adc_post - font_adc)

    if has_rune(page, "Second Wind"):
        missing = 0.38 * b_hp
        sw = (6.0 + 0.03 * missing) * (5.0 / 5.0)
        font_self += sw

    catcher = yordle_procs(st["yordle"], q_casts, r_in_fight)
    # 30% ally AS shortens the dive a little (ADC kills faster).
    if catcher:
        adc_post *= 0.92

    stun = stun_duration(level) if q_casts >= 1 else 0.0
    knock = r_knockup(r_rank) if r_in_fight else 0.0
    q_slow_eq = min(2.0 * q_casts, 3.2) * 0.35
    ice_slow = 0.0
    if ice_up:
        ice_slow = min(3.0, 3.0) * ice_overlord_slow(b_hp - braum_base_hp(level)) * 0.45
    zeke_slow = 0.0
    if st["zeke"] and r_in_fight:
        zeke_slow = 5.0 * 0.30 * 0.45
    cc = stun + knock + q_slow_eq + ice_slow + zeke_slow

    aa_dps_post = (aa_raw * mit(adc_armor_eff)) / FIGHT_WINDOW
    cc_save = aa_dps_post * cc * 0.65
    adc_taken = max(0.0, adc_post - cc_save)

    base_aa, base_sp, base_sm, _ = window_threat(minute)
    _, base_ar, base_mr, _ = adc_defenses(minute)
    base_w = w_flat(w_rank) * w_up
    base_taken = (
        (base_aa + base_sp * (1.0 - 0.38 * e_up)) * mit(base_ar + base_w)
        + (base_sm * (1.0 - 0.38 * e_up * 0.75)) * mit(base_mr + base_w)
    )
    base_cc = stun + (r_knockup(r_rank) if r_rank else 0.0) + min(2.0, 2.0) * 0.35
    base_aa_dps = (base_aa * mit(base_ar + base_w)) / FIGHT_WINDOW
    base_taken = max(0.0, base_taken - base_aa_dps * base_cc * 0.65)
    adc_prevented = max(0.0, base_taken - adc_taken)

    first_hit = 180.0 + 18.0 * minute
    rest_phys = (aa_raw * 0.35 + to_braum_phys) * (1.0 - st["aa_red"])
    rest_magic = to_braum_magic + spell_magic * 0.25
    e_mult = 1.0 - e_dr(e_rank) * e_up
    braum_taken = (
        rest_phys * mit(b_armor_eff) * e_mult
        + rest_magic * mit(b_mr_eff) * e_mult
        - first_hit * 0.55
    )
    if st["armored"]:
        braum_taken -= (20.0 + 8.0 * level) + 0.05 * b_hp
    if st["kaenic"]:
        braum_taken -= lerp(50.0, 150.0, level) + 0.14 * b_hp * 0.55
    if st["amaranth"]:
        b_armor_eff *= 1.0 + 0.30 * 0.55
        b_mr_eff *= 1.0 + 0.30 * 0.55
    if has_rune(page, "Bone Plating"):
        plate = lerp(28.0, 55.0, level)
        braum_taken -= 3.0 * plate
    if page.keystone == "Grasp" and q_casts >= 1:
        # One empowered auto: 2% max HP heal. Damage is not peel.
        font_self += 0.02 * b_hp
    braum_taken = max(0.0, braum_taken - braum_shield - virtue_self - font_self)
    braum_ehp = b_hp / max(0.18, mit(b_armor_eff) * 0.6 + mit(b_mr_eff) * 0.4)

    stay = min(1.18, 0.80 + 0.20 * min(1.0, braum_ehp / (1800 + 90 * minute)))
    kit = 1.0
    if st["vow"] and st["locket"]:
        kit = 1.08
    elif st["vow"] and st["fh"]:
        kit = 1.06
    elif st["vow"] and st["virtue"]:
        kit = 1.04
    elif st["locket"]:
        kit = 1.03
    elif st["vow"]:
        kit = 1.04

    peel = (adc_prevented + 52.0 * cc + 0.035 * braum_ehp + font_adc) * stay * kit

    notes = []
    if st["vow"]:
        notes.append("Vow 12%")
    if st["locket"]:
        notes.append("Locket")
    if st["fh"]:
        notes.append("FH 25% AS")
    if st["virtue"] and r_in_fight:
        notes.append("RV on R")
    if catcher:
        notes.append("Catcher on Q")
    elif st["yordle"]:
        notes.append("Yordle (no Q yet)")
    if st["zeke"] and r_in_fight:
        notes.append("Zeke on R")
    if st["redemption"]:
        notes.append("Redemption")
    if st["warmog"]:
        notes.append("Warmog HP")
    if guardian_up:
        notes.append("Guardian")
    elif page.keystone == "Guardian":
        notes.append("Guardian partial")
    if ice_up:
        notes.append("Ice Overlord")
    if page.keystone == "Grasp":
        notes.append("Grasp")
    if not notes:
        notes.append("pre-legendary")

    n_leg = sum(1 for n in st["names"] if n in LEGENDARIES)

    return Snapshot(
        minute=minute,
        build_name=build_name,
        page_name=page.name,
        items=st["names"],
        gold=gold,
        level=level,
        hp=round(b_hp, 1),
        armor=round(b_armor, 1),
        mr=round(b_mr, 1),
        ah=ah,
        legendary_count=n_leg,
        adc_taken=round(adc_taken, 1),
        adc_prevented=round(adc_prevented, 1),
        braum_ehp=round(braum_ehp, 1),
        cc_seconds=round(cc, 2),
        peel_score=round(peel, 1),
        q_casts=q_casts,
        r_in_fight=r_in_fight,
        catcher_this_fight=catcher,
        notes=", ".join(notes),
        has_vow=st["vow"],
        has_locket=st["locket"],
        has_fh=st["fh"],
        has_yordle=st["yordle"],
        has_virtue=st["virtue"],
        has_zeke=st["zeke"],
        has_redemption=st["redemption"],
        guardian_up=guardian_up,
        ice_up=ice_up,
    )


def snapshot_weight(s: Snapshot) -> float:
    # Games are decided 8–16. Late is extra, not the whole metric.
    if s.minute <= 6:
        return 0.7
    if s.minute <= 12:
        return 1.15
    if s.minute <= 16:
        return 1.20
    return 1.0


def weighted_peel(snaps: List[Snapshot]) -> float:
    num = sum(s.peel_score * snapshot_weight(s) for s in snaps)
    den = sum(snapshot_weight(s) for s in snaps)
    return num / den


def run_builds(page: Page) -> Tuple[Dict[str, List[Snapshot]], List[dict]]:
    results: Dict[str, List[Snapshot]] = {}
    for name, path in BUILD_PATHS.items():
        results[name] = [
            compute_snapshot(name, path, m, page) for m in range(1, GAME_MINUTES + 1)
        ]

    timeline = []
    for m in range(1, GAME_MINUTES + 1):
        best_n, best_s = max(
            ((n, results[n][m - 1]) for n in results),
            key=lambda kv: kv[1].peel_score,
        )
        timeline.append(
            {
                "minute": m,
                "winner": best_n,
                "peel": best_s.peel_score,
                "adc_taken": best_s.adc_taken,
                "adc_prevented": best_s.adc_prevented,
                "cc": best_s.cc_seconds,
                "items": best_s.items,
                "notes": best_s.notes,
            }
        )
    return results, timeline


def run_runes(build_name: str, path: List[str]) -> List[Tuple[Page, float, float, float, Snapshot]]:
    ranked = []
    for page in PAGES:
        snaps = [
            compute_snapshot(build_name, path, m, page)
            for m in range(1, GAME_MINUTES + 1)
        ]
        ranked.append(
            (page, weighted_peel(snaps), snaps[11].peel_score, snaps[19].peel_score, snaps[19])
        )
    ranked.sort(key=lambda row: row[1], reverse=True)
    return ranked


def first_minute_with(snaps: List[Snapshot], pred) -> Optional[int]:
    for s in snaps:
        if pred(s):
            return s.minute
    return None


def rank_builds(results: Dict[str, List[Snapshot]]):
    rows = []
    for name, snaps in results.items():
        rows.append(
            (
                weighted_peel(snaps),
                snaps[15].peel_score,
                snaps[19].peel_score,
                name,
                snaps[7].peel_score,
                snaps[11].peel_score,
                snaps,
            )
        )
    rows.sort(key=lambda x: (x[0], x[1]), reverse=True)
    return rows


def snap_to_dict(s: Snapshot) -> dict:
    return {
        "minute": s.minute,
        "page": s.page_name,
        "items": s.items,
        "gold": s.gold,
        "level": s.level,
        "hp": s.hp,
        "armor": s.armor,
        "mr": s.mr,
        "ah": s.ah,
        "legendary_count": s.legendary_count,
        "adc_taken": s.adc_taken,
        "adc_prevented": s.adc_prevented,
        "braum_ehp": s.braum_ehp,
        "cc_seconds": s.cc_seconds,
        "peel_score": s.peel_score,
        "q_casts": s.q_casts,
        "r_in_fight": s.r_in_fight,
        "catcher_this_fight": s.catcher_this_fight,
        "notes": s.notes,
    }


def summarize(results, timeline, rune_rank) -> str:
    ranking = rank_builds(results)
    best = ranking[0]
    winner_name = best[3]
    snaps = best[6]
    rune_page, rune_avg, rune_12, rune_20, rune_last = rune_rank[0]

    vow_m = first_minute_with(snaps, lambda s: s.has_vow)
    locket_m = first_minute_with(snaps, lambda s: s.has_locket)
    fh_m = first_minute_with(snaps, lambda s: s.has_fh)
    virt_m = first_minute_with(snaps, lambda s: s.has_virtue)
    yordle_m = first_minute_with(snaps, lambda s: s.has_yordle)

    yordle_rush = results.get("Yordle → Vow → FH")
    warmog_live = results.get("Vow → Warmog → Virtue")

    lines = []
    a = lines.append
    a("=" * 80)
    a("BRAUM SUPPORT — FULL BUILD + RUNES  (Wild Rift Patch 7.3)")
    a("Playstyle: bodyguard ADC (W + E + Concussive Blows) | Game: 20:00")
    a("Metric: ADC damage prevented / 8s dive  + CC lock  + stay-in-front EHP")
    a("=" * 80)
    a("")
    a("7.3 CHANGES VS THE OLD 'NO YORDLE' READ")
    a("  • Yordle Trap Catcher now procs on slow OR immobilize.")
    a("    Winter's Bite (70% slow) lights it. R is no longer required.")
    a("  • Yordle / Locket / Zeke share Kindlegem + Cloth + Null.")
    a("  • Radiant Virtue is Cloth + Null + Giant's Belt (split from Vow).")
    a("  • Frozen Heart is a 25% AS aura, not Chill stacks.")
    a("  • Aftershock is gone. Ice Overlord is the immobilize keystone.")
    a("  • Guardian is the bodyguard keystone (shield you + the carry).")
    a("")
    a("GOLD / LEVEL")
    a(f"  {'Min':>3}  {'Gold':>6}  {'Lvl':>3}")
    for m in range(1, GAME_MINUTES + 1):
        if m in (1, 4, 5, 8, 10, 12, 14, 16, 18, 20):
            a(f"  {m:>3}  {gold_at_minute(m):>6}  {level_at_minute(m):>3}")

    a("")
    a("-" * 80)
    a("MINUTE-BY-MINUTE OPTIMAL  (default Guardian bodyguard page)")
    a("-" * 80)
    for row in timeline:
        if row["minute"] % 2 != 0 and row["minute"] not in (1, 5, 9, 11, 15):
            continue
        item_short = " › ".join(row["items"][:5])
        if len(row["items"]) > 5:
            item_short += " › …"
        a(
            f"  {row['minute']:>2}:00 | peel {row['peel']:>7.0f} | "
            f"ADC taken {row['adc_taken']:>6.0f} | saved {row['adc_prevented']:>5.0f} | "
            f"CC {row['cc']:>4.1f}s | {row['winner']}"
        )
        a(f"         items: {item_short}")
        a(f"         {row['notes']}")

    a("")
    a("-" * 80)
    a("BUILD COMPARISON — PEEL  (higher = carry lives)")
    a("-" * 80)
    a(
        f"  {'Build':<28} {'8:00':>7} {'12:00':>7} {'16:00':>7} {'20:00':>7} "
        f"{'Wtd':>7}"
    )
    for wtd, b16, b20, name, b8, b12, _snaps in ranking:
        a(f"  {name:<28} {b8:>7.0f} {b12:>7.0f} {b16:>7.0f} {b20:>7.0f} {wtd:>7.0f}")

    a("")
    a("-" * 80)
    a("ADC DAMAGE TAKEN / 8s DIVE  (lower = better)")
    a("-" * 80)
    for _wtd, _b16, _b20, name, _b8, _b12, sn in ranking:
        a(
            f"  {name:<28} {sn[7].adc_taken:>7.0f} {sn[11].adc_taken:>7.0f} "
            f"{sn[15].adc_taken:>7.0f} {sn[19].adc_taken:>7.0f}"
        )

    a("")
    a("-" * 80)
    a("RUNE PAGES ON THE WINNING CORE")
    a(f"  Core: {winner_name}")
    a("-" * 80)
    a(f"  {'Page':<42} {'Wtd':>7} {'12:00':>7} {'20:00':>7}")
    for page, avg, p12, p20, _last in rune_rank:
        a(f"  {page.name:<42} {avg:>7.0f} {p12:>7.0f} {p20:>7.0f}")

    a("")
    a("-" * 80)
    a("VERDICT")
    a("-" * 80)
    a(f"  Best item path: {winner_name}")
    a(f"  Peel-weighted avg: {best[0]:.0f} | 16:00: {best[1]:.0f} | 20:00: {best[2]:.0f}")
    if vow_m:
        a(f"  Knight's Vow:     ~{vow_m}:00  (12% redirect while you W-glue)")
    else:
        a("  Knight's Vow:     not finished by 20:00")
    if locket_m:
        a(f"  Locket:           ~{locket_m}:00  (team shield, no R required)")
    else:
        a("  Locket:           not finished by 20:00")
    if virt_m:
        a(f"  Radiant Virtue:   ~{virt_m}:00  (R heal — Transcend + 2.5% max HP/s)")
    if fh_m:
        a(f"  Frozen Heart:     ~{fh_m}:00  (25% AS aura, bodyguard range)")
    else:
        a("  Frozen Heart:     not finished by 20:00 on this path")
    if yordle_m:
        a(f"  Yordle Trap:      ~{yordle_m}:00  (Catcher on Q slow)")

    if yordle_rush is not None:
        y12, w12 = yordle_rush[11].peel_score, snaps[11].peel_score
        y16, w16 = yordle_rush[15].peel_score, snaps[15].peel_score
        pct12 = 100.0 * (w12 / y12 - 1.0) if y12 else 0.0
        pct16 = 100.0 * (w16 / y16 - 1.0) if y16 else 0.0
        a("")
        a("  YORDLE TRAP (7.3, Q-legal):")
        a("  • Catcher now lights on Winter's Bite. The old 'R-only' ban is dead.")
        a("  • It still shares the Locket/Zeke cart (Kindlegem + Cloth + Null).")
        a("  • 30% ally AS is enable, not a shield. Peel still prefers Locket/Vow.")
        a(
            f"  • Phút 12: Yordle rush {y12:.0f} vs {winner_name} {w12:.0f} "
            f"({pct12:+.0f}%). Phút 16: {y16:.0f} vs {w16:.0f} ({pct16:+.0f}%)."
        )

    if warmog_live is not None:
        a("")
        a("  LIVE VOW → WARMOG:")
        a(
            f"  • Diamond+ popular core. Sim peel @16 {warmog_live[15].peel_score:.0f} "
            f"vs winner {snaps[15].peel_score:.0f}."
        )
        a("  • Warmog 700 HP + Blessed keeps YOU up. It does not shield the ADC.")
        a("  • Buy it 3rd if you are the soak and the carry already has Vow.")

    a("")
    a(f"  Best runes: {rune_page.keystone} · {' · '.join(rune_page.runes)} · {rune_page.secondary}")
    a(f"  Rune-weighted peel: {rune_avg:.0f} | 12:00 {rune_12:.0f} | 20:00 {rune_20:.0f}")
    second = rune_rank[1]
    a(f"  Runner-up page: {second[0].name} ({second[1]:.0f})")

    a("")
    a("  FULL BUILD (Braum support, 7.3)")
    a("  Spells: Flash + Heal")
    a("  Skill: max Q, 1 early W (dash), then E. R at 5 / 9 / 13.")
    a("  Start: Relic Shield → Bulwark of the Mountain (~5:00)")
    a("  Boots: Plated Steelcaps (Mercs vs AP/CC)")
    a(f"  Core:  {winner_name}")
    a("  Full 6 if the game lasts:")
    a("    Relic → Bulwark · Steelcaps · Locket · Radiant Virtue · Knight's Vow")
    a("    then Frozen Heart vs AS / Thornmail vs healing / FoN vs AP /")
    a("    Randuin vs crit / Kaenic vs mages.")
    a("  Do not rush Armored Advance — 2200g on support gold delays item 2.")
    a("")
    a("  RUNES")
    a(f"    Keystone:  {rune_page.keystone}")
    a(f"    Primary:   {' · '.join(rune_page.runes)}")
    a(f"    Secondary: {rune_page.secondary}")
    a("    Row 1 Font of Life (heal on Q). Swap Unshakeable in 5-man clumps.")
    a("    Row 2 Second Wind vs poke. Swap Bone Plating vs melee burst.")
    a("    Row 3 Overgrowth for HP; Perseverance vs heavy CC.")
    a("    Ice Overlord if you engage (stun/R) more than you bodyguard.")
    a("    Grasp is a top-lane trade keystone — it does not save the ADC.")
    a("")
    a("  TẠI SAO BUILD NÀY:")
    a("  • Guardian shield cả bạn và ADC mỗi khi đứng sát — đúng kit W+E.")
    a("  • Font of Life proc bằng Q. Second Wind hàn poke; Overgrowth cộng HP.")
    a("  • Transcendence = thêm Q/E, thêm stun Concussive Blows.")
    a("  • Knight's Vow là món bodyguard (12% redirect). Locket là shield team,")
    a("    không cần R. Virtue heal R, Warmog tank bản thân.")
    a("  • Yordle 7.3 proc được bằng Q, nhưng cùng nấc với Locket — đừng")
    a("    đổi shield ADC lấy 30% AS nếu nhiệm vụ là giữ mạng carry.")
    a("")
    a("  Trap: Aftershock — deleted in 7.1. Use Ice Overlord or Guardian.")
    a("  Trap: Protector's Vow — deleted in 7.1 (Guardian ate the niche).")
    a("  Trap: Yordle first 'because Catcher is for tanks'. Catcher is legal")
    a("  on Q now, but Locket still peels the same cart better.")
    a("  Trap: Gathering Storm / damage pages. Braum is not the damage.")
    a("=" * 80)
    return "\n".join(lines)


def export_json(results, timeline, rune_rank, path: str) -> None:
    payload = {
        "meta": {
            "champion": "Braum",
            "role": "Support",
            "patch": "7.3",
            "game_minutes": GAME_MINUTES,
            "playstyle": "bodyguard peel",
            "yordle_note": (
                "7.3 Catcher procs on slow or immobilize. "
                "Braum Q Winter's Bite is enough; R is not required."
            ),
            "rune_note": (
                "Aftershock removed in 7.1 (Ice Overlord). "
                "Guardian is the bodyguard keystone."
            ),
        },
        "winner_build": rank_builds(results)[0][3],
        "winner_runes": {
            "name": rune_rank[0][0].name,
            "keystone": rune_rank[0][0].keystone,
            "primary": rune_rank[0][0].runes,
            "secondary": rune_rank[0][0].secondary,
        },
        "timeline": timeline,
        "rune_ranking": [
            {
                "name": p.name,
                "keystone": p.keystone,
                "runes": list(p.runes),
                "secondary": p.secondary,
                "weighted": round(avg, 1),
                "peel_12": round(p12, 1),
                "peel_20": round(p20, 1),
            }
            for p, avg, p12, p20, _ in rune_rank
        ],
        "builds": {
            name: [snap_to_dict(s) for s in snaps]
            for name, snaps in results.items()
        },
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def self_check(results: Dict[str, List[Snapshot]], rune_rank) -> None:
    # Ult at WR level 5 (minute 4).
    assert level_at_minute(4) == 5
    assert skill_rank(5, "R") == 1
    assert skill_rank(4, "R") == 0

    # 7.3 Catcher: Q slow is enough. R is not required.
    assert yordle_procs(True, 1, False)
    assert yordle_procs(True, 0, True)
    assert not yordle_procs(True, 0, False)
    assert not yordle_procs(False, 2, True)

    yordle = results["Yordle → Vow → FH"]
    online = first_minute_with(yordle, lambda s: s.has_yordle)
    assert online is not None and online <= 12, online
    for s in yordle:
        if s.has_yordle and s.q_casts >= 1:
            assert s.catcher_this_fight, (s.minute, s.notes)

    # Aftershock is not a legal page.
    for page, *_ in rune_rank:
        assert page.keystone in ("Guardian", "Ice Overlord", "Grasp")
        assert page.keystone != "Aftershock"
        assert "Ingenious Hunter" not in page.runes
        assert page.secondary != "Ingenious Hunter"
        assert len(page.runes) == 3
        assert page.runes[0] in ROW1
        assert page.runes[1] in ROW2
        assert page.runes[2] in ROW3

    # 7.3 costs
    assert ITEMS["Knight's Vow"].cost == 2450
    assert ITEMS["Yordle Trap"].cost == 2400
    assert ITEMS["Frozen Heart"].cost == 2550
    assert ITEMS["Radiant Virtue"].cost == 2650
    assert ITEMS["Redemption"].cost == 2450
    assert ITEMS["Plated Steelcaps"].aa_red == 0.10
    assert ITEMS["Plated Steelcaps"].hp == 150

    # Virtue no longer shares Vow's Kindlegem + Vest cart.
    assert "Kindlegem" not in UPGRADE_COMPONENTS["Radiant Virtue"]
    assert "Kindlegem" in UPGRADE_COMPONENTS["Knight's Vow"]
    assert "Kindlegem" in UPGRADE_COMPONENTS["Yordle Trap"]
    assert "Kindlegem" in UPGRADE_COMPONENTS["Locket of the Iron Solari"]

    g20 = gold_at_minute(20)
    assert 8500 < g20 < 11500, g20

    # Frozen Heart aura is on without R.
    fh = results["FH → Vow → Locket"]
    fh_on = first_minute_with(fh, lambda s: s.has_fh)
    assert fh_on is not None
    assert fh[fh_on - 1].has_fh
    assert "FH 25% AS" in fh[fh_on - 1].notes

    # Steelcaps unique
    lock = results["Locket → Vow → FH"]
    for s in lock:
        boots = [n for n in s.items if n in BOOT_TIERS]
        assert len(boots) <= 1, boots

    # Winner is a real path
    ranking = rank_builds(results)
    assert ranking[0][0] > 0
    assert rune_rank[0][1] > 0


def main() -> None:
    results, timeline = run_builds(DEFAULT_PAGE)
    winner_name = rank_builds(results)[0][3]
    rune_rank = run_runes(winner_name, BUILD_PATHS[winner_name])
    self_check(results, rune_rank)
    report = summarize(results, timeline, rune_rank)
    print(report)
    with open(os.path.join(OUT_DIR, "report.txt"), "w", encoding="utf-8") as f:
        f.write(report + "\n")
    export_json(
        results, timeline, rune_rank, os.path.join(OUT_DIR, "results.json")
    )
    print(f"\nWrote {OUT_DIR}/report.txt and {OUT_DIR}/results.json")


if __name__ == "__main__":
    main()
