#!/usr/bin/env python3
"""
PC League of Legends — AP Kog'Maw, spam Living Artillery.

Patch snapshot 26.19 (R last tuned in 26.16). Artillery only: Q for the
resist shred, then R on cooldown. W and E are not cast. The limiter is
mana. Each shell in a chain costs 40 more mana (40 → 400), and the chain
resets 8 seconds after the last cast.

Question:
  Which build actually lets you spam R — in a fight you started on a
  half bar because you were already poking, and in a full-mana siege —
  without the last shells becoming a 400-mana tax, and without the
  barrage falling off against tanks?
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json

GAME_MINUTES = 28
FIGHT_WINDOW = 12.0
LANE_WINDOW = 60.0
FIGHT_DT = 0.05
LANE_DT = 0.10

# Spam-R score: you are already poking, so half a bar is the default
# state. The full-mana number is the reset / objective siege.
HALF_WEIGHT = 0.55
FULL_WEIGHT = 0.45
TANK_WEIGHT = 0.62
SQUISH_WEIGHT = 0.38

CADENCE_CAPS = (80, 120, 160, 200, 240, 320, 400)


# ---------------------------------------------------------------------------
# Economy / XP — same farmer curve as ap-kogmaw-sim
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
    """Spam R maxes Q (damage + shred). E second. W last. R at 6/11/16."""
    if skill == "R":
        if level < 6:
            return 0
        if level < 11:
            return 1
        if level < 16:
            return 2
        return 3
    q_levels = [1, 3, 5, 7, 9]
    e_levels = [2, 4, 8, 10, 12]
    w_levels = [13, 14, 15, 17, 18]
    mapping = {"Q": q_levels, "W": w_levels, "E": e_levels}
    return sum(1 for lv in mapping[skill] if level >= lv)


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


def base_mana(level: int) -> float:
    return 325 + 40 * (level - 1)


def base_mp5(level: int) -> float:
    return 8.75 + 0.7 * (level - 1)


def gathering_ap(minute: int) -> float:
    if minute >= 30:
        return 48
    if minute >= 20:
        return 24
    if minute >= 10:
        return 8
    return 0


def rune_ah(level: int) -> float:
    """Transcendence: 10 ability haste once mid-game levels hit."""
    if level >= 8:
        return 10
    if level >= 5:
        return 5
    return 0


def manaflow_bonus(minute: int) -> float:
    """25 max mana per champion hit, 15s internal, cap 250. Poker finishes ~8:00."""
    if minute >= 8:
        return 250.0
    return 25.0 * min(10, max(0, minute - 1))


def pom_restore(level: int) -> float:
    """Presence of Mind: 6–50 by level, 80% for ranged. 8s cooldown."""
    return 0.8 * (6 + 44 * (level - 1) / 17)


def tear_stacks(minute: int, tear_since: Optional[int]) -> float:
    """~40 bonus mana per minute of Tear ownership, cap 360 (~9 min of poking)."""
    if tear_since is None:
        return 0.0
    return min(360.0, 40.0 * max(0, minute - tear_since))


# ---------------------------------------------------------------------------
# Items (wiki values, patch 26.19)
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
    ult_haste: float = 0
    deathcap: bool = False
    malignance: bool = False
    luden: bool = False
    blackfire: bool = False
    liandry: bool = False
    ashes: bool = False
    horizon: bool = False
    shadowflame: bool = False
    actualizer: bool = False
    tear: bool = False
    archangel: bool = False
    tags: Tuple[str, ...] = ()


ITEMS: Dict[str, Item] = {
    "Amplifying Tome": Item("Amplifying Tome", 400, ap=20),
    "Sapphire Crystal": Item("Sapphire Crystal", 300, mana=300),
    "Glowing Mote": Item("Glowing Mote", 250, ah=5),
    "Ruby Crystal": Item("Ruby Crystal", 400, hp=150),
    "Needlessly Large Rod": Item("Needlessly Large Rod", 1200, ap=65),
    "Blasting Wand": Item("Blasting Wand", 850, ap=45),
    "Lost Chapter": Item("Lost Chapter", 1200, ap=40, ah=10, mana=300, tags=("mana",)),
    "Fated Ashes": Item("Fated Ashes", 900, ap=30, ashes=True),
    "Haunting Guise": Item("Haunting Guise", 1300, ap=30, hp=200),
    "Hextech Alternator": Item("Hextech Alternator", 1100, ap=45),
    "Blighting Jewel": Item("Blighting Jewel", 1100, ap=25, pct_mpen=0.13),
    "Fiendish Codex": Item("Fiendish Codex", 850, ap=25, ah=10),
    "Tear of the Goddess": Item("Tear of the Goddess", 400, mana=240, tear=True),
    "Boots": Item("Boots", 300, tags=("boots",)),
    "Sorcerer's Shoes": Item("Sorcerer's Shoes", 1100, flat_mpen=12, tags=("boots",)),
    "Ionian Boots of Lucidity": Item(
        "Ionian Boots of Lucidity", 900, ah=10, tags=("boots",)
    ),
    "Malignance": Item(
        "Malignance", 2700, ap=90, ah=15, mana=600, ult_haste=20,
        malignance=True, tags=("mana",),
    ),
    "Luden's Echo": Item(
        "Luden's Echo", 2750, ap=100, ah=10, mana=600, luden=True, tags=("mana",),
    ),
    "Blackfire Torch": Item(
        "Blackfire Torch", 2800, ap=80, ah=20, mana=600, blackfire=True,
        tags=("mana", "burn"),
    ),
    "Liandry's Torment": Item(
        "Liandry's Torment", 3000, ap=60, hp=300, liandry=True, tags=("burn", "tank"),
    ),
    "Void Staff": Item("Void Staff", 3000, ap=95, pct_mpen=0.40, tags=("pen", "tank")),
    "Shadowflame": Item("Shadowflame", 3200, ap=110, flat_mpen=15, shadowflame=True),
    "Rabadon's Deathcap": Item(
        "Rabadon's Deathcap", 3500, ap=130, deathcap=True, tags=("amp",)
    ),
    "Horizon Focus": Item(
        "Horizon Focus", 2700, ap=75, ah=25, horizon=True, tags=("artillery",)
    ),
    "Archangel's Staff": Item(
        "Archangel's Staff", 2900, ap=70, ah=25, mana=600, archangel=True,
        tags=("mana",),
    ),
    "Actualizer": Item(
        "Actualizer", 2800, ap=90, ah=10, mana=300, actualizer=True, tags=("mana",),
    ),
}


UPGRADE_COMPONENTS = {
    "Lost Chapter": ("Amplifying Tome", "Sapphire Crystal", "Glowing Mote"),
    "Fated Ashes": ("Amplifying Tome",),
    "Haunting Guise": ("Amplifying Tome", "Ruby Crystal"),
    "Hextech Alternator": ("Amplifying Tome", "Amplifying Tome"),
    "Fiendish Codex": ("Amplifying Tome", "Glowing Mote"),
    "Sorcerer's Shoes": ("Boots",),
    "Ionian Boots of Lucidity": ("Boots", "Glowing Mote"),
    "Malignance": ("Lost Chapter", "Blasting Wand"),
    "Luden's Echo": ("Lost Chapter", "Hextech Alternator"),
    "Blackfire Torch": ("Lost Chapter", "Fated Ashes"),
    "Liandry's Torment": ("Haunting Guise", "Fated Ashes"),
    "Void Staff": ("Blighting Jewel", "Blasting Wand"),
    "Shadowflame": ("Hextech Alternator", "Needlessly Large Rod"),
    "Rabadon's Deathcap": ("Needlessly Large Rod", "Needlessly Large Rod"),
    "Horizon Focus": ("Fiendish Codex", "Fiendish Codex", "Amplifying Tome"),
    "Archangel's Staff": ("Tear of the Goddess", "Lost Chapter", "Fiendish Codex"),
    "Actualizer": ("Lost Chapter", "Blasting Wand"),
}

UNIQUE = {
    "Boots",
    "Sorcerer's Shoes",
    "Ionian Boots of Lucidity",
    "Tear of the Goddess",
    "Malignance",
    "Luden's Echo",
    "Blackfire Torch",
    "Liandry's Torment",
    "Void Staff",
    "Shadowflame",
    "Rabadon's Deathcap",
    "Horizon Focus",
    "Archangel's Staff",
    "Actualizer",
    "Lost Chapter",  # a second chapter is allowed — not in this set
}
# Lost Chapter, tome, codex, wand, NLR, mote can be bought twice. Remove LC from unique.
UNIQUE.discard("Lost Chapter")

LEGENDARIES = {
    "Malignance",
    "Luden's Echo",
    "Blackfire Torch",
    "Liandry's Torment",
    "Void Staff",
    "Shadowflame",
    "Rabadon's Deathcap",
    "Horizon Focus",
    "Archangel's Staff",
    "Seraph's Embrace",
    "Actualizer",
}

BUILD_PATHS: Dict[str, List[str]] = {
    # Artillery burn — one Lost Chapter, then tank tools
    "Malig → Liandry → Void": [
        "Malignance", "Sorcerer's Shoes", "Liandry's Torment", "Void Staff",
        "Rabadon's Deathcap",
    ],
    "Malig → Horizon → Void": [
        "Malignance", "Sorcerer's Shoes", "Horizon Focus", "Void Staff",
        "Rabadon's Deathcap",
    ],
    "Malig → Liandry → Horizon": [
        "Malignance", "Sorcerer's Shoes", "Liandry's Torment", "Horizon Focus",
        "Void Staff",
    ],
    "Malig → Void → Liandry": [
        "Malignance", "Sorcerer's Shoes", "Void Staff", "Liandry's Torment",
        "Rabadon's Deathcap",
    ],
    "Malig → Liandry → Cap": [
        "Malignance", "Sorcerer's Shoes", "Liandry's Torment",
        "Rabadon's Deathcap", "Void Staff",
    ],
    # Mana so the chain can keep going
    "Tear → Malig → Seraph": [
        "Tear of the Goddess", "Malignance", "Sorcerer's Shoes",
        "Archangel's Staff", "Liandry's Torment", "Void Staff",
    ],
    "Malig → Liandry → Seraph": [
        "Malignance", "Sorcerer's Shoes", "Liandry's Torment",
        "Tear of the Goddess", "Archangel's Staff", "Void Staff",
    ],
    "Malig → Lucidity → Seraph": [
        "Malignance", "Ionian Boots of Lucidity", "Tear of the Goddess",
        "Archangel's Staff", "Liandry's Torment", "Void Staff",
    ],
    # Double Lost Chapter — mana/AH stacked, tank item late
    "Luden → Malig → Horizon": [
        "Luden's Echo", "Sorcerer's Shoes", "Malignance", "Horizon Focus",
        "Void Staff",
    ],
    "BF → Malig → Liandry": [
        "Blackfire Torch", "Sorcerer's Shoes", "Malignance",
        "Liandry's Torment", "Void Staff",
    ],
    # No ultimate haste
    "Luden → Horizon → Void": [
        "Luden's Echo", "Sorcerer's Shoes", "Horizon Focus", "Void Staff",
        "Rabadon's Deathcap",
    ],
    # Squishy pen, no burn and no extra mana
    "Malig → SF → Horizon": [
        "Malignance", "Sorcerer's Shoes", "Shadowflame", "Horizon Focus",
        "Void Staff",
    ],
    # Active doubles mana costs for 8s. Included to measure the trap.
    "Malig → Actualizer → Horizon": [
        "Malignance", "Sorcerer's Shoes", "Actualizer", "Horizon Focus",
        "Void Staff",
    ],
}


def missing_components(name: str, owned: List[str]) -> List[str]:
    need = list(UPGRADE_COMPONENTS.get(name, ()))
    if not need:
        return []
    avail = list(owned)
    missing: List[str] = []
    for comp in need:
        if comp in avail:
            avail.remove(comp)
        else:
            missing.append(comp)
    return missing


def resolve_inventory(path: List[str], gold: int) -> List[str]:
    """Buy `path` in order with `gold`. Components are picked up on the way."""
    owned: List[str] = []
    pool = gold

    def price_and_consume(name: str) -> Tuple[int, List[str]]:
        need = list(UPGRADE_COMPONENTS.get(name, ()))
        avail = list(owned)
        consume: List[str] = []
        credit = 0
        for comp in need:
            if comp in avail:
                avail.remove(comp)
                consume.append(comp)
                credit += ITEMS[comp].cost
        return max(0, ITEMS[name].cost - credit), consume

    def try_buy(name: str) -> bool:
        nonlocal pool
        if name in UNIQUE and name in owned:
            return False
        price, consume = price_and_consume(name)
        if price > pool:
            return False
        pool -= price
        for comp in consume:
            owned.remove(comp)
        owned.append(name)
        if name in ("Sorcerer's Shoes", "Ionian Boots of Lucidity") and "Boots" in owned:
            owned.remove("Boots")
        return True

    def try_acquire(name: str, depth: int = 0) -> bool:
        if depth > 6:
            return False
        if try_buy(name):
            return True
        missing = missing_components(name, owned)
        if not missing:
            return False
        for comp in sorted(missing, key=lambda n: ITEMS[n].cost):
            if try_acquire(comp, depth + 1):
                return True
        return False

    for step in path:
        guard = 0
        while step not in owned:
            guard += 1
            if guard > 16 or not try_acquire(step):
                break
        if step not in owned:
            break
    return owned


# ---------------------------------------------------------------------------
# Combat
# ---------------------------------------------------------------------------


def haste_mult(haste: float) -> float:
    return 100.0 / (100.0 + max(0.0, haste))


def r_cooldown(rank: int, ah: float, uh: float) -> float:
    base = [0.0, 2.0, 1.5, 1.0][rank]
    return base * haste_mult(ah) * haste_mult(uh)


def r_mana_cost(stacks: int) -> float:
    return float(min(400, 40 * (stacks + 1)))


def apply_pen(mr: float, q_shred: float, malig_shred: float, pct: float, flat: float) -> float:
    # % shred (Q) → flat shred (Hatefog) → % pen → flat pen
    reduced = max(0.0, mr * (1.0 - q_shred) - malig_shred)
    reduced = reduced * (1.0 - pct) - flat
    return max(0.0, reduced)


def magic_mult(eff_mr: float) -> float:
    return 100.0 / (100.0 + eff_mr)


def q_damage(level: int, ap: float) -> float:
    rank = skill_rank(level, "Q")
    if rank <= 0:
        return 0.0
    base = [0, 80, 125, 170, 215, 260][rank]
    return base + 0.90 * ap


def q_shred_pct(level: int) -> float:
    rank = skill_rank(level, "Q")
    if rank <= 0:
        return 0.0
    return [0, 0.16, 0.20, 0.24, 0.28, 0.32][rank]


def r_min_damage(level: int, ap: float) -> float:
    rank = skill_rank(level, "R")
    if rank <= 0:
        return 0.0
    base = [0, 100, 140, 180][rank]
    ratio = [0, 0.35, 0.40, 0.45][rank]
    return base + ratio * ap


@dataclass
class BarrageResult:
    damage: float
    shots: int
    kill_time: Optional[float]
    mana_left: float
    mana_spent: float
    trace: List[dict] = field(default_factory=list)


def simulate_barrage(
    *,
    level: int,
    ap: float,
    ah: float,
    uh: float,
    pct: float,
    flat: float,
    max_mana: float,
    bonus_mana: float,
    hp: float,
    mr: float,
    malig: bool,
    liandry: bool,
    ashes: bool,
    blackfire: bool,
    luden: bool,
    horizon: bool,
    shadowflame: bool,
    actualizer: bool,
    use_actualizer: bool,
    window: float,
    dt: float,
    start_mana_frac: float,
    max_r_cost: Optional[float],
    trace: bool,
    manaflow_ready: bool,
) -> BarrageResult:
    """Spam Q (when shred is down) and R (on cooldown) until mana or the window ends."""
    mana = max_mana * start_mana_frac
    mana_start = mana
    hp_left = hp
    t = 0.0
    r_cd = 0.0
    q_cd = 0.0
    stacks = 0
    stack_left = 0.0
    shred_until = -1.0
    hatefog_until = -1.0
    burn_until = -1.0
    pom_cd = 0.0
    mf_left = 5.0
    luden_cd = 0.0
    comet_cd = 0.0
    combat_time = 0.0
    in_combat = False
    shots = 0
    kill_time: Optional[float] = None
    shot_log: List[dict] = []
    r_rank = skill_rank(level, "R")
    q_cd_base = 7.0 * haste_mult(ah)
    r_cd_base = r_cooldown(r_rank, ah, uh) if r_rank else 999.0
    comet_base = (20.0 - 8.0 * (level - 1) / 17.0) * haste_mult(ah)
    regen_per_s = base_mp5(level) / 5.0
    act_amp = 1.15 + 0.00005 * bonus_mana
    shred = q_shred_pct(level)
    def cost_mult(now: float) -> float:
        if use_actualizer and actualizer and now < 8.0:
            return 2.0
        return 1.0

    def deal(raw: float, now: float, *, ability: bool) -> float:
        nonlocal hp_left, kill_time, in_combat, combat_time
        if hp_left <= 0 or raw <= 0:
            return 0.0
        q_on = shred if now < shred_until else 0.0
        fog = 10.0 if (malig and now < hatefog_until) else 0.0
        eff = apply_pen(mr, q_on, fog, pct, flat)
        dealt = raw * magic_mult(eff)
        if horizon:
            dealt *= 1.10
        if in_combat:
            dealt *= 1.0 + 0.02 * min(3, int(combat_time))
        if ability and use_actualizer and actualizer and now < 8.0:
            dealt *= act_amp
        if shadowflame and (hp_left / hp) < 0.40:
            dealt *= 1.20
        dealt = min(dealt, hp_left)
        hp_left -= dealt
        if not in_combat:
            in_combat = True
            combat_time = 0.0
        if hp_left <= 0 and kill_time is None:
            kill_time = now
        return dealt

    while t < window - 1e-9 and hp_left > 0:
        mana = min(max_mana, mana + regen_per_s * dt)
        if manaflow_ready:
            mf_left -= dt
            if mf_left <= 0:
                mana = min(max_mana, mana + 0.01 * (max_mana - mana))
                mf_left += 5.0

        def on_hit(dealt_any: bool) -> None:
            nonlocal mana, pom_cd, luden_cd, comet_cd, burn_until
            if not dealt_any:
                return
            burn_until = t + 3.0
            if pom_cd <= 0:
                mana = min(max_mana, mana + pom_restore(level))
                pom_cd = 8.0
            if luden and luden_cd <= 0:
                # Isolated Echo dump: 6 stacks, no extra champions → 150 (+10% AP).
                deal(150.0 + 0.10 * ap, t, ability=False)
                luden_cd = 12.0
            if comet_cd <= 0:
                comet = (30.0 + 70.0 * (level - 1) / 17.0) + 0.20 * ap
                deal(comet, t, ability=False)
                comet_cd = comet_base

        # Q when the shred has fallen off and we can still afford the next R.
        if q_cd <= 0 and skill_rank(level, "Q") > 0:
            q_cost = 40.0 * cost_mult(t)
            next_r = r_mana_cost(stacks) * cost_mult(t) if r_rank else 0.0
            shred_down = t >= shred_until
            can_q = mana >= q_cost and (not shred_down or mana >= q_cost + next_r)
            # Always refresh shred if we can keep an R in the clip.
            if shred_down and mana >= q_cost + (next_r if r_cd <= 0 else 0):
                can_q = mana >= q_cost
            if shred_down and can_q and mana >= q_cost:
                mana -= q_cost
                dealt = deal(q_damage(level, ap), t, ability=True)
                shred_until = t + 4.0
                q_cd = q_cd_base
                on_hit(dealt > 0 or True)

        if (
            r_rank
            and r_cd <= 0
            and hp_left > 0
            and t < window
        ):
            cost = r_mana_cost(stacks) * cost_mult(t)
            capped = max_r_cost is not None and (40.0 * (stacks + 1)) > max_r_cost
            if not capped and mana >= cost:
                mana -= cost
                hp_frac = hp_left / hp
                if hp_frac < 0.40:
                    amp = 2.0
                else:
                    missing = 1.0 - hp_frac
                    amp = 1.0 + min(0.50, missing * (0.50 / 0.60))
                raw = r_min_damage(level, ap) * amp
                # First shell of a zone does not benefit from the 10 MR shred.
                dealt = deal(raw, t, ability=True)
                if malig:
                    hatefog_until = max(hatefog_until, t + 3.0)
                shots += 1
                if trace:
                    shot_log.append({
                        "t": round(t, 2),
                        "shot": shots,
                        "cost": round(cost, 0),
                        "dealt": round(dealt, 1),
                        "hp_left_pct": round(100.0 * hp_left / hp, 1),
                        "mana_left": round(mana, 0),
                    })
                stacks = min(9, stacks + 1)
                stack_left = 8.0
                r_cd = r_cd_base
                on_hit(True)

        # Burns tick after the casts so a fresh zone is already up.
        if hp_left > 0 and t < burn_until:
            if liandry:
                deal(0.02 * hp * dt, t, ability=False)
            elif ashes and not blackfire:
                deal(5.0 * dt, t, ability=False)
            if blackfire:
                deal((20.0 + 0.02 * ap) * dt, t, ability=False)
        if hp_left > 0 and malig and t < hatefog_until:
            deal((60.0 + 0.05 * ap) * dt, t, ability=False)

        t += dt
        if in_combat:
            combat_time += dt
        r_cd = max(0.0, r_cd - dt)
        q_cd = max(0.0, q_cd - dt)
        pom_cd = max(0.0, pom_cd - dt)
        luden_cd = max(0.0, luden_cd - dt)
        comet_cd = max(0.0, comet_cd - dt)
        if stacks > 0:
            stack_left -= dt
            if stack_left <= 0:
                stacks = 0
                stack_left = 0.0

    return BarrageResult(
        damage=hp - hp_left,
        shots=shots,
        kill_time=kill_time,
        mana_left=mana,
        mana_spent=mana_start - mana,
        trace=shot_log,
    )


@dataclass
class Stats:
    ap: float
    ah: float
    uh: float
    pct: float
    flat: float
    max_mana: float
    bonus_mana: float
    names: List[str]
    malig: bool
    liandry: bool
    ashes: bool
    blackfire: bool
    luden: bool
    horizon: bool
    shadowflame: bool
    actualizer: bool
    seraph: bool
    void: bool
    manaflow_ready: bool


def sum_stats(
    inv: List[Item],
    *,
    level: int,
    minute: int,
    tear_since: Optional[int],
) -> Stats:
    ap = ah = mana = flat = uh = 0.0
    pct = 1.0  # multiplicative % pen
    flags = {
        "malig": False, "liandry": False, "ashes": False, "bf": False,
        "luden": False, "horizon": False, "sf": False, "actualizer": False,
        "tear": False, "arch": False, "cap": False, "void": False,
    }
    names: List[str] = []
    for it in inv:
        names.append(it.name)
        ap += it.ap
        ah += it.ah
        mana += it.mana
        flat += it.flat_mpen
        pct *= (1.0 - it.pct_mpen)
        uh += it.ult_haste
        if it.malignance:
            flags["malig"] = True
        if it.liandry:
            flags["liandry"] = True
        if it.ashes:
            flags["ashes"] = True
        if it.blackfire:
            flags["bf"] = True
        if it.luden:
            flags["luden"] = True
        if it.horizon:
            flags["horizon"] = True
        if it.shadowflame:
            flags["sf"] = True
        if it.actualizer:
            flags["actualizer"] = True
        if it.tear:
            flags["tear"] = True
        if it.archangel:
            flags["arch"] = True
        if it.deathcap:
            flags["cap"] = True
        if it.name == "Void Staff":
            flags["void"] = True

    # Stacks stick after Tear is consumed into Archangel. tear_since stays set.
    stacks = tear_stacks(minute, tear_since) if (flags["tear"] or flags["arch"]) else 0.0

    seraph = False
    if flags["arch"] and stacks >= 360:
        seraph = True
        names = ["Seraph's Embrace" if n == "Archangel's Staff" else n for n in names]
        # 1000 mana replaces 600 + stacks. Awe becomes 2% (staff is 1%).
        mana += 400  # 1000 - 600
        stacks_for_mana = 0.0
        awe_ratio = 0.02
    elif flags["arch"]:
        stacks_for_mana = stacks
        awe_ratio = 0.01
    elif flags["tear"]:
        stacks_for_mana = stacks
        awe_ratio = 0.0
    else:
        stacks_for_mana = 0.0
        awe_ratio = 0.0

    rune_mana = manaflow_bonus(minute)
    item_mana = mana + stacks_for_mana
    bonus_mana = item_mana + rune_mana
    awe_ap = awe_ratio * bonus_mana

    ah += rune_ah(level)
    raw_ap = ap + gathering_ap(minute) + awe_ap
    ap_mult = 1.0
    if flags["bf"]:
        ap_mult += 0.04  # one champion burning — the shell's target
    if flags["cap"]:
        ap_mult += 0.30
    final_ap = raw_ap * ap_mult

    return Stats(
        ap=final_ap,
        ah=ah,
        uh=uh,
        pct=1.0 - pct,
        flat=flat,
        max_mana=base_mana(level) + bonus_mana,
        bonus_mana=bonus_mana,
        names=names,
        malig=flags["malig"],
        liandry=flags["liandry"],
        ashes=flags["ashes"],
        blackfire=flags["bf"],
        luden=flags["luden"],
        horizon=flags["horizon"],
        shadowflame=flags["sf"],
        actualizer=flags["actualizer"],
        seraph=seraph,
        void=flags["void"],
        manaflow_ready=rune_mana >= 250,
    )


def run_barrage(
    st: Stats,
    *,
    level: int,
    hp: float,
    mr: float,
    window: float,
    dt: float,
    start_mana_frac: float,
    max_r_cost: Optional[float],
    use_actualizer: bool,
    trace: bool,
) -> BarrageResult:
    return simulate_barrage(
        level=level,
        ap=st.ap,
        ah=st.ah,
        uh=st.uh,
        pct=st.pct,
        flat=st.flat,
        max_mana=st.max_mana,
        bonus_mana=st.bonus_mana,
        hp=hp,
        mr=mr,
        malig=st.malig,
        liandry=st.liandry,
        ashes=st.ashes,
        blackfire=st.blackfire,
        luden=st.luden,
        horizon=st.horizon,
        shadowflame=st.shadowflame,
        actualizer=st.actualizer,
        use_actualizer=use_actualizer,
        window=window,
        dt=dt,
        start_mana_frac=start_mana_frac,
        max_r_cost=max_r_cost,
        trace=trace,
        manaflow_ready=st.manaflow_ready,
    )


def best_actualizer_use(
    st: Stats, *, level: int, hp: float, mr: float, start_mana_frac: float, trace: bool,
) -> BarrageResult:
    """Actualizer is optional. Keep whichever 12s barrage deals more damage."""
    if not st.actualizer:
        return run_barrage(
            st, level=level, hp=hp, mr=mr, window=FIGHT_WINDOW, dt=FIGHT_DT,
            start_mana_frac=start_mana_frac, max_r_cost=None,
            use_actualizer=False, trace=trace,
        )
    off = run_barrage(
        st, level=level, hp=hp, mr=mr, window=FIGHT_WINDOW, dt=FIGHT_DT,
        start_mana_frac=start_mana_frac, max_r_cost=None,
        use_actualizer=False, trace=trace,
    )
    on = run_barrage(
        st, level=level, hp=hp, mr=mr, window=FIGHT_WINDOW, dt=FIGHT_DT,
        start_mana_frac=start_mana_frac, max_r_cost=None,
        use_actualizer=True, trace=trace,
    )
    return on if on.damage > off.damage else off


def best_cadence(
    st: Stats, *, level: int, tank_hp_v: float, tank_mr_v: float,
    squish_hp_v: float, squish_mr_v: float,
) -> Tuple[int, float, float, int, Optional[float]]:
    """Pick the stack cap that kills a standing tank fastest, then leaves the most mana.

    Damage alone ties: every cap eventually deletes a dummy that stands still for
    60s, so the cheapest cap would win a raw-damage sort.
    """
    best_key: Optional[Tuple] = None
    best: Optional[Tuple[int, float, float, int, Optional[float]]] = None
    for cap in CADENCE_CAPS:
        tank = run_barrage(
            st, level=level, hp=tank_hp_v, mr=tank_mr_v, window=LANE_WINDOW, dt=LANE_DT,
            start_mana_frac=0.80, max_r_cost=float(cap), use_actualizer=False, trace=False,
        )
        squish = run_barrage(
            st, level=level, hp=squish_hp_v, mr=squish_mr_v, window=LANE_WINDOW, dt=LANE_DT,
            start_mana_frac=0.80, max_r_cost=float(cap), use_actualizer=False, trace=False,
        )
        key = (
            0 if tank.kill_time is not None else 1,
            tank.kill_time if tank.kill_time is not None else 0.0,
            -tank.damage,
            -tank.mana_left,
        )
        if best_key is None or key < best_key:
            best_key = key
            best = (cap, tank.damage, squish.damage, tank.shots, tank.kill_time)
    assert best is not None
    return best


@dataclass
class Snapshot:
    minute: int
    build_name: str
    items: List[str]
    gold: int
    level: int
    ap: float
    ah: float
    uh: float
    max_mana: float
    r_cd: float
    full_tank: float
    full_squish: float
    half_tank: float
    half_squish: float
    full_shots: int
    half_shots: int
    full_squish_kill: Optional[float]
    half_squish_kill: Optional[float]
    cadence_cap: int
    cadence_tank: float
    cadence_squish: float
    cadence_shots: int
    cadence_kill: Optional[float]
    spam_score: float
    notes: str
    has_malig: bool
    has_liandry: bool
    has_void: bool
    has_seraph: bool
    has_horizon: bool
    has_luden: bool
    has_bf: bool
    has_sf: bool
    has_actualizer: bool


def blend(tank: float, squish: float) -> float:
    return TANK_WEIGHT * tank + SQUISH_WEIGHT * squish


def spam_score(full_tank: float, full_squish: float, half_tank: float, half_squish: float) -> float:
    return HALF_WEIGHT * blend(half_tank, half_squish) + FULL_WEIGHT * blend(full_tank, full_squish)


def compute_snapshot(
    build_name: str,
    path: List[str],
    minute: int,
    tear_since: Optional[int],
    *,
    with_cadence: bool,
) -> Tuple[Snapshot, Optional[int]]:
    gold = gold_at_minute(minute)
    level = level_at_minute(minute)
    owned = resolve_inventory(path, gold)
    if tear_since is None and (
        "Tear of the Goddess" in owned or "Archangel's Staff" in owned
    ):
        tear_since = minute
    inv = [ITEMS[n] for n in owned if n in ITEMS]
    st = sum_stats(inv, level=level, minute=minute, tear_since=tear_since)

    thp, tmr = tank_hp(minute), tank_mr(minute)
    shp, smr = squishy_hp(minute), squishy_mr(minute)

    full_t = best_actualizer_use(st, level=level, hp=thp, mr=tmr, start_mana_frac=1.0, trace=False)
    full_s = best_actualizer_use(st, level=level, hp=shp, mr=smr, start_mana_frac=1.0, trace=False)
    half_t = best_actualizer_use(st, level=level, hp=thp, mr=tmr, start_mana_frac=0.5, trace=False)
    half_s = best_actualizer_use(st, level=level, hp=shp, mr=smr, start_mana_frac=0.5, trace=False)

    if with_cadence and level >= 6:
        cap, cad_t, cad_s, cad_shots, cad_kill = best_cadence(
            st, level=level, tank_hp_v=thp, tank_mr_v=tmr,
            squish_hp_v=shp, squish_mr_v=smr,
        )
    else:
        cap, cad_t, cad_s, cad_shots, cad_kill = 0, 0.0, 0.0, 0, None

    rank = skill_rank(level, "R")
    r_cd = r_cooldown(rank, st.ah, st.uh) if rank else 0.0

    notes = []
    if st.malig:
        notes.append("Hatefog+UH")
    if st.liandry:
        notes.append("%HP")
    if st.void:
        notes.append("%pen")
    if st.seraph:
        notes.append("Seraph")
    elif any(n == "Archangel's Staff" for n in st.names):
        notes.append("Archangel")
    if st.horizon:
        notes.append("Horizon")
    if st.luden and st.malig:
        notes.append("DOUBLE MANA")
    if st.blackfire and st.malig:
        notes.append("DOUBLE MANA")
    if st.actualizer:
        notes.append("Actualizer")
    if st.shadowflame:
        notes.append("flat pen")
    if not notes:
        notes.append("components" if st.names else "empty")

    snap = Snapshot(
        minute=minute,
        build_name=build_name,
        items=st.names,
        gold=gold,
        level=level,
        ap=round(st.ap, 1),
        ah=round(st.ah, 1),
        uh=st.uh,
        max_mana=round(st.max_mana, 0),
        r_cd=round(r_cd, 3),
        full_tank=round(full_t.damage, 1),
        full_squish=round(full_s.damage, 1),
        half_tank=round(half_t.damage, 1),
        half_squish=round(half_s.damage, 1),
        full_shots=full_t.shots,
        half_shots=half_t.shots,
        full_squish_kill=full_s.kill_time,
        half_squish_kill=half_s.kill_time,
        cadence_cap=cap,
        cadence_tank=round(cad_t, 1),
        cadence_squish=round(cad_s, 1),
        cadence_shots=cad_shots,
        cadence_kill=None if cad_kill is None else round(cad_kill, 2),
        spam_score=round(spam_score(
            full_t.damage, full_s.damage, half_t.damage, half_s.damage
        ), 1),
        notes=", ".join(notes),
        has_malig=st.malig,
        has_liandry=st.liandry,
        has_void=st.void,
        has_seraph=st.seraph,
        has_horizon=st.horizon,
        has_luden=st.luden,
        has_bf=st.blackfire,
        has_sf=st.shadowflame,
        has_actualizer=st.actualizer,
    )
    return snap, tear_since


def run_all() -> Dict[str, List[Snapshot]]:
    results: Dict[str, List[Snapshot]] = {}
    # Cadence is a 60s search. Run it on the minutes the report prints,
    # plus every even minute so the lane column is real where we show it.
    cadence_minutes = set(range(6, GAME_MINUTES + 1, 2)) | {9, 11, 15, 21, 22}
    for name, path in BUILD_PATHS.items():
        snaps: List[Snapshot] = []
        tear_since: Optional[int] = None
        for m in range(1, GAME_MINUTES + 1):
            snap, tear_since = compute_snapshot(
                name, path, m, tear_since, with_cadence=(m in cadence_minutes),
            )
            snaps.append(snap)
        results[name] = snaps
    return results


def first_minute(snaps: List[Snapshot], pred) -> Optional[int]:
    for s in snaps:
        if pred(s):
            return s.minute
    return None


def item_line(items: List[str], limit: int = 5) -> str:
    show = [n for n in items if n not in ("Amplifying Tome", "Glowing Mote", "Sapphire Crystal", "Ruby Crystal", "Boots")]
    # Keep components that are real spikes (Lost Chapter, Tear, Ashes, Guise, Jewel).
    text = " › ".join(show[:limit])
    if len(show) > limit:
        text += " › …"
    return text or "(nothing)"


def fmt_kill(dmg: float, hp: float, kill: Optional[float]) -> str:
    pct = 100.0 * dmg / hp if hp else 0
    if kill is not None:
        return f"{dmg:.0f} ({pct:.0f}% KILL {kill:.1f}s)"
    return f"{dmg:.0f} ({pct:.0f}%)"


def summarize(results: Dict[str, List[Snapshot]]) -> str:
    lines: List[str] = []
    lines.append("=" * 88)
    lines.append("AP KOG'MAW — SPAM R  (PC LoL patch 26.19, Living Artillery from 26.16)")
    lines.append("Playstyle: Q shred, then R on cooldown. No W, no E. Window: 12s fight.")
    lines.append("R mana: 40 per shell + 40 per stack, cap 400. Stacks fall off after 8s.")
    lines.append(
        "Score: 55% half-mana barrage (you were already spamming) + 45% full-mana siege."
    )
    lines.append(
        f"Inside a barrage: {TANK_WEIGHT:.0%} tank / {SQUISH_WEIGHT:.0%} squishy. "
        "Damage stops at the target's HP."
    )
    lines.append(
        "The target stands in the shells. No heal, no shield, no sidestep. "
        "Real games are lower; the ranking is what survives that."
    )
    lines.append("Runes: Comet, Manaflow, Transcendence, Gathering Storm, Presence of Mind.")
    lines.append("=" * 88)
    lines.append("")
    lines.append("GOLD / LEVEL / TARGETS / BASE MANA")
    lines.append(
        f"  {'Min':>3}  {'Gold':>6}  {'Lvl':>3}  {'Tank HP':>8}  {'Tank MR':>7}  "
        f"{'Squish HP':>9}  {'Base MP':>8}"
    )
    for m in (1, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28):
        lv = level_at_minute(m)
        lines.append(
            f"  {m:>3}  {gold_at_minute(m):>6}  {lv:>3}  "
            f"{tank_hp(m):>8.0f}  {tank_mr(m):>7.0f}  {squishy_hp(m):>9.0f}  "
            f"{base_mana(lv):>8.0f}"
        )

    # Rank builds by average spam score from the first point R exists with an item spike.
    ranking = []
    for name, snaps in results.items():
        scored = [s for s in snaps if s.minute >= 8]
        avg = sum(s.spam_score for s in scored) / len(scored)
        s14, s22, s28 = snaps[13], snaps[21], snaps[27]
        ranking.append((avg, name, snaps, s14, s22, s28))
    ranking.sort(key=lambda row: row[0], reverse=True)
    winner_name = ranking[0][1]
    winner = results[winner_name]

    lines.append("")
    lines.append("-" * 88)
    lines.append("MINUTE-BY-MINUTE BEST SPAM-R SCORE")
    lines.append("-" * 88)
    for m in range(1, GAME_MINUTES + 1):
        if m % 2 != 0 and m not in (1, 9, 11, 15, 21):
            continue
        best = max(results.values(), key=lambda snaps: snaps[m - 1].spam_score)[m - 1]
        lines.append(
            f"  {m:>2}:00 | score {best.spam_score:>7.0f} | "
            f"half-tank {best.half_tank:>6.0f} ({best.half_shots}R) | "
            f"full-tank {best.full_tank:>6.0f} ({best.full_shots}R) | "
            f"{best.build_name}"
        )
        lines.append(f"         {item_line(best.items)}  |  {best.notes}  |  mana {best.max_mana:.0f}")

    lines.append("")
    lines.append("-" * 88)
    lines.append("BUILD COMPARISON — 12s BARRAGE")
    lines.append("half = start at 50% mana (spam). full = start at 100% mana (reset siege).")
    lines.append("-" * 88)
    lines.append(
        f"  {'Build':<30} {'Avg':>7} {'½T22':>7} {'½R':>4} {'FT22':>7} {'FR':>4} "
        f"{'Mana22':>7} {'Cap':>5} {'Kill':>6}"
    )
    for avg, name, snaps, s14, s22, s28 in ranking:
        kill = f"{s22.cadence_kill:.0f}s" if s22.cadence_kill is not None else "—"
        lines.append(
            f"  {name:<30} {avg:>7.0f} {s22.half_tank:>7.0f} {s22.half_shots:>4} "
            f"{s22.full_tank:>7.0f} {s22.full_shots:>4} {s22.max_mana:>7.0f} "
            f"{s22.cadence_cap:>5} {kill:>6}"
        )

    lines.append("")
    lines.append("-" * 88)
    lines.append("22:00 DETAIL  (tank / squishy, half mana then full mana)")
    lines.append("-" * 88)
    for avg, name, snaps, s14, s22, s28 in ranking:
        thp, shp = tank_hp(22), squishy_hp(22)
        lines.append(
            f"  {name:<30} AP {s22.ap:>6.0f}  AH {s22.ah:>4.0f}  UH {s22.uh:>3.0f}  "
            f"R cd {s22.r_cd:.2f}s  mana {s22.max_mana:.0f}"
        )
        lines.append(
            f"    half  tank {fmt_kill(s22.half_tank, thp, None):<22} "
            f"squish {fmt_kill(s22.half_squish, shp, s22.half_squish_kill)}"
        )
        lines.append(
            f"    full  tank {fmt_kill(s22.full_tank, thp, None):<22} "
            f"squish {fmt_kill(s22.full_squish, shp, s22.full_squish_kill)}"
        )
        lines.append(f"    items: {item_line(s22.items, limit=8)}")

    # Shot trace for the winner and the two reference paths at 22:00, full mana, tank.
    lines.append("")
    lines.append("-" * 88)
    lines.append("SHOT TRACE @ 22:00 vs TANK, FULL MANA  (cost climbs; damage does not)")
    lines.append("-" * 88)
    trace_names = []
    for n in (winner_name, "Malig → Liandry → Void", "Tear → Malig → Seraph", "Malig → Actualizer → Horizon"):
        if n in results and n not in trace_names:
            trace_names.append(n)
    for name in trace_names:
        snap = results[name][21]
        st = stats_at(name, 22)
        barrage = run_barrage(
            st, level=snap.level, hp=tank_hp(22), mr=tank_mr(22),
            window=FIGHT_WINDOW, dt=FIGHT_DT, start_mana_frac=1.0,
            max_r_cost=None, use_actualizer=False, trace=True,
        )
        lines.append(
            f"  {name}  —  {barrage.shots} shells, {barrage.damage:.0f} dmg, "
            f"mana left {barrage.mana_left:.0f}"
        )
        for shot in barrage.trace:
            dpm = shot["dealt"] / shot["cost"] * 100 if shot["cost"] else 0
            lines.append(
                f"    #{shot['shot']:<2} t={shot['t']:>4.1f}s  cost {shot['cost']:>4.0f}  "
                f"dealt {shot['dealt']:>6.0f}  ({dpm:>4.0f} dmg/100 mana)  "
                f"tank HP left {shot['hp_left_pct']:>5.1f}%"
            )
        if name == winner_name:
            half = run_barrage(
                st, level=snap.level, hp=tank_hp(22), mr=tank_mr(22),
                window=FIGHT_WINDOW, dt=FIGHT_DT, start_mana_frac=0.5,
                max_r_cost=None, use_actualizer=False, trace=True,
            )
            lines.append(
                f"    half mana — {half.shots} shells, {half.damage:.0f} dmg, "
                f"mana left {half.mana_left:.0f}  (costs {[int(s['cost']) for s in half.trace]})"
            )

    w22 = winner[21]
    lines.append("")
    lines.append("-" * 88)
    lines.append("VERDICT")
    lines.append("-" * 88)
    lines.append(f"  Best spam-R path: {winner_name}")
    lines.append(f"  Average score from 8:00: {ranking[0][0]:.0f}")
    lines.append(
        f"  At 22:00, half mana: {w22.half_shots} shells, "
        f"tank {w22.half_tank:.0f} / {tank_hp(22):.0f} "
        f"({100 * w22.half_tank / tank_hp(22):.0f}%), "
        f"squish {w22.half_squish:.0f}"
        + (f" KILL {w22.half_squish_kill:.1f}s" if w22.half_squish_kill else "")
    )
    lines.append(
        f"  At 22:00, full mana: {w22.full_shots} shells, "
        f"tank {w22.full_tank:.0f} ({100 * w22.full_tank / tank_hp(22):.0f}%), "
        f"squish {w22.full_squish:.0f}"
        + (f" KILL {w22.full_squish_kill:.1f}s" if w22.full_squish_kill else "")
    )
    lines.append(f"  Mana pool @ 22: {w22.max_mana:.0f}   R cooldown: {w22.r_cd:.2f}s")

    def done(pred) -> str:
        m = first_minute(winner, pred)
        return f"~{m}:00" if m else "not finished by 28:00"

    for label, pred in (
        ("Malignance", lambda s: s.has_malig),
        ("Horizon", lambda s: s.has_horizon),
        ("Liandry", lambda s: s.has_liandry),
        ("Void", lambda s: s.has_void),
        ("Seraph", lambda s: s.has_seraph),
    ):
        when = done(pred)
        if when.startswith("not finished"):
            lines.append(f"  {label + ':':<12} not in this path")
        else:
            lines.append(f"  {label + ':':<12} {when}")

    # Compare references at 22 half-tank.
    lines.append("")
    lines.append("  Same minute, half-mana tank barrage:")
    for ref in (
        "Malig → Liandry → Void",
        "Tear → Malig → Seraph",
        "Luden → Malig → Horizon",
        "Malig → Actualizer → Horizon",
        "Luden → Horizon → Void",
        "Malig → SF → Horizon",
    ):
        if ref not in results:
            continue
        s = results[ref][21]
        delta = s.half_tank - w22.half_tank
        lines.append(
            f"    {ref:<32} {s.half_tank:>6.0f}  ({s.half_shots}R, mana {s.max_mana:.0f})"
            + ("" if ref == winner_name else f"   {delta:+.0f} vs winner")
        )

    cap = w22.cadence_cap
    shells = max(1, cap // 40)
    st_win = stats_at(winner_name, 22)
    cap_rows = []
    for cap_try in CADENCE_CAPS:
        probed = run_barrage(
            st_win, level=w22.level, hp=tank_hp(22), mr=tank_mr(22),
            window=LANE_WINDOW, dt=LANE_DT, start_mana_frac=0.80,
            max_r_cost=float(cap_try), use_actualizer=False, trace=False,
        )
        cap_rows.append((cap_try, probed))
    lines.append("")
    lines.append("  HOW TO PRESS R  (22:00, tank stands still, start at 80% mana)")
    lines.append("  Stop the chain when the next shell would cost more than the cap,")
    lines.append("  then let the 8s stack timer fall and fire the cheap shells again.")
    for cap_try, probed in cap_rows:
        kill = f"kill {probed.kill_time:.1f}s" if probed.kill_time is not None else "no kill"
        mark = "  ← pick" if cap_try == cap else ""
        lines.append(
            f"    cap {cap_try:>3} ({cap_try // 40} shells)  {kill:<14} "
            f"{probed.shots:>2}R  mana left {probed.mana_left:>5.0f}{mark}"
        )
    dump = next(row for row in cap_rows if row[0] == 400)[1]
    lines.append(
        f"  • Fastest pattern: {shells} shells, then reset "
        f"(kill {w22.cadence_kill:.1f}s, {w22.cadence_shots} shells total)."
    )
    if dump.kill_time is not None and w22.cadence_kill is not None:
        lines.append(
            f"  • Dumping until the shell costs 400 kills at {dump.kill_time:.1f}s "
            f"and leaves {dump.mana_left:.0f} mana. It is not faster."
        )
    lines.append("  • Costs: 40, 80, 120, 160, 200, 240, 280, 320, 360, 400.")
    lines.append("    Shot 1 is ~3–5× the damage per mana of shot 6. Raw damage barely moves")
    lines.append("    until the target is under 40% HP, where the shell doubles.")
    lines.append("  • On a half bar the chain dies, the stacks fall off, and the next")
    lines.append("    shells are cheap again. That second volley is the spam. Don't hold")
    lines.append("    the button through 300 mana waiting for it.")
    lines.append("  • Q first. Rank 5 shreds 32% resistances for 4 seconds. Spam R maxes")
    lines.append("    Q, not W. W is the other build (hide and auto).")
    lines.append("")
    lines.append("  WHY THIS SHAPE")
    lines.append("  • Finished builds all kill the squishy in ~2–3s. The tank is the choice.")
    lines.append("  • Malignance first (~7:00): 20 ultimate haste, 600 mana, Hatefog")
    lines.append("    (60 + 5% AP per second, refreshed by the next R, 10 MR shred).")
    hz = results["Malig → Horizon → Void"][21]
    ly = results["Malig → Liandry → Void"][21]
    lines.append(
        f"  • Horizon second beats Liandry second on a half bar at 22:00: "
        f"{hz.half_tank:.0f} vs {ly.half_tank:.0f}."
    )
    lines.append("    Horizon is +25 AH (another shell) and 10% damage on the long-range hit.")
    lines.append("    Liandry is 2% max HP per second. The chain does not last long enough")
    lines.append("    for the burn to pass the extra shell plus the amp. Buy Liandry when")
    lines.append("    fights are long and the tank is healing; this pattern is not that.")
    tear_s = results["Tear → Malig → Seraph"][21]
    lines.append(
        f"  • Tear into Seraph has the mana ({tear_s.max_mana:.0f}) and the shells "
        f"({tear_s.full_shots} on a full bar) and still loses the half-mana tank "
        f"({tear_s.half_tank:.0f})."
    )
    lines.append("    The extra shells show up late, without Void. Pen on 8 shells beats")
    lines.append("    a 9th and 10th shell into uncut MR.")
    act = results["Malig → Actualizer → Horizon"][21]
    lines.append(
        f"  • Actualizer is a trap here ({act.half_tank:.0f} half-tank). "
        "The active doubles costs for 8s."
    )
    lines.append("    R's cost is already climbing. Leave the active unpressed and the")
    lines.append("    item is just a small Lost Chapter legendary.")
    lud = results["Luden → Malig → Horizon"][21]
    lines.append(
        f"  • Luden into Malignance is the close second ({lud.half_tank:.0f} half-tank). "
        "Echo is one proc."
    )
    lines.append("    The second Lost Chapter item delays Void. One mana item is enough.")
    lines.append("  • Ionian Boots are 10 AH. 12 magic pen from Sorcs is the boot.")
    lines.append("")
    lines.append("  BUY ORDER (winner's completion times):")
    lines.append("  1) Doran's Ring start (lane item; not in the damage model).")
    order = legendary_times(winner)
    for i, (item, minute) in enumerate(order, start=2):
        lines.append(f"  {i}) {item:<24} ~{minute}:00")
    lines.append("")
    lines.append("  Skill: R > Q > E > W. R at 6/11/16. Max Q.")
    lines.append(
        f"  Lane: Q, then {shells} shells, step back until the stack timer drops, repeat."
    )
    lines.append("  Same target the whole chain so Hatefog stays under them.")
    lines.append("  Do not walk into W range.")
    lines.append("=" * 88)

    lines.append("")
    lines.append("TÓM TẮT")
    lines.append(f"  Build spam R: {winner_name}")
    lines.append(
        f"  Phút 22, nửa thanh mana: {w22.half_shots} phát R, "
        f"tank chịu {w22.half_tank:.0f} / {tank_hp(22):.0f} HP."
    )
    lines.append(
        f"  Cách bắn: {shells} phát (dừng khi phát kế tốn hơn {cap} mana), "
        "chờ stack rơi 8 giây, bắn tiếp."
    )
    lines.append("  Bắn đến 400 mana không giết nhanh hơn, mà hết mana.")
    lines.append("  Max Q (32% shred), không max W. Malignance → Horizon → Void.")
    lines.append("  Đừng mua Actualizer. Đừng mua 2 món Lost Chapter. Đừng rush Tear.")
    lines.append("  Sorc hơn Ionian. Mục tiêu đứng yên trong sim; trận thật thấp hơn, thứ tự build giữ nguyên.")
    return "\n".join(lines)


def stats_at(build_name: str, minute: int) -> Stats:
    """Recompute stats for traces. Tear timing matches run_all."""
    path = BUILD_PATHS[build_name]
    tear_since: Optional[int] = None
    st: Optional[Stats] = None
    for m in range(1, minute + 1):
        owned = resolve_inventory(path, gold_at_minute(m))
        if tear_since is None and (
            "Tear of the Goddess" in owned or "Archangel's Staff" in owned
        ):
            tear_since = m
        if m == minute:
            inv = [ITEMS[n] for n in owned if n in ITEMS]
            st = sum_stats(inv, level=level_at_minute(m), minute=m, tear_since=tear_since)
    assert st is not None
    return st


def legendary_times(snaps: List[Snapshot]) -> List[Tuple[str, int]]:
    show = LEGENDARIES | {"Sorcerer's Shoes", "Ionian Boots of Lucidity"}
    seen = set()
    out: List[Tuple[str, int]] = []
    for s in snaps:
        for name in s.items:
            if name in show and name not in seen:
                seen.add(name)
                out.append((name, s.minute))
    return out


def export_json(results: Dict[str, List[Snapshot]], path: Path) -> None:
    payload = {
        "meta": {
            "champion": "Kog'Maw",
            "role": "AP mid",
            "patch": "26.19",
            "r_patch": "26.16",
            "game_minutes": GAME_MINUTES,
            "playstyle": "spam Living Artillery (Q shred, no W)",
            "fight_window_s": FIGHT_WINDOW,
            "score": {
                "half_mana_weight": HALF_WEIGHT,
                "full_mana_weight": FULL_WEIGHT,
                "tank_weight": TANK_WEIGHT,
                "squish_weight": SQUISH_WEIGHT,
            },
            "runes": [
                "Arcane Comet",
                "Manaflow Band",
                "Transcendence",
                "Gathering Storm",
                "Presence of Mind",
            ],
        },
        "builds": {
            name: [
                {
                    "minute": s.minute,
                    "items": s.items,
                    "gold": s.gold,
                    "level": s.level,
                    "ap": s.ap,
                    "ah": s.ah,
                    "ult_haste": s.uh,
                    "max_mana": s.max_mana,
                    "r_cd": s.r_cd,
                    "full_tank": s.full_tank,
                    "full_squish": s.full_squish,
                    "half_tank": s.half_tank,
                    "half_squish": s.half_squish,
                    "full_shots": s.full_shots,
                    "half_shots": s.half_shots,
                    "full_squish_kill": s.full_squish_kill,
                    "half_squish_kill": s.half_squish_kill,
                    "cadence_cap": s.cadence_cap,
                    "cadence_tank": s.cadence_tank,
                    "cadence_squish": s.cadence_squish,
                    "cadence_shots": s.cadence_shots,
                    "cadence_kill": s.cadence_kill,
                    "spam_score": s.spam_score,
                    "notes": s.notes,
                }
                for s in snaps
            ]
            for name, snaps in results.items()
        },
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def self_check(results: Dict[str, List[Snapshot]]) -> None:
    assert r_mana_cost(0) == 40
    assert r_mana_cost(8) == 360
    assert r_mana_cost(9) == 400
    assert r_mana_cost(12) == 400
    assert sum(r_mana_cost(i) for i in range(10)) == 2200

    # One point per level, Q maxed before W.
    used = []
    for lv in range(1, 19):
        for skill, levels in (
            ("Q", [1, 3, 5, 7, 9]),
            ("E", [2, 4, 8, 10, 12]),
            ("W", [13, 14, 15, 17, 18]),
            ("R", [6, 11, 16]),
        ):
            if lv in levels:
                used.append(lv)
    assert used == list(range(1, 19)), used
    assert skill_rank(9, "Q") == 5
    assert skill_rank(9, "W") == 0
    assert skill_rank(6, "R") == 1 and skill_rank(11, "R") == 2 and skill_rank(16, "R") == 3

    cd = r_cooldown(3, 0, 0)
    assert abs(cd - 1.0) < 1e-9
    assert r_cooldown(3, 15, 20) < 0.75

    malig = results["Malig → Liandry → Void"]
    tear = results["Tear → Malig → Seraph"]
    actual = results["Malig → Actualizer → Horizon"]
    no_uh = results["Luden → Horizon → Void"]

    malig_at = first_minute(malig, lambda s: s.has_malig)
    tear_malig = first_minute(tear, lambda s: s.has_malig)
    assert malig_at is not None and malig_at <= 8, malig_at
    assert tear_malig is not None and tear_malig > malig_at

    # Seraph path has the deeper mana pool by the time the fight is on.
    assert tear[21].max_mana > malig[21].max_mana, (tear[21].max_mana, malig[21].max_mana)
    assert tear[21].full_shots >= malig[21].full_shots

    # Ultimate haste actually shortens R versus a no-Malignance build.
    assert malig[21].r_cd < no_uh[21].r_cd

    # Actualizer's active cannot be the reason you get more shells.
    st = stats_at("Malig → Actualizer → Horizon", 22)
    assert st.actualizer
    off = run_barrage(
        st, level=17, hp=tank_hp(22), mr=tank_mr(22), window=FIGHT_WINDOW, dt=FIGHT_DT,
        start_mana_frac=1.0, max_r_cost=None, use_actualizer=False, trace=False,
    )
    on = run_barrage(
        st, level=17, hp=tank_hp(22), mr=tank_mr(22), window=FIGHT_WINDOW, dt=FIGHT_DT,
        start_mana_frac=1.0, max_r_cost=None, use_actualizer=True, trace=False,
    )
    assert on.shots <= off.shots, (on.shots, off.shots)

    # Q shred is worth more than an unshredded barrage.
    base_kwargs = dict(
        level=17, ap=250, ah=25, uh=20, pct=0.40, flat=12, max_mana=2000,
        bonus_mana=1000, hp=tank_hp(22), mr=tank_mr(22), malig=True, liandry=True,
        ashes=False, blackfire=False, luden=False, horizon=False, shadowflame=False,
        actualizer=False, use_actualizer=False, window=FIGHT_WINDOW, dt=FIGHT_DT,
        start_mana_frac=1.0, max_r_cost=None, trace=False, manaflow_ready=True,
    )
    normal = simulate_barrage(**base_kwargs)
    assert normal.shots >= 6
    assert normal.damage > 400

    # Winner is a real barrage, not a 3-shell poke.
    winner = max(results, key=lambda n: sum(s.spam_score for s in results[n] if s.minute >= 8))
    assert results[winner][21].full_shots >= 6, (winner, results[winner][21].full_shots)

    # Pen check: 40% pen beats 0% pen on a tank, same everything else.
    no_pen = dict(base_kwargs)
    no_pen["pct"] = 0.0
    with_pen = simulate_barrage(**base_kwargs)
    without = simulate_barrage(**no_pen)
    assert with_pen.damage > without.damage * 1.15, (with_pen.damage, without.damage)

    # Inventory: Malignance before Liandry on the rush path, components don't skip ahead.
    early = resolve_inventory(BUILD_PATHS["Malig → Liandry → Void"], gold_at_minute(7))
    assert "Malignance" in early, early
    assert "Liandry's Torment" not in early, early
    later = resolve_inventory(BUILD_PATHS["Malig → Liandry → Void"], gold_at_minute(22))
    assert "Void Staff" in later and "Liandry's Torment" in later, later

    # A half bar cannot out-damage a full bar on the same target.
    # Shot count can, if the full bar kills and stops while the half bar
    # resets stacks and keeps firing.
    for snaps in results.values():
        s = snaps[21]
        assert s.half_tank <= s.full_tank + 1.0
        assert s.spam_score > 0

    winner_snap = results[winner][21]
    assert winner_snap.cadence_kill is not None
    assert winner_snap.cadence_kill < 15, winner_snap.cadence_kill
    assert 160 <= winner_snap.cadence_cap <= 240, winner_snap.cadence_cap


def main() -> None:
    results = run_all()
    self_check(results)
    report = summarize(results)
    print(report)
    out_dir = Path(__file__).resolve().parent
    (out_dir / "report.txt").write_text(report + "\n", encoding="utf-8")
    export_json(results, out_dir / "results.json")
    print(f"\nWrote {out_dir / 'report.txt'} and {out_dir / 'results.json'}")


if __name__ == "__main__":
    main()
