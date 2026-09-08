#!/usr/bin/env python3
"""
40-minute over-time: proposed Malig core vs BF → Boots of Mana → Liandry
→ Malignance → Infinity Orb → Deathcap.

Boots of Mana and Infinity Orb are Wild Rift names (user path). Combat
model is the same AP Kog fog/W sim. BF+Malig is two Lost Chapter items
(legal on WR; unique-blocked on PC).
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple
import json

from simulate_ap_kogmaw import (
    LEGENDARIES,
    compute_snapshot,
    gold_at_minute,
    level_at_minute,
    squishy_hp,
    squishy_mr,
    tank_hp,
    tank_mr,
)

GAME_MINUTES = 40

PROPOSED = [
    "Lost Chapter",
    "Blasting Wand",
    "Malignance",
    "Boots",
    "Sorcerer's Shoes",
    "Fated Ashes",
    "Haunting Guise",
    "Liandry's Torment",
    "Blighting Jewel",
    "Void Staff",
    "Needlessly Large Rod",
    "Rabadon's Deathcap",
    "Fiendish Codex",
    "Horizon Focus",
]

USER_BF = [
    "Fated Ashes",
    "Lost Chapter",
    "Blackfire Torch",
    "Boots",
    "Boots of Mana",
    "Haunting Guise",
    "Liandry's Torment",
    "Lost Chapter",
    "Blasting Wand",
    "Malignance",
    "Hextech Alternator",
    "Needlessly Large Rod",
    "Infinity Orb",
    "Needlessly Large Rod",
    "Rabadon's Deathcap",
]

PATHS = {
    "Core đề xuất (Malig→Liandry→Void→Cap)": PROPOSED,
    "BF→BoM→Liandry→Malig→Orb→Cap": USER_BF,
}


def first_item(snaps, pred) -> Optional[int]:
    for s in snaps:
        if pred(s):
            return s.minute
    return None


def compare() -> Tuple[str, dict]:
    assert gold_at_minute(28) == 500 + 5 * 310 + 5 * 420 + 6 * 500 + 6 * 540 + 6 * 580
    results = {
        name: [compute_snapshot(name, path, m) for m in range(1, GAME_MINUTES + 1)]
        for name, path in PATHS.items()
    }
    core_name = "Core đề xuất (Malig→Liandry→Void→Cap)"
    bf_name = "BF→BoM→Liandry→Malig→Orb→Cap"
    core = results[core_name]
    bf = results[bf_name]

    def has(name: str):
        return lambda s: name in s.items

    spikes = {
        core_name: {
            "Malignance": first_item(core, has("Malignance")),
            "Sorcerer's Shoes": first_item(core, has("Sorcerer's Shoes")),
            "Liandry's Torment": first_item(core, has("Liandry's Torment")),
            "Void Staff": first_item(core, has("Void Staff")),
            "Rabadon's Deathcap": first_item(core, has("Rabadon's Deathcap")),
            "Horizon Focus": first_item(core, has("Horizon Focus")),
        },
        bf_name: {
            "Blackfire Torch": first_item(bf, has("Blackfire Torch")),
            "Boots of Mana": first_item(bf, has("Boots of Mana")),
            "Liandry's Torment": first_item(bf, has("Liandry's Torment")),
            "Malignance": first_item(bf, has("Malignance")),
            "Infinity Orb": first_item(bf, has("Infinity Orb")),
            "Rabadon's Deathcap": first_item(bf, has("Rabadon's Deathcap")),
        },
    }

    lines: List[str] = []
    lines.append("=" * 88)
    lines.append("40:00 OVER TIME — CORE ĐỀ XUẤT vs BF → BOOTS OF MANA → LIANDRY → MALIG → ORB → CAP")
    lines.append("Mix 70% fog R / 30% W siege | farmer gold | núp bắn")
    lines.append("=" * 88)
    lines.append("")
    lines.append("ITEM MAP")
    lines.append("  Core đề xuất (PC, 6 slot): Malignance → Sorcs → Liandry → Void")
    lines.append("    → Deathcap → Horizon Focus")
    lines.append("  Path bạn: Blackfire → Boots of Mana → Liandry → Malignance")
    lines.append("    → Infinity Orb → Deathcap")
    lines.append("  Boots of Mana (WR): 1200g, 25 AP, 8 flat pen, mana regen.")
    lines.append("  Infinity Orb (WR): 3100g, 110 AP, 15 flat pen, +20% dmg khi")
    lines.append("    đích <35% HP (fog tank đầy máu = 0 execute).")
    lines.append("  BF+Malig = 2 Lost Chapter. WR cho phép; PC Manaflow unique")
    lines.append("    thì không — sim vẫn cho mua để so đúng thứ tự bạn hỏi.")
    lines.append("")
    lines.append("SPIKE ONLINE")
    for name in PATHS:
        lines.append(f"  {name}")
        for item, m in spikes[name].items():
            tag = f"~{m}:00" if m else "CHƯA XONG @40"
            lines.append(f"    {item:<22} {tag}")
    lines.append("")

    marks = [8, 12, 16, 20, 22, 24, 28, 32, 36, 40]
    lines.append("-" * 88)
    lines.append("GOLD / LEVEL / TANK")
    lines.append("-" * 88)
    lines.append(
        f"  {'m':>3}  {'gold':>6}  {'lv':>3}  {'tankHP':>7}  {'tankMR':>6}  {'sqHP':>6}  {'sqMR':>5}"
    )
    for m in marks:
        lines.append(
            f"  {m:>3}  {gold_at_minute(m):>6}  {level_at_minute(m):>3}  "
            f"{tank_hp(m):>7.0f}  {tank_mr(m):>6.0f}  "
            f"{squishy_hp(m):>6.0f}  {squishy_mr(m):>5.0f}"
        )
    lines.append("")

    lines.append("-" * 88)
    lines.append("DAMAGE / 8s WINDOW THEO PHÚT   Δ = core − BF path  (dương = core thắng)")
    lines.append("-" * 88)
    hdr = (
        f"  {'m':>3}  {'core mixT':>10}  {'BF mixT':>9}  {'ΔmixT':>7}  "
        f"{'core fogT':>10}  {'BF fogT':>8}  {'ΔfogT':>7}  "
        f"{'core sq':>8}  {'BF sq':>7}  {'Δsq':>7}"
    )
    lines.append(hdr)
    table_rows = []
    for m in range(1, GAME_MINUTES + 1):
        c, b = core[m - 1], bf[m - 1]
        row = {
            "minute": m,
            "core_items": c.items,
            "bf_items": b.items,
            "core_mix_tank": c.mix_tank,
            "bf_mix_tank": b.mix_tank,
            "core_fog_tank": c.fog_tank,
            "bf_fog_tank": b.fog_tank,
            "core_siege_tank": c.siege_tank,
            "bf_siege_tank": b.siege_tank,
            "core_mix_squish": c.mix_squish,
            "bf_mix_squish": b.mix_squish,
            "core_ap": c.ap,
            "bf_ap": b.ap,
            "core_notes": c.notes,
            "bf_notes": b.notes,
        }
        table_rows.append(row)
        if m in marks or m % 2 == 0:
            lines.append(
                f"  {m:>3}  {c.mix_tank:>10.0f}  {b.mix_tank:>9.0f}  "
                f"{c.mix_tank - b.mix_tank:>+7.0f}  "
                f"{c.fog_tank:>10.0f}  {b.fog_tank:>8.0f}  "
                f"{c.fog_tank - b.fog_tank:>+7.0f}  "
                f"{c.mix_squish:>8.0f}  {b.mix_squish:>7.0f}  "
                f"{c.mix_squish - b.mix_squish:>+7.0f}"
            )
    lines.append("")
    lines.append("  Items @ spike phút:")
    for m in marks:
        c, b = core[m - 1], bf[m - 1]
        lines.append(f"    {m:>2}:00 CORE  {c.ap:.0f} AP  { ' › '.join(c.items)}")
        lines.append(f"         BF    {b.ap:.0f} AP  { ' › '.join(b.items)}")
    lines.append("")

    # Who is ahead how often
    ahead_tank = sum(1 for m in range(GAME_MINUTES) if core[m].mix_tank >= bf[m].mix_tank)
    ahead_sq = sum(1 for m in range(GAME_MINUTES) if core[m].mix_squish >= bf[m].mix_squish)
    # Integrated "damage over game" — sum of mix windows as a rough area
    area_core_t = sum(s.mix_tank for s in core)
    area_bf_t = sum(s.mix_tank for s in bf)
    area_core_s = sum(s.mix_squish for s in core)
    area_bf_s = sum(s.mix_squish for s in bf)

    lines.append("-" * 88)
    lines.append("PHASE")
    lines.append("-" * 88)
    phases = [
        ("Lane / first item  1–10", 1, 10),
        ("Mid spike          11–20", 11, 20),
        ("3–4 món            21–28", 21, 28),
        ("Siêu trễ           29–40", 29, 40),
    ]
    for label, a, bmin in phases:
        cavg = sum(core[m - 1].mix_tank for m in range(a, bmin + 1)) / (bmin - a + 1)
        bavg = sum(bf[m - 1].mix_tank for m in range(a, bmin + 1)) / (bmin - a + 1)
        csq = sum(core[m - 1].mix_squish for m in range(a, bmin + 1)) / (bmin - a + 1)
        bsq = sum(bf[m - 1].mix_squish for m in range(a, bmin + 1)) / (bmin - a + 1)
        dt = 100.0 * (cavg / bavg - 1.0) if bavg else 0.0
        ds = 100.0 * (csq / bsq - 1.0) if bsq else 0.0
        lines.append(
            f"  {label}  mix-tank core {cavg:.0f} vs BF {bavg:.0f} ({dt:+.1f}%)  |  "
            f"squish {csq:.0f} vs {bsq:.0f} ({ds:+.1f}%)"
        )
    lines.append("")
    lines.append(
        f"  Phút core ≥ BF vs tank: {ahead_tank}/{GAME_MINUTES}  | vs squishy: {ahead_sq}/{GAME_MINUTES}"
    )
    lines.append(
        f"  Diện tích mix-tank (tổng 40 cửa sổ): core {area_core_t:.0f} vs BF {area_bf_t:.0f}  "
        f"({100*(area_core_t/area_bf_t-1):+.1f}%)"
    )
    lines.append(
        f"  Diện tích mix-squishy: core {area_core_s:.0f} vs BF {area_bf_s:.0f}  "
        f"({100*(area_core_s/area_bf_s-1):+.1f}%)"
    )
    lines.append("")

    c28, b28 = core[27], bf[27]
    c40, b40 = core[39], bf[39]
    lines.append("-" * 88)
    lines.append("VERDICT 40:00")
    lines.append("-" * 88)
    lines.append(
        f"  @28:00 mix tank  core {c28.mix_tank:.0f} vs BF {b28.mix_tank:.0f}  "
        f"({100*(c28.mix_tank/b28.mix_tank-1):+.1f}%)"
    )
    lines.append(
        f"  @40:00 mix tank  core {c40.mix_tank:.0f} vs BF {b40.mix_tank:.0f}  "
        f"({100*(c40.mix_tank/b40.mix_tank-1):+.1f}%)"
    )
    lines.append(
        f"  @40:00 mix squish core {c40.mix_squish:.0f} vs BF {b40.mix_squish:.0f}  "
        f"({100*(c40.mix_squish/b40.mix_squish-1):+.1f}%)"
    )
    lines.append("")
    lines.append("  Core đề xuất thắng phần lớn game vì Malig sớm (~7) + Void")
    lines.append("  vs tank MR. Path BF mua Malig muộn (Lost Chapter thứ 2) nên")
    lines.append("  mất Hatefog cả mid-game; Infinity Orb là anti-squishy")
    lines.append("  execute, fog tank không proc <35% HP; không có Void.")
    lines.append("  Nếu game kéo 40 phút và BF path kịp Cap, khoảng cách hẹp")
    lines.append("  lại trên squishy (Orb+Cap AP), tank vẫn thua vì thiếu %pen.")
    lines.append("=" * 88)

    payload = {
        "game_minutes": GAME_MINUTES,
        "paths": {n: PATHS[n] for n in PATHS},
        "spikes": spikes,
        "gold_28": gold_at_minute(28),
        "gold_40": gold_at_minute(40),
        "ahead_minutes_tank": ahead_tank,
        "ahead_minutes_squish": ahead_sq,
        "area_mix_tank": {
            core_name: round(area_core_t, 1),
            bf_name: round(area_bf_t, 1),
        },
        "minutes": table_rows,
    }
    return "\n".join(lines), payload


def main() -> None:
    text, payload = compare()
    print(text)
    with open("/workspace/ap-kogmaw-sim/overtime_40.txt", "w", encoding="utf-8") as f:
        f.write(text + "\n")
    with open("/workspace/ap-kogmaw-sim/overtime_40.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print("\nWrote ap-kogmaw-sim/overtime_40.txt and overtime_40.json")


if __name__ == "__main__":
    main()
