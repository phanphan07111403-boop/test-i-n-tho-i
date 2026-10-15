#!/usr/bin/env python3
"""
Wild Rift 7.3b support component order for Brand and Zyra.

Same five legendary items as the Liandry-third build, plus Ionian boots:

  1. Black Mist Scythe
  2. Liandry's Torment
  3. Diadem of Songs (Whispering Circlet transforms)
  4. Echoes of Helia
  5. Harmonic Echo
  and Ionian Boots of Lucidity

Goal: spend gold on pieces instead of saving for a finished legendary, and
make Helia turn damage into healing as soon as possible. Helia spends its
shards only when Diadem heals an ally, so the clock that matters is the
first minute both are owned.

The search walks support gold minute by minute. It tries every order of the
item chains and keeps the path that converts earliest, then heals the most.
"""

from __future__ import annotations

import itertools
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))

from compare_brand_zyra import (  # noqa: E402
    body,
    brand_utility,
    lane_heal_per_min,
    zyra_utility,
)
from simulate_brand_support import (  # noqa: E402
    FIGHT_S,
    ITEMS,
    evaluate,
    gold_at_minute,
    helia_cap,
    helia_stored,
    level_at_minute,
    scythe_stacks,
    stats_from_names,
)

# Live 7.3b alpha sheets. The shared item table still has the older Guise
# AP, Kindlegem HP, and Idol line. Patch only this process.
ITEMS["Haunting Guise"].ap = 30
ITEMS["Kindlegem"].hp = 175
ITEMS["Forbidden Idol"].hp = 100
ITEMS["Forbidden Idol"].ah = 5

CLOCK = 26
FULL_GOLD = 11800  # sickle + 4 crafted legendaries + Ionian


def charge_rate(ah: float) -> float:
    """Lane casts per minute on Circlet, scaled by haste, cap 2 per 10s."""
    return min(12.0, 8.0 * (100.0 + ah) / 110.0)


@dataclass(frozen=True)
class Step:
    id: str
    item: str
    cost: int
    consumes: Tuple[str, ...]
    legendary: str


def S(sid: str, item: str, cost: int, legendary: str, consumes: Tuple[str, ...] = ()) -> Step:
    return Step(sid, item, cost, consumes, legendary)


STEPS: Dict[str, Step] = {
    s.id: s
    for s in [
        S("tear", "Tear of the Goddess", 400, "Diadem of Songs"),
        S("ruby_c", "Ruby Crystal", 500, "Diadem of Songs"),
        S("idol", "Forbidden Idol", 700, "Diadem of Songs"),
        S("circlet", "Whispering Circlet", 800, "Diadem of Songs", ("idol", "tear", "ruby_c")),
        S("ruby_kh", "Ruby Crystal", 500, "Echoes of Helia"),
        S("kg_h", "Kindlegem", 500, "Echoes of Helia", ("ruby_kh",)),
        S("tome_bh", "Amplifying Tome", 500, "Echoes of Helia"),
        S("ring_bh", "Ring of Revelation", 300, "Echoes of Helia"),
        S("bg_h", "Bandleglass Mirror", 100, "Echoes of Helia", ("tome_bh", "ring_bh")),
        S("helia", "Echoes of Helia", 500, "Echoes of Helia", ("bg_h", "kg_h")),
        S("ring_i", "Ring of Revelation", 300, "Ionian Boots of Lucidity"),
        S("boots", "Boots of Speed", 400, "Ionian Boots of Lucidity"),
        S("ionian", "Ionian Boots of Lucidity", 300, "Ionian Boots of Lucidity", ("boots", "ring_i")),
        S("tome_a", "Amplifying Tome", 500, "Liandry's Torment"),
        S("ashes", "Fated Ashes", 400, "Liandry's Torment", ("tome_a",)),
        S("tome_g", "Amplifying Tome", 500, "Liandry's Torment"),
        S("ruby_g", "Ruby Crystal", 500, "Liandry's Torment"),
        S("guise", "Haunting Guise", 300, "Liandry's Torment", ("tome_g", "ruby_g")),
        S("liandry", "Liandry's Torment", 800, "Liandry's Torment", ("ashes", "guise")),
        S("tome_br", "Amplifying Tome", 500, "Harmonic Echo"),
        S("ring_br", "Ring of Revelation", 300, "Harmonic Echo"),
        S("bg_r", "Bandleglass Mirror", 100, "Harmonic Echo", ("tome_br", "ring_br")),
        S("ruby_kr", "Ruby Crystal", 500, "Harmonic Echo"),
        S("kg_r", "Kindlegem", 500, "Harmonic Echo", ("ruby_kr",)),
        S("harmonic", "Harmonic Echo", 600, "Harmonic Echo", ("bg_r", "kg_r")),
    ]
}

CIRCLET_ORDERS: Tuple[Tuple[str, ...], ...] = (
    ("ruby_c", "tear", "idol", "circlet"),
    ("tear", "ruby_c", "idol", "circlet"),
    ("ruby_c", "idol", "tear", "circlet"),
    ("tear", "idol", "ruby_c", "circlet"),
    ("idol", "ruby_c", "tear", "circlet"),
    ("idol", "tear", "ruby_c", "circlet"),
)

OTHER_BLOCKS: Tuple[Tuple[str, Tuple[str, ...]], ...] = (
    ("KH", ("ruby_kh", "kg_h")),
    ("BH", ("tome_bh", "ring_bh", "bg_h")),
    ("H", ("helia",)),
    ("A", ("tome_a", "ashes")),
    ("G", ("tome_g", "ruby_g", "guise", "liandry")),
    ("I", ("ring_i", "boots", "ionian")),
    ("R", ("tome_br", "ring_br", "ruby_kr", "kg_r", "bg_r", "harmonic")),
)

