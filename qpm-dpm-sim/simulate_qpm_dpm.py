#!/usr/bin/env python3
"""
Wild Rift 7.2e — ignore gold. Finished 5-slot inventories that
maximize poke cadence (QPM / EPM) and poke DPM for Morgana and Viktor.

Locked:
  Client: Tốc Chiến. Not PC. T3 mage = 0% pen.
  Role: mid. Morgana Q-poke. Viktor E-poke (Death Ray is the poke button).
  Pair: every boots × 4-legendary set. No gold, no buy order, no spike.
  Metric: 60s poke on a squishy at 90% HP, minute 20 / level 15.
          QPM = Dark Binding / min. EPM = Death Ray / min (Viktor analog).

HF: +10% after a ≥600 ability; applying hit is not amped.
Viktor E: laser applies HF, Blastquake 1s later IS amped.
Echo: 140+15% AP / 10s. Orb 20% off at 90% HP.
Void and Cryptbloom are exclusive (% pen legendary).
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Dict, List, Optional, Tuple
import json
import os

MINUTE = 20
LEVEL = 15
ECHO_CD = 10.0
HF_AMP = 1.10
HF_MARK_S = 8.0
OUT_DIR = os.path.dirname(os.path.abspath(__file__))


@dataclass
class Item:
    name: str
    ap: float = 0
    ah: float = 0
    flat_mpen: float = 0
    pct_mpen: float = 0
    deathcap: bool = False
    luden: bool = False
    orb: bool = False
    horizon: bool = False
    blackfire: bool = False
    liandry: bool = False
    boots: bool = False


ITEMS: Dict[str, Item] = {
    "Spellslinger's Shoes": Item(
        "Spellslinger's Shoes", ap=40, flat_mpen=18, pct_mpen=0.08, boots=True,
    ),
    "Crimson Lucidity": Item(
        "Crimson Lucidity", ah=25, boots=True,
    ),
    "Luden's Echo": Item("Luden's Echo", ap=100, ah=10, luden=True),
    "Infinity Orb": Item("Infinity Orb", ap=110, flat_mpen=15, orb=True),
    "Horizon Focus": Item(
        "Horizon Focus", ap=80, ah=25, pct_mpen=0.07, horizon=True,
    ),
    "Rabadon's Deathcap": Item("Rabadon's Deathcap", ap=130, deathcap=True),
    "Blackfire Torch": Item("Blackfire Torch", ap=80, ah=20, blackfire=True),
    "Void Staff": Item("Void Staff", ap=95, pct_mpen=0.40),
    "Cryptbloom": Item("Cryptbloom", ap=70, ah=20, pct_mpen=0.30),
    "Cosmic Drive": Item("Cosmic Drive", ap=70, ah=25),
    "Stormsurge": Item("Stormsurge", ap=90, flat_mpen=15),
    "Seraph's Embrace": Item("Seraph's Embrace", ap=60, ah=25),
    "Liandry's Torment": Item("Liandry's Torment", ap=70, liandry=True),
}

BOOTS = ["Spellslinger's Shoes", "Crimson Lucidity"]
LEGENDS = [
    "Luden's Echo", "Infinity Orb", "Horizon Focus", "Rabadon's Deathcap",
    "Blackfire Torch", "Void Staff", "Cryptbloom", "Cosmic Drive",
    "Stormsurge", "Seraph's Embrace", "Liandry's Torment",
]
PCT_EXCLUSIVE = {"Void Staff", "Cryptbloom"}


def trans_ah() -> float:
    return 12.0


@dataclass
class Stats:
    names: List[str]
    ap: float
    ah: float
    flat_mpen: float
    pct_mpen: float
    luden: bool
    orb: bool
    horizon: bool
    blackfire: bool
    liandry: bool


def stats_of(names: List[str]) -> Stats:
    ap = ah = flat = pct = 0.0
    luden = orb = horizon = bf = li = False
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
        if it.deathcap:
            ap *= 1.30
    ah += trans_ah()
    if bf:
        ap *= 1.04
    return Stats(list(names), ap, ah, flat, pct, luden, orb, horizon, bf, li)


def pen_mult(st: Stats, mr: float) -> float:
    mr = mr * (1.0 - st.pct_mpen) - st.flat_mpen
    return 100.0 / (100.0 + max(8.0, mr))


def ah_cd(base: float, ah: float) -> float:
    return base * 100.0 / (100.0 + max(0.0, ah))


def squishy() -> Tuple[float, float]:
    hp = 620 + 95 * LEVEL + 18 * MINUTE
    mr = 32 + 1.25 * LEVEL + 16
    return hp, mr


def magic(raw: float, st: Stats, mr: float, hf_amp: bool) -> float:
    dmg = raw * pen_mult(st, mr)
    if hf_amp:
        dmg *= HF_AMP
    return dmg


def burn(st: Stats, hp: float, seconds: float) -> float:
    dps = 0.0
    if st.blackfire:
        dps += 20.0 + 0.02 * st.ap
    if st.liandry:
        dps += 0.02 * hp
    return dps * seconds


def morgana_q_cd(ah: float) -> float:
    return ah_cd(9.0, ah) * 0.95


def viktor_e_cd(ah: float) -> float:
    return ah_cd(7.0, ah)


def morgana_dpm(st: Stats) -> Tuple[float, float]:
    """Q spam 60s from 90% HP. Echo 10s. HF on Qs after the apply hit."""
    q_cd = morgana_q_cd(st.ah)
    hp_max, mr = squishy()
    t = 0.0
    echo_ready = 0.0
    mark_until = -99.0
    total = 0.0
    n = 0
    while t < 60.0 - 1e-9:
        marked = st.horizon and t < mark_until
        raw = 320.0 + 0.90 * st.ap
        if st.luden and t + 1e-9 >= echo_ready:
            raw += 140.0 + 0.15 * st.ap
            echo_ready = t + ECHO_CD
        total += magic(raw, st, mr, marked)
        total += magic(burn(st, hp_max, 3.0), st, mr, marked)
        if st.horizon:
            mark_until = t + HF_MARK_S
        n += 1
        t += q_cd
    return 60.0 / q_cd, total


def viktor_dpm(st: Stats) -> Tuple[float, float]:
    """E spam 60s. Laser applies HF; Blastquake 1s later is amped. Echo with laser."""
    e_cd = viktor_e_cd(st.ah)
    hp_max, mr = squishy()
    t = 0.0
    echo_ready = 0.0
    mark_until = -99.0
    total = 0.0
    while t < 60.0 - 1e-9:
        marked = st.horizon and t < mark_until
        laser = 210.0 + 0.30 * st.ap
        shock = 150.0 + 0.60 * st.ap
        echo = 0.0
        if st.luden and t + 1e-9 >= echo_ready:
            echo = 140.0 + 0.15 * st.ap
            echo_ready = t + ECHO_CD
        total += magic(laser + echo, st, mr, marked)
        if st.horizon:
            mark_until = t + HF_MARK_S
            marked = True
        total += magic(shock, st, mr, marked)
        total += magic(burn(st, hp_max, 3.0), st, mr, marked)
        t += e_cd
    return 60.0 / e_cd, total


@dataclass
class Row:
    champ: str
    items: List[str]
    ap: float
    ah: float
    cpm: float
    dpm: float


def legal_sets() -> List[List[str]]:
    out: List[List[str]] = []
    for boot in BOOTS:
        for four in combinations(LEGENDS, 4):
            s = set(four)
            if len(s & PCT_EXCLUSIVE) == 2:
                continue
            out.append([boot, *four])
    return out


def eval_champ(champ: str) -> List[Row]:
    rows: List[Row] = []
    fn = morgana_dpm if champ == "Morgana" else viktor_dpm
    for names in legal_sets():
        st = stats_of(names)
        cpm, dpm = fn(st)
        rows.append(Row(champ, names, round(st.ap, 1), round(st.ah, 1), cpm, dpm))
    return rows


def short(items: List[str]) -> str:
    nick = {
        "Spellslinger's Shoes": "Spell",
        "Crimson Lucidity": "Crimson",
        "Luden's Echo": "Luden",
        "Infinity Orb": "Orb",
        "Horizon Focus": "HF",
        "Rabadon's Deathcap": "Cap",
        "Blackfire Torch": "BF",
        "Void Staff": "Void",
        "Cryptbloom": "Crypt",
        "Cosmic Drive": "Cosmic",
        "Stormsurge": "Storm",
        "Seraph's Embrace": "Seraph",
        "Liandry's Torment": "Liandry",
    }
    return " · ".join(nick[n] for n in items)


def pct(num: float, den: float) -> str:
    return f"{100.0 * (num / den - 1.0):+.1f}%"


def top_n(rows: List[Row], key: str, n: int = 8) -> List[Row]:
    return sorted(rows, key=lambda r: getattr(r, key), reverse=True)[:n]


def pick_max(rows: List[Row], key: str) -> Row:
    return max(rows, key=lambda r: getattr(r, key))


def find(rows: List[Row], *must: str) -> Optional[Row]:
    need = set(must)
    hits = [r for r in rows if need <= set(r.items)]
    if not hits:
        return None
    return max(hits, key=lambda r: r.dpm)


def summarize(morg: List[Row], vik: List[Row]) -> str:
    mq, md = pick_max(morg, "cpm"), pick_max(morg, "dpm")
    vq, vd = pick_max(vik, "cpm"), pick_max(vik, "dpm")
    # Reference: previous Luden max-damage lock (gold-aware).
    lock_m = find(morg, "Spellslinger's Shoes", "Luden's Echo", "Infinity Orb", "Rabadon's Deathcap")
    lock_v = find(vik, "Spellslinger's Shoes", "Luden's Echo", "Infinity Orb", "Rabadon's Deathcap")
    L: List[str] = []
    L.append("=" * 78)
    L.append("IGNORE GOLD — MAX QPM / DPM  (WR 7.2e, mid, 5 slot xong trận)")
    L.append("Morgana = Dark Binding. Viktor = Death Ray (E). Squishy 90% HP, 60s poke.")
    L.append("=" * 78)
    L.append("")
    L.append("4 Ô")
    L.append("-" * 78)
    L.append("  Client : Tốc Chiến 7.2e. Không PC. T3 mage = 0 pen.")
    L.append("  Role   : mid. Bỏ vàng / spike / build path. Chỉ inventory.")
    L.append("  Cặp    : mọi boots × 4 legendary (Void XOR Cryptbloom).")
    L.append("  Metric : CPM (Q hoặc E / phút) và DPM poke 90%. HF 10% sau hit apply.")
    L.append("")
    L.append("QPM max = stack AH (Crimson 25 + HF/Cosmic/Seraph 25 + BF 20).")
    L.append("DPM max = Spell 18+8% + Echo + Cap 30% ± HF 10%/AH ± Orb 15 flat.")
    L.append("Hai metric lệch: Ionian/Crimson thắng QPM, thua DPM trên squishy.")
    L.append("")

    def block(title: str, rows: List[Row], qrow: Row, drow: Row, lock: Optional[Row], unit: str) -> None:
        L.append("-" * 78)
        L.append(title)
        L.append("-" * 78)
        L.append(f"  MAX {unit}: {short(qrow.items)}")
        L.append(f"           AP {qrow.ap:.0f}  AH {qrow.ah:.0f}  {unit} {qrow.cpm:.2f}  DPM {qrow.dpm:.0f}")
        L.append(f"  MAX DPM:  {short(drow.items)}")
        L.append(f"           AP {drow.ap:.0f}  AH {drow.ah:.0f}  {unit} {drow.cpm:.2f}  DPM {drow.dpm:.0f}")
        if lock:
            L.append(
                f"  Lock Luden·Orb·Cap·Spell: {unit} {lock.cpm:.2f}  DPM {lock.dpm:.0f}  "
                f"vs maxDPM {pct(lock.dpm, drow.dpm)}  vs max{unit} {pct(lock.cpm, qrow.cpm)}"
            )
        L.append(f"  MAX DPM vs MAX {unit}: DPM {pct(drow.dpm, qrow.dpm)}  {unit} {pct(drow.cpm, qrow.cpm)}")
        L.append("")
        L.append(f"  Top {unit}")
        for r in top_n(rows, "cpm", 5):
            L.append(
                f"    {r.cpm:5.2f} {unit}  DPM {r.dpm:7.0f}  AH {r.ah:5.0f}  {short(r.items)}"
            )
        L.append(f"  Top DPM")
        for r in top_n(rows, "dpm", 5):
            L.append(
                f"    DPM {r.dpm:7.0f}  {r.cpm:5.2f} {unit}  AP {r.ap:5.0f}  {short(r.items)}"
            )
        L.append("")

    block("MORGANA — Dark Binding Q", morg, mq, md, lock_m, "QPM")
    block("VIKTOR — Death Ray E  (Q Siphon không phải poke)", vik, vq, vd, lock_v, "EPM")

    L.append("-" * 78)
    L.append("VERDICT — bỏ vàng, maximize QPM và DPM")
    L.append("-" * 78)
    L.append(f"  Morgana max QPM: {short(mq.items)}")
    L.append(f"  Morgana max DPM: {short(md.items)}")
    L.append(f"  Viktor  max EPM: {short(vq.items)}")
    L.append(f"  Viktor  max DPM: {short(vd.items)}")
    L.append("  Build order không đổi số khi bỏ vàng — thứ tự = ưu tiên slot:")
    L.append("    QPM/EPM: Crimson → HF → Cosmic → Seraph → BF (132 AH).")
    L.append("    DPM: Spell → Luden → HF → BF → Crypt (Echo + 10% + burn + 30% pen + AH).")
    L.append("  Cap/Orb không vào max DPM @90%: Cap 0 AH, Orb 20% tắt khi full HP.")
    L.append("  Crimson thắng cadence (−19% CPM vs Spell-DPM), thua DPM vì mất 18+8% + 40 AP.")
    L.append("  Không max được cả hai cùng lúc. Muốn damage → Spell DPM set. Muốn spam → Crimson AH set.")
    L.append("=" * 78)
    return "\n".join(L)


def export_json(morg: List[Row], vik: List[Row], path: str) -> None:
    def pack(r: Row) -> dict:
        return {
            "items": r.items,
            "ap": r.ap,
            "ah": r.ah,
            "cpm": round(r.cpm, 3),
            "dpm": round(r.dpm, 1),
        }

    payload = {
        "meta": {
            "patch": "7.2e",
            "client": "Wild Rift",
            "gold": "ignored",
            "snapshot": "minute 20, level 15, squishy 90% HP, 60s poke",
            "morgana_spell": "Q Dark Binding",
            "viktor_spell": "E Death Ray (evolved)",
        },
        "morgana": {
            "max_qpm": pack(pick_max(morg, "cpm")),
            "max_dpm": pack(pick_max(morg, "dpm")),
            "top_qpm": [pack(r) for r in top_n(morg, "cpm", 8)],
            "top_dpm": [pack(r) for r in top_n(morg, "dpm", 8)],
        },
        "viktor": {
            "max_epm": pack(pick_max(vik, "cpm")),
            "max_dpm": pack(pick_max(vik, "dpm")),
            "top_epm": [pack(r) for r in top_n(vik, "cpm", 8)],
            "top_dpm": [pack(r) for r in top_n(vik, "dpm", 8)],
        },
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def self_check(morg: List[Row], vik: List[Row]) -> None:
    mq, md = pick_max(morg, "cpm"), pick_max(morg, "dpm")
    vq, vd = pick_max(vik, "cpm"), pick_max(vik, "dpm")
    assert "Crimson Lucidity" in mq.items
    assert "Crimson Lucidity" in vq.items
    assert "Spellslinger's Shoes" in md.items
    assert "Spellslinger's Shoes" in vd.items
    assert mq.cpm > md.cpm
    assert md.dpm > mq.dpm
    assert vq.cpm > vd.cpm
    assert vd.dpm > vq.dpm
    assert "Horizon Focus" in mq.items
    print("self-check OK")


def main() -> None:
    morg = eval_champ("Morgana")
    vik = eval_champ("Viktor")
    self_check(morg, vik)
    report = summarize(morg, vik)
    print(report)
    with open(os.path.join(OUT_DIR, "report.txt"), "w", encoding="utf-8") as f:
        f.write(report + "\n")
    export_json(morg, vik, os.path.join(OUT_DIR, "results.json"))
    print(f"\nWrote {OUT_DIR}/report.txt and {OUT_DIR}/results.json")
    print(f"Inventories scored: {len(morg)} per champion")


if __name__ == "__main__":
    main()
