#!/usr/bin/env python3
"""
PC League of Legends — Smolder bot
Patch snapshot 26.19 (Data Dragon 16.19.1, wiki ratios Sep 2026).

Question:
  Crit scale (Infinity Edge, crit chance, Rapid Firecannon) versus
  ability scale (ability haste, Spear of Shojin, Black Cleaver).
  Every fight aspect, and when to pick which.

Crit scale
  Q physical damage is multiplied by crit chance, not rolled.
  At 100% crit the hit is +75%. Infinity Edge's 30% crit-damage stat
  multiplies that bonus, so 100% crit + IE is +97.5% (1.975x).
  Autos use the 2026 base of 200% crits; IE raises that to 230%.
  Dragon Practice magic on Q also grows with crit (25% of stacks at
  0 crit, 55% at 100% crit, 64% with IE).

Ability scale
  Haste shortens Q, which is both the damage spell and the stack engine.
  Shojin adds 25 basic-ability haste and up to +12% ability damage.
  Cleaver shreds armor for Smolder and for the rest of an AD team.
  Health and a shorter E are the reason the build exists.

Shared
  Essence Reaver first on the five comparison paths. Deathfire Touch on
  every path. No runes besides that keystone, so the item delta stays visible.

Trinity path
  Tear on the first back, then Trinity Force, Ionian, Manamune, Serylda,
  Shojin. No crit, so Q never gets the 1.75x multiplier. Trinity spellblade
  is 200% base AD. Muramana Shock is 3% max mana on abilities.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import json
import math

GAME_MINUTES = 28
WINDOW = 8.0


# ---------------------------------------------------------------------------
# Economy / levels — even bot lane, not fed
# ---------------------------------------------------------------------------


def gold_at_minute(m: int) -> int:
    if m <= 0:
        return 500
    total = 500
    for t in range(1, m + 1):
        if t <= 6:
            total += 380
        elif t <= 12:
            total += 470
        elif t <= 18:
            total += 560
        else:
            total += 620
    return total


def level_at_minute(m: int) -> int:
    table = {
        1: 1, 2: 2, 3: 3, 4: 3, 5: 4, 6: 5, 7: 5, 8: 6, 9: 6, 10: 7,
        11: 7, 12: 8, 13: 9, 14: 9, 15: 10, 16: 11, 17: 11, 18: 12,
        19: 12, 20: 13, 21: 13, 22: 14, 23: 14, 24: 15, 25: 16, 26: 16,
        27: 17, 28: 18,
    }
    return table.get(m, 18)


def skill_rank(level: int, skill: str) -> int:
    """Q max, W second, E last. R at 6 / 11 / 16."""
    if skill == "R":
        if level < 6:
            return 0
        if level < 11:
            return 1
        if level < 16:
            return 2
        return 3
    q_levels = [1, 4, 5, 7, 8]
    w_levels = [2, 9, 10, 12, 13]
    e_levels = [3, 14, 15, 17, 18]
    return sum(1 for lv in {"Q": q_levels, "W": w_levels, "E": e_levels}[skill] if level >= lv)


def haste_factor(ah: float) -> float:
    return 100.0 / (100.0 + ah)


# ---------------------------------------------------------------------------
# Champion formulas
# ---------------------------------------------------------------------------

Q_BASE = [60, 70, 80, 90, 100]
Q_CD = [5.5, 5.0, 4.5, 4.0, 3.5]
W_GLOB = [60, 70, 80, 90, 100]
W_EXPL = [10, 35, 60, 85, 110]
W_CD = [14, 13, 12, 11, 10]
E_BASE = [10, 15, 20, 25, 30]
E_CD = [24, 22, 20, 18, 16]
R_BASE = [150, 250, 350]
R_HEAL = [100, 135, 170]


def q_crit_bonus(crit: float, ie: float) -> float:
    """Fraction added to Q physical damage. 0.75 at 100% crit, 0.975 with IE."""
    return crit * 0.75 * (1.0 + ie)


def auto_crit_bonus(crit: float, ie: float) -> float:
    """Fraction added to an auto's expected damage. Base crits are 200%."""
    return crit * 1.00 * (1.0 + ie)


def q_stack_ratio(crit: float, ie: float) -> float:
    """Magic damage as a fraction of Dragon Practice stacks."""
    return 0.25 * (1.0 + crit * 1.2 * (1.0 + ie))


def e_stack_ratio(crit: float, ie: float) -> float:
    return 0.08 * (1.0 + crit * 0.6 * (1.0 + ie))


def burn_max_hp_fraction(bonus_ad: float, stacks: float) -> float:
    """Tier 3 true damage over 3 seconds. 0 before 225 stacks."""
    if stacks < 225:
        return 0.0
    return 0.025 * (bonus_ad / 100.0) + 0.005 * (stacks / 100.0)


def dft_per_second(level: int, bonus_ad: float) -> float:
    """Deathfire Touch magic damage per second before the 3s empowerment."""
    base = 3.0 + 9.0 * (level - 1) / 17.0
    return base + 0.07 * bonus_ad


def shieldbow_shield(level: int) -> float:
    """Ranged Lifeline shield, level 1 → 18."""
    return 320.0 + (560.0 - 320.0) * (level - 1) / 17.0


def mitigate(amount: float, resist: float) -> float:
    if resist >= 0:
        return amount * 100.0 / (100.0 + resist)
    return amount * (2.0 - 100.0 / (100.0 - resist))


def effective_armor(armor: float, shred: float, pct_pen: float, lethality: float) -> float:
    return armor * (1.0 - shred) * (1.0 - pct_pen) - lethality


# ---------------------------------------------------------------------------
# Items
# ---------------------------------------------------------------------------


@dataclass
class Item:
    name: str
    cost: int
    ad: float = 0
    ah: float = 0
    basic_ah: float = 0
    hp: float = 0
    crit: float = 0
    as_pct: float = 0
    pct_pen: float = 0
    lethality: float = 0
    lifesteal: float = 0
    omnivamp: float = 0
    tenacity: float = 0
    ie: float = 0
    er: bool = False
    sheen: bool = False
    shojin: bool = False
    cleaver: bool = False
    rfc: bool = False
    ldr: bool = False
    navori: bool = False
    hunger: bool = False
    shieldbow: bool = False
    boots: bool = False
    trinity: bool = False
    tear: bool = False
    manamune: bool = False


ITEMS: Dict[str, Item] = {
    "Doran's Blade": Item("Doran's Blade", 450, ad=10, hp=80, omnivamp=0.025),
    "Long Sword": Item("Long Sword", 350, ad=10),
    "Ruby Crystal": Item("Ruby Crystal", 400, hp=150),
    "Dagger": Item("Dagger", 250, as_pct=0.10),
    "Cloak of Agility": Item("Cloak of Agility", 600, crit=0.15),
    "B. F. Sword": Item("B. F. Sword", 1300, ad=40),
    "Pickaxe": Item("Pickaxe", 875, ad=25),
    "Glowing Mote": Item("Glowing Mote", 250, ah=5),
    "Boots": Item("Boots", 300, boots=True),
    "Sheen": Item("Sheen", 900, ah=10, sheen=True),
    "Caulfield's Warhammer": Item("Caulfield's Warhammer", 1050, ad=20, ah=10),
    "Kindlegem": Item("Kindlegem", 800, hp=200, ah=10),
    "Phage": Item("Phage", 1100, ad=15, hp=200),
    "Tunneler": Item("Tunneler", 1150, ad=15, hp=250),
    "Zeal": Item("Zeal", 1200, crit=0.15, as_pct=0.15),
    "Scout's Slingshot": Item("Scout's Slingshot", 600, as_pct=0.20),
    "Noonquiver": Item("Noonquiver", 1300, ad=15, crit=0.20),
    "Last Whisper": Item("Last Whisper", 1450, ad=20, pct_pen=0.18),
    "Vampiric Scepter": Item("Vampiric Scepter", 900, ad=15, lifesteal=0.07),
    "Essence Reaver": Item("Essence Reaver", 3050, ad=50, ah=20, crit=0.25, er=True),
    "Infinity Edge": Item("Infinity Edge", 3500, ad=75, crit=0.25, ie=0.30),
    "Rapid Firecannon": Item("Rapid Firecannon", 2650, crit=0.25, as_pct=0.35, rfc=True),
    "Lord Dominik's Regards": Item(
        "Lord Dominik's Regards", 3300, ad=35, crit=0.25, pct_pen=0.35, ldr=True
    ),
    "Bloodthirster": Item("Bloodthirster", 3400, ad=80, lifesteal=0.15),
    "Navori Flickerblade": Item(
        "Navori Flickerblade", 2650, crit=0.25, as_pct=0.40, navori=True
    ),
    "Black Cleaver": Item("Black Cleaver", 3000, ad=45, ah=20, hp=400, cleaver=True),
    "Spear of Shojin": Item(
        "Spear of Shojin", 3100, ad=45, hp=450, basic_ah=25, shojin=True
    ),
    "Endless Hunger": Item("Endless Hunger", 3100, ad=65, omnivamp=0.05, tenacity=0.20, hunger=True),
    "Serylda's Grudge": Item("Serylda's Grudge", 3000, ad=45, ah=15, pct_pen=0.35),
    "Berserker's Greaves": Item("Berserker's Greaves", 1100, as_pct=0.30, boots=True),
    "Ionian Boots of Lucidity": Item("Ionian Boots of Lucidity", 900, ah=10, boots=True),
    "Gluttonous Greaves": Item("Gluttonous Greaves", 1000, omnivamp=0.04, boots=True),
    "Immortal Shieldbow": Item("Immortal Shieldbow", 3000, ad=55, crit=0.25, shieldbow=True),
    "Tear of the Goddess": Item("Tear of the Goddess", 400, tear=True),
    "Hearthbound Axe": Item("Hearthbound Axe", 1200, ad=20, as_pct=0.20),
    "Trinity Force": Item(
        "Trinity Force", 3333, ad=36, ah=15, hp=333, as_pct=0.30, trinity=True
    ),
    "Manamune": Item("Manamune", 2900, ad=35, ah=15, manamune=True),
}


