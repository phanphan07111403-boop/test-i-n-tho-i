#!/usr/bin/env python3
"""
WR 7.2e — Dark Harvest burst 5-slot, takedown reset 1s.

Keep Luden. Ignore gold. Spellslinger (max-damage boot already locked).
Poke DPM winner (Luden·HF·BF·Crypt) is the control, not the metric.

Metric: one all-in combo on a squishy, then 4 extra DH procs at 1s CD
(the reset). Not 60s poke DPM. AH does not reduce DH CD.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import List, Optional
import json
import os

from simulate_qpm_dpm import (
    DAMAGE_BOOT,
    DAMAGE_FOUR,
    HF_AMP,
    ITEMS,
    LEGENDS,
    PCT_EXCLUSIVE,
    LEVEL,
    Stats,
    pen_mult,
    short,
    squishy,
    trans_ah,
)

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
SOULS = 8
SOULS_HI = 10
DUMP_N = 4
SQUALL_NEED = 0.25
VIKTOR_AD = 54.0 + 3.5 * (LEVEL - 1)
ROOT_S = 2.75
BURST_S = 2.5
POKE_SET = [DAMAGE_BOOT, *DAMAGE_FOUR]


def stats_of(names: List[str], extra_ap: float = 0.0) -> Stats:
    """Deathcap amps total AP, including items listed after Cap and rune AP."""
    ap = ah = flat = pct = 0.0
    luden = orb = horizon = bf = li = False
    cap = False
    for n in names:
        it = ITEMS[n]
        ap += it.ap
        ah += it.ah
        flat += it.flat_mpen
        pct += it.pct_mpen
        luden = luden or it.luden
        orb = orb or it.orb
        horizon = horizon or it.horizon
        bf = bf or it.blackfire
        li = li or it.liandry
        cap = cap or it.deathcap
    ap += extra_ap
    if cap:
        ap *= 1.30
    ah += trans_ah()
    if bf:
        ap *= 1.04
    return Stats(list(names), ap, ah, flat, pct, luden, orb, horizon, bf, li)


def dh_raw(ap: float, souls: int) -> float:
    return 35.0 + 11.0 * souls + 0.05 * ap


def squall_raw(ap: float) -> float:
    return 125.0 + 0.10 * ap


def echo_raw(st: Stats) -> float:
    return (140.0 + 0.15 * st.ap) if st.luden else 0.0


def strike(raw: float, st: Stats, mr: float, frac: float, hf: bool) -> float:
    dmg = raw * pen_mult(st, mr)
    if hf:
        dmg *= HF_AMP
    if st.orb and frac <= 0.35:
        dmg *= 1.20
    return dmg


class Fight:
    def __init__(self, st: Stats, start_frac: float, souls: int, hp_rune: str = ""):
        self.st = st
        self.souls = souls
        self.hp_rune = hp_rune
        hp_max, mr = squishy()
        self.hp_max = hp_max
        self.mr = mr
        self.hp = start_frac * hp_max
        self.dealt = 0.0
        self.dh = 0
        self.orb_hits = 0
        self.hf = False
        self.window = 0.0
        self.squall = 0.0

    @property
    def frac(self) -> float:
        return self.hp / self.hp_max

    def rune_mult(self, frac: float) -> float:
        if self.hp_rune == "cut" and frac > 0.60:
            return 1.0657
        if self.hp_rune == "coup" and frac < 0.40:
            return 1.08
        return 1.0

    def hit(self, raw: float, apply_hf: bool = False, allow_dh: bool = True) -> float:
        frac = self.frac
        if self.st.orb and frac <= 0.35:
            self.orb_hits += 1
        dmg = strike(raw, self.st, self.mr, frac, self.hf) * self.rune_mult(frac)
        self.hp -= dmg
        self.dealt += dmg
        self.window += dmg
        if apply_hf and self.st.horizon:
            self.hf = True
        if allow_dh and self.dh == 0 and self.hp <= 0.50 * self.hp_max:
            self.dh_once()
        return dmg

    def dh_once(self) -> float:
        frac = self.frac
        raw = dh_raw(self.st.ap, self.souls)
        if self.st.orb and frac <= 0.35:
            self.orb_hits += 1
        dmg = strike(raw, self.st, self.mr, frac, self.hf) * self.rune_mult(frac)
        self.hp -= dmg
        self.dealt += dmg
        self.window += dmg
        self.dh += 1
        return dmg

    def maybe_squall(self) -> float:
        if "Stormsurge" not in self.st.names:
            return 0.0
        if self.window + 1e-9 < SQUALL_NEED * self.hp_max:
            return 0.0
        dmg = strike(squall_raw(self.st.ap), self.st, self.mr, self.frac, self.hf)
        dmg *= self.rune_mult(self.frac)
        self.hp -= dmg
        self.dealt += dmg
        self.squall = dmg
        return dmg


def burn_lump(st: Stats, hp_max: float, seconds: float) -> float:
    dps = 0.0
    if st.blackfire:
        dps += 20.0 + 0.02 * st.ap
    if st.liandry:
        dps += 0.02 * hp_max
    return dps * seconds


def morgana_combo(st: Stats, start_frac: float, souls: int = SOULS, hp_rune: str = "") -> Fight:
    """Q+Echo (HF apply) → DH → R → W ticks in the root → burn → Squall."""
    f = Fight(st, start_frac, souls, hp_rune=hp_rune)
    q = 320.0 + 0.90 * st.ap + echo_raw(st)
    f.hit(q, apply_hf=True)
    f.hit(300.0 + 0.70 * st.ap)
    missing = 1.0 - max(0.05, f.frac)
    w_amp = 1.0 + 1.7 * min(0.7, missing)
    tick = (22.0 + 0.07 * st.ap) * w_amp
    ticks = int(ROOT_S / 0.5)
    burn = burn_lump(st, f.hp_max, ROOT_S) / max(1, ticks)
    for _ in range(ticks):
        missing = 1.0 - max(0.05, f.frac)
        w_amp = 1.0 + 1.7 * min(0.7, missing)
        tick = (22.0 + 0.07 * st.ap) * w_amp
        f.hit(tick + burn)
    f.maybe_squall()
    return f


def viktor_combo(st: Stats, start_frac: float, souls: int = SOULS, hp_rune: str = "") -> Fight:
    """E laser+Echo (HF apply) → DH → Q+AA → Blastquake → R initial → burn → Squall.

    No 5.5s Chaos Storm ticks — that is dwell, not burst.
    """
    f = Fight(st, start_frac, souls, hp_rune=hp_rune)
    laser = 210.0 + 0.30 * st.ap + echo_raw(st)
    f.hit(laser, apply_hf=True)
    q = 90.0 + 0.30 * st.ap
    aa = 80.0 + VIKTOR_AD + 0.40 * st.ap
    f.hit(q + aa)
    f.hit(150.0 + 0.60 * st.ap)
    f.hit(250.0 + 0.60 * st.ap)
    f.hit(burn_lump(st, f.hp_max, BURST_S))
    f.maybe_squall()
    return f


def dump_dh(st: Stats, frac: float, n: int, souls: int, hf_on: bool, hp_rune: str = "") -> float:
    """n Dark Harvest procs after a takedown (1s CD). Fresh target at `frac`."""
    _, mr = squishy()
    total = 0.0
    hp_max, _ = squishy()
    hp = frac * hp_max
    for _ in range(n):
        f = hp / hp_max
        dmg = strike(dh_raw(st.ap, souls), st, mr, f, hf_on)
        if hp_rune == "cut" and f > 0.60:
            dmg *= 1.0657
        elif hp_rune == "coup" and f < 0.40:
            dmg *= 1.08
        hp -= dmg
        total += dmg
        hp = frac * hp_max
    return total


def luden_sets() -> List[List[str]]:
    rest = [n for n in LEGENDS if n != "Luden's Echo"]
    out: List[List[str]] = []
    for three in combinations(rest, 3):
        if len(set(three) & PCT_EXCLUSIVE) == 2:
            continue
        out.append([DAMAGE_BOOT, "Luden's Echo", *three])
    return out


@dataclass
class Row:
    champ: str
    items: List[str]
    ap: float
    ah: float
    burst70: float
    burst40: float
    dump40: float
    dump32: float
    total: float
    dh70: int
    squall70: float
    hp_left: float


def eval_champ(champ: str, souls: int = SOULS) -> List[Row]:
    rows: List[Row] = []
    fn = morgana_combo if champ == "Morgana" else viktor_combo
    for names in luden_sets():
        st = stats_of(names)
        a70 = fn(st, 0.70, souls)
        a40 = fn(st, 0.40, souls)
        d40 = dump_dh(st, 0.40, DUMP_N, souls, st.horizon)
        d32 = dump_dh(st, 0.32, DUMP_N, souls, st.horizon)
        rows.append(
            Row(
                champ,
                names,
                round(st.ap, 1),
                round(st.ah, 1),
                a70.dealt,
                a40.dealt,
                d40,
                d32,
                a70.dealt + d40,
                a70.dh,
                a70.squall,
                max(0.0, a70.hp / a70.hp_max),
            )
        )
    return rows


def exact(rows: List[Row], names: List[str]) -> Optional[Row]:
    want = set(names)
    for r in rows:
        if set(r.items) == want:
            return r
    return None


def top_n(rows: List[Row], key: str, n: int = 8) -> List[Row]:
    return sorted(rows, key=lambda r: getattr(r, key), reverse=True)[:n]


def pick_max(rows: List[Row], key: str) -> Row:
    return max(rows, key=lambda r: getattr(r, key))


def pct(num: float, den: float) -> str:
    return f"{100.0 * (num / den - 1.0):+.1f}%"


def named(four: List[str]) -> List[str]:
    return [DAMAGE_BOOT, "Luden's Echo", *four]


FEATURED = [
    ["Infinity Orb", "Rabadon's Deathcap", "Stormsurge"],
    ["Infinity Orb", "Rabadon's Deathcap", "Horizon Focus"],
    ["Infinity Orb", "Rabadon's Deathcap", "Void Staff"],
    ["Infinity Orb", "Rabadon's Deathcap", "Blackfire Torch"],
    ["Infinity Orb", "Rabadon's Deathcap", "Cryptbloom"],
    ["Infinity Orb", "Horizon Focus", "Stormsurge"],
    ["Rabadon's Deathcap", "Horizon Focus", "Stormsurge"],
    ["Rabadon's Deathcap", "Stormsurge", "Void Staff"],
    ["Infinity Orb", "Stormsurge", "Void Staff"],
    ["Horizon Focus", "Blackfire Torch", "Cryptbloom"],
]


def champ_block(L: List[str], title: str, rows: List[Row], poke: Row) -> None:
    best70 = pick_max(rows, "burst70")
    best_tot = pick_max(rows, "total")
    L.append("-" * 78)
    L.append(title)
    L.append("-" * 78)
    L.append(
        f"  Burst 70%+R     {best70.burst70:7.0f}  AP {best70.ap:.0f}  AH {best70.ah:.0f}  "
        f"HP left {100*best70.hp_left:.0f}%  {short(best70.items)}"
    )
    L.append(
        f"  Burst+4 DH dump {best_tot.total:7.0f}  "
        f"combo {best_tot.burst70:.0f} + dump40 {best_tot.dump40:.0f}  {short(best_tot.items)}"
    )
    L.append(
        f"  Poke-DPM set    {poke.burst70:7.0f}  combo  {pct(poke.burst70, best70.burst70)}  "
        f"dump40 {pct(poke.dump40, best70.dump40)}  {short(poke.items)}"
    )
    L.append("")
    L.append("  Top 5 combo @70%+R")
    for r in top_n(rows, "burst70", 5):
        L.append(
            f"    {r.burst70:7.0f}  @40% {r.burst40:7.0f}  dump40 {r.dump40:5.0f}  "
            f"dump32 {r.dump32:5.0f}  AP {r.ap:.0f}  {short(r.items)}"
        )
    L.append("")
    L.append("  Featured Luden 3-sets vs winner")
    for four in FEATURED:
        row = exact(rows, named(four))
        if not row:
            continue
        mark = "  ← poke DPM set" if four == ["Horizon Focus", "Blackfire Torch", "Cryptbloom"] else ""
        L.append(
            f"    {row.burst70:7.0f} ({pct(row.burst70, best70.burst70)})  "
            f"dump40 {row.dump40:.0f}  dump32 {row.dump32:.0f}  {short(row.items)}{mark}"
        )
    L.append("")


def summarize(morg: List[Row], vik: List[Row]) -> str:
    mp = exact(morg, POKE_SET)
    vp = exact(vik, POKE_SET)
    assert mp and vp
    mb = pick_max(morg, "burst70")
    vb = pick_max(vik, "burst70")
    mt = pick_max(morg, "total")
    vt = pick_max(vik, "total")
    L: List[str] = []
    L.append("=" * 78)
    L.append("DH BURST — takedown reset 1s  (WR 7.2e)")
    L.append("Giữ Luden. Spellslinger. Bỏ vàng. lv15 / phút 20 / 8 souls.")
    L.append("=" * 78)
    L.append("")
    L.append("4 Ô")
    L.append("-" * 78)
    L.append("  Client : Tốc Chiến 7.2e. DH 35+11×soul+5% AP, <50%, 35s / 1s takedown.")
    L.append("  Role   : mid. Giữ Luden. Spell (max-damage boot). Không copy support Ionia.")
    L.append("  Cặp    : 5-slot burst nhất vs poke-DPM set (Spell·Luden·HF·BF·Crypt).")
    L.append("  Metric : combo Q/E+R trên squishy 70% (Orb cửa 35%, DH cửa 50%),")
    L.append("           rồi 4 DH dump 1s trên target 40% (HF 10% chỉ khi có HF). Không phải DPM poke.")
    L.append("")
    L.append("  Morgana: Q+Echo → DH → R → W 2.75s root. Viktor: E laser+Echo → Q+AA")
    L.append("           → Blastquake → R initial (không 5.5s tick). Stormsurge Squall")
    L.append("           nếu combo ≥25% max HP / 2.5s (125+10% AP, delay 2s).")
    L.append("  Orb 20% chỉ khi target đã <35% TRƯỚC hit. HF 10% không amp hit apply.")
    L.append("")
    champ_block(L, "MORGANA — burst 5-slot (Spell · Luden · ?)", morg, mp)
    champ_block(L, "VIKTOR — burst 5-slot (Spell · Luden · ?)", vik, vp)

    L.append("-" * 78)
    L.append("VERDICT — burst nhất khi DH reset 1s")
    L.append("-" * 78)
    L.append(f"  Morgana: {short(mb.items)}")
    L.append(
        f"    combo70 {mb.burst70:.0f}  combo40 {mb.burst40:.0f}  "
        f"4×DH@40% {mb.dump40:.0f}  total {mb.total:.0f}"
    )
    L.append(
        f"    vs poke set {pct(mp.burst70, mb.burst70)} combo  "
        f"{pct(mp.dump40, mb.dump40)} dump40  {short(mp.items)}"
    )
    L.append(f"  Viktor : {short(vb.items)}")
    L.append(
        f"    combo70 {vb.burst70:.0f}  combo40 {vb.burst40:.0f}  "
        f"4×DH@40% {vb.dump40:.0f}  total {vb.total:.0f}"
    )
    L.append(
        f"    vs poke set {pct(vp.burst70, vb.burst70)} combo  "
        f"{pct(vp.dump40, vb.dump40)} dump40  {short(vp.items)}"
    )
    same = set(mb.items) == set(mt.items) and set(vb.items) == set(vt.items)
    if same:
        L.append("  Combo @70% và combo+dump chọn cùng 5-slot.")
    else:
        L.append(f"  Dump đổi Morgana → {short(mt.items)}" if set(mb.items) != set(mt.items) else "  Dump không đổi Morgana.")
        L.append(f"  Dump đổi Viktor  → {short(vt.items)}" if set(vb.items) != set(vt.items) else "  Dump không đổi Viktor.")
    L.append("  Reset 1s = spam DH, không spam Q. AH (HF/Crypt/BF/Crimson) không giảm DH CD.")
    L.append("  Cap amp mỗi DH. Orb 20% trên dump nếu target đã <35%. HF 10% chỉ khi có HF.")
    m_storm = exact(morg, named(["Infinity Orb", "Rabadon's Deathcap", "Stormsurge"]))
    m_void = exact(morg, named(["Infinity Orb", "Rabadon's Deathcap", "Void Staff"]))
    v_storm = exact(vik, named(["Infinity Orb", "Rabadon's Deathcap", "Stormsurge"]))
    v_void = exact(vik, named(["Infinity Orb", "Rabadon's Deathcap", "Void Staff"]))
    if m_storm and m_void and v_storm and v_void:
        L.append(
            f"  Slot 4 Storm vs Void: combo70 Morgana {pct(m_void.burst70, m_storm.burst70)}  "
            f"Viktor {pct(v_void.burst70, v_storm.burst70)}."
        )
        L.append(
            f"    dump@40% Void {pct(m_void.dump40, m_storm.dump40)}  "
            f"dump@32% Void {pct(m_void.dump32, m_storm.dump32)}  "
            "(cùng Orb — gap là 40% pen, không phải execute 20%)."
        )
    L.append("  Poke set thắng 60s DPM 90%; thua burst vì 0 Cap / 0 Orb / 0 Storm.")
    L.append("=" * 78)
    return "\n".join(L)


def export_json(morg: List[Row], vik: List[Row], path: str) -> None:
    def pack_row(r: Row) -> dict:
        return {
            "items": r.items,
            "ap": r.ap,
            "ah": r.ah,
            "burst70": round(r.burst70, 1),
            "burst40": round(r.burst40, 1),
            "dump40": round(r.dump40, 1),
            "dump32": round(r.dump32, 1),
            "total": round(r.total, 1),
            "hp_left_70": round(r.hp_left, 3),
        }

    payload = {
        "meta": {
            "patch": "7.2e",
            "keep_luden": True,
            "boot": DAMAGE_BOOT,
            "souls": SOULS,
            "dh_reset_s": 1.0,
            "dump_n": DUMP_N,
            "metric": "combo from 70% + 4 DH dumps at 40% after takedown reset",
        },
        "morgana": {
            "burst_winner": pack_row(pick_max(morg, "burst70")),
            "dump_winner": pack_row(pick_max(morg, "total")),
            "poke_set": pack_row(exact(morg, POKE_SET)),
        },
        "viktor": {
            "burst_winner": pack_row(pick_max(vik, "burst70")),
            "dump_winner": pack_row(pick_max(vik, "total")),
            "poke_set": pack_row(exact(vik, POKE_SET)),
        },
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def self_check(morg: List[Row], vik: List[Row]) -> None:
    # Deathcap amps items listed after it (Storm is after Cap in LEGENDS).
    cap_storm = stats_of(
        [
            DAMAGE_BOOT,
            "Luden's Echo",
            "Infinity Orb",
            "Rabadon's Deathcap",
            "Stormsurge",
        ]
    )
    raw = (
        ITEMS[DAMAGE_BOOT].ap
        + ITEMS["Luden's Echo"].ap
        + ITEMS["Infinity Orb"].ap
        + ITEMS["Rabadon's Deathcap"].ap
        + ITEMS["Stormsurge"].ap
    )
    assert abs(cap_storm.ap - raw * 1.30) < 1e-6, cap_storm.ap

    mb = pick_max(morg, "burst70")
    vb = pick_max(vik, "burst70")
    mp = exact(morg, POKE_SET)
    vp = exact(vik, POKE_SET)
    assert mp and vp
    assert "Luden's Echo" in mb.items and DAMAGE_BOOT in mb.items
    assert "Luden's Echo" in vb.items and DAMAGE_BOOT in vb.items
    assert mb.burst70 > mp.burst70
    assert vb.burst70 > vp.burst70
    assert mb.dump40 > mp.dump40
    # Poke set has no Cap/Orb — burst should pick at least one execute item.
    burst_items = set(mb.items) | set(vb.items)
    assert "Rabadon's Deathcap" in burst_items or "Infinity Orb" in burst_items
    # 10 souls must not flip the Morgana 70% winner vs poke set.
    m10 = eval_champ("Morgana", SOULS_HI)
    assert pick_max(m10, "burst70").burst70 > exact(m10, POKE_SET).burst70
    print("self-check OK")


def main() -> None:
    morg = eval_champ("Morgana")
    vik = eval_champ("Viktor")
    self_check(morg, vik)
    report = summarize(morg, vik)
    print(report)
    with open(os.path.join(OUT_DIR, "burst_dh_report.txt"), "w", encoding="utf-8") as f:
        f.write(report + "\n")
    export_json(morg, vik, os.path.join(OUT_DIR, "burst_dh.json"))
    print(f"\nWrote {OUT_DIR}/burst_dh_report.txt")
    print(f"Inventories scored: {len(morg)} per champion")


if __name__ == "__main__":
    main()
