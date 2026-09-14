#!/usr/bin/env python3
"""
WR 7.2e — Cut Down vs Coup de Grace vs Ingenious Hunter.

Not the same slot:
  Cut Down / Coup de Grace = Precision slot 2 (exclusive, + Last Stand).
  Ingenious Hunter         = Domination slot 3.

DH keystone + Gathering Storm secondary (locked) → primary is either
Domination (Ingenious) or Precision (Cut or Coup). Cannot take all three
and keep GS.

Cut Down 7.2: 6.57% vs champions >60% HP (was 8%).
Coup de Grace: 8% vs champions <40% HP.
Ingenious: 20 item haste + 5 per takedown (champ or epic), max 5 = 45 IH.
  Item haste reduces Luden Echo 10s. Does not reduce Q/E/R, DH, Scorch, Comet.
  One combo still has one Echo (6.9s > 2.5s).
"""

from __future__ import annotations

from typing import List, Tuple
import json
import os

from simulate_burst_dh import (
    DUMP_N,
    POKE_SET,
    SOULS,
    dump_dh,
    morgana_combo,
    stats_of,
    viktor_combo,
)
from simulate_qpm_dpm import (
    DAMAGE_BOOT,
    ECHO_CD,
    HF_MARK_S,
    ah_cd,
    burn,
    magic,
    morgana_q_cd,
    short,
    squishy,
    viktor_e_cd,
)
from simulate_scorch_gs import gs_ap

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
GAME_END = 25
GS_AP = gs_ap(GAME_END)
CUT = 1.0657
COUP = 1.08
IH_BASE = 20
IH_MAX = 45
BURST = [
    DAMAGE_BOOT,
    "Luden's Echo",
    "Infinity Orb",
    "Rabadon's Deathcap",
    "Stormsurge",
]


def echo_cd(item_haste: float) -> float:
    return ECHO_CD * 100.0 / (100.0 + max(0.0, item_haste))


def poke(
    champ: str,
    st,
    item_haste: float = 0.0,
    hp_mult: float = 1.0,
) -> Tuple[float, float, int]:
    """60s poke at 90% HP. hp_mult is constant (Cut on, Coup off)."""
    hp_max, mr = squishy()
    ecd = echo_cd(item_haste)
    t = 0.0
    echo_ready = 0.0
    mark_until = -99.0
    total = 0.0
    echos = 0
    if champ == "Morgana":
        gap = morgana_q_cd(st.ah)
        while t < 60.0 - 1e-9:
            marked = st.horizon and t < mark_until
            raw = 320.0 + 0.90 * st.ap
            if st.luden and t + 1e-9 >= echo_ready:
                raw += 140.0 + 0.15 * st.ap
                echo_ready = t + ecd
                echos += 1
            total += magic(raw, st, mr, marked) * hp_mult
            total += magic(burn(st, hp_max, 3.0), st, mr, marked) * hp_mult
            if st.horizon:
                mark_until = t + HF_MARK_S
            t += gap
        return 60.0 / gap, total, echos
    gap = viktor_e_cd(st.ah)
    while t < 60.0 - 1e-9:
        marked = st.horizon and t < mark_until
        laser = 210.0 + 0.30 * st.ap
        shock = 150.0 + 0.60 * st.ap
        echo = 0.0
        if st.luden and t + 1e-9 >= echo_ready:
            echo = 140.0 + 0.15 * st.ap
            echo_ready = t + ecd
            echos += 1
        total += magic(laser + echo, st, mr, marked) * hp_mult
        if st.horizon:
            mark_until = t + HF_MARK_S
            marked = True
        total += magic(shock, st, mr, marked) * hp_mult
        total += magic(burn(st, hp_max, 3.0), st, mr, marked) * hp_mult
        t += gap
    return 60.0 / gap, total, echos


