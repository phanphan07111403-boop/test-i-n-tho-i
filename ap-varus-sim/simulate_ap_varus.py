#!/usr/bin/env python3
"""
PC League of Legends — AP Varus burst (patch 26.21).

Question: with Fleet / Alacrity and Sorcery AP runes, which 5 legendary
items spike the one-shot every time one of them is finished, and in what
buy order?

Primary combo (all-in, uses the attack-speed rune):
  3 autos (3 Blight) → R from ≥600 range (detonates them, applies 3 more)
  → fully charged W+Q (detonates the new stacks, missing-HP active).

Pick combo (no setup):
  R from range → fully charged W+Q on the stacks R applies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import permutations
from typing import Dict, List, Optional, Sequence, Tuple
import json
import os

PATCH = "26.21"

# ---------------------------------------------------------------------------
# Items — patch 26.20/26.21 wiki + shop stats
# ---------------------------------------------------------------------------


@dataclass
class Item:
    name: str
    cost: int
    ap: float = 0
    ah: float = 0
    hp: float = 0
    ad: float = 0
    as_pct: float = 0
    flat_mpen: float = 0
    pct_mpen: float = 0
    mana: float = 0
    deathcap: bool = False
    nashor: bool = False
    shadowflame: bool = False
    stormsurge: bool = False
    horizon: bool = False
    luden: bool = False
    liandry: bool = False
    riftmaker: bool = False
    bloodletter: bool = False
    guinsoo: bool = False
    ashes: bool = False
    guise: bool = False
    recurve: bool = False
    legendary: bool = False


def I(name: str, cost: int, **kwargs) -> Item:
    return Item(name, cost, **kwargs)


ITEMS: Dict[str, Item] = {
    "Doran's Ring": I("Doran's Ring", 400, ap=18, hp=90),
    "Amplifying Tome": I("Amplifying Tome", 400, ap=20),
    "Needlessly Large Rod": I("Needlessly Large Rod", 1200, ap=65),
    "Blasting Wand": I("Blasting Wand", 850, ap=45),
    "Fiendish Codex": I("Fiendish Codex", 850, ap=25, ah=10),
    "Lost Chapter": I("Lost Chapter", 1200, ap=40, ah=10, mana=300),
    "Hextech Alternator": I("Hextech Alternator", 1100, ap=45),
    "Aether Wisp": I("Aether Wisp", 900, ap=30),
    "Blighting Jewel": I("Blighting Jewel", 1100, ap=25, pct_mpen=0.13),
    "Haunting Guise": I("Haunting Guise", 1300, ap=30, hp=200, guise=True),
    "Fated Ashes": I("Fated Ashes", 900, ap=30, ashes=True),
    "Recurve Bow": I("Recurve Bow", 700, as_pct=0.15, recurve=True),
    "Pickaxe": I("Pickaxe", 875, ad=25),
    "Sheen": I("Sheen", 900, ah=10),
    "Seeker's Armguard": I("Seeker's Armguard", 1600, ap=40),
    "Boots": I("Boots", 300),
    "Sorcerer's Shoes": I("Sorcerer's Shoes", 1100, flat_mpen=12),
    "Nashor's Tooth": I(
        "Nashor's Tooth", 2900, ap=80, ah=15, as_pct=0.50, nashor=True, legendary=True
    ),
    "Stormsurge": I(
        "Stormsurge",
        2800,
        ap=90,
        flat_mpen=15,
        stormsurge=True,
        legendary=True,
    ),
    "Shadowflame": I(
        "Shadowflame",
        3200,
        ap=110,
        flat_mpen=15,
        shadowflame=True,
        legendary=True,
    ),
    "Luden's Echo": I(
        "Luden's Echo",
        2750,
        ap=100,
        ah=10,
        mana=600,
        luden=True,
        legendary=True,
    ),
    "Horizon Focus": I(
        "Horizon Focus", 2700, ap=75, ah=25, horizon=True, legendary=True
    ),
    "Rabadon's Deathcap": I(
        "Rabadon's Deathcap", 3500, ap=130, deathcap=True, legendary=True
    ),
    "Void Staff": I(
        "Void Staff", 3000, ap=95, pct_mpen=0.40, legendary=True
    ),
    "Cryptbloom": I(
        "Cryptbloom", 3000, ap=75, ah=20, pct_mpen=0.30, legendary=True
    ),
    "Lich Bane": I("Lich Bane", 2900, ap=100, ah=10, legendary=True),
    "Liandry's Torment": I(
        "Liandry's Torment", 3000, ap=60, hp=300, liandry=True, legendary=True
    ),
    "Riftmaker": I(
        "Riftmaker", 3100, ap=70, hp=350, ah=15, riftmaker=True, legendary=True
    ),
    "Bloodletter's Curse": I(
        "Bloodletter's Curse",
        2900,
        ap=65,
        hp=400,
        ah=15,
        bloodletter=True,
        legendary=True,
    ),
    "Zhonya's Hourglass": I(
        "Zhonya's Hourglass", 3250, ap=105, legendary=True
    ),
    "Guinsoo's Rageblade": I(
        "Guinsoo's Rageblade",
        3000,
        ap=30,
        ad=30,
        as_pct=0.25,
        guinsoo=True,
        legendary=True,
    ),
}

# Components bought before the combine, highest burst piece first.
RECIPES: Dict[str, Tuple[str, ...]] = {
    "Sorcerer's Shoes": ("Boots",),
    "Stormsurge": ("Hextech Alternator", "Aether Wisp"),
    "Shadowflame": ("Needlessly Large Rod", "Hextech Alternator"),
    "Luden's Echo": ("Lost Chapter", "Hextech Alternator"),
    "Horizon Focus": ("Amplifying Tome", "Fiendish Codex", "Fiendish Codex"),
    "Rabadon's Deathcap": ("Needlessly Large Rod", "Needlessly Large Rod"),
    "Void Staff": ("Blighting Jewel", "Blasting Wand"),
    "Nashor's Tooth": ("Blasting Wand", "Fiendish Codex", "Recurve Bow"),
    "Cryptbloom": ("Blighting Jewel", "Fiendish Codex", "Fiendish Codex"),
    "Lich Bane": ("Blasting Wand", "Aether Wisp", "Sheen"),
    "Liandry's Torment": ("Haunting Guise", "Fated Ashes"),
    "Riftmaker": ("Haunting Guise", "Fiendish Codex", "Amplifying Tome"),
    "Zhonya's Hourglass": ("Needlessly Large Rod", "Seeker's Armguard"),
    "Guinsoo's Rageblade": ("Pickaxe", "Amplifying Tome", "Recurve Bow"),
    "Bloodletter's Curse": (),
}

LEGEND_POOL = [
    "Stormsurge",
    "Shadowflame",
    "Luden's Echo",
    "Horizon Focus",
    "Rabadon's Deathcap",
    "Void Staff",
    "Nashor's Tooth",
    "Cryptbloom",
    "Lich Bane",
    "Liandry's Torment",
]
EXTRA_POOL = [
    "Riftmaker",
    "Bloodletter's Curse",
    "Zhonya's Hourglass",
    "Guinsoo's Rageblade",
]

UNIQUE = {
    name
    for name, it in ITEMS.items()
    if it.legendary or name in ("Sorcerer's Shoes", "Boots", "Doran's Ring", "Sheen")
}


# ---------------------------------------------------------------------------
# Economy / levels
# ---------------------------------------------------------------------------


def gold_at_minute(m: int, mult: float = 1.0) -> int:
    """Farmer curve (not a fed snowball). Start 500 included."""
    if m <= 0:
        return 500
    total = 500
    for t in range(1, m + 1):
        if t <= 5:
            total += 310
        elif t <= 10:
            total += 420
        elif t <= 16:
            total += 500
        elif t <= 22:
            total += 540
        else:
            total += 580
    if mult != 1.0:
        total = int(500 + (total - 500) * mult)
    return total


_LEVEL = {
    1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7, 7: 8, 8: 9,
    9: 10, 10: 11, 11: 11, 12: 12, 13: 12, 14: 13,
    15: 13, 16: 14, 17: 14, 18: 15, 19: 15, 20: 16,
    21: 16, 22: 17, 23: 17, 24: 17, 25: 18, 26: 18,
    27: 18, 28: 18,
}


def level_at_minute(m: int) -> int:
    if m <= 0:
        return 1
    if m > 28:
        return 18
    return _LEVEL[m]


def skill_rank(level: int, skill: str) -> int:
    """W max, Q second, E last. R at 6/11/16. Start Q."""
    if skill == "R":
        if level < 6:
            return 0
        if level < 11:
            return 1
        if level < 16:
            return 2
        return 3
    levels = {
        "Q": (1, 9, 10, 12, 13),
        "W": (2, 4, 5, 7, 8),
        "E": (3, 14, 15, 17, 18),
    }[skill]
    return sum(1 for lv in levels if level >= lv)


def alacrity_stacks(minute: int) -> int:
    """~7 cs/min (4 points) and a takedown every ~3 min (100 points)."""
    points = 4 * (7.0 * minute) + 100 * (0.35 * minute)
    return min(10, int(points // 100))


def gathering_storm_ap(minute: int) -> float:
    n = minute // 10
    return float(4 * n * (n + 1))


def absolute_focus_ap(level: int) -> float:
    # Live tooltip: 3 – 33.18 AP from level 1 to 18 while above 70% HP.
    return 3.0 + (33.18 - 3.0) * (level - 1) / 17.0


# ---------------------------------------------------------------------------
# Targets
# ---------------------------------------------------------------------------


def target_stats(m: int, kind: str) -> dict:
    lv = level_at_minute(m)
    if kind == "squishy":
        # Smooth item growth. Step-function MR (a Null-Magic at 12:00 on the
        # dot) made any legendary that finished one minute earlier look like
        # a different build.
        hp = 620 + 108 * (lv - 1) + min(900.0, max(0, m - 6) * 32.0)
        mr = 32 + 1.3 * (lv - 1) + min(48.0, max(0, m - 8) * 1.7)
        armor = 28 + 4.2 * (lv - 1) + min(55.0, max(0, m - 10) * 2.2)
        tenacity = 0.0
    else:
        hp = 680 + 112 * (lv - 1) + 140 * max(0, m - 5)
        mr = 34 + 2.05 * (lv - 1) + min(8.0 * max(0, m - 7), 140)
        armor = 36 + 4.7 * (lv - 1) + min(9.0 * max(0, m - 6), 160)
        tenacity = 0.30 if m >= 12 else 0.0
    return {
        "hp": float(hp),
        "mr": float(mr),
        "armor": float(armor),
        "tenacity": tenacity,
        "level": lv,
    }


# ---------------------------------------------------------------------------
# Stats from an inventory
# ---------------------------------------------------------------------------


@dataclass
class Stats:
    ap: float
    bonus_ad: float
    as_pct: float
    flat_pen: float
    pct_pens: List[float]
    bonus_hp: float
    deathcap: bool = False
    nashor: bool = False
    shadowflame: bool = False
    stormsurge: bool = False
    horizon: bool = False
    luden: bool = False
    liandry: bool = False
    riftmaker: bool = False
    bloodletter: bool = False
    guinsoo: bool = False
    ashes: bool = False
    guise: bool = False
    recurve: bool = False
    names: List[str] = field(default_factory=list)


def compute_stats(
    names: Sequence[str],
    level: int,
    minute: int,
    *,
    use_af: bool = True,
    use_gs: bool = True,
) -> Stats:
    ap = ad = hp = as_pct = flat = 0.0
    pens: List[float] = []
    flags = dict(
        deathcap=False,
        nashor=False,
        shadowflame=False,
        stormsurge=False,
        horizon=False,
        luden=False,
        liandry=False,
        riftmaker=False,
        bloodletter=False,
        guinsoo=False,
        ashes=False,
        guise=False,
        recurve=False,
    )
    for name in names:
        it = ITEMS[name]
        ap += it.ap
        ad += it.ad
        hp += it.hp
        as_pct += it.as_pct
        flat += it.flat_mpen
        if it.pct_mpen:
            pens.append(it.pct_mpen)
        for key in flags:
            if getattr(it, key):
                flags[key] = True

    # Riftmaker turns bonus HP into AP before Deathcap.
    if flags["riftmaker"]:
        ap += 0.02 * hp

    af = absolute_focus_ap(level) if use_af else 0.0
    gs = gathering_storm_ap(minute) if use_gs else 0.0
    shards = 18.0  # two adaptive shards
    adaptive_ap = af + gs + shards
    # Varus adaptive type is physical on a tie.
    if ap > ad:
        ap += adaptive_ap
    elif ad > ap:
        ad += 0.6 * adaptive_ap
    else:
        ad += 0.6 * adaptive_ap

    if flags["deathcap"]:
        ap *= 1.30

    return Stats(
        ap=ap,
        bonus_ad=ad,
        as_pct=as_pct,
        flat_pen=flat,
        pct_pens=pens,
        bonus_hp=hp,
        names=list(names),
        **flags,
    )


def magic_mult(mr: float, pens: Sequence[float], flat: float, shred_stacks: int) -> float:
    reduced = mr * (1.0 - 0.075 * shred_stacks)
    for p in pens:
        reduced *= 1.0 - p
    reduced -= flat
    return 100.0 / (100.0 + reduced)


def armor_mult(armor: float) -> float:
    return 100.0 / (100.0 + armor)


# ---------------------------------------------------------------------------
# Combo
# ---------------------------------------------------------------------------

_BLIGHT = (0.025, 0.025, 0.030, 0.035, 0.040, 0.045)
_W_ACTIVE = (0.0, 0.06, 0.07, 0.08, 0.09, 0.10)
_W_ONHIT = (0, 4, 10, 16, 22, 28)
_Q_MAX = (0, 85, 161.5, 238, 314.5, 391)
_R_BASE = (0, 150, 250, 350)
_STACK_TIMES = (0.65, 1.20, 1.75)


def blight_ratio(rank: int, ap: float, stacks: int, charged: bool) -> float:
    per = _BLIGHT[rank] + 0.014 * (ap / 100.0)
    return per * stacks * (1.70 if charged else 1.0)


def r_stacks_and_release(tenacity: float) -> Tuple[int, float]:
    """Stacks R actually applies, and when Q is released (seconds into the root)."""
    root = 2.0 * (1.0 - tenacity)
    applied = [t for t in _STACK_TIMES if t <= root + 1e-9]
    if root > 0 and not applied:
        applied = [root]
    n = len(applied)
    release = 1.25
    if applied:
        release = max(1.25, applied[-1])
    return n, release


def attack_speed(level: int, minute: int, bonus_as: float) -> float:
    growth = 0.035 * (level - 1)
    ala = 0.03 + 0.015 * alacrity_stacks(minute)
    return 0.658 * (1.0 + growth + ala + bonus_as)


def _amp(
    hp: float,
    max_hp: float,
    kind: str,
    time: float,
    combat_start: float,
    st: Stats,
    rune: str,
    mark_time: Optional[float],
) -> float:
    a = 1.0
    secs = max(0, int(time - combat_start))
    if st.liandry or st.guise:
        cap = 0.06
        a *= 1.0 + min(cap, 0.02 * secs)
    if st.riftmaker:
        a *= 1.0 + min(0.08, 0.02 * secs)
    if st.horizon and mark_time is not None and time >= mark_time - 1e-9:
        a *= 1.10
    clamped = min(max_hp, max(0.0, hp))
    if rune == "cut" and clamped > 0.60 * max_hp:
        a *= 1.08
    elif rune == "coup" and clamped < 0.40 * max_hp:
        a *= 1.08
    if kind == "magic" and st.shadowflame and clamped < 0.40 * max_hp:
        a *= 1.20
    return a


def simulate(
    st: Stats,
    level: int,
    minute: int,
    target: dict,
    rune: str,
    mode: str,
) -> dict:
    """
    mode 'allin': 3 autos, R detonates them, W+Q detonates R's new stacks.
    mode 'pick': R from range, W+Q detonates R's stacks. No setup autos.
    Damage keeps counting after the target would die so later items still
    show a bigger combo. tags are post-mitigation.
    """
    max_hp = target["hp"]
    mr = target["mr"]
    armor = target["armor"]
    tenacity = target["tenacity"]
    ap = st.ap
    wr = skill_rank(level, "W")
    qr = skill_rank(level, "Q")
    rr = skill_rank(level, "R")

    stacks, release = r_stacks_and_release(tenacity)
    aps = attack_speed(level, minute, st.as_pct)
    # R cast just after the third auto (all-in) or at t=0 (pick).
    t_autos_done = (2.0 / aps) if mode == "allin" else 0.0
    t_r_cast_end = t_autos_done + 0.24
    travel_r = 0.45
    travel_q = 0.42
    t_r = t_r_cast_end + travel_r
    t_q = t_r + release + travel_q
    combat_start = 0.0 if mode == "allin" else t_r
    mark_time = t_r if st.horizon else None

    # (time, kind, raw_or_none, tag, special)
    # special: None | ("blight", ratio_of_max) | ("wactive", ratio_of_missing) | ("burn",) | ("squall",)
    events: List[tuple] = []

    base_ad = 59.0 + 3.4 * (level - 1)
    total_ad = base_ad + st.bonus_ad

    if mode == "allin":
        onhit_magic = 0.0
        if wr > 0:
            onhit_magic += _W_ONHIT[wr] + 0.20 * st.bonus_ad + 0.30 * ap
        if st.nashor:
            onhit_magic += 15.0 + 0.15 * ap
        if st.guinsoo:
            onhit_magic += 30.0
        for i in range(3):
            t = 0.0 if i == 0 else i / aps
            events.append((t, "physical", total_ad, "auto", None))
            if onhit_magic:
                events.append((t + 0.01, "magic", onhit_magic, "onhit", None))
            if st.recurve and not st.nashor and not st.guinsoo:
                events.append((t + 0.02, "physical", 15.0, "auto", None))
            # Guinsoo phantom on the 3rd auto: on-hits twice. Blight still caps at 3.
            if st.guinsoo and i == 2 and onhit_magic:
                events.append((t + 0.03, "magic", onhit_magic, "onhit", None))

    if rr > 0:
        events.append((t_r, "magic", _R_BASE[rr] + 1.00 * ap, "r", None))
        if st.luden:
            events.append((t_r + 0.01, "magic", 150.0 + 0.10 * ap, "luden", None))
        if mode == "allin":
            ratio = blight_ratio(wr, ap, 3, charged=False)
            events.append((t_r + 0.02, "magic", None, "blight_r", ("blight", ratio)))
        if stacks > 0 and qr > 0:
            q_raw = _Q_MAX[qr] + 1.36 * st.bonus_ad
            events.append((t_q, "physical", q_raw, "q", None))
            ratio_q = blight_ratio(wr, ap, stacks, charged=True)
            events.append((t_q + 0.01, "magic", None, "blight_q", ("blight", ratio_q)))
            if wr > 0:
                active = _W_ACTIVE[wr] * stacks * 1.70
                events.append((t_q + 0.02, "magic", None, "w_active", ("wactive", active)))
    elif qr > 0 and mode == "allin":
        # Pre-6 fallback: autos + charged WQ only.
        q_raw = _Q_MAX[qr] + 1.36 * st.bonus_ad
        events.append((t_autos_done + 1.25, "physical", q_raw, "q", None))
        ratio_q = blight_ratio(wr, ap, 3, charged=True)
        events.append((t_autos_done + 1.26, "magic", None, "blight_q", ("blight", ratio_q)))
        if wr > 0:
            active = _W_ACTIVE[wr] * 3 * 1.70
            events.append(
                (t_autos_done + 1.27, "magic", None, "w_active", ("wactive", active))
            )

    events.sort(key=lambda e: e[0])

    hp = max_hp
    total = 0.0
    by_tag: Dict[str, float] = {}
    window = 0.0
    shred = 0
    arm = armor_mult(armor)

    def apply_one(time, kind, raw, tag, shred_now):
        nonlocal hp, total, window, shred
        if st.bloodletter:
            shred_now = shred
        mult = magic_mult(mr, st.pct_pens, st.flat_pen, shred_now) if kind == "magic" else arm
        dealt = raw * _amp(hp, max_hp, kind, time, combat_start, st, rune, mark_time) * mult
        total += dealt
        by_tag[tag] = by_tag.get(tag, 0.0) + dealt
        # Squall window is the R → WQ stretch (setup autos sit just outside 2.5s).
        if rr > 0 and (t_r - 1e-9) <= time <= (t_q + 0.05):
            window += dealt
        hp -= dealt
        if kind == "magic" and st.bloodletter:
            shred = min(4, shred + 1)

    for time, kind, raw, tag, special in events:
        if special is None:
            apply_one(time, kind, raw, tag, shred)
        elif special[0] == "blight":
            apply_one(time, "magic", special[1] * max_hp, tag, shred)
        elif special[0] == "wactive":
            missing = max_hp - min(max_hp, max(0.0, hp))
            apply_one(time, "magic", special[1] * missing, tag, shred)

    # Liandry / Ashes / Squall resolve after the direct cast.
    tail: List[tuple] = []
    if st.liandry:
        for i, dt in enumerate((1.0, 2.0, 3.0)):
            tail.append((t_q + dt, "magic", 0.02 * max_hp, "burn"))
    elif st.ashes:
        tail.append((t_q + 1.0, "magic", 15.0, "burn"))
    if st.stormsurge and window >= 0.25 * max_hp:
        tail.append((t_q + 2.0, "magic", 125.0 + 0.10 * ap, "squall"))
    for time, kind, raw, tag in tail:
        apply_one(time, kind, raw, tag, shred)

    return {
        "damage": total,
        "tags": by_tag,
        "window": window,
        "hp": max_hp,
        "killed": total >= max_hp,
        "stacks": stacks,
        "aps": aps,
        "auto_time": (2.0 / aps) if mode == "allin" else 0.0,
        "ap": ap,
    }


# ---------------------------------------------------------------------------
# Shopping
# ---------------------------------------------------------------------------


def steps_for(legs: Sequence[str], boots_at: int) -> List[str]:
    steps: List[str] = []
    for i, leg in enumerate(legs):
        if boots_at == i:
            steps.append("Sorcerer's Shoes")
        steps.extend(RECIPES.get(leg, ()))
        steps.append(leg)
    if boots_at >= len(legs):
        steps.append("Sorcerer's Shoes")
    return steps


def _credit(item_name: str, owned: List[str]) -> Tuple[int, List[str]]:
    credit = 0
    remove: List[str] = []
    available = list(owned)
    for comp in RECIPES.get(item_name, ()):
        if comp in available:
            credit += ITEMS[comp].cost
            available.remove(comp)
            remove.append(comp)
    return credit, remove


def _try_buy(owned: List[str], gold: int, name: str) -> Optional[Tuple[List[str], int]]:
    """Buy `name` in one shop click. Returns (owned, gold) or None.

    Missing components are paid for inside the click, so a full inventory can
    still upgrade: League only needs the slots left after the combine.
    """
    if name in UNIQUE and name in owned:
        return owned, gold
    credit, remove = _credit(name, owned)
    cost = ITEMS[name].cost - credit
    if gold < cost:
        return None
    trial = list(owned)
    slots_after = len(trial) - len(remove) + 1
    if slots_after > 6 and "Doran's Ring" in trial:
        trial.remove("Doran's Ring")
        gold += 280
        slots_after -= 1
    if slots_after > 6 or gold < cost:
        return None
    for comp in remove:
        trial.remove(comp)
    trial.append(name)
    return trial, gold - cost


def inventory_at(steps: Sequence[str], minute: int, mult: float = 1.0) -> List[str]:
    earned = gold_at_minute(minute, mult)
    owned = ["Doran's Ring"]
    gold = earned - 400
    idx = 0
    steps = list(steps)
    while idx < len(steps):
        bought = _try_buy(owned, gold, steps[idx])
        if bought is not None:
            owned, gold = bought
            idx += 1
            continue
        # Component doesn't fit (or isn't affordable). If a later finished
        # item can be bought in one click, do that and skip the parts.
        jumped = False
        for j in range(idx + 1, len(steps)):
            nxt = steps[j]
            if not (ITEMS[nxt].legendary or nxt == "Sorcerer's Shoes"):
                continue
            bought = _try_buy(owned, gold, nxt)
            if bought is not None:
                owned, gold = bought
                idx = j + 1
                jumped = True
            break
        if not jumped:
            break
    return owned


def finished_legendaries(owned: Sequence[str]) -> List[str]:
    return [n for n in owned if ITEMS[n].legendary]


def completion_minutes_fast(
    legs: Sequence[str], boots_at: int, mult: float = 1.0
) -> List[Tuple[str, int]]:
    """(legendary name, minute it finishes) using full item prices."""
    cum = 400  # Doran's Ring
    legs_done = 0
    out: List[Tuple[str, int]] = []
    sequence: List[Tuple[str, int, bool]] = []
    for i, leg in enumerate(legs):
        if boots_at == i:
            sequence.append(("Sorcerer's Shoes", 1100, False))
        sequence.append((leg, ITEMS[leg].cost, True))
    if boots_at >= len(legs):
        sequence.append(("Sorcerer's Shoes", 1100, False))
    refund_used = False
    for name, cost, is_leg in sequence:
        if is_leg and legs_done == 4 and not refund_used:
            cum -= 280
            refund_used = True
        cum += cost
        if is_leg:
            legs_done += 1
            minute = 0
            while minute < 48 and gold_at_minute(minute, mult) < cum:
                minute += 1
            out.append((name, minute))
    return out


def score_path(
    legs: Sequence[str],
    boots_at: int,
    rune: str,
    *,
    use_af: bool = True,
    use_gs: bool = True,
    mult: float = 1.0,
    accurate: bool = False,
    with_side: bool = True,
) -> dict:
    weights = (1.35, 1.25, 1.15, 1.08, 1.00)
    if accurate:
        steps = steps_for(legs, boots_at)
        spikes = []
        seen = 0
        for minute in range(0, 48):
            owned = inventory_at(steps, minute, mult)
            done = finished_legendaries(owned)
            if len(done) > seen:
                for name in done[seen:]:
                    spikes.append((name, minute, list(owned)))
                seen = len(done)
            if seen >= 5:
                break
        # Fall back if the walker couldn't finish (shouldn't).
        if len(spikes) < 5:
            spikes = [
                (name, minute, None)
                for name, minute in completion_minutes_fast(legs, boots_at, mult)
            ]
    else:
        spikes = [
            (name, minute, None)
            for name, minute in completion_minutes_fast(legs, boots_at, mult)
        ]

    score = 0.0
    rows = []
    prev = 0.0
    for i, (name, minute, owned) in enumerate(spikes):
        level = level_at_minute(minute)
        if owned is None:
            names = ["Doran's Ring"] if i < 4 else []
            if boots_at <= i:
                names.append("Sorcerer's Shoes")
            names.extend(legs[: i + 1])
        else:
            names = owned
        st = compute_stats(names, level, minute, use_af=use_af, use_gs=use_gs)
        squish = target_stats(minute, "squishy")
        allin = simulate(st, level, minute, squish, rune, "allin")
        if with_side:
            brute = target_stats(minute, "bruiser")
            pick = simulate(st, level, minute, squish, rune, "pick")
            vs_b = simulate(st, level, minute, brute, rune, "allin")
            pick_dmg = pick["damage"]
            pick_pct = 100.0 * pick_dmg / squish["hp"]
            bruiser_hp = brute["hp"]
            bruiser_mr = brute["mr"]
            bruiser = vs_b["damage"]
            bruiser_pct = 100.0 * bruiser / bruiser_hp
        else:
            pick_dmg = pick_pct = bruiser_hp = bruiser_mr = bruiser = bruiser_pct = 0.0
        ratio = allin["damage"] / squish["hp"]
        score += weights[i] * ratio
        gain = allin["damage"] - prev
        prev = allin["damage"]
        rows.append(
            {
                "item": name,
                "minute": minute,
                "level": level,
                "owned": names,
                "ap": round(st.ap, 1),
                "flat_pen": st.flat_pen,
                "pct_pen": round(1.0 - _pen_product(st.pct_pens), 3),
                "squishy_hp": round(squish["hp"]),
                "squishy_mr": round(squish["mr"], 1),
                "squishy_armor": round(squish["armor"], 1),
                "allin": round(allin["damage"]),
                "allin_pct": round(100.0 * ratio, 1),
                "pick": round(pick_dmg),
                "pick_pct": round(pick_pct, 1),
                "bruiser_hp": round(bruiser_hp),
                "bruiser_mr": round(bruiser_mr, 1),
                "bruiser": round(bruiser),
                "bruiser_pct": round(bruiser_pct, 1),
                "gain": round(gain),
                "killed": allin["killed"],
                "tags": {k: round(v) for k, v in allin["tags"].items()},
                "auto_time": round(allin["auto_time"], 2),
            }
        )
    return {
        "score": score,
        "rune": rune,
        "boots_at": boots_at,
        "items": list(legs),
        "spikes": rows,
        "use_af": use_af,
        "use_gs": use_gs,
    }


def _pen_product(pens: Sequence[float]) -> float:
    kept = 1.0
    for p in pens:
        kept *= 1.0 - p
    return kept


def combine_delta(owned: List[str], legendary: str, minute: int, rune: str) -> int:
    """Damage gained the moment the components turn into the finished item."""
    if legendary not in owned:
        return 0
    broken = [n for n in owned if n != legendary]
    # Only break one copy.
    broken.extend(RECIPES.get(legendary, ()))
    level = level_at_minute(minute)
    squish = target_stats(minute, "squishy")
    d_fin = simulate(
        compute_stats(owned, level, minute), level, minute, squish, rune, "allin"
    )["damage"]
    d_comp = simulate(
        compute_stats(broken, level, minute), level, minute, squish, rune, "allin"
    )["damage"]
    return int(round(d_fin - d_comp))


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------


def search(mult: float = 1.0) -> List[dict]:
    found: List[dict] = []
    pools = [LEGEND_POOL]
    # If an off-meta legendary wins the first slot on a probe, pull it in.
    probe_best = -1.0
    probe_name = None
    for name in LEGEND_POOL + EXTRA_POOL:
        for boots_at in (0, 1):
            for rune in ("cut", "coup"):
                # Score just the first completion by using a dummy 4-pack of
                # cheap fillers that we then ignore — cheaper to call simulate
                # directly.
                minute = completion_minutes_fast((name,), boots_at, mult)[0][1]
                level = level_at_minute(minute)
                names = ["Doran's Ring", name]
                if boots_at == 0:
                    names.insert(1, "Sorcerer's Shoes")
                st = compute_stats(names, level, minute)
                squish = target_stats(minute, "squishy")
                dmg = simulate(st, level, minute, squish, rune, "allin")["damage"]
                ratio = dmg / squish["hp"]
                if ratio > probe_best:
                    probe_best = ratio
                    probe_name = name
    if probe_name in EXTRA_POOL:
        pools = [LEGEND_POOL + [probe_name]]

    pool = pools[0]
    for legs in permutations(pool, 5):
        for boots_at in (0, 1, 2, 3):
            for rune in ("cut", "coup"):
                found.append(
                    score_path(
                        legs, boots_at, rune, mult=mult, with_side=False
                    )
                )
    found.sort(key=lambda r: r["score"], reverse=True)
    return found


def rescore_top(found: List[dict], k: int = 25) -> List[dict]:
    """Re-rank the fast leaders with the real component shopper."""
    uniq = []
    seen = set()
    for row in found:
        key = (tuple(row["items"]), row["boots_at"], row["rune"])
        if key in seen:
            continue
        seen.add(key)
        uniq.append(row)
        if len(uniq) >= k:
            break
    # Always keep the best Nashor-first path in the accurate pass.
    for row in found:
        if row["items"][0] == "Nashor's Tooth":
            key = (tuple(row["items"]), row["boots_at"], row["rune"])
            if key not in seen:
                uniq.append(row)
            break
    accurate = [
        score_path(row["items"], row["boots_at"], row["rune"], accurate=True)
        for row in uniq
    ]
    accurate.sort(key=lambda r: r["score"], reverse=True)
    return accurate


def minute_curve(legs: Sequence[str], boots_at: int, rune: str) -> List[dict]:
    steps = steps_for(legs, boots_at)
    rows = []
    for minute in range(1, 41):
        owned = inventory_at(steps, minute)
        if owned == ["Doran's Ring"] and minute > 1 and gold_at_minute(minute) < 800:
            continue
        level = level_at_minute(minute)
        st = compute_stats(owned, level, minute)
        squish = target_stats(minute, "squishy")
        allin = simulate(st, level, minute, squish, rune, "allin")
        rows.append(
            {
                "minute": minute,
                "level": level,
                "owned": owned,
                "legendaries": finished_legendaries(owned),
                "ap": round(st.ap, 1),
                "allin": round(allin["damage"]),
                "pct": round(100.0 * allin["damage"] / squish["hp"], 1),
                "hp": round(squish["hp"]),
            }
        )
    return rows


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------


def _boots_phrase(boots_at: int) -> str:
    if boots_at == 0:
        return "Sorcerer's Shoes before the first legendary"
    if boots_at == 1:
        return "Sorcerer's Shoes right after the first legendary"
    return f"Sorcerer's Shoes after legendary {boots_at}"


def _buy_lines(legs: Sequence[str], boots_at: int) -> List[str]:
    steps = ["Doran's Ring"] + steps_for(legs, boots_at)
    lines = []
    spent = 0
    owned: List[str] = []
    for i, name in enumerate(steps, start=1):
        credit, remove = _credit(name, owned)
        pay = ITEMS[name].cost - credit
        spent += pay
        for comp in remove:
            owned.remove(comp)
        owned.append(name)
        mark = "  ← legendary" if ITEMS[name].legendary else ""
        if name == "Sorcerer's Shoes":
            mark = "  ← boots"
        lines.append(f"  {i:>2}. {name:<22} pay {pay:>4}g   total {spent:>5}g{mark}")
    lines.append("  Sell Doran's Ring once the inventory is full (+280g).")
    lines.append(f"  Net gold to finish the 5th legendary: {spent - 280}g.")
    return lines


def render(
    winner: dict,
    top: List[dict],
    curve: List[dict],
    tradeoffs: List[dict],
    fifths: List[dict],
) -> str:
    rune_name = "Cut Down" if winner["rune"] == "cut" else "Coup de Grace"
    lines: List[str] = []
    a = lines.append
    a(f"AP Varus — burst spikes on every finished item (patch {PATCH})")
    a("=" * 72)
    a("")
    a("Build")
    a("-----")
    a("Start Doran's Ring, then:")
    for i, name in enumerate(winner["items"], start=1):
        row = winner["spikes"][i - 1]
        a(
            f"  {i}. {name}   finishes ~{row['minute']}:00"
            f"   all-in {row['allin']} ({row['allin_pct']}% of the squishy)"
        )
    a(f"Boots: {_boots_phrase(winner['boots_at'])}.")
    a("")
    a("Buy order")
    a("---------")
    lines.extend(_buy_lines(winner["items"], winner["boots_at"]))
    a("")
    a("Runes (legal page — the listed Sorcery trio does not fit)")
    a("---------------------------------------------------------")
    a("Precision  Fleet Footwork → Presence of Mind → Legend: Alacrity → " + rune_name)
    a("Sorcery    Absolute Focus + Gathering Storm")
    a("Shards     Adaptive, Adaptive, scaling health")
    a("")
    a("Fleet, Presence of Mind, Alacrity, and Manaflow add no damage to this")
    a("combo. Fleet keeps you above 70% HP so Absolute Focus stays on.")
    a("Alacrity is how you get the 3 setup autos off. Manaflow cannot be taken")
    a("with both Absolute Focus and Gathering Storm (Sorcery secondary is 2")
    a("runes, one per row). Presence of Mind is the mana rune that does fit.")
    a(f"Finish rune is {rune_name} — it won the all-in on this target.")
    a("")
    a("Combo that the spikes are measured on")
    a("--------------------------------------")
    a("All-in: 3 autos apply Blight → R from at least 600 range detonates them")
    a("and applies a fresh set → hold Q through the root (W during the channel)")
    a("and release fully charged. Pick (no autos) is the same R → W+Q when you")
    a("cannot walk up. Blight is 2.5–4.5% max HP per stack (+1.4% per 100 AP),")
    a("×1.70 on a full Q. W active is 6–10% missing HP per stack, ×1.70, no AP")
    a("ratio. Numbers are post-mitigation and keep counting after the kill, so")
    a("a later item still shows a bigger combo once you already one-shot.")
    a("")
    a("Spike at each finished legendary  (squishy all-in)")
    a("--------------------------------------------------")
    a(
        f"{'#':>2} {'Min':>4} {'Item':<22} {'AP':>6} {'Burst':>7} {'%HP':>6}"
        f" {'Gain':>7} {'Combine':>8} {'Pick%':>6} {'Bruiser%':>8}"
    )
    for i, row in enumerate(winner["spikes"], start=1):
        combine = combine_delta(row["owned"], row["item"], row["minute"], winner["rune"])
        a(
            f"{i:>2} {row['minute']:>3}m {row['item']:<22} {row['ap']:>6.0f}"
            f" {row['allin']:>7} {row['allin_pct']:>5.1f}%"
            f" {row['gain']:>+7} {combine:>+8} {row['pick_pct']:>5.1f}%"
            f" {row['bruiser_pct']:>7.1f}%"
        )
    a("")
    a("Gain = all-in damage now minus the previous finished item (components")
    a("of this item are included in the jump). Combine = the jump from clicking")
    a("the item while already holding its components. Pick% is R → W+Q with no")
    a("setup autos. Bruiser% is the all-in into Mercury's Treads (2 Blight")
    a("stacks from the root instead of 3).")
    a("")
    last = winner["spikes"][-1]
    a("Where the full-build all-in comes from")
    a("--------------------------------------")
    labels = [
        ("auto", "Autos (physical)"),
        ("onhit", "W / Nashor / Guinsoo on-hit"),
        ("r", "R base"),
        ("luden", "Luden echoes"),
        ("blight_r", "Blight popped by R (3 stacks, no charge)"),
        ("q", "Q (physical, full charge)"),
        ("blight_q", "Blight popped by Q (charged)"),
        ("w_active", "W active (missing HP, charged)"),
        ("burn", "Liandry / Ashes burn"),
        ("squall", "Stormsurge Squall"),
    ]
    for key, label in labels:
        val = last["tags"].get(key, 0)
        if val:
            a(f"  {label:<42} {val:>6}")
    a(f"  {'Total':<42} {last['allin']:>6}")
    a(
        f"  Target at {last['minute']}:00 — squishy {last['squishy_hp']} HP"
        f" / {last['squishy_mr']} MR / {last['squishy_armor']} armor."
        f"  Varus AP {last['ap']:.0f}, flat pen {last['flat_pen']:.0f},"
        f" percent pen {100 * last['pct_pen']:.0f}%."
    )
    a("")
    a("Minute curve (all-in vs the squishy, from level 6)")
    a("------------------------------------------------")
    a("A dip on the minute after a spike is the enemy leveling, not the item")
    a("turning off. Burst keeps counting after they die, so the % can sit")
    a("well above 100 once the combo one-shots.")
    first_kill = next(
        (row for row in curve if row["minute"] >= 6 and row["pct"] >= 100.0),
        None,
    )
    if first_kill:
        a(
            f"First minute the all-in crosses 100% of the squishy: "
            f"{first_kill['minute']}:00 ({first_kill['pct']}%)."
        )
    a(f"{'Min':>4} {'Lv':>3} {'AP':>6} {'Burst':>7} {'%HP':>6}  Inventory")
    prev_legs = 0
    for row in curve:
        if row["minute"] < 5:
            continue
        nlegs = len(row["legendaries"])
        mark = ""
        if nlegs > prev_legs:
            mark = "  << " + row["legendaries"][-1]
            prev_legs = nlegs
        inv = ", ".join(n for n in row["owned"] if n != "Doran's Ring")
        if len(inv) > 54:
            inv = inv[:51] + "..."
        a(
            f"{row['minute']:>3}m {row['level']:>3} {row['ap']:>6.0f}"
            f" {row['allin']:>7} {row['pct']:>5.1f}%  {inv}{mark}"
        )
    a("")
    a("Manaflow instead of a damage rune (same items)")
    a("----------------------------------------------")
    a(f"{'Secondary':<32} {'Item1 %':>8} {'Item3 %':>8} {'Full %':>8}")
    for row in tradeoffs:
        label = row["label"]
        s = row["spikes"]
        a(
            f"{label:<32} {s[0]['allin_pct']:>7.1f}% {s[2]['allin_pct']:>7.1f}%"
            f" {s[-1]['allin_pct']:>7.1f}%"
        )
    a("")
    if fifths:
        a("5th item on the same first four")
        a("-------------------------------")
        a(
            f"{winner['items'][-1]} is the damage buy. "
            "The others are the swaps people ask about."
        )
        a(f"{'5th item':<22} {'Full all-in':>12} {'%HP':>7}")
        for row in fifths:
            last = row["spikes"][-1]
            a(f"{row['fifth']:<22} {last['allin']:>12} {last['allin_pct']:>6.1f}%")
        a("")
    a("Other orders the search measured")
    a("---------------------------------")
    a(f"{'Score':>6} {'Rune':<5} {'Boots':>5}  Build (all-in %HP at each finish)")
    shown = 0
    seen = set()
    for row in top:
        key = tuple(row["items"])
        if key in seen:
            continue
        seen.add(key)
        pcts = "  ".join(f"{s['allin_pct']:.0f}%" for s in row["spikes"])
        a(
            f"{row['score']:>6.2f} {row['rune']:<5} {row['boots_at']:>5}"
            f"  {' → '.join(row['items'])}"
        )
        a(f"{'':>20}{pcts}")
        shown += 1
        if shown >= 6:
            break
    a("")
    a("Assumptions")
    a("-----------")
    a("- Patch 26.21 Varus: Q full-charge amp is 70% (was 50%). W on-hit is")
    a("  4–28 (+20% bonus AD) (+30% AP). Blight is 2.5/3/3.5/4/4.5% max HP")
    a("  per stack (+1.4% per 100 AP). W active is 6/7/8/9/10% missing HP")
    a("  per stack, also ×1.70 at full charge, and does not scale with AP.")
    a("- R applies Blight at 0.65s / 1.20s / 1.75s of the root. A squishy with")
    a("  no tenacity gets 3. Mercury's Treads (30% tenacity) cut that to 2.")
    a("  Cleanse or QSS before 0.65s applies zero stacks and the combo fizzles.")
    a("- Horizon Focus amps the R cast and everything after it. Setup autos")
    a("  happen before the mark. The R is taken from ≥600 range; from melee")
    a("  the 10% does not start.")
    a("- Shadowflame is +20% magic damage on hits that start below 40% HP.")
    a("  Cut Down is +8% while the target is above 60% HP. Coup de Grace is")
    a("  +8% while they are below 40% HP. They apply per hit, not to the combo")
    a("  as a lump.")
    a("- Stormsurge Squall (125 + 10% AP) counts when the R → W+Q stretch")
    a("  deals 25% of max HP. Luden is the isolated-target dump, 150 + 10% AP,")
    a("  once. Liandry is 2% max HP per second for 3 seconds.")
    a("- Lich Bane's spellblade needs an auto after the spell. Q's channel")
    a("  locks attacks, so the proc is not in this combo.")
    a("- Deathcap is +30% AP, including runes. Percent pen stacks multiplicatively.")
    a("  Flat pen can push MR below zero.")
    a("- Gold is an unfed farmer. Sorcs and the first legendary land around")
    a("  5:00 and 12:00, the fourth legendary in the high 20s, the fifth around")
    a("  33:00. A kill lead finishes the same order sooner.")
    a("- Same-item dips of a few hundred damage are the 40% execute line")
    a("  (Shadowflame and Coup de Grace) flicking off as the target gains HP.")
    a("- Skill order is Q start, then W max, Q, E. R at 6/11/16.")
    a("")
    return "\n".join(lines) + "\n"


def self_check() -> None:
    assert abs(blight_ratio(5, 0, 3, False) - 0.135) < 1e-9
    assert abs(blight_ratio(5, 0, 3, True) - 0.2295) < 1e-9
    assert abs(blight_ratio(5, 100, 1, False) - 0.059) < 1e-9
    assert gathering_storm_ap(0) == 0
    assert gathering_storm_ap(10) == 8
    assert gathering_storm_ap(20) == 24
    assert gathering_storm_ap(30) == 48
    assert abs(absolute_focus_ap(1) - 3.0) < 1e-9
    assert abs(absolute_focus_ap(18) - 33.18) < 1e-6
    # 0 MR, 0 armor, 0 AP, level 13 (W and Q max, R rank 2): W active after
    # a scripted chunk. Use pick mode so the only missing-HP source is R+Q+blight.
    level = 13
    st = compute_stats([], level, 0, use_af=False, use_gs=False)
    # Strip shards by passing use flags and empty items — shards still apply.
    # Build the expected active from the real function instead, and check the
    # ratio helper against a hand total.
    target = {"hp": 2000.0, "mr": 0.0, "armor": 0.0, "tenacity": 0.0, "level": 13}
    # No items, AF+GS off, but shards still add 18 AP. Turn shards off by
    # giving 0 and checking blight math in isolation above. Here, confirm
    # pen: 80 MR, 40% + 12 flat → 36, multiplier 100/136.
    mult = magic_mult(80, [0.40], 12, 0)
    assert abs(mult - (100 / 136)) < 1e-9
    neg = magic_mult(40, [0.40], 30, 0)  # 24 - 30 = -6
    assert abs(neg - (100 / 94)) < 1e-9
    # W active per stack at rank 5, full charge, 3 stacks, 1000 missing, 0 MR.
    # Reconstruct with a dummy simulate by using level 13 and a target, then
    # reading the tag. Shards/AF make AP nonzero, so check the tag is > 0
    # and scales: more missing HP (lower prior damage) is covered by the
    # formula unit above.
    out = simulate(st, level, 0, target, "coup", "pick")
    assert out["tags"].get("w_active", 0) > 0
    assert out["tags"].get("blight_q", 0) > 0
    assert out["stacks"] == 3
    # Tenacity: mercs → 2 stacks.
    merc = dict(target)
    merc["tenacity"] = 0.30
    out_m = simulate(st, level, 0, merc, "cut", "pick")
    assert out_m["stacks"] == 2
    assert out_m["damage"] < out["damage"]


def main() -> None:
    self_check()
    here = os.path.dirname(os.path.abspath(__file__))
    print("Searching item orders...")
    found = search()
    top = rescore_top(found, 30)
    winner = top[0]
    # Accurate Nashor-first, if the winner is not already that.
    nashor = next((r for r in top if r["items"][0] == "Nashor's Tooth"), None)
    if nashor is None:
        nashor_fast = next(r for r in found if r["items"][0] == "Nashor's Tooth")
        nashor = score_path(
            nashor_fast["items"],
            nashor_fast["boots_at"],
            nashor_fast["rune"],
            accurate=True,
        )

    tradeoffs = []
    specs = [
        ("Absolute Focus + Gathering Storm", True, True),
        ("Manaflow + Gathering Storm", False, True),
        ("Manaflow + Absolute Focus", True, False),
    ]
    for label, af, gs in specs:
        # Manaflow itself adds no damage; dropping AF or GS is the whole cost.
        row = score_path(
            winner["items"],
            winner["boots_at"],
            winner["rune"],
            use_af=af,
            use_gs=gs,
            accurate=True,
        )
        row["label"] = label
        tradeoffs.append(row)

    curve = minute_curve(winner["items"], winner["boots_at"], winner["rune"])
    # Attach combine numbers into the json spikes.
    for row in winner["spikes"]:
        row["combine"] = combine_delta(
            row["owned"], row["item"], row["minute"], winner["rune"]
        )

    fifth_names = [
        "Cryptbloom",
        "Horizon Focus",
        "Zhonya's Hourglass",
        "Nashor's Tooth",
        "Luden's Echo",
    ]
    fifths = []
    core = list(winner["items"][:4])
    for name in fifth_names:
        legs = core + [name]
        if len(set(legs)) < 5:
            continue
        row = score_path(
            legs, winner["boots_at"], winner["rune"], accurate=True
        )
        row["fifth"] = name
        fifths.append(row)

    text = render(winner, top, curve, tradeoffs, fifths)
    # Nashor comparison paragraph injected before Assumptions.
    if winner["items"][0] != "Nashor's Tooth" and nashor is not None:
        w3 = winner["spikes"][2]["allin_pct"]
        n3 = nashor["spikes"][2]["allin_pct"]
        wf = winner["spikes"][-1]["allin_pct"]
        nf = nashor["spikes"][-1]["allin_pct"]
        extra = (
            "\nNashor's Tooth first\n"
            "-------------------\n"
            "Best order that starts Nashor's, same search:\n"
            f"  {' → '.join(nashor['items'])}\n"
            f"  Boots slot: {nashor['boots_at']}. Finish rune: {nashor['rune']}.\n"
            f"  All-in at item 3: {n3}% HP vs the winner's {w3}%.\n"
            f"  All-in at item 5: {nf}% HP vs the winner's {wf}%.\n"
            "Nashor is the attack-speed / on-hit item. This combo's damage is\n"
            "the Blight pop, and R already applies the stacks, so a pen or AP\n"
            "legendary finishes harder. Buy Nashor only when ult is down often\n"
            "enough that the 3 autos are the whole trade.\n"
        )
        text = text.replace("\nAssumptions\n", extra + "\nAssumptions\n")

    report_path = os.path.join(here, "report.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(text)

    def slim(row: dict) -> dict:
        return {
            "score": round(row["score"], 3),
            "rune": row["rune"],
            "boots_at": row["boots_at"],
            "items": row["items"],
            "spikes": [
                {
                    "item": s["item"],
                    "minute": s["minute"],
                    "level": s["level"],
                    "ap": s["ap"],
                    "allin": s["allin"],
                    "allin_pct": s["allin_pct"],
                    "pick": s["pick"],
                    "pick_pct": s["pick_pct"],
                    "bruiser_pct": s["bruiser_pct"],
                    "gain": s["gain"],
                    "combine": s.get("combine"),
                    "tags": s["tags"],
                }
                for s in row["spikes"]
            ],
        }

    payload = {
        "patch": PATCH,
        "winner": slim(winner),
        "nashor_first": slim(nashor) if nashor else None,
        "top": [slim(r) for r in top[:8]],
        "manaflow_tradeoff": [
            {
                "label": r["label"],
                "spikes_pct": [s["allin_pct"] for s in r["spikes"]],
            }
            for r in tradeoffs
        ],
    }
    with open(os.path.join(here, "results.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
        f.write("\n")
    print(text)
    print(f"Wrote {report_path}")


if __name__ == "__main__":
    main()
