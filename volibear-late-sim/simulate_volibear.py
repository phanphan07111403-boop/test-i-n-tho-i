#!/usr/bin/env python3
"""
PC League of Legends — Volibear top, patch 26.21.

Question: the most late-game Volibear who is hard to kill and still
deals high damage. Not a pure tank, not a glass bite.

Kit facts the build has to respect (wiki, V26.19–26.21):
  W  105 + 110% AD + 6% bonus HP. The wounded bite multiplies that by
     1.50 + 0.25 per 100 bonus AD, and heals 80 + 20% missing HP.
  Q  50 + 160% bonus AD on the pounce.
  E  200 + 70% AP + 15% target max HP. Shield is 14% max HP + 75% AP.
  R  700 + 250% bonus AD + 125% AP, and +525 bonus HP for 12s.
  Passive lightning at 5 stacks: 68 + 20% bonus AD + 45% AP.

Health that does not become AD never multiplies the bite. AD that does
not come with health, haste, and a heal amp dies when the fight focuses him.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple
import itertools
import json
import os
import time

HERE = os.path.dirname(os.path.abspath(__file__))
GAME_MINUTES = 34
DT = 0.1
COMBAT = 11.0  # seconds of being focused, inside the 12s ultimate

# Late-game focus: one crit carry plus one mage, for the whole window.
# Tuned so a real bruiser lives the ultimate and a glass build does not.
PHYS_DPS = 980.0
MAGIC_DPS = 640.0
BASE_CC = 1.15  # one peel spell as he lands, reduced by tenacity


@dataclass
class Item:
    name: str
    cost: int
    ad: float = 0.0
    ap: float = 0.0
    ah: float = 0.0
    hp: float = 0.0
    armor: float = 0.0
    mr: float = 0.0
    as_pct: float = 0.0
    crit: float = 0.0
    armor_pen: float = 0.0
    magic_pen: float = 0.0
    flat_mpen: float = 0.0
    lifesteal: float = 0.0
    omnivamp: float = 0.0
    tenacity: float = 0.0
    mana: float = 0.0
    tags: Tuple[str, ...] = ()
    recipe: Tuple[str, ...] = ()


def I(name, cost, recipe=(), **kw) -> Item:
    tags = tuple(kw.pop("tags", ()))
    return Item(name=name, cost=cost, recipe=tuple(recipe), tags=tags, **kw)


ITEMS: Dict[str, Item] = {}


def add(it: Item) -> None:
    ITEMS[it.name] = it


# --- components ---
add(I("Boots", 300))
add(I("Dagger", 250, as_pct=0.10))
add(I("Long Sword", 350, ad=10))
add(I("Ruby Crystal", 400, hp=150))
add(I("Cloth Armor", 300, armor=15))
add(I("Null-Magic Mantle", 400, mr=20))
add(I("Glowing Mote", 250, ah=5))
add(I("Amplifying Tome", 400, ap=20))
add(I("Pickaxe", 875, ad=25))
add(I("Blasting Wand", 850, ap=45))
add(I("Needlessly Large Rod", 1200, ap=65))
add(I("Cloak of Agility", 600, crit=0.15))
add(I("Chain Vest", 800, armor=40))
add(I("Negatron Cloak", 850, mr=45))
add(I("Giant's Belt", 900, hp=350))
add(I("Recurve Bow", 700, as_pct=0.15))
add(I("Tunneler", 1150, ad=15, hp=250))
add(I("Kindlegem", 800, ah=10, hp=200))
add(I("Caulfield's Warhammer", 1050, ad=20, ah=10))
add(I("Phage", 1100, ad=15, hp=200))
add(I("Sheen", 900, ah=10, tags=("sheen",)))
add(I("Hearthbound Axe", 1200, ad=20, as_pct=0.20))
add(I("Fiendish Codex", 850, ap=25, ah=10))
add(I("Haunting Guise", 1300, ap=30, hp=200))
add(I("Fated Ashes", 900, ap=30))
add(I("Spectre's Cowl", 1250, hp=200, mr=35))
add(I("Crystalline Bracer", 800, hp=200))
add(I("Bami's Cinder", 900, hp=150, ah=5, tags=("bami",)))
add(I("Winged Moonplate", 800, hp=200))
add(I("Warden's Mail", 1000, armor=40))
add(I("Tear of the Goddess", 400, mana=240))
add(I("Last Whisper", 1450, ad=20, armor_pen=0.18))
add(I("Vampiric Scepter", 900, ad=15, lifesteal=0.07))
add(I("Zeal", 1200, as_pct=0.15, crit=0.15))
add(I("Seeker's Armguard", 1600, ap=40, armor=25))
add(I("Blighting Jewel", 1100, ap=25, magic_pen=0.13))
add(I("Hextech Alternator", 1100, ap=45))
add(I("Aether Wisp", 900, ap=30))
add(I("Steel Sigil", 1100, ad=15, armor=30))
add(I("Tiamat", 1200, ad=20))

# --- boots and legendaries (patch 26.21 stat pass) ---
add(I("Plated Steelcaps", 1200, recipe=("Boots", "Cloth Armor"), armor=25, tags=("boots", "steelcaps")))
add(I("Mercury's Treads", 1250, recipe=("Boots", "Null-Magic Mantle"), mr=20, tenacity=0.30, tags=("boots", "mercs")))
add(I("Ionian Boots of Lucidity", 900, recipe=("Boots", "Glowing Mote"), ah=10, tags=("boots", "ionian")))

add(I("Spear of Shojin", 3100, recipe=("Pickaxe", "Tunneler", "Ruby Crystal"), ad=45, hp=450, tags=("shojin",)))
add(I("Overlord's Bloodmail", 3300, recipe=("Tunneler", "Tunneler"), ad=30, hp=550, tags=("bloodmail",)))
add(I("Sterak's Gage", 3200, recipe=("Pickaxe", "Tunneler", "Ruby Crystal"), hp=400, tenacity=0.20, tags=("sterak",)))
add(I("Spirit Visage", 2700, recipe=("Spectre's Cowl", "Kindlegem"), ah=10, hp=400, mr=50, tags=("visage",)))
add(I("Unending Despair", 2800, recipe=("Chain Vest", "Kindlegem", "Ruby Crystal"), ah=15, hp=400, armor=50, tags=("unending",)))
add(I("Heartsteel", 3000, recipe=("Giant's Belt", "Crystalline Bracer", "Giant's Belt"), hp=900, tags=("heartsteel",)))
add(I("Titanic Hydra", 3300, recipe=("Tiamat", "Tunneler", "Giant's Belt"), ad=40, hp=600, tags=("titanic",)))
add(I("Jak'Sho, The Protean", 3200, recipe=("Giant's Belt", "Chain Vest", "Negatron Cloak"), hp=350, armor=45, mr=45, tags=("jaksho",)))
add(I("Death's Dance", 3300, recipe=("Steel Sigil", "Caulfield's Warhammer", "Pickaxe"), ad=60, ah=15, armor=50, tags=("dd",)))
add(I("Trinity Force", 3333, recipe=("Sheen", "Phage", "Hearthbound Axe"), ad=36, ah=15, as_pct=0.30, hp=333, tags=("trinity",)))
add(I("Sundered Sky", 3100, recipe=("Tunneler", "Caulfield's Warhammer"), ad=40, ah=10, hp=400, tags=("sundered",)))
add(I("Endless Hunger", 3100, recipe=("Caulfield's Warhammer", "Pickaxe", "Long Sword"), ad=65, omnivamp=0.05, tenacity=0.20, tags=("endless",)))
add(I("Black Cleaver", 3000, recipe=("Phage", "Kindlegem", "Pickaxe"), ad=45, ah=20, hp=400, tags=("cleaver",)))
add(I("Dusk and Dawn", 3100, recipe=("Sheen", "Blasting Wand", "Kindlegem", "Dagger"), ap=60, ah=20, as_pct=0.20, hp=300, tags=("dusk",)))
add(I("Riftmaker", 3100, recipe=("Haunting Guise", "Fiendish Codex"), ap=70, ah=15, hp=350, tags=("riftmaker",)))
add(I("Nashor's Tooth", 2900, recipe=("Recurve Bow", "Blasting Wand", "Fiendish Codex"), ap=80, ah=15, as_pct=0.50, tags=("nashor",)))
add(I("Rabadon's Deathcap", 3500, recipe=("Needlessly Large Rod", "Needlessly Large Rod"), ap=130, tags=("deathcap",)))
add(I("Zhonya's Hourglass", 3250, recipe=("Seeker's Armguard", "Needlessly Large Rod"), ap=105, armor=50, tags=("zhonya",)))
add(I("Liandry's Torment", 3000, recipe=("Fated Ashes", "Haunting Guise"), ap=60, hp=300, tags=("liandry",)))
add(I("Navori Flickerblade", 2650, recipe=("Dagger", "Zeal", "Dagger"), as_pct=0.40, crit=0.25, tags=("navori",)))
add(I("Iceborn Gauntlet", 2900, recipe=("Sheen", "Ruby Crystal", "Chain Vest"), ah=15, hp=300, armor=50, tags=("ibg",)))
add(I("Sunfire Aegis", 2800, recipe=("Bami's Cinder", "Chain Vest", "Ruby Crystal"), ah=10, hp=350, armor=50, tags=("sunfire",)))
add(I("Thornmail", 2450, recipe=("Chain Vest", "Ruby Crystal", "Cloth Armor"), hp=150, armor=75, tags=("thornmail",)))
add(I("Randuin's Omen", 2700, recipe=("Warden's Mail", "Giant's Belt", "Cloth Armor"), hp=350, armor=75, tags=("randuin",)))
add(I("Force of Nature", 2800, recipe=("Negatron Cloak", "Ruby Crystal", "Winged Moonplate"), hp=400, mr=55, tags=("fon",)))
add(I("Kaenic Rookern", 2900, recipe=("Negatron Cloak", "Kindlegem", "Ruby Crystal"), hp=400, mr=80, tags=("kaenic",)))
add(I("Blade of the Ruined King", 3200, recipe=("Vampiric Scepter", "Recurve Bow", "Pickaxe"), ad=40, as_pct=0.25, lifesteal=0.10, tags=("bork",)))
add(I("Serylda's Grudge", 3000, recipe=("Last Whisper", "Caulfield's Warhammer"), ad=45, ah=15, armor_pen=0.35, tags=("serylda",)))
add(I("Lord Dominik's Regards", 3300, recipe=("Last Whisper", "Cloak of Agility", "Pickaxe"), ad=35, crit=0.25, armor_pen=0.35, tags=("ldr",)))
add(I("Terminus", 3000, recipe=("Recurve Bow", "Pickaxe", "Dagger"), ad=30, as_pct=0.35, tags=("terminus",)))
add(I("Wit's End", 2800, recipe=("Recurve Bow", "Negatron Cloak", "Dagger"), as_pct=0.50, mr=45, tenacity=0.20, tags=("wits",)))
add(I("Guinsoo's Rageblade", 3000, recipe=("Recurve Bow", "Amplifying Tome", "Pickaxe"), ad=30, ap=30, as_pct=0.25, tags=("guinsoo",)))
add(I("Void Staff", 3000, recipe=("Blighting Jewel", "Blasting Wand"), ap=95, magic_pen=0.40, tags=("void",)))
add(I("Shadowflame", 3200, recipe=("Hextech Alternator", "Needlessly Large Rod"), ap=110, flat_mpen=15, tags=("shadowflame",)))
add(I("Cosmic Drive", 3000, recipe=("Kindlegem", "Fiendish Codex", "Aether Wisp"), ap=70, ah=25, hp=350, tags=("cosmic",)))
add(I("Warmog's Armor", 3100, recipe=("Giant's Belt", "Giant's Belt", "Crystalline Bracer"), hp=1000, tags=("warmog",)))
add(I("Abyssal Mask", 2650, recipe=("Negatron Cloak", "Kindlegem", "Ruby Crystal"), ah=15, hp=350, mr=45, tags=("abyssal",)))
add(I("Fimbulwinter", 2400, recipe=("Tear of the Goddess", "Kindlegem", "Giant's Belt"), ah=15, hp=550, mana=1000, tags=("fimbul",)))
add(I("Frozen Heart", 2500, ah=20, armor=75, mana=400, tags=("frozen",)))
add(I("Dead Man's Plate", 2900, hp=350, armor=55, tags=("deadman",)))
add(I("Hullbreaker", 3000, ad=40, hp=500, tags=("hull",)))
add(I("Stridebreaker", 3300, recipe=("Hearthbound Axe", "Phage", "Ruby Crystal"), ad=40, as_pct=0.25, hp=450, tags=("stride",)))
add(I("Hexdrinker", 1300, recipe=("Long Sword", "Null-Magic Mantle", "Long Sword"), ad=25, mr=30))
add(I("Statikk Shiv", 3000, recipe=("Pickaxe", "Aether Wisp"), ad=45, ap=45, as_pct=0.30, tags=("statikk",)))
add(I("Experimental Hexplate", 3000, recipe=("Tunneler", "Phage", "Dagger"), ad=40, as_pct=0.20, hp=450, tags=("hexplate",)))
add(I("Maw of Malmortius", 3100, recipe=("Hexdrinker", "Caulfield's Warhammer"), ad=60, ah=15, mr=40, tags=("maw", "lifeline")))
add(I("Protoplasm Harness", 2600, recipe=("Kindlegem", "Giant's Belt"), ah=20, hp=600, tags=("protoplasm", "lifeline")))
add(I("Eclipse", 2900, recipe=("Caulfield's Warhammer", "Pickaxe", "Long Sword"), ad=60, ah=15, tags=("eclipse",)))
add(I("Ravenous Hydra", 3300, recipe=("Tiamat", "Vampiric Scepter", "Caulfield's Warhammer"), ad=65, ah=15, lifesteal=0.12, tags=("ravenous", "hydra")))
add(I("Hextech Gunblade", 3000, recipe=("Pickaxe", "Needlessly Large Rod"), ad=40, ap=80, omnivamp=0.10, tags=("gunblade",)))
add(I("Berserker's Greaves", 1100, recipe=("Boots", "Dagger"), as_pct=0.30, tags=("boots", "zerker")))
add(I("Gunmetal Greaves", 1100, recipe=("Boots", "Dagger"), as_pct=0.45, lifesteal=0.05, tags=("boots", "gunmetal")))

BOOTS = (
    "Plated Steelcaps",
    "Mercury's Treads",
    "Ionian Boots of Lucidity",
    "Berserker's Greaves",
    "Gunmetal Greaves",
)
SPELLBLADES = ("Trinity Force", "Dusk and Dawn", "Iceborn Gauntlet")
LIFELINES = ("Sterak's Gage", "Maw of Malmortius", "Protoplasm Harness")
HYDRAS = ("Titanic Hydra", "Ravenous Hydra")
AS_BASE = 0.625
AS_RATIO = 0.7  # Volibear. Total AS = base + bonus_AS * ratio.
AS_CAP = 3.003
LEGENDARIES: Tuple[str, ...] = tuple(
    n for n, it in ITEMS.items() if it.tags and "boots" not in it.tags and it.cost >= 2400
)

SHORT = {
    "Plated Steelcaps": "Steelcaps",
    "Mercury's Treads": "Mercs",
    "Ionian Boots of Lucidity": "Ionian",
    "Spear of Shojin": "Shojin",
    "Overlord's Bloodmail": "Bloodmail",
    "Sterak's Gage": "Sterak",
    "Spirit Visage": "Visage",
    "Unending Despair": "Unending",
    "Heartsteel": "Heartsteel",
    "Titanic Hydra": "Titanic",
    "Jak'Sho, The Protean": "Jak'Sho",
    "Death's Dance": "DD",
    "Trinity Force": "Trinity",
    "Sundered Sky": "Sundered",
    "Endless Hunger": "Endless",
    "Black Cleaver": "Cleaver",
    "Dusk and Dawn": "Dusk",
    "Riftmaker": "Riftmaker",
    "Nashor's Tooth": "Nashor",
    "Rabadon's Deathcap": "Deathcap",
    "Zhonya's Hourglass": "Zhonya",
    "Liandry's Torment": "Liandry",
    "Navori Flickerblade": "Navori",
    "Iceborn Gauntlet": "IBG",
    "Sunfire Aegis": "Sunfire",
    "Thornmail": "Thornmail",
    "Randuin's Omen": "Randuin",
    "Force of Nature": "FoN",
    "Kaenic Rookern": "Kaenic",
    "Blade of the Ruined King": "BotRK",
    "Serylda's Grudge": "Serylda",
    "Lord Dominik's Regards": "LDR",
    "Terminus": "Terminus",
    "Wit's End": "Wit's End",
    "Guinsoo's Rageblade": "Guinsoo",
    "Void Staff": "Void",
    "Shadowflame": "Shadowflame",
    "Cosmic Drive": "Cosmic",
    "Warmog's Armor": "Warmog",
    "Abyssal Mask": "Abyssal",
    "Fimbulwinter": "Fimbul",
    "Frozen Heart": "Frozen Heart",
    "Dead Man's Plate": "Dead Man",
    "Hullbreaker": "Hullbreaker",
    "Stridebreaker": "Stride",
    "Statikk Shiv": "Statikk",
    "Experimental Hexplate": "Hexplate",
    "Maw of Malmortius": "Maw",
    "Protoplasm Harness": "Protoplasm",
    "Eclipse": "Eclipse",
    "Ravenous Hydra": "Ravenous",
    "Hextech Gunblade": "Gunblade",
    "Berserker's Greaves": "Zerks",
    "Gunmetal Greaves": "Gunmetal",
}


def short(name: str) -> str:
    return SHORT.get(name, name)


def show(items: Sequence[str]) -> str:
    boots = [short(i) for i in items if i in BOOTS]
    legs = [short(i) for i in items if i not in BOOTS]
    return " → ".join(boots + legs)


SKILL_ORDER = "QWEWWRWEWEREEQQRQQ"
W_BASE = (0, 5, 30, 55, 80, 105)
W_HEAL = (0, 20, 35, 50, 65, 80)
W_HEAL_PCT = (0, 0.08, 0.11, 0.14, 0.17, 0.20)
Q_BASE = (0, 10, 20, 30, 40, 50)
Q_CD = (0, 12.0, 11.5, 11.0, 10.5, 10.0)
E_BASE = (0, 80, 110, 140, 170, 200)
E_HP = (0, 0.11, 0.12, 0.13, 0.14, 0.15)
R_BASE = (0, 300, 500, 700)
R_HP = (0, 175, 350, 525)
R_CD = (0, 160.0, 135.0, 110.0)


def gold_at_minute(m: int) -> int:
    """Farming top. ~13.9k at 28:00, full bruiser build finishes ~33:00."""
    if m <= 0:
        return 500
    total = 500
    for t in range(1, m + 1):
        if t <= 4:
            total += 330
        elif t <= 10:
            total += 410
        elif t <= 16:
            total += 490
        elif t <= 24:
            total += 540
        else:
            total += 580
    return total


def growth_mult(level: int) -> float:
    """Riot growth: g * (n-1) * (0.7025 + 0.0175 * (n-1)). Equals (n-1) at level 18."""
    n = max(0, level - 1)
    return n * (0.7025 + 0.0175 * n)


def level_at_minute(m: int) -> int:
    table = {
        1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 7, 8: 8, 9: 9, 10: 10,
        11: 11, 12: 11, 13: 12, 14: 12, 15: 13, 16: 13, 17: 14, 18: 14,
        19: 15, 20: 15, 21: 16, 22: 16, 23: 16, 24: 17, 25: 17, 26: 17,
        27: 18, 28: 18, 29: 18, 30: 18, 31: 18, 32: 18, 33: 18, 34: 18,
    }
    return table.get(m, 18)


def skill_ranks(level: int) -> Dict[str, int]:
    counts = {"Q": 0, "W": 0, "E": 0, "R": 0}
    for ch in SKILL_ORDER[: max(0, min(18, level))]:
        counts[ch] += 1
    return counts


def conq_values(level: int) -> Tuple[float, float]:
    """Fully stacked Conqueror. Wiki: 12.96–30.66 AD or 21.6–51.11 AP."""
    t = (level - 1) / 17.0
    return 12.96 + (30.66 - 12.96) * t, 21.6 + (51.11 - 21.6) * t


class Build:
    """Resolved combat stats for one inventory."""

    def __init__(
        self,
        names: Sequence[str],
        level: int,
        minute: int,
        hs_procs: int,
        with_r: bool,
        keystone: str = "conqueror",
        legend: str = "haste",
        secondary: str = "conditioning",
    ):
        self.names = list(names)
        self.level = level
        self.tags = set()
        ad = ap = ah = hp = armor = mr = as_pct = crit = 0.0
        ls = ov = mana = flat_mpen = 0.0
        ten_mult = 1.0
        self.armor_pens: List[float] = []
        self.magic_pens: List[float] = []
        for n in names:
            it = ITEMS[n]
            ad += it.ad
            ap += it.ap
            ah += it.ah
            hp += it.hp
            armor += it.armor
            mr += it.mr
            as_pct += it.as_pct
            crit += it.crit
            ls += it.lifesteal
            ov += it.omnivamp
            mana += it.mana
            flat_mpen += it.flat_mpen
            if it.armor_pen:
                self.armor_pens.append(it.armor_pen)
            if it.magic_pen:
                self.magic_pens.append(it.magic_pen)
            if it.tenacity:
                ten_mult *= 1.0 - it.tenacity
            self.tags.update(it.tags)

        grown = growth_mult(level)
        self.base_hp = 650 + 104 * grown
        self.base_ad = 65 + 3.5 * grown
        self.base_armor = 35 + 5.2 * grown
        self.base_mr = 32 + 2.05 * grown
        self.base_mana = 350 + 70 * grown + mana
        self.keystone = keystone
        self.legend = legend
        self.secondary = secondary
        self.conq_frac = 1.0

        ranks = skill_ranks(level)
        self.q_rank = ranks["Q"]
        self.w_rank = ranks["W"]
        self.e_rank = ranks["E"]
        self.r_rank = ranks["R"]

        hp_now = self.base_hp + hp + 65.0
        self.hs_hp = 0.0
        if "heartsteel" in self.tags and hs_procs > 0:
            for _ in range(hs_procs):
                grant = 7.0 + 0.006 * hp_now
                self.hs_hp += grant
                hp_now += grant
        og_frac = 1.0 if minute >= 18 else max(0.0, minute) / 18.0
        self.overgrowth = 0.035 * og_frac * hp_now
        self.bonus_hp = hp + 65.0 + self.hs_hp + self.overgrowth
        self.r_hp = R_HP[self.r_rank] if with_r and self.r_rank else 0.0
        self.bonus_hp += self.r_hp
        self.max_hp = self.base_hp + self.bonus_hp

        self.sterak_ad = 0.50 * self.base_ad if "sterak" in self.tags else 0.0
        self.tyranny = 0.025 * self.bonus_hp if "bloodmail" in self.tags else 0.0
        rift_ap = 0.02 * self.bonus_hp if "riftmaker" in self.tags else 0.0
        item_bonus_ad = ad + self.sterak_ad + self.tyranny
        item_ap = ap + rift_ap
        c_ad, c_ap = conq_values(level)
        self.conq_ad_full = 0.0
        self.conq_ap_full = 0.0
        if item_ap > item_bonus_ad and item_ap > 0:
            self.adapt = "AP"
            shard_ap = 9.0
            shard_ad = 0.0
            if keystone == "conqueror":
                self.conq_ap_full = c_ap
        else:
            self.adapt = "AD"
            shard_ap = 0.0
            shard_ad = 5.4
            if keystone == "conqueror":
                self.conq_ad_full = c_ad
        self.deathcap = "deathcap" in self.tags
        amp = 1.30 if self.deathcap else 1.0
        self.ap_no_conq = (item_ap + shard_ap) * amp
        self.conq_ap_full *= amp
        self.bonus_ad_no_conq = item_bonus_ad + shard_ad
        self.bloodmail = "bloodmail" in self.tags
        # Stat sheet and cooldown use fully stacked Conqueror.
        self.bonus_ad_flat = self.bonus_ad(0.0)
        self.ad_other = self.base_ad + self.bonus_ad_flat
        self.ap = self.ap_now()

        conditioning = secondary == "conditioning" and minute >= 12
        if conditioning:
            self.bonus_armor = (armor + 8.0) * 1.03
            self.bonus_mr = (mr + 8.0) * 1.03
        else:
            self.bonus_armor = armor
            self.bonus_mr = mr
        self.item_armor = armor
        self.item_mr = mr
        self.revitalize = secondary == "revitalize"

        if legend == "haste":
            legend_ah = 15.0 if minute >= 12 else 5.0
        else:
            legend_ah = 0.0
        self.famine = (5.0 + 0.13 * self.bonus_ad_flat) if "endless" in self.tags else 0.0
        self.ah = ah + legend_ah + self.famine
        basic = self.ah + (25.0 if "shojin" in self.tags else 0.0)
        self.w_cd = 5.0 * 100.0 / (100.0 + basic) if self.w_rank else 999.0
        self.e_cd = 16.0 * 100.0 / (100.0 + basic) if self.e_rank else 999.0
        qbase = Q_CD[self.q_rank] if self.q_rank else 999.0
        self.q_cd = qbase * 100.0 / (100.0 + basic)

        alacrity = 0.18 if legend == "alacrity" and minute >= 12 else (0.06 if legend == "alacrity" else 0.0)
        self.item_as = as_pct + alacrity
        self.guinsoo = "guinsoo" in self.tags
        self.crit = 0.0 if self.guinsoo else min(1.0, crit)
        # Sheet attack speed: passive fully stacked, no Lethal Tempo, no Guinsoo stacks.
        self.aspeed = attack_speed_of(self, pstacks=5, lt_stacks=0, gcount=0, overdrive=False)

        self.lifesteal = ls
        self.omnivamp = ov
        self.flat_mpen = flat_mpen
        self.tenacity = 1.0 - ten_mult
        # Heal and shield power stacks additively. Revitalize's extra 5% below
        # 40% HP is applied in the fight, not on this full-HP sheet.
        power = (0.25 if "visage" in self.tags else 0.0) + (0.05 if self.revitalize else 0.0)
        self.heal_amp = 1.0 + power
        self.shojin = "shojin" in self.tags
        self.visage = "visage" in self.tags
        self.sterak = "sterak" in self.tags
        self.unending = "unending" in self.tags
        self.heartsteel = "heartsteel" in self.tags
        self.jaksho = "jaksho" in self.tags
        self.titanic = "titanic" in self.tags
        self.sundered = "sundered" in self.tags
        self.dd = "dd" in self.tags
        self.navori = "navori" in self.tags
        self.cleaver = "cleaver" in self.tags
        self.nashor = "nashor" in self.tags
        self.liandry = "liandry" in self.tags
        self.bork = "bork" in self.tags
        self.wits = "wits" in self.tags
        self.terminus = "terminus" in self.tags
        self.sunfire = "sunfire" in self.tags
        self.bami = "bami" in self.tags and not self.sunfire
        self.thornmail = "thornmail" in self.tags
        self.kaenic = "kaenic" in self.tags
        self.fon = "fon" in self.tags
        self.steelcaps = "steelcaps" in self.tags
        self.randuin = "randuin" in self.tags
        self.abyssal = "abyssal" in self.tags
        self.fimbul = "fimbul" in self.tags
        self.frozen = "frozen" in self.tags
        self.ldr = "ldr" in self.tags
        self.riftmaker = "riftmaker" in self.tags
        self.endless = "endless" in self.tags
        self.statikk = "statikk" in self.tags
        self.hexplate = "hexplate" in self.tags
        self.maw = "maw" in self.tags
        self.protoplasm = "protoplasm" in self.tags
        self.eclipse = "eclipse" in self.tags
        self.ravenous = "ravenous" in self.tags
        self.gunblade = "gunblade" in self.tags
        if "dusk" in self.tags:
            self.spell = "dusk"
        elif "trinity" in self.tags:
            self.spell = "trinity"
        elif "ibg" in self.tags:
            self.spell = "ibg"
        elif "sheen" in self.tags:
            self.spell = "sheen"
        else:
            self.spell = None
        self.lightning_base = 11.0 + (68.0 - 11.0) * (level - 1) / 17.0
        self.with_r = with_r

    def bonus_ad(self, missing: float) -> float:
        """Bonus AD, including Conqueror's current stacks and Bloodmail Retribution."""
        flat = self.bonus_ad_no_conq + self.conq_ad_full * self.conq_frac
        extra = missing * 0.12 * (self.base_ad + flat) if self.bloodmail else 0.0
        return flat + extra

    def total_ad(self, missing: float) -> float:
        return self.base_ad + self.bonus_ad(missing)

    def ap_now(self) -> float:
        return self.ap_no_conq + self.conq_ap_full * self.conq_frac

    def add_bonus_hp(self, delta: float) -> None:
        if delta == 0:
            return
        self.bonus_hp += delta
        self.max_hp += delta
        if self.bloodmail:
            extra = 0.025 * delta
            self.bonus_ad_no_conq += extra
            self.tyranny += extra
        if self.riftmaker:
            extra_ap = 0.02 * delta * (1.30 if self.deathcap else 1.0)
            self.ap_no_conq += extra_ap
        self.bonus_ad_flat = self.bonus_ad(0.0)
        self.ad_other = self.base_ad + self.bonus_ad_flat
        self.ap = self.ap_now()

    def w2_premit(self, missing: float = 0.0) -> float:
        """Wounded bite before resists, for the stat check and the report."""
        if not self.w_rank:
            return 0.0
        raw = W_BASE[self.w_rank] + 1.10 * self.total_ad(missing) + 0.06 * self.bonus_hp
        return raw * (1.5 + self.bonus_ad(missing) / 400.0)

    def e_shield(self) -> float:
        return (0.14 * self.max_hp + 0.75 * self.ap) * self.heal_amp

    def sterak_shield(self) -> float:
        if not self.sterak:
            return 0.0
        return 0.60 * self.bonus_hp * self.heal_amp


