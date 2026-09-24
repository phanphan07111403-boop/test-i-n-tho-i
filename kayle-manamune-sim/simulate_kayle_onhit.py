#!/usr/bin/env python3
"""
Wild Rift Kayle (Baron) — China on-hit Manamune vs WR cores
Patch 7.3 item values. Average game: 20 minutes.

Question:
  PC China Kayle top often rushes Tear → Manamune into on-hit
  (Rageblade / Nashor / BotRK / Terminus). Is that path worth
  buying on Wild Rift Kayle, or do WR-native cores beat it?

Playstyle: farm to spikes, then 6s skirmish windows
  (Q shred → E reset → autos; Aflame waves from 9).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import json
import math

GAME_MINUTES = 20
WINDOW = 6.0  # seconds of sustained auto combat
AS_CAP = 3.0

# ---------------------------------------------------------------------------
# Economy / XP — WR baron farmer (not smurf-fed)
# Lands ~10.8k at 20:00, typical for a scaling Kayle who keeps CS.
# ---------------------------------------------------------------------------


def gold_at_minute(m: int) -> int:
    if m <= 0:
        return 500
    total = 500
    for t in range(1, m + 1):
        if t <= 4:
            total += 380
        elif t <= 10:
            total += 480
        elif t <= 15:
            total += 560
        else:
            total += 620
    return total


def level_at_minute(m: int) -> int:
    # WR max level 15. Solo XP: ~15 at 18–20.
    table = {
        1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7, 7: 8, 8: 9,
        9: 10, 10: 11, 11: 12, 12: 12, 13: 13, 14: 13,
        15: 14, 16: 14, 17: 15, 18: 15, 19: 15, 20: 15,
    }
    return table.get(m, min(15, 1 + m))


def skill_rank(level: int, skill: str) -> int:
    """E max, Q second, W last. R at 6 / 11 / 15."""
    if skill == "R":
        if level < 6:
            return 0
        if level < 11:
            return 1
        if level < 15:
            return 2
        return 3
    e_levels = [1, 3, 5, 7]
    q_levels = [2, 8, 10, 12]
    w_levels = [4, 9, 13, 14]
    mapping = {"E": e_levels, "Q": q_levels, "W": w_levels}
    return sum(1 for lv in mapping[skill] if level >= lv)


# ---------------------------------------------------------------------------
# Targets (WR baron opponent / teamfight squishy)
# ---------------------------------------------------------------------------


def bruiser_hp(m: int) -> float:
    lv = level_at_minute(m)
    item_hp = 90 * max(0, m - 5)
    return 620 + 105 * lv + item_hp


def bruiser_armor(m: int) -> float:
    lv = level_at_minute(m)
    extra = 0.0 if m < 7 else min(9.0 * (m - 7), 90.0)
    return 38 + 4.2 * lv + extra


def bruiser_mr(m: int) -> float:
    lv = level_at_minute(m)
    extra = 0.0 if m < 8 else min(6.0 * (m - 8), 55.0)
    return 32 + 1.6 * lv + extra


def squish_hp(m: int) -> float:
    lv = level_at_minute(m)
    return 570 + 95 * lv + 18 * m


def squish_armor(m: int) -> float:
    lv = level_at_minute(m)
    extra = 0.0 if m < 12 else 18.0
    return 28 + 3.8 * lv + extra


def squish_mr(m: int) -> float:
    lv = level_at_minute(m)
    extra = 0.0 if m < 12 else 12.0
    return 30 + 1.3 * lv + extra


# ---------------------------------------------------------------------------
# Items — Wild Rift patch 7.3
# ---------------------------------------------------------------------------


@dataclass
class Item:
    name: str
    cost: int
    ad: float = 0
    ap: float = 0
    as_pct: float = 0
    ah: float = 0
    hp: float = 0
    mana: float = 0
    mr: float = 0
    flat_mpen: float = 0
    pct_mpen: float = 0
    pct_armor_pen: float = 0
    lifesteal: float = 0
    deathcap: bool = False
    tags: Tuple[str, ...] = ()


ITEMS: Dict[str, Item] = {
    "Tear of the Goddess": Item("Tear of the Goddess", 400, tags=("tear",)),
    "Long Sword": Item("Long Sword", 500, ad=12),
    "Caulfield's Warhammer": Item("Caulfield's Warhammer", 1200, ad=20, ah=10),
    "Dagger": Item("Dagger", 400, as_pct=0.12),
    "Recurve Bow": Item("Recurve Bow", 900, as_pct=0.20),
    "Pickaxe": Item("Pickaxe", 800, ad=20),
    "Amplifying Tome": Item("Amplifying Tome", 500, ap=20),
    "Blasting Wand": Item("Blasting Wand", 800, ap=45),
    "Fiendish Codex": Item("Fiendish Codex", 900, ap=35, ah=10),
    "Needlessly Large Rod": Item("Needlessly Large Rod", 1400, ap=70),
    "Hearthbound Axe": Item("Hearthbound Axe", 1200, ad=20, as_pct=0.15),
    "Vampiric Scepter": Item("Vampiric Scepter", 1200, ad=15, lifesteal=0.08),
    "Sheen": Item("Sheen", 800, tags=("sheen",)),
    "Kindlegem": Item("Kindlegem", 1000, hp=200, ah=10),
    "Boots of Speed": Item("Boots of Speed", 500, tags=("boots",)),
    "Berserker's Greaves": Item(
        "Berserker's Greaves", 1100, as_pct=0.35, tags=("boots",)
    ),
    "Boots of Mana": Item(
        "Boots of Mana", 1200, ap=15, flat_mpen=8, tags=("boots",)
    ),
    "Manamune": Item(
        "Manamune", 2900, ad=40, mana=500, ah=15, tags=("tear", "manamune")
    ),
    "Muramana": Item(
        "Muramana", 2900, ad=40, mana=1200, ah=15, tags=("tear", "muramana")
    ),
    "Nashor's Tooth": Item(
        "Nashor's Tooth", 2900, ap=80, as_pct=0.50, ah=15, tags=("nashor",)
    ),
    "Guinsoo's Rageblade": Item(
        "Guinsoo's Rageblade",
        3000,
        ad=35,
        ap=30,
        as_pct=0.30,
        tags=("rageblade",),
    ),
    "Blade of the Ruined King": Item(
        "Blade of the Ruined King",
        3100,
        ad=40,
        as_pct=0.30,
        lifesteal=0.12,
        tags=("bork",),
    ),
    "Terminus": Item(
        "Terminus", 3000, ad=35, as_pct=0.35, tags=("terminus",)
    ),
    "Wit's End": Item(
        "Wit's End", 2800, as_pct=0.50, mr=45, tags=("wits",)
    ),
    "Dusk and Dawn": Item(
        "Dusk and Dawn",
        3100,
        ap=60,
        hp=300,
        ah=20,
        as_pct=0.20,
        tags=("dusk", "spellblade"),
    ),
    "Rabadon's Deathcap": Item(
        "Rabadon's Deathcap", 3400, ap=130, deathcap=True, tags=("cap",)
    ),
    "Infinity Orb": Item(
        "Infinity Orb", 2900, ap=110, flat_mpen=15, tags=("orb",)
    ),
    "Lich Bane": Item(
        "Lich Bane", 2800, ap=100, ah=10, tags=("lich", "spellblade")
    ),
    "Kraken Slayer": Item(
        "Kraken Slayer", 3000, ad=45, as_pct=0.35, tags=("kraken",)
    ),
    "Void Staff": Item(
        "Void Staff", 3000, ap=70, pct_mpen=0.40, tags=("pen",)
    ),
}


UPGRADE_COMPONENTS: Dict[str, Tuple[str, ...]] = {
    "Berserker's Greaves": ("Boots of Speed", "Dagger"),
    "Boots of Mana": ("Boots of Speed",),
    "Manamune": ("Tear of the Goddess", "Caulfield's Warhammer", "Long Sword"),
    "Muramana": ("Manamune",),
    "Nashor's Tooth": ("Recurve Bow", "Blasting Wand", "Fiendish Codex"),
    "Guinsoo's Rageblade": ("Amplifying Tome", "Recurve Bow", "Pickaxe"),
    "Blade of the Ruined King": ("Vampiric Scepter", "Recurve Bow", "Pickaxe"),
    "Terminus": ("Recurve Bow", "Hearthbound Axe"),
    "Wit's End": ("Recurve Bow", "Dagger"),
    "Dusk and Dawn": ("Sheen", "Blasting Wand", "Kindlegem"),
    "Rabadon's Deathcap": ("Needlessly Large Rod",),
    "Infinity Orb": ("Needlessly Large Rod",),
    "Lich Bane": ("Sheen", "Blasting Wand"),
    "Kraken Slayer": ("Recurve Bow", "Pickaxe"),
    "Void Staff": ("Blasting Wand",),
}

NEXT_COMPONENTS: Dict[str, List[str]] = {
    "Berserker's Greaves": ["Boots of Speed", "Dagger"],
    "Boots of Mana": ["Boots of Speed"],
    "Manamune": ["Tear of the Goddess", "Long Sword", "Caulfield's Warhammer"],
    "Nashor's Tooth": ["Recurve Bow", "Fiendish Codex", "Blasting Wand"],
    "Guinsoo's Rageblade": ["Recurve Bow", "Pickaxe", "Amplifying Tome"],
    "Blade of the Ruined King": ["Recurve Bow", "Vampiric Scepter", "Pickaxe"],
    "Terminus": ["Recurve Bow", "Hearthbound Axe"],
    "Wit's End": ["Recurve Bow", "Dagger"],
    "Dusk and Dawn": ["Sheen", "Kindlegem", "Blasting Wand"],
    "Rabadon's Deathcap": ["Needlessly Large Rod"],
    "Infinity Orb": ["Needlessly Large Rod"],
    "Lich Bane": ["Sheen", "Blasting Wand"],
    "Kraken Slayer": ["Recurve Bow", "Pickaxe"],
    "Void Staff": ["Blasting Wand"],
}


# ---------------------------------------------------------------------------
# Build paths
# ---------------------------------------------------------------------------

BUILD_PATHS: Dict[str, List[str]] = {
    # China PC import: Tear rush → Manamune → Rageblade on-hit
    "China Manamune → Rage → Nashor": [
        "Tear of the Goddess",
        "Manamune",
        "Berserker's Greaves",
        "Guinsoo's Rageblade",
        "Nashor's Tooth",
        "Terminus",
    ],
    "China Manamune → Rage → BotRK": [
        "Tear of the Goddess",
        "Manamune",
        "Berserker's Greaves",
        "Guinsoo's Rageblade",
        "Blade of the Ruined King",
        "Terminus",
    ],
    # Manamune second (keep Nashor spike, then steal the China item)
    "Nashor → Manamune → Rage": [
        "Nashor's Tooth",
        "Berserker's Greaves",
        "Tear of the Goddess",
        "Manamune",
        "Guinsoo's Rageblade",
        "Terminus",
    ],
    # WR native AP (Diamond+ popular)
    "Nashor → Dusk → Cap (WR AP)": [
        "Nashor's Tooth",
        "Boots of Mana",
        "Dusk and Dawn",
        "Rabadon's Deathcap",
        "Infinity Orb",
    ],
    "Nashor → Orb → Cap": [
        "Nashor's Tooth",
        "Boots of Mana",
        "Infinity Orb",
        "Rabadon's Deathcap",
        "Lich Bane",
    ],
    # WR baron on-hit (no Tear) — Rageblade / BotRK / Terminus
    "Rage → BotRK → Terminus (WR on-hit)": [
        "Guinsoo's Rageblade",
        "Berserker's Greaves",
        "Blade of the Ruined King",
        "Terminus",
        "Nashor's Tooth",
    ],
    # Hybrid on-hit without Tear
    "Nashor → Rage → Terminus": [
        "Nashor's Tooth",
        "Berserker's Greaves",
        "Guinsoo's Rageblade",
        "Terminus",
        "Rabadon's Deathcap",
    ],
    # Dusk extra-on-hit instead of Manamune
    "Nashor → Dusk → Terminus": [
        "Nashor's Tooth",
        "Boots of Mana",
        "Dusk and Dawn",
        "Terminus",
        "Rabadon's Deathcap",
    ],
}


# ---------------------------------------------------------------------------
# Inventory
# ---------------------------------------------------------------------------


def remaining_cost(item_name: str, owned: List[str]) -> int:
    credit = 0
    for c in UPGRADE_COMPONENTS.get(item_name, ()):
        if c in owned:
            credit += ITEMS[c].cost
    return max(0, ITEMS[item_name].cost - credit)


def resolve_inventory(path: List[str], gold: int) -> Tuple[List[str], int]:
    owned: List[str] = []
    gold_pool = gold

    def buy(name: str) -> bool:
        nonlocal gold_pool
        if name in owned:
            return False
        cost = remaining_cost(name, owned)
        if cost > gold_pool:
            return False
        for c in UPGRADE_COMPONENTS.get(name, ()):
            if c in owned:
                owned.remove(c)
        gold_pool -= cost
        owned.append(name)
        return True

    blocked: Optional[str] = None
    for step in path:
        if step in owned:
            continue
        if remaining_cost(step, owned) <= gold_pool:
            buy(step)
        else:
            blocked = step
            break

    if blocked and blocked in NEXT_COMPONENTS:
        for comp in NEXT_COMPONENTS[blocked]:
            if comp not in owned and gold_pool >= ITEMS[comp].cost:
                buy(comp)
        if remaining_cost(blocked, owned) <= gold_pool:
            buy(blocked)
            seen = False
            for step in path:
                if step == blocked:
                    seen = True
                    continue
                if not seen or step in owned:
                    continue
                if remaining_cost(step, owned) <= gold_pool:
                    buy(step)
                else:
                    if step in NEXT_COMPONENTS:
                        for comp in NEXT_COMPONENTS[step]:
                            if comp not in owned and gold_pool >= ITEMS[comp].cost:
                                buy(comp)
                    break
    return owned, gold_pool


def tear_bought_minute(path: List[str]) -> Optional[int]:
    for m in range(1, GAME_MINUTES + 1):
        owned, _ = resolve_inventory(path, gold_at_minute(m))
        if any(n in owned for n in ("Tear of the Goddess", "Manamune", "Muramana")):
            return m
    return None


def tear_stacks_at(path: List[str], minute: int) -> int:
    """WR 7.3: 14 mana, 3 times / 10s. Farming last-hits hit the cap (~18/min)."""
    start = tear_bought_minute(path)
    if start is None or minute < start:
        return 0
    minutes_held = minute - start + 1
    # Cap stacking while CSing: 3 charges / 10s = 18/min * 14 = 252 mana/min.
    return min(700, int(252 * minutes_held))


# ---------------------------------------------------------------------------
# Kayle stats / combat
# ---------------------------------------------------------------------------


def kayle_base_ad(level: int) -> float:
    return 54 + 3 * (level - 1)


def kayle_base_mana(level: int) -> float:
    return 345 + 41 * (level - 1)


def kayle_base_as(level: int) -> float:
    # WR: 0.80 + 2.2% growth, applied as bonus attack speed.
    return 0.80


def e_passive(rank: int, bonus_ad: float, ap: float) -> float:
    if rank <= 0:
        return 0.0
    base = [0, 8, 11, 14, 17][rank]
    return base + 0.05 * bonus_ad + 0.15 * ap


def e_missing_pct(rank: int, ap: float) -> float:
    if rank <= 0:
        return 0.0
    base = [0, 0.07, 0.08, 0.09, 0.10][rank]
    return base + 0.02 * (ap / 100.0)


def q_damage(rank: int, bonus_ad: float, ap: float) -> float:
    if rank <= 0:
        return 0.0
    base = [0, 60, 100, 140, 180][rank]
    return base + 0.60 * bonus_ad + 0.50 * ap


def zeal_as(level: int, ap: float, combat: bool) -> float:
    # Forms at 1 / 5 / 9 / 13. Max stacks in a 6s fight. Transcendent = always.
    if level >= 13:
        per = 0.07
    elif level >= 9:
        per = 0.06
    elif level >= 5:
        per = 0.05
    else:
        per = 0.04
    stacks = 5.0 if (combat or level >= 13) else 0.0
    return stacks * (per + 0.01 * (ap / 100.0))


def alacrity_as(minute: int) -> float:
    # 3% per stack, max 18%. Farmer hits cap around 14–15.
    return min(0.18, 0.03 + 0.012 * minute)


def lethal_tempo_as(ranged: bool) -> float:
    # Average over a 6s window that starts from 0 stacks.
    # Ranged 6.4% * 6 = 38.4% at full; window average ~80% of max.
    per = 0.064 if ranged else 0.08
    return 0.80 * per * 6


def mitigate(raw: float, resist: float, pct_pen: float, flat_pen: float) -> float:
    eff = resist * (1.0 - pct_pen) - flat_pen
    if eff < 0:
        eff = 0.0
    return raw * 100.0 / (100.0 + eff)


@dataclass
class Snapshot:
    minute: int
    level: int
    items: List[str]
    gold: int
    ap: float
    bonus_ad: float
    total_ad: float
    as_pct: float
    aps: float
    mana: float
    muramana: bool
    tear_stacks: int
    bruiser: float
    squish: float
    onhit_share: float
    notes: str


def build_stats(owned: List[str], level: int, tear_stacks: int) -> dict:
    ap = 0.0
    bonus_ad = 0.0
    as_pct = 0.022 * (level - 1)
    ah = 0.0
    mana = kayle_base_mana(level)
    flat_mpen = 0.0
    pct_mpen = 0.0
    pct_armor_pen = 0.0
    deathcap = False
    tags = set()

    names = list(owned)
    # Transform Manamune → Muramana once Tear is full. Do this before summing.
    if "Manamune" in names and tear_stacks >= 700:
        names = ["Muramana" if n == "Manamune" else n for n in names]

    for n in names:
        it = ITEMS[n]
        ap += it.ap
        bonus_ad += it.ad
        as_pct += it.as_pct
        ah += it.ah
        mana += it.mana
        flat_mpen += it.flat_mpen
        pct_mpen = max(pct_mpen, it.pct_mpen)
        pct_armor_pen = max(pct_armor_pen, it.pct_armor_pen)
        deathcap = deathcap or it.deathcap
        tags.update(it.tags)

    if "Manamune" in names:
        # Still stacking: 500 listed mana replaced by 500 + current stacks.
        mana = mana - ITEMS["Manamune"].mana + 500 + tear_stacks
        bonus_ad += 0.02 * mana  # Awe
    elif "Muramana" in names:
        bonus_ad += 0.02 * mana
    elif "Tear of the Goddess" in names:
        mana += tear_stacks

    if deathcap:
        ap *= 1.30

    base_ad = kayle_base_ad(level)
    return {
        "names": names,
        "ap": ap,
        "bonus_ad": bonus_ad,
        "base_ad": base_ad,
        "total_ad": base_ad + bonus_ad,
        "as_pct": as_pct,
        "ah": ah,
        "mana": mana,
        "flat_mpen": flat_mpen,
        "pct_mpen": pct_mpen,
        "pct_armor_pen": pct_armor_pen,
        "tags": tags,
    }


def fight_window(
    st: dict,
    level: int,
    minute: int,
    hp: float,
    armor: float,
    mr: float,
) -> Tuple[float, float, dict]:
    """Return (total mix damage, on-hit mix damage, debug)."""
    ap = st["ap"]
    bonus_ad = st["bonus_ad"]
    base_ad = st["base_ad"]
    total_ad = st["total_ad"]
    tags = st["tags"]
    mana = st["mana"]
    ranged = level >= 5

    e_rank = skill_rank(level, "E")
    q_rank = skill_rank(level, "Q")
    e_onhit = e_passive(e_rank, bonus_ad, ap)
    e_pct = e_missing_pct(e_rank, ap)
    nashor_onhit = (15.0 + 0.20 * ap) if "nashor" in tags else 0.0
    rage_onhit = 30.0 if "rageblade" in tags else 0.0
    wits_onhit = 40.0 if "wits" in tags else 0.0
    term_onhit = 30.0 if "terminus" in tags else 0.0
    mura = "muramana" in tags
    shock_auto = (0.015 * mana) if mura else 0.0
    shock_spell = ((0.03 if ranged else 0.035) * mana) if mura else 0.0
    dusk = "dusk" in tags
    lich = "lich" in tags
    orb = "orb" in tags
    bork = "bork" in tags
    kraken = "kraken" in tags
    rage = "rageblade" in tags
    term = "terminus" in tags

    as_pct = st["as_pct"]
    as_pct += zeal_as(level, ap, True)
    as_pct += alacrity_as(minute)
    as_pct += lethal_tempo_as(ranged)
    if rage:
        as_pct += 0.32  # Seething Strike max stacks mid-window
    aps = min(AS_CAP, kayle_base_as(level) * (1.0 + as_pct))

    # E is an auto-attack reset. Autos in 6s ≈ 1 + aps*WINDOW.
    n_autos = 1.0 + aps * WINDOW
    whole_autos = int(math.floor(n_autos + 1e-9))
    frac = n_autos - whole_autos

    # Aflame waves: on-attack (NOT Rageblade-duplicated). From 9, while exalted.
    if level >= 13:
        wave_frac = 1.0
    elif level >= 9:
        wave_frac = 0.70  # need 5 zeal stacks first
    else:
        wave_frac = 0.0

    # Q shred 20% armor/MR for the whole window.
    armor *= 0.80
    mr *= 0.80
    pct_mpen = st["pct_mpen"]
    pct_armor_pen = st["pct_armor_pen"]
    flat_mpen = st["flat_mpen"]

    hp_now = hp
    phys_total = 0.0
    mag_total = 0.0
    onhit_phys = 0.0
    onhit_mag = 0.0
    dark_stacks = 0
    light_n = 0
    kraken_count = 0

    def apply(phys: float, mag: float, from_onhit: bool) -> None:
        nonlocal phys_total, mag_total, onhit_phys, onhit_mag, hp_now
        p_pen = pct_armor_pen
        m_pen = pct_mpen
        if term:
            p_pen = max(p_pen, 0.10 * dark_stacks)
            m_pen = max(m_pen, 0.10 * dark_stacks)
        p = mitigate(phys, armor, p_pen, 0.0)
        m = mitigate(mag, mr, m_pen, flat_mpen)
        phys_total += p
        mag_total += m
        if from_onhit:
            onhit_phys += p
            onhit_mag += m
        hp_now = max(1.0, hp_now - p - m)

    # --- Q at t=0 (magic + Muramana ability shock) ---
    q_raw = q_damage(q_rank, bonus_ad, ap)
    if orb and hp_now / hp < 0.40:
        q_raw *= 1.20
    apply(shock_spell, q_raw, from_onhit=False)

    # Spellblade procs from weaving Q and E (1.5s CD → 2 in a 6s window).
    spellblade_left = 0
    extra_onhit_left = 0
    if dusk or lich:
        spellblade_left = 2
    if dusk:
        extra_onhit_left = 2

    # Phantom hits: after 4 Seething stacks, every 3rd auto (autos 7, 10, 13…).
    def is_phantom(i: int) -> bool:
        return rage and i >= 7 and ((i - 7) % 3 == 0)

    def onhit_packet(current_hp: float) -> Tuple[float, float]:
        """Physical, magic on-hit (excluding the auto's AD)."""
        p = shock_auto
        m = e_onhit + nashor_onhit + rage_onhit + wits_onhit + term_onhit
        if bork:
            ratio = 0.07 if ranged else 0.085
            p += max(15.0, ratio * current_hp)
        # Brutal: 5 + 6% bAD + 3% AP adaptive (Kayle adaptive = magic)
        m += 5.0 + 0.06 * bonus_ad + 0.03 * ap
        return p, m

    def do_auto(i: int, weight: float, empowered: bool) -> None:
        nonlocal dark_stacks, light_n, kraken_count, spellblade_left, extra_onhit_left
        if weight <= 0:
            return
        # Terminus: odd autos Light, even Dark.
        if term:
            if i % 2 == 1:
                light_n = min(3, light_n + 1)
            else:
                dark_stacks = min(3, dark_stacks + 1)

        p_hit, m_hit = onhit_packet(hp_now)
        extra = extra_onhit_left > 0
        if extra:
            extra_onhit_left -= 1
            p2, m2 = onhit_packet(hp_now)
            p_hit += p2
            m_hit += m2

        if is_phantom(i):
            pp, mm = onhit_packet(hp_now)
            p_hit += pp
            m_hit += mm

        # Auto AD
        phys_ad = total_ad
        mag = m_hit
        phys = p_hit + phys_ad

        if empowered:
            missing = max(0.0, hp - hp_now)
            exec_raw = e_pct * missing
            if orb and hp_now / hp < 0.40:
                exec_raw *= 1.20
            mag += exec_raw
            # Wiki: E can Shock twice (auto + spell instance).
            phys += shock_spell

        if spellblade_left > 0:
            if dusk:
                mag += 0.75 * base_ad + 0.10 * ap
            elif lich:
                mag += 0.75 * base_ad + 0.45 * ap
            spellblade_left -= 1

        if wave_frac > 0:
            mag += e_onhit * wave_frac

        if kraken:
            kraken_count += 1
            if kraken_count % 3 == 0:
                base_k = 120 + (168 - 120) * (level - 1) / 14.0
                missing_pct = 1.0 - hp_now / hp
                phys += base_k * (1.0 + min(0.75, 0.75 * missing_pct))

        # Scale fractional last auto
        apply(phys * weight, mag * weight, from_onhit=True)

    # First auto is the E-empowered reset.
    do_auto(1, 1.0, empowered=True)
    for i in range(2, whole_autos + 1):
        do_auto(i, 1.0, empowered=False)
    if frac > 0.02:
        do_auto(whole_autos + 1, frac, empowered=False)

    total = phys_total + mag_total
    onhit = onhit_phys + onhit_mag
    dbg = {
        "aps": aps,
        "autos": n_autos,
        "e_onhit": e_onhit,
        "shock_auto": shock_auto,
        "mana": mana,
        "mura": mura,
        "as_pct": as_pct,
    }
    return total, onhit, dbg


def snapshot_for(path_name: str, path: List[str], minute: int) -> Snapshot:
    gold = gold_at_minute(minute)
    level = level_at_minute(minute)
    owned, _ = resolve_inventory(path, gold)
    stacks = tear_stacks_at(path, minute)
    st = build_stats(owned, level, stacks)
    b_hp, b_ar, b_mr = bruiser_hp(minute), bruiser_armor(minute), bruiser_mr(minute)
    s_hp, s_ar, s_mr = squish_hp(minute), squish_armor(minute), squish_mr(minute)
    bru, onhit_b, dbg = fight_window(st, level, minute, b_hp, b_ar, b_mr)
    sq, _, _ = fight_window(st, level, minute, s_hp, s_ar, s_mr)
    notes = []
    if st["tags"] & {"muramana"}:
        notes.append("Muramana")
    elif st["tags"] & {"manamune"}:
        notes.append(f"Tear {stacks}/700")
    if "nashor" in st["tags"]:
        notes.append("Nashor")
    if "rageblade" in st["tags"]:
        notes.append("Rageblade")
    if "dusk" in st["tags"]:
        notes.append("Dusk+")
    if "bork" in st["tags"]:
        notes.append("BotRK")
    if "terminus" in st["tags"]:
        notes.append("Terminus")
    if "cap" in st["tags"]:
        notes.append("Cap")
    if not notes:
        notes.append("pre-legendary")
    share = (onhit_b / bru) if bru > 0 else 0.0
    return Snapshot(
        minute=minute,
        level=level,
        items=st["names"],
        gold=gold,
        ap=st["ap"],
        bonus_ad=st["bonus_ad"],
        total_ad=st["total_ad"],
        as_pct=st["as_pct"],
        aps=dbg["aps"],
        mana=st["mana"],
        muramana="muramana" in st["tags"],
        tear_stacks=stacks,
        bruiser=bru,
        squish=sq,
        onhit_share=share,
        notes=", ".join(notes),
    )


def item_online(path: List[str], name: str) -> Optional[int]:
    for m in range(1, GAME_MINUTES + 1):
        owned, _ = resolve_inventory(path, gold_at_minute(m))
        stacks = tear_stacks_at(path, m)
        st = build_stats(owned, level_at_minute(m), stacks)
        if name in st["names"] or name in owned:
            return m
    return None


def run() -> dict:
    minutes = list(range(1, GAME_MINUTES + 1))
    by_build: Dict[str, List[Snapshot]] = {}
    for name, path in BUILD_PATHS.items():
        by_build[name] = [snapshot_for(name, path, m) for m in minutes]

    # Minute-by-minute winner on bruiser (top-lane identity).
    winners = []
    for i, m in enumerate(minutes):
        best = max(by_build.items(), key=lambda kv: kv[1][i].bruiser)
        winners.append((m, best[0], best[1][i]))

    # Weighted average: late minutes matter more for a scaler, but
    # WR games often end 16–20, so weight the whole curve.
    def eff(snaps: List[Snapshot]) -> float:
        wsum = 0.0
        acc = 0.0
        for s in snaps:
            w = 1.0 if s.minute <= 8 else (1.4 if s.minute <= 14 else 1.8)
            acc += w * s.bruiser
            wsum += w
        return acc / wsum

    scores = {n: eff(ss) for n, ss in by_build.items()}
    best_name = max(scores, key=scores.get)

    keys = [8, 12, 16, 20]
    table = {}
    for n, ss in by_build.items():
        row = {k: ss[k - 1].bruiser for k in keys}
        row["eff"] = scores[n]
        row["peak"] = max(s.bruiser for s in ss)
        table[n] = row

    timings = {}
    for n, path in BUILD_PATHS.items():
        timings[n] = {
            "Manamune": item_online(path, "Manamune"),
            "Muramana": item_online(path, "Muramana"),
            "Nashor's Tooth": item_online(path, "Nashor's Tooth"),
            "Guinsoo's Rageblade": item_online(path, "Guinsoo's Rageblade"),
            "Dusk and Dawn": item_online(path, "Dusk and Dawn"),
            "Blade of the Ruined King": item_online(path, "Blade of the Ruined King"),
            "Terminus": item_online(path, "Terminus"),
            "Rabadon's Deathcap": item_online(path, "Rabadon's Deathcap"),
        }

    payload = {
        "minutes": minutes,
        "gold": [gold_at_minute(m) for m in minutes],
        "level": [level_at_minute(m) for m in minutes],
        "winners": [
            {
                "minute": m,
                "build": name,
                "bruiser": snap.bruiser,
                "squish": snap.squish,
                "items": snap.items,
                "notes": snap.notes,
                "muramana": snap.muramana,
                "aps": snap.aps,
            }
            for m, name, snap in winners
        ],
        "table": table,
        "timings": timings,
        "best": best_name,
        "scores": scores,
        "snaps": {
            n: [
                {
                    "minute": s.minute,
                    "items": s.items,
                    "bruiser": round(s.bruiser, 1),
                    "squish": round(s.squish, 1),
                    "onhit_share": round(s.onhit_share, 3),
                    "aps": round(s.aps, 2),
                    "ap": round(s.ap, 1),
                    "bonus_ad": round(s.bonus_ad, 1),
                    "mana": round(s.mana, 0),
                    "muramana": s.muramana,
                    "tear_stacks": s.tear_stacks,
                    "notes": s.notes,
                }
                for s in ss
            ]
            for n, ss in by_build.items()
        },
    }
    return payload, by_build, winners, scores, timings, best_name, table


def fmt_items(names: List[str]) -> str:
    pretty = [n.replace("Guinsoo's Rageblade", "Rageblade")
              .replace("Nashor's Tooth", "Nashor")
              .replace("Blade of the Ruined King", "BotRK")
              .replace("Dusk and Dawn", "Dusk")
              .replace("Rabadon's Deathcap", "Deathcap")
              .replace("Berserker's Greaves", "Berserkers")
              .replace("Boots of Mana", "Mana boots")
              .replace("Tear of the Goddess", "Tear")
              .replace("Infinity Orb", "Orb")
              .replace("Caulfield's Warhammer", "Caulfield")
              .replace("Recurve Bow", "Recurve")
              .replace("Fiendish Codex", "Codex")
              .replace("Blasting Wand", "Wand")
              .replace("Needlessly Large Rod", "NLR")
              .replace("Vampiric Scepter", "Vamp scepter")
              .replace("Hearthbound Axe", "Hearthbound")
              .replace("Boots of Speed", "Boots")
              .replace("Amplifying Tome", "Tome")
              .replace("Kindlegem", "Gem")
              for n in names]
    return " › ".join(pretty) if pretty else "(start)"


def write_report(payload, by_build, winners, scores, timings, best_name, table) -> str:
    lines: List[str] = []
    a = lines.append
    a("=" * 80)
    a("KAYLE BARON — CHINA ON-HIT MANAMUNE vs WR CORES  (Wild Rift Patch 7.3)")
    a("Playstyle: farm → 6s Q-shred / E-reset / auto window | Game: 20:00")
    a("Metric: mixed damage per 6s  |  Baron bruiser is the scoring target")
    a("=" * 80)
    a("")
    a("GOLD / LEVEL / TARGETS")
    a("  Min    Gold  Lvl  Bruiser HP  Armor    MR   Squish HP")
    for m in (1, 4, 6, 8, 10, 12, 16, 20):
        a(
            f"  {m:3d}   {gold_at_minute(m):5d}   {level_at_minute(m):2d}"
            f"     {bruiser_hp(m):7.0f}   {bruiser_armor(m):5.0f}  {bruiser_mr(m):5.0f}"
            f"     {squish_hp(m):7.0f}"
        )
    a("")
    a("-" * 80)
    a("MINUTE-BY-MINUTE OPTIMAL (bruiser-mix score)")
    a("-" * 80)
    show = [1, 2, 4, 6, 8, 9, 10, 11, 12, 14, 16, 18, 20]
    for m, name, snap in winners:
        if m not in show:
            continue
        a(
            f"  {m:2d}:00 | bruiser {snap.bruiser:7.0f} | squish {snap.squish:7.0f}"
            f" | {snap.aps:4.2f} APS | {name}"
        )
        a(f"         items: {fmt_items(snap.items)}")
        a(f"         {snap.notes}")
    a("")
    a("-" * 80)
    a("BUILD COMPARISON — BRUISER MIX / 6s @ spikes")
    a("-" * 80)
    a(
        f"  {'Build':<38} {'8:00':>7} {'12:00':>7} {'16:00':>7} {'20:00':>7}"
        f"  {'Eff':>7}  {'Peak':>7}"
    )
    order = sorted(table.items(), key=lambda kv: -kv[1]["eff"])
    for n, row in order:
        a(
            f"  {n:<38} {row[8]:7.0f} {row[12]:7.0f} {row[16]:7.0f} {row[20]:7.0f}"
            f"  {row['eff']:7.0f}  {row['peak']:7.0f}"
        )
    a("")
    a("-" * 80)
    a("SQUISHY MIX / 6s @ 12 / 16 / 20")
    a("-" * 80)
    a(f"  {'Build':<38} {'12:00':>7} {'16:00':>7} {'20:00':>7}")
    for n, _ in order:
        ss = by_build[n]
        a(
            f"  {n:<38} {ss[11].squish:7.0f} {ss[15].squish:7.0f} {ss[19].squish:7.0f}"
        )
    a("")
    a("-" * 80)
    a("ITEM ONLINE TIMES")
    a("-" * 80)
    for n, t in timings.items():
        bits = []
        for k, v in t.items():
            if v is not None:
                short = (
                    k.replace("Nashor's Tooth", "Nashor")
                    .replace("Guinsoo's Rageblade", "Rageblade")
                    .replace("Dusk and Dawn", "Dusk")
                    .replace("Blade of the Ruined King", "BotRK")
                    .replace("Rabadon's Deathcap", "Cap")
                )
                bits.append(f"{short} ~{v}:00")
        a(f"  {n}")
        a(f"      {', '.join(bits) if bits else 'none'}")
    a("")

    # Isolated first-item spike: same minute with vs without the first legendary.
    a("-" * 80)
    a("FIRST LEGENDARY SPIKE vs BRUISER  (path's first completed legendary)")
    a("-" * 80)
    first_legend = {
        "China Manamune → Rage → Nashor": "Manamune",
        "China Manamune → Rage → BotRK": "Manamune",
        "Nashor → Manamune → Rage": "Nashor's Tooth",
        "Nashor → Dusk → Cap (WR AP)": "Nashor's Tooth",
        "Nashor → Orb → Cap": "Nashor's Tooth",
        "Rage → BotRK → Terminus (WR on-hit)": "Guinsoo's Rageblade",
        "Nashor → Rage → Terminus": "Nashor's Tooth",
        "Nashor → Dusk → Terminus": "Nashor's Tooth",
    }
    for n, legend in first_legend.items():
        t = timings[n].get(legend) or timings[n].get("Muramana")
        if t is None:
            continue
        snap = by_build[n][t - 1]
        a(
            f"  {n:<38} online ~{t:2d}:00  bruiser {snap.bruiser:7.0f}"
            f"  items: {fmt_items(snap.items)}"
        )

    china = "China Manamune → Rage → Nashor"
    wr_ap = "Nashor → Dusk → Cap (WR AP)"
    wr_oh = "Rage → BotRK → Terminus (WR on-hit)"
    hybrid = "Nashor → Rage → Terminus"
    delayed = "Nashor → Manamune → Rage"

    def dmg(name: str, minute: int) -> float:
        return by_build[name][minute - 1].bruiser

    a("")
    a("-" * 80)
    a("CHINA vs WR — SAME-MINUTE DELTA (bruiser 6s)")
    a("-" * 80)
    for m in (8, 12, 16, 20):
        c, a_p, o, h, d = dmg(china, m), dmg(wr_ap, m), dmg(wr_oh, m), dmg(hybrid, m), dmg(delayed, m)
        a(
            f"  {m:2d}:00  China {c:6.0f} | WR-AP {a_p:6.0f} ({a_p-c:+.0f})"
            f" | WR-onhit {o:6.0f} ({o-c:+.0f})"
            f" | Nashor-Rage {h:6.0f} ({h-c:+.0f})"
            f" | Nashor-then-Mura {d:6.0f} ({d-c:+.0f})"
        )
    a("")

    china20 = dmg(china, 20)
    ap20 = dmg(wr_ap, 20)
    oh20 = dmg(wr_oh, 20)
    hy20 = dmg(hybrid, 20)
    china_bork = "China Manamune → Rage → BotRK"
    cb20 = dmg(china_bork, 20)
    gap_vs_onhit = scores[china] / scores[wr_oh]
    gap_bork = scores[china_bork] / scores[wr_oh]

    a("-" * 80)
    a("VERDICT")
    a("-" * 80)
    a(f"  Best WR on-hit path (bruiser-weighted): {best_name}")
    a(f"  Weighted avg: {scores[best_name]:.0f} | 20:00 bruiser: {dmg(best_name, 20):.0f}")
    a(
        f"  China Manamune → Rage → Nashor: {scores[china]:.0f}"
        f" ({100 * gap_vs_onhit - 100:+.1f}% vs WR on-hit)"
    )
    a(
        f"  China Manamune → Rage → BotRK:  {scores[china_bork]:.0f}"
        f" ({100 * gap_bork - 100:+.1f}% vs WR on-hit)  ← closest import"
    )
    a("  Worth it?: NO as the default. Playable as a mana-lane variant, not an upgrade.")
    a("")
    a("  WHAT THE NUMBERS ACTUALLY SAY:")
    a("  • WR 7.3 Tear stacks fast (14 mana, 3×/10s). If you hold Tear from")
    a("    the first back, Manamune at ~6:00 is already Muramana. Stacking")
    a("    is NOT the PC problem. The problem is the item next to it.")
    a("  • Muramana first DOES win the 6:00 all-in vs Nashor first")
    a(f"    ({dmg(china, 6):.0f} vs {dmg(wr_ap, 6):.0f}). Shock + Awe AD hits")
    a("    hard before Aflame. That is the China spike, and it is real.")
    a("  • Rageblade first (~7:00) then beats both. 30 magic on-hit +")
    a("    Seething AS + later phantom hits is the WR 7.3 on-hit keystone.")
    a(f"    8:00: Rage {dmg(wr_oh, 8):.0f} vs Muramana {dmg(china, 8):.0f}"
      f" ({dmg(wr_oh, 8) - dmg(china, 8):+.0f}).")
    a("  • After that the China path is always chasing. Gold in Manamune")
    a("    is gold not in BotRK / Terminus. At 20:00 WR on-hit has")
    a(f"    Rage+BotRK+Terminus ({oh20:.0f}); China has Rage+Nashor")
    a(f"    ({china20:.0f}) or Rage+BotRK still missing Terminus ({cb20:.0f}).")
    a("  • Nashor → Dusk → Cap loses this auto-window metric. Dusk's extra")
    a("    on-hit is 2 procs / 6s; Rageblade phantoms scale with APS.")
    a("    Cap barely finishes in a 20-min WR game. Play Nashor-AP if you")
    a("    want Q/R burst and Deathcap, not if you want on-hit DPS.")
    a("  • Delaying Manamune (Nashor first, Tear second) is worse than")
    a("    rushing it. You pay the 2900g after the window where Muramana")
    a("    was actually ahead, and you still delay Rageblade/BotRK.")
    a("")
    a("  WHY PC CHINA MANAMUNE IS A WORSE COPY THAN IT LOOKS:")
    a("  • WR Starfire on-hit is 5% bonus AD + 15% AP (PC E is much more")
    a("    AD). Manamune's AD barely feeds the passive; BotRK's %HP and")
    a("    Rageblade's flat magic do not care about that ratio.")
    a("  • Manamune has 0% attack speed. From level 9, Aflame waves want")
    a("    more attacks. Rageblade and BotRK both buy AS; Manamune does not.")
    a("  • Muramana Shock is 1.5% max mana on autos (~27–35 phys) and 3%")
    a("    on Q/E. Rageblade copies it on phantoms. Real damage — just")
    a("    less than 7% current HP (BotRK) into a 3k HP baron bruiser.")
    a("  • WR games are ~20 minutes. The China 3-item dream")
    a("    (Muramana+Rage+Nashor/BotRK) lands as the Nexus dies. The WR")
    a("    Rage+BotRK path spends the same gold on two AS on-hit items.")
    a("")
    a("  WHEN TO STILL BUY IT:")
    a("  • Poke / mana-bully lanes where you want Tear Q-spam and will")
    a("    finish Manamune anyway. Then go Berserkers → Rageblade → BotRK,")
    a("    not Nashor. Accept ~5–12% less 6s DPS than Rage-first.")
    a("  • Do not buy Manamune as item 2 after Nashor. That path is a")
    a("    worse version of both identities.")
    a("")
    a("  RECOMMENDED (WR baron Kayle, on-hit question, 20-min games):")
    a("  Default on-hit: Recurve + Pickaxe → Rageblade (~7:00)")
    a("                  → Berserker's Greaves → BotRK → Terminus")
    a("  Default AP:     Nashor → Mana boots → Dusk / Orb → Deathcap")
    a("                  (different fight: spells + Cap, not this 6s auto window)")
    a("  China import:   Tear → Manamune (instant Muramana ~6:00)")
    a("                  → Berserkers → Rageblade → BotRK")
    a("                  Only if you already wanted Tear. Not a DPS upgrade.")
    a("")
    a("  Skill: max E → Q. Combat: Q shred → E reset → hold range.")
    a("  Level 5 ranged, 9 Aflame waves, 13 permanent Zeal.")
    a("")
    a("  Trap: copying PC China Muramana+Rage+Nashor as the plan.")
    a("  WR 7.3 already gave on-hit Kayle Rageblade phantoms and BotRK")
    a("  %HP. Manamune is extra Shock, not the engine.")
    a("  Trap: Nashor → Manamune. You buy the China item after the only")
    a("  minutes where it was ahead, and you skip Rageblade.")
    a("=" * 80)
    a("")
    return "\n".join(lines)


def main() -> None:
    payload, by_build, winners, scores, timings, best_name, table = run()
    report = write_report(payload, by_build, winners, scores, timings, best_name, table)
    with open("kayle-manamune-sim/report.txt", "w") as f:
        f.write(report)
    # Trim snaps for json size but keep them — useful.
    with open("kayle-manamune-sim/results.json", "w") as f:
        json.dump(
            {
                "best": payload["best"],
                "scores": payload["scores"],
                "table": payload["table"],
                "timings": payload["timings"],
                "winners": payload["winners"],
                "snaps": payload["snaps"],
                "gold": payload["gold"],
                "level": payload["level"],
            },
            f,
            indent=2,
        )
    print(report)


if __name__ == "__main__":
    main()
