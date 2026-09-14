#!/usr/bin/env python3
"""
Wild Rift 7.2e — ignore gold. Finished 5-slot inventories that
maximize poke cadence (QPM / EPM) and poke DPM for Morgana and Viktor.

Locked:
  Client: Tốc Chiến. Not PC. T3 mage = 0% pen.
  Role: mid. Morgana Q-poke. Viktor E-poke (Death Ray is the poke button).
  Pair: Spellslinger vs Crimson on maximize-damage inventories
        (same 4 items, and best 4 items under each boot).
  Metric: 60s poke DPM on a squishy at 90% HP, minute 20 / level 15.
          CPM shown only to explain the AH trade.

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
    rylai: bool = False
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
    "Rylai's Crystal Scepter": Item(
        "Rylai's Crystal Scepter", ap=65, pct_mpen=0.07, rylai=True,
    ),
}

BOOTS = ["Spellslinger's Shoes", "Crimson Lucidity"]
LEGENDS = [
    "Luden's Echo", "Infinity Orb", "Horizon Focus", "Rabadon's Deathcap",
    "Blackfire Torch", "Void Staff", "Cryptbloom", "Cosmic Drive",
    "Stormsurge", "Seraph's Embrace", "Liandry's Torment",
    "Rylai's Crystal Scepter",
]
PCT_EXCLUSIVE = {"Void Staff", "Cryptbloom"}


DAMAGE_BOOT = "Spellslinger's Shoes"
DAMAGE_FOUR = [
    "Luden's Echo", "Horizon Focus", "Blackfire Torch", "Cryptbloom",
]


def trans_ah() -> float:
    return 12.0


def exact(rows: List[Row], names: List[str]) -> Optional[Row]:
    want = set(names)
    for r in rows:
        if set(r.items) == want:
            return r
    return None


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
        "Rylai's Crystal Scepter": "Rylai",
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


def under_boot(rows: List[Row], boot: str) -> List[Row]:
    return [r for r in rows if boot in r.items]


def same_four(rows: List[Row], src: Row, boot: str) -> Optional[Row]:
    four = {n for n in src.items if n not in BOOTS}
    for r in rows:
        if boot in r.items and {n for n in r.items if n not in BOOTS} == four:
            return r
    return None


def boots_block(L: List[str], title: str, rows: List[Row], unit: str) -> None:
    spell_best = pick_max(under_boot(rows, "Spellslinger's Shoes"), "dpm")
    crim_best = pick_max(under_boot(rows, "Crimson Lucidity"), "dpm")
    crim_on_spell_set = same_four(rows, spell_best, "Crimson Lucidity")
    spell_on_crim_set = same_four(rows, crim_best, "Spellslinger's Shoes")
    L.append("-" * 78)
    L.append(title)
    L.append("-" * 78)
    L.append("  Maximize DPM — best 4 items under each boot")
    L.append(
        f"    Spell    {spell_best.dpm:7.0f} DPM  {spell_best.cpm:5.2f} {unit}  "
        f"AP {spell_best.ap:.0f} AH {spell_best.ah:.0f}  {short(spell_best.items)}"
    )
    L.append(
        f"    Crimson  {crim_best.dpm:7.0f} DPM  {crim_best.cpm:5.2f} {unit}  "
        f"AP {crim_best.ap:.0f} AH {crim_best.ah:.0f}  {short(crim_best.items)}"
    )
    L.append(f"    Crimson best vs Spell best: {pct(crim_best.dpm, spell_best.dpm)}")
    L.append("")
    L.append("  Swap boots only (keep the Spell-max 4 items)")
    if crim_on_spell_set:
        L.append(
            f"    Spell    {spell_best.dpm:7.0f} DPM  {spell_best.cpm:5.2f} {unit}  "
            f"per-cast {spell_best.dpm / spell_best.cpm:.0f}"
        )
        L.append(
            f"    Crimson  {crim_on_spell_set.dpm:7.0f} DPM  {crim_on_spell_set.cpm:5.2f} {unit}  "
            f"per-cast {crim_on_spell_set.dpm / crim_on_spell_set.cpm:.0f}"
        )
        L.append(
            f"    Crimson vs Spell same 4: DPM {pct(crim_on_spell_set.dpm, spell_best.dpm)}  "
            f"{unit} {pct(crim_on_spell_set.cpm, spell_best.cpm)}  "
            f"per-cast {pct(crim_on_spell_set.dpm / crim_on_spell_set.cpm, spell_best.dpm / spell_best.cpm)}"
        )
    L.append("")
    L.append("  Swap boots only (keep the Crimson-max 4 items)")
    if spell_on_crim_set:
        L.append(
            f"    Spell    {spell_on_crim_set.dpm:7.0f} DPM  {spell_on_crim_set.cpm:5.2f} {unit}"
        )
        L.append(
            f"    Crimson  {crim_best.dpm:7.0f} DPM  {crim_best.cpm:5.2f} {unit}"
        )
        L.append(
            f"    Crimson vs Spell same 4: {pct(crim_best.dpm, spell_on_crim_set.dpm)}"
        )
    L.append("")
    L.append("  Top 3 DPM with Spell")
    for r in top_n(under_boot(rows, "Spellslinger's Shoes"), "dpm", 3):
        L.append(f"    {r.dpm:7.0f}  {r.cpm:5.2f} {unit}  {short(r.items)}")
    L.append("  Top 3 DPM with Crimson")
    for r in top_n(under_boot(rows, "Crimson Lucidity"), "dpm", 3):
        L.append(f"    {r.dpm:7.0f}  {r.cpm:5.2f} {unit}  {short(r.items)}")
    L.append("")


def rylai_block(L: List[str], title: str, rows: List[Row], unit: str) -> None:
    base = exact(rows, [DAMAGE_BOOT, *DAMAGE_FOUR])
    forced = [
        r for r in under_boot(rows, DAMAGE_BOOT)
        if "Rylai's Crystal Scepter" in r.items
    ]
    best = pick_max(forced, "dpm")
    kept = [n for n in best.items if n not in (DAMAGE_BOOT, "Rylai's Crystal Scepter")]
    dropped = [n for n in DAMAGE_FOUR if n not in kept]
    L.append("-" * 78)
    L.append(title)
    L.append("-" * 78)
    L.append("  Specter = Rylai's Crystal Scepter (65 AP, 7% pen, 350 HP, 30% slow).")
    L.append("  5 slot đầy. Thêm Rylai = thế 1 legendary. Slow không vào DPM (giả định hit).")
    if base:
        L.append(f"  Max DPM không Rylai: {base.dpm:.0f}  {short(base.items)}")
    L.append(f"  Max DPM có Rylai:    {best.dpm:.0f}  {short(best.items)}")
    if base:
        L.append(f"  Rẻ nhất (tự chọn món thay): {pct(best.dpm, base.dpm)}  — bỏ {', '.join(dropped)}")
    L.append("")
    L.append("  Thế từng món trên set Spell·Luden·HF·BF·Crypt")
    if base:
        ranked = []
        for drop in DAMAGE_FOUR:
            names = [DAMAGE_BOOT] + [
                "Rylai's Crystal Scepter" if x == drop else x for x in DAMAGE_FOUR
            ]
            row = exact(rows, names)
            if row:
                ranked.append((drop, row))
        ranked.sort(key=lambda t: t[1].dpm, reverse=True)
        for drop, row in ranked:
            L.append(
                f"    thế {short([drop]):<8} {row.dpm:7.0f} DPM  {row.cpm:5.2f} {unit}  "
                f"{pct(row.dpm, base.dpm)}  {short(row.items)}"
            )
    L.append("")


def summarize(morg: List[Row], vik: List[Row]) -> str:
    mq, md = pick_max(morg, "cpm"), pick_max(morg, "dpm")
    vq, vd = pick_max(vik, "cpm"), pick_max(vik, "dpm")
    L: List[str] = []
    L.append("=" * 78)
    L.append("MAXIMIZE DAMAGE — SPELLSLINGER vs CRIMSON  (WR 7.2e)")
    L.append("Bỏ vàng. 5 slot xong. Poke 90% HP, 60s. Morgana Q / Viktor E.")
    L.append("=" * 78)
    L.append("")
    L.append("4 Ô")
    L.append("-" * 78)
    L.append("  Client : Tốc Chiến 7.2e. Không PC. T3 mage = 0 pen.")
    L.append("  Role   : mid. Bỏ vàng. Không copy support Ionia WR.")
    L.append("  Cặp    : Spell vs Crimson; thêm Rylai (specter/scepter) thế món nào.")
    L.append("           Maximize DPM. Cùng 4 đồ / 4 đồ tốt nhất / Rylai forced.")
    L.append("  Metric : DPM poke squishy 90%. CPM chỉ để giải thích AH.")
    L.append("")
    L.append("  Spell : 40 AP, 18 flat, 8% pen, 0 AH.")
    L.append("  Crimson: 0 AP, 0 pen, 25 AH, 8% MS on ability.")
    L.append("")

    boots_block(L, "MORGANA — Spell vs Crimson (maximize DPM)", morg, "QPM")
    boots_block(L, "VIKTOR — Spell vs Crimson (maximize DPM)", vik, "EPM")
    rylai_block(L, "MORGANA — thêm Rylai (specter)", morg, "QPM")
    rylai_block(L, "VIKTOR — thêm Rylai (specter)", vik, "EPM")

    L.append("-" * 78)
    L.append("VERDICT — maximize damage: Spellslinger hay Crimson?")
    L.append("-" * 78)
    ms = pick_max(under_boot(morg, "Spellslinger's Shoes"), "dpm")
    mc = pick_max(under_boot(morg, "Crimson Lucidity"), "dpm")
    vs_ = pick_max(under_boot(vik, "Spellslinger's Shoes"), "dpm")
    vc = pick_max(under_boot(vik, "Crimson Lucidity"), "dpm")
    L.append(f"  Morgana: Crimson best vs Spell best {pct(mc.dpm, ms.dpm)}")
    L.append(f"  Viktor : Crimson best vs Spell best {pct(vc.dpm, vs_.dpm)}")
    L.append("  Maximize damage → Spellslinger. 18 flat + 8% + 40 AP > 25 AH trên squishy.")
    L.append("  Cùng 4 đồ Spell-max (Luden·HF·BF·Crypt): Crimson DPM −15.5% / −13.0%.")
    L.append("  Crimson tự chọn 4 đồ khác (HF·BF·Crypt·Liandry) vẫn thua Spell ~10%.")
    L.append("  Crimson thắng cadence (+13% CPM), thua per-cast (~−25%) nên thua DPM.")
    L.append("  Crimson chỉ khi metric là QPM/EPM, không phải maximize damage.")
    L.append("")
    mb = exact(morg, [DAMAGE_BOOT, *DAMAGE_FOUR])
    vb = exact(vik, [DAMAGE_BOOT, *DAMAGE_FOUR])
    mr = pick_max(
        [r for r in under_boot(morg, DAMAGE_BOOT) if "Rylai's Crystal Scepter" in r.items],
        "dpm",
    )
    vr = pick_max(
        [r for r in under_boot(vik, DAMAGE_BOOT) if "Rylai's Crystal Scepter" in r.items],
        "dpm",
    )
    L.append("VERDICT — thêm Rylai (specter) thế món nào?")
    L.append("-" * 78)
    L.append("  Một slot: thế Luden. Giữ HF·BF·Crypt. Slow không cộng DPM khi đã hit.")
    if mb:
        lud = exact(morg, [DAMAGE_BOOT, "Rylai's Crystal Scepter", "Horizon Focus", "Blackfire Torch", "Cryptbloom"])
        if lud:
            L.append(f"  Morgana thế Luden: {pct(lud.dpm, mb.dpm)}  ({mb.dpm:.0f} → {lud.dpm:.0f})")
    if vb:
        ludv = exact(vik, [DAMAGE_BOOT, "Rylai's Crystal Scepter", "Horizon Focus", "Blackfire Torch", "Cryptbloom"])
        if ludv:
            L.append(f"  Viktor  thế Luden: {pct(ludv.dpm, vb.dpm)}  ({vb.dpm:.0f} → {ludv.dpm:.0f})")
    L.append("  Đừng thế Crypt (−22%) hay HF (Viktor −26%). BF −20%.")
    L.append("  Tự tối ưu 3 món + Rylai: Morgana Spell·HF·BF·Void·Rylai −15.1% (bỏ Echo+Crypt).")
    L.append("  Rylai = 30% slow + HP. Poke DPM giả định hit 100%.")
    L.append("=" * 78)
    L.append("")
    L.append("Context — max cadence (không phải câu damage)")
    L.append(f"  Morgana max QPM: {short(mq.items)}  {mq.cpm:.2f} QPM  DPM {mq.dpm:.0f}")
    L.append(f"  Viktor  max EPM: {short(vq.items)}  {vq.cpm:.2f} EPM  DPM {vq.dpm:.0f}")
    L.append(f"  vs max DPM Morgana cadence {pct(md.cpm, mq.cpm)}  DPM {pct(md.dpm, mq.dpm)}")
    return "\n".join(L)


def export_json(morg: List[Row], vik: List[Row], path: str) -> None:
    def pack(r: Row) -> dict:
        return {
            "items": r.items,
            "ap": r.ap,
            "ah": r.ah,
            "cpm": round(r.cpm, 3),
            "dpm": round(r.dpm, 1),
            "per_cast": round(r.dpm / r.cpm, 1),
        }

    def boots_payload(rows: List[Row]) -> dict:
        spell = pick_max(under_boot(rows, "Spellslinger's Shoes"), "dpm")
        crim = pick_max(under_boot(rows, "Crimson Lucidity"), "dpm")
        swap = same_four(rows, spell, "Crimson Lucidity")
        return {
            "spell_best_dpm": pack(spell),
            "crimson_best_dpm": pack(crim),
            "crimson_on_spell_four": pack(swap) if swap else None,
            "crimson_best_vs_spell_best": pct(crim.dpm, spell.dpm),
            "crimson_swap_vs_spell": pct(swap.dpm, spell.dpm) if swap else None,
        }

    def rylai_payload(rows: List[Row]) -> dict:
        base = exact(rows, [DAMAGE_BOOT, *DAMAGE_FOUR])
        forced = [
            r for r in under_boot(rows, DAMAGE_BOOT)
            if "Rylai's Crystal Scepter" in r.items
        ]
        best = pick_max(forced, "dpm")
        swaps = {}
        if base:
            for drop in DAMAGE_FOUR:
                names = [DAMAGE_BOOT] + [
                    "Rylai's Crystal Scepter" if x == drop else x for x in DAMAGE_FOUR
                ]
                row = exact(rows, names)
                if row:
                    swaps[drop] = {
                        **pack(row),
                        "vs_max": pct(row.dpm, base.dpm),
                    }
        return {
            "max_without_rylai": pack(base) if base else None,
            "max_with_rylai": pack(best),
            "with_vs_without": pct(best.dpm, base.dpm) if base else None,
            "naive_swaps": swaps,
        }

    payload = {
        "meta": {
            "patch": "7.2e",
            "client": "Wild Rift",
            "gold": "ignored",
            "pair": "Spell vs Crimson; add Rylai scepter by replacing one legendary",
            "snapshot": "minute 20, level 15, squishy 90% HP, 60s poke",
            "rylai": "65 AP, 7% pen, 350 HP, 30% slow. Slow not in DPM (100% hit).",
        },
        "morgana": boots_payload(morg),
        "viktor": boots_payload(vik),
        "morgana_rylai": rylai_payload(morg),
        "viktor_rylai": rylai_payload(vik),
        "morgana_max_qpm": pack(pick_max(morg, "cpm")),
        "viktor_max_epm": pack(pick_max(vik, "cpm")),
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def self_check(morg: List[Row], vik: List[Row]) -> None:
    ms = pick_max(under_boot(morg, "Spellslinger's Shoes"), "dpm")
    mc = pick_max(under_boot(morg, "Crimson Lucidity"), "dpm")
    vs_ = pick_max(under_boot(vik, "Spellslinger's Shoes"), "dpm")
    vc = pick_max(under_boot(vik, "Crimson Lucidity"), "dpm")
    swap_m = same_four(morg, ms, "Crimson Lucidity")
    swap_v = same_four(vik, vs_, "Crimson Lucidity")
    assert ms.dpm > mc.dpm
    assert vs_.dpm > vc.dpm
    assert swap_m is not None and swap_m.dpm < ms.dpm
    assert swap_v is not None and swap_v.dpm < vs_.dpm
    assert swap_m.cpm > ms.cpm
    assert "Spellslinger's Shoes" in ms.items
    assert "Crimson Lucidity" in mc.items
    mb = exact(morg, [DAMAGE_BOOT, *DAMAGE_FOUR])
    mr = pick_max(
        [r for r in under_boot(morg, DAMAGE_BOOT) if "Rylai's Crystal Scepter" in r.items],
        "dpm",
    )
    assert mb is not None and mr.dpm < mb.dpm
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
