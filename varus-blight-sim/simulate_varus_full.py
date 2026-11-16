#!/usr/bin/env python3
"""Finish Statikk + Hurricane + Guinsoo: the last two items, the rune page, the buy order.

The three named items stay. Boots, one lifesteal item, and Terminus fill the
other three slots. Level 15 uses the patch 7.3 base attack damage of 58.
A wave is 3 melee minions at 640 health and 3 casters at 340, with no resists.
Lifesteal heals basic attacks and physical on-hit effects against minions and
champions. Omnivamp heals everything, at one fifth against minions.
"""

from __future__ import annotations

import json
from pathlib import Path

from simulate_varus_blight import (
    BORK,
    BT,
    CARRY,
    ENERGY_MAX,
    GREAVES,
    GUINSOO,
    HURRICANE,
    RIFT,
    STATIKK,
    TERMINUS,
    VAMP,
    Mods,
    Target,
    fight,
)

HERE = Path(__file__).resolve().parent
CORE = [GREAVES, STATIKK, GUINSOO, HURRICANE]
MELEE = Target("melee", 640, 0, 0, minion=True)
CASTER = Target("caster", 340, 0, 0, minion=True)
WAVE = [MELEE, MELEE, MELEE, CASTER, CASTER, CASTER]
GROUP = [Target("tank", 4500, 220, 120), Target("bruiser", 3400, 140, 80), Target("carry", 2100, 70, 42)]

ALACRITY = Mods(bonus_as=0.18, lethal=True, brutal=True, cut_down=True, base_ad=58)
BLOODLINE = Mods(omnivamp=0.07, lethal=True, brutal=True, cut_down=True, base_ad=58)
CONQUEROR = Mods(bonus_as=0.18, conqueror=True, brutal=True, cut_down=True, base_ad=58)
BARE = Mods(base_ad=58)


def show(label: str, row) -> str:
    dead = " ".join(
        f"{name} {row.deaths[name]:.2f}s" for name in row.deaths if row.deaths[name] is not None
    )
    return (
        f"{label:<28} dmg {row.damage:>5}  heal {row.healed:>4}  "
        f"time {row.finished:>4}  autos {row.autos:>2}  Q {row.arrows}  {dead}"
    )


def main() -> None:
    lines = [
        "Varus full build, level 15, base AD 58.",
        "Core is Berserker's Greaves, Statikk Shiv, Guinsoo's Rageblade, Runaan's Hurricane.",
        "Wave is 3 melee at 640 health and 3 casters at 340. Group is tank, bruiser, carry.",
        "The grouped fight is 8 seconds with lightning ready. The wave is autos only.",
        "",
    ]

    builds = [
        ("BotRK + Terminus", CORE + [BORK, TERMINUS]),
        ("BotRK + Bloodthirster", CORE + [BORK, BT]),
        ("Bloodthirster + Terminus", CORE + [BT, TERMINUS]),
        ("Riftmaker + Terminus", CORE + [RIFT, TERMINUS]),
        ("BotRK, no sixth", CORE + [BORK]),
        ("Terminus, no lifesteal", CORE + [TERMINUS]),
    ]
    lines.append("FINISHED ITEMS, Lethal Tempo page (Bloodline, Brutal, Cut Down)")
    saved = {}
    for name, items in builds:
        group = fight(items, GROUP, 8.0, "poke", True, ENERGY_MAX, mods=BLOODLINE)
        wave = fight(items, WAVE, 20.0, "farm", True, ENERGY_MAX, mods=BLOODLINE)
        lines.append(show("group  " + name, group))
        lines.append(show("wave   " + name, wave))
        saved[name] = {
            "group_damage": group.damage,
            "group_heal": group.healed,
            "group_deaths": group.deaths,
            "wave_time": wave.finished,
            "wave_heal": wave.healed,
            "gold": group.gold,
        }
    lines.append("")
    lines.append("SAME SIX ITEMS (BotRK + Terminus), rune page changes")
    finished = CORE + [BORK, TERMINUS]
    pages = {"Alacrity": ALACRITY, "Bloodline": BLOODLINE, "Conqueror": CONQUEROR, "items only": BARE}
    for name, mods in pages.items():
        group = fight(finished, GROUP, 8.0, "poke", True, ENERGY_MAX, mods=mods)
        early = fight(finished, GROUP, 4.0, "poke", True, ENERGY_MAX, mods=mods)
        wave = fight(finished, WAVE, 20.0, "farm", True, ENERGY_MAX, mods=mods)
        lines.append(show("group  " + name, group))
        lines.append(show("4s     " + name, early))
        lines.append(show("wave   " + name, wave))
        saved["rune " + name] = {
            "group_damage": group.damage,
            "group_heal": group.healed,
            "four_damage": early.damage,
            "four_heal": early.healed,
            "wave_time": wave.finished,
            "wave_heal": wave.healed,
        }

    lines.append("")
    lines.append("BUY-ORDER CHECKPOINTS, autos on one wave, lightning ready")
    steps = [
        ("Scepter + boots", [GREAVES, VAMP]),
        ("Statikk + boots, no Scepter", [GREAVES, STATIKK]),
        ("Statikk + Scepter + boots", [GREAVES, STATIKK, VAMP]),
        ("Statikk + Guinsoo + Scepter", [GREAVES, STATIKK, GUINSOO, VAMP]),
        ("Core three, Scepter still held", CORE + [VAMP]),
        ("Core + BotRK", CORE + [BORK]),
        ("Core + BotRK + Terminus", finished),
    ]
    for name, items in steps:
        wave = fight(items, WAVE, 20.0, "farm", True, ENERGY_MAX, mods=BLOODLINE)
        lines.append(show(name, wave) + f"  gold {wave.gold}")
        saved["step " + name] = {"wave_time": wave.finished, "wave_heal": wave.healed, "gold": wave.gold}

    text = "\n".join(lines) + "\n"
    (HERE / "full-report.txt").write_text(text)
    (HERE / "full-results.json").write_text(json.dumps(saved, indent=2) + "\n")
    print(text)


if __name__ == "__main__":
    main()