# Previous legendary order: Ionian, then Liandry, then Circlet, Helia, Harmonic.
# No spending ahead into a later legendary.
BASELINE_BLOCKS: Tuple[Tuple[str, ...], ...] = (
    ("boots", "ring_i", "ionian"),
    ("tome_a", "ashes", "tome_g", "ruby_g", "guise", "liandry"),
    ("idol", "tear", "ruby_c", "circlet"),
    ("tome_bh", "ring_bh", "bg_h", "ruby_kh", "kg_h", "helia"),
    ("tome_br", "ring_br", "bg_r", "ruby_kr", "kg_r", "harmonic"),
)

PIECE_OF = {
    "Spectral Sickle": "Black Mist Scythe",
    "Black Mist Scythe": "Black Mist Scythe",
    "Diadem of Songs": "Diadem of Songs",
}


@dataclass
class Event:
    minute: int
    kind: str
    name: str
    cost: int
    gold: int
    left: int
    legendary: str
    names: List[str]
    charges: float


@dataclass
class Walk:
    label: str
    priority: Tuple[str, ...]
    events: List[Event]
    snaps: Dict[int, dict]
    circlet: Optional[int] = None
    diadem: Optional[int] = None
    helia: Optional[int] = None
    transfer: Optional[int] = None
    ashes: Optional[int] = None
    liandry: Optional[int] = None
    harmonic: Optional[int] = None
    ionian: Optional[int] = None
    legendary: Optional[int] = None
    idle: int = 0
    ap_sum: float = 0.0
    charges_at: Dict[int, float] = field(default_factory=dict)


def ability_haste(names: Sequence[str]) -> float:
    return sum(ITEMS[n].ah for n in names)


def bundle_cost(step: Step, owned: set) -> int:
    """Gold still required to finish the legendary that consumes this mirror.

    A Ruby already combined into Kindlegem is no longer in `owned`. Count it
    only when Kindlegem itself is still unbuilt.
    """
    if step.id == "bg_h":
        need = step.cost + STEPS["helia"].cost
        if "kg_h" not in owned:
            need += STEPS["kg_h"].cost
            if "ruby_kh" not in owned:
                need += STEPS["ruby_kh"].cost
        return need
    if step.id == "bg_r":
        need = step.cost + STEPS["harmonic"].cost
        if "kg_r" not in owned:
            need += STEPS["kg_r"].cost
            if "ruby_kr" not in owned:
                need += STEPS["ruby_kr"].cost
        return need
    return step.cost


def should_defer(step: Step, pool: int, names: Sequence[str], owned: set) -> bool:
    """Hold Bandleglass until its legendary can be finished in this same buy.

    Combining it deletes the Tome's 20 AP and gives 10 AH. During the charge
    window that haste is worth buying early only while total AH is still under
    20. After that, the Tome stays until Helia or Harmonic is paid.
    """
    if step.id not in ("bg_h", "bg_r"):
        return False
    if ability_haste(names) < 20:
        return False
    return pool < bundle_cost(step, owned)


def afford_minute(pool: int, cost: int, minute: int) -> int:
    if pool >= cost:
        return minute
    spent = gold_at_minute(minute) - pool
    for t in range(minute + 1, 36):
        if gold_at_minute(t) - spent >= cost:
            return t
    return 99


def delays(pool: int, target_cost: int, fill_cost: int, minute: int) -> bool:
    return afford_minute(pool - fill_cost, target_cost, minute) > afford_minute(pool, target_cost, minute)


def _flags(names: Sequence[str]) -> dict:
    owned = set(names)
    return {
        "circlet": "Whispering Circlet" in owned,
        "diadem": "Diadem of Songs" in owned,
        "helia": "Echoes of Helia" in owned,
        "ashes": "Fated Ashes" in owned and "Liandry's Torment" not in owned,
        "liandry": "Liandry's Torment" in owned,
        "harmonic": "Harmonic Echo" in owned,
        "ionian": "Ionian Boots of Lucidity" in owned,
        "scythe": "Black Mist Scythe" in owned,
    }