class Champ:
    def __init__(self, hp: float, armor: float, mr: float):
        self.max_hp = float(hp)
        self.hp = float(hp)
        self.armor = float(armor)
        self.mr = float(mr)
        self.cleaver = 0
        self.burn_until = 0.0

    @property
    def alive(self) -> bool:
        return self.hp > 1.0


def targets_at(minute: int, level: int) -> Tuple[Champ, Champ]:
    carry_hp = 1100 + 70 * level + 4 * minute
    carry_ar = 42 + 2.9 * level
    carry_mr = 28 + 1.15 * level
    tank_hp = 1300 + 100 * level + 50 * max(0, minute - 8)
    tank_ar = 50 + 2.2 * level + min(155.0, 6.5 * max(0, minute - 9))
    tank_mr = 34 + 1.3 * level + min(95.0, 4.2 * max(0, minute - 11))
    return Champ(carry_hp, carry_ar, carry_mr), Champ(tank_hp, tank_ar, tank_mr)


def focus_scale(minute: int) -> float:
    if minute >= 30:
        return 1.0
    if minute <= 8:
        return 0.32
    return 0.32 + 0.68 * (minute - 8) / 22.0


def pen_scale(minute: int) -> float:
    return min(1.0, max(0.0, (minute - 12) / 16.0))


