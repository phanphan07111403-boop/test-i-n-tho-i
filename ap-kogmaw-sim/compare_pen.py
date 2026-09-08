#!/usr/bin/env python3
"""
AP Kog'Maw — magic-pen stacking vs burn+Void core.

Patch ~26.x: Void Staff and Cryptbloom are limited to 1 Void Pen item
(cannot stack 40%+30%). Flat pen (Sorcs, Shadowflame) applies after %pen.
Q shreds 16–32% MR before all of that; Hatefog then −10 MR.
"""

from __future__ import annotations

from typing import Dict, List, Tuple
import json

from compare_seraph import (
    Kit,
    kit_stats,
    pct,
    r_count,
    window_parts,
)
from simulate_ap_kogmaw import (
    apply_pen,
    magic_mult,
    q_shred_pct,
    squishy_hp,
    squishy_mr,
    tank_hp,
    tank_mr,
)


FULL_BUILDS: Dict[str, Kit] = {
    "Burn+Void (baseline)": Kit(
        "Burn+Void (baseline)",
        [
            "Malignance",
            "Sorcerer's Shoes",
            "Liandry's Torment",
            "Void Staff",
            "Rabadon's Deathcap",
            "Horizon Focus",
        ],
        "Malig + Liandry + Void + Cap + Horizon — core núp + tank",
    ),
    "SF thay Liandry": Kit(
        "SF thay Liandry",
        [
            "Malignance",
            "Sorcerer's Shoes",
            "Void Staff",
            "Shadowflame",
            "Rabadon's Deathcap",
            "Horizon Focus",
        ],
        "Magic-pen mage: Void 40% + SF 15 flat, bỏ 2% max HP burn.",
    ),
    "SF thay Horizon": Kit(
        "SF thay Horizon",
        [
            "Malignance",
            "Sorcerer's Shoes",
            "Liandry's Torment",
            "Void Staff",
            "Rabadon's Deathcap",
            "Shadowflame",
        ],
        "Giữ burn+Void+Cap; SF 15 flat + Cinderbloom thay Hypershot 10%.",
    ),
    "SF thay Void": Kit(
        "SF thay Void",
        [
            "Malignance",
            "Sorcerer's Shoes",
            "Liandry's Torment",
            "Shadowflame",
            "Rabadon's Deathcap",
            "Horizon Focus",
        ],
        "Chỉ flat pen. Q shred + Sorcs + SF, không %pen.",
    ),
    "Crypt thay Void": Kit(
        "Crypt thay Void",
        [
            "Malignance",
            "Sorcerer's Shoes",
            "Liandry's Torment",
            "Cryptbloom",
            "Rabadon's Deathcap",
            "Horizon Focus",
        ],
        "30% pen + 20 AH + Life from Death. Void Pen unique: không đeo cùng Void.",
    ),
    "SF thay Deathcap": Kit(
        "SF thay Deathcap",
        [
            "Malignance",
            "Sorcerer's Shoes",
            "Liandry's Torment",
            "Void Staff",
            "Horizon Focus",
            "Shadowflame",
        ],
        "Giữ fog kit + Void; mất 30% AP amp.",
    ),
}


def mr_pipeline(mr: float, st: dict, level: int, cursed: bool) -> List[Tuple[str, float]]:
    """Step-through effective MR after each pen layer."""
    shred = q_shred_pct(level)
    malig = 10.0 if (cursed and st["malig"]) else 0.0
    steps = [("raw", mr)]
    after_q = mr * (1.0 - shred)
    steps.append((f"Q shred {100*shred:.0f}%", after_q))
    after_hf = max(0.0, after_q - malig)
    if malig:
        steps.append(("Hatefog −10", after_hf))
    after_pct = after_hf * (1.0 - st["pct"])
    if st["pct"]:
        label = "Void 40%" if st["void"] else f"%pen {100*st['pct']:.0f}%"
        steps.append((label, after_pct))
    after_flat = max(0.0, after_pct - st["flat"])
    if st["flat"]:
        steps.append((f"flat −{st['flat']:.0f}", after_flat))
    return steps


def eff_mr(mr: float, st: dict, level: int, cursed: bool = True) -> float:
    shred = q_shred_pct(level)
    malig = 10.0 if (cursed and st["malig"]) else 0.0
    return apply_pen(mr, shred, malig, st["pct"], st["flat"])


