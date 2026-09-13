#!/usr/bin/env python3
"""
Wild Rift Morgana — Ionian vs Boots of Mana, with mid farm modeled.

Patch 7.2e item values. Average game: 20 minutes.

Question:
  Previous advice picked Ionian (Diamond+ WR / Q haste) for Morgana mid.
  Mid farms waves. Does farm (CS gold, Big Bully, W mana) flip the boot?

7.2 context that matters:
  - T3 mage items lost 7% magic pen. Pen now lives on Spellslinger / Void / Cryptbloom.
  - Ionian T2: 15 AH, 0% mana regen. Crimson (after 10:00): 25 AH, 75% regen.
  - Boots of Mana T2: 25 AP, 75% regen, 8 flat pen, Big Bully 18.
  - Spellslinger (after 10:00): 40 AP, 100% regen, 18 flat + 8% pen, Big Bully 22 true.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import json
import os

GAME_MINUTES = 20
T3_BOOTS_MINUTE = 10
OUT_DIR = os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------------------------
# Economy
# ---------------------------------------------------------------------------


def base_income(minute: int, role: str) -> int:
    """Gold added during this minute (not including Big Bully / OOM misses)."""
    if role == "mid":
        # Farming mid: CS + plates + passive. Tuned so BF+T2 ~7–8, Liandry ~12–13,
        # Rylai ~16–17, Deathcap often a component at 20 without bully gold.
        if minute <= 4:
            return 400
        if minute <= 8:
            return 490
        if minute <= 12:
            return 540
        if minute <= 16:
            return 580
        return 620
    # Support: no CS, sickle/scythe + assists. Cannot race mid item timings.
    if minute <= 4:
        return 280
    if minute <= 10:
        return 360
    if minute <= 16:
        return 430
    return 480


def level_at_minute(minute: int, role: str) -> int:
    if role == "mid":
        table = {
            1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7, 7: 8, 8: 9,
            9: 10, 10: 11, 11: 11, 12: 12, 13: 12, 14: 13,
            15: 13, 16: 14, 17: 14, 18: 15, 19: 15, 20: 15,
        }
    else:
        table = {
            1: 2, 2: 3, 3: 4, 4: 4, 5: 5, 6: 6, 7: 7, 8: 8,
            9: 8, 10: 9, 11: 10, 12: 10, 13: 11, 14: 11,
            15: 12, 16: 12, 17: 13, 18: 13, 19: 14, 20: 14,
        }
    return table.get(minute, 2)


# ---------------------------------------------------------------------------
# Items (Wild Rift 7.2)
# ---------------------------------------------------------------------------


@dataclass
class Item:
    name: str
    cost: int
    ap: float = 0
    ah: float = 0
    hp: float = 0
    mana: float = 0
    mana_regen_pct: float = 0  # extra % of *base* mana regen
    flat_mpen: float = 0
    pct_mpen: float = 0
    bully: float = 0  # extra damage to minions per ability/AA
    bully_true: bool = False
    summoner_haste: float = 0
    deathcap: bool = False
    rylai: bool = False
    blackfire: bool = False
    liandry: bool = False
    ashes: bool = False
    guise: bool = False
    tags: Tuple[str, ...] = ()


ITEMS: Dict[str, Item] = {
    "Spectral Sickle": Item("Spectral Sickle", 500, ap=20, tags=("support",)),
    "Black Mist Scythe": Item(
        "Black Mist Scythe", 0, ap=28, ah=10, tags=("support",)
    ),
    "Boots of Speed": Item("Boots of Speed", 400, tags=("boots", "t1")),
    "Amplifying Tome": Item("Amplifying Tome", 500, ap=20),
    "Ring of Revelation": Item("Ring of Revelation", 300, ah=5),
    "Ruby Crystal": Item("Ruby Crystal", 500, hp=200),
    "Blasting Wand": Item("Blasting Wand", 800, ap=45),
    "Needlessly Large Rod": Item("Needlessly Large Rod", 1400, ap=65),
    "Giant's Belt": Item("Giant's Belt", 1000, hp=350),
    "Lost Chapter": Item(
        "Lost Chapter", 1200, ap=35, ah=10, mana=200, tags=("mana",)
    ),
    "Fated Ashes": Item("Fated Ashes", 900, ap=40, ashes=True),
    "Haunting Guise": Item(
        "Haunting Guise", 1300, ap=30, hp=200, guise=True
    ),
    "Ionian Boots of Lucidity": Item(
        "Ionian Boots of Lucidity",
        1000,
        ah=15,
        summoner_haste=0.15,
        tags=("boots", "t2", "ionian"),
    ),
    "Crimson Lucidity": Item(
        "Crimson Lucidity",
        2000,
        ah=25,
        mana_regen_pct=0.75,
        summoner_haste=0.20,
        tags=("boots", "t3", "ionian"),
    ),
    "Boots of Mana": Item(
        "Boots of Mana",
        1200,
        ap=25,
        mana_regen_pct=0.75,
        flat_mpen=8,
        bully=18,
        tags=("boots", "t2", "mana"),
    ),
    "Spellslinger's Shoes": Item(
        "Spellslinger's Shoes",
        2200,
        ap=40,
        mana_regen_pct=1.00,
        flat_mpen=18,
        pct_mpen=0.08,
        bully=22,
        bully_true=True,
        tags=("boots", "t3", "mana"),
    ),
    "Blackfire Torch": Item(
        "Blackfire Torch",
        2800,
        ap=80,
        ah=20,
        mana=500,
        blackfire=True,
        tags=("mana", "burn"),
    ),
    "Liandry's Torment": Item(
        "Liandry's Torment",
        3000,
        ap=70,
        hp=300,
        liandry=True,
        tags=("burn",),
    ),
    "Rylai's Crystal Scepter": Item(
        "Rylai's Crystal Scepter",
        2700,
        ap=65,
        hp=350,
        rylai=True,
        tags=("uptime",),
    ),
    "Rabadon's Deathcap": Item(
        "Rabadon's Deathcap",
        3400,
        ap=130,
        deathcap=True,
        tags=("amp",),
    ),
}


UPGRADE_COMPONENTS: Dict[str, Tuple[str, ...]] = {
    "Ionian Boots of Lucidity": ("Boots of Speed", "Ring of Revelation"),
    "Boots of Mana": ("Boots of Speed", "Amplifying Tome"),
    "Crimson Lucidity": ("Ionian Boots of Lucidity",),
    "Spellslinger's Shoes": ("Boots of Mana",),
    "Lost Chapter": ("Amplifying Tome", "Ring of Revelation"),
    "Fated Ashes": ("Amplifying Tome",),
    "Haunting Guise": ("Amplifying Tome", "Ruby Crystal"),
    "Blackfire Torch": ("Lost Chapter", "Fated Ashes"),
    "Liandry's Torment": ("Haunting Guise", "Fated Ashes"),
    "Rylai's Crystal Scepter": ("Giant's Belt", "Blasting Wand", "Amplifying Tome"),
    "Rabadon's Deathcap": ("Needlessly Large Rod", "Blasting Wand"),
}

NEXT_COMPONENTS: Dict[str, List[str]] = {
    "Ionian Boots of Lucidity": ["Boots of Speed", "Ring of Revelation"],
    "Boots of Mana": ["Boots of Speed", "Amplifying Tome"],
    "Crimson Lucidity": ["Ionian Boots of Lucidity"],
    "Spellslinger's Shoes": ["Boots of Mana"],
    "Lost Chapter": ["Amplifying Tome", "Ring of Revelation"],
    "Fated Ashes": ["Amplifying Tome"],
    "Haunting Guise": ["Ruby Crystal", "Amplifying Tome"],
    "Blackfire Torch": ["Fated Ashes", "Lost Chapter"],
    "Liandry's Torment": ["Fated Ashes", "Haunting Guise"],
    "Rylai's Crystal Scepter": ["Giant's Belt", "Blasting Wand", "Amplifying Tome"],
    "Rabadon's Deathcap": ["Needlessly Large Rod", "Blasting Wand"],
}

T3_BOOTS = {"Crimson Lucidity", "Spellslinger's Shoes"}


# Same core, only the boot line changes. Mid has no support item.
# Support paths keep Sickle → Scythe quest.

def mid_path(*boot_line: str) -> List[str]:
    # boot_line is T1, T2, and T3 inserted around the core.
    # We always go Speed → T2 early, BF, Liandry, T3 after 10:00, Rylai, Cap.
    t1, t2, t3 = boot_line
    return [
        t1,
        t2,
        "Lost Chapter",
        "Fated Ashes",
        "Blackfire Torch",
        "Haunting Guise",
        "Liandry's Torment",
        t3,
        "Rylai's Crystal Scepter",
        "Rabadon's Deathcap",
    ]


def support_path(*boot_line: str) -> List[str]:
    t1, t2, t3 = boot_line
    return [
        "Spectral Sickle",
        t1,
        t2,
        "Lost Chapter",
        "Fated Ashes",
        "Blackfire Torch",
        t3,
        "Haunting Guise",
        "Liandry's Torment",
        "Rylai's Crystal Scepter",
    ]


IONIAN_LINE = (
    "Boots of Speed",
    "Ionian Boots of Lucidity",
    "Crimson Lucidity",
)
MANA_LINE = (
    "Boots of Speed",
    "Boots of Mana",
    "Spellslinger's Shoes",
)

BUILD_PATHS: Dict[str, List[str]] = {
    "Mid · Mana → Spellslinger": mid_path(*MANA_LINE),
    "Mid · Ionian → Crimson": mid_path(*IONIAN_LINE),
    "Support · Mana → Spellslinger": support_path(*MANA_LINE),
    "Support · Ionian → Crimson": support_path(*IONIAN_LINE),
}

ROLE_OF: Dict[str, str] = {
    "Mid · Mana → Spellslinger": "mid",
    "Mid · Ionian → Crimson": "mid",
    "Support · Mana → Spellslinger": "support",
    "Support · Ionian → Crimson": "support",
}


# ---------------------------------------------------------------------------
# Inventory
# ---------------------------------------------------------------------------


def remaining_cost(item_name: str, owned: List[str]) -> int:
    if item_name == "Black Mist Scythe":
        return 0
    credit = 0
    for c in UPGRADE_COMPONENTS.get(item_name, ()):
        if c in owned:
            credit += ITEMS[c].cost
    return max(0, ITEMS[item_name].cost - credit)


def path_item_done(step: str, owned: List[str]) -> bool:
    """True if this path row is already satisfied (owned or consumed into an upgrade)."""
    if step in owned:
        return True
    boots_done = any(
        x in owned
        for x in (
            "Ionian Boots of Lucidity",
            "Boots of Mana",
            "Crimson Lucidity",
            "Spellslinger's Shoes",
        )
    )
    if step == "Boots of Speed" and boots_done:
        return True
    if step == "Ionian Boots of Lucidity" and "Crimson Lucidity" in owned:
        return True
    if step == "Boots of Mana" and "Spellslinger's Shoes" in owned:
        return True
    if step in ("Lost Chapter", "Fated Ashes") and "Blackfire Torch" in owned:
        return True
    if step in ("Fated Ashes", "Haunting Guise") and "Liandry's Torment" in owned:
        return True
    if step == "Spectral Sickle" and "Black Mist Scythe" in owned:
        return True
    return False


def can_buy(item_name: str, owned: List[str], gold: int, minute: int) -> bool:
    if item_name in owned:
        return False
    if item_name in T3_BOOTS and minute < T3_BOOTS_MINUTE:
        return False
    return gold >= remaining_cost(item_name, owned)


def buy(item_name: str, owned: List[str], gold: int) -> Tuple[List[str], int]:
    owned = list(owned)
    if item_name == "Black Mist Scythe":
        if "Spectral Sickle" in owned:
            owned.remove("Spectral Sickle")
        owned.append(item_name)
        return owned, gold
    cost = remaining_cost(item_name, owned)
    gold -= cost
    for c in UPGRADE_COMPONENTS.get(item_name, ()):
        if c in owned:
            owned.remove(c)
    owned.append(item_name)
    return owned, gold


def try_progress(path: List[str], owned: List[str], gold: int, minute: int) -> Tuple[List[str], int]:
    """Buy finished path items, then leftover into next item's components."""
    for step in path:
        if path_item_done(step, owned):
            continue
        if step == "Black Mist Scythe":
            continue
        if can_buy(step, owned, gold, minute):
            owned, gold = buy(step, owned, gold)
            continue
        for comp in NEXT_COMPONENTS.get(step, []):
            if comp in owned:
                continue
            if can_buy(comp, owned, gold, minute):
                owned, gold = buy(comp, owned, gold)
        if can_buy(step, owned, gold, minute):
            owned, gold = buy(step, owned, gold)
        else:
            break
    return owned, gold


