#!/usr/bin/env python3
"""
WR 7.2e — Scorch vs Gathering Storm, average game 25:00.

Both are Sorcery slot 3 after 7.1 (mutually exclusive).
Keep Luden. Spellslinger. Ignore gold (finished 5-slot).

Scorch: 21–49 magic (lv1–15), 1s delay, 8s CD. AH does not reduce it.
Gathering Storm: first stack 6:00, then every 3:00. AP = x(x+3)
  6/9/12/15/18/21/24 → 4/10/18/28/40/54/70. Still 70 at 25:00 (next 27:00).
Deathcap amps GS AP.
"""

from __future__ import annotations

from typing import List, Optional, Tuple
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
    magic,
    morgana_dpm,
    pen_mult,
    short,
    squishy,
    viktor_dpm,
)

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
GAME_END = 25
SCORCH_CD = 8.0
BURST = [
    DAMAGE_BOOT,
    "Luden's Echo",
    "Infinity Orb",
    "Rabadon's Deathcap",
    "Stormsurge",
]
CLOCKS = [6, 9, 12, 15, 18, 21, 24, 25]


def gs_stacks(minute: float) -> int:
    if minute < 6:
        return 0
    return 1 + int((minute - 6) // 3)


def gs_ap(minute: float) -> float:
    x = gs_stacks(minute)
    return float(x * (x + 3))


def scorch_raw(level: int) -> float:
    return 21.0 + 28.0 * (level - 1) / 14.0


def level_at(minute: int) -> int:
    if minute >= 18:
        return 15
    table = {
        1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7, 7: 8, 8: 9,
        9: 10, 10: 11, 11: 11, 12: 12, 13: 12, 14: 13,
        15: 13, 16: 14, 17: 14,
    }
    return table.get(minute, 2)


def scorch_hit(st, level: int) -> float:
    """Pen only. Delayed burn is not ability damage for HF/Orb."""
    _, mr = squishy()
    return magic(scorch_raw(level), st, mr, hf_amp=False)


def scorch_dpm(st, level: int) -> Tuple[int, float]:
    n = 0
    t = 0.0
    total = 0.0
    hit = scorch_hit(st, level)
    while t < 60.0 - 1e-9:
        total += hit
        n += 1
        t += SCORCH_CD
    return n, total


def combo_of(champ: str, st, frac: float = 0.70):
    fn = morgana_combo if champ == "Morgana" else viktor_combo
    return fn(st, frac, SOULS)


def snapshot(names: List[str], champ: str, minute: int) -> dict:
    lv = level_at(minute)
    ap_gs = gs_ap(minute)
    st0 = stats_of(names, 0.0)
    stg = stats_of(names, ap_gs)
    c0 = combo_of(champ, st0)
    cg = combo_of(champ, stg)
    d0 = dump_dh(st0, 0.40, DUMP_N, SOULS, st0.horizon)
    dg = dump_dh(stg, 0.40, DUMP_N, SOULS, stg.horizon)
    poke_fn = morgana_dpm if champ == "Morgana" else viktor_dpm
    _, poke0 = poke_fn(st0)
    _, pokeg = poke_fn(stg)
    n, s_dpm = scorch_dpm(st0, lv)
    s_one = scorch_hit(st0, lv)
    return {
        "minute": minute,
        "level": lv,
        "gs_ap": ap_gs,
        "ap0": round(st0.ap, 1),
        "ap_gs": round(stg.ap, 1),
        "combo0": c0.dealt,
        "combo_gs": cg.dealt,
        "combo_delta": cg.dealt - c0.dealt,
        "dump0": d0,
        "dump_gs": dg,
        "dump_delta": dg - d0,
        "poke0": poke0,
        "poke_gs": pokeg,
        "poke_delta": pokeg - poke0,
        "scorch_one": s_one,
        "scorch_n": n,
        "scorch_dpm": s_dpm,
        "combo_gs_wins": (cg.dealt - c0.dealt) > s_one,
        "poke_gs_wins": (pokeg - poke0) > s_dpm,
        "total_gs_wins": (cg.dealt - c0.dealt + dg - d0) > s_one,
    }


def first_win(names: List[str], champ: str, key: str) -> Optional[int]:
    for m in CLOCKS:
        row = snapshot(names, champ, m)
        if row[key]:
            return m
    return None


def block(L: List[str], title: str, names: List[str], champ: str) -> None:
    end = snapshot(names, champ, GAME_END)
    L.append("-" * 78)
    L.append(title)
    L.append("-" * 78)
    L.append(f"  Build {short(names)}  AP {end['ap0']:.0f} → GS {end['ap_gs']:.0f} (+{end['gs_ap']:.0f} pre-amp)")
    L.append(
        f"  @25:00  combo0 {end['combo0']:.0f}  GS {end['combo_gs']:.0f}  "
        f"Δ {end['combo_delta']:.0f}  Scorch×1 {end['scorch_one']:.0f}"
    )
    L.append(
        f"          dump Δ {end['dump_delta']:.0f}  poke Δ {end['poke_delta']:.0f} DPM  "
        f"Scorch {end['scorch_n']}×/60s {end['scorch_dpm']:.0f} DPM"
    )
    combo_vs = end["combo_delta"] - end["scorch_one"]
    poke_vs = end["poke_delta"] - end["scorch_dpm"]
    L.append(
        f"  GS vs Scorch @25: combo {combo_vs:+.0f}  "
        f"poke 60s {poke_vs:+.0f}  "
        f"({'GS' if end['combo_gs_wins'] else 'Scorch'} combo, "
        f"{'GS' if end['poke_gs_wins'] else 'Scorch'} poke)"
    )
    L.append("")
    L.append(f"  {'min':>4} {'lv':>3} {'GS AP':>6} {'Δcombo':>8} {'Scorch':>7} {'Δpoke':>8} {'S-DPM':>7} {'combo':>6} {'poke':>6}")
    for m in CLOCKS:
        r = snapshot(names, champ, m)
        L.append(
            f"  {m:4d} {r['level']:3d} {r['gs_ap']:6.0f} {r['combo_delta']:8.0f} "
            f"{r['scorch_one']:7.0f} {r['poke_delta']:8.0f} {r['scorch_dpm']:7.0f} "
            f"{'GS':>6} {('GS' if r['poke_gs_wins'] else 'Scorch'):>6}"
            if r["combo_gs_wins"]
            else
            f"  {m:4d} {r['level']:3d} {r['gs_ap']:6.0f} {r['combo_delta']:8.0f} "
            f"{r['scorch_one']:7.0f} {r['poke_delta']:8.0f} {r['scorch_dpm']:7.0f} "
            f"{'Scorch':>6} {('GS' if r['poke_gs_wins'] else 'Scorch'):>6}"
        )
    br_c = first_win(names, champ, "combo_gs_wins")
    br_p = first_win(names, champ, "poke_gs_wins")
    L.append("")
    L.append(f"  GS > Scorch combo from minute {br_c}" if br_c else "  GS never beats 1 Scorch on combo ≤25")
    L.append(f"  GS > Scorch poke  from minute {br_p}" if br_p else "  GS never beats Scorch DPM ≤25")
    L.append("")


def summarize() -> str:
    L: List[str] = []
    L.append("=" * 78)
    L.append("SCORCH vs GATHERING STORM — game average 25:00  (WR 7.2e)")
    L.append("Sorcery slot 3. Giữ Luden. Spell. Bỏ vàng (5-slot xong).")
    L.append("=" * 78)
    L.append("")
    L.append("4 Ô")
    L.append("-" * 78)
    L.append("  Client : Tốc Chiến 7.2e. Scorch 21–49 / 8s. GS 6:00 rồi +3:00, AP=x(x+3).")
    L.append("           24:00–26:59 = 70 AP. Cap amp GS. Không copy PC 10-phút stack.")
    L.append("  Role   : mid. Game TB 25m. Giữ Luden. Spellslinger.")
    L.append("  Cặp    : Scorch vs Gathering Storm trên (1) burst Orb·Cap·Storm")
    L.append("           (2) poke Luden·HF·BF·Crypt.")
    L.append("  Metric : @25:00 combo 70%+R và 60s poke DPM. Breakpoint phút GS vượt Scorch.")
    L.append("           Scorch: pen only, CD không giảm bởi AH. 8 proc / 60s.")
    L.append("")
    L.append("  5-slot xong cả game (ignore gold). Cap phút 6 chưa có → GS early yếu hơn bảng.")
    L.append("")
    block(L, "BURST — Spell · Luden · Orb · Cap · Storm  (Morgana)", BURST, "Morgana")
    block(L, "BURST — Spell · Luden · Orb · Cap · Storm  (Viktor)", BURST, "Viktor")
    block(L, "POKE — Spell · Luden · HF · BF · Crypt  (Morgana)", POKE_SET, "Morgana")
    block(L, "POKE — Spell · Luden · HF · BF · Crypt  (Viktor)", POKE_SET, "Viktor")

    mb = snapshot(BURST, "Morgana", GAME_END)
    vb = snapshot(BURST, "Viktor", GAME_END)
    mp = snapshot(POKE_SET, "Morgana", GAME_END)
    vp = snapshot(POKE_SET, "Viktor", GAME_END)
    L.append("-" * 78)
    L.append("VERDICT — Scorch hay Gathering Storm, game TB 25m?")
    L.append("-" * 78)
    burst_combo = mb["combo_gs_wins"] and vb["combo_gs_wins"]
    burst_poke = mb["poke_gs_wins"] and vb["poke_gs_wins"]
    poke_combo = mp["combo_gs_wins"] and vp["combo_gs_wins"]
    poke_dpm = mp["poke_gs_wins"] and vp["poke_gs_wins"]
    if burst_combo and burst_poke and poke_combo and poke_dpm:
        L.append("  Gathering Storm. @25:00 GS thắng combo và poke DPM trên cả hai 5-slot.")
    elif burst_combo:
        L.append("  Burst DH: Gathering Storm. Poke lane: xem breakpoint.")
    else:
        L.append("  Scorch vẫn thắng snapshot 25m trên ít nhất một metric.")
    L.append(
        f"  Burst Morgana @25: GS combo Δ {mb['combo_delta']:.0f} vs Scorch {mb['scorch_one']:.0f}  "
        f"poke Δ {mb['poke_delta']:.0f} vs {mb['scorch_dpm']:.0f}"
    )
    L.append(
        f"  Burst Viktor  @25: GS combo Δ {vb['combo_delta']:.0f} vs Scorch {vb['scorch_one']:.0f}  "
        f"poke Δ {vb['poke_delta']:.0f} vs {vb['scorch_dpm']:.0f}"
    )
    L.append(
        f"  Poke  Morgana @25: GS combo Δ {mp['combo_delta']:.0f} vs Scorch {mp['scorch_one']:.0f}  "
        f"poke Δ {mp['poke_delta']:.0f} vs {mp['scorch_dpm']:.0f}"
    )
    L.append(
        f"  Poke  Viktor  @25: GS combo Δ {vp['combo_delta']:.0f} vs Scorch {vp['scorch_one']:.0f}  "
        f"poke Δ {vp['poke_delta']:.0f} vs {vp['scorch_dpm']:.0f}"
    )
    L.append(
        f"  Breakpoint burst Morgana: combo phút {first_win(BURST, 'Morgana', 'combo_gs_wins')}  "
        f"poke phút {first_win(BURST, 'Morgana', 'poke_gs_wins')}"
    )
    L.append(
        f"  Breakpoint poke Morgana:  combo phút {first_win(POKE_SET, 'Morgana', 'combo_gs_wins')}  "
        f"poke phút {first_win(POKE_SET, 'Morgana', 'poke_gs_wins')}"
    )
    L.append("  Scorch thắng lane trước stack đầu / trước Cap. Game 25m sống tới 70 AP → GS.")
    L.append("  AH không thêm Scorch proc (8s). Cap ×1.30 GS trên burst set.")
    L.append("=" * 78)
    return "\n".join(L)


def export_json(path: str) -> None:
    payload = {
        "meta": {
            "patch": "7.2e",
            "slot": "Sorcery 3",
            "game_end": GAME_END,
            "gs_ap_25": gs_ap(GAME_END),
            "scorch_cd": SCORCH_CD,
            "scorch_lv15": scorch_raw(15),
            "note": "GS AP = x(x+3), x=1 at 6:00 then +1 per 3:00. Cap amps GS.",
        },
        "burst": {
            "items": BURST,
            "morgana_25": snapshot(BURST, "Morgana", GAME_END),
            "viktor_25": snapshot(BURST, "Viktor", GAME_END),
            "morgana_combo_from": first_win(BURST, "Morgana", "combo_gs_wins"),
            "morgana_poke_from": first_win(BURST, "Morgana", "poke_gs_wins"),
        },
        "poke": {
            "items": POKE_SET,
            "morgana_25": snapshot(POKE_SET, "Morgana", GAME_END),
            "viktor_25": snapshot(POKE_SET, "Viktor", GAME_END),
            "morgana_combo_from": first_win(POKE_SET, "Morgana", "combo_gs_wins"),
            "morgana_poke_from": first_win(POKE_SET, "Morgana", "poke_gs_wins"),
        },
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def self_check() -> None:
    assert gs_ap(5) == 0
    assert gs_ap(6) == 4
    assert gs_ap(9) == 10
    assert gs_ap(12) == 18
    assert gs_ap(15) == 28
    assert gs_ap(18) == 40
    assert gs_ap(21) == 54
    assert gs_ap(24) == 70
    assert gs_ap(25) == 70
    assert gs_ap(27) == 88
    assert abs(scorch_raw(1) - 21.0) < 1e-9
    assert abs(scorch_raw(15) - 49.0) < 1e-9
    st0 = stats_of(BURST, 0.0)
    stg = stats_of(BURST, 70.0)
    # Cap amps the 70.
    assert stg.ap - st0.ap > 70.0
    assert abs((stg.ap - st0.ap) - 70.0 * 1.30) < 1e-6
    m = snapshot(BURST, "Morgana", GAME_END)
    assert m["scorch_n"] == 8
    assert m["combo_delta"] > 0
    n, _ = scorch_dpm(st0, 15)
    assert n == 8
    print("self-check OK")


def main() -> None:
    self_check()
    report = summarize()
    print(report)
    with open(os.path.join(OUT_DIR, "scorch_gs_report.txt"), "w", encoding="utf-8") as f:
        f.write(report + "\n")
    export_json(os.path.join(OUT_DIR, "scorch_gs.json"))
    print(f"\nWrote {OUT_DIR}/scorch_gs_report.txt")


if __name__ == "__main__":
    main()
