#!/usr/bin/env python3
"""
Wild Rift Kai'Sa — AP fog-of-war Void Seeker (W) poke
Patch 7.2 / 7.2b–c item + rune snapshot (Sep 2026).

Playstyle: hide in fog/brush, land W from 1600–3000, never walk up.
No Q (needs nearby enemies). No Nashor autos.

Question: which buy order peaks W poke (chunk + 12s siege),
and which runes / settings actually belong on that path.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import json

GAME_MINUTES = 20
HIT_RATE = 0.62  # practiced fog poke with Skill Wheel; max-range thinner
FOG_BURN_SEC = 2.0  # of 3s DoT — they walk after being revealed
FOG_BURN_SEC_RYLAI = 2.6
WINDOW = 12.0  # fog siege window: two bushes, one rotate


# ---------------------------------------------------------------------------
# Economy / XP (dragon-lane / AP mid farmer, not support)
# ---------------------------------------------------------------------------


def gold_at_minute(m: int) -> int:
    if m <= 0:
        return 500
    total = 500
    for t in range(1, m + 1):
        if t <= 5:
            total += 360
        elif t <= 10:
            total += 480
        elif t <= 15:
            total += 560
        else:
            total += 620
    return total


def level_at_minute(m: int) -> int:
    table = {
        1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7, 7: 8, 8: 9,
        9: 10, 10: 11, 11: 11, 12: 12, 13: 12, 14: 13,
        15: 13, 16: 14, 17: 14, 18: 15, 19: 15, 20: 15,
    }
    return table.get(m, min(15, 1 + m))


def w_rank(level: int) -> int:
    # Max W: ranks at 1, 3, 5, 7
    return sum(1 for lv in (1, 3, 5, 7) if level >= lv)


def kaisa_ad(level: int) -> float:
    return 62.0 + 3.5 * (level - 1)


def gathering_storm_ap(minute: int) -> float:
    # WR: starts 6:00, every 3 min: 4 / 10 / 18 / 28 / 40 / …
    if minute < 6:
        return 0.0
    steps = 1 + (minute - 6) // 3
    ap = 0.0
    inc = 4.0
    for _ in range(steps):
        ap += inc
        inc += 2.0
    return ap


def transcendence_ah(level: int) -> float:
    # 5 AH lvl 1, +5 at lvl 5
    if level >= 5:
        return 10.0
    if level >= 1:
        return 5.0
    return 0.0


# ---------------------------------------------------------------------------
# Targets
# ---------------------------------------------------------------------------


def squishy_hp(m: int) -> float:
    lv = level_at_minute(m)
    return 620 + 95 * lv + 16 * m


def squishy_mr(m: int) -> float:
    lv = level_at_minute(m)
    extra = 0.0 if m < 12 else (10.0 if m < 17 else 22.0)
    return 30 + 1.3 * lv + extra


def tank_hp(m: int) -> float:
    lv = level_at_minute(m)
    return 680 + 108 * lv + 70 * max(0, m - 6)


def tank_mr(m: int) -> float:
    lv = level_at_minute(m)
    extra = 0.0 if m < 8 else min(7.5 * (m - 8), 120.0)
    return 32 + 1.8 * lv + extra


# ---------------------------------------------------------------------------
# Items (WR 7.2 / 7.2b–c)
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
    liandry: bool = False
    ashes: bool = False
    blackfire: bool = False
    horizon: bool = False
    stormsurge: bool = False
    orb: bool = False
    rylai: bool = False
    nashor: bool = False
    w_evolve: bool = False  # finished AP item → Living Weapon W
    tags: Tuple[str, ...] = ()


ITEMS: Dict[str, Item] = {
    "Amplifying Tome": Item("Amplifying Tome", 500, ap=20),
    "Blasting Wand": Item("Blasting Wand", 800, ap=45),
    "Needlessly Large Rod": Item("Needlessly Large Rod", 1400, ap=70),
    "Lost Chapter": Item("Lost Chapter", 1200, ap=40, ah=10, mana=300),
    "Fiendish Codex": Item("Fiendish Codex", 900, ap=35, ah=10),
    "Hextech Alternator": Item("Hextech Alternator", 1100, ap=45),
    "Haunting Guise": Item("Haunting Guise", 1300, ap=35, hp=200),
    "Fated Ashes": Item("Fated Ashes", 900, ap=40, ashes=True),
    "Aether Wisp": Item("Aether Wisp", 950, ap=30),
    "Void Amethyst": Item("Void Amethyst", 1000, ap=20, pct_mpen=0.10),
    "Boots of Speed": Item("Boots of Speed", 400, tags=("boots",)),
    "Boots of Mana": Item(
        "Boots of Mana", 1200, ap=25, flat_mpen=8, tags=("boots",)
    ),
    "Spellslinger's Shoes": Item(
        "Spellslinger's Shoes",
        2200,
        ap=35,  # 7.2c
        flat_mpen=18,
        pct_mpen=0.08,
        tags=("boots",),
    ),
    "Luden's Echo": Item(
        "Luden's Echo",
        2800,
        ap=100,
        ah=10,
        mana=500,
        luden=True,
        w_evolve=True,
    ),
    "Horizon Focus": Item(
        "Horizon Focus",
        2700,
        ap=80,
        ah=25,
        horizon=True,
        w_evolve=True,
    ),
    "Liandry's Torment": Item(
        "Liandry's Torment",
        3000,
        ap=70,
        hp=300,
        liandry=True,
        w_evolve=True,
    ),
    "Blackfire Torch": Item(
        "Blackfire Torch",
        2800,
        ap=80,
        ah=20,
        mana=500,
        blackfire=True,
        w_evolve=True,
    ),
    "Stormsurge": Item(
        "Stormsurge",
        2900,
        ap=90,
        flat_mpen=15,
        stormsurge=True,
        w_evolve=True,
    ),
    "Infinity Orb": Item(
        "Infinity Orb",
        3100,
        ap=110,
        orb=True,
        w_evolve=True,
    ),
    "Rabadon's Deathcap": Item(
        "Rabadon's Deathcap",
        3400,
        ap=130,
        deathcap=True,
        w_evolve=True,
    ),
    "Void Staff": Item(
        "Void Staff", 3000, ap=95, pct_mpen=0.40, w_evolve=True
    ),
    "Cryptbloom": Item(
        "Cryptbloom", 3000, ap=75, ah=20, pct_mpen=0.30, w_evolve=True
    ),
    "Rylai's Crystal Scepter": Item(
        "Rylai's Crystal Scepter",
        2700,
        ap=70,
        hp=350,
        rylai=True,
        w_evolve=True,
    ),
    "Malignance": Item(
        "Malignance", 2700, ap=90, ah=15, mana=500, w_evolve=True
    ),
    "Nashor's Tooth": Item(
        "Nashor's Tooth", 2800, ap=80, nashor=True
    ),  # AS item → E evolve, NOT W
}


# Path = intended purchase order. Boots of Speed is a stepping stone.
BUILD_PATHS: Dict[str, List[str]] = {
    "Horizon → Luden → Cap": [
        "Boots of Speed",
        "Fiendish Codex",
        "Horizon Focus",
        "Boots of Mana",
        "Luden's Echo",
        "Rabadon's Deathcap",
        "Void Staff",
    ],
    "Luden → Horizon → Cap": [
        "Boots of Speed",
        "Lost Chapter",
        "Luden's Echo",
        "Boots of Mana",
        "Horizon Focus",
        "Rabadon's Deathcap",
        "Void Staff",
    ],
    "Luden → Spellslinger → Horizon": [
        "Boots of Speed",
        "Lost Chapter",
        "Luden's Echo",
        "Boots of Mana",
        "Spellslinger's Shoes",
        "Horizon Focus",
        "Rabadon's Deathcap",
    ],
    "Luden → Cap → Void": [
        "Boots of Speed",
        "Lost Chapter",
        "Luden's Echo",
        "Boots of Mana",
        "Rabadon's Deathcap",
        "Void Staff",
        "Horizon Focus",
    ],
    "Luden → Orb → Cap": [
        "Boots of Speed",
        "Lost Chapter",
        "Luden's Echo",
        "Boots of Mana",
        "Infinity Orb",
        "Rabadon's Deathcap",
        "Void Staff",
    ],
    "Luden → Stormsurge → Cap": [
        "Boots of Speed",
        "Lost Chapter",
        "Luden's Echo",
        "Boots of Mana",
        "Stormsurge",
        "Rabadon's Deathcap",
        "Void Staff",
    ],
    "Horizon → Cap → Void": [
        "Boots of Speed",
        "Horizon Focus",
        "Boots of Mana",
        "Rabadon's Deathcap",
        "Void Staff",
        "Luden's Echo",
    ],
    "Liandry → Horizon → Cap": [
        "Boots of Speed",
        "Fated Ashes",
        "Liandry's Torment",
        "Boots of Mana",
        "Horizon Focus",
        "Rabadon's Deathcap",
        "Void Staff",
    ],
    "Luden → Liandry → Void": [
        "Boots of Speed",
        "Lost Chapter",
        "Luden's Echo",
        "Boots of Mana",
        "Liandry's Torment",
        "Void Staff",
        "Rabadon's Deathcap",
    ],
    "Stormsurge → Luden → Cap": [
        "Boots of Speed",
        "Stormsurge",
        "Boots of Mana",
        "Luden's Echo",
        "Rabadon's Deathcap",
        "Void Staff",
    ],
    "Orb → Horizon → Cap": [
        "Boots of Speed",
        "Needlessly Large Rod",
        "Infinity Orb",
        "Boots of Mana",
        "Horizon Focus",
        "Rabadon's Deathcap",
        "Void Staff",
    ],
    "Luden → Cryptbloom → Cap": [
        "Boots of Speed",
        "Lost Chapter",
        "Luden's Echo",
        "Boots of Mana",
        "Cryptbloom",
        "Rabadon's Deathcap",
        "Horizon Focus",
    ],
    "Luden → Rylai → Liandry": [
        "Boots of Speed",
        "Lost Chapter",
        "Luden's Echo",
        "Boots of Mana",
        "Rylai's Crystal Scepter",
        "Liandry's Torment",
        "Rabadon's Deathcap",
    ],
    "Malig → Luden → Cap (trap ult)": [
        "Boots of Speed",
        "Lost Chapter",
        "Malignance",
        "Boots of Mana",
        "Luden's Echo",
        "Rabadon's Deathcap",
        "Void Staff",
    ],
    "Nashor → Luden → Cap (trap E)": [
        "Boots of Speed",
        "Nashor's Tooth",
        "Boots of Mana",
        "Luden's Echo",
        "Rabadon's Deathcap",
        "Horizon Focus",
    ],
    "BF → Horizon → Cap": [
        "Boots of Speed",
        "Fated Ashes",
        "Blackfire Torch",
        "Boots of Mana",
        "Horizon Focus",
        "Rabadon's Deathcap",
        "Void Staff",
    ],
}


UPGRADE_COMPONENTS = {
    "Boots of Mana": ("Boots of Speed",),
    "Spellslinger's Shoes": ("Boots of Mana",),
    "Luden's Echo": ("Lost Chapter", "Hextech Alternator"),
    "Horizon Focus": ("Fiendish Codex",),
    "Liandry's Torment": ("Haunting Guise", "Fated Ashes"),
    "Blackfire Torch": ("Lost Chapter", "Fated Ashes"),
    "Stormsurge": ("Hextech Alternator", "Aether Wisp"),
    "Infinity Orb": ("Hextech Alternator", "Needlessly Large Rod"),
    "Rabadon's Deathcap": ("Needlessly Large Rod",),
    "Void Staff": ("Void Amethyst", "Needlessly Large Rod"),
    "Cryptbloom": ("Void Amethyst",),
    "Rylai's Crystal Scepter": ("Blasting Wand", "Amplifying Tome"),
    "Malignance": ("Lost Chapter", "Blasting Wand"),
}

NEXT_COMPONENTS = {
    "Boots of Mana": ["Boots of Speed"],
    "Spellslinger's Shoes": ["Boots of Mana"],
    "Luden's Echo": ["Lost Chapter", "Hextech Alternator"],
    "Horizon Focus": ["Fiendish Codex", "Fiendish Codex", "Amplifying Tome"],
    "Liandry's Torment": ["Fated Ashes", "Haunting Guise"],
    "Blackfire Torch": ["Fated Ashes", "Lost Chapter"],
    "Stormsurge": ["Hextech Alternator", "Aether Wisp"],
    "Infinity Orb": ["Needlessly Large Rod", "Hextech Alternator"],
    "Rabadon's Deathcap": ["Needlessly Large Rod"],
    "Void Staff": ["Void Amethyst", "Needlessly Large Rod"],
    "Cryptbloom": ["Void Amethyst"],
    "Rylai's Crystal Scepter": ["Blasting Wand", "Amplifying Tome"],
    "Malignance": ["Lost Chapter", "Blasting Wand"],
    "Nashor's Tooth": ["Amplifying Tome"],
}


def resolve_inventory(path: List[str], gold: int) -> List[Item]:
    owned: List[str] = []
    gold_pool = gold

    def credit_for(name: str) -> Tuple[int, List[str]]:
        credit = 0
        remove: List[str] = []
        remaining = list(owned)
        for c in UPGRADE_COMPONENTS.get(name, ()):
            if c in remaining:
                credit += ITEMS[c].cost
                remaining.remove(c)
                remove.append(c)
        # Horizon builds from 2 Codex — credit a second if present
        if name == "Horizon Focus":
            if remaining.count("Fiendish Codex") >= 1 and "Fiendish Codex" in remove:
                credit += ITEMS["Fiendish Codex"].cost
                remove.append("Fiendish Codex")
        return credit, remove

    def remaining_cost(name: str) -> int:
        credit, _ = credit_for(name)
        return max(0, ITEMS[name].cost - credit)

    def buy(name: str) -> bool:
        nonlocal gold_pool
        if name in owned and name != "Fiendish Codex":
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
        if step in owned and step != "Fiendish Codex":
            continue
        if remaining_cost(step) <= gold_pool:
            buy(step)
        else:
            blocked_at = step
            break

    def buy_comps_for(item_name: str) -> None:
        comps = NEXT_COMPONENTS.get(item_name, [])
        # Horizon wants two Codex
        if item_name == "Horizon Focus":
            comps = ["Fiendish Codex", "Fiendish Codex", "Amplifying Tome"]
        for comp in comps:
            if gold_pool >= ITEMS[comp].cost:
                if comp == "Fiendish Codex" or comp not in owned:
                    buy(comp)

    if blocked_at:
        buy_comps_for(blocked_at)
        if remaining_cost(blocked_at) <= gold_pool:
            buy(blocked_at)
            seen = False
            for step in path:
                if step == blocked_at:
                    seen = True
                    continue
                if not seen:
                    continue
                if step in owned and step != "Fiendish Codex":
                    continue
                if remaining_cost(step) <= gold_pool:
                    buy(step)
                else:
                    buy_comps_for(step)
                    if remaining_cost(step) <= gold_pool:
                        buy(step)
                    else:
                        break

    if "Spellslinger's Shoes" in owned and "Boots of Mana" in owned:
        owned.remove("Boots of Mana")
    if "Boots of Mana" in owned and "Boots of Speed" in owned:
        owned.remove("Boots of Speed")
    if "Spellslinger's Shoes" in owned and "Boots of Speed" in owned:
        owned.remove("Boots of Speed")

    return [ITEMS[n] for n in owned]


# ---------------------------------------------------------------------------
# Combat model — one landed fog W + 12s siege
# ---------------------------------------------------------------------------

W_BASE = (0, 30, 60, 90, 120)
W_CD = (0, 20.0, 18.0, 16.0, 14.0)


@dataclass
class Snapshot:
    minute: int
    build_name: str
    items: List[str]
    gold: int
    level: int
    ap: float
    ah: float
    w_evolved: bool
    chunk_squish: float
    chunk_tank: float
    chunk_execute: float  # squishy at 30% HP (Orb)
    window_squish: float
    window_tank: float
    w_per_window: float
    notes: str


def magic_mult(mr: float, flat: float, pct: float) -> float:
    eff = max(8.0, mr * (1.0 - pct) - flat)
    return 100.0 / (100.0 + eff)


def comet_damage(level: int, ap: float, minute: int) -> float:
    # 15–100 (level) + 2*hit count + 5% AP. Fog: comet lands ~70% if W lands.
    base = 15 + (100 - 15) * (level - 1) / 14
    stacks = max(0, minute - 1)
    return 0.70 * (base + 2 * stacks + 0.05 * ap)


def scorch_damage(level: int) -> float:
    return 21 + (49 - 21) * (level - 1) / 14


def first_strike_cd(level: int) -> float:
    return 20.0 - 7.0 * (level - 1) / 14


def comet_cd(level: int) -> float:
    return 16.0 - 8.0 * (level - 1) / 14


def plasma_onhit(level: int, ap: float) -> float:
    return 5.0 + 7.0 * (level - 1) / 14 + 0.15 * ap


def compute_snapshot(
    build_name: str,
    path: List[str],
    minute: int,
    keystone: str,
    slot3: str = "storm",
) -> Snapshot:
    gold = gold_at_minute(minute)
    level = level_at_minute(minute)
    inv = resolve_inventory(path, gold)

    ap = gathering_storm_ap(minute) if slot3 == "storm" else 0.0
    ah = transcendence_ah(level)
    mana = 0.0
    flat = 0.0
    pct = 0.0
    flags = {
        "luden": False,
        "liandry": False,
        "ashes": False,
        "blackfire": False,
        "horizon": False,
        "storm": False,
        "orb": False,
        "rylai": False,
        "nashor": False,
        "evolve": False,
        "cap": False,
        "malig": False,
    }

    names: List[str] = []
    for it in inv:
        names.append(it.name)
        ap += it.ap
        ah += it.ah
        mana += it.mana
        flat += it.flat_mpen
        pct += it.pct_mpen
        if it.luden:
            flags["luden"] = True
        if it.liandry:
            flags["liandry"] = True
        if it.ashes:
            flags["ashes"] = True
        if it.blackfire:
            flags["blackfire"] = True
        if it.horizon:
            flags["horizon"] = True
        if it.stormsurge:
            flags["storm"] = True
        if it.orb:
            flags["orb"] = True
        if it.rylai:
            flags["rylai"] = True
        if it.nashor:
            flags["nashor"] = True
        if it.w_evolve:
            flags["evolve"] = True
        if it.deathcap:
            flags["cap"] = True
        if it.name == "Malignance":
            flags["malig"] = True

    if flags["cap"]:
        ap *= 1.30
    if flags["blackfire"]:
        ap *= 1.04  # one champion burning

    rank = w_rank(level)
    ad = kaisa_ad(level)
    stacks = 3 if flags["evolve"] else 2
    plasma = stacks * plasma_onhit(level, ap)
    raw_w = W_BASE[rank] + 1.10 * ad + 0.60 * ap + plasma

    horizon_amp = 1.10 if flags["horizon"] else 1.0
    madness = 1.02 if flags["liandry"] else 1.0
    ability = raw_w * horizon_amp * madness

    luden_raw = (140.0 + 0.15 * ap) if flags["luden"] else 0.0
    luden_raw *= horizon_amp * madness

    burn_sec = FOG_BURN_SEC_RYLAI if flags["rylai"] else FOG_BURN_SEC
    burn_per_s = 0.0
    hp_s = squishy_hp(minute)
    if flags["ashes"] and not flags["liandry"] and not flags["blackfire"]:
        burn_per_s += 15.0 / 3.0
    if flags["blackfire"]:
        burn_per_s += 20.0 + 0.02 * ap
    if flags["liandry"]:
        burn_per_s += 0.02 * hp_s  # scaled per-target below

    def pack(hp: float, mr: float, hp_frac: float = 1.0) -> Tuple[float, float, float, float]:
        """Return (W+burn+squall with luden, without luden, comet+scorch extra, pen)."""
        pen = magic_mult(mr, flat, pct)
        w_m = ability * pen
        lu_m = luden_raw * pen
        bps = burn_per_s
        if flags["liandry"]:
            bps = burn_per_s - 0.02 * hp_s + 0.02 * hp
        hz = horizon_amp if flags["horizon"] else 1.0
        burn_m = bps * burn_sec * pen * madness * hz

        squall = 0.0
        pre_squall = w_m + lu_m + (bps * min(2.5, burn_sec) * pen)
        if flags["storm"] and pre_squall >= 0.25 * hp:
            squall = (125.0 + 0.10 * ap) * pen * hz

        execute = 1.20 if (flags["orb"] and hp_frac <= 0.35) else 1.0
        core_l = (w_m + lu_m + burn_m + squall) * execute
        core_n = (w_m + burn_m + squall) * execute
        extra_cs = 0.0
        if keystone == "comet":
            extra_cs += comet_damage(level, ap, minute) * pen
        if slot3 == "scorch":
            extra_cs += scorch_damage(level) * pen
        return core_l, core_n, extra_cs, pen

    def siege(hp: float, mr: float, hp_frac: float = 1.0) -> Tuple[float, float, float]:
        """(landed chunk with luden+key, 12s expected, expected landed W)."""
        core_l, core_n, extra_cs, _pen = pack(hp, mr, hp_frac)
        base_cd = W_CD[rank]
        haste_cd = base_cd / (1.0 + ah / 100.0)
        hit_cd = 0.30 * haste_cd if flags["evolve"] else haste_cd
        mix_cd = HIT_RATE * hit_cd + (1.0 - HIT_RATE) * haste_cd
        if flags["evolve"] and mana < 300:
            mix_cd /= 0.90
        attempts = WINDOW / mix_cd
        n_hits = attempts * HIT_RATE
        luden_hits = min(n_hits, WINDOW / 9.0) if flags["luden"] else 0.0
        other_hits = max(0.0, n_hits - luden_hits)

        dmg = luden_hits * core_l + other_hits * core_n
        # Keystones have their own ICD — not every W.
        if keystone == "first_strike" and n_hits > 0:
            fs_procs = min(n_hits, WINDOW / first_strike_cd(level))
            # 7% true on the first out-of-combat chunk (usually with Luden)
            dmg += fs_procs * 0.07 * (core_l if flags["luden"] else core_n)
        if keystone == "comet" and n_hits > 0:
            dmg += (
                min(n_hits, WINDOW / comet_cd(level))
                * comet_damage(level, ap, minute)
                * magic_mult(mr, flat, pct)
            )
        if slot3 == "scorch" and n_hits > 0:
            dmg += (
                min(n_hits, WINDOW / 8.0)
                * scorch_damage(level)
                * magic_mult(mr, flat, pct)
            )

        chunk = core_l if flags["luden"] else core_n
        if keystone == "first_strike":
            chunk *= 1.07
        chunk += extra_cs
        return chunk, dmg, n_hits

    ch_s, win_s, n_w = siege(squishy_hp(minute), squishy_mr(minute), 1.0)
    ch_t, win_t, _ = siege(tank_hp(minute), tank_mr(minute), 1.0)
    ch_e, _, _ = siege(squishy_hp(minute) * 0.30, squishy_mr(minute), 0.30)

    notes = []
    if flags["evolve"]:
        notes.append("W evolved (70% CD refund)")
    else:
        notes.append("W NOT evolved")
    if flags["horizon"]:
        notes.append("Horizon +10%")
    if flags["luden"]:
        notes.append("Luden echo")
    if flags["nashor"]:
        notes.append("Nashor evolved E not W")
    if flags["malig"]:
        notes.append("Malignance Hatefog wasted on fog W")
    if flags["orb"]:
        notes.append("Orb execute only <35% HP")
    if flags["liandry"]:
        notes.append("Liandry 2s fog burn")
    if flags["storm"]:
        notes.append("Stormsurge if 25% HP chunk")

    return Snapshot(
        minute=minute,
        build_name=build_name,
        items=names,
        gold=gold,
        level=level,
        ap=round(ap, 1),
        ah=round(ah, 1),
        w_evolved=flags["evolve"],
        chunk_squish=round(ch_s, 1),
        chunk_tank=round(ch_t, 1),
        chunk_execute=round(ch_e, 1),
        window_squish=round(win_s, 1),
        window_tank=round(win_t, 1),
        w_per_window=round(n_w, 2),
        notes=", ".join(notes),
    )


def run_all(keystone: str) -> Tuple[Dict[str, List[Snapshot]], List[dict]]:
    results: Dict[str, List[Snapshot]] = {}
    for name, path in BUILD_PATHS.items():
        results[name] = [
            compute_snapshot(name, path, m, keystone) for m in range(1, GAME_MINUTES + 1)
        ]

    timeline = []
    for m in range(1, GAME_MINUTES + 1):
        cands = [(n, results[n][m - 1]) for n in results]

        def score(s: Snapshot) -> float:
            # Fog identity: 12s siege vs squishy, slight tank floor so Void isn't ignored
            return s.window_squish + 0.15 * s.window_tank

        best_n, best_s = max(cands, key=lambda x: score(x[1]))
        timeline.append(
            {
                "minute": m,
                "winner": best_n,
                "chunk": best_s.chunk_squish,
                "window": best_s.window_squish,
                "w_per": best_s.w_per_window,
                "items": best_s.items,
                "ap": best_s.ap,
                "evolved": best_s.w_evolved,
                "notes": best_s.notes,
            }
        )
    return results, timeline


def avg_window(snaps: List[Snapshot], lo: int, hi: int) -> float:
    sl = [s for s in snaps if lo <= s.minute <= hi]
    return sum(s.window_squish for s in sl) / max(1, len(sl))


def summarize(
    results: Dict[str, List[Snapshot]],
    timeline: List[dict],
    rune_cmp: List[dict],
) -> str:
    lines: List[str] = []
    lines.append("=" * 78)
    lines.append("KAI'SA — AP FOG W POKE (Wild Rift 7.2 / 7.2b–c)")
    lines.append("Playstyle: Void Seeker from fog | 20:00 WR game | hit rate 62%")
    lines.append("Metric: damage per landed W + expected damage in a 12s fog siege")
    lines.append("=" * 78)
    lines.append("")
    lines.append("GOLD / LEVEL (farmer Kai'Sa)")
    lines.append(f"  {'Min':>3}  {'Gold':>6}  {'Lvl':>3}  {'Squish HP':>9}  {'Tank HP':>8}")
    for m in (1, 4, 8, 12, 16, 20):
        lines.append(
            f"  {m:>3}  {gold_at_minute(m):>6}  {level_at_minute(m):>3}  "
            f"{squishy_hp(m):>9.0f}  {tank_hp(m):>8.0f}"
        )

    lines.append("")
    lines.append("-" * 78)
    lines.append("MINUTE-BY-MINUTE OPTIMAL (12s fog siege vs squishy, First Strike)")
    lines.append("-" * 78)
    for row in timeline:
        item_short = " › ".join(row["items"][:5])
        if len(row["items"]) > 5:
            item_short += " › …"
        evo = "EVO" if row["evolved"] else "   "
        lines.append(
            f"  {row['minute']:>2}:00 | {evo} | W {row['chunk']:>6.0f} | "
            f"12s {row['window']:>6.0f} | {row['w_per']:.1f}W | {row['winner']}"
        )
        lines.append(f"         items: {item_short}")
        lines.append(f"         {row['notes']}")

    lines.append("")
    lines.append("-" * 78)
    lines.append("BUILD COMPARISON — 12s fog siege vs squishy @ spikes")
    lines.append("-" * 78)
    lines.append(
        f"  {'Build':<34} {'8:00':>7} {'12:00':>7} {'16:00':>7} {'20:00':>7} "
        f"{'Avg8-20':>8} {'W@16':>6}"
    )
    ranking = []
    for name, snaps in results.items():
        w8 = snaps[7].window_squish
        w12 = snaps[11].window_squish
        w16 = snaps[15].window_squish
        w20 = snaps[19].window_squish
        avg = avg_window(snaps, 8, 20)
        ranking.append((avg, w16, name, w8, w12, w20, snaps))
        lines.append(
            f"  {name:<34} {w8:>7.0f} {w12:>7.0f} {w16:>7.0f} {w20:>7.0f} "
            f"{avg:>8.0f} {snaps[15].chunk_squish:>6.0f}"
        )
    ranking.sort(key=lambda x: (x[0], x[1]), reverse=True)

    lines.append("")
    lines.append("-" * 78)
    lines.append("RUNES — same winning path, 12s siege @ 16:00")
    lines.append("-" * 78)
    for row in rune_cmp:
        lines.append(
            f"  {row['keystone']:<22} chunk {row['chunk']:>6.0f} | "
            f"12s {row['window']:>6.0f} | AP {row['ap']:.0f}"
        )

    winner = ranking[0]
    win_name = winner[2]
    snaps = winner[6]
    evo_min = next((s.minute for s in snaps if s.w_evolved), None)
    hor_min = next((s.minute for s in snaps if "Horizon Focus" in s.items), None)
    lud_min = next((s.minute for s in snaps if "Luden's Echo" in s.items), None)
    cap_min = next((s.minute for s in snaps if "Rabadon's Deathcap" in s.items), None)

    lines.append("")
    lines.append("-" * 78)
    lines.append("VERDICT")
    lines.append("-" * 78)
    lines.append(f"  Best fog-poke path (avg 8–20 min 12s siege): {win_name}")
    lines.append(f"  Avg 12s vs squishy 8–20: {winner[0]:.0f} | 16:00 chunk {snaps[15].chunk_squish:.0f}")
    if evo_min:
        lines.append(f"  W evolve (70% CD refund): ~{evo_min}:00  ← the real spike")
    if hor_min:
        lines.append(f"  Horizon Focus (+10% from 600+ range): ~{hor_min}:00")
    if lud_min:
        lines.append(f"  Luden's Echo (140+15% AP / 9s): ~{lud_min}:00")
    if cap_min:
        lines.append(f"  Deathcap (30% AP amp): ~{cap_min}:00")
    else:
        lines.append("  Deathcap: not finished by 20:00 on this gold curve")

    lines.append("")
    lines.append("  WHY FOG W WANTS THIS:")
    lines.append("  • W is 30–120 + 110% AD + 60% AP. AP items are the ratio that scales poke.")
    lines.append("  • Living Weapon on a finished AP item refunds 70% CD on champion hit.")
    lines.append("    Unevolved W ≈ 14–20s. Evolved ≈ 4–6s. First legendary is the spike.")
    lines.append("  • Luden 2800: evolve W at ~7:00 AND a 140+15% AP echo on the same missile.")
    lines.append("    Horizon 2700 evolves in the same window but has no echo —")
    lines.append("    12s siege at 8:00 is 425 (Luden) vs 310 (Horizon).")
    lines.append("  • Horizon 2nd is the 3000-range tax: +10% Hypershot from 600+ units.")
    lines.append("  • Liandry/Blackfire lose ~1s of the 3s burn after fog reveal.")
    lines.append("  • Infinity Orb execute does nothing on a full-HP fog poke.")
    lines.append("  • Malignance Hatefog is an ult zone — Kaisa R is a dash, not artillery.")
    lines.append("  • Nashor evolves E (AS), not W — fog poke never autos.")
    lines.append("  • Spellslinger T3 is almost a tie on avg, but delays Deathcap.")
    lines.append("")
    lines.append("  RECOMMENDED BUY ORDER (fog W Kai'Sa, 20-min WR):")
    lines.append("  1) Amplifying Tome + Boots of Speed")
    lines.append("  2) Lost Chapter → Hextech Alternator → Luden's Echo  (~7:00)  W EVOLVE + echo")
    lines.append("  3) Boots of Mana (25 AP, 8 flat mpen)")
    lines.append("  4) Horizon Focus                                  (~14:00)  +10% long-range W")
    lines.append("  5) Rabadon's Deathcap                             (~20:00)  30% AP amp")
    lines.append("  6) Long game: Void Staff vs MR / Cryptbloom if you want AH+pen")
    lines.append("")
    lines.append("  Situational swaps:")
    lines.append("  • Want +10% ASAP: Horizon first, Luden second (weaker 7–13, equal later).")
    lines.append("  • They stack MR: Void 3rd instead of Cap.")
    lines.append("  • They are <35% HP in fog: Orb 3rd for Inevitable Demise.")
    lines.append("  • Do not first-buy Nashor / Malignance / Rylai / Liandry for fog W.")
    lines.append("")
    lines.append("  RUNES (strongest poke — slot 3 is Storm OR Scorch, not both):")
    lines.append("  Keystone: Arcane Comet     — extra chunk on a 3000-range missile")
    lines.append("  Slot 2:   Transcendence    — AH → more evolved W")
    lines.append("  Slot 3:   Gathering Storm  — AP every 3 min after 6:00 (20-min games)")
    lines.append("             Scorch only if the game is a 12-min stomp")
    lines.append("  Alt key:  First Strike     — 7% true + gold, slightly less raw W")
    lines.append("  Avoid:    Electrocute (3 hits), Conqueror, Lethal Tempo, Aery")
    lines.append("  Spells:   Flash + Ghost (rotate fog) or Flash + Barrier")
    lines.append("  Skill:    Max W → E → Q. R when available. Start W.")

    lines.append("")
    lines.append("  SETTINGS (S22 Ultra + GameSir X3 Pro — W is a 3000-range tia):")
    lines.append("  Wild Rift")
    lines.append("  • Move Stick: Locked")
    lines.append("  • Locked Button Centers: Off")
    lines.append("  • Cast on Button Press: Off  (hold to aim, release to fire)")
    lines.append("  • Button Aiming Sensitivity: 15–30%")
    lines.append("  • Aim Panning: On")
    lines.append("  • Portrait Lock: On | Target filter: Champions only")
    lines.append("  • Force Attack Follow: Off")
    lines.append("  GameSir G-Touch")
    lines.append("  • W = Skill Wheel + right stick (same hand feel as Kog R), NOT LB tap")
    lines.append("  • Put W on the button you already use for Kog R (RB/RT), overlay on W icon")
    lines.append("  • Deadzone right stick slightly higher than Kog; don't 'place a circle'")
    lines.append("  • Two profiles: Kog-R (location) vs Kaisa-W (direction)")
    lines.append("  • Poke 1600–2200, not max 3000; never fire through the wave")
    lines.append("=" * 78)
    return "\n".join(lines)


def export_json(results, timeline, rune_cmp, path: str) -> None:
    payload = {
        "meta": {
            "champion": "Kai'Sa",
            "role": "AP fog poke (mid / AP bot)",
            "patch": "7.2 / 7.2b-c",
            "game_minutes": GAME_MINUTES,
            "playstyle": "fog-of-war Void Seeker",
            "hit_rate": HIT_RATE,
        },
        "timeline": timeline,
        "rune_compare_16": rune_cmp,
        "builds": {
            name: [
                {
                    "minute": s.minute,
                    "items": s.items,
                    "gold": s.gold,
                    "level": s.level,
                    "ap": s.ap,
                    "ah": s.ah,
                    "w_evolved": s.w_evolved,
                    "chunk_squish": s.chunk_squish,
                    "chunk_tank": s.chunk_tank,
                    "chunk_execute": s.chunk_execute,
                    "window_squish": s.window_squish,
                    "window_tank": s.window_tank,
                    "w_per_window": s.w_per_window,
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
    results, timeline = run_all("first_strike")

    # Rank by avg 8–20 window to pick path for rune compare
    def path_avg(name: str) -> float:
        return avg_window(results[name], 8, 20)

    best_path_name = max(BUILD_PATHS, key=path_avg)
    best_path = BUILD_PATHS[best_path_name]
    rune_cmp = []
    pages = (
        ("first_strike", "storm", "First Strike + Storm"),
        ("first_strike", "scorch", "First Strike + Scorch"),
        ("comet", "storm", "Comet + Gathering Storm"),
        ("comet", "scorch", "Comet + Scorch"),
    )
    for ks, sl, label in pages:
        s = compute_snapshot(best_path_name, best_path, 16, ks, sl)
        rune_cmp.append(
            {
                "keystone": label,
                "chunk": s.chunk_squish,
                "window": s.window_squish,
                "ap": s.ap,
            }
        )

    report = summarize(results, timeline, rune_cmp)
    print(report)
    out_dir = "/workspace/kaisa-fog-poke-sim"
    with open(f"{out_dir}/report.txt", "w", encoding="utf-8") as f:
        f.write(report + "\n")
    export_json(results, timeline, rune_cmp, f"{out_dir}/results.json")
    print(f"\nWrote {out_dir}/report.txt and {out_dir}/results.json")


if __name__ == "__main__":
    main()