def walk_priority(
    priority: Sequence[str],
    label: str,
    strict_blocks: Optional[Sequence[Sequence[str]]] = None,
) -> Walk:
    """Buy along `priority`. Leftover gold buys the next piece that fits
    without pushing the current payment to a later minute.

    `strict_blocks` reproduces the old legendary order: do not start the
    next legendary's pieces until the current block is finished.
    """
    names: List[str] = ["Spectral Sickle"]
    spent = 500
    owned = set()
    done = set()
    charges = 0.0
    circlet_at: Optional[int] = None
    events: List[Event] = [
        Event(0, "buy", "Spectral Sickle", 500, 500, 0, "Black Mist Scythe", list(names), 0.0)
    ]
    snaps: Dict[int, dict] = {}
    walk = Walk(label=label, priority=tuple(priority), events=events, snaps=snaps)

    def purchase(step: Step, minute: int, pool: int) -> int:
        nonlocal spent
        if step.cost > pool:
            raise RuntimeError(f"cannot afford {step.item}")
        for cid in step.consumes:
            if cid not in owned:
                raise RuntimeError(f"{step.item} missing {cid}")
            owned.remove(cid)
            done.add(cid)
            names.remove(STEPS[cid].item)
        pool -= step.cost
        spent += step.cost
        owned.add(step.id)
        names.append(step.item)
        events.append(
            Event(
                minute, "buy", step.item, step.cost, gold_at_minute(minute), pool,
                step.legendary, list(names), charges,
            )
        )
        return pool

    def ready_steps(allowed: Optional[set]) -> List[Step]:
        out = []
        for sid in priority:
            if allowed is not None and sid not in allowed:
                continue
            if sid in owned or sid in done:
                continue
            step = STEPS[sid]
            if all(c in owned for c in step.consumes):
                out.append(step)
        return out

    for minute in range(0, CLOCK + 1):
        pool = gold_at_minute(minute) - spent
        if strict_blocks is None:
            allowed = None
        else:
            allowed = set()
            for block in strict_blocks:
                allowed.update(block)
                if any(sid not in owned and sid not in done for sid in block):
                    break

        while True:
            options = ready_steps(allowed)
            if not options:
                break
            target = None
            target_cost = None
            for step in options:
                if should_defer(step, pool, names, owned):
                    target = step
                    target_cost = bundle_cost(step, owned)
                    break
                target = step
                target_cost = step.cost
                break
            if target is None or target_cost is None:
                break
            if not should_defer(target, pool, names, owned) and target.cost <= pool:
                pool = purchase(target, minute, pool)
                continue
            filled = False
            for step in options:
                if step.id == target.id or should_defer(step, pool, names, owned):
                    continue
                if step.cost > pool:
                    continue
                if delays(pool, target_cost, step.cost, minute):
                    continue
                pool = purchase(step, minute, pool)
                filled = True
                break
            if not filled:
                break

        if minute >= 5 and "Spectral Sickle" in names:
            names.remove("Spectral Sickle")
            names.append("Black Mist Scythe")
            events.append(
                Event(
                    minute, "upgrade", "Black Mist Scythe", 0, gold_at_minute(minute), pool,
                    "Black Mist Scythe", list(names), charges,
                )
            )

        flags = _flags(names)
        if flags["circlet"] and circlet_at is None:
            circlet_at = minute
            walk.circlet = minute
        if circlet_at is not None and minute > circlet_at and walk.diadem is None:
            charges += charge_rate(ability_haste(names))
            if charges >= 50:
                names.remove("Whispering Circlet")
                names.append("Diadem of Songs")
                flags = _flags(names)
                events.append(
                    Event(
                        minute, "transform", "Diadem of Songs", 0, gold_at_minute(minute), pool,
                        "Diadem of Songs", list(names), charges,
                    )
                )

        flags = _flags(names)
        if walk.diadem is None and flags["diadem"]:
            walk.diadem = minute
        if walk.helia is None and flags["helia"]:
            walk.helia = minute
        if walk.transfer is None and flags["diadem"] and flags["helia"]:
            walk.transfer = minute
        if walk.ashes is None and ("Fated Ashes" in names or flags["liandry"]):
            # Ashes minute is the first minute the burn component exists,
            # including the minute it is immediately combined into Liandry.
            if any(ev.minute == minute and ev.name == "Fated Ashes" for ev in events) or flags["liandry"]:
                if any(ev.name == "Fated Ashes" and ev.minute == minute for ev in events):
                    walk.ashes = minute
                elif flags["liandry"] and walk.ashes is None:
                    walk.ashes = minute
        if walk.ashes is None and any(ev.name == "Fated Ashes" for ev in events):
            walk.ashes = next(ev.minute for ev in events if ev.name == "Fated Ashes")
        if walk.liandry is None and flags["liandry"]:
            walk.liandry = minute
        if walk.harmonic is None and flags["harmonic"]:
            walk.harmonic = minute
        if walk.ionian is None and flags["ionian"]:
            walk.ionian = minute
        if walk.legendary is None and all(
            (flags["scythe"], flags["liandry"], flags["diadem"], flags["helia"], flags["harmonic"])
        ):
            walk.legendary = minute

        ap = sum(ITEMS[n].ap for n in names)
        if flags["scythe"]:
            ap += 4 * scythe_stacks(minute)
        walk.ap_sum += ap
        walk.idle += pool
        walk.charges_at[minute] = charges
        snaps[minute] = {
            "names": list(names),
            "charges": charges if (flags["circlet"] or flags["diadem"]) else 0.0,
            "pool": pool,
            "spent": spent,
        }
    return walk


def cheap_score(w: Walk) -> tuple:
    return (
        w.transfer if w.transfer is not None else 99,
        w.liandry if w.liandry is not None else 99,
        w.ashes if w.ashes is not None else 99,
        w.harmonic if w.harmonic is not None else 99,
        w.legendary if w.legendary is not None else 99,
        -int(w.ap_sum),
        w.idle,
        w.ionian if w.ionian is not None else 99,
    )


def search() -> Tuple[Walk, int]:
    best: Optional[tuple] = None
    checked = 0
    for circlet in CIRCLET_ORDERS:
        for perm in itertools.permutations(OTHER_BLOCKS):
            checked += 1
            order: List[str] = list(circlet)
            for _name, block in perm:
                order.extend(block)
            w = walk_priority(order, "candidate")
            score = cheap_score(w)
            key = (score, order)
            if best is None or key < best:
                best = key
    assert best is not None
    _score, order = best
    return walk_priority(tuple(order), "gold-efficient"), checked


def stats_at_snap(champ: str, snap: dict, minute: int):
    return stats_from_names(
        champ,
        snap["names"],
        level_at_minute(minute),
        minute,
        snap["charges"],
        gold_at_minute(minute),
        scythe_stacks(minute),
    )


