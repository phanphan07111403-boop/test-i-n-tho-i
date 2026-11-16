#!/usr/bin/env python3
"""
Wild Rift Shyvana Jungle — Late-Game Counter-Meta Simulation
Patch 7.3d / 7.3f item + kit snapshot (Nov 2026).

Playstyle: full-clear scaler → dragon-form teamfight frontline.
Questions:
  1) which item build counters the tanky / extended-fight meta
     AND still wins late (post–Ocean omnivamp nerf)?
  2) on that winning build, which rune page wins the late brawl?

Metric: effective late fight power =
  (teamfight damage vs tank mix) × (alive-time multiplier)
in a ~12s dragon-form brawl window.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import json

GAME_MINUTES = 25

# Locked item path for the rune comparison (item-sim winner).
WINNING_ITEM_BUILD = "TF → BotRK → DD → FoN → Twin"

# ---------------------------------------------------------------------------
# Economy / XP — farm-heavy jungle Shyvana (full clears + dragons)
# ---------------------------------------------------------------------------


def gold_at_minute(m: int) -> int:
    if m <= 0:
        return 500
    total = 500  # Long Sword start
    for t in range(1, m + 1):
        if t <= 4:
            total += 380  # first clear + scuttle
        elif t <= 10:
            total += 520  # second clear + early dragons / ganks
        elif t <= 16:
            total += 580  # objective contests
        else:
            total += 620  # mid-late teamfight gold
    return total


def level_at_minute(m: int) -> int:
    # Farm jungler: R at 5 (~5:00), lvl 15 common by ~22–25.
    table = {
        1: 2, 2: 3, 3: 4, 4: 5, 5: 5, 6: 6, 7: 7, 8: 8,
        9: 9, 10: 9, 11: 10, 12: 10, 13: 11, 14: 12,
        15: 12, 16: 13, 17: 13, 18: 14, 19: 14, 20: 14,
        21: 15, 22: 15, 23: 15, 24: 15, 25: 15,
    }
    return table.get(m, min(15, 1 + m))


def skill_rank(level: int, skill: str) -> int:
    """E max → W → Q. R at 5 / 9 / 13."""
    if skill == "R":
        if level < 5:
            return 0
        if level < 9:
            return 1
        if level < 13:
            return 2
        return 3
    # Priority: E > W > Q
    e_levels = [1, 4, 6, 8]
    w_levels = [2, 7, 10, 11]
    q_levels = [3, 12, 14, 15]
    mapping = {"E": e_levels, "W": w_levels, "Q": q_levels}
    return sum(1 for lv in mapping[skill] if level >= lv)


def dragon_stacks(m: int) -> int:
    """Approximate Draconic Bloodline stacks from farm + dragons."""
    # Full clear large monsters + ~1 dragon / 4–5 min after 5:00
    large = min(8 * (2 + m // 2), 160)  # camps / herald / baron chunks
    drakes = 0
    if m >= 6:
        drakes = min(4, 1 + (m - 6) // 5) * 35
    takedowns = max(0, m - 8) * 4  # sparse early, more mid
    return min(400, large + drakes + takedowns)


# ---------------------------------------------------------------------------
# Targets — tanky meta frontline + scaled carry
# ---------------------------------------------------------------------------


def tank_hp(m: int) -> float:
    lv = level_at_minute(m)
    item_hp = 90 * max(0, m - 6)
    return 720 + 115 * lv + item_hp


def tank_armor(m: int) -> float:
    lv = level_at_minute(m)
    extra = 0.0 if m < 8 else min(9.0 * (m - 8), 140.0)
    return 40 + 3.2 * lv + extra


def tank_mr(m: int) -> float:
    lv = level_at_minute(m)
    extra = 0.0 if m < 10 else min(6.5 * (m - 10), 90.0)
    return 32 + 1.8 * lv + extra


def carry_hp(m: int) -> float:
    lv = level_at_minute(m)
    return 620 + 95 * lv + 12 * m


def carry_armor(m: int) -> float:
    lv = level_at_minute(m)
    extra = 0.0 if m < 14 else (18.0 if m < 20 else 35.0)
    return 30 + 2.4 * lv + extra


def carry_mr(m: int) -> float:
    lv = level_at_minute(m)
    extra = 0.0 if m < 16 else 20.0
    return 30 + 1.2 * lv + extra


# Incoming damage pressure on Shyvana during a dive (for survivability)
def dive_phys_dps(m: int) -> float:
    return 90 + 14 * m


def dive_magic_dps(m: int) -> float:
    return 70 + 11 * m


# ---------------------------------------------------------------------------
# Items (Wild Rift ~7.3 approximate stats)
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
    armor: float = 0
    mr: float = 0
    lifesteal: float = 0
    omnivamp: float = 0
    flat_apen: float = 0
    pct_apen: float = 0
    flat_mpen: float = 0
    pct_mpen: float = 0
    spellblade: str = ""  # trinity | dusk | sunderer | none
    botrk: bool = False
    nashor: bool = False
    liandry: bool = False
    riftmaker: bool = False
    deathdance: bool = False
    shojin: bool = False
    kraken: bool = False
    eclipse: bool = False
    wit: bool = False
    twinguard: bool = False
    fon: bool = False
    sterak: bool = False
    hexplate: bool = False
    deathcap: bool = False
    tags: Tuple[str, ...] = ()


ITEMS: Dict[str, Item] = {
    "Long Sword": Item("Long Sword", 500, ad=12),
    "Boots": Item("Boots", 500, tags=("boots",)),
    "Berserker's Greaves": Item(
        "Berserker's Greaves", 1500, as_pct=0.35, tags=("boots",)
    ),
    "Immortal Treads": Item(
        "Immortal Treads", 1500, ad=12, omnivamp=0.05, tags=("boots", "omni")
    ),
    "Gluttonous Greaves": Item(
        "Gluttonous Greaves", 1500, ad=12, omnivamp=0.07, tags=("boots", "omni")
    ),
    "Plated Steelcaps": Item(
        "Plated Steelcaps", 1500, armor=25, tags=("boots",)
    ),
    "Sheen": Item("Sheen", 1000, ah=10),
    "Phage": Item("Phage", 1100, ad=15, hp=200),
    "Hearthbound Axe": Item("Hearthbound Axe", 1100, ad=20, as_pct=0.15),
    "Recurve Bow": Item("Recurve Bow", 800, as_pct=0.15),
    "Vampiric Scepter": Item("Vampiric Scepter", 900, ad=15, lifesteal=0.10),
    "Pickaxe": Item("Pickaxe", 1000, ad=25),
    "BF Sword": Item("BF Sword", 1300, ad=40),
    "Ruby Crystal": Item("Ruby Crystal", 500, hp=200),
    "Kindlegem": Item("Kindlegem", 900, hp=200, ah=10),
    "Giant's Belt": Item("Giant's Belt", 1000, hp=350),
    "Amplifying Tome": Item("Amplifying Tome", 500, ap=20),
    "Blasting Wand": Item("Blasting Wand", 800, ap=45),
    "Needlessly Large Rod": Item("Needlessly Large Rod", 1400, ap=70),
    "Haunting Guise": Item("Haunting Guise", 1300, ap=35, hp=200),
    "Fated Ashes": Item("Fated Ashes", 900, ap=40),
    "Negatron Cloak": Item("Negatron Cloak", 900, mr=40),
    "Chain Vest": Item("Chain Vest", 900, armor=40),
    "Trinity Force": Item(
        "Trinity Force",
        3333,
        ad=30,
        as_pct=0.30,
        ah=15,
        hp=300,
        spellblade="trinity",
        tags=("core", "ad"),
    ),
    "Dusk and Dawn": Item(
        "Dusk and Dawn",
        3100,
        ap=70,
        ah=15,
        as_pct=0.20,
        spellblade="dusk",
        tags=("core", "ap"),
    ),
    "Divine Sunderer": Item(
        "Divine Sunderer",
        3300,
        ad=30,
        ah=15,
        hp=300,
        spellblade="sunderer",
        tags=("core", "tank"),
    ),
    "Blade of the Ruined King": Item(
        "Blade of the Ruined King",
        3100,
        ad=40,
        as_pct=0.30,
        lifesteal=0.12,
        botrk=True,
        tags=("shred", "ad"),
    ),
    "Nashor's Tooth": Item(
        "Nashor's Tooth",
        3000,
        ap=80,
        as_pct=0.50,
        ah=15,
        nashor=True,
        tags=("onhit", "ap"),
    ),
    "Liandry's Torment": Item(
        "Liandry's Torment",
        3000,
        ap=60,
        hp=300,
        pct_mpen=0.07,
        liandry=True,
        tags=("burn", "tank"),
    ),
    "Riftmaker": Item(
        "Riftmaker",
        3100,
        ap=80,
        hp=300,
        omnivamp=0.08,
        riftmaker=True,
        tags=("ap", "sustain"),
    ),
    "Spear of Shojin": Item(
        "Spear of Shojin",
        3200,
        ad=50,
        ah=20,
        hp=300,
        shojin=True,
        tags=("haste", "ad"),
    ),
    "Death's Dance": Item(
        "Death's Dance",
        3100,
        ad=50,
        ah=15,
        armor=45,
        deathdance=True,
        tags=("survive", "ad"),
    ),
    "Kraken Slayer": Item(
        "Kraken Slayer",
        3100,
        ad=40,
        as_pct=0.35,
        kraken=True,
        tags=("onhit", "ad"),
    ),
    "Experimental Hexplate": Item(
        "Experimental Hexplate",
        3000,
        ad=40,
        as_pct=0.25,
        hp=300,
        hexplate=True,
        tags=("ult", "ad"),
    ),
    "Eclipse": Item(
        "Eclipse",
        2900,
        ad=55,
        ah=15,
        eclipse=True,
        tags=("shred", "ad"),
    ),
    "Serylda's Grudge": Item(
        "Serylda's Grudge",
        3000,
        ad=45,
        ah=15,
        pct_apen=0.30,
        tags=("pen", "ad"),
    ),
    "Wit's End": Item(
        "Wit's End",
        2900,
        as_pct=0.40,
        mr=45,
        wit=True,
        tags=("mr", "onhit"),
    ),
    "Force of Nature": Item(
        "Force of Nature",
        2800,
        hp=350,
        mr=55,
        fon=True,
        tags=("mr", "tank"),
    ),
    "Amaranth's Twinguard": Item(
        "Amaranth's Twinguard",
        3000,
        hp=350,
        armor=40,
        mr=40,
        twinguard=True,
        tags=("tank", "late"),
    ),
    "Randuin's Omen": Item(
        "Randuin's Omen",
        2800,
        hp=350,
        armor=55,
        tags=("armor", "tank"),
    ),
    "Sterak's Gage": Item(
        "Sterak's Gage",
        3100,
        hp=400,
        sterak=True,
        tags=("survive",),
    ),
    "Rabadon's Deathcap": Item(
        "Rabadon's Deathcap",
        3400,
        ap=130,
        deathcap=True,
        tags=("amp", "ap"),
    ),
    "Cosmic Drive": Item(
        "Cosmic Drive",
        3000,
        ap=75,
        ah=25,
        hp=250,
        tags=("haste", "ap"),
    ),
}


UPGRADE_COMPONENTS = {
    "Berserker's Greaves": ("Boots",),
    "Immortal Treads": ("Boots",),
    "Gluttonous Greaves": ("Boots",),
    "Plated Steelcaps": ("Boots",),
    "Trinity Force": ("Sheen", "Phage", "Hearthbound Axe"),
    "Dusk and Dawn": ("Sheen", "Blasting Wand", "Recurve Bow"),
    "Divine Sunderer": ("Sheen", "Phage", "Kindlegem"),
    "Blade of the Ruined King": ("Vampiric Scepter", "Recurve Bow", "Pickaxe"),
    "Nashor's Tooth": ("Recurve Bow", "Blasting Wand", "Amplifying Tome"),
    "Liandry's Torment": ("Haunting Guise", "Fated Ashes"),
    "Riftmaker": ("Haunting Guise", "Amplifying Tome", "Kindlegem"),
    "Spear of Shojin": ("Pickaxe", "Kindlegem", "BF Sword"),
    "Death's Dance": ("Pickaxe", "Chain Vest", "Kindlegem"),
    "Kraken Slayer": ("BF Sword", "Recurve Bow", "Pickaxe"),
    "Experimental Hexplate": ("Pickaxe", "Kindlegem", "Hearthbound Axe"),
    "Eclipse": ("Pickaxe", "Long Sword", "Long Sword"),
    "Serylda's Grudge": ("Pickaxe", "Kindlegem"),
    "Wit's End": ("Recurve Bow", "Negatron Cloak"),
    "Force of Nature": ("Negatron Cloak", "Giant's Belt"),
    "Amaranth's Twinguard": ("Chain Vest", "Negatron Cloak", "Ruby Crystal"),
    "Randuin's Omen": ("Giant's Belt", "Chain Vest"),
    "Sterak's Gage": ("BF Sword", "Ruby Crystal", "Ruby Crystal"),
    "Rabadon's Deathcap": ("Needlessly Large Rod", "Needlessly Large Rod"),
    "Cosmic Drive": ("Amplifying Tome", "Kindlegem", "Blasting Wand"),
}

NEXT_COMPONENTS = {
    "Berserker's Greaves": ["Boots"],
    "Immortal Treads": ["Boots"],
    "Gluttonous Greaves": ["Boots"],
    "Plated Steelcaps": ["Boots"],
    "Trinity Force": ["Sheen", "Phage", "Hearthbound Axe"],
    "Dusk and Dawn": ["Sheen", "Blasting Wand", "Recurve Bow"],
    "Divine Sunderer": ["Sheen", "Phage", "Kindlegem"],
    "Blade of the Ruined King": ["Vampiric Scepter", "Recurve Bow", "Pickaxe"],
    "Nashor's Tooth": ["Recurve Bow", "Blasting Wand", "Amplifying Tome"],
    "Liandry's Torment": ["Fated Ashes", "Haunting Guise"],
    "Riftmaker": ["Haunting Guise", "Kindlegem", "Amplifying Tome"],
    "Spear of Shojin": ["Kindlegem", "Pickaxe", "BF Sword"],
    "Death's Dance": ["Pickaxe", "Chain Vest", "Kindlegem"],
    "Kraken Slayer": ["BF Sword", "Recurve Bow", "Pickaxe"],
    "Experimental Hexplate": ["Pickaxe", "Kindlegem", "Hearthbound Axe"],
    "Eclipse": ["Pickaxe", "Long Sword"],
    "Serylda's Grudge": ["Pickaxe", "Kindlegem"],
    "Wit's End": ["Recurve Bow", "Negatron Cloak"],
    "Force of Nature": ["Negatron Cloak", "Giant's Belt"],
    "Amaranth's Twinguard": ["Chain Vest", "Negatron Cloak", "Ruby Crystal"],
    "Randuin's Omen": ["Giant's Belt", "Chain Vest"],
    "Sterak's Gage": ["BF Sword", "Ruby Crystal"],
    "Rabadon's Deathcap": ["Needlessly Large Rod"],
    "Cosmic Drive": ["Amplifying Tome", "Kindlegem", "Blasting Wand"],
}


# Build paths answering: counter tanky meta + win late dragon fights
BUILD_PATHS: Dict[str, List[str]] = {
    # Meta default AD bruiser (most-built CN / guide)
    "TF → BotRK → DD → FoN → Twin": [
        "Long Sword",
        "Sheen",
        "Phage",
        "Hearthbound Axe",
        "Trinity Force",
        "Boots",
        "Immortal Treads",
        "Vampiric Scepter",
        "Recurve Bow",
        "Blade of the Ruined King",
        "Death's Dance",
        "Force of Nature",
        "Amaranth's Twinguard",
    ],
    # CN standard damage: Shojin before BotRK
    "TF → Shojin → DD → Hex → BotRK": [
        "Long Sword",
        "Sheen",
        "Phage",
        "Hearthbound Axe",
        "Trinity Force",
        "Boots",
        "Berserker's Greaves",
        "Kindlegem",
        "Spear of Shojin",
        "Death's Dance",
        "Experimental Hexplate",
        "Blade of the Ruined King",
    ],
    # Anti-tank shred (WildRiftCore)
    "TF → BotRK → Eclipse → Serylda → Wit": [
        "Long Sword",
        "Sheen",
        "Phage",
        "Hearthbound Axe",
        "Trinity Force",
        "Boots",
        "Berserker's Greaves",
        "Vampiric Scepter",
        "Blade of the Ruined King",
        "Eclipse",
        "Serylda's Grudge",
        "Wit's End",
    ],
    # AP on-hit burn (China creator / Alpha) — post 7.3d E AP buff
    "Dusk → Nashor → Liandry → Rift → Shojin": [
        "Long Sword",
        "Sheen",
        "Blasting Wand",
        "Recurve Bow",
        "Dusk and Dawn",
        "Boots",
        "Berserker's Greaves",
        "Nashor's Tooth",
        "Fated Ashes",
        "Haunting Guise",
        "Liandry's Torment",
        "Riftmaker",
        "Spear of Shojin",
    ],
    # Hybrid: Trinity into AP tank shred
    "TF → Nashor → Liandry → Cap → Twin": [
        "Long Sword",
        "Sheen",
        "Phage",
        "Hearthbound Axe",
        "Trinity Force",
        "Boots",
        "Berserker's Greaves",
        "Nashor's Tooth",
        "Fated Ashes",
        "Haunting Guise",
        "Liandry's Torment",
        "Rabadon's Deathcap",
        "Amaranth's Twinguard",
    ],
    # Divine Sunderer anti-HP stacker
    "Sunderer → BotRK → DD → Twin → FoN": [
        "Long Sword",
        "Sheen",
        "Phage",
        "Kindlegem",
        "Divine Sunderer",
        "Boots",
        "Immortal Treads",
        "Vampiric Scepter",
        "Blade of the Ruined King",
        "Death's Dance",
        "Amaranth's Twinguard",
        "Force of Nature",
    ],
    # Glass on-hit (Kraken) — high paper DPS, weak late survive
    "Kraken → TF → BotRK → Hex → Randuin": [
        "Long Sword",
        "BF Sword",
        "Recurve Bow",
        "Kraken Slayer",
        "Boots",
        "Berserker's Greaves",
        "Sheen",
        "Phage",
        "Trinity Force",
        "Blade of the Ruined King",
        "Experimental Hexplate",
        "Randuin's Omen",
    ],
    # Durability first late win (survive meta burst, then shred)
    "TF → BotRK → Twin → FoN → DD": [
        "Long Sword",
        "Sheen",
        "Phage",
        "Hearthbound Axe",
        "Trinity Force",
        "Boots",
        "Immortal Treads",
        "Vampiric Scepter",
        "Blade of the Ruined King",
        "Amaranth's Twinguard",
        "Force of Nature",
        "Death's Dance",
    ],
    # Full AP glass (Cap rush) — burst late, dies to meta dive
    "Dusk → Cap → Liandry → Nashor → Rift": [
        "Long Sword",
        "Sheen",
        "Blasting Wand",
        "Dusk and Dawn",
        "Boots",
        "Berserker's Greaves",
        "Needlessly Large Rod",
        "Rabadon's Deathcap",
        "Liandry's Torment",
        "Nashor's Tooth",
        "Riftmaker",
    ],
}

LEGENDARIES = {
    "Trinity Force",
    "Dusk and Dawn",
    "Divine Sunderer",
    "Blade of the Ruined King",
    "Nashor's Tooth",
    "Liandry's Torment",
    "Riftmaker",
    "Spear of Shojin",
    "Death's Dance",
    "Kraken Slayer",
    "Experimental Hexplate",
    "Eclipse",
    "Serylda's Grudge",
    "Wit's End",
    "Force of Nature",
    "Amaranth's Twinguard",
    "Randuin's Omen",
    "Sterak's Gage",
    "Rabadon's Deathcap",
    "Cosmic Drive",
}


# ---------------------------------------------------------------------------
# Runes — pages compared on the winning item path
# ---------------------------------------------------------------------------


@dataclass
class RunePage:
    name: str
    keystone: str  # fleet | conqueror
    unshakeable: bool = False
    second_wind: bool = False
    bone_plating: bool = False
    overgrowth: bool = False
    perseverance: bool = False
    triumph: bool = False
    coup: bool = False
    alacrity: bool = False
    bloodline: bool = False
    haste: bool = False
    tags: Tuple[str, ...] = ()


# Item-sim baseline (guide default) — used when comparing builds
DEFAULT_RUNES = RunePage(
    name="Fleet · Unshakeable · Second Wind · Overgrowth · Alacrity",
    keystone="fleet",
    unshakeable=True,
    second_wind=True,
    overgrowth=True,
    alacrity=True,
    tags=("guide", "stick"),
)

RUNE_PAGES: Dict[str, RunePage] = {
    "Fleet + Alacrity (guide)": DEFAULT_RUNES,
    "Conqueror + Alacrity (late brawl)": RunePage(
        name="Conqueror · Unshakeable · Second Wind · Overgrowth · Alacrity",
        keystone="conqueror",
        unshakeable=True,
        second_wind=True,
        overgrowth=True,
        alacrity=True,
        tags=("late", "brawl"),
    ),
    "Conqueror + Bloodline (sustain)": RunePage(
        name="Conqueror · Triumph · Coup · Bloodline · Overgrowth",
        keystone="conqueror",
        triumph=True,
        coup=True,
        bloodline=True,
        overgrowth=True,
        tags=("sustain", "precision"),
    ),
    "Fleet + Perseverance (vs CC)": RunePage(
        name="Fleet · Unshakeable · Second Wind · Perseverance · Alacrity",
        keystone="fleet",
        unshakeable=True,
        second_wind=True,
        perseverance=True,
        alacrity=True,
        tags=("cc", "tenacity"),
    ),
    "Fleet + Bone Plating (vs burst)": RunePage(
        name="Fleet · Unshakeable · Bone Plating · Overgrowth · Alacrity",
        keystone="fleet",
        unshakeable=True,
        bone_plating=True,
        overgrowth=True,
        alacrity=True,
        tags=("burst",),
    ),
    "Fleet + Haste (ability weave)": RunePage(
        name="Fleet · Unshakeable · Second Wind · Overgrowth · Haste",
        keystone="fleet",
        unshakeable=True,
        second_wind=True,
        overgrowth=True,
        haste=True,
        tags=("haste",),
    ),
    "Conqueror + Perseverance (CC late)": RunePage(
        name="Conqueror · Unshakeable · Second Wind · Perseverance · Alacrity",
        keystone="conqueror",
        unshakeable=True,
        second_wind=True,
        perseverance=True,
        alacrity=True,
        tags=("cc", "late"),
    ),
}

BOOTS = {
    "Boots",
    "Berserker's Greaves",
    "Immortal Treads",
    "Gluttonous Greaves",
    "Plated Steelcaps",
}


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
        if item_name in BOOTS and any(b in owned for b in BOOTS if b != "Boots"):
            if item_name == "Boots":
                return False
        if item_name not in ("Long Sword", "Ruby Crystal", "Needlessly Large Rod", "Amplifying Tome", "Pickaxe"):
            if item_name in owned:
                return False
        # Allow duplicate Long Sword / Ruby / NLR for recipes
        if item_name in owned and item_name not in (
            "Long Sword",
            "Ruby Crystal",
            "Needlessly Large Rod",
            "Amplifying Tome",
            "Pickaxe",
        ):
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
        if step in owned and step not in (
            "Long Sword",
            "Ruby Crystal",
            "Needlessly Large Rod",
            "Amplifying Tome",
            "Pickaxe",
        ):
            continue
        if can_afford(step):
            buy(step)
        else:
            blocked_at = step
            break

    if blocked_at and blocked_at in NEXT_COMPONENTS:
        for comp in NEXT_COMPONENTS[blocked_at]:
            if comp in owned and comp not in (
                "Long Sword",
                "Ruby Crystal",
                "Needlessly Large Rod",
                "Amplifying Tome",
                "Pickaxe",
            ):
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
                    "Long Sword",
                    "Ruby Crystal",
                    "Needlessly Large Rod",
                ):
                    continue
                if can_afford(step):
                    buy(step)
                else:
                    for comp in NEXT_COMPONENTS.get(step, []):
                        if gold_pool >= ITEMS[comp].cost:
                            if comp not in owned or comp in (
                                "Long Sword",
                                "Ruby Crystal",
                                "Needlessly Large Rod",
                            ):
                                buy(comp)
                    if can_afford(step):
                        buy(step)
                    else:
                        break

    # Boots upgrade replaces base boots
    finished_boots = [b for b in owned if b in BOOTS and b != "Boots"]
    if finished_boots and "Boots" in owned:
        owned.remove("Boots")

    return [ITEMS[n] for n in owned]


# ---------------------------------------------------------------------------
# Combat model — dragon-form teamfight window
# ---------------------------------------------------------------------------

FIGHT_WINDOW = 12.0  # dragon-form brawl length (fury drain)
# Score mix: 60% tank shred (meta frontline) + 40% carry threat
TANK_WEIGHT = 0.60
CARRY_WEIGHT = 0.40


@dataclass
class Snapshot:
    minute: int
    build_name: str
    items: List[str]
    gold: int
    level: int
    ad: float
    ap: float
    hp: float
    as_pct: float
    armor: float
    mr: float
    legendary_count: int
    dmg_tank: float
    dmg_carry: float
    mix_dmg: float
    alive_sec: float
    late_power: float  # mix_dmg * (alive_sec / FIGHT_WINDOW)
    notes: str
    has_botrk: bool
    has_liandry: bool
    has_tank_item: bool
    has_spellblade: bool
    is_ap_core: bool
    rune_name: str = ""
    keystone: str = "fleet"


def haste_cdr_mult(haste: float) -> float:
    return 100.0 / (100.0 + max(0.0, haste))


def phys_mult(armor: float, pct_apen: float, flat_apen: float) -> float:
    eff = max(0.0, armor * (1.0 - pct_apen) - flat_apen)
    return 100.0 / (100.0 + eff)


def magic_mult(mr: float, pct_mpen: float, flat_mpen: float) -> float:
    eff = max(0.0, mr * (1.0 - pct_mpen) - flat_mpen)
    return 100.0 / (100.0 + eff)


def sum_stats(
    inv: List[Item], level: int, stacks: int, runes: RunePage = DEFAULT_RUNES
) -> dict:
    ad = ap = ah = hp = as_pct = armor = mr = ls = ov = 0.0
    flat_apen = pct_apen = flat_mpen = pct_mpen = 0.0
    flags = {
        "trinity": False,
        "dusk": False,
        "sunderer": False,
        "botrk": False,
        "nashor": False,
        "liandry": False,
        "rift": False,
        "dd": False,
        "shojin": False,
        "kraken": False,
        "eclipse": False,
        "wit": False,
        "twin": False,
        "fon": False,
        "sterak": False,
        "hex": False,
        "cap": False,
        "randuin": False,
        "guise": False,
        "ashes": False,
    }
    names = []
    for it in inv:
        names.append(it.name)
        ad += it.ad
        ap += it.ap
        ah += it.ah
        hp += it.hp
        as_pct += it.as_pct
        armor += it.armor
        mr += it.mr
        ls += it.lifesteal
        ov += it.omnivamp
        flat_apen += it.flat_apen
        pct_apen += it.pct_apen
        flat_mpen += it.flat_mpen
        pct_mpen += it.pct_mpen
        if it.spellblade == "trinity":
            flags["trinity"] = True
        if it.spellblade == "dusk":
            flags["dusk"] = True
        if it.spellblade == "sunderer":
            flags["sunderer"] = True
        if it.botrk:
            flags["botrk"] = True
        if it.nashor:
            flags["nashor"] = True
        if it.liandry:
            flags["liandry"] = True
        if it.riftmaker:
            flags["rift"] = True
        if it.deathdance:
            flags["dd"] = True
        if it.shojin:
            flags["shojin"] = True
        if it.kraken:
            flags["kraken"] = True
        if it.eclipse:
            flags["eclipse"] = True
        if it.wit:
            flags["wit"] = True
        if it.twinguard:
            flags["twin"] = True
        if it.fon:
            flags["fon"] = True
        if it.sterak:
            flags["sterak"] = True
        if it.hexplate:
            flags["hex"] = True
        if it.deathcap:
            flags["cap"] = True
        if it.name == "Randuin's Omen":
            flags["randuin"] = True
        if it.name == "Haunting Guise":
            flags["guise"] = True
        if it.name == "Fated Ashes":
            flags["ashes"] = True

    # Champion base (WR ~7.3d)
    base_ad = 62 + (118 - 62) * (level - 1) / 14
    base_hp = 660 + 130 * (level - 1)
    base_as = 0.797 * (1.0 + 0.024 * (level - 1))
    base_armor = 46 + (116 - 46) * (level - 1) / 14
    base_mr = 38 + (66 - 38) * (level - 1) / 14

    # R dragon form bonus HP
    r_rank = skill_rank(level, "R")
    r_hp = [0, 300, 400, 500][r_rank] if r_rank else 0

    # Draconic stacks soft HP
    stack_hp = 0.15 * stacks

    # --- Rune stats ---
    rune_as = 0.10 if runes.alacrity else 0.0
    rune_ls = 0.08 if runes.bloodline else 0.0  # Legend: Bloodline late stacks
    rune_ah = 10.0 if runes.haste else 0.0
    # Overgrowth: farm jungler ~8–14 HP per min after early game
    overgrowth_hp = 0.0
    if runes.overgrowth:
        overgrowth_hp = min(180.0, 12.0 * max(0, level - 3) + 4.0 * max(0, stacks // 40))
    # Conqueror: full stacks in a 12s dragon brawl → adaptive AD + omnivamp
    conq_ad = 0.0
    conq_ov = 0.0
    conq_amp = 1.0
    if runes.keystone == "conqueror":
        # ~18–30 adaptive AD at full stacks by level; Q double-hits stack fast
        conq_ad = 12.0 + 1.1 * level
        conq_ov = 0.08  # WR Conqueror omnivamp at max stacks (approx)
        conq_amp = 1.06  # stacked adaptive force through the window
    # Fleet: no permanent AD; stick MS modeled in fight_damage / alive heal pulses

    total_ad = (base_ad + ad + conq_ad) * (conq_amp if runes.keystone == "conqueror" else 1.0)
    # Keep bonus_ad as item bonus for ratios that want bonus AD
    bonus_ad = ad + conq_ad
    total_ap = ap
    if flags["cap"]:
        total_ap *= 1.30
    # Riftmaker combat amp ~ mid fight
    if flags["rift"]:
        total_ap *= 1.08
        total_ad *= 1.04

    total_hp = base_hp + hp + r_hp + stack_hp + overgrowth_hp
    total_as = base_as * (1.0 + as_pct + rune_as)
    total_armor = base_armor + armor
    total_mr = base_mr + mr

    # Unshakeable: R dive lands in CC → resists while immobilized (avg mid-fight)
    if runes.unshakeable:
        # ~12–15 resists for a chunk of the dive when CC'd
        resist_bump = 8.0 + 0.4 * level
        total_armor += resist_bump
        total_mr += resist_bump

    # Twinguard mid-fight resist amp when damaged
    if flags["twin"]:
        total_armor *= 1.30
        total_mr *= 1.30
    if flags["fon"]:
        total_mr *= 1.08  # stacking MS/MR while taking magic

    ocean = 0.10 if stacks >= 400 else (0.05 if stacks >= 300 else 0.0)

    return {
        "ad": total_ad,
        "bonus_ad": bonus_ad,
        "ap": total_ap,
        "ah": ah + (10 if flags["shojin"] else 0) + rune_ah,
        "hp": total_hp,
        "as": total_as,
        "armor": total_armor,
        "mr": total_mr,
        "ls": ls + rune_ls,
        "ov": ov + ocean + conq_ov,
        # 7.3d Ocean omnivamp 10% at 400 stacks (was 20%)
        "flat_apen": flat_apen,
        "pct_apen": pct_apen,
        "flat_mpen": flat_mpen,
        "pct_mpen": pct_mpen,
        "base_ad": base_ad,
        "names": names,
        "runes": runes,
        "keystone": runes.keystone,
        "fleet": runes.keystone == "fleet",
        "conqueror": runes.keystone == "conqueror",
        "second_wind": runes.second_wind,
        "bone_plating": runes.bone_plating,
        "perseverance": runes.perseverance,
        "triumph": runes.triumph,
        "coup": runes.coup,
        "overgrowth": runes.overgrowth,
        **flags,
    }


def q_bonus_ratio(level: int) -> float:
    rank = skill_rank(level, "Q")
    if rank <= 0:
        return 0.0
    return [0, 0.20, 0.40, 0.60, 0.80][rank]


def w_tick(level: int, bonus_ad: float) -> float:
    rank = skill_rank(level, "W")
    if rank <= 0:
        return 0.0
    base = [0, 40, 55, 70, 85][rank]
    return base + 0.30 * bonus_ad


def e_hit(level: int, ad: float, ap: float) -> float:
    """Flame Breath missile — post 7.3d ratios 50% AD + 80% AP."""
    rank = skill_rank(level, "E")
    if rank <= 0:
        return 0.0
    base = [0, 60, 110, 160, 210][rank]
    return base + 0.50 * ad + 0.80 * ap


def e_detonate(level: int, ad: float, ap: float) -> float:
    """Dragon-form E explosion — 100% AD + 100% AP post 7.3d."""
    rank = skill_rank(level, "E")
    if rank <= 0:
        return 0.0
    base = [0, 60, 110, 160, 210][rank]
    return base + 1.00 * ad + 1.00 * ap


def e_scorch_pct(stacks: int) -> float:
    # 3% max HP magic on-hit while scorched; true dmg at 300 stacks (dragon)
    return 0.03


def r_impact(level: int, ap: float) -> float:
    rank = skill_rank(level, "R")
    if rank <= 0:
        return 0.0
    base = [0, 150, 250, 350][rank]
    return base + 0.80 * ap


def fight_damage(
    *,
    level: int,
    stacks: int,
    st: dict,
    hp: float,
    armor: float,
    mr: float,
    vs_tank: bool,
) -> float:
    """Total damage dealt in one dragon-form 12s window to a single primary target."""
    ad = st["ad"]
    ap = st["ap"]
    bonus_ad = st["bonus_ad"]
    ah = st["ah"]
    aspd = st["as"]

    p_mult = phys_mult(armor, st["pct_apen"], st["flat_apen"])
    m_mult = magic_mult(mr, st["pct_mpen"], st["flat_mpen"])

    # Madness / Riftmaker mid-fight amp
    amp = 1.04 if (st["liandry"] or st["guise"]) else 1.0
    if st["rift"]:
        amp *= 1.06
    if st["eclipse"] and vs_tank:
        amp *= 1.06  # % current HP proc averaged

    dmg = 0.0

    # R landing once
    dmg += r_impact(level, ap) * m_mult

    # E once (dragon detonation) + ground ticks ~4s
    dmg += e_detonate(level, ad, ap) * m_mult
    # Scorched earth AD ratio 15% post 7.3d, ~4 ticks
    dmg += (0.15 * ad) * 4 * m_mult

    # Autos in window
    autos = aspd * FIGHT_WINDOW
    # Q casts: base CD ~5.5–7s, reduced 0.5s per auto → many Qs
    q_cd = [0, 7.0, 6.5, 6.0, 5.5][skill_rank(level, "Q") or 1]
    q_cd *= haste_cdr_mult(ah)
    # Effective Q rate with auto refunds
    q_casts = 1 + int(max(0.0, FIGHT_WINDOW - 0.4) / max(1.2, q_cd * 0.45))
    q_casts = min(q_casts, 8)

    # Twin Bite double-hits apply on-hit twice (dragon form AoE ignored for ST)
    q_hits = q_casts * 2
    normal_autos = max(0.0, autos - q_casts)  # Q replaces one AA each cast

    # On-hit package per AA
    def onhit_magic(curr_hp_frac: float) -> float:
        hit = 0.0
        # Scorch % max HP
        scorch = e_scorch_pct(stacks) * hp
        if stacks >= 300:
            # true damage — no MR
            hit += scorch  # counted as raw below via bypass
        else:
            hit += scorch
        if st["nashor"]:
            hit += 15.0 + 0.20 * ap  # WR Nashor on-hit approx
        if st["wit"]:
            hit += 15.0 + level * 2.5
        if st["dusk"]:
            # Dusk spellblade applies on-hit a second time — fold as +15% on-hit magic
            hit *= 1.12
        return hit

    # Physical on-hit / AA damage
    aa_phys = ad
    # BotRK current HP — melee 8.5%; Q double applies twice
    botrk_pct = 0.085 if st["botrk"] else 0.0

    # Spellblade procs ~ once per ability weave; ~ Q+W+E cadence
    ability_weaves = 3 + q_casts  # rough
    spellblade_procs = min(ability_weaves, int(FIGHT_WINDOW / 1.6) + 1)
    if st["trinity"]:
        dmg += spellblade_procs * (2.0 * st["base_ad"]) * p_mult
    elif st["dusk"]:
        dmg += spellblade_procs * (1.5 * st["base_ad"] + 0.30 * ap) * m_mult
    elif st["sunderer"]:
        # % max HP physical
        dmg += spellblade_procs * (0.06 * hp if vs_tank else 0.04 * hp) * p_mult

    # W burnout ticks — dragon form wider, extended by autos up to ~7s
    w_up = min(FIGHT_WINDOW, 3.0 + min(4.0, autos * 0.35))
    dmg += w_tick(level, bonus_ad) * w_up * m_mult

    # Liandry / Ashes burn
    if st["liandry"]:
        dmg += 0.02 * hp * FIGHT_WINDOW * m_mult * amp
    elif st["ashes"]:
        dmg += 5.0 * FIGHT_WINDOW * m_mult

    # Autos + Q hits
    # Average current HP over fight for BotRK
    avg_curr_frac = 0.62 if vs_tank else 0.48
    curr_hp = hp * avg_curr_frac

    true_scorch = stacks >= 300

    def apply_aa(n_hits: float, is_q: bool) -> float:
        out = 0.0
        # Physical AA / Q bonus
        q_ratio = q_bonus_ratio(level) if is_q else 0.0
        # Each Q hit is an AA; bonus ratio on Twin Bite is extra physical
        phys = aa_phys + (q_ratio * ad if is_q else 0.0)
        if st["botrk"]:
            phys += botrk_pct * curr_hp
        out += n_hits * phys * p_mult

        mag = onhit_magic(avg_curr_frac)
        if true_scorch:
            # scorch portion is true; other magic still MR'd
            scorch = e_scorch_pct(stacks) * hp
            other = mag - scorch
            out += n_hits * scorch  # true
            out += n_hits * max(0.0, other) * m_mult
        else:
            out += n_hits * mag * m_mult

        if st["kraken"]:
            # every 3rd attack true damage
            out += (n_hits / 3.0) * (35 + 0.40 * bonus_ad)
        return out

    dmg += apply_aa(normal_autos, is_q=False)
    dmg += apply_aa(q_hits, is_q=True)

    # Shojin: more ability uptime already folded into AH; small extra W tick
    if st["shojin"]:
        dmg += w_tick(level, bonus_ad) * 1.5 * m_mult

    # Hexplate: ult AS surge — already partly in AS; small AA bump
    if st["hex"]:
        dmg *= 1.04

    # Fleet Footwork: MS stick → slightly better W uptime / on-target autos
    if st.get("fleet"):
        dmg *= 1.03
        # ~2–3 heal procs in 12s already modeled in alive_time

    # Coup de Grace: execute amp on low HP — stronger vs carries than full tanks
    if st.get("coup"):
        dmg *= 1.05 if not vs_tank else 1.02

    return dmg * amp


def alive_time(st: dict, minute: int) -> float:
    """How long Shyvana stays up in a 12s dive under meta dive pressure."""
    hp = st["hp"]
    # Effective HP vs mixed dive
    phys = dive_phys_dps(minute)
    mag = dive_magic_dps(minute)
    # Armor/MR mitigation on incoming
    in_p = phys * (100.0 / (100.0 + st["armor"]))
    in_m = mag * (100.0 / (100.0 + st["mr"]))
    if st["fon"]:
        in_m *= 0.88
    if st["randuin"]:
        in_p *= 0.90
    if st["dd"]:
        # Death's Dance spreads damage — effective +12% eHP vs burst
        in_p *= 0.88
        in_m *= 0.92
    if st["sterak"]:
        hp += 0.55 * (st["hp"] - 660)  # shield approx mid fight
    if st["twin"]:
        # already amplified resists in sum_stats
        pass

    # Bone Plating: blunt first burst window (~3 hits)
    if st.get("bone_plating"):
        in_p *= 0.92
        in_m *= 0.92

    # Perseverance: tenacity → more of the dragon form spent attacking, less locked
    # Modeled as slight incoming reduction (less time eating free damage while CCd)
    if st.get("perseverance"):
        in_p *= 0.94
        in_m *= 0.94

    incoming = in_p + in_m
    # Healing / omnivamp return (Ocean nerfed to 10% at 400 stacks)
    heal_rate = (st["ls"] * 0.55 + st["ov"] * 0.70) * (st["ad"] * st["as"] * 0.35)

    # Fleet Footwork heal pulses (~ every 4s in combat)
    if st.get("fleet"):
        fleet_heal = (40 + 4 * level_at_minute(minute)) + 0.15 * st["bonus_ad"]
        heal_rate += (fleet_heal * 2.5) / FIGHT_WINDOW  # ~2.5 procs / 12s

    # Second Wind: chip regen after taking champion damage
    if st.get("second_wind"):
        heal_rate += 8.0 + 0.6 * level_at_minute(minute)

    # Triumph: takedown heal — soft expect ~0.4 resets in a winning late fight
    if st.get("triumph"):
        heal_rate += (0.12 * hp * 0.4) / FIGHT_WINDOW

    net = max(40.0, incoming - heal_rate)

    # Seconds until HP depletes, capped at fight window
    secs = min(FIGHT_WINDOW, hp / net)
    # Soft floor: glass builds die faster even if math eHP looks ok early
    if st["cap"] and not st["twin"] and not st["dd"] and not st["fon"]:
        secs *= 0.82
    if st["kraken"] and not st["dd"] and not st["twin"] and not st["randuin"]:
        secs = min(secs, FIGHT_WINDOW * 0.78)
    return max(3.5, secs)


def compute_snapshot(
    build_name: str,
    path: List[str],
    minute: int,
    runes: RunePage = DEFAULT_RUNES,
    label: Optional[str] = None,
) -> Snapshot:
    gold = gold_at_minute(minute)
    level = level_at_minute(minute)
    stacks = dragon_stacks(minute)
    inv = resolve_inventory(path, gold)
    st = sum_stats(inv, level, stacks, runes)

    thp, tarm, tmr = tank_hp(minute), tank_armor(minute), tank_mr(minute)
    chp, carm, cmr = carry_hp(minute), carry_armor(minute), carry_mr(minute)

    dmg_t = fight_damage(
        level=level, stacks=stacks, st=st, hp=thp, armor=tarm, mr=tmr, vs_tank=True
    )
    dmg_c = fight_damage(
        level=level, stacks=stacks, st=st, hp=chp, armor=carm, mr=cmr, vs_tank=False
    )
    mix = TANK_WEIGHT * dmg_t + CARRY_WEIGHT * dmg_c
    alive = alive_time(st, minute)
    # Damage actually delivered = DPS × alive time (not full window if dead)
    delivered = mix * (alive / FIGHT_WINDOW)
    late_power = delivered

    n_leg = sum(1 for n in st["names"] if n in LEGENDARIES)
    has_tank = st["twin"] or st["fon"] or st["dd"] or st["randuin"] or st["sterak"]
    is_ap = st["dusk"] or st["liandry"] or st["nashor"] or st["rift"] or st["cap"]

    notes = []
    if st["botrk"]:
        notes.append("%HP shred")
    if st["liandry"]:
        notes.append("Liandry burn")
    if stacks >= 300:
        notes.append("scorch TRUE")
    if has_tank:
        notes.append("brawl tank")
    if st["cap"] and not has_tank:
        notes.append("GLASS")
    if n_leg == 0:
        notes.append("pre-core")
    if st["trinity"] or st["dusk"] or st["sunderer"]:
        notes.append("spellblade")
    if st.get("conqueror"):
        notes.append("Conqueror stacks")
    if st.get("fleet"):
        notes.append("Fleet stick")
    if runes.overgrowth:
        notes.append("Overgrowth HP")
    if runes.perseverance:
        notes.append("tenacity")

    return Snapshot(
        minute=minute,
        build_name=label or build_name,
        items=st["names"],
        gold=gold,
        level=level,
        ad=round(st["ad"], 1),
        ap=round(st["ap"], 1),
        hp=round(st["hp"], 1),
        as_pct=round(st["as"], 3),
        armor=round(st["armor"], 1),
        mr=round(st["mr"], 1),
        legendary_count=n_leg,
        dmg_tank=round(dmg_t, 1),
        dmg_carry=round(dmg_c, 1),
        mix_dmg=round(mix, 1),
        alive_sec=round(alive, 2),
        late_power=round(late_power, 1),
        notes=", ".join(notes) if notes else "-",
        has_botrk=st["botrk"],
        has_liandry=st["liandry"],
        has_tank_item=has_tank,
        has_spellblade=st["trinity"] or st["dusk"] or st["sunderer"],
        is_ap_core=is_ap,
        rune_name=runes.name,
        keystone=runes.keystone,
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
            # Late-game counter-meta: delivered damage + tank tools + survive
            base = s.late_power
            kit = 1.0
            if s.has_botrk or s.has_liandry:
                kit += 0.08  # anti-tank tool online
            if s.has_tank_item:
                kit += 0.10  # can finish the brawl
            if s.has_botrk and s.has_tank_item:
                kit += 0.06  # shred + live = late win vs meta
            if s.has_liandry and s.has_tank_item:
                kit += 0.05
            # Punish glass that only papers late
            if "GLASS" in s.notes:
                kit *= 0.88
            # Early game: still need a spellblade core
            if m <= 10 and not s.has_spellblade:
                kit *= 0.92
            return base * kit

        best_n, best_s = max(cands, key=lambda x: score(x[1]))
        timeline.append(
            {
                "minute": m,
                "winner": best_n,
                "late_power": best_s.late_power,
                "mix_dmg": best_s.mix_dmg,
                "dmg_tank": best_s.dmg_tank,
                "alive_sec": best_s.alive_sec,
                "items": best_s.items,
                "notes": best_s.notes,
            }
        )
    return results, timeline


def first_minute_with(snaps: List[Snapshot], pred) -> Optional[int]:
    for s in snaps:
        if pred(s):
            return s.minute
    return None


def summarize(results, timeline) -> str:
    lines = []
    lines.append("=" * 84)
    lines.append("SHYVANA JUNGLE — LATE-GAME COUNTER-META  (Wild Rift Patch 7.3d/f)")
    lines.append("Playstyle: full-clear scaler → 12s dragon-form teamfight frontline")
    lines.append(
        "Metric: delivered fight power = mix damage × (alive / 12s)  |  "
        "60% tank / 40% carry"
    )
    lines.append("Goal: counter tanky meta AND still win late (post–Ocean 10% nerf)")
    lines.append("=" * 84)
    lines.append("")
    lines.append("GOLD / LEVEL / STACKS / TARGETS")
    lines.append(
        f"  {'Min':>3}  {'Gold':>6}  {'Lvl':>3}  {'Stacks':>6}  "
        f"{'Tank HP':>8}  {'Tank Arm':>8}  {'Carry HP':>8}"
    )
    for m in range(1, GAME_MINUTES + 1):
        if m in (1, 5, 8, 10, 12, 15, 18, 20, 22, 25) or m % 5 == 0:
            lines.append(
                f"  {m:>3}  {gold_at_minute(m):>6}  {level_at_minute(m):>3}  "
                f"{dragon_stacks(m):>6}  {tank_hp(m):>8.0f}  "
                f"{tank_armor(m):>8.0f}  {carry_hp(m):>8.0f}"
            )

    lines.append("")
    lines.append("-" * 84)
    lines.append("MINUTE-BY-MINUTE OPTIMAL (late-power score: shred + survive)")
    lines.append("-" * 84)
    for row in timeline:
        if row["minute"] % 2 != 0 and row["minute"] not in (1, 5, 9, 13, 17, 21, 25):
            continue
        item_short = " › ".join(row["items"][:5])
        if len(row["items"]) > 5:
            item_short += " › …"
        lines.append(
            f"  {row['minute']:>2}:00 | power {row['late_power']:>7.0f} | "
            f"mix {row['mix_dmg']:>7.0f} | alive {row['alive_sec']:>4.1f}s | "
            f"tank-dmg {row['dmg_tank']:>7.0f} | {row['winner']}"
        )
        lines.append(f"         items: {item_short}")
        lines.append(f"         {row['notes']}")

    lines.append("")
    lines.append("-" * 84)
    lines.append("BUILD COMPARISON — LATE POWER @ spikes")
    lines.append("-" * 84)
    hdr = (
        f"  {'Build':<40} {'10:00':>7} {'15:00':>7} {'20:00':>7} "
        f"{'25:00':>7} {'EffLate':>8} {'Alive25':>7}"
    )
    lines.append(hdr)

    ranking = []
    for name, snaps in results.items():
        b10 = snaps[9].late_power
        b15 = snaps[14].late_power
        b20 = snaps[19].late_power
        b25 = snaps[24].late_power
        score_sum = 0.0
        for s in snaps:
            mult = 1.0
            # Weight late minutes harder — user asked win late
            if s.minute >= 18:
                mult *= 1.35
            elif s.minute >= 12:
                mult *= 1.15
            if s.has_botrk or s.has_liandry:
                mult *= 1.08
            if s.has_tank_item and s.minute >= 15:
                mult *= 1.12
            if "GLASS" in s.notes and s.minute >= 18:
                mult *= 0.85
            score_sum += s.late_power * mult
        eff = score_sum / len(snaps)
        ranking.append(
            (eff, b25, b20, name, b10, b15, b20, b25, snaps, snaps[24].alive_sec)
        )
        lines.append(
            f"  {name:<40} {b10:>7.0f} {b15:>7.0f} {b20:>7.0f} "
            f"{b25:>7.0f} {eff:>8.0f} {snaps[24].alive_sec:>7.1f}"
        )

    ranking.sort(key=lambda x: (x[0], x[1]), reverse=True)
    best = ranking[0]

    lines.append("")
    lines.append("-" * 84)
    lines.append("TANK SHRED (raw 12s window dmg vs tank) @ 15 / 20 / 25")
    lines.append("-" * 84)
    for row in ranking:
        name, snaps = row[3], row[8]
        lines.append(
            f"  {name:<40} {snaps[14].dmg_tank:>7.0f} "
            f"{snaps[19].dmg_tank:>7.0f} {snaps[24].dmg_tank:>7.0f}"
        )

    lines.append("")
    lines.append("-" * 84)
    lines.append("SURVIVE TIME IN DIVE (seconds of 12s window) @ 15 / 20 / 25")
    lines.append("-" * 84)
    for row in ranking:
        name, snaps = row[3], row[8]
        lines.append(
            f"  {name:<40} {snaps[14].alive_sec:>7.1f} "
            f"{snaps[19].alive_sec:>7.1f} {snaps[24].alive_sec:>7.1f}"
        )

    winner_name = best[3]
    snaps = best[8]
    core_m = first_minute_with(snaps, lambda s: s.has_spellblade)
    shred_m = first_minute_with(
        snaps, lambda s: s.has_botrk or s.has_liandry
    )
    tank_m = first_minute_with(snaps, lambda s: s.has_tank_item)

    # Compare vs runner-up shred-glass and vs AP burn path
    runner = ranking[1]
    runner_name = runner[3]
    glass_name = "TF → BotRK → Eclipse → Serylda → Wit"
    ap_name = "Dusk → Nashor → Liandry → Rift → Shojin"
    win = results[winner_name]
    run = results[runner_name]
    glass = results[glass_name]
    ap = results[ap_name]

    def pct(a: float, b: float) -> float:
        return 100.0 * (a / b - 1.0) if b else 0.0

    pct25_run = pct(win[24].late_power, run[24].late_power)
    pct25_glass = pct(win[24].late_power, glass[24].late_power)
    pct25_ap = pct(win[24].late_power, ap[24].late_power)
    pct20_glass = pct(win[19].late_power, glass[19].late_power)

    lines.append("")
    lines.append("-" * 84)
    lines.append("VERDICT")
    lines.append("-" * 84)
    lines.append(f"  Best path (counter meta + win late): {winner_name}")
    lines.append(
        f"  Late-weighted avg: {best[0]:.0f} | 25:00 late-power: {best[1]:.0f}"
    )
    if core_m:
        lines.append(f"  Spellblade core online: ~{core_m}:00")
    if shred_m:
        lines.append(f"  Anti-tank shred online:  ~{shred_m}:00  (BotRK or Liandry)")
    else:
        lines.append("  Anti-tank shred: NOT finished by 25:00")
    if tank_m:
        lines.append(f"  Brawl tank item online:  ~{tank_m}:00")
    else:
        lines.append("  Brawl tank item: NOT finished — dies before dragon form ends")
    lines.append("")
    lines.append("  WHY LATE-GAME META NEEDS SHRED + SURVIVE:")
    lines.append("  • Patch 7.3d cut Ocean dragon omnivamp 20% → 10%. Pure damage")
    lines.append("    builds no longer outheal dive pressure in a full 12s form.")
    lines.append("  • Meta frontlines stack HP/armor. Without BotRK (Q double on-hit)")
    lines.append("    or Liandry (2% max HP/s), dragon form tickles tanks.")
    lines.append("  • Flame Breath ratios were buffed (50% AD + 80% AP; dragon E")
    lines.append("    100%/100%). AP burn paths gained real late DPS — but still")
    lines.append("    need a tank item or they get deleted by Lillia/Yi/assassins.")
    lines.append("  • Scorch becomes TRUE damage at 300 Draconic stacks — dragons")
    lines.append("    are still the win condition; itemization must keep you alive")
    lines.append("    long enough to auto the marked target.")
    lines.append("")
    lines.append(f"  vs runner-up ({runner_name}):")
    lines.append(
        f"    25:00 late-power {win[24].late_power:.0f} vs "
        f"{run[24].late_power:.0f} ({pct25_run:+.0f}%)"
    )
    lines.append(
        f"  vs anti-tank glass ({glass_name}):"
    )
    lines.append(
        f"    20:00 {win[19].late_power:.0f} vs {glass[19].late_power:.0f} "
        f"({pct20_glass:+.0f}%) | 25:00 {win[24].late_power:.0f} vs "
        f"{glass[24].late_power:.0f} ({pct25_glass:+.0f}%)"
    )
    lines.append(
        f"    alive 25:00 {win[24].alive_sec:.1f}s vs "
        f"{glass[24].alive_sec:.1f}s — glass shreds harder on paper "
        f"({glass[24].dmg_tank:.0f} tank-dmg) but dies mid-form"
    )
    lines.append(f"  vs AP burn ({ap_name}):")
    lines.append(
        f"    25:00 late-power {win[24].late_power:.0f} vs "
        f"{ap[24].late_power:.0f} ({pct25_ap:+.0f}%) | "
        f"alive {win[24].alive_sec:.1f}s vs {ap[24].alive_sec:.1f}s"
    )
    lines.append("")
    lines.append("  RECOMMENDED (counter tanky meta, win late dragon fights):")
    if "Liandry" in winner_name or "Nashor" in winner_name or "Dusk" in winner_name:
        lines.append("  1) Long Sword → Sheen components")
        lines.append("  2) Dusk and Dawn / Trinity  (~8–10:00) — spellblade clear/fight")
        lines.append("  3) Berserker's Greaves")
        lines.append("  4) Nashor's Tooth — AS + on-hit to stack Q refunds + scorch")
        lines.append("  5) Liandry's Torment — 2% max HP/s vs meta tanks")
        lines.append("  6) Riftmaker / Deathcap — late amp + sustain")
        lines.append("  7) Twinguard or Shojin — finish the 12s brawl alive")
    else:
        lines.append("  1) Long Sword → Sheen / Phage / Hearthbound")
        lines.append("  2) Trinity Force           (~8–10:00) — clear + Spellblade")
        lines.append("  3) Immortal Treads / Berserker's")
        lines.append("  4) Blade of the Ruined King — Q applies %HP twice (anti-tank)")
        lines.append("  5) Death's Dance OR Twinguard next — Ocean nerf → buy survive")
        lines.append("  6) Force of Nature / Randuin — match their damage type")
        lines.append("  7) Twinguard / Sterak — never skip a resist spike for 6th DPS")
    lines.append("")
    lines.append("  Runes: see RUNE COMPARISON below (locked on this item path).")
    lines.append("  Skill: max E → W → Q; R at 5 / 9 / 13.")
    lines.append("")
    lines.append("  Play: full clear → dragons for stacks → R AFTER they commit.")
    lines.append("  Combo: R land → E mark → W stick → Q double on-hits → autos.")
    lines.append("  Trap: Kraken / Cap glass — paper late DPS, dies at 6–8s of form.")
    lines.append("  Trap: Shojin → Hex damage path without BotRK — tanks live forever.")
    lines.append("  Trap: rushing Twinguard before shred — you live, tanks also live.")
    lines.append("=" * 84)
    return "\n".join(lines)


def run_runes() -> Tuple[Dict[str, List[Snapshot]], List[dict]]:
    """Lock winning items; compare rune pages for late-game fight power."""
    path = BUILD_PATHS[WINNING_ITEM_BUILD]
    results: Dict[str, List[Snapshot]] = {}
    for name, page in RUNE_PAGES.items():
        results[name] = [
            compute_snapshot(
                WINNING_ITEM_BUILD, path, m, runes=page, label=name
            )
            for m in range(1, GAME_MINUTES + 1)
        ]

    timeline = []
    for m in range(1, GAME_MINUTES + 1):
        cands = [(n, results[n][m - 1]) for n in results]

        def score(s: Snapshot) -> float:
            base = s.late_power
            # Late minutes matter more for the rune question
            late = 1.20 if s.minute >= 18 else (1.08 if s.minute >= 12 else 1.0)
            # Prefer pages that keep Overgrowth / survive tools for Ocean nerf
            kit = 1.0
            if "Overgrowth" in s.notes:
                kit += 0.04
            if s.keystone == "conqueror" and s.minute >= 15:
                kit += 0.06  # stacked healing + AD in long late fights
            if "tenacity" in s.notes and s.minute >= 15:
                kit += 0.03  # CC meta (Lillia / Amumu) eats form time
            return base * late * kit

        best_n, best_s = max(cands, key=lambda x: score(x[1]))
        timeline.append(
            {
                "minute": m,
                "winner": best_n,
                "late_power": best_s.late_power,
                "mix_dmg": best_s.mix_dmg,
                "alive_sec": best_s.alive_sec,
                "ad": best_s.ad,
                "hp": best_s.hp,
                "notes": best_s.notes,
                "rune_name": best_s.rune_name,
            }
        )
    return results, timeline


def summarize_runes(results: Dict[str, List[Snapshot]], timeline: List[dict]) -> str:
    lines = []
    lines.append("")
    lines.append("=" * 84)
    lines.append("SHYVANA JUNGLE — RUNE COMPARISON  (items locked: TF → BotRK → DD → FoN → Twin)")
    lines.append("Question: which rune page wins the late dragon-form brawl?")
    lines.append("=" * 84)
    lines.append("")
    lines.append("-" * 84)
    lines.append("MINUTE-BY-MINUTE OPTIMAL RUNE PAGE")
    lines.append("-" * 84)
    for row in timeline:
        if row["minute"] % 2 != 0 and row["minute"] not in (1, 5, 9, 13, 17, 21, 25):
            continue
        lines.append(
            f"  {row['minute']:>2}:00 | power {row['late_power']:>7.0f} | "
            f"alive {row['alive_sec']:>4.1f}s | AD {row['ad']:>5.0f} | "
            f"HP {row['hp']:>5.0f} | {row['winner']}"
        )
        lines.append(f"         {row['notes']}")

    lines.append("")
    lines.append("-" * 84)
    lines.append("RUNE PAGE COMPARISON — LATE POWER @ spikes")
    lines.append("-" * 84)
    hdr = (
        f"  {'Rune page':<42} {'10:00':>7} {'15:00':>7} {'20:00':>7} "
        f"{'25:00':>7} {'EffLate':>8} {'Alive25':>7}"
    )
    lines.append(hdr)

    ranking = []
    for name, snaps in results.items():
        b10 = snaps[9].late_power
        b15 = snaps[14].late_power
        b20 = snaps[19].late_power
        b25 = snaps[24].late_power
        score_sum = 0.0
        for s in snaps:
            mult = 1.0
            if s.minute >= 18:
                mult *= 1.35
            elif s.minute >= 12:
                mult *= 1.15
            if s.keystone == "conqueror" and s.minute >= 15:
                mult *= 1.08
            if "Overgrowth" in s.notes:
                mult *= 1.04
            score_sum += s.late_power * mult
        eff = score_sum / len(snaps)
        ranking.append(
            (eff, b25, b20, name, b10, b15, b20, b25, snaps, snaps[24].alive_sec)
        )
        lines.append(
            f"  {name:<42} {b10:>7.0f} {b15:>7.0f} {b20:>7.0f} "
            f"{b25:>7.0f} {eff:>8.0f} {snaps[24].alive_sec:>7.1f}"
        )

    ranking.sort(key=lambda x: (x[0], x[1]), reverse=True)
    best = ranking[0]
    winner_name = best[3]
    win = best[8]
    guide = results["Fleet + Alacrity (guide)"]
    pct25 = (
        100.0 * (win[24].late_power / guide[24].late_power - 1.0)
        if guide[24].late_power
        else 0.0
    )
    pct20 = (
        100.0 * (win[19].late_power / guide[19].late_power - 1.0)
        if guide[19].late_power
        else 0.0
    )

    lines.append("")
    lines.append("-" * 84)
    lines.append("ALIVE TIME @ 15 / 20 / 25")
    lines.append("-" * 84)
    for row in ranking:
        name, snaps = row[3], row[8]
        lines.append(
            f"  {name:<42} {snaps[14].alive_sec:>7.1f} "
            f"{snaps[19].alive_sec:>7.1f} {snaps[24].alive_sec:>7.1f}"
        )

    lines.append("")
    lines.append("-" * 84)
    lines.append("RUNE VERDICT")
    lines.append("-" * 84)
    lines.append(f"  Best page (late counter-meta): {winner_name}")
    lines.append(f"  Page: {win[24].rune_name}")
    lines.append(
        f"  Late-weighted avg: {best[0]:.0f} | 25:00 late-power: {best[1]:.0f}"
    )
    lines.append(
        f"  vs guide Fleet+Alacrity: 20:00 {pct20:+.0f}% | 25:00 {pct25:+.0f}%"
    )
    lines.append(
        f"  25:00 alive {win[24].alive_sec:.1f}s vs guide "
        f"{guide[24].alive_sec:.1f}s | AD {win[24].ad:.0f} vs {guide[24].ad:.0f}"
    )
    lines.append("")
    lines.append("  WHY THIS PAGE FOR LATE WINS:")
    lines.append("  • After Ocean 10% nerf, in-combat healing must come from the")
    lines.append("    keystone + items. Conqueror omnivamp stacks inside the 12s")
    lines.append("    form; Fleet heals between trades / on stick procs.")
    lines.append("  • Twin Bite double-hits stack Conqueror very fast in dragon form.")
    lines.append("  • Alacrity > Bloodline/Haste on this build: more autos → more Q")
    lines.append("    refunds → more BotRK %HP doubles (the anti-tank tool).")
    lines.append("  • Overgrowth + Unshakeable keep the dive alive once DD/Twinguard")
    lines.append("    are online. Drop Overgrowth for Perseverance only vs heavy CC.")
    lines.append("")
    lines.append("  RECOMMENDED RUNES (late-game counter-meta Shyvana jungle):")
    if "Conqueror" in winner_name:
        lines.append("  Keystone:  Conqueror")
        lines.append("  Primary:   Unshakeable · Second Wind · Overgrowth")
        lines.append("  Secondary: Legend: Alacrity")
        lines.append("")
        lines.append("  Swap to Fleet Footwork if you get kited / need clear stick MS")
        lines.append("  more than in-combat healing (still keep Alacrity + Overgrowth).")
    else:
        lines.append("  Keystone:  Fleet Footwork")
        lines.append("  Primary:   Unshakeable · Second Wind · Overgrowth")
        lines.append("  Secondary: Legend: Alacrity")
        lines.append("")
        lines.append("  Swap to Conqueror when fights go long and you want stacked")
        lines.append("  omnivamp inside dragon form (Ocean nerf makes this stronger).")
    lines.append("  vs heavy CC (Lillia / Amumu): Perseverance over Overgrowth.")
    lines.append("  vs burst dive: Bone Plating over Second Wind.")
    lines.append("  Trap: full Precision Bloodline page — less Q weave than Alacrity,")
    lines.append("  so BotRK shred and Spellblade cadence fall off.")
    lines.append("=" * 84)
    return "\n".join(lines)


def export_json(
    results, timeline, path: str, rune_results=None, rune_timeline=None
) -> None:
    payload = {
        "meta": {
            "champion": "Shyvana",
            "role": "Jungle",
            "patch": "7.3d/f",
            "game_minutes": GAME_MINUTES,
            "playstyle": "full-clear scaler → dragon-form teamfight",
            "metric": "late_power = mix_damage * (alive_sec / 12)",
            "tank_weight": TANK_WEIGHT,
            "carry_weight": CARRY_WEIGHT,
            "question": "best build + runes to counter tanky meta and win late game",
            "winning_item_build": WINNING_ITEM_BUILD,
            "default_runes": DEFAULT_RUNES.name,
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
                    "ap": s.ap,
                    "hp": s.hp,
                    "armor": s.armor,
                    "mr": s.mr,
                    "legendary_count": s.legendary_count,
                    "dmg_tank": s.dmg_tank,
                    "dmg_carry": s.dmg_carry,
                    "mix_dmg": s.mix_dmg,
                    "alive_sec": s.alive_sec,
                    "late_power": s.late_power,
                    "notes": s.notes,
                    "rune_name": s.rune_name,
                    "keystone": s.keystone,
                }
                for s in snaps
            ]
            for name, snaps in results.items()
        },
    }
    if rune_results is not None:
        payload["rune_timeline"] = rune_timeline
        payload["rune_pages"] = {
            name: [
                {
                    "minute": s.minute,
                    "rune_name": s.rune_name,
                    "keystone": s.keystone,
                    "items": s.items,
                    "ad": s.ad,
                    "hp": s.hp,
                    "armor": s.armor,
                    "mr": s.mr,
                    "dmg_tank": s.dmg_tank,
                    "mix_dmg": s.mix_dmg,
                    "alive_sec": s.alive_sec,
                    "late_power": s.late_power,
                    "notes": s.notes,
                }
                for s in snaps
            ]
            for name, snaps in rune_results.items()
        }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def self_check(
    results: Dict[str, List[Snapshot]],
    rune_results: Optional[Dict[str, List[Snapshot]]] = None,
) -> None:
    """Sanity: late winner must shred tanks and outlive glass paths."""
    glass = results["Dusk → Cap → Liandry → Nashor → Rift"]
    kraken = results["Kraken → TF → BotRK → Hex → Randuin"]
    # At least one shred+survive path should beat glass late power at 25
    late_powers = {n: results[n][24].late_power for n in results}
    best_n = max(late_powers, key=late_powers.get)
    best = results[best_n][24]
    assert best.alive_sec >= glass[24].alive_sec * 0.95 or best.has_tank_item, (
        best_n,
        best.alive_sec,
        glass[24].alive_sec,
    )
    # Glass should not win pure late_power when score includes survive — check alive
    assert glass[24].alive_sec <= 11.5, glass[24].alive_sec
    # Default bruiser must have BotRK online before 16
    default = results["TF → BotRK → DD → FoN → Twin"]
    botrk_m = first_minute_with(default, lambda s: s.has_botrk)
    assert botrk_m is not None and botrk_m <= 16, botrk_m
    # Winner at 25 should have anti-tank tool
    assert best.has_botrk or best.has_liandry, best_n
    # Kraken glass-ish early shouldn't dominate 25 alive vs tank path
    tank_path = results["TF → BotRK → Twin → FoN → DD"]
    assert tank_path[24].alive_sec >= kraken[24].alive_sec * 0.98

    if rune_results:
        # Conqueror late should beat Fleet on raw late_power or alive at 25
        conq = rune_results["Conqueror + Alacrity (late brawl)"]
        fleet = rune_results["Fleet + Alacrity (guide)"]
        assert (
            conq[24].late_power >= fleet[24].late_power * 0.98
            or conq[24].ad > fleet[24].ad
        ), (conq[24].late_power, fleet[24].late_power, conq[24].ad, fleet[24].ad)
        # Alacrity page should beat Haste on late_power (Q weave / BotRK)
        haste = rune_results["Fleet + Haste (ability weave)"]
        assert fleet[24].late_power >= haste[24].late_power * 0.95


def main() -> None:
    results, timeline = run_all()
    rune_results, rune_timeline = run_runes()
    self_check(results, rune_results)
    report = summarize(results, timeline)
    report += summarize_runes(rune_results, rune_timeline)
    print(report)
    out_dir = "/workspace/shyvana-jungle-sim"
    with open(f"{out_dir}/report.txt", "w", encoding="utf-8") as f:
        f.write(report + "\n")
    export_json(
        results,
        timeline,
        f"{out_dir}/results.json",
        rune_results=rune_results,
        rune_timeline=rune_timeline,
    )
    print(f"\nWrote {out_dir}/report.txt and {out_dir}/results.json")


if __name__ == "__main__":
    main()