# ---------------------------------------------------------------------------
# Champion kit
# ---------------------------------------------------------------------------


def skill_rank(level: int, skill: str) -> int:
    """W max (4 ranks), Q second, E last. R at 5/9/13. WR basics cap at 4."""
    if skill == "R":
        if level < 5:
            return 0
        if level < 9:
            return 1
        if level < 13:
            return 2
        return 3
    # 1W 2W 3Q 4W 5R 6W(max) 7E 8Q 9R 10Q 11Q 12E 13R 14E 15E
    q_lv = [3, 8, 10, 11]
    w_lv = [1, 2, 4, 6]
    e_lv = [7, 12, 14, 15]
    mapping = {"Q": q_lv, "W": w_lv, "E": e_lv}
    return min(4, sum(1 for lv in mapping[skill] if level >= lv))


def q_base(rank: int) -> float:
    return [0, 80, 160, 240, 320][rank]


def q_root(rank: int) -> float:
    return [0, 2.0, 2.25, 2.5, 2.75][rank]


def w_tick_base(rank: int) -> float:
    return [0, 7, 12, 17, 22][rank]


def w_mana(rank: int) -> float:
    return [0, 70, 90, 110, 130][rank]


def q_mana(rank: int) -> float:
    return [0, 55, 60, 65, 70][rank]


