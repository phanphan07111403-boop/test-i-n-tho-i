#!/usr/bin/env python3
"""
Wild Rift Kog'Maw — BoRK → Berserker's, then Runaan's vs Guinsoo's.

Patch 7.3 (2026-09-21) item and attack-speed model.
Question: after rushing Blade of the Ruined King and Berserker's Greaves,
what changes in a fight and on the map if the next item is Runaan's Hurricane
or Guinsoo's Rageblade?

Both paths spend the same gold. They diverge only in the order of the two
on-hit items, including the components you actually hold before the combine.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
import json

GAME_MINUTES = 18
W_WINDOW = 8.0
AS_CAP = 3.0
CRIT_DAMAGE = 2.0  # patch 7.3 base crit damage 200%


# ---------------------------------------------------------------------------
# Economy / levels — even dragon-lane farmer, not a stomp
# ---------------------------------------------------------------------------

def gold_at_minute(m: int) -> int:
    """Starting 500, then CS + plates + objective share. ~10.8k by 18:00."""
    if m <= 0:
        return 500
    total = 500
    for t in range(1, m + 1):
        if t <= 5:
            total += 430
        elif t <= 11:
            total += 560
        else:
            total += 680
    return total


def level_at_minute(m: int) -> int:
    table = {
        1: 1, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7, 7: 8, 8: 8,
        9: 9, 10: 10, 11: 11, 12: 12, 13: 12, 14: 13,
        15: 13, 16: 14, 17: 14, 18: 15,
    }
    return table.get(m, 15)


SKILL_ORDER = ["W", "Q", "E", "W", "R", "W", "W", "Q", "R", "Q", "Q", "Q", "R", "E", "E"]


def ranks_at_level(level: int) -> dict[str, int]:
    ranks = {"Q": 0, "W": 0, "E": 0, "R": 0}
    for i in range(min(level, len(SKILL_ORDER))):
        ranks[SKILL_ORDER[i]] += 1
    return ranks


def level_as_bonus(asp_per_level: float, level: int) -> float:
    """7.3 per-level bonus AS. Sum through level 15 equals 14 × the per-level stat."""
    total = 0.0
    for reached_from in range(1, level):
        total += asp_per_level * (0.7 + 0.04 * reached_from)
    return total


def attack_speed(level: int, extra_bonus: float) -> float:
    """Total AS = base + ratio × (base bonus + level bonus + items/runes/abilities)."""
    bonus = 0.2 + level_as_bonus(0.03, level) + extra_bonus
    return min(AS_CAP, 0.665 + 0.665 * bonus)


def bonus_as_fraction(level: int, extra_bonus: float) -> float:
    return 0.2 + level_as_bonus(0.03, level) + extra_bonus


# ---------------------------------------------------------------------------
# Items (incremental cost; parent consumes its components)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Step:
    name: str
    cost: int
    consumes: tuple[tuple[str, int], ...] = ()


@dataclass
class Stats:
    ad: float = 0.0
    ap: float = 0.0
    aspd: float = 0.0
    crit: float = 0.0
    lifesteal: float = 0.0
    onhit_phys: float = 0.0
    wrath: float = 0.0
    greaves_heal: float = 0.0
    onhit_magic: float = 0.0
    bork: bool = False
    guinsoo: bool = False
    runaan: bool = False
    shiv: bool = False
    terminus: bool = False
    shock: bool = False

    def add(self, other: "Stats", n: int = 1) -> "Stats":
        return Stats(
            ad=self.ad + other.ad * n,
            ap=self.ap + other.ap * n,
            aspd=self.aspd + other.aspd * n,
            crit=self.crit + other.crit * n,
            lifesteal=self.lifesteal + other.lifesteal * n,
            onhit_phys=self.onhit_phys + other.onhit_phys * n,
            wrath=self.wrath + other.wrath * n,
            onhit_magic=self.onhit_magic + other.onhit_magic * n,
            greaves_heal=self.greaves_heal + other.greaves_heal * n,
            bork=self.bork or other.bork,
            guinsoo=self.guinsoo or other.guinsoo,
            runaan=self.runaan or other.runaan,
            shiv=self.shiv or other.shiv,
            terminus=self.terminus or other.terminus,
            shock=self.shock or other.shock,
        )


STATS: dict[str, Stats] = {
    "Long Sword": Stats(ad=12),
    "Dagger": Stats(aspd=0.12),
    "Brawler's Gloves": Stats(crit=0.10),
    "Amplifying Tome": Stats(ap=20),
    "Vampiric Scepter": Stats(ad=15, lifesteal=0.08),
    # 7.3 Recurve: 20% AS. Reinforced (15 physical on-hit) was not listed as removed.
    "Recurve Bow": Stats(aspd=0.20, onhit_phys=15),
    "Pickaxe": Stats(ad=20),
    "Zeal": Stats(aspd=0.15, crit=0.15),
    # Kircheis Shock is a 40 magic proc, not a per-hit on-hit.
    "Kircheis Shard": Stats(aspd=0.20, shock=True),
    "Boots of Speed": Stats(),
    "Blade of the Ruined King": Stats(ad=40, aspd=0.30, lifesteal=0.12, bork=True),
    "Berserker's Greaves": Stats(aspd=0.35, greaves_heal=10),
    "Guinsoo's Rageblade": Stats(ad=35, ap=30, aspd=0.30, wrath=30, guinsoo=True),
    "Runaan's Hurricane": Stats(aspd=0.40, crit=0.25, runaan=True),
    # 7.3 rework: on-hit chain, no crit. Bounce count is additional targets.
    "Statikk Shiv": Stats(ad=40, ap=40, aspd=0.30, shiv=True),
    "Terminus": Stats(ad=35, aspd=0.35, onhit_magic=30, terminus=True),
    "Wit's End": Stats(aspd=0.50, onhit_magic=40),
}

# Energized cap is 100. Base gain matches the current Energized family
# (6 per attack, 1 per 24 units). 7.3 only publishes Shiv's extra +5 per attack.
ENERGY_CAP = 100.0
ENERGY_PER_ATTACK = 6.0
ENERGY_PER_UNIT = 1.0 / 24.0
SHIV_BONUS_STACKS = 5.0
KITE_MOVE_FRACTION = 0.60


def shiv_bounce_count(level: int) -> int:
    """Additional targets. 3 / 4 / 5 / 6 at levels 1 / 5 / 9 / 13."""
    if level >= 13:
        return 6
    if level >= 9:
        return 5
    if level >= 5:
        return 4
    return 3


def move_speed(items: Stats) -> float:
    ms = 335.0 + (45.0 if items.greaves_heal else 0.0)
    if items.shiv:
        ms *= 1.04
    return ms


BORK_CHAIN: list[Step] = [
    Step("Long Sword", 500),
    Step("Vampiric Scepter", 700, (("Long Sword", 1),)),
    Step("Dagger", 400),
    Step("Recurve Bow", 500, (("Dagger", 1),)),
    Step("Long Sword", 500),
    Step("Pickaxe", 300, (("Long Sword", 1),)),
    Step(
        "Blade of the Ruined King",
        200,
        (("Vampiric Scepter", 1), ("Recurve Bow", 1), ("Pickaxe", 1)),
    ),
    Step("Boots of Speed", 400),
    Step("Berserker's Greaves", 500, (("Boots of Speed", 1),)),
]

GUINSOO_CHAIN: list[Step] = [
    Step("Dagger", 400),
    Step("Recurve Bow", 500, (("Dagger", 1),)),
    Step("Long Sword", 500),
    Step("Pickaxe", 300, (("Long Sword", 1),)),
    Step("Amplifying Tome", 500),
    Step(
        "Guinsoo's Rageblade",
        800,
        (("Recurve Bow", 1), ("Pickaxe", 1), ("Amplifying Tome", 1)),
    ),
]

# Same components as GUINSOO_CHAIN, but the long sword is the starting buy
# so it lines up with the BoRK rush (both open Long Sword).
GUINSOO_FIRST_CHAIN: list[Step] = [
    Step("Long Sword", 500),
    Step("Dagger", 400),
    Step("Recurve Bow", 500, (("Dagger", 1),)),
    Step("Pickaxe", 300, (("Long Sword", 1),)),
    Step("Amplifying Tome", 500),
    Step(
        "Guinsoo's Rageblade",
        800,
        (("Recurve Bow", 1), ("Pickaxe", 1), ("Amplifying Tome", 1)),
    ),
]

RUNAAN_CHAIN: list[Step] = [
    Step("Dagger", 400),
    Step("Brawler's Gloves", 500),
    Step("Zeal", 500, (("Dagger", 1), ("Brawler's Gloves", 1))),
    Step("Dagger", 400),
    Step("Kircheis Shard", 400, (("Dagger", 1),)),
    Step("Runaan's Hurricane", 450, (("Zeal", 1), ("Kircheis Shard", 1))),
]


BUILD_PATHS: dict[str, list[Step]] = {
    "Guinsoo 2nd": BORK_CHAIN + GUINSOO_CHAIN + RUNAAN_CHAIN,
    "Runaan 2nd": BORK_CHAIN + RUNAAN_CHAIN + GUINSOO_CHAIN,
}


def purchase(gold: int, steps: list[Step]) -> Counter:
    owned: Counter = Counter()
    spent = 0
    for step in steps:
        if spent + step.cost > gold:
            break
        for name, n in step.consumes:
            if owned[name] < n:
                raise RuntimeError(f"cannot buy {step.name}: missing {n} {name}")
            owned[name] -= n
            if owned[name] == 0:
                del owned[name]
        owned[step.name] += 1
        spent += step.cost
    return owned


def aggregate(owned: Counter) -> Stats:
    total = Stats()
    for name, n in owned.items():
        if n > 0:
            total = total.add(STATS[name], n)
    total.crit = min(1.0, total.crit)
    return total


def item_names(owned: Counter) -> list[str]:
    order = list(STATS.keys())
    return [name for name in order if owned[name] > 0]


# ---------------------------------------------------------------------------
# Targets
# ---------------------------------------------------------------------------

@dataclass
class Target:
    name: str
    max_hp: float
    armor: float
    mr: float
    kind: str  # champion | minion | monster
    hp: float = 0.0
    shred_until: float = -1.0

    def clone(self) -> "Target":
        return Target(self.name, self.max_hp, self.armor, self.mr, self.kind, self.max_hp, -1.0)


def champion_targets(minute: int) -> dict[str, Target]:
    lvl = level_at_minute(minute)
    return {
        "squishy": Target(
            "squishy",
            max_hp=640 + 95 * lvl + 28 * minute,
            armor=28 + 3.2 * lvl + 1.6 * minute,
            mr=30 + 1.2 * lvl + 0.8 * minute,
            kind="champion",
        ),
        "bruiser": Target(
            "bruiser",
            max_hp=780 + 110 * lvl + 48 * minute,
            armor=34 + 3.6 * lvl + 4.5 * minute,
            mr=32 + 1.6 * lvl + 2.2 * minute,
            kind="champion",
        ),
        "tank": Target(
            "tank",
            max_hp=860 + 125 * lvl + 95 * minute,
            armor=42 + 4.0 * lvl + 7.5 * minute,
            mr=34 + 1.8 * lvl + 3.5 * minute,
            kind="champion",
        ),
    }


def dragon_target(minute: int) -> Target:
    return Target(
        "dragon",
        max_hp=2800 + 160 * minute,
        armor=70 + 3.0 * minute,
        mr=60 + 2.5 * minute,
        kind="monster",
    )


def wave_targets(minute: int) -> list[Target]:
    melee_hp = 500 + 22 * minute
    caster_hp = 330 + 14 * minute
    minions = []
    for i in range(3):
        minions.append(Target(f"melee{i}", melee_hp, armor=10, mr=0, kind="minion"))
    for i in range(3):
        minions.append(Target(f"caster{i}", caster_hp, armor=8, mr=0, kind="minion"))
    return minions


# ---------------------------------------------------------------------------
# Combat
# ---------------------------------------------------------------------------

@dataclass
class Loadout:
    level: int
    minute: int
    items: Stats
    ranks: dict[str, int]

    @property
    def base_ad(self) -> float:
        return 54 + 3.5 * (self.level - 1)

    @property
    def bonus_ad(self) -> float:
        return self.items.ad

    @property
    def ad(self) -> float:
        return self.base_ad + self.bonus_ad

    @property
    def ap(self) -> float:
        return self.items.ap

    @property
    def q_as(self) -> float:
        return [0, 0.05, 0.10, 0.15, 0.20, 0.25][self.ranks["Q"]]

    @property
    def w_pct(self) -> float:
        return [0, 0.015, 0.025, 0.035, 0.045][self.ranks["W"]]

    @property
    def shred(self) -> float:
        return [0, 0.16, 0.20, 0.24, 0.28, 0.32][self.ranks["Q"]]

    @property
    def q_raw(self) -> float:
        base = [0, 80, 125, 170, 215, 260][self.ranks["Q"]]
        return base + 0.90 * self.ap

    @property
    def alacrity(self) -> float:
        stacks = max(0, min(6, self.minute - 2))
        return 0.03 * stacks

    @property
    def brutal(self) -> float:
        # Adaptive physical. Primary attacks only — not a free bolt/phantom proc.
        return 5 + 0.06 * self.bonus_ad + 0.03 * self.ap

    def lt_bolt_raw(self, extra_as: float) -> float:
        base = 6 + (24 - 6) * (self.level - 1) / 14
        bonus_pct = bonus_as_fraction(self.level, extra_as) * 100
        return base * (1 + bonus_pct * 0.0067)


@dataclass
class FightResult:
    seconds: float
    attacks: int
    total_damage: float
    healed: float
    ttk_focus: float | None
    wiped_at: float | None
    by_target: dict[str, float]
    breakdown: dict[str, float]
    focus_alive: bool
    wave_clear: float | None = None


def resist_mult(resist: float) -> float:
    if resist >= 0:
        return 100.0 / (100.0 + resist)
    return 2.0 - 100.0 / (100.0 - resist)


def mitigated(raw: float, resist: float, shred: float, pen: float = 0.0) -> float:
    if raw <= 0:
        return 0.0
    effective = resist * (1.0 - shred) * (1.0 - pen)
    return raw * resist_mult(effective)


@dataclass
class FightResultBuilder:
    by_target: dict[str, float] = field(default_factory=dict)
    breakdown: dict[str, float] = field(default_factory=dict)
    healed: float = 0.0
    attacks: int = 0

    def add(self, target: str, bucket: str, amount: float) -> None:
        if amount <= 0:
            return
        self.by_target[target] = self.by_target.get(target, 0.0) + amount
        self.breakdown[bucket] = self.breakdown.get(bucket, 0.0) + amount


def apply_damage(
    builder: FightResultBuilder,
    target: Target,
    raw: float,
    resist: float,
    shred: float,
    bucket: str,
    lifesteal: float,
    pen: float = 0.0,
) -> float:
    if target.hp <= 0 or raw <= 0:
        return 0.0
    dealt = min(target.hp, mitigated(raw, resist, shred, pen))
    target.hp -= dealt
    builder.add(target.name, bucket, dealt)
    builder.healed += dealt * lifesteal
    return dealt


def on_hit_package(
    loadout: Loadout,
    target: Target,
    t: float,
    w_on: bool,
) -> tuple[list[tuple[str, float, str]], float]:
    """On-hit procs Phantom Hit is allowed to duplicate. Returns (bucket, raw, type)."""
    shred = loadout.shred if t < target.shred_until else 0.0
    packets: list[tuple[str, float, str]] = []
    heal = 0.0
    kind = target.kind

    if loadout.items.bork:
        raw = max(15.0, 0.07 * target.hp)
        if kind == "monster":
            raw = min(100.0, raw)
        packets.append(("bork", raw, "phys"))

    if loadout.items.onhit_phys:
        packets.append(("recurve", loadout.items.onhit_phys, "phys"))

    if w_on and loadout.w_pct > 0:
        raw = target.max_hp * (loadout.w_pct + 0.015 * loadout.ap / 100.0)
        if kind in ("minion", "monster"):
            raw = min(100.0, raw)
        packets.append(("w", raw, "magic"))

    if loadout.items.wrath:
        packets.append(("wrath", loadout.items.wrath, "magic"))

    if loadout.items.onhit_magic:
        packets.append(("flat_magic", loadout.items.onhit_magic, "magic"))

    if loadout.items.greaves_heal:
        heal += loadout.items.greaves_heal

    return packets, heal


def deliver_packets(
    builder: FightResultBuilder,
    loadout: Loadout,
    target: Target,
    t: float,
    packets: list[tuple[str, float, str]],
    flat_heal: float,
    pen: float = 0.0,
) -> None:
    shred = loadout.shred if (target.kind == "champion" and t < target.shred_until) else 0.0
    # Monsters can be shredded by Q too.
    if target.kind == "monster" and t < target.shred_until:
        shred = loadout.shred
    cut = 1.0
    if target.kind == "champion" and target.hp > 0.60 * target.max_hp:
        cut = 1.065
    ls = loadout.items.lifesteal
    for bucket, raw, typ in packets:
        resist = target.armor if typ == "phys" else target.mr
        apply_damage(builder, target, raw * cut, resist, shred, bucket, ls, pen)
    builder.healed += flat_heal


def simulate_window(
    loadout: Loadout,
    targets: list[Target],
    seconds: float = W_WINDOW,
    w_on: bool = True,
    use_q: bool = True,
    max_attacks: int | None = None,
    energy_mode: str = "kite",
) -> FightResult:
    units = [t.clone() for t in targets]
    builder = FightResultBuilder()
    t = 0.0
    g_stacks = 0
    phantom_n = 0
    lt_stacks = 0
    next_q = 0.0
    shock_ready = loadout.items.shock
    focus_death: float | None = None
    wipe: float | None = None
    focus_name = units[0].name
    # walked_in: you path onto the fight and the first auto is already Energized.
    energy = ENERGY_CAP if energy_mode == "walked_in" else 0.0
    attack_n = 0
    dark_times: list[float] = []

    def living() -> list[Target]:
        return [u for u in units if u.hp > 0]

    def pen_now(now: float) -> float:
        if not loadout.items.terminus:
            return 0.0
        stacks = sum(1 for ts in dark_times if now - ts <= 5.0)
        return 0.10 * min(3, stacks)

    while t < seconds - 1e-9:
        alive = living()
        if not alive:
            wipe = t
            break
        if max_attacks is not None and builder.attacks >= max_attacks:
            break

        focus = alive[0]
        pen = pen_now(t)
        if use_q and loadout.q_raw > 0 and t >= next_q - 1e-9 and focus.kind != "minion":
            focus.shred_until = t + 4.0
            shred = loadout.shred
            apply_damage(
                builder, focus, loadout.q_raw, focus.mr, shred, "q", 0.0, pen
            )
            next_q = t + 7.0
            if focus.hp <= 0 and focus.name == focus_name and focus_death is None:
                focus_death = t
            alive = living()
            if not alive:
                wipe = t
                break
            focus = alive[0]

        extra_as = (
            loadout.items.aspd
            + loadout.alacrity
            + loadout.q_as
            + 0.08 * g_stacks
            + (0.064 * lt_stacks if focus.kind == "champion" else 0.0)
        )
        aps = attack_speed(loadout.level, extra_as)
        dt = 1.0 / aps

        # Lethal Tempo bolt only once the rune is already stacked, champions only.
        lt_ready = focus.kind == "champion" and lt_stacks >= 6
        shred = loadout.shred if t < focus.shred_until else 0.0
        cut = 1.065 if (focus.kind == "champion" and focus.hp > 0.60 * focus.max_hp) else 1.0
        ls = loadout.items.lifesteal

        energized = loadout.items.shiv and energy >= ENERGY_CAP
        if energized:
            energy -= ENERGY_CAP
            builder.breakdown["shiv_procs"] = builder.breakdown.get("shiv_procs", 0) + 1
            lightning = 90.0 if focus.kind in ("minion", "monster") else 60.0
            apply_damage(
                builder, focus, lightning * cut, focus.mr, shred, "shiv", ls, pen
            )

        auto_raw = loadout.ad * (1.0 + loadout.items.crit * (CRIT_DAMAGE - 1.0))
        apply_damage(builder, focus, auto_raw * cut, focus.armor, shred, "auto", ls, pen)

        if focus.kind == "champion":
            apply_damage(
                builder, focus, loadout.brutal * cut, focus.armor, shred, "brutal", ls, pen
            )
            if lt_ready and focus.hp > 0:
                bolt = loadout.lt_bolt_raw(extra_as)
                apply_damage(builder, focus, bolt * cut, focus.armor, shred, "lt", ls, pen)

        if shock_ready and focus.kind == "champion" and focus.hp > 0:
            apply_damage(builder, focus, 40.0 * cut, focus.mr, shred, "shock", ls, pen)
            shock_ready = False

        packets, flat_heal = on_hit_package(loadout, focus, t, w_on)
        deliver_packets(builder, loadout, focus, t, packets, flat_heal, pen)

        # Phantom Hit: extra on-hit on the primary only, after the first packet.
        if loadout.items.guinsoo and g_stacks >= 4 and focus.hp > 0:
            phantom_n += 1
            if phantom_n % 3 == 0:
                packets, flat_heal = on_hit_package(loadout, focus, t, w_on)
                deliver_packets(builder, loadout, focus, t, packets, flat_heal, pen)
                builder.breakdown["phantom_procs"] = builder.breakdown.get("phantom_procs", 0) + 1

        if focus.hp <= 0 and focus.name == focus_name and focus_death is None:
            focus_death = t + dt

        # Bolts pick other living units. They apply on-hit once. They do not crit-double
        # phantom, and they do not carry Brutal or Lethal Tempo.
        if loadout.items.runaan:
            sides = [u for u in living() if u is not focus][:2]
            bolt_ad = 0.55 * loadout.ad * (1.0 + loadout.items.crit * (CRIT_DAMAGE - 1.0))
            for side in sides:
                side_cut = 1.065 if (side.kind == "champion" and side.hp > 0.60 * side.max_hp) else 1.0
                side_shred = loadout.shred if t < side.shred_until else 0.0
                apply_damage(
                    builder, side, bolt_ad * side_cut, side.armor, side_shred, "bolt_ad", ls, pen
                )
                packets, flat_heal = on_hit_package(loadout, side, t, w_on)
                # Retag so the report can see splash on-hit separately from primary W/BoRK.
                retagged = []
                for bucket, raw, typ in packets:
                    name = bucket if bucket in ("w", "bork", "wrath", "recurve", "flat_magic") else bucket
                    retagged.append((f"bolt_{name}", raw, typ))
                deliver_packets(builder, loadout, side, t, retagged, flat_heal, pen)

        # Chain hits other living units. On-hit on those bounces is full strength.
        # It does not repeat Phantom Hit and it does not add a second auto.
        if energized:
            bounces = [u for u in living() if u is not focus][: shiv_bounce_count(loadout.level)]
            for side in bounces:
                side_cut = 1.065 if (side.kind == "champion" and side.hp > 0.60 * side.max_hp) else 1.0
                side_shred = loadout.shred if t < side.shred_until else 0.0
                lightning = 90.0 if side.kind in ("minion", "monster") else 60.0
                apply_damage(
                    builder, side, lightning * side_cut, side.mr, side_shred, "shiv_bounce", ls, pen
                )
                packets, flat_heal = on_hit_package(loadout, side, t, w_on)
                retagged = []
                for bucket, raw, typ in packets:
                    retagged.append((f"shiv_{bucket}", raw, typ))
                deliver_packets(builder, loadout, side, t, retagged, flat_heal, pen)

        if loadout.items.shiv:
            energy += ENERGY_PER_ATTACK + SHIV_BONUS_STACKS
            if energy_mode in ("kite", "walked_in"):
                energy += move_speed(loadout.items) * dt * KITE_MOVE_FRACTION * ENERGY_PER_UNIT

        # Dark stacks apply on every second attack and then pen the hits after them.
        if loadout.items.terminus and attack_n % 2 == 1:
            dark_times.append(t)

        if loadout.items.guinsoo:
            g_stacks = min(4, g_stacks + 1)
        if focus.kind == "champion":
            lt_stacks = min(6, lt_stacks + 1)

        builder.attacks += 1
        attack_n += 1
        t += dt

    if wipe is None and not living():
        wipe = min(t, seconds)

    total = sum(builder.by_target.values())
    focus_alive = any(u.name == focus_name and u.hp > 0 for u in units)
    return FightResult(
        seconds=min(t, seconds),
        attacks=builder.attacks,
        total_damage=total,
        healed=builder.healed,
        ttk_focus=focus_death,
        wiped_at=wipe,
        by_target=builder.by_target,
        breakdown=builder.breakdown,
        focus_alive=focus_alive,
        wave_clear=wipe if units and units[0].kind == "minion" else None,
    )


def loadout_at(path: list[Step], minute: int) -> tuple[Loadout, Counter]:
    owned = purchase(gold_at_minute(minute), path)
    lvl = level_at_minute(minute)
    load = Loadout(level=lvl, minute=minute, items=aggregate(owned), ranks=ranks_at_level(lvl))
    return load, owned


def first_minute_with(path: list[Step], item: str) -> int | None:
    for m in range(1, GAME_MINUTES + 1):
        owned = purchase(gold_at_minute(m), path)
        if owned[item] > 0:
            return m
    return None


# ---------------------------------------------------------------------------
# Scenarios
# ---------------------------------------------------------------------------

def scenario_pack(loadout: Loadout, minute: int) -> dict[str, FightResult]:
    champs = champion_targets(minute)
    tank = champs["tank"]
    bruiser = champs["bruiser"]
    squishy = champs["squishy"]
    return {
        "tank": simulate_window(loadout, [tank]),
        "tank4": simulate_window(loadout, [tank], seconds=4.0),
        "tank_w_down": simulate_window(loadout, [tank], w_on=False),
        "duel": simulate_window(loadout, [squishy]),
        "skirmish2": simulate_window(loadout, [bruiser, squishy]),
        "fight3": simulate_window(loadout, [tank, bruiser, squishy]),
        "trade3": simulate_window(loadout, [bruiser], max_attacks=3),
        "dragon": simulate_window(loadout, [dragon_target(minute)]),
        "wave": simulate_window(loadout, wave_targets(minute), seconds=14.0, use_q=False),
    }


def stats_for(*names: str) -> Stats:
    total = Stats()
    for name in names:
        total = total.add(STATS[name])
    return total


def isolated_at(minute: int) -> dict[str, dict]:
    """BoRK + Greaves + one legendary, no components of the other item."""
    lvl = level_at_minute(minute)
    ranks = ranks_at_level(lvl)
    out = {}
    for label, legendary in (
        ("Guinsoo", "Guinsoo's Rageblade"),
        ("Runaan", "Runaan's Hurricane"),
    ):
        load = Loadout(
            level=lvl,
            minute=minute,
            items=stats_for("Blade of the Ruined King", "Berserker's Greaves", legendary),
            ranks=ranks,
        )
        pack = scenario_pack(load, minute)
        out[label] = {
            "tank_ttk": pack["tank"].ttk_focus,
            "tank4": round(pack["tank4"].total_damage, 1),
            "w_down": round(pack["tank_w_down"].total_damage, 1),
            "duel_ttk": pack["duel"].ttk_focus,
            "trade3": round(pack["trade3"].total_damage, 1),
            "fight_dmg": round(pack["fight3"].total_damage, 1),
            "fight_wipe": pack["fight3"].wiped_at,
            "fight_tank_ttk": pack["fight3"].ttk_focus,
            "fight_heal": round(pack["fight3"].healed, 1),
            "dragon": round(pack["dragon"].total_damage, 1),
            "wave": pack["wave"].wave_clear,
            "phantom": pack["tank"].breakdown.get("phantom_procs", 0),
            "attacks": pack["tank"].attacks,
            "breakdown": {k: round(v, 1) for k, v in pack["tank"].breakdown.items()},
            "fight_breakdown": {k: round(v, 1) for k, v in pack["fight3"].breakdown.items()},
        }
    return out


def team_targets(minute: int) -> list[Target]:
    champs = champion_targets(minute)
    tank = champs["tank"]
    bruiser = champs["bruiser"]
    squishy = champs["squishy"]
    return [
        tank,
        bruiser,
        Target("bruiser-2", bruiser.max_hp, bruiser.armor, bruiser.mr, "champion"),
        squishy,
        Target("carry-2", squishy.max_hp, squishy.armor, squishy.mr, "champion"),
    ]


def _row_for(load: Loadout, minute: int, energy_mode: str) -> dict:
    champs = champion_targets(minute)
    tank = simulate_window(load, [champs["tank"]], energy_mode=energy_mode)
    tank4 = simulate_window(load, [champs["tank"]], seconds=4.0, energy_mode=energy_mode)
    fight3 = simulate_window(
        load, [champs["tank"], champs["bruiser"], champs["squishy"]], energy_mode=energy_mode
    )
    fight5 = simulate_window(load, team_targets(minute), energy_mode=energy_mode)
    wave = simulate_window(
        load, wave_targets(minute), seconds=14.0, use_q=False, energy_mode=energy_mode
    )
    dragon = simulate_window(load, [dragon_target(minute)], energy_mode=energy_mode)
    return {
        "tank_ttk": tank.ttk_focus,
        "tank4": tank4.total_damage,
        "fight3": fight3.total_damage,
        "wipe3": fight3.wiped_at,
        "fight5": fight5.total_damage,
        "wipe5": fight5.wiped_at,
        "wave": wave.wave_clear,
        "dragon": dragon.total_damage,
        "dragon_ttk": dragon.ttk_focus,
        "procs": tank.breakdown.get("shiv_procs", 0),
        "procs5": fight5.breakdown.get("shiv_procs", 0),
        "procs_wave": wave.breakdown.get("shiv_procs", 0),
    }


def rush_metrics(load: Loadout, minute: int) -> dict:
    champs = champion_targets(minute)
    duel = simulate_window(load, [champs["squishy"]])
    trade = simulate_window(load, [champs["squishy"]], max_attacks=3)
    tank = simulate_window(load, [champs["tank"]])
    wave = simulate_window(load, wave_targets(minute), seconds=14.0, use_q=False)
    dragon = simulate_window(load, [dragon_target(minute)])
    return {
        "duel_ttk": duel.ttk_focus,
        "trade": trade.total_damage,
        "tank_ttk": tank.ttk_focus,
        "tank4": tank.total_damage if tank.ttk_focus is None else None,
        "heal": duel.healed,
        "wave": wave.wave_clear,
        "dragon_ttk": dragon.ttk_focus,
        "phantom": duel.breakdown.get("phantom_procs", 0),
    }


def rush_section() -> list[str]:
    """BoRK 3100 first vs Guinsoo 3000 first, then Berserker's, then the other."""
    boots = BORK_CHAIN[-2:]
    bork_only = BORK_CHAIN[:-2]
    paths = {
        "BoRK": bork_only + boots + GUINSOO_CHAIN,
        "Guinsoo": GUINSOO_FIRST_CHAIN + boots + bork_only,
    }
    rows: dict[str, list[dict]] = {name: [] for name in paths}
    for minute in range(1, 14):
        for name, path in paths.items():
            load, owned = loadout_at(path, minute)
            row = rush_metrics(load, minute)
            row["items"] = item_names(owned)
            row["label"] = short_items(Counter({n: 1 for n in row["items"]}))
            rows[name].append(row)

    bork_at = next(i + 1 for i, row in enumerate(rows["BoRK"]) if "Blade of the Ruined King" in row["items"])
    guin_at = next(i + 1 for i, row in enumerate(rows["Guinsoo"]) if "Guinsoo's Rageblade" in row["items"])
    both_at = next(
        i + 1
        for i, (b, g) in enumerate(zip(rows["BoRK"], rows["Guinsoo"]))
        if "Blade of the Ruined King" in b["items"]
        and "Guinsoo's Rageblade" in b["items"]
        and "Blade of the Ruined King" in g["items"]
        and "Guinsoo's Rageblade" in g["items"]
    )

    lines = [
        "",
        "-" * 78,
        "FIRST ITEM — RUSH BoRK (3100) vs RUSH GUINSOO (3000)",
        "Then Berserker's Greaves, then the other legendary. Long Sword start on both.",
        "Duel and the 3-hit trade are the enemy carry. Tank is a frontliner. Heal is from the duel.",
        "-" * 78,
        f"  {'Min':>3}  {'BoRK rush':<28} {'Duel':>6} {'Trade':>6} {'Tank':>6} {'Heal':>5} {'Wave':>6}"
        f"  {'Guinsoo rush':<28} {'Duel':>6} {'Trade':>6} {'Tank':>6} {'Heal':>5} {'Wave':>6}",
    ]
    for i, (b, g) in enumerate(zip(rows["BoRK"], rows["Guinsoo"])):
        minute = i + 1
        if minute < 3:
            continue
        lines.append(
            f"  {minute:>3}  {clip_label(b['label'], 28):<28} "
            f"{fmt_time(b['duel_ttk']):>6} {b['trade']:>6.0f} {fmt_time(b['tank_ttk']):>6} "
            f"{b['heal']:>5.0f} {fmt_time(b['wave']):>6}  "
            f"{clip_label(g['label'], 28):<28} "
            f"{fmt_time(g['duel_ttk']):>6} {g['trade']:>6.0f} {fmt_time(g['tank_ttk']):>6} "
            f"{g['heal']:>5.0f} {fmt_time(g['wave']):>6}"
        )

    lines.append("")
    lines.append(
        f"  BoRK completes {bork_at}:00. Guinsoo completes {guin_at}:00. "
        f"Both legendaries on both paths: {both_at}:00."
    )
    spike = min(bork_at, guin_at)
    b_spike = rows["BoRK"][spike - 1]
    g_spike = rows["Guinsoo"][spike - 1]
    lines.append(f"  At the shared spike ({spike}:00, level {level_at_minute(spike)}):")
    lines.append(
        f"    Lane all-in:     BoRK {fmt_time(b_spike['duel_ttk'])} | "
        f"Guinsoo {fmt_time(g_spike['duel_ttk'])}"
    )
    lines.append(
        f"    3-hit trade:     BoRK {b_spike['trade']:.0f} | Guinsoo {g_spike['trade']:.0f}"
    )
    lines.append(
        f"    Frontliner:      BoRK {fmt_time(b_spike['tank_ttk'])} | "
        f"Guinsoo {fmt_time(g_spike['tank_ttk'])}"
    )
    lines.append(
        f"    Heal in the duel: BoRK {b_spike['heal']:.0f} | Guinsoo {g_spike['heal']:.0f}"
    )
    lines.append(
        f"    Wave / dragon:   BoRK {fmt_time(b_spike['wave'])} / {fmt_time(b_spike['dragon_ttk'])} | "
        f"Guinsoo {fmt_time(g_spike['wave'])} / {fmt_time(g_spike['dragon_ttk'])}"
    )
    lines.append(
        f"  At {both_at}:00 both paths hold BoRK + Greaves + Guinsoo and the rows match."
    )
    last_b = rows["BoRK"][both_at - 1]
    last_g = rows["Guinsoo"][both_at - 1]
    assert last_b["trade"] == last_g["trade"]
    assert last_b["duel_ttk"] == last_g["duel_ttk"]
    assert abs(last_b["heal"] - last_g["heal"]) < 1.0
    lines.append("")
    lines.append("  PROS — RUSH BoRK")
    lines.append("  • Vampiric Scepter is in the build path, so lane healing starts before the")
    lines.append("    item exists. Finished BoRK is 12% lifesteal. Guinsoo has none until later.")
    lines.append("  • The 7% current-health hit is immediate. A 3-auto trade does not need stacks.")
    lines.append("  • Three hits also slow the target by 30% for 1.5s. That is stick and kite,")
    lines.append("    and it is not in the damage numbers above.")
    lines.append("  • The combine is 200g after a 300g Pickaxe. Guinsoo's last payment is 800g,")
    lines.append("    so a short recall can finish BoRK and cannot finish Guinsoo. On this")
    lines.append("    gold curve both still complete at the same minute.")
    lines.append("  CONS — RUSH BoRK")
    lines.append("  • Current-health damage shrinks as the target drops. A long fight into a")
    lines.append("    tank gets less from the passive than Guinsoo's repeat of max-health Barrage.")
    lines.append("  • No attack-speed steroid and no Phantom Hit. Extended all-ins ramp slower.")
    lines.append("")
    lines.append("  PROS — RUSH GUINSOO")
    lines.append("  • 100g cheaper. Recurve + Pickaxe + Tome, before the combine, already wins")
    lines.append("    the lane all-in against Vamp + Recurve. Phantom Hit then repeats Barrage")
    lines.append("    (max health, so it keeps working on a low tank) and Seething Strike adds")
    lines.append("    up to 32% attack speed in a long fight.")
    lines.append("  • 30 AP adds a little to Barrage and Caustic Spittle.")
    lines.append("  CONS — RUSH GUINSOO")
    lines.append("  • No lifesteal at all until BoRK is the second legendary. You lose the lane")
    lines.append("    sustain war and the 3-hit slow.")
    lines.append("  • Phantom Hit is the 7th attack of a fight. A short trade never sees it.")
    lines.append("  • The 800g combine is the awkward base: components are done, the item is not.")
    return lines


