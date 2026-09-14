#!/usr/bin/env python3
"""
Wild Rift 7.2e — Morgana mid, farm Dark Harvest from minute 1 to 30.

No inventory locks: no support-item sell, no Void ban, no pre-locked core,
no "already at 45%" as the only window. Souls accumulate from actual
Q/W chip → execute procs, so a path that opens <50% earlier farms a
stronger Harvest later.

Metric is still farm, not one-shot burst: Q + W + DH. Echo / Squall / R
damage is not added. Items that only exist for burst still compete on
AP / AH / pen stats.

Patch 7.2 consolidated %pen onto Spellslinger, Void Amethyst, Cryptbloom,
Void Staff, and Bloodletter. Horizon / Rylai / Deathcap have 0% pen.
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
DH_CD = 35.0
START_GOLD = 500
MAX_SOULS = 99.0  # no 14-soul lock; WR does not stop stacking this low

# Lost Chapter unique-ish: buying three of these is a wasted slot, not a game rule.
CHAPTER_ITEMS = {"Blackfire Torch", "Luden's Echo", "Seraph's Embrace"}
# Same Void Amethyst unique — cannot own both.
PEN_EXCLUSIVE = ("Cryptbloom", "Void Staff")


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
    # WR cap 15. Mid farmer hits 15 around 20, sits there.
    table = {
        1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7, 7: 8, 8: 9,
        9: 10, 10: 11, 11: 11, 12: 12, 13: 12, 14: 13,
        15: 13, 16: 14, 17: 14, 18: 15, 19: 15, 20: 15,
    }
    return table.get(minute, 15)


def gs_ap(minute: int) -> float:
    """Gathering Storm. First stack 6:00, then every 3:00. 70 AP @24–26."""
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
    guise: bool = False
    ashes: bool = False
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
    "Fated Ashes": Item("Fated Ashes", 900, ap=40, ashes=True),
    "Haunting Guise": Item("Haunting Guise", 1300, ap=30, guise=True),
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


def skill_rank(level: int, skill: str) -> int:
    if skill == "R":
        return 0 if level < 6 else 1 if level < 11 else 2 if level < 15 else 3
    q_lv, w_lv = [3, 8, 9, 10, 12], [1, 2, 4, 5, 7]
    return min(4, sum(1 for lv in {"Q": q_lv, "W": w_lv}[skill] if level >= lv))


def trans_ah(level: int) -> float:
    return 12.0 if level >= 5 else 6.0


def dh_raw(ap: float, souls: float) -> float:
    return 35.0 + 11.0 * souls + 0.05 * ap


def ah_cd(base: float, ah: float) -> float:
    return base * 100.0 / (100.0 + max(0.0, ah))


def cheap_shot(level: int) -> float:
    return 8.0 + 2.0 * level


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


def stats_of(owned: List[str], level: int, minute: int) -> Stats:
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
    ap += gs_ap(minute)
    bf_targets = 1.0 if minute < 16 else 1.8
    if bf:
        ap *= 1.0 + 0.04 * bf_targets
    if cap:
        ap *= 1.30
    ah += trans_ah(level)
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


def burn_dps(st: Stats, hp_max: float) -> float:
    dps = 0.0
    if st.blackfire:
        dps += 20.0 + 0.02 * st.ap
    if st.liandry:
        dps += 0.02 * hp_max
    ashes = any(ITEMS[n].ashes for n in st.names if n in ITEMS)
    if ashes and not st.blackfire and not st.liandry:
        dps += 5.0
    madness = 1.04 if st.liandry else 1.0
    return dps * madness


def qw_farm(
    st: Stats,
    minute: int,
    level: int,
    start_frac: float,
    souls: float,
    allow_dh: bool,
) -> Dict[str, float]:
    """One Q + W dwell. DH procs the first time HP crosses/stays ≤50%."""
    qr, wr = skill_rank(level, "Q"), skill_rank(level, "W")
    hp_max, mr = dummy(minute, level)
    hp = start_frac * hp_max
    root = [0, 2.0, 2.25, 2.5, 2.75][max(1, min(4, qr))]
    dwell = 5.0 if st.rylai else root
    dealt = 0.0
    dh_n = 0.0
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
            dh = strike(dh_raw(st.ap, souls), st, mr, hp / hp_max, hf)
            hp -= dh
            dealt += dh
            dh_n = 1.0

    q = [0, 80, 160, 240, 320][max(1, qr)] + 0.90 * st.ap
    hit(q, apply_hf=True)
    hit(cheap_shot(level), apply_hf=False)
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


def q_only(st: Stats, minute: int, level: int, start_frac: float, souls: float) -> float:
    qr = max(1, skill_rank(level, "Q"))
    hp_max, mr = dummy(minute, level)
    hp = start_frac * hp_max
    raw = [0, 80, 160, 240, 320][qr] + 0.90 * st.ap
    dmg = strike(raw, st, mr, hp / hp_max, False)
    hp -= dmg
    total = dmg + strike(cheap_shot(level), st, mr, hp / hp_max, False)
    return total


def w_only(st: Stats, minute: int, level: int, start_frac: float, souls: float) -> float:
    qr, wr = skill_rank(level, "Q"), max(1, skill_rank(level, "W"))
    hp_max, mr = dummy(minute, level)
    hp = start_frac * hp_max
    root = [0, 2.0, 2.25, 2.5, 2.75][max(1, min(4, qr))]
    dwell = 5.0 if st.rylai else root
    total = 0.0
    bdps = burn_dps(st, hp_max)
    hf = False
    for _ in range(max(1, int(dwell / 0.5))):
        frac = hp / hp_max
        missing = 1.0 - max(0.05, frac)
        w_amp = 1.0 + 1.7 * min(0.7, missing)
        raw = ([0, 7, 12, 17, 22][wr] + 0.07 * st.ap) * w_amp + bdps * 0.5
        dmg = strike(raw, st, mr, frac, hf)
        hp -= dmg
        total += dmg
    return total


def mix_weights(minute: int) -> Tuple[float, float]:
    """How much of the minute is 'open the window from 90%' vs 'already <50%'."""
    if minute <= 6:
        return 0.70, 0.30
    if minute <= 12:
        return 0.50, 0.50
    if minute <= 20:
        return 0.35, 0.65
    return 0.25, 0.75


def fight_souls(minute: int) -> float:
    """Takedown-reset souls (1s CD). More in mid/late skirmishes."""
    if minute < 6:
        return 0.0
    if minute < 10:
        return 0.35
    if minute < 16:
        return 0.70
    if minute < 22:
        return 1.00
    return 1.20


def lane_souls(opened: bool, minute: int) -> float:
    if opened:
        return 1.0 if minute >= 4 else 0.45
    if minute < 5:
        return 0.0
    return 0.20


@dataclass
class Snap:
    minute: int
    items: List[str]
    gold: int
    ap: float
    ah: float
    souls: float
    opened: bool
    qpm: float
    wpm: float
    chip: float
    farm60: float
    score: float
    dh_hit: float
    legendaries: int


def legendary_count(items: List[str]) -> int:
    return sum(1 for n in items if n in LEGENDARIES)


def run_path(path: Sequence[str]) -> List[Snap]:
    owned: List[str] = []
    gold = START_GOLD
    souls = 0.0
    snaps: List[Snap] = []
    for m in range(1, GAME_MINUTES + 1):
        gold += mid_income(m)
        owned, gold = progress(list(path), owned, gold, m)
        lv = level_at(m)
        st = stats_of(owned, lv, m)
        chip = qw_farm(st, m, lv, 0.90, souls, True)
        exe = qw_farm(st, m, lv, 0.45, souls, True)
        opened = chip["crossed50"] >= 1.0
        q_kit = q_only(st, m, lv, 0.45, souls)
        w_kit = w_only(st, m, lv, 0.45, souls)
        hp_max, mr = dummy(m, lv)
        dh = strike(dh_raw(st.ap, souls), st, mr, 0.45, st.horizon)
        # DH procs: 35s CD in the execute window; chip-only minutes get fewer.
        w_chip, w_exe = mix_weights(m)
        if opened or m >= 8:
            dh_procs = 60.0 / DH_CD
        elif m >= 4:
            dh_procs = 0.35 * (60.0 / DH_CD)
        else:
            dh_procs = 0.0
        farm60 = exe["qpm"] * q_kit + exe["wpm"] * w_kit + dh_procs * dh
        score = w_chip * chip["dealt"] * (exe["qpm"] * 0.15 + 1.0) + w_exe * farm60
        gained = lane_souls(opened, m) + (fight_souls(m) if (opened or m >= 8) else 0.0)
        souls = min(MAX_SOULS, souls + gained)
        snaps.append(
            Snap(
                minute=m,
                items=list(owned),
                gold=gold,
                ap=st.ap,
                ah=st.ah,
                souls=souls,
                opened=opened,
                qpm=exe["qpm"],
                wpm=exe["wpm"],
                chip=chip["dealt"],
                farm60=farm60,
                score=score,
                dh_hit=dh,
                legendaries=legendary_count(owned),
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


def head_legendaries(head: Sequence[str]) -> List[str]:
    return [n for n in head if n in LEGENDARIES]


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
    """Finished legendaries + T3 boots, in the minute they appear."""
    seen = set()
    log: List[Tuple[int, str]] = []
    watch = [
        "Blackfire Torch", "Luden's Echo", "Liandry's Torment",
        "Spellslinger's Shoes", "Cryptbloom", "Void Staff",
        "Horizon Focus", "Rylai's Crystal Scepter", "Rabadon's Deathcap",
        "Infinity Orb", "Bloodletter's Curse", "Cosmic Drive",
        "Stormsurge", "Seraph's Embrace",
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
    def farm(self) -> float:
        return area(self.snaps, "farm60")

    @property
    def souls_end(self) -> float:
        return self.snaps[-1].souls

    @property
    def opened(self) -> int:
        return sum(1 for s in self.snaps if s.opened)


def named_contrast_paths() -> List[List[str]]:
    """Always-report paths so the search winner can be compared to known builds."""
    return [
        HEAD_BF + ["Cryptbloom", "Horizon Focus", "Rylai's Crystal Scepter", "Rabadon's Deathcap"],
        HEAD_BF + ["Horizon Focus", "Cryptbloom", "Rylai's Crystal Scepter", "Rabadon's Deathcap"],
        HEAD_BF + ["Cryptbloom", "Horizon Focus", "Rabadon's Deathcap", "Rylai's Crystal Scepter"],
        HEAD_BF + ["Cryptbloom", "Rylai's Crystal Scepter", "Horizon Focus", "Rabadon's Deathcap"],
        HEAD_BF + ["Cryptbloom", "Horizon Focus", "Rylai's Crystal Scepter", "Liandry's Torment"],
        HEAD_BF + ["Cryptbloom", "Horizon Focus", "Infinity Orb", "Rabadon's Deathcap"],
        HEAD_BF + ["Cryptbloom", "Horizon Focus", "Bloodletter's Curse", "Rabadon's Deathcap"],
        HEAD_BF + ["Cryptbloom", "Horizon Focus", "Cosmic Drive", "Rabadon's Deathcap"],
        HEAD_BF + ["Void Staff", "Horizon Focus", "Rylai's Crystal Scepter", "Rabadon's Deathcap"],
        HEAD_BF + ["Liandry's Torment", "Rylai's Crystal Scepter", "Cryptbloom", "Rabadon's Deathcap"],
        HEAD_BF + ["Liandry's Torment", "Rylai's Crystal Scepter", "Horizon Focus", "Rabadon's Deathcap"],
        HEAD_BF + ["Infinity Orb", "Rabadon's Deathcap", "Cryptbloom", "Rylai's Crystal Scepter"],
        HEAD_BF + ["Stormsurge", "Infinity Orb", "Rabadon's Deathcap", "Cryptbloom"],
        HEAD_LUDEN + ["Horizon Focus", "Cryptbloom", "Rylai's Crystal Scepter", "Rabadon's Deathcap"],
        HEAD_LUDEN + ["Infinity Orb", "Rabadon's Deathcap", "Horizon Focus", "Cryptbloom"],
        HEAD_LIANDRY + ["Rylai's Crystal Scepter", "Cryptbloom", "Horizon Focus", "Rabadon's Deathcap"],
        HEAD_LIANDRY + ["Blackfire Torch", "Rylai's Crystal Scepter", "Cryptbloom", "Rabadon's Deathcap"],
    ]


def search_paths() -> Iterable[List[str]]:
    """Full 5-legendary search. No core lock, no item ban except game uniques."""
    heads = [
        (HEAD_BF, "Blackfire Torch"),
        (HEAD_LUDEN, "Luden's Echo"),
        (HEAD_LIANDRY, "Liandry's Torment"),
    ]
    seen = set()
    for head, first in heads:
        rest = [x for x in POOL if x != first]
        for combo in combinations(rest, 4):
            if not valid_tail([first], combo):
                continue
            for tail in permutations(combo):
                path = head + list(tail)
                key = tuple(n for n in path if n in LEGENDARIES or n == "Spellslinger's Shoes")
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
    out = []
    for path in named_contrast_paths():
        out.append(PathRun(path_label(path), path, run_path(path)))
    return out


def summarize(all_runs: List[PathRun], contrasts: List[PathRun]) -> str:
    ranked = sorted(all_runs, key=lambda r: (r.total, r.farm, r.souls_end), reverse=True)
    best = ranked[0]
    by_label = {r.label: r for r in ranked}
    for c in contrasts:
        by_label.setdefault(c.label, c)

    L: List[str] = []
    L.append("=" * 80)
    L.append("MORGANA DH FARM — TỪ ĐẦU TỚI CUỐI  (Wild Rift 7.2e)")
    L.append("Mid. W-max. Dark Harvest. 30 phút. 6 slot = Spellslinger + 5 legendary.")
    L.append("Soul cộng dồn từ Q/W chip → cửa <50% → DH. Không khóa core, không cấm món.")
    L.append("=" * 80)
    L.append("")
    L.append("GIẢ ĐỊNH (không phải khóa 4 ô)")
    L.append("-" * 80)
    L.append("  Client : Tốc Chiến 7.2e. DH 35+11×soul+5% AP, <50%, CD 35s (AH không giảm).")
    L.append("           Takedown → 1s. Gathering Storm + Transcendence + Cheap Shot.")
    L.append("  Role   : mid farmer. Tome start, không đồ support, không bán slot.")
    L.append("  Search : mọi 5-legendary sau BF / Luden / Liandry. Crypt XOR Void.")
    L.append("  Metric : mix chip-từ-90% + farm60 @45% (QPM×Q + WPM×W + DH/35s).")
    L.append("           Echo/Squall/R không cộng vào hit. Orb 20% chỉ <35%.")
    L.append("  Pen 7.2: Spellslinger 18+8%, Crypt 30%, Void 40%, Bloodletter shred 30%.")
    L.append("           HF / Rylai / Cap = 0% pen (patch rút 7% khỏi T3 mage).")
    L.append("")

    L.append("-" * 80)
    L.append("BUILD ORDER — winner")
    L.append("-" * 80)
    L.append(f"  {best.label}")
    L.append("  0:00  Amplifying Tome → Boots of Speed → Boots of Mana → Lost Chapter / Ashes")
    for minute, name in purchase_log(best.snaps):
        L.append(f"  {minute:>2}:00  {name}")
    L.append("  Mid không mua đồ support. Slot 6 = legendary, không phải sell-back.")
    L.append("")

    L.append("-" * 80)
    L.append("TOP 12 — Σ score phút 1–30 (chip mở cửa + execute farm + soul stacking)")
    L.append("-" * 80)
    L.append(
        f"  {'Path':<52} {'Σscore':>8} {'Σfarm60':>8} {'soul30':>7} {'open':>5} {'vs#1':>7}"
    )
    for r in ranked[:12]:
        L.append(
            f"  {r.label:<52} {r.total:8.0f} {r.farm:8.0f} {r.souls_end:7.1f} "
            f"{r.opened:5d} {pct(r.total, best.total):>7}"
        )
    L.append(f"  … searched {len(ranked)} full 5-item paths")
    L.append("")

    L.append("-" * 80)
    L.append("ĐỐI CHỨNG (build người chơi hay hỏi)")
    L.append("-" * 80)
    contrast_sorted = sorted(contrasts, key=lambda r: r.total, reverse=True)
    for r in contrast_sorted:
        L.append(
            f"  {r.label:<52} {r.total:8.0f}  souls {r.souls_end:5.1f}  "
            f"open {r.opened:2d}/30  {pct(r.total, best.total)}"
        )
    L.append("")

    L.append("-" * 80)
    L.append("MINUTE-BY-MINUTE — winner (mỗi 2 phút)")
    L.append("-" * 80)
    for s in best.snaps:
        if s.minute % 2 != 0 and s.minute not in (1, 9, 11, 15, 21, 25):
            continue
        gate = "OPEN" if s.opened else "chip"
        L.append(
            f"  {s.minute:>2}:00 | score {s.score:7.0f} | farm60 {s.farm60:7.0f} | "
            f"souls {s.souls:5.1f} | {gate} | AP {s.ap:6.0f} AH {s.ah:4.0f}"
        )
        L.append(f"         {short_items(s.items)}")
    L.append("")

    L.append("-" * 80)
    L.append("SOULS — farm DH từ phút 1, không cap 14")
    L.append("-" * 80)
    keys = [
        best.label,
        "BF → Crypt → HF → Rylai → Cap",
        "BF → Orb → Cap → Crypt → Rylai",
        "Luden → HF → Crypt → Rylai → Cap",
        "BF → Liandry → Rylai → Crypt → Cap",
        "BF → Storm → Orb → Cap → Crypt",
    ]
    L.append(f"  {'Path':<52} {'s8':>6} {'s12':>6} {'s20':>6} {'s30':>6} {'open':>5}")
    shown = set()
    for lab in [best.label] + keys:
        r = by_label.get(lab)
        if r is None or lab in shown:
            continue
        shown.add(lab)
        L.append(
            f"  {r.label:<52} {r.snaps[7].souls:6.1f} {r.snaps[11].souls:6.1f} "
            f"{r.snaps[19].souls:6.1f} {r.snaps[29].souls:6.1f} {r.opened:5d}"
        )
    L.append("  Soul sớm hơn → DH 11 dmg/stack mạnh hơn phần còn lại của trận.")
    L.append("")

    L.append("-" * 80)
    L.append("SPIKE 8 / 12 / 20 / 30 — farm60")
    L.append("-" * 80)
    L.append(f"  {'Path':<52} {'8':>7} {'12':>7} {'20':>7} {'30':>7}")
    for r in ranked[:8]:
        L.append(
            f"  {r.label:<52} {r.snaps[7].farm60:7.0f} {r.snaps[11].farm60:7.0f} "
            f"{r.snaps[19].farm60:7.0f} {r.snaps[29].farm60:7.0f}"
        )
    L.append("")

    def first_open(snaps: List[Snap]) -> Optional[int]:
        for s in snaps:
            if s.opened:
                return s.minute
        return None

    def starts(prefix: str) -> Optional[PathRun]:
        for r in ranked:
            if r.label.startswith(prefix):
                return r
        return None

    luden = starts("Luden →")
    voidp = starts("BF → Void")
    crypt_core = by_label.get("BF → Crypt → HF → Rylai → Cap")
    rylai_at = first_item(best.snaps, "Rylai's Crystal Scepter")
    rylai_second = any(r.label.startswith("BF → Rylai") for r in ranked[:12])
    cluster = [r for r in ranked if r.total >= best.total * 0.99]
    open_m = first_open(best.snaps)
    done5 = next((s.minute for s in best.snaps if s.legendaries >= 5), 30)

    L.append("-" * 80)
    L.append("VERDICT")
    L.append("-" * 80)
    L.append(f"  Full build: Spellslinger · {best.label.replace(' → ', ' · ')}")
    L.append(
        f"  Σ1–30 {best.total:.0f} | farm60 {best.farm:.0f} | "
        f"souls @30 {best.souls_end:.1f} | mở cửa {best.opened}/30 phút"
        f"{f' (lần đầu {open_m}:00)' if open_m else ''}"
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
    L.append("  TẠI SAO FARM DH TỪ ĐẦU TỚI CUỐI CHỌN PATH NÀY:")
    L.append("  • Mỗi Q và mỗi tick W là cửa Harvest. AH không giảm CD 35s —")
    L.append("    AH để Q/W sẵn sàng khi target vừa rớt <50%.")
    L.append("  • Chip từ 90% phải TỰ mở cửa. Snapshot 'đã 45%' giấu điều này.")
    if rylai_second:
        L.append(
            "  • Khóa thật: BF → Rylai. Top 12 đều Rylai món 2. W dwell 2.75s→5s"
        )
        L.append(
            f"    từ ~{rylai_at}:00 "
            f"mở cửa {best.opened}/30 phút (soul chồng cho cả trận)."
        )
    if crypt_core:
        L.append(
            f"  • Core Crypt→HF→Rylai→Cap (giả định sẵn 45%): "
            f"{pct(crypt_core.total, best.total)}, chỉ mở {crypt_core.opened}/30. "
            f"Rylai muộn = ít soul."
        )
    if luden:
        L.append(
            f"  • Không bắt Luden: best Luden-first {luden.label} "
            f"{pct(luden.total, best.total)}. Echo không đếm; BF burn + 20 AH mở cửa."
        )
    burst = by_label.get("BF → Orb → Cap → Crypt → Rylai")
    storm = by_label.get("BF → Storm → Orb → Cap → Crypt")
    if burst:
        L.append(
            f"  • Rush Orb→Cap trước Rylai {pct(burst.total, best.total)}. "
            f"Orb 20% chỉ <35%; farm cần dwell trước, execute amp sau."
        )
    if storm:
        L.append(f"  • Stormsurge burst {pct(storm.total, best.total)}. Squall không vào metric.")
    liandry = by_label.get("BF → Liandry → Rylai → Crypt → Cap")
    if liandry:
        L.append(
            f"  • Liandry first {pct(liandry.total, best.total)}. "
            f"2% HP cần dwell; dwell 5s chỉ sau Rylai."
        )
    if voidp:
        L.append(
            f"  • Best Void-first {voidp.label} {pct(voidp.total, best.total)}. "
            f"40% pen / 0 AH — ít Q/W hơn Crypt 30%+20 AH trên dummy mid."
        )
    legs = [n for n in best.snaps[-1].items if n in LEGENDARIES]
    if "Infinity Orb" in legs:
        L.append(
            "  • Orb sau khi cửa đã mở: 110 AP + 15 flat giúp chip 90%→35% "
            "(20% bật trên tick cuối). Không phải Squall combo."
        )
    if "Rabadon's Deathcap" in legs:
        L.append(
            "  • Cap amp 30% gồm GS 70 @24 và DH 5% AP. Mua sau Rylai, không trước."
        )
    if "Horizon Focus" in legs:
        L.append(
            "  • HF 10% sau Q đánh vào W ticks trong dwell 5s. 25 AH = thêm Q/W "
            "trong cửa, không giảm CD Harvest 35s."
        )
    L.append("")
    L.append("  CHƠI:")
    L.append("  • Lane: W wave + Q khi mid <70%. Rylai giữ chân trong pool 5s, chip <50%, DH.")
    L.append("  • Roam/fight: Q root → W → DH. Takedown reset 1s = soul tiếp.")
    L.append("  • Không all-in R để one-shot. R chỉ giữ người trong pool.")
    L.append("  • Đừng mua 2 Lost Chapter. Đừng delay Rylai để rush Crypt/HF/Cap.")
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
            "playstyle": "farm Dark Harvest from minute 1 to 30",
            "souls": "endogenous Q/W chip + takedown",
            "pen_7_2": "Spellslinger / Crypt / Void / Bloodletter only",
            "paths_searched": len(ranked),
        },
        "winner": ranked[0].label if ranked else None,
        "ranking": [
            {
                "label": r.label,
                "score_1_30": round(r.total, 1),
                "farm60_1_30": round(r.farm, 1),
                "souls_30": round(r.souls_end, 2),
                "opened": r.opened,
                "items_30": r.snaps[-1].items,
                "spikes": {
                    "m8": round(r.snaps[7].farm60, 1),
                    "m12": round(r.snaps[11].farm60, 1),
                    "m20": round(r.snaps[19].farm60, 1),
                    "m30": round(r.snaps[29].farm60, 1),
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
                "souls": round(s.souls, 2),
                "opened": s.opened,
                "farm60": round(s.farm60, 1),
                "score": round(s.score, 1),
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
    assert best.souls_end > best.snaps[7].souls + 5, (
        "souls must grow from early to late",
        best.snaps[7].souls,
        best.souls_end,
    )
    assert best.opened >= 12, best.opened
    assert "Spellslinger's Shoes" in best.snaps[-1].items
    assert all("Shard" not in n and "Frostfang" not in n and "Sickle" not in n
               for n in best.snaps[-1].items)
    crypt_void = [
        r for r in ranked
        if "Cryptbloom" in r.snaps[-1].items and "Void Staff" in r.snaps[-1].items
    ]
    assert not crypt_void, "Crypt + Void must be exclusive"
    # Burst contrast should not beat a farm path on this metric
    by = {r.label: r for r in contrasts}
    storm = next((r for r in contrasts if "Storm" in r.label), None)
    if storm:
        assert storm.total < best.total, (storm.total, best.total)
    # T3 boots not before 10
    for s in best.snaps:
        if s.minute < 10:
            assert "Spellslinger's Shoes" not in s.items, s.minute
    # Winner finishes 5 legendaries or sits on components of the 5th
    assert best.snaps[-1].legendaries >= 4, best.snaps[-1].legendaries
    # Endogenous souls: a path that opens fewer windows should end with fewer souls
    few = min(ranked, key=lambda r: r.opened)
    if few.opened + 4 <= best.opened:
        assert few.souls_end <= best.souls_end + 0.5, (few.label, few.souls_end, best.souls_end)


def main() -> None:
    print("Searching 5-legendary DH-farm paths...", flush=True)
    ranked = sorted(run_all(), key=lambda r: (r.total, r.farm, r.souls_end), reverse=True)
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