def fight_row(champ: str, snap: dict, minute: int) -> dict:
    st = stats_at_snap(champ, snap, minute)
    fight = evaluate(st)
    util = (brand_utility if champ == "Brand" else zyra_utility)(st.level)
    tank = body(champ, st.level, st.hp)
    hsp = st.hsp
    diadem_heal = 0.0
    helia_heal = 0.0
    if st.diadem:
        diadem_heal = 0.008 * st.mana * FIGHT_S * 0.92 * hsp
    if st.helia and st.diadem:
        helia_heal = helia_stored(fight.pre, st.level, FIGHT_S, True, 0) * hsp
    if st.harmonic:
        diadem_heal *= 1.30
        helia_heal *= 1.30
    return {
        "champ": champ,
        "minute": minute,
        "level": st.level,
        "gold": gold_at_minute(minute),
        "left": snap["pool"],
        "items": list(snap["names"]),
        "ap": round(st.ap, 1),
        "ah": st.ah,
        "hp": round(st.hp),
        "mana": round(st.mana),
        "hsp": round((st.hsp - 1) * 100, 1),
        "charges": round(snap["charges"], 1),
        "diadem": st.diadem,
        "helia": st.helia,
        "liandry": st.liandry,
        "harmonic": st.harmonic,
        "ashes": st.ashes,
        "damage": round(fight.post_front + fight.post_carry),
        "front": round(fight.post_front),
        "carry": round(fight.post_carry),
        "pre": round(fight.pre),
        "heal": round(fight.heal),
        "diadem_heal": round(diadem_heal),
        "helia_heal": round(helia_heal),
        "lane_heal": round(lane_heal_per_min(st)),
        "hard_cc": round(util["hard_cc"], 2),
        "uncleanseable": round(util["uncleanseable"], 2),
        "body_hp": round(tank["hp"]),
        "ehp_phys": round(tank["ehp_phys"]),
        "ehp_magic": round(tank["ehp_magic"]),
    }


def deep_totals(w: Walk) -> dict:
    out = {"lane": 0, "heal": 0, "damage": 0, "rows": []}
    for minute in range(1, CLOCK + 1):
        for champ in ("Brand", "Zyra"):
            row = fight_row(champ, w.snaps[minute], minute)
            out["rows"].append(row)
            out["lane"] += row["lane_heal"]
            out["heal"] += row["heal"]
            out["damage"] += row["damage"]
    return out


def refine(seed: Walk, pool: int = 40) -> Walk:
    """Re-rank the cheapest paths that match the best conversion minute.

    The mass search ranks by when Liandry and Ashes finish. This pass adds
    real lane healing and fight healing for the paths tied on that clock.
    """
    target = cheap_score(seed)
    found: List[Walk] = [seed]
    signatures = {tuple((e.minute, e.kind, e.name) for e in seed.events)}
    kept = 0
    for circlet in CIRCLET_ORDERS:
        for perm in itertools.permutations(OTHER_BLOCKS):
            order: List[str] = list(circlet)
            for _name, block in perm:
                order.extend(block)
            w = walk_priority(order, "candidate")
            score = cheap_score(w)
            if score > target:
                continue
            if score < target:
                # Search should already have returned the minimum. Keep it.
                target = score
                found = [w]
                signatures = {tuple((e.minute, e.kind, e.name) for e in w.events)}
                kept = 0
                continue
            sig = tuple((e.minute, e.kind, e.name) for e in w.events)
            if sig in signatures:
                continue
            signatures.add(sig)
            found.append(w)
            kept += 1
            if kept >= pool:
                break
        if kept >= pool:
            break

    def deep_key(w: Walk) -> tuple:
        totals = deep_totals(w)
        w.label = "scored"
        return (
            w.transfer if w.transfer is not None else 99,
            -totals["lane"],
            -totals["heal"],
            -totals["damage"],
            w.legendary if w.legendary is not None else 99,
            w.idle,
        )

    ranked = sorted(found, key=deep_key)
    winner = ranked[0]
    winner.label = "gold-efficient"
    return winner


def shop_level(minute: int) -> int:
    if minute <= 0:
        return 1
    return level_at_minute(minute)


def piece_delta(
    champ: str,
    before_names: List[str],
    after_names: List[str],
    minute: int,
    before_charges: float,
    after_charges: float,
) -> Tuple[str, str]:
    b_charges = before_charges
    if "Whispering Circlet" in before_names and b_charges >= 50:
        b_charges = 49
    b = stats_from_names(
        champ, before_names, shop_level(minute), minute, b_charges, 0, scythe_stacks(minute)
    )
    a = stats_from_names(
        champ, after_names, shop_level(minute), minute, after_charges, 0, scythe_stacks(minute)
    )
    parts = []
    if round(a.ap - b.ap):
        parts.append(f"{a.ap - b.ap:+.0f} AP")
    if round(a.ah - b.ah):
        parts.append(f"{a.ah - b.ah:+.0f} AH")
    if round(a.hp - b.hp):
        parts.append(f"{a.hp - b.hp:+.0f} HP")
    if round(a.mana - b.mana):
        parts.append(f"{a.mana - b.mana:+.0f} mana")
    hsp = (a.hsp - b.hsp) * 100
    if abs(hsp) >= 0.05:
        parts.append(f"{hsp:+.1f}% HSP")
    text = ", ".join(parts) if parts else "no combat-stat change"
    return text, ""


def running_line(champ: str, event: Event) -> str:
    charges = event.charges
    names = event.names
    # Diadem swap already applied on transform events. Circlet mana uses charges.
    st = stats_from_names(
        champ, names, shop_level(event.minute), event.minute,
        charges, gold_at_minute(event.minute), scythe_stacks(event.minute),
    )
    hsp = (st.hsp - 1) * 100
    return (
        f"AP {st.ap:.0f}  AH {st.ah:.0f}  HP {st.hp:.0f}  "
        f"mana {st.mana:.0f}  HSP {hsp:.1f}%"
    )


