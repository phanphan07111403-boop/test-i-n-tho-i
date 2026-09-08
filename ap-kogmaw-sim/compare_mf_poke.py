#!/usr/bin/env python3
"""
Kog'Maw vs Miss Fortune poke package: Luden + Blackfire + Liandry + Muramana.

MF Double Up is physical, infrequent, and loves one Echo proc + Muramana Shock
per Q. Kog Living Artillery is magic and dumps many shots per window — Echo
is 1/12s, Shock is physical, and Luden+BF share Manaflow on PC.
"""

from __future__ import annotations

from typing import Dict, List, Tuple
import json

from compare_mix import Kit, pct, window_parts as mix_window
from compare_mix import kit_stats as mix_kit_stats
from simulate_ap_kogmaw import (
    ITEMS,
    apply_pen,
    magic_mult,
    q_shred_pct,
    squishy_armor,
    squishy_hp,
    squishy_mr,
    tank_armor,
    tank_hp,
    tank_mr,
)


FULL_BUILDS: Dict[str, Kit] = {
    "Core Kog": Kit(
        "Core Kog",
        [
            "Malignance",
            "Sorcerer's Shoes",
            "Liandry's Torment",
            "Void Staff",
            "Rabadon's Deathcap",
            "Horizon Focus",
        ],
        "Malig + Liandry + Void + Cap + Horizon",
    ),
    "MF 4-pack + Cap": Kit(
        "MF 4-pack + Cap",
        [
            "Luden's Echo",
            "Blackfire Torch",
            "Liandry's Torment",
            "Muramana",
            "Rabadon's Deathcap",
            "Sorcerer's Shoes",
        ],
        "Luden+BF+Liandry+Mura+Cap — poke MF. 2× Lost Chapter, không Void/Malig.",
    ),
    "MF 4-pack + Void": Kit(
        "MF 4-pack + Void",
        [
            "Luden's Echo",
            "Blackfire Torch",
            "Liandry's Torment",
            "Muramana",
            "Void Staff",
            "Sorcerer's Shoes",
        ],
        "Giữ 4-pack, Void thay Cap.",
    ),
    "PC-legal Luden poke": Kit(
        "PC-legal Luden poke",
        [
            "Luden's Echo",
            "Liandry's Torment",
            "Muramana",
            "Void Staff",
            "Rabadon's Deathcap",
            "Sorcerer's Shoes",
        ],
        "Một Lost Chapter (Luden). Mura sau transform. Có Void+Cap.",
    ),
    "PC-legal BF poke": Kit(
        "PC-legal BF poke",
        [
            "Blackfire Torch",
            "Liandry's Torment",
            "Muramana",
            "Void Staff",
            "Rabadon's Deathcap",
            "Sorcerer's Shoes",
        ],
        "Một Lost Chapter (BF). Mura sau transform. Có Void+Cap.",
    ),
    "4-pack không Mura": Kit(
        "4-pack không Mura",
        [
            "Luden's Echo",
            "Blackfire Torch",
            "Liandry's Torment",
            "Void Staff",
            "Rabadon's Deathcap",
            "Sorcerer's Shoes",
        ],
        "Luden+BF+Liandry+Void+Cap — bỏ Shock, giữ %pen.",
    ),
}


def kit_stats(kit: Kit, level: int) -> dict:
    st = mix_kit_stats(kit, level)
    inv = [ITEMS[n] for n in kit.items]
    st["luden"] = any(it.luden for it in inv)
    st["bf"] = any(it.blackfire for it in inv)
    manaflow = sum(1 for it in inv if it.luden or it.blackfire or it.malignance or it.manamune)
    st["manaflow_count"] = manaflow
    # Deathcap and Blackfire AP amp stack additively (same as gold-curve sim).
    raw = st["ap"] / 1.30 if st["cap"] else st["ap"]
    mult = 1.0
    if st["bf"]:
        mult += 0.04 * 1.2
    if st["cap"]:
        mult += 0.30
    st["ap"] = raw * mult
    return st


