#!/usr/bin/env python3
"""
Wild Rift Varus, patch 7.3f. Level 15.

Does Statikk Shiv plus Runaan's Hurricane earn its gold when the plan is
a charged Piercing Arrow and Blight on more than one champion?

Statikk's chain applies on-hit effects to every target after the first.
Hurricane's bolts apply on-hit effects to two champions in front of you.
Blight is an on-hit. A charged Piercing Arrow detonates it for percent
max-health magic damage and refunds cooldown per stack.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent

LEVEL = 15
BASE_AD = 54 + 3.6 * (LEVEL - 1)  # 104.4
BASE_AS_RATIO = 0.625
BASE_BONUS_AS = 0.205 + 0.032 * (LEVEL - 1)  # wiki level-1 bonus plus growth
BASE_MS = 340
BASE_MANA = 390 + 33 * (LEVEL - 1)  # 852, Manamune only

Q_CD = 12.0
Q_CHANNEL = 1.5
Q_BASE = 260.0
Q_AD = 1.40
# A full channel is +50% to the arrow and to Blight detonated by the arrow.
Q_CHARGE = 1.5
Q_FALLOFF = 0.15
Q_MIN_MULT = 0.33

E_CD = 10.0
E_CAST = 0.85  # 0.35 cast plus 0.50 for the arrows to land
E_BASE = 205.0
E_BONUS_AD = 0.90

W_ONHIT = 45.0
W_ONHIT_AP = 0.35
# Rank 4: 4.5% max health per stack, plus 1.2% per 100 AP.
BLIGHT_PCT = 0.045
BLIGHT_AP = 0.00012
BLIGHT_CAP = 3
BLIGHT_TIME = 6.0
# Each stack refunds 13% of the detonated ability's cooldown, capped at 39% per champion.
REFUND_PER_STACK = 0.13
REFUND_CAP = 0.39

# Energized: 6 per attack, 1 per 24 units moved, 100 to proc.
# Statikk's Electroshock adds 7, so an attack with Statikk grants 13.
ENERGY_PER_ATTACK = 6
ENERGY_PER_DISTANCE = 1 / 24
ENERGY_MAX = 100
STATIKK_BONUS_ENERGY = 7
WALK_IN = 575  # one attack range of walking before the first auto


@dataclass(frozen=True)
class Item:
    name: str
    cost: int
    ad: float = 0
    ap: float = 0
    as_pct: float = 0
    crit: float = 0
    ah: float = 0
    flat_pen: float = 0
    ms: float = 0
    onhit_magic: float = 0
    onhit_pct_hp: float = 0  # physical, percent of current health
    lifesteal: float = 0
    magic_vamp: float = 0
    rift: bool = False
    statikk: bool = False
    hurricane: bool = False
    guinsoo: bool = False
    terminus: bool = False
    duskblade: bool = False


GREAVES = Item("Berserker's Greaves", 1200, as_pct=0.35)
STATIKK = Item("Statikk Shiv", 2900, ad=40, ap=40, as_pct=0.30, ms=0.04, statikk=True)
HURRICANE = Item("Runaan's Hurricane", 2650, as_pct=0.40, crit=0.25, ms=0.04, hurricane=True)
GUINSOO = Item("Guinsoo's Rageblade", 3000, ad=35, ap=30, as_pct=0.30, onhit_magic=30, guinsoo=True)
BORK = Item("Blade of the Ruined King", 3100, ad=40, as_pct=0.30, onhit_pct_hp=0.07, lifesteal=0.12)
VAMP = Item("Vampiric Scepter", 1200, ad=20, lifesteal=0.08)
BT = Item("Bloodthirster", 3200, ad=75, lifesteal=0.15)
RIFT = Item("Riftmaker", 3100, ap=77, ah=15, magic_vamp=0.11, rift=True)
YOUMUU = Item("Youmuu's Ghostblade", 2900, ad=55, ah=15, flat_pen=15, ms=0.04)
DUSKBLADE = Item("Duskblade of Draktharr", 3000, ad=55, ah=10, flat_pen=18, duskblade=True)
MANAMUNE = Item("Manamune", 2900, ad=40 + 0.02 * (BASE_MANA + 500), ah=15)
TERMINUS = Item("Terminus", 3000, ad=35, as_pct=0.35, onhit_magic=30, terminus=True)


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


@dataclass
class Champ:
    spec: Target
    hp: float
    blight: int = 0
    blight_until: float = -1
    dealt: float = 0
    first_q: float = 0
    first_stacks: int = 0
    died: float | None = None


@dataclass
class Result:
    name: str
    gold: int
    policy: str
    targets: int
    spread: bool
    seconds: float
    damage: float
    per_target: dict
    first_q: float
    first_q_at: float | None
    first_stacks: list
    arrows: int
    autos: int
    deaths: dict = field(default_factory=dict)
    by_source: dict = field(default_factory=dict)
    healed: float = 0
    finished: float = 0


@dataclass
class Mods:
    """Empty mods keep the original fight numbers."""

    lifesteal: float = 0.0
    omnivamp: float = 0.0
    bonus_as: float = 0.0
    lethal: bool = False
    brutal: bool = False
    cut_down: bool = False
    conqueror: bool = False
    base_ad: float = BASE_AD


def loadout(items: list[Item], base_ad: float = BASE_AD) -> dict:
    return {
        "ad": base_ad + sum(i.ad for i in items),
        "bonus_ad": sum(i.ad for i in items),
        "ap": sum(i.ap for i in items),
        "crit": min(1.0, sum(i.crit for i in items)),
        "crit_dmg": 2.3 if any(i.name == "Infinity Edge" for i in items) else 2.0,
        "ah": sum(i.ah for i in items),
        "pen": sum(i.flat_pen for i in items),
        "as": sum(i.as_pct for i in items),
        "magic_onhit": sum(i.onhit_magic for i in items),
        "pct_hp": sum(i.onhit_pct_hp for i in items),
        "lifesteal": sum(i.lifesteal for i in items),
        "magic_vamp": sum(i.magic_vamp for i in items),
        "rift": any(i.rift for i in items),
        "statikk": any(i.statikk for i in items),
        "hurricane": any(i.hurricane for i in items),
        "guinsoo": any(i.guinsoo for i in items),
        "terminus": any(i.terminus for i in items),
        "dusk": any(i.duskblade for i in items),
        "spread_items": any(i.statikk or i.hurricane or i.guinsoo or i.onhit_pct_hp or i.terminus for i in items),
    }


def mitigate(raw: float, resist: float, pct_pen: float, flat_pen: float) -> float:
    resisted = resist * (1.0 - pct_pen) - flat_pen
    if resisted < 0:
        resisted = 0.0
    return raw * 100.0 / (100.0 + resisted)


def fight(
    items: list[Item],
    targets: list[Target],
    seconds: float,
    policy: str,
    spread: bool,
    energy: float,
    double_dip: bool = True,
    mods: Mods | None = None,
) -> Result:
    mods = mods or Mods()
    st = loadout(items, mods.base_ad)
    champs = [Champ(spec=t, hp=t.hp) for t in targets]
    rage = 0
    attacks = 0
    arrows = 0
    autos = 0
    pen_stacks = 0
    dusk_ready = 0.0
    w_active = True
    healed = 0.0
    tempo = 0
    tempo_at = -10.0
    conq = 0
    conq_at = -10.0
    sources = {"auto": 0.0, "bolt": 0.0, "onhit": 0.0, "statikk": 0.0, "arrow": 0.0, "blight": 0.0, "missing": 0.0, "e": 0.0, "tempo": 0.0, "brutal": 0.0}
    first_q_at = None
    t = 0.0
    next_auto = 0.0
    q_ready = 0.0
    e_ready = 0.0
    since_q = 0
    pending = None  # (kind, when)

    def pct_pen() -> float:
        return 0.10 * pen_stacks if st["terminus"] else 0.0

    def hurt(
        ch: Champ, amount: float, source: str, when: float, count_first: bool,
        kind: str = "magic", attack: bool = False, aoe: bool = False,
    ) -> None:
        nonlocal healed
        if amount <= 0 or ch.hp <= 0:
            return
        if st["rift"]:
            amount *= 1.0 + min(0.08, 0.02 * int(when))
        if mods.cut_down and not ch.spec.minion and ch.hp > 0.60 * ch.spec.hp:
            amount *= 1.065
        dealt = min(ch.hp, amount)
        ch.hp -= dealt
        ch.dealt += dealt
        if ch.hp <= 0 and ch.died is None:
            ch.died = when
        sources[source] += dealt
        if count_first and first_q_at is not None and abs(when - first_q_at) < 1e-9:
            ch.first_q += dealt
        rate = mods.lifesteal + st["lifesteal"] if attack else 0.0
        if kind == "magic":
            magic = st["magic_vamp"] * (1.0 / 3.0 if aoe else 1.0)
            rate += magic if not ch.spec.minion else magic * 0.20
        omni = mods.omnivamp + (0.05 if mods.conqueror and conq >= 6 and not ch.spec.minion else 0.0)
        if st["rift"] and when >= 4.0:
            omni += 0.06
        rate += omni * (0.20 if ch.spec.minion else 1.0)
        healed += dealt * rate

    def apply_blight(ch: Champ, when: float) -> None:
        if ch.hp <= 0:
            return
        if when > ch.blight_until:
            ch.blight = 0
        ch.blight = min(BLIGHT_CAP, ch.blight + 1)
        ch.blight_until = when + BLIGHT_TIME

    def on_hit(ch: Champ, when: float, count_first: bool) -> None:
        hurt(ch, mitigate(W_ONHIT + W_ONHIT_AP * st["ap"], ch.spec.mr, pct_pen(), 0), "onhit", when, count_first)
        if st["magic_onhit"]:
            hurt(ch, mitigate(st["magic_onhit"], ch.spec.mr, pct_pen(), 0), "onhit", when, count_first)
        if st["pct_hp"]:
            raw = max(15.0, st["pct_hp"] * ch.hp)
            hurt(ch, mitigate(raw, ch.spec.armor, pct_pen(), st["pen"]), "onhit", when, count_first, "physical", True)
        apply_blight(ch, when)

    def bonus_as() -> float:
        stacks = tempo if t <= tempo_at + 6.0 else 0
        return BASE_BONUS_AS + st["as"] + mods.bonus_as + (0.08 * rage if st["guinsoo"] else 0) + 0.064 * stacks

    def attack_speed() -> float:
        return min(3.0, BASE_AS_RATIO * (1.0 + bonus_as()))

    def do_auto(when: float) -> None:
        nonlocal attacks, autos, rage, pen_stacks, energy, dusk_ready, tempo, tempo_at, conq, conq_at
        autos += 1
        attacks += 1
        since = attacks
        primary = next(ch for ch in champs if ch.hp > 0)
        if not primary.spec.minion:
            if mods.lethal:
                if when > tempo_at + 6.0:
                    tempo = 0
                tempo = min(6, tempo + 1)
                tempo_at = when
            if mods.conqueror:
                if when > conq_at + 6.0:
                    conq = 0
                conq = min(6, conq + 1)
                conq_at = when
        if st["guinsoo"]:
            rage = min(4, rage + 1)
        if st["terminus"]:
            pen_stacks = min(3, pen_stacks + 1)
        energized = st["statikk"] and energy >= ENERGY_MAX
        if energized:
            energy = 0
        energy += ENERGY_PER_ATTACK + (STATIKK_BONUS_ENERGY if st["statikk"] else 0)
        if energy > ENERGY_MAX:
            energy = ENERGY_MAX

        crit_mult = 1.0 + st["crit"] * (st["crit_dmg"] - 1.0)
        ad_now = st["ad"] + (5.0 * max(0, conq - 1) if mods.conqueror and not primary.spec.minion else 0.0)
        physical = ad_now * crit_mult
        if mods.brutal and not primary.spec.minion:
            physical += 5.0 + 0.06 * (ad_now - mods.base_ad) + 0.03 * st["ap"]
        if st["dusk"] and when >= dusk_ready and not primary.spec.minion:
            physical += 160.0
            dusk_ready = when + 10.0
        if mods.lethal and tempo >= 6 and not primary.spec.minion:
            physical += 24.0 * (1.0 + 0.67 * bonus_as())
        hurt(primary, mitigate(physical, primary.spec.armor, pct_pen(), st["pen"]), "auto", when, False, "physical", True)
        on_hit(primary, when, False)

        secondaries = [ch for ch in champs if ch is not primary and ch.hp > 0] if spread else []
        bolted = []
        if st["hurricane"]:
            for ch in secondaries[:2]:
                bolt = 0.55 * ad_now * crit_mult
                hurt(ch, mitigate(bolt, ch.spec.armor, pct_pen(), st["pen"]), "bolt", when, False, "physical", True)
                on_hit(ch, when, False)
                bolted.append(ch)
        if energized:
            chain = [primary] + secondaries[:6]
            for ch in chain:
                spark = 90.0 if ch.spec.minion else 60.0
                hurt(ch, mitigate(spark, ch.spec.mr, pct_pen(), 0), "statikk", when, False, "magic", False, True)
                if ch is primary:
                    continue
                if (not double_dip) and ch in bolted:
                    continue
                on_hit(ch, when, False)
        if st["guinsoo"] and rage >= 4 and since % 3 == 0:
            on_hit(primary, when, False)
            if spread:
                for ch in secondaries[:2]:
                    on_hit(ch, when, False)

    def release(kind: str, when: float) -> None:
        nonlocal q_ready, e_ready, since_q, first_q_at, arrows, w_active, conq, conq_at
        living = [ch for ch in champs if ch.hp > 0]
        if not living:
            return
        if mods.conqueror and any(not ch.spec.minion for ch in living):
            if when > conq_at + 6.0:
                conq = 0
            spell_ad = 5.0 * conq
            conq = min(6, conq + 1)
            conq_at = when
        else:
            spell_ad = 0.0
        count_first = first_q_at is None and kind == "Q"
        if count_first:
            first_q_at = when
        primary = champs[0] if champs[0].hp > 0 else living[0]
        ordered = [primary] + [ch for ch in living if ch is not primary]
        refund = 0.0
        base_cd = Q_CD if kind == "Q" else E_CD
        hasted = base_cd * 100.0 / (100.0 + st["ah"])
        for index, ch in enumerate(ordered):
            stacks = ch.blight if when <= ch.blight_until else 0
            if count_first:
                ch.first_stacks = stacks
            before = ch.hp
            if kind == "Q":
                arrow = (Q_BASE + Q_AD * (st["ad"] + spell_ad)) * Q_CHARGE
                arrow *= max(Q_MIN_MULT, 1.0 - Q_FALLOFF * index)
                hurt(ch, mitigate(arrow, ch.spec.armor, pct_pen(), st["pen"]), "arrow", when, count_first, "physical")
                if stacks:
                    pct = (BLIGHT_PCT + BLIGHT_AP * st["ap"]) * stacks * Q_CHARGE
                    hurt(ch, mitigate(pct * ch.spec.hp, ch.spec.mr, pct_pen(), 0), "blight", when, count_first, "magic")
                # W is on a 25s cooldown, so one arrow in this fight carries it.
                # 18% is already the full-charge value.
                if w_active:
                    missing = ch.spec.hp - before
                    if missing > 0:
                        hurt(ch, mitigate(0.18 * missing, ch.spec.mr, pct_pen(), 0), "missing", when, count_first, "magic")
            else:
                raw = E_BASE + E_BONUS_AD * (st["bonus_ad"] + spell_ad)
                hurt(ch, mitigate(raw, ch.spec.armor, pct_pen(), st["pen"]), "e", when, False, "physical", False, True)
                if stacks:
                    pct = (BLIGHT_PCT + BLIGHT_AP * st["ap"]) * stacks
                    hurt(ch, mitigate(pct * ch.spec.hp, ch.spec.mr, pct_pen(), 0), "blight", when, False, "magic", False, True)
            if stacks:
                refund += min(REFUND_CAP, REFUND_PER_STACK * stacks) * hasted
                ch.blight = 0
        ready = when + max(0.0, hasted - refund)
        if kind == "Q":
            arrows += 1
            q_ready = ready
            since_q = 0
            w_active = False
        else:
            e_ready = ready

    while t < seconds - 1e-9 and any(ch.hp > 0 for ch in champs):
        if pending is not None:
            kind, when = pending
            if when > seconds:
                break
            t = when
            pending = None
            release(kind, t)
            continue

        primary_stacks = champs[0].blight if t <= champs[0].blight_until else 0
        q_up = q_ready <= t and t + Q_CHANNEL <= seconds + 1e-9
        e_up = e_ready <= t and t + E_CAST <= seconds + 1e-9
        cast = None
        if policy == "farm":
            cast = None
        elif policy == "commit" and st["spread_items"]:
            if q_up and (primary_stacks >= BLIGHT_CAP or t + Q_CHANNEL >= seconds - 0.05):
                cast = "Q"
            elif e_up and not q_up and primary_stacks >= BLIGHT_CAP:
                cast = "E"
        else:
            # Poke: an arrow build fires Q on cooldown. A Blight build autos once between arrows.
            ready_to_shoot = since_q >= 1 or not st["spread_items"]
            if q_up and ready_to_shoot:
                cast = "Q"
            elif e_up and since_q >= 1 and primary_stacks >= BLIGHT_CAP and not q_up:
                cast = "E"
        if cast == "Q":
            pending = ("Q", t + Q_CHANNEL)
            q_ready = 1e9
            continue
        if cast == "E":
            pending = ("E", t + E_CAST)
            e_ready = 1e9
            continue
        if next_auto <= t and any(ch.hp > 0 for ch in champs):
            do_auto(t)
            since_q += 1
            next_auto = t + 1.0 / attack_speed()
            continue
        nxt = seconds
        if next_auto > t:
            nxt = min(nxt, next_auto)
        if q_ready > t:
            nxt = min(nxt, q_ready)
        if e_ready > t:
            nxt = min(nxt, e_ready)
        if nxt <= t:
            break
        t = nxt

    return Result(
        name=" + ".join(i.name for i in items if i.name != "Berserker's Greaves"),
        gold=sum(i.cost for i in items),
        policy=policy,
        targets=len(targets),
        spread=spread,
        seconds=seconds,
        damage=round(sum(ch.dealt for ch in champs)),
        per_target={ch.spec.name: round(ch.dealt) for ch in champs},
        first_q=round(sum(ch.first_q for ch in champs)),
        first_q_at=None if first_q_at is None else round(first_q_at, 2),
        first_stacks=[ch.first_stacks for ch in champs],
        arrows=arrows,
        autos=autos,
        deaths={ch.spec.name: None if ch.died is None else round(ch.died, 2) for ch in champs},
        by_source={k: round(v) for k, v in sources.items()},
        healed=round(healed),
        finished=round(t, 2),
    )


def walked_in_energy(items: list[Item]) -> float:
    """Energy after walking one auto-attack of distance, before the first auto."""
    energy = WALK_IN * ENERGY_PER_DISTANCE
    return min(ENERGY_MAX, energy)


def catalog() -> list[list[Item]]:
    return [
        [GREAVES, STATIKK, HURRICANE],
        [GREAVES, STATIKK, GUINSOO],
        [GREAVES, HURRICANE, GUINSOO],
        [GREAVES, STATIKK, BORK],
        [GREAVES, YOUMUU, DUSKBLADE],
        [GREAVES, STATIKK, HURRICANE, GUINSOO],
        [GREAVES, STATIKK, GUINSOO, BORK],
        [GREAVES, YOUMUU, DUSKBLADE, MANAMUNE],
        [GREAVES, STATIKK, HURRICANE, GUINSOO, TERMINUS],
    ]


def run_all() -> list[Result]:
    rows = []
    situations = [
        ("poke", [CARRY], True, "charged"),
        ("poke", [TANK, BRUISER, CARRY], True, "charged"),
        ("commit", [TANK, BRUISER, CARRY], True, "charged"),
        ("poke", [TANK, BRUISER, CARRY], True, "short"),
        ("poke", [TANK, BRUISER, CARRY], False, "charged"),
    ]
    for items in catalog():
        for policy, targets, spread, opening in situations:
            energy = ENERGY_MAX if opening == "charged" else walked_in_energy(items)
            # A full bar means the first auto is the lightning. Walking one
            # attack range only banks 575/24 energy, so the proc is later.
            if opening == "charged" and not any(i.statikk for i in items):
                energy = walked_in_energy(items)
            rows.append(fight(items, targets, 8.0, policy, spread, energy))
    return rows


def _line(row: Result) -> str:
    per = " ".join(
        f"{k} {v}" + ("" if row.deaths.get(k) is None else f" dead {row.deaths[k]:.2f}s")
        for k, v in row.per_target.items()
    )
    when = "no arrow" if row.first_q_at is None else f"{row.first_q_at:.2f}s"
    return (
        f"{row.damage:6d}  first arrow {row.first_q:5d} at {when:>8}  "
        f"stacks {row.first_stacks}  Qx{row.arrows} autos {row.autos:2d}  {per}"
    )


def render(rows: list[Result]) -> str:
    lines = []
    w = lines.append
    w("=" * 78)
    w("VARUS — STATIKK SHIV + RUNAAN'S HURRICANE (Wild Rift 7.3f)")
    w("Level 15. Q, W, and E are maxed. Full 1.5s Piercing Arrow.")
    w("Front target is the tank, then the bruiser, then the carry.")
    w("=" * 78)
    w("")
    w("Poke fires a full arrow after one auto, then repeats when Q is back.")
    w("Commit holds the arrow until the champion you are hitting has 3 Blight.")
    w("Charged means the first auto is the Statikk lightning. A wave in front")
    w("sends the bolts and the bounces into minions, so champions are not spread to.")
    w("")
    groups = [
        ("ONE CHAMPION, POKE, FIRST AUTO IS LIGHTNING", lambda r: r.targets == 1 and r.policy == "poke"),
        ("THREE CHAMPIONS, POKE, FIRST AUTO IS LIGHTNING", lambda r: r.targets == 3 and r.policy == "poke" and r.spread and r.first_q_at == 1.5),
        ("THREE CHAMPIONS, COMMIT TO 3 BLIGHT, THEN THE ARROW", lambda r: r.policy == "commit"),
        ("THREE CHAMPIONS, POKE, ONLY A SHORT WALK IN", lambda r: r.targets == 3 and r.policy == "poke" and r.spread and r.first_q_at != 1.5),
        ("THREE CHAMPIONS, POKE, A MINION WAVE IS IN THE WAY", lambda r: not r.spread),
    ]
    # The charged poke's first arrow is at 1.5s only when an auto fits before the channel.
    # Identify the short-walk group by energy outcome: first arrow later than 1.5, spread on.
    # Recompute grouping from the result fields more carefully below.
    by_key: dict[tuple, list[Result]] = {}
    for row in rows:
        by_key.setdefault((row.policy, row.targets, row.spread, row.first_q_at == 1.5 or row.targets == 1), []).append(row)

    def section(title: str, chosen: list[Result]) -> None:
        w("-" * 78)
        w(title)
        w("-" * 78)
        for row in chosen:
            w(f"  {row.name}  ({row.gold}g)")
            w(f"    {_line(row)}")
            src = row.by_source
            w(f"    arrow {src['arrow']}  blight {src['blight']}  missing-health {src['missing']}  "
              f"autos {src['auto']}  bolts {src['bolt']}  on-hit {src['onhit']}  lightning {src['statikk']}")
        w("")

    one = [r for r in rows if r.targets == 1]
    three_poke = [r for r in rows if r.targets == 3 and r.policy == "poke" and r.spread and r.first_q_at == 1.5]
    # Short walk still autos once then channels, so the first arrow is also at 1.5s
    # unless attack time pushes it. Both charged and short-walk poke start with an auto
    # at t=0 for blight builds. Distinguish them by arrows and by running order.
    # Tag was not stored. Split by matching names in run order: each build emits
    # poke-1, poke-3-charged, commit, poke-3-short, poke-3-blocked.
    per_build = 5
    builds = [rows[i:i + per_build] for i in range(0, len(rows), per_build)]
    section("ONE CHAMPION, POKE", [b[0] for b in builds])
    section("THREE CHAMPIONS TOGETHER, POKE, LIGHTNING READY", [b[1] for b in builds])
    section("THREE CHAMPIONS TOGETHER, HOLD THE ARROW FOR 3 BLIGHT", [b[2] for b in builds])
    section("THREE CHAMPIONS TOGETHER, POKE AFTER A SHORT WALK", [b[3] for b in builds])
    section("THREE CHAMPIONS, MINIONS IN FRONT, POKE", [b[4] for b in builds])

    pair, guinsoo, hurricane, bork, ad, both, onhit, poke, full = builds
    w("-" * 78)
    w("WHAT THE PAIR CHANGES")
    w("-" * 78)
    w("One carry, from the first arrow until the kill. Everyone here kills them,")
    w("so the clock is the comparison.")
    w(f"  Statikk + Hurricane: dead at {pair[0].deaths['carry']}s, first arrow {pair[0].first_q}")
    w(f"  Hurricane + Guinsoo: dead at {hurricane[0].deaths['carry']}s, first arrow {hurricane[0].first_q}")
    w(f"  Youmuu + Duskblade: dead at {ad[0].deaths['carry']}s, first arrow {ad[0].first_q}")
    w("Three champions, lightning ready, one auto then the arrow, eight seconds:")
    w(f"  Statikk + Hurricane: {pair[1].damage}, first arrow {pair[1].first_q}, stacks {pair[1].first_stacks}, Qx{pair[1].arrows}")
    w(f"  Hurricane + Guinsoo: {hurricane[1].damage}, first arrow {hurricane[1].first_q}, stacks {hurricane[1].first_stacks}, Qx{hurricane[1].arrows}")
    w(f"  Statikk + Guinsoo: {guinsoo[1].damage}, first arrow {guinsoo[1].first_q}, stacks {guinsoo[1].first_stacks}, Qx{guinsoo[1].arrows}")
    w(f"  Youmuu + Duskblade: {ad[1].damage}, first arrow {ad[1].first_q}, stacks {ad[1].first_stacks}, Qx{ad[1].arrows}")
    w("Add Guinsoo to the pair and the bolts carry that on-hit on every attack:")
    w(f"  Statikk + Hurricane + Guinsoo: {both[1].damage}, first arrow {both[1].first_q}, Qx{both[1].arrows}")
    w(f"  Youmuu + Duskblade + Manamune: {poke[1].damage}, first arrow {poke[1].first_q}, Qx{poke[1].arrows}")
    w("")
    w("-" * 78)
    w("ASSUMPTIONS")
    w("-" * 78)
    w("  Statikk is the 7.3b item: 40 AD, 40 AP, 30% attack speed, 2900 gold.")
    w("  At level 15 the lightning hits up to 6 extra targets for 60 magic damage")
    w("  and applies on-hit effects to those targets, not a second on-hit on the")
    w("  champion you attacked. Hurricane bolts are 55% AD, can crit, and apply")
    w("  on-hit to two champions in front. Both can hit the same side champion,")
    w("  so one lightning auto can put two Blight stacks on each of them.")
    w("  Energized is 6 per attack plus 1 per 24 units moved. Statikk adds 7 per")
    w("  attack. A full bar is the walked-in case. One attack range of walking")
    w("  is only 24 energy, so the lightning is not ready yet.")
    w("  Blight is 4.5% max health per stack at W rank 4, plus 1.2% per 100 AP.")
    w("  A full arrow adds 50% to that and to the arrow. The arrow itself loses")
    w("  15% damage per champion after the first, down to 33%. Blight does not.")
    w("  W's active is on the first arrow only. It is a 25s cooldown: 18% missing")
    w("  health at a full charge, from health missing before that arrow. Each stack")
    w("  refunds 13% of that ability's hasted cooldown, up to 39% per champion.")
    w("  Base crits deal 200% damage. Runaan's 25% crit is averaged, not rolled.")
    w("  Guinsoo's extra on-hit starts once it is at four stacks, every third")
    w("  attack, and the bolts copy that extra on-hit. Duskblade adds 160")
    w("  physical damage to the first attack, then on a 10s cooldown.")
    w("  Manamune's Awe is 2% of Varus's level-15 mana plus the item's 500.")
    w("  No Lethal Tempo, no legend runes, no Living Vengeance. Armor and magic")
    w("  resist are the targets above. Damage stops at 0 health.")
    w("")
    return "\n".join(lines)


def main() -> None:
    rows = run_all()
    text = render(rows)
    (OUT / "report.txt").write_text(text)
    payload = []
    for row in rows:
        payload.append({
            "name": row.name,
            "gold": row.gold,
            "policy": row.policy,
            "targets": row.targets,
            "spread": row.spread,
            "damage": row.damage,
            "per_target": row.per_target,
            "first_q": row.first_q,
            "first_q_at": row.first_q_at,
            "first_stacks": row.first_stacks,
            "arrows": row.arrows,
            "autos": row.autos,
            "deaths": row.deaths,
            "by_source": row.by_source,
        })
    (OUT / "results.json").write_text(json.dumps(payload, indent=2))
    print(text)


if __name__ == "__main__":
    main()
