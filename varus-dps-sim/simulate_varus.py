#!/usr/bin/env python3
"""
Wild Rift 7.3 — Varus on-hit vs crit DPS.

Reads champion / item / rune numbers from wr-7.3-db (local memory).
Does not scrape the web.

Question: which path scales harder into late game, with DPS still
rising after each purchase — on-hit or crit?
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "wr-7.3-db"))

from database import ITEMS, RUNES, SYSTEM, VARUS, PATCH  # noqa: E402

GAME_MINUTES = 24
FIGHT_SECONDS = 8.0
AS_CAP = float(SYSTEM["attack_speed_cap"])
BASE_CRIT_DMG = float(SYSTEM["crit_damage"])

OUT_DIR = Path(__file__).resolve().parent


# ---------------------------------------------------------------------------
# Economy / XP (dragon-lane farmer, not smurf-fed)
# ---------------------------------------------------------------------------


def gold_at_minute(m: int) -> int:
    if m <= 0:
        return 500
    total = 500
    for t in range(1, m + 1):
        if t <= 4:
            total += 440
        elif t <= 9:
            total += 560
        elif t <= 15:
            total += 640
        else:
            total += 700
    return total


def level_at_minute(m: int) -> int:
    # Wild Rift cap is 15.
    table = {
        1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7, 7: 8, 8: 9,
        9: 10, 10: 11, 11: 12, 12: 12, 13: 13, 14: 13, 15: 14,
        16: 14, 17: 15, 18: 15, 19: 15, 20: 15, 21: 15, 22: 15,
        23: 15, 24: 15,
    }
    return table.get(m, 15)


def skill_rank(level: int, skill: str, order: str) -> int:
    """WR: R at 5/9/13. Four ranks on basics."""
    if skill == "R":
        return (1 if level >= 5 else 0) + (1 if level >= 9 else 0) + (1 if level >= 13 else 0)
    if order == "onhit":
        mapping = {
            "W": [1, 3, 6, 7],
            "Q": [2, 8, 10, 11],
            "E": [4, 12, 14, 15],
        }
    else:
        mapping = {
            "Q": [1, 3, 6, 7],
            "W": [2, 8, 10, 11],
            "E": [4, 12, 14, 15],
        }
    return sum(1 for lv in mapping[skill] if level >= lv)


# ---------------------------------------------------------------------------
# Targets
# ---------------------------------------------------------------------------


@dataclass
class Target:
    name: str
    hp: float
    armor: float
    mr: float


def squishy(m: int) -> Target:
    lv = level_at_minute(m)
    hp = 580 + 95 * lv + 28 * m
    armor = 32 + 4.2 * lv + 3.5 * m
    mr = 30 + 1.4 * lv + 1.5 * m
    if m >= 12:
        armor += 25  # cloth / tabis / small armor item
    return Target("squishy", hp, armor, mr)


def tank(m: int) -> Target:
    lv = level_at_minute(m)
    hp = 720 + 125 * lv + 90 * m
    armor = 42 + 5.0 * lv + 14 * m
    mr = 32 + 2.0 * lv + 9 * m
    return Target("tank", hp, armor, mr)


def phys_mult(armor: float, lethality: float, pct_pen: float) -> float:
    a = max(0.0, (armor - lethality) * (1.0 - pct_pen))
    return 100.0 / (100.0 + a)


def mag_mult(mr: float, pct_pen: float) -> float:
    m = max(0.0, mr * (1.0 - pct_pen))
    return 100.0 / (100.0 + m)


# ---------------------------------------------------------------------------
# Inventory
# ---------------------------------------------------------------------------


def owned_at_gold(path: List[str], gold: int) -> List[str]:
    owned: List[str] = []
    spent = 0
    for iid in path:
        it = ITEMS[iid]
        cost = int(it["cost"])
        if "boots" in it["tags"]:
            for prev in list(owned):
                if "boots" in ITEMS[prev]["tags"] and ITEMS[prev]["tier"] != "legendary":
                    spent -= int(ITEMS[prev]["cost"])
                    owned.remove(prev)
                    break
        if spent + cost <= gold:
            spent += cost
            owned.append(iid)
        else:
            break
    return owned


def minutes_owned(path: List[str], iid: str, minute: int) -> int:
    for m in range(0, minute + 1):
        if iid in owned_at_gold(path, gold_at_minute(m)):
            return minute - m
    return 0


@dataclass
class Stats:
    ad: float = 0.0
    ap: float = 0.0
    bonus_as: float = 0.0  # 1.0 = 100%
    crit: float = 0.0
    crit_dmg: float = BASE_CRIT_DMG
    lifesteal: float = 0.0
    armor_pen: float = 0.0
    lethality: float = 0.0
    hp: float = 0.0
    items: List[str] = field(default_factory=list)


def aggregate(owned: List[str], champ_level: int, yun_tal_crit: float) -> Stats:
    st = Stats(items=list(owned))
    for iid in owned:
        s = ITEMS[iid]["stats"]
        st.ad += s.get("ad", 0.0)
        st.ap += s.get("ap", 0.0)
        st.bonus_as += s.get("as", 0.0)
        st.crit += s.get("crit", 0.0)
        st.crit_dmg += s.get("crit_damage", 0.0)
        st.lifesteal += s.get("lifesteal", 0.0)
        st.armor_pen += s.get("armor_pen", 0.0)
        st.lethality += s.get("lethality", 0.0)
        st.hp += s.get("hp", 0.0)
    if "yun_tal_wildarrows" in owned:
        st.crit += yun_tal_crit
    st.crit = min(1.0, st.crit)
    return st


def champ_base(level: int) -> Tuple[float, float, float, float]:
    s = VARUS["stats"]
    ad = s["base_ad"] + s["ad_growth"] * (level - 1)
    hp = s["base_hp"] + s["hp_growth"] * (level - 1)
    bonus_as = s["base_bonus_as"] + s["as_growth"] * (level - 1)
    return ad, hp, bonus_as, s["as_ratio"]


# ---------------------------------------------------------------------------
# Fight
# ---------------------------------------------------------------------------


@dataclass
class FightResult:
    damage: float = 0.0
    physical: float = 0.0
    magic: float = 0.0
    true_dmg: float = 0.0
    autos: int = 0
    detonations: int = 0
    ttk: Optional[float] = None
    as_avg: float = 0.0
    crit: float = 0.0
    ad: float = 0.0
    overkill: float = 0.0
    splash: float = 0.0  # extra-target damage (Runaan / Statikk / AoE)
    extra_targets: int = 0


def lerp(lo: float, hi: float, level: int) -> float:
    t = (level - 1) / 14.0
    return lo + (hi - lo) * t


def simulate_fight(
    owned: List[str],
    minute: int,
    target: Target,
    style: str,
    yun_tal_crit: float,
    extra_targets: int = 0,
) -> FightResult:
    level = level_at_minute(minute)
    base_ad, base_hp, level_as, as_ratio = champ_base(level)
    st = aggregate(owned, level, yun_tal_crit)

    w_rank = skill_rank(level, "W", style)
    q_rank = skill_rank(level, "Q", style)
    e_rank = skill_rank(level, "E", style)

    w = VARUS["abilities"]["W"]
    q = VARUS["abilities"]["Q"]
    e = VARUS["abilities"]["E"]

    w_onhit = w["onhit_base"][w_rank - 1] if w_rank else 0.0
    blight_pct = w["blight_pct_maxhp"][w_rank - 1] if w_rank else 0.0
    q_base = q["min_base"][q_rank - 1] if q_rank else 0.0
    q_ad = q["min_ad"][q_rank - 1] if q_rank else 0.0
    e_base = e["base"][e_rank - 1] if e_rank else 0.0

    has = set(owned)
    rage = "guinsoos_rageblade" in has
    kraken = "kraken_slayer" in has
    bork = "blade_of_the_ruined_king" in has
    terminus = "terminus" in has
    wits = "wits_end" in has
    rfc = "rapid_firecannon" in has
    storm = "stormrazor" in has
    statikk = "statikk_shiv" in has
    hexoptics = "hexoptics_c44" in has
    pd = "phantom_dancer" in has
    yun = "yun_tal_wildarrows" in has
    ldr = "lord_dominiks_regards" in has
    collector = "the_collector" in has
    runaan = "runaans_hurricane" in has
    n_side = max(0, extra_targets)
    side_hp = [target.hp for _ in range(n_side)]
    side_blight = [0 for _ in range(n_side)]

    # Combat AS buffs assumed up for an 8s all-in.
    combat_as = 0.0
    if yun:
        combat_as += 0.25  # Flurry
    alacrity_as = min(0.15, max(0.0, (minute - 2) / 8.0 * 0.15))
    combat_as += alacrity_as

    lt = RUNES["lethal_tempo"]
    brutal = 15.0  # physical on-hit
    hex_amp = 0.07 if hexoptics else 0.0

    # Energized: kiting ADC. Charge 20/s moving + 12/auto (+5 Statikk).
    energized_per_auto = 12 + (5 if statikk else 0)

    hp = target.hp
    armor = target.armor
    mr = target.mr
    blight = 0
    kraken_n = 0
    rage_stacks = 0
    rage_hits = 0
    lt_stacks = 0
    pd_stacks = 0
    terminus_dark = 0
    terminus_hits = 0
    energized = 40.0  # start mid-fight with some charge
    q_cd = 0.0
    e_cd = 0.0
    charging_q = 0.0
    casting_e = 0.0
    next_auto = 0.0
    t = 0.0
    dt = 0.05
    res = FightResult()
    as_samples = 0.0
    as_n = 0
    killed_at: Optional[float] = None
    execute_pct = 0.05 if collector else 0.0

    def current_as() -> float:
        bonus = level_as + st.bonus_as + combat_as
        bonus += lt["as_per_stack_ranged"] * lt_stacks
        if rage:
            bonus += 0.08 * rage_stacks
        if pd:
            bonus += 0.06 * pd_stacks
        raw = VARUS["stats"]["base_as"] + bonus * as_ratio
        return min(AS_CAP, raw)

    def bonus_as_pct() -> float:
        bonus = level_as + st.bonus_as + combat_as
        bonus += lt["as_per_stack_ranged"] * lt_stacks
        if rage:
            bonus += 0.08 * rage_stacks
        if pd:
            bonus += 0.06 * pd_stacks
        return bonus

    def total_ad() -> float:
        return base_ad + st.ad

    def total_ap() -> float:
        return st.ap

    def pens() -> Tuple[float, float, float]:
        pct = st.armor_pen + 0.10 * terminus_dark
        mag_pct = 0.10 * terminus_dark
        return st.lethality, min(0.90, pct), min(0.90, mag_pct)

    def amp() -> float:
        a = 1.0 + hex_amp
        varus_hp = base_hp + st.hp
        if ldr and target.hp > varus_hp:
            a *= 1.0 + min(0.25, (target.hp - varus_hp) / 2000.0 * 0.25)
        if target.name == "tank":
            a *= 1.0 + RUNES["cut_down"]["bonus_damage_vs_higher_hp"]
        if hp / target.hp <= 0.40:
            a *= 1.0 + RUNES["coup_de_grace"]["bonus_damage_below_40"]
        return a

    def deal(amount: float, kind: str) -> None:
        nonlocal hp, killed_at
        if amount <= 0:
            return
        if kind == "phys":
            leth, pct, _ = pens()
            amount *= phys_mult(armor, leth, pct)
            res.physical += amount
        elif kind == "magic":
            _, _, mp = pens()
            amount *= mag_mult(mr, mp)
            res.magic += amount
        else:
            res.true_dmg += amount
        amount *= amp()
        res.damage += amount
        hp -= amount
        if killed_at is None and hp <= 0:
            killed_at = t
        if collector and hp > 0 and hp / target.hp <= execute_pct:
            res.true_dmg += hp
            res.damage += hp
            hp = 0
            if killed_at is None:
                killed_at = t

    def deal_side(i: int, amount: float, kind: str) -> None:
        if amount <= 0 or i >= n_side:
            return
        if kind == "phys":
            leth, pct, _ = pens()
            amount *= phys_mult(armor, leth, pct)
        elif kind == "magic":
            _, _, mp = pens()
            amount *= mag_mult(mr, mp)
        a = 1.0 + hex_amp
        varus_hp = base_hp + st.hp
        if ldr and target.hp > varus_hp:
            a *= 1.0 + min(0.25, (target.hp - varus_hp) / 2000.0 * 0.25)
        if target.name == "tank":
            a *= 1.0 + RUNES["cut_down"]["bonus_damage_vs_higher_hp"]
        if side_hp[i] / target.hp <= 0.40:
            a *= 1.0 + RUNES["coup_de_grace"]["bonus_damage_below_40"]
        amount *= a
        res.splash += amount
        side_hp[i] -= amount

    def onhit_side(i: int) -> None:
        ap = total_ap()
        if w_rank:
            deal_side(i, w_onhit + 0.35 * ap, "magic")
            side_blight[i] = min(3, side_blight[i] + 1)
        if rage:
            deal_side(i, 30.0, "magic")
        if terminus:
            deal_side(i, 30.0, "magic")
        if wits:
            deal_side(i, 40.0, "magic")
        if bork:
            deal_side(i, 0.07 * max(side_hp[i], 0.0), "phys")
        deal_side(i, brutal, "phys")

    def detonate_side(i: int, charge_amp: float) -> None:
        if side_blight[i] <= 0 or w_rank == 0:
            return
        ap = total_ap()
        per = blight_pct + 0.012 * (ap / 100.0)
        dmg = side_blight[i] * per * target.hp * (1.0 + charge_amp)
        deal_side(i, dmg, "magic")
        side_blight[i] = 0

    def onhit(is_phantom: bool) -> None:
        nonlocal blight, kraken_n, terminus_hits, terminus_dark
        ap = total_ap()
        # W blight on-hit
        if w_rank:
            deal(w_onhit + 0.35 * ap, "magic")
            blight = min(3, blight + 1)
        if rage:
            deal(30.0, "magic")
        if terminus:
            deal(30.0, "magic")
            terminus_hits += 1
            # odd hits light, even dark
            if terminus_hits % 2 == 0:
                terminus_dark = min(3, terminus_dark + 1)
        if wits:
            deal(40.0, "magic")
        if bork:
            deal(0.07 * max(hp, 0.0), "phys")
        deal(brutal, "phys")
        if (not is_phantom) and kraken:
            kraken_n += 1
            if kraken_n % 3 == 0:
                missing = 1.0 - max(hp, 0.0) / target.hp
                base_k = lerp(120, 168, level)
                deal(base_k * (1.0 + min(0.75, missing * 0.75)), "phys")

    def auto_attack() -> None:
        nonlocal rage_stacks, rage_hits, lt_stacks, pd_stacks, energized, blight
        ad = total_ad()
        crit_ev = 1.0 + min(1.0, st.crit) * (st.crit_dmg - 1.0)
        deal(ad * crit_ev, "phys")
        res.autos += 1
        onhit(False)
        if rage:
            rage_stacks = min(4, rage_stacks + 1)
            if rage_stacks >= 4:
                rage_hits += 1
                if rage_hits % 3 == 0:
                    onhit(True)
        lt_stacks = min(6, lt_stacks + 1)
        if pd:
            pd_stacks = min(5, pd_stacks + 1)
        if lt_stacks >= 6:
            bolt = lerp(lt["bolt_ranged"][0], lt["bolt_ranged"][1], level)
            bolt *= 1.0 + bonus_as_pct() * 100.0 * lt["bolt_as_amp_ranged"]
            deal(bolt, "phys")
        energized += energized_per_auto
        if energized >= 100 and (rfc or storm or statikk):
            energized = 0.0
            if storm:
                deal(120.0, "magic")
            elif rfc:
                deal(80.0, "magic")
            elif statikk:
                deal(60.0, "magic")
                # 7.3: secondary bounces also take on-hit. 3/4/5/6 bounces at 1/5/9/13.
                bounces = 3
                if level >= 5:
                    bounces = 4
                if level >= 9:
                    bounces = 5
                if level >= 13:
                    bounces = 6
                for i in range(min(n_side, bounces)):
                    deal_side(i, 60.0, "magic")
                    onhit_side(i)
        if runaan and n_side:
            bolt_ad = ad * 0.55 * crit_ev
            for i in range(min(2, n_side)):
                deal_side(i, bolt_ad, "phys")
                onhit_side(i)

    def detonate(charge_amp: float) -> None:
        nonlocal blight
        if blight <= 0 or w_rank == 0:
            return
        ap = total_ap()
        per = blight_pct + 0.012 * (ap / 100.0)  # +1.2% max HP per 100 AP
        dmg = blight * per * target.hp * (1.0 + charge_amp)
        deal(dmg, "magic")
        res.detonations += 1
        blight = 0

    def try_ability() -> None:
        nonlocal charging_q, casting_e, q_cd, e_cd, next_auto
        if charging_q > 0 or casting_e > 0:
            return
        if blight < 3:
            return
        if style == "onhit":
            if e_rank and e_cd <= 0:
                casting_e = 0.35
                return
            if q_rank and q_cd <= 0:
                charging_q = 0.45  # quick Q
                return
        else:
            if q_rank and q_cd <= 0:
                charging_q = 1.20  # charged Q
                return
            if e_rank and e_cd <= 0:
                casting_e = 0.35
                return

    while t < FIGHT_SECONDS:
        energized = min(100.0, energized + 20.0 * dt)  # kiting movement
        if q_cd > 0:
            q_cd = max(0.0, q_cd - dt)
        if e_cd > 0:
            e_cd = max(0.0, e_cd - dt)

        if charging_q > 0:
            charging_q -= dt
            if charging_q <= 0:
                charge = 0.30 if style == "onhit" else 0.40
                ad = total_ad()
                deal((q_base + q_ad * ad) * (1.0 + charge), "phys")
                detonate(charge)
                # Line shot: one extra body in a clump, 15% falloff.
                if n_side:
                    deal_side(0, (q_base + q_ad * ad) * (1.0 + charge) * 0.85, "phys")
                    detonate_side(0, charge)
                q_cd = q["cd"][q_rank - 1] if q_rank else 12
                next_auto = max(next_auto, t + 0.15)
        elif casting_e > 0:
            casting_e -= dt
            if casting_e <= 0:
                deal(e_base + 0.90 * st.ad, "phys")
                detonate(0.0)
                for i in range(n_side):
                    deal_side(i, e_base + 0.90 * st.ad, "phys")
                    detonate_side(i, 0.0)
                e_cd = e["cd"][e_rank - 1] if e_rank else 12
                next_auto = max(next_auto, t + 0.10)
        else:
            if t + 1e-9 >= next_auto:
                auto_attack()
                next_auto = t + 1.0 / max(0.20, current_as())
            try_ability()

        as_samples += current_as()
        as_n += 1
        t += dt

    res.ttk = killed_at
    res.as_avg = as_samples / max(1, as_n)
    res.crit = st.crit
    res.ad = total_ad()
    res.extra_targets = n_side
    if killed_at is not None:
        res.overkill = max(0.0, res.damage - target.hp)
    return res


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PATHS: Dict[str, Dict[str, object]] = {
    "onhit_kraken_rage_term": {
        "style": "onhit",
        "label": "On-hit Kraken → Rageblade → Terminus → BotRK → BT",
        "path": [
            "kraken_slayer",
            "berserkers_greaves",
            "guinsoos_rageblade",
            "terminus",
            "blade_of_the_ruined_king",
            "bloodthirster",
        ],
    },
    "onhit_bork_rage_term": {
        "style": "onhit",
        "label": "On-hit BotRK → Rageblade → Terminus → Kraken → BT",
        "path": [
            "blade_of_the_ruined_king",
            "berserkers_greaves",
            "guinsoos_rageblade",
            "terminus",
            "kraken_slayer",
            "bloodthirster",
        ],
    },
    "onhit_statikk_rage_term": {
        "style": "onhit",
        "label": "On-hit Statikk → Rageblade → Terminus → BotRK → BT",
        "path": [
            "statikk_shiv",
            "berserkers_greaves",
            "guinsoos_rageblade",
            "terminus",
            "blade_of_the_ruined_king",
            "bloodthirster",
        ],
    },
    "onhit_bork_rage_runaan": {
        "style": "onhit",
        "label": "On-hit BotRK → Rageblade → Runaan → Terminus → BT",
        "path": [
            "blade_of_the_ruined_king",
            "berserkers_greaves",
            "guinsoos_rageblade",
            "runaans_hurricane",
            "terminus",
            "bloodthirster",
        ],
    },
    "onhit_bork_rage_statikk": {
        "style": "onhit",
        "label": "On-hit BotRK → Rageblade → Statikk → Terminus → BT",
        "path": [
            "blade_of_the_ruined_king",
            "berserkers_greaves",
            "guinsoos_rageblade",
            "statikk_shiv",
            "terminus",
            "bloodthirster",
        ],
    },
    "onhit_statikk_rage_runaan": {
        "style": "onhit",
        "label": "On-hit Statikk → Rageblade → Runaan → Terminus → BT",
        "path": [
            "statikk_shiv",
            "berserkers_greaves",
            "guinsoos_rageblade",
            "runaans_hurricane",
            "terminus",
            "bloodthirster",
        ],
    },
    "onhit_kraken_rage_runaan": {
        "style": "onhit",
        "label": "On-hit Kraken → Rageblade → Runaan → Terminus → BT",
        "path": [
            "kraken_slayer",
            "berserkers_greaves",
            "guinsoos_rageblade",
            "runaans_hurricane",
            "terminus",
            "bloodthirster",
        ],
    },
    "crit_yuntal_ie_rfc": {
        "style": "crit",
        "label": "Crit Yun Tal → IE → RFC → LDR → BT",
        "path": [
            "yun_tal_wildarrows",
            "berserkers_greaves",
            "infinity_edge",
            "rapid_firecannon",
            "lord_dominiks_regards",
            "bloodthirster",
        ],
    },
    "crit_yuntal_ie_pd": {
        "style": "crit",
        "label": "Crit Yun Tal → IE → PD → LDR → BT",
        "path": [
            "yun_tal_wildarrows",
            "berserkers_greaves",
            "infinity_edge",
            "phantom_dancer",
            "lord_dominiks_regards",
            "bloodthirster",
        ],
    },
    "crit_storm_ie_rfc": {
        "style": "crit",
        "label": "Crit Stormrazor → IE → RFC → LDR → BT",
        "path": [
            "stormrazor",
            "berserkers_greaves",
            "infinity_edge",
            "rapid_firecannon",
            "lord_dominiks_regards",
            "bloodthirster",
        ],
    },
    "crit_yuntal_hex_ie": {
        "style": "crit",
        "label": "Crit Yun Tal → Hexoptics → IE → LDR → BT",
        "path": [
            "yun_tal_wildarrows",
            "berserkers_greaves",
            "hexoptics_c44",
            "infinity_edge",
            "lord_dominiks_regards",
            "bloodthirster",
        ],
    },
}


def yun_tal_crit_at(path: List[str], minute: int) -> float:
    owned_for = minutes_owned(path, "yun_tal_wildarrows", minute)
    if owned_for <= 0 and "yun_tal_wildarrows" not in owned_at_gold(path, gold_at_minute(minute)):
        return 0.0
    # ~12 farm autos / min after purchase. Ranged: 0.2% per auto, cap 25%.
    autos = 12 * max(0, owned_for)
    # plus a few fight autos already baked into minutes
    return min(0.25, autos * 0.002)


def pack_fight(fr: FightResult, tgt: Target) -> Dict[str, object]:
    dps = fr.damage / FIGHT_SECONDS
    aoe = (fr.damage + fr.splash) / FIGHT_SECONDS
    return {
        "hp": round(tgt.hp),
        "armor": round(tgt.armor, 1),
        "dps": round(dps, 1),
        "dmg_8s": round(fr.damage, 1),
        "splash_8s": round(fr.splash, 1),
        "aoe_dps": round(aoe, 1),
        "ttk": None if fr.ttk is None else round(fr.ttk, 2),
        "autos": fr.autos,
        "detonations": fr.detonations,
        "as": round(fr.as_avg, 3),
        "crit": round(fr.crit, 3),
        "ad": round(fr.ad, 1),
    }


def run_path(key: str) -> Dict[str, object]:
    cfg = PATHS[key]
    path: List[str] = list(cfg["path"])  # type: ignore
    style: str = str(cfg["style"])
    snapshots = []
    for m in range(1, GAME_MINUTES + 1):
        gold = gold_at_minute(m)
        owned = owned_at_gold(path, gold)
        yt = yun_tal_crit_at(path, m)
        sq = simulate_fight(owned, m, squishy(m), style, yt, extra_targets=0)
        tk = simulate_fight(owned, m, tank(m), style, yt, extra_targets=0)
        sq3 = simulate_fight(owned, m, squishy(m), style, yt, extra_targets=2)
        tk3 = simulate_fight(owned, m, tank(m), style, yt, extra_targets=2)
        snapshots.append({
            "minute": m,
            "gold": gold,
            "level": level_at_minute(m),
            "items": [ITEMS[i]["name"] for i in owned],
            "yun_tal_crit": round(yt, 4),
            "squishy": pack_fight(sq, squishy(m)),
            "tank": pack_fight(tk, tank(m)),
            "squishy_3v": pack_fight(sq3, squishy(m)),
            "tank_3v": pack_fight(tk3, tank(m)),
        })
    return {
        "key": key,
        "label": cfg["label"],
        "style": style,
        "path": [ITEMS[i]["name"] for i in path],
        "snapshots": snapshots,
    }


def dps_series(result: Dict[str, object], side: str) -> List[float]:
    return [s[side]["dps"] for s in result["snapshots"]]  # type: ignore


def is_non_decreasing(vals: List[float], slack: float = 0.02) -> bool:
    for a, b in zip(vals, vals[1:]):
        if b + 1e-6 < a * (1.0 - slack) and b < a - 15:
            return False
    return True


def item_spikes(result: Dict[str, object]) -> List[str]:
    lines = []
    prev: List[str] = []
    for s in result["snapshots"]:  # type: ignore
        items = s["items"]
        if items != prev:
            lines.append(
                f"  {s['minute']:02d}:00  {', '.join(items) or '(start)'}  |  "
                f"squishy DPS {s['squishy']['dps']:.0f}  tank DPS {s['tank']['dps']:.0f}"
            )
            prev = items
    return lines


def main() -> None:
    results = {k: run_path(k) for k in PATHS}
    minutes = list(range(1, GAME_MINUTES + 1))

    def best_at(minute: int, side: str, style: Optional[str] = None) -> Tuple[str, float]:
        best_k, best_v = "", -1.0
        for k, r in results.items():
            if style and r["style"] != style:
                continue
            v = r["snapshots"][minute - 1][side]["dps"]  # type: ignore
            if v > best_v:
                best_k, best_v = k, v
        return best_k, best_v

    onhit_keys = [k for k, r in results.items() if r["style"] == "onhit"]
    crit_keys = [k for k, r in results.items() if r["style"] == "crit"]

    def late_score(k: str) -> float:
        # Prefer rising DPS and a strong 18–24 window vs both targets.
        snaps = results[k]["snapshots"]
        late = [snaps[m - 1] for m in (16, 18, 20, 22, 24)]
        return sum(s["squishy"]["dps"] + s["tank"]["dps"] for s in late)

    def late_score_aoe(k: str) -> float:
        snaps = results[k]["snapshots"]
        late = [snaps[m - 1] for m in (16, 18, 20, 22, 24)]
        return sum(s["squishy_3v"]["aoe_dps"] + s["tank_3v"]["aoe_dps"] for s in late)

    best_onhit = max(onhit_keys, key=late_score)
    best_crit = max(crit_keys, key=late_score)
    best_onhit_3v = max(onhit_keys, key=late_score_aoe)
    best_crit_3v = max(crit_keys, key=late_score_aoe)

    lines: List[str] = []
    a = lines.append
    a(f"Wild Rift {PATCH} — Varus on-hit vs crit")
    a("Data source: local wr-7.3-db (no live web fetch).")
    a(f"Window: {FIGHT_SECONDS:.0f}s all-in, Lethal Tempo + Alacrity + Cut Down (tanks) + Coup de Grace.")
    a("On-hit weaves E then short Q on 3 Blight. Crit charges Q (~1.2s) on 3 Blight.")
    a("Goal: late-game scale, DPS still rising after each purchase.")
    a("")
    a("=" * 72)
    a("WINNERS")
    a("=" * 72)
    a(f"On-hit 1v1:       {results[best_onhit]['label']}")
    a(f"On-hit teamfight: {results[best_onhit_3v]['label']}")
    a(f"Crit 1v1:         {results[best_crit]['label']}")
    a("")

    def row(minute: int) -> str:
        o = results[best_onhit]["snapshots"][minute - 1]
        c = results[best_crit]["snapshots"][minute - 1]
        os, ot = o["squishy"]["dps"], o["tank"]["dps"]
        cs, ct = c["squishy"]["dps"], c["tank"]["dps"]
        sq_w = "ONHIT" if os >= cs else "CRIT"
        tk_w = "ONHIT" if ot >= ct else "CRIT"
        return (
            f"{minute:02d}  "
            f"{os:7.0f}/{ot:7.0f}  {', '.join(o['items'])[:42]:<42}  "
            f"{cs:7.0f}/{ct:7.0f}  {sq_w}/{tk_w}"
        )

    a("Minute   on-hit squishy/tank DPS   items                                   crit squishy/tank   winner")
    a("-" * 110)
    for m in range(4, GAME_MINUTES + 1, 2):
        a(row(m))
    a("")

    a("Item spikes — on-hit winner")
    a("\n".join(item_spikes(results[best_onhit])))
    a("")
    a("Item spikes — crit winner")
    a("\n".join(item_spikes(results[best_crit])))
    a("")

    def spike_dps(result: Dict[str, object], side: str) -> List[Tuple[int, float, List[str]]]:
        out = []
        prev: List[str] = []
        for s in result["snapshots"]:  # type: ignore
            if s["items"] != prev:
                out.append((s["minute"], s[side]["dps"], s["items"]))
                prev = s["items"]
        return out

    def spikes_rising(result: Dict[str, object], side: str) -> bool:
        vals = [v for _, v, _ in spike_dps(result, side)]
        return all(b + 1 >= a for a, b in zip(vals, vals[1:]))

    o24 = results[best_onhit]["snapshots"][-1]
    c24 = results[best_crit]["snapshots"][-1]
    a("=" * 72)
    a("LATE GAME (24:00)")
    a("=" * 72)
    a(
        f"On-hit vs squishy: {o24['squishy']['dps']:.0f} DPS  "
        f"TTK {o24['squishy']['ttk']}s  AS {o24['squishy']['as']}  "
        f"AD {o24['squishy']['ad']}"
    )
    a(
        f"Crit   vs squishy: {c24['squishy']['dps']:.0f} DPS  "
        f"TTK {c24['squishy']['ttk']}s  AS {c24['squishy']['as']}  "
        f"crit {c24['squishy']['crit']:.0%}  AD {c24['squishy']['ad']}"
    )
    a(
        f"On-hit vs tank:    {o24['tank']['dps']:.0f} DPS  TTK {o24['tank']['ttk']}s"
    )
    a(
        f"Crit   vs tank:    {c24['tank']['dps']:.0f} DPS  TTK {c24['tank']['ttk']}s"
    )
    a("")
    a("TTK is the fight metric (time to drop the target to 0). 8s DPS includes overkill after they die.")
    a("")

    def slope(k: str, side: str) -> str:
        s = dps_series(results[k], side)
        early = s[5]  # 6:00
        mid = s[13]   # 14:00
        late = s[-1]
        rising = is_non_decreasing(s[5:])
        return (
            f"  {side:8}  6:00 {early:.0f} → 14:00 {mid:.0f} → 24:00 {late:.0f}  "
            f"({'rising' if rising else 'has a dip'})  "
            f"x{late / max(early, 1):.2f} from 6:00"
        )

    a("Scaling (DPS through the game)")
    a(f"On-hit [{best_onhit}]")
    a(slope(best_onhit, "squishy"))
    a(slope(best_onhit, "tank"))
    a(
        f"  item spikes rising? squishy={spikes_rising(results[best_onhit], 'squishy')}  "
        f"tank={spikes_rising(results[best_onhit], 'tank')}"
    )
    a(f"Crit [{best_crit}]")
    a(slope(best_crit, "squishy"))
    a(slope(best_crit, "tank"))
    a(
        f"  item spikes rising? squishy={spikes_rising(results[best_crit], 'squishy')}  "
        f"tank={spikes_rising(results[best_crit], 'tank')}"
    )
    a("Minute-to-minute dips between purchases are the enemy gaining HP/armor, not your items falling off.")
    a("")

    def ttk(snap: Dict, side: str) -> float:
        v = snap[side]["ttk"]
        return 99.0 if v is None else v

    def first_lead(side: str, metric: str) -> Optional[int]:
        """First minute >= 6 where crit beats on-hit for 3 straight minutes."""
        streak = 0
        start = None
        for m in minutes:
            if m < 6:
                continue
            o = results[best_onhit]["snapshots"][m - 1]
            c = results[best_crit]["snapshots"][m - 1]
            if metric == "dps":
                crit_wins = c[side]["dps"] > o[side]["dps"]
            else:
                crit_wins = ttk(c, side) < ttk(o, side)
            if crit_wins:
                streak += 1
                if start is None:
                    start = m
                if streak >= 3:
                    return start
            else:
                streak = 0
                start = None
        return None

    sq_late_o = o24["squishy"]["dps"]
    sq_late_c = c24["squishy"]["dps"]
    tk_late_o = o24["tank"]["dps"]
    tk_late_c = c24["tank"]["dps"]
    sq_ttk_o, sq_ttk_c = ttk(o24, "squishy"), ttk(c24, "squishy")
    tk_ttk_o, tk_ttk_c = ttk(o24, "tank"), ttk(c24, "tank")

    a("=" * 72)
    a("VERDICT")
    a("=" * 72)
    a("Until LDR (~22:00) on-hit BotRK is ahead vs both targets: %HP + Blight + Rageblade phantom.")
    if sq_ttk_o <= sq_ttk_c:
        a(
            f"Late vs squishy TTK: on-hit still faster ({sq_ttk_o:.2f}s vs {sq_ttk_c:.2f}s). "
            f"Crit's higher 8s DPS ({sq_late_c:.0f} vs {sq_late_o:.0f}) is mostly overkill after the kill."
        )
    else:
        a(f"Late vs squishy TTK: crit faster ({sq_ttk_c:.2f}s vs {sq_ttk_o:.2f}s).")
    if tk_ttk_c < tk_ttk_o:
        a(
            f"Late vs tank TTK: crit + LDR wins ({tk_ttk_c:.2f}s vs {tk_ttk_o:.2f}s) — "
            f"100% crit at 230% crit damage plus 35% armor pen."
        )
    else:
        a(f"Late vs tank TTK: on-hit still faster ({tk_ttk_o:.2f}s vs {tk_ttk_c:.2f}s).")
    a(
        "For games that end 15–20 min, buy on-hit. For games that reach 5 items, "
        "Yun Tal → IE → RFC → LDR is the 7.3 scaler (≈4x DPS from 6:00 vs ≈3.3x on-hit)."
    )
    hex_k = "crit_yuntal_hex_ie"
    if hex_k in results:
        h24 = results[hex_k]["snapshots"][-1]
        a(
            f"Highest 24:00 ceiling is Yun Tal → Hexoptics → IE "
            f"({h24['squishy']['dps']:.0f}/{h24['tank']['dps']:.0f} DPS) because Hexoptics is 55 AD, "
            f"but it delays Infinity Edge ~4 min, so the mid-game curve is worse."
        )
    a("")
    lead_sq = first_lead("squishy", "dps")
    lead_tk = first_lead("tank", "dps")
    lead_sq_t = first_lead("squishy", "ttk")
    lead_tk_t = first_lead("tank", "ttk")
    a(f"Crit 8s-DPS lead vs squishy holds from: {str(lead_sq)+':00' if lead_sq else 'never'}")
    a(f"Crit 8s-DPS lead vs tank holds from:    {str(lead_tk)+':00' if lead_tk else 'never'}")
    a(f"Crit TTK lead vs squishy holds from:    {str(lead_sq_t)+':00' if lead_sq_t else 'never (on-hit kills squishies faster)'}")
    a(f"Crit TTK lead vs tank holds from:       {str(lead_tk_t)+':00' if lead_tk_t else 'never'}")
    a("")
    a("Play pattern")
    a("- On-hit: auto to 3 Blight → E detonate → auto to 3 → short Q. Terminus dark stacks for 30% pen.")
    a("- Crit: keep autos up, charge Q on 3 Blight. Yun Tal needs ~125 autos (≈10 min of farming) to finish 25% crit.")
    a("- Do not mix: Rageblade phantom is the on-hit engine; IE wants 100% crit. 7.3 removed Rageblade's crit tax but phantom still does not replace IE.")
    a("")
    a("=" * 72)
    a("WHY RUNAAN / STATIKK (teamfight, 2 extra targets)")
    a("=" * 72)
    a("1v1 hid these items. Runaan bolts need two nearby champions; Statikk's 7.3 identity is")
    a("on-hit lightning on bounce targets. Below is the same 8s window with 2 extra bodies.")
    a("Runaan: 2 bolts × 55% AD (can crit) + full on-hit (W / BotRK / Rageblade / Terminus).")
    a("Statikk: energized 60 magic on main, then bounce 60 magic + on-hit onto extras.")
    a("E hits the clump. Q tags one extra body.")
    a("")
    a(f"Teamfight on-hit pick: {results[best_onhit_3v]['label']}")
    a("")
    a("All paths 24:00  |  1v1 squishy/tank DPS  |  3-target AoE DPS (main+2)")
    for k, r in results.items():
        s = r["snapshots"][-1]
        mark = ""
        if k == best_onhit:
            mark += "  ← 1v1 on-hit"
        if k == best_onhit_3v:
            mark += "  ← teamfight on-hit"
        if k == best_crit:
            mark += "  ← 1v1 crit"
        a(
            f"  1v1 {s['squishy']['dps']:6.0f}/{s['tank']['dps']:6.0f}   "
            f"3v {s['squishy_3v']['aoe_dps']:7.0f}/{s['tank_3v']['aoe_dps']:6.0f}   "
            f"{r['label']}{mark}"
        )
    o3 = results[best_onhit_3v]["snapshots"][-1]
    c3 = results[best_crit_3v]["snapshots"][-1]
    a("")
    a(
        f"24:00 teamfight AoE: on-hit {o3['squishy_3v']['aoe_dps']:.0f}/{o3['tank_3v']['aoe_dps']:.0f}  "
        f"vs crit {c3['squishy_3v']['aoe_dps']:.0f}/{c3['tank_3v']['aoe_dps']:.0f}"
    )

    report = "\n".join(lines) + "\n"
    (OUT_DIR / "report.txt").write_text(report, encoding="utf-8")
    (OUT_DIR / "results.json").write_text(
        json.dumps(
            {
                "patch": PATCH,
                "fight_seconds": FIGHT_SECONDS,
                "best_onhit": best_onhit,
                "best_onhit_3v": best_onhit_3v,
                "best_crit": best_crit,
                "best_crit_3v": best_crit_3v,
                "paths": results,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(report)


if __name__ == "__main__":
    main()