def compare(level: int = 18, minute: int = 28) -> Tuple[str, dict]:
    thp, tmr = tank_hp(minute), tank_mr(minute)
    shp, smr = squishy_hp(minute), squishy_mr(minute)
    kits = {k: kit_stats(v, level) for k, v in FULL_BUILDS.items()}
    damage_names = list(FULL_BUILDS.keys())
    base_name = "Burn+Void (baseline)"

    shred = q_shred_pct(level)
    assert 0.30 < shred <= 0.32
    # Void + Cryptbloom cannot both apply; kits never include both.
    for name, kit in FULL_BUILDS.items():
        n_void_pen = sum(
            1 for it in kit.items if it in ("Void Staff", "Cryptbloom")
        )
        assert n_void_pen <= 1, name

    scenarios = [
        ("Fog 8s vs TANK (núp R, không W)", 8.0, False, True, thp, tmr),
        ("Fog 8s vs SQUISHY", 8.0, False, False, shp, smr),
        ("W siege 8s vs TANK (brush autos)", 8.0, True, True, thp, tmr),
        ("W siege 8s vs SQUISHY", 8.0, True, False, shp, smr),
        ("Fog 20s vs TANK (siege R kéo dài)", 20.0, False, True, thp, tmr),
        ("Fog 20s vs SQUISHY", 20.0, False, False, shp, smr),
    ]

    results: dict = {}
    for label, window, use_w, vs_tank, hp, mr in scenarios:
        results[label] = {}
        for name in damage_names:
            st = kits[name]
            dmg, parts, mult = window_parts(
                level=level,
                st=st,
                hp=hp,
                mr=mr,
                window=window,
                use_w=use_w,
                vs_tank=vs_tank,
            )
            results[label][name] = {
                "dmg": dmg,
                "parts": parts,
                "mult": mult,
                "shots": parts.shots,
                "cd_cap": parts.cd_cap,
                "mana_capped": parts.mana_capped,
            }

    lines: List[str] = []
    lines.append("=" * 82)
    lines.append("AP KOG'MAW — MAGIC PEN (Void / Shadowflame / Cryptbloom)")
    lines.append(f"Full build (5 legendary + Sorcs) | level {level} | target @ {minute}:00")
    lines.append(f"Tank {thp:.0f} HP / {tmr:.0f} MR   |  Squishy {shp:.0f} HP / {smr:.0f} MR")
    lines.append("=" * 82)
    lines.append("")
    lines.append("LUẬT PEN (Kog đã xuyên sẵn)")
    lines.append("  • Thứ tự: Q shred % MR → Hatefog −10 MR → %pen item → flat pen.")
    lines.append("  • Q max = 32% shred ARMOR và MR — Kog không phải mage 0% pen.")
    lines.append("  • Void Staff 40% và Cryptbloom 30% = 1 Void Pen item.")
    lines.append("    Không mua cả hai. %pen không cộng 40+30.")
    lines.append("  • Shadowflame = 15 flat + Cinderbloom (crit khi đích <40% HP).")
    lines.append("    Fog poke tank đầy máu: Cinderbloom = 0. Chỉ còn 15 flat.")
    lines.append("  • Sorcs 12 flat sau %pen. Vs squishy, Q+Void+Hatefog+Sorcs")
    lines.append("    đã gần về 0 MR — thêm SF 15 flat gần như phí.")
    lines.append("  • Liandry 2% max HP/s không cần pen để 'tồn tại'; chỉ bị MR")
    lines.append("    giảm khi tick. Bỏ Liandry = mất cột tank lớn nhất.")
    lines.append("")

    lines.append("-" * 82)
    lines.append("MR HIỆU DỤNG SAU FULL PEN  (có Q + Hatefog curse)")
    lines.append("-" * 82)
    lines.append(
        f"  {'Build':<24} {'AP':>5} {'%pen':>5} {'flat':>5} "
        f"{'tankMR':>7} {'take%':>6} {'sqMR':>6} {'sqTake':>7}"
    )
    for name in damage_names:
        st = kits[name]
        t_eff = eff_mr(tmr, st, level, True)
        s_eff = eff_mr(smr, st, level, True)
        lines.append(
            f"  {name:<24} {st['ap']:>5.0f} {100*st['pct']:>4.0f}% {st['flat']:>5.0f} "
            f"{t_eff:>7.0f} {100*magic_mult(t_eff):>5.0f}% "
            f"{s_eff:>6.0f} {100*magic_mult(s_eff):>6.0f}%"
        )
    lines.append("")
    lines.append("  Pipeline tank, Burn+Void (baseline):")
    for label, val in mr_pipeline(tmr, kits[base_name], level, True):
        lines.append(
            f"    {label:<22} MR {val:6.1f}  → eat {100*magic_mult(val):.0f}%"
        )
    lines.append("  Pipeline tank, SF thay Liandry (thêm 15 flat, cùng 40%):")
    for label, val in mr_pipeline(tmr, kits["SF thay Liandry"], level, True):
        lines.append(
            f"    {label:<22} MR {val:6.1f}  → eat {100*magic_mult(val):.0f}%"
        )
    lines.append("  Pipeline squishy, baseline (Q+Void+Sorcs đã gần cap):")
    for label, val in mr_pipeline(smr, kits[base_name], level, True):
        lines.append(
            f"    {label:<22} MR {val:6.1f}  → eat {100*magic_mult(val):.0f}%"
        )
    lines.append("")

    lines.append("-" * 82)
    lines.append("DAMAGE THEO CỬA SỔ  (Δ vs Burn+Void)")
    lines.append("-" * 82)
    for label, *_ in scenarios:
        lines.append(f"  [{label}]")
        base_d = results[label][base_name]["dmg"]
        for name in damage_names:
            row = results[label][name]
            if row["mana_capped"]:
                tag = f"  mana-cap {row['shots']}/{row['cd_cap']} R"
            else:
                tag = f"  CD-cap {row['shots']} R"
            delta = pct(row["dmg"], base_d) if name != base_name else "baseline"
            lines.append(
                f"    {name:<24} {row['dmg']:>8.0f}  {delta:>8}{tag}"
            )
        lines.append("")

    focus = [
        "Burn+Void (baseline)",
        "SF thay Liandry",
        "SF thay Horizon",
        "SF thay Void",
    ]
    lines.append("-" * 82)
    lines.append("BREAKDOWN  (sau MR, trước Horizon/Cut Down/Madness)")
    lines.append("-" * 82)
    for label in (
        "Fog 8s vs TANK (núp R, không W)",
        "W siege 8s vs TANK (brush autos)",
        "Fog 8s vs SQUISHY",
    ):
        lines.append(f"  [{label}]")
        for name in focus:
            row = results[label][name]
            p = row["parts"]
            st = kits[name]
            lines.append(
                f"    {name}  AP {st['ap']:.0f}  MR→{eff_mr(tmr if 'TANK' in label else smr, st, level):.0f}  "
                f"mult x{row['mult']:.3f}  final {row['dmg']:.0f}"
            )
            lines.append(
                f"      Q {p.q:7.0f} | R {p.r:7.0f} ({p.shots} shot) | "
                f"W {p.w:7.0f} | Liandry {p.liandry:7.0f} | "
                f"Hatefog {p.hatefog:7.0f} | Comet {p.comet:6.0f}"
            )
        lines.append("")

    fog8_t = results["Fog 8s vs TANK (núp R, không W)"]
    fog8_s = results["Fog 8s vs SQUISHY"]
    w8_t = results["W siege 8s vs TANK (brush autos)"]
    w8_s = results["W siege 8s vs SQUISHY"]
    fog20_t = results["Fog 20s vs TANK (siege R kéo dài)"]
    sf_li = "SF thay Liandry"
    sf_hz = "SF thay Horizon"
    sf_void = "SF thay Void"
    crypt = "Crypt thay Void"
    sf_cap = "SF thay Deathcap"

    def mix70(fog, w) -> float:
        return 0.70 * fog["dmg"] + 0.30 * w["dmg"]

    mix_base = mix70(fog8_t[base_name], w8_t[base_name])
    mix_sfli = mix70(fog8_t[sf_li], w8_t[sf_li])
    mix_sfhz = mix70(fog8_t[sf_hz], w8_t[sf_hz])
    mix_sfv = mix70(fog8_t[sf_void], w8_t[sf_void])

    t_base = eff_mr(tmr, kits[base_name], level)
    t_sf = eff_mr(tmr, kits[sf_li], level)
    s_base = eff_mr(smr, kits[base_name], level)
    s_sf = eff_mr(smr, kits[sf_li], level)

    lines.append("-" * 82)
    lines.append("MẠNH CHỖ NÀO / YẾU CHỖ NÀO")
    lines.append("-" * 82)
    lines.append("  1) SHADOWFLAME THAY LIANDRY  (kit 'magic pen mage')")
    lines.append(
        f"     Fog 8s tank:   {pct(fog8_t[sf_li]['dmg'], fog8_t[base_name]['dmg'])}  "
        f"({fog8_t[sf_li]['dmg']:.0f} vs {fog8_t[base_name]['dmg']:.0f})"
    )
    lines.append(
        f"     Fog 8s squish: {pct(fog8_s[sf_li]['dmg'], fog8_s[base_name]['dmg'])}"
    )
    lines.append(
        f"     W 8s tank:     {pct(w8_t[sf_li]['dmg'], w8_t[base_name]['dmg'])}"
    )
    lines.append(
        f"     W 8s squish:   {pct(w8_s[sf_li]['dmg'], w8_s[base_name]['dmg'])}"
    )
    lines.append(
        f"     Fog 20s tank:  {pct(fog20_t[sf_li]['dmg'], fog20_t[base_name]['dmg'])}"
    )
    lines.append(
        f"     Mix 70/30 tank:{pct(mix_sfli, mix_base)}  "
        f"({mix_sfli:.0f} vs {mix_base:.0f})"
    )
    lines.append(
        f"     Tank MR {t_base:.0f}→{t_sf:.0f} (eat {100*magic_mult(t_base):.0f}%→"
        f"{100*magic_mult(t_sf):.0f}%). Squishy {s_base:.0f}→{s_sf:.0f} "
        f"(đã gần 0)."
    )
    lines.append("     8s gần hòa vs tank vì SF 110 AP + 15 flat bù Liandry")
    lines.append("     tick. Fog 20s −12%: burn 2% HP là cột núp kéo dài.")
    lines.append("     MẠNH vs squishy (+22%): Cinderbloom <40% HP + AP cao hơn.")
    lines.append("     Đó là kit giết ADC, không phải kit đau tank / siege R.")
    lines.append("")
    lines.append("  2) SHADOWFLAME THAY HORIZON  (thêm pen, giữ Liandry+Void+Cap)")
    lines.append(
        f"     Fog 8s tank:   {pct(fog8_t[sf_hz]['dmg'], fog8_t[base_name]['dmg'])}"
    )
    lines.append(
        f"     Fog 8s squish: {pct(fog8_s[sf_hz]['dmg'], fog8_s[base_name]['dmg'])}"
    )
    lines.append(
        f"     W 8s tank:     {pct(w8_t[sf_hz]['dmg'], w8_t[base_name]['dmg'])}"
    )
    lines.append(
        f"     Mix 70/30 tank:{pct(mix_sfhz, mix_base)}"
    )
    lines.append("     Flex món 5 khi địch squishy/shield: +21% fog ADC, tank 8s")
    lines.append("     vẫn +3% (110 AP + 15 flat > Horizon 75 AP + 10%).")
    lines.append("     Núp tank thuần / Hypershot R max range thì Horizon ổn hơn")
    lines.append("     về cảm giác mark; DPS 8s SF thắng trên giấy.")
    lines.append("")
    lines.append("  3) SHADOWFLAME THAY VOID  (bỏ %pen)")
    lines.append(
        f"     Fog 8s tank:   {pct(fog8_t[sf_void]['dmg'], fog8_t[base_name]['dmg'])}"
    )
    lines.append(
        f"     W 8s tank:     {pct(w8_t[sf_void]['dmg'], w8_t[base_name]['dmg'])}"
    )
    lines.append(
        f"     Mix 70/30 tank:{pct(mix_sfv, mix_base)}"
    )
    lines.append("     YẾU NẶNG vs tank: 15 flat + Q 32% không thay 40% Void.")
    lines.append("     Đây là trap món 3 cũ (Luden→Malig→SF).")
    lines.append("")
    lines.append("  4) CRYPTBLOOM THAY VOID")
    lines.append(
        f"     Fog 8s tank:   {pct(fog8_t[crypt]['dmg'], fog8_t[base_name]['dmg'])}"
    )
    lines.append(
        f"     W 8s tank:     {pct(w8_t[crypt]['dmg'], w8_t[base_name]['dmg'])}"
    )
    lines.append("     30% vs 40% + ít AP hơn. Đổi DPS lấy 20 AH + heal nova.")
    lines.append("     Chỉ khi team cần Life from Death / thiếu haste, không phải")
    lines.append("     default đau tank.")
    lines.append("")
    lines.append("  5) SHADOWFLAME THAY DEATHCAP")
    lines.append(
        f"     Fog 8s tank:   {pct(fog8_t[sf_cap]['dmg'], fog8_t[base_name]['dmg'])}"
    )
    lines.append(
        f"     W 8s tank:     {pct(w8_t[sf_cap]['dmg'], w8_t[base_name]['dmg'])}"
    )
    lines.append("     Mất 30% AP trên W %HP + R + Hatefog. Pen không bù amp.")
    lines.append("")
    lines.append("  GOLD CURVE (đã có ở sim chính): món 3 Void sau Liandry")
    lines.append("     isolated Δ vs tank gấp đôi Shadowflame. Pen stack sớm")
    lines.append("     (Malig→Void) thắng phút 12–16 fog, rồi Liandry bắt kịp.")
    lines.append("")

    lines.append("-" * 82)
    lines.append("VERDICT MAGIC PEN")
    lines.append("-" * 82)
    lines.append(
        f"  Kit 'full magic pen' (Void+SF, bỏ Liandry) mix 70/30 tank: "
        f"{pct(mix_sfli, mix_base)}"
    )
    lines.append(
        f"  Fog tank {pct(fog8_t[sf_li]['dmg'], fog8_t[base_name]['dmg'])}  |  "
        f"W tank {pct(w8_t[sf_li]['dmg'], w8_t[base_name]['dmg'])}  |  "
        f"fog squish {pct(fog8_s[sf_li]['dmg'], fog8_s[base_name]['dmg'])}"
    )
    lines.append("  Kog núp bắn ĐÃ LÀ magic-pen champion: Q 32% + Void 40% +")
    lines.append("  Hatefog −10 + Sorcs 12. Thêm Shadowflame không phải build")
    lines.append("  mới vs tank — 15 flat sau %pen chỉ 73→58 MR (eat 58%→63%).")
    lines.append("  Vs squishy, Q+Void+Sorcs đã gần 0 MR; giá trị SF là")
    lines.append("  Cinderbloom khi chúng <40% HP (+22% fog ADC), không phải")
    lines.append("  thêm 'xuyên phép'.")
    lines.append("")
    lines.append("  Void+SF bỏ Liandry: mix 8s tank +1.6% (AP SF bù tick),")
    lines.append("  nhưng fog 20s −12% — siege R cần burn. Squishy thì +22%.")
    lines.append("")
    lines.append("  Làm:")
    lines.append("    • Magic pen của Kog = Void (hoặc Crypt nếu cần heal/AH)")
    lines.append("      + Sorcs + Q shred. Đó là cả kit pen.")
    lines.append("    • Giữ Liandry nếu núp tank / R kéo dài.")
    lines.append("    • SF = flex món 5 thay Horizon khi team địch squishy")
    lines.append("      (+21% ADC, tank 8s vẫn +3%). Không thay Void / Cap.")
    lines.append("  Không làm:")
    lines.append("    • Luden + Malig + SF (trap món 3, −18% tank nếu bỏ Void).")
    lines.append("    • Void + Cryptbloom (unique, không chồng).")
    lines.append("    • Bỏ Liandry chỉ để 'stack pen' nếu bạn siege tank 15s+.")
    lines.append("  Default đau tank: Malig → Liandry → Void → Cap → Horizon.")
    lines.append("  Default giết ADC: cùng core, SF món 5 thay Horizon.")
    lines.append("=" * 82)

    payload = {
        "level": level,
        "minute": minute,
        "tank": {"hp": thp, "mr": tmr},
        "squishy": {"hp": shp, "mr": smr},
        "void_crypt_unique": True,
        "kits": {
            n: {
                "items": FULL_BUILDS[n].items,
                "ap": round(st["ap"], 1),
                "pct_mpen": st["pct"],
                "flat_mpen": st["flat"],
                "eff_mr_tank": round(eff_mr(tmr, st, level), 1),
                "eff_mr_squishy": round(eff_mr(smr, st, level), 1),
                "note": FULL_BUILDS[n].note,
            }
            for n, st in kits.items()
            if n in damage_names
        },
        "scenarios": {
            label: {
                name: {
                    "damage": round(row["dmg"], 1),
                    "shots": row["shots"],
                    "mana_capped": row["mana_capped"],
                    "mult": round(row["mult"], 4),
                    "parts": row["parts"].as_dict(),
                }
                for name, row in results[label].items()
            }
            for label, *_ in scenarios
        },
        "mix_70_30_tank": {
            "Burn+Void (baseline)": round(mix_base, 1),
            "SF thay Liandry": round(mix_sfli, 1),
            "SF thay Horizon": round(mix_sfhz, 1),
            "SF thay Void": round(mix_sfv, 1),
        },
    }
    return "\n".join(lines), payload


def main() -> None:
    text, payload = compare()
    print(text)
    with open("/workspace/ap-kogmaw-sim/pen_compare.txt", "w", encoding="utf-8") as f:
        f.write(text + "\n")
    with open("/workspace/ap-kogmaw-sim/pen_compare.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print("\nWrote ap-kogmaw-sim/pen_compare.txt and pen_compare.json")


if __name__ == "__main__":
    main()
