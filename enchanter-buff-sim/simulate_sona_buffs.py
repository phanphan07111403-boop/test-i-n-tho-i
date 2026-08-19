#!/usr/bin/env python3
"""
Wild Rift Sona — Buff-max build sim (Patch 7.2+) + recommended runes.
Minute-by-minute over a 20-minute average game.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import json

GAME_MINUTES = 20


def gold_at_minute(m: int) -> int:
    total = 500
    for t in range(1, m + 1):
        if t <= 4:
            total += 320
        elif t <= 10:
            total += 460
        else:
            total += 560
    return total


def level_at_minute(m: int) -> int:
    table = {
        1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7, 7: 8, 8: 8,
        9: 9, 10: 10, 11: 10, 12: 11, 13: 11, 14: 12,
        15: 12, 16: 13, 17: 13, 18: 14, 19: 14, 20: 15,
    }
    return table.get(m, min(15, 1 + m))


def scythe_ap(minute: int) -> float:
    if minute < 6:
        return 0.0
    return 4.0 * min(10, minute - 5)


@dataclass
class Item:
    name: str
    cost: int
    ap: float = 0
    ah: float = 0
    hsp: float = 0
    hp: float = 0
    mana: float = 0
    ardent: bool = False
    staff: bool = False
    harmonic: bool = False
    redemption: bool = False
    seraph: bool = False
    tear: bool = False


ITEMS: Dict[str, Item] = {
    "Spectral Sickle": Item("Spectral Sickle", 500, ap=20),
    "Black Mist Scythe": Item("Black Mist Scythe", 0, ap=28, ah=10),
    "Boots of Speed": Item("Boots of Speed", 500),
    "Ionian Boots of Lucidity": Item("Ionian Boots of Lucidity", 1000, ah=20),
    "Forbidden Idol": Item("Forbidden Idol", 900, ah=10, hsp=0.05),
    "Fiendish Codex": Item("Fiendish Codex", 900, ap=35, ah=10),
    "Amplifying Tome": Item("Amplifying Tome", 500, ap=20),
    "Kindlegem": Item("Kindlegem", 1000, hp=200, ah=10),
    "Aether Wisp": Item("Aether Wisp", 950, ap=30),
    "Lost Chapter": Item("Lost Chapter", 1200, ap=40, ah=10),
    "Tear of the Goddess": Item("Tear of the Goddess", 800, mana=240, tear=True),
    "Seraph's Embrace": Item(
        "Seraph's Embrace", 2800, ap=70, mana=860, ah=10, seraph=True
    ),
    "Ardent Censer": Item(
        "Ardent Censer", 2700, ap=45, ah=10, hp=250, hsp=0.05, ardent=True
    ),
    "Staff of Flowing Water": Item(
        "Staff of Flowing Water", 2500, ap=50, ah=15, hp=100, hsp=0.05, staff=True
    ),
    "Harmonic Echo": Item(
        "Harmonic Echo", 2800, ap=50, ah=15, hp=100, hsp=0.05, harmonic=True
    ),
    "Redemption": Item(
        "Redemption", 2600, ap=50, ah=15, hp=150, hsp=0.05, redemption=True
    ),
}

UPGRADE = {
    "Ionian Boots of Lucidity": ("Boots of Speed",),
    "Ardent Censer": ("Forbidden Idol", "Kindlegem"),
    "Staff of Flowing Water": ("Forbidden Idol", "Aether Wisp"),
    "Harmonic Echo": ("Forbidden Idol", "Lost Chapter"),
    "Redemption": ("Forbidden Idol", "Fiendish Codex"),
    "Seraph's Embrace": ("Tear of the Goddess",),
}

NEXT = {
    "Ionian Boots of Lucidity": ["Boots of Speed"],
    "Ardent Censer": ["Forbidden Idol", "Kindlegem"],
    "Staff of Flowing Water": ["Forbidden Idol", "Aether Wisp"],
    "Harmonic Echo": ["Forbidden Idol", "Lost Chapter"],
    "Redemption": ["Forbidden Idol", "Fiendish Codex"],
    "Seraph's Embrace": ["Tear of the Goddess"],
}

BUILD_PATHS: Dict[str, List[str]] = {
    "Ardent → Staff → Harmonic → Redemption (Buff Max)": [
        "Spectral Sickle",
        "Boots of Speed",
        "Forbidden Idol",
        "Ardent Censer",
        "Ionian Boots of Lucidity",
        "Staff of Flowing Water",
        "Harmonic Echo",
        "Redemption",
    ],
    "Ardent → Redemption → Staff → Harmonic (Teamfight)": [
        "Spectral Sickle",
        "Boots of Speed",
        "Forbidden Idol",
        "Ardent Censer",
        "Ionian Boots of Lucidity",
        "Redemption",
        "Staff of Flowing Water",
        "Harmonic Echo",
    ],
    "Harmonic → Ardent → Redemption → Staff (Heal First)": [
        "Spectral Sickle",
        "Boots of Speed",
        "Forbidden Idol",
        "Harmonic Echo",
        "Ionian Boots of Lucidity",
        "Ardent Censer",
        "Redemption",
        "Staff of Flowing Water",
    ],
    "Tear → Ardent → Harmonic → Staff (Mana Scale)": [
        "Spectral Sickle",
        "Boots of Speed",
        "Tear of the Goddess",
        "Forbidden Idol",
        "Ardent Censer",
        "Ionian Boots of Lucidity",
        "Harmonic Echo",
        "Seraph's Embrace",
        "Staff of Flowing Water",
    ],
    "Ardent → Harmonic → Staff → Redemption (Guide-ish)": [
        "Spectral Sickle",
        "Boots of Speed",
        "Forbidden Idol",
        "Ardent Censer",
        "Ionian Boots of Lucidity",
        "Harmonic Echo",
        "Staff of Flowing Water",
        "Redemption",
    ],
}


def resolve_inventory(path: List[str], gold: int, minute: int) -> List[Item]:
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
        return pool >= remaining(name)

    def buy(name: str) -> bool:
        nonlocal pool
        if name in owned:
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

    # Tear stacks toward Seraph ~ after 8+ min if tear owned
    if (
        "Tear of the Goddess" in owned
        and "Seraph's Embrace" not in owned
        and minute >= 12
        and can("Seraph's Embrace")
    ):
        # only auto-finish if path wants Seraph later and we have gold
        if "Seraph's Embrace" in path:
            pass  # let path / blocked logic handle

    if blocked and blocked in NEXT:
        for comp in NEXT[blocked]:
            if comp not in owned and pool >= ITEMS[comp].cost:
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
                            buy(comp)
                    if can(step):
                        buy(step)
                    else:
                        break

    if "Ionian Boots of Lucidity" in owned and "Boots of Speed" in owned:
        owned.remove("Boots of Speed")
    return [ITEMS[n] for n in owned]


@dataclass
class Snap:
    minute: int
    build: str
    items: List[str]
    gold: int
    level: int
    ap: float
    ah: float
    hsp: float
    heal_hps: float
    shield_hps: float
    combat_buff_dps: float
    buff_score: float
    aura_uptime: float
    notes: str


def ranks(level: int) -> Tuple[int, int, int]:
    # Max Q then W then E for poke/aura; for buff-max prefer W max — use hybrid: W priority
    w = min(3, max(0, (level + 1) // 2 - 1))
    q = min(3, max(0, level // 3))
    e = min(3, max(0, (level - 2) // 4))
    if level >= 3:
        w = max(w, 1)
    if level >= 2:
        q = max(q, 1)
    if level >= 9:
        w = 3
    if level >= 8:
        q = max(q, 2)
    if level >= 11:
        q = 3
    return q, w, e


def compute(build: str, path: List[str], minute: int) -> Snap:
    gold = gold_at_minute(minute)
    level = level_at_minute(minute)
    inv = resolve_inventory(path, gold, minute)

    ap = ah = hsp = 0.0
    has_a = has_s = has_h = has_r = has_seraph = False
    names = []
    for it in inv:
        names.append(it.name)
        ap += it.ap
        ah += it.ah
        hsp += it.hsp
        if it.ardent:
            has_a = True
        if it.staff:
            has_s = True
        if it.harmonic:
            has_h = True
        if it.redemption:
            has_r = True
        if it.seraph:
            has_seraph = True
            ap += it.mana * 0.025  # rough Awe AP
        if it.name == "Black Mist Scythe":
            ap += scythe_ap(minute)

    # Revitalize rune ~ +5% hsp baseline for recommended page
    hsp += 0.05

    staff_ap = 0.0
    if has_s:
        staff_ap = 30 + 20 * (level - 1) / 14
        ap += staff_ap * 0.7

    cast_mult = 1.0 + ah / (ah + 100) * 0.55
    # Passive: each basic creates 3s aura; rotate Q/W/E → near-permanent with AH
    # Base aura uptime without AH ~0.70; with Ionian+items → 0.90+
    aura_uptime = min(0.98, 0.62 + 0.28 * (cast_mult - 1) / 0.4 + (0.08 if has_a or has_s else 0))

    q_r, w_r, e_r = ranks(level)

    # W heal (self + ally) — ally portion only for buff score
    w_heal = [35, 50, 65, 80][w_r] + 0.20 * ap
    w_cd = 10.0 / cast_mult
    heal_hps = (w_heal * (1 + hsp)) / w_cd

    # W shield aura — absorb value / 3s, refreshed by re-casting W
    w_shield = [25, 50, 75, 100][w_r] + 0.18 * ap
    # Effective shield HPS ≈ shield * aura_uptime / 3 (refresh window)
    shield_hps = (w_shield * (1 + hsp) * aura_uptime) / 3.0

    # Harmonic Echo procs on W
    if has_h:
        echo = 100 + 60 * (level - 1) / 14 + 0.15 * ap
        heal_hps += (echo * 1.1 * (1 + hsp)) / 15.0

    if has_r:
        red = 150 + 200 * (level - 1) / 14
        heal_hps += (red * 1.6 * (1 + hsp)) / 60.0

    # Q aura: next attack bonus for allies — main combat buff
    q_bonus = [8, 13, 18, 23][q_r] + 0.20 * ap
    # Allies get empowered autos while Q aura up; ADC ~1.2 AS
    q_buff_dps = q_bonus * 1.15 * aura_uptime

    # Ardent on heal/shield (W) — nearly permanent with aura spam
    ardent_dps = 0.0
    if has_a:
        on_hit = 16 + 6 * (level - 1) / 14
        ardent_uptime = min(0.97, 6.0 / max(5.5, w_cd) * 1.15)
        ardent_dps = on_hit * 1.2 * ardent_uptime + 8 * ardent_uptime

    staff_dps = staff_ap * 0.25 * aura_uptime if has_s else 0.0

    combat = q_buff_dps + ardent_dps + staff_dps

    # E MS — light util
    util = 5.0 * aura_uptime
    if has_seraph:
        util += 3.0  # mana = more casts

    buff_score = heal_hps * 1.0 + shield_hps * 1.15 + combat * 1.35 + util * 0.4

    notes = []
    if has_a and has_s:
        notes.append("DOUBLE BUFF")
    elif has_a:
        notes.append("Ardent")
    elif has_s:
        notes.append("Staff")
    if has_h:
        notes.append("Echo")
    if has_r:
        notes.append("Redemption")
    if has_seraph:
        notes.append("Seraph")
    if aura_uptime >= 0.9:
        notes.append("aura locked")

    return Snap(
        minute=minute,
        build=build,
        items=names,
        gold=gold,
        level=level,
        ap=round(ap, 1),
        ah=ah,
        hsp=hsp,
        heal_hps=round(heal_hps, 1),
        shield_hps=round(shield_hps, 1),
        combat_buff_dps=round(combat, 1),
        buff_score=round(buff_score, 1),
        aura_uptime=round(aura_uptime, 3),
        notes=", ".join(notes) or "building",
    )


RUNES_PAGE = """
SONA RUNES (recommended — buff / heal max)
==========================================
Keystone:  Aery
  → Extra shield when you W allies + poke when you Q. Best for aura spam.

