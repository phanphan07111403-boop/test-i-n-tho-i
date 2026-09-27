#!/usr/bin/env python3
"""
Wild Rift 7.3 — Volibear vs Shen Baron.

Scores are a documented rubric (0–10), not a shared combat engine.
Kits do different jobs; the table is which job each one wins.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple
import json
from pathlib import Path

PATCH = "7.3"
OUT_DIR = Path(__file__).resolve().parent


@dataclass(frozen=True)
class Champ:
    name: str
    gamesir: float
    touch: float
    lane: float
    duel: float
    teamfight: float
    wr_all: str
    wr_cn: str


VOLI = Champ(
    name="Volibear",
    gamesir=9.4,
    touch=8.0,
    lane=8.6,
    duel=9.2,
    teamfight=6.2,
    wr_all="54.4% WR / 5.0% pick, S+ wildriftmeta all ranks",
    wr_cn="48.3% WR, C-tier Diamond+ CN (#32/41)",
)

SHEN = Champ(
    name="Shen",
    gamesir=6.2,
    touch=8.6,
    lane=6.4,
    duel=6.2,
    teamfight=9.3,
    wr_all="48.4% WR / 1.1% pick, A wildriftmeta all ranks",
    wr_cn="56.8% WR, S+ Diamond+ CN (#2/41)",
)

ASPECTS: List[Tuple[str, str]] = [
    ("gamesir", "GameSir X3 Pro"),
    ("touch", "Touch (no pad)"),
    ("lane", "Lane (generic)"),
    ("duel", "1v1 / side"),
    ("teamfight", "Teamfight"),
]


def winner(attr: str) -> str:
    a, b = getattr(VOLI, attr), getattr(SHEN, attr)
    if abs(a - b) < 0.25:
        return "tie"
    return VOLI.name if a > b else SHEN.name


def report_text() -> str:
    lines = [
        f"Wild Rift Volibear vs Shen Baron — patch {PATCH}",
        "Same question split: GameSir vs touch, then lane / 1v1 / teamfight.",
        "",
        f"{'Aspect':<22}{'Volibear':>10}{'Shen':>10}{'edge':>12}",
        "-" * 54,
    ]
    for attr, label in ASPECTS:
        v, s = getattr(VOLI, attr), getattr(SHEN, attr)
        lines.append(f"{label:<22}{v:>10.1f}{s:>10.1f}{winner(attr):>12}")
    lines += [
        f"{'Head-to-head lane':<22}{'skill':>10}{'W wins':>10}{'Shen W':>12}",
        "",
        "Ranked signal",
        f"  Volibear  {VOLI.wr_all}",
        f"            {VOLI.wr_cn}",
        f"  Shen      {SHEN.wr_all}",
        f"            {SHEN.wr_cn}",
        "",
        "GameSir X3 Pro — Volibear",
        "  Q is analog chase + stun auto. W is a targeted bite. E can sit",
        "  on-feet with a GameSir gesture. R is a fat landing zone that",
        "  turns the tower off. Overlay mapping matches the kit.",
        "",
        "GameSir X3 Pro — Shen",
        "  E is a dash you must draw through them (miss = no taunt, no",
        "  energy). W needs the spirit blade in the right place. R is",
        "  picking an ally on the map — overlay is bad at portraits and",
        "  the minimap. Playable, not the pad champ.",
        "",
        "Touch (no pad) — Shen slightly",
        "  Thumbs are what WR was built for: swipe E, tap R on the ally",
        "  portrait, drag Q through them. Volibear is still easy, but",
        "  Shen's extra buttons stop being a tax. CN Diamond+ WR then",
        "  decides it: Shen S+ 56.8%, Volibear C 48.3%.",
        "",
        "Lane — Volibear",
        "  Q stun, W heal, E shield, R dive. Shen is the lowest-damage",
        "  top: Q is empowered autos, he farms and waits for R. Volibear",
        "  crashes and kills. Shen holds and does not die.",
        "",
        "1v1 / side — Volibear",
        "  Isolated 8s slugfest is Volibear's whole kit (Dusk → Hull →",
        "  Rift). Shen's kit is not a kill threat; he 1v9s by living and",
        "  ulting out, not by winning the duel.",
        "",
        "Teamfight — Shen",
        "  Global R + taunt peel + W block. Volibear dives one person",
        "  and has no peel after R. Shen threatens two places at once.",
        "",
        "Head-to-head (Voli lane vs Shen)",
        "  Shen W blocks the autos Volibear lives on (Q stun hit, W bite,",
        "  lightning). Taunt pauses Thundering Smash. Volibear E is magic",
        "  so it still lands. Fight around W: if Shen holds W for the",
        "  bite, he wins the trade. If W is down, Volibear runs him down.",
        "",
        "Pick",
        "  GameSir + want 1v1s: Volibear.",
        "  Touch + want to win ranked games: Shen.",
        "  Team needs a dive: Volibear. Team needs a save: Shen.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    text = report_text()
    payload = {
        "patch": PATCH,
        "voli": VOLI.__dict__,
        "shen": SHEN.__dict__,
        "edge": {attr: winner(attr) for attr, _ in ASPECTS},
        "head_to_head": "Shen W if timed; Volibear if W is down",
        "pick": {
            "gamesir_1v1": "Volibear",
            "touch_ranked": "Shen",
            "lane": "Volibear",
            "duel": "Volibear",
            "teamfight": "Shen",
        },
    }
    (OUT_DIR / "report.txt").write_text(text, encoding="utf-8")
    (OUT_DIR / "results.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )
    print(text)


if __name__ == "__main__":
    main()