def attack_speed_of(build: "Build", pstacks: int, lt_stacks: int, gcount: int, overdrive: bool) -> float:
    """Total AS = base + bonus_AS * Volibear's 0.7 ratio, capped at 3.003."""
    passive = pstacks * (0.05 + 0.04 * build.ap_now() / 100.0)
    guinsoo = 0.08 * min(4, gcount) if build.guinsoo else 0.0
    bonus = (
        0.02 * growth_mult(build.level)
        + build.item_as
        + 0.10
        + passive
        + guinsoo
        + (0.06 * lt_stacks if build.keystone == "lethal" else 0.0)
        + (0.50 if overdrive else 0.0)
    )
    return min(AS_CAP, AS_BASE + bonus * AS_RATIO)


def mitigate(amount: float, resist: float, pct_pens: Sequence[float], flat: float) -> float:
    if amount <= 0:
        return 0.0
    r = max(0.0, resist)
    for p in pct_pens:
        r *= 1.0 - p
    r = max(0.0, r - flat)
    return amount * 100.0 / (100.0 + r)


def last_stand(hp_frac: float) -> float:
    if hp_frac > 0.60:
        return 0.0
    if hp_frac <= 0.30:
        return 0.11
    return 0.05 + 0.06 * (0.60 - hp_frac) / 0.30


def hs_procs_for(minute: int, names: Sequence[str], finish_minute: Optional[int]) -> int:
    if "Heartsteel" not in names:
        return 0
    start = 14 if finish_minute is None else finish_minute
    owned = max(0, minute - start)
    return min(18, int(owned * 0.75))