RECIPES: Dict[str, Tuple[str, ...]] = {
    "Sheen": ("Glowing Mote",),
    "Caulfield's Warhammer": ("Long Sword", "Long Sword", "Glowing Mote"),
    "Kindlegem": ("Ruby Crystal", "Glowing Mote"),
    "Phage": ("Ruby Crystal", "Long Sword"),
    "Tunneler": ("Long Sword", "Ruby Crystal"),
    "Zeal": ("Cloak of Agility", "Dagger"),
    "Scout's Slingshot": ("Dagger", "Dagger"),
    "Noonquiver": ("Long Sword", "Cloak of Agility"),
    "Last Whisper": ("Long Sword", "Long Sword"),
    "Vampiric Scepter": ("Long Sword",),
    "Essence Reaver": ("Sheen", "Caulfield's Warhammer", "Cloak of Agility"),
    "Infinity Edge": ("B. F. Sword", "Pickaxe", "Cloak of Agility"),
    "Rapid Firecannon": ("Zeal", "Scout's Slingshot"),
    "Lord Dominik's Regards": ("Last Whisper", "Noonquiver"),
    "Bloodthirster": ("B. F. Sword", "Pickaxe", "Vampiric Scepter"),
    "Navori Flickerblade": ("Dagger", "Zeal", "Dagger"),
    "Black Cleaver": ("Phage", "Kindlegem", "Pickaxe"),
    "Spear of Shojin": ("Pickaxe", "Tunneler", "Ruby Crystal"),
    "Endless Hunger": ("Caulfield's Warhammer", "Pickaxe", "Long Sword"),
    "Serylda's Grudge": ("Caulfield's Warhammer", "Last Whisper"),
    "Berserker's Greaves": ("Boots", "Dagger", "Dagger"),
    "Ionian Boots of Lucidity": ("Boots", "Glowing Mote"),
    "Gluttonous Greaves": ("Boots",),
    "Immortal Shieldbow": ("Pickaxe", "Noonquiver"),
    "Hearthbound Axe": ("Long Sword", "Dagger", "Long Sword"),
    "Trinity Force": ("Sheen", "Phage", "Hearthbound Axe"),
    "Manamune": ("Tear of the Goddess", "Caulfield's Warhammer", "Long Sword"),
}

LEGENDARIES = {
    "Essence Reaver",
    "Infinity Edge",
    "Rapid Firecannon",
    "Lord Dominik's Regards",
    "Bloodthirster",
    "Navori Flickerblade",
    "Black Cleaver",
    "Spear of Shojin",
    "Endless Hunger",
    "Serylda's Grudge",
    "Immortal Shieldbow",
    "Trinity Force",
    "Manamune",
}

FINISHED_BOOTS = {
    "Berserker's Greaves",
    "Ionian Boots of Lucidity",
    "Gluttonous Greaves",
}


def _er_path() -> List[str]:
    # Sheen is a Glowing Mote. Caulfield is two Long Swords and a Mote.
    return [
        "Doran's Blade",
        "Glowing Mote",
        "Sheen",
        "Long Sword",
        "Long Sword",
        "Glowing Mote",
        "Caulfield's Warhammer",
        "Cloak of Agility",
        "Essence Reaver",
    ]


BUILD_PATHS: Dict[str, List[str]] = {
    "Crit: ER → IE → RFC → LDR": _er_path()
    + [
        "Boots",
        "Dagger",
        "Dagger",
        "Berserker's Greaves",
        "B. F. Sword",
        "Cloak of Agility",
        "Pickaxe",
        "Infinity Edge",
        "Cloak of Agility",
        "Dagger",
        "Zeal",
        "Dagger",
        "Dagger",
        "Scout's Slingshot",
        "Rapid Firecannon",
        "Long Sword",
        "Long Sword",
        "Last Whisper",
        "Long Sword",
        "Cloak of Agility",
        "Noonquiver",
        "Lord Dominik's Regards",
        "B. F. Sword",
        "Long Sword",
        "Vampiric Scepter",
        "Pickaxe",
        "Bloodthirster",
    ],
    "Crit: ER → IE → Navori → LDR": _er_path()
    + [
        "Boots",
        "Dagger",
        "Dagger",
        "Berserker's Greaves",
        "B. F. Sword",
        "Cloak of Agility",
        "Pickaxe",
        "Infinity Edge",
        "Dagger",
        "Cloak of Agility",
        "Dagger",
        "Zeal",
        "Dagger",
        "Navori Flickerblade",
        "Long Sword",
        "Long Sword",
        "Last Whisper",
        "Long Sword",
        "Cloak of Agility",
        "Noonquiver",
        "Lord Dominik's Regards",
        "Cloak of Agility",
        "Dagger",
        "Zeal",
        "Scout's Slingshot",
        "Rapid Firecannon",
    ],
    "Ability: ER → Cleaver → Shojin": _er_path()
    + [
        "Boots",
        "Glowing Mote",
        "Ionian Boots of Lucidity",
        "Ruby Crystal",
        "Long Sword",
        "Phage",
        "Ruby Crystal",
        "Glowing Mote",
        "Kindlegem",
        "Pickaxe",
        "Black Cleaver",
        "Long Sword",
        "Ruby Crystal",
        "Tunneler",
        "Pickaxe",
        "Ruby Crystal",
        "Spear of Shojin",
        "Long Sword",
        "Long Sword",
        "Glowing Mote",
        "Caulfield's Warhammer",
        "Pickaxe",
        "Long Sword",
        "Endless Hunger",
        "Long Sword",
        "Long Sword",
        "Last Whisper",
        "Caulfield's Warhammer",
        "Serylda's Grudge",
    ],
    "Hybrid: ER → Shojin → IE": _er_path()
    + [
        "Boots",
        "Gluttonous Greaves",
        "Long Sword",
        "Ruby Crystal",
        "Tunneler",
        "Pickaxe",
        "Ruby Crystal",
        "Spear of Shojin",
        "B. F. Sword",
        "Cloak of Agility",
        "Pickaxe",
        "Infinity Edge",
        "Long Sword",
        "Long Sword",
        "Last Whisper",
        "Long Sword",
        "Cloak of Agility",
        "Noonquiver",
        "Lord Dominik's Regards",
        "Cloak of Agility",
        "Dagger",
        "Zeal",
        "Scout's Slingshot",
        "Rapid Firecannon",
    ],
    "Hybrid: ER → Cleaver → IE": _er_path()
    + [
        "Boots",
        "Gluttonous Greaves",
        "Ruby Crystal",
        "Long Sword",
        "Phage",
        "Ruby Crystal",
        "Glowing Mote",
        "Kindlegem",
        "Pickaxe",
        "Black Cleaver",
        "B. F. Sword",
        "Cloak of Agility",
        "Pickaxe",
        "Infinity Edge",
        "Long Sword",
        "Long Sword",
        "Last Whisper",
        "Long Sword",
        "Cloak of Agility",
        "Noonquiver",
        "Lord Dominik's Regards",
        "Cloak of Agility",
        "Dagger",
        "Zeal",
        "Scout's Slingshot",
        "Rapid Firecannon",
    ],
    # Tear on the first back so Muramana can finish. Trinity is still the first legendary.
    "Trinity → Manamune → Serylda → Shojin": [
        "Doran's Blade",
        "Tear of the Goddess",
        "Glowing Mote",
        "Sheen",
        "Ruby Crystal",
        "Long Sword",
        "Phage",
        "Long Sword",
        "Dagger",
        "Long Sword",
        "Hearthbound Axe",
        "Trinity Force",
        "Boots",
        "Glowing Mote",
        "Ionian Boots of Lucidity",
        "Long Sword",
        "Long Sword",
        "Glowing Mote",
        "Caulfield's Warhammer",
        "Long Sword",
        "Manamune",
        "Long Sword",
        "Long Sword",
        "Last Whisper",
        "Long Sword",
        "Long Sword",
        "Glowing Mote",
        "Caulfield's Warhammer",
        "Serylda's Grudge",
        "Long Sword",
        "Ruby Crystal",
        "Tunneler",
        "Pickaxe",
        "Ruby Crystal",
        "Spear of Shojin",
    ],
}


def resolve_inventory(path: List[str], gold: int) -> List[str]:
    owned: List[str] = []
    pool = gold
    sold_doran = False

    def credit_for(name: str) -> Tuple[int, List[str]]:
        needed = list(RECIPES.get(name, ()))
        available = list(owned)
        remove: List[str] = []
        credit = 0
        for comp in needed:
            if comp in available:
                credit += ITEMS[comp].cost
                available.remove(comp)
                remove.append(comp)
        return credit, remove

    def buy(name: str) -> bool:
        nonlocal pool, sold_doran
        if name in FINISHED_BOOTS and any(b in owned for b in FINISHED_BOOTS):
            return False
        if name in LEGENDARIES and name in owned:
            return False
        if name == "Doran's Blade" and name in owned:
            return False
        credit, remove = credit_for(name)
        cost = max(0, ITEMS[name].cost - credit)
        slots_after = len(owned) - len(remove) + 1
        if (
            name in LEGENDARIES
            and "Doran's Blade" in owned
            and "Doran's Blade" not in remove
            and slots_after > 6
            and not sold_doran
        ):
            owned.remove("Doran's Blade")
            pool += 180
            sold_doran = True
            slots_after -= 1
        if cost > pool:
            return False
        pool -= cost
        for comp in remove:
            owned.remove(comp)
        owned.append(name)
        return True

    for step in path:
        if step in owned and step not in (
            "Long Sword",
            "Dagger",
            "Cloak of Agility",
            "Ruby Crystal",
            "Glowing Mote",
            "Pickaxe",
        ):
            continue
        if not buy(step):
            break
    return owned


# ---------------------------------------------------------------------------
# Targets
# ---------------------------------------------------------------------------


@dataclass
class Target:
    name: str
    hp: float
    bonus_hp: float
    armor: float
    mr: float


def target_at(kind: str, minute: int) -> Target:
    lv = level_at_minute(minute)
    if kind == "squish":
        base = 630 + 105 * (lv - 1)
        bonus = 0 if minute < 12 else (250 if minute < 20 else 450)
        armor = 26 + 4.2 * (lv - 1)
        if minute >= 14:
            armor += 25  # Plated Steelcaps
        mr = 33 + 1.1 * (lv - 1) + (0 if minute < 18 else 25)
    elif kind == "bruiser":
        base = 640 + 110 * (lv - 1)
        bonus = 0 if minute < 8 else min(140 * (minute - 7), 1800)
        armor = 36 + 4.7 * (lv - 1) + (0 if minute < 8 else min(7 * (minute - 7), 80))
        mr = 32 + 2.05 * (lv - 1) + (0 if minute < 12 else min(5 * (minute - 11), 60))
    else:
        base = 650 + 120 * (lv - 1)
        bonus = 0 if minute < 6 else min(150 * (minute - 5), 2400)
        armor = 40 + 5.0 * (lv - 1) + (0 if minute < 7 else min(9 * (minute - 6), 130))
        mr = 32 + 2.05 * (lv - 1) + (0 if minute < 10 else min(7 * (minute - 9), 110))
    return Target(kind, base + bonus, bonus, armor, mr)


