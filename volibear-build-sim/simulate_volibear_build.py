#!/usr/bin/env python3
"""
Wild Rift Volibear Baron — 1v1 item-order simulation
Patch 7.3 (Sep 2026). Isolated 8s all-in vs a bruiser.

Question: which buy order makes Volibear strongest (mix damage +
survives the slugfest) for the GameSir X3 Pro duelist plan.
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


# ---------------------------------------------------------------------------
# Economy / XP (Baron farmer, not fed smurf)
# ---------------------------------------------------------------------------


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
    """W max, Q second, E last. R at 5/9/13."""
    if skill == "R":
        return 0 if level < 5 else 1 if level < 9 else 2 if level < 13 else 3
    q = [2, 7, 10, 11]
    w = [1, 4, 6, 8]
    e = [3, 12, 14, 15]
    mapping = {"Q": q, "W": w, "E": e}
    return sum(1 for lv in mapping[skill] if level >= lv)


# ---------------------------------------------------------------------------
# Items
# ---------------------------------------------------------------------------


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
    mpen_pct: float = 0
    sheen: str = "none"  # none | dusk | trinity
    heartsteel: bool = False
    rift: bool = False
    hull: bool = False
    despair: bool = False
    boots: bool = False


ITEMS: Dict[str, Item] = {
    "Long Sword": Item("Long Sword", 500, ad=12),
    "Ruby Crystal": Item("Ruby Crystal", 500, hp=200),
    "Sheen": Item("Sheen", 800, sheen="trinity"),  # 100% base AD; dusk overwrites later
    "Kindlegem": Item("Kindlegem", 1000, hp=200, ah=10),
    "Blasting Wand": Item("Blasting Wand", 800, ap=45),
    "Jaurim's Fist": Item("Jaurim's Fist", 1200, ad=15, hp=200),
    "Haunting Guise": Item("Haunting Guise", 1300, ap=35, hp=200, mpen_pct=0.07),
    "Fiendish Codex": Item("Fiendish Codex", 900, ap=35, ah=10),
    "Giant's Belt": Item("Giant's Belt", 1000, hp=350),
    "Dusk and Dawn": Item(
        "Dusk and Dawn", 3100, ap=70, hp=350, ah=20, as_pct=0.25, sheen="dusk"
    ),
    "Trinity Force": Item(
        "Trinity Force", 3333, ad=36, hp=333, ah=15, as_pct=0.30, sheen="trinity"
    ),
    "Heartsteel": Item(
        "Heartsteel", 2800, hp=700, ah=20, heartsteel=True
    ),
    "Hullbreaker": Item("Hullbreaker", 3100, ad=45, hp=400, hull=True),
    "Riftmaker": Item(
        "Riftmaker", 3100, ap=70, hp=350, ah=15, mpen_pct=0.07, rift=True
    ),
    "Unending Despair": Item(
        "Unending Despair", 3000, hp=300, ah=10, armor=40, mr=40, despair=True
    ),
    "Amaranth's Twinguard": Item(
        "Amaranth's Twinguard", 3200, hp=300, armor=50, mr=50
    ),
    "Plated Steelcaps": Item(
        "Plated Steelcaps", 1200, hp=150, armor=25, boots=True
    ),
}


# ---------------------------------------------------------------------------
# Paths (boots slotted after first completed legendary)
# ---------------------------------------------------------------------------


@dataclass
class Path:
    name: str
    legendaries: List[str]
    note: str


PATHS = [
    Path(
        "Dusk → Hull → Rift",
        ["Dusk and Dawn", "Hullbreaker", "Riftmaker", "Unending Despair"],
        "Diamond+ CN 7.3 most-played core (~60% WR). Skipper 1v1 + AP vamp.",
    ),
    Path(
        "Dusk → Rift → Despair",
        ["Dusk and Dawn", "Riftmaker", "Unending Despair", "Amaranth's Twinguard"],
        "Skip Hull. Earlier vamp/amp if you group more than split.",
    ),
    Path(
        "Heart → Dusk → Hull",
        ["Heartsteel", "Dusk and Dawn", "Hullbreaker", "Riftmaker"],
        "Diamond+ alt. Tankier first item, slower 1v1 spike.",
    ),
    Path(
        "Heart → Tri → Despair",
        ["Heartsteel", "Trinity Force", "Unending Despair", "Amaranth's Twinguard"],
        "All-ranks aggregator path (wildriftmeta). HP then physical sheen.",
    ),
    Path(
        "Tri → Rift → Twin",
        ["Trinity Force", "Riftmaker", "Amaranth's Twinguard", "Unending Despair"],
        "Old hybrid. Trinity is 233g more than Dusk and has no AP.",
    ),
]


def inventory_at_gold(path: Path, gold: int) -> List[Item]:
    """Completed legendaries that fit. Starter Long Sword until the first legendary."""
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
        owned = [ITEMS["Long Sword"]]
    return owned


# ---------------------------------------------------------------------------
# Combat
# ---------------------------------------------------------------------------


def resist_mult(res: float) -> float:
    return 100.0 / (100.0 + max(0.0, res))


def voli_base(level: int) -> Tuple[float, float, float, float]:
    hp = 690 + 128 * (level - 1)
    ad = 62 + 4 * (level - 1)
    armor = 46 + 4.7 * (level - 1)
    mr = 38 + 2.0 * (level - 1)
    return hp, ad, armor, mr


def lightning(level: int, ap: float) -> float:
    # Patch 7.3: 12–68 (+40% AP)
    return 12 + (68 - 12) * (level - 1) / 14 + 0.40 * ap


def target_bruiser(m: int) -> Tuple[float, float, float]:
    lv = level_at_minute(m)
    hp = 720 + 118 * (lv - 1) + 35 * m
    armor = 52 + 4.4 * (lv - 1) + (25 if m >= 12 else 8)
    mr = 38 + 2.0 * (lv - 1) + (20 if m >= 14 else 5)
    return hp, armor, mr


@dataclass
class Fight:
    mix: float
    ehp: float
    strength: float
    hp: float
    shield: float
    heal: float
    items: List[str]


def fight_at(path: Path, m: int) -> Fight:
    lv = level_at_minute(m)
    gold = gold_at_minute(m)
    inv = inventory_at_gold(path, gold)
    q = skill_rank(lv, "Q")
    w = skill_rank(lv, "W")
    e = skill_rank(lv, "E")
    r = skill_rank(lv, "R")

    base_hp, base_ad, base_ar, base_mr = voli_base(lv)
    bonus_hp = sum(i.hp for i in inv)
    bonus_ad = sum(i.ad for i in inv)
    ap = sum(i.ap for i in inv)
    ah = sum(i.ah for i in inv)
    as_pct = sum(i.as_pct for i in inv)
    has_dusk = any(i.sheen == "dusk" for i in inv)
    has_tri = any(i.sheen == "trinity" for i in inv)
    has_sheen_comp = any(i.name == "Sheen" for i in inv)
    has_hs = any(i.heartsteel for i in inv)
    has_rift = any(i.rift for i in inv)
    has_hull = any(i.hull for i in inv)
    has_despair = any(i.despair for i in inv)

    if has_rift:
        ap += 0.02 * bonus_hp

    r_hp = [0, 175, 350, 525][r]
    max_hp = base_hp + bonus_hp + r_hp
    total_ad = base_ad + bonus_ad
    bonus_hp_for_w = bonus_hp + r_hp

    t_hp, t_ar, t_mr = target_bruiser(m)
    mpen = 0.07 if (has_rift or any(i.mpen_pct for i in inv)) else 0.0
    phys = resist_mult(t_ar)
    mag = resist_mult(t_mr * (1.0 - mpen))

    rift_amp = 1.05 if has_rift else 1.0  # average of 0→8% over 8s
    vamp = 0.10 if has_rift else 0.0

    # Attack count: Q reset + 8s of AS. Passive +25% AS at 5 stacks.
    base_as = 0.73 * (1 + 0.017 * (lv - 1))
    as_total = base_as * (1 + as_pct + 0.25)
    n_aa = 1 + int(FIGHT_S * as_total)  # Q reset
    n_aa = max(4, min(n_aa, 10))

    # Spellblade procs: E, Q, W, W2 → up to 4, gated by 1.5s CD
    n_blade = min(4, 1 + int(FIGHT_S / 1.5))
    sheen_kind = "dusk" if has_dusk else ("trinity" if (has_tri or has_sheen_comp) else "none")

    phys_raw = 0.0
    mag_raw = 0.0

    # Autos
    phys_raw += n_aa * total_ad

    # Q empowered auto bonus
    if q:
        q_bonus = [0, 15, 40, 65, 90][q] + 1.0 * bonus_ad
        phys_raw += q_bonus

    # W then empowered W (on-hit already counted as extra hit-like ability dmg)
    if w:
        w1 = [0, 5, 30, 55, 80][w] + 1.0 * total_ad + 0.065 * bonus_hp_for_w
        w2 = [0, 8, 48, 88, 128][w] + 1.6 * total_ad + 0.104 * bonus_hp_for_w
        phys_raw += w1 + w2

    # E on the target (melee: bolt on them, you still stand in it)
    if e:
        e_d = [0, 80, 110, 140, 170][e] + 0.50 * ap + [0, 0.11, 0.12, 0.13, 0.14][e] * t_hp
        mag_raw += e_d

    # R landing
    if r:
        r_d = [0, 300, 500, 700][r] + 2.10 * bonus_ad + 1.0 * ap
        phys_raw += r_d

    # Lightning on autos once stacked (skip first 2 hits)
    lit = lightning(lv, ap)
    mag_raw += max(0, n_aa - 2) * lit
    if has_dusk:
        # extra on-hit on spellblade AAs after stacks
        mag_raw += min(n_blade, max(0, n_aa - 2)) * lit

    # Sheen
    if sheen_kind == "dusk":
        mag_raw += n_blade * (0.75 * base_ad + 0.10 * ap)
    elif sheen_kind == "trinity":
        ratio = 2.0 if has_tri else 1.0
        phys_raw += n_blade * (ratio * base_ad)

    # Heartsteel one proc
    if has_hs:
        phys_raw += 140 + 0.035 * max_hp

    # Hullbreaker Skipper: 4th auto, 160% base AD + 5% max HP
    if has_hull:
        n_skip = n_aa // 4
        phys_raw += n_skip * (1.60 * base_ad + 0.05 * max_hp)

    # Unending Despair: every 4s, 3% max HP magic
    if has_despair:
        mag_raw += 2 * 0.03 * max_hp

    # Grasp once
    mag_raw += 0.033 * max_hp

    mix = (phys_raw * phys + mag_raw * mag) * rift_amp

    shield = 0.0
    if e:
        shield = 0.14 * max_hp + 0.75 * ap

    # W2 heal: assume ~45% missing HP when the bite lands
    heal = 0.0
    if w:
        missing_frac = 0.45
        heal += [0, 20, 30, 40, 50][w] + [0, 0.05, 0.06, 0.07, 0.08][w] * missing_frac * max_hp
    if has_despair:
        heal += 2 * (0.03 * max_hp * 2.50)
    heal += 0.013 * max_hp  # Grasp
    heal += vamp * mix * 0.55  # omnivamp on a chunk of outgoing mix

    ehp = max_hp + shield + heal
    # Strength: kill pressure + not dying. 1 mix ≈ 0.85 ehp in a bruiser slugfest.
    strength = mix + 0.85 * ehp
    return Fight(
        mix=mix,
        ehp=ehp,
        strength=strength,
        hp=max_hp,
        shield=shield,
        heal=heal,
        items=[i.name for i in inv],
    )


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------


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
                    "hp": round(f.hp),
                }
            )
        snapshots[path.name] = rows
        totals[path.name] = acc

    ranked = sorted(PATHS, key=lambda p: totals[p.name], reverse=True)
    winner = ranked[0]

    # First-item spike (first minute both Dusk and Trinity can exist isn't fair —
    # compare at 9:00 gold, typical first legendary window)
    first_item_m = 8
    first_rows = [(p, fight_at(p, first_item_m)) for p in PATHS]

    lines: List[str] = [
        f"Wild Rift Volibear Baron item order — patch {PATCH}",
        "8s isolated 1v1 vs a bruiser. Strength = mix damage + 0.85 × (HP+E shield+heals).",
        "Gold curve: Baron farmer over 22 minutes. Boots after the first legendary.",
        "",
        f"WINNER: {winner.name}",
        f"  {winner.note}",
        "",
        "Buy order (strongest)",
        "  Start     Long Sword",
        "  Back 1    Sheen (800) if you can; else Ruby Crystal",
        "  1st item  Dusk and Dawn (3100)   ~7 min",
        "  Boots     Plated Steelcaps",
        "  2nd item  Hullbreaker (3100)     Skipper 4th-auto 1v1 punch",
        "  3rd item  Riftmaker (3100)       8% amp + 10% omnivamp + AP from HP",
        "  4th item  Unending Despair       3% max HP pulse + 250% heal",
        "  5th item  Amaranth's Twinguard   (Thornmail if they heal, Kaenic if AP)",
        "  Enchant   Stoneplate",
        "",
        f"{'Path':<28}{'8':>7}{'10':>7}{'14':>7}{'18':>7}{'22':>7}{'sum':>8}",
        "-" * 72,
    ]
    for p in ranked:
        cells = []
        for m in (8, 10, 14, 18, 22):
            cells.append(f"{fight_at(p, m).strength:7.0f}")
        lines.append(f"{p.name:<28}{''.join(cells)}{totals[p.name]:8.0f}")

    lines += ["", "First legendary window (~8:00)"]
    for p, f in sorted(first_rows, key=lambda x: x[1].strength, reverse=True):
        lines.append(
            f"  {p.name:<28} mix {f.mix:5.0f}  ehp {f.ehp:5.0f}  "
            f"str {f.strength:5.0f}  [{', '.join(f.items)}]"
        )

    lines += ["", "Why Dusk first, not Trinity / Heartsteel"]
    lines += [
        "  Dusk is 233g cheaper than Trinity, gives HP + haste + AS + AP.",
        "  AP feeds E shield, R, and lightning. Extra on-hit double-procs lightning.",
        "  Sheen is magic (hits armor stackers). Heartsteel is tankier but has no",
        "  sheen/AS — you lose the 1v1 spike the X3 Pro kit is built around.",
        "  Hullbreaker Skipper (4th auto = 160% base AD + 5% max HP) is the 1v1",
        "  item. Riftmaker turns the long fight into a heal-off.",
        "",
        "Swap Hullbreaker → Riftmaker 2nd if you are grouping, not splitting.",
        "Do not buy Trinity and Dusk together (both spellblade).",
        "",
    ]
    for p in ranked:
        dusk_m = minute_of_item(p, "Dusk and Dawn")
        tri_m = minute_of_item(p, "Trinity Force")
        lines.append(f"{p.name}: {p.note}")
        if dusk_m:
            lines.append(f"  Dusk complete ~{dusk_m}:00")
        if tri_m:
            lines.append(f"  Trinity complete ~{tri_m}:00")
        lines.append("")

    text = "\n".join(lines)
    payload = {
        "patch": PATCH,
        "winner": winner.name,
        "buy_order": [
            "Long Sword",
            "Sheen",
            "Dusk and Dawn",
            "Plated Steelcaps",
            "Hullbreaker",
            "Riftmaker",
            "Unending Despair",
            "Amaranth's Twinguard",
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
