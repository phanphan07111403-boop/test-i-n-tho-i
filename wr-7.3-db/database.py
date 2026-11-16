#!/usr/bin/env python3
"""
Wild Rift patch 7.3 local item + system database.

This is the in-repo memory for later build / DPS work. Simulations should
import from here instead of scraping the web.

Values come from:
  - Official global patch notes 7.3 (2026-09-21)
  - WR China PBE notes (2026-09-01) where they add numeric passives
  - wildriftfire 7.3 Varus page for kit numbers not in the notes
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

PATCH = "7.3"
PATCH_DATE = "2026-09-22"

SYSTEM: Dict[str, Any] = {
    "crit_damage": 2.0,  # 175% → 200%
    "attack_speed_cap": 3.0,  # 2.5 → 3.0 attacks/sec
    "as_ratio_split": "per_champion",  # no longer melee vs ranged
    "new_stat": "lifesteal",
    "replaced_stat": "omnivamp_and_physical_vamp_on_listed_items",
    "lifesteal_replaces_vamp_on": [
        "mercurial_scimitar",
        "vampiric_scepter",
        "bloodthirster",
        "blade_of_the_ruined_king",
        "gunmetal_greaves",
    ],
    "new_champions": ["Hwei", "Sylas", "Rek'Sai"],
    "removed_items": [
        "Magnetic Blaster",
        "Soul Transfer",
        "Cloak of Agility",
        "Nashor's Talon",
        "Surging Scales",
        "Stinger",
        "Shimmering Spark",
        "Ingenious Hunter (rune)",
        "Legend: Tenacity (rune)",
    ],
    "new_items": [
        "Pickaxe",
        "Hearthbound Axe",
        "Hexoptics C44",
        "Yun Tal Wildarrows",
        "Stormrazor",
        "Rapid Firecannon",
        "Fiendhunter Bolts",
        "Immortal Shieldbow",
        "Statikk Shiv",
        "Bandleglass Mirror",
        "Whispering Circlet",
        "Diadem of Songs",
        "Echoes of Helia",
    ],
    "armor_formula": "100 / (100 + armor)",
    "mr_formula": "100 / (100 + mr)",
    "pen_order": "flat_lethality_then_percent_pen",
}

# ---------------------------------------------------------------------------
# Items. Stats are the 7.3 live values. `new` = added this patch.
# `approx` marks a leftover stat not printed in 7.3 notes (pre-7.3 WR value).
# ---------------------------------------------------------------------------

def _item(
    item_id: str,
    name: str,
    cost: int,
    *,
    tier: str,
    klass: str,
    stats: Dict[str, float],
    build_path: str = "",
    passives: Optional[list] = None,
    new: bool = False,
    removed_stats: Optional[list] = None,
    tags: Optional[list] = None,
    notes: str = "",
    approx_stats: Optional[list] = None,
) -> Dict[str, Any]:
    return {
        "id": item_id,
        "name": name,
        "cost": cost,
        "tier": tier,
        "class": klass,
        "stats": stats,
        "build_path": build_path,
        "passives": passives or [],
        "new_in_7_3": new,
        "removed_stats": removed_stats or [],
        "tags": tags or [],
        "notes": notes,
        "approx_stats": approx_stats or [],
    }


ITEMS: Dict[str, Dict[str, Any]] = {}


def add(item: Dict[str, Any]) -> None:
    ITEMS[item["id"]] = item


# -- components --------------------------------------------------------------
add(_item("long_sword", "Long Sword", 500, tier="basic", klass="ad", stats={"ad": 12}, tags=["component"], notes="Unchanged component.", approx_stats=["ad"]))
add(_item("dagger", "Dagger", 400, tier="basic", klass="as", stats={"as": 0.12}, tags=["component"], notes="7.3: 500→400g, AS 15%→12%."))
add(_item("brawlers_gloves", "Brawler's Gloves", 500, tier="basic", klass="crit", stats={"crit": 0.12}, tags=["component"], notes="Crit gloves. Cloak of Agility removed.", approx_stats=["crit"]))
add(_item("bf_sword", "B.F. Sword", 1500, tier="epic", klass="ad", stats={"ad": 40}, tags=["component"], approx_stats=["ad"]))
add(_item("pickaxe", "Pickaxe", 800, tier="epic", klass="ad", stats={"ad": 20}, build_path="Long Sword (500) + 300", new=True, tags=["component", "new"]))
add(_item("recurve_bow", "Recurve Bow", 900, tier="epic", klass="onhit", stats={"as": 0.20}, build_path="Dagger (400) + 500", tags=["component", "onhit"], notes="7.3: 1400→900g, AS 30%→20%."))
add(_item("noonquiver", "Noonquiver", 1300, tier="epic", klass="crit", stats={"ad": 20, "crit": 0.15}, build_path="Long Sword (500) + Brawler's Gloves (500) + 300", tags=["component", "crit"], notes="7.3: AD 25→20, AS removed, +15% crit."))
add(_item("hearthbound_axe", "Hearthbound Axe", 1200, tier="epic", klass="onhit", stats={"ad": 20, "as": 0.15}, build_path="Long Sword (500) + Dagger (400) + 300", new=True, tags=["component", "onhit", "new"]))
add(_item("kircheis_shard", "Kircheis Shard", 800, tier="epic", klass="energized", stats={"as": 0.20}, build_path="Dagger (400) + 400", tags=["component", "energized"], notes="7.3: AD removed, +20% AS.", passives=[{"name": "Shock", "magic": 40, "cd": 25, "cd_refund_per_auto": 1}]))
add(_item("last_whisper", "Last Whisper", 1200, tier="epic", klass="pen", stats={"ad": 15, "armor_pen": 0.15}, build_path="Long Sword (500) + 700", tags=["component", "pen"]))
add(_item("vampiric_scepter", "Vampiric Scepter", 1200, tier="epic", klass="lifesteal", stats={"ad": 15, "lifesteal": 0.08}, tags=["component"], notes="Physical vamp → 8% lifesteal.", approx_stats=["ad"]))
add(_item("zeal", "Zeal", 1400, tier="epic", klass="crit", stats={"as": 0.20, "crit": 0.15, "ms_pct": 0.04}, tags=["component", "crit"], notes="MS 5%→4%. AS/crit leftover from pre-7.3 Zeal.", approx_stats=["as", "crit"]))
add(_item("serrated_dirk", "Serrated Dirk", 1000, tier="epic", klass="lethality", stats={"ad": 20, "lethality": 12}, tags=["component"], approx_stats=["ad", "lethality"]))
add(_item("caulfields_warhammer", "Caulfield's Warhammer", 1200, tier="epic", klass="ad", stats={"ad": 20, "ah": 20}, tags=["component"], approx_stats=["ad", "ah"]))
add(_item("sheen", "Sheen", 800, tier="epic", klass="spellblade", stats={}, tags=["component"], passives=[{"name": "Spellblade", "phys_from_base_ad": 1.0, "cd": 1.5}]))
add(_item("executioners_calling", "Executioner's Calling", 800, tier="epic", klass="antiheal", stats={"ad": 15}, tags=["component"], passives=[{"name": "Sepsis", "grievous": 0.50, "duration": 3}], approx_stats=["ad"]))
add(_item("amplifying_tome", "Amplifying Tome", 500, tier="basic", klass="ap", stats={"ap": 20}, tags=["component"]))
add(_item("negatron_cloak", "Negatron Cloak", 900, tier="epic", klass="mr", stats={"mr": 35}, tags=["component"], approx_stats=["mr"]))
add(_item("aether_wisp", "Aether Wisp", 950, tier="epic", klass="ap", stats={"ap": 30, "ms_pct": 0.04}, tags=["component"], notes="MS 5%→4%.", approx_stats=["ap"]))
add(_item("tear_of_the_goddess", "Tear of the Goddess", 400, tier="epic", klass="mana", stats={"mana": 240}, tags=["component"], notes="7.3 Manamune path uses Tear 400–500.", approx_stats=["mana"]))
add(_item("ruby_crystal", "Ruby Crystal", 500, tier="basic", klass="hp", stats={"hp": 200}, tags=["component"]))
add(_item("kindlegem", "Kindlegem", 1000, tier="epic", klass="hp", stats={"hp": 200, "ah": 10}, tags=["component"], approx_stats=["hp", "ah"]))
add(_item("forbidden_idol", "Forbidden Idol", 700, tier="epic", klass="enchanter", stats={"heal_shield": 0.06}, tags=["component"], notes="7.3: 900→700g, HSP 4%→6%, HP and AH removed."))
add(_item("bandleglass_mirror", "Bandleglass Mirror", 900, tier="epic", klass="enchanter", stats={"ap": 20, "mana_regen": 0.50, "ah": 10}, build_path="Amplifying Tome (500) + Ring of Revelation (300) + 100", new=True, tags=["component", "new"]))
add(_item("boots_of_speed", "Boots of Speed", 400, tier="basic", klass="boots", stats={"ms": 25}, tags=["boots"], approx_stats=["ms"]))
add(_item("berserkers_greaves", "Berserker's Greaves", 1200, tier="boots", klass="boots", stats={"ad": 10, "as": 0.35, "ms": 45}, build_path="Boots of Speed (400) + Dagger (400) + 400", tags=["boots"], notes="7.2c: AS 30%→35%. Unchanged in 7.3 notes.", approx_stats=["ad", "ms"]))
add(_item("plated_steelcaps", "Plated Steelcaps", 900, tier="boots", klass="boots", stats={"armor": 15, "ms": 45}, tags=["boots"], notes="Unchanged in 7.3 notes.", approx_stats=["armor", "ms"]))
add(_item("ionian_boots", "Ionian Boots of Lucidity", 900, tier="boots", klass="boots", stats={"ah": 20, "ms": 45}, tags=["boots"], approx_stats=["ah", "ms"]))

# -- new legendaries ---------------------------------------------------------
add(_item(
    "hexoptics_c44", "Hexoptics C44", 2900, tier="legendary", klass="crit",
    stats={"ad": 55, "crit": 0.25},
    build_path="Pickaxe (800) + Noonquiver (1300) + Long Sword (500) + 300",
    new=True, tags=["crit", "new", "range"],
    passives=[
        {"name": "Magnification", "bonus_damage_min": 0.0, "bonus_damage_max": 0.10, "max_range": 550},
        {"name": "Arcane Aim", "bonus_range": 100, "duration": 8, "takedown_window": 3},
    ],
    notes="Distance amp on attacks. Takedown grants +100 range for 8s.",
))
add(_item(
    "yun_tal_wildarrows", "Yun Tal Wildarrows", 3100, tier="legendary", klass="crit",
    stats={"ad": 50, "crit": 0.0, "as": 0.25},
    build_path="Noonquiver (1300) + Pickaxe (800) + Kircheis Shard (800) + 200",
    new=True, tags=["crit", "new", "first_item", "scaling"],
    passives=[
        {
            "name": "Practice Makes Perfect",
            "crit_per_auto_melee": 0.004,
            "crit_per_auto_ranged": 0.002,
            "crit_cap": 0.25,
        },
        {
            "name": "Flurry",
            "as": 0.25,
            "duration": 6,
            "cd": 20,
            "cd_refund_auto": 1,
            "cd_refund_crit": 2,
        },
    ],
    notes="Starts at 0% crit. Ranged needs 125 autos to cap 25% crit.",
))
add(_item(
    "stormrazor", "Stormrazor", 3000, tier="legendary", klass="crit",
    stats={"ad": 50, "crit": 0.25, "as": 0.20},
    build_path="B.F. Sword (1500) + Kircheis Shard (800) + Brawler's Gloves (500) + 200",
    new=True, tags=["crit", "new", "energized", "first_item"],
    passives=[
        {"name": "Energized", "kind": "move_and_attack"},
        {"name": "Bolt", "magic": 120, "ms_pct": 0.45, "ms_duration": 1.5},
    ],
))
add(_item(
    "rapid_firecannon", "Rapid Firecannon", 2650, tier="legendary", klass="crit",
    stats={"crit": 0.25, "as": 0.40, "ms_pct": 0.04},
    build_path="Zeal (1400) + Kircheis Shard (800) + 450",
    new=True, tags=["crit", "new", "energized", "zeal", "range"],
    passives=[
        {"name": "Energized", "kind": "move_and_attack"},
        {"name": "Sharpshooter", "magic": 80, "range_pct": 0.35, "range_cap": 150},
    ],
))
add(_item(
    "fiendhunter_bolts", "Fiendhunter Bolts", 2650, tier="legendary", klass="crit",
    stats={"crit": 0.25, "as": 0.45, "ms_pct": 0.04, "ult_haste": 20},
    build_path="Zeal (1400) + Kircheis Shard (800) + 450",
    new=True, tags=["crit", "new", "zeal", "ultimate"],
    passives=[
        {"name": "Night Vigil", "ult_haste": 20},
        {
            "name": "Opening Barrage",
            "after_ult_attacks": 3,
            "as": 0.50,
            "guaranteed_crit": True,
            "crit_damage_factor": 0.80,
            "already_crit_true_pct": 0.15,
            "window": 8,
            "cd": 45,
        },
    ],
))
add(_item(
    "immortal_shieldbow", "Immortal Shieldbow", 3000, tier="legendary", klass="crit",
    stats={"ad": 55, "crit": 0.25},
    build_path="Noonquiver (1300) + Pickaxe (800) + 900",
    new=True, tags=["crit", "new", "defensive"],
    passives=[
        {
            "name": "Lifeline",
            "hp_threshold": 0.35,
            "duration": 3,
            "shield_melee": [350, 650],
            "shield_ranged": [300, 550],
            "cd": 70,
        },
    ],
    notes="Official EN uses 35% HP; CN notes said 30%. Using EN 35%.",
))
add(_item(
    "statikk_shiv", "Statikk Shiv", 3000, tier="legendary", klass="onhit",
    stats={"ad": 40, "ap": 40, "as": 0.30, "ms_pct": 0.04},
    build_path="Aether Wisp (950) + Pickaxe (800) + Kircheis Shard (800) + 450",
    new=True, tags=["onhit", "new", "energized", "waveclear"],
    passives=[
        {"name": "Energized", "kind": "move_and_attack"},
        {
            "name": "Electroshock",
            "bounces": [3, 4, 5, 6],
            "bounce_levels": [1, 5, 9, 13],
            "magic": 60,
            "magic_minion": 90,
            "bounces_apply_onhit": True,
        },
        {"name": "Electrotherapy", "bonus_energized_per_auto": 5},
    ],
))

# -- reworked marksman legendaries ------------------------------------------
add(_item(
    "bloodthirster", "Bloodthirster", 3200, tier="legendary", klass="ad",
    stats={"ad": 75, "lifesteal": 0.15},
    build_path="Vampiric Scepter (1200) + B.F. Sword (1500) + 500",
    tags=["ad", "lifesteal", "no_crit"],
    removed_stats=["crit 25%", "hp 250", "physical_vamp 8%"],
    passives=[{"name": "Ichorshield", "overheal_shield": [165, 345]}],
    notes="No longer a crit item. High AD + lifesteal capstone.",
))
add(_item(
    "essence_reaver", "Essence Reaver", 3000, tier="legendary", klass="crit",
    stats={"ad": 50, "crit": 0.25, "ah": 20},
    build_path="Sheen (800) + Caulfield's Warhammer (1200) + Brawler's Gloves (500) + 500",
    tags=["crit", "spellblade"],
    approx_stats=["crit", "ah", "cost"],
    passives=[{
        "name": "Spellblade",
        "phys": "1.35 * base_ad + 0 to 80 from crit (0.8 per 1% crit)",
        "mana_restore": 0.50,
        "cd": 1.5,
        "window": 10,
    }],
))
add(_item(
    "galeforce", "Galeforce", 3100, tier="legendary", klass="crit",
    stats={"ad": 60, "crit": 0.25, "ms_pct": 0.04},
    build_path="Noonquiver (1300) + Pickaxe (800) + Long Sword (500) + 500",
    tags=["crit", "mobility"],
    approx_stats=["crit", "cost"],
    removed_stats=["as 15%"],
    notes="Dash active. AS removed, AD 50→60.",
))
add(_item(
    "the_collector", "The Collector", 3000, tier="legendary", klass="crit",
    stats={"ad": 50, "crit": 0.25, "lethality": 12},
    build_path="Serrated Dirk (1000) + Noonquiver (1300) + 700",
    tags=["crit", "lethality", "execute"],
    approx_stats=["crit", "lethality"],
    passives=[{
        "name": "Death and Taxes",
        "execute_pct": 0.05,
        "execute_growth": 0.001,
        "bonus_gold": 25,
    }],
))
add(_item(
    "kraken_slayer", "Kraken Slayer", 2900, tier="legendary", klass="onhit",
    stats={"ad": 45, "as": 0.35, "ms_pct": 0.04},
    build_path="Recurve Bow (900) + Hearthbound Axe (1200) + Long Sword (500) + 300",
    tags=["onhit", "first_item"],
    passives=[{
        "name": "Bring It Down",
        "every": 3,
        "phys_melee": [150, 210],
        "phys_ranged": [120, 168],
        "missing_hp_amp_per_pct": 0.0075,
        "missing_hp_amp_cap": 0.75,
    }],
))
add(_item(
    "blade_of_the_ruined_king", "Blade of the Ruined King", 3100, tier="legendary", klass="onhit",
    stats={"ad": 40, "as": 0.30, "lifesteal": 0.12},
    build_path="Vampiric Scepter (1200) + Pickaxe (800) + Recurve Bow (900) + 200",
    tags=["onhit", "lifesteal", "first_item"],
    notes="CN notes AD 25→40. Lifesteal 12% replaces omnivamp.",
    passives=[
        {"name": "Ruined Strike", "current_hp_ranged": 0.07, "current_hp_melee": 0.085, "min": 15, "monster_cap": 100},
        {"name": "Drain", "hits": 3, "slow": 0.30, "duration": 1.5, "cd": 30},
    ],
))
add(_item(
    "guinsoos_rageblade", "Guinsoo's Rageblade", 3000, tier="legendary", klass="onhit",
    stats={"ad": 35, "ap": 30},
    build_path="Amplifying Tome (500) + Recurve Bow (900) + Pickaxe (800) + 800",
    tags=["onhit", "core"],
    notes="Crit restriction removed. No innate AS; AS comes from Seething Strike stacks. No MS.",
    passives=[
        {"name": "Wrath", "magic": 30},
        {"name": "Seething Strike", "as_per_stack": 0.08, "max_stacks": 4, "phantom_every": 3},
    ],
))
add(_item(
    "wits_end", "Wit's End", 2800, tier="legendary", klass="onhit",
    stats={"as": 0.50, "mr": 40, "tenacity": 0.20},
    build_path="Recurve Bow (900) + Negatron Cloak (900) + Dagger (400) + 600",
    tags=["onhit", "mr"],
    approx_stats=["mr", "cost"],
    passives=[{"name": "At Wit's End", "magic": 40}],
))
add(_item(
    "terminus", "Terminus", 3000, tier="legendary", klass="onhit",
    stats={"ad": 35, "as": 0.35},
    build_path="Recurve Bow (900) + Hearthbound Axe (1200) + 900",
    tags=["onhit", "pen"],
    passives=[
        {"name": "Shadow", "magic": 30},
        {
            "name": "Juxtaposition",
            "light_armor_mr": [5, 8],
            "dark_pen": 0.10,
            "max_stacks": 3,
        },
    ],
))
add(_item(
    "phantom_dancer", "Phantom Dancer", 2650, tier="legendary", klass="crit",
    stats={"as": 0.40, "crit": 0.25, "ms_pct": 0.07},
    build_path="Zeal (1400) + Dagger (400) + Dagger (400) + 450",
    tags=["crit", "zeal", "kiting"],
    approx_stats=["as", "crit"],
    removed_stats=["ad 20"],
    notes="AD removed. MS 5%→7%. AS/crit inferred from Zeal + 2 Daggers.",
    passives=[{"name": "Spectral Waltz", "as_per_stack": 0.06, "ms_per_stack": 0.01, "max_stacks": 5, "duration": 6}],
))
add(_item(
    "runaans_hurricane", "Runaan's Hurricane", 2650, tier="legendary", klass="onhit",
    stats={"as": 0.40, "crit": 0.25, "ms_pct": 0.04},
    build_path="Zeal (1400) + Kircheis Shard (800) + 450",
    tags=["onhit", "crit", "aoe", "zeal"],
    approx_stats=["crit"],
    notes="Wind's Edge removed. Bolts can crit and apply on-hit.",
    passives=[{"name": "Wind's Fury", "bolts": 2, "ad_ratio": 0.55, "can_crit": True, "apply_onhit": True}],
))
add(_item(
    "mortal_reminder", "Mortal Reminder", 3000, tier="legendary", klass="crit",
    stats={"ad": 35, "crit": 0.25, "armor_pen": 0.30},
    build_path="Last Whisper (1200) + Executioner's Calling (800) + Brawler's Gloves (500) + 500",
    tags=["crit", "pen", "antiheal"],
    approx_stats=["crit"],
    removed_stats=["as 15%"],
    passives=[{"name": "Sepsis", "grievous": 0.50, "duration": 3}],
))
add(_item(
    "infinity_edge", "Infinity Edge", 3500, tier="legendary", klass="crit",
    stats={"ad": 75, "crit": 0.25, "crit_damage": 0.30},
    build_path="B.F. Sword (1500) + Pickaxe (800) + Brawler's Gloves (500) + 700",
    tags=["crit", "capstone"],
    notes="Crit damage 200%→230%. Break the Limit removed. Cost from build path.",
    passives=[{"name": "Infinity", "crit_damage": 2.30}],
))
add(_item(
    "manamune", "Manamune", 2900, tier="legendary", klass="mana",
    stats={"ad": 40, "mana": 500, "ah": 15},
    build_path="Caulfield's Warhammer (1200) + Tear of the Goddess (400) + Long Sword (500) + 800",
    tags=["mana", "ad"],
    passives=[
        {"name": "Awe", "ad_from_mana": 0.02, "mana_refund": 0.15},
        {"name": "Mana Charge", "mana_per_proc": 14, "cap": 700, "max_per_10s": 3},
    ],
))
add(_item(
    "muramana", "Muramana", 2900, tier="legendary", klass="mana",
    stats={"ad": 40, "mana": 1200, "ah": 15},
    tags=["mana", "ad", "onhit"],
    notes="Tear transform. Shock is on-hit + ability.",
    passives=[
        {"name": "Awe", "ad_from_mana": 0.02, "mana_refund": 0.15},
        {"name": "Shock", "auto_mana": 0.015, "ability_mana_melee": 0.035, "ability_mana_ranged": 0.03},
    ],
))
add(_item(
    "seryldas_grudge", "Serylda's Grudge", 3100, tier="legendary", klass="pen",
    stats={"ad": 50, "ah": 20, "armor_pen": 0.35},
    build_path="Caulfield's Warhammer (1200) + Last Whisper (1200) + 700",
    tags=["pen", "ability"],
    approx_stats=["ah"],
    passives=[{"name": "Icy", "slow": 0.30, "duration": 1, "hp_threshold": 0.60}],
    notes="Frostbite removed. Slow only below 60% HP.",
))
add(_item(
    "navori_quickblades", "Navori Quickblades", 2650, tier="legendary", klass="crit",
    stats={"as": 0.40, "crit": 0.25, "ms_pct": 0.04},
    tags=["crit", "zeal", "haste"],
    approx_stats=["crit"],
    passives=[{"name": "Deft Strikes", "basic_cdr_remaining": 0.15}],
))
add(_item(
    "lord_dominiks_regards", "Lord Dominik's Regards", 3300, tier="legendary", klass="crit",
    stats={"ad": 35, "crit": 0.25, "armor_pen": 0.35},
    build_path="Last Whisper (1200) + Noonquiver (1300) + 800",
    tags=["crit", "pen", "vs_tanks"],
    approx_stats=["crit"],
    notes="CN notes AD 25→35; EN 30→35. Using 35. Giant Slayer leftover.",
    passives=[{"name": "Giant Slayer", "max_bonus_damage": 0.25, "vs_higher_hp": True, "approx": True}],
))
add(_item(
    "mercurial_scimitar", "Mercurial Scimitar", 2900, tier="legendary", klass="ad",
    stats={"ad": 40, "mr": 40, "lifesteal": 0.12},
    tags=["qss", "lifesteal"],
    approx_stats=["ad", "mr", "cost"],
    notes="Physical vamp → 12% lifesteal. QSS active unchanged.",
))

# -- new / changed enchanter -------------------------------------------------
add(_item("whispering_circlet", "Whispering Circlet", 2400, tier="legendary", klass="enchanter", stats={"hp": 200, "mana": 500, "mana_regen": 0.50, "heal_shield": 0.08}, new=True, tags=["enchanter", "new", "mana"]))
add(_item("diadem_of_songs", "Diadem of Songs", 2400, tier="legendary", klass="enchanter", stats={"hp": 200, "mana": 1200, "mana_regen": 0.50, "heal_shield": 0.08}, new=True, tags=["enchanter", "new", "mana"]))
add(_item("echoes_of_helia", "Echoes of Helia", 2400, tier="legendary", klass="enchanter", stats={"hp": 200, "ap": 40, "ah": 20, "mana_regen": 0.50}, new=True, tags=["enchanter", "new"]))
add(_item("ardent_censer", "Ardent Censer", 2400, tier="legendary", klass="enchanter", stats={"ap": 50, "heal_shield": 0.08, "ms_pct": 0.04}, tags=["enchanter"], passives=[{"name": "Censer", "as": 0.30, "onhit_magic": 25, "duration": 6}]))
add(_item("staff_of_flowing_waters", "Staff of Flowing Waters", 2400, tier="legendary", klass="enchanter", stats={"ap": 50, "heal_shield": 0.08, "ah": 10, "ms_pct": 0.04}, tags=["enchanter"], approx_stats=["ap", "ms_pct"]))
add(_item("harmonic_echo", "Harmonic Echo", 2500, tier="legendary", klass="enchanter", stats={"hp": 200, "ap": 40, "ah": 20}, tags=["enchanter"]))
add(_item("imperial_mandate", "Imperial Mandate", 2600, tier="legendary", klass="enchanter", stats={"ap": 60, "ah": 20, "mana_regen": 0.50}, tags=["enchanter"], passives=[{"name": "Control", "cc_haste": 20, "mark_amp": 0.07, "mark_duration": 4}], approx_stats=["ah"]))
add(_item("shurelyas_battlesong", "Shurelya's Battlesong", 2500, tier="legendary", klass="enchanter", stats={"ap": 40, "ah": 20, "ms_pct": 0.04, "mana_regen": 0.50}, tags=["enchanter"], approx_stats=["ap", "ah", "cost"]))
add(_item("bamis_cinder", "Bami's Cinder", 1200, tier="epic", klass="tank", stats={"hp": 200, "ah": 5}, tags=["tank"]))

RUNES: Dict[str, Dict[str, Any]] = {
    "lethal_tempo": {
        "name": "Lethal Tempo",
        "slot": "keystone",
        "rewritten_in_7_3": True,
        "as_per_stack_melee": 0.08,
        "as_per_stack_ranged": 0.064,
        "max_stacks": 6,
        "duration": 6,
        "bolt_melee": [9, 30],
        "bolt_ranged": [6, 24],
        "bolt_as_amp_melee": 0.01,
        "bolt_as_amp_ranged": 0.0067,
        "notes": "No longer grants huge free AS/range. Scales with built AS.",
    },
    "conqueror": {
        "name": "Conqueror",
        "slot": "keystone",
        "ad_per_stack": [3, 5],
        "ap_per_stack": [5, 8.33],
        "notes": "AP ratio standardized to 1.667x AD.",
    },
    "legend_alacrity": {
        "name": "Legend: Alacrity",
        "slot": "legend",
        "as_cap": 0.15,
        "approx": True,
    },
    "legend_haste": {
        "name": "Legend: Haste",
        "slot": "legend",
        "new_in_7_3": True,
        "ah_cap": 15,
        "ah_per_stack": 1.5,
        "replaces": "Legend: Tenacity",
    },
    "cut_down": {
        "name": "Cut Down",
        "slot": "precision",
        "bonus_damage_vs_higher_hp": 0.08,
        "approx": True,
        "notes": "Used vs tanks. Exact WR curve is HP-diff based; sim uses 8% vs tanks, 0% vs equal squishy.",
    },
    "coup_de_grace": {
        "name": "Coup de Grace",
        "slot": "precision",
        "bonus_damage_below_40": 0.08,
        "approx": True,
    },
    "brutal": {
        "name": "Brutal",
        "slot": "domination",
        "onhit_phys": [12, 18],
        "approx": True,
        "notes": "Early auto bonus. Sim uses 15 physical on-hit.",
    },
}

# Varus kit — 7.3 live (base AD buffed; kit otherwise last touched 7.2).
VARUS: Dict[str, Any] = {
    "id": "varus",
    "name": "Varus",
    "roles": ["marksman", "mage"],
    "position": "dragon_lane",
    "range": 575,
    "move_speed": 340,
    "resource": "mana",
    "patch_7_3": {"base_ad": {"from": 54, "to": 58}},
    "stats": {
        "base_hp": 600,
        "hp_growth": 128,
        "base_ad": 58,
        "ad_growth": 4.0,
        "base_armor": 35,
        "armor_growth": 4.5,
        "base_mr": 30,
        "mr_growth": 1.4,
        "base_mana": 390,
        "mana_growth": 33,
        "as_ratio": 0.658,
        "base_as": 0.658,
        "base_bonus_as": 0.22,
        "as_growth": 0.03,
        "attack_range": 575,
    },
    "abilities": {
        "P": {
            "name": "Living Vengeance",
            "on_takedown_as": 0.55,
            "on_takedown_convert": 0.20,
            "on_minion_as": [0.20, 0.25, 0.30],
            "on_minion_convert": 0.10,
            "duration": [5, 7, 9, 11],
            "notes": "Convert is AD and AP = convert * bonus AS. Not baseline DPS.",
        },
        "Q": {
            "name": "Piercing Arrow",
            "max_rank": 4,
            "cd": [15, 14, 13, 12],
            "mana": [75, 80, 85, 90],
            "min_base": [80, 140, 200, 260],
            "min_ad": [1.10, 1.20, 1.30, 1.40],
            "charge_amp": 0.50,
            "notes": "Max damage = min * 1.5. Blight detonated by Q also * (1+charge_amp).",
        },
        "W": {
            "name": "Blighted Quiver",
            "max_rank": 4,
            "cd": [25, 25, 25, 25],
            "onhit_base": [15, 25, 35, 45],
            "onhit_ap": 0.35,
            "blight_max_stacks": 3,
            "blight_duration": 6,
            "blight_pct_maxhp": [0.03, 0.035, 0.04, 0.045],
            "blight_pct_per_100_ap": 0.012,
            "active_missing_hp": [0.06, 0.08, 0.10, 0.12],
            "active_charge_amp": 0.50,
            "cdr_per_stack": 0.13,
            "monster_cap_per_stack": 120,
        },
        "E": {
            "name": "Hail of Arrows",
            "max_rank": 4,
            "cd": [13, 12, 11, 10],
            "mana": 80,
            "base": [70, 115, 160, 205],
            "bonus_ad": 0.90,
            "slow": [0.25, 0.30, 0.35, 0.40],
            "grievous": 0.40,
            "ground_duration": 4,
            "cast_time": 0.35,
        },
        "R": {
            "name": "Chain of Corruption",
            "max_rank": 3,
            "cd": [75, 65, 55],
            "base": [150, 250, 350],
            "ap": 0.85,
            "root": 2.0,
            "applies_3_blight": True,
        },
    },
    "skill_orders": {
        "onhit": ["W", "Q", "E"],
        "crit": ["Q", "W", "E"],
    },
}


def load_champions() -> Dict[str, Any]:
    path = Path(__file__).parent / "champions.json"
    return json.loads(path.read_text(encoding="utf-8"))


def item(item_id: str) -> Dict[str, Any]:
    if item_id not in ITEMS:
        raise KeyError(f"Unknown 7.3 item id: {item_id}")
    return ITEMS[item_id]


def dump_json(out_dir: Optional[Path] = None) -> None:
    out_dir = out_dir or Path(__file__).parent
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "patch.json").write_text(
        json.dumps(
            {
                "patch": PATCH,
                "date": PATCH_DATE,
                "title": "Spotlight Moment / marksman overhaul",
                "system": SYSTEM,
                "sources": [
                    "https://wildrift.leagueoflegends.com/en-us/news/game-updates/wild-rift-patch-notes-7-3/",
                    "https://wrchina.gg/patch-notes/",
                    "https://www.wildriftfire.com/guide/varus",
                    "https://wiki.leagueoflegends.com/en-us/WR:Varus",
                ],
            },
            indent=2,
        )
        + "\n"
    )
    (out_dir / "items.json").write_text(json.dumps({"patch": PATCH, "items": ITEMS}, indent=2) + "\n")
    (out_dir / "runes.json").write_text(json.dumps({"patch": PATCH, "runes": RUNES}, indent=2) + "\n")
    (out_dir / "varus.json").write_text(json.dumps({"patch": PATCH, "champion": VARUS}, indent=2) + "\n")
    # Overlay Varus live stats onto the roster dump.
    champs = load_champions()
    champs["champions"].setdefault("Varus", {})
    champs["champions"]["Varus"]["stats"].update(VARUS["stats"])
    champs["champions"]["Varus"]["changes_7_3"]["base_ad"] = VARUS["patch_7_3"]["base_ad"]
    champs["champions"]["Varus"]["kit"] = "see varus.json"
    (out_dir / "champions.json").write_text(json.dumps(champs, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    dump_json()
    store = Path("/cursor/stores/self/wr-7.3")
    dump_json(store)
    print(f"dumped {len(ITEMS)} items, varus kit, {len(RUNES)} runes")
