#!/usr/bin/env python3
"""
Zyra Support — Pen path order sim (21 minutes)
Build 1: Liandry → Boots of Mana → Spellslinger → Void Amethyst → Void Staff
Build 2: Liandry → Boots of Mana → Void Amethyst → Void Staff → Spellslinger

Enemy team MR profiles: 0 tank / 1 tank / 2 tanks
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import json

GAME_MINUTES = 21


def gold_at(m: int) -> int:
    total = 500
    for t in range(1, m + 1):
        if t <= 4:
            total += 320
        elif t <= 10:
            total += 460
        else:
            total += 560
    return total


def level_at(m: int) -> int:
    table = {
        1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7, 7: 8, 8: 8,
        9: 9, 10: 10, 11: 10, 12: 11, 13: 11, 14: 12,
        15: 12, 16: 13, 17: 13, 18: 14, 19: 14, 20: 15, 21: 15,
    }
    return table.get(m, min(15, 1 + m))


def scythe_ap(m: int) -> float:
    if m < 6:
        return 0.0
    return 4.0 * min(10, m - 5)


@dataclass
class Item:
    name: str
    cost: int
    ap: float = 0
    ah: float = 0
    hp: float = 0
    flat_mpen: float = 0
    pct_mpen: float = 0
    burn: str = "none"  # none | ashes | liandry


ITEMS: Dict[str, Item] = {
    "Spectral Sickle": Item("Spectral Sickle", 500, ap=20),
    "Black Mist Scythe": Item("Black Mist Scythe", 0, ap=28, ah=10),
    "Boots of Speed": Item("Boots of Speed", 500),
    "Boots of Mana": Item("Boots of Mana", 1200, ap=25, flat_mpen=8),
    "Spellslinger's Shoes": Item(
        "Spellslinger's Shoes", 2200, ap=40, flat_mpen=18, pct_mpen=0.08
    ),
    "Amplifying Tome": Item("Amplifying Tome", 500, ap=20),
    "Fated Ashes": Item("Fated Ashes", 900, ap=40, burn="ashes"),
    "Haunting Guise": Item("Haunting Guise", 1300, ap=35, hp=200),
    "Liandry's Torment": Item(
        "Liandry's Torment", 3000, ap=70, hp=300, burn="liandry"
    ),
    "Void Amethyst": Item("Void Amethyst", 1000, ap=20, pct_mpen=0.10),
    "Needlessly Large Rod": Item("Needlessly Large Rod", 1400, ap=70),
    "Void Staff": Item("Void Staff", 3000, ap=95, pct_mpen=0.40),
}

# Credit when upgrading
UPGRADE = {
    "Boots of Mana": ("Boots of Speed",),
    "Spellslinger's Shoes": ("Boots of Mana",),
    "Liandry's Torment": ("Haunting Guise", "Fated Ashes"),
    "Void Staff": ("Void Amethyst", "Needlessly Large Rod"),
}

NEXT = {
    "Boots of Mana": ["Boots of Speed"],
    "Spellslinger's Shoes": ["Boots of Mana"],
    "Liandry's Torment": ["Fated Ashes", "Haunting Guise"],
    "Void Staff": ["Void Amethyst", "Needlessly Large Rod"],
    "Void Amethyst": ["Amplifying Tome"],
}

BUILD1 = [
    "Spectral Sickle",
    "Boots of Speed",
    "Fated Ashes",
    "Haunting Guise",
    "Liandry's Torment",
    "Boots of Mana",
    "Spellslinger's Shoes",
    "Void Amethyst",
    "Needlessly Large Rod",
    "Void Staff",
]

BUILD2 = [
    "Spectral Sickle",
    "Boots of Speed",
    "Fated Ashes",
    "Haunting Guise",
    "Liandry's Torment",
    "Boots of Mana",
    "Void Amethyst",
    "Needlessly Large Rod",
    "Void Staff",
    "Spellslinger's Shoes",
]

BUILDS = {
    "B1: Liandry→Mana→Spellslinger→Amethyst→Void": BUILD1,
    "B2: Liandry→Mana→Amethyst→Void→Spellslinger": BUILD2,
}


# ---------------------------------------------------------------------------
# Enemy MR / HP profiles by tank count
# ---------------------------------------------------------------------------

@dataclass
class TargetProfile:
    name: str
    # Typical primary burn target for Zyra poke / frontline
    description: str


def target_stats(tank_count: int, minute: int, level: int) -> Tuple[float, float, str]:
    """Return (max_hp, mr, label) for the main target Zyra burns."""
    # Squishy baseline (ADC / mage)
    squish_hp = 620 + 52 * level + 18 * minute
    squish_mr = 32 + 1.4 * level + (8 if minute >= 14 else 0)

    # Tank baseline (Ornn/Sion/Malphite style + MR items mid/late)
    tank_hp = 850 + 95 * level + 55 * minute
    tank_mr = 38 + 2.2 * level + (25 if minute >= 10 else 0) + (35 if minute >= 16 else 0)

    if tank_count == 0:
        # Burn ADC / mid — no dedicated tank
        return squish_hp, squish_mr, "squishy (no tank)"
    if tank_count == 1:
        # Frontline soaks plants — burn the tank often
        # Blend: 70% tank / 30% squishy exposure in fights
        hp = 0.70 * tank_hp + 0.30 * squish_hp
        mr = 0.70 * tank_mr + 0.30 * squish_mr
        return hp, mr, "1-tank mix (mostly frontline)"
    # 2 tanks — almost always hitting MR stacks
    hp = 0.85 * tank_hp + 0.15 * squish_hp
    mr = 0.85 * tank_mr + 0.15 * squish_mr + (10 if minute >= 14 else 0)
    return hp, mr, "2-tank heavy frontline"


def resolve_inventory(path: List[str], gold: int, minute: int) -> List[str]:
    owned: List[str] = []
    pool = gold

    def credit(name: str) -> Tuple[int, List[str]]:
        c, rem = 0, []
        for x in UPGRADE.get(name, ()):
            if x in owned:
                c += ITEMS[x].cost
                rem.append(x)
        return c, rem

    def remaining(name: str) -> int:
        if name == "Black Mist Scythe":
            return 0
        c, _ = credit(name)
        return max(0, ITEMS[name].cost - c)

    def can(name: str) -> bool:
        if name == "Spellslinger's Shoes" and minute < 10:
            return False
        return pool >= remaining(name)

    def buy(name: str) -> bool:
        nonlocal pool
        if name in owned:
            return False
        if name == "Spellslinger's Shoes" and minute < 10:
            return False
        if name == "Black Mist Scythe":
            if "Spectral Sickle" in owned:
                owned.remove("Spectral Sickle")
            owned.append(name)
            return True
        cost = remaining(name)
        if cost > pool:
            return False
        _, rem = credit(name)
        pool -= cost
        for r in rem:
            owned.remove(r)
        if name == "Spellslinger's Shoes" and "Boots of Speed" in owned:
            owned.remove("Boots of Speed")
        owned.append(name)
        return True

    blocked: Optional[str] = None
    for step in path:
        if step == "Black Mist Scythe":
            continue
        if step == "Spectral Sickle":
            if "Spectral Sickle" not in owned and "Black Mist Scythe" not in owned:
                buy(step)
            continue
        if step in owned:
            continue
        if can(step):
            buy(step)
        else:
            blocked = step
            break

    if minute >= 5 and "Spectral Sickle" in owned:
        owned.remove("Spectral Sickle")
        owned.insert(0, "Black Mist Scythe")

    if blocked and blocked in NEXT:
        for comp in NEXT[blocked]:
            if comp not in owned and pool >= ITEMS[comp].cost:
                # don't buy ashes if Liandry done
                if comp == "Fated Ashes" and "Liandry's Torment" in owned:
                    continue
                buy(comp)
        if can(blocked):
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
                if can(step):
                    buy(step)
                else:
                    for comp in NEXT.get(step, []):
                        if comp not in owned and pool >= ITEMS[comp].cost:
                            if not (
                                comp == "Fated Ashes"
                                and "Liandry's Torment" in owned
                            ):
                                buy(comp)
                    if can(step):
                        buy(step)
                    else:
                        break

    if "Boots of Mana" in owned and "Boots of Speed" in owned:
        owned.remove("Boots of Speed")
    if "Spellslinger's Shoes" in owned and "Boots of Mana" in owned:
        owned.remove("Boots of Mana")
    if "Void Staff" in owned and "Void Amethyst" in owned:
        owned.remove("Void Amethyst")
    if "Void Staff" in owned and "Needlessly Large Rod" in owned:
        owned.remove("Needlessly Large Rod")

    return owned


@dataclass
class Row:
    minute: int
    build: str
    tanks: int
    items: List[str]
    ap: float
    flat_mpen: float
    pct_mpen: float
    target_hp: float
    target_mr: float
    pen_mult: float
    plant_dps: float
    ability_dps: float
    burn_dps: float
    total_dps: float
    notes: str


def plant_base(level: int) -> float:
    return 10 + (108 - 10) * (level - 1) / 14


def compute(build_name: str, path: List[str], minute: int, tanks: int) -> Row:
    gold = gold_at(minute)
    level = level_at(minute)
    names = resolve_inventory(path, gold, minute)

    ap = ah = flat = pct = 0.0
    has_ashes = has_liandry = has_guise = False
    for n in names:
        it = ITEMS[n]
        ap += it.ap
        ah += it.ah
        flat += it.flat_mpen
        pct += it.pct_mpen
        if it.burn == "ashes":
            has_ashes = True
        if it.burn == "liandry":
            has_liandry = True
        if n == "Haunting Guise":
            has_guise = True
        if n == "Black Mist Scythe":
            ap += scythe_ap(minute)

    # % mpen does not stack additively beyond items — Void Staff replaces Amethyst
    # (Amethyst consumed). Spellslinger 8% stacks with Void 40% → 48% total.
    pct = min(pct, 0.55)  # soft cap sanity

    hp, mr, tlabel = target_stats(tanks, minute, level)
    eff_mr = max(8.0, mr * (1.0 - pct) - flat)
    pen_mult = 100.0 / (100.0 + eff_mr)

    cast_mult = 1.0 + ah / (ah + 100) * 0.5
    plants = 1.7 + 0.035 * minute + 0.35 * (cast_mult - 1)
    plant_as = 1.05 * (1.0 + 0.1 * cast_mult)
    plant_hit = plant_base(level) + 0.10 * ap
    plant_dps = plants * plant_as * plant_hit * 0.75 * pen_mult

    # Ability poke DPS: Q primary + occasional E
    w_rank = min(3, max(0, (level + 1) // 2 - 1))
    q_dmg = [60, 115, 170, 225][min(3, max(0, level // 3))] + 0.60 * ap
    # crude rank by level
    q_lvl = min(3, max(0, (level - 1) // 3))
    q_dmg = [60, 115, 170, 225][q_lvl] + 0.60 * ap
    e_lvl = min(3, max(0, (level - 2) // 4))
    e_dmg = [60, 100, 140, 180][e_lvl] + 0.40 * ap
    q_cd = (8 - q_lvl * 0.5) / cast_mult
    e_cd = 12.0 / cast_mult
    ability_dps = (q_dmg / q_cd + 0.55 * e_dmg / e_cd) * pen_mult

    # Burn
    burn = 0.0
    if has_ashes and not has_liandry:
        burn += 15.0 / 3.0
    if has_liandry:
        # 2% max HP per second while burning (7.2); plant refresh → high uptime
        burn += 0.02 * hp
    uptime = 0.78 if has_liandry or has_ashes else 0.0
    madness = 1.04 if (has_liandry or has_guise) else 1.0
    burn_dps = burn * uptime * madness * pen_mult

    plant_dps *= madness
    ability_dps *= madness
    total = plant_dps + ability_dps + burn_dps

    notes = []
    if has_liandry:
        notes.append("Liandry")
    if any(n == "Spellslinger's Shoes" for n in names):
        notes.append("Spellslinger")
    if any(n == "Void Amethyst" for n in names):
        notes.append("Amethyst 10%")
    if any(n == "Void Staff" for n in names):
        notes.append("Void 40%")
    notes.append(tlabel)

    return Row(
        minute=minute,
        build=build_name,
        tanks=tanks,
        items=names,
        ap=round(ap, 1),
        flat_mpen=flat,
        pct_mpen=pct,
        target_hp=round(hp),
        target_mr=round(mr, 1),
        pen_mult=round(pen_mult, 3),
        plant_dps=round(plant_dps, 1),
        ability_dps=round(ability_dps, 1),
        burn_dps=round(burn_dps, 1),
        total_dps=round(total, 1),
        notes=", ".join(notes),
    )


def main() -> None:
    # results[build][tanks] = list of rows
    results: Dict[str, Dict[int, List[Row]]] = {}
    for bname, path in BUILDS.items():
        results[bname] = {}
        for tanks in (0, 1, 2):
            results[bname][tanks] = [
                compute(bname, path, m, tanks) for m in range(1, GAME_MINUTES + 1)
            ]

    lines = []
    lines.append("=" * 80)
    lines.append("ZYRA SUPPORT — PEN ORDER SIM (to 21:00)")
    lines.append("B1: Liandry → Boots of Mana → Spellslinger → Void Amethyst → Void Staff")
    lines.append("B2: Liandry → Boots of Mana → Void Amethyst → Void Staff → Spellslinger")
    lines.append("Targets: 0 tank / 1 tank / 2 tanks (MR + HP profiles)")
    lines.append("=" * 80)

    # Item timeline (same across tank counts)
    lines.append("")
    lines.append("-" * 80)
    lines.append("ITEM TIMELINE (by gold)")
    lines.append("-" * 80)
    for bname, path in BUILDS.items():
        lines.append(f"  {bname}")
        prev = []
        for m in range(1, GAME_MINUTES + 1):
            items = results[bname][0][m - 1].items
            if items != prev:
                lines.append(f"    {m:>2}:00  gold {gold_at(m):>5}  → {' › '.join(items)}")
                prev = list(items)

    # Head-to-head tables per tank count
    for tanks in (0, 1, 2):
        lines.append("")
        lines.append("=" * 80)
        lines.append(f"DAMAGE DPS — {tanks} TANK TEAM")
        lines.append("=" * 80)
        lines.append(
            f"  {'Min':>3} | {'B1 tot':>7} {'B1 burn':>7} {'B1 MR':>5} | "
            f"{'B2 tot':>7} {'B2 burn':>7} {'B2 MR':>5} | edge"
        )
        b1 = results[list(BUILDS.keys())[0]][tanks]
        b2 = results[list(BUILDS.keys())[1]][tanks]
        wins = {"B1": 0, "B2": 0, "tie": 0}
        for m in range(1, GAME_MINUTES + 1):
            r1, r2 = b1[m - 1], b2[m - 1]
            if r1.total_dps > r2.total_dps * 1.02:
                edge, wins["B1"] = "B1", wins["B1"] + 1
            elif r2.total_dps > r1.total_dps * 1.02:
                edge, wins["B2"] = "B2", wins["B2"] + 1
            else:
                edge, wins["tie"] = "tie", wins["tie"] + 1
            lines.append(
                f"  {m:>3} | {r1.total_dps:>7.1f} {r1.burn_dps:>7.1f} {r1.target_mr:>5.0f} | "
                f"{r2.total_dps:>7.1f} {r2.burn_dps:>7.1f} {r2.target_mr:>5.0f} | {edge}"
            )
        avg1 = sum(r.total_dps for r in b1) / len(b1)
        avg2 = sum(r.total_dps for r in b2) / len(b2)
        lines.append(
            f"  Avg total DPS: B1 {avg1:.1f}  |  B2 {avg2:.1f}  |  "
            f"minute-wins B1:{wins['B1']} B2:{wins['B2']} tie:{wins['tie']}"
        )
        # Key spikes
        for label, m in (("12:00", 12), ("16:00", 16), ("21:00", 21)):
            r1, r2 = b1[m - 1], b2[m - 1]
            lines.append(
                f"  @{label}: B1 items={r1.items} | tot {r1.total_dps} "
                f"(pen {r1.pct_mpen*100:.0f}%+{r1.flat_mpen:.0f} flat, mult {r1.pen_mult})"
            )
            lines.append(
                f"           B2 items={r2.items} | tot {r2.total_dps} "
                f"(pen {r2.pct_mpen*100:.0f}%+{r2.flat_mpen:.0f} flat, mult {r2.pen_mult})"
            )

    # Verdict
    lines.append("")
    lines.append("=" * 80)
    lines.append("VERDICT")
    lines.append("=" * 80)
    for tanks in (0, 1, 2):
        b1 = results[list(BUILDS.keys())[0]][tanks]
        b2 = results[list(BUILDS.keys())[1]][tanks]
        avg1 = sum(r.total_dps for r in b1) / len(b1)
        avg2 = sum(r.total_dps for r in b2) / len(b2)
        late1 = sum(r.total_dps for r in b1[15:]) / 6  # 16–21
        late2 = sum(r.total_dps for r in b2[15:]) / 6
        winner = "B1 (Spellslinger before Void)" if avg1 >= avg2 else "B2 (Void before Spellslinger)"
        lines.append(
            f"  {tanks} tank: avg B1 {avg1:.1f} vs B2 {avg2:.1f} → {winner}"
        )
        lines.append(
            f"           late(16–21) B1 {late1:.1f} vs B2 {late2:.1f}"
        )

    lines.append("")
    lines.append("  How to read:")
    lines.append("  • B1 gets flat+%% pen earlier (Spellslinger @10+) → better mid spike on squishies.")
    lines.append("  • B2 finishes Void Staff sooner → bigger %% pen vs tanks once online.")
    lines.append("  • Vs 2 tanks, earlier Void (B2) usually wins once Amethyst/Void complete.")
    lines.append("  • Vs 0 tanks, Spellslinger-first (B1) often wins mid game before Void.")
    lines.append("=" * 80)

    text = "\n".join(lines)
    print(text)
    out = "/workspace/zyra-burn-sim"
    with open(f"{out}/pen_order_21m_report.txt", "w", encoding="utf-8") as f:
        f.write(text + "\n")

    payload = {
        "builds": {
            bname: {
                str(tanks): [
                    {
                        "minute": r.minute,
                        "items": r.items,
                        "ap": r.ap,
                        "flat_mpen": r.flat_mpen,
                        "pct_mpen": r.pct_mpen,
                        "target_hp": r.target_hp,
                        "target_mr": r.target_mr,
                        "pen_mult": r.pen_mult,
                        "plant_dps": r.plant_dps,
                        "ability_dps": r.ability_dps,
                        "burn_dps": r.burn_dps,
                        "total_dps": r.total_dps,
                        "notes": r.notes,
                    }
                    for r in rows
                ]
                for tanks, rows in by_tank.items()
            }
            for bname, by_tank in results.items()
        }
    }
    with open(f"{out}/pen_order_21m_results.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print(f"\nWrote {out}/pen_order_21m_report.txt and pen_order_21m_results.json")


if __name__ == "__main__":
    main()