def describe_event(event: Event, prev_names: List[str], prev_charges: float) -> str:
    # Buys are diffed at one charge total so a Circlet tick is not credited
    # to the piece. The transform is the line that shows the bank crossing 50.
    before_c = prev_charges if event.kind == "transform" else event.charges
    text, _extra = piece_delta(
        "Brand", prev_names, event.names, event.minute, before_c, event.charges
    )
    notes = {
        "Spectral Sickle": "support quest starts",
        "Black Mist Scythe": "free upgrade; +4 AP and +25 HP each minute from 6:00, cap 10",
        "Tear of the Goddess": "+200 mana, sits until Circlet",
        "Ruby Crystal": "+200 HP, sits until its recipe consumes it",
        "Forbidden Idol": "+100 HP, +5 AH, +6% HSP, until Circlet consumes it",
        "Whispering Circlet": "Harmony starts; the buy minute adds 0 charges",
        "Diadem of Songs": "50 charges reached; heals 0.8% max mana per second and spends Helia",
        "Kindlegem": "+175 HP and +10 AH after the Ruby is consumed",
        "Amplifying Tome": "+20 AP until a recipe consumes it",
        "Ring of Revelation": "recipe piece, no combat stats",
        "Bandleglass Mirror": "consumes the Tome, so its 20 AP leaves and +10 AH arrives",
        "Echoes of Helia": "stores 30% of pre-mitigation damage; Diadem is what spends it",
        "Boots of Speed": "movement, no combat stats",
        "Ionian Boots of Lucidity": "+15 AH and summoner haste",
        "Fated Ashes": "+40 AP and Kindle, about 5 magic damage per second",
        "Haunting Guise": "item is +30 AP and +200 HP; the Ruby's 200 HP is consumed, so the net is the delta",
        "Liandry's Torment": "burn becomes 2% max HP per second, plus 7% magic pen",
        "Harmonic Echo": "does not create a heal; multiplies Diadem and Helia healing by 1.30",
    }
    note = notes.get(event.name, "")
    if event.name == "Kindlegem" and event.legendary == "Echoes of Helia":
        note = "+175 HP and +10 AH. This is the haste that lets the charge clock finish on time"
    elif event.name == "Kindlegem":
        note = "+175 HP and +10 AH. Diadem is already up, so this haste does not move the heal"
    if text and note:
        return f"{text}. {note}"
    return note or text


def fmt_minute(m: Optional[int]) -> str:
    if m is None:
        return "—"
    return f"{m}:00"


def clock_lines(w: Walk) -> List[str]:
    lines = []
    end = max(w.legendary or 0, w.ionian or 0, w.transfer or 0)
    for minute in range(0, end + 1):
        snap = w.snaps[minute]
        flags = _flags(snap["names"])
        tags = []
        if flags["scythe"]:
            tags.append("Scythe")
        if flags["circlet"]:
            tags.append(f"Circlet {snap['charges']:.0f}/50")
        if flags["diadem"]:
            tags.append("DIADEM")
        if flags["helia"]:
            tags.append("Helia")
        if flags["ashes"]:
            tags.append("Ashes")
        if flags["liandry"]:
            tags.append("Liandry")
        if flags["harmonic"]:
            tags.append("Harmonic")
        if flags["ionian"]:
            tags.append("Ionian")
        held = ", ".join(snap["names"])
        lines.append(
            f"  {minute:>2}:00  gold {gold_at_minute(minute):>5}  "
            f"left {snap['pool']:>4}  {' · '.join(tags) or 'Sickle':<42}  {held}"
        )
    return lines


def purchase_lines(w: Walk) -> List[str]:
    lines = []
    prev: List[str] = []
    prev_charges = 0.0
    for event in w.events:
        delta = describe_event(event, prev, prev_charges)
        if event.name == "Bandleglass Mirror":
            later = [
                ev for ev in w.events
                if ev.minute == event.minute and ev.name in ("Echoes of Helia", "Harmonic Echo")
                and w.events.index(ev) > w.events.index(event)
            ]
            if later:
                if not delta.endswith("."):
                    delta += "."
                delta += " The legendary is bought this same minute, so the lost 20 AP is replaced at once."
        kind = {"buy": "buy", "upgrade": "upgrade", "transform": "transform"}[event.kind]
        lines.append(
            f"  {event.minute:>2}:00  {event.cost:>4}g  left {event.left:>4}  "
            f"{kind:<9} {event.name:<28} [{event.legendary}]"
        )
        lines.append(f"         piece  {delta}")
        lines.append(f"         now    {running_line('Brand', event)}")
        prev = list(event.names)
        prev_charges = event.charges
    return lines


def comparison_table(new: Walk, old: Walk) -> List[str]:
    lines = []
    minutes = []
    for m in range(8, 24):
        if m in (8, 10, 12, 13, 14, 16, 18, 20, 21, 23) or m in (
            new.transfer, old.transfer, new.liandry, old.liandry, new.legendary, old.legendary
        ):
            if m not in minutes and m <= CLOCK:
                minutes.append(m)
    lines.append(
        f"  {'Min':>5} {'Build':<8} {'Dmg':>6} {'Heal':>6} {'Lane/m':>7} "
        f"{'AP':>5} {'AH':>4} {'HSP':>6}  State"
    )
    for minute in minutes:
        for label, w in (("New", new), ("Old", old)):
            row = fight_row("Zyra", w.snaps[minute], minute)
            state = []
            if row["diadem"]:
                state.append("Diadem")
            elif "Whispering Circlet" in row["items"]:
                state.append("charging")
            if row["helia"]:
                state.append("Helia")
            if row["liandry"]:
                state.append("Liandry")
            elif row["ashes"]:
                state.append("Ashes")
            if row["harmonic"]:
                state.append("Harmonic")
            lines.append(
                f"  {minute:>4}:00 {label:<8} {row['damage']:>6} {row['heal']:>6} "
                f"{row['lane_heal']:>7} {row['ap']:>5.0f} {row['ah']:>4.0f} "
                f"{row['hsp']:>5.1f}%  {', '.join(state) or 'no converter'}"
            )
        lines.append("")
    return lines


