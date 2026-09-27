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
    n_aa: int = 0
    keystone: str = "tempo"


def voli_autos(
    fight_s: float, lv: int, as_pct_items: float, keystone: str
) -> Tuple[int, int]:
    """Autos in fight_s including the Q reset. Tempo: 8% AS/stack, 6 max (7.3).
    Tempo page also has Legend: Alacrity (18%). Grasp page does not.
    """
    base_as = 0.73 * (1 + 0.017 * (lv - 1))
    alacrity = 0.18 if keystone == "tempo" else 0.0
    n = 1  # Q reset
    stacks = 1 if keystone == "tempo" else 0
    t = 0.0
    while n < 16:
        pass_as = 0.25 if n >= 5 else 0.05 * n
        tempo_as = 0.08 * stacks if keystone == "tempo" else 0.0
        as_now = base_as * (1 + as_pct_items + alacrity + pass_as + tempo_as)
        interval = 1.0 / max(0.45, as_now)
        t += interval
        if t > fight_s:
            break
        n += 1
        if keystone == "tempo":
            stacks = min(6, stacks + 1)
    return n, stacks


def grasp_procs(fight_s: float, prestack: bool) -> int:
    """7.2/7.3 Grasp: 4 stacks, then the next auto. ~4s to first proc.
    Prestack (you already hit the wave) = first auto of the trade is the proc.
    """
    if prestack:
        return 1 + (1 if fight_s >= 7.0 else 0)
    if fight_s >= 7.5:
        return 2
    if fight_s >= 4.0:
        return 1
    return 0


