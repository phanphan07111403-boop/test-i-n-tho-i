#!/usr/bin/env python3
"""
Wild Rift Morgana Jungle — Dark Harvest full build
Patch 7.2e. Average game 20 minutes.

Locked:
  Client: Tốc Chiến (not PC)
  Role: jungle (not mid / support)
  Keystone: Dark Harvest
  Constraint: camp clear (W 195% monsters + Smite) then gank Q
             so W can drop them under 50% and DH procs.

No Diamond+ jungle WR page exists (wrchina is mid+support only).
This is a mechanism build, not a copied ranked core.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import json
import os

GAME_MINUTES = 20
T3_BOOTS_MINUTE = 10
OUT_DIR = os.path.dirname(os.path.abspath(__file__))


def jg_income(minute: int) -> int:
    """Camp gold + Smite 20% monster bonus + modest gank gold.

    No sickle, no lane CS, no Big Bully (minions only). Smite extra
    monster gold until 11:00. Tuned so BF ~8, Liandry ~13, Spell ~15,
    Rylai ~19 — same 20-min envelope as the mid sim, without bully gold.
    """
    if minute <= 4:
        return 430
    if minute <= 8:
        return 510
    if minute <= 12:
        return 575
    if minute <= 16:
        return 640
    return 700


def level_at(minute: int) -> int:
    # Jungle XP is front-loaded (full clear ~5 by 4:00). Cap 15 at 20.
    table = {
        1: 3, 2: 4, 3: 5, 4: 5, 5: 6, 6: 7, 7: 8, 8: 8,
        9: 9, 10: 10, 11: 11, 12: 11, 13: 12, 14: 12,
        15: 13, 16: 13, 17: 14, 18: 14, 19: 15, 20: 15,
    }
    return table.get(minute, 3)


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
    mr_shred: float = 0
    deathcap: bool = False
    rylai: bool = False
    blackfire: bool = False
    liandry: bool = False
    ashes: bool = False
    guise: bool = False
    zhonya: bool = False
    tags: Tuple[str, ...] = ()


ITEMS: Dict[str, Item] = {
    "Amplifying Tome": Item("Amplifying Tome", 500, ap=20),
    "Ring of Revelation": Item("Ring of Revelation", 300, ah=5),
    "Boots of Speed": Item("Boots of Speed", 400, tags=("boots", "t1")),
    "Ruby Crystal": Item("Ruby Crystal", 500, hp=200),
    "Blasting Wand": Item("Blasting Wand", 800, ap=45),
    "Needlessly Large Rod": Item("Needlessly Large Rod", 1400, ap=65),
    "Giant's Belt": Item("Giant's Belt", 1000, hp=350),
    "Seeker's Armguard": Item("Seeker's Armguard", 1400, ap=30),
    "Lost Chapter": Item("Lost Chapter", 1200, ap=35, ah=10, mana=200),
    "Fated Ashes": Item("Fated Ashes", 900, ap=40, ashes=True),
    "Haunting Guise": Item("Haunting Guise", 1300, ap=30, hp=200, guise=True),
    "Fiendish Codex": Item("Fiendish Codex", 900, ap=25, ah=10),
    "Void Amethyst": Item("Void Amethyst", 1000, ap=20, pct_mpen=0.10),
    "Ionian Boots of Lucidity": Item(
        "Ionian Boots of Lucidity", 1000, ah=15, tags=("boots", "t2")
    ),
    "Crimson Lucidity": Item(
        "Crimson Lucidity", 2000, ah=25, mana_regen_pct=0.75, tags=("boots", "t3")
    ),
    "Boots of Mana": Item(
        "Boots of Mana",
        1200,
        ap=25,
        mana_regen_pct=0.75,
        flat_mpen=8,
        tags=("boots", "t2"),
    ),
    "Spellslinger's Shoes": Item(
        "Spellslinger's Shoes",
        2200,
        ap=40,
        mana_regen_pct=1.00,
        flat_mpen=18,
        pct_mpen=0.08,
        tags=("boots", "t3"),
    ),
    "Blackfire Torch": Item(
        "Blackfire Torch", 2800, ap=80, ah=20, mana=500, blackfire=True
    ),
    "Liandry's Torment": Item(
        "Liandry's Torment", 3000, ap=70, hp=300, liandry=True
    ),
    "Rylai's Crystal Scepter": Item(
        "Rylai's Crystal Scepter", 2700, ap=65, hp=350, rylai=True
    ),
    "Rabadon's Deathcap": Item(
        "Rabadon's Deathcap", 3400, ap=130, deathcap=True
    ),
    "Zhonya's Hourglass": Item(
        "Zhonya's Hourglass", 3300, ap=110, zhonya=True
    ),
    "Void Staff": Item("Void Staff", 3000, ap=95, pct_mpen=0.40),
    "Bloodletter's Curse": Item(
        "Bloodletter's Curse", 2900, ap=65, hp=350, ah=15, mr_shred=0.30
    ),
}

UPGRADE = {
    "Ionian Boots of Lucidity": ("Boots of Speed", "Ring of Revelation"),
    "Boots of Mana": ("Boots of Speed", "Amplifying Tome"),
    "Crimson Lucidity": ("Ionian Boots of Lucidity",),
    "Spellslinger's Shoes": ("Boots of Mana",),
    "Lost Chapter": ("Amplifying Tome", "Ring of Revelation"),
    "Fated Ashes": ("Amplifying Tome",),
    "Haunting Guise": ("Amplifying Tome", "Ruby Crystal"),
    "Blackfire Torch": ("Lost Chapter", "Fated Ashes"),
    "Liandry's Torment": ("Haunting Guise", "Fated Ashes"),
    "Rylai's Crystal Scepter": ("Giant's Belt", "Blasting Wand", "Amplifying Tome"),
    "Rabadon's Deathcap": ("Needlessly Large Rod", "Blasting Wand"),
    "Zhonya's Hourglass": ("Seeker's Armguard", "Needlessly Large Rod"),
    "Void Staff": ("Void Amethyst", "Needlessly Large Rod"),
    "Bloodletter's Curse": ("Haunting Guise", "Fiendish Codex"),
}

NEXT = {
    "Ionian Boots of Lucidity": ["Boots of Speed", "Ring of Revelation"],
    "Boots of Mana": ["Boots of Speed", "Amplifying Tome"],
    "Crimson Lucidity": ["Ionian Boots of Lucidity"],
    "Spellslinger's Shoes": ["Boots of Mana"],
    "Lost Chapter": ["Amplifying Tome", "Ring of Revelation"],
    "Fated Ashes": ["Amplifying Tome"],
    "Haunting Guise": ["Ruby Crystal", "Amplifying Tome"],
    "Blackfire Torch": ["Fated Ashes", "Lost Chapter"],
    "Liandry's Torment": ["Fated Ashes", "Haunting Guise"],
    "Rylai's Crystal Scepter": ["Giant's Belt", "Blasting Wand", "Amplifying Tome"],
    "Rabadon's Deathcap": ["Needlessly Large Rod", "Blasting Wand"],
    "Zhonya's Hourglass": ["Seeker's Armguard", "Needlessly Large Rod"],
    "Void Staff": ["Void Amethyst", "Needlessly Large Rod"],
    "Bloodletter's Curse": ["Haunting Guise", "Fiendish Codex"],
}

T3 = {"Crimson Lucidity", "Spellslinger's Shoes"}


def jg_core(t2: str, t3: str, late: List[str]) -> List[str]:
    return [
        "Amplifying Tome",
        "Boots of Speed",
        t2,
        "Lost Chapter",
        "Fated Ashes",
        "Blackfire Torch",
        "Haunting Guise",
        "Liandry's Torment",
        t3,
        "Rylai's Crystal Scepter",
        *late,
    ]


BUILD_PATHS: Dict[str, List[str]] = {
    # Default DH jungle: pen boots (7.2 core has 0 pen) + Rylai so W holds for DH
    "DH · Mana → Spellslinger → Rylai → Cap": jg_core(
        "Boots of Mana",
        "Spellslinger's Shoes",
        ["Rabadon's Deathcap"],
    ),
    "DH · Ionian → Crimson → Rylai → Cap": jg_core(
        "Ionian Boots of Lucidity",
        "Crimson Lucidity",
        ["Rabadon's Deathcap"],
    ),
    # Skip Rylai — DH often fails because they walk out above 50%
    "DH · Spellslinger → Void (no Rylai)": [
        "Amplifying Tome",
        "Boots of Speed",
        "Boots of Mana",
        "Lost Chapter",
        "Fated Ashes",
        "Blackfire Torch",
        "Haunting Guise",
        "Liandry's Torment",
        "Spellslinger's Shoes",
        "Void Staff",
        "Rabadon's Deathcap",
    ],
    # Dive games: Zhonya after Rylai (R channel, no dash)
    "DH · Spellslinger → Rylai → Zhonya": jg_core(
        "Boots of Mana",
        "Spellslinger's Shoes",
        ["Zhonya's Hourglass"],
    ),
}


def remaining(name: str, owned: List[str]) -> int:
    credit = sum(ITEMS[c].cost for c in UPGRADE.get(name, ()) if c in owned)
    return max(0, ITEMS[name].cost - credit)


def done(step: str, owned: List[str]) -> bool:
    if step in owned:
        return True
    boots = {
        "Ionian Boots of Lucidity",
        "Boots of Mana",
        "Crimson Lucidity",
        "Spellslinger's Shoes",
    }
    if step == "Boots of Speed" and any(b in owned for b in boots):
        return True
    if step == "Ionian Boots of Lucidity" and "Crimson Lucidity" in owned:
        return True
    if step == "Boots of Mana" and "Spellslinger's Shoes" in owned:
        return True
    if step in ("Lost Chapter", "Fated Ashes") and "Blackfire Torch" in owned:
        return True
    if step in ("Fated Ashes", "Haunting Guise") and "Liandry's Torment" in owned:
        return True
    if step == "Amplifying Tome" and any(
        x in owned
        for x in ("Lost Chapter", "Fated Ashes", "Boots of Mana", "Haunting Guise")
    ):
        # Tome is a component that gets consumed; don't re-buy as a path row
        # unless the path explicitly needs a fresh one (handled via NEXT).
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
    # Conservative ganking jungler, not a 20-kill stomp.
    return max(0.0, min(14.0, 0.7 * max(0, minute - 3)))


@dataclass
class Stats:
    names: List[str]
    ap: float
    ah: float
    mana: float
    mana_regen_pct: float
    flat_mpen: float
    pct_mpen: float
    mr_shred: float
    rylai: bool
    blackfire: bool
    liandry: bool
    ashes: bool
    guise: bool
    zhonya: bool


def stats_of(owned: List[str], level: int) -> Stats:
    ap = ah = mana = regen = flat = pct = shred = 0.0
    rylai = bf = li = ashes = guise = zh = False
    for n in owned:
        it = ITEMS[n]
        ap += it.ap
        ah += it.ah
        mana += it.mana
        regen += it.mana_regen_pct
        flat += it.flat_mpen
        pct += it.pct_mpen
        shred = max(shred, it.mr_shred)
        rylai = rylai or it.rylai
        bf = bf or it.blackfire
        li = li or it.liandry
        ashes = ashes or it.ashes
        guise = guise or it.guise
        zh = zh or it.zhonya
        if it.deathcap:
            ap *= 1.30
    ah += trans_ah(level)
    if bf:
        ap *= 1.08  # 2 stacks: 1 champ gank + 1 large monster recently
    return Stats(
        list(owned), ap, ah, mana, regen, flat, pct, shred,
        rylai, bf, li, ashes, guise, zh,
    )


def pen_mult(st: Stats, mr: float) -> float:
    mr = mr * (1.0 - st.pct_mpen) * (1.0 - st.mr_shred) - st.flat_mpen
    return 100.0 / (100.0 + max(8.0, mr))


def ah_cd(base: float, ah: float) -> float:
    return base * 100.0 / (100.0 + max(0.0, ah))


def _pool_dps(st: Stats, wr: int, hp: float, dwell: float) -> Tuple[float, float, float]:
    """W tick DPS + burn DPS while they stay in the pool."""
    missing_avg = 0.48 if dwell >= 4.5 else 0.28
    w_amp = 1.0 + 1.7 * missing_avg
    tick = ([0, 7, 12, 17, 22][max(1, wr)] + 0.07 * st.ap) * w_amp
    w_dps = tick / 0.5
    burn_dps = 0.0
    if st.ashes and not st.blackfire and not st.liandry:
        burn_dps += 5.0
    if st.blackfire:
        burn_dps += 20.0 + 0.02 * st.ap
    if st.liandry:
        burn_dps += 0.02 * hp
    return tick, w_dps, burn_dps


def dh_chance(start_hp: float, instant: float, dps: float, dwell: float, fifty: float) -> float:
    """P(DH): Q already <50%, or W+burn crosses 50% before they leave the pool."""
    hp_after_q = start_hp - instant
    if hp_after_q <= fifty:
        return 1.0
    t = (hp_after_q - fifty) / max(1.0, dps)
    if t <= dwell * 0.65:
        return 1.0
    if t <= dwell:
        return 0.75
    if t <= dwell + 0.8:
        return 0.40
    return 0.10


def gank_combo(st: Stats, minute: int, level: int) -> Dict[str, float]:
    """70% = DH identity (Q often execute). 90% = healthy lane, W must hold."""
    qr, wr, rr = skill_rank(level, "Q"), skill_rank(level, "W"), skill_rank(level, "R")
    q_cd = ah_cd(9.0, st.ah) * (0.95 if level >= 9 else 1.0)
    root = [0, 2.0, 2.25, 2.5, 2.75][max(1, qr)]
    # No Rylai: they walk/Flash the pool the moment root ends.
    dwell = 5.0 if st.rylai else root
    ticks = dwell / 0.5
    hp = 620 + 90 * level + 16 * minute
    tick, w_dps, burn_dps = _pool_dps(st, wr, hp, dwell)
    q_dmg = [0, 80, 160, 240, 320][max(1, qr)] + 0.90 * st.ap
    w_dmg = ticks * tick
    r_dmg = 0.0
    if rr and minute >= 6:
        r_dmg = 1.4 * ([0, 150, 225, 300][rr] + 0.70 * st.ap)
    burn_t = dwell + (2.4 if st.rylai else 0.6)
    burn = burn_dps * burn_t
    cheap = 10 + 2.2 * level  # Cheap Shot on Q root
    mr = 32 + 1.3 * level + (0 if minute < 11 else 14)
    mit = pen_mult(st, mr) * (1.04 if st.liandry or st.guise else 1.0)
    instant = (q_dmg + cheap) * mit
    dps = (w_dps + burn_dps) * mit
    souls = dh_souls(minute)
    dh = 35.0 + 11.0 * souls + 0.05 * st.ap
    fifty = 0.50 * hp
    dh_70 = dh_chance(0.70 * hp, instant, dps, dwell, fifty)
    dh_90 = dh_chance(0.90 * hp, instant, dps, dwell, fifty)
    raw = (q_dmg + cheap) + w_dmg + r_dmg + burn + dh * dh_70
    dealt = raw * mit
    return {
        "gank": dealt,
        "dh": dh * dh_70,
        "dh_p": dh_70,
        "dh_p90": dh_90,
        "q_per_min": 60.0 / q_cd,
        "dwell": dwell,
        "souls": souls,
        "pen": mit,
    }


def camp_clear(st: Stats, minute: int, level: int) -> float:
    """DPS into a large camp (buff/krug). Smite 30% ability dmg vs monsters."""
    wr = max(1, skill_rank(level, "W"))
    tick = ([0, 7, 12, 17, 22][wr] + 0.07 * st.ap) * 1.95  # 195% monsters
    # ~10 ticks if they stay in pool (camps do)
    w = 10 * tick
    smite_mult = 1.30
    burn = 0.0
    if st.blackfire:
        burn += (40.0 + 0.02 * st.ap) * 5.0  # monster BF burn
    elif st.ashes:
        burn += 45.0  # ashes extra vs monsters
    return (w + burn) * smite_mult


@dataclass
class Snap:
    minute: int
    build: str
    items: List[str]
    gold: int
    level: int
    ap: float
    ah: float
    gank: float
    camp: float
    dh_p: float
    dh_p90: float
    souls: float
    q_per_min: float
    dwell: float
    notes: str


def run_build(name: str, path: List[str]) -> List[Snap]:
    gold, owned = 500, []
    owned, gold = progress(path, owned, gold, 0)
    out: List[Snap] = []
    for m in range(1, GAME_MINUTES + 1):
        gold += jg_income(m)
        owned, gold = progress(path, owned, gold, m)
        lv = level_at(m)
        st = stats_of(owned, lv)
        g = gank_combo(st, m, lv)
        camp = camp_clear(st, m, lv)
        notes = []
        if st.blackfire:
            notes.append("BF camp burn")
        if st.liandry:
            notes.append("Liandry")
        if st.rylai:
            notes.append("rylai lock")
        if g["dh_p"] >= 0.9:
            notes.append("DH@70% on Q")
        elif g["dh_p"] < 0.4:
            notes.append("DH@70% misses")
        if g["dh_p90"] >= 0.7:
            notes.append("DH@90% holds")
        elif g["dh_p90"] < 0.4:
            notes.append("DH@90% walks out")
        if st.zhonya:
            notes.append("stasis")
        spent = 500 + sum(jg_income(t) for t in range(1, m + 1)) - gold
        out.append(
            Snap(
                m, name, list(owned), int(spent + gold), lv,
                round(st.ap, 1), round(st.ah, 1),
                round(g["gank"], 1), round(camp, 1),
                round(g["dh_p"], 2), round(g["dh_p90"], 2), round(g["souls"], 1),
                round(g["q_per_min"], 2), round(g["dwell"], 2),
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
    skip = {"Amplifying Tome", "Ring of Revelation", "Ruby Crystal", "Boots of Speed"}
    shown = [n for n in items if n not in skip]
    return " › ".join(shown[:5] + (["…"] if len(shown) > 5 else [])) or "(comp)"


def summarize(results: Dict[str, List[Snap]]) -> str:
    defn = "DH · Mana → Spellslinger → Rylai → Cap"
    ion = "DH · Ionian → Crimson → Rylai → Cap"
    nor = "DH · Spellslinger → Void (no Rylai)"
    zho = "DH · Spellslinger → Rylai → Zhonya"
    a, b, c, d = results[defn], results[ion], results[nor], results[zho]
    L: List[str] = []
    L.append("=" * 78)
    L.append("MORGANA JUNGLE — DARK HARVEST FULL BUILD (Wild Rift 7.2e)")
    L.append("Role: đi rừng · Keystone: Dark Harvest · Clear then gank <50%")
    L.append("Không có Diamond+ jungle WR — đây là kit, không copy mid/support.")
    L.append("=" * 78)
    L.append("")
    L.append("FULL BUILD (mặc định)")
    L.append("-" * 78)
    L.append("  Summoner : Flash + Smite")
    L.append("  Skill    : W > Q > E   |  R @ 5 / 9 / 13")
    L.append("  Ngọc     : Dark Harvest · Cheap Shot · Manaflow")
    L.append("             Transcendence · Relentless Hunter")
    L.append("  Start    : Amplifying Tome  (WR không có món rừng — Smite chứa clear)")
    L.append("  Slot     : 5 ô (giày + 4 món). Đừng list món 6 như PC.")
    L.append("")

    def spike(snaps: List[Snap], item: str) -> str:
        t = first(snaps, item)
        return f"~{t}:00" if t else "không xong 20p"

    L.append(f"  1. Lost Chapter → Fated Ashes → Blackfire Torch   ({spike(a, 'Blackfire Torch')})")
    L.append(f"  2. Boots of Mana                                 ({spike(a, 'Boots of Mana')} T2)")
    L.append(f"  3. Liandry's Torment                             ({spike(a, "Liandry's Torment")})")
    L.append(f"  4. Spellslinger's Shoes                          (sau 10:00, {spike(a, "Spellslinger's Shoes")})")
    L.append(f"  5. Rylai's Crystal Scepter                       ({spike(a, "Rylai's Crystal Scepter")})  ← giữ W / DH@90%")
    L.append("  Full 5 ô: Spellslinger · Blackfire · Liandry · Rylai · Deathcap")
    L.append("  Deathcap không xong trong 20p vàng rừng. Zhonya/Void thay Cap.")
    L.append("")
    L.append("  Vì sao không copy mid:")
    L.append("  • Smite Recoup = 4 mana/s trong rừng — OOM clear nhẹ hơn mid.")
    L.append("  • Big Bully không ăn camp. Spellslinger vẫn lấy vì 7.2 core = 0 pen.")
    L.append("  • Blackfire burn quái 40+2% AP/s + stack trên large monster.")
    L.append("  • DH proc tướng <50%. Gank 70%: Q thường đã execute — DH nổ trên Q.")
    L.append("  • Gank 90% (lane còn máu): không Rylai → họ bước ra pool trước 50%.")
    L.append("  • Rylai là ô 4 vì giữ W/teamfight, không vì 70% gank hụt DH.")
    L.append("")
    L.append("-" * 78)
    L.append("GANK 70% HP (execute) + DH@90% (healthy — Rylai quyết proc)")
    L.append("-" * 78)
    for m in (6, 8, 10, 12, 14, 16, 18, 20):
        x, y, z = a[m - 1], b[m - 1], c[m - 1]
        L.append(
            f"  {m:>2}:00 | Spell+Rylai {x.gank:>6.0f} (DH70 {x.dh_p:.0%} / DH90 {x.dh_p90:.0%})"
            f"  Ionia {y.gank:>6.0f}  noRylai {z.gank:>6.0f} (DH90 {z.dh_p90:.0%})"
        )
        L.append(f"         items: {short(x.items)}")
    L.append("")
    L.append(
        f"  Diện tích gank 70% 20p: Spell+Rylai {area(a,'gank'):.0f}  |  "
        f"Ionia {area(b,'gank'):.0f} ({100*(area(b,'gank')/area(a,'gank')-1):+.1f}%)  |  "
        f"noRylai {area(c,'gank'):.0f} ({100*(area(c,'gank')/area(a,'gank')-1):+.1f}%)"
    )
    L.append(
        f"  DH@90% phút 12–20: Rylai {sum(s.dh_p90 for s in a[11:]):.1f}  "
        f"noRylai {sum(s.dh_p90 for s in c[11:]):.1f}  "
        f"(dwell @20 {a[19].dwell:.1f}s vs {c[19].dwell:.1f}s)"
    )
    L.append(
        f"  Q/phút @20: Spell {a[19].q_per_min:.1f}  Ionia {b[19].q_per_min:.1f}"
    )
    L.append(
        f"  Clear camp @8 (sau BF): Spell {a[7].camp:.0f}  Ionia {b[7].camp:.0f}"
    )
    L.append("")
    L.append("  Spike")
    for label, snaps in (("Spell+Rylai", a), ("Ionia", b), ("noRylai", c), ("Zhonya", d)):
        bits = []
        for it in (
            "Boots of Mana", "Ionian Boots of Lucidity", "Blackfire Torch",
            "Liandry's Torment", "Spellslinger's Shoes", "Crimson Lucidity",
            "Rylai's Crystal Scepter", "Void Staff", "Zhonya's Hourglass",
            "Rabadon's Deathcap",
        ):
            t = first(snaps, it)
            if t:
                bits.append(f"{it.split()[0]}~{t}:00")
        L.append(f"    {label}: " + ", ".join(bits))
    L.append("")
    L.append("-" * 78)
    L.append("SITUATIONAL")
    L.append("-" * 78)
    L.append("  Zhonya     thay Cap nếu assassin / cần R-stasis (ô 5).")
    L.append("  Void       thay Cap nếu 2+ tank (40% pen). Đừng thay Rylai.")
    L.append("  Bloodletter  thay Cap vs tank/burn — shred 30% từ tick W.")
    L.append("  Cryptbloom  nếu cần 30% pen + 20 AH, không cần max Void.")
    L.append("  Ionia/Crimson  nếu Flash-R / Q haste > pen (ít gank execute).")
    L.append("  Mercury     chỉ khi CC nặng — không phải default DH.")
    L.append("")
    L.append("  PLAY: full clear W (để W tick hết bãi, đừng AA cắt CDR) →")
    L.append("  gank lane đã thê → Q → W dưới chân → Cheap Shot + DH khi <50%.")
    L.append("=" * 78)
    return "\n".join(L)


def export_json(results: Dict[str, List[Snap]], path: str) -> None:
    payload = {
        "meta": {
            "champion": "Morgana",
            "role": "Jungle",
            "keystone": "Dark Harvest",
            "patch": "7.2e",
            "note": "No Diamond+ jungle WR sample; mechanism build.",
        },
        "builds": {
            name: [
                {
                    "minute": s.minute,
                    "items": s.items,
                    "gold": s.gold,
                    "gank": s.gank,
                    "camp": s.camp,
                    "dh_p": s.dh_p,
                    "dh_p90": s.dh_p90,
                    "souls": s.souls,
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
    a = results["DH · Mana → Spellslinger → Rylai → Cap"]
    c = results["DH · Spellslinger → Void (no Rylai)"]
    for snaps in results.values():
        for s in snaps:
            if s.minute < 10:
                assert "Spellslinger's Shoes" not in s.items
                assert "Crimson Lucidity" not in s.items
    ion = results["DH · Ionian → Crimson → Rylai → Cap"]
    bf, li, sp, ry = (
        first(a, "Blackfire Torch"),
        first(a, "Liandry's Torment"),
        first(a, "Spellslinger's Shoes"),
        first(a, "Rylai's Crystal Scepter"),
    )
    assert bf is not None and 7 <= bf <= 10, bf
    assert li is not None and 12 <= li <= 15, li
    assert sp is not None and 10 <= sp <= 17, sp
    assert ry is not None and 16 <= ry <= 20, ry
    # Pen boots beat Ionia on execute ganks (70%).
    assert area(a, "gank") > area(ion, "gank")
    # Rylai is the W-hold: longer dwell, better DH on a still-healthy laner.
    assert a[19].dwell > c[19].dwell
    late_90_a = sum(s.dh_p90 for s in a[11:])
    late_90_c = sum(s.dh_p90 for s in c[11:])
    assert late_90_a > late_90_c, (late_90_a, late_90_c)


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