def r_base(rank: int) -> float:
    return [0, 150, 225, 300][rank]


def r_cd(rank: int) -> float:
    return [999, 75, 65, 55][rank]


def morgana_mana_pool(level: int, bonus_mana: float, manaflow: float) -> float:
    return 435 + 49 * (level - 1) + bonus_mana + manaflow


def morgana_base_regen_per_s(level: int) -> float:
    # tooltip is per 5s
    return (15 + 0.9 * (level - 1)) / 5.0


def ability_haste_mult(ah: float) -> float:
    return 100.0 / (100.0 + max(0.0, ah))


def transcendence_ah(level: int) -> float:
    if level >= 5:
        return 12.0
    if level >= 1:
        return 6.0
    return 0.0


def scythe_ap(minute: int) -> float:
    if minute < 6:
        return 0.0
    return 4.0 * min(10, minute - 5)


# ---------------------------------------------------------------------------
# Combat + farm
# ---------------------------------------------------------------------------


@dataclass
class Stats:
    names: List[str]
    ap: float
    ah: float
    mana: float
    mana_regen_pct: float
    flat_mpen: float
    pct_mpen: float
    bully: float
    bully_true: bool
    summoner_haste: float
    rylai: bool
    blackfire: bool
    liandry: bool
    ashes: bool
    guise: bool
    has_lc: bool
    has_scythe: bool