def fight_at(
    path: Path,
    m: int,
    keystone: str = "tempo",
    fight_s: float = FIGHT_S,
    grasp_prestack: bool = False,
) -> Fight:
    lv = level_at_minute(m)
    gold = gold_at_minute(m)
    inv = inventory_at_gold(path, gold)
    q = skill_rank(lv, "Q")
    w = skill_rank(lv, "W")
    e = skill_rank(lv, "E")
    r = skill_rank(lv, "R")

    base_hp, base_ad, base_ar, base_mr = voli_base(lv)
    bonus_hp = sum(i.hp for i in inv)
    if keystone == "grasp":
        # ~1 Grasp proc/min in lane after level 3, 10 HP each, cap 250
        bonus_hp += min(250.0, 10.0 * max(0, m - 3))
    bonus_ad = sum(i.ad for i in inv)
    ap = sum(i.ap for i in inv)
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

    rift_amp = 1.05 if has_rift else 1.0
    vamp = 0.10 if has_rift else 0.0

    n_aa, tempo_stacks = voli_autos(fight_s, lv, as_pct, keystone)
    n_aa = max(3, n_aa)

    n_blade = min(4, 1 + int(fight_s / 1.5))
    sheen_kind = "dusk" if has_dusk else ("trinity" if (has_tri or has_sheen_comp) else "none")

    phys_raw = 0.0
    mag_raw = 0.0

    phys_raw += n_aa * total_ad

    if q:
        q_bonus = [0, 15, 40, 65, 90][q] + 1.0 * bonus_ad
        phys_raw += q_bonus

    if w:
        w1 = [0, 5, 30, 55, 80][w] + 1.0 * total_ad + 0.065 * bonus_hp_for_w
        w2 = [0, 8, 48, 88, 128][w] + 1.6 * total_ad + 0.104 * bonus_hp_for_w
        phys_raw += w1 + w2

    if e:
        e_d = [0, 80, 110, 140, 170][e] + 0.50 * ap + [0, 0.11, 0.12, 0.13, 0.14][e] * t_hp
        mag_raw += e_d

    if r and fight_s >= 6.0:
        r_d = [0, 300, 500, 700][r] + 2.10 * bonus_ad + 1.0 * ap
        phys_raw += r_d

    lit = lightning(lv, ap)
    mag_raw += max(0, n_aa - 2) * lit
    if has_dusk:
        mag_raw += min(n_blade, max(0, n_aa - 2)) * lit

    if sheen_kind == "dusk":
        mag_raw += n_blade * (0.75 * base_ad + 0.10 * ap)
    elif sheen_kind == "trinity":
        ratio = 2.0 if has_tri else 1.0
        phys_raw += n_blade * (ratio * base_ad)

    if has_hs:
        phys_raw += 140 + 0.035 * max_hp

    if has_hull:
        n_skip = n_aa // 4
        phys_raw += n_skip * (1.60 * base_ad + 0.05 * max_hp)

    if has_despair:
        mag_raw += int(fight_s / 4.0) * 0.03 * max_hp

    n_grasp = grasp_procs(fight_s, grasp_prestack) if keystone == "grasp" else 0
    mag_raw += n_grasp * 0.033 * max_hp

    # 7.3 Tempo max-stack bullet: 9–30 melee, +1% per 1% bonus AS
    n_bullets = 0
    if keystone == "tempo" and tempo_stacks >= 6:
        n_bullets = max(0, n_aa - 5)
        bullet = (9 + (30 - 9) * (lv - 1) / 14) * (
            1 + as_pct + 0.18 + 0.25 + 0.48
        )
        mag_raw += n_bullets * bullet

    mix = (phys_raw * phys + mag_raw * mag) * rift_amp

    shield = 0.0
    if e:
        shield = 0.14 * max_hp + 0.75 * ap

    heal = 0.0
    if w:
        missing_frac = 0.45
        heal += [0, 20, 30, 40, 50][w] + [0, 0.05, 0.06, 0.07, 0.08][w] * missing_frac * max_hp
    if has_despair:
        heal += int(fight_s / 4.0) * (0.03 * max_hp * 2.50)
    heal += n_grasp * 0.013 * max_hp
    heal += vamp * mix * 0.55

    # Unshakeable on the Grasp page: ~7% resists in a 1v1, ~9% in a 3-man
    twin = 0.0
    if keystone == "grasp" and fight_s >= 5.0:
        twin = 0.05 * max_hp

    ehp = max_hp + shield + heal + twin
    strength = mix + 0.85 * ehp
    return Fight(
        mix=mix,
        ehp=ehp,
        strength=strength,
        hp=max_hp,
        shield=shield,
        heal=heal,
        items=[i.name for i in inv],
        n_aa=n_aa,
        keystone=keystone,
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


# Precision slot 2 (patch 7.3). Giant Slayer was renamed Cut Down in 7.1
# and nerfed 8% → 6.5% in 7.2.
CUT_DOWN = 0.065  # vs enemies above 60% HP
COUP = 0.08  # vs enemies below 40% HP
# Last Stand: 5% at 60% HP, 11% at 30% HP or below. 0 above 60%.


def last_stand_amp(hp_frac: float) -> float:
    if hp_frac >= 0.60:
        return 0.0
    if hp_frac <= 0.30:
        return 0.11
    return 0.05 + 0.06 * (0.60 - hp_frac) / 0.30


def rune_extras(mix: float, target_hp: float, voli_low_uptime: float, voli_hp: float) -> dict:
    """Extra mix from each Precision slot-2 rune over an 8s linear fight."""
    dealt = max(0.0, mix)
    band_40 = 0.40 * target_hp
    cut_portion = min(dealt, band_40)
    if dealt > 0.60 * target_hp:
        coup_portion = min(dealt - 0.60 * target_hp, band_40)
    else:
        coup_portion = 0.0
    ls = mix * voli_low_uptime * last_stand_amp(voli_hp)
    return {
        "Last Stand": ls,
        "Cut Down": cut_portion * CUT_DOWN,
        "Coup de Grace": coup_portion * COUP,
    }


def rune_table(path: Path) -> List[str]:
    """Slugfest 1v1 (you sit low) vs a clean dive (you stay high, they drop)."""
    lines = [
        "Precision slot 2 (Last Stand / Cut Down / Coup de Grace)",
        "  Cut Down is old Giant Slayer, nerfed 8% → 6.5% in 7.2.",
        "  Extra mix on the Dusk → Hull → Rift 8s 1v1.",
        "",
        "  Slugfest: you drop below 60% at ~2s, sit ~45% HP (W heal).",
        "  Dive/stomp: you stay healthy; they fall through 60% then 40%.",
        "",
    ]
    for label, uptime, hp_you in (
        ("slugfest 1v1", 0.70, 0.45),
        ("you stay full", 0.00, 0.90),
    ):
        lines.append(
            f"  {label:<16}{'8:00':>10}{'14:00':>10}{'22:00':>10}"
        )
        rows = {"Last Stand": [], "Cut Down": [], "Coup de Grace": []}
        for m in (8, 14, 22):
            f = fight_at(path, m)
            t_hp, _, _ = target_bruiser(m)
            extras = rune_extras(f.mix, t_hp, uptime, hp_you)
            for name in rows:
                rows[name].append(extras[name])
        for name, vals in rows.items():
            cells = "".join(f"{v:10.0f}" for v in vals)
            lines.append(f"    {name:<14}{cells}")
        edges = []
        for i, m in enumerate((8, 14, 22)):
            best = max(rows, key=lambda n: rows[n][i])
            edges.append(f"{m}:00 {best}")
        lines.append(f"    edge          {', '.join(edges)}")
        lines.append("")
    lines.append("  Default on this page: Last Stand. You live in the W-heal 1v1.")
    lines.append("  Cut Down only if you are the full-HP one hitting a tank.")
    lines.append("  Coup only if you already put them in execute and stay healthy.")
    lines.append("")
    return lines


def _edge(t: float, g: float) -> str:
    if abs(t - g) < 0.03 * max(abs(t), abs(g), 1.0):
        return "tie"
    return "Tempo" if t > g else "Grasp"


def keystone_table(path: Path) -> List[str]:
    """Lethal Tempo (7.3 rework) vs Grasp on the Dusk → Hull → Rift page."""
    lines = [
        "Lethal Tempo vs Grasp of the Undying (Dusk → Hull → Rift)",
        "  7.3 Tempo: 8% AS per auto, 6 stacks, then adaptive bullets",
        "  (9–30 + 1% per 1% bonus AS). No more bonus range.",
        "  Tempo page includes Legend: Alacrity. Grasp page does not.",
        "  Grasp: 3.3% max HP magic + 1.3% max HP heal per proc, +10 HP.",
        "",
    ]

    def row(label: str, m: int, fight_s: float, prestack: bool = False) -> None:
        t = fight_at(path, m, "tempo", fight_s)
        g = fight_at(path, m, "grasp", fight_s, grasp_prestack=prestack)
        lines.append(
            f"  {label:<22} Tempo mix {t.mix:5.0f} ehp {t.ehp:5.0f} aa {t.n_aa}"
            f"  Grasp mix {g.mix:5.0f} ehp {g.ehp:5.0f} aa {g.n_aa}"
            f"  dmg {_edge(t.mix, g.mix):<5} live {_edge(t.ehp, g.ehp)}"
        )

    lines.append("  Lane 3s (no prestack) — first trade, Grasp not up yet")
    row("lane 3s cold 8:00", 8, 3.0, False)
    row("lane 3s cold 14:00", 14, 3.0, False)
    lines.append("  Lane 3s (Grasp prestacked on the wave)")
    row("lane 3s stacked 8:00", 8, 3.0, True)
    row("lane 3s stacked 14:00", 14, 3.0, True)
    lines.append("  1v1 8s slugfest")
    row("1v1 8:00", 8, 8.0, False)
    row("1v1 14:00", 14, 8.0, False)
    row("1v1 22:00", 22, 8.0, False)
    lines.append("  Teamfight = 8s dive on one carry (same 1v1, Grasp has Unshakeable)")
    row("TF dive 22:00", 22, 8.0, False)
    lines.append("")
    lines.append("  Damage / 1v1 / all-in: Lethal Tempo (extra autos, lightning, Skipper, bullets).")
    lines.append("  Survival / short lane trades: Grasp (heal + HP stacks + Unshakeable).")
    lines.append("  Teamfight: Tempo kills the dive target faster; Grasp lives the collapse.")
    lines.append("  Default on this Dusk page: Lethal Tempo. Grasp into poke/range.")
    lines.append("")
    return lines


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
    lines += rune_table(winner)
    lines += keystone_table(winner)
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
        "precision_slot2": "Last Stand",
        "keystone": "Lethal Tempo",
        "snapshots": snapshots,
    }
    (OUT_DIR / "report.txt").write_text(text + "\n", encoding="utf-8")
    (OUT_DIR / "results.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )
    print(text)


if __name__ == "__main__":
    main()
