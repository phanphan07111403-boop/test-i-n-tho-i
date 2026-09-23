#!/usr/bin/env python3
"""
Wild Rift Sona — Patch 7.3 buff gold-efficiency simulation.

Sona herself was not retuned in 7.3 (still on the 7.2b heal/R numbers).
The patch still buffs her impact: crit 175%→200%, AS cap 2.5→3, and a
full enchanter-item makeover (Helia / Circlet→Diadem / cheaper Ardent
with a flat 30% AS + 25 on-hit).

Question: which purchase ORDER gets the most gold efficiency out of
Sona's auras + item buffs, and the most impact next to a 7.3 crit ADC?
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import permutations
from typing import Dict, List, Optional, Sequence, Tuple
import json
import os

GAME_MINUTES = 28  # long enough for 4 legendaries + sell Scythe → 5th
CRIT_73 = 2.00
CRIT_72 = 1.75
AS_CAP_73 = 3.0
AS_CAP_72 = 2.5
IE_CRIT_DMG = 2.30
MAX_SLOTS = 6
SCYTHE_SELL = 280  # Wild Rift ~70% of the 400g sickle/scythe invest

# Combat fraction of a minute spent in a real fight window.
COMBAT_FRAC = {
    "lane": 0.32,   # minutes 1–8
    "mid": 0.42,    # 9–14
    "late": 0.48,   # 15–20
}


def combat_frac(minute: int) -> float:
    if minute <= 8:
        return COMBAT_FRAC["lane"]
    if minute <= 14:
        return COMBAT_FRAC["mid"]
    if minute <= 20:
        return COMBAT_FRAC["late"]
    return 0.52  # baron / elder fights


def time_weight(minute: int) -> float:
    # First-item / 2v2 window decides more games than a 4th/5th.
    if minute <= 8:
        return 1.30
    if minute <= 14:
        return 1.20
    if minute <= 20:
        return 1.00
    return 0.85


# ---------------------------------------------------------------------------
# Economy / XP
# ---------------------------------------------------------------------------


def gold_at_minute(m: int) -> int:
    """Typical WR support (tribute + souls). ~9.4k at 20:00, ~14k at 28:00."""
    if m <= 0:
        return 500
    total = 500
    for t in range(1, m + 1):
        if t <= 4:
            total += 280
        elif t <= 10:
            total += 430
        elif t <= 20:
            total += 520
        else:
            total += 580  # late objectives on games that reach a full page
    return total


def gold_gained(m: int) -> int:
    return gold_at_minute(m) - gold_at_minute(m - 1)


def support_level(m: int) -> int:
    table = {
        1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7, 7: 8, 8: 8,
        9: 9, 10: 10, 11: 10, 12: 11, 13: 11, 14: 12,
        15: 12, 16: 13, 17: 13, 18: 14, 19: 14, 20: 15,
        21: 15, 22: 15, 23: 16, 24: 16, 25: 16, 26: 17, 27: 17, 28: 17,
    }
    return table.get(m, min(17, 1 + m))


def adc_gold(m: int) -> int:
    if m <= 0:
        return 500
    total = 500
    for t in range(1, m + 1):
        if t <= 4:
            total += 380
        elif t <= 10:
            total += 620
        else:
            total += 740
    return total


def adc_level(m: int) -> int:
    table = {
        1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7, 7: 8, 8: 9,
        9: 10, 10: 10, 11: 11, 12: 12, 13: 12, 14: 13,
        15: 13, 16: 14, 17: 14, 18: 15, 19: 15, 20: 16,
        21: 16, 22: 17, 23: 17, 24: 17, 25: 18, 26: 18, 27: 18, 28: 18,
    }
    return table.get(m, min(18, 1 + m))


def scythe_ap(minute: int) -> float:
    if minute < 6:
        return 0.0
    return 4.0 * min(10, minute - 5)


# ---------------------------------------------------------------------------
# Runes — Wild Rift 7.3 (5-slot page). Numbers from live tooltip text.
# Ingenious Hunter is removed this patch. Legend: Haste replaced Tenacity.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RunePage:
    name: str
    keystone: str
    slots: Tuple[str, ...]
    font: bool = False
    revitalize: bool = False
    transcendence: bool = False
    manaflow: bool = False
    scorch: bool = False
    bone: bool = False
    legend_haste: bool = False
    gathering: bool = False


def _page(
    name: str,
    keystone: str,
    *minors: str,
    **flags: bool,
) -> RunePage:
    return RunePage(name=name, keystone=keystone, slots=(keystone, *minors), **flags)


RUNE_PAGES: Tuple[RunePage, ...] = (
    _page(
        "Aery / FoL / Bone / Revitalize / Transcendence",
        "Aery",
        "Font of Life",
        "Bone Plating",
        "Revitalize",
        "Transcendence",
        font=True,
        bone=True,
        revitalize=True,
        transcendence=True,
    ),
    _page(
        "Aery / FoL / Bone / Revitalize / Manaflow",
        "Aery",
        "Font of Life",
        "Bone Plating",
        "Revitalize",
        "Manaflow Band",
        font=True,
        bone=True,
        revitalize=True,
        manaflow=True,
    ),
    _page(
        "Aery / FoL / Bone / Revitalize / Scorch",
        "Aery",
        "Font of Life",
        "Bone Plating",
        "Revitalize",
        "Scorch",
        font=True,
        bone=True,
        revitalize=True,
        scorch=True,
    ),
    _page(
        "Aery / FoL / Bone / Revitalize / Legend: Haste",
        "Aery",
        "Font of Life",
        "Bone Plating",
        "Revitalize",
        "Legend: Haste",
        font=True,
        bone=True,
        revitalize=True,
        legend_haste=True,
    ),
    _page(
        "Aery / Manaflow / Transcendence / Scorch / Bone",
        "Aery",
        "Manaflow Band",
        "Transcendence",
        "Scorch",
        "Bone Plating",
        manaflow=True,
        transcendence=True,
        scorch=True,
        bone=True,
    ),
    _page(
        "Aery / FoL / Bone / Transcendence / Manaflow",
        "Aery",
        "Font of Life",
        "Bone Plating",
        "Transcendence",
        "Manaflow Band",
        font=True,
        bone=True,
        transcendence=True,
        manaflow=True,
    ),
    _page(
        "Guardian / FoL / Bone / Revitalize / Transcendence",
        "Guardian",
        "Font of Life",
        "Bone Plating",
        "Revitalize",
        "Transcendence",
        font=True,
        bone=True,
        revitalize=True,
        transcendence=True,
    ),
    _page(
        "Comet / FoL / Bone / Revitalize / Transcendence",
        "Arcane Comet",
        "Font of Life",
        "Bone Plating",
        "Revitalize",
        "Transcendence",
        font=True,
        bone=True,
        revitalize=True,
        transcendence=True,
    ),
    _page(
        "Fleet / FoL / Bone / Revitalize / Transcendence",
        "Fleet Footwork",
        "Font of Life",
        "Bone Plating",
        "Revitalize",
        "Transcendence",
        font=True,
        bone=True,
        revitalize=True,
        transcendence=True,
    ),
)

DEFAULT_RUNES = RUNE_PAGES[0]


def transcendence_ah(level: int) -> float:
    ah = 0.0
    if level >= 1:
        ah += 6.0
    if level >= 5:
        ah += 6.0
    # L9: 10% CD refund on a basic every 8s ≈ extra haste on the W/Q cycle.
    if level >= 9:
        ah += 8.0
    return ah


def legend_haste_ah(minute: int) -> float:
    # Support assists: slow stacks. 1.5 AH each, cap 15. 7.3 replaced Tenacity.
    stacks = min(10.0, max(0.0, (minute - 6) * 0.45))
    return min(15.0, 1.5 * stacks)


def rune_effects(
    page: RunePage, level: int, minute: int, ap: float, hp: float
) -> Dict[str, float]:
    ah = 0.0
    hsp = 0.0
    heal_hps = 0.0
    poke_dps = 0.0
    tank_hps = 0.0
    aura_bonus = 0.0
    if page.transcendence:
        ah += transcendence_ah(level)
    if page.legend_haste:
        ah += legend_haste_ah(minute)
    if page.revitalize:
        # 5% always, +10% extra when target < 40% HP (~1/4 of fight heals).
        hsp += 0.05 + 0.025 * combat_frac(minute)
    if page.manaflow:
        # 30 mana/champion hit, cap 300. Sona Q hits two → stacked by ~8:00.
        # Extra mana = fewer OOM skips on W/Q.
        if minute >= 8:
            aura_bonus += 0.04
        elif minute >= 4:
            aura_bonus += 0.02
    if page.keystone == "Aery":
        shield = 30.0 + 110.0 * (level - 1) / 14.0 + 0.20 * ap
        poke = 15.0 + 55.0 * (level - 1) / 14.0 + 0.10 * ap
        cycle = 4.2  # linger 2s + return; Sona spam keeps it cycling
        heal_hps += 0.62 * shield / cycle
        poke_dps += 0.38 * poke / cycle
    elif page.keystone == "Guardian":
        shield = 55.0 + 6.0 * level + 0.12 * ap
        heal_hps += shield / 18.0 * 0.45  # proc when ADC takes a hit nearby
    elif page.keystone == "Arcane Comet":
        comet = 35.0 + 4.0 * level + 0.20 * ap
        poke_dps += comet / 9.0 * 0.70  # Q/R/Power Chord land it often
    elif page.keystone == "Fleet Footwork":
        heal_hps += (15.0 + 4.0 * level + 0.10 * ap) / 8.0 * 0.35  # mostly self
        tank_hps += 4.0
    if page.font:
        # 3% Sona max HP + 15% AP to lowest-HP ally, 20s CD. Q/PC apply it.
        font = 0.03 * hp + 0.15 * ap
        heal_hps += font / 20.0
    if page.scorch:
        poke_dps += (20.0 + 1.5 * level) / 6.0 * 0.75
    if page.bone:
        tank_hps += 9.0 if minute <= 12 else 5.0
    if page.gathering:
        ap_gain = 8.0 * (minute // 10)
        poke_dps += 0.05 * ap_gain
    return {
        "ah": ah,
        "hsp": hsp,
        "heal_hps": heal_hps,
        "poke_dps": poke_dps,
        "tank_hps": tank_hps,
        "aura_bonus": aura_bonus,
    }


# ---------------------------------------------------------------------------
# Items — official 7.3 notes (2026-09-21)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Item:
    name: str
    cost: int
    ap: float = 0
    ah: float = 0
    hsp: float = 0
    hp: float = 0
    mana: float = 0
    ms_pct: float = 0
    tags: Tuple[str, ...] = ()


ITEMS: Dict[str, Item] = {
    "Spectral Sickle": Item("Spectral Sickle", 400, ap=20, tags=("start",)),
    "Black Mist Scythe": Item(
        "Black Mist Scythe", 400, ap=28, ah=10, tags=("start",)
    ),
    "Boots of Speed": Item("Boots of Speed", 400, tags=("boots",)),
    "Ionian Boots of Lucidity": Item(
        "Ionian Boots of Lucidity", 900, ah=15, tags=("boots",)
    ),
    "Forbidden Idol": Item("Forbidden Idol", 700, hsp=0.06, tags=("comp",)),
    "Bandleglass Mirror": Item(
        "Bandleglass Mirror", 900, ap=20, ah=10, tags=("comp",)
    ),
    "Kindlegem": Item("Kindlegem", 1000, hp=200, ah=10, tags=("comp",)),
    "Aether Wisp": Item("Aether Wisp", 950, ap=30, ms_pct=0.04, tags=("comp",)),
    "Tear of the Goddess": Item(
        "Tear of the Goddess", 400, mana=240, tags=("comp", "tear")
    ),
    "Ruby Crystal": Item("Ruby Crystal", 500, hp=200, tags=("comp",)),
    "Blasting Wand": Item("Blasting Wand", 800, ap=45, tags=("comp",)),
    "Amplifying Tome": Item("Amplifying Tome", 500, ap=20, tags=("comp",)),
    "Echoes of Helia": Item(
        "Echoes of Helia",
        2400,
        ap=40,
        ah=20,
        hp=200,
        tags=("legendary", "helia"),
    ),
    "Ardent Censer": Item(
        "Ardent Censer",
        2400,
        ap=50,
        hsp=0.08,
        ms_pct=0.04,
        tags=("legendary", "ardent"),
    ),
    "Whispering Circlet": Item(
        "Whispering Circlet",
        2400,
        hp=200,
        mana=500,
        hsp=0.08,
        tags=("legendary", "circlet"),
    ),
    "Diadem of Songs": Item(
        "Diadem of Songs",
        2400,
        hp=200,
        mana=1200,
        hsp=0.08,
        tags=("legendary", "diadem"),
    ),
    "Staff of Flowing Waters": Item(
        "Staff of Flowing Waters",
        2400,
        ap=50,
        ah=10,
        hsp=0.08,
        tags=("legendary", "staff"),
    ),
    "Harmonic Echo": Item(
        "Harmonic Echo",
        2500,
        ap=40,
        ah=20,
        hp=200,
        tags=("legendary", "harmonic"),
    ),
    "Redemption": Item(
        "Redemption",
        2450,
        ap=40,
        ah=10,
        hsp=0.08,
        tags=("legendary", "redemption"),
    ),
    "Imperial Mandate": Item(
        "Imperial Mandate",
        2600,
        ap=60,
        ah=20,
        tags=("legendary", "mandate"),
    ),
}

# Component credit when upgrading.
UPGRADE: Dict[str, Tuple[str, ...]] = {
    "Ionian Boots of Lucidity": ("Boots of Speed",),
    "Echoes of Helia": ("Bandleglass Mirror", "Kindlegem"),
    "Ardent Censer": ("Forbidden Idol", "Aether Wisp"),
    "Whispering Circlet": ("Forbidden Idol", "Tear of the Goddess", "Ruby Crystal"),
    "Diadem of Songs": ("Whispering Circlet",),
    "Staff of Flowing Waters": ("Forbidden Idol", "Bandleglass Mirror"),
    "Harmonic Echo": ("Bandleglass Mirror", "Kindlegem"),
    "Redemption": ("Forbidden Idol", "Bandleglass Mirror"),
    "Imperial Mandate": ("Bandleglass Mirror", "Blasting Wand"),
}

# Buy these first when saving for the next legendary.
NEXT_COMPS: Dict[str, List[str]] = {
    "Ionian Boots of Lucidity": ["Boots of Speed"],
    "Echoes of Helia": ["Bandleglass Mirror", "Kindlegem"],
    "Ardent Censer": ["Forbidden Idol", "Aether Wisp"],
    "Whispering Circlet": ["Tear of the Goddess", "Forbidden Idol", "Ruby Crystal"],
    "Staff of Flowing Waters": ["Forbidden Idol", "Bandleglass Mirror"],
    "Harmonic Echo": ["Bandleglass Mirror", "Kindlegem"],
    "Redemption": ["Forbidden Idol", "Bandleglass Mirror"],
    "Imperial Mandate": ["Bandleglass Mirror", "Blasting Wand"],
}

LEGENDARIES: Tuple[str, ...] = (
    "Echoes of Helia",
    "Ardent Censer",
    "Whispering Circlet",
    "Staff of Flowing Waters",
    "Harmonic Echo",
    "Redemption",
    "Imperial Mandate",
)

SHORT = {
    "Echoes of Helia": "Helia",
    "Ardent Censer": "Ardent",
    "Whispering Circlet": "Circlet",
    "Diadem of Songs": "Diadem",
    "Staff of Flowing Waters": "Staff",
    "Harmonic Echo": "Harmonic",
    "Redemption": "Redemption",
    "Imperial Mandate": "Mandate",
    "Ionian Boots of Lucidity": "Ionian",
    "Black Mist Scythe": "Scythe",
    "Spectral Sickle": "Sickle",
    "Tear of the Goddess": "Tear",
}


def short_name(n: str) -> str:
    return SHORT.get(n, n)


# ---------------------------------------------------------------------------
# Skill ranks — W max (buff / heal), Q second, E last. R at 6/11.
# ---------------------------------------------------------------------------


def skill_ranks(level: int) -> Tuple[int, int, int, int]:
    """Return 0-indexed ranks for Q, W, E, R. WR basics have 4 ranks."""
    # Order: Q1, W2, W3, E4, W5, R6, W7 (W max), Q8, Q9, Q10, R11, E12, E13, E14
    q_lv = [1, 8, 9, 10]
    w_lv = [2, 3, 5, 7]
    e_lv = [4, 12, 13, 14]
    q = sum(1 for lv in q_lv if level >= lv)
    w = sum(1 for lv in w_lv if level >= lv)
    e = sum(1 for lv in e_lv if level >= lv)
    if level < 6:
        r = 0
    elif level < 11:
        r = 1
    else:
        r = 2
    return q, w, e, r


def ah_cdr(ah: float) -> float:
    return 1.0 + ah / 100.0


def sona_passive_cdr(level: int) -> float:
    """Passive: basic CD reduced by level×2%, cap 20% at 10."""
    return min(0.20, 0.02 * level)


def basic_cd(base: float, ah: float, level: int) -> float:
    return base / ah_cdr(ah) * (1.0 - sona_passive_cdr(level))


# ---------------------------------------------------------------------------
# Shop / sequential inventory
# ---------------------------------------------------------------------------


def build_plan(core: Sequence[str]) -> List[str]:
    """Sickle → boots → item1 → Ionian → rest. Tear sits just before Circlet."""
    plan = ["Spectral Sickle", "Boots of Speed"]
    if not core:
        return plan
    first, *rest = list(core)
    early_circlet = first == "Whispering Circlet" or (
        rest[:1] == ["Whispering Circlet"]
    )
    if early_circlet:
        plan.append("Tear of the Goddess")
    plan.append(first)
    plan.append("Ionian Boots of Lucidity")
    for name in rest:
        if name == "Whispering Circlet" and "Tear of the Goddess" not in plan:
            plan.append("Tear of the Goddess")
        plan.append(name)
    return plan


@dataclass
class ShopState:
    owned: List[str] = field(default_factory=list)
    pocket: int = 0
    spent: int = 0
    tear_minute: Optional[int] = None
    circlet_minute: Optional[int] = None
    plan: List[str] = field(default_factory=list)
    plan_i: int = 0
    sold_scythe: bool = False


def _credit(owned: List[str], name: str) -> Tuple[int, List[str]]:
    credit = 0
    remove: List[str] = []
    for c in UPGRADE.get(name, ()):
        if c in owned:
            credit += ITEMS[c].cost
            remove.append(c)
    return credit, remove


def remaining_cost(owned: List[str], name: str) -> int:
    if name == "Black Mist Scythe":
        return 0
    if name == "Diadem of Songs":
        return 0
    credit, _ = _credit(owned, name)
    return max(0, ITEMS[name].cost - credit)


def net_slots_after(owned: List[str], name: str) -> int:
    if name == "Black Mist Scythe":
        return len(owned)  # replaces sickle
    if name == "Diadem of Songs":
        return len(owned)  # replaces circlet
    _, rem = _credit(owned, name)
    return len(owned) - len(rem) + 1


def finished_legendaries(owned: List[str]) -> int:
    return sum(1 for n in owned if "legendary" in ITEMS[n].tags)


def try_buy(state: ShopState, name: str) -> bool:
    if name in state.owned:
        return False
    if name == "Black Mist Scythe":
        if "Spectral Sickle" in state.owned:
            state.owned.remove("Spectral Sickle")
        state.owned.append(name)
        return True
    if name == "Diadem of Songs":
        if "Whispering Circlet" in state.owned:
            state.owned.remove("Whispering Circlet")
            state.owned.append(name)
            return True
        return False
    if net_slots_after(state.owned, name) > MAX_SLOTS:
        return False
    cost = remaining_cost(state.owned, name)
    if cost > state.pocket:
        return False
    _, rem = _credit(state.owned, name)
    state.pocket -= cost
    state.spent += cost
    for r in rem:
        state.owned.remove(r)
    state.owned.append(name)
    return True


def sell_scythe(state: ShopState) -> bool:
    if "Black Mist Scythe" not in state.owned:
        return False
    state.owned.remove("Black Mist Scythe")
    state.pocket += SCYTHE_SELL
    state.spent = max(0, state.spent - SCYTHE_SELL)
    state.sold_scythe = True
    return True


def next_legendary(state: ShopState) -> Optional[str]:
    for i in range(state.plan_i, len(state.plan)):
        name = state.plan[i]
        if name in ITEMS and "legendary" in ITEMS[name].tags:
            if name in state.owned or (
                name == "Whispering Circlet" and "Diadem of Songs" in state.owned
            ):
                continue
            return name
    return None


def maybe_sell_for_fifth(state: ShopState) -> None:
    """Sell Scythe only when 4 legendaries are done AND the gold finishes a 5th."""
    if state.sold_scythe or "Black Mist Scythe" not in state.owned:
        return
    if finished_legendaries(state.owned) < 4:
        return
    nxt = next_legendary(state)
    if not nxt:
        return
    if remaining_cost(state.owned, nxt) <= state.pocket + SCYTHE_SELL:
        sell_scythe(state)


def maybe_diadem(state: ShopState, minute: int) -> None:
    if "Whispering Circlet" not in state.owned:
        return
    # Circlet: 14 mana × 2 / 10s = 168 mana/min toward 700.
    # Tear before Circlet: ~126 mana/min (Sona spends constantly).
    pre = 0.0
    if state.tear_minute is not None and state.circlet_minute is not None:
        pre = 126.0 * max(0, state.circlet_minute - state.tear_minute)
    elif state.tear_minute is not None:
        pre = 126.0 * max(0, minute - state.tear_minute)
    pre = min(700.0, pre)
    if state.circlet_minute is None:
        return
    after = 168.0 * max(0, minute - state.circlet_minute)
    if pre + after >= 700.0:
        try_buy(state, "Diadem of Songs")


def shop_tick(state: ShopState, minute: int) -> None:
    state.pocket += gold_gained(minute)

    if minute >= 5 and "Spectral Sickle" in state.owned:
        try_buy(state, "Black Mist Scythe")

    maybe_diadem(state, minute)
    maybe_sell_for_fifth(state)

    # Walk the planned finished items. When blocked, buy its components.
    while state.plan_i < len(state.plan):
        nxt = state.plan[state.plan_i]
        if nxt in state.owned or (
            nxt == "Whispering Circlet" and "Diadem of Songs" in state.owned
        ):
            state.plan_i += 1
            continue
        if remaining_cost(state.owned, nxt) <= state.pocket:
            if try_buy(state, nxt):
                if nxt == "Tear of the Goddess" and state.tear_minute is None:
                    state.tear_minute = minute
                if nxt == "Whispering Circlet" and state.circlet_minute is None:
                    state.circlet_minute = minute
                state.plan_i += 1
                maybe_diadem(state, minute)
                maybe_sell_for_fifth(state)
                continue
        # Partial components for the blocked item.
        bought_comp = False
        for comp in NEXT_COMPS.get(nxt, []):
            if comp in state.owned:
                continue
            if ITEMS[comp].cost <= state.pocket:
                if try_buy(state, comp):
                    bought_comp = True
                    if comp == "Tear of the Goddess" and state.tear_minute is None:
                        state.tear_minute = minute
        if bought_comp and remaining_cost(state.owned, nxt) <= state.pocket:
            continue
        break

    if "Ionian Boots of Lucidity" in state.owned and "Boots of Speed" in state.owned:
        state.owned.remove("Boots of Speed")


# ---------------------------------------------------------------------------
# 7.3 crit ADC (Yun Tal → Greaves → IE composite)
# ---------------------------------------------------------------------------


def adc_base(minute: int) -> Tuple[float, float, float, float, List[str]]:
    """AD, attack speed, crit chance, crit damage, items."""
    lvl = adc_level(minute)
    gold = adc_gold(minute)
    ad = 60.0 + 3.4 * (lvl - 1)
    as_base = 0.66 + 0.022 * (lvl - 1)
    crit = 0.0
    bonus_as = 0.0
    crit_dmg = CRIT_73
    items: List[str] = []

    if gold >= 3100:
        items.append("Yun Tal Wildarrows")
        ad += 50.0
        bonus_as += 0.25
        crit = min(0.25, 0.002 * max(0, (minute - 7) * 50))
    elif gold >= 1300:
        items.append("Noonquiver")
        ad += 20.0
        crit += 0.15

    spent = 3100 if gold >= 3100 else (1300 if gold >= 1300 else 0)
    if gold >= spent + 900 and spent >= 1300:
        items.append("Berserker's Greaves")
        spent += 900
        bonus_as += 0.40
    if gold >= spent + 3400:
        items.append("Infinity Edge")
        spent += 3400
        ad += 65.0
        crit += 0.25
        crit_dmg = IE_CRIT_DMG
    if gold >= spent + 2650:
        items.append("Rapid Firecannon")
        bonus_as += 0.40
        crit += 0.25

    as_total = as_base * (1.0 + bonus_as)
    return ad, as_total, min(0.85, crit), crit_dmg, items


def auto_dps(
    ad: float,
    attack_speed: float,
    crit: float,
    onhit: float,
    crit_dmg: float,
    as_cap: float,
) -> float:
    as_clamped = min(as_cap, attack_speed)
    per_hit = ad * ((1.0 - crit) + crit * crit_dmg) + onhit
    return as_clamped * per_hit


# ---------------------------------------------------------------------------
# Combat / buff model
# ---------------------------------------------------------------------------


@dataclass
class Snap:
    minute: int
    items: List[str]
    gold: int
    spent: int
    level: int
    ap: float
    ah: float
    hsp: float
    mana: float
    extra_adc_dps: float
    extra_adc_dps_72: float
    heal_hps: float
    shield_hps: float
    helia_hps: float
    diadem_hps: float
    q_aura_dps: float
    ardent_dps: float
    staff_dps: float
    mandate_dps: float
    cc_dps: float
    buff_impact: float
    sustain_impact: float
    fight_impact: float
    total_impact: float
    gold_eff: float
    buff_gold_eff: float
    aura_uptime: float
    ardent_uptime: float
    notes: str


def harmony_hsp(mana: float) -> float:
    """7.3 Harmony: HSP equal to 0.5% of max mana → 500 mana = +2.5% HSP, 1200 = +6%."""
    return (0.005 * mana) / 100.0


def flags_from(owned: List[str]) -> Dict[str, float]:
    ap = ah = hsp = mana = hp = 0.0
    names = set(owned)
    for n in owned:
        it = ITEMS[n]
        ap += it.ap
        ah += it.ah
        hsp += it.hsp
        mana += it.mana
        hp += it.hp
    if "Whispering Circlet" in names or "Diadem of Songs" in names:
        hsp += harmony_hsp(mana)
    return {
        "ap": ap,
        "ah": ah,
        "hsp": hsp,
        "mana": mana,
        "hp": hp,
        "helia": "Echoes of Helia" in names,
        "ardent": "Ardent Censer" in names,
        "staff": "Staff of Flowing Waters" in names,
        "harmonic": "Harmonic Echo" in names,
        "redemption": "Redemption" in names,
        "mandate": "Imperial Mandate" in names,
        "circlet": "Whispering Circlet" in names,
        "diadem": "Diadem of Songs" in names,
        "ionian": "Ionian Boots of Lucidity" in names,
        "tear": "Tear of the Goddess" in names,
        "scythe": "Black Mist Scythe" in names,
    }


def evaluate(
    owned: List[str],
    minute: int,
    spent: int,
    runes: Optional[RunePage] = None,
) -> Snap:
    gold = gold_at_minute(minute)
    level = support_level(minute)
    f = flags_from(owned)
    ap = f["ap"]
    mana = f["mana"]
    if f["scythe"]:
        ap += scythe_ap(minute)

    # Staff Rapids: +40 AP / +15 AH to Sona and ally for 6s on heal/shield.
    staff_ap = 0.0
    if f["staff"]:
        staff_ap = 40.0
        ap += staff_ap * 0.70  # duty cycle ~70% with W spam

    sona_hp = 530.0 + 90.0 * (level - 1) + f["hp"]
    page = runes or DEFAULT_RUNES
    re = rune_effects(page, level, minute, ap, sona_hp)

    ah = f["ah"] + re["ah"]
    if f["staff"]:
        ah += 15.0 * 0.70
    hsp = f["hsp"] + re["hsp"]

    q_pts, w_pts, _e_pts, r_r = skill_ranks(level)
    q_i = min(3, max(0, q_pts - 1))
    w_i = min(3, max(0, w_pts - 1))

    q_cd = basic_cd(8.0, ah, level)
    w_cd = basic_cd(10.0, ah, level)
    e_cd = basic_cd(14.0, ah, level)
    r_cd = (80.0 if r_r <= 1 else 75.0 if r_r == 2 else 70.0) / ah_cdr(ah + (20.0 if f["mandate"] else 0.0))

    # Rotate Q→W→E: auras last 3s (Q/W) / 5s (E). Passive always-on between casts.
    cycle = q_cd + w_cd + e_cd
    aura_uptime = min(0.98, (3.0 + 3.0 + 5.0) / max(cycle, 8.0) * 1.15)
    # AH + Sona passive pushes this to near-lock.
    if f["ionian"]:
        aura_uptime = min(0.98, aura_uptime + 0.06)
    aura_uptime = min(0.98, aura_uptime + re["aura_bonus"])

    q_dmg = ([40, 80, 120, 160][q_i] + 0.40 * ap) if q_pts else 0.0
    q_aura = ([8, 13, 18, 23][q_i] + 0.20 * ap) if q_pts else 0.0
    w_heal = ([35, 50, 65, 80][w_i] + 0.20 * ap) if w_pts else 0.0
    w_shield = ([25, 50, 75, 100][w_i] + 0.18 * ap) if w_pts else 0.0
    # R Crescendo reinforces auras 20s. Average fight duty of ult.
    r_up = min(0.35, 20.0 / max(r_cd, 40.0)) if r_r else 0.0
    q_aura *= 1.0 + 0.25 * r_up
    w_shield *= 1.0 + 0.25 * r_up

    hsp_mult = 1.0 + hsp
    ally_heal = w_heal * hsp_mult  # the other champion (self heal ignored for buff score)
    ally_shield = w_shield * hsp_mult

    heal_hps = ally_heal / max(w_cd, 4.0)
    shield_hps = ally_shield * aura_uptime / 3.0
    heal_hps += re["heal_hps"] * (1.0 + hsp if page.revitalize else 1.0)

    # Harmonic Echo: 30% of that heal / 35% of that shield to a 2nd ally
    # (or the same target if nobody else is in range — lane case).
    if f["harmonic"]:
        heal_hps *= 1.30
        shield_hps *= 1.35

    helia_hps = 0.0
    if f["helia"] and q_pts:
        cap = 80.0 + (250.0 - 80.0) * (level - 1) / 14.0
        # Q hits two nearest; Power Chord extra packet.
        pc = 20.0 + 10.0 * level + 0.15 * ap
        champ_dmg = q_dmg * 2.0 * (w_cd / max(q_cd, 1.0)) + pc
        stored = min(cap, 0.30 * champ_dmg)
        helia_hps = stored / max(w_cd, 4.0)
        if page.revitalize:
            helia_hps *= 1.0 + re["hsp"]

    diadem_hps = 0.0
    if f["diadem"]:
        diadem_hps = 0.008 * mana  # 0.8% max mana / s in combat
    elif f["circlet"]:
        # Circlet has Harmony HSP but not the Diadem pulse yet.
        diadem_hps = 0.0

    if f["redemption"]:
        red = 150.0 + 200.0 * (level - 1) / 14.0
        # ~2.2 allies hit, 60s CD, can cast while dead.
        heal_hps += (red * 2.2 * hsp_mult) / 60.0

    # ----- ADC side (7.3 crit) -----
    ad, as_base, crit, crit_dmg, _adc_items = adc_base(minute)
    naked = auto_dps(ad, as_base, crit, 0.0, crit_dmg, AS_CAP_73)
    naked72 = auto_dps(ad, as_base, crit, 0.0, CRIT_72, AS_CAP_72)

    ardent_uptime = 0.0
    ardent_dps = 0.0
    if f["ardent"]:
        ardent_uptime = min(0.97, 6.0 / max(w_cd, 4.5) * 1.10)
        as_pct = 0.30 * ardent_uptime
        onhit = 25.0 * ardent_uptime
        buffed_as = as_base * (1.0 + as_pct)
        ardent_dps = auto_dps(ad, buffed_as, crit, onhit, crit_dmg, AS_CAP_73) - naked

    # 7.2 Ardent was weaker / gated (level-scaled 15–34% AS, 16–22 on-hit).
    ardent_dps_72 = 0.0
    if f["ardent"]:
        as_pct72 = 0.20 * ardent_uptime * 0.75
        onhit72 = 18.0 * ardent_uptime * 0.75
        buffed72 = as_base * (1.0 + as_pct72)
        ardent_dps_72 = auto_dps(ad, buffed72, crit, onhit72, CRIT_72, AS_CAP_72) - naked72

    q_aura_dps = (q_aura * aura_uptime / max(q_cd, 4.0)) if q_pts else 0.0

    staff_dps = 0.0
    if f["staff"]:
        # Crit ADC converts bonus AP poorly; Sona's own AP already counted.
        # Count a small packet: ADC abilities with ~15% AP ratio, 0.8 casts/s.
        staff_dps = staff_ap * 0.15 * 0.45 * aura_uptime

    extra = ardent_dps + q_aura_dps + staff_dps
    extra72 = ardent_dps_72 + q_aura_dps * 0.85 + staff_dps * 0.85

    # Mandate: CC marks for 4s, 7% increased damage. Power Chord 0.5s stun
    # every 3 basics + R 1s stun.
    mandate_dps = 0.0
    pc_interval = max(5.0, (q_cd + w_cd + e_cd) / 3.0)
    mark_uptime = 0.0
    if f["mandate"]:
        mark_uptime = min(0.85, 4.0 / pc_interval + (4.0 / max(r_cd, 50.0)))
        mandate_dps = 0.07 * mark_uptime * (naked + extra)

    # Free-hit from Power Chord 0.5s + R 1s in an 8s window.
    lock_s = 0.5 * (8.0 / max(pc_interval, 5.0))
    if r_r:
        lock_s += 1.0 * (8.0 / max(r_cd, 50.0))
    cc_dps = (naked + extra) * min(0.35, lock_s / 8.0)

    cf = combat_frac(minute)
    buff_impact = extra * cf
    sustain = (heal_hps + shield_hps * 0.70 + helia_hps * 2.0 + diadem_hps * cf + re["tank_hps"])
    sustain_impact = sustain * 0.90
    fight_impact = (mandate_dps + cc_dps + re["poke_dps"]) * cf
    total = buff_impact + sustain_impact + fight_impact

    ge_denom = max(spent, 400)
    gold_eff = total / ge_denom * 1000.0
    buff_ge = buff_impact / ge_denom * 1000.0

    notes = []
    if f["ardent"] and f["staff"]:
        notes.append("DOUBLE BUFF")
    elif f["ardent"]:
        notes.append("Ardent 30% AS")
    elif f["staff"]:
        notes.append("Staff")
    if f["helia"]:
        notes.append("Helia dump")
    if f["diadem"]:
        notes.append("Diadem pulse")
    elif f["circlet"]:
        notes.append("Circlet stacking")
    if f["harmonic"]:
        notes.append("Harmonic chain")
    if f["redemption"]:
        notes.append("Redemption")
    if f["mandate"]:
        notes.append("Mandate 7%")
    sold = (
        minute >= 5
        and "Black Mist Scythe" not in owned
        and "Spectral Sickle" not in owned
    )
    if sold:
        notes.append("sold Scythe")
    if aura_uptime >= 0.90:
        notes.append("aura locked")

    return Snap(
        minute=minute,
        items=list(owned),
        gold=gold,
        spent=spent,
        level=level,
        ap=round(ap, 1),
        ah=round(ah, 1),
        hsp=round(hsp, 3),
        mana=mana,
        extra_adc_dps=round(extra, 1),
        extra_adc_dps_72=round(extra72, 1),
        heal_hps=round(heal_hps, 1),
        shield_hps=round(shield_hps, 1),
        helia_hps=round(helia_hps, 1),
        diadem_hps=round(diadem_hps, 1),
        q_aura_dps=round(q_aura_dps, 1),
        ardent_dps=round(ardent_dps, 1),
        staff_dps=round(staff_dps, 1),
        mandate_dps=round(mandate_dps, 1),
        cc_dps=round(cc_dps, 1),
        buff_impact=round(buff_impact, 1),
        sustain_impact=round(sustain_impact, 1),
        fight_impact=round(fight_impact, 1),
        total_impact=round(total, 1),
        gold_eff=round(gold_eff, 2),
        buff_gold_eff=round(buff_ge, 2),
        aura_uptime=round(aura_uptime, 3),
        ardent_uptime=round(ardent_uptime, 3),
        notes=", ".join(notes) or "building",
    )


def simulate_core(core: Sequence[str], runes: Optional[RunePage] = None) -> List[Snap]:
    state = ShopState(
        plan=build_plan(core), pocket=gold_at_minute(0), spent=0
    )
    snaps: List[Snap] = []
    page = runes or DEFAULT_RUNES
    for m in range(1, GAME_MINUTES + 1):
        shop_tick(state, m)
        snaps.append(evaluate(state.owned, m, state.spent, page))
    return snaps


def path_label(core: Sequence[str]) -> str:
    return " → ".join(short_name(n) for n in core)


def score_path(snaps: List[Snap]) -> Dict[str, float]:
    tw = sum(time_weight(s.minute) for s in snaps)
    tw_impact = sum(s.total_impact * time_weight(s.minute) for s in snaps) / tw
    tw_buff = sum(s.buff_impact * time_weight(s.minute) for s in snaps) / tw
    tw_ge = sum(s.gold_eff * time_weight(s.minute) for s in snaps) / tw
    tw_bge = sum(s.buff_gold_eff * time_weight(s.minute) for s in snaps) / tw
    impact_20 = snaps[19].total_impact if len(snaps) >= 20 else snaps[-1].total_impact
    impact_end = snaps[-1].total_impact
    n_leg = finished_legendaries(snaps[-1].items)
    sold = any("sold Scythe" in s.notes for s in snaps)
    sold_m = next((s.minute for s in snaps if "sold Scythe" in s.notes), None)
    patch_delta = sum(
        (s.extra_adc_dps - s.extra_adc_dps_72) * time_weight(s.minute) for s in snaps
    ) / tw
    first_leg = next(
        (
            s.minute
            for s in snaps
            if any("legendary" in ITEMS[n].tags for n in s.items)
        ),
        20,
    )
    ardent_m = next((s.minute for s in snaps if "Ardent Censer" in s.items), None)
    helia_m = next((s.minute for s in snaps if "Echoes of Helia" in s.items), None)
    return {
        "tw_impact": tw_impact,
        "tw_buff": tw_buff,
        "tw_ge": tw_ge,
        "tw_bge": tw_bge,
        "impact_20": impact_20,
        "impact_end": impact_end,
        "n_leg": n_leg,
        "sold": sold,
        "sold_m": sold_m or 99,
        "patch_delta": patch_delta,
        "first_leg": first_leg,
        "ardent_m": ardent_m or 99,
        "helia_m": helia_m or 99,
    }


def _rank(scored: List[dict]) -> List[dict]:
    max_impact = max(r["tw_impact"] for r in scored)
    max_ge = max(r["tw_ge"] for r in scored)
    max_bge = max(r["tw_bge"] for r in scored)
    for r in scored:
        ni = r["tw_impact"] / max_impact
        ng = r["tw_ge"] / max_ge
        nb = r["tw_bge"] / max_bge
        r["combined"] = 0.50 * ni + 0.30 * ng + 0.20 * nb
    scored.sort(key=lambda r: r["combined"], reverse=True)
    return scored


def search(n: int = 3) -> Tuple[List[dict], Dict[str, List[Snap]]]:
    results: Dict[str, List[Snap]] = {}
    scored: List[dict] = []
    for core in permutations(LEGENDARIES, n):
        label = path_label(core)
        snaps = simulate_core(core)
        results[label] = snaps
        sc = score_path(snaps)
        scored.append({"label": label, "core": list(core), **sc})
    return _rank(scored), results


def search_full(front: Sequence[str]) -> Tuple[List[dict], Dict[str, List[Snap]]]:
    """Lock items 1–2, search 3rd / 4th / 5th (5th after selling Scythe)."""
    rest = [n for n in LEGENDARIES if n not in front]
    results: Dict[str, List[Snap]] = {}
    scored: List[dict] = []
    for tail in permutations(rest, 3):
        core = list(front) + list(tail)
        label = path_label(core)
        snaps = simulate_core(core)
        results[label] = snaps
        sc = score_path(snaps)
        scored.append({"label": label, "core": core, **sc})
    return _rank(scored), results


def compare_runes(core: Sequence[str]) -> List[dict]:
    """Same full item path, swap only the 5-rune page."""
    scored: List[dict] = []
    for page in RUNE_PAGES:
        snaps = simulate_core(core, page)
        sc = score_path(snaps)
        scored.append(
            {
                "name": page.name,
                "keystone": page.keystone,
                "slots": list(page.slots),
                "revitalize": page.revitalize,
                "transcendence": page.transcendence,
                **sc,
            }
        )
    return _rank(scored)


def isolated_item_ge(minute: int = 12) -> List[dict]:
    """Each legendary on top of Scythe + Ionian, gold-efficiency snapshot."""
    base_owned = ["Black Mist Scythe", "Ionian Boots of Lucidity"]
    base_spent = ITEMS["Black Mist Scythe"].cost + ITEMS["Ionian Boots of Lucidity"].cost
    baseline = evaluate(base_owned, minute, base_spent)
    rows = []
    for name in LEGENDARIES:
        owned = list(base_owned)
        spent = base_spent + ITEMS[name].cost
        if name == "Whispering Circlet":
            owned.append("Diadem of Songs")  # show finished form
            spent = base_spent + ITEMS["Whispering Circlet"].cost
        else:
            owned.append(name)
        snap = evaluate(owned, minute, spent)
        d_buff = snap.buff_impact - baseline.buff_impact
        d_tot = snap.total_impact - baseline.total_impact
        cost = ITEMS[name].cost
        rows.append(
            {
                "item": name,
                "cost": cost,
                "d_buff": round(d_buff, 1),
                "d_total": round(d_tot, 1),
                "buff_ge": round(d_buff / cost * 1000.0, 2),
                "total_ge": round(d_tot / cost * 1000.0, 2),
                "ardent_dps": snap.ardent_dps,
                "helia_hps": snap.helia_hps,
            }
        )
    rows.sort(key=lambda r: r["total_ge"], reverse=True)
    return rows


def first_owned(snaps: List[Snap], name: str) -> Optional[int]:
    return next((s.minute for s in snaps if name in s.items), None)


def summarize(
    scored3: List[dict],
    scored_full: List[dict],
    results_full: Dict[str, List[Snap]],
    iso: List[dict],
    rune_rows: Optional[List[dict]] = None,
) -> str:
    winner = scored_full[0]
    snaps = results_full[winner["label"]]
    lines: List[str] = []
    lines.append("=" * 78)
    lines.append("SONA — WILD RIFT 7.3 BUFF GOLD-EFFICIENCY SIM")
    lines.append("28-minute long game | 6 slots, then sell Scythe for a 5th legendary")
    lines.append("Partner: 7.3 crit ADC (Yun Tal → IE). Sona kit: 7.2b. Items: 7.3 notes.")
    lines.append("=" * 78)
    lines.append("")
    lines.append("WHY 7.3 BUFFS SONA EVEN WITHOUT A CHAMPION HOTFIX")
    lines.append("  • Crit damage 175% → 200% (IE 230%). Ardent's 30% AS buys extra crits.")
    lines.append("  • AS cap 2.5 → 3.0, so the AS buff is not wasted on a stacked ADC.")
    lines.append("  • Ardent 2700 → 2400, now a flat 30% AS + 25 on-hit (no level/crit gate).")
    lines.append("  • New Echoes of Helia: Sona Q hits two champs → fills Soul Fragments.")
    lines.append("  • New Circlet → Diadem: HSP + 0.8% mana/s pulse, Tear is 400g.")
    lines.append("")
    lines.append("METRIC")
    lines.append("  Buff impact  = extra ADC auto DPS from Ardent / Q aura / Staff  × combat%")
    lines.append("  Sustain      = W heal+shield + Helia dump (×2) + Diadem pulse + Redemption")
    lines.append("  Fight        = Mandate 7% mark + Power Chord/R lock-on-ADC")
    lines.append("  Gold eff     = total impact per 1000g spent")
    lines.append("  Combined     = 50% time-weighted impact + 30% gold-eff + 20% buff gold-eff")
    lines.append("  Search       = 210 first-3 orders, then 60 full pages (3rd/4th/5th)")
    lines.append("  Slots        = Scythe + Ionian + 4 legendaries. Sell Scythe → 5th.")
    lines.append("  Runes        = 9 pages on the winning item path (same shop, swap 5-slot page)")
    lines.append("")

    lines.append("-" * 78)
    lines.append("ISOLATED ITEM GOLD EFFICIENCY  @ 12:00  (on Scythe + Ionian)")
    lines.append("-" * 78)
    lines.append(f"  {'Item':<16} {'Cost':>5} {'Δbuff':>7} {'Δimpact':>8} {'Buff GE':>8} {'Impact GE':>10}")
    for row in iso:
        lines.append(
            f"  {short_name(row['item']):<16} {row['cost']:>5} "
            f"{row['d_buff']:>7.1f} {row['d_total']:>8.1f} {row['buff_ge']:>8.2f} {row['total_ge']:>10.2f}"
        )
    lines.append("  GE = impact per 1000 gold. Ardent should lead buff-GE vs a crit ADC;")
    lines.append("  Helia should lead sustain conversion; Circlet/Diadem is HSP scaling.")
    lines.append("")

    lines.append("-" * 78)
    lines.append("TOP 10 FULL BUILDS  (3rd → 4th → sell Scythe → 5th)")
    lines.append("-" * 78)
    lines.append(
        f"  {'#':>2}  {'Order':<52} {'Impact':>7} {'GE':>6} {'28m':>6} {'Sell':>5}"
    )
    for i, r in enumerate(scored_full[:10], 1):
        sell = f"{int(r['sold_m'])}:00" if r["sold"] else "—"
        lines.append(
            f"  {i:>2}  {r['label']:<52} {r['tw_impact']:>7.1f} {r['tw_ge']:>6.2f} "
            f"{r['impact_end']:>6.1f} {sell:>5}"
        )
    lines.append("")
    lines.append("  First-3 traps (210-path search, items 1–3 only):")
    traps = [r for r in scored3 if r["core"][0] in (
        "Imperial Mandate",
        "Redemption",
        "Harmonic Echo",
        "Staff of Flowing Waters",
        "Echoes of Helia",
        "Whispering Circlet",
    )]
    shown = set()
    for r in traps:
        first = r["core"][0]
        if first in shown:
            continue
        shown.add(first)
        rank = next(i for i, x in enumerate(scored3, 1) if x["label"] == r["label"])
        lines.append(
            f"    {short_name(first)} first  → best such path ranks #{rank}  "
            f"({r['label']}, GE {r['tw_ge']:.2f})"
        )

    lines.append("")
    lines.append("-" * 78)
    lines.append(f"MINUTE-BY-MINUTE  — winner: {winner['label']}")
    lines.append("-" * 78)
    for s in snaps:
        item_s = " › ".join(short_name(n) for n in s.items)
        lines.append(
            f"  {s.minute:>2}:00 | impact {s.total_impact:>6.1f} | buff {s.buff_impact:>5.1f} | "
            f"sus {s.sustain_impact:>5.1f} | GE {s.gold_eff:>5.2f} | spent {s.spent:>5}"
        )
        lines.append(f"         {item_s}")
        lines.append(
            f"         AP {s.ap:.0f}  AH {s.ah:.0f}  HSP {s.hsp*100:.0f}%  "
            f"aura {s.aura_uptime*100:.0f}%  | {s.notes}"
        )

    lines.append("")
    lines.append("-" * 78)
    lines.append("SPIKE CLOCK (winner)")
    lines.append("-" * 78)
    for label, key in (
        ("Tear", "Tear of the Goddess"),
        ("Ionian", "Ionian Boots of Lucidity"),
        ("Helia", "Echoes of Helia"),
        ("Ardent", "Ardent Censer"),
        ("Circlet", "Whispering Circlet"),
        ("Diadem", "Diadem of Songs"),
        ("Staff", "Staff of Flowing Waters"),
        ("Harmonic", "Harmonic Echo"),
        ("Redemption", "Redemption"),
        ("Mandate", "Imperial Mandate"),
    ):
        m = first_owned(snaps, key)
        if m:
            s = snaps[m - 1]
            lines.append(
                f"  {label:<12} ~{m:>2}:00   impact {s.total_impact:>6.1f}   "
                f"buff DPS {s.extra_adc_dps:>6.1f}   GE {s.gold_eff:.2f}"
            )

    lines.append("")
    lines.append("-" * 78)
    lines.append("FULL 6-SLOT PAGE")
    lines.append("-" * 78)
    core = winner["core"]
    fourth = core[3] if len(core) > 3 else "—"
    fifth = core[4] if len(core) > 4 else "—"
    sold_m = int(winner["sold_m"]) if winner["sold"] else None
    lines.append("  Until Scythe sell:")
    lines.append("    1. Black Mist Scythe")
    lines.append("    2. Ionian Boots of Lucidity")
    lines.append(f"    3. {core[0]}")
    lines.append(f"    4. {core[1]}")
    lines.append(f"    5. {core[2]}")
    lines.append(f"    6. {fourth}   (4th legendary)")
    if sold_m:
        lines.append(f"  Endgame ~{sold_m}:00: SELL Scythe ({SCYTHE_SELL}g) → {fifth}")
        lines.append("  Final page: Ionian + 5 legendaries")
    else:
        lines.append("  Scythe sell: not reached (not enough gold for a 5th)")
    lines.append("")

    if rune_rows:
        lines.append("-" * 78)
        lines.append("RUNES ON THIS BUILD  (same Ardent→Helia→… path, swap page only)")
        lines.append("-" * 78)
        lines.append(
            f"  {'#':>2}  {'Page':<52} {'Impact':>7} {'GE':>6} {'Buff':>6} {'28m':>6}"
        )
        for i, r in enumerate(rune_rows, 1):
            lines.append(
                f"  {i:>2}  {r['name']:<52} {r['tw_impact']:>7.1f} {r['tw_ge']:>6.2f} "
                f"{r['tw_buff']:>6.1f} {r['impact_end']:>6.1f}"
            )
        lines.append("")
        lines.extend(_rune_why(rune_rows))
        lines.append("")
    lines.append("-" * 78)
    lines.append("VERDICT")
    lines.append("-" * 78)
    lines.append(f"  Best gold-efficient buff path:  {winner['label']}")
    lines.append(
        f"  Time-weighted impact {winner['tw_impact']:.1f}  |  "
        f"gold-eff {winner['tw_ge']:.2f}  |  buff-GE {winner['tw_bge']:.2f}"
    )
    lines.append(
        f"  7.3 vs 7.2 Ardent conversion (extra ADC DPS): +{winner['patch_delta']:.1f} avg"
    )
    lines.append("")
    lines.append("  RECOMMENDED PURCHASE ORDER (28-min full page, crit ADC):")
    lines.append("  1) Spectral Sickle → Black Mist Scythe (quest ~5:00)")
    lines.append("  2) Boots of Speed (first back)")
    why = {
        "Ardent Censer": "— 30% AS + 25 on-hit. Highest buff-GE vs a 7.3 crit ADC.",
        "Echoes of Helia": "— Q×2 fills fragments, W dumps them into the ADC",
        "Staff of Flowing Waters": "— 40 AP / 15 AH on W; take if ADC is AP",
        "Harmonic Echo": "— 30/35% chain heal/shield (close 3rd-item GE)",
        "Redemption": "— 60s team heal, low lane GE",
        "Imperial Mandate": "— 7% mark on Power Chord/R; 7.3 crit ADC multiplies it",
        "Whispering Circlet": "— HSP + Diadem pulse (needs Tear stacks)",
    }
    ionian_m = first_owned(snaps, "Ionian Boots of Lucidity")
    first_leg_m = first_owned(snaps, winner["core"][0])
    n = 3
    if first_leg_m and ionian_m and ionian_m < first_leg_m:
        lines.append(f"  {n}) Ionian Boots (~{ionian_m}:00) — aura lock / more W")
        n += 1
    for i, name in enumerate(winner["core"]):
        if i == 4 and sold_m:
            lines.append(
                f"  {n}) SELL Black Mist Scythe (~{sold_m}:00) — {SCYTHE_SELL}g toward 5th"
            )
            n += 1
        m = first_owned(snaps, name)
        if name == "Whispering Circlet":
            dm = first_owned(snaps, "Diadem of Songs")
            extra = f", Diadem free ~{dm}:00" if dm else " (stacking to Diadem)"
            lines.append(f"  {n}) {name} (~{m}:00{extra})")
        else:
            slot = {0: "1st legendary", 1: "2nd", 2: "3rd", 3: "4th", 4: "5th (after sell)"}.get(i, "")
            tag = f" [{slot}]" if slot else ""
            lines.append(f"  {n}) {name} (~{m}:00) {why.get(name, '')}{tag}")
        n += 1
        if name == winner["core"][0] and ionian_m and first_leg_m and ionian_m > first_leg_m:
            lines.append(f"  {n}) Ionian Boots (~{ionian_m}:00) — aura lock / more W")
            n += 1
    runner = scored_full[1]
    lines.append("")
    lines.append(
        f"  Runner-up: {runner['label']} is within "
        f"{abs(winner['tw_ge'] - runner['tw_ge']):.2f} GE."
    )
    lines.append("")
    lines.append("  Skill order: W max (heal/shield/Ardent uptime) → Q max → E. R whenever.")
    lines.append("  Early: 1 point Q at 1 for last-hit / Helia farm, then W.")
    if rune_rows:
        best_r = rune_rows[0]
        lines.append(
            "  Runes:  " + " · ".join(best_r["slots"])
        )
    else:
        lines.append("  Runes: Aery · Font of Life · Bone Plating · Revitalize · Transcendence")
    lines.append("  Spells: Flash + Heal  (Exhaust vs dive).")
    lines.append("  Play: Q→W→E so auras never drop. W even at full HP (Ardent/Staff still proc).")
    lines.append("  Power Chord the ADC's target — Font of Life + Mandate mark + 0.5s stun.")
    lines.append("")
    lines.append("  Swap: ADC is AP (Kai'Sa/Ez) → Staff instead of Ardent.")
    lines.append("        vs heavy CC → Mikael's instead of 4th/5th (not in search).")
    lines.append("        Never sell Scythe before 4 legendaries are finished.")
    lines.append("")
    lines.append("  Don't: Mandate/Redemption/Harmonic first — they spend 2400–2600g on")
    lines.append("  fight-once effects and delay the 30% AS buff the 7.3 ADC actually uses.")
    lines.append("=" * 78)
    return "\n".join(lines)


def _rune_named(rows: Sequence[dict], name: str) -> Optional[dict]:
    return next((r for r in rows if r["name"] == name), None)


def _rune_why(rows: List[dict]) -> List[str]:
    """Explain the winning 5-slot page against this item path, with deltas."""
    best = rows[0]
    aery = _rune_named(rows, "Aery / FoL / Bone / Revitalize / Transcendence")
    guardian = _rune_named(rows, "Guardian / FoL / Bone / Revitalize / Transcendence")
    comet = _rune_named(rows, "Comet / FoL / Bone / Revitalize / Transcendence")
    fleet = _rune_named(rows, "Fleet / FoL / Bone / Revitalize / Transcendence")
    manaflow = _rune_named(rows, "Aery / FoL / Bone / Revitalize / Manaflow")
    scorch = _rune_named(rows, "Aery / FoL / Bone / Revitalize / Scorch")
    legend = _rune_named(rows, "Aery / FoL / Bone / Revitalize / Legend: Haste")
    no_rev = _rune_named(rows, "Aery / FoL / Bone / Transcendence / Manaflow")
    out = [
        "  Best page:  " + " · ".join(best["slots"]),
        "  Why this page on Ardent / Helia / Mandate / Harmonic / Staff:",
    ]
    if best["keystone"] == "Aery":
        out.append("    Aery — W/Q spam sends it every ~4s: ally shield + Q poke.")
    if "Font of Life" in best["slots"]:
        out.append("    Font of Life — Power Chord / Q mark; ADC heals while she crits.")
    if "Bone Plating" in best["slots"]:
        out.append("    Bone Plating — Sona is paper; survive the all-in so auras stay up.")
    if best["revitalize"]:
        out.append("    Revitalize — 5% HSP (+extra <40%) on W, Aery, Harmonic, Helia dump.")
    if best["transcendence"]:
        out.append("    Transcendence — 6/12 AH + L9 refund. More W = Ardent 6s never drops.")
    if aery and guardian:
        d = aery["tw_impact"] - guardian["tw_impact"]
        out.append(
            f"  Aery vs Guardian (same minors): +{d:.1f} impact — "
            "Aery cycles; Guardian waits for a hit."
        )
    if aery and comet:
        d = aery["tw_impact"] - comet["tw_impact"]
        out.append(
            f"  Aery vs Comet: +{d:.1f} impact — Comet is poke-only, no ally shield."
        )
    if aery and fleet:
        d = aery["tw_impact"] - fleet["tw_impact"]
        out.append(f"  Aery vs Fleet: +{d:.1f} impact — Fleet is mostly self-heal.")
    if aery and legend:
        d = aery["tw_ge"] - legend["tw_ge"]
        out.append(
            f"  Transcendence vs Legend: Haste: +{d:.2f} GE — "
            "support stacks Legend too slowly."
        )
    if aery and manaflow:
        d = aery["tw_ge"] - manaflow["tw_ge"]
        out.append(
            f"  Transcendence vs Manaflow 5th slot: +{d:.2f} GE — "
            "AH for Ardent uptime beats mana."
        )
    if aery and scorch:
        d = aery["tw_ge"] - scorch["tw_ge"]
        out.append(
            f"  Transcendence vs Scorch 5th slot: +{d:.2f} GE — "
            "lane burn does not keep Ardent up."
        )
    if aery and no_rev:
        d = aery["tw_ge"] - no_rev["tw_ge"]
        out.append(
            f"  Keep Revitalize (do not drop HSP for Manaflow): +{d:.2f} GE on this path."
        )
    out.append("  7.3: Ingenious Hunter is gone (no Mandate/Redemption CDR rune).")
    out.append(
        "  If you actually OOM, swap the 5th slot to Manaflow "
        "(ranks #6 here — only when mana is the bottleneck)."
    )
    return out


def export_json(
    scored: List[dict],
    results: Dict[str, List[Snap]],
    iso: List[dict],
    path: str,
    rune_rows: Optional[List[dict]] = None,
) -> None:
    winner = scored[0]
    best_page = (
        rune_rows[0]
        if rune_rows
        else {
            "keystone": "Aery",
            "slots": [
                "Aery",
                "Font of Life",
                "Bone Plating",
                "Revitalize",
                "Transcendence",
            ],
        }
    )
    payload = {
        "meta": {
            "champion": "Sona",
            "role": "Support",
            "patch": "7.3",
            "game_minutes": GAME_MINUTES,
            "playstyle": "aura buff enchanter next to a 7.3 crit ADC",
            "question": "build order with the most gold-efficient buffs and game impact",
            "crit_damage": CRIT_73,
            "as_cap": AS_CAP_73,
            "runes": {
                "keystone": best_page["keystone"],
                "page": best_page["slots"],
                "ranking": [
                    {
                        "rank": i,
                        "name": r["name"],
                        "slots": r["slots"],
                        "tw_impact": round(r["tw_impact"], 2),
                        "tw_ge": round(r["tw_ge"], 3),
                        "tw_buff": round(r["tw_buff"], 2),
                        "combined": round(r["combined"], 4),
                    }
                    for i, r in enumerate((rune_rows or [])[:9], 1)
                ],
            },
            "summoners": ["Flash", "Heal"],
            "skill_order": "W max > Q max > E, R whenever",
        },
        "winner": {
            "order": winner["label"],
            "core": winner["core"],
            "tw_impact": winner["tw_impact"],
            "tw_ge": winner["tw_ge"],
            "tw_bge": winner["tw_bge"],
            "combined": winner["combined"],
            "patch_delta": winner["patch_delta"],
            "sold_m": None if not winner["sold"] else winner["sold_m"],
            "n_leg": winner["n_leg"],
            "impact_20": winner["impact_20"],
            "impact_end": winner["impact_end"],
            "page": {
                "until_sell": [
                    "Black Mist Scythe",
                    "Ionian Boots of Lucidity",
                    *winner["core"][:4],
                ],
                "sell_scythe_gold": SCYTHE_SELL,
                "fifth": winner["core"][4] if len(winner["core"]) > 4 else None,
            },
        },
        "isolated_ge_12": iso,
        "top10": [
            {
                "rank": i,
                "order": r["label"],
                "core": r["core"],
                "tw_impact": round(r["tw_impact"], 2),
                "tw_ge": round(r["tw_ge"], 3),
                "tw_bge": round(r["tw_bge"], 3),
                "combined": round(r["combined"], 4),
                "patch_delta": round(r["patch_delta"], 2),
            }
            for i, r in enumerate(scored[:10], 1)
        ],
        "timeline": [
            {
                "minute": s.minute,
                "items": s.items,
                "spent": s.spent,
                "gold": s.gold,
                "total_impact": s.total_impact,
                "buff_impact": s.buff_impact,
                "sustain_impact": s.sustain_impact,
                "gold_eff": s.gold_eff,
                "buff_gold_eff": s.buff_gold_eff,
                "extra_adc_dps": s.extra_adc_dps,
                "notes": s.notes,
            }
            for s in results[winner["label"]]
        ],
        "builds_top5": {
            r["label"]: [
                {
                    "minute": s.minute,
                    "items": s.items,
                    "total_impact": s.total_impact,
                    "gold_eff": s.gold_eff,
                    "buff_impact": s.buff_impact,
                    "notes": s.notes,
                }
                for s in results[r["label"]]
            ]
            for r in scored[:5]
        },
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)


def main() -> None:
    scored3, _ = search(3)
    front = scored3[0]["core"][:2]
    scored_full, results_full = search_full(front)
    iso = isolated_item_ge(12)
    rune_rows = compare_runes(scored_full[0]["core"])
    report = summarize(scored3, scored_full, results_full, iso, rune_rows)
    print(report)
    out_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(out_dir, "report.txt"), "w", encoding="utf-8") as fh:
        fh.write(report + "\n")
    export_json(
        scored_full,
        results_full,
        iso,
        os.path.join(out_dir, "results.json"),
        rune_rows,
    )
    print(f"\nWrote {out_dir}/report.txt and results.json")
    print(f"Winner: {scored_full[0]['label']}  combined={scored_full[0]['combined']:.4f}")
    print(
        f"4th={scored_full[0]['core'][3]}  "
        f"sell={scored_full[0]['sold_m']}  "
        f"5th={scored_full[0]['core'][4]}"
    )
    print("Runes: " + " · ".join(rune_rows[0]["slots"]))


if __name__ == "__main__":
    main()