def clip_label(text: str, width: int) -> str:
    if len(text) <= width:
        return text
    return text[: width - 1] + "…"


def shiv_section(minute: int = 15) -> list[str]:
    """On-hit core is BoRK + Greaves + Guinsoo. Shiv competes with Runaan for the spread slot."""
    lvl = level_at_minute(minute)
    ranks = ranks_at_level(lvl)
    builds = [
        ("Guinsoo + Runaan", ("Blade of the Ruined King", "Berserker's Greaves", "Guinsoo's Rageblade", "Runaan's Hurricane")),
        ("Guinsoo + Shiv", ("Blade of the Ruined King", "Berserker's Greaves", "Guinsoo's Rageblade", "Statikk Shiv")),
        ("Runaan + Shiv", ("Blade of the Ruined King", "Berserker's Greaves", "Guinsoo's Rageblade", "Runaan's Hurricane", "Statikk Shiv")),
        ("Runaan + Terminus", ("Blade of the Ruined King", "Berserker's Greaves", "Guinsoo's Rageblade", "Runaan's Hurricane", "Terminus")),
        ("Runaan + Wit's End", ("Blade of the Ruined King", "Berserker's Greaves", "Guinsoo's Rageblade", "Runaan's Hurricane", "Wit's End")),
    ]
    lines = [
        "",
        "-" * 78,
        f"STATIKK SHIV ON ON-HIT KOG ({minute}:00, level {lvl}, Q{ranks['Q']}/W{ranks['W']})",
        "Core is BoRK + Greaves + Guinsoo. Shiv is the 7.3 on-hit chain, not a crit item.",
        "Kite: move between autos, charge starts empty. Walked-in: first auto is already Energized.",
        "-" * 78,
    ]
    header = (
        f"  {'Build':<20} {'Tank':>6} {'3-man':>6} {'5-man':>6} "
        f"{'Wave':>6} {'Dragon':>6} {'Proc':>5}"
    )
    for mode, title in (
        ("kite", "KITING, CHARGE STARTS AT 0"),
        ("still", "STANDING STILL, CHARGE STARTS AT 0"),
        ("walked_in", "WALKED INTO THE FIGHT ALREADY ENERGIZED"),
    ):
        lines.append(f"  {title}")
        lines.append(header)
        for label, names in builds:
            load = Loadout(lvl, minute, stats_for(*names), ranks)
            row = _row_for(load, minute, mode)
            lines.append(
                f"  {label:<20} {fmt_time(row['tank_ttk']):>6} {fmt_time(row['wipe3']):>6} "
                f"{fmt_time(row['wipe5']):>6} {fmt_time(row['wave']):>6} "
                f"{fmt_time(row['dragon_ttk']):>6} {row['procs5']:>5.0f}"
            )
        lines.append("")
    lines.append("  Times are how long the target or the group stays alive. 'lives' means")
    lines.append("  they are still up at the end of the 8s Barrage (14s for the wave).")
    lines.append("  HOW TO READ THE PROC COLUMN")
    lines.append("  Proc is Energized chains during the 5-champion fight. Each chain can touch")
    lines.append("  up to 6 other units at level 13 and puts W, BoRK, and Guinsoo's 30 magic")
    lines.append("  on-hit on them once. Runaan puts those on-hits on 2 units on every auto.")
    lines.append("  Shiv costs 3000. Runaan costs 2650. Terminus and Wit's End are the other")
    lines.append("  last-slot damage items if the game actually reaches a 5th legendary.")
    lines.append("  Even-gold core (BoRK + Greaves + Guinsoo + Runaan) is 9650 and finishes")
    lines.append(f"  at 17:00. Adding Shiv makes 12650. Gold at 18:00 is {gold_at_minute(18)}.")
    lines.append("")
    lines.append("  SHIV VERDICT")
    lines.append("  • Skip it. On-hit Kog already has the spread item: Runaan hits 2 extra")
    lines.append("    units on every auto. Shiv's chain fires about twice per Barrage, so the")
    lines.append("    6-target bounce does not replace that.")
    lines.append("  • Guinsoo + Shiv, with no Runaan: the 3-champion fight is still alive")
    lines.append("    when Barrage ends. Guinsoo + Runaan wipes that fight in 5.8s. The wave")
    lines.append("    goes from 3.4s to 6.5s. The solo tank is only ~0.3s faster.")
    lines.append("  • Guinsoo + Runaan + Shiv does wipe a 5-champion clump inside Barrage")
    lines.append("    (7.1s). Terminus in that same slot also wipes it (7.1s) and kills the")
    lines.append("    tank in 3.6s instead of 4.0s and the dragon in 5.7s instead of 6.9s.")
    lines.append("  • An even 18:00 game has 10770 gold. The 4-item core is 9650. The 3000g")
    lines.append("    Shiv does not fit unless you are ahead or the game runs long, and the")
    lines.append("    long-game slot is Terminus when a frontliner is the problem.")
    return lines