class Sim:
    def __init__(self, build: Build, minute: int, grievous: bool, trace: bool, scenario: str):
        self.b = build
        self.minute = minute
        self.grievous = 0.60 if grievous else 1.0
        self.trace = trace
        self.scenario = scenario
        self.logs: List[str] = []
        self.hp = build.max_hp
        self.shields: List[dict] = []
        self.sources: Dict[str, float] = {}
        self.heals: Dict[str, float] = {}
        self.absorbed = 0.0
        self.total = 0.0
        self.carry_dmg = 0.0
        self.tank_dmg = 0.0
        self.w_casts = 0
        self.w_bites = 0
        self.autos = 0
        self.spellblades = 0
        self.e_hits = 0
        self.died = False
        self.death_t = None
        self.jak_on = False
        self.fon_mr = 0.0
        self.fon_stacks = 0
        self.term_stacks = 0
        self.term_ar = 0.0
        self.term_mr = 0.0
        self.rift_stacks = 0
        self.shojin_stacks = 0
        self.gcount = 0
        self.bleeds: List[List[float]] = []
        scale = focus_scale(minute)
        pscale = pen_scale(minute)
        self.phys_dps = PHYS_DPS * scale
        self.magic_dps = MAGIC_DPS * scale
        self.enemy_apen = 0.12 + 0.18 * pscale
        self.enemy_flat_ar = 6.0 + 6.0 * pscale
        self.enemy_mpen = 0.15 + 0.20 * pscale
        self.enemy_flat_mr = 6.0 + 4.0 * pscale
        self.carry, self.tank = targets_at(minute, build.level)
        # Dive: he is on the carry, tank is in the R/E. Brawl: he is on the tank.
        if scenario == "brawl":
            self.primary, self.secondary = self.tank, self.carry
        else:
            self.primary, self.secondary = self.carry, self.tank

    def log(self, t: float, msg: str) -> None:
        if self.trace and len(self.logs) < 80:
            self.logs.append(f"{t:5.2f}  {msg}  hp {self.hp:.0f}/{self.b.max_hp:.0f}")

    def missing(self) -> float:
        if self.b.max_hp <= 0:
            return 0.0
        return max(0.0, min(1.0, 1.0 - self.hp / self.b.max_hp))

    def heal(self, amount: float, source: str, overheal: bool = False) -> None:
        amount *= self.grievous
        if amount <= 0 or self.hp <= 0:
            return
        room = max(0.0, self.b.max_hp - self.hp)
        gain = min(room, amount)
        self.hp += gain
        self.heals[source] = self.heals.get(source, 0.0) + gain
        if overheal and amount > room:
            extra = amount - room
            self.b.add_bonus_hp(extra)
            self.hp += extra
            self.heals[source] += extra

    def add_shield(self, source: str, amount: float, duration: float, t: float, decay: bool = False, magic_only: bool = False) -> None:
        amount *= 1.0  # heal amp already applied by callers that need it
        if amount <= 0:
            return
        self.shields = [s for s in self.shields if s["source"] != source]
        self.shields.append({
            "source": source,
            "hp": amount,
            "expires": t + duration,
            "decay": (amount / duration) if decay else 0.0,
            "magic_only": magic_only,
        })

    def decay_shields(self, t: float) -> None:
        kept = []
        for s in self.shields:
            if t >= s["expires"]:
                continue
            if s["decay"]:
                s["hp"] = max(0.0, s["hp"] - s["decay"] * DT)
            if s["hp"] > 0:
                kept.append(s)
        self.shields = kept

    def absorb(self, amount: float, magic: bool) -> float:
        for s in self.shields:
            if amount <= 0:
                break
            if s["magic_only"] and not magic:
                continue
            use = min(s["hp"], amount)
            s["hp"] -= use
            amount -= use
            self.absorbed += use
        return amount

    def refresh_amp(self, hp: Optional[float] = None) -> None:
        """Heal/shield power. Visage +25 and Revitalize +5, or +10 below 40% HP."""
        cur = self.hp if hp is None else hp
        power = 0.25 if self.b.visage else 0.0
        if self.b.revitalize:
            power += 0.10 if cur <= 0.40 * self.b.max_hp else 0.05
        self.b.heal_amp = 1.0 + power

    def on_takedown(self) -> None:
        if self.b.endless:
            self.feast_until = self.t + 8.0
            self.log(self.t, "Endless Feast")

    def take(self, amount: float, magic: bool, defer: bool) -> None:
        if amount <= 0 or self.hp <= 0:
            return
        # Melee Death's Dance stores 30% of post-mitigation physical and magic.
        if defer and self.b.dd:
            stored = 0.30 * amount
            self.bleeds.append([3.0, stored / 3.0])
            amount -= stored
        hp_part = self._preview_hp_damage(amount, magic)
        post_hp = self.hp - hp_part
        crossed = hp_part > 0 and post_hp <= 0.30 * self.b.max_hp
        self.refresh_amp(post_hp if crossed else self.hp)
        if crossed:
            self._lifeline(magic)
        leftover = self.absorb(amount, magic)
        self.hp -= leftover
        if self.hp <= 0:
            self.hp = 0.0
            self.died = True

    def _lifeline(self, magic: bool) -> None:
        b = self.b
        t = getattr(self, "t", 0.0)
        if b.sterak and not self.sterak_used:
            self.sterak_used = True
            shield = 0.60 * b.bonus_hp * b.heal_amp
            self.add_shield("sterak", shield, 4.5, t, decay=True)
            self.log(t, f"Sterak shield {shield:.0f}")
            return
        if b.maw and magic and not self.maw_used:
            self.maw_used = True
            shield = (200.0 + 1.50 * b.bonus_ad(self.missing())) * b.heal_amp
            self.add_shield("maw", shield, 3.0, t, magic_only=True)
            self.maw_omni = 0.10
            self.log(t, f"Maw shield {shield:.0f}")
            return
        if b.protoplasm and not self.proto_used:
            self.proto_used = True
            lvl = b.level
            bonus = 100.0 + (300.0 - 100.0) * (lvl - 1) / 17.0
            heal = 100.0 + (400.0 - 100.0) * (lvl - 1) / 17.0
            heal += 1.75 * b.bonus_armor + 1.75 * b.bonus_mr
            b.add_bonus_hp(bonus)
            self.hp += bonus
            self.proto_bonus = bonus
            self.proto_until = t + 5.0
            self.proto_regen = heal / 5.0
            self.log(t, f"Protoplasm +{bonus:.0f} HP, heal {heal:.0f}")

    def _preview_hp_damage(self, amount: float, magic: bool) -> float:
        left = amount
        for s in self.shields:
            if left <= 0:
                break
            if s["magic_only"] and not magic:
                continue
            left -= min(s["hp"], left)
        return left

    def armor_now(self) -> float:
        bonus = self.b.bonus_armor * (1.30 if self.jak_on else 1.0) + self.term_ar
        return self.b.base_armor + bonus

    def mr_now(self) -> float:
        bonus = self.b.bonus_mr * (1.30 if self.jak_on else 1.0) + self.term_mr + self.fon_mr
        return self.b.base_mr + bonus

    def pens_ar(self) -> List[float]:
        pens = list(self.b.armor_pens)
        if self.term_stacks:
            pens.append(0.06 * self.term_stacks)
        return pens

    def pens_mr(self) -> List[float]:
        pens = list(self.b.magic_pens)
        if self.term_stacks:
            pens.append(0.06 * self.term_stacks)
        return pens

    def emit(
        self,
        raw: float,
        dtype: str,
        target: Optional[Champ],
        bucket: str,
        *,
        shojin: bool = False,
        ability: bool = False,
        aoe: bool = False,
        lifesteal: bool = False,
        stack_cleaver: bool = False,
    ) -> float:
        if self.died or target is None or not target.alive or raw <= 0:
            return 0.0
        dmg = raw
        if shojin and self.b.shojin:
            dmg *= 1.0 + 0.03 * self.shojin_stacks
        dmg *= 1.0 + last_stand(self.hp / self.b.max_hp if self.b.max_hp else 1.0)
        dmg *= 1.0 + 0.02 * self.rift_stacks
        if dtype == "phys" and self.b.ldr:
            if target.max_hp > self.b.max_hp:
                dmg *= 1.0 + min(0.15, 0.15 * (target.max_hp - self.b.max_hp) / self.b.max_hp)
            else:
                pass
        if dtype == "phys":
            armor = target.armor * (1.0 - 0.06 * target.cleaver)
            post = mitigate(dmg, armor, self.pens_ar(), 0.0)
            if stack_cleaver and self.b.cleaver:
                target.cleaver = min(5, target.cleaver + 1)
        else:
            post = mitigate(dmg, target.mr, self.pens_mr(), self.b.flat_mpen)
            if self.b.abyssal:
                post *= 1.12
        if ability and self.b.liandry:
            target.burn_until = self.t + 3.0
        target.hp = max(0.0, target.hp - post)
        self.sources[bucket] = self.sources.get(bucket, 0.0) + post
        self.total += post
        if target is self.carry:
            self.carry_dmg += post
        else:
            self.tank_dmg += post
        vamp = 0.0
        self.refresh_amp()
        if lifesteal and self.b.lifesteal:
            vamp += post * self.b.lifesteal * self.b.heal_amp
        omni = self.b.omnivamp + getattr(self, "maw_omni", 0.0)
        if self.b.riftmaker and self.rift_stacks >= 4:
            omni += 0.10
        if self.b.endless and self.t < getattr(self, "feast_until", -1.0):
            omni += 0.15
        # Omnivamp is full value against champions, including area damage.
        if omni:
            vamp += post * omni * self.b.heal_amp
        if vamp:
            self.heal(vamp, "vamp")
        if target.hp <= 0:
            self.on_takedown()
        if ability and self.b.shojin:
            self.shojin_stacks = min(4, self.shojin_stacks + 1)
        return post

    def try_prime(self, t: float) -> None:
        if self.b.spell and t >= self.spell_cd_until:
            self.primed_until = t + 10.0

    def consume_spellblade(self, t: float, target: Champ) -> bool:
        if not self.b.spell or t < self.spell_cd_until or t > self.primed_until:
            return False
        b = self.b
        echo = False
        if b.spell == "dusk":
            self.emit(0.75 * b.base_ad + 0.10 * b.ap_now(), "magic", target, "spellblade", lifesteal=True)
            self.heal((0.10 * b.ap_now() + 0.03 * b.bonus_hp) * b.heal_amp, "dusk")
            echo = True
        elif b.spell == "trinity":
            self.emit(2.0 * b.base_ad, "phys", target, "spellblade", lifesteal=True, stack_cleaver=False)
        elif b.spell == "ibg":
            self.emit(1.5 * b.base_ad, "phys", target, "spellblade", lifesteal=True)
        else:
            self.emit(1.0 * b.base_ad, "phys", target, "spellblade", lifesteal=True)
        self.primed_until = -1.0
        self.spell_cd_until = t + 1.5
        self.spellblades += 1
        return echo

    def attack_speed(self) -> float:
        over = self.t < self.overdrive_until
        return attack_speed_of(self.b, self.pstacks, self.lt_stacks, self.gcount, over)

    def grant_stacks(self, on_hit: bool) -> None:
        """Passive, Conqueror and Lethal Tempo stacks are granted by the hit, after its damage."""
        if self.b.keystone == "conqueror":
            self.conq_stacks = min(12, self.conq_stacks + 2)
            self.b.conq_frac = self.conq_stacks / 12.0
        if self.b.keystone == "lethal" and on_hit:
            self.lt_stacks = min(6, self.lt_stacks + 1)
        if self.pstacks < 5:
            self.pstacks += 1

    def lightning_ready(self) -> bool:
        # The hit that reaches 5 stacks is empowered, and every on-hit after.
        return self.pstacks >= 4

    def eclipse_hit(self, target: Champ) -> None:
        if not self.b.eclipse or target is None or not target.alive or self.t < self.eclipse_cd:
            return
        prev = self.eclipse_last.get(id(target), -999.0)
        self.eclipse_last[id(target)] = self.t
        if self.t - prev > 2.0 or prev < 0:
            return
        self.eclipse_cd = self.t + 6.0
        self.refresh_amp()
        shield = (150.0 + 0.40 * self.b.bonus_ad(self.missing())) * self.b.heal_amp
        self.add_shield("eclipse", shield, 2.0, self.t)
        self.emit(0.08 * target.max_hp, "phys", target, "eclipse")
        self.log(self.t, f"Eclipse shield {shield:.0f}")

    def statikk_proc(self, target: Champ) -> None:
        if not self.b.statikk or target is None:
            return
        self.energy += 15.0
        if self.energy < 100.0:
            return
        self.energy -= 100.0
        other = self.secondary if target is self.primary else self.primary
        self.emit(60.0, "magic", target, "statikk")
        if other is not None and other.alive:
            self.emit(60.0, "magic", other, "statikk")
            # Chain applies on-hit to the bounce target once. It does not retarget.
            self.on_hits(other, 1, crescent=False, bounce=False)
        self.log(self.t, "Statikk chain")

    def ravenous_cleave(self, target: Champ, crescent: bool) -> None:
        if not self.b.ravenous:
            return
        other = self.secondary if target is self.primary else self.primary
        ratio = 0.80 if crescent else 0.40
        if other is not None and other.alive:
            self.emit(ratio * self.b.total_ad(self.missing()), "phys", other, "ravenous", lifesteal=True, aoe=True)
        if crescent:
            self.emit(ratio * self.b.total_ad(self.missing()), "phys", target, "ravenous", lifesteal=True, aoe=True)

    def on_hits(self, target: Champ, times: int, crescent: bool, bounce: bool = True) -> None:
        b = self.b
        other = self.secondary if target is self.primary else self.primary
        missing = self.missing()
        light = b.lightning_base + 0.20 * b.bonus_ad(missing) + 0.45 * b.ap_now()
        wit = 15.0 + 65.0 * (b.level - 1) / 17.0
        for _ in range(times):
            if self.lightning_ready():
                self.emit(light, "magic", target, "lightning")
                if bounce and other is not None and other.alive:
                    self.emit(light, "magic", other, "lightning", aoe=True)
            if b.nashor:
                self.emit(15.0 + 0.15 * b.ap_now(), "magic", target, "nashor", lifesteal=True)
            if b.bork and target.alive:
                self.emit(0.09 * target.hp, "phys", target, "bork", lifesteal=True)
            if b.wits:
                self.emit(wit, "magic", target, "wits")
            if b.titanic:
                prim = 0.04 if crescent else 0.01
                cone = 0.09 if crescent else 0.03
                self.emit(prim * b.max_hp, "phys", target, "titanic", lifesteal=True)
                if other is not None and other.alive:
                    self.emit(cone * b.max_hp, "phys", other, "titanic", aoe=True)
            if b.ravenous and not crescent:
                self.ravenous_cleave(target, crescent=False)
            self.maybe_terminus()
            if b.keystone == "lethal" and self.lt_stacks >= 6 and target.alive:
                base = 9.0 + (32.47 - 9.0) * (b.level - 1) / 17.0
                bonus_as = (self.attack_speed() - AS_BASE) / AS_RATIO
                bolt = base * (1.0 + max(0.0, bonus_as))
                kind = "magic" if b.ap_now() > b.bonus_ad(missing) else "phys"
                self.emit(bolt, kind, target, "tempo")

    def maybe_terminus(self) -> None:
        if not self.b.terminus:
            return
        self.term_stacks = min(3, self.term_stacks + 1)
        if self.term_stacks == 3 and self.term_ar == 0.0:
            self.term_ar = 10.0
            self.term_mr = 10.0

    def navori(self, t: float) -> None:
        if not self.b.navori:
            return
        for attr in ("q_ready", "w_ready", "e_ready"):
            ready = getattr(self, attr)
            rem = ready - t
            if rem > 0:
                setattr(self, attr, t + rem * 0.85)

    def phantom(self) -> bool:
        self.gcount += 1
        return self.b.guinsoo and self.gcount % 3 == 0

    def do_auto(self, t: float, from_q: bool) -> None:
        b = self.b
        self.refresh_amp()
        target = self.primary if self.primary.alive else self.secondary
        if target is None or not target.alive:
            return
        missing = self.missing()
        is_phantom = self.phantom()
        w_in = self.w_ready - t
        hold = from_q or (0 < w_in <= 1.15)
        echo = False if hold else self.consume_spellblade(t, target)
        mult = 1.0
        if b.sundered and self.sundered_ready and not b.guinsoo and (self.hp < 0.90 * b.max_hp or t > self.start + 5):
            mult = 1.60
            self.sundered_ready = False
            self.sundered_at = t + 10.0
            miss_hp = self.missing() * b.max_hp
            self.heal((0.90 * b.base_ad + 0.04 * miss_hp) * b.heal_amp, "sundered", overheal=True)
            self.log(t, "Sundered crit")
        elif not b.guinsoo:
            mult = 1.0 + b.crit
        self.emit(b.total_ad(missing) * mult, "phys", target, "auto", lifesteal=True, stack_cleaver=True)
        if from_q and b.q_rank:
            bonus = Q_BASE[b.q_rank] + 1.60 * b.bonus_ad(missing)
            self.emit(bonus, "phys", target, "Q", shojin=True, ability=True, lifesteal=True)
            self.q_buff = False
            self.log(t, f"Q auto +{bonus:.0f} pre")
        if b.heartsteel and not self.hs_used and t >= self.start + 3.0:
            raw = 70.0 + 0.06 * b.max_hp
            self.emit(raw, "phys", target, "heartsteel", lifesteal=True)
            grant = 0.10 * raw
            b.add_bonus_hp(grant)
            self.hp += grant
            self.hs_used = True
            self.log(t, f"Heartsteel {raw:.0f}")
        if b.tags.__contains__("deadman") and not self.deadman_used:
            self.emit(40.0 + b.base_ad, "phys", target, "deadman", lifesteal=True)
            self.deadman_used = True
        crescent = False
        if b.titanic and self.crescent_ready and not from_q:
            crescent = True
            self.crescent_ready = False
        times = 1 + (1 if echo else 0) + (1 if is_phantom else 0)
        self.on_hits(target, times, crescent)
        if b.ravenous and self.rav_ready and not from_q:
            self.ravenous_cleave(target, crescent=True)
            self.rav_ready = False
        self.statikk_proc(target)
        self.eclipse_hit(target)
        self.grant_stacks(on_hit=True)
        self.navori(t)
        self.autos += 1
        if not from_q:
            delay = 0.0 if crescent else 1.0 / max(0.2, self.attack_speed())
            self.atk_ready = t + delay

    def resolve_w(self, t: float) -> None:
        b = self.b
        target = self.primary if self.primary.alive else self.secondary
        if target is None or not target.alive or not b.w_rank:
            return
        missing = self.missing()
        self.refresh_amp()
        raw = W_BASE[b.w_rank] + 1.10 * b.total_ad(missing) + 0.06 * b.bonus_hp
        bite = False
        wounded = self.wounded and self.wound_target is target and t <= self.wound_until
        if wounded:
            raw *= 1.5 + b.bonus_ad(missing) / 400.0
            miss_hp = missing * b.max_hp
            heal = (W_HEAL[b.w_rank] + W_HEAL_PCT[b.w_rank] * miss_hp) * b.heal_amp
            self.heal(heal, "W")
            bite = True
            self.w_bites += 1
        self.wounded = True
        self.wound_target = target
        self.wound_until = t + 8.0
        post = self.emit(raw, "phys", target, "W", shojin=True, ability=True, lifesteal=True, stack_cleaver=True)
        echo = self.consume_spellblade(t, target)
        is_phantom = self.phantom()
        times = 1 + (1 if echo else 0) + (1 if is_phantom else 0)
        self.on_hits(target, times, crescent=False)
        self.statikk_proc(target)
        self.eclipse_hit(target)
        self.grant_stacks(on_hit=True)
        self.navori(t)
        self.w_casts += 1
        kind = "W2" if bite else "W1"
        self.log(t, f"{kind} pre {raw:.0f} post {post:.0f}")

    def resolve_e(self, t: float) -> None:
        b = self.b
        if not b.e_rank:
            return
        self.refresh_amp()
        shield = (0.14 * b.max_hp + 0.75 * b.ap_now()) * b.heal_amp
        self.add_shield("e", shield, 3.0, t)
        self.log(t, f"E shield {shield:.0f}")
        for tgt in (self.primary, self.secondary):
            if tgt is None or not tgt.alive:
                continue
            raw = E_BASE[b.e_rank] + 0.70 * b.ap_now() + E_HP[b.e_rank] * tgt.max_hp
            self.emit(raw, "magic", tgt, "E", shojin=True, ability=True, aoe=True)
            self.eclipse_hit(tgt)
        self.grant_stacks(on_hit=False)
        if b.fimbul and t >= self.fimbul_ready:
            fshield = (100.0 + 0.045 * b.base_mana) * b.heal_amp
            self.add_shield("fimbul", fshield, 3.0, t)
            self.fimbul_ready = t + 8.0
        self.e_hits += 1

    def run(self) -> dict:
        b = self.b
        self.sterak_used = False
        self.maw_used = False
        self.maw_omni = 0.0
        self.proto_used = False
        self.proto_bonus = 0.0
        self.proto_until = 0.0
        self.proto_regen = 0.0
        self.sundered_ready = b.sundered
        self.sundered_at = 0.0
        self.hs_used = False
        self.deadman_used = False
        self.crescent_ready = b.titanic
        self.rav_ready = b.ravenous
        self.wounded = False
        self.wound_target = None
        self.wound_until = 0.0
        self.pstacks = 0
        self.lt_stacks = 0
        self.conq_stacks = 0
        self.b.conq_frac = 0.0 if b.keystone == "conqueror" else 0.0
        self.feast_until = -1.0
        self.eclipse_cd = 0.0
        self.eclipse_last = {}
        self.energy = (700.0 / 24.0) if (b.statikk and b.with_r) else 0.0
        self.overdrive_until = -1.0
        self.q_buff = True
        self.spell_cd_until = 0.0
        self.primed_until = 10.0 if b.spell else -1.0
        self.fimbul_ready = 0.0
        self.start = 1.0 if b.with_r else 0.0
        self.end = self.start + COMBAT
        self.t = self.start
        self.q_ready = b.q_cd  # cast at t=0 for the engage
        self.e_ready = b.e_cd
        self.w_ready = self.start  # W is up as he lands
        self.e_land = 2.0
        self.e_in_air = b.e_rank > 0
        self.atk_ready = self.start
        self.pending: Optional[Tuple[str, float]] = None
        self.unending_next = self.start + 4.0
        self.rift_next = self.start + 1.0
        self.fon_next = self.start + 1.0
        cc = BASE_CC * (1.0 - b.tenacity)
        self.cc_until = self.start + cc

        self.refresh_amp()
        if b.kaenic:
            self.add_shield("kaenic", 0.15 * b.max_hp * b.heal_amp, 30.0, self.start, magic_only=True)

        # Impact. Conqueror has no stacks yet. Hexplate Overdrive started on the cast,
        # one second before he lands, so 7s of the 8s remain.
        if b.with_r and b.r_rank:
            if b.hexplate:
                self.overdrive_until = self.start + 7.0
            raw = R_BASE[b.r_rank] + 2.50 * b.bonus_ad(0.0) + 1.25 * b.ap_now()
            for tgt in (self.primary, self.secondary):
                if tgt is not None:
                    self.emit(raw, "phys", tgt, "R", shojin=True, ability=True, aoe=True, stack_cleaver=True)
                    self.eclipse_hit(tgt)
            self.grant_stacks(on_hit=False)
            self.log(self.start, f"R impact pre {raw:.0f} x2")
        if b.gunblade and (self.primary.alive or self.secondary.alive):
            bolt = 175.0 + (253.0 - 175.0) * (b.level - 1) / 17.0 + 0.30 * b.ap_now()
            tgt = self.primary if self.primary.alive else self.secondary
            self.emit(bolt, "magic", tgt, "gunblade")
            self.log(self.start, f"Gunblade {bolt:.0f}")
        # Q pounce on landing, before the peel connects. Does not spend spellblade.
        if self.primary.alive or self.secondary.alive:
            self.do_auto(self.start, from_q=True)
        self.q_buff = False

        while self.t < self.end and not self.died:
            t = self.t
            self.refresh_amp()
            self.decay_shields(t)
            if b.jaksho and not self.jak_on and t >= self.start + 5.0:
                self.jak_on = True
                self.log(t, "Jak'Sho resists")
            if b.fon and t >= self.fon_next:
                self.fon_stacks += 1
                self.fon_next += 1.0
                if self.fon_stacks == 8:
                    self.fon_mr = 70.0
                    self.log(t, "Force of Nature")
            if b.riftmaker and self.rift_stacks < 4 and t >= self.rift_next:
                self.rift_stacks += 1
                self.rift_next += 1.0

            if self.e_in_air and t >= self.e_land:
                self.resolve_e(t)
                self.e_in_air = False

            # Incoming focus, then bleeds.
            phys = self.phys_dps * DT
            if b.steelcaps:
                phys *= 1.0 - 0.12 * 0.80
            if b.randuin:
                phys *= 0.85
            if b.frozen:
                phys *= 0.90
            post_p = mitigate(phys, self.armor_now(), [self.enemy_apen], self.enemy_flat_ar)
            post_m = mitigate(self.magic_dps * DT, self.mr_now(), [self.enemy_mpen], self.enemy_flat_mr)
            self.take(post_p, magic=False, defer=True)
            if self.died:
                self.death_t = t
                break
            self.take(post_m, magic=True, defer=True)
            if self.died:
                self.death_t = t
                break
            still = []
            for bleed in self.bleeds:
                self.take(bleed[1] * DT, magic=False, defer=False)
                bleed[0] -= DT
                if bleed[0] > 0 and not self.died:
                    still.append(bleed)
                if self.died:
                    self.death_t = t
                    break
            self.bleeds = still
            if self.died:
                break

            if b.thornmail and post_p > 0 and self.carry.alive:
                reflect = (10.0 + 0.10 * b.bonus_armor) * 1.15 * DT
                self.emit(reflect, "magic", self.carry, "thorns")

            # His damage.
            if b.liandry:
                for tgt in (self.carry, self.tank):
                    if tgt.alive and t < tgt.burn_until:
                        self.emit(0.02 * tgt.max_hp * DT, "magic", tgt, "liandry", aoe=True)
            if b.sunfire or b.bami:
                aura = (12.0 + 18.0 * (b.level - 1) / 17.0 + 0.01 * b.bonus_hp)
                if b.bami and not b.sunfire:
                    aura *= 0.45
                for tgt in (self.primary, self.secondary):
                    if tgt is not None and tgt.alive:
                        self.emit(aura * DT, "magic", tgt, "sunfire", aoe=True)
            if self.proto_regen and t < self.proto_until:
                self.refresh_amp()
                self.heal(self.proto_regen * DT, "protoplasm")
            elif self.proto_bonus and t >= self.proto_until:
                self.b.add_bonus_hp(-self.proto_bonus)
                self.hp = min(self.hp, self.b.max_hp)
                self.proto_bonus = 0.0
                self.proto_regen = 0.0

            if b.unending and t >= self.unending_next:
                healed = 0.0
                for tgt in (self.primary, self.secondary):
                    if tgt is not None and tgt.alive:
                        post = self.emit(0.03 * b.bonus_hp, "magic", tgt, "unending", aoe=True, ability=True)
                        healed += 2.50 * post
                if healed:
                    self.heal(healed * b.heal_amp, "unending")
                self.unending_next += 4.0
                self.log(t, f"Unending heal {healed * b.heal_amp:.0f}")

            if self.sundered_at and t >= self.sundered_at:
                self.sundered_ready = True
                self.sundered_at = 0.0

            acted = False
            if self.pending and t >= self.pending[1]:
                kind = self.pending[0]
                self.pending = None
                if kind == "W":
                    self.resolve_w(t)
                acted = True
            elif t >= self.cc_until:
                if t >= self.w_ready and b.w_rank:
                    self.try_prime(t)
                    self.w_ready = t + b.w_cd
                    self.pending = ("W", t + 0.25)
                    acted = True
                elif self.q_buff and t >= self.atk_ready:
                    self.do_auto(t, from_q=True)
                    acted = True
                elif t >= self.e_ready and not self.e_in_air and b.e_rank:
                    self.try_prime(t)
                    self.e_land = t + 2.0
                    self.e_in_air = True
                    self.e_ready = t + b.e_cd
                    self.log(t, "cast E")
                    acted = True
                elif t >= self.q_ready and not self.q_buff and b.q_rank:
                    self.try_prime(t)
                    self.q_buff = True
                    self.q_ready = t + b.q_cd
                    if b.fimbul and t >= self.fimbul_ready:
                        pass  # shield lands with the stun on the auto
                    self.log(t, "cast Q")
                    acted = True
                elif t >= self.atk_ready:
                    self.do_auto(t, from_q=False)
                    acted = True
            if not acted and t >= self.atk_ready and t >= self.cc_until and self.pending is None:
                pass
            self.t += DT

        survival = (self.death_t if self.death_t is not None else self.end) - self.start
        survival = max(0.0, min(COMBAT, survival))
        return {
            "total": self.total,
            "carry": self.carry_dmg,
            "tank": self.tank_dmg,
            "survival": survival,
            "died": self.died or self.hp <= 0,
            "end_hp": max(0.0, self.hp),
            "max_hp": self.b.max_hp,
            "healed": sum(self.heals.values()),
            "heals": dict(self.heals),
            "absorbed": self.absorbed,
            "sources": dict(self.sources),
            "w_casts": self.w_casts,
            "w_bites": self.w_bites,
            "autos": self.autos,
            "spellblades": self.spellblades,
            "e_hits": self.e_hits,
            "logs": list(self.logs),
            "bonus_ad": self.b.bonus_ad_flat,
            "ap": self.b.ap,
            "armor": self.armor_now(),
            "mr": self.mr_now(),
        }