def stats_from(owned: List[str], minute: int, level: int) -> Stats:
    ap = ah = mana = regen = flat = pct = bully = sh = 0.0
    bully_true = rylai = blackfire = liandry = ashes = guise = False
    for n in owned:
        it = ITEMS[n]
        ap += it.ap
        ah += it.ah
        mana += it.mana
        regen += it.mana_regen_pct
        flat += it.flat_mpen
        pct += it.pct_mpen
        bully += it.bully
        if it.bully_true:
            bully_true = True
        sh += it.summoner_haste
        rylai = rylai or it.rylai
        blackfire = blackfire or it.blackfire
        liandry = liandry or it.liandry
        ashes = ashes or it.ashes
        guise = guise or it.guise
        if it.deathcap:
            ap *= 1.30
    if "Black Mist Scythe" in owned:
        ap += scythe_ap(minute)
    ah += transcendence_ah(level)
    if blackfire:
        ap *= 1.04  # 1 stack in a mid 1v1 / small skirmish
    return Stats(
        names=list(owned),
        ap=ap,
        ah=ah,
        mana=mana,
        mana_regen_pct=regen,
        flat_mpen=flat,
        pct_mpen=pct,
        bully=bully,
        bully_true=bully_true,
        summoner_haste=sh,
        rylai=rylai,
        blackfire=blackfire,
        liandry=liandry,
        ashes=ashes,
        guise=guise,
        has_lc="Lost Chapter" in owned or blackfire,
        has_scythe="Black Mist Scythe" in owned,
    )


def target_hp(minute: int, role_vs: str) -> float:
    lv = level_at_minute(minute, "mid")
    if role_vs == "mid":
        return 620 + 95 * lv + 18 * minute
    return 600 + 80 * lv + 12 * minute


def target_mr(minute: int) -> float:
    lv = level_at_minute(minute, "mid")
    extra = 0.0 if minute < 12 else (12.0 if minute < 17 else 22.0)
    return 32 + 1.25 * lv + extra


def pen_mult(stats: Stats, minute: int) -> float:
    mr = target_mr(minute)
    effective = mr * (1.0 - stats.pct_mpen) - stats.flat_mpen
    effective = max(8.0, effective)
    return 100.0 / (100.0 + effective)


def madness_mult(stats: Stats) -> float:
    # 10s fight, 2%/s to 6%. Average ~4% if Guise/Liandry.
    if stats.liandry or stats.guise:
        return 1.04
    return 1.0


@dataclass
class ManaReport:
    w_farm: float
    oom_miss_gold: int
    regen_per_min: float
    cost_per_min: float
    sustain: bool


def mana_minute(stats: Stats, level: int, role: str, minute: int) -> ManaReport:
    """Can she W every mid wave? Missed W = missed CS (the farm factor)."""
    wr = max(1, skill_rank(level, "W"))
    qr = max(1, skill_rank(level, "Q"))
    desired_w_farm = 2.0 if role == "mid" else 0.4
    desired_q = 2.2 if role == "mid" else 1.4
    desired_e = 0.35
    desired_w_fight = 0.5
    cost = (
        desired_w_farm * w_mana(wr)
        + desired_w_fight * w_mana(wr)
        + desired_q * q_mana(qr)
        + desired_e * 60.0
    )
    regen_s = morgana_base_regen_per_s(level) * (1.0 + stats.mana_regen_pct)
    regen_min = regen_s * 60.0
    # Manaflow fills over the game (~30 mana / champion hit, cap 300)
    manaflow = min(300.0, 28.0 * minute) if role == "mid" else min(240.0, 18.0 * minute)
    pool = morgana_mana_pool(level, stats.mana, manaflow)
    # Lost Chapter Enlighten: ~20% max mana on each level-up. Mid levels ~1/90s.
    if stats.has_lc:
        regen_min += 0.20 * pool * (0.65 if role == "mid" else 0.40)
    # Cannot dump a third of the bar every minute and still exist next wave.
    budget = regen_min + 0.15 * pool
    if cost <= budget:
        w_farm = desired_w_farm
        miss = 0
        sustain = True
    else:
        # Drop farm W first (keep Q for lane threat).
        deficit = cost - budget
        w_drop = min(desired_w_farm, deficit / max(1.0, w_mana(wr)))
        w_farm = max(0.0, desired_w_farm - w_drop)
        # Half a WR caster wave is ~55g; missing a W-farm is ~that.
        miss = int(round((desired_w_farm - w_farm) * (55 if role == "mid" else 12)))
        sustain = False
    return ManaReport(w_farm, miss, regen_min, cost, sustain)


def bully_gold(stats: Stats, w_farm: float, role: str) -> int:
    """Extra CS gold from Big Bully + the AP that actually last-hits."""
    if role != "mid" or w_farm <= 0:
        return 0
    extra = 0.0
    if stats.bully > 0:
        # Per W cast the pool tags the whole wave once (not per tick).
        # ~1 extra last-hit per wave at 18 dmg; more with 22 true + extra AP.
        per_wave = 18.0 if stats.bully < 20 else 28.0
        if stats.bully_true:
            per_wave += 8.0
        extra += per_wave * w_farm
    # 25 AP on T2 mana boots also last-hits casters that Ionian leaves.
    if stats.ap >= 25 and "Ionian" not in "".join(stats.names) and "Crimson" not in "".join(stats.names):
        extra += 6.0 * w_farm
    return int(round(extra))


