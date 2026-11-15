#!/usr/bin/env python3
"""
Conqueror and spellvamp on the Blackfire Ryze build.

Phase Rush, Manaflow, Transcendence, Gathering Storm, Legend: Haste
is the comparison page. Conqueror replaces that keystone, so the page
also drops to one Sorcery rune. Spellvamp sources a Ryze can still hold
at six items are Legend: Bloodline, Conqueror's 5% omnivamp, and
Riftmaker.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
import json
from pathlib import Path

from simulate_ryze_haste import (
    BRUISER,
    CombatMods,
    SQUISHY,
    TANK,
    compute_stats,
    simulate,
)

OUT = Path(__file__).resolve().parent

BUILD = [
    "Spellslinger's Shoes",
    "Seraph's Embrace",
    "Rabadon's Deathcap",
    "Infinity Orb",
    "Void Staff",
    "Blackfire Torch",
]
RIFT_FOR_ORB = [
    "Spellslinger's Shoes",
    "Seraph's Embrace",
    "Rabadon's Deathcap",
    "Riftmaker",
    "Void Staff",
    "Blackfire Torch",
]
RIFT_FOR_BLACKFIRE = [
    "Spellslinger's Shoes",
    "Seraph's Embrace",
    "Rabadon's Deathcap",
    "Infinity Orb",
    "Void Staff",
    "Riftmaker",
]

# The shared item table still has Riftmaker at 80 AP. Patch 7.2 set it to 70.
RIFT_AP_FIX = -10.0


@dataclass
class Setup:
    name: str
    kind: str
    items: list[str]
    extra_ap: float
    extra_mana: float
    extra_ah: float
    mods: CombatMods


def _mods_for(setup: Setup, n_burn: int) -> tuple[object, CombatMods]:
    st = compute_stats(
        setup.items, n_burn=n_burn, extra_ap=setup.extra_ap,
        extra_mana=setup.extra_mana, extra_ah=setup.extra_ah,
    )
    mods = setup.mods
    if mods.conqueror:
        up = compute_stats(
            setup.items, n_burn=n_burn, extra_ap=setup.extra_ap + 1.0,
            extra_mana=setup.extra_mana, extra_ah=setup.extra_ah,
        )
        mods = replace(
            mods,
            q_per_ap=up.q_raw - st.q_raw,
            w_per_ap=up.w_raw - st.w_raw,
            e_per_ap=up.e_raw - st.e_raw,
            burn_per_ap=up.bf_dps - st.bf_dps,
        )
    return st, mods


def evaluate(setup: Setup) -> dict:
    burn = 3 if "Blackfire Torch" in setup.items else 0
    st1, m1 = _mods_for(setup, 1)
    st3, m3 = _mods_for(setup, burn)
    sq = simulate(st1, [SQUISHY], 12.0, stop_on_primary_death=True, mods=m1)
    br = simulate(st1, [BRUISER], 12.0, stop_on_primary_death=True, mods=m1)
    tk = simulate(st1, [TANK], 14.0, stop_on_primary_death=True, mods=m1)
    real = simulate(st3, [SQUISHY, BRUISER, TANK], 12.0, mods=m3)
    short = simulate(st3, [SQUISHY, BRUISER, TANK], 4.0, dummy=True, mods=m3)
    dummy = simulate(st3, [SQUISHY, BRUISER, TANK], 8.0, dummy=True, mods=m3)
    wipe = max(real.deaths.values()) if len(real.deaths) == 3 else 99.0
    return {
        "name": setup.name,
        "kind": setup.kind,
        "ap": round(st1.ap, 1),
        "mana": round(st1.max_mana),
        "ah": st1.ah,
        "ttk_squishy": sq.ttk if sq.ttk is not None else 99,
        "ttk_bruiser": br.ttk if br.ttk is not None else 99,
        "ttk_tank": tk.ttk if tk.ttk is not None else 99,
        "wipe": wipe,
        "heal_squishy": round(sq.healed),
        "heal_bruiser": round(br.healed),
        "heal_tank": round(tk.healed),
        "heal_team": round(real.healed),
        "team_damage": round(real.dealt),
        "dummy4": round(short.dealt),
        "heal4": round(short.healed),
        "dummy8": round(dummy.dealt),
        "heal8": round(dummy.healed),
        "single8": round(dummy.single_dealt),
        "aoe8": round(dummy.aoe_dealt),
        "conq_full": None if dummy.conq_full is None else round(dummy.conq_full, 2),
        "effective_pct": round(100.0 * dummy.healed / dummy.dealt, 2) if dummy.dealt else 0,
    }


def catalog() -> list[Setup]:
    rush = CombatMods(transcendence=True)
    pages = [
        Setup(
            "Phase Rush, Gathering Storm, Legend: Haste",
            "reference", BUILD, 40, 300, 25, rush,
        ),
        Setup(
            "Phase Rush page, Legend: Bloodline instead of Haste",
            "bloodline", BUILD, 40, 300, 10,
            replace(rush, omnivamp=0.07),
        ),
    ]
    for secondary, ap, mana, ah, trans, scorch in (
        ("Manaflow Band", 0, 300, 15, False, False),
        ("Transcendence", 0, 0, 25, True, False),
        ("Gathering Storm", 40, 0, 15, False, False),
        ("Absolute Focus", 40, 0, 15, False, False),
        ("Scorch", 0, 0, 15, False, True),
    ):
        pages.append(Setup(
            f"Conqueror, Battle Zeal, Cut Down, Legend: Haste + {secondary}",
            "conqueror", BUILD, ap, mana, ah,
            CombatMods(
                phase_rush=False, conqueror=True, transcendence=trans,
                battle_zeal=True, cut_down=True, scorch=scorch,
            ),
        ))
    pages.append(Setup(
        "Conqueror, Battle Zeal, Cut Down, Bloodline + Gathering Storm",
        "conqueror-vamp", BUILD, 40, 0, 0,
        CombatMods(
            phase_rush=False, conqueror=True, battle_zeal=True,
            cut_down=True, omnivamp=0.07,
        ),
    ))
    rift = replace(rush, magic_vamp=0.11, rift_omnivamp=0.06)
    pages.append(Setup(
        "Phase Rush page, Riftmaker instead of Infinity Orb",
        "rift-orb", RIFT_FOR_ORB, 40 + RIFT_AP_FIX, 300, 25, rift,
    ))
    pages.append(Setup(
        "Phase Rush page, Riftmaker instead of Blackfire Torch",
        "rift-blackfire", RIFT_FOR_BLACKFIRE, 40 + RIFT_AP_FIX, 300, 25, rift,
    ))
    pages.append(Setup(
        "Bloodline and Riftmaker instead of Infinity Orb",
        "both", RIFT_FOR_ORB, 40 + RIFT_AP_FIX, 300, 10,
        replace(rift, omnivamp=0.07),
    ))
    return pages


def _time(seconds: float) -> str:
    if seconds >= 90:
        return "no kill"
    return f"{seconds:.2f}s"


def render(rows: list[dict]) -> str:
    base = next(r for r in rows if r["kind"] == "reference")
    lines = []
    w = lines.append
    w("=" * 78)
    w("RYZE — CONQUEROR AND SPELLVAMP ON THE BLACKFIRE BUILD")
    w("Spellslinger · Seraph · Deathcap · Infinity Orb · Void · Blackfire")
    w("Level 15. Ryze is ranged, so Conqueror heals at 5%, not the melee 9%.")
    w("=" * 78)
    w("")
    w("COMPARISON PAGE")
    w(f"  {base['name']}")
    w(f"  {base['ap']:.0f} AP · {base['ah']:.0f} AH · squishy {_time(base['ttk_squishy'])} · "
      f"bruiser {_time(base['ttk_bruiser'])} · tank {_time(base['ttk_tank'])} · "
      f"wipe {_time(base['wipe'])}")
    aoe = base["aoe8"] / (base["aoe8"] + base["single8"])
    w(f"  4s clump {base['dummy4']} · 8s clump {base['dummy8']} · healing 0")
    w(f"  {aoe:.0%} of that damage is area: Flux Overload, the Spell Flux spread, and the burn.")
    w("  The 4-second total is the fight this build actually has. The 8-second")
    w("  total is only there to show a fight that runs long enough for stacks.")
    w("")
    w(f"{'Page':<62} {'4s dmg':>7} {'4s heal':>7} {'wipe':>7}")
    for row in rows:
        w(f"{row['name']:<62} {row['dummy4']:7d} {row['heal4']:7d} "
          f"{_time(row['wipe']):>7}")
    w("")
    w("-" * 78)
    w("HEALING ON REAL KILLS, AND WHAT THE 4 SECONDS COST")
    w("-" * 78)
    for row in rows:
        if row["kind"] == "reference":
            continue
        lost = base["dummy4"] - row["dummy4"]
        rate = "4s damage is higher" if lost <= 0 else f"{row['heal4'] / lost:.2f} healed per 1 damage given up over 4s"
        w(f"  {row['name']}")
        w(f"    4s damage {row['dummy4']} ({-lost:+d}) · 4s heal {row['heal4']} · "
          f"8s heal {row['heal8']} ({row['effective_pct']:.1f}% of the 8s damage)")
        w(f"    Carry kill heals {row['heal_squishy']} · bruiser {row['heal_bruiser']} · "
          f"tank {row['heal_tank']} · the real teamfight heals {row['heal_team']}")
        w(f"    Kill clock: squishy {_time(row['ttk_squishy'])} · "
          f"bruiser {_time(row['ttk_bruiser'])} · tank {_time(row['ttk_tank'])} · "
          f"wipe {_time(row['wipe'])}")
        if row["conq_full"] is not None:
            w(f"    Conqueror reaches 6 stacks at {row['conq_full']:.2f}s")
        w(f"    {rate}")
        w("")
    w("-" * 78)
    w("ASSUMPTIONS")
    w("-" * 78)
    w("  Conqueror at level 15 is 8.33 AP per stack, 50 AP at 6 stacks, before")
    w("  Deathcap. One stack per spell cast. The spell deals damage with the")
    w("  stacks it was cast on, then the new stack can heal that hit. Stacks")
    w("  fall off after 6 seconds without a hit. Ryze's combo reaches 6 stacks")
    w("  on the sixth cast, which is after the squishy is already dead.")
    w("  Taking Conqueror makes Precision the main tree. The other three runes")
    w("  here are Battle Zeal, Cut Down, and Legend: Haste, plus one Sorcery rune.")
    w("  Manaflow, Transcendence, and Gathering Storm cannot all stay.")
    w("  Legend: Bloodline is 7% omnivamp from the first point of damage.")
    w("  Omnivamp heals the full amount of champion damage, including area")
    w("  spells and the Blackfire burn. It does not heal more against minions.")
    w("  Riftmaker is the 7.2 version: 70 AP, 15 haste, 350 health, 11% magic")
    w("  vamp, and 2% of bonus health as AP. Void Corruption still ramps to 8%")
    w("  damage and, at 4 seconds, adds 6% omnivamp because Ryze is ranged.")
    w("  Magic vamp is the spellvamp stat. Area damage heals at one third:")
    w("  Flux Overload, the Spell Flux spread, and the burn. The first Spell")
    w("  Flux hit and a raw Overload heal at the full 11%.")
    w("  The shared item table still lists Riftmaker at 80 AP. This run uses 70.")
    w("  Hextech Gunblade was removed. Gluttonous Greaves are a component boot,")
    w("  not a sixth item. Blade of the Ruined King is omnivamp on an attack")
    w("  item, so it is not a spellvamp source for this build. Triumph heals")
    w("  on a takedown. It is not vamp.")
    w("")
    return "\n".join(lines)


def main() -> None:
    check = compute_stats(BUILD, n_burn=3)
    dealt = simulate(check, [SQUISHY, BRUISER, TANK], 4.0, dummy=True).dealt
    if round(dealt) != 20664:
        raise SystemExit(f"baseline clump changed: {dealt}")
    rows = [evaluate(s) for s in catalog()]
    text = render(rows)
    (OUT / "vamp-report.txt").write_text(text)
    (OUT / "vamp-results.json").write_text(json.dumps(rows, indent=2))
    print(text)


if __name__ == "__main__":
    main()
