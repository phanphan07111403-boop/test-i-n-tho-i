#!/usr/bin/env python3
"""
Wild Rift Pantheon Baron — Hullbreaker + Demolish siege sim
Patch 7.2+ item/rune snapshot (Sep 2026).

Playstyle: do not start fights. Circle empty side lanes, crash a
cannon wave, stand 3s for Demolish, auto the turret, leave when
anyone rotates. R is a teleport to the next empty tower, not a 5v5.

Question: which purchase order peaks turret damage in an 8s cannon
window while stacking HP for Demolish + Hullbreaker Skipper.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import json
import math

GAME_MINUTES = 20
SIEGE_SECONDS = 8.0


def gold_at_minute(m: int) -> int:
    """Solo-lane farm, plates, turret gold. No kill gold (no combat)."""
    if m <= 0:
        return 500
    total = 500
    for t in range(1, m + 1):
        if t <= 5:
            total += 360
        elif t <= 12:
            total += 500
        else:
            total += 560
        # First outer ~11:00, second side ~16:00 — this playstyle's only extra gold.
        if t == 11:
            total += 450
        if t == 16:
            total += 450
    return total


def level_at_minute(m: int) -> int:
    table = {
        1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7, 7: 8, 8: 9,
        9: 10, 10: 11, 11: 11, 12: 12, 13: 12, 14: 13,
        15: 13, 16: 14, 17: 14, 18: 15, 19: 15, 20: 15,
    }
    return table.get(m, min(15, 1 + m))


def r_rank(level: int) -> int:
    if level >= 13:
        return 3
    if level >= 9:
        return 2
    if level >= 5:
        return 1
    return 0


def panth_base_hp(level: int) -> float:
    return 690 + 120 * (level - 1)


def panth_base_ad(level: int) -> float:
    return 64 + 3.6 * (level - 1)


def panth_base_as(level: int) -> float:
    return 0.80 * (1.0 + 0.022 * (level - 1))


def overgrowth_hp(minute: int, bonus_hp: float, base_hp: float) -> float:
    """Enemy wave deaths in vision. 7.2: 3 HP per 3 minions; 3% at 30 stacks."""
    waves = max(0, minute - 1)
    stacks = min(80, int(waves * 6 / 3))
    flat = 3.0 * stacks
    pct = 0.03 if stacks >= 30 else 0.0
    return flat + pct * (base_hp + bonus_hp + flat)


def turret_armor(kind: str) -> float:
    if kind == "outer":
        return 60.0
    if kind == "inner":
        return 15.0
    return 30.0


def turret_hp(kind: str) -> float:
    if kind == "outer":
        return 4200.0
    if kind == "inner":
        return 3600.0
    return 3000.0


def phys_after_armor(raw: float, armor: float, pct_pen: float) -> float:
    effective = max(0.0, armor * (1.0 - pct_pen))
    return raw * 100.0 / (100.0 + effective)


@dataclass
class Item:
    name: str
    cost: int
    ad: float = 0
    hp: float = 0
    as_pct: float = 0
    ah: float = 0
    lethality: float = 0
    pct_pen: float = 0
    hull: bool = False
    trinity: bool = False
    titanic: bool = False
    dmp: bool = False
    tags: Tuple[str, ...] = ()


ITEMS: Dict[str, Item] = {
    "Doran's Shield": Item("Doran's Shield", 450, hp=80),
    "Long Sword": Item("Long Sword", 500, ad=12),
    "Ruby Crystal": Item("Ruby Crystal", 500, hp=150),
    "Jaurim's Fist": Item("Jaurim's Fist", 1200, ad=15, hp=200),
    "Pickaxe": Item("Pickaxe", 875, ad=25),
    "Boots": Item("Boots", 500, tags=("boots",)),
    "Mercury's Treads": Item("Mercury's Treads", 1100, tags=("boots",)),
    "Hullbreaker": Item(
        "Hullbreaker", 3100, ad=50, hp=400, hull=True, tags=("siege",)
    ),
    "Trinity Force": Item(
        "Trinity Force",
        3333,
        ad=30,
        hp=333,
        as_pct=0.30,
        ah=20,
        trinity=True,
        tags=("siege",),
    ),
    "Titanic Hydra": Item(
        "Titanic Hydra", 3000, ad=40, hp=450, titanic=True, tags=("siege", "hp")
    ),
    "Warmog's Armor": Item("Warmog's Armor", 2850, hp=700, ah=20, tags=("hp",)),
    "Dead Man's Plate": Item(
        "Dead Man's Plate", 2800, hp=350, dmp=True, tags=("circle", "hp")
    ),
    "Sterak's Gage": Item("Sterak's Gage", 3200, hp=400, tags=("hp",)),
    "Eclipse": Item("Eclipse", 2800, ad=60, lethality=18, tags=("combat",)),
    "Black Cleaver": Item(
        "Black Cleaver", 3000, ad=40, hp=350, ah=25, tags=("combat",)
    ),
    "Youmuu's Ghostblade": Item(
        "Youmuu's Ghostblade", 2700, ad=55, lethality=18, tags=("combat",)
    ),
    "Caulfield's Warhammer": Item("Caulfield's Warhammer", 1100, ad=20, ah=10),
    "Sheen": Item("Sheen", 700, tags=("spellblade",)),
    "Phage": Item("Phage", 1100, ad=15, hp=200),
}


UPGRADE_COMPONENTS = {
    "Mercury's Treads": ("Boots",),
    "Hullbreaker": ("Jaurim's Fist", "Jaurim's Fist"),
    "Trinity Force": ("Sheen", "Phage", "Sheen"),
    "Titanic Hydra": ("Jaurim's Fist", "Ruby Crystal"),
    "Warmog's Armor": ("Ruby Crystal", "Ruby Crystal"),
    "Dead Man's Plate": ("Ruby Crystal",),
    "Sterak's Gage": ("Ruby Crystal",),
    "Eclipse": ("Long Sword", "Long Sword"),
    "Black Cleaver": ("Phage", "Caulfield's Warhammer"),
    "Youmuu's Ghostblade": ("Long Sword", "Caulfield's Warhammer"),
}

NEXT_COMPONENTS: Dict[str, List[str]] = {
    "Hullbreaker": ["Jaurim's Fist", "Jaurim's Fist"],
    "Trinity Force": ["Sheen", "Phage"],
    "Titanic Hydra": ["Jaurim's Fist", "Ruby Crystal"],
    "Warmog's Armor": ["Ruby Crystal", "Ruby Crystal"],
    "Dead Man's Plate": ["Ruby Crystal"],
    "Sterak's Gage": ["Ruby Crystal"],
    "Mercury's Treads": ["Boots"],
    "Eclipse": ["Long Sword"],
    "Black Cleaver": ["Phage", "Caulfield's Warhammer"],
    "Youmuu's Ghostblade": ["Caulfield's Warhammer"],
}


BUILD_PATHS: Dict[str, List[str]] = {
    "Hull → Trinity → Titanic (Siege)": [
        "Doran's Shield",
        "Jaurim's Fist",
        "Boots",
        "Jaurim's Fist",
        "Hullbreaker",
        "Mercury's Treads",
        "Sheen",
        "Phage",
        "Trinity Force",
        "Titanic Hydra",
        "Dead Man's Plate",
    ],
    "Hull → Titanic → Warmog (HP)": [
        "Doran's Shield",
        "Jaurim's Fist",
        "Boots",
        "Jaurim's Fist",
        "Hullbreaker",
        "Mercury's Treads",
        "Ruby Crystal",
        "Titanic Hydra",
        "Warmog's Armor",
        "Dead Man's Plate",
    ],
    "Hull → Trinity → Warmog": [
        "Doran's Shield",
        "Jaurim's Fist",
        "Boots",
        "Hullbreaker",
        "Mercury's Treads",
        "Sheen",
        "Trinity Force",
        "Warmog's Armor",
        "Dead Man's Plate",
    ],
    "Hull → Warmog → DMP (tank circle)": [
        "Doran's Shield",
        "Jaurim's Fist",
        "Boots",
        "Hullbreaker",
        "Mercury's Treads",
        "Ruby Crystal",
        "Warmog's Armor",
        "Dead Man's Plate",
        "Titanic Hydra",
    ],
    "Trinity → Hull → Titanic": [
        "Doran's Shield",
        "Sheen",
        "Boots",
        "Phage",
        "Trinity Force",
        "Mercury's Treads",
        "Jaurim's Fist",
        "Hullbreaker",
        "Titanic Hydra",
        "Dead Man's Plate",
    ],
    "Eclipse → Cleaver → Youmuu (combat)": [
        "Doran's Shield",
        "Long Sword",
        "Boots",
        "Eclipse",
        "Mercury's Treads",
        "Phage",
        "Black Cleaver",
        "Youmuu's Ghostblade",
        "Sterak's Gage",
    ],
}


def _count(names: List[str], name: str) -> int:
    return sum(1 for n in names if n == name)


def credit_for(item_name: str, owned: List[str]) -> Tuple[int, List[str]]:
    needed = list(UPGRADE_COMPONENTS.get(item_name, ()))
    credit = 0
    remove: List[str] = []
    owned_copy = list(owned)
    for c in needed:
        if c in owned_copy:
            credit += ITEMS[c].cost
            remove.append(c)
            owned_copy.remove(c)
    # Trinity recipe on wiki is Sheen+Phage+kindle; treat 1 Sheen + Phage.
    if item_name == "Trinity Force":
        credit = 0
        remove = []
        owned_copy = list(owned)
        for c in ("Sheen", "Phage"):
            if c in owned_copy:
                credit += ITEMS[c].cost
                remove.append(c)
                owned_copy.remove(c)
    if item_name == "Hullbreaker":
        credit = 0
        remove = []
        owned_copy = list(owned)
        taken = 0
        for i, n in enumerate(list(owned_copy)):
            if n == "Jaurim's Fist" and taken < 2:
                credit += ITEMS[n].cost
                remove.append(n)
                taken += 1
    return credit, remove


def resolve_inventory(path: List[str], gold: int) -> List[Item]:
    owned: List[str] = []
    pool = gold

    def try_buy(name: str) -> bool:
        nonlocal pool
        if name not in ITEMS:
            return False
        credit, remove = credit_for(name, owned)
        price = ITEMS[name].cost - credit
        if pool >= price:
            for r in remove:
                if r in owned:
                    owned.remove(r)
            owned.append(name)
            pool -= price
            return True
        return False

    for name in path:
        if name in owned and name not in ("Jaurim's Fist", "Ruby Crystal", "Long Sword", "Sheen"):
            continue
        try_buy(name)

    # leftover: components of the next unfinished legendary
    for name in path:
        if name in owned:
            continue
        for comp in NEXT_COMPONENTS.get(name, []):
            if pool >= ITEMS[comp].cost:
                owned.append(comp)
                pool -= ITEMS[comp].cost
            else:
                break
        break
    return [ITEMS[n] for n in owned]


def stats_from_items(
    items: List[Item], level: int, minute: int
) -> Dict[str, float]:
    ad = panth_base_ad(level)
    base_ad = panth_base_ad(level)
    hp_item = 0.0
    as_pct = 0.0
    lethality = 0.0
    pct_pen = 0.10 * r_rank(level)  # R passive
    hull = False
    trinity = False
    titanic = False
    dmp = False
    for it in items:
        ad += it.ad
        hp_item += it.hp
        as_pct += it.as_pct
        lethality += it.lethality
        pct_pen += it.pct_pen
        hull = hull or it.hull
        trinity = trinity or it.trinity
        titanic = titanic or it.titanic
        dmp = dmp or it.dmp
        if it.name == "Sheen":
            trinity = True  # spellblade at 100% base if unfinished; treat as 100%
    sheen_ratio = 2.0 if any(i.trinity for i in items) else (
        1.0 if any(i.name == "Sheen" for i in items) else 0.0
    )
    base_hp = panth_base_hp(level)
    og = overgrowth_hp(minute, hp_item, base_hp)
    max_hp = base_hp + hp_item + og
    alacrity = 0.12
    attack_speed = panth_base_as(level) + 0.80 * (as_pct + alacrity)
    return {
        "ad": ad,
        "base_ad": base_ad,
        "max_hp": max_hp,
        "bonus_hp": hp_item + og,
        "as": attack_speed,
        "lethality": lethality,
        "pct_pen": min(0.45, pct_pen),
        "hull": 1.0 if hull else 0.0,
        "sheen": sheen_ratio,
        "titanic": 1.0 if titanic else 0.0,
        "dmp": 1.0 if dmp else 0.0,
    }


def demolish_raw(max_hp: float) -> float:
    return 100.0 + 0.22 * max_hp


def skipper_raw(base_ad: float, max_hp: float) -> float:
    return 2.40 * base_ad + 0.09 * max_hp


def titanic_onhit(bonus_hp: float) -> float:
    return 25.0 + 0.03 * bonus_hp


def siege_window(stats: Dict[str, float], kind: str = "outer") -> Dict[str, float]:
    armor = max(0.0, turret_armor(kind) - stats["lethality"])
    n_aa = max(1, int(round(stats["as"] * SIEGE_SECONDS)))
    # Walk-up already charged Demolish (3s with the wave).
    demolish = demolish_raw(stats["max_hp"])
    total = 0.0
    skippers = 0
    sheens = 0
    titanics = 0
    # One Q tap on the turret to proc Sheen (waveclear leftover / melee stab).
    q_done = False
    titanic_cd = 0.0
    sheen_cd = 0.0
    t = 0.0
    interval = 1.0 / max(0.5, stats["as"])
    for i in range(n_aa):
        raw = stats["ad"]
        if i == 0:
            raw += demolish
            if stats["dmp"]:
                raw += 80.0  # momentum leftover after walking up
        if stats["hull"] and (i + 1) % 4 == 0:
            raw += skipper_raw(stats["base_ad"], stats["max_hp"])
            skippers += 1
        if stats["titanic"] and titanic_cd <= 0:
            raw += titanic_onhit(stats["bonus_hp"])
            titanics += 1
            titanic_cd = 1.75
        if stats["sheen"] > 0 and not q_done:
            raw += stats["sheen"] * stats["base_ad"]
            sheens += 1
            q_done = True
            sheen_cd = 1.5
        total += phys_after_armor(raw, armor, stats["pct_pen"])
        titanic_cd -= interval
        sheen_cd -= interval
        t += interval
        # Second Sheen if Q comes back (~7s) and window still open.
        if stats["sheen"] > 0 and q_done and t >= 7.0 and sheen_cd <= 0:
            q_done = False
    hp = turret_hp(kind)
    return {
        "damage": total,
        "aas": float(n_aa),
        "skippers": float(skippers),
        "sheens": float(sheens),
        "titanics": float(titanics),
        "demolish": phys_after_armor(demolish, armor, stats["pct_pen"]),
        "hp": stats["max_hp"],
        "kill": 1.0 if total >= hp else 0.0,
        "tta": hp / max(1.0, total / SIEGE_SECONDS),
    }


def run() -> Dict:
    minutes = list(range(1, GAME_MINUTES + 1))
    per_build: Dict[str, List[Dict]] = {k: [] for k in BUILD_PATHS}
    for m in minutes:
        gold = gold_at_minute(m)
        lv = level_at_minute(m)
        for name, path in BUILD_PATHS.items():
            inv = resolve_inventory(path, gold)
            st = stats_from_items(inv, lv, m)
            outer = siege_window(st, "outer")
            inner = siege_window(st, "inner")
            per_build[name].append(
                {
                    "minute": m,
                    "gold": gold,
                    "level": lv,
                    "items": [i.name for i in inv],
                    "hp": round(st["max_hp"]),
                    "ad": round(st["ad"], 1),
                    "as": round(st["as"], 2),
                    "outer": round(outer["damage"]),
                    "inner": round(inner["damage"]),
                    "demolish": round(outer["demolish"]),
                    "skippers": int(outer["skippers"]),
                    "kill_outer": bool(outer["kill"]),
                    "tta_outer": round(outer["tta"], 1),
                }
            )

    def avg(name: str, key: str, start: int = 8) -> float:
        rows = [r for r in per_build[name] if r["minute"] >= start]
        return sum(r[key] for r in rows) / max(1, len(rows))

    ranking = sorted(
        BUILD_PATHS,
        key=lambda n: avg(n, "outer"),
        reverse=True,
    )
    return {
        "gold_curve": [{"minute": m, "gold": gold_at_minute(m), "level": level_at_minute(m)} for m in minutes],
        "builds": per_build,
        "ranking": ranking,
        "avg_outer_8_20": {n: round(avg(n, "outer")) for n in BUILD_PATHS},
    }


def fmt_items(names: List[str]) -> str:
    return " › ".join(names) if names else "(empty)"


def write_report(data: Dict) -> str:
    lines: List[str] = []
    a = lines.append
    a("=" * 78)
    a("PANTHEON — HULLBREAKER + DEMOLISH  (Wild Rift 7.2+)")
    a("Playstyle: no all-in. Circle empty turrets. Cannon wave 8s window.")
    a("Metric: physical damage to outer turret / 8s  |  HP fuels Demolish + Skipper")
    a("=" * 78)
    a("")
    a("GOLD / LEVEL (no kill gold)")
    a("  Min    Gold  Lvl")
    for row in data["gold_curve"]:
        if row["minute"] in (1, 4, 6, 8, 10, 12, 16, 20):
            a(f"  {row['minute']:4d}   {row['gold']:5d}   {row['level']:2d}")
    a("")
    a("-" * 78)
    a("MINUTE-BY-MINUTE OPTIMAL (outer turret 8s)")
    a("-" * 78)
    best_name = data["ranking"][0]
    for m in range(1, GAME_MINUTES + 1):
        scored = []
        for name in BUILD_PATHS:
            row = data["builds"][name][m - 1]
            scored.append((row["outer"], name, row))
        scored.sort(key=lambda x: (x[0], 1 if x[1].startswith("Hull") else 0), reverse=True)
        dmg, name, row = scored[0]
        hull = "Hull" if any("Hullbreaker" in x for x in [row["items"]]) or "Hullbreaker" in row["items"] else ""
        note = []
        if "Hullbreaker" in row["items"]:
            note.append("Skipper")
        if "Trinity Force" in row["items"] or "Sheen" in row["items"]:
            note.append("Sheen")
        if "Titanic Hydra" in row["items"]:
            note.append("Titanic")
        a(
            f"  {m:2d}:00 | outer {row['outer']:5d} | inner {row['inner']:5d} | "
            f"HP {row['hp']:4d} | Demo {row['demolish']:3d} | {name}"
        )
        a(f"         items: {fmt_items(row['items'])}")
        if note:
            a(f"         {', '.join(note)}")
    a("")
    a("-" * 78)
    a("BUILD COMPARISON — OUTER TURRET / 8s")
    a("-" * 78)
    a(f"  {'Build':<40} {'8:00':>6} {'12:00':>6} {'16:00':>6} {'20:00':>6}  avg")
    for name in data["ranking"]:
        rows = data["builds"][name]
        def at(mm: int) -> int:
            return rows[mm - 1]["outer"]
        a(
            f"  {name:<40} {at(8):6d} {at(12):6d} {at(16):6d} {at(20):6d}  "
            f"{data['avg_outer_8_20'][name]:4d}"
        )
    a("")
    a("-" * 78)
    a("DEMOLISH PROC (after armor) @ 12 / 16 / 20")
    a("-" * 78)
    for name in data["ranking"]:
        rows = data["builds"][name]
        a(
            f"  {name:<40} {rows[11]['demolish']:4d} {rows[15]['demolish']:4d} "
            f"{rows[19]['demolish']:4d}   HP {rows[19]['hp']}"
        )
    a("")
    winner = data["ranking"][0]
    w20 = data["builds"][winner][19]
    combat = data["builds"]["Eclipse → Cleaver → Youmuu (combat)"][19]
    a("-" * 78)
    a("VERDICT")
    a("-" * 78)
    a(f"  Best path (turret window, still Hull+Demolish): {winner}")
    a(f"  20:00 outer/8s: {w20['outer']}   HP {w20['hp']}   Demolish {w20['demolish']}")
    a(f"  Combat Eclipse path 20:00 outer/8s: {combat['outer']}   HP {combat['hp']}")
    a("")
    a("  WHY HULL + HP, NOT ECLIPSE:")
    a("  • Demolish = 100 + 22% max HP / 30s. More HP = bigger proc.")
    a("  • Hullbreaker Skipper = 4th AA vs turret: 240% base AD + 9% max HP.")
    a("  • Both want the same stat. Lethality does not feed Demolish.")
    a("  • Trinity Sheen (200% base AD) after Q is extra turret hit, not combat.")
    a("  • Titanic Cleave tooltip: also applies to turrets, scales bonus HP.")
    a("  • Warmog is Demolish juice + regen while circling; slower autos.")
    a("  • Eclipse/Youmuu: AD/lethality for W-Q all-in. You asked not to take")
    a("    that fight. They lose Skipper and ~700–1000 HP on the proc.")
    a("")
    a("  PLAY (đi vòng, không chủ động combat):")
    a("  1) Q ném wave, không W nhảy người.")
    a("  2) Crash lính đại bác vào trụ trống. Đứng 3s cạnh trụ → AA = Demolish.")
    a("  3) AA đến Skipper (đòn 4). Q đâm trụ nếu Trinity (Sheen).")
    a("  4) Thấy 1 người rotate: analog ra rừng / Ghost. E chặn đòn người,")
    a("     E KHÔNG chặn đạn trụ.")
    a("  5) R = nhảy sang trụ trống lane kia, không R vào 5v5.")
    a("  6) Một mình (Boarding Party). Đồng đội đứng cạnh = mất buff lính.")
    a("")
    text = "\n".join(lines) + "\n"
    return text


def main() -> None:
    data = run()
    report = write_report(data)
    with open("report.txt", "w", encoding="utf-8") as f:
        f.write(report)
    slim = {
        "ranking": data["ranking"],
        "avg_outer_8_20": data["avg_outer_8_20"],
        "snapshots": {
            name: {
                "m8": data["builds"][name][7],
                "m12": data["builds"][name][11],
                "m16": data["builds"][name][15],
                "m20": data["builds"][name][19],
            }
            for name in BUILD_PATHS
        },
    }
    with open("results.json", "w", encoding="utf-8") as f:
        json.dump(slim, f, indent=2, ensure_ascii=False)
    print(report)


if __name__ == "__main__":
    main()
