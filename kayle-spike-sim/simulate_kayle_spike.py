#!/usr/bin/env python3
"""
Wild Rift Kayle — late-game spike simulation (patch 7.3).

Locked rush: Kraken Slayer → boots → Dusk and Dawn.
Keystone search: Empowerment, Lethal Tempo, Conqueror, plus the minor
runes whose keywords support on-hit, stacks, attack speed, and the late page.
Question: which finished six-item page spikes hardest late, and which rune
page supports that build. Dusk's extra on-hit counts as a stack for
Empowerment and for Kraken.

Stack rule (Dusk and Dawn Spellblade):
  After an ability, the next attack applies on-hit effects a second time.
  Each on-hit application is one stack.
  E then that auto (E-A) = 2 Empowerment stacks and 2 Kraken stacks.
  The next single auto is the 3rd stack and procs both.

Sources: WR 7.3 patch notes (Kraken, Dusk, Nashor, Guinsoo, Terminus),
league wiki infoboxes, WildRift Alpha 7.3b boot pages.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations, permutations
from typing import Dict, List, Optional, Sequence, Tuple
import json

GAME_MINUTES = 24
FIGHT_SECONDS = 6.0
AS_CAP = 2.5
AS_BASE = 0.667
AS_RATIO = 0.667
AS_BASE_BONUS = 0.13
AS_PER_LEVEL = 0.028

# Late score weights. Kayle autos the frontline; the carry is the second check.
TANK_WEIGHT = 0.60
SQUISHY_WEIGHT = 0.40


# ---------------------------------------------------------------------------
# Economy / level / runes
# ---------------------------------------------------------------------------


def gold_at_minute(m: int) -> int:
    """Solo-lane Kayle who farms for the late page. Six items finish ~22–24:00."""
    if m <= 0:
        return 500
    total = 500
    for t in range(1, m + 1):
        if t <= 6:
            total += 450
        elif t <= 8:
            total += 650
        elif t <= 12:
            total += 780
        elif t <= 15:
            total += 900
        elif t <= 18:
            total += 1050
        elif t <= 21:
            total += 1000
        else:
            total += 850
    return total


def level_at_minute(m: int) -> int:
    table = {
        0: 1,
        1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7, 7: 8, 8: 9,
        9: 10, 10: 11, 11: 11, 12: 12, 13: 13, 14: 13,
        15: 14, 16: 14, 17: 15, 18: 15, 19: 15, 20: 15,
        21: 15, 22: 15, 23: 15, 24: 15,
    }
    return table.get(m, 15)


def skill_ranks(level: int) -> Dict[str, int]:
    """Q max, E second, W last. R at 5 / 9 / 13. Ascension still follows level."""
    order = ["E", "Q", "Q", "Q", "R", "Q", "E", "E", "R", "E", "W", "W", "R", "W", "W"]
    ranks = {"Q": 0, "W": 0, "E": 0, "R": 0}
    for i in range(max(0, min(level, 15))):
        ranks[order[i]] += 1
    return ranks


def level_bonus_as(level: int) -> float:
    """Patch 7.3: each level-up adds AS_PER_LEVEL * (0.7 + 0.04 * level_left)."""
    total = 0.0
    for i in range(1, level):
        total += AS_PER_LEVEL * (0.7 + 0.04 * i)
    return total


def alacrity_as(minute: int) -> float:
    """Legend: Alacrity — 3% + 1% per stack, 17 stacks, 20% cap."""
    stacks = min(17, int(max(0, minute) * 1.6))
    return min(0.20, 0.03 + 0.01 * stacks)


def legend_haste(minute: int) -> float:
    """Legend: Haste — 1.5 ability haste per stack, 10 stacks, 15 cap."""
    stacks = min(10, int(max(0, minute) * 1.0))
    return 1.5 * stacks


def gathering_ap(minute: int) -> float:
    """Gathering Storm, adaptive AP. From 6:00, every 3 minutes.

    Live totals: 4, then 10, 18, 28, and onward (the AD line 2, 5, 9, 14
    doubled). The step grows by 2 AP each tick.
    """
    if minute < 6:
        return 0.0
    n = 1 + (minute - 6) // 3
    if n == 1:
        ad = 2.0
    else:
        ad = 2.0 + (n - 1) * 3 + (n - 2) * (n - 1) / 2.0
    return ad * 2.0


def absolute_focus_ap(level: int) -> float:
    """4–40 AP while above 65% health. Kayle is the attacker here, so it is on."""
    return _lerp(level, 4, 40)


def zeal_per_stack(level: int, ap: float) -> float:
    if level >= 13:
        base = 0.07
    elif level >= 9:
        base = 0.06
    elif level >= 5:
        base = 0.05
    else:
        base = 0.04
    return base + (ap / 100.0) * 0.01


def bonus_attack_speed(
    level: int,
    ap: float,
    item_as: float,
    minute: int,
    zeal_stacks: int,
    seething: int,
    extra_as: float = 0.0,
    alacrity: bool = True,
) -> float:
    return (
        AS_BASE_BONUS
        + level_bonus_as(level)
        + item_as
        + (alacrity_as(minute) if alacrity else 0.0)
        + zeal_stacks * zeal_per_stack(level, ap)
        + 0.08 * seething
        + extra_as
    )


def attack_speed(
    level: int,
    ap: float,
    item_as: float,
    minute: int,
    zeal_stacks: int,
    seething: int,
    extra_as: float = 0.0,
    alacrity: bool = True,
) -> float:
    bonus = bonus_attack_speed(
        level, ap, item_as, minute, zeal_stacks, seething, extra_as, alacrity
    )
    return min(AS_CAP, AS_BASE + AS_RATIO * bonus)


# ---------------------------------------------------------------------------
# Items
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Item:
    name: str
    cost: int
    ad: float = 0
    ap: float = 0
    ah: float = 0
    hp: float = 0
    as_pct: float = 0
    flat_mpen: float = 0
    pct_mpen: float = 0
    unique: bool = False
    # Finished-item flags
    kraken: bool = False
    dusk: bool = False
    sheen: bool = False
    nashor: bool = False
    deathcap: bool = False
    guinsoo: bool = False
    terminus: bool = False
    rift: bool = False
    orb: bool = False
    boots: bool = False


ITEMS: Dict[str, Item] = {
    "Long Sword": Item("Long Sword", 500, ad=12),
    "Dagger": Item("Dagger", 400, as_pct=0.12),
    "Pickaxe": Item("Pickaxe", 800, ad=20),
    "Amplifying Tome": Item("Amplifying Tome", 500, ap=20),
    "Blasting Wand": Item("Blasting Wand", 800, ap=45),
    "Needlessly Large Rod": Item("Needlessly Large Rod", 1400, ap=70),
    "Fiendish Codex": Item("Fiendish Codex", 900, ap=25, ah=10),
    "Hextech Alternator": Item("Hextech Alternator", 1100, ap=40),
    "Recurve Bow": Item("Recurve Bow", 900, as_pct=0.20),
    "Hearthbound Axe": Item("Hearthbound Axe", 1200, ad=15, as_pct=0.15),
    "Sheen": Item("Sheen", 800, ah=10, sheen=True),
    "Kindlegem": Item("Kindlegem", 1000, hp=200, ah=10),
    "Haunting Guise": Item("Haunting Guise", 1300, ap=30, hp=200),
    "Void Amethyst": Item("Void Amethyst", 1000, ap=20, pct_mpen=0.15),
    "Boots of Speed": Item("Boots of Speed", 400, unique=True, boots=True),
    "Berserker's Greaves": Item(
        "Berserker's Greaves", 1200, as_pct=0.35, unique=True, boots=True
    ),
    "Boots of Mana": Item(
        "Boots of Mana",
        1200,
        ap=25,
        flat_mpen=8,
        unique=True,
        boots=True,
    ),
    "Gunmetal Greaves": Item(
        "Gunmetal Greaves", 2200, as_pct=0.50, unique=True, boots=True
    ),
    "Spellslinger's Shoes": Item(
        "Spellslinger's Shoes",
        2200,
        ap=35,
        flat_mpen=18,
        pct_mpen=0.08,
        unique=True,
        boots=True,
    ),
    "Kraken Slayer": Item(
        "Kraken Slayer",
        2900,
        ad=45,
        as_pct=0.35,
        unique=True,
        kraken=True,
    ),
    "Dusk and Dawn": Item(
        "Dusk and Dawn",
        3100,
        ap=60,
        ah=20,
        hp=300,
        as_pct=0.20,
        unique=True,
        dusk=True,
    ),
    "Nashor's Tooth": Item(
        "Nashor's Tooth",
        2900,
        ap=80,
        ah=15,
        as_pct=0.50,
        unique=True,
        nashor=True,
    ),
    "Rabadon's Deathcap": Item(
        "Rabadon's Deathcap", 3400, ap=130, unique=True, deathcap=True
    ),
    "Guinsoo's Rageblade": Item(
        "Guinsoo's Rageblade",
        3000,
        ad=35,
        ap=30,
        as_pct=0.30,
        unique=True,
        guinsoo=True,
    ),
    "Void Staff": Item(
        "Void Staff", 3000, ap=95, pct_mpen=0.40, unique=True
    ),
    "Terminus": Item(
        "Terminus", 3000, ad=35, as_pct=0.35, unique=True, terminus=True
    ),
    "Riftmaker": Item(
        "Riftmaker", 3100, ap=80, ah=15, hp=350, unique=True, rift=True
    ),
    "Infinity Orb": Item(
        "Infinity Orb",
        3100,
        ap=110,
        flat_mpen=15,
        unique=True,
        orb=True,
    ),
}


# Component credit when the finished item is bought.
UPGRADE: Dict[str, Tuple[str, ...]] = {
    "Hearthbound Axe": ("Long Sword", "Dagger"),
    "Recurve Bow": ("Dagger",),
    "Kraken Slayer": ("Hearthbound Axe", "Recurve Bow", "Long Sword"),
    "Berserker's Greaves": ("Boots of Speed",),
    "Boots of Mana": ("Boots of Speed", "Amplifying Tome"),
    "Gunmetal Greaves": ("Berserker's Greaves",),
    "Spellslinger's Shoes": ("Boots of Mana",),
    "Dusk and Dawn": ("Sheen", "Blasting Wand", "Kindlegem"),
    "Nashor's Tooth": ("Recurve Bow", "Blasting Wand", "Fiendish Codex"),
    "Rabadon's Deathcap": ("Needlessly Large Rod", "Needlessly Large Rod"),
    "Guinsoo's Rageblade": ("Amplifying Tome", "Recurve Bow", "Pickaxe"),
    "Void Staff": ("Needlessly Large Rod", "Void Amethyst"),
    "Terminus": ("Hearthbound Axe", "Recurve Bow"),
    "Riftmaker": ("Haunting Guise", "Fiendish Codex"),
    "Infinity Orb": ("Hextech Alternator", "Needlessly Large Rod"),
}

# Explicit buy order for each finisher, components first.
FINISHER_STEPS: Dict[str, List[str]] = {
    "Nashor's Tooth": ["Recurve Bow", "Blasting Wand", "Fiendish Codex", "Nashor's Tooth"],
    "Rabadon's Deathcap": [
        "Needlessly Large Rod",
        "Needlessly Large Rod",
        "Rabadon's Deathcap",
    ],
    "Guinsoo's Rageblade": [
        "Amplifying Tome",
        "Recurve Bow",
        "Pickaxe",
        "Guinsoo's Rageblade",
    ],
    "Void Staff": ["Needlessly Large Rod", "Void Amethyst", "Void Staff"],
    "Terminus": [
        "Long Sword",
        "Dagger",
        "Hearthbound Axe",
        "Recurve Bow",
        "Terminus",
    ],
    "Riftmaker": ["Haunting Guise", "Fiendish Codex", "Riftmaker"],
    "Infinity Orb": ["Hextech Alternator", "Needlessly Large Rod", "Infinity Orb"],
}

FINISH_POOL = [
    "Nashor's Tooth",
    "Rabadon's Deathcap",
    "Guinsoo's Rageblade",
    "Void Staff",
    "Terminus",
    "Riftmaker",
    "Infinity Orb",
]

BOOT_LINES = {
    "Gunmetal Greaves": ("Boots of Speed", "Berserker's Greaves", "Gunmetal Greaves"),
    "Spellslinger's Shoes": (
        "Boots of Speed",
        "Amplifying Tome",
        "Boots of Mana",
        "Spellslinger's Shoes",
    ),
}

FINISHED_NAMES = {
    "Kraken Slayer",
    "Dusk and Dawn",
    "Berserker's Greaves",
    "Boots of Mana",
    "Gunmetal Greaves",
    "Spellslinger's Shoes",
    *FINISH_POOL,
}


def resolve_inventory(path: Sequence[str], gold: int) -> List[str]:
    owned: List[str] = []
    pool = gold
    for step in path:
        item = ITEMS[step]
        if item.unique and step in owned:
            continue
        cost = item.cost
        temp = list(owned)
        remove: List[str] = []
        for comp in UPGRADE.get(step, ()):
            if comp in temp:
                cost -= ITEMS[comp].cost
                temp.remove(comp)
                remove.append(comp)
        cost = max(0, cost)
        if pool < cost:
            break
        pool -= cost
        for comp in remove:
            owned.remove(comp)
        owned.append(step)
    return owned


def core_steps(boot_upgrade: str) -> List[str]:
    """Kraken → tier-2 boots → Dusk. Boot upgrade is appended later."""
    line = BOOT_LINES[boot_upgrade]
    # tier-2 is everything except the final upgrade
    tier2 = list(line[:-1])
    return [
        "Long Sword",
        "Dagger",
        "Hearthbound Axe",
        "Recurve Bow",
        "Long Sword",
        "Kraken Slayer",
        *tier2,
        "Sheen",
        "Blasting Wand",
        "Kindlegem",
        "Dusk and Dawn",
    ]


def path_for(boot_upgrade: str, finishers: Sequence[str], upgrade_at: int) -> List[str]:
    """upgrade_at: 0 = right after Dusk, 1 = after first finisher, ... 3 = last."""
    steps = core_steps(boot_upgrade)
    upgrade = BOOT_LINES[boot_upgrade][-1]
    for i, name in enumerate(finishers):
        if upgrade_at == i:
            steps.append(upgrade)
        steps.extend(FINISHER_STEPS[name])
    if upgrade_at >= len(finishers):
        steps.append(upgrade)
    return steps


# ---------------------------------------------------------------------------
# Targets
# ---------------------------------------------------------------------------


@dataclass
class Target:
    name: str
    hp: float
    armor: float
    mr: float


def squishy_at(minute: int) -> Target:
    level = level_at_minute(minute)
    hp = 640 + 95 * level + 35 * minute
    armor = 28 + 3.1 * level + (0 if minute < 10 else 18 if minute < 16 else 40)
    mr = 30 + 1.25 * level + (0 if minute < 10 else 12 if minute < 16 else 30)
    return Target("squishy", hp, armor, mr)


def tank_at(minute: int) -> Target:
    level = level_at_minute(minute)
    hp = 720 + 115 * level + 70 * max(0, minute - 4)
    extra_ar = 0 if minute < 6 else min(11 * (minute - 6), 160)
    extra_mr = 0 if minute < 8 else min(7.5 * (minute - 8), 110)
    return Target("tank", hp, 34 + 3.4 * level + extra_ar, 32 + 1.5 * level + extra_mr)


# ---------------------------------------------------------------------------
# Loadout derived from owned item names
# ---------------------------------------------------------------------------


@dataclass
class Loadout:
    names: Tuple[str, ...]
    bonus_ad: float
    ap: float
    ah: float
    as_pct: float
    hp: float
    flat_mpen: float
    static_mpen: float  # multiplicative percent, before Terminus and the 40% cap
    kraken: bool
    dusk: bool
    sheen: bool
    nashor: bool
    guinsoo: bool
    terminus: bool
    rift: bool
    orb: bool
    deathcap: bool


@dataclass(frozen=True)
class RunePage:
    """One keystone, up to three primary-path slots, one off-path rune."""

    keystone: str
    precision1: str = ""  # brutal | battle_zeal
    precision2: str = ""  # cut_down | coup
    precision3: str = ""  # alacrity | haste
    sorcery2: str = ""  # absolute
    sorcery3: str = ""  # gathering

    def label(self) -> str:
        names = {
            "empowerment": "Empowerment",
            "lethal": "Lethal Tempo",
            "conqueror": "Conqueror",
            "brutal": "Brutal",
            "battle_zeal": "Battle Zeal",
            "cut_down": "Cut Down",
            "coup": "Coup de Grace",
            "alacrity": "Legend: Alacrity",
            "haste": "Legend: Haste",
            "absolute": "Absolute Focus",
            "gathering": "Gathering Storm",
        }
        parts = [names[self.keystone]]
        for key in (
            self.precision1,
            self.precision2,
            self.precision3,
            self.sorcery2,
            self.sorcery3,
        ):
            if key:
                parts.append(names[key])
        return " / ".join(parts)

    def keywords(self) -> List[str]:
        table = {
            "empowerment": ["on-hit", "stack"],
            "lethal": ["basic attack", "attack speed", "stack"],
            "conqueror": ["attack", "ability", "stack"],
            "brutal": ["on-hit"],
            "battle_zeal": ["ability"],
            "cut_down": ["above 60% health"],
            "coup": ["below 40% health"],
            "alacrity": ["attack speed"],
            "haste": ["ability haste"],
            "absolute": ["above 65% health"],
            "gathering": ["late"],
        }
        out: List[str] = []
        for key in (
            self.keystone,
            self.precision1,
            self.precision2,
            self.precision3,
            self.sorcery2,
            self.sorcery3,
        ):
            for word in table.get(key, []):
                if word not in out:
                    out.append(word)
        return out


# The build's own keywords. A rune "supports" the page when its tooltip
# uses one of these.
BUILD_KEYWORDS = (
    "on-hit",
    "stack",
    "attack speed",
    "ability",
    "ability haste",
    "late",
    "above 60% health",
    "below 40% health",
)


def page_is_legal(page: RunePage) -> bool:
    """Primary path can fill its slots. The other path contributes one rune."""
    precision = sum(
        1 for key in (page.precision1, page.precision2, page.precision3) if key
    )
    sorcery = sum(1 for key in (page.sorcery2, page.sorcery3) if key)
    if precision > 3 or sorcery > 2:
        return False
    if precision and sorcery and min(precision, sorcery) > 1:
        return False
    return True


def iter_rune_pages() -> List[RunePage]:
    keys = ("empowerment", "lethal", "conqueror")
    pages: List[RunePage] = []
    for key in keys:
        for slot1 in ("brutal", "battle_zeal"):
            for slot2 in ("cut_down", "coup"):
                for slot3 in ("alacrity", "haste"):
                    for off in ("gathering", "absolute"):
                        page = RunePage(
                            key,
                            slot1,
                            slot2,
                            slot3,
                            "absolute" if off == "absolute" else "",
                            "gathering" if off == "gathering" else "",
                        )
                        pages.append(page)
        # Sorcery primary keeps both late AP runes and one Precision keyword.
        for precision in (
            ("brutal", "", ""),
            ("", "cut_down", ""),
            ("", "coup", ""),
            ("", "", "alacrity"),
            ("", "", "haste"),
        ):
            pages.append(
                RunePage(key, precision[0], precision[1], precision[2], "absolute", "gathering")
            )
    return [page for page in pages if page_is_legal(page)]


DEFAULT_RUNES = RunePage("empowerment", "brutal", "cut_down", "alacrity", "", "gathering")


def loadout_from(
    names: Sequence[str], minute: int, runes: Optional[RunePage] = None
) -> Loadout:
    bonus_ad = ap = ah = as_pct = hp = flat = 0.0
    mpen_remain = 1.0
    flags = dict(
        kraken=False, dusk=False, sheen=False, nashor=False, guinsoo=False,
        terminus=False, rift=False, orb=False, deathcap=False,
    )
    for name in names:
        item = ITEMS[name]
        bonus_ad += item.ad
        ap += item.ap
        ah += item.ah
        as_pct += item.as_pct
        hp += item.hp
        flat += item.flat_mpen
        if item.pct_mpen:
            mpen_remain *= 1.0 - item.pct_mpen
        for key in flags:
            if getattr(item, key):
                flags[key] = True
    page = runes or DEFAULT_RUNES
    if page.sorcery3 == "gathering":
        if ap >= bonus_ad:
            ap += gathering_ap(minute)
        else:
            bonus_ad += gathering_ap(minute) / 2.0
    if page.sorcery2 == "absolute":
        if ap >= bonus_ad:
            ap += absolute_focus_ap(level_at_minute(minute))
        else:
            bonus_ad += absolute_focus_ap(level_at_minute(minute)) / 2.0
    if page.precision3 == "haste":
        ah += legend_haste(minute)
    if flags["rift"]:
        ap += 0.02 * hp
    if flags["deathcap"]:
        ap *= 1.30
    # Sheen is consumed by Dusk. Guard anyway.
    if flags["dusk"]:
        flags["sheen"] = False
    return Loadout(
        names=tuple(names),
        bonus_ad=bonus_ad,
        ap=ap,
        ah=ah,
        as_pct=as_pct,
        hp=hp,
        flat_mpen=flat,
        static_mpen=1.0 - mpen_remain,
        **flags,
    )


def percent_pen(static: float, terminus_dark: int, has_terminus: bool) -> float:
    """Item percent pen stacks multiplicatively, then caps at 40% (Terminus)."""
    remain = 1.0 - static
    if has_terminus and terminus_dark:
        remain *= 1.0 - 0.10 * terminus_dark
    return min(0.40, 1.0 - remain)


def resist_multiplier(resist: float, pct_pen: float, flat_pen: float, shred: float) -> float:
    value = resist * (1.0 - shred)
    value *= 1.0 - pct_pen
    value -= flat_pen
    if value >= 0:
        return 100.0 / (100.0 + value)
    return 2.0 - 100.0 / (100.0 - value)


# ---------------------------------------------------------------------------
# Fight
# ---------------------------------------------------------------------------


@dataclass
class Fight:
    dps: float
    damage: float
    kill_time: Optional[float]
    attacks: int
    onhits: int
    emp_procs: int
    kraken_procs: int
    spellblades: int
    phantoms: int
    sources: Dict[str, float]
    diary: List[dict] = field(default_factory=list)
    as_end: float = 0
    ap: float = 0
    bonus_ad: float = 0
    kill_dps: float = 0


def _lerp(level: int, lo: float, hi: float) -> float:
    return lo + (hi - lo) * ((level - 1) / 14.0)


def kraken_damage(level: int, ranged: bool, missing_frac: float) -> float:
    base = _lerp(level, 120, 168) if ranged else _lerp(level, 150, 210)
    return base * (1.0 + 0.75 * max(0.0, min(1.0, missing_frac)))


def empowerment_damage(level: int) -> float:
    return _lerp(level, 60, 200)


def simulate_fight(
    load: Loadout,
    level: int,
    minute: int,
    target: Target,
    duration: float = FIGHT_SECONDS,
    include_ult: bool = False,
    dusk_double: bool = True,
    diary_limit: int = 12,
    runes: Optional[RunePage] = None,
) -> Fight:
    ranks = skill_ranks(level)
    q_rank = max(1, ranks["Q"])
    e_rank = max(1, ranks["E"])
    r_rank = ranks["R"]
    q_base = [0, 70, 120, 170, 220][q_rank]
    q_cd = [0, 11, 10, 9, 8][q_rank] * (100.0 / (100.0 + load.ah))
    e_cd = [0, 8, 7.5, 7, 6.5][e_rank] * (100.0 / (100.0 + load.ah))
    w_cd = 14.0 * (100.0 / (100.0 + load.ah))
    e_flat = [0, 8, 11, 14, 17][e_rank]
    e_missing_flat = [0, 0.07, 0.08, 0.09, 0.10][e_rank]
    r_base = [0, 150, 225, 300][r_rank] if r_rank else 0
    base_only = 54 + 3 * (level - 1)
    magic_adaptive = load.ap >= load.bonus_ad
    ranged = level >= 5
    page = runes or DEFAULT_RUNES

    hp = target.hp
    max_hp = target.hp
    sources: Dict[str, float] = {}
    diary: List[dict] = []
    emp_stacks = 0
    kraken_stacks = 0
    dark_stacks = 0
    light_turn = False  # False → next on-hit is Light, True → next is Dark
    emp_amp = False
    zeal = 5 if level >= 13 else 0
    seething = 0
    phantom_stacks = 0
    armed = False
    primer: Optional[str] = None
    e_mark = False
    sb_ready = 0.0
    shred_until = -1.0
    q_ready = 0.0
    e_ready = 0.0
    w_ready = 0.0
    ult_done = False
    attacks = onhits = emp_procs = kraken_procs = spellblades = phantoms = 0
    dealt = 0.0
    kill_time: Optional[float] = None
    conq_stacks = 0
    lt_stacks = 0

    def live_ap_ad() -> Tuple[float, float]:
        ap = load.ap
        ad = load.bonus_ad
        if page.keystone == "conqueror" and conq_stacks:
            if magic_adaptive:
                ap += conq_stacks * _lerp(level, 5.0, 8.33)
            else:
                ad += conq_stacks * _lerp(level, 3.0, 5.0)
        return ap, ad

    def add_conq() -> None:
        nonlocal conq_stacks
        if page.keystone == "conqueror":
            conq_stacks = min(6, conq_stacks + 1)

    def lt_bonus_as() -> float:
        if page.keystone != "lethal":
            return 0.0
        per = 0.064 if ranged else 0.08
        return lt_stacks * per

    def current_as(ap: float) -> float:
        return attack_speed(
            level,
            ap,
            load.as_pct,
            minute,
            zeal,
            seething,
            extra_as=lt_bonus_as(),
            alacrity=page.precision3 == "alacrity",
        )

    def ability_amp(t: float) -> float:
        if page.precision1 != "battle_zeal":
            return 1.0
        # 2% at the start of combat, +2% each second, cap 6%.
        return 1.0 + min(0.06, 0.02 * (1 + int(t)))

    as_now = current_as(load.ap)

    def shred_at(t: float) -> float:
        return 0.20 if t < shred_until else 0.0

    def deal(raw: float, typ: str, source: str, t: float) -> None:
        nonlocal hp, dealt, kill_time
        if raw <= 0:
            return
        magic_pen = percent_pen(load.static_mpen, dark_stacks, load.terminus)
        armor_pen = percent_pen(0.0, dark_stacks, load.terminus)
        if typ == "magic":
            mult = resist_multiplier(target.mr, magic_pen, load.flat_mpen, shred_at(t))
        else:
            mult = resist_multiplier(target.armor, armor_pen, 0.0, shred_at(t))
        amount = raw * mult
        amount *= 1.0 + (rift_bonus(t) if load.rift else 0.0)
        if emp_amp:
            amount *= 1.09
        frac = 1.0 if max_hp <= 0 else hp / max_hp
        if page.precision2 == "cut_down" and frac > 0.60:
            amount *= 1.08
        elif page.precision2 == "coup" and frac < 0.40:
            amount *= 1.08
        dealt += amount
        # Missing-health ratios use a body that can fall to 0. Damage keeps
        # counting after that so a build that deletes the first target still
        # shows the swings that hit the next one.
        hp = max(0.0, max_hp - dealt)
        sources[source] = sources.get(source, 0.0) + amount
        if kill_time is None and dealt >= max_hp:
            kill_time = t

    def rift_bonus(t: float) -> float:
        return 0.02 * min(4, int(t))

    def cast_q(t: float) -> None:
        nonlocal q_ready, shred_until, armed, primer
        add_conq()
        ap_now, ad_now = live_ap_ad()
        raw = (q_base + 0.60 * ad_now + 0.50 * ap_now) * ability_amp(t)
        if load.orb and hp / max_hp < 0.40:
            raw *= 1.20
        deal(raw, "magic", "Q", t)
        shred_until = t + 4.0
        q_ready = t + q_cd
        armed = True
        if primer is None:
            primer = "Q"

    def cast_e(t: float) -> None:
        nonlocal e_ready, e_mark, armed, primer
        add_conq()
        e_mark = True
        e_ready = t + e_cd
        armed = True
        primer = "E"

    def cast_w(t: float) -> None:
        nonlocal w_ready, armed, primer
        add_conq()
        w_ready = t + w_cd
        armed = True
        primer = "W"

    # Opener: Q shred, then E, then the first auto is E-A.
    cast_q(0.0)
    cast_e(0.0)

    t = 0.0
    while t <= duration + 1e-9:
        if include_ult and r_rank and not ult_done and t >= 2.5:
            add_conq()
            ap_now, ad_now = live_ap_ad()
            raw = (r_base + 0.85 * ad_now + 0.60 * ap_now) * ability_amp(t)
            if load.orb and hp / max_hp < 0.40:
                raw *= 1.20
            deal(raw, "magic", "R", t)
            ult_done = True

        add_conq()
        if page.keystone == "lethal":
            lt_stacks = min(6, lt_stacks + 1)
        ap_now, ad_now = live_ap_ad()
        as_now = current_as(ap_now)
        e_onhit = e_flat + 0.05 * ad_now + 0.15 * ap_now
        e_missing = e_missing_flat + 0.02 * (ap_now / 100.0)
        ad_total = base_only + ad_now
        want_sb = (load.dusk or load.sheen) and t >= sb_ready - 1e-9 and not armed
        if t >= e_ready - 1e-9 and (want_sb or not (load.dusk or load.sheen)):
            cast_e(t)
            want_sb = False
        if t >= q_ready - 1e-9 and (t >= shred_until - 0.05 or want_sb):
            cast_q(t)
            want_sb = False
        if (
            not armed
            and (load.dusk or load.sheen)
            and t >= sb_ready - 1e-9
            and t >= w_ready - 1e-9
        ):
            cast_w(t)

        doubled = False
        used_primer = None
        spellblade = False
        if armed and (load.dusk or load.sheen) and t >= sb_ready - 1e-9:
            spellblade = True
            doubled = bool(load.dusk and dusk_double)
            used_primer = primer
            armed = False
            primer = None
            sb_ready = t + 1.5
            spellblades += 1

        phantom = False
        if load.guinsoo and seething >= 4:
            phantom_stacks += 1
            if phantom_stacks >= 3:
                phantom_stacks = 0
                phantom = True
                phantoms += 1

        apps = 1 + (1 if doubled else 0) + (1 if phantom else 0)
        if spellblade and used_primer == "E" and doubled:
            label = "E-A"
        elif spellblade and used_primer == "Q" and doubled:
            label = "Q-A"
        elif spellblade and used_primer == "W" and doubled:
            label = "W-A"
        elif e_mark:
            label = "E"
        else:
            label = "auto"
        if phantom:
            label += "+phantom"

        emp_before = emp_stacks
        kraken_before = kraken_stacks
        emp_proc = False
        kraken_proc = False

        deal(ad_total, "physical", "auto", t)

        if spellblade and load.dusk:
            deal(0.75 * base_only + 0.10 * ap_now, "magic", "dusk", t)
        elif spellblade and load.sheen:
            deal(base_only, "physical", "sheen", t)

        if e_mark:
            raw = e_missing * max(0.0, max_hp - hp) * ability_amp(t)
            if load.orb and hp / max_hp < 0.40:
                raw *= 1.20
            deal(raw, "magic", "E active", t)
            e_mark = False

        if page.keystone == "lethal" and lt_stacks >= 6:
            bonus_frac = bonus_attack_speed(
                level,
                ap_now,
                load.as_pct,
                minute,
                zeal,
                seething,
                extra_as=lt_bonus_as(),
                alacrity=page.precision3 == "alacrity",
            )
            bullet = _lerp(level, 6 if ranged else 9, 24 if ranged else 30)
            scale = 0.0067 if ranged else 0.01
            bullet *= 1.0 + scale * (bonus_frac * 100.0)
            deal(bullet, "magic" if magic_adaptive else "physical", "lethal", t)

        if level >= 9 and zeal >= 4:
            deal(e_onhit, "magic", "wave", t)

        for _ in range(apps):
            onhits += 1
            deal(e_onhit, "magic", "E passive", t)
            if load.nashor:
                deal(15 + 0.20 * ap_now, "magic", "nashor", t)
            if page.precision1 == "brutal":
                brutal = 6 + 0.08 * ad_now
                deal(brutal, "magic" if magic_adaptive else "physical", "brutal", t)
            if load.guinsoo:
                deal(30, "magic", "guinsoo", t)
            if load.terminus:
                deal(30, "magic", "terminus", t)
                # On-hit alternates Light / Dark. Dark stacks 10% dual pen, up to 3.
                if light_turn:
                    dark_stacks = min(3, dark_stacks + 1)
                light_turn = not light_turn

            if page.keystone == "empowerment":
                emp_stacks += 1
                if emp_stacks >= 3:
                    emp_stacks = 0
                    emp_procs += 1
                    emp_proc = True
                    raw = empowerment_damage(level)
                    typ = "magic" if magic_adaptive else "physical"
                    # The proc grants the amp; the bonus itself is not amplified.
                    emp_amp = False
                    deal(raw, typ, "empowerment", t)
                    emp_amp = True

            if load.kraken:
                kraken_stacks += 1
                if kraken_stacks >= 3:
                    kraken_stacks = 0
                    kraken_procs += 1
                    kraken_proc = True
                    missing = 0 if max_hp <= 0 else 1.0 - hp / max_hp
                    deal(
                        kraken_damage(level, ranged, missing),
                        "physical",
                        "kraken",
                        t,
                    )

        attacks += 1
        if len(diary) < diary_limit:
            diary.append(
                {
                    "t": round(t, 2),
                    "label": label,
                    "apps": apps,
                    "emp_before": emp_before,
                    "emp_after": emp_stacks,
                    "kraken_before": kraken_before,
                    "kraken_after": kraken_stacks,
                    "emp_proc": emp_proc,
                    "kraken_proc": kraken_proc,
                    "phantom": phantom,
                }
            )

        if zeal < 5:
            zeal += 1
        if load.guinsoo and seething < 4:
            seething += 1
        t += 1.0 / as_now

    if kill_time:
        kill_dps = max_hp / kill_time
    else:
        kill_dps = dealt / duration
    return Fight(
        dps=dealt / duration,
        damage=dealt,
        kill_time=kill_time,
        kill_dps=kill_dps,
        attacks=attacks,
        onhits=onhits,
        emp_procs=emp_procs,
        kraken_procs=kraken_procs,
        spellblades=spellblades,
        phantoms=phantoms,
        sources=sources,
        diary=diary,
        as_end=as_now,
        ap=load.ap,
        bonus_ad=load.bonus_ad,
    )


def score_pair(tank: Fight, squishy: Fight) -> float:
    return TANK_WEIGHT * tank.dps + SQUISHY_WEIGHT * squishy.dps


def fight_pair(
    load: Loadout,
    minute: int,
    include_ult: bool = False,
    dusk_double: bool = True,
    runes: Optional[RunePage] = None,
) -> Tuple[Fight, Fight]:
    level = level_at_minute(minute)
    page = runes or DEFAULT_RUNES
    tank = simulate_fight(
        load,
        level,
        minute,
        tank_at(minute),
        include_ult=include_ult,
        dusk_double=dusk_double,
        runes=page,
    )
    squishy = simulate_fight(
        load,
        level,
        minute,
        squishy_at(minute),
        include_ult=include_ult,
        dusk_double=dusk_double,
        runes=page,
    )
    return tank, squishy


def rune_score(tank: Fight, squishy: Fight) -> float:
    """DPS until the first body drops. Cleanup swings do not pick the rune."""
    return TANK_WEIGHT * tank.kill_dps + SQUISHY_WEIGHT * squishy.kill_dps


LOCKED_BUILD = (
    "Kraken Slayer",
    "Dusk and Dawn",
    "Spellslinger's Shoes",
    "Guinsoo's Rageblade",
    "Terminus",
    "Nashor's Tooth",
)


@dataclass
class RuneResult:
    page: RunePage
    score: float
    tank_kill_dps: float
    squishy_kill_dps: float
    tank_kill: Optional[float]
    squishy_kill: Optional[float]
    swing: float


def compare_runes(minute: int = GAME_MINUTES) -> List[RuneResult]:
    """Rank runes on damage while the target is still up.

    A full-fight kill time lands on the same attack for every Empowerment
    page, so Cut Down and Brutal would look identical. The tank window is
    2.0s (the kill is ~3.2s). The squishy window is 1.2s (the kill is ~1.6s).
    """
    rows: List[RuneResult] = []
    level = level_at_minute(minute)
    for page in iter_rune_pages():
        load = loadout_from(LOCKED_BUILD, minute, page)
        tank, squishy = fight_pair(load, minute, runes=page)
        tank_open = simulate_fight(
            load, level, minute, tank_at(minute), duration=2.0, runes=page
        )
        squish_open = simulate_fight(
            load, level, minute, squishy_at(minute), duration=1.2, runes=page
        )
        open_dps = TANK_WEIGHT * (tank_open.damage / 2.0) + SQUISHY_WEIGHT * (
            squish_open.damage / 1.2
        )
        rows.append(
            RuneResult(
                page=page,
                score=open_dps,
                tank_kill_dps=tank.kill_dps,
                squishy_kill_dps=squishy.kill_dps,
                tank_kill=tank.kill_time,
                squishy_kill=squishy.kill_time,
                swing=score_pair(tank, squishy),
            )
        )
    rows.sort(key=lambda row: (row.score, row.swing), reverse=True)
    return rows


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------


@dataclass
class Page:
    boot: str
    finishers: Tuple[str, ...]
    score: float
    tank_dps: float
    squishy_dps: float
    tank_kill: Optional[float]
    squishy_kill: Optional[float]


def final_names(boot: str, finishers: Sequence[str]) -> List[str]:
    return ["Kraken Slayer", "Dusk and Dawn", boot, *finishers]


def search_pages(minute: int = GAME_MINUTES) -> List[Page]:
    pages: List[Page] = []
    for boot in BOOT_LINES:
        for combo in combinations(FINISH_POOL, 3):
            load = loadout_from(final_names(boot, combo), minute)
            tank, squishy = fight_pair(load, minute)
            pages.append(
                Page(
                    boot=boot,
                    finishers=tuple(combo),
                    score=score_pair(tank, squishy),
                    tank_dps=tank.dps,
                    squishy_dps=squishy.dps,
                    tank_kill=tank.kill_time,
                    squishy_kill=squishy.kill_time,
                )
            )
    pages.sort(key=lambda p: p.score, reverse=True)
    return pages


def best_order(page: Page) -> Tuple[List[str], int, float]:
    """Order the three finishers and the boot upgrade to maximize the curve."""
    best: Tuple[float, List[str], int] = (-1.0, [], 0)
    for perm in permutations(page.finishers):
        for upgrade_at in range(4):
            path = path_for(page.boot, perm, upgrade_at)
            total = 0.0
            for minute in range(12, GAME_MINUTES + 1):
                owned = resolve_inventory(path, gold_at_minute(minute))
                load = loadout_from(owned, minute)
                tank, squishy = fight_pair(load, minute)
                total += score_pair(tank, squishy)
            if total > best[0]:
                best = (total, list(perm), upgrade_at)
    return best[1], best[2], best[0]


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------


def fmt_time(seconds: Optional[float]) -> str:
    if seconds is None:
        return "alive"
    return f"kill {seconds:.2f}s"


def page_label(boot: str, finishers: Sequence[str]) -> str:
    short = {
        "Gunmetal Greaves": "Gunmetal",
        "Spellslinger's Shoes": "Spellslinger",
        "Nashor's Tooth": "Nashor",
        "Rabadon's Deathcap": "Deathcap",
        "Guinsoo's Rageblade": "Guinsoo",
        "Void Staff": "Void",
        "Terminus": "Terminus",
        "Riftmaker": "Riftmaker",
        "Infinity Orb": "Infinity Orb",
    }
    parts = [short.get(boot, boot)] + [short.get(n, n) for n in finishers]
    return " + ".join(parts)


def finished_owned(owned: Sequence[str]) -> List[str]:
    return [n for n in owned if n in FINISHED_NAMES]


def carried(owned: Sequence[str]) -> List[str]:
    """Finished items, plus components that are actually sitting in the inventory."""
    out = []
    for name in owned:
        item = ITEMS[name]
        if name in FINISHED_NAMES or item.ap or item.pct_mpen or item.ad >= 15 or item.sheen:
            out.append(name)
    return out


def diary_line(row: dict) -> str:
    emp = f"{row['emp_before']}→{row['emp_after']}"
    kr = f"{row['kraken_before']}→{row['kraken_after']}"
    flags = []
    if row["emp_proc"]:
        flags.append("Empowerment PROC")
    if row["kraken_proc"]:
        flags.append("Kraken PROC")
    extra = f"   {', '.join(flags)}" if flags else ""
    return (
        f"  {row['t']:4.2f}  {row['label']:<14} on-hit x{row['apps']}"
        f"   Empowerment {emp:<5} Kraken {kr:<5}{extra}"
    )


def build_report(
    pages: List[Page], winner_path: List[str], rune_rows: List[RuneResult]
):
    winner = pages[0]
    minute = GAME_MINUTES
    load = loadout_from(final_names(winner.boot, winner.finishers), minute)
    tank, squishy = fight_pair(load, minute)
    tank_off, _squishy_off = fight_pair(load, minute, dusk_double=False)
    tank_ult, squishy_ult = fight_pair(load, minute, include_ult=True)

    # 4th-item spike from the locked core, same late target, tier-2 boots.
    tier2 = "Berserker's Greaves" if winner.boot == "Gunmetal Greaves" else "Boots of Mana"
    core_names = ["Kraken Slayer", "Dusk and Dawn", tier2]
    core_load = loadout_from(core_names, minute)
    core_tank, core_squishy = fight_pair(core_load, minute)
    core_score = score_pair(core_tank, core_squishy)
    fourth_rows = []
    for name in FINISH_POOL:
        nxt = loadout_from(core_names + [name], minute)
        t, s = fight_pair(nxt, minute)
        fourth_rows.append((score_pair(t, s) - core_score, score_pair(t, s), name, t, s))
    fourth_rows.sort(reverse=True)

    lines: List[str] = []
    a = lines.append
    best_rune = rune_rows[0]
    a("Wild Rift Kayle — best rune for the Kraken / Dusk / Guinsoo page")
    a("Patch 7.3. Solo lane. The six items stay locked. The rune is the search.")
    a("")
    a("BEST RUNE")
    a("  " + best_rune.page.label())
    a(
        "  Keywords: " + ", ".join(best_rune.page.keywords())
        + ". Build keywords those runes cover: "
        + ", ".join(
            word for word in best_rune.page.keywords() if word in BUILD_KEYWORDS
        )
        + "."
    )
    a(
        f"  Alive-window score {best_rune.score:.0f}/s  "
        f"(tank still up for the first 2.0s, squishy for the first 1.2s). "
        f"Full fight: tank {fmt_time(best_rune.tank_kill)}, "
        f"squishy {fmt_time(best_rune.squishy_kill)}."
    )
    a("  Dusk's extra on-hit is an on-hit keyword. Empowerment reads that keyword:")
    a("  E-A = 2 Empowerment stacks and 2 Kraken stacks. Lethal Tempo and")
    a("  Conqueror count the swing once. Conqueror also counts the cast.")
    a("")
    a("RUNE PAGES (top 8, same six items)")
    a("  Ranked on damage while the target is still alive, not on the kill tick.")
    a(f"  {'page':<78} {'open':>7} {'tank':>7} {'squish':>7}")
    for row in rune_rows[:8]:
        a(
            f"  {row.page.label():<78} {row.score:7.0f} "
            f"{row.tank_kill_dps:7.0f} {row.squishy_kill_dps:7.0f}"
        )
    a("  Best page of each keystone:")
    seen_keys = set()
    for row in rune_rows:
        if row.page.keystone in seen_keys:
            continue
        seen_keys.add(row.page.keystone)
        a(f"    {row.page.label()}  —  {row.score:.0f}/s")
    a("")
    a("Wild Rift Kayle — Kraken → boots → Dusk and Dawn")
    a("Patch 7.3. Solo lane. Goal: strongest late-game spike on a finished page.")
    a("")
    a("STACK RULE")
    a("Dusk and Dawn Spellblade: after an ability, the next attack applies")
    a("on-hit effects again (1.5s cooldown). That second application is a stack.")
    a("E-A = 2 stacks on Empowerment and 2 stacks on Kraken.")
    a("Empowerment procs at 3 (60–200 adaptive + 9% damage for the rest of the fight).")
    a("Kraken procs at 3 (120–168 physical ranged, up to +75% from missing health).")
    a("Guinsoo Phantom Hit is a separate extra on-hit and adds a stack the same way.")
    a("")
    a("Opening weave on the finished page, vs the late tank:")
    for row in tank.diary[:8]:
        a(diary_line(row))
    a("")
    a(
        f"In {FIGHT_SECONDS:.0f}s vs tank: {tank.attacks} attacks, {tank.onhits} on-hits, "
        f"{tank.spellblades} spellblades, {tank.phantoms} phantom hits, "
        f"{tank.emp_procs} Empowerment procs, {tank.kraken_procs} Kraken procs."
    )
    a(
        f"Same finished fight with Dusk's extra on-hit turned off "
        f"(Guinsoo phantom still on): "
        f"{tank_off.emp_procs} Empowerment procs, {tank_off.kraken_procs} Kraken procs, "
        f"tank DPS {tank_off.dps:.0f} → {tank.dps:.0f} "
        f"({(tank.dps / max(tank_off.dps, 1) - 1) * 100:.0f}%)."
    )
    core_off_t, _core_off_s = fight_pair(core_load, minute, dusk_double=False)
    core_on_t = core_tank
    a(
        f"Before Guinsoo, on Kraken + {tier2} + Dusk only, that same extra on-hit is "
        f"tank DPS {core_off_t.dps:.0f} → {core_on_t.dps:.0f} "
        f"({(core_on_t.dps / max(core_off_t.dps, 1) - 1) * 100:.0f}%), "
        f"{core_off_t.emp_procs} → {core_on_t.emp_procs} Empowerment procs."
    )
    a("")
    a("WINNER")
    # Reconstruct the printed rush from the path's finished items in buy order.
    seen = []
    for step in winner_path:
        if step in FINISHED_NAMES and step not in seen:
            seen.append(step)
    a("  " + " → ".join(seen))
    a(
        f"  Late score {winner.score:.0f}  "
        f"(60% tank DPS {winner.tank_dps:.0f} / 40% squishy DPS {winner.squishy_dps:.0f})"
    )
    a(
        f"  6s of swinging: tank {tank.damage:.0f} ({tank.dps:.0f}/s, first body {fmt_time(tank.kill_time)})   "
        f"squishy {squishy.damage:.0f} ({squishy.dps:.0f}/s, {fmt_time(squishy.kill_time)})"
    )
    a(
        f"  With R landing once: tank {tank_ult.damage:.0f} ({fmt_time(tank_ult.kill_time)}), "
        f"squishy {squishy_ult.damage:.0f} ({fmt_time(squishy_ult.kill_time)})"
    )
    a(
        f"  Level 15 stats: {load.ap:.0f} AP, {load.bonus_ad:.0f} bonus AD, "
        f"{load.ah:.0f} AH, {tank.as_end:.2f} attack speed"
        f"{' (cap 2.50)' if tank.as_end >= AS_CAP - 0.001 else ''}"
    )
    a("")
    a("Where the tank damage comes from (post-mitigation):")
    for src, amount in sorted(tank.sources.items(), key=lambda kv: -kv[1]):
        a(f"  {src:<14} {amount:7.0f}   {100 * amount / max(tank.damage, 1):4.1f}%")
    a("")
    a("WHY THIS PAGE")
    a("Dusk makes E-A worth two stacks, so Empowerment and Kraken proc on the")
    a("next auto. Guinsoo is the first buy after that because Phantom Hit is")
    a("another extra on-hit: same stacks, and it repeats E passive, Nashor, and")
    a("Terminus. Terminus is the armor pen for Kraken plus magic pen for the")
    a("on-hits, stacking to 30% of each. Nashor is the late spike — its on-hit")
    a("is the one both doubles keep firing, and it is the biggest completion")
    a("jump on the curve.")
    a("Deathcap sets sit behind this. The winning page has a modest AP pool,")
    a("and the cap does not add an on-hit for the extra stack to repeat.")
    a("Void does not replace Terminus here. Void is magic pen only, and item")
    a("percent pen caps at 40%, so stacking it on Terminus wastes the overlap.")
    a("Boots of Mana into Spellslinger beat Berserker into Gunmetal. The full")
    a("page is already at the 2.50 attack speed cap, so more attack speed does")
    a("not add swings. Spellslinger's penetration does.")
    a("Lich Bane is out. It is the same Spellblade unique as Dusk.")
    a("")
    a("4th-item spike if you are sitting on Kraken + tier-2 boots + Dusk")
    a("(same level-15 target, so this is the item spike, not the level spike):")
    for delta, total, name, t, s in fourth_rows:
        a(
            f"  {name:<22} score {total:7.0f}   +{delta:6.0f}   "
            f"tank {t.dps:6.0f}   squishy {s.dps:6.0f}"
        )
    a("")
    a("FULL PAGES (top 8 at minute 24, items finished)")
    a(f"  {'page':<42} {'score':>7} {'tank':>7} {'squishy':>8}  kills")
    for page in pages[:8]:
        a(
            f"  {page_label(page.boot, page.finishers):<42} "
            f"{page.score:7.0f} {page.tank_dps:7.0f} {page.squishy_dps:8.0f}  "
            f"tank {fmt_time(page.tank_kill)}, squishy {fmt_time(page.squishy_kill)}"
        )
    a("")
    a("GAME CURVE — winner path")
    a("Gold is a solo laner playing for the late page, not a support curve.")
    a(f"{'min':>4} {'lv':>3} {'gold':>6}  {'score':>7} {'tank':>7} {'squish':>7}  items")
    prev = None
    spikes = []
    timeline_rows = []
    for m in range(0, GAME_MINUTES + 1):
        owned = resolve_inventory(winner_path, gold_at_minute(m))
        load_m = loadout_from(owned, m)
        t, s = fight_pair(load_m, m)
        sc = score_pair(t, s)
        have = finished_owned(owned)
        holding = carried(owned)
        timeline_rows.append(
            {
                "minute": m,
                "level": level_at_minute(m),
                "gold": gold_at_minute(m),
                "score": round(sc, 1),
                "tank_dps": round(t.dps, 1),
                "squishy_dps": round(s.dps, 1),
                "items": have,
                "inventory": holding,
                "ap": round(load_m.ap, 1),
                "as": round(t.as_end, 3),
                "emp_procs": t.emp_procs,
                "kraken_procs": t.kraken_procs,
            }
        )
        a(
            f"{m:4d} {level_at_minute(m):3d} {gold_at_minute(m):6d}  "
            f"{sc:7.0f} {t.dps:7.0f} {s.dps:7.0f}  "
            f"{', '.join(holding) if holding else '—'}"
        )
        if prev is not None:
            new_items = [n for n in have if n not in prev[0]]
            if new_items:
                spikes.append((m, new_items, sc - prev[1], sc))
        prev = (have, sc)
    a("")
    a("SPIKES (minute the finished item is bought, score vs the minute before)")
    for m, names, delta, sc in spikes:
        a(f"  {m:4.0f}:00  {', '.join(names):<28} score {sc:7.0f}   {delta:+7.0f}")
    a("")
    a("ASSUMPTIONS")
    a("- 6s all-in. Damage keeps counting after the first target drops, so two")
    a("  pages are not tied just because both delete one body. Q and E open")
    a("  together (20% shred for 4s). The first auto is E-A. W primes Dusk when")
    a("  Q and E are both down. R is off in the ranking fight and on in the combo line.")
    a("- A minute with no new item can dip. The target's resists are still climbing.")
    a("- Extra on-hit repeats E passive, Nashor, Brutal, Guinsoo, Terminus, and")
    a("  adds Empowerment / Kraken stacks. It does not repeat the auto, the wave,")
    a("  Dusk's own Spellblade damage, or E's missing-health active.")
    a("- Waves (level 9, Exalted) hit the primary once per attack for E passive damage.")
    a("- Kayle is ranged from level 5, so Kraken uses the ranged numbers after that.")
    a("- Empowerment and Brutal are magic once AP is at least bonus AD.")
    a("- Terminus Dark stacks 10% armor and magic pen, up to 30%. Item percent pen")
    a("  is capped at 40%, so Void + Terminus does not go past 40% magic pen.")
    a("- Attack speed cap 2.50. Zeal is permanent at level 13.")
    a("- Rune page in the item curve is the kill-score winner above.")
    a("  A legal page is one keystone, three slots from the primary path, and")
    a("  one rune from a second path. Bone Plating is the usual defensive")
    a("  flex and is not in the damage.")
    a("- Gathering Storm AP totals from 6:00, every 3 minutes: 4, 10, 18, 28,")
    a("  then onward. Absolute Focus is 4–40 AP while Kayle stays above 65% HP.")
    a("- Lethal Tempo is the 7.3 bullet: 6.4% attack speed per stack for ranged,")
    a("  and at 6 stacks a 6–24 adaptive bullet that scales with bonus attack speed.")
    a("  It does not break the 2.50 cap. Conqueror is 5–8.33 AP per stack at")
    a("  the AP adaptive, 6 stacks, one stack per cast or attack.")
    a("- Boot rush is tier-2 (Berserker or Mana). The matching upgrade")
    a("  (Gunmetal or Spellslinger) finishes that same slot once the legendaries")
    a("  are in. The search picks the line with the higher full-page score.")
    a("- Enchant is not modeled. It does not change the damage page.")
    return "\n".join(lines), timeline_rows, {
        "tank": tank,
        "squishy": squishy,
        "tank_off": tank_off,
        "load": load,
        "seen": seen,
    }


def check_stack_rule() -> None:
    page = RunePage("empowerment", "brutal", "", "alacrity", "", "gathering")
    load = loadout_from(LOCKED_BUILD, GAME_MINUTES, page)
    fight = simulate_fight(
        load,
        level_at_minute(GAME_MINUTES),
        GAME_MINUTES,
        tank_at(GAME_MINUTES),
        runes=page,
    )
    diary = fight.diary
    if len(diary) < 2:
        raise SystemExit("stack diary too short")
    first, second = diary[0], diary[1]
    if first["label"] != "E-A" or first["apps"] != 2:
        raise SystemExit(f"expected E-A x2, got {first}")
    if first["emp_before"] != 0 or first["emp_after"] != 2 or first["emp_proc"]:
        raise SystemExit(f"E-A should land on 2 Empowerment stacks, got {first}")
    if first["kraken_before"] != 0 or first["kraken_after"] != 2 or first["kraken_proc"]:
        raise SystemExit(f"E-A should land on 2 Kraken stacks, got {first}")
    if not (second["emp_proc"] and second["kraken_proc"]):
        raise SystemExit(f"the auto after E-A should proc both, got {second}")


def main() -> None:
    global DEFAULT_RUNES
    rune_rows = compare_runes(GAME_MINUTES)
    DEFAULT_RUNES = rune_rows[0].page
    pages = search_pages(GAME_MINUTES)
    winner = pages[0]
    order, upgrade_at, _curve = best_order(winner)
    winner_path = path_for(winner.boot, order, upgrade_at)
    report, timeline, extra = build_report(pages, winner_path, rune_rows)
    check_stack_rule()
    print(report)
    out_dir = "/workspace/kayle-spike-sim"
    with open(f"{out_dir}/report.txt", "w", encoding="utf-8") as f:
        f.write(report + "\n")

    def fight_blob(fight: Fight) -> dict:
        return {
            "dps": round(fight.dps, 1),
            "damage": round(fight.damage, 1),
            "kill_time": fight.kill_time,
            "attacks": fight.attacks,
            "onhits": fight.onhits,
            "empowerment_procs": fight.emp_procs,
            "kraken_procs": fight.kraken_procs,
            "spellblades": fight.spellblades,
            "phantoms": fight.phantoms,
            "attack_speed": round(fight.as_end, 3),
            "sources": {k: round(v, 1) for k, v in fight.sources.items()},
            "diary": fight.diary,
        }

    payload = {
        "champion": "Kayle",
        "game": "Wild Rift",
        "patch": "7.3",
        "keystone": DEFAULT_RUNES.keystone,
        "rune_page": DEFAULT_RUNES.label(),
        "rune_keywords": DEFAULT_RUNES.keywords(),
        "rush": ["Kraken Slayer", "boots", "Dusk and Dawn"],
        "stack_rule": "E-A = 2 stacks on Empowerment and on Kraken",
        "rune_rows": [
            {
                "page": row.page.label(),
                "keywords": row.page.keywords(),
                "kill_score": round(row.score, 1),
                "tank_kill_dps": round(row.tank_kill_dps, 1),
                "squishy_kill_dps": round(row.squishy_kill_dps, 1),
                "tank_kill": row.tank_kill,
                "squishy_kill": row.squishy_kill,
            }
            for row in rune_rows[:12]
        ],
        "winner": extra["seen"],
        "winner_score": round(winner.score, 1),
        "late_fight": {
            "tank": fight_blob(extra["tank"]),
            "squishy": fight_blob(extra["squishy"]),
            "tank_without_dusk_double": fight_blob(extra["tank_off"]),
            "ap": round(extra["load"].ap, 1),
            "bonus_ad": round(extra["load"].bonus_ad, 1),
        },
        "top_pages": [
            {
                "boot": p.boot,
                "finishers": list(p.finishers),
                "score": round(p.score, 1),
                "tank_dps": round(p.tank_dps, 1),
                "squishy_dps": round(p.squishy_dps, 1),
                "tank_kill": p.tank_kill,
                "squishy_kill": p.squishy_kill,
            }
            for p in pages[:12]
        ],
        "timeline": timeline,
    }
    with open(f"{out_dir}/results.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print(f"\nWrote {out_dir}/report.txt and {out_dir}/results.json")


if __name__ == "__main__":
    main()