def champ_table(w: Walk, minutes: Sequence[int]) -> List[str]:
    lines = []
    lines.append(
        f"  {'Min':>5} {'Champ':<6} {'Dmg':>6} {'Front':>6} {'Carry':>6} "
        f"{'Heal':>6} {'of Helia':>8} {'Lane/m':>7} {'CC':>5} {'AP':>5}"
    )
    for minute in minutes:
        pair = []
        for champ in ("Brand", "Zyra"):
            row = fight_row(champ, w.snaps[minute], minute)
            pair.append(row)
            lines.append(
                f"  {minute:>4}:00 {champ:<6} {row['damage']:>6} {row['front']:>6} "
                f"{row['carry']:>6} {row['heal']:>6} {row['helia_heal']:>8} "
                f"{row['lane_heal']:>7} {row['hard_cc']:>5.2f} {row['ap']:>5.0f}"
            )
        b, z = pair
        if b["damage"]:
            lines.append(
                f"         Zyra damage {100 * z['damage'] / b['damage'] - 100:+.0f}% vs Brand. "
                f"Fight heal {z['heal'] - b['heal']:+d}. Lane heal {z['lane_heal'] - b['lane_heal']:+d}/min."
            )
        lines.append("")
    return lines


def cumulative(w: Walk, champ: str, start: int, end: int) -> dict:
    lane = heal = dmg = 0
    for minute in range(start, end + 1):
        row = fight_row(champ, w.snaps[minute], minute)
        lane += row["lane_heal"]
        heal += row["heal"]
        dmg += row["damage"]
    return {"lane": lane, "heal": heal, "damage": dmg}


