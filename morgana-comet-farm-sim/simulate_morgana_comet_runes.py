#!/usr/bin/env python3
"""
Wild Rift 7.2e — rune page for Morgana's late Comet core.

Lock items: Rylai → Spellslinger → Void → Orb → HF → Cap (gold timeline).
Keystones are independent of path. Loadout = 1 keystone + 3 primary
(one per slot) + 1 secondary from a different path.

Late metric = Σ minutes 20–30 of 50% poke@90% + 50% fight@32%.
Includes Q+W, keystone, Scorch, Cheap Shot, Cut/Coup, Tyrant.
AH does not reduce Comet / Scorch / Cheap Shot / Electrocute CD.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Sequence, Tuple
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from simulate_morgana_comet import (  # noqa: E402
    GAME_MINUTES,
    HEAD_RYLAI,
    START_GOLD,
    Stats,
    comet_cd,
    comet_hit_dmg,
    dummy,
    level_at,
    mid_income,
    procs_this_minute,
    progress,
    stats_of,
    strike,
)

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
LATE_START = 20
WIN_PATH = HEAD_RYLAI + [
    "Void Staff", "Infinity Orb", "Horizon Focus", "Rabadon's Deathcap",
]
CUT = 1.0657
COUP = 1.08
DH_CD = 35.0
CHEAP_CD = 7.0
SCORCH_CD = 8.0
AERY_CD = 4.0
FS_TRUE = 0.07


def skill_rank(level: int, skill: str) -> int:
    q_lv, w_lv = [3, 8, 9, 10, 12], [1, 2, 4, 5, 7]
    return min(4, sum(1 for lv in {"Q": q_lv, "W": w_lv}[skill] if level >= lv))


def ah_cd(base: float, ah: float) -> float:
    return base * 100.0 / (100.0 + max(0.0, ah))


def lerp_level(lo: float, hi: float, level: int) -> float:
    return lo + (hi - lo) * (level - 1) / 14.0


def cheap_raw(level: int) -> float:
    return lerp_level(10.0, 45.0, level)


def scorch_raw(level: int) -> float:
    return lerp_level(21.0, 49.0, level)


def aery_raw(ap: float, level: int) -> float:
    return lerp_level(15.0, 70.0, level) + 0.05 * ap


def electro_raw(ap: float, level: int) -> float:
    return lerp_level(40.0, 210.0, level) + 0.05 * ap


def electro_cd(level: int) -> float:
    return 20.0 - 7.0 * (level - 1) / 14.0


def first_strike_cd(level: int) -> float:
    return electro_cd(level)


def dh_raw(ap: float, souls: float) -> float:
    return 35.0 + 11.0 * souls + 0.05 * ap


def tyrant_raw(ap: float, level: int) -> float:
    return lerp_level(20.0, 70.0, level) + 0.03 * ap


def abs_focus_ap(level: int, frac: float) -> float:
    if frac < 0.65:
        return 0.0
    return lerp_level(2.0, 30.0, level)


def hp_mult(frac: float, cut: bool, coup: bool) -> float:
    m = 1.0
    if cut and frac > 0.60:
        m *= CUT
    if coup and frac < 0.40:
        m *= COUP
    return m


def item_timeline(path: Sequence[str]) -> List[List[str]]:
    owned: List[str] = []
    gold = START_GOLD
    snaps: List[List[str]] = []
    for m in range(1, GAME_MINUTES + 1):
        gold += mid_income(m)
        owned, gold = progress(list(path), owned, gold, m)
        snaps.append(list(owned))
    return snaps


def q_raw(st: Stats, level: int) -> float:
    qr = max(1, skill_rank(level, "Q"))
    return [0, 80, 160, 240, 320][qr] + 0.90 * st.ap


def w_dwell_raw(st: Stats, level: int, start_frac: float) -> float:
    wr = max(1, skill_rank(level, "W"))
    dwell = 5.0 if st.rylai else 2.5
    ticks = max(1, int(dwell / 0.5))
    total = 0.0
    frac = start_frac
    for _ in range(ticks):
        missing = 1.0 - max(0.05, frac)
        w_amp = 1.0 + 1.7 * min(0.7, missing)
        total += ([0, 7, 12, 17, 22][wr] + 0.07 * st.ap) * w_amp
        frac = max(0.05, frac - 0.04)
    return total


def qpm(st: Stats, level: int) -> float:
    qr = max(1, skill_rank(level, "Q"))
    base = 10.0 if qr <= 2 else 9.0
    return 60.0 / (ah_cd(base, st.ah) * (0.95 if level >= 9 else 1.0))


def wpm(st: Stats, level: int) -> float:
    return 60.0 / ah_cd(12.0, st.ah)


@dataclass
class Page:
    name: str
    keystone: str
    primary: str
    runes: Tuple[str, ...]
    secondary: str


def pages() -> List[Page]:
    """Legal 7.2 loadouts worth asking on this core."""
    return [
        Page("Comet / Sorc Focus·GS / Cut", "Comet", "Sorcery",
             ("Manaflow Band", "Absolute Focus", "Gathering Storm"), "Cut Down"),
        Page("Comet / Sorc Focus·GS / Coup", "Comet", "Sorcery",
             ("Manaflow Band", "Absolute Focus", "Gathering Storm"), "Coup de Grace"),
        Page("Comet / Sorc Focus·GS / Cheap", "Comet", "Sorcery",
             ("Manaflow Band", "Absolute Focus", "Gathering Storm"), "Cheap Shot"),
        Page("Comet / Sorc Trans·GS / Cut", "Comet", "Sorcery",
             ("Manaflow Band", "Transcendence", "Gathering Storm"), "Cut Down"),
        Page("Comet / Sorc Trans·GS / Coup", "Comet", "Sorcery",
             ("Manaflow Band", "Transcendence", "Gathering Storm"), "Coup de Grace"),
        Page("Comet / Sorc Trans·GS / Cheap", "Comet", "Sorcery",
             ("Manaflow Band", "Transcendence", "Gathering Storm"), "Cheap Shot"),
        Page("Comet / Sorc Focus·Scorch / Cut", "Comet", "Sorcery",
             ("Manaflow Band", "Absolute Focus", "Scorch"), "Cut Down"),
        Page("Comet / Sorc Focus·Scorch / Cheap", "Comet", "Sorcery",
             ("Manaflow Band", "Absolute Focus", "Scorch"), "Cheap Shot"),
        Page("Comet / Sorc Focus·GS / Tyrant", "Comet", "Sorcery",
             ("Manaflow Band", "Absolute Focus", "Gathering Storm"), "Tyrant"),
        Page("Comet / Sorc Focus·GS / Eyeball", "Comet", "Sorcery",
             ("Manaflow Band", "Absolute Focus", "Gathering Storm"), "Eyeball Collection"),
        Page("Comet / Dom Cheap·Tyrant·Eye / GS", "Comet", "Domination",
             ("Cheap Shot", "Tyrant", "Eyeball Collection"), "Gathering Storm"),
        Page("Comet / Dom Cheap·Tyrant·Eye / Cut", "Comet", "Domination",
             ("Cheap Shot", "Tyrant", "Eyeball Collection"), "Cut Down"),
        Page("Comet / Prec Brutal·Cut / GS", "Comet", "Precision",
             ("Brutal", "Cut Down", "Legend: Bloodline"), "Gathering Storm"),
        Page("Comet / Prec Brutal·Coup / GS", "Comet", "Precision",
             ("Brutal", "Coup de Grace", "Legend: Bloodline"), "Gathering Storm"),
        Page("DH / Sorc Focus·GS / Cut", "Dark Harvest", "Sorcery",
             ("Manaflow Band", "Absolute Focus", "Gathering Storm"), "Cut Down"),
        Page("DH / Sorc Focus·GS / Coup", "Dark Harvest", "Sorcery",
             ("Manaflow Band", "Absolute Focus", "Gathering Storm"), "Coup de Grace"),
        Page("Aery / Sorc Focus·GS / Cut", "Aery", "Sorcery",
             ("Manaflow Band", "Absolute Focus", "Gathering Storm"), "Cut Down"),
        Page("Electro / Sorc Focus·GS / Cut", "Electrocute", "Sorcery",
             ("Manaflow Band", "Absolute Focus", "Gathering Storm"), "Cut Down"),
        Page("First Strike / Sorc Focus·GS / Cut", "First Strike", "Sorcery",
             ("Manaflow Band", "Absolute Focus", "Gathering Storm"), "Cut Down"),
        Page("Comet / Sorc Focus·GS / Axiom", "Comet", "Sorcery",
             ("Axiom Arcanist", "Absolute Focus", "Gathering Storm"), "Cut Down"),
    ]


def has(page: Page, name: str) -> bool:
    return name in page.runes or page.secondary == name or page.keystone == name


def rune_ap(page: Page, level: int, minute: int, frac: float) -> float:
    ap = 0.0
    if has(page, "Absolute Focus"):
        ap += abs_focus_ap(level, frac)
    if has(page, "Eyeball Collection"):
        # Late: 8 stacks by 20:00 (champ + epic). 3 AP each.
        stacks = 0 if minute < 8 else min(8, 2 + (minute - 8) // 2)
        ap += 3.0 * stacks
    return ap


def make_stats(
    owned: List[str], level: int, minute: int, page: Page, frac: float,
) -> Stats:
    extra = rune_ap(page, level, minute, frac)
    return stats_of(
        owned, level, minute,
        extra_ap=extra,
        extra_ah=0.0,
        gs=has(page, "Gathering Storm"),
        trans=has(page, "Transcendence"),
    )


def kit_hit(
    st: Stats, minute: int, level: int, frac: float, page: Page,
) -> float:
    _, mr = dummy(minute, level)
    hf_q = False
    q = strike(q_raw(st, level), st, mr, frac, False)
    if st.horizon:
        hf_q = True
    w = strike(w_dwell_raw(st, level, frac), st, mr, frac, hf_q)
    dealt = q + w
    if has(page, "Tyrant") and frac < 0.50:
        dealt += strike(tyrant_raw(st.ap, level), st, mr, frac, hf_q)
    if has(page, "Brutal"):
        dealt += strike(5.0 + 0.03 * st.ap, st, mr, frac, False)
    return dealt * hp_mult(frac, has(page, "Cut Down"), has(page, "Coup de Grace"))


def keystone_hit(
    st: Stats,
    minute: int,
    level: int,
    frac: float,
    page: Page,
    stacks: float,
    souls: float,
    kit_once: float,
) -> Tuple[float, float]:
    """Return (damage of one proc, procs this minute)."""
    _, mr = dummy(minute, level)
    hf = st.horizon
    trig, comet_hits = procs_this_minute(st, minute, level)
    combat_s = trig * comet_cd(level)
    hpm = hp_mult(frac, has(page, "Cut Down"), has(page, "Coup de Grace"))
    ks = page.keystone
    if ks == "Comet":
        dmg = comet_hit_dmg(st, minute, level, stacks, frac) * hpm
        return dmg, comet_hits
    if ks == "Dark Harvest":
        if frac > 0.50:
            return 0.0, 0.0
        dmg = strike(dh_raw(st.ap, souls), st, mr, frac, hf) * hpm
        n = 60.0 / DH_CD
        if minute >= 16:
            n += 0.8
        if minute >= 22:
            n += 0.6
        n *= 0.55 if minute < 12 else 0.75
        return dmg, n
    if ks == "Aery":
        dmg = strike(aery_raw(st.ap, level), st, mr, frac, hf) * hpm
        n = (combat_s / AERY_CD) * (0.95 if st.rylai else 0.80)
        return dmg, n
    if ks == "Electrocute":
        dmg = strike(electro_raw(st.ap, level), st, mr, frac, hf) * hpm
        n = (combat_s / electro_cd(level)) * (0.90 if st.rylai else 0.70)
        return dmg, n
    if ks == "First Strike":
        comet = comet_hit_dmg(st, minute, level, stacks, frac) * hpm
        chunk = kit_once + comet
        dmg = FS_TRUE * chunk
        n = (combat_s / first_strike_cd(level)) * 0.65
        return dmg, n
    return 0.0, 0.0


def scorch_dpm(st: Stats, minute: int, level: int, frac: float, page: Page) -> float:
    if not has(page, "Scorch"):
        return 0.0
    _, mr = dummy(minute, level)
    hpm = hp_mult(frac, has(page, "Cut Down"), has(page, "Coup de Grace"))
    hit = strike(scorch_raw(level), st, mr, frac, False) * hpm
    trig, _ = procs_this_minute(st, minute, level)
    cap = 60.0 / SCORCH_CD
    return min(cap, trig) * hit


def cheap_dpm(st: Stats, minute: int, level: int, page: Page) -> float:
    if not has(page, "Cheap Shot"):
        return 0.0
    trig, _ = procs_this_minute(st, minute, level)
    cap = 60.0 / CHEAP_CD
    return min(cap, trig) * cheap_raw(level)


@dataclass
class Minute:
    minute: int
    total: float
    kit: float
    keystone: float
    extra: float
    stacks: float
    souls: float
    ap90: float


@dataclass
class Run:
    page: Page
    minutes: List[Minute] = field(default_factory=list)

    def area(self, start: int, end: int = GAME_MINUTES) -> float:
        return sum(m.total for m in self.minutes if start <= m.minute <= end)

    @property
    def late(self) -> float:
        return self.area(LATE_START, GAME_MINUTES)

    @property
    def full(self) -> float:
        return self.area(1, GAME_MINUTES)


def simulate(page: Page, owned_at: List[List[str]]) -> Run:
    stacks = 0.0
    souls = 0.0
    rows: List[Minute] = []
    for m in range(1, GAME_MINUTES + 1):
        owned = owned_at[m - 1]
        lv = level_at(m)
        parts = []
        for frac, w in ((0.90, 0.50), (0.32, 0.50)):
            st = make_stats(owned, lv, m, page, frac)
            kit_once = kit_hit(st, m, lv, frac, page)
            qp, wp = qpm(st, lv), wpm(st, lv)
            # One Q + one W per "poke window", cadence gated by W (pool) ~ wpm.
            windows = min(wp, qp) * 0.35  # not every CD is a champion poke
            kit = kit_once * windows
            ks_hit, ks_n = keystone_hit(
                st, m, lv, frac, page, stacks, souls, kit_once,
            )
            ks = ks_hit * ks_n
            extra = scorch_dpm(st, m, lv, frac, page) + cheap_dpm(st, m, lv, page)
            parts.append((w, kit, ks, extra, st.ap))
        kit = parts[0][1] * parts[0][0] + parts[1][1] * parts[1][0]
        ks = parts[0][2] * parts[0][0] + parts[1][2] * parts[1][0]
        extra = parts[0][3] * parts[0][0] + parts[1][3] * parts[1][0]
        total = kit + ks + extra
        st90 = make_stats(owned, lv, m, page, 0.90)
        _t, hits = procs_this_minute(st90, m, lv)
        if page.keystone == "Comet":
            stacks = min(200.0, stacks + hits)
        if page.keystone == "Dark Harvest":
            # Souls when the <50% window exists (Rylai / mid-game).
            opened = st90.rylai or m >= 10
            if opened:
                souls = min(99.0, souls + (1.0 if m >= 6 else 0.4) + (0.7 if m >= 16 else 0.0))
            elif m >= 8:
                souls = min(99.0, souls + 0.25)
        rows.append(
            Minute(m, total, kit, ks, extra, stacks, souls, parts[0][4]),
        )
    return Run(page, rows)


def pct(num: float, den: float) -> str:
    if den <= 1e-9:
        return "n/a"
    return f"{100.0 * (num / den - 1.0):+.1f}%"


def summarize(runs: List[Run]) -> str:
    ranked = sorted(runs, key=lambda r: (r.late, r.full), reverse=True)
    best = ranked[0]
    by = {r.page.name: r for r in ranked}

    def get(*keys: str) -> Optional[Run]:
        for k in keys:
            if k in by:
                return by[k]
        return None

    L: List[str] = []
    L.append("=" * 80)
    L.append("MORGANA LATE PAGE — keystone + rune  (WR 7.2e)")
    L.append("Core khóa: Rylai → Spell → Void → Orb → HF → Cap. Gold timeline.")
    L.append("Late = Σ phút 20–30. Mix 50% poke 90% HP + 50% fight 32% HP.")
    L.append("=" * 80)
    L.append("")
    L.append("GIẢ ĐỊNH (không phải khóa 4 ô)")
    L.append("-" * 80)
    L.append("  Client : Tốc Chiến 7.2e. Keystone độc lập với path.")
    L.append("           Loadout = 1 keystone + 3 primary (mỗi slot) + 1 secondary path khác.")
    L.append("           Comet 15–100+2×hit+5% AP. DH 35+11×soul+5% AP, <50%, CD 35s.")
    L.append("           Aery 15–70+5% AP. Electro 40–210+5% AP, CD 20–13s.")
    L.append("           First Strike 7% true / 3s, CD 20–13s. GS x(x+3) AP, Cap ×1.30.")
    L.append("           Focus 2–30 AP khi >65% HP. Cut 6.57% >60%. Coup 8% <40%.")
    L.append("           Cheap Shot 10–45 true / 7s (slow Rylai cũng impair). Scorch 21–49 / 8s.")
    L.append("  Role   : mid. Build late Rylai-first. W-max. Không đồ support.")
    L.append("  Cặp    : Comet vs DH / Aery / Electro / First Strike trên cùng GS+Focus.")
    L.append("           Secondary Cut vs Coup vs Cheap. Focus vs Trans. GS vs Scorch.")
    L.append("           Dom Cheap·Tyrant·Eye vs Sorc Focus·GS.")
    L.append("  Metric : Σ20–30 (Q+W cadence + keystone DPM + Scorch/Cheap leftover).")
    L.append("           Cùng uptime combat với farm Comet. AH không giảm CD Comet/Scorch.")
    L.append("")

    L.append("-" * 80)
    L.append("WINNER PAGE")
    L.append("-" * 80)
    L.append(f"  {best.page.name}")
    L.append(f"  Keystone : {best.page.keystone}")
    L.append(f"  Primary  : {best.page.primary} — {', '.join(best.page.runes)}")
    L.append(f"  Secondary: {best.page.secondary}")
    L.append(
        f"  Σ20–30 {best.late:.0f} | Σ1–30 {best.full:.0f} | "
        f"stacks/souls @30 {best.minutes[-1].stacks:.1f}/{best.minutes[-1].souls:.1f}"
    )
    L.append("")

    L.append("-" * 80)
    L.append("RANK — Σ phút 20–30")
    L.append("-" * 80)
    L.append(f"  {'Page':<44} {'late':>8} {'full':>8} {'@30 ks':>8}  vs#1")
    for r in ranked:
        L.append(
            f"  {r.page.name:<44} {r.late:8.0f} {r.full:8.0f} "
            f"{r.minutes[-1].keystone:8.0f}  {pct(r.late, best.late)}"
        )
    L.append("")

    L.append("-" * 80)
    L.append("KEYSTONE — cùng page Sorc Focus·GS / Cut")
    L.append("-" * 80)
    keys = [
        "Comet / Sorc Focus·GS / Cut",
        "DH / Sorc Focus·GS / Cut",
        "Aery / Sorc Focus·GS / Cut",
        "Electro / Sorc Focus·GS / Cut",
        "First Strike / Sorc Focus·GS / Cut",
    ]
    L.append(f"  {'Keystone':<44} {'late':>8} {'ks20':>7} {'ks24':>7} {'ks30':>7}")
    for name in keys:
        r = by.get(name)
        if r is None:
            continue
        L.append(
            f"  {r.page.keystone:<44} {r.late:8.0f} "
            f"{r.minutes[19].keystone:7.0f} {r.minutes[23].keystone:7.0f} "
            f"{r.minutes[29].keystone:7.0f}"
        )
    L.append("")

    L.append("-" * 80)
    L.append("MINUTE 20 / 24 / 28 / 30 — winner vs đối chứng")
    L.append("-" * 80)
    show = [
        best.page.name,
        "Comet / Sorc Focus·GS / Cut",
        "Comet / Sorc Focus·GS / Coup",
        "Comet / Sorc Focus·GS / Cheap",
        "Comet / Sorc Trans·GS / Cut",
        "Comet / Sorc Trans·GS / Coup",
        "Comet / Sorc Focus·Scorch / Cut",
        "Comet / Dom Cheap·Tyrant·Eye / GS",
        "DH / Sorc Focus·GS / Coup",
        "Aery / Sorc Focus·GS / Cut",
        "First Strike / Sorc Focus·GS / Cut",
    ]
    L.append(f"  {'Page':<44} {'20':>7} {'24':>7} {'28':>7} {'30':>7}")
    seen = set()
    for name in show:
        r = by.get(name)
        if r is None or name in seen:
            continue
        seen.add(name)
        L.append(
            f"  {r.page.name:<44} {r.minutes[19].total:7.0f} {r.minutes[23].total:7.0f} "
            f"{r.minutes[27].total:7.0f} {r.minutes[29].total:7.0f}"
        )
    L.append("")

    comet_cut = get("Comet / Sorc Focus·GS / Cut")
    comet_coup = get("Comet / Sorc Focus·GS / Coup")
    comet_cheap = get("Comet / Sorc Focus·GS / Cheap")
    comet_scorch = get("Comet / Sorc Focus·Scorch / Cut")
    comet_trans = get("Comet / Sorc Trans·GS / Cut")
    comet_trans_coup = get("Comet / Sorc Trans·GS / Coup")
    comet_dom = get("Comet / Dom Cheap·Tyrant·Eye / GS")
    dh_coup = get("DH / Sorc Focus·GS / Coup")
    aery = get("Aery / Sorc Focus·GS / Cut")
    fs = get("First Strike / Sorc Focus·GS / Cut")
    electro = get("Electro / Sorc Focus·GS / Cut")

    L.append("-" * 80)
    L.append("VERDICT")
    L.append("-" * 80)
    L.append(f"  {best.page.keystone} + {best.page.primary}: {', '.join(best.page.runes)}")
    L.append(f"  Secondary {best.page.secondary}.")
    L.append("")
    L.append("  KEYSTONE (build late, stack/soul từ phút 1):")
    if comet_cut and aery:
        L.append(
            f"  • Comet vs Aery {pct(comet_cut.late, aery.late)}. "
            f"Aery 5% AP / 70 base, không stack. Comet +2/hit suốt trận."
        )
    if comet_cut and electro:
        L.append(
            f"  • Comet vs Electro {pct(comet_cut.late, electro.late)}. "
            f"Electro CD 13s @15, 5% AP — không farm stack."
        )
    if comet_cut and fs:
        L.append(
            f"  • Comet vs First Strike {pct(comet_cut.late, fs.late)}. "
            f"7% true chỉ 3s đầu combat / CD 13s. Siege late không retrigger."
        )
    if comet_cut and dh_coup:
        L.append(
            f"  • Comet vs DH+Coup {pct(comet_cut.late, dh_coup.late)}. "
            f"DH cửa <50% đóng lúc poke 90%. Takedown 1s chỉ 1 phần fight."
        )
    L.append("  • Comet giữ: farm stack từ Rylai 8:00, late hit = base+2×stack+pen.")
    L.append("")
    L.append("  MINOR (late):")
    if comet_cut and comet_scorch:
        L.append(
            f"  • GS vs Scorch {pct(comet_cut.late, comet_scorch.late)}. "
            f"GS 70 AP @24, 88 @27, 108 @30, Cap ×1.30. Q 90% AP. "
            f"Comet chỉ 5% AP nhưng kit late thắng Scorch 49/8s."
        )
    if comet_cut and comet_trans:
        L.append(
            f"  • Transcendence vs Focus {pct(comet_trans.late, comet_cut.late)}. "
            f"Focus 30 AP tắt dưới 65% HP (cửa fight 32%). Trans 10 AH tăng Q/W "
            f"cả hai cửa. AH vẫn không giảm CD Comet — chỉ cadence kit."
        )
    if comet_trans_coup and comet_trans:
        L.append(
            f"  • Trans+Coup vs Trans+Cut {pct(comet_trans_coup.late, comet_trans.late)}. "
            f"Mix 50/50 late: Coup 8% @32%+Orb thắng Cut 6.57% @90%."
        )
    if comet_cut and comet_coup:
        L.append(
            f"  • Cut vs Coup (cùng Focus+GS) {pct(comet_coup.late, comet_cut.late)}. "
            f"Poke-only → Cut. Fight/Orb late → Coup."
        )
    if comet_cut and comet_cheap:
        L.append(
            f"  • Cut vs Cheap Shot {pct(comet_cheap.late, comet_cut.late)}. "
            f"Cheap 45 true / 7s trên Rylai slow. Cut nhân Q+W+Comet @90%."
        )
    if comet_trans and comet_dom:
        L.append(
            f"  • Trans+GS+Cut vs Dom Cheap+Tyrant+Eye+GS "
            f"{pct(comet_dom.late, comet_trans.late)}. "
            f"Dom giữ GS; Cheap/Tyrant mạnh cửa 32%."
        )
    L.append("")
    L.append("  PAGE:")
    L.append(f"  • Keystone {best.page.keystone}")
    L.append(f"  • Primary {best.page.primary}: {' · '.join(best.page.runes)}")
    L.append(f"  • Secondary {best.page.secondary}")
    L.append("  • Fork: Cut Down nếu siege poke 90%. Coup de Grace nếu fight/Orb.")
    L.append("  • Không Scorch (game late). Không First Strike. Không Electro.")
    L.append("=" * 80)
    return "\n".join(L)


def export_json(runs: List[Run], path: str) -> None:
    ranked = sorted(runs, key=lambda r: (r.late, r.full), reverse=True)
    payload = {
        "meta": {
            "champion": "Morgana",
            "patch": "7.2e",
            "core": "Rylai → Spell → Void → Orb → HF → Cap",
            "late_minutes": f"{LATE_START}-{GAME_MINUTES}",
            "mix": "50% @90% HP + 50% @32% HP",
            "loadout": "1 keystone + 3 primary + 1 secondary",
        },
        "winner": {
            "name": ranked[0].page.name,
            "keystone": ranked[0].page.keystone,
            "primary": ranked[0].page.primary,
            "runes": list(ranked[0].page.runes),
            "secondary": ranked[0].page.secondary,
            "late": round(ranked[0].late, 1),
        },
        "ranking": [
            {
                "name": r.page.name,
                "keystone": r.page.keystone,
                "late_20_30": round(r.late, 1),
                "full_1_30": round(r.full, 1),
                "stacks_30": round(r.minutes[-1].stacks, 2),
                "souls_30": round(r.minutes[-1].souls, 2),
            }
            for r in ranked
        ],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def self_check(runs: List[Run]) -> None:
    assert runs
    ranked = sorted(runs, key=lambda r: r.late, reverse=True)
    by = {r.page.name: r for r in ranked}
    comet = by["Comet / Sorc Focus·GS / Cut"]
    assert comet.minutes[-1].stacks > 40
    dh = by["DH / Sorc Focus·GS / Coup"]
    assert dh.minutes[-1].souls > 15
    # GS must beat Scorch on the late kit (Q 90% AP).
    scorch = by["Comet / Sorc Focus·Scorch / Cut"]
    assert comet.late > scorch.late, (comet.late, scorch.late)
    trans = by["Comet / Sorc Trans·GS / Cut"]
    trans_coup = by["Comet / Sorc Trans·GS / Coup"]
    assert trans.late > 0 and trans_coup.late > 0
    # Winner is a Comet page — stack farm is the late identity.
    assert ranked[0].page.keystone == "Comet", ranked[0].page.keystone
    # First Strike is a roam opener, not late siege DPM.
    fs = by["First Strike / Sorc Focus·GS / Cut"]
    assert fs.late < comet.late
    print("self-check OK")


def main() -> None:
    print("Simulating late rune pages on Rylai-Void-Orb-HF-Cap...", flush=True)
    owned_at = item_timeline(WIN_PATH)
    assert "Rylai's Crystal Scepter" in owned_at[7]
    assert "Rabadon's Deathcap" in owned_at[27] or "Rabadon's Deathcap" in owned_at[29]
    runs = [simulate(p, owned_at) for p in pages()]
    self_check(runs)
    report = summarize(runs)
    print(report)
    with open(os.path.join(OUT_DIR, "runes_report.txt"), "w", encoding="utf-8") as f:
        f.write(report + "\n")
    export_json(runs, os.path.join(OUT_DIR, "runes.json"))
    print(f"\nWrote {OUT_DIR}/runes_report.txt")


if __name__ == "__main__":
    main()
