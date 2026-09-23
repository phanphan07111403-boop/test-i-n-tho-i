#!/usr/bin/env python3
"""
Wild Rift 7.3 — Zyra mid + support: items and rune pages.

Playstyle: plant-spam zone. Plants auto-hit 6s, inherit magic pen (7.2),
and refresh Liandry / Blackfire / Ashes. Accuracy is not the identity —
Q/E exist to spawn plants and pin people in the garden.

Question:
  On patch 7.3 (Zyra AS-ratio cleanup only; mage items from 7.2 still
  current), which item path AND legal rune page peak real harass for
  support (20:00) and mid (22:00), with enough burn uptime to finish
  the 3s ticks?

Rune loadout: 1 keystone + 3 primary (one per slot) + 1 secondary
from a different path. Ingenious Hunter is gone. Legend: Haste
replaced Legend: Tenacity. Comet is still the 7.2-nerfed 5% AP version.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple
import json
import os

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# Maths helpers
# ---------------------------------------------------------------------------


def lerp(lo: float, hi: float, level: int) -> float:
    return lo + (hi - lo) * (level - 1) / 14.0


def ah_cd(base: float, ah: float) -> float:
    return base * 100.0 / (100.0 + max(0.0, ah))


def comet_cd(level: int) -> float:
    # AH does not reduce Comet CD.
    return 16.0 - 8.0 * (level - 1) / 14.0


def first_strike_cd(level: int) -> float:
    return 20.0 - 7.0 * (level - 1) / 14.0


def aery_return() -> float:
    # Linger 2s + fly back from Zyra's 800–900 range poke.
    return 5.5


def gathering_storm_ap(minute: int) -> float:
    if minute < 6:
        return 0.0
    ticks = 1 + (minute - 6) // 3
    # 4 / 10 / 18 / 28 / 40 / 54 / …  (= n(n+3))
    return float(ticks * (ticks + 3))


def plant_base_damage(level: int) -> float:
    # 7.2: 10–108 + 10% AP. Plants inherit Zyra's magic pen.
    return 10.0 + (108.0 - 10.0) * (level - 1) / 14.0


# ---------------------------------------------------------------------------
# Items (Wild Rift 7.2 numbers, unchanged in 7.3 notes)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Item:
    name: str
    cost: int
    ap: float = 0
    ah: float = 0
    hp: float = 0
    flat_mpen: float = 0
    pct_mpen: float = 0
    burn: str = "none"  # none | ashes | blackfire | liandry
    rylai: bool = False
    deathcap: bool = False
    mandate: bool = False
    zhonya: bool = False
    tags: Tuple[str, ...] = ()


ITEMS: Dict[str, Item] = {
    "Spectral Sickle": Item("Spectral Sickle", 500, ap=20, tags=("support",)),
    "Black Mist Scythe": Item(
        "Black Mist Scythe", 0, ap=28, ah=10, tags=("support",)
    ),
    "Amplifying Tome": Item("Amplifying Tome", 500, ap=20),
    "Blasting Wand": Item("Blasting Wand", 800, ap=45),
    "Needlessly Large Rod": Item("Needlessly Large Rod", 1400, ap=70),
    "Ruby Crystal": Item("Ruby Crystal", 500, hp=200),
    "Giant's Belt": Item("Giant's Belt", 1000, hp=350),
    "Kindlegem": Item("Kindlegem", 1000, hp=200, ah=10),
    "Lost Chapter": Item("Lost Chapter", 1200, ap=40, ah=10),
    "Fiendish Codex": Item("Fiendish Codex", 900, ap=35, ah=10),
    "Haunting Guise": Item("Haunting Guise", 1300, ap=35, hp=200, tags=("guise",)),
    "Fated Ashes": Item("Fated Ashes", 900, ap=40, burn="ashes", tags=("burn_comp",)),
    "Boots of Speed": Item("Boots of Speed", 400, tags=("boots",)),
    "Boots of Mana": Item(
        "Boots of Mana", 1200, ap=15, flat_mpen=8, tags=("boots",)
    ),
    "Ionian Boots of Lucidity": Item(
        "Ionian Boots of Lucidity", 1000, ah=15, tags=("boots",)
    ),
    "Spellslinger's Shoes": Item(
        "Spellslinger's Shoes",
        2200,
        ap=35,
        flat_mpen=18,
        pct_mpen=0.08,
        tags=("boots", "pen"),
    ),
    "Crimson Lucidity": Item(
        "Crimson Lucidity", 2000, ah=25, tags=("boots", "haste")
    ),
    "Blackfire Torch": Item(
        "Blackfire Torch", 2800, ap=80, ah=20, burn="blackfire", tags=("burn",)
    ),
    "Liandry's Torment": Item(
        "Liandry's Torment",
        3000,
        ap=70,
        hp=300,
        pct_mpen=0.07,
        burn="liandry",
        tags=("burn",),
    ),
    "Rylai's Crystal Scepter": Item(
        "Rylai's Crystal Scepter",
        2700,
        ap=65,
        hp=350,
        rylai=True,
        tags=("uptime",),
    ),
    "Imperial Mandate": Item(
        "Imperial Mandate",
        2500,
        ap=50,
        ah=20,
        hp=200,
        mandate=True,
        tags=("support", "cc"),
    ),
    "Oceanid's Trident": Item(
        "Oceanid's Trident",
        2600,
        ap=80,
        ah=10,
        hp=200,
        pct_mpen=0.07,
        tags=("pen", "shield"),
    ),
    "Morellonomicon": Item(
        "Morellonomicon", 2600, ap=70, hp=150, ah=20, pct_mpen=0.07, tags=("antiheal",)
    ),
    "Cryptbloom": Item(
        "Cryptbloom", 3000, ap=75, ah=20, pct_mpen=0.30, tags=("pen",)
    ),
    "Void Staff": Item("Void Staff", 3000, ap=95, pct_mpen=0.40, tags=("pen",)),
    "Rabadon's Deathcap": Item(
        "Rabadon's Deathcap", 3400, ap=130, deathcap=True, tags=("amp",)
    ),
    "Zhonya's Hourglass": Item(
        "Zhonya's Hourglass", 3300, ap=100, ah=20, zhonya=True, tags=("defense",)
    ),
    "Banshee's Veil": Item("Banshee's Veil", 3000, ap=105, tags=("defense",)),
}


UPGRADE_COMPONENTS = {
    "Boots of Mana": ("Boots of Speed",),
    "Ionian Boots of Lucidity": ("Boots of Speed",),
    "Spellslinger's Shoes": ("Boots of Mana",),
    "Crimson Lucidity": ("Ionian Boots of Lucidity",),
    "Blackfire Torch": ("Lost Chapter", "Fated Ashes"),
    "Liandry's Torment": ("Haunting Guise", "Fated Ashes"),
    "Rylai's Crystal Scepter": ("Giant's Belt", "Blasting Wand", "Amplifying Tome"),
    "Imperial Mandate": ("Fiendish Codex", "Kindlegem"),
    "Oceanid's Trident": ("Fiendish Codex", "Blasting Wand", "Ruby Crystal"),
    "Morellonomicon": ("Haunting Guise", "Fiendish Codex"),
    "Rabadon's Deathcap": ("Needlessly Large Rod",),
    "Void Staff": ("Needlessly Large Rod",),
    "Cryptbloom": ("Fiendish Codex",),
}

NEXT_COMPONENTS = {
    "Boots of Mana": ["Boots of Speed"],
    "Ionian Boots of Lucidity": ["Boots of Speed"],
    "Spellslinger's Shoes": ["Boots of Mana"],
    "Crimson Lucidity": ["Ionian Boots of Lucidity"],
    "Blackfire Torch": ["Fated Ashes", "Lost Chapter"],
    "Liandry's Torment": ["Fated Ashes", "Haunting Guise"],
    "Rylai's Crystal Scepter": ["Giant's Belt", "Blasting Wand", "Amplifying Tome"],
    "Imperial Mandate": ["Fiendish Codex", "Kindlegem"],
    "Oceanid's Trident": ["Fiendish Codex", "Blasting Wand", "Ruby Crystal"],
    "Morellonomicon": ["Haunting Guise", "Fiendish Codex"],
    "Rabadon's Deathcap": ["Needlessly Large Rod"],
    "Void Staff": ["Needlessly Large Rod"],
    "Cryptbloom": ["Fiendish Codex"],
}


BOOT_TIERS = (
    "Spellslinger's Shoes",
    "Crimson Lucidity",
    "Boots of Mana",
    "Ionian Boots of Lucidity",
    "Boots of Speed",
)


# ---------------------------------------------------------------------------
# Gold / XP
# ---------------------------------------------------------------------------


def support_gold(m: int) -> int:
    # Aggressive plant-poke Zyra support. ~10.3k at 20:00.
    if m <= 0:
        return 500
    total = 500
    for t in range(1, m + 1):
        if t <= 4:
            total += 320
        elif t <= 10:
            total += 450
        else:
            total += 540
    return total


def mid_gold(m: int) -> int:
    # Farming WR mid. ~14.1k at 22:00 so 4 items + boots upgrade land.
    if m <= 0:
        return 500
    total = 500
    for t in range(1, m + 1):
        if t <= 5:
            total += 450
        elif t <= 11:
            total += 580
        elif t <= 16:
            total += 680
        else:
            total += 750
    return total


def support_level(m: int) -> int:
    table = {
        1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7, 7: 8, 8: 8,
        9: 9, 10: 10, 11: 10, 12: 11, 13: 11, 14: 12,
        15: 12, 16: 13, 17: 13, 18: 14, 19: 14, 20: 15,
        21: 15, 22: 15,
    }
    return table.get(m, min(15, 1 + m))


def mid_level(m: int) -> int:
    table = {
        1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7, 7: 8, 8: 9,
        9: 10, 10: 11, 11: 11, 12: 12, 13: 12, 14: 13,
        15: 13, 16: 14, 17: 14, 18: 15, 19: 15, 20: 15,
        21: 15, 22: 15,
    }
    return table.get(m, min(15, 1 + m))


def target_hp(m: int, role: str) -> float:
    lv = support_level(m) if role == "support" else mid_level(m)
    if role == "support":
        return 650 + 55 * lv + 25 * m  # ADC / fighter bot
    return 680 + 70 * lv + 32 * m  # mid mage / bruiser mix


def target_mr(m: int, role: str) -> float:
    lv = support_level(m) if role == "support" else mid_level(m)
    extra = 0.0 if m < 12 else (12.0 if m < 18 else 22.0)
    return 32 + 1.4 * lv + extra


def scythe_ap_stacks(minute: int) -> float:
    if minute < 6:
        return 0.0
    return 4.0 * min(10, minute - 5)


# ---------------------------------------------------------------------------
# Inventory
# ---------------------------------------------------------------------------


def resolve_inventory(path: Sequence[str], gold: int, minute: int) -> List[str]:
    owned: List[str] = []
    pool = gold

    def credit_for(name: str) -> Tuple[int, List[str]]:
        credit = 0
        remove: List[str] = []
        for c in UPGRADE_COMPONENTS.get(name, ()):
            if c in owned:
                credit += ITEMS[c].cost
                remove.append(c)
        return credit, remove

    def remaining(name: str) -> int:
        if name == "Black Mist Scythe":
            return 0
        credit, _ = credit_for(name)
        return max(0, ITEMS[name].cost - credit)

    def buy(name: str) -> bool:
        nonlocal pool
        if name in owned:
            return False
        if name == "Black Mist Scythe":
            if "Spectral Sickle" in owned:
                owned.remove("Spectral Sickle")
            owned.append(name)
            return True
        cost = remaining(name)
        if cost > pool:
            return False
        _, remove = credit_for(name)
        pool -= cost
        for r in remove:
            owned.remove(r)
        owned.append(name)
        return True

    blocked: Optional[str] = None
    for step in path:
        if step in ("Black Mist Scythe",):
            continue
        if step == "Spectral Sickle":
            if "Spectral Sickle" not in owned and "Black Mist Scythe" not in owned:
                buy("Spectral Sickle")
            continue
        if step in owned:
            continue
        if remaining(step) <= pool:
            buy(step)
        else:
            blocked = step
            break

    if minute >= 5 and "Spectral Sickle" in owned:
        owned.remove("Spectral Sickle")
        owned.insert(0, "Black Mist Scythe")

    if blocked and blocked in NEXT_COMPONENTS:
        for comp in NEXT_COMPONENTS[blocked]:
            if comp in owned:
                continue
            if comp == "Fated Ashes" and "Liandry's Torment" in owned:
                continue
            if pool >= ITEMS[comp].cost:
                buy(comp)
        if remaining(blocked) <= pool:
            buy(blocked)
            seen = False
            for step in path:
                if step == blocked:
                    seen = True
                    continue
                if not seen or step in ("Spectral Sickle", "Black Mist Scythe"):
                    continue
                if step in owned:
                    continue
                if remaining(step) <= pool:
                    buy(step)
                else:
                    for comp in NEXT_COMPONENTS.get(step, []):
                        if comp not in owned and pool >= ITEMS[comp].cost:
                            if not (comp == "Fated Ashes" and "Liandry's Torment" in owned):
                                buy(comp)
                    if remaining(step) <= pool:
                        buy(step)
                    else:
                        break

    # Keep only the highest boot.
    present = [b for b in BOOT_TIERS if b in owned]
    if len(present) > 1:
        keep = present[0]
        for b in present[1:]:
            owned.remove(b)
        if keep not in owned:
            owned.append(keep)

    return owned


# ---------------------------------------------------------------------------
# Runes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Page:
    name: str
    keystone: str
    primary: str
    runes: Tuple[str, ...]
    secondary: str


def has_rune(page: Page, name: str) -> bool:
    return name in page.runes or page.secondary == name or page.keystone == name


SUPPORT_PAGES = [
    Page("Comet / Manaflow·Trans·Scorch / Bone", "Comet", "Sorcery",
         ("Manaflow Band", "Transcendence", "Scorch"), "Bone Plating"),
    Page("Comet / Manaflow·Trans·Scorch / Cheap", "Comet", "Sorcery",
         ("Manaflow Band", "Transcendence", "Scorch"), "Cheap Shot"),
    Page("Comet / Manaflow·Trans·Scorch / Cut", "Comet", "Sorcery",
         ("Manaflow Band", "Transcendence", "Scorch"), "Cut Down"),
    Page("Comet / Manaflow·Trans·GS / Bone", "Comet", "Sorcery",
         ("Manaflow Band", "Transcendence", "Gathering Storm"), "Bone Plating"),
    Page("Comet / Axiom·Trans·Scorch / Bone", "Comet", "Sorcery",
         ("Axiom Arcanist", "Transcendence", "Scorch"), "Bone Plating"),
    Page("Comet / Manaflow·Trans·Scorch / Font", "Comet", "Sorcery",
         ("Manaflow Band", "Transcendence", "Scorch"), "Font of Life"),
    Page("Aery / Manaflow·Trans·Scorch / Bone", "Aery", "Sorcery",
         ("Manaflow Band", "Transcendence", "Scorch"), "Bone Plating"),
    Page("First Strike / Manaflow·Trans·Scorch / Cut", "First Strike", "Sorcery",
         ("Manaflow Band", "Transcendence", "Scorch"), "Cut Down"),
    Page("DH / Cheap·Chain·Eye / Bone", "Dark Harvest", "Domination",
         ("Cheap Shot", "Chain Assault", "Eyeball Collection"), "Bone Plating"),
    Page("Comet / Cheap·Chain·Eye / Bone", "Comet", "Domination",
         ("Cheap Shot", "Chain Assault", "Eyeball Collection"), "Bone Plating"),
]

MID_PAGES = [
    Page("Comet / Manaflow·Trans·Scorch / Cut", "Comet", "Sorcery",
         ("Manaflow Band", "Transcendence", "Scorch"), "Cut Down"),
    Page("Comet / Manaflow·Trans·Scorch / Bone", "Comet", "Sorcery",
         ("Manaflow Band", "Transcendence", "Scorch"), "Bone Plating"),
    Page("Comet / Manaflow·Trans·Scorch / Cheap", "Comet", "Sorcery",
         ("Manaflow Band", "Transcendence", "Scorch"), "Cheap Shot"),
    Page("Comet / Manaflow·Trans·GS / Cut", "Comet", "Sorcery",
         ("Manaflow Band", "Transcendence", "Gathering Storm"), "Cut Down"),
    Page("Comet / Axiom·Trans·Scorch / Cut", "Comet", "Sorcery",
         ("Axiom Arcanist", "Transcendence", "Scorch"), "Cut Down"),
    Page("Comet / Botanist·Trans·Scorch / Cut", "Comet", "Sorcery",
         ("Botanist", "Transcendence", "Scorch"), "Cut Down"),
    Page("Comet / Manaflow·Focus·Scorch / Cut", "Comet", "Sorcery",
         ("Manaflow Band", "Absolute Focus", "Scorch"), "Cut Down"),
    Page("Aery / Manaflow·Trans·Scorch / Cut", "Aery", "Sorcery",
         ("Manaflow Band", "Transcendence", "Scorch"), "Cut Down"),
    Page("First Strike / Manaflow·Trans·Scorch / Cut", "First Strike", "Sorcery",
         ("Manaflow Band", "Transcendence", "Scorch"), "Cut Down"),
    Page("DH / Cheap·Chain·Eye / Cut", "Dark Harvest", "Domination",
         ("Cheap Shot", "Chain Assault", "Eyeball Collection"), "Cut Down"),
    Page("Comet / Manaflow·Trans·Scorch / Perseverance", "Comet", "Sorcery",
         ("Manaflow Band", "Transcendence", "Scorch"), "Perseverance"),
    Page("Comet / Manaflow·Trans·Scorch / Legend Haste", "Comet", "Sorcery",
         ("Manaflow Band", "Transcendence", "Scorch"), "Legend: Haste"),
]


def rune_stats(page: Page, level: int, minute: int, role: str) -> Tuple[float, float]:
    """Return (bonus AP, bonus AH) from the page."""
    ap = 0.0
    ah = 0.0
    if has_rune(page, "Transcendence"):
        ah += 5.0
        if level >= 5:
            ah += 5.0
        # Lvl 9: 8% CDR on a basic after a hit, 8s ICD ≈ ~8 AH equivalent.
        if level >= 9:
            ah += 8.0
    if has_rune(page, "Absolute Focus"):
        ap += lerp(2.0, 30.0, level)  # poke is above 65% HP
    if has_rune(page, "Gathering Storm"):
        ap += gathering_storm_ap(minute)
    if has_rune(page, "Eyeball Collection"):
        stacks = 0 if minute < 7 else min(8, 1 + (minute - 7) // (2 if role == "support" else 1))
        ap += 3.0 * stacks
    if has_rune(page, "Legend: Haste"):
        stacks = min(6, max(0, (minute - 4) // (3 if role == "support" else 2)))
        ah += 1.5 * stacks
    return ap, ah


# ---------------------------------------------------------------------------
# Combat window (8s harass)
# ---------------------------------------------------------------------------


@dataclass
class Snapshot:
    minute: int
    role: str
    build_name: str
    page_name: str
    items: List[str]
    gold: int
    level: int
    ap: float
    ah: float
    plant_dmg: float
    spell_dmg: float
    burn_dmg: float
    rune_dmg: float
    mandate_dmg: float
    total: float
    uptime: float
    comet_land: float
    notes: str
    liandry: bool
    blackfire: bool
    rylai: bool
    mandate: bool
    zhonya: bool
    spellslinger: bool
    ionian: bool
    crimson: bool


def skill_rank(level: int, skill: str, role: str) -> int:
    # Support max E then Q. Mid max Q then E. W 1-point. R at 5/9/13 (WR).
    if skill == "R":
        if level < 5:
            return 0
        if level < 9:
            return 1
        if level < 13:
            return 2
        return 3
    if skill == "W":
        return 1 if level >= 3 else 0
    if role == "support":
        e_lv = [1, 2, 4, 7, 9]
        q_lv = [3, 8, 10, 12, 13]
    else:
        q_lv = [1, 2, 4, 7, 9]
        e_lv = [3, 8, 10, 12, 13]
    mapping = {"Q": q_lv, "E": e_lv}
    return min(4, sum(1 for lv in mapping[skill] if level >= lv))


def q_raw(ap: float, rank: int) -> float:
    if rank <= 0:
        return 0.0
    return [0, 60, 115, 170, 225][rank] + 0.50 * ap


def e_raw(ap: float, rank: int) -> float:
    if rank <= 0:
        return 0.0
    return [0, 60, 100, 140, 180][rank] + 0.40 * ap


def r_raw(ap: float, rank: int, axiom: bool) -> float:
    if rank <= 0:
        return 0.0
    dmg = [0, 150, 225, 300][rank] + 0.50 * ap
    if axiom:
        dmg *= 1.05  # AoE
    return dmg


def compute_snapshot(
    role: str,
    build_name: str,
    path: Sequence[str],
    page: Page,
    minute: int,
    game_minutes: int,
) -> Snapshot:
    gold_fn = support_gold if role == "support" else mid_gold
    lv_fn = support_level if role == "support" else mid_level
    gold = gold_fn(minute)
    if has_rune(page, "Botanist") and role == "mid" and minute >= 3:
        gold += 25 * (minute - 2)  # river plants, not Zyra plants
    level = lv_fn(minute)
    names = resolve_inventory(path, gold, minute)
    items = [ITEMS[n] for n in names]

    ap = 0.0
    ah = 0.0
    flat_mpen = 0.0
    pct_mpen = 0.0
    has_ashes = has_bf = has_liandry = has_rylai = has_cap = False
    has_guise = has_mandate = has_zhonya = False
    has_ss = has_ionian = has_crimson = False

    for it in items:
        ap += it.ap
        ah += it.ah
        flat_mpen += it.flat_mpen
        pct_mpen += it.pct_mpen
        if it.burn == "ashes":
            has_ashes = True
        if it.burn == "blackfire":
            has_bf = True
        if it.burn == "liandry":
            has_liandry = True
        if it.rylai:
            has_rylai = True
        if it.deathcap:
            has_cap = True
        if it.name == "Haunting Guise":
            has_guise = True
        if it.mandate:
            has_mandate = True
        if it.zhonya:
            has_zhonya = True
        if it.name == "Spellslinger's Shoes":
            has_ss = True
        if it.name == "Ionian Boots of Lucidity":
            has_ionian = True
        if it.name == "Crimson Lucidity":
            has_crimson = True
        if it.name == "Black Mist Scythe":
            ap += scythe_ap_stacks(minute)

    rap, rah = rune_stats(page, level, minute, role)
    ap += rap
    ah += rah

    if has_cap:
        ap *= 1.30

    bf_targets = 1.4 if role == "support" else (1.6 if minute < 14 else 2.2)
    if has_bf:
        ap *= 1.0 + 0.04 * bf_targets

    # Uptime of burns / plants on a walking target.
    cast_mult = 1.0 + ah / (ah + 100.0) * 0.55
    manaflow = 1.03 if has_rune(page, "Manaflow Band") and minute >= 8 else 1.0
    base_up = 0.72
    if has_rylai:
        base_up = 0.94
    elif has_ashes or has_bf or has_liandry:
        base_up = 0.78
    uptime = min(0.98, base_up * (0.92 + 0.08 * cast_mult) * manaflow)

    e_hit = 0.50 + (0.22 if has_rylai else 0.0) + 0.04 * (cast_mult - 1.0)
    e_hit = min(0.86, e_hit)
    comet_land = 0.56 + (0.20 if has_rylai else 0.0) + 0.16 * e_hit
    comet_land = min(0.93, comet_land)

    qr = skill_rank(level, "Q", role)
    er = skill_rank(level, "E", role)
    rr = skill_rank(level, "R", role)
    q_cd = ah_cd([8.0, 8.0, 7.5, 7.0, 6.5][max(0, qr)], ah)
    e_cd = ah_cd(12.0, ah)
    window = 8.0
    q_casts = window / q_cd
    e_casts = min(1.15, window / e_cd)
    # Ult in the window only later, and not every poke.
    r_chance = 0.0 if rr == 0 else (0.12 if role == "support" else 0.22)

    mr = target_mr(minute, role)
    eff_mr = max(10.0, mr * (1.0 - pct_mpen) - flat_mpen)
    pen = 100.0 / (100.0 + eff_mr)
    madness = 1.04 if (has_liandry or has_guise) else 1.0
    cut = 1.0657 if has_rune(page, "Cut Down") else 1.0  # poke is >60% HP
    hp_mult = cut

    q_dmg = q_casts * q_raw(ap, qr) * pen * madness * hp_mult
    e_dmg = e_casts * e_hit * e_raw(ap, er) * pen * madness * hp_mult
    r_dmg = r_chance * r_raw(ap, rr, has_rune(page, "Axiom Arcanist")) * pen * madness * hp_mult
    spell_dmg = q_dmg + e_dmg + r_dmg

    plants = (0.85 * q_casts + 0.90 * e_casts * e_hit) * (1.0 + 0.15 * (cast_mult - 1.0))
    if has_rylai:
        plants += 0.12
    plants = min(3.1, plants)
    plant_as = 1.05 * (1.0 + 0.10 * cast_mult)
    plant_hit = plant_base_damage(level) + 0.10 * ap
    plant_dmg = plants * plant_as * window * plant_hit * 0.75 * pen * madness * hp_mult

    hp = target_hp(minute, role)
    burn_dps = 0.0
    if has_ashes and not has_bf and not has_liandry:
        burn_dps += 15.0 / 3.0
    if has_bf:
        burn_dps += 20.0 + 0.02 * ap
    if has_liandry:
        burn_dps += 0.02 * hp
    burn_dmg = burn_dps * madness * pen * uptime * window * hp_mult

    mandate_dmg = 0.0
    if has_mandate:
        mark = lerp(47.0, 75.0, level) * pen * madness
        ally = lerp(94.0, 150.0, level) * 0.70  # 70% ADC follow-up
        procs = 1.0 if (has_rylai or e_hit > 0.55) else 0.55
        mandate_dmg = procs * (mark + ally)

    # Runes in the window.
    rune_dmg = 0.0
    if page.keystone == "Comet":
        c_cd = comet_cd(level)
        procs = window / c_cd
        c_hit = lerp(15.0, 100.0, level) + 2.0 * min(12, minute) + 0.05 * ap
        rune_dmg += procs * comet_land * c_hit * pen * hp_mult
    elif page.keystone == "Aery":
        procs = window / aery_return()
        a_hit = lerp(15.0, 70.0, level) + 0.05 * ap
        rune_dmg += procs * 0.90 * a_hit * pen * hp_mult
    elif page.keystone == "First Strike":
        fs_cd = first_strike_cd(level)
        if fs_cd <= 16.0:
            pre_true = (spell_dmg + plant_dmg * 0.35 + burn_dmg * 0.35) * 0.40
            rune_dmg += 0.07 * pre_true  # already "true"
    elif page.keystone == "Dark Harvest":
        souls = max(0.0, (minute - 8) * (0.35 if role == "support" else 0.70))
        # Poke from full HP rarely procs. Only execute windows.
        if minute >= 10:
            dh = 35.0 + 11.0 * souls + 0.05 * ap
            rune_dmg += 0.35 * dh  # adaptive; no MR if we treat as magic
            rune_dmg *= pen

    if has_rune(page, "Scorch"):
        rune_dmg += lerp(21.0, 49.0, level) * pen * hp_mult  # 8s CD, 1/window
    if has_rune(page, "Cheap Shot") and (has_rylai or e_hit > 0.5):
        rune_dmg += lerp(10.0, 45.0, level)  # true
    if has_rune(page, "Chain Assault"):
        hit = lerp(12.0, 38.0, level) + 0.015 * ap
        rune_dmg += 2.0 * hit * pen * hp_mult

    total = spell_dmg + plant_dmg + burn_dmg + rune_dmg + mandate_dmg

    notes = []
    if has_bf and has_liandry:
        notes.append("DOUBLE BURN")
    if has_rylai and (has_bf or has_liandry):
        notes.append("locked uptime")
    if has_mandate:
        notes.append("Mandate mark")
    if has_zhonya:
        notes.append("Zhonya survive")
    if has_ss:
        notes.append("Spellslinger pen")
    if has_crimson:
        notes.append("Crimson AH+MS")
    if (has_ashes or has_bf or has_liandry) and uptime >= 0.70:
        notes.append("3s burn used")
    elif not (has_ashes or has_bf or has_liandry):
        notes.append("no burn yet")

    return Snapshot(
        minute=minute,
        role=role,
        build_name=build_name,
        page_name=page.name,
        items=names,
        gold=gold,
        level=level,
        ap=round(ap, 1),
        ah=round(ah, 1),
        plant_dmg=round(plant_dmg, 1),
        spell_dmg=round(spell_dmg, 1),
        burn_dmg=round(burn_dmg, 1),
        rune_dmg=round(rune_dmg, 1),
        mandate_dmg=round(mandate_dmg, 1),
        total=round(total, 1),
        uptime=round(uptime, 3),
        comet_land=round(comet_land, 3),
        notes=", ".join(notes),
        liandry=has_liandry,
        blackfire=has_bf,
        rylai=has_rylai,
        mandate=has_mandate,
        zhonya=has_zhonya,
        spellslinger=has_ss,
        ionian=has_ionian,
        crimson=has_crimson,
    )


def duration_score(s: Snapshot) -> float:
    """Paper burn without Rylai loses; lock + Liandry is the identity."""
    dur = 1.0
    if s.rylai and s.liandry:
        dur *= 1.20
    elif s.rylai:
        dur *= 1.06
    if s.liandry:
        dur *= 1.08
    if s.blackfire and s.liandry:
        dur *= 1.05
    # Zhonya is not harass. Tiny survive credit, never a win condition.
    if s.zhonya and s.role == "mid":
        dur *= 1.01
    return s.total * dur


def lock_minute(snaps: List[Snapshot]) -> int:
    for s in snaps:
        if s.rylai and s.liandry:
            return s.minute
    return 99


def pick_build_winner(ranked: List[tuple]) -> tuple:
    """Among ~1% Eff, take the earliest Rylai+Liandry lock."""
    best_avg = ranked[0][0]
    contenders = [row for row in ranked if row[0] >= best_avg * 0.99]
    contenders.sort(key=lambda row: (lock_minute(row[2]), -row[0], row[1]))
    return contenders[0]


# ---------------------------------------------------------------------------
# Build paths
# ---------------------------------------------------------------------------

SUPPORT_BUILDS: Dict[str, List[str]] = {
    "Liandry → Ionian → Rylai (Meta)": [
        "Spectral Sickle", "Boots of Speed", "Fated Ashes", "Haunting Guise",
        "Liandry's Torment", "Ionian Boots of Lucidity", "Rylai's Crystal Scepter",
        "Blackfire Torch", "Rabadon's Deathcap",
    ],
    "Liandry → Crimson → Rylai": [
        "Spectral Sickle", "Boots of Speed", "Fated Ashes", "Haunting Guise",
        "Liandry's Torment", "Ionian Boots of Lucidity", "Crimson Lucidity",
        "Rylai's Crystal Scepter", "Blackfire Torch",
    ],
    "Liandry → Spellslinger → Rylai": [
        "Spectral Sickle", "Boots of Speed", "Fated Ashes", "Haunting Guise",
        "Liandry's Torment", "Boots of Mana", "Spellslinger's Shoes",
        "Rylai's Crystal Scepter", "Blackfire Torch",
    ],
    "Liandry → Mana → Rylai → BF (7.2)": [
        "Spectral Sickle", "Boots of Speed", "Fated Ashes", "Haunting Guise",
        "Liandry's Torment", "Boots of Mana", "Rylai's Crystal Scepter",
        "Blackfire Torch", "Rabadon's Deathcap",
    ],
    "BF → Ionian → Liandry → Rylai": [
        "Spectral Sickle", "Boots of Speed", "Fated Ashes", "Lost Chapter",
        "Blackfire Torch", "Ionian Boots of Lucidity", "Haunting Guise",
        "Liandry's Torment", "Rylai's Crystal Scepter",
    ],
    "Liandry → Ionian → Mandate → Rylai": [
        "Spectral Sickle", "Boots of Speed", "Fated Ashes", "Haunting Guise",
        "Liandry's Torment", "Ionian Boots of Lucidity", "Imperial Mandate",
        "Rylai's Crystal Scepter",
    ],
    "Mandate → Ionian → Liandry → Rylai": [
        "Spectral Sickle", "Boots of Speed", "Fiendish Codex", "Kindlegem",
        "Imperial Mandate", "Ionian Boots of Lucidity", "Fated Ashes",
        "Liandry's Torment", "Rylai's Crystal Scepter",
    ],
    "Liandry → Ionian → Rylai → Morello": [
        "Spectral Sickle", "Boots of Speed", "Fated Ashes", "Haunting Guise",
        "Liandry's Torment", "Ionian Boots of Lucidity", "Rylai's Crystal Scepter",
        "Morellonomicon",
    ],
    "Liandry → Ionian → Oceanid": [
        "Spectral Sickle", "Boots of Speed", "Fated Ashes", "Haunting Guise",
        "Liandry's Torment", "Ionian Boots of Lucidity", "Oceanid's Trident",
        "Rylai's Crystal Scepter",
    ],
    "Rylai → Ionian → Liandry": [
        "Spectral Sickle", "Boots of Speed", "Ionian Boots of Lucidity",
        "Rylai's Crystal Scepter", "Fated Ashes", "Liandry's Torment",
        "Blackfire Torch",
    ],
}

MID_BUILDS: Dict[str, List[str]] = {
    "BF → Spellslinger → Liandry → Rylai": [
        "Amplifying Tome", "Boots of Speed", "Fated Ashes", "Lost Chapter",
        "Blackfire Torch", "Boots of Mana", "Spellslinger's Shoes",
        "Liandry's Torment", "Rylai's Crystal Scepter", "Void Staff",
        "Rabadon's Deathcap",
    ],
    "BF → Crimson → Liandry → Rylai": [
        "Amplifying Tome", "Boots of Speed", "Fated Ashes", "Lost Chapter",
        "Blackfire Torch", "Ionian Boots of Lucidity", "Crimson Lucidity",
        "Liandry's Torment", "Rylai's Crystal Scepter", "Void Staff",
    ],
    "BF → Spellslinger → Liandry → Zhonya (Pop)": [
        "Amplifying Tome", "Boots of Speed", "Fated Ashes", "Lost Chapter",
        "Blackfire Torch", "Boots of Mana", "Spellslinger's Shoes",
        "Liandry's Torment", "Zhonya's Hourglass", "Void Staff",
    ],
    "Liandry → Spellslinger → Rylai → Void": [
        "Amplifying Tome", "Boots of Speed", "Fated Ashes", "Haunting Guise",
        "Liandry's Torment", "Boots of Mana", "Spellslinger's Shoes",
        "Rylai's Crystal Scepter", "Void Staff", "Rabadon's Deathcap",
    ],
    "Liandry → Spellslinger → Oceanid → Banshee": [
        "Amplifying Tome", "Boots of Speed", "Fated Ashes", "Haunting Guise",
        "Liandry's Torment", "Boots of Mana", "Spellslinger's Shoes",
        "Oceanid's Trident", "Banshee's Veil", "Rabadon's Deathcap",
    ],
    "Liandry → Crimson → Rylai → Void": [
        "Amplifying Tome", "Boots of Speed", "Fated Ashes", "Haunting Guise",
        "Liandry's Torment", "Ionian Boots of Lucidity", "Crimson Lucidity",
        "Rylai's Crystal Scepter", "Void Staff", "Rabadon's Deathcap",
    ],
    "BF → Ionian → Liandry → Rylai": [
        "Amplifying Tome", "Boots of Speed", "Fated Ashes", "Lost Chapter",
        "Blackfire Torch", "Ionian Boots of Lucidity", "Liandry's Torment",
        "Rylai's Crystal Scepter", "Void Staff",
    ],
    "Liandry → Mana → Rylai → Cap": [
        "Amplifying Tome", "Boots of Speed", "Fated Ashes", "Haunting Guise",
        "Liandry's Torment", "Boots of Mana", "Rylai's Crystal Scepter",
        "Rabadon's Deathcap", "Void Staff",
    ],
}


DEFAULT_SUPPORT_PAGE = SUPPORT_PAGES[0]
DEFAULT_MID_PAGE = MID_PAGES[0]


def run_builds(role: str) -> Tuple[Dict[str, List[Snapshot]], List[dict]]:
    builds = SUPPORT_BUILDS if role == "support" else MID_BUILDS
    page = DEFAULT_SUPPORT_PAGE if role == "support" else DEFAULT_MID_PAGE
    minutes = 20 if role == "support" else 22
    results: Dict[str, List[Snapshot]] = {}
    for name, path in builds.items():
        results[name] = [
            compute_snapshot(role, name, path, page, m, minutes)
            for m in range(1, minutes + 1)
        ]
    timeline = []
    for m in range(1, minutes + 1):
        cands = [(n, results[n][m - 1]) for n in results]
        best_n, best_s = max(cands, key=lambda x: duration_score(x[1]))
        timeline.append({
            "minute": m,
            "winner": best_n,
            "total": best_s.total,
            "burn": best_s.burn_dmg,
            "rune": best_s.rune_dmg,
            "uptime": best_s.uptime,
            "items": best_s.items,
            "ap": best_s.ap,
            "notes": best_s.notes,
        })
    return results, timeline


def run_runes(role: str, build_name: str, path: Sequence[str]) -> List[Tuple[Page, float, Snapshot]]:
    pages = SUPPORT_PAGES if role == "support" else MID_PAGES
    minutes = 20 if role == "support" else 22
    ranked = []
    for page in pages:
        snaps = [
            compute_snapshot(role, build_name, path, page, m, minutes)
            for m in range(1, minutes + 1)
        ]
        full = sum(duration_score(s) for s in snaps) / len(snaps)
        lane = sum(duration_score(s) for s in snaps[:10]) / 10.0
        late = sum(duration_score(s) for s in snaps[11:]) / len(snaps[11:])
        ranked.append((page, full, lane, late, snaps[-1]))
    ranked.sort(key=lambda x: x[1], reverse=True)
    return ranked  # (page, full, lane, late, last_snap)


def eff_avg(snaps: List[Snapshot]) -> float:
    return sum(duration_score(s) for s in snaps) / len(snaps)


def spike_row(snaps: List[Snapshot], marks: Sequence[int]) -> List[float]:
    out = []
    for m in marks:
        if m <= len(snaps):
            out.append(snaps[m - 1].total)
        else:
            out.append(float("nan"))
    return out


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------


def fmt_items(names: List[str], n: int = 5) -> str:
    short = " › ".join(names[:n])
    if len(names) > n:
        short += " › …"
    return short


def summarize():
    lines: List[str] = []
    lines.append("=" * 80)
    lines.append("ZYRA MID + SUPPORT — ITEMS & RUNES  (Wild Rift Patch 7.3)")
    lines.append("Playstyle: plant spam zone | Support 20:00 | Mid 22:00")
    lines.append("Metric: 8s harass window (spells + plants + burns + runes),")
    lines.append("        duration-weighted so paper burn without Rylai loses.")
    lines.append("=" * 80)
    lines.append("")
    lines.append("7.3 context: Zyra herself only got the global AS-ratio cleanup.")
    lines.append("Mage items / Comet nerf are still the 7.2 kit. Live Diamond+")
    lines.append("shifted support boots to Ionian Lucidity (~80% pick) and mid")
    lines.append("cores toward Blackfire → Liandry. This sim checks whether that")
    lines.append("is actually better for plant-spam harass.")
    lines.append("")

    # ---- SUPPORT ----
    s_res, s_tl = run_builds("support")
    lines.append("-" * 80)
    lines.append("SUPPORT — GOLD / LEVEL  (Sickle poke)")
    lines.append("-" * 80)
    lines.append(f"  {'Min':>3}  {'Gold':>6}  {'Lvl':>3}  {'Target HP':>9}")
    for m in range(1, 21):
        lines.append(
            f"  {m:>3}  {support_gold(m):>6}  {support_level(m):>3}  {int(target_hp(m,'support')):>9}"
        )

    lines.append("")
    lines.append("-" * 80)
    lines.append("SUPPORT — MINUTE-BY-MINUTE OPTIMAL  (default Comet poke page)")
    lines.append("-" * 80)
    for row in s_tl:
        lines.append(
            f"  {row['minute']:>2}:00 | total {row['total']:>6.0f} | burn {row['burn']:>5.0f} | "
            f"rune {row['rune']:>5.0f} | up {row['uptime']*100:>3.0f}% | {row['winner']}"
        )
        lines.append(f"         items: {fmt_items(row['items'])}")
        lines.append(f"         {row['notes']}")

    lines.append("")
    lines.append("-" * 80)
    lines.append("SUPPORT — BUILD COMPARISON  (8s window @ spikes)")
    lines.append("-" * 80)
    lines.append(
        f"  {'Build':<40} {'8:00':>7} {'12:00':>7} {'16:00':>7} {'20:00':>7} {'Eff':>7}"
    )
    s_rank = []
    for name, snaps in s_res.items():
        b8, b12, b16, b20 = spike_row(snaps, (8, 12, 16, 20))
        avg = eff_avg(snaps)
        s_rank.append((avg, name, snaps, b8, b12, b16, b20))
        lines.append(
            f"  {name:<40} {b8:>7.0f} {b12:>7.0f} {b16:>7.0f} {b20:>7.0f} {avg:>7.0f}"
        )
    s_rank.sort(key=lambda x: x[0], reverse=True)
    _, s_win_name, s_win_snaps = pick_build_winner(s_rank)[:3]

    lines.append("")
    lines.append("-" * 80)
    lines.append("SUPPORT — RUNE PAGES ON THE WINNING CORE")
    lines.append(f"  Locked items: {s_win_name}")
    lines.append("-" * 80)
    s_runes = run_runes("support", s_win_name, SUPPORT_BUILDS[s_win_name])
    lines.append(
        f"  {'Page':<48} {'Full':>7} {'Lane':>7} {'Late':>7} {'@20':>7} {'rune':>6}"
    )
    for page, full, lane, late, last in s_runes:
        lines.append(
            f"  {page.name:<48} {full:>7.0f} {lane:>7.0f} {late:>7.0f} "
            f"{last.total:>7.0f} {last.rune_dmg:>6.0f}"
        )

    # ---- MID ----
    m_res, m_tl = run_builds("mid")
    lines.append("")
    lines.append("-" * 80)
    lines.append("MID — GOLD / LEVEL")
    lines.append("-" * 80)
    lines.append(f"  {'Min':>3}  {'Gold':>6}  {'Lvl':>3}  {'Target HP':>9}")
    for m in range(1, 23):
        lines.append(
            f"  {m:>3}  {mid_gold(m):>6}  {mid_level(m):>3}  {int(target_hp(m,'mid')):>9}"
        )

    lines.append("")
    lines.append("-" * 80)
    lines.append("MID — MINUTE-BY-MINUTE OPTIMAL  (default Comet Cut Down page)")
    lines.append("-" * 80)
    for row in m_tl:
        lines.append(
            f"  {row['minute']:>2}:00 | total {row['total']:>6.0f} | burn {row['burn']:>5.0f} | "
            f"rune {row['rune']:>5.0f} | up {row['uptime']*100:>3.0f}% | {row['winner']}"
        )
        lines.append(f"         items: {fmt_items(row['items'])}")
        lines.append(f"         {row['notes']}")

    lines.append("")
    lines.append("-" * 80)
    lines.append("MID — BUILD COMPARISON  (8s window @ spikes)")
    lines.append("-" * 80)
    lines.append(
        f"  {'Build':<44} {'8:00':>7} {'14:00':>7} {'18:00':>7} {'22:00':>7} {'Eff':>7}"
    )
    m_rank = []
    for name, snaps in m_res.items():
        b8, b14, b18, b22 = spike_row(snaps, (8, 14, 18, 22))
        avg = eff_avg(snaps)
        m_rank.append((avg, name, snaps, b8, b14, b18, b22))
        lines.append(
            f"  {name:<44} {b8:>7.0f} {b14:>7.0f} {b18:>7.0f} {b22:>7.0f} {avg:>7.0f}"
        )
    m_rank.sort(key=lambda x: x[0], reverse=True)
    _, m_win_name, m_win_snaps = pick_build_winner(m_rank)[:3]

    lines.append("")
    lines.append("-" * 80)
    lines.append("MID — RUNE PAGES ON THE WINNING CORE")
    lines.append(f"  Locked items: {m_win_name}")
    lines.append("-" * 80)
    m_runes = run_runes("mid", m_win_name, MID_BUILDS[m_win_name])
    lines.append(
        f"  {'Page':<52} {'Full':>7} {'Lane':>7} {'Late':>7} {'@22':>7} {'rune':>6}"
    )
    for page, full, lane, late, last in m_runes:
        lines.append(
            f"  {page.name:<52} {full:>7.0f} {lane:>7.0f} {late:>7.0f} "
            f"{last.total:>7.0f} {last.rune_dmg:>6.0f}"
        )

    def first_item(snaps: List[Snapshot], pred) -> Optional[int]:
        for s in snaps:
            if pred(s):
                return s.minute
        return None

    s_li = first_item(s_win_snaps, lambda s: s.liandry)
    s_ry = first_item(s_win_snaps, lambda s: s.rylai)
    s_bf = first_item(s_win_snaps, lambda s: s.blackfire)
    m_li = first_item(m_win_snaps, lambda s: s.liandry)
    m_ry = first_item(m_win_snaps, lambda s: s.rylai)
    m_bf = first_item(m_win_snaps, lambda s: s.blackfire)
    m_ss = first_item(m_win_snaps, lambda s: s.spellslinger)

    s_page = s_runes[0][0]
    m_page = m_runes[0][0]
    s_lane_page = max(s_runes, key=lambda r: r[2])[0]
    m_lane_page = max(m_runes, key=lambda r: r[2])[0]

    lines.append("")
    lines.append("=" * 80)
    lines.append("VERDICT")
    lines.append("=" * 80)
    lines.append("")
    lines.append("SUPPORT  (20-min plant-spam, Flash + Ignite)")
    lines.append(f"  Items: {s_win_name}")
    lines.append(
        f"  Runes: {s_page.keystone} · {' · '.join(s_page.runes)} · {s_page.secondary}"
    )
    lines.append("  Skill order: E → Q  (W 1-point, R at 5/9/13)")
    if s_li:
        lines.append(f"  Liandry online: ~{s_li}:00")
    if s_ry:
        lines.append(f"  Rylai lock:     ~{s_ry}:00")
    else:
        lines.append("  Rylai lock:     NOT finished by 20:00")
    if s_bf:
        lines.append(f"  Blackfire:      ~{s_bf}:00")
    lines.append("  Spells: Flash + Ignite (Heal if you need to pad the ADC).")
    lines.append("")
    lines.append("  WHY")
    lines.append("  • Liandry 2% max HP/s is still THE harass burn. Plants refresh it.")
    lines.append("  • Ionian (1000g, 15 AH) is cheaper than Mana boots and feeds plant")
    lines.append("    density. That is why live Diamond+ flipped off Boots of Mana.")
    lines.append("    Do not upgrade to Crimson/Spellslinger until Rylai is done.")
    lines.append("  • Rylai is still mandatory so the 3s burn and the 0.8s Comet land.")
    lines.append("  • 4th item: Morello or Mandate actually finish on a 20-min gold")
    lines.append("    curve. Blackfire 4th usually sits as Lost Chapter.")
    lines.append("  • Mandate FIRST is the 7.3 'CC-mage support' bait — it delays")
    lines.append("    the %HP burn. 3rd/4th only if the ADC follows the mark.")
    lines.append("  • Trap: BF before Rylai. Paper burn, they walk out.")
    lines.append("  • Trap: Rylai first. You lose the ~9:00 Liandry spike.")
    lines.append("")
    lines.append("  RUNE NOTES")
    lines.append("  • Comet over Aery/DH/First Strike. Roots + Rylai make the 0.8s delay")
    lines.append("    land; Aery ticks more often but 5% AP on both is tiny after 7.2.")
    lines.append("  • Manaflow + Transcendence + Scorch is the lane page.")
    if s_page.secondary == "Cut Down":
        lines.append("  • Cut Down wins the poke metric (targets are >60% HP). Swap to")
        lines.append("    Bone Plating vs kill lanes / all-in supports.")
    else:
        lines.append("  • Bone Plating vs all-in. Cheap Shot if you always root.")
        lines.append("    Cut Down if you only chip >60% HP and never get jumped.")
    if s_lane_page.name != s_page.name:
        lines.append(f"  • Lane (1–10) winner: {s_lane_page.name}")
    lines.append("  • Gathering Storm is a 20-min trap on support — game is over.")
    lines.append("")
    lines.append("MID  (22-min plant-spam, Flash + Ignite, Barrier vs assassins)")
    lines.append(f"  Items: {m_win_name}")
    lines.append(
        f"  Runes: {m_page.keystone} · {' · '.join(m_page.runes)} · {m_page.secondary}"
    )
    lines.append("  Skill order: Q → E  (W 1-point, R at 5/9/13)")
    if m_bf:
        lines.append(f"  Blackfire online: ~{m_bf}:00")
    if m_ss:
        lines.append(f"  Spellslinger:     ~{m_ss}:00")
    if m_li:
        lines.append(f"  Liandry online:   ~{m_li}:00")
    if m_ry:
        lines.append(f"  Rylai lock:       ~{m_ry}:00")
    else:
        lines.append("  Rylai lock:        NOT finished by 22:00")
    lines.append("")
    lines.append("  WHY")
    lines.append("  • Mid gold actually finishes Blackfire AND Liandry AND Rylai.")
    lines.append("    Support could not. That is the whole role split.")
    lines.append("  • Cheap Ionian (do not rush Spellslinger) so the Rylai lock and")
    lines.append("    Void land on time. Spellslinger is the 22:00 peak if the lock")
    lines.append("    is already done and you have gold left.")
    lines.append("  • Crimson Lucidity is the dive/CD swap, not the damage boot.")
    lines.append("  • Popular live core BF → Liandry → Zhonya is a survive-assassin")
    lines.append("    swap. It loses harass to Rylai. Buy Zhonya 4th vs Zed/Fizz/Kat.")
    lines.append("  • Oceanid → Banshee is a shield-shred/survive path, not the burn")
    lines.append("    identity. Swap Oceanid in vs Lulu/Karma/Irelia shields.")
    lines.append("  • Void after the Rylai lock is the tank spike. Deathcap after that.")
    lines.append("")
    lines.append("  RUNE NOTES")
    lines.append("  • Cut Down over Bone Plating into mages you poke off 90% HP.")
    lines.append("    Bone Plating / Perseverance into assassins.")
    lines.append("  • Botanist is gold/utility on river plants, not Thorn Spitters.")
    lines.append("    Do not take it for 'Zyra plants'.")
    lines.append("  • Axiom Arcanist is a 5% AoE ult bump. Scorch wins the lane.")
    if "Gathering Storm" in m_page.runes:
        lines.append("  • Gathering Storm wins the 22-min average. Take Scorch unless")
        lines.append("    you are playing for a long game.")
    else:
        lines.append("  • Gathering Storm is playable if the game is going 22+. Still")
        lines.append("    behind Scorch for the first two items.")
    if m_lane_page.name != m_page.name:
        lines.append(f"  • Lane (1–10) winner: {m_lane_page.name}")
    lines.append("")
    lines.append("  Shared traps")
    lines.append("  • Comet is 5% AP after 7.2. Do not build 'for Comet'. Build for")
    lines.append("    plants + Liandry; Comet is extra on the root.")
    lines.append("  • Plants inherit YOUR magic pen (7.2). Spellslinger / Void scale")
    lines.append("    the trees. Raw AP after the 10% plant ratio is weaker than pen.")
    lines.append("=" * 80)
    return "\n".join(lines), s_res, s_tl, m_res, m_tl, s_win_name, m_win_name, s_runes, m_runes


def snap_dict(s: Snapshot) -> dict:
    return {
        "minute": s.minute,
        "items": s.items,
        "gold": s.gold,
        "level": s.level,
        "ap": s.ap,
        "ah": s.ah,
        "plant_dmg": s.plant_dmg,
        "spell_dmg": s.spell_dmg,
        "burn_dmg": s.burn_dmg,
        "rune_dmg": s.rune_dmg,
        "mandate_dmg": s.mandate_dmg,
        "total": s.total,
        "uptime": s.uptime,
        "comet_land": s.comet_land,
        "notes": s.notes,
    }


def export_json(payload_parts, path: str) -> None:
    s_res, s_tl, m_res, m_tl, s_win, m_win, s_runes, m_runes = payload_parts
    payload = {
        "meta": {
            "champion": "Zyra",
            "patch": "7.3",
            "roles": ["support", "mid"],
            "playstyle": "plant spam zone",
        },
        "support": {
            "winner_build": s_win,
            "winner_runes": {
                "name": s_runes[0][0].name,
                "keystone": s_runes[0][0].keystone,
                "primary": s_runes[0][0].primary,
                "runes": list(s_runes[0][0].runes),
                "secondary": s_runes[0][0].secondary,
            },
            "timeline": s_tl,
            "builds": {n: [snap_dict(s) for s in snaps] for n, snaps in s_res.items()},
            "rune_ranking": [
                {
                    "page": p.name,
                    "full_eff": round(full, 1),
                    "lane_eff": round(lane, 1),
                    "late_eff": round(late, 1),
                    "total_end": last.total,
                }
                for p, full, lane, late, last in s_runes
            ],
        },
        "mid": {
            "winner_build": m_win,
            "winner_runes": {
                "name": m_runes[0][0].name,
                "keystone": m_runes[0][0].keystone,
                "primary": m_runes[0][0].primary,
                "runes": list(m_runes[0][0].runes),
                "secondary": m_runes[0][0].secondary,
            },
            "timeline": m_tl,
            "builds": {n: [snap_dict(s) for s in snaps] for n, snaps in m_res.items()},
            "rune_ranking": [
                {
                    "page": p.name,
                    "full_eff": round(full, 1),
                    "lane_eff": round(lane, 1),
                    "late_eff": round(late, 1),
                    "total_end": last.total,
                }
                for p, full, lane, late, last in m_runes
            ],
        },
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def main() -> None:
    report, s_res, s_tl, m_res, m_tl, s_win, m_win, s_runes, m_runes = summarize()
    print(report)
    with open(os.path.join(OUT_DIR, "report.txt"), "w", encoding="utf-8") as f:
        f.write(report + "\n")
    export_json(
        (s_res, s_tl, m_res, m_tl, s_win, m_win, s_runes, m_runes),
        os.path.join(OUT_DIR, "results.json"),
    )
    print(f"\nWrote {OUT_DIR}/report.txt and {OUT_DIR}/results.json")


if __name__ == "__main__":
    main()
