#!/usr/bin/env python3
"""
Wild Rift Senna — Aggressive Dark Harvest Peak Simulation
Patch 7.2+ item / rune values. Average game: 20 minutes.

Playstyle: AGGRESSIVE carry Senna (bot or flex).
  - Constant skirmish / dive pressure
  - Force enemies below 50% HP to proc Dark Harvest
  - Secure takedown resets so DH farms every fight, not every 20s
  - Goal: max Dark Harvest souls + peak execute burst

Dark Harvest (7.2):
  35 + 11*souls + 10% bonus AD + 5% AP  (adaptive)
  20s CD, resets to 1s on champion takedown
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import json

GAME_MINUTES = 20

# ---------------------------------------------------------------------------
# Aggressive gold / XP (ADC-level income, not support)
# ---------------------------------------------------------------------------

def gold_at_minute(m: int) -> int:
    """Aggressive bot/flex Senna: CS + fights + objectives. ~12.5–13.5k @ 20."""
    if m <= 0:
        return 500
    total = 500
    for t in range(1, m + 1):
        if t <= 4:
            total += 380   # lane CS + early all-ins
        elif t <= 10:
            total += 560   # snowball mid skirmishes
        else:
            total += 680   # objective / mid-game fight gold
    return total


def level_at_minute(m: int) -> int:
    # Aggressive ADC XP — higher than support curve
    table = {
        1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7, 7: 8, 8: 9,
        9: 10, 10: 10, 11: 11, 12: 12, 13: 12, 14: 13,
        15: 13, 16: 14, 17: 14, 18: 15, 19: 15, 20: 15,
    }
    return table.get(m, min(15, 2 + m))


def target_max_hp(m: int) -> int:
    # Squishy mid/ADC target Senna wants to execute
    return 580 + 50 * level_at_minute(m) + 18 * m


# ---------------------------------------------------------------------------
# Items (Patch 7.2+ WR)
# ---------------------------------------------------------------------------

@dataclass
class Item:
    name: str
    cost: int
    ad: float = 0
    ah: float = 0
    as_pct: float = 0
    crit: float = 0
    flat_apen: float = 0
    pct_apen: float = 0
    mana: float = 0
    hp: float = 0
    lethality_burst: bool = False   # Draktharr Nightstalker
    collector: bool = False
    muramana: bool = False
    manamune: bool = False
    magnetic: bool = False
    ie: bool = False
    serylda: bool = False
    essence: bool = False
    serpent: bool = False
    cleaver: bool = False
    tags: Tuple[str, ...] = ()


ITEMS: Dict[str, Item] = {
    "Long Sword": Item("Long Sword", 450, ad=12),
    "Boots of Speed": Item("Boots of Speed", 500, tags=("boots",)),
    "Boots of Dynamism": Item(
        "Boots of Dynamism", 900, ad=10, flat_apen=8, tags=("boots",)
    ),
    "Tear of the Goddess": Item("Tear of the Goddess", 800, mana=240),
    "Caulfield's Warhammer": Item("Caulfield's Warhammer", 1100, ad=25, ah=10),
    "Pickaxe": Item("Pickaxe", 1000, ad=25),
    "B.F. Sword": Item("B.F. Sword", 1400, ad=40),
    "Cloak of Agility": Item("Cloak of Agility", 800, crit=0.20),
    "Last Whisper": Item("Last Whisper", 1300, ad=20, pct_apen=0.18),
    "Serrated Dirk": Item("Serrated Dirk", 1100, ad=25, flat_apen=10),
    "Manamune": Item(
        "Manamune", 2700, ad=25, ah=15, mana=500, manamune=True, tags=("mana",)
    ),
    "Muramana": Item(
        "Muramana", 2700, ad=25, ah=20, mana=1000, muramana=True, tags=("mana",)
    ),
    "Duskblade of Draktharr": Item(
        "Duskblade of Draktharr",
        3000,
        ad=55,
        ah=10,
        flat_apen=18,
        lethality_burst=True,
        tags=("lethality", "burst"),
    ),
    "The Collector": Item(
        "The Collector",
        3000,
        ad=45,
        crit=0.25,
        flat_apen=10,
        collector=True,
        tags=("execute", "crit"),
    ),
    "Magnetic Blaster": Item(
        "Magnetic Blaster",
        3000,
        as_pct=0.35,
        crit=0.25,
        magnetic=True,
        tags=("range", "crit"),
    ),
    "Infinity Edge": Item(
        "Infinity Edge", 3400, ad=60, crit=0.25, ie=True, tags=("crit",)
    ),
    "Serylda's Grudge": Item(
        "Serylda's Grudge",
        3300,
        ad=40,
        ah=15,
        pct_apen=0.33,
        serylda=True,
        tags=("pen", "slow"),
    ),
    "Mortal Reminder": Item(
        "Mortal Reminder",
        3300,
        ad=25,
        as_pct=0.15,
        crit=0.25,
        pct_apen=0.30,
        tags=("pen", "antiheal"),
    ),
    "Essence Reaver": Item(
        "Essence Reaver",
        3000,
        ad=35,
        crit=0.25,
        ah=20,
        essence=True,
        tags=("crit", "spellblade"),
    ),
    "Serpent's Fang": Item(
        "Serpent's Fang",
        2800,
        ad=50,
        ah=10,
        flat_apen=15,
        serpent=True,
        tags=("lethality",),
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
    "Umbral Glaive": Item(
        "Umbral Glaive",
        2400,
        ad=45,
        ah=10,
        flat_apen=12,
        tags=("lethality", "vision"),
    ),
}


# ---------------------------------------------------------------------------
# Aggressive build paths (purchase order)
# ---------------------------------------------------------------------------

BUILD_PATHS: Dict[str, List[str]] = {
    # Burst + reset engine — classic aggressive DH Senna
    "Draktharr → Collector → Magnetic (DH Farm)": [
        "Long Sword",
        "Boots of Speed",
        "Serrated Dirk",
        "Duskblade of Draktharr",
        "Boots of Dynamism",
        "The Collector",
        "Magnetic Blaster",
        "Serylda's Grudge",
        "Infinity Edge",
    ],
    # Manamune poke to force <50%, then lethality finish
    "Manamune → Draktharr → Collector (Q Poke)": [
        "Tear of the Goddess",
        "Long Sword",
        "Boots of Speed",
        "Manamune",
        "Boots of Dynamism",
        "Serrated Dirk",
        "Duskblade of Draktharr",
        "The Collector",
        "Magnetic Blaster",
    ],
    # Manamune into crit range — safer DH procs from distance
    "Manamune → Magnetic → Collector (Range Farm)": [
        "Tear of the Goddess",
        "Long Sword",
        "Boots of Speed",
        "Manamune",
        "Boots of Dynamism",
        "Magnetic Blaster",
        "The Collector",
        "Infinity Edge",
        "Mortal Reminder",
    ],
    # Pure assassin — max single-target execute, fewer safe procs
    "Draktharr → Serpent → Serylda (Assassin)": [
        "Long Sword",
        "Boots of Speed",
        "Serrated Dirk",
        "Duskblade of Draktharr",
        "Boots of Dynamism",
        "Serpent's Fang",
        "Serylda's Grudge",
        "The Collector",
        "Umbral Glaive",
    ],
    # Crit IE peak — mist crit conversion, slower DH early
    "Magnetic → IE → Collector (Crit Peak)": [
        "Long Sword",
        "Boots of Speed",
        "Cloak of Agility",
        "Magnetic Blaster",
        "Boots of Dynamism",
        "B.F. Sword",
        "Infinity Edge",
        "The Collector",
        "Mortal Reminder",
    ],
    # Umbral early vision/control then Draktharr — aggressive roam
    "Umbral → Draktharr → Collector (Roam)": [
        "Long Sword",
        "Boots of Speed",
        "Serrated Dirk",
        "Umbral Glaive",
        "Boots of Dynamism",
        "Duskblade of Draktharr",
        "The Collector",
        "Magnetic Blaster",
        "Serylda's Grudge",
    ],
    # Essence Reaver weave — AA after Q for DH proc windows
    "Essence → Magnetic → Collector (Spellblade)": [
        "Long Sword",
        "Boots of Speed",
        "Caulfield's Warhammer",
        "Essence Reaver",
        "Boots of Dynamism",
        "Magnetic Blaster",
        "The Collector",
        "Infinity Edge",
        "Mortal Reminder",
    ],
    # Cleaver shred into Collector — vs bruiser comps, still aggressive
    "Draktharr → Cleaver → Collector (Shred)": [
        "Long Sword",
        "Boots of Speed",
        "Serrated Dirk",
        "Duskblade of Draktharr",
        "Boots of Dynamism",
        "Black Cleaver",
        "The Collector",
        "Serylda's Grudge",
        "Magnetic Blaster",
    ],
}


UPGRADE_COMPONENTS = {
    "Boots of Dynamism": ("Boots of Speed",),
    "Manamune": ("Tear of the Goddess", "Long Sword"),
    "Muramana": (),  # transforms from Manamune
    "Duskblade of Draktharr": ("Serrated Dirk", "Caulfield's Warhammer"),
    "The Collector": ("Pickaxe", "Cloak of Agility"),
    "Magnetic Blaster": ("Cloak of Agility",),
    "Infinity Edge": ("B.F. Sword", "Pickaxe", "Cloak of Agility"),
    "Serylda's Grudge": ("Last Whisper", "Caulfield's Warhammer"),
    "Mortal Reminder": ("Last Whisper", "Cloak of Agility"),
    "Essence Reaver": ("Caulfield's Warhammer", "Cloak of Agility"),
    "Serpent's Fang": ("Serrated Dirk",),
    "Umbral Glaive": ("Serrated Dirk",),
    "Black Cleaver": ("Caulfield's Warhammer",),
}

NEXT_COMPONENTS = {
    "Boots of Dynamism": ["Boots of Speed"],
    "Manamune": ["Tear of the Goddess", "Long Sword"],
    "Duskblade of Draktharr": ["Serrated Dirk", "Caulfield's Warhammer"],
    "The Collector": ["Pickaxe", "Cloak of Agility"],
    "Magnetic Blaster": ["Cloak of Agility"],
    "Infinity Edge": ["B.F. Sword", "Pickaxe", "Cloak of Agility"],
    "Serylda's Grudge": ["Last Whisper", "Caulfield's Warhammer"],
    "Mortal Reminder": ["Last Whisper", "Cloak of Agility"],
    "Essence Reaver": ["Caulfield's Warhammer", "Cloak of Agility"],
    "Serpent's Fang": ["Serrated Dirk"],
    "Umbral Glaive": ["Serrated Dirk"],
    "Black Cleaver": ["Caulfield's Warhammer"],
}


# ---------------------------------------------------------------------------
# Inventory
# ---------------------------------------------------------------------------

def resolve_inventory(path: List[str], gold: int, minute: int) -> List[Item]:
    owned: List[str] = []
    gold_pool = gold

    def credit_for(name: str) -> Tuple[int, List[str]]:
        credit = 0
        remove: List[str] = []
        for c in UPGRADE_COMPONENTS.get(name, ()):
            if c in owned:
                credit += ITEMS[c].cost
                remove.append(c)
        return credit, remove

    def remaining_cost(name: str) -> int:
        credit, _ = credit_for(name)
        return max(0, ITEMS[name].cost - credit)

    def can_afford(name: str) -> bool:
        return gold_pool >= remaining_cost(name)

    def buy(name: str) -> bool:
        nonlocal gold_pool
        if name in owned:
            return False
        cost = remaining_cost(name)
        if cost > gold_pool:
            return False
        _, remove = credit_for(name)
        gold_pool -= cost
        for r in remove:
            owned.remove(r)
        owned.append(name)
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

    # Manamune → Muramana ~ stacks complete by ~12–14 aggressive
    if "Manamune" in owned and minute >= 12:
        owned[owned.index("Manamune")] = "Muramana"

    if blocked_at and blocked_at in NEXT_COMPONENTS:
        for comp in NEXT_COMPONENTS[blocked_at]:
            if comp not in owned and gold_pool >= ITEMS[comp].cost:
                buy(comp)
        if can_afford(blocked_at):
            buy(blocked_at)
            seen = False
            for step in path:
                if step == blocked_at:
                    seen = True
                    continue
                if not seen or step in owned:
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

    if "Boots of Dynamism" in owned and "Boots of Speed" in owned:
        owned.remove("Boots of Speed")

    if "Manamune" in owned and minute >= 12:
        owned[owned.index("Manamune")] = "Muramana"

    return [ITEMS[n] for n in owned]


# ---------------------------------------------------------------------------
# Mist stacks (aggressive farming)
# ---------------------------------------------------------------------------

def mist_at_minute(m: int, aggression: float) -> int:
    """
    Aggressive Senna farms Mist hard: Living Extraction every trade +
    Soul Reap from constant fights. aggression 0.8–1.3.
    """
    stacks = 0.0
    for t in range(1, m + 1):
        if t <= 4:
            # Early all-ins: ~3–5 Living Extraction + some wraiths
            stacks += (4.5 + 1.5 * aggression)
        elif t <= 10:
            # Mid snowball fights: wraiths from kills + siphon spam
            stacks += (7.0 + 2.5 * aggression)
        else:
            # Mid-late: objective fights, multi-kill wraiths
            stacks += (8.5 + 3.0 * aggression)
    return int(stacks)


# ---------------------------------------------------------------------------
# Combat model — aggressive DH farm + peak burst
# ---------------------------------------------------------------------------

@dataclass
class Snapshot:
    minute: int
    build_name: str
    items: List[str]
    gold: int
    level: int
    mist: int
    bonus_ad: float
    total_ad: float
    crit: float
    flat_apen: float
    pct_apen: float
    dh_souls: int
    dh_procs_cum: int
    dh_proc_damage: float
    combo_burst: float          # AA+Q+on-hits+DH into <50% target
    peak_execute: float         # combo + Draktharr + Collector threshold help
    dh_farm_score: float        # weighted souls + reset rate
    aggression: float
    notes: str = ""


SENNA_BASE_AD = 50.0  # no AD/level (Relic Cannon)


def q_rank(level: int) -> int:
    # Max Q first: ranks at 1,3,5,7 → rank 1..4
    points = min(4, 1 + (level - 1) // 2)
    return max(1, min(4, points))


def q_base_damage(rank: int) -> float:
    return 50 + 40 * (rank - 1)  # 50/90/130/170


def living_extraction_pct(level: int) -> float:
    # Patch 7.2a: 1%–10% current HP by level
    return 0.01 + 0.09 * (level - 1) / 14


def nightstalker_damage(level: int) -> float:
    # 60–160 by level
    return 60 + 100 * (level - 1) / 14


def magnetic_energized(level: int) -> float:
    return 40 + 60 * (level - 1) / 14


def compute_aggression(inv: List[Item], minute: int) -> float:
    """
    How hard this build forces fights / DH procs.
    Lethality + execute + early spike → higher aggression → more souls.
    """
    names = {it.name for it in inv}
    score = 1.0
    if any(it.lethality_burst for it in inv):
        score += 0.22
    if any(it.collector for it in inv):
        score += 0.18
    if any(it.muramana or it.manamune for it in inv):
        score += 0.12  # Q poke forces <50% safely
    if any(it.magnetic for it in inv):
        score += 0.10  # range = safer procs / more trades
    if any(it.serylda for it in inv):
        score += 0.08  # Q slow sticks chase
    if any(it.essence for it in inv):
        score += 0.06
    if "Umbral Glaive" in names:
        score += 0.08  # vision → picks
    if any(it.serpent for it in inv):
        score += 0.05
    # Early spike bonus: Draktharr/Umbral/Manamune before 12
    if minute <= 12:
        if any(it.lethality_burst for it in inv) or "Umbral Glaive" in names:
            score += 0.12
        if any(it.manamune or it.muramana for it in inv):
            score += 0.08
    # Crit-only without lethality is slightly less aggressive early
    if any(it.ie for it in inv) and not any(it.lethality_burst for it in inv):
        score -= 0.05
    return max(0.75, min(1.45, score))


def expected_dh_souls(minute: int, aggression: float, has_reset_engine: bool) -> Tuple[int, int]:
    """
    Cumulative DH souls + total procs by minute for aggressive play.
    Base CD 20s → ~3/min without resets.
    Aggressive fights + takedown resets → many more.
    """
    souls = 0.0
    procs = 0.0
    for t in range(1, minute + 1):
        # Fight windows per minute (aggressive)
        if t <= 4:
            fights = 0.9 * aggression
        elif t <= 10:
            fights = 1.4 * aggression
        else:
            fights = 1.7 * aggression

        # Without reset: at most 1 proc per ~20s inside fights
        base_procs = min(3.0, fights * 1.1)

        # Takedown resets: each fight can chain 1–2 extra procs if burst is high
        if has_reset_engine:
            reset_procs = fights * 1.35 * aggression
        else:
            reset_procs = fights * 0.55 * aggression

        minute_procs = base_procs + reset_procs
        # Cap: you can't realistically farm > ~8–9 souls/min even in chaos
        minute_procs = min(8.5, minute_procs)
        procs += minute_procs
        souls += minute_procs  # 1 soul per proc
    return int(souls), int(procs)


def armor_mult(flat_apen: float, pct_apen: float, level: int, minute: int) -> float:
    armor = 32 + 2.2 * level + (0 if minute < 12 else 18)
    effective = armor * (1 - pct_apen) - flat_apen
    effective = max(8.0, effective)
    return 100.0 / (100.0 + effective)


def compute_snapshot(build_name: str, path: List[str], minute: int) -> Snapshot:
    gold = gold_at_minute(minute)
    level = level_at_minute(minute)
    inv = resolve_inventory(path, gold, minute)

    item_ad = 0.0
    ah = 0.0
    as_pct = 0.0
    crit = 0.0
    flat_apen = 0.0
    pct_apen = 0.0
    mana = 0.0
    has_drak = False
    has_collector = False
    has_mura = False
    has_mana = False
    has_magnetic = False
    has_ie = False
    has_serylda = False
    has_essence = False
    has_cleaver = False
    names: List[str] = []

    for it in inv:
        names.append(it.name)
        item_ad += it.ad
        ah += it.ah
        as_pct += it.as_pct
        crit += it.crit
        flat_apen += it.flat_apen
        pct_apen = min(0.45, pct_apen + it.pct_apen)  # soft stack
        mana += it.mana
        if it.lethality_burst:
            has_drak = True
        if it.collector:
            has_collector = True
        if it.muramana:
            has_mura = True
        if it.manamune:
            has_mana = True
        if it.magnetic:
            has_magnetic = True
        if it.ie:
            has_ie = True
        if it.serylda:
            has_serylda = True
        if it.essence:
            has_essence = True
        if it.cleaver:
            has_cleaver = True

    aggression = compute_aggression(inv, minute)
    mist = mist_at_minute(minute, aggression)
    mist_ad = mist * 1.25
    mist_crit = (mist // 20) * 0.15
    crit = min(1.0, crit + mist_crit)

    # Muramana Awe: 1.5% max mana as AD (post 7.2a values)
    awe_ad = 0.0
    if has_mura:
        # ~1000 base + tear stacks already in item; Senna base mana ~small
        awe_ad = 0.015 * (mana + 450)
    elif has_mana:
        # Partial stacks — ~60% of full mana pool mid-stack
        awe_ad = 0.015 * (mana * 0.7 + 300)

    bonus_ad = item_ad + mist_ad + awe_ad
    total_ad = SENNA_BASE_AD + bonus_ad

    has_reset_engine = has_drak or has_collector
    dh_souls, dh_procs = expected_dh_souls(minute, aggression, has_reset_engine)

    # Dark Harvest proc damage (adaptive → physical for AD Senna)
    dh_raw = 35 + 11 * dh_souls + 0.10 * bonus_ad
    # Ranged 80% from 6.3d — still applies unless reverted; keep it
    dh_raw *= 0.80

    pen = armor_mult(flat_apen, pct_apen, level, minute)
    if has_cleaver:
        # Avg ~3 Sunder stacks in a dive (~18% armor shred) — modest, not paper-god
        pen = min(1.02, pen * 1.06)

    dh_proc = dh_raw * pen

    # --- Aggressive combo burst into <50% target ---
    # Relic Cannon on-hit: 20% AD
    aa = total_ad + 0.20 * total_ad
    # Crit expectation (Senna crit = 141.75% base; IE → 205% WR crit)
    crit_mult = 1.4175 if not has_ie else 2.05
    aa_expected = aa * (1 + crit * (crit_mult - 1))

    # Q (Piercing Darkness) — applies on-hits
    qr = q_rank(level)
    q_dmg = q_base_damage(qr) + 0.60 * bonus_ad

    # Living Extraction consume (assume mark already applied — aggressive AA→Q)
    hp = target_max_hp(minute)
    # Target at ~40% HP when DH procs (aggressive execute window)
    extract = living_extraction_pct(level) * (0.40 * hp)

    # Muramana Shock on ability
    mura_shock = 0.0
    if has_mura:
        cur_mana = mana + 400
        mura_shock = 0.04 * cur_mana + 0.045 * bonus_ad
    elif has_mana:
        mura_shock = 0.04 * (mana * 0.6 + 250) + 0.045 * bonus_ad * 0.5

    # Draktharr Nightstalker (first hit in fight — aggressive dive)
    drak = nightstalker_damage(level) if has_drak else 0.0

    # Magnetic energized (often charged in chase)
    mag = magnetic_energized(level) if has_magnetic else 0.0
    # magic — rough resist
    mag *= 100 / (100 + 30 + level)

    # Essence Spellblade
    essence = 90.0 if has_essence else 0.0
    if has_essence:
        essence *= 1 + crit * (crit_mult - 1) * 0.5

    # Physical portion of combo (before DH)
    phys = (aa_expected + q_dmg + extract + mura_shock + drak + essence) * pen
    combo = phys + mag + dh_proc

    # Collector execute floor help — treat as +% of remaining HP deleted
    peak = combo
    if has_collector:
        exec_pct = 0.04 + 0.02 * crit  # base Collector threshold
        peak += exec_pct * hp * 0.55  # partial credit: enables finishes → resets

    # Serylda chase: slight uptime on multi-proc fights
    if has_serylda:
        peak *= 1.04

    # DH farm score: souls weighted + reset potential + poke to force <50%
    poke_force = 1.0
    if has_mura or has_mana:
        poke_force += 0.25
    if has_magnetic:
        poke_force += 0.15
    if has_drak:
        poke_force += 0.20
    if has_collector:
        poke_force += 0.18
    dh_farm_score = dh_souls * 12.0 * poke_force + dh_proc * 0.35 + aggression * 40

    notes = []
    if has_drak and has_collector:
        notes.append("RESET ENGINE (Drak+Collector)")
    elif has_drak:
        notes.append("Nightstalker resets")
    elif has_collector:
        notes.append("Collector execute")
    if has_mura:
        notes.append("Muramana Shock Q")
    elif has_mana:
        notes.append("Manamune stacking")
    if has_magnetic:
        notes.append("range farm")
    if aggression >= 1.25:
        notes.append("MAX AGGRESSION")
    notes.append(f"Mist {mist} | DH souls {dh_souls}")

    return Snapshot(
        minute=minute,
        build_name=build_name,
        items=names,
        gold=gold,
        level=level,
        mist=mist,
        bonus_ad=round(bonus_ad, 1),
        total_ad=round(total_ad, 1),
        crit=round(crit, 3),
        flat_apen=flat_apen,
        pct_apen=round(pct_apen, 3),
        dh_souls=dh_souls,
        dh_procs_cum=dh_procs,
        dh_proc_damage=round(dh_proc, 1),
        combo_burst=round(combo, 1),
        peak_execute=round(peak, 1),
        dh_farm_score=round(dh_farm_score, 1),
        aggression=round(aggression, 3),
        notes=", ".join(notes),
    )


def score_snapshot(s: Snapshot) -> float:
    """Peak damage + MAX DH farm — aggressive priority.

    Souls are weighted hard: the brief is farm Dark Harvest as much as possible
    while still peaking damage (not paper DPS without resets).
    """
    early = 1.10 if s.minute <= 12 and s.aggression >= 1.15 else 1.0
    reset_bonus = 1.0
    if "Draktharr" in " ".join(s.items) and "Collector" in " ".join(s.items):
        reset_bonus = 1.12
    elif "Draktharr" in " ".join(s.items) or "Collector" in " ".join(s.items):
        reset_bonus = 1.05
    return (
        s.peak_execute * 0.85
        + s.dh_souls * 28.0
        + s.dh_proc_damage * 1.1
        + s.dh_farm_score * 0.15
    ) * early * reset_bonus


def run_all() -> Tuple[Dict[str, List[Snapshot]], List[dict]]:
    results: Dict[str, List[Snapshot]] = {}
    for name, path in BUILD_PATHS.items():
        results[name] = [compute_snapshot(name, path, m) for m in range(1, GAME_MINUTES + 1)]

    timeline = []
    for m in range(1, GAME_MINUTES + 1):
        cands = [(n, results[n][m - 1]) for n in results]
        best_n, best_s = max(cands, key=lambda x: score_snapshot(x[1]))
        timeline.append(
            {
                "minute": m,
                "winner": best_n,
                "peak_execute": best_s.peak_execute,
                "combo_burst": best_s.combo_burst,
                "dh_souls": best_s.dh_souls,
                "dh_proc": best_s.dh_proc_damage,
                "mist": best_s.mist,
                "aggression": best_s.aggression,
                "items": best_s.items,
                "bonus_ad": best_s.bonus_ad,
                "notes": best_s.notes,
            }
        )
    return results, timeline


def summarize(results, timeline) -> str:
    lines = []
    lines.append("=" * 78)
    lines.append("SENNA — AGGRESSIVE DARK HARVEST PEAK SIM (Wild Rift Patch 7.2+)")
    lines.append("Playstyle: dive / skirmish / force <50% / takedown resets")
    lines.append("Game length: 20:00 | Role: aggressive ADC / flex carry (NOT poke support)")
    lines.append("=" * 78)
    lines.append("")
    lines.append("GOLD / LEVEL / MIST (aggression=1.2 reference)")
    lines.append(f"  {'Min':>3}  {'Gold':>6}  {'Lvl':>3}  {'Mist~':>5}  {'TargetHP':>8}")
    for m in range(1, 21):
        lines.append(
            f"  {m:>3}  {gold_at_minute(m):>6}  {level_at_minute(m):>3}  "
            f"{mist_at_minute(m, 1.2):>5}  {target_max_hp(m):>8}"
        )

    lines.append("")
    lines.append("-" * 78)
    lines.append("MINUTE-BY-MINUTE OPTIMAL (peak execute × DH farm)")
    lines.append("-" * 78)
    for row in timeline:
        item_short = " › ".join(row["items"][:5])
        if len(row["items"]) > 5:
            item_short += " › …"
        lines.append(
            f"  {row['minute']:>2}:00 | peak {row['peak_execute']:>7.0f} | "
            f"DH {row['dh_souls']:>3} souls ({row['dh_proc']:>5.0f} dmg) | "
            f"agg {row['aggression']:.2f} | {row['winner']}"
        )
        lines.append(f"         items: {item_short}")
        lines.append(f"         {row['notes']}")

    lines.append("")
    lines.append("-" * 78)
    lines.append("BUILD COMPARISON — peak execute / DH souls @ spikes")
    lines.append("-" * 78)
    lines.append(
        f"  {'Build':<42} {'8pk':>6} {'12pk':>6} {'16pk':>6} {'20pk':>6} "
        f"{'DH20':>5} {'Score':>7}"
    )
    ranking = []
    for name, snaps in results.items():
        p8 = snaps[7].peak_execute
        p12 = snaps[11].peak_execute
        p16 = snaps[15].peak_execute
        p20 = snaps[19].peak_execute
        dh20 = snaps[19].dh_souls
        # Aggressive score: early-mid peak weighted + total souls
        score = 0.0
        for s in snaps:
            w = 1.25 if s.minute <= 12 else 1.0
            score += score_snapshot(s) * w
        score /= len(snaps)
        ranking.append((score, dh20, p20, name, p8, p12, p16, p20, snaps))
        lines.append(
            f"  {name:<42} {p8:>6.0f} {p12:>6.0f} {p16:>6.0f} {p20:>6.0f} "
            f"{dh20:>5} {score:>7.0f}"
        )

    # Prefer highest souls when scores are within ~4%; else raw score
    ranking.sort(key=lambda x: (x[0], x[1], x[2]), reverse=True)
    best = ranking[0]
    for cand in ranking[1:]:
        if cand[1] > best[1] and cand[0] >= best[0] * 0.96:
            best = cand
            break
    # Also surface the pure max-DH build for the report
    max_dh = max(ranking, key=lambda x: (x[1], x[0], x[2]))

    winner_name = best[3]
    snaps = best[8]

    drak_m = next((s.minute for s in snaps if any("Draktharr" in i for i in s.items)), None)
    col_m = next((s.minute for s in snaps if any("Collector" in i for i in s.items)), None)
    mag_m = next((s.minute for s in snaps if any("Magnetic" in i for i in s.items)), None)
    cleave_m = next((s.minute for s in snaps if any("Cleaver" in i for i in s.items)), None)
    serpent_m = next((s.minute for s in snaps if any("Serpent" in i for i in s.items)), None)
    mana_m = next(
        (s.minute for s in snaps if any(x in i for i in s.items for x in ("Manamune", "Muramana"))),
        None,
    )

    lines.append("")
    lines.append("-" * 78)
    lines.append("VERDICT — MOST DAMAGE PEAK + MAX DARK HARVEST FARM")
    lines.append("-" * 78)
    lines.append(f"  Winner: {winner_name}")
    lines.append(f"  Aggression-weighted score: {best[0]:.0f}")
    lines.append(f"  DH souls @ 20:00: {best[1]} | Peak execute @ 20: {best[2]:.0f}")
    if max_dh[3] != winner_name:
        lines.append(
            f"  Max-souls runner-up: {max_dh[3]} ({max_dh[1]} souls, peak {max_dh[2]:.0f})"
        )
    if drak_m:
        lines.append(f"  Draktharr online: ~{drak_m}:00 (Nightstalker + takedown reset)")
    if col_m:
        lines.append(f"  Collector online: ~{col_m}:00 (execute floor → more resets)")
    if mag_m:
        lines.append(f"  Magnetic Blaster online: ~{mag_m}:00 (range to farm DH safely)")
    if cleave_m:
        lines.append(f"  Black Cleaver online: ~{cleave_m}:00 (armor shred on dive)")
    if serpent_m:
        lines.append(f"  Serpent's Fang online: ~{serpent_m}:00")
    if mana_m:
        lines.append(f"  Manamune/Muramana online: ~{mana_m}:00")

    lines.append("")
    lines.append("  WHY AGGRESSIVE DH SENNA PEAKS THIS WAY:")
    lines.append("  • Dark Harvest only procs below 50% — you must FORCE fights, not poke forever")
    lines.append("  • Takedown resets CD to 1s — each kill snowballs souls HARD")
    lines.append("  • Draktharr Nightstalker = dive burst + reset on takedown (soul printer)")
    lines.append("  • Collector execute = finishes that create more DH resets")
    lines.append("  • Magnetic / range tools keep you alive to chain the next <50% proc")
    lines.append("  • Mist AD (1.25/stack) feeds both autos and the 10% bonus AD on DH")
    lines.append("  • This is NOT support poke Senna — aggression > safe Q poke for souls")
    lines.append("")
    lines.append("  RECOMMENDED PURCHASE ORDER (aggressive DH Senna, 20-min):")
    # Emit path from winner build
    win_path = BUILD_PATHS[winner_name]
    step_n = 1
    for item_name in win_path:
        if item_name in ("Long Sword", "Boots of Speed", "Serrated Dirk", "Cloak of Agility",
                         "Pickaxe", "B.F. Sword", "Caulfield's Warhammer", "Tear of the Goddess",
                         "Last Whisper"):
            continue
        marker = ""
        if "Draktharr" in item_name:
            marker = " — FIRST spike, start reset chaining"
        elif "Collector" in item_name:
            marker = " — execute floor, more takedown resets"
        elif "Magnetic" in item_name:
            marker = " — range to keep farming DH after you get focused"
        elif "Cleaver" in item_name:
            marker = " — shred on repeated dive autos/Q"
        lines.append(f"  {step_n}) {item_name}{marker}")
        step_n += 1
        if step_n > 6:
            break
    lines.append("")
    lines.append("  PLAY PATTERN TO MAX DH SOULS:")
    lines.append("  • Look for 2v2 / river fights early — every takedown = free soul")
    lines.append("  • AA → Q to apply Living Extraction, then finish with DH window")
    lines.append("  • After first kill, immediately look for next <50% target (1s CD)")
    lines.append("  • Wraiths from kills = Mist AD = stronger DH (10% bonus AD)")
    lines.append("  • Trap: pure crit IE path — higher paper late DPS, fewer early resets")
    lines.append("  • Trap: Manamune-first — safer poke, slower reset engine vs Drak rush")
    lines.append("  • Trap: playing like enchanter Senna — you will starve Dark Harvest")
    lines.append("=" * 78)
    return "\n".join(lines)


def export_json(results, timeline, path: str) -> None:
    payload = {
        "meta": {
            "champion": "Senna",
            "role": "Aggressive ADC / flex carry",
            "patch": "7.2+",
            "game_minutes": GAME_MINUTES,
            "playstyle": "aggressive Dark Harvest farm + peak execute",
            "dark_harvest": "35 + 11*souls + 10% bonus AD + 5% AP; 20s CD, 1s on takedown; ranged 80%",
        },
        "timeline": timeline,
        "builds": {
            name: [
                {
                    "minute": s.minute,
                    "items": s.items,
                    "gold": s.gold,
                    "level": s.level,
                    "mist": s.mist,
                    "bonus_ad": s.bonus_ad,
                    "total_ad": s.total_ad,
                    "crit": s.crit,
                    "dh_souls": s.dh_souls,
                    "dh_procs_cum": s.dh_procs_cum,
                    "dh_proc_damage": s.dh_proc_damage,
                    "combo_burst": s.combo_burst,
                    "peak_execute": s.peak_execute,
                    "dh_farm_score": s.dh_farm_score,
                    "aggression": s.aggression,
                    "notes": s.notes,
                }
                for s in snaps
            ]
            for name, snaps in results.items()
        },
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def main() -> None:
    results, timeline = run_all()
    report = summarize(results, timeline)
    print(report)
    out_dir = "/workspace/senna-dh-sim"
    with open(f"{out_dir}/report.txt", "w", encoding="utf-8") as f:
        f.write(report + "\n")
    export_json(results, timeline, f"{out_dir}/results.json")
    print(f"\nWrote {out_dir}/report.txt and {out_dir}/results.json")


if __name__ == "__main__":
    main()
