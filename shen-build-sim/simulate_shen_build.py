#!/usr/bin/env python3
"""
Wild Rift Shen Baron — farm / 1v1 / tank item-order
Patch 7.3 (Sep 2026).

Heartsteel first is too slow (no wave tool). Constraint:
  1st  farm the wave
  2nd  1v1
  rest tank for 1v9
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import json
from pathlib import Path

PATCH = "7.3"
GAME_MINUTES = 26
FIGHT_S = 8.0
OUT_DIR = Path(__file__).resolve().parent


def gold_at_minute(m: int) -> int:
    if m <= 0:
        return 500
    total = 500
    for t in range(1, m + 1):
        if t <= 4:
            total += 350
        elif t <= 10:
            total += 460
        elif t <= 16:
            total += 530
        else:
            total += 570
    return total


def level_at_minute(m: int) -> int:
    table = {
        1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7, 7: 8, 8: 9,
        9: 10, 10: 11, 11: 11, 12: 12, 13: 12, 14: 13,
        15: 13, 16: 14, 17: 14, 18: 15, 19: 15, 20: 15,
        21: 15, 22: 15, 23: 15, 24: 15, 25: 15, 26: 15,
    }
    return table.get(m, min(15, 1 + m))


def skill_rank(level: int, skill: str) -> int:
    """Q max, E second, W last. R at 5/9/13."""
    if skill == "R":
        return 0 if level < 5 else 1 if level < 9 else 2 if level < 13 else 3
    q = [1, 4, 6, 8]
    e = [2, 7, 10, 11]
    w = [3, 12, 14, 15]
    mapping = {"Q": q, "E": e, "W": w}
    return sum(1 for lv in mapping[skill] if level >= lv)


@dataclass
class Item:
    name: str
    cost: int
    ad: float = 0
    ap: float = 0
    hp: float = 0
    ah: float = 0
    as_pct: float = 0
    armor: float = 0
    mr: float = 0
    sheen: str = "none"  # none | dusk | iceborn
    heartsteel: bool = False
    sunfire: bool = False
    titanic: bool = False
    dawn: bool = False
    hull: bool = False
    rift: bool = False
    despair: bool = False
    thorn: bool = False
    twinguard: bool = False
    boots: bool = False


ITEMS: Dict[str, Item] = {
    "Ruby Crystal": Item("Ruby Crystal", 500, hp=150),
    "Long Sword": Item("Long Sword", 500, ad=12),
    "Dusk and Dawn": Item(
        "Dusk and Dawn", 3100, ap=70, hp=350, ah=20, as_pct=0.25, sheen="dusk"
    ),
    "Heartsteel": Item("Heartsteel", 2800, hp=700, ah=20, heartsteel=True),
    "Sunfire Aegis": Item(
        "Sunfire Aegis", 2900, hp=350, ah=15, armor=40, sunfire=True
    ),
    "Titanic Hydra": Item("Titanic Hydra", 3000, ad=40, hp=450, titanic=True),
    "Dawnshroud": Item(
        "Dawnshroud", 2700, hp=250, armor=50, mr=30, dawn=True
    ),
    "Iceborn Gauntlet": Item(
        "Iceborn Gauntlet", 3000, hp=300, ah=30, armor=50, sheen="iceborn"
    ),
    "Hullbreaker": Item("Hullbreaker", 3100, ad=45, hp=400, hull=True),
    "Riftmaker": Item("Riftmaker", 3100, ap=70, hp=350, ah=15, rift=True),
    "Unending Despair": Item(
        "Unending Despair", 3000, hp=300, ah=10, armor=40, mr=40, despair=True
    ),
    "Thornmail": Item("Thornmail", 2800, hp=200, armor=75, thorn=True),
    "Amaranth's Twinguard": Item(
        "Amaranth's Twinguard", 3200, hp=300, armor=50, mr=50, twinguard=True
    ),
    "Force of Nature": Item(
        "Force of Nature", 2800, hp=400, mr=60
    ),
    "Hollow Radiance": Item(
        "Hollow Radiance", 2800, hp=400, ah=15, mr=40, sunfire=True
    ),
    "Plated Steelcaps": Item(
        "Plated Steelcaps", 1200, hp=150, armor=25, boots=True
    ),
}


@dataclass
class Path:
    name: str
    legendaries: List[str]
    note: str


PATHS = [
    Path(
        "Sunfire → Dusk → tank",
        ["Sunfire Aegis", "Dusk and Dawn", "Dawnshroud", "Amaranth's Twinguard"],
        "1st burn-farm, 2nd Q sheen 1v1, rest tank. Fits the constraint.",
    ),
    Path(
        "Sunfire → Titanic → tank",
        ["Sunfire Aegis", "Titanic Hydra", "Dawnshroud", "Amaranth's Twinguard"],
        "1st burn-farm, 2nd cleave 1v1, rest tank.",
    ),
    Path(
        "Titanic → Dusk → tank",
        ["Titanic Hydra", "Dusk and Dawn", "Dawnshroud", "Amaranth's Twinguard"],
        "Fastest shove 1st, Dusk 2nd, Dawnshroud then Twinguard.",
    ),
    Path(
        "Titanic → Dusk → Despair",
        ["Titanic Hydra", "Dusk and Dawn", "Dawnshroud", "Unending Despair"],
        "Same farm/1v1; 4th Unending Despair for 1v9 pulse heal instead of Twinguard.",
    ),
    Path(
        "Hollow → Dusk → tank",
        ["Hollow Radiance", "Dusk and Dawn", "Force of Nature", "Unending Despair"],
        "AP-lane farm (Hollow burn). Same 2nd/rest plan.",
    ),
    Path(
        "CN 62% WR",
        ["Heartsteel", "Sunfire Aegis", "Thornmail", "Amaranth's Twinguard"],
        "China 7.3 most-used core (62.3% WR / 25% use). Heartsteel first.",
    ),
    Path(
        "Heart → Sunfire → Dawn",
        ["Heartsteel", "Sunfire Aegis", "Dawnshroud", "Thornmail"],
        "China 61.3% WR variant (6% use). Still Heartsteel first.",
    ),
    Path(
        "Dusk first (Voli copy)",
        ["Dusk and Dawn", "Hullbreaker", "Riftmaker", "Unending Despair"],
        "Rejected: Dusk does not farm the wave.",
    ),
]


def inventory_at_gold(path: Path, gold: int) -> List[Item]:
    owned: List[Item] = []
    spent = 0
    boots_pending = False
    for i, name in enumerate(path.legendaries):
        item = ITEMS[name]
        if spent + item.cost <= gold:
            owned.append(item)
            spent += item.cost
            if i == 0:
                boots_pending = True
        else:
            break
        if boots_pending and spent + ITEMS["Plated Steelcaps"].cost <= gold:
            owned.append(ITEMS["Plated Steelcaps"])
            spent += ITEMS["Plated Steelcaps"].cost
            boots_pending = False
    if not owned:
        owned = [ITEMS["Ruby Crystal"]]
    return owned


def resist_mult(res: float) -> float:
    return 100.0 / (100.0 + max(0.0, res))


def shen_base(level: int) -> Tuple[float, float, float, float]:
    # Patch 7.3: HP/lvl 124
    hp = 630 + 124 * (level - 1)
    ad = 58 + 4.55 * (level - 1)
    armor = 40 + 4.2 * (level - 1)
    mr = 32 + 2.05 * (level - 1)
    return hp, ad, armor, mr


def minute_of_item(path: Path, item_name: str) -> Optional[int]:
    for m in range(1, GAME_MINUTES + 1):
        names = [i.name for i in inventory_at_gold(path, gold_at_minute(m))]
        if item_name in names:
            return m
    return None


def heartsteel_stack_hp(path: Path, m: int) -> float:
    """~28 bonus HP per minute after Heartsteel completes, cap 600.
    Typical WR games land 400–600 stacks; this is the conservative middle.
    """
    bought = minute_of_item(path, "Heartsteel")
    if bought is None:
        return 0.0
    return min(600.0, max(0, m - bought) * 28.0)


def target_bruiser(m: int) -> Tuple[float, float, float]:
    lv = level_at_minute(m)
    hp = 720 + 118 * (lv - 1) + 35 * m
    armor = 52 + 4.4 * (lv - 1) + (25 if m >= 12 else 8)
    mr = 38 + 2.0 * (lv - 1) + (20 if m >= 14 else 5)
    return hp, armor, mr


def q_hit_pct(rank: int, ap: float, empowered: bool) -> float:
    if rank <= 0:
        return 0.0
    if empowered:
        base = [0, 0.055, 0.06, 0.065, 0.07][rank]
        return base + 0.02 * (ap / 100.0)
    base = [0, 0.03, 0.035, 0.04, 0.045][rank]
    return base + 0.015 * (ap / 100.0)


def q_flat(level: int) -> float:
    return 12 + (40 - 12) * (level - 1) / 14


@dataclass
class Fight:
    mix: float
    ehp: float
    strength: float
    hp: float
    shield: float
    items: List[str]
    bonus_hp: float = 0.0
    ap: float = 0.0
    armor: float = 0.0
    mr: float = 0.0
    r_shield: float = 0.0
    aoe: float = 0.0
    mitig: float = 1.0
    thorn: bool = False
    hs_stacks: float = 0.0


def fight_at(path: Path, m: int, fight_s: float = FIGHT_S) -> Fight:
    lv = level_at_minute(m)
    gold = gold_at_minute(m)
    inv = inventory_at_gold(path, gold)
    q = skill_rank(lv, "Q")
    e = skill_rank(lv, "E")
    w = skill_rank(lv, "W")
    r = skill_rank(lv, "R")

    base_hp, base_ad, base_ar, base_mr = shen_base(lv)
    hs_stacks = heartsteel_stack_hp(path, m)
    bonus_hp = sum(i.hp for i in inv) + hs_stacks
    bonus_ad = sum(i.ad for i in inv)
    ap = sum(i.ap for i in inv)
    as_pct = sum(i.as_pct for i in inv)
    armor = base_ar + sum(i.armor for i in inv)
    mr = base_mr + sum(i.mr for i in inv)
    has_dusk = any(i.sheen == "dusk" for i in inv)
    has_ice = any(i.sheen == "iceborn" for i in inv)
    has_hs = any(i.heartsteel for i in inv)
    has_sf = any(i.sunfire for i in inv)
    has_ti = any(i.titanic for i in inv)
    has_dawn = any(i.dawn for i in inv)
    has_hull = any(i.hull for i in inv)
    has_rift = any(i.rift for i in inv)
    has_despair = any(i.despair for i in inv)
    has_thorn = any(i.thorn for i in inv)
    has_twin = any(i.twinguard for i in inv)

    if has_rift:
        ap += 0.02 * bonus_hp

    max_hp = base_hp + bonus_hp
    total_ad = base_ad + bonus_ad
    t_hp, t_ar, t_mr = target_bruiser(m)
    mpen = 0.07 if has_rift else 0.0
    phys = resist_mult(t_ar)
    mag = resist_mult(t_mr * (1.0 - mpen))
    rift_amp = 1.05 if has_rift else 1.0

    # Q 3 empowered autos (blade through them) + extra AAs
    as_total = 0.70 * (1 + 0.025 * (lv - 1) + as_pct + (0.50 if q else 0))
    n_aa = max(3, min(1 + int(fight_s * as_total), 8))
    n_q_hits = min(3, n_aa)

    phys_raw = n_aa * total_ad
    mag_raw = 0.0

    pct = q_hit_pct(q, ap, empowered=True)
    flat = q_flat(lv)
    mag_raw += n_q_hits * (flat + pct * t_hp)
    if has_dusk:
        # extra on-hit on the spellblade auto = one extra Q on-hit
        mag_raw += flat + pct * t_hp
        mag_raw += 0.75 * base_ad + 0.10 * ap
    if has_ice:
        phys_raw += 1.00 * base_ad

    if e:
        e_d = [0, 60, 90, 120, 150][e] + 0.15 * bonus_hp
        phys_raw += e_d

    # Heartsteel: 2.5s charge then a hit. 3s lane trades often miss it.
    if has_hs and fight_s >= 4.0:
        phys_raw += 140 + 0.035 * max_hp
    if has_sf:
        mag_raw += fight_s * (20 + 0.015 * bonus_hp)
    n_cleave = 0
    if has_ti:
        n_cleave = max(1, int(fight_s / 1.75))
        phys_raw += n_cleave * (25 + 0.03 * bonus_hp)
    if has_dawn:
        mag_raw += 40 + 0.025 * bonus_hp
    if has_hull:
        phys_raw += (n_aa // 4) * (1.60 * base_ad + 0.05 * max_hp)
    n_despair = int(fight_s / 4.0) if has_despair else 0
    if n_despair:
        mag_raw += n_despair * 0.03 * max_hp
    if has_thorn:
        # they auto ~once per 1.6s; reflect 20 + 6% bonus armor + 1% bonus HP
        n_hit = max(1, int(fight_s / 1.6))
        mag_raw += n_hit * (20 + 0.06 * (armor - base_ar) + 0.01 * bonus_hp)

    mag_raw += 0.033 * max_hp  # Grasp
    mix = (phys_raw * phys + mag_raw * mag) * rift_amp

    ki = (51 + (100 - 51) * (lv - 1) / 14) + 0.14 * bonus_hp
    colo = 35 + 0.01 * max_hp  # Courage of the Colossus on E taunt
    w_block = 550.0 if w else 0.0  # Spirit's Refuge eats ~3 bruiser autos
    dawn_res = 0.0
    if has_dawn:
        dawn_res = 0.12 * max_hp  # 20% bonus resists ≈ extra ehp
    twin_res = 0.0
    if has_twin:
        # +30% resists after 5s. In 8s that is ~3s boosted ≈ 0.10 extra ehp.
        twin_res = 0.10 * max_hp
    heal = 0.013 * max_hp
    if n_despair:
        heal += n_despair * (0.03 * max_hp * 2.50)
    if has_rift:
        heal += 0.10 * mix * 0.50
    shield = ki + colo + w_block + dawn_res + twin_res
    ehp = max_hp + shield + heal

    if has_dawn:
        armor *= 1.08
        mr *= 1.08
    if has_twin and fight_s >= 5.0:
        armor *= 1.11
        mr *= 1.11
    mitig = 0.5 * resist_mult(armor) + 0.5 * resist_mult(mr)

    r_base = [0, 170, 340, 510][r]
    r_shield = r_base + 1.35 * ap + 0.15 * bonus_hp

    # Extra bodies in a 3-man brawl (Sunfire / Despair / Titanic cone).
    extra_mag = 0.0
    extra_phys = 0.0
    if has_sf:
        extra_mag += 2 * fight_s * (20 + 0.015 * bonus_hp)
    if n_despair:
        extra_mag += 2 * n_despair * 0.03 * max_hp
    if has_ti:
        extra_phys += 2 * n_cleave * (80 + 0.10 * bonus_hp)
    aoe = mix + extra_phys * phys + extra_mag * mag

    return Fight(
        mix=mix,
        ehp=ehp,
        strength=mix + 0.85 * ehp,
        hp=max_hp,
        shield=shield,
        items=[i.name for i in inv],
        bonus_hp=bonus_hp,
        ap=ap,
        armor=armor,
        mr=mr,
        r_shield=r_shield,
        aoe=aoe,
        mitig=mitig,
        thorn=has_thorn,
        hs_stacks=hs_stacks,
    )


def wave_frac(path: Path, m: int, seconds: float = 4.0) -> float:
    """Fraction of a cannon wave killed in `seconds`. Q is 150% vs minions.
    Sunfire Immolate is 200% vs minions. Titanic cone hits the rest of the wave.
    """
    lv = level_at_minute(m)
    inv = inventory_at_gold(path, gold_at_minute(m))
    q = skill_rank(lv, "Q")
    base_hp, base_ad, _, _ = shen_base(lv)
    bonus_hp = sum(i.hp for i in inv)
    bonus_ad = sum(i.ad for i in inv)
    ap = sum(i.ap for i in inv)
    as_pct = sum(i.as_pct for i in inv)
    total_ad = base_ad + bonus_ad
    has_dusk = any(i.sheen == "dusk" for i in inv)
    has_sf = any(i.sunfire for i in inv)
    has_ti = any(i.titanic for i in inv)

    # ~8 min cannon wave
    melee_hp, caster_hp, cannon_hp = 480.0, 320.0, 900.0
    melee_n, caster_n = 3, 3
    minion_ar = 12.0
    phys = resist_mult(minion_ar)

    as_total = 0.70 * (1 + 0.025 * (lv - 1) + as_pct + (0.50 if q else 0))
    n_aa = max(3, min(1 + int(seconds * as_total), 6))
    n_q = min(3, n_aa)
    # Q vs minions: 150% of the magic hit. Cap %HP so casters don't explode from champ ratios.
    pct = min(q_hit_pct(q, ap, empowered=False) * 1.5, 0.12)
    flat = q_flat(lv) * 1.5
    q_hit = (flat + pct * 400.0)  # dummy 400 HP minion

    aa_phys = n_aa * total_ad * phys
    q_mag = n_q * q_hit
    if has_dusk:
        q_mag += q_hit
        aa_phys += (0.75 * base_ad) * phys

    burn = 0.0
    if has_sf:
        tick = (20 + 0.015 * bonus_hp) * 2.0  # ~200% vs minions
        burn = tick * seconds

    cleave_primary = 0.0
    cleave_aoe = 0.0
    if has_ti:
        n_c = max(1, int(seconds / 1.75))
        cleave_primary = n_c * (25 + 0.03 * bonus_hp) * phys
        cleave_aoe = n_c * (80 + 0.10 * bonus_hp) * phys

    def kill_frac(hp: float, extra: float) -> float:
        dmg = aa_phys / 7.0 + q_mag / 7.0 + burn + extra
        return min(1.0, dmg / hp)

    # Autos+Q focus the cannon; burn and Titanic cone hit everyone.
    cannon = min(1.0, (aa_phys + q_mag + burn + cleave_primary) / cannon_hp)
    melee = kill_frac(melee_hp, cleave_aoe)
    caster = kill_frac(caster_hp, cleave_aoe)
    killed = cannon * cannon_hp + melee * melee_n * melee_hp + caster * caster_n * caster_hp
    total = cannon_hp + melee_n * melee_hp + caster_n * caster_hp
    return killed / total


def mitigated_ehp(f: Fight) -> float:
    """HP+shield+heal after 50/50 phys/magic incoming."""
    return f.ehp / max(0.20, f.mitig)


def aspect_row(path: Path) -> dict:
    short = fight_at(path, 8, fight_s=3.0)
    duel = fight_at(path, 16)
    late = fight_at(path, 26)
    return {
        "path": path.name,
        "lane_wave": wave_frac(path, 8),
        "lane_short_mix": short.mix,
        "lane_hp": short.hp,
        "solo_mix": duel.mix,
        "solo_ehp": duel.ehp,
        "solo_str": duel.strength,
        "tf_aoe": late.aoe,
        "tf_ehp": mitigated_ehp(late),
        "r_shield": late.r_shield,
        "split_ehp": late.ehp,
        "split_mix": late.mix,
        "thorn": late.thorn,
        "hs_stacks": late.hs_stacks,
        "hp26": late.hp,
        "items8": fight_at(path, 8).items,
        "items16": duel.items,
        "items26": late.items,
    }


def pick_side(ours: float, cn: float, ours_name: str, cn_name: str) -> str:
    if abs(ours - cn) < 0.03 * max(abs(ours), abs(cn), 1.0):
        return "tie"
    return ours_name if ours > cn else cn_name


def main() -> None:
    minutes = list(range(6, GAME_MINUTES + 1))
    snapshots: Dict[str, List[dict]] = {}
    # Constraint score: farm at 8, 1v1 mix at 16, tank ehp at 26.
    farm_m, duel_m, tank_m = 8, 16, 26
    rows_score = []
    for path in PATHS:
        snap = []
        for m in minutes:
            f = fight_at(path, m)
            snap.append(
                {
                    "m": m,
                    "gold": gold_at_minute(m),
                    "level": level_at_minute(m),
                    "items": f.items,
                    "mix": round(f.mix),
                    "ehp": round(f.ehp),
                    "wave": round(wave_frac(path, m), 3),
                    "r_shield": round(f.r_shield),
                    "aoe": round(f.aoe),
                    "hs_stacks": round(f.hs_stacks),
                }
            )
        snapshots[path.name] = snap
        farm = wave_frac(path, farm_m)
        mix = fight_at(path, duel_m).mix
        ehp = fight_at(path, tank_m).ehp
        rows_score.append((path, farm, mix, ehp))

    farm_max = max(r[1] for r in rows_score) or 1.0
    mix_max = max(r[2] for r in rows_score) or 1.0
    ehp_max = max(r[3] for r in rows_score) or 1.0

    def composite(row: Tuple[Path, float, float, float]) -> float:
        path, farm, mix, ehp = row
        # Heartsteel / Dusk-first are shown but lose the constraint.
        if path.legendaries[0] in ("Heartsteel", "Dusk and Dawn"):
            return -1.0
        return 0.34 * farm / farm_max + 0.33 * mix / mix_max + 0.33 * ehp / ehp_max

    ranked = sorted(rows_score, key=composite, reverse=True)
    winner = ranked[0][0]
    cn_path = next(p for p in PATHS if p.name == "CN 62% WR")
    ours_a = aspect_row(winner)
    cn_a = aspect_row(cn_path)

    lines = [
        f"Wild Rift Shen Baron — farm / 1v1 / tank — patch {PATCH}",
        "Heartsteel first is too slow (no wave tool).",
        "1st farms the wave, 2nd wins the 1v1, rest is tank for 1v9.",
        "",
        f"WINNER: {winner.name}",
        f"  {winner.note}",
        "",
        "Buy order",
        f"  Start     Ruby Crystal. First back: Bami's Cinder (farm now).",
        f"  1st item  {winner.legendaries[0]:<22} farm the wave",
        "  Boots     Plated Steelcaps",
        f"  2nd item  {winner.legendaries[1]:<22} 1v1",
        f"  3rd item  {winner.legendaries[2]:<22} tank",
        f"  4th item  {winner.legendaries[3]:<22} tank / 1v9",
        "  Enchant   Stoneplate",
        "",
        "Vs AP lane: Hollow Radiance 1st instead of Titanic, FoN later.",
        "Safer/cheaper farm: Sunfire 1st (Bami's), then Dusk 2nd, same tank rest.",
        "Do not buy Heartsteel. Do not rush Dusk first (it does not farm).",
        "",
        f"{'Path':<28}{'farm8':>8}{'mix16':>8}{'ehp26':>8}{'fit':>7}",
        "-" * 57,
    ]
    for path, farm, mix, ehp in ranked:
        fit = composite((path, farm, mix, ehp))
        fit_s = f"{fit:7.2f}" if fit >= 0 else "   skip"
        lines.append(f"{path.name:<26}{farm:8.2f}{mix:8.0f}{ehp:8.0f}{fit_s}")

    lines += ["", "First item ~8:00 (the farm check)"]
    for path, farm, mix, ehp in ranked:
        f = fight_at(path, 8)
        lines.append(
            f"  {path.name:<26} wave {wave_frac(path, 8):.0%}  "
            f"[{', '.join(f.items)}]"
        )
    lines += ["", "Two-item ~16:00 (the 1v1 check)"]
    for path, farm, mix, ehp in ranked:
        f = fight_at(path, 16)
        lines.append(
            f"  {path.name:<26} mix {f.mix:5.0f}  ehp {f.ehp:5.0f}  "
            f"[{', '.join(f.items)}]"
        )
    lines.append("")
    for path, farm, mix, ehp in ranked:
        lines.append(f"{path.name}: {path.note}")
        lines.append("")

    ours_n, cn_n = winner.name, cn_path.name
    lines += [
        "Vs China 62.3% WR (Heartsteel → Sunfire → Thornmail → Twinguard)",
        "Source: wrchina.gg patch 7.3, stats 2026-09-26. 25% of CN Shen games.",
        f"  Ours  8:00  {', '.join(ours_a['items8'])}",
        f"  CN    8:00  {', '.join(cn_a['items8'])}",
        f"  Ours 16:00  {', '.join(ours_a['items16'])}",
        f"  CN   16:00  {', '.join(cn_a['items16'])}",
        f"  Ours 26:00  {', '.join(ours_a['items26'])}",
        f"  CN   26:00  {', '.join(cn_a['items26'])}  HS stacks {cn_a['hs_stacks']:.0f} HP",
        "",
        f"{'Aspect':<22}{ours_n:<28}{cn_n:<16}{'edge':>8}",
        "-" * 74,
        f"{'Lane shove 8:00':<22}{ours_a['lane_wave']:<28.0%}{cn_a['lane_wave']:<16.0%}"
        f"{pick_side(ours_a['lane_wave'], cn_a['lane_wave'], 'ours', 'CN'):>8}",
        f"{'Lane 3s trade dmg':<22}{ours_a['lane_short_mix']:<28.0f}{cn_a['lane_short_mix']:<16.0f}"
        f"{pick_side(ours_a['lane_short_mix'], cn_a['lane_short_mix'], 'ours', 'CN'):>8}",
        f"{'Lane 3s HP':<22}{ours_a['lane_hp']:<28.0f}{cn_a['lane_hp']:<16.0f}"
        f"{pick_side(ours_a['lane_hp'], cn_a['lane_hp'], 'ours', 'CN'):>8}",
        f"{'Solo 1v1 dmg 16:00':<22}{ours_a['solo_mix']:<28.0f}{cn_a['solo_mix']:<16.0f}"
        f"{pick_side(ours_a['solo_mix'], cn_a['solo_mix'], 'ours', 'CN'):>8}",
        f"{'Solo 1v1 ehp 16:00':<22}{ours_a['solo_ehp']:<28.0f}{cn_a['solo_ehp']:<16.0f}"
        f"{pick_side(ours_a['solo_ehp'], cn_a['solo_ehp'], 'ours', 'CN'):>8}",
        f"{'Solo 1v1 strength':<22}{ours_a['solo_str']:<28.0f}{cn_a['solo_str']:<16.0f}"
        f"{pick_side(ours_a['solo_str'], cn_a['solo_str'], 'ours', 'CN'):>8}",
        f"{'Teamfight AoE 26:00':<22}{ours_a['tf_aoe']:<28.0f}{cn_a['tf_aoe']:<16.0f}"
        f"{pick_side(ours_a['tf_aoe'], cn_a['tf_aoe'], 'ours', 'CN'):>8}",
        f"{'Teamfight tank ehp':<22}{ours_a['tf_ehp']:<28.0f}{cn_a['tf_ehp']:<16.0f}"
        f"{pick_side(ours_a['tf_ehp'], cn_a['tf_ehp'], 'ours', 'CN'):>8}",
        f"{'R ally shield 26:00':<22}{ours_a['r_shield']:<28.0f}{cn_a['r_shield']:<16.0f}"
        f"{pick_side(ours_a['r_shield'], cn_a['r_shield'], 'ours', 'CN'):>8}",
        f"{'1v9 split dmg 26:00':<22}{ours_a['split_mix']:<28.0f}{cn_a['split_mix']:<16.0f}"
        f"{pick_side(ours_a['split_mix'], cn_a['split_mix'], 'ours', 'CN'):>8}",
        f"{'1v9 split ehp 26:00':<22}{ours_a['split_ehp']:<28.0f}{cn_a['split_ehp']:<16.0f}"
        f"{pick_side(ours_a['split_ehp'], cn_a['split_ehp'], 'ours', 'CN'):>8}",
        f"{'Anti-heal (Thorn)':<22}{'no':<28}{'yes':<16}{'CN':>8}",
        f"{'Ranked WR (CN)':<22}{'(untracked)':<28}{'62.3%':<16}{'CN':>8}",
        "",
        "62% WR is the global-tank job: hold the side, R, peel, Thornmail.",
        "This build is the farm / 1v1 / 1v9 job. Different win condition.",
        "",
    ]

    text = "\n".join(lines)
    payload = {
        "patch": PATCH,
        "constraint": "1st farm, 2nd 1v1, rest tank; no Heartsteel first",
        "winner": winner.name,
        "buy_order": ["Ruby Crystal", "Plated Steelcaps"] + winner.legendaries,
        "cn_62_wr": {
            "source": "wrchina.gg patch 7.3 2026-09-26",
            "core": cn_path.legendaries,
            "wr": 0.623,
            "use": 0.253,
        },
        "aspects": {"ours": ours_a, "cn_62_wr": cn_a},
        "scores": [
            {
                "path": p.name,
                "farm8": round(farm, 3),
                "mix16": round(mix),
                "ehp26": round(ehp),
                "fit": None if composite((p, farm, mix, ehp)) < 0 else round(composite((p, farm, mix, ehp)), 3),
            }
            for p, farm, mix, ehp in ranked
        ],
        "snapshots": snapshots,
    }
    (OUT_DIR / "report.txt").write_text(text + "\n", encoding="utf-8")
    (OUT_DIR / "results.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )
    print(text)


if __name__ == "__main__":
    main()