def fmt_time(value: float | None) -> str:
    if value is None:
        return "lives"
    return f"{value:.1f}s"


def rel_pct(new: float, old: float) -> float:
    if old <= 0:
        return 0.0
    return (new - old) / old * 100.0


SHORT = {
    "Blade of the Ruined King": "BoRK",
    "Berserker's Greaves": "Greaves",
    "Guinsoo's Rageblade": "Guinsoo",
    "Runaan's Hurricane": "Runaan",
    "Recurve Bow": "Recurve",
    "Pickaxe": "Pickaxe",
    "Amplifying Tome": "Tome",
    "Zeal": "Zeal",
    "Kircheis Shard": "Kircheis",
    "Vampiric Scepter": "Vamp",
    "Long Sword": "Sword",
    "Dagger": "Dagger",
    "Brawler's Gloves": "Gloves",
    "Boots of Speed": "Boots",
}

CORE_ITEMS = {"Blade of the Ruined King", "Berserker's Greaves", "Boots of Speed"}


def short_items(owned: Counter) -> str:
    return " + ".join(SHORT.get(n, n) for n in item_names(owned)) or "(empty)"


def fork_label(items: list[str]) -> str:
    """What this path holds beyond the shared BoRK + Greaves rush."""
    extra = [n for n in items if n not in CORE_ITEMS]
    if not extra:
        if "Berserker's Greaves" in items:
            text = "BoRK + Greaves"
        elif "Blade of the Ruined King" in items:
            text = "BoRK"
        else:
            text = short_items(Counter({n: 1 for n in items}))
    else:
        text = short_items(Counter({n: 1 for n in extra}))
    if len(text) <= 24:
        return text
    return text[:23] + "…"