DEFAULT_RUNES = ("conqueror", "haste", "conditioning")


def run_fight(
    names: Sequence[str],
    minute: int,
    *,
    with_r: bool,
    grievous: bool = False,
    hs_finish: Optional[int] = None,
    scenario: str = "dive",
    trace: bool = False,
    runes: Sequence[str] = DEFAULT_RUNES,
) -> dict:
    level = level_at_minute(minute) if minute < 34 else 18
    if minute >= 27:
        level = 18
    procs = hs_procs_for(minute, names, hs_finish)
    keystone, legend, secondary = runes
    build = Build(
        names, level, minute, procs, with_r,
        keystone=keystone, legend=legend, secondary=secondary,
    )
    sim = Sim(build, minute, grievous, trace, scenario)
    return sim.run()


def purchase(order: Sequence[str], gold: int) -> List[str]:
    owned: List[str] = []
    spent = 0
    for name in order:
        it = ITEMS[name]
        for comp in it.recipe:
            cost = ITEMS[comp].cost
            if spent + cost > gold:
                return owned
            spent += cost
            owned.append(comp)
        finish = it.cost - sum(ITEMS[c].cost for c in it.recipe)
        if spent + finish > gold:
            return owned
        spent += finish
        for comp in it.recipe:
            owned.remove(comp)
        owned.append(name)
    return owned


def finish_minute(order: Sequence[str], name: str) -> Optional[int]:
    for m in range(0, GAME_MINUTES + 1):
        if name in purchase(order, gold_at_minute(m)):
            return m
    return None


