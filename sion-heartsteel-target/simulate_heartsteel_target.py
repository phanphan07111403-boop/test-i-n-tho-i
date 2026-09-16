#!/usr/bin/env python3
"""Wild Rift Sion Heartsteel: targeting policy comparison.

Heartsteel (WR ~6.0+ Colossal Consumption):
  Charge 2.5s while a champion is within 700 range (per target, up to 6 stacks).
  Next *basic attack* on a fully stacked champion consumes the mark:
    damage = 140 + 3.5% max HP
    bonus HP = 15% of that damage
  20s cooldown *per unique champion*.

No in-game targeting mode reads that mark. Auto-attack priority
(closest / lowest HP / lowest HP%) only looks at range and health.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

CHARGE_S = 2.5
PER_TARGET_CD = 20.0
SWITCH_AA_S = 1.2  # walk + one basic attack onto a locked champion
FIGHT_S = 40.0
START_HP = 3200.0  # Sion ~Heartsteel + belt/kindlegem + levels, pre-stacks
PATCH = "WR 6.0+"

ENEMIES = ("tank", "bruiser", "mid", "adc", "sup")


def proc_damage(sion_hp: float) -> float:
    return 140.0 + 0.035 * sion_hp


def bonus_hp(damage: float) -> float:
    return 0.15 * damage


@dataclass
class Enemy:
    name: str
    closest: bool
    lowest_hp: bool
    mark_ready_at: float = CHARGE_S
    next_ready: float = CHARGE_S


def fresh_enemies() -> list[Enemy]:
    return [
        Enemy("tank", closest=True, lowest_hp=False),
        Enemy("bruiser", closest=False, lowest_hp=False),
        Enemy("mid", closest=False, lowest_hp=False),
        Enemy("adc", closest=False, lowest_hp=True),
        Enemy("sup", closest=False, lowest_hp=False),
    ]


def pick(policy: str, enemies: list[Enemy], now: float) -> Enemy | None:
    if policy == "portrait_cycle_ready":
        ready = [e for e in enemies if now + 1e-9 >= e.next_ready]
        return ready[0] if ready else None
    if policy == "auto_closest":
        return next(e for e in enemies if e.closest)
    if policy == "auto_lowest_hp":
        return next(e for e in enemies if e.lowest_hp)
    raise ValueError(policy)


def run_policy(policy: str) -> dict:
    enemies = fresh_enemies()
    sion_hp = START_HP
    t = CHARGE_S
    hits: list[dict] = []
    wasted_aa = 0

    while t <= FIGHT_S + 1e-9:
        target = pick(policy, enemies, t)
        if target is None:
            nxt = min(e.next_ready for e in enemies)
            if nxt > FIGHT_S:
                break
            t = nxt
            continue
        if t + 1e-9 < target.next_ready:
            wasted_aa += 1
            t += SWITCH_AA_S
            continue
        dmg = proc_damage(sion_hp)
        gain = bonus_hp(dmg)
        sion_hp += gain
        hits.append(
            {
                "t": round(t, 2),
                "target": target.name,
                "damage": round(dmg, 1),
                "bonus_hp": round(gain, 1),
                "sion_hp": round(sion_hp, 1),
            }
        )
        target.next_ready = t + PER_TARGET_CD
        t += SWITCH_AA_S

    return {
        "policy": policy,
        "procs": len(hits),
        "unique_targets": sorted({h["target"] for h in hits}),
        "bonus_hp": round(sion_hp - START_HP, 1),
        "end_hp": round(sion_hp, 1),
        "wasted_aa_on_cd": wasted_aa,
        "hits": hits,
    }


POLICIES = ("auto_closest", "auto_lowest_hp", "portrait_cycle_ready")


def simulate() -> dict:
    results = {name: run_policy(name) for name in POLICIES}
    best = max(results.values(), key=lambda r: (r["procs"], r["bonus_hp"]))
    return {
        "patch": PATCH,
        "question": "Does Wild Rift have an attack mode that prefers Heartsteel-ready champions?",
        "answer": "No. Closest / lowest HP do not read Colossal Consumption marks. Lock the marked portrait.",
        "fight_s": FIGHT_S,
        "start_hp": START_HP,
        "charge_s": CHARGE_S,
        "per_target_cd": PER_TARGET_CD,
        "results": results,
        "best_policy": best["policy"],
    }


def report_text(data: dict) -> str:
    lines = [
        f"Sion Heartsteel targeting — {data['patch']}",
        f"Fight {data['fight_s']:.0f}s, start HP {data['start_hp']:.0f}, "
        f"charge {data['charge_s']}s, CD {data['per_target_cd']:.0f}s/target",
        "",
        data["answer"],
        "",
    ]
    for name in POLICIES:
        r = data["results"][name]
        lines.append(
            f"{name}: {r['procs']} procs, +{r['bonus_hp']} HP "
            f"({', '.join(r['unique_targets']) or 'none'})"
        )
    best = data["results"][data["best_policy"]]
    auto = data["results"]["auto_closest"]
    if auto["bonus_hp"]:
        ratio = best["bonus_hp"] / auto["bonus_hp"]
        lines.append(
            f"\nPortrait cycle vs auto-closest: {ratio:.2f}x bonus HP "
            f"({best['procs']} vs {auto['procs']} procs)."
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    root = Path(__file__).resolve().parent
    data = simulate()
    (root / "results.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    (root / "report.txt").write_text(report_text(data), encoding="utf-8")
    print(report_text(data), end="")


if __name__ == "__main__":
    main()
