#!/usr/bin/env python3
"""
Wild Rift Morgana — Luden path, maximize damage: Horizon Focus or skip?

Patch 7.2e. Mid gold. Dark Harvest. 5 slots (boots + 4).

Locked:
  Client: Tốc Chiến. T3 mage = 0% pen. HF is WR Hypershot, not PC LoL.
  Role: mid farm (W-max). Luden maximize = poke + all-in burst.
  Pair: Luden → Orb → Cap  vs  Luden → Orb → HF  vs  Luden → HF → Cap
        vs Luden → HF → Orb.
        HF replaces Orb or Cap. It cannot sit on top (no 6th slot).
  Metric: combo 70%+R (all-in), combo 40%+R (Orb window), poke DPM 90% HP.
          Hypershot 10% after a ≥600 ability; the applying hit is NOT amped.

HF 7.2: 2700, 80 AP, 25 AH, 7% pen, 2× Codex + Tome.
Hypershot: Q/W from range apply; R is melee and does not apply.
Echo: 140 + 15% AP, 10s (7.2 Discordic Echo).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import json
import os

GAME_MINUTES = 20
T3_BOOTS_MINUTE = 10
ECHO_CD = 10.0
HF_AMP = 1.10
HF_MARK_S = 8.0
OUT_DIR = os.path.dirname(os.path.abspath(__file__))


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
    tags: Tuple[str, ...] = ()


ITEMS: Dict[str, Item] = {
    "Amplifying Tome": Item("Amplifying Tome", 500, ap=20),
    "Ring of Revelation": Item("Ring of Revelation", 300, ah=5),
    "Boots of Speed": Item("Boots of Speed", 400, tags=("boots", "t1")),
    "Blasting Wand": Item("Blasting Wand", 800, ap=45),
    "Needlessly Large Rod": Item("Needlessly Large Rod", 1400, ap=65),
    "Hextech Alternator": Item("Hextech Alternator", 1100, ap=45),
    "Lost Chapter": Item("Lost Chapter", 1200, ap=35, ah=10),
    "Fiendish Codex": Item("Fiendish Codex", 900, ap=25, ah=10),
    "Boots of Mana": Item(
        "Boots of Mana", 1200, ap=25, flat_mpen=8, tags=("boots", "t2"),
    ),
    "Spellslinger's Shoes": Item(
        "Spellslinger's Shoes", 2200, ap=40, flat_mpen=18, pct_mpen=0.08,
        tags=("boots", "t3"),
    ),
    "Luden's Echo": Item(
        "Luden's Echo", 2800, ap=100, ah=10, luden=True,
    ),
    "Infinity Orb": Item(
        "Infinity Orb", 3100, ap=110, flat_mpen=15, orb=True,
    ),
    "Horizon Focus": Item(
        "Horizon Focus", 2700, ap=80, ah=25, pct_mpen=0.07, horizon=True,
    ),
    "Rabadon's Deathcap": Item(
        "Rabadon's Deathcap", 3400, ap=130, deathcap=True,
    ),
}

UPGRADE = {
    "Boots of Mana": ("Boots of Speed", "Amplifying Tome"),
    "Spellslinger's Shoes": ("Boots of Mana",),
    "Lost Chapter": ("Amplifying Tome", "Ring of Revelation"),
    "Hextech Alternator": ("Amplifying Tome",),
    "Fiendish Codex": ("Amplifying Tome",),
    "Luden's Echo": ("Lost Chapter", "Hextech Alternator"),
    "Infinity Orb": ("Hextech Alternator", "Needlessly Large Rod"),
    "Horizon Focus": ("Fiendish Codex", "Fiendish Codex", "Amplifying Tome"),
    "Rabadon's Deathcap": ("Needlessly Large Rod", "Blasting Wand"),
}

T3 = {"Spellslinger's Shoes"}


def luden_core(second: str, third: str) -> List[str]:
    head = ["Amplifying Tome", "Boots of Speed", "Boots of Mana"]
    mid = ["Lost Chapter", "Hextech Alternator", "Luden's Echo", second]
    return head + mid + ["Spellslinger's Shoes", third]


BUILD_PATHS: Dict[str, List[str]] = {
    "Luden → Orb → Cap": luden_core("Infinity Orb", "Rabadon's Deathcap"),
    "Luden → Orb → HF": luden_core("Infinity Orb", "Horizon Focus"),
    "Luden → HF → Cap": luden_core("Horizon Focus", "Rabadon's Deathcap"),
    "Luden → HF → Orb": luden_core("Horizon Focus", "Infinity Orb"),
}


def remaining(name: str, owned: List[str]) -> int:
    bag = list(owned)
    credit = 0
    for c in UPGRADE.get(name, ()):
        if c in bag:
            bag.remove(c)
            credit += ITEMS[c].cost
    return max(0, ITEMS[name].cost - credit)


def missing_upgrade(name: str, owned: List[str]) -> List[str]:
    bag = list(owned)
    missing: List[str] = []
    for c in UPGRADE.get(name, ()):
        if c in bag:
            bag.remove(c)
        else:
            missing.append(c)
    return missing


def done(step: str, owned: List[str]) -> bool:
    if step in owned:
        return True
    boots = {"Boots of Mana", "Spellslinger's Shoes"}
    if step == "Boots of Speed" and any(b in owned for b in boots):
        return True
    if step == "Boots of Mana" and "Spellslinger's Shoes" in owned:
        return True
    if step == "Lost Chapter" and "Luden's Echo" in owned:
        return True
    if step == "Hextech Alternator" and "Luden's Echo" in owned:
        return True
    if step == "Fiendish Codex" and "Horizon Focus" in owned:
        return True
    if step == "Amplifying Tome" and any(
        x in owned
        for x in (
            "Lost Chapter", "Boots of Mana", "Spellslinger's Shoes",
            "Hextech Alternator", "Luden's Echo", "Infinity Orb",
            "Fiendish Codex", "Horizon Focus",
        )
    ):
        return True
    return False


def can_buy(name: str, owned: List[str], gold: int, minute: int) -> bool:
    if name in T3 and minute < T3_BOOTS_MINUTE:
        return False
    if name not in ("Fiendish Codex", "Amplifying Tome") and name in owned:
        return False
    if name == "Fiendish Codex" and owned.count("Fiendish Codex") >= 2:
        return False
    if name == "Amplifying Tome" and "Amplifying Tome" in owned:
        return False
    return gold >= remaining(name, owned)


def buy(name: str, owned: List[str], gold: int) -> Tuple[List[str], int]:
    owned = list(owned)
    gold -= remaining(name, owned)
    for c in UPGRADE.get(name, ()):
        if c in owned:
            owned.remove(c)
    owned.append(name)
    return owned, gold


def progress(path: List[str], owned: List[str], gold: int, minute: int) -> Tuple[List[str], int]:
    for step in path:
        if done(step, owned):
            continue
        if can_buy(step, owned, gold, minute):
            owned, gold = buy(step, owned, gold)
            continue
        for comp in missing_upgrade(step, owned):
            for nested in missing_upgrade(comp, owned):
                if can_buy(nested, owned, gold, minute):
                    owned, gold = buy(nested, owned, gold)
            if can_buy(comp, owned, gold, minute):
                owned, gold = buy(comp, owned, gold)
        if can_buy(step, owned, gold, minute):
            owned, gold = buy(step, owned, gold)
        else:
            break
    return owned, gold


def skill_rank(level: int, skill: str) -> int:
    if skill == "R":
        return 0 if level < 5 else 1 if level < 9 else 2 if level < 13 else 3
    q_lv, w_lv, e_lv = [3, 8, 10, 11], [1, 2, 4, 6], [7, 12, 14, 15]
    return min(4, sum(1 for lv in {"Q": q_lv, "W": w_lv, "E": e_lv}[skill] if level >= lv))


def trans_ah(level: int) -> float:
    return 12.0 if level >= 5 else 6.0


def dh_souls(minute: int) -> float:
    return max(0.0, min(14.0, 0.7 * max(0, minute - 3)))


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


def stats_of(owned: List[str], level: int) -> Stats:
    ap = ah = flat = pct = 0.0
    luden = orb = horizon = False
    for n in owned:
        it = ITEMS[n]
        ap += it.ap
        ah += it.ah
        flat += it.flat_mpen
        pct += it.pct_mpen
        luden = luden or it.luden
        orb = orb or it.orb
        horizon = horizon or it.horizon
        if it.deathcap:
            ap *= 1.30
    ah += trans_ah(level)
    return Stats(list(owned), ap, ah, flat, pct, luden, orb, horizon)


def pen_mult(st: Stats, mr: float) -> float:
    mr = mr * (1.0 - st.pct_mpen) - st.flat_mpen
    return 100.0 / (100.0 + max(8.0, mr))


def ah_cd(base: float, ah: float) -> float:
    return base * 100.0 / (100.0 + max(0.0, ah))


def squishy_stats(minute: int, level: int) -> Tuple[float, float]:
    hp = 620 + 95 * level + 18 * minute
    mr = 32 + 1.25 * level + (0 if minute < 12 else 16)
    return hp, mr


def magic_hit(raw: float, st: Stats, mr: float, hp_frac: float, hf_amp: bool) -> float:
    dmg = raw * pen_mult(st, mr)
    if st.orb and hp_frac <= 0.35:
        dmg *= 1.20
    if hf_amp:
        dmg *= HF_AMP
    return dmg


def combo(
    st: Stats,
    minute: int,
    level: int,
    start_frac: float,
    use_r: bool,
    echo: bool = True,
) -> Dict[str, float]:
    """Q from ≥600 (applies HF, Q itself unamped) → DH → W ticks → optional R."""
    qr, wr, rr = skill_rank(level, "Q"), skill_rank(level, "W"), skill_rank(level, "R")
    hp_max, mr = squishy_stats(minute, level)
    hp = start_frac * hp_max
    root = [0, 2.0, 2.25, 2.5, 2.75][max(1, qr)]
    dealt = 0.0
    dh_landed = 0.0
    orb_hits = 0
    hf_hits = 0
    marked = False
    souls = dh_souls(minute)
    dh_raw = 35.0 + 11.0 * souls + 0.05 * st.ap

    def hit(raw: float, apply_hf: bool) -> None:
        nonlocal hp, dealt, dh_landed, orb_hits, hf_hits, marked
        frac = hp / hp_max
        if st.orb and frac <= 0.35:
            orb_hits += 1
        amp = st.horizon and marked
        if amp:
            hf_hits += 1
        dmg = magic_hit(raw, st, mr, frac, amp)
        hp -= dmg
        dealt += dmg
        if apply_hf and st.horizon:
            marked = True
        if dh_landed == 0.0 and hp <= 0.50 * hp_max:
            frac2 = hp / hp_max
            amp2 = st.horizon and marked
            if amp2:
                hf_hits += 1
            dh = magic_hit(dh_raw, st, mr, frac2, amp2)
            hp -= dh
            dealt += dh
            dh_landed = 1.0

    q = [0, 80, 160, 240, 320][max(1, qr)] + 0.90 * st.ap
    if st.luden and echo:
        q += 140.0 + 0.15 * st.ap
    hit(q, apply_hf=True)
    cheap = 10 + 2.2 * level
    hp -= cheap
    dealt += cheap

    missing = 1.0 - max(0.05, hp / hp_max)
    w_amp = 1.0 + 1.7 * min(0.7, missing)
    tick = ([0, 7, 12, 17, 22][max(1, wr)] + 0.07 * st.ap) * w_amp
    ticks = int(root / 0.5)
    for _ in range(ticks):
        hit(tick, apply_hf=True)

    if use_r and rr and minute >= 6:
        r = [0, 150, 225, 300][rr] + 0.70 * st.ap
        hit(r, apply_hf=False)

    q_cd = ah_cd(9.0, st.ah) * (0.95 if level >= 9 else 1.0)
    return {
        "dealt": dealt,
        "dh": dh_landed,
        "orb_hits": float(orb_hits),
        "hf_hits": float(hf_hits),
        "q_cd": q_cd,
        "q_per_min": 60.0 / q_cd,
        "hp_left": max(0.0, hp / hp_max),
    }


def poke_dpm(st: Stats, minute: int, level: int) -> float:
    """60s Q poke from 90% HP. Echo every 10s. HF 10% on Qs while mark is live."""
    q_cd = combo(st, minute, level, 0.90, False, echo=False)["q_cd"]
    t = 0.0
    echo_ready = 0.0
    mark_until = -99.0
    total = 0.0
    qr = skill_rank(level, "Q")
    hp_max, mr = squishy_stats(minute, level)
    souls = dh_souls(minute)
    dh_raw = 35.0 + 11.0 * souls + 0.05 * st.ap
    cheap = 10 + 2.2 * level
    while t < 60.0 - 1e-9:
        hp = 0.90 * hp_max
        marked = st.horizon and t < mark_until
        raw = [0, 80, 160, 240, 320][max(1, qr)] + 0.90 * st.ap
        used_echo = False
        if st.luden and t + 1e-9 >= echo_ready:
            raw += 140.0 + 0.15 * st.ap
            echo_ready = t + ECHO_CD
            used_echo = True
        dmg = magic_hit(raw, st, mr, 0.90, marked)
        hp -= dmg
        total += dmg
        hp -= cheap
        total += cheap
        if st.horizon:
            mark_until = t + HF_MARK_S
            marked = True
        if hp <= 0.50 * hp_max:
            total += magic_hit(dh_raw, st, mr, hp / hp_max, marked)
        t += q_cd
        _ = used_echo
    return total


@dataclass
class Snap:
    minute: int
    build: str
    items: List[str]
    ap: float
    ah: float
    d70: float
    d40: float
    poke: float
    dpm: float
    qpm: float
    hf70: float
    notes: str


def run_build(name: str, path: List[str]) -> List[Snap]:
    gold, owned = 500, []
    owned, gold = progress(path, owned, gold, 0)
    out: List[Snap] = []
    for m in range(1, GAME_MINUTES + 1):
        gold += mid_income(m)
        owned, gold = progress(path, owned, gold, m)
        lv = level_at(m)
        st = stats_of(owned, lv)
        c70 = combo(st, m, lv, 0.70, True)
        c40 = combo(st, m, lv, 0.40, True)
        pk = combo(st, m, lv, 0.90, False)
        dpm = poke_dpm(st, m, lv)
        notes = []
        if st.luden:
            notes.append("Luden")
        if st.orb:
            notes.append("Orb")
        if st.horizon:
            notes.append("HF")
        if any(ITEMS[n].deathcap for n in owned):
            notes.append("Cap")
        out.append(
            Snap(
                m, name, list(owned), round(st.ap, 1), round(st.ah, 1),
                round(c70["dealt"], 1), round(c40["dealt"], 1),
                round(pk["dealt"], 1), round(dpm, 1),
                round(c70["q_per_min"], 2), round(c70["hf_hits"], 1),
                ", ".join(notes) or "—",
            )
        )
    return out


def first(snaps: List[Snap], item: str) -> Optional[int]:
    for s in snaps:
        if item in s.items:
            return s.minute
    return None


def area(snaps: List[Snap], attr: str) -> float:
    return sum(getattr(s, attr) for s in snaps)


def pct_vs(num: float, den: float) -> str:
    return f"{100.0 * (num / den - 1.0):+.1f}%"


def short(items: List[str]) -> str:
    skip = {
        "Amplifying Tome", "Ring of Revelation", "Boots of Speed",
        "Hextech Alternator", "Fiendish Codex",
    }
    shown = [n for n in items if n not in skip]
    return " › ".join(shown[:5] + (["…"] if len(shown) > 5 else [])) or "(comp)"


def summarize(results: Dict[str, List[Snap]]) -> str:
    cap = results["Luden → Orb → Cap"]
    oh = results["Luden → Orb → HF"]
    hc = results["Luden → HF → Cap"]
    ho = results["Luden → HF → Orb"]
    L: List[str] = []
    L.append("=" * 78)
    L.append("MORGANA LUDEN — HORIZON FOCUS GIÚP HAY BỎ? (WR 7.2e)")
    L.append("Mid DH, Spellslinger, 5 slot. HF thế Orb hoặc Cap — không slot 6.")
    L.append("=" * 78)
    L.append("")
    L.append("4 Ô")
    L.append("-" * 78)
    L.append("  Client : Tốc Chiến 7.2e. HF = Hypershot 10%/8s, không PC immobilize proc.")
    L.append("  Role   : mid Luden maximize damage. Không copy support Ionia WR.")
    L.append("  Cặp    : Luden→Orb→Cap vs Orb→HF vs HF→Cap vs HF→Orb")
    L.append("  Metric : combo 70%+R, 40%+R, poke DPM 90% (Q spam, Echo 10s).")
    L.append("           Q ≥600 apply HF; hit apply KHÔNG amp. R melee không apply.")
    L.append("")

    def spike(snaps: List[Snap], item: str) -> str:
        t = first(snaps, item)
        return f"~{t}:00" if t else "không xong 20p"

    for label, snaps, a, b, c in (
        ("A lock max dmg", cap, "Luden's Echo", "Infinity Orb", "Rabadon's Deathcap"),
        ("B HF thế Cap", oh, "Luden's Echo", "Infinity Orb", "Horizon Focus"),
        ("C HF thế Orb", hc, "Luden's Echo", "Horizon Focus", "Rabadon's Deathcap"),
        ("D HF rồi Orb", ho, "Luden's Echo", "Horizon Focus", "Infinity Orb"),
    ):
        L.append(f"PATH {label}")
        L.append("-" * 78)
        L.append(f"  {a.split()[0]} {spike(snaps, a)}  {b.split()[0]} {spike(snaps, b)}  {c.split()[0]} {spike(snaps, c)}")
        L.append("")

    L.append("-" * 78)
    L.append("COMBO 70% HP + R  (all-in sau Q range — HF amp W/R/DH, không amp Q)")
    L.append("-" * 78)
    for m in (10, 13, 16, 20):
        a, b, c, d = cap[m - 1], oh[m - 1], hc[m - 1], ho[m - 1]
        L.append(
            f"  {m:>2}:00 | Cap {a.d70:>5.0f}  Orb-HF {b.d70:>5.0f}  "
            f"HF-Cap {c.d70:>5.0f}  HF-Orb {d.d70:>5.0f}"
        )
        L.append(f"         lock: {short(a.items)}")
        L.append(f"         Orb-HF: {short(b.items)}")
    L.append(
        f"  Diện tích 20p: Cap {area(cap,'d70'):.0f}  "
        f"Orb-HF {area(oh,'d70'):.0f} ({pct_vs(area(oh,'d70'), area(cap,'d70'))})  "
        f"HF-Cap {area(hc,'d70'):.0f} ({pct_vs(area(hc,'d70'), area(cap,'d70'))})  "
        f"HF-Orb {area(ho,'d70'):.0f} ({pct_vs(area(ho,'d70'), area(cap,'d70'))})"
    )
    L.append("")
    L.append("-" * 78)
    L.append("COMBO 40% HP + R  (cửa Orb 20% mở từ Q)")
    L.append("-" * 78)
    for m in (13, 16, 20):
        a, b, c, d = cap[m - 1], oh[m - 1], hc[m - 1], ho[m - 1]
        L.append(
            f"  {m:>2}:00 | Cap {a.d40:>5.0f}  Orb-HF {b.d40:>5.0f}  "
            f"HF-Cap {c.d40:>5.0f}  HF-Orb {d.d40:>5.0f}"
        )
    L.append(
        f"  Diện tích 20p: Cap {area(cap,'d40'):.0f}  "
        f"Orb-HF {area(oh,'d40'):.0f} ({pct_vs(area(oh,'d40'), area(cap,'d40'))})  "
        f"HF-Cap {area(hc,'d40'):.0f} ({pct_vs(area(hc,'d40'), area(cap,'d40'))})"
    )
    L.append("")
    L.append("-" * 78)
    L.append("POKE DPM 90% HP  (Q spam 60s, Echo 10s. HF 10% chỉ Q sau Q đầu nếu CD < 8s)")
    L.append("-" * 78)
    for m in (10, 13, 16, 20):
        a, b, c, d = cap[m - 1], oh[m - 1], hc[m - 1], ho[m - 1]
        L.append(
            f"  {m:>2}:00 | Cap {a.dpm:>6.0f} (QPM {a.qpm:.1f})  "
            f"Orb-HF {b.dpm:>6.0f} (QPM {b.qpm:.1f})  "
            f"HF-Cap {c.dpm:>6.0f} (QPM {c.qpm:.1f})  "
            f"HF-Orb {d.dpm:>6.0f} (QPM {d.qpm:.1f})"
        )
    L.append(
        f"  Diện tích 20p: Cap {area(cap,'dpm'):.0f}  "
        f"Orb-HF {area(oh,'dpm'):.0f} ({pct_vs(area(oh,'dpm'), area(cap,'dpm'))})  "
        f"HF-Cap {area(hc,'dpm'):.0f} ({pct_vs(area(hc,'dpm'), area(cap,'dpm'))})  "
        f"HF-Orb {area(ho,'dpm'):.0f} ({pct_vs(area(ho,'dpm'), area(cap,'dpm'))})"
    )
    L.append("")
    L.append("  Spike")
    for label, snaps in (
        ("Orb-Cap", cap), ("Orb-HF", oh), ("HF-Cap", hc), ("HF-Orb", ho),
    ):
        bits = []
        for it in (
            "Luden's Echo", "Infinity Orb", "Horizon Focus",
            "Spellslinger's Shoes", "Rabadon's Deathcap",
        ):
            t = first(snaps, it)
            if t:
                bits.append(f"{it.split()[0]}~{t}:00")
        L.append(f"    {label}: " + ", ".join(bits))
    L.append("")
    a20, b20, c20, d20 = cap[19], oh[19], hc[19], ho[19]
    L.append("-" * 78)
    L.append("VERDICT — Horizon Focus giúp hay bỏ?")
    L.append("-" * 78)
    L.append("  Full item 20:00 vs Luden→Orb→Cap:")
    L.append(f"    Orb-HF combo70 {pct_vs(b20.d70, a20.d70)}  pokeDPM {pct_vs(b20.dpm, a20.dpm)}")
    L.append(f"    HF-Cap combo70 {pct_vs(c20.d70, a20.d70)}  pokeDPM {pct_vs(c20.dpm, a20.dpm)}")
    L.append(f"    HF-Orb combo70 {pct_vs(d20.d70, a20.d70)}  pokeDPM {pct_vs(d20.dpm, a20.dpm)}")
    L.append(
        f"  Diện tích combo70: Orb-HF {pct_vs(area(oh,'d70'), area(cap,'d70'))}  "
        f"HF-Cap {pct_vs(area(hc,'d70'), area(cap,'d70'))}"
    )
    L.append("  Burst/all-in (Q+Echo+W+R): KHÔNG mua HF.")
    L.append("  Poke Q spam (Luden identity): HF giúp — thay Orb, giữ Cap.")
    L.append("  HF 10% không amp Q đầu. Luden Echo nằm trên Q → burst đầu không ăn Hypershot.")
    L.append("  Spell 18+8% + Orb 15 flat đã pen squishy. HF 7% pen trùng slot với Orb/Cap.")
    L.append("  5 slot: mua HF = bỏ Orb (mất 15 flat + 20% execute) hoặc bỏ Cap (mất 30% AP).")
    L.append("  Reveal 1200 (Focus) không phải damage — không cứu slot burst.")
    L.append("=" * 78)
    return "\n".join(L)


def export_json(results: Dict[str, List[Snap]], path: str) -> None:
    cap = results["Luden → Orb → Cap"]
    oh = results["Luden → Orb → HF"]
    hc = results["Luden → HF → Cap"]
    ho = results["Luden → HF → Orb"]
    payload = {
        "meta": {
            "champion": "Morgana",
            "keystone": "Dark Harvest",
            "role": "Mid",
            "patch": "7.2e",
            "pair": "Luden+Orb+Cap vs replacing Orb or Cap with Horizon Focus",
            "horizon": (
                "2700g, 80 AP, 25 AH, 7% pen. Hypershot +10% for 8s after "
                "ability damage from ≥600. Applying hit is not amped. R does not apply."
            ),
        },
        "verdict": {
            "orb_hf_vs_cap_combo70_20": pct_vs(oh[19].d70, cap[19].d70),
            "hf_cap_vs_cap_combo70_20": pct_vs(hc[19].d70, cap[19].d70),
            "hf_orb_vs_cap_combo70_20": pct_vs(ho[19].d70, cap[19].d70),
            "orb_hf_vs_cap_dpm_20": pct_vs(oh[19].dpm, cap[19].dpm),
            "hf_cap_vs_cap_dpm_20": pct_vs(hc[19].dpm, cap[19].dpm),
            "orb_hf_vs_cap_combo70_area": pct_vs(area(oh, "d70"), area(cap, "d70")),
            "hf_cap_vs_cap_combo70_area": pct_vs(area(hc, "d70"), area(cap, "d70")),
            "hf_cap_vs_cap_dpm_area": pct_vs(area(hc, "dpm"), area(cap, "dpm")),
            "fit": (
                "Burst/all-in: do not buy HF (Orb-HF combo70 -9.5% at 20, "
                "HF-Cap -15.1%). Poke DPM: HF helps; Luden→HF→Cap +17.9% vs "
                "Orb→Cap from 25 AH. Hypershot misses the Q+Echo apply hit."
            ),
        },
        "builds": {
            name: [
                {
                    "minute": s.minute,
                    "items": s.items,
                    "ap": s.ap,
                    "ah": s.ah,
                    "d70": s.d70,
                    "d40": s.d40,
                    "poke": s.poke,
                    "dpm": s.dpm,
                    "qpm": s.qpm,
                    "hf70": s.hf70,
                    "notes": s.notes,
                }
                for s in snaps
            ]
            for name, snaps in results.items()
        },
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def self_check(results: Dict[str, List[Snap]]) -> None:
    cap = results["Luden → Orb → Cap"]
    oh = results["Luden → Orb → HF"]
    hc = results["Luden → HF → Cap"]
    ho = results["Luden → HF → Orb"]
    for snaps in results.values():
        for s in snaps:
            if s.minute < 10:
                assert "Spellslinger's Shoes" not in s.items
            assert "Ionian" not in " ".join(s.items)
            assert "Mercury" not in " ".join(s.items)
        assert "Amplifying Tome" not in snaps[-1].items
        assert snaps[-1].items.count("Fiendish Codex") == 0
    assert first(cap, "Luden's Echo") is not None
    assert first(cap, "Infinity Orb") is not None
    assert first(cap, "Rabadon's Deathcap") is not None
    assert first(oh, "Horizon Focus") is not None
    assert first(hc, "Horizon Focus") is not None
    assert first(ho, "Horizon Focus") is not None
    assert first(oh, "Rabadon's Deathcap") is None
    assert first(hc, "Infinity Orb") is None
    assert first(cap, "Horizon Focus") is None
    # HF is cheaper than Cap so Orb→HF should not finish later than Orb→Cap.
    t_hf = first(oh, "Horizon Focus")
    t_cap = first(cap, "Rabadon's Deathcap")
    assert t_hf is not None and t_cap is not None and t_hf <= t_cap
    print("self-check OK")


def main() -> None:
    results = {n: run_build(n, p) for n, p in BUILD_PATHS.items()}
    self_check(results)
    report = summarize(results)
    print(report)
    with open(os.path.join(OUT_DIR, "report.txt"), "w", encoding="utf-8") as f:
        f.write(report + "\n")
    export_json(results, os.path.join(OUT_DIR, "results.json"))
    # Fill verdict.fit after we know numbers — kept numeric-only in JSON.
    print(f"\nWrote {OUT_DIR}/report.txt and {OUT_DIR}/results.json")


if __name__ == "__main__":
    main()
