#!/usr/bin/env python3
"""
Wild Rift 7.3 — Kai'Sa on-hit full build (pad / MB03).

Question: Kraken vs BotRK vs Statikk first, then which 6-slot on-hit
page to actually play. Evolve is on completing a legendary (not PC
stat thresholds). Magnetic Blaster is gone; Statikk is the 7.3 on-hit
energized rewrite. Nashor's Talon (component) is removed; WRF 7.3
still lists Nashor's Tooth 4th.

Numbers: patch 7.3 notes (Kaisa / Kraken / Rageblade / Terminus /
BotRK / Statikk / LT), WRF 7.3 Kaisa page, wr-7.3-db item dump.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import json
import os

PATCH = "7.3"
AS_CAP = 3.0
FIGHT_SECONDS = 8.0
MINUTES = (8, 12, 16, 20, 24)

# ---------------------------------------------------------------------------
# Economy / XP (dragon-lane farmer — same curve as support-73 adc_gold)
# ---------------------------------------------------------------------------


def gold_at_minute(m: int) -> int:
    if m <= 0:
        return 500
    total = 500
    for t in range(1, m + 1):
        if t <= 4:
            total += 380
        elif t <= 10:
            total += 620
        elif t <= 20:
            total += 740
        else:
            total += 800
    return total


def level_at_minute(m: int) -> int:
    table = {
        1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7, 7: 8, 8: 9,
        9: 10, 10: 10, 11: 11, 12: 12, 13: 12, 14: 13,
        15: 13, 16: 14, 17: 14, 18: 15, 19: 15, 20: 15,
        21: 15, 22: 15, 23: 15, 24: 15,
    }
    return table.get(m, min(15, 1 + m))


def skill_rank(level: int, skill: str) -> int:
    """Q > E > W. R at 5 / 9 / 13. Four ranks on basics."""
    if skill == "R":
        return (1 if level >= 5 else 0) + (1 if level >= 9 else 0) + (1 if level >= 13 else 0)
    mapping = {
        "Q": [1, 3, 6, 7],
        "E": [2, 8, 10, 11],
        "W": [4, 12, 14, 15],
    }
    return sum(1 for lv in mapping[skill] if level >= lv)


def lerp(lo: float, hi: float, level: int) -> float:
    t = (level - 1) / 14.0
    return lo + (hi - lo) * t


# ---------------------------------------------------------------------------
# Items (7.3). Tooth/Zhonya are not in the marksman dump — wiki / WRF.
# ---------------------------------------------------------------------------

ITEMS: Dict[str, Dict] = {
    "long_sword": {
        "name": "Long Sword", "cost": 500, "tier": "start",
        "stats": {"ad": 12},
    },
    "berserkers_greaves": {
        "name": "Berserker's Greaves", "cost": 1200, "tier": "boots",
        "stats": {"ad": 10, "as": 0.35},
    },
    "kraken_slayer": {
        "name": "Kraken Slayer", "cost": 2900, "tier": "legendary",
        "stats": {"ad": 45, "as": 0.35},
        "credits": ["long_sword"],
    },
    "blade_of_the_ruined_king": {
        "name": "Blade of the Ruined King", "cost": 3100, "tier": "legendary",
        "stats": {"ad": 40, "as": 0.30, "lifesteal": 0.12},
    },
    "statikk_shiv": {
        "name": "Statikk Shiv", "cost": 3000, "tier": "legendary",
        "stats": {"ad": 40, "ap": 40, "as": 0.30},
    },
    "guinsoos_rageblade": {
        "name": "Guinsoo's Rageblade", "cost": 3000, "tier": "legendary",
        "stats": {"ad": 35, "ap": 30},
    },
    "terminus": {
        "name": "Terminus", "cost": 3000, "tier": "legendary",
        "stats": {"ad": 35, "as": 0.35},
    },
    "nashors_tooth": {
        "name": "Nashor's Tooth", "cost": 2800, "tier": "legendary",
        "stats": {"as": 0.45, "ah": 20},
        "adaptive": True,  # Magic Fang: 25 AD or 50 AP
        "notes": "Talon component removed in 7.3; Tooth still on WRF Kaisa.",
    },
    "zhonyas_hourglass": {
        "name": "Zhonya's Hourglass", "cost": 3300, "tier": "legendary",
        "stats": {"ap": 110, "armor": 40},
    },
    "wits_end": {
        "name": "Wit's End", "cost": 2800, "tier": "legendary",
        "stats": {"as": 0.50, "mr": 40},
    },
    "runaans_hurricane": {
        "name": "Runaan's Hurricane", "cost": 2650, "tier": "legendary",
        "stats": {"as": 0.40, "crit": 0.25},
    },
}


def item_name(iid: str) -> str:
    return ITEMS[iid]["name"]


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PATHS: Dict[str, List[str]] = {
    # WRF 7.3 A-tier on-hit (default)
    "kraken": [
        "long_sword", "berserkers_greaves", "kraken_slayer",
        "guinsoos_rageblade", "terminus", "nashors_tooth", "zhonyas_hourglass",
    ],
    # 7.3 Statikk rewrite — AoE on-hit / plasma
    "statikk": [
        "long_sword", "berserkers_greaves", "statikk_shiv",
        "guinsoos_rageblade", "terminus", "nashors_tooth", "zhonyas_hourglass",
    ],
    # BotRK first vs tanks (lifesteal 12%)
    "botrk": [
        "long_sword", "berserkers_greaves", "blade_of_the_ruined_king",
        "guinsoos_rageblade", "terminus", "kraken_slayer", "wits_end",
    ],
    # Same core, 4th BotRK instead of Nashor (DPS check)
    "kraken_bork4": [
        "long_sword", "berserkers_greaves", "kraken_slayer",
        "guinsoos_rageblade", "terminus", "blade_of_the_ruined_king", "wits_end",
    ],
}

PATH_LABEL = {
    "kraken": "Kraken → Rage → Terminus → Nashor → Zhonya",
    "statikk": "Statikk → Rage → Terminus → Nashor → Zhonya",
    "botrk": "BotRK → Rage → Terminus → Kraken → Wit's End",
    "kraken_bork4": "Kraken → Rage → Terminus → BotRK → Wit's End",
}

DEFAULT_PATH = "kraken"


# ---------------------------------------------------------------------------
# Targets
# ---------------------------------------------------------------------------

@dataclass
class Target:
    name: str
    hp: float
    armor: float
    mr: float


def squishy(m: int) -> Target:
    lv = level_at_minute(m)
    hp = 580 + 95 * lv + 28 * m
    armor = 32 + 4.2 * lv + 3.5 * m
    mr = 30 + 1.4 * lv + 1.5 * m
    if m >= 12:
        armor += 25
    return Target("squishy", hp, armor, mr)


def tank(m: int) -> Target:
    lv = level_at_minute(m)
    hp = 720 + 125 * lv + 90 * m
    armor = 42 + 5.0 * lv + 14 * m
    mr = 32 + 2.0 * lv + 9 * m
    return Target("tank", hp, armor, mr)


def phys_mult(armor: float, pct_pen: float) -> float:
    a = max(0.0, armor * (1.0 - pct_pen))
    return 100.0 / (100.0 + a)


def mag_mult(mr: float, pct_pen: float) -> float:
    m = max(0.0, mr * (1.0 - pct_pen))
    return 100.0 / (100.0 + m)


# ---------------------------------------------------------------------------
# Inventory
# ---------------------------------------------------------------------------


def owned_at_gold(path: List[str], gold: int) -> List[str]:
    owned: List[str] = []
    spent = 0
    for iid in path:
        it = ITEMS[iid]
        cost = int(it["cost"])
        for cred in it.get("credits", []):
            if cred in owned:
                spent -= int(ITEMS[cred]["cost"])
                owned.remove(cred)
                break
        if "boots" in iid:
            for prev in list(owned):
                if "boots" in prev:
                    spent -= int(ITEMS[prev]["cost"])
                    owned.remove(prev)
                    break
        if spent + cost <= gold:
            spent += cost
            owned.append(iid)
        else:
            break
    return owned


def legendaries(owned: List[str]) -> List[str]:
    return [i for i in owned if ITEMS[i]["tier"] == "legendary"]


def evolves(owned: List[str]) -> Dict[str, bool]:
    n = len(legendaries(owned))
    return {"Q": n >= 1, "E": n >= 2, "W": n >= 3}


@dataclass
class Stats:
    ad: float = 0.0
    ap: float = 0.0
    bonus_as: float = 0.0
    lifesteal: float = 0.0
    items: List[str] = field(default_factory=list)


def aggregate(owned: List[str]) -> Stats:
    st = Stats(items=list(owned))
    nashor = False
    for iid in owned:
        s = ITEMS[iid]["stats"]
        st.ad += s.get("ad", 0.0)
        st.ap += s.get("ap", 0.0)
        st.bonus_as += s.get("as", 0.0)
        st.lifesteal += s.get("lifesteal", 0.0)
        if iid == "nashors_tooth":
            nashor = True
    if nashor:
        if st.ap >= st.ad:
            st.ap += 50.0
        else:
            st.ad += 25.0
    return st


# ---------------------------------------------------------------------------
# Kai'Sa kit
# ---------------------------------------------------------------------------

BASE_AD = 59.0          # 7.3: 62 → 59
AD_GROWTH = 3.5
BASE_AS = 0.75
AS_GROWTH = 0.032       # per level after 1
HP_BASE = 600.0
HP_GROWTH = 128.0

# Lethal Tempo 7.3 (ranged)
LT_AS_STACK = 0.064
LT_MAX = 6
LT_BOLT = (6.0, 24.0)
LT_BOLT_AS_AMP = 0.0067
BRUTAL = 15.0
CUT_DOWN = 0.08

Q_MISSILE = [40.0, 60.0, 80.0, 100.0]
# Isolated totals: 2.25× / 3.75× one missile (unevolved / evolved)
W_BASE = [30.0, 60.0, 90.0, 120.0]
E_AS = [0.40, 0.50, 0.60, 0.70]
E_CD = [16.0, 14.0, 12.0, 10.0]


def champ_ad(level: int) -> float:
    return BASE_AD + AD_GROWTH * (level - 1)


def champ_hp(level: int) -> float:
    return HP_BASE + HP_GROWTH * (level - 1)


@dataclass
class FightResult:
    damage: float = 0.0
    physical: float = 0.0
    magic: float = 0.0
    autos: int = 0
    plasma_pops: int = 0
    ttk: Optional[float] = None
    as_avg: float = 0.0
    as_peak: float = 0.0
    ad: float = 0.0
    ap: float = 0.0
    splash: float = 0.0
    evolved: Dict[str, bool] = field(default_factory=dict)
    items: List[str] = field(default_factory=list)


def simulate_fight(
    owned: List[str],
    minute: int,
    target: Target,
    extra_targets: int = 0,
) -> FightResult:
    level = level_at_minute(minute)
    st = aggregate(owned)
    evo = evolves(owned)
    has = set(owned)
    rage = "guinsoos_rageblade" in has
    kraken = "kraken_slayer" in has
    bork = "blade_of_the_ruined_king" in has
    terminus = "terminus" in has
    wits = "wits_end" in has
    nashor = "nashors_tooth" in has
    statikk = "statikk_shiv" in has
    runaan = "runaans_hurricane" in has
    n_side = max(0, extra_targets)
    side_hp = [target.hp for _ in range(n_side)]
    side_plasma = [0 for _ in range(n_side)]

    q_rank = skill_rank(level, "Q")
    w_rank = skill_rank(level, "W")
    e_rank = skill_rank(level, "E")

    base_ad = champ_ad(level)
    level_as = AS_GROWTH * (level - 1)
    e_as = E_AS[e_rank - 1] if e_rank else 0.0
    e_charge = max(0.50, 1.00 - 0.35 * min(1.2, st.bonus_as + level_as))

    hp = target.hp
    armor = target.armor
    mr = target.mr
    plasma = 0
    kraken_n = 0
    rage_stacks = 0
    rage_hits = 0
    lt_stacks = 0
    terminus_hits = 0
    terminus_dark = 0
    energized = 50.0
    energized_per_auto = 12 + (5 if statikk else 0)
    e_as_left = 0.0
    e_cd = 0.0
    charging = e_charge
    q_used = False
    w_used = False
    t = 0.0
    dt = 0.05
    next_auto = 0.0
    res = FightResult(evolved=dict(evo), items=list(owned))
    as_sum = 0.0
    as_n = 0
    killed_at: Optional[float] = None

    def total_ad() -> float:
        return base_ad + st.ad

    def total_ap() -> float:
        return st.ap

    def bonus_as() -> float:
        b = level_as + st.bonus_as + LT_AS_STACK * lt_stacks
        if rage:
            b += 0.08 * rage_stacks
        if e_as_left > 0:
            b += e_as
        return b

    def current_as() -> float:
        return min(AS_CAP, BASE_AS * (1.0 + bonus_as()))

    def pens() -> Tuple[float, float]:
        p = 0.10 * terminus_dark
        return min(0.90, p), min(0.90, p)

    def amp() -> float:
        a = 1.0
        if target.name == "tank":
            a *= 1.0 + CUT_DOWN
        return a

    def deal(amount: float, kind: str) -> None:
        nonlocal hp, killed_at
        if amount <= 0:
            return
        pp, mp = pens()
        if kind == "phys":
            amount *= phys_mult(armor, pp)
            res.physical += amount
        else:
            amount *= mag_mult(mr, mp)
            res.magic += amount
        amount *= amp()
        res.damage += amount
        hp -= amount
        if killed_at is None and hp <= 0:
            killed_at = t

    def deal_side(i: int, amount: float, kind: str) -> None:
        if amount <= 0 or i >= n_side:
            return
        pp, mp = pens()
        if kind == "phys":
            amount *= phys_mult(armor, pp)
        else:
            amount *= mag_mult(mr, mp)
        amount *= amp()
        res.splash += amount
        side_hp[i] -= amount

    def plasma_hit_damage(stacks_now: int) -> float:
        ap = total_ap()
        return (
            4.0 + 1.0 * level + 0.12 * ap
            + stacks_now * (1.0 + 0.2 * level + 0.02 * ap)
        )

    def apply_plasma(n: int = 1) -> None:
        nonlocal plasma
        for _ in range(n):
            plasma = min(5, plasma + 1)
            deal(plasma_hit_damage(plasma), "magic")
            if plasma >= 5:
                missing = max(0.0, target.hp - max(hp, 0.0))
                pct = 0.15 + 0.05 * (total_ap() / 100.0)
                deal(pct * missing, "magic")
                res.plasma_pops += 1
                plasma = 0

    def apply_plasma_side(i: int, n: int = 1) -> None:
        for _ in range(n):
            side_plasma[i] = min(5, side_plasma[i] + 1)
            deal_side(i, plasma_hit_damage(side_plasma[i]), "magic")
            if side_plasma[i] >= 5:
                missing = max(0.0, target.hp - max(side_hp[i], 0.0))
                pct = 0.15 + 0.05 * (total_ap() / 100.0)
                deal_side(i, pct * missing, "magic")
                side_plasma[i] = 0

    def onhit(is_phantom: bool) -> None:
        nonlocal kraken_n, terminus_hits, terminus_dark
        apply_plasma(1)
        if rage:
            deal(30.0, "magic")
        if terminus:
            deal(30.0, "magic")
            terminus_hits += 1
            if terminus_hits % 2 == 0:
                terminus_dark = min(3, terminus_dark + 1)
        if wits:
            deal(40.0, "magic")
        if nashor:
            deal(15.0 + 0.20 * st.ad + 0.30 * st.ap, "magic")
        if bork:
            deal(0.07 * max(hp, 0.0), "phys")
        deal(BRUTAL, "phys")
        if (not is_phantom) and kraken:
            kraken_n += 1
            if kraken_n % 3 == 0:
                missing = 1.0 - max(hp, 0.0) / max(target.hp, 1.0)
                base_k = lerp(120.0, 168.0, level)
                deal(base_k * (1.0 + min(0.75, missing * 0.75)), "phys")

    def onhit_side(i: int) -> None:
        apply_plasma_side(i, 1)
        if rage:
            deal_side(i, 30.0, "magic")
        if terminus:
            deal_side(i, 30.0, "magic")
        if wits:
            deal_side(i, 40.0, "magic")
        if nashor:
            deal_side(i, 15.0 + 0.20 * st.ad + 0.30 * st.ap, "magic")
        if bork:
            deal_side(i, 0.07 * max(side_hp[i], 0.0), "phys")
        deal_side(i, BRUTAL, "phys")

    def fire_q() -> None:
        if q_rank <= 0:
            return
        missile = Q_MISSILE[q_rank - 1] + 0.50 * st.ad + 0.30 * total_ap()
        n = 12 if evo["Q"] else 6
        # first missile 100%, others 25%
        total = missile * (1.0 + 0.25 * (n - 1))
        deal(total, "phys")

    def fire_w() -> None:
        if w_rank <= 0:
            return
        dmg = W_BASE[w_rank - 1] + 1.30 * total_ad() + 0.50 * total_ap()
        deal(dmg, "magic")
        apply_plasma(3 if evo["W"] else 2)

    def auto_attack() -> None:
        nonlocal rage_stacks, rage_hits, lt_stacks, energized, e_cd
        ad = total_ad()
        deal(ad, "phys")
        res.autos += 1
        onhit(False)
        if rage:
            rage_stacks = min(4, rage_stacks + 1)
            if rage_stacks >= 4:
                rage_hits += 1
                if rage_hits % 3 == 0:
                    onhit(True)
        lt_stacks = min(LT_MAX, lt_stacks + 1)
        if lt_stacks >= LT_MAX:
            bolt = lerp(LT_BOLT[0], LT_BOLT[1], level)
            bolt *= 1.0 + bonus_as() * 100.0 * LT_BOLT_AS_AMP
            deal(bolt, "phys")
        e_cd = max(0.0, e_cd - 0.5)
        energized += energized_per_auto
        if statikk and energized >= 100:
            energized = 0.0
            deal(60.0, "magic")
            bounces = 3
            if level >= 5:
                bounces = 4
            if level >= 9:
                bounces = 5
            if level >= 13:
                bounces = 6
            for i in range(min(n_side, bounces)):
                deal_side(i, 60.0, "magic")
                onhit_side(i)
        if runaan and n_side:
            # two bolts, 55% AD + on-hit
            for i in range(min(n_side, 2)):
                deal_side(i, 0.55 * ad, "phys")
                onhit_side(i)

    # 8s all-in: E charge (W during charge) → autos → Q isolated
    while t < FIGHT_SECONDS and (killed_at is None or t < killed_at + 0.01):
        as_sum += current_as()
        as_n += 1
        res.as_peak = max(res.as_peak, current_as())
        if charging > 0:
            charging -= dt
            if not w_used and w_rank:
                fire_w()
                w_used = True
            if charging <= 0:
                e_as_left = 4.0
                e_cd = E_CD[e_rank - 1] if e_rank else 16.0
                next_auto = t
        else:
            if e_as_left > 0:
                e_as_left -= dt
            if e_cd > 0:
                e_cd -= dt
            if e_rank and e_cd <= 0 and e_as_left <= 0 and charging <= 0:
                charging = e_charge
            if (not q_used) and q_rank and t >= e_charge + 0.55 and plasma >= 2:
                fire_q()
                q_used = True
            if charging <= 0 and t + 1e-9 >= next_auto:
                auto_attack()
                next_auto = t + 1.0 / max(0.40, current_as())
            energized += 20.0 * dt  # kiting
        t += dt

    res.ttk = killed_at
    res.as_avg = as_sum / max(1, as_n)
    res.ad = total_ad()
    res.ap = total_ap()
    return res


# ---------------------------------------------------------------------------
# Playable page
# ---------------------------------------------------------------------------

PAGE = {
    "champ": "Kai'Sa",
    "role": "ADC",
    "wrf": "A",
    "page": [
        "Kraken Slayer",
        "Berserker's Greaves",
        "Guinsoo's Rageblade",
        "Terminus",
        "Nashor's Tooth",
        "Zhonya's Hourglass",
    ],
    "buy": [
        "Long Sword",
        "Berserker's Greaves",
        "Kraken Slayer",
        "Guinsoo's Rageblade",
        "Terminus",
        "Nashor's Tooth",
        "Zhonya's Hourglass",
    ],
    "skill": "Q > E > W   (R mọi cấp)",
    "evolve": "Q rồi E rồi W   (mỗi legendary hoàn thành = 1 evolve)",
    "spells": "Flash + Ghost",
    "runes": [
        "Lethal Tempo",
        "Brutal",
        "Cut Down",
        "Legend: Bloodline",
        "Bone Plating",
    ],
    "pad": {
        "L1": "Q Icathian Rain (xả)",
        "L2": "W Void Seeker (aim)",
        "L3": "E Supercharge (GIỮ ~1s)",
        "L4": "R Killer Instinct (lock plasma)",
        "A": "AA tướng",
    },
    "combo": (
        "L3 giữ E → L2 W (2/3 plasma) → A A A (pop 5) → "
        "L1 Q đơn mục tiêu → L4 R nhảy / né. Ghost + E kite analog."
    ),
    "sit": [
        "BotRK first vs 2+ tank (12% lifesteal)",
        "Statikk first nếu teamfight / wave — bounce 7.3 apply on-hit + plasma",
        "Wit's End ô 5/6 vs AP poke (thay Nashor hoặc Zhonya)",
        "Runaan ô 5 nếu cần AoE plasma (crit 25% không phải identity)",
        "Steelcaps vs AD all-in",
        "Zhonya 6th = stasis sau R dive, không phải DPS",
    ],
    "pad_score": 78,
    "pad_note": (
        "Q tap, E giữ, R lock plasma. W aim nặng hơn Ashe. "
        "Analog kite + Supercharge. D-pad ← lính farm, → trụ."
    ),
}


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------


def snapshot(path_key: str, minute: int, extra: int = 0) -> Dict:
    path = PATHS[path_key]
    gold = gold_at_minute(minute)
    owned = owned_at_gold(path, gold)
    sq = simulate_fight(owned, minute, squishy(minute), extra)
    tk = simulate_fight(owned, minute, tank(minute), extra)
    return {
        "minute": minute,
        "level": level_at_minute(minute),
        "gold": gold,
        "owned": [item_name(i) for i in owned],
        "ids": owned,
        "evolved": evolves(owned),
        "squishy": round(sq.damage),
        "tank": round(tk.damage),
        "splash": round(sq.splash),
        "sq_ttk": None if sq.ttk is None else round(sq.ttk, 2),
        "tk_ttk": None if tk.ttk is None else round(tk.ttk, 2),
        "autos": sq.autos,
        "pops": sq.plasma_pops,
        "as_avg": round(sq.as_avg, 2),
        "ad": round(sq.ad, 1),
        "ap": round(sq.ap, 1),
    }


def first_item_ready(path_key: str) -> int:
    path = PATHS[path_key]
    first_leg = next(i for i in path if ITEMS[i]["tier"] == "legendary")
    for m in range(1, 25):
        if first_leg in owned_at_gold(path, gold_at_minute(m)):
            return m
    return 24


def score_path(path_key: str) -> float:
    """Weighted 1v1 damage: early spike + 3-item + late. Tank 40%."""
    total = 0.0
    weights = {8: 0.8, 12: 1.2, 16: 1.4, 20: 1.2, 24: 1.0}
    for m, w in weights.items():
        s = snapshot(path_key, m, 0)
        total += w * (0.60 * s["squishy"] + 0.40 * s["tank"])
    return total


def write_report(path: str) -> Dict:
    lines: List[str] = []
    a = lines.append
    a("=" * 78)
    a("TỐC CHIẾN 7.3 — KAI'SA ON-HIT FULL BUILD")
    a("WRF A · evolve = hoàn thành legendary · Mag Blaster gỡ · Statikk on-hit mới")
    a("Pad MB03 + D-pad. DPS 8s all-in (E charge → W → AA → Q isolated).")
    a("=" * 78)
    a("")

    scores = {k: score_path(k) for k in ("kraken", "statikk", "botrk")}
    winner = max(scores, key=scores.get)
    tf = {k: snapshot(k, 16, 2) for k in ("kraken", "statikk", "botrk")}
    shiv_tf = tf["statikk"]["squishy"] + tf["statikk"]["splash"]
    krak_tf = tf["kraken"]["squishy"] + tf["kraken"]["splash"]

    pg = PAGE
    a("PLAY THIS  (WRF 7.3 + sim 1v1)")
    a(f"  Ô:     {' › '.join(pg['page'])}")
    a(f"  Mua:   {' › '.join(pg['buy'])}")
    a(f"  Max    {pg['skill']}")
    a(f"  Evolve {pg['evolve']}")
    a(f"  Spell  {pg['spells']}")
    a(f"  Runes  {' · '.join(pg['runes'])}")
    a(f"  Pad    L1 {pg['pad']['L1']}")
    a(f"         L2 {pg['pad']['L2']}")
    a(f"         L3 {pg['pad']['L3']}")
    a(f"         L4 {pg['pad']['L4']}")
    a(f"         A  {pg['pad']['A']}")
    a(f"  Combo  {pg['combo']}")
    a(f"  Pad score {pg['pad_score']}  {pg['pad_note']}")
    a("")
    a("  Swap:")
    for s in pg["sit"]:
        a(f"    · {s}")
    a("")

    a("-" * 78)
    a("VÌ SAO KRAKEN FIRST (không phải crit 7.3)")
    a("-" * 78)
    a("  • Magnetic Blaster gỡ — không còn 1 item range+wave+burst.")
    a("  • Evolve Q lúc legendary 1 (~phút 8). Kraken Recurve path + Long Sword.")
    a("  • Rageblade 7.3: 35 AD / 30 AP, Wrath 30 magic, Seething 8% AS×4,")
    a("    phantom mỗi 3 hit. Bỏ khóa crit → on-hit không bị phạt.")
    a("  • Terminus 3000g, 35 AD / 35% AS, Shadow 30 + 30% pen @3 stack.")
    a("  • Plasma 7.3 scale AP + stack — Nashor/Zhonya 4th/6th bơm pop.")
    a("  • Supercharge MS = bonus AS (cap 100–130%) — AS cap 3.0 giúp E.")
    a("  • Base AD 62→59 — không đi crit; identity on-hit.")
    a("")

    a("-" * 78)
    a("FIRST ITEM  (1v1, 8s)")
    a("-" * 78)
    a(f"  {'Path':<44}{'8':>7}{'12':>7}{'16':>7}{'20':>7}{'24':>7}  ready")
    first_table = []
    for key in ("kraken", "statikk", "botrk"):
        row = {"key": key, "label": PATH_LABEL[key], "ready": first_item_ready(key)}
        cells = []
        for m in MINUTES:
            s = snapshot(key, m, 0)
            row[str(m)] = s
            cells.append(f"{s['squishy']:>7}")
        a(f"  {PATH_LABEL[key]:<44}{''.join(cells)}  {row['ready']}:00")
        first_table.append(row)
    a("")
    a("  Tank 1v1 @12 / @16 / @20")
    for key in ("kraken", "statikk", "botrk"):
        bits = [str(snapshot(key, m, 0)["tank"]) for m in (12, 16, 20)]
        a(f"    {PATH_LABEL[key]:<44}  {' / '.join(bits)}")
    a("")
    a("  Teamfight 3 mục tiêu @16 (main + splash)")
    for key in ("kraken", "statikk", "botrk"):
        s = snapshot(key, 16, 2)
        a(
            f"    {PATH_LABEL[key]:<44}  "
            f"main {s['squishy']} + splash {s['splash']} = {s['squishy'] + s['splash']}"
        )
    a("")
    a(f"  1v1 weighted winner: {PATH_LABEL[winner]}")
    if shiv_tf > krak_tf:
        a("  Teamfight @16: Statikk thắng splash (bounce apply on-hit + plasma).")
    else:
        a("  Teamfight @16: Kraken vẫn hơn hoặc sát Statikk.")
    a("")

    a("-" * 78)
    a("SPIKE MUA ĐỒ  (path Kraken mặc định)")
    a("-" * 78)
    for m in MINUTES:
        s = snapshot("kraken", m, 0)
        evo = "".join(k if v else "·" for k, v in s["evolved"].items())
        a(
            f"  {m:02d}:00  lv{s['level']:<2}  {s['gold']:>5}g  "
            f"evo {evo}  AS {s['as_avg']:.2f}  "
            f"squish {s['squishy']:<5}  tank {s['tank']}"
        )
        a(f"         { ' › '.join(s['owned']) }")
    a("")

    a("-" * 78)
    a("4TH ITEM SAU TERMINUS  (Kraken+Rage+Terminus core, @20)")
    a("-" * 78)
    s20_n = snapshot("kraken", 20, 0)
    s20_b = snapshot("kraken_bork4", 20, 0)
    a(f"  Nashor   squish {s20_n['squishy']}  tank {s20_n['tank']}  AS {s20_n['as_avg']}")
    a(f"  BotRK    squish {s20_b['squishy']}  tank {s20_b['tank']}  AS {s20_b['as_avg']}")
    a("  WRF giữ Nashor (AS 45% + Gnaw + AP/AD fang → plasma).")
    a("  BotRK 4th nếu team tank và cần 12% lifesteal.")
    a("")

    a("-" * 78)
    a("PAD MB03")
    a("-" * 78)
    a("  Analog di chuyển. A = AA tướng. D-pad ↑ bảng  ↓ hồi  ← lính  → trụ.")
    a("  Đừng bind Q vào analog. E là gồng–nhả (giống Vi Q), không tap.")
    a("  R chỉ lock được tướng đang có Plasma — W hoặc AA trước.")
    a("")
    a("KIT 7.3 (nhớ khi chơi)")
    a("  Plasma on-hit: 4 + 1×lv + 12% AP + stacks×(1 + 0.2×lv + 2% AP)")
    a("  Pop 5: (15 + 5% AP)% missing HP.")
    a("  W: 30–120 + 130% AD + 50% AP. Evolve = 3 stack + refund 70% CD.")
    a("  E MS: bonus AS (cap 100/110/120/130%). Invisible khi evolve.")
    a("  R shield: 100–150 + 80/120/160% AD + 100% AP. Landing 5.5.")
    a("=" * 78)

    payload = {
        "patch": PATCH,
        "champ": "Kai'Sa",
        "winner_1v1": winner,
        "scores": {k: round(v) for k, v in scores.items()},
        "page": pg,
        "first_item": {
            k: {
                "ready": first_item_ready(k),
                "label": PATH_LABEL[k],
                "by_minute": {str(m): snapshot(k, m, 0) for m in MINUTES},
                "teamfight16": snapshot(k, 16, 2),
            }
            for k in ("kraken", "statikk", "botrk")
        },
        "fourth_at_20": {
            "nashor": snapshot("kraken", 20, 0),
            "botrk": snapshot("kraken_bork4", 20, 0),
        },
        "default_spikes": [snapshot("kraken", m, 0) for m in MINUTES],
        "notes": {
            "nashor_talon_removed": True,
            "magnetic_blaster_removed": True,
            "evolve": "complete legendary",
        },
    }

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return payload


def main() -> None:
    here = os.path.dirname(os.path.abspath(__file__))
    payload = write_report(os.path.join(here, "report.txt"))
    with open(os.path.join(here, "results.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print("1v1 winner:", PATH_LABEL[payload["winner_1v1"]])
    print("Page:", " › ".join(PAGE["page"]))
    for s in payload["default_spikes"]:
        print(
            f"  {s['minute']:02d}:00 evo "
            f"{''.join(k if v else '.' for k, v in s['evolved'].items())} "
            f"squish {s['squishy']} tank {s['tank']}  { ' › '.join(s['owned']) }"
        )
    print("Wrote report.txt and results.json")


if __name__ == "__main__":
    main()