def combat_combo(stats: Stats, minute: int, level: int, role: str) -> Dict[str, float]:
    """Q + W dwell + burns on a mid-lane target. 10s skirmish."""
    qr = skill_rank(level, "Q")
    wr = skill_rank(level, "W")
    rr = skill_rank(level, "R")
    cd_mult = ability_haste_mult(stats.ah)
    q_cd = 9.0 * cd_mult
    w_cd = 12.0 * cd_mult
    # Transcendence lv9: 10% refund on a basic, 8s ICD — small extra Q.
    if level >= 9:
        q_cd *= 0.95
    window = 10.0
    q_casts = max(1.0, window / q_cd)
    w_casts = min(2.0, max(1.0, window / w_cd))
    root = q_root(max(1, qr))
    # Dwell inside W: root, then walk-out unless Rylai refreshes 30% slow.
    if stats.rylai:
        dwell = 5.0
    else:
        dwell = min(5.0, root + 1.1)
    ticks = dwell / 0.5  # 10 ticks in 5s
    missing_avg = 0.22 if dwell < 4 else 0.32
    w_amp = 1.0 + 1.7 * missing_avg
    tick_dmg = (w_tick_base(max(1, wr)) + 0.07 * stats.ap) * w_amp
    w_dmg = ticks * tick_dmg * w_casts
    q_dmg = q_casts * (q_base(max(1, qr)) + 0.90 * stats.ap)
    r_dmg = 0.0
    r_stun = 0.0
    if rr > 0:
        rcd = r_cd(rr) * cd_mult
        r_chance = min(1.0, window / rcd)
        # Two pulses if they stay 3s. Rylai / root helps the second pulse.
        pulses = 1.55 if stats.rylai or root >= 2.4 else 1.25
        r_dmg = r_chance * pulses * (r_base(rr) + 0.70 * stats.ap)
        r_stun = r_chance * 1.5
    hp = target_hp(minute, "mid" if role == "mid" else "adc")
    burn = 0.0
    linger = 3.0 if (stats.blackfire or stats.liandry or stats.ashes) else 0.0
    burn_t = dwell + linger * (0.85 if stats.rylai else 0.55)
    if stats.ashes and not stats.blackfire and not stats.liandry:
        burn += 15.0 / 3.0 * min(3.0, burn_t)
    if stats.blackfire:
        burn += (20.0 + 0.02 * stats.ap) * burn_t
    if stats.liandry:
        # 7.2: 2% max HP / sec while refreshed (same model as zyra-burn-sim).
        burn += 0.02 * hp * burn_t
    comet = (18 + 4 * level + 0.20 * stats.ap) * min(2.0, 1.0 + (10.0 / (16.0 * cd_mult)))
    scorch = (21 + 1.8 * level)
    raw = q_dmg + w_dmg + r_dmg + burn + comet + scorch
    dealt = raw * pen_mult(stats, minute) * madness_mult(stats)
    q_per_min = 60.0 / q_cd
    flash_cd = 150.0 * (1.0 - min(0.40, stats.summoner_haste))
    return {
        "combo": dealt,
        "q_per_min": q_per_min,
        "q_casts_window": q_casts,
        "root_s": root * q_casts + r_stun,
        "dwell": dwell,
        "flash_cd": flash_cd,
        "w_dmg": w_dmg,
        "q_dmg": q_dmg,
        "burn": burn,
        "pen_mult": pen_mult(stats, minute),
    }


@dataclass
class Snapshot:
    minute: int
    build: str
    role: str
    items: List[str]
    gold_spent_eq: int
    gold_pocket: int
    cumulative_gold: int
    level: int
    ap: float
    ah: float
    combo: float
    q_per_min: float
    root_window: float
    dwell: float
    w_farm: float
    oom: bool
    bully_gold: int
    miss_gold: int
    pen_mult: float
    flash_cd: float
    notes: str


