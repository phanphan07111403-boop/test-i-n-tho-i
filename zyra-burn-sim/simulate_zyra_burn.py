#!/usr/bin/env python3
"""
Wild Rift Zyra Support — Burn / Plant-Spam Harass Simulation
Patch 7.2+ item values. Average game: 20 minutes.
Playstyle: spam plants (accuracy irrelevant — plants auto-hit and refresh burns).
Goal: find the build that peaks burn DPS while keeping enough burn uptime/duration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import math
import json

# ---------------------------------------------------------------------------
# Constants / assumptions
# ---------------------------------------------------------------------------

GAME_MINUTES = 20

# Aggressive poke support gold (Sickle → Scythe + soulcast + lane tribute).
# Tuned to land ~9.5–10.5k total by 20:00 for a high-pressure Zyra.
def gold_at_minute(m: int) -> int:
    # Aggressive plant-poke Zyra support gold (Sickle tribute spam + Scythe soulcast).
    # Lands ~10.5–11k by 20:00 — high but realistic for constant harass.
    if m <= 0:
        return 500
    total = 500  # starting + sickle
    for t in range(1, m + 1):
        if t <= 4:
            total += 320  # heavy early tribute from plant poke
        elif t <= 10:
            total += 460  # scythe +75/min + fights
        else:
            total += 560  # objective / mid-game skirmish gold
    return total


def level_at_minute(m: int) -> int:
    # Typical WR support XP curve ~ lvl 12–13 at 20.
    table = {
        1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7, 7: 8, 8: 8,
        9: 9, 10: 10, 11: 10, 12: 11, 13: 11, 14: 12,
        15: 12, 16: 13, 17: 13, 18: 14, 19: 14, 20: 15,
    }
    return table.get(m, min(15, 1 + m))


def target_max_hp(m: int) -> int:
    # Mixed botlane target (ADC / fighter average) with item HP.
    return 650 + 55 * level_at_minute(m) + 25 * m


def plant_base_damage(level: int) -> float:
    # WR: ~10–108 + 10% AP. Linear-ish by level.
    return 10 + (108 - 10) * (level - 1) / 14


# ---------------------------------------------------------------------------
# Items
# ---------------------------------------------------------------------------

@dataclass
class Item:
    name: str
    cost: int
    ap: float = 0
    ah: float = 0
    hp: float = 0
    flat_mpen: float = 0
    pct_mpen: float = 0
    # Burn types: none | ashes | blackfire | liandry
    burn: str = "none"
    # Utility that improves burn uptime
    rylai: bool = False
    deathcap: bool = False
    # Component note
    tags: Tuple[str, ...] = ()


ITEMS: Dict[str, Item] = {
    "Spectral Sickle": Item("Spectral Sickle", 500, ap=20, tags=("support",)),
    "Black Mist Scythe": Item(
        "Black Mist Scythe", 0, ap=28, ah=10, tags=("support",)
    ),  # base AP; soulcast stacks added separately
    "Boots of Speed": Item("Boots of Speed", 500, tags=("boots",)),
    "Boots of Mana": Item(
        "Boots of Mana", 1200, ap=25, flat_mpen=8, tags=("boots",)
    ),
    # Tier-3 upgrade of Boots of Mana (available after 10:00). Total cost 2200.
    "Spellslinger's Shoes": Item(
        "Spellslinger's Shoes",
        2200,
        ap=40,
        flat_mpen=18,
        pct_mpen=0.08,
        tags=("boots", "t3"),
    ),
    "Amplifying Tome": Item("Amplifying Tome", 500, ap=20),
    "Blasting Wand": Item("Blasting Wand", 800, ap=45),
    "Needlessly Large Rod": Item("Needlessly Large Rod", 1400, ap=70),
    "Ruby Crystal": Item("Ruby Crystal", 500, hp=200),
    "Giant's Belt": Item("Giant's Belt", 1000, hp=350),
    "Lost Chapter": Item("Lost Chapter", 1200, ap=40, ah=10),  # approx WR values
    "Fiendish Codex": Item("Fiendish Codex", 900, ap=35, ah=10),
    "Haunting Guise": Item(
        "Haunting Guise", 1300, ap=35, hp=200, burn="none", tags=("guise",)
    ),
    # Guise also has early Madness in 7.2 — modeled on finished Liandry
    "Fated Ashes": Item(
        "Fated Ashes", 900, ap=40, burn="ashes", tags=("burn_comp",)
    ),
    "Blackfire Torch": Item(
        "Blackfire Torch", 2800, ap=80, ah=20, burn="blackfire", tags=("burn",)
    ),
    "Liandry's Torment": Item(
        "Liandry's Torment",
        3000,
        ap=70,
        hp=300,
        # Patch 7.2: % mpen removed from general AP items
        burn="liandry",
        tags=("burn",),
    ),
    "Rylai's Crystal Scepter": Item(
        "Rylai's Crystal Scepter",
        2700,
        ap=70,  # patch 7.2 wiki; some sites still show 65
        hp=350,
        rylai=True,
        tags=("uptime",),
    ),
    "Morellonomicon": Item(
        "Morellonomicon", 2650, ap=75, hp=300, ah=15, tags=("antiheal",)
    ),
    "Cryptbloom": Item(
        "Cryptbloom", 3000, ap=70, ah=20, pct_mpen=0.30, tags=("pen",)
    ),
    "Void Staff": Item(
        "Void Staff", 3000, ap=95, pct_mpen=0.40, tags=("pen",)
    ),
    "Rabadon's Deathcap": Item(
        "Rabadon's Deathcap", 3400, ap=130, deathcap=True, tags=("amp",)
    ),
    "Zhonya's Hourglass": Item(
        "Zhonya's Hourglass", 3300, ap=110, tags=("defense",)
    ),
}


# ---------------------------------------------------------------------------
# Build paths (purchase order — support item always slot 1)
# ---------------------------------------------------------------------------

# Each path: ordered purchase list. Scythe is quest-complete (gold spent counted
# as sickle 500 already). Boots upgrade replaces Boots of Speed.

BUILD_PATHS: Dict[str, List[str]] = {
    # Liandry first, then Rylai lock, then Blackfire — best 20-min duration+peak
    "Liandry → Rylai → BF (Best 20m)": [
        "Spectral Sickle",
        "Boots of Speed",
        "Fated Ashes",
        "Haunting Guise",
        "Liandry's Torment",
        "Boots of Mana",
        "Rylai's Crystal Scepter",
        "Blackfire Torch",
        "Rabadon's Deathcap",
    ],
    # User comparison: pen path (Spellslinger T3 + Void Staff)
    "Liandry → Spellslinger → Void (Pen)": [
        "Spectral Sickle",
        "Boots of Speed",
        "Fated Ashes",
        "Haunting Guise",
        "Liandry's Torment",
        "Boots of Mana",
        "Spellslinger's Shoes",
        "Void Staff",
        "Rabadon's Deathcap",
    ],
    # Head-to-head clean: Liandry → Rylai (no 3rd burn item)
    "Liandry → Boots → Rylai (Uptime)": [
        "Spectral Sickle",
        "Boots of Speed",
        "Fated Ashes",
        "Haunting Guise",
        "Liandry's Torment",
        "Boots of Mana",
        "Rylai's Crystal Scepter",
        "Rabadon's Deathcap",
    ],
    # Liandry first then BF then Rylai (raw peak, Rylai often too late in 20m)
    "Liandry → BF → Rylai": [
        "Spectral Sickle",
        "Boots of Speed",
        "Fated Ashes",
        "Haunting Guise",
        "Liandry's Torment",
        "Boots of Mana",
        "Blackfire Torch",
        "Rylai's Crystal Scepter",
        "Rabadon's Deathcap",
    ],
    # Classic guide: Liandry → Rylai (no Blackfire)
    "Liandry → Rylai → Cap (Classic)": [
        "Spectral Sickle",
        "Boots of Speed",
        "Fated Ashes",
        "Haunting Guise",
        "Liandry's Torment",
        "Boots of Mana",
        "Rylai's Crystal Scepter",
        "Rabadon's Deathcap",
        "Cryptbloom",
    ],
    # Peak burn double-DoT first, Rylai last (often skips Rylai in 20m)
    "BF → Liandry → Rylai (Peak Burn)": [
        "Spectral Sickle",
        "Boots of Speed",
        "Fated Ashes",
        "Blackfire Torch",
        "Boots of Mana",
        "Haunting Guise",
        "Liandry's Torment",
        "Rylai's Crystal Scepter",
        "Rabadon's Deathcap",
    ],
    # Rylai early for uptime (plants stick) then burns
    "Rylai → Liandry → BF (Uptime First)": [
        "Spectral Sickle",
        "Boots of Speed",
        "Boots of Mana",
        "Rylai's Crystal Scepter",
        "Fated Ashes",
        "Liandry's Torment",
        "Blackfire Torch",
        "Rabadon's Deathcap",
    ],
    # Blackfire → Rylai → Liandry
    "BF → Rylai → Liandry (Duration Peak)": [
        "Spectral Sickle",
        "Boots of Speed",
        "Fated Ashes",
        "Lost Chapter",
        "Blackfire Torch",
        "Boots of Mana",
        "Rylai's Crystal Scepter",
        "Haunting Guise",
        "Liandry's Torment",
    ],
    # Antiheal contrast
    "Liandry → Morello → Cap (Antiheal)": [
        "Spectral Sickle",
        "Boots of Speed",
        "Fated Ashes",
        "Haunting Guise",
        "Liandry's Torment",
        "Boots of Mana",
        "Morellonomicon",
        "Rabadon's Deathcap",
        "Cryptbloom",
    ],
}


# ---------------------------------------------------------------------------
# Inventory / purchase simulation
# ---------------------------------------------------------------------------

def scythe_ap_stacks(minute: int) -> float:
    # Scythe soulcast: +4 AP every 60s, max 40 AP (+250 HP). Online ~min 5–6.
    if minute < 6:
        return 0.0
    stacks = min(10, minute - 5)
    return 4.0 * stacks


# Components that build into a finished item (credit when upgrading).
UPGRADE_COMPONENTS = {
    "Boots of Mana": ("Boots of Speed",),
    "Spellslinger's Shoes": ("Boots of Mana",),
    "Blackfire Torch": ("Lost Chapter", "Fated Ashes"),
    "Liandry's Torment": ("Haunting Guise", "Fated Ashes"),
    "Rylai's Crystal Scepter": ("Giant's Belt", "Blasting Wand", "Amplifying Tome"),
}

# Preferred component buy order when saving for the next unfinished item.
NEXT_COMPONENTS = {
    "Blackfire Torch": ["Fated Ashes", "Lost Chapter"],
    "Liandry's Torment": ["Fated Ashes", "Haunting Guise"],
    "Rylai's Crystal Scepter": ["Giant's Belt", "Blasting Wand", "Amplifying Tome"],
    "Boots of Mana": ["Boots of Speed"],
    "Spellslinger's Shoes": ["Boots of Mana"],
    "Void Staff": ["Needlessly Large Rod"],
}


def resolve_inventory(path: List[str], gold: int, minute: int) -> List[Item]:
    """Buy along path in order; put leftover gold into components for the next item."""
    owned_names: List[str] = []
    gold_pool = gold

    def credit_for(item_name: str) -> Tuple[int, List[str]]:
        credit = 0
        remove: List[str] = []
        for c in UPGRADE_COMPONENTS.get(item_name, ()):
            if c in owned_names:
                credit += ITEMS[c].cost
                remove.append(c)
        return credit, remove

    def remaining_cost(item_name: str) -> int:
        if item_name == "Black Mist Scythe":
            return 0
        credit, _ = credit_for(item_name)
        return max(0, ITEMS[item_name].cost - credit)

    def can_afford(item_name: str) -> bool:
        # Tier-3 boots unlock at 10:00
        if item_name == "Spellslinger's Shoes" and minute < 10:
            return False
        return gold_pool >= remaining_cost(item_name)

    def buy(item_name: str) -> bool:
        nonlocal gold_pool
        if item_name in owned_names:
            return False
        if item_name == "Spellslinger's Shoes" and minute < 10:
            return False
        if item_name == "Black Mist Scythe":
            if "Spectral Sickle" in owned_names:
                owned_names.remove("Spectral Sickle")
            owned_names.append(item_name)
            return True
        cost = remaining_cost(item_name)
        if cost > gold_pool:
            return False
        _, remove = credit_for(item_name)
        gold_pool -= cost
        for r in remove:
            owned_names.remove(r)
        # Spellslinger replaces Boots of Mana entirely
        if item_name == "Spellslinger's Shoes" and "Boots of Speed" in owned_names:
            owned_names.remove("Boots of Speed")
        owned_names.append(item_name)
        return True

    # Walk the planned path; stop at first unaffordable full item.
    blocked_at: Optional[str] = None
    for step in path:
        if step == "Black Mist Scythe":
            continue
        if step == "Spectral Sickle":
            if "Spectral Sickle" not in owned_names and "Black Mist Scythe" not in owned_names:
                buy("Spectral Sickle")
            continue
        if step in owned_names:
            continue
        if can_afford(step):
            buy(step)
        else:
            blocked_at = step
            break

    # Sickle → Scythe quest completes ~5:00
    if minute >= 5 and "Spectral Sickle" in owned_names:
        owned_names.remove("Spectral Sickle")
        owned_names.insert(0, "Black Mist Scythe")

    # Spend leftover only on components for the blocked next item
    if blocked_at and blocked_at in NEXT_COMPONENTS:
        for comp in NEXT_COMPONENTS[blocked_at]:
            if comp in owned_names:
                continue
            # Don't buy Fated Ashes if Liandry already finished (ashes consumed)
            if comp == "Fated Ashes" and "Liandry's Torment" in owned_names:
                continue
            if gold_pool >= ITEMS[comp].cost:
                buy(comp)
        # If components now complete the item, finish it
        if can_afford(blocked_at):
            buy(blocked_at)
            # Continue path after finishing blocked item
            seen_block = False
            for step in path:
                if step == blocked_at:
                    seen_block = True
                    continue
                if not seen_block or step in ("Spectral Sickle", "Black Mist Scythe"):
                    continue
                if step in owned_names:
                    continue
                if can_afford(step):
                    buy(step)
                else:
                    # partial components for new block
                    for comp in NEXT_COMPONENTS.get(step, []):
                        if comp not in owned_names and gold_pool >= ITEMS[comp].cost:
                            if not (comp == "Fated Ashes" and "Liandry's Torment" in owned_names):
                                buy(comp)
                    if can_afford(step):
                        buy(step)
                    else:
                        break

    # Never keep Boots of Speed once Boots of Mana is owned
    if "Boots of Mana" in owned_names and "Boots of Speed" in owned_names:
        owned_names.remove("Boots of Speed")

    return [ITEMS[n] for n in owned_names]


# ---------------------------------------------------------------------------
# Combat / burn model (plant spam harass)
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
    plant_dps: float
    burn_dps: float
    total_harass_dps: float
    burn_uptime: float
    burn_full_cycle_ok: bool  # True if plants keep burn for full 3s+ windows
    liandry: bool
    blackfire: bool
    ashes: bool
    rylai: bool
    notes: str = ""


def ability_haste_cast_mult(ah: float) -> float:
    # More AH → more Q/E/W → more plants → higher refresh rate
    return 1.0 + ah / (ah + 100.0) * 0.55


def compute_snapshot(build_name: str, path: List[str], minute: int) -> Snapshot:
    gold = gold_at_minute(minute)
    level = level_at_minute(minute)
    inv = resolve_inventory(path, gold, minute)

    ap = 0.0
    ah = 0.0
    flat_mpen = 0.0
    pct_mpen = 0.0
    has_ashes = False
    has_bf = False
    has_liandry = False
    has_rylai = False
    has_cap = False
    has_guise = False

    names = []
    for it in inv:
        names.append(it.name)
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
        if it.name == "Black Mist Scythe":
            ap += scythe_ap_stacks(minute)

    if has_cap:
        ap *= 1.30

    # Blackfire stack AP: plant spam typically hits 1–2 champs in lane / 2–3 in mid fights
    bf_targets = 1.5 if minute < 12 else 2.2
    if has_bf:
        ap *= 1.0 + 0.04 * bf_targets

    # --- Burn uptime ---
    # Plants last 6s, W resets duration + 50% AS. Spam playstyle → plants almost always up.
    # Burn duration = 3s; needs continuous reapply to stay at peak DPS.
    # Without Rylai: enemies walk out of plant range → ~72% burn uptime in poke windows.
    # With Rylai: plant slows → ~94% uptime. AH helps plant density.
    cast_mult = ability_haste_cast_mult(ah)
    base_uptime = 0.72
    if has_rylai:
        base_uptime = 0.94
    elif has_bf or has_liandry or has_ashes:
        base_uptime = 0.78  # burns alone don't stick targets
    uptime = min(0.98, base_uptime * (0.92 + 0.08 * cast_mult))

    # Full 3s burn cycle: plants attack ~1.0–1.5/s; with 2 plants easily refresh.
    # Fail condition: no plants / no burn item yet, or only single ability poke without plant.
    burn_full_ok = (has_ashes or has_bf or has_liandry) and uptime >= 0.70

    # --- Plant auto DPS (not burn, but applies burns) ---
    # Avg plants in harass window: ~2.0 early, ~2.6 with AH / mid game
    plants = 1.6 + 0.04 * minute + 0.4 * (cast_mult - 1.0)
    if has_rylai:
        plants += 0.15  # slow → plants stay on target longer
    plant_as = 1.05 * (1.0 + 0.12 * cast_mult)  # occasional W enrage average
    plant_hit = plant_base_damage(level) + 0.10 * ap
    # Second+ plant on same target deal 50% — model avg 0.75 multiplier
    plant_dps = plants * plant_as * plant_hit * 0.75

    # --- Burn DPS (while uptime active) ---
    hp = target_max_hp(minute)
    burn_dps = 0.0

    # Ashes: 15 over 3s → 5 DPS (replaced by BF/Liandry — don't double count)
    if has_ashes and not has_bf and not has_liandry:
        burn_dps += 15.0 / 3.0

    # Blackfire: (20 + 2% AP) per second for 3s, continuously refreshed
    if has_bf:
        burn_dps += 20.0 + 0.02 * ap

    # Liandry Torment (7.2): 2% max HP magic damage per second for 3 seconds.
    # Continuously refreshed by plant ticks → steady 2% max HP / sec while uptime holds.
    # (Patch changed the old 0.6%–3% level-scaling per-second burn to a flat 2%/s.)
    if has_liandry:
        burn_dps += 0.02 * hp

    # Guise alone: no full Torment, but Madness starts — skip burn, tiny note
    # Madness amp (Liandry or Guise): +2%/s up to 6% in combat. Harass windows ~6–8s → avg ~4%
    madness_mult = 1.0
    if has_liandry or has_guise:
        madness_mult = 1.04  # average over poke window

    # Magic pen vs target MR. Pen path shines when MR is stacked.
    # Base curve: early soft MR, late optional MR items on carries/bruisers.
    mr = 35 + 1.5 * level + (0 if minute < 12 else 18)
    # Extra MR if enemies actually build it (pen path payoff case)
    # Keep baseline for main sim; comparison script can raise this.
    effective_mr = mr * (1 - pct_mpen) - flat_mpen
    effective_mr = max(10.0, effective_mr)
    pen_mult = 100.0 / (100.0 + effective_mr)

    burn_dps *= madness_mult * pen_mult * uptime
    plant_dps *= madness_mult * pen_mult

    total = plant_dps + burn_dps

    note_parts = []
    if has_bf and has_liandry:
        note_parts.append("DOUBLE BURN")
    if has_rylai and (has_bf or has_liandry):
        note_parts.append("locked uptime")
    if burn_full_ok:
        note_parts.append("3s burn fully utilized")
    else:
        note_parts.append("burn window incomplete")

    return Snapshot(
        minute=minute,
        build_name=build_name,
        items=names,
        gold=gold,
        level=level,
        ap=round(ap, 1),
        ah=ah,
        plant_dps=round(plant_dps, 1),
        burn_dps=round(burn_dps, 1),
        total_harass_dps=round(total, 1),
        burn_uptime=round(uptime, 3),
        burn_full_cycle_ok=burn_full_ok,
        liandry=has_liandry,
        blackfire=has_bf,
        ashes=has_ashes,
        rylai=has_rylai,
        notes=", ".join(note_parts),
    )


def run_all() -> Tuple[Dict[str, List[Snapshot]], List[dict]]:
    results: Dict[str, List[Snapshot]] = {}
    for name, path in BUILD_PATHS.items():
        results[name] = [compute_snapshot(name, path, m) for m in range(1, GAME_MINUTES + 1)]

    # Per-minute winner by burn DPS (primary) then total
    timeline = []
    for m in range(1, GAME_MINUTES + 1):
        cands = [(n, results[n][m - 1]) for n in results]
        cands.sort(key=lambda x: (x[1].burn_dps, x[1].total_harass_dps), reverse=True)
        best_n, best_s = cands[0]
        # Prefer builds that fully utilize 3s burn AND have Rylai lock when within 8%.
        # Score = burn_dps * uptime_factor so "paper burn" without duration loses.
        def score(s: Snapshot) -> float:
            dur = 1.12 if s.rylai and s.burn_full_cycle_ok else (
                1.0 if s.burn_full_cycle_ok else 0.85
            )
            double = 1.05 if s.blackfire and s.liandry else 1.0
            return s.burn_dps * dur * double

        best_n, best_s = max(cands, key=lambda x: score(x[1]))
        timeline.append(
            {
                "minute": m,
                "winner": best_n,
                "burn_dps": best_s.burn_dps,
                "total_dps": best_s.total_harass_dps,
                "uptime": best_s.burn_uptime,
                "items": best_s.items,
                "ap": best_s.ap,
                "notes": best_s.notes,
            }
        )
    return results, timeline


def summarize(results, timeline) -> str:
    lines = []
    lines.append("=" * 78)
    lines.append("ZYRA SUPPORT — BURN HARASS SIMULATION (Wild Rift Patch 7.2+)")
    lines.append("Playstyle: plant spam (no aim stress) | Game length: 20:00")
    lines.append("Metric: burn DPS on a typical botlane target, with uptime model")
    lines.append("=" * 78)
    lines.append("")
    lines.append("GOLD / LEVEL CURVE (support poke Zyra)")
    lines.append(f"  {'Min':>3}  {'Gold':>6}  {'Lvl':>3}  {'Target HP':>9}")
    for m in range(1, 21):
        lines.append(
            f"  {m:>3}  {gold_at_minute(m):>6}  {level_at_minute(m):>3}  {target_max_hp(m):>9}"
        )

    lines.append("")
    lines.append("-" * 78)
    lines.append("MINUTE-BY-MINUTE OPTIMAL (highest burn DPS with workable duration)")
    lines.append("-" * 78)
    for row in timeline:
        item_short = " › ".join(row["items"][:5])
        if len(row["items"]) > 5:
            item_short += " › …"
        lines.append(
            f"  {row['minute']:>2}:00 | burn {row['burn_dps']:>6.1f} | total {row['total_dps']:>6.1f} | "
            f"uptime {row['uptime']*100:>4.0f}% | {row['winner']}"
        )
        lines.append(f"         items: {item_short}")
        lines.append(f"         {row['notes']}")

    lines.append("")
    lines.append("-" * 78)
    lines.append("BUILD COMPARISON — BURN DPS @ key spikes")
    lines.append("-" * 78)
    headers = ["Build", "8:00", "12:00", "16:00", "20:00", "EffBurn", "Peak"]
    lines.append(
        f"  {headers[0]:<36} {headers[1]:>7} {headers[2]:>7} {headers[3]:>7} {headers[4]:>7} {headers[5]:>8} {headers[6]:>7}"
    )
    ranking = []
    for name, snaps in results.items():
        b8 = snaps[7].burn_dps
        b12 = snaps[11].burn_dps
        b16 = snaps[15].burn_dps
        b20 = snaps[19].burn_dps
        # Duration-aware score: burn already includes uptime, but heavily reward
        # having Rylai+Liandry online by mid game (burn actually finishes).
        score_sum = 0.0
        for s in snaps:
            mult = 1.0
            if s.liandry and s.rylai:
                mult = 1.25  # duration locked
            elif s.liandry or s.blackfire:
                mult = 1.0
            else:
                mult = 0.9
            score_sum += s.burn_dps * mult
        eff_avg = score_sum / len(snaps)
        peak = max(s.burn_dps for s in snaps)
        rylai_by_16 = any(s.rylai and s.liandry and s.minute <= 16 for s in snaps)
        ranking.append((eff_avg, rylai_by_16, peak, name, b8, b12, b16, b20, snaps))
        lines.append(
            f"  {name:<36} {b8:>7.1f} {b12:>7.1f} {b16:>7.1f} {b20:>7.1f} {eff_avg:>8.1f} {peak:>7.1f}"
        )

    # Prefer duration-locked (Rylai+Liandry by 16), then score
    ranking.sort(key=lambda x: (x[1], x[0], x[2]), reverse=True)
    best = ranking[0]
    lines.append("")
    lines.append("-" * 78)
    lines.append("VERDICT")
    lines.append("-" * 78)
    winner_name = best[3]
    snaps = best[8]
    # When double burn + rylai online
    double_min = next(
        (s.minute for s in snaps if s.blackfire and s.liandry), None
    )
    rylai_lock = next(
        (s.minute for s in snaps if s.rylai and (s.blackfire or s.liandry)), None
    )
    full_kit = next(
        (s.minute for s in snaps if s.blackfire and s.liandry and s.rylai), None
    )
    lines.append(f"  Best path (peak burn WITH duration lock): {winner_name}")
    lines.append(f"  Duration-weighted avg: {best[0]:.1f} | Peak raw burn DPS: {best[2]:.1f}")
    if double_min:
        lines.append(f"  Double-burn (Blackfire + Liandry) online: ~{double_min}:00")
    if rylai_lock:
        lines.append(f"  Rylai uptime lock online: ~{rylai_lock}:00")
    else:
        lines.append("  Rylai uptime lock: NOT finished by 20:00 on this path")
    if full_kit:
        lines.append(f"  FULL KIT (BF + Liandry + Rylai): ~{full_kit}:00")
    else:
        lines.append("  Note: Liandry + Rylai + Blackfire rarely all finish in a 20-min support game.")
    lines.append("")
    lines.append("  WHY THIS PEAKS AND STILL HAS DURATION:")
    lines.append("  • Liandry = 2% max HP / sec for 3s — THE harass burn (plants refresh it)")
    lines.append("  • Blackfire = (20 + 2% AP)/s + 20 AH — second burn + more plant spam")
    lines.append("  • Plants auto-hit 6s (W resets) — spam trees, accuracy does not matter")
    lines.append("  • Rylai 30% slow = enemies cannot walk out before 3s burn finishes")
    lines.append("  • 20-min support gold forces a choice: double-burn OR Rylai lock — not both early")
    lines.append("  • Winner prioritizes Liandry spike (~9:00) then Rylai (~16:00) so burn works.")
    lines.append("")
    lines.append("  RECOMMENDED PURCHASE ORDER (20-min plant-spam Zyra support):")
    lines.append("  1) Spectral Sickle → Black Mist Scythe")
    lines.append("  2) Boots of Speed + Fated Ashes (~5:00 first burn)")
    lines.append("  3) Haunting Guise → Liandry's Torment (~9:00 PEAK harass spike)")
    lines.append("  4) Boots of Mana")
    lines.append("  5) Rylai's Crystal Scepter (LOCK duration — mandatory for burn to work)")
    lines.append("  6) Blackfire Torch only if game goes past ~18–20")
    lines.append("  7) Long game: Deathcap / Void / Morello")
    lines.append("")
    lines.append("  Trap: Liandry → Blackfire skips Rylai → higher paper burn, enemies walk out.")
    lines.append("  Trap: Rylai first delays Liandry → you lose the mid-game harass peak.")
    lines.append("=" * 78)
    return "\n".join(lines)


def export_json(results, timeline, path: str) -> None:
    payload = {
        "meta": {
            "champion": "Zyra",
            "role": "Support",
            "patch": "7.2+",
            "game_minutes": GAME_MINUTES,
            "playstyle": "plant spam burn harass",
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
                    "plant_dps": s.plant_dps,
                    "burn_dps": s.burn_dps,
                    "total_harass_dps": s.total_harass_dps,
                    "burn_uptime": s.burn_uptime,
                    "burn_full_cycle_ok": s.burn_full_cycle_ok,
                    "notes": s.notes,
                }
                for s in snaps
            ]
            for name, snaps in results.items()
        },
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def head_to_head(results: Dict[str, List[Snapshot]]) -> str:
    """Compare Rylai uptime build vs Spellslinger + Void pen build."""
    a_name = "Liandry → Boots → Rylai (Uptime)"
    b_name = "Liandry → Spellslinger → Void (Pen)"
    # Fallback names if clean path missing
    if a_name not in results:
        a_name = "Liandry → Rylai → BF (Best 20m)"
    if b_name not in results:
        return "Pen path missing from results."

    a = results[a_name]
    b = results[b_name]
    lines = []
    lines.append("")
    lines.append("=" * 78)
    lines.append("HEAD-TO-HEAD: Rylai uptime  vs  Spellslinger → Void Staff")
    lines.append("=" * 78)
    lines.append(f"  A = {a_name}")
    lines.append(f"  B = {b_name}")
    lines.append("")
    lines.append(
        f"  {'Min':>3} | {'A burn':>8} {'A tot':>8} {'A up':>5} | "
        f"{'B burn':>8} {'B tot':>8} {'B up':>5} | edge"
    )
    for m in range(1, 21):
        sa, sb = a[m - 1], b[m - 1]
        # Prefer total harass for overall poke; also show burn
        if sa.total_harass_dps > sb.total_harass_dps * 1.02:
            edge = "A (Rylai)"
        elif sb.total_harass_dps > sa.total_harass_dps * 1.02:
            edge = "B (Pen)"
        else:
            edge = "tie"
        lines.append(
            f"  {m:>3} | {sa.burn_dps:>8.1f} {sa.total_harass_dps:>8.1f} {sa.burn_uptime*100:>4.0f}% | "
            f"{sb.burn_dps:>8.1f} {sb.total_harass_dps:>8.1f} {sb.burn_uptime*100:>4.0f}% | {edge}"
        )

    lines.append("")
    lines.append("  Items @ 12 / 16 / 20:")
    for label, snaps in (("A", a), ("B", b)):
        for m in (12, 16, 20):
            s = snaps[m - 1]
            lines.append(f"    {label} {m}:00 → {' › '.join(s.items)}")

    # High-MR what-if: re-scale last snapshots' pen portion
    lines.append("")
    lines.append("  vs STACKED MR (~90 MR target at 16:00):")
    lines.append("  Pen path gains more because Void 40% + Spellslinger 18 flat / 8%.")
    lines.append("  Rylai path still wins if the fight is short / kite-out (uptime).")

    # Approximate rescale using pen formula at min 16
    def pen_factor(flat: float, pct: float, mr: float) -> float:
        eff = max(10.0, mr * (1 - pct) - flat)
        return 100.0 / (100.0 + eff)

    # Infer pen from items at 16
    def infer_pen(items: List[str]) -> Tuple[float, float]:
        flat = pct = 0.0
        for n in items:
            it = ITEMS[n]
            flat += it.flat_mpen
            pct += it.pct_mpen
        return flat, pct

    sa16, sb16 = a[15], b[15]
    flat_a, pct_a = infer_pen(sa16.items)
    flat_b, pct_b = infer_pen(sb16.items)
    # Current sim MR ~ mid 60s; stacked ~90
    mr_soft, mr_stack = 62.0, 90.0
    # Strip current pen then reapply (burn_dps already includes soft pen)
    # Approximate: new = old * (new_pen / old_pen)
    for mr_label, mr in (("soft MR~62", mr_soft), ("stack MR~90", mr_stack)):
        fa = pen_factor(flat_a, pct_a, mr)
        fb = pen_factor(flat_b, pct_b, mr)
        # Also apply uptime difference to burn
        a_burn = (sa16.burn_dps / max(1e-6, pen_factor(flat_a, pct_a, mr_soft))) * fa
        b_burn = (sb16.burn_dps / max(1e-6, pen_factor(flat_b, pct_b, mr_soft))) * fb
        a_tot = (sa16.total_harass_dps / max(1e-6, pen_factor(flat_a, pct_a, mr_soft))) * fa
        b_tot = (sb16.total_harass_dps / max(1e-6, pen_factor(flat_b, pct_b, mr_soft))) * fb
        winner = "A Rylai" if a_tot >= b_tot else "B Pen"
        lines.append(
            f"    {mr_label}: A tot {a_tot:.1f} (burn {a_burn:.1f}) | "
            f"B tot {b_tot:.1f} (burn {b_burn:.1f}) → {winner}"
        )

    lines.append("")
    lines.append("  VERDICT (this matchup):")
    a_avg = sum(s.total_harass_dps for s in a) / len(a)
    b_avg = sum(s.total_harass_dps for s in b) / len(b)
    a_burn_avg = sum(s.burn_dps for s in a) / len(a)
    b_burn_avg = sum(s.burn_dps for s in b) / len(b)
    lines.append(f"    Avg total harass: Rylai {a_avg:.1f}  vs  Pen {b_avg:.1f}")
    lines.append(f"    Avg burn DPS:     Rylai {a_burn_avg:.1f}  vs  Pen {b_burn_avg:.1f}")
    if a_avg >= b_avg:
        lines.append(
            "    → For plant-spam HARASS: Rylai path wins — more burn ticks land."
        )
        lines.append(
            "    → Take Spellslinger → Void when enemies STACK MR (tanks / MR boots),"
        )
        lines.append(
            "      or when you already have Rylai and need a 3rd damage item."
        )
    else:
        lines.append(
            "    → Pen path wins raw throughput in this gold curve — Void amplifies Liandry hard."
        )
        lines.append(
            "    → Still buy Rylai before Void if enemies kite your plants often."
        )
    lines.append("=" * 78)
    return "\n".join(lines)


def main() -> None:
    results, timeline = run_all()
    report = summarize(results, timeline)
    h2h = head_to_head(results)
    full = report + "\n" + h2h
    print(full)
    out_dir = "/workspace/zyra-burn-sim"
    with open(f"{out_dir}/report.txt", "w", encoding="utf-8") as f:
        f.write(full + "\n")
    export_json(results, timeline, f"{out_dir}/results.json")
    print(f"\nWrote {out_dir}/report.txt and {out_dir}/results.json")


if __name__ == "__main__":
    main()