def window_parts(*, level, st, hp, mr, armor, window, use_w, vs_tank):
    total, p, mult = mix_window(
        level=level,
        st=st,
        hp=hp,
        mr=mr,
        armor=armor,
        window=window,
        use_w=use_w,
        vs_tank=vs_tank,
    )
    shred = q_shred_pct(level)
    malig_shred = 10.0 if st["malig"] and p.shots >= 1 else 0.0
    mr_pre = apply_pen(mr, shred, 0.0, st["pct"], st["flat"])
    mr_post = apply_pen(mr, shred, malig_shred, st["pct"], st["flat"])
    m_pre = magic_mult(mr_pre)
    m_post = magic_mult(mr_post)
    extra = 0.0
    echo = 0.0
    bf_burn = 0.0
    if st.get("luden"):
        echo = (105.0 + 0.07 * st["ap"]) * m_pre
        extra += echo
    burn_t = max(0.0, window - 0.45)
    if st.get("bf"):
        bf_burn = (20.0 + 0.02 * st["ap"]) * burn_t * m_post
        extra += bf_burn
    p.echo = echo
    p.blackfire = bf_burn
    # mix Parts.as_dict doesn't include these; stash on object
    return (total + extra * mult), p, mult, echo, bf_burn


def compare(level: int = 18, minute: int = 28) -> Tuple[str, dict]:
    thp, tmr, tar = tank_hp(minute), tank_mr(minute), tank_armor(minute)
    shp, smr, sar = squishy_hp(minute), squishy_mr(minute), squishy_armor(minute)
    kits = {k: kit_stats(v, level) for k, v in FULL_BUILDS.items()}
    base_name = "Core Kog"
    mf = kits["MF 4-pack + Cap"]
    assert mf["luden"] and mf["bf"] and mf["muramana"] and mf["liandry"]
    assert mf["manaflow_count"] >= 2
    assert kits["PC-legal Luden poke"]["manaflow_count"] == 1
    assert kits["PC-legal BF poke"]["manaflow_count"] == 1

    scenarios = [
        ("Fog 8s vs TANK", 8.0, False, True, thp, tmr, tar),
        ("Fog 8s vs SQUISHY", 8.0, False, False, shp, smr, sar),
        ("W 8s vs TANK", 8.0, True, True, thp, tmr, tar),
        ("W 8s vs SQUISHY", 8.0, True, False, shp, smr, sar),
        ("Fog 20s vs TANK", 20.0, False, True, thp, tmr, tar),
        ("Fog 20s vs SQUISHY", 20.0, False, False, shp, smr, sar),
    ]

    results: dict = {}
    for label, window, use_w, vs_tank, hp, mr, armor in scenarios:
        results[label] = {}
        for name, st in kits.items():
            dmg, parts, mult, echo, bf_burn = window_parts(
                level=level, st=st, hp=hp, mr=mr, armor=armor,
                window=window, use_w=use_w, vs_tank=vs_tank,
            )
            results[label][name] = {
                "dmg": dmg,
                "parts": parts,
                "mult": mult,
                "echo": echo * mult,
                "bf": bf_burn * mult,
                "shots": parts.shots,
                "cd_cap": parts.cd_cap,
                "mana_capped": parts.mana_capped,
                "magic": parts.magic_pre() * mult + echo * mult + bf_burn * mult,
                "phys": parts.phys_pre() * mult,
            }

    lines: List[str] = []
    lines.append("=" * 82)
    lines.append("KOG'MAW vs POKE MISS FORTUNE  (Luden + BF + Liandry + Muramana)")
    lines.append(f"Full 5 legendary + Sorcs | level {level} | target @ {minute}:00")
    lines.append(f"Tank {thp:.0f} HP / {tmr:.0f} MR / {tar:.0f} armor  |  "
                 f"Squishy {shp:.0f} HP / {smr:.0f} MR / {sar:.0f} armor")
    lines.append("=" * 82)
    lines.append("")
    lines.append("TẠI SAO MF BUILD ĐƯỢC, KOG THÌ KHÁC")
    lines.append("  • MF Q Double Up = VẬT LÝ, 1–2 hit / lượt poke. Luden Echo")
    lines.append("    (12s) ≈ cả trade. Muramana Shock 3% mana là vật lý, chồng")
    lines.append("    đúng damage type Q. Awe AD scale thẳng Q.")
    lines.append("  • Kog R = PHÉP, dump 8–10 shot / 8s. Echo vẫn 1 proc — còn")
    lines.append("    lại 7 R không có Echo. Shock R là vật lý (~10% cửa sổ),")
    lines.append("    không xuyên giáp vì kit này không Serylda.")
    lines.append("  • Luden + Blackfire = 2 Lost Chapter / Manaflow. PC: unique,")
    lines.append("    KHÔNG đeo cùng. WR: thường cho. Sim vẫn tính 4-pack.")
    lines.append("  • Muramana (sau transform) không còn Manaflow → đeo được với")
    lines.append("    MỘT món Lost Chapter nếu transform trước.")
    lines.append("  • Liandry là món chung (2% HP) — hợp cả hai tướng.")
    lines.append("  • BF burn = (20+2% AP)/s, không phải max HP. Vs tank nhỏ.")
    lines.append("  • 4-pack không có Malig (Hatefog) và thường không có Void.")
    lines.append("")

    lines.append("-" * 82)
    lines.append("STATS")
    lines.append("-" * 82)
    lines.append(
        f"  {'Build':<22} {'AP':>5} {'bAD':>5} {'AH':>4} {'UH':>3} "
        f"{'Mana':>5} {'LC':>3} {'%pen':>5} {'flat':>5}"
    )
    for name, st in kits.items():
        lines.append(
            f"  {name:<22} {st['ap']:>5.0f} {st['bonus_ad']:>5.0f} "
            f"{st['ah']:>4.0f} {st['uh']:>3.0f} {st['max_mana']:>5.0f} "
            f"{st['manaflow_count']:>3} {100*st['pct']:>4.0f}% {st['flat']:>5.0f}"
        )
    lines.append("  LC = số item Lost Chapter / Manaflow (Luden, BF, Malig, Manamune).")
    lines.append("")

    lines.append("-" * 82)
    lines.append("DAMAGE  (Δ vs Core Kog)  | Echo và BF burn đã cộng")
    lines.append("-" * 82)
    for label, *_ in scenarios:
        lines.append(f"  [{label}]")
        base_d = results[label][base_name]["dmg"]
        for name in FULL_BUILDS:
            row = results[label][name]
            tag = (
                f"  mana-cap {row['shots']}/{row['cd_cap']} R"
                if row["mana_capped"]
                else f"  CD-cap {row['shots']} R"
            )
            delta = pct(row["dmg"], base_d) if name != base_name else "baseline"
            phys_share = 100.0 * row["phys"] / row["dmg"] if row["dmg"] else 0.0
            lines.append(
                f"    {name:<22} {row['dmg']:>8.0f}  {delta:>8}  "
                f"echo {row['echo']:>5.0f} BF {row['bf']:>5.0f} "
                f"phys {phys_share:.0f}%{tag}"
            )
        lines.append("")

    focus = ["Core Kog", "MF 4-pack + Cap", "PC-legal Luden poke", "PC-legal BF poke"]
    lines.append("-" * 82)
    lines.append("BREAKDOWN fog 8s TANK  (sau MR/armor, trước mult)")
    lines.append("-" * 82)
    label = "Fog 8s vs TANK"
    for name in focus:
        row = results[label][name]
        p = row["parts"]
        st = kits[name]
        lines.append(
            f"  {name}  AP {st['ap']:.0f} bAD {st['bonus_ad']:.0f}  "
            f"mult x{row['mult']:.3f}  final {row['dmg']:.0f}"
        )
        lines.append(
            f"    MAGIC Q {p.q:.0f} | R {p.r:.0f} ({p.shots}s) | "
            f"Liandry {p.liandry:.0f} | Hatefog {p.hatefog:.0f} | "
            f"Comet {p.comet:.0f} | Echo {row['echo']/row['mult']:.0f} | "
            f"BF {row['bf']/row['mult']:.0f}"
        )
        lines.append(
            f"    PHYS  Shock Q {p.shock_q:.0f} R {p.shock_r:.0f} "
            f"(raw {p.shock_raw_r:.0f}/R)"
        )
    lines.append("")

    fog_t = results["Fog 8s vs TANK"]
    fog_s = results["Fog 8s vs SQUISHY"]
    w_t = results["W 8s vs TANK"]
    fog20 = results["Fog 20s vs TANK"]
    pack = "MF 4-pack + Cap"
    pack_v = "MF 4-pack + Void"
    lud = "PC-legal Luden poke"
    bfp = "PC-legal BF poke"
    nom = "4-pack không Mura"

    def mix70(a, b):
        return 0.70 * a["dmg"] + 0.30 * b["dmg"]

    mix_core = mix70(fog_t[base_name], w_t[base_name])
    mix_pack = mix70(fog_t[pack], w_t[pack])
    mix_lud = mix70(fog_t[lud], w_t[lud])
    mix_bf = mix70(fog_t[bfp], w_t[bfp])

    lines.append("-" * 82)
    lines.append("MẠNH / YẾU")
    lines.append("-" * 82)
    lines.append("  1) FULL 4-PACK + CAP  (đúng MF poke, 2× Lost Chapter)")
    lines.append(
        f"     Fog tank 8s:  {pct(fog_t[pack]['dmg'], fog_t[base_name]['dmg'])}  "
        f"({fog_t[pack]['dmg']:.0f} vs {fog_t[base_name]['dmg']:.0f})"
    )
    lines.append(f"     Fog squish:   {pct(fog_s[pack]['dmg'], fog_s[base_name]['dmg'])}")
    lines.append(f"     W tank:       {pct(w_t[pack]['dmg'], w_t[base_name]['dmg'])}")
    lines.append(f"     Fog 20s tank: {pct(fog20[pack]['dmg'], fog20[base_name]['dmg'])}")
    lines.append(f"     Mix 70/30 tank:{pct(mix_pack, mix_core)}")
    lines.append(
        f"     Echo fog tank: {fog_t[pack]['echo']:.0f}  |  BF burn: {fog_t[pack]['bf']:.0f}  "
        f"|  Shock phys: {fog_t[pack]['phys']:.0f}"
    )
    lines.append("     NHIỀU QUÁ: 2 mana item chồng AH/mana, BF burn nhỏ vs tank,")
    lines.append("     Echo 1 lần / 8s trong khi R bắn 10 shot, không Hatefog,")
    lines.append("     không Void. Mana cao → nhiều R, không bù %pen + zone.")
    lines.append("")
    lines.append("  2) 4-PACK + VOID (bỏ Cap)")
    lines.append(f"     Fog tank: {pct(fog_t[pack_v]['dmg'], fog_t[base_name]['dmg'])}")
    lines.append(f"     W tank:   {pct(w_t[pack_v]['dmg'], w_t[base_name]['dmg'])}")
    lines.append("     Void cứu tank hơn Cap trên 4-pack, vẫn thiếu Malig 10%.")
    lines.append("")
    lines.append("  3) PC-LEGAL: một Lost Chapter + Mura + Liandry + Void + Cap")
    lines.append(
        f"     Luden version mix tank: {pct(mix_lud, mix_core)}  fog "
        f"{pct(fog_t[lud]['dmg'], fog_t[base_name]['dmg'])}"
    )
    lines.append(
        f"     BF version mix tank:    {pct(mix_bf, mix_core)}  fog "
        f"{pct(fog_t[bfp]['dmg'], fog_t[base_name]['dmg'])}"
    )
    lines.append("     Fog nhỉnh nhờ Mura +2 R (mana-cap). W-tank thua vì mất")
    lines.append("     Horizon 10% trên W %HP. Mix gần hòa. Thua core+Mura 5th")
    lines.append("     (~+9% mix) vì Luden/BF ≠ Hatefog zone. Echo/BF burn nhỏ.")
    lines.append("")
    lines.append("  4) BỎ MURAMANA, GIỮ VOID+CAP")
    lines.append(f"     Fog tank: {pct(fog_t[nom]['dmg'], fog_t[base_name]['dmg'])}")
    lines.append("     Tách Shock: Mura không cứu 4-pack vs tank.")
    lines.append("")

    lines.append("-" * 82)
    lines.append("VERDICT")
    lines.append("-" * 82)
    lines.append(
        f"  4-pack Luden+BF+Liandry+Mura+Cap vs core, mix 70/30 tank: "
        f"{pct(mix_pack, mix_core)}"
    )
    lines.append("  Có, NHIỀU QUÁ — ba món poke chồng cùng một việc (mana +")
    lines.append("  burn AP + Shock) và thiếu identity Kog (Hatefog + Void).")
    lines.append("  Trên MF: Q vật lý + 1 Echo/trade = kit đúng. Trên Kog: R")
    lines.append("  phép spam → Echo loãng, Shock vật lý, 2× LC illegal PC.")
    lines.append("")
    lines.append("  Nếu thích 'mana poke' trên Kog:")
    lines.append("    • Một Lost Chapter thôi: Malignance (không Luden/BF).")
    lines.append("    • Liandry vs tank. Void vs MR. Cap.")
    lines.append("    • Muramana = flex món 5 nếu dump R OOM (như Seraph),")
    lines.append("      transform trước Malig. Không stack Luden+BF.")
    lines.append("  Default vẫn: Malig → Liandry → Void → Cap → Horizon.")
    lines.append("=" * 82)

    payload = {
        "level": level,
        "minute": minute,
        "manaflow_note": "Luden+Blackfire unique on PC; simulated anyway",
        "kits": {
            n: {
                "items": FULL_BUILDS[n].items,
                "ap": round(st["ap"], 1),
                "bonus_ad": round(st["bonus_ad"], 1),
                "max_mana": round(st["max_mana"], 1),
                "manaflow_count": st["manaflow_count"],
                "note": FULL_BUILDS[n].note,
            }
            for n, st in kits.items()
        },
        "scenarios": {
            label: {
                name: {
                    "damage": round(row["dmg"], 1),
                    "echo": round(row["echo"], 1),
                    "blackfire": round(row["bf"], 1),
                    "physical": round(row["phys"], 1),
                    "shots": row["shots"],
                    "mana_capped": row["mana_capped"],
                }
                for name, row in results[label].items()
            }
            for label, *_ in scenarios
        },
        "mix_70_30_tank": {
            "Core Kog": round(mix_core, 1),
            "MF 4-pack + Cap": round(mix_pack, 1),
            "PC-legal Luden poke": round(mix_lud, 1),
            "PC-legal BF poke": round(mix_bf, 1),
        },
    }
    return "\n".join(lines), payload


def main() -> None:
    text, payload = compare()
    print(text)
    with open("/workspace/ap-kogmaw-sim/mf_poke_compare.txt", "w", encoding="utf-8") as f:
        f.write(text + "\n")
    with open("/workspace/ap-kogmaw-sim/mf_poke_compare.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print("\nWrote ap-kogmaw-sim/mf_poke_compare.txt and mf_poke_compare.json")


if __name__ == "__main__":
    main()
