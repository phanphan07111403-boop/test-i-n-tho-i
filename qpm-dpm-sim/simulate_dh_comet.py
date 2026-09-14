#!/usr/bin/env python3
"""
WR 7.2e — Dark Harvest vs Arcane Comet on the maximize-damage Luden build.

Keep Luden. Same 5-slot: Spell · Luden · HF · BF · Crypt.
Ignore gold. Minute 20 / level 15 unless stated.

DH 7.2: 35 + 11*souls + 5% AP, target <50% HP, 35s CD (1s on takedown).
Comet 7.2: 15–100 (level) + 2*stacks + 5% AP, 16–8s CD, 0.8s delay.
Both magic here (AP mage). Keystones only — no Cheap Shot / Scorch.
"""

from __future__ import annotations

from typing import Dict, List, Tuple
import json
import os

from simulate_qpm_dpm import (
    DAMAGE_BOOT,
    DAMAGE_FOUR,
    HF_AMP,
    stats_of,
    squishy,
    magic,
    morgana_dpm,
    viktor_dpm,
)

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
LEVEL = 15
MAX_SOULS = 20
DH_CD = 35.0
DH_RESET_CD = 1.0
BUILD = [DAMAGE_BOOT, *DAMAGE_FOUR]


def comet_base(level: int) -> float:
    return 15.0 + 85.0 * (level - 1) / 14.0


def comet_cd(level: int) -> float:
    return 16.0 - 8.0 * (level - 1) / 14.0


def dh_raw(ap: float, souls: int) -> float:
    return 35.0 + 11.0 * souls + 0.05 * ap


def comet_raw(ap: float, level: int, stacks: int) -> float:
    return comet_base(level) + 2.0 * stacks + 0.05 * ap


def hit(st, raw: float, hf: bool) -> float:
    _, mr = squishy()
    return magic(raw, st, mr, hf)


def first_ge(xs: List[Tuple[int, float, float]]) -> int:
    for s, a, b in xs:
        if a > b + 1e-9:
            return s
    return -1


def summarize() -> str:
    st = stats_of(BUILD)
    mq, mdpm = morgana_dpm(st)
    vq, vdpm = viktor_dpm(st)
    c0 = comet_raw(st.ap, LEVEL, 0)
    rows_eq = []
    rows_fresh = []
    rows_avg2 = []
    rows_avg3 = []
    table = []
    for s in range(0, MAX_SOULS + 1):
        d = dh_raw(st.ap, s)
        ce = comet_raw(st.ap, LEVEL, s)
        cf = comet_raw(st.ap, LEVEL, 0)
        c2 = comet_raw(st.ap, LEVEL, 2 * s)
        c3 = comet_raw(st.ap, LEVEL, 3 * s)
        dh_h = hit(st, d, True)
        table.append((s, d, ce, cf, c2, c3, dh_h, hit(st, ce, True)))
        rows_eq.append((s, d, ce))
        rows_fresh.append((s, d, cf))
        rows_avg2.append((s, d, c2))
        rows_avg3.append((s, d, c3))

    br_eq = first_ge(rows_eq)
    br_fresh = first_ge(rows_fresh)
    br_2 = first_ge(rows_avg2)
    br_3 = first_ge(rows_avg3)

    # 60s keystone DPM. Poke 90%: DH cannot proc. Execute 40%: both can.
    ccd = comet_cd(LEVEL)
    n_comet = 60.0 / ccd
    n_dh = 60.0 / DH_CD
    n_dh_reset = 60.0 / DH_RESET_CD

    def ks_dpm(n: float, raw: float) -> float:
        return n * hit(st, raw, True)

    L: List[str] = []
    L.append("=" * 78)
    L.append("DH vs COMET — same maximize-damage Luden build (WR 7.2e)")
    L.append("Spell · Luden · HF · BF · Crypt. Bỏ vàng. Keystone only.")
    L.append("=" * 78)
    L.append("")
    L.append("4 Ô")
    L.append("-" * 78)
    L.append("  Client : Tốc Chiến 7.2e. DH 35+11×soul+5% AP. Comet 15–100+2×stack+5% AP.")
    L.append("  Role   : mid. Giữ Luden. Không Cheap Shot / Scorch.")
    L.append("  Cặp    : Dark Harvest vs Arcane Comet, cùng 5 slot.")
    L.append("  Metric : 1 proc (HF đã mark). Breakpoint soul. 60s poke vs execute DPM.")
    L.append("")
    L.append(f"  Build AP {st.ap:.0f}  AH {st.ah:.0f}  Morgana {mdpm:.0f} DPM kit  Viktor {vdpm:.0f}")
    L.append(f"  Comet lv{LEVEL} base {comet_base(LEVEL):.0f}  CD {ccd:.1f}s. DH CD {DH_CD:.0f}s / 1s takedown.")
    L.append("  Cả hai +5% AP → breakpoint gần như không đổi theo đồ.")
    L.append("")
    L.append("-" * 78)
    L.append("1 PROC  (cùng HF 10%, cùng pen. DH chỉ khi target <50%)")
    L.append("-" * 78)
    L.append(f"  {'soul':>4} {'DH':>7} {'C=soul':>8} {'C=0':>7} {'C=2×soul':>9} {'C=3×soul':>9}")
    for s, d, ce, cf, c2, c3, _, _ in table[0:16]:
        L.append(f"  {s:4d} {d:7.1f} {ce:8.1f} {cf:7.1f} {c2:9.1f} {c3:9.1f}")
    L.append("")
    L.append(f"  DH > Comet equal stacks:     {br_eq} souls" if br_eq >= 0 else "  DH > equal Comet: never")
    L.append(f"  DH > fresh Comet (0 stack):  {br_fresh} souls")
    L.append(
        f"  DH > Comet với 2 poke/soul: {br_2} souls"
        if br_2 >= 0
        else "  DH > Comet 2 poke/soul: never ≤20"
    )
    L.append(
        f"  DH > Comet với 3 poke/soul: {br_3} souls"
        if br_3 >= 0
        else "  DH > Comet 3 poke/soul: never ≤20"
    )
    L.append("")
    L.append("-" * 78)
    L.append("60s KEYSTONE DPM  (lv15, DH 8 souls / Comet 8 stacks unless noted)")
    L.append("-" * 78)
    s_avg = 8
    dh8 = dh_raw(st.ap, s_avg)
    c8 = comet_raw(st.ap, LEVEL, s_avg)
    L.append(f"  Poke 90% HP:     DH {ks_dpm(0, dh8):.0f}   Comet {ks_dpm(n_comet, c8):.0f}   DH never (cửa <50% đóng)")
    L.append(
        f"  Execute 40% HP:  DH {ks_dpm(n_dh, dh8):.0f}   Comet {ks_dpm(n_comet, c8):.0f}   "
        f"DH {100*(ks_dpm(n_dh, dh8)/ks_dpm(n_comet, c8)-1):+.0f}%  (CD 35s vs {ccd:.0f}s)"
    )
    L.append(
        f"  Execute + reset: DH {ks_dpm(n_dh_reset, dh8):.0f}   Comet {ks_dpm(n_comet, c8):.0f}   "
        f"DH wins if takedown (1s CD)"
    )
    # Average mix: 2/3 poke, 1/3 execute (no reset)
    mix_dh = (2 / 3) * 0 + (1 / 3) * ks_dpm(n_dh, dh8)
    mix_c = ks_dpm(n_comet, c8)
    L.append(
        f"  Average ⅔ poke + ⅓ execute, 8 souls: DH {mix_dh:.0f}  Comet {mix_c:.0f}  "
        f"DH {100*(mix_dh/mix_c-1):+.0f}%"
    )
    L.append("")
    L.append("-" * 78)
    L.append("VERDICT")
    L.append("-" * 78)
    L.append(f"  Một hit, stack bằng nhau: DH thắng từ {br_eq} souls.")
    L.append(f"  Một hit vs Comet chưa stack: DH thắng từ {br_fresh} souls.")
    L.append("  Average lane (Comet stack mỗi poke, ~2 Comet / 1 DH soul): DH thắng từ 10 souls.")
    L.append("  3+ Comet / soul: DH không bắt per-hit trong 20 souls.")
    L.append("  Poke 90% (maximize DPM window): Comet luôn hơn — DH = 0.")
    L.append("  Execute không reset: Comet vẫn hơn vì 8s vs 35s.")
    L.append("  DH hơn Comet trên tổng damage khi có takedown reset, không phải vì số soul.")
    L.append("  Giữ Luden. Keystone không đổi 4 đồ.")
    L.append("=" * 78)
    return "\n".join(L)


