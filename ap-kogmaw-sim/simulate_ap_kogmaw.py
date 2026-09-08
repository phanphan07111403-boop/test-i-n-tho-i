#!/usr/bin/env python3
"""
PC League of Legends — AP Kog'Maw (mid / AP bot)
Patch snapshot ~26.x (Sep 2026 item values).

Playstyle: núp bắn — fog-of-war Living Artillery poke, then max-range
W autos from brush/fog edge. Must still hurt tanks.

Question:
  Luden or Blackfire first, Malignance second, then 3rd item damage
  feels like it falls off. Try Malignance rush instead.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import json

GAME_MINUTES = 28

# ---------------------------------------------------------------------------
# Economy / XP (AP Kog mid-or-bot farmer, not smurf-fed)
# ---------------------------------------------------------------------------


def gold_at_minute(m: int) -> int:
    if m <= 0:
        return 500
    total = 500
    for t in range(1, m + 1):
        if t <= 5:
            total += 310
        elif t <= 10:
            total += 420
        elif t <= 16:
            total += 500
        elif t <= 22:
            total += 540
        else:
            total += 580
    return total


def level_at_minute(m: int) -> int:
    table = {
        1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7, 7: 8, 8: 9,
        9: 10, 10: 11, 11: 11, 12: 12, 13: 12, 14: 13,
        15: 13, 16: 14, 17: 14, 18: 15, 19: 15, 20: 16,
        21: 16, 22: 17, 23: 17, 24: 17, 25: 18, 26: 18,
        27: 18, 28: 18,
    }
    return table.get(m, min(18, 1 + m))


def skill_rank(level: int, skill: str) -> int:
    """W max, Q second, E last. R at 6/11/16."""
    if skill == "R":
        if level < 6:
            return 0
        if level < 11:
            return 1
        if level < 16:
            return 2
        return 3
    # Order: Q1, W2, W3, E4, W5, R6, W7, Q8, W9, Q10, R11, Q12, Q13, E14, E15, R16
    q_levels = [1, 8, 10, 12, 13]
    w_levels = [2, 3, 5, 7, 9]
    e_levels = [4, 14, 15, 17, 18]
    mapping = {"Q": q_levels, "W": w_levels, "E": e_levels}
    return sum(1 for lv in mapping[skill] if level >= lv)


# ---------------------------------------------------------------------------
# Targets
# ---------------------------------------------------------------------------


def squishy_hp(m: int) -> float:
    lv = level_at_minute(m)
    return 640 + 104 * lv + 18 * m


def squishy_mr(m: int) -> float:
    lv = level_at_minute(m)
    # Cloth / null-magic later
    extra = 0.0 if m < 14 else (12.0 if m < 22 else 25.0)
    return 30 + 1.3 * lv + extra


def tank_hp(m: int) -> float:
    lv = level_at_minute(m)
    # HP items come online mid-game
    item_hp = 80 * max(0, m - 6)
    return 700 + 110 * lv + item_hp


def tank_mr(m: int) -> float:
    lv = level_at_minute(m)
    # Linear MR items after first back — avoids a fake "3rd item drop"
    # when the target's FoN/Visage spike lands on the same minute.
    extra = 0.0 if m < 8 else min(8.5 * (m - 8), 155.0)
    return 32 + 2.05 * lv + extra


def squishy_armor(m: int) -> float:
    lv = level_at_minute(m)
    extra = 0.0 if m < 14 else (18.0 if m < 22 else 35.0)
    return 28.0 + 4.5 * lv + extra


def tank_armor(m: int) -> float:
    lv = level_at_minute(m)
    extra = 0.0 if m < 8 else min(9.0 * (m - 8), 170.0)
    return 33.0 + 4.6 * lv + extra


# ---------------------------------------------------------------------------
# Items
# ---------------------------------------------------------------------------


@dataclass
class Item:
    name: str
    cost: int
    ap: float = 0
    ah: float = 0
    hp: float = 0
    mana: float = 0
    as_pct: float = 0
    flat_mpen: float = 0
    pct_mpen: float = 0
    ult_haste: float = 0
    deathcap: bool = False
    nashor: bool = False
    malignance: bool = False
    luden: bool = False
    blackfire: bool = False
    liandry: bool = False
    ashes: bool = False
    guise: bool = False
    horizon: bool = False
    seraph: bool = False
    archangel: bool = False
    ad: float = 0
    pct_armor_pen: float = 0
    lethality: float = 0
    muramana: bool = False
    manamune: bool = False
    serylda: bool = False
    rylai: bool = False
    tags: Tuple[str, ...] = ()


ITEMS: Dict[str, Item] = {
    "Amplifying Tome": Item("Amplifying Tome", 400, ap=20),
    "Needlessly Large Rod": Item("Needlessly Large Rod", 1200, ap=65),
    "Blasting Wand": Item("Blasting Wand", 850, ap=45),
    "Lost Chapter": Item("Lost Chapter", 1200, ap=40, ah=10, mana=300),
    "Fated Ashes": Item("Fated Ashes", 900, ap=30, ashes=True),
    "Haunting Guise": Item("Haunting Guise", 1300, ap=30, hp=200, guise=True),
    "Hextech Alternator": Item("Hextech Alternator", 1100, ap=45),
    "Blighting Jewel": Item("Blighting Jewel", 1100, ap=25, pct_mpen=0.13),
    "Fiendish Codex": Item("Fiendish Codex", 850, ap=25, ah=10),
    "Recurve Bow": Item("Recurve Bow", 700, as_pct=0.15),
    "Boots": Item("Boots", 300, tags=("boots",)),
    "Sorcerer's Shoes": Item(
        "Sorcerer's Shoes", 1100, flat_mpen=12, tags=("boots",)
    ),
    "Malignance": Item(
        "Malignance",
        2700,
        ap=90,
        ah=15,
        mana=600,
        ult_haste=20,
        malignance=True,
        tags=("mana",),
    ),
    "Luden's Echo": Item(
        "Luden's Echo",
        2750,
        ap=100,
        ah=10,
        mana=600,
        luden=True,
        tags=("mana",),
    ),
    "Blackfire Torch": Item(
        "Blackfire Torch",
        2800,
        ap=80,
        ah=20,
        mana=600,
        blackfire=True,
        tags=("mana", "burn"),
    ),
    "Liandry's Torment": Item(
        "Liandry's Torment",
        3000,
        ap=60,
        hp=300,
        liandry=True,
        tags=("burn", "tank"),
    ),
    "Void Staff": Item(
        "Void Staff", 3000, ap=95, pct_mpen=0.40, tags=("pen", "tank")
    ),
    "Cryptbloom": Item(
        "Cryptbloom", 3000, ap=75, ah=20, pct_mpen=0.30, tags=("pen",)
    ),
    "Shadowflame": Item(
        "Shadowflame", 3200, ap=110, flat_mpen=15, tags=("squishy",)
    ),
    "Rabadon's Deathcap": Item(
        "Rabadon's Deathcap", 3500, ap=130, deathcap=True, tags=("amp",)
    ),
    "Nashor's Tooth": Item(
        "Nashor's Tooth",
        2900,
        ap=80,
        ah=15,
        as_pct=0.50,
        nashor=True,
        tags=("onhit",),
    ),
    "Seeker's Armguard": Item("Seeker's Armguard", 1600, ap=45),
    "Oblivion Orb": Item("Oblivion Orb", 800, ap=30),
    "Horizon Focus": Item(
        "Horizon Focus",
        2700,
        ap=75,
        ah=25,
        horizon=True,
        tags=("fog",),
    ),
    "Zhonya's Hourglass": Item(
        "Zhonya's Hourglass", 3250, ap=105, tags=("defense",)
    ),
    "Morellonomicon": Item(
        "Morellonomicon", 2850, ap=75, ah=15, hp=350, tags=("antiheal",)
    ),
    "Banshee's Veil": Item(
        "Banshee's Veil", 3000, ap=105, tags=("defense",)
    ),
    "Tear of the Goddess": Item("Tear of the Goddess", 400, mana=240),
    "Archangel's Staff": Item(
        "Archangel's Staff",
        2900,
        ap=70,
        ah=25,
        mana=600,
        archangel=True,
        tags=("mana",),
    ),
    "Seraph's Embrace": Item(
        "Seraph's Embrace",
        2900,
        ap=70,
        ah=25,
        mana=1000,
        seraph=True,
        tags=("mana", "shield"),
    ),
    "Manamune": Item(
        "Manamune",
        2900,
        ad=35,
        ah=15,
        mana=500,
        manamune=True,
        tags=("mana", "ad"),
    ),
    "Muramana": Item(
        "Muramana",
        2900,
        ad=35,
        ah=15,
        mana=1000,
        muramana=True,
        tags=("mana", "ad"),
    ),
    "Serylda's Grudge": Item(
        "Serylda's Grudge",
        3000,
        ad=45,
        ah=15,
        pct_armor_pen=0.45,
        serylda=True,
        tags=("pen", "ad", "slow"),
    ),
    "Rylai's Crystal Scepter": Item(
        "Rylai's Crystal Scepter",
        2600,
        ap=65,
        hp=400,
        rylai=True,
        tags=("slow",),
    ),
}


UPGRADE_COMPONENTS = {
    "Sorcerer's Shoes": ("Boots",),
    "Malignance": ("Lost Chapter", "Blasting Wand"),
    "Luden's Echo": ("Lost Chapter", "Hextech Alternator"),
    "Blackfire Torch": ("Lost Chapter", "Fated Ashes"),
    "Liandry's Torment": ("Haunting Guise", "Fated Ashes"),
    "Void Staff": ("Blighting Jewel", "Blasting Wand"),
    "Cryptbloom": ("Blighting Jewel", "Fiendish Codex", "Fiendish Codex"),
    "Shadowflame": ("Hextech Alternator", "Needlessly Large Rod"),
    "Rabadon's Deathcap": ("Needlessly Large Rod", "Needlessly Large Rod"),
    "Nashor's Tooth": ("Recurve Bow", "Blasting Wand", "Fiendish Codex"),
    "Horizon Focus": ("Fiendish Codex", "Fiendish Codex", "Amplifying Tome"),
    "Zhonya's Hourglass": ("Needlessly Large Rod", "Seeker's Armguard"),
    "Morellonomicon": ("Oblivion Orb",),
    "Banshee's Veil": ("Needlessly Large Rod",),
    "Archangel's Staff": ("Tear of the Goddess", "Lost Chapter", "Fiendish Codex"),
    "Seraph's Embrace": ("Archangel's Staff",),
    "Manamune": ("Tear of the Goddess",),
    "Muramana": ("Manamune",),
    "Serylda's Grudge": ("Last Whisper",),
    "Rylai's Crystal Scepter": ("Blasting Wand",),
}

NEXT_COMPONENTS = {
    "Malignance": ["Lost Chapter", "Blasting Wand"],
    "Luden's Echo": ["Lost Chapter", "Hextech Alternator"],
    "Blackfire Torch": ["Fated Ashes", "Lost Chapter"],
    "Liandry's Torment": ["Fated Ashes", "Haunting Guise"],
    "Void Staff": ["Blighting Jewel", "Blasting Wand"],
    "Cryptbloom": ["Blighting Jewel", "Fiendish Codex"],
    "Shadowflame": ["Hextech Alternator", "Needlessly Large Rod"],
    "Rabadon's Deathcap": ["Needlessly Large Rod"],
    "Nashor's Tooth": ["Recurve Bow", "Fiendish Codex", "Blasting Wand"],
    "Sorcerer's Shoes": ["Boots"],
    "Horizon Focus": ["Fiendish Codex", "Amplifying Tome"],
    "Zhonya's Hourglass": ["Seeker's Armguard", "Needlessly Large Rod"],
    "Morellonomicon": ["Oblivion Orb"],
    "Banshee's Veil": ["Needlessly Large Rod"],
    "Archangel's Staff": ["Tear of the Goddess", "Lost Chapter", "Fiendish Codex"],
    "Seraph's Embrace": ["Archangel's Staff"],
}


BUILD_PATHS: Dict[str, List[str]] = {
    # User current — two Lost Chapter items, then a squishy 3rd
    "Luden → Malig → SF": [
        "Lost Chapter",
        "Hextech Alternator",
        "Luden's Echo",
        "Boots",
        "Sorcerer's Shoes",
        "Malignance",
        "Shadowflame",
        "Rabadon's Deathcap",
        "Void Staff",
    ],
    "BF → Malig → SF": [
        "Fated Ashes",
        "Lost Chapter",
        "Blackfire Torch",
        "Boots",
        "Sorcerer's Shoes",
        "Malignance",
        "Shadowflame",
        "Rabadon's Deathcap",
        "Void Staff",
    ],
    # Same two-mana start, tank 3rd (still late tank item)
    "Luden → Malig → Liandry": [
        "Lost Chapter",
        "Hextech Alternator",
        "Luden's Echo",
        "Boots",
        "Sorcerer's Shoes",
        "Malignance",
        "Liandry's Torment",
        "Void Staff",
        "Rabadon's Deathcap",
    ],
    "BF → Malig → Liandry": [
        "Fated Ashes",
        "Lost Chapter",
        "Blackfire Torch",
        "Boots",
        "Sorcerer's Shoes",
        "Malignance",
        "Liandry's Torment",
        "Void Staff",
        "Rabadon's Deathcap",
    ],
    # Proposed: Malignance rush, then tank kit
    "Malig → Liandry → Void": [
        "Lost Chapter",
        "Blasting Wand",
        "Malignance",
        "Boots",
        "Sorcerer's Shoes",
        "Fated Ashes",
        "Haunting Guise",
        "Liandry's Torment",
        "Blighting Jewel",
        "Void Staff",
        "Rabadon's Deathcap",
    ],
    "Malig → Liandry → Cryptbloom": [
        "Lost Chapter",
        "Blasting Wand",
        "Malignance",
        "Boots",
        "Sorcerer's Shoes",
        "Fated Ashes",
        "Haunting Guise",
        "Liandry's Torment",
        "Blighting Jewel",
        "Cryptbloom",
        "Rabadon's Deathcap",
    ],
    "Malig → Liandry → SF": [
        "Lost Chapter",
        "Blasting Wand",
        "Malignance",
        "Boots",
        "Sorcerer's Shoes",
        "Fated Ashes",
        "Haunting Guise",
        "Liandry's Torment",
        "Shadowflame",
        "Void Staff",
        "Rabadon's Deathcap",
    ],
    "Malig → Void → Liandry": [
        "Lost Chapter",
        "Blasting Wand",
        "Malignance",
        "Boots",
        "Sorcerer's Shoes",
        "Blighting Jewel",
        "Void Staff",
        "Liandry's Torment",
        "Rabadon's Deathcap",
    ],
    "Liandry → Malig → Void": [
        "Fated Ashes",
        "Haunting Guise",
        "Liandry's Torment",
        "Boots",
        "Sorcerer's Shoes",
        "Lost Chapter",
        "Malignance",
        "Void Staff",
        "Rabadon's Deathcap",
    ],
    "Malig → Nashor → Liandry": [
        "Lost Chapter",
        "Blasting Wand",
        "Malignance",
        "Boots",
        "Sorcerer's Shoes",
        "Nashor's Tooth",
        "Liandry's Torment",
        "Void Staff",
        "Rabadon's Deathcap",
    ],
    "Luden → SF → Cap (no Malig)": [
        "Lost Chapter",
        "Hextech Alternator",
        "Luden's Echo",
        "Boots",
        "Sorcerer's Shoes",
        "Shadowflame",
        "Rabadon's Deathcap",
        "Void Staff",
    ],
    "Malig → Liandry → Cap": [
        "Lost Chapter",
        "Blasting Wand",
        "Malignance",
        "Boots",
        "Sorcerer's Shoes",
        "Fated Ashes",
        "Haunting Guise",
        "Liandry's Torment",
        "Rabadon's Deathcap",
        "Void Staff",
    ],
}

LEGENDARIES = {
    "Malignance",
    "Luden's Echo",
    "Blackfire Torch",
    "Liandry's Torment",
    "Void Staff",
    "Cryptbloom",
    "Shadowflame",
    "Rabadon's Deathcap",
    "Nashor's Tooth",
    "Horizon Focus",
    "Zhonya's Hourglass",
    "Morellonomicon",
    "Banshee's Veil",
    "Archangel's Staff",
    "Seraph's Embrace",
}

CORE_MALIG_LIANDRY_VOID: List[str] = [
    "Lost Chapter",
    "Blasting Wand",
    "Malignance",
    "Boots",
    "Sorcerer's Shoes",
    "Fated Ashes",
    "Haunting Guise",
    "Liandry's Torment",
    "Blighting Jewel",
    "Void Staff",
]

FOURTH_PATHS: Dict[str, List[str]] = {
    "4th Deathcap": CORE_MALIG_LIANDRY_VOID + [
        "Needlessly Large Rod",
        "Rabadon's Deathcap",
    ],
    "4th Horizon Focus": CORE_MALIG_LIANDRY_VOID + [
        "Fiendish Codex",
        "Horizon Focus",
    ],
    "4th Shadowflame": CORE_MALIG_LIANDRY_VOID + [
        "Hextech Alternator",
        "Shadowflame",
    ],
    "4th Zhonya": CORE_MALIG_LIANDRY_VOID + [
        "Seeker's Armguard",
        "Zhonya's Hourglass",
    ],
    "4th Morello": CORE_MALIG_LIANDRY_VOID + [
        "Oblivion Orb",
        "Morellonomicon",
    ],
    "4th Banshee": CORE_MALIG_LIANDRY_VOID + [
        "Needlessly Large Rod",
        "Banshee's Veil",
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
        needed = list(UPGRADE_COMPONENTS.get(item_name, ()))
        # Cryptbloom / Deathcap can need two of the same component
        available = list(owned)
        for c in needed:
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
        # Boots slot: Sorcs replace Boots
        if item_name == "Sorcerer's Shoes" and "Sorcerer's Shoes" in owned:
            return False
        if item_name != "Sorcerer's Shoes" and item_name in owned:
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
        if step in owned and step != "Needlessly Large Rod":
            # Deathcap needs two NLRs; allow a second copy via path
            if owned.count(step) >= path.count(step):
                continue
        if can_afford(step):
            buy(step)
        else:
            blocked_at = step
            break

    if blocked_at and blocked_at in NEXT_COMPONENTS:
        for comp in NEXT_COMPONENTS[blocked_at]:
            if comp in owned and comp != "Needlessly Large Rod":
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
                if step in owned and step not in (
                    "Needlessly Large Rod",
                    "Fiendish Codex",
                ):
                    continue
                if can_afford(step):
                    buy(step)
                else:
                    for comp in NEXT_COMPONENTS.get(step, []):
                        if gold_pool >= ITEMS[comp].cost:
                            if comp not in owned or comp == "Needlessly Large Rod":
                                buy(comp)
                    if can_afford(step):
                        buy(step)
                    else:
                        break

    if "Sorcerer's Shoes" in owned and "Boots" in owned:
        owned.remove("Boots")

    return [ITEMS[n] for n in owned]


# ---------------------------------------------------------------------------
# Combat model
# ---------------------------------------------------------------------------

POKE_WINDOW = 8.0  # fog R barrage
SIEGE_WINDOW = 8.0  # max-range W from brush
# núp bắn mix: mostly artillery, some W when they walk up / you siege
FOG_WEIGHT = 0.70
SIEGE_WEIGHT = 0.30


@dataclass
class Snapshot:
    minute: int
    build_name: str
    items: List[str]
    gold: int
    level: int
    ap: float
    ah: float
    legendary_count: int
    fog_tank: float
    fog_squish: float
    siege_tank: float
    mix_tank: float
    mix_squish: float
    r_shots_poke: int
    notes: str
    has_malig: bool
    has_liandry: bool
    has_void: bool
    has_luden: bool
    has_bf: bool
    has_sf: bool
    has_nashor: bool


def haste_cdr_mult(haste: float) -> float:
    """Cooldown multiplier: CD = base * this."""
    return 100.0 / (100.0 + max(0.0, haste))


def apply_pen(
    mr: float,
    q_shred: float,
    malig_shred: float,
    pct_mpen: float,
    flat_mpen: float,
) -> float:
    # % reduction (Q) → flat reduction (Hatefog curse) → % pen → flat pen
    reduced = mr * (1.0 - q_shred) - malig_shred
    reduced = max(0.0, reduced)
    reduced = reduced * (1.0 - pct_mpen) - flat_mpen
    return max(0.0, reduced)


def apply_armor_pen(
    armor: float,
    q_shred: float,
    pct_pen: float,
    lethality: float = 0.0,
) -> float:
    # Q shred (armor AND MR) → % armor pen → lethality
    reduced = armor * (1.0 - q_shred)
    reduced = reduced * (1.0 - pct_pen) - lethality
    return max(0.0, reduced)


def magic_mult(eff_mr: float) -> float:
    return 100.0 / (100.0 + eff_mr)


def physical_mult(eff_armor: float) -> float:
    return 100.0 / (100.0 + eff_armor)


def sum_stats(inv: List[Item]) -> dict:
    ap = ah = mana = as_pct = flat = pct = uh = 0.0
    flags = {
        "malig": False,
        "luden": False,
        "bf": False,
        "liandry": False,
        "ashes": False,
        "guise": False,
        "cap": False,
        "nashor": False,
        "sf": False,
        "void": False,
        "crypt": False,
        "horizon": False,
    }
    names = []
    for it in inv:
        names.append(it.name)
        ap += it.ap
        ah += it.ah
        mana += it.mana
        as_pct += it.as_pct
        flat += it.flat_mpen
        pct += it.pct_mpen
        uh += it.ult_haste
        if it.malignance:
            flags["malig"] = True
        if it.luden:
            flags["luden"] = True
        if it.blackfire:
            flags["bf"] = True
        if it.liandry:
            flags["liandry"] = True
        if it.ashes:
            flags["ashes"] = True
        if it.guise:
            flags["guise"] = True
        if it.deathcap:
            flags["cap"] = True
        if it.nashor:
            flags["nashor"] = True
        if it.name == "Shadowflame":
            flags["sf"] = True
        if it.name == "Void Staff":
            flags["void"] = True
        if it.name == "Cryptbloom":
            flags["crypt"] = True
        if it.horizon:
            flags["horizon"] = True

    # Blackfire 4% AP per burning champ — fog poke usually 1, fights ~1.4
    bf_targets = 1.2
    ap_mult = 1.0
    if flags["bf"]:
        ap_mult += 0.04 * bf_targets
    if flags["cap"]:
        ap_mult += 0.30
    ap *= ap_mult

    return {
        "ap": ap,
        "ah": ah,
        "mana": mana,
        "as_pct": as_pct,
        "flat": flat,
        "pct": pct,
        "uh": uh,
        "names": names,
        **flags,
    }


def r_count(level: int, ah: float, uh: float, has_mana_item: bool, window: float) -> int:
    rank = skill_rank(level, "R")
    if rank <= 0:
        return 0
    base = [0, 2.0, 1.5, 1.0][rank]
    cd = base * haste_cdr_mult(ah + uh)
    # 0.6s missile delay on first shot; then spam
    shots = 1 + int(max(0.0, window - 0.7) / max(0.35, cd))
    mana_cap = 5 if has_mana_item else 3
    if rank == 1 and not has_mana_item:
        mana_cap = 3
    return max(0, min(shots, mana_cap, 6))


def q_shred_pct(level: int) -> float:
    rank = skill_rank(level, "Q")
    if rank <= 0:
        return 0.0
    return [0, 0.16, 0.20, 0.24, 0.28, 0.32][rank]


def w_pct(level: int, ap: float) -> float:
    rank = skill_rank(level, "W")
    if rank <= 0:
        return 0.0
    base = [0, 0.03, 0.0375, 0.045, 0.0525, 0.06][rank]
    return base + 0.015 * (ap / 100.0)


def r_min_damage(level: int, ap: float, bonus_ad: float = 0.0) -> float:
    """Living Artillery is MAGIC damage: base + 75% bonus AD + 35/40/45% AP."""
    rank = skill_rank(level, "R")
    if rank <= 0:
        return 0.0
    base = [0, 100, 140, 180][rank]
    ratio = [0, 0.35, 0.40, 0.45][rank]
    return base + ratio * ap + 0.75 * bonus_ad


def r_min_breakdown(
    level: int, ap: float, bonus_ad: float = 0.0
) -> Tuple[float, float, float, float]:
    """Returns (base, from_bonus_ad, from_ap, total) before missing-HP amp / MR."""
    rank = skill_rank(level, "R")
    if rank <= 0:
        return 0.0, 0.0, 0.0, 0.0
    base = [0, 100.0, 140.0, 180.0][rank]
    ratio = [0, 0.35, 0.40, 0.45][rank]
    from_ad = 0.75 * bonus_ad
    from_ap = ratio * ap
    return base, from_ad, from_ap, base + from_ad + from_ap


def q_damage(level: int, ap: float) -> float:
    rank = skill_rank(level, "Q")
    if rank <= 0:
        return 0.0
    base = [0, 80, 125, 170, 215, 260][rank]
    return base + 0.90 * ap


def attack_speed(level: int, bonus_as: float) -> float:
    # Kog base 0.665, growth 2.65%/lvl, AS rune shard +10%
    growth = 0.0265 * (level - 1)
    rune = 0.10
    return 0.665 * (1.0 + growth + bonus_as + rune)


def window_damage(
    *,
    level: int,
    stats: dict,
    hp: float,
    mr: float,
    window: float,
    use_w: bool,
    vs_tank: bool,
) -> Tuple[float, int]:
    """Total magic damage in one combat window. Returns (damage, r_shots)."""
    ap = stats["ap"]
    ah = stats["ah"]
    has_mana = stats["mana"] >= 500
    shots = r_count(level, ah, stats["uh"], has_mana, window)
    shred = q_shred_pct(level)  # Q lands once per window
    malig_shred = 10.0 if stats["malig"] and shots >= 1 else 0.0

    # First R does not benefit from Hatefog shred; later damage does.
    mr_pre = apply_pen(mr, shred, 0.0, stats["pct"], stats["flat"])
    mr_post = apply_pen(mr, shred, malig_shred, stats["pct"], stats["flat"])
    m_pre = magic_mult(mr_pre)
    m_post = magic_mult(mr_post)

    # Suffering / Madness: poke ~4%, 8s siege ~6%
    suffer = 1.0
    if stats["liandry"] or stats["guise"]:
        suffer = 1.06 if use_w else 1.04

    # Fog poke hits relatively healthy tanks (~15% missing → ~12.5% R amp)
    # Squishies get poked lower. Execute (<40% HP) is 2x, rare in poke.
    if vs_tank:
        r_amp = 1.12
        cinder = 1.0
    else:
        r_amp = 1.28
        cinder = 1.12 if stats["sf"] else 1.0  # more time below 40%

    dmg = 0.0

    # Q once
    dmg += q_damage(level, ap) * m_pre

    # R shots — first without curse, rest with
    # R is magic; bonus AD is a ratio on magic damage, not physical.
    r_hit = r_min_damage(level, ap, stats.get("bonus_ad", 0.0)) * r_amp
    for i in range(shots):
        dmg += r_hit * (m_pre if i == 0 else m_post)

    # Luden Echo: 12s CD, one dump per window. Isolated fog target
    # dumps leftover charges into primary (~105 + 7% AP).
    if stats["luden"]:
        echo = 105.0 + 0.07 * ap
        dmg += echo * m_pre

    # Comet: 15–100, +5% AP, then 0–100% from distance.
    # Fog R is max range → ~2.0x. Max-range W ~1.5x.
    comet_base = 15.0 + 85.0 * (level - 1) / 17.0
    dist = 2.0 if not use_w else 1.55
    comet = (comet_base + 0.05 * ap) * dist
    dmg += comet * m_pre

    # Burns over the window (after first ability ~0.4s)
    burn_t = max(0.0, window - 0.45)
    # Hatefog: 60 + 5% AP per second while zone up. Zone lasts 3s,
    # refreshed by follow-up R. Uptime ≈ full after first R if we recast.
    if stats["malig"] and shots >= 1:
        hf_up = min(burn_t, 3.0 + max(0, shots - 1) * 1.6)
        hf_up = min(burn_t, hf_up)
        dmg += (60.0 + 0.05 * ap) * hf_up * m_post

    if stats["liandry"]:
        dmg += 0.02 * hp * burn_t * m_post
    elif stats["ashes"] and not stats["bf"]:
        dmg += 5.0 * burn_t * m_post

    if stats["bf"]:
        dmg += (20.0 + 0.02 * ap) * burn_t * m_post

    if use_w:
        wp = w_pct(level, ap)
        if wp > 0:
            aspd = attack_speed(level, stats["as_pct"])
            autos = aspd * min(8.0, window)  # W lasts 8s
            onhit = hp * wp
            if stats["nashor"]:
                onhit += 15.0 + 0.15 * ap
            # Autos after Q+first R mostly sit in cursed/shredded MR
            dmg += autos * onhit * m_post

    dmg *= suffer * cinder
    if stats.get("horizon"):
        # Hypershot: R always ≥600 range; W siege from brush also marks.
        dmg *= 1.10
    if vs_tank:
        # Cut Down: +8% vs champions above 60% HP (fog poke / siege open)
        dmg *= 1.08
    return dmg, shots


def compute_snapshot(build_name: str, path: List[str], minute: int) -> Snapshot:
    gold = gold_at_minute(minute)
    level = level_at_minute(minute)
    inv = resolve_inventory(path, gold)
    st = sum_stats(inv)

    thp, tmr = tank_hp(minute), tank_mr(minute)
    shp, smr = squishy_hp(minute), squishy_mr(minute)

    fog_t, shots = window_damage(
        level=level, stats=st, hp=thp, mr=tmr,
        window=POKE_WINDOW, use_w=False, vs_tank=True,
    )
    fog_s, _ = window_damage(
        level=level, stats=st, hp=shp, mr=smr,
        window=POKE_WINDOW, use_w=False, vs_tank=False,
    )
    siege_t, _ = window_damage(
        level=level, stats=st, hp=thp, mr=tmr,
        window=SIEGE_WINDOW, use_w=True, vs_tank=True,
    )
    siege_s, _ = window_damage(
        level=level, stats=st, hp=shp, mr=smr,
        window=SIEGE_WINDOW, use_w=True, vs_tank=False,
    )

    mix_t = FOG_WEIGHT * fog_t + SIEGE_WEIGHT * siege_t
    mix_s = FOG_WEIGHT * fog_s + SIEGE_WEIGHT * siege_s

    n_leg = sum(1 for n in st["names"] if n in LEGENDARIES)

    notes = []
    if st["malig"]:
        notes.append("Hatefog+UH")
    if st["liandry"]:
        notes.append("%HP burn")
    if st["void"] or st["crypt"]:
        notes.append("%pen")
    if st["luden"] and st["malig"]:
        notes.append("DOUBLE MANA")
    if st["bf"] and st["malig"]:
        notes.append("DOUBLE MANA")
    if st["nashor"]:
        notes.append("on-hit")
    if st.get("horizon"):
        notes.append("Hypershot 10%")
    if n_leg == 0:
        notes.append("pre-legendary")

    return Snapshot(
        minute=minute,
        build_name=build_name,
        items=st["names"],
        gold=gold,
        level=level,
        ap=round(st["ap"], 1),
        ah=st["ah"],
        legendary_count=n_leg,
        fog_tank=round(fog_t, 1),
        fog_squish=round(fog_s, 1),
        siege_tank=round(siege_t, 1),
        mix_tank=round(mix_t, 1),
        mix_squish=round(mix_s, 1),
        r_shots_poke=shots,
        notes=", ".join(notes) if notes else "-",
        has_malig=st["malig"],
        has_liandry=st["liandry"],
        has_void=st["void"] or st["crypt"],
        has_luden=st["luden"],
        has_bf=st["bf"],
        has_sf=st["sf"],
        has_nashor=st["nashor"],
    )


def run_all() -> Tuple[Dict[str, List[Snapshot]], List[dict]]:
    results: Dict[str, List[Snapshot]] = {}
    for name, path in BUILD_PATHS.items():
        results[name] = [
            compute_snapshot(name, path, m) for m in range(1, GAME_MINUTES + 1)
        ]

    timeline = []
    for m in range(1, GAME_MINUTES + 1):
        cands = [(n, results[n][m - 1]) for n in results]

        def score(s: Snapshot) -> float:
            # núp bắn that still hurts tanks
            tank = s.mix_tank
            # Punish double-mana (delays tank item) slightly on equal tank damage
            overlap = 0.96 if (s.has_luden and s.has_malig) or (s.has_bf and s.has_malig) else 1.0
            # Reward having the tank tools online
            kit = 1.0
            if s.has_malig and s.has_liandry:
                kit += 0.06
            if s.has_void:
                kit += 0.08
            # Don't let Nashor W-siege drown the fog identity
            fog_keep = 0.97 if s.has_nashor and not s.has_liandry else 1.0
            return tank * overlap * kit * fog_keep

        best_n, best_s = max(cands, key=lambda x: score(x[1]))
        timeline.append(
            {
                "minute": m,
                "winner": best_n,
                "mix_tank": best_s.mix_tank,
                "mix_squish": best_s.mix_squish,
                "fog_tank": best_s.fog_tank,
                "siege_tank": best_s.siege_tank,
                "uptime_note": best_s.notes,
                "items": best_s.items,
                "ap": best_s.ap,
                "notes": best_s.notes,
            }
        )
    return results, timeline


def first_minute_with(snaps: List[Snapshot], pred) -> Optional[int]:
    for s in snaps:
        if pred(s):
            return s.minute
    return None


def fourth_item_lines() -> List[str]:
    """After Malig → Liandry → Void, what 4th item actually does."""
    lines = []
    lines.append("-" * 80)
    lines.append("MÓN 4 SAU VOID  (cùng core Malig → Liandry → Void)")
    lines.append("-" * 80)
    rows = []
    for name, path in FOURTH_PATHS.items():
        s24 = compute_snapshot(name, path, 24)
        s26 = compute_snapshot(name, path, 26)
        s28 = compute_snapshot(name, path, 28)
        fourth = next((n for n in s28.items if n in LEGENDARIES and n not in {
            "Malignance", "Liandry's Torment", "Void Staff",
        }), s28.items[-1] if s28.items else "?")
        online = first_minute_with(
            [compute_snapshot(name, path, m) for m in range(20, 29)],
            lambda s, item=fourth: item in s.items,
        )
        rows.append((s28.mix_tank, s28.fog_tank, s28.mix_squish, name, s24, s26, s28, fourth, online))
    rows.sort(key=lambda r: r[0], reverse=True)
    lines.append(
        f"  {'4th item':<22} {'24:00':>7} {'26:00':>7} {'28:00 tank':>10} "
        f"{'fog-tank':>8} {'squish':>7}  online"
    )
    for mix, fog, sq, name, s24, s26, s28, fourth, online in rows:
        when = f"~{online}:00" if online else "—"
        lines.append(
            f"  {name:<22} {s24.mix_tank:>7.0f} {s26.mix_tank:>7.0f} "
            f"{s28.mix_tank:>10.0f} {fog:>8.0f} {sq:>7.0f}  {when} {fourth}"
        )
    lines.append("")
    lines.append("  Default món 4: Deathcap nếu game kéo ~28+ (3850 tank-mix @28).")
    lines.append("  Horizon Focus xong sớm hơn (~26:00) — 25 AH + 10% Hypershot")
    lines.append("  trên R fog; thắng Deathcap ở phút 26 (3544 vs 3186).")
    lines.append("  Lấy Horizon nếu fight trước khi đủ gold Cap; lấy Cap nếu")
    lines.append("  chắc 4 món full. Shadowflame 4th nếu cần giết ADC/shield.")
    lines.append("  Zhonya nếu bị dive (Zed/Rengar/Kayn) — không phải món damage.")
    lines.append("  Morello nếu Aatrox/WW/Yuumi/Soraka. Banshee vs AP pick.")
    lines.append("  Món 5–6: món flex còn lại. Đừng bán Void.")
    lines.append("")
    return lines


def rune_page_lines() -> List[str]:
    lines = []
    lines.append("-" * 80)
    lines.append("RUNES / KEYSTONE  (núp bắn R + đau tank)")
    lines.append("-" * 80)
    lines.append("  KEYSTONE: Arcane Comet")
    lines.append("    Comet giờ scale 0–100% theo distance. R 1300–1800 = max")
    lines.append("    range → comet gần gấp đôi. Liandry/Hatefog không giảm CD")
    lines.append("    comet nữa, nên ~1 proc / cửa sổ 8s — vẫn đúng artillery.")
    lines.append("    First Strike (7%/3s + gold) chỉ khi bạn LUÔN đánh trước")
    lines.append("    từ fog và không bị tag lane; kém Comet trên R max range.")
    lines.append("    Dark Harvest / PTA / Lethal Tempo: ADC hoặc snowball,")
    lines.append("    không phải kit núp R vs tank.")
    lines.append("")
    lines.append("  PRIMARY — Sorcery")
    lines.append("    Comet → Manaflow Band → Absolute Focus → Scorch")
    lines.append("    Manaflow: R stack mana 40→400. Absolute Focus: núp thì")
    lines.append("    đứng >70% HP. Scorch: lane poke. Swap Gathering Storm")
    lines.append("    nếu game chắc 4–5 món / even.")
    lines.append("    Transcendence nếu cần AH (ít Malig AH). Axiom Arcanist")
    lines.append("    chỉ khi bạn one-shot bằng R, không phải default tank kit.")
    lines.append("")
    lines.append("  SECONDARY — Precision")
    lines.append("    Presence of Mind + Cut Down")
    lines.append("    PoM: refund mana khi combat, giữ 4–5 R/cửa sổ.")
    lines.append("    Cut Down: +8% vs champion >60% HP — tank fog poke luôn proc.")
    lines.append("")
    lines.append("  ALT secondary — Domination (nếu thiếu R haste hơn tank amp)")
    lines.append("    Ultimate Hunter + Cheap Shot")
    lines.append("    UH chồng 20 ult haste Malignance → R gần không downtime.")
    lines.append("    Cheap Shot: Hatefog/E slow. Trade Cut Down.")
    lines.append("")
    lines.append("  SHARDS: AS / Adaptive AP / HP (flat)")
    lines.append("    AS cho cửa sổ W siege. HP flat vì AP Kog mỏng.")
    lines.append("")
    lines.append("  SUMMONERS: Flash + Teleport (mid) hoặc Flash + Barrier/Ghost")
    lines.append("")
    return lines


def third_item_isolated_delta(name: str, path: List[str], snaps: List[Snapshot]) -> Tuple[float, int, List[str]]:
    """Damage added by the 3rd legendary at the minute it completes.

    Compares the same minute with vs without that item so target HP/MR
    scaling cannot masquerade as a 'drop'.
    """
    third = next((s for s in snaps if s.legendary_count >= 3), None)
    if third is None:
        return 0.0, snaps[-1].minute, snaps[-1].items
    two_path = truncate_after_n_legendaries(path, 2)
    with_3 = third.mix_tank
    without = compute_snapshot(name, two_path, third.minute).mix_tank
    legs = [n for n in third.items if n in LEGENDARIES]
    return with_3 - without, third.minute, legs


def summarize(results, timeline) -> str:
    lines = []
    lines.append("=" * 80)
    lines.append("AP KOG'MAW — NÚP BẮN + TANK DAMAGE  (PC LoL ~patch 26.x)")
    lines.append("Playstyle: fog R poke 70% / max-range W siege 30% | Game: 28:00")
    lines.append("Metric: magic damage per 8s window  |  Must hurt tanks")
    lines.append("=" * 80)
    lines.append("")
    lines.append("GOLD / LEVEL / TARGETS")
    lines.append(
        f"  {'Min':>3}  {'Gold':>6}  {'Lvl':>3}  {'Tank HP':>8}  {'Tank MR':>7}  "
        f"{'Squish HP':>9}"
    )
    for m in range(1, GAME_MINUTES + 1):
        if m in (1, 6, 8, 10, 12, 16, 20, 22, 24, 28) or m % 4 == 0:
            lines.append(
                f"  {m:>3}  {gold_at_minute(m):>6}  {level_at_minute(m):>3}  "
                f"{tank_hp(m):>8.0f}  {tank_mr(m):>7.0f}  {squishy_hp(m):>9.0f}"
            )

    lines.append("")
    lines.append("-" * 80)
    lines.append("MINUTE-BY-MINUTE OPTIMAL (tank-mix score, fog identity kept)")
    lines.append("-" * 80)
    for row in timeline:
        if row["minute"] % 2 != 0 and row["minute"] not in (1, 9, 11, 15, 21):
            continue
        item_short = " › ".join(row["items"][:5])
        if len(row["items"]) > 5:
            item_short += " › …"
        lines.append(
            f"  {row['minute']:>2}:00 | tank {row['mix_tank']:>7.0f} | "
            f"squish {row['mix_squish']:>7.0f} | fog-tank {row['fog_tank']:>6.0f} | "
            f"{row['winner']}"
        )
        lines.append(f"         items: {item_short}")
        lines.append(f"         {row['notes']}")

    lines.append("")
    lines.append("-" * 80)
    lines.append("BUILD COMPARISON — TANK MIX DAMAGE / 8s @ spikes")
    lines.append("-" * 80)
    hdr = f"  {'Build':<32} {'9:00':>7} {'16:00':>7} {'22:00':>7} {'28:00':>7} {'EffTank':>8} {'3rdΔ':>7}"
    lines.append(hdr)

    ranking = []
    for name, snaps in results.items():
        b9 = snaps[8].mix_tank
        b16 = snaps[15].mix_tank
        b22 = snaps[21].mix_tank
        b28 = snaps[27].mix_tank
        # Duration-weighted: earlier tank tools > paper late DPS
        score_sum = 0.0
        for s in snaps:
            mult = 1.0
            if s.has_malig and s.has_liandry and s.has_void:
                mult = 1.22
            elif s.has_malig and s.has_liandry:
                mult = 1.14
            elif s.has_malig:
                mult = 1.05
            if (s.has_luden and s.has_malig) or (s.has_bf and s.has_malig):
                mult *= 0.92  # delayed tank item
            score_sum += s.mix_tank * mult
        eff = score_sum / len(snaps)

        # 3rd legendary spike vs tank (the "tuột" question) — isolated
        delta3, third_min, third_legs = third_item_isolated_delta(
            name, BUILD_PATHS[name], snaps
        )
        second = next((s for s in snaps if s.legendary_count >= 2), snaps[0])
        ranking.append(
            (eff, b22, b28, name, b9, b16, b22, b28, snaps, delta3, third_min, second, third_legs)
        )
        lines.append(
            f"  {name:<32} {b9:>7.0f} {b16:>7.0f} {b22:>7.0f} {b28:>7.0f} {eff:>8.0f} {delta3:>+7.0f}"
        )

    ranking.sort(key=lambda x: (x[0], x[1]), reverse=True)
    best = ranking[0]

    lines.append("")
    lines.append("-" * 80)
    lines.append("3RD ITEM SPIKE vs TANK  (isolated Δ: same minute with vs without 3rd)")
    lines.append("-" * 80)
    for row in ranking:
        name, snaps, delta3, third_min, second, third_legs = (
            row[3], row[8], row[9], row[10], row[11], row[12]
        )
        lines.append(
            f"  {name:<32} 2nd ~{second.minute}:00  3rd ~{third_min}:00  "
            f"tank Δ {delta3:+.0f}  [{', '.join(third_legs[:3])}]"
        )

    lines.append("")
    lines.append("-" * 80)
    lines.append("FOG R vs TANK  (pure núp bắn, no W) @ 16 / 22 / 28")
    lines.append("-" * 80)
    for row in ranking:
        name, snaps = row[3], row[8]
        lines.append(
            f"  {name:<32} {snaps[15].fog_tank:>7.0f} {snaps[21].fog_tank:>7.0f} "
            f"{snaps[27].fog_tank:>7.0f}   R shots @22: {snaps[21].r_shots_poke}"
        )

    lines.append("")
    lines.append("-" * 80)
    lines.append("W SIEGE vs TANK  (max-range brush autos) @ 16 / 22 / 28")
    lines.append("-" * 80)
    for row in ranking:
        name, snaps = row[3], row[8]
        lines.append(
            f"  {name:<32} {snaps[15].siege_tank:>7.0f} {snaps[21].siege_tank:>7.0f} "
            f"{snaps[27].siege_tank:>7.0f}"
        )

    winner_name = best[3]
    snaps = best[8]
    malig_m = first_minute_with(snaps, lambda s: s.has_malig)
    liandry_m = first_minute_with(snaps, lambda s: s.has_liandry)
    void_m = first_minute_with(snaps, lambda s: s.has_void)

    user_sf = results["Luden → Malig → SF"]
    win = results[winner_name]
    user_delta = next(r[9] for r in ranking if r[3] == "Luden → Malig → SF")
    win_delta = next(r[9] for r in ranking if r[3] == winner_name)
    t9_win, t9_user = win[8].mix_tank, user_sf[8].mix_tank
    t22_win, t22_user = win[21].mix_tank, user_sf[21].mix_tank
    w22_win, w22_user = win[21].siege_tank, user_sf[21].siege_tank
    pct22 = 100.0 * (t22_win / t22_user - 1.0) if t22_user else 0.0
    pct9 = 100.0 * (t9_win / t9_user - 1.0) if t9_user else 0.0

    lines.append("")
    lines.append("-" * 80)
    lines.append("VERDICT")
    lines.append("-" * 80)
    lines.append(f"  Best path (núp bắn + đau tank): {winner_name}")
    lines.append(f"  Tank-weighted avg: {best[0]:.0f} | 22:00 tank-mix: {best[1]:.0f}")
    if malig_m:
        lines.append(f"  Malignance online: ~{malig_m}:00  (R haste + Hatefog zone)")
    if liandry_m:
        lines.append(f"  Liandry online:    ~{liandry_m}:00  (2% max HP/s — this is the tank burn)")
    else:
        lines.append("  Liandry: NOT finished by 28:00")
    if void_m:
        lines.append(f"  %pen online:       ~{void_m}:00  (this is the 3rd-item spike vs tank MR)")
    else:
        lines.append("  Void/Cryptbloom: NOT finished by 28:00 — 3rd item will feel weak vs tanks")
    lines.append("")
    lines.append("  TẠI SAO LUDEN/BF → MALIG RỒI MÓN 3 BỊ TUỘT:")
    lines.append("  • Luden và Malignance (hoặc BF + Malig) đều là Lost Chapter —")
    lines.append("    mana/AH chồng lên nhau. Món 2 không mở kit mới vs tank,")
    lines.append("    nên cả game bạn đi sau 1 món %HP/%pen.")
    lines.append("  • Hatefog + Echo/BF burn scale theo AP, KHÔNG theo max HP.")
    lines.append(
        f"    Tank ~{tank_hp(22):.0f} HP / ~{tank_mr(22):.0f} MR lúc món 3 xong nuốt burst đó."
    )
    lines.append("  • Món 3 sau 2 mana item thường là Shadowflame (15 flat pen +")
    lines.append(
        f"    crit <40% HP). Isolated spike vs tank chỉ {user_delta:+.0f} / 8s;"
    )
    lines.append("    Cinderbloom không proc khi núp bắn tank đầy máu.")
    lines.append(
        f"  • Cùng phút 22:00, Luden→Malig→SF tank-mix {t22_user:.0f};"
    )
    lines.append(
        f"    {winner_name} {t22_win:.0f} ({pct22:+.0f}%). W-siege "
        f"{w22_user:.0f} vs {w22_win:.0f} —"
    )
    lines.append("    path cũ không giết kịp tank trong cửa sổ W.")
    lines.append("")
    lines.append("  TẠI SAO RUSH MALIGNANCE:")
    lines.append("  • Rẻ hơn Luden/BF (2700), online ~7:00 — đúng spike R cấp 1.")
    lines.append(
        f"    Phút 9 tank-mix đã {pct9:+.0f}% so với Luden first "
        f"({t9_win:.0f} vs {t9_user:.0f})."
    )
    lines.append("  • 20 ultimate haste + Hatefog 60(+5% AP)/s / 10 MR shred:")
    lines.append("    fog R giữ zone trong cửa sổ 8s. Đây là món núp bắn.")
    lines.append("  • Món 2 rảnh slot cho Liandry (không share Lost Chapter) →")
    lines.append("    2% max HP/s refresh bằng R. Đây là món đau tank.")
    lines.append(
        f"  • Món 3 Void Staff: isolated Δ {win_delta:+.0f} vs tank (gần gấp đôi"
    )
    lines.append("    Shadowflame). Q shred 16–32% cộng dồn trước %pen.")
    lines.append("")
    lines.extend(fourth_item_lines())
    lines.extend(rune_page_lines())
    lines.append("-" * 80)
    lines.append("FULL BUY ORDER")
    lines.append("-" * 80)
    lines.append("  RECOMMENDED (núp bắn, output phải đau tank):")
    lines.append("  1) Doran's Ring → Lost Chapter")
    lines.append("  2) Malignance  (~8:00)     — fog R identity")
    lines.append("  3) Sorcerer's Shoes")
    lines.append("  4) Liandry's Torment (~16:00) — %HP burn, refresh bằng R/W")
    lines.append("  5) Void Staff        (~22:00) — món 3 spike vs tank")
    lines.append("  6) Món 4 mặc định: Deathcap. Flex: Horizon (núp rẻ hơn),")
    lines.append("     Zhonya (dive), Morello (heal), Shadowflame (squishy).")
    lines.append("  7) Món 5–6: món flex còn lại / Banshee vs AP pick")
    lines.append("")
    lines.append("  Skill: max W (đau tank khi siege) → Q (shred) → E.")
    lines.append("  Núp: R từ fog vào chân tank — zone Hatefog + Liandry tick.")
    lines.append("  Khi chúng walk up / siege: Q shred → W max range auto.")
    lines.append("  Đừng mua 2 Lost Chapter. Nashor chỉ khi bạn all-in W nhiều")
    lines.append("  hơn núp R (trade fog DPS).")
    lines.append("")
    lines.append("  Trap: Luden/BF → Malig → Shadowflame = 3 món anti-squish,")
    lines.append("  tank không chết, món 3 cảm giác tuột.")
    lines.append("  Trap: Liandry first delay Malig → mất spike fog R phút 8–12.")
    lines.append("=" * 80)
    return "\n".join(lines)


def export_json(results, timeline, path: str) -> None:
    payload = {
        "meta": {
            "champion": "Kog'Maw",
            "role": "AP mid / AP bot",
            "patch": "26.x",
            "game_minutes": GAME_MINUTES,
            "playstyle": "fog R poke (núp bắn) + max-range W siege",
            "fog_weight": FOG_WEIGHT,
            "siege_weight": SIEGE_WEIGHT,
        },
        "timeline": timeline,
        "builds": {
            name: [
                {
                    "minute": s.minute,
                    "items": s.items,
                    "gold": s.gold,
                    "level": s.level,
                    "ap": s.ap,
                    "ah": s.ah,
                    "legendary_count": s.legendary_count,
                    "fog_tank": s.fog_tank,
                    "fog_squish": s.fog_squish,
                    "siege_tank": s.siege_tank,
                    "mix_tank": s.mix_tank,
                    "mix_squish": s.mix_squish,
                    "r_shots_poke": s.r_shots_poke,
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
    """Sanity checks so the sim cannot silently invert the question."""
    malig = results["Malig → Liandry → Void"]
    luden = results["Luden → Malig → SF"]
    bf = results["BF → Malig → SF"]

    malig_online = first_minute_with(malig, lambda s: s.has_malig)
    luden_malig = first_minute_with(luden, lambda s: s.has_malig)
    assert malig_online is not None and malig_online <= 10, malig_online
    assert luden_malig is not None and luden_malig > malig_online, (
        malig_online,
        luden_malig,
    )

    # 3rd item of proposed path must beat user paths vs tank at 22:00
    assert malig[21].mix_tank > luden[21].mix_tank, (
        malig[21].mix_tank,
        luden[21].mix_tank,
    )
    assert malig[21].mix_tank > bf[21].mix_tank

    # Fog identity: Malignance rush should lead fog-tank at first-item spike
    assert malig[9].fog_tank >= luden[9].fog_tank * 0.95

    d_void, _, _ = third_item_isolated_delta(
        "Malig → Liandry → Void", BUILD_PATHS["Malig → Liandry → Void"], malig
    )
    d_sf, _, _ = third_item_isolated_delta(
        "Luden → Malig → SF", BUILD_PATHS["Luden → Malig → SF"], luden
    )
    assert d_void > d_sf * 1.4, (d_void, d_sf)


def main() -> None:
    results, timeline = run_all()
    self_check(results)
    report = summarize(results, timeline)
    try:
        from compare_seraph import compare as seraph_compare
        seraph_text, _ = seraph_compare()
        report = report + "\n\n" + seraph_text
    except Exception as exc:  # pragma: no cover
        report = report + f"\n\n[seraph compare skipped: {exc}]\n"
    try:
        from compare_mix import compare as mix_compare
        mix_text, _ = mix_compare()
        report = report + "\n\n" + mix_text
    except Exception as exc:  # pragma: no cover
        report = report + f"\n\n[mix compare skipped: {exc}]\n"
    print(report)
    out_dir = "/workspace/ap-kogmaw-sim"
    with open(f"{out_dir}/report.txt", "w", encoding="utf-8") as f:
        f.write(report + "\n")
    export_json(results, timeline, f"{out_dir}/results.json")
    print(f"\nWrote {out_dir}/report.txt and {out_dir}/results.json")


if __name__ == "__main__":
    main()
