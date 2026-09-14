#!/usr/bin/env python3
"""
WR 7.2e — Morgana Dark Harvest farm (Q + W), not burst.

Ignore burst from start to finish: no Stormsurge, no R, no Echo, no Squall
in the metric. Luden is a candidate, not a lock.

Every Q and every W is DH potential: target already <50%, or Q+W chips
into that window. DH 35s CD (AH does not reduce it). 1s only on takedown.

Build order uses mid gold. W-max. Spellslinger when T3 boots unlock (10:00).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import json
import os

GAME_MINUTES = 20
T3_BOOTS_MINUTE = 10
OUT_DIR = os.path.dirname(os.path.abspath(__file__))
HF_AMP = 1.10
DH_CD = 35.0


def mid_income(minute: int) -> int:
    if minute <= 4:
        return 430
    if minute <= 8:
        return 520
    if minute <= 12:
        return 570
    if minute <= 16:
        return 620
    return 660


def level_at(minute: int) -> int:
    table = {
        1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7, 7: 8, 8: 9,
        9: 10, 10: 11, 11: 11, 12: 12, 13: 12, 14: 13,
        15: 13, 16: 14, 17: 14, 18: 15, 19: 15, 20: 15,
    }
    return table.get(minute, 2)


@dataclass
class Item:
    name: str
    cost: int
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
    guise: bool = False
    ashes: bool = False
    tags: Tuple[str, ...] = ()


ITEMS: Dict[str, Item] = {
    "Amplifying Tome": Item("Amplifying Tome", 500, ap=20),
    "Ring of Revelation": Item("Ring of Revelation", 300, ah=5),
    "Boots of Speed": Item("Boots of Speed", 400, tags=("boots", "t1")),
    "Ruby Crystal": Item("Ruby Crystal", 500),
    "Blasting Wand": Item("Blasting Wand", 800, ap=45),
    "Needlessly Large Rod": Item("Needlessly Large Rod", 1400, ap=65),
    "Giant's Belt": Item("Giant's Belt", 1000),
    "Fiendish Codex": Item("Fiendish Codex", 900, ap=25, ah=10),
    "Lost Chapter": Item("Lost Chapter", 1200, ap=35, ah=10),
    "Fated Ashes": Item("Fated Ashes", 900, ap=40, ashes=True),
    "Haunting Guise": Item("Haunting Guise", 1300, ap=30, guise=True),
    "Void Amethyst": Item("Void Amethyst", 1000, ap=20, pct_mpen=0.10),
    "Hextech Alternator": Item("Hextech Alternator", 1100, ap=45),
    "Boots of Mana": Item(
        "Boots of Mana", 1200, ap=25, flat_mpen=8, tags=("boots", "t2"),
    ),
    "Spellslinger's Shoes": Item(
        "Spellslinger's Shoes", 2200, ap=40, flat_mpen=18, pct_mpen=0.08,
        tags=("boots", "t3"),
    ),
    "Blackfire Torch": Item(
        "Blackfire Torch", 2800, ap=80, ah=20, blackfire=True,
    ),
    "Luden's Echo": Item("Luden's Echo", 2800, ap=100, ah=10, luden=True),
    "Horizon Focus": Item(
        "Horizon Focus", 2700, ap=80, ah=25, pct_mpen=0.07, horizon=True,
    ),
    "Cryptbloom": Item("Cryptbloom", 3000, ap=70, ah=20, pct_mpen=0.30),
    "Liandry's Torment": Item("Liandry's Torment", 3000, ap=70, liandry=True),
    "Rylai's Crystal Scepter": Item(
        "Rylai's Crystal Scepter", 2700, ap=65, pct_mpen=0.07, rylai=True,
    ),
    "Rabadon's Deathcap": Item(
        "Rabadon's Deathcap", 3400, ap=130, deathcap=True,
    ),
    "Infinity Orb": Item("Infinity Orb", 3100, ap=110, flat_mpen=15, orb=True),
    "Void Staff": Item("Void Staff", 3000, ap=95, pct_mpen=0.40),
}

UPGRADE = {
    "Boots of Mana": ("Boots of Speed", "Amplifying Tome"),
    "Spellslinger's Shoes": ("Boots of Mana",),
    "Lost Chapter": ("Amplifying Tome", "Ring of Revelation"),
    "Fiendish Codex": ("Amplifying Tome",),
    "Fated Ashes": ("Amplifying Tome",),
    "Haunting Guise": ("Amplifying Tome", "Ruby Crystal"),
    "Hextech Alternator": ("Amplifying Tome",),
    "Blackfire Torch": ("Lost Chapter", "Fated Ashes"),
    "Luden's Echo": ("Lost Chapter", "Hextech Alternator"),
    "Horizon Focus": ("Fiendish Codex", "Fiendish Codex", "Amplifying Tome"),
    "Cryptbloom": ("Void Amethyst", "Fiendish Codex", "Amplifying Tome"),
    "Liandry's Torment": ("Haunting Guise", "Fated Ashes"),
    "Rylai's Crystal Scepter": ("Giant's Belt", "Blasting Wand", "Amplifying Tome"),
    "Rabadon's Deathcap": ("Needlessly Large Rod", "Blasting Wand"),
    "Infinity Orb": ("Hextech Alternator", "Needlessly Large Rod"),
    "Void Staff": ("Void Amethyst", "Needlessly Large Rod"),
    "Void Amethyst": ("Amplifying Tome",),
}

NEXT = {k: list(v) for k, v in UPGRADE.items()}
T3 = {"Spellslinger's Shoes"}

HEAD = [
    "Amplifying Tome", "Boots of Speed", "Boots of Mana",
    "Lost Chapter", "Fated Ashes", "Blackfire Torch", "Spellslinger's Shoes",
]
LUDEN_HEAD = [
    "Amplifying Tome", "Boots of Speed", "Boots of Mana",
    "Lost Chapter", "Hextech Alternator", "Luden's Echo", "Spellslinger's Shoes",
]

PATHS: Dict[str, List[str]] = {
    "BF → HF → Crypt": HEAD + ["Horizon Focus", "Cryptbloom"],
    "BF → Crypt → HF": HEAD + ["Cryptbloom", "Horizon Focus"],
    "BF → HF → Cap": HEAD + ["Horizon Focus", "Rabadon's Deathcap"],
    "BF → Liandry → Rylai": HEAD + ["Haunting Guise", "Liandry's Torment", "Rylai's Crystal Scepter"],
    "Luden → HF → Crypt": LUDEN_HEAD + ["Horizon Focus", "Cryptbloom"],
    "BF → Orb → Cap": HEAD + ["Infinity Orb", "Rabadon's Deathcap"],
}


def remaining(name: str, owned: List[str]) -> int:
    need = list(UPGRADE.get(name, ()))
    have = list(owned)
    credit = 0
    for c in need:
        if c in have:
            have.remove(c)
            credit += ITEMS[c].cost
    return max(0, ITEMS[name].cost - credit)


def done(step: str, owned: List[str]) -> bool:
    if step in owned:
        return True
    if step == "Boots of Speed" and any(
        b in owned for b in ("Boots of Mana", "Spellslinger's Shoes")
    ):
        return True
    if step == "Boots of Mana" and "Spellslinger's Shoes" in owned:
        return True
    if step == "Lost Chapter" and (
        "Luden's Echo" in owned or "Blackfire Torch" in owned
    ):
        return True
    if step == "Fated Ashes" and (
        "Blackfire Torch" in owned or "Liandry's Torment" in owned
    ):
        return True
    if step == "Haunting Guise" and "Liandry's Torment" in owned:
        return True
    if step == "Hextech Alternator" and (
        "Luden's Echo" in owned or "Infinity Orb" in owned
    ):
        return True
    if step == "Fiendish Codex" and (
        "Horizon Focus" in owned or "Cryptbloom" in owned
    ):
        return True
    if step == "Void Amethyst" and (
        "Cryptbloom" in owned or "Void Staff" in owned
    ):
        return True
    if step == "Amplifying Tome" and any(
        x in owned
        for x in ITEMS
        if x != "Amplifying Tome" and x != "Boots of Speed"
    ):
        return True
    return False


def can_buy(
    name: str, owned: List[str], gold: int, minute: int, ignore_owned: bool = False,
) -> bool:
    if not ignore_owned and name in owned:
        return False
    if name in T3 and minute < T3_BOOTS_MINUTE:
        return False
    return gold >= remaining(name, owned)


def buy(name: str, owned: List[str], gold: int) -> Tuple[List[str], int]:
    owned = list(owned)
    gold -= remaining(name, owned)
    need = list(UPGRADE.get(name, ()))
    for c in need:
        if c in owned:
            owned.remove(c)
    owned.append(name)
    return owned, gold


def progress(
    path: List[str], owned: List[str], gold: int, minute: int,
) -> Tuple[List[str], int]:
    for step in path:
        if done(step, owned):
            continue
        if can_buy(step, owned, gold, minute):
            owned, gold = buy(step, owned, gold)
            continue
        missing = []
        have = list(owned)
        for c in UPGRADE.get(step, ()):
            if c in have:
                have.remove(c)
            else:
                missing.append(c)
        for comp in missing:
            if can_buy(comp, owned, gold, minute, ignore_owned=True):
                owned, gold = buy(comp, owned, gold)
        if can_buy(step, owned, gold, minute):
            owned, gold = buy(step, owned, gold)
        else:
            break
    return owned, gold


def skill_rank(level: int, skill: str) -> int:
    if skill == "R":
        return 0 if level < 6 else 1 if level < 11 else 2 if level < 15 else 3
    q_lv, w_lv = [3, 8, 9, 10, 12], [1, 2, 4, 5, 7]
    return min(4, sum(1 for lv in {"Q": q_lv, "W": w_lv}[skill] if level >= lv))


def trans_ah(level: int) -> float:
    return 12.0 if level >= 5 else 6.0


def dh_souls(minute: int) -> float:
    return max(0.0, min(14.0, 0.7 * max(0, minute - 3)))


def dh_raw(ap: float, souls: float) -> float:
    return 35.0 + 11.0 * souls + 0.05 * ap


def ah_cd(base: float, ah: float) -> float:
    return base * 100.0 / (100.0 + max(0.0, ah))


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
    rylai: bool


def stats_of(owned: List[str], level: int) -> Stats:
    ap = ah = flat = pct = 0.0
    luden = orb = horizon = bf = li = rylai = False
    cap = False
    for n in owned:
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
        rylai = rylai or it.rylai
        cap = cap or it.deathcap
    if cap:
        ap *= 1.30
    ah += trans_ah(level)
    if bf:
        ap *= 1.04
    return Stats(list(owned), ap, ah, flat, pct, luden, orb, horizon, bf, li, rylai)


def pen_mult(st: Stats, mr: float) -> float:
    mr = mr * (1.0 - st.pct_mpen) - st.flat_mpen
    return 100.0 / (100.0 + max(8.0, mr))


def dummy(minute: int, level: int) -> Tuple[float, float]:
    hp = 620 + 95 * level + 18 * minute
    mr = 32 + 1.25 * level + (0 if minute < 12 else 16)
    return hp, mr


def strike(raw: float, st: Stats, mr: float, frac: float, hf: bool) -> float:
    dmg = raw * pen_mult(st, mr)
    if hf:
        dmg *= HF_AMP
    if st.orb and frac <= 0.35:
        dmg *= 1.20
    return dmg


def burn_dps(st: Stats, hp_max: float) -> float:
    dps = 0.0
    if st.blackfire:
        dps += 20.0 + 0.02 * st.ap
    if st.liandry:
        dps += 0.02 * hp_max
    if st.names and any(ITEMS[n].ashes for n in st.names if n in ITEMS) and not st.blackfire and not st.liandry:
        dps += 5.0
    return dps


def qw_farm(
    st: Stats,
    minute: int,
    level: int,
    start_frac: float,
    allow_dh: bool,
) -> Dict[str, float]:
    """Q + W only. No R, Echo, Squall. DH if already <50% or Q/W crosses it."""
    qr, wr = skill_rank(level, "Q"), skill_rank(level, "W")
    hp_max, mr = dummy(minute, level)
    hp = start_frac * hp_max
    root = [0, 2.0, 2.25, 2.5, 2.75][max(1, qr)]
    dwell = 5.0 if st.rylai else root
    dealt = 0.0
    dh_n = 0.0
    souls = dh_souls(minute)
    hf = False

    def hit(raw: float, apply_hf: bool = False) -> None:
        nonlocal hp, dealt, dh_n, hf
        frac = hp / hp_max
        dmg = strike(raw, st, mr, frac, hf)
        hp -= dmg
        dealt += dmg
        if apply_hf and st.horizon:
            hf = True
        if allow_dh and dh_n == 0.0 and hp <= 0.50 * hp_max:
            frac2 = hp / hp_max
            dh = strike(dh_raw(st.ap, souls), st, mr, frac2, hf)
            hp -= dh
            dealt += dh
            dh_n = 1.0

    q = [0, 80, 160, 240, 320][max(1, qr)] + 0.90 * st.ap
    hit(q, apply_hf=True)
    ticks = max(1, int(dwell / 0.5))
    bdps = burn_dps(st, hp_max)
    for _ in range(ticks):
        missing = 1.0 - max(0.05, hp / hp_max)
        w_amp = 1.0 + 1.7 * min(0.7, missing)
        tick = ([0, 7, 12, 17, 22][max(1, wr)] + 0.07 * st.ap) * w_amp
        hit(tick + bdps * 0.5)

    q_base = 10.0 if qr <= 2 else 9.0
    q_cd = ah_cd(q_base, st.ah) * (0.95 if level >= 9 else 1.0)
    w_cd = ah_cd(12.0, st.ah)
    return {
        "dealt": dealt,
        "dh": dh_n,
        "hp_left": max(0.0, hp / hp_max),
        "crossed50": 1.0 if hp <= 0.50 * hp_max or dh_n else 0.0,
        "qpm": 60.0 / q_cd,
        "wpm": 60.0 / w_cd,
        "dwell": dwell,
        "ap": st.ap,
        "ah": st.ah,
    }


def q_only(st: Stats, minute: int, level: int, start_frac: float, allow_dh: bool = True) -> float:
    """One Q + DH if it enters/stays in the window. No Echo."""
    qr = max(1, skill_rank(level, "Q"))
    hp_max, mr = dummy(minute, level)
    hp = start_frac * hp_max
    raw = [0, 80, 160, 240, 320][qr] + 0.90 * st.ap
    frac = hp / hp_max
    dmg = strike(raw, st, mr, frac, False)
    hp -= dmg
    total = dmg
    if allow_dh and hp <= 0.50 * hp_max:
        hf = bool(st.horizon)
        total += strike(dh_raw(st.ap, dh_souls(minute)), st, mr, hp / hp_max, hf)
    return total


def w_only(st: Stats, minute: int, level: int, start_frac: float, allow_dh: bool = True) -> float:
    """W dwell + DH if in window. No Q, so no HF mark."""
    qr, wr = skill_rank(level, "Q"), max(1, skill_rank(level, "W"))
    hp_max, mr = dummy(minute, level)
    hp = start_frac * hp_max
    root = [0, 2.0, 2.25, 2.5, 2.75][max(1, qr)]
    dwell = 5.0 if st.rylai else root
    total = 0.0
    dh_n = 0.0
    bdps = burn_dps(st, hp_max)
    for _ in range(max(1, int(dwell / 0.5))):
        frac = hp / hp_max
        missing = 1.0 - max(0.05, frac)
        w_amp = 1.0 + 1.7 * min(0.7, missing)
        raw = ([0, 7, 12, 17, 22][wr] + 0.07 * st.ap) * w_amp + bdps * 0.5
        dmg = strike(raw, st, mr, frac, False)
        hp -= dmg
        total += dmg
        if allow_dh and dh_n == 0.0 and hp <= 0.50 * hp_max:
            total += strike(dh_raw(st.ap, dh_souls(minute)), st, mr, hp / hp_max, False)
            dh_n = 1.0
    return total


@dataclass
class Snap:
    minute: int
    items: List[str]
    gold: int
    ap: float
    ah: float
    qw45: float
    q45: float
    w45: float
    chip70: float
    crossed: float
    qpm: float
    wpm: float
    farm60: float


def run_path(path: List[str]) -> List[Snap]:
    owned: List[str] = []
    gold = 0
    snaps: List[Snap] = []
    for m in range(1, GAME_MINUTES + 1):
        gold += mid_income(m)
        owned, gold = progress(path, owned, gold, m)
        lv = level_at(m)
        st = stats_of(owned, lv)
        farm = qw_farm(st, m, lv, 0.45, True)
        chip = qw_farm(st, m, lv, 0.70, True)
        q_kit = q_only(st, m, lv, 0.45, False)
        w_kit = w_only(st, m, lv, 0.45, False)
        hp_max, mr = dummy(m, lv)
        dh = strike(dh_raw(st.ap, dh_souls(m)), st, mr, 0.45, st.horizon)
        f60 = farm["qpm"] * q_kit + farm["wpm"] * w_kit + (60.0 / DH_CD) * dh
        snaps.append(
            Snap(
                m, list(owned), gold, st.ap, st.ah,
                farm["dealt"], q_only(st, m, lv, 0.45, True), w_only(st, m, lv, 0.45, True),
                chip["dealt"], chip["crossed50"], farm["qpm"], farm["wpm"], f60,
            )
        )
    return snaps


def first(snaps: List[Snap], item: str) -> Optional[int]:
    for s in snaps:
        if item in s.items:
            return s.minute
    return None


def area(snaps: List[Snap], attr: str) -> float:
    return sum(getattr(s, attr) for s in snaps)


def short_items(items: List[str]) -> str:
    nick = {
        "Spellslinger's Shoes": "Spell",
        "Blackfire Torch": "BF",
        "Luden's Echo": "Luden",
        "Horizon Focus": "HF",
        "Cryptbloom": "Crypt",
        "Liandry's Torment": "Liandry",
        "Rylai's Crystal Scepter": "Rylai",
        "Rabadon's Deathcap": "Cap",
        "Infinity Orb": "Orb",
        "Lost Chapter": "Chapter",
        "Fated Ashes": "Ashes",
        "Fiendish Codex": "Codex",
        "Boots of Mana": "Mana",
        "Haunting Guise": "Guise",
        "Void Amethyst": "Amethyst",
        "Needlessly Large Rod": "NLR",
    }
    show = [
        n for n in items
        if n in (
            "Spellslinger's Shoes", "Blackfire Torch", "Luden's Echo",
            "Horizon Focus", "Cryptbloom", "Liandry's Torment",
            "Rylai's Crystal Scepter", "Rabadon's Deathcap", "Infinity Orb",
            "Lost Chapter", "Fated Ashes", "Boots of Mana",
        )
    ]
    if not show:
        return ", ".join(items[-3:]) if items else "(empty)"
    return " · ".join(nick.get(n, n) for n in show)


def pct(num: float, den: float) -> str:
    if den <= 1e-9:
        return "n/a"
    return f"{100.0 * (num / den - 1.0):+.1f}%"


def summarize(results: Dict[str, List[Snap]]) -> str:
    win_name = "BF → Crypt → HF"
    a = results[win_name]
    L: List[str] = []
    L.append("=" * 78)
    L.append("MORGANA DH FARM — Q + W  (WR 7.2e)")
    L.append("Bỏ burst: không R, Echo, Squall, Stormsurge. Không khóa Luden.")
    L.append("Mỗi Q và W là cửa DH (<50%). Mid gold. W-max. Spell lúc 10:00.")
    L.append("=" * 78)
    L.append("")
    L.append("4 Ô")
    L.append("-" * 78)
    L.append("  Client : Tốc Chiến 7.2e. DH 35+11×soul+5% AP, <50%, 35s CD.")
    L.append("  Role   : mid. Farm soul bằng Q/W chip → execute. Không jungle camp.")
    L.append("  Cặp    : BF→HF→Crypt vs BF→Liandry→Rylai vs Luden→HF→Crypt")
    L.append("           vs BF→Orb→Cap (burst path, đối chứng).")
    L.append("  Metric : 60s farm @45% = QPM×Q + WPM×W + DH mỗi 35s. Q-only / W-only.")
    L.append("           Chip 70% Q+W không R. Tổng phút 1–20. Không combo burst.")
    L.append("")
    L.append("  DH CD 35s không giảm bởi AH. AH để Q/W chip vào cửa thường hơn.")
    L.append("  HF: Q apply, W ticks +10%. W amp mạnh khi thiếu máu (cửa DH).")
    L.append("")
    L.append("-" * 78)
    L.append("BUILD ORDER — BF → Spell → Crypt → HF")
    L.append("-" * 78)
    for label, item in (
        ("Chapter", "Lost Chapter"),
        ("Ashes", "Fated Ashes"),
        ("BF", "Blackfire Torch"),
        ("Spell", "Spellslinger's Shoes"),
        ("HF", "Horizon Focus"),
        ("Crypt", "Cryptbloom"),
    ):
        m = first(a, item)
        L.append(f"  {label:<8} phút {m if m is not None else '—'}")
    L.append("  1) Tome → Boots of Speed → Boots of Mana → Lost Chapter")
    L.append("  2) Fated Ashes → Blackfire Torch")
    L.append("  3) Spellslinger's Shoes (T3 mở 10:00)")
    L.append("  4) Cryptbloom (Void Amethyst + Codex + Tome) — pen cho mọi Q/W/DH")
    L.append("  5) Horizon Focus (2× Codex + Tome) — Q apply, W +10%")
    L.append("  HF trước Crypt: −1.4% Σ60s (AH sớm, pen muộn).")
    L.append("")
    L.append("-" * 78)
    L.append("Q+W farm 60s @45%  (QPM×Q + WPM×W + DH/35s)  — metric chính")
    L.append("-" * 78)
    L.append(f"  {'path':<24} {'Σ1-20':>8} {'m8':>7} {'m12':>7} {'m18':>7} {'m20':>7}")
    ranked = sorted(results, key=lambda n: area(results[n], "farm60"), reverse=True)
    best = area(results[ranked[0]], "farm60")
    for name in ranked:
        s = results[name]
        L.append(
            f"  {name:<24} {area(s, 'farm60'):8.0f} {s[7].farm60:7.0f} "
            f"{s[11].farm60:7.0f} {s[17].farm60:7.0f} {s[19].farm60:7.0f}  "
            f"{pct(area(s, 'farm60'), best)}"
        )
    L.append("")
    L.append("-" * 78)
    L.append("Q-only / W-only @45%  — từng skill là cửa DH")
    L.append("-" * 78)
    for name in ranked:
        s = results[name]
        L.append(
            f"  {name:<24} ΣQ {area(s, 'q45'):7.0f}  ΣW {area(s, 'w45'):7.0f}  "
            f"QPM@12 {s[11].qpm:.2f}  WPM@12 {s[11].wpm:.2f}"
        )
    L.append("")
    L.append("-" * 78)
    L.append("CHIP 70% bằng Q+W (không R) — vào cửa <50%?")
    L.append("-" * 78)
    for name in ranked:
        s = results[name]
        n_cross = sum(1 for x in s if x.crossed)
        L.append(
            f"  {name:<24} vào cửa {n_cross}/20 phút  "
            f"chip@8 {s[7].chip70:.0f}  @12 {s[11].chip70:.0f}  "
            f"crossed@12 {'yes' if s[11].crossed else 'no'}"
        )
    L.append("")
    L.append("-" * 78)
    L.append("SNAPSHOT phút 8 / 12 / 18 / 20")
    L.append("-" * 78)
    for m in (8, 12, 18, 20):
        L.append(f"  phút {m}")
        for name in ranked:
            s = results[name][m - 1]
            L.append(
                f"    {name:<24} 60s {s.farm60:6.0f}  QW {s.qw45:5.0f}  "
                f"AP {s.ap:5.0f} AH {s.ah:4.0f}  {short_items(s.items)}"
            )
    L.append("")
    lud = results["Luden → HF → Crypt"]
    ryl = results["BF → Liandry → Rylai"]
    orb = results["BF → Orb → Cap"]
    win = ranked[0]
    wsnaps = results[win]
    L.append("-" * 78)
    L.append("VERDICT — farm DH, không burst")
    L.append("-" * 78)
    L.append(f"  Winner 60s farm: {win}")
    if win == "BF → HF → Crypt":
        L.append("  Build: Blackfire → Spellslinger → Horizon Focus → Cryptbloom.")
    elif win == "BF → Crypt → HF":
        L.append("  Build: Blackfire → Spellslinger → Cryptbloom → Horizon Focus.")
    elif win.startswith("BF → Liandry"):
        L.append("  Build: Blackfire → Spellslinger → Liandry → Rylai (W dwell 5s).")
    else:
        L.append(f"  Build order: xem spike {win}.")
    L.append(
        f"  vs Luden core  {pct(area(wsnaps, 'farm60'), area(lud, 'farm60'))} Σ60s. "
        f"Echo không đếm (burst). Không bắt Luden."
    )
    L.append(
        f"  vs Liandry-Rylai {pct(area(wsnaps, 'farm60'), area(ryl, 'farm60'))}."
    )
    L.append(
        f"  vs Orb-Cap burst {pct(area(wsnaps, 'farm60'), area(orb, 'farm60'))}. "
        f"Orb tắt @45%. Cap/NLR 0 AH — ít Q/W hơn."
    )
    L.append("  Đừng Stormsurge. Đừng tối ưu 1 combo R. Q và W là cửa DH; AH để spam khi <50%.")
    L.append("=" * 78)
    return "\n".join(L)


def export_json(results: Dict[str, List[Snap]], path: str) -> None:
    def pack(s: Snap) -> dict:
        return {
            "minute": s.minute,
            "items": s.items,
            "ap": round(s.ap, 1),
            "ah": round(s.ah, 1),
            "qw45": round(s.qw45, 1),
            "q45": round(s.q45, 1),
            "w45": round(s.w45, 1),
            "farm60": round(s.farm60, 1),
            "crossed": bool(s.crossed),
        }

    payload = {
        "meta": {
            "patch": "7.2e",
            "burst": False,
            "luden_required": False,
            "metric": "Q+W+DH at 45% HP, mid gold minutes 1-20",
        },
        "areas": {n: round(area(s, "farm60"), 1) for n, s in results.items()},
        "spikes": {
            n: {
                "BF": first(s, "Blackfire Torch"),
                "Luden": first(s, "Luden's Echo"),
                "Spell": first(s, "Spellslinger's Shoes"),
                "HF": first(s, "Horizon Focus"),
                "Crypt": first(s, "Cryptbloom"),
            }
            for n, s in results.items()
        },
        "minute_12": {n: pack(s[11]) for n, s in results.items()},
        "minute_18": {n: pack(s[17]) for n, s in results.items()},
        "minute_20": {n: pack(s[19]) for n, s in results.items()},
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def self_check(results: Dict[str, List[Snap]]) -> None:
    farm = results["BF → Crypt → HF"]
    lud = results["Luden → HF → Crypt"]
    orb = results["BF → Orb → Cap"]
    assert first(farm, "Blackfire Torch") is not None
    assert first(farm, "Luden's Echo") is None
    assert first(farm, "Cryptbloom") is not None
    assert first(farm, "Horizon Focus") is not None
    assert first(farm, "Cryptbloom") <= first(farm, "Horizon Focus")
    assert first(farm, "Spellslinger's Shoes") >= T3_BOOTS_MINUTE
    assert area(farm, "farm60") > area(orb, "farm60")
    assert area(farm, "farm60") >= area(lud, "farm60") * 0.98
    st = stats_of(["Blackfire Torch", "Spellslinger's Shoes"], 9)
    q = qw_farm(st, 8, 9, 0.45, True)
    assert q["dh"] == 1.0
    # Burst pieces must not be in the recommended path.
    assert "Stormsurge" not in farm[-1].items
    print("self-check OK")


def main() -> None:
    results = {n: run_path(p) for n, p in PATHS.items()}
    self_check(results)
    report = summarize(results)
    print(report)
    with open(os.path.join(OUT_DIR, "dh_farm_report.txt"), "w", encoding="utf-8") as f:
        f.write(report + "\n")
    export_json(results, os.path.join(OUT_DIR, "dh_farm.json"))
    print(f"\nWrote {OUT_DIR}/dh_farm_report.txt")


if __name__ == "__main__":
    main()