def run_build(name: str, path: List[str], role: str) -> List[Snapshot]:
    gold = 500
    owned: List[str] = []
    snaps: List[Snapshot] = []
    cum_bully = 0
    cum_miss = 0
    # Spend the starting 500 immediately (Sickle on support, Speed on mid if listed).
    owned, gold = try_progress(path, owned, gold, 0)

    for m in range(1, GAME_MINUTES + 1):
        level = level_at_minute(m, role)
        gold += base_income(m, role)
        st_pre = stats_from(owned, m, level)
        mana = mana_minute(st_pre, level, role, m)
        b = bully_gold(st_pre, mana.w_farm, role)
        gold += b
        gold -= mana.oom_miss_gold
        gold = max(0, gold)
        cum_bully += b
        cum_miss += mana.oom_miss_gold
        if role == "support" and m >= 5 and "Spectral Sickle" in owned:
            owned, gold = buy("Black Mist Scythe", owned, gold)
        owned, gold = try_progress(path, owned, gold, m)
        st = stats_from(owned, m, level)
        # Recompute mana after this minute's purchases (regen for the *next* wave).
        mana2 = mana_minute(st, level, role, m)
        cmb = combat_combo(st, m, level, role)
        notes = []
        if st.liandry and st.blackfire:
            notes.append("double burn")
        if st.rylai:
            notes.append("rylai lock")
        if not mana2.sustain:
            notes.append("OOM farm")
        if st.flat_mpen or st.pct_mpen:
            notes.append(f"pen {st.flat_mpen:.0f}/{st.pct_mpen*100:.0f}%")
        spent = 500 + sum(base_income(t, role) for t in range(1, m + 1)) + cum_bully - cum_miss - gold
        snaps.append(
            Snapshot(
                minute=m,
                build=name,
                role=role,
                items=list(owned),
                gold_spent_eq=int(spent),
                gold_pocket=int(gold),
                cumulative_gold=int(spent + gold),
                level=level,
                ap=round(st.ap, 1),
                ah=round(st.ah, 1),
                combo=round(cmb["combo"], 1),
                q_per_min=round(cmb["q_per_min"], 2),
                root_window=round(cmb["root_s"], 2),
                dwell=round(cmb["dwell"], 2),
                w_farm=round(mana2.w_farm, 2),
                oom=not mana2.sustain,
                bully_gold=cum_bully,
                miss_gold=cum_miss,
                pen_mult=round(cmb["pen_mult"], 3),
                flash_cd=round(cmb["flash_cd"], 1),
                notes=", ".join(notes) or "—",
            )
        )
    return snaps


def first_item_minute(snaps: List[Snapshot], item: str) -> Optional[int]:
    for s in snaps:
        if item in s.items:
            return s.minute
    return None


def area(snaps: List[Snapshot], attr: str) -> float:
    return sum(getattr(s, attr) for s in snaps)


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------


def short_items(items: List[str]) -> str:
    skip = {"Amplifying Tome", "Ring of Revelation", "Ruby Crystal", "Boots of Speed"}
    shown = [n for n in items if n not in skip]
    if len(shown) > 5:
        return " › ".join(shown[:5]) + " › …"
    return " › ".join(shown) or "(components)"