def dive_burst(minute: int) -> Tuple[float, float]:
    """Yardstick assassin/engage burst. Not a specific champion.

    Tuned so a crit build with no health item is threatened from the
    mid game, while Cleaver or Shojin health can still eat one rotation.
    """
    return 500 + 95 * minute, 280 + 75 * minute


# ---------------------------------------------------------------------------
# Loadout
# ---------------------------------------------------------------------------


@dataclass
class Loadout:
    level: int
    base_ad: float
    bonus_ad: float
    ad: float
    crit: float
    ie: float
    ah: float
    basic_ah: float
    as_bonus: float
    attack_speed: float
    hp: float
    armor: float
    mr: float
    pct_pen: float
    lethality: float
    lifesteal: float
    omnivamp: float
    tenacity: float
    er: bool
    sheen: bool
    shojin: bool
    cleaver: bool
    rfc: bool
    ldr: bool
    navori: bool
    shieldbow: bool
    stacks: float
    trinity: bool = False
    max_mana: float = 0
    muramana: bool = False
    tear_bonus: float = 0
    names: List[str] = field(default_factory=list)

    @property
    def q_cd(self) -> float:
        rank = skill_rank(self.level, "Q")
        base = Q_CD[max(0, rank - 1)]
        return base * haste_factor(self.ah) * haste_factor(self.basic_ah)

    @property
    def w_cd(self) -> float:
        rank = skill_rank(self.level, "W")
        if rank <= 0:
            return 999
        return W_CD[rank - 1] * haste_factor(self.ah) * haste_factor(self.basic_ah)

    @property
    def e_cd(self) -> float:
        rank = skill_rank(self.level, "E")
        if rank <= 0:
            return 999
        return E_CD[rank - 1] * haste_factor(self.ah) * haste_factor(self.basic_ah)


def loadout_from(names: List[str], level: int, stacks: float, tear_bonus: float = 0.0) -> Loadout:
    base_ad = 58.0 + 2.3 * (level - 1)
    bonus_ad = 0.0
    crit = 0.0
    ie = 0.0
    ah = 0.0
    basic_ah = 0.0
    as_bonus = 0.04 * (level - 1)
    hp = 575.0 + 100.0 * (level - 1)
    pct_pen = 0.0
    lethality = 0.0
    lifesteal = 0.0
    omnivamp = 0.0
    tenacity = 0.0
    flags = dict(
        er=False, sheen=False, shojin=False, cleaver=False, rfc=False,
        ldr=False, navori=False, shieldbow=False, trinity=False,
    )
    # Sheen is consumed by ER; don't keep both procs.
    for name in names:
        it = ITEMS[name]
        bonus_ad += it.ad
        crit += it.crit
        ie = max(ie, it.ie)
        ah += it.ah
        basic_ah += it.basic_ah
        as_bonus += it.as_pct
        hp += it.hp
        pct_pen = max(pct_pen, it.pct_pen)
        lethality += it.lethality
        lifesteal += it.lifesteal
        omnivamp += it.omnivamp
        tenacity += it.tenacity
        for key in flags:
            if getattr(it, key):
                flags[key] = True
    if flags["er"] or flags["trinity"]:
        flags["sheen"] = False
    item_mana = 0.0
    muramana = False
    if "Manamune" in names and tear_bonus >= 360:
        item_mana = 1000.0
        muramana = True
    elif "Manamune" in names:
        item_mana = 500.0
    elif "Tear of the Goddess" in names:
        item_mana = 240.0
    base_mana = 300.0 + 40.0 * (level - 1)
    stacked = tear_bonus if item_mana else 0.0
    max_mana = base_mana + item_mana + stacked
    if item_mana:
        # Awe: 2% max mana as bonus AD. Muramana's own 1000 mana is 20 AD.
        bonus_ad += 0.02 * max_mana
    if any(ITEMS[n].hunger for n in names):
        # Ranged Famine: 5 + 10% bonus AD ability haste. Includes this item's AD.
        ah += 5.0 + 0.10 * bonus_ad
    crit_cap = min(1.0, crit)
    return Loadout(
        level=level,
        base_ad=base_ad,
        bonus_ad=bonus_ad,
        ad=base_ad + bonus_ad,
        crit=crit_cap,
        ie=ie,
        ah=ah,
        basic_ah=basic_ah,
        as_bonus=as_bonus,
        attack_speed=0.638 * (1.0 + as_bonus),
        hp=hp,
        armor=24.0 + 4.0 * (level - 1),
        mr=33.0 + 1.1 * (level - 1),
        pct_pen=pct_pen,
        lethality=lethality,
        lifesteal=lifesteal,
        omnivamp=omnivamp,
        tenacity=tenacity,
        stacks=stacks,
        names=list(names),
        max_mana=max_mana,
        muramana=muramana,
        tear_bonus=stacked,
        **flags,
    )


# ---------------------------------------------------------------------------
# Stack engine — Q uptime. Haste builds pull ahead after their haste items.
# ---------------------------------------------------------------------------


def stacks_gained_during(minute: int, q_cd: float, has_er: bool, has_tear: bool = False) -> float:
    """
    Q casts that produce a Dragon Practice stack this minute.
    Lane (through 14:00) is mostly last-hits. After that, fights replace farm.
    Essence Reaver refunds mana. Tear only enlarges the pool, so the cast
    rate is a bit lower. With neither, mana cuts uptime harder.
    """
    uptime = 0.82 if minute <= 14 else 0.60
    if not has_er:
        uptime *= 0.90 if has_tear else 0.72
    chance = 0.78 if minute <= 14 else 0.62
    return (60.0 / q_cd) * uptime * chance


def stack_timeline(path: List[str]) -> List[float]:
    """stacks[m] = stacks owned at minute m, after that minute's farming."""
    stacks = [0.0]
    total = 0.0
    for m in range(1, GAME_MINUTES + 1):
        names = resolve_inventory(path, gold_at_minute(m))
        kit = loadout_from(names, level_at_minute(m), 0)
        has_tear = any(n in names for n in ("Tear of the Goddess", "Manamune"))
        total += stacks_gained_during(m, kit.q_cd, kit.er, has_tear)
        stacks.append(total)
    return stacks


def tear_bonus_timeline(path: List[str]) -> List[float]:
    """Bonus mana from Tear at minute m. +27 per minute while Tear or Manamune is owned, cap 360."""
    out = [0.0]
    mana = 0.0
    for m in range(1, GAME_MINUTES + 1):
        names = resolve_inventory(path, gold_at_minute(m))
        if any(n in names for n in ("Tear of the Goddess", "Manamune")):
            mana = min(360.0, mana + 27.0)
        out.append(mana)
    return out


# ---------------------------------------------------------------------------
# Fight
# ---------------------------------------------------------------------------


@dataclass
class Fight:
    phys: float = 0
    magic: float = 0
    true_dmg: float = 0
    heal: float = 0
    qs: int = 0
    autos: int = 0

    @property
    def total(self) -> float:
        return self.phys + self.magic + self.true_dmg


