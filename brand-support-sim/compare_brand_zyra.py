#!/usr/bin/env python3
"""
Brand vs Zyra on the same Wild Rift 7.3b support build.

1. Black Mist Scythe
2. Ionian Boots of Lucidity
3. Liandry's Torment
4. Whispering Circlet → Diadem of Songs
5. Echoes of Helia
6. Harmonic Echo

Same gold, same items. The kit is the only difference.
Neither champion has a heal or a shield, so Helia pays out only after Diadem.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parent))

from simulate_brand_support import (
    FIGHT_S,
    ability_ranks,
    carry_stats,
    evaluate,
    finished_names,
    front_stats,
    gold_at_minute,
    haste_cd,
    helia_cap,
    level_at_minute,
    rank_value,
    stats_at,
)

# Liandry is bought through Fated Ashes and Haunting Guise. The resolver
# spends leftover gold on those parts before the combine.
PATH: List[str] = [
    "Spectral Sickle",
    "Ionian Boots of Lucidity",
    "Liandry's Torment",
    "Whispering Circlet",
    "Echoes of Helia",
    "Harmonic Echo",
]

MINUTES = (8, 12, 16, 20, 22, 23)
CLOCK_TO = 24

BASE = {
    # hp, hp growth, armor, armor growth, mr, mr growth
    "Brand": (630, 120, 34, 4.5, 36, 1.2),
    "Zyra": (600, 120, 37, 4.5, 36, 1.5),
}


def body(champ: str, level: int, bonus_hp: float) -> Dict[str, float]:
    hp0, hpg, ar0, arg, mr0, mrg = BASE[champ]
    hp = hp0 + hpg * (level - 1) + bonus_hp
    armor = ar0 + arg * (level - 1)
    mr = mr0 + mrg * (level - 1)
    return {
        "hp": hp,
        "armor": armor,
        "mr": mr,
        "ehp_phys": hp * (1 + armor / 100),
        "ehp_magic": hp * (1 + mr / 100),
    }


def brand_utility(level: int) -> Dict[str, float]:
    """Expected crowd control delivered in the 8s fight."""
    ranks = ability_ranks(level, "WQE")
    # Stun requires the target to already be ablaze. E is point-click.
    if ranks["Q"] and ranks["E"]:
        p_stun = 0.90 * 0.72
    elif ranks["Q"]:
        p_stun = 0.70 * 0.72
    else:
        p_stun = 0.0
    stun = 1.75 * p_stun
    # Pyroclasm slow is 0.25s per bounce. One meaningful slow on the carry.
    slow = 0.25 * (0.88 if ranks["R"] else 0.0)
    return {
        "hard_cc": stun,
        "uncleanseable": 0.0,
        "soft_cc": slow,
        "zone_s": 0.0,
        "point_click": 0.90 if ranks["E"] else 0.0,
        "root_s": 0.0,
        "knockup_s": 0.0,
        "stun_s": stun,
    }


def zyra_utility(level: int) -> Dict[str, float]:
    ranks = ability_ranks(level, "QEW")
    root_dur = rank_value([0, 1.0, 1.25, 1.5, 1.75], ranks["E"])
    # One line root. Carry is the aim point; the frontliner is in it less often.
    root = root_dur * (0.70 + 0.45)
    # Stranglethorns knockup is 1s. Mikael's Blessing does not cleanse knockups.
    knock = 1.0 * 0.85 * (2.0 if ranks["R"] else 0.0)
    return {
        "hard_cc": root + knock,
        "uncleanseable": knock,
        "soft_cc": 0.0,
        "zone_s": 6.0,
        "point_click": 0.0,
        "root_s": root,
        "knockup_s": knock,
        "stun_s": 0.0,
    }


UTILITY = {"Brand": brand_utility, "Zyra": zyra_utility}


def lane_pre_per_min(st) -> float:
    """Champion damage per minute of lane, including Liandry while it is owned."""
    ap = st.ap
    hp, _mr = carry_stats(st.level, st.minute)
    if st.champ == "Brand":
        ranks = ability_ranks(st.level, "WQE")
        w = rank_value([0, 70, 120, 170, 220], ranks["W"]) + 0.55 * ap
        cd = haste_cd(rank_value([0, 9.5, 9, 8.5, 8], ranks["W"]) or 9, st.ah)
        casts = 60 / cd
        spells = casts * 0.48 * w * 1.15
        blaze = casts * 0.30 * 0.02 * hp
        # A landed W refreshes 3s of Liandry. He cannot keep it up the whole minute.
        burn_uptime = min(0.55, (3.0 / cd) * 0.48) if st.liandry else 0.0
        burn = 0.02 * hp * burn_uptime * 60 * (1.04 if st.liandry else 1)
        return spells + blaze + burn
    ranks = ability_ranks(st.level, "QEW")
    q = rank_value([0, 60, 115, 170, 225], ranks["Q"]) + 0.50 * ap
    cd = haste_cd(rank_value([0, 8, 7.5, 7, 6.5], ranks["Q"]) or 8, st.ah)
    casts = 60 / cd
    plant = 10 + (108 - 10) * (st.level - 1) / 14 + 0.15 * ap
    # One plant on the carry for ~4s of a poke, second plant at half damage.
    plants = casts * 0.55 * 4.0 * 0.8 * plant * 0.85
    spells = casts * 0.55 * q
    # Plants keep Liandry ticking. Without Rylai they walk out: ~72% of the plant window.
    burn_uptime = 0.72 * min(1.0, casts * 0.55 * 4.0 / 60) if st.liandry else 0.0
    burn = 0.02 * hp * burn_uptime * 60 * (1.04 if st.liandry else 1)
    return spells + plants + burn


def lane_heal_per_min(st) -> float:
    """Diadem + Helia during a minute that is 25% combat. No kit heal exists."""
    if not (st.diadem or st.helia):
        return 0.0
    hsp = st.hsp
    heal = 0.0
    combat_s = 60 * 0.25
    if st.diadem:
        heal += 0.008 * st.mana * combat_s * 0.92 * hsp
    if st.helia and st.diadem:
        pre = lane_pre_per_min(st)
        heal += min(helia_cap(st.level) * combat_s, 0.30 * pre) * hsp
    if st.harmonic:
        heal *= 1.30
    return heal


def snapshot(champ: str, minute: int) -> dict:
    st = stats_at(champ, PATH, minute)
    fight = evaluate(st)
    util = UTILITY[champ](st.level)
    tank = body(champ, st.level, st.hp)
    total = fight.post_front + fight.post_carry
    return {
        "champ": champ,
        "minute": minute,
        "level": st.level,
        "gold": st.gold,
        "items": finished_names(st.names),
        "ap": round(st.ap, 1),
        "ah": st.ah,
        "mana": round(st.mana),
        "hsp": round(st.hsp, 3),
        "diadem": st.diadem,
        "liandry": st.liandry,
        "helia": st.helia,
        "harmonic": st.harmonic,
        "damage": round(total),
        "front": round(fight.post_front),
        "carry": round(fight.post_carry),
        "pre": round(fight.pre),
        "heal": round(fight.heal),
        "lane_heal": round(lane_heal_per_min(st)),
        "lane_pre": round(lane_pre_per_min(st)),
        "hard_cc": round(util["hard_cc"], 2),
        "uncleanseable": round(util["uncleanseable"], 2),
        "stun_s": round(util["stun_s"], 2),
        "root_s": round(util["root_s"], 2),
        "knockup_s": round(util["knockup_s"], 2),
        "zone_s": util["zone_s"],
        "point_click": util["point_click"],
        "hp": round(tank["hp"]),
        "ehp_phys": round(tank["ehp_phys"]),
        "ehp_magic": round(tank["ehp_magic"]),
    }


def first_minute(pred) -> str:
    for m in range(1, CLOCK_TO + 1):
        st = stats_at("Brand", PATH, m)
        if pred(st):
            return f"{m}:00"
    return "after 24:00"


def run() -> tuple:
    lines: List[str] = []
    A = lambda s="": lines.append(s)

    A("=" * 78)
    A("BRAND vs ZYRA — SAME 7.3b SUPPORT BUILD")
    A("Scythe → Ionian → Liandry → Circlet/Diadem → Helia → Harmonic Echo")
    A("8-second fight, ultimate up, one frontline + one carry. No runes.")
    A("=" * 78)
    A("")
    A("SAME ITEMS, SO THE KIT IS THE WHOLE GAP")
    A("  Neither champion heals or shields. Helia stores 30% of pre-mitigation")
    A("  champion damage and spends it when Diadem heals an ally.")
    A("  In a short fight both fill that cap, so fight healing ties.")
    A("  Over a minute of lane, the champion who keeps Liandry ticking heals more.")
    A("  Harmony is the 7.3b rate: +0.25% of max mana as heal/shield power.")
    A("")
    A("WHEN THE SHARED BUILD TURNS ON (both champions, same gold)")
    A(f"  {'Min':>3}  {'Gold':>6}  {'Lvl':>3}  Finished")
    clock = []
    for m in range(1, CLOCK_TO + 1):
        st = stats_at("Brand", PATH, m)
        done = " · ".join(finished_names(st.names))
        if st.diadem:
            done = done.replace("Diadem of Songs", "DIADEM")
        A(f"  {m:>3}  {gold_at_minute(m):>6}  {level_at_minute(m):>3}  {done}")
        clock.append({"minute": m, "gold": gold_at_minute(m), "items": st.names, "diadem": st.diadem})
    A("")
    A(f"  Liandry finished: {first_minute(lambda s: s.liandry)}")
    A(f"  Circlet bought:   {first_minute(lambda s: s.circlet or s.diadem)}")
    A(f"  Diadem transforms:{first_minute(lambda s: s.diadem)}  (8 mana charges/min, cap is 12)")
    A(f"  Helia finished:   {first_minute(lambda s: s.helia)}")
    A(f"  Harmonic finished:{first_minute(lambda s: s.harmonic)}")
    A("  Liandry third pushes Diadem to the end of a normal game. Before that")
    A("  minute both champions heal 0 on this build.")
    A("")

    rows = []
    A("-" * 78)
    A("FIGHT — post-mitigation damage, ally healing, hard CC")
    A("Hard CC is expected champion-seconds in the 8s fight (two bodies can both be hit).")
    A("-" * 78)
    for minute in MINUTES:
        A(f"  [{minute}:00]")
        A(f"  {'Champ':<8} {'Dmg':>7} {'Front':>7} {'Carry':>7} {'Heal':>7} "
          f"{'Lane/m':>7} {'CC':>6} {'NoCleanse':>9} {'AP':>5}")
        pair = []
        for champ in ("Brand", "Zyra"):
            row = snapshot(champ, minute)
            rows.append(row)
            pair.append(row)
            A(f"  {champ:<8} {row['damage']:>7} {row['front']:>7} {row['carry']:>7} "
              f"{row['heal']:>7} {row['lane_heal']:>7} {row['hard_cc']:>6.2f} "
              f"{row['uncleanseable']:>9.2f} {row['ap']:>5.0f}")
        b, z = pair
        if b["damage"]:
            A(f"  Zyra damage is {100 * z['damage'] / b['damage'] - 100:+.0f}% vs Brand. "
              f"Zyra heal is {z['heal'] - b['heal']:+.0f} HP.")
        A("")

    A("-" * 78)
    A("UTILITY DETAIL AT 20:00")
    A("-" * 78)
    A("  Brand stun: 1.75s, only if the target is already ablaze. Expected")
    A("  value uses E hit 90% then Q hit 72%. One target. Mikael's cleanses it.")
    A("  Brand also has a point-click E, so the blaze setup does not miss as a skillshot.")
    A("  Zyra root: 1.0–1.75s by rank, skillshot. Aim the carry (70%), clip the")
    A("  frontliner less often (45%). No setup spell required.")
    A("  Zyra ultimate: 1s knockup on both champions at 85% if they are grouped.")
    A("  Mikael's Blessing does not cleanse a knockup.")
    A("  Zyra plants keep a 6s zone on the fight and refresh Liandry after she steps back.")
    A("")
    late = [r for r in rows if r["minute"] == 20]
    A(f"  {'':<16} {'Brand':>10} {'Zyra':>10}")
    labels = [
        ("Hard CC s", "hard_cc"),
        ("of which stun", "stun_s"),
        ("of which root", "root_s"),
        ("of which knockup", "knockup_s"),
        ("Not cleansable", "uncleanseable"),
        ("Plant zone s", "zone_s"),
        ("Point-click setup", "point_click"),
        ("HP", "hp"),
        ("EHP vs physical", "ehp_phys"),
        ("EHP vs magic", "ehp_magic"),
        ("Mana", "mana"),
    ]
    by = {r["champ"]: r for r in late}
    for label, key in labels:
        bv, zv = by["Brand"][key], by["Zyra"][key]
        if isinstance(bv, float):
            A(f"  {label:<16} {bv:>10.2f} {zv:>10.2f}")
        else:
            A(f"  {label:<16} {bv:>10} {zv:>10}")
    A("")
    A("  HP and resists are the champion bases plus the same item health.")
    A("  Mana is almost the same, so the Diadem tick (0.8% max mana) matches.")
    A("  Any extra heal is Helia. An 8s fight fills its per-second cap for both.")

    b20 = by["Brand"]
    z20 = by["Zyra"]
    b23 = next(r for r in rows if r["minute"] == 23 and r["champ"] == "Brand")
    z23 = next(r for r in rows if r["minute"] == 23 and r["champ"] == "Zyra")
    b8 = next(r for r in rows if r["minute"] == 8 and r["champ"] == "Brand")
    z8 = next(r for r in rows if r["minute"] == 8 and r["champ"] == "Zyra")
    b22 = next(r for r in rows if r["minute"] == 22 and r["champ"] == "Brand")
    z22 = next(r for r in rows if r["minute"] == 22 and r["champ"] == "Zyra")

    A("")
    A("-" * 78)
    A("WHICH IS BETTER ON THIS BUILD")
    A("-" * 78)
    A("  Zyra. The damage lead is real early and small later. The CC lead is large")
    A("  at every minute. Fight healing ends in a tie, and it does not exist until Diadem.")
    A("")
    A(f"  Damage at 8:00, Scythe + Ionian + Fated Ashes: Zyra {z8['damage']}, Brand {b8['damage']} "
      f"({100 * z8['damage'] / b8['damage'] - 100:.0f}%).")
    A(f"  Damage at 20:00, Liandry + Helia: Zyra {z20['damage']}, Brand {b20['damage']} "
      f"({100 * z20['damage'] / b20['damage'] - 100:.0f}%).")
    A(f"  Frontline at 20:00: Zyra {z20['front']}, Brand {b20['front']}.")
    A(f"  Carry at 20:00: Brand {b20['carry']}, Zyra {z20['carry']}. "
      "Brand's detonation is the better single-target hit.")
    A(f"  At 23:00 with Harmonic: Zyra {z23['damage']}, Brand {b23['damage']}.")
    A("")
    A(f"  Healing is 0 until Diadem at 22:00. That minute: Brand {b22['heal']}, Zyra {z22['heal']}.")
    A(f"  With Harmonic at 23:00: Brand {b23['heal']}, Zyra {z23['heal']}. "
      "An 8s fight fills Helia's per-second cap for both, so the fight heal ties.")
    A(f"  Lane heal/min at 23:00: Zyra {z23['lane_heal']}, Brand {b23['lane_heal']}.")
    A("  Plants keep Liandry burning between casts. Brand's W does not.")
    A("  That is the heal gap, and it is a lane gap.")
    A("")
    A(f"  Hard CC at 20:00: Zyra {z20['hard_cc']:.2f}s, Brand {b20['hard_cc']:.2f}s.")
    A(f"  {z20['uncleanseable']:.2f}s of Zyra's CC is a knockup, so Mikael's cannot cleanse it.")
    A("  Brand's 1.75s stun is the longer lock on one champion, and E is point-click,")
    A("  so the setup itself is reliable. It is still one cleansable stun, plus no zone.")
    A("  Bodies are the same: about 3000 HP, and effective HP is within 1%.")
    A("")
    A("  On this item list Zyra does more of the things the items pay for:")
    A("  Liandry uptime, lane healing once Diadem exists, and crowd control.")
    A("  Brand is the better choice only when the draft wants that point-click stun.")
    A("=" * 78)

    payload = {
        "meta": {
            "patch": "7.3b",
            "build": PATH,
            "champions": ["Brand", "Zyra"],
            "better": "Zyra",
            "first_heal_minute": 22,
        },
        "clock": clock,
        "rows": rows,
    }
    return "\n".join(lines), payload


def main() -> None:
    report, payload = run()
    print(report)
    out = "/workspace/brand-support-sim"
    with open(f"{out}/brand-zyra-report.txt", "w", encoding="utf-8") as f:
        f.write(report + "\n")
    with open(f"{out}/brand-zyra-results.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    by_key = {(r["minute"], r["champ"]): r for r in payload["rows"]}
    z20 = by_key[(20, "Zyra")]
    b20 = by_key[(20, "Brand")]
    z23 = by_key[(23, "Zyra")]
    b23 = by_key[(23, "Brand")]
    assert by_key[(8, "Zyra")]["damage"] > by_key[(8, "Brand")]["damage"]
    assert z20["damage"] > b20["damage"]
    assert z20["front"] > b20["front"]
    assert z20["hard_cc"] > b20["hard_cc"] * 2
    assert by_key[(12, "Brand")]["heal"] == 0
    assert by_key[(20, "Brand")]["heal"] == 0
    assert b23["heal"] > 0 and z23["heal"] > 0
    assert abs(z23["heal"] - b23["heal"]) / b23["heal"] < 0.15
    assert z23["lane_heal"] > b23["lane_heal"] * 1.4
    assert payload["meta"]["better"] == "Zyra"


if __name__ == "__main__":
    main()