Primary (Resolve / support tree — names vary by client):
  Font of Life  → Your CC / Power Chord marks enemies; ADC heals when hitting them
  Bone Plating  → Survive all-ins (Sona is fragile)
  Revitalize    → +heal & shield power (huge on W heal + W shield aura)

Secondary:
  Transcendence → Ability Haste (more auras = permanent buffs)

Summoners: Flash + Heal  (or Exhaust vs heavy dive / Ignite if ADC already Heal)

Skill order: W max (heal/shield) → Q max (aura damage buff) → E → R whenever
  Early: put 1–2 points Q for lane poke, then max W for buff-max.
"""


def main() -> None:
    results = {
        n: [compute(n, p, m) for m in range(1, GAME_MINUTES + 1)]
        for n, p in BUILD_PATHS.items()
    }
    timeline = []
    for m in range(1, GAME_MINUTES + 1):
        best_n, best_s = max(
            ((n, results[n][m - 1]) for n in results),
            key=lambda x: x[1].buff_score,
        )
        timeline.append(
            {
                "minute": m,
                "winner": best_n,
                "buff_score": best_s.buff_score,
                "heal_hps": best_s.heal_hps,
                "shield_hps": best_s.shield_hps,
                "combat_buff_dps": best_s.combat_buff_dps,
                "aura_uptime": best_s.aura_uptime,
                "items": best_s.items,
                "notes": best_s.notes,
            }
        )

    lines = []
    lines.append("=" * 78)
    lines.append("SONA BUFF-MAX SIM + RUNES (Wild Rift Patch 7.2+)")
    lines.append("20-minute game | Metric: heal + shield aura + combat buff DPS")
    lines.append("=" * 78)
    lines.append(RUNES_PAGE)
    lines.append("-" * 78)
    lines.append("MINUTE-BY-MINUTE OPTIMAL")
    lines.append("-" * 78)
    for row in timeline:
        items = " › ".join(row["items"][:5])
        if len(row["items"]) > 5:
            items += " › …"
        lines.append(
            f"  {row['minute']:>2}:00 | score {row['buff_score']:>6.1f} | "
            f"heal {row['heal_hps']:>5.1f} | sh {row['shield_hps']:>5.1f} | "
            f"buff {row['combat_buff_dps']:>5.1f} | aura {row['aura_uptime']*100:>3.0f}%"
        )
        lines.append(f"         {row['winner']}")
        lines.append(f"         {items}")
        lines.append(f"         {row['notes']}")

    lines.append("")
    lines.append("-" * 78)
    lines.append("BUILD COMPARISON (Buff Score)")
    lines.append("-" * 78)
    lines.append(f"  {'Build':<52} {'8':>6} {'12':>6} {'16':>6} {'20':>6} {'Avg':>7}")
    ranking = []
    for name, snaps in results.items():
        vals = [snaps[m - 1].buff_score for m in (8, 12, 16, 20)]
        avg = sum(s.buff_score for s in snaps) / len(snaps)
        ranking.append((avg, name, vals, snaps))
        lines.append(
            f"  {name:<52} {vals[0]:>6.1f} {vals[1]:>6.1f} {vals[2]:>6.1f} {vals[3]:>6.1f} {avg:>7.1f}"
        )
    ranking.sort(reverse=True)
    best = ranking[0]
    snaps = best[3]

    def first(item: str) -> Optional[int]:
        return next((s.minute for s in snaps if item in s.items), None)

    lines.append("")
    lines.append("-" * 78)
    lines.append("VERDICT")
    lines.append("-" * 78)
    lines.append(f"  Best buff path: {best[1]}")
    lines.append(f"  Avg Buff Score: {best[0]:.1f}")
    for label, key in (
        ("Ardent", "Ardent Censer"),
        ("Staff", "Staff of Flowing Water"),
        ("Harmonic", "Harmonic Echo"),
        ("Redemption", "Redemption"),
        ("Seraph", "Seraph's Embrace"),
    ):
        m = first(key)
        if m:
            lines.append(f"  {label} online: ~{m}:00")
    lines.append("")
    lines.append("  RECOMMENDED BUILD ORDER:")
    lines.append("  1) Sickle → Scythe")
    lines.append("  2) Boots + Forbidden Idol")
    lines.append("  3) Ardent Censer (~9–11) — AS/on-hit on every W")
    lines.append("  4) Ionian Boots — permanent aura uptime")
    lines.append("  5) Staff of Flowing Water — double buff with Ardent")
    lines.append("  6) Harmonic Echo — heal amp")
    lines.append("  7) Redemption — teamfight heal")
    lines.append("")
    lines.append("  Optional: Tear early if you OOMan a lot, then Seraph later")
    lines.append("  (mana path delays Ardent — lower early buff score).")
    lines.append("")
    lines.append("  PLAY: rotate Q→W→E so auras never drop; W even at full HP")
    lines.append("  (Ardent/Staff still proc). Power Chord for Font of Life marks.")
    lines.append("=" * 78)

    text = "\n".join(lines)
    print(text)
    out = "/workspace/enchanter-buff-sim"
    with open(f"{out}/sona_report.txt", "w", encoding="utf-8") as f:
        f.write(text + "\n")
    with open(f"{out}/sona_results.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "champion": "Sona",
                "runes": {
                    "keystone": "Aery",
                    "primary": ["Font of Life", "Bone Plating", "Revitalize"],
                    "secondary": ["Transcendence"],
                    "summoners": ["Flash", "Heal"],
                    "skill_order": "W max > Q max > E, R whenever",
                },
                "timeline": timeline,
                "builds": {
                    n: [
                        {
                            "minute": s.minute,
                            "items": s.items,
                            "buff_score": s.buff_score,
                            "heal_hps": s.heal_hps,
                            "shield_hps": s.shield_hps,
                            "combat_buff_dps": s.combat_buff_dps,
                            "aura_uptime": s.aura_uptime,
                            "notes": s.notes,
                        }
                        for s in sn
                    ]
                    for n, sn in results.items()
                },
            },
            f,
            indent=2,
        )
    print(f"\nWrote {out}/sona_report.txt and sona_results.json")


if __name__ == "__main__":
    main()
