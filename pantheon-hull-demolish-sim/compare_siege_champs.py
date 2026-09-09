#!/usr/bin/env python3
"""
Same Hullbreaker + Demolish siege path, four Baron kits.
Playstyle constraint: no all-in. Farm waves, crash turret, leave.

Pantheon = previous baseline (W-Q kit fighting the constraint).
Sion / Nasus / Tryndamere = actual split-siege kits.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List
import json

from simulate_pantheon_siege import (
    BUILD_PATHS,
    SIEGE_SECONDS,
    demolish_raw,
    gold_at_minute,
    level_at_minute,
    overgrowth_hp,
    phys_after_armor,
    resolve_inventory,
    skipper_raw,
    titanic_onhit,
    turret_armor,
    turret_hp,
)


PATH = "Hull → Trinity → Titanic (Siege)"


@dataclass
class Champ:
    key: str
    hp0: float
    hp_lvl: float
    ad0: float
    ad_lvl: float
    as0: float
    as_lvl: float  # bonus AS % per level (HUD)
    as_ratio: float
    r_pen: float  # % armor pen from kit (Pantheon R passive)


CHAMPS = {
    "Pantheon": Champ("Pantheon", 690, 120, 64, 3.6, 0.80, 0.022, 0.80, 0.0),
    "Sion": Champ("Sion", 630, 104, 64, 4.55, 0.80, 0.012, 0.667, 0.0),
    "Nasus": Champ("Nasus", 650, 120, 58, 4.0, 0.70, 0.018, 0.70, 0.0),
    "Tryndamere": Champ("Tryndamere", 625, 98, 69, 4.2, 0.70, 0.029, 0.67, 0.0),
}


def panth_r_pen(level: int) -> float:
    if level >= 13:
        return 0.30
    if level >= 9:
        return 0.20
    if level >= 5:
        return 0.10
    return 0.0


def sion_glory_hp(minute: int) -> float:
    """Last-hit only. +5 small, +20 cannon. ~1.8 waves/min, 80% of last hits."""
    waves = max(0.0, (minute - 1) * 1.8)
    return waves * (6 * 5 + 20) * 0.80


def nasus_q_stacks(minute: int) -> float:
    """Q last-hits only, no champion stacks. ~2 Q/wave early, more when CD 4s."""
    stacks = 0.0
    for t in range(2, minute + 1):
        q_cd = 7.0 if t < 8 else (5.0 if t < 14 else 4.0)
        q_per_wave = min(3.0, 8.0 / q_cd)
        waves = 1.8
        small = q_per_wave * waves * 5.0 * 0.75
        cannon = 1.8 * 14.0 * 0.45
        stacks += small + cannon
    return stacks


def nasus_q_base(level: int) -> float:
    if level >= 13:
        return 110.0
    if level >= 9:
        return 80.0
    if level >= 5:
        return 50.0
    return 20.0


def nasus_q_cd(level: int) -> float:
    if level >= 13:
        return 4.0
    if level >= 9:
        return 5.0
    if level >= 5:
        return 6.0
    return 7.0


def champ_stats(name: str, items, minute: int) -> Dict[str, float]:
    c = CHAMPS[name]
    lv = level_at_minute(minute)
    ad = c.ad0 + c.ad_lvl * (lv - 1)
    base_ad = ad
    hp_item = 0.0
    as_pct = 0.0
    lethality = 0.0
    hull = trinity = titanic = dmp = False
    sheen = 0.0
    for it in items:
        ad += it.ad
        hp_item += it.hp
        as_pct += it.as_pct
        lethality += it.lethality
        hull = hull or it.hull
        trinity = trinity or it.trinity
        titanic = titanic or it.titanic
        dmp = dmp or it.dmp
        if it.name == "Sheen" and not trinity:
            sheen = 1.0
    if trinity:
        sheen = 2.0
    extra_hp = 0.0
    if name == "Sion":
        extra_hp = sion_glory_hp(minute)
    base_hp = c.hp0 + c.hp_lvl * (lv - 1)
    og = overgrowth_hp(minute, hp_item + extra_hp, base_hp)
    max_hp = base_hp + hp_item + extra_hp + og
    alacrity = 0.12
    attack_speed = c.as0 + c.as_ratio * (as_pct + alacrity + c.as_lvl * (lv - 1))
    pen = panth_r_pen(lv) if name == "Pantheon" else 0.0
    q_bonus = 0.0
    q_cd = 99.0
    if name == "Nasus":
        q_bonus = nasus_q_base(lv) + nasus_q_stacks(minute)
        q_cd = nasus_q_cd(lv)
    return {
        "ad": ad,
        "base_ad": base_ad,
        "max_hp": max_hp,
        "bonus_hp": hp_item + extra_hp + og,
        "as": attack_speed,
        "lethality": lethality,
        "pct_pen": pen,
        "hull": 1.0 if hull else 0.0,
        "sheen": sheen,
        "titanic": 1.0 if titanic else 0.0,
        "dmp": 1.0 if dmp else 0.0,
        "q_bonus": q_bonus,
        "q_cd": q_cd,
        "glory": extra_hp,
        "stacks": nasus_q_stacks(minute) if name == "Nasus" else 0.0,
    }


def window(st: Dict[str, float], kind: str = "outer") -> Dict[str, float]:
    armor = max(0.0, turret_armor(kind) - st["lethality"])
    n_aa = max(1, int(round(st["as"] * SIEGE_SECONDS)))
    demolish = demolish_raw(st["max_hp"])
    total = 0.0
    q_ready = st["q_bonus"] > 0
    q_cd_left = 0.0
    sheen_ready = st["sheen"] > 0
    titanic_cd = 0.0
    interval = 1.0 / max(0.5, st["as"])
    t = 0.0
    qs = 0
    skippers = 0
    for i in range(n_aa):
        raw = st["ad"]
        if i == 0:
            raw += demolish
            if st["dmp"]:
                raw += 80.0
        if st["hull"] and (i + 1) % 4 == 0:
            raw += skipper_raw(st["base_ad"], st["max_hp"])
            skippers += 1
        if st["titanic"] and titanic_cd <= 0:
            raw += titanic_onhit(st["bonus_hp"])
            titanic_cd = 1.75
        if q_ready and q_cd_left <= 0:
            raw += st["q_bonus"]
            qs += 1
            q_ready = False
            q_cd_left = st["q_cd"]
        elif st["sheen"] > 0 and sheen_ready:
            raw += st["sheen"] * st["base_ad"]
            sheen_ready = False
        total += phys_after_armor(raw, armor, st["pct_pen"])
        titanic_cd -= interval
        q_cd_left -= interval
        t += interval
        if st["q_bonus"] > 0 and q_cd_left <= 0:
            q_ready = True
        if st["sheen"] > 0 and t >= 7.0:
            sheen_ready = True
    hp = turret_hp(kind)
    return {
        "damage": total,
        "demolish": phys_after_armor(demolish, armor, st["pct_pen"]),
        "hp": st["max_hp"],
        "aas": float(n_aa),
        "skippers": float(skippers),
        "qs": float(qs),
        "tta": hp / max(1.0, total / SIEGE_SECONDS),
        "kill": total >= hp,
    }


def main() -> None:
    minutes = (8, 12, 16, 20)
    rows: Dict[str, Dict[int, Dict]] = {n: {} for n in CHAMPS}
    for m in minutes:
        gold = gold_at_minute(m)
        inv = resolve_inventory(BUILD_PATHS[PATH], gold)
        for name in CHAMPS:
            st = champ_stats(name, inv, m)
            outer = window(st, "outer")
            inner = window(st, "inner")
            rows[name][m] = {
                "items": [i.name for i in inv],
                "hp": round(st["max_hp"]),
                "glory": round(st["glory"]),
                "stacks": round(st["stacks"]),
                "as": round(st["as"], 2),
                "outer": round(outer["damage"]),
                "inner": round(inner["damage"]),
                "demolish": round(outer["demolish"]),
                "skippers": int(outer["skippers"]),
                "qs": int(outer["qs"]),
                "tta_outer": round(outer["tta"], 1),
            }

    lines: List[str] = []
    a = lines.append
    a("=" * 76)
    a("HULLBREAKER + DEMOLISH — tướng nào khớp 'không đánh, đi vòng phá trụ'")
    a("Cùng path: Hullbreaker → Trinity → Titanic. Cửa sổ 8s lính đại bác.")
    a("=" * 76)
    a("")
    a(f"  {'Tướng':<14} {'8:00':>7} {'12:00':>7} {'16:00':>7} {'20:00':>7}  HP@20  Demo")
    order = sorted(CHAMPS, key=lambda n: rows[n][20]["outer"], reverse=True)
    for name in order:
        r = rows[name]
        a(
            f"  {name:<14} {r[8]['outer']:7d} {r[12]['outer']:7d} "
            f"{r[16]['outer']:7d} {r[20]['outer']:7d}  {r[20]['hp']:4d}  {r[20]['demolish']}"
        )
    a("")
    a(f"  Sion Glory HP @20: {rows['Sion'][20]['glory']}")
    a(f"  Nasus Q stacks @20: {rows['Nasus'][20]['stacks']}  Q in window: {rows['Nasus'][20]['qs']}")
    a("  Tryndamere: crit không ăn trụ — chỉ AS + Skipper.")
    a("")
    # Sion AS ratio 0.667 — Trinity AS is weak; test HP path.
    gold20 = gold_at_minute(20)
    inv_hp = resolve_inventory(BUILD_PATHS["Hull → Warmog → DMP (tank circle)"], gold20)
    st_hp = champ_stats("Sion", inv_hp, 20)
    w_hp = window(st_hp, "outer")
    a(
        f"  Sion Hull→Warmog→DMP @20: outer {round(w_hp['damage'])}  HP {round(st_hp['max_hp'])}  "
        f"Demo {round(w_hp['demolish'])}  items: {', '.join(i.name for i in inv_hp)}"
    )
    a("")
    a("FIT (lối chơi, không chỉ DPS):")
    a("  Sion     — last-hit = HP = Demolish. R analog đi trụ khác. Q gồng wave.")
    a("             Chết vẫn zombie AA trụ (50% dmg). Đã map MB03 gồng.")
    a("  Nasus    — Q stack ăn trụ, Wither nếu chúng tới (phản ứng, không all-in).")
    a("             Không dash; đi vòng chậm. Ngồi một trụ hơn là xoay map.")
    a("  Trynd    — AA nhanh, E thoát. Kit sống nhờ 1v1 + R bất tử = chủ động đánh.")
    a("             Crit phí trên trụ. Fury kém nếu không combat.")
    a("  Pantheon — W-Q và R vào fight. Pen trụ có, nhưng kit kéo bạn all-in.")
    a("")
    a("VERDICT: Sion.")
    text = "\n".join(lines) + "\n"
    print(text)
    with open("champ_compare.txt", "w", encoding="utf-8") as f:
        f.write(text)
    with open("champ_compare.json", "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