def pack(names: List[str], champ: str, hp_rune: str, item_haste: float) -> dict:
    st = stats_of(names, GS_AP)
    fn = morgana_combo if champ == "Morgana" else viktor_combo
    c70 = fn(st, 0.70, SOULS, hp_rune=hp_rune)
    c40 = fn(st, 0.40, SOULS, hp_rune=hp_rune)
    c90 = fn(st, 0.90, SOULS, hp_rune=hp_rune)
    d35 = dump_dh(st, 0.35, DUMP_N, SOULS, st.horizon, hp_rune=hp_rune)
    d32 = dump_dh(st, 0.32, DUMP_N, SOULS, st.horizon, hp_rune=hp_rune)
    hp_mult = CUT if hp_rune == "cut" else 1.0
    _, poke_dpm, echos = poke(champ, st, item_haste, hp_mult)
    return {
        "combo70": c70.dealt,
        "combo40": c40.dealt,
        "combo90": c90.dealt,
        "dump35": d35,
        "dump32": d32,
        "poke_dpm": poke_dpm,
        "echos": echos,
        "ap": st.ap,
    }


def pct(num: float, den: float) -> str:
    return f"{100.0 * (num / den - 1.0):+.1f}%"


def champ_block(L: List[str], title: str, names: List[str], champ: str) -> dict:
    none = pack(names, champ, "", 0.0)
    cut = pack(names, champ, "cut", 0.0)
    coup = pack(names, champ, "coup", 0.0)
    ih20 = pack(names, champ, "", IH_BASE)
    ih45 = pack(names, champ, "", IH_MAX)
    L.append("-" * 78)
    L.append(title)
    L.append("-" * 78)
    L.append(f"  {short(names)}  GS {GS_AP:.0f} AP @25:00  AP {none['ap']:.0f}")
    L.append(
        f"  {'rune':<14} {'70%+R':>8} {'40%+R':>8} {'90%':>8} "
        f"{'dump35':>8} {'poke DPM':>9} {'Echo/60':>8}"
    )
    rows = [
        ("None", none),
        ("Cut Down", cut),
        ("Coup de Grace", coup),
        ("IH 20 (base)", ih20),
        ("IH 45 (max)", ih45),
    ]
    for label, r in rows:
        L.append(
            f"  {label:<14} {r['combo70']:8.0f} {r['combo40']:8.0f} {r['combo90']:8.0f} "
            f"{r['dump35']:8.0f} {r['poke_dpm']:9.0f} {r['echos']:8d}"
        )
    L.append("")
    L.append("  vs no Precision/IH rune")
    L.append(
        f"    Cut  combo70 {pct(cut['combo70'], none['combo70'])}  "
        f"combo40 {pct(cut['combo40'], none['combo40'])}  "
        f"poke {pct(cut['poke_dpm'], none['poke_dpm'])}  "
        f"dump35 {pct(cut['dump35'], none['dump35'])}"
    )
    L.append(
        f"    Coup combo70 {pct(coup['combo70'], none['combo70'])}  "
        f"combo40 {pct(coup['combo40'], none['combo40'])}  "
        f"poke {pct(coup['poke_dpm'], none['poke_dpm'])}  "
        f"dump35 {pct(coup['dump35'], none['dump35'])}"
    )
    L.append(
        f"    IH20 combo70 {pct(ih20['combo70'], none['combo70'])}  "
        f"poke {pct(ih20['poke_dpm'], none['poke_dpm'])}  "
        f"Echo {none['echos']}→{ih20['echos']}"
    )
    L.append(
        f"    IH45 combo70 {pct(ih45['combo70'], none['combo70'])}  "
        f"poke {pct(ih45['poke_dpm'], none['poke_dpm'])}  "
        f"Echo {none['echos']}→{ih45['echos']}"
    )
    L.append(
        f"  Cut vs Coup: combo70 {pct(cut['combo70'], coup['combo70'])}  "
        f"combo40 {pct(cut['combo40'], coup['combo40'])}  "
        f"poke {pct(cut['poke_dpm'], coup['poke_dpm'])}"
    )
    L.append("")
    return {"none": none, "cut": cut, "coup": coup, "ih20": ih20, "ih45": ih45}