def run() -> Tuple[str, dict]:
    print("Searching component orders...", flush=True)
    seed, checked = search()
    print(f"Checked {checked} orders. Best cheap transfer {seed.transfer}:00. Scoring heals...", flush=True)
    winner = refine(seed)
    baseline = walk_priority(
        [sid for block in BASELINE_BLOCKS for sid in block],
        "liandry-third",
        strict_blocks=BASELINE_BLOCKS,
    )
    new_tot = deep_totals(winner)
    old_tot = deep_totals(baseline)

    lines: List[str] = []
    A = lines.append
    A("=" * 78)
    A("COMPONENT ORDER — GOLD EFFICIENCY AND DAMAGE-TO-HEAL (Wild Rift 7.3b)")
    A("Black Mist Scythe, Liandry, Diadem, Helia, Harmonic, plus Ionian boots.")
    A("Every component is listed. Legendaries are only the combine or the transform.")
    A("8-second fight, ultimate up, one frontline + one carry. No runes.")
    A("=" * 78)
    A("")
    A("WHAT WAS OPTIMIZED")
    A("  Spend gold on the next affordable piece. Do not sit on gold to finish")
    A("  a legendary in one buy. Helia stores 30% of pre-mitigation damage and")
    A("  spends all of it only when something heals an ally. Brand and Zyra have")
    A("  no heal, so that something is Diadem. The conversion minute is the first")
    A("  minute both Diadem and Helia are owned.")
    A("  Circlet charges 8 procs a minute at 10 AH, up to the 12/min cap:")
    A("  rate = min(12, 8 × (100 + AH) / 110). The buy minute adds 0 charges.")
    A("  50 charges transform Circlet into Diadem. Harmony is +0.25% of max mana")
    A("  as heal/shield power.")
    A("")
    A(f"  Orders checked: {checked}.")
    A(f"  Conversion, this order: {fmt_minute(winner.transfer)} "
      f"(Circlet {fmt_minute(winner.circlet)}, Helia {fmt_minute(winner.helia)}, "
      f"Diadem {fmt_minute(winner.diadem)}).")
    A(f"  Conversion, Liandry third: {fmt_minute(baseline.transfer)} "
      f"(Circlet {fmt_minute(baseline.circlet)}, Helia {fmt_minute(baseline.helia)}, "
      f"Diadem {fmt_minute(baseline.diadem)}).")
    A(f"  All 5 legendaries: this order {fmt_minute(winner.legendary)}, "
      f"Liandry third {fmt_minute(baseline.legendary)}.")
    new_idle = sum(winner.snaps[m]["pool"] for m in range(0, 24))
    old_idle = sum(baseline.snaps[m]["pool"] for m in range(0, 24))
    A(f"  Gold left in pocket at the end of each minute, 0:00 through 23:00: "
      f"this order {new_idle}, Liandry third {old_idle}.")
    A("")
    A("FIVE LEGENDARIES, IN THE ORDER THEY TURN ON")
    for title, minute in (
        ("Black Mist Scythe", next(ev.minute for ev in winner.events if ev.name == "Black Mist Scythe")),
        ("Echoes of Helia", winner.helia),
        ("Diadem of Songs", winner.diadem),
        ("Liandry's Torment", winner.liandry),
        ("Harmonic Echo", winner.harmonic),
    ):
        A(f"  {fmt_minute(minute):>5}  {title}")
    A(f"  {fmt_minute(winner.ionian):>5}  Ionian Boots of Lucidity (epic boots, not a legendary)")
    A("")
    A("-" * 78)
    A("PIECE BY PIECE")
    A("Cost is the gold paid at that buy (components already owned are not paid again).")
    A("Running totals are Brand's. Zyra's AP and AH match; her base mana is within a few points.")
    A("-" * 78)
    A("")
    lines.extend(purchase_lines(winner))
    A("")
    A("-" * 78)
    A("INVENTORY EACH MINUTE")
    A("-" * 78)
    lines.extend(clock_lines(winner))
    A("")
    A("-" * 78)
    A("WHY THE DAMAGE BECOMES A HEAL HERE")
    A("-" * 78)
    tmin = winner.transfer or 0
    zrow = fight_row("Zyra", winner.snaps[tmin], tmin)
    brow = fight_row("Brand", winner.snaps[tmin], tmin)
    if winner.helia == tmin and winner.diadem == tmin:
        A(f"  At {tmin}:00 Helia is bought and Circlet becomes Diadem on the same minute.")
    elif winner.helia is not None and winner.helia < tmin:
        A(f"  Helia is finished at {winner.helia}:00. Diadem arrives at {tmin}:00.")
        A("  Until Diadem exists, Helia is in the inventory and the heal is still 0.")
    else:
        A(f"  At {tmin}:00 both Helia and Diadem are on.")
    A(f"  Charges that minute: {winner.charges_at[tmin]:.1f} (need 50).")
    A(f"  Zyra 8s fight: {zrow['damage']} damage, {zrow['heal']} heal.")
    A(f"    Diadem's own heal {zrow['diadem_heal']}. Helia turning damage into heal {zrow['helia_heal']}.")
    A(f"  Brand 8s fight: {brow['damage']} damage, {brow['heal']} heal "
      f"(Helia portion {brow['helia_heal']}).")
    A("  Helia stores 30% of pre-mitigation damage and spends it only when Diadem")
    A("  heals an ally. The heal before that minute is 0 even if Helia is owned.")
    A("")
    A(f"  Circlet is finished at {winner.circlet}:00. Minute {(winner.circlet or 1) - 1} has "
      f"{gold_at_minute((winner.circlet or 1) - 1)} gold, short of Sickle plus Circlet (2900).")
    A("  The buy minute adds 0 charges. Six minutes at 10 AH are 48 charges, short of 50,")
    A("  so the clock needs haste above the Scythe's 10 before it can land on 13:00.")
    kg_min = next(
        ev.minute for ev in winner.events
        if ev.name == "Kindlegem" and ev.legendary == "Echoes of Helia"
    )
    A(f"  No checked order converts before {winner.transfer}:00. This one buys Helia's")
    A(f"  Kindlegem at {kg_min}:00, the first minute its 1000 gold is up after Ashes.")
    A(f"  Fated Ashes is finished at {winner.ashes}:00 with the gold in front of that")
    A("  Kindlegem. Moving Ashes later does not finish Liandry sooner: Sickle + Circlet")
    A(f"  + Helia + Liandry is 8300 gold, and 16:00 has {gold_at_minute(16)}. "
      f"Liandry is {fmt_minute(winner.liandry)}.")
    A(f"  Harmonic Echo is {fmt_minute(winner.harmonic)}. It multiplies a heal, so it is last")
    A("  among the legendaries. Its mirror is combined on the Harmonic minute, so the")
    A("  Tome's 20 AP stays until that buy replaces it.")
    A(f"  Ionian boots finish at {fmt_minute(winner.ionian)}. Those pieces are bought only")
    A("  when they do not push Helia, Liandry, or Harmonic to a later minute.")
    A("")
    A("-" * 78)
    A("AGAINST LIANDRY THIRD (same pieces, old legendary order, same spending rules)")
    A("Zyra row. Damage is lower before Liandry on the new order. Healing starts")
    A("at the conversion minute instead of when Liandry-third reaches Diadem.")
    A("The earlier published sheet used a flat 8 charges per minute and first healed")
    A("at 22:00. This table uses the haste-scaled charge rate on both orders.")
    A("-" * 78)
    A("")
    lines.extend(comparison_table(winner, baseline))
    nz = cumulative(winner, "Zyra", 1, 23)
    nb = cumulative(winner, "Brand", 1, 23)
    oz = cumulative(baseline, "Zyra", 1, 23)
    ob = cumulative(baseline, "Brand", 1, 23)
    A(f"  Sum of Zyra lane heal/min from 1:00 to 23:00: new {nz['lane']}, old {oz['lane']}.")
    A(f"  Sum of Brand lane heal/min from 1:00 to 23:00: new {nb['lane']}, old {ob['lane']}.")
    A(f"  Sum of Zyra 8s-fight heal at each minute 1–23: new {nz['heal']}, old {oz['heal']}.")
    A(f"  Sum of Zyra fight damage at each minute 1–23: new {nz['damage']}, old {oz['damage']}.")
    A(f"  Sum of Brand fight damage at each minute 1–23: new {nb['damage']}, old {ob['damage']}.")
    A("  The new order heals earlier and leaves less gold in pocket. It deals less")
    A("  damage from 8:00 to 16:00, because Liandry is the 17:00 item instead of the")
    A(f"  {fmt_minute(baseline.liandry)} item. At 23:00 both orders hold the same items.")
    A("")
    A("-" * 78)
    A("BRAND vs ZYRA ON THIS ORDER")
    A("-" * 78)
    A("")
    show = []
    for m in (8, 12, winner.transfer or 13, winner.liandry or 18, 20, winner.legendary or 23):
        if m not in show:
            show.append(m)
    lines.extend(champ_table(winner, show))
    late_m = winner.legendary or 22
    b20 = fight_row("Brand", winner.snaps[late_m], late_m)
    z20 = fight_row("Zyra", winner.snaps[late_m], late_m)
    A(f"  At {late_m}:00, with all 5 legendaries, hard CC is Zyra {z20['hard_cc']:.2f}s "
      f"vs Brand {b20['hard_cc']:.2f}s.")
    A(f"  Zyra's knockup is {z20['uncleanseable']:.2f}s and Mikael's cannot cleanse it.")
    A(f"  Bodies that minute: Brand {b20['body_hp']} HP, Zyra {z20['body_hp']} HP.")
    A(f"  Carry damage at {late_m}:00 is Brand {b20['carry']}, Zyra {z20['carry']}.")
    A(f"  Frontline damage is Zyra {z20['front']}, Brand {b20['front']}.")
    A("  Zyra still does more frontline damage, more lane healing once Diadem is")
    A("  up (plants keep Liandry ticking), and more crowd control. Brand's edge is")
    A("  the point-click stun. The item order does not close that kit gap. It moves")
    A("  the minute both of them start turning damage into healing.")
    A("")
    A("ITEM LINES USED FOR THIS SEARCH")
    A("  Kindlegem 1000g: Ruby + 500, +175 HP, +10 AH.")
    A("  Haunting Guise 1300g: Tome + Ruby + 300, +30 AP, +200 HP.")
    A("  Forbidden Idol 700g: +100 HP, +5 AH, +6% HSP, no sub-recipe.")
    A("  Fated Ashes 900g: Tome + 400, +40 AP, Kindle (~5 damage per second).")
    A("  Earlier sims in this folder used Guise 35 AP and Kindlegem 200 HP.")
    A("  Those files were not rewritten. Only this order uses the 7.3b alpha lines.")
    A("=" * 78)

    payload = {
        "meta": {
            "patch": "7.3b",
            "orders_checked": checked,
            "conversion_minute": winner.transfer,
            "baseline_conversion_minute": baseline.transfer,
            "legendary_minute": winner.legendary,
            "baseline_legendary_minute": baseline.legendary,
            "idle_gold_through_23": new_idle,
            "baseline_idle_gold_through_23": old_idle,
            "circlet_minute": winner.circlet,
            "diadem_minute": winner.diadem,
            "helia_minute": winner.helia,
            "liandry_minute": winner.liandry,
            "harmonic_minute": winner.harmonic,
            "ionian_minute": winner.ionian,
            "charge_formula": "min(12, 8 * (100 + AH) / 110), 0 on the Circlet buy minute",
            "full_gold": FULL_GOLD,
        },
        "purchases": [
            {
                "minute": ev.minute,
                "kind": ev.kind,
                "name": ev.name,
                "cost": ev.cost,
                "gold": ev.gold,
                "left": ev.left,
                "legendary": ev.legendary,
                "inventory": ev.names,
                "charges": round(ev.charges, 2),
            }
            for ev in winner.events
        ],
        "priority": list(winner.priority),
        "new_rows": new_tot["rows"],
        "old_rows": old_tot["rows"],
        "totals": {
            "new_zyra": nz,
            "new_brand": nb,
            "old_zyra": oz,
            "old_brand": ob,
        },
    }
    return "\n".join(lines), payload, winner, baseline