def simulate_fight(kit: Loadout, target: Target, mode: str) -> Fight:
    """
    mode:
      poke  — Q only, max range, no autos
      kite  — Q and autos, one W, E and R held
      allin — R sweetspot, then E, then Q / W / autos
    """
    out = Fight()
    t = 0.0
    q_at = 0.0
    w_at = 0.0
    e_at = 0.0
    r_at = 0.0
    blade_at = 0.0
    shojin_stacks = 0
    carve = 0
    dft_from: Optional[float] = None
    dft_until = -1.0
    used_w = False
    used_e = False
    used_r = False
    energy = 0.0
    windup = 0.16622 / kit.attack_speed
    aa_time = 1.0 / kit.attack_speed

    def shojin_mult() -> float:
        if not kit.shojin:
            return 1.0
        return 1.0 + 0.03 * shojin_stacks

    def bump_shojin() -> None:
        nonlocal shojin_stacks
        if kit.shojin:
            shojin_stacks = min(4, shojin_stacks + 1)

    def armor_now() -> float:
        shred = 0.06 * carve if kit.cleaver else 0.0
        return effective_armor(target.armor, shred, kit.pct_pen, kit.lethality)

    def giant(kind: str) -> float:
        if kind == "true" or not kit.ldr:
            return 1.0
        return 1.0 + 0.15 * min(1.0, target.bonus_hp / 1500.0)

    def deal(raw: float, kind: str, ability: bool, ls_ratio: float, do_carve: bool) -> float:
        nonlocal carve
        amount = raw * (shojin_mult() if ability else 1.0) * giant(kind)
        if kind == "phys":
            dealt = mitigate(amount, armor_now())
            out.phys += dealt
            out.heal += dealt * kit.lifesteal * ls_ratio
        elif kind == "magic":
            dealt = mitigate(amount, target.mr)
            out.magic += dealt
        else:
            dealt = amount
            out.true_dmg += dealt
        out.heal += dealt * kit.omnivamp
        if do_carve and kit.cleaver and kind == "phys":
            carve = min(5, carve + 1)
        return dealt

    def refresh_dft(duration: float) -> None:
        nonlocal dft_from, dft_until
        if dft_until < t:
            dft_from = t
        elif dft_from is None:
            dft_from = t
        dft_until = t + duration

    def dft_tick(tick_at: float) -> None:
        if dft_from is None or dft_until + 1e-9 < tick_at:
            return
        empowered = (tick_at - dft_from) >= 3.0
        per = dft_per_second(kit.level, kit.bonus_ad) * (1.75 if empowered else 1.0)
        deal(per, "magic", ability=False, ls_ratio=0.0, do_carve=False)

    def advance(dt: float) -> None:
        nonlocal t
        if dt <= 0:
            return
        end = t + dt
        n = 1
        while True:
            tick_at = math.floor(t) + n
            if tick_at > end + 1e-9:
                break
            if tick_at <= WINDOW + 1e-9:
                dft_tick(float(tick_at))
            n += 1
        t = end

    def navori_on_auto() -> None:
        nonlocal q_at, w_at, e_at
        if not kit.navori:
            return
        if q_at > t:
            q_at = t + (q_at - t) * 0.85
        if w_at > t:
            w_at = t + (w_at - t) * 0.85
        if e_at > t:
            e_at = t + (e_at - t) * 0.85

    def cast_q() -> None:
        nonlocal q_at, blade_at, energy
        advance(windup)
        rank = skill_rank(kit.level, "Q") - 1
        raw_phys = (Q_BASE[rank] + 1.30 * kit.bonus_ad) * (1.0 + q_crit_bonus(kit.crit, kit.ie))
        raw_magic = kit.stacks * q_stack_ratio(kit.crit, kit.ie)
        deal(raw_phys, "phys", True, 0.5, True)
        deal(raw_magic, "magic", True, 0.0, False)
        blade = spellblade_damage(kit)
        if t >= blade_at and blade > 0:
            # Same frame as Q: one Carve stack, already applied by the fireball.
            deal(blade, "phys", False, 0.5, False)
            blade_at = t + 1.5
        if kit.muramana:
            # Q is a spell and an on-hit in one instance, so Shock uses the
            # ranged ability ratio only: 3% max mana.
            deal(0.03 * kit.max_mana, "phys", False, 0.5, False)
        frac = burn_max_hp_fraction(kit.bonus_ad, kit.stacks)
        if frac > 0:
            overlap = min(3.0, max(0.0, WINDOW - t))
            deal(target.hp * frac * (overlap / 3.0), "true", True, 0.0, False)
        refresh_dft(2.0 if kit.stacks >= 25 else 4.0)
        bump_shojin()
        q_at = t + kit.q_cd
        out.qs += 1

    def cast_w() -> None:
        nonlocal used_w, w_at
        advance(0.35)
        rank = skill_rank(kit.level, "W") - 1
        raw_phys = (W_GLOB[rank] + W_EXPL[rank]) + 1.10 * kit.bonus_ad
        raw_magic = 0.55 * kit.stacks
        deal(raw_phys, "phys", True, 0.0, True)
        deal(raw_magic, "magic", True, 0.0, False)
        if kit.muramana:
            deal(0.03 * kit.max_mana, "phys", False, 0.0, False)
        refresh_dft(2.0)
        bump_shojin()
        used_w = True
        w_at = t + kit.w_cd

    def cast_e() -> None:
        nonlocal used_e, e_at
        bolts = 5 + int(math.floor(kit.stacks / 100.0))
        rank = skill_rank(kit.level, "E") - 1
        per_phys = E_BASE[rank] + 0.30 * kit.ad
        per_magic = kit.stacks * e_stack_ratio(kit.crit, kit.ie)
        # Bolts land across the flight. Step time so Carve ramps inside E.
        step = 1.25 / bolts
        for _ in range(bolts):
            advance(step)
            deal(per_phys, "phys", True, 0.0, True)
            deal(per_magic, "magic", True, 0.0, False)
        if kit.muramana:
            deal(0.03 * kit.max_mana, "phys", False, 0.0, False)
        refresh_dft(4.0)
        bump_shojin()
        used_e = True
        e_at = t + kit.e_cd

    def cast_r() -> None:
        nonlocal used_r, r_at
        advance(0.75)
        rank = skill_rank(kit.level, "R") - 1
        if rank >= 0:
            raw = (R_BASE[rank] + 1.00 * kit.bonus_ad) * 1.50
            deal(raw, "phys", True, 0.0, True)
            if kit.muramana:
                deal(0.03 * kit.max_mana, "phys", False, 0.0, False)
            refresh_dft(2.0)
            bump_shojin()
        used_r = True
        r_at = t + 999

    def cast_auto() -> None:
        nonlocal energy
        advance(aa_time)
        deal(kit.ad * (1.0 + auto_crit_bonus(kit.crit, kit.ie)), "phys", False, 1.0, True)
        if kit.muramana:
            deal(0.012 * kit.max_mana, "phys", False, 1.0, False)
        energy += 20.0
        if kit.rfc and energy >= 100.0:
            energy -= 100.0
            deal(40.0, "magic", False, 0.0, False)
        navori_on_auto()
        out.autos += 1

    while t < WINDOW - 1e-6:
        if mode == "poke":
            if t + 1e-9 >= q_at:
                cast_q()
            else:
                advance(min(q_at, WINDOW) - t)
                if t >= WINDOW - 1e-9:
                    break
        elif mode == "kite":
            if t + 1e-9 >= q_at:
                cast_q()
            elif not used_w and skill_rank(kit.level, "W") > 0 and t + 1e-9 >= w_at:
                cast_w()
            else:
                cast_auto()
        else:
            if (
                not used_r
                and skill_rank(kit.level, "R") > 0
                and t + 1e-9 >= r_at
            ):
                cast_r()
            elif not used_e and skill_rank(kit.level, "E") > 0 and used_r:
                cast_e()
            elif t + 1e-9 >= q_at:
                cast_q()
            elif not used_w and skill_rank(kit.level, "W") > 0 and t + 1e-9 >= w_at:
                cast_w()
            else:
                cast_auto()
        if t > WINDOW + 5:
            break
    return out


def survival(kit: Loadout, minute: int) -> Tuple[float, float, float]:
    """Return (incoming post-mitigation, uptime 0-1, effective HP vs the burst)."""
    phys, magic = dive_burst(minute)
    incoming = mitigate(phys, kit.armor) + mitigate(magic, kit.mr)
    shield = shieldbow_shield(kit.level) if kit.shieldbow and incoming >= kit.hp * 0.70 else 0.0
    pool = kit.hp + shield
    uptime = min(1.0, pool / incoming) if incoming > 0 else 1.0
    ehp = kit.hp * (1.0 + kit.armor / 100.0)
    return incoming, uptime, ehp


def ally_phys_amp(armor: float) -> float:
    """Extra physical damage an ally deals to a fully carved target."""
    before = 100.0 / (100.0 + armor)
    after = 100.0 / (100.0 + armor * 0.70)
    return after / before - 1.0


# ---------------------------------------------------------------------------
# Snapshots
# ---------------------------------------------------------------------------


@dataclass
class MinuteRow:
    minute: int
    build: str
    items: List[str]
    level: int
    stacks: float
    crit: float
    ah: float
    basic_ah: float
    bonus_ad: float
    hp: float
    q_cd: float
    e_cd: float
    q_squish: float
    poke_squish: float
    kite_squish: float
    kite_tank: float
    kite_bruiser: float
    allin_tank: float
    allin_squish: float
    heal_kite: float
    uptime: float
    ehp: float
    qs_poke: int
    qs_kite: int
    team_amp: float
    equal_kite_tank: float
    legendaries: int
    tear_bonus: float
    muramana: bool


def spellblade_damage(kit: Loadout) -> float:
    """Trinity is 200% base AD. Essence Reaver is 125% base AD plus up to 50 from crit."""
    if kit.trinity:
        return 2.0 * kit.base_ad
    if kit.er:
        return 1.25 * kit.base_ad + 50.0 * kit.crit
    if kit.sheen:
        return kit.base_ad
    return 0.0


def q_hit_on(kit: Loadout, target: Target) -> float:
    """One isolated Q with no Carve yet and no Shojin stacks. Includes spellblade and full burn."""
    rank = skill_rank(kit.level, "Q") - 1
    raw_phys = (Q_BASE[rank] + 1.30 * kit.bonus_ad) * (1.0 + q_crit_bonus(kit.crit, kit.ie))
    raw_magic = kit.stacks * q_stack_ratio(kit.crit, kit.ie)
    armor = effective_armor(target.armor, 0.0, kit.pct_pen, kit.lethality)
    giant = 1.0 + (0.15 * min(1.0, target.bonus_hp / 1500.0) if kit.ldr else 0.0)
    dealt = mitigate(raw_phys * giant, armor) + mitigate(raw_magic * giant, target.mr)
    blade = spellblade_damage(kit)
    if blade:
        dealt += mitigate(blade, armor)
    if kit.muramana:
        dealt += mitigate(0.03 * kit.max_mana, armor)
    dealt += target.hp * burn_max_hp_fraction(kit.bonus_ad, kit.stacks)
    return dealt


def row_for(
    build: str, minute: int, stacks: float, equal_stacks: float, tear_bonus: float = 0.0
) -> MinuteRow:
    names = resolve_inventory(BUILD_PATHS[build], gold_at_minute(minute))
    level = level_at_minute(minute)
    kit = loadout_from(names, level, stacks, tear_bonus)
    squish = target_at("squish", minute)
    bruiser = target_at("bruiser", minute)
    tank = target_at("tank", minute)
    kite_s = simulate_fight(kit, squish, "kite")
    kite_t = simulate_fight(kit, tank, "kite")
    kite_b = simulate_fight(kit, bruiser, "kite")
    poke = simulate_fight(kit, squish, "poke")
    all_t = simulate_fight(kit, tank, "allin")
    all_s = simulate_fight(kit, squish, "allin")
    equal_kit = loadout_from(names, level, equal_stacks, tear_bonus)
    equal_tank = simulate_fight(equal_kit, tank, "kite")
    _incoming, uptime, ehp = survival(kit, minute)
    return MinuteRow(
        minute=minute,
        build=build,
        items=names,
        level=level,
        stacks=stacks,
        crit=kit.crit,
        ah=kit.ah,
        basic_ah=kit.basic_ah,
        bonus_ad=kit.bonus_ad,
        hp=kit.hp,
        q_cd=kit.q_cd,
        e_cd=kit.e_cd,
        q_squish=q_hit_on(kit, squish),
        poke_squish=poke.total,
        kite_squish=kite_s.total,
        kite_tank=kite_t.total,
        kite_bruiser=kite_b.total,
        allin_tank=all_t.total,
        allin_squish=all_s.total,
        heal_kite=kite_s.heal,
        uptime=uptime,
        ehp=ehp,
        qs_poke=poke.qs,
        qs_kite=kite_s.qs,
        team_amp=ally_phys_amp(tank.armor) if kit.cleaver else 0.0,
        equal_kite_tank=equal_tank.total,
        legendaries=sum(1 for n in names if n in LEGENDARIES),
        tear_bonus=kit.tear_bonus,
        muramana=kit.muramana,
    )


def milestone(stacks: List[float], goal: float) -> Optional[int]:
    for m, value in enumerate(stacks):
        if value >= goal:
            return m
    return None


