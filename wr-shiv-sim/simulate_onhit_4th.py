#!/usr/bin/env python3
"""
Wild Rift 7.3 — On-hit clump, 4th item: Runaan's vs the alternatives

Core is already Shiv → Rageblade → Terminus (or Nashor on Teemo).
Shiv copies on-hit on Energized (~every 4.2 autos).
Runaan copies on-hit on EVERY auto, to 2 nearby targets (55% AD bolts).

Question: should the 4th item be Runaan's Hurricane?
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple
import json

GAME_MINUTES = 26
FIGHT_SECONDS = 8.0
KEY_MINUTES = (20, 22, 24, 26)


def gold_at_minute(m: int) -> int:
    if m <= 0:
        return 500
    total = 500
    for t in range(1, m + 1):
        if t <= 5:
            total += 380
        elif t <= 10:
            total += 490
        else:
            total += 560
    return total


def level_at_minute(m: int) -> int:
    # WR 15-cap. Farmer hits 15 ~20:00 and stays there.
    table = {
        1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7, 7: 8, 8: 8,
        9: 9, 10: 10, 11: 11, 12: 11, 13: 12, 14: 12,
        15: 13, 16: 13, 17: 14, 18: 14, 19: 15, 20: 15,
        21: 15, 22: 15, 23: 15, 24: 15, 25: 15, 26: 15,
    }
    return table.get(m, 15)


def basic_rank(level: int) -> int:
    if level >= 9:
        return 4
    if level >= 6:
        return 3
    if level >= 3:
        return 2
    return 1


def mit(amount: float, resist: float, pct_pen: float = 0.0, flat: float = 0.0) -> float:
    eff = max(0.0, resist * (1.0 - pct_pen) - flat)
    return amount * 100.0 / (100.0 + eff)


def clump(m: int) -> List[Tuple[str, float, float, float, float]]:
    """(name, hp, armor, mr, hp_frac)"""
    lv = level_at_minute(m)
    return [
        ("tank", 750 + 110 * lv + 70 * m, 45 + 3.2 * lv + 8 * max(0, m - 8), 40 + 2.2 * lv + 6 * max(0, m - 8), 0.80),
        ("bruiser", 680 + 100 * lv + 40 * m, 40 + 2.8 * lv + 4 * max(0, m - 8), 36 + 1.8 * lv + 3 * max(0, m - 8), 0.75),
        ("squish", 600 + 90 * lv + 18 * m, 32 + 2.0 * lv + 1.5 * max(0, m - 10), 32 + 1.4 * lv + 1.2 * max(0, m - 10), 0.70),
        ("squish", 580 + 88 * lv + 16 * m, 32 + 2.0 * lv + 1.5 * max(0, m - 10), 32 + 1.4 * lv + 1.2 * max(0, m - 10), 0.70),
    ]


# ---------------------------------------------------------------------------
# Items / loadouts
# ---------------------------------------------------------------------------

FOURTH = {
    "none": {"cost": 0, "ad": 0, "ap": 0, "as": 0, "onhit_m": 0, "botrk": False, "runaan": False, "wit": False, "terminus": False, "label": "(no 4th)"},
    "runaan": {"cost": 2650, "ad": 0, "ap": 0, "as": 0.40, "onhit_m": 0, "botrk": False, "runaan": True, "wit": False, "terminus": False, "label": "Runaan's Hurricane"},
    "botrk": {"cost": 3100, "ad": 40, "ap": 0, "as": 0.30, "onhit_m": 0, "botrk": True, "runaan": False, "wit": False, "terminus": False, "label": "Blade of the Ruined King"},
    "wit": {"cost": 2800, "ad": 0, "ap": 0, "as": 0.50, "onhit_m": 40, "botrk": False, "runaan": False, "wit": True, "terminus": False, "label": "Wit's End"},
    "terminus": {"cost": 3000, "ad": 35, "ap": 0, "as": 0.35, "onhit_m": 30, "botrk": False, "runaan": False, "wit": False, "terminus": True, "label": "Terminus"},
    "bt": {"cost": 3200, "ad": 75, "ap": 0, "as": 0, "onhit_m": 0, "botrk": False, "runaan": False, "wit": False, "terminus": False, "label": "Bloodthirster"},
}


@dataclass
class Champ:
    name: str
    base_ad: float
    ad_g: float
    base_as: float
    as_ratio: float
    as_g: float
    bonus0: float
    ap_core: bool  # Nashor 3rd instead of Terminus
    note: str


CHAMPS = [
    Champ("Kog'Maw", 54, 3.5, 0.665, 0.665, 0.027, 0.20, False, "W %HP on every bolt"),
    Champ("Varus", 54, 3.6, 0.658, 0.658, 0.032, 0.22, False, "Blight stacks on every bolt, one Q pops the pit"),
    Champ("Kalista", 54, 4.5, 0.694, 0.694, 0.032, 0.205, False, "Rend spears on every bolt, one E rips"),
    Champ("Teemo", 52, 3.6, 0.690, 0.690, 0.022, 0.125, True, "Poison on every bolt; Nashor 3rd"),
    Champ("Kai'Sa", 59, 3.5, 0.644, 0.644, 0.032, 0.125, False, "Plasma on bolts; still hard to 5-pop extras"),
]


@dataclass
class Loadout:
    ad: float
    ap: float
    as_pct: float
    onhit_m: float
    pct_pen: float
    flat_mpen: float
    shiv: bool
    guinsoo: bool
    botrk: bool
    runaan: bool
    nashor: bool
    items: List[str]
    fourth_online: bool
    leftover: int


def build(champ: Champ, gold: int, fourth_key: str) -> Loadout:
    boots = 1200 if champ.ap_core else 1000
    core = [
        ("Statikk Shiv", 3000),
        ("Guinsoo's Rageblade", 3000),
        ("Nashor's Tooth" if champ.ap_core else "Terminus", 2900 if champ.ap_core else 3000),
    ]
    pool = gold - boots
    items = ["Boots of Mana"] if champ.ap_core else ["Berserker's"]
    bought = 0
    for name, cost in core:
        if pool >= cost:
            pool -= cost
            items.append(name)
            bought += 1
        else:
            break

    fourth_online = False
    spec = FOURTH[fourth_key]
    if bought == 3 and fourth_key != "none" and pool >= spec["cost"]:
        pool -= spec["cost"]
        items.append(spec["label"])
        fourth_online = True
    elif bought < 3:
        spec = FOURTH["none"]

    lv = 15  # filled in by caller via stats; items only here
    ad = champ.base_ad
    ap = 25.0 if champ.ap_core else 0.0
    asp = champ.bonus0 + (0.0 if champ.ap_core else 0.35)
    onhit = 0.0
    pct_pen = 0.0
    flat = 8.0 if champ.ap_core else 0.0
    shiv = guinsoo = nashor = False

    if "Statikk Shiv" in items:
        ad += 40
        ap += 40
        asp += 0.30
        shiv = True
    if "Guinsoo's Rageblade" in items:
        ad += 35
        ap += 30
        onhit += 30
        guinsoo = True
    if "Terminus" in items:
        ad += 35
        asp += 0.35
        onhit += 30
        pct_pen = 0.10
    if "Nashor's Tooth" in items:
        ap += 80
        asp += 0.50
        onhit += 15 + 0.20 * ap
        nashor = True
    if fourth_online:
        ad += spec["ad"]
        ap += spec["ap"]
        asp += spec["as"]
        onhit += spec["onhit_m"]
        if spec["terminus"]:
            ad += 0  # already in spec
            pct_pen = max(pct_pen, 0.10)
            onhit += 0  # spec already added 30
    # Nashor on-hit uses total AP after 4th (Teemo 4th has no AP anyway)

    return Loadout(
        ad=ad,
        ap=ap,
        as_pct=asp,
        onhit_m=onhit,
        pct_pen=pct_pen,
        flat_mpen=flat,
        shiv=shiv,
        guinsoo=guinsoo,
        botrk=fourth_online and spec["botrk"],
        runaan=fourth_online and spec["runaan"],
        nashor=nashor,
        items=items,
        fourth_online=fourth_online or fourth_key == "none",
        leftover=pool,
    )


def finish_stats(champ: Champ, lo: Loadout, level: int) -> Loadout:
    lo.ad += champ.ad_g * (level - 1)
    lo.as_pct += champ.as_g * (level - 1)
    if champ.name == "Varus":
        gained = lo.as_pct * 0.15 * 100.0
        lo.ad += gained
        lo.ap += gained
    return lo


# ---------------------------------------------------------------------------
# Kit on-hit / detonates
# ---------------------------------------------------------------------------


def kit_onhit(champ: Champ, lo: Loadout, level: int, tgt, bounce: bool) -> float:
    hp, ar, mr = tgt[1], tgt[2], tgt[3]
    r = basic_rank(level)
    if champ.name == "Kog'Maw":
        pct = [0, 0.015, 0.025, 0.035, 0.045][r] + 0.015 * lo.ap / 100.0
        return mit(pct * hp, mr, lo.pct_pen, lo.flat_mpen)
    if champ.name == "Varus":
        return mit([0, 15, 25, 35, 45][r] + 0.35 * lo.ap, mr, lo.pct_pen, lo.flat_mpen)
    if champ.name == "Teemo":
        return mit(8 + (36 - 8) * (level - 1) / 14 + 0.20 * lo.ap, mr, lo.pct_pen, lo.flat_mpen)
    if champ.name == "Kai'Sa":
        stacks = 0 if bounce else 2
        plasma = 4 + level + 0.12 * lo.ap + stacks * (1 + 0.2 * level + 0.02 * lo.ap)
        return mit(plasma, mr, lo.pct_pen, lo.flat_mpen)
    return 0.0


def item_onhit(lo: Loadout, tgt) -> Tuple[float, float]:
    """magic, physical"""
    hp, ar, mr, frac = tgt[1], tgt[2], tgt[3], tgt[4]
    mag = mit(lo.onhit_m, mr, lo.pct_pen, lo.flat_mpen) if lo.onhit_m else 0.0
    phys = mit(0.07 * hp * frac, ar, lo.pct_pen) if lo.botrk else 0.0
    return mag, phys


def detonate(champ: Champ, lo: Loadout, level: int, tgt, extra_hits: float) -> float:
    if extra_hits <= 0:
        return 0.0
    hp, ar, mr = tgt[1], tgt[2], tgt[3]
    r = basic_rank(level)
    if champ.name == "Varus":
        stacks = min(3.0, extra_hits)
        pct = ([0, 0.030, 0.035, 0.040, 0.045][r] + 0.012 * lo.ap / 100.0) * stacks * 1.25
        return mit(pct * hp, mr, lo.pct_pen, lo.flat_mpen)
    if champ.name == "Kalista":
        spears = max(1, int(round(extra_hits)))
        base = [0, 30, 45, 60, 75][r] + 0.70 * lo.ad
        extra = [0, 12, 22, 32, 42][r] + [0, 0.36, 0.43, 0.50, 0.57][r] * lo.ad
        return mit(base + extra * (spears - 1), ar, lo.pct_pen)
    if champ.name == "Teemo":
        per_s = 11 + (53 - 11) * (level - 1) / 14 + 0.09 * lo.ap
        return mit(per_s * 4.0, mr, lo.pct_pen, lo.flat_mpen)
    return 0.0


def attacks_in_fight(champ: Champ, lo: Loadout, level: int) -> float:
    extra = 0.24 if lo.guinsoo else 0.0
    if champ.name == "Kog'Maw":
        extra += [0, 0.05, 0.10, 0.15, 0.20][basic_rank(level)]
    total = min(3.0, champ.base_as + champ.as_ratio * (lo.as_pct + extra))
    return total * FIGHT_SECONDS * 0.85


def fight(champ: Champ, lo: Loadout, minute: int, mode: str) -> Tuple[float, float, float, str]:
    """
    mode: 'clump' (4 champs) or 'duel' (tank only).
    Conservative overlap: on a given auto, a body hit by a Runaan bolt
    does NOT also eat Shiv's copied on-hit (lightning still applies).
    """
    level = level_at_minute(minute)
    lo = finish_stats(champ, lo, level)
    targets = clump(minute)
    if mode == "duel":
        targets = targets[:1]
    n = attacks_in_fight(champ, lo, level)
    phantom = 1.33 if lo.guinsoo else 1.0
    en = (n / 4.2) if lo.shiv else 0.0
    extras = targets[1:]
    runaan_n = min(2, len(extras)) if lo.runaan else 0

    primary = targets[0]
    auto_p = mit(lo.ad, primary[2], lo.pct_pen)
    mag, phys = item_onhit(lo, primary)
    kit = kit_onhit(champ, lo, level, primary, bounce=False)
    dmg = n * (auto_p + (mag + phys + kit) * phantom)
    if lo.shiv:
        dmg += en * mit(60.0, primary[3], lo.pct_pen, lo.flat_mpen)

    # Primary detonate uses YOUR autos, not 4th-item unique — skip for delta fairness
    # (both 4ths still let you E/Q the tank). Count it once in total, same without 4th.
    dmg += detonate(champ, lo, level, primary, n if champ.name == "Kalista" else (3 if champ.name == "Varus" else (1 if champ.name == "Teemo" else 0)))

    bounce_dmg = 0.0
    bolt_dmg = 0.0

    if runaan_n:
        for tgt in extras[:runaan_n]:
            bolt_ad = mit(0.55 * lo.ad, tgt[2], lo.pct_pen)
            mag, phys = item_onhit(lo, tgt)
            kit = kit_onhit(champ, lo, level, tgt, bounce=True)
            bolt_dmg += n * (bolt_ad + mag + phys + kit)
            # stacks: every auto
            bounce_dmg += detonate(champ, lo, level, tgt, n)

    # Shiv: lightning to all extras. Copied on-hit only on extras Runaan did not cover.
    uncovered = extras[runaan_n:]
    if lo.shiv and extras:
        for tgt in extras:
            bounce_dmg += en * mit(60.0, tgt[3], lo.pct_pen, lo.flat_mpen)
        for tgt in uncovered:
            mag, phys = item_onhit(lo, tgt)
            kit = kit_onhit(champ, lo, level, tgt, bounce=True)
            bounce_dmg += en * (mag + phys + kit)
            bounce_dmg += detonate(champ, lo, level, tgt, en)

    note = []
    if lo.runaan:
        note.append(f"runaan {runaan_n} bolts/auto")
    if lo.botrk:
        note.append("botrk %HP")
    if lo.shiv:
        note.append("shiv energized")
    total = dmg + bolt_dmg + bounce_dmg
    return total, bolt_dmg, bounce_dmg, ", ".join(note) if note else "core only"


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------


FOURTH_KEYS_ADC = ["none", "runaan", "botrk", "wit", "bt"]
FOURTH_KEYS_AP = ["none", "runaan", "botrk", "wit", "terminus"]


def keys_for(champ: Champ) -> List[str]:
    return FOURTH_KEYS_AP if champ.ap_core else FOURTH_KEYS_ADC


def run_all() -> Dict:
    out: Dict = {}
    for champ in CHAMPS:
        out[champ.name] = {"note": champ.note, "minutes": {}}
        for m in KEY_MINUTES:
            gold = gold_at_minute(m)
            rows = []
            for k in keys_for(champ):
                lo = build(champ, gold, k)
                # rebuild a fresh loadout per mode (finish_stats mutates)
                lo_c = build(champ, gold, k)
                lo_d = build(champ, gold, k)
                clump_d, bolts, shiv, note = fight(champ, lo_c, m, "clump")
                duel_d, _, _, _ = fight(champ, lo_d, m, "duel")
                rows.append({
                    "fourth": FOURTH[k]["label"] if k != "none" else "(no 4th)",
                    "key": k,
                    "online": lo.fourth_online if k != "none" else True,
                    "items": lo.items,
                    "clump": round(clump_d, 1),
                    "duel": round(duel_d, 1),
                    "bolts": round(bolts, 1),
                    "shiv_extra": round(shiv, 1),
                    "note": note,
                    "gold": gold,
                    "leftover": lo.leftover,
                })
            out[champ.name]["minutes"][str(m)] = rows
    return out


def summarize(data: Dict) -> str:
    lines: List[str] = []
    a = lines.append
    a("=" * 78)
    a("ON-HIT CLUMP — 4TH ITEM: RUNAAN'S OR NOT?  (Wild Rift 7.3)")
    a("Core: Shiv → Rageblade → Terminus (Nashor on Teemo)")
    a("8s window  |  clump = 4 champs  |  duel = the tank only")
    a("=" * 78)
    a("")
    a("WHY THIS IS A REAL QUESTION")
    a("  Shiv already copies on-hit, but only on Energized (~every 4.2 autos).")
    a("  Runaan copies on-hit on EVERY auto, to 2 nearby targets (55% AD bolts).")
    a("  7.3 Runaan is 2650g — cheaper than BotRK (3100) or Wit's End (2800).")
    a("")
    a("GOLD (farmer)")
    for m in KEY_MINUTES:
        a(f"  {m}:00  {gold_at_minute(m):>6}g   3-item core ~10000g + boots")
    a("  Runaan 4th (~12650g with Berserker's) finishes ~24:00. BotRK (~13100g) ~25:00.")
    a("  Teemo on Boots of Mana is ~100g short of Runaan at 24:00 — online ~25:00.")
    a("")

    # Per-champ tables at 26 (all 4ths online) and 24 (only Runaan)
    for m in (24, 26):
        a("-" * 78)
        a(f"MINUTE {m}:00")
        a("-" * 78)
        for champ in CHAMPS:
            rows = data[champ.name]["minutes"][str(m)]
            a(f"  {champ.name} — {champ.note}")
            a(f"    {'4th':<28} {'Clump':>8} {'Duel':>8} {'On?':>5}  items")
            best_c = max(rows, key=lambda r: r["clump"] if r["online"] else -1)
            best_d = max(rows, key=lambda r: r["duel"] if r["online"] else -1)
            for r in sorted(rows, key=lambda x: x["clump"], reverse=True):
                mark = ""
                if r is best_c and r["online"]:
                    mark += " ← clump"
                if r is best_d and r["online"] and r["key"] != best_c["key"]:
                    mark += " ← duel"
                on = "yes" if r["online"] else "no"
                a(f"    {r['fourth']:<28} {r['clump']:>8.0f} {r['duel']:>8.0f} {on:>5}  {' › '.join(r['items'][-4:])}{mark}")
            a("")

    # Verdict per champ using 26:00 (fair completed 4th)
    a("-" * 78)
    a("VERDICT")
    a("-" * 78)
    a("  Should on-hit clump buy Runaan 4th?")
    a("")
    yes = 0
    for champ in CHAMPS:
        rows = {r["key"]: r for r in data[champ.name]["minutes"]["26"]}
        base = rows["none"]["clump"]
        run = rows["runaan"]
        alt_keys = [k for k in rows if k not in ("none", "runaan")]
        best_alt = max(alt_keys, key=lambda k: rows[k]["clump"])
        alt = rows[best_alt]
        duel_run = run["duel"]
        duel_alt = max(rows[k]["duel"] for k in alt_keys)
        clump_win = run["clump"] >= alt["clump"]
        if clump_win:
            yes += 1
            rec = "YES — Runaan"
        else:
            rec = f"NO — {alt['fourth']}"
        a(f"  {champ.name}: {rec}")
        a(f"     Clump 26:00  Runaan {run['clump']:.0f}  vs {alt['fourth']} {alt['clump']:.0f}  (3-item {base:.0f})")
        a(f"     Duel  26:00  Runaan {duel_run:.0f}  vs best other {duel_alt:.0f}")
        a("")

    a("  RULE:")
    a("  • Fight is still a clump (dragon, Baron, mid choke): YES, buy Runaan 4th.")
    a("    It is the only 4th that copies Kog W / Varus Blight / Kalista spears /")
    a("    Teemo poison on every auto, not just on Shiv procs.")
    a("  • Fight is you hitting one tank: NO. BotRK (or Wit's vs AP) beats empty bolts.")
    a("  • Games that end 20–22: you never finish a 4th. Don't force it.")
    a("  • If the game is stretching, Runaan completes first (2650 vs 3100 BotRK).")
    a("  • Do not sell Shiv for Runaan. Shiv is 40 AP + lightning + 3–6 bounce;")
    a("    Runaan is the per-auto copier. They stack: bolts cover 2 extras every")
    a("    swing, Shiv still tags whoever the bolts missed and pays 60 magic.")
    a("  • Vayne is not in this lane. Silver Bolts still do not ride Runaan bolts.")
    a("=" * 78)
    return "\n".join(lines)


def main() -> None:
    data = run_all()
    report = summarize(data)
    print(report)
    out = "/workspace/wr-shiv-sim"
    with open(f"{out}/report_4th.txt", "w", encoding="utf-8") as fh:
        fh.write(report + "\n")
    with open(f"{out}/results_4th.json", "w", encoding="utf-8") as fh:
        json.dump({"meta": {"question": "On-hit clump 4th item Runaan?", "patch": "7.3"}, "data": data}, fh, indent=2)
    print(f"\nWrote {out}/report_4th.txt and {out}/results_4th.json")


if __name__ == "__main__":
    main()