def run() -> dict:
    results: dict[str, list[dict]] = {name: [] for name in BUILD_PATHS}
    for minute in range(1, GAME_MINUTES + 1):
        for name, path in BUILD_PATHS.items():
            load, owned = loadout_at(path, minute)
            pack = scenario_pack(load, minute)
            results[name].append(
                {
                    "minute": minute,
                    "gold": gold_at_minute(minute),
                    "level": load.level,
                    "ranks": load.ranks,
                    "items": item_names(owned),
                    "ad": round(load.ad, 1),
                    "ap": round(load.ap, 1),
                    "bonus_as": round(load.items.aspd + load.alacrity + load.q_as, 3),
                    "crit": round(load.items.crit, 3),
                    "tank_dmg": round(pack["tank"].total_damage, 1),
                    "tank_ttk": pack["tank"].ttk_focus,
                    "tank4": round(pack["tank4"].total_damage, 1),
                    "tank_heal": round(pack["tank"].healed, 1),
                    "tank_attacks": pack["tank"].attacks,
                    "tank_breakdown": {k: round(v, 1) for k, v in pack["tank"].breakdown.items()},
                    "fight_breakdown": {k: round(v, 1) for k, v in pack["fight3"].breakdown.items()},
                    "fight_heal": round(pack["fight3"].healed, 1),
                    "fight_tank_ttk": pack["fight3"].ttk_focus,
                    "w_down_dmg": round(pack["tank_w_down"].total_damage, 1),
                    "duel_dmg": round(pack["duel"].total_damage, 1),
                    "duel_ttk": pack["duel"].ttk_focus,
                    "skirmish2_dmg": round(pack["skirmish2"].total_damage, 1),
                    "fight3_dmg": round(pack["fight3"].total_damage, 1),
                    "fight3_wipe": pack["fight3"].wiped_at,
                    "trade3_dmg": round(pack["trade3"].total_damage, 1),
                    "dragon_dmg": round(pack["dragon"].total_damage, 1),
                    "dragon_ttk": pack["dragon"].ttk_focus,
                    "wave_time": pack["wave"].wave_clear,
                    "wave_dmg": round(pack["wave"].total_damage, 1),
                }
            )
    return results