def item_names(names: List[str]) -> str:
    legs = [n for n in names if n in LEGENDARIES or n in FINISHED_BOOTS]
    comps = [n for n in names if n not in legs and n != "Doran's Blade"]
    text = " › ".join(legs) if legs else "(components)"
    if comps:
        text += " + " + ", ".join(comps)
    return text


def completed_names(path: List[str]) -> List[str]:
    """Finished boots and legendaries on the path, Doran's sold."""
    out: List[str] = []
    for name in path:
        if name in LEGENDARIES or name in FINISHED_BOOTS:
            if name not in out:
                out.append(name)
    return out


def winner(rows: List[MinuteRow], key) -> str:
    best = max(rows, key=key)
    top = key(best)
    tied = [r for r in rows if abs(key(r) - top) <= 0.002 * max(1.0, top)]
    if len(tied) == len(rows):
        return "tie"
    names = {r.build for r in tied}
    crits = {"Crit: ER → IE → RFC → LDR", "Crit: ER → IE → Navori → LDR"}
    if names == crits:
        return "Both crit"
    if len(tied) == 1:
        return best.build
    abbrev = {
        "Crit: ER → IE → RFC → LDR": "Crit",
        "Crit: ER → IE → Navori → LDR": "Navori",
        "Ability: ER → Cleaver → Shojin": "Ability",
        "Hybrid: ER → Shojin → IE": "Shojin",
        "Hybrid: ER → Cleaver → IE": "Cleaver",
    }
    return "+".join(abbrev[r.build] for r in tied)


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

BUILD_ORDER = [
    "Crit: ER → IE → RFC → LDR",
    "Crit: ER → IE → Navori → LDR",
    "Ability: ER → Cleaver → Shojin",
    "Hybrid: ER → Shojin → IE",
    "Hybrid: ER → Cleaver → IE",
]
TRI_NAME = "Trinity → Manamune → Serylda → Shojin"


def short(name: str) -> str:
    return {
        "Crit: ER → IE → RFC → LDR": "Crit IE/RFC",
        "Crit: ER → IE → Navori → LDR": "Crit Navori",
        "Ability: ER → Cleaver → Shojin": "Ability",
        "Hybrid: ER → Shojin → IE": "Hybrid Shojin",
        "Hybrid: ER → Cleaver → IE": "Hybrid Cleaver",
        "Trinity → Manamune → Serylda → Shojin": "Trinity",
        "tie": "tie",
        "Both crit": "Both crit",
    }.get(name, name)


def fmt_min(m: Optional[int]) -> str:
    if m is None:
        return "  — "
    return f"{m:02d}:00"


def build_report(timelines: Dict[str, List[MinuteRow]], stacks: Dict[str, List[float]]) -> str:
    lines: List[str] = []
    a = lines.append
    a("=" * 88)
    a("SMOLDER — CRIT SCALE vs ABILITY SCALE   (PC LoL patch 26.19)")
    a("Bot lane, even gold, Deathfire Touch. Essence Reaver first on the five paths below.")
    a("Window: 8 seconds.  Kite = Q + autos + one W.  Poke = Q only.  All-in = R + E + Q.")
    a("=" * 88)
    a("")
    a("GOLD / LEVEL / TARGETS")
    a(f"  {'Min':>4} {'Gold':>7} {'Lvl':>4} {'Sq HP':>7} {'Sq AR':>6} {'Tank HP':>8} {'Tank AR':>8} {'Tank MR':>8}")
    for m in (1, 8, 11, 14, 16, 18, 22, 25, 28):
        sq = target_at("squish", m)
        tk = target_at("tank", m)
        a(
            f"  {m:4d} {gold_at_minute(m):7d} {level_at_minute(m):4d}"
            f" {sq.hp:7.0f} {sq.armor:6.0f} {tk.hp:8.0f} {tk.armor:8.0f} {tk.mr:8.0f}"
        )
    a("")
    a("-" * 88)
    a("DRAGON PRACTICE — minute you cross 25 / 125 / 225")
    a("Stacks come from Q casts. Haste does nothing until the haste items exist.")
    a("-" * 88)
    a(f"  {'Build':<28} {'25':>7} {'125':>7} {'225':>7} {'stacks@22':>10} {'stacks@28':>10}")
    for name in list(BUILD_ORDER) + [TRI_NAME]:
        st = stacks[name]
        a(
            f"  {short(name):<28} {fmt_min(milestone(st, 25)):>7}"
            f" {fmt_min(milestone(st, 125)):>7} {fmt_min(milestone(st, 225)):>7}"
            f" {st[22]:10.0f} {st[28]:10.0f}"
        )
    a("")
    a("-" * 88)
    a("MINUTE-BY-MINUTE — who leads each job")
    a("messy = kite damage on a squishy, multiplied by whether the dive burst kills you")
    a("-" * 88)
    a(f"  {'Min':>4}  {'Squishy kite':<16} {'Tank kite':<16} {'Poke':<16} {'Messy fight':<16}")
    for m in range(1, GAME_MINUTES + 1):
        rows = [timelines[n][m] for n in BUILD_ORDER]
        messy = winner(rows, lambda r: r.kite_squish * r.uptime)
        a(
            f"  {m:02d}:00  {short(winner(rows, lambda r: r.kite_squish)):<16}"
            f" {short(winner(rows, lambda r: r.kite_tank)):<16}"
            f" {short(winner(rows, lambda r: r.poke_squish)):<16}"
            f" {short(messy):<16}"
        )
    a("")
    spikes = (11, 16, 18, 22, 28)
    a("-" * 88)
    a("ASPECTS — same minute, every build")
    a("Q hit is one Q on a squishy before Carve ramps, including spellblade and the 225 burn.")
    a("Equal-stack tank kite gives every build the crit build's stack count, so the")
    a("remaining gap is items rather than who farmed Q faster.")
    a("-" * 88)
    for m in spikes:
        sq = target_at("squish", m)
        tk = target_at("tank", m)
        a("")
        a(f"  {m:02d}:00   level {level_at_minute(m)}   gold {gold_at_minute(m)}")
        a(f"           squishy {sq.hp:.0f} HP / {sq.armor:.0f} AR     tank {tk.hp:.0f} HP / {tk.armor:.0f} AR / {tk.mr:.0f} MR")
        a(
            f"  {'Build':<16} {'Items':>5} {'Crit':>5} {'Q cd':>5} {'Stk':>5}"
            f" {'Q hit':>7} {'Poke':>7} {'KiteSq':>7} {'KiteTk':>7} {'AllTk':>7}"
            f" {'HP':>6} {'Live':>5} {'E cd':>5} {'Team':>5}"
        )
        for name in BUILD_ORDER:
            r = timelines[name][m]
            a(
                f"  {short(name):<16} {r.legendaries:5d} {r.crit*100:4.0f}%"
                f" {r.q_cd:5.2f} {r.stacks:5.0f} {r.q_squish:7.0f} {r.poke_squish:7.0f}"
                f" {r.kite_squish:7.0f} {r.kite_tank:7.0f} {r.allin_tank:7.0f}"
                f" {r.hp:6.0f} {r.uptime*100:4.0f}% {r.e_cd:5.1f} {r.team_amp*100:4.0f}%"
            )
            a(f"                 {item_names(r.items)}")
        a(
            "  Qs in kite / poke, heal from kite: "
            + "   ".join(
                f"{short(n)} {timelines[n][m].qs_kite}/{timelines[n][m].qs_poke}q {timelines[n][m].heal_kite:.0f}hp"
                for n in BUILD_ORDER
            )
        )
        a("  Equal-stack tank kite (crit build's stacks on every build):")
        ref = timelines["Crit: ER → IE → RFC → LDR"][m].stacks
        a(f"    pinned stacks = {ref:.0f}")
        for name in BUILD_ORDER:
            r = timelines[name][m]
            a(f"    {short(name):<16} own {r.kite_tank:7.0f}    pinned {r.equal_kite_tank:7.0f}")
    a("")
    a("-" * 88)
    a("HEAD TO HEAD — Crit IE/RFC minus Ability, and the closer hybrid")
    a("Positive means crit dealt more. Messy uses dive uptime.")
    a("-" * 88)
    a(f"  {'Min':>4} {'Δ kite sq':>10} {'Δ kite tk':>10} {'Δ poke':>8} {'Δ messy':>9} {'Δ stacks':>9} {'Ability HP':>10} {'Crit HP':>8}")
    crit_name = "Crit: ER → IE → RFC → LDR"
    abil_name = "Ability: ER → Cleaver → Shojin"
    hyb_name = "Hybrid: ER → Shojin → IE"
    cleave_name = "Hybrid: ER → Cleaver → IE"
    for m in spikes:
        c = timelines[crit_name][m]
        b = timelines[abil_name][m]
        a(
            f"  {m:02d}:00 {c.kite_squish - b.kite_squish:10.0f} {c.kite_tank - b.kite_tank:10.0f}"
            f" {c.poke_squish - b.poke_squish:8.0f} {c.kite_squish*c.uptime - b.kite_squish*b.uptime:9.0f}"
            f" {c.stacks - b.stacks:9.0f} {b.hp:10.0f} {c.hp:8.0f}"
        )
    lines.extend(trinity_lines(timelines, stacks))
    lines.extend(full_build_lines())
    a("-" * 88)
    a("WHEN TO CHOOSE WHICH")
    a("-" * 88)
    lines.extend(decision_lines(timelines, stacks))
    a("")
    a("-" * 88)
    a("ASSUMPTIONS THAT MOVE THE ANSWER")
    a("-" * 88)
    a("  • Q crit is a ratio, not a roll. 100% crit = 1.75x physical. IE makes it 1.975x.")
    a("  • Autos crit for 200%, or 230% with Infinity Edge. Expected value, not a lucky fight.")
    a("  • Stack magic on Q is 25–55% of stacks from crit, 64% with IE. It is not crit twice.")
    a("  • W magic is 55% of stacks and does not care about crit. E magic does, bolts do not.")
    a("  • 225-stack burn is true damage from bonus AD and stacks. Crit does not increase the %.")
    a("  • Execute threshold is a flat 6.5% max HP. The Collector's 5% does not add anything.")
    a("  • Shojin's +12% ramps across the fight and applies to abilities, including the burn.")
    a("    It does not apply to autos, spellblade, Deathfire Touch, or Muramana Shock.")
    a("  • Trinity spellblade is 200% base AD on a 1.5s cooldown, and it does not restore mana.")
    a("    Essence Reaver is 125% base AD plus up to 50 from crit, and it refunds mana.")
    a("  • Awe is 2% max mana as bonus AD. Tear gains 27 bonus mana a minute while held,")
    a("    cap 360. Muramana replaces the item's mana with 1000 and turns Shock on.")
    a("    Q is a spell and an on-hit in one instance, so Shock uses the ranged ability")
    a("    ratio only (3% max mana). Autos are 1.2%. W, E, and R each proc it once.")
    a("  • After 25 stacks, Q is treated as AoE for Deathfire Touch (2s burn). Haste that")
    a("    holds Q under 2s keeps the burn up; a 2.9s Q lets it fall off between casts.")
    a("  • Cleaver is 6% armor reduction per physical hit, 5 stacks. Q and each auto add one.")
    a("    E's bolts fill it immediately. Allies get that shred; it is the Team column.")
    a("  • Rapid Firecannon range is the energized attack only: +35% range, capped at +150.")
    a("    Q inherits bonus attack range, so the proc Q reaches 700. Damage column adds the")
    a("    40 magic proc, not the range. Range is why you live, and it is not in the DPS.")
    a("  • Navori reduces remaining basic cooldowns by 15% per auto. Q itself is not counted")
    a("    as that auto. If Q does proc it in the live client, Navori is better than shown.")
    a("  • Endless Hunger Famine uses the ranged rate, 5 + 10% bonus AD ability haste.")
    a("  • All-in spends about 2s on R and E. Into armor those spells replace Qs and autos")
    a("    that would have hurt more, so tank kite is often higher than tank all-in.")
    a("    E is still the escape. The damage sim does not give it credit for dodging.")
    a("  • Dive uptime is a growing physical+magic burst against your HP, armor, and MR.")
    a("    Shieldbow would add its shield; none of these paths buy it. The Live column is")
    a("    'you got hit'. RFC's extra range is how the crit path makes that burst miss.")
    a("  • No Gathering Storm, no Jack of All Trades, no adaptive shards.")
    a("")
    return "\n".join(lines) + "\n"


