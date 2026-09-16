#!/usr/bin/env python3
"""
PC League of Legends — Ziggs mid, Q-spam
Patch snapshot ~26.18.

Playstyle: bounce Bouncing Bomb on cooldown from max range. No satchel
all-in, no minefield setup. Short Fuse only if they walk into auto range
(not the default).

Question:
  Is Dark Harvest worth it on Q-spam Ziggs, or do you just run Comet?
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import json

GAME_MINUTES = 28
WINDOW = 12.0

# Q-spam game mix: most bombs go on healthy targets. Harvest only pays
# once they're already chunked.
W_FULL = 0.45    # lane / first poke, ~100% HP
W_CHUNK = 0.35   # siege after prior poke, ~65% HP
W_EXEC = 0.20    # they're already in Harvest range, ~40% HP

HIT_SQUISH = 0.50
HIT_TANK = 0.58
COMET_LAND = 0.72  # 0.825s delay, they can step out
HORIZON_AMP = 0.10
CINDER = 1.20


# ---------------------------------------------------------------------------
# Economy / XP (mid farmer)
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
    """Q max, E second, W last. R at 6/11/16."""
    if skill == "R":
        if level < 6:
            return 0
        if level < 11:
            return 1
        if level < 16:
            return 2
        return 3
    q_levels = [1, 3, 5, 7, 9]
    e_levels = [2, 8, 10, 12, 13]
    w_levels = [4, 14, 15, 17, 18]
    return sum(1 for lv in {"Q": q_levels, "W": w_levels, "E": e_levels}[skill] if level >= lv)


def squishy_hp(m: int) -> float:
    lv = level_at_minute(m)
    return 640 + 104 * lv + 18 * m


def squishy_mr(m: int) -> float:
    lv = level_at_minute(m)
    extra = 0.0 if m < 14 else (12.0 if m < 22 else 25.0)
    return 30 + 1.3 * lv + extra


def tank_hp(m: int) -> float:
    lv = level_at_minute(m)
    return 700 + 110 * lv + 80 * max(0, m - 6)


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
    luden: bool = False
    blackfire: bool = False
    liandry: bool = False
    ashes: bool = False
    guise: bool = False
    horizon: bool = False
    storm: bool = False
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
    "Aether Wisp": Item("Aether Wisp", 900, ap=30),
    "Boots": Item("Boots", 300, tags=("boots",)),
    "Sorcerer's Shoes": Item(
        "Sorcerer's Shoes", 1100, flat_mpen=12, tags=("boots",)
    ),
    "Luden's Echo": Item(
        "Luden's Echo", 2750, ap=100, ah=10, mana=600, luden=True, tags=("mana",)
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
        "Liandry's Torment", 3000, ap=60, hp=300, liandry=True, tags=("burn",)
    ),
    "Horizon Focus": Item(
        "Horizon Focus", 2700, ap=75, ah=25, horizon=True, tags=("poke",)
    ),
    "Stormsurge": Item(
        "Stormsurge", 2800, ap=90, flat_mpen=15, storm=True, tags=("burst",)
    ),
    "Void Staff": Item("Void Staff", 3000, ap=95, pct_mpen=0.40, tags=("pen",)),
    "Shadowflame": Item(
        "Shadowflame", 3200, ap=110, flat_mpen=15, tags=("squishy",)
    ),
    "Rabadon's Deathcap": Item(
        "Rabadon's Deathcap", 3500, ap=130, deathcap=True, tags=("amp",)
    ),
}

UPGRADE_COMPONENTS = {
    "Sorcerer's Shoes": ("Boots",),
    "Luden's Echo": ("Lost Chapter", "Hextech Alternator"),
    "Blackfire Torch": ("Lost Chapter", "Fated Ashes"),
    "Liandry's Torment": ("Haunting Guise", "Fated Ashes"),
    "Horizon Focus": ("Fiendish Codex", "Fiendish Codex", "Amplifying Tome"),
    "Stormsurge": ("Hextech Alternator", "Aether Wisp"),
    "Void Staff": ("Blighting Jewel", "Blasting Wand"),
    "Shadowflame": ("Hextech Alternator", "Needlessly Large Rod"),
    "Rabadon's Deathcap": ("Needlessly Large Rod", "Needlessly Large Rod"),
}

NEXT_COMPONENTS = {
    "Sorcerer's Shoes": ["Boots"],
    "Luden's Echo": ["Lost Chapter", "Hextech Alternator"],
    "Blackfire Torch": ["Fated Ashes", "Lost Chapter"],
    "Liandry's Torment": ["Fated Ashes", "Haunting Guise"],
    "Horizon Focus": ["Fiendish Codex", "Amplifying Tome"],
    "Stormsurge": ["Hextech Alternator", "Aether Wisp"],
    "Void Staff": ["Blighting Jewel", "Blasting Wand"],
    "Shadowflame": ["Hextech Alternator", "Needlessly Large Rod"],
    "Rabadon's Deathcap": ["Needlessly Large Rod"],
}

BUILD_PATHS: Dict[str, List[str]] = {
    "Luden → SF → Cap": [
        "Lost Chapter",
        "Hextech Alternator",
        "Luden's Echo",
        "Boots",
        "Sorcerer's Shoes",
        "Shadowflame",
        "Rabadon's Deathcap",
        "Void Staff",
    ],
    "Luden → Horizon → Void": [
        "Lost Chapter",
        "Hextech Alternator",
        "Luden's Echo",
        "Boots",
        "Sorcerer's Shoes",
        "Fiendish Codex",
        "Fiendish Codex",
        "Horizon Focus",
        "Void Staff",
        "Rabadon's Deathcap",
    ],
    "Luden → Horizon → SF": [
        "Lost Chapter",
        "Hextech Alternator",
        "Luden's Echo",
        "Boots",
        "Sorcerer's Shoes",
        "Fiendish Codex",
        "Horizon Focus",
        "Shadowflame",
        "Rabadon's Deathcap",
    ],
    "BF → SF → Cap": [
        "Fated Ashes",
        "Lost Chapter",
        "Blackfire Torch",
        "Boots",
        "Sorcerer's Shoes",
        "Shadowflame",
        "Rabadon's Deathcap",
        "Void Staff",
    ],
    "Liandry → Horizon → Void": [
        "Fated Ashes",
        "Haunting Guise",
        "Liandry's Torment",
        "Boots",
        "Sorcerer's Shoes",
        "Fiendish Codex",
        "Horizon Focus",
        "Void Staff",
        "Rabadon's Deathcap",
    ],
    "Stormsurge → SF → Cap": [
        "Hextech Alternator",
        "Aether Wisp",
        "Stormsurge",
        "Boots",
        "Sorcerer's Shoes",
        "Shadowflame",
        "Rabadon's Deathcap",
        "Void Staff",
    ],
}

LEGENDARIES = {
    "Luden's Echo",
    "Blackfire Torch",
    "Liandry's Torment",
    "Horizon Focus",
    "Stormsurge",
    "Void Staff",
    "Shadowflame",
    "Rabadon's Deathcap",
}


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
        if item_name not in ("Sorcerer's Shoes", "Needlessly Large Rod", "Fiendish Codex"):
            if item_name in owned:
                return False
        if item_name == "Needlessly Large Rod" and owned.count(item_name) >= 2:
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
                if step in owned and step not in ("Needlessly Large Rod", "Fiendish Codex"):
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


def sum_stats(inv: List[Item]) -> dict:
    ap = ah = mana = flat = pct = 0.0
    flags = {
        "luden": False,
        "bf": False,
        "liandry": False,
        "ashes": False,
        "guise": False,
        "horizon": False,
        "storm": False,
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
        if it.horizon:
            flags["horizon"] = True
        if it.storm:
            flags["storm"] = True
        if it.deathcap:
            flags["cap"] = True
        if it.name == "Shadowflame":
            flags["sf"] = True
        if it.name == "Void Staff":
            flags["void"] = True
    ap += 18.0  # adaptive shards
    ah += 10.0  # Transcendence (Comet primary or DH + Sorcery second)
    ap_mult = 1.0
    if flags["bf"]:
        ap_mult += 0.04
    if flags["cap"]:
        ap_mult += 0.30
    ap *= ap_mult
    return {"ap": ap, "ah": ah, "mana": mana, "flat": flat, "pct": pct, "names": names, **flags}


# ---------------------------------------------------------------------------
# Combat
# ---------------------------------------------------------------------------


def haste_cdr_mult(haste: float) -> float:
    return 100.0 / (100.0 + max(0.0, haste))


def apply_pen(mr: float, pct: float, flat: float) -> float:
    return max(0.0, mr * (1.0 - pct) - flat)


def magic_mult(eff_mr: float) -> float:
    return 100.0 / (100.0 + eff_mr)


def q_cd(level: int, ah: float) -> float:
    r = max(1, skill_rank(level, "Q"))
    base = [6.0, 5.5, 5.0, 4.5, 4.0][r - 1]
    return base * haste_cdr_mult(ah) + 0.25


def q_throws(level: int, ah: float) -> int:
    cd = q_cd(level, ah)
    return min(6, 1 + int(max(0.0, WINDOW - 0.4) / max(0.5, cd)))


def q_raw(level: int, ap: float) -> float:
    r = skill_rank(level, "Q")
    if r <= 0:
        return 0.0
    base = [0, 80, 130, 180, 230, 280][r]
    ratio = [0, 0.60, 0.65, 0.70, 0.75, 0.80][r]
    return base + ratio * ap


def comet_raw(level: int, ap: float) -> float:
    # Long bounce ≈ 80% of the 0–100% travel amp.
    base = 15.0 + (100.0 - 15.0) * (level - 1) / 17.0
    return (base + 0.05 * ap) * 1.80


def comet_cd(level: int) -> float:
    return 20.0 + (6.59 - 20.0) * (level - 1) / 17.0


def scorch_raw(level: int) -> float:
    return 20.0 + 20.0 * (level - 1) / 17.0


def dh_souls(minute: int, snowball: bool) -> int:
    if snowball:
        return max(0, minute - 5)
    return max(0, (minute - 6) // 2)


def dh_raw(ap: float, souls: int) -> float:
    return 30.0 + 11.0 * souls + 0.05 * ap


def suffer_mult(stats: dict) -> float:
    if stats["liandry"] or stats["guise"]:
        return 1.06
    return 1.0


@dataclass
class WindowDmg:
    total: float
    q_hits_exp: float
    dh_exp: float
    comet_exp: float
    dh_proc_p: float


def window_damage(
    *,
    level: int,
    minute: int,
    stats: dict,
    hp: float,
    mr: float,
    start_frac: float,
    keystone: str,
    snowball: bool,
    vs_tank: bool,
) -> WindowDmg:
    """Expected magic damage of max-range Q spam.

    start_frac is the target's HP fraction at t=0.
    DH procs on the first *ability* hit while the target is below 50%
    (Short Fuse is proc damage and does not harvest).
    """
    ap = stats["ap"]
    n = q_throws(level, stats["ah"])
    p = HIT_TANK if vs_tank else HIT_SQUISH
    suffer = suffer_mult(stats)
    m = magic_mult(apply_pen(mr, stats["pct"], stats["flat"])) * suffer
    raw_q = q_raw(level, ap)
    souls = dh_souls(minute, snowball)
    dh = dh_raw(ap, souls)
    comet = comet_raw(level, ap)

    hp_left = hp * start_frac
    dmg = 0.0
    dh_exp = 0.0
    comet_exp = 0.0
    comet_ready_t = 0.0
    cd = q_cd(level, stats["ah"])
    horizon_up = False
    first_hit_done = False
    dh_proc_p = 0.0
    # One harvest per 35s. Snowball execute: takedown resets to 1s → second proc.
    dh_charges = 0.0
    if keystone == "harvest":
        dh_charges = 2.0 if (snowball and start_frac <= 0.50) else 1.0

    for i in range(n):
        t = i * cd
        frac = hp_left / hp
        cinder = CINDER if (stats["sf"] and frac <= 0.40) else 1.0
        hz = 1.0 + (HORIZON_AMP if (stats["horizon"] and horizon_up) else 0.0)
        q_hit = raw_q * m * cinder * hz

        echo = 0.0
        if stats["luden"] and not first_hit_done:
            echo = (105.0 + 0.07 * ap) * m * cinder * hz

        if keystone == "harvest" and frac <= 0.50 and dh_charges > 0:
            take = min(1.0, dh_charges)
            dmg += p * take * dh * m * cinder * hz
            dh_exp += p * take * dh * m * cinder * hz
            dh_proc_p += p * take
            dh_charges -= p * take

        if keystone == "comet" and t + 1e-6 >= comet_ready_t:
            c_hit = comet * m * hz * COMET_LAND
            dmg += p * c_hit
            comet_exp += p * c_hit
            comet_ready_t = t + comet_cd(level)

        # Scorch, both pages (DH often takes it as Sorcery second).
        if i == 0:
            dmg += p * scorch_raw(level) * m

        # Burns: 3s per landed Q, expected seconds this throw contributes.
        burn_s = p * min(3.0, cd)
        if stats["liandry"]:
            dmg += 0.02 * hp * burn_s * m * hz
        elif stats["ashes"] and not stats["bf"]:
            dmg += 5.0 * burn_s * m
        if stats["bf"]:
            dmg += (20.0 + 0.02 * ap) * burn_s * m * hz

        if stats["storm"] and (hp * start_frac - hp_left + p * q_hit) >= 0.25 * hp:
            # One squall if the window already dealt 25% max HP.
            pass  # applied once below

        # Expected HP drop (Q + echo only; DH already folded into dmg)
        dmg += p * (q_hit + echo)
        hp_left = max(1.0, hp_left - p * (q_hit + echo))
        if p > 0:
            first_hit_done = True
            if stats["horizon"]:
                horizon_up = True

    if stats["storm"]:
        dealt = hp * start_frac - hp_left
        if dealt >= 0.25 * hp:
            dmg += (1.0 - (1.0 - p) ** n) * (140.0 + 0.20 * ap) * m

    return WindowDmg(
        total=dmg,
        q_hits_exp=n * p,
        dh_exp=dh_exp,
        comet_exp=comet_exp,
        dh_proc_p=dh_proc_p if keystone == "harvest" else 0.0,
    )


@dataclass
class Snapshot:
    minute: int
    build_name: str
    keystone: str
    items: List[str]
    gold: int
    level: int
    ap: float
    ah: float
    throws: int
    souls: int
    full_s: float
    chunk_s: float
    exec_s: float
    mix_s: float
    mix_t: float
    dh_p_full: float
    dh_p_chunk: float
    dh_p_exec: float
    notes: str
    has_sf: bool
    has_horizon: bool
    has_luden: bool
    has_liandry: bool
    has_void: bool


def compute_snapshot(
    build_name: str, path: List[str], minute: int, keystone: str, snowball: bool
) -> Snapshot:
    gold = gold_at_minute(minute)
    level = level_at_minute(minute)
    inv = resolve_inventory(path, gold)
    st = sum_stats(inv)
    shp, smr = squishy_hp(minute), squishy_mr(minute)
    thp, tmr = tank_hp(minute), tank_mr(minute)

    def run(hp, mr, frac, tank=False) -> WindowDmg:
        return window_damage(
            level=level, minute=minute, stats=st, hp=hp, mr=mr,
            start_frac=frac, keystone=keystone, snowball=snowball, vs_tank=tank,
        )

    full = run(shp, smr, 1.00)
    chunk = run(shp, smr, 0.65)
    exe = run(shp, smr, 0.40)
    mix_s = W_FULL * full.total + W_CHUNK * chunk.total + W_EXEC * exe.total
    tank_full = run(thp, tmr, 1.00, tank=True)
    tank_chunk = run(thp, tmr, 0.65, tank=True)
    mix_t = 0.70 * tank_full.total + 0.30 * tank_chunk.total

    notes = []
    notes.append("DH" if keystone == "harvest" else "Comet")
    if snowball and keystone == "harvest":
        notes.append("snowball souls")
    if st["luden"]:
        notes.append("Echo")
    if st["horizon"]:
        notes.append("Hypershot")
    if st["sf"]:
        notes.append("Cinderbloom")
    if st["liandry"]:
        notes.append("%HP burn")
    if st["void"]:
        notes.append("%pen")
    if st["bf"]:
        notes.append("BF burn")

    return Snapshot(
        minute=minute,
        build_name=build_name,
        keystone=keystone,
        items=st["names"],
        gold=gold,
        level=level,
        ap=round(st["ap"], 1),
        ah=st["ah"],
        throws=q_throws(level, st["ah"]),
        souls=dh_souls(minute, snowball) if keystone == "harvest" else 0,
        full_s=round(full.total, 1),
        chunk_s=round(chunk.total, 1),
        exec_s=round(exe.total, 1),
        mix_s=round(mix_s, 1),
        mix_t=round(mix_t, 1),
        dh_p_full=round(full.dh_proc_p, 3),
        dh_p_chunk=round(chunk.dh_proc_p, 3),
        dh_p_exec=round(exe.dh_proc_p, 3),
        notes=", ".join(notes),
        has_sf=st["sf"],
        has_horizon=st["horizon"],
        has_luden=st["luden"],
        has_liandry=st["liandry"],
        has_void=st["void"],
    )


KEYSTONES = (
    ("Comet", "comet", False),
    ("DH", "harvest", False),
    ("DH snow", "harvest", True),
)


def run_all() -> Dict[str, List[Snapshot]]:
    results: Dict[str, List[Snapshot]] = {}
    for bname, path in BUILD_PATHS.items():
        for ks_label, ks, snow in KEYSTONES:
            key = f"{ks_label} | {bname}"
            results[key] = [
                compute_snapshot(bname, path, m, ks, snow)
                for m in range(1, GAME_MINUTES + 1)
            ]
    return results


def summarize(results: Dict[str, List[Snapshot]]) -> str:
    lines = []
    lines.append("=" * 80)
    lines.append("ZIGGS Q-SPAM — DARK HARVEST vs COMET  (PC LoL ~patch 26.18)")
    lines.append("Max-range Bouncing Bomb on CD | 12s window | mid gold")
    lines.append(
        f"Mix: {100 * W_FULL:.0f}% full-HP poke / {100 * W_CHUNK:.0f}% chunked (65%) / "
        f"{100 * W_EXEC:.0f}% execute (40%)"
    )
    lines.append("=" * 80)
    lines.append("")
    lines.append("GOLD / LEVEL / TARGET")
    lines.append(f"  {'Min':>3}  {'Gold':>6}  {'Lvl':>3}  {'Squish HP':>9}  {'Q throws':>8}")
    dummy_ah = 20.0
    for m in (1, 6, 8, 10, 12, 16, 20, 22, 28):
        lv = level_at_minute(m)
        lines.append(
            f"  {m:>3}  {gold_at_minute(m):>6}  {lv:>3}  {squishy_hp(m):>9.0f}  "
            f"{q_throws(lv, dummy_ah + (20 if m >= 8 else 0) + (25 if m >= 16 else 0)):>8}"
        )

    def mix_avg(snaps: List[Snapshot]) -> float:
        return sum(s.mix_s for s in snaps) / len(snaps)

    ranking = sorted(
        ((mix_avg(snaps), name, snaps) for name, snaps in results.items()),
        reverse=True,
    )

    lines.append("")
    lines.append("-" * 80)
    lines.append("BUILD × KEYSTONE — squish mix / 12s")
    lines.append("-" * 80)
    lines.append(
        f"  {'Page':<32} {'9mix':>6} {'16full':>7} {'16chk':>7} {'16ex':>6} "
        f"{'22mix':>6} {'22ex':>6} {'Eff':>6}"
    )
    for eff, name, snaps in ranking:
        s9, s16, s22 = snaps[8], snaps[15], snaps[21]
        lines.append(
            f"  {name:<32} {s9.mix_s:>6.0f} {s16.full_s:>7.0f} {s16.chunk_s:>7.0f} "
            f"{s16.exec_s:>6.0f} {s22.mix_s:>6.0f} {s22.exec_s:>6.0f} {eff:>6.0f}"
        )

    lines.append("")
    lines.append("-" * 80)
    lines.append("HARVEST PROCS  (expected harvests in the 12s window; 1.0 = one proc)")
    lines.append("-" * 80)
    lines.append(f"  {'Page':<32} {'16 full':>8} {'16 chunk':>9} {'16 exec':>8} {'souls22':>8}")
    for _, name, snaps in ranking:
        if snaps[0].keystone != "harvest":
            continue
        s16, s22 = snaps[15], snaps[21]
        lines.append(
            f"  {name:<32} {100 * s16.dh_p_full:>7.0f}% {100 * s16.dh_p_chunk:>8.0f}% "
            f"{100 * s16.dh_p_exec:>7.0f}% {s22.souls:>8}"
        )

    comet_luden = results["Comet | Luden → SF → Cap"]
    dh_luden = results["DH | Luden → SF → Cap"]
    dh_snow = results["DH snow | Luden → SF → Cap"]
    comet_hz = results["Comet | Luden → Horizon → Void"]
    dh_sf = results["DH | Luden → SF → Cap"]

    def pct(a: float, b: float) -> float:
        return 100.0 * (a / b - 1.0) if b else 0.0

    lines.append("")
    lines.append("-" * 80)
    lines.append("A/B — SAME ITEMS, COMET vs HARVEST  (Luden → Shadowflame → Cap)")
    lines.append("-" * 80)
    for m, i in ((9, 8), (16, 15), (22, 21)):
        c, d, s = comet_luden[i], dh_luden[i], dh_snow[i]
        lines.append(
            f"  {m}:00 mix   Comet {c.mix_s:.0f}  |  DH {d.mix_s:.0f} ({pct(d.mix_s, c.mix_s):+.0f}%)  "
            f"|  DH snow {s.mix_s:.0f} ({pct(s.mix_s, c.mix_s):+.0f}%)"
        )
        lines.append(
            f"         full  Comet {c.full_s:.0f}  |  DH {d.full_s:.0f} ({pct(d.full_s, c.full_s):+.0f}%)"
        )
        lines.append(
            f"         exec  Comet {c.exec_s:.0f}  |  DH {d.exec_s:.0f} ({pct(d.exec_s, c.exec_s):+.0f}%)  "
            f"souls {d.souls}/{s.souls}"
        )

    best_comet = max(
        ((mix_avg(v), k, v) for k, v in results.items() if k.startswith("Comet")),
        key=lambda x: x[0],
    )
    best_dh = max(
        ((mix_avg(v), k, v) for k, v in results.items() if k.startswith("DH |")),
        key=lambda x: x[0],
    )
    best_snow = max(
        ((mix_avg(v), k, v) for k, v in results.items() if k.startswith("DH snow")),
        key=lambda x: x[0],
    )

    c22, d22 = comet_luden[21], dh_luden[21]
    lines.append("")
    lines.append("-" * 80)
    lines.append("VERDICT")
    lines.append("-" * 80)
    lines.append(f"  Best Comet path:    {best_comet[1]}   (avg mix {best_comet[0]:.0f})")
    lines.append(f"  Best DH path:       {best_dh[1]}   (avg mix {best_dh[0]:.0f})")
    lines.append(f"  Best DH snowball:   {best_snow[1]}   (avg mix {best_snow[0]:.0f})")
    lines.append("")
    lines.append("  IS DARK HARVEST WORTH IT ON Q-SPAM ZIGGS?")
    lines.append("  No as the default. Yes only if you are already snowballing squishies.")
    lines.append("")
    lines.append("  WHY HARVEST LOSES THE SPAM PATTERN:")
    lines.append("  • Harvest needs the target below 50% HP, then 35s CD (1s on takedown).")
    lines.append("    Q-spam's job is chunking people who start the window at full HP.")
    lines.append(
        f"    At 16:00 a full-HP squishy: DH proc chance {100 * dh_luden[15].dh_p_full:.0f}% "
        f"— mean path never crosses 50% in 12s."
    )
    lines.append("  • Comet doesn't care about HP. Long bombs also travel far, so the")
    lines.append("    V26.09 distance amp is real on bounce-Q. It ticks every ~8–12s.")
    lines.append(
        f"    Same Luden+SF items @22 mix: Comet {c22.mix_s:.0f} vs DH {d22.mix_s:.0f} "
        f"({pct(d22.mix_s, c22.mix_s):+.0f}%)."
    )
    lines.append("  • Short Fuse is proc damage — it does NOT harvest. Stay at 1400 and")
    lines.append("    only the bomb itself can proc DH.")
    lines.append("  • Live data still locks Comet (Manaflow / Transcendence / Scorch).")
    lines.append("")
    lines.append("  WHEN HARVEST IS THE PAGE:")
    lines.append("  • Not on the first poke. Comet's long-travel bomb (V26.09 distance")
    lines.append("    amp) is a bigger proc than Harvest at average souls, and it repeats.")
    lines.append(
        f"    Execute @22 same items: Comet {c22.exec_s:.0f} vs DH {d22.exec_s:.0f} "
        f"({pct(d22.exec_s, c22.exec_s):+.0f}%)."
    )
    lines.append("  • Snowball + takedown reset (second harvest in the 12s window)")
    lines.append(
        f"    @22 mix: DH snow {dh_snow[21].mix_s:.0f} vs Comet {c22.mix_s:.0f} "
        f"({pct(dh_snow[21].mix_s, c22.mix_s):+.0f}%), souls {dh_snow[21].souls}."
    )
    lines.append("    That's a fed fight with a kill in the window — not Q-spam lane.")
    lines.append("  • Item for DH: Shadowflame (Cinderbloom <40%). Item for Comet poke:")
    lines.append("    Horizon (10% on every bomb after the first) or Liandry vs HP.")
    lines.append("")
    lines.append("  HOW TO PLAY Q-SPAM ZIGGS:")
    lines.append("  1) Runes: Arcane Comet, Manaflow, Transcendence, Scorch.")
    lines.append("     Precision: Presence of Mind + Cut Down / Coup de Grace.")
    lines.append("  2) Items: Luden's Echo → Sorcs → Shadowflame → Deathcap")
    lines.append("     (Horizon / Void if they stack HP/MR; Liandry vs tanks).")
    lines.append("  3) Max Q. Throw bounce bombs on CD from 1400. Don't walk up")
    lines.append("     for Short Fuse unless they already can't punish.")
    lines.append("  4) Take Dark Harvest only into 4+ squishies when you will get")
    lines.append("     takedown resets. Then rush Luden + Shadowflame and look for")
    lines.append("     the bomb that lands below 50%, not the one that starts the poke.")
    lines.append("=" * 80)
    return "\n".join(lines)


def export_json(results: Dict[str, List[Snapshot]], path: str) -> None:
    payload = {
        "meta": {
            "champion": "Ziggs",
            "role": "mid",
            "patch": "26.18",
            "playstyle": "max-range Q spam",
            "window_s": WINDOW,
            "mix": {"full": W_FULL, "chunked": W_CHUNK, "execute": W_EXEC},
        },
        "builds": {
            name: [
                {
                    "minute": s.minute,
                    "keystone": s.keystone,
                    "items": s.items,
                    "gold": s.gold,
                    "level": s.level,
                    "ap": s.ap,
                    "throws": s.throws,
                    "souls": s.souls,
                    "full_s": s.full_s,
                    "chunk_s": s.chunk_s,
                    "exec_s": s.exec_s,
                    "mix_s": s.mix_s,
                    "mix_t": s.mix_t,
                    "dh_p_full": s.dh_p_full,
                    "dh_p_chunk": s.dh_p_chunk,
                    "dh_p_exec": s.dh_p_exec,
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
    comet = results["Comet | Luden → SF → Cap"]
    dh = results["DH | Luden → SF → Cap"]
    snow = results["DH snow | Luden → SF → Cap"]
    # Default Q-spam: Comet beats average-soul DH on mix.
    assert comet[15].mix_s > dh[15].mix_s, (comet[15].mix_s, dh[15].mix_s)
    assert comet[21].mix_s > dh[21].mix_s
    # Full-HP poke: Harvest almost never procs.
    assert dh[15].dh_p_full < 0.35
    # Execute is where Harvest is allowed to live; it must beat full-HP DH.
    assert dh[21].exec_s > dh[21].full_s
    # Snowball DH is closer; must at least beat average DH.
    assert snow[21].mix_s >= dh[21].mix_s
    # Q throws exist.
    assert comet[21].throws >= 4


def main() -> None:
    results = run_all()
    self_check(results)
    report = summarize(results)
    print(report)
    out = "/workspace/ziggs-harvest-sim"
    with open(f"{out}/report.txt", "w", encoding="utf-8") as f:
        f.write(report + "\n")
    export_json(results, f"{out}/results.json")
    print(f"\nWrote {out}/report.txt and {out}/results.json")


if __name__ == "__main__":
    main()
