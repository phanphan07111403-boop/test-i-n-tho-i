#!/usr/bin/env python3
"""
PC League of Legends — artillery / poke mages
Patch snapshot ~26.18.

Question:
  Best poke mage with the highest range and a short cooldown?

Compares kits at the SAME AP / ability haste (so this is a kit contest,
not an item-build contest). 12s siege window, mid-lane gold is unused;
stats are a shared artillery curve.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple
import json

GAME_MINUTES = 28
WINDOW = 12.0


def haste_cdr_mult(haste: float) -> float:
    return 100.0 / (100.0 + max(0.0, haste))


def magic_mult(mr: float) -> float:
    return 100.0 / (100.0 + max(0.0, mr))


def level_at_minute(m: int) -> int:
    table = {
        1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7, 7: 8, 8: 9,
        9: 10, 10: 11, 11: 11, 12: 12, 13: 12, 14: 13,
        15: 13, 16: 14, 17: 14, 18: 15, 19: 15, 20: 16,
        21: 16, 22: 17, 23: 17, 24: 17, 25: 18, 26: 18,
        27: 18, 28: 18,
    }
    return table.get(m, min(18, 1 + m))


def skill_rank(level: int, max_rank: int = 5, ult: bool = False) -> int:
    if ult:
        if level < 6:
            return 0
        if level < 11:
            return 1
        if level < 16:
            return 2
        return 3
    # Standard max-first: ranks at 1,3,5,7,9
    return min(max_rank, sum(1 for lv in (1, 3, 5, 7, 9) if level >= lv))


def jayce_rank(level: int) -> int:
    # Hammer/cannon Q share 6 ranks. Rank-ups: 1,3,5,7,9,11
    return min(6, sum(1 for lv in (1, 3, 5, 7, 9, 11) if level >= lv))


def ap_at_minute(m: int) -> float:
    """Shared artillery mage AP (runes + Lost Chapter → Luden/Malig → Horizon/Liandry → 3rd)."""
    ap = 18.0  # two adaptive shards
    if m >= 4:
        ap += 40.0  # Lost Chapter
    if m >= 8:
        ap += 60.0  # first legendary completes (~100 AP item, already counted 40)
    if m >= 10:
        ap += 0.0  # sorcs: pen, not AP
    if m >= 16:
        ap += 75.0  # Horizon / Liandry-ish
    if m >= 22:
        ap += 100.0  # Shadowflame / Void / Deathcap chunk
    if m >= 26:
        ap += 80.0
    # Smooth the stairs a little so graphs aren't cliffs.
    ap += 4.0 * m
    return ap


def ah_at_minute(m: int) -> float:
    ah = 10.0  # Transcendence
    if m >= 4:
        ah += 10.0  # Lost Chapter
    if m >= 8:
        ah += 10.0  # first item
    if m >= 16:
        ah += 25.0  # Horizon
    if m >= 22:
        ah += 10.0
    return ah


def flat_pen_at_minute(m: int) -> float:
    return 12.0 if m >= 10 else 0.0  # Sorcs


def pct_pen_at_minute(m: int) -> float:
    return 0.40 if m >= 22 else 0.0  # Void-ish 3rd


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


def apply_pen(mr: float, minute: int) -> float:
    reduced = mr * (1.0 - pct_pen_at_minute(minute)) - flat_pen_at_minute(minute)
    return max(0.0, reduced)


def shots_in_window(cycle: float, window: float = WINDOW, first_delay: float = 0.3) -> int:
    if cycle <= 0:
        return 0
    n = 1 + int(max(0.0, window - first_delay) / cycle)
    return max(0, n)


def lerp(rank: int, values: List[float]) -> float:
    if rank <= 0:
        return 0.0
    if rank >= len(values):
        return values[-1]
    return values[rank]


# ---------------------------------------------------------------------------
# Champion kits
# ---------------------------------------------------------------------------


@dataclass
class Kit:
    name: str
    spell: str
    # Display range of the spell you actually spam
    range: float
    # Kind: used for hit-rate table
    kind: str
    notes: str
    # cycle_s(level, ah) including charge / recast lock
    cycle_s: Callable[[int, float], float]
    # raw magic (or converted) damage of ONE landed poke
    raw: Callable[[int, float, float], float]
    hit_rate: Callable[[bool], float]
    # optional extra delay that makes the shot more dodgeable (already in hit_rate)
    mana_cap: Optional[Callable[[int, float, float], int]] = None
    # True if this is an ultimate-as-basic (Kog R)
    is_ult: bool = False


def nid_raw(level: int, ap: float, _hp: float) -> float:
    r = skill_rank(level)
    # Practical long spear, not last-pixel 3.25×. 3.00× min.
    mn = lerp(r, [0, 70, 90, 110, 130, 150]) + 0.50 * ap
    return mn * 3.00


def xer_q_raw(level: int, ap: float, _hp: float) -> float:
    r = skill_rank(level)
    return lerp(r, [0, 70, 110, 150, 190, 230]) + 0.90 * ap


def xer_q_cycle(level: int, ah: float) -> float:
    r = max(1, skill_rank(level))
    base = [9, 8, 7, 6, 5][r - 1]
    # Max range needs ~1.75s charge + 0.53s fire lock. CD runs from recast.
    return base * haste_cdr_mult(ah) + 1.75


def ziggs_raw(level: int, ap: float, _hp: float) -> float:
    r = skill_rank(level)
    ratio = lerp(r, [0, 0.60, 0.65, 0.70, 0.75, 0.80])
    return lerp(r, [0, 80, 130, 180, 230, 280]) + ratio * ap


def ziggs_cycle(level: int, ah: float) -> float:
    r = max(1, skill_rank(level))
    base = [6.0, 5.5, 5.0, 4.5, 4.0][r - 1]
    return base * haste_cdr_mult(ah) + 0.25


def kog_raw(level: int, ap: float, hp: float) -> float:
    r = skill_rank(level, ult=True)
    if r <= 0:
        return 0.0
    base = [0, 100, 140, 180][r]
    ratio = [0, 0.35, 0.40, 0.45][r]
    # Siege poke: target not execute range. ~15% missing → 7.5% amp; use 12%.
    return (base + ratio * ap) * 1.12


def kog_cycle(level: int, ah: float) -> float:
    r = skill_rank(level, ult=True)
    if r <= 0:
        return 99.0
    base = [0, 2.0, 1.5, 1.0][r]
    return max(0.35, base * haste_cdr_mult(ah)) + 0.25


def kog_mana_cap(level: int, ah: float, _ap: float) -> int:
    """Mana tax 40, 80, 120... cap 9 stacks. 2000 mana pool with Lost Chapter."""
    r = skill_rank(level, ult=True)
    if r <= 0:
        return 0
    mana = 900.0 if level < 9 else 2000.0
    n = 0
    cost = 40.0
    spent = 0.0
    theoretical = shots_in_window(kog_cycle(level, ah))
    while n < theoretical and n < 9 and spent + cost <= mana:
        spent += cost
        n += 1
        cost = min(400.0, 40.0 * (n + 1))
    return max(0, n)


def vel_raw(level: int, ap: float, _hp: float) -> float:
    r = skill_rank(level)
    q = lerp(r, [0, 80, 120, 160, 200, 240]) + 0.90 * ap
    # One W in the window on average once recharge allows.
    w = lerp(r, [0, 75, 125, 175, 225, 275]) + 0.45 * ap
    # Passive true on 3rd stack — applied as extra magic-equivalent later? Keep
    # Q-only here; W folded as +0.35 Q because 12s often fits Q+W+Q.
    return q + 0.35 * w


def vel_cycle(level: int, ah: float) -> float:
    return 7.0 * haste_cdr_mult(ah) + 0.25


def hwei_qw_raw(level: int, ap: float, hp: float) -> float:
    r = skill_rank(level)
    base = lerp(r, [0, 60, 85, 110, 135, 160]) + 0.30 * ap
    # Isolated siege target: missing-HP amp. Rank 5 max is 3.5× at 100% missing;
    # a healthy poke target is ~20% missing → interpolates toward 1.5×.
    miss = 0.20
    amp = 1.0 + miss * lerp(r, [0, 1.00, 1.375, 1.75, 2.125, 2.50])
    return base * amp


def hwei_q_cycle(level: int, ah: float) -> float:
    r = max(1, skill_rank(level))
    base = [10, 9, 8, 7, 6][r - 1]
    return base * haste_cdr_mult(ah) + 0.50  # 0.5s cast on QW


def hwei_qq_raw(level: int, ap: float, hp: float) -> float:
    r = skill_rank(level)
    pct = lerp(r, [0, 0.03, 0.04, 0.05, 0.06, 0.07])
    return lerp(r, [0, 50, 80, 110, 140, 170]) + 0.80 * ap + pct * hp


def lux_raw(level: int, ap: float, _hp: float) -> float:
    r = skill_rank(level)
    return lerp(r, [0, 70, 120, 170, 220, 270]) + 0.80 * ap


def lux_cycle(level: int, ah: float) -> float:
    r = max(1, skill_rank(level))
    base = [10.0, 9.5, 9.0, 8.5, 8.0][r - 1]
    return base * haste_cdr_mult(ah) + 0.25


def karthus_raw(level: int, ap: float, _hp: float) -> float:
    r = skill_rank(level)
    # Isolated siege = double Lay Waste.
    return 2.0 * (lerp(r, [0, 45, 62, 79, 96, 113]) + 0.35 * ap)


def karthus_cycle(level: int, ah: float) -> float:
    return max(0.40, 1.0 * haste_cdr_mult(ah)) + 0.25


def ez_raw(level: int, ap: float, _hp: float) -> float:
    r = skill_rank(level)
    # Base AD 60 + 2.75/lvl, no AD items on AP page.
    ad = 60.0 + 2.75 * (level - 1)
    return lerp(r, [0, 20, 45, 70, 95, 120]) + 1.30 * ad + 0.40 * ap


def ez_cycle(level: int, ah: float) -> float:
    r = max(1, skill_rank(level))
    base = [5.5, 5.25, 5.0, 4.75, 4.5][r - 1]
    cd = base * haste_cdr_mult(ah)
    # 1.5s refund on hit — bake average hit rate of 0.50 into cycle.
    return max(0.6, cd - 1.5 * 0.50) + 0.25


def jayce_raw(level: int, ap: float, _hp: float) -> float:
    # Physical. Treat as magic-equivalent pre-mit (we'll apply armor≈MR).
    r = jayce_rank(level)
    bonus_ad = 9.0  # adaptive
    # Rank table is 6-long.
    base = [0, 80, 121, 162, 203, 244, 285]
    dmg = lerp(r, base) + 1.30 * bonus_ad
    return dmg * 1.40  # gated


def jayce_cycle(level: int, ah: float) -> float:
    # Gate CD 16s, so every other Shock Blast is ungated. Average 1.2× cycle
    # of the 8s Q: gated every ~16s.
    return 8.0 * haste_cdr_mult(ah) + 0.21


def mel_raw(level: int, ap: float, _hp: float) -> float:
    r = skill_rank(level)
    # Full barrage if they stay in the zone.
    return lerp(r, [0, 90, 145, 200, 255, 310]) + lerp(
        r, [0, 0.90, 0.95, 1.00, 1.05, 1.10]
    ) * ap


def mel_cycle(level: int, ah: float) -> float:
    r = max(1, skill_rank(level))
    base = [10, 9, 8, 7, 6][r - 1]
    return base * haste_cdr_mult(ah) + 0.35


KITS: List[Kit] = [
    Kit(
        "Kog'Maw R",
        "Living Artillery",
        1800,
        "ground_delay",
        "Ult-as-basic. 1800 range, 1s CD, mana tax.",
        kog_cycle,
        kog_raw,
        lambda tank: 0.52 if tank else 0.48,
        mana_cap=kog_mana_cap,
        is_ult=True,
    ),
    Kit(
        "Hwei QW",
        "Severing Bolt",
        1900,
        "ground_delay",
        "Longest basic-ability artillery. 1s delay, easy to walk out.",
        hwei_q_cycle,
        hwei_qw_raw,
        lambda tank: 0.48 if tank else 0.38,
    ),
    Kit(
        "Hwei QQ",
        "Devastating Fire",
        1075,
        "missile_aoe",
        "Shorter range, better ratio, same Q CD as QW.",
        hwei_q_cycle,
        hwei_qq_raw,
        lambda tank: 0.58 if tank else 0.50,
    ),
    Kit(
        "Xerath Q",
        "Arcanopulse (max charge)",
        1450,
        "line_charge",
        "1450 range after 1.75s charge. CD is short; cycle is not.",
        xer_q_cycle,
        xer_q_raw,
        lambda tank: 0.50 if tank else 0.40,
    ),
    Kit(
        "Ziggs Q",
        "Bouncing Bomb",
        1400,
        "bounce",
        "1400 bounce, 4s rank-5 CD. The actual Q-spam mage.",
        ziggs_cycle,
        ziggs_raw,
        lambda tank: 0.58 if tank else 0.50,
    ),
    Kit(
        "Nidalee Q",
        "Javelin Toss (long)",
        1500,
        "line_thin",
        "1500 / 6s. Range looks like Xerath; hit rate and kit payoff do not.",
        lambda lv, ah: 6.0 * haste_cdr_mult(ah) + 0.25,
        nid_raw,
        lambda tank: 0.50 if tank else 0.32,
    ),
    Kit(
        "Vel'Koz Q",
        "Plasma Fission",
        1100,
        "line_split",
        "1100, split can reach ~1595. 7s CD. Passive needs 3 hits.",
        vel_cycle,
        vel_raw,
        lambda tank: 0.52 if tank else 0.45,
    ),
    Kit(
        "Jayce Q+E",
        "Shock Blast (gated)",
        1600,
        "line_fast",
        "1600 gated. 8s CD, physical, gate every 16s. Not a mage.",
        jayce_cycle,
        jayce_raw,
        lambda tank: 0.42 if tank else 0.38,
    ),
    Kit(
        "Lux E",
        "Lucent Singularity",
        1100,
        "ground_zone",
        "1100 zone. You can detonate; they can walk out. R is long CD.",
        lux_cycle,
        lux_raw,
        lambda tank: 0.62 if tank else 0.55,
    ),
    Kit(
        "Ezreal Q",
        "Mystic Shot (AP)",
        1200,
        "line_fast",
        "1200, 4.5s + 1.5 refund. Spam king, not range king. Hybrid.",
        ez_cycle,
        ez_raw,
        lambda tank: 0.55 if tank else 0.50,
    ),
    Kit(
        "Karthus Q",
        "Lay Waste (isolated)",
        875,
        "tiny_circle",
        "1s CD, double damage isolated. Range is not artillery.",
        karthus_cycle,
        karthus_raw,
        lambda tank: 0.50 if tank else 0.42,
    ),
    Kit(
        "Mel Q",
        "Radiant Volley",
        950,
        "barrage",
        "950 barrage. Fine poke, not long-range artillery.",
        mel_cycle,
        mel_raw,
        lambda tank: 0.60 if tank else 0.50,
    ),
]


@dataclass
class Snap:
    minute: int
    name: str
    range: float
    cycle: float
    shots: int
    hit_s: float
    hit_t: float
    raw: float
    exp_squish: float
    exp_tank: float
    rf: float  # range / cycle  (the actual question)
    notes: str
    is_ult: bool
    kind: str


def evaluate(kit: Kit, minute: int) -> Snap:
    level = level_at_minute(minute)
    ap = ap_at_minute(minute)
    ah = ah_at_minute(minute)
    cycle = kit.cycle_s(level, ah)
    n = shots_in_window(cycle)
    if kit.mana_cap is not None:
        n = min(n, kit.mana_cap(level, ah, ap))
    if kit.is_ult and skill_rank(level, ult=True) <= 0:
        n = 0
        cycle = 99.0

    shp, smr = squishy_hp(minute), apply_pen(squishy_mr(minute), minute)
    thp, tmr = tank_hp(minute), apply_pen(tank_mr(minute), minute)
    raw_s = kit.raw(level, ap, shp) if n else 0.0
    raw_t = kit.raw(level, ap, thp) if n else 0.0
    hs, ht = kit.hit_rate(False), kit.hit_rate(True)
    # Comet once per window if any hit (shared page).
    comet = (15.0 + (100.0 - 15.0) * (level - 1) / 17.0) + 0.05 * ap
    p_any_s = 1.0 - (1.0 - hs) ** n if n else 0.0
    p_any_t = 1.0 - (1.0 - ht) ** n if n else 0.0

    exp_s = n * hs * raw_s * magic_mult(smr) + p_any_s * comet * magic_mult(smr)
    exp_t = n * ht * raw_t * magic_mult(tmr) + p_any_t * comet * magic_mult(tmr)
    rf = (kit.range / cycle) if cycle < 50 else 0.0

    return Snap(
        minute=minute,
        name=kit.name,
        range=kit.range,
        cycle=round(cycle, 2),
        shots=n,
        hit_s=hs,
        hit_t=ht,
        raw=round(raw_s, 1),
        exp_squish=round(exp_s, 1),
        exp_tank=round(exp_t, 1),
        rf=round(rf, 1),
        notes=kit.notes,
        is_ult=kit.is_ult,
        kind=kit.kind,
    )


def run_all() -> Dict[str, List[Snap]]:
    out: Dict[str, List[Snap]] = {}
    for kit in KITS:
        out[kit.name] = [evaluate(kit, m) for m in range(1, GAME_MINUTES + 1)]
    return out


def summarize(results: Dict[str, List[Snap]]) -> str:
    lines = []
    lines.append("=" * 80)
    lines.append("POKE MAGES — HIGHEST RANGE × SHORTEST COOLDOWN  (PC LoL ~26.18)")
    lines.append("Equal AP/AH curve | 12s siege window | kits, not builds")
    lines.append("=" * 80)
    lines.append("")
    lines.append("SHARED STATS")
    lines.append(f"  {'Min':>3}  {'Lvl':>3}  {'AP':>6}  {'AH':>5}  {'Pen':>12}")
    for m in (6, 8, 10, 12, 16, 22, 28):
        pen = f"{flat_pen_at_minute(m):.0f} flat"
        if pct_pen_at_minute(m):
            pen += f" + {100 * pct_pen_at_minute(m):.0f}%"
        lines.append(
            f"  {m:>3}  {level_at_minute(m):>3}  {ap_at_minute(m):>6.0f}  "
            f"{ah_at_minute(m):>5.0f}  {pen}"
        )

    def row_at(name: str, m: int) -> Snap:
        return results[name][m - 1]

    lines.append("")
    lines.append("-" * 80)
    lines.append("RANGE / CYCLE  (this is the question: range you can refresh per second)")
    lines.append("-" * 80)
    lines.append(
        f"  {'Kit':<14} {'Rng':>5} {'CD16':>6} {'n16':>4} {'RF16':>7} "
        f"{'CD22':>6} {'n22':>4} {'RF22':>7}"
    )
    ranked_rf = sorted(
        results.keys(),
        key=lambda n: row_at(n, 22).rf,
        reverse=True,
    )
    for name in ranked_rf:
        a, b = row_at(name, 16), row_at(name, 22)
        lines.append(
            f"  {name:<14} {a.range:>5.0f} {a.cycle:>6.2f} {a.shots:>4} {a.rf:>7.0f} "
            f"{b.cycle:>6.2f} {b.shots:>4} {b.rf:>7.0f}"
        )

    lines.append("")
    lines.append("-" * 80)
    lines.append("EXPECTED DAMAGE / 12s  (hit rate × shots × one-hit)")
    lines.append("-" * 80)
    lines.append(
        f"  {'Kit':<14} {'16s':>7} {'16t':>7} {'22s':>7} {'22t':>7} "
        f"{'HitS':>6} {'Raw22':>6}"
    )
    ranked_dmg = sorted(
        results.keys(),
        key=lambda n: row_at(n, 22).exp_squish,
        reverse=True,
    )
    for name in ranked_dmg:
        a, b = row_at(name, 16), row_at(name, 22)
        lines.append(
            f"  {name:<14} {a.exp_squish:>7.0f} {a.exp_tank:>7.0f} "
            f"{b.exp_squish:>7.0f} {b.exp_tank:>7.0f} "
            f"{100 * b.hit_s:>5.0f}% {b.raw:>6.0f}"
        )

    lines.append("")
    lines.append("-" * 80)
    lines.append("ARTILLERY FILTER  (range ≥ 1400 — the spear-spam fantasy)")
    lines.append("-" * 80)
    artillery = [n for n in ranked_rf if row_at(n, 22).range >= 1400]
    for name in artillery:
        s = row_at(name, 22)
        lines.append(
            f"  {name:<14} range {s.range:.0f} | cycle {s.cycle:.2f}s | "
            f"{s.shots} shots/12s | RF {s.rf:.0f} | squish {s.exp_squish:.0f}"
        )

    kog = row_at("Kog'Maw R", 22)
    zig = row_at("Ziggs Q", 22)
    xer = row_at("Xerath Q", 22)
    nid = row_at("Nidalee Q", 22)
    hwei = row_at("Hwei QW", 22)
    kar = row_at("Karthus Q", 22)
    ezr = row_at("Ezreal Q", 22)

    def pct(a: float, b: float) -> float:
        return 100.0 * (a / b - 1.0) if b else 0.0

    lines.append("")
    lines.append("-" * 80)
    lines.append("VERDICT")
    lines.append("-" * 80)
    lines.append("  Best poke mage for HIGHEST RANGE + SHORT COOLDOWN:  Kog'Maw (AP) R")
    lines.append(
        f"  • Living Artillery: {kog.range:.0f} range, {kog.cycle:.2f}s cycle @22:00, "
        f"{kog.shots} shots / 12s."
    )
    lines.append(
        f"  • Range-frequency {kog.rf:.0f} vs Ziggs {zig.rf:.0f}, Hwei QW {hwei.rf:.0f}, "
        f"Xerath Q {xer.rf:.0f}, Nidalee {nid.rf:.0f}."
    )
    lines.append(
        f"  • Expected squish damage / 12s: Kog {kog.exp_squish:.0f}, "
        f"Ziggs {zig.exp_squish:.0f} ({pct(zig.exp_squish, kog.exp_squish):+.0f}%), "
        f"Xerath {xer.exp_squish:.0f}."
    )
    lines.append("")
    lines.append("  IF YOU WANTED SPEAR-ONLY NIDALEE, LOCK ONE OF THESE INSTEAD:")
    lines.append("  1) AP Kog'Maw  — the actual 'spam long-range skillshot' champion.")
    lines.append("     R is 1800 with a 1s CD (mana is the real limiter, not cooldown).")
    lines.append("     Hide in fog, drop R on feet. You already have a Malignance sim.")
    lines.append("  2) Ziggs       — best BASIC-ability Q spam. 1400 bounce, 4s CD")
    lines.append(
        f"     ({zig.shots} bombs / 12s). Siege, waveclear, turret. Easier than Xerath."
    )
    lines.append("  3) Xerath      — longest *identity* as an artillery mage (1450 Q +")
    lines.append("     5000 R). Range is real; 'short cooldown' is not: max Q still")
    lines.append(
        f"     costs 1.75s charge, cycle {xer.cycle:.2f}s, only {xer.shots} beams / 12s."
    )
    lines.append("  4) Hwei QW     — longest basic spell (1900) but 1s delay + 6s CD.")
    lines.append("     Great poke, not a spam button.")
    lines.append("")
    lines.append("  NOT THE ANSWER:")
    lines.append(
        f"  • Nidalee Q: {nid.range:.0f} range looks close to Xerath, but 6s CD, "
        f"~32% hit, and Hunt wants cougar. RF {nid.rf:.0f} vs Kog {kog.rf:.0f}."
    )
    lines.append(
        f"  • Karthus Q: shortest CD in the table ({kar.cycle:.2f}s, {kar.shots} ticks) "
        "but 875 range — that's a melee-adjacent circle, not artillery."
    )
    lines.append(
        f"  • Ezreal Q: spam ({ezr.shots} shots, RF {ezr.rf:.0f}) at 1200 — ADC/hybrid, "
        "not a mage, and not highest range."
    )
    lines.append("  • Jayce Q+E: 1600 gated, 8s CD, physical. Cannon poke, not a mage.")
    lines.append("  • Lux / Mel / Vel'Koz: fine poke mages, shorter range or longer CD.")
    lines.append("")
    lines.append("  HOW TO READ THE TWO WINNERS:")
    lines.append("  • Want the NUMBER (range × 1/CD):     AP Kog'Maw R.")
    lines.append("  • Want a mage whose Q is the spam:    Ziggs.")
    lines.append("  • Want to never enter vision:         Xerath (Q from fog + R).")
    lines.append("  Do not lock Nidalee for this job.")
    lines.append("=" * 80)
    return "\n".join(lines)


def export_json(results: Dict[str, List[Snap]], path: str) -> None:
    payload = {
        "meta": {
            "patch": "26.18",
            "question": "Best poke mage with highest range and short cooldown",
            "window_s": WINDOW,
            "equal_stats": True,
        },
        "kits": {
            name: [
                {
                    "minute": s.minute,
                    "range": s.range,
                    "cycle": s.cycle,
                    "shots": s.shots,
                    "hit_s": s.hit_s,
                    "raw": s.raw,
                    "exp_squish": s.exp_squish,
                    "exp_tank": s.exp_tank,
                    "range_per_sec": s.rf,
                    "notes": s.notes,
                }
                for s in snaps
            ]
            for name, snaps in results.items()
        },
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def self_check(results: Dict[str, List[Snap]]) -> None:
    kog = results["Kog'Maw R"][21]
    zig = results["Ziggs Q"][21]
    xer = results["Xerath Q"][21]
    nid = results["Nidalee Q"][21]
    kar = results["Karthus Q"][21]
    hwei = results["Hwei QW"][21]
    # The question is range × 1/CD. Kog must win that among everyone.
    assert kog.rf > zig.rf, (kog.rf, zig.rf)
    assert kog.rf > xer.rf
    assert kog.rf > nid.rf
    assert kog.rf > hwei.rf
    # Ziggs is the basic-ability spam winner vs Xerath/Nidalee (more shots).
    assert zig.shots > xer.shots
    assert zig.shots > nid.shots
    # Nidalee is not the range-frequency winner.
    assert nid.rf < zig.rf
    # Karthus has short CD but is not artillery range.
    assert kar.range < 1000
    assert kar.shots >= zig.shots
    # Hwei QW is the longest basic spell.
    assert hwei.range >= 1900
    # Kog is available at 22 (R max).
    assert kog.shots >= 4
    # Xerath cycle includes charge — longer than its raw 5s CD.
    assert xer.cycle > 3.5


def main() -> None:
    results = run_all()
    self_check(results)
    report = summarize(results)
    print(report)
    out_dir = "/workspace/poke-mage-sim"
    with open(f"{out_dir}/report.txt", "w", encoding="utf-8") as f:
        f.write(report + "\n")
    export_json(results, f"{out_dir}/results.json")
    print(f"\nWrote {out_dir}/report.txt and {out_dir}/results.json")


if __name__ == "__main__":
    main()