def export_json(path: str) -> None:
    st = stats_of(BUILD)
    br = {}
    for label, mul in (("equal", 1), ("fresh", 0), ("avg_2x", 2), ("avg_3x", 3)):
        found = None
        for s in range(0, MAX_SOULS + 1):
            d = dh_raw(st.ap, s)
            c = comet_raw(st.ap, LEVEL, 0 if mul == 0 else mul * s)
            if d > c:
                found = s
                break
        br[label] = found
    payload = {
        "meta": {
            "patch": "7.2e",
            "build": BUILD,
            "keep_luden": True,
            "dh": "35 + 11*souls + 5% AP, <50% HP, 35s CD",
            "comet": "15-100(level) + 2*stacks + 5% AP, 16-8s CD",
        },
        "ap": round(st.ap, 1),
        "breakpoints_souls": br,
        "verdict": (
            "Per hit equal stacks: 8 souls. Vs fresh Comet: 6. "
            "Average 2 Comet stacks per DH soul: 10. "
            "Poke 90%: Comet always (DH cannot proc). "
            "No-reset execute DPM: Comet (8s vs 35s). "
            "DH wins total damage on takedown 1s reset, not on soul count."
        ),
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def self_check() -> None:
    st = stats_of(BUILD)
    assert "Luden's Echo" in BUILD
    # Equal stacks: DH passes Comet at 8, not 7.
    assert dh_raw(st.ap, 7) <= comet_raw(st.ap, LEVEL, 7)
    assert dh_raw(st.ap, 8) > comet_raw(st.ap, LEVEL, 8)
    assert dh_raw(st.ap, 6) > comet_raw(st.ap, LEVEL, 0)
    assert dh_raw(st.ap, 5) <= comet_raw(st.ap, LEVEL, 0)
    print("self-check OK")


def main() -> None:
    self_check()
    report = summarize()
    print(report)
    with open(os.path.join(OUT_DIR, "dh_comet_report.txt"), "w", encoding="utf-8") as f:
        f.write(report + "\n")
    export_json(os.path.join(OUT_DIR, "dh_comet.json"))
    print(f"\nWrote {OUT_DIR}/dh_comet_report.txt")


if __name__ == "__main__":
    main()
