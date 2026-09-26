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
  Does buying IE 2nd vs 3rd change Dragon Practice stacking?
  Which boots keep the extra Q — Ionian vs Greaves vs Immortal Treads?
  Ability scale vs crit scale — what actually multiplies Super Scorcher?
  ER 20 AH is not enough early — which path actually optimizes Dragon Practice?
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
    """Baseline farm curve (no item feedback). Used for tables / isolated deltas."""
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


def minion_hp_for_q(minute: int) -> float:
    """Caster/melee mix a Q is trying to last-hit."""
    return 210.0 + 16.0 * minute


def stacks_gained_this_minute(minute: int, st: dict, stacks_so_far: int) -> float:
    """Dragon Practice income: Q last-hits + champion ability hits.

    IE raises last-hit reliability (Q damage / crit amp). Shojin raises Q
    count (AH). Hexoptics raises champion-hit safety (range amp). Navori
    refunds farm Q CD. Early AH (Ionian / Caulfield) raises Q count before IE.
    """
    level = level_at_minute(minute)
    ah = st["ah"]
    q_cd = q_cooldown(level, ah)
    if st.get("trans_refund"):
        q_cd *= 0.92
    # Farm has autos between Qs. Navori 15% remaining-CD refund, ~2 procs/min.
    if st.get("navori"):
        q_cd *= 0.85 ** 2
    q_per_min = 60.0 / max(1.6, q_cd)

    crit = min(1.0, st["crit"])
    amp = q_amp(crit, st["crit_dmg"])
    q_rank = skill_rank(level, "Q")
    q_phys = q_base_phys(q_rank, st["bonus_ad"]) * (1.0 + amp)
    if st.get("er"):
        q_phys += 1.35 * st["base_ad"] + 80.0 * crit
    elif st.get("trinity"):
        q_phys += 2.00 * st["base_ad"]
    if st.get("hexoptics"):
        q_phys *= 1.10

    rel = min(1.0, max(0.50, q_phys / minion_hp_for_q(minute)))
    farm = q_per_min * 0.38 * rel
    if stacks_so_far >= 25:
        farm *= 1.10
    if stacks_so_far >= 100:
        farm *= 1.06

    # Champion hits: opportunities, filled better with more Qs / safer range.
    opp = 1.5 + 0.055 * minute
    cd_fill = min(1.28, max(0.78, q_per_min / 18.0))
    champ = opp * cd_fill
    if st.get("hexoptics"):
        champ *= 1.12
    if st.get("shojin"):
        champ *= 1.06
    if st.get("navori"):
        champ *= 1.05
    if stacks_so_far >= 25:
        champ *= 1.08
    if stacks_so_far >= 100:
        champ *= 1.10
    return farm + champ