ARCHETYPES: List[Tuple[str, Tuple[str, ...]]] = [
    ("Bloodmail Warlord", ("Plated Steelcaps", "Spear of Shojin", "Overlord's Bloodmail", "Sterak's Gage", "Spirit Visage", "Unending Despair")),
    ("Warlord + DD", ("Plated Steelcaps", "Spear of Shojin", "Overlord's Bloodmail", "Sterak's Gage", "Spirit Visage", "Death's Dance")),
    ("Warlord Mercs", ("Mercury's Treads", "Spear of Shojin", "Overlord's Bloodmail", "Sterak's Gage", "Spirit Visage", "Unending Despair")),
    ("Trinity Bruiser", ("Plated Steelcaps", "Trinity Force", "Spear of Shojin", "Sterak's Gage", "Spirit Visage", "Overlord's Bloodmail")),
    ("Heartsteel Titan", ("Plated Steelcaps", "Heartsteel", "Overlord's Bloodmail", "Titanic Hydra", "Spirit Visage", "Sterak's Gage")),
    ("Full Tank", ("Plated Steelcaps", "Heartsteel", "Spirit Visage", "Unending Despair", "Jak'Sho, The Protean", "Randuin's Omen")),
    ("Endless Drain", ("Mercury's Treads", "Endless Hunger", "Spear of Shojin", "Overlord's Bloodmail", "Spirit Visage", "Sterak's Gage")),
    ("Navori Bites", ("Plated Steelcaps", "Navori Flickerblade", "Spear of Shojin", "Overlord's Bloodmail", "Titanic Hydra", "Spirit Visage")),
    ("Dusk Hybrid", ("Mercury's Treads", "Dusk and Dawn", "Riftmaker", "Overlord's Bloodmail", "Spirit Visage", "Sterak's Gage")),
    ("Dusk Titanic", ("Plated Steelcaps", "Dusk and Dawn", "Titanic Hydra", "Overlord's Bloodmail", "Spirit Visage", "Sterak's Gage")),
    ("AP Nashor", ("Mercury's Treads", "Dusk and Dawn", "Nashor's Tooth", "Riftmaker", "Rabadon's Deathcap", "Spirit Visage")),
    ("AP Glass", ("Ionian Boots of Lucidity", "Dusk and Dawn", "Nashor's Tooth", "Rabadon's Deathcap", "Shadowflame", "Void Staff")),
    ("IBG Tank", ("Plated Steelcaps", "Iceborn Gauntlet", "Spirit Visage", "Unending Despair", "Jak'Sho, The Protean", "Thornmail")),
    ("Sundered", ("Plated Steelcaps", "Sundered Sky", "Spear of Shojin", "Sterak's Gage", "Spirit Visage", "Overlord's Bloodmail")),
    ("Cleaver", ("Plated Steelcaps", "Black Cleaver", "Spear of Shojin", "Overlord's Bloodmail", "Sterak's Gage", "Spirit Visage")),
    ("Serylda", ("Plated Steelcaps", "Spear of Shojin", "Overlord's Bloodmail", "Sterak's Gage", "Spirit Visage", "Serylda's Grudge")),
    ("BotRK Cleaver", ("Plated Steelcaps", "Blade of the Ruined King", "Black Cleaver", "Sterak's Gage", "Spirit Visage", "Overlord's Bloodmail")),
    ("Sunfire Titan", ("Plated Steelcaps", "Sunfire Aegis", "Spirit Visage", "Unending Despair", "Jak'Sho, The Protean", "Titanic Hydra")),
    ("Liandry Rift", ("Mercury's Treads", "Riftmaker", "Liandry's Torment", "Dusk and Dawn", "Spirit Visage", "Zhonya's Hourglass")),
    ("Warmog Mail", ("Plated Steelcaps", "Warmog's Armor", "Overlord's Bloodmail", "Spear of Shojin", "Spirit Visage", "Sterak's Gage")),
    ("Terminus", ("Plated Steelcaps", "Terminus", "Wit's End", "Titanic Hydra", "Spirit Visage", "Jak'Sho, The Protean")),
    ("Kaenic Hybrid", ("Mercury's Treads", "Dusk and Dawn", "Riftmaker", "Kaenic Rookern", "Spirit Visage", "Overlord's Bloodmail")),
    ("FoN Warlord", ("Mercury's Treads", "Spear of Shojin", "Overlord's Bloodmail", "Sterak's Gage", "Spirit Visage", "Force of Nature")),
    ("Stride", ("Plated Steelcaps", "Stridebreaker", "Spear of Shojin", "Overlord's Bloodmail", "Sterak's Gage", "Spirit Visage")),
    ("LDR Warlord", ("Plated Steelcaps", "Spear of Shojin", "Overlord's Bloodmail", "Sterak's Gage", "Lord Dominik's Regards", "Spirit Visage")),
    ("Guinsoo On-hit", ("Plated Steelcaps", "Guinsoo's Rageblade", "Blade of the Ruined King", "Wit's End", "Titanic Hydra", "Jak'Sho, The Protean")),
    ("Fimbul Tank", ("Plated Steelcaps", "Iceborn Gauntlet", "Fimbulwinter", "Spirit Visage", "Unending Despair", "Frozen Heart")),
    ("Abyssal AP", ("Mercury's Treads", "Dusk and Dawn", "Riftmaker", "Nashor's Tooth", "Abyssal Mask", "Spirit Visage")),
    ("Statikk Navori", ("Mercury's Treads", "Statikk Shiv", "Navori Flickerblade", "Dusk and Dawn", "Spirit Visage", "Unending Despair")),
    ("Hexplate Warlord", ("Plated Steelcaps", "Experimental Hexplate", "Spear of Shojin", "Overlord's Bloodmail", "Sterak's Gage", "Spirit Visage")),
    ("Gunblade Hybrid", ("Mercury's Treads", "Hextech Gunblade", "Dusk and Dawn", "Nashor's Tooth", "Riftmaker", "Spirit Visage")),
    ("Eclipse Bite", ("Plated Steelcaps", "Eclipse", "Spear of Shojin", "Overlord's Bloodmail", "Sterak's Gage", "Spirit Visage")),
    ("Ravenous Bite", ("Plated Steelcaps", "Ravenous Hydra", "Spear of Shojin", "Overlord's Bloodmail", "Sterak's Gage", "Spirit Visage")),
    ("Maw Warlord", ("Mercury's Treads", "Spear of Shojin", "Overlord's Bloodmail", "Maw of Malmortius", "Spirit Visage", "Unending Despair")),
    ("Protoplasm Tank", ("Plated Steelcaps", "Protoplasm Harness", "Spirit Visage", "Unending Despair", "Jak'Sho, The Protean", "Titanic Hydra")),
    ("Cosmic Hybrid", ("Mercury's Treads", "Dusk and Dawn", "Spear of Shojin", "Cosmic Drive", "Spirit Visage", "Riftmaker")),
    ("Gunmetal On-hit", ("Gunmetal Greaves", "Statikk Shiv", "Navori Flickerblade", "Dusk and Dawn", "Spirit Visage", "Sterak's Gage")),
]


def conflicts(have: Sequence[str], cand: str) -> bool:
    if cand in have:
        return True
    for group in (SPELLBLADES, BOOTS, LIFELINES, HYDRAS):
        if cand in group and any(x in group for x in have):
            return True
    return False


def neighbors(build: Sequence[str]) -> List[Tuple[str, ...]]:
    boots = [i for i in build if i in BOOTS]
    legs = [i for i in build if i not in BOOTS]
    out = []
    for b in BOOTS:
        if b not in boots:
            out.append(tuple(boots_first([b] + legs)))
    for i, leg in enumerate(legs):
        rest = legs[:i] + legs[i + 1 :]
        for cand in LEGENDARIES:
            if conflicts(rest, cand):
                continue
            out.append(tuple(boots_first(boots + rest[:i] + [cand] + rest[i:])))
    return out


def boots_first(items: Sequence[str]) -> List[str]:
    boots = [i for i in items if i in BOOTS]
    legs = [i for i in items if i not in BOOTS]
    return boots + legs


R_CACHE: Dict[Tuple, dict] = {}


def snapshot_r(
    items: Sequence[str],
    grievous: bool = False,
    trace: bool = False,
    scenario: str = "dive",
    runes: Sequence[str] = DEFAULT_RUNES,
) -> dict:
    key = (tuple(sorted(items)), grievous, scenario, trace, tuple(runes))
    if not trace and key in R_CACHE:
        return R_CACHE[key]
    hs_finish = 14 if "Heartsteel" in items else None
    result = run_fight(
        items, 34, with_r=True, grievous=grievous, hs_finish=hs_finish,
        scenario=scenario, trace=trace, runes=runes,
    )
    if not trace:
        R_CACHE[key] = result
    return result


def snapshot_nor(items: Sequence[str], scenario: str = "dive", runes: Sequence[str] = DEFAULT_RUNES) -> dict:
    key = (tuple(sorted(items)), False, "nor", scenario, tuple(runes))
    if key in R_CACHE:
        return R_CACHE[key]
    hs_finish = 14 if "Heartsteel" in items else None
    result = run_fight(
        items, 34, with_r=False, grievous=False, hs_finish=hs_finish,
        scenario=scenario, trace=False, runes=runes,
    )
    R_CACHE[key] = result
    return result


def quick_score(r: dict) -> Tuple[int, float]:
    """Search key: living the ultimate outranks raw burst, then damage."""
    if r["died"]:
        return (0, r["total"] * (r["survival"] / COMBAT))
    leftover = r["end_hp"] / r["max_hp"] if r["max_hp"] else 0.0
    return (1, r["total"] * (0.82 + 0.18 * leftover))


def final_rank(r: dict, nor: dict, brawl: dict) -> Tuple[int, float]:
    """
    Hard to kill: still up at the end of the ultimate dive, and not deleted
    in a no-ult front-to-front. High damage: teamfight damage once that is true.
    """
    lived_r = not r["died"]
    lived_n = not nor["died"]
    if lived_r and lived_n:
        tier = 2
    elif lived_r and nor["survival"] >= 7.0:
        tier = 2
    elif lived_r:
        tier = 1
    else:
        tier = 0
    dmg = r["total"] + 0.25 * brawl["total"] + 0.20 * nor["total"]
    if lived_r:
        dmg += 0.12 * r["total"] * (r["end_hp"] / r["max_hp"])
    return (tier, dmg)


def evaluate_full(items: Sequence[str], runes: Sequence[str] = DEFAULT_RUNES) -> dict:
    r = snapshot_r(items, scenario="dive", runes=runes)
    brawl = snapshot_r(items, scenario="brawl", runes=runes)
    nor = snapshot_nor(items, scenario="dive", runes=runes)
    tier, score = final_rank(r, nor, brawl)
    return {
        "items": tuple(boots_first(items)),
        "r": r,
        "brawl": brawl,
        "nor": nor,
        "tier": tier,
        "score": score,
        "runes": tuple(runes),
    }


def search() -> List[dict]:
    seen = set()
    ranked: List[dict] = []

    def consider(items: Sequence[str]) -> None:
        fs = frozenset(items)
        if fs in seen or len(fs) != 6:
            return
        if sum(1 for i in fs if i in BOOTS) != 1:
            return
        seen.add(fs)
        r = snapshot_r(items)
        ranked.append({"items": tuple(boots_first(items)), "r": r, "quick": quick_score(r)})

    seeds = [build for _, build in ARCHETYPES]
    for build in seeds:
        consider(build)
    print(f"  cores {len(ranked)}", flush=True)

    for round_i in range(2):
        seeds = [e["items"] for e in sorted(ranked, key=lambda e: e["quick"], reverse=True)[:8]]
        if round_i == 0:
            seeds = [build for _, build in ARCHETYPES]
        before = len(seen)
        for seed in seeds:
            for nb in neighbors(seed):
                consider(nb)
        print(f"  swap round {round_i + 1}: +{len(seen) - before} builds (pool {len(seen)})", flush=True)

    top = sorted(ranked, key=lambda e: e["quick"], reverse=True)[:28]
    print(f"  full-scoring {len(top)} finalists", flush=True)
    full = [evaluate_full(e["items"]) for e in top]
    # Always full-score the named cores so the report can compare them.
    have = {frozenset(e["items"]) for e in full}
    for _, build in ARCHETYPES:
        if frozenset(build) not in have:
            full.append(evaluate_full(build))
    full.sort(key=lambda e: (e["tier"], e["score"]), reverse=True)
    return full


def best_order(items: Sequence[str], runes: Sequence[str] = DEFAULT_RUNES) -> Tuple[str, ...]:
    boots = [i for i in items if i in BOOTS]
    legs = [i for i in items if i not in BOOTS]
    best: Optional[Tuple[float, Tuple[str, ...]]] = None
    minutes = (10, 14, 18, 22, 26, 30)
    for perm in itertools.permutations(legs):
        order = tuple(boots + list(perm))
        score = 0.0
        hs_m = None
        for m in minutes:
            owned = purchase(order, gold_at_minute(m))
            if not owned:
                continue
            if hs_m is None and "Heartsteel" in owned:
                hs_m = m
            fight = run_fight(owned, m, with_r=True, hs_finish=hs_m, scenario="dive", runes=runes)
            live = 1.0 if not fight["died"] else fight["survival"] / COMBAT
            score += fight["total"] * (0.55 + 0.45 * live)
        if best is None or score > best[0]:
            best = (score, order)
    assert best is not None
    return best[1]