def first_with(timelines: Dict[str, List[MinuteRow]], build: str, item: str) -> Optional[int]:
    for row in timelines[build]:
        if item in row.items:
            return row.minute
    return None


def trinity_lines(timelines: Dict[str, List[MinuteRow]], stacks: Dict[str, List[float]]) -> List[str]:
    """Trinity / Manamune / Serylda / Shojin against the ER ability path and straight crit."""
    crit = "Crit: ER → IE → RFC → LDR"
    abil = "Ability: ER → Cleaver → Shojin"
    tri = TRI_NAME
    lines = [
        "-" * 88,
        "TRINITY → MANAMUNE → SERYLDA → SHOJIN",
        "Tear on the first back starts the 360 mana clock. Trinity is still the first legendary.",
        "This path has 0 crit, so Q stays at 1.00x. Spellblade is 200% base AD. Shock is 3% max mana.",
        "Tear uptime is 90% of Essence Reaver's, because Tear does not refund mana.",
        "-" * 88,
    ]

    def at_item(item: str) -> str:
        return fmt_min(first_with(timelines, tri, item)).strip()

    mura_at = next((row.minute for row in timelines[tri] if row.muramana), None)
    lines.append(
        f"  Tear {at_item('Tear of the Goddess')}   Trinity {at_item('Trinity Force')}"
        f"   Ionian {at_item('Ionian Boots of Lucidity')}   Manamune {at_item('Manamune')}"
        f"   Muramana {fmt_min(mura_at).strip()}"
    )
    serylda = "Serylda's Grudge"
    lines.append(
        f"  Last Whisper {at_item('Last Whisper')}   Serylda {at_item(serylda)}"
        f"   Shojin {at_item('Spear of Shojin')}"
    )
    lines.append("")
    lines.append(
        f"  {'Min':>4} {'Build':<10} {'Q cd':>5} {'Stk':>5} {'Tear':>5} {'AD':>6}"
        f" {'Poke':>7} {'KiteSq':>7} {'KiteTk':>7} {'HP':>6} {'Live':>5}"
    )
    for m in (11, 16, 18, 22, 28):
        for name in (tri, abil, crit):
            r = timelines[name][m]
            mura = "mura" if r.muramana else ""
            lines.append(
                f"  {m:02d}:00 {short(name):<10} {r.q_cd:5.2f} {r.stacks:5.0f}"
                f" {r.tear_bonus:5.0f} {r.bonus_ad:6.0f} {r.poke_squish:7.0f}"
                f" {r.kite_squish:7.0f} {r.kite_tank:7.0f} {r.hp:6.0f} {r.uptime*100:4.0f}% {mura}"
            )
            lines.append(f"              {item_names(r.items)}")
        lines.append("")
    t225 = milestone(stacks[tri], 225)
    lines.append(
        f"  225 stacks on Trinity: {fmt_min(t225).strip()}."
        f" Ability {fmt_min(milestone(stacks[abil], 225)).strip()},"
        f" crit {fmt_min(milestone(stacks[crit], 225)).strip()}."
    )
    lines.append("")
    return lines


def full_build_lines(level_targets_minute: int = 28) -> List[str]:
    """Completed paths at level 18, same stacks, minute-28 targets. Gold ignored."""
    stacks = 250.0
    lines = [
        "-" * 88,
        "FULL BUILD — level 18, 250 stacks, gold ignored, targets from 28:00",
        "This is the item philosophy after the last buy. The timeline above is when it arrives.",
        "Navori's fifth crit item is past 100% crit and does not raise Q. Bloodthirster adds no crit.",
        "Trinity's row is Muramana with 360 bonus mana. It still has no crit.",
        "-" * 88,
    ]
    squish = target_at("squish", level_targets_minute)
    tank = target_at("tank", level_targets_minute)
    lines.append(
        f"  {'Build':<16} {'Crit':>5} {'Q cd':>5} {'HP':>6} {'E cd':>5}"
        f" {'Q hit':>7} {'Poke':>7} {'KiteSq':>7} {'KiteTk':>7} {'Qs':>3} {'Live':>5} {'Team':>5}"
    )
    for name in list(BUILD_ORDER) + [TRI_NAME]:
        names = completed_names(BUILD_PATHS[name])
        tear = 360.0 if name == TRI_NAME else 0.0
        kit = loadout_from(names, 18, stacks, tear)
        poke = simulate_fight(kit, squish, "poke")
        kite_s = simulate_fight(kit, squish, "kite")
        kite_t = simulate_fight(kit, tank, "kite")
        _incoming, uptime, _ehp = survival(kit, level_targets_minute)
        raw_crit = sum(ITEMS[n].crit for n in names)
        lines.append(
            f"  {short(name):<16} {raw_crit*100:4.0f}% {kit.q_cd:5.2f} {kit.hp:6.0f}"
            f" {kit.e_cd:5.1f} {q_hit_on(kit, squish):7.0f} {poke.total:7.0f}"
            f" {kite_s.total:7.0f} {kite_t.total:7.0f} {kite_s.qs:3d} {uptime*100:4.0f}%"
            f" {(ally_phys_amp(tank.armor) if kit.cleaver else 0)*100:4.0f}%"
        )
        lines.append(f"                 {item_names(names)}")
    lines.append("")
    return lines


