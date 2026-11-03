#!/usr/bin/env python3
"""
Wild Rift Volibear, baron lane, patch 7.3d.

Question: the late-game six-item set that is hard to kill in a focused
teamfight and still deals high damage. Level cap is 15. The fight is an
11-second Stormbringer window at 18:00.

Kit (wiki + patch 7.3b, which the 7.3d notes did not touch):
  Passive  5% (+4% per 100 AP) attack speed per stack, max 5.
            Lightning at 5 stacks: 12–68 by level + 40% AP. No AD ratio.
            Attacks stay empowered at 5 stacks and chain to the other champion.
  Q  15/40/65/90 + 100% bonus AD, stun 1s, attack reset. CD 13/12/11/10.
     Immobilize pauses the buff instead of cancelling it.
  W  5/30/55/80 + 110% AD + 6.5% bonus HP. Mauling a champion grants
     Frenzy for 8s. The next maul while Frenzied is exactly 1.6× and
     heals 20/30/40/50 + 5/8/11/14% missing HP. Frenzy is on Volibear,
     not a mark on the target. CD 5. Applies on-hit and on-attack.
  E  80/110/140/170 + 50% AP + 11/12/13/14% target max HP. Shield is
     14% max HP + 75% AP for 2.5s. CD 13. Lands 2s after the cast.
  R  300/500/700 + 210% bonus AD + 100% AP, and +175/350/525 HP for 12s.
     Leap 1s. CD 90/80/70.

Attack speed (patch 7.3): base 0.7, ratio 0.7, level-1 bonus AS 0.05,
+0.014 bonus AS per level, cap 3.0. Crit damage 200%.
Stats grow linearly: base + growth × (level − 1).

Spirit Visage was removed in 7.0. There is no Overlord's Bloodmail and
no Protoplasm Harness. The tank Lifeline is Mantle of the Twelfth Hour.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple
import itertools
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
GAME_MINUTES = 18
DT = 0.1
SURVIVE = 11.0

# 18:00 focus: a fed marksman plus a mage, for the whole window.
# Tuned so a real frontliner can live the ultimate and a no-health
# AP build cannot. Pre-mitigation.
PHYS_DPS = 900.0
MAGIC_DPS = 520.0
BASE_CC = 1.0


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


# --- components. Costs match the 7.3 build paths used below. ---
add(I("Boots", 500))
add(I("Dagger", 400, as_pct=0.10))
add(I("Long Sword", 500, ad=12))
add(I("Ruby Crystal", 500, hp=150))
add(I("Cloth Armor", 500, armor=20))
add(I("Null-Magic Mantle", 500, mr=20))
add(I("Amplifying Tome", 500, ap=20))
add(I("Pickaxe", 800, recipe=("Long Sword",), ad=25))
add(I("Blasting Wand", 800, ap=40))
add(I("Needlessly Large Rod", 1400, ap=65))
add(I("B. F. Sword", 1500, ad=40))
add(I("Recurve Bow", 900, recipe=("Dagger",), as_pct=0.15))
add(I("Chain Vest", 900, armor=40))
add(I("Negatron Cloak", 900, mr=40))
add(I("Giant's Belt", 1000, recipe=("Ruby Crystal", "Ruby Crystal"), hp=300))
add(I("Kindlegem", 1000, recipe=("Ruby Crystal",), hp=200, ah=10))
add(I("Sheen", 800, tags=("sheen",)))
add(I("Phage", 1000, recipe=("Long Sword", "Ruby Crystal"), ad=15, hp=200))
add(I("Caulfield's Warhammer", 1200, recipe=("Long Sword", "Long Sword"), ad=20, ah=10))
add(I("Jaurim's Fist", 1200, recipe=("Long Sword", "Ruby Crystal"), ad=15, hp=200))
add(I("Fiendish Codex", 900, recipe=("Amplifying Tome",), ap=25, ah=10))
add(I("Haunting Guise", 1300, recipe=("Amplifying Tome", "Ruby Crystal"), ap=30, hp=200))
add(I("Fated Ashes", 900, recipe=("Amplifying Tome",), ap=30))
add(I("Aether Wisp", 950, recipe=("Amplifying Tome",), ap=35))
add(I("Hearthbound Axe", 1200, ad=20, as_pct=0.20))
add(I("Kircheis Shard", 800, recipe=("Dagger",), as_pct=0.15))
add(I("Zeal", 1400, recipe=("Dagger", "Dagger"), as_pct=0.15, crit=0.15))
add(I("Vampiric Scepter", 1200, recipe=("Long Sword",), ad=15, lifesteal=0.10))
add(I("Glacial Buckler", 1000, recipe=("Cloth Armor",), armor=20, ah=10, mana=150))
add(I("Spectre's Cowl", 1100, recipe=("Null-Magic Mantle", "Ruby Crystal"), hp=175, mr=20))
add(I("Warden's Mail", 1050, armor=35))
add(I("Bami's Cinder", 1200, hp=250, ah=5))
add(I("Winged Moonplate", 900, recipe=("Ruby Crystal",), hp=150))
add(I("Blighting Jewel", 1000, ap=20, magic_pen=0.10))
add(I("Seeker's Armguard", 1400, ap=35, armor=20))

# --- boots. Enchant is the same slot, not a seventh item. ---
add(I("Plated Steelcaps", 1200, recipe=("Boots", "Cloth Armor"), hp=150, armor=20, tags=("boots", "steelcaps")))
add(I("Mercury's Treads", 1200, recipe=("Boots", "Null-Magic Mantle"), hp=150, mr=25, tenacity=0.30, tags=("boots", "mercs")))
add(I("Armored Advance", 2200, recipe=("Plated Steelcaps",), hp=150, armor=30, tags=("boots", "steelcaps", "advance")))
add(I("Chainlaced Crushers", 2200, recipe=("Mercury's Treads",), hp=150, mr=30, tenacity=0.30, tags=("boots", "crushers")))
add(I("Immortal Treads", 2000, recipe=("Boots",), omnivamp=0.05, tags=("boots", "immortal")))

# --- finished items (patch 7.3 / 7.3d stat pass) ---
add(I("Dusk and Dawn", 3100, recipe=("Sheen", "Blasting Wand", "Kindlegem", "Dagger"), ap=60, ah=20, as_pct=0.20, hp=300, tags=("item", "dusk")))
add(I("Navori Quickblades", 2650, recipe=("Dagger", "Zeal", "Dagger"), as_pct=0.40, crit=0.25, tags=("item", "navori")))
add(I("Heartsteel", 2800, recipe=("Ruby Crystal", "Kindlegem", "Giant's Belt"), hp=700, ah=20, tags=("item", "heartsteel")))
add(I("Trinity Force", 3333, recipe=("Sheen", "Phage", "Hearthbound Axe"), ad=36, ah=15, as_pct=0.30, hp=333, tags=("item", "trinity")))
add(I("Divine Sunderer", 3300, recipe=("Sheen", "Kindlegem", "Jaurim's Fist"), ad=25, ah=25, hp=425, tags=("item", "divine")))
add(I("Hullbreaker", 3100, recipe=("Jaurim's Fist", "Jaurim's Fist"), ad=50, hp=400, tags=("item", "hull")))
add(I("Sterak's Gage", 3200, recipe=("B. F. Sword", "Jaurim's Fist"), hp=400, tenacity=0.20, tags=("item", "sterak", "lifeline")))
add(I("Titanic Hydra", 3000, recipe=("Pickaxe", "Jaurim's Fist", "Ruby Crystal"), ad=40, hp=450, tags=("item", "titanic")))
add(I("Sundered Sky", 2900, recipe=("Caulfield's Warhammer", "Jaurim's Fist"), ad=40, ah=15, hp=350, tags=("item", "sundered")))
add(I("Black Cleaver", 3000, recipe=("Phage", "Kindlegem", "Long Sword"), ad=40, ah=20, hp=400, tags=("item", "cleaver")))
add(I("Death's Dance", 3300, recipe=("Caulfield's Warhammer", "Pickaxe", "Chain Vest"), ad=50, ah=15, armor=45, tags=("item", "dd")))
add(I("Spear of Shojin", 3100, recipe=("Jaurim's Fist", "Jaurim's Fist"), ad=40, hp=450, ah=20, tags=("item", "shojin")))
add(I("Eclipse", 2900, recipe=("Caulfield's Warhammer", "Caulfield's Warhammer"), ad=65, ah=20, tags=("item", "eclipse")))
add(I("Blade of the Ruined King", 3100, recipe=("Vampiric Scepter", "Pickaxe", "Recurve Bow"), ad=40, as_pct=0.30, lifesteal=0.12, tags=("item", "bork")))
add(I("Guinsoo's Rageblade", 3000, recipe=("Amplifying Tome", "Recurve Bow", "Pickaxe"), ad=35, ap=30, as_pct=0.30, tags=("item", "guinsoo")))
add(I("At Wit's End", 2800, recipe=("Recurve Bow", "Negatron Cloak", "Dagger"), as_pct=0.50, mr=45, tenacity=0.20, tags=("item", "wits")))
add(I("Terminus", 3000, recipe=("Recurve Bow", "Hearthbound Axe"), ad=35, as_pct=0.35, tags=("item", "terminus")))
add(I("Statikk Shiv", 3000, recipe=("Aether Wisp", "Pickaxe", "Kircheis Shard"), ad=40, ap=40, as_pct=0.30, tags=("item", "statikk")))
add(I("Unending Despair", 3000, recipe=("Kindlegem", "Chain Vest", "Negatron Cloak"), ah=10, hp=300, armor=40, mr=40, tags=("item", "unending")))
add(I("Amaranth's Twinguard", 3200, recipe=("Giant's Belt", "Chain Vest", "Negatron Cloak"), hp=300, armor=50, mr=50, tags=("item", "twinguard")))
add(I("Thornmail", 2850, recipe=("Chain Vest", "Ruby Crystal", "Cloth Armor"), hp=200, armor=75, tags=("item", "thorn")))
add(I("Randuin's Omen", 2800, recipe=("Giant's Belt", "Warden's Mail"), hp=400, armor=75, tags=("item", "randuin")))
add(I("Sunfire Aegis", 2900, recipe=("Bami's Cinder", "Chain Vest", "Ruby Crystal"), ah=15, hp=350, armor=40, tags=("item", "sunfire")))
add(I("Iceborn Gauntlet", 3000, recipe=("Sheen", "Glacial Buckler", "Kindlegem"), ah=30, hp=300, armor=50, mana=500, tags=("item", "iceborn")))
add(I("Force of Nature", 2800, recipe=("Winged Moonplate", "Negatron Cloak", "Ruby Crystal"), hp=400, mr=80, tags=("item", "fon")))
add(I("Kaenic Rookern", 2800, recipe=("Negatron Cloak", "Spectre's Cowl"), hp=550, mr=80, tags=("item", "kaenic")))
add(I("Mantle of the Twelfth Hour", 2550, recipe=("Kindlegem", "Giant's Belt"), ah=20, hp=600, tags=("item", "mantle", "lifeline")))
add(I("Radiant Virtue", 2650, recipe=("Giant's Belt", "Cloth Armor", "Null-Magic Mantle"), ah=10, hp=300, armor=30, mr=30, tags=("item", "radiant")))
add(I("Frozen Heart", 2550, recipe=("Glacial Buckler", "Warden's Mail"), ah=20, armor=80, mana=600, tags=("item", "frozen")))
add(I("Dead Man's Plate", 2800, recipe=("Winged Moonplate", "Chain Vest", "Ruby Crystal"), hp=350, armor=70, tags=("item", "deadman")))
add(I("Warmog's Armor", 2850, recipe=("Giant's Belt", "Giant's Belt", "Ruby Crystal"), ah=20, hp=700, tags=("item", "warmog")))
add(I("Riftmaker", 3100, recipe=("Haunting Guise", "Fiendish Codex"), ap=70, ah=15, hp=350, tags=("item", "rift")))
add(I("Nashor's Tooth", 2900, recipe=("Recurve Bow", "Blasting Wand", "Fiendish Codex"), ap=80, ah=15, as_pct=0.50, tags=("item", "nashor")))
add(I("Rabadon's Deathcap", 3400, recipe=("Needlessly Large Rod", "Needlessly Large Rod"), ap=130, tags=("item", "deathcap")))
add(I("Liandry's Torment", 3000, recipe=("Haunting Guise", "Fated Ashes"), ap=70, hp=300, tags=("item", "liandry")))
add(I("Void Staff", 3000, recipe=("Blighting Jewel", "Blasting Wand"), ap=95, magic_pen=0.40, tags=("item", "void")))
add(I("Infinity Orb", 3100, recipe=("Needlessly Large Rod", "Blighting Jewel"), ap=110, flat_mpen=15, tags=("item", "orb")))
add(I("Cosmic Drive", 3000, recipe=("Kindlegem", "Fiendish Codex", "Aether Wisp"), ap=70, ah=25, hp=300, tags=("item", "cosmic")))
add(I("Abyssal Mask", 2400, recipe=("Kindlegem", "Negatron Cloak"), ah=10, hp=350, mr=45, tags=("item", "abyssal")))
add(I("Zhonya's Hourglass", 3300, recipe=("Seeker's Armguard", "Needlessly Large Rod"), ap=110, armor=40, tags=("item", "zhonya")))

BOOTS = (
    "Plated Steelcaps",
    "Mercury's Treads",
    "Armored Advance",
    "Chainlaced Crushers",
    "Immortal Treads",
)
SPELLBLADES = ("Trinity Force", "Dusk and Dawn", "Divine Sunderer", "Iceborn Gauntlet")
LIFELINES = ("Sterak's Gage", "Mantle of the Twelfth Hour")
LEGENDARIES: Tuple[str, ...] = tuple(
    n for n, it in ITEMS.items() if "item" in it.tags
)

SHORT = {
    "Plated Steelcaps": "Steelcaps",
    "Mercury's Treads": "Mercs",
    "Armored Advance": "Armored",
    "Chainlaced Crushers": "Chainlaced",
    "Immortal Treads": "Immortal",
    "Dusk and Dawn": "Dusk",
    "Navori Quickblades": "Navori",
    "Heartsteel": "Heartsteel",
    "Trinity Force": "Trinity",
    "Divine Sunderer": "Divine",
    "Hullbreaker": "Hullbreaker",
    "Sterak's Gage": "Sterak",
    "Titanic Hydra": "Titanic",
    "Sundered Sky": "Sundered",
    "Black Cleaver": "Cleaver",
    "Death's Dance": "DD",
    "Spear of Shojin": "Shojin",
    "Eclipse": "Eclipse",
    "Blade of the Ruined King": "BotRK",
    "Guinsoo's Rageblade": "Guinsoo",
    "At Wit's End": "Wit's End",
    "Terminus": "Terminus",
    "Statikk Shiv": "Statikk",
    "Unending Despair": "Unending",
    "Amaranth's Twinguard": "Twinguard",
    "Thornmail": "Thornmail",
    "Randuin's Omen": "Randuin",
    "Sunfire Aegis": "Sunfire",
    "Iceborn Gauntlet": "Iceborn",
    "Force of Nature": "FoN",
    "Kaenic Rookern": "Kaenic",
    "Mantle of the Twelfth Hour": "Mantle",
    "Radiant Virtue": "Radiant",
    "Frozen Heart": "Frozen Heart",
    "Dead Man's Plate": "Dead Man",
    "Warmog's Armor": "Warmog",
    "Riftmaker": "Riftmaker",
    "Nashor's Tooth": "Nashor",
    "Rabadon's Deathcap": "Deathcap",
    "Liandry's Torment": "Liandry",
    "Void Staff": "Void",
    "Infinity Orb": "Infinity Orb",
    "Cosmic Drive": "Cosmic",
    "Abyssal Mask": "Abyssal",
    "Zhonya's Hourglass": "Zhonya",
}

AS_BASE = 0.7
AS_RATIO = 0.7
AS_CAP = 3.0
SKILL_SEQ = "WEWERWWEREQQRQQ"
Q_BASE = (0, 15, 40, 65, 90)
Q_CD = (0.0, 13.0, 12.0, 11.0, 10.0)
W_BASE = (0, 5, 30, 55, 80)
W_HEAL = (0, 20, 30, 40, 50)
W_HEAL_PCT = (0, 0.05, 0.08, 0.11, 0.14)
E_BASE = (0, 80, 110, 140, 170)
E_PCT = (0, 0.11, 0.12, 0.13, 0.14)
R_BASE = (0, 300, 500, 700)
R_HP = (0, 175, 350, 525)


def short(name: str) -> str:
    return SHORT.get(name, name)


def show(items: Sequence[str]) -> str:
    boots = [short(i) for i in items if i in BOOTS]
    legs = [short(i) for i in items if i not in BOOTS]
    return " → ".join(boots + legs)


def gold_at_minute(m: int) -> int:
    """Baron lane with farm and a few fights. A ~15k set finishes ~17:00."""
    if m <= 0:
        return 500
    total = 500
    for t in range(1, m + 1):
        if t <= 4:
            total += 520
        elif t <= 10:
            total += 860
        else:
            total += 1320
    return total


def level_at_minute(m: int) -> int:
    # 5 by ~4:00, 9 by 8:00, 13 by 12:00, 15 by 14:00.
    table = {0: 1, 1: 1, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7, 7: 8, 8: 9,
             9: 10, 10: 11, 11: 12, 12: 13, 13: 14}
    if m >= 14:
        return 15
    return table.get(m, 1)


def skill_ranks(level: int) -> Tuple[int, int, int, int]:
    q = w = e = r = 0
    for ch in SKILL_SEQ[:max(0, min(15, level))]:
        if ch == "Q":
            q += 1
        elif ch == "W":
            w += 1
        elif ch == "E":
            e += 1
        else:
            r += 1
    return q, w, e, r


def growth(base: float, per: float, level: int) -> float:
    return base + per * (level - 1)


def cd(base: float, ah: float) -> float:
    return base * 100.0 / (100.0 + ah)


def resist_mult(stat: float, pen: float, flat: float) -> float:
    n = max(0.0, stat * (1.0 - pen) - flat)
    return 100.0 / (100.0 + n)


def enemy_pen(minute: int) -> Tuple[float, float, float, float]:
    """Armor pen, lethality, magic pen, flat magic pen of the focus."""
    s = 0.0 if minute <= 8 else min(1.0, (minute - 8) / 6.0)
    return 0.30 * s, 12.0 * s, 0.35 * s, 12.0 * s


def focus_scale(minute: int) -> float:
    if minute <= 6:
        return 0.40
    if minute >= 16:
        return 1.0
    return 0.40 + 0.60 * (minute - 6) / 10.0


def enemies_at(minute: int) -> Tuple[dict, dict]:
    lvl = level_at_minute(minute)
    # Late-game bodies, not the level-1 base. The carry is a marksman with
    # two items of health; the other champion is the frontliner in the ult.
    carry = {"hp": 1200 + 130 * lvl, "armor": 32 + 4.0 * lvl, "mr": 30 + 1.6 * lvl}
    tank = {"hp": 1800 + 280 * lvl, "armor": 60 + 10.0 * lvl, "mr": 42 + 5.0 * lvl}
    return carry, tank


def buy(name: str, gold: int, spent: int, owned: List[str]) -> Tuple[int, List[str], bool]:
    it = ITEMS[name]
    if not it.recipe:
        if spent + it.cost > gold:
            return spent, owned, False
        return spent + it.cost, owned + [name], True
    for comp in it.recipe:
        spent, owned, ok = buy(comp, gold, spent, owned)
        if not ok:
            return spent, owned, False
    finish = it.cost - sum(ITEMS[c].cost for c in it.recipe)
    if spent + finish > gold:
        return spent, owned, False
    spent += finish
    for comp in it.recipe:
        owned.remove(comp)
    return spent, owned + [name], True


def purchase(order: Sequence[str], gold: int) -> List[str]:
    spent = 0
    owned: List[str] = []
    for name in order:
        spent, owned, ok = buy(name, gold, spent, owned)
        if not ok:
            return owned
    return owned


def finish_minute(order: Sequence[str], name: str) -> Optional[int]:
    for m in range(0, GAME_MINUTES + 1):
        if name in purchase(order, gold_at_minute(m)):
            return m
    return None


def heartsteel_bonus(hp_without: float, procs: int) -> float:
    bonus = 0.0
    for _ in range(procs):
        dmg = 140.0 + 0.035 * (hp_without + bonus)
        bonus += 0.15 * dmg
    return bonus


class Build:
    def __init__(self, names: Sequence[str], level: int, minute: int, with_r: bool,
                 runes: Sequence[str], hs_finish: Optional[int]):
        self.names = list(names)
        self.level = level
        self.minute = minute
        self.with_r = with_r
        self.runes = tuple(runes)
        self.have = set(names)
        q, w, e, r = skill_ranks(level)
        self.q_rank, self.w_rank, self.e_rank, self.r_rank = q, w, e, r
        self.base_hp = growth(690, 128, level)
        self.base_ad = growth(62, 4, level)
        self.base_armor = growth(46, 4.7, level)
        self.base_mr = growth(38, 2, level)
        self.ad = self.ap = self.ah = self.hp = 0.0
        self.armor = self.mr = self.as_pct = self.crit = 0.0
        self.armor_pen = self.magic_pen = self.flat_mpen = 0.0
        self.lifesteal = self.omnivamp = 0.0
        self.tenacity: List[float] = []
        for n in names:
            it = ITEMS[n]
            self.ad += it.ad
            self.ap += it.ap
            self.ah += it.ah
            self.hp += it.hp
            self.armor += it.armor
            self.mr += it.mr
            self.as_pct += it.as_pct
            self.crit += it.crit
            self.armor_pen += it.armor_pen
            self.magic_pen += it.magic_pen
            self.flat_mpen += it.flat_mpen
            self.lifesteal += it.lifesteal
            self.omnivamp += it.omnivamp
            if it.tenacity:
                self.tenacity.append(it.tenacity)
        if "perseverance" in self.runes:
            self.tenacity.append(0.10)
        if "transcendence" in self.runes and level >= 5:
            self.ah += 10
        if "alacrity" in self.runes:
            self.as_pct += 0.21 if minute >= 10 else 0.03 + 0.18 * min(1.0, minute / 10.0)
        self.sterak_ad = 0.5 * self.base_ad if "sterak" in self.tags() else 0.0
        self.r_hp = R_HP[self.r_rank] if with_r else 0.0
        grasp_hp = 0.0
        if "grasp" in self.runes:
            grasp_hp = int(max(0, minute - 3) * 2.2) * 8
        hs = 0.0
        if "Heartsteel" in self.have and hs_finish is not None:
            rough = self.base_hp + self.hp + self.r_hp + grasp_hp
            n = int(0.7 * max(0, minute - hs_finish))
            hs = heartsteel_bonus(rough, n)
        self.hs_bonus = hs
        self.grasp_bank = grasp_hp
        og_flat = og_pct = 0.0
        if "overgrowth" in self.runes:
            stacks = min(30, int(max(0, minute - 2) * 2.5))
            og_flat = 3 * stacks
            og_pct = 0.03 if stacks >= 30 else 0.0
        pre = self.hp + self.r_hp + grasp_hp + hs + og_flat
        self.og_bonus = og_flat + og_pct * (self.base_hp + pre)
        self.bonus_hp = pre + og_pct * (self.base_hp + pre)
        self.max_hp = self.base_hp + self.bonus_hp
        # Adaptive boots, then the Conqueror choice, then Deathcap.
        self.immortal_ad = self.immortal_ap = 0.0
        if "immortal" in self.tags():
            rift_ap = 0.02 * self.bonus_hp if "rift" in self.tags() else 0.0
            if (self.ad + self.sterak_ad) >= (self.ap + rift_ap):
                self.immortal_ad = 12.0
            else:
                self.immortal_ap = 20.0
        self.bonus_ad = self.ad + self.sterak_ad + self.immortal_ad
        rift_ap = 0.02 * self.bonus_hp if "rift" in self.tags() else 0.0
        self.conq_is_ad = self.bonus_ad >= (self.ap + self.immortal_ap + rift_ap)
        span = (level - 1) / 14.0
        self.conq_ad_per = 3.0 + 2.0 * span
        self.conq_ap_per = 5.0 + 3.0 * span
        self.ap_amp = 1.30 if "deathcap" in self.tags() else 1.0

    def tags(self) -> set:
        out = set()
        for n in self.names:
            out.update(ITEMS[n].tags)
        return out

    def has(self, tag: str) -> bool:
        return tag in self.tags()

    def conq_ad(self, stacks: int) -> float:
        if "conqueror" not in self.runes or not self.conq_is_ad:
            return 0.0
        return stacks * self.conq_ad_per

    def total_ad(self, conq: int) -> float:
        return self.base_ad + self.bonus_ad + self.conq_ad(conq)

    def ap_of(self, bonus_hp: float, conq: int) -> float:
        ap = self.ap + self.immortal_ap
        if self.has("rift"):
            ap += 0.02 * bonus_hp
        if "conqueror" in self.runes and not self.conq_is_ad:
            ap += conq * self.conq_ap_per
        return ap * self.ap_amp

    def attack_speed(self, pstacks: int, lt: int, guinsoo: int, overdrive: float = 0.0, conq: int = 0) -> float:
        ap = self.ap_of(self.bonus_hp, conq)
        passive = pstacks * (0.05 + 0.04 * ap / 100.0)
        bonus = 0.05 + 0.014 * (self.level - 1)
        bonus += self.as_pct + passive + overdrive
        bonus += 0.08 * min(4, guinsoo)
        if "lethal" in self.runes:
            bonus += 0.06 * lt
        return min(AS_CAP, AS_BASE + bonus * AS_RATIO)

    def w_damage(self, frenzy: bool, ad: float, bonus_hp: float) -> float:
        raw = W_BASE[self.w_rank] + 1.10 * ad + 0.065 * bonus_hp
        return raw * (1.6 if frenzy else 1.0)

    def w_heal(self, missing: float) -> float:
        return W_HEAL[self.w_rank] + W_HEAL_PCT[self.w_rank] * missing

    def e_shield(self, max_hp: float, ap: float) -> float:
        return 0.14 * max_hp + 0.75 * ap

    def q_bonus(self, bonus_ad: float) -> float:
        return Q_BASE[self.q_rank] + 1.00 * bonus_ad

    def r_damage(self, bonus_ad: float, ap: float) -> float:
        return R_BASE[self.r_rank] + 2.10 * bonus_ad + 1.00 * ap


class Enemy:
    def __init__(self, hp: float, armor: float, mr: float):
        self.max_hp = hp
        self.hp = hp
        self.armor = armor
        self.mr = mr
        self.cleaver = 0
        self.hits: List[float] = []
        self.sundered = -999.0
        self.liandry = -999.0
        self.eclipse_cd = -999.0

    @property
    def alive(self) -> bool:
        return self.hp > 0


class Fight:
    def __init__(self, build: Build, scenario: str, grievous: bool, trace: bool):
        self.b = build
        self.scenario = scenario
        self.grievous = grievous
        self.trace = trace
        self.log: List[str] = []
        carry, tank = enemies_at(build.minute)
        self.carry = Enemy(carry["hp"], carry["armor"], carry["mr"])
        self.tank = Enemy(tank["hp"], tank["armor"], tank["mr"])
        self.carry_death: Optional[float] = None
        self.tank_death: Optional[float] = None
        self.primary = self.tank if scenario == "brawl" else self.carry
        self.max_hp = build.max_hp
        self.hp = build.max_hp
        self.bonus_armor = build.armor
        self.bonus_mr = build.mr
        self.fon = 0
        self.twin = 0
        self.shields: List[dict] = []
        self.bleed = 0.0
        self.sources: Dict[str, float] = {}
        self.heals: Dict[str, float] = {}
        self.absorbed = 0.0
        self.bites = self.w_casts = self.autos = self.spellblades = self.e_hits = 0
        self.conq = 0
        self.pstacks = 0
        self.lt = 0
        self.guinsoo = 0
        self.g_count = 0
        self.rift = 0
        self.madness = 0
        self.term_dark = 0
        self.term_light = 0
        self.term_flip = False
        self.hull_n = 0
        self.energy = 0.0
        self.frenzy_until = -1.0
        self.sb_armed = False
        self.sb_ready = 0.0
        self.q_buff = False
        self.stun_until = -1.0
        self.stasis_until = -1.0
        self.busy_until = 0.0
        self.lifeline_used = False
        self.mantle_left = 0.0
        self.mantle_drop = 0.0
        self.kaenic_up = build.has("kaenic")
        self.advance_up = build.has("advance")
        self.crush_up = build.has("crushers")
        self.grasp_armed = "grasp" in build.runes
        self.next_grasp = 3.0
        self.died = False
        self.death_t: Optional[float] = None
        pen_a, flat_a, pen_m, flat_m = enemy_pen(build.minute)
        self.pen_a, self.flat_a, self.pen_m, self.flat_m = pen_a, flat_a, pen_m, flat_m
        self.scale = focus_scale(build.minute)
        if build.with_r and build.has("radiant") and build.r_rank:
            grant = 0.10 * self.max_hp
            self.add_max(grant)
            self.radiant_until = 6.0
            self.radiant_drop = grant
        else:
            self.radiant_until = -1.0
            self.radiant_drop = 0.0
        if build.with_r and build.has("statikk"):
            self.energy = 700 / 25.0

    def note(self, t: float, msg: str) -> None:
        if self.trace:
            self.log.append(f"t={t:4.1f}  {msg}")

    def add_max(self, delta: float) -> None:
        self.max_hp += delta
        if delta >= 0:
            self.hp += delta
        else:
            self.hp = min(self.max_hp, max(1.0, self.hp + delta))

    def bonus_hp(self) -> float:
        return max(0.0, self.max_hp - self.b.base_hp)

    def conq_stacks_for_damage(self) -> int:
        return self.conq

    def ad_now(self) -> float:
        return self.b.total_ad(self.conq)

    def bonus_ad_now(self) -> float:
        return self.b.bonus_ad + self.b.conq_ad(self.conq)

    def ap_now(self) -> float:
        return self.b.ap_of(self.bonus_hp(), self.conq)

    def amp(self, ability: bool, target: Enemy) -> float:
        m = 1.0
        m *= 1.0 + 0.02 * self.rift
        m *= 1.0 + 0.02 * self.madness
        if "laststand" in self.b.runes and self.max_hp:
            frac = self.hp / self.max_hp
            if frac < 0.60:
                t = min(1.0, (0.60 - frac) / 0.30)
                m *= 1.0 + (0.05 + 0.06 * t)
        if self.b.has("immortal") and self.hp > 0.5 * self.max_hp:
            m *= 1.05
        if ability and self.b.has("orb") and target.max_hp and target.hp / target.max_hp < 0.40:
            m *= 1.20
        return m

    def heal_amp(self) -> float:
        if self.b.has("immortal") and self.hp < 0.5 * self.max_hp:
            return 1.12
        return 1.0

    def heal(self, amount: float, source: str) -> float:
        if amount <= 0 or self.hp <= 0:
            return 0.0
        amount *= self.heal_amp()
        if self.grievous:
            amount *= 0.40
        got = min(amount, max(0.0, self.max_hp - self.hp))
        self.hp += got
        self.heals[source] = self.heals.get(source, 0.0) + got
        return got

    def shield(self, amount: float, until: float, kind: str) -> None:
        if amount <= 0:
            return
        amount *= self.heal_amp()
        self.shields.append({"hp": amount, "until": until, "kind": kind})

    def absorb(self, amount: float, kind: str, t: float) -> float:
        left = amount
        for sh in self.shields:
            if left <= 0:
                break
            if sh["hp"] <= 0 or t > sh["until"]:
                continue
            if sh["kind"] not in (kind, "all"):
                continue
            use = min(sh["hp"], left)
            sh["hp"] -= use
            left -= use
            self.absorbed += use
        return left

    def resists(self, t: float) -> Tuple[float, float]:
        arm_b = self.bonus_armor + (8.0 * self.term_light)
        mr_b = self.bonus_mr + (8.0 * self.term_light)
        if self.fon >= 4:
            mr_b += 70.0
        if self.twin >= 5:
            arm_b *= 1.30
            mr_b *= 1.30
        arm = self.b.base_armor + arm_b
        mr = self.b.base_mr + mr_b
        if "perseverance" in self.b.runes and t < getattr(self, "persev_until", -1):
            arm += 15
            mr += 15
        return arm, mr

    def take(self, raw: float, kind: str, t: float) -> float:
        if raw <= 0 or self.hp <= 0 or t < self.stasis_until:
            return 0.0
        left = self.absorb(raw, kind, t)
        if left <= 0:
            return 0.0
        if self.b.has("dd") and kind in ("phys", "magic"):
            self.bleed += left * 0.30
            left *= 0.70
        self.hp -= left
        if self.hp <= 0 and self.b.has("zhonya") and t >= self.stasis_until:
            self.hp = 1.0
            self.stasis_until = t + 2.5
            self.note(t, "Zhonya stasis")
            return left
        self.check_lifeline(t, kind)
        if self.hp <= 0 and not self.died:
            self.hp = 0.0
            self.died = True
            self.death_t = t
        return left

    def check_lifeline(self, t: float, kind: str) -> None:
        if self.lifeline_used or self.hp <= 0:
            return
        if self.b.has("sterak") and self.hp < 0.35 * self.max_hp:
            self.lifeline_used = True
            shield = 0.75 * self.bonus_hp()
            self.shield(shield, t + 5.0, "all")
            self.note(t, f"Sterak shield {shield:.0f}")
        elif self.b.has("mantle") and self.hp < 0.30 * self.max_hp:
            self.lifeline_used = True
            self.add_max(300.0)
            self.mantle_drop = 300.0
            self.mantle_left = 5.0
            heal = 400.0 + 1.20 * self.bonus_armor + 1.20 * self.bonus_mr + 0.15 * (self.bonus_hp() - 300.0)
            self.mantle_regen = heal / 5.0
            self.note(t, f"Mantle +300 HP, heal {heal:.0f}")
        if self.advance_up and kind == "phys":
            self.advance_up = False
            val = 140.0 + 0.08 * self.max_hp
            self.shield(val, t + 5.0, "phys")
            self.note(t, f"Armored Advance shield {val:.0f}")
        if self.crush_up and kind == "magic":
            self.crush_up = False
            val = 120.0 + 0.05 * self.max_hp
            self.shield(val, t + 5.0, "magic")
            self.note(t, f"Chainlaced shield {val:.0f}")

    def deal(self, raw: float, target: Enemy, kind: str, source: str, ability: bool, t: float,
             pen_bonus: float = 0.0) -> float:
        if raw <= 0 or not target.alive or self.hp <= 0:
            return 0.0
        raw *= self.amp(ability, target)
        if kind == "magic" and self.b.has("abyssal"):
            raw *= 1.12
        if kind == "phys":
            shred = 0.06 * target.cleaver
            pen = min(0.80, self.b.armor_pen + pen_bonus + 0.10 * self.term_dark)
            mult = resist_mult(target.armor * (1.0 - shred), pen, 0.0)
        elif kind == "magic":
            pen = min(0.80, self.b.magic_pen + pen_bonus + 0.10 * self.term_dark)
            mult = resist_mult(target.mr, pen, self.b.flat_mpen)
        else:
            mult = 1.0
        post = min(target.hp, raw * mult)
        target.hp -= post
        if target.hp <= 0:
            if target is self.carry and self.carry_death is None:
                self.carry_death = t
            elif target is self.tank and self.tank_death is None:
                self.tank_death = t
        self.sources[source] = self.sources.get(source, 0.0) + post
        if self.omni() > 0:
            self.heal(post * self.omni(), "omnivamp")
        if self.b.has("liandry") and ability:
            target.liandry = t + 3.0
        return post

    def omni(self) -> float:
        v = self.b.omnivamp
        if "conqueror" in self.b.runes and self.conq >= 6:
            v += 0.09
        if self.b.has("rift") and self.rift >= 4:
            v += 0.10
        return v

    def grant_conq(self) -> None:
        if "conqueror" in self.b.runes:
            self.conq = min(6, self.conq + 1)

    def grant_passive(self, on_hit: bool, target: Enemy, t: float) -> None:
        if on_hit and self.pstacks >= 4:
            self.lightning(target, t)
        if self.pstacks < 5:
            self.pstacks += 1
        if "lethal" in self.b.runes and on_hit:
            if self.lt >= 6:
                self.bolt(target, t)
            else:
                self.lt += 1
                if self.lt >= 6:
                    self.bolt(target, t)

    def lightning(self, target: Enemy, t: float) -> None:
        dmg = 12.0 + 4.0 * (self.b.level - 1) + 0.40 * self.ap_now()
        self.deal(dmg, target, "magic", "lightning", False, t)
        other = self.tank if target is self.carry else self.carry
        if other.alive:
            self.deal(dmg, other, "magic", "lightning", False, t)

    def bolt(self, target: Enemy, t: float) -> None:
        base = 9.0 + (30.0 - 9.0) * (self.b.level - 1) / 14.0
        frac = max(0.0, (self.b.attack_speed(self.pstacks, self.lt, self.guinsoo, conq=self.conq) - AS_BASE) / AS_RATIO)
        dmg = base * (1.0 + 0.50 * frac)
        kind = "phys" if self.b.conq_is_ad else "magic"
        self.deal(dmg, target, kind, "tempo", False, t)

    def on_hit(self, target: Enemy, t: float, extra: bool) -> None:
        if self.b.has("nashor"):
            self.deal(15.0 + 0.20 * self.ap_now(), target, "magic", "nashor", False, t)
        if self.b.has("wits"):
            self.deal(40.0, target, "magic", "wits", False, t)
        if self.b.has("guinsoo"):
            self.deal(30.0, target, "magic", "guinsoo", False, t)
        if self.b.has("bork"):
            post = self.deal(max(15.0, 0.085 * target.hp), target, "phys", "bork", False, t)
            self.lifesteal(post)
        if self.b.has("terminus"):
            self.deal(30.0, target, "magic", "terminus", False, t)
            if self.term_flip:
                self.term_light = min(3, self.term_light + 1)
            else:
                self.term_dark = min(3, self.term_dark + 1)
            self.term_flip = not self.term_flip
        if "brutal" in self.b.runes:
            raw = 5.0 + 0.06 * self.bonus_ad_now() + 0.03 * self.ap_now()
            kind = "phys" if self.b.conq_is_ad else "magic"
            self.deal(raw, target, kind, "brutal", False, t)
        if self.grasp_armed and not extra:
            self.grasp_armed = False
            self.next_grasp = t + 3.0
            post = self.deal(0.03 * self.max_hp, target, "magic", "grasp", False, t)
            self.heal(0.013 * self.max_hp, "grasp")
            self.add_max(8.0)
        self.grant_passive(True, target, t)
        if self.b.has("statikk") and not extra:
            self.statikk(target, t)

    def statikk(self, target: Enemy, t: float) -> None:
        self.energy += 6 + 5
        if self.energy < 100:
            return
        self.energy -= 100
        self.deal(60.0, target, "magic", "statikk", False, t)
        other = self.tank if target is self.carry else self.carry
        if other.alive:
            self.deal(60.0, other, "magic", "statikk", False, t)
            self.on_hit(other, t, extra=True)

    def lifesteal(self, post_phys: float) -> None:
        if self.b.lifesteal > 0 and post_phys > 0:
            self.heal(post_phys * self.b.lifesteal, "lifesteal")

    def navori(self, t: float, cds: dict) -> None:
        if not self.b.has("navori"):
            return
        for k in ("w", "e", "q"):
            if cds[k] > t:
                cds[k] = t + (cds[k] - t) * 0.85

    def spellblade(self, target: Enemy, t: float) -> None:
        if not self.sb_armed or t < self.sb_ready:
            return
        self.sb_armed = False
        self.sb_ready = t + 1.5
        self.spellblades += 1
        b = self.b
        if b.has("trinity"):
            post = self.deal(2.00 * b.base_ad, target, "phys", "spellblade", True, t)
        elif b.has("divine"):
            post = self.deal(0.10 * target.max_hp, target, "phys", "spellblade", True, t)
            self.heal(0.06 * target.max_hp, "divine")
        elif b.has("dusk"):
            post = self.deal(0.75 * b.base_ad + 0.10 * self.ap_now(), target, "magic", "spellblade", True, t)
            self.heal(0.10 * self.ap_now() + 0.03 * self.bonus_hp(), "dusk")
            self.on_hit(target, t, extra=True)
        elif b.has("iceborn"):
            raw = b.base_ad + 0.25 * self.bonus_armor
            self.deal(raw, target, "phys", "spellblade", True, t)
            other = self.tank if target is self.carry else self.carry
            if other.alive:
                self.deal(raw, other, "phys", "spellblade", True, t)
        if b.has("liandry"):
            target.liandry = t + 3.0

    def eclipse(self, target: Enemy, t: float) -> None:
        if not self.b.has("eclipse") or t < target.eclipse_cd:
            return
        target.hits = [h for h in target.hits if t - h <= 1.8]
        target.hits.append(t)
        if len(target.hits) >= 2:
            target.hits.clear()
            target.eclipse_cd = t + 6.0
            self.deal(0.07 * target.max_hp, target, "phys", "eclipse", True, t)
            self.shield(150.0 + 0.40 * self.bonus_ad_now(), t + 2.0, "all")

    def attack(self, target: Enemy, t: float, from_q: bool, cds: dict) -> None:
        if not target.alive:
            return
        self.autos += 1
        ad = self.ad_now()
        crit = 1.0 + min(1.0, self.b.crit)
        sundered = self.b.has("sundered") and t >= target.sundered
        if sundered:
            crit = 1.60
            target.sundered = t + 6.0
            self.heal(1.25 * self.b.base_ad + 0.06 * (self.max_hp - self.hp), "sundered")
        post = self.deal(ad * crit, target, "phys", "auto", False, t)
        bonus = 0.0
        if from_q and self.b.q_rank:
            bonus = self.deal(self.b.q_bonus(self.bonus_ad_now()), target, "phys", "Q", True, t)
            self.stun_until = t + 1.0
            self.q_buff = False
            self.note(t, f"Q auto {post + bonus:.0f}")
        self.lifesteal(post + bonus)
        if self.b.has("titanic") and t >= getattr(self, "titanic_at", 0):
            self.titanic_at = t + 1.75
            cleave = self.deal(25.0 + 0.03 * self.bonus_hp(), target, "phys", "titanic", False, t)
            self.lifesteal(cleave)
            other = self.tank if target is self.carry else self.carry
            if other.alive:
                self.deal(80.0 + 0.10 * self.bonus_hp(), other, "phys", "titanic", False, t)
        if self.b.has("hull"):
            self.hull_n += 1
            if self.hull_n % 4 == 0:
                hpst = self.deal(1.60 * self.b.base_ad, target, "phys", "hull", False, t)
                self.lifesteal(hpst)
        self.spellblade(target, t)
        self.on_hit(target, t, extra=False)
        self.eclipse(target, t)
        self.grant_conq()
        self.navori(t, cds)
        if self.b.has("cleaver"):
            target.cleaver = min(5, target.cleaver + 1)
        if self.b.has("guinsoo"):
            self.g_count += 1
            self.guinsoo = min(4, self.guinsoo + 1)
            if self.guinsoo >= 4 and self.g_count % 3 == 0:
                self.on_hit(target, t, extra=True)
        if not target.alive:
            self.on_takedown()

    def on_takedown(self) -> None:
        if "triumph" in self.b.runes:
            self.heal(0.10 * (self.max_hp - self.hp), "triumph")
        if self.b.has("immortal"):
            self.b.omnivamp = min(0.10, self.b.omnivamp + 0.005)

    def cast_w(self, target: Enemy, t: float, cds: dict) -> None:
        self.w_casts += 1
        frenzy = t < self.frenzy_until
        if frenzy:
            self.bites += 1
        raw = self.b.w_damage(frenzy, self.ad_now(), self.bonus_hp())
        post = self.deal(raw, target, "phys", "W", True, t)
        self.lifesteal(post)
        if frenzy:
            missing = max(0.0, self.max_hp - self.hp)
            self.heal(self.b.w_heal(missing), "W")
            self.note(t, f"W2 {post:.0f}")
        else:
            self.note(t, f"W1 {post:.0f}")
        self.frenzy_until = t + 8.0
        self.spellblade(target, t)
        self.on_hit(target, t, extra=False)
        self.eclipse(target, t)
        self.grant_conq()
        self.navori(t, cds)
        if self.b.has("cleaver"):
            target.cleaver = min(5, target.cleaver + 1)
        self.sb_armed = True
        if not target.alive:
            self.on_takedown()

    def land_e(self, t: float) -> None:
        ap = self.ap_now()
        shield = self.b.e_shield(self.max_hp, ap)
        self.shield(shield, t + 2.5, "all")
        self.e_hits += 1
        self.note(t, f"E shield {shield:.0f}")
        for enemy in (self.carry, self.tank):
            if not enemy.alive:
                continue
            raw = E_BASE[self.b.e_rank] + 0.50 * ap + E_PCT[self.b.e_rank] * enemy.max_hp
            self.deal(raw, enemy, "magic", "E", True, t)
            self.eclipse(enemy, t)
        self.grant_conq()
        if self.pstacks < 5:
            self.pstacks += 1

    def land_r(self, t: float) -> None:
        raw = self.b.r_damage(self.bonus_ad_now(), self.ap_now())
        self.note(t, f"R {raw:.0f} pre")
        for enemy in (self.carry, self.tank):
            if enemy.alive:
                self.deal(raw, enemy, "phys", "R", True, t)
                if self.b.has("cleaver"):
                    enemy.cleaver = min(5, enemy.cleaver + 1)
                self.eclipse(enemy, t)
        self.grant_conq()
        if self.pstacks < 5:
            self.pstacks += 1
        self.sb_armed = True

    def living_primary(self) -> Optional[Enemy]:
        if self.scenario == "brawl":
            order = (self.tank, self.carry)
        else:
            order = (self.carry, self.tank)
        for e in order:
            if e.alive:
                return e
        return None

    def run(self) -> dict:
        b = self.b
        with_r = b.with_r and b.r_rank > 0
        end = 12.0 if with_r else SURVIVE
        focus_from = 1.0 if with_r else 0.0
        ah = b.ah
        w_cd = cd(5.0, ah)
        e_cd = cd(13.0, ah)
        q_cd = cd(Q_CD[b.q_rank], ah) if b.q_rank else 999.0
        cds = {"w": focus_from, "e": 0.0, "q": 0.0}
        if with_r:
            # E was cast 1s before the leap so it lands as he does. Q was cast with R.
            cds["e"] = e_cd - 1.0
            cds["q"] = q_cd
            self.q_buff = b.q_rank > 0
            self.sb_armed = True
            r_land = 1.0
            e_land = 1.0
        else:
            r_land = -1.0
            e_land = 2.0 if b.e_rank else -1.0
            cds["e"] = e_cd if b.e_rank else 999.0
            self.q_buff = False
        ten = 1.0
        for src in b.tenacity:
            ten *= (1.0 - src)
        cc_until = focus_from + BASE_CC * ten
        self.persev_until = cc_until + 0.5 if "perseverance" in b.runes else -1.0
        atk_ready = focus_from
        hs_at = focus_from + 2.5 if b.has("heartsteel") else 999.0
        next_unending = focus_from + 4.0
        titanic_at = focus_from
        self.titanic_at = titanic_at
        if b.has("kaenic"):
            self.shield(150.0 + 0.14 * self.max_hp, 999.0, "magic")
        t = 0.0
        last_second = -1
        while t < end - 1e-9 and not self.died:
            if with_r and r_land >= 0 and t + 1e-9 >= r_land:
                self.land_r(t)
                r_land = -1.0
            if e_land >= 0 and t + 1e-9 >= e_land:
                self.land_e(t)
                e_land = -1.0
            if int(t) != last_second and t >= focus_from:
                last_second = int(t)
                if self.rift < 4:
                    self.rift += 1
                if self.madness < 3 and b.has("liandry"):
                    self.madness += 1
                if b.has("twinguard"):
                    self.twin = min(5, self.twin + 1)
                if b.has("fon"):
                    self.fon = min(4, self.fon + 1)
            if t >= focus_from and t >= self.stasis_until:
                arm, mr = self.resists(t)
                phys = PHYS_DPS * self.scale
                auto_share = 0.65
                if b.has("frozen"):
                    phys *= auto_share * 0.75 + (1.0 - auto_share)
                if b.has("steelcaps"):
                    phys *= auto_share * 0.90 + (1.0 - auto_share)
                if b.has("randuin"):
                    phys *= 1.0 - 0.55 * 0.30
                if t < self.stun_until:
                    phys *= 0.30
                phys *= resist_mult(arm, self.pen_a, self.flat_a)
                magic = MAGIC_DPS * self.scale * resist_mult(mr, self.pen_m, self.flat_m)
                self.take(phys * DT, "phys", t)
                if self.died:
                    break
                self.take(magic * DT, "magic", t)
                if self.died:
                    break
                if self.bleed > 0 and t >= self.stasis_until:
                    tick = self.bleed / 3.0 * DT
                    self.bleed = max(0.0, self.bleed - tick)
                    self.take(tick, "true", t)
                    if self.died:
                        break
                if b.has("thorn"):
                    rate = 1.7 * (0.75 if b.has("frozen") else 1.0)
                    th = 20.0 + 0.06 * self.bonus_armor + 0.01 * self.bonus_hp()
                    if self.carry.alive:
                        self.deal(th * rate * DT, self.carry, "magic", "thorns", False, t)
            if "second" in b.runes and t >= focus_from and t >= self.stasis_until:
                missing = max(0.0, self.max_hp - self.hp)
                self.heal((6.0 + 0.03 * missing) / 5.0 * DT, "second wind")
            if self.radiant_until >= t:
                self.heal(0.025 * self.max_hp * DT, "radiant")
            if self.mantle_left > 0:
                self.heal(self.mantle_regen * DT, "mantle")
                self.mantle_left -= DT
                if self.mantle_left <= 0 and self.mantle_drop:
                    self.add_max(-self.mantle_drop)
                    self.mantle_drop = 0.0
            if self.radiant_drop and t + 1e-6 >= self.radiant_until > 0:
                self.add_max(-self.radiant_drop)
                self.radiant_drop = 0.0
            for enemy in (self.carry, self.tank):
                if enemy.alive and t < enemy.liandry:
                    self.deal(0.02 * enemy.max_hp * DT, enemy, "magic", "liandry", False, t)
            if b.has("sunfire") and t >= focus_from:
                burn = (20.0 + 0.015 * self.bonus_hp()) * DT
                for enemy in (self.carry, self.tank):
                    if enemy.alive:
                        self.deal(burn, enemy, "magic", "sunfire", False, t)
            if b.has("unending") and t + 1e-9 >= next_unending:
                for enemy in (self.carry, self.tank):
                    if enemy.alive:
                        post = self.deal(0.03 * self.max_hp, enemy, "magic", "unending", False, t)
                        self.heal(2.50 * post, "unending")
                next_unending += 4.0
            if t + 1e-9 >= hs_at and self.primary_alive():
                tgt = self.living_primary()
                if tgt is not None:
                    raw = 140.0 + 0.035 * self.max_hp
                    post = self.deal(raw, tgt, "phys", "heartsteel", False, t)
                    gain = 0.15 * raw
                    self.add_max(gain)
                    self.note(t, f"Heartsteel {post:.0f}, +{gain:.0f} HP")
                hs_at = 999.0
            if "grasp" in b.runes and t >= self.next_grasp and not self.grasp_armed:
                self.grasp_armed = True
            acted = False
            if (not self.died and t >= focus_from and t >= cc_until
                    and t >= self.busy_until and t >= self.stasis_until):
                tgt = self.living_primary()
                if tgt is not None:
                    if t >= cds["w"] and b.w_rank:
                        cds["w"] = t + w_cd
                        self.cast_w(tgt, t, cds)
                        self.busy_until = t + 0.25
                        atk_ready = max(atk_ready, t + 0.25)
                        self.sb_armed = True
                        acted = True
                    elif self.q_buff and t >= atk_ready:
                        self.attack(tgt, t, True, cds)
                        atk_ready = t + 1.0 / max(0.2, b.attack_speed(self.pstacks, self.lt, self.guinsoo, conq=self.conq))
                        acted = True
                    elif t >= cds["e"] and b.e_rank:
                        e_land = t + 2.0
                        cds["e"] = t + e_cd
                        self.sb_armed = True
                        self.note(t, "cast E")
                        acted = True
                    elif t >= cds["q"] and b.q_rank and not self.q_buff:
                        self.q_buff = True
                        cds["q"] = t + q_cd
                        self.sb_armed = True
                        acted = True
                    elif t >= atk_ready:
                        self.attack(tgt, t, False, cds)
                        atk_ready = t + 1.0 / max(0.2, b.attack_speed(self.pstacks, self.lt, self.guinsoo, conq=self.conq))
                        acted = True
            t += DT
        if self.radiant_drop:
            # fight ended while the bonus was up; leave it in the end HP snapshot
            pass
        origin = 1.0 if with_r else 0.0
        survival = SURVIVE if not self.died else max(0.0, (self.death_t or end) - origin)
        return {
            "total": sum(self.sources.values()),
            "sources": self.sources,
            "heals": self.heals,
            "healed": sum(self.heals.values()),
            "absorbed": self.absorbed,
            "survival": min(SURVIVE, survival),
            "died": self.died,
            "end_hp": self.hp,
            "max_hp": self.max_hp,
            "bites": self.bites,
            "w_casts": self.w_casts,
            "autos": self.autos,
            "spellblades": self.spellblades,
            "e_hits": self.e_hits,
            "carry": self.carry.max_hp - self.carry.hp,
            "tank": self.tank.max_hp - self.tank.hp,
            "carry_death": self.carry_death,
            "tank_death": self.tank_death,
            "log": self.log,
            "sheet_hp": b.max_hp,
            "conq": self.conq,
        }

    def primary_alive(self) -> bool:
        return self.carry.alive or self.tank.alive


def run_fight(items: Sequence[str], minute: int, with_r: bool = True, grievous: bool = False,
              hs_finish: Optional[int] = None, scenario: str = "dive",
              runes: Sequence[str] = (), trace: bool = False) -> dict:
    level = level_at_minute(minute)
    build = Build(items, level, minute, with_r, runes, hs_finish)
    return Fight(build, scenario, grievous, trace).run()


DEFAULT_RUNES = ("conqueror", "brutal", "laststand", "alacrity", "overgrowth")
RUNE_PAGES = (
    ("Conqueror, Last Stand, Alacrity, Overgrowth, Brutal",
     ("conqueror", "brutal", "laststand", "alacrity", "overgrowth")),
    ("Grasp, Second Wind, Perseverance, Brutal",
     ("grasp", "second", "perseverance", "brutal")),
    ("Lethal Tempo, Last Stand, Alacrity, Overgrowth, Brutal",
     ("lethal", "brutal", "laststand", "alacrity", "overgrowth")),
    ("Conqueror, Triumph, Last Stand, Alacrity, Overgrowth",
     ("conqueror", "triumph", "laststand", "alacrity", "overgrowth")),
)
HS_SNAPSHOT = 10


def rune_name(runes: Sequence[str]) -> str:
    for label, page in RUNE_PAGES:
        if tuple(page) == tuple(runes):
            return label
    return ", ".join(runes)


CACHE: Dict[Tuple, dict] = {}


def snapshot(items: Sequence[str], minute: int = GAME_MINUTES, with_r: bool = True,
             grievous: bool = False, scenario: str = "dive",
             runes: Sequence[str] = DEFAULT_RUNES, hs_finish: Optional[int] = None,
             trace: bool = False) -> dict:
    if hs_finish is None and "Heartsteel" in items:
        hs_finish = HS_SNAPSHOT
    key = (tuple(sorted(items)), minute, with_r, grievous, scenario, tuple(runes), hs_finish, trace)
    if not trace and key in CACHE:
        return CACHE[key]
    result = run_fight(items, minute, with_r, grievous, hs_finish, scenario, runes, trace)
    if not trace:
        CACHE[key] = result
    return result


def pct(fight: dict) -> float:
    if fight["max_hp"] <= 0:
        return 0.0
    return 100.0 * fight["end_hp"] / fight["max_hp"]


def quick_score(r: dict) -> Tuple[int, float]:
    if r["died"]:
        return (0, r["total"] * (r["survival"] / SURVIVE))
    left = r["end_hp"] / r["max_hp"] if r["max_hp"] else 0.0
    return (1, r["total"] * (0.82 + 0.18 * left))


def final_rank(r: dict, nor: dict, brawl: dict) -> Tuple[int, float]:
    lived_r = not r["died"]
    lived_n = not nor["died"]
    if lived_r and (lived_n or nor["survival"] >= 7.0):
        tier = 2
    elif lived_r:
        tier = 1
    else:
        tier = 0
    dmg = r["total"] + 0.25 * brawl["total"] + 0.20 * nor["total"]
    if lived_r and r["max_hp"]:
        dmg += 0.12 * r["total"] * (r["end_hp"] / r["max_hp"])
    return tier, dmg


def evaluate_full(items: Sequence[str], runes: Sequence[str] = DEFAULT_RUNES) -> dict:
    r = snapshot(items, scenario="dive", runes=runes)
    brawl = snapshot(items, scenario="brawl", runes=runes)
    nor = snapshot(items, with_r=False, scenario="dive", runes=runes)
    tier, score = final_rank(r, nor, brawl)
    return {
        "items": tuple(boots_first(items)),
        "r": r, "brawl": brawl, "nor": nor,
        "tier": tier, "score": score, "runes": tuple(runes),
    }


def boots_first(items: Sequence[str]) -> List[str]:
    boots = [i for i in items if i in BOOTS]
    legs = [i for i in items if i not in BOOTS]
    return boots + legs


def conflicts(have: Sequence[str], cand: str) -> bool:
    if cand in have:
        return True
    groups = (SPELLBLADES, BOOTS, LIFELINES)
    for group in groups:
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
    for i, _leg in enumerate(legs):
        rest = legs[:i] + legs[i + 1:]
        for cand in LEGENDARIES:
            if conflicts(rest, cand):
                continue
            out.append(tuple(boots_first(boots + rest[:i] + [cand] + rest[i:])))
    return out


ARCHETYPES: List[Tuple[str, Tuple[str, ...]]] = [
    ("Dusk Navori", ("Armored Advance", "Dusk and Dawn", "Navori Quickblades", "Riftmaker", "Unending Despair", "Amaranth's Twinguard")),
    ("Divine Frontline", ("Armored Advance", "Divine Sunderer", "Unending Despair", "Randuin's Omen", "Frozen Heart", "Amaranth's Twinguard")),
    ("Heartsteel", ("Plated Steelcaps", "Heartsteel", "Titanic Hydra", "Sterak's Gage", "Unending Despair", "Amaranth's Twinguard")),
    ("Trinity Bruiser", ("Plated Steelcaps", "Trinity Force", "Black Cleaver", "Sterak's Gage", "Death's Dance", "Amaranth's Twinguard")),
    ("Sundered", ("Plated Steelcaps", "Sundered Sky", "Spear of Shojin", "Sterak's Gage", "Death's Dance", "Amaranth's Twinguard")),
    ("Full Tank", ("Armored Advance", "Heartsteel", "Unending Despair", "Randuin's Omen", "Kaenic Rookern", "Amaranth's Twinguard")),
    ("Eclipse Bite", ("Plated Steelcaps", "Eclipse", "Black Cleaver", "Spear of Shojin", "Sterak's Gage", "Death's Dance")),
    ("Hullbreaker", ("Plated Steelcaps", "Hullbreaker", "Divine Sunderer", "Titanic Hydra", "Sterak's Gage", "Amaranth's Twinguard")),
    ("Mantle Front", ("Armored Advance", "Mantle of the Twelfth Hour", "Heartsteel", "Unending Despair", "Amaranth's Twinguard", "Sunfire Aegis")),
    ("Radiant", ("Armored Advance", "Radiant Virtue", "Heartsteel", "Unending Despair", "Force of Nature", "Amaranth's Twinguard")),
    ("Statikk On-hit", ("Mercury's Treads", "Statikk Shiv", "Dusk and Dawn", "Nashor's Tooth", "Riftmaker", "Amaranth's Twinguard")),
    ("AP Glass", ("Mercury's Treads", "Dusk and Dawn", "Nashor's Tooth", "Rabadon's Deathcap", "Infinity Orb", "Void Staff")),
    ("Liandry Rift", ("Chainlaced Crushers", "Riftmaker", "Liandry's Torment", "Dusk and Dawn", "Nashor's Tooth", "Kaenic Rookern")),
    ("Guinsoo On-hit", ("Plated Steelcaps", "Guinsoo's Rageblade", "Blade of the Ruined King", "At Wit's End", "Titanic Hydra", "Amaranth's Twinguard")),
    ("Navori AD", ("Plated Steelcaps", "Navori Quickblades", "Trinity Force", "Black Cleaver", "Sterak's Gage", "Death's Dance")),
    ("Iceborn", ("Plated Steelcaps", "Iceborn Gauntlet", "Heartsteel", "Frozen Heart", "Unending Despair", "Amaranth's Twinguard")),
    ("Thornmail", ("Armored Advance", "Thornmail", "Randuin's Omen", "Unending Despair", "Heartsteel", "Amaranth's Twinguard")),
    ("Immortal Hybrid", ("Immortal Treads", "Dusk and Dawn", "Navori Quickblades", "Riftmaker", "Sterak's Gage", "Amaranth's Twinguard")),
    ("Zhonya Glass", ("Mercury's Treads", "Zhonya's Hourglass", "Riftmaker", "Nashor's Tooth", "Rabadon's Deathcap", "Void Staff")),
    ("Shojin Titan", ("Plated Steelcaps", "Spear of Shojin", "Titanic Hydra", "Sundered Sky", "Sterak's Gage", "Kaenic Rookern")),
    ("Warmog Tank", ("Armored Advance", "Warmog's Armor", "Heartsteel", "Force of Nature", "Randuin's Omen", "Amaranth's Twinguard")),
]


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
        r = snapshot(items)
        ranked.append({"items": tuple(boots_first(items)), "r": r, "quick": quick_score(r)})

    for _, build in ARCHETYPES:
        consider(build)
    print(f"  cores {len(ranked)}", flush=True)
    for round_i in range(2):
        if round_i == 0:
            seeds = [build for _, build in ARCHETYPES]
        else:
            seeds = [e["items"] for e in sorted(ranked, key=lambda e: e["quick"], reverse=True)[:8]]
        before = len(seen)
        for seed in seeds:
            for nb in neighbors(seed):
                consider(nb)
        print(f"  swap round {round_i + 1}: +{len(seen) - before} (pool {len(seen)})", flush=True)
    top = sorted(ranked, key=lambda e: e["quick"], reverse=True)[:28]
    print(f"  full-scoring {len(top)} finalists", flush=True)
    full = [evaluate_full(e["items"]) for e in top]
    have = {frozenset(e["items"]) for e in full}
    for _, build in ARCHETYPES:
        if frozenset(build) not in have:
            full.append(evaluate_full(build))
    full.sort(key=lambda e: (e["tier"], e["score"]), reverse=True)
    return full


def best_order(items: Sequence[str], runes: Sequence[str]) -> Tuple[str, ...]:
    boots = [i for i in items if i in BOOTS]
    legs = [i for i in items if i not in BOOTS]
    best: Optional[Tuple[float, Tuple[str, ...]]] = None
    for perm in itertools.permutations(legs):
        order = tuple(boots + list(perm))
        score = 0.0
        hs_m = None
        for m in (8, 10, 12, 14, 16, 18):
            owned = purchase(order, gold_at_minute(m))
            if not owned:
                continue
            if hs_m is None and "Heartsteel" in owned:
                hs_m = m
            fight = run_fight(owned, m, True, False, hs_m, "dive", runes, False)
            live = 1.0 if not fight["died"] else fight["survival"] / SURVIVE
            score += fight["total"] * (0.55 + 0.45 * live)
        if best is None or score > best[0]:
            best = (score, order)
    assert best is not None
    return best[1]


def refine_runes(full: List[dict]) -> List[dict]:
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
        for e in full:
            e["runes"] = DEFAULT_RUNES
        return full
    print(f"  expanding {rune_name(best_page)}", flush=True)
    pool = [e["items"] for e in scored if e["runes"] == best_page][:5]
    extra = {frozenset(items) for items in pool}
    for seed in list(pool):
        for nb in neighbors(seed):
            fs = frozenset(nb)
            if fs in extra or len(fs) != 6:
                continue
            if sum(1 for i in fs if i in BOOTS) != 1:
                continue
            extra.add(fs)
            scored.append(evaluate_full(nb, best_page))
    have = {(frozenset(e["items"]), e["runes"]) for e in scored}
    for e in full:
        key = (frozenset(e["items"]), DEFAULT_RUNES)
        if key not in have:
            e["runes"] = DEFAULT_RUNES
            scored.append(e)
    scored.sort(key=lambda e: (e["tier"], e["score"]), reverse=True)
    return scored


def self_check() -> None:
    for name, it in ITEMS.items():
        finish = it.cost - sum(ITEMS[c].cost for c in it.recipe)
        if finish < 0:
            raise AssertionError(f"negative combine on {name}: {finish}")
        for c in it.recipe:
            if c not in ITEMS:
                raise AssertionError(f"{name} missing {c}")
    for label, build in ARCHETYPES:
        if len(set(build)) != 6:
            raise AssertionError(label)
        if sum(1 for i in build if i in BOOTS) != 1:
            raise AssertionError(label + " boots")
        for group, gname in ((SPELLBLADES, "spellblade"), (LIFELINES, "lifeline")):
            if sum(1 for i in build if i in group) > 1:
                raise AssertionError(f"{label} two {gname}")
    q, w, e, r = skill_ranks(15)
    if (q, w, e, r) != (4, 4, 4, 3):
        raise AssertionError(f"ranks {q, w, e, r}")
    st = Build(("Plated Steelcaps", "Sterak's Gage"), 15, 18, True, (), None)
    problems = []

    def near(got, exp, tol, label):
        if abs(got - exp) > tol:
            problems.append(f"{label}: got {got:.3f} expected {exp:.3f}")

    near(st.max_hp, 3557.0, 0.1, "HP")
    near(st.total_ad(0), 177.0, 0.1, "AD")
    near(st.w_damage(True, st.total_ad(0), st.bonus_hp), 551.32, 0.2, "W2")
    near(st.e_shield(st.max_hp, 0), 497.98, 0.2, "shield")
    near(0.75 * st.bonus_hp, 806.25, 0.2, "sterak")
    near(st.base_armor + st.armor, 131.8, 0.05, "armor")
    near(st.attack_speed(5, 0, 0), 1.0472, 0.01, "AS")
    owned = purchase(("Plated Steelcaps", "Sterak's Gage"), 1200)
    if owned != ["Plated Steelcaps"]:
        problems.append(f"purchase boots {owned}")
    owned = purchase(("Plated Steelcaps", "Sterak's Gage"), 4400)
    if "Sterak's Gage" not in owned or "Plated Steelcaps" not in owned:
        problems.append(f"purchase full {owned}")
    if problems:
        raise AssertionError("; ".join(problems))


def antiheal(items: Sequence[str], runes: Sequence[str]) -> List[Tuple[Tuple[str, ...], dict]]:
    opts = [tuple(items)]
    boots = [i for i in items if i in BOOTS]
    legs = [i for i in items if i not in BOOTS]
    for b in BOOTS:
        opts.append(tuple(boots_first([b] + legs)))
    for i, _leg in enumerate(legs):
        rest = legs[:i] + legs[i + 1:]
        for alt in ("Kaenic Rookern", "Mantle of the Twelfth Hour", "Frozen Heart",
                    "Randuin's Omen", "Force of Nature", "Death's Dance", "Sterak's Gage"):
            if conflicts(rest, alt):
                continue
            opts.append(tuple(boots_first(boots + rest[:i] + [alt] + rest[i:])))
    seen = set()
    rows = []
    for opt in opts:
        fs = frozenset(opt)
        if fs in seen or len(fs) != 6:
            continue
        seen.add(fs)
        rows.append((opt, snapshot(opt, grievous=True, runes=runes)))
    rows.sort(key=lambda pair: (not pair[1]["died"], pair[1]["total"]), reverse=True)
    return rows[:8]


def render(full: List[dict], items: Sequence[str], runes: Sequence[str], order: Sequence[str]) -> str:
    r = snapshot(items, runes=runes, trace=True)
    brawl = snapshot(items, scenario="brawl", runes=runes)
    nor = snapshot(items, with_r=False, runes=runes)
    st = Build(items, 15, 18, True, runes, HS_SNAPSHOT if "Heartsteel" in items else None)
    lines = []
    a = lines.append
    a("=" * 78)
    a("VOLIBEAR — WILD RIFT, HARD TO KILL, HIGH DAMAGE   (patch 7.3d)")
    a("Baron lane. R onto the carry and stand in the focus for 11 seconds. 18:00, level 15.")
    a("=" * 78)
    a("")
    a("WHAT THE BITE SCALES WITH")
    a("  W1 = 80 + 110% AD + 6.5% bonus HP")
    a("  W2 = W1 × 1.60, and heals 50 + 14% missing HP")
    a("  Frenzy is on Volibear for 8s after he mauls a champion. It is not a")
    a("  mark that falls off when he changes target, and bonus AD does not")
    a("  raise the 1.60. Q is 90 + 100% bonus AD. R is 700 + 210% bonus AD")
    a("  + 100% AP, plus 525 HP. Lightning is 68 + 40% AP and has no AD ratio.")
    a("")
    a("WINNER")
    a(f"  {show(order)}")
    a(f"  Runes: {rune_name(runes)}")
    a(f"  R dive:     {r['total']:.0f} damage   lived {r['survival']:.1f}s   "
      f"end HP {r['end_hp']:.0f} / {r['max_hp']:.0f} ({pct(r):.0f}%)")
    a(f"              carry {r['carry']:.0f}   tank {r['tank']:.0f}   "
      f"healed {r['healed']:.0f}   shields absorbed {r['absorbed']:.0f}")
    a(f"  R brawl:    {brawl['total']:.0f} damage on the frontline  lived {brawl['survival']:.1f}s")
    a(f"  No ultimate:{nor['total']:.0f} damage   lived {nor['survival']:.1f}s   end HP {pct(nor):.0f}%")
    def down(when: Optional[float]) -> str:
        return f"{when:.1f}s" if when is not None else "still up"
    a(f"  Carry down at {down(r['carry_death'])}   frontliner down at {down(r['tank_death'])}")
    a(f"  Bites {r['bites']}   W casts {r['w_casts']}   autos {r['autos']}   "
      f"spellblades {r['spellblades']}   E hits {r['e_hits']}")
    a("")
    a("DAMAGE BY SOURCE  (R dive, post-mitigation)")
    for name, val in sorted(r["sources"].items(), key=lambda kv: -kv[1]):
        if val >= 1:
            a(f"  {name:<14} {val:7.0f}")
    a("")
    a("HEALS")
    for name, val in sorted(r["heals"].items(), key=lambda kv: -kv[1]):
        if val >= 1:
            a(f"  {name:<14} {val:7.0f}")
    a("")
    a("LEVEL 15, ULT UP, BEFORE THE FIGHT")
    a(f"  HP {st.max_hp:.0f} (bonus {st.bonus_hp:.0f}, includes +{st.r_hp:.0f} from R)")
    a(f"  AD {st.total_ad(6 if 'conqueror' in runes else 0):.0f}   "
      f"bonus AD {st.bonus_ad + (st.conq_ad(6) if 'conqueror' in runes else 0):.0f}")
    ap = st.ap_of(st.bonus_hp, 6 if "conqueror" in runes else 0)
    a(f"  AP {ap:.0f}   armor {st.base_armor + st.armor:.0f}   MR {st.base_mr + st.mr:.0f}")
    a(f"  W cooldown {cd(5, st.ah):.2f}s before Navori   "
      f"attack speed {st.attack_speed(5, 0, 0, conq=6 if 'conqueror' in runes else 0):.2f} at 5 passive stacks")
    w2 = st.w_damage(True, st.total_ad(6 if "conqueror" in runes else 0), st.bonus_hp)
    a(f"  W2 pre-mit {w2:.0f}    E shield {st.e_shield(st.max_hp, ap):.0f}")
    if "conqueror" in runes:
        a("  AD and AP above include fully stacked Conqueror. The fight ramps it from zero.")
    if r["max_hp"] > st.max_hp + 40:
        a(f"  The fight's max HP is {r['max_hp']:.0f} once a temporary bonus (Radiant or Mantle) is up.")
    a("")
    rows = antiheal(items, runes)
    a("60% GRIEVOUS  (Wild Rift Ignite. Thornmail on an enemy is 50%.)")
    for opt, g in rows:
        a(f"  {show(opt)}  dmg {g['total']:.0f}  lived {g['survival']:.1f}s  "
          f"end {pct(g):.0f}%  died {g['died']}")
    a("")
    a("-" * 78)
    a("FULL BUILDS AT 18:00  (tier 2 lives the ult, and lives the no-ult fight or lasts 7s)")
    a(f"  {'':<6} {'R dmg':>7} {'Live':>6} {'End':>5} {'Brawl':>7} {'NoR':>6} T  Build")
    for ev in full[:18]:
        mark = ""
        page = ev["runes"]
        if page[0] == "grasp":
            mark = "GR"
        elif page[0] == "lethal":
            mark = "LT"
        elif "triumph" in page:
            mark = "TR"
        a(f"  {mark:<6} {ev['r']['total']:>7.0f} {ev['r']['survival']:>5.1f}s "
          f"{pct(ev['r']):>4.0f}% {ev['brawl']['total']:>7.0f} {ev['nor']['survival']:>5.1f}s "
          f"{ev['tier']}  {show(ev['items'])}")
    a("")
    a("-" * 78)
    a("PURCHASE ORDER  (same 6 items, order maximizes damage from 8:00 to 18:00)")
    a(f"  {show(order)}")
    a("")
    a(f"  {'Min':>4} {'Gold':>7} {'Lvl':>4}  Inventory")
    for m in list(range(4, 19, 2)) + [18]:
        owned = purchase(order, gold_at_minute(m))
        inv = " › ".join(short(n) for n in owned) if owned else "(start)"
        a(f"  {m:>4} {gold_at_minute(m):>7} {level_at_minute(m):>4}  {inv}")
    a("")
    a("-" * 78)
    a("VERDICT")
    a("-" * 78)
    a(f"  Buy: {show(order)}")
    a("")
    owned_set = set(items)
    a("  WHY THIS IS THE LATE-GAME VOLIBEAR ON WILD RIFT:")
    a("  • The wounded bite is 1.60× the normal maul. Bonus AD does not raise")
    a("    that multiplier. AD still feeds the 110% / 176% ratios, Q and R.")
    a("    Bonus HP feeds the 6.5% / 10.4% ratios and the E shield.")
    a("  • Spirit Visage is not in the game. Healing is the raw W heal,")
    a("    spellblade heals, and whatever Lifeline he bought.")
    if "Navori Quickblades" in owned_set:
        a("  • Navori is how W comes back inside the ultimate. Each attack cuts")
        a("    15% off the remaining Q, W and E cooldown. The 25% crit is on the")
        a("    attack, and crits deal 200% damage on this patch.")
    if "Dusk and Dawn" in owned_set:
        a("  • Dusk and Dawn is the spellblade that also heals (10% AP + 3% bonus")
        a("    HP) and applies on-hit a second time. Lightning has no AD ratio,")
        a("    so the AP and the extra on-hit are the point of the item.")
    if "Divine Sunderer" in owned_set:
        a("  • Divine Sunderer is 10% of the target's max HP on the spellblade")
        a("    and a heal for 6% of their max HP, on a 1.5s cooldown.")
    if "Riftmaker" in owned_set:
        a("  • Riftmaker turns 2% of bonus HP into AP. After 4 seconds in the")
        a("    fight it is +8% damage and 10% omnivamp.")
    if "At Wit's End" in owned_set:
        a("  • Wit's End is 50% attack speed, 45 magic resistance and a 40")
        a("    magic on-hit. Patch 7.3 removed its heal.")
    if "Trinity Force" in owned_set:
        a("  • Trinity's spellblade is 200% base AD. It is one hit on a 1.5s")
        a("    cooldown, which is why it has to come with a way to bite again.")
    if "Sterak's Gage" in owned_set:
        a("  • Sterak is 50% of base AD as bonus AD, 20% tenacity, and a shield")
        a("    for 75% of bonus HP when he crosses 35% life.")
    if "Mantle of the Twelfth Hour" in owned_set:
        a("  • Mantle is the tank Lifeline: +300 HP and a heal for bonus resists")
        a("    plus 15% bonus HP when he crosses 30% life. It shares the Lifeline")
        a("    slot with Sterak.")
    if "Radiant Virtue" in owned_set:
        a("  • Radiant Virtue adds 10% max HP for 6s on the ultimate and heals")
        a("    2.5% max HP per second for those 6s. The no-ult column is there")
        a("    so a build that only exists during Stormbringer does not win.")
    if "Amaranth's Twinguard" in owned_set:
        a("  • Twinguard, after 5s in the fight, adds 30% of his bonus armor and")
        a("    bonus MR. It is the capstone, not the first buy, unless the order")
        a("    search says otherwise.")
    if "Unending Despair" in owned_set:
        a("  • Unending pulses 3% max HP magic every 4s and heals for 250% of")
        a("    the post-mitigation damage, once per enemy standing in it.")
    if "Heartsteel" in owned_set:
        a("  • Heartsteel's proc is 140 + 3.5% max HP, and 15% of that becomes")
        a("    permanent HP. One proc lands in this fight. Lane stacks assume")
        a("    the item was finished at 10:00.")
    a("  • R's bonus HP is bonus health for the bite and the E shield. The")
    a("    no-ult column keeps a 12-second stat stick from winning the search.")
    a("")
    by_name = {label: build for label, build in ARCHETYPES}
    for label in ("Full Tank", "AP Glass", "Trinity Bruiser", "Heartsteel"):
        ev = next(e for e in full if frozenset(e["items"]) == frozenset(by_name[label]))
        a(f"  Vs {label} ({show(ev['items'])}):")
        a(f"    {ev['r']['total']:.0f} in {ev['r']['survival']:.1f}s, died={ev['r']['died']}, "
          f"end {pct(ev['r']):.0f}%.")
    a("")
    lived = [(opt, g) for opt, g in rows if not g["died"]]
    a("  ANTIHEAL:")
    g0 = rows[0][1]
    if not snapshot(items, grievous=True, runes=runes)["died"]:
        gwin = snapshot(items, grievous=True, runes=runes)
        a(f"    With 60% grievous the winner still stands ({gwin['survival']:.1f}s, "
          f"end {pct(gwin):.0f}%, {gwin['total']:.0f} damage).")
    else:
        gwin = snapshot(items, grievous=True, runes=runes)
        a(f"    With 60% grievous the winner dies at {gwin['survival']:.1f}s.")
        if lived:
            opt, g = max(lived, key=lambda pair: pair[1]["total"])
            a(f"    Into Ignite, prefer {show(opt)}")
            a(f"    ({g['total']:.0f} damage, lived, end {pct(g):.0f}%).")
    a("")
    a("  RUNES:")
    a(f"    {rune_name(runes)}")
    if runes[0] == "conqueror":
        a("    Conqueror is 5 AD or 8 AP per stack at level 15, six stacks,")
        a("    then 9% omnivamp. The fight starts at zero stacks.")
    elif runes[0] == "grasp":
        a("    Grasp is 3% max HP magic, a 1.3% max HP heal, and +8 permanent")
        a("    HP every 3s. Demolish is the other published slot and does")
        a("    nothing to a champion, so it is not in the fight.")
    elif runes[0] == "lethal":
        a("    Lethal Tempo is 6% attack speed per stack, then a bolt that")
        a("    scales with bonus attack speed.")
    a("    Last Stand is 5–11% damage below 60% HP. Alacrity is 21% attack")
    a("    speed once it is stacked. Overgrowth is +90 HP and 3% max HP.")
    a("  SKILL ORDER: W max, E second, Q last. R at 5/9/13. At level 15")
    a("    Q, W and E are all rank 4, so the finished fight does not change")
    a("    if Q was maxed second. E second is the shield on the way there.")
    if "Navori Quickblades" in owned_set:
        a("  FIGHT: Cast E on the dive, Q, R so you land as E hits, Q auto the")
        a("    carry, bite, keep attacking. Navori does nothing if he is kited.")
    else:
        a("  FIGHT: Cast E on the dive, Q, R so you land as E hits, Q auto the")
        a("    carry, bite, keep attacking between spells. Spellblade is ready")
        a("    again 1.5s after it fires, so an ability into an attack is the loop.")
    a("    Frenzy stays on him when the carry dies. The next bite on whoever")
    a("    is left is still the 1.60× maul until the 8 seconds run out.")
    a("")
    a("  TRAPS:")
    a("    • A full resist page with no AD leaves the 176% ratio on base AD.")
    a("      Heartsteel's one proc does not replace the bites.")
    a("    • Deathcap and Nashor with no health fall over while the ultimate")
    a("      is still up. Lightning and E scale with AP. The W heal does not.")
    a("    • Stacking two spellblades is impossible. Trinity, Dusk, Divine")
    a("      and Iceborn share the slot.")
    a("    • Sterak and Mantle share the Lifeline. Buying both does nothing")
    a("      for the second proc.")
    a("")
    a("MODEL")
    a("  Discrete 0.1s. Damage is post-mitigation. Conqueror, passive stacks")
    a("  and Lethal Tempo start at zero. Lightning is not on from the first")
    a("  attack. Omnivamp is full value against champions. The W heal is")
    a("  grievous-cut in the Ignite column. Shields are not.")
    a("  Steelcaps / Armored Advance cut 10% of the basic-attack share of")
    a("  the physical focus (65% of it). Randuin cuts crits, modeled as 30%")
    a("  off 55% of incoming physical. Frozen Heart cuts 25% attack speed")
    a("  off that same basic-attack share. Q's stun removes most of the")
    a("  physical focus for 1s.")
    a("  Shojin's Focused Will percent is not on the stat card this sim")
    a("  used, so Shojin is scored on 40 AD, 450 HP and 20 haste. Hullbreaker's")
    a("  every-fourth-attack bonus is 160% base AD. Dead Man's crush is not")
    a("  modeled. Guinsoo still crits: patch 7.3 removed the crit lock.")
    a("  Wit's End no longer heals. Heartsteel lane stacks are 0.7 procs a")
    a("  minute after it is finished. Grasp lane stacks are 2.2 procs a minute.")
    a("")
    return "\n".join(lines) + "\n"


def main() -> None:
    t0 = time.time()
    self_check()
    print("searching", flush=True)
    full = search()
    full = refine_runes(full)
    winner = full[0]
    items = winner["items"]
    runes = winner["runes"]
    print("ordering", show(items), flush=True)
    order = best_order(items, runes)
    text = render(full, items, runes, order)
    with open(os.path.join(HERE, "report.txt"), "w", encoding="utf-8") as f:
        f.write(text)
    payload = []
    for ev in full[:20]:
        payload.append({
            "items": list(ev["items"]),
            "runes": list(ev["runes"]),
            "tier": ev["tier"],
            "score": round(ev["score"], 1),
            "damage": round(ev["r"]["total"], 1),
            "survival": round(ev["r"]["survival"], 2),
            "end_hp_pct": round(pct(ev["r"]), 1),
            "died": ev["r"]["died"],
            "no_ult_survival": round(ev["nor"]["survival"], 2),
            "brawl": round(ev["brawl"]["total"], 1),
        })
    with open(os.path.join(HERE, "results.json"), "w", encoding="utf-8") as f:
        json.dump({"patch": "7.3d", "game_minutes": GAME_MINUTES, "builds": payload}, f, indent=2)
    print(text)
    print(f"done in {time.time() - t0:.1f}s", flush=True)


if __name__ == "__main__":
    if "--check" in sys.argv:
        self_check()
        print("self_check ok")
    else:
        main()