RUNE_PAGES = (
    ("Conqueror, Haste, Conditioning", ("conqueror", "haste", "conditioning")),
    ("Conqueror, Haste, Revitalize", ("conqueror", "haste", "revitalize")),
    ("Lethal Tempo, Haste, Conditioning", ("lethal", "haste", "conditioning")),
    ("Lethal Tempo, Alacrity, Revitalize", ("lethal", "alacrity", "revitalize")),
)


def rune_name(runes: Sequence[str]) -> str:
    for label, page in RUNE_PAGES:
        if tuple(page) == tuple(runes):
            return label
    return " / ".join(runes)


def refine_runes(full: List[dict]) -> List[dict]:
    """Re-score the cores and the item-search finalists on each rune page.

    If a page other than the search default wins, swap outward from its best
    builds once, so an attack-speed page can find its own items.
    """
    seeds = [e["items"] for e in full[:12]]
    for _, build in ARCHETYPES:
        if build not in seeds:
            seeds.append(build)
    scored: List[dict] = []
    seen = set()
    for label, page in RUNE_PAGES:
        print(f"  rune page: {label}", flush=True)
        for items in seeds:
            key = (frozenset(items), tuple(page))
            if key in seen:
                continue
            seen.add(key)
            scored.append(evaluate_full(items, page))
    scored.sort(key=lambda e: (e["tier"], e["score"]), reverse=True)
    best_page = scored[0]["runes"]
    if best_page == DEFAULT_RUNES:
        # Keep the wider default-rune search, but carry the rune tag.
        for e in full:
            e["runes"] = DEFAULT_RUNES
        return full
    print(f"  expanding {rune_name(best_page)}", flush=True)
    pool = [e["items"] for e in scored if e["runes"] == best_page][:5]
    extra_seen = {frozenset(items) for items in pool}
    for seed in list(pool):
        for nb in neighbors(seed):
            fs = frozenset(nb)
            if fs in extra_seen or len(fs) != 6:
                continue
            if sum(1 for i in fs if i in BOOTS) != 1:
                continue
            extra_seen.add(fs)
            scored.append(evaluate_full(nb, best_page))
    # The default page's wider search still belongs in the table.
    have = {(frozenset(e["items"]), e["runes"]) for e in scored}
    for e in full:
        key = (frozenset(e["items"]), DEFAULT_RUNES)
        if key not in have:
            e["runes"] = DEFAULT_RUNES
            scored.append(e)
            have.add(key)
    scored.sort(key=lambda e: (e["tier"], e["score"]), reverse=True)
    return scored


def self_check() -> Build:
    for name, it in ITEMS.items():
        finish = it.cost - sum(ITEMS[c].cost for c in it.recipe)
        if finish < 0:
            raise AssertionError(f"negative combine on {name}: {finish}")
        for c in it.recipe:
            if c not in ITEMS:
                raise AssertionError(f"{name} recipe missing {c}")
    for label, build in ARCHETYPES:
        if len(set(build)) != 6:
            raise AssertionError(f"{label} is not 6 unique items")
        if sum(1 for i in build if i in BOOTS) != 1:
            raise AssertionError(f"{label} boots")
        spells = [i for i in build if i in SPELLBLADES]
        if len(spells) > 1:
            raise AssertionError(f"{label} two spellblades {spells}")
        lives = [i for i in build if i in LIFELINES]
        if len(lives) > 1:
            raise AssertionError(f"{label} two lifelines {lives}")
        hydras = [i for i in build if i in HYDRAS]
        if len(hydras) > 1:
            raise AssertionError(f"{label} two hydras {hydras}")

    ref = ARCHETYPES[0][1]
    st = Build(ref, 18, 34, 0, True)
    # Hand calc at level 18 with R, Conqueror AD, +5.4 shard, Overgrowth, Conditioning.
    problems = []
    def near(got, exp, tol, label):
        if abs(got - exp) > tol:
            problems.append(f"{label}: got {got:.3f} expected {exp:.3f}")

    near(st.max_hp, 5371.905, 1.5, "max HP")
    near(st.total_ad(0.0), 371.658, 0.2, "AD")
    near(st.w2_premit(0.0), 1463.58, 2.0, "W2")
    near(st.e_shield(), 940.083, 2.0, "E shield")
    near(st.sterak_shield(), 2215.429, 2.0, "Sterak")
    near(st.base_armor + st.bonus_armor, 208.89, 0.3, "armor")
    near(st.base_mr + st.bonus_mr, 126.59, 0.3, "MR")
    near(st.w_cd, 3.0303, 0.02, "W cd")
    # 0.625 + (34% level + 10% rune + 25% passive) * 0.7 ratio.
    near(st.aspeed, 1.108, 0.01, "AS")
    if problems:
        raise AssertionError("stat check failed:\n  " + "\n  ".join(problems))

    total = sum(ITEMS[n].cost for n in ref)
    assert sorted(purchase(ref, total)) == sorted(ref)
    assert sorted(purchase(ref, total - 1)) != sorted(ref)

    t0 = time.perf_counter()
    fight = run_fight(ref, 34, with_r=True, trace=True, scenario="dive")
    dt = time.perf_counter() - t0
    print(f"reference fight {dt*1000:.1f} ms  dmg {fight['total']:.0f}  "
          f"lived {fight['survival']:.1f}s  died {fight['died']}  "
          f"end {fight['end_hp']:.0f}  bites {fight['w_bites']}  W {fight['w_casts']}  "
          f"autos {fight['autos']}  healed {fight['healed']:.0f}")
    for line in fight["logs"]:
        print("   ", line)
    if fight["w_bites"] < 1 or fight["total"] < 2000:
        raise AssertionError("reference fight did not bite or did no damage")
    print("stat check ok", f"W2 {st.w2_premit():.0f}", f"HP {st.max_hp:.0f}", f"AD {st.total_ad(0):.0f}")
    return st


def pct(fight: dict) -> float:
    if fight["max_hp"] <= 0:
        return 0.0
    return 100.0 * fight["end_hp"] / fight["max_hp"]


