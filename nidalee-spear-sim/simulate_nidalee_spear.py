#!/usr/bin/env python3
"""
PC League of Legends — Nidalee jungle
Patch snapshot ~26.18 (Sep 2026 item / kit values).

Question:
  Is spear-only Q spam worth playing on Nidalee?

Playstyles (champion combat — both still cougar-clear jungle):
  SO  spear-only: stay human, Q on cooldown (70% mid-range / 30% max), never convert.
  CV  convert:    throw a Hunt spear, then cougar Pounce → Swipe → Takedown.

Metric: expected magic damage in a 12s skirmish/siege window, plus
squishy kill threat (post-mitigation / target HP). Convert vs tanks is
discounted because committing melee onto a healthy tank is often wrong.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import json

GAME_MINUTES = 28
WINDOW = 12.0

# Spear travel amp is 0–225% of minimum damage (wiki). Practical, not
# theoretical-max: a "max" spear is long, not always the last pixel.
AMP_MAX = 2.00  # × min ≈ 3.00×  (wiki max is 3.25×)
AMP_MID = 1.00  # × min ≈ 2.00×
AMP_SHORT = 0.40  # × min ≈ 1.40×  (Hunt-range setup spear)

# Hit rates: max-range spears are the fantasy, Hunt-range spears are the job.
HIT_MAX_SQUISH = 0.32
HIT_MAX_TANK = 0.50
HIT_MID_SQUISH = 0.55
HIT_MID_TANK = 0.72
HIT_SHORT_SQUISH = 0.68
HIT_SHORT_TANK = 0.84

# Melee convert onto a healthy tank is often declined / interrupted.
TANK_CONVERT_COMMIT = 0.55
COUGAR_COMBO_LAND = 0.95

# Horizon Focus Hypershot: ability damage from ≥600 range, then +10% for 6s.
HORIZON_AMP = 0.10


# ---------------------------------------------------------------------------
# Economy / XP (average Nidalee jungle, not smurf-fed)
# ---------------------------------------------------------------------------


def gold_at_minute(m: int) -> int:
    if m <= 0:
        return 500
    total = 500  # starting + pet
    for t in range(1, m + 1):
        if t <= 5:
            total += 280
        elif t <= 11:
            total += 370
        elif t <= 18:
            total += 460
        elif t <= 24:
            total += 520
        else:
            total += 560
    return total


def level_at_minute(m: int) -> int:
    table = {
        1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 6, 7: 7, 8: 8,
        9: 8, 10: 9, 11: 10, 12: 11, 13: 11, 14: 12,
        15: 12, 16: 13, 17: 13, 18: 14, 19: 14, 20: 15,
        21: 15, 22: 16, 23: 16, 24: 16, 25: 17, 26: 17,
        27: 18, 28: 18,
    }
    return table.get(m, min(18, 1 + m))


def skill_rank(level: int, skill: str) -> int:
    """Q max, E second, W last. Cougar R starts ranked and ups at 6/11/16."""
    if skill == "R":
        rank = 1
        if level >= 6:
            rank += 1
        if level >= 11:
            rank += 1
        if level >= 16:
            rank += 1
        return rank
    q_levels = [1, 3, 5, 7, 9]
    e_levels = [4, 8, 10, 12, 13]
    w_levels = [2, 14, 15, 17, 18]
    mapping = {"Q": q_levels, "W": w_levels, "E": e_levels}
    return sum(1 for lv in mapping[skill] if level >= lv)


def nid_base_ad(level: int) -> float:
    return 58.0 + 3.5 * (level - 1)


# ---------------------------------------------------------------------------
# Targets
# ---------------------------------------------------------------------------


def squishy_hp(m: int) -> float:
    lv = level_at_minute(m)
    return 640 + 104 * lv + 18 * m


def squishy_mr(m: int) -> float:
    lv = level_at_minute(m)
    extra = 0.0 if m < 14 else (12.0 if m < 22 else 25.0)
    return 30 + 1.3 * lv + extra


def tank_hp(m: int) -> float:
    lv = level_at_minute(m)
    item_hp = 80 * max(0, m - 6)
    return 700 + 110 * lv + item_hp


def tank_mr(m: int) -> float:
    lv = level_at_minute(m)
    extra = 0.0 if m < 8 else min(8.5 * (m - 8), 155.0)
    return 32 + 2.05 * lv + extra


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
    flat_mpen: float = 0
    pct_mpen: float = 0
    deathcap: bool = False
    lich: bool = False
    sheen: bool = False
    belt: bool = False
    horizon: bool = False
    storm: bool = False
    luden: bool = False
    blackfire: bool = False
    liandry: bool = False
    ashes: bool = False
    guise: bool = False
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
    "Sheen": Item("Sheen", 900, sheen=True),
    "Aether Wisp": Item("Aether Wisp", 900, ap=30),
    "Ruby Crystal": Item("Ruby Crystal", 400, hp=150),
    "Boots": Item("Boots", 300, tags=("boots",)),
    "Sorcerer's Shoes": Item(
        "Sorcerer's Shoes", 1100, flat_mpen=12, tags=("boots",)
    ),
    "Lich Bane": Item(
        "Lich Bane", 2900, ap=100, ah=10, lich=True, tags=("spellblade",)
    ),
    "Hextech Rocketbelt": Item(
        "Hextech Rocketbelt",
        2650,
        ap=70,
        ah=20,
        hp=300,
        belt=True,
        tags=("engage",),
    ),
    "Horizon Focus": Item(
        "Horizon Focus", 2700, ap=75, ah=25, horizon=True, tags=("poke",)
    ),
    "Stormsurge": Item(
        "Stormsurge", 2800, ap=90, flat_mpen=15, storm=True, tags=("burst",)
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
    "Shadowflame": Item(
        "Shadowflame", 3200, ap=110, flat_mpen=15, tags=("squishy",)
    ),
    "Rabadon's Deathcap": Item(
        "Rabadon's Deathcap", 3500, ap=130, deathcap=True, tags=("amp",)
    ),
}


UPGRADE_COMPONENTS = {
    "Sorcerer's Shoes": ("Boots",),
    "Lich Bane": ("Sheen", "Aether Wisp", "Blasting Wand"),
    "Hextech Rocketbelt": ("Hextech Alternator", "Fiendish Codex", "Ruby Crystal"),
    "Horizon Focus": ("Fiendish Codex", "Fiendish Codex", "Amplifying Tome"),
    "Stormsurge": ("Hextech Alternator", "Aether Wisp"),
    "Luden's Echo": ("Lost Chapter", "Hextech Alternator"),
    "Blackfire Torch": ("Lost Chapter", "Fated Ashes"),
    "Liandry's Torment": ("Haunting Guise", "Fated Ashes"),
    "Void Staff": ("Blighting Jewel", "Blasting Wand"),
    "Shadowflame": ("Hextech Alternator", "Needlessly Large Rod"),
    "Rabadon's Deathcap": ("Needlessly Large Rod", "Needlessly Large Rod"),
}

NEXT_COMPONENTS = {
    "Sorcerer's Shoes": ["Boots"],
    "Lich Bane": ["Sheen", "Aether Wisp", "Blasting Wand"],
    "Hextech Rocketbelt": ["Hextech Alternator", "Ruby Crystal", "Fiendish Codex"],
    "Horizon Focus": ["Fiendish Codex", "Amplifying Tome"],
    "Stormsurge": ["Hextech Alternator", "Aether Wisp"],
    "Luden's Echo": ["Lost Chapter", "Hextech Alternator"],
    "Blackfire Torch": ["Fated Ashes", "Lost Chapter"],
    "Liandry's Torment": ["Fated Ashes", "Haunting Guise"],
    "Void Staff": ["Blighting Jewel", "Blasting Wand"],
    "Shadowflame": ["Hextech Alternator", "Needlessly Large Rod"],
    "Rabadon's Deathcap": ["Needlessly Large Rod"],
}


# Prefix SO = spear-only combat, CV = convert combat. Same jungle gold.
BUILD_PATHS: Dict[str, List[str]] = {
    # Spear-only: haste + burn + long-range amp. Lich Bane does nothing.
    "SO Liandry → Horizon → Void": [
        "Fated Ashes",
        "Haunting Guise",
        "Liandry's Torment",
        "Boots",
        "Sorcerer's Shoes",
        "Fiendish Codex",
        "Horizon Focus",
        "Blighting Jewel",
        "Void Staff",
        "Rabadon's Deathcap",
    ],
    "SO Horizon → Liandry → Void": [
        "Fiendish Codex",
        "Fiendish Codex",
        "Amplifying Tome",
        "Horizon Focus",
        "Boots",
        "Sorcerer's Shoes",
        "Fated Ashes",
        "Haunting Guise",
        "Liandry's Torment",
        "Void Staff",
        "Rabadon's Deathcap",
    ],
    "SO Luden → Horizon → Void": [
        "Lost Chapter",
        "Hextech Alternator",
        "Luden's Echo",
        "Boots",
        "Sorcerer's Shoes",
        "Fiendish Codex",
        "Horizon Focus",
        "Void Staff",
        "Rabadon's Deathcap",
    ],
    "SO Stormsurge → SF → Cap": [
        "Hextech Alternator",
        "Aether Wisp",
        "Stormsurge",
        "Boots",
        "Sorcerer's Shoes",
        "Shadowflame",
        "Rabadon's Deathcap",
        "Void Staff",
    ],
    "SO Luden → SF → Cap": [
        "Lost Chapter",
        "Hextech Alternator",
        "Luden's Echo",
        "Boots",
        "Sorcerer's Shoes",
        "Shadowflame",
        "Rabadon's Deathcap",
        "Void Staff",
    ],
    # Same items as the meta convert path — shows Lich Bane is wasted.
    "SO Lich → Belt → SF": [
        "Sheen",
        "Aether Wisp",
        "Blasting Wand",
        "Lich Bane",
        "Boots",
        "Sorcerer's Shoes",
        "Hextech Alternator",
        "Hextech Rocketbelt",
        "Shadowflame",
        "Rabadon's Deathcap",
    ],
    # Convert: Lich Bane spellblade lives on Takedown.
    "CV Lich → Belt → SF": [
        "Sheen",
        "Aether Wisp",
        "Blasting Wand",
        "Lich Bane",
        "Boots",
        "Sorcerer's Shoes",
        "Hextech Alternator",
        "Hextech Rocketbelt",
        "Shadowflame",
        "Rabadon's Deathcap",
    ],
    "CV Lich → Belt → Void": [
        "Sheen",
        "Aether Wisp",
        "Blasting Wand",
        "Lich Bane",
        "Boots",
        "Sorcerer's Shoes",
        "Hextech Alternator",
        "Hextech Rocketbelt",
        "Void Staff",
        "Rabadon's Deathcap",
    ],
    "CV Lich → Liandry → Void": [
        "Sheen",
        "Aether Wisp",
        "Blasting Wand",
        "Lich Bane",
        "Boots",
        "Sorcerer's Shoes",
        "Fated Ashes",
        "Haunting Guise",
        "Liandry's Torment",
        "Void Staff",
    ],
    "CV Liandry → Lich → Horizon": [
        "Fated Ashes",
        "Haunting Guise",
        "Liandry's Torment",
        "Boots",
        "Sorcerer's Shoes",
        "Sheen",
        "Lich Bane",
        "Horizon Focus",
        "Void Staff",
    ],
    # Same poke items, but you convert when the spear lands.
    "CV Liandry → Horizon → Void": [
        "Fated Ashes",
        "Haunting Guise",
        "Liandry's Torment",
        "Boots",
        "Sorcerer's Shoes",
        "Fiendish Codex",
        "Horizon Focus",
        "Blighting Jewel",
        "Void Staff",
        "Rabadon's Deathcap",
    ],
    "CV Horizon → Liandry → Void": [
        "Fiendish Codex",
        "Fiendish Codex",
        "Amplifying Tome",
        "Horizon Focus",
        "Boots",
        "Sorcerer's Shoes",
        "Fated Ashes",
        "Haunting Guise",
        "Liandry's Torment",
        "Void Staff",
        "Rabadon's Deathcap",
    ],
}

LEGENDARIES = {
    "Lich Bane",
    "Hextech Rocketbelt",
    "Horizon Focus",
    "Stormsurge",
    "Luden's Echo",
    "Blackfire Torch",
    "Liandry's Torment",
    "Void Staff",
    "Shadowflame",
    "Rabadon's Deathcap",
}


def playstyle_of(name: str) -> str:
    return "spear" if name.startswith("SO ") else "convert"


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
        if item_name == "Sorcerer's Shoes" and "Sorcerer's Shoes" in owned:
            return False
        if item_name == "Fiendish Codex":
            pass
        elif item_name != "Sorcerer's Shoes" and item_name != "Needlessly Large Rod":
            if item_name in owned:
                return False
        elif item_name == "Needlessly Large Rod" and owned.count(item_name) >= 2:
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
        if step in owned and step not in ("Needlessly Large Rod", "Fiendish Codex"):
            if owned.count(step) >= path.count(step):
                continue
        if can_afford(step):
            buy(step)
        else:
            blocked_at = step
            break

    if blocked_at and blocked_at in NEXT_COMPONENTS:
        for comp in NEXT_COMPONENTS[blocked_at]:
            if comp in owned and comp not in ("Needlessly Large Rod", "Fiendish Codex"):
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
                            if comp not in owned or comp in (
                                "Needlessly Large Rod",
                                "Fiendish Codex",
                            ):
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


def haste_cdr_mult(haste: float) -> float:
    return 100.0 / (100.0 + max(0.0, haste))


def apply_pen(mr: float, pct_mpen: float, flat_mpen: float) -> float:
    reduced = mr * (1.0 - pct_mpen) - flat_mpen
    return max(0.0, reduced)


def magic_mult(eff_mr: float) -> float:
    return 100.0 / (100.0 + eff_mr)


def sum_stats(inv: List[Item], playstyle: str) -> dict:
    ap = ah = mana = flat = pct = 0.0
    flags = {
        "lich": False,
        "sheen": False,
        "belt": False,
        "horizon": False,
        "storm": False,
        "luden": False,
        "bf": False,
        "liandry": False,
        "ashes": False,
        "guise": False,
        "cap": False,
        "sf": False,
        "void": False,
    }
    names = []
    for it in inv:
        names.append(it.name)
        ap += it.ap
        ah += it.ah
        mana += it.mana
        flat += it.flat_mpen
        pct += it.pct_mpen
        if it.lich:
            flags["lich"] = True
        if it.sheen:
            flags["sheen"] = True
        if it.belt:
            flags["belt"] = True
        if it.horizon:
            flags["horizon"] = True
        if it.storm:
            flags["storm"] = True
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
        if it.name == "Shadowflame":
            flags["sf"] = True
        if it.name == "Void Staff":
            flags["void"] = True

    # Adaptive shards: spear-only takes AP/AP; convert takes AP + AS.
    ap += 18.0 if playstyle == "spear" else 9.0
    # Transcendence
    ah += 10.0
    ap_mult = 1.0
    if flags["bf"]:
        ap_mult += 0.04
    if flags["cap"]:
        ap_mult += 0.30
    ap *= ap_mult
    return {"ap": ap, "ah": ah, "mana": mana, "flat": flat, "pct": pct, "names": names, **flags}


def q_cd(ah: float) -> float:
    return 6.0 * haste_cdr_mult(ah)


def spear_throws(ah: float, window: float) -> int:
    cd = q_cd(ah)
    # 0.25s cast + 0.15s recovery; first spear at t=0.
    n = 1 + int(max(0.0, window - 0.4) / max(0.5, cd))
    return min(n, 5)


def javelin_min(level: int, ap: float) -> float:
    rank = skill_rank(level, "Q")
    if rank <= 0:
        return 0.0
    base = [0, 70, 90, 110, 130, 150][rank]
    return base + 0.50 * ap


def javelin_damage(level: int, ap: float, amp: float) -> float:
    return javelin_min(level, ap) * (1.0 + amp)


def pounce_damage(level: int, ap: float) -> float:
    rank = skill_rank(level, "R")
    base = [0, 55, 100, 145, 190][rank]
    return base + 0.30 * ap


def swipe_damage(level: int, ap: float) -> float:
    rank = skill_rank(level, "R")
    base = [0, 70, 130, 190, 250][rank]
    return base + 0.55 * ap


def takedown_damage(
    level: int, ap: float, total_ad: float, missing_pct: float, hunted: bool
) -> float:
    rank = skill_rank(level, "R")
    base = [0, 5, 30, 55, 80][rank]
    ad_r = 0.75
    ap_r = 0.40
    per = [0, 0.01, 0.0125, 0.015, 0.0175][rank]
    missing_pct = max(0.0, min(0.99, missing_pct))
    raw = (base + ad_r * total_ad + ap_r * ap) * (1.0 + per * missing_pct * 100.0)
    if hunted:
        raw *= 1.30
    return raw


def spellblade(level: int, ap: float, stats: dict) -> float:
    base_ad = nid_base_ad(level)
    if stats["lich"]:
        return 0.75 * base_ad + 0.45 * ap
    if stats["sheen"]:
        return 1.00 * base_ad
    return 0.0


def comet_raw(level: int, ap: float, amp: float) -> float:
    # 15–100 + 5% AP, then 0–100% from travel distance (V26.09).
    base = 15.0 + (100.0 - 15.0) * (level - 1) / 17.0
    return (base + 0.05 * ap) * (1.0 + min(1.0, amp / 2.25))


def comet_cd(level: int) -> float:
    return 20.0 + (6.59 - 20.0) * (level - 1) / 17.0


def dh_raw(level: int, ap: float, minute: int) -> float:
    souls = max(0, (minute - 7) // 3)
    return 30.0 + 11.0 * souls + 0.05 * ap


def scorch_raw(level: int) -> float:
    return 20.0 + 20.0 * (level - 1) / 17.0


def suffer_mult(stats: dict, burn_s: float) -> float:
    if stats["liandry"] or stats["guise"]:
        # Madness ramps; poke windows sit around 4–8%.
        return 1.04 + 0.02 * min(1.0, burn_s / 8.0)
    return 1.0


@dataclass
class Snapshot:
    minute: int
    build_name: str
    playstyle: str
    items: List[str]
    gold: int
    level: int
    ap: float
    ah: float
    legendary_count: int
    spears_thrown: int
    exp_tank: float
    exp_squish: float
    kill_tank: float
    kill_squish: float
    landed_spear: float
    landed_combo: float
    notes: str
    has_lich: bool
    has_liandry: bool
    has_horizon: bool
    has_void: bool
    has_belt: bool
    has_sf: bool


def hit_rate(amp: float, vs_tank: bool) -> float:
    if amp >= 1.7:
        return HIT_MAX_TANK if vs_tank else HIT_MAX_SQUISH
    if amp >= 0.8:
        return HIT_MID_TANK if vs_tank else HIT_MID_SQUISH
    return HIT_SHORT_TANK if vs_tank else HIT_SHORT_SQUISH


def apply_magic(
    raw: float,
    mr: float,
    stats: dict,
    extra_flat: float = 0.0,
    cinder: float = 1.0,
    horizon: bool = False,
    suffer: float = 1.0,
) -> float:
    eff = apply_pen(mr, stats["pct"], stats["flat"] + extra_flat)
    amp = HORIZON_AMP if horizon else 0.0
    return raw * magic_mult(eff) * (1.0 + amp) * cinder * suffer


def combo_landed(
    *,
    level: int,
    minute: int,
    stats: dict,
    hp: float,
    mr: float,
    spear_amp: float,
    vs_tank: bool,
) -> float:
    """100% hit convert: Hunt spear + cougar combo. Returns post-mit dmg."""
    ap = stats["ap"]
    ad = nid_base_ad(level)
    # Sudden Impact (7 mpen) after Pounce / Rocketbelt — not on the setup spear.
    dash_flat = 7.0
    horizon_on_combo = stats["horizon"]  # spear from ≥600 marks for 6s
    suffer = suffer_mult(stats, 3.5)
    dmg = 0.0
    hp_left = hp

    def hit(raw: float, horizon=False, cinder=1.0, extra=0.0) -> float:
        return apply_magic(
            raw, mr, stats, extra_flat=extra, cinder=cinder,
            horizon=horizon, suffer=suffer,
        )

    spear = hit(javelin_damage(level, ap, spear_amp), horizon=False, extra=0.0)
    dmg += spear
    hp_left = max(1.0, hp_left - spear)

    if stats["luden"]:
        echo = hit(105.0 + 0.07 * ap, horizon=horizon_on_combo)
        dmg += echo
        hp_left = max(1.0, hp_left - echo)

    comet = hit(comet_raw(level, ap, spear_amp), horizon=horizon_on_combo)
    # Convert page is Dark Harvest, not Comet. DH waits until <50% HP.
    # Model: convert runs DH; ignore comet here.
    _ = comet

    if stats["belt"]:
        belt = hit(100.0 + 0.10 * ap, horizon=horizon_on_combo, extra=dash_flat)
        dmg += belt
        hp_left = max(1.0, hp_left - belt)

    pounce = hit(pounce_damage(level, ap), horizon=horizon_on_combo, extra=dash_flat)
    dmg += pounce
    hp_left = max(1.0, hp_left - pounce)

    swipe = hit(swipe_damage(level, ap), horizon=horizon_on_combo, extra=dash_flat)
    dmg += swipe
    hp_left = max(1.0, hp_left - swipe)

    missing = 1.0 - (hp_left / hp)
    cinder = 1.20 if (stats["sf"] and hp_left / hp <= 0.40) else 1.0
    td = hit(
        takedown_damage(level, ap, ad, missing, hunted=True),
        horizon=horizon_on_combo,
        cinder=cinder,
        extra=dash_flat,
    )
    blade = hit(spellblade(level, ap, stats), horizon=horizon_on_combo, extra=dash_flat)
    dmg += td + blade
    hp_left = max(1.0, hp_left - td - blade)

    # DH once they are below 50% (typical after spear+pounce on a squishy).
    if hp_left / hp <= 0.50:
        dh_cinder = 1.20 if (stats["sf"] and hp_left / hp <= 0.40) else 1.0
        dh = hit(
            dh_raw(level, ap, minute),
            horizon=horizon_on_combo,
            cinder=dh_cinder,
            extra=dash_flat,
        )
        dmg += dh
        hp_left = max(1.0, hp_left - dh)

    if stats["storm"]:
        dealt = hp - hp_left
        if dealt >= 0.25 * hp:
            squall = hit(140.0 + 0.20 * ap, horizon=horizon_on_combo, extra=dash_flat)
            dmg += squall
            hp_left = max(1.0, hp_left - squall)

    burn_t = 3.0
    if stats["liandry"]:
        dmg += 0.02 * hp * burn_t * magic_mult(apply_pen(mr, stats["pct"], stats["flat"] + dash_flat)) * suffer * (1.0 + (HORIZON_AMP if horizon_on_combo else 0.0))
    elif stats["ashes"] and not stats["bf"]:
        dmg += 5.0 * burn_t * magic_mult(apply_pen(mr, stats["pct"], stats["flat"])) * suffer
    if stats["bf"]:
        dmg += (20.0 + 0.02 * ap) * burn_t * magic_mult(apply_pen(mr, stats["pct"], stats["flat"])) * suffer

    _ = vs_tank  # commit discount applied by caller
    return dmg


def spear_only_expected(
    *,
    level: int,
    minute: int,
    stats: dict,
    hp: float,
    mr: float,
    amp: float,
    vs_tank: bool,
) -> Tuple[float, int]:
    """Expected damage over WINDOW throwing spears, never converting.

    Default combat spam is a mix: 70% mid-range (trying to hit) and 30%
    greedy max-range. Pass amp=AMP_MAX/MID to force a single range.
    """
    ap = stats["ap"]
    n = spear_throws(stats["ah"], WINDOW)
    if amp < 0:
        # Mixed Q spam (charitable spear-only).
        p = 0.30 * hit_rate(AMP_MAX, vs_tank) + 0.70 * hit_rate(AMP_MID, vs_tank)
        raw_spear = (
            0.30 * javelin_damage(level, ap, AMP_MAX)
            + 0.70 * javelin_damage(level, ap, AMP_MID)
        )
        comet_amp = 0.30 * AMP_MAX + 0.70 * AMP_MID
        comet_land = 0.80
    else:
        p = hit_rate(amp, vs_tank)
        raw_spear = javelin_damage(level, ap, amp)
        comet_amp = amp
        comet_land = 0.70 if amp >= 1.7 else 0.85
    suffer = suffer_mult(stats, WINDOW)
    horizon_after = stats["horizon"]
    extra_flat = 0.0

    # First hit does not yet have Horizon; later hits do.
    # Expected: n * p hits. Treat hit 1 as unmarked, rest marked.
    exp_hits = n * p
    first_hit_share = min(1.0, exp_hits)  # at most one "first"
    later_hits = max(0.0, exp_hits - first_hit_share)

    def mag(raw: float, horizon: bool, cinder: float = 1.0) -> float:
        return apply_magic(
            raw, mr, stats, extra_flat=extra_flat, cinder=cinder,
            horizon=horizon, suffer=suffer,
        )

    dmg = 0.0
    dmg += first_hit_share * mag(raw_spear, horizon=False)
    dmg += later_hits * mag(raw_spear, horizon=horizon_after)

    if stats["luden"]:
        # One Echo on the first successful spear (12s ICD).
        dmg += (1.0 - (1.0 - p) ** n) * mag(105.0 + 0.07 * ap, horizon=horizon_after)

    # Comet: spear-only page. One guaranteed if any hit and CD allows a second.
    p_any = 1.0 - (1.0 - p) ** n
    dmg += p_any * comet_land * mag(comet_raw(level, ap, comet_amp), horizon=horizon_after)
    if WINDOW > comet_cd(level) + 0.5:
        # Second comet only if a later spear hits after CD.
        dmg += later_hits * 0.5 * comet_land * mag(
            comet_raw(level, ap, comet_amp), horizon=horizon_after
        )

    dmg += p_any * mag(scorch_raw(level), horizon=horizon_after)

    # Liandry: 3s per application. Spears every q_cd seconds, so uptime is
    # 3s per hit, overlapping if CD < 3s (it isn't until very high AH).
    cd = q_cd(stats["ah"])
    # Expected burn seconds ≈ exp_hits * min(3, cd) with no overlap if cd>=3.
    burn_each = min(3.0, cd)
    burn_s = min(WINDOW, exp_hits * burn_each)
    m = magic_mult(apply_pen(mr, stats["pct"], stats["flat"])) * suffer
    hz = 1.0 + (HORIZON_AMP if horizon_after else 0.0)
    if stats["liandry"]:
        dmg += 0.02 * hp * burn_s * m * hz
    elif stats["ashes"] and not stats["bf"]:
        dmg += 5.0 * burn_s * m
    if stats["bf"]:
        dmg += (20.0 + 0.02 * ap) * burn_s * m * hz

    if stats["storm"]:
        # A max spear on a squishy often crosses 25% max HP; tanks rarely.
        one = mag(raw_spear, horizon=False)
        if one >= 0.25 * hp:
            dmg += p_any * mag(140.0 + 0.20 * ap, horizon=horizon_after)
        elif vs_tank:
            pass
        else:
            # Two hits might.
            p_two = 1.0 - (1.0 - p) ** n - n * p * (1.0 - p) ** (n - 1) if n >= 2 else 0.0
            if 2 * one >= 0.25 * hp:
                dmg += p_two * mag(140.0 + 0.20 * ap, horizon=horizon_after)

    # DH almost never from full-HP poke on a tank; squishy maybe after 2 spears.
    if not vs_tank:
        one = mag(raw_spear, horizon=False)
        if one >= 0.50 * hp:
            dmg += p_any * mag(dh_raw(level, ap, minute), horizon=horizon_after) * 0.0
            # Spear-only runs Comet, not DH. Left as 0 on purpose.

    return dmg, n


def convert_expected(
    *,
    level: int,
    minute: int,
    stats: dict,
    hp: float,
    mr: float,
    vs_tank: bool,
) -> Tuple[float, int]:
    """Throw Hunt-range spears until one hits, then convert once.

    Missed spears deal 0. After the combo (~3s) you can throw one more
    human spear if the window has time, at mid range while they run.
    """
    n = spear_throws(stats["ah"], WINDOW)
    p = hit_rate(AMP_SHORT, vs_tank)
    commit = TANK_CONVERT_COMMIT if vs_tank else 1.0
    combo = combo_landed(
        level=level, minute=minute, stats=stats, hp=hp, mr=mr,
        spear_amp=AMP_SHORT, vs_tank=vs_tank,
    )
    combo *= COUGAR_COMBO_LAND * commit

    # P(convert on throw k) = (1-p)^{k-1} * p, k=1..n, remaining time after.
    exp = 0.0
    p_fail = 1.0
    for k in range(1, n + 1):
        pk = p_fail * p
        exp += pk * combo
        p_fail *= (1.0 - p)

    # Residual: if the first convert happened early, one extra mid spear
    # after swapping back (~3.2s combo). Approx: P(first hit on throw 1 or 2)
    # times mid-spear expected hit.
    p_early = p + (1.0 - p) * p
    mid_p = hit_rate(AMP_MID, vs_tank)
    leftover_spear = apply_magic(
        javelin_damage(level, stats["ap"], AMP_MID),
        mr, stats, horizon=stats["horizon"],
        suffer=suffer_mult(stats, 2.0),
    )
    exp += p_early * mid_p * leftover_spear
    return exp, n


def window_damage(
    playstyle: str,
    level: int,
    minute: int,
    stats: dict,
    hp: float,
    mr: float,
    vs_tank: bool,
) -> Tuple[float, int]:
    if playstyle == "spear":
        # Charitable Q spam: mix mid-range hits with some greedy max spears.
        return spear_only_expected(
            level=level, minute=minute, stats=stats, hp=hp, mr=mr,
            amp=-1.0, vs_tank=vs_tank,
        )
    return convert_expected(
        level=level, minute=minute, stats=stats, hp=hp, mr=mr, vs_tank=vs_tank,
    )


def compute_snapshot(build_name: str, path: List[str], minute: int) -> Snapshot:
    gold = gold_at_minute(minute)
    level = level_at_minute(minute)
    style = playstyle_of(build_name)
    inv = resolve_inventory(path, gold)
    st = sum_stats(inv, style)

    thp, tmr = tank_hp(minute), tank_mr(minute)
    shp, smr = squishy_hp(minute), squishy_mr(minute)

    exp_t, n = window_damage(style, level, minute, st, thp, tmr, True)
    exp_s, _ = window_damage(style, level, minute, st, shp, smr, False)

    landed_spear = apply_magic(
        javelin_damage(level, st["ap"], AMP_MAX),
        smr, st, suffer=1.0,
    )
    landed_combo = combo_landed(
        level=level, minute=minute, stats=st, hp=shp, mr=smr,
        spear_amp=AMP_SHORT, vs_tank=False,
    )

    kill_s = min(1.5, exp_s / max(1.0, shp))
    kill_t = min(1.5, exp_t / max(1.0, thp))

    n_leg = sum(1 for nme in st["names"] if nme in LEGENDARIES)
    notes = []
    if st["lich"]:
        notes.append("Lich" + ("(no auto)" if style == "spear" else "+Takedown"))
    if st["horizon"]:
        notes.append("Hypershot")
    if st["liandry"]:
        notes.append("%HP burn")
    if st["void"]:
        notes.append("%pen")
    if st["belt"]:
        notes.append("Belt dash")
    if st["sf"]:
        notes.append("Cinderbloom")
    if n_leg == 0:
        notes.append("pre-legendary")

    return Snapshot(
        minute=minute,
        build_name=build_name,
        playstyle=style,
        items=st["names"],
        gold=gold,
        level=level,
        ap=round(st["ap"], 1),
        ah=st["ah"],
        legendary_count=n_leg,
        spears_thrown=n,
        exp_tank=round(exp_t, 1),
        exp_squish=round(exp_s, 1),
        kill_tank=round(kill_t, 3),
        kill_squish=round(kill_s, 3),
        landed_spear=round(landed_spear, 1),
        landed_combo=round(landed_combo, 1),
        notes=", ".join(notes) if notes else "-",
        has_lich=st["lich"],
        has_liandry=st["liandry"],
        has_horizon=st["horizon"],
        has_void=st["void"],
        has_belt=st["belt"],
        has_sf=st["sf"],
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

        def score(pair) -> float:
            name, s = pair
            # Worth-to-play score: must kill squishies AND not be useless vs tanks.
            # Convert's job is picks; spear-only's job is siege. Weight picks higher
            # because that's why you lock Nidalee.
            return 0.62 * s.exp_squish + 0.38 * s.exp_tank

        best_n, best_s = max(cands, key=score)
        timeline.append(
            {
                "minute": m,
                "winner": best_n,
                "exp_tank": best_s.exp_tank,
                "exp_squish": best_s.exp_squish,
                "kill_squish": best_s.kill_squish,
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


def summarize(results, timeline) -> str:
    lines = []
    lines.append("=" * 80)
    lines.append("NIDALEE — SPEAR-ONLY Q SPAM vs CONVERT  (PC LoL ~patch 26.18)")
    lines.append("Role: jungle | Game: 28:00 | Window: 12s skirmish/siege")
    lines.append("SO = stay human, mix of mid/max Q spam | CV = Hunt spear → cougar combo")
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
    lines.append("MINUTE-BY-MINUTE OPTIMAL (0.62 squish + 0.38 tank expected dmg)")
    lines.append("-" * 80)
    for row in timeline:
        if row["minute"] % 2 != 0 and row["minute"] not in (1, 9, 11, 15, 21):
            continue
        item_short = " › ".join(row["items"][:5])
        if len(row["items"]) > 5:
            item_short += " › …"
        lines.append(
            f"  {row['minute']:>2}:00 | squish {row['exp_squish']:>7.0f} "
            f"({100 * row['kill_squish']:.0f}% HP) | tank {row['exp_tank']:>7.0f} | "
            f"{row['winner']}"
        )
        lines.append(f"         items: {item_short}")
        lines.append(f"         {row['notes']}")

    def avg_score(snaps: List[Snapshot]) -> float:
        return sum(0.62 * s.exp_squish + 0.38 * s.exp_tank for s in snaps) / len(snaps)

    ranking = []
    for name, snaps in results.items():
        ranking.append((avg_score(snaps), name, snaps))
    ranking.sort(key=lambda x: x[0], reverse=True)

    lines.append("")
    lines.append("-" * 80)
    lines.append("BUILD COMPARISON — expected dmg / 12s @ spikes")
    lines.append("-" * 80)
    lines.append(
        f"  {'Build':<34} {'9s':>6} {'9t':>6} {'16s':>6} {'16t':>6} "
        f"{'22s':>6} {'22t':>6} {'Kill22':>7} {'Eff':>6}"
    )
    for eff, name, snaps in ranking:
        s9, s16, s22 = snaps[8], snaps[15], snaps[21]
        lines.append(
            f"  {name:<34} {s9.exp_squish:>6.0f} {s9.exp_tank:>6.0f} "
            f"{s16.exp_squish:>6.0f} {s16.exp_tank:>6.0f} "
            f"{s22.exp_squish:>6.0f} {s22.exp_tank:>6.0f} "
            f"{100 * s22.kill_squish:>6.0f}% {eff:>6.0f}"
        )

    lines.append("")
    lines.append("-" * 80)
    lines.append("LANDED HIT (100% accuracy) — one max spear vs one convert combo")
    lines.append("-" * 80)
    lines.append(f"  {'Build':<34} {'Spear16':>8} {'Combo16':>8} {'Spear22':>8} {'Combo22':>8}")
    for _, name, snaps in ranking:
        lines.append(
            f"  {name:<34} {snaps[15].landed_spear:>8.0f} {snaps[15].landed_combo:>8.0f} "
            f"{snaps[21].landed_spear:>8.0f} {snaps[21].landed_combo:>8.0f}"
        )

    # Headline A/Bs
    so_best = max(
        ((avg_score(s), n, s) for n, s in results.items() if n.startswith("SO ")),
        key=lambda x: x[0],
    )
    cv_best = max(
        ((avg_score(s), n, s) for n, s in results.items() if n.startswith("CV ")),
        key=lambda x: x[0],
    )
    so_lich = results["SO Lich → Belt → SF"]
    cv_lich = results["CV Lich → Belt → SF"]
    so_poke = results["SO Liandry → Horizon → Void"]
    cv_poke = results["CV Liandry → Horizon → Void"]

    def pct(a: float, b: float) -> float:
        return 100.0 * (a / b - 1.0) if b else 0.0

    lines.append("")
    lines.append("-" * 80)
    lines.append("A/B — SAME ITEMS, DIFFERENT PLAYSTYLE  @ 16:00 / 22:00")
    lines.append("-" * 80)
    for label, so, cv in (
        ("Lich → Belt → SF (her real build)", so_lich, cv_lich),
        ("Liandry → Horizon → Void (poke items)", so_poke, cv_poke),
    ):
        lines.append(f"  {label}")
        for m, i in ((16, 15), (22, 21)):
            lines.append(
                f"    {m}:00 squish  SO {so[i].exp_squish:.0f}  vs  CV {cv[i].exp_squish:.0f}  "
                f"({pct(so[i].exp_squish, cv[i].exp_squish):+.0f}%)   "
                f"kill {100 * so[i].kill_squish:.0f}% vs {100 * cv[i].kill_squish:.0f}%"
            )
            lines.append(
                f"    {m}:00 tank    SO {so[i].exp_tank:.0f}  vs  CV {cv[i].exp_tank:.0f}  "
                f"({pct(so[i].exp_tank, cv[i].exp_tank):+.0f}%)"
            )

    lines.append("")
    lines.append("-" * 80)
    lines.append("VERDICT")
    lines.append("-" * 80)
    lines.append(
        f"  Best convert path: {cv_best[1]}   (weighted avg {cv_best[0]:.0f})"
    )
    lines.append(
        f"  Best spear-only:   {so_best[1]}   (weighted avg {so_best[0]:.0f})"
    )
    cv22 = cv_best[2][21]
    so22 = so_best[2][21]
    lines.append(
        f"  At 22:00 vs squishy: convert {cv22.exp_squish:.0f} ({100 * cv22.kill_squish:.0f}% HP) "
        f"vs spear-only {so22.exp_squish:.0f} ({100 * so22.kill_squish:.0f}% HP), "
        f"{pct(so22.exp_squish, cv22.exp_squish):+.0f}%."
    )
    lines.append(
        f"  At 22:00 vs tank:    convert {cv22.exp_tank:.0f} vs spear-only {so22.exp_tank:.0f}, "
        f"{pct(so22.exp_tank, cv22.exp_tank):+.0f}%."
    )
    lines.append("")
    lines.append("  IS SPEAR-ONLY Q SPAM WORTH PLAYING?")
    lines.append("  No — not as Nidalee's identity. Yes — as the setup / siege phase.")
    lines.append("")
    lines.append("  WHY SPEAR-ONLY LOSES THE CHAMPION:")
    lines.append("  • Hunt exists to buff Takedown (+30%) and Pounce range. If you")
    lines.append("    never convert, you spent the kit's payoff button on a mark")
    lines.append("    you refuse to cash.")
    lines.append("  • A landed max spear is a chunk, not a kill. At 16:00 the spear")
    lines.append(
        f"    is {so_poke[15].landed_spear:.0f} into a {squishy_hp(16):.0f} HP squishy "
        f"({100 * so_poke[15].landed_spear / squishy_hp(16):.0f}% HP)."
    )
    lines.append(
        f"    The convert combo is {cv_lich[15].landed_combo:.0f} "
        f"({100 * cv_lich[15].landed_combo / squishy_hp(16):.0f}% HP) — that's a pick"
    )
    lines.append("    once they're already tagged, or with ignite / a teammate.")
    lines.append("  • Expected max-range accuracy is ~32% vs mobile targets. Even a")
    lines.append("    charitable mix (70% mid-range / 30% max) still loses the")
    lines.append("    squishy window because you never cash Hunt. Convert uses a")
    lines.append("    short Hunt spear (~68% hit) then melee that almost always lands.")
    lines.append("  • Lich Bane (~91% pick, her actual core) is Spellblade")
    lines.append("    on the Takedown auto. Spear-only never attacks, so the item is")
    lines.append(
        f"    dead. Same Lich path @22 squish: SO {so_lich[21].exp_squish:.0f} vs "
        f"CV {cv_lich[21].exp_squish:.0f}."
    )
    lines.append("  • Jungle clear / scuttle / 2v2 still needs cougar QWE. Spear-only")
    lines.append("    as a full-game plan is a different (worse) champion.")
    lines.append("")
    lines.append("  WHEN Q SPAM *IS* THE CORRECT BUTTON:")
    lines.append("  • Pre-objective poke and vs tanks you should not melee.")
    tank_delta = pct(so_poke[21].exp_tank, cv_lich[21].exp_tank)
    lines.append(
        f"    Liandry+Horizon spear-only vs tank @22: {so_poke[21].exp_tank:.0f} vs "
        f"Lich-convert {cv_lich[21].exp_tank:.0f} ({tank_delta:+.0f}%)."
    )
    lines.append("    Convert onto a healthy tank is discounted (55% commit) because")
    lines.append("    you often just die. Spear-only is the tank pattern.")
    lines.append("  • Horizon Focus 10% is real on long spears AND on the convert")
    lines.append("    that follows a ≥600-range Hunt mark (6s). Don't skip cougar")
    lines.append("    just because you bought a poke item.")
    lines.append("")
    lines.append("  HOW TO PLAY IT:")
    lines.append("  1) Clear and fight cougar. Human is for spears / heal / traps.")
    lines.append("  2) Spam Q to apply Hunt, not to farm poke damage. Short spears")
    lines.append("     that land beat max-range spears that miss.")
    lines.append("  3) Convert: Pounce (Hunt range) → Swipe → Takedown+Lich.")
    lines.append("  4) Vs tanks / siege: stay human, Liandry ticks, don't dive.")
    lines.append("  5) Build: Lich Bane → Sorcs → Rocketbelt → Shadowflame/Zhonya")
    lines.append("     into squishies. Swap Liandry/Horizon/Void when they stack HP.")
    lines.append("     Do not rush Lich if you refuse to auto.")
    lines.append("=" * 80)
    return "\n".join(lines)


def export_json(results, timeline, path: str) -> None:
    payload = {
        "meta": {
            "champion": "Nidalee",
            "role": "jungle",
            "patch": "26.18",
            "game_minutes": GAME_MINUTES,
            "window_s": WINDOW,
            "question": "Is spear-only Q spam worth playing?",
            "hit_rates": {
                "max_squish": HIT_MAX_SQUISH,
                "max_tank": HIT_MAX_TANK,
                "short_squish": HIT_SHORT_SQUISH,
                "short_tank": HIT_SHORT_TANK,
            },
            "tank_convert_commit": TANK_CONVERT_COMMIT,
        },
        "timeline": timeline,
        "builds": {
            name: [
                {
                    "minute": s.minute,
                    "playstyle": s.playstyle,
                    "items": s.items,
                    "gold": s.gold,
                    "level": s.level,
                    "ap": s.ap,
                    "ah": s.ah,
                    "legendary_count": s.legendary_count,
                    "spears_thrown": s.spears_thrown,
                    "exp_tank": s.exp_tank,
                    "exp_squish": s.exp_squish,
                    "kill_tank": s.kill_tank,
                    "kill_squish": s.kill_squish,
                    "landed_spear": s.landed_spear,
                    "landed_combo": s.landed_combo,
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
    cv = results["CV Lich → Belt → SF"]
    so_lich = results["SO Lich → Belt → SF"]
    so_poke = results["SO Liandry → Horizon → Void"]
    cv_poke = results["CV Liandry → Horizon → Void"]

    # Convert with her real item must beat spear-only on that same item vs squishies.
    assert cv[15].exp_squish > so_lich[15].exp_squish, (
        cv[15].exp_squish,
        so_lich[15].exp_squish,
    )
    assert cv[21].exp_squish > so_lich[21].exp_squish
    # Kill threat: convert is a pick, spear-only is a chunk.
    assert cv[21].kill_squish > so_poke[21].kill_squish
    assert cv[15].landed_combo > cv[15].landed_spear * 1.25
    # Lich Bane is wasted if you never auto: poke items beat Lich on spear-only.
    assert so_poke[21].exp_squish > so_lich[21].exp_squish
    # Same poke items: converting the landed spear still beats never converting vs squish.
    assert cv_poke[21].exp_squish > so_poke[21].exp_squish
    # Spear-only is allowed to win the tank column vs melee convert on Lich.
    assert so_poke[21].exp_tank >= cv[21].exp_tank * 0.85
    # Lich convert comes online as a legendary before 12:00 on this gold curve.
    lich_m = first_minute_with(cv, lambda s: s.has_lich)
    assert lich_m is not None and lich_m <= 12, lich_m


def main() -> None:
    results, timeline = run_all()
    self_check(results)
    report = summarize(results, timeline)
    print(report)
    out_dir = "/workspace/nidalee-spear-sim"
    with open(f"{out_dir}/report.txt", "w", encoding="utf-8") as f:
        f.write(report + "\n")
    export_json(results, timeline, f"{out_dir}/results.json")
    print(f"\nWrote {out_dir}/report.txt and {out_dir}/results.json")


if __name__ == "__main__":
    main()