def stack_curve_for_path(
    path: List[str], runes: RunePage = DEFAULT_RUNES
) -> List[int]:
    """curve[m] = stacks at minute m (curve[0] unused)."""
    stacks = 0.0
    curve = [0]
    for m in range(1, GAME_MINUTES + 1):
        gold = gold_at_minute(m)
        level = level_at_minute(m)
        inv = resolve_inventory(path, gold, m)
        st = sum_stats(inv, m, level, runes)
        stacks += stacks_gained_this_minute(m, st, stacks)
        curve.append(int(round(stacks)))
    return curve


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
    immortal: bool = False
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
    # 7.2c: 35% AS. T3 Gunmetal is the 50% AS + 5% LS upgrade (7.3).
    "Berserker's Greaves": Item(
        "Berserker's Greaves", 1200, as_pct=0.35, tags=("boots",)
    ),
    # T3 unlocks at 10:00. Crimson is +10 AH over Ionian, still one boot slot.
    "Crimson Lucidity": Item(
        "Crimson Lucidity", 2000, ah=25, tags=("boots", "t3")
    ),
    # 12 AD + 5–10% omnivamp + 5% damage while above 50% HP.
    "Immortal Treads": Item(
        "Immortal Treads", 2000, ad=12, immortal=True, tags=("boots", "t3")
    ),
    # 7.3: physical vamp → 5% lifesteal. Autohit heal is not Q vamp.
    "Gunmetal Greaves": Item(
        "Gunmetal Greaves", 2200, as_pct=0.50, ls=0.05, tags=("boots", "t3")
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
    "Berserker's Greaves": ("Boots",),
    "Crimson Lucidity": ("Ionian Boots of Lucidity",),
    "Immortal Treads": ("Gluttonous Greaves",),
    "Gunmetal Greaves": ("Berserker's Greaves",),
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
    "Berserker's Greaves": ["Boots"],
    "Crimson Lucidity": ["Ionian Boots of Lucidity"],
    "Immortal Treads": ["Gluttonous Greaves"],
    "Gunmetal Greaves": ["Berserker's Greaves"],
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
    # IE 3rd — Hexoptics 2nd (range/safety for champion stacks)
    "ER → Hex → IE → LDR → BT": [
        "Long Sword",
        "Sheen",
        "Essence Reaver",
        "Boots",
        "Ionian Boots of Lucidity",
        "Hexoptics C44",
        "Infinity Edge",
        "Lord Dominik's Regards",
        "Bloodthirster",
    ],
    # IE 2nd then Shojin (damage spike, then stacking AH)
    "ER → IE → Shojin → Hex → LDR": [
        "Long Sword",
        "Sheen",
        "Essence Reaver",
        "Boots",
        "Ionian Boots of Lucidity",
        "Infinity Edge",
        "Spear of Shojin",
        "Hexoptics C44",
        "Lord Dominik's Regards",
    ],
    # IE 3rd — Shojin 2nd (AH stacking, IE delayed)
    "ER → Shojin → IE → Hex → LDR": [
        "Long Sword",
        "Sheen",
        "Essence Reaver",
        "Boots",
        "Ionian Boots of Lucidity",
        "Spear of Shojin",
        "Infinity Edge",
        "Hexoptics C44",
        "Lord Dominik's Regards",
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


def path_with_boots(*boot_steps: str) -> List[str]:
    """Winning legendaries, only the boot slot changes."""
    return [
        "Long Sword",
        "Sheen",
        "Essence Reaver",
        "Boots",
        *boot_steps,
        "Infinity Edge",
        "Hexoptics C44",
        "Lord Dominik's Regards",
        "Bloodthirster",
    ]


# Same items as WINNING_ITEMS. T3 boots unlock at 10:00 and cost +1000.
BOOT_PAGES: Dict[str, List[str]] = {
    "Ionian Boots of Lucidity": path_with_boots("Ionian Boots of Lucidity"),
    "Crimson Lucidity": path_with_boots(
        "Ionian Boots of Lucidity", "Crimson Lucidity"
    ),
    "Gluttonous Greaves": path_with_boots("Gluttonous Greaves"),
    "Immortal Treads": path_with_boots("Gluttonous Greaves", "Immortal Treads"),
    "Berserker's Greaves": path_with_boots("Berserker's Greaves"),
    "Gunmetal Greaves": path_with_boots("Berserker's Greaves", "Gunmetal Greaves"),
}

BOOT_GOLD = {
    "Ionian Boots of Lucidity": 1000,
    "Crimson Lucidity": 2000,
    "Gluttonous Greaves": 1000,
    "Immortal Treads": 2000,
    "Berserker's Greaves": 1200,
    "Gunmetal Greaves": 2200,
}

TIER3_BOOTS = {
    "Crimson Lucidity",
    "Immortal Treads",
    "Gunmetal Greaves",
}
TIER3_UNLOCK_MINUTE = 10
T3_REPLACES = {
    "Crimson Lucidity": "Ionian Boots of Lucidity",
    "Immortal Treads": "Gluttonous Greaves",
    "Gunmetal Greaves": "Berserker's Greaves",
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
    "Berserker's Greaves",
    "Crimson Lucidity",
    "Immortal Treads",
    "Gunmetal Greaves",
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
        if item_name in TIER3_BOOTS and minute < TIER3_UNLOCK_MINUTE:
            return False
        return gold_pool >= remaining_cost(item_name)

    def buy(item_name: str) -> bool:
        nonlocal gold_pool
        if item_name in TIER3_BOOTS and minute < TIER3_UNLOCK_MINUTE:
            return False
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
        # T3 boots unlock at 10:00 — skip them, keep buying legendaries.
        if step in TIER3_BOOTS and minute < TIER3_UNLOCK_MINUTE:
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
                if step in TIER3_BOOTS and minute < TIER3_UNLOCK_MINUTE:
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

    for t3, t2 in T3_REPLACES.items():
        if t3 in owned and t2 in owned:
            owned.remove(t2)
    for b in (
        "Ionian Boots of Lucidity",
        "Gluttonous Greaves",
        "Berserker's Greaves",
        "Crimson Lucidity",
        "Immortal Treads",
        "Gunmetal Greaves",
    ):
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


def auto_expected_mult(crit: float, crit_dmg: float) -> float:
    return 1.0 + min(1.0, crit) * (crit_dmg - 1.0)


def scorcher_one(
    minute: int,
    bonus_ad: float,
    base_ad: float,
    crit: float,
    ie: bool,
    stacks: int,
    *,
    shojin: bool = False,
    hexoptics: bool = False,
    er: bool = True,
    pct_pen: float = 0.35,
) -> dict:
    """One Super Scorcher vs a squishy. Isolates crit amp vs Shojin 12%."""
    level = level_at_minute(minute)
    armor = squishy_armor(minute)
    mr = 32.0 + 1.2 * level
    hp = squishy_hp(minute)
    crit_dmg = 2.30 if ie else 2.00
    c = min(1.0, crit)
    amp = q_amp(c, crit_dmg)
    magic_ratio = stack_magic_ratio_q(c, crit_dmg)
    auto_m = auto_expected_mult(c, crit_dmg)
    q_rank = 4 if level >= 7 else skill_rank(level, "Q")
    q_raw = q_base_phys(q_rank, bonus_ad)
    sheen = (1.35 * base_ad + 80.0 * c) if er else 0.0
    q_phys = q_raw * (1.0 + amp) + sheen
    q_magic = stacks * magic_ratio
    burn = burn_true_ratio(bonus_ad, stacks) * hp
    pmult = phys_mult(apply_armor(armor, pct_pen, 0.0, 0.0))
    mmult = magic_mult(mr)
    sh = 1.12 if shojin else 1.0
    hx = 1.10 if hexoptics else 1.0
    zeal = 1.045  # poke average Battle Zeal
    hit = (q_phys * pmult + q_magic * mmult) * sh * zeal
    # Burn is true damage; Hexoptics range amp applies to the whole Q packet.
    one_q = (hit + burn * zeal) * hx
    w_rank = skill_rank(level, "W")
    w_raw = w_champ_phys(w_rank, bonus_ad, 0.0)
    # W/E/R do not get Q's crit amp — only AD ratios + Shojin.
    w_one = w_raw * pmult * sh * zeal * hx
    return {
        "amp": amp,
        "magic_ratio": magic_ratio,
        "auto_mult": auto_m,
        "q_raw": q_raw,
        "q_phys": q_phys,
        "q_magic": q_magic,
        "sheen": sheen,
        "one_q": one_q,
        "w_one": w_one,
        "crit": c,
        "ie": ie,
        "shojin": shojin,
        "hexoptics": hexoptics,
    }


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
        "immortal": False,
        "crimson": False,
        "berserker": False,
        "gunmetal": False,
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
        if it.immortal:
            flags["immortal"] = True
        if it.name == "Gluttonous Greaves":
            flags["greaves"] = True
        if it.name == "Crimson Lucidity":
            flags["crimson"] = True
        if it.name == "Berserker's Greaves":
            flags["berserker"] = True
        if it.name == "Gunmetal Greaves":
            flags["gunmetal"] = True

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

    # Immortal Treads: +5% damage while above 50% HP (poke 82% / fight 70%).
    if stats.get("immortal") and current_hp_frac > 0.50:
        dmg *= 1.05

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
    stacks: Optional[int] = None,
) -> Snapshot:
    gold = gold_at_minute(minute)
    level = level_at_minute(minute)
    if stacks is None:
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
    if st.get("immortal"):
        notes.append("Immortal 5%")
    if st.get("crimson"):
        notes.append("Crimson 25 AH")
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


def run_all() -> Tuple[Dict[str, List[Snapshot]], List[dict], Dict[str, List[int]]]:
    results: Dict[str, List[Snapshot]] = {}
    curves: Dict[str, List[int]] = {}
    for name, path in BUILD_PATHS.items():
        curve = stack_curve_for_path(path)
        curves[name] = curve
        results[name] = [
            compute_snapshot(name, path, m, stacks=curve[m])
            for m in range(1, GAME_MINUTES + 1)
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
    return results, timeline, curves


def mix_of(s: Snapshot) -> float:
    return 0.55 * s.mix_tank + 0.45 * s.mix_squish


def run_runes() -> Dict[str, List[Snapshot]]:
    path = BUILD_PATHS[WINNING_ITEMS]
    out: Dict[str, List[Snapshot]] = {}
    for name, page in RUNE_PAGES.items():
        curve = stack_curve_for_path(path, page)
        out[name] = [
            compute_snapshot(WINNING_ITEMS, path, m, page, stacks=curve[m])
            for m in range(1, GAME_MINUTES + 1)
        ]
    return out


def run_boots() -> Dict[str, List[Snapshot]]:
    """Winning legendaries, only the boot slot changes."""
    out: Dict[str, List[Snapshot]] = {}
    for name, path in BOOT_PAGES.items():
        curve = stack_curve_for_path(path)
        out[name] = [
            compute_snapshot(WINNING_ITEMS, path, m, stacks=curve[m])
            for m in range(1, GAME_MINUTES + 1)
        ]
    return out


HASTE_RUNES = RUNE_PAGES["Fleet / Zeal / Cut Down / Haste / Transcendence"]


def _er_then(*rest: str) -> List[str]:
    return [
        "Long Sword",
        "Sheen",
        "Caulfield's Warhammer",
        "Essence Reaver",
        "Boots",
        "Ionian Boots of Lucidity",
        *rest,
    ]


# Goal: T3 clock and stacks@16. ER last-hit first, then dump AH, convert with IE.
STACK_PAGES: Dict[str, Tuple[List[str], RunePage]] = {
    "IE 2nd / Bloodline": (
        _er_then("Infinity Edge", "Hexoptics C44", "Lord Dominik's Regards", "Bloodthirster"),
        DEFAULT_RUNES,
    ),
    "IE 2nd / Haste": (
        _er_then("Infinity Edge", "Hexoptics C44", "Lord Dominik's Regards", "Bloodthirster"),
        HASTE_RUNES,
    ),
    "Shojin 2nd / Bloodline": (
        _er_then("Spear of Shojin", "Infinity Edge", "Hexoptics C44", "Lord Dominik's Regards"),
        DEFAULT_RUNES,
    ),
    "Shojin 2nd / Haste": (
        _er_then("Spear of Shojin", "Infinity Edge", "Hexoptics C44", "Lord Dominik's Regards"),
        HASTE_RUNES,
    ),
    "Navori 2nd / Haste": (
        _er_then("Navori Quickblades", "Infinity Edge", "Hexoptics C44", "Lord Dominik's Regards"),
        HASTE_RUNES,
    ),
    "Ionian before ER / Shojin / Haste": (
        [
            "Long Sword",
            "Boots",
            "Ionian Boots of Lucidity",
            "Sheen",
            "Essence Reaver",
            "Spear of Shojin",
            "Infinity Edge",
            "Hexoptics C44",
            "Lord Dominik's Regards",
        ],
        HASTE_RUNES,
    ),
    "Caulfield+Ionian opener / Shojin / Haste": (
        [
            "Long Sword",
            "Caulfield's Warhammer",
            "Boots",
            "Ionian Boots of Lucidity",
            "Sheen",
            "Essence Reaver",
            "Spear of Shojin",
            "Infinity Edge",
            "Hexoptics C44",
            "Lord Dominik's Regards",
        ],
        HASTE_RUNES,
    ),
    "Crimson+Shojin / Haste": (
        _er_then(
            "Crimson Lucidity",
            "Spear of Shojin",
            "Infinity Edge",
            "Hexoptics C44",
            "Lord Dominik's Regards",
        ),
        HASTE_RUNES,
    ),
    "Hex 2nd / Haste": (
        _er_then("Hexoptics C44", "Infinity Edge", "Lord Dominik's Regards", "Bloodthirster"),
        HASTE_RUNES,
    ),
    "Cleaver 2nd / Haste": (
        _er_then(
            "Black Cleaver",
            "Infinity Edge",
            "Hexoptics C44",
            "Lord Dominik's Regards",
        ),
        HASTE_RUNES,
    ),
}


def farm_qpm(s: Snapshot) -> float:
    q_cd = q_cooldown(s.level, s.ah)
    if s.level >= 9:
        q_cd *= 0.92
    if s.has_navori:
        q_cd *= 0.85 ** 2
    return 60.0 / max(1.6, q_cd)


def run_stacking() -> Dict[str, List[Snapshot]]:
    """ER last-hit first, then extra AH, then IE — pick the T3 clock."""
    out: Dict[str, List[Snapshot]] = {}
    for name, (path, runes) in STACK_PAGES.items():
        curve = stack_curve_for_path(path, runes)
        out[name] = [
            compute_snapshot(name, path, m, runes, stacks=curve[m])
            for m in range(1, GAME_MINUTES + 1)
        ]
    return out


SCALE_PATHS = [
    ("Crit (100% + IE + Hex)", "ER → IE → Hex → LDR → BT"),
    ("Hybrid (IE then Shojin)", "ER → IE → Shojin → Hex → LDR"),
    ("Ability (Shojin 2nd)", "ER → Shojin → IE → Hex → LDR"),
    ("Ability (Navori Qs)", "ER → IE → Navori → Mortal → BT"),
    ("Old mana (0% crit Q)", "Mura → Tri → Serylda → Shojin → IE"),
]


def run_scale_lab(results: Dict[str, List[Snapshot]]) -> Tuple[List[dict], List[dict]]:
    """Same AD/stacks as the winning page at 22:00; only the multiplier changes."""
    s = results[WINNING_ITEMS][21]
    base_ad = s.ad - s.bonus_ad
    specs = [
        ("AD ratios only (0% crit)", 0.00, False, False, False),
        ("Shojin 12%, 0% crit", 0.00, False, True, False),
        ("25% crit (ER, no IE)", 0.25, False, False, False),
        ("50% crit, no IE", 0.50, False, False, False),
        ("100% crit, no IE", 1.00, False, False, False),
        ("100% crit + IE", 1.00, True, False, False),
        ("100% + IE + Hex 10%", 1.00, True, False, True),
        ("100% + IE + Shojin", 1.00, True, True, False),
        ("100% + IE + Hex + Shojin", 1.00, True, True, True),
    ]
    lab = []
    for name, crit, ie, shojin, hexoptics in specs:
        row = scorcher_one(
            22,
            s.bonus_ad,
            base_ad,
            crit,
            ie,
            s.stacks,
            shojin=shojin,
            hexoptics=hexoptics,
            er=True,
            pct_pen=0.35,
        )
        row["name"] = name
        row["bonus_ad"] = s.bonus_ad
        row["stacks"] = s.stacks
        lab.append(row)

    paths = []
    for label, key in SCALE_PATHS:
        if key not in results:
            continue
        snaps = results[key]
        a = snaps[21]
        b = snaps[24]
        paths.append(
            {
                "name": label,
                "key": key,
                "crit": a.crit,
                "amp": q_amp(min(1.0, a.crit), a.crit_dmg),
                "magic_ratio": stack_magic_ratio_q(min(1.0, a.crit), a.crit_dmg),
                "auto_mult": auto_expected_mult(a.crit, a.crit_dmg),
                "qs": a.q_casts_poke,
                "ah": a.ah,
                "bonus_ad": a.bonus_ad,
                "has_ie": a.has_ie,
                "has_shojin": a.has_shojin,
                "has_hex": a.has_hex,
                "mix22": mix_of(a),
                "mix25": mix_of(b),
                "poke22": a.poke_squish,
                "fight22": a.fight_tank,
            }
        )
    return lab, paths


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


def boot_score(snaps: List[Snapshot], name: str) -> float:
    """Fit score: extra Qs and on-time IE beat T3 gold delay and AS boots."""
    mix18 = mix_of(snaps[17])
    mix22 = mix_of(snaps[21])
    mix25 = mix_of(snaps[24])
    qs = snaps[21].q_casts_poke
    ie_m = first_minute_with(snaps, lambda s: s.has_ie) or 25
    kit = 1.0
    if qs >= 4:
        kit += 0.12
    if ie_m <= 14:
        kit += 0.05
    elif ie_m >= 16:
        kit *= 0.94
    if name in ("Berserker's Greaves", "Gunmetal Greaves"):
        kit *= 0.90
    return (0.30 * mix18 + 0.40 * mix22 + 0.30 * mix25) * kit


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


def summarize(
    results, timeline, rune_results, boot_results, scale_lab, scale_paths, stack_results
) -> str:
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

    ie_stack_names = [
        "ER → IE → Hex → LDR → BT",
        "ER → Hex → IE → LDR → BT",
        "ER → IE → Shojin → Hex → LDR",
        "ER → Shojin → IE → Hex → LDR",
        "ER → Shojin → IE → Mortal → Hex",
    ]
    lines.append("")
    lines.append("-" * 80)
    lines.append("IE 2ND vs 3RD — DRAGON PRACTICE STACKING")
    lines.append("-" * 80)
    lines.append(
        f"  {'Path':<36} {'T3':>4} {'IE':>7} "
        f"{'Stk13':>6} {'Stk16':>6} {'Stk18':>6} "
        f"{'Mix13':>7} {'Mix16':>7} {'Mix18':>7} {'Mix22':>7}"
    )
    ie_stack_rows = []
    for name in ie_stack_names:
        if name not in results:
            continue
        snaps = results[name]
        t1 = first_minute_with(snaps, lambda s: s.stacks >= 25)
        t2 = first_minute_with(snaps, lambda s: s.stacks >= 100)
        t3 = first_minute_with(snaps, lambda s: s.stacks >= 175)
        ie_at = first_minute_with(snaps, lambda s: s.has_ie)
        n_leg_ie = snaps[ie_at - 1].legendary_count if ie_at else 0
        slot = {1: "1st", 2: "2nd", 3: "3rd"}.get(n_leg_ie, str(n_leg_ie))
        ie_lab = f"{ie_at} {slot}" if ie_at else "-"
        lines.append(
            f"  {name:<36} {t3 or 0:>4} {ie_lab:>7} "
            f"{snaps[12].stacks:>6} {snaps[15].stacks:>6} {snaps[17].stacks:>6} "
            f"{mix_of(snaps[12]):>7.0f} {mix_of(snaps[15]):>7.0f} "
            f"{mix_of(snaps[17]):>7.0f} {mix_of(snaps[21]):>7.0f}"
        )
        ie_stack_rows.append((name, t1, t2, t3, ie_at, n_leg_ie, snaps))

    ie2 = results.get("ER → IE → Hex → LDR → BT")
    hex2 = results.get("ER → Hex → IE → LDR → BT")
    sho2 = results.get("ER → Shojin → IE → Hex → LDR")
    ie2sho = results.get("ER → IE → Shojin → Hex → LDR")
    if ie2 and hex2:
        ie2_m = first_minute_with(ie2, lambda s: s.has_ie)
        hex_ie_m = first_minute_with(hex2, lambda s: s.has_ie)
        t3_ie2 = first_minute_with(ie2, lambda s: s.stacks >= 175)
        t3_hex2 = first_minute_with(hex2, lambda s: s.stacks >= 175)
        t3_sho = (
            first_minute_with(sho2, lambda s: s.stacks >= 175) if sho2 else None
        )
        lines.append("")
        lines.append("  Isolated at the IE-2nd complete minute (same clock, different 2nd):")
        if ie2_m:
            a, b = ie2[ie2_m - 1], hex2[ie2_m - 1]
            lines.append(
                f"    ~{ie2_m}:00  IE 2nd: {a.stacks} stacks, mix {mix_of(a):.0f}, "
                f"Q amp {int(a.crit*100)}% crit + IE"
            )
            lines.append(
                f"    ~{ie2_m}:00  Hex 2nd: {b.stacks} stacks, mix {mix_of(b):.0f}, "
                f"{int(b.crit*100)}% crit, no IE"
            )
            lines.append(
                f"    Stack Δ (IE 2nd − Hex 2nd): {a.stacks - b.stacks:+d}  |  "
                f"mix Δ {mix_of(a) - mix_of(b):+.0f}"
            )
        if sho2 and ie2_m:
            c = sho2[ie2_m - 1]
            lines.append(
                f"    ~{ie2_m}:00  Shojin 2nd: {c.stacks} stacks, mix {mix_of(c):.0f} "
                f"(AH stacking, IE not in)"
            )
            lines.append(
                f"    Stack Δ (IE 2nd − Shojin 2nd): {ie2[ie2_m-1].stacks - c.stacks:+d}"
            )
        lines.append("")
        lines.append("  When IE-3rd finally lands vs IE-2nd already online:")
        if hex_ie_m:
            d, e = hex2[hex_ie_m - 1], ie2[hex_ie_m - 1]
            lines.append(
                f"    ~{hex_ie_m}:00 Hex→IE completes. Stacks {d.stacks} vs IE-2nd path "
                f"{e.stacks} ({d.stacks - e.stacks:+d}). Mix {mix_of(d):.0f} vs {mix_of(e):.0f}."
            )
        lines.append("")
        lines.append("  T3 (175) clock — this is the stacking payoff:")
        if t3_ie2:
            lines.append(
                f"    IE 2nd  (ER→IE→Hex)     T3 ~{t3_ie2}:00  mix {mix_of(ie2[t3_ie2-1]):.0f}"
            )
        if t3_hex2:
            lines.append(
                f"    IE 3rd  (ER→Hex→IE)     T3 ~{t3_hex2}:00  mix {mix_of(hex2[t3_hex2-1]):.0f}"
            )
        if t3_sho:
            lines.append(
                f"    IE 3rd  (ER→Shojin→IE)  T3 ~{t3_sho}:00  mix {mix_of(sho2[t3_sho-1]):.0f}"
            )
        if ie2sho:
            t3_i2s = first_minute_with(ie2sho, lambda s: s.stacks >= 175)
            if t3_i2s:
                lines.append(
                    f"    IE 2nd  (ER→IE→Shojin)  T3 ~{t3_i2s}:00  mix {mix_of(ie2sho[t3_i2s-1]):.0f}"
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
    lines.append(f"BOOTS ON {WINNING_ITEMS}  (same legendaries, swap only the boot)")
    lines.append("-" * 80)
    lines.append(
        f"  {'Boot':<26} {'Gold':>5} {'IE':>4} {'Qs':>3} "
        f"{'Stk16':>5} {'Mix16':>6} {'Mix22':>6} {'Mix25':>6} "
        f"{'Poke22':>6} {'Fight22':>7}"
    )
    boot_rank = []
    for name, snaps in boot_results.items():
        ie_m = first_minute_with(snaps, lambda s: s.has_ie)
        sc = boot_score(snaps, name)
        boot_rank.append((sc, name, snaps, ie_m))
        lines.append(
            f"  {name:<26} {BOOT_GOLD[name]:>5} {ie_m or 0:>4} "
            f"{snaps[21].q_casts_poke:>3} {snaps[15].stacks:>5} "
            f"{mix_of(snaps[15]):>6.0f} {mix_of(snaps[21]):>6.0f} "
            f"{mix_of(snaps[24]):>6.0f} {snaps[21].poke_squish:>6.0f} "
            f"{snaps[21].fight_tank:>7.0f}"
        )
    boot_rank.sort(key=lambda x: x[0], reverse=True)
    best_boot = boot_rank[0]

    ion_b = boot_results.get("Ionian Boots of Lucidity")
    gre_b = boot_results.get("Gluttonous Greaves")
    imm_b = boot_results.get("Immortal Treads")
    cri_b = boot_results.get("Crimson Lucidity")
    ber_b = boot_results.get("Berserker's Greaves")
    gun_b = boot_results.get("Gunmetal Greaves")
    if ion_b and gre_b:
        lines.append("")
        lines.append("  Isolated (same clock, only the boot differs):")
        lines.append(
            f"    Ionian   {ion_b[21].q_casts_poke} Qs @22  mix {mix_of(ion_b[21]):.0f}  "
            f"AH {ion_b[21].ah:.0f}"
        )
        lines.append(
            f"    Greaves  {gre_b[21].q_casts_poke} Qs @22  mix {mix_of(gre_b[21]):.0f}  "
            f"+12 AD, 5–10% omnivamp (no extra Q)"
        )
        if imm_b:
            ie_ion = first_minute_with(ion_b, lambda s: s.has_ie)
            ie_imm = first_minute_with(imm_b, lambda s: s.has_ie)
            lines.append(
                f"    Immortal {imm_b[21].q_casts_poke} Qs @22  mix {mix_of(imm_b[21]):.0f}  "
                f"12 AD + 5% while healthy, IE ~{ie_imm}:00 vs Ionian ~{ie_ion}:00"
            )
        if cri_b:
            lines.append(
                f"    Crimson  {cri_b[21].q_casts_poke} Qs @22  mix {mix_of(cri_b[21]):.0f}  "
                f"25 AH still {cri_b[21].q_casts_poke} Qs; 1000g delays IE"
            )
        if ber_b:
            lines.append(
                f"    Berserker {ber_b[21].q_casts_poke} Qs @22 mix {mix_of(ber_b[21]):.0f}  "
                f"35% AS  fight-tank {ber_b[21].fight_tank:.0f} vs "
                f"Ionian {ion_b[21].fight_tank:.0f}"
            )

    lines.append("")
    lines.append("-" * 80)
    lines.append("ABILITY SCALE vs CRIT SCALE  (same AD/stacks as winning page @22:00)")
    lines.append("-" * 80)
    lines.append("  Ability scale: 110% bAD on Q, 60+55% W, 30% E, 110% R, AH, Shojin 12%.")
    lines.append("  Crit scale:    Q physical 0–45% (58.5% with IE), Dragon Practice magic")
    lines.append("                 30%→69% of stacks, autos crit. W/E/R do NOT get Q's amp.")
    lines.append(
        f"  Shared lab: {scale_lab[0]['bonus_ad']:.0f} bAD, {scale_lab[0]['stacks']} stacks, "
        f"ER sheen, 35% pen, vs squishy."
    )
    lines.append(
        f"  {'Multiplier':<28} {'Q amp':>6} {'Magic':>6} {'Auto':>5} "
        f"{'1 Q':>6} {'1 W':>6}"
    )
    by_name = {r["name"]: r for r in scale_lab}
    for row in scale_lab:
        lines.append(
            f"  {row['name']:<28} {100*row['amp']:>5.1f}% "
            f"{100*row['magic_ratio']:>5.0f}% {row['auto_mult']:>5.2f} "
            f"{row['one_q']:>6.0f} {row['w_one']:>6.0f}"
        )
    ad0 = by_name.get("AD ratios only (0% crit)")
    sho0 = by_name.get("Shojin 12%, 0% crit")
    ie100 = by_name.get("100% crit + IE")
    hex100 = by_name.get("100% + IE + Hex 10%")
    both = by_name.get("100% + IE + Shojin")
    if ad0 and sho0 and ie100:
        sho_pct = 100.0 * (sho0["one_q"] / ad0["one_q"] - 1.0)
        ie_pct = 100.0 * (ie100["one_q"] / ad0["one_q"] - 1.0)
        lines.append("")
        lines.append("  Isolated on one Super Scorcher (same AD, same stacks):")
        lines.append(
            f"    Shojin 12% on a 0-crit Q: {sho0['one_q']:.0f} vs {ad0['one_q']:.0f} "
            f"({sho_pct:+.0f}%). W also {sho_pct:+.0f}%."
        )
        lines.append(
            f"    100% crit + IE on that Q: {ie100['one_q']:.0f} vs {ad0['one_q']:.0f} "
            f"({ie_pct:+.0f}%). W unchanged ({ie100['w_one']:.0f} vs {ad0['w_one']:.0f})."
        )
        if both:
            lines.append(
                f"    They multiply: 100%+IE+Shojin one Q {both['one_q']:.0f} "
                f"({100.0*(both['one_q']/ad0['one_q']-1.0):+.0f}%)."
            )
            lines.append("    Slot conflict: 100% crit needs 4 crit items. Shojin replaces")
            lines.append("    Hex, LDR, or BT — you do not get both packages for free.")
        if hex100:
            lines.append(
                f"    Hexoptics 10% at Q range: one Q {hex100['one_q']:.0f} "
                f"(crit package, not ability amp)."
            )

    lines.append("")
    lines.append("  Real pages (gold curve, not a lab toggle):")
    lines.append(
        f"  {'Page':<28} {'Crit':>5} {'Q amp':>6} {'Qs':>3} "
        f"{'Mix22':>6} {'Mix25':>6} {'Poke22':>6}"
    )
    for row in scale_paths:
        lines.append(
            f"  {row['name']:<28} {100*row['crit']:>4.0f}% {100*row['amp']:>5.1f}% "
            f"{row['qs']:>3} {row['mix22']:>6.0f} {row['mix25']:>6.0f} "
            f"{row['poke22']:>6.0f}"
        )

    lines.append("")
    lines.append("-" * 80)
    lines.append("STACKING OPENER  (ER last-hit first, then extra AH — T3 clock)")
    lines.append("-" * 80)
    lines.append("  ER 20 AH does not move farm Qs enough. Last-hit rel needs ER;")
    lines.append("  extra AH after ER (Ionian + Shojin / Navori / Haste) is the dump.")
    lines.append(
        f"  {'Opener':<42} {'T3':>3} {'AH8':>4} {'Q/m8':>5} "
        f"{'St8':>4} {'St12':>5} {'St16':>5} {'Mix16':>6} {'Mix22':>6}"
    )
    stack_rank = []
    for name, snaps in stack_results.items():
        t3 = first_minute_with(snaps, lambda s: s.stacks >= 175)
        row = (
            name,
            t3 or 25,
            snaps[7].ah,
            farm_qpm(snaps[7]),
            snaps[7].stacks,
            snaps[11].stacks,
            snaps[15].stacks,
            mix_of(snaps[15]),
            mix_of(snaps[21]),
            snaps,
        )
        stack_rank.append(row)
        lines.append(
            f"  {name:<42} {t3 or 0:>3} {snaps[7].ah:>4.0f} {farm_qpm(snaps[7]):>5.1f} "
            f"{snaps[7].stacks:>4} {snaps[11].stacks:>5} {snaps[15].stacks:>5} "
            f"{mix_of(snaps[15]):>6.0f} {mix_of(snaps[21]):>6.0f}"
        )
    # Best stacking: earlier T3, then stacks@16. Mix@22 is the tax.
    stack_rank.sort(key=lambda r: (r[1], -r[6], -r[7]))
    best_stack = stack_rank[0] if stack_rank else None
    base_stack = stack_results.get("IE 2nd / Bloodline")
    haste_only = stack_results.get("IE 2nd / Haste")
    sho_h = stack_results.get("Shojin 2nd / Haste")
    ion_first = stack_results.get("Ionian before ER / Shojin / Haste")
    cau_first = stack_results.get("Caulfield+Ionian opener / Shojin / Haste")
    nav_h = stack_results.get("Navori 2nd / Haste")
    if base_stack and sho_h:
        t3_b = first_minute_with(base_stack, lambda s: s.stacks >= 175)
        t3_s = first_minute_with(sho_h, lambda s: s.stacks >= 175)
        lines.append("")
        lines.append("  Isolated:")
        lines.append(
            f"    IE 2nd / Bloodline  T3 ~{t3_b}:00  "
            f"stacks@16 {base_stack[15].stacks}  Q/min@8 {farm_qpm(base_stack[7]):.1f}"
        )
        if haste_only:
            t3_h = first_minute_with(haste_only, lambda s: s.stacks >= 175)
            lines.append(
                f"    IE 2nd / Haste      T3 ~{t3_h}:00  "
                f"stacks@16 {haste_only[15].stacks}  "
                f"(rune AH only, still 25% crit Q until Hex)"
            )
        lines.append(
            f"    Shojin 2nd / Haste  T3 ~{t3_s}:00  "
            f"stacks@16 {sho_h[15].stacks}  Q/min@8 {farm_qpm(sho_h[7]):.1f}  "
            f"mix22 {mix_of(sho_h[21]):.0f} vs IE-2nd {mix_of(base_stack[21]):.0f}"
        )
        if ion_first:
            t3_i = first_minute_with(ion_first, lambda s: s.stacks >= 175)
            lines.append(
                f"    Ionian before ER    T3 ~{t3_i}:00  "
                f"stacks@16 {ion_first[15].stacks}  "
                f"(last-hit rel stays 50% until ER)"
            )
        if cau_first:
            t3_c = first_minute_with(cau_first, lambda s: s.stacks >= 175)
            lines.append(
                f"    Caulfield+Ionian    T3 ~{t3_c}:00  "
                f"stacks@16 {cau_first[15].stacks}"
            )
        if nav_h:
            t3_n = first_minute_with(nav_h, lambda s: s.stacks >= 175)
            lines.append(
                f"    Navori 2nd / Haste  T3 ~{t3_n}:00  "
                f"stacks@16 {nav_h[15].stacks}  mix22 {mix_of(nav_h[21]):.0f}"
            )

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
    lines.append("  3) Ionian Boots of Lucidity  — 4th Q. Sit on T2; T3 is not a 5th Q")
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
    lines.append("  ABILITY SCALE vs CRIT SCALE:")
    lines.append("  • Ability scale is the kit ratios + more casts. Q 110% bAD, W ~115%")
    lines.append("    bAD, E 30% AD, R 110% bAD. Shojin 12% multiplies Q/W/E/R. AH")
    lines.append("    buys extra Qs. None of that needs crit.")
    lines.append("  • Crit scale is Super Scorcher + autos. 100% crit + IE is +58.5%")
    lines.append("    on Q physical and 30%→69% of stacks as magic. Autos go to 2.30x.")
    lines.append("    W/E/R do not get that amp — only the AD on the crit items.")
    if ad0 and sho0 and ie100:
        lines.append(
            f"  • Same AD, one Q: Shojin {sho0['one_q']:.0f} ({sho_pct:+.0f}%) vs "
            f"100%+IE {ie100['one_q']:.0f} ({ie_pct:+.0f}%)."
        )
        lines.append(
            f"    Same AD, one W: Shojin {sho0['w_one']:.0f} vs IE {ie100['w_one']:.0f} "
            f"(W ignores crit amp)."
        )
    if scale_paths:
        crit_p = next((p for p in scale_paths if p["key"] == WINNING_ITEMS), None)
        abi_p = next(
            (p for p in scale_paths if "Shojin 2nd" in p["name"]), None
        )
        old_p = next((p for p in scale_paths if "mana" in p["name"]), None)
        if crit_p and abi_p:
            lines.append(
                f"  • Real pages @22: crit {crit_p['mix22']:.0f} vs Shojin-2nd "
                f"{abi_p['mix22']:.0f} ({100.0*(crit_p['mix22']/abi_p['mix22']-1.0):+.0f}%)."
            )
        if crit_p and old_p:
            lines.append(
                f"    Old mana 0% crit Q: {old_p['mix22']:.0f} mix, "
                f"Q amp {100*old_p['amp']:.0f}%."
            )
    lines.append("  • They multiply if you own both, but 100% crit spends 4 slots.")
    lines.append("    Shojin as 3rd after IE if you still want W/E/R amp — not 2nd.")
    lines.append("")
    lines.append("  STACKING OPENER (ER 20 AH is not enough early):")
    lines.append("  • Do not delay Essence Reaver. Without Spellblade last-hit rel is")
    lines.append("    50% — extra Ionian/Caulfield Qs at 50% rel lose farm stacks.")
    lines.append("  • After ER: Ionian immediately, Legend: Haste until T3, Shojin 2nd,")
    lines.append("    then Infinity Edge. That is the Q-count dump. IE 2nd adds 0 farm")
    lines.append("    stacks because casters are already one-shot.")
    if best_stack:
        lines.append(
            f"  • Fastest T3: {best_stack[0]}  ~{best_stack[1]}:00  "
            f"stacks@16 {best_stack[6]}  mix22 {best_stack[8]:.0f}"
        )
    if base_stack and sho_h:
        t3_b = first_minute_with(base_stack, lambda s: s.stacks >= 175)
        t3_s = first_minute_with(sho_h, lambda s: s.stacks >= 175)
        lines.append(
            f"    IE 2nd / Bloodline T3 ~{t3_b}:00 ({base_stack[15].stacks} @16) vs "
            f"Shojin 2nd / Haste T3 ~{t3_s}:00 ({sho_h[15].stacks} @16)."
        )
        lines.append(
            f"    Mix tax @22: {mix_of(sho_h[21]):.0f} vs {mix_of(base_stack[21]):.0f} "
            f"— T3 lands on a 25% crit Q until IE."
        )
    lines.append("  • Swap Haste → Bloodline and finish IE → Hex → LDR after 175.")
    lines.append("  • Navori 2nd refunds farm Qs but 0 AD. Cleaver is AH without Q amp.")
    lines.append("")
    if ie2 and hex2:
        t3_ie2 = first_minute_with(ie2, lambda s: s.stacks >= 175)
        t3_hex2 = first_minute_with(hex2, lambda s: s.stacks >= 175)
        ie2_m = first_minute_with(ie2, lambda s: s.has_ie)
        lines.append("  IE 2ND vs 3RD (stacking):")
        lines.append("  • Essence Reaver already one-shots casters (~8:00). Last-hit")
        lines.append("    reliability is 100%, so IE 2nd adds ~0 farm stacks. Wave")
        lines.append("    stacks are gated by Q count, not Q damage.")
        lines.append("  • Hex 2nd: +2 stacks at 13:00 (safer champion Qs). T3 still 17:00.")
        lines.append("  • Shojin 2nd is the actual stacking purchase (more Qs).")
        if sho2 and ie2_m:
            lines.append(
                f"    {sho2[ie2_m-1].stacks} vs {ie2[ie2_m-1].stacks} stacks at "
                f"{ie2_m}:00; {sho2[15].stacks} vs {ie2[15].stacks} at 16:00."
            )
        if t3_ie2 and t3_hex2:
            lines.append(
                f"  • T3 (175) does not move a full minute: IE 2nd / Hex 2nd / "
                f"Shojin 2nd all ~{t3_ie2}:00."
            )
        if sho2:
            lines.append(
                f"  • Mix at 16:00: IE 2nd {mix_of(ie2[15]):.0f} | Hex 2nd "
                f"{mix_of(hex2[15]):.0f} | Shojin 2nd {mix_of(sho2[15]):.0f}."
            )
            lines.append(
                f"    Mix at 22:00: IE→Hex {mix_of(ie2[21]):.0f} | Hex→IE "
                f"{mix_of(hex2[21]):.0f} (same page) | Shojin→IE "
                f"{mix_of(sho2[21]):.0f} (T3 on a 25% crit Q)."
            )
        lines.append("  • Do not buy IE 2nd to stack. Buy it 2nd to convert stacks into")
        lines.append("    Q damage in the 13–16 window. Hex 2nd is a wash on stacks and")
        lines.append("    a cheaper spike; IE 3rd after Hex hits the same 17:00 T3.")
        lines.append("  • Do not buy Shojin 2nd to stack unless you accept a weak T3")
        lines.append("    fireball. AH as 3rd after IE if you still want extra Qs.")
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
    lines.append("")
    if ion_b:
        lines.append("  BOOTS THAT FIT THIS PAGE:")
        lines.append(f"  {best_boot[1]}")
        lines.append(
            f"    22:00 mix {mix_of(ion_b[21]):.0f} | 25:00 {mix_of(ion_b[24]):.0f} | "
            f"Qs @22 {ion_b[21].q_casts_poke} | AH {ion_b[21].ah:.0f}"
        )
        lines.append("  • Ionian 15 AH is the 4th Super Scorcher in 8s. This page is")
        lines.append("    Q-poke; one extra fireball beats 12 AD and extra autos.")
        if gre_b:
            lines.append(
                f"  • Gluttonous Greaves — 12 AD + 5–10% omnivamp, {gre_b[21].q_casts_poke} Qs. "
                f"Mix {mix_of(gre_b[21]):.0f} vs {mix_of(ion_b[21]):.0f}."
            )
            lines.append("    The page already has Bloodline 7% omnivamp (heals Q magic")
            lines.append("    + true burn). Greaves only if you are diving and dying.")
        if imm_b:
            ie_ion = first_minute_with(ion_b, lambda s: s.has_ie)
            ie_imm = first_minute_with(imm_b, lambda s: s.has_ie)
            lines.append(
                f"  • Immortal Treads — same 12 AD + vamp, plus 5% damage above 50% HP. "
                f"Still {imm_b[21].q_casts_poke} Qs."
            )
            lines.append(
                f"    22:00 mix {mix_of(imm_b[21]):.0f}. IE ~{ie_imm}:00 vs Ionian "
                f"~{ie_ion}:00 — the extra 1000g delays the capstone."
            )
            lines.append("    Take Immortal after the core if you are already on Greaves")
            lines.append("    and fighting healthy tanks. Do not buy it to skip Ionian.")
        if cri_b:
            ie_cri = first_minute_with(cri_b, lambda s: s.has_ie)
            lines.append(
                f"  • Crimson Lucidity — 25 AH, still {cri_b[21].q_casts_poke} Qs in 8s "
                f"(need ~90 AH for a 5th)."
            )
            lines.append(
                f"    Mix {mix_of(cri_b[21]):.0f}. IE ~{ie_cri}:00. Sit on T2 Ionian;"
            )
            lines.append("    upgrade only with leftover gold after LDR/BT.")
        if ber_b and gun_b:
            lines.append(
                f"  • Berserker's / Gunmetal — {ber_b[21].q_casts_poke} Qs. Fight-tank "
                f"{ber_b[21].fight_tank:.0f} / {gun_b[21].fight_tank:.0f} vs "
                f"Ionian {ion_b[21].fight_tank:.0f}."
            )
            lines.append("    Hexoptics poke does not auto. Gunmetal 5% LS is physical;")
            lines.append("    Q magic + T3 true burn do not heal from it.")
        lines.append("  • Mercury's / Steelcaps are the CC / all-in-AD swaps. 0 extra Qs.")
    lines.append("=" * 80)
    return "\n".join(lines)


def export_json(
    results,
    timeline,
    rune_results,
    boot_results,
    scale_lab,
    scale_paths,
    stack_results,
    path: str,
) -> None:
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
        "boots": {
            name: [
                {
                    "minute": s.minute,
                    "items": s.items,
                    "mix_tank": s.mix_tank,
                    "mix_squish": s.mix_squish,
                    "poke_squish": s.poke_squish,
                    "fight_tank": s.fight_tank,
                    "q_casts_poke": s.q_casts_poke,
                    "ah": s.ah,
                    "as_pct": s.as_pct,
                    "ad": s.ad,
                    "stacks": s.stacks,
                    "notes": s.notes,
                }
                for s in snaps
            ]
            for name, snaps in boot_results.items()
        },
        "scale_lab": scale_lab,
        "scale_paths": scale_paths,
        "stacking": {
            name: [
                {
                    "minute": s.minute,
                    "items": s.items,
                    "stacks": s.stacks,
                    "ah": s.ah,
                    "q_casts_poke": s.q_casts_poke,
                    "mix_tank": s.mix_tank,
                    "mix_squish": s.mix_squish,
                    "notes": s.notes,
                }
                for s in snaps
            ]
            for name, snaps in stack_results.items()
        },
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def self_check(
    results: Dict[str, List[Snapshot]],
    rune_results: Dict[str, List[Snapshot]],
    boot_results: Dict[str, List[Snapshot]],
    scale_lab: List[dict],
    stack_results: Dict[str, List[Snapshot]],
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

    ie2 = results["ER → IE → Hex → LDR → BT"]
    hex2 = results["ER → Hex → IE → LDR → BT"]
    sho2 = results["ER → Shojin → IE → Hex → LDR"]
    assert sho2[15].stacks >= ie2[15].stacks
    t3_ie = first_minute_with(ie2, lambda s: s.stacks >= 175)
    t3_hex = first_minute_with(hex2, lambda s: s.stacks >= 175)
    assert t3_ie is not None and t3_hex is not None
    assert abs(t3_ie - t3_hex) <= 1

    fit = rune_results["Fleet / Zeal / Cut Down / Haste / Transcendence"]
    coup = rune_results["Fleet / Zeal / Coup / Haste / Transcendence"]
    blood = rune_results["Fleet / Zeal / Cut Down / Bloodline / Transcendence"]
    assert fit[24].poke_squish >= coup[24].poke_squish, (
        fit[24].poke_squish,
        coup[24].poke_squish,
    )
    assert fit[21].q_casts_poke >= blood[21].q_casts_poke
    assert fit[24].crit100

    ion = boot_results["Ionian Boots of Lucidity"]
    gre = boot_results["Gluttonous Greaves"]
    imm = boot_results["Immortal Treads"]
    cri = boot_results["Crimson Lucidity"]
    ber = boot_results["Berserker's Greaves"]
    assert ion[21].q_casts_poke > gre[21].q_casts_poke
    assert mix_of(ion[21]) > mix_of(gre[21])
    assert ion[21].q_casts_poke >= ber[21].q_casts_poke
    assert ion[21].q_casts_poke >= cri[21].q_casts_poke
    ie_ion = first_minute_with(ion, lambda s: s.has_ie)
    ie_imm = first_minute_with(imm, lambda s: s.has_ie)
    assert ie_ion is not None and ie_imm is not None
    assert ie_ion <= ie_imm

    by_name = {r["name"]: r for r in scale_lab}
    ad0 = by_name["AD ratios only (0% crit)"]
    sho0 = by_name["Shojin 12%, 0% crit"]
    ie100 = by_name["100% crit + IE"]
    assert abs(ie100["amp"] - 0.585) < 0.001
    assert ie100["one_q"] > sho0["one_q"] > ad0["one_q"]
    # W/E/R ignore Q crit amp; Shojin still multiplies W.
    assert abs(ie100["w_one"] - ad0["w_one"]) < 1.0
    assert sho0["w_one"] > ad0["w_one"] * 1.10

    ie_bld = stack_results["IE 2nd / Bloodline"]
    sho_h = stack_results["Shojin 2nd / Haste"]
    ion_first = stack_results["Ionian before ER / Shojin / Haste"]
    assert sho_h[15].stacks >= ie_bld[15].stacks
    # Delaying ER for Ionian should not beat ER→Shojin on farm stacks.
    assert sho_h[15].stacks >= ion_first[15].stacks - 2
    t3_sho = first_minute_with(sho_h, lambda s: s.stacks >= 175)
    t3_ie = first_minute_with(ie_bld, lambda s: s.stacks >= 175)
    assert t3_sho is not None and t3_ie is not None
    assert t3_sho <= t3_ie


def main() -> None:
    results, timeline, _curves = run_all()
    rune_results = run_runes()
    boot_results = run_boots()
    scale_lab, scale_paths = run_scale_lab(results)
    stack_results = run_stacking()
    self_check(results, rune_results, boot_results, scale_lab, stack_results)
    report = summarize(
        results,
        timeline,
        rune_results,
        boot_results,
        scale_lab,
        scale_paths,
        stack_results,
    )
    print(report)
    out_dir = "/workspace/smolder-late-sim"
    with open(f"{out_dir}/report.txt", "w", encoding="utf-8") as f:
        f.write(report + "\n")
    export_json(
        results,
        timeline,
        rune_results,
        boot_results,
        scale_lab,
        scale_paths,
        stack_results,
        f"{out_dir}/results.json",
    )
    print(f"\nWrote {out_dir}/report.txt and {out_dir}/results.json")


if __name__ == "__main__":
    main()
