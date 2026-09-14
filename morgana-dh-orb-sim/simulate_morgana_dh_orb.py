#!/usr/bin/env python3
"""
Wild Rift Morgana Dark Harvest — does BF → Orb → Cap fit?

Patch 7.2e. Mid gold (thay Viktor). DH keystone (not Comet).

Locked:
  Client: Tốc Chiến. T3 mage = 0% pen.
  Role: mid farm (W-max). DH is execute, not a jungle-clear rune.
  Pair: BF → Orb → Cap vs BF → Orb → Void (magic pen)
        vs 5 squishy team and 4 squishy + 1 tank.
  Also keep BF→Liandry→Rylai and Luden→Orb→Cap as context.
  Metric: combo from 70% HP (DH identity), 40% HP (Orb+DH overlap),
          and 90% HP (dwell). Orb amps a hit only if already <35% before it.

DH procs <50%. Orb execute <35%. DH often fires on Q before Orb turns on.
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
    flat_mpen: float = 0
    pct_mpen: float = 0
    deathcap: bool = False
    luden: bool = False
    orb: bool = False
    blackfire: bool = False
    liandry: bool = False
    ashes: bool = False
    guise: bool = False
    rylai: bool = False
    tags: Tuple[str, ...] = ()


ITEMS: Dict[str, Item] = {
    "Amplifying Tome": Item("Amplifying Tome", 500, ap=20),
    "Ring of Revelation": Item("Ring of Revelation", 300, ah=5),
    "Boots of Speed": Item("Boots of Speed", 400, tags=("boots", "t1")),
    "Ruby Crystal": Item("Ruby Crystal", 500, hp=200),
    "Blasting Wand": Item("Blasting Wand", 800, ap=45),
    "Needlessly Large Rod": Item("Needlessly Large Rod", 1400, ap=65),
    "Giant's Belt": Item("Giant's Belt", 1000, hp=350),
    "Hextech Alternator": Item("Hextech Alternator", 1100, ap=45),
    "Lost Chapter": Item("Lost Chapter", 1200, ap=35, ah=10, mana=200),
    "Fated Ashes": Item("Fated Ashes", 900, ap=40, ashes=True),
    "Haunting Guise": Item("Haunting Guise", 1300, ap=30, hp=200, guise=True),
    "Void Amethyst": Item("Void Amethyst", 1000, ap=20, pct_mpen=0.10),
    "Boots of Mana": Item(
        "Boots of Mana", 1200, ap=25, flat_mpen=8, tags=("boots", "t2"),
    ),
    "Spellslinger's Shoes": Item(
        "Spellslinger's Shoes", 2200, ap=40, flat_mpen=18, pct_mpen=0.08,
        tags=("boots", "t3"),
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
    "Rylai's Crystal Scepter": Item(
        "Rylai's Crystal Scepter", 2700, ap=65, hp=350, rylai=True,
    ),
    "Rabadon's Deathcap": Item(
        "Rabadon's Deathcap", 3400, ap=130, deathcap=True,
    ),
    "Void Staff": Item("Void Staff", 3000, ap=95, pct_mpen=0.40),
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
    "Rylai's Crystal Scepter": ("Giant's Belt", "Blasting Wand", "Amplifying Tome"),
    "Rabadon's Deathcap": ("Needlessly Large Rod", "Blasting Wand"),
    "Void Staff": ("Void Amethyst", "Needlessly Large Rod"),
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
    "Rylai's Crystal Scepter": ["Giant's Belt", "Blasting Wand", "Amplifying Tome"],
    "Rabadon's Deathcap": ["Needlessly Large Rod", "Blasting Wand"],
    "Void Staff": ["Void Amethyst", "Needlessly Large Rod"],
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
    "DH · BF → Liandry → Rylai": core(
        "Blackfire Torch", "Liandry's Torment", "Rylai's Crystal Scepter",
    ),
    "DH · BF → Orb → Cap": core(
        "Blackfire Torch", "Infinity Orb", "Rabadon's Deathcap",
    ),
    "DH · BF → Orb → Void": core(
        "Blackfire Torch", "Infinity Orb", "Void Staff",
    ),
    "DH · Luden → Orb → Cap": core(
        "Luden's Echo", "Infinity Orb", "Rabadon's Deathcap",
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
        return True
    if step == "Void Amethyst" and "Void Staff" in owned:
        return True
    if step == "Amplifying Tome" and any(
        x in owned
        for x in (
            "Lost Chapter", "Fated Ashes", "Boots of Mana",
            "Spellslinger's Shoes", "Haunting Guise", "Hextech Alternator",
            "Luden's Echo", "Infinity Orb", "Blackfire Torch",
            "Liandry's Torment", "Rylai's Crystal Scepter",
            "Void Amethyst", "Void Staff",
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
    blackfire: bool
    liandry: bool
    ashes: bool
    guise: bool
    rylai: bool


def stats_of(owned: List[str], level: int, bf_stacks: int = 1) -> Stats:
    ap = ah = flat = pct = 0.0
    luden = orb = bf = li = ashes = guise = rylai = False
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
        rylai = rylai or it.rylai
        if it.deathcap:
            ap *= 1.30
    ah += trans_ah(level)
    if bf:
        ap *= 1.0 + 0.04 * max(1, min(5, bf_stacks))
    return Stats(list(owned), ap, ah, flat, pct, luden, orb, bf, li, ashes, guise, rylai)


def pen_mult(st: Stats, mr: float) -> float:
    mr = mr * (1.0 - st.pct_mpen) - st.flat_mpen
    return 100.0 / (100.0 + max(8.0, mr))


def ah_cd(base: float, ah: float) -> float:
    return base * 100.0 / (100.0 + max(0.0, ah))


def squishy_stats(minute: int, level: int) -> Tuple[float, float]:
    hp = 620 + 95 * level + 18 * minute
    mr = 32 + 1.25 * level + (0 if minute < 12 else 16)
    return hp, mr


def tank_stats(minute: int, level: int) -> Tuple[float, float]:
    hp = 700 + 110 * level + 80 * max(0, minute - 6)
    mr = 34 + 2.0 * level + (0 if minute < 8 else min(8.0 * (minute - 8), 90.0))
    return hp, mr


def burn_dps(st: Stats, hp: float) -> float:
    dps = 0.0
    if st.ashes and not st.blackfire and not st.liandry:
        dps += 5.0
    if st.blackfire:
        dps += 20.0 + 0.02 * st.ap
    if st.liandry:
        dps += 0.02 * hp
    return dps


def magic_hit(raw: float, st: Stats, mr: float, hp_frac: float, long_fight: bool) -> float:
    """Orb 20% only if already below 35% before this hit."""
    amp = 1.06 if (st.liandry or st.guise) and long_fight else (
        1.02 if st.liandry or st.guise else 1.0
    )
    dmg = raw * pen_mult(st, mr) * amp
    if st.orb and hp_frac <= 0.35:
        dmg *= 1.20
    return dmg


def combo(
    st: Stats,
    minute: int,
    level: int,
    start_frac: float,
    use_r: bool,
    kind: str = "squishy",
    include_q: bool = True,
) -> Dict[str, float]:
    """Q (optional) → DH if crossed 50% → W ticks → optional R."""
    qr, wr, rr = skill_rank(level, "Q"), skill_rank(level, "W"), skill_rank(level, "R")
    hp_max, mr = (tank_stats if kind == "tank" else squishy_stats)(minute, level)
    hp = start_frac * hp_max
    root = [0, 2.0, 2.25, 2.5, 2.75][max(1, qr)]
    dwell = 5.0 if st.rylai else root
    long_fight = use_r or st.rylai
    dealt = 0.0
    dh_landed = 0.0
    orb_hits = 0
    souls = dh_souls(minute)
    dh_raw = 35.0 + 11.0 * souls + 0.05 * st.ap

    def hit(raw: float) -> None:
        nonlocal hp, dealt, dh_landed, orb_hits
        frac = hp / hp_max
        if st.orb and frac <= 0.35:
            orb_hits += 1
        dmg = magic_hit(raw, st, mr, frac, long_fight)
        hp -= dmg
        dealt += dmg
        if dh_landed == 0.0 and hp <= 0.50 * hp_max:
            frac2 = hp / hp_max
            dh = magic_hit(dh_raw, st, mr, frac2, long_fight)
            hp -= dh
            dealt += dh
            dh_landed = 1.0

    if include_q:
        q = [0, 80, 160, 240, 320][max(1, qr)] + 0.90 * st.ap
        if st.luden:
            q += 140.0 + 0.15 * st.ap
        hit(q)
        cheap = 10 + 2.2 * level
        hp -= cheap
        dealt += cheap

    missing = 1.0 - max(0.05, hp / hp_max)
    w_amp = 1.0 + 1.7 * min(0.7, missing)
    tick = ([0, 7, 12, 17, 22][max(1, wr)] + 0.07 * st.ap) * w_amp
    ticks = int(dwell / 0.5)
    bdps = burn_dps(st, hp_max)
    for _ in range(ticks):
        hit(tick + bdps * 0.5)

    if use_r and rr and minute >= 6:
        r = [0, 150, 225, 300][rr] + 0.70 * st.ap
        hit(r)
        if st.rylai:
            hit(0.4 * r)

    q_cd = ah_cd(9.0, st.ah) * (0.95 if level >= 9 else 1.0)
    return {
        "dealt": dealt,
        "dh": dh_landed,
        "orb_hits": float(orb_hits),
        "dwell": dwell,
        "q_per_min": 60.0 / q_cd,
        "hp_left": max(0.0, hp / hp_max),
        "pen": pen_mult(st, mr),
    }


@dataclass
class Snap:
    minute: int
    build: str
    items: List[str]
    gold: int
    level: int
    ap: float
    d70: float
    d40: float
    d90: float
    dh70: float
    dh90: float
    orb70: float
    sq70: float
    tank70: float
    team5: float
    team41: float
    notes: str


def run_build(name: str, path: List[str]) -> List[Snap]:
    gold, owned = 500, []
    owned, gold = progress(path, owned, gold, 0)
    out: List[Snap] = []
    for m in range(1, GAME_MINUTES + 1):
        gold += mid_income(m)
        owned, gold = progress(path, owned, gold, m)
        lv = level_at(m)
        st1 = stats_of(owned, lv, bf_stacks=1)
        st5 = stats_of(owned, lv, bf_stacks=5)
        c70 = combo(st1, m, lv, 0.70, True)
        c40 = combo(st1, m, lv, 0.40, True)
        c90 = combo(st1, m, lv, 0.90, False)
        sq = combo(st5, m, lv, 0.70, True, kind="squishy", include_q=True)
        splash_sq = combo(st5, m, lv, 0.70, True, kind="squishy", include_q=False)
        splash_tk = combo(st5, m, lv, 0.70, True, kind="tank", include_q=False)
        tank = combo(st5, m, lv, 0.70, True, kind="tank", include_q=True)
        team5 = sq["dealt"] + 4.0 * splash_sq["dealt"]
        team41 = sq["dealt"] + 3.0 * splash_sq["dealt"] + splash_tk["dealt"]
        notes = []
        if st1.orb:
            notes.append("Orb")
        if st1.blackfire:
            notes.append("BF")
        if "Void Staff" in owned:
            notes.append("Void 40%")
        if any(ITEMS[n].deathcap for n in owned):
            notes.append("Cap")
        spent = 500 + sum(mid_income(t) for t in range(1, m + 1)) - gold
        out.append(
            Snap(
                m, name, list(owned), int(spent + gold), lv, round(st1.ap, 1),
                round(c70["dealt"], 1), round(c40["dealt"], 1), round(c90["dealt"], 1),
                round(c70["dh"], 2), round(c90["dh"], 2), round(c70["orb_hits"], 1),
                round(sq["dealt"], 1), round(tank["dealt"], 1),
                round(team5, 1), round(team41, 1),
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
        "Boots of Speed", "Hextech Alternator", "Giant's Belt",
    }
    shown = [n for n in items if n not in skip]
    return " › ".join(shown[:5] + (["…"] if len(shown) > 5 else [])) or "(comp)"


def pct_vs(num: float, den: float) -> str:
    return f"{100.0 * (num / den - 1.0):+.1f}%"


def summarize(results: Dict[str, List[Snap]]) -> str:
    lock = "DH · BF → Liandry → Rylai"
    hyb = "DH · BF → Orb → Cap"
    voi = "DH · BF → Orb → Void"
    lud = "DH · Luden → Orb → Cap"
    a, b, d, c = results[lock], results[hyb], results[voi], results[lud]
    L: List[str] = []
    L.append("=" * 78)
    L.append("MORGANA DH — BF→ORB→CAP vs BF→ORB→VOID (WR 7.2e)")
    L.append("Mid gold, DH, Spellslinger 18+8%. Teamfight BF 5 stack. 5 slot.")
    L.append("=" * 78)
    L.append("")
    L.append("4 Ô")
    L.append("-" * 78)
    L.append("  Client : Tốc Chiến 7.2e. Không PC. T3 mage = 0 pen.")
    L.append("  Role   : mid + DH (execute). Không copy support Ionia WR.")
    L.append("  Cặp    : BF→Orb→Cap  vs  BF→Orb→Void")
    L.append("           đội 5 squishy  vs  4 squishy + 1 tank")
    L.append("  Metric : TF phút 20 / diện tích 20p. Q carry + W/R splash.")
    L.append("           70% HP, R on, BF 5 stack. Orb chỉ amp hit khi đã <35%.")
    L.append("")

    def spike(snaps: List[Snap], item: str) -> str:
        t = first(snaps, item)
        return f"~{t}:00" if t else "không xong 20p"

    L.append("PATH A — DH lock (mặc định kit W)")
    L.append("-" * 78)
    L.append("  Spellslinger · Blackfire · Liandry · Rylai")
    L.append(
        f"  BF {spike(a, 'Blackfire Torch')}  Liandry {spike(a, "Liandry's Torment")}  "
        f"Rylai {spike(a, "Rylai's Crystal Scepter")}"
    )
    L.append("")
    L.append("PATH B — BF → Orb → Cap")
    L.append("-" * 78)
    L.append("  Spellslinger · Blackfire · Infinity Orb · Deathcap")
    L.append(
        f"  BF {spike(b, 'Blackfire Torch')}  Orb {spike(b, 'Infinity Orb')}  "
        f"Cap {spike(b, "Rabadon's Deathcap")}"
    )
    L.append("  Orb +20% khi <35%. DH nổ khi <50% — thường là Q, TRƯỚC cửa Orb.")
    L.append("")
    L.append("PATH D — BF → Orb → Void  (câu hỏi magic pen)")
    L.append("-" * 78)
    L.append("  Spellslinger · Blackfire · Infinity Orb · Void Staff")
    L.append(
        f"  BF {spike(d, 'Blackfire Torch')}  Orb {spike(d, 'Infinity Orb')}  "
        f"Void {spike(d, 'Void Staff')}"
    )
    L.append("  Spell 18+8% + Orb 15 flat đã gần cap MR squishy. Void 40% trên 1 tank.")
    L.append("")
    L.append("PATH C — Luden → Orb → Cap (context burst)")
    L.append("-" * 78)
    L.append(
        f"  Luden {spike(c, "Luden's Echo")}  Orb {spike(c, 'Infinity Orb')}  "
        f"Cap {spike(c, "Rabadon's Deathcap")}"
    )
    L.append("")
    L.append("-" * 78)
    L.append("1 TARGET — squishy Q+W+R  (BF 5 stack, 70% HP)")
    L.append("-" * 78)
    for m in (12, 16, 20):
        y, v = b[m - 1], d[m - 1]
        L.append(
            f"  {m:>2}:00 | Cap {y.sq70:>5.0f}  Void {v.sq70:>5.0f}  "
            f"Void vs Cap {pct_vs(v.sq70, y.sq70)}"
        )
    L.append(
        f"  Diện tích 20p: Cap {area(b,'sq70'):.0f}  "
        f"Void {area(d,'sq70'):.0f} ({pct_vs(area(d,'sq70'), area(b,'sq70'))})"
    )
    L.append("")
    L.append("-" * 78)
    L.append("1 TARGET — tank Q+W+R  (BF 5 stack, 70% HP)")
    L.append("-" * 78)
    for m in (12, 16, 20):
        y, v = b[m - 1], d[m - 1]
        L.append(
            f"  {m:>2}:00 | Cap {y.tank70:>5.0f}  Void {v.tank70:>5.0f}  "
            f"Void vs Cap {pct_vs(v.tank70, y.tank70)}"
        )
    L.append(
        f"  Diện tích 20p: Cap {area(b,'tank70'):.0f}  "
        f"Void {area(d,'tank70'):.0f} ({pct_vs(area(d,'tank70'), area(b,'tank70'))})"
    )
    L.append("")
    L.append("-" * 78)
    L.append("TEAMFIGHT — Q carry + W/R splash, 70% HP, R on, BF 5")
    L.append("-" * 78)
    L.append("  5 squishy = 1 full Q combo + 4 splash.")
    L.append("  4 squishy + 1 tank = 1 full Q + 3 splash sq + 1 splash tank.")
    for m in (12, 16, 20):
        y, v = b[m - 1], d[m - 1]
        L.append(
            f"  {m:>2}:00 | 5sq  Cap {y.team5:>6.0f}  Void {v.team5:>6.0f}  "
            f"{pct_vs(v.team5, y.team5)}"
        )
        L.append(
            f"         | 4+1  Cap {y.team41:>6.0f}  Void {v.team41:>6.0f}  "
            f"{pct_vs(v.team41, y.team41)}"
        )
        L.append(f"           Cap: {short(y.items)}")
        L.append(f"           Void: {short(v.items)}")
    L.append("")
    L.append(
        f"  Diện tích 5 squishy 20p: Cap {area(b,'team5'):.0f}  "
        f"Void {area(d,'team5'):.0f} ({pct_vs(area(d,'team5'), area(b,'team5'))})"
    )
    L.append(
        f"  Diện tích 4sq+1tank 20p: Cap {area(b,'team41'):.0f}  "
        f"Void {area(d,'team41'):.0f} ({pct_vs(area(d,'team41'), area(b,'team41'))})"
    )
    L.append("")
    L.append("  Spike")
    for label, snaps in (
        ("BF-Orb Cap", b),
        ("BF-Orb Void", d),
        ("Rylai", a),
        ("Luden-Orb", c),
    ):
        bits = []
        for it in (
            "Blackfire Torch", "Luden's Echo", "Liandry's Torment",
            "Infinity Orb", "Spellslinger's Shoes", "Rylai's Crystal Scepter",
            "Rabadon's Deathcap", "Void Staff",
        ):
            t = first(snaps, it)
            if t:
                bits.append(f"{it.split()[0]}~{t}:00")
        L.append(f"    {label}: " + ", ".join(bits))
    L.append("")
    L.append("-" * 78)
    L.append("VERDICT — Cap hay Void?")
    L.append("-" * 78)
    y20, v20 = b[19], d[19]
    L.append("  Full item 20:00 (cả hai xong T4 cùng phút):")
    L.append(f"    1 squishy:        Void vs Cap {pct_vs(v20.sq70, y20.sq70)}")
    L.append(f"    1 tank:           Void vs Cap {pct_vs(v20.tank70, y20.tank70)}")
    L.append(f"    đội 5 squishy:    Void vs Cap {pct_vs(v20.team5, y20.team5)}")
    L.append(f"    đội 4 sq + 1 tank: Void vs Cap {pct_vs(v20.team41, y20.team41)}")
    L.append("  Diện tích 20p (Wand Cap ngồi phút 16; Amethyst Void phút 17; T4 cùng 20):")
    L.append(f"    1 squishy:        Void vs Cap {pct_vs(area(d,'sq70'), area(b,'sq70'))}")
    L.append(f"    1 tank:           Void vs Cap {pct_vs(area(d,'tank70'), area(b,'tank70'))}")
    L.append(f"    đội 5 squishy:    Void vs Cap {pct_vs(area(d,'team5'), area(b,'team5'))}")
    L.append(f"    đội 4 sq + 1 tank: Void vs Cap {pct_vs(area(d,'team41'), area(b,'team41'))}")
    L.append("  Spell 18+8% + Orb 15 flat đã gần cap effective MR squishy.")
    L.append("  Cap 30% amp trên đống AP BF5×Orb. Void 40% pen trả tiền trên tank.")
    L.append("  5 squishy: Cap. 4+1: gần hòa — Void +mỏng lúc full item nếu splash tank.")
    L.append("  1 tank không đủ bắt Void. Void khi 2+ tank / stacked MR / Q vào tank.")
    L.append("  Cryptbloom = Void nhẹ (30%+AH), không thay Cap 5sq.")
    L.append("")
    L.append("-" * 78)
    L.append("CONTEXT — DH vs Rylai (báo cáo trước, 1 stack BF, 1 squishy)")
    L.append("-" * 78)
    L.append(
        f"  70%+R: BF-Orb-Cap vs Rylai {pct_vs(area(b,'d70'), area(a,'d70'))}"
    )
    L.append(
        f"  40%+R: BF-Orb-Cap vs Rylai {pct_vs(area(b,'d40'), area(a,'d40'))}"
    )
    L.append(
        f"  90% noR: BF-Orb-Cap vs Rylai {pct_vs(area(b,'d90'), area(a,'d90'))}"
    )
    L.append(
        f"  DH@90% phút 12–20: Rylai {sum(s.dh90 for s in a[11:]):.1f}  "
        f"BF-Orb {sum(s.dh90 for s in b[11:]):.1f}"
    )
    L.append("  Giữ Liandry+Rylai nếu W-zone người còn máu, không phải Q-execute.")
    L.append("=" * 78)
    return "\n".join(L)


def export_json(results: Dict[str, List[Snap]], path: str) -> None:
    cap = results["DH · BF → Orb → Cap"]
    voi = results["DH · BF → Orb → Void"]
    ryl = results["DH · BF → Liandry → Rylai"]
    payload = {
        "meta": {
            "champion": "Morgana",
            "keystone": "Dark Harvest",
            "role": "Mid (Viktor gold curve)",
            "patch": "7.2e",
            "pair": "BF+Orb+Cap vs BF+Orb+Void on 5 squishy and 4 squishy + 1 tank",
            "metric": (
                "Teamfight: Q carry + W/R splash, 70% HP, R on, BF 5 stacks. "
                "Orb +20% only if target already <35% before the hit."
            ),
        },
        "verdict": {
            "void_vs_cap_1_squishy_20": pct_vs(voi[19].sq70, cap[19].sq70),
            "void_vs_cap_1_tank_20": pct_vs(voi[19].tank70, cap[19].tank70),
            "void_vs_cap_team_5sq_20": pct_vs(voi[19].team5, cap[19].team5),
            "void_vs_cap_team_4sq_1tank_20": pct_vs(voi[19].team41, cap[19].team41),
            "void_vs_cap_1_squishy_area": pct_vs(area(voi, "sq70"), area(cap, "sq70")),
            "void_vs_cap_1_tank_area": pct_vs(area(voi, "tank70"), area(cap, "tank70")),
            "void_vs_cap_team_5sq_area": pct_vs(area(voi, "team5"), area(cap, "team5")),
            "void_vs_cap_team_4sq_1tank_area": pct_vs(area(voi, "team41"), area(cap, "team41")),
            "bf_orb_vs_rylai_70": pct_vs(area(cap, "d70"), area(ryl, "d70")),
            "fit": (
                "5 squishy: Cap. 4+1 full item: Void by a thin splash-tank margin; "
                "20p area still Cap (same T4 minute). 1 tank is not enough to force Void. "
                "Void when 2+ tanks / stacked MR / Q the tank."
            ),
        },
        "builds": {
            name: [
                {
                    "minute": s.minute,
                    "items": s.items,
                    "d70": s.d70,
                    "d40": s.d40,
                    "d90": s.d90,
                    "dh70": s.dh70,
                    "dh90": s.dh90,
                    "orb70": s.orb70,
                    "sq70": s.sq70,
                    "tank70": s.tank70,
                    "team5": s.team5,
                    "team41": s.team41,
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
    a = results["DH · BF → Liandry → Rylai"]
    b = results["DH · BF → Orb → Cap"]
    v = results["DH · BF → Orb → Void"]
    for snaps in results.values():
        for s in snaps:
            if s.minute < 10:
                assert "Spellslinger's Shoes" not in s.items
            assert "Ionian" not in " ".join(s.items)
            assert "Mercury" not in " ".join(s.items)
        assert "Amplifying Tome" not in snaps[-1].items
    assert first(a, "Blackfire Torch") is not None
    assert first(b, "Infinity Orb") is not None
    assert first(v, "Infinity Orb") is not None
    assert first(a, "Rylai's Crystal Scepter") is not None
    assert first(b, "Liandry's Torment") is None
    assert first(v, "Void Staff") is not None
    assert first(b, "Rabadon's Deathcap") is not None
    assert first(b, "Void Staff") is None
    assert first(v, "Rabadon's Deathcap") is None
    assert abs((first(b, "Infinity Orb") or 99) - (first(v, "Infinity Orb") or 0)) <= 1
    # 90% dwell: Rylai must beat no-Rylai hybrid on DH chance late.
    assert sum(s.dh90 for s in a[11:]) >= sum(s.dh90 for s in b[11:])
    # 40% execute: Orb path should not collapse vs Rylai.
    assert area(b, "d40") > 0 and area(a, "d40") > 0
    # Spell+Orb already pens squishies — Cap AP pile should beat Void there.
    assert area(b, "sq70") > area(v, "sq70")
    assert area(b, "team5") > area(v, "team5")
    assert b[-1].sq70 > v[-1].sq70
    assert b[-1].team5 > v[-1].team5
    # 1 tank at full item: Void must pay for 40% pen (do not force 4+1).
    assert v[-1].tank70 > b[-1].tank70
    print("self-check OK")


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