def summarize() -> str:
    L: List[str] = []
    L.append("=" * 78)
    L.append("CUT DOWN vs COUP DE GRACE vs INGENIOUS HUNTER  (WR 7.2e)")
    L.append("DH + GS locked. Spell · Luden · Orb · Cap · Storm. Game 25m.")
    L.append("=" * 78)
    L.append("")
    L.append("4 Ô")
    L.append("-" * 78)
    L.append("  Client : Tốc Chiến 7.2e. Cut 6.57% >60% HP. Coup 8% <40% HP.")
    L.append("           IH 20 + 5×takedown (max 45) item haste. Không copy PC Giant Slayer.")
    L.append("  Role   : mid. DH keystone. GS secondary (70 AP @25:00). Giữ Luden.")
    L.append("  Cặp    : Cut vs Coup (Precision 2). IH (Domination 3) vs Cut/Coup")
    L.append("           khi primary đổi để giữ GS.")
    L.append("  Metric : combo 70%+R (burst), combo 40% (execute), poke 90% 60s,")
    L.append("           4×DH dump @35% (cửa Coup+Orb). Echo count cho IH.")
    L.append("")
    L.append("  Slot: Cut và Coup loại nhau. IH không cùng slot.")
    L.append("  DH + GS → primary Domination (IH) hoặc Precision (Cut/Coup), không cả hai.")
    L.append("")
    mb = champ_block(L, "BURST — Morgana", BURST, "Morgana")
    vb = champ_block(L, "BURST — Viktor", BURST, "Viktor")
    mp = champ_block(L, "POKE SET — Morgana", POKE_SET, "Morgana")
    vp = champ_block(L, "POKE SET — Viktor", POKE_SET, "Viktor")

    L.append("-" * 78)
    L.append("VERDICT")
    L.append("-" * 78)
    L.append("  Không chọn 1 trong 3 trên cùng slot. Cut vs Coup = Precision 2.")
    L.append("  IH = Domination 3. Với DH+GS: primary Dom (IH) hoặc Precision (Cut/Coup).")
    cut70 = mb["cut"]["combo70"]
    coup70 = mb["coup"]["combo70"]
    if cut70 >= coup70:
        L.append("  Burst combo 70%+R: Cut Down (hit đầu >60% là phần lớn burst).")
    else:
        L.append("  Burst combo 70%+R: Coup de Grace (Q hạ dưới 40%, phần còn lại + DH dump).")
    L.append(
        f"    Morgana Cut vs Coup combo70 {pct(mb['cut']['combo70'], mb['coup']['combo70'])}  "
        f"combo40 {pct(mb['cut']['combo40'], mb['coup']['combo40'])}  "
        f"poke {pct(mb['cut']['poke_dpm'], mb['coup']['poke_dpm'])}"
    )
    L.append(
        f"    Viktor  Cut vs Coup combo70 {pct(vb['cut']['combo70'], vb['coup']['combo70'])}  "
        f"combo40 {pct(vb['cut']['combo40'], vb['coup']['combo40'])}  "
        f"poke {pct(vb['cut']['poke_dpm'], vb['coup']['poke_dpm'])}"
    )
    L.append("  Poke 90%: Cut +6.57% cả kit. Coup = 0 (cửa 40% đóng).")
    L.append("  DH dump @35% (Orb+Coup): Coup +8%, Cut 0. Coup đúng cửa DH/Orb.")
    L.append(
        f"  Ingenious: 0 trên 1 combo (Echo CD vẫn > burst). "
        f"Burst Morgana IH45 Echo {mb['none']['echos']}→{mb['ih45']['echos']} "
        f"poke {pct(mb['ih45']['poke_dpm'], mb['none']['poke_dpm'])}. "
        f"Viktor burst IH45 {pct(vb['ih45']['poke_dpm'], vb['none']['poke_dpm'])} "
        f"(E đã nhanh hơn Echo)."
    )
    L.append("  Giữ GS (70 AP > Cut +2% / Coup +5% combo). DH burst → Precision Coup.")
    L.append("  IH (Dom primary) chỉ khi muốn Echo/poke; 0 damage trên all-in.")
    L.append("  Cut chỉ khi metric là poke 90%. Đừng Coup cho poke; đừng Cut cho execute.")
    L.append("=" * 78)
    # silence unused
    _ = (mp, vp)
    return "\n".join(L)


