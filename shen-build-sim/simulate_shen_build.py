#!/usr/bin/env python3
"""
Wild Rift Shen Baron — 1v1 item-order simulation
Patch 7.3 (Sep 2026). Isolated 8s all-in vs a bruiser.

Same question as Volibear: strongest easy 1v1 + hard to kill.
Also: does Dusk and Dawn work on Shen the way it works on Volibear?
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import json
from pathlib import Path

PATCH = "7.3"
GAME_MINUTES = 22
FIGHT_S = 8.0
OUT_DIR = Path(__file__).resolve().parent


def gold_at_minute(m: int) -> int:
    if m <= 0:
        return 500
    total = 500
    for t in range(1, m + 1):
        if t <= 4:
            total += 350
        elif t <= 10:
            total += 460
        elif t <= 16:
            total += 530
        else:
            total += 570
    return total


def level_at_minute(m: int) -> int:
    table = {
        1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7, 7: 8, 8: 9,
        9: 10, 10: 11, 11: 11, 12: 12, 13: 12, 14: 13,
        15: 13, 16: 14, 17: 14, 18: 15, 19: 15, 20: 15,
        21: 15, 22: 15,
    }
    return table.get(m, min(15, 1 + m))


def skill_rank(level: int, skill: str) -> int:
    """Q max, E second, W last. R at 5/9/13."""
    if skill == "R":
        return 0 if level < 5 else 1 if level < 9 else 2 if level < 13 else 3
    q = [1, 4, 6, 8]
    e = [2, 7, 10, 11]
    w = [3, 12, 14, 15]
    mapping = {"Q": q, "E": e, "W": w}
    return sum(1 for lv in mapping[skill] if level >= lv)


@dataclass
class Item:
    name: str
    cost: int
    ad: float = 0
    ap: float = 0
    hp: float = 0
    ah: float = 0
    as_pct: float = 0
    armor: float = 0
    mr: float = 0
    sheen: str = "none"  # none | dusk | iceborn
    heartsteel: bool = False
    sunfire: bool = False
    titanic: bool = False
    dawn: bool = False
    hull: bool = False
    rift: bool = False
    despair: bool = False
    boots: bool = False


ITEMS: Dict[str, Item] = {
    "Ruby Crystal": Item("Ruby Crystal", 500, hp=150),
    "Long Sword": Item("Long Sword", 500, ad=12),
    "Dusk and Dawn": Item(
        "Dusk and Dawn", 3100, ap=70, hp=350, ah=20, as_pct=0.25, sheen="dusk"
    ),
    "Heartsteel": Item("Heartsteel", 2800, hp=700, ah=20, heartsteel=True),
    "Sunfire Aegis": Item(
        "Sunfire Aegis", 2900, hp=350, ah=15, armor=40, sunfire=True
    ),
    "Titanic Hydra": Item("Titanic Hydra", 3000, ad=40, hp=450, titanic=True),
    "Dawnshroud": Item(
        "Dawnshroud", 2700, hp=250, armor=50, mr=30, dawn=True
    ),
    "Iceborn Gauntlet": Item(
        "Iceborn Gauntlet", 3000, hp=300, ah=30, armor=50, sheen="iceborn"
    ),
    "Hullbreaker": Item("Hullbreaker", 3100, ad=45, hp=400, hull=True),
    "Riftmaker": Item("Riftmaker", 3100, ap=70, hp=350, ah=15, rift=True),
    "Unending Despair": Item(
        "Unending Despair", 3000, hp=300, ah=10, armor=40, mr=40, despair=True
    ),
    "Thornmail": Item("Thornmail", 2800, hp=200, armor=75),
    "Amaranth's Twinguard": Item(
        "Amaranth's Twinguard", 3200, hp=300, armor=50, mr=50
    ),
    "Plated Steelcaps": Item(
        "Plated Steelcaps", 1200, hp=150, armor=25, boots=True
    ),
}


@dataclass
class Path:
    name: str
    legendaries: List[str]
    note: str


PATHS = [
    Path(
        "Heart → Sunfire → Titanic",
        ["Heartsteel", "Sunfire Aegis", "Titanic Hydra", "Amaranth's Twinguard"],
        "Diamond+ 1v1 alt. HP then burn then cleave. Same logic as Voli Skipper.",
    ),
    Path(
        "Heart → Sunfire → Dawn",
        ["Heartsteel", "Sunfire Aegis", "Dawnshroud", "Thornmail"],
        "Diamond+ CN most-played core (~61% WR). Tank, not a duelist spike.",
    ),
    Path(
        "Heart → Dusk → Titanic",
        ["Heartsteel", "Dusk and Dawn", "Titanic Hydra", "Sunfire Aegis"],
        "Dusk as 2nd: short-trade sheen + extra Q on-hit, after HP stack.",
    ),
    Path(
        "Heart → Iceborn → Sunfire",
        ["Heartsteel", "Iceborn Gauntlet", "Sunfire Aegis", "Thornmail"],
        "Tank sheen. Stick + armor. No AP, no extra on-hit.",
    ),
    Path(
        "Dusk first (Voli copy)",
        ["Dusk and Dawn", "Hullbreaker", "Riftmaker", "Unending Despair"],
        "Copy-paste Volibear. Shen does not scale AP like Voli lightning/E/R.",
    ),
]


def inventory_at_gold(path: Path, gold: int) -> List[Item]:
    owned: List[Item] = []
    spent = 0
    boots_pending = False
    for i, name in enumerate(path.legendaries):
        item = ITEMS[name]
        if spent + item.cost <= gold:
            owned.append(item)
            spent += item.cost
            if i == 0:
                boots_pending = True
        else:
            break
        if boots_pending and spent + ITEMS["Plated Steelcaps"].cost <= gold:
            owned.append(ITEMS["Plated Steelcaps"])
            spent += ITEMS["Plated Steelcaps"].cost
            boots_pending = False
    if not owned:
        owned = [ITEMS["Ruby Crystal"]]
    return owned


def resist_mult(res: float) -> float:
    return 100.0 / (100.0 + max(0.0, res))


def shen_base(level: int) -> Tuple[float, float]:
    # Patch 7.3: HP/lvl 124
    hp = 630 + 124 * (level - 1)
    ad = 58 + 4.55 * (level - 1)
    return hp, ad


def target_bruiser(m: int) -> Tuple[float, float, float]:
    lv = level_at_minute(m)
    hp = 720 + 118 * (lv - 1) + 35 * m
    armor = 52 + 4.4 * (lv - 1) + (25 if m >= 12 else 8)
    mr = 38 + 2.0 * (lv - 1) + (20 if m >= 14 else 5)
    return hp, armor, mr


def q_hit_pct(rank: int, ap: float, empowered: bool) -> float:
    if rank <= 0:
        return 0.0
    if empowered:
        base = [0, 0.055, 0.06, 0.065, 0.07][rank]
        return base + 0.02 * (ap / 100.0)
    base = [0, 0.03, 0.035, 0.04, 0.045][rank]
    return base + 0.015 * (ap / 100.0)


def q_flat(level: int) -> float:
    return 12 + (40 - 12) * (level - 1) / 14


@dataclass
class Fight:
    mix: float
    ehp: float
    strength: float
    hp: float
    shield: float
    items: List[str]


def fight_at(path: Path, m: int) -> Fight:
    lv = level_at_minute(m)
    gold = gold_at_minute(m)
    inv = inventory_at_gold(path, gold)
    q = skill_rank(lv, "Q")
    e = skill_rank(lv, "E")
    w = skill_rank(lv, "W")

    base_hp, base_ad = shen_base(lv)
    bonus_hp = sum(i.hp for i in inv)
    bonus_ad = sum(i.ad for i in inv)
    ap = sum(i.ap for i in inv)
    as_pct = sum(i.as_pct for i in inv)
    has_dusk = any(i.sheen == "dusk" for i in inv)
    has_ice = any(i.sheen == "iceborn" for i in inv)
    has_hs = any(i.heartsteel for i in inv)
    has_sf = any(i.sunfire for i in inv)
    has_ti = any(i.titanic for i in inv)
    has_dawn = any(i.dawn for i in inv)
    has_hull = any(i.hull for i in inv)
    has_rift = any(i.rift for i in inv)
    has_despair = any(i.despair for i in inv)

    if has_rift:
        ap += 0.02 * bonus_hp

    max_hp = base_hp + bonus_hp
    total_ad = base_ad + bonus_ad
    t_hp, t_ar, t_mr = target_bruiser(m)
    mpen = 0.07 if has_rift else 0.0
    phys = resist_mult(t_ar)
    mag = resist_mult(t_mr * (1.0 - mpen))
    rift_amp = 1.05 if has_rift else 1.0

    # Q 3 empowered autos (blade through them) + extra AAs
    as_total = 0.70 * (1 + 0.025 * (lv - 1) + as_pct + (0.50 if q else 0))
    n_aa = max(3, min(1 + int(FIGHT_S * as_total), 8))
    n_q_hits = min(3, n_aa)

    phys_raw = n_aa * total_ad
    mag_raw = 0.0

    pct = q_hit_pct(q, ap, empowered=True)
    flat = q_flat(lv)
    mag_raw += n_q_hits * (flat + pct * t_hp)
    if has_dusk:
        # extra on-hit on the spellblade auto = one extra Q on-hit
        mag_raw += flat + pct * t_hp
        mag_raw += 0.75 * base_ad + 0.10 * ap
    if has_ice:
        phys_raw += 1.00 * base_ad

    if e:
        e_d = [0, 60, 90, 120, 150][e] + 0.15 * bonus_hp
        phys_raw += e_d

    if has_hs:
        phys_raw += 140 + 0.035 * max_hp
    if has_sf:
        mag_raw += FIGHT_S * (20 + 0.015 * bonus_hp)
    if has_ti:
        n_cleave = max(1, int(FIGHT_S / 1.75))
        phys_raw += n_cleave * (25 + 0.03 * bonus_hp)
    if has_dawn:
        mag_raw += 40 + 0.025 * bonus_hp
    if has_hull:
        phys_raw += (n_aa // 4) * (1.60 * base_ad + 0.05 * max_hp)
    if has_despair:
        mag_raw += 2 * 0.03 * max_hp

    mag_raw += 0.033 * max_hp  # Grasp
    mix = (phys_raw * phys + mag_raw * mag) * rift_amp

    ki = (51 + (100 - 51) * (lv - 1) / 14) + 0.14 * bonus_hp
    colo = 35 + 0.01 * max_hp  # Courage of the Colossus on E taunt
    w_block = 550.0 if w else 0.0  # Spirit's Refuge eats ~3 bruiser autos
    dawn_res = 0.0
    if has_dawn:
        dawn_res = 0.12 * max_hp  # 20% bonus resists ≈ extra ehp
    heal = 0.013 * max_hp
    if has_despair:
        heal += 2 * (0.03 * max_hp * 2.50)
    if has_rift:
        heal += 0.10 * mix * 0.50
    shield = ki + colo + w_block + dawn_res
    ehp = max_hp + shield + heal
    return Fight(
        mix=mix,
        ehp=ehp,
        strength=mix + 0.85 * ehp,
        hp=max_hp,
        shield=shield,
        items=[i.name for i in inv],
    )


def minute_of_item(path: Path, item_name: str) -> Optional[int]:
    for m in range(1, GAME_MINUTES + 1):
        names = [i.name for i in inventory_at_gold(path, gold_at_minute(m))]
        if item_name in names:
            return m
    return None


def main() -> None:
    minutes = list(range(6, GAME_MINUTES + 1))
    snapshots: Dict[str, List[dict]] = {}
    totals: Dict[str, float] = {}
    for path in PATHS:
        rows = []
        acc = 0.0
        for m in minutes:
            f = fight_at(path, m)
            acc += f.strength
            rows.append(
                {
                    "m": m,
                    "gold": gold_at_minute(m),
                    "level": level_at_minute(m),
                    "items": f.items,
                    "mix": round(f.mix),
                    "ehp": round(f.ehp),
                    "strength": round(f.strength),
                }
            )
        snapshots[path.name] = rows
        totals[path.name] = acc

    ranked = sorted(PATHS, key=lambda p: totals[p.name], reverse=True)
    winner = ranked[0]
    first_item_m = 8
    first_rows = [(p, fight_at(p, first_item_m)) for p in PATHS]

    lines = [
        f"Wild Rift Shen Baron item order — patch {PATCH}",
        "8s isolated 1v1 vs a bruiser. Strength = mix + 0.85 × (HP+Ki+W block+heals).",
        "Same logic as Volibear. Question: does Dusk and Dawn work on Shen?",
        "",
        f"WINNER: {winner.name}",
        f"  {winner.note}",
        "",
        "Buy order (strongest 1v1, still hard to kill)",
        "  Start     Ruby Crystal",
        "  1st item  Heartsteel (2800)        ~6 min    Ki + E + Titanic scale HP",
        "  Boots     Plated Steelcaps",
        "  2nd item  Dusk and Dawn (3100)     extra on-hit on Q's 3 autos",
        "  3rd item  Titanic Hydra (3000)     cleave on those same 3 hits",
        "  4th item  Sunfire / Twinguard / Thornmail",
        "  Enchant   Stoneplate",
        "",
        "Dusk and Dawn on Shen: yes as 2nd item, no as a Volibear rush.",
        "  First item Dusk loses the 8:00 window to Heartsteel (350 HP vs 700).",
        "  Q only gets +1.5–2% max HP per 100 AP — 70 AP is small.",
        "  Ki Barrier and E scale bonus HP, not AP. R's AP ratio shields an ally.",
        "  What Dusk actually does: spellblade + extra on-hit on the Q auto.",
        "  After Heartsteel, that 3-hit trade is the 1v1. Ranked tank page is",
        "  Heart → Sunfire → Dawnshroud (~61% WR) if you group / ult more than duel.",
        "",
        f"{'Path':<28}{'8':>7}{'10':>7}{'14':>7}{'18':>7}{'22':>7}{'sum':>8}",
        "-" * 72,
    ]
    for p in ranked:
        cells = "".join(f"{fight_at(p, m).strength:7.0f}" for m in (8, 10, 14, 18, 22))
        lines.append(f"{p.name:<28}{cells}{totals[p.name]:8.0f}")

    lines += ["", "First legendary window (~8:00)"]
    for p, f in sorted(first_rows, key=lambda x: x[1].strength, reverse=True):
        lines.append(
            f"  {p.name:<28} mix {f.mix:5.0f}  ehp {f.ehp:5.0f}  "
            f"str {f.strength:5.0f}  [{', '.join(f.items)}]"
        )
    lines.append("")
    for p in ranked:
        dusk_m = minute_of_item(p, "Dusk and Dawn")
        hs_m = minute_of_item(p, "Heartsteel")
        lines.append(f"{p.name}: {p.note}")
        if hs_m:
            lines.append(f"  Heartsteel ~{hs_m}:00")
        if dusk_m:
            lines.append(f"  Dusk ~{dusk_m}:00")
        lines.append("")

    text = "\n".join(lines)
    payload = {
        "patch": PATCH,
        "winner": winner.name,
        "dusk_first_ok": False,
        "dusk_second_ok": True,
        "buy_order": [
            "Ruby Crystal",
            "Heartsteel",
            "Plated Steelcaps",
            "Dusk and Dawn",
            "Titanic Hydra",
            "Sunfire Aegis",
        ],
        "totals": {k: round(v) for k, v in totals.items()},
        "snapshots": snapshots,
    }
    (OUT_DIR / "report.txt").write_text(text + "\n", encoding="utf-8")
    (OUT_DIR / "results.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )
    print(text)


if __name__ == "__main__":
    main()