def self_check(results: dict) -> None:
    # Patch 7.3 worked example: level-15 Caitlyn bonus from levels is 0.04 × 14.
    assert abs(level_as_bonus(0.04, 15) - 0.56) < 1e-9
    cait = 0.625 + 0.625 * (0.28 + level_as_bonus(0.04, 15) + 0.18 + 0.35)
    assert abs(cait - 1.48125) < 1e-6

    # 100 damage into 100 resist is 50.
    assert abs(mitigated(100, 100, 0) - 50) < 1e-9

    g_done = first_minute_with(BUILD_PATHS["Guinsoo 2nd"], "Guinsoo's Rageblade")
    r_done = first_minute_with(BUILD_PATHS["Runaan 2nd"], "Runaan's Hurricane")
    assert g_done is not None and r_done is not None
    assert r_done < g_done

    # Once both legendaries are finished, the inventories match and so does tank damage.
    both = None
    for m in range(1, GAME_MINUTES + 1):
        g_items = set(results["Guinsoo 2nd"][m - 1]["items"])
        r_items = set(results["Runaan 2nd"][m - 1]["items"])
        if "Guinsoo's Rageblade" in g_items and "Runaan's Hurricane" in g_items:
            both = m
            assert g_items == r_items
            assert abs(
                results["Guinsoo 2nd"][m - 1]["tank_dmg"]
                - results["Runaan 2nd"][m - 1]["tank_dmg"]
            ) < 1.0
            break
    assert both is not None

    # A finished 2-item Kog actually attacks and deals damage.
    row = results["Guinsoo 2nd"][g_done - 1]
    assert row["tank_attacks"] >= 8
    assert row["tank_dmg"] > 1000

    # Shiv chains at least once if you walk into a fight fully Energized,
    # and a build without Shiv never records a proc.
    lvl = level_at_minute(15)
    ranks = ranks_at_level(lvl)
    shiv_load = Loadout(
        lvl, 15,
        stats_for("Blade of the Ruined King", "Berserker's Greaves", "Guinsoo's Rageblade", "Statikk Shiv"),
        ranks,
    )
    bare = Loadout(
        lvl, 15,
        stats_for("Blade of the Ruined King", "Berserker's Greaves", "Guinsoo's Rageblade", "Runaan's Hurricane"),
        ranks,
    )
    shiv_fight = simulate_window(shiv_load, team_targets(15), energy_mode="walked_in")
    bare_fight = simulate_window(bare, team_targets(15), energy_mode="walked_in")
    assert shiv_fight.breakdown.get("shiv_procs", 0) >= 1
    assert bare_fight.breakdown.get("shiv_procs", 0) == 0
    assert shiv_bounce_count(13) == 6
    assert shiv_bounce_count(1) == 3


