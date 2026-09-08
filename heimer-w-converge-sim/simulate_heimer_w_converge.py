#!/usr/bin/env python3
"""
Wild Rift Heimerdinger — W auto-aim converge analysis.

Question: auto-aim luôn lấy tướng làm điểm tụ cả 5 tên lửa — có tác dụng không, có lời không?

Patch: 7.1g+ turret beam (55% AP). W values from WR wiki (Hextech Micro-Rockets).
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import List, Sequence


# ---------------------------------------------------------------------------
# Ability numbers (Wild Rift wiki)
# ---------------------------------------------------------------------------

W_INITIAL = (60, 85, 110, 135)  # + 60% AP, rank 1–4
W_AP = 0.60
W_SUBSEQUENT_CHAMP = 0.20  # same champion / monster
W_SUBSEQUENT_MINION = 0.60

# R+W Hextech Rocket Swarm — ranks follow R (1–3)
RW_FIRST = (135, 185, 235)  # + 45% AP
RW_FIRST_AP = 0.45
RW_2_TO_5 = (32, 45, 58)  # + 12% AP
RW_2_TO_5_AP = 0.12
RW_6_TO_20 = (16, 22.5, 29)  # + 6% AP
RW_6_TO_20_AP = 0.06
RW_ROCKETS = 20  # 4 waves × 5

# Q turret beam — patch 7.1g
BEAM = (25, 45, 65, 85)  # + 55% AP
BEAM_AP = 0.55
BEAM_CHARGE_PER_ROCKET = 0.20  # per rocket that hits a champion
BEAM_PASSIVE_PER_SEC = 0.0111

# E grenade — champion hit = 100% beam charge
E_DAMAGE = (70, 120, 170, 220)  # + 60% AP
E_AP = 0.60


def w_rank_damage(rank: int, ap: float, rockets: int, minion: bool = False) -> float:
    """Damage of `rockets` hitting the same unit. Rank is 1–4."""
    if rockets <= 0:
        return 0.0
    initial = W_INITIAL[rank - 1] + W_AP * ap
    pct = W_SUBSEQUENT_MINION if minion else W_SUBSEQUENT_CHAMP
    return initial * (1.0 + pct * (rockets - 1))


def rw_damage(r_rank: int, ap: float, rockets: int, minion: bool = False) -> float:
    """Damage of `rockets` from Hextech Rocket Swarm on one unit. R rank 1–3."""
    if rockets <= 0:
        return 0.0
    if minion:
        each = RW_FIRST[r_rank - 1] + RW_FIRST_AP * ap
        return each * rockets
    total = 0.0
    for i in range(1, rockets + 1):
        if i == 1:
            total += RW_FIRST[r_rank - 1] + RW_FIRST_AP * ap
        elif i <= 5:
            total += RW_2_TO_5[r_rank - 1] + RW_2_TO_5_AP * ap
        else:
            total += RW_6_TO_20[r_rank - 1] + RW_6_TO_20_AP * ap
    return total


def beam_damage(q_rank: int, ap: float) -> float:
    return BEAM[q_rank - 1] + BEAM_AP * ap


def beams_fired(rockets_on_champ: int, turret_start_charge: float, turrets: int) -> int:
    """How many turret lasers fire immediately from this W."""
    charge = min(1.0, turret_start_charge + BEAM_CHARGE_PER_ROCKET * rockets_on_champ)
    if charge >= 1.0 and turret_start_charge < 1.0:
        return turrets
    return 0


def magic_after_mr(raw: float, mr: float, flat_pen: float = 0.0, pct_pen: float = 0.0) -> float:
    effective = max(0.0, (mr - flat_pen) * (1.0 - pct_pen))
    return raw * (100.0 / (100.0 + effective))


# ---------------------------------------------------------------------------
# Snapshots: typical Heimer mid gold/AP, not a full item optimizer
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Snapshot:
    name: str
    minute: int
    w_rank: int
    q_rank: int
    e_rank: int
    r_rank: int
    ap: float
    turrets: int
    target_mr: float
    # Typical turret charge when you poke (passive + leftover)
    turret_charge: float


SNAPSHOTS: Sequence[Snapshot] = (
    # Typical max W → Q, E last.
    Snapshot("Lane early", 4, 2, 2, 1, 0, 70, 2, 42, 0.25),
    Snapshot("Lane spike (6)", 6, 3, 3, 1, 1, 140, 2, 48, 0.35),
    Snapshot("Mid item", 10, 4, 4, 1, 1, 260, 3, 55, 0.40),
    Snapshot("2-item+", 14, 4, 4, 2, 2, 380, 3, 62, 0.45),
    Snapshot("Late Deathcap", 18, 4, 4, 3, 3, 520, 3, 70, 0.50),
)


@dataclass
class ScenarioResult:
    label: str
    rockets_on_champ: int
    w_raw: float
    e_raw: float
    beam_raw: float
    total_raw: float
    total_after_mr: float
    beams: int
    notes: str


def e_damage(s: Snapshot) -> float:
    return E_DAMAGE[s.e_rank - 1] + E_AP * s.ap


def poke_scenarios(s: Snapshot) -> List[ScenarioResult]:
    """Single-target poke: auto-aim converge vs the other common W shapes."""
    out: List[ScenarioResult] = []
    one_beam = beam_damage(s.q_rank, s.ap)

    specs = [
        (
            "Auto-aim tụ 5/5 vào tướng (line sạch)",
            5,
            False,
            "Đúng điểm hội tụ. Max W + charge beam 100% từ 0%.",
        ),
        (
            "Auto-aim tụ tướng nhưng đứng sau lính",
            1,
            False,
            "Tên lửa chạm first-unit. 4 quả ăn lính, 1 quả lọt / hoặc 0.",
        ),
        (
            "Aim xa / quạt trước khi tụ (1–2 quả)",
            2,
            False,
            "Cursor max range: rocket còn đang xòe khi tới tướng.",
        ),
        (
            "Trượt điểm tụ (tướng bước ra)",
            0,
            False,
            "Auto-aim bắn vị trí hiện tại, rocket bay chậm → miss cả volley.",
        ),
        (
            "E stun + W 1 quả (không tụ)",
            1,
            True,
            "E đã bắn laser 1 lần. W 1 quả không nạp đủ laser 2.",
        ),
        (
            "E stun + auto-aim tụ 5/5",
            5,
            True,
            "E laser #1, W 5/5 nạp 100% lại → laser #2. Stun giữ điểm tụ.",
        ),
    ]
    for label, rockets, with_e, note in specs:
        w_raw = w_rank_damage(s.w_rank, s.ap, rockets)
        e_raw = e_damage(s) if with_e else 0.0
        if with_e:
            # E hitting a champion is 100% charge → volley 1, charge resets.
            # Then W rockets charge from 0. Need 5 hits to fire volley 2.
            beams = s.turrets + beams_fired(rockets, 0.0, s.turrets)
        else:
            beams = beams_fired(rockets, s.turret_charge, s.turrets)
        beam_raw = beams * one_beam
        total = w_raw + e_raw + beam_raw
        out.append(
            ScenarioResult(
                label=label,
                rockets_on_champ=rockets,
                w_raw=round(w_raw, 1),
                e_raw=round(e_raw, 1),
                beam_raw=round(beam_raw, 1),
                total_raw=round(total, 1),
                total_after_mr=round(magic_after_mr(total, s.target_mr), 1),
                beams=beams,
                notes=note,
            )
        )
    return out


def charge_table(q_rank: int, ap: float, turrets: int) -> List[dict]:
    """When does W actually pop lasers, by rocket count and starting charge."""
    rows = []
    beam = beam_damage(q_rank, ap)
    for start_pct in (0, 20, 40, 60, 80):
        row = {"start_charge": start_pct}
        for rockets in range(1, 6):
            n = beams_fired(rockets, start_pct / 100.0, turrets)
            row[f"r{rockets}_beams"] = n
            row[f"r{rockets}_beam_dmg"] = round(n * beam, 1)
        rows.append(row)
    return rows


def waveclear_vs_poke(s: Snapshot) -> dict:
    """
    Spread vs converge on a cannon wave.

    Spread: 5 rockets can each be a 'first hit' on 5 different minions → full damage each.
    Converge on champion behind wave: rockets die on the front minion (subsequent 60%).
    """
    full_minion = w_rank_damage(s.w_rank, s.ap, 1, minion=True)
    stacked_on_one_minion = w_rank_damage(s.w_rank, s.ap, 5, minion=True)
    spread_five_minions = full_minion * 5
    converge_champ_blocked = w_rank_damage(s.w_rank, s.ap, 0)  # none leak
    converge_champ_clean = w_rank_damage(s.w_rank, s.ap, 5)
    return {
        "one_rocket_minion": round(full_minion, 1),
        "five_stacked_one_minion": round(stacked_on_one_minion, 1),
        "spread_five_minions": round(spread_five_minions, 1),
        "auto_aim_champ_behind_wave": round(converge_champ_blocked, 1),
        "auto_aim_champ_clean": round(converge_champ_clean, 1),
        "spread_vs_stack_minion_ratio": round(spread_five_minions / max(stacked_on_one_minion, 1), 2),
    }


def multi_champ_tradeoff(s: Snapshot) -> dict:
    """One target 5 rockets vs three targets 1 rocket each (teamfight fan)."""
    one = w_rank_damage(s.w_rank, s.ap, 5)
    three = w_rank_damage(s.w_rank, s.ap, 1) * 3
    return {
        "one_champ_5_rockets": round(one, 1),
        "three_champs_1_each": round(three, 1),
        "winner": "tụ 1 tướng" if one >= three else "xòe 3 tướng",
        "ratio_spread_over_converge": round(three / max(one, 1), 2),
    }


def rw_compare(s: Snapshot) -> dict:
    if s.r_rank <= 0:
        return {"available": False}
    full = rw_damage(s.r_rank, s.ap, RW_ROCKETS)
    five = rw_damage(s.r_rank, s.ap, 5)  # only first wave connects
    one = rw_damage(s.r_rank, s.ap, 1)
    minion_full = rw_damage(s.r_rank, s.ap, RW_ROCKETS, minion=True)
    return {
        "available": True,
        "r_rank": s.r_rank,
        "full_20_on_champ": round(full, 1),
        "only_first_wave_5": round(five, 1),
        "only_1_rocket": round(one, 1),
        "full_vs_one_ratio": round(full / max(one, 1), 2),
        "minion_20_full_each": round(minion_full, 1),
        "note": "R+W bắt buộc tụ vào 1 tướng (hoặc E stun) mới ăn cap 503/702/902 + 175% AP.",
    }


def run() -> dict:
    payload = {
        "patch": "7.1g+",
        "question": (
            "Heimerdinger auto-aim luôn lấy tướng làm điểm tụ toàn bộ tên lửa "
            "— có tác dụng không, có lời không?"
        ),
        "verdict": {
            "has_effect": True,
            "profitable_when": [
                "Poke 1 tướng, line sạch hoặc sau last-hit",
                "Combo E stun → W tụ 5/5: laser lần 1 (E) + laser lần 2 (W nạp 100% lại)",
                "R+W burst 1 mục tiêu",
            ],
            "not_profitable_when": [
                "Clear lính: cần xòe để mỗi lính ăn first-hit 100%",
                "Tướng núp sau wave: auto-aim tụ vào tướng = rocket đấm lính",
                "Teamfight 3+ người đứng lệch: xòe 1 rocket/người > 5 rocket (20%) vào 1 người",
                "Kite không CC: auto-aim không lead, dễ miss cả volley",
            ],
        },
        "snapshots": [],
    }

    for s in SNAPSHOTS:
        poke = poke_scenarios(s)
        baseline = next(p for p in poke if "line sạch" in p.label)
        miss = next(p for p in poke if p.rockets_on_champ == 0)
        blocked = next(p for p in poke if "sau lính" in p.label)
        fan = next(p for p in poke if "quạt" in p.label)
        e_w1 = next(p for p in poke if "W 1 quả" in p.label)
        e_w5 = next(p for p in poke if "tụ 5/5" in p.label and p.label.startswith("E"))
        payload["snapshots"].append(
            {
                "meta": asdict(s),
                "w_one_rocket": round(w_rank_damage(s.w_rank, s.ap, 1), 1),
                "w_five_rockets": round(w_rank_damage(s.w_rank, s.ap, 5), 1),
                "w_multiplier_5_vs_1": round(
                    w_rank_damage(s.w_rank, s.ap, 5) / max(w_rank_damage(s.w_rank, s.ap, 1), 1),
                    2,
                ),
                "beam_each": round(beam_damage(s.q_rank, s.ap), 1),
                "passive_seconds_to_beam_from_0": round(1.0 / BEAM_PASSIVE_PER_SEC, 1),
                "poke": [asdict(p) for p in poke],
                "profit_vs_miss_after_mr": round(baseline.total_after_mr - miss.total_after_mr, 1),
                "profit_vs_blocked_after_mr": round(
                    baseline.total_after_mr - blocked.total_after_mr, 1
                ),
                "profit_vs_fan2_after_mr": round(baseline.total_after_mr - fan.total_after_mr, 1),
                "profit_e_w5_vs_e_w1_after_mr": round(
                    e_w5.total_after_mr - e_w1.total_after_mr, 1
                ),
                "charge_breakpoints": charge_table(s.q_rank, s.ap, s.turrets),
                "waveclear": waveclear_vs_poke(s),
                "teamfight": multi_champ_tradeoff(s),
                "rw": rw_compare(s),
            }
        )
    return payload


def report(data: dict) -> str:
    lines: List[str] = []
    lines.append("=" * 78)
    lines.append("HEIMERDINGER W — AUTO-AIM TỤ TÊN LỬA VÀO TƯỚNG (Wild Rift 7.1g+)")
    lines.append("Câu hỏi: auto-aim luôn lấy tướng làm điểm tụ 5 rocket — có tác dụng? có lời?")
    lines.append("=" * 78)
    lines.append("")
    lines.append("CƠ CHẾ (wiki WR)")
    lines.append("  W bắn 5 rocket, hội tụ tại điểm aim rồi xòe tiếp.")
    lines.append("  Auto-aim lock tướng = điểm hội tụ nằm đúng trên tướng → cả 5 quả cùng lúc.")
    lines.append("  Rocket 1: 100% damage. Rocket 2–5 cùng tướng: 20% mỗi quả.")
    lines.append("  Full 5/5 = 1.80× damage 1 quả  (108% AP, không phải 300% AP).")
    lines.append("  Mỗi rocket trúng tướng = +20% charge laser trụ. 5 quả = 100% → bắn ngay.")
    lines.append("  Laser trụ tự charge 1.11%/s (~90s từ 0%). W tụ 5 quả = skip cả phút chờ.")
    lines.append("  Rocket chạm first enemy — lính chắn là mất poke.")
    lines.append("")

    lines.append("-" * 78)
    lines.append("VERDICT")
    lines.append("-" * 78)
    lines.append("  CÓ TÁC DỤNG. Đây không phải cosmetic — đây là điểm ngọt single-target của W.")
    lines.append("  CÓ LỜI khi poke 1 tướng (line sạch / sau last-hit / sau E stun) và khi R+W.")
    lines.append("  KHÔNG LỜI nếu luôn-luôn auto-aim tướng: clear lính kém, dễ đấm wave,")
    lines.append("  teamfight xòe ra nhiều người còn nhiều damage hơn, kite không CC thì dễ miss.")
    lines.append("")
    lines.append("  Luật dùng:")
    lines.append("    Poke / all-in 1 người  → GIỮ auto-aim tụ vào tướng (hoặc E rồi W).")
    lines.append("    Clear wave / check bụi → KÉO aim xa để xòe, đừng lock tướng.")
    lines.append("    Tướng núp lính         → đừng bắn; đợi last-hit hoặc E trước.")
    lines.append("")

    lines.append("-" * 78)
    lines.append("DAMAGE W THEO SỐ ROCKET (công thức, mọi mốc AP)")
    lines.append("-" * 78)
    lines.append("  Hits | Damage vs 1 quả | Charge laser")
    lines.append("     1 | 1.00×           |  20%  (chưa bắn nếu trụ <80%)")
    lines.append("     2 | 1.20×           |  40%")
    lines.append("     3 | 1.40×           |  60%")
    lines.append("     4 | 1.60×           |  80%")
    lines.append("     5 | 1.80×  ← auto-aim tụ tướng")
    lines.append("       |                 | 100%  (laser chắc từ 0% charge)")
    lines.append("")
    lines.append("  Rank 4, 0 AP: 1 quả = 135.  5 quả = 243.  Không phải 675.")
    lines.append("  Lời của 4 quả phụ = +108 dmg (+48% AP), CỘNG instant laser.")
    lines.append("")

    for snap in data["snapshots"]:
        m = snap["meta"]
        lines.append("-" * 78)
        lines.append(
            f"{m['name'].upper()}  @ {m['minute']}:00  |  "
            f"W{m['w_rank']} Q{m['q_rank']} E{m['e_rank']} R{m['r_rank'] or '-'}  |  "
            f"{m['ap']:.0f} AP  |  {m['turrets']} trụ  |  target MR {m['target_mr']:.0f}"
        )
        lines.append("-" * 78)
        lines.append(
            f"  W 1 quả {snap['w_one_rocket']:.0f}  →  W 5 quả {snap['w_five_rockets']:.0f}  "
            f"({snap['w_multiplier_5_vs_1']:.2f}×)  |  "
            f"1 laser {snap['beam_each']:.0f}  |  passive beam {snap['passive_seconds_to_beam_from_0']:.0f}s"
        )
        lines.append("")
        lines.append(
            f"  {'Kịch bản':<42} {'W':>6} {'E':>6} {'Laser':>7} {'Raw':>7} {'Sau MR':>7} B"
        )
        for p in snap["poke"]:
            lines.append(
                f"  {p['label']:<42} {p['w_raw']:>6.0f} {p['e_raw']:>6.0f} "
                f"{p['beam_raw']:>7.0f} {p['total_raw']:>7.0f} "
                f"{p['total_after_mr']:>7.0f} {p['beams']}"
            )
        lines.append("")
        lines.append(
            f"  Lời auto-aim 5/5 vs miss:     +{snap['profit_vs_miss_after_mr']:.0f} (sau MR)"
        )
        lines.append(
            f"  Lời auto-aim 5/5 vs bị lính chặn: +{snap['profit_vs_blocked_after_mr']:.0f}"
        )
        lines.append(
            f"  Lời auto-aim 5/5 vs xòe 2 quả: +{snap['profit_vs_fan2_after_mr']:.0f}"
        )
        lines.append(
            f"  Lời combo E+W tụ 5/5 vs E+W 1 quả: +{snap['profit_e_w5_vs_e_w1_after_mr']:.0f}  "
            "(chênh lệch = laser #2 + 0.8× W)"
        )
        wc = snap["waveclear"]
        tf = snap["teamfight"]
        lines.append(
            f"  Clear lính: xòe 5 lính {wc['spread_five_minions']:.0f}  vs  "
            f"tụ 5 quả 1 lính {wc['five_stacked_one_minion']:.0f}  "
            f"({wc['spread_vs_stack_minion_ratio']:.2f}× nghiêng về XÒE)"
        )
        lines.append(
            f"  Teamfight: 1 tướng 5 quả {tf['one_champ_5_rockets']:.0f}  vs  "
            f"3 tướng 1 quả {tf['three_champs_1_each']:.0f}  "
            f"→ {tf['winner']} ({tf['ratio_spread_over_converge']:.2f}×)"
        )
        rw = snap["rw"]
        if rw.get("available"):
            lines.append(
                f"  R+W: full 20 {rw['full_20_on_champ']:.0f}  |  "
                f"chỉ wave 1 (5 quả) {rw['only_first_wave_5']:.0f}  |  "
                f"1 quả {rw['only_1_rocket']:.0f}  "
                f"({rw['full_vs_one_ratio']:.1f}× nếu tụ đủ)"
            )
        lines.append("")

    lines.append("-" * 78)
    lines.append("LASER BREAKPOINT — cần bao nhiêu rocket để bắn ngay")
    lines.append("-" * 78)
    # Use mid-item snapshot for the table
    mid = data["snapshots"][2]
    lines.append(f"  Mốc {mid['meta']['name']}: {mid['meta']['turrets']} trụ, mỗi laser {mid['beam_each']:.0f} raw")
    lines.append("  Charge sẵn | 1 rocket | 2 | 3 | 4 | 5 (auto-aim tụ)")
    for row in mid["charge_breakpoints"]:
        cells = []
        for r in range(1, 6):
            n = row[f"r{r}_beams"]
            d = row[f"r{r}_beam_dmg"]
            cells.append(f"{n}×/{d:.0f}" if n else "—")
        lines.append(
            f"     {row['start_charge']:>3}%   | " + " | ".join(f"{c:>8}" for c in cells)
        )
    lines.append("")
    lines.append("  Ý: trụ 0% charge thì CHỈ 5/5 mới bắn laser. Đây là lời lớn nhất của auto-aim tụ tướng.")
    lines.append("  Trụ đã ~40–60% thì 2–3 quả cũng đủ laser — lúc đó auto-aim 5/5 vẫn lời thêm 0.4–0.6× W.")
    lines.append("")

    lines.append("-" * 78)
    lines.append("KẾT LUẬN NGẮN")
    lines.append("-" * 78)
    lines.append("  1) Auto-aim lấy tướng làm điểm tụ = đúng skill expression của W poke.")
    lines.append("  2) Có lời: +80% damage W (1.8× không phải 5×) + instant 100% laser mọi trụ gần.")
    lines.append("  3) Lời thật nằm ở LASER, không phải 4 quả 20%. Đừng bỏ converge khi trade 1v1.")
    lines.append("  4) Combo E→W tụ 5/5 = 2 volley laser (E nạp 100%, W nạp lại 100%). W 1 quả thì mất laser #2.")
    lines.append("  5) Không lock auto-aim 100% thời gian: clear wave phải xòe, sau lính thì cấm bắn.")
    lines.append("  6) R+W không tụ = bỏ ~3–4× burst. Stun rồi mới W.")
    lines.append("=" * 78)
    return "\n".join(lines) + "\n"


def main() -> None:
    data = run()
    text = report(data)
    with open("results.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    with open("report.txt", "w", encoding="utf-8") as f:
        f.write(text)
    print(text)


if __name__ == "__main__":
    main()
