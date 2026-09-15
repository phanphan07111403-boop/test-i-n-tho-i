#!/usr/bin/env python3
"""
Wild Rift 7.2e — Morgana mid, farm Arcane Comet from minute 1 to 30.

7.2 nerfed Comet AP 20% → 5% and stack 3 → 2. Each landing comet is +1
stack for the rest of the game. Ability Haste does not reduce Comet CD
(16→8s by level, 0.8s delay). Persistent W / burn can trigger it; the
delay is what misses unless the target is rooted or Rylai-slowed.

Metric is Comet: stacks farmed × per-hit damage (pen / HF / tiny AP).
Echo / Squall / R are not Comet. Ability Haste does not add procs.

No inventory lock: BF / Luden / Liandry / Rylai first, then 4 legendaries.
Crypt XOR Void. Mid gold, no support item.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations, permutations
from typing import Dict, Iterable, List, Optional, Sequence, Tuple
import json
import os

GAME_MINUTES = 30
T3_BOOTS_MINUTE = 10
OUT_DIR = os.path.dirname(os.path.abspath(__file__))
HF_AMP = 1.10
START_GOLD = 500
MAX_STACKS = 200.0  # WR does not publish a 14/99 cap; live games sit ~40–60

CHAPTER_ITEMS = {"Blackfire Torch", "Luden's Echo", "Seraph's Embrace"}

# 7.2e Comet: 15–100 (level) + 2×hits + 10% bAD + 5% AP. CD 16–8s.
# No AD on this mage. No CD refund. One stack per comet that hits.


def comet_base(level: int) -> float:
    return 15.0 + 85.0 * (level - 1) / 14.0


def comet_cd(level: int) -> float:
    return 16.0 - 8.0 * (level - 1) / 14.0


def comet_raw(ap: float, level: int, stacks: float) -> float:
    return comet_base(level) + 2.0 * stacks + 0.05 * ap


def mid_income(minute: int) -> int:
    if minute <= 4:
        return 430
    if minute <= 8:
        return 520
    if minute <= 12:
        return 570
    if minute <= 16:
        return 620
    if minute <= 22:
        return 660
    return 700


def level_at(minute: int) -> int:
    table = {
        1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7, 7: 8, 8: 9,
        9: 10, 10: 11, 11: 11, 12: 12, 13: 12, 14: 13,
        15: 13, 16: 14, 17: 14, 18: 15, 19: 15, 20: 15,
    }
    return table.get(minute, 15)


def gs_ap(minute: int) -> float:
    if minute < 6:
        return 0.0
    stacks = 1 + (minute - 6) // 3
    return float(stacks * (stacks + 3))


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
    shred: float = 0.0
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
    "Fated Ashes": Item("Fated Ashes", 900, ap=40),
    "Haunting Guise": Item("Haunting Guise", 1300, ap=30),
    "Void Amethyst": Item("Void Amethyst", 1000, ap=20, pct_mpen=0.10),
    "Hextech Alternator": Item("Hextech Alternator", 1100, ap=45),
    "Aether Wisp": Item("Aether Wisp", 950, ap=30),
    "Kindlegem": Item("Kindlegem", 1000, ah=10),
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
        "Horizon Focus", 2700, ap=80, ah=25, horizon=True,
    ),
    "Cryptbloom": Item("Cryptbloom", 3000, ap=70, ah=20, pct_mpen=0.30),
    "Liandry's Torment": Item("Liandry's Torment", 3000, ap=70, liandry=True),
    "Rylai's Crystal Scepter": Item(
        "Rylai's Crystal Scepter", 2700, ap=65, rylai=True,
    ),
    "Rabadon's Deathcap": Item(
        "Rabadon's Deathcap", 3400, ap=130, deathcap=True,
    ),
    "Infinity Orb": Item("Infinity Orb", 3100, ap=110, flat_mpen=15, orb=True),
    "Void Staff": Item("Void Staff", 3000, ap=95, pct_mpen=0.40),
    "Cosmic Drive": Item("Cosmic Drive", 3000, ap=70, ah=25),
    "Bloodletter's Curse": Item(
        "Bloodletter's Curse", 2900, ap=65, ah=15, shred=0.30,
    ),
    "Seraph's Embrace": Item("Seraph's Embrace", 3000, ap=80, ah=25),
    "Stormsurge": Item(
        "Stormsurge", 2900, ap=90, flat_mpen=15, tags=("burst",),
    ),
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
    "Aether Wisp": ("Amplifying Tome",),
    "Kindlegem": ("Ruby Crystal",),
    "Cosmic Drive": ("Aether Wisp", "Kindlegem", "Fiendish Codex"),
    "Bloodletter's Curse": ("Haunting Guise", "Fiendish Codex"),
    "Seraph's Embrace": ("Lost Chapter", "Kindlegem", "Amplifying Tome"),
    "Stormsurge": ("Hextech Alternator", "Aether Wisp"),
}

T3 = {"Spellslinger's Shoes"}
LEGENDARIES = {
    "Blackfire Torch", "Luden's Echo", "Horizon Focus", "Cryptbloom",
    "Liandry's Torment", "Rylai's Crystal Scepter", "Rabadon's Deathcap",
    "Infinity Orb", "Void Staff", "Cosmic Drive", "Bloodletter's Curse",
    "Seraph's Embrace", "Stormsurge",
}

HEAD_BF = [
    "Amplifying Tome", "Boots of Speed", "Boots of Mana",
    "Lost Chapter", "Fated Ashes", "Blackfire Torch", "Spellslinger's Shoes",
]
HEAD_LUDEN = [
    "Amplifying Tome", "Boots of Speed", "Boots of Mana",
    "Lost Chapter", "Hextech Alternator", "Luden's Echo", "Spellslinger's Shoes",
]
HEAD_LIANDRY = [
    "Amplifying Tome", "Boots of Speed", "Boots of Mana",
    "Fated Ashes", "Haunting Guise", "Liandry's Torment", "Spellslinger's Shoes",
]
HEAD_RYLAI = [
    "Amplifying Tome", "Boots of Speed", "Boots of Mana",
    "Giant's Belt", "Blasting Wand", "Rylai's Crystal Scepter",
    "Spellslinger's Shoes",
]

POOL = [
    "Horizon Focus",
    "Cryptbloom",
    "Void Staff",
    "Rylai's Crystal Scepter",
    "Rabadon's Deathcap",
    "Infinity Orb",
    "Liandry's Torment",
    "Cosmic Drive",
    "Bloodletter's Curse",
    "Luden's Echo",
    "Blackfire Torch",
]


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
    boots = {
        "Boots of Speed": ("Boots of Mana", "Spellslinger's Shoes"),
        "Boots of Mana": ("Spellslinger's Shoes",),
    }
    if step in boots and any(b in owned for b in boots[step]):
        return True
    consumed = {
        "Lost Chapter": ("Luden's Echo", "Blackfire Torch", "Seraph's Embrace"),
        "Fated Ashes": ("Blackfire Torch", "Liandry's Torment"),
        "Haunting Guise": ("Liandry's Torment", "Bloodletter's Curse"),
        "Hextech Alternator": ("Luden's Echo", "Infinity Orb", "Stormsurge"),
        "Aether Wisp": ("Cosmic Drive", "Stormsurge"),
        "Kindlegem": ("Cosmic Drive", "Seraph's Embrace"),
        "Giant's Belt": ("Rylai's Crystal Scepter",),
        "Void Amethyst": ("Cryptbloom", "Void Staff"),
    }
    if step in consumed and any(x in owned for x in consumed[step]):
        return True
    if step == "Fiendish Codex" and any(
        x in owned
        for x in ("Horizon Focus", "Cryptbloom", "Cosmic Drive", "Bloodletter's Curse")
    ):
        return True
    if step == "Needlessly Large Rod" and any(
        x in owned for x in ("Rabadon's Deathcap", "Infinity Orb", "Void Staff")
    ):
        return True
    if step == "Blasting Wand" and any(
        x in owned for x in ("Rabadon's Deathcap", "Rylai's Crystal Scepter")
    ):
        return True
    if step == "Amplifying Tome" and any(
        x in owned for x in ITEMS if x not in ("Amplifying Tome", "Boots of Speed")
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
        have = list(owned)
        missing = []
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


def trans_ah(level: int) -> float:
    """7.2 Transcendence: 5 AH, +5 at 5 (total 10)."""
    if level >= 5:
        return 10.0
    return 5.0


@dataclass
class Stats:
    names: List[str]
    ap: float
    ah: float
    flat_mpen: float
    pct_mpen: float
    shred: float
    luden: bool
    orb: bool
    horizon: bool
    blackfire: bool
    liandry: bool
    rylai: bool


def stats_of(
    owned: List[str],
    level: int,
    minute: int,
    extra_ap: float = 0.0,
    extra_ah: float = 0.0,
    gs: bool = True,
    trans: bool = True,
) -> Stats:
    ap = ah = flat = pct = shred = 0.0
    luden = orb = horizon = bf = li = rylai = False
    cap = False
    for n in owned:
        it = ITEMS[n]
        ap += it.ap
        ah += it.ah
        flat += it.flat_mpen
        pct += it.pct_mpen
        shred += it.shred
        luden = luden or it.luden
        orb = orb or it.orb
        horizon = horizon or it.horizon
        bf = bf or it.blackfire
        li = li or it.liandry
        rylai = rylai or it.rylai
        cap = cap or it.deathcap
    if gs:
        ap += gs_ap(minute)
    ap += extra_ap
    bf_targets = 1.0 if minute < 16 else 1.8
    if bf:
        ap *= 1.0 + 0.04 * bf_targets
    if cap:
        ap *= 1.30
    if trans:
        ah += trans_ah(level)
    ah += extra_ah
    return Stats(
        list(owned), ap, ah, flat, pct, shred, luden, orb, horizon, bf, li, rylai,
    )


def pen_mult(st: Stats, mr: float) -> float:
    mr = mr * (1.0 - min(0.90, st.shred)) * (1.0 - min(1.0, st.pct_mpen)) - st.flat_mpen
    return 100.0 / (100.0 + max(8.0, mr))


def dummy(minute: int, level: int) -> Tuple[float, float]:
    hp = 620 + 95 * level + 18 * minute
    mr = 32 + 1.25 * level + (0 if minute < 12 else 8 + 1.2 * (minute - 12))
    return hp, mr


def strike(raw: float, st: Stats, mr: float, frac: float, hf: bool) -> float:
    dmg = raw * pen_mult(st, mr)
    if hf:
        dmg *= HF_AMP
    if st.orb and frac <= 0.35:
        dmg *= 1.20
    return dmg


def land_p(st: Stats) -> float:
    """P(the 0.8s delayed comet actually hits).

    Immobilize (Q root) ≈ guaranteed. Rylai slow makes the walk-out hard.
    W/burn still *triggers* Comet on a miss; the projectile is what misses.
    """
    q_p = 0.60 if st.rylai else 0.45
    rooted = 0.96
    walk = 0.84 if st.rylai else 0.48
    return q_p * rooted + (1.0 - q_p) * walk


def lane_uptime(minute: int) -> float:
    """Fraction of theoretical Comet CDs you are actually in range.

    Clock time is not combat time. ~50 landing stacks is a good Morgana
    game; 7.5 procs/min at lv15 would be fighting every second.
    """
    if minute <= 3:
        return 0.42
    if minute <= 6:
        return 0.36
    if minute <= 12:
        return 0.32
    if minute <= 20:
        return 0.28
    return 0.27


def fight_extra(minute: int) -> float:
    """Extra comet windows from roams / skirmishes, before accuracy."""
    if minute < 6:
        return 0.0
    if minute < 10:
        return 0.25
    if minute < 16:
        return 0.45
    if minute < 22:
        return 0.60
    return 0.70


def procs_this_minute(st: Stats, minute: int, level: int) -> Tuple[float, float]:
    """(triggers, hits). Hits become stacks. AH does not raise the CD cap."""
    cap = 60.0 / comet_cd(level)
    triggers = cap * lane_uptime(minute) + fight_extra(minute)
    hits = triggers * land_p(st)
    return triggers, hits


def comet_hit_dmg(st: Stats, minute: int, level: int, stacks: float, frac: float) -> float:
    _, mr = dummy(minute, level)
    # Q marks HF; comet lands 0.8s later with the mark on.
    hf = st.horizon
    return strike(comet_raw(st.ap, level, stacks), st, mr, frac, hf)


@dataclass
class Snap:
    minute: int
    items: List[str]
    gold: int
    ap: float
    ah: float
    stacks: float
    land: float
    hits: float
    comet_hit: float
    comet60: float
    score: float
    legendaries: int
    rylai: bool


def legendary_count(items: List[str]) -> int:
    return sum(1 for n in items if n in LEGENDARIES)


def run_path(path: Sequence[str]) -> List[Snap]:
    owned: List[str] = []
    gold = START_GOLD
    stacks = 0.0
    snaps: List[Snap] = []
    for m in range(1, GAME_MINUTES + 1):
        gold += mid_income(m)
        owned, gold = progress(list(path), owned, gold, m)
        lv = level_at(m)
        st = stats_of(owned, lv, m)
        _trig, hits = procs_this_minute(st, m, lv)
        d90 = comet_hit_dmg(st, m, lv, stacks, 0.90)
        d32 = comet_hit_dmg(st, m, lv, stacks, 0.32)
        comet60 = hits * (0.75 * d90 + 0.25 * d32)
        stacks = min(MAX_STACKS, stacks + hits)
        snaps.append(
            Snap(
                minute=m,
                items=list(owned),
                gold=gold,
                ap=st.ap,
                ah=st.ah,
                stacks=stacks,
                land=land_p(st),
                hits=hits,
                comet_hit=d90,
                comet60=comet60,
                score=comet60,
                legendaries=legendary_count(owned),
                rylai=st.rylai,
            )
        )
    return snaps


def valid_tail(head_legendaries: Sequence[str], tail: Sequence[str]) -> bool:
    built = list(head_legendaries) + list(tail)
    if len(set(built)) != len(built):
        return False
    if "Cryptbloom" in built and "Void Staff" in built:
        return False
    if sum(1 for x in built if x in CHAPTER_ITEMS) > 2:
        return False
    return True


def path_label(path: Sequence[str]) -> str:
    nick = {
        "Blackfire Torch": "BF",
        "Luden's Echo": "Luden",
        "Horizon Focus": "HF",
        "Cryptbloom": "Crypt",
        "Liandry's Torment": "Liandry",
        "Rylai's Crystal Scepter": "Rylai",
        "Rabadon's Deathcap": "Cap",
        "Infinity Orb": "Orb",
        "Void Staff": "Void",
        "Cosmic Drive": "Cosmic",
        "Bloodletter's Curse": "Bloodletter",
        "Seraph's Embrace": "Seraph",
        "Stormsurge": "Storm",
        "Spellslinger's Shoes": "Spell",
    }
    legs = [nick[n] for n in path if n in nick and n != "Spellslinger's Shoes"]
    return " → ".join(legs)


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
        "Void Staff": "Void",
        "Lost Chapter": "Chapter",
        "Fated Ashes": "Ashes",
        "Boots of Mana": "Mana",
        "Cosmic Drive": "Cosmic",
        "Bloodletter's Curse": "Bloodletter",
        "Seraph's Embrace": "Seraph",
        "Stormsurge": "Storm",
        "Needlessly Large Rod": "NLR",
        "Haunting Guise": "Guise",
        "Blasting Wand": "Wand",
        "Giant's Belt": "Belt",
        "Hextech Alternator": "Alt",
        "Void Amethyst": "Amethyst",
        "Fiendish Codex": "Codex",
        "Amplifying Tome": "Tome",
        "Boots of Speed": "Boots",
    }
    show: List[str] = []
    for n in items:
        if n in nick and nick[n] not in show:
            show.append(nick[n])
    if not show:
        return ", ".join(items[-3:]) if items else "(empty)"
    return " · ".join(show)


def pct(num: float, den: float) -> str:
    if den <= 1e-9:
        return "n/a"
    return f"{100.0 * (num / den - 1.0):+.1f}%"


def first_item(snaps: List[Snap], item: str) -> Optional[int]:
    for s in snaps:
        if item in s.items:
            return s.minute
    return None


def purchase_log(snaps: List[Snap]) -> List[Tuple[int, str]]:
    seen = set()
    log: List[Tuple[int, str]] = []
    watch = [
        "Rylai's Crystal Scepter", "Blackfire Torch", "Luden's Echo",
        "Liandry's Torment", "Spellslinger's Shoes", "Cryptbloom", "Void Staff",
        "Horizon Focus", "Rabadon's Deathcap", "Infinity Orb",
        "Bloodletter's Curse", "Cosmic Drive", "Stormsurge", "Seraph's Embrace",
    ]
    for s in snaps:
        for name in watch:
            if name in s.items and name not in seen:
                seen.add(name)
                log.append((s.minute, name))
    log.sort()
    return log


def area(snaps: List[Snap], attr: str, start: int = 1, end: int = GAME_MINUTES) -> float:
    return sum(getattr(s, attr) for s in snaps if start <= s.minute <= end)


@dataclass
class PathRun:
    label: str
    path: List[str]
    snaps: List[Snap] = field(default_factory=list)

    @property
    def total(self) -> float:
        return area(self.snaps, "score")

    @property
    def comet(self) -> float:
        return area(self.snaps, "comet60")

    @property
    def hits(self) -> float:
        return area(self.snaps, "hits")

    @property
    def stacks_end(self) -> float:
        return self.snaps[-1].stacks

    @property
    def rylai_min(self) -> int:
        return sum(1 for s in self.snaps if s.rylai)


def named_contrast_paths() -> List[List[str]]:
    return [
        HEAD_RYLAI + ["Void Staff", "Horizon Focus", "Blackfire Torch", "Rabadon's Deathcap"],
        HEAD_RYLAI + ["Void Staff", "Horizon Focus", "Infinity Orb", "Rabadon's Deathcap"],
        HEAD_RYLAI + ["Void Staff", "Horizon Focus", "Luden's Echo", "Rabadon's Deathcap"],
        HEAD_RYLAI + ["Cryptbloom", "Horizon Focus", "Blackfire Torch", "Rabadon's Deathcap"],
        HEAD_RYLAI + ["Blackfire Torch", "Void Staff", "Horizon Focus", "Rabadon's Deathcap"],
        HEAD_BF + ["Rylai's Crystal Scepter", "Void Staff", "Horizon Focus", "Rabadon's Deathcap"],
        HEAD_BF + ["Rylai's Crystal Scepter", "Cryptbloom", "Infinity Orb", "Horizon Focus"],
        HEAD_BF + ["Rylai's Crystal Scepter", "Cryptbloom", "Infinity Orb", "Rabadon's Deathcap"],
        HEAD_BF + ["Void Staff", "Horizon Focus", "Rylai's Crystal Scepter", "Rabadon's Deathcap"],
        HEAD_BF + ["Cryptbloom", "Horizon Focus", "Rylai's Crystal Scepter", "Rabadon's Deathcap"],
        HEAD_BF + ["Cryptbloom", "Horizon Focus", "Infinity Orb", "Rabadon's Deathcap"],
        HEAD_BF + ["Infinity Orb", "Rabadon's Deathcap", "Void Staff", "Horizon Focus"],
        HEAD_LUDEN + ["Horizon Focus", "Blackfire Torch", "Cryptbloom", "Rabadon's Deathcap"],
        HEAD_LUDEN + ["Rylai's Crystal Scepter", "Void Staff", "Horizon Focus", "Rabadon's Deathcap"],
        HEAD_LUDEN + ["Horizon Focus", "Cryptbloom", "Rylai's Crystal Scepter", "Rabadon's Deathcap"],
        HEAD_LIANDRY + ["Rylai's Crystal Scepter", "Void Staff", "Horizon Focus", "Rabadon's Deathcap"],
        HEAD_BF + ["Stormsurge", "Infinity Orb", "Rabadon's Deathcap", "Void Staff"],
        HEAD_BF + ["Rylai's Crystal Scepter", "Cosmic Drive", "Horizon Focus", "Rabadon's Deathcap"],
    ]


def search_paths() -> Iterable[List[str]]:
    heads = [
        (HEAD_BF, "Blackfire Torch"),
        (HEAD_LUDEN, "Luden's Echo"),
        (HEAD_LIANDRY, "Liandry's Torment"),
        (HEAD_RYLAI, "Rylai's Crystal Scepter"),
    ]
    seen = set()
    for head, first in heads:
        rest = [x for x in POOL if x != first]
        for combo in combinations(rest, 4):
            if not valid_tail([first], combo):
                continue
            for tail in permutations(combo):
                path = head + list(tail)
                key = tuple(
                    n for n in path if n in LEGENDARIES or n == "Spellslinger's Shoes"
                )
                if key in seen:
                    continue
                seen.add(key)
                yield path


def run_all() -> List[PathRun]:
    runs: List[PathRun] = []
    seen_labels = set()
    for path in search_paths():
        label = path_label(path)
        if label in seen_labels:
            continue
        seen_labels.add(label)
        runs.append(PathRun(label, path, run_path(path)))
    return runs


def contrast_runs() -> List[PathRun]:
    return [PathRun(path_label(p), p, run_path(p)) for p in named_contrast_paths()]


def summarize(all_runs: List[PathRun], contrasts: List[PathRun]) -> str:
    ranked = sorted(
        all_runs, key=lambda r: (r.total, r.stacks_end, r.hits), reverse=True,
    )
    best = ranked[0]
    by_label = {r.label: r for r in ranked}
    for c in contrasts:
        by_label.setdefault(c.label, c)

    L: List[str] = []
    L.append("=" * 80)
    L.append("MORGANA COMET FARM — TỪ ĐẦU TỚI CUỐI  (Wild Rift 7.2e)")
    L.append("Mid. W-max. Arcane Comet. 30 phút. 6 slot = Spellslinger + 5 legendary.")
    L.append("Stack cộng dồn từ comet TRÚNG. Không khóa core, không cấm món.")
    L.append("=" * 80)
    L.append("")
    L.append("GIẢ ĐỊNH (không phải khóa 4 ô)")
    L.append("-" * 80)
    L.append("  Client : Tốc Chiến 7.2e. Comet 15–100 + 2×hit + 5% AP, CD 16–8s")
    L.append("           (AH không giảm). Delay 0.8s. 1 stack / comet trúng ≥1 tướng.")
    L.append("           Patch 7.2: AP 20%→5%, stack 3→2. Gathering Storm + Transcendence.")
    L.append("  Role   : mid farmer. Tome start, không đồ support, không bán slot.")
    L.append("  Search : mọi 5-legendary sau BF / Luden / Liandry / Rylai. Crypt XOR Void.")
    L.append("  Metric : Σ comet60 phút 1–30 (0.75 poke 90% HP + 0.25 <35% Orb).")
    L.append("           Hits = (60/CD × uptime lane + fight) × P(trúng delay).")
    L.append("           Echo/Squall/R không phải Comet. Q+W kit không xếp hạng.")
    L.append("  Trúng  : Q root 96%. Rylai + Q 60%/walk 84%. Không Rylai Q 45%/walk 48%.")
    L.append("  Pen 7.2: Spellslinger 18+8%, Crypt 30%, Void 40%, Bloodletter shred 30%.")
    L.append("           HF / Rylai / Cap = 0% pen.")
    L.append("")

    L.append("-" * 80)
    L.append("BUILD ORDER — winner")
    L.append("-" * 80)
    L.append(f"  {best.label}")
    L.append("  0:00  Amplifying Tome → Boots of Speed → Boots of Mana")
    for minute, name in purchase_log(best.snaps):
        L.append(f"  {minute:>2}:00  {name}")
    L.append("  Mid không mua đồ support. Slot 6 = legendary, không phải sell-back.")
    L.append("")

    L.append("-" * 80)
    L.append("TOP 12 — Σ comet damage phút 1–30 (farm stack × sát thương / hit)")
    L.append("-" * 80)
    L.append(
        f"  {'Path':<52} {'Σcomet':>8} {'hits':>7} {'stk30':>6} {'rylai':>5}  vs#1"
    )
    for r in ranked[:12]:
        L.append(
            f"  {r.label:<52} {r.total:8.0f} {r.hits:7.1f} {r.stacks_end:6.1f} "
            f"{r.rylai_min:5d}  {pct(r.total, best.total)}"
        )
    L.append(f"  … searched {len(ranked)} full 5-item paths")
    L.append("")

    L.append("-" * 80)
    L.append("ĐỐI CHỨNG (build người chơi hay hỏi)")
    L.append("-" * 80)
    seen = set()
    for r in contrasts:
        if r.label in seen:
            continue
        seen.add(r.label)
        live = by_label.get(r.label, r)
        L.append(
            f"  {live.label:<52} {live.total:7.0f}  stacks {live.stacks_end:5.1f}  "
            f"rylai {live.rylai_min:2d}/30  {pct(live.total, best.total)}"
        )
    L.append("")

    L.append("-" * 80)
    L.append("MINUTE-BY-MINUTE — winner (mỗi 2 phút)")
    L.append("-" * 80)
    for s in best.snaps:
        if s.minute % 2 != 0 and s.minute not in (1, 9, 11, 15, 21, 25):
            continue
        L.append(
            f"  {s.minute:>2}:00 | comet60 {s.comet60:7.0f} | hit {s.comet_hit:6.0f} | "
            f"stacks {s.stacks:5.1f} | land {100*s.land:4.0f}% | "
            f"AP {s.ap:6.0f} AH {s.ah:4.0f}"
        )
        L.append(f"         {short_items(s.items)}")
    L.append("")

    L.append("-" * 80)
    L.append("STACKS — farm Comet từ phút 1 (không cap thấp; game thật ~40–60)")
    L.append("-" * 80)
    keys = [
        best.label,
        "Rylai → Void → HF → BF → Cap",
        "Rylai → Void → HF → Orb → Cap",
        "BF → Rylai → Void → HF → Cap",
        "BF → Rylai → Crypt → Orb → HF",
        "Luden → HF → BF → Crypt → Cap",
        "BF → Crypt → HF → Orb → Cap",
        "BF → Orb → Cap → Void → HF",
        "Luden → Rylai → Void → HF → Cap",
        "Liandry → Rylai → Void → HF → Cap",
        "BF → Storm → Orb → Cap → Void",
    ]
    L.append(f"  {'Path':<52} {'s8':>6} {'s12':>6} {'s20':>6} {'s30':>6} {'ryl':>5}")
    shown = set()
    for lab in [best.label] + keys:
        r = by_label.get(lab)
        if r is None or lab in shown:
            continue
        shown.add(lab)
        L.append(
            f"  {r.label:<52} {r.snaps[7].stacks:6.1f} {r.snaps[11].stacks:6.1f} "
            f"{r.snaps[19].stacks:6.1f} {r.snaps[29].stacks:6.1f} {r.rylai_min:5d}"
        )
    L.append("  Stack sớm hơn → mỗi comet sau đó +2 dmg. 5% AP không đuổi kịp.")
    L.append("")

    L.append("-" * 80)
    L.append("SPIKE 8 / 12 / 20 / 30 — comet60")
    L.append("-" * 80)
    L.append(f"  {'Path':<52} {'8':>7} {'12':>7} {'20':>7} {'30':>7}")
    for r in ranked[:8]:
        L.append(
            f"  {r.label:<52} {r.snaps[7].comet60:7.0f} {r.snaps[11].comet60:7.0f} "
            f"{r.snaps[19].comet60:7.0f} {r.snaps[29].comet60:7.0f}"
        )
    L.append("")

    def starts(prefix: str) -> Optional[PathRun]:
        for r in ranked:
            if r.label.startswith(prefix):
                return r
        return None

    rylai_at = first_item(best.snaps, "Rylai's Crystal Scepter")
    void_at = first_item(best.snaps, "Void Staff")
    crypt_at = first_item(best.snaps, "Cryptbloom")
    hf_at = first_item(best.snaps, "Horizon Focus")
    cluster = [r for r in ranked if r.total >= best.total * 0.99]
    done5 = next((s.minute for s in best.snaps if s.legendaries >= 5), 30)
    luden = starts("Luden →")
    bf = starts("BF →")
    liandry = starts("Liandry →")
    rylai_h = starts("Rylai →")
    no_rylai = max(
        (r for r in ranked if r.rylai_min == 0),
        key=lambda r: r.total,
        default=None,
    )
    late_rylai = by_label.get("BF → Crypt → HF → Rylai → Cap")
    dh_win = by_label.get("BF → Rylai → Crypt → Orb → HF")
    old_luden = by_label.get("Luden → HF → BF → Crypt → Cap")
    burst = by_label.get("BF → Orb → Cap → Void → HF") or by_label.get(
        "BF → Storm → Orb → Cap → Void"
    )
    cosmic = by_label.get("BF → Rylai → Cosmic → HF → Cap")

    L.append("-" * 80)
    L.append("VERDICT")
    L.append("-" * 80)
    L.append(f"  Full build: Spellslinger · {best.label.replace(' → ', ' · ')}")
    L.append(
        f"  Σ1–30 comet {best.total:.0f} | hits {best.hits:.1f} | "
        f"stacks @30 {best.stacks_end:.1f} | Rylai {best.rylai_min}/30 phút"
        f"{f' (lần đầu {rylai_at}:00)' if rylai_at else ''}"
    )
    L.append(
        f"  5 legendary xong phút {done5} "
        f"(không bán support — mid không mua Frostfang)."
    )
    if len(cluster) > 1:
        L.append(
            f"  Cụm ≤1%: {', '.join(r.label for r in cluster[:6])}"
            + ("…" if len(cluster) > 6 else "")
        )
    L.append("")
    L.append("  TẠI SAO FARM COMET + SÁT THƯƠNG COMET CHỌN PATH NÀY:")
    L.append("  • 7.2 cắt AP Comet xuống 5%. 100 AP = +5 raw. 1 stack = +2 raw")
    L.append("    suốt phần còn lại của trận. Farm trúng > mua AP.")
    L.append("  • CD 16–8s không ăn AH. Spam Q / Cosmic / Crimson không thêm proc.")
    L.append("    Trần proc = 60/CD. Cửa thắt là delay 0.8s — Q root hoặc Rylai.")
    L.append("  • W tick / burn vẫn TRIGGER comet khi Q hụt. Projectile mới miss.")
    if rylai_at:
        L.append(
            f"  • Rylai phút {rylai_at}:00 nâng P(trúng) ~70%→91%. Đó là farm stack."
        )
    if best.snaps[-1].land >= 0.85:
        L.append(
            f"  • Winner land {100*best.snaps[-1].land:.0f}% sau Rylai "
            f"({best.stacks_end:.0f} stacks @30)."
        )
    if rylai_h and bf and rylai_h.label == best.label:
        L.append(
            f"  • Rylai-first (best {rylai_h.label}) vs best BF-first "
            f"{bf.label} {pct(bf.total, best.total)}. "
            f"Stack từ ~8:00, không chờ 14:00."
        )
    elif rylai_h and bf:
        L.append(
            f"  • Best Rylai-first {rylai_h.label} {pct(rylai_h.total, best.total)}."
        )
        L.append(f"  • Best BF-first {bf.label} {pct(bf.total, best.total)}.")
    if void_at and crypt_at is None:
        L.append(
            f"  • Void phút {void_at}:00 — 40% pen nhân cả base+stack. "
            f"Crypt 30%+20 AH thua vì AH không giảm CD Comet."
        )
    elif crypt_at and void_at is None:
        L.append(
            f"  • Crypt phút {crypt_at}:00. 30% pen + 20 AH; AH không proc thêm Comet."
        )
    if hf_at:
        L.append(
            f"  • HF phút {hf_at}:00: Q mark → comet đáp 0.8s sau, +10%. "
            f"25 AH không thêm stack."
        )
    if no_rylai:
        L.append(
            f"  • Best không Rylai {no_rylai.label} {pct(no_rylai.total, best.total)}, "
            f"stacks {no_rylai.stacks_end:.1f} vs {best.stacks_end:.1f}."
        )
    if late_rylai:
        L.append(
            f"  • Rylai sau Crypt+HF {pct(late_rylai.total, best.total)} — "
            f"stack muộn, Comet yếu cả trận."
        )
    if dh_win:
        L.append(
            f"  • Winner farm DH (BF→Rylai→Crypt→Orb→HF) {pct(dh_win.total, best.total)} "
            f"trên metric Comet. Crypt/Orb là cửa DH, không phải 5% AP Comet."
        )
    if old_luden:
        L.append(
            f"  • Core Luden max-DPM cũ (Luden→HF→BF→Crypt, bỏ vàng) "
            f"{pct(old_luden.total, best.total)}. Echo không phải Comet; "
            f"không Rylai = miss delay."
        )
    if luden:
        L.append(
            f"  • Best Luden-first {luden.label} {pct(luden.total, best.total)}. "
            f"Echo không trigger Comet."
        )
    if liandry:
        L.append(
            f"  • Best Liandry-first {liandry.label} {pct(liandry.total, best.total)}. "
            f"2% HP không vào Comet; Liandry chỉ giúp trigger (đã đủ từ W)."
        )
    if burst:
        L.append(
            f"  • Rush Orb/Cap/Storm {pct(burst.total, best.total)}. "
            f"Orb 20% tắt ở 90% poke; Storm Squall không phải Comet."
        )
    if cosmic:
        L.append(
            f"  • Cosmic Drive (AH) {pct(cosmic.total, best.total)} — "
            f"AH không farm Comet."
        )
    legs_now = [n for n in best.snaps[-1].items if n in LEGENDARIES]
    if "Infinity Orb" in legs_now:
        L.append(
            "  • Orb: 15 flat + 110 AP. 20% chỉ khi chip ≤35% (25% metric). "
            "Không phải lý do mua sớm."
        )
    if "Rabadon's Deathcap" in legs_now:
        L.append(
            "  • Cap 30% AP gồm GS. 5% của đó ≈ 3–5 extra Comet. Mua sau pen + Rylai."
        )
    L.append("")
    L.append("  CHƠI:")
    L.append("  • Lane: W wave sao cho mid dẫm pool. Comet bắn dù Q hụt.")
    L.append("  • Q khi họ bước vào — root 2s > delay 0.8s = stack chắc.")
    L.append("  • Rylai xong: thả W dưới chân, Comet farm không cần aim Q.")
    L.append("  • Đừng spam Q vì AH. Trần là CD Comet. Đừng delay Rylai để rush Cap.")
    L.append("  • Đừng mua 2 Lost Chapter. Echo không phải Comet.")
    L.append("=" * 80)
    return "\n".join(L)


def export_json(ranked: List[PathRun], path: str) -> None:
    top = ranked[:25]
    payload = {
        "meta": {
            "champion": "Morgana",
            "role": "mid",
            "patch": "7.2e",
            "game_minutes": GAME_MINUTES,
            "playstyle": "farm Arcane Comet from minute 1 to 30",
            "comet": "15-100 + 2*hits + 5% AP, CD 16-8s, 0.8s delay, 1 stack per landing",
            "metric": "comet60 mix 75% @90% HP + 25% @32% HP",
            "pen_7_2": "Spellslinger / Crypt / Void / Bloodletter only",
            "paths_searched": len(ranked),
        },
        "winner": ranked[0].label if ranked else None,
        "ranking": [
            {
                "label": r.label,
                "comet_1_30": round(r.total, 1),
                "hits_1_30": round(r.hits, 2),
                "stacks_30": round(r.stacks_end, 2),
                "rylai_minutes": r.rylai_min,
                "items_30": r.snaps[-1].items,
                "spikes": {
                    "m8": round(r.snaps[7].comet60, 1),
                    "m12": round(r.snaps[11].comet60, 1),
                    "m20": round(r.snaps[19].comet60, 1),
                    "m30": round(r.snaps[29].comet60, 1),
                },
            }
            for r in top
        ],
        "winner_timeline": [
            {
                "minute": s.minute,
                "items": s.items,
                "ap": round(s.ap, 1),
                "ah": round(s.ah, 1),
                "stacks": round(s.stacks, 2),
                "land": round(s.land, 4),
                "hits": round(s.hits, 3),
                "comet_hit": round(s.comet_hit, 1),
                "comet60": round(s.comet60, 1),
                "legendaries": s.legendaries,
            }
            for s in ranked[0].snaps
        ],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def self_check(ranked: List[PathRun], contrasts: List[PathRun]) -> None:
    assert ranked, "search returned no paths"
    best = ranked[0]
    assert best.stacks_end > best.snaps[7].stacks + 8, (
        "stacks must grow from early to late",
        best.snaps[7].stacks,
        best.stacks_end,
    )
    assert best.rylai_min >= 12, best.rylai_min
    assert "Spellslinger's Shoes" in best.snaps[-1].items
    assert all(
        "Shard" not in n and "Frostfang" not in n and "Sickle" not in n
        for n in best.snaps[-1].items
    )
    crypt_void = [
        r for r in ranked
        if "Cryptbloom" in r.snaps[-1].items and "Void Staff" in r.snaps[-1].items
    ]
    assert not crypt_void, "Crypt + Void must be exclusive"
    for s in best.snaps:
        if s.minute < 10:
            assert "Spellslinger's Shoes" not in s.items, s.minute
    assert best.snaps[-1].legendaries >= 4, best.snaps[-1].legendaries
    no_rylai = [r for r in ranked if r.rylai_min == 0]
    if no_rylai:
        worst_land = max(no_rylai, key=lambda r: r.total)
        assert worst_land.stacks_end < best.stacks_end - 4, (
            worst_land.label,
            worst_land.stacks_end,
            best.stacks_end,
        )
        assert worst_land.total < best.total, (worst_land.total, best.total)
    # Rylai on → land_p jumps
    before = next((s for s in best.snaps if not s.rylai), None)
    after = next((s for s in best.snaps if s.rylai), None)
    if before and after:
        assert after.land > before.land + 0.10, (before.land, after.land)
    # 5% AP: extra AP cannot beat missing stacks by a huge margin
    st0 = Stats([], 0, 0, 0, 0, 0, False, False, False, False, False, False)
    st1 = Stats([], 400, 0, 0, 0, 0, False, False, False, False, False, False)
    assert comet_raw(st1.ap, 15, 0) - comet_raw(st0.ap, 15, 0) == 20.0
    assert comet_raw(0, 15, 10) - comet_raw(0, 15, 0) == 20.0
    by = {r.label: r for r in contrasts}
    storm = next((r for r in contrasts if "Storm" in r.label), None)
    if storm:
        assert storm.total < best.total, (storm.total, best.total)


def main() -> None:
    print("Searching 5-legendary Comet-farm paths...", flush=True)
    ranked = sorted(
        run_all(), key=lambda r: (r.total, r.stacks_end, r.hits), reverse=True,
    )
    contrasts = contrast_runs()
    self_check(ranked, contrasts)
    report = summarize(ranked, contrasts)
    print(report)
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, "report.txt"), "w", encoding="utf-8") as f:
        f.write(report + "\n")
    export_json(ranked, os.path.join(OUT_DIR, "results.json"))
    print(f"\nWrote {OUT_DIR}/report.txt and {OUT_DIR}/results.json")
    print(f"Winner: {ranked[0].label}  ({len(ranked)} paths)")


if __name__ == "__main__":
    main()
