#!/usr/bin/env python3
"""
Wild Rift Kai'Sa — Statikk Shiv farm vs Guinsoo's Rageblade.

Patch snapshot: 7.3 kit, 7.3b Statikk (2900g, Electroshock +7), 7.3f meta.
No 7.3d/7.3f change to Kai'Sa or these two items.

Question:
  How much does Statikk help Kai'Sa clear a wave compared with Guinsoo,
  and what happens if Statikk is moved to the last item the way a Kalista
  farm pattern can afford (Rend resets; Kai'Sa Q does not)?

Sources (numbers the sim does not invent):
  - Riot patch 7.3 / 7.3b notes: Kai'Sa ratios, Statikk, Guinsoo, Nashor,
    Kraken, Terminus, Recurve, Pickaxe, Hearthbound, Dagger, Kircheis.
  - Attack speed formula and the worked example (Alacrity 18%, Berserker 35%)
    in the 7.3 notes. Kai'Sa AS coefficients match the published 0.753 / 0.952
    level 1 / 15 attack speed: ratio 0.644, base bonus 17%, per level 0.022.
  - Q missile table and the 25% extra-missile rule: League wiki WR:Kai'Sa,
    unchanged in 7.3. Evolve gates: 70 bonus AD / 80 AP / 65% bonus AS
    (WrTrueMeta kit text).
  - Energized: 6 per attack and 1 per 24 units (WR v5.3 Energized note,
    not restated in 7.3). Electroshock adds the 7.3b bonus on top.
  - Waves are 4 minions (2 melee + 2 caster, cannon replaces one caster).
    HP curve is the last published one (melee 473+44/min, caster 296+16/min,
    cannon 828+40/min). 7.3 did not change those HP values.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple
import json


GAME_MINUTES = 26

# ---------------------------------------------------------------------------
# Kit
# ---------------------------------------------------------------------------


def base_ad(level: int) -> float:
    # 7.3 base 62 → 59. Growth left at 3.5 (wiki; 7.3 did not list a growth change).
    return 59.0 + 3.5 * (level - 1)


def level_as_bonus(level: int) -> float:
    """Sum of per-level gains. Each level L→L+1 adds per_level * (0.7 + 0.04*L).

    That sum equals 14 * per_level at level 15, which is the 1400% cap in the
    7.3 attack-speed notes. The Caitlyn example uses the closed form at 15.
    """
    per = 0.022
    total = 0.0
    for left in range(1, level):
        total += 0.7 + 0.04 * left
    return per * total


def attack_speed(level: int, bonus_as: float) -> float:
    # Total AS = base + ratio * bonus, ratio == base for Kai'Sa.
    base = 0.644
    bonus = 0.17 + level_as_bonus(level) + bonus_as
    return min(2.5, base + base * bonus)


def skill_ranks(level: int) -> Dict[str, int]:
    """Q max, E second, W last. R at 5 / 9 / 13. Level cap 15, rank cap 4."""
    order = ["Q", "E", "Q", "W", "R", "Q", "Q", "E", "R", "E", "E", "W", "R", "W", "W"]
    got = order[: max(0, min(15, level))]
    return {s: got.count(s) for s in "QWER"}


def q_cooldown(rank: int, ah: float) -> float:
    base = [0, 9, 8, 7, 6][rank]
    return base * 100.0 / (100.0 + ah)


def w_cooldown(rank: int, ah: float, evolved: bool) -> float:
    base = [0, 20, 18, 16, 14][rank]
    cd = base * 100.0 / (100.0 + ah)
    # Evolved Void Seeker refunds 70% on a champion hit.
    if evolved:
        cd *= 0.30
    return cd


def chain_extra(level: int) -> int:
    """Additional Statikk bounces. Patch 7.3: 3/4/5/6 at levels 1/5/9/13.

    Primary + these extras = the wiki's 4/5/6/7 targets. A wave is 4 minions,
    so level 1 already covers the whole wave.
    """
    if level >= 13:
        return 6
    if level >= 9:
        return 5
    if level >= 5:
        return 4
    return 3


def plasma_tick(level: int, ap: float, stacks_after: int) -> float:
    """7.3 Second Skin. `stacks_after` is the stack just applied (1–5)."""
    base = 4.0 + level + 0.12 * ap
    per = 1.0 + 0.2 * level + 0.02 * ap
    return base + stacks_after * per


def plasma_pop_ratio(ap: float) -> float:
    # "(15 + 5% AP)%" with the old wiki reading "per 100 AP".
    return 0.15 + 0.05 * (ap / 100.0)


def kraken_raw(level: int, missing_frac: float) -> float:
    """Ranged Bring It Down: 120–168 by level, +0.75% per 1% HP missing, cap +75%."""
    t = (min(15, max(1, level)) - 1) / 14.0
    base = 120.0 + 48.0 * t
    return base * (1.0 + min(0.75, 0.75 * missing_frac))


def missile_raw(q_rank: int, bonus_ad: float, ap: float) -> float:
    base = [0, 40, 60, 80, 100][q_rank]
    # Wiki: 50% bonus AD + 30% AP. Minions take full damage per missile.
    return base + 0.50 * bonus_ad + 0.30 * ap


def isolated_q_raw(q_rank: int, bonus_ad: float, ap: float, evolved: bool) -> float:
    """Champions: first missile full, every extra missile 25%.

    6 missiles → 2.25x (90/135/180/225). 12 missiles → 3.75x.
    """
    one = missile_raw(q_rank, bonus_ad, ap)
    n = 12 if evolved else 6
    return one * (1.0 + 0.25 * (n - 1))


def w_raw(w_rank: int, total_ad: float, ap: float) -> float:
    # 7.3: 30/60/90/120 + 130% AD + 50% AP. AD here is total, as written.
    base = [0, 30, 60, 90, 120][w_rank]
    return base + 1.30 * total_ad + 0.50 * ap


def mitigated(raw: float, resist: float, pct_pen: float = 0.0) -> float:
    if raw <= 0:
        return 0.0
    r = resist * (1.0 - pct_pen)
    if r >= 0:
        return raw * 100.0 / (100.0 + r)
    return raw * (2.0 - 100.0 / (100.0 - r))


def alacrity_at(minute: float) -> float:
    """Legend: Alacrity, 18% fully stacked (7.3 attack-speed example).

    A farming marksman is stacked around the mid game. Not counted for
    Living Weapon — evolve checks item stats only.
    """
    if minute <= 4:
        return 0.0
    return min(0.18, 0.018 * (minute - 4))


# ---------------------------------------------------------------------------
# Items
# ---------------------------------------------------------------------------


@dataclass
class Item:
    name: str
    ad: float = 0.0
    ap: float = 0.0
    ah: float = 0.0
    as_pct: float = 0.0
    ms_flat: float = 0.0
    ms_pct: float = 0.0
    statikk: bool = False
    guinsoo: bool = False
    nashor: bool = False
    kraken: bool = False
    terminus: bool = False


@dataclass(frozen=True)
class Buy:
    name: str
    cost: int
    result: Item
    consumes: Tuple[str, ...] = ()


def _ls() -> Item:
    return Item("Long Sword", ad=12)


def _dagger() -> Item:
    return Item("Dagger", as_pct=0.12)


def _pickaxe() -> Item:
    return Item("Pickaxe", ad=20)


def _recurve() -> Item:
    return Item("Recurve Bow", as_pct=0.20)


def _kircheis() -> Item:
    return Item("Kircheis Shard", as_pct=0.20)


def _tome() -> Item:
    return Item("Amplifying Tome", ap=20)


def _aether() -> Item:
    # Completed Statikk is 40 AP. Aether Wisp's own AP is not printed in the
    # 7.3 notes (only 4% move speed). 25 AP is the component estimate.
    return Item("Aether Wisp", ap=25, ms_pct=0.04)


def _wand() -> Item:
    return Item("Blasting Wand", ap=45)


def _codex() -> Item:
    # Fiendish Codex stats are not reprinted in 7.3 (price 900). 25 AP + 10 AH.
    return Item("Fiendish Codex", ap=25, ah=10)


def _hearth() -> Item:
    return Item("Hearthbound Axe", ad=20, as_pct=0.15)


def _boots() -> Item:
    return Item("Boots", ms_flat=25)


def finish_statikk() -> Item:
    return Item("Statikk Shiv", ad=40, ap=40, as_pct=0.30, ms_pct=0.04, statikk=True)


def finish_guinsoo() -> Item:
    return Item("Guinsoo's Rageblade", ad=35, ap=30, as_pct=0.30, guinsoo=True)


def finish_nashor() -> Item:
    return Item("Nashor's Tooth", ap=80, as_pct=0.50, ah=15, nashor=True)


def finish_kraken() -> Item:
    return Item("Kraken Slayer", ad=45, as_pct=0.35, ms_pct=0.04, kraken=True)


def finish_terminus() -> Item:
    return Item("Terminus", ad=35, as_pct=0.35, terminus=True)


def finish_greaves() -> Item:
    # 35% AS is in the 7.3 attack-speed example. 1500g matches this repo's
    # 7.3 boots snapshot; the marksman notes did not restate the price.
    return Item("Berserker's Greaves", as_pct=0.35, ms_flat=25)


def steps_statikk(buy_long_sword: bool) -> List[Buy]:
    # Pickaxe 800 = Long Sword 500 + 300. Kircheis 800 = Dagger 400 + 400.
    # Aether 950 + combine 350. Full price 2900 (7.3b).
    steps: List[Buy] = []
    if buy_long_sword:
        steps.append(Buy("Long Sword", 500, _ls()))
    steps.extend(
        [
            Buy("Pickaxe", 300, _pickaxe(), ("Long Sword",)),
            Buy("Dagger", 400, _dagger()),
            Buy("Kircheis Shard", 400, _kircheis(), ("Dagger",)),
            Buy("Aether Wisp", 950, _aether()),
            Buy(
                "Statikk Shiv",
                350,
                finish_statikk(),
                ("Pickaxe", "Kircheis Shard", "Aether Wisp"),
            ),
        ]
    )
    return steps


def steps_guinsoo(buy_long_sword: bool) -> List[Buy]:
    # Tome 500 + Recurve 900 + Pickaxe 800 + 800 = 3000.
    steps: List[Buy] = []
    if buy_long_sword:
        steps.append(Buy("Long Sword", 500, _ls()))
    steps.extend(
        [
            Buy("Pickaxe", 300, _pickaxe(), ("Long Sword",)),
            Buy("Dagger", 400, _dagger()),
            Buy("Recurve Bow", 500, _recurve(), ("Dagger",)),
            Buy("Amplifying Tome", 500, _tome()),
            Buy(
                "Guinsoo's Rageblade",
                800,
                finish_guinsoo(),
                ("Pickaxe", "Recurve Bow", "Amplifying Tome"),
            ),
        ]
    )
    return steps


def steps_nashor() -> List[Buy]:
    # Recurve 900 + Blasting Wand 800 + Codex 900 + 300 = 2900.
    return [
        Buy("Dagger", 400, _dagger()),
        Buy("Recurve Bow", 500, _recurve(), ("Dagger",)),
        Buy("Blasting Wand", 800, _wand()),
        Buy("Fiendish Codex", 900, _codex()),
        Buy(
            "Nashor's Tooth",
            300,
            finish_nashor(),
            ("Recurve Bow", "Blasting Wand", "Fiendish Codex"),
        ),
    ]


def steps_kraken() -> List[Buy]:
    # Recurve 900 + Hearthbound 1200 + Long Sword 500 + 300 = 2900.
    return [
        Buy("Long Sword", 500, _ls()),
        Buy("Dagger", 400, _dagger()),
        Buy("Hearthbound Axe", 300, _hearth(), ("Long Sword", "Dagger")),
        Buy("Dagger", 400, _dagger()),
        Buy("Recurve Bow", 500, _recurve(), ("Dagger",)),
        Buy("Long Sword", 500, _ls()),
        Buy(
            "Kraken Slayer",
            300,
            finish_kraken(),
            ("Hearthbound Axe", "Recurve Bow", "Long Sword"),
        ),
    ]


def steps_terminus() -> List[Buy]:
    # Recurve 900 + Hearthbound 1200 + 900 = 3000.
    return [
        Buy("Long Sword", 500, _ls()),
        Buy("Dagger", 400, _dagger()),
        Buy("Hearthbound Axe", 300, _hearth(), ("Long Sword", "Dagger")),
        Buy("Dagger", 400, _dagger()),
        Buy("Recurve Bow", 500, _recurve(), ("Dagger",)),
        Buy("Terminus", 900, finish_terminus(), ("Hearthbound Axe", "Recurve Bow")),
    ]


def steps_greaves() -> List[Buy]:
    return [
        Buy("Boots", 500, _boots()),
        Buy("Berserker's Greaves", 1000, finish_greaves(), ("Boots",)),
    ]


def build_statikk_rush() -> List[Buy]:
    # Starting Long Sword feeds Statikk. Chain first.
    return (
        steps_statikk(False)
        + steps_greaves()
        + steps_guinsoo(True)
        + steps_nashor()
        + steps_kraken()
        + steps_terminus()
    )


def build_guinsoo_then_statikk() -> List[Buy]:
    # Same items, Guinsoo finished before the chain.
    return (
        steps_guinsoo(False)
        + steps_greaves()
        + steps_statikk(True)
        + steps_nashor()
        + steps_kraken()
        + steps_terminus()
    )


def build_statikk_last() -> List[Buy]:
    # Kalista-style delay: single-target on-hit first, chain in the last slot.
    # Kai'Sa still wants Nashor (W evolve + on-hit). Statikk is slot 6.
    return (
        steps_guinsoo(False)
        + steps_greaves()
        + steps_nashor()
        + steps_kraken()
        + steps_terminus()
        + steps_statikk(True)
    )


FINISHED = (
    "Statikk Shiv",
    "Guinsoo's Rageblade",
    "Nashor's Tooth",
    "Kraken Slayer",
    "Terminus",
    "Berserker's Greaves",
)


def gold_at(t: float) -> float:
    """Farming dragon lane, no kills. Start 500.

    Early rate is a clean last-hit lane (~380 gpm). It rises after the first
    item because plates and a shoved wave are worth more — the clock itself
    does NOT pay Statikk extra, so the clear-time gap is not double-counted
    as gold.
    """
    if t <= 0:
        return 500.0
    segments = (
        (0.0, 8.0, 380.0),
        (8.0, 14.0, 520.0),
        (14.0, 20.0, 590.0),
        (20.0, 40.0, 640.0),
    )
    gold = 500.0
    for start, end, rate in segments:
        if t <= start:
            break
        gold += (min(t, end) - start) * rate
    return gold


def level_at(minute: float) -> int:
    # Dragon lane, not a solo lane. 15 by the low 20s.
    table = {
        1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7, 7: 7, 8: 8,
        9: 9, 10: 9, 11: 10, 12: 11, 13: 11, 14: 12,
        15: 12, 16: 13, 17: 13, 18: 14, 19: 14, 20: 15,
        21: 15, 22: 15, 23: 15, 24: 15, 25: 15, 26: 15,
    }
    m = int(minute)
    return table.get(m, 15 if m > 26 else 1)


def minion_max_hp(kind: str, minute: float) -> float:
    if kind == "melee":
        return 473.0 + 44.0 * minute
    if kind == "caster":
        return 296.0 + 16.0 * minute
    if kind == "cannon":
        return 828.0 + 40.0 * minute
    raise KeyError(kind)


# ---------------------------------------------------------------------------
# Combat
# ---------------------------------------------------------------------------


@dataclass
class Unit:
    kind: str
    max_hp: float
    hp: float
    armor: float
    mr: float
    plasma: int = 0
    plasma_t: float = -999.0
    monster: bool = False


@dataclass
class Kit:
    level: int
    items: List[Item]
    ad: float
    bonus_ad: float
    ap: float
    ah: float
    item_as: float
    ms: float
    statikk: bool
    guinsoo: bool
    nashor: bool
    kraken: bool
    terminus: bool
    q_rank: int
    w_rank: int
    e_rank: int
    q_evo: bool
    w_evo: bool
    e_evo: bool
    alacrity: float


def make_kit(level: int, items: Sequence[Item], alacrity: float = 0.0) -> Kit:
    ranks = skill_ranks(level)
    ad_b = sum(i.ad for i in items)
    ap = sum(i.ap for i in items)
    item_as = sum(i.as_pct for i in items)
    ms_flat = sum(i.ms_flat for i in items)
    ms_pct = sum(i.ms_pct for i in items)
    return Kit(
        level=level,
        items=list(items),
        ad=base_ad(level) + ad_b,
        bonus_ad=ad_b,
        ap=ap,
        ah=sum(i.ah for i in items),
        item_as=item_as,
        ms=(340.0 + ms_flat) * (1.0 + ms_pct),
        statikk=any(i.statikk for i in items),
        guinsoo=any(i.guinsoo for i in items),
        nashor=any(i.nashor for i in items),
        kraken=any(i.kraken for i in items),
        terminus=any(i.terminus for i in items),
        q_rank=ranks["Q"],
        w_rank=ranks["W"],
        e_rank=ranks["E"],
        q_evo=ad_b >= 70.0,
        w_evo=ap >= 80.0,
        e_evo=item_as >= 0.65,
        alacrity=alacrity,
    )


def kit_as(kit: Kit, guinsoo_stacks: int, t: float, e_until: float) -> float:
    extra = kit.alacrity + 0.08 * guinsoo_stacks
    if t < e_until and kit.e_rank > 0:
        extra += [0, 0.40, 0.50, 0.60, 0.70][kit.e_rank]
    return attack_speed(kit.level, kit.item_as + extra)


def fresh_wave(kind: str, minute: float, armor: float, mr: float) -> List[Unit]:
    if kind == "standard":
        parts = ("melee", "melee", "caster", "caster")
    elif kind == "cannon":
        parts = ("melee", "melee", "caster", "cannon")
    else:
        raise KeyError(kind)
    units = []
    for part in parts:
        hp = minion_max_hp(part, minute)
        units.append(Unit(part, hp, hp, armor, mr))
    return units


def _deal(unit: Unit, amount: float) -> float:
    taken = min(max(unit.hp, 0.0), max(amount, 0.0))
    unit.hp -= taken
    return taken


def _apply_plasma(unit: Unit, n: int, t: float, kit: Kit, pen: float) -> float:
    if t - unit.plasma_t > 4.0:
        unit.plasma = 0
    total = 0.0
    for _ in range(n):
        if unit.hp <= 0:
            break
        unit.plasma += 1
        unit.plasma_t = t
        raw = plasma_tick(kit.level, kit.ap, unit.plasma)
        total += _deal(unit, mitigated(raw, unit.mr, pen))
        if unit.plasma >= 5 and unit.hp > 0:
            missing = unit.max_hp - unit.hp
            raw_pop = missing * plasma_pop_ratio(kit.ap)
            if unit.monster:
                raw_pop = min(400.0, raw_pop)
            total += _deal(unit, mitigated(raw_pop, unit.mr, pen))
            unit.plasma = 0
    return total


def _on_hit(unit: Unit, t: float, kit: Kit, pen: float) -> float:
    total = 0.0
    if kit.guinsoo:
        total += _deal(unit, mitigated(30.0, unit.mr, pen))
    if kit.nashor:
        total += _deal(unit, mitigated(15.0 + 0.20 * kit.ap, unit.mr, pen))
    if kit.terminus:
        total += _deal(unit, mitigated(30.0, unit.mr, pen))
    total += _apply_plasma(unit, 1, t, kit, pen)
    return total


@dataclass
class Clear:
    seconds: float
    caster_seconds: float
    energized_procs: int
    max_targets_one_auto: int
    finished: bool
    # HP removed from the whole wave by t=1s, and on the first auto.
    # Full-clear time hides the shove: the last melee often dies on the same
    # Q cooldown either way. The first second is the chain.
    removed_1s: float
    first_auto: float
    wave_hp: float


def clear_wave(
    kit: Kit,
    minute: float,
    wave: str,
    use_e: bool = False,
    armor: float = 0.0,
    mr: float = 0.0,
) -> Clear:
    """Solo clear. Walk up fully Energized. Lightning auto, then Q, then autos.

    Stutter-step moves at 45% of move speed, which refills Energized.
    Kircheis components do not chain — only the finished Shiv does.
    """
    minions = fresh_wave(wave, minute, armor, mr)
    wave_hp = sum(m.max_hp for m in minions)
    energy = 100.0 if kit.statikk else 0.0
    g_stacks = 0
    phantom_n = 0
    kraken_n = 0
    procs = 0
    widest = 1
    opened = False
    first_auto = 0.0
    removed_1s = 0.0
    saw_1s = False
    caster_t: Optional[float] = None
    e_until = 4.0 if use_e else -1.0
    next_auto = 0.0
    q_ready = 0.0
    # (impact_time, unit, raw physical before the 35% minion amp)
    pending: List[Tuple[float, Unit, float]] = []
    dt = 0.02
    steps = int(25.0 / dt)
    full_t = 25.0
    finished = False

    def casters_down(now: float) -> None:
        nonlocal caster_t
        if caster_t is None and all(m.hp <= 0 for m in minions if m.kind == "caster"):
            caster_t = now

    for step in range(steps + 1):
        t = step * dt
        if pending:
            still = []
            for impact, unit, raw in pending:
                if impact <= t + 1e-9:
                    if unit.hp > 0:
                        amp = 1.5 if (unit.hp / unit.max_hp) < 0.35 else 1.0
                        _deal(unit, mitigated(raw * amp, unit.armor, 0.0))
                else:
                    still.append((impact, unit, raw))
            pending = still
            casters_down(t)
        if not saw_1s and t + 1e-9 >= 1.0:
            removed_1s = wave_hp - sum(max(m.hp, 0.0) for m in minions)
            saw_1s = True
        if all(m.hp <= 0 for m in minions):
            full_t = t
            finished = True
            break

        if t + 1e-9 >= next_auto:
            alive = [m for m in minions if m.hp > 0]
            primary = min(alive, key=lambda m: (m.hp / m.max_hp, m.max_hp))
            hp_before = sum(max(m.hp, 0.0) for m in minions)
            energized = kit.statikk and energy >= 100.0 - 1e-6
            if energized:
                energy = 0.0
                procs += 1
            kraken_n += 1
            missing = 1.0 - primary.hp / primary.max_hp
            _deal(primary, mitigated(kit.ad, primary.armor, 0.0))
            if kit.kraken and kraken_n % 3 == 0:
                _deal(primary, mitigated(kraken_raw(kit.level, missing), primary.armor, 0.0))
            if energized:
                _deal(primary, mitigated(90.0, primary.mr, 0.0))
            _on_hit(primary, t, kit, 0.0)
            do_phantom = False
            if kit.guinsoo:
                if g_stacks >= 4:
                    phantom_n += 1
                    do_phantom = phantom_n % 3 == 0
                else:
                    g_stacks += 1
            if do_phantom and primary.hp > 0:
                _on_hit(primary, t, kit, 0.0)
            targets = 1
            if energized:
                others = [m for m in minions if m.hp > 0 and m is not primary]
                splash = others[: chain_extra(kit.level)]
                targets += len(splash)
                for m in splash:
                    _deal(m, mitigated(90.0, m.mr, 0.0))
                    if m.hp > 0:
                        _on_hit(m, t, kit, 0.0)
            widest = max(widest, targets)
            if first_auto == 0.0:
                first_auto = hp_before - sum(max(m.hp, 0.0) for m in minions)
            if kit.statikk:
                energy = min(100.0, energy + 6.0 + 7.0)
            opened = True
            next_auto = t + 1.0 / kit_as(kit, g_stacks, t, e_until)
            casters_down(t)
            if all(m.hp <= 0 for m in minions):
                full_t = t
                finished = True
                break

        if opened and kit.q_rank > 0 and t + 1e-9 >= q_ready:
            alive = [m for m in minions if m.hp > 0]
            if alive:
                n = 12 if kit.q_evo else 6
                base_n = n // len(alive)
                extra_n = n % len(alive)
                order = sorted(alive, key=lambda m: (m.hp / m.max_hp, m.max_hp))
                counts = {id(m): base_n for m in alive}
                for m in order[:extra_n]:
                    counts[id(m)] += 1
                raw = missile_raw(kit.q_rank, kit.bonus_ad, kit.ap)
                delay = 0.40
                for m in order:
                    for _ in range(counts[id(m)]):
                        pending.append((t + delay, m, raw))
                        delay += 0.08
                q_ready = t + q_cooldown(kit.q_rank, kit.ah)

        if kit.statikk and energy < 100.0:
            energy = min(100.0, energy + kit.ms * 0.45 / 24.0 * dt)

    if caster_t is None:
        caster_t = full_t
    if not saw_1s:
        removed_1s = wave_hp - sum(max(m.hp, 0.0) for m in minions)
    return Clear(
        full_t, caster_t, procs, widest, finished, removed_1s, first_auto, wave_hp
    )


@dataclass
class Fight:
    damage: float
    ttk: Optional[float]
    target_hp: float


def fight_target(kind: str, minute: float, level: int) -> Unit:
    if kind == "squishy":
        hp = 640.0 + 105.0 * (level - 1) + 18.0 * minute
        armor = 32.0 + 3.2 * (level - 1)
        mr = 30.0 + 1.3 * (level - 1)
        if minute >= 14:
            armor += 18.0
            mr += 12.0
    elif kind == "frontline":
        hp = 780.0 + 125.0 * (level - 1) + 90.0 * max(0.0, minute - 6)
        armor = 38.0 + 3.5 * (level - 1) + min(140.0, 9.0 * max(0.0, minute - 8))
        mr = 32.0 + 1.6 * (level - 1) + min(80.0, 6.0 * max(0.0, minute - 10))
    else:
        raise KeyError(kind)
    return Unit(kind, hp, hp, armor, mr)


def fight(
    kit: Kit,
    minute: float,
    target_kind: str,
    abilities: bool,
    seconds: float = 8.0,
) -> Fight:
    """8s all-in. Ability mode opens with W, then Q and autos, Supercharge up for 4s.

    Auto mode is items only: no W, no Q, no E. Same Energized opener.
    """
    target = fight_target(target_kind, minute, kit.level)
    energy = 100.0 if kit.statikk else 0.0
    g_stacks = 0
    phantom_n = 0
    kraken_n = 0
    dark = 0
    next_dark = False
    dealt = 0.0
    ttk: Optional[float] = None
    e_until = 4.0 if abilities else -1.0
    next_auto = 0.35 if abilities else 0.0
    next_w = 0.0 if abilities and kit.w_rank > 0 else 1e9
    w_land: Optional[float] = None
    q_ready = 0.35 if abilities else 1e9
    q_land: Optional[float] = None
    dt = 0.02
    steps = int(seconds / dt)

    def pen() -> float:
        return 0.10 * dark

    def note(now: float) -> None:
        nonlocal ttk
        if target.hp <= 0 and ttk is None:
            ttk = now

    for step in range(steps + 1):
        t = round(step * dt, 4)
        if t > seconds + 1e-9:
            break
        if w_land is not None and t + 1e-9 >= w_land:
            if target.hp > 0:
                raw = w_raw(kit.w_rank, kit.ad, kit.ap)
                dealt += _deal(target, mitigated(raw, target.mr, pen()))
                stacks = 3 if kit.w_evo else 2
                dealt += _apply_plasma(target, stacks, t, kit, pen())
            w_land = None
            note(t)
        if q_land is not None and t + 1e-9 >= q_land:
            if target.hp > 0 and kit.q_rank > 0:
                raw = isolated_q_raw(kit.q_rank, kit.bonus_ad, kit.ap, kit.q_evo)
                dealt += _deal(target, mitigated(raw, target.armor, pen()))
            q_land = None
            note(t)
        if target.hp <= 0:
            break

        if t + 1e-9 >= next_w and w_land is None:
            w_land = t + 0.35
            cd = w_cooldown(kit.w_rank, kit.ah, kit.w_evo)
            next_w = w_land + cd

        if t + 1e-9 >= next_auto and target.hp > 0:
            if kit.terminus:
                if next_dark:
                    dark = min(3, dark + 1)
                next_dark = not next_dark
            energized = kit.statikk and energy >= 100.0 - 1e-6
            if energized:
                energy = 0.0
            kraken_n += 1
            missing = 1.0 - target.hp / target.max_hp
            dealt += _deal(target, mitigated(kit.ad, target.armor, pen()))
            if kit.kraken and kraken_n % 3 == 0 and target.hp > 0:
                dealt += _deal(
                    target, mitigated(kraken_raw(kit.level, missing), target.armor, pen())
                )
            bolt = 60.0 if target.kind != "minion" else 90.0
            if energized and target.hp > 0:
                dealt += _deal(target, mitigated(bolt, target.mr, pen()))
            if target.hp > 0:
                dealt += _on_hit(target, t, kit, pen())
            do_phantom = False
            if kit.guinsoo:
                if g_stacks >= 4:
                    phantom_n += 1
                    do_phantom = phantom_n % 3 == 0
                else:
                    g_stacks += 1
            if do_phantom and target.hp > 0:
                dealt += _on_hit(target, t, kit, pen())
            if kit.statikk:
                energy = min(100.0, energy + 6.0 + 7.0)
            next_auto = t + 1.0 / kit_as(kit, g_stacks, t, e_until)
            note(t)
            if target.hp <= 0:
                break

        if abilities and kit.q_rank > 0 and q_land is None and t + 1e-9 >= q_ready and t >= 0.35:
            q_land = t + 0.40
            q_ready = t + q_cooldown(kit.q_rank, kit.ah)

        if kit.statikk and energy < 100.0:
            energy = min(100.0, energy + kit.ms * 0.45 / 24.0 * dt)

    return Fight(dealt, ttk, target.max_hp)


# ---------------------------------------------------------------------------
# Timeline
# ---------------------------------------------------------------------------


@dataclass
class Snapshot:
    minute: int
    gold: int
    level: int
    owned: List[str]
    finished: List[str]
    bonus_ad: float
    ap: float
    item_as: float
    q_evo: bool
    w_evo: bool
    e_evo: bool
    clear_standard: float
    clear_cannon: float
    caster_standard: float
    shove_1s: float
    first_auto: float
    ttk_squishy: Optional[float]
    dmg_front: float
    auto_front: float


@dataclass
class Completion:
    item: str
    minute: float


def _consume(owned: List[Item], names: Sequence[str]) -> None:
    for name in names:
        idx = next(i for i, it in enumerate(owned) if it.name == name)
        owned.pop(idx)


def simulate_build(buys: Sequence[Buy]) -> Tuple[List[Snapshot], List[Completion]]:
    owned: List[Item] = [_ls()]
    spent = 500.0
    index = 0
    completions: List[Completion] = []
    snaps: List[Snapshot] = []
    dt = 0.05
    steps = int(GAME_MINUTES / dt)
    seen_minute = set()

    def maybe_buy(t: float) -> None:
        nonlocal index, spent
        while index < len(buys) and gold_at(t) + 1e-6 >= spent + buys[index].cost:
            buy = buys[index]
            _consume(owned, buy.consumes)
            owned.append(buy.result)
            spent += buy.cost
            index += 1
            if buy.name in FINISHED:
                completions.append(Completion(buy.name, round(t, 2)))

    def shoot(minute: int) -> None:
        lvl = level_at(minute)
        kit = make_kit(lvl, owned, alacrity_at(minute))
        std = clear_wave(kit, float(minute), "standard")
        can = clear_wave(kit, float(minute), "cannon")
        burst = fight(kit, float(minute), "squishy", abilities=True)
        front = fight(kit, float(minute), "frontline", abilities=True)
        autos = fight(kit, float(minute), "frontline", abilities=False)
        finished = [n for n in FINISHED if any(i.name == n for i in owned)]
        snaps.append(
            Snapshot(
                minute=minute,
                gold=int(gold_at(minute)),
                level=lvl,
                owned=[i.name for i in owned],
                finished=finished,
                bonus_ad=kit.bonus_ad,
                ap=kit.ap,
                item_as=kit.item_as,
                q_evo=kit.q_evo,
                w_evo=kit.w_evo,
                e_evo=kit.e_evo,
                clear_standard=std.seconds,
                clear_cannon=can.seconds,
                caster_standard=std.caster_seconds,
                shove_1s=std.removed_1s,
                first_auto=std.first_auto,
                ttk_squishy=burst.ttk,
                dmg_front=front.damage,
                auto_front=autos.damage,
            )
        )

    maybe_buy(0.0)
    shoot(0)
    seen_minute.add(0)
    for step in range(1, steps + 1):
        t = round(step * dt, 2)
        maybe_buy(t)
        if abs(t - round(t)) < 1e-6:
            minute = int(round(t))
            if minute not in seen_minute and minute <= GAME_MINUTES:
                shoot(minute)
                seen_minute.add(minute)
    return snaps, completions


def first_time(events: Sequence[Completion], name: str) -> Optional[float]:
    for ev in events:
        if ev.item == name:
            return ev.minute
    return None


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------


def _sec(v: float) -> str:
    if v >= 24.9:
        return ">25s"
    return f"{v:.1f}s"


def _ttk(v: Optional[float]) -> str:
    if v is None:
        return "lives"
    return f"{v:.1f}s"


def _flags(s: Snapshot) -> str:
    marks = []
    if s.q_evo:
        marks.append("Q")
    if s.w_evo:
        marks.append("W")
    if s.e_evo:
        marks.append("E")
    return "+".join(marks) if marks else "-"


def duel_rows() -> List[str]:
    """Item-for-item, so the gold clock cannot hide the mechanic."""
    greaves = finish_greaves()
    rows = []

    def line(label: str, level: int, minute: float, items: Sequence[Item], alacrity: float) -> str:
        kit = make_kit(level, items, alacrity)
        std = clear_wave(kit, minute, "standard")
        can = clear_wave(kit, minute, "cannon")
        burst = fight(kit, minute, "squishy", True)
        front = fight(kit, minute, "frontline", True)
        autos = fight(kit, minute, "frontline", False)
        evo = []
        if kit.q_evo:
            evo.append("Q")
        if kit.w_evo:
            evo.append("W")
        if kit.e_evo:
            evo.append("E")
        return (
            f"  {label:<28} {_sec(std.caster_seconds):>7} {_sec(std.seconds):>6} "
            f"{_sec(can.seconds):>6} {std.removed_1s:7.0f} {std.first_auto:6.0f} "
            f"{_ttk(burst.ttk):>6} {front.damage:7.0f} {autos.damage:7.0f}  "
            f"{'+'.join(evo) or '-':<5}"
        )

    rows.append(
        "  Kit                          casters   full cannon   dmg@1s  1stAA  squish  front  autos  evo"
    )
    rows.append("  " + "-" * 96)
    rows.append("  Level 9, minute-9 minions, no boots, Alacrity off. One finished item.")
    rows.append(line("Statikk only", 9, 9, [finish_statikk()], 0.0))
    rows.append(line("Guinsoo only", 9, 9, [finish_guinsoo()], 0.0))
    rows.append(line("Long Sword only", 9, 9, [_ls()], 0.0))
    rows.append("")
    rows.append("  Same gold 7400: two legendaries + Berserker's. Level 12, minute 15.")
    rows.append(
        line(
            "Statikk + Guinsoo + Greaves",
            12,
            15,
            [finish_statikk(), finish_guinsoo(), greaves],
            0.18,
        )
    )
    rows.append(
        line(
            "Guinsoo + Nashor + Greaves",
            12,
            15,
            [finish_guinsoo(), finish_nashor(), greaves],
            0.18,
        )
    )
    rows.append("")
    rows.append("  Same gold ~10300: three legendaries + Greaves. Level 14, minute 18.")
    rows.append(
        line(
            "Shiv Guinsoo Nashor Greaves",
            14,
            18,
            [finish_statikk(), finish_guinsoo(), finish_nashor(), greaves],
            0.18,
        )
    )
    rows.append(
        line(
            "Guinsoo Nashor Kraken Greaves",
            14,
            18,
            [finish_guinsoo(), finish_nashor(), finish_kraken(), greaves],
            0.18,
        )
    )
    rows.append("")
    rows.append("  Slot-6 check, level 15, minute 24 minions. Full damage build.")
    rows.append(
        line(
            "Chain in the build",
            15,
            24,
            [
                finish_statikk(),
                finish_guinsoo(),
                finish_nashor(),
                finish_kraken(),
                finish_terminus(),
                greaves,
            ],
            0.18,
        )
    )
    rows.append(
        line(
            "Same build, no Statikk",
            15,
            24,
            [finish_guinsoo(), finish_nashor(), finish_kraken(), finish_terminus(), greaves],
            0.18,
        )
    )
    return rows


def summarize(
    results: Dict[str, List[Snapshot]],
    events: Dict[str, List[Completion]],
) -> str:
    rush = "Statikk → Guinsoo"
    second = "Guinsoo → Statikk"
    last = "Statikk last"
    lines: List[str] = []
    a = lines.append
    a("=" * 96)
    a("WILD RIFT KAI'SA — STATIKK FARM vs GUINSOO, AND STATIKK LAST")
    a("Patch 7.3 kit / 7.3b Statikk / 7.3f shop. Dragon lane, Q → E → W.")
    a("=" * 96)
    a("")
    a("QUESTION")
    a("  Guinsoo's Rageblade (the 'gusinoo' slot) is the single-target on-hit item.")
    a("  Statikk Shiv is the chain. How much farm does the chain actually buy,")
    a("  and what happens if it is moved to the last item the way Kalista can")
    a("  farm without it?")
    a("")
    a("HOW THE CLEAR WORKS")
    a("  A Wild Rift wave is 4 minions, not 6. Statikk's bolt hits 4 targets from")
    a("  level 1 (3 extra bounces + the one you auto) for 90 magic on minions, and")
    a("  on-hits ride the bounces. Guinsoo hits the minion you clicked: +30 magic,")
    a("  and a phantom hit only after 4 Rageblade stacks, only on that minion.")
    a("  Q throws 6 missiles across whoever is standing there (12 if evolved) and")
    a("  does not reset on kill. Minions under 35% HP take 150% from those missiles.")
    a("  Kalista's Rend DOES reset on a minion kill, so she can front-load Guinsoo")
    a("  or Terminus and still chain the wave. Kai'Sa cannot copy that and keep")
    a("  the same shove.")
    a("")
    a("ONE-ITEM AND EQUAL-GOLD DUELS")
    a("  casters = seconds until both casters are dead (the shove). full = last minion.")
    a("  cannon = full cannon-wave clear. dmg@1s = HP removed from a standard wave")
    a("  in the first second. 1stAA = damage of the opening auto, including the bolt.")
    a("  squish = time to kill a bot laner in an 8s W+Q+auto all-in, or 'lives'.")
    a("  front = damage onto a frontliner in that all-in. autos = 8s of autos only.")
    a("  evo = Living Weapon from items (Q 70 bonus AD, W 80 AP, E 65% item AS).")
    for row in duel_rows():
        a(row)
    a("")
    a("CLOCK — SAME FARM, NO KILLS")
    a("  Gold is identical on every path. Faster clears are NOT given extra gold,")
    a("  so this understates the plates and roams the chain creates.")
    a(f"  Start 500, then 380 / 520 / 590 / 640 gpm across 0–8 / 8–14 / 14–20 / 20+.")
    a("")
    a(f"  {'Item':<22} {'Statikk first':>14} {'Guinsoo first':>14} {'Statikk last':>14}")
    for item in FINISHED:
        cells = []
        for name in (rush, second, last):
            t = first_time(events[name], item)
            cells.append(f"{t:.2f}m" if t is not None else "—")
        a(f"  {item:<22} {cells[0]:>14} {cells[1]:>14} {cells[2]:>14}")
    a("")
    a("  Minute snapshots. clear = seconds to kill a standard wave (the last melee).")
    a("  1s = HP already removed from that wave at one second — the shove, which")
    a("  moves even when the last melee dies on the same Q. squish = all-in kill")
    a("  time. front = 8s frontline damage. evo = Q/W/E.")
    a(f"  {'m':>3} {'gold':>6}  {'rush clear':>10} {'2nd clear':>10} {'last clear':>10}  "
      f"{'rush 1s':>8} {'last 1s':>8}  {'rush kill':>9} {'last kill':>9}  "
      f"{'rush fr':>7} {'last fr':>7}  rush evo / last evo")
    for i in range(6, GAME_MINUTES + 1):
        rs, ss, ls = results[rush][i], results[second][i], results[last][i]
        a(
            f"  {i:3d} {rs.gold:6d}  {_sec(rs.clear_standard):>10} "
            f"{_sec(ss.clear_standard):>10} {_sec(ls.clear_standard):>10}  "
            f"{rs.shove_1s:8.0f} {ls.shove_1s:8.0f}  "
            f"{_ttk(rs.ttk_squishy):>9} {_ttk(ls.ttk_squishy):>9}  "
            f"{rs.dmg_front:7.0f} {ls.dmg_front:7.0f}  "
            f"{_flags(rs):<7} {_flags(ls)}"
        )
    a("")

    # Verdict numbers from the duels, recomputed so the text cannot drift.
    kit_s = make_kit(9, [finish_statikk()], 0.0)
    kit_g = make_kit(9, [finish_guinsoo()], 0.0)
    s_wave = clear_wave(kit_s, 9, "standard")
    g_wave = clear_wave(kit_g, 9, "standard")
    s_can = clear_wave(kit_s, 9, "cannon")
    g_can = clear_wave(kit_g, 9, "cannon")
    s_tough = clear_wave(kit_s, 9, "cannon", armor=15, mr=20)
    g_tough = clear_wave(kit_g, 9, "cannon", armor=15, mr=20)
    s_auto = fight(kit_s, 9, "frontline", False)
    g_auto = fight(kit_g, 9, "frontline", False)
    mid_chain = make_kit(
        12, [finish_statikk(), finish_guinsoo(), finish_greaves()], 0.18
    )
    mid_nash = make_kit(
        12, [finish_guinsoo(), finish_nashor(), finish_greaves()], 0.18
    )
    mid_c = clear_wave(mid_chain, 15, "cannon")
    mid_n = clear_wave(mid_nash, 15, "cannon")
    mid_std_c = clear_wave(mid_chain, 15, "standard")
    mid_std_n = clear_wave(mid_nash, 15, "standard")
    mid_cf = fight(mid_chain, 15, "frontline", True)
    mid_nf = fight(mid_nash, 15, "frontline", True)
    mid_cs = fight(mid_chain, 15, "squishy", True)
    mid_ns = fight(mid_nash, 15, "squishy", True)
    mid_auto_c = fight(mid_chain, 15, "frontline", False)
    mid_auto_n = fight(mid_nash, 15, "frontline", False)
    full = make_kit(
        15,
        [
            finish_statikk(),
            finish_guinsoo(),
            finish_nashor(),
            finish_kraken(),
            finish_terminus(),
            finish_greaves(),
        ],
        0.18,
    )
    no_shiv = make_kit(
        15,
        [finish_guinsoo(), finish_nashor(), finish_kraken(), finish_terminus(), finish_greaves()],
        0.18,
    )
    full_c = clear_wave(full, 24, "cannon")
    none_c = clear_wave(no_shiv, 24, "cannon")
    full_std = clear_wave(full, 24, "standard")
    none_std = clear_wave(no_shiv, 24, "standard")
    shiv_t = first_time(events[rush], "Statikk Shiv")
    last_t = first_time(events[last], "Statikk Shiv")
    q_rush = next(s.minute for s in results[rush] if s.q_evo)
    q_last = next((s.minute for s in results[last] if s.q_evo), None)
    w_rush = next(s.minute for s in results[rush] if s.w_evo)
    w_last = next(s.minute for s in results[last] if s.w_evo)

    def pct_faster(slower: float, faster: float) -> float:
        return (slower - faster) / slower * 100.0

    a("-" * 96)
    a("VERDICT")
    a("-" * 96)
    a("  For the wave, finish Statikk before Guinsoo. Guinsoo first is the 1v1,")
    a("  and Statikk second still catches the shove at the same two-item gold.")
    a("  Do not move Statikk to the last slot.")
    a("")
    a("  ONE ITEM, LEVEL 9 — THE CHAIN SHOVES, IT DOES NOT SKIP THE LAST MELEE")
    a(f"    Opening auto: Statikk {s_wave.first_auto:.0f} on {s_wave.max_targets_one_auto} "
      f"minions, Guinsoo {g_wave.first_auto:.0f} on {g_wave.max_targets_one_auto}.")
    a(f"    Casters die in {_sec(s_wave.caster_seconds)} with Statikk vs "
      f"{_sec(g_wave.caster_seconds)} with Guinsoo. By one second the wave has lost "
      f"{s_wave.removed_1s:.0f} HP vs {g_wave.removed_1s:.0f}.")
    a(f"    Full standard clear is {_sec(s_wave.seconds)} vs {_sec(g_wave.seconds)}. "
      f"That is a tie. Both are waiting on the 6s Q to finish the last melee.")
    a(f"    Cannon full clear {_sec(s_can.seconds)} vs {_sec(g_can.seconds)}. "
      f"With 15 armor / 20 MR it is {_sec(s_tough.seconds)} vs {_sec(g_tough.seconds)}.")
    a(f"    Autos only, frontliner, 8s: Guinsoo {g_auto.damage:.0f} vs Statikk "
      f"{s_auto.damage:.0f}. Guinsoo wins the duel. Statikk wins the first second.")
    a("    Neither item evolves Q (40 AD and 35 AD, gate is 70). Six missiles either way.")
    a("")
    a("  SAME GOLD, TWO LEGENDARIES + GREAVES — THIS IS THE FORK")
    a(f"    Statikk + Guinsoo: Q evolved (40+35 AD), standard wave {_sec(mid_std_c.seconds)}, "
      f"cannon {_sec(mid_c.seconds)}, {mid_std_c.removed_1s:.0f} HP gone at 1s.")
    a(f"    Guinsoo + Nashor: Q not evolved, standard wave {_sec(mid_std_n.seconds)} "
      f"({pct_faster(mid_std_n.seconds, mid_std_c.seconds):.0f}% slower), "
      f"cannon {_sec(mid_n.seconds)}, {mid_std_n.removed_1s:.0f} HP at 1s.")
    a(f"    Nashor evolves W. A frontliner dies in {_ttk(mid_nf.ttk)} vs "
      f"{_ttk(mid_cf.ttk)} on the chain, and auto-only damage is "
      f"{mid_auto_n.damage:.0f} vs {mid_auto_c.damage:.0f}.")
    a(f"    A squishy dies in {_ttk(mid_cs.ttk)} on the chain vs {_ttk(mid_ns.ttk)} "
      f"on Nashor — 12 missiles win the short fight.")
    a("    So Nashor second wins the long frontline scrap. It does not win the")
    a("    squishy all-in, and it does not shove. The chain is the Q evolve.")
    a("")
    a("  LAST SLOT")
    a(f"    On this no-kill clock Statikk is finished at {shiv_t:.2f} min if you rush it.")
    if last_t is None:
        a(f"    Moved to last, it is still not bought at {GAME_MINUTES}:00. "
          f"A normal game is over.")
    else:
        a(f"    Moved to last, it finishes at {last_t:.2f} min "
          f"({last_t - shiv_t:.1f} min later).")
    a(f"    Q evolves at minute {q_rush} on the rush (Guinsoo completes the 70 AD).")
    if q_last is None:
        a("    With Statikk last, Q never evolves inside this clock.")
    else:
        a(f"    With Statikk last, Q waits until minute {q_last} (Kraken's AD).")
    a(f"    W evolves earlier if Nashor is second: minute {w_last} vs {w_rush}.")
    a(f"    At level 15 the same five damage items, with the chain added, clear a")
    a(f"    standard wave in {_sec(full_std.seconds)} vs {_sec(none_std.seconds)} and a cannon in "
      f"{_sec(full_c.seconds)} vs {_sec(none_c.seconds)} "
      f"({pct_faster(none_c.seconds, full_c.seconds):.0f}% faster on the cannon).")
    a("    The 90 magic bolt is not what does that. Guinsoo, Nashor and Terminus")
    a("    finally have a bounce. That spike only exists if the game lasts long")
    a("    enough to buy a sixth item.")
    a("")
    a("  WHY KALISTA CAN AND KAI'SA CANNOT")
    a("    Kalista E refunds its cooldown on a minion kill, so a Guinsoo / Terminus")
    a("    order still chains the wave. One public baron list never buys Statikk")
    a("    (BotRK → Runaan → Guinsoo → Terminus) and still farms. Her dragon-lane")
    a("    list in 7.3d actually opens Statikk anyway, for the fight chain, not")
    a("    because she is stuck in the wave.")
    a("    Kai'Sa Q splits missiles and does not reset. Holding Statikk until last")
    a("    keeps her on 6 missiles until a later AD item, and the bounce that would")
    a("    spread Guinsoo / Nashor / Terminus never shows up in a 20-minute game.")
    a("")
    a("  BUY")
    a("    1) Long Sword → Pickaxe → Kircheis → Aether Wisp → Statikk")
    a("       The bolt does not replace the last melee. It kills the casters on")
    a("       the first auto + Q, so the wave is already pushing.")
    a("    2) Berserker's Greaves")
    a("    3) Guinsoo's Rageblade — Q evolves here, and the duel damage shows up")
    a("    4) Nashor's Tooth — W evolves, and the chain starts spreading the on-hit")
    a("    5) Kraken Slayer, then Terminus")
    a("    Guinsoo first wins the 1v1 and reaches the same two-item inventory at")
    a("    the same gold, with a worse shove until the bolt exists. Statikk last")
    a("    is a Kalista habit: she refunds Rend on a minion kill. Kai'Sa spends")
    a("    the whole mid game on 6 missiles and a single-target auto.")
    a("")
    a("  ASSUMPTIONS")
    a("    • Minion armor/MR default 0. The verdict reruns the cannon at 15 armor / 20 MR.")
    a("    • Energized opener is full (about 7s of walking at 340 MS fills 100).")
    a("    • Attack Energized is 6 + Electroshock 7. Move stacks are 1 per 24 units.")
    a("    • Bounce on-hits: Guinsoo 30, Nashor 15+20% AP, Terminus 30, Plasma.")
    a("      Not Kraken, not a second auto's AD, not a Rageblade phantom.")
    a("    • Phantom hit starts once 4 Guinsoo stacks are already up, every 3rd")
    a("      attack, and repeats on-hits including Guinsoo's own 30.")
    a("    • Q evolve counts bonus AD from items only. E evolve counts item AS only.")
    a("    • Aether Wisp 25 AP and Fiendish Codex 25 AP / 10 AH are component")
    a("      estimates. Finished-item stats are the patch numbers. The chain")
    a("      exists only on finished Statikk, not on Kircheis.")
    a("    • Lethal Tempo is off, so the fight gap is items and evolves, not the rune.")
    a("    • Gold has no kills. Both paths share it.")
    a("=" * 96)
    return "\n".join(lines)


def export_json(
    results: Dict[str, List[Snapshot]],
    events: Dict[str, List[Completion]],
    path: str,
) -> None:
    payload = {
        "meta": {
            "champion": "Kai'Sa",
            "role": "Dragon lane",
            "patch": "7.3 / 7.3b Statikk / 7.3f",
            "game_minutes": GAME_MINUTES,
            "question": "Statikk farm vs Guinsoo, and Statikk moved to last item",
            "wave": "4 minions; cannon replaces one caster",
            "gold": "500 start, 380/520/590/640 gpm, no kills, same clock every path",
        },
        "completions": {
            name: [{"item": e.item, "minute": e.minute} for e in ev]
            for name, ev in events.items()
        },
        "builds": {
            name: [
                {
                    "minute": s.minute,
                    "gold": s.gold,
                    "level": s.level,
                    "owned": s.owned,
                    "finished": s.finished,
                    "bonus_ad": round(s.bonus_ad, 1),
                    "ap": round(s.ap, 1),
                    "item_as": round(s.item_as, 3),
                    "q_evo": s.q_evo,
                    "w_evo": s.w_evo,
                    "e_evo": s.e_evo,
                    "clear_standard": round(s.clear_standard, 3),
                    "clear_cannon": round(s.clear_cannon, 3),
                    "caster_standard": round(s.caster_standard, 3),
                    "shove_1s": round(s.shove_1s, 1),
                    "first_auto": round(s.first_auto, 1),
                    "ttk_squishy": None if s.ttk_squishy is None else round(s.ttk_squishy, 3),
                    "dmg_front": round(s.dmg_front, 1),
                    "auto_front": round(s.auto_front, 1),
                }
                for s in snaps
            ]
            for name, snaps in results.items()
        },
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def self_check(
    results: Dict[str, List[Snapshot]],
    events: Dict[str, List[Completion]],
) -> None:
    kit_s = make_kit(9, [finish_statikk()], 0.0)
    kit_g = make_kit(9, [finish_guinsoo()], 0.0)
    wave_s = clear_wave(kit_s, 9, "standard")
    wave_g = clear_wave(kit_g, 9, "standard")
    assert wave_s.max_targets_one_auto == 4, wave_s
    assert wave_g.max_targets_one_auto == 1, wave_g
    # Full clear ties: both finish the last melee on the 6s Q. The chain's
    # job at one item is the opener and the casters.
    assert wave_s.seconds <= wave_g.seconds + 0.25, (wave_s.seconds, wave_g.seconds)
    assert wave_s.caster_seconds < wave_g.caster_seconds * 0.7, (
        wave_s.caster_seconds,
        wave_g.caster_seconds,
    )
    assert wave_s.first_auto > wave_g.first_auto * 2.5, (wave_s.first_auto, wave_g.first_auto)
    assert wave_s.removed_1s > wave_g.removed_1s * 1.15, (wave_s.removed_1s, wave_g.removed_1s)
    assert wave_s.finished and wave_g.finished

    can_s = clear_wave(kit_s, 9, "cannon")
    can_g = clear_wave(kit_g, 9, "cannon")
    assert can_s.seconds < can_g.seconds, (can_s.seconds, can_g.seconds)

    # Resists do not flip the one-item farm result.
    tough_s = clear_wave(kit_s, 9, "cannon", armor=15, mr=20)
    tough_g = clear_wave(kit_g, 9, "cannon", armor=15, mr=20)
    assert tough_s.seconds < tough_g.seconds, (tough_s.seconds, tough_g.seconds)

    auto_s = fight(kit_s, 9, "frontline", False)
    auto_g = fight(kit_g, 9, "frontline", False)
    assert auto_g.damage > auto_s.damage * 1.2, (auto_g.damage, auto_s.damage)

    assert not kit_s.q_evo and not kit_g.q_evo
    both = make_kit(11, [finish_statikk(), finish_guinsoo()], 0.0)
    assert both.q_evo and not both.w_evo

    # Nashor second does not evolve Q; the chain second does.
    nash_second = make_kit(12, [finish_guinsoo(), finish_nashor(), finish_greaves()], 0.18)
    chain_second = make_kit(12, [finish_statikk(), finish_guinsoo(), finish_greaves()], 0.18)
    assert chain_second.q_evo and not nash_second.q_evo
    assert nash_second.w_evo and not chain_second.w_evo
    c_can = clear_wave(chain_second, 15, "cannon")
    n_can = clear_wave(nash_second, 15, "cannon")
    c_std = clear_wave(chain_second, 15, "standard")
    n_std = clear_wave(nash_second, 15, "standard")
    assert c_std.seconds < n_std.seconds * 0.75, (c_std.seconds, n_std.seconds)
    assert c_can.seconds < n_can.seconds, (c_can.seconds, n_can.seconds)
    # Nashor second should win the frontline all-in. Both can kill, so compare
    # time-to-kill rather than damage capped at the target's HP.
    nash_front = fight(nash_second, 15, "frontline", True)
    chain_front = fight(chain_second, 15, "frontline", True)
    assert nash_front.ttk is not None and chain_front.ttk is not None
    assert nash_front.ttk < chain_front.ttk, (nash_front.ttk, chain_front.ttk)

    # On-hit spread still matters at full damage items.
    full = make_kit(
        15,
        [
            finish_statikk(),
            finish_guinsoo(),
            finish_nashor(),
            finish_kraken(),
            finish_terminus(),
            finish_greaves(),
        ],
        0.18,
    )
    bare = make_kit(
        15,
        [finish_guinsoo(), finish_nashor(), finish_kraken(), finish_terminus(), finish_greaves()],
        0.18,
    )
    assert clear_wave(full, 24, "cannon").seconds < clear_wave(bare, 24, "cannon").seconds

    rush_t = first_time(events["Statikk → Guinsoo"], "Statikk Shiv")
    last_t = first_time(events["Statikk last"], "Statikk Shiv")
    assert rush_t is not None and rush_t < 8.0, rush_t
    assert last_t is None or last_t > rush_t + 10.0, (rush_t, last_t)

    # Later plasma stacks hurt more, and the 5th stack also pops missing HP.
    assert plasma_tick(9, 0, 5) > plasma_tick(9, 0, 1)
    assert plasma_pop_ratio(0) == 0.15
    assert abs(plasma_pop_ratio(100) - 0.20) < 1e-9

    # Level 1 and 15 attack speed match the published sheet (0.753 / 0.952).
    assert abs(attack_speed(1, 0) - 0.753) < 0.002
    assert abs(attack_speed(15, 0) - 0.952) < 0.002

    # Clock is shared and increasing.
    rush = results["Statikk → Guinsoo"]
    assert rush[10].gold > rush[6].gold
    assert results["Statikk last"][10].gold == rush[10].gold


def run_all() -> Tuple[Dict[str, List[Snapshot]], Dict[str, List[Completion]]]:
    builds = {
        "Statikk → Guinsoo": build_statikk_rush(),
        "Guinsoo → Statikk": build_guinsoo_then_statikk(),
        "Statikk last": build_statikk_last(),
    }
    results: Dict[str, List[Snapshot]] = {}
    events: Dict[str, List[Completion]] = {}
    for name, buys in builds.items():
        snaps, done = simulate_build(buys)
        results[name] = snaps
        events[name] = done
    return results, events


def main() -> None:
    results, events = run_all()
    self_check(results, events)
    report = summarize(results, events)
    print(report)
    out_dir = "/workspace/kaisa-farm-sim"
    with open(f"{out_dir}/report.txt", "w", encoding="utf-8") as f:
        f.write(report + "\n")
    export_json(results, events, f"{out_dir}/results.json")
    print(f"\nWrote {out_dir}/report.txt and {out_dir}/results.json")


if __name__ == "__main__":
    main()
