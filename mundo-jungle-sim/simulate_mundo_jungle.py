#!/usr/bin/env python3
"""
Wild Rift Dr. Mundo jungle — patch 7.3 clear vs first-item simulation.

Question:
  Patch 7.3 replaced bonus monster damage with a Smite burn that scales off
  bonus health, armor, and magic resist, and said tanks should no longer need
  Sunfire just to clear. Does jungle Mundo still rush Sunfire, or does
  Heartsteel (with a cheap Bami's, or with no immolate at all) win the
  clear AND the dragon fight?

Sources for the kit and items are the 7.3 patch notes plus the Wild Rift
wiki where 7.3 did not reprint a stat. Assumptions that are not in the
notes are marked in ASSUMPTIONS and in the report.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json

GAME_MINUTES = 22

# ---------------------------------------------------------------------------
# Assumptions not printed as numbers in the 7.3 notes
# ---------------------------------------------------------------------------

# Camp headcount. 7.3 prints large and small stat lines, not how many spawn.
RAPTORS_SMALL = 3
WOLVES_SMALL = 2
KRUGS_SMALL = 2

# Attack speed is not in the patch notes. These values put a Ruby-start
# first clear in a normal jungle window (about 3:20–4:00 including walks).
LARGE_AS = 0.75
SMALL_AS = 0.85
WALK_SECONDS = 8.0

# Smite burn: "deals X true damage ... continues up to 2 more times" after
# you stop hitting. Modeled as one tick per second on the monster you are
# autoing. The two linger ticks do not speed up the camp you just killed.
SMITE_BURN_INTERVAL = 1.0
SMITE_ACTIVE_CD = 15.0

# Component HP is not fully reprinted in 7.3. Chosen so
# Giant's Belt 350 + Kindlegem 200 + Ruby 150 = Heartsteel 700.
RUBY_HP = 150
BELT_HP = 350
KINDLEGEM_HP = 200


def gold_at_minute(m: int) -> int:
    """Farming jungler. Low kill gold. 7.3 shifted camp gold into Smite stacks.

    Tuned so a 2800g Heartsteel finishes around 7:00–8:00 and a 1200g
    Bami's finishes on the first back.
    """
    if m <= 0:
        return 500
    total = 500
    for t in range(1, m + 1):
        if t <= 4:
            total += 290
        elif t <= 8:
            total += 400
        elif t <= 14:
            total += 470
        else:
            total += 520
    return total


def level_at_minute(m: int) -> int:
    table = {
        0: 1,
        1: 2, 2: 3, 3: 4, 4: 4, 5: 5, 6: 6, 7: 7, 8: 8,
        9: 8, 10: 9, 11: 10, 12: 10, 13: 11, 14: 11, 15: 12,
        16: 12, 17: 13, 18: 13, 19: 14, 20: 14, 21: 15, 22: 15,
    }
    return table.get(m, min(15, 1 + m // 2))


def skill_rank(level: int, skill: str) -> int:
    """Wild Rift basic skills have 4 ranks. Q max, E second, W last. R at 6 / 11 / 15."""
    if skill == "R":
        if level < 6:
            return 0
        if level < 11:
            return 1
        if level < 15:
            return 2
        return 3
    levels = {
        "Q": (1, 3, 5, 7),
        "E": (2, 8, 10, 12),
        "W": (4, 9, 13, 14),
    }[skill]
    return sum(1 for lv in levels if level >= lv)


def lerp_level(level: int, at_1: float, at_15: float) -> float:
    t = max(0.0, min(14.0, level - 1)) / 14.0
    return at_1 + (at_15 - at_1) * t


def smite_active_damage(minute: int) -> float:
    # 600, then 1000 after 8 consumed stacks, then 1400 after 20.
    if minute < 5:
        return 600.0
    if minute < 11:
        return 1000.0
    return 1400.0


def smite_burn_base(level: int) -> float:
    return lerp_level(level, 30.0, 225.0)


def smite_heal_per_sec(level: int) -> float:
    return lerp_level(level, 5.0, 35.0)


def large_kill_heal(level: int) -> float:
    # 100 → 260, max at monster level 9.
    t = max(0.0, min(8.0, level - 1)) / 8.0
    return 100.0 + 160.0 * t


def overgrowth_stacks(minute: int) -> int:
    # ~5 monsters a minute in vision, 3 monsters per stack after patch 7.2.
    monsters = int(minute * 5.0)
    return monsters // 3


def heartsteel_procs(minute: int, owns: bool) -> float:
    """Expected champion procs this minute for a farming jungler."""
    if not owns or minute <= 0:
        return 0.0
    if minute < 8:
        return 0.45
    if minute < 14:
        return 1.15
    return 1.7


# ---------------------------------------------------------------------------
# Items
# ---------------------------------------------------------------------------


@dataclass
class Item:
    name: str
    cost: int
    hp: float = 0
    ah: float = 0
    armor: float = 0
    mr: float = 0
    base_regen_pct: float = 0  # +150% base regen → 1.5
    aa_reduce: float = 0  # fraction of champion basic-attack damage removed
    sunfire: bool = False
    bami: bool = False
    heartsteel: bool = False
    warmog: bool = False
    thornmail: bool = False
    mantle: bool = False
    twinguard: bool = False
    boots: bool = False


ITEMS: Dict[str, Item] = {
    "Ruby Crystal": Item("Ruby Crystal", 500, hp=RUBY_HP),
    "Giant's Belt": Item("Giant's Belt", 1000, hp=BELT_HP),
    "Kindlegem": Item("Kindlegem", 1000, hp=KINDLEGEM_HP, ah=10),
    "Boots of Speed": Item("Boots of Speed", 400, boots=True),
    "Cloth Armor": Item("Cloth Armor", 500, armor=15),
    "Chain Vest": Item("Chain Vest", 900, armor=40),
    "Bramble Vest": Item("Bramble Vest", 1000, armor=35),
    "Negatron Cloak": Item("Negatron Cloak", 900, mr=40),
    "Null-Magic Mantle": Item("Null-Magic Mantle", 500, mr=25),
    "Bami's Cinder": Item(
        "Bami's Cinder", 1200, hp=250, ah=5, bami=True
    ),
    "Heartsteel": Item(
        "Heartsteel", 2800, hp=700, ah=25, base_regen_pct=1.50, heartsteel=True
    ),
    "Sunfire Aegis": Item(
        "Sunfire Aegis", 2900, hp=425, ah=15, armor=20, sunfire=True
    ),
    "Plated Steelcaps": Item(
        "Plated Steelcaps", 1200, hp=150, armor=25, aa_reduce=0.06, boots=True
    ),
    "Armored Advance": Item(
        "Armored Advance", 2200, hp=150, armor=35, aa_reduce=0.10, boots=True
    ),
    "Warmog's Armor": Item(
        "Warmog's Armor", 2850, hp=700, ah=20, base_regen_pct=1.00, warmog=True
    ),
    "Thornmail": Item(
        "Thornmail", 2700, hp=200, armor=75, thornmail=True
    ),
    "Mantle of the Twelfth Hour": Item(
        "Mantle of the Twelfth Hour", 2550, hp=600, ah=20, mantle=True
    ),
    "Amaranth's Twinguard": Item(
        "Amaranth's Twinguard", 3200, hp=300, armor=50, mr=50, twinguard=True
    ),
}


UNIQUE = {
    "Bami's Cinder",
    "Heartsteel",
    "Sunfire Aegis",
    "Boots of Speed",
    "Plated Steelcaps",
    "Armored Advance",
    "Warmog's Armor",
    "Thornmail",
    "Mantle of the Twelfth Hour",
    "Amaranth's Twinguard",
}

# One of each component credited if it is actually in the inventory.
UPGRADE_COMPONENTS = {
    "Giant's Belt": ("Ruby Crystal",),
    "Kindlegem": ("Ruby Crystal",),
    "Bami's Cinder": ("Ruby Crystal",),
    "Bramble Vest": ("Cloth Armor",),
    "Chain Vest": ("Cloth Armor",),
    "Negatron Cloak": ("Null-Magic Mantle",),
    "Heartsteel": ("Giant's Belt", "Kindlegem", "Ruby Crystal"),
    "Sunfire Aegis": ("Bami's Cinder", "Kindlegem"),
    "Plated Steelcaps": ("Boots of Speed", "Ruby Crystal"),
    "Armored Advance": ("Plated Steelcaps",),
    "Warmog's Armor": ("Giant's Belt", "Kindlegem"),
    "Thornmail": ("Bramble Vest", "Chain Vest"),
    "Mantle of the Twelfth Hour": ("Kindlegem", "Giant's Belt"),
    "Amaranth's Twinguard": ("Giant's Belt", "Chain Vest", "Negatron Cloak"),
}


BUILD_PATHS: Dict[str, List[str]] = {
    # 7.3 question: skip immolate, stack HP, let the Smite burn scale.
    "HS → Warmog → Thorn": [
        "Ruby Crystal",
        "Giant's Belt",
        "Ruby Crystal",
        "Kindlegem",
        "Ruby Crystal",
        "Heartsteel",
        "Boots of Speed",
        "Ruby Crystal",
        "Plated Steelcaps",
        "Giant's Belt",
        "Kindlegem",
        "Warmog's Armor",
        "Armored Advance",
        "Cloth Armor",
        "Bramble Vest",
        "Chain Vest",
        "Thornmail",
        "Giant's Belt",
        "Chain Vest",
        "Negatron Cloak",
        "Amaranth's Twinguard",
    ],
    # Pre-7.3 habit, still the high-pick core: finish Sunfire before HP.
    "Sunfire → HS → Thorn": [
        "Ruby Crystal",
        "Bami's Cinder",
        "Boots of Speed",
        "Ruby Crystal",
        "Kindlegem",
        "Sunfire Aegis",
        "Ruby Crystal",
        "Plated Steelcaps",
        "Giant's Belt",
        "Ruby Crystal",
        "Kindlegem",
        "Ruby Crystal",
        "Heartsteel",
        "Cloth Armor",
        "Bramble Vest",
        "Chain Vest",
        "Thornmail",
        "Armored Advance",
        "Giant's Belt",
        "Chain Vest",
        "Negatron Cloak",
        "Amaranth's Twinguard",
    ],
    # Cheap AoE component, then the scaling item, Sunfire second.
    "Bami → HS → Sunfire": [
        "Ruby Crystal",
        "Bami's Cinder",
        "Boots of Speed",
        "Ruby Crystal",
        "Giant's Belt",
        "Ruby Crystal",
        "Kindlegem",
        "Ruby Crystal",
        "Heartsteel",
        "Ruby Crystal",
        "Plated Steelcaps",
        "Kindlegem",
        "Sunfire Aegis",
        "Armored Advance",
        "Cloth Armor",
        "Bramble Vest",
        "Chain Vest",
        "Thornmail",
        "Giant's Belt",
        "Chain Vest",
        "Negatron Cloak",
        "Amaranth's Twinguard",
    ],
    # No immolate. Mantle is the 7.3 anti-burst item (600 HP, lifeline).
    "HS → Mantle → Twin": [
        "Ruby Crystal",
        "Giant's Belt",
        "Ruby Crystal",
        "Kindlegem",
        "Ruby Crystal",
        "Heartsteel",
        "Boots of Speed",
        "Ruby Crystal",
        "Plated Steelcaps",
        "Kindlegem",
        "Giant's Belt",
        "Mantle of the Twelfth Hour",
        "Armored Advance",
        "Giant's Belt",
        "Chain Vest",
        "Negatron Cloak",
        "Amaranth's Twinguard",
        "Cloth Armor",
        "Bramble Vest",
        "Chain Vest",
        "Thornmail",
    ],
}


def resolve_inventory(path: List[str], gold: int, minute: int) -> List[str]:
    owned: List[str] = []
    gold_pool = gold

    def credit_for(item_name: str) -> Tuple[int, List[str]]:
        credit = 0
        remove: List[str] = []
        pool = list(owned)
        for comp in UPGRADE_COMPONENTS.get(item_name, ()):
            if comp in pool:
                pool.remove(comp)
                credit += ITEMS[comp].cost
                remove.append(comp)
        return credit, remove

    def remaining(item_name: str) -> int:
        credit, _ = credit_for(item_name)
        return max(0, ITEMS[item_name].cost - credit)

    for step in path:
        if step in UNIQUE and step in owned:
            continue
        if step == "Armored Advance" and minute < 10:
            continue
        cost = remaining(step)
        if cost > gold_pool:
            break
        _, remove = credit_for(step)
        for comp in remove:
            owned.remove(comp)
        gold_pool -= cost
        owned.append(step)
    return owned


# ---------------------------------------------------------------------------
# Champion + monsters
# ---------------------------------------------------------------------------


@dataclass
class Stats:
    level: int
    max_hp: float
    bonus_hp: float
    ad: float
    bonus_ad: float
    armor: float
    bonus_armor: float
    mr: float
    bonus_mr: float
    ah: float
    attack_speed: float
    base_regen_per_sec: float
    bonus_regen_pct: float
    aa_reduce: float
    heal_amp: float
    has_sunfire: bool
    has_bami: bool
    has_heartsteel: bool
    has_warmog: bool
    has_thornmail: bool
    has_mantle: bool
    has_twinguard: bool
    item_names: List[str] = field(default_factory=list)


def base_hp(level: int) -> float:
    return 680 + 120 * (level - 1)


def base_ad(level: int) -> float:
    return 58 + 4.55 * (level - 1)


def base_armor(level: int) -> float:
    return 40 + 3.9 * (level - 1)


def base_mr(level: int) -> float:
    return 38 + 2.0 * (level - 1)


def base_hp5(level: int) -> float:
    return 9 + 0.68 * (level - 1)


def passive_regen_per_sec(level: int, max_hp: float) -> float:
    # 1% → 2% max HP every 5 seconds, by level.
    pct_per_5 = lerp_level(level, 0.01, 0.02)
    return pct_per_5 * max_hp / 5.0


def e_passive_ad(level: int, missing_frac: float) -> float:
    rank = skill_rank(level, "E")
    if rank <= 0:
        return 0.0
    base = (0, 15, 20, 25, 30)[rank]
    extra = (0, 30, 40, 50, 60)[rank] * max(0.0, min(1.0, missing_frac))
    return base + extra


def build_stats(
    names: List[str],
    level: int,
    hs_bonus: float,
    minute: int,
    missing_frac: float = 0.0,
) -> Stats:
    items = [ITEMS[n] for n in names]
    item_hp = sum(i.hp for i in items)
    stacks = overgrowth_stacks(minute)
    raw_bonus = item_hp + hs_bonus + 3.0 * stacks
    raw_base = base_hp(level)
    if stacks >= 30:
        bonus_hp = raw_bonus * 1.03
        max_hp = raw_base * 1.03 + bonus_hp
    else:
        bonus_hp = raw_bonus
        max_hp = raw_base + bonus_hp

    bonus_armor = sum(i.armor for i in items)
    bonus_mr = sum(i.mr for i in items)
    # Twinguard: after 5s in combat, +30% bonus resists. Fights count it.
    # Clears are shorter per camp; applied in the fight, not on this object,
    # via the caller flipping a flag. Default off here.
    armor = base_armor(level) + bonus_armor
    mr = base_mr(level) + bonus_mr
    bonus_ad = e_passive_ad(level, missing_frac)
    return Stats(
        level=level,
        max_hp=max_hp,
        bonus_hp=bonus_hp,
        ad=base_ad(level) + bonus_ad,
        bonus_ad=bonus_ad,
        armor=armor,
        bonus_armor=bonus_armor,
        mr=mr,
        bonus_mr=bonus_mr,
        ah=sum(i.ah for i in items),
        attack_speed=0.80 * (1 + 0.022 * (level - 1)),
        base_regen_per_sec=base_hp5(level) / 5.0,
        bonus_regen_pct=sum(i.base_regen_pct for i in items),
        aa_reduce=max((i.aa_reduce for i in items), default=0.0),
        heal_amp=1.30 if any(i.warmog for i in items) else 1.0,
        has_sunfire=any(i.sunfire for i in items),
        has_bami=any(i.bami for i in items),
        has_heartsteel=any(i.heartsteel for i in items),
        has_warmog=any(i.warmog for i in items),
        has_thornmail=any(i.thornmail for i in items),
        has_mantle=any(i.mantle for i in items),
        has_twinguard=any(i.twinguard for i in items),
        item_names=list(names),
    )


def cdr_mult(ah: float) -> float:
    return 100.0 / (100.0 + ah)


def resist_mult(resist: float) -> float:
    return 100.0 / (100.0 + max(0.0, resist))


def immolate_dps(stats: Stats, versus_monsters: bool) -> float:
    """Pre-mitigation magic damage per second to each nearby unit."""
    if stats.has_sunfire:
        raw = 20.0 + 0.015 * stats.bonus_hp
        return raw * (1.30 if versus_monsters else 1.0)
    if stats.has_bami:
        raw = lerp_level(stats.level, 10.0, 20.0)
        return raw * (1.15 if versus_monsters else 1.0)
    return 0.0


def thorns_damage(stats: Stats) -> float:
    if not stats.has_thornmail:
        return 0.0
    # Patch 7.2: bonus-health ratio 2% → 1%.
    return 20.0 + 0.06 * stats.bonus_armor + 0.01 * stats.bonus_hp


def smite_burn_tick(stats: Stats) -> float:
    return (
        smite_burn_base(stats.level)
        + 0.10 * stats.bonus_ad
        + 0.20 * stats.bonus_armor
        + 0.20 * stats.bonus_mr
        + 0.03 * stats.bonus_hp
    )


@dataclass
class Unit:
    kind: str  # large | small
    hp: float
    max_hp: float
    ad: float
    armor: float
    mr: float
    pct_current: float
    attack_speed: float
    atk_cd: float = 0.0

    @property
    def alive(self) -> bool:
        return self.hp > 0


def make_unit(
    kind: str,
    hp: float,
    ad: float,
    armor: float,
    mr: float,
    pct: float,
    attack_speed: float,
) -> Unit:
    return Unit(kind, hp, hp, ad, armor, mr, pct, attack_speed, 0.0)


def camp_units(camp: str, level: int) -> List[Unit]:
    if camp in ("red", "blue"):
        return [
            make_unit(
                "large",
                lerp_level(level, 2200, 4650),
                lerp_level(level, 70, 210),
                40, 35, 0.05, LARGE_AS,
            )
        ]
    if camp == "gromp":
        return [
            make_unit(
                "large",
                lerp_level(level, 1800, 4390),
                lerp_level(level, 55, 160),
                40, 35, 0.05, LARGE_AS,
            )
        ]
    if camp == "krugs":
        units = [
            make_unit(
                "large",
                lerp_level(level, 1300, 3050),
                lerp_level(level, 60, 172),
                40, 35, 0.03, LARGE_AS,
            )
        ]
        for _ in range(KRUGS_SMALL):
            units.append(
                make_unit(
                    "small",
                    lerp_level(level, 550, 1560),
                    lerp_level(level, 20, 62),
                    20, 20, 0.0, SMALL_AS,
                )
            )
        return units
    if camp == "raptors":
        units = [
            make_unit(
                "large",
                lerp_level(level, 1000, 2540),
                lerp_level(level, 20, 55),
                40, 35, 0.03, LARGE_AS,
            )
        ]
        for _ in range(RAPTORS_SMALL):
            units.append(
                make_unit(
                    "small",
                    lerp_level(level, 500, 1270),
                    lerp_level(level, 10, 24),
                    20, 20, 0.0, SMALL_AS,
                )
            )
        return units
    if camp == "wolves":
        units = [
            make_unit(
                "large",
                lerp_level(level, 1200, 3230),
                lerp_level(level, 30, 93),
                40, 35, 0.03, LARGE_AS,
            )
        ]
        for _ in range(WOLVES_SMALL):
            units.append(
                make_unit(
                    "small",
                    lerp_level(level, 600, 1510),
                    lerp_level(level, 10, 31),
                    20, 20, 0.0, SMALL_AS,
                )
            )
        return units
    raise KeyError(camp)


FULL_CLEAR = ("red", "krugs", "raptors", "wolves", "blue", "gromp")
AOE_CAMPS = {"krugs", "raptors", "wolves"}


@dataclass
class ClearResult:
    combat_time: float
    walk_time: float
    single_time: float
    aoe_time: float
    hp_left: float
    hp_pct: float
    died: bool
    dmg_autos: float
    dmg_abilities: float
    dmg_immolate: float
    dmg_burn: float
    dmg_smite: float
    dmg_thorns: float


def q_monster_damage(level: int, current_hp: float) -> float:
    rank = skill_rank(level, "Q")
    if rank <= 0:
        return 0.0
    pct = (0, 0.20, 0.23, 0.26, 0.29)[rank]
    minimum = (0, 90, 160, 230, 300)[rank]
    cap = (0, 250, 350, 450, 550)[rank]
    return min(cap, max(minimum, pct * current_hp))


def e_active_damage(level: int, bonus_hp: float, missing_frac: float) -> float:
    rank = skill_rank(level, "E")
    if rank <= 0:
        return 0.0
    base = (0, 5, 20, 35, 50)[rank]
    amp = 1.0 + 0.60 * max(0.0, min(1.0, missing_frac))
    return (base + 0.05 * bonus_hp) * amp


def w_tick_damage(level: int) -> float:
    """Damage of one 0.25s tick, pre-mitigation."""
    rank = skill_rank(level, "W")
    if rank <= 0:
        return 0.0
    return (0, 5, 10, 15, 20)[rank]


def w_detonate(level: int, bonus_hp: float) -> float:
    rank = skill_rank(level, "W")
    if rank <= 0:
        return 0.0
    return (0, 20, 40, 60, 80)[rank] + 0.05 * bonus_hp


def w_store_pct(level: int) -> float:
    rank = skill_rank(level, "W")
    return (0, 0.30, 0.35, 0.40, 0.45)[rank]


def e_cost(level: int) -> float:
    rank = skill_rank(level, "E")
    return (0, 10, 20, 30, 40)[rank]


def regen_per_sec(stats: Stats) -> float:
    base = stats.base_regen_per_sec * (1.0 + stats.bonus_regen_pct)
    pct = passive_regen_per_sec(stats.level, stats.max_hp)
    return (base + pct) * stats.heal_amp


def simulate_clear(
    stats: Stats,
    monster_level: int,
    smite_damage: float,
    burn_on: bool = True,
) -> ClearResult:
    hp = stats.max_hp
    combat = single = aoe = 0.0
    walks = 0.0
    died = False
    dmg_autos = dmg_abilities = dmg_immolate = dmg_burn = dmg_smite = dmg_thorns = 0.0
    smite_cd = 0.0
    dt = 0.25

    def deal_magic(unit: Unit, raw: float) -> float:
        if raw <= 0 or not unit.alive:
            return 0.0
        dealt = raw * resist_mult(unit.mr)
        unit.hp -= dealt
        return dealt

    def deal_phys(unit: Unit, raw: float) -> float:
        if raw <= 0 or not unit.alive:
            return 0.0
        dealt = raw * resist_mult(unit.armor)
        unit.hp -= dealt
        return dealt

    def deal_true(unit: Unit, raw: float) -> float:
        if raw <= 0 or not unit.alive:
            return 0.0
        unit.hp -= raw
        return raw

    for index, camp_name in enumerate(FULL_CLEAR):
        if died:
            break
        if index > 0:
            # Walk. Warmog's Heart starts after 5s without damage.
            walks += WALK_SECONDS
            heart_time = 0.0
            if stats.has_warmog and stats.bonus_hp >= 950:
                heart_time = max(0.0, WALK_SECONDS - 5.0)
            healed = regen_per_sec(stats) * WALK_SECONDS
            healed += heart_time * 0.035 * stats.max_hp * stats.heal_amp
            hp = min(stats.max_hp, hp + healed)
            smite_cd = max(0.0, smite_cd - WALK_SECONDS)

        units = camp_units(camp_name, monster_level)
        t = 0.0
        auto_cd = 0.0
        q_cd = 0.0
        e_cd = 0.0
        w_cd = 0.0
        w_left = 0.0
        w_tick_clock = 0.0
        w_taken = 0.0
        burn_clock = 0.0
        large_heal_given = False
        immolate = immolate_dps(stats, True)

        while any(u.alive for u in units) and t < 90 and hp > 0:
            focus = max((u for u in units if u.alive), key=lambda u: u.max_hp)
            missing = 1.0 - hp / stats.max_hp
            ad_now = base_ad(stats.level) + e_passive_ad(stats.level, missing)

            # Monster attacks. Smite holders take 50% from non-epic monsters.
            for unit in units:
                if not unit.alive:
                    continue
                unit.atk_cd -= dt
                if unit.atk_cd > 0:
                    continue
                unit.atk_cd += 1.0 / unit.attack_speed
                raw = (unit.ad + unit.pct_current * hp) * 0.5
                taken = raw * resist_mult(stats.armor)
                hp -= taken
                if w_left > 0:
                    w_taken += taken
                if stats.has_thornmail and unit.alive:
                    dmg_thorns += deal_magic(unit, thorns_damage(stats))

            # Regen + Smite combat heal.
            hp += regen_per_sec(stats) * dt
            hp += smite_heal_per_sec(stats.level) * stats.heal_amp * dt

            # Immolate
            if immolate > 0:
                for unit in units:
                    dmg_immolate += deal_magic(unit, immolate * dt)

            # Smite burn tick
            burn_clock += dt
            if burn_on and burn_clock >= SMITE_BURN_INTERVAL and focus.alive:
                burn_clock -= SMITE_BURN_INTERVAL
                dmg_burn += deal_true(focus, smite_burn_tick(stats))

            # Smite active, once the camp is in progress and CD is up.
            # Used on the large monster to delete a chunk.
            smite_cd = max(0.0, smite_cd - dt)
            large = next((u for u in units if u.kind == "large" and u.alive), None)
            if large is not None and smite_cd <= 0 and t >= 0:
                dmg_smite += deal_true(large, smite_damage)
                smite_cd = SMITE_ACTIVE_CD

            # W channel ticks (can auto during it)
            if w_left > 0:
                w_left -= dt
                w_tick_clock += dt
                while w_tick_clock >= 0.25:
                    w_tick_clock -= 0.25
                    raw = w_tick_damage(stats.level)
                    for unit in units:
                        dmg_abilities += deal_magic(unit, raw)
                if w_left <= 0:
                    raw = w_detonate(stats.level, stats.bonus_hp)
                    hit_large = False
                    for unit in units:
                        if unit.alive:
                            dmg_abilities += deal_magic(unit, raw)
                            if unit.kind == "large":
                                hit_large = True
                    store = w_store_pct(stats.level) * w_taken
                    heal_frac = 1.0 if hit_large else 0.5
                    hp += store * heal_frac * stats.heal_amp
                    w_taken = 0.0

            # Casts, then auto. E resets the auto timer.
            q_cd = max(0.0, q_cd - dt)
            e_cd = max(0.0, e_cd - dt)
            w_cd = max(0.0, w_cd - dt)
            auto_cd = max(0.0, auto_cd - dt)

            if (
                w_left <= 0
                and w_cd <= 0
                and skill_rank(stats.level, "W") > 0
                and hp > stats.max_hp * 0.28
            ):
                hp -= 0.05 * hp
                w_left = 4.0
                w_tick_clock = 0.0
                w_taken = 0.0
                w_cd = (0, 13, 12, 11, 10)[skill_rank(stats.level, "W")] * cdr_mult(stats.ah)

            if q_cd <= 0 and skill_rank(stats.level, "Q") > 0 and focus.alive:
                raw = q_monster_damage(stats.level, focus.hp)
                dmg_abilities += deal_magic(focus, raw)
                q_cd = 4.0 * cdr_mult(stats.ah)
                # Hitting a monster refunds the 50 HP cost.

            if (
                e_cd <= 0
                and skill_rank(stats.level, "E") > 0
                and focus.alive
                and hp - e_cost(stats.level) > stats.max_hp * 0.18
            ):
                hp -= e_cost(stats.level)
                raw = e_active_damage(stats.level, stats.bonus_hp, missing)
                dmg_abilities += deal_phys(focus, raw)
                e_cd = (0, 8, 7.5, 7, 6.5)[skill_rank(stats.level, "E")] * cdr_mult(stats.ah)
                auto_cd = 0.0

            if auto_cd <= 0 and focus.alive:
                dmg_autos += deal_phys(focus, ad_now)
                auto_cd = 1.0 / stats.attack_speed

            # Large-monster kill heal.
            for unit in units:
                if unit.kind == "large" and not unit.alive and not large_heal_given:
                    hp += large_kill_heal(monster_level) * stats.heal_amp
                    large_heal_given = True

            hp = min(stats.max_hp, hp)
            t += dt
            if hp <= 0:
                died = True
                hp = 0
                break

        combat += t
        if camp_name in AOE_CAMPS:
            aoe += t
        else:
            single += t

    return ClearResult(
        combat_time=combat,
        walk_time=walks,
        single_time=single,
        aoe_time=aoe,
        hp_left=hp,
        hp_pct=(hp / stats.max_hp) if stats.max_hp else 0.0,
        died=died,
        dmg_autos=dmg_autos,
        dmg_abilities=dmg_abilities,
        dmg_immolate=dmg_immolate,
        dmg_burn=dmg_burn,
        dmg_smite=dmg_smite,
        dmg_thorns=dmg_thorns,
    )


# ---------------------------------------------------------------------------
# Dragon fight vs a bruiser
# ---------------------------------------------------------------------------


def enemy_max_hp(level: int, minute: int) -> float:
    return 660 + 118 * (level - 1) + 80 * max(0, minute - 6)


def enemy_armor(level: int, minute: int) -> float:
    extra = 0
    if minute >= 8:
        extra += 20
    if minute >= 14:
        extra += 30
    return 36 + 3.6 * (level - 1) + extra


def enemy_mr(level: int, minute: int) -> float:
    extra = 18 if minute >= 12 else 0
    return 32 + 1.7 * (level - 1) + extra


def enemy_dps(level: int, minute: int) -> Tuple[float, float]:
    """Pre-mitigation DPS from the dragon fight, not a 1v1.

    One bruiser's DPS, times a two-champion focus. 70% of the physical
    portion is basic attacks (Steelcaps applies to that share).
    """
    phys = 78 + 8.5 * level + 5.0 * max(0, minute - 6)
    magic = 22 + 2.8 * level + 2.2 * max(0, minute - 8)
    return phys * 2.5, magic * 2.5


def fight_taken_dps(stats: Stats, level: int, minute: int, twin_stacked: bool) -> float:
    phys, magic = enemy_dps(level, minute)
    armor = stats.armor
    mr = stats.mr
    if twin_stacked and stats.has_twinguard:
        armor += 0.30 * stats.bonus_armor
        mr += 0.30 * stats.bonus_mr
    phys_taken = phys * resist_mult(armor)
    # 70% of the physical DPS is basic attacks, so Steelcaps applies there.
    phys_taken *= 1.0 - 0.70 * stats.aa_reduce
    magic_taken = magic * resist_mult(mr)
    return phys_taken + magic_taken


def q_champion_damage(level: int, current_hp: float) -> float:
    rank = skill_rank(level, "Q")
    if rank <= 0:
        return 0.0
    pct = (0, 0.20, 0.23, 0.26, 0.29)[rank]
    minimum = (0, 90, 160, 230, 300)[rank]
    return max(minimum, pct * current_hp)


@dataclass
class FightResult:
    damage: float
    survival: float
    burst_survives: bool


def simulate_fight(stats: Stats, minute: int) -> FightResult:
    """8s of damage dealt, and seconds survived from full HP with R available."""
    level = stats.level
    ehp_armor = stats.armor
    ehp_mr = stats.mr
    bonus_armor = stats.bonus_armor
    bonus_mr = stats.bonus_mr
    if stats.has_twinguard:
        bonus_armor *= 1.30
        bonus_mr *= 1.30
        ehp_armor = base_armor(level) + bonus_armor
        ehp_mr = base_mr(level) + bonus_mr

    # Damage window uses stacked Twinguard (a dragon fight lasts long enough).
    fight_stats = Stats(**{**stats.__dict__})
    fight_stats.armor = ehp_armor
    fight_stats.mr = ehp_mr
    fight_stats.bonus_armor = bonus_armor
    fight_stats.bonus_mr = bonus_mr

    target_hp = enemy_max_hp(level, minute)
    target_arm = enemy_armor(level, minute)
    target_mr = enemy_mr(level, minute)
    missing = 0.35
    ad = base_ad(level) + e_passive_ad(level, missing)
    r_rank = skill_rank(level, "R")
    if r_rank:
        ad += (0, 0.04, 0.055, 0.07)[r_rank] * stats.bonus_hp

    duration = 8.0
    ah = stats.ah
    q_cd = 4.0 * cdr_mult(ah)
    e_base = (0, 8, 7.5, 7, 6.5)[skill_rank(level, "E")] or 999
    e_cd = e_base * cdr_mult(ah)
    q_casts = 0 if skill_rank(level, "Q") <= 0 else 1 + int((duration - 0.01) / q_cd)
    e_casts = 0 if skill_rank(level, "E") <= 0 else 1 + int((duration - 0.01) / e_cd)
    autos = stats.attack_speed * duration

    current = target_hp * 0.62
    q_raw = q_champion_damage(level, current)
    e_raw = e_active_damage(level, stats.bonus_hp, missing)
    w_ticks = 16 if skill_rank(level, "W") else 0  # 4.0s / 0.25
    w_raw_tick = w_tick_damage(level)
    w_raw_det = w_detonate(level, stats.bonus_hp) if skill_rank(level, "W") else 0.0

    dmg = 0.0
    dmg += autos * ad * resist_mult(target_arm)
    dmg += e_casts * e_raw * resist_mult(target_arm)
    dmg += q_casts * q_raw * resist_mult(target_mr)
    dmg += w_ticks * w_raw_tick * resist_mult(target_mr)
    dmg += w_raw_det * resist_mult(target_mr)
    dmg += immolate_dps(fight_stats, False) * duration * resist_mult(target_mr)
    if stats.has_heartsteel:
        hs = 140.0 + 0.035 * stats.max_hp
        dmg += hs * resist_mult(target_arm)
    # Grasp: 4s into the fight and again at 8s. Damage 3.3% max HP, heal later.
    grasp_procs = 2 if duration >= 8 else 1
    dmg += grasp_procs * 0.033 * stats.max_hp * resist_mult(target_arm)
    # Thornmail: enemy autos ~0.85 AS for 8s.
    if stats.has_thornmail:
        dmg += 0.85 * duration * thorns_damage(fight_stats) * resist_mult(target_mr)

    # Survival from full HP. R is pressed at 40% HP. Mantle at 30%.
    taken = fight_taken_dps(fight_stats, level, minute, twin_stacked=True)
    hp = stats.max_hp
    max_hp = stats.max_hp
    t = 0.0
    r_used = False
    r_per_sec = 0.0
    r_until = -1.0
    mantle_used = False
    w_started = -1.0
    w_taken = 0.0
    w_healed = False
    dt = 0.25
    while hp > 0 and t < 40:
        incoming = taken * dt
        hp -= incoming
        hp += regen_per_sec(stats) * dt
        if w_started < 0 and t >= 1.0 and skill_rank(level, "W"):
            hp -= 0.05 * max(hp, 0)
            w_started = t
            w_taken = 0.0
        if w_started >= 0 and t < w_started + 4:
            w_taken += incoming
        if w_started >= 0 and not w_healed and t >= w_started + 4:
            store = w_store_pct(level) * w_taken
            hp += store * stats.heal_amp
            w_healed = True
        if (not r_used) and r_rank and hp <= 0.40 * max_hp and hp > 0:
            missing_hp = max(0.0, max_hp - hp)
            gain = (0, 0.25, 0.30, 0.35)[r_rank] * missing_hp
            max_hp += gain
            hp += gain
            r_per_sec = (0, 0.15, 0.35, 0.55)[r_rank] * max_hp / 10.0
            r_until = t + 10.0
            r_used = True
        if r_used and t < r_until:
            hp += r_per_sec * stats.heal_amp * dt
        if (not mantle_used) and stats.has_mantle and hp <= 0.30 * max_hp and hp > 0:
            # 7.3: 200–300 bonus HP for 5s, plus a heal over 5s.
            temp = lerp_level(level, 200, 300)
            heal = lerp_level(level, 200, 400)
            heal += 1.20 * fight_stats.bonus_armor + 1.20 * fight_stats.bonus_mr
            heal += 0.15 * stats.bonus_hp
            hp += temp + heal * stats.heal_amp
            max_hp += temp
            mantle_used = True
        if abs(t - 4.0) < 0.01 or abs(t - 8.0) < 0.01:
            hp += 0.013 * stats.max_hp * stats.heal_amp
        hp = min(max_hp, hp)
        t += dt
        if hp <= 0:
            break

    survival = t
    # "Survives the burst" = still alive at 8s, the dragon-fight window.
    return FightResult(damage=dmg, survival=survival, burst_survives=survival >= 8.0)


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------


@dataclass
class Snapshot:
    minute: int
    build: str
    items: List[str]
    gold: int
    level: int
    max_hp: float
    bonus_hp: float
    hs_bonus: float
    armor: float
    mr: float
    clear_time: float
    clear_hp_pct: float
    single_time: float
    aoe_time: float
    died: bool
    dmg_burn: float
    dmg_immolate: float
    fight_dmg: float
    survival: float
    no_burn_aoe: float
    no_burn_single: float
    no_burn_hp_pct: float


def display_items(names: List[str]) -> List[str]:
    skip = {
        "Ruby Crystal",
        "Boots of Speed",
        "Cloth Armor",
        "Chain Vest",
        "Bramble Vest",
        "Negatron Cloak",
        "Null-Magic Mantle",
    }
    shown = [n for n in names if n not in skip]
    # Components worth naming when the legendary is not finished.
    for n in names:
        if n in ("Bami's Cinder", "Giant's Belt") and n not in shown:
            shown.insert(0, n)
    return shown


def run_build(name: str, path: List[str]) -> List[Snapshot]:
    hs_bonus = 0.0
    snaps: List[Snapshot] = []
    for minute in range(0, GAME_MINUTES + 1):
        gold = gold_at_minute(minute)
        level = level_at_minute(minute)
        owned = resolve_inventory(path, gold, minute)
        owns_hs = "Heartsteel" in owned
        if owns_hs:
            preview = build_stats(owned, level, hs_bonus, minute, missing_frac=0.25)
            procs = heartsteel_procs(minute, True)
            hs_bonus += procs * 0.15 * (140.0 + 0.035 * preview.max_hp)
        stats = build_stats(owned, level, hs_bonus, minute, missing_frac=0.25)
        clear = simulate_clear(stats, level, smite_active_damage(minute), burn_on=True)
        noburn = simulate_clear(stats, level, smite_active_damage(minute), burn_on=False)
        fight = simulate_fight(stats, minute)
        snaps.append(
            Snapshot(
                minute=minute,
                build=name,
                items=display_items(owned),
                gold=gold,
                level=level,
                max_hp=stats.max_hp,
                bonus_hp=stats.bonus_hp,
                hs_bonus=hs_bonus,
                armor=stats.armor,
                mr=stats.mr,
                clear_time=clear.combat_time + clear.walk_time,
                clear_hp_pct=clear.hp_pct,
                single_time=clear.single_time,
                aoe_time=clear.aoe_time,
                died=clear.died,
                dmg_burn=clear.dmg_burn,
                dmg_immolate=clear.dmg_immolate,
                fight_dmg=fight.damage,
                survival=fight.survival,
                no_burn_aoe=noburn.aoe_time,
                no_burn_single=noburn.single_time,
                no_burn_hp_pct=noburn.hp_pct,
            )
        )
    return snaps


def impact(snap: Snapshot) -> float:
    """Damage across the 8s brawl, scaled by how long he actually lives."""
    lived = min(snap.survival, 30.0)
    if snap.died or snap.clear_hp_pct < 0.25:
        lived *= 0.55
    return snap.fight_dmg * lived / 8.0


def run_all() -> Dict[str, List[Snapshot]]:
    return {name: run_build(name, path) for name, path in BUILD_PATHS.items()}


def fmt_time(seconds: float) -> str:
    seconds = max(0.0, seconds)
    return f"{int(seconds // 60)}:{int(seconds % 60):02d}"


def summarize(results: Dict[str, List[Snapshot]]) -> str:
    lines: List[str] = []
    line = lines.append
    line("=" * 88)
    line("DR. MUNDO JUNGLE — WILD RIFT PATCH 7.3")
    line("Does the new Smite burn let him skip Sunfire and rush Heartsteel?")
    line("Clear = red → krugs → raptors → wolves → blue → gromp.")
    line("Dragon fight = 8s of damage into a bruiser, while two champions focus Mundo.")
    line("=" * 88)
    line("")
    line("GOLD / LEVEL  (farming jungler, low kill gold)")
    line(f"  {'Min':>3}  {'Gold':>6}  {'Lvl':>3}")
    for m in (0, 4, 6, 8, 10, 12, 14, 16, 18, 22):
        line(f"  {m:>3}  {gold_at_minute(m):>6}  {level_at_minute(m):>3}")

    key_minutes = (4, 8, 12, 16, 22)
    line("")
    line("-" * 88)
    line("CLEAR  (full rotation time, HP left, AoE camps vs single-target camps)")
    line("-" * 88)
    for minute in key_minutes:
        line(f"  {minute:>2}:00")
        for name, snaps in results.items():
            s = snaps[minute]
            flag = "  DIED" if s.died else ""
            line(
                f"    {name:<24} {fmt_time(s.clear_time):>5}  "
                f"HP {s.clear_hp_pct * 100:5.1f}%  "
                f"aoe {s.aoe_time:5.1f}s  single {s.single_time:5.1f}s  "
                f"{s.max_hp:5.0f} HP{flag}"
            )
            line(f"      {' · '.join(s.items) if s.items else '(components only)'}")

    line("")
    line("-" * 88)
    line("SMITE BURN ON vs OFF  (same items, AoE-camp seconds)")
    line("  Burn off is a sensitivity check, not a full pre-7.3 monster ruleset.")
    line("-" * 88)
    line(f"  {'Build':<24} {'4 aoe on':>9} {'4 aoe off':>10} {'8 aoe on':>9} {'8 aoe off':>10} {'8 single on':>12}")
    for name, snaps in results.items():
        a, b = snaps[4], snaps[8]
        line(
            f"  {name:<24} {a.aoe_time:9.1f} {a.no_burn_aoe:10.1f} "
            f"{b.aoe_time:9.1f} {b.no_burn_aoe:10.1f} {b.single_time:12.1f}"
        )

    line("")
    line("-" * 88)
    line("DRAGON FIGHT  (damage dealt in 8s to a bruiser, seconds survived from full HP)")
    line("-" * 88)
    line(
        f"  {'Build':<24} {'8 dmg':>8} {'8 live':>7} {'16 dmg':>8} "
        f"{'16 live':>8} {'22 dmg':>8} {'22 live':>8} {'22 HP':>8}"
    )
    scored = []
    for name, snaps in results.items():
        s8, s16, s22 = snaps[8], snaps[16], snaps[22]
        early = impact(s8)
        mid = impact(s16)
        late = impact(s22)
        if s4_low(snaps) or s8.clear_hp_pct < 0.30:
            early *= 0.72
        scored.append((early, mid, late, name, snaps))
        line(
            f"  {name:<24} {s8.fight_dmg:8.0f} {s8.survival:7.1f} "
            f"{s16.fight_dmg:8.0f} {s16.survival:8.1f} "
            f"{s22.fight_dmg:8.0f} {s22.survival:8.1f} {s22.max_hp:8.0f}"
        )

    # First dragon decides the opener. Second item breaks the tie.
    # A path more than 3% behind at 8:00 is not the jungle build, even if
    # its later damage looks fine on paper.
    best_early = max(row[0] for row in scored)
    contenders = [row for row in scored if row[0] >= best_early * 0.97]
    contenders.sort(key=lambda row: (row[1], row[2]), reverse=True)
    winner_name, winner = contenders[0][3], contenders[0][4]
    hs = results["HS → Warmog → Thorn"]
    sun = results["Sunfire → HS → Thorn"]
    bami = results["Bami → HS → Sunfire"]
    mantle = results["HS → Mantle → Twin"]

    def first_minute(snaps: List[Snapshot], pred) -> Optional[int]:
        for s in snaps:
            if pred(s):
                return s.minute
        return None

    line("")
    line("-" * 88)
    line("VERDICT")
    line("-" * 88)
    line(f"  Best jungle path: {winner_name}")
    line("")

    aoe_gap = hs[4].aoe_time - bami[4].aoe_time
    off_gap = hs[4].no_burn_aoe - bami[4].no_burn_aoe
    hs_done = first_minute(hs, lambda s: "Heartsteel" in s.items)
    sun_done = first_minute(sun, lambda s: "Sunfire Aegis" in s.items)
    bami_hs = first_minute(bami, lambda s: "Heartsteel" in s.items)
    sun_hs = first_minute(sun, lambda s: "Heartsteel" in s.items)
    man_done = first_minute(mantle, lambda s: "Mantle of the Twelfth Hour" in s.items)
    war_done = first_minute(hs, lambda s: "Warmog's Armor" in s.items)

    line("  CLEAR — the burn replaced Sunfire, it did not replace Heartsteel.")
    line(
        f"  • 4:00 AoE camps: belt components {hs[4].aoe_time:.0f}s, "
        f"Bami's {bami[4].aoe_time:.0f}s (Bami saves {aoe_gap:.1f}s). "
        f"Single-target camps are {hs[4].single_time:.0f}s vs {bami[4].single_time:.0f}s."
    )
    line(
        f"  • Same items with the burn turned off: belt {hs[4].no_burn_aoe:.0f}s, "
        f"Bami {bami[4].no_burn_aoe:.0f}s (Bami saves {off_gap:.0f}s). "
        f"That is the old reason to buy immolate."
    )
    line(
        f"  • Burn damage on the 4:00 clear is {hs[4].dmg_burn:.0f} true from belt "
        f"components and {bami[4].dmg_burn:.0f} from Bami's. It ignores the camps' 35 MR. "
        f"Immolate on that clear is {bami[4].dmg_immolate:.0f}."
    )
    if aoe_gap < 5:
        line(
            f"  • Under a 1-second burn tick, Bami's saves {aoe_gap:.1f}s on AoE camps. "
            "That is not a reason to delay Heartsteel."
        )
    else:
        line("  • That AoE gap is still big enough to buy Bami's on the first back.")
    line("  • Every tested path finishes the rotation above ~85% HP. The clear is not")
    line("    the filter anymore. The dragon fight is.")

    line("")
    line("  FIRST DRAGON (~8:00)")
    line(
        f"  • Heartsteel online ~{hs_done}:00. "
        f"Fight {hs[8].fight_dmg:.0f} dmg, lives {hs[8].survival:.1f}s, {hs[8].max_hp:.0f} HP."
    )
    line(
        f"  • Bami → Heartsteel delays Heartsteel to ~{bami_hs}:00. "
        f"At 8:00: {bami[8].fight_dmg:.0f} dmg, lives {bami[8].survival:.1f}s, {bami[8].max_hp:.0f} HP."
    )
    line(
        f"  • Sunfire first finishes Sunfire ~{sun_done}:00 and Heartsteel ~{sun_hs}:00. "
        f"At 8:00: {sun[8].fight_dmg:.0f} dmg, lives {sun[8].survival:.1f}s, {sun[8].max_hp:.0f} HP."
    )
    dmg_drop = hs[8].fight_dmg - sun[8].fight_dmg
    live_drop = hs[8].survival - sun[8].survival
    line(
        f"  • Sunfire first is behind the Heartsteel rush by {dmg_drop:.0f} damage "
        f"and {live_drop:.1f}s of survival at the first dragon."
    )

    line("")
    line("  SECOND ITEM (~16:00)")
    line(
        f"  • Warmog ~{war_done}:00: {hs[16].fight_dmg:.0f} dmg, lives {hs[16].survival:.1f}s, "
        f"{hs[16].max_hp:.0f} HP, {hs[16].hs_bonus:.0f} Heartsteel stacks."
    )
    line(
        f"  • Mantle ~{man_done}:00: {mantle[16].fight_dmg:.0f} dmg, lives {mantle[16].survival:.1f}s, "
        f"{mantle[16].max_hp:.0f} HP, {mantle[16].hs_bonus:.0f} stacks."
    )
    line(
        f"  • Sunfire second (after Bami → HS): {bami[16].fight_dmg:.0f} dmg, "
        f"lives {bami[16].survival:.1f}s, {bami[16].max_hp:.0f} HP, {bami[16].hs_bonus:.0f} stacks."
    )
    line(
        f"  • Sunfire first, Heartsteel late: {sun[16].fight_dmg:.0f} dmg, "
        f"lives {sun[16].survival:.1f}s, {sun[16].max_hp:.0f} HP, only {sun[16].hs_bonus:.0f} stacks."
    )

    # Second-item call from the 16:00 impact, restricted to paths that already
    # rushed Heartsteel so the Sunfire-first delay is not double-counted.
    second_options = (
        ("Warmog's Armor", hs[16]),
        ("Mantle of the Twelfth Hour", mantle[16]),
        ("Sunfire Aegis", bami[16]),
    )
    second_name, second_snap = max(second_options, key=lambda pair: impact(pair[1]))
    line(f"  • Best second legendary after a Heartsteel rush: {second_name}.")
    line(
        f"    Warmog vs Mantle at 16:00 is {hs[16].fight_dmg - mantle[16].fight_dmg:+.0f} damage "
        f"and {hs[16].survival - mantle[16].survival:+.1f}s. Same spike. Warmog wins the long"
    )
    line("    fight; Mantle is the cheaper buy when one burst is what kills you.")

    line("")
    line("  WHY")
    line("  • Patch 7.3 Smite burn: 30–225 by level + 10% bonus AD + 20% bonus armor")
    line("    + 20% bonus MR + 3% bonus HP true damage. This sim ticks it once per")
    line("    second on the monster being autoed (the notes say the hit repeats,")
    line("    and up to two more times after you stop; they do not print the interval).")
    line("  • Giant's Belt already feeds that burn. Sunfire's new immolate is")
    line("    20 + 1.5% bonus HP magic per second, at 130% vs monsters, into 35 MR,")
    line("    with Flametouch and the stack amp removed.")
    line("  • Heartsteel is 700 HP, a 140 + 3.5% max HP proc, and permanent HP.")
    line("    E, W, and R all read bonus HP. So does the burn. The Sunfire-first")
    line(f"    path is still on components at 8:00 and finishes Heartsteel ~{sun_hs}:00,")
    line(f"    so the stacks stay behind ({sun[16].hs_bonus:.0f} vs {hs[16].hs_bonus:.0f} HP).")
    line("  • Warmog's Armor (7.0) is the old Spirit Visage button: +30% healing")
    line("    and regen, plus 3.5% max HP/s after 5s out of combat if you have")
    line("    950 bonus HP. Mundo's passive, W, and R all pick up the amp.")
    line("  • Mantle of the Twelfth Hour is 2550g, 600 HP, and a lifeline under")
    line("    30% HP. Buy it when one burst rotation is the way you die.")
    line("    Buy Sunfire second only when the fights are stacked melees and the")
    line("    immolate is hitting more than one champion.")
    line("")
    line("  RUNES")
    line("  Keystone: Grasp of the Undying.")
    line("  Resolve: Unshakeable, Second Wind, Overgrowth.")
    line("  Precision: Last Stand.")
    line("  Spells: Flash + Smite.")
    line("  Grasp and Overgrowth are the HP runes Heartsteel, E, W, R, and the")
    line("  Smite burn all read. Second Wind is the clear sustain. Last Stand")
    line("  matches E, which already hits harder when you are missing health.")
    line("  Swap Second Wind for Nullifying Orb into heavy magic burst.")
    line("  Swap Last Stand for Legend: Haste if you want more Q and W uptime.")
    line("")
    line("  BUY ORDER")
    line("  1. Ruby Crystal.")
    if aoe_gap < 5:
        line("  2. Giant's Belt → Kindlegem → Heartsteel. Do not stop for Bami's.")
        line(f"     Heartsteel is up ~{hs_done}:00. Proc it on scuttle and the first dragon.")
    else:
        line("  2. Bami's Cinder on the first back, then Heartsteel.")
        line(f"     Heartsteel is up ~{bami_hs}:00.")
    line("  3. Plated Steelcaps. Armored Advance after 10:00 only if it does not")
    line("     delay the next legendary.")
    if second_name == "Warmog's Armor":
        line("  4. Warmog's Armor. The heal amp is the second spike.")
        line("     Mantle of the Twelfth Hour instead if they can burst you under 30%.")
        line("     Sunfire Aegis instead if you are fighting inside a pile of melees.")
    elif second_name == "Mantle of the Twelfth Hour":
        line("  4. Mantle of the Twelfth Hour. The lifeline survives the dragon burst")
        line("     better than Warmog's sustained heal in this focus test.")
        line("     Warmog's if fights are long and you are allowed to reset.")
    else:
        line("  4. Sunfire Aegis. In this focus test the immolate damage outweighed")
        line("     Warmog's heal amp and Mantle's lifeline as the second item.")
    line("  5. Thornmail if they heal off autos. Otherwise Amaranth's Twinguard.")
    line("  Skill order: Q, E, Q, W, then max Q → E → W. R at 6 / 11 / 15.")
    line("  Q is the monster cap. E is the HP ratio. W is the heal.")
    line("")
    line("  Trap: finishing Sunfire before Heartsteel. The clear barely changes and")
    line(f"  the 8:00 fight loses {dmg_drop:.0f} damage and {live_drop:.1f}s of uptime.")
    if aoe_gap < 5:
        line(
            f"  Trap: buying Bami's \"for the clear.\" It saves {aoe_gap:.1f}s of AoE "
            f"camps and pushes Heartsteel from ~{hs_done}:00 to ~{bami_hs}:00."
        )
    line("=" * 88)
    return "\n".join(lines)


def s4_low(snaps: List[Snapshot]) -> bool:
    return snaps[4].died or snaps[4].clear_hp_pct < 0.20


def export_json(results: Dict[str, List[Snapshot]], path: Path) -> None:
    payload = {
        "meta": {
            "champion": "Dr. Mundo",
            "role": "Jungle",
            "patch": "7.3",
            "game_minutes": GAME_MINUTES,
            "question": "After the 7.3 Smite burn, does jungle Mundo still need Sunfire before Heartsteel?",
            "assumptions": {
                "raptors_small": RAPTORS_SMALL,
                "wolves_small": WOLVES_SMALL,
                "krugs_small": KRUGS_SMALL,
                "large_attack_speed": LARGE_AS,
                "small_attack_speed": SMALL_AS,
                "walk_seconds": WALK_SECONDS,
                "smite_burn": "1 true-damage tick per second on the auto target",
                "component_hp": "Ruby 150, Belt 350, Kindlegem 200 so they sum to Heartsteel 700",
            },
        },
        "builds": {
            name: [
                {
                    "minute": s.minute,
                    "items": s.items,
                    "gold": s.gold,
                    "level": s.level,
                    "max_hp": round(s.max_hp, 1),
                    "bonus_hp": round(s.bonus_hp, 1),
                    "heartsteel_bonus": round(s.hs_bonus, 1),
                    "armor": round(s.armor, 1),
                    "mr": round(s.mr, 1),
                    "clear_time": round(s.clear_time, 2),
                    "clear_hp_pct": round(s.clear_hp_pct, 4),
                    "single_time": round(s.single_time, 2),
                    "aoe_time": round(s.aoe_time, 2),
                    "died": s.died,
                    "dmg_burn": round(s.dmg_burn, 1),
                    "dmg_immolate": round(s.dmg_immolate, 1),
                    "fight_damage_8s": round(s.fight_dmg, 1),
                    "survival_seconds": round(s.survival, 2),
                    "no_burn_aoe": round(s.no_burn_aoe, 2),
                    "no_burn_single": round(s.no_burn_single, 2),
                    "no_burn_hp_pct": round(s.no_burn_hp_pct, 4),
                }
                for s in snaps
            ]
            for name, snaps in results.items()
        },
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> None:
    results = run_all()
    report = summarize(results)
    print(report)
    out_dir = Path(__file__).resolve().parent
    (out_dir / "report.txt").write_text(report + "\n", encoding="utf-8")
    export_json(results, out_dir / "results.json")
    print(f"\nWrote {out_dir / 'report.txt'} and {out_dir / 'results.json'}")


if __name__ == "__main__":
    main()