def decision_lines(timelines: Dict[str, List[MinuteRow]], stacks: Dict[str, List[float]]) -> List[str]:
    crit = "Crit: ER → IE → RFC → LDR"
    navori = "Crit: ER → IE → Navori → LDR"
    abil = "Ability: ER → Cleaver → Shojin"
    hyb = "Hybrid: ER → Shojin → IE"
    cleave = "Hybrid: ER → Cleaver → IE"
    out: List[str] = []

    def at(name: str, m: int) -> MinuteRow:
        return timelines[name][m]

    c16, b16 = at(crit, 16), at(abil, 16)
    c18, b18 = at(crit, 18), at(abil, 18)
    c22, b22, h22, k22 = at(crit, 22), at(abil, 22), at(hyb, 22), at(cleave, 22)
    c28, b28, h28, k28, n28 = at(crit, 28), at(abil, 28), at(hyb, 28), at(cleave, 28), at(navori, 28)
    ie_at = first_with(timelines, crit, "Infinity Edge")

    def pct(new: float, old: float) -> str:
        if old <= 0:
            return "n/a"
        return f"{(new / old - 1) * 100:+.0f}%"

    out.append("  IE is ability scaling. Q is multiplied by crit chance (up to 1.75x) and IE")
    out.append("  multiplies that bonus again (1.975x at 100% crit). Haste does not raise the")
    out.append("  multiplier. It raises how often Q is cast, how fast 225 stacks arrive, and")
    out.append("  how long Deathfire stays up once Q is an AoE. Shojin then adds up to +12%.")
    out.append("")
    out.append("  Choose CRIT (ER → Berserker's → IE → RFC → LDR) when you can auto and you")
    out.append("  need range more than you need a health bar.")
    if ie_at is None:
        out.append("    This gold curve never finishes Infinity Edge.")
    else:
        bought = at(crit, ie_at)
        out.append(
            f"    IE completes at {ie_at:02d}:00. Squishy kite that minute is {bought.kite_squish:.0f}"
            f" vs ability {at(abil, ie_at).kite_squish:.0f} ({pct(bought.kite_squish, at(abil, ie_at).kite_squish)})."
        )
    out.append(
        f"    At 16:00 IE is {'in' if 'Infinity Edge' in c16.items else 'not finished'}"
        f" ({item_names(c16.items)}). Squishy kite is {c16.kite_squish:.0f} vs ability"
        f" {b16.kite_squish:.0f} ({pct(c16.kite_squish, b16.kite_squish)}). Poke is already"
        f" ability's: {b16.poke_squish:.0f} vs {c16.poke_squish:.0f}."
    )
    out.append(
        f"    At 22:00, with RFC, squishy kite is {c22.kite_squish:.0f} vs ability {b22.kite_squish:.0f}"
        f" ({pct(c22.kite_squish, b22.kite_squish)}) and vs Cleaver-into-IE {k22.kite_squish:.0f}."
        f" Poke is {c22.poke_squish:.0f} vs ability {b22.poke_squish:.0f}"
        f" and vs Shojin-into-IE {h22.poke_squish:.0f}."
    )
    out.append(
        "    RFC's damage proc is small. The energized Q goes out from 700 range instead of"
    )
    out.append(
        "    550. That range is not in the damage columns. It is how this path avoids the dive"
    )
    out.append("    the Live column assumes you ate. Skip RFC only when nothing outranges you.")
    out.append(
        f"    At 28:00 crit kite-squishy is {c28.kite_squish:.0f}, behind Cleaver-into-IE"
        f" ({k28.kite_squish:.0f}) and ahead of pure ability ({b28.kite_squish:.0f})."
        f" Crit chance on the crit path is {c28.crit*100:.0f}%."
        " Another crit item would not raise Q's multiplier."
    )
    out.append("")
    out.append("  Choose ABILITY (ER → Ionian → Cleaver → Shojin → Hunger → Serylda) when you")
    out.append("  will get hit, you are mostly throwing Q, or an AD team needs the shred.")
    out.append(
        f"    Health at 22:00 is {b22.hp:.0f} vs crit {c22.hp:.0f}. If the dive lands, uptime is"
        f" {b22.uptime*100:.0f}% vs {c22.uptime*100:.0f}%. Messy damage (kite × uptime) is"
        f" {b22.kite_squish*b22.uptime:.0f} vs {c22.kite_squish*c22.uptime:.0f}."
    )
    out.append(
        f"    E is back in {b22.e_cd:.1f}s vs {c22.e_cd:.1f}s. Q cooldown is {b22.q_cd:.2f}s"
        f" vs {c22.q_cd:.2f}s, so the 8s poke throws {b22.qs_poke} Qs vs {c22.qs_poke}."
    )
    t225_b = milestone(stacks[abil], 225)
    t225_c = milestone(stacks[crit], 225)
    t225_h = milestone(stacks[hyb], 225)
    out.append(
        f"    The 225 burn and execute arrive at {fmt_min(t225_b).strip()} on ability,"
        f" {fmt_min(t225_h).strip()} on Shojin-into-IE, and {fmt_min(t225_c).strip()} on crit."
    )
    out.append(
        f"    Full Carve is {b22.team_amp*100:.0f}% more physical damage for allies on the 22:00 tank."
    )
    out.append(
        f"    Personal tank kite at 28:00 is still lower: ability {b28.kite_tank:.0f} vs crit"
        f" {c28.kite_tank:.0f} ({pct(b28.kite_tank, c28.kite_tank)}). Equal-stack tank kite is"
        f" {b28.equal_kite_tank:.0f}, so the extra stacks are a small slice of that gap."
        " The multiplier and LDR are the rest. Serylda is not finished; the pen in the bag"
        " is a Last Whisper (18%), not 35%."
    )
    out.append(
        f"    Heal over the 28:00 squishy kite is {b28.heal_kite:.0f} on ability vs {c28.heal_kite:.0f}"
        f" on crit. Hunger and Gluttonous are the vamp; crit has Doran's 2.5% until a later item."
    )
    out.append("")
    out.append("  Choose HYBRID when the game asks for both jobs in order.")
    out.append("    Shojin second, then IE. Take this when dive is real and you will outscale it.")
    out.append(
        f"    You do not have IE at 16:00 (ability-haste second). At 18:00 squishy kite is"
        f" {at(hyb, 18).kite_squish:.0f} vs crit {c18.kite_squish:.0f}. At 22:00, IE is in:"
        f" poke {h22.poke_squish:.0f} (best of the five), squishy kite {h22.kite_squish:.0f},"
        f" HP {h22.hp:.0f}, dive uptime {h22.uptime*100:.0f}%, E in {h22.e_cd:.1f}s."
    )
    out.append(
        f"    At 28:00 Shojin-into-IE kite-squishies for {h28.kite_squish:.0f} and kite-tanks for"
        f" {h28.kite_tank:.0f}, with {h28.qs_kite} Qs inside the kite."
    )
    out.append("    Cleaver second, then IE and LDR. Take this when the front line is the fight")
    out.append("    and someone else on your team is physical damage.")
    out.append(
        f"    At 22:00 tank kite is {k22.kite_tank:.0f} (crit {c22.kite_tank:.0f}, ability {b22.kite_tank:.0f})"
        f" and ally amp is {k22.team_amp*100:.0f}%, at {k22.uptime*100:.0f}% dive uptime."
    )
    out.append(
        f"    At 28:00 it leads the gold-gated table: squishy kite {k28.kite_squish:.0f},"
        f" tank kite {k28.kite_tank:.0f}, HP {k28.hp:.0f}, dive uptime {k28.uptime*100:.0f}%."
        " It still has no RFC, so that lead assumes 550 range."
    )
    out.append("")
    out.append("  Navori is crit's way of buying Qs without giving up crit chance.")
    out.append(
        f"    At 28:00 the sheet Q cooldown is still {n28.q_cd:.2f}s. The 8s kite fits"
        f" {n28.qs_kite} Qs on Navori and {c28.qs_kite} on RFC crit, so this window does not"
        f" show an extra cast. {n28.kite_squish:.0f} vs {c28.kite_squish:.0f} is the attack speed."
        f" Poke, with no autos to refund cooldown, is {n28.poke_squish:.0f} vs {c28.poke_squish:.0f}."
    )
    out.append("    It does not replace Shojin. Shojin works from fog. Navori works while you auto.")
    out.append("    It also does not give the health Cleaver and Shojin give.")
    squish = target_at("squish", 28)
    tank = target_at("tank", 28)
    finished = {}
    for name in (crit, navori, abil, hyb, cleave):
        kit = loadout_from(completed_names(BUILD_PATHS[name]), 18, 250)
        finished[name] = (
            simulate_fight(kit, squish, "kite").total,
            simulate_fight(kit, tank, "kite").total,
            simulate_fight(kit, squish, "poke").total,
            survival(kit, 28)[1],
            simulate_fight(kit, squish, "kite").qs,
        )
    fc, fn, fb, fk = finished[crit], finished[navori], finished[abil], finished[cleave]
    out.append("")
    out.append("  The full-build table is the same fight after the last buy, stacks pinned at 250.")
    out.append(
        f"    Bloodthirster crit kite-squishy is {fc[0]:.0f} and tank kite {fc[1]:.0f},"
        f" at {fc[3]*100:.0f}% dive uptime. Cleaver-into-IE-LDR-RFC is {fk[0]:.0f} / {fk[1]:.0f}"
        f" at {fk[3]*100:.0f}% uptime. The 28:00 Cleaver lead was timing: crit had not bought"
        f" the 80 AD yet, and Cleaver had no RFC."
    )
    out.append(
        f"    Finished ability poke is {fb[2]:.0f} vs finished crit poke {fc[2]:.0f},"
        f" with dive uptime {fb[3]*100:.0f}% vs {fc[3]*100:.0f}%."
        f" Finished Navori gets {fn[4]} Qs in the kite vs {fc[4]}, and kite-squishy"
        f" {fn[0]:.0f} vs Bloodthirster's {fc[0]:.0f}."
    )
    out.append("")
    out.append("  Rule of thumb from these spikes:")
    out.append("    • You can free-hit squishies and you need 700 range — crit, IE before health.")
    out.append("    • You will only Q — haste first. Add IE when you can. Do not buy RFC to poke.")
    out.append("    • Assassin or engage will touch you — Shojin or Cleaver before IE.")
    out.append("    • Tanks, and your team is AD — Cleaver, then IE and LDR. Do not stop on Shojin.")
    out.append("    • Tanks, and you are the only AD — LDR is your pen. Cleaver's amp has no partner.")
    out.append("    • At 100% crit, stop buying crit. The next cloak does not scale Q.")
    out.append("    • Do not buy The Collector. The execute is already 6.5% max health.")
    out.extend(trinity_decision(timelines, stacks))
    return out


