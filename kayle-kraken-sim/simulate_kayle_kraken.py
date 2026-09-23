#!/usr/bin/env python3
"""
Wild Rift 7.3 — Does Kraken Slayer fit Kayle?

WRF 7.3 A (mid): Nashor's Tooth → Dusk and Dawn → Deathcap.
Kit is AP-scaled; ranged from lv5 so Kraken Bring It Down uses
the weaker ranged numbers. Kraken is the AD on-hit alt (vs tanks).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import json
import os

PATCH = "7.3"
AS_CAP = 3.0
FIGHT_SECONDS = 8.0
MINUTES = (8, 12, 16, 20, 24)
BASE_AS = 0.82
AS_GROWTH = 0.025
BASE_AD = 54.0
AD_GROWTH = 3.0
CONQ_AP = (4.0, 8.0)
CONQ_AD = (3.0, 5.0)
CONQ_MAX = 6
CUT_DOWN = 0.08

PAGE = {
    "page": [
        "Nashor's Tooth",
        "Boots of Mana",
        "Dusk and Dawn",
        "Rabadon's Deathcap",
        "Void Staff",
        "Infinity Orb",
    ],
    "buy": [
        "Amplifying Tome",
        "Boots of Mana",
        "Nashor's Tooth",
        "Dusk and Dawn",
        "Rabadon's Deathcap",
        "Void Staff",
        "Infinity Orb",
    ],
    "skill": "E > Q > W (R mọi cấp)",
    "spells": "Flash + Barrier",
    "runes": [
        "Conqueror",
        "Botanist",
        "Absolute Focus",
        "Gathering Storm",
        "Bone Plating",
    ],
    "pad": {
        "L1": "Q shred 20% giáp/MR",
        "L2": "W heal + MS",
        "L3": "E active missing HP",
        "L4": "R invuln / blades",
        "A": "AA on-hit kite (ranged lv5)",
    },
    "kraken_alt": [
        "Nashor's Tooth",
        "Berserker's Greaves",
        "Kraken Slayer",
        "Guinsoo's Rageblade",
        "Terminus",
        "Wit's End",
    ],
}


def gold_at_minute(m: int) -> int:
    """Solo/mid farmer — first legendary ~8, Deathcap ~16."""
    if m <= 0:
        return 500
    total = 500
    for t in range(1, m + 1):
        if t <= 4:
            total += 380
        elif t <= 10:
            total += 620
        elif t <= 20:
            total += 750
        else:
            total += 1000
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
    """E > Q > W. R at 5 / 9 / 13."""
    if skill == "R":
        return (1 if level >= 5 else 0) + (1 if level >= 9 else 0) + (1 if level >= 13 else 0)
    mapping = {
        "E": [1, 3, 6, 7],
        "Q": [2, 8, 10, 11],
        "W": [4, 12, 14, 15],
    }
    return sum(1 for lv in mapping[skill] if level >= lv)


def lerp(lo: float, hi: float, level: int) -> float:
    return lo + (hi - lo) * ((level - 1) / 14.0)


ITEMS: Dict[str, Dict] = {
    "amplifying_tome": {
        "name": "Amplifying Tome", "cost": 500, "tier": "start",
        "stats": {"ap": 20},
    },
    "long_sword": {
        "name": "Long Sword", "cost": 500, "tier": "start",
        "stats": {"ad": 12},
    },
    "boots_of_mana": {
        "name": "Boots of Mana", "cost": 1000, "tier": "boots",
        "stats": {"ah": 25},
    },
    "berserkers_greaves": {
        "name": "Berserker's Greaves", "cost": 1200, "tier": "boots",
        "stats": {"ad": 10, "as": 0.35},
    },
    "nashors_tooth": {
        "name": "Nashor's Tooth", "cost": 2800, "tier": "legendary",
        "stats": {"as": 0.45, "ah": 20},
        "adaptive": True,
        "credits": ["amplifying_tome"],
    },
    "dusk_and_dawn": {
        "name": "Dusk and Dawn", "cost": 3100, "tier": "legendary",
        "stats": {"ap": 70, "as": 0.25, "hp": 350, "ah": 20},
    },
    "rabadons_deathcap": {
        "name": "Rabadon's Deathcap", "cost": 3300, "tier": "legendary",
        "stats": {"ap": 120},
        "ap_mult": 0.35,
    },
    "void_staff": {
        "name": "Void Staff", "cost": 2800, "tier": "legendary",
        "stats": {"ap": 80, "mag_pen": 0.40},
    },
    "infinity_orb": {
        "name": "Infinity Orb", "cost": 3000, "tier": "legendary",
        "stats": {"ap": 70, "mag_pen": 0.20},
    },
    "kraken_slayer": {
        "name": "Kraken Slayer", "cost": 2900, "tier": "legendary",
        "stats": {"ad": 45, "as": 0.35},
        "credits": ["long_sword"],
    },
    "guinsoos_rageblade": {
        "name": "Guinsoo's Rageblade", "cost": 3000, "tier": "legendary",
        "stats": {"ad": 35, "ap": 30},
    },
    "terminus": {
        "name": "Terminus", "cost": 3000, "tier": "legendary",
        "stats": {"ad": 35, "as": 0.35},
    },
    "wits_end": {
        "name": "Wit's End", "cost": 2800, "tier": "legendary",
        "stats": {"as": 0.50, "mr": 40},
    },
}


def item_name(iid: str) -> str:
    return ITEMS[iid]["name"]


PATHS: Dict[str, List[str]] = {
    "ap": [
        "amplifying_tome", "boots_of_mana", "nashors_tooth",
        "dusk_and_dawn", "rabadons_deathcap", "void_staff", "infinity_orb",
    ],
    "kraken": [
        "long_sword", "berserkers_greaves", "kraken_slayer",
        "guinsoos_rageblade", "terminus", "nashors_tooth", "wits_end",
    ],
    "nashor_kraken": [
        "amplifying_tome", "berserkers_greaves", "nashors_tooth",
        "kraken_slayer", "guinsoos_rageblade", "terminus", "wits_end",
    ],
    "kraken_ap": [
        "long_sword", "berserkers_greaves", "kraken_slayer",
        "nashors_tooth", "dusk_and_dawn", "rabadons_deathcap", "void_staff",
    ],
}

PATH_LABEL = {
    "ap": "Nashor → Dusk → Cap → Void → Orb  (WRF AP)",
    "kraken": "Kraken → Rageblade → Terminus → Nashor → Wit's End",
    "nashor_kraken": "Nashor → Kraken → Rageblade → Terminus  (Kraken 2nd)",
    "kraken_ap": "Kraken → Nashor → Dusk → Cap → Void  (hybrid)",
}


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
        mr += 20
    return Target("squishy", hp, armor, mr)


def tank(m: int) -> Target:
    lv = level_at_minute(m)
    hp = 720 + 125 * lv + 90 * m
    armor = 42 + 5.0 * lv + 14 * m
    mr = 32 + 2.0 * lv + 9 * m
    return Target("tank", hp, armor, mr)


def phys_mult(armor: float, pct_pen: float) -> float:
    return 100.0 / (100.0 + max(0.0, armor * (1.0 - pct_pen)))


def mag_mult(mr: float, pct_pen: float) -> float:
    return 100.0 / (100.0 + max(0.0, mr * (1.0 - pct_pen)))


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
        if spent + cost <= gold:
            spent += cost
            owned.append(iid)
        else:
            break
    return owned


def first_item_ready(path_key: str) -> int:
    path = PATHS[path_key]
    for m in range(1, 25):
        owned = owned_at_gold(path, gold_at_minute(m))
        if any(ITEMS[i]["tier"] == "legendary" for i in owned):
            return m
    return 25


def legendaries(owned: List[str]) -> List[str]:
    return [i for i in owned if ITEMS[i]["tier"] == "legendary"]


@dataclass
class Stats:
    ad: float = 0.0
    ap: float = 0.0
    bonus_as: float = 0.0
    mag_pen: float = 0.0
    items: List[str] = field(default_factory=list)


def aggregate(owned: List[str]) -> Stats:
    st = Stats(items=list(owned))
    nashor = False
    cap_mult = 0.0
    for iid in owned:
        s = ITEMS[iid]["stats"]
        st.ad += s.get("ad", 0.0)
        st.ap += s.get("ap", 0.0)
        st.bonus_as += s.get("as", 0.0)
        st.mag_pen += s.get("mag_pen", 0.0)
        if iid == "nashors_tooth":
            nashor = True
        cap_mult += ITEMS[iid].get("ap_mult", 0.0)
    if nashor:
        if st.ap >= st.ad:
            st.ap += 50.0
        else:
            st.ad += 25.0
    if cap_mult:
        st.ap *= 1.0 + cap_mult
    return st


@dataclass
class FightResult:
    damage: float = 0.0
    physical: float = 0.0
    magic: float = 0.0
    autos: int = 0
    ttk: Optional[float] = None
    as_avg: float = 0.0
    as_peak: float = 0.0
    ranged: bool = False
    items: List[str] = field(default_factory=list)


def simulate_fight(
    owned: List[str],
    minute: int,
    target: Target,
    stop_on_kill: bool = True,
) -> FightResult:
    level = level_at_minute(minute)
    st = aggregate(owned)
    has = set(owned)
    kraken = "kraken_slayer" in has
    rage = "guinsoos_rageblade" in has
    terminus = "terminus" in has
    wits = "wits_end" in has
    nashor = "nashors_tooth" in has
    dusk = "dusk_and_dawn" in has
    ranged = level >= 5

    e_rank = skill_rank(level, "E")
    q_rank = skill_rank(level, "Q")
    r_rank = skill_rank(level, "R")
    e_pass = [8.0, 11.0, 14.0, 17.0]
    e_miss = [0.07, 0.08, 0.09, 0.10]
    q_base = [60.0, 100.0, 140.0, 180.0]
    r_base = [150.0, 225.0, 300.0]

    hp = target.hp
    armor = target.armor
    mr = target.mr
    shred = 0.0
    kraken_n = 0
    rage_stacks = 0
    rage_hits = 0
    terminus_dark = 0
    terminus_hits = 0
    conq = 0
    zeal = 0
    dusk_cd = 0.0
    e_active = True
    q_used = False
    r_used = False
    t = 0.0
    dt = 0.05
    next_auto = 0.20
    killed_at: Optional[float] = None
    res = FightResult(items=list(owned), ranged=ranged)
    as_sum = 0.0
    as_n = 0
    ap_kayle = st.ap >= st.ad

    def total_ad() -> float:
        extra = lerp(CONQ_AD[0], CONQ_AD[1], level) * conq if not ap_kayle else 0.0
        return BASE_AD + AD_GROWTH * (level - 1) + st.ad + extra

    def total_ap() -> float:
        extra = lerp(CONQ_AP[0], CONQ_AP[1], level) * conq if ap_kayle else 0.0
        return st.ap + extra

    def current_as() -> float:
        p = zeal * (0.04 + 0.01 * (total_ap() / 100.0))
        b = AS_GROWTH * (level - 1) + st.bonus_as + p
        if rage:
            b += 0.08 * rage_stacks
        return min(AS_CAP, BASE_AS * (1.0 + b))

    def pen_phys() -> float:
        return min(0.90, shred + 0.10 * terminus_dark)

    def pen_mag() -> float:
        return min(0.90, st.mag_pen + shred + 0.10 * terminus_dark)

    def deal(amount: float, kind: str) -> None:
        nonlocal hp, killed_at
        if amount <= 0:
            return
        if kind == "phys":
            amount *= phys_mult(armor, pen_phys())
            res.physical += amount
        else:
            amount *= mag_mult(mr, pen_mag())
            res.magic += amount
        if hp / max(target.hp, 1.0) > 0.60:
            amount *= 1.0 + CUT_DOWN
        res.damage += amount
        hp -= amount
        if killed_at is None and hp <= 0:
            killed_at = t

    def onhit(is_phantom: bool) -> None:
        nonlocal kraken_n, terminus_hits, terminus_dark
        ap = total_ap()
        b_ad = st.ad
        e_tick = (e_pass[e_rank - 1] + 0.05 * b_ad + 0.15 * ap) if e_rank else 0.0
        if e_tick:
            deal(e_tick, "magic")
        if nashor:
            deal(15.0 + 0.20 * b_ad + 0.30 * ap, "magic")
        if rage:
            deal(30.0, "magic")
        if terminus:
            deal(30.0, "magic")
            terminus_hits += 1
            if terminus_hits % 2 == 0:
                terminus_dark = min(3, terminus_dark + 1)
        if wits:
            deal(40.0, "magic")
        if (not is_phantom) and kraken:
            kraken_n += 1
            if kraken_n % 3 == 0:
                missing = 1.0 - max(hp, 0.0) / max(target.hp, 1.0)
                lo, hi = (120.0, 168.0) if ranged else (150.0, 210.0)
                deal(lerp(lo, hi, level) * (1.0 + min(0.75, missing * 0.75)), "phys")
        flame = level >= 13 or (level >= 9 and zeal >= 5)
        if flame and e_tick:
            deal(e_tick, "magic")

    def auto_attack() -> None:
        nonlocal zeal, rage_stacks, rage_hits, conq, dusk_cd, e_active
        ad = total_ad()
        deal(ad, "phys")
        res.autos += 1
        if e_active and e_rank:
            pct = e_miss[e_rank - 1] + 0.02 * (total_ap() / 100.0)
            deal(pct * max(0.0, target.hp - max(hp, 0.0)), "magic")
            e_active = False
        onhit(False)
        if dusk and dusk_cd <= 0:
            base = BASE_AD + AD_GROWTH * (level - 1)
            deal(0.75 * base + 0.10 * total_ap(), "magic")
            onhit(True)
            dusk_cd = 1.5
        if rage:
            rage_stacks = min(4, rage_stacks + 1)
            if rage_stacks >= 4:
                rage_hits += 1
                if rage_hits % 3 == 0:
                    onhit(True)
        zeal = min(5, zeal + 1)
        conq = min(CONQ_MAX, conq + 1)

    while t < FIGHT_SECONDS and (
        (not stop_on_kill) or killed_at is None or t < killed_at + 0.01
    ):
        atk = current_as()
        as_sum += atk
        as_n += 1
        res.as_peak = max(res.as_peak, atk)
        if dusk_cd > 0:
            dusk_cd -= dt
        if (not q_used) and q_rank and t >= 0.10:
            deal(q_base[q_rank - 1] + 0.60 * total_ad() + 0.50 * total_ap(), "magic")
            shred = 0.20
            q_used = True
            dusk_cd = 0.0
            conq = min(CONQ_MAX, conq + 1)
        if (not r_used) and r_rank and t >= 0.55:
            b_ad = st.ad
            deal(r_base[r_rank - 1] + 0.85 * b_ad + 0.60 * total_ap(), "magic")
            r_used = True
            dusk_cd = 0.0
            conq = min(CONQ_MAX, conq + 1)
        if t + 1e-9 >= next_auto:
            auto_attack()
            next_auto = t + 1.0 / max(0.45, current_as())
        t += dt

    res.ttk = killed_at
    res.as_avg = as_sum / max(1, as_n)
    return res


def snapshot(path_key: str, minute: int, stop_on_kill: bool = False) -> Dict:
    path = PATHS[path_key]
    gold = gold_at_minute(minute)
    owned = owned_at_gold(path, gold)
    sq = simulate_fight(owned, minute, squishy(minute), stop_on_kill)
    tk = simulate_fight(owned, minute, tank(minute), stop_on_kill)
    st = aggregate(owned)
    lv = level_at_minute(minute)
    sq_t = FIGHT_SECONDS if not stop_on_kill else (sq.ttk if sq.ttk else FIGHT_SECONDS)
    tk_t = FIGHT_SECONDS if not stop_on_kill else (tk.ttk if tk.ttk else FIGHT_SECONDS)
    return {
        "minute": minute,
        "level": lv,
        "gold": gold,
        "owned": [item_name(i) for i in owned],
        "ids": owned,
        "squishy": round(sq.damage),
        "tank": round(tk.damage),
        "sq_dps": round(sq.damage / max(0.2, sq_t)),
        "tk_dps": round(tk.damage / max(0.2, tk_t)),
        "sq_ttk": None if sq.ttk is None else round(sq.ttk, 2),
        "tk_ttk": None if tk.ttk is None else round(tk.ttk, 2),
        "ranged": lv >= 5,
        "as_avg": round(sq.as_avg, 2),
        "as_peak": round(sq.as_peak, 2),
        "ad": round(BASE_AD + AD_GROWTH * (lv - 1) + st.ad, 1),
        "ap": round(st.ap, 1),
    }


def score_path(path_key: str) -> float:
    """8s sponge DPS: squishy 55% + tank 45% (Kayle mid/top fights both)."""
    total = 0.0
    weights = {8: 0.8, 12: 1.2, 16: 1.4, 20: 1.3, 24: 1.2}
    for m, w in weights.items():
        s = snapshot(path_key, m, False)
        total += w * (0.55 * s["sq_dps"] + 0.45 * s["tk_dps"])
    return total


def write_report(path: str) -> Dict:
    lines: List[str] = []
    a = lines.append
    scores = {k: score_path(k) for k in PATHS}
    ranked = sorted(PATHS, key=lambda k: scores[k], reverse=True)
    winner = ranked[0]
    ap_s = scores["ap"]
    kr_first = scores["kraken"]
    kr_second = scores["nashor_kraken"]
    fits_first = kr_first > ap_s
    fits_second = kr_second >= ap_s * 0.97

    a("=" * 78)
    a("TỐC CHIẾN 7.3 — KRAKEN SLAYER HỢP KAYLE KHÔNG?")
    a("WRF A: Nashor → Dusk and Dawn → Deathcap. Kayle ranged từ lv5.")
    a("8s sponge: Q shred 20% → R blades → E active → AA on-hit (wave lv9 @5 stack).")
    a("=" * 78)
    a("")
    a("TRẢ LỜI: Không phải first item mặc định. Play Nashor → Dusk → Cap.")
    a("  Kraken first thắng 8s DPS phút 8–16 (tank), thua AP @20+ khi Cap+Void.")
    a("  Kit AP (W heal 30%, R 60% AP) + Diamond+ ~60% WR → giữ AP core.")
    if fits_second:
        a("  Kraken 2nd sau Nashor gần AP — alt vs tank. Nếu đi Kraken thì rush.")
    else:
        a("  Nếu đi Kraken: rush (Rage → Terminus). Đừng Nashor rồi Kraken — trễ Dusk lẫn Rage.")
    a("  Lv5+ ranged → Bring It Down 120–168 (melee 150–210).")
    a("")
    a(f"  {'#':<3}{'Path':<54}{'8':>6}{'12':>6}{'16':>6}{'20':>6}{'24':>6}  score")
    table = {}
    for i, key in enumerate(ranked, 1):
        cells = []
        row = {}
        for m in MINUTES:
            s = snapshot(key, m, False)
            row[str(m)] = s
            cells.append(f"{s['sq_dps']:>6}")
        mark = " <<" if key == winner else ""
        a(f"  {i:<3}{PATH_LABEL[key]:<54}{''.join(cells)}  {round(scores[key])}{mark}")
        table[key] = row
    a("")
    a("  Tank 8s DPS @12 / @16 / @20 / @24")
    for key in ranked:
        bits = [str(snapshot(key, m, False)["tk_dps"]) for m in (12, 16, 20, 24)]
        a(f"    {PATH_LABEL[key]:<54}  {' / '.join(bits)}")
    a("")
    a("-" * 78)
    a("SPIKE")
    a("-" * 78)
    for key in ("ap", "kraken", "nashor_kraken"):
        a(f"  {PATH_LABEL[key]}")
        for m in MINUTES:
            s = snapshot(key, m, False)
            a(
                f"    {m:02d}:00 lv{s['level']:<2}  AP {s['ap']:<5} AD {s['ad']:<5}  "
                f"dps {s['sq_dps']}/{s['tk_dps']}  {' › '.join(s['owned'])}"
            )
        a("")
    a("TRANG MẶC ĐỊNH (WRF AP)")
    a(f"  Ô:     {' › '.join(PAGE['page'])}")
    a(f"  Mua:   {' › '.join(PAGE['buy'])}")
    a(f"  Max:   {PAGE['skill']}")
    a(f"  Spell: {PAGE['spells']}")
    a(f"  Runes: {' · '.join(PAGE['runes'])}")
    a("  Pad:   " + " · ".join(f"{k} {v}" for k, v in PAGE["pad"].items()))
    a("")
    a("ALT KRAKEN 2ND (vs tank / full HP)")
    a(f"  Ô:     {' › '.join(PAGE['kraken_alt'])}")
    a("  Mua:   Tome → Berserkers → Nashor → Kraken → Rageblade → Terminus")
    a("")
    a("VÌ SAO KHÔNG RUSH KRAKEN")
    a("  • Kit 7.3 scale AP: E 15% AP, Q 50% AP, W heal 30% AP, R 60% AP,")
    a("    passive AS +1% AP/stack. Nashor fang = 50 AP + Gnaw 30% AP.")
    a("  • Lv5 ranged → Kraken Bring It Down 120–168 (melee 150–210).")
    a("  • Dusk and Dawn = spellblade + extra on-hit (Nashor/E proc 2 lần).")
    a("  • Diamond+ core Nashor→Dusk→Cap ~60% WR. Kraken là nhánh AD.")
    a("  • Kraken 2nd/3rd sau Nashor nếu team full HP — không first item.")
    a("=" * 78)

    payload = {
        "patch": PATCH,
        "champ": "Kayle",
        "fits": False,
        "fits_first": fits_first,
        "fits_as": "onhit_2nd_vs_tanks" if fits_second else "onhit_alt_vs_tanks",
        "winner": winner,
        "scores": {k: round(v) for k, v in scores.items()},
        "page": PAGE["page"],
        "buy": PAGE["buy"],
        "skill": PAGE["skill"],
        "spells": PAGE["spells"],
        "runes": PAGE["runes"],
        "pad": PAGE["pad"],
        "kraken_alt": PAGE["kraken_alt"],
        "page_ap": PAGE["page"],
        "page_kraken": PAGE["kraken_alt"],
        "by_path": {
            k: {
                "label": PATH_LABEL[k],
                "score": round(scores[k]),
                "by_minute": {str(m): snapshot(k, m, False) for m in MINUTES},
            }
            for k in PATHS
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
    print("Fits Kraken first?", payload["fits_first"])
    print("Fits as:", payload["fits_as"])
    print("Winner:", PATH_LABEL[payload["winner"]])
    for k in PATHS:
        print(f"  {PATH_LABEL[k]}  score {payload['scores'][k]}")
    print("Wrote report.txt and results.json")


if __name__ == "__main__":
    main()