def render(full: List[dict], order: Tuple[str, ...], arch_by_items: Dict[frozenset, str]) -> str:
    winner = full[0]
    items = order
    r, nor, brawl = winner["r"], winner["nor"], winner["brawl"]
    names = {frozenset(build): label for label, build in ARCHETYPES}
    # Recompute winner fights are already on the item set; order is purchase only.
    wset = frozenset(winner["items"])

    def label_of(ev: dict) -> str:
        return names.get(frozenset(ev["items"]), show(ev["items"]))

    lines: List[str] = []
    a = lines.append
    a("=" * 78)
    a("VOLIBEAR — LATE GAME, HARD TO KILL, HIGH DAMAGE   (PC LoL patch 26.21)")
    a("Playstyle: R onto the carry, stand in E, keep biting  |  Game: 34:00")
    a("Must live the Stormbringer window under carry+mage focus, then max damage")
    a("=" * 78)
    a("")
    a("WHAT THE BITE ACTUALLY SCALES WITH")
    a("  W1 = 105 + 110% AD + 6% bonus HP")
    a("  W2 = W1 × (1.50 + 0.25 per 100 bonus AD) and heals 80 + 20% missing HP")
    a("  Bonus HP is inside the multiplier. Bonus AD raises the multiplier.")
    a("  Overlord's Bloodmail is 2.5% of bonus HP as AD, plus up to 12% more AD")
    a("  when missing health. That AD feeds W, the bite amp, Q (160% bonus AD)")
    a("  and R (250% bonus AD). Spirit Visage does not raise the bite. It raises")
    a("  the heal, the E shield and the Sterak shield, which is why he gets to bite.")
    a("")
    runes = winner.get("runes", DEFAULT_RUNES)
    a("WINNER")
    a(f"  {show(items)}")
    known = names.get(wset)
    if known:
        a(f"  Search name: {known}")
    a(f"  Runes: {rune_name(runes)}")
    a(f"  R dive:     {r['total']:.0f} damage   lived {r['survival']:.1f}s   "
      f"end HP {r['end_hp']:.0f} / {r['max_hp']:.0f} ({pct(r):.0f}%)")
    a(f"              carry {r['carry']:.0f}   tank {r['tank']:.0f}   "
      f"healed {r['healed']:.0f}   shields absorbed {r['absorbed']:.0f}")
    a(f"  R brawl:    {brawl['total']:.0f} damage on the frontline  lived {brawl['survival']:.1f}s")
    a(f"  No ultimate:{nor['total']:.0f} damage   lived {nor['survival']:.1f}s   "
      f"end HP {pct(nor):.0f}%")
    a(f"  Bites {r['w_bites']}   W casts {r['w_casts']}   autos {r['autos']}   "
      f"spellblades {r['spellblades']}   E hits {r['e_hits']}")
    a("")
    a("DAMAGE BY SOURCE  (R dive, post-mitigation)")
    for key, val in sorted(r["sources"].items(), key=lambda kv: -kv[1]):
        if val < 1:
            continue
        a(f"  {key:<12} {val:>7.0f}")
    a("")
    a("HEALS")
    for key, val in sorted(r["heals"].items(), key=lambda kv: -kv[1]):
        if val < 1:
            continue
        a(f"  {key:<12} {val:>7.0f}")
    a("")
    st = Build(
        items, 18, 34, hs_procs_for(34, items, 14), True,
        keystone=runes[0], legend=runes[1], secondary=runes[2],
    )
    a("LEVEL 18, ULT UP")
    a(f"  HP {st.max_hp:.0f} (bonus {st.bonus_hp:.0f}, includes +{st.r_hp:.0f} from R)")
    a(f"  AD {st.total_ad(0):.0f}  ({st.bonus_ad_flat:.0f} bonus, Bloodmail tyranny {st.tyranny:.0f})")
    a(f"  At 40% missing HP, Retribution adds {st.bonus_ad(0.40) - st.bonus_ad_flat:.0f} AD")
    a(f"  AP {st.ap:.0f}   armor {st.base_armor + st.bonus_armor:.0f}   MR {st.base_mr + st.bonus_mr:.0f}")
    a(f"  W cooldown {st.w_cd:.2f}s   attack speed {st.aspeed:.2f} at 5 passive stacks")
    a("  Sheet attack speed is before Lethal Tempo stacks, Guinsoo stacks and Hexplate.")
    a(f"  W2 pre-mit at full HP {st.w2_premit(0):.0f}   at 40% missing {st.w2_premit(0.40):.0f}")
    a(f"  E shield {st.e_shield():.0f}   Sterak shield {st.sterak_shield():.0f}")
    if "Protoplasm Harness" in set(items) and r["max_hp"] > st.max_hp + 50:
        a(f"  The fight's max HP is {r['max_hp']:.0f} while Protoplasm's +300 bonus HP is up.")
    a(f"  Adaptive shard: {st.adapt}")
    if st.keystone == "conqueror":
        a("  AD and AP above include fully stacked Conqueror. The fight ramps it from zero.")
    else:
        a("  Lethal Tempo adds attack speed and a bolt during the fight. It is not in the AD.")
    a("")

    # Grievous stress on the winner and a few finalists.
    a("40% GRIEVOUS  (Ignite / Thornmail up the whole window)")
    grievous_rows = []
    for ev in full[:8]:
        g = snapshot_r(ev["items"], grievous=True, scenario="dive", runes=ev.get("runes", DEFAULT_RUNES))
        grievous_rows.append((ev, g))
        a(f"  {show(ev['items'])}  dmg {g['total']:.0f}  "
          f"lived {g['survival']:.1f}s  end {pct(g):.0f}%  died {g['died']}")
    a("")

    a("-" * 78)
    a("FULL BUILDS AT 34:00  (tier 2 lives the ult and the no-ult fight)")
    a("  Rune mark: blank = Conqueror/Haste/Conditioning, LT = Lethal Tempo,")
    a("  RV = Revitalize instead of Conditioning, AL = Legend: Alacrity")
    a(f"  {'':<4} {'R dmg':>7} {'Live':>6} {'End':>5} {'Brawl':>7} {'NoR':>6} T  Build")
    for ev in full[:18]:
        page = ev.get("runes", DEFAULT_RUNES)
        mark = ""
        if page[0] == "lethal":
            mark += "LT"
        if page[1] == "alacrity":
            mark += "AL"
        if page[2] == "revitalize":
            mark += "RV"
        a(f"  {mark:<4} {ev['r']['total']:>7.0f} {ev['r']['survival']:>5.1f}s "
          f"{pct(ev['r']):>4.0f}% {ev['brawl']['total']:>7.0f} {ev['nor']['survival']:>5.1f}s {ev['tier']}  {show(ev['items'])}")
    a("")

    # Path curve for the winning order vs tank vs glass vs AP bruiser.
    a("-" * 78)
    a("PURCHASE ORDER  (same 6 items, order maximizes damage from 10:00 to 30:00)")
    a(f"  {show(items)}")
    a("")
    a(f"  {'Min':>4} {'Gold':>7} {'Lvl':>4}  Inventory")
    hs_m = finish_minute(items, "Heartsteel")
    for m in list(range(6, 35, 2)) + [34]:
        owned = purchase(items, gold_at_minute(m))
        inv = " › ".join(short(n) for n in owned) if owned else "(doran's only)"
        if len(inv) > 86:
            inv = inv[:83] + "…"
        a(f"  {m:>4} {gold_at_minute(m):>7} {level_at_minute(m):>4}  {inv}")
    a("")

    compare_orders = [("Winner", items)]
    for label, build in ARCHETYPES:
        if label in ("Full Tank", "AP Glass", "AP Nashor", "Trinity Bruiser", "Heartsteel Titan", "Endless Drain", "Bloodmail Warlord"):
            compare_orders.append((label, build))
    a("-" * 78)
    a("PATH VS THE TRAPS  — R-dive damage at that minute's gold (scaled focus)")
    header = f"  {'Min':>4}" + "".join(f" {name[:12]:>12}" for name, _ in compare_orders)
    a(header)
    for m in (8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 34):
        cells = [f"{m:>4}"]
        for _, order_i in compare_orders:
            owned = purchase(order_i, gold_at_minute(m))
            if not owned:
                cells.append(f"{'—':>12}")
                continue
            fm = None
            if "Heartsteel" in order_i:
                fm = finish_minute(order_i, "Heartsteel")
            page = runes if order_i == items else DEFAULT_RUNES
            fight = run_fight(owned, m, with_r=True, hs_finish=fm, scenario="dive", runes=page)
            mark = "*" if fight["died"] else " "
            cells.append(f"{fight['total']:>10.0f}{mark} ")
        a("  " + "".join(cells))
    a("  * died during the window. Focus scales up to the 34:00 carry+mage number.")
    a("")

    tank = next(ev for ev in full if frozenset(ev["items"]) == frozenset(ARCHETYPES[5][1]))
    glass = next(ev for ev in full if frozenset(ev["items"]) == frozenset(dict(ARCHETYPES)["AP Glass"]))
    a("-" * 78)
    a("VERDICT")
    a("-" * 78)
    a(f"  Buy: {show(items)}")
    a("")
    owned_set = set(items)
    a("  WHY THIS IS THE LATE-GAME VOLIBEAR:")
    a("  • The wounded bite multiplies bonus health by bonus AD. A tank with the")
    a("    same health and no AD leaves that multiplier at 1.50x. This build's")
    a(f"    bite amp at full HP, Conqueror counted only if it is the keystone, is {1.5 + st.bonus_ad(0)/400:.2f}x.")
    if "Overlord's Bloodmail" in owned_set:
        a("  • Bloodmail turns that same bonus HP into AD (2.5%) and adds up to 12%")
        a("    more AD as he drops, which is when Last Stand and the W heal are both")
        a("    online. The AD feeds W, Q (160% bonus AD) and R (250% bonus AD).")
    if "Spear of Shojin" in owned_set:
        a(f"  • Shojin is 25 basic ability haste plus up to 12% ability damage. W's")
        a(f"    base 5s becomes {st.w_cd:.2f}s before Navori, so the second bite and")
        a("    the missing-health heal happen inside the ultimate.")
    if "Sterak's Gage" in owned_set:
        a("  • Sterak is 50% base AD, which counts as bonus AD for Q, W and R, and a")
        a("    60% bonus-HP shield at 30% life.")
    if "Maw of Malmortius" in owned_set:
        a("  • Maw is the magic Lifeline: a shield of 200 + 150% bonus AD and 10%")
        a("    omnivamp for the rest of the fight. It cannot be paired with Sterak.")
    if "Protoplasm Harness" in owned_set:
        a("  • Protoplasm is the tank Lifeline: bonus HP and a resist-scaled heal")
        a("    when he crosses 30% life. It shares the Lifeline slot with Sterak.")
    if "Spirit Visage" in owned_set:
        a("  • Visage is +25% healing and shielding. It does not raise the bite.")
        a("    It raises the W heal, the E shield and whichever Lifeline he has,")
        a("    which is why he is still standing for the next bite.")
    if "Unending Despair" in owned_set or "Death's Dance" in owned_set:
        a("  • The armor item is what stops the carry from deleting him before that")
        a("    second bite. Unending also heals off the enemies standing in the ult.")
    if "Dusk and Dawn" in owned_set:
        a("  • Dusk and Dawn is the spellblade that heals (10% AP + 3% bonus HP)")
        a("    and applies on-hit effects a second time. Lightning only starts at")
        a("    5 passive stacks, so the repeat matters once the claws are on.")
    if "Navori Flickerblade" in owned_set:
        a("  • Navori is how the bite comes back inside the ultimate. Each auto")
        a("    cuts 15% off the remaining W, E and Q cooldowns, and the 25% crit")
        a("    is on the attack itself. He has to be in range and autoing.")
    if "Statikk Shiv" in owned_set:
        a("  • Statikk's chain applies on-hit to the second champion once per")
        a("    energized attack. The leap starts the charge.")
    if "Experimental Hexplate" in owned_set:
        a("  • Hexplate's Overdrive is 50% bonus attack speed for 7s of the 8s")
        a("    after the ultimate cast. The fight the build is for is that window.")
    legs = [i for i in items if i not in BOOTS]
    if legs and legs[0] == "Protoplasm Harness":
        a("  • Protoplasm is first on purpose. The same six items with Navori or")
        a("    Cleaver rushed are still dying in the 30:00 focus. The Lifeline is")
        a("    why the 26:00 version, Visage just finished, already stands up.")
    a("  • R's +525 HP is bonus health for the bite and for both shields. The")
    a("    no-ult column is there so a build that only exists for 12 seconds")
    a("    does not win.")
    a("")
    a(f"  Vs full tank ({show(ARCHETYPES[5][1])}):")
    a(f"    tank R-dive {tank['r']['total']:.0f} in {tank['r']['survival']:.1f}s "
      f"(end {pct(tank['r']):.0f}%)   this build {r['total']:.0f} in {r['survival']:.1f}s "
      f"(end {pct(r):.0f}%).")
    a("    The tank lives. The bite does not, because nothing is feeding bonus AD")
    a("    into the multiplier. Heartsteel damage does not replace W2.")
    a(f"  Vs AP glass ({show(dict(ARCHETYPES)['AP Glass'])}):")
    a(f"    glass R-dive {glass['r']['total']:.0f} in {glass['r']['survival']:.1f}s, died={glass['r']['died']}.")
    a("    E and lightning scale with AP, and the E shield is real, but W heal")
    a("    has no AP ratio on this patch. Focused, the glass build falls over")
    a("    before the bites come back. High damage on a target dummy, not in a fight.")
    a("")
    # Grievous note
    g_win = grievous_rows[0][1]
    survivors = [(ev, g) for ev, g in grievous_rows if not g["died"]]
    a("  ANTIHEAL:")
    if not g_win["died"]:
        a(f"    With 40% grievous the winner still stands ({g_win['survival']:.1f}s, "
          f"end {pct(g_win):.0f}%, {g_win['total']:.0f} damage). Shields are not reduced.")
    else:
        a(f"    With 40% grievous the winner dies at {g_win['survival']:.1f}s.")
        if survivors:
            alt, g = max(survivors, key=lambda pair: pair[1]["total"])
            a(f"    If they have Ignite and a Thornmail, prefer {show(alt['items'])}")
            a(f"    ({g['total']:.0f} damage, lived, end {pct(g):.0f}%).")
        else:
            a("    Nothing in the top 8 fully lives a grevious window. Sterak + E shield")
            a("    still delay the death; do not drop them for more AD.")
    a("")
    keystone, legend, secondary = runes
    legend_label = "Legend: Alacrity" if legend == "alacrity" else "Legend: Haste"
    secondary_label = "Revitalize" if secondary == "revitalize" else "Conditioning"
    keystone_label = "Lethal Tempo" if keystone == "lethal" else "Conqueror"
    a("  RUNES (baked into the sim):")
    a(f"    {keystone_label}, Triumph, {legend_label}, Last Stand")
    a(f"    {secondary_label}, Overgrowth")
    a("    Attack speed, adaptive force, health shard +65")
    a("  SKILL ORDER: W max, E second (the %HP bolt), Q last. R at 6/11/16.")
    a("  FIGHT: E on the dive spot, Q, R into it so you land as E hits, Q auto,")
    a("    bite, keep autoing. Navori does nothing if he is kited. The carry is")
    a("    the one he bites. The other champion eats R, E and the lightning chain.")
    a("")
    a("  TRAPS:")
    a("    • Heartsteel + pure resists. You are hard to kill and the bite stays")
    a("      a 1.5x slap. Bloodmail is the item that makes the health deal damage.")
    a("    • Deathcap / Nashor with no health. Lightning looks good for 4 seconds.")
    a("    • Trinity instead of Shojin + Bloodmail. Spellblade is 200% base AD")
    a("      and does not scale with the bonus AD the bite wants. Trinity is the")
    a("      1-item spike, not the 6-item ceiling.")
    a("    • Hullbreaker in a 5v5. The solo resist passive is off in this fight.")
    a("    • Stacking two Spellblades. Dusk, Trinity and Iceborn share the slot.")
    a("      Dusk is the one that also heals (10% AP + 3% bonus HP) and repeats")
    a("      on-hits. Take it when the team is magic-heavy, not by default.")
    a("")
    a("  MODEL (so the numbers stay honest):")
    a("    Patch 26.21 item stats and Volibear ratios from the wiki (V26.19 kit,")
    a("    V26.21 items). 11s focus after the R landing. Incoming at 34:00 is")
    a(f"    {PHYS_DPS:.0f} pre-mit physical (30% pen, 12 lethality, Steelcaps/Randuin")
    a(f"    applied) and {MAGIC_DPS:.0f} pre-mit magic (35% pen, 10 flat). Two champions")
    a("    in the fight: the one he is biting, and one other for R/E/Unending/chain.")
    a("    Heartsteel assumes about 0.75 procs a minute after it is finished,")
    a("    capped at 18. Conqueror starts at 0 and gains 2 stacks per hit, up to")
    a("    12. Lethal Tempo ramps to 6 on-hit stacks, then its bolt scales with")
    a("    bonus attack speed. Lightning Claws turns on at 5 passive stacks, and")
    a("    the hit that reaches 5 is empowered. Attack speed uses Volibear's 0.7")
    a("    ratio and the 3.003 cap. Grievous is a separate column, not the ranking.")
    a("    Tenacity shortens one 1.15s peel. No flash, no turret, no Elder.")
    a("    Search swapped items on the cores until neighbors stopped winning on")
    a("    'lived the fight, then damage', then re-scored the finalists on four")
    a("    rune pages.")
    a("=" * 78)
    return "\n".join(lines) + "\n"


def main() -> None:
    t0 = time.perf_counter()
    print("checking kit math...", flush=True)
    self_check()
    print("searching 6-item builds...", flush=True)
    full = search()
    print("comparing rune pages...", flush=True)
    full = refine_runes(full)
    winner_items = full[0]["items"]
    winner_runes = full[0].get("runes", DEFAULT_RUNES)
    print("ordering", show(winner_items), rune_name(winner_runes), flush=True)
    order = best_order(winner_items, winner_runes)
    # Attach the winning order's full eval (same items).
    text = render(full, order, {})
    report_path = os.path.join(HERE, "report.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(text)
    payload = []
    for ev in full[:20]:
        payload.append({
            "items": list(ev["items"]),
            "order_shown": show(ev["items"]),
            "runes": list(ev.get("runes", DEFAULT_RUNES)),
            "tier": ev["tier"],
            "score": round(ev["score"], 1),
            "r_damage": round(ev["r"]["total"], 1),
            "r_survival": round(ev["r"]["survival"], 2),
            "r_end_hp": round(ev["r"]["end_hp"], 1),
            "r_max_hp": round(ev["r"]["max_hp"], 1),
            "r_died": ev["r"]["died"],
            "brawl_damage": round(ev["brawl"]["total"], 1),
            "nor_damage": round(ev["nor"]["total"], 1),
            "nor_survival": round(ev["nor"]["survival"], 2),
            "nor_died": ev["nor"]["died"],
            "sources": {k: round(v, 1) for k, v in ev["r"]["sources"].items()},
        })
    with open(os.path.join(HERE, "results.json"), "w", encoding="utf-8") as f:
        json.dump({"winner_order": list(order), "builds": payload}, f, indent=2)
    print(text)
    print(f"done in {time.perf_counter() - t0:.1f}s")


if __name__ == "__main__":
    main()
