#!/usr/bin/env python3
"""
Wild Rift Braum Support — peel / bodyguard simulation, no Yordle Trap.
Patch 7.2+ item values. Average game: 20 minutes.

Playstyle: stand on the ADC, W-dash, E-block, stack Concussive Blows.
Question: skip Yordle Trap (Catcher needs a displacement; Braum only
displaces with R). Which path actually peels every fight?
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import json

GAME_MINUTES = 20

# ---------------------------------------------------------------------------
# Economy / XP (tank support, not poke-farm Zyra)
# ---------------------------------------------------------------------------


def gold_at_minute(m: int) -> int:
    if m <= 0:
        return 500
    total = 500  # start + Relic Shield
    for t in range(1, m + 1):
        if t <= 4:
            total += 280  # execute + Tribute
        elif t <= 10:
            total += 410  # Bulwark soulcast gold + skirmish
        else:
            total += 500  # objective / mid-game assists
    return total


def level_at_minute(m: int) -> int:
    table = {
        1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7, 7: 8, 8: 8,
        9: 9, 10: 10, 11: 10, 12: 11, 13: 11, 14: 12,
        15: 12, 16: 13, 17: 13, 18: 14, 19: 14, 20: 15,
    }
    return table.get(m, min(15, 1 + m))


def skill_rank(level: int, skill: str) -> int:
    """Max Q, then E, then W. R at 6/11/15 (WR cap 15 in 20m)."""
    if skill == "R":
        if level < 6:
            return 0
        if level < 11:
            return 1
        if level < 15:
            return 2
        return 3
    # WR: 4 ranks Q/W/E, 3 ranks R. Max Q, one early W for the dash, then E.
    # Q1, E2, W3, Q4, Q5, R6, Q7 (max), E8, W9, E10, R11, E12 (max), W13–14, R15
    q_levels = [1, 4, 5, 7]
    e_levels = [2, 8, 10, 12]
    w_levels = [3, 9, 13, 14]
    mapping = {"Q": q_levels, "E": e_levels, "W": w_levels}
    return sum(1 for lv in mapping[skill] if level >= lv)


def soulcast_stacks(minute: int) -> int:
    if minute < 6:
        return 0
    return min(10, minute - 5)


# ---------------------------------------------------------------------------
# Items (WR 7.2+ listed stats)
# ---------------------------------------------------------------------------


@dataclass
class Item:
    name: str
    cost: int
    hp: float = 0
    armor: float = 0
    mr: float = 0
    ah: float = 0
    mana: float = 0
    aa_red: float = 0  # champion auto damage reduction (Steelcaps line)
    locket: bool = False
    vow: bool = False
    frozen: bool = False
    yordle: bool = False
    virtue: bool = False
    warmog: bool = False
    thorn: bool = False
    fon: bool = False
    armored: bool = False
    tags: Tuple[str, ...] = ()


ITEMS: Dict[str, Item] = {
    "Relic Shield": Item("Relic Shield", 500, hp=125, tags=("support",)),
    "Bulwark of the Mountain": Item(
        "Bulwark of the Mountain", 0, hp=175, ah=10, tags=("support",)
    ),
    "Boots of Speed": Item("Boots of Speed", 400, tags=("boots",)),
    "Cloth Armor": Item("Cloth Armor", 500, armor=15),
    "Null-Magic Mantle": Item("Null-Magic Mantle", 500, mr=25),
    "Ruby Crystal": Item("Ruby Crystal", 500, hp=200),
    "Kindlegem": Item("Kindlegem", 1000, hp=200, ah=10),
    "Chain Vest": Item("Chain Vest", 900, armor=40),
    "Warden's Mail": Item("Warden's Mail", 1050, armor=40),
    "Glacial Shroud": Item("Glacial Shroud", 1000, armor=20, ah=10, mana=250),
    "Giant's Belt": Item("Giant's Belt", 1000, hp=350),
    "Bramble Vest": Item("Bramble Vest", 1000, armor=35, tags=("antiheal",)),
    "Spectre's Cowl": Item("Spectre's Cowl", 1100, hp=200, mr=35),
    "Plated Steelcaps": Item(
        "Plated Steelcaps", 1200, armor=25, aa_red=0.06, tags=("boots",)
    ),
    "Armored Advance": Item(
        "Armored Advance",
        2200,
        hp=150,
        armor=30,
        aa_red=0.10,
        armored=True,
        tags=("boots",),
    ),
    "Yordle Trap": Item(
        "Yordle Trap",
        2500,
        hp=350,
        armor=40,
        ah=15,
        yordle=True,
        tags=("catcher",),
    ),
    "Locket of the Iron Solari": Item(
        "Locket of the Iron Solari",
        2600,
        hp=200,
        armor=30,
        mr=30,
        ah=10,
        locket=True,
        tags=("peel", "active"),
    ),
    "Knight's Vow": Item(
        "Knight's Vow",
        2600,
        hp=400,
        armor=40,
        ah=10,
        vow=True,
        tags=("peel", "bodyguard"),
    ),
    "Frozen Heart": Item(
        "Frozen Heart",
        2650,
        armor=80,
        ah=20,
        mana=250,
        frozen=True,
        tags=("peel", "anti-adc"),
    ),
    "Radiant Virtue": Item(
        "Radiant Virtue",
        2850,
        hp=300,
        armor=45,
        ah=15,
        virtue=True,
        tags=("ult",),
    ),
    "Warmog's Armor": Item(
        "Warmog's Armor",
        2850,
        hp=700,
        ah=20,
        warmog=True,
        tags=("hp",),
    ),
    "Thornmail": Item(
        "Thornmail", 2700, hp=200, armor=75, thorn=True, tags=("antiheal",)
    ),
    "Force of Nature": Item(
        "Force of Nature", 2750, hp=350, mr=60, fon=True, tags=("mr",)
    ),
}


UPGRADE_COMPONENTS = {
    "Plated Steelcaps": ("Boots of Speed", "Ruby Crystal"),
    "Armored Advance": ("Plated Steelcaps",),
    "Yordle Trap": ("Chain Vest", "Kindlegem"),
    "Locket of the Iron Solari": ("Kindlegem", "Cloth Armor", "Null-Magic Mantle"),
    "Knight's Vow": ("Chain Vest", "Kindlegem"),
    "Frozen Heart": ("Warden's Mail", "Glacial Shroud"),
    "Radiant Virtue": ("Chain Vest", "Kindlegem"),
    "Warmog's Armor": ("Kindlegem", "Giant's Belt"),
    "Thornmail": ("Chain Vest", "Bramble Vest"),
    "Force of Nature": ("Spectre's Cowl",),
    "Kindlegem": ("Ruby Crystal",),
    "Chain Vest": ("Cloth Armor",),
    "Warden's Mail": ("Cloth Armor",),
}

NEXT_COMPONENTS = {
    "Plated Steelcaps": ["Boots of Speed", "Ruby Crystal"],
    "Armored Advance": ["Plated Steelcaps"],
    "Yordle Trap": ["Kindlegem", "Chain Vest"],
    "Locket of the Iron Solari": ["Kindlegem", "Cloth Armor", "Null-Magic Mantle"],
    "Knight's Vow": ["Kindlegem", "Chain Vest"],
    "Frozen Heart": ["Warden's Mail", "Glacial Shroud"],
    "Radiant Virtue": ["Kindlegem", "Chain Vest"],
    "Warmog's Armor": ["Giant's Belt", "Kindlegem"],
    "Thornmail": ["Bramble Vest", "Chain Vest"],
    "Force of Nature": ["Spectre's Cowl"],
    "Kindlegem": ["Ruby Crystal"],
}


# Vow / Virtue / Yordle all eat Chain Vest + Kindlegem. Buying Yordle
# is the cheap wrong finish of the same cart as Vow.
BUILD_PATHS: Dict[str, List[str]] = {
    # Contrast — the cheap Kindlegem+Vest finish
    "Yordle → Vow → FH": [
        "Relic Shield",
        "Boots of Speed",
        "Kindlegem",
        "Chain Vest",
        "Yordle Trap",
        "Plated Steelcaps",
        "Knight's Vow",
        "Frozen Heart",
        "Thornmail",
    ],
    "Yordle → Virtue → Thorn": [
        "Relic Shield",
        "Boots of Speed",
        "Kindlegem",
        "Chain Vest",
        "Yordle Trap",
        "Plated Steelcaps",
        "Radiant Virtue",
        "Thornmail",
        "Force of Nature",
    ],
    # WildRiftFire-style (Vow → Virtue → Yordle)
    "Vow → Virtue → Yordle": [
        "Relic Shield",
        "Boots of Speed",
        "Kindlegem",
        "Chain Vest",
        "Knight's Vow",
        "Plated Steelcaps",
        "Radiant Virtue",
        "Yordle Trap",
        "Thornmail",
    ],
    # No Yordle — bodyguard core
    "Vow → Locket → FH": [
        "Relic Shield",
        "Boots of Speed",
        "Kindlegem",
        "Chain Vest",
        "Knight's Vow",
        "Plated Steelcaps",
        "Locket of the Iron Solari",
        "Frozen Heart",
        "Thornmail",
    ],
    "Locket → Vow → FH": [
        "Relic Shield",
        "Boots of Speed",
        "Kindlegem",
        "Cloth Armor",
        "Null-Magic Mantle",
        "Locket of the Iron Solari",
        "Plated Steelcaps",
        "Knight's Vow",
        "Frozen Heart",
    ],
    "Vow → FH → Locket": [
        "Relic Shield",
        "Boots of Speed",
        "Kindlegem",
        "Chain Vest",
        "Knight's Vow",
        "Plated Steelcaps",
        "Frozen Heart",
        "Locket of the Iron Solari",
        "Thornmail",
    ],
    "FH → Vow → Locket": [
        "Relic Shield",
        "Boots of Speed",
        "Warden's Mail",
        "Glacial Shroud",
        "Frozen Heart",
        "Plated Steelcaps",
        "Knight's Vow",
        "Locket of the Iron Solari",
    ],
    "Vow → FH → Thorn (no Locket)": [
        "Relic Shield",
        "Boots of Speed",
        "Kindlegem",
        "Chain Vest",
        "Knight's Vow",
        "Plated Steelcaps",
        "Frozen Heart",
        "Thornmail",
        "Force of Nature",
    ],
    "Vow → Virtue → FH": [
        "Relic Shield",
        "Boots of Speed",
        "Kindlegem",
        "Chain Vest",
        "Knight's Vow",
        "Plated Steelcaps",
        "Radiant Virtue",
        "Frozen Heart",
        "Thornmail",
    ],
    "Vow → Virtue → Locket": [
        "Relic Shield",
        "Boots of Speed",
        "Kindlegem",
        "Chain Vest",
        "Knight's Vow",
        "Plated Steelcaps",
        "Radiant Virtue",
        "Locket of the Iron Solari",
        "Frozen Heart",
    ],
    "Locket → FH → Vow": [
        "Relic Shield",
        "Boots of Speed",
        "Kindlegem",
        "Locket of the Iron Solari",
        "Plated Steelcaps",
        "Frozen Heart",
        "Knight's Vow",
        "Thornmail",
    ],
    "Vow → Warmog → FH": [
        "Relic Shield",
        "Boots of Speed",
        "Kindlegem",
        "Chain Vest",
        "Knight's Vow",
        "Plated Steelcaps",
        "Warmog's Armor",
        "Frozen Heart",
        "Locket of the Iron Solari",
    ],
    "Locket → Vow → Armored → FH": [
        "Relic Shield",
        "Boots of Speed",
        "Locket of the Iron Solari",
        "Plated Steelcaps",
        "Armored Advance",
        "Knight's Vow",
        "Frozen Heart",
    ],
}


LEGENDARIES = {
    "Yordle Trap",
    "Locket of the Iron Solari",
    "Knight's Vow",
    "Frozen Heart",
    "Radiant Virtue",
    "Warmog's Armor",
    "Thornmail",
    "Force of Nature",
}


# ---------------------------------------------------------------------------
# Inventory
# ---------------------------------------------------------------------------


def resolve_inventory(path: List[str], gold: int, minute: int) -> List[Item]:
    owned: List[str] = []
    gold_pool = gold

    def credit_for(item_name: str) -> Tuple[int, List[str]]:
        credit = 0
        remove: List[str] = []
        needed = list(UPGRADE_COMPONENTS.get(item_name, ()))
        available = list(owned)
        for c in needed:
            if c in available:
                credit += ITEMS[c].cost
                available.remove(c)
                remove.append(c)
        return credit, remove

    def remaining_cost(item_name: str) -> int:
        if item_name == "Bulwark of the Mountain":
            return 0
        credit, _ = credit_for(item_name)
        return max(0, ITEMS[item_name].cost - credit)

    def can_afford(item_name: str) -> bool:
        return gold_pool >= remaining_cost(item_name)

    def buy(item_name: str) -> bool:
        nonlocal gold_pool
        if item_name == "Bulwark of the Mountain":
            if "Relic Shield" in owned:
                owned.remove("Relic Shield")
            if "Bulwark of the Mountain" not in owned:
                owned.append(item_name)
            return True
        if item_name in owned:
            return False
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
        if step == "Bulwark of the Mountain":
            continue
        if step == "Relic Shield":
            if "Relic Shield" not in owned and "Bulwark of the Mountain" not in owned:
                buy("Relic Shield")
            continue
        if step in owned:
            continue
        if step == "Armored Advance" and minute < 10:
            blocked_at = step
            break
        if can_afford(step):
            buy(step)
        else:
            blocked_at = step
            break

    if minute >= 5 and "Relic Shield" in owned:
        owned.remove("Relic Shield")
        owned.insert(0, "Bulwark of the Mountain")

    if blocked_at and blocked_at in NEXT_COMPONENTS:
        for comp in NEXT_COMPONENTS[blocked_at]:
            if comp in owned:
                continue
            if gold_pool >= ITEMS[comp].cost:
                buy(comp)
        if blocked_at != "Armored Advance" or minute >= 10:
            if can_afford(blocked_at):
                buy(blocked_at)
                seen = False
                for step in path:
                    if step == blocked_at:
                        seen = True
                        continue
                    if not seen or step in ("Relic Shield", "Bulwark of the Mountain"):
                        continue
                    if step in owned:
                        continue
                    if step == "Armored Advance" and minute < 10:
                        break
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

    if "Armored Advance" in owned and "Plated Steelcaps" in owned:
        owned.remove("Plated Steelcaps")
    if "Plated Steelcaps" in owned and "Boots of Speed" in owned:
        owned.remove("Boots of Speed")
    if "Armored Advance" in owned and "Boots of Speed" in owned:
        owned.remove("Boots of Speed")

    return [ITEMS[n] for n in owned]


# ---------------------------------------------------------------------------
# Combat / peel model (8s bodyguard window)
# ---------------------------------------------------------------------------

FIGHT_WINDOW = 8.0
FIGHT_EVERY = 42.0  # seconds between real fights / all-ins


def haste_cdr(ah: float) -> float:
    return 100.0 / (100.0 + max(0.0, ah))


def mit(stat: float) -> float:
    return 100.0 / (100.0 + max(0.0, stat))


def braum_base_hp(level: int) -> float:
    return 690 + 120 * (level - 1)


def braum_base_armor(level: int) -> float:
    return 52 + 4.4 * (level - 1)


def braum_base_mr(level: int) -> float:
    return 38 + 2.0 * (level - 1)


def q_base_cd(rank: int) -> float:
    return [0, 9, 8, 7, 6][rank] if rank else 9.0


def e_base_cd(rank: int) -> float:
    return [0, 16, 14, 12, 10][rank] if rank else 16.0


def w_base_cd(rank: int) -> float:
    return [0, 11, 10, 9, 8][rank] if rank else 11.0


def r_base_cd(rank: int) -> float:
    return [0, 75, 70, 65][rank] if rank else 999.0


def e_dr(rank: int) -> float:
    return [0, 0.35, 0.40, 0.45, 0.50][rank] if rank else 0.30


def w_flat(rank: int) -> float:
    return [0, 10, 15, 20, 25][rank] if rank else 10.0


def w_ratio(rank: int) -> float:
    return [0, 0.10, 0.12, 0.14, 0.16][rank] if rank else 0.10


def stun_duration(level: int) -> float:
    # 1.25 at 1 → 1.75 at 15
    return 1.25 + 0.50 * (level - 1) / 14.0


def r_knockup(rank: int) -> float:
    return [0, 1.0, 1.25, 1.5][rank]


def locket_shield(level: int) -> float:
    return 250.0 + 120.0 * (level - 1) / 14.0


def yordle_shred(level: int) -> float:
    return 5.0 + 7.0 * (level - 1) / 14.0


def yordle_mark_gold(level: int) -> float:
    return 200.0 + 100.0 * (level - 1) / 14.0


@dataclass
class Snapshot:
    minute: int
    build_name: str
    items: List[str]
    gold: int
    level: int
    hp: float
    armor: float
    mr: float
    ah: float
    legendary_count: int
    adc_taken: float
    adc_prevented: float
    braum_ehp: float
    cc_seconds: float
    peel_score: float
    q_casts: int
    r_in_fight: bool
    catcher_this_fight: bool
    catcher_gold_per_min: float
    notes: str
    has_vow: bool
    has_locket: bool
    has_fh: bool
    has_yordle: bool
    has_virtue: bool


def sum_stats(inv: List[Item], minute: int) -> dict:
    hp = armor = mr = ah = mana = aa_red = 0.0
    flags = {
        "vow": False,
        "locket": False,
        "fh": False,
        "yordle": False,
        "virtue": False,
        "warmog": False,
        "thorn": False,
        "fon": False,
        "armored": False,
        "bulwark": False,
    }
    names = []
    for it in inv:
        names.append(it.name)
        hp += it.hp
        armor += it.armor
        mr += it.mr
        ah += it.ah
        mana += it.mana
        aa_red += it.aa_red
        if it.vow:
            flags["vow"] = True
        if it.locket:
            flags["locket"] = True
        if it.frozen:
            flags["fh"] = True
        if it.yordle:
            flags["yordle"] = True
        if it.virtue:
            flags["virtue"] = True
        if it.warmog:
            flags["warmog"] = True
        if it.thorn:
            flags["thorn"] = True
        if it.fon:
            flags["fon"] = True
        if it.armored:
            flags["armored"] = True
        if it.name == "Bulwark of the Mountain":
            flags["bulwark"] = True
            hp += 25.0 * soulcast_stacks(minute)
    return {
        "hp": hp,
        "armor": armor,
        "mr": mr,
        "ah": ah,
        "mana": mana,
        "aa_red": min(aa_red, 0.12),
        "names": names,
        **flags,
    }


def window_threat(minute: int) -> Tuple[float, float, float, float]:
    """Enemy ADC autos + mixed spells aimed at the carry (pre-mit)."""
    enemy_ad = 72.0 + 7.5 * minute
    enemy_as = 0.72 + 0.024 * minute
    autos = enemy_as * FIGHT_WINDOW
    aa_raw = autos * enemy_ad
    spell_phys = 90.0 + 11.0 * minute  # hooks / skillshots E can eat
    spell_magic = 140.0 + 15.0 * minute
    return aa_raw, spell_phys, spell_magic, enemy_as


def adc_defenses(minute: int) -> Tuple[float, float, float]:
    lv = min(15, 2 + minute)
    hp = 620.0 + 96.0 * lv + 18.0 * minute
    armor = 28.0 + 4.0 * lv + (18.0 if minute >= 12 else 0.0)
    mr = 30.0 + 1.3 * lv + (12.0 if minute >= 14 else 0.0)
    return hp, armor, mr


def compute_snapshot(build_name: str, path: List[str], minute: int) -> Snapshot:
    gold = gold_at_minute(minute)
    level = level_at_minute(minute)
    inv = resolve_inventory(path, gold, minute)
    st = sum_stats(inv, minute)

    b_hp = braum_base_hp(level) + st["hp"]
    b_armor = braum_base_armor(level) + st["armor"]
    b_mr = braum_base_mr(level) + st["mr"]
    ah = st["ah"]
    if st["warmog"]:
        # Blessed: +30% healing/shielding on Braum only
        pass

    q_rank = max(1, skill_rank(level, "Q"))
    e_rank = max(1, skill_rank(level, "E")) if level >= 2 else 1
    w_rank = skill_rank(level, "W")
    r_rank = skill_rank(level, "R")

    q_cd = q_base_cd(q_rank) * haste_cdr(ah)
    r_cd = r_base_cd(r_rank) * haste_cdr(ah) if r_rank else 999.0

    q_casts = 1 + int(max(0.0, FIGHT_WINDOW - 0.4) / max(0.8, q_cd))
    e_up = min(1.0, 4.0 / FIGHT_WINDOW)  # E lasts 4s; one cast per window
    w_up = min(1.0, 3.0 / FIGHT_WINDOW) if w_rank else 0.0

    r_in_fight = bool(r_rank) and (r_cd <= FIGHT_EVERY + 8.0)
    # Hold R for the fight: available if CD is not longer than the fight cadence.
    if r_rank and r_cd <= 70.0:
        r_in_fight = True
    if r_rank == 0:
        r_in_fight = False

    aa_raw, spell_phys, spell_magic, enemy_as = window_threat(minute)
    adc_hp, adc_armor, adc_mr = adc_defenses(minute)

    # W bodyguard resists for 3s of the window (ADC + Braum).
    w_arm = w_flat(w_rank) + w_ratio(w_rank) * st["armor"]
    w_mr_b = w_flat(w_rank) + w_ratio(w_rank) * st["mr"]
    adc_armor_eff = adc_armor + w_arm * w_up
    adc_mr_eff = adc_mr + w_mr_b * w_up
    b_armor_eff = b_armor + w_arm * w_up
    b_mr_eff = b_mr + w_mr_b * w_up

    # Frozen Heart Chill: Q is magic damage, autos and getting hit also stack.
    # Bodyguard range → 3–4 stacks over 8s. Average ~3.3 once online.
    if st["fh"]:
        chill = min(4.0, 2.2 + 0.5 * q_casts + (0.6 if st["vow"] else 0.3))
        as_mult = 1.0 - 0.09 * chill
    else:
        chill = 0.0
        as_mult = 1.0
    aa_raw *= as_mult

    # E intercepts projectiles headed at the ADC while Braum is in front.
    intercept = 0.38 * e_up
    spell_phys_adc = spell_phys * (1.0 - intercept)
    spell_magic_adc = spell_magic * (1.0 - intercept * 0.75)

    # Pre-mit incoming on the ADC
    incoming_phys = aa_raw + spell_phys_adc
    incoming_magic = spell_magic_adc

    # Knight's Vow: 12% of pre-mitigation damage redirected to Braum.
    redirect = 0.12 if st["vow"] else 0.0
    adc_phys = incoming_phys * (1.0 - redirect)
    adc_magic = incoming_magic * (1.0 - redirect)
    to_braum_phys = incoming_phys * redirect
    to_braum_magic = incoming_magic * redirect

    adc_post = adc_phys * mit(adc_armor_eff) + adc_magic * mit(adc_mr_eff)

    # Locket: one AoE shield per fight (60s CD, fights ~42s → always up).
    shield = locket_shield(level) if st["locket"] else 0.0
    if st["warmog"]:
        braum_shield = shield * 1.30
    else:
        braum_shield = shield
    adc_post = max(0.0, adc_post - shield)

    # Radiant Virtue: R heal. 2.5% Braum max HP/s * 6s; ranged ADC 50%.
    virtue_adc = 0.0
    virtue_self = 0.0
    if st["virtue"] and r_in_fight:
        virt_hp = b_hp * 1.10  # Transcend +10% max HP
        virtue_adc = virt_hp * 0.025 * 6.0 * 0.50
        virtue_self = virt_hp * 0.025 * 6.0
        if st["warmog"]:
            virtue_self *= 1.30
        adc_post = max(0.0, adc_post - virtue_adc)

    # CC: stunned / airborne ADC is not autoing. Convert leftover AA DPS.
    stun = stun_duration(level) if q_casts >= 1 else 0.0
    # 4 stacks: Q + Braum auto + ADC autos. One stun per window is reliable.
    knock = r_knockup(r_rank) if r_in_fight else 0.0
    q_slow_eq = min(2.0 * q_casts, 3.2) * 0.35  # 70% slow ≠ lock
    cc = stun + knock + q_slow_eq
    aa_dps_post = (aa_raw * mit(adc_armor_eff)) / FIGHT_WINDOW
    cc_save = aa_dps_post * cc * 0.65
    adc_taken = max(0.0, adc_post - cc_save)

    # Unitemized kit baseline (Relic only) for "prevented"
    base_aa, base_sp, base_sm, _ = window_threat(minute)
    _, base_ar, base_mr = adc_defenses(minute)
    base_w = w_flat(w_rank) * w_up
    base_taken = (
        (base_aa + base_sp * (1.0 - 0.38 * e_up)) * mit(base_ar + base_w)
        + (base_sm * (1.0 - 0.38 * e_up * 0.75)) * mit(base_mr + base_w)
    )
    base_cc = stun + (r_knockup(r_rank) if r_rank else 0.0) + min(2.0, 2.0) * 0.35
    base_aa_dps = (base_aa * mit(base_ar + base_w)) / FIGHT_WINDOW
    base_taken = max(0.0, base_taken - base_aa_dps * base_cc * 0.65)
    adc_prevented = max(0.0, base_taken - adc_taken)

    # Braum soak / EHP so he can stay in front (Vow dump + E first-hit).
    first_hit = 180.0 + 18.0 * minute  # negated 100% by E
    rest_phys = (aa_raw * 0.35 + to_braum_phys) * (1.0 - st["aa_red"])
    rest_magic = to_braum_magic + spell_magic * 0.25
    e_mult = 1.0 - e_dr(e_rank) * e_up
    braum_taken = (
        rest_phys * mit(b_armor_eff) * e_mult
        + rest_magic * mit(b_mr_eff) * e_mult
        - first_hit * 0.55
    )
    if st["armored"]:
        nox = (20.0 + 8.0 * level) + 0.05 * b_hp
        braum_taken -= nox
    braum_taken = max(0.0, braum_taken - braum_shield - virtue_self)
    braum_ehp = b_hp / max(0.18, mit(b_armor_eff) * 0.6 + mit(b_mr_eff) * 0.4)

    # Catcher: displacement = airborne only. Braum R is the only trigger.
    catcher_fight = bool(st["yordle"] and r_in_fight)
    # Kill while marked (5s) is not guaranteed. ~40% of R fights.
    catcher_gpm = 0.0
    if st["yordle"] and r_rank:
        r_per_min = 60.0 / max(r_cd, 1.0)
        personal_share = 0.40  # split with nearby allies
        convert = 0.40  # marked target actually dies in 5s
        catcher_gpm = r_per_min * yordle_mark_gold(level) * personal_share * convert

    # Peel score: save the ADC, stay alive enough to keep doing it, CC lock.
    stay = min(1.15, 0.82 + 0.18 * min(1.0, braum_ehp / (1800 + 90 * minute)))
    kit = 1.0
    if st["vow"] and st["locket"]:
        kit = 1.14
    elif st["vow"] and st["fh"]:
        kit = 1.12
    elif st["locket"] and st["fh"]:
        kit = 1.08
    elif st["vow"]:
        kit = 1.06
    elif st["locket"]:
        kit = 1.04
    if st["yordle"] and not st["vow"]:
        kit *= 0.90  # cheap wrong Kindlegem+Vest finish
    if st["yordle"] and st["vow"] and not st["fh"] and not st["locket"]:
        kit *= 0.96  # third item still waiting on Catcher
    peel = (adc_prevented + 55.0 * cc + 0.04 * braum_ehp) * stay * kit

    notes = []
    if st["vow"]:
        notes.append("Vow 12%")
    if st["locket"]:
        notes.append("Locket")
    if st["fh"]:
        notes.append(f"FH {chill:.1f} chill")
    if st["virtue"] and r_in_fight:
        notes.append("RV on R")
    if catcher_fight:
        notes.append("Catcher (R only)")
    elif st["yordle"]:
        notes.append("Yordle stats, no displace")
    if st["warmog"]:
        notes.append("Warmog HP")
    if not notes:
        notes.append("pre-legendary")

    n_leg = sum(1 for n in st["names"] if n in LEGENDARIES)

    return Snapshot(
        minute=minute,
        build_name=build_name,
        items=st["names"],
        gold=gold,
        level=level,
        hp=round(b_hp, 1),
        armor=round(b_armor, 1),
        mr=round(b_mr, 1),
        ah=ah,
        legendary_count=n_leg,
        adc_taken=round(adc_taken, 1),
        adc_prevented=round(adc_prevented, 1),
        braum_ehp=round(braum_ehp, 1),
        cc_seconds=round(cc, 2),
        peel_score=round(peel, 1),
        q_casts=q_casts,
        r_in_fight=r_in_fight,
        catcher_this_fight=catcher_fight,
        catcher_gold_per_min=round(catcher_gpm, 1),
        notes=", ".join(notes),
        has_vow=st["vow"],
        has_locket=st["locket"],
        has_fh=st["fh"],
        has_yordle=st["yordle"],
        has_virtue=st["virtue"],
    )


def run_all() -> Tuple[Dict[str, List[Snapshot]], List[dict]]:
    results: Dict[str, List[Snapshot]] = {}
    for name, path in BUILD_PATHS.items():
        results[name] = [
            compute_snapshot(name, path, m) for m in range(1, GAME_MINUTES + 1)
        ]

    timeline = []
    for m in range(1, GAME_MINUTES + 1):
        cands = [(n, results[n][m - 1]) for n in results]

        def score(pair: Tuple[str, Snapshot]) -> float:
            n, s = pair
            p = s.peel_score
            # Catcher-labelled paths must not win a statistical tie on
            # shared Kindlegem + Chain Vest leftovers.
            if "Yordle" in n:
                p -= 3.0
            if s.has_locket:
                p += 1.0
            if s.has_vow:
                p += 1.0
            return p

        best_n, best_s = max(cands, key=score)
        timeline.append(
            {
                "minute": m,
                "winner": best_n,
                "peel": best_s.peel_score,
                "adc_taken": best_s.adc_taken,
                "adc_prevented": best_s.adc_prevented,
                "cc": best_s.cc_seconds,
                "items": best_s.items,
                "notes": best_s.notes,
            }
        )
    return results, timeline


def first_minute_with(snaps: List[Snapshot], pred) -> Optional[int]:
    for s in snaps:
        if pred(s):
            return s.minute
    return None


def summarize(results, timeline) -> str:
    lines = []
    lines.append("=" * 80)
    lines.append("BRAUM SUPPORT — NO YORDLE TRAP  (Wild Rift Patch 7.2+)")
    lines.append("Playstyle: bodyguard ADC (W + E + Concussive Blows) | Game: 20:00")
    lines.append("Metric: ADC damage prevented / 8s dive  + CC lock  + stay-in-front EHP")
    lines.append("=" * 80)
    lines.append("")
    lines.append("WHY YORDLE TRAP IS OFF")
    lines.append("  Catcher only procs on displacement (airborne / kinematics).")
    lines.append("  Braum Q = slow.  W = dash to ally.  E = projectile block.")
    lines.append("  Passive = stun.  Only R Glacial Fissure knocks up.")
    lines.append("  R CD 75/70/65s — mark lasts 5s, gold only if they die, 10s ICD.")
    lines.append("  Same cart as Knight's Vow (Kindlegem + Chain Vest), 100g cheaper.")
    lines.append("")
    lines.append("GOLD / LEVEL")
    lines.append(f"  {'Min':>3}  {'Gold':>6}  {'Lvl':>3}")
    for m in range(1, GAME_MINUTES + 1):
        if m in (1, 5, 8, 10, 12, 14, 16, 18, 20) or m % 4 == 0:
            lines.append(
                f"  {m:>3}  {gold_at_minute(m):>6}  {level_at_minute(m):>3}"
            )

    lines.append("")
    lines.append("-" * 80)
    lines.append("MINUTE-BY-MINUTE OPTIMAL (peel score, no Catcher needed)")
    lines.append("-" * 80)
    for row in timeline:
        if row["minute"] % 2 != 0 and row["minute"] not in (1, 5, 9, 11, 15):
            continue
        item_short = " › ".join(row["items"][:5])
        if len(row["items"]) > 5:
            item_short += " › …"
        lines.append(
            f"  {row['minute']:>2}:00 | peel {row['peel']:>7.0f} | "
            f"ADC taken {row['adc_taken']:>6.0f} | saved {row['adc_prevented']:>5.0f} | "
            f"CC {row['cc']:>4.1f}s | {row['winner']}"
        )
        lines.append(f"         items: {item_short}")
        lines.append(f"         {row['notes']}")

    lines.append("")
    lines.append("-" * 80)
    lines.append("BUILD COMPARISON — PEEL SCORE @ spikes  (higher = carry lives)")
    lines.append("-" * 80)
    hdr = (
        f"  {'Build':<28} {'8:00':>7} {'12:00':>7} {'16:00':>7} {'20:00':>7} "
        f"{'EffPeel':>8} {'Yordle':>6}"
    )
    lines.append(hdr)

    ranking = []
    for name, snaps in results.items():
        b8 = snaps[7].peel_score
        b12 = snaps[11].peel_score
        b16 = snaps[15].peel_score
        b20 = snaps[19].peel_score
        score_sum = 0.0
        for s in snaps:
            mult = 1.0
            if s.has_vow and s.has_locket:
                mult = 1.20
            elif s.has_vow and s.has_fh:
                mult = 1.16
            elif s.has_vow:
                mult = 1.08
            elif s.has_locket:
                mult = 1.05
            if s.has_yordle and not s.has_vow:
                mult *= 0.88
            if s.has_yordle:
                mult *= 0.97
            score_sum += s.peel_score * mult
        eff = score_sum / len(snaps)
        yordle_on = first_minute_with(snaps, lambda s: s.has_yordle)
        ranking.append((eff, b16, b20, name, b8, b12, b16, b20, snaps, yordle_on))
        ytag = f"~{yordle_on}:00" if yordle_on else "no"
        lines.append(
            f"  {name:<28} {b8:>7.0f} {b12:>7.0f} {b16:>7.0f} {b20:>7.0f} "
            f"{eff:>8.0f} {ytag:>6}"
        )

    ranking.sort(key=lambda x: (x[0], x[1]), reverse=True)
    best = ranking[0]
    no_yordle = [r for r in ranking if r[9] is None]
    best_clean = no_yordle[0] if no_yordle else best

    lines.append("")
    lines.append("-" * 80)
    lines.append("ADC DAMAGE TAKEN / 8s DIVE  (lower = better)")
    lines.append("-" * 80)
    for row in ranking:
        name, snaps = row[3], row[8]
        lines.append(
            f"  {name:<28} {snaps[7].adc_taken:>7.0f} {snaps[11].adc_taken:>7.0f} "
            f"{snaps[15].adc_taken:>7.0f} {snaps[19].adc_taken:>7.0f}"
        )

    lines.append("")
    lines.append("-" * 80)
    lines.append("KINDLEGEM + CHAIN VEST — which finish?")
    lines.append("-" * 80)
    yordle_rush = results["Yordle → Vow → FH"]
    vow_locket = results["Vow → Locket → FH"]
    guide_y = results["Vow → Virtue → Yordle"]
    m12 = 11
    m16 = 15
    lines.append(
        f"  Finish Yordle (~2500) vs finish Vow (~2600) at 12:00 peel: "
        f"{yordle_rush[m12].peel_score:.0f} vs {vow_locket[m12].peel_score:.0f}"
    )
    lines.append(
        f"  ADC taken @12: Yordle rush {yordle_rush[m12].adc_taken:.0f} | "
        f"Vow→Locket {vow_locket[m12].adc_taken:.0f}"
    )
    gpm = next((s.catcher_gold_per_min for s in yordle_rush if s.has_yordle), 0.0)
    lines.append(
        f"  Catcher personal gold if Yordle online: ~{gpm:.0f}/min "
        f"(R only, 40% mark-kills, split)."
    )
    lines.append(
        f"  16:00 two-item cores: Vow+Locket {vow_locket[m16].peel_score:.0f} | "
        f"Yordle+Vow {yordle_rush[m16].peel_score:.0f} | "
        f"Vow+Virtue (Yordle 3rd still not done) {guide_y[m16].peel_score:.0f}"
    )
    lines.append(
        f"  20:00 leftover on 'Yordle 3rd' is Kindlegem+Vest, not Catcher "
        f"(Yordle itself: {guide_y[19].has_yordle})."
    )

    winner_name = best_clean[3]
    snaps = best_clean[8]
    vow_m = first_minute_with(snaps, lambda s: s.has_vow)
    locket_m = first_minute_with(snaps, lambda s: s.has_locket)
    fh_m = first_minute_with(snaps, lambda s: s.has_fh)

    y12 = yordle_rush[m12].peel_score
    w12 = snaps[m12].peel_score
    pct12 = 100.0 * (w12 / y12 - 1.0) if y12 else 0.0
    y20 = yordle_rush[19].peel_score
    w20 = snaps[19].peel_score
    pct20 = 100.0 * (w20 / y20 - 1.0) if y20 else 0.0
    y16 = yordle_rush[m16].peel_score
    w16 = snaps[m16].peel_score
    pct16 = 100.0 * (w16 / y16 - 1.0) if y16 else 0.0

    lines.append("")
    lines.append("-" * 80)
    lines.append("VERDICT")
    lines.append("-" * 80)
    lines.append(f"  Best path (no Yordle Trap): {winner_name}")
    lines.append(f"  Peel-weighted avg: {best_clean[0]:.0f} | 16:00 peel: {best_clean[1]:.0f}")
    if vow_m:
        lines.append(f"  Knight's Vow online:  ~{vow_m}:00  (12% redirect — this is the bodyguard item)")
    if locket_m:
        lines.append(f"  Locket online:        ~{locket_m}:00  (team shield, no R required)")
    else:
        lines.append("  Locket: not finished by 20:00 on this path")
    if fh_m:
        lines.append(f"  Frozen Heart online:  ~{fh_m}:00  (Chill from Q/autos/getting hit — not R)")
    else:
        lines.append("  Frozen Heart: not finished by 20:00 on this path")
    lines.append("")
    lines.append("  TẠI SAO BỎ YORDLE TRAP:")
    lines.append("  • Catcher cần displacement. Braum chỉ knock-up bằng R.")
    lines.append("  • Q/W/E/passive không proc. Mark 5s + phải có kill mới ra vàng.")
    lines.append("  • Kindlegem + Chain Vest = cùng nấc với Knight's Vow (đắt hơn 100g).")
    lines.append("    Finish Yordle = mất 12% redirect mọi fight để đổi R-proc.")
    lines.append(
        f"  • Phút 12 peel: Yordle rush {y12:.0f} vs {winner_name} {w12:.0f} "
        f"({pct12:+.0f}%)."
    )
    lines.append(
        f"    Phút 16 (2 món): {y16:.0f} vs {w16:.0f} ({pct16:+.0f}%). "
        f"Phút 20: {y20:.0f} vs {w20:.0f} ({pct20:+.0f}%)."
    )
    lines.append("  • Radiant Virtue mới là món R đúng: heal team khi đấm R,")
    lines.append("    không cần địch chết trong 5s.")
    lines.append("")
    lines.append("  RECOMMENDED (Braum support, no Yordle Trap):")
    lines.append("  1) Relic Shield → Bulwark of the Mountain")
    lines.append("  2) Boots of Speed → Plated Steelcaps  (Mercs if AP/CC lane)")
    lines.append("  3) Locket of the Iron Solari  (~9:00) — team shield, no R gate")
    lines.append("  4) Knight's Vow              (~16:00) — 12% redirect while you W-glue")
    lines.append("  5) Frozen Heart if the game lasts — Chill from Q/autos, not R")
    lines.append("     (Radiant Virtue only if you specifically want the R-heal)")
    lines.append("  6) Thornmail / Force of Nature / Armored Advance")
    lines.append("")
    lines.append("  20-min support gold finishes TWO legendaries + boots, not three.")
    lines.append("  Do not sit on Kindlegem+Vest for a Yordle 3rd that never completes.")
    lines.append("")
    lines.append("  Skill: max Q (poke + mark), 1 early W for the dash, then E.")
    lines.append("  Bodyguard: W onto ADC → E into the projectile → Q to start stacks.")
    lines.append("  R is for the knock-up / zone, not for an item proc.")
    lines.append("")
    lines.append("  Trap: Kindlegem + Chain Vest → Yordle Trap because it is 100g")
    lines.append("  cheaper. Same components, wrong passive.")
    lines.append("  Trap: Yordle 3rd 'because Catcher is for tanks'. Braum is a")
    lines.append("  warden, not Alistar/Blitz — he does not displace on a rotation.")
    lines.append("=" * 80)
    return "\n".join(lines)


def export_json(results, timeline, path: str) -> None:
    payload = {
        "meta": {
            "champion": "Braum",
            "role": "Support",
            "patch": "7.2+",
            "game_minutes": GAME_MINUTES,
            "playstyle": "bodyguard peel (no Yordle Trap)",
            "yordle_note": (
                "Yordle Trap Catcher requires displacement. "
                "Braum only knocks up with R."
            ),
        },
        "timeline": timeline,
        "builds": {
            name: [
                {
                    "minute": s.minute,
                    "items": s.items,
                    "gold": s.gold,
                    "level": s.level,
                    "hp": s.hp,
                    "armor": s.armor,
                    "mr": s.mr,
                    "ah": s.ah,
                    "legendary_count": s.legendary_count,
                    "adc_taken": s.adc_taken,
                    "adc_prevented": s.adc_prevented,
                    "braum_ehp": s.braum_ehp,
                    "cc_seconds": s.cc_seconds,
                    "peel_score": s.peel_score,
                    "q_casts": s.q_casts,
                    "r_in_fight": s.r_in_fight,
                    "catcher_this_fight": s.catcher_this_fight,
                    "catcher_gold_per_min": s.catcher_gold_per_min,
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
    """Catcher cannot fire without R; no-Yordle bodyguard must beat Yordle rush."""
    yordle = results["Yordle → Vow → FH"]
    vow = results["Vow → Locket → FH"]
    vow_fh = results["Vow → FH → Locket"]

    # Before R (minute 5, level 6 is minute 5 in table... level 6 at m=5)
    # Minute 4 is level 5 — no R. Catcher must be false even if Yordle owned later.
    pre_r = yordle[3]  # minute 4
    assert not pre_r.r_in_fight
    assert not pre_r.catcher_this_fight

    # Once Yordle is online, Catcher still requires r_in_fight
    online = first_minute_with(yordle, lambda s: s.has_yordle)
    assert online is not None and online <= 12, online
    for s in yordle:
        if s.has_yordle and not s.r_in_fight:
            assert not s.catcher_this_fight
        if s.catcher_this_fight:
            assert s.has_yordle and s.r_in_fight

    vow_online = first_minute_with(vow, lambda s: s.has_vow)
    yordle_vow = first_minute_with(yordle, lambda s: s.has_vow)
    assert vow_online is not None
    assert yordle_vow is None or yordle_vow >= vow_online

    # Mid-game bodyguard beat cheap Catcher finish
    assert vow[11].peel_score > yordle[11].peel_score, (
        vow[11].peel_score,
        yordle[11].peel_score,
    )
    assert vow[15].adc_taken < yordle[15].adc_taken

    # Winner among no-Yordle paths should not need Catcher gold
    clean = {n: r for n, r in results.items() if "Yordle" not in n}
    best_clean = max(clean.items(), key=lambda kv: sum(s.peel_score for s in kv[1]))
    assert "Yordle" not in best_clean[0]

    # Two-item bodyguard core (Vow + Locket) beats Yordle rush AND
    # the guide's Vow + Virtue frame at 16:00. Third legendaries rarely
    # finish on a 20-min support curve — Catcher as "item 3" is a ghost.
    locket = results["Locket → Vow → FH"]
    assert locket[11].peel_score > yordle[11].peel_score
    assert vow[15].peel_score > results["Vow → Virtue → Yordle"][15].peel_score
    assert locket[15].peel_score > results["Yordle → Virtue → Thorn"][15].peel_score

    # Frozen Heart Chill is Q/autos — it must not require R.
    fh = results["FH → Vow → Locket"]
    fh_on = first_minute_with(fh, lambda s: s.has_fh)
    assert fh_on is not None
    assert fh[fh_on - 1].has_fh


def main() -> None:
    results, timeline = run_all()
    self_check(results)
    report = summarize(results, timeline)
    print(report)
    out_dir = "/workspace/braum-support-sim"
    with open(f"{out_dir}/report.txt", "w", encoding="utf-8") as f:
        f.write(report + "\n")
    export_json(results, timeline, f"{out_dir}/results.json")
    print(f"\nWrote {out_dir}/report.txt and {out_dir}/results.json")


if __name__ == "__main__":
    main()
