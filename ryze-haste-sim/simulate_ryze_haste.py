#!/usr/bin/env python3
"""
Wild Rift Ryze — end-game damage vs ability haste.

Patch model: 7.3f (November 2026). Level 15, six items, Rod of Ages fully stacked.
Question: top ranked build vs a full ability-haste build, in a 1v1 and in a
teamfight, and which six items sit between raw damage and haste.

Kit (last patch notes + Wild Rift Fire 7.3f guide):
  Q 145 + 45% AP + 2% bonus mana, CD 5. Flux at R rank 3 doubles it.
  W 170 + 55% AP + 3% bonus mana, CD 7.   (7.2c nerf)
  E 170 + 40% AP + 2% bonus mana, CD 2.    (6.1b ratios; guide CD)
  Cast time 0.25s. W/E reset Q. E marks for 4s and spreads to the clump.
Wiki currently lists E as 170 + 55% AP + 3% mana on a 2.5s CD, the same
shape as the W nerf. That profile is re-run on the finalists as a check.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations
from pathlib import Path
import json
import math

OUT = Path(__file__).resolve().parent

# ---------------------------------------------------------------------------
# Champion / rune constants
# ---------------------------------------------------------------------------

LEVEL = 15
BASE_MANA = 340 + 60 * (LEVEL - 1)  # 1180, growth unchanged in 7.2c/7.3
MANAFLOW = 300
BASE_REGEN = (10 + 1 * (LEVEL - 1)) / 5  # 4.8 mana per second
RUNE_AH = 10 + 15  # Transcendence 5+5, Legend: Haste fully stacked
CAST = 0.25
FLUX_Q_MULT = 2.0  # Realm Warp rank 3: +100%
FLUX_DURATION = 4.0
PHASE_RUSH_AH = 10  # basic-ability haste, 3s
PHASE_RUSH_DURATION = 3.0
PHASE_RUSH_CD = 7.0  # level 15
PHASE_RUSH_REFUND = 0.20
TRANS_REFUND = 0.08
TRANS_CD = 8.0

Q_BASE, Q_AP, Q_MANA, Q_CD, Q_COST = 145.0, 0.45, 0.02, 5.0, 29.0
W_BASE, W_AP, W_MANA, W_CD, W_COST = 170.0, 0.55, 0.03, 7.0, 80.0
E_BASE, E_AP, E_MANA, E_CD, E_COST = 170.0, 0.40, 0.02, 2.0, 60.0

# League wiki E, used only as a sensitivity on the shortlist.
WIKI_E = dict(base=170.0, ap=0.55, mana=0.03, cd=2.5)


@dataclass(frozen=True)
class Item:
    name: str
    cost: int
    ap: float = 0
    ah: float = 0
    mana: float = 0
    hp: float = 0
    flat_pen: float = 0
    pct_pen: float = 0
    regen_pct: float = 0  # extra fraction of BASE regen
    awe: float = 0
    deathcap: float = 0
    refund: float = 0
    blackfire: bool = False
    liandry: bool = False
    rift: bool = False
    luden: bool = False
    orb: bool = False
    rocket: bool = False
    bloodletter: bool = False
    group: str = ""  # "pen" items are unique


ITEMS = {
    "Seraph's Embrace": Item(
        "Seraph's Embrace", 3000, ap=60, ah=25, mana=1200, awe=0.02, refund=0.25
    ),
    "Rod of Ages": Item(
        "Rod of Ages", 2600, ap=90, mana=800, hp=550, pct_pen=0.07
    ),  # 10 Veteran stacks (7.3f: +4 AP, +40 mana, +20 HP per stack)
    "Rabadon's Deathcap": Item("Rabadon's Deathcap", 3400, ap=130, deathcap=0.30),
    "Infinity Orb": Item("Infinity Orb", 3100, ap=110, flat_pen=15, orb=True),
    "Void Staff": Item("Void Staff", 3000, ap=95, pct_pen=0.40, group="pen"),
    "Cryptbloom": Item(
        "Cryptbloom", 3000, ap=75, ah=20, pct_pen=0.30, group="pen"
    ),
    "Bloodletter's Curse": Item(
        "Bloodletter's Curse",
        2900,
        ap=65,
        ah=15,
        hp=350,
        bloodletter=True,
        group="pen",
    ),
    "Cosmic Drive": Item("Cosmic Drive", 3000, ap=70, ah=25, hp=300),
    "Horizon Focus": Item("Horizon Focus", 2700, ap=80, ah=25),
    "Blackfire Torch": Item(
        "Blackfire Torch", 2800, ap=80, ah=20, mana=500, blackfire=True
    ),
    "Luden's Echo": Item("Luden's Echo", 2800, ap=100, ah=10, mana=500, luden=True),
    "Riftmaker": Item("Riftmaker", 3100, ap=80, ah=15, hp=350, rift=True),
    "Liandry's Torment": Item("Liandry's Torment", 3000, ap=60, hp=300, liandry=True),
    "Hextech Rocketbelt": Item(
        "Hextech Rocketbelt", 2650, ap=70, ah=20, hp=300, rocket=True
    ),
    "Morellonomicon": Item("Morellonomicon", 2550, ap=75, ah=15, hp=300),
    "Malignance": Item("Malignance", 2700, ap=90, ah=15, mana=500),
    "Spellslinger's Shoes": Item(
        "Spellslinger's Shoes",
        2200,
        ap=35,
        flat_pen=18,
        pct_pen=0.08,
        regen_pct=1.00,
        group="boots",
    ),
    "Crimson Lucidity": Item(
        "Crimson Lucidity", 2000, ah=25, regen_pct=0.75, group="boots"
    ),
    "Boots of Mana": Item(
        "Boots of Mana", 1200, ap=25, flat_pen=8, regen_pct=0.75, group="boots"
    ),
}

BOOTS = ["Spellslinger's Shoes", "Crimson Lucidity", "Boots of Mana"]
POOL = [n for n, it in ITEMS.items() if it.group != "boots"]


@dataclass(frozen=True)
class Target:
    name: str
    hp: float
    mr: float


SQUISHY = Target("squishy", 2300, 60)
BRUISER = Target("bruiser", 3400, 120)
TANK = Target("tank", 4500, 190)


@dataclass
class Stats:
    names: tuple
    ap: float
    max_mana: float
    bonus_mana: float
    item_ah: float
    ah: float
    flat_pen: float
    pen_factor: float
    regen: float
    refund: float
    cost: int
    q_raw: float
    q_flux: float
    w_raw: float
    e_raw: float
    bf_dps: float
    liandry: bool
    rift: bool
    luden: bool
    orb: bool
    rocket: bool
    bloodletter: bool
    blackfire: bool
    e_cd: float
    e_ap: float
    e_mana: float
    e_base: float


def compute_stats(
    names: list[str],
    n_burn: int,
    e_cd: float = E_CD,
    e_ap: float = E_AP,
    e_mana: float = E_MANA,
    e_base: float = E_BASE,
) -> Stats:
    items = [ITEMS[n] for n in names]
    ap_flat = sum(i.ap for i in items)
    bonus_hp = sum(i.hp for i in items)
    if any(i.rift for i in items):
        ap_flat += 0.02 * bonus_hp
    m_flat = BASE_MANA + MANAFLOW + sum(i.mana for i in items)
    deathcap = max((i.deathcap for i in items), default=0.0)
    awe = max((i.awe for i in items), default=0.0)
    bf = 1.0 + (0.04 * n_burn if any(i.blackfire for i in items) else 0.0)
    mult = (1.0 + deathcap) * bf
    denom = 1.0 - mult * awe * m_flat / 1000.0
    if denom <= 0.05:
        raise RuntimeError(f"mana/AP loop unstable for {names}")
    ap = mult * (ap_flat + awe * m_flat) / denom
    max_mana = m_flat * (1.0 + ap / 1000.0)
    bonus_mana = max_mana - BASE_MANA
    item_ah = sum(i.ah for i in items)
    pen_factor = 1.0
    for i in items:
        pen_factor *= 1.0 - i.pct_pen
    q_raw = Q_BASE + Q_AP * ap + Q_MANA * bonus_mana
    return Stats(
        names=tuple(names),
        ap=ap,
        max_mana=max_mana,
        bonus_mana=bonus_mana,
        item_ah=item_ah,
        ah=item_ah + RUNE_AH,
        flat_pen=sum(i.flat_pen for i in items),
        pen_factor=pen_factor,
        regen=BASE_REGEN * (1.0 + sum(i.regen_pct for i in items)),
        refund=max((i.refund for i in items), default=0.0),
        cost=sum(i.cost for i in items),
        q_raw=q_raw,
        q_flux=q_raw * FLUX_Q_MULT,
        w_raw=W_BASE + W_AP * ap + W_MANA * bonus_mana,
        e_raw=e_base + e_ap * ap + e_mana * bonus_mana,
        bf_dps=(20.0 + 0.02 * ap) if any(i.blackfire for i in items) else 0.0,
        liandry=any(i.liandry for i in items),
        rift=any(i.rift for i in items),
        luden=any(i.luden for i in items),
        orb=any(i.orb for i in items),
        rocket=any(i.rocket for i in items),
        bloodletter=any(i.bloodletter for i in items),
        blackfire=any(i.blackfire for i in items),
        e_cd=e_cd,
        e_ap=e_ap,
        e_mana=e_mana,
        e_base=e_base,
    )


def _mitigate(raw: float, mr: float, st: Stats, shred: float) -> float:
    resisted = mr * (1.0 - shred) * st.pen_factor - st.flat_pen
    if resisted < 0:
        resisted = 0.0
    return raw * 100.0 / (100.0 + resisted)


def _amp(st: Stats, combat: float) -> float:
    amp = 1.0
    if st.liandry:
        amp *= 1.0 + min(0.06, 0.02 * combat)
    if st.rift:
        amp *= 1.0 + min(0.08, 0.02 * math.floor(combat))
    return amp


def _luden_hits(st: Stats, n_enemies: int) -> tuple[float, float]:
    """Return (primary bonus, each secondary bonus) before mitigation."""
    secondary = min(4, max(0, n_enemies - 1))
    missing = 4 - secondary
    primary = (80.0 + 0.09 * st.ap) + missing * (22.2 + 0.014 * st.ap)
    splash = 80.0 + 0.09 * st.ap
    return primary, splash


@dataclass
class Fight:
    dealt: float = 0.0
    by_source: dict = field(default_factory=lambda: {"Q": 0.0, "W": 0.0, "E": 0.0, "burn": 0.0, "luden": 0.0, "rocket": 0.0})
    casts: dict = field(default_factory=lambda: {"Q": 0, "W": 0, "E": 0})
    ttk: float | None = None
    deaths: dict = field(default_factory=dict)
    per_target: dict = field(default_factory=dict)
    duration: float = 0.0
    dummy: bool = False


def simulate(
    st: Stats,
    targets: list[Target],
    duration: float,
    dummy: bool = False,
    stop_on_primary_death: bool = False,
) -> Fight:
    """Free-cast for `duration` seconds. Damage past 0 HP is not counted."""
    hp = [1e18 if dummy else t.hp for t in targets]
    hp_max = [t.hp for t in targets]
    flux = [-1.0] * len(targets)
    shred_stacks = [0] * len(targets)
    shred_at = [-1.0] * len(targets)
    burn_until = [-1.0] * len(targets)
    fight = Fight(dummy=dummy, per_target={t.name: 0.0 for t in targets})
    mana = st.max_mana
    t = 0.0
    lock = 0.0
    cd = {"Q": 0.0, "W": 0.0, "E": 0.0}
    opener = False
    combat_start = None
    pr_until = -1.0
    pr_ready = 0.0
    pr_hits: list[float] = []
    trans_ready = 0.0
    luden_ready = 0.0
    rocket_left = 1 if st.rocket else 0
    pending = None  # spell name whose hit lands at `lock`

    def basic_ah(now: float) -> float:
        return st.ah + (PHASE_RUSH_AH if now < pr_until else 0.0)

    def spell_cd(spell: str, now: float) -> float:
        base = {"Q": Q_CD, "W": W_CD, "E": st.e_cd}[spell]
        return base * 100.0 / (100.0 + basic_ah(now))

    def cost_of(spell: str) -> float:
        return {"Q": Q_COST, "W": W_COST, "E": E_COST}[spell] * (1.0 - st.refund)

    def living() -> list[int]:
        return [i for i, h in enumerate(hp) if h > 0]

    def primary() -> int | None:
        alive = living()
        return alive[0] if alive else None

    def choose(now: float) -> str | None:
        alive = living()
        if not alive:
            return None
        p = alive[0]
        has_flux = flux[p] >= now
        ready = {s: cd[s] <= now and mana >= cost_of(s) - 1e-6 for s in ("Q", "W", "E")}
        nonlocal opener
        if not opener and ready["Q"] and ready["E"]:
            opener = True
            return "Q"
        if ready["E"]:
            return "E"
        if ready["Q"] and has_flux:
            return "Q"
        e_wait = cd["E"] - now
        if ready["W"] and ready["Q"] and e_wait > 0.55:
            return "W"
        if ready["Q"] and e_wait > 0.30:
            return "Q"
        if ready["W"] and e_wait > 0.55:
            return "W"
        return None

    def mark_burn(idxs: list[int], now: float) -> None:
        if not (st.blackfire or st.liandry):
            return
        for i in idxs:
            burn_until[i] = now + 3.0

    def add_damage(i: int, amount: float, source: str, now: float) -> None:
        if amount <= 0 or hp[i] <= 0:
            return
        dealt = amount if dummy else min(hp[i], amount)
        hp[i] -= 0 if dummy else dealt
        fight.dealt += dealt
        fight.by_source[source] += dealt
        fight.per_target[targets[i].name] += dealt
        if not dummy and hp[i] <= 0 and targets[i].name not in fight.deaths:
            fight.deaths[targets[i].name] = now

    def on_ability_hit(spell: str, idxs: list[int], now: float) -> None:
        nonlocal combat_start, pr_until, pr_ready, trans_ready, luden_ready
        if combat_start is None:
            combat_start = now
        combat = now - combat_start
        amp = _amp(st, combat)
        mark_burn(idxs, now)
        for i in idxs:
            if st.bloodletter and now >= shred_at[i]:
                shred_stacks[i] = min(4, shred_stacks[i] + 1)
                shred_at[i] = now + 0.3
            shred = 0.075 * shred_stacks[i]
            if spell == "Q":
                raw = st.q_flux if flux[i] >= now else st.q_raw
            elif spell == "W":
                raw = st.w_raw
            else:
                raw = st.e_raw
            if st.orb and not dummy and hp[i] < 0.40 * hp_max[i]:
                raw *= 1.20
            add_damage(i, _mitigate(raw, targets[i].mr, st, shred) * amp, spell, now)
        if spell == "E":
            for i in idxs:
                flux[i] = now + FLUX_DURATION
        elif spell == "Q":
            for i in idxs:
                if flux[i] >= now:
                    flux[i] = -1.0
        elif spell == "W" and flux[idxs[0]] >= now:
            flux[idxs[0]] = -1.0

        # Phase Rush: 3 champion hits in 4s.
        pr_hits.append(now)
        pr_hits[:] = [h for h in pr_hits if now - h <= 4.0]
        if len(pr_hits) >= 3 and now >= pr_ready:
            for s in ("Q", "W", "E"):
                remain = cd[s] - now
                if remain > 0:
                    cd[s] = now + remain * (1.0 - PHASE_RUSH_REFUND)
            pr_until = now + PHASE_RUSH_DURATION
            pr_ready = now + PHASE_RUSH_CD
            pr_hits.clear()

        if now >= trans_ready:
            base = {"Q": Q_CD, "W": W_CD, "E": st.e_cd}[spell]
            refund = TRANS_REFUND * base * 100.0 / (100.0 + basic_ah(now))
            cd[spell] = max(now, cd[spell] - refund)
            trans_ready = now + TRANS_CD

        if st.luden and now >= luden_ready:
            primary_bonus, splash = _luden_hits(st, len(idxs))
            for n, i in enumerate(idxs):
                raw = primary_bonus if n == 0 else splash
                shred = 0.075 * shred_stacks[i]
                add_damage(i, _mitigate(raw, targets[i].mr, st, shred) * amp, "luden", now)
            luden_ready = now + 9.0

    def apply_burns(t0: float, t1: float) -> None:
        if t1 <= t0:
            return
        nonlocal mana
        mana = min(st.max_mana, mana + st.regen * (t1 - t0))
        if combat_start is None:
            return
        # Sample the midpoint so a 3s burn refreshes cleanly between casts.
        mid = (t0 + t1) / 2.0
        combat = max(0.0, mid - combat_start)
        amp = _amp(st, combat)
        for i, tgt in enumerate(targets):
            if burn_until[i] <= t0 or hp[i] <= 0:
                continue
            overlap = min(t1, burn_until[i]) - t0
            if overlap <= 0:
                continue
            shred = 0.075 * shred_stacks[i]
            raw = 0.0
            if st.liandry:
                raw += tgt.hp * 0.02 / 3.0
            if st.blackfire:
                raw += st.bf_dps
            add_damage(i, _mitigate(raw, tgt.mr, st, shred) * amp * overlap, "burn", t1)

    def fire_rocket(now: float) -> None:
        nonlocal rocket_left, combat_start
        if rocket_left <= 0:
            return
        rocket_left = 0
        if combat_start is None:
            combat_start = now
        amp = _amp(st, 0.0)
        alive = living()
        raw = 100.0 + 0.15 * st.ap
        for n, i in enumerate(alive):
            # One champion eats overlapping missiles. A clump splits them.
            shot = raw * (1.20 if len(alive) == 1 else 1.0)
            shred = 0.075 * shred_stacks[i]
            add_damage(i, _mitigate(shot, targets[i].mr, st, shred) * amp, "rocket", now)

    fire_rocket(0.0)

    while t < duration - 1e-9:
        if not living():
            break
        if stop_on_primary_death and hp[0] <= 0:
            break
        if pending is not None:
            apply_burns(t, lock)
            t = lock
            spell = pending
            pending = None
            if spell == "E":
                idxs = living()
            elif spell == "Q":
                alive = living()
                if any(flux[i] >= t for i in alive):
                    idxs = [i for i in alive if flux[i] >= t]
                else:
                    idxs = alive[:1]
            else:
                idxs = living()[:1]
            if idxs:
                on_ability_hit(spell, idxs, t)
            continue

        if t < lock:
            apply_burns(t, min(lock, duration))
            t = min(lock, duration)
            continue

        spell = choose(t)
        if spell is None:
            nxt = duration
            for s in ("Q", "W", "E"):
                if cd[s] > t:
                    nxt = min(nxt, cd[s])
            if nxt <= t:
                break
            apply_burns(t, min(nxt, duration))
            t = min(nxt, duration)
            continue

        mana -= cost_of(spell)
        fight.casts[spell] += 1
        cd[spell] = t + spell_cd(spell, t)
        if spell in ("E", "W"):
            cd["Q"] = t
        pending = spell
        lock = t + CAST

    if fight.ttk is None and not dummy and hp[0] <= 0:
        fight.ttk = fight.deaths.get(targets[0].name, t)
    fight.duration = t
    return fight


def ttk(st: Stats, target: Target, limit: float = 16.0) -> Fight:
    fight = simulate(st, [target], limit, dummy=False, stop_on_primary_death=True)
    return fight


def label(names: tuple | list[str]) -> str:
    boots = [n for n in names if ITEMS[n].group == "boots"]
    rest = [n for n in names if ITEMS[n].group != "boots"]
    order = {n: i for i, n in enumerate(POOL)}
    rest.sort(key=lambda n: order.get(n, 99))
    return " · ".join(boots + rest)


def short(names: tuple | list[str]) -> str:
    alias = {
        "Seraph's Embrace": "Seraph",
        "Rod of Ages": "RoA",
        "Rabadon's Deathcap": "Deathcap",
        "Infinity Orb": "Orb",
        "Void Staff": "Void",
        "Cryptbloom": "Crypt",
        "Bloodletter's Curse": "Bloodletter",
        "Cosmic Drive": "Cosmic",
        "Horizon Focus": "Horizon",
        "Blackfire Torch": "Blackfire",
        "Luden's Echo": "Luden",
        "Riftmaker": "Riftmaker",
        "Liandry's Torment": "Liandry",
        "Hextech Rocketbelt": "Rocketbelt",
        "Morellonomicon": "Morello",
        "Malignance": "Malignance",
        "Spellslinger's Shoes": "Spellslinger",
        "Crimson Lucidity": "Crimson",
        "Boots of Mana": "Mana boots",
    }
    return " + ".join(alias[n] for n in _ordered(names))


def _ordered(names) -> list[str]:
    boots = [n for n in names if ITEMS[n].group == "boots"]
    rest = [n for n in names if ITEMS[n].group != "boots"]
    order = {n: i for i, n in enumerate(POOL)}
    rest.sort(key=lambda n: order.get(n, 99))
    return boots + rest


NAMED = {
    "Top 1": [
        "Spellslinger's Shoes",
        "Seraph's Embrace",
        "Rod of Ages",
        "Rabadon's Deathcap",
        "Infinity Orb",
        "Void Staff",
    ],
    "Full AH": [
        "Crimson Lucidity",
        "Seraph's Embrace",
        "Cosmic Drive",
        "Horizon Focus",
        "Blackfire Torch",
        "Cryptbloom",
    ],
}


def legal(names: list[str]) -> bool:
    pens = [n for n in names if ITEMS[n].group == "pen"]
    return len(pens) <= 1


def grid() -> list[dict]:
    rows = []
    seen = set()
    for boots in BOOTS:
        for picked in combinations(POOL, 5):
            names = [boots, *picked]
            if not legal(names):
                continue
            key = tuple(sorted(names))
            if key in seen:
                continue
            seen.add(key)
            st1 = compute_stats(names, n_burn=1)
            st3 = compute_stats(names, n_burn=3 if st1.blackfire else 0)
            sq = ttk(st1, SQUISHY, 12.0)
            br = ttk(st1, BRUISER, 12.0)
            tk = ttk(st1, TANK, 14.0)
            tf = simulate(st3, [SQUISHY, BRUISER, TANK], 12.0)
            # Uncapped clump: how hard the build hits if shields/heals keep them up.
            dummy = simulate(st3, [SQUISHY, BRUISER, TANK], 4.0, dummy=True)
            deaths = tf.deaths
            if len(deaths) == 3:
                wipe = max(deaths.values())
            else:
                wipe = 99.0
            rows.append(
                {
                    "names": _ordered(names),
                    "key": short(names),
                    "cost": st1.cost,
                    "ap": round(st1.ap, 1),
                    "ap_clump": round(st3.ap, 1),
                    "mana": round(st1.max_mana),
                    "bonus_mana": round(st1.bonus_mana),
                    "item_ah": st1.item_ah,
                    "ah": st1.ah,
                    "e_cd": round(st1.e_cd * 100.0 / (100.0 + st1.ah), 3),
                    "ttk_squishy": sq.ttk if sq.ttk is not None else 99.0,
                    "ttk_bruiser": br.ttk if br.ttk is not None else 99.0,
                    "ttk_tank": tk.ttk if tk.ttk is not None else 99.0,
                    "wipe": wipe,
                    "dummy4": round(dummy.dealt),
                    "tf_deaths": {k: round(v, 2) for k, v in deaths.items()},
                    "casts_tf": tf.casts,
                }
            )
    return rows


def detail(names: list[str], e_override: dict | None = None) -> dict:
    kw = {}
    if e_override:
        kw = dict(
            e_cd=e_override["cd"],
            e_ap=e_override["ap"],
            e_mana=e_override["mana"],
            e_base=e_override["base"],
        )
    st1 = compute_stats(names, n_burn=1, **kw)
    st3 = compute_stats(names, n_burn=3 if st1.blackfire else 0, **kw)
    out = {
        "build": short(names),
        "items": _ordered(names),
        "cost": st1.cost,
        "ap": round(st1.ap, 1),
        "ap_clump": round(st3.ap, 1),
        "max_mana": round(st1.max_mana),
        "bonus_mana": round(st1.bonus_mana),
        "item_ah": st1.item_ah,
        "ah": st1.ah,
        "e_cd": round(st1.e_cd * 100 / (100 + st1.ah), 3),
        "w_cd": round(W_CD * 100 / (100 + st1.ah), 3),
        "q_flux": round(st1.q_flux),
        "e_raw": round(st1.e_raw),
        "w_raw": round(st1.w_raw),
    }
    scenarios = {}
    for name, st, tgts, dur, dummy, stop in (
        ("1v1 squishy TTK", st1, [SQUISHY], 16.0, False, True),
        ("1v1 bruiser TTK", st1, [BRUISER], 16.0, False, True),
        ("1v1 tank TTK", st1, [TANK], 16.0, False, True),
        ("1v1 squishy 4s dummy", st1, [SQUISHY], 4.0, True, False),
        ("1v1 bruiser 4s dummy", st1, [BRUISER], 4.0, True, False),
        ("1v1 tank 4s dummy", st1, [TANK], 4.0, True, False),
        ("teamfight 8s", st3, [SQUISHY, BRUISER, TANK], 12.0, False, False),
        ("teamfight 4s dummy", st3, [SQUISHY, BRUISER, TANK], 4.0, True, False),
        ("tank only 8s", st1, [TANK], 12.0, False, False),
    ):
        fight = simulate(st, tgts, dur, dummy=dummy, stop_on_primary_death=stop)
        scenarios[name] = {
            "damage": round(fight.dealt),
            "ttk": None if fight.ttk is None else round(fight.ttk, 2),
            "deaths": {k: round(v, 2) for k, v in fight.deaths.items()},
            "casts": fight.casts,
            "sources": {k: round(v) for k, v in fight.by_source.items()},
            "per_target": {k: round(v) for k, v in fight.per_target.items()},
            "time": round(fight.duration, 2),
        }
    out["scenarios"] = scenarios
    # One EQ at full HP, no amp, no orb.
    eq = {}
    for tgt in (SQUISHY, BRUISER, TANK):
        e = _mitigate(st1.e_raw, tgt.mr, st1, 0.0)
        q = _mitigate(st1.q_flux, tgt.mr, st1, 0.0)
        eq[tgt.name] = {"E": round(e), "Q": round(q), "EQ": round(e + q)}
    out["eq"] = eq
    return out


def _fmt_time(seconds: float) -> str:
    if seconds >= 90:
        return "no kill"
    return f"{seconds:.2f}s"


def choose(rows: list[dict]) -> dict:
    """Pick headline builds from the search.

    Real health bars die, so teamfight 'damage dealt' ties once a build
    wipes the clump. Rank the fight on wipe time and on uncapped 4s damage
    (the output if a shield or a heal keeps the targets standing).
    """
    best_dummy = max(rows, key=lambda r: (r["dummy4"], -r["wipe"], -r["ttk_tank"]))
    fastest_wipe = min(rows, key=lambda r: (r["wipe"], -r["dummy4"], r["ttk_tank"]))
    fastest_sq = min(rows, key=lambda r: (r["ttk_squishy"], r["ttk_bruiser"], r["ttk_tank"]))
    fastest_br = min(rows, key=lambda r: (r["ttk_bruiser"], r["ttk_tank"], r["ttk_squishy"]))
    fastest_tk = min(rows, key=lambda r: (r["ttk_tank"], r["ttk_bruiser"]))
    max_ah = max(rows, key=lambda r: (r["item_ah"], r["dummy4"]))
    dummy_cap = best_dummy["dummy4"] or 1
    ah_cap = max(r["item_ah"] for r in rows) or 1
    # Still one-combo the squishy (cast floor is 0.75s) and stay close to the
    # best bruiser/tank kill, then take as much haste as that allows.
    burst = [
        r for r in rows
        if r["ttk_squishy"] <= fastest_sq["ttk_squishy"] + 0.05
        and r["ttk_bruiser"] <= fastest_br["ttk_bruiser"] * 1.35
        and r["ttk_tank"] <= fastest_tk["ttk_tank"] * 1.25
        and r["dummy4"] >= 0.90 * dummy_cap
    ]
    balance = max(burst or rows, key=lambda r: (r["item_ah"], r["dummy4"], -r["ttk_bruiser"]))
    knee = max(
        rows,
        key=lambda r: math.sqrt((r["dummy4"] / dummy_cap) * (r["item_ah"] / ah_cap)),
    )
    return {
        "best_dummy": best_dummy,
        "fastest_wipe": fastest_wipe,
        "fastest_sq": fastest_sq,
        "fastest_br": fastest_br,
        "fastest_tk": fastest_tk,
        "max_ah": max_ah,
        "balance": balance,
        "knee": knee,
        "dummy_cap": dummy_cap,
    }


def render(rows: list[dict], details: dict, wiki_details: dict) -> str:
    picks = choose(rows)

    def find_named(title: str) -> dict:
        want = set(NAMED[title])
        for r in rows:
            if set(r["names"]) == want:
                return r
        raise KeyError(title)

    top1 = find_named("Top 1")
    full = find_named("Full AH")

    lines = []
    w = lines.append
    w("=" * 78)
    w("RYZE — TOP BUILD vs FULL ABILITY HASTE (Wild Rift 7.3f)")
    w("Level 15 · 6 items · RoA fully stacked · Phase Rush page")
    w("=" * 78)
    w("")
    w("TARGETS (end-game estimates, not a specific match)")
    w("  Squishy   2300 HP   60 MR    mid/ADC with no MR item")
    w("  Bruiser   3400 HP  120 MR    one MR item")
    w("  Tank      4500 HP  190 MR    two MR items")
    w("  Teamfight is those three standing in one Spell Flux. W hits the squishy.")
    w("  Q and empowered Q hit every marked champion. A kill stops that target's")
    w("  damage, so an 8s total ties once the team is dead. The 4s dummy number")
    w("  is the same fight with infinite HP: shields, heals, and extra targets.")
    w("")
    w("VERDICT")
    w("  Take the damage build in a 1v1 and in a teamfight. Full haste casts")
    w("  more often, but each Flux Overload is about half as large, and a 4s")
    w("  fight only fits one or two extra spells before cast time gets in the way.")
    w(f"  Top 1 kills the squishy in {_fmt_time(top1['ttk_squishy'])}, the bruiser in "
      f"{_fmt_time(top1['ttk_bruiser'])}, the tank in {_fmt_time(top1['ttk_tank'])}.")
    w(f"  Full AH takes {_fmt_time(full['ttk_squishy'])}, {_fmt_time(full['ttk_bruiser'])}, "
      f"and {_fmt_time(full['ttk_tank'])}.")
    w(f"  Over 4s on a clump that does not die: Top 1 {top1['dummy4']}, Full AH {full['dummy4']} "
      f"({100 * full['dummy4'] / top1['dummy4']:.0f}%).")
    w("  The balance point is not 140 ability haste. Swapping Rod of Ages for")
    w("  Blackfire Torch (Seraph, Deathcap, Infinity Orb, Void, Spellslinger)")
    w(f"  is {picks['best_dummy']['item_ah']:.0f} item AH and the highest damage in the search:")
    w(f"  4s clump {picks['best_dummy']['dummy4']}, team dead at {_fmt_time(picks['best_dummy']['wipe'])}.")
    w("  Past that, more haste means selling Deathcap, Void, or Orb, and the")
    w("  kill times get worse. Rod of Ages stays correct if you need its 550 HP;")
    w("  in that case drop Infinity Orb, not Void Staff or Deathcap.")
    w("")
    w("SHARED RUNES (every build)")
    w("  Phase Rush, Manaflow (300 mana), Transcendence (+10 AH, 8% refund / 8s),")
    w("  Legend: Haste (15 AH). Nimbus is move speed only, not in the damage.")
    w("  Phase Rush: after 3 hits, basic cooldowns cut 20% and +10 AH for 3s.")
    w("")
    w("-" * 78)
    w("HEADLINE BUILDS")
    w("-" * 78)

    def block(title: str) -> None:
        d = details[title]
        sq = d["scenarios"]["1v1 squishy TTK"]
        br = d["scenarios"]["1v1 bruiser TTK"]
        tk = d["scenarios"]["1v1 tank TTK"]
        clump = d["scenarios"]["teamfight 8s"]
        dummy = d["scenarios"]["teamfight 4s dummy"]
        one = d["scenarios"]["1v1 squishy 4s dummy"]
        deaths = clump["deaths"]
        wipe = max(deaths.values()) if len(deaths) == 3 else None
        w(f"{title}")
        w(f"  {d['build']}")
        ap_line = f"{d['ap']:.0f} AP"
        if abs(d["ap_clump"] - d["ap"]) >= 5:
            ap_line += f" ({d['ap_clump']:.0f} AP while three champions are burning)"
        w(
            f"  {ap_line} · {d['max_mana']} mana · {d['bonus_mana']} bonus mana · "
            f"{d['item_ah']:.0f} item AH ({d['ah']:.0f} with runes) · E {d['e_cd']:.2f}s · W {d['w_cd']:.2f}s"
        )
        w(
            "  One EQ, full HP, magic resist applied: "
            + " · ".join(f"{k} {v['EQ']}" for k, v in d["eq"].items())
        )
        w(
            f"  1v1 kill: squishy {_fmt_time(sq['ttk'])} · bruiser {_fmt_time(br['ttk'])} · "
            f"tank {_fmt_time(tk['ttk'])}"
        )
        w(
            f"  4s into one target that does not die: squishy {one['damage']} · "
            f"bruiser {d['scenarios']['1v1 bruiser 4s dummy']['damage']} · "
            f"tank {d['scenarios']['1v1 tank 4s dummy']['damage']}"
        )
        if wipe is None:
            w("  Team wipe: still standing at 12s")
        else:
            w(
                "  Team wipe: "
                + " · ".join(f"{name} {_fmt_time(deaths[name])}" for name in ("squishy", "bruiser", "tank"))
                + f" · last death {_fmt_time(wipe)}"
            )
        w(
            f"  4s clump, infinite HP: {dummy['damage']} total "
            f"(squishy {dummy['per_target']['squishy']}, bruiser {dummy['per_target']['bruiser']}, "
            f"tank {dummy['per_target']['tank']})"
        )
        src = dummy["sources"]
        w(
            f"  Those 4s come from Q {src['Q']} · W {src['W']} · E {src['E']} · "
            f"burn {src['burn']} · Luden {src['luden']} · belt {src['rocket']}"
            f" · casts Q{dummy['casts']['Q']} W{dummy['casts']['W']} E{dummy['casts']['E']}"
        )
        w("")

    seen = set()
    for title in details:
        build = details[title]["build"]
        if build in seen:
            w(f"{title} — same items as a build already listed ({build})")
            w("")
            continue
        seen.add(build)
        block(title)

    w("-" * 78)
    w("SEARCH (every legal 6-item mix of the mage pool)")
    w("-" * 78)
    w(f"  Builds searched: {len(rows)}")
    w(f"  Fastest squishy: {picks['fastest_sq']['key']}")
    w(f"    {_fmt_time(picks['fastest_sq']['ttk_squishy'])} · bruiser {_fmt_time(picks['fastest_sq']['ttk_bruiser'])} · {picks['fastest_sq']['item_ah']:.0f} item AH")
    w(f"  Fastest bruiser: {picks['fastest_br']['key']}")
    w(f"    {_fmt_time(picks['fastest_br']['ttk_bruiser'])} · tank {_fmt_time(picks['fastest_br']['ttk_tank'])} · {picks['fastest_br']['item_ah']:.0f} item AH")
    w(f"  Fastest tank: {picks['fastest_tk']['key']}")
    w(f"    {_fmt_time(picks['fastest_tk']['ttk_tank'])} · {picks['fastest_tk']['item_ah']:.0f} item AH · 4s clump {picks['fastest_tk']['dummy4']}")
    w(f"  Fastest team wipe: {picks['fastest_wipe']['key']}")
    w(f"    last death {_fmt_time(picks['fastest_wipe']['wipe'])} · {picks['fastest_wipe']['item_ah']:.0f} item AH")
    w(f"  Highest 4s clump damage: {picks['best_dummy']['key']}")
    w(f"    {picks['best_dummy']['dummy4']} · wipe {_fmt_time(picks['best_dummy']['wipe'])} · {picks['best_dummy']['item_ah']:.0f} item AH")
    w(f"  Highest item AH: {picks['max_ah']['key']}")
    w(f"    {picks['max_ah']['item_ah']:.0f} AH · 4s clump {picks['max_ah']['dummy4']} · squishy {_fmt_time(picks['max_ah']['ttk_squishy'])}")
    bal = picks["balance"]
    w("  Balance: most item AH that still one-combos the squishy, stays within")
    w("  35% of the best bruiser kill and 25% of the best tank kill, and keeps")
    w("  at least 90% of the best 4s clump damage.")
    w(f"    {bal['key']}")
    w(f"    {bal['item_ah']:.0f} item AH · 4s clump {bal['dummy4']} ({100*bal['dummy4']/picks['dummy_cap']:.1f}% of best) · squishy {_fmt_time(bal['ttk_squishy'])} · bruiser {_fmt_time(bal['ttk_bruiser'])} · tank {_fmt_time(bal['ttk_tank'])}")
    knee = picks["knee"]
    w("  Knee (geometric mean of 4s clump damage and item AH):")
    w(f"    {knee['key']}")
    w(f"    {knee['dummy4']} · {knee['item_ah']:.0f} item AH · squishy {_fmt_time(knee['ttk_squishy'])} · tank {_fmt_time(knee['ttk_tank'])}")
    w("")
    w("Highest 4s clump damage:")
    for r in sorted(rows, key=lambda r: (-r["dummy4"], r["wipe"]))[:8]:
        w(
            f"  {r['dummy4']:5d}  wipe {_fmt_time(r['wipe']):>8}  AH {r['item_ah']:5.0f}  "
            f"sq {_fmt_time(r['ttk_squishy']):>8}  tank {_fmt_time(r['ttk_tank']):>8}  {r['key']}"
        )
    w("")
    w("-" * 78)
    w("NAMED COMPARISON")
    w("-" * 78)
    def pct(a, b):
        return 100.0 * a / b if b else 0
    w(f"  4s clump: Top 1 {top1['dummy4']} vs Full AH {full['dummy4']} "
      f"({pct(full['dummy4'], top1['dummy4']):.1f}% of Top 1)")
    w(f"  Squishy kill {_fmt_time(top1['ttk_squishy'])} vs {_fmt_time(full['ttk_squishy'])}")
    w(f"  Bruiser kill {_fmt_time(top1['ttk_bruiser'])} vs {_fmt_time(full['ttk_bruiser'])}")
    w(f"  Tank kill {_fmt_time(top1['ttk_tank'])} vs {_fmt_time(full['ttk_tank'])}")
    w(f"  Team wipe {_fmt_time(top1['wipe'])} vs {_fmt_time(full['wipe'])}")
    w(f"  Item AH {top1['item_ah']:.0f} vs {full['item_ah']:.0f}")
    w("")
    w("-" * 78)
    w("WIKI E CHECK (170 + 55% AP + 3% mana, 2.5s CD) on the same builds")
    w("Primary results above use the 7.3f guide E (170 + 40% AP + 2% mana, 2s).")
    w("-" * 78)
    for title, d in wiki_details.items():
        sq = d["scenarios"]["1v1 squishy TTK"]
        br = d["scenarios"]["1v1 bruiser TTK"]
        tk = d["scenarios"]["1v1 tank TTK"]
        dummy = d["scenarios"]["teamfight 4s dummy"]
        w(f"  {title}: squishy {_fmt_time(sq['ttk'])} · bruiser {_fmt_time(br['ttk'])} · "
          f"tank {_fmt_time(tk['ttk'])} · 4s clump {dummy['damage']} · E {d['e_cd']:.2f}s")
    w("")
    w("-" * 78)
    w("ASSUMPTIONS")
    w("-" * 78)
    w("  Arcane Mastery: max mana = (base + items + Manaflow) × (1 + AP/1000).")
    w("  Seraph Awe is 2% max mana as AP (current wiki), refunds 25% mana, no magic pen.")
    w("  Deathcap is +30% AP and multiplies Awe, Riftmaker HP-to-AP, and Blackfire's")
    w("  4% AP per burning champion. Blackfire burn is 20 + 2% AP per second.")
    w("  Liandry burn is 2% max HP over 3 seconds (about 0.67% HP per second) plus")
    w("  Madness, +2% damage per second up to +6%. Riftmaker is +2% per second up to +8%,")
    w("  and +2% bonus HP as AP.")
    w("  Infinity Orb is +20% ability damage when the target is already under 40% HP.")
    w("  Luden echo every 9s. Rocketbelt once: 100 + 15% AP, 1.2× on a lone target.")
    w("  Bloodletter shreds 7.5% MR per hit, up to 30%. It cannot be paired with Void")
    w("  or Cryptbloom. Percent pen from RoA, Void, and Spellslinger multiplies.")
    w("  Malignance Hatefog is not counted: Realm Warp deals no damage.")
    w("  Crimson/Ionian Summoned lowers summoner spells, not Q/W/E.")
    w("  Horizon's 10% amp needs a cast from 600 range. EQ is inside 550, so it is")
    w("  not applied. The item is still in the pool as 80 AP and 25 AH.")
    w("  You are free-casting. Stuns, Zhonya, and missed Qs are not modeled.")
    w("  Move speed from Cosmic, Phase Rush, and Spell Flux is not damage, but it is")
    w("  why a haste build gets to spend the full 8 seconds in range.")
    w("  Cast time caps an EQ loop at 0.50s. None of these builds reach that cap.")
    w("")
    return "\n".join(lines)


def main() -> None:
    print("Searching builds...", flush=True)
    rows = grid()
    print(f"  {len(rows)} legal builds", flush=True)

    chosen = choose(rows)
    picks = {
        "Top 1": NAMED["Top 1"],
        "Full AH": NAMED["Full AH"],
        "Fastest 1v1": chosen["fastest_br"]["names"],
        "Fastest team wipe": chosen["fastest_wipe"]["names"],
        "Highest 4s clump": chosen["best_dummy"]["names"],
        "Balance": chosen["balance"]["names"],
        "Knee": chosen["knee"]["names"],
    }
    # De-duplicate while keeping the first title for identical item sets.
    details = {}
    seen_detail = {}
    for title, names in picks.items():
        key = tuple(sorted(names))
        if key in seen_detail:
            details[title] = details[seen_detail[key]]
            continue
        details[title] = detail(names)
        seen_detail[key] = title

    wiki_details = {}
    for title in ("Top 1", "Full AH", "Balance", "Fastest team wipe"):
        wiki_details[title] = detail(picks[title], e_override=WIKI_E)

    report = render(rows, details, wiki_details)
    # render() looks up NAMED rows itself and then every details title.
    # Balance titles are not in NAMED, and render's block() handles that.
    (OUT / "report.txt").write_text(report)
    payload = {
        "patch": "7.3f",
        "level": 15,
        "targets": {
            "squishy": {"hp": SQUISHY.hp, "mr": SQUISHY.mr},
            "bruiser": {"hp": BRUISER.hp, "mr": BRUISER.mr},
            "tank": {"hp": TANK.hp, "mr": TANK.mr},
        },
        "picks": {title: details[title]["build"] for title in picks},
        "details": details,
        "wiki_e_check": {
            title: {
                "build": wiki_details[title]["build"],
                "ap": wiki_details[title]["ap"],
                "e_cd": wiki_details[title]["e_cd"],
                "ttk_squishy": wiki_details[title]["scenarios"]["1v1 squishy TTK"]["ttk"],
                "ttk_bruiser": wiki_details[title]["scenarios"]["1v1 bruiser TTK"]["ttk"],
                "tank_ttk": wiki_details[title]["scenarios"]["1v1 tank TTK"]["ttk"],
                "clump_4s": wiki_details[title]["scenarios"]["teamfight 4s dummy"]["damage"],
            }
            for title in wiki_details
        },
        "top_clump": [
            {
                k: r[k]
                for k in (
                    "key", "dummy4", "wipe", "item_ah", "ah", "ap",
                    "ttk_squishy", "ttk_bruiser", "ttk_tank", "cost",
                )
            }
            for r in sorted(rows, key=lambda r: (-r["dummy4"], r["wipe"]))[:15]
        ],
        "builds_searched": len(rows),
    }
    (OUT / "results.json").write_text(json.dumps(payload, indent=2))
    print(report)


if __name__ == "__main__":
    main()