def export_json(path: str) -> None:
    def all_pack(names: List[str], champ: str) -> dict:
        return {
            "none": pack(names, champ, "", 0.0),
            "cut": pack(names, champ, "cut", 0.0),
            "coup": pack(names, champ, "coup", 0.0),
            "ih20": pack(names, champ, "", IH_BASE),
            "ih45": pack(names, champ, "", IH_MAX),
        }

    payload = {
        "meta": {
            "patch": "7.2e",
            "cut": "6.57% if target >60% HP",
            "coup": "8% if target <40% HP",
            "ingenious": "20 + 5*takedowns item haste, cap 45",
            "gs_ap_25": GS_AP,
            "slots": {
                "cut_coup": "Precision 2",
                "ingenious": "Domination 3",
            },
        },
        "burst_morgana": all_pack(BURST, "Morgana"),
        "burst_viktor": all_pack(BURST, "Viktor"),
        "poke_morgana": all_pack(POKE_SET, "Morgana"),
        "poke_viktor": all_pack(POKE_SET, "Viktor"),
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def self_check() -> None:
    st = stats_of(BURST, GS_AP)
    none = morgana_combo(st, 0.70, SOULS, hp_rune="")
    cut = morgana_combo(st, 0.70, SOULS, hp_rune="cut")
    coup = morgana_combo(st, 0.70, SOULS, hp_rune="coup")
    assert cut.dealt > none.dealt
    assert coup.dealt > none.dealt
    c40_cut = morgana_combo(st, 0.40, SOULS, hp_rune="cut")
    c40_coup = morgana_combo(st, 0.40, SOULS, hp_rune="coup")
    assert abs(c40_cut.dealt - none.dealt) < 1e-6 or c40_cut.dealt <= none.dealt + 1e-6
    # 40% start: Cut off, Coup on.
    assert c40_coup.dealt > c40_cut.dealt
    d0 = dump_dh(st, 0.35, DUMP_N, SOULS, False, hp_rune="")
    dcoup = dump_dh(st, 0.35, DUMP_N, SOULS, False, hp_rune="coup")
    dcut = dump_dh(st, 0.35, DUMP_N, SOULS, False, hp_rune="cut")
    assert dcoup > d0
    assert abs(dcut - d0) < 1e-6
    _, p0, e0 = poke("Morgana", st, 0.0, 1.0)
    _, p45, e45 = poke("Morgana", st, IH_MAX, 1.0)
    assert e45 > e0
    assert p45 > p0
    _, pcut, _ = poke("Morgana", st, 0.0, CUT)
    _, pcoup, _ = poke("Morgana", st, 0.0, 1.0)
    assert pcut > pcoup
    assert abs(echo_cd(0.0) - 10.0) < 1e-9
    assert abs(echo_cd(100.0) - 5.0) < 1e-9
    print("self-check OK")


def main() -> None:
    self_check()
    report = summarize()
    print(report)
    with open(os.path.join(OUT_DIR, "cut_coup_ih_report.txt"), "w", encoding="utf-8") as f:
        f.write(report + "\n")
    export_json(os.path.join(OUT_DIR, "cut_coup_ih.json"))
    print(f"\nWrote {OUT_DIR}/cut_coup_ih_report.txt")


if __name__ == "__main__":
    main()
