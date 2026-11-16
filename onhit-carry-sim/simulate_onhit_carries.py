#!/usr/bin/env python3
"""Kai'Sa and Kalista on the Varus six-item build. Wild Rift 7.3f, level 15.

The Varus build is Berserker's Greaves, Statikk Shiv, Guinsoo's Rageblade,
Runaan's Hurricane, Blade of the Ruined King, and Terminus. This asks which
of those slots their kits actually want changed.

Kai'Sa evolves one ability per completed item, in the order Q, then E, then W.
Boots and Vampiric Scepter do not count. Plasma uses the 7.3 formula. Icathian
Rain missiles scale with bonus attack damage. A grouped fight splits the
missiles. An isolated fight puts all of them on one champion.

Kalista's spears come from her own attack and from on-hit applications, so a
bolt and a Statikk bounce each add a spear. Rend uses the 7.3f rank-4 ratios.
She rends when the spears would kill something, and otherwise at the stack
count that wins the fight.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

OUT = Path(__file__).resolve().parent
LEVEL = 15
AS_CAP = 3.0

ENERGY_PER_ATTACK = 6
ENERGY_PER_DISTANCE = 1 / 24
ENERGY_MAX = 100
STATIKK_BONUS_ENERGY = 7


@dataclass(frozen=True)
class Item:
    name: str
    cost: int
    ad: float = 0
    ap: float = 0
    as_pct: float = 0
    crit: float = 0
    ah: float = 0
    onhit_magic: float = 0
    onhit_pct_hp: float = 0
    lifesteal: float = 0
    statikk: bool = False
    hurricane: bool = False
    guinsoo: bool = False
    terminus: bool = False
    kraken: bool = False
    nashor: bool = False
    counts_for_evolve: bool = True


GREAVES = Item("Berserker's Greaves", 1200, as_pct=0.35, counts_for_evolve=False)
STATIKK = Item("Statikk Shiv", 2900, ad=40, ap=40, as_pct=0.30, statikk=True)
HURRICANE = Item("Runaan's Hurricane", 2650, as_pct=0.40, crit=0.25, hurricane=True)
GUINSOO = Item("Guinsoo's Rageblade", 3000, ad=35, ap=30, as_pct=0.30, onhit_magic=30, guinsoo=True)
BORK = Item("Blade of the Ruined King", 3100, ad=40, as_pct=0.30, onhit_pct_hp=0.07, lifesteal=0.12)
VAMP = Item("Vampiric Scepter", 1200, ad=20, lifesteal=0.08, counts_for_evolve=False)
BT = Item("Bloodthirster", 3200, ad=75, lifesteal=0.15)
TERMINUS = Item("Terminus", 3000, ad=35, as_pct=0.35, onhit_magic=30, terminus=True)
KRAKEN = Item("Kraken Slayer", 2900, ad=45, as_pct=0.35, kraken=True)
NASHOR = Item("Nashor's Tooth", 2900, ap=80, as_pct=0.50, ah=15, nashor=True)

VARUS_BUILD = [GREAVES, STATIKK, GUINSOO, HURRICANE, BORK, TERMINUS]


@dataclass(frozen=True)
class Target:
    name: str
    hp: float
    armor: float
    mr: float
    minion: bool = False


CARRY = Target("carry", 2100, 70, 42)
BRUISER = Target("bruiser", 3400, 140, 80)
TANK = Target("tank", 4500, 220, 120)
GROUP = [TANK, BRUISER, CARRY]
MELEE = Target("melee", 640, 0, 0, minion=True)
CASTER = Target("caster", 340, 0, 0, minion=True)
WAVE = [MELEE, MELEE, MELEE, CASTER, CASTER, CASTER]


@dataclass
class Mods:
    omnivamp: float = 0.07
    bonus_as: float = 0.0
    lethal: bool = True
    brutal: bool = True
    cut_down: bool = True


BLOODLINE = Mods()
ALACRITY = Mods(omnivamp=0.0, bonus_as=0.18)


def mitigate(raw: float, resist: float, pct_pen: float) -> float:
    resisted = resist * (1.0 - pct_pen)
    if resisted < 0:
        resisted = 0.0
    return raw * 100.0 / (100.0 + resisted)


@dataclass
class Unit:
    spec: Target
    hp: float
    stacks: int = 0
    until: float = -1.0
    dealt: float = 0.0
    died: float | None = None


@dataclass
class Outcome:
    name: str
    gold: int
    damage: int
    healed: int
    finished: float
    deaths: dict
    sources: dict
    autos: int
    note: str = ""


def load(items: list[Item]) -> dict:
    return {
        "ad": sum(i.ad for i in items),
        "ap": sum(i.ap for i in items),
        "as": sum(i.as_pct for i in items),
        "crit": sum(i.crit for i in items),
        "ah": sum(i.ah for i in items),
        "magic_onhit": sum(i.onhit_magic for i in items),
        "pct_hp": sum(i.onhit_pct_hp for i in items),
        "lifesteal": sum(i.lifesteal for i in items),
        "statikk": any(i.statikk for i in items),
        "hurricane": any(i.hurricane for i in items),
        "guinsoo": any(i.guinsoo for i in items),
        "terminus": any(i.terminus for i in items),
        "kraken": any(i.kraken for i in items),
        "nashor": any(i.nashor for i in items),
        "evolved": sum(1 for i in items if i.counts_for_evolve),
        "gold": sum(i.cost for i in items),
        "name": " + ".join(i.name for i in items if not i.name.startswith("Berserker")),
    }


def fight_kaisa(
    items: list[Item],
    targets: list[Target],
    seconds: float,
    mods: Mods,
    wave: bool = False,
    double_dip: bool = True,
) -> Outcome:
    """Level 15 Kai'Sa. Base AD 59 + 3.5 per level. Attack speed ratio 0.625, 20% level-1 bonus, 3.2% growth."""
    st = load(items)
    base_ad = 59 + 3.5 * (LEVEL - 1)  # 108
    base_bonus = 0.20 + 0.032 * (LEVEL - 1)
    ratio = 0.625
    ad = base_ad + st["ad"]
    ap = st["ap"]
    q_evolved = st["evolved"] >= 1
    e_evolved = st["evolved"] >= 2
    w_evolved = st["evolved"] >= 3
    units = [Unit(spec=t, hp=t.hp) for t in targets]
    sources = {k: 0.0 for k in ("auto", "onhit", "plasma", "pop", "q", "w", "kraken", "tempo")}
    healed = 0.0
    rage = 0
    attacks = 0
    autos = 0
    pen = 0
    tempo = 0
    tempo_at = -10.0
    energy = ENERGY_MAX if st["statikk"] else 0.0
    steroid_until = 4.0 if e_evolved else -1.0
    e_ready = 10.0 if e_evolved else 1e9
    channel_until = None
    q_ready = 0.0
    w_ready = 0.0
    t = 0.0
    next_auto = 0.0

    def bonus_as() -> float:
        stacks = tempo if t <= tempo_at + 6.0 else 0
        steroid = 0.70 if t < steroid_until else 0.0
        return base_bonus + st["as"] + mods.bonus_as + steroid + (0.08 * rage if st["guinsoo"] else 0) + 0.064 * stacks

    def attack_speed() -> float:
        return min(AS_CAP, ratio * (1.0 + bonus_as()))

    def hurt(unit: Unit, amount: float, source: str, kind: str, attack: bool) -> None:
        nonlocal healed
        if amount <= 0 or unit.hp <= 0:
            return
        if mods.cut_down and not unit.spec.minion and unit.hp > 0.60 * unit.spec.hp:
            amount *= 1.065
        dealt = min(unit.hp, amount)
        unit.hp -= dealt
        unit.dealt += dealt
        if unit.hp <= 0 and unit.died is None:
            unit.died = t
        sources[source] += dealt
        rate = st["lifesteal"] if attack else 0.0
        omni = mods.omnivamp * (0.20 if unit.spec.minion else 1.0)
        healed += dealt * (rate + omni)

    def add_plasma(unit: Unit, n: int) -> None:
        if t > unit.until:
            unit.stacks = 0
        for _ in range(n):
            if unit.hp <= 0:
                return
            unit.stacks += 1
            per = 4 + LEVEL + 0.12 * ap + unit.stacks * (1 + 0.2 * LEVEL + 0.02 * ap)
            resist = unit.spec.mr
            hurt(unit, mitigate(per, resist, 0.10 * pen if st["terminus"] else 0.0), "plasma", "magic", False)
            if unit.stacks >= 5 and unit.hp > 0:
                missing = unit.spec.hp - unit.hp
                pop = (0.15 + 0.0005 * ap) * missing
                hurt(unit, mitigate(pop, resist, 0.10 * pen if st["terminus"] else 0.0), "pop", "magic", False)
                unit.stacks = 0
            unit.until = t + 4.0

    def on_hit(unit: Unit) -> None:
        pct = 0.10 * pen if st["terminus"] else 0.0
        add_plasma(unit, 1)
        if unit.hp <= 0:
            return
        if st["magic_onhit"]:
            hurt(unit, mitigate(st["magic_onhit"], unit.spec.mr, pct), "onhit", "magic", False)
        if st["nashor"]:
            hurt(unit, mitigate(15 + 0.20 * ap, unit.spec.mr, pct), "onhit", "magic", False)
        if st["pct_hp"] and unit.hp > 0:
            raw = max(15.0, st["pct_hp"] * unit.hp)
            hurt(unit, mitigate(raw, unit.spec.armor, pct), "onhit", "physical", True)

    def living() -> list[Unit]:
        return [u for u in units if u.hp > 0]

    def do_auto() -> None:
        nonlocal attacks, autos, rage, pen, energy, tempo, tempo_at, e_ready
        alive = living()
        if not alive:
            return
        autos += 1
        attacks += 1
        primary = alive[0]
        if not primary.spec.minion:
            if mods.lethal:
                if t > tempo_at + 6.0:
                    tempo = 0
                tempo = min(6, tempo + 1)
                tempo_at = t
        if st["guinsoo"]:
            rage = min(4, rage + 1)
        if st["terminus"]:
            pen = min(3, pen + 1)
        pct = 0.10 * pen if st["terminus"] else 0.0
        energized = st["statikk"] and energy >= ENERGY_MAX
        if energized:
            energy = 0
        if st["statikk"]:
            energy = min(ENERGY_MAX, energy + ENERGY_PER_ATTACK + STATIKK_BONUS_ENERGY)
        crit = 1.0 + st["crit"] * 1.0
        physical = ad * crit
        if mods.brutal and not primary.spec.minion:
            physical += 5 + 0.06 * st["ad"] + 0.03 * ap
        if mods.lethal and tempo >= 6 and not primary.spec.minion:
            physical += 24 * (1 + 0.67 * bonus_as())
        hurt(primary, mitigate(physical, primary.spec.armor, pct), "auto", "physical", True)
        on_hit(primary)
        if st["kraken"] and attacks % 3 == 0 and primary.hp > 0:
            missing = (primary.spec.hp - primary.hp) / primary.spec.hp
            proc = (168 if not primary.spec.minion else 168) * (1 + min(0.75, 0.75 * missing))
            hurt(primary, mitigate(proc, primary.spec.armor, pct), "kraken", "physical", True)
        secondaries = [u for u in alive if u is not primary and u.hp > 0]
        bolted = []
        if st["hurricane"]:
            for unit in secondaries[:2]:
                if unit.hp <= 0:
                    continue
                hurt(unit, mitigate(0.55 * ad * crit, unit.spec.armor, pct), "auto", "physical", True)
                on_hit(unit)
                bolted.append(unit)
        if energized:
            for unit in [primary] + secondaries[:6]:
                if unit.hp <= 0:
                    continue
                spark = 90.0 if unit.spec.minion else 60.0
                hurt(unit, mitigate(spark, unit.spec.mr, pct), "onhit", "magic", False)
                if unit is primary:
                    continue
                if (not double_dip) and unit in bolted:
                    continue
                on_hit(unit)
        if st["guinsoo"] and rage >= 4 and attacks % 3 == 0:
            if primary.hp > 0:
                on_hit(primary)
            for unit in secondaries[:2]:
                if unit.hp > 0:
                    on_hit(unit)
        if e_evolved:
            e_ready = max(t, e_ready - 0.5)

    def cast_w() -> None:
        nonlocal w_ready
        alive = living()
        if not alive:
            return
        target = alive[0]
        raw = 120 + 1.30 * ad + 0.50 * ap
        pct = 0.10 * pen if st["terminus"] else 0.0
        hurt(target, mitigate(raw, target.spec.mr, pct), "w", "magic", False)
        add_plasma(target, 3 if w_evolved else 2)
        cd = 14 * 100 / (100 + st["ah"])
        if w_evolved and not target.spec.minion:
            cd *= 0.30
        w_ready = t + cd

    def cast_q() -> None:
        nonlocal q_ready
        alive = living()
        if not alive:
            return
        missiles = 12 if q_evolved else 6
        # Grouped enemies share the swarm. Isolation puts every missile on one target.
        recipients = alive if (wave or len(alive) > 1) else alive
        counts = [missiles // len(recipients)] * len(recipients)
        for i in range(missiles % len(recipients)):
            counts[i] += 1
        pct = 0.10 * pen if st["terminus"] else 0.0
        missile = 100 + 0.50 * st["ad"] + 0.30 * ap
        for unit, count in zip(recipients, counts):
            first = True
            for _ in range(count):
                if unit.hp <= 0:
                    break
                scale = 1.0
                if not unit.spec.minion and not first:
                    scale = 0.25
                if unit.spec.minion and unit.hp < 0.35 * unit.spec.hp:
                    scale *= 1.5
                hurt(unit, mitigate(missile * scale, unit.spec.armor, pct), "q", "physical", False)
                first = False
        q_ready = t + 6 * 100 / (100 + st["ah"])

    while t < seconds - 1e-9 and living():
        if channel_until is not None and t >= channel_until:
            steroid_until = t + 4.0
            channel_until = None
        acted = False
        if w_ready <= t and (channel_until is None or True):
            cast_w()
            t += 0.25
            acted = True
        elif q_ready <= t:
            cast_q()
            t += 0.25
            acted = True
        elif e_evolved and channel_until is None and e_ready <= t and t >= steroid_until:
            channel_until = t + (0.5 if bonus_as() >= 1 else 1.0)
            e_ready = t + 10 * 100 / (100 + st["ah"])
            t = channel_until
            acted = True
        elif next_auto <= t and channel_until is None:
            do_auto()
            next_auto = t + 1.0 / attack_speed()
            acted = True
        if not acted:
            nxt = seconds
            if next_auto > t:
                nxt = min(nxt, next_auto)
            if q_ready > t:
                nxt = min(nxt, q_ready)
            if w_ready > t:
                nxt = min(nxt, w_ready)
            if channel_until is not None:
                nxt = min(nxt, channel_until)
            if e_evolved and e_ready > t:
                nxt = min(nxt, max(e_ready, steroid_until))
            if nxt <= t:
                break
            t = nxt
        if t > seconds:
            t = seconds
            break

    deaths = {u.spec.name: None if u.died is None else round(u.died, 2) for u in units}
    # Duplicate minion names collapse. Keep the latest death, which is the clear.
    return Outcome(
        name=st["name"],
        gold=st["gold"],
        damage=round(sum(u.dealt for u in units)),
        healed=round(healed),
        finished=round(min(t, seconds), 2),
        deaths=deaths,
        sources={k: round(v) for k, v in sources.items()},
        autos=autos,
        note=("Q evolved" if q_evolved else "Q base") + (", E" if e_evolved else "") + (", W" if w_evolved else ""),
    )


def fight_kalista(
    items: list[Item],
    targets: list[Target],
    seconds: float,
    mods: Mods,
    wave: bool = False,
    hold: int = 8,
    double_dip: bool = True,
) -> Outcome:
    """Level 15 Kalista. Base AD 57 + 5.2 per level. Attack speed ratio 0.694."""
    st = load(items)
    base_ad = 57 + 5.2 * (LEVEL - 1)  # 129.8
    base_bonus = 0.16 + 0.046 * (LEVEL - 1)
    ratio = 0.694
    ad = base_ad + st["ad"]
    ap = st["ap"]
    units = [Unit(spec=t, hp=t.hp) for t in targets]
    sources = {k: 0.0 for k in ("auto", "onhit", "rend", "pierce", "kraken", "tempo")}
    healed = 0.0
    rage = 0
    attacks = 0
    autos = 0
    pen = 0
    tempo = 0
    tempo_at = -10.0
    energy = ENERGY_MAX if st["statikk"] else 0.0
    e_ready = 0.0
    q_ready = 0.0
    rends = 0
    t = 0.0
    next_auto = 0.0

    def bonus_as() -> float:
        stacks = tempo if t <= tempo_at + 6.0 else 0
        return base_bonus + st["as"] + mods.bonus_as + (0.08 * rage if st["guinsoo"] else 0) + 0.064 * stacks

    def attack_speed() -> float:
        return min(AS_CAP, ratio * (1.0 + bonus_as()))

    def hurt(unit: Unit, amount: float, source: str, attack: bool) -> None:
        nonlocal healed
        if amount <= 0 or unit.hp <= 0:
            return
        if mods.cut_down and not unit.spec.minion and unit.hp > 0.60 * unit.spec.hp:
            amount *= 1.065
        dealt = min(unit.hp, amount)
        unit.hp -= dealt
        unit.dealt += dealt
        if unit.hp <= 0 and unit.died is None:
            unit.died = t
        sources[source] += dealt
        rate = st["lifesteal"] if attack else 0.0
        omni = mods.omnivamp * (0.20 if unit.spec.minion else 1.0)
        healed += dealt * (rate + omni)

    def spears(unit: Unit) -> int:
        if t > unit.until:
            return 0
        return unit.stacks

    def add_spear(unit: Unit) -> None:
        if unit.hp <= 0:
            return
        if t > unit.until:
            unit.stacks = 0
        unit.stacks += 1
        unit.until = t + 4.0

    def rend_raw(unit: Unit) -> float:
        stacks = spears(unit)
        if stacks <= 0:
            return 0.0
        return (75 + 0.70 * ad) + (stacks - 1) * (42 + 0.57 * ad)

    def on_hit(unit: Unit) -> None:
        pct = 0.10 * pen if st["terminus"] else 0.0
        add_spear(unit)
        if st["magic_onhit"] and unit.hp > 0:
            hurt(unit, mitigate(st["magic_onhit"], unit.spec.mr, pct), "onhit", False)
        if st["pct_hp"] and unit.hp > 0:
            raw = max(15.0, st["pct_hp"] * unit.hp)
            hurt(unit, mitigate(raw, unit.spec.armor, pct), "onhit", True)

    def living() -> list[Unit]:
        return [u for u in units if u.hp > 0]

    def do_auto() -> None:
        nonlocal attacks, autos, rage, pen, energy, tempo, tempo_at
        alive = living()
        if not alive:
            return
        autos += 1
        attacks += 1
        primary = alive[0]
        if not primary.spec.minion and mods.lethal:
            if t > tempo_at + 6.0:
                tempo = 0
            tempo = min(6, tempo + 1)
            tempo_at = t
        if st["guinsoo"]:
            rage = min(4, rage + 1)
        if st["terminus"]:
            pen = min(3, pen + 1)
        pct = 0.10 * pen if st["terminus"] else 0.0
        energized = st["statikk"] and energy >= ENERGY_MAX
        if energized:
            energy = 0
        if st["statikk"]:
            energy = min(ENERGY_MAX, energy + ENERGY_PER_ATTACK + STATIKK_BONUS_ENERGY)
        crit = 1.0 + st["crit"] * 1.0
        physical = ad * crit
        if mods.brutal and not primary.spec.minion:
            physical += 5 + 0.06 * st["ad"] + 0.03 * ap
        if mods.lethal and tempo >= 6 and not primary.spec.minion:
            physical += 24 * (1 + 0.67 * bonus_as())
        hurt(primary, mitigate(physical, primary.spec.armor, pct), "auto", True)
        on_hit(primary)
        if st["kraken"] and attacks % 3 == 0 and primary.hp > 0:
            missing = (primary.spec.hp - primary.hp) / primary.spec.hp
            proc = 168 * (1 + min(0.75, 0.75 * missing))
            hurt(primary, mitigate(proc, primary.spec.armor, pct), "kraken", True)
        secondaries = [u for u in alive if u is not primary]
        bolted = []
        if st["hurricane"]:
            for unit in secondaries[:2]:
                if unit.hp <= 0:
                    continue
                hurt(unit, mitigate(0.55 * ad * crit, unit.spec.armor, pct), "auto", True)
                on_hit(unit)
                bolted.append(unit)
        if energized:
            for unit in [primary] + secondaries[:6]:
                if unit.hp <= 0:
                    continue
                spark = 90.0 if unit.spec.minion else 60.0
                hurt(unit, mitigate(spark, unit.spec.mr, pct), "onhit", False)
                if unit is primary or ((not double_dip) and unit in bolted):
                    continue
                on_hit(unit)
        if st["guinsoo"] and rage >= 4 and attacks % 3 == 0:
            if primary.hp > 0:
                on_hit(primary)
            for unit in secondaries[:2]:
                if unit.hp > 0:
                    on_hit(unit)

    def cast_rend() -> bool:
        nonlocal e_ready, rends
        killed = False
        pct = 0.10 * pen if st["terminus"] else 0.0
        for unit in living():
            raw = rend_raw(unit)
            if raw <= 0:
                continue
            before = unit.hp
            hurt(unit, mitigate(raw, unit.spec.armor, pct), "rend", False)
            unit.stacks = 0
            if unit.hp <= 0 < before:
                killed = True
        rends += 1
        e_ready = t if killed else t + 7.0
        return killed

    def cast_q() -> None:
        nonlocal q_ready
        alive = living()
        if not alive:
            return
        target = alive[0]
        pct = 0.10 * pen if st["terminus"] else 0.0
        add_spear(target)
        hurt(target, mitigate(270 + 1.10 * ad, target.spec.armor, pct), "pierce", False)
        if target.hp <= 0 and len(alive) > 1:
            nxt = alive[1]
            nxt.stacks += target.stacks
            nxt.until = t + 4.0
            target.stacks = 0
        q_ready = t + 6.0

    def want_rend() -> bool:
        if e_ready > t:
            return False
        alive = living()
        if not alive:
            return False
        pct = 0.10 * pen if st["terminus"] else 0.0
        for unit in alive:
            raw = rend_raw(unit)
            if raw > 0 and mitigate(raw, unit.spec.armor, pct) >= unit.hp:
                return True
        primary = alive[0]
        return spears(primary) >= hold

    while t < seconds - 1e-9 and living():
        acted = False
        if want_rend():
            cast_rend()
            t += 0.25
            acted = True
        elif q_ready <= t and not wave:
            cast_q()
            t += 0.25
            acted = True
        elif next_auto <= t:
            do_auto()
            next_auto = t + 1.0 / attack_speed()
            acted = True
        if not acted:
            nxt = seconds
            if next_auto > t:
                nxt = min(nxt, next_auto)
            if e_ready > t:
                nxt = min(nxt, e_ready)
            if q_ready > t and not wave:
                nxt = min(nxt, q_ready)
            if nxt <= t:
                break
            t = nxt

    return Outcome(
        name=st["name"],
        gold=st["gold"],
        damage=round(sum(u.dealt for u in units)),
        healed=round(healed),
        finished=round(min(t, seconds), 2),
        deaths={u.spec.name: None if u.died is None else round(u.died, 2) for u in units},
        sources={k: round(v) for k, v in sources.items()},
        autos=autos,
        note=(f"rend at {hold} spears, cast {rends}" if hold < 90 else f"rend on a kill, cast {rends}"),
    )


def best_kalista(items, targets, seconds, mods, wave=False) -> Outcome:
    # On a wave she holds Rend until it kills a minion and the cooldown resets.
    holds = (99,) if wave else (6, 8, 10, 12)
    rows = [fight_kalista(items, targets, seconds, mods, wave, hold) for hold in holds]
    if wave:
        return rows[0]

    def rank(row: Outcome):
        deaths = [v for v in row.deaths.values() if v is not None]
        return (len(deaths), -row.finished if len(deaths) == len(row.deaths) else 0, row.damage)

    return max(rows, key=rank)


def show(label: str, row: Outcome) -> str:
    clocks = " ".join(f"{name} {when:.2f}s" for name, when in row.deaths.items() if when is not None)
    return (
        f"{label:<32} dmg {row.damage:>5} heal {row.healed:>4} time {row.finished:>5} "
        f"autos {row.autos:>2}  {clocks}  {row.note}"
    )


def main() -> None:
    lines = [
        "Kai'Sa and Kalista, level 15, patch 7.3f, on the Varus build.",
        "Varus build: Berserker's Greaves, Statikk, Guinsoo, Hurricane, BotRK, Terminus.",
        "Runes unless noted: Lethal Tempo, Brutal, Cut Down, Legend: Bloodline.",
        "Group is tank, bruiser, carry. Wave is 3 melee at 640 and 3 casters at 340.",
        "Kai'Sa starts the fight with Supercharge already channeled when E is evolved.",
        "",
    ]
    saved = {}

    kaisa_builds = [
        ("Varus build", VARUS_BUILD),
        ("Kraken for Statikk", [GREAVES, KRAKEN, GUINSOO, HURRICANE, BORK, TERMINUS]),
        ("Nashor for Hurricane", [GREAVES, STATIKK, GUINSOO, NASHOR, BORK, TERMINUS]),
        ("Kraken and Nashor", [GREAVES, KRAKEN, GUINSOO, NASHOR, BORK, TERMINUS]),
        ("Kraken, no Hurricane", [GREAVES, KRAKEN, GUINSOO, BORK, TERMINUS]),
    ]
    lines.append("KAI'SA, 8 seconds, three champions, missiles split")
    for name, items in kaisa_builds:
        row = fight_kaisa(items, GROUP, 8.0, BLOODLINE)
        short = fight_kaisa(items, GROUP, 4.0, BLOODLINE)
        wave = fight_kaisa(items, WAVE, 12.0, BLOODLINE, wave=True)
        solo = fight_kaisa(items, [CARRY], 8.0, BLOODLINE)
        lines.append(show("group  " + name, row))
        lines.append(show("4s     " + name, short))
        lines.append(show("solo   " + name, solo))
        lines.append(show("wave   " + name, wave))
        saved["kaisa " + name] = {
            "group": row.damage, "heal": row.healed, "deaths": row.deaths,
            "four": short.damage, "four_heal": short.healed,
            "solo_time": solo.finished, "solo_deaths": solo.deaths, "solo_damage": solo.damage,
            "wave_time": wave.finished, "wave_heal": wave.healed, "sources": row.sources, "gold": row.gold,
        }
    lines.append("")
    lines.append("KAI'SA buy order, Bloodline, one wave and the 8 second group")
    for name, items in (
        ("Scepter + boots", [GREAVES, VAMP]),
        ("Statikk + boots", [GREAVES, STATIKK]),
        ("Kraken + boots", [GREAVES, KRAKEN]),
        ("Statikk + Scepter + boots", [GREAVES, STATIKK, VAMP]),
        ("Statikk + Guinsoo + Scepter", [GREAVES, STATIKK, GUINSOO, VAMP]),
        ("Core three + Scepter", [GREAVES, STATIKK, GUINSOO, HURRICANE, VAMP]),
        ("Finished Varus build", VARUS_BUILD),
    ):
        group = fight_kaisa(items, GROUP, 8.0, BLOODLINE)
        wave = fight_kaisa(items, WAVE, 12.0, BLOODLINE, wave=True)
        lines.append(show(name, wave) + f"  gold {wave.gold}")
        lines.append(show("group  " + name, group))
        saved["kaisa step " + name] = {"wave": wave.finished, "wave_heal": wave.healed, "group": group.damage, "deaths": group.deaths, "gold": wave.gold}

    lines.append("")
    lines.append("KAI'SA rune check on the Varus build")
    for label, mods in (("Bloodline", BLOODLINE), ("Alacrity", ALACRITY)):
        short = fight_kaisa(VARUS_BUILD, GROUP, 4.0, mods)
        wave = fight_kaisa(VARUS_BUILD, WAVE, 12.0, mods, wave=True)
        lines.append(show(label, short) + f"  wave {wave.finished}s heal {wave.healed}")
        saved["kaisa rune " + label] = {"four": short.damage, "four_heal": short.healed, "wave": wave.finished, "wave_heal": wave.healed}

    lines.append("")
    lines.append("KALISTA, 8 seconds. She rends at the stack count that kills sooner.")
    kalista_builds = [
        ("Varus build", VARUS_BUILD),
        ("Kraken for Statikk", [GREAVES, KRAKEN, GUINSOO, HURRICANE, BORK, TERMINUS]),
        ("Bloodthirster for Statikk", [GREAVES, BT, GUINSOO, HURRICANE, BORK, TERMINUS]),
        ("No Statikk", [GREAVES, GUINSOO, HURRICANE, BORK, TERMINUS]),
    ]
    for name, items in kalista_builds:
        row = best_kalista(items, GROUP, 8.0, BLOODLINE)
        short = best_kalista(items, GROUP, 4.0, BLOODLINE)
        solo = best_kalista(items, [CARRY], 8.0, BLOODLINE)
        wave = best_kalista(items, WAVE, 12.0, BLOODLINE, wave=True)
        lines.append(show("group  " + name, row))
        lines.append(show("4s     " + name, short))
        lines.append(show("solo   " + name, solo))
        lines.append(show("wave   " + name, wave))
        saved["kalista " + name] = {
            "group": row.damage, "heal": row.healed, "deaths": row.deaths, "note": row.note,
            "four": short.damage, "four_heal": short.healed,
            "solo_time": solo.finished, "solo_deaths": solo.deaths,
            "wave_time": wave.finished, "wave_heal": wave.healed, "sources": row.sources, "gold": row.gold,
        }

    lines.append("")
    lines.append("KALISTA buy order, Bloodline")
    for name, items in (
        ("Scepter + boots", [GREAVES, VAMP]),
        ("BotRK + boots", [GREAVES, BORK]),
        ("Statikk + boots", [GREAVES, STATIKK]),
        ("BotRK + Guinsoo", [GREAVES, BORK, GUINSOO]),
        ("BotRK + Guinsoo + Hurricane", [GREAVES, BORK, GUINSOO, HURRICANE]),
        ("Those four + Terminus", [GREAVES, BORK, GUINSOO, HURRICANE, TERMINUS]),
        ("Finished, Statikk last", VARUS_BUILD),
    ):
        group = best_kalista(items, GROUP, 8.0, BLOODLINE)
        wave = best_kalista(items, WAVE, 12.0, BLOODLINE, wave=True)
        lines.append(show(name, wave) + f"  gold {wave.gold}")
        lines.append(show("group  " + name, group))
        saved["kalista step " + name] = {"wave": wave.finished, "wave_heal": wave.healed, "group": group.damage, "deaths": group.deaths, "gold": wave.gold}

    lines.append("")
    lines.append("KALISTA rune check on the Varus build")
    for label, mods in (("Bloodline", BLOODLINE), ("Alacrity", ALACRITY)):
        short = best_kalista(VARUS_BUILD, GROUP, 4.0, mods)
        wave = best_kalista(VARUS_BUILD, WAVE, 12.0, mods, wave=True)
        lines.append(show(label, short) + f"  wave {wave.finished}s heal {wave.healed}")
        saved["kalista rune " + label] = {"four": short.damage, "four_heal": short.healed, "wave": wave.finished, "wave_heal": wave.healed}

    text = "\n".join(lines) + "\n"
    (OUT / "report.txt").write_text(text)
    (OUT / "results.json").write_text(json.dumps(saved, indent=2) + "\n")
    print(text)


if __name__ == "__main__":
    main()
