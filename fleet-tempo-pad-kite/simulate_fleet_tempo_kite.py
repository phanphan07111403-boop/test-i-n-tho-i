#!/usr/bin/env python3
"""
Wild Rift 7.3 — Fleet Footwork vs Lethal Tempo while kiting on a pad.

Pad = GameSir X3 Pro, Android G-Touch, the loop from the pad guide:
  left stick held away, RT taps the attack button, Force Attack Follow OFF.
  Mapping delay 50 ms. A correct map makes the next auto LATE (extra walk).
  A broken map freezes the stick on RT (extra stand). Both are simulated.

Question:
  Which keystone actually kites — opens space against a melee running at you —
  when the only movement tool is the left stick between autos?

Sources baked in:
  - Lethal Tempo: official patch notes 7.3 (6.4% AS × 6 ranged, bolt, no range).
  - Attack speed: official 7.3 formula, including the per-level curve that
    sums to 14 × (AS per level) at level 15.
  - Fleet Footwork: current WR wiki description (heal 15–110, +40% AS on that
    auto, +20% MS for 1s). Not reprinted in the 7.3 notes.
  - Kai'Sa E: official 7.3 Supercharge formula.
  - Kai'Sa plasma: official 7.3 Second Skin formula.
  - Windup percent is NOT published for WR. Kai'Sa 18% and Ashe 22% are
    assumptions (PC Kai'Sa is ~16%). A second pass uses a sticky windup
    (bonus AS shrinks the windup slower than the attack period).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Dict, List


AS_CAP = 3.0
HORIZON = 8.0
DT = 0.01
MELEE = 175.0
ARMOR = 80.0
MR = 45.0
TARGET_HP = 2800.0

# Ranged Lethal Tempo, patch 7.3.
LT_AS = 0.064
LT_STACKS = 6
LT_TIME = 6.0
LT_BOLT = (6.0, 24.0)  # level 1 → 15
LT_BOLT_AMP = 0.0067  # per 1% bonus AS

# Fleet Footwork, WR wiki (live description).
FLEET_HEAL = (15.0, 110.0)
FLEET_AS = 0.40
FLEET_MS = 0.20
FLEET_MS_TIME = 1.0
FLEET_AD = 0.15
ENERGIZE_PER_AUTO = 6.0
ENERGIZE_UNITS = 24.0

# Kai'Sa Supercharge, patch 7.3.
# MS = rank_base * (1 + bonus AS), capped.
E_BASE = {1: 0.50, 2: 0.55, 3: 0.60, 4: 0.65}
E_CAP = {1: 1.00, 2: 1.10, 3: 1.20, 4: 1.30}
E_AS = {1: 0.40, 2: 0.50, 3: 0.60, 4: 0.70}
E_AS_TIME = 4.0


@dataclass
class Champ:
    name: str
    base_as: float
    as_ratio: float
    base_bonus_as: float
    as_per_level: float
    base_ad: float
    ad_growth: float
    ms: float
    attack_range: float
    windup: float  # fraction of the attack period when windup modifier is 1
    plasma: bool = False
    ashe_slow: float = 0.0


@dataclass
class Loadout:
    label: str
    level: int
    bonus_ad: float
    bonus_as: float  # items + rageblade stacks, not runes
    flat_ms: float
    ms_pct: float
    ap: float = 0.0
    crit: float = 0.0
    kraken: bool = False
    rage_magic: float = 0.0
    rage_start: int = 0
    stormrazor: bool = False
    e_rank: int = 0


@dataclass
class Hands:
    name: str
    delay: float  # RT arrives late → extra walk. Correct 50 ms map.
    floor: float  # minimum seconds between RT taps
    stuck: float = 0.0  # extra stand glued onto each windup. Broken map.


@dataclass
class FightResult:
    lived: float
    caught: bool
    damage: float
    heal: float
    autos: int
    fleet_procs: int
    min_gap: float
    end_gap: float
    stand_time: float
    walk_time: float
    e_used: bool
    period_at_6: float
    walk_at_6: float
    killed: bool


def level_bonus_as(per_level: float, level: int) -> float:
    """Official curve. Each level-up from L to L+1 adds per_level*(0.7+0.04*L).

    Sum from L=1..14 equals 14*per_level, which is the level-15 example in
    the 7.3 notes (Caitlyn: 0.04 × 14).
    """
    total = 0.0
    for level_before in range(1, level):
        total += per_level * (0.7 + 0.04 * level_before)
    return total


def lerp_level(pair: tuple, level: int) -> float:
    t = min(1.0, max(0.0, (level - 1) / 14.0))
    return pair[0] + (pair[1] - pair[0]) * t


def bonus_as_of(champ: Champ, loadout: Loadout, extra: float) -> float:
    return (
        champ.base_bonus_as
        + level_bonus_as(champ.as_per_level, loadout.level)
        + loadout.bonus_as
        + extra
    )


def period_of(champ: Champ, bonus: float) -> float:
    aps = min(AS_CAP, champ.base_as + bonus * champ.as_ratio)
    return 1.0 / aps


def windup_of(champ: Champ, bonus: float, windup_mod: float) -> float:
    """windup_mod 1: windup is a constant fraction of the period.

    windup_mod < 1: bonus AS shrinks the windup slower than the period,
    so you stand a larger share of each auto. Stress test only.
    """
    raw = champ.windup * (1.0 / champ.base_as) / (1.0 + bonus * windup_mod)
    return min(raw, period_of(champ, bonus) * 0.92)


def armor_mult() -> float:
    return 100.0 / (100.0 + ARMOR)


def mr_mult() -> float:
    return 100.0 / (100.0 + MR)


def total_ad(champ: Champ, loadout: Loadout) -> float:
    return champ.base_ad + champ.ad_growth * (loadout.level - 1) + loadout.bonus_ad


def simulate(
    champ: Champ,
    loadout: Loadout,
    hands: Hands,
    rune: str,
    enemy_ms: float,
    use_e: bool,
    windup_mod: float = 1.0,
) -> FightResult:
    ad = total_ad(champ, loadout)
    bonus_ad = loadout.bonus_ad
    crit_mult = 1.0 + loadout.crit  # 200% crit damage → +100% on a crit
    base_ms = (champ.ms + loadout.flat_ms) * (1.0 + loadout.ms_pct)

    t = 0.0
    gap = champ.attack_range
    hp = TARGET_HP
    energy = 0.0
    energy_dist = 0.0
    fleet_until = 0.0
    fleet_as_next = False
    storm_until = 0.0
    slow_until = 0.0
    lt_stacks = 0
    lt_until = 0.0
    rage = loadout.rage_start
    rage_hits = 0
    kraken_n = 0
    plasma = 0
    e_used = False
    e_as_until = -1.0
    phase = "windup"
    phase_left = 0.0
    attack_started = 0.0
    attack_ready = 0.0
    last_tap = -10.0
    period = 0.0
    caught = False
    damage = 0.0
    heal = 0.0
    autos = 0
    fleet_procs = 0
    min_gap = gap
    stand_time = 0.0
    walk_time = 0.0

    def extra_as() -> float:
        extra = 0.0
        if rune == "tempo" and t <= lt_until:
            extra += LT_AS * lt_stacks
        if loadout.e_rank and 0.0 <= t <= e_as_until:
            extra += E_AS[loadout.e_rank]
        return extra

    def your_ms() -> float:
        ms = base_ms
        if t <= fleet_until:
            ms *= 1.0 + FLEET_MS
        if t <= storm_until:
            ms *= 1.45
        if e_casting():
            b = bonus_as_of(champ, loadout, extra_as())
            ms *= 1.0 + e_ms_pct(loadout.e_rank, b)
        return ms

    def enemy_speed() -> float:
        ms = enemy_ms
        if champ.ashe_slow and t <= slow_until:
            ms *= 1.0 - champ.ashe_slow
        return ms

    e_left = 0.0

    def e_casting() -> bool:
        return e_left > 0.0

    def e_ms_pct(rank: int, bonus: float) -> float:
        return min(E_CAP[rank], E_BASE[rank] * (1.0 + max(0.0, bonus)))

    # Opening auto is already pressed as they step into range.
    b0 = bonus_as_of(champ, loadout, extra_as())
    period = period_of(champ, b0)
    phase = "windup"
    phase_left = windup_of(champ, b0, windup_mod) + hands.stuck
    attack_started = 0.0
    attack_ready = period
    last_tap = 0.0

    def fire() -> None:
        nonlocal hp, energy, fleet_until, fleet_as_next, storm_until
        nonlocal lt_stacks, lt_until, rage, rage_hits, kraken_n, plasma
        nonlocal damage, heal, autos, fleet_procs, slow_until

        autos += 1
        dealt = ad * crit_mult * armor_mult()
        # Brutal, mid of the 12–18 band.
        dealt += lerp_level((12.0, 18.0), loadout.level) * armor_mult()
        if loadout.rage_magic:
            dealt += loadout.rage_magic * mr_mult()
            rage = min(4, rage + 1)
            if rage >= 4:
                rage_hits += 1
                if rage_hits % 3 == 0:
                    # Phantom applies on-hit, does not take an attack period.
                    if champ.plasma:
                        dealt += plasma_hit()
                    dealt += loadout.rage_magic * mr_mult()
                    dealt += lerp_level((12.0, 18.0), loadout.level) * armor_mult()
        if loadout.kraken:
            kraken_n += 1
            if kraken_n % 3 == 0:
                dealt += lerp_level((120.0, 168.0), loadout.level) * armor_mult()
        if champ.plasma:
            dealt += plasma_hit()
        if rune == "tempo":
            if t > lt_until:
                lt_stacks = 0
            lt_stacks = min(LT_STACKS, lt_stacks + 1)
            lt_until = t + LT_TIME
            if lt_stacks >= LT_STACKS:
                bolt = lerp_level(LT_BOLT, loadout.level)
                b = bonus_as_of(champ, loadout, extra_as())
                bolt *= 1.0 + b * 100.0 * LT_BOLT_AMP
                dealt += bolt * armor_mult()
        energy += ENERGIZE_PER_AUTO
        if energy >= 100.0:
            energy -= 100.0
            if rune == "fleet":
                fleet_procs += 1
                fleet_as_next = True
                fleet_until = t + FLEET_MS_TIME
                h = lerp_level(FLEET_HEAL, loadout.level) + FLEET_AD * bonus_ad
                heal += h
            if loadout.stormrazor:
                storm_until = t + 1.5
                dealt += 120.0 * mr_mult()
        if champ.ashe_slow:
            slow_until = t + 2.0
        damage += dealt
        hp = max(0.0, hp - dealt)

    def plasma_hit() -> float:
        nonlocal plasma, hp
        plasma = min(5, plasma + 1)
        stacks = plasma
        raw = (
            4.0
            + loadout.level
            + 0.12 * loadout.ap
            + stacks * (1.0 + 0.2 * loadout.level + 0.02 * loadout.ap)
        )
        dealt = raw * mr_mult()
        if stacks >= 5:
            missing = 1.0 - hp / TARGET_HP
            pop = (0.15 + 0.05 * loadout.ap / 100.0) * missing * hp
            dealt += pop * mr_mult()
            plasma = 0
        return dealt

    while t < HORIZON and not caught and hp > 0:
        step = min(DT, HORIZON - t)
        # Movement this step.
        move = phase != "windup"
        if phase == "hold":
            move = False
        ym = your_ms() if move else 0.0
        em = enemy_speed()
        # Don't integrate a full DT if a phase ends sooner.
        if phase == "windup":
            step = min(step, phase_left)
        elif e_left > 0:
            step = min(step, e_left)

        gap += (ym - em) * step
        if move:
            energy_dist += ym * step
            walk_time += step
        else:
            stand_time += step
        while energy_dist >= ENERGIZE_UNITS:
            energy_dist -= ENERGIZE_UNITS
            energy += 1.0
        t += step
        if gap < min_gap:
            min_gap = gap
        if gap <= MELEE:
            caught = True
            gap = MELEE
            break

        if phase == "windup":
            phase_left -= step
            if phase_left <= 1e-9:
                fire()
                phase = "walk"
                attack_ready = attack_started + period
            continue

        if e_left > 0:
            e_left -= step
            if e_left <= 1e-9:
                e_as_until = t + E_AS_TIME
                phase = "walk"
            continue

        # Out of range: hold still and let them walk back into the auto.
        if gap > champ.attack_range:
            phase = "hold"
            continue

        phase = "walk"
        # Press E once, on the walk, when they have closed some space.
        if (
            use_e
            and loadout.e_rank
            and not e_used
            and gap <= champ.attack_range - 80.0
        ):
            b = bonus_as_of(champ, loadout, extra_as())
            e_used = True
            e_left = e_cast_time(b)
            phase = "walk"
            continue

        intent = max(attack_ready, last_tap + hands.floor)
        start = max(intent + hands.delay, attack_ready)
        if t + 1e-9 < start:
            continue
        b = bonus_as_of(champ, loadout, extra_as())
        if rune == "fleet" and fleet_as_next:
            b += FLEET_AS
            fleet_as_next = False
        period = period_of(champ, b)
        phase = "windup"
        phase_left = windup_of(champ, b, windup_mod) + hands.stuck
        attack_started = t
        last_tap = intent

    lived = t
    b6 = bonus_as_of(champ, loadout, LT_AS * LT_STACKS if rune == "tempo" else 0.0)
    p6 = period_of(champ, b6)
    w6 = windup_of(champ, b6, windup_mod)
    return FightResult(
        lived=lived,
        caught=caught,
        damage=damage,
        heal=heal,
        autos=autos,
        fleet_procs=fleet_procs,
        min_gap=min_gap,
        end_gap=gap,
        stand_time=stand_time,
        walk_time=walk_time,
        e_used=e_used,
        period_at_6=p6,
        walk_at_6=p6 - w6,
        killed=hp <= 0.0 and not caught,
    )


def e_cast_time(bonus: float) -> float:
    """Wiki cast, 1.0s → 0.5s as bonus AS goes 0 → 100%. Not in the 7.3 notes."""
    return 0.5 + 0.5 * (1.0 - min(1.0, max(0.0, bonus)))


KAISA = Champ(
    "Kai'Sa",
    base_as=0.644,
    as_ratio=0.644,
    base_bonus_as=0.17,
    as_per_level=0.022,
    base_ad=59,
    ad_growth=3.5,
    ms=340,
    attack_range=575,
    windup=0.18,
    plasma=True,
)
ASHE = Champ(
    "Ashe",
    base_as=0.658,
    as_ratio=0.658,
    base_bonus_as=0.23,
    as_per_level=0.03,
    base_ad=60,
    ad_growth=4.0,
    ms=335,
    attack_range=625,
    windup=0.22,
    ashe_slow=0.20,
)

# Item AS / MS from the 7.3 item pass used by the Varus sim.
# Berserker AD is marked approximate there (10). Greaves AS 35% is in the
# official Caitlyn example.
KAISA_BUILDS: List[Loadout] = [
    Loadout("lane L4 long sword", 4, bonus_ad=12, bonus_as=0.0, flat_ms=0, ms_pct=0, e_rank=1),
    Loadout("boots L8 greaves", 8, bonus_ad=10, bonus_as=0.35, flat_ms=45, ms_pct=0, e_rank=1),
    Loadout(
        "2-item L12 Kraken",
        12,
        bonus_ad=10 + 45,
        bonus_as=0.35 + 0.35,
        flat_ms=45,
        ms_pct=0.04,
        kraken=True,
        e_rank=2,
    ),
    Loadout(
        "3-item L15 Rageblade stacked",
        15,
        bonus_ad=10 + 45 + 35,
        bonus_as=0.35 + 0.35 + 0.32,
        flat_ms=45,
        ms_pct=0.04,
        ap=30,
        kraken=True,
        rage_magic=30,
        rage_start=4,
        e_rank=4,
    ),
]
ASHE_BUILDS: List[Loadout] = [
    Loadout("boots L8 greaves", 8, bonus_ad=10, bonus_as=0.35, flat_ms=45, ms_pct=0),
    Loadout(
        "2-item L12 Stormrazor",
        12,
        bonus_ad=10 + 50,
        bonus_as=0.35 + 0.20,
        flat_ms=45,
        ms_pct=0,
        crit=0.25,
        stormrazor=True,
    ),
    Loadout(
        "3-item L15 Runaan",
        15,
        bonus_ad=10 + 50,
        bonus_as=0.35 + 0.20 + 0.40,
        flat_ms=45,
        ms_pct=0.04,
        crit=0.50,
        stormrazor=True,
    ),
]

HANDS = [
    Hands("mouse", delay=0.0, floor=0.0),
    Hands("pad", delay=0.05, floor=0.36),
    Hands("pad fast", delay=0.05, floor=0.28),
    Hands("pad stuck", delay=0.0, floor=0.36, stuck=0.05),
]
CHASERS = [
    ("walk 370", 370.0),
    ("boots 415", 415.0),
    ("ghost 490", 490.0),
]
RUNES = ("fleet", "tempo")


def row_key(champ: str, build: str, hands: str, rune: str, chaser: str, e: bool, mod: float) -> str:
    return f"{champ}|{build}|{hands}|{rune}|{chaser}|e={int(e)}|wmod={mod}"


def run_all() -> Dict[str, FightResult]:
    out: Dict[str, FightResult] = {}
    jobs = [(KAISA, KAISA_BUILDS, True), (ASHE, ASHE_BUILDS, False)]
    for champ, builds, can_e in jobs:
        for build in builds:
            for hands in HANDS:
                for rune in RUNES:
                    for cname, cms in CHASERS:
                        for use_e in ((False, True) if can_e else (False,)):
                            if use_e and not build.e_rank:
                                continue
                            r = simulate(champ, build, hands, rune, cms, use_e)
                            out[row_key(champ.name, build.label, hands.name, rune, cname, use_e, 1.0)] = r
    # Sticky-windup stress: Kai'Sa pad, no E, one chaser, 3-item.
    stress_build = KAISA_BUILDS[-1]
    pad = HANDS[1]
    for rune in RUNES:
        for cname, cms in CHASERS:
            r = simulate(KAISA, stress_build, pad, rune, cms, False, windup_mod=0.6)
            out[row_key(KAISA.name, stress_build.label, pad.name, rune, cname, False, 0.6)] = r
    return out


def fmt_time(r: FightResult) -> str:
    if r.killed:
        return f"{r.lived:4.2f}s KILL"
    if r.caught:
        return f"{r.lived:4.2f}s CAUGHT"
    return "8.0s up"


def write_report(results: Dict[str, FightResult]) -> str:
    lines: List[str] = []
    a = lines.append
    a("=" * 78)
    a("FLEET FOOTWORK vs LETHAL TEMPO — KITING ON A PAD")
    a("Wild Rift 7.3  |  GameSir X3 Pro  |  stick held away, RT tap, Follow OFF")
    a("Window: 8.0s  |  CAUGHT = melee reaches 175  |  KILL = that body dies  |  up = 8s, still apart")
    a("Body: 2800 HP, 80 armor, 45 MR. Damage is post-mitigation and can overkill.")
    a("=" * 78)
    a("")
    a("WHAT THE PAD IS DOING")
    a("  Analog kite = left stick away between autos, RT on each attack.")
    a("  Wind-up: you stand. A new move in that window cancels the shot.")
    a("  Cooldown after the shot: this is the walk. This is the kite.")
    a("  Correct map (50 ms, Mapping Enhancement on): the next auto is LATE.")
    a("    That lateness is extra walk. Hands below called 'pad' (tap floor 0.36s).")
    a("  Broken map (RT drops the stick): each auto adds a 0.05s stand. 'pad stuck'.")
    a("  'mouse' is the same champ with no delay and no tap floor.")
    a("  7.3 Tempo is +6.4% AS per stack, 6 stacks, then a bolt. No bonus range.")
    a("  Fleet is +20% move speed for 1s, a heal, and +40% AS on that one auto.")
    a("")
    a("-" * 78)
    a("CADENCE — can the shoulder button spend Tempo?  (Kai'Sa, no E)")
    a("  period = seconds per auto at 0 Tempo stacks and at 6.")
    a("  walk   = period minus wind-up at 6 stacks. That is stick time.")
    a("  A 0.36s tap floor wastes AS only when the 6-stack period is shorter.")
    a("-" * 78)
    pad = HANDS[1]
    for build in KAISA_BUILDS:
        b0 = bonus_as_of(KAISA, build, 0.0)
        b6 = bonus_as_of(KAISA, build, LT_AS * LT_STACKS)
        p0 = period_of(KAISA, b0)
        p6 = period_of(KAISA, b6)
        w6 = windup_of(KAISA, b6, 1.0)
        flag = "FINGER CANNOT SPEND 6 STACKS" if p6 < pad.floor else "finger can spend it"
        a(
            f"  {build.label:<32}  0stk {p0:.2f}s   6stk {p6:.2f}s"
            f"   walk {p6 - w6:.2f}s   {flag}"
        )
    a("")
    a("  7.3 Tempo at 6 stacks is a 0.54–0.97s auto on these builds.")
    a("  A normal RT cadence (0.36s) is faster than every one of them.")
    a("  The old 'Tempo is too fast for a pad' problem is gone.")
    a("")

    def emit_block(title: str, champ: Champ, builds: List[Loadout], use_e: bool, windup_mod: float) -> None:
        a("-" * 78)
        a(title)
        a("-" * 78)
        a(
            f"  {'Build':<32} {'Hands':<10} {'Chaser':<12} {'Rune':<6}"
            f" {'Lived':<14} {'Dmg':>6} {'Heal':>5} {'AA':>3} {'MinGap':>7}"
        )
        for build in builds:
            for hands in HANDS:
                if hands.name == "pad fast":
                    continue  # kept in json; the table shows mouse / pad / stuck
                for cname, _cms in CHASERS:
                    for rune in RUNES:
                        key = row_key(
                            champ.name, build.label, hands.name, rune, cname, use_e, windup_mod
                        )
                        r = results[key]
                        a(
                            f"  {build.label:<32} {hands.name:<10} {cname:<12} {rune:<6}"
                            f" {fmt_time(r):<14} {r.damage:6.0f} {r.heal:5.0f}"
                            f" {r.autos:3d} {r.min_gap:7.0f}"
                        )
            a("")

    emit_block(
        "KAI'SA — STICK + RT ONLY  (E not pressed)",
        KAISA,
        KAISA_BUILDS,
        False,
        1.0,
    )
    emit_block(
        "KAI'SA — STICK + RT, ONE SUPERCHARGE when they close 80 range",
        KAISA,
        KAISA_BUILDS,
        True,
        1.0,
    )
    emit_block(
        "ASHE — STICK + RT  (20% slow for 2s on each auto, both runes)",
        ASHE,
        ASHE_BUILDS,
        False,
        1.0,
    )
    a("-" * 78)
    a("STICKY WIND-UP STRESS — Kai'Sa 3-item, pad, no E, windup modifier 0.6")
    a("  Bonus AS shrinks the wind-up slower than the period, so Tempo stands more.")
    a("  Not the base case. WR does not publish wind-up modifiers.")
    a("-" * 78)
    stress = KAISA_BUILDS[-1]
    for cname, _cms in CHASERS:
        for rune in RUNES:
            r = results[row_key(KAISA.name, stress.label, "pad", rune, cname, False, 0.6)]
            a(
                f"  {cname:<12} {rune:<6} {fmt_time(r):<14}"
                f" dmg {r.damage:6.0f}  stand {r.stand_time:.2f}s  walk {r.walk_time:.2f}s"
            )
    a("")
    a(verdict(results))
    a("")
    return "\n".join(lines) + "\n"


def _get(results: Dict[str, FightResult], build: str, hands: str, rune: str, chaser: str, e: bool, champ: str = "Kai'Sa", mod: float = 1.0) -> FightResult:
    return results[row_key(champ, build, hands, rune, chaser, e, mod)]


def verdict(results: Dict[str, FightResult]) -> str:
    """Short answer, numbers pulled from the same rows as the tables."""
    lines = []
    a = lines.append
    a("-" * 78)
    a("VERDICT")
    a("-" * 78)
    a("  On a pad, take Tempo unless Supercharge is what keeps the fight going.")
    a("  7.3 Tempo is slow enough to tap. It does not create space.")
    a("  Fleet's 20% move speed does, but only after the energize bar")
    a("  fills — a long fight, not a 2-second run-down. A ghost on")
    a("  Kai'Sa ends before either rune turns on.")
    a("")
    a("  KILL = you killed the 2800 HP body. CAUGHT = they reached 175.")
    a("  up = the 8s window ended with you untouched. Heal 0 means Fleet")
    a("  never proc'd.")
    a("")

    # Representative: boots and 3-item, pad, ghost and boots chaser, no E.
    pairs = [
        ("boots L8 greaves", "boots 415"),
        ("boots L8 greaves", "ghost 490"),
        ("3-item L15 Rageblade stacked", "boots 415"),
        ("3-item L15 Rageblade stacked", "ghost 490"),
    ]
    a("  Kai'Sa, pad (50 ms late auto, tap every 0.36s), E not pressed:")
    for build, chaser in pairs:
        f = _get(results, build, "pad", "fleet", chaser, False)
        t = _get(results, build, "pad", "tempo", chaser, False)
        a(
            f"    {build}, {chaser}:  Fleet {fmt_time(f)} / {f.damage:.0f} dmg"
            f"   Tempo {fmt_time(t)} / {t.damage:.0f} dmg"
        )

    a("")
    a("  Same hands, Supercharge pressed once when they step in:")
    for build, chaser in pairs:
        f = _get(results, build, "pad", "fleet", chaser, True)
        t = _get(results, build, "pad", "tempo", chaser, True)
        a(
            f"    {build}, {chaser}:  Fleet {fmt_time(f)} / {f.damage:.0f}"
            f"   Tempo {fmt_time(t)} / {t.damage:.0f}"
            f"   E {'yes' if t.e_used else 'no'}"
        )

    a("")
    a("  Ashe pad, Stormrazor already spending the energize bar:")
    for build, chaser in (
        ("2-item L12 Stormrazor", "ghost 490"),
        ("3-item L15 Runaan", "ghost 490"),
    ):
        f = _get(results, build, "pad", "fleet", chaser, False, champ="Ashe")
        t = _get(results, build, "pad", "tempo", chaser, False, champ="Ashe")
        a(
            f"    {build}, {chaser}:  Fleet {fmt_time(f)} / {f.damage:.0f}"
            f"   Tempo {fmt_time(t)} / {t.damage:.0f}"
        )

    ashe_f = _get(results, "3-item L15 Runaan", "pad", "fleet", "ghost 490", False, champ="Ashe")
    ashe_t = _get(results, "3-item L15 Runaan", "pad", "tempo", "ghost 490", False, champ="Ashe")
    walk_f = _get(results, "3-item L15 Rageblade stacked", "pad", "fleet", "walk 370", False)
    walk_t = _get(results, "3-item L15 Rageblade stacked", "pad", "tempo", "walk 370", False)
    run_f = _get(results, "3-item L15 Rageblade stacked", "pad", "fleet", "boots 415", False)
    run_t = _get(results, "3-item L15 Rageblade stacked", "pad", "tempo", "boots 415", False)
    e_f = _get(results, "3-item L15 Rageblade stacked", "pad", "fleet", "boots 415", True)
    e_t = _get(results, "3-item L15 Rageblade stacked", "pad", "tempo", "boots 415", True)
    e_mouse_t = _get(results, "3-item L15 Rageblade stacked", "mouse", "tempo", "boots 415", True)
    ghost_f = _get(results, "3-item L15 Rageblade stacked", "pad", "fleet", "ghost 490", False)
    ghost_t = _get(results, "3-item L15 Rageblade stacked", "pad", "tempo", "ghost 490", False)
    ghost_e_f = _get(results, "3-item L15 Rageblade stacked", "pad", "fleet", "ghost 490", True)
    ghost_e_t = _get(results, "3-item L15 Rageblade stacked", "pad", "tempo", "ghost 490", True)
    lane_f = _get(results, "lane L4 long sword", "pad", "fleet", "walk 370", False)
    lane_t = _get(results, "lane L4 long sword", "pad", "tempo", "walk 370", False)

    a("")
    a("  TAKE TEMPO when you can already hold the edge.")
    a("    Ashe slows on every auto. Stormrazor + Runaan vs ghost:")
    a(f"    Fleet {fmt_time(ashe_f)} / {ashe_f.damage:.0f}    Tempo {fmt_time(ashe_t)} / {ashe_t.damage:.0f}.")
    a("    Kai'Sa vs a 370 MS walker, 3 items, no E, pad:")
    a(f"    Fleet {fmt_time(walk_f)} / {walk_f.damage:.0f}    Tempo {fmt_time(walk_t)} / {walk_t.damage:.0f}.")
    a("    Both stay out of melee. Tempo spends the time harder.")
    a("    7.3 Tempo is only +38.4% AS at 6 stacks, and the shoulder")
    a("    button can spend it. You do not lose the kite by picking it.")
    a("")
    a("  TAKE TEMPO for a short run-down if Supercharge is down.")
    a("    A melee faster than your backswing touches you before Fleet")
    a("    energizes (heal stays 0) and before Tempo's bolt. 3 items,")
    a("    pad, no E, vs 415 MS:")
    a(f"    Fleet {fmt_time(run_f)} / {run_f.damage:.0f} (heal {run_f.heal:.0f})")
    a(f"    Tempo {fmt_time(run_t)} / {run_t.damage:.0f}.")
    a("    Same collapse, Tempo's damage. The stick gets no new gap")
    a("    from either rune in a fight this short.")
    a("")
    a("  TAKE FLEET when Supercharge keeps the fight past one energize")
    a("    and you are on the pad.")
    a("    3 items, pad, E pressed, vs 415 MS:")
    a(f"    Fleet {fmt_time(e_f)} / {e_f.damage:.0f} (heal {e_f.heal:.0f}, procs {e_f.fleet_procs})")
    a(f"    Tempo {fmt_time(e_t)} / {e_t.damage:.0f}.")
    a(f"    Same fight on a mouse, Tempo: {fmt_time(e_mouse_t)} / {e_mouse_t.damage:.0f}.")
    a("    The 50 ms late auto is the difference between Tempo killing")
    a("    them on a mouse and getting touched on the pad. Fleet's proc")
    a("    is the extra second and the heal. It still does not secure")
    a("    the kill. At 3 items E's move speed is already capped without")
    a("    Tempo, so Tempo is not making Supercharge faster.")
    a("")
    a("  NEITHER RUNE kites a ghost on Kai'Sa.")
    a("    3 items, pad, no E, ghost 490:")
    a(f"    Fleet {fmt_time(ghost_f)} / {ghost_f.damage:.0f} (heal {ghost_f.heal:.0f})")
    a(f"    Tempo {fmt_time(ghost_t)} / {ghost_t.damage:.0f}.")
    a("    With E:")
    a(f"    Fleet {fmt_time(ghost_e_f)} / {ghost_e_f.damage:.0f} (heal {ghost_e_f.heal:.0f})")
    a(f"    Tempo {fmt_time(ghost_e_t)} / {ghost_e_t.damage:.0f}.")
    a("    Too few autos to fill Fleet's bar or finish Tempo. Pressing E")
    a("    as they arrive does not fix it. You need your own Ghost or")
    a("    Flash, or to not be in auto range when theirs starts.")
    a("")
    a("  LANE (no boots) is also neither rune.")
    a(f"    Pad vs 370: Fleet {fmt_time(lane_f)} / heal {lane_f.heal:.0f}")
    a(f"    Tempo {fmt_time(lane_t)}. The bolt is not up. The small")
    a("    survival gap is attack timing, not Fleet's move speed.")
    a("")
    a("  PAD, NOT THE RUNE, IF THE MAP IS WRONG.")
    a("    'pad stuck' freezes you 0.05s on every RT. That is Mapping")
    a("    Enhancement off, or the joystick not Locked. Both runes get")
    a("    caught faster. Fix the map before you swap the keystone.")
    a("    Follow OFF. Do not hold RT. Holding RT with Follow off is")
    a("    standing still, which is neither Fleet nor Tempo.")
    a("")
    a("  ASSUMPTIONS THAT MOVE THE ANSWER")
    a("    Wind-up 18% Kai'Sa / 22% Ashe, and it scales 1:1 with attack")
    a("    speed. Not in the 7.3 notes. The stress table (modifier 0.6)")
    a("    is the case where bonus AS makes you stand a larger share")
    a("    of each auto. There Tempo gets caught sooner vs a walker")
    a("    you could previously hold. Treat that as a risk, not the")
    a("    base answer.")
    a("    Chaser runs straight at you. No dash, no Flash, no your Ghost.")
    a("    Both pages can take Ghost. It is not in the numbers.")
    a("    Kai'Sa E cast time (1.0s → 0.5s with bonus AS) is the wiki")
    a("    value. 7.3 reprinted the move-speed formula, not the cast.")
    a("    Berserker AD (10) is the approximate value from the item pass.")
    a("    Ashe slow is a flat 20% for 2s. The slow, not the rune, is")
    a("    why she holds a ghost at 3 items.")
    return "\n".join(lines)


def to_json(results: Dict[str, FightResult]) -> dict:
    rows = []
    for key, r in results.items():
        rows.append(
            {
                "key": key,
                "lived": round(r.lived, 3),
                "caught": r.caught,
                "damage": round(r.damage, 1),
                "heal": round(r.heal, 1),
                "autos": r.autos,
                "fleet_procs": r.fleet_procs,
                "min_gap": round(r.min_gap, 1),
                "end_gap": round(r.end_gap, 1),
                "stand_time": round(r.stand_time, 3),
                "walk_time": round(r.walk_time, 3),
                "e_used": r.e_used,
                "period_at_6": round(r.period_at_6, 3),
                "walk_at_6": round(r.walk_at_6, 3),
                "killed": r.killed,
            }
        )
    return {"patch": "7.3", "horizon_s": HORIZON, "rows": rows}


def sanity(results: Dict[str, FightResult]) -> None:
    """Catch an inverted gap. Damage order is a result, not a constraint."""
    slow = _get(results, "boots L8 greaves", "mouse", "tempo", "walk 370", False)
    fast = _get(results, "boots L8 greaves", "mouse", "tempo", "ghost 490", False)
    assert fast.lived < slow.lived, (slow.lived, fast.lived)

    # 6-stack period on the 3-item build is still above the 0.36s finger.
    three = _get(results, "3-item L15 Rageblade stacked", "pad", "tempo", "boots 415", False)
    assert three.period_at_6 > 0.36, three.period_at_6

    # Level curve matches the patch-note identity: 14 × per-level at level 15.
    assert abs(level_bonus_as(0.04, 15) - 0.56) < 1e-9
    assert abs(level_bonus_as(0.04, 2) - 0.0296) < 1e-9

    # Stuck map stands more than the correct pad map.
    stuck = _get(results, "boots L8 greaves", "pad stuck", "tempo", "ghost 490", False)
    pad = _get(results, "boots L8 greaves", "pad", "tempo", "ghost 490", False)
    assert stuck.stand_time > pad.stand_time

    # Fleet's heal actually fired across a full kite, not a two-auto death.
    fleet = _get(results, "boots L8 greaves", "mouse", "fleet", "walk 370", True)
    assert fleet.heal > 0 and fleet.fleet_procs > 0, (fleet.heal, fleet.fleet_procs)

    # The written verdict depends on these shapes.
    ashe_t = _get(results, "3-item L15 Runaan", "pad", "tempo", "ghost 490", False, champ="Ashe")
    ashe_f = _get(results, "3-item L15 Runaan", "pad", "fleet", "ghost 490", False, champ="Ashe")
    assert not ashe_t.caught and not ashe_f.caught
    assert ashe_t.damage > ashe_f.damage

    e_mouse_t = _get(results, "3-item L15 Rageblade stacked", "mouse", "tempo", "boots 415", True)
    e_pad_t = _get(results, "3-item L15 Rageblade stacked", "pad", "tempo", "boots 415", True)
    e_pad_f = _get(results, "3-item L15 Rageblade stacked", "pad", "fleet", "boots 415", True)
    assert e_mouse_t.killed and not e_pad_t.killed
    assert e_pad_f.heal > 0 and e_pad_f.lived > e_pad_t.lived

    short_f = _get(results, "3-item L15 Rageblade stacked", "pad", "fleet", "boots 415", False)
    assert short_f.heal == 0


def main() -> None:
    results = run_all()
    sanity(results)
    text = write_report(results)
    report_path = __file__.replace("simulate_fleet_tempo_kite.py", "report.txt")
    json_path = __file__.replace("simulate_fleet_tempo_kite.py", "results.json")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(text)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(to_json(results), f, indent=2)
    print(text)


if __name__ == "__main__":
    main()
