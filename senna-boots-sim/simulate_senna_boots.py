#!/usr/bin/env python3
"""
Wild Rift Senna — Ionian Boots vs Boots of Dynamism.

Patch 7.3 champion values. Boot stats from 7.2 / 7.2a (unchanged in 7.3 notes).
Average game: 20 minutes. Same core, only the boot line changes.

Question:
  Aggressive DH Senna sims defaulted to Dynamism. Enchanter Senna sims
  defaulted to Ionian. Is that role-split real once T2/T3 stats, leftover
  Long Sword, Q refunds, and Flash haste are modeled — or is one boot
  just better?
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import json
import os

GAME_MINUTES = 20
T3_BOOTS_MINUTE = 10
OUT_DIR = os.path.dirname(os.path.abspath(__file__))

# Flash is 150s in WR. Summoner haste uses the same 100/(100+H) formula as AH.
FLASH_BASE = 150.0


# ---------------------------------------------------------------------------
# Economy
# ---------------------------------------------------------------------------


def adc_gold(minute: int) -> int:
    """Aggressive bot/flex Senna: CS + fights. Matches the DH-sim curve."""
    if minute <= 0:
        return 500
    total = 500
    for t in range(1, minute + 1):
        if t <= 4:
            total += 380
        elif t <= 10:
            total += 560
        else:
            total += 680
    return total


def support_gold(minute: int) -> int:
    """Support Senna: sickle tribute + fights. Matches the enchanter-sim curve."""
    if minute <= 0:
        return 500
    total = 500
    for t in range(1, minute + 1):
        if t <= 4:
            total += 330
        elif t <= 10:
            total += 460
        else:
            total += 560
    return total


def gold_at_minute(minute: int, role: str) -> int:
    return adc_gold(minute) if role == "adc" else support_gold(minute)


def level_at_minute(minute: int, role: str) -> int:
    if role == "adc":
        table = {
            1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7, 7: 8, 8: 9,
            9: 10, 10: 10, 11: 11, 12: 12, 13: 12, 14: 13,
            15: 13, 16: 14, 17: 14, 18: 15, 19: 15, 20: 15,
        }
    else:
        table = {
            1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7, 7: 8, 8: 8,
            9: 9, 10: 10, 11: 10, 12: 11, 13: 11, 14: 12,
            15: 12, 16: 13, 17: 13, 18: 14, 19: 14, 20: 15,
        }
    return table.get(minute, min(15, 1 + minute))


def mist_at_minute(minute: int, role: str) -> float:
    if role == "adc":
        # Aggressive mist: Living Extraction + fight wraiths.
        stacks = 0.0
        for t in range(1, minute + 1):
            if t <= 4:
                stacks += 6.0
            elif t <= 10:
                stacks += 9.5
            else:
                stacks += 11.5
        return stacks
    return min(100.0, 8.0 + 3.5 * minute)


# ---------------------------------------------------------------------------
# Items — WR 7.2 boots (7.2a Armorcrusher nerf) + 7.3 Senna cores
# ---------------------------------------------------------------------------


@dataclass
class Item:
    name: str
    cost: int
    ad: float = 0
    ah: float = 0
    as_pct: float = 0
    crit: float = 0
    ap: float = 0
    hp: float = 0
    hsp: float = 0
    mana_regen_pct: float = 0
    flat_apen: float = 0
    pct_apen: float = 0
    summoner_haste: float = 0
    drak: bool = False
    collector: bool = False
    serylda: bool = False
    magnetic: bool = False
    ardent: bool = False
    helia: bool = False
    harmonic: bool = False
    tags: Tuple[str, ...] = ()


ITEMS: Dict[str, Item] = {
    "Long Sword": Item("Long Sword", 500, ad=12),
    "Boots of Speed": Item("Boots of Speed", 400, tags=("boots", "t1")),
    "Ring of Revelation": Item("Ring of Revelation", 300, ah=5),
    "Pickaxe": Item("Pickaxe", 800, ad=20),
    "Caulfield's Warhammer": Item("Caulfield's Warhammer", 1200, ad=20, ah=20),
    "Serrated Dirk": Item("Serrated Dirk", 1000, ad=20, flat_apen=12),
    "Cloak of Agility": Item("Cloak of Agility", 800, crit=0.20),
    "Last Whisper": Item("Last Whisper", 1200, ad=15, pct_apen=0.15),
    "Amplifying Tome": Item("Amplifying Tome", 500, ap=20),
    "Kindlegem": Item("Kindlegem", 1000, hp=200, ah=10),
    "Bandleglass Mirror": Item(
        "Bandleglass Mirror", 900, ap=20, ah=10, mana_regen_pct=0.50
    ),
    "Spectral Sickle": Item("Spectral Sickle", 500, ap=20, tags=("support",)),
    "Black Mist Scythe": Item(
        "Black Mist Scythe", 0, ap=28, ah=10, tags=("support",)
    ),
    # T2 — 7.2
    "Ionian Boots of Lucidity": Item(
        "Ionian Boots of Lucidity",
        1000,
        ah=15,
        summoner_haste=15.0,
        tags=("boots", "t2", "ionian"),
    ),
    "Boots of Dynamism": Item(
        "Boots of Dynamism",
        1200,
        ad=15,
        flat_apen=10,
        tags=("boots", "t2", "dynamism"),
    ),
    # T3 — Crimson 7.2; Armorcrusher 7.2a (AD 25→20, flat pen 12→10)
    "Crimson Lucidity": Item(
        "Crimson Lucidity",
        2000,
        ah=25,
        mana_regen_pct=0.75,
        summoner_haste=20.0,
        tags=("boots", "t3", "ionian"),
    ),
    "Armorcrusher Boots": Item(
        "Armorcrusher Boots",
        2200,
        ad=20,
        flat_apen=10,
        pct_apen=0.06,
        tags=("boots", "t3", "dynamism"),
    ),
    "Duskblade of Draktharr": Item(
        "Duskblade of Draktharr",
        3000,
        ad=55,
        ah=10,
        flat_apen=18,
        drak=True,
        tags=("lethality",),
    ),
    "The Collector": Item(
        "The Collector",
        3000,
        ad=50,
        crit=0.25,
        flat_apen=12,
        collector=True,
        tags=("execute",),
    ),
    "Magnetic Blaster": Item(
        "Magnetic Blaster",
        3000,
        as_pct=0.35,
        crit=0.25,
        magnetic=True,
        tags=("range",),
    ),
    "Serylda's Grudge": Item(
        "Serylda's Grudge",
        3100,
        ad=50,
        ah=20,
        pct_apen=0.35,
        serylda=True,
        tags=("pen",),
    ),
    "Ardent Censer": Item(
        "Ardent Censer",
        2400,
        ap=50,
        hsp=0.08,
        mana_regen_pct=0.50,
        ardent=True,
        tags=("enchanter",),
    ),
    "Echoes of Helia": Item(
        "Echoes of Helia",
        2400,
        ap=40,
        ah=20,
        hp=200,
        mana_regen_pct=0.50,
        helia=True,
        tags=("enchanter",),
    ),
    "Harmonic Echo": Item(
        "Harmonic Echo",
        2500,
        ap=40,
        ah=20,
        hp=200,
        harmonic=True,
        tags=("enchanter",),
    ),
}


UPGRADE_COMPONENTS: Dict[str, Tuple[str, ...]] = {
    "Ionian Boots of Lucidity": ("Boots of Speed", "Ring of Revelation"),
    "Boots of Dynamism": ("Boots of Speed", "Long Sword"),
    "Crimson Lucidity": ("Ionian Boots of Lucidity",),
    "Armorcrusher Boots": ("Boots of Dynamism",),
    "Duskblade of Draktharr": ("Serrated Dirk", "Caulfield's Warhammer"),
    "The Collector": ("Pickaxe", "Cloak of Agility"),
    "Magnetic Blaster": ("Cloak of Agility",),
    "Serylda's Grudge": ("Last Whisper", "Caulfield's Warhammer"),
    "Echoes of Helia": ("Bandleglass Mirror", "Kindlegem"),
    "Harmonic Echo": ("Bandleglass Mirror", "Kindlegem"),
    "Ardent Censer": ("Amplifying Tome",),
}

NEXT_COMPONENTS: Dict[str, List[str]] = {
    "Ionian Boots of Lucidity": ["Boots of Speed", "Ring of Revelation"],
    "Boots of Dynamism": ["Boots of Speed", "Long Sword"],
    "Crimson Lucidity": ["Ionian Boots of Lucidity"],
    "Armorcrusher Boots": ["Boots of Dynamism"],
    "Duskblade of Draktharr": ["Serrated Dirk", "Caulfield's Warhammer"],
    "The Collector": ["Pickaxe", "Cloak of Agility"],
    "Magnetic Blaster": ["Cloak of Agility"],
    "Serylda's Grudge": ["Last Whisper", "Caulfield's Warhammer"],
    "Echoes of Helia": ["Bandleglass Mirror", "Kindlegem"],
    "Harmonic Echo": ["Kindlegem", "Bandleglass Mirror"],
    "Ardent Censer": ["Amplifying Tome"],
}

T3_BOOTS = {"Crimson Lucidity", "Armorcrusher Boots"}
T2_BOOTS = {"Ionian Boots of Lucidity", "Boots of Dynamism"}
FINISHED_BOOTS = T2_BOOTS | T3_BOOTS


def adc_path(*boot_line: str) -> List[str]:
    """DH carry core from the existing Senna sim — only the boot line swaps."""
    t1, t2, t3 = boot_line
    return [
        "Long Sword",
        t1,
        t2,
        "Serrated Dirk",
        "Duskblade of Draktharr",
        "The Collector",
        t3,
        "Magnetic Blaster",
        "Serylda's Grudge",
    ]


def support_path(*boot_line: str) -> List[str]:
    """Enchanter core (Ardent → Helia → Harmonic) — only the boot line swaps."""
    t1, t2, t3 = boot_line
    return [
        "Spectral Sickle",
        t1,
        t2,
        "Ardent Censer",
        "Echoes of Helia",
        t3,
        "Harmonic Echo",
    ]


IONIAN_LINE = (
    "Boots of Speed",
    "Ionian Boots of Lucidity",
    "Crimson Lucidity",
)
DYNAMISM_LINE = (
    "Boots of Speed",
    "Boots of Dynamism",
    "Armorcrusher Boots",
)

BUILD_PATHS: Dict[str, List[str]] = {
    "ADC · Dynamism → Armorcrusher": adc_path(*DYNAMISM_LINE),
    "ADC · Ionian → Crimson": adc_path(*IONIAN_LINE),
    "Support · Dynamism → Armorcrusher": support_path(*DYNAMISM_LINE),
    "Support · Ionian → Crimson": support_path(*IONIAN_LINE),
}

ROLE_OF = {
    "ADC · Dynamism → Armorcrusher": "adc",
    "ADC · Ionian → Crimson": "adc",
    "Support · Dynamism → Armorcrusher": "support",
    "Support · Ionian → Crimson": "support",
}


# ---------------------------------------------------------------------------
# Inventory
# ---------------------------------------------------------------------------


def remaining_cost(item_name: str, owned: List[str]) -> int:
    if item_name == "Black Mist Scythe":
        return 0
    credit = 0
    for c in UPGRADE_COMPONENTS.get(item_name, ()):
        if c in owned:
            credit += ITEMS[c].cost
    return max(0, ITEMS[item_name].cost - credit)


def path_item_done(step: str, owned: List[str]) -> bool:
    if step in owned:
        return True
    if step == "Boots of Speed" and any(b in owned for b in FINISHED_BOOTS):
        return True
    if step == "Ionian Boots of Lucidity" and "Crimson Lucidity" in owned:
        return True
    if step == "Boots of Dynamism" and "Armorcrusher Boots" in owned:
        return True
    if step == "Long Sword" and "Boots of Dynamism" in owned:
        return True
    if step == "Long Sword" and "Armorcrusher Boots" in owned:
        return True
    if step == "Spectral Sickle" and "Black Mist Scythe" in owned:
        return True
    if step in ("Serrated Dirk", "Caulfield's Warhammer") and "Duskblade of Draktharr" in owned:
        return True
    if step in ("Pickaxe", "Cloak of Agility") and "The Collector" in owned:
        return True
    if step == "Cloak of Agility" and "Magnetic Blaster" in owned:
        return True
    if step in ("Bandleglass Mirror", "Kindlegem") and (
        "Echoes of Helia" in owned or "Harmonic Echo" in owned
    ):
        return True
    return False


def can_buy(item_name: str, owned: List[str], gold: int, minute: int) -> bool:
    if item_name in owned:
        return False
    if item_name in T3_BOOTS and minute < T3_BOOTS_MINUTE:
        return False
    return gold >= remaining_cost(item_name, owned)


def buy(item_name: str, owned: List[str], gold: int) -> Tuple[List[str], int]:
    owned = list(owned)
    if item_name == "Black Mist Scythe":
        if "Spectral Sickle" in owned:
            owned.remove("Spectral Sickle")
        owned.append(item_name)
        return owned, gold
    cost = remaining_cost(item_name, owned)
    gold -= cost
    for c in UPGRADE_COMPONENTS.get(item_name, ()):
        if c in owned:
            owned.remove(c)
    owned.append(item_name)
    return owned, gold


def try_progress(path: List[str], owned: List[str], gold: int, minute: int) -> Tuple[List[str], int]:
    for step in path:
        if path_item_done(step, owned):
            continue
        if step == "Black Mist Scythe":
            continue
        if can_buy(step, owned, gold, minute):
            owned, gold = buy(step, owned, gold)
            continue
        for comp in NEXT_COMPONENTS.get(step, []):
            if comp in owned:
                continue
            if can_buy(comp, owned, gold, minute):
                owned, gold = buy(comp, owned, gold)
        if can_buy(step, owned, gold, minute):
            owned, gold = buy(step, owned, gold)
        else:
            break
    return owned, gold


def resolve_inventory(path: List[str], gold: int, minute: int, role: str) -> List[str]:
    owned: List[str] = []
    pocket = gold
    owned, pocket = try_progress(path, owned, pocket, minute)
    if role == "support" and minute >= 6 and "Spectral Sickle" in owned:
        owned, pocket = buy("Black Mist Scythe", owned, pocket)
    return owned


# ---------------------------------------------------------------------------
# Champion math (7.3 Senna)
# ---------------------------------------------------------------------------


def haste_cd_mult(ah: float) -> float:
    return 100.0 / (100.0 + max(0.0, ah))


def transcendence_ah(level: int) -> float:
    if level >= 5:
        return 12.0
    return 6.0


def skill_rank(level: int, skill: str) -> int:
    """Q max, W second. R at 6/11/15."""
    if skill == "R":
        if level < 6:
            return 0
        if level < 11:
            return 1
        if level < 15:
            return 2
        return 3
    q_lv = [1, 3, 5, 7, 9]
    w_lv = [2, 4, 8, 10, 12]
    mapping = {"Q": q_lv, "W": w_lv}
    return min(4, sum(1 for lv in mapping[skill] if level >= lv))


def q_damage(rank: int, bonus_ad: float) -> float:
    if rank <= 0:
        return 0.0
    return [0, 50, 80, 110, 140][rank] + 0.60 * bonus_ad


def q_heal(rank: int, bonus_ad: float, ap: float) -> float:
    if rank <= 0:
        return 0.0
    return [0, 40, 70, 100, 130][rank] + 0.40 * bonus_ad + 0.25 * ap


def w_damage(rank: int, bonus_ad: float) -> float:
    if rank <= 0:
        return 0.0
    return [0, 90, 155, 220, 285][rank] + 0.70 * bonus_ad


def living_extraction_pct(level: int) -> float:
    return 0.01 + 0.09 * (level - 1) / 14.0


def nightstalker_damage(level: int) -> float:
    return 60.0 + 100.0 * (level - 1) / 14.0


def magnetic_energized(level: int) -> float:
    return 40.0 + 60.0 * (level - 1) / 14.0


def senna_attack_speed(level: int, bonus_as: float) -> float:
    """7.3: base 0.4, ratio 0.4, base bonus 0.6, per-level 0.05."""
    level_as = 0.0
    for lv in range(2, level + 1):
        level_as += 0.05 * (0.7 + 0.04 * lv)
    return 0.40 + 0.40 * (0.60 + level_as + bonus_as)


def target_hp(level: int, minute: int) -> float:
    return 580.0 + 50.0 * level + 18.0 * minute


def armor_mult(flat_apen: float, pct_apen: float, level: int, minute: int) -> float:
    armor = 32.0 + 2.2 * level + (0.0 if minute < 12 else 18.0)
    effective = armor * (1.0 - min(0.45, pct_apen)) - flat_apen
    effective = max(8.0, effective)
    return 100.0 / (100.0 + effective)


def dh_souls_at(minute: int, role: str) -> int:
    """Souls driven by fight rate, not by the boot — isolate the boot delta."""
    if role != "adc":
        return 0
    souls = 0.0
    for t in range(1, minute + 1):
        if t <= 4:
            souls += 1.6
        elif t <= 10:
            souls += 4.2
        else:
            souls += 6.4
    return int(souls)


def q_interval(ah: float, aspd: float) -> float:
    """15s Q, each auto refunds 1s. Floor so refunds cannot zero the CD."""
    q_cd = max(4.5, 15.0 * haste_cd_mult(ah))
    return max(3.4, (q_cd - 1.0) / (1.0 + aspd))


# ---------------------------------------------------------------------------
# Snapshot
# ---------------------------------------------------------------------------


@dataclass
class Snapshot:
    minute: int
    build_name: str
    role: str
    items: List[str]
    gold: int
    level: int
    mist: float
    bonus_ad: float
    total_ad: float
    ah: float
    ap: float
    flat_apen: float
    pct_apen: float
    pen_mult: float
    q_per_min: float
    w_per_min: float
    flash_cd: float
    combo: float  # 8s fight damage (ADC execute / support poke+heal converted)
    heal: float  # ally+self heal in the same 8s window
    dh_proc: float
    notes: str = ""
    tags: Dict[str, bool] = field(default_factory=dict)


def stack_items(names: List[str]) -> Item:
    acc = Item(name="stack", cost=0)
    for n in names:
        it = ITEMS[n]
        acc.ad += it.ad
        acc.ah += it.ah
        acc.as_pct += it.as_pct
        acc.crit += it.crit
        acc.ap += it.ap
        acc.hp += it.hp
        acc.hsp += it.hsp
        acc.mana_regen_pct += it.mana_regen_pct
        acc.flat_apen += it.flat_apen
        acc.pct_apen = min(0.45, acc.pct_apen + it.pct_apen)
        acc.summoner_haste = max(acc.summoner_haste, it.summoner_haste)
        acc.drak = acc.drak or it.drak
        acc.collector = acc.collector or it.collector
        acc.serylda = acc.serylda or it.serylda
        acc.magnetic = acc.magnetic or it.magnetic
        acc.ardent = acc.ardent or it.ardent
        acc.helia = acc.helia or it.helia
        acc.harmonic = acc.harmonic or it.harmonic
    return acc


def compute_snapshot(build_name: str, path: List[str], minute: int, role: str) -> Snapshot:
    gold = gold_at_minute(minute, role)
    level = level_at_minute(minute, role)
    names = resolve_inventory(path, gold, minute, role)
    st = stack_items(names)
    ah = st.ah + transcendence_ah(level)
    mist = mist_at_minute(minute, role)
    mist_ad = mist * 1.25
    bonus_ad = st.ad + mist_ad
    total_ad = 50.0 + bonus_ad  # Relic Cannon: no AD/level
    crit = min(1.0, st.crit + 0.10 * (mist // 20.0))
    aspd = senna_attack_speed(level, st.as_pct + (0.30 if st.ardent else 0.0))
    pen = armor_mult(st.flat_apen, st.pct_apen, level, minute)
    qr, wr = skill_rank(level, "Q"), skill_rank(level, "W")

    interval = q_interval(ah, aspd)
    qpm = 60.0 / interval
    w_cd = max(4.0, 11.0 * haste_cd_mult(ah))
    wpm = 60.0 / w_cd
    flash = FLASH_BASE * haste_cd_mult(st.summoner_haste)

    window = 8.0
    q_casts = window / interval
    autos = aspd * window
    onhit = 0.20 * total_ad + (25.0 if st.ardent else 0.0)
    # Non-crit auto = 100% AD + Relic 20%. Crit = 90% of 200% AD + Relic.
    avg_auto = total_ad * (1.20 + crit * 0.80) + (25.0 if st.ardent else 0.0)

    q_raw = q_damage(qr, bonus_ad) + onhit
    w_raw = w_damage(wr, bonus_ad)
    hp = target_hp(level, minute)
    extract = living_extraction_pct(level) * 0.40 * hp  # consume at ~40% HP

    auto_land = 0.85 if role == "adc" else 0.40
    q_land = 0.90 if role == "adc" else 0.80
    w_land = 0.70 if role == "adc" else 0.55

    phys = (
        autos * auto_land * avg_auto
        + q_casts * q_land * q_raw
        + (1.0 if role == "adc" else 0.6) * extract
        + (window / w_cd) * w_land * w_raw * (0.35 if role == "adc" else 0.70)
    )
    if st.drak:
        phys += nightstalker_damage(level)
    combo = phys * pen
    if st.magnetic:
        combo += magnetic_energized(level) * (100.0 / (100.0 + 30.0 + level))
    if st.collector:
        combo += (0.05 + 0.02 * crit) * hp * 0.50
    if st.serylda:
        combo *= 1.03

    dh = 0.0
    if role == "adc":
        souls = dh_souls_at(minute, role)
        dh = (35.0 + 11.0 * souls + 0.10 * bonus_ad) * 0.80 * pen
        combo += dh

    heal = q_heal(qr, bonus_ad, st.ap) * (1.0 + st.hsp)
    ally = 1.55 if role == "support" else 0.35
    heals = heal * q_casts * (1.0 + ally)  # self always + ally land
    if st.helia:
        heals += min(80.0 + 170.0 * (level - 1) / 14.0, 0.22 * combo) * q_casts * 0.45
    if st.harmonic:
        heals *= 1.18

    notes_bits = []
    if any(n in T2_BOOTS for n in names) and not any(n in T3_BOOTS for n in names):
        notes_bits.append("T2 boots")
    if any(n in T3_BOOTS for n in names):
        notes_bits.append("T3 boots")
    if st.drak:
        notes_bits.append("Draktharr")
    if st.collector:
        notes_bits.append("Collector")
    if st.ardent:
        notes_bits.append("Ardent")
    if "Long Sword" in names:
        notes_bits.append("leftover Long Sword")
    if st.summoner_haste:
        notes_bits.append(f"Flash {flash:.0f}s")

    return Snapshot(
        minute=minute,
        build_name=build_name,
        role=role,
        items=names,
        gold=gold,
        level=level,
        mist=mist,
        bonus_ad=bonus_ad,
        total_ad=total_ad,
        ah=ah,
        ap=st.ap,
        flat_apen=st.flat_apen,
        pct_apen=st.pct_apen,
        pen_mult=pen,
        q_per_min=qpm,
        w_per_min=wpm,
        flash_cd=flash,
        combo=combo,
        heal=heals,
        dh_proc=dh,
        notes=", ".join(notes_bits),
        tags={
            "drak": st.drak,
            "collector": st.collector,
            "ardent": st.ardent,
            "t3": any(n in T3_BOOTS for n in names),
        },
    )


def run_build(name: str, path: List[str], role: str) -> List[Snapshot]:
    return [compute_snapshot(name, path, m, role) for m in range(1, GAME_MINUTES + 1)]


def area(snaps: List[Snapshot], attr: str) -> float:
    return sum(getattr(s, attr) for s in snaps)


def first_item_minute(snaps: List[Snapshot], item: str) -> Optional[int]:
    for s in snaps:
        if item in s.items:
            return s.minute
    return None


def item_short(names: List[str]) -> str:
    shown = " › ".join(names[:5])
    if len(names) > 5:
        shown += " › …"
    return shown


def pct_delta(a: float, b: float) -> str:
    if b <= 0:
        return "n/a"
    d = (a / b - 1.0) * 100.0
    return f"{d:+.1f}%"


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------


def summarize(results: Dict[str, List[Snapshot]]) -> str:
    adc_dyn = results["ADC · Dynamism → Armorcrusher"]
    adc_ion = results["ADC · Ionian → Crimson"]
    sup_dyn = results["Support · Dynamism → Armorcrusher"]
    sup_ion = results["Support · Ionian → Crimson"]

    lines: List[str] = []
    lines.append("=" * 78)
    lines.append("SENNA — IONIAN vs BOOTS OF DYNAMISM (Wild Rift 7.3)")
    lines.append("Same core, only the boot line. 20:00. Transcendence on both paths.")
    lines.append("ADC core: Draktharr → Collector → Magnetic. Support: Ardent → Helia → Harmonic.")
    lines.append("=" * 78)
    lines.append("")
    lines.append("BOOT STATS (7.2 / 7.2a — unchanged in 7.3 notes)")
    lines.append("-" * 78)
    lines.append("  T2 Ionian    1000g  15 AH, 15% summoner haste. Recipe: Speed + Ring + 300.")
    lines.append("  T2 Dynamism  1200g  15 AD, 10 flat armor pen. Recipe: Speed + Long Sword + 300.")
    lines.append("  T3 Crimson   2000g  after 10:00. 25 AH, 75% mana regen, 20% summoner haste,")
    lines.append("                      8% MS (ranged) after Q/heal/Flash.")
    lines.append("  T3 Armorcrusher 2200g after 10:00. 20 AD, 10 flat + 6% pen, 20 OOC MS.")
    lines.append("  7.2a Armorcrusher nerf: AD 25→20, flat pen 12→10. 6% pen stayed.")
    lines.append("  Ionia is the BOOT. Ability haste also comes from Transcendence, Draktharr,")
    lines.append("  Helia, Harmonic, Serylda — do not treat 'needs HA' as 'buy Ionia'.")
    lines.append("")
    lines.append("  Gold @20: ADC %d  Support %d" % (adc_gold(20), support_gold(20)))
    lines.append("")

    def table_role(title: str, dyn: List[Snapshot], ion: List[Snapshot], metric: str) -> None:
        lines.append("-" * 78)
        lines.append(title)
        lines.append("-" * 78)
        lines.append(
            f"  {'Min':>4}  {'Dyn':>7}  {'Ionia':>7}  {'Δ':>7}  {'Q/m D':>6}  {'Q/m I':>6}  "
            f"{'FlashD':>6}  {'FlashI':>6}  winner"
        )
        wins_dyn = 0
        for a, b in zip(dyn, ion):
            va, vb = getattr(a, metric), getattr(b, metric)
            winner = "DYN" if va >= vb else "IONIA"
            if va >= vb:
                wins_dyn += 1
            lines.append(
                f"  {a.minute:>3}:00  {va:>7.0f}  {vb:>7.0f}  {pct_delta(va, vb):>7}  "
                f"{a.q_per_min:>6.1f}  {b.q_per_min:>6.1f}  "
                f"{a.flash_cd:>6.0f}  {b.flash_cd:>6.0f}  {winner}"
            )
            if a.minute in (6, 8, 10, 12, 14, 16, 18, 20):
                lines.append(f"         Dyn  : {item_short(a.items)}")
                lines.append(f"         Ionia: {item_short(b.items)}")
        lines.append("")
        lines.append(
            f"  Combat area 20p: Dyn {area(dyn, metric):.0f}  vs  Ionia {area(ion, metric):.0f}  "
            f"({pct_delta(area(dyn, metric), area(ion, metric))})"
        )
        lines.append(
            f"  Q/min area:      Dyn {area(dyn, 'q_per_min'):.1f}  vs  Ionia {area(ion, 'q_per_min'):.1f}  "
            f"(Ionia {pct_delta(area(ion, 'q_per_min'), area(dyn, 'q_per_min'))})"
        )
        lines.append(f"  Dyn wins {wins_dyn}/20 minutes on {metric}.")
        lines.append(
            f"  T2 spike: Dynamism ~{first_item_minute(dyn, 'Boots of Dynamism')}:00  "
            f"Ionian ~{first_item_minute(ion, 'Ionian Boots of Lucidity')}:00"
        )
        lines.append(
            f"  T3 spike: Armorcrusher ~{first_item_minute(dyn, 'Armorcrusher Boots')}:00  "
            f"Crimson ~{first_item_minute(ion, 'Crimson Lucidity')}:00"
        )

    table_role(
        "ADC — 8s execute window (AA→Q + Relic + DH + Nightstalker). Souls equal across boots.",
        adc_dyn,
        adc_ion,
        "combo",
    )
    lines.append(
        f"  Draktharr: Dyn ~{first_item_minute(adc_dyn, 'Duskblade of Draktharr')}:00  "
        f"Ionia ~{first_item_minute(adc_ion, 'Duskblade of Draktharr')}:00"
    )
    lines.append(
        f"  Collector: Dyn ~{first_item_minute(adc_dyn, 'The Collector')}:00  "
        f"Ionia ~{first_item_minute(adc_ion, 'The Collector')}:00"
    )
    lines.append("")

    table_role(
        "SUPPORT — 8s window damage (Q poke + autos + W). Heal is scored separately.",
        sup_dyn,
        sup_ion,
        "combo",
    )
    lines.append(
        f"  Heal area 20p: Dyn {area(sup_dyn, 'heal'):.0f}  vs  Ionia {area(sup_ion, 'heal'):.0f}  "
        f"(Ionia {pct_delta(area(sup_ion, 'heal'), area(sup_dyn, 'heal'))})"
    )
    lines.append(
        f"  W/min area:    Dyn {area(sup_dyn, 'w_per_min'):.1f}  vs  Ionia {area(sup_ion, 'w_per_min'):.1f}  "
        f"(Ionia {pct_delta(area(sup_ion, 'w_per_min'), area(sup_dyn, 'w_per_min'))})"
    )
    lines.append(
        f"  Ardent: Dyn ~{first_item_minute(sup_dyn, 'Ardent Censer')}:00  "
        f"Ionia ~{first_item_minute(sup_ion, 'Ardent Censer')}:00"
    )
    lines.append("")

    adc_dyn_area = area(adc_dyn, "combo")
    adc_ion_area = area(adc_ion, "combo")
    sup_dyn_area = area(sup_dyn, "combo")
    sup_ion_area = area(sup_ion, "combo")
    sup_ion_heal = area(sup_ion, "heal")
    sup_dyn_heal = area(sup_dyn, "heal")

    lines.append("-" * 78)
    lines.append("VERDICT")
    lines.append("-" * 78)
    if adc_dyn_area > adc_ion_area:
        lines.append(
            f"  ADC / flex DH: Boots of Dynamism → Armorcrusher "
            f"({pct_delta(adc_dyn_area, adc_ion_area)} combat area)."
        )
    else:
        lines.append(
            f"  ADC / flex DH: Ionian → Crimson "
            f"({pct_delta(adc_ion_area, adc_dyn_area)} combat area)."
        )
    lines.append(
        f"  Support: damage {pct_delta(sup_dyn_area, sup_ion_area)} Dynamism, "
        f"heal {pct_delta(sup_ion_heal, sup_dyn_heal)} Ionian, "
        f"Q/min {pct_delta(area(sup_ion, 'q_per_min'), area(sup_dyn, 'q_per_min'))} Ionian."
    )
    lines.append("")
    lines.append("  WHY THE ROLE SPLIT HOLDS:")
    lines.append("  1) Dynamism is AD + pen. Senna's Q, autos, Relic Cannon, Living Extraction,")
    lines.append("     and Dark Harvest (10% bonus AD) are all physical. Pen multiplies the kit.")
    lines.append("  2) Ionian is 15 AH. Transcendence already gives 12. Draktharr adds 10.")
    lines.append("     Helia + Harmonic add 40 more on support. Extra Q/min is real, smaller")
    lines.append("     than 15 AD + 10 pen on a champion whose damage is auto+Q.")
    lines.append("  3) Dynamism eats the Long Sword ADC already bought — T2 at 2:00,")
    lines.append("     Draktharr 8:00. Ionia does not use that sword, so 500g sits leftover")
    lines.append("     and Draktharr slips to 9:00, Collector to 14:00. Support has to BUY")
    lines.append("     a Long Sword just for Dynamism; Ardent still ~9:00, T3 16:00 vs 15:00.")
    lines.append("  4) Ionian Flash (T2 15% / Crimson 20%) is the support reason, not DPS.")
    lines.append("     150s → ~130s → 125s. W roots and Q heals also scale with haste.")
    lines.append("  5) Armorcrusher's 6% pen is the T3 identity. Crimson's T3 identity is")
    lines.append("     Flash + MS after Q heal — peel, not execute.")
    lines.append("")
    lines.append("  BUY DYNAMISM WHEN:")
    lines.append("  • Bot / flex carry, Dark Harvest, you auto then Q (AA→Q).")
    lines.append("  • First legendary is Draktharr / Collector / Youmuu — pen stacks.")
    lines.append("  • You already have a Long Sword in lane.")
    lines.append("")
    lines.append("  BUY IONIAN WHEN:")
    lines.append("  • Support. Q is a heal. Flash + W root are the job.")
    lines.append("  • You already hit haste from Helia / Harmonic / Mandate and still want")
    lines.append("    Flash 125s more than 20 AD.")
    lines.append("  • You cannot auto (max-range poke/heal only) — then AH is the damage stat.")
    lines.append("")
    lines.append("  TRAPS:")
    lines.append("  • 'Senna needs haste' → Ionia. She needs Q uptime. Autos already refund")
    lines.append("    1s. Transcendence + Draktharr/Helia cover most of the 15 AH.")
    lines.append("  • Copying ADC Dynamism onto support. Heal/Q/W/Flash lose; damage is selfish.")
    lines.append("  • Copying support Ionia onto DH carry. Leftover Long Sword delays Draktharr;")
    lines.append("    0 pen until Collector/Serylda.")
    lines.append("  • Buying T3 before 10:00 — the shop will not allow it.")
    lines.append("=" * 78)
    return "\n".join(lines)


def export_json(results: Dict[str, List[Snapshot]], path: str) -> None:
    payload = {
        "meta": {
            "champion": "Senna",
            "patch": "7.3",
            "question": "Ionian vs Boots of Dynamism, same core",
            "game_minutes": GAME_MINUTES,
            "sources": {
                "boots_t2": "WR 7.2 patch notes (Dynamism 1200g 15 AD 10 pen; Ionian 1000g 15 AH)",
                "armorcrusher": "WR 7.2a nerf: 20 AD, 10 flat, 6% pen, 2200g",
                "crimson": "WR 7.2: 25 AH, 75% regen, 20% summoner haste, 2000g",
                "senna": "WR 7.3: Q 50/80/110/140, mist crit 10%/20 stacks, 90% crit damage",
            },
        },
        "builds": {
            name: [
                {
                    "minute": s.minute,
                    "items": s.items,
                    "gold": s.gold,
                    "level": s.level,
                    "mist": s.mist,
                    "bonus_ad": s.bonus_ad,
                    "ah": s.ah,
                    "flat_apen": s.flat_apen,
                    "pct_apen": s.pct_apen,
                    "pen_mult": s.pen_mult,
                    "q_per_min": s.q_per_min,
                    "w_per_min": s.w_per_min,
                    "flash_cd": s.flash_cd,
                    "combo": s.combo,
                    "heal": s.heal,
                    "dh_proc": s.dh_proc,
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
    adc_dyn = results["ADC · Dynamism → Armorcrusher"]
    adc_ion = results["ADC · Ionian → Crimson"]
    sup_dyn = results["Support · Dynamism → Armorcrusher"]
    sup_ion = results["Support · Ionian → Crimson"]

    for snaps in results.values():
        for s in snaps:
            if s.minute < T3_BOOTS_MINUTE:
                assert "Armorcrusher Boots" not in s.items, s
                assert "Crimson Lucidity" not in s.items, s
        golds = [s.gold for s in snaps]
        assert golds == sorted(golds)

    # ADC already bought Long Sword — Dynamism credits it, so T2 completes first.
    t_dyn = first_item_minute(adc_dyn, "Boots of Dynamism")
    t_ion = first_item_minute(adc_ion, "Ionian Boots of Lucidity")
    assert t_ion and t_dyn and t_dyn <= t_ion, (t_dyn, t_ion)

    # Support has no Long Sword. Ionian is the cheaper T2 (1000 vs 1200).
    st_dyn = first_item_minute(sup_dyn, "Boots of Dynamism")
    st_ion = first_item_minute(sup_ion, "Ionian Boots of Lucidity")
    assert st_ion and st_dyn and st_ion <= st_dyn, (st_ion, st_dyn)

    assert "Armorcrusher Boots" in adc_dyn[19].items
    assert "Crimson Lucidity" in adc_ion[19].items

    # Leftover Long Sword is the Ionian ADC tax — Dynamism consumed it.
    assert "Long Sword" in adc_ion[7].items
    assert "Long Sword" not in adc_dyn[7].items

    # Haste is real — Ionian must cast more Q.
    assert area(adc_ion, "q_per_min") > area(adc_dyn, "q_per_min")
    assert area(sup_ion, "q_per_min") > area(sup_dyn, "q_per_min")

    # Flash haste is Ionian-only.
    assert adc_ion[19].flash_cd < adc_dyn[19].flash_cd
    assert abs(adc_dyn[19].flash_cd - FLASH_BASE) < 1e-6

    # Dynamism is the pen boot.
    assert adc_dyn[19].flat_apen > adc_ion[19].flat_apen
    assert adc_dyn[19].pct_apen > adc_ion[19].pct_apen

    # ADC damage should follow the pen/AD boot once cores match.
    assert area(adc_dyn, "combo") > area(adc_ion, "combo")

    # Support heals follow Q count — Ionian.
    assert area(sup_ion, "heal") > area(sup_dyn, "heal")


def main() -> None:
    results = {
        name: run_build(name, path, ROLE_OF[name])
        for name, path in BUILD_PATHS.items()
    }
    self_check(results)
    report = summarize(results)
    print(report)
    with open(os.path.join(OUT_DIR, "report.txt"), "w", encoding="utf-8") as f:
        f.write(report + "\n")
    export_json(results, os.path.join(OUT_DIR, "results.json"))
    print(f"\nWrote {OUT_DIR}/report.txt and {OUT_DIR}/results.json")


if __name__ == "__main__":
    main()
