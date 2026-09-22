#!/usr/bin/env python3
"""
Wild Rift — Statikk Shiv champion suitability (Patch 7.3)

Magnetic Blaster is gone. Shiv is the on-hit teamfight item:
  3000g, 40 AD, 40 AP, 30% AS, 4% MS
  Energized chain lightning bounces 3/4/5/6 (lv 1/5/9/13)
  60 magic (90 vs minions/monsters)
  **Applies on-hit effects to secondary bounce targets**

Question: which champions actually convert that bounce, plus the hybrid
40 AD / 40 AP, well enough to buy it? Rank a top 5.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import json

GAME_MINUTES = 20
FIGHT_SECONDS = 8.0
FIGHT_UPTIME = 0.85  # kiting / CC / repositioning

# ---------------------------------------------------------------------------
# Economy / XP — dragon-lane or solo-lane farmer, same gold for fairness
# ---------------------------------------------------------------------------


def gold_at_minute(m: int) -> int:
    if m <= 0:
        return 500
    total = 500
    for t in range(1, m + 1):
        if t <= 5:
            total += 380
        elif t <= 10:
            total += 490
        else:
            total += 560
    return total


def level_at_minute(m: int) -> int:
    # WR 15-cap. Farmer ~15 at 20:00.
    table = {
        1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7, 7: 8, 8: 8,
        9: 9, 10: 10, 11: 11, 12: 11, 13: 12, 14: 12,
        15: 13, 16: 13, 17: 14, 18: 14, 19: 15, 20: 15,
    }
    return table.get(m, min(15, 1 + m))


def basic_rank(level: int) -> int:
    """Maxed first basic (W for most of these). WR 4 ranks."""
    if level >= 9:
        return 4
    if level >= 6:
        return 3
    if level >= 3:
        return 2
    return 1


def ult_rank(level: int) -> int:
    if level >= 13:
        return 3
    if level >= 9:
        return 2
    if level >= 5:
        return 1
    return 0


def shiv_bounces(level: int) -> int:
    if level >= 13:
        return 6
    if level >= 9:
        return 5
    if level >= 5:
        return 4
    return 3


# ---------------------------------------------------------------------------
# Mitigation
# ---------------------------------------------------------------------------


def mit(amount: float, resist: float, pct_pen: float = 0.0, flat_pen: float = 0.0) -> float:
    eff = max(0.0, resist * (1.0 - pct_pen) - flat_pen)
    return amount * 100.0 / (100.0 + eff)


# ---------------------------------------------------------------------------
# Items (7.3 patch notes)
# ---------------------------------------------------------------------------


@dataclass
class Item:
    name: str
    cost: int
    ad: float = 0
    ap: float = 0
    as_pct: float = 0
    ms_pct: float = 0
    ah: float = 0
    flat_mpen: float = 0
    pct_pen: float = 0  # terminus dark / last whisper style, applied mixed
    onhit_magic: float = 0
    onhit_magic_ap: float = 0  # extra magic on-hit per AP
    botrk: bool = False
    guinsoo: bool = False
    terminus: bool = False
    nashor: bool = False
    kraken: bool = False
    shiv: bool = False
    tags: Tuple[str, ...] = ()


ITEMS: Dict[str, Item] = {
    "Boots": Item("Boots", 500, tags=("boots",)),
    "Berserker's Greaves": Item(
        "Berserker's Greaves", 1000, as_pct=0.35, tags=("boots",)
    ),
    "Boots of Mana": Item(
        "Boots of Mana", 1200, ap=25, flat_mpen=8, tags=("boots",)
    ),
    "Dagger": Item("Dagger", 400, as_pct=0.12),
    "Long Sword": Item("Long Sword", 500, ad=15),
    "Pickaxe": Item("Pickaxe", 800, ad=20),
    "Kircheis Shard": Item("Kircheis Shard", 800, as_pct=0.20),
    "Aether Wisp": Item("Aether Wisp", 950, ap=30, ms_pct=0.05),
    "Amplifying Tome": Item("Amplifying Tome", 500, ap=20),
    "Recurve Bow": Item("Recurve Bow", 900, as_pct=0.20),
    "Hearthbound Axe": Item("Hearthbound Axe", 1200, ad=20, as_pct=0.15),
    "Blasting Wand": Item("Blasting Wand", 800, ap=45),
    "Fiendish Codex": Item("Fiendish Codex", 900, ap=35, ah=10),
    "Negatron Cloak": Item("Negatron Cloak", 900),
    "Vampiric Scepter": Item("Vampiric Scepter", 1200, ad=20),
    "Statikk Shiv": Item(
        "Statikk Shiv",
        3000,
        ad=40,
        ap=40,
        as_pct=0.30,
        ms_pct=0.04,
        shiv=True,
        tags=("shiv",),
    ),
    "Guinsoo's Rageblade": Item(
        "Guinsoo's Rageblade",
        3000,
        ad=35,
        ap=30,
        onhit_magic=30,
        guinsoo=True,
        tags=("onhit",),
    ),
    "Terminus": Item(
        "Terminus",
        3000,
        ad=35,
        as_pct=0.35,
        onhit_magic=30,
        terminus=True,
        pct_pen=0.10,  # ~1 stack averaged over the window; 3 stacks = 30%
        tags=("onhit",),
    ),
    "Nashor's Tooth": Item(
        "Nashor's Tooth",
        2900,
        ap=80,
        as_pct=0.50,
        ah=15,
        onhit_magic=15,
        onhit_magic_ap=0.20,
        nashor=True,
        tags=("onhit",),
    ),
    "Blade of the Ruined King": Item(
        "Blade of the Ruined King",
        3100,
        ad=40,  # 7.3 didn't reprint AD; keep pre-patch 40
        as_pct=0.30,
        botrk=True,
        tags=("onhit",),
    ),
    "Wit's End": Item(
        "Wit's End",
        2800,
        as_pct=0.50,
        onhit_magic=40,
        tags=("onhit",),
    ),
    "Kraken Slayer": Item(
        "Kraken Slayer",
        2900,
        ad=45,
        as_pct=0.35,
        ms_pct=0.04,
        kraken=True,
        tags=("alt",),
    ),
    # Stat-stick control: same 40 AD / 30% AS / 4% MS, no AP, no bounce.
    "Shiv Stick": Item(
        "Shiv Stick",
        3000,
        ad=40,
        as_pct=0.30,
        ms_pct=0.04,
        tags=("control",),
    ),
}


UPGRADE_COMPONENTS: Dict[str, Tuple[str, ...]] = {
    "Berserker's Greaves": ("Boots",),
    "Boots of Mana": ("Boots",),
    "Statikk Shiv": ("Aether Wisp", "Pickaxe", "Kircheis Shard"),
    "Shiv Stick": ("Aether Wisp", "Pickaxe", "Kircheis Shard"),
    "Guinsoo's Rageblade": ("Amplifying Tome", "Recurve Bow", "Pickaxe"),
    "Terminus": ("Recurve Bow", "Hearthbound Axe"),
    "Nashor's Tooth": ("Recurve Bow", "Blasting Wand", "Fiendish Codex"),
    "Kraken Slayer": ("Recurve Bow", "Hearthbound Axe", "Long Sword"),
    "Blade of the Ruined King": ("Vampiric Scepter", "Pickaxe", "Recurve Bow"),
    "Wit's End": ("Recurve Bow", "Negatron Cloak", "Dagger"),
}

NEXT_COMPONENTS: Dict[str, List[str]] = {
    "Berserker's Greaves": ["Boots"],
    "Boots of Mana": ["Boots"],
    "Statikk Shiv": ["Kircheis Shard", "Pickaxe", "Aether Wisp"],
    "Shiv Stick": ["Kircheis Shard", "Pickaxe", "Aether Wisp"],
    "Guinsoo's Rageblade": ["Recurve Bow", "Pickaxe", "Amplifying Tome"],
    "Terminus": ["Recurve Bow", "Hearthbound Axe"],
    "Nashor's Tooth": ["Recurve Bow", "Fiendish Codex", "Blasting Wand"],
    "Kraken Slayer": ["Recurve Bow", "Hearthbound Axe", "Long Sword"],
    "Blade of the Ruined King": ["Recurve Bow", "Vampiric Scepter", "Pickaxe"],
    "Wit's End": ["Recurve Bow", "Dagger", "Negatron Cloak"],
}


# ---------------------------------------------------------------------------
# Inventory
# ---------------------------------------------------------------------------


def resolve_inventory(path: List[str], gold: int) -> List[Item]:
    owned: List[str] = []
    pool = gold

    def credit_for(name: str) -> Tuple[int, List[str]]:
        credit = 0
        remove: List[str] = []
        for c in UPGRADE_COMPONENTS.get(name, ()):
            if c in owned:
                credit += ITEMS[c].cost
                remove.append(c)
        return credit, remove

    def remaining(name: str) -> int:
        credit, _ = credit_for(name)
        return max(0, ITEMS[name].cost - credit)

    def buy(name: str) -> bool:
        nonlocal pool
        if name in owned:
            return False
        cost = remaining(name)
        if cost > pool:
            return False
        _, remove = credit_for(name)
        pool -= cost
        for r in remove:
            owned.remove(r)
        owned.append(name)
        return True

    blocked: Optional[str] = None
    for step in path:
        if step in owned:
            continue
        if remaining(step) <= pool:
            buy(step)
        else:
            blocked = step
            break

    if blocked and blocked in NEXT_COMPONENTS:
        for comp in NEXT_COMPONENTS[blocked]:
            if comp not in owned and pool >= ITEMS[comp].cost:
                buy(comp)
        if remaining(blocked) <= pool:
            buy(blocked)
            seen = False
            for step in path:
                if step == blocked:
                    seen = True
                    continue
                if not seen or step in owned:
                    continue
                if remaining(step) <= pool:
                    buy(step)
                else:
                    for comp in NEXT_COMPONENTS.get(step, []):
                        if comp not in owned and pool >= ITEMS[comp].cost:
                            buy(comp)
                    if remaining(step) <= pool:
                        buy(step)
                    else:
                        break

    # drop base boots once upgraded
    if "Berserker's Greaves" in owned and "Boots" in owned:
        owned.remove("Boots")
    if "Boots of Mana" in owned and "Boots" in owned:
        owned.remove("Boots")
    return [ITEMS[n] for n in owned]


# ---------------------------------------------------------------------------
# Targets — 4-champion clump (dragon / Baron pit)
# ---------------------------------------------------------------------------


@dataclass
class Target:
    name: str
    hp: float
    armor: float
    mr: float
    current_hp_frac: float = 0.75


def clump_at(m: int) -> List[Target]:
    lv = level_at_minute(m)
    return [
        Target("tank", 750 + 110 * lv + 70 * m, 45 + 3.2 * lv + 8 * max(0, m - 8), 40 + 2.2 * lv + 6 * max(0, m - 8), 0.80),
        Target("bruiser", 680 + 100 * lv + 40 * m, 40 + 2.8 * lv + 4 * max(0, m - 8), 36 + 1.8 * lv + 3 * max(0, m - 8), 0.75),
        Target("squish", 600 + 90 * lv + 18 * m, 32 + 2.0 * lv + 1.5 * max(0, m - 10), 32 + 1.4 * lv + 1.2 * max(0, m - 10), 0.70),
        Target("squish", 580 + 88 * lv + 16 * m, 32 + 2.0 * lv + 1.5 * max(0, m - 10), 32 + 1.4 * lv + 1.2 * max(0, m - 10), 0.70),
    ]


# ---------------------------------------------------------------------------
# Champion kits
# ---------------------------------------------------------------------------


@dataclass
class Champ:
    name: str
    role: str
    # stats
    base_ad: float
    ad_growth: float
    base_as: float
    as_ratio: float
    as_growth: float  # per level as decimal (0.03 = 3%)
    base_bonus_as: float
    # how much of Shiv's 40 AP is "wanted" (0–1)
    ap_want: float
    # does kit on-hit apply to Shiv bounces?
    kit_bounces: bool
    notes: str
    # build path (forced Shiv first legendary)
    shiv_path: List[str]
    stick_path: List[str]
    kraken_path: List[str]


# Shared on-hit cores. AP casters swap Terminus for Nashor.
ADC_SHIV = [
    "Boots",
    "Kircheis Shard",
    "Berserker's Greaves",
    "Statikk Shiv",
    "Recurve Bow",
    "Guinsoo's Rageblade",
    "Terminus",
    "Blade of the Ruined King",
]
ADC_STICK = [
    "Boots",
    "Kircheis Shard",
    "Berserker's Greaves",
    "Shiv Stick",
    "Recurve Bow",
    "Guinsoo's Rageblade",
    "Terminus",
    "Blade of the Ruined King",
]
ADC_KRAKEN = [
    "Boots",
    "Recurve Bow",
    "Berserker's Greaves",
    "Kraken Slayer",
    "Guinsoo's Rageblade",
    "Terminus",
    "Blade of the Ruined King",
]
AP_SHIV = [
    "Boots",
    "Kircheis Shard",
    "Boots of Mana",
    "Statikk Shiv",
    "Recurve Bow",
    "Nashor's Tooth",
    "Guinsoo's Rageblade",
    "Terminus",
]
AP_STICK = [
    "Boots",
    "Kircheis Shard",
    "Boots of Mana",
    "Shiv Stick",
    "Recurve Bow",
    "Nashor's Tooth",
    "Guinsoo's Rageblade",
    "Terminus",
]
AP_KRAKEN = [
    "Boots",
    "Recurve Bow",
    "Boots of Mana",
    "Kraken Slayer",
    "Nashor's Tooth",
    "Guinsoo's Rageblade",
    "Terminus",
]


CHAMPS: List[Champ] = [
    Champ(
        "Kog'Maw",
        "ADC",
        54, 3.5, 0.665, 0.665, 0.027, 0.20,
        ap_want=0.95,
        kit_bounces=True,
        notes="W Bio-Arcane is %max HP on-hit for 8s. Bounce copies W onto the whole pit.",
        shiv_path=ADC_SHIV,
        stick_path=ADC_STICK,
        kraken_path=ADC_KRAKEN,
    ),
    Champ(
        "Varus",
        "ADC",
        54, 3.6, 0.658, 0.625, 0.032, 0.205,
        ap_want=1.00,
        kit_bounces=True,
        notes="W on-hit + Blight stacks bounce, then one Q detonates the clump. Innate turns AS into AD+AP.",
        shiv_path=ADC_SHIV,
        stick_path=ADC_STICK,
        kraken_path=ADC_KRAKEN,
    ),
    Champ(
        "Kalista",
        "ADC",
        54, 4.5, 0.694, 0.694, 0.032, 0.205,
        ap_want=0.10,
        kit_bounces=True,
        notes="Rend spears bounce; one E rips the whole clump. 40 AP is mostly wasted.",
        shiv_path=ADC_SHIV,
        stick_path=ADC_STICK,
        kraken_path=ADC_KRAKEN,
    ),
    Champ(
        "Teemo",
        "Top/Mid",
        52, 3.6, 0.690, 0.690, 0.022, 0.125,
        ap_want=1.00,
        kit_bounces=True,
        notes="Toxic Shot on-hit + 4s poison bounce. 40 AP is fully spent. Nashor core.",
        shiv_path=AP_SHIV,
        stick_path=AP_STICK,
        kraken_path=AP_KRAKEN,
    ),
    Champ(
        "Kai'Sa",
        "ADC",
        59, 3.5, 0.644, 0.644, 0.032, 0.125,
        ap_want=0.90,
        kit_bounces=True,
        notes="Plasma on-hit bounces (7.3 AP ratios). Secondaries rarely reach a 5-stack pop from Shiv alone.",
        shiv_path=ADC_SHIV,
        stick_path=ADC_STICK,
        kraken_path=ADC_KRAKEN,
    ),
    Champ(
        "Kayle",
        "Top/Mid",
        54, 3.0, 0.667, 0.667, 0.022, 0.133,
        ap_want=1.00,
        kit_bounces=True,
        notes="E on-hit + 40/40/30% is her dream stat line. Aflame waves already splash E after 9, so kit overlap.",
        shiv_path=AP_SHIV,
        stick_path=AP_STICK,
        kraken_path=AP_KRAKEN,
    ),
    Champ(
        "Twitch",
        "ADC",
        58, 4.0, 0.679, 0.679, 0.030, 0.20,
        ap_want=0.70,
        kit_bounces=True,
        notes="Venom stacks bounce, then E (7.3 hybrid). Spray and Pray already applies on-hit in a line — overlap.",
        shiv_path=ADC_SHIV,
        stick_path=ADC_STICK,
        kraken_path=ADC_KRAKEN,
    ),
    Champ(
        "Vayne",
        "ADC",
        60, 3.0, 0.658, 0.625, 0.027, 0.205,
        ap_want=0.00,
        kit_bounces=False,
        notes="Silver Bolts do not apply to extra targets (same as Runaan's) and expire on switch. AP wasted.",
        shiv_path=ADC_SHIV,
        stick_path=ADC_STICK,
        kraken_path=ADC_KRAKEN,
    ),
    Champ(
        "Ashe",
        "ADC",
        60, 4.2, 0.658, 0.658, 0.030, 0.22,
        ap_want=0.15,
        kit_bounces=True,
        notes="Frost Shot slow bounces — utility, almost no extra damage. 7.3 Frost bonus is crit-scaled.",
        shiv_path=ADC_SHIV,
        stick_path=ADC_STICK,
        kraken_path=ADC_KRAKEN,
    ),
]


# ---------------------------------------------------------------------------
# Kit on-hit / detonate
# ---------------------------------------------------------------------------


def kog_w_pct(level: int, ap: float) -> float:
    r = basic_rank(level)
    return [0.0, 0.015, 0.025, 0.035, 0.045][r] + 0.015 * ap / 100.0


def varus_w_onhit(level: int, ap: float) -> float:
    r = basic_rank(level)
    return [0.0, 15.0, 25.0, 35.0, 45.0][r] + 0.35 * ap


def varus_blight_pct(level: int, ap: float) -> float:
    r = basic_rank(level)
    return [0.0, 0.030, 0.035, 0.040, 0.045][r] + 0.012 * ap / 100.0


def teemo_onhit(level: int, ap: float) -> float:
    return 8.0 + (36.0 - 8.0) * (level - 1) / 14.0 + 0.20 * ap


def teemo_poison_total(level: int, ap: float) -> float:
    # 4s poison: 11–53 + 9% AP per second
    per_s = 11.0 + (53.0 - 11.0) * (level - 1) / 14.0 + 0.09 * ap
    return per_s * 4.0


def kayle_e_onhit(level: int, bonus_ad: float, ap: float) -> float:
    r = basic_rank(level)
    return [0.0, 8.0, 11.0, 14.0, 17.0][r] + 0.05 * bonus_ad + 0.15 * ap


def kaisa_plasma_hit(level: int, ap: float, stacks_before: int) -> float:
    # 7.3: 4 + 1×lv + 12% AP + current stacks × (1 + 0.2×lv + 2% AP)
    return (
        4.0
        + 1.0 * level
        + 0.12 * ap
        + stacks_before * (1.0 + 0.2 * level + 0.02 * ap)
    )


def kalista_rend(level: int, ad: float, spears: int) -> float:
    r = basic_rank(level)
    base = [0.0, 30.0, 45.0, 60.0, 75.0][r] + 0.70 * ad
    extra = [0.0, 12.0, 22.0, 32.0, 42.0][r] + [0.0, 0.36, 0.43, 0.50, 0.57][r] * ad
    extra_n = max(0, spears - 1)
    return base + extra * extra_n


def twitch_e(level: int, bonus_ad: float, ap: float, stacks: int) -> float:
    # 7.3: 30/40/50/60 + per stack (20–35 + 35% bAD) phys + 35% AP magic
    r = basic_rank(level)
    base = [0.0, 30.0, 40.0, 50.0, 60.0][r]
    per_phys = [0.0, 20.0, 25.0, 30.0, 35.0][r] + 0.35 * bonus_ad
    per_magic = 0.35 * ap
    return base + stacks * (per_phys + per_magic)


def twitch_venom_total(level: int, ap: float, stacks: int) -> float:
    # 7.3: 1–5 + 3% AP true per stack per second over 5s
    per = (1.0 + (5.0 - 1.0) * (level - 1) / 14.0 + 0.03 * ap) * stacks * 5.0
    return per


def vayne_w_true(level: int, hp: float) -> float:
    r = basic_rank(level)
    # 7.3: 6/7/8/9% max HP
    pct = [0.0, 0.06, 0.07, 0.08, 0.09][r]
    return pct * hp


# ---------------------------------------------------------------------------
# Combat
# ---------------------------------------------------------------------------


@dataclass
class BuildStats:
    names: List[str]
    ad: float
    bonus_ad: float
    ap: float
    as_pct: float
    flat_mpen: float
    pct_pen: float
    onhit_magic: float
    botrk: bool
    guinsoo: bool
    terminus: bool
    nashor: bool
    kraken: bool
    shiv: bool


def tally(champ: Champ, items: List[Item], level: int) -> BuildStats:
    ad = champ.base_ad + champ.ad_growth * (level - 1)
    ap = 0.0
    as_pct = champ.base_bonus_as + champ.as_growth * (level - 1)
    flat_mpen = 0.0
    pct_pen = 0.0
    onhit_m = 0.0
    flags = dict(botrk=False, guinsoo=False, terminus=False, nashor=False, kraken=False, shiv=False)
    names = []
    for it in items:
        names.append(it.name)
        ad += it.ad
        ap += it.ap
        as_pct += it.as_pct
        flat_mpen += it.flat_mpen
        pct_pen += it.pct_pen
        if it.botrk:
            flags["botrk"] = True
        if it.guinsoo:
            flags["guinsoo"] = True
        if it.terminus:
            flags["terminus"] = True
        if it.nashor:
            flags["nashor"] = True
        if it.kraken:
            flags["kraken"] = True
        if it.shiv:
            flags["shiv"] = True
    for it in items:
        onhit_m += it.onhit_magic + it.onhit_magic_ap * ap
    bonus_ad = ad - (champ.base_ad + champ.ad_growth * (level - 1))
    # Varus Living Vengeance: +AD/AP = 10% of bonus AS (lane), 20% on takedown.
    # Model a mid fight with the lesser (minion) convert always on, half a takedown.
    if champ.name == "Varus":
        # as_pct is already decimal; 0.80 AS → 0.80 * 0.15 * 100 = 12 AD/AP
        gained = as_pct * 0.15 * 100.0
        ad += gained
        bonus_ad += gained
        ap += gained
    return BuildStats(
        names=names,
        ad=ad,
        bonus_ad=bonus_ad,
        ap=ap,
        as_pct=as_pct,
        flat_mpen=flat_mpen,
        pct_pen=pct_pen,
        onhit_magic=onhit_m,
        **flags,
    )


def attacks_in_fight(champ: Champ, st: BuildStats, level: int) -> float:
    total_as = champ.base_as + champ.as_ratio * st.as_pct
    if st.guinsoo:
        # 4×8% AS after a couple hits — average ~24% extra AS over the window
        total_as += champ.as_ratio * 0.24
    if champ.name == "Kog'Maw":
        total_as += champ.as_ratio * [0.0, 0.05, 0.10, 0.15, 0.20][basic_rank(level)]
    if champ.name == "Kayle":
        # Zealous stacks: up to 20–35% + 5% per 100 AP. Average ~80% of cap.
        cap = [0.20, 0.20, 0.25, 0.30, 0.35][min(4, (level - 1) // 4)] + 0.05 * st.ap / 100.0
        if level >= 13:
            total_as += champ.as_ratio * cap
        else:
            total_as += champ.as_ratio * cap * 0.80
    if champ.name == "Twitch":
        # 7.3 Ambush: 35–50% AS for 6s after leaving camo. Fight starts from stealth ~half the time.
        amb = [0.35, 0.35, 0.40, 0.45, 0.50][min(4, (level - 1) // 4)]
        total_as += champ.as_ratio * amb * 0.55
    total_as = min(3.0, total_as)
    return total_as * FIGHT_SECONDS * FIGHT_UPTIME


def energized_count(attacks: float, has_shiv: bool) -> float:
    if not has_shiv:
        return 0.0
    # Attacks grant +5 Energized; movement fills the rest.
    # With the +5, ~1 proc per 4.2 autos while kiting.
    return min(attacks / 4.2, attacks)


def item_onhit(st: BuildStats, tgt: Target) -> float:
    dmg = 0.0
    if st.onhit_magic:
        dmg += mit(st.onhit_magic, tgt.mr, st.pct_pen, st.flat_mpen)
    if st.botrk:
        dmg += mit(0.07 * tgt.hp * tgt.current_hp_frac, tgt.armor, st.pct_pen, 0.0)
    return dmg


def kit_onhit(champ: Champ, st: BuildStats, level: int, tgt: Target, bounce: bool) -> float:
    """Instant kit on-hit on this target. Bounce=False is the auto you actually fired."""
    if bounce and not champ.kit_bounces:
        return 0.0
    dmg = 0.0
    if champ.name == "Kog'Maw":
        dmg += mit(kog_w_pct(level, st.ap) * tgt.hp, tgt.mr, st.pct_pen, st.flat_mpen)
        # Q shred ~20–32% — already in fight, fold a slice into mit via extra pct_pen
        shred = [0.0, 0.16, 0.20, 0.24, 0.28][basic_rank(level)]
        # re-mit with shred (approximate: extra 8% damage vs typical MR)
        dmg *= 1.0 + shred * 0.45
    elif champ.name == "Varus":
        dmg += mit(varus_w_onhit(level, st.ap), tgt.mr, st.pct_pen, st.flat_mpen)
    elif champ.name == "Teemo":
        dmg += mit(teemo_onhit(level, st.ap), tgt.mr, st.pct_pen, st.flat_mpen)
    elif champ.name == "Kayle":
        hit = kayle_e_onhit(level, st.bonus_ad, st.ap)
        # After 9, Aflame waves already deal E passive in a line (~1.5 extra).
        # Bounce kit-on-hit is partly redundant; item on-hits still fully apply.
        if bounce and level >= 9:
            hit *= 0.35
        dmg += mit(hit, tgt.mr, st.pct_pen, st.flat_mpen)
    elif champ.name == "Kai'Sa":
        # Primary: 4 autos typical before first energized, so stacks climb.
        # Bounce: only energized hits, so stacks_before ≈ 0 then 1.
        stacks_before = 2 if not bounce else 0
        dmg += mit(kaisa_plasma_hit(level, st.ap, stacks_before), tgt.mr, st.pct_pen, st.flat_mpen)
    elif champ.name == "Twitch":
        # Venom is a DoT; instant on-hit is just the stack application (no burst).
        pass
    elif champ.name == "Kalista":
        pass  # Rend is the detonate
    elif champ.name == "Vayne":
        if not bounce:
            # Every 3rd auto on the focused target
            dmg += vayne_w_true(level, tgt.hp) / 3.0
    elif champ.name == "Ashe":
        # 7.3 Frost bonus is crit-scaled, not a real on-hit package.
        dmg += mit(0.04 * st.ad, tgt.armor, st.pct_pen, 0.0)
    return dmg


def detonate_bonus(
    champ: Champ,
    st: BuildStats,
    level: int,
    tgt: Target,
    extra_stacks: float,
) -> float:
    """Ability detonate that consumes stacks Shiv put on this target."""
    if extra_stacks <= 0:
        return 0.0
    if champ.name == "Varus":
        # One charged-ish Q (~25% bonus) detonates blight. Extra stacks only.
        pct = varus_blight_pct(level, st.ap) * extra_stacks * 1.25
        return mit(pct * tgt.hp, tgt.mr, st.pct_pen, st.flat_mpen)
    if champ.name == "Kalista":
        # Compare E with (primary spears + extra) vs primary-only, but here
        # we only add the extra spears Shiv lodged in this target.
        # If this target was never auto'd, extra_stacks is the full spear count.
        spears = max(1, int(round(extra_stacks)))
        full = kalista_rend(level, st.ad, spears)
        # Physical
        return mit(full, tgt.armor, st.pct_pen, 0.0)
    if champ.name == "Twitch":
        # E hits anyone with venom. Extra stacks on people you didn't focus.
        # Twitch R already multi-hits — discount 40% after ult rank exists.
        raw = twitch_e(level, st.bonus_ad, st.ap, extra_stacks)
        # Split roughly 70% phys / 30% magic after 7.3 hybrid E
        phys = mit(raw * 0.70, tgt.armor, st.pct_pen, 0.0)
        mag = mit(raw * 0.30, tgt.mr, st.pct_pen, st.flat_mpen)
        # poison ticks on those extra stacks
        poison = twitch_venom_total(level, st.ap, extra_stacks)
        disc = 0.60 if ult_rank(level) >= 1 else 1.0  # R overlap
        return (phys + mag + poison) * disc
    if champ.name == "Teemo":
        return mit(teemo_poison_total(level, st.ap), tgt.mr, st.pct_pen, st.flat_mpen)
    if champ.name == "Kai'Sa":
        # Secondaries only get energized plasmas (~2). No 5-stack pop.
        # Extra plasma hits beyond the first are already in kit_onhit.
        return 0.0
    return 0.0


def kraken_proc(st: BuildStats, attacks: float, tgt: Target) -> float:
    if not st.kraken:
        return 0.0
    procs = attacks / 3.0
    # 7.3 ranged Bring It Down ~120–168, +0.75% per 1% missing, up to 75%
    missing = 1.0 - tgt.current_hp_frac
    base = 144.0 * (1.0 + 0.75 * missing)
    return procs * mit(base, tgt.armor, st.pct_pen, 0.0)


@dataclass
class Fight:
    minute: int
    champ: str
    variant: str
    items: List[str]
    level: int
    gold: int
    ad: float
    ap: float
    attacks: float
    energized: float
    bounce_targets: float
    primary_dmg: float
    bounce_dmg: float
    detonate_dmg: float
    total: float
    shiv_online: bool
    notes: str


def simulate_fight(champ: Champ, path: List[str], minute: int, variant: str) -> Fight:
    gold = gold_at_minute(minute)
    level = level_at_minute(minute)
    inv = resolve_inventory(path, gold)
    st = tally(champ, inv, level)
    targets = clump_at(minute)
    attacks = attacks_in_fight(champ, st, level)
    phantom = 1.0 + (0.33 if st.guinsoo else 0.0)  # extra on-hit on primary
    n_energized = energized_count(attacks, st.shiv)
    extra = min(float(shiv_bounces(level)), float(len(targets) - 1))

    primary = targets[0]
    # Primary: autos + on-hits (phantom) + kraken + shiv lightning on energized
    auto = mit(st.ad, primary.armor, st.pct_pen, 0.0)
    primary_onhit = (item_onhit(st, primary) + kit_onhit(champ, st, level, primary, bounce=False)) * phantom
    primary_dmg = attacks * (auto + primary_onhit)
    primary_dmg += kraken_proc(st, attacks, primary)
    if st.shiv:
        primary_dmg += n_energized * mit(60.0, primary.mr, st.pct_pen, st.flat_mpen)

    # Focused-target detonates happen even without Shiv (you stacked them yourself).
    # Do NOT count those. Only extra stacks on secondary targets.

    bounce_dmg = 0.0
    detonate_dmg = 0.0
    if st.shiv and extra > 0 and n_energized > 0:
        secondaries = targets[1:]
        # Spread extras across the available secondaries, capped by bounce count.
        hit_n = min(int(extra), len(secondaries))
        for tgt in secondaries[:hit_n]:
            lightning = n_energized * mit(60.0, tgt.mr, st.pct_pen, st.flat_mpen)
            bounced_onhit = n_energized * (
                item_onhit(st, tgt) + kit_onhit(champ, st, level, tgt, bounce=True)
            )
            bounce_dmg += lightning + bounced_onhit
            detonate_dmg += detonate_bonus(champ, st, level, tgt, n_energized)

    note_bits = []
    if st.shiv:
        note_bits.append(f"shiv {shiv_bounces(level)}-bounce")
    if st.kraken:
        note_bits.append("kraken")
    if st.guinsoo:
        note_bits.append("rageblade")
    if st.nashor:
        note_bits.append("nashor")
    if st.terminus:
        note_bits.append("terminus")
    if st.botrk:
        note_bits.append("botrk")

    return Fight(
        minute=minute,
        champ=champ.name,
        variant=variant,
        items=st.names,
        level=level,
        gold=gold,
        ad=round(st.ad, 1),
        ap=round(st.ap, 1),
        attacks=round(attacks, 2),
        energized=round(n_energized, 2),
        bounce_targets=extra if st.shiv else 0.0,
        primary_dmg=round(primary_dmg, 1),
        bounce_dmg=round(bounce_dmg, 1),
        detonate_dmg=round(detonate_dmg, 1),
        total=round(primary_dmg + bounce_dmg + detonate_dmg, 1),
        shiv_online=st.shiv,
        notes=", ".join(note_bits) if note_bits else "components",
    )


# ---------------------------------------------------------------------------
# Ranking
# ---------------------------------------------------------------------------


@dataclass
class ChampResult:
    champ: Champ
    shiv: List[Fight]
    stick: List[Fight]
    kraken: List[Fight]


def run_all() -> List[ChampResult]:
    out = []
    for c in CHAMPS:
        shiv = [simulate_fight(c, c.shiv_path, m, "shiv") for m in range(1, GAME_MINUTES + 1)]
        stick = [simulate_fight(c, c.stick_path, m, "stick") for m in range(1, GAME_MINUTES + 1)]
        kraken = [simulate_fight(c, c.kraken_path, m, "kraken") for m in range(1, GAME_MINUTES + 1)]
        out.append(ChampResult(c, shiv, stick, kraken))
    return out


def window(fights: List[Fight], start: int = 10, end: int = 20) -> List[Fight]:
    return [f for f in fights if start <= f.minute <= end]


def score_champ(res: ChampResult) -> dict:
    """
    Suitability = unique Shiv package once the item is online (min 10–20):
      bounce on-hits + lightning + detonates on extras
      PLUS the 40 AP (shiv vs stick, which has the same AD/AS/MS and no AP/bounce)
    Also report vs Kraken so you can see the item-choice, not just the passive.
    """
    sh = window(res.shiv)
    st = window(res.stick)
    kr = window(res.kraken)
    # Only minutes where Shiv finished
    paired = [(a, b, c) for a, b, c in zip(sh, st, kr) if a.shiv_online]
    if not paired:
        unique = 0.0
        vs_kraken = 0.0
        bounce = 0.0
        online_at = None
    else:
        unique = sum((a.total - b.total) for a, b, _ in paired) / len(paired)
        vs_kraken = sum((a.total - c.total) for a, _, c in paired) / len(paired)
        bounce = sum((a.bounce_dmg + a.detonate_dmg) for a, _, _ in paired) / len(paired)
        online_at = next((f.minute for f in res.shiv if f.shiv_online), None)

    # Hybrid waste penalty already lives in unique (stick has no AP).
    # Extra: kit_bounces false heavily nerfs bounce; keep as-is from the model.

    f20_s = res.shiv[19]
    f20_k = res.kraken[19]
    f16_s = res.shiv[15]
    return {
        "name": res.champ.name,
        "role": res.champ.role,
        "ap_want": res.champ.ap_want,
        "kit_bounces": res.champ.kit_bounces,
        "notes": res.champ.notes,
        "online_at": online_at,
        "unique": unique,          # shiv − stick
        "vs_kraken": vs_kraken,    # shiv − kraken
        "bounce_pkg": bounce,      # bounce + detonate only
        "total_20": f20_s.total,
        "kraken_20": f20_k.total,
        "bounce_20": f20_s.bounce_dmg + f20_s.detonate_dmg,
        "total_16": f16_s.total,
        "energized_20": f20_s.energized,
        "items_20": f20_s.items,
        "ad_20": f20_s.ad,
        "ap_20": f20_s.ap,
        "attacks_20": f20_s.attacks,
    }


def summarize(results: List[ChampResult]) -> str:
    rows = [score_champ(r) for r in results]
    rows.sort(key=lambda x: (x["unique"], x["bounce_pkg"], x["vs_kraken"]), reverse=True)

    lines: List[str] = []
    a = lines.append
    a("=" * 78)
    a("WILD RIFT — STATIKK SHIV SUITABILITY  (Patch 7.3)")
    a("Playstyle: 8s dragon-pit clump (4 champs) | Game length: 20:00")
    a("Metric: unique Shiv package = bounce on-hits + 40 AP  (Shiv − stat stick)")
    a("=" * 78)
    a("")
    a("ITEM (7.3 rework)")
    a("  3000g · 40 AD · 40 AP · 30% AS · 4% MS")
    a("  Energized lightning bounces 3/4/5/6 (lv 1/5/9/13), 60 magic")
    a("  Applies on-hit effects to secondary bounce targets.")
    a("  Magnetic Blaster removed — this is the on-hit teamfight item.")
    a("")
    a("GOLD / LEVEL (farmer)")
    a(f"  {'Min':>3}  {'Gold':>6}  {'Lvl':>3}  {'Bounces':>7}")
    for m in (4, 8, 10, 12, 16, 20):
        a(f"  {m:>3}  {gold_at_minute(m):>6}  {level_at_minute(m):>3}  {shiv_bounces(level_at_minute(m)):>7}")

    a("")
    a("-" * 78)
    a("FULL RANKING  (avg unique Shiv damage, minutes 10–20 while item is online)")
    a("-" * 78)
    a(f"  {'#':<3} {'Champion':<12} {'Role':<8} {'Unique':>8} {'Bounce+E':>9} {'vsKraken':>9} {'20:00':>8} {'On':>5}")
    for i, r in enumerate(rows, 1):
        on = f"{r['online_at']}:00" if r["online_at"] else "—"
        a(
            f"  {i:<3} {r['name']:<12} {r['role']:<8} {r['unique']:>8.0f} "
            f"{r['bounce_pkg']:>9.0f} {r['vs_kraken']:>9.0f} {r['total_20']:>8.0f} {on:>5}"
        )

    top5 = rows[:5]
    a("")
    a("-" * 78)
    a("TOP 5 — WHY SHIV")
    a("-" * 78)
    medals = ["1", "2", "3", "4", "5"]
    for i, r in enumerate(top5):
        a(f"  {medals[i]}. {r['name']} ({r['role']})")
        a(f"     Unique Shiv package: {r['unique']:.0f}  |  Bounce+detonate: {r['bounce_pkg']:.0f}  |  vs Kraken: {r['vs_kraken']:+.0f}")
        a(f"     20:00 clump: {r['total_20']:.0f}  (Kraken path {r['kraken_20']:.0f})  AP {r['ap_20']:.0f}  AD {r['ad_20']:.0f}")
        a(f"     Items: {' › '.join(r['items_20'][:6])}")
        a(f"     {r['notes']}")
        a("")

    a("-" * 78)
    a("MINUTE-BY-MINUTE  unique Shiv package (Shiv − stick) for the top 5")
    a("-" * 78)
    name_to = {r.champ.name: r for r in results}
    a(f"  {'Min':>4} " + " ".join(f"{r['name'][:8]:>10}" for r in top5) + "   leader")
    for m in range(8, 21):
        vals = []
        for r in top5:
            sh = name_to[r["name"]].shiv[m - 1]
            st = name_to[r["name"]].stick[m - 1]
            vals.append(sh.total - st.total if sh.shiv_online else 0.0)
        leader = top5[vals.index(max(vals))]["name"] if max(vals) > 0 else "—"
        a("  {:>4} ".format(f"{m}:00") + " ".join(f"{v:>10.0f}" for v in vals) + f"   {leader}")

    a("")
    a("-" * 78)
    a("BOUNCE ANATOMY @ 16:00  (what the lightning actually copies)")
    a("-" * 78)
    a(f"  {'Champion':<12} {'Energ':>6} {'Extra':>6} {'Lightning+OH':>13} {'Detonate':>9} {'Primary':>8}")
    for r in rows:
        f = name_to[r["name"]].shiv[15]
        a(
            f"  {r['name']:<12} {f.energized:>6.1f} {f.bounce_targets:>6.0f} "
            f"{f.bounce_dmg:>13.0f} {f.detonate_dmg:>9.0f} {f.primary_dmg:>8.0f}"
        )

    a("")
    a("-" * 78)
    a("VERDICT")
    a("-" * 78)
    a("  Top 5 Statikk Shiv users (Wild Rift 7.3, on-hit bounce rework):")
    for i, r in enumerate(top5, 1):
        a(f"    {i}) {r['name']}")
    a("")
    a("  WHY THIS ORDER:")
    a("  • Shiv's unique job is copying on-hit onto the people you did not auto.")
    a("  • %HP on-hits (Kog W, Varus Blight) scale with tank HP in a 4-man pit.")
    a("  • Stack-then-detonate kits (Varus Q, Kalista E, Twitch E) cash extras in one spell.")
    a("  • 40 AP is real on Kog / Varus / Teemo / Kayle / Kai'Sa, dead on Vayne / Kalista.")
    a("  • Vayne Silver Bolts do not apply to extra targets (same rule as Runaan's).")
    a("  • Ashe's Frost is a slow, not a damage on-hit — Shiv is a utility toy on her.")
    a("  • vs Kraken: Kraken wins pure single-target. Shiv wins the clump. Buy Shiv")
    a("    when fights are grouped (dragon, Baron, mid siege), not for 1v1 lane.")
    a("")
    a("  RECOMMENDED BUYS when the champ is in the top 5:")
    a("  1) Kircheis Shard + Berserker's (or Boots of Mana on Teemo/Kayle)")
    a("  2) Statikk Shiv (~9–11:00) — bounce comes online")
    a("  3) Guinsoo's Rageblade — phantom hit multiplies the on-hits Shiv copies")
    a("  4) Terminus (AD on-hit) or Nashor's Tooth (AP on-hit)")
    a("  5) BotRK if the frontline is thick")
    a("")
    a("  Trap: buying Shiv on crit ADCs (Jinx, Caitlyn, Miss Fortune, Jhin).")
    a("  They wanted Magnetic Blaster. In 7.3 they want Stormrazor / RFC / IE.")
    a("=" * 78)
    return "\n".join(lines)


def export_json(results: List[ChampResult], ranking: List[dict], path: str) -> None:
    payload = {
        "meta": {
            "item": "Statikk Shiv",
            "patch": "7.3",
            "game": "Wild Rift",
            "game_minutes": GAME_MINUTES,
            "fight_seconds": FIGHT_SECONDS,
            "question": "Which champions convert 7.3 Statikk Shiv's on-hit bounce? Top 5.",
        },
        "ranking": ranking,
        "top5": [r["name"] for r in ranking[:5]],
        "champions": {
            res.champ.name: {
                "role": res.champ.role,
                "notes": res.champ.notes,
                "shiv": [
                    {
                        "minute": f.minute,
                        "items": f.items,
                        "gold": f.gold,
                        "level": f.level,
                        "ad": f.ad,
                        "ap": f.ap,
                        "attacks": f.attacks,
                        "energized": f.energized,
                        "primary_dmg": f.primary_dmg,
                        "bounce_dmg": f.bounce_dmg,
                        "detonate_dmg": f.detonate_dmg,
                        "total": f.total,
                        "shiv_online": f.shiv_online,
                        "notes": f.notes,
                    }
                    for f in res.shiv
                ],
                "kraken": [
                    {
                        "minute": f.minute,
                        "total": f.total,
                        "items": f.items,
                    }
                    for f in res.kraken
                ],
            }
            for res in results
        },
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)


def main() -> None:
    results = run_all()
    ranking = [score_champ(r) for r in results]
    ranking.sort(key=lambda x: (x["unique"], x["bounce_pkg"], x["vs_kraken"]), reverse=True)
    report = summarize(results)
    print(report)
    out_dir = "/workspace/wr-shiv-sim"
    with open(f"{out_dir}/report.txt", "w", encoding="utf-8") as fh:
        fh.write(report + "\n")
    export_json(results, ranking, f"{out_dir}/results.json")
    print(f"\nWrote {out_dir}/report.txt and {out_dir}/results.json")


if __name__ == "__main__":
    main()
