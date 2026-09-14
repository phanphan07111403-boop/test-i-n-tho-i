#!/usr/bin/env python3
"""
Wild Rift 7.2e — Viktor mid, farm Dark Harvest from minute 1 to 30.

Same method as Morgana: no support-item sell, no Void ban, no pre-locked
core, no "already at 45%" as the only window. Souls accumulate from
actual E/Q chip → execute procs.

Viktor farms with Hextech Ray (laser + Blastquake) and Siphon Power.
E-max. E evolves ~6:00 from hex fragments. Echo / Squall / R are not
added to hits. Items still compete on AP / AH / pen.

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


@dataclass
class Stats:
    names: List[str]
    ap: float
    ah: float
    ad: float
    flat_mpen: float
    pct_mpen: float
    shred: float
    luden: bool
    orb: bool
    horizon: bool
    blackfire: bool
    liandry: bool
    rylai: bool


def skill_rank(level: int, skill: str) -> int:
    if skill == "R":
        return 0 if level < 5 else 1 if level < 9 else 2 if level < 13 else 3
    q_lv, w_lv, e_lv = [3, 8, 10, 11], [7, 12, 14, 15], [1, 2, 4, 6]
    return min(4, sum(1 for lv in {"Q": q_lv, "W": w_lv, "E": e_lv}[skill] if level >= lv))


def trans_ah(level: int) -> float:
    return 12.0 if level >= 5 else 6.0


def dh_raw(ap: float, souls: float) -> float:
    return 35.0 + 11.0 * souls + 0.05 * ap


def ah_cd(base: float, ah: float) -> float:
    return base * 100.0 / (100.0 + max(0.0, ah))


def e_evolved(minute: int) -> bool:
    return minute >= 6


def w_evolved(minute: int) -> bool:
    return minute >= 18


def viktor_ad(level: int) -> float:
    return 54.0 + 3.5 * max(0, level - 1)


def aftershock_land(st: Stats, minute: int) -> float:
    """Blastquake is 1s after the laser. Slow makes it land."""
    p = 0.80
    if w_evolved(minute):
        p += 0.08
    if st.rylai:
        p += 0.12
    return min(0.98, p)


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
        list(owned), ap, ah, viktor_ad(level), flat, pct, shred,
        luden, orb, horizon, bf, li, rylai,
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


def eq_farm(
    st: Stats,
    minute: int,
    level: int,
    start_frac: float,
    souls: float,
    allow_dh: bool,
) -> Dict[str, float]:
    """One E (laser + Blastquake) + Q (blast + discharge AA). DH on first ≤50%."""
    er, qr = skill_rank(level, "E"), skill_rank(level, "Q")
    hp_max, mr = dummy(minute, level)
    hp = start_frac * hp_max
    dealt = 0.0
    dh_n = 0.0
    hf = False
    land = aftershock_land(st, minute)

    def hit(raw: float, apply_hf: bool = False, chance: float = 1.0) -> None:
        nonlocal hp, dealt, dh_n, hf
        if chance <= 0.0:
            return
        frac = hp / hp_max
        dmg = strike(raw, st, mr, frac, hf) * chance
        hp -= dmg
        dealt += dmg
        if apply_hf and st.horizon:
            hf = True
        if allow_dh and dh_n == 0.0 and hp <= 0.50 * hp_max:
            dh = strike(dh_raw(st.ap, souls), st, mr, hp / hp_max, hf)
            hp -= dh
            dealt += dh
            dh_n = 1.0

    laser = [0, 75, 120, 165, 210][max(1, er)] + 0.30 * st.ap
    hit(laser, apply_hf=True)
    if e_evolved(minute):
        shock = [0, 30, 70, 110, 150][max(1, er)] + 0.60 * st.ap
        hit(shock, apply_hf=False, chance=land)
    q_blast = [0, 45, 60, 75, 90][max(1, qr)] + 0.30 * st.ap
    hit(q_blast)
    q_aa = [0, 20, 40, 60, 80][max(1, qr)] + st.ad + 0.40 * st.ap
    hit(q_aa)
    bdps = burn_dps(st, hp_max)
    burn_t = 3.5 if st.rylai else 3.0
    hit(bdps * burn_t)

    e_cd = ah_cd([0, 10, 9, 8, 7][max(1, er)], st.ah)
    q_cd = ah_cd([0, 8, 7, 6, 5][max(1, qr)], st.ah)
    return {
        "dealt": dealt,
        "dh": dh_n,
        "hp_left": max(0.0, hp / hp_max),
        "crossed50": 1.0 if hp <= 0.50 * hp_max or dh_n else 0.0,
        "epm": 60.0 / e_cd,
        "qpm": 60.0 / q_cd,
        "land": land,
        "ap": st.ap,
        "ah": st.ah,
    }


def e_only(st: Stats, minute: int, level: int, start_frac: float) -> float:
    """Laser + expected aftershock + 3s burn. No DH, no Echo."""
    er = max(1, skill_rank(level, "E"))
    hp_max, mr = dummy(minute, level)
    frac = start_frac
    hf = False
    total = 0.0
    laser = [0, 75, 120, 165, 210][er] + 0.30 * st.ap
    total += strike(laser, st, mr, frac, False)
    hf = bool(st.horizon)
    if e_evolved(minute):
        shock = [0, 30, 70, 110, 150][er] + 0.60 * st.ap
        total += strike(shock, st, mr, frac, hf) * aftershock_land(st, minute)
    total += strike(burn_dps(st, hp_max) * (3.5 if st.rylai else 3.0), st, mr, frac, hf)
    return total


def q_only(st: Stats, minute: int, level: int, start_frac: float) -> float:
    qr = max(1, skill_rank(level, "Q"))
    hp_max, mr = dummy(minute, level)
    frac = start_frac
    blast = [0, 45, 60, 75, 90][qr] + 0.30 * st.ap
    aa = [0, 20, 40, 60, 80][qr] + st.ad + 0.40 * st.ap
    return strike(blast, st, mr, frac, False) + strike(aa, st, mr, frac, False)


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
    epm: float
    qpm: float
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
        chip = eq_farm(st, m, lv, 0.90, souls, True)
        exe = eq_farm(st, m, lv, 0.45, souls, True)
        opened = chip["crossed50"] >= 1.0
        e_kit = e_only(st, m, lv, 0.45)
        q_kit = q_only(st, m, lv, 0.45)
        hp_max, mr = dummy(m, lv)
        dh = strike(dh_raw(st.ap, souls), st, mr, 0.45, st.horizon)
        w_chip, w_exe = mix_weights(m)
        if opened or m >= 8:
            dh_procs = 60.0 / DH_CD
        elif m >= 4:
            dh_procs = 0.35 * (60.0 / DH_CD)
        else:
            dh_procs = 0.0
        farm60 = exe["epm"] * e_kit + exe["qpm"] * q_kit + dh_procs * dh
        score = w_chip * chip["dealt"] * (exe["epm"] * 0.12 + 1.0) + w_exe * farm60
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
                epm=exe["epm"],
                qpm=exe["qpm"],
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
        HEAD_LUDEN + ["Infinity Orb", "Rabadon's Deathcap", "Horizon Focus", "Cryptbloom"],
        HEAD_LUDEN + ["Horizon Focus", "Cryptbloom", "Rabadon's Deathcap", "Infinity Orb"],
        HEAD_LUDEN + ["Horizon Focus", "Cryptbloom", "Rylai's Crystal Scepter", "Rabadon's Deathcap"],
        HEAD_LUDEN + ["Infinity Orb", "Horizon Focus", "Cryptbloom", "Rabadon's Deathcap"],
        HEAD_BF + ["Liandry's Torment", "Void Staff", "Horizon Focus", "Rabadon's Deathcap"],
        HEAD_BF + ["Infinity Orb", "Rabadon's Deathcap", "Horizon Focus", "Cryptbloom"],
        HEAD_BF + ["Horizon Focus", "Cryptbloom", "Rylai's Crystal Scepter", "Rabadon's Deathcap"],
        HEAD_BF + ["Cryptbloom", "Horizon Focus", "Rylai's Crystal Scepter", "Rabadon's Deathcap"],
        HEAD_BF + ["Rylai's Crystal Scepter", "Cryptbloom", "Infinity Orb", "Horizon Focus"],
        HEAD_BF + ["Horizon Focus", "Cryptbloom", "Rabadon's Deathcap", "Infinity Orb"],
        HEAD_LIANDRY + ["Rylai's Crystal Scepter", "Blackfire Torch", "Void Staff", "Rabadon's Deathcap"],
        HEAD_BF + ["Stormsurge", "Infinity Orb", "Rabadon's Deathcap", "Cryptbloom"],
        HEAD_LUDEN + ["Cryptbloom", "Horizon Focus", "Rylai's Crystal Scepter", "Rabadon's Deathcap"],
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
    L.append("VIKTOR DH FARM — TỪ ĐẦU TỚI CUỐI  (Wild Rift 7.2e)")
    L.append("Mid. E-max. Dark Harvest. 30 phút. 6 slot = Spellslinger + 5 legendary.")
    L.append("Soul cộng dồn từ E/Q chip → cửa <50% → DH. Không khóa core, không cấm món.")
    L.append("=" * 80)
    L.append("")
    L.append("GIẢ ĐỊNH (không phải khóa 4 ô)")
    L.append("-" * 80)
    L.append("  Client : Tốc Chiến 7.2e. DH 35+11×soul+5% AP, <50%, CD 35s (AH không giảm).")
    L.append("           Takedown → 1s. Gathering Storm + Transcendence.")
    L.append("           E evolve ~6:00 (hex fragments). W evolve ~18:00 (20% slow).")
    L.append("  Role   : mid farmer. Tome start, không đồ support, không bán slot.")
    L.append("  Search : mọi 5-legendary sau BF / Luden / Liandry. Crypt XOR Void.")
    L.append("  Metric : mix chip-từ-90% + farm60 @45% (EPM×E + QPM×Q + DH/35s).")
    L.append("           Laser apply HF; Blastquake 1s sau được amp. Echo/Squall/R không cộng.")
    L.append("           Blastquake land 80% → +12% Rylai / +8% W-evolve.")
    L.append("  Pen 7.2: Spellslinger 18+8%, Crypt 30%, Void 40%, Bloodletter shred 30%.")
    L.append("           HF / Rylai / Cap = 0% pen.")
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
        "Luden → Orb → Cap → HF → Crypt",
        "Luden → HF → Crypt → Cap → Orb",
        "BF → Liandry → Void → HF → Cap",
        "BF → Orb → Cap → HF → Crypt",
        "BF → Rylai → Crypt → Orb → HF",
        "BF → Storm → Orb → Cap → Crypt",
        "Luden → HF → Crypt → Rylai → Cap",
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
    bf_first = starts("BF →")
    voidp = starts("BF → Void")
    diamond = by_label.get("Luden → Orb → Cap → HF → Crypt")
    burn = by_label.get("BF → Liandry → Void → HF → Cap")
    hybrid = by_label.get("BF → Orb → Cap → HF → Crypt")
    morg_copy = by_label.get("BF → Rylai → Crypt → Orb → HF")
    rylai_second = any("→ Rylai →" in r.label[:20] or r.label.startswith("BF → Rylai") or r.label.startswith("Luden → Rylai") for r in ranked[:12])
    hf_early = any(r.label.split(" → ")[1] == "HF" for r in ranked[:8] if len(r.label.split(" → ")) > 2)
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
    L.append("  • Mỗi E (laser + Blastquake) và mỗi Q là cửa Harvest.")
    L.append("    AH không giảm CD 35s — AH để E/Q sẵn sàng khi target <50%.")
    L.append("  • Laser apply HF; Blastquake 1s sau ăn 10%. Đó là cửa DH kép.")
    L.append("  • Chip từ 90% phải TỰ mở cửa. E evolve @6 cho aftershock.")
    L.append("    Pen (Crypt) + HF 10% trên shock mở cửa ~19:00 — không cần Rylai 5s.")
    if diamond:
        L.append(
            f"  • Diamond+ Luden→Orb→Cap (thêm HF/Crypt): {diamond.label} "
            f"{pct(diamond.total, best.total)}. Echo không đếm trên farm hit."
        )
    if luden and not (best.label.startswith("Luden")):
        L.append(
            f"  • Best Luden-first: {luden.label} {pct(luden.total, best.total)}."
        )
    elif luden and best.label.startswith("Luden"):
        L.append("  • Luden-first thắng search: 100 AP giúp laser+shock mở cửa;")
        L.append("    Echo vẫn không cộng vào farm60 spam.")
    if burn:
        L.append(
            f"  • BF→Liandry→Void {pct(burn.total, best.total)}. "
            f"Burn 2%/s trên poke 3s thua pen+HF trên E hai hit."
        )
    if hybrid:
        L.append(
            f"  • Hybrid BF→Orb→Cap {pct(hybrid.total, best.total)}."
        )
    if morg_copy:
        L.append(
            f"  • Copy Morgana (BF→Rylai→Crypt→Orb→HF) {pct(morg_copy.total, best.total)}. "
            f"Viktor không có W pool 5s; Rylai chỉ +12% land Blastquake."
        )
    storm = by_label.get("BF → Storm → Orb → Cap → Crypt")
    if storm:
        L.append(f"  • Stormsurge burst {pct(storm.total, best.total)}. Squall không vào metric.")
    if voidp:
        L.append(
            f"  • Best Void-first {voidp.label} {pct(voidp.total, best.total)}."
        )
    legs = [n for n in best.snaps[-1].items if n in LEGENDARIES]
    if "Horizon Focus" in legs:
        L.append(
            "  • HF: laser đánh dấu, Blastquake +10%. 25 AH = thêm E/phút trong cửa."
        )
    if "Infinity Orb" in legs:
        L.append(
            "  • Orb 110 AP + 15 flat. 20% bật khi laser đã đẩy dưới 35% trước shock/Q."
        )
    if "Rabadon's Deathcap" in legs:
        L.append("  • Cap 30% amp gồm GS 70 @24 và DH 5% AP.")
    if "Blackfire Torch" in legs:
        L.append("  • BF burn refresh bằng E/Q + 20 AH. Không bắt phải Luden.")
    L.append("")
    L.append("  CHƠI:")
    L.append("  • Lane: E wave + E lên người khi mid <70%. Laser → shock → Q AA → DH.")
    L.append("  • Evolve E trước (hex fragments). W evolve 20% slow giúp shock dính.")
    L.append("  • Fight: E → Q → DH. Takedown reset 1s = soul tiếp. R không phải cửa farm.")
    L.append("  • Đừng copy Morgana Rylai-second. Đừng mua 2 Lost Chapter.")
    L.append("=" * 80)
    return "\n".join(L)


def export_json(ranked: List[PathRun], path: str) -> None:
    top = ranked[:25]
    payload = {
        "meta": {
            "champion": "Viktor",
            "role": "mid",
            "patch": "7.2e",
            "game_minutes": GAME_MINUTES,
            "playstyle": "farm Dark Harvest from minute 1 to 30 with E+Q",
            "souls": "endogenous E/Q chip + takedown",
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