def summarize(results: dict) -> str:
    g_path = results["Guinsoo 2nd"]
    r_path = results["Runaan 2nd"]
    g_done = first_minute_with(BUILD_PATHS["Guinsoo 2nd"], "Guinsoo's Rageblade")
    r_done = first_minute_with(BUILD_PATHS["Runaan 2nd"], "Runaan's Hurricane")
    both = next(
        m
        for m in range(1, GAME_MINUTES + 1)
        if "Guinsoo's Rageblade" in g_path[m - 1]["items"]
        and "Runaan's Hurricane" in g_path[m - 1]["items"]
    )
    fork = next(
        m
        for m in range(1, GAME_MINUTES + 1)
        if g_path[m - 1]["items"] != r_path[m - 1]["items"]
    )

    lines: list[str] = []
    lines.append("=" * 78)
    lines.append("KOG'MAW — RUNAAN vs GUINSOO AS THE ITEM AFTER BoRK + GREAVES")
    lines.append("Wild Rift patch 7.3 | Dragon lane | W window = 8s | even gold, not fed")
    lines.append("=" * 78)
    lines.append("")
    lines.append("PATHS (same gold, fork after Berserker's Greaves)")
    lines.append("  Guinsoo 2nd: BoRK → Greaves → Guinsoo's Rageblade → Runaan's Hurricane")
    lines.append("  Runaan 2nd:  BoRK → Greaves → Runaan's Hurricane → Guinsoo's Rageblade")
    lines.append("")
    lines.append("GOLD / LEVEL")
    lines.append(f"  {'Min':>3}  {'Gold':>6}  {'Lvl':>3}")
    for m in range(1, GAME_MINUTES + 1):
        lines.append(f"  {m:>3}  {gold_at_minute(m):>6}  {level_at_minute(m):>3}")
    lines.append("")
    lines.append(
        f"  Paths match until {fork}:00. Runaan completes {r_done}:00. "
        f"Guinsoo completes {g_done}:00. Both items owned {both}:00."
    )
    lines.append("  Runaan is 2650g. Guinsoo is 3000g. The gap is 350g, about one wave.")
    lines.append("")
    lines.append("-" * 78)
    lines.append("W WINDOW — TANK TIME-TO-KILL, 3-CHAMPION HP REMOVED, WAVE CLEAR")
    lines.append("Tank ttk is solo frontliner. Fight is tank + bruiser + squishy standing in bolt range.")
    lines.append("Both paths share BoRK + Greaves; the label is only the items after that.")
    lines.append("-" * 78)
    lines.append(
        f"  {'Min':>3}  {'Guinsoo path':<24} {'ttk':>6} {'Fight':>7} {'Wave':>6}  "
        f"{'Runaan path':<24} {'ttk':>6} {'Fight':>7} {'Wave':>6}"
    )
    for m in range(1, GAME_MINUTES + 1):
        g = g_path[m - 1]
        r = r_path[m - 1]
        lines.append(
            f"  {m:>3}  {fork_label(g['items']):<24} "
            f"{fmt_time(g['tank_ttk']):>6} {g['fight3_dmg']:>7.0f} {fmt_time(g['wave_time']):>6}  "
            f"{fork_label(r['items']):<24} "
            f"{fmt_time(r['tank_ttk']):>6} {r['fight3_dmg']:>7.0f} {fmt_time(r['wave_time']):>6}"
        )

    def block(title: str, minute: int) -> None:
        g = g_path[minute - 1]
        r = r_path[minute - 1]
        lines.append("")
        lines.append("-" * 78)
        lines.append(f"{title}  ({minute}:00, {g['gold']}g, level {g['level']}, Q{g['ranks']['Q']}/W{g['ranks']['W']})")
        lines.append("-" * 78)
        lines.append(f"  Guinsoo path: {short_items(Counter({n: 1 for n in g['items']}))}")
        lines.append(f"  Runaan path:  {short_items(Counter({n: 1 for n in r['items']}))}")
        rows = [
            ("Tank ttk", "tank_ttk", None, True),
            ("Tank dmg in 4s", "tank4", None, False),
            ("Tank, W down", "w_down_dmg", None, False),
            ("Squishy ttk", "duel_ttk", None, True),
            ("3-hit trade", "trade3_dmg", None, False),
            ("3 nearby HP", "fight3_dmg", "fight3_wipe", False),
            ("Dragon in 8s", "dragon_dmg", None, False),
            ("Wave clear", "wave_time", None, True),
        ]
        lines.append(f"  {'Window':<16} {'Guinsoo':>10} {'Runaan':>10} {'Runaan vs G':>12}")
        time_keys = {"wave_time", "tank_ttk", "duel_ttk"}
        for label, key, time_key, _lower_better in rows:
            gv = g[key]
            rv = r[key]
            if key in time_keys:
                g_txt = fmt_time(gv)
                r_txt = fmt_time(rv)
                if gv and rv:
                    d_txt = f"{rel_pct(rv, gv):+.0f}% time"
                else:
                    d_txt = "—"
            else:
                g_txt = f"{gv:.0f}"
                r_txt = f"{rv:.0f}"
                d_txt = f"{rel_pct(rv, gv):+.0f}%"
            lines.append(f"  {label:<16} {g_txt:>10} {r_txt:>10} {d_txt:>12}")
            if time_key:
                lines.append(
                    f"  {'wipe':<16} {fmt_time(g[time_key]):>10} {fmt_time(r[time_key]):>10}"
                )
        lines.append(
            f"  Heal, solo tank / 3-champion fight: "
            f"Guinsoo {g['tank_heal']:.0f} / {g['fight_heal']:.0f} | "
            f"Runaan {r['tank_heal']:.0f} / {r['fight_heal']:.0f}"
        )
        lines.append(
            f"  In the 3-champion fight the tank falls at "
            f"{fmt_time(g['fight_tank_ttk'])} (Guinsoo path) / "
            f"{fmt_time(r['fight_tank_ttk'])} (Runaan path)."
        )
        lines.append("  Solo-tank sources (Guinsoo path / Runaan path):")
        keys = [
            "auto", "w", "bork", "wrath", "recurve", "bolt_ad", "bolt_w",
            "bolt_bork", "q", "brutal", "lt", "phantom_procs",
        ]
        for key in keys:
            gv = g["tank_breakdown"].get(key, 0.0)
            rv = r["tank_breakdown"].get(key, 0.0)
            if gv == 0 and rv == 0:
                continue
            lines.append(f"    {key:<10} {gv:>8.0f}  {rv:>8.0f}")

    block("SPIKE — RUNAAN COMPLETES, GUINSOO IS STILL COMPONENTS", r_done)
    block("SPIKE — GUINSOO COMPLETES, RUNAAN PATH HAS HURRICANE ONLY", g_done)
    # A minute in the middle of the real fork, if there is one.
    if g_done + 2 < both:
        block("MID FORK — EACH BUILD OWNS ITS ITEM, NOT THE OTHER", g_done + 2)
    block("BOTH ITEMS FINISHED — ORDER NO LONGER MATTERS", both)

    iso_min = g_done
    iso = isolated_at(iso_min)
    ig, ir = iso["Guinsoo"], iso["Runaan"]
    lines.append("")
    lines.append("-" * 78)
    lines.append(
        f"ITEM VS ITEM — BoRK + GREAVES + ONE LEGENDARY, NOTHING ELSE ({iso_min}:00 targets)"
    )
    lines.append("No component of the other item. This is the raw second-item choice.")
    lines.append("-" * 78)
    iso_rows = [
        ("Tank ttk", "tank_ttk", True),
        ("Tank dmg in 4s", "tank4", False),
        ("Tank, W down", "w_down", False),
        ("Squishy ttk", "duel_ttk", True),
        ("3-hit trade", "trade3", False),
        ("3 nearby HP", "fight_dmg", False),
        ("Dragon in 8s", "dragon", False),
        ("Wave clear", "wave", True),
    ]
    lines.append(f"  {'Window':<16} {'Guinsoo':>10} {'Runaan':>10} {'Runaan vs G':>12}")
    for label, key, is_time in iso_rows:
        gv, rv = ig[key], ir[key]
        if is_time:
            g_txt, r_txt = fmt_time(gv), fmt_time(rv)
            d_txt = f"{rel_pct(rv, gv):+.0f}% time" if gv and rv else "—"
        else:
            g_txt, r_txt = f"{gv:.0f}", f"{rv:.0f}"
            d_txt = f"{rel_pct(rv, gv):+.0f}%"
        lines.append(f"  {label:<16} {g_txt:>10} {r_txt:>10} {d_txt:>12}")
    lines.append(
        f"  3-champion wipe: {fmt_time(ig['fight_wipe'])} vs {fmt_time(ir['fight_wipe'])}. "
        f"Tank falls at {fmt_time(ig['fight_tank_ttk'])} vs {fmt_time(ir['fight_tank_ttk'])}."
    )
    lines.append(
        f"  Heal in that fight: Guinsoo {ig['fight_heal']:.0f} | Runaan {ir['fight_heal']:.0f}. "
        f"Phantom procs on the solo tank: {ig['phantom']:.0f}."
    )

    # The minutes each path owns its legendary and not the other one.
    own_start = g_done
    ttk_g = ttk_r = d4_g = d4_r = fight_g = fight_r = drag_g = drag_r = 0.0
    wave_g = wave_r = 0.0
    n_own = 0
    for m in range(own_start, both):
        n_own += 1
        ttk_g += g_path[m - 1]["tank_ttk"] or 0
        ttk_r += r_path[m - 1]["tank_ttk"] or 0
        d4_g += g_path[m - 1]["tank4"]
        d4_r += r_path[m - 1]["tank4"]
        fight_g += g_path[m - 1]["fight3_dmg"]
        fight_r += r_path[m - 1]["fight3_dmg"]
        drag_g += g_path[m - 1]["dragon_dmg"]
        drag_r += r_path[m - 1]["dragon_dmg"]
        wave_g += g_path[m - 1]["wave_time"] or 0
        wave_r += r_path[m - 1]["wave_time"] or 0

    lines.append("")
    lines.append("-" * 78)
    lines.append(
        f"VERDICT — {own_start}:00 TO {both - 1}:00, EACH PATH OWNS ITS ITEM AND NOT THE OTHER"
    )
    lines.append("-" * 78)
    if n_own:
        lines.append(
            f"  Avg solo-tank ttk:   Guinsoo {ttk_g / n_own:.1f}s | Runaan {ttk_r / n_own:.1f}s "
            f"({rel_pct(ttk_r / n_own, ttk_g / n_own):+.0f}% time on the Runaan path)"
        )
        lines.append(
            f"  Avg tank dmg in 4s:  Guinsoo {d4_g / n_own:.0f} | Runaan {d4_r / n_own:.0f} "
            f"({rel_pct(d4_r / n_own, d4_g / n_own):+.0f}% if you bought Runaan)"
        )
        lines.append(
            f"  3-champion HP sum:   Guinsoo {fight_g:.0f} | Runaan {fight_r:.0f} "
            f"({rel_pct(fight_r, fight_g):+.0f}% if you bought Runaan)"
        )
        lines.append(
            f"  Avg dragon damage:   Guinsoo {drag_g / n_own:.0f} | Runaan {drag_r / n_own:.0f} "
            f"({rel_pct(drag_r / n_own, drag_g / n_own):+.0f}% if you bought Runaan)"
        )
        lines.append(
            f"  Avg wave-clear time: Guinsoo {wave_g / n_own:.1f}s | Runaan {wave_r / n_own:.1f}s "
            f"({rel_pct(wave_r / n_own, wave_g / n_own):+.0f}% time)"
        )
    lines.append("")
    lines.append("  WHAT EACH SECOND ITEM ACTUALLY CHANGES")
    lines.append("  • Guinsoo is the single-target item. After four attacks, Seething Strike is")
    lines.append("    +32% attack speed and every 3rd attack repeats W, BoRK, and the 30 magic")
    lines.append("    on-hit. W reads max HP, so the repeat still hurts a tank that is already low.")
    lines.append("    The 30 AP is a small W/Q bump, not the reason to buy it.")
    lines.append("  • Runaan does not add a second hit on the champion you clicked. It adds two")
    lines.append("    bolts. Each bolt is 55% AD, can crit, and applies W and BoRK at full value")
    lines.append("    to whoever is standing beside the target. On a solo frontliner the bolts")
    lines.append("    hit nothing. In a clump or a wave they are the item.")
    lines.append("  • The physical auto is close either way. Runaan's 25% crit at 200% damage")
    lines.append("    covers most of Guinsoo's extra 35 AD. The split is Phantom Hit vs splash.")
    lines.append("  • Solo-tank healing is almost the same. In the 3-champion fight Runaan")
    lines.append("    heals roughly two thirds more, because each bolt procs lifesteal and the")
    lines.append("    Greaves on-hit. That is extra time alive, not extra damage on the tank.")
    lines.append("  • A 3-auto trade never reaches Phantom Hit. Finished Guinsoo still wins that")
    lines.append("    trade on AD plus the 30 magic on-hit, by a small margin. The large tank")
    lines.append("    gap shows up across the full Barrage, not in one lane trade.")
    lines.append("  • Dragon caps W at 100 and caps BoRK at 100. Phantom Hit still raises")
    lines.append("    objective damage, just not as a percent-health melter. Waves do not care")
    lines.append("    about that cap: Runaan hits three minions per auto, Guinsoo hits one.")
    lines.append("  • Capped kill damage hides this. Once both builds kill the tank inside 8s,")
    lines.append("    total HP removed matches. Time-to-kill and the first 4 seconds do not.")
    lines.append("  • At 17:00 both items are owned and the paths deal the same damage. Runaan")
    lines.append("    second spends 2650 and comes online one wave earlier. Guinsoo second spends")
    lines.append("    3000 and is the tank/dragon item for the four minutes after that.")
    lines.append("")
    lines.append("  BUY")
    lines.append("  • Guinsoo's second when one champion is the win condition: the tank you")
    lines.append("    have to cut through, or the dragon you have to burn. You kill that target")
    lines.append("    faster inside the same Barrage. You do not wipe the people beside him,")
    lines.append("    and the wave takes most of W plus a little more.")
    lines.append("  • Runaan's second when they stand on top of each other or you need to shove")
    lines.append("    and move. The clumped fight actually ends. The wave dies inside one W.")
    lines.append("    The solo tank still dies during Barrage, about a second and a half later.")
    lines.append("  • Either way the other item is next. Order stops mattering the moment both")
    lines.append("    are finished. Crit on Runaan does not replace Phantom Hit on a lone tank.")
    lines.extend(rush_section())
    lines.extend(shiv_section(15))
    lines.append("")
    lines.append("ASSUMPTIONS")
    lines.append("  • 7.3: Guinsoo 3000g, 35 AD / 30 AP / 30% AS, 30 magic on-hit, +8% AS × 4,")
    lines.append("    Phantom Hit, crit no longer disabled. Runaan 2650g, 40% AS / 25% crit /")
    lines.append("    4% MS, two bolts at 55% AD. BoRK 3100g, 40 AD / 30% AS / 12% lifesteal,")
    lines.append("    7% current HP. Greaves 35% AS and 10 heal on-hit, 900g. Crit damage 200%.")
    lines.append("  • AS cap 3.0. Kog ratio 0.665, base 0.665, base bonus 0.2, +0.03/level")
    lines.append("    on the 7.3 curve. Q passive AS is always on. W is 8s, pressed at the start.")
    lines.append("  • Bolts apply on-hit at 100% and can crit. They do not spawn more bolts,")
    lines.append("    do not stack Guinsoo or Lethal Tempo, and do not carry Brutal.")
    lines.append("  • Phantom Hit repeats on-hit on the primary only, using HP after the first hit.")
    lines.append("  • Runes: Lethal Tempo, Brutal, Cut Down (6.5% vs targets above 60% HP),")
    lines.append("    Legend: Alacrity stacked by ~8:00. No Coup de Grace.")
    lines.append("  • You land Q on the focused champion (4s shred, 7s cooldown). Side targets")
    lines.append("    and minions are not shredded. No misses, no CC, expected crit, not a coin flip.")
    lines.append("  • Lifesteal applies to the auto, the bolts, and on-hit damage. Flat Greaves")
    lines.append("    heal procs on each on-hit application, including bolts and Phantom Hit.")
    lines.append("  • Zeal component is 15% AS / 15% crit. Recurve still has 15 physical on-hit")
    lines.append("    until the legendary consumes it. Wind Blade's old 15 flat damage is omitted;")
    lines.append("    the 7.3 item card does not list it.")
    lines.append("  • Statikk Shiv: 40 AD, 40 AP, 30% AS, 4% MS, 3000g. At level 13 the chain")
    lines.append("    hits 6 extra targets for 60 magic (90 vs minions and monsters), no crit.")
    lines.append("    Bounces apply on-hit once and do not repeat Phantom Hit.")
    lines.append("  • Energized cap is 100. Base gain is 6 per attack and 1 per 24 units")
    lines.append("    moved; Shiv adds 5 per attack. Kiting moves for 60% of the gap between")
    lines.append("    autos. Patch 7.3 does not republish that base gain.")
    lines.append("=" * 78)
    return "\n".join(lines)


def export_json(results: dict, path: Path) -> None:
    payload = {
        "meta": {
            "champion": "Kog'Maw",
            "role": "Dragon lane",
            "patch": "7.3",
            "game_minutes": GAME_MINUTES,
            "question": "BoRK > Berserker's, then Runaan's Hurricane vs Guinsoo's Rageblade",
            "w_window_seconds": W_WINDOW,
        },
        "builds": results,
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> None:
    results = run()
    self_check(results)
    report = summarize(results)
    print(report)
    out = Path(__file__).resolve().parent
    (out / "report.txt").write_text(report + "\n", encoding="utf-8")
    export_json(results, out / "results.json")
    print(f"\nWrote {out / 'report.txt'} and {out / 'results.json'}")


if __name__ == "__main__":
    main()