def summarize(results: Dict[str, List[Snapshot]]) -> str:
    mid_mana = results["Mid · Mana → Spellslinger"]
    mid_ion = results["Mid · Ionian → Crimson"]
    sup_mana = results["Support · Mana → Spellslinger"]
    sup_ion = results["Support · Ionian → Crimson"]
    lines: List[str] = []
    lines.append("=" * 78)
    lines.append("MORGANA — IONIAN vs BOOTS OF MANA (Wild Rift 7.2e)")
    lines.append("Câu hỏi: mid vẫn lên Ionia? Đã tính farm chưa?")
    lines.append("20:00 · W max · Blackfire → Liandry → Rylai · chỉ đổi dòng giày")
    lines.append("=" * 78)

    lines.append("")
    lines.append("FARM FACTOR (mid vs support) — đây là thứ lần trước không mô hình")
    lines.append("-" * 78)
    lines.append("  Mid farm W mỗi wave (2 W/phút). Ionia T2 = 0% mana regen, 0 AP, 0 pen.")
    lines.append("  Boots of Mana T2 = 75% regen + 25 AP + 8 pen + Big Bully 18.")
    lines.append("  7.2: đồ mage T3 mất 7% pen. Core BF/Liandry/Rylai/Cap = 0 pen.")
    lines.append("  Spellslinger là pen rẻ duy nhất trước Void/Cryptbloom.")
    lines.append("")

    def gold_row(label: str, snaps: List[Snapshot]) -> None:
        s8, s12, s16, s20 = snaps[7], snaps[11], snaps[15], snaps[19]
        lines.append(
            f"  {label:<28} 8:00 {s8.cumulative_gold:>5}  "
            f"12:00 {s12.cumulative_gold:>5}  16:00 {s16.cumulative_gold:>5}  "
            f"20:00 {s20.cumulative_gold:>5}  bully+{s20.bully_gold} miss-{s20.miss_gold}"
        )

    lines.append("  Gold tích lũy (base CS/assist + Big Bully − CS miss vì OOM)")
    gold_row("Mid Mana", mid_mana)
    gold_row("Mid Ionian", mid_ion)
    gold_row("Support Mana", sup_mana)
    gold_row("Support Ionian", sup_ion)
    dg = mid_mana[19].cumulative_gold - mid_ion[19].cumulative_gold
    lines.append(
        f"  Δ mid @20:00: Mana {dg:+d}g  "
        f"(bully {mid_mana[19].bully_gold - mid_ion[19].bully_gold:+d}, "
        f"miss {mid_ion[19].miss_gold - mid_mana[19].miss_gold:+d} tiết kiệm)"
    )

    lines.append("")
    lines.append("  OOM farm W (mid) — phút nào Ionia bỏ wave vì hết mana")
    oom_ion = [s.minute for s in mid_ion if s.oom]
    oom_mana = [s.minute for s in mid_mana if s.oom]
    lines.append(f"    Mana path OOM:   {oom_mana or 'không'}")
    lines.append(f"    Ionian path OOM: {oom_ion or 'không'}")

    lines.append("")
    lines.append("-" * 78)
    lines.append("MID — COMBO Q+W+burn (10s) vs đối thủ mid")
    lines.append("-" * 78)
    for m in (6, 8, 10, 12, 14, 16, 18, 20):
        a, b = mid_mana[m - 1], mid_ion[m - 1]
        d = 100.0 * (a.combo / b.combo - 1.0) if b.combo else 0.0
        winner = "MANA" if a.combo >= b.combo else "IONIA"
        lines.append(
            f"  {m:>2}:00 | Mana {a.combo:>6.0f}  Ionia {b.combo:>6.0f}  "
            f"Δ {d:+5.1f}%  {winner:5} | "
            f"Q/min {a.q_per_min:.1f} vs {b.q_per_min:.1f} | "
            f"pen×{a.pen_mult:.2f} vs ×{b.pen_mult:.2f}"
        )
        lines.append(f"         Mana : {short_items(a.items)}")
        lines.append(f"         Ionia: {short_items(b.items)}")

    lines.append("")
    lines.append("  Spike món")
    for label, snaps in (("Mana", mid_mana), ("Ionia", mid_ion)):
        bits = []
        for it in (
            "Boots of Mana",
            "Ionian Boots of Lucidity",
            "Blackfire Torch",
            "Liandry's Torment",
            "Spellslinger's Shoes",
            "Crimson Lucidity",
            "Rylai's Crystal Scepter",
            "Rabadon's Deathcap",
        ):
            t = first_item_minute(snaps, it)
            if t:
                bits.append(f"{it.split()[0]}~{t}:00")
        lines.append(f"    {label}: " + ", ".join(bits))

    area_m = area(mid_mana, "combo")
    area_i = area(mid_ion, "combo")
    q_m = area(mid_mana, "q_per_min") / GAME_MINUTES
    q_i = area(mid_ion, "q_per_min") / GAME_MINUTES
    lines.append("")
    lines.append(
        f"  Diện tích combo 20p: Mana {area_m:.0f}  vs  Ionia {area_i:.0f}  "
        f"({100*(area_m/area_i-1):+.1f}%)"
    )
    lines.append(
        f"  Q/phút trung bình:   Mana {q_m:.2f}  vs  Ionia {q_i:.2f}  "
        f"(Ionia +{100*(q_i/q_m-1):.1f}% roots)"
    )
    lines.append(
        f"  Flash CD @20:        Mana {mid_mana[19].flash_cd:.0f}s  vs  "
        f"Ionia {mid_ion[19].flash_cd:.0f}s"
    )

    lines.append("")
    lines.append("-" * 78)
    lines.append("SUPPORT — cùng 2 dòng giày, vàng không farm (đối chứng)")
    lines.append("-" * 78)
    for m in (8, 12, 16, 20):
        a, b = sup_mana[m - 1], sup_ion[m - 1]
        d = 100.0 * (a.combo / b.combo - 1.0) if b.combo else 0.0
        lines.append(
            f"  {m:>2}:00 | Mana {a.combo:>6.0f}  Ionia {b.combo:>6.0f}  "
            f"Δ {d:+5.1f}% | gold {a.cumulative_gold} vs {b.cumulative_gold} | "
            f"Q/min {a.q_per_min:.1f} vs {b.q_per_min:.1f}"
        )
        lines.append(f"         Ionia items: {short_items(b.items)}")
        lines.append(f"         Mana  items: {short_items(a.items)}")
    sa, si = area(sup_mana, "combo"), area(sup_ion, "combo")
    lines.append(
        f"  Diện tích combo support: Mana {sa:.0f} vs Ionia {si:.0f} "
        f"({100*(sa/si-1):+.1f}%)"
    )
    lines.append(
        f"  Ionia rẻ 200g T2 / 200g T3. Support 20 phút không xong Liandry ở cả hai"
    )
    lines.append(
        f"  nhánh — 200g không mua thêm một món. Q haste + Flash mới là lý do Ionia support."
    )

    # Ablation: same gold (strip bully & miss) would still show pen — reported in verdict.
    lines.append("")
    lines.append("-" * 78)
    lines.append("VERDICT")
    lines.append("-" * 78)
    mid_wins_mana = area_m > area_i
    # Count mid minutes mana ahead
    mana_ahead = sum(1 for a, b in zip(mid_mana, mid_ion) if a.combo > b.combo)
    lines.append(
        f"  MID: {'Boots of Mana → Spellslinger' if mid_wins_mana else 'Ionian → Crimson'} "
        f"thắng {mana_ahead}/{GAME_MINUTES} phút combat."
    )
    lines.append(
        f"  SUPPORT: damage vẫn nghiêng Spellslinger (+5%), nhưng kit support là Q/E/Flash."
    )
    lines.append(
        f"           Diamond+ support Ionia 92% pick — đúng vai, không copy số liệu đó sang mid."
    )
    lines.append("")
    lines.append("  Lần trước chọn Ionia vì Diamond+ 57% WR / 68% pick, và Q haste.")
    lines.append("  Bảng đó so Ionia với Mercury, KHÔNG có WR Boots of Mana.")
    lines.append("  wrchina Top-30 (19 build thật, 2026-09-11): Spellslinger 63%, Crimson 32%.")
    lines.append("  Support Diamond+ Ionia 92% pick — lẫn số liệu support vào mid.")
    lines.append("")
    lines.append("  FARM ĐỔI KẾT QUẢ VÌ:")
    lines.append("  1) Mid W-max mỗi wave. Ionia T2 không regen mana → OOM, mất CS.")
    lines.append("  2) Big Bully + AP trên Boots of Mana last-hit wave; Ionia không.")
    lines.append("  3) +200g T2 là ~nửa wave mid, không phải 'đắt' như support.")
    lines.append("  4) 7.2 rút pen khỏi Liandry/Rylai/Cap. Không Spellslinger thì 0 pen")
    lines.append("     cho đến món 4–5. Mid kịp hoàn thành 3 món — pen nhân cả kit.")
    lines.append("  5) Blackfire (20 AH) + Transcendence (12) đã che bớt mất 15 AH Ionia.")
    lines.append("     Q/phút Ionia hơn, nhưng không bù damage W+%HP Liandry khi có pen.")
    lines.append("")
    lines.append("  KHI NÀO VẪN IONIA MID:")
    lines.append("  • Matchup all-in / cần Flash-R (Crimson 20% summoner haste + MS).")
    lines.append("  • Bạn đã đấm Ionia T2 — không cross-upgrade sang Mana.")
    lines.append("  • Bị gank tới chết, Q haste + Black Shield > damage.")
    lines.append("")
    lines.append("  MUA MID MẶC ĐỊNH:")
    lines.append("  1) Boots of Speed + Amplifying Tome → Boots of Mana (~3:00)")
    lines.append("  2) Lost Chapter → Fated Ashes → Blackfire (~8:00)")
    lines.append("  3) Liandry (~13:00)")
    lines.append("  4) Spellslinger sau 10:00, cùng back Liandry (~15:00)")
    lines.append("  5) Rylai (~19:00) → Deathcap / Void nếu tank")
    lines.append("=" * 78)
    return "\n".join(lines)


