#!/usr/bin/env python3
"""
Wild Rift Viktor mid — magic-pen/burst vs Blackfire + Liandry
Patch 7.2e. Average game 20 minutes.

Locked:
  Client: Tốc Chiến (not PC). T3 mage items lost 7% pen.
  Role: mid (E-max waveclear). Not jungle / support.
  Pair: Luden → Infinity Orb → Cap
        vs Blackfire → Liandry → Void
        vs Blackfire → Infinity Orb → Cap  (hybrid: burn + execute, no Liandry)
  Metric: E poke (full HP) vs 5.5s all-in (R storm) on squishy AND tank.

Diamond+ (riftpatchnotes, 2026-09-06) has both cores. That WR is not
the metric — it is unconditioned vs the whole mid pool.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import json
import os

GAME_MINUTES = 20
T3_BOOTS_MINUTE = 10
OUT_DIR = os.path.dirname(os.path.abspath(__file__))


def mid_income(minute: int) -> int:
    """CS + plates + Big Bully after Mana boots. No sickle."""
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
    hp: float = 0
    mana: float = 0
    mana_regen_pct: float = 0
    flat_mpen: float = 0
    pct_mpen: float = 0
    deathcap: bool = False
    luden: bool = False
    orb: bool = False
    blackfire: bool = False
    liandry: bool = False
    ashes: bool = False
    guise: bool = False
    tags: Tuple[str, ...] = ()


ITEMS: Dict[str, Item] = {
    "Amplifying Tome": Item("Amplifying Tome", 500, ap=20),
    "Ring of Revelation": Item("Ring of Revelation", 300, ah=5),
    "Boots of Speed": Item("Boots of Speed", 400, tags=("boots", "t1")),
    "Ruby Crystal": Item("Ruby Crystal", 500, hp=200),
    "Blasting Wand": Item("Blasting Wand", 800, ap=45),
    "Needlessly Large Rod": Item("Needlessly Large Rod", 1400, ap=65),
    "Hextech Alternator": Item("Hextech Alternator", 1100, ap=45),
    "Lost Chapter": Item("Lost Chapter", 1200, ap=35, ah=10, mana=200),
    "Fated Ashes": Item("Fated Ashes", 900, ap=40, ashes=True),
    "Haunting Guise": Item("Haunting Guise", 1300, ap=30, hp=200, guise=True),
    "Void Amethyst": Item("Void Amethyst", 1000, ap=20, pct_mpen=0.10),
    "Boots of Mana": Item(
        "Boots of Mana", 1200, ap=25, mana_regen_pct=0.75, flat_mpen=8,
        tags=("boots", "t2"),
    ),
    "Spellslinger's Shoes": Item(
        "Spellslinger's Shoes", 2200, ap=40, mana_regen_pct=1.00,
        flat_mpen=18, pct_mpen=0.08, tags=("boots", "t3"),
    ),
    "Luden's Echo": Item(
        "Luden's Echo", 2800, ap=100, ah=10, mana=500, luden=True,
    ),
    "Infinity Orb": Item(
        "Infinity Orb", 3100, ap=110, flat_mpen=15, orb=True,
    ),
    "Blackfire Torch": Item(
        "Blackfire Torch", 2800, ap=80, ah=20, mana=500, blackfire=True,
    ),
    "Liandry's Torment": Item(
        "Liandry's Torment", 3000, ap=70, hp=300, liandry=True,
    ),
    "Void Staff": Item("Void Staff", 3000, ap=95, pct_mpen=0.40),
    "Rabadon's Deathcap": Item(
        "Rabadon's Deathcap", 3400, ap=130, deathcap=True,
    ),
}

UPGRADE = {
    "Boots of Mana": ("Boots of Speed", "Amplifying Tome"),
    "Spellslinger's Shoes": ("Boots of Mana",),
    "Lost Chapter": ("Amplifying Tome", "Ring of Revelation"),
    "Hextech Alternator": ("Amplifying Tome",),
    "Fated Ashes": ("Amplifying Tome",),
    "Haunting Guise": ("Amplifying Tome", "Ruby Crystal"),
    "Luden's Echo": ("Lost Chapter", "Hextech Alternator"),
    "Infinity Orb": ("Hextech Alternator", "Needlessly Large Rod"),
    "Blackfire Torch": ("Lost Chapter", "Fated Ashes"),
    "Liandry's Torment": ("Haunting Guise", "Fated Ashes"),
    "Void Staff": ("Void Amethyst", "Needlessly Large Rod"),
    "Rabadon's Deathcap": ("Needlessly Large Rod", "Blasting Wand"),
}

NEXT = {
    "Boots of Mana": ["Boots of Speed", "Amplifying Tome"],
    "Spellslinger's Shoes": ["Boots of Mana"],
    "Lost Chapter": ["Amplifying Tome", "Ring of Revelation"],
    "Hextech Alternator": ["Amplifying Tome"],
    "Fated Ashes": ["Amplifying Tome"],
    "Haunting Guise": ["Ruby Crystal", "Amplifying Tome"],
    "Luden's Echo": ["Lost Chapter", "Hextech Alternator"],
    "Infinity Orb": ["Needlessly Large Rod", "Hextech Alternator"],
    "Blackfire Torch": ["Fated Ashes", "Lost Chapter"],
    "Liandry's Torment": ["Fated Ashes", "Haunting Guise"],
    "Void Staff": ["Void Amethyst", "Needlessly Large Rod"],
    "Rabadon's Deathcap": ["Needlessly Large Rod", "Blasting Wand"],
}

T3 = {"Spellslinger's Shoes"}


def core(first: str, second: str, third: str) -> List[str]:
    head = ["Amplifying Tome", "Boots of Speed", "Boots of Mana"]
    if first == "Luden's Echo":
        mid = ["Lost Chapter", "Hextech Alternator", "Luden's Echo"]
    else:
        mid = ["Lost Chapter", "Fated Ashes", "Blackfire Torch"]
    if second == "Infinity Orb":
        mid += ["Infinity Orb"]
    else:
        mid += ["Haunting Guise", "Liandry's Torment"]
    return head + mid + ["Spellslinger's Shoes", third]


BUILD_PATHS: Dict[str, List[str]] = {
    "Pen · Luden → Orb → Cap": core(
        "Luden's Echo", "Infinity Orb", "Rabadon's Deathcap",
    ),
    "Pen · Luden → Orb → Void": core(
        "Luden's Echo", "Infinity Orb", "Void Staff",
    ),
    "Burn · BF → Liandry → Void": core(
        "Blackfire Torch", "Liandry's Torment", "Void Staff",
    ),
    "Burn · BF → Liandry → Cap": core(
        "Blackfire Torch", "Liandry's Torment", "Rabadon's Deathcap",
    ),
    "Hybrid · BF → Orb → Cap": core(
        "Blackfire Torch", "Infinity Orb", "Rabadon's Deathcap",
    ),
}


def remaining(name: str, owned: List[str]) -> int:
    credit = sum(ITEMS[c].cost for c in UPGRADE.get(name, ()) if c in owned)
    return max(0, ITEMS[name].cost - credit)


def done(step: str, owned: List[str]) -> bool:
    if step in owned:
        return True
    boots = {"Boots of Mana", "Spellslinger's Shoes"}
    if step == "Boots of Speed" and any(b in owned for b in boots):
        return True
    if step == "Boots of Mana" and "Spellslinger's Shoes" in owned:
        return True
    if step == "Lost Chapter" and (
        "Luden's Echo" in owned or "Blackfire Torch" in owned
    ):
        return True
    if step in ("Fated Ashes", "Haunting Guise") and "Liandry's Torment" in owned:
        return True
    if step == "Fated Ashes" and "Blackfire Torch" in owned:
        return True
    if step == "Hextech Alternator" and "Luden's Echo" in owned:
        # First Alternator was consumed; Orb buys a fresh one via NEXT.
        return True
    if step == "Amplifying Tome" and any(
        x in owned
        for x in (
            "Lost Chapter",
            "Fated Ashes",
            "Boots of Mana",
            "Spellslinger's Shoes",
            "Haunting Guise",
            "Hextech Alternator",
            "Void Amethyst",
            "Luden's Echo",
            "Infinity Orb",
            "Blackfire Torch",
            "Liandry's Torment",
        )
    ):
        return True
    return False


def can_buy(name: str, owned: List[str], gold: int, minute: int) -> bool:
    if name in owned:
        return False
    if name in T3 and minute < T3_BOOTS_MINUTE:
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
        for comp in NEXT.get(step, []):
            if comp in owned:
                continue
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
    q_lv, w_lv, e_lv = [3, 8, 10, 11], [7, 12, 14, 15], [1, 2, 4, 6]
    return min(4, sum(1 for lv in {"Q": q_lv, "W": w_lv, "E": e_lv}[skill] if level >= lv))


def e_evolved(minute: int) -> bool:
    return minute >= 6


def trans_ah(level: int) -> float:
    return 12.0 if level >= 5 else 6.0


@dataclass
class Stats:
    names: List[str]
    ap: float
    ah: float
    ad: float
    flat_mpen: float
    pct_mpen: float
    luden: bool
    orb: bool
    blackfire: bool
    liandry: bool
    ashes: bool
    guise: bool


def stats_of(owned: List[str], level: int) -> Stats:
    ap = ah = flat = pct = 0.0
    luden = orb = bf = li = ashes = guise = False
    for n in owned:
        it = ITEMS[n]
        ap += it.ap
        ah += it.ah
        flat += it.flat_mpen
        pct += it.pct_mpen
        luden = luden or it.luden
        orb = orb or it.orb
        bf = bf or it.blackfire
        li = li or it.liandry
        ashes = ashes or it.ashes
        guise = guise or it.guise
        if it.deathcap:
            ap *= 1.30
    ah += trans_ah(level)
    if bf:
        ap *= 1.04  # 1 champ burning
    ad = 54.0 + 3.5 * max(0, level - 1)
    return Stats(list(owned), ap, ah, ad, flat, pct, luden, orb, bf, li, ashes, guise)


def pen_mult(st: Stats, mr: float) -> float:
    mr = mr * (1.0 - st.pct_mpen) - st.flat_mpen
    return 100.0 / (100.0 + max(8.0, mr))


def ah_cd(base: float, ah: float) -> float:
    return base * 100.0 / (100.0 + max(0.0, ah))


def squishy(minute: int, level: int) -> Tuple[float, float]:
    hp = 620 + 95 * level + 18 * minute
    mr = 32 + 1.25 * level + (0 if minute < 12 else 16)
    return hp, mr


def tank(minute: int, level: int) -> Tuple[float, float]:
    hp = 700 + 110 * level + 80 * max(0, minute - 6)
    mr = 34 + 2.0 * level + (0 if minute < 8 else min(8.0 * (minute - 8), 90.0))
    return hp, mr


def e_raw(st: Stats, er: int, evolved: bool) -> float:
    laser = [0, 75, 120, 165, 210][max(1, er)] + 0.30 * st.ap
    shock = ([0, 30, 70, 110, 150][max(1, er)] + 0.60 * st.ap) if evolved else 0.0
    return laser + shock


def q_raw(st: Stats, qr: int) -> float:
    blast = [0, 45, 60, 75, 90][max(1, qr)] + 0.30 * st.ap
    aa = [0, 20, 40, 60, 80][max(1, qr)] + st.ad + 0.40 * st.ap
    return blast + aa


def r_raw(st: Stats, rr: int, seconds: float) -> float:
    if rr <= 0:
        return 0.0
    initial = [0, 100, 175, 250][rr] + 0.60 * st.ap
    tick = [0, 50, 90, 130][rr] + 0.40 * st.ap
    return initial + tick * seconds


def burn_dps(st: Stats, hp: float) -> float:
    dps = 0.0
    if st.ashes and not st.blackfire and not st.liandry:
        dps += 5.0
    if st.blackfire:
        dps += 20.0 + 0.02 * st.ap
    if st.liandry:
        dps += 0.02 * hp
    return dps


def luden_proc(st: Stats) -> float:
    return (140.0 + 0.15 * st.ap) if st.luden else 0.0


def apply_orb(dmg: float, hp: float, has_orb: bool, start_frac: float) -> float:
    """Inevitable Demise: +20% while the target is below 35% HP."""
    if not has_orb:
        return dmg
    hp_now = start_frac * hp
    thresh = 0.35 * hp
    if hp_now - dmg >= thresh:
        return dmg
    to_thresh = max(0.0, hp_now - thresh)
    rest = dmg - to_thresh
    return to_thresh + rest * 1.20


def deal(raw: float, st: Stats, mr: float, long_fight: bool) -> float:
    amp = 1.0
    if st.liandry or st.guise:
        amp += 0.06 if long_fight else 0.02
    return raw * pen_mult(st, mr) * amp


def combat(st: Stats, minute: int, level: int) -> Dict[str, float]:
    er, qr, rr = skill_rank(level, "E"), skill_rank(level, "Q"), skill_rank(level, "R")
    evolved = e_evolved(minute)
    e_cd = ah_cd([0, 10, 9, 8, 7][max(1, er)], st.ah)
    e_per_min = 60.0 / e_cd
    sh, smr = squishy(minute, level)
    th, tmr = tank(minute, level)

    def poke(hp: float, mr: float) -> float:
        raw = e_raw(st, er, evolved) + luden_proc(st) + burn_dps(st, hp) * 3.0
        mit = deal(raw, st, mr, long_fight=False)
        return apply_orb(mit, hp, st.orb, 1.0)

    def allin(hp: float, mr: float, start_frac: float = 1.0) -> float:
        # W stun holds R: 5.5s storm. One Luden (9s CD). Burns the whole window.
        raw = (
            e_raw(st, er, evolved)
            + q_raw(st, qr)
            + r_raw(st, rr, 5.5 if rr else 0.0)
            + luden_proc(st)
            + burn_dps(st, hp) * (5.5 if rr else 3.0)
        )
        mit = deal(raw, st, mr, long_fight=bool(rr))
        return apply_orb(mit, hp, st.orb, start_frac)

    return {
        "poke_sq": poke(sh, smr),
        "poke_tk": poke(th, tmr),
        "allin_sq": allin(sh, smr),
        "allin_tk": allin(th, tmr),
        "e_per_min": e_per_min,
        "sh": sh,
        "th": th,
    }


@dataclass
class Snap:
    minute: int
    build: str
    items: List[str]
    gold: int
    level: int
    ap: float
    ah: float
    poke_sq: float
    poke_tk: float
    allin_sq: float
    allin_tk: float
    e_per_min: float
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
        c = combat(st, m, lv)
        notes = []
        if st.luden:
            notes.append("Luden echo")
        if st.orb:
            notes.append("Orb execute")
        if st.blackfire:
            notes.append("BF burn")
        if st.liandry:
            notes.append("Liandry %HP")
        spent = 500 + sum(mid_income(t) for t in range(1, m + 1)) - gold
        out.append(
            Snap(
                m, name, list(owned), int(spent + gold), lv,
                round(st.ap, 1), round(st.ah, 1),
                round(c["poke_sq"], 1), round(c["poke_tk"], 1),
                round(c["allin_sq"], 1), round(c["allin_tk"], 1),
                round(c["e_per_min"], 2),
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


def short(items: List[str]) -> str:
    skip = {
        "Amplifying Tome", "Ring of Revelation", "Ruby Crystal",
        "Boots of Speed", "Hextech Alternator", "Void Amethyst",
    }
    shown = [n for n in items if n not in skip]
    return " › ".join(shown[:5] + (["…"] if len(shown) > 5 else [])) or "(comp)"


def summarize(results: Dict[str, List[Snap]]) -> str:
    pen = "Pen · Luden → Orb → Cap"
    burn = "Burn · BF → Liandry → Void"
    pen_v = "Pen · Luden → Orb → Void"
    burn_c = "Burn · BF → Liandry → Cap"
    hyb = "Hybrid · BF → Orb → Cap"
    a, b, c, d, h = (
        results[pen], results[burn], results[pen_v], results[burn_c], results[hyb],
    )
    L: List[str] = []
    L.append("=" * 78)
    L.append("VIKTOR MID — LUDEN+ORB vs BF+LIANDRY vs BF+ORB+CAP (WR 7.2e)")
    L.append("Role: mid · E-max poke then R 5.5s · 5 ô (giày + 4)")
    L.append("Cặp: Luden→Orb→Cap  vs  BF→Liandry→Void  vs  BF→Orb→Cap")
    L.append("=" * 78)
    L.append("")
    L.append("4 Ô")
    L.append("-" * 78)
    L.append("  Client : Tốc Chiến 7.2e. T3 mage mất 7% pen. Không PC Shadowflame.")
    L.append("  Role   : mid. E waveclear + Big Bully. Không copy jungle/support.")
    L.append("  Cặp    : Luden+Orb vs BF+Liandry vs BF+Orb+Cap. Cùng Spellslinger.")
    L.append("  Metric : E poke full HP, và all-in 5.5s (E+Q+AA+R) lên squishy vs tank.")
    L.append("")
    L.append("  Diamond+ (2026-09-06): Luden→Orb→Cap 54.66% WR / 25% pick;")
    L.append("  BF→Liandry→Void 51.91% WR / 7.6% pick. WR không phải metric cặp này.")
    L.append("  Mercury 39% pick so với Ionia — A vs C, không dùng cho cặp này.")
    L.append("")

    def spike(snaps: List[Snap], item: str) -> str:
        t = first(snaps, item)
        return f"~{t}:00" if t else "không xong 20p"

    L.append("PATH A — Luden → Orb → Cap")
    L.append("-" * 78)
    L.append("  Spellslinger · Luden's Echo · Infinity Orb · Deathcap")
    L.append(
        f"  Luden {spike(a, "Luden's Echo")}  Orb {spike(a, 'Infinity Orb')}  "
        f"Spell {spike(a, "Spellslinger's Shoes")}  Cap {spike(a, "Rabadon's Deathcap")}"
    )
    L.append("  Luden = Echo 140+15% AP / 9s (7.2b), 0% pen (T3 stripped).")
    L.append("")
    L.append("PATH B — BF → Liandry → Void")
    L.append("-" * 78)
    L.append("  Spellslinger · Blackfire · Liandry · Void Staff")
    L.append(
        f"  BF {spike(b, 'Blackfire Torch')}  Liandry {spike(b, "Liandry's Torment")}  "
        f"Spell {spike(b, "Spellslinger's Shoes")}  Void {spike(b, 'Void Staff')}"
    )
    L.append("  BF 20+2% AP/s + 20 AH. Liandry 2% max HP/s. Void 40%.")
    L.append("")
    L.append("PATH C — BF → Orb → Cap  (hybrid, câu hỏi follow-up)")
    L.append("-" * 78)
    L.append("  Spellslinger · Blackfire · Infinity Orb · Deathcap")
    L.append(
        f"  BF {spike(h, 'Blackfire Torch')}  Orb {spike(h, 'Infinity Orb')}  "
        f"Spell {spike(h, "Spellslinger's Shoes")}  Cap {spike(h, "Rabadon's Deathcap")}"
    )
    L.append("  Có burn + 20 AH + Orb execute + Cap. Không Echo, không Liandry, không Void.")
    L.append("")
    L.append("-" * 78)
    L.append("E POKE (full HP)")
    L.append("-" * 78)
    for m in (6, 8, 10, 12, 14, 16, 18, 20):
        x, y, z = a[m - 1], b[m - 1], h[m - 1]
        L.append(
            f"  {m:>2}:00 | Pen {x.poke_sq:>5.0f}  BF-Orb {z.poke_sq:>5.0f}"
            f"  Burn {y.poke_sq:>5.0f}  | tank Pen {x.poke_tk:>5.0f}"
            f"  BF-Orb {z.poke_tk:>5.0f}  Burn {y.poke_tk:>5.0f}"
        )
        L.append(f"         BF-Orb: {short(z.items)}")
    L.append("")
    L.append(
        f"  Poke squishy 20p: Pen {area(a,'poke_sq'):.0f}  "
        f"BF-Orb {area(h,'poke_sq'):.0f} "
        f"({100*(area(h,'poke_sq')/area(a,'poke_sq')-1):+.1f}% vs Pen)  "
        f"Burn {area(b,'poke_sq'):.0f} "
        f"({100*(area(b,'poke_sq')/area(a,'poke_sq')-1):+.1f}% vs Pen)"
    )
    L.append(
        f"  E/phút @20: Pen {a[19].e_per_min:.1f}  BF-Orb {h[19].e_per_min:.1f}  "
        f"Burn {b[19].e_per_min:.1f}"
    )
    L.append("")
    L.append("-" * 78)
    L.append("ALL-IN 5.5s (E + Q + empowered AA + R storm + burns)")
    L.append("-" * 78)
    for m in (8, 10, 12, 14, 16, 18, 20):
        x, y, z = a[m - 1], b[m - 1], h[m - 1]
        L.append(
            f"  {m:>2}:00 | Pen sq {x.allin_sq:>5.0f}  BF-Orb {z.allin_sq:>5.0f}"
            f"  Burn {y.allin_sq:>5.0f}"
        )
        L.append(
            f"         tank | Pen {x.allin_tk:>5.0f}  BF-Orb {z.allin_tk:>5.0f}"
            f"  Burn {y.allin_tk:>5.0f}"
        )
    L.append("")
    L.append(
        f"  All-in squishy 20p: Pen {area(a,'allin_sq'):.0f}  "
        f"BF-Orb {area(h,'allin_sq'):.0f} "
        f"({100*(area(h,'allin_sq')/area(a,'allin_sq')-1):+.1f}%)  "
        f"Burn {area(b,'allin_sq'):.0f} "
        f"({100*(area(b,'allin_sq')/area(a,'allin_sq')-1):+.1f}%)"
    )
    L.append(
        f"  All-in tank 20p:    Pen {area(a,'allin_tk'):.0f}  "
        f"BF-Orb {area(h,'allin_tk'):.0f} "
        f"({100*(area(h,'allin_tk')/area(a,'allin_tk')-1):+.1f}%)  "
        f"Burn {area(b,'allin_tk'):.0f} "
        f"({100*(area(b,'allin_tk')/area(a,'allin_tk')-1):+.1f}%)"
    )
    L.append(
        f"  Pen+Void tank: {area(c,'allin_tk'):.0f}  "
        f"Burn+Cap tank: {area(d,'allin_tk'):.0f}"
    )
    L.append("")
    L.append("  Spike")
    for label, snaps in (
        ("Pen Cap", a), ("Burn Void", b), ("BF-Orb Cap", h),
        ("Pen Void", c), ("Burn Cap", d),
    ):
        bits = []
        for it in (
            "Boots of Mana", "Luden's Echo", "Infinity Orb",
            "Blackfire Torch", "Liandry's Torment", "Spellslinger's Shoes",
            "Void Staff", "Rabadon's Deathcap",
        ):
            t = first(snaps, it)
            if t:
                bits.append(f"{it.split()[0]}~{t}:00")
        L.append(f"    {label}: " + ", ".join(bits))
    L.append("")
    L.append("-" * 78)
    L.append("VERDICT")
    L.append("-" * 78)
    L.append(
        f"  Poke squishy vs Pen: BF-Orb {100*(area(h,'poke_sq')/area(a,'poke_sq')-1):+.1f}%  "
        f"Burn {100*(area(b,'poke_sq')/area(a,'poke_sq')-1):+.1f}%"
    )
    L.append(
        f"  All-in squishy vs Pen: BF-Orb {100*(area(h,'allin_sq')/area(a,'allin_sq')-1):+.1f}%  "
        f"Burn {100*(area(b,'allin_sq')/area(a,'allin_sq')-1):+.1f}%"
    )
    L.append(
        f"  All-in tank vs Pen: BF-Orb {100*(area(h,'allin_tk')/area(a,'allin_tk')-1):+.1f}%  "
        f"Burn {100*(area(b,'allin_tk')/area(a,'allin_tk')-1):+.1f}%"
    )
    L.append("  BF→Orb→Cap = burn + execute, mất Echo và mất Liandry/%HP.")
    L.append("  Không phải 'best of both': poke/squishy thua Luden; tank thua BF+Liandry+Void.")
    L.append("  Default squishy/poke → Luden Orb Cap. 2+ tank → BF Liandry Void.")
    L.append("  BF Orb Cap chỉ khi muốn AH/burn first-item mà vẫn execute, chấp nhận thua hai đầu.")
    L.append("  Đừng thay Spellslinger: core 7.2 = 0 pen nếu không giày/% Void.")
    L.append("=" * 78)
    return "\n".join(L)


def export_json(results: Dict[str, List[Snap]], path: str) -> None:
    payload = {
        "meta": {
            "champion": "Viktor",
            "role": "Mid",
            "patch": "7.2e",
            "pair": "Luden+Orb+Cap vs BF+Liandry+Void vs BF+Orb+Cap",
            "ranked_note": (
                "Diamond+ Luden-Orb-Cap 54.66% WR / 25% pick vs "
                "BF-Liandry-Void 51.91% WR / 7.6% pick (2026-09-06). "
                "Unconditioned; not this sim's metric."
            ),
        },
        "builds": {
            name: [
                {
                    "minute": s.minute,
                    "items": s.items,
                    "gold": s.gold,
                    "poke_sq": s.poke_sq,
                    "poke_tk": s.poke_tk,
                    "allin_sq": s.allin_sq,
                    "allin_tk": s.allin_tk,
                    "e_per_min": s.e_per_min,
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
    a = results["Pen · Luden → Orb → Cap"]
    b = results["Burn · BF → Liandry → Void"]
    for snaps in results.values():
        for s in snaps:
            if s.minute < 10:
                assert "Spellslinger's Shoes" not in s.items
    h = results["Hybrid · BF → Orb → Cap"]
    lu, orb, bf, li, h_orb, h_cap = (
        first(a, "Luden's Echo"),
        first(a, "Infinity Orb"),
        first(b, "Blackfire Torch"),
        first(b, "Liandry's Torment"),
        first(h, "Infinity Orb"),
        first(h, "Rabadon's Deathcap"),
    )
    assert lu is not None and 6 <= lu <= 10, lu
    assert bf is not None and 6 <= bf <= 10, bf
    assert orb is not None and 11 <= orb <= 17, orb
    assert li is not None and 11 <= li <= 16, li
    assert first(h, "Blackfire Torch") == bf
    assert h_orb is not None and 11 <= h_orb <= 17, h_orb
    assert h_cap is not None and 18 <= h_cap <= 20, h_cap
    # Hybrid has Orb+BF, never Liandry.
    assert first(h, "Liandry's Torment") is None
    assert first(h, "Luden's Echo") is None
    # Path-row Tome must not leak back after Spellslinger (500g/min bug).
    for snaps in results.values():
        for s in snaps:
            finished = sum(
                1
                for n in s.items
                if n in (
                    "Luden's Echo", "Infinity Orb", "Blackfire Torch",
                    "Liandry's Torment", "Spellslinger's Shoes",
                    "Void Staff", "Rabadon's Deathcap",
                )
            )
            if finished >= 3 and "Amplifying Tome" in s.items:
                raise AssertionError(f"Tome leak @ {s.minute}: {s.items}")
    # Constraint must flip the winner across metrics.
    assert area(a, "poke_sq") > area(b, "poke_sq"), (
        area(a, "poke_sq"), area(b, "poke_sq"),
    )
    assert area(b, "allin_tk") > area(a, "allin_tk"), (
        area(b, "allin_tk"), area(a, "allin_tk"),
    )


def main() -> None:
    results = {n: run_build(n, p) for n, p in BUILD_PATHS.items()}
    self_check(results)
    report = summarize(results)
    print(report)
    with open(os.path.join(OUT_DIR, "report.txt"), "w", encoding="utf-8") as f:
        f.write(report + "\n")
    export_json(results, os.path.join(OUT_DIR, "results.json"))
    print(f"\nWrote {OUT_DIR}/report.txt and {OUT_DIR}/results.json")


if __name__ == "__main__":
    main()
