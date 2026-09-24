#!/usr/bin/env python3
"""
Wild Rift — GameSir X3 Pro duelist picker
Patch snapshot: 7.3 (Sep 2026).

Question: which champ is strong in easy 1v1s, hard to kill, and maps
cleanly onto a GameSir X3 Pro (hall sticks + overlay buttons, no native
Wild Rift gamepad API).

Weights: 1v1 35% / unkillable 35% / controller 30%.
Scores are a documented rubric (0–10), not a combat engine.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import List
import json
from pathlib import Path

PATCH = "7.3"
OUT_DIR = Path(__file__).resolve().parent


@dataclass(frozen=True)
class Champ:
    name: str
    lane: str
    # Easy 1v1: wins melee duels with a short, forgiving combo.
    duel: float
    # Hard to kill: in-fight heal / shield / resists, not just out-of-combat regen.
    tank: float
    # GameSir X3 Pro: targeted buttons, analog chase, no extra targeting modes.
    pad: float
    wr_note: str
    why: str
    skip_if: str


# Rubric notes (controller column):
#   + analog left stick for "run at them" Q / stickiness
#   + targeted W/R (auto-target is enough)
#   + E that can be dumped on self / under feet
#   − 3-cast skillshots, parry windows, minion-Q, throw-angle ults
CHAMPS: List[Champ] = [
    Champ(
        name="Volibear",
        lane="Baron (also Jungle)",
        duel=9.2,
        tank=9.1,
        pad=9.4,
        wr_note="Baron ~54.4% WR, S+ on wildriftmeta 7.3",
        why=(
            "Q is 'hold left stick toward them, then auto' — hall sticks beat a "
            "virtual joystick. W is targeted bite + heal. E can be cast on your "
            "feet for the shield. R is a huge landing zone that also turns the "
            "tower off, so dives do not delete you."
        ),
        skip_if="Vayne / kite-heavy range + disengage; they never let you bite twice.",
    ),
    Champ(
        name="Garen",
        lane="Baron",
        duel=8.1,
        tank=7.4,
        pad=9.8,
        wr_note="High pick, ~49.6% WR on wildriftcore 7.3",
        why=(
            "Zero aim: Q targeted silence, E spin around you, W self-cast, R "
            "execute. Best raw X3 mapping. Loses long 1v1s to true duelists "
            "and is less unkillable mid-fight than Voli/Sett."
        ),
        skip_if="Fiora, Vayne, or any lane that kites the spin forever.",
    ),
    Champ(
        name="Sett",
        lane="Baron",
        duel=8.4,
        tank=8.8,
        pad=7.2,
        wr_note="~49.9% WR, A-tier baron 7.3",
        why=(
            "E pull + grit W makes him a brawler who lives the first burst. "
            "W cone center and R throw-angle need right-stick aim — doable on "
            "X3 Pro, but more miss-prone than Voli's targeted bite."
        ),
        skip_if="Poke/kite comps that never let you stack grit.",
    ),
    Champ(
        name="Mordekaiser",
        lane="Baron",
        duel=9.0,
        tank=8.3,
        pad=7.0,
        wr_note="S-tier baron on several 7.2/7.3 lists; high ban",
        why=(
            "R is a forced 1v1 with stolen stats — closest thing to 'easy 1v1' "
            "in the kit. W shield is tanky. Q facing + E pull are skillshots, "
            "so overlay aim is worse than point-and-click Voli/Garen."
        ),
        skip_if="Fiora, Gwen, Vayne — they win the isolated duel.",
    ),
    Champ(
        name="Warwick",
        lane="Jungle (Baron possible)",
        duel=8.3,
        tank=8.4,
        pad=8.6,
        wr_note="Ult CD nerfed 7.2c (80/70/60 → 100/90/80)",
        why=(
            "Q is targeted sustain, analog stick helps stay in bite range, R "
            "is one dash skillshot. Easy 1v1s when the fear + Q heal line up. "
            "Weaker pick after the ult cooldown hit."
        ),
        skip_if="You need Baron lane, or they have heavy anti-heal + range.",
    ),
    Champ(
        name="Darius",
        lane="Baron",
        duel=9.0,
        tank=6.4,
        pad=7.6,
        wr_note="Often S+/S baron; dunk 1v1s, not a tank",
        why=(
            "Bleed + dunk wins most melee 1v1s. Analog stick is great for Q "
            "outer-ring. He is not hard to kill — if the dunk is not ready, "
            "he loses the 'unkillable' check."
        ),
        skip_if="You wanted to survive messy fights, not win a bleed race.",
    ),
    Champ(
        name="Jax",
        lane="Baron",
        duel=8.6,
        tank=7.2,
        pad=8.0,
        wr_note="S baron on several 7.2/7.3 lists; scales, weaker early",
        why=(
            "Leap is targeted, E is a button-hold dodge. Analog spacing around "
            "E is a controller superpower. Not 'easy' until items, and not as "
            "tanky as Heartsteel Voli."
        ),
        skip_if="You want to win lane at 3, not at 2 items.",
    ),
    Champ(
        name="Dr. Mundo",
        lane="Baron",
        duel=6.2,
        tank=9.6,
        pad=8.3,
        wr_note="B-tier baron on 7.2d lists — unkillable, not a duelist",
        why=(
            "Hardest to actually kill. Cleaver Q is a skillshot; E is an auto "
            "reset. Loses clean 1v1s to %HP / true-damage bruisers."
        ),
        skip_if="You asked for easy 1v1s, not just a walking HP bar.",
    ),
    Champ(
        name="Olaf",
        lane="Jungle / Baron",
        duel=8.2,
        tank=7.8,
        pad=7.4,
        wr_note="A-tier on several 7.2 lists",
        why=(
            "R makes him unstoppable in the 1v1. Axes are skillshots you must "
            "pick up — overlay aiming + pathing is messier than targeted Voli W."
        ),
        skip_if="You do not want to chase axes on a mapped right stick.",
    ),
    Champ(
        name="Aatrox",
        lane="Baron",
        duel=8.0,
        tank=8.0,
        pad=5.4,
        wr_note="A-tier; revive + drain, three Q sweet spots",
        why=(
            "Sustain 1v1s are real. Three directional Qs on a touch overlay "
            "are the opposite of X3-Pro-friendly."
        ),
        skip_if="You are on a mapped gamepad.",
    ),
    Champ(
        name="Fiora",
        lane="Baron",
        duel=8.8,
        tank=5.5,
        pad=5.0,
        wr_note="C-tier on 7.2d baron list; best pure duelist, not easy",
        why=(
            "Wins 1v1s, dies if vitals/parry are late. Analog stick helps "
            "vital dancing; W parry window is a poor overlay-button skill."
        ),
        skip_if="You asked for easy and hard to kill.",
    ),
]


W_DUEL, W_TANK, W_PAD = 0.35, 0.35, 0.30


def total(c: Champ) -> float:
    return W_DUEL * c.duel + W_TANK * c.tank + W_PAD * c.pad


def rank() -> List[Champ]:
    return sorted(CHAMPS, key=total, reverse=True)


def report_text(ranked: List[Champ]) -> str:
    winner = ranked[0]
    lines = [
        f"Wild Rift GameSir X3 Pro duelist rank — patch {PATCH}",
        "Question: strong easy 1v1 + hard to kill + maps onto X3 Pro.",
        f"Weights: 1v1 {W_DUEL:.0%} / unkillable {W_TANK:.0%} / controller {W_PAD:.0%}.",
        "",
        f"WINNER: {winner.name} ({winner.lane})",
        f"  score {total(winner):.2f}  1v1 {winner.duel}  tank {winner.tank}  pad {winner.pad}",
        f"  {winner.wr_note}",
        "",
        f"{'Rk':<4}{'Champ':<16}{'Lane':<22}{'1v1':>5}{'Tank':>6}{'Pad':>6}{'Tot':>7}",
        "-" * 66,
    ]
    for i, c in enumerate(ranked, 1):
        lines.append(
            f"{i:<4}{c.name:<16}{c.lane:<22}{c.duel:>5.1f}{c.tank:>6.1f}"
            f"{c.pad:>6.1f}{total(c):>7.2f}"
        )
    lines += [
        "",
        "Why the analog stick matters",
        "  Wild Rift has no native gamepad API. X3 Pro uses overlay mapping.",
        "  Hall left stick > virtual joystick for chase. Targeted buttons >",
        "  dragged skillshots. Extra champ modes (3-cast Q, parry, minion Q)",
        "  eat mapping slots and miss more.",
        "",
        "X3 Pro mapping for Volibear",
        "  LS move   A Q (Thundering Smash)   B W (Frenzied Maul, auto-target)",
        "  X E (Sky Splitter — default on-feet / self)   Y R",
        "  RB attack   RT Flash   LT Ignite   LB recall",
        "  RS only if you want to throw E/R off your feet",
        "",
        "Play the 1v1",
        "  E on your feet (shield) → Q run-at-them → auto (stun) → W → auto (heal bite).",
        "  R when they sit under tower. Tower is disabled; you are not.",
        "",
        "Do not first-pick into Vayne / long-range kite. Then take Garen",
        "  (simpler buttons, weaker in-fight sustain) or Sett (W must be aimed).",
        "",
    ]
    for c in ranked[:5]:
        lines += [f"{c.name}: {c.why}", f"  Skip if: {c.skip_if}", ""]
    return "\n".join(lines)


def main() -> None:
    ranked = rank()
    payload = {
        "patch": PATCH,
        "weights": {"duel": W_DUEL, "tank": W_TANK, "pad": W_PAD},
        "winner": ranked[0].name,
        "ranking": [
            {**asdict(c), "total": round(total(c), 3)} for c in ranked
        ],
    }
    (OUT_DIR / "results.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )
    (OUT_DIR / "report.txt").write_text(report_text(ranked) + "\n", encoding="utf-8")
    print(report_text(ranked))


if __name__ == "__main__":
    main()
