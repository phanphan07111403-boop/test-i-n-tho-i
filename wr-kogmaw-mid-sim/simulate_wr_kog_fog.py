#!/usr/bin/env python3
"""
Wild Rift — AP Kog'Maw mid, fog Living Artillery, Dark Harvest.
Patch snapshot 7.3d (R nerf from 7.2c still in force, IO threshold from 7.3).

Playstyle: spam R from fog. The rule that makes every cast a kill:
only press Living Artillery when the target's current HP is at or under
the kill line. Chip shots above that line are not part of the pattern —
they spend mana and can put Dark Harvest on a 20s cooldown.

Metric: the highest current-HP fraction at which ONE artillery cast
kills. "Chain" is the cast that has to work for every R in a fight
(Dark Harvest up, Luden's Echo down). "Opener" adds Echo when it is ready.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple
import json
from pathlib import Path

GAME_MINUTES = 18
OUT_DIR = Path(__file__).resolve().parent

# R ranks at levels 5 / 9 / 13. Basic abilities cap at rank 4.
R_BASE = (80.0, 120.0, 160.0)
R_RATIO = 0.25
R_EXEC_BASE = (200.0, 280.0, 360.0)
R_EXEC_RATIO = 0.50
R_COOLDOWN = (2.0, 1.5, 1.0)
# 0%–50% amp across 0%–60% missing HP. Below 40% HP the execute formula replaces it.
R_AMP_CAP = 0.50
R_AMP_MISSING = 0.60
EXECUTE_HP = 0.40
DH_HP = 0.50


# ---------------------------------------------------------------------------
# Economy — even mid who cashes artillery assists, not a stomp.
# Full build is not assumed. ~13k gold by 18:00.
# ---------------------------------------------------------------------------


def gold_at_minute(m: int) -> int:
    if m <= 0:
        return 500
    total = 500
    for t in range(1, m + 1):
        if t <= 4:
            total += 450
        elif t <= 9:
            total += 600
        elif t <= 14:
            total += 720
        else:
            total += 800
    if m >= 6:
        total += 180 * ((m - 4) // 2)
    return total


def level_at_minute(m: int) -> int:
    table = {
        1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7, 7: 8, 8: 8,
        9: 9, 10: 10, 11: 11, 12: 12, 13: 13, 14: 13,
        15: 14, 16: 15, 17: 15, 18: 15,
    }
    return table.get(m, 15 if m > 18 else 1)


def eyeball_stacks(level: int) -> int:
    """Eyeball Collection: 3 AP per takedown, cap 8. Assumes the kill pattern is working."""
    if level < 5:
        return 0
    return {5: 2, 6: 2, 7: 3, 8: 3, 9: 4, 10: 4, 11: 5, 12: 5, 13: 6, 14: 7, 15: 8}.get(
        level, 8
    )


def dark_harvest_souls(level: int, minute: int) -> int:
    """Harvests from the kills this pattern takes, plus a few extra procs."""
    if level < 5:
        return 0
    return min(16, eyeball_stacks(level) + max(0, (minute - 8) // 2))


def q_rank(level: int) -> int:
    """R > Q > E > W. Q is rank 4 from level 8."""
    if level < 1:
        return 0
    if level < 3:
        return 1
    if level < 6:
        return 2
    if level < 8:
        return 3
    return 4


def q_shred(level: int) -> float:
    rank = q_rank(level)
    if rank <= 0:
        return 0.0
    return (0.20, 0.24, 0.28, 0.32)[rank - 1]


def r_rank(level: int) -> int:
    if level < 5:
        return 0
    if level < 9:
        return 1
    if level < 13:
        return 2
    return 3


# ---------------------------------------------------------------------------
# Targets. MR items come in on a smooth clock so a spike is not a fake drop.
# ---------------------------------------------------------------------------


def base_mr(level: int) -> float:
    return 32.0 + 1.5 * (level - 1)


def target_stats(kind: str, minute: int) -> Tuple[float, float]:
    level = level_at_minute(minute)
    if kind == "adc":
        hp = 610 + 100 * (level - 1) + 45 * max(0, minute - 2)
        extra = 0.0 if minute < 11 else (22.0 if minute < 16 else 40.0)
    elif kind == "mid":
        hp = 640 + 110 * (level - 1) + 55 * max(0, minute - 4)
        extra = 0.0 if minute < 8 else (18.0 if minute < 14 else 42.0)
    elif kind == "enchanter":
        hp = 580 + 88 * (level - 1) + 35 * max(0, minute - 4)
        extra = 0.0 if minute < 9 else 28.0
    elif kind == "bruiser":
        hp = 720 + 130 * (level - 1) + 100 * max(0, minute - 3)
        extra = 0.0 if minute < 6 else min(14.0 * (minute - 6), 130.0)
    else:
        raise KeyError(kind)
    return hp, base_mr(level) + extra


# ---------------------------------------------------------------------------
# Items — Wild Rift 7.2 mage overhaul, IO threshold bumped in 7.3.
# ---------------------------------------------------------------------------


@dataclass
class Item:
    name: str
    cost: int
    ap: float = 0
    ah: float = 0
    mana: float = 0
    flat_mpen: float = 0
    pct_mpen: float = 0
    ult_haste: float = 0
    mana_regen: float = 0  # fraction added to base regen (0.75 = +75%)
    deathcap: bool = False
    luden: bool = False
    malignance: bool = False
    infinity_orb: bool = False
    horizon: bool = False
    tags: Tuple[str, ...] = ()


ITEMS: Dict[str, Item] = {
    "Amplifying Tome": Item("Amplifying Tome", 500, ap=20),
    "Ring of Revelation": Item("Ring of Revelation", 300, ah=5),
    "Blasting Wand": Item("Blasting Wand", 800, ap=40),
    "Needlessly Large Rod": Item("Needlessly Large Rod", 1400, ap=70),
    "Aether Wisp": Item("Aether Wisp", 950, ap=25),
    "Fiendish Codex": Item("Fiendish Codex", 900, ap=30, ah=10),
    "Void Amethyst": Item("Void Amethyst", 1000, ap=20, pct_mpen=0.10),
    "Haunting Guise": Item("Haunting Guise", 1300, ap=35),
    "Fated Ashes": Item("Fated Ashes", 900, ap=35),
    "Lost Chapter": Item("Lost Chapter", 1200, ap=35, ah=10, mana=200),
    "Hextech Alternator": Item("Hextech Alternator", 1100, ap=45),
    "Boots of Speed": Item("Boots of Speed", 400, tags=("boots",)),
    "Boots of Mana": Item(
        "Boots of Mana", 1200, ap=25, flat_mpen=8, mana_regen=0.75, tags=("boots",)
    ),
    "Spellslinger's Shoes": Item(
        "Spellslinger's Shoes",
        2200,
        ap=35,
        flat_mpen=18,
        pct_mpen=0.08,
        mana_regen=1.00,
        tags=("boots",),
    ),
    "Luden's Echo": Item(
        "Luden's Echo", 2800, ap=100, ah=10, mana=500, luden=True, tags=("mana",)
    ),
    "Malignance": Item(
        "Malignance",
        2700,
        ap=90,
        ah=15,
        mana=500,
        ult_haste=20,
        malignance=True,
        tags=("mana",),
    ),
    "Stormsurge": Item("Stormsurge", 2900, ap=90, flat_mpen=15, tags=("pen",)),
    "Infinity Orb": Item(
        "Infinity Orb", 3100, ap=110, flat_mpen=15, infinity_orb=True, tags=("execute",)
    ),
    "Horizon Focus": Item(
        "Horizon Focus", 2700, ap=80, ah=25, horizon=True, tags=("amp",)
    ),
    "Void Staff": Item("Void Staff", 3000, ap=95, pct_mpen=0.40, tags=("pen",)),
    "Rabadon's Deathcap": Item(
        "Rabadon's Deathcap", 3400, ap=130, deathcap=True, tags=("amp",)
    ),
    "Liandry's Torment": Item(
        "Liandry's Torment", 3000, ap=70, tags=("burn",)
    ),
}


# Direct components only. acquire() crafts them recursively.
UPGRADE: Dict[str, Tuple[str, ...]] = {
    "Lost Chapter": ("Amplifying Tome", "Ring of Revelation"),
    "Hextech Alternator": ("Amplifying Tome",),
    "Boots of Mana": ("Boots of Speed", "Amplifying Tome"),
    "Spellslinger's Shoes": ("Boots of Mana",),
    "Luden's Echo": ("Lost Chapter", "Hextech Alternator"),
    "Malignance": ("Lost Chapter", "Blasting Wand"),
    "Stormsurge": ("Hextech Alternator", "Aether Wisp"),
    "Infinity Orb": ("Hextech Alternator", "Needlessly Large Rod"),
    "Horizon Focus": ("Fiendish Codex", "Fiendish Codex", "Amplifying Tome"),
    "Void Staff": ("Void Amethyst", "Needlessly Large Rod"),
    "Rabadon's Deathcap": ("Needlessly Large Rod", "Needlessly Large Rod"),
    "Liandry's Torment": ("Haunting Guise", "Fated Ashes"),
}

UNIQUE = {
    "Boots of Speed",
    "Boots of Mana",
    "Spellslinger's Shoes",
    "Lost Chapter",
    "Hextech Alternator",
    "Luden's Echo",
    "Malignance",
    "Stormsurge",
    "Infinity Orb",
    "Horizon Focus",
    "Void Staff",
    "Rabadon's Deathcap",
    "Liandry's Torment",
    "Void Amethyst",
    "Aether Wisp",
    "Haunting Guise",
    "Fated Ashes",
}

LEGENDARIES = {
    "Luden's Echo",
    "Malignance",
    "Stormsurge",
    "Infinity Orb",
    "Horizon Focus",
    "Void Staff",
    "Rabadon's Deathcap",
    "Liandry's Torment",
}


BUILD_PATHS: Dict[str, List[str]] = {
    # Flat pen first. Mana comes from boots only — lethal shots cost 50 if staggered.
    "Storm → IO → Void → Cap": [
        "Stormsurge",
        "Boots of Mana",
        "Spellslinger's Shoes",
        "Infinity Orb",
        "Void Staff",
        "Rabadon's Deathcap",
    ],
    # Same items, Infinity Orb before the boot upgrade so the execute amp is not
    # stuck behind Spellslinger's 1000g combine.
    "Storm → IO → Slinger → Void": [
        "Stormsurge",
        "Infinity Orb",
        "Boots of Mana",
        "Spellslinger's Shoes",
        "Void Staff",
        "Rabadon's Deathcap",
    ],
    "IO → Storm → Void → Cap": [
        "Infinity Orb",
        "Boots of Mana",
        "Spellslinger's Shoes",
        "Stormsurge",
        "Void Staff",
        "Rabadon's Deathcap",
    ],
    # Echo on the staggered opener, then the same pen stack.
    "Luden → Storm → IO → Void": [
        "Luden's Echo",
        "Boots of Mana",
        "Spellslinger's Shoes",
        "Stormsurge",
        "Infinity Orb",
        "Void Staff",
    ],
    # Ult haste + Hatefog for a second tap. First tap does not get the shred.
    "Malig → Storm → IO → Void": [
        "Malignance",
        "Boots of Mana",
        "Spellslinger's Shoes",
        "Stormsurge",
        "Infinity Orb",
        "Void Staff",
    ],
    "Luden → IO → Void → Cap": [
        "Luden's Echo",
        "Boots of Mana",
        "Spellslinger's Shoes",
        "Infinity Orb",
        "Void Staff",
        "Rabadon's Deathcap",
    ],
    "Luden → IO → Storm → Void": [
        "Luden's Echo",
        "Infinity Orb",
        "Boots of Mana",
        "Spellslinger's Shoes",
        "Stormsurge",
        "Void Staff",
    ],
    "Malig → IO → Void → Cap": [
        "Malignance",
        "Boots of Mana",
        "Spellslinger's Shoes",
        "Infinity Orb",
        "Void Staff",
        "Rabadon's Deathcap",
    ],
    # 10% amp looks like fog synergy. It does not apply to the first hit on a new target.
    "Luden → IO → Horizon → Cap": [
        "Luden's Echo",
        "Boots of Mana",
        "Spellslinger's Shoes",
        "Infinity Orb",
        "Horizon Focus",
        "Rabadon's Deathcap",
    ],
    # Burn foil. Torment does not raise the one-cast kill line.
    "Malig → Liandry → Void": [
        "Malignance",
        "Boots of Mana",
        "Spellslinger's Shoes",
        "Liandry's Torment",
        "Void Staff",
        "Rabadon's Deathcap",
    ],
}


SECONDARIES = ("Axiom", "Coup", "Scorch")


# ---------------------------------------------------------------------------
# Inventory
# ---------------------------------------------------------------------------


def resolve_inventory(path: Sequence[str], gold: int, minute: int) -> List[str]:
    owned: List[str] = []
    pool = gold

    def missing_components(name: str) -> List[str]:
        need = list(UPGRADE.get(name, ()))
        have = owned.copy()
        missing: List[str] = []
        for comp in need:
            if comp in have:
                have.remove(comp)
            else:
                missing.append(comp)
        return missing

    def remaining_cost(name: str) -> int:
        credit = 0
        have = owned.copy()
        for comp in UPGRADE.get(name, ()):
            if comp in have:
                have.remove(comp)
                credit += ITEMS[comp].cost
        return max(0, ITEMS[name].cost - credit)

    def pay(name: str) -> bool:
        nonlocal pool
        if name in UNIQUE and name in owned:
            return True
        cost = remaining_cost(name)
        if cost > pool:
            return False
        have = owned.copy()
        for comp in UPGRADE.get(name, ()):
            if comp in have:
                have.remove(comp)
                owned.remove(comp)
        pool -= cost
        owned.append(name)
        return True

    def acquire_one(name: str, depth: int = 0) -> bool:
        if depth > 8:
            return False
        if name in UNIQUE and name in owned:
            return True
        guard = 0
        while guard < 8:
            guard += 1
            if pay(name):
                return True
            missing = missing_components(name)
            if not missing:
                return False
            if not acquire_one(missing[0], depth + 1):
                return False
        return False

    wanted_slinger = False
    for step in path:
        if step == "Spellslinger's Shoes":
            wanted_slinger = True
            if minute < 10:
                continue
        if not acquire_one(step):
            break

    if wanted_slinger and minute >= 10 and "Spellslinger's Shoes" not in owned:
        acquire_one("Spellslinger's Shoes")
    return owned


# ---------------------------------------------------------------------------
# Combat
# ---------------------------------------------------------------------------


@dataclass
class Loadout:
    ap: float
    ah: float
    ult_haste: float
    mana: float
    mana_regen: float
    flat_pen: float
    pct_pens: Tuple[float, ...]
    luden: bool
    malignance: bool
    infinity_orb: bool
    horizon: bool
    names: List[str]
    secondary: str
    level: int
    minute: int
    souls: int
    eyeballs: int


def haste_factor(haste: float) -> float:
    return 100.0 / (100.0 + max(0.0, haste))


def scorch_damage(level: int) -> float:
    # 21 at level 1 → 49 at level 15.
    return 21.0 + (49.0 - 21.0) * (level - 1) / 14.0


def build_loadout(
    names: Sequence[str], minute: int, secondary: str
) -> Loadout:
    level = level_at_minute(minute)
    ap = ah = mana = regen = flat = uh = 0.0
    pct: List[float] = []
    flags = {"luden": False, "malig": False, "io": False, "horizon": False, "cap": False}
    for name in names:
        it = ITEMS[name]
        ap += it.ap
        ah += it.ah
        mana += it.mana
        regen += it.mana_regen
        flat += it.flat_mpen
        uh += it.ult_haste
        if it.pct_mpen:
            pct.append(it.pct_mpen)
        flags["luden"] = flags["luden"] or it.luden
        flags["malig"] = flags["malig"] or it.malignance
        flags["io"] = flags["io"] or it.infinity_orb
        flags["horizon"] = flags["horizon"] or it.horizon
        flags["cap"] = flags["cap"] or it.deathcap

    eyes = eyeball_stacks(level)
    ap += 3.0 * eyes
    if flags["cap"]:
        ap *= 1.30

    return Loadout(
        ap=ap,
        ah=ah,
        ult_haste=uh,
        mana=mana,
        mana_regen=regen,
        flat_pen=flat,
        pct_pens=tuple(pct),
        luden=flags["luden"],
        malignance=flags["malig"],
        infinity_orb=flags["io"],
        horizon=flags["horizon"],
        names=list(names),
        secondary=secondary,
        level=level,
        minute=minute,
        souls=dark_harvest_souls(level, minute),
        eyeballs=eyes,
    )


def r_cooldown(load: Loadout) -> float:
    rank = r_rank(load.level)
    if rank <= 0:
        return 99.0
    return R_COOLDOWN[rank - 1] * haste_factor(load.ah + load.ult_haste)


def max_mana(load: Loadout) -> float:
    return 380.0 + 50.0 * (load.level - 1) + load.mana


def mana_per_sec(load: Loadout) -> float:
    per5 = (14.0 + 1.0 * (load.level - 1)) * (1.0 + load.mana_regen)
    return per5 / 5.0


def effective_mr(
    mr: float,
    *,
    q: float = 0.0,
    flat_shred: float = 0.0,
    pct_pens: Sequence[float] = (),
    flat_pen: float = 0.0,
) -> float:
    value = max(0.0, mr * (1.0 - q) - flat_shred)
    for pct in pct_pens:
        value *= 1.0 - pct
    return max(0.0, value - flat_pen)


def magic_mult(mr: float) -> float:
    return 100.0 / (100.0 + mr)


def artillery_raw(rank: int, ap: float, hp_frac: float) -> float:
    if rank <= 0:
        return 0.0
    if hp_frac < EXECUTE_HP:
        return R_EXEC_BASE[rank - 1] + R_EXEC_RATIO * ap
    missing = 1.0 - hp_frac
    amp = R_AMP_CAP * min(1.0, missing / R_AMP_MISSING)
    return (R_BASE[rank - 1] + R_RATIO * ap) * (1.0 + amp)


def dark_harvest_raw(load: Loadout) -> float:
    # 35 + 11 per soul + 10% bonus AD + 5% AP. AP Kog has no bonus AD.
    return 35.0 + 11.0 * load.souls + 0.05 * load.ap


def luden_raw(ap: float) -> float:
    """Isolated Echo. Client tooltip: primary + up to 4 other targets.

    Each missing secondary adds 20 + 1.2% AP onto the champion.
    Patch-note wording says "5 nearby"; the post-7.3 client transcription
    counts 4 other targets. Fog cast on a lone champion uses the 4.
    """
    return (75.0 + 0.08 * ap) + 4.0 * (20.0 + 0.012 * ap)


@dataclass
class CastMods:
    """What is already true about THIS target before the glob lands."""

    dh_ready: bool = True
    luden_ready: bool = False
    # Hypershot / Hatefog shred are on the target only after a previous hit.
    marked: bool = False
    hatefog_shred: bool = False
    q_shred: float = 0.0
    include_scorch: bool = True


def cast_damage(
    load: Loadout,
    hp_frac: float,
    mr: float,
    mods: CastMods,
) -> float:
    """Damage of one fog cast resolved against a target at hp_frac of max HP.

    Same-tick pieces (R, Dark Harvest, Echo) read the pre-hit HP.
    Scorch lands 1 second later and may pick up Coup de Grace if the glob
    already dropped the target under 40%.
    """
    rank = r_rank(load.level)
    if rank <= 0 or hp_frac <= 0:
        return 0.0

    shred = 10.0 if (mods.hatefog_shred and load.malignance) else 0.0
    eff = effective_mr(
        mr,
        q=mods.q_shred,
        flat_shred=shred,
        pct_pens=load.pct_pens,
        flat_pen=load.flat_pen,
    )
    mult = magic_mult(eff)
    below_exec = hp_frac < EXECUTE_HP
    coup = 1.08 if (load.secondary == "Coup" and below_exec) else 1.0
    io = 1.20 if (load.infinity_orb and below_exec) else 1.0
    axiom = 1.08 if load.secondary == "Axiom" else 1.0
    focus = 1.10 if (mods.marked and load.horizon) else 1.0

    raw_r = artillery_raw(rank, load.ap, hp_frac) * axiom * io
    dealt = raw_r * coup * focus * mult

    if mods.dh_ready and hp_frac < DH_HP:
        # Rune damage. Infinity Orb and Axiom do not amp it. Coup does.
        dealt += dark_harvest_raw(load) * coup * focus * mult

    if mods.luden_ready and load.luden:
        dealt += luden_raw(load.ap) * coup * focus * mult

    if load.secondary == "Scorch" and mods.include_scorch:
        # Lands 1s later. Coup applies if they are already under 40% after the glob.
        # Approximate post-hit fraction with the damage dealt so far.
        # Caller passes max HP via the fraction only — scorch coup uses pre-hit
        # OR the knowledge that any lethal-line search under 40% already has coup.
        # If the pre-hit is above 40%, give Coup only when this same glob's damage
        # is being evaluated inside the execute search. Handled by pre-hit flag:
        # scorch coup if pre-hit is already in execute range. Above 40%, scorch
        # is a small delayed tick without Coup (they may still be above 40%).
        dealt += scorch_damage(load.level) * coup * focus * mult

    return dealt


def kill_line(load: Loadout, max_hp: float, mr: float, mods: CastMods) -> float:
    """Highest current-HP fraction at which this cast kills. 0 if R is unlearned."""
    if r_rank(load.level) <= 0 or max_hp <= 0:
        return 0.0

    def lethal(frac: float) -> bool:
        if frac <= 0:
            return True
        return cast_damage(load, frac, mr, mods) >= frac * max_hp - 0.05

    if not lethal(0.001):
        return 0.0
    lo, hi = 0.0, 1.0
    for _ in range(24):
        mid = (lo + hi) / 2.0
        if lethal(mid):
            lo = mid
        else:
            hi = mid
    return lo


def r_mana_cost(shot_index: int) -> int:
    """shot_index 0 is the first cast. Stacks cap at 9. Cost 50 → 500."""
    stacks = min(max(shot_index, 0), 9)
    return 50 + 50 * stacks


# ---------------------------------------------------------------------------
# Snapshots
# ---------------------------------------------------------------------------


@dataclass
class Snapshot:
    minute: int
    build: str
    secondary: str
    items: List[str]
    gold: int
    level: int
    ap: float
    ah: float
    mana_pool: float
    r_cd: float
    souls: int
    chain_adc: float
    chain_mid: float
    chain_ench: float
    chain_bruiser: float
    open_adc: float
    dry_adc: float
    chain_adc_q: float
    adc_hp: float
    adc_mr: float
    mid_hp: float
    mid_mr: float
    notes: str = ""
    score_part: float = 0.0


def snapshot_for(build: str, path: Sequence[str], minute: int, secondary: str) -> Snapshot:
    names = resolve_inventory(path, gold_at_minute(minute), minute)
    load = build_loadout(names, minute, secondary)
    adc_hp, adc_mr = target_stats("adc", minute)
    mid_hp, mid_mr = target_stats("mid", minute)
    ench_hp, ench_mr = target_stats("enchanter", minute)
    bruiser_hp, bruiser_mr = target_stats("bruiser", minute)

    chain = CastMods(dh_ready=True, luden_ready=False)
    opener = CastMods(dh_ready=True, luden_ready=True)
    dry = CastMods(dh_ready=False, luden_ready=False)
    with_q = CastMods(dh_ready=True, luden_ready=False, q_shred=q_shred(load.level))

    notes = []
    if load.luden:
        notes.append("Echo")
    if load.malignance:
        notes.append("Hatefog")
    if load.infinity_orb:
        notes.append("IO <40%")
    if load.horizon:
        notes.append("Focus after 1st hit")
    if any(n == "Void Staff" for n in names):
        notes.append("40% pen")
    elif any(n == "Void Amethyst" for n in names):
        notes.append("10% pen")
    pen_txt = f"{load.flat_pen:.0f} flat"
    if load.pct_pens:
        pen_txt += " + " + "/".join(f"{p * 100:.0f}%" for p in load.pct_pens)
    notes.append(pen_txt)
    if "Rabadon's Deathcap" in names:
        notes.append("30% AP")
    elif "Needlessly Large Rod" in names:
        notes.append("rod toward Cap")

    return Snapshot(
        minute=minute,
        build=build,
        secondary=secondary,
        items=names,
        gold=gold_at_minute(minute),
        level=load.level,
        ap=round(load.ap, 1),
        ah=load.ah,
        mana_pool=round(max_mana(load), 1),
        r_cd=round(r_cooldown(load), 3),
        souls=load.souls,
        chain_adc=kill_line(load, adc_hp, adc_mr, chain),
        chain_mid=kill_line(load, mid_hp, mid_mr, chain),
        chain_ench=kill_line(load, ench_hp, ench_mr, chain),
        chain_bruiser=kill_line(load, bruiser_hp, bruiser_mr, chain),
        open_adc=kill_line(load, adc_hp, adc_mr, opener),
        dry_adc=kill_line(load, adc_hp, adc_mr, dry),
        chain_adc_q=kill_line(load, adc_hp, adc_mr, with_q),
        adc_hp=adc_hp,
        adc_mr=adc_mr,
        mid_hp=mid_hp,
        mid_mr=mid_mr,
        notes=", ".join(notes) if notes else "components",
    )


def pattern_score(snaps: Sequence[Snapshot]) -> float:
    total = 0.0
    weight = 0.0
    for s in snaps:
        if s.level < 5:
            continue
        w = 1.35 if 8 <= s.minute <= 16 else 1.0
        value = 0.50 * s.chain_adc + 0.30 * s.chain_mid + 0.20 * s.chain_ench
        if s.chain_adc >= 0.399:
            value += 0.06
        if s.chain_mid >= 0.399:
            value += 0.04
        if s.chain_ench >= 0.399:
            value += 0.03
        value += 0.05 * s.open_adc
        total += value * w
        weight += w
    return total / weight if weight else 0.0


def run_all() -> Dict[Tuple[str, str], List[Snapshot]]:
    results: Dict[Tuple[str, str], List[Snapshot]] = {}
    for build, path in BUILD_PATHS.items():
        for secondary in SECONDARIES:
            results[(build, secondary)] = [
                snapshot_for(build, path, minute, secondary)
                for minute in range(1, GAME_MINUTES + 1)
            ]
    return results


def best_key(results: Dict[Tuple[str, str], List[Snapshot]]) -> Tuple[str, str]:
    return max(results, key=lambda k: pattern_score(results[k]))


# ---------------------------------------------------------------------------
# Same-target spam (the pattern this build refuses) and a kill chain.
# ---------------------------------------------------------------------------


@dataclass
class Shot:
    index: int
    pre_hp: float
    pre_frac: float
    damage: float
    killed: bool
    dh_used: bool
    luden_used: bool
    mana_cost: int


def spam_one_target(
    load: Loadout,
    max_hp: float,
    mr: float,
    *,
    start_frac: float = 1.0,
    q: float = 0.0,
) -> Tuple[List[Shot], float, float]:
    """Dump R on one champion from start_frac until they die or mana stops.

    Returns shots, HP left, mana left.
    """
    hp = max_hp * start_frac
    mana = max_mana(load)
    shots: List[Shot] = []
    dh_ready_at = 0.0
    luden_ready_at = 0.0
    clock = 0.0
    marked = False
    shredded = False
    cd = r_cooldown(load)
    for index in range(12):
        if hp <= 1:
            break
        cost = r_mana_cost(index)
        if mana < cost:
            break
        frac = hp / max_hp
        mods = CastMods(
            dh_ready=clock + 1e-6 >= dh_ready_at,
            luden_ready=clock + 1e-6 >= luden_ready_at and load.luden,
            marked=marked,
            hatefog_shred=shredded,
            q_shred=q,
        )
        dmg = cast_damage(load, frac, mr, mods)
        mana -= cost
        killed = dmg >= hp - 0.05
        dh_used = mods.dh_ready and frac < DH_HP
        shots.append(
            Shot(
                index=index + 1,
                pre_hp=hp,
                pre_frac=frac,
                damage=dmg,
                killed=killed,
                dh_used=dh_used,
                luden_used=mods.luden_ready,
                mana_cost=cost,
            )
        )
        hp = max(0.0, hp - dmg)
        if dh_used:
            dh_ready_at = clock + (1.0 if killed or hp <= 0 else 20.0)
        if mods.luden_ready:
            luden_ready_at = clock + 9.0
        marked = True
        shredded = load.malignance
        step = max(cd, 0.05)
        clock += step
        mana = min(max_mana(load), mana + mana_per_sec(load) * step)
        if killed or hp <= 0:
            break
    return shots, hp, mana


def chain_kills(
    load: Loadout,
    targets: Sequence[Tuple[str, float, float, float]],
) -> List[Tuple[str, Shot]]:
    """One R per champion. Wait max(R cd, 1.0s) so Dark Harvest's reset is up.

    Each target starts at `start_frac` of their max HP. Luden only on the
    first cast. New targets are not pre-marked.
    """
    mana = max_mana(load)
    clock = 0.0
    cd = r_cooldown(load)
    step = max(cd, 1.0)
    out: List[Tuple[str, Shot]] = []
    for i, (name, max_hp, mr, start_frac) in enumerate(targets):
        hp = max_hp * start_frac
        cost = r_mana_cost(i)
        if mana < cost or hp <= 0:
            break
        mods = CastMods(dh_ready=True, luden_ready=(i == 0))
        dmg = cast_damage(load, start_frac, mr, mods)
        mana -= cost
        shot = Shot(
            index=i + 1,
            pre_hp=hp,
            pre_frac=start_frac,
            damage=dmg,
            killed=dmg >= hp - 0.05,
            dh_used=start_frac < DH_HP,
            luden_used=i == 0 and load.luden,
            mana_cost=cost,
        )
        out.append((name, shot))
        clock += step
        mana = min(max_mana(load), mana + mana_per_sec(load) * step)
    return out


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------


def pct(frac: float) -> str:
    return f"{frac * 100:5.1f}%"


def first_minute(snaps: Sequence[Snapshot], pred) -> Optional[int]:
    for s in snaps:
        if pred(s):
            return s.minute
    return None


def summarize(results: Dict[Tuple[str, str], List[Snapshot]]) -> str:
    winner_key = best_key(results)
    winner = results[winner_key]
    w_build, w_sec = winner_key

    # Best secondary per item path, for the comparison table.
    best_by_build: Dict[str, Tuple[str, float]] = {}
    for (build, secondary), snaps in results.items():
        score = pattern_score(snaps)
        prev = best_by_build.get(build)
        if prev is None or score > prev[1]:
            best_by_build[build] = (secondary, score)

    lines: List[str] = []
    lines.append("=" * 88)
    lines.append("WILD RIFT — AP KOG'MAW MID  ·  FOG R  ·  DARK HARVEST  ·  EVERY R IS A KILL")
    lines.append("Patch 7.3d. R base 80/120/160 + 25% AP. Below 40% HP: 200/280/360 + 50% AP.")
    lines.append("Dark Harvest: 35 + 11/soul + 5% AP, below 50% HP, 20s CD, reset to 1s on takedown.")
    lines.append("Game: 18:00 even mid. Metric: highest current HP% at which ONE R kills.")
    lines.append("=" * 88)
    lines.append("")
    lines.append("PRESS RULE")
    lines.append("  Spam is allowed only inside the kill line. Above the line the glob is chip,")
    lines.append("  and if they are under 50% HP that chip also puts Dark Harvest on a 20s CD.")
    lines.append("  Chain casts (Echo on cooldown) are the number that has to hold for EVERY R.")
    lines.append("  Wait 1.0s between takedowns so the Harvest reset is up. Do not queue early.")
    lines.append("")
    lines.append("RUNE PAGE")
    lines.append("  Keystone: Dark Harvest")
    lines.append("  Domination: Eyeball Collection (3 AP × takedowns, cap 8). Other dom slots")
    lines.append("  do not add artillery damage (no dash for Sudden Impact, R does not impair).")
    lines.append(f"  Off-tree: {w_sec}  — best of Axiom (+8% ult, R is AoE so not 12%),")
    lines.append("  Coup de Grace (+8% damage below 40% HP), Scorch (21–49 magic, 1s later).")
    lines.append("")
    lines.append("GOLD / LEVEL / TARGETS")
    lines.append(
        f"  {'Min':>3}  {'Gold':>6}  {'Lvl':>3}  {'ADC HP':>7}  {'ADC MR':>6}  "
        f"{'Mid HP':>7}  {'Mid MR':>6}  {'Ench HP':>7}"
    )
    for minute in (1, 4, 6, 8, 10, 12, 14, 16, 18):
        adc_hp, adc_mr = target_stats("adc", minute)
        mid_hp, mid_mr = target_stats("mid", minute)
        ench_hp, _ = target_stats("enchanter", minute)
        lines.append(
            f"  {minute:>3}  {gold_at_minute(minute):>6}  {level_at_minute(minute):>3}  "
            f"{adc_hp:>7.0f}  {adc_mr:>6.0f}  {mid_hp:>7.0f}  {mid_mr:>6.0f}  {ench_hp:>7.0f}"
        )

    lines.append("")
    lines.append("-" * 88)
    lines.append(f"WINNER OVER TIME  —  {w_build}  |  {w_sec}")
    lines.append("Chain = the cast every follow-up R must match (DH up, Echo down).")
    lines.append("Open = Echo ready, only if the build owns Luden. Dry = Dark Harvest down. Q+R = Caustic Spittle shred already on them.")
    lines.append("-" * 88)
    lines.append(
        f"  {'Min':>3}  {'ADC':>7}  {'Mid':>7}  {'Ench':>7}  {'Bruiser':>8}  "
        f"{'Open':>7}  {'Dry':>7}  {'Q+R':>7}"
    )
    for s in winner:
        if s.minute not in (4, 6, 8, 9, 10, 11, 12, 13, 14, 16, 18):
            continue
        if s.level < 5:
            continue
        lines.append(
            f"  {s.minute:>3}  {pct(s.chain_adc):>7}  {pct(s.chain_mid):>7}  "
            f"{pct(s.chain_ench):>7}  {pct(s.chain_bruiser):>8}  {pct(s.open_adc):>7}  "
            f"{pct(s.dry_adc):>7}  {pct(s.chain_adc_q):>7}"
        )
        lines.append(f"       {s.ap:>5.0f} AP  {', '.join(s.items)}")

    lines.append("")
    lines.append("-" * 88)
    lines.append("BUILD COMPARISON — chain kill line vs ADC (best secondary for that path)")
    lines.append("-" * 88)
    lines.append(
        f"  {'Build':<34} {'Rune':<7} {'8:00':>7} {'12:00':>7} {'16:00':>7} {'18:00':>7}  Score"
    )
    ranking = []
    for build, (secondary, score) in best_by_build.items():
        snaps = results[(build, secondary)]
        ranking.append((score, build, secondary, snaps))
    ranking.sort(reverse=True)
    for score, build, secondary, snaps in ranking:
        lines.append(
            f"  {build:<34} {secondary:<7} {pct(snaps[7].chain_adc):>7} "
            f"{pct(snaps[11].chain_adc):>7} {pct(snaps[15].chain_adc):>7} "
            f"{pct(snaps[17].chain_adc):>7}  {score:.3f}"
        )

    lines.append("")
    lines.append("-" * 88)
    lines.append(f"SECONDARY ON THE WINNING ITEMS ({w_build}) — chain ADC line")
    lines.append("-" * 88)
    lines.append(f"  {'Rune':<8} {'8:00':>7} {'12:00':>7} {'16:00':>7} {'18:00':>7}  What it does")
    rune_blurb = {
        "Axiom": "+8% ultimate damage on every R (AoE rate, not 12%)",
        "Coup": "+8% to all damage only while they are under 40% HP",
        "Scorch": "21–49 magic damage, 1 second after the glob",
    }
    for secondary in SECONDARIES:
        snaps = results[(w_build, secondary)]
        lines.append(
            f"  {secondary:<8} {pct(snaps[7].chain_adc):>7} {pct(snaps[11].chain_adc):>7} "
            f"{pct(snaps[15].chain_adc):>7} {pct(snaps[17].chain_adc):>7}  {rune_blurb[secondary]}"
        )

    # Concrete gates at key minutes.
    lines.append("")
    lines.append("-" * 88)
    lines.append("WHEN EVERY R YOU PRESS IS A KILL  (chain cast: Dark Harvest up, Echo not required)")
    lines.append("Press only at or under the percent. That cast kills. Above it, do not cast.")
    lines.append("-" * 88)
    for minute in (8, 10, 12, 14, 16, 18):
        s = winner[minute - 1]
        adc_gate = s.chain_adc * s.adc_hp
        mid_gate = s.chain_mid * s.mid_hp
        adc_state = (
            "ADC: any R under 40% HP kills"
            if s.chain_adc >= 0.399
            else "ADC: 40% HP is not lethal yet"
        )
        lines.append(
            f"  {minute:>2}:00  ADC ≤ {s.chain_adc * 100:4.1f}% ({adc_gate:4.0f} HP)  "
            f"mid ≤ {s.chain_mid * 100:4.1f}% ({mid_gate:4.0f} HP)  "
            f"ench ≤ {s.chain_ench * 100:4.1f}%   {adc_state}"
        )
        lines.append(
            f"         bruiser ≤ {s.chain_bruiser * 100:4.1f}%   "
            f"dry (no DH) ADC ≤ {s.dry_adc * 100:4.1f}%   "
            f"if Q shred is already on them, ADC ≤ {s.chain_adc_q * 100:4.1f}%"
        )

    lines.append("")
    lines.append("-" * 88)
    lines.append("ONE GLOB vs ADC  —  same cast, three HP bars. This is the execute jump.")
    lines.append("-" * 88)
    for minute in (12, 18):
        s = winner[minute - 1]
        load = build_loadout(s.items, minute, w_sec)
        adc_hp, adc_mr = target_stats("adc", minute)
        lines.append(f"  {minute}:00  ADC {adc_hp:.0f} HP / {adc_mr:.0f} MR  AP {s.ap:.0f}")
        rows = (
            (1.0, "full"),
            (0.50, "50%"),
            (0.39, "39% execute"),
            (max(s.chain_adc - 0.001, 0.05), f"line {s.chain_adc * 100:.1f}%"),
        )
        for frac, label in rows:
            dmg = cast_damage(load, frac, adc_mr, CastMods(dh_ready=True, luden_ready=False))
            kills = dmg >= frac * adc_hp - 0.05
            lines.append(
                f"      {label:<12} {dmg:5.0f} dmg   "
                f"{'KILLS' if kills else 'does not kill'}   "
                f"({dmg / adc_hp * 100:4.1f}% of max HP)"
            )

    # Wrong pattern vs right pattern at two spikes.
    lines.append("")
    lines.append("-" * 88)
    lines.append("DUMPING R ON A FULL HP ADC  —  chip, then the pool runs out")
    lines.append("-" * 88)
    for minute in (10, 14, 18):
        s = winner[minute - 1]
        load = build_loadout(s.items, minute, w_sec)
        adc_hp, adc_mr = target_stats("adc", minute)
        shots, hp_left, mana_left = spam_one_target(load, adc_hp, adc_mr, start_frac=1.0)
        if not shots:
            lines.append(f"  {minute}:00  no cast")
            continue
        kill_shot = next((sh.index for sh in shots if sh.killed), None)
        lines.append(
            f"  {minute}:00 ADC {adc_hp:.0f} HP / {adc_mr:.0f} MR   shots {len(shots)}   "
            f"killing shot: {kill_shot if kill_shot else 'none'}"
        )
        for sh in shots:
            tag = "KILL" if sh.killed else "chip"
            extra = []
            if sh.luden_used:
                extra.append("echo")
            if sh.dh_used:
                extra.append("DH")
            extra_s = f" ({', '.join(extra)})" if extra else ""
            lines.append(
                f"      R{sh.index}  {sh.pre_frac * 100:5.1f}% → {sh.damage:5.0f} dmg  "
                f"mana {sh.mana_cost:<3}  {tag}{extra_s}"
            )
        if kill_shot is None:
            nxt = r_mana_cost(len(shots))
            lines.append(
                f"      left at {hp_left / adc_hp * 100:4.1f}% ({hp_left:.0f} HP), "
                f"mana {mana_left:.0f}, next R costs {nxt}. The pool dies before the kill."
            )

    lines.append("")
    lines.append("-" * 88)
    lines.append("KILL CHAIN  —  one R per champion, each already standing on their own line")
    lines.append("R1 may include Echo if Luden is owned and up. R2 and R3 do not. DH is up on all three.")
    lines.append("-" * 88)
    for minute in (12, 16, 18):
        s = winner[minute - 1]
        load = build_loadout(s.items, minute, w_sec)
        targets = []
        for kind, line in (
            ("adc", s.chain_adc),
            ("mid", s.chain_mid),
            ("enchanter", s.chain_ench),
        ):
            hp, mr = target_stats(kind, minute)
            frac = max(0.05, line - 0.005)
            targets.append((kind, hp, mr, frac))
        chain = chain_kills(load, targets)
        bits = []
        for name, sh in chain:
            state = "dies" if sh.killed else "LIVES"
            bits.append(f"{name} {state} ({sh.damage:.0f} dmg on {sh.pre_hp:.0f} HP)")
        lines.append(
            f"  {minute}:00  " + "   ".join(bits)
            + f"    R cd {s.r_cd:.2f}s  mana pool {s.mana_pool:.0f}"
        )

    late = winner[-1]
    midgame = winner[11]  # 12:00
    early = winner[7]  # 8:00
    owns_luden = "Luden's Echo" in late.items
    q_bump = (late.chain_adc_q - late.chain_adc) * 100
    horizon_key = (
        "Luden → IO → Horizon → Cap",
        best_by_build["Luden → IO → Horizon → Cap"][0],
    )
    foil_key = (
        "Malig → Liandry → Void",
        best_by_build["Malig → Liandry → Void"][0],
    )
    horizon_late = results[horizon_key][-1].chain_adc
    foil_late = results[foil_key][-1].chain_adc
    # 11:00 is the ADC MR-component minute. Call it out when the line actually drops.
    mr_dip = winner[9].chain_adc - winner[10].chain_adc

    lines.append("")
    lines.append("-" * 88)
    lines.append("VERDICT")
    lines.append("-" * 88)
    lines.append(f"  Items: {w_build}")
    lines.append(f"  18:00 inventory: {', '.join(late.items)}")
    lines.append(f"  Rune:  Dark Harvest + Eyeball Collection + {w_sec}")
    lines.append(f"  Pattern score: {pattern_score(winner):.3f}")
    lines.append(
        f"  18:00 press R at or under  ADC {late.chain_adc * 100:.1f}%"
        f" ({late.chain_adc * late.adc_hp:.0f} HP)"
        f"   mid {late.chain_mid * 100:.1f}%"
        f" ({late.chain_mid * late.mid_hp:.0f} HP)"
        f"   enchanter {late.chain_ench * 100:.1f}%"
        f"   bruiser {late.chain_bruiser * 100:.1f}%"
    )
    if late.chain_adc >= 0.399:
        lines.append("  ADC: any Living Artillery into a target under 40% HP kills.")
    else:
        lines.append(
            f"  ADC: a target at 40% HP still lives. Wait until {late.chain_adc * 100:.1f}%."
        )
    if late.chain_mid >= 0.399:
        lines.append("  Mid: any R under 40% HP kills.")
    else:
        lines.append(
            f"  Mid: 40% HP is not lethal. The line is {late.chain_mid * 100:.1f}%."
        )
    if late.chain_ench >= 0.399:
        lines.append("  Enchanter: any R under 40% HP kills.")
    else:
        lines.append(
            f"  Enchanter: line is {late.chain_ench * 100:.1f}%, not the whole 40% bracket."
        )
    if late.chain_adc >= 0.50:
        lines.append("  The ADC line is at or above 50%, so Dark Harvest is inside every legal cast.")
    else:
        lines.append("  The line stays under 50% HP. Harvest is on the kill shot because you")
        lines.append("  waited until they were already under 50%, not because the glob reaches half.")
    lines.append(
        f"  No Harvest: ADC line drops to {late.dry_adc * 100:.1f}%."
        f"  Do not spend the rune on a chip."
    )
    lines.append("")
    lines.append(
        f"  8:00  ADC {early.chain_adc * 100:.1f}% / mid {early.chain_mid * 100:.1f}%  "
        f"AP {early.ap:.0f}  [{early.notes}]"
    )
    lines.append(
        f"  12:00 ADC {midgame.chain_adc * 100:.1f}% / mid {midgame.chain_mid * 100:.1f}%  "
        f"AP {midgame.ap:.0f}  [{midgame.notes}]"
    )
    lines.append(
        f"  18:00 ADC {late.chain_adc * 100:.1f}% / mid {late.chain_mid * 100:.1f}%  "
        f"AP {late.ap:.0f}  dry {late.dry_adc * 100:.1f}%  "
        f"with Q shred {late.chain_adc_q * 100:.1f}%  [{late.notes}]"
    )
    if not owns_luden and abs(late.open_adc - late.chain_adc) < 0.002:
        lines.append("  No Luden in the finished inventory, so a staggered shot matches the chain shot.")
    elif owns_luden:
        lines.append(
            f"  Echo opener vs ADC is {late.open_adc * 100:.1f}%."
            " Only the first target of a fight gets Echo. R2/R3 use the chain line."
        )
    lines.append("")
    lines.append("  WHY THIS PATH")
    lines.append("  • Full-HP Living Artillery is 25% AP. One glob does not remove a healthy")
    lines.append("    bar. The kill is the under-40% formula (200/280/360 + 50% AP), Infinity")
    lines.append("    Orb's 20% on that same bracket, Coup de Grace, and Dark Harvest.")
    lines.append("  • Flat pen and Void's 40% pen are what make that execute clear the")
    lines.append("    remaining HP. Horizon Focus is +10% only after you have already hit")
    lines.append(
        f"    the target, so it misses a one-R kill. At 18:00 the Horizon path's ADC"
    )
    lines.append(
        f"    line is {horizon_late * 100:.1f}% against {late.chain_adc * 100:.1f}% here."
    )
    lines.append("  • Liandry does not move a one-cast kill. At 18:00 that foil sits at")
    lines.append(f"    {foil_late * 100:.1f}% ADC. Hatefog's 10 MR shred hits the next glob, not this one.")
    lines.append("  • Luden's Echo raises the first cast and is down for 9s. The score")
    lines.append("    uses the naked follow-up, because spam means R2 and R3 still have to kill.")
    if "Rabadon's Deathcap" not in late.items:
        lines.append("  • Deathcap is not finished on even-mid gold by 18:00. The rod in the")
        lines.append("    inventory is the start of it, not the 30% multiplier.")
    if mr_dip > 0.03:
        lines.append(
            f"  • 11:00 the ADC picks up an MR component and the line drops "
            f"{mr_dip * 100:.1f} points until the next pen item."
        )
    if q_bump < 3:
        lines.append(
            f"  • Q shred adds {q_bump:.1f} points at 18:00. Pen has already eaten most of"
        )
        lines.append("    the ADC's MR, so the bush spit is a small bump, not the build.")
    else:
        lines.append(
            f"  • A Q from the same bush before you R adds {q_bump:.1f} points to the ADC line."
        )
    # Second place, so the crossover is visible.
    if len(ranking) > 1:
        _score2, build2, _sec2, snaps2 = ranking[1]
        lines.append(
            f"  • Next path ({build2}) is ADC {snaps2[7].chain_adc * 100:.1f}% at 8:00,"
            f" {snaps2[11].chain_adc * 100:.1f}% at 12:00,"
            f" {snaps2[15].chain_adc * 100:.1f}% at 16:00."
            f" This path is {early.chain_adc * 100:.1f}% / {midgame.chain_adc * 100:.1f}% /"
            f" {winner[15].chain_adc * 100:.1f}%."
        )
        if w_build.startswith("IO") and abs(snaps2[15].chain_adc - winner[15].chain_adc) < 0.008:
            lines.append(
                "    Those paths finish the same pen stack. The gap is earlier:"
                " Infinity Orb is the execute amp, so it is the first legendary."
            )
    lines.append("")
    lines.append("  HOW TO SPAM")
    lines.append("  1. Sit in fog. Do not open on a full HP bar. That glob is chip, and under")
    lines.append("     50% HP it also puts Dark Harvest on a 20s cooldown.")
    lines.append("  2. Press R only when their current HP% is at or under the chain line.")
    lines.append("  3. That cast kills. Harvest resets to 1s. Wait that second, then the")
    lines.append("     next champion under their own line dies to the next R.")
    lines.append("  4. If Harvest is down, use the dry line or do not cast.")
    lines.append("  5. Skip bruisers until their printed percent. One R is not a tank button.")
    lines.append("  6. Mana ramps 50 → 500 if you chain inside 8s. Three kill shots cost")
    lines.append("     50+100+150. Base mana pays for that. It does not pay for chipping")
    lines.append("     one full bar down to the line by yourself.")
    lines.append("")
    lines.append("  Skill order: R at 5/9/13, then Q, then E, W last.")
    lines.append("  W max is the on-hit build. This one does not auto from fog.")
    lines.append("=" * 88)
    return "\n".join(lines)


def export_json(results, path: Path) -> None:
    winner = best_key(results)
    payload = {
        "meta": {
            "champion": "Kog'Maw",
            "game": "Wild Rift",
            "patch": "7.3d",
            "role": "mid",
            "playstyle": "spam Living Artillery from fog, only inside the kill line",
            "keystone": "Dark Harvest",
            "winner_build": winner[0],
            "winner_secondary": winner[1],
            "game_minutes": GAME_MINUTES,
        },
        "builds": {
            f"{build} | {secondary}": [
                {
                    "minute": s.minute,
                    "items": s.items,
                    "gold": s.gold,
                    "level": s.level,
                    "ap": s.ap,
                    "mana_pool": s.mana_pool,
                    "r_cd": s.r_cd,
                    "souls": s.souls,
                    "chain_adc": round(s.chain_adc, 4),
                    "chain_mid": round(s.chain_mid, 4),
                    "chain_ench": round(s.chain_ench, 4),
                    "chain_bruiser": round(s.chain_bruiser, 4),
                    "open_adc": round(s.open_adc, 4),
                    "dry_adc": round(s.dry_adc, 4),
                    "chain_adc_q": round(s.chain_adc_q, 4),
                    "notes": s.notes,
                }
                for s in snaps
            ]
            for (build, secondary), snaps in results.items()
        },
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------


def self_check(results: Dict[Tuple[str, str], List[Snapshot]]) -> None:
    # Formula fixture: 400 AP, no pen, 0 MR, execute region, no runes / no DH.
    bare = Loadout(
        ap=400, ah=0, ult_haste=0, mana=0, mana_regen=0, flat_pen=0, pct_pens=(),
        luden=False, malignance=False, infinity_orb=False, horizon=False,
        names=[], secondary="Axiom", level=15, minute=18, souls=0, eyeballs=0,
    )
    # Axiom is on, which amps R. Build a no-rune loadout by using a fake secondary.
    bare.secondary = "None"
    # 0 souls but DH would still add 35 + 5% AP if ready. Turn DH off.
    line = kill_line(bare, 2000, 0.0, CastMods(dh_ready=False))
    # Execute raw = 360 + 200 = 560. Line = 560/2000 = 0.28, and 0.28 < 0.40 so execute applies.
    assert abs(line - 0.28) < 0.005, line

    io = Loadout(**{**bare.__dict__, "infinity_orb": True})
    line_io = kill_line(io, 2000, 0.0, CastMods(dh_ready=False))
    # 560 * 1.2 = 672; 672/2000 = 0.336
    assert abs(line_io - 0.336) < 0.005, line_io
    assert line_io > line

    # Pen order: 100 MR, 40% then 8%, then 18 flat → 100*0.6*0.92 - 18 = 37.2
    eff = effective_mr(100, pct_pens=(0.40, 0.08), flat_pen=18)
    assert abs(eff - 37.2) < 0.01, eff

    # Spellslinger cannot be owned before minute 10 even with infinite-looking gold.
    early = resolve_inventory(BUILD_PATHS["Storm → IO → Void → Cap"], 20000, 9)
    assert "Spellslinger's Shoes" not in early, early
    later = resolve_inventory(BUILD_PATHS["Storm → IO → Void → Cap"], 20000, 10)
    assert "Spellslinger's Shoes" in later, later

    # Full-HP one-shot is not a thing at minute 12.
    winner = results[best_key(results)]
    assert winner[11].chain_adc < 0.85, winner[11].chain_adc
    assert winner[11].open_adc < 0.90

    # Echo opener is at least the naked chain line.
    assert winner[15].open_adc + 1e-6 >= winner[15].chain_adc

    # Q shred raises the ADC line once Q exists.
    assert winner[11].chain_adc_q >= winner[11].chain_adc

    # Burn foil does not beat the pen stack at 16:00 on the chain ADC line.
    foil_key = max(
        (k for k in results if k[0] == "Malig → Liandry → Void"),
        key=lambda k: pattern_score(results[k]),
    )
    pen_key = best_key(results)
    assert results[pen_key][15].chain_adc >= results[foil_key][15].chain_adc - 0.005

    # More AP does not lower the line.
    richer = Loadout(**{**bare.__dict__, "ap": 700, "secondary": "None"})
    assert kill_line(richer, 2000, 0.0, CastMods(dh_ready=False)) > line

    # Inventory crafts Luden out of components and spends gold.
    luden_items = resolve_inventory(["Luden's Echo"], 2800, 8)
    assert "Luden's Echo" in luden_items, luden_items
    assert "Lost Chapter" not in luden_items
    broke = resolve_inventory(["Luden's Echo"], 2000, 8)
    assert "Luden's Echo" not in broke
    full = resolve_inventory(BUILD_PATHS["Storm → IO → Void → Cap"], 20000, 18)
    assert "Void Staff" in full and "Void Amethyst" not in full, full
    assert "Rabadon's Deathcap" in full and "Needlessly Large Rod" not in full, full
    assert "Infinity Orb" in full and "Stormsurge" in full


def main() -> None:
    results = run_all()
    self_check(results)
    report = summarize(results)
    print(report)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "report.txt").write_text(report + "\n", encoding="utf-8")
    export_json(results, OUT_DIR / "results.json")
    print(f"\nWrote {OUT_DIR / 'report.txt'} and {OUT_DIR / 'results.json'}")


if __name__ == "__main__":
    main()