def trinity_decision(timelines: Dict[str, List[MinuteRow]], stacks: Dict[str, List[float]]) -> List[str]:
    """When Tear → Trinity → Manamune → Serylda → Shojin beats the Essence Reaver haste path."""
    tri = TRI_NAME
    abil = "Ability: ER → Cleaver → Shojin"
    crit = "Crit: ER → IE → RFC → LDR"
    out: List[str] = []

    def at(name: str, m: int) -> MinuteRow:
        return timelines[name][m]

    def pct(new: float, old: float) -> str:
        if old <= 0:
            return "n/a"
        return f"{(new / old - 1) * 100:+.0f}%"

    mura_at = next((row.minute for row in timelines[tri] if row.muramana), None)
    tri_at = first_with(timelines, tri, "Trinity Force")
    mana_at = first_with(timelines, tri, "Manamune")
    sery_at = first_with(timelines, tri, "Serylda's Grudge")
    shoj_at = first_with(timelines, tri, "Spear of Shojin")
    t11, a11, c11 = at(tri, 11), at(abil, 11), at(crit, 11)
    t16, a16, c16 = at(tri, 16), at(abil, 16), at(crit, 16)
    t22, a22, c22 = at(tri, 22), at(abil, 22), at(crit, 22)
    t28, a28, c28 = at(tri, 28), at(abil, 28), at(crit, 28)
    out.append("")
    out.append("  TRINITY (Tear → Trinity → Ionian → Manamune → Serylda → Shojin) is the")
    out.append("  no-crit ability path. Q stays at 1.00x. Tear is the first back, or the")
    out.append("  360 mana clock starts late and Muramana misses the mid game.")
    if tri_at is not None:
        out.append(
            f"    Trinity completes at {tri_at:02d}:00, Ionian at 11:00, Manamune at"
            f" {fmt_min(mana_at).strip()}. Muramana turns on at {fmt_min(mura_at).strip()}"
            f" because Tear is already at {at(tri, mura_at).tear_bonus:.0f} bonus mana."
            if mura_at is not None
            else f"    Trinity completes at {tri_at:02d}:00. Muramana is not online by 28:00."
        )
    out.append(
        f"    At 11:00, with Trinity and Ionian, squishy kite is {t11.kite_squish:.0f}"
        f" vs ability {a11.kite_squish:.0f} ({pct(t11.kite_squish, a11.kite_squish)})"
        f" and vs crit {c11.kite_squish:.0f} ({pct(t11.kite_squish, c11.kite_squish)})."
        f" HP is {t11.hp:.0f} vs {a11.hp:.0f} vs {c11.hp:.0f}."
        " This is the window the item is for: before Infinity Edge exists."
    )
    out.append(
        f"    Muramana's minute, poke is {t16.poke_squish:.0f} vs ability {a16.poke_squish:.0f}"
        f" ({pct(t16.poke_squish, a16.poke_squish)}) and vs crit {c16.poke_squish:.0f}"
        f" ({pct(t16.poke_squish, c16.poke_squish)}). Squishy kite is {t16.kite_squish:.0f}"
        f" vs ability {a16.kite_squish:.0f} vs crit {c16.kite_squish:.0f}."
    )
    out.append(
        f"    At 22:00 Serylda is in and Shojin is not. Poke {t22.poke_squish:.0f} vs ability"
        f" {a22.poke_squish:.0f} ({pct(t22.poke_squish, a22.poke_squish)}). Kite-squishy"
        f" {t22.kite_squish:.0f} vs ability {a22.kite_squish:.0f} vs crit {c22.kite_squish:.0f}."
        f" Tank kite {t22.kite_tank:.0f} vs {a22.kite_tank:.0f} vs {c22.kite_tank:.0f}."
        f" HP {t22.hp:.0f} vs ability {a22.hp:.0f} (Shojin is already on that path)."
        f" Dive uptime {t22.uptime*100:.0f}% vs {a22.uptime*100:.0f}% vs {c22.uptime*100:.0f}%."
    )
    out.append(
        f"    At 28:00 Serylda is {'in' if sery_at is not None and sery_at <= 28 else 'not finished'}"
        f" and Shojin is {'in' if shoj_at is not None and shoj_at <= 28 else 'not finished'}."
        f" Poke {t28.poke_squish:.0f} vs ability {a28.poke_squish:.0f} ({pct(t28.poke_squish, a28.poke_squish)})."
        f" Kite-squishy {t28.kite_squish:.0f} vs ability {a28.kite_squish:.0f}"
        f" vs crit {c28.kite_squish:.0f}. Tank kite {t28.kite_tank:.0f} vs {a28.kite_tank:.0f}"
        f" vs {c28.kite_tank:.0f}. HP {t28.hp:.0f}, dive uptime {t28.uptime*100:.0f}%."
    )
    out.append(
        f"    225 stacks arrive at {fmt_min(milestone(stacks[tri], 225)).strip()} on Trinity,"
        f" {fmt_min(milestone(stacks[abil], 225)).strip()} on ability,"
        f" {fmt_min(milestone(stacks[crit], 225)).strip()} on crit."
        " Tear does not refund mana, so the cast rate stays under Essence Reaver."
    )
    squish = target_at("squish", 28)
    tank = target_at("tank", 28)
    kit = loadout_from(completed_names(BUILD_PATHS[tri]), 18, 250, 360)
    abil_kit = loadout_from(completed_names(BUILD_PATHS[abil]), 18, 250)
    kite_s = simulate_fight(kit, squish, "kite").total
    kite_t = simulate_fight(kit, tank, "kite").total
    poke = simulate_fight(kit, squish, "poke").total
    abil_poke = simulate_fight(abil_kit, squish, "poke").total
    uptime = survival(kit, 28)[1]
    out.append(
        f"    Finished, stacks pinned at 250: poke {poke:.0f} vs ability {abil_poke:.0f},"
        f" kite-squishy {kite_s:.0f}, kite-tank {kite_t:.0f}, dive uptime {uptime*100:.0f}%."
        " Essence Reaver's 25% crit still multiplies Q, and Cleaver shreds for the team."
    )
    out.append("    Take Trinity when you want the 09:00 spike and you are not going crit.")
    out.append("    Take Essence Reaver → Cleaver when the game goes long or the team is AD.")
    out.append("    Take crit when you can auto after Infinity Edge. This path never catches that kite.")
    out.append("    Buy Shojin before Serylda when the dive is already landing. Pen does not add HP.")
    return out


def rows_to_json(timelines: Dict[str, List[MinuteRow]], stacks: Dict[str, List[float]]) -> dict:
    def row_dict(r: MinuteRow) -> dict:
        return {
            "minute": r.minute,
            "items": r.items,
            "level": r.level,
            "stacks": round(r.stacks, 1),
            "crit": round(r.crit, 3),
            "ah": round(r.ah, 1),
            "basic_ah": round(r.basic_ah, 1),
            "bonus_ad": round(r.bonus_ad, 1),
            "hp": round(r.hp, 1),
            "q_cd": round(r.q_cd, 3),
            "e_cd": round(r.e_cd, 3),
            "q_hit_squish": round(r.q_squish, 1),
            "poke_squish": round(r.poke_squish, 1),
            "kite_squish": round(r.kite_squish, 1),
            "kite_bruiser": round(r.kite_bruiser, 1),
            "kite_tank": round(r.kite_tank, 1),
            "allin_squish": round(r.allin_squish, 1),
            "allin_tank": round(r.allin_tank, 1),
            "heal_kite_squish": round(r.heal_kite, 1),
            "dive_uptime": round(r.uptime, 3),
            "ehp_physical": round(r.ehp, 1),
            "qs_in_poke": r.qs_poke,
            "qs_in_kite": r.qs_kite,
            "ally_phys_amp_vs_tank": round(r.team_amp, 3),
            "equal_stack_kite_tank": round(r.equal_kite_tank, 1),
            "legendaries": r.legendaries,
            "tear_bonus_mana": round(r.tear_bonus, 1),
            "muramana": r.muramana,
        }

    builds = {}
    for name, rows in timelines.items():
        builds[name] = {
            "stacks_at": {str(m): round(stacks[name][m], 1) for m in range(0, 29)},
            "milestone_25": milestone(stacks[name], 25),
            "milestone_125": milestone(stacks[name], 125),
            "milestone_225": milestone(stacks[name], 225),
            "minutes": {str(m): row_dict(rows[m]) for m in range(0, 29)},
        }
    return {
        "patch": "26.19",
        "ddragon": "16.19.1",
        "window_seconds": WINDOW,
        "builds": builds,
    }


def self_check() -> None:
    assert abs(q_crit_bonus(1.0, 0.0) - 0.75) < 1e-9
    assert abs(q_crit_bonus(1.0, 0.30) - 0.975) < 1e-9
    assert abs(q_stack_ratio(0.0, 0.0) - 0.25) < 1e-9
    assert abs(q_stack_ratio(1.0, 0.0) - 0.55) < 1e-9
    assert abs(q_stack_ratio(1.0, 0.30) - 0.64) < 1e-9
    assert abs(e_stack_ratio(1.0, 0.0) - 0.128) < 1e-9
    assert abs(e_stack_ratio(1.0, 0.30) - 0.1424) < 1e-6
    assert abs(auto_crit_bonus(1.0, 0.30) - 1.30) < 1e-9
    # 200 bonus AD, 225 stacks → 5% + 1.125% = 6.125% max HP
    assert abs(burn_max_hp_fraction(200, 225) - 0.06125) < 1e-9
    assert burn_max_hp_fraction(200, 224) == 0.0
    # Q cooldown: rank 5, 40 AH, 25 basic AH → 2.0s
    assert abs(3.5 * haste_factor(40) * haste_factor(25) - 2.0) < 1e-9
    names = resolve_inventory(BUILD_PATHS["Crit: ER → IE → RFC → LDR"], gold_at_minute(18))
    assert "Infinity Edge" in names, names
    assert "Essence Reaver" in names
    kit = loadout_from(names, 11, 100)
    assert kit.ie == 0.30
    assert kit.er and not kit.sheen
    # Spellblade base and Q ratio stay in a human range at two items.
    assert 150 < q_hit_on(kit, target_at("squish", 16)) < 900
    # Level 11 base AD is 81. Trinity spellblade is 200% of that.
    tri_kit = loadout_from(["Trinity Force"], 11, 0)
    assert abs(tri_kit.base_ad - 81.0) < 1e-9
    assert abs(spellblade_damage(tri_kit) - 162.0) < 1e-9
    assert tri_kit.trinity and not tri_kit.sheen
    # Level 18, Muramana, 360 bonus mana: 300 + 680 + 1000 + 360 = 2340. Awe is 46.8.
    mura = loadout_from(["Manamune"], 18, 0, tear_bonus=360)
    assert mura.muramana
    assert abs(mura.max_mana - 2340.0) < 1e-9
    assert abs(mura.bonus_ad - (35.0 + 0.02 * 2340.0)) < 1e-9
    half = loadout_from(["Manamune"], 18, 0, tear_bonus=200)
    assert not half.muramana
    assert abs(half.max_mana - (300.0 + 40.0 * 17 + 500.0 + 200.0)) < 1e-9
    tri_path = BUILD_PATHS[TRI_NAME]
    tear_line = tear_bonus_timeline(tri_path)
    first_tear = first_tri = first_mana = first_mura = None
    for m in range(0, GAME_MINUTES + 1):
        names = resolve_inventory(tri_path, gold_at_minute(m))
        if first_tear is None and any(n in names for n in ("Tear of the Goddess", "Manamune")):
            first_tear = m
        if first_tri is None and "Trinity Force" in names:
            first_tri = m
        if first_mana is None and "Manamune" in names:
            first_mana = m
        owned = loadout_from(names, level_at_minute(m), 0, tear_line[m])
        if first_mura is None and owned.muramana:
            first_mura = m
    assert first_tear is not None and first_tri is not None and first_tear < first_tri
    assert first_mana is not None and first_tri < first_mana
    assert first_mura is not None and first_mura >= first_mana
    assert tear_line[first_mura] >= 360


def main() -> None:
    self_check()
    stacks = {name: stack_timeline(path) for name, path in BUILD_PATHS.items()}
    tear_lines = {name: tear_bonus_timeline(path) for name, path in BUILD_PATHS.items()}
    # Equal-stack column pins everyone to the straight crit build's stacks.
    ref_stacks = stacks["Crit: ER → IE → RFC → LDR"]
    timelines: Dict[str, List[MinuteRow]] = {}
    for name in BUILD_PATHS:
        rows = []
        for m in range(0, GAME_MINUTES + 1):
            rows.append(row_for(name, m, stacks[name][m], ref_stacks[m], tear_lines[name][m]))
        timelines[name] = rows
    report = build_report(timelines, stacks)
    out_dir = __file__.rsplit("/", 1)[0]
    report_path = out_dir + "/report.txt"
    json_path = out_dir + "/results.json"
    with open(report_path, "w", encoding="utf-8") as fh:
        fh.write(report)
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(rows_to_json(timelines, stacks), fh, indent=2)
        fh.write("\n")
    print(report)
    print(f"Wrote {report_path}")
    print(f"Wrote {json_path}")


if __name__ == "__main__":
    main()
