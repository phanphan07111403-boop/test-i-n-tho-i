#!/usr/bin/env python3
"""
AP Kog'Maw — mix (Muramana + armor pen + slow) vs full AP.

Patch ~26.x: Living Artillery is MAGIC damage. The 75% bonus AD ratio
rides on that magic hit — armor pen does not apply to R/Q/W/Liandry/Hatefog.

Muramana Shock is the only meaningful physical damage in this kit.
Serylda's Grudge (45% armor pen, Bitter Cold 30% slow below 60% HP)
only helps Shock / autos, not R itself. Kog E already slows 40–60%.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple
import json

from compare_seraph import (
    kog_base_hp,
    kog_base_mana,
    manaflow_bonus,
    r_count,
    rune_ap,
)
from simulate_ap_kogmaw import (
    ITEMS,
    apply_armor_pen,
    apply_pen,
    attack_speed,
    magic_mult,
    physical_mult,
    q_damage,
    q_shred_pct,
    r_min_breakdown,
    r_min_damage,
    skill_rank,
    squishy_armor,
    squishy_hp,
    squishy_mr,
    tank_armor,
    tank_hp,
    tank_mr,
    w_pct,
)


@dataclass
class Kit:
    name: str
    items: List[str]
    note: str = ""


FULL_BUILDS: Dict[str, Kit] = {
    "AP (baseline)": Kit(
        "AP (baseline)",
        [
            "Malignance",
            "Sorcerer's Shoes",
            "Liandry's Torment",
            "Void Staff",
            "Rabadon's Deathcap",
            "Horizon Focus",
        ],
        "Malig + Liandry + Void + Cap + Horizon — núp bắn default",
    ),
    "Mix Mura+Serylda": Kit(
        "Mix Mura+Serylda",
        [
            "Muramana",
            "Serylda's Grudge",
            "Malignance",
            "Sorcerer's Shoes",
            "Liandry's Torment",
            "Void Staff",
        ],
        "User mix: Muramana + 45% armor pen + Bitter Cold. Mất Cap + Horizon.",
    ),
    "Mix Mura+Rylai": Kit(
        "Mix Mura+Rylai",
        [
            "Muramana",
            "Rylai's Crystal Scepter",
            "Malignance",
            "Sorcerer's Shoes",
            "Liandry's Torment",
            "Void Staff",
        ],
        "Muramana + Rylai 30% slow luôn trên R. Không xuyên giáp.",
    ),
    "Mix Mura+Serylda+Cap": Kit(
        "Mix Mura+Serylda+Cap",
        [
            "Muramana",
            "Serylda's Grudge",
            "Malignance",
            "Sorcerer's Shoes",
            "Liandry's Torment",
            "Rabadon's Deathcap",
        ],
        "Giữ Cap, bỏ Void — R magic yếu vs tank MR.",
    ),
    "AP + Muramana 5th": Kit(
        "AP + Muramana 5th",
        [
            "Malignance",
            "Sorcerer's Shoes",
            "Liandry's Torment",
            "Void Staff",
            "Rabadon's Deathcap",
            "Muramana",
        ],
        "Giữ AP core; Muramana thay Horizon (Shock + 75% bAD trên R magic).",
    ),
    "AP + Rylai 5th": Kit(
        "AP + Rylai 5th",
        [
            "Malignance",
            "Sorcerer's Shoes",
            "Liandry's Torment",
            "Void Staff",
            "Rabadon's Deathcap",
            "Rylai's Crystal Scepter",
        ],
        "Giữ AP core; Rylai thay Horizon — slow magic, không Shock.",
    ),
    "AP + Serylda 5th": Kit(
        "AP + Serylda 5th",
        [
            "Malignance",
            "Sorcerer's Shoes",
            "Liandry's Torment",
            "Void Staff",
            "Rabadon's Deathcap",
            "Serylda's Grudge",
        ],
        "Xuyên giáp không Shock: 45 AD trên R magic, pen không ăn R.",
    ),
    "Mix không Malig": Kit(
        "Mix không Malig",
        [
            "Muramana",
            "Serylda's Grudge",
            "Sorcerer's Shoes",
            "Liandry's Torment",
            "Void Staff",
            "Rabadon's Deathcap",
        ],
        "Mura+Serylda+Liandry+Void+Cap — mất Hatefog + 20 ult haste.",
    ),
}


def kit_stats(kit: Kit, level: int) -> dict:
    inv = [ITEMS[n] for n in kit.items]
    ap = ah = item_mana = as_pct = flat = pct = uh = item_hp = 0.0
    item_ad = pct_armor = lethality = 0.0
    malig = liandry = cap = horizon = seraph = archangel = False
    sf = void = nashor = muramana = manamune = serylda = rylai = False
    for it in inv:
        ap += it.ap
        ah += it.ah
        item_mana += it.mana
        as_pct += it.as_pct
        flat += it.flat_mpen
        pct += it.pct_mpen
        uh += it.ult_haste
        item_hp += it.hp
        item_ad += it.ad
        pct_armor += it.pct_armor_pen
        lethality += it.lethality
        malig = malig or it.malignance
        liandry = liandry or it.liandry
        cap = cap or it.deathcap
        horizon = horizon or it.horizon
        seraph = seraph or it.seraph
        archangel = archangel or it.archangel
        sf = sf or it.name == "Shadowflame"
        void = void or it.name == "Void Staff"
        nashor = nashor or it.nashor
        muramana = muramana or it.muramana
        manamune = manamune or it.manamune
        serylda = serylda or it.serylda
        rylai = rylai or it.rylai

    bonus_mana = item_mana + manaflow_bonus(level)
    max_mana = kog_base_mana(level) + bonus_mana
    awe_ap = (0.02 if seraph else (0.01 if archangel else 0.0)) * bonus_mana
    awe_ad = (0.02 * max_mana) if (muramana or manamune) else 0.0
    ap += awe_ap + rune_ap(level)
    if cap:
        ap *= 1.30
    bonus_ad = item_ad + awe_ad

    return {
        "ap": ap,
        "bonus_ad": bonus_ad,
        "item_ad": item_ad,
        "awe_ad": awe_ad,
        "ah": ah,
        "uh": uh,
        "as_pct": as_pct,
        "flat": flat,
        "pct": pct,
        "pct_armor": pct_armor,
        "lethality": lethality,
        "bonus_mana": bonus_mana,
        "max_mana": max_mana,
        "kog_hp": kog_base_hp(level) + item_hp,
        "malig": malig,
        "liandry": liandry,
        "cap": cap,
        "horizon": horizon,
        "seraph": seraph,
        "sf": sf,
        "void": void,
        "nashor": nashor,
        "muramana": muramana,
        "manamune": manamune,
        "serylda": serylda,
        "rylai": rylai,
        "names": kit.items,
    }


@dataclass
class Parts:
    q: float = 0.0
    r: float = 0.0
    w: float = 0.0
    nashor: float = 0.0
    liandry: float = 0.0
    hatefog: float = 0.0
    comet: float = 0.0
    shock_q: float = 0.0
    shock_r: float = 0.0
    shock_w: float = 0.0
    shock_auto: float = 0.0
    shots: int = 0
    cd: float = 0.0
    cd_cap: int = 0
    mana_capped: bool = False
    autos: float = 0.0
    r_raw: float = 0.0
    r_from_ad: float = 0.0
    r_from_ap: float = 0.0
    r_base: float = 0.0
    shock_raw_r: float = 0.0

    def magic_pre(self) -> float:
        return (
            self.q
            + self.r
            + self.w
            + self.nashor
            + self.liandry
            + self.hatefog
            + self.comet
        )

    def phys_pre(self) -> float:
        return self.shock_q + self.shock_r + self.shock_w + self.shock_auto

    def pre_mult(self) -> float:
        return self.magic_pre() + self.phys_pre()

    def as_dict(self) -> dict:
        return {
            "Q": round(self.q, 1),
            "R_magic": round(self.r, 1),
            "W": round(self.w, 1),
            "Nashor": round(self.nashor, 1),
            "Liandry": round(self.liandry, 1),
            "Hatefog": round(self.hatefog, 1),
            "Comet": round(self.comet, 1),
            "Shock_Q": round(self.shock_q, 1),
            "Shock_R": round(self.shock_r, 1),
            "Shock_W": round(self.shock_w, 1),
            "Shock_auto": round(self.shock_auto, 1),
            "magic_pre": round(self.magic_pre(), 1),
            "phys_pre": round(self.phys_pre(), 1),
            "shots": self.shots,
            "autos": round(self.autos, 2),
        }


def window_parts(
    *,
    level: int,
    st: dict,
    hp: float,
    mr: float,
    armor: float,
    window: float,
    use_w: bool,
    vs_tank: bool,
) -> Tuple[float, Parts, float]:
    ap = st["ap"]
    bonus_ad = st["bonus_ad"]
    shots, cd, cd_cap = r_count(level, st, window, use_w)
    p = Parts(shots=shots, cd=cd, cd_cap=cd_cap, mana_capped=shots < cd_cap)

    shred = q_shred_pct(level)
    malig_shred = 10.0 if st["malig"] and shots >= 1 else 0.0
    mr_pre = apply_pen(mr, shred, 0.0, st["pct"], st["flat"])
    mr_post = apply_pen(mr, shred, malig_shred, st["pct"], st["flat"])
    m_pre = magic_mult(mr_pre)
    m_post = magic_mult(mr_post)
    # Q shreds armor too; Serylda %pen only after shred
    a_eff = apply_armor_pen(armor, shred, st["pct_armor"], st["lethality"])
    p_mult = physical_mult(a_eff)

    suffer = 1.0
    if st["liandry"]:
        suffer = 1.06 if use_w else 1.04
    if vs_tank:
        r_amp = 1.12
        cinder = 1.0
    else:
        r_amp = 1.28
        cinder = 1.12 if st["sf"] else 1.0

    base, from_ad, from_ap, r_raw = r_min_breakdown(level, ap, bonus_ad)
    p.r_base, p.r_from_ad, p.r_from_ap, p.r_raw = base, from_ad, from_ap, r_raw

    p.q = q_damage(level, ap) * m_pre
    r_hit = r_min_damage(level, ap, bonus_ad) * r_amp
    for i in range(shots):
        p.r += r_hit * (m_pre if i == 0 else m_post)

    comet_base = 15.0 + 85.0 * (level - 1) / 17.0
    dist = 2.0 if not use_w else 1.55
    p.comet = (comet_base + 0.05 * ap) * dist * m_pre

    burn_t = max(0.0, window - 0.45)
    if st["malig"] and shots >= 1:
        hf_up = min(burn_t, 3.0 + max(0, shots - 1) * 1.6)
        p.hatefog = (60.0 + 0.05 * ap) * hf_up * m_post
    if st["liandry"]:
        p.liandry = 0.02 * hp * burn_t * m_post

    autos = 0.0
    if use_w:
        wp = w_pct(level, ap)
        if wp > 0:
            autos = attack_speed(level, st["as_pct"]) * min(8.0, window)
            p.autos = autos
            p.w = autos * (hp * wp) * m_post
            if st["nashor"]:
                p.nashor = autos * (15.0 + 0.15 * ap) * m_post

    # Muramana Shock is PHYSICAL. Abilities: 3% max mana once per cast (ranged).
    # Autos: 1.2% max mana on-hit. Burns do not re-Shock (same-cast DoT).
    if st["muramana"] or st["manamune"]:
        shock_ability = 0.03 * st["max_mana"]
        shock_auto = 0.012 * st["max_mana"]
        p.shock_q = shock_ability * p_mult
        p.shock_r = shock_ability * shots * p_mult
        p.shock_raw_r = shock_ability
        if use_w:
            p.shock_w = shock_ability * p_mult
            p.shock_auto = shock_auto * autos * p_mult

    mult = suffer * cinder
    if st["horizon"]:
        mult *= 1.10
    if vs_tank:
        mult *= 1.08
    total = p.pre_mult() * mult
    return total, p, mult


def pct(a: float, b: float) -> str:
    if b == 0:
        return "n/a"
    return f"{100.0 * (a / b - 1.0):+.1f}%"


def fog_slow_note(st: dict) -> str:
    """Slow on fog R without landing E. Highest wins; they do not stack."""
    bits = []
    if st["rylai"]:
        bits.append("Rylai 30% luôn trên R")
    if st["serylda"]:
        bits.append("Serylda 30%/1s CHỈ khi đích <60% HP")
    if not bits:
        bits.append("không (E 40–60% nếu rời fog)")
    return "; ".join(bits)


def compare(level: int = 18, minute: int = 28) -> Tuple[str, dict]:
    thp, tmr, tar = tank_hp(minute), tank_mr(minute), tank_armor(minute)
    shp, smr, sar = squishy_hp(minute), squishy_mr(minute), squishy_armor(minute)
    kits = {k: kit_stats(v, level) for k, v in FULL_BUILDS.items()}
    base_name = "AP (baseline)"
    base = kits[base_name]

    # Sanity: 75% bAD is on magic R
    b, ad_part, ap_part, tot = r_min_breakdown(level, base["ap"], base["bonus_ad"])
    assert abs(tot - r_min_damage(level, base["ap"], base["bonus_ad"])) < 1e-6
    mix = kits["Mix Mura+Serylda"]
    assert mix["bonus_ad"] > 100
    assert mix["pct_armor"] >= 0.40
    assert abs(r_min_damage(18, 0.0, 100.0) - (180.0 + 75.0)) < 1e-6
    assert abs(r_min_damage(18, 100.0, 0.0) - (180.0 + 45.0)) < 1e-6

    scenarios = [
        ("Fog 8s vs TANK (núp R, không W)", 8.0, False, True, thp, tmr, tar),
        ("Fog 8s vs SQUISHY", 8.0, False, False, shp, smr, sar),
        ("W siege 8s vs TANK (brush autos)", 8.0, True, True, thp, tmr, tar),
        ("W siege 8s vs SQUISHY", 8.0, True, False, shp, smr, sar),
        ("Fog 20s vs TANK (siege R kéo dài)", 20.0, False, True, thp, tmr, tar),
        ("Fog 20s vs SQUISHY", 20.0, False, False, shp, smr, sar),
    ]

    results: dict = {}
    for label, window, use_w, vs_tank, hp, mr, armor in scenarios:
        results[label] = {}
        for name, st in kits.items():
            dmg, parts, mult = window_parts(
                level=level,
                st=st,
                hp=hp,
                mr=mr,
                armor=armor,
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
                "magic": parts.magic_pre() * mult,
                "phys": parts.phys_pre() * mult,
            }

    lines: List[str] = []
    lines.append("=" * 82)
    lines.append("AP KOG'MAW — MIX MURAMANA / XUYÊN GIÁP / SLOW vs FULL AP")
    lines.append(f"Full build (5 legendary + Sorcs) | level {level} | target @ {minute}:00")
    lines.append(
        f"Tank {thp:.0f} HP / {tmr:.0f} MR / {tar:.0f} armor  |  "
        f"Squishy {shp:.0f} HP / {smr:.0f} MR / {sar:.0f} armor"
    )
    lines.append("=" * 82)
    lines.append("")
    lines.append("LUẬT QUAN TRỌNG (hay hiểu nhầm)")
    lines.append("  • R Living Artillery = SÁT THƯƠNG PHÉP. Ratio 75% bonus AD")
    lines.append("    nằm TRÊN hit phép — không đổi R thành vật lý.")
    lines.append("  • Xuyên giáp (Serylda 45%, LDR, lethality) KHÔNG ăn R/Q/W/")
    lines.append("    Liandry/Hatefog/Comet. Chỉ ăn Shock Muramana + auto.")
    lines.append("  • Q Caustic Spittle shred 16–32% ARMOR và MR — đã có sẵn")
    lines.append("    trên full AP, không cần Serylda để shred tank.")
    lines.append("  • Muramana Shock = vật lý: 3% max mana / chiêu vs tướng")
    lines.append("    (ranged), 1.2% / auto. DoT không proc lại.")
    lines.append("  • Manamune = Manaflow → không đeo cùng Malignance.")
    lines.append("    Muramana (sau transform) không còn Manaflow → được đeo")
    lines.append("    cùng Malig NẾU transform xong rồi mới mua Malig (Tear delay).")
    lines.append("  • Serylda Bitter Cold: 30% slow / 1s CHỈ khi đích <60% HP")
    lines.append("    (patch 26.17: ngưỡng 50%→60%, pen 40%→45%). Fog poke")
    lines.append("    tank ~85% HP → KHÔNG slow. Rylai slow 30% luôn trên R.")
    lines.append("  • E Kog đã slow 40–60% — mạnh hơn Serylda/Rylai. Slow")
    lines.append("    không cộng dồn; cái mạnh nhất thắng. Serylda/Rylai chỉ")
    lines.append("    có giá khi núp R mà không ném E.")
    lines.append("")

    lines.append("-" * 82)
    lines.append("R MIN (trước missing-HP amp / MR) — TẠI SAO 75% AD NGHE CAO")
    lines.append("-" * 82)
    for name in (
        "AP (baseline)",
        "Mix Mura+Serylda",
        "AP + Muramana 5th",
        "AP + Serylda 5th",
    ):
        st = kits[name]
        b0, ad0, ap0, tot0 = r_min_breakdown(level, st["ap"], st["bonus_ad"])
        share_ad = 100.0 * ad0 / tot0 if tot0 else 0.0
        share_ap = 100.0 * ap0 / tot0 if tot0 else 0.0
        lines.append(
            f"  {name:<24} AP {st['ap']:6.0f}  bAD {st['bonus_ad']:5.0f}  "
            f"R={tot0:6.0f}  (base {b0:.0f} + AD {ad0:.0f} {share_ad:.0f}% "
            f"+ AP {ap0:.0f} {share_ap:.0f}%)"
        )
    lines.append("  75% bAD của mix (~100 dmg) < 45% AP của Deathcap kit (~290).")
    lines.append("  Mix R raw THẤP hơn full AP — AD không bù nổi mất Cap/Horizon.")
    lines.append("")

    lines.append("-" * 82)
    lines.append("STATS FULL BUILD")
    lines.append("-" * 82)
    lines.append(
        f"  {'Build':<24} {'AP':>5} {'bAD':>5} {'AH':>4} {'UH':>3} "
        f"{'Mana':>5} {'AweAD':>6} {'ArPen':>5} {'HP':>5}"
    )
    for name, st in kits.items():
        lines.append(
            f"  {name:<24} {st['ap']:>5.0f} {st['bonus_ad']:>5.0f} "
            f"{st['ah']:>4.0f} {st['uh']:>3.0f} {st['max_mana']:>5.0f} "
            f"{st['awe_ad']:>6.0f} {100*st['pct_armor']:>4.0f}% {st['kog_hp']:>5.0f}"
        )
    lines.append("")
    lines.append("  Slow fog-R (không E):")
    for name, st in kits.items():
        lines.append(f"    {name:<24} {fog_slow_note(st)}")
    lines.append("")

    lines.append("-" * 82)
    lines.append("DAMAGE THEO CỬA SỔ  (Δ vs full AP)  |  magic / physical sau mit")
    lines.append("-" * 82)
    for label, *_ in scenarios:
        lines.append(f"  [{label}]")
        base_d = results[label][base_name]["dmg"]
        for name in FULL_BUILDS:
            row = results[label][name]
            if row["mana_capped"]:
                tag = f"  mana-cap {row['shots']}/{row['cd_cap']} R"
            else:
                tag = f"  CD-cap {row['shots']} R"
            delta = pct(row["dmg"], base_d) if name != base_name else "baseline"
            phys_share = (
                100.0 * row["phys"] / row["dmg"] if row["dmg"] else 0.0
            )
            lines.append(
                f"    {name:<24} {row['dmg']:>8.0f}  {delta:>8}  "
                f"mag {row['magic']:>6.0f} phys {row['phys']:>5.0f} "
                f"({phys_share:.0f}%){tag}"
            )
        lines.append("")

    focus = [
        "AP (baseline)",
        "Mix Mura+Serylda",
        "AP + Muramana 5th",
        "Mix Mura+Rylai",
    ]
    lines.append("-" * 82)
    lines.append("BREAKDOWN  (sau MR/armor, trước Horizon/Cut Down/Madness)")
    lines.append("-" * 82)
    for label in (
        "Fog 8s vs TANK (núp R, không W)",
        "W siege 8s vs TANK (brush autos)",
        "Fog 20s vs TANK (siege R kéo dài)",
    ):
        lines.append(f"  [{label}]")
        for name in focus:
            row = results[label][name]
            p = row["parts"]
            st = kits[name]
            lines.append(
                f"    {name}  AP {st['ap']:.0f} bAD {st['bonus_ad']:.0f}  "
                f"mult x{row['mult']:.3f}  final {row['dmg']:.0f}"
            )
            lines.append(
                f"      MAGIC  Q {p.q:6.0f} | R {p.r:6.0f} ({p.shots} shot) | "
                f"W {p.w:6.0f} | Liandry {p.liandry:6.0f} | "
                f"Hatefog {p.hatefog:6.0f} | Comet {p.comet:5.0f}"
            )
            lines.append(
                f"      PHYS   Shock Q {p.shock_q:5.0f} | R {p.shock_r:5.0f} "
                f"(raw {p.shock_raw_r:.0f}/shot) | W {p.shock_w:5.0f} | "
                f"auto {p.shock_auto:5.0f}"
            )
            lines.append(
                f"      R raw split: base {p.r_base:.0f} + 75%AD {p.r_from_ad:.0f} "
                f"+ AP {p.r_from_ap:.0f} = {p.r_raw:.0f}"
            )
        lines.append("")

    fog8_t = results["Fog 8s vs TANK (núp R, không W)"]
    fog8_s = results["Fog 8s vs SQUISHY"]
    w8_t = results["W siege 8s vs TANK (brush autos)"]
    w8_s = results["W siege 8s vs SQUISHY"]
    fog20_t = results["Fog 20s vs TANK (siege R kéo dài)"]
    mixn = "Mix Mura+Serylda"
    mura5 = "AP + Muramana 5th"
    rylai_mix = "Mix Mura+Rylai"
    rylai5 = "AP + Rylai 5th"
    ser5 = "AP + Serylda 5th"
    mixcap = "Mix Mura+Serylda+Cap"
    nomal = "Mix không Malig"

    def mix70(row_fog, row_w) -> float:
        return 0.70 * row_fog["dmg"] + 0.30 * row_w["dmg"]

    mix_base = mix70(fog8_t[base_name], w8_t[base_name])
    mix_user = mix70(fog8_t[mixn], w8_t[mixn])
    mix_m5 = mix70(fog8_t[mura5], w8_t[mura5])

    # Armor leftover after Q shred + Serylda, for the writeup
    shred18 = q_shred_pct(18)
    tank_a_q = apply_armor_pen(tar, shred18, 0.0)
    tank_a_sery = apply_armor_pen(tar, shred18, 0.45)
    tank_mr_void = apply_pen(tmr, shred18, 10.0, 0.40, 12.0)

    lines.append("-" * 82)
    lines.append("MẠNH CHỖ NÀO / YẾU CHỖ NÀO")
    lines.append("-" * 82)
    lines.append("  1) MIX MURAMANA + SERYLDA (thay Cap + Horizon)")
    lines.append(
        f"     Fog 8s tank:   {pct(fog8_t[mixn]['dmg'], fog8_t[base_name]['dmg'])}  "
        f"({fog8_t[mixn]['dmg']:.0f} vs {fog8_t[base_name]['dmg']:.0f})"
    )
    lines.append(
        f"     Fog 8s squish: {pct(fog8_s[mixn]['dmg'], fog8_s[base_name]['dmg'])}"
    )
    lines.append(
        f"     W 8s tank:     {pct(w8_t[mixn]['dmg'], w8_t[base_name]['dmg'])}"
    )
    lines.append(
        f"     W 8s squish:   {pct(w8_s[mixn]['dmg'], w8_s[base_name]['dmg'])}"
    )
    lines.append(
        f"     Fog 20s tank:  {pct(fog20_t[mixn]['dmg'], fog20_t[base_name]['dmg'])}"
    )
    lines.append(
        f"     Mix 70/30 tank:{pct(mix_user, mix_base)}  "
        f"({mix_user:.0f} vs {mix_base:.0f})"
    )
    lines.append(
        f"     Physical share fog tank: "
        f"{100*fog8_t[mixn]['phys']/fog8_t[mixn]['dmg']:.0f}%  "
        f"| W tank: {100*w8_t[mixn]['phys']/w8_t[mixn]['dmg']:.0f}%"
    )
    lines.append(
        f"     Tank armor sau Q shred: {tank_a_q:.0f} → +Serylda 45%: "
        f"{tank_a_sery:.0f} (Shock ăn ~{100*physical_mult(tank_a_sery):.0f}% dmg)."
    )
    lines.append(
        f"     Tank MR sau Q+Hatefog+Void+Sorcs: {tank_mr_void:.0f} "
        f"(R magic ăn ~{100*magic_mult(tank_mr_void):.0f}%)."
    )
    lines.append("     YẾU: mất Deathcap 30% AP (W %HP + R AP ratio + Hatefog).")
    lines.append("           mất Horizon 10% trên CẢ cửa sổ (Liandry + W).")
    lines.append("           R raw thấp hơn dù có 75% bAD. Slow fog không proc")
    lines.append("           trên tank đầy máu (Bitter Cold <60% HP).")
    lines.append("     MẠNH: Shock cho mỗi R; mana cao hơn một chút; 45 AD + Awe")
    lines.append("           trên R magic. Không đủ bù 2 slot AP.")
    lines.append("")
    lines.append("  2) MURAMANA SLOT 5 (giữ Malig+Liandry+Void+Cap)")
    lines.append(
        f"     Fog 8s tank:   {pct(fog8_t[mura5]['dmg'], fog8_t[base_name]['dmg'])}  "
        f"({fog8_t[mura5]['dmg']:.0f} vs {fog8_t[base_name]['dmg']:.0f})"
    )
    lines.append(
        f"     W 8s tank:     {pct(w8_t[mura5]['dmg'], w8_t[base_name]['dmg'])}"
    )
    lines.append(
        f"     Mix 70/30 tank:{pct(mix_m5, mix_base)}"
    )
    lines.append("     Đây là test công bằng nhất: chỉ đổi Horizon → Muramana.")
    lines.append("     Rank 3 R bị mana-cap (8 vs 10 shot) giống Seraph.")
    lines.append("     Fog: +2 R + Shock + 75% bAD > 75 AP Horizon + 10%.")
    lines.append("     W-tank gần hòa: Horizon 10% ăn W %HP; Muramana bù bằng")
    lines.append("     Shock auto + 2 R. Không shield (Seraph có Lifeline).")
    lines.append("     Chỉ thắng nếu bạn thật sự dump R đến OOM. Ít R hơn thì")
    lines.append("     Horizon 10% thắng.")
    lines.append("")
    lines.append("  3) SERYLDA SLOT 5 KHÔNG MURAMANA")
    lines.append(
        f"     Fog 8s tank:   {pct(fog8_t[ser5]['dmg'], fog8_t[base_name]['dmg'])}"
    )
    lines.append(
        f"     W 8s tank:     {pct(w8_t[ser5]['dmg'], w8_t[base_name]['dmg'])}"
    )
    lines.append("     Xuyên giáp gần như phí: không Shock, R vẫn phép.")
    lines.append("     45 AD * 0.75 = +34 R raw — thua 75 AP Horizon + 10%.")
    lines.append("     Slow fog không proc tank đầy máu.")
    lines.append("")
    lines.append("  4) RYlai (slow phép) vs SERYLDA (slow + pen vật lý)")
    lines.append(
        f"     Mix Mura+Rylai fog tank: "
        f"{pct(fog8_t[rylai_mix]['dmg'], fog8_t[base_name]['dmg'])}  |  "
        f"vs Mura+Serylda {pct(fog8_t[rylai_mix]['dmg'], fog8_t[mixn]['dmg'])}"
    )
    lines.append(
        f"     AP + Rylai 5th fog tank: "
        f"{pct(fog8_t[rylai5]['dmg'], fog8_t[base_name]['dmg'])}"
    )
    lines.append("     Rylai: 65 AP + 400 HP + 30% slow LUÔN trên R fog.")
    lines.append("     Serylda thắng DPS Shock vs armor; Rylai thắng utility fog")
    lines.append("     (slow không cần E, không cần đích thấp máu) + AP cho R/W.")
    lines.append("     E Kog 40–60% vẫn mạnh hơn cả hai nếu bạn chịu ném E.")
    lines.append("")
    lines.append("  5) MIX + CAP BỎ VOID / MIX BỎ MALIG")
    lines.append(
        f"     Mura+Serylda+Cap (không Void) fog tank: "
        f"{pct(fog8_t[mixcap]['dmg'], fog8_t[base_name]['dmg'])}"
    )
    lines.append(
        f"     Mix không Malig fog tank: "
        f"{pct(fog8_t[nomal]['dmg'], fog8_t[base_name]['dmg'])}  /  "
        f"20s {pct(fog20_t[nomal]['dmg'], fog20_t[base_name]['dmg'])}"
    )
    lines.append("     Đừng bỏ Void vs tank MR. Đừng bỏ Malig — Hatefog là identity núp.")
    lines.append("")
    lines.append("  TIMING: Manamune/Tear TRƯỚC Malig nếu muốn cả hai.")
    lines.append("     Mất spike Hatefog phút 7. Giống tax Seraph. Mid-game mix TỤT.")
    lines.append("")

    lines.append("-" * 82)
    lines.append("VERDICT MIX")
    lines.append("-" * 82)
    lines.append(
        f"  Mix Muramana+Serylda vs full AP, mix 70/30 tank: "
        f"{pct(mix_user, mix_base)}"
    )
    lines.append(
        f"  Fog 8s tank {pct(fog8_t[mixn]['dmg'], fog8_t[base_name]['dmg'])}  |  "
        f"W 8s tank {pct(w8_t[mixn]['dmg'], w8_t[base_name]['dmg'])}"
    )
    lines.append("  Không hiệu quả hơn nếu thay Cap+Horizon bằng Mura+Serylda.")
    lines.append("  75% bonus AD nghe lớn nhưng:")
    lines.append("    (1) nó là ratio PHÉP — xuyên giáp không nhân R;")
    lines.append("    (2) AP Deathcap kit cho ~3× damage R từ ratio so với AD mix;")
    lines.append("    (3) Shock chỉ ~10% total sau armor tank;")
    lines.append("    (4) Serylda slow không proc fog tank đầy máu;")
    lines.append("    (5) E đã slow mạnh hơn; Q đã shred armor+MR.")
    lines.append("")
    lines.append("  Fog thuần gần hòa (+1%) vì mix bắn 10 R + Shock, full AP")
    lines.append("  bắn 8 R nhưng có Cap+Horizon. W siege -16%: mất 30% AP")
    lines.append("  trên W %HP. Mix 70/30 tank -6%.")
    lines.append("")
    lines.append("  Nếu vẫn muốn 'adap':")
    lines.append("    • Slot 5 Muramana (giữ Malig+Liandry+Void+Cap) — dump R")
    lines.append("      mana-cap, Shock mỗi shot. KHÔNG mua Serylda. Boots Sorcs.")
    lines.append("      Fog tank +15% / W tank +2% / mix +9% vs Horizon 5th,")
    lines.append("      cùng lý do Seraph (+2 R). Không có shield.")
    lines.append("    • Slow fog: Rylai slot 5/6, không phải Serylda.")
    lines.append("    • Serylda chỉ khi W-siege auto nhiều VÀ địch giáp dày")
    lines.append("      — không phải kit núp R.")
    lines.append("  Default damage peak vẫn: Malig → Liandry → Void → Cap →")
    lines.append("  Horizon, trừ khi bạn OOM rank 3 thì Muramana/Seraph flex 5.")
    lines.append("=" * 82)

    payload = {
        "level": level,
        "minute": minute,
        "tank": {"hp": thp, "mr": tmr, "armor": tar},
        "squishy": {"hp": shp, "mr": smr, "armor": sar},
        "r_is_magic": True,
        "armor_pen_applies_to_r": False,
        "kits": {
            n: {
                "items": FULL_BUILDS[n].items,
                "ap": round(st["ap"], 1),
                "bonus_ad": round(st["bonus_ad"], 1),
                "awe_ad": round(st["awe_ad"], 1),
                "ah": st["ah"],
                "ult_haste": st["uh"],
                "max_mana": round(st["max_mana"], 1),
                "pct_armor_pen": st["pct_armor"],
                "kog_hp": round(st["kog_hp"], 1),
                "r_min": round(
                    r_min_damage(level, st["ap"], st["bonus_ad"]), 1
                ),
                "fog_slow": fog_slow_note(st),
                "note": FULL_BUILDS[n].note,
            }
            for n, st in kits.items()
        },
        "scenarios": {
            label: {
                name: {
                    "damage": round(row["dmg"], 1),
                    "magic": round(row["magic"], 1),
                    "physical": round(row["phys"], 1),
                    "shots": row["shots"],
                    "cd_cap": row["cd_cap"],
                    "mana_capped": row["mana_capped"],
                    "mult": round(row["mult"], 4),
                    "parts": row["parts"].as_dict(),
                }
                for name, row in results[label].items()
            }
            for label, *_ in scenarios
        },
        "mix_70_30_tank": {
            "AP (baseline)": round(mix_base, 1),
            "Mix Mura+Serylda": round(mix_user, 1),
            "AP + Muramana 5th": round(mix_m5, 1),
        },
    }
    return "\n".join(lines), payload


def main() -> None:
    text, payload = compare()
    print(text)
    with open("/workspace/ap-kogmaw-sim/mix_compare.txt", "w", encoding="utf-8") as f:
        f.write(text + "\n")
    with open("/workspace/ap-kogmaw-sim/mix_compare.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print("\nWrote ap-kogmaw-sim/mix_compare.txt and mix_compare.json")


if __name__ == "__main__":
    main()
