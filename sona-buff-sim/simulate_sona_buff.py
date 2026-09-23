#!/usr/bin/env python3
"""
Wild Rift Sona Support — Buff / Gold-Efficiency Simulation
Patch 7.3 enchanter items. Average game: 20 minutes.

Question:
  Given Echoes of Helia, Whispering Circlet (→ Diadem of Songs),
  Ardent Censer, and Harmonic Echo, which purchase ORDER converts
  the same support gold into the most ally buff + game impact?

Patch 7.3 identities (official notes):
  Helia     — 30% pre-mitigation champ damage stored, dumped as heal on ally heal/shield
  Whisper   — HSP from mana (Harmony) + Tear stack → Diadem 0.8% max-mana HPS
  Ardent    — 30% AS + 25 on-hit for 6s on you and the healed/shielded ally (ADC patch)
  Harmonic  — chain 30% of heal / 35% of shield to a second ally (or extra on primary)
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import permutations
from typing import Dict, List, Optional, Tuple
import json
import math

GAME_MINUTES = 20

# ---------------------------------------------------------------------------
# Economy / XP (WR support Sona — Q sickle poke, not Zyra plant-spam)
# ---------------------------------------------------------------------------


def gold_at_minute(m: int) -> int:
    if m <= 0:
        return 500
    total = 500  # start + Spectral Sickle
    for t in range(1, m + 1):
        if t <= 4:
            total += 320  # sickle tribute from Q poke
        elif t <= 10:
            total += 450  # scythe +75/min + skirmish
        else:
            total += 560  # objective / mid-game
    return total


def level_at_minute(m: int) -> int:
    table = {
        1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7, 7: 8, 8: 8,
        9: 9, 10: 10, 11: 10, 12: 11, 13: 11, 14: 12,
        15: 12, 16: 13, 17: 13, 18: 14, 19: 14, 20: 15,
    }
    return table.get(m, min(15, 1 + m))


def skill_rank(level: int, skill: str) -> int:
    """Q max, W second, E last. R at 6/11/15."""
    if skill == "R":
        if level < 6:
            return 0
        if level < 11:
            return 1
        if level < 15:
            return 2
        return 3
    q_levels = [1, 3, 5, 7, 9]
    w_levels = [2, 4, 8, 10, 12]
    e_levels = [6, 13, 14, 15]
    mapping = {"Q": q_levels, "W": w_levels, "E": e_levels}
    return min(4, sum(1 for lv in mapping[skill] if level >= lv))


# ---------------------------------------------------------------------------
# Items — Wild Rift patch 7.3
# ---------------------------------------------------------------------------


@dataclass
class Item:
    name: str
    cost: int
    ap: float = 0
    ah: float = 0
    hp: float = 0
    mana: float = 0
    mana_regen_pct: float = 0
    hsp: float = 0  # heal/shield power, decimal (0.08 = 8%)
    ms_pct: float = 0
    helia: bool = False
    circlet: bool = False
    diadem: bool = False
    ardent: bool = False
    harmonic: bool = False
    tear: bool = False
    tags: Tuple[str, ...] = ()


ITEMS: Dict[str, Item] = {
    "Spectral Sickle": Item("Spectral Sickle", 500, ap=20, tags=("support",)),
    "Black Mist Scythe": Item(
        "Black Mist Scythe", 0, ap=28, ah=10, tags=("support",)
    ),
    "Boots of Speed": Item("Boots of Speed", 400, tags=("boots",)),
    "Ionian Boots of Lucidity": Item(
        "Ionian Boots of Lucidity",
        1000,
        ah=15,
        mana_regen_pct=0.50,
        tags=("boots",),
    ),
    "Amplifying Tome": Item("Amplifying Tome", 500, ap=20),
    "Ruby Crystal": Item("Ruby Crystal", 500, hp=200),
    "Kindlegem": Item("Kindlegem", 1000, hp=200, ah=10),
    "Forbidden Idol": Item("Forbidden Idol", 700, hsp=0.06),
    "Tear of the Goddess": Item(
        "Tear of the Goddess", 400, mana=200, ah=5, tear=True
    ),
    "Bandleglass Mirror": Item(
        "Bandleglass Mirror", 900, ap=20, ah=10, mana_regen_pct=0.50
    ),
    "Aether Wisp": Item("Aether Wisp", 950, ap=30, ms_pct=0.04),
    "Echoes of Helia": Item(
        "Echoes of Helia",
        2400,
        ap=40,
        ah=20,
        hp=200,
        mana_regen_pct=0.50,
        helia=True,
        tags=("legendary", "heal_convert"),
    ),
    "Whispering Circlet": Item(
        "Whispering Circlet",
        2400,
        hp=200,
        mana=500,
        mana_regen_pct=0.50,
        hsp=0.08,
        circlet=True,
        tags=("legendary", "hsp_mana"),
    ),
    "Diadem of Songs": Item(
        "Diadem of Songs",
        2400,
        hp=200,
        mana=1200,
        mana_regen_pct=0.50,
        hsp=0.08,
        circlet=True,
        diadem=True,
        tags=("legendary", "hsp_mana", "aura_heal"),
    ),
    "Ardent Censer": Item(
        "Ardent Censer",
        2400,
        ap=50,
        hsp=0.08,
        mana_regen_pct=0.50,
        ms_pct=0.04,
        ardent=True,
        tags=("legendary", "adc_buff"),
    ),
    "Harmonic Echo": Item(
        "Harmonic Echo",
        2500,
        ap=40,
        ah=20,
        hp=200,
        harmonic=True,
        tags=("legendary", "chain"),
    ),
}

LEGENDARIES = {
    "Echoes of Helia",
    "Whispering Circlet",
    "Diadem of Songs",
    "Ardent Censer",
    "Harmonic Echo",
}

UPGRADE_COMPONENTS = {
    "Ionian Boots of Lucidity": ("Boots of Speed",),
    "Echoes of Helia": ("Bandleglass Mirror", "Kindlegem"),
    "Harmonic Echo": ("Bandleglass Mirror", "Kindlegem"),
    "Ardent Censer": ("Forbidden Idol", "Aether Wisp"),
    "Whispering Circlet": (
        "Forbidden Idol",
        "Tear of the Goddess",
        "Ruby Crystal",
    ),
    "Diadem of Songs": ("Whispering Circlet",),
}

NEXT_COMPONENTS = {
    "Echoes of Helia": ["Bandleglass Mirror", "Kindlegem"],
    "Harmonic Echo": ["Bandleglass Mirror", "Kindlegem"],
    "Ardent Censer": ["Forbidden Idol", "Aether Wisp"],
    "Whispering Circlet": [
        "Tear of the Goddess",
        "Forbidden Idol",
        "Ruby Crystal",
    ],
    "Ionian Boots of Lucidity": ["Boots of Speed"],
}

SHORT = {
    "Echoes of Helia": "Helia",
    "Whispering Circlet": "Whisper",
    "Diadem of Songs": "Diadem",
    "Ardent Censer": "Ardent",
    "Harmonic Echo": "Harmonic",
}


def path_label(order: Tuple[str, ...], tear_rush: bool) -> str:
    names = [SHORT[n] for n in order]
    suffix = " (Tear rush)" if tear_rush else ""
    return " → ".join(names) + suffix


def make_path(order: Tuple[str, ...], tear_rush: bool) -> List[str]:
    path = ["Spectral Sickle"]
    if tear_rush:
        path.append("Tear of the Goddess")
    path.append("Boots of Speed")
    first = True
    for item in order:
        path.append(item)
        if first:
            path.append("Ionian Boots of Lucidity")
            first = False
    return path


# ---------------------------------------------------------------------------
# Inventory
# ---------------------------------------------------------------------------


def resolve_inventory(path: List[str], gold: int, minute: int) -> List[Item]:
    owned: List[str] = []
    gold_pool = gold

    def credit_for(item_name: str) -> Tuple[int, List[str]]:
        credit = 0
        remove: List[str] = []
        for c in UPGRADE_COMPONENTS.get(item_name, ()):
            if c in owned:
                credit += ITEMS[c].cost
                remove.append(c)
        return credit, remove

    def remaining_cost(item_name: str) -> int:
        if item_name == "Black Mist Scythe":
            return 0
        credit, _ = credit_for(item_name)
        return max(0, ITEMS[item_name].cost - credit)

    def can_afford(item_name: str) -> bool:
        return gold_pool >= remaining_cost(item_name)

    def buy(item_name: str) -> bool:
        nonlocal gold_pool
        if item_name in owned:
            return False
        if item_name == "Black Mist Scythe":
            if "Spectral Sickle" in owned:
                owned.remove("Spectral Sickle")
            owned.append(item_name)
            return True
        cost = remaining_cost(item_name)
        if cost > gold_pool:
            return False
        _, remove = credit_for(item_name)
        gold_pool -= cost
        for r in remove:
            owned.remove(r)
        owned.append(item_name)
        return True

    blocked_at: Optional[str] = None
    for step in path:
        if step in owned:
            continue
        if can_afford(step):
            buy(step)
        else:
            blocked_at = step
            break

    if minute >= 5 and "Spectral Sickle" in owned:
        owned.remove("Spectral Sickle")
        owned.insert(0, "Black Mist Scythe")

    if blocked_at and blocked_at in NEXT_COMPONENTS:
        for comp in NEXT_COMPONENTS[blocked_at]:
            if comp in owned:
                continue
            if gold_pool >= ITEMS[comp].cost:
                buy(comp)
        if can_afford(blocked_at):
            buy(blocked_at)
            seen = False
            for step in path:
                if step == blocked_at:
                    seen = True
                    continue
                if not seen or step in owned:
                    continue
                if can_afford(step):
                    buy(step)
                else:
                    for comp in NEXT_COMPONENTS.get(step, []):
                        if comp not in owned and gold_pool >= ITEMS[comp].cost:
                            buy(comp)
                    if can_afford(step):
                        buy(step)
                    else:
                        break

    if "Ionian Boots of Lucidity" in owned and "Boots of Speed" in owned:
        owned.remove("Boots of Speed")

    return [ITEMS[n] for n in owned]


def scythe_ap_stacks(minute: int) -> float:
    if minute < 6:
        return 0.0
    return 4.0 * min(10, minute - 5)


# Tear: +5 mana / 3.3s while Tear is held.
# Circlet: +14 mana, at most 2 / 10s. Stacks transfer. 700 → Diadem.
TEAR_MANA_PER_MIN = 5.0 * (60.0 / 3.3) * 0.88  # ~80, downtime for recalls
CIRCLET_MANA_PER_MIN = 14.0 * 6.0 * 0.85  # 2/10s * 6 = 168, *0.85 downtime


def mana_charge_at(path: List[str], minute: int) -> Tuple[float, bool, bool]:
    """Return (bonus mana from charge, has_circlet_line, is_diadem)."""
    first_tear = None
    first_circlet = None
    for m in range(1, minute + 1):
        names = [it.name for it in resolve_inventory(path, gold_at_minute(m), m)]
        if first_tear is None and any(
            n in names
            for n in (
                "Tear of the Goddess",
                "Whispering Circlet",
                "Diadem of Songs",
            )
        ):
            first_tear = m
        if first_circlet is None and any(
            n in names for n in ("Whispering Circlet", "Diadem of Songs")
        ):
            first_circlet = m
    if first_tear is None:
        return 0.0, False, False
    stacks = 0.0
    end_tear = first_circlet - 1 if first_circlet else minute
    stacks += TEAR_MANA_PER_MIN * max(0, end_tear - first_tear + 1)
    stacks = min(700.0, stacks)
    if first_circlet is not None:
        stacks += CIRCLET_MANA_PER_MIN * max(0, minute - first_circlet + 1)
        stacks = min(700.0, stacks)
        return stacks, True, stacks >= 700.0
    return stacks, False, False


# ---------------------------------------------------------------------------
# Champion math
# ---------------------------------------------------------------------------


def haste_cd_mult(ah: float) -> float:
    return 100.0 / (100.0 + max(0.0, ah))


def sona_passive_cdr(level: int) -> float:
    return 0.02 + 0.18 * (level - 1) / 14.0


def sona_base_mana(level: int) -> float:
    return 345.0 + 49.0 * (level - 1)


def sona_mana_regen_per_sec(level: int, regen_pct: float) -> float:
    base_5 = 15.0 + 0.9 * (level - 1)
    return (base_5 / 5.0) * (1.0 + regen_pct)


def q_damage(rank: int, ap: float) -> float:
    if rank <= 0:
        return 0.0
    return [0, 40, 80, 120, 160][rank] + 0.40 * ap


def q_aura(rank: int, ap: float) -> float:
    if rank <= 0:
        return 0.0
    return [0, 8, 13, 18, 23][rank] + 0.20 * ap


def w_heal(rank: int, ap: float) -> float:
    """7.2b values: 35/50/65/80 + 20% AP."""
    if rank <= 0:
        return 0.0
    return [0, 35, 50, 65, 80][rank] + 0.20 * ap


def w_shield(rank: int, ap: float) -> float:
    if rank <= 0:
        return 0.0
    return [0, 25, 50, 75, 100][rank] + 0.18 * ap


def power_chord(level: int, ap: float) -> float:
    return 20.0 + 140.0 * (level - 1) / 14.0 + 0.15 * ap


def helia_cap(level: int) -> float:
    return 80.0 + 170.0 * (level - 1) / 14.0


def adc_ad(minute: int, level: int) -> float:
    item = 0.0
    if minute >= 6:
        item += 40
    if minute >= 10:
        item += 55  # 7.3 Yun Tal / IE component
    if minute >= 14:
        item += 50
    if minute >= 18:
        item += 40
    return 60.0 + 3.4 * level + item


def adc_as(minute: int, level: int) -> float:
    item_as = 0.0
    if minute >= 8:
        item_as += 0.25
    if minute >= 13:
        item_as += 0.30
    if minute >= 17:
        item_as += 0.20
    return 0.70 * (1.0 + 0.025 * (level - 1) + item_as)


def adc_crit(minute: int) -> float:
    if minute < 10:
        return 0.0
    if minute < 14:
        return 0.25
    if minute < 18:
        return 0.50
    return 0.70


ADC_AS_RATIO = 0.70
FIGHT_S = 12.0
LANE_S = 8.0


# ---------------------------------------------------------------------------
# Combat snapshot
# ---------------------------------------------------------------------------


@dataclass
class Snapshot:
    minute: int
    build_name: str
    items: List[str]
    gold: int
    level: int
    ap: float
    ah: float
    hsp: float
    max_mana: float
    legendary_count: int
    heal_window: float
    shield_window: float
    helia_heal: float
    harmonic_extra: float
    diadem_heal: float
    sustain: float
    ardent_dps: float
    q_aura_dps: float
    sona_dps: float
    damage_enabled: float
    impact: float
    gold_eff: float
    w_casts: float
    q_casts: float
    notes: str
    has_helia: bool
    has_circlet: bool
    has_diadem: bool
    has_ardent: bool
    has_harmonic: bool
    has_idol: bool


def sum_stats(inv: List[Item], minute: int, charge_mana: float, is_diadem: bool) -> dict:
    ap = ah = hp = mana = regen = hsp = ms = 0.0
    flags = {
        "helia": False,
        "circlet": False,
        "diadem": is_diadem,
        "ardent": False,
        "harmonic": False,
        "tear": False,
        "idol": False,
        "scythe": False,
    }
    names: List[str] = []
    for it in inv:
        name = it.name
        if name == "Whispering Circlet" and is_diadem:
            name = "Diadem of Songs"
            it = ITEMS["Diadem of Songs"]
        names.append(name)
        ap += it.ap
        ah += it.ah
        hp += it.hp
        mana += it.mana
        regen += it.mana_regen_pct
        hsp += it.hsp
        ms += it.ms_pct
        if it.helia:
            flags["helia"] = True
        if it.circlet or name == "Diadem of Songs":
            flags["circlet"] = True
        if it.diadem or name == "Diadem of Songs":
            flags["diadem"] = True
        if it.ardent:
            flags["ardent"] = True
        if it.harmonic:
            flags["harmonic"] = True
        if it.tear:
            flags["tear"] = True
        if it.name == "Forbidden Idol":
            flags["idol"] = True
        if it.name == "Black Mist Scythe":
            flags["scythe"] = True
            ap += scythe_ap_stacks(minute)

    # Harmony: +0.5% HSP per max mana (item + Sona base + charge until Diadem
    # replaces Circlet's 500 + stacks with a flat 1200).
    level = level_at_minute(minute)
    base_mana = sona_base_mana(level)
    if flags["diadem"]:
        item_mana = 1200.0
        charge_shown = 0.0
    elif flags["circlet"]:
        item_mana = 500.0
        charge_shown = charge_mana
    elif flags["tear"]:
        item_mana = 200.0
        charge_shown = charge_mana
    else:
        item_mana = 0.0
        charge_shown = 0.0
    max_mana = base_mana + item_mana + charge_shown
    if flags["circlet"] or flags["diadem"]:
        # WR 7.3: "0.5% of max Mana" as HSP. 2000 mana → +10% HSP.
        # Stored as decimal, matching item hsp=0.08 for 8%.
        hsp += 0.005 * max_mana / 100.0

    return {
        "ap": ap,
        "ah": ah,
        "hp": hp,
        "mana": max_mana,
        "regen": regen,
        "hsp": hsp,
        "ms": ms,
        "names": names,
        **flags,
    }


def window_output(level: int, minute: int, st: dict, seconds: float, teamfight: bool) -> dict:
    ap, ah, hsp = st["ap"], st["ah"], st["hsp"]
    q_r, w_r = skill_rank(level, "Q"), skill_rank(level, "W")
    cdr = sona_passive_cdr(level)
    q_cd = 8.0 * haste_cd_mult(ah) * (1.0 - cdr)
    w_cd = 10.0 * haste_cd_mult(ah) * (1.0 - cdr)
    e_cd = 14.0 * haste_cd_mult(ah) * (1.0 - cdr)
    q_cd, w_cd, e_cd = max(1.8, q_cd), max(2.2, w_cd), max(3.5, e_cd)

    q_casts = seconds / q_cd
    w_casts = seconds / w_cd
    e_casts = seconds / e_cd
    # 0.54s GCD rarely binds; CDs are the limiter.

    q_mana = [0, 60, 65, 70, 75][q_r] if q_r else 60
    w_mana = [0, 85, 90, 95, 100][w_r] if w_r else 85
    e_mana = 80.0
    spent = q_casts * q_mana + w_casts * w_mana + e_casts * e_mana
    if st["circlet"] or st["diadem"]:
        spent *= 0.75  # Harmony 25% refund
    regen = sona_mana_regen_per_sec(level, st["regen"]) * seconds
    pool = st["mana"]
    mana_ok = regen + pool * 0.45
    if spent > mana_ok > 0:
        scale = max(0.62, mana_ok / spent)
        q_casts *= scale
        w_casts *= scale
        e_casts *= scale
        spent *= scale

    heal = w_heal(w_r, ap) * (1.0 + hsp)
    shield = w_shield(w_r, ap) * (1.0 + hsp)
    q_dmg = q_damage(q_r, ap)
    aura = q_aura(q_r, ap)
    pc = power_chord(level, ap)

    # Q hits: lane usually 1 champ + 1 minion; fights 1.6 champs.
    champ_hits = 1.65 if teamfight else 1.15
    q_champ_dmg = q_casts * q_dmg * champ_hits
    pc_hits = q_casts + w_casts + e_casts
    pc_dmg = (pc_hits / 3.0) * pc

    # Helia stores 30% pre-mitigation, dumped on each ally W.
    helia_heal = 0.0
    if st["helia"] and w_casts > 0:
        stored_total = 0.30 * (q_champ_dmg + pc_dmg)
        per_w = min(helia_cap(level), stored_total / w_casts)
        helia_heal = per_w * w_casts * (1.0 + hsp)

    # W: heal self + 1 ally. Ally heal triggers Helia / Harmonic / Ardent.
    ally_heal = heal * w_casts + helia_heal
    self_heal = heal * w_casts
    # Aura shields Sona + tagged allies. Fights tag ~2.2 allies; lane ~1.0.
    tagged = 2.2 if teamfight else 1.0
    ally_shield = shield * w_casts * tagged
    self_shield = shield * w_casts

    harmonic_extra = 0.0
    if st["harmonic"]:
        if teamfight:
            # Spread to a second teammate.
            harmonic_extra = 0.30 * (heal * w_casts) + 0.35 * (shield * w_casts * min(tagged, 1.4))
        else:
            # No second ally → extra on the ADC.
            harmonic_extra = 0.30 * (heal * w_casts) + 0.35 * (shield * w_casts)

    diadem_heal = 0.0
    if st["diadem"]:
        # 0.8% max mana / s while you or a recently buffed ally is in combat.
        tick = 0.008 * st["mana"] * (1.0 + hsp)
        diadem_heal = tick * seconds

    sustain = (
        ally_heal
        + 0.55 * self_heal
        + 0.85 * ally_shield
        + 0.40 * self_shield
        + harmonic_extra
        + diadem_heal
    )

    # Ardent: 30% bonus AS (AS ratio) + 25 magic on-hit, 6s, you + primary ally.
    ardent_dps = 0.0
    if st["ardent"]:
        uptime = min(0.97, 6.0 / max(5.4, w_cd) * 1.08)
        base_as = adc_as(minute, level)
        extra_as = 0.30 * ADC_AS_RATIO
        crit = adc_crit(minute)
        ad = adc_ad(minute, level)
        avg_auto = ad * (1.0 + crit)  # 7.3 crit damage 200%
        onhit_existing = base_as * 25.0
        extra_autos = extra_as * (avg_auto + 25.0)
        adc_extra = (onhit_existing + extra_autos) * uptime
        # Sona herself also gets the buff — much weaker autos.
        sona_as = 0.75
        sona_extra = (sona_as * 25.0 + extra_as * 25.0) * uptime * 0.35
        # Teamfight: aura shield sometimes Ardents a second ally (~35%).
        second = 0.35 if teamfight else 0.0
        ardent_dps = adc_extra * (1.0 + second) + sona_extra

    # Q aura on-hit for ADC + Sona (and a tagged fighter in fights).
    aura_targets = 2.1 if teamfight else 1.6
    q_aura_dps = (q_casts * aura * aura_targets) / seconds if seconds else 0.0

    sona_dps = (q_champ_dmg + pc_dmg) / seconds if seconds else 0.0

    # 7.3 is an ADC-buff patch: extra carry DPS is the game-winning buff.
    # Sustain keeps that ADC in the fight (realized-uptime). Raw HPS has
    # diminishing returns — overheal past a health bar does not win games.
    adc_hp = 700 + 90 * level + 20 * minute
    survive = min(1.18, 0.92 + sustain / max(1.0, adc_hp * 0.85))
    damage_enabled = (
        ardent_dps * seconds * survive
        + q_aura_dps * seconds * 0.90
        + sona_dps * seconds * 0.62
    )
    soft_sustain = 2400.0 * (1.0 - math.exp(-max(0.0, sustain) / 2400.0))
    impact = soft_sustain + damage_enabled

    return {
        "heal_window": ally_heal + self_heal,
        "shield_window": ally_shield + self_shield,
        "helia_heal": helia_heal,
        "harmonic_extra": harmonic_extra,
        "diadem_heal": diadem_heal,
        "sustain": sustain,
        "ardent_dps": ardent_dps,
        "q_aura_dps": q_aura_dps,
        "sona_dps": sona_dps,
        "damage_enabled": damage_enabled,
        "impact": impact,
        "w_casts": w_casts,
        "q_casts": q_casts,
    }


def compute_snapshot(build_name: str, path: List[str], minute: int) -> Snapshot:
    gold = gold_at_minute(minute)
    level = level_at_minute(minute)
    charge, _, is_diadem = mana_charge_at(path, minute)
    inv = resolve_inventory(path, gold, minute)
    st = sum_stats(inv, minute, charge, is_diadem)

    lane = window_output(level, minute, st, LANE_S, teamfight=False)
    fight = window_output(level, minute, st, FIGHT_S, teamfight=True)

    if minute < 8:
        lw, fw = 0.72, 0.28
    elif minute < 14:
        lw, fw = 0.38, 0.62
    else:
        lw, fw = 0.14, 0.86

    mix = {}
    for k in lane:
        mix[k] = lw * lane[k] + fw * fight[k]

    n_leg = sum(1 for n in st["names"] if n in LEGENDARIES)
    gold_eff = mix["impact"] / max(1.0, gold / 1000.0)

    notes = []
    if st["ardent"]:
        notes.append("Ardent 30% AS")
    if st["helia"]:
        notes.append("Helia dump")
    if st["diadem"]:
        notes.append("Diadem HPS")
    elif st["circlet"]:
        notes.append("Circlet stacking")
    if st["harmonic"]:
        notes.append("Harmonic chain")
    if st["idol"] and not st["ardent"] and not st["circlet"]:
        notes.append("Idol HSP")
    if n_leg == 0:
        notes.append("pre-legendary")

    return Snapshot(
        minute=minute,
        build_name=build_name,
        items=st["names"],
        gold=gold,
        level=level,
        ap=round(st["ap"], 1),
        ah=st["ah"],
        hsp=round(st["hsp"], 3),
        max_mana=round(st["mana"], 0),
        legendary_count=n_leg,
        heal_window=round(mix["heal_window"], 1),
        shield_window=round(mix["shield_window"], 1),
        helia_heal=round(mix["helia_heal"], 1),
        harmonic_extra=round(mix["harmonic_extra"], 1),
        diadem_heal=round(mix["diadem_heal"], 1),
        sustain=round(mix["sustain"], 1),
        ardent_dps=round(mix["ardent_dps"], 1),
        q_aura_dps=round(mix["q_aura_dps"], 1),
        sona_dps=round(mix["sona_dps"], 1),
        damage_enabled=round(mix["damage_enabled"], 1),
        impact=round(mix["impact"], 1),
        gold_eff=round(gold_eff, 2),
        w_casts=round(mix["w_casts"], 2),
        q_casts=round(mix["q_casts"], 2),
        notes=", ".join(notes) if notes else "-",
        has_helia=st["helia"],
        has_circlet=st["circlet"],
        has_diadem=st["diadem"],
        has_ardent=st["ardent"],
        has_harmonic=st["harmonic"],
        has_idol=st["idol"],
    )


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

CORE = (
    "Echoes of Helia",
    "Whispering Circlet",
    "Ardent Censer",
    "Harmonic Echo",
)


def all_paths() -> Dict[str, List[str]]:
    out: Dict[str, List[str]] = {}
    for order in permutations(CORE):
        for tear_rush in (True, False):
            # Skip Tear-rush when Circlet is already first — path already
            # buys Tear as the first Circlet component.
            if tear_rush and order[0] == "Whispering Circlet":
                continue
            name = path_label(order, tear_rush)
            out[name] = make_path(order, tear_rush)
    return out


def time_weight(m: int) -> float:
    # WR games are decided on mid-game objectives, not minute 20 paper stats.
    if m <= 6:
        return 0.75
    if m <= 10:
        return 1.15  # first legendary + first dragon
    if m <= 16:
        return 1.28  # Herald / second dragon / first Baron window
    return 1.05


def snapshot_score(s: Snapshot) -> float:
    # Buff + impact, with a small gold-efficiency kicker so a cheaper
    # spike beats an equal-impact more expensive inventory.
    kit = 1.0
    if s.has_ardent:
        kit += 0.08  # 7.3 ADC patch — this is the carry buff
    if s.has_diadem:
        kit += 0.05
    elif s.has_circlet:
        kit += 0.02
    if s.has_helia:
        kit += 0.03
    if s.has_harmonic:
        kit += 0.03
    return s.impact * kit * (1.0 + 0.04 * (s.gold_eff / 40.0))


def run_all(paths: Dict[str, List[str]]):
    results: Dict[str, List[Snapshot]] = {}
    for name, path in paths.items():
        results[name] = [compute_snapshot(name, path, m) for m in range(1, GAME_MINUTES + 1)]

    timeline = []
    for m in range(1, GAME_MINUTES + 1):
        cands = [(n, results[n][m - 1]) for n in results]
        best_n, best_s = max(cands, key=lambda x: snapshot_score(x[1]))
        timeline.append(
            {
                "minute": m,
                "winner": best_n,
                "impact": best_s.impact,
                "sustain": best_s.sustain,
                "damage_enabled": best_s.damage_enabled,
                "gold_eff": best_s.gold_eff,
                "ardent_dps": best_s.ardent_dps,
                "items": best_s.items,
                "ap": best_s.ap,
                "hsp": best_s.hsp,
                "notes": best_s.notes,
            }
        )
    return results, timeline


def first_minute_with(snaps: List[Snapshot], pred) -> Optional[int]:
    for s in snaps:
        if pred(s):
            return s.minute
    return None


def weighted_avg(snaps: List[Snapshot], attr: str) -> float:
    num = den = 0.0
    for s in snaps:
        w = time_weight(s.minute)
        num += getattr(s, attr) * w
        den += w
    return num / den if den else 0.0


def summarize(results, timeline, paths) -> str:
    ranking = []
    for name, snaps in results.items():
        w_impact = 0.0
        w_eff = 0.0
        w_sum = 0.0
        for s in snaps:
            w = time_weight(s.minute)
            w_impact += snapshot_score(s) * w
            w_eff += s.gold_eff * w
            w_sum += w
        score = w_impact / w_sum
        eff = w_eff / w_sum
        ranking.append((score, eff, name, snaps))
    ranking.sort(key=lambda x: (x[0], x[1]), reverse=True)

    lines: List[str] = []
    lines.append("=" * 80)
    lines.append("SONA SUPPORT — BUFF GOLD EFFICIENCY  (Wild Rift Patch 7.3)")
    lines.append("Items: Helia · Whispering Circlet/Diadem · Ardent · Harmonic Echo")
    lines.append("Playstyle: Q-max enchanter, cycle QWE on the ADC  |  Game: 20:00")
    lines.append("Metric: ally buff + fight impact from the SAME support gold curve")
    lines.append("=" * 80)
    lines.append("")
    lines.append("GOLD / LEVEL (support Sona)")
    lines.append(f"  {'Min':>3}  {'Gold':>6}  {'Lvl':>3}")
    for m in range(1, GAME_MINUTES + 1):
        if m in (1, 4, 6, 8, 10, 12, 14, 16, 18, 20):
            lines.append(f"  {m:>3}  {gold_at_minute(m):>6}  {level_at_minute(m):>3}")

    lines.append("")
    lines.append("-" * 80)
    lines.append("MINUTE-BY-MINUTE OPTIMAL (buff+impact score)")
    lines.append("-" * 80)
    for row in timeline:
        if row["minute"] % 2 != 0 and row["minute"] not in (1, 9, 11, 15):
            continue
        item_short = " › ".join(row["items"][:5])
        if len(row["items"]) > 5:
            item_short += " › …"
        lines.append(
            f"  {row['minute']:>2}:00 | impact {row['impact']:>7.0f} | "
            f"sustain {row['sustain']:>6.0f} | dmg+ {row['damage_enabled']:>6.0f} | "
            f"g/eff {row['gold_eff']:>5.1f} | {row['winner']}"
        )
        lines.append(f"         items: {item_short}")
        lines.append(f"         {row['notes']}")

    lines.append("")
    lines.append("-" * 80)
    lines.append("BUILD ORDER RANKING — time-weighted buff/impact  (top 12)")
    lines.append("-" * 80)
    hdr = (
        f"  {'#':<3} {'Build':<42} {'8:00':>6} {'12:00':>6} {'16:00':>6} "
        f"{'20:00':>6} {'Score':>7} {'g/eff':>6}"
    )
    lines.append(hdr)
    for i, (score, eff, name, snaps) in enumerate(ranking[:12], 1):
        lines.append(
            f"  {i:<3} {name:<42} {snaps[7].impact:>6.0f} {snaps[11].impact:>6.0f} "
            f"{snaps[15].impact:>6.0f} {snaps[19].impact:>6.0f} {score:>7.0f} {eff:>6.1f}"
        )

    lines.append("")
    lines.append("-" * 80)
    lines.append("WHEN EACH BUFF COMES ONLINE  (best path vs selected contrasts)")
    lines.append("-" * 80)

    def spike_line(name: str, snaps: List[Snapshot]) -> str:
        a = first_minute_with(snaps, lambda s: s.has_ardent)
        h = first_minute_with(snaps, lambda s: s.has_helia)
        c = first_minute_with(snaps, lambda s: s.has_circlet)
        d = first_minute_with(snaps, lambda s: s.has_diadem)
        m = first_minute_with(snaps, lambda s: s.has_harmonic)
        def fmt(x):
            return f"{x:>2}:00" if x else "  —  "
        return (
            f"  {name:<42} Ard {fmt(a)}  Hel {fmt(h)}  "
            f"Whp {fmt(c)}  Dia {fmt(d)}  Harm {fmt(m)}"
        )

    show_names = {r[2] for r in ranking[:5]}
    shown = 0
    for _, _, name, snaps in ranking:
        trap = name.startswith("Harmonic → Helia") or name.startswith("Helia → Harmonic")
        if name in show_names or trap:
            lines.append(spike_line(name, snaps))
            shown += 1
        if shown >= 8:
            break

    best_name = ranking[0][2]
    best_snaps = ranking[0][3]
    best_score = ranking[0][0]
    best_eff = ranking[0][1]
    core_tokens = [t.replace(" (Tear rush)", "") for t in best_name.split(" → ")]

    ardent_first = next(
        (r for r in ranking if r[2].startswith("Ardent → Whisper") and "Tear rush" not in r[2]),
        None,
    )
    whisper_first = next(
        (r for r in ranking if r[2].startswith("Whisper → Ardent") and "Tear rush" not in r[2]),
        None,
    )
    double_kindle = next(
        (r for r in ranking if r[2].startswith("Helia → Harmonic") or r[2].startswith("Harmonic → Helia")),
        ranking[-1],
    )

    win = best_snaps
    lose = double_kindle[3]
    t12w, t12l = win[11].impact, lose[11].impact
    t16w, t16l = win[15].impact, lose[15].impact
    pct12 = 100.0 * (t12w / t12l - 1.0) if t12l else 0.0
    pct16 = 100.0 * (t16w / t16l - 1.0) if t16l else 0.0

    ard_m = first_minute_with(win, lambda s: s.has_ardent)
    hel_m = first_minute_with(win, lambda s: s.has_helia)
    cir_m = first_minute_with(win, lambda s: s.has_circlet)
    dia_m = first_minute_with(win, lambda s: s.has_diadem)
    har_m = first_minute_with(win, lambda s: s.has_harmonic)

    lines.append("")
    lines.append("-" * 80)
    lines.append("FIRST-ITEM GOLD EFFICIENCY  (same gold, different 2400g spike @ 8–10)")
    lines.append("-" * 80)
    for prefix in ("Ardent", "Whisper", "Helia", "Harmonic"):
        row = next(
            (r for r in ranking if r[2].startswith(prefix + " →") and "Tear rush" not in r[2]),
            None,
        )
        if row is None:
            row = next((r for r in ranking if r[2].startswith(prefix + " →")), None)
        if row:
            s8, s10 = row[3][7], row[3][9]
            lines.append(
                f"  {prefix:<10}  8:00 impact {s8.impact:>6.0f} (g/eff {s8.gold_eff:>6.1f})"
                f"   10:00 impact {s10.impact:>6.0f} (g/eff {s10.gold_eff:>6.1f})  {s8.notes}"
            )

    lines.append("")
    lines.append("-" * 80)
    lines.append("ITEM ROLES (why order matters)")
    lines.append("-" * 80)
    lines.append("  Ardent  2400  50 AP, 8% HSP, NO haste. Buff: 30% AS + 25 on-hit for 6s")
    lines.append("                 on you AND the ally you W. This is the 7.3 ADC-patch item.")
    lines.append("  Helia   2400  40 AP, 20 AH, 200 HP. 30% of your champ damage stored")
    lines.append("                 (cap 80–250 by level), dumped as extra heal on W.")
    lines.append("                 Shares Bandleglass + Kindlegem with Harmonic.")
    lines.append("  Whisper 2400  8% HSP + Harmony (0.5% of max mana as HSP, 25% mana refund).")
    lines.append("                 Tear stacks transfer; 700 bonus mana → Diadem of Songs.")
    lines.append("                 Diadem: 0.8% max mana HPS in combat to lowest-HP ally.")
    lines.append("  Harmonic 2500 40 AP, 20 AH, 200 HP, NO HSP. Chain 30% heal / 35% shield")
    lines.append("                 to a second ally (or extra on the ADC in 2v2).")
    lines.append("                 Same components as Helia — buying one delays the other")
    lines.append("                 by a full item.")
    lines.append("")
    lines.append("  20-min support gold finishes ~3 legendaries. The 4th is often leftover.")
    lines.append("  First two slots decide the game. Do not spend them on the two Kindlegem")
    lines.append("  items back-to-back.")

    lines.append("")
    lines.append("-" * 80)
    lines.append("VERDICT")
    lines.append("-" * 80)
    lines.append(f"  Best order: {best_name}")
    lines.append(f"  Time-weighted buff/impact: {best_score:.0f}  |  gold-eff: {best_eff:.1f} impact / 1k gold")
    if ard_m:
        lines.append(f"  Ardent online:   ~{ard_m}:00   (ADC 30% AS + 25 on-hit — the fight buff)")
    else:
        lines.append("  Ardent: NOT finished by 20:00 — ADC has no AS buff this game")
    if cir_m:
        lines.append(f"  Circlet online:  ~{cir_m}:00   (HSP + mana refund → more W, bigger heals)")
        if dia_m:
            lines.append(f"  Diadem online:   ~{dia_m}:00   (Harmony HSP + 0.8% mana HPS)")
        else:
            lines.append("  Diadem: Circlet bought but 700 mana not stacked by 20:00")
    else:
        lines.append("  Circlet/Diadem: NOT finished by 20:00 — 4th item on a 20-min clock")
    if hel_m:
        lines.append(f"  Helia online:    ~{hel_m}:00   (poke → extra W heal, 20 AH)")
    else:
        lines.append("  Helia: NOT finished by 20:00")
    if har_m:
        lines.append(f"  Harmonic online: ~{har_m}:00   (chain to the second ally in 5v5)")
    else:
        lines.append("  Harmonic: NOT finished by 20:00 — buy only if the game goes long")
    lines.append("")
    lines.append(
        f"  Vs double-Kindlegem first ({double_kindle[2]}): "
        f"+{pct12:.0f}% impact at 12:00 ({t12w:.0f} vs {t12l:.0f}), "
        f"+{pct16:.0f}% at 16:00."
    )
    if ardent_first and whisper_first:
        a8, w8 = ardent_first[3][7].impact, whisper_first[3][7].impact
        a16, w16 = ardent_first[3][15].impact, whisper_first[3][15].impact
        lines.append(
            f"  Ardent-first vs Whisper-first: 8:00 {a8:.0f} vs {w8:.0f}  |  "
            f"16:00 {a16:.0f} vs {w16:.0f}."
        )

    first = core_tokens[0] if core_tokens else ""
    second = core_tokens[1] if len(core_tokens) > 1 else ""
    third = core_tokens[2] if len(core_tokens) > 2 else ""
    tear_on_best = "Tear rush" in best_name

    lines.append("")
    lines.append("  WHY THIS ORDER:")
    if first == "Whisper":
        lines.append("  • Whispering Circlet is the cheapest permanent heal/shield amp.")
        lines.append("    8% HSP + Harmony (~6–11% HSP from Sona's mana) + 25% mana refund.")
        lines.append("    Every later Helia dump, Harmonic chain, and W is multiplied.")
        lines.append("    Circlet completes ~8:00 (Tear + Idol + Ruby are cheap); Diadem")
        lines.append("    then comes online around the first mid-game objective swing.")
    elif first == "Ardent":
        lines.append("  • Patch 7.3 buffed marksmen (200% crit, new ADC items). Ardent is")
        lines.append("    a flat 30% AS / 25 on-hit at 2400g. First-item Ardent turns every")
        lines.append("    W into ADC damage during the 8–14 dragon window.")
    elif first == "Helia":
        lines.append("  • Helia first buys 20 AH so you cast more Q/W immediately, and")
        lines.append("    converts that poke into extra heals. It has 0 HSP, so Circlet")
        lines.append("    still needs to follow or the dumps stay small.")
    else:
        lines.append("  • First item is the earliest full legendary the gold curve can")
        lines.append("    finish, and it opens the rest of the kit.")
    if second == "Ardent":
        lines.append("  • Ardent second lands while the 7.3 ADC is finishing their first")
        lines.append("    damage item, so the 30% AS buff sits on a real auto-attacker.")
    elif second == "Helia":
        lines.append("  • Helia second adds 20 AH so Ardent stays up (more W) and turns")
        lines.append("    Q poke into extra heals. Helia has 0 HSP; Ardent already brought 8%.")
    elif second == "Whisper":
        lines.append("  • Circlet second is the HSP/mana engine. Tear stacked during item 1")
        lines.append("    so Circlet often walks into Diadem instead of a 4-minute wait.")
    if third:
        lines.append(f"  • Third ({third}) is the long-game slot — only live if the match")
        lines.append("    lasts. 20-min support gold usually finishes exactly three legendaries.")
    lines.append("  • Harmonic shares Bandleglass + Kindlegem with Helia. Buying both")
    lines.append("    before Ardent/Circlet means the ADC never gets the 7.3 fight buff.")
    lines.append("  • Tear rush before Ardent delays the 2400g spike by one component.")
    if tear_on_best:
        lines.append("    This path still buys Tear early because Circlet is first;")
        lines.append("    the 400g starts Harmony stacks immediately.")
    else:
        lines.append("    Skip Tear until Circlet is next if you are rushing Ardent.")

    rec = [
        ("Spectral Sickle → Black Mist Scythe", "quest gold / 10 AH"),
        ("Boots of Speed", "don't delay the first 2400g"),
    ]
    if first == "Whisper" or tear_on_best:
        rec.insert(1, ("Tear of the Goddess (first back)", "start Diadem stacks"))
    order_map = {
        "Ardent": ("Ardent Censer", "ADC 30% AS + 25 on-hit, 8% HSP"),
        "Whisper": ("Whispering Circlet → Diadem", "HSP + mana refund + combat HPS"),
        "Helia": ("Echoes of Helia", "20 AH + poke-to-heal"),
        "Harmonic": ("Harmonic Echo", "chain heal/shield in 5v5s"),
    }
    placed_ionian = False
    for token in core_tokens:
        if token in order_map:
            rec.append(order_map[token])
            if not placed_ionian:
                rec.append(("Ionian Boots of Lucidity", "15 AH, more W uptime"))
                placed_ionian = True

    lines.append("")
    lines.append("  RECOMMENDED PURCHASE ORDER (20-min Sona, Wild Rift 7.3):")
    for i, (item, why) in enumerate(rec, 1):
        lines.append(f"  {i}) {item:<36} — {why}")
    lines.append("")
    lines.append("  Swap Ardent → Staff of Flowing Waters (40 AP / 15 AH for 6s) if your")
    lines.append("  carry is AP (Kai'Sa hybrid, Corki, AP Ezreal). Same slot, same timing.")
    lines.append("")
    lines.append("  Trap: Helia → Harmonic. Same recipe, no ADC buff, Ardent never lands")
    lines.append("  for the 12:00 dragon. Shared Kindlegem is the least gold-efficient pair.")
    lines.append("  Trap: Harmonic first in lane. Chain has no second target; 2500g for")
    lines.append("  AH that Helia also buys, without HSP or the AS buff.")
    lines.append("  Trap: Tear rush into Ardent first. The extra 400g delays the ADC buff")
    lines.append("  a full recall — only rush Tear when Circlet is item 1 or 2.")
    lines.append("=" * 80)
    return "\n".join(lines)


def export_json(results, timeline, path: str) -> None:
    payload = {
        "meta": {
            "champion": "Sona",
            "role": "Support",
            "patch": "7.3",
            "game_minutes": GAME_MINUTES,
            "playstyle": "Q-max enchanter, buff ADC",
            "items": [
                "Echoes of Helia",
                "Whispering Circlet / Diadem of Songs",
                "Ardent Censer",
                "Harmonic Echo",
            ],
        },
        "timeline": timeline,
        "builds": {
            name: [
                {
                    "minute": s.minute,
                    "items": s.items,
                    "gold": s.gold,
                    "level": s.level,
                    "ap": s.ap,
                    "ah": s.ah,
                    "hsp": s.hsp,
                    "max_mana": s.max_mana,
                    "legendary_count": s.legendary_count,
                    "heal_window": s.heal_window,
                    "shield_window": s.shield_window,
                    "helia_heal": s.helia_heal,
                    "harmonic_extra": s.harmonic_extra,
                    "diadem_heal": s.diadem_heal,
                    "sustain": s.sustain,
                    "ardent_dps": s.ardent_dps,
                    "damage_enabled": s.damage_enabled,
                    "impact": s.impact,
                    "gold_eff": s.gold_eff,
                    "notes": s.notes,
                }
                for s in snaps
            ]
            for name, snaps in results.items()
        },
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def self_check(results: Dict[str, List[Snapshot]]) -> None:
    ardent_first = None
    helia_harmonic = None
    for name, snaps in results.items():
        if name.startswith("Ardent →") and "Whisper" in name and ardent_first is None:
            if snaps[9].has_ardent:
                ardent_first = snaps
        if name.startswith("Helia → Harmonic") and helia_harmonic is None:
            helia_harmonic = snaps
    assert ardent_first is not None, "no Ardent-first path completed Ardent by 10"
    ard10 = first_minute_with(ardent_first, lambda s: s.has_ardent)
    assert ard10 is not None and ard10 <= 10, ard10
    if helia_harmonic is not None:
        # Shared Kindlegem path should not have Ardent by the time Ardent-first does
        hh_ard = first_minute_with(helia_harmonic, lambda s: s.has_ardent)
        assert hh_ard is None or hh_ard > ard10, (hh_ard, ard10)
        assert ardent_first[11].impact > helia_harmonic[11].impact


def main() -> None:
    paths = all_paths()
    results, timeline = run_all(paths)
    self_check(results)
    report = summarize(results, timeline, paths)
    print(report)
    out_dir = "/workspace/sona-buff-sim"
    with open(f"{out_dir}/report.txt", "w", encoding="utf-8") as f:
        f.write(report + "\n")
    export_json(results, timeline, f"{out_dir}/results.json")
    print(f"\nWrote {out_dir}/report.txt and {out_dir}/results.json")


if __name__ == "__main__":
    main()
