#!/usr/bin/env python3
"""
Wild Rift Patch 7.3 — which build/playstyles gained the most?

Compare a 7.2-ish kit+item snapshot vs 7.3 on the same 8s combat window.
Rank by average extra damage (post − pre) at 12 / 16 / 20 minutes.

7.3 thesis: split Magnetic Blaster's all-in-one power into distinct jobs
(crit vs on-hit vs range vs ult-burst), raise base crit to 200%, and
give several kits explicit crit or on-hit identities.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Tuple
import json

GAME_MINUTES = 20
FIGHT_SECONDS = 8.0
SNAPSHOTS = (12, 16, 20)


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
    table = {
        1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7, 7: 8, 8: 8,
        9: 9, 10: 10, 11: 11, 12: 11, 13: 12, 14: 12,
        15: 13, 16: 13, 17: 14, 18: 14, 19: 15, 20: 15,
    }
    return table.get(m, min(15, 1 + m))


def basic_rank(level: int) -> int:
    if level >= 9:
        return 4
    if level >= 6:
        return 3
    if level >= 3:
        return 2
    return 1


def ult_rank(level: int) -> int:
    if level >= 13:
        return 3
    if level >= 9:
        return 2
    if level >= 5:
        return 1
    return 0


def mit(amount: float, resist: float, pct_pen: float = 0.0, flat: float = 0.0) -> float:
    eff = max(0.0, resist * (1.0 - pct_pen) - flat)
    return amount * 100.0 / (100.0 + eff)


def squish(m: int) -> Tuple[float, float, float]:
    lv = level_at_minute(m)
    hp = 600 + 90 * lv + 18 * m
    armor = 32 + 2.0 * lv + 1.5 * max(0, m - 10)
    mr = 32 + 1.4 * lv + 1.2 * max(0, m - 10)
    return hp, armor, mr


def bruiser(m: int) -> Tuple[float, float, float]:
    lv = level_at_minute(m)
    hp = 680 + 100 * lv + 40 * m
    armor = 40 + 2.8 * lv + 4 * max(0, m - 8)
    mr = 36 + 1.8 * lv + 3 * max(0, m - 8)
    return hp, armor, mr


def tank(m: int) -> Tuple[float, float, float]:
    lv = level_at_minute(m)
    hp = 750 + 110 * lv + 70 * m
    armor = 45 + 3.2 * lv + 8 * max(0, m - 8)
    mr = 40 + 2.2 * lv + 6 * max(0, m - 8)
    return hp, armor, mr


def legendaries(gold: int, first: int, second: int, third: int, boots: int = 1000) -> int:
    """How many finished legendaries a farmer can afford (boots reserved)."""
    pool = gold - boots
    n = 0
    for cost in (first, second, third):
        if pool >= cost:
            pool -= cost
            n += 1
        else:
            break
    return n


def crit_auto(ad: float, crit_rate: float, crit_dmg: float) -> float:
    return ad * (1.0 + crit_rate * (crit_dmg - 1.0))


def ability_crit_mult(crit_rate: float, crit_dmg: float, ratio: float = 0.40) -> float:
    """7.3 pattern: (1 + crit_rate * ratio + (crit_dmg-2) * ratio * crit_rate)."""
    return 1.0 + crit_rate * ratio + max(0.0, crit_dmg - 2.0) * ratio * crit_rate


# ---------------------------------------------------------------------------
# Shared 7.2 vs 7.3 item snapshots (boots already stripped out of gold)
# ---------------------------------------------------------------------------


@dataclass
class Loadout:
    ad: float
    ap: float
    as_pct: float
    crit: float
    crit_dmg: float
    onhit_m: float
    pct_pen: float
    flat_mpen: float
    items: List[str]
    shiv: bool = False
    guinsoo: bool = False
    kraken: bool = False
    fiendhunter: bool = False
    stormrazor: bool = False
    rfc: bool = False
    yuntal: bool = False
    nashor: bool = False
    magnetic: bool = False
    ie: bool = False


def adc_base(champ_ad: float, champ_as: float, lv: int, ad_g: float, as_g: float, bonus0: float) -> Tuple[float, float]:
    ad = champ_ad + ad_g * (lv - 1)
    as_pct = bonus0 + as_g * (lv - 1)
    return ad, as_pct


# --- builders ---

def pre_onhit(gold: int, ad0: float, as0: float) -> Loadout:
    """7.2 on-hit: BotRK + Rageblade (no AD/AP, no crit) + Terminus 3300."""
    n = legendaries(gold, 3100, 3100, 3300)
    ad, ap, asp, onhit, items = ad0, 0.0, as0 + 0.35, 0.0, ["Berserker's"]
    flags = dict(guinsoo=False)
    if n >= 1:
        ad += 40
        asp += 0.35
        onhit += 0.0  # BotRK is %HP, applied in fight
        items.append("Blade of the Ruined King")
    if n >= 2:
        asp += 0.25
        onhit += 30
        flags["guinsoo"] = True
        items.append("Guinsoo's Rageblade")
    if n >= 3:
        ad += 40
        asp += 0.30
        onhit += 30
        items.append("Terminus")
    return Loadout(ad, ap, asp, 0.0, 1.75, onhit, 0.10 if n >= 3 else 0.0, 0.0, items, **flags)


def post_shiv_onhit(gold: int, ad0: float, as0: float, ap_boots: bool = False, third: str = "terminus") -> Loadout:
    """7.3 on-hit: Shiv + Rageblade (35 AD 30 AP) + Terminus or BotRK."""
    boots = 1200 if ap_boots else 1000
    third_cost = 3100 if third == "botrk" else 3000
    n = legendaries(gold, 3000, 3000, third_cost, boots=boots)
    ad, ap, asp = ad0, 0.0, as0 + (0.0 if ap_boots else 0.35)
    onhit = 0.0
    items = ["Boots of Mana"] if ap_boots else ["Berserker's"]
    if ap_boots:
        ap += 25
    flags = dict(shiv=False, guinsoo=False)
    if n >= 1:
        ad += 40
        ap += 40
        asp += 0.30
        flags["shiv"] = True
        items.append("Statikk Shiv")
    if n >= 2:
        ad += 35
        ap += 30
        onhit += 30
        flags["guinsoo"] = True
        items.append("Guinsoo's Rageblade")
    if n >= 3:
        if third == "botrk":
            ad += 40
            asp += 0.30
            items.append("Blade of the Ruined King")
        else:
            ad += 35
            asp += 0.35
            onhit += 30
            items.append("Terminus")
    return Loadout(ad, ap, asp, 0.0, 2.00, onhit, 0.10 if n >= 3 and third == "terminus" else 0.0, 8.0 if ap_boots else 0.0, items, **flags)


def post_nashor_onhit(gold: int, ad0: float, as0: float) -> Loadout:
    n = legendaries(gold, 3000, 2900, 3000, boots=1200)
    ad, ap, asp = ad0, 25.0, as0
    onhit = 0.0
    items = ["Boots of Mana"]
    flags = dict(shiv=False, nashor=False, guinsoo=False)
    if n >= 1:
        ad += 40
        ap += 40
        asp += 0.30
        flags["shiv"] = True
        items.append("Statikk Shiv")
    if n >= 2:
        ap += 80
        asp += 0.50
        onhit += 15 + 0.20 * ap
        flags["nashor"] = True
        items.append("Nashor's Tooth")
    if n >= 3:
        ad += 35
        ap += 30
        onhit += 30
        flags["guinsoo"] = True
        items.append("Guinsoo's Rageblade")
    return Loadout(ad, ap, asp, 0.0, 2.00, onhit, 0.0, 8.0, items, **flags)


def pre_nashor(gold: int, ad0: float, as0: float) -> Loadout:
    """7.2 Nashor was Adaptive Force, weaker AP identity. Model 45% AS, ~40 AP equivalent, 20 AH."""
    n = legendaries(gold, 2800, 3000, 3100, boots=1200)
    ad, ap, asp = ad0, 25.0, as0
    onhit = 0.0
    items = ["Boots of Mana"]
    flags = dict(nashor=False, guinsoo=False)
    if n >= 1:
        ap += 40
        asp += 0.45
        onhit += 15 + 0.10 * ap  # adaptive, not full AP
        flags["nashor"] = True
        items.append("Nashor's Tooth")
    if n >= 2:
        ap += 70
        items.append("Riftmaker")
    if n >= 3:
        asp += 0.25
        onhit += 30
        flags["guinsoo"] = True
        items.append("Guinsoo's Rageblade")
    return Loadout(ad, ap, asp, 0.0, 1.75, onhit, 0.0, 8.0, items, **flags)


def pre_crit(gold: int, ad0: float, as0: float) -> Loadout:
    """7.2 crit: Magnetic Blaster + IE + PD/RFC-ish zeal."""
    n = legendaries(gold, 2800, 3400, 2900)
    ad, asp, crit, cd = ad0, as0 + 0.35, 0.0, 1.75
    items = ["Berserker's"]
    flags = dict(magnetic=False, ie=False)
    if n >= 1:
        asp += 0.35
        crit += 0.25
        flags["magnetic"] = True
        items.append("Magnetic Blaster")
    if n >= 2:
        ad += 65
        crit += 0.25
        cd = 2.00
        flags["ie"] = True
        items.append("Infinity Edge")
    if n >= 3:
        asp += 0.35
        crit += 0.25
        items.append("Phantom Dancer")
    return Loadout(ad, 0.0, asp, min(1.0, crit), cd, 0.0, 0.0, 0.0, items, **flags)


def post_crit_ie(gold: int, ad0: float, as0: float, first: str = "yuntal") -> Loadout:
    """7.3 crit: Yun Tal or Stormrazor → IE → zeal/Hexoptics."""
    first_cost = 3100 if first == "yuntal" else 3000
    n = legendaries(gold, first_cost, 3400, 2900)
    ad, asp, crit, cd = ad0, as0 + 0.35, 0.0, 2.00
    items = ["Berserker's"]
    flags = dict(yuntal=False, stormrazor=False, ie=False, rfc=False)
    if n >= 1:
        if first == "yuntal":
            ad += 50
            asp += 0.25
            # ranged 0.2% crit per auto; ~70/110/150 autos by 12/16/20
            flags["yuntal"] = True
            items.append("Yun Tal Wildarrows")
        else:
            ad += 50
            asp += 0.20
            crit += 0.25
            flags["stormrazor"] = True
            items.append("Stormrazor")
    if n >= 2:
        ad += 75
        crit += 0.25
        cd = 2.30
        flags["ie"] = True
        items.append("Infinity Edge")
    if n >= 3:
        asp += 0.40
        crit += 0.25
        flags["rfc"] = True
        items.append("Rapid Firecannon")
    return Loadout(ad, 0.0, asp, min(1.0, crit), cd, 0.0, 0.0, 0.0, items, **flags)


def yuntal_crit(m: int) -> float:
    autos = 55 + 8 * max(0, m - 8)
    return min(0.25, autos * 0.002)


def post_fiendhunter(gold: int, ad0: float, as0: float) -> Loadout:
    n = legendaries(gold, 3100, 2650, 3400)
    ad, asp, crit, cd = ad0, as0 + 0.35, 0.0, 2.00
    items = ["Berserker's"]
    flags = dict(yuntal=False, fiendhunter=False, ie=False)
    if n >= 1:
        ad += 50
        asp += 0.25
        flags["yuntal"] = True
        items.append("Yun Tal Wildarrows")
    if n >= 2:
        asp += 0.45
        crit += 0.25
        flags["fiendhunter"] = True
        items.append("Fiendhunter Bolts")
    if n >= 3:
        ad += 75
        crit += 0.25
        cd = 2.30
        flags["ie"] = True
        items.append("Infinity Edge")
    return Loadout(ad, 0.0, asp, min(1.0, crit), cd, 0.0, 0.0, 0.0, items, **flags)


def post_vayne(gold: int, ad0: float, as0: float) -> Loadout:
    """Kraken / Rageblade / Terminus — duelist, not Shiv (W does not bounce)."""
    n = legendaries(gold, 2900, 3000, 3000)
    ad, ap, asp, onhit = ad0, 0.0, as0 + 0.35, 0.0
    items = ["Berserker's"]
    flags = dict(kraken=False, guinsoo=False)
    if n >= 1:
        ad += 45
        asp += 0.35
        flags["kraken"] = True
        items.append("Kraken Slayer")
    if n >= 2:
        ad += 35
        ap += 30
        onhit += 30
        flags["guinsoo"] = True
        items.append("Guinsoo's Rageblade")
    if n >= 3:
        ad += 35
        asp += 0.35
        onhit += 30
        items.append("Terminus")
    return Loadout(ad, ap, asp, 0.0, 2.00, onhit, 0.10 if n >= 3 else 0.0, 0.0, items, **flags)


def pre_vayne(gold: int, ad0: float, as0: float) -> Loadout:
    n = legendaries(gold, 2800, 3100, 3300)
    ad, asp, onhit = ad0, as0 + 0.35, 0.0
    items = ["Berserker's"]
    flags = dict(kraken=False, guinsoo=False)
    if n >= 1:
        ad += 40
        asp += 0.30
        flags["kraken"] = True
        items.append("Kraken Slayer")
    if n >= 2:
        asp += 0.25
        onhit += 30
        flags["guinsoo"] = True
        items.append("Guinsoo's Rageblade")
    if n >= 3:
        ad += 40
        asp += 0.30
        onhit += 30
        items.append("Terminus")
    return Loadout(ad, 0.0, asp, 0.0, 1.75, onhit, 0.10 if n >= 3 else 0.0, 0.0, items, **flags)


def post_ezreal(gold: int, ad0: float, as0: float) -> Loadout:
    n = legendaries(gold, 2900, 2800, 3000, boots=1200)
    ad, ap, asp = ad0, 25.0, as0
    items = ["Ionian / Mana"]
    if n >= 1:
        ad += 40
        items.append("Manamune")
    if n >= 2:
        ad += 50
        items.append("Essence Reaver")
    if n >= 3:
        ad += 40
        ap += 40
        asp += 0.30
        items.append("Statikk Shiv")
    return Loadout(ad, ap, asp, 0.25 if n >= 2 else 0.0, 2.00, 0.0, 0.0, 8.0, items)


def pre_ezreal(gold: int, ad0: float, as0: float) -> Loadout:
    n = legendaries(gold, 2700, 2800, 2800, boots=1200)
    ad, ap, asp = ad0, 25.0, as0
    items = ["Ionian / Mana"]
    if n >= 1:
        ad += 25
        items.append("Manamune")
    if n >= 2:
        ad += 35
        items.append("Essence Reaver")
    if n >= 3:
        items.append("Magnetic Blaster")
        asp += 0.35
    return Loadout(ad, ap, asp, 0.25 if n >= 3 else 0.0, 1.75, 0.0, 0.0, 8.0, items)


def attacks(as_base: float, as_ratio: float, as_pct: float, extra: float = 0.0) -> float:
    total = min(3.0, as_base + as_ratio * (as_pct + extra))
    return total * FIGHT_SECONDS * 0.85


def energized(n_attacks: float, bonus: bool) -> float:
    # +5 per auto on Shiv / Stormrazor / RFC / Magnetic
    return n_attacks / (4.2 if bonus else 5.5)


# ---------------------------------------------------------------------------
# Playstyle fights
# ---------------------------------------------------------------------------

FightFn = Callable[[int, str], Tuple[float, List[str], str]]


def varus_fight(m: int, patch: str) -> Tuple[float, List[str], str]:
    lv = level_at_minute(m)
    ad0, as0 = adc_base(54, 0.22, lv, 3.6, 0.032, 0.22)
    lo = post_shiv_onhit(gold_at_minute(m), ad0, as0) if patch == "73" else pre_onhit(gold_at_minute(m), ad0, as0)
    # Living Vengeance: 7.3 buff 20–30% AS (was 15–25%) + convert 15% of bonus AS → AD/AP
    as_extra = 0.25 if patch == "73" else 0.20
    convert = lo.as_pct * 0.15 * 100.0
    ad, ap = lo.ad + convert, lo.ap + convert
    n = attacks(0.658, 0.658, lo.as_pct, as_extra + (0.24 if lo.guinsoo else 0.0))
    hp_t, ar_t, mr_t = tank(m)
    hp_b, ar_b, mr_b = bruiser(m)
    hp_s, ar_s, mr_s = squish(m)
    clump = [(hp_t, ar_t, mr_t), (hp_b, ar_b, mr_b), (hp_s, ar_s, mr_s), (hp_s, ar_s, mr_s)]
    r = basic_rank(lv)
    w_hit = [0, 15, 25, 35, 45][r] + 0.35 * ap
    blight = [0, 0.030, 0.035, 0.040, 0.045][r] + 0.012 * ap / 100.0
    dmg = 0.0
    # primary autos
    primary = clump[0]
    auto = mit(ad, primary[1], lo.pct_pen)
    onh = mit(lo.onhit_m + w_hit, primary[2], lo.pct_pen, lo.flat_mpen)
    if "Blade of the Ruined King" in lo.items:
        onh += mit(0.07 * primary[0] * 0.80, primary[1], lo.pct_pen)
    dmg += n * (auto + onh * (1.33 if lo.guinsoo else 1.0))
    # Q detonate on primary (3 blight from autos)
    dmg += mit(blight * 3 * 1.25 * primary[0], primary[2], lo.pct_pen, lo.flat_mpen)
    if lo.shiv:
        en = energized(n, True)
        extra = min(3, len(clump) - 1)
        for tgt in clump[1:1 + extra]:
            dmg += en * (mit(60, tgt[2], lo.pct_pen, lo.flat_mpen) + mit(lo.onhit_m + w_hit, tgt[2], lo.pct_pen, lo.flat_mpen))
            dmg += mit(blight * en * 1.25 * tgt[0], tgt[2], lo.pct_pen, lo.flat_mpen)
        note = "blight-Shiv artillery: bounce stacks, one Q detonates the pit"
    else:
        note = "7.2 BotRK/Rageblade — no bounce, blight only on the person you auto"
    return dmg, lo.items, note


def kog_fight(m: int, patch: str) -> Tuple[float, List[str], str]:
    lv = level_at_minute(m)
    ad0, as0 = adc_base(54, 0.20, lv, 3.5, 0.027, 0.20)
    lo = post_shiv_onhit(gold_at_minute(m), ad0, as0, third="botrk") if patch == "73" else pre_onhit(gold_at_minute(m), ad0, as0)
    n = attacks(0.665, 0.665, lo.as_pct, [0, 0.05, 0.10, 0.15, 0.20][basic_rank(lv)] + (0.24 if lo.guinsoo else 0.0))
    hp_t, ar_t, mr_t = tank(m)
    hp_b, ar_b, mr_b = bruiser(m)
    hp_s, ar_s, mr_s = squish(m)
    clump = [(hp_t, ar_t, mr_t), (hp_b, ar_b, mr_b), (hp_s, ar_s, mr_s)]
    w = [0, 0.015, 0.025, 0.035, 0.045][basic_rank(lv)] + 0.015 * lo.ap / 100.0
    dmg = 0.0
    p = clump[0]
    auto = mit(lo.ad, p[1], lo.pct_pen)
    onh = mit(lo.onhit_m + w * p[0], p[2], lo.pct_pen, lo.flat_mpen)
    botrk = "Blade of the Ruined King" in lo.items
    if botrk:
        onh += mit(0.07 * p[0] * 0.80, p[1], lo.pct_pen)
    dmg += n * (auto + onh * (1.33 if lo.guinsoo else 1.0))
    if lo.shiv:
        en = energized(n, True)
        for tgt in clump[1:]:
            bounced = lo.onhit_m + w * tgt[0]
            if botrk:
                bounced_phys = 0.07 * tgt[0] * 0.75
            else:
                bounced_phys = 0.0
            dmg += en * (
                mit(60, tgt[2], lo.pct_pen)
                + mit(bounced, tgt[2], lo.pct_pen)
                + mit(bounced_phys, tgt[1], lo.pct_pen)
            )
        note = "Bio-Arcane + BotRK bounce: %HP copied onto the pit"
    else:
        note = "7.2 single-target barrage — W never leaves the tank"
    return dmg, lo.items, note


def kalista_fight(m: int, patch: str) -> Tuple[float, List[str], str]:
    lv = level_at_minute(m)
    ad0, as0 = adc_base(54, 0.205, lv, 4.5, 0.032, 0.205)
    lo = post_shiv_onhit(gold_at_minute(m), ad0, as0) if patch == "73" else pre_onhit(gold_at_minute(m), ad0, as0)
    n = attacks(0.694, 0.694, lo.as_pct, 0.24 if lo.guinsoo else 0.0)
    hp_t, ar_t, _ = tank(m)
    hp_b, ar_b, _ = bruiser(m)
    hp_s, ar_s, _ = squish(m)
    clump = [(hp_t, ar_t), (hp_b, ar_b), (hp_s, ar_s)]
    r = basic_rank(lv)
    base = [0, 30, 45, 60, 75][r] + 0.70 * lo.ad
    extra = [0, 12, 22, 32, 42][r] + [0, 0.36, 0.43, 0.50, 0.57][r] * lo.ad
    dmg = 0.0
    p = clump[0]
    auto = mit(lo.ad, p[1], lo.pct_pen)
    onh = mit(lo.onhit_m, 40.0, lo.pct_pen)
    dmg += n * (auto + onh * (1.33 if lo.guinsoo else 1.0))
    spears_p = max(1, int(n))
    dmg += mit(base + extra * (spears_p - 1), p[1], lo.pct_pen)
    if lo.shiv:
        en = energized(n, True)
        for tgt in clump[1:]:
            dmg += en * (mit(60, 40.0) + mit(lo.onhit_m, 40.0))
            sp = max(1, int(round(en)))
            dmg += mit(base + extra * (sp - 1), tgt[1], lo.pct_pen)
        note = "Rend spears bounce; one E rips the clump"
    else:
        note = "7.2 Rend only on who you jumped"
    return dmg, lo.items, note


def teemo_fight(m: int, patch: str) -> Tuple[float, List[str], str]:
    lv = level_at_minute(m)
    ad0, as0 = adc_base(52, 0.125, lv, 3.6, 0.022, 0.125)
    lo = post_nashor_onhit(gold_at_minute(m), ad0, as0) if patch == "73" else pre_nashor(gold_at_minute(m), ad0, as0)
    n = attacks(0.690, 0.690, lo.as_pct, 0.24 if lo.guinsoo else 0.0)
    hp_b, ar_b, mr_b = bruiser(m)
    hp_s, _, mr_s = squish(m)
    onhit = 8 + (36 - 8) * (lv - 1) / 14 + 0.20 * lo.ap + lo.onhit_m
    poison = (11 + (53 - 11) * (lv - 1) / 14 + 0.09 * lo.ap) * 4
    dmg = n * (mit(lo.ad, ar_b) + mit(onhit, mr_b, 0.0, lo.flat_mpen))
    dmg += mit(poison, mr_b, 0.0, lo.flat_mpen)
    if lo.shiv:
        en = energized(n, True)
        for _ in range(2):
            dmg += en * (mit(60, mr_s, 0.0, lo.flat_mpen) + mit(onhit, mr_s, 0.0, lo.flat_mpen))
            dmg += mit(poison, mr_s, 0.0, lo.flat_mpen)
        note = "Nashor is 80 AP again; Shiv paints poison on the side lanes"
    else:
        note = "7.2 adaptive Nashor — weaker AP, no bounce"
    return dmg, lo.items, note


def twitch_fight(m: int, patch: str) -> Tuple[float, List[str], str]:
    lv = level_at_minute(m)
    ad_g = 4.0 if patch == "73" else 4.5
    base_ad = 58 if patch == "73" else 54
    ad0, as0 = adc_base(base_ad, 0.20, lv, ad_g, 0.030, 0.20)
    if patch == "73":
        lo = post_fiendhunter(gold_at_minute(m), ad0, as0)
        if lo.yuntal:
            lo.crit += yuntal_crit(m)
            lo.crit = min(1.0, lo.crit)
        ambush = [0.35, 0.35, 0.40, 0.45, 0.50][min(4, (lv - 1) // 4)]
        extra_as = ambush
        if lo.fiendhunter:
            extra_as += 0.18  # 3 attacks at +50% AS inside the window
        note = "leave camouflage → Ambush AS → R + Fiendhunter 3-crit window → E"
    else:
        lo = pre_crit(gold_at_minute(m), ad0, as0)
        extra_as = 0.40  # old max-venom AS
        note = "7.2 max-stack AS + Magnetic — no stealth burst identity"
    n = attacks(0.679, 0.679, lo.as_pct, extra_as)
    hp, ar, mr = bruiser(m)
    hp2, ar2, mr2 = squish(m)
    auto = crit_auto(lo.ad, lo.crit, lo.crit_dmg)
    if patch == "73" and lo.fiendhunter:
        # 3 guaranteed crits at 80% of normal crit dmg
        auto = (auto * (n - 3) + 3 * lo.ad * (1 + 0.80 * (lo.crit_dmg - 1))) / max(n, 1)
    dmg = n * mit(auto, ar)
    # Spray and Pray exists on both patches; 7.3 missiles are slightly faster
    splash = 0.45 if patch == "73" else 0.40
    dmg += splash * n * mit(auto, ar2)
    # E
    r = basic_rank(lv)
    stacks = 5
    if patch == "73":
        e = [0, 30, 40, 50, 60][r] + stacks * ([0, 20, 25, 30, 35][r] + 0.35 * (lo.ad - base_ad) + 0.35 * lo.ap)
        dmg += mit(e * 0.7, ar) + mit(e * 0.3, mr)
        # splash E on a second poisoned body
        dmg += 0.55 * (mit(e * 0.7, ar2) + mit(e * 0.3, mr2))
    else:
        e = [0, 25, 35, 45, 55][r] + stacks * ([0, 20, 25, 30, 35][r] + 0.42 * (lo.ad - base_ad) + 0.18 * lo.ap)
        dmg += mit(e, ar)
    if lo.shiv or lo.magnetic:
        dmg += energized(n, True) * mit(80 if lo.magnetic else 60, mr)
    return dmg, lo.items, note


def vayne_fight(m: int, patch: str) -> Tuple[float, List[str], str]:
    lv = level_at_minute(m)
    base_ad = 60 if patch == "73" else 54
    ad_g = 3.0
    ad0, as0 = adc_base(base_ad, 0.205, lv, ad_g, 0.027, 0.205)
    lo = post_vayne(gold_at_minute(m), ad0, as0) if patch == "73" else pre_vayne(gold_at_minute(m), ad0, as0)
    r = basic_rank(lv)
    ur = ult_rank(lv)
    if patch == "73":
        q = [0, 0.50, 0.60, 0.70, 0.80][r]
        w = [0, 0.06, 0.07, 0.08, 0.09][r]
        ult_ad = [0, 30, 40, 50][ur]
        w_as = [0, 0.10, 0.15, 0.20, 0.25][r]
        note = "Tumble 50–80% AD, W 6–9% true, R +30–50 AD — duel the bruiser"
    else:
        q = [0, 0.35, 0.45, 0.55, 0.65][r]
        w = [0, 0.02, 0.05, 0.08, 0.11][r]
        ult_ad = [0, 15, 25, 35][ur]
        w_as = [0, 0.10, 0.15, 0.20, 0.25][r]
        note = "7.2 weaker Tumble / late-only Silver Bolts / tiny R AD"
    ad = lo.ad + ult_ad
    n = attacks(0.658, 0.625, lo.as_pct, w_as + (0.24 if lo.guinsoo else 0.0))
    hp, ar, mr = bruiser(m)
    auto = mit(ad, ar, lo.pct_pen)
    onh = mit(lo.onhit_m, mr, lo.pct_pen)
    tumbles = 3.0  # rank-4 Tumble CD is 2s; 8s window fits three resets
    w_procs = n / 3.0
    dmg = n * (auto + onh * (1.33 if lo.guinsoo else 1.0))
    dmg += tumbles * mit(q * ad, ar, lo.pct_pen)
    dmg += w_procs * (w * hp)  # true
    if lo.kraken:
        dmg += (n / 3.0) * mit(144 * 1.20, ar, lo.pct_pen)
    return dmg, lo.items, note


def caitlyn_fight(m: int, patch: str) -> Tuple[float, List[str], str]:
    lv = level_at_minute(m)
    if patch == "73":
        ad0, as0 = adc_base(60, 0.28, lv, 4.2, 0.04, 0.28)
        lo = post_crit_ie(gold_at_minute(m), ad0, as0, first="stormrazor")
        note = "Stormrazor lane → trap Headshot bonus → IE 230% Headshot / Ace"
    else:
        ad0, as0 = adc_base(54, 0.20, lv, 4.5, 0.03, 0.20)
        lo = pre_crit(gold_at_minute(m), ad0, as0)
        note = "7.2 Magnetic + 175% crit Headshot"
    n = attacks(0.625, 0.625, lo.as_pct)
    hp, ar, _ = squish(m)
    auto = crit_auto(lo.ad, lo.crit, lo.crit_dmg)
    dmg = n * mit(auto, ar)
    # 2 headshots in the window (passive + trap)
    if patch == "73":
        hs = (0.80 * lo.ad) + lo.ad * (lo.crit * 1.0 + max(0, lo.crit_dmg - 2) * lo.crit * 1.0)
        trap = [0, 40, 90, 140, 190][basic_rank(lv)] + 0.30 * (lo.ad - 60 - 4.2 * (lv - 1))
        trap = max(0, trap)
        dmg += 2 * mit(hs, ar) + mit(trap, ar)
        # Ace in the Hole once if ult up and window is a pick — 40% duty
        ur = ult_rank(lv)
        ace = [0, 250, 450, 650][ur] + 1.0 * (lo.ad - 60) + 0.20 * hp
        ace *= ability_crit_mult(lo.crit, lo.crit_dmg, 0.30)
        dmg += 0.40 * mit(ace, ar)
        if lo.stormrazor:
            dmg += energized(n, True) * mit(120, 40)
    else:
        hs = (0.85 * lo.ad) + 200 * lo.crit * 0.01 * lo.ad
        dmg += 2 * mit(hs, ar)
        ur = ult_rank(lv)
        ace = [0, 200, 375, 550][ur] + 2.0 * (lo.ad - 54) + 0.20 * hp
        dmg += 0.40 * mit(ace, ar)
        if lo.magnetic:
            dmg += energized(n, True) * mit(80, 40)
    return dmg, lo.items, note


def lucian_fight(m: int, patch: str) -> Tuple[float, List[str], str]:
    lv = level_at_minute(m)
    base = 60 if patch == "73" else 58
    ad_g = 3.5 if patch == "73" else 4.0
    ad0, as0 = adc_base(base, 0.20, lv, ad_g, 0.030, 0.20)
    lo = post_crit_ie(gold_at_minute(m), ad0, as0, first="stormrazor") if patch == "73" else pre_crit(gold_at_minute(m), ad0, as0)
    n = attacks(0.638, 0.638, lo.as_pct)
    # Lightslinger double-shot
    second = [0, 0.40, 0.50, 0.60, 0.60][min(4, basic_rank(lv))] if patch == "73" else [0, 0.35, 0.50, 0.65, 0.65][min(4, basic_rank(lv))]
    hp, ar, _ = squish(m)
    auto = crit_auto(lo.ad, lo.crit, lo.crit_dmg)
    dmg = n * mit(auto * (1 + second), ar)
    ur = ult_rank(lv)
    if patch == "73":
        bullets = 20 + 20 * lo.crit + max(0, lo.crit_dmg - 2) * 20 * lo.crit
        per = [0, 20, 25, 30][ur] + 0.25 * lo.ad + 0.15 * lo.ap
        note = "The Culling scales with crit rate + IE capstone"
    else:
        bullets = [0, 22, 26, 30][ur]
        per = [0, 20, 35, 50][ur] + 0.25 * lo.ad + 0.10 * lo.ap
        note = "7.2 Culling is a fixed bullet count"
    dmg += 0.70 * bullets * mit(per, ar)  # 70% of R lands in the window
    if lo.stormrazor:
        dmg += energized(n, True) * mit(120, 40)
    if lo.magnetic:
        dmg += energized(n, True) * mit(80, 40)
    return dmg, lo.items, note


def xayah_fight(m: int, patch: str) -> Tuple[float, List[str], str]:
    lv = level_at_minute(m)
    ad0, as0 = adc_base(60 if patch == "73" else 54, 0.22, lv, 4.2 if patch == "73" else 5.0, 0.03, 0.22)
    lo = post_crit_ie(gold_at_minute(m), ad0, as0, first="yuntal") if patch == "73" else pre_crit(gold_at_minute(m), ad0, as0)
    if lo.yuntal:
        lo.crit += yuntal_crit(m)
        lo.crit = min(1.0, lo.crit)
    n = attacks(0.658, 0.658, lo.as_pct, [0, 0.40, 0.45, 0.50, 0.55][basic_rank(lv)] if patch == "73" else [0, 0.45, 0.50, 0.55, 0.60][basic_rank(lv)])
    hp, ar, _ = bruiser(m)
    auto = crit_auto(lo.ad, lo.crit, lo.crit_dmg)
    dmg = n * mit(auto, ar)
    r = basic_rank(lv)
    if patch == "73":
        e = ([0, 70, 80, 90, 100][r] + 0.50 * (lo.ad - 60)) * ability_crit_mult(lo.crit, lo.crit_dmg, 0.50)
        note = "Bladecaller now scales with crit rate and IE damage"
    else:
        e = [0, 60, 70, 80, 90][r] + 0.90 * (lo.ad - 54)
        note = "7.2 Bladecaller ignores crit"
    dmg += mit(e, ar)
    # feathers from autos (~1 per auto, recall hits 5)
    dmg += 5 * mit(auto * (0.25 if patch == "73" else 0.20), ar)
    return dmg, lo.items, note


def jinx_fight(m: int, patch: str) -> Tuple[float, List[str], str]:
    lv = level_at_minute(m)
    ad_g = 4.0 if patch == "73" else 4.5
    ad0, as0 = adc_base(58, 0.17, lv, ad_g, 0.017, 0.17)
    lo = post_crit_ie(gold_at_minute(m), ad0, as0, first="yuntal") if patch == "73" else pre_crit(gold_at_minute(m), ad0, as0)
    if lo.yuntal:
        lo.crit += yuntal_crit(m)
        lo.crit = min(1.0, lo.crit)
    n = attacks(0.625, 0.625, lo.as_pct, 0.30)  # rockets + pow-pow frenzy slice
    hp, ar, _ = bruiser(m)
    hp2, ar2, _ = squish(m)
    auto = crit_auto(lo.ad, lo.crit, lo.crit_dmg)
    # rockets splash
    dmg = n * mit(auto, ar) + 0.45 * n * mit(auto, ar2)
    if patch == "73":
        note = "200% crit + Yun Tal stacking + IE 230% — rockets still crit"
    else:
        note = "7.2 Magnetic rockets at 175% crit"
    if lo.magnetic:
        dmg += energized(n, True) * mit(80, 40)
    return dmg, lo.items, note


def trist_fight(m: int, patch: str) -> Tuple[float, List[str], str]:
    lv = level_at_minute(m)
    ad0, as0 = adc_base(60 if patch == "73" else 54, 0.20, lv, 5.0 if patch == "73" else 6.0, 0.03, 0.20)
    lo = post_crit_ie(gold_at_minute(m), ad0, as0, first="stormrazor") if patch == "73" else pre_crit(gold_at_minute(m), ad0, as0)
    n = attacks(0.656, 0.656, lo.as_pct)
    hp, ar, mr = bruiser(m)
    auto = crit_auto(lo.ad, lo.crit, lo.crit_dmg)
    dmg = n * mit(auto, ar)
    r = basic_rank(lv)
    if patch == "73":
        bomb = ([0, 80, 100, 120, 140][r] + 1.00 * (lo.ad - 60) + 0.50 * lo.ap) * ability_crit_mult(lo.crit, lo.crit_dmg, 0.40)
        note = "Explosive Charge active now crit-scales; jump-bomb pick"
    else:
        bomb = [0, 50, 75, 100, 125][r] + [0, 0.75, 1.10, 1.45, 1.80][r] * (lo.ad - 54) + 0.50 * lo.ap
        note = "7.2 bomb is raw AD, Magnetic for the jump"
    dmg += mit(bomb, ar)
    if lo.stormrazor:
        dmg += energized(n, True) * mit(120, 40)
    if lo.magnetic:
        dmg += energized(n, True) * mit(80, 40)
    return dmg, lo.items, note


def zeri_fight(m: int, patch: str) -> Tuple[float, List[str], str]:
    lv = level_at_minute(m)
    ad0, as0 = adc_base(58, 0.20, lv, 3.5, 0.03, 0.20)
    if patch == "73":
        lo = post_fiendhunter(gold_at_minute(m), ad0, as0)
        if lo.yuntal:
            lo.crit += yuntal_crit(m)
            lo.crit = min(1.0, lo.crit)
        # Living Battery: bonus AS → AD at 60% (was 50%)
        lo.ad += lo.as_pct * 0.60 * 100.0
        note = "R Overload 2.5s/7.5s + Fiendhunter 3-crit burst"
        r_uptime = 2.5 / FIGHT_SECONDS
    else:
        lo = pre_crit(gold_at_minute(m), ad0, as0)
        lo.ad += lo.as_pct * 0.50 * 100.0
        note = "7.2 Magnetic Zeri, 1.5s Overload"
        r_uptime = 1.5 / FIGHT_SECONDS
    n = attacks(0.658, 0.658, lo.as_pct)
    hp, ar, _ = squish(m)
    auto = crit_auto(lo.ad, lo.crit, lo.crit_dmg)
    dmg = n * mit(auto, ar)
    # Q burst fire
    r = basic_rank(lv)
    if patch == "73":
        q = [0, 70, 100, 130, 160][r] + 0.80 * (lo.ad - 58)
    else:
        q = [0, 35, 60, 85, 110][r] + [0, 0.55, 0.70, 0.85, 1.00][r] * lo.ad
    dmg += 3 * mit(q, ar)
    dmg += r_uptime * n * mit(auto * 0.30, ar)  # overload lightning
    return dmg, lo.items, note


def kaisa_fight(m: int, patch: str) -> Tuple[float, List[str], str]:
    lv = level_at_minute(m)
    base = 59 if patch == "73" else 62
    ad0, as0 = adc_base(base, 0.125, lv, 3.5, 0.032, 0.125)
    lo = post_shiv_onhit(gold_at_minute(m), ad0, as0) if patch == "73" else pre_onhit(gold_at_minute(m), ad0, as0)
    n = attacks(0.644, 0.644, lo.as_pct, 0.24 if lo.guinsoo else 0.0)
    hp, ar, mr = bruiser(m)
    dmg = 0.0
    auto = mit(lo.ad, ar, lo.pct_pen)
    for i in range(int(n)):
        stacks = min(4, i)
        if patch == "73":
            plasma = 4 + 1 * lv + 0.12 * lo.ap + stacks * (1 + 0.2 * lv + 0.02 * lo.ap)
            pop = (0.15 + 0.05 * lo.ap / 100.0) * hp * 0.40 if (i + 1) % 5 == 0 else 0.0
        else:
            plasma = 4.5 + 0.5 * lv + 0.15 * lo.ap
            pop = (0.15 + 0.025 * lo.ap / 100.0) * hp * 0.40 if (i + 1) % 5 == 0 else 0.0
        dmg += auto + mit(lo.onhit_m + plasma, mr, lo.pct_pen) + mit(pop, mr, lo.pct_pen)
    if lo.shiv:
        en = energized(n, True)
        dmg += en * 2 * (mit(60, mr) + mit(lo.onhit_m + 4 + lv, mr, lo.pct_pen))
        note = "7.3 Plasma AP ratios + Rageblade 35/30, but bounce never 5-pops"
    else:
        note = "7.2 Terminus/Rageblade hybrid, Magnetic gone later"
    return dmg, lo.items, note


def kayle_fight(m: int, patch: str) -> Tuple[float, List[str], str]:
    lv = level_at_minute(m)
    ad0, as0 = adc_base(54, 0.133, lv, 3.0, 0.022, 0.133)
    lo = post_nashor_onhit(gold_at_minute(m), ad0, as0) if patch == "73" else pre_nashor(gold_at_minute(m), ad0, as0)
    cap = 0.30 + 0.05 * lo.ap / 100.0
    n = attacks(0.667, 0.667, lo.as_pct, cap)
    hp, ar, mr = bruiser(m)
    r = basic_rank(lv)
    e = [0, 8, 11, 14, 17][r] + 0.05 * (lo.ad - 54) + 0.15 * lo.ap
    dmg = n * (mit(lo.ad, ar) + mit(lo.onhit_m + e, mr, 0.0, lo.flat_mpen))
    if lv >= 9:
        dmg += n * 1.4 * mit(e, mr, 0.0, lo.flat_mpen)  # Aflame waves
    if lo.shiv:
        en = energized(n, True)
        dmg += en * 2 * (mit(60, mr) + mit(lo.onhit_m, mr, 0.0, lo.flat_mpen))
        note = "Nashor 80 AP + Shiv 40/40/30% is her stat dream; waves already AoE"
    else:
        note = "7.2 adaptive Nashor"
    return dmg, lo.items, note


def ezreal_fight(m: int, patch: str) -> Tuple[float, List[str], str]:
    lv = level_at_minute(m)
    base = 60 if patch == "73" else 58
    ad0, as0 = adc_base(base, 0.20, lv, 3.5, 0.025, 0.20)
    lo = post_ezreal(gold_at_minute(m), ad0, as0) if patch == "73" else pre_ezreal(gold_at_minute(m), ad0, as0)
    r = basic_rank(lv)
    # Q cadence: 7.3 CD 5.5–4s but refunds itself; 7.2 4.5–3s refund others
    q_cd = 4.4 if patch == "73" else 3.8
    q_casts = FIGHT_SECONDS / q_cd * 0.90
    q = [0, 25, 55, 85, 115][r] + 1.35 * lo.ad + 0.30 * lo.ap if patch == "73" else [0, 50, 85, 120, 155][r] + 1.35 * lo.ad + 0.30 * lo.ap
    hp, ar, _ = bruiser(m)
    mana = 500 + 700  # stacked tear
    sheen = 1.35 * (base + 3.5 * (lv - 1)) if patch == "73" and "Essence Reaver" in str(lo.items) else 1.20 * (base)
    muramana = 0.015 * mana if "Manamune" in lo.items else 0.0
    dmg = q_casts * mit(q + sheen + muramana * (0.035 / 0.015) * 0.3, ar)
    n = attacks(0.625, 0.625, lo.as_pct + 0.20)
    dmg += n * mit(lo.ad + muramana, ar)
    note = "Muramana no longer needs mana spend; Q damage/CD nerfed" if patch == "73" else "7.2 Tear spend + Magnetic"
    return dmg, lo.items, note


def jhin_fight(m: int, patch: str) -> Tuple[float, List[str], str]:
    lv = level_at_minute(m)
    ad_g = 5.0 if patch == "73" else 4.55
    base = 60 if patch == "73" else 58
    ad0, as0 = adc_base(base, 0.0, lv, ad_g, 0.0, 0.0)
    lo = post_crit_ie(gold_at_minute(m), ad0, as0, first="stormrazor") if patch == "73" else pre_crit(gold_at_minute(m), ad0, as0)
    # Whisper converts AS+crit to AD
    if patch == "73":
        conv = lo.as_pct * 0.30 + lo.crit * 0.40 + lv * 0.03
        crit_mod = 0.80
        note = "7.3 crit 200% but Whisper shots only deal 80% crit damage"
    else:
        conv = lo.as_pct * 0.30 + lo.crit * 0.45 + lv * 0.045
        crit_mod = 1.00
        note = "7.2 full crit conversion"
    ad = lo.ad * (1 + conv)
    # 4-shot cadence ~0.9 "attacks" weighted, 4th is big
    shots = 6.0  # ~1.5 cycles
    hp, ar, _ = squish(m)
    normal = crit_auto(ad, lo.crit, 1 + (lo.crit_dmg - 1) * crit_mod)
    fourth = ad * lo.crit_dmg * (1.0 if patch != "73" else 1.0)
    dmg = (shots * 0.75) * mit(normal, ar) + (shots * 0.25) * mit(fourth, ar)
    if lo.stormrazor:
        dmg += 1.5 * mit(120, 40)
    return dmg, lo.items, note


def ashe_fight(m: int, patch: str) -> Tuple[float, List[str], str]:
    lv = level_at_minute(m)
    ad0, as0 = adc_base(60 if patch == "73" else 58, 0.22, lv, 4.2 if patch == "73" else 2.65, 0.03, 0.22)
    lo = post_crit_ie(gold_at_minute(m), ad0, as0, first="yuntal") if patch == "73" else pre_crit(gold_at_minute(m), ad0, as0)
    if lo.yuntal:
        lo.crit += yuntal_crit(m)
        lo.crit = min(1.0, lo.crit)
    n = attacks(0.658, 0.658, lo.as_pct, 0.20)
    hp, ar, _ = bruiser(m)
    auto = crit_auto(lo.ad, lo.crit, lo.crit_dmg)
    if patch == "73":
        frost = auto * (lo.crit + max(0, lo.crit_dmg - 2) * lo.crit)
        note = "Frost bonus is now pure crit; Focus mana down — still a utility carry"
    else:
        frost = auto * (0.10 + lo.crit * (lo.crit_dmg - 1))
        note = "7.2 Frost 10% + crit"
    dmg = n * mit(auto + 0.15 * frost, ar)
    return dmg, lo.items, note


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


@dataclass
class Style:
    name: str
    champ: str
    playstyle: str
    job: str
    fight: FightFn


STYLES: List[Style] = [
    Style("Varus blight-Shiv", "Varus", "On-hit artillery", "Stack blight on the pit, Q detonate", varus_fight),
    Style("Kog'Maw barrage-Shiv", "Kog'Maw", "On-hit hypercarry", "W %HP copied onto the clump", kog_fight),
    Style("Kalista Rend-Shiv", "Kalista", "On-hit spear dump", "Bounce spears, one E rips", kalista_fight),
    Style("Teemo Nashor-Shiv", "Teemo", "AP on-hit poison", "Nashor 80 AP + poison bounce", teemo_fight),
    Style("Twitch stealth-Fiendhunter", "Twitch", "Stealth ult burst", "Camo → Ambush AS → R 3-crit window → E", twitch_fight),
    Style("Vayne silver-duelist", "Vayne", "On-hit duelist", "Tumble + Silver Bolts + Kraken, not Shiv", vayne_fight),
    Style("Caitlyn trap-Headshot", "Caitlyn", "Crit sniper", "Stormrazor lane, trap Headshot, IE Ace", caitlyn_fight),
    Style("Lucian Culling-crit", "Lucian", "Crit tempo", "Lane poke then R scales with IE", lucian_fight),
    Style("Xayah feather-crit", "Xayah", "Crit zone control", "Bladecaller now crit-scales", xayah_fight),
    Style("Jinx rocket-Yun Tal", "Jinx", "Crit hypercarry", "Yun Tal stack + 200%/230% rocket crits", jinx_fight),
    Style("Tristana jump-bomb", "Tristana", "Crit pick assassin", "E explosion scales with crit", trist_fight),
    Style("Zeri Fiendhunter-R", "Zeri", "Ult-window carry", "Longer Overload + Fiendhunter 3-crit", zeri_fight),
    Style("Kai'Sa hybrid on-hit", "Kai'Sa", "Hybrid on-hit", "Plasma AP buff + Rageblade 35/30", kaisa_fight),
    Style("Kayle Nashor-ascend", "Kayle", "AP on-hit scaler", "Nashor 80 AP + Shiv stats", kayle_fight),
    Style("Ezreal Muramana poke", "Ezreal", "Spellweaver ADC", "Tear no longer needs mana spend", ezreal_fight),
    Style("Jhin Whisper-crit", "Jhin", "Crit 4th-shot", "System crit up, Whisper crit down to 80%", jhin_fight),
    Style("Ashe Focus-crit", "Ashe", "Crit utility kiter", "Frost formula is crit, still utility", ashe_fight),
]


@dataclass
class Snap:
    minute: int
    pre: float
    post: float
    delta: float
    pre_items: List[str]
    post_items: List[str]
    note: str


def run_style(s: Style) -> List[Snap]:
    out = []
    for m in SNAPSHOTS:
        pre, pre_it, _ = s.fight(m, "72")
        post, post_it, note = s.fight(m, "73")
        out.append(Snap(m, pre, post, post - pre, pre_it, post_it, note))
    return out


def summarize(all_res: Dict[str, List[Snap]]) -> str:
    ranking = []
    for s in STYLES:
        snaps = all_res[s.name]
        avg = sum(x.delta for x in snaps) / len(snaps)
        d20 = snaps[-1].delta
        ranking.append((avg, d20, s, snaps))
    ranking.sort(key=lambda x: (x[0], x[1]), reverse=True)

    lines: List[str] = []
    a = lines.append
    a("=" * 78)
    a("WILD RIFT 7.3 — TOP BUILD / PLAYSTYLES (who gained the most)")
    a("Metric: 8s combat window  |  extra damage = 7.3 − 7.2 at 12/16/20")
    a("=" * 78)
    a("")
    a("WHAT 7.3 CHANGED")
    a("  • Base crit 175% → 200%, IE capstone 230% / 75 AD")
    a("  • Magnetic Blaster removed — power split into Stormrazor / RFC / Shiv")
    a("  • Shiv is on-hit bounce (40 AD / 40 AP / 30% AS)")
    a("  • Rageblade: 35 AD / 30 AP, no longer blocks crit")
    a("  • Nashor: dedicated 80 AP on-hit again")
    a("  • New: Yun Tal, Fiendhunter Bolts, Hexoptics C44, Stormrazor")
    a("  • Kits: Twitch stealth rework, Vayne/Caitlyn/Lucian/Xayah/Trist/Zeri crit hooks")
    a("")
    a("-" * 78)
    a("FULL RANKING  (avg extra damage in the 8s window)")
    a("-" * 78)
    a(f"  {'#':<3} {'Build / playstyle':<28} {'Δ12':>7} {'Δ16':>7} {'Δ20':>7} {'AvgΔ':>7}")
    for i, (avg, _, s, snaps) in enumerate(ranking, 1):
        d12, d16, d20 = snaps[0].delta, snaps[1].delta, snaps[2].delta
        a(f"  {i:<3} {s.name:<28} {d12:>7.0f} {d16:>7.0f} {d20:>7.0f} {avg:>7.0f}")

    top10 = ranking[:10]
    a("")
    a("-" * 78)
    a("TOP 10 — PLAYSTYLE AND WHY 7.3")
    a("-" * 78)
    for i, (avg, _, s, snaps) in enumerate(top10, 1):
        post = snaps[-1]
        a(f"  {i}. {s.name}  [{s.champ} · {s.playstyle}]")
        a(f"     Job: {s.job}")
        a(f"     Avg Δ {avg:.0f}   20:00  {post.pre:.0f} → {post.post:.0f}  ({post.delta:+.0f})")
        a(f"     7.3 build: {' › '.join(post.post_items)}")
        a(f"     {post.note}")
        a("")

    a("-" * 78)
    a("VERDICT")
    a("-" * 78)
    a("  Play 7.3 as one of these, in order of who gained the most:")
    for i, (_, _, s, _) in enumerate(top10, 1):
        a(f"    {i}) {s.name} — {s.playstyle.lower()}")
    a("")
    a("  Three lanes of 7.3, don't mix them:")
    a("  • ON-HIT CLUMP  (Shiv → Rageblade → Terminus/Nashor)")
    a("      Varus / Kog'Maw / Kalista / Teemo")
    a("  • CRIT SNIPER   (Stormrazor or Yun Tal → IE → RFC/Fiendhunter)")
    a("      Caitlyn / Lucian / Xayah / Jinx / Tristana / Twitch / Zeri")
    a("  • DUELIST       (Kraken → Rageblade → Terminus) — not Shiv")
    a("      Vayne")
    a("")
    a("  Traps:")
    a("  • Magnetic Blaster is gone. Crit ADCs who still buy 'the waveclear item'")
    a("    want Stormrazor (lane) or RFC (range), not Shiv.")
    a("  • Vayne Silver Bolts do not bounce. Shiv is a bait.")
    a("  • Jhin / Senna / Yasuo / Yone were compensated — they are not 7.3 winners.")
    a("  • Ezreal Q was nerfed; Muramana QoL does not cover it.")
    a("  • Kog'Maw Shiv is a late teamfight upgrade — 7.2 BotRK wins 12–16.")
    a("  • Vayne Tumble/R went up, rank-4 Silver Bolts 11% → 9%. Lane up, 3-item flat.")
    a("=" * 78)
    return "\n".join(lines)


def export_json(all_res: Dict[str, List[Snap]], ranking_meta: list, path: str) -> None:
    payload = {
        "meta": {
            "patch": "7.3",
            "game": "Wild Rift",
            "question": "Which build/playstyles benefit most in 7.3? Top 10.",
            "metric": "8s combat window extra damage (7.3 − 7.2) at 12/16/20",
        },
        "ranking": ranking_meta,
        "styles": {
            s.name: {
                "champion": s.champ,
                "playstyle": s.playstyle,
                "job": s.job,
                "snapshots": [
                    {
                        "minute": x.minute,
                        "pre": round(x.pre, 1),
                        "post": round(x.post, 1),
                        "delta": round(x.delta, 1),
                        "pre_items": x.pre_items,
                        "post_items": x.post_items,
                        "note": x.note,
                    }
                    for x in all_res[s.name]
                ],
            }
            for s in STYLES
        },
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)


def main() -> None:
    all_res = {s.name: run_style(s) for s in STYLES}
    ranking = []
    for s in STYLES:
        snaps = all_res[s.name]
        avg = sum(x.delta for x in snaps) / len(snaps)
        ranking.append({
            "name": s.name,
            "champion": s.champ,
            "playstyle": s.playstyle,
            "job": s.job,
            "avg_delta": round(avg, 1),
            "d12": round(snaps[0].delta, 1),
            "d16": round(snaps[1].delta, 1),
            "d20": round(snaps[2].delta, 1),
            "items_20": snaps[-1].post_items,
            "note": snaps[-1].note,
        })
    ranking.sort(key=lambda x: x["avg_delta"], reverse=True)
    report = summarize(all_res)
    print(report)
    out = "/workspace/wr-73-playstyles"
    with open(f"{out}/report.txt", "w", encoding="utf-8") as fh:
        fh.write(report + "\n")
    export_json(all_res, ranking, f"{out}/results.json")
    print(f"\nWrote {out}/report.txt and {out}/results.json")


if __name__ == "__main__":
    main()