def _assert(winner: Walk, baseline: Walk, payload: dict) -> None:
    assert charge_rate(10) == 8
    assert 6 * charge_rate(10) < 50
    assert 7 * charge_rate(10) >= 50
    assert gold_at_minute(7) == 3160
    assert gold_at_minute(13) == 6220
    assert gold_at_minute(23) == 11820
    spent = sum(ev.cost for ev in winner.events)
    assert spent == FULL_GOLD, spent
    assert winner.circlet == 7
    assert winner.transfer == 13
    assert winner.liandry is not None and winner.liandry <= 17
    assert winner.transfer < baseline.transfer
    assert winner.legendary is not None and winner.legendary <= 23
    assert baseline.transfer is not None and baseline.transfer >= 20
    assert sum(ev.cost for ev in baseline.events) == FULL_GOLD
    # The Tome inside Bandleglass is still in the inventory on the minute
    # before each legendary that consumes it.
    for done_at, legendary in ((winner.helia, "Echoes of Helia"), (winner.harmonic, "Harmonic Echo")):
        assert done_at is not None and done_at > 0
        assert "Bandleglass Mirror" not in winner.snaps[done_at - 1]["names"]
        assert legendary in winner.snaps[done_at]["names"]
    assert winner.helia is not None and winner.diadem is not None
    # Buying Circlet must not add a charge on that minute.
    assert winner.charges_at[winner.circlet] == 0
    names_bought = [ev.name for ev in winner.events if ev.kind == "buy"]
    for item, count in (
        ("Ruby Crystal", 4),
        ("Amplifying Tome", 4),
        ("Ring of Revelation", 3),
        ("Tear of the Goddess", 1),
        ("Forbidden Idol", 1),
        ("Whispering Circlet", 1),
        ("Echoes of Helia", 1),
        ("Harmonic Echo", 1),
        ("Liandry's Torment", 1),
        ("Fated Ashes", 1),
        ("Haunting Guise", 1),
        ("Ionian Boots of Lucidity", 1),
        ("Kindlegem", 2),
        ("Bandleglass Mirror", 2),
    ):
        assert names_bought.count(item) == count, (item, names_bought.count(item))
    # No negative gold and no buy above the pool that minute.
    spent_run = 0
    for ev in winner.events:
        spent_run += ev.cost
        assert ev.left == gold_at_minute(ev.minute) - spent_run
        assert ev.left >= 0
    z_new = payload["totals"]["new_zyra"]["lane"]
    z_old = payload["totals"]["old_zyra"]["lane"]
    assert z_new > z_old
    # Fight heal stays 0 on the minute before conversion.
    if winner.transfer and winner.transfer > 1:
        pre = fight_row("Brand", winner.snaps[winner.transfer - 1], winner.transfer - 1)
        assert pre["heal"] == 0, pre
    at = fight_row("Zyra", winner.snaps[winner.transfer], winner.transfer)
    assert at["heal"] > 0
    assert at["helia_heal"] > 0


def main() -> None:
    report, payload, winner, baseline = run()
    _assert(winner, baseline, payload)
    print(report)
    out = Path(__file__).resolve().parent
    (out / "component-path-report.txt").write_text(report + "\n", encoding="utf-8")
    (out / "component-path-results.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"\nWrote {out / 'component-path-report.txt'}")


if __name__ == "__main__":
    main()
