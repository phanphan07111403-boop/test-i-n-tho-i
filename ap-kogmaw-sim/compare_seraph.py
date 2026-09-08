#!/usr/bin/env python3
"""
AP Kog'Maw — Seraph's Embrace vs no-Seraph full-build comparison.

Patch ~26.x: Seraph is 70 AP / 1000 mana / 25 AH, Awe = 2% bonus mana as AP,
Lifeline = 18% max mana shield (3s, 90s CD). Seraph is NOT Manaflow-exclusive
(after 26.1), but Archangel's Staff still is — so Malignance + Seraph only
works if Seraph has already transformed, then you buy Malignance.

Full build = 5 legendaries + Sorcerer's Shoes (6 inventory slots).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple
import json

from simulate_ap_kogmaw import (
    ITEMS,
    apply_pen,
    attack_speed,
    haste_cdr_mult,
    level_at_minute,
    magic_mult,
    q_damage,
    q_shred_pct,
    r_min_damage,
    skill_rank,
    squishy_hp,
    squishy_mr,
    tank_hp,
    tank_mr,
    w_pct,
)


def kog_base_mana(level: int) -> float:
    return 350.0 + 40.0 * (level - 1)


def kog_base_hp(level: int) -> float:
    return 635.0 + 99.0 * (level - 1)


def rune_ap(level: int) -> float:
    adaptive = 18.0
    # Absolute Focus ~8 → 30 while >70% HP (fog poke)
    focus = 8.0 + 22.0 * (level - 1) / 17.0
    return adaptive + focus


def manaflow_bonus(level: int) -> float:
    # Stacked by mid game
    return 250.0 if level >= 10 else 25.0 * max(0, level - 2)


@dataclass
class Kit:
    name: str
    items: List[str]
    note: str = ""


FULL_BUILDS: Dict[str, Kit] = {
    "KHÔNG Seraph (hiện tại)": Kit(
        "KHÔNG Seraph (hiện tại)",
        [
            "Malignance",
            "Sorcerer's Shoes",
            "Liandry's Torment",
            "Void Staff",
            "Rabadon's Deathcap",
            "Horizon Focus",
        ],
        "Malig + Liandry + Void + Cap + Horizon — món 5 là Hypershot 10%",
    ),
    "CÓ Seraph (thay Horizon)": Kit(
        "CÓ Seraph (thay Horizon)",
        [
            "Malignance",
            "Sorcerer's Shoes",
            "Liandry's Torment",
            "Void Staff",
            "Rabadon's Deathcap",
            "Seraph's Embrace",
        ],
        "Giữ Malig+Liandry+Void+Cap; Seraph thay Horizon. Phải transform Seraph TRƯỚC Malig.",
    ),
    "CÓ Seraph (thay Malig)": Kit(
        "CÓ Seraph (thay Malig)",
        [
            "Seraph's Embrace",
            "Sorcerer's Shoes",
            "Liandry's Torment",
            "Void Staff",
            "Rabadon's Deathcap",
            "Horizon Focus",
        ],
        "Seraph làm mana item, giữ Horizon 10%. Mất Hatefog + 20 ult haste.",
    ),
    "CÓ Seraph (thay Deathcap)": Kit(
        "CÓ Seraph (thay Deathcap)",
        [
            "Malignance",
            "Sorcerer's Shoes",
            "Liandry's Torment",
            "Void Staff",
            "Horizon Focus",
            "Seraph's Embrace",
        ],
        "Giữ fog kit (Malig+Horizon) nhưng mất 30% AP amp.",
    ),
}


def kit_stats(kit: Kit, level: int) -> dict:
    inv = [ITEMS[n] for n in kit.items]
    ap = ah = item_mana = as_pct = flat = pct = uh = item_hp = 0.0
    malig = liandry = cap = horizon = seraph = archangel = sf = void = False
    for it in inv:
        ap += it.ap
        ah += it.ah
        item_mana += it.mana
        as_pct += it.as_pct
        flat += it.flat_mpen
        pct += it.pct_mpen
        uh += it.ult_haste
        item_hp += it.hp
        malig = malig or it.malignance
        liandry = liandry or it.liandry
        cap = cap or it.deathcap
        horizon = horizon or it.horizon
        seraph = seraph or it.seraph
        archangel = archangel or it.archangel
        sf = sf or it.name == "Shadowflame"
        void = void or it.name == "Void Staff"

    bonus_mana = item_mana + manaflow_bonus(level)
    awe_ratio = 0.02 if seraph else (0.01 if archangel else 0.0)
    awe_ap = awe_ratio * bonus_mana
    ap += awe_ap + rune_ap(level)
    if cap:
        ap *= 1.30

    max_mana = kog_base_mana(level) + bonus_mana
    shield = 0.18 * max_mana if seraph else 0.0
    kog_hp = kog_base_hp(level) + item_hp

    return {
        "ap": ap,
        "ah": ah,
        "uh": uh,
        "as_pct": as_pct,
        "flat": flat,
        "pct": pct,
        "bonus_mana": bonus_mana,
        "max_mana": max_mana,
        "awe_ap": awe_ap * (1.30 if cap else 1.0),
        "awe_ap_raw": awe_ap,
        "shield": shield,
        "kog_hp": kog_hp,
        "malig": malig,
        "liandry": liandry,
        "cap": cap,
        "horizon": horizon,
        "seraph": seraph,
        "sf": sf,
        "void": void,
        "names": kit.items,
    }


def r_mana_total(n: int) -> float:
    """Total mana for n Living Artillery shots (40, 80, … 40n)."""
    return 20.0 * n * (n + 1)


def r_count(level: int, st: dict, window: float, use_w: bool) -> Tuple[int, float, int]:
    """Returns (shots, cd, cd_cap). Mana and cooldown both bind."""
    rank = skill_rank(level, "R")
    if rank <= 0:
        return 0, 99.0, 0
    base = [0, 2.0, 1.5, 1.0][rank]
    cd = base * haste_cdr_mult(st["ah"] + st["uh"])
    cd_cap = min(12, 1 + int(max(0.0, window - 0.55) / max(0.35, cd)))
    pool = st["max_mana"] * 0.90
    opener = 180.0 if use_w else 40.0  # Q+W+E vs Q only
    budget = max(0.0, pool - opener)
    n = 0
    for k in range(1, cd_cap + 1):
        if r_mana_total(k) <= budget:
            n = k
        else:
            break
    return n, cd, cd_cap


@dataclass
class Parts:
    q: float = 0.0
    r: float = 0.0
    w: float = 0.0
    liandry: float = 0.0
    hatefog: float = 0.0
    comet: float = 0.0
    shots: int = 0
    cd: float = 0.0
    cd_cap: int = 0
    mana_capped: bool = False

    def pre_mult(self) -> float:
        return self.q + self.r + self.w + self.liandry + self.hatefog + self.comet

    def as_dict(self) -> dict:
        return {
            "Q": round(self.q, 1),
            "R": round(self.r, 1),
            "W": round(self.w, 1),
            "Liandry": round(self.liandry, 1),
            "Hatefog": round(self.hatefog, 1),
            "Comet": round(self.comet, 1),
            "shots": self.shots,
        }


def window_parts(
    *,
    level: int,
    st: dict,
    hp: float,
    mr: float,
    window: float,
    use_w: bool,
    vs_tank: bool,
) -> Tuple[float, Parts, float]:
    """Returns (final damage, parts before horizon/cutdown, final multiplier)."""
    ap = st["ap"]
    shots, cd, cd_cap = r_count(level, st, window, use_w)
    p = Parts(shots=shots, cd=cd, cd_cap=cd_cap, mana_capped=shots < cd_cap)

    shred = q_shred_pct(level)
    malig_shred = 10.0 if st["malig"] and shots >= 1 else 0.0
    mr_pre = apply_pen(mr, shred, 0.0, st["pct"], st["flat"])
    mr_post = apply_pen(mr, shred, malig_shred, st["pct"], st["flat"])
    m_pre = magic_mult(mr_pre)
    m_post = magic_mult(mr_post)

    suffer = 1.0
    if st["liandry"]:
        suffer = 1.06 if use_w else 1.04
    if vs_tank:
        r_amp = 1.12
        cinder = 1.0
    else:
        r_amp = 1.28
        cinder = 1.12 if st["sf"] else 1.0

    p.q = q_damage(level, ap) * m_pre
    r_hit = r_min_damage(level, ap) * r_amp
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
    if use_w:
        wp = w_pct(level, ap)
        if wp > 0:
            autos = attack_speed(level, st["as_pct"]) * min(8.0, window)
            p.w = autos * (hp * wp) * m_post

    mult = suffer * cinder
    if st["horizon"]:
        mult *= 1.10
    if vs_tank:
        mult *= 1.08  # Cut Down
    total = p.pre_mult() * mult
    return total, p, mult


def pct(a: float, b: float) -> str:
    if b == 0:
        return "n/a"
    d = 100.0 * (a / b - 1.0)
    return f"{d:+.1f}%"


def line_table(rows: List[Tuple[str, ...]], widths: List[int]) -> List[str]:
    out = []
    for row in rows:
        out.append("  " + "".join(str(c).ljust(w) for c, w in zip(row, widths)))
    return out


def compare(level: int = 18, minute: int = 28) -> Tuple[str, dict]:
    thp, tmr = tank_hp(minute), tank_mr(minute)
    shp, smr = squishy_hp(minute), squishy_mr(minute)
    kits = {k: kit_stats(v, level) for k, v in FULL_BUILDS.items()}
    base_name = "KHÔNG Seraph (hiện tại)"
    base = kits[base_name]

    scenarios = [
        ("Fog 8s vs TANK (núp R, không W)", 8.0, False, True, thp, tmr),
        ("Fog 8s vs SQUISHY", 8.0, False, False, shp, smr),
        ("W siege 8s vs TANK (brush autos)", 8.0, True, True, thp, tmr),
        ("W siege 8s vs SQUISHY", 8.0, True, False, shp, smr),
        ("Fog 20s vs TANK (siege R kéo dài)", 20.0, False, True, thp, tmr),
        ("Fog 20s vs SQUISHY", 20.0, False, False, shp, smr),
    ]

    results = {}
    for label, window, use_w, vs_tank, hp, mr in scenarios:
        results[label] = {}
        for name, st in kits.items():
            dmg, parts, mult = window_parts(
                level=level, st=st, hp=hp, mr=mr,
                window=window, use_w=use_w, vs_tank=vs_tank,
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
    lines.append("AP KOG'MAW — SERAPH'S EMBRACE vs KHÔNG SERAPH")
    lines.append(f"Full build (5 legendary + Sorcs) | level {level} | target @ {minute}:00")
    lines.append(f"Tank {thp:.0f} HP / {tmr:.0f} MR   |  Squishy {shp:.0f} HP / {smr:.0f} MR")
    lines.append("=" * 82)
    lines.append("")
    lines.append("LUẬT ITEM (quan trọng)")
    lines.append("  • Archangel's Staff = Manaflow → KHÔNG đeo cùng Malignance/Luden/BF.")
    lines.append("  • Seraph (sau transform) KHÔNG còn Manaflow (patch 26.1) → được")
    lines.append("    đeo cùng Malignance, NHƯNG phải transform xong rồi mới mua Malig.")
    lines.append("  • Hệ quả: muốn Malig+Seraph thì Tear/Archangel TRƯỚC, Malig sau")
    lines.append("    ~12–16:00. Mất spike Malig phút 7. Liandry/Void delayed.")
    lines.append("  • Seraph: 70 AP, 1000 mana, 25 AH, Awe 2% bonus mana,")
    lines.append("    Lifeline 18% max mana shield / 3s / 90s CD.")
    lines.append("")
    lines.append("-" * 82)
    lines.append("STATS FULL BUILD")
    lines.append("-" * 82)
    hdr = (
        f"  {'Build':<32} {'AP':>6} {'AH':>4} {'UH':>3} {'Mana':>5} "
        f"{'AweAP':>6} {'Shield':>7} {'HP':>5}"
    )
    lines.append(hdr)
    for name, st in kits.items():
        lines.append(
            f"  {name:<32} {st['ap']:>6.0f} {st['ah']:>4.0f} {st['uh']:>3.0f} "
            f"{st['max_mana']:>5.0f} {st['awe_ap']:>6.0f} {st['shield']:>7.0f} "
            f"{st['kog_hp']:>5.0f}"
        )
    lines.append("")
    lines.append("  Slot 5 so với Horizon (75 AP + 25 AH + 10% Hypershot):")
    s = kits["CÓ Seraph (thay Horizon)"]
    lines.append(
        f"    Seraph: 70 AP + {s['awe_ap_raw']:.0f} Awe raw "
        f"({s['awe_ap']:.0f} sau Deathcap) + 1000 mana + "
        f"{s['shield']:.0f} shield. Cùng 25 AH. Mất 10% amp."
    )
    lines.append("")

    lines.append("-" * 82)
    lines.append("DAMAGE THEO CỬA SỔ  (Δ vs KHÔNG Seraph)")
    lines.append("-" * 82)
    for label, *_ in scenarios:
        lines.append(f"  [{label}]")
        base_d = results[label][base_name]["dmg"]
        for name in FULL_BUILDS:
            row = results[label][name]
            tag = ""
            if row["mana_capped"]:
                tag = f"  mana-cap {row['shots']}/{row['cd_cap']} R"
            else:
                tag = f"  CD-cap {row['shots']} R"
            delta = pct(row["dmg"], base_d) if name != base_name else "baseline"
            lines.append(
                f"    {name:<32} {row['dmg']:>8.0f}  {delta:>8}{tag}"
            )
        lines.append("")

    # Breakdown on the two primary builds
    pair = [base_name, "CÓ Seraph (thay Horizon)"]
    lines.append("-" * 82)
    lines.append("BREAKDOWN NGUỒN DAMAGE  (sau MR, trước Horizon/Cut Down/Suffering)")
    lines.append("  Rồi nhân multiplier (Horizon 10% / Cut Down 8% / Madness).")
    lines.append("-" * 82)
    for label in (
        "Fog 8s vs TANK (núp R, không W)",
        "W siege 8s vs TANK (brush autos)",
        "Fog 20s vs TANK (siege R kéo dài)",
    ):
        lines.append(f"  [{label}]")
        for name in pair:
            row = results[label][name]
            p = row["parts"]
            st = kits[name]
            lines.append(
                f"    {name}  AP {st['ap']:.0f}  mult x{row['mult']:.3f}  "
                f"final {row['dmg']:.0f}"
            )
            lines.append(
                f"      Q {p.q:7.0f} | R {p.r:7.0f} ({p.shots} shot) | "
                f"W {p.w:7.0f} | Liandry {p.liandry:7.0f} | "
                f"Hatefog {p.hatefog:7.0f} | Comet {p.comet:6.0f}"
            )
        # per-source delta
        a = results[label][pair[1]]["parts"]
        b = results[label][pair[0]]["parts"]
        lines.append("    Seraph−baseline (pre-mult):")
        lines.append(
            f"      Q {a.q-b.q:+.0f} | R {a.r-b.r:+.0f} | W {a.w-b.w:+.0f} | "
            f"Liandry {a.liandry-b.liandry:+.0f} | Hatefog {a.hatefog-b.hatefog:+.0f} | "
            f"Comet {a.comet-b.comet:+.0f}"
        )
        lines.append("")

    # Where strong / weak
    fog8_t = results["Fog 8s vs TANK (núp R, không W)"]
    fog8_s = results["Fog 8s vs SQUISHY"]
    w8_t = results["W siege 8s vs TANK (brush autos)"]
    fog20_t = results["Fog 20s vs TANK (siege R kéo dài)"]
    ser = "CÓ Seraph (thay Horizon)"
    nomal = "CÓ Seraph (thay Malig)"
    nocap = "CÓ Seraph (thay Deathcap)"

    lines.append("-" * 82)
    lines.append("MẠNH CHỖ NÀO / YẾU CHỖ NÀO")
    lines.append("-" * 82)
    lines.append("  1) Seraph THAY HORIZON (giữ Malig+Liandry+Void+Cap)")
    lines.append(
        f"     Fog 8s tank:   {pct(fog8_t[ser]['dmg'], fog8_t[base_name]['dmg'])}  "
        f"({fog8_t[ser]['dmg']:.0f} vs {fog8_t[base_name]['dmg']:.0f})"
    )
    lines.append(
        f"     Fog 8s squish: {pct(fog8_s[ser]['dmg'], fog8_s[base_name]['dmg'])}"
    )
    lines.append(
        f"     W 8s tank:     {pct(w8_t[ser]['dmg'], w8_t[base_name]['dmg'])}"
    )
    lines.append(
        f"     Fog 20s tank:  {pct(fog20_t[ser]['dmg'], fog20_t[base_name]['dmg'])}"
    )
    lines.append(
        f"     R shots 8s fog: {fog8_t[ser]['shots']} vs {fog8_t[base_name]['shots']}  "
        f"| 20s: {fog20_t[ser]['shots']} vs {fog20_t[base_name]['shots']}"
    )
    lines.append(f"     Shield: {kits[ser]['shield']:.0f} HP-equivalent / 90s (dưới 30% HP).")
    lines.append("     MẠNH: +2 R (8→10) vì trần là mana; Awe+Cap +48 AP; shield 518.")
    lines.append("     YẾU: mất Horizon 10% trên Liandry + W %HP. Liandry pre-mult")
    lines.append("           không tăng (burn không scale AP). W-tank gần hòa.")
    lines.append("           Fog thuần (không W) thì Seraph thắng rõ.")
    lines.append("")
    lines.append("  2) Seraph THAY MALIGNANCE (giữ Horizon)")
    lines.append(
        f"     Fog 8s tank:   {pct(fog8_t[nomal]['dmg'], fog8_t[base_name]['dmg'])}  "
        f"({fog8_t[nomal]['dmg']:.0f} vs {fog8_t[base_name]['dmg']:.0f})"
    )
    lines.append(
        f"     Fog 20s tank:  {pct(fog20_t[nomal]['dmg'], fog20_t[base_name]['dmg'])}"
    )
    lines.append("     YẾU NẶNG: mất Hatefog 60(+5% AP)/s + 10 MR shred + 20 UH.")
    lines.append("     Zone R là identity núp bắn. Seraph không thay được.")
    lines.append("     MẠNH hơn một chút ở shield + mana thuần, không đủ bù zone.")
    lines.append("")
    lines.append("  3) Seraph THAY DEATHCAP (giữ Malig+Horizon)")
    lines.append(
        f"     Fog 8s tank:   {pct(fog8_t[nocap]['dmg'], fog8_t[base_name]['dmg'])}"
    )
    lines.append(
        f"     W 8s tank:     {pct(w8_t[nocap]['dmg'], w8_t[base_name]['dmg'])}"
    )
    lines.append("     YẾU: W %HP và R scale AP mất 30% multiplier. Đau tank giảm.")
    lines.append("     Chỉ cân nhắc nếu bạn OOM liên tục và không bao giờ đủ gold Cap.")
    lines.append("")
    lines.append("  TIMING (không hiện trên bảng full-build):")
    lines.append("     Tear 400g từ back đầu → Archangel ~11:00 → Seraph transform")
    lines.append("     ~14–16:00 → Malig ~18–20:00 → Liandry ~24:00. Path không")
    lines.append("     Seraph đã có Liandry ~16 và Void ~21. Mid-game tank damage")
    lines.append("     của path Seraph+Malig TỤT cho đến khi 4 món xong.")
    lines.append("")
    lines.append("-" * 82)
    lines.append("VERDICT SERAPH")
    lines.append("-" * 82)

    d8 = fog8_t[ser]["dmg"] - fog8_t[base_name]["dmg"]
    d20 = fog20_t[ser]["dmg"] - fog20_t[base_name]["dmg"]
    dw = w8_t[ser]["dmg"] - w8_t[base_name]["dmg"]
    mix_base = 0.70 * fog8_t[base_name]["dmg"] + 0.30 * w8_t[base_name]["dmg"]
    mix_ser = 0.70 * fog8_t[ser]["dmg"] + 0.30 * w8_t[ser]["dmg"]
    lines.append("  LATE GAME (cả 5 món xong, so slot 5 Seraph vs Horizon):")
    lines.append(
        f"    Fog 8s tank {d8:+.0f} ({pct(fog8_t[ser]['dmg'], fog8_t[base_name]['dmg'])})  "
        f"| W-tank {dw:+.0f} ({pct(w8_t[ser]['dmg'], w8_t[base_name]['dmg'])})"
    )
    lines.append(
        f"    Mix 70/30 núp+siege vs tank: {mix_ser:.0f} vs {mix_base:.0f}  "
        f"({pct(mix_ser, mix_base)})"
    )
    lines.append("    Seraph thắng DPS vì +2 R (8→10) — mana là trần, không phải CD.")
    lines.append("    W vs tank gần hòa: Horizon 10% ăn vào W %HP (cột W to),")
    lines.append("    bù gần hết 2 R thêm. Fog thuần (không W) thì Seraph rõ hơn.")
    lines.append("")
    lines.append("  KHÔNG đổi Malignance: fog tank "
                 f"{pct(fog8_t[nomal]['dmg'], fog8_t[base_name]['dmg'])} / "
                 f"20s {pct(fog20_t[nomal]['dmg'], fog20_t[base_name]['dmg'])}.")
    lines.append("  KHÔNG đổi Deathcap: W tank "
                 f"{pct(w8_t[nocap]['dmg'], w8_t[base_name]['dmg'])} — mất 30% AP.")
    lines.append("")
    lines.append("  GIÁ PHẢI TRẢ: Tear → Archangel → Seraph TRƯỚC Malig.")
    lines.append("    Mất spike Hatefog phút 7–16, Liandry/Void muộn ~4–6 phút.")
    lines.append("    Bảng trên là full-build đã xong; mid-game path Seraph TỤT.")
    lines.append("")
    lines.append("  Nên Seraph khi:")
    lines.append("    • Bạn chấp nhận late (4–5 món) và núp R dump — mana-cap thật;")
    lines.append("    • Bị dive, cần Lifeline ~518 shield / 90s;")
    lines.append("    • Có slot 6/7 (bot quest): giữ Horizon + thêm Seraph, không thay.")
    lines.append("  Không Seraph khi:")
    lines.append("    • Game hay kết 20–25 phút (chưa tới 5 món / Tear delay);")
    lines.append("    • Play W siege tank nhiều hơn dump R;")
    lines.append("    • Phải thay Malig hoặc Deathcap.")
    lines.append("  Default vẫn: Malig → Liandry → Void → Cap → Horizon.")
    lines.append("  Seraph = flex món 5 NẾU bạn dump R đến OOM; không phải core.")
    lines.append("=" * 82)

    payload = {
        "level": level,
        "minute": minute,
        "tank": {"hp": thp, "mr": tmr},
        "squishy": {"hp": shp, "mr": smr},
        "kits": {
            n: {
                "items": FULL_BUILDS[n].items,
                "ap": round(st["ap"], 1),
                "ah": st["ah"],
                "ult_haste": st["uh"],
                "max_mana": round(st["max_mana"], 1),
                "awe_ap": round(st["awe_ap"], 1),
                "shield": round(st["shield"], 1),
                "kog_hp": round(st["kog_hp"], 1),
                "note": FULL_BUILDS[n].note,
            }
            for n, st in kits.items()
        },
        "scenarios": {
            label: {
                name: {
                    "damage": round(row["dmg"], 1),
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
    }
    return "\n".join(lines), payload


def main() -> None:
    text, payload = compare()
    print(text)
    with open("/workspace/ap-kogmaw-sim/seraph_compare.txt", "w", encoding="utf-8") as f:
        f.write(text + "\n")
    with open("/workspace/ap-kogmaw-sim/seraph_compare.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print("\nWrote ap-kogmaw-sim/seraph_compare.txt and seraph_compare.json")


if __name__ == "__main__":
    main()