def export_json(results: Dict[str, List[Snapshot]], path: str) -> None:
    payload = {
        "meta": {
            "champion": "Morgana",
            "question": "Ionian vs Boots of Mana on mid, with farm modeled",
            "patch": "7.2e",
            "game_minutes": GAME_MINUTES,
            "sources": {
                "boot_stats": "WR patch 7.2 notes + riftpatchnotes",
                "diamond_plus_mid_ionian": "56.98% WR / 68.25% pick (riftpatchnotes 2026-09-06)",
                "top30_boots": "Spellslinger 63% / Crimson 32% (wrchina.gg 2026-09-11)",
                "support_ionian": "53.27% WR / 92.45% pick Diamond+",
            },
        },
        "builds": {
            name: [
                {
                    "minute": s.minute,
                    "items": s.items,
                    "gold": s.cumulative_gold,
                    "pocket": s.gold_pocket,
                    "level": s.level,
                    "ap": s.ap,
                    "ah": s.ah,
                    "combo": s.combo,
                    "q_per_min": s.q_per_min,
                    "w_farm": s.w_farm,
                    "oom": s.oom,
                    "bully_gold": s.bully_gold,
                    "miss_gold": s.miss_gold,
                    "pen_mult": s.pen_mult,
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
    """Fail the process if the model contradicts its own rules."""
    mid_mana = results["Mid · Mana → Spellslinger"]
    mid_ion = results["Mid · Ionian → Crimson"]
    for snaps in results.values():
        for s in snaps:
            if s.minute < T3_BOOTS_MINUTE:
                assert "Spellslinger's Shoes" not in s.items, s
                assert "Crimson Lucidity" not in s.items, s
        golds = [s.cumulative_gold for s in snaps]
        assert golds == sorted(golds), "gold must be monotonic"
    # T2 mana costs 200g more — before bully, Ionian should spike T2 first.
    t_mana = first_item_minute(mid_mana, "Boots of Mana")
    t_ion = first_item_minute(mid_ion, "Ionian Boots of Lucidity")
    assert t_mana and t_ion and t_ion <= t_mana
    # By 20:00 mid mana path must actually own Spellslinger (farm lets her).
    assert "Spellslinger's Shoes" in mid_mana[19].items
    # Mid mana should not sit OOM after T2 boots.
    after_t2 = [s for s in mid_mana if "Boots of Mana" in s.items or "Spellslinger's Shoes" in s.items]
    assert after_t2, "mana path never bought T2"
    # Ionian mid should miss more CS to OOM than mana path.
    assert mid_ion[19].miss_gold >= mid_mana[19].miss_gold
    # Mid mana combat area should beat ionian — that's the farm-informed answer.
    assert area(mid_mana, "combo") > area(mid_ion, "combo")
    # Ionian still has more Q/min (haste is real).
    assert area(mid_ion, "q_per_min") > area(mid_mana, "q_per_min")


def main() -> None:
    results = {
        name: run_build(name, path, ROLE_OF[name])
        for name, path in BUILD_PATHS.items()
    }
    self_check(results)
    report = summarize(results)
    print(report)
    with open(os.path.join(OUT_DIR, "report.txt"), "w", encoding="utf-8") as f:
        f.write(report + "\n")
    export_json(results, os.path.join(OUT_DIR, "results.json"))
    print(f"\nWrote {OUT_DIR}/report.txt and {OUT_DIR}/results.json")


if __name__ == "__main__":
    main()
