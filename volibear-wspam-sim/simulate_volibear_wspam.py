#!/usr/bin/env python3
"""
Wild Rift Volibear Baron — W-spam heal / shield simulation
Patch 7.3 (Sep 2026). 12s slugfest vs a bruiser.

Playstyle: max Frenzied Maul, bite on cooldown, stand in Sky Splitter,
never swap W targets. Score heal + shield (the identity), not 1v1 mix.

The Dusk → Hull → Rift duelist page lives in volibear-build-sim/.
This file asks a different question: which shop and rune page actually
feed spam-W sustain now that Spirit Visage is gone.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import json
from pathlib import Path

PATCH = "7.3"
GAME_MINUTES = 22
FIGHT_S = 12.0
W_BASE_CD = 5.0
W_CAST = 0.25
E_BASE_CD = 13.0
DESPAIR_PERIOD = 4.0
TITANIC_CD = 1.75
# Sit in the W-heal band. Revitalize's extra 10% is <40% HP.
FIGHT_HP_FRAC = 0.38
OUT_DIR = Path(__file__).resolve().parent


# ---------------------------------------------------------------------------
# Economy / XP (Baron farmer, same curve as the duelist sim)
# ---------------------------------------------------------------------------


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
        21: 15, 22: 15,
    }
    return table.get(m, min(15, 1 + m))


def skill_rank(level: int, skill: str) -> int:
    """W max, Q second, E last. R at 5/9/13."""
    if skill == "R":
        return 0 if level < 5 else 1 if level < 9 else 2 if level < 13 else 3
    q = [2, 7, 10, 11]
    w = [1, 4, 6, 8]
    e = [3, 12, 14, 15]
    mapping = {"Q": q, "W": w, "E": e}
    return sum(1 for lv in mapping[skill] if level >= lv)


# ---------------------------------------------------------------------------
# Items (7.3 live aggregator + 7.2e Despair; Spirit Visage removed in 7.0)
# ---------------------------------------------------------------------------


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
    mana: float = 0
    tenacity: float = 0
    sheen: str = "none"  # none | dusk | trinity
    heartsteel: bool = False
    rift: bool = False
    hull: bool = False
    despair: bool = False
    sterak: bool = False
    titanic: bool = False
    fimbul: bool = False
    boots: bool = False


# Tốc Chiến shop name. Mid-tier, not a legendary — search or open Despair.
KINDLE_KEY = "Kindlegem"
KINDLE_NAME = "Hỏa Ngọc (Kindlegem)"


ITEMS: Dict[str, Item] = {
    "Long Sword": Item("Long Sword", 500, ad=12),
    "Ruby Crystal": Item("Ruby Crystal", 500, hp=200),
    KINDLE_KEY: Item(KINDLE_NAME, 1000, hp=175, ah=10),
    "Sheen": Item("Sheen", 800, sheen="trinity"),
    "Giant's Belt": Item("Giant's Belt", 1000, hp=350),
    "Heartsteel": Item("Heartsteel", 2800, hp=700, ah=20, heartsteel=True),
    "Trinity Force": Item(
        "Trinity Force", 3333, ad=36, hp=333, ah=15, as_pct=0.30, sheen="trinity"
    ),
    "Dusk and Dawn": Item(
        "Dusk and Dawn", 3100, ap=70, hp=350, ah=20, as_pct=0.25, sheen="dusk"
    ),
    "Hullbreaker": Item("Hullbreaker", 3100, ad=45, hp=400, hull=True),
    "Riftmaker": Item(
        "Riftmaker", 3100, ap=70, hp=350, ah=15, rift=True
    ),
    "Unending Despair": Item(
        "Unending Despair", 3000, hp=300, ah=10, armor=40, mr=40, despair=True
    ),
    "Sterak's Gage": Item(
        "Sterak's Gage", 3200, hp=400, tenacity=0.20, sterak=True
    ),
    "Titanic Hydra": Item(
        "Titanic Hydra", 3000, ad=40, hp=450, titanic=True
    ),
    "Fimbulwinter": Item(
        "Fimbulwinter", 2600, hp=350, ah=15, mana=1200, fimbul=True
    ),
    "Amaranth's Twinguard": Item(
        "Amaranth's Twinguard", 3200, hp=300, armor=50, mr=50
    ),
    "Plated Steelcaps": Item(
        "Plated Steelcaps", 1200, hp=150, armor=25, boots=True
    ),
}


assert "Spirit Visage" not in ITEMS, "Spirit Visage was removed in patch 7.0"


@dataclass
class Path:
    name: str
    legendaries: List[str]
    note: str


# Leftover gold after the last finished legendary buys this component of the next one.
# Hỏa Ngọc (Kindlegem) is the W-spam component: +10 AH is the extra bite.
NEXT_COMPONENT = {
    "Unending Despair": KINDLE_KEY,
    "Trinity Force": "Sheen",
    "Riftmaker": KINDLE_KEY,
    "Sterak's Gage": "Ruby Crystal",
    "Heartsteel": KINDLE_KEY,
    "Titanic Hydra": "Ruby Crystal",
    "Hullbreaker": "Ruby Crystal",
    "Amaranth's Twinguard": "Ruby Crystal",
    "Dusk and Dawn": "Sheen",
    "Fimbulwinter": "Giant's Belt",
}


PATHS = [
    Path(
        "Heart → Despair → Sterak",
        ["Heartsteel", "Unending Despair", "Sterak's Gage", "Amaranth's Twinguard"],
        "Skip sheen. Hỏa Ngọc leftover + Despair 10 AH is the extra bite.",
    ),
    Path(
        "Heart → Sterak → Despair",
        ["Heartsteel", "Sterak's Gage", "Unending Despair", "Amaranth's Twinguard"],
        "Hỏa Ngọc buys the extra bite. Lifeline at ~17 is the mid-game shield.",
    ),
    Path(
        "Heart → Tri → Despair",
        ["Heartsteel", "Trinity Force", "Unending Despair", "Sterak's Gage"],
        "HP then sheen. Trinity delays both sustain items.",
    ),
    Path(
        "Heart → Tri → Sterak",
        ["Heartsteel", "Trinity Force", "Sterak's Gage", "Unending Despair"],
        "Sheen then lifeline. Despair often unfinished.",
    ),
    Path(
        "Heart → Titanic → Despair",
        ["Heartsteel", "Titanic Hydra", "Unending Despair", "Sterak's Gage"],
        "W applies on-hit, so Cleave rides every bite.",
    ),
    Path(
        "Heart → Titanic → Sterak",
        ["Heartsteel", "Titanic Hydra", "Sterak's Gage", "Unending Despair"],
        "On-hit W plus lifeline. No pulse.",
    ),
    Path(
        "Tri → Heart → Despair",
        ["Trinity Force", "Heartsteel", "Unending Despair", "Sterak's Gage"],
        "W cadence first. E shield waits on the 700 HP.",
    ),
    Path(
        "Heart → Rift → Despair",
        ["Heartsteel", "Riftmaker", "Unending Despair", "Sterak's Gage"],
        "10% omnivamp heal-off. AP feeds E shield.",
    ),
    Path(
        "Dusk → Hull → Rift",
        ["Dusk and Dawn", "Hullbreaker", "Riftmaker", "Unending Despair"],
        "Duelist control from volibear-build-sim. Mix, not sustain.",
    ),
    Path(
        "Dusk → Rift → Despair",
        ["Dusk and Dawn", "Riftmaker", "Unending Despair", "Sterak's Gage"],
        "AP vamp, skip Hull. Still no Heartsteel HP for E.",
    ),
    Path(
        "Fimbul → Sterak → Twin",
        ["Fimbulwinter", "Sterak's Gage", "Amaranth's Twinguard", "Unending Despair"],
        "Shield-tank / Tear. Q stun and E slow proc Frozen Colossus.",
    ),
]


def inventory_at_gold(path: Path, gold: int) -> List[Item]:
    """Sequential shop. Once Hỏa Ngọc (Kindlegem) is bought, that gold is gone.

    After Heartsteel + boots, leftover Hỏa Ngọc is the extra bite
    (30 AH). Despair later consumes it. Sterak does not — so Sterak
    second pays a 1000g delay.
    """
    owned: List[Item] = []
    spent = 0
    boots_pending = False
    kindle_checked = False
    unfinished: Optional[str] = None

    def has(key: str) -> bool:
        want = ITEMS[key].name
        return any(i.name == want for i in owned)

    def consume(key: str) -> None:
        want = ITEMS[key].name
        for idx, it in enumerate(owned):
            if it.name == want:
                owned.pop(idx)
                return

    def try_kindlegem() -> None:
        nonlocal spent, kindle_checked
        if kindle_checked:
            return
        if not any(i.heartsteel for i in owned):
            return
        if boots_pending:
            return
        kindle_checked = True
        ah = sum(i.ah for i in owned)
        if ah >= 28 or has(KINDLE_KEY):
            return
        if spent + ITEMS[KINDLE_KEY].cost <= gold:
            owned.append(ITEMS[KINDLE_KEY])
            spent += ITEMS[KINDLE_KEY].cost

    for i, name in enumerate(path.legendaries):
        try_kindlegem()
        item = ITEMS[name]
        comp = NEXT_COMPONENT.get(name)
        credit = ITEMS[comp].cost if (comp and has(comp)) else 0
        net = item.cost - credit
        if spent + net <= gold:
            if credit:
                consume(comp)
            owned.append(item)
            spent += net
            if i == 0:
                boots_pending = True
        else:
            unfinished = name
            break
        if boots_pending and spent + ITEMS["Plated Steelcaps"].cost <= gold:
            owned.append(ITEMS["Plated Steelcaps"])
            spent += ITEMS["Plated Steelcaps"].cost
            boots_pending = False
        try_kindlegem()

    try_kindlegem()
    if unfinished and not boots_pending:
        comp = NEXT_COMPONENT.get(unfinished)
        if (
            comp
            and spent + ITEMS[comp].cost <= gold
            and not has(comp)
        ):
            owned.append(ITEMS[comp])

    if not owned:
        owned = [ITEMS["Long Sword"]]
    return owned


def item_label(key: str) -> str:
    return ITEMS[key].name if key in ITEMS else key


def minute_of_item(path: Path, item_name: str) -> Optional[int]:
    want = item_label(item_name)
    for m in range(1, GAME_MINUTES + 1):
        names = [i.name for i in inventory_at_gold(path, gold_at_minute(m))]
        if want in names:
            return m
    return None


# ---------------------------------------------------------------------------
# Kit math
# ---------------------------------------------------------------------------


def resist_mult(res: float) -> float:
    return 100.0 / (100.0 + max(0.0, res))


def voli_base(level: int) -> Tuple[float, float, float, float, float]:
    hp = 690 + 128 * (level - 1)
    ad = 62 + 4 * (level - 1)
    armor = 46 + 4.7 * (level - 1)
    mr = 38 + 2.0 * (level - 1)
    mana = 390 + 65 * (level - 1)
    return hp, ad, armor, mr, mana


def lightning(level: int, ap: float) -> float:
    # Patch 7.3: 12–68 (+40% AP)
    return 12 + (68 - 12) * (level - 1) / 14 + 0.40 * ap


def target_bruiser(m: int) -> Tuple[float, float, float]:
    lv = level_at_minute(m)
    hp = 720 + 118 * (lv - 1) + 35 * m
    armor = 52 + 4.4 * (lv - 1) + (25 if m >= 12 else 8)
    mr = 38 + 2.0 * (lv - 1) + (20 if m >= 14 else 5)
    return hp, armor, mr


def w_cooldown(ah: float) -> float:
    return W_BASE_CD / (1.0 + ah / 100.0)


def w_cast_times(ah: float, fight_s: float = FIGHT_S) -> List[float]:
    """W starts at t=0, then on cooldown. Need 0.25s to land before the window ends."""
    cd = w_cooldown(ah)
    times: List[float] = []
    t = 0.0
    while t + W_CAST <= fight_s + 1e-9:
        times.append(round(t, 4))
        t += cd
    return times


def n_w_bites(n_casts: int) -> int:
    """First champion W starts Frenzy (slash). Every later W is a heal-bite."""
    return max(0, n_casts - 1)


def extra_bite_ah_needed(fight_s: float = FIGHT_S) -> float:
    """AH so a 4th W still lands (3rd bite). 3 * cd + 0.25 <= fight_s."""
    # 3 * 5 / (1+ah/100) <= fight_s - 0.25
    budget = fight_s - W_CAST
    # 15 / (1+ah/100) <= budget → 15/budget <= 1+ah/100 → ah >= 100*(15/budget - 1)
    return 100.0 * (15.0 / budget - 1.0)


def heartsteel_stacks(m: int, owned: bool) -> int:
    """~1.3 Colossal procs/min after Heartsteel comes online (~7:00)."""
    if not owned or m < 7:
        return 0
    return int((m - 7) * 1.3)


def heartsteel_stack_hp(max_hp_no_stacks: float, stacks: int) -> float:
    per = 0.15 * (140.0 + 0.035 * max_hp_no_stacks)
    return stacks * per


def overgrowth_hp(m: int) -> float:
    """~2 stacks/min from lane minions, cap 30 then +3% max HP."""
    stacks = min(30, max(0, 2 * m))
    flat = 3.0 * stacks
    return flat


def colossus_shield(level: int, max_hp: float) -> float:
    base = 25.0 + (45.0 - 25.0) * (level - 1) / 14.0
    return base + 0.01 * max_hp


def fimbul_shield(level: int, current_mana: float, nearby: int = 1) -> float:
    # Patch 6.0: 90–180 (+4.5% current mana), +80% if 2+ nearby.
    base = 90.0 + (180.0 - 90.0) * (level - 1) / 14.0
    raw = base + 0.045 * current_mana
    if nearby >= 2:
        raw *= 1.80
    return raw


# ---------------------------------------------------------------------------
# Runes
# ---------------------------------------------------------------------------


@dataclass
class Page:
    name: str
    keystone: str  # Grasp | Lethal Tempo | Conqueror
    resolve: Tuple[str, ...]
    secondary: str
    note: str


PAGES = [
    Page(
        "Grasp / Revitalize / Overgrowth",
        "Grasp",
        ("Second Wind", "Revitalize", "Overgrowth"),
        "Last Stand",
        "Resolve primary (legal 3+1). HSP + HP for E and the bite.",
    ),
    Page(
        "Grasp / Revitalize / Colossus",
        "Grasp",
        ("Second Wind", "Revitalize", "Courage of the Colossus"),
        "Last Stand",
        "Q stun shield instead of Overgrowth HP.",
    ),
    Page(
        "Grasp / no Revitalize",
        "Grasp",
        ("Second Wind", "Overgrowth", "Bone Plating"),
        "Last Stand",
        "Same keystone, no heal/shield amp.",
    ),
    Page(
        "Conqueror / Bloodline / Revitalize",
        "Conqueror",
        ("Brutal", "Last Stand", "Legend: Bloodline"),
        "Revitalize",
        "Precision primary. 9% Conq omnivamp + Bloodline. One Resolve: Revitalize.",
    ),
    Page(
        "Lethal Tempo / Alacrity",
        "Lethal Tempo",
        ("Brutal", "Legend: Alacrity", "Last Stand"),
        "Second Wind",
        "Duelist keystone. Extra autos, no HSP, no Overgrowth.",
    ),
]


def page_has(page: Page, rune: str) -> bool:
    if page.keystone == rune or page.secondary == rune:
        return True
    return rune in page.resolve


# ---------------------------------------------------------------------------
# Combat
# ---------------------------------------------------------------------------


@dataclass
class Fight:
    mix: float
    heal: float
    shield: float
    sustain: float
    ehp: float
    identity: float
    hp: float
    ah: float
    w_casts: int
    w_bites: int
    w_cd: float
    items: List[str]
    notes: List[str] = field(default_factory=list)


def fight_at(
    path: Path,
    m: int,
    page: Optional[Page] = None,
) -> Fight:
    page = page or PAGES[0]
    lv = level_at_minute(m)
    gold = gold_at_minute(m)
    inv = inventory_at_gold(path, gold)
    q = skill_rank(lv, "Q")
    w = skill_rank(lv, "W")
    e = skill_rank(lv, "E")
    r = skill_rank(lv, "R")

    base_hp, base_ad, _base_ar, _base_mr, base_mana = voli_base(lv)
    bonus_hp = sum(i.hp for i in inv)
    bonus_ad = sum(i.ad for i in inv)
    ap = sum(i.ap for i in inv)
    ah = sum(i.ah for i in inv)
    as_pct = sum(i.as_pct for i in inv)
    mana = base_mana + sum(i.mana for i in inv)

    has_dusk = any(i.sheen == "dusk" for i in inv)
    has_tri = any(i.sheen == "trinity" for i in inv)
    has_sheen_comp = any(i.name == "Sheen" for i in inv)
    has_hs = any(i.heartsteel for i in inv)
    has_rift = any(i.rift for i in inv)
    has_hull = any(i.hull for i in inv)
    has_despair = any(i.despair for i in inv)
    has_sterak = any(i.sterak for i in inv)
    has_titanic = any(i.titanic for i in inv)
    has_fimbul = any(i.fimbul for i in inv)

    if has_sterak:
        bonus_ad += 0.50 * base_ad
    if has_fimbul:
        bonus_hp += 0.08 * mana  # Awe
    if has_rift:
        ap += 0.02 * bonus_hp

    r_hp = [0, 175, 350, 525][r]
    max_hp_no_hs = base_hp + bonus_hp + r_hp
    stacks = heartsteel_stacks(m, has_hs)
    hs_hp = heartsteel_stack_hp(max_hp_no_hs, stacks) if has_hs else 0.0
    og_flat = overgrowth_hp(m) if page_has(page, "Overgrowth") else 0.0
    max_hp = max_hp_no_hs + hs_hp + og_flat
    if page_has(page, "Overgrowth") and min(30, max(0, 2 * m)) >= 30:
        max_hp *= 1.03
    bonus_hp_for_w = max_hp - base_hp
    total_ad = base_ad + bonus_ad

    t_hp, t_ar, t_mr = target_bruiser(m)
    mpen = 0.07 if has_rift else 0.0
    phys = resist_mult(t_ar)
    mag = resist_mult(t_mr * (1.0 - mpen))
    rift_amp = 1.06 if has_rift else 1.0  # 12s window, stacked longer than 8s
    vamp = 0.0
    if has_rift:
        vamp += 0.10
    if page.keystone == "Conqueror":
        vamp += 0.09  # melee, fully stacked ~3s into the fight
    if page_has(page, "Legend: Bloodline"):
        vamp += min(0.07, 0.025 + 0.0025 * m)

    tempo_as = 0.0
    if page.keystone == "Lethal Tempo":
        tempo_as = 0.08 * 6  # 48% AS at 6 stacks
    if page_has(page, "Legend: Alacrity"):
        tempo_as += 0.18

    # Attack count: Q reset + 12s of AS. Passive +25% AS at 5 stacks.
    base_as = 0.73 * (1 + 0.017 * (lv - 1))
    as_total = base_as * (1 + as_pct + 0.25 + tempo_as)
    n_aa = 1 + int(FIGHT_S * as_total)
    n_aa = max(5, min(n_aa, 16))

    times = w_cast_times(ah)
    n_w = len(times) if w else 0
    n_bites = n_w_bites(n_w) if w else 0
    w_cd = w_cooldown(ah)

    n_blade = min(n_w + 1, 1 + int(FIGHT_S / 1.5))  # E/Q/W weave, 1.5s sheen CD
    sheen_kind = "dusk" if has_dusk else ("trinity" if (has_tri or has_sheen_comp) else "none")

    hsp_low = page_has(page, "Revitalize")
    # Bite / Sterak happen in the <40% band. E is usually thrown healthy.
    hsp_bite = 1.15 if hsp_low else 1.0
    hsp_e = 1.05 if hsp_low else 1.0
    hsp_mid = 1.10 if hsp_low else 1.0

    phys_raw = 0.0
    mag_raw = 0.0
    notes: List[str] = []

    phys_raw += n_aa * total_ad

    if q:
        q_bonus = [0, 15, 40, 65, 90][q] + 1.0 * bonus_ad
        phys_raw += q_bonus

    if w:
        slash = [0, 5, 30, 55, 80][w] + 1.0 * total_ad + 0.065 * bonus_hp_for_w
        bite = [0, 8, 48, 88, 128][w] + 1.6 * total_ad + 0.104 * bonus_hp_for_w
        phys_raw += slash + n_bites * bite
        notes.append(f"{n_w} W ({n_bites} bites) cd {w_cd:.2f}s")

    if e:
        e_d = [0, 80, 110, 140, 170][e] + 0.50 * ap + [0, 0.11, 0.12, 0.13, 0.14][e] * t_hp
        mag_raw += e_d

    if r:
        r_d = [0, 300, 500, 700][r] + 2.10 * bonus_ad + 1.0 * ap
        phys_raw += r_d

    lit = lightning(lv, ap)
    mag_raw += max(0, n_aa - 2) * lit
    if has_dusk:
        mag_raw += min(n_blade, max(0, n_aa - 2)) * lit

    if sheen_kind == "dusk":
        mag_raw += n_blade * (0.75 * base_ad + 0.10 * ap)
    elif sheen_kind == "trinity":
        ratio = 2.0 if has_tri else 1.0
        phys_raw += n_blade * (ratio * base_ad)

    if has_hs:
        phys_raw += 140 + 0.035 * max_hp

    if has_hull:
        n_skip = n_aa // 4
        phys_raw += n_skip * (1.60 * base_ad + 0.05 * max_hp)

    n_despair = 0
    if has_despair:
        n_despair = int(FIGHT_S / DESPAIR_PERIOD)  # 4, 8, 12 → 3
        mag_raw += n_despair * 0.03 * max_hp
        notes.append(f"Despair x{n_despair}")

    if has_titanic:
        n_cleave = min(n_aa + n_w, 1 + int(FIGHT_S / TITANIC_CD))
        phys_raw += n_cleave * (25 + 0.03 * bonus_hp_for_w)
        notes.append(f"Titanic x{n_cleave}")

    n_grasp = 0
    if page.keystone == "Grasp":
        n_grasp = 2  # first ~4s, second ~10s in a 12s fight
        mag_raw += n_grasp * 0.033 * max_hp
        notes.append("Grasp x2")

    mix = (phys_raw * phys + mag_raw * mag) * rift_amp

    # ---- Heals ----
    missing = (1.0 - FIGHT_HP_FRAC) * max_hp
    heal = 0.0
    if w and n_bites:
        base_heal = [0, 20, 30, 40, 50][w]
        ratio = [0, 0.05, 0.06, 0.07, 0.08][w]
        heal += n_bites * (base_heal + ratio * missing) * hsp_bite
    if has_despair:
        # 250% of the 3% max HP tick (pre-mitigation as live tooltip)
        heal += n_despair * (0.03 * max_hp * 2.50) * hsp_mid
    if n_grasp:
        heal += n_grasp * 0.013 * max_hp * hsp_mid
    if vamp:
        heal += vamp * mix * 0.70 * hsp_mid  # 12s contact
    # Second Wind: doubled melee, 3 + 1.5% missing over 5s, twice in 12s
    if page_has(page, "Second Wind"):
        heal += 2.0 * (3.0 + 0.015 * missing) * 2.0 * hsp_mid

    # ---- Shields ----
    shield = 0.0
    if e:
        shield += (0.14 * max_hp + 0.75 * ap) * hsp_e
        notes.append("stand in E")
    if has_sterak:
        # Lifeline assumed to fire in this slugfest (you sit at 38%).
        shield += 0.75 * bonus_hp_for_w * hsp_bite
        notes.append("Sterak Lifeline")
    if page_has(page, "Courage of the Colossus") and q:
        shield += colossus_shield(lv, max_hp) * hsp_e
        notes.append("Colossus on Q")
    if has_fimbul and (q or e):
        shield += fimbul_shield(lv, mana, nearby=1) * hsp_e
        notes.append("Fimbul on Q/E")

    sustain = heal + shield
    ehp = max_hp + shield + heal
    # Identity: sustain first. A bit of mix so a wet noodle cannot win.
    identity = sustain + 0.25 * mix
    return Fight(
        mix=mix,
        heal=heal,
        shield=shield,
        sustain=sustain,
        ehp=ehp,
        identity=identity,
        hp=max_hp,
        ah=ah,
        w_casts=n_w,
        w_bites=n_bites,
        w_cd=w_cd,
        items=[i.name for i in inv],
        notes=notes,
    )


def path_by_name(name: str) -> Path:
    for p in PATHS:
        if p.name == name:
            return p
    raise KeyError(name)


def page_by_name(name: str) -> Page:
    for p in PAGES:
        if p.name == name:
            return p
    raise KeyError(name)


def weighted_identity(path: Path, page: Optional[Page] = None) -> float:
    acc = 0.0
    for m in range(6, GAME_MINUTES + 1):
        acc += fight_at(path, m, page).identity
    return acc


def weighted_sustain(path: Path, page: Optional[Page] = None) -> float:
    acc = 0.0
    for m in range(6, GAME_MINUTES + 1):
        acc += fight_at(path, m, page).sustain
    return acc


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------


def fmt_items(names: List[str]) -> str:
    skip = {"Plated Steelcaps", "Long Sword"}
    core = [n for n in names if n not in skip]
    return ", ".join(core) if core else ", ".join(names)


def build_report() -> Tuple[str, dict]:
    default_page = PAGES[0]
    minutes = list(range(6, GAME_MINUTES + 1))
    snapshots: Dict[str, List[dict]] = {}
    totals: Dict[str, float] = {}
    sustain_totals: Dict[str, float] = {}

    for path in PATHS:
        rows = []
        acc = 0.0
        sus = 0.0
        for m in minutes:
            f = fight_at(path, m, default_page)
            acc += f.identity
            sus += f.sustain
            rows.append(
                {
                    "m": m,
                    "gold": gold_at_minute(m),
                    "level": level_at_minute(m),
                    "items": f.items,
                    "mix": round(f.mix),
                    "heal": round(f.heal),
                    "shield": round(f.shield),
                    "sustain": round(f.sustain),
                    "ehp": round(f.ehp),
                    "identity": round(f.identity),
                    "hp": round(f.hp),
                    "ah": round(f.ah, 1),
                    "w_casts": f.w_casts,
                    "w_bites": f.w_bites,
                    "w_cd": round(f.w_cd, 2),
                    "notes": f.notes,
                }
            )
        snapshots[path.name] = rows
        totals[path.name] = acc
        sustain_totals[path.name] = sus

    ranked = sorted(PATHS, key=lambda p: totals[p.name], reverse=True)
    winner = ranked[0]
    dusk = path_by_name("Dusk → Hull → Rift")

    # Rune rank on the winning shop
    rune_rows = []
    for page in PAGES:
        acc_id = 0.0
        acc_sus = 0.0
        at14 = fight_at(winner, 14, page)
        at22 = fight_at(winner, 22, page)
        for m in minutes:
            f = fight_at(winner, m, page)
            acc_id += f.identity
            acc_sus += f.sustain
        rune_rows.append(
            {
                "page": page.name,
                "keystone": page.keystone,
                "identity": acc_id,
                "sustain": acc_sus,
                "heal14": at14.heal,
                "shield14": at14.shield,
                "mix14": at14.mix,
                "heal22": at22.heal,
                "shield22": at22.shield,
                "mix22": at22.mix,
                "note": page.note,
            }
        )
    rune_rows.sort(key=lambda r: r["identity"], reverse=True)
    rune_winner = rune_rows[0]

    bite_ah = extra_bite_ah_needed()
    f8 = fight_at(winner, 8, default_page)
    f14 = fight_at(winner, 14, default_page)
    f22 = fight_at(winner, 22, default_page)
    d14 = fight_at(dusk, 14, default_page)
    d22 = fight_at(dusk, 22, default_page)

    def minute_held(path: Path, item_name: str, with_item: Optional[str] = None) -> Optional[int]:
        want = item_label(item_name)
        req = item_label(with_item) if with_item else None
        for m in range(1, GAME_MINUTES + 1):
            names = [i.name for i in inventory_at_gold(path, gold_at_minute(m))]
            if want in names and (req is None or req in names):
                return m
        return None

    spikes = []
    for item, require in (
        ("Heartsteel", None),
        ("Kindlegem", "Heartsteel"),
        ("Unending Despair", None),
        ("Sterak's Gage", None),
        ("Trinity Force", None),
        ("Titanic Hydra", None),
        ("Fimbulwinter", None),
    ):
        mm = minute_held(winner, item, require)
        if mm:
            spikes.append((item, mm))

    second = winner.legendaries[1] if len(winner.legendaries) > 1 else "?"
    third = winner.legendaries[2] if len(winner.legendaries) > 2 else "?"
    fourth = winner.legendaries[3] if len(winner.legendaries) > 3 else "Twinguard"

    lines: List[str] = [
        f"Wild Rift Volibear — W-spam heal / shield — patch {PATCH}",
        f"{FIGHT_S:.0f}s slugfest vs a bruiser. Sit at {int(FIGHT_HP_FRAC*100)}% HP.",
        "Identity = (heal + shield) + 0.25 × mix. Boots after the first legendary.",
        "Spirit Visage was removed in 7.0. Heal amp is Revitalize; pulse is Despair.",
        "",
        f"WINNER: {winner.name}",
        f"  {winner.note}",
        f"RUNES: {rune_winner['page']}",
        "",
        "Buy order (W-spam sustain)",
        "  Start     Long Sword",
        "  1st item  Heartsteel (2800)     E is 14% max HP; W bite is 10.4% bonus HP",
        "  Then      Hỏa Ngọc (Kindlegem) — extra bite; buy from Despair tree",
        "  Boots     Plated Steelcaps (Mercury's if they are AP/CC)",
        f"  2nd item  {second}",
        f"  3rd item  {third}",
        f"  4th item  {fourth} / Thornmail / Kaenic",
        "  Enchant   Stoneplate",
        "  Skill     max W, one E, then Q. R at 5 / 9 / 13",
        "  Spells    Flash + Ignite (Teleport if you are splitting)",
        "",
        f"AH for a 3rd bite in {FIGHT_S:.0f}s: {bite_ah:.1f}. Heartsteel 20 is not enough.",
        "Hỏa Ngọc leftover (30 AH) is the extra W. It is not a legendary.",
        "Tốc Chiến name: Hỏa Ngọc. English shop: Kindlegem. Skip Trinity.",
        "",
        "Where to buy Hỏa Ngọc (Kindlegem) — it is not on Recommended",
        "  Sterak does not use Hỏa Ngọc, so Volibear Recommended will not show it.",
        "  Tốc Chiến: tìm 'Hỏa Ngọc'. English client: search 'Kindlegem'.",
        "  Or open Unending Despair (Thất Vọng Bất Tận) / Heartsteel (Giáp Tim Thép)",
        "  / Black Cleaver and tap the HP + 10 haste component.",
        "  Recipe: Hồng Ngọc / Ruby Crystal 500 + 500 = 1000.",
        "  Stats: +175 HP, +10 AH. Mid-tier, Defense / Support.",
        "  Heartsteel already ate the first one. Buy a SECOND Hỏa Ngọc after it.",
        "",
        f"{'Path':<28}{'8':>7}{'12':>7}{'14':>7}{'18':>7}{'22':>7}{'sum':>8}",
        "-" * 72,
    ]
    for p in ranked:
        cells = []
        for mm in (8, 12, 14, 18, 22):
            cells.append(f"{fight_at(p, mm, default_page).identity:7.0f}")
        lines.append(f"{p.name:<28}{''.join(cells)}{totals[p.name]:8.0f}")

    lines += [
        "",
        "Sustain (heal + shield) at the same minutes",
        f"{'Path':<28}{'8':>7}{'14':>7}{'22':>7}{'W@14':>7}{'heal':>7}{'shld':>7}",
        "-" * 72,
    ]
    for p in ranked:
        a, b, c = (fight_at(p, mm, default_page) for mm in (8, 14, 22))
        lines.append(
            f"{p.name:<28}{a.sustain:7.0f}{b.sustain:7.0f}{c.sustain:7.0f}"
            f"{b.w_casts:7d}{b.heal:7.0f}{b.shield:7.0f}"
        )

    lines += [
        "",
        "Why Heartsteel first (this playstyle, not the 1v1)",
        "  E Sky Splitter shield is 14% of YOUR max HP if you stand in it.",
        "  Empowered W is 10.4% bonus HP damage and 5–8% missing HP heal.",
        "  Heartsteel is 700 HP + 20 AH + stacks. That is the shield and the bite.",
        "  Dusk → Hull → Rift still wins isolated mix. It loses heal+shield here:",
        f"    @14:00  {winner.name} sustain {f14.sustain:.0f} vs Dusk/Hull {d14.sustain:.0f}",
        f"    @22:00  {winner.name} sustain {f22.sustain:.0f} vs Dusk/Hull {d22.sustain:.0f}",
        "",
        "Why Sterak second — skip Trinity, skip Despair-second as default",
        "  Hỏa Ngọc after Heartsteel already buys the 4th W (~11:00). Despair's",
        "  10 AH is not the extra bite anymore; its unique is the 4s pulse.",
        "  Sterak's unique is Lifeline (75% bonus HP). A 18–20 min game sees",
        "  Sterak second (~17:00) and never sees Despair third (~21:00).",
        "  Despair second is the fork: pulse at ~15:00, but no panic shield",
        "  until ~21:00. Take it into a heal-off when they cannot burst you.",
        "  Trinity is 3333g of sheen with no heal and no shield. Hỏa Ngọc",
        "  already covered cadence. Do not buy it on this page.",
        "",
        "Why not Fimbulwinter",
        "  Q/E Frozen Colossus looks strong until ~14:00. Heartsteel stacks",
        "  plus Hỏa Ngọc bites bury it once the game lasts. Tear does not",
        "  help Frenzied Maul. Do not start Tear.",
        "",
        "Spirit Visage is gone",
        "  Removed in 7.0. Do not look for a 25% heal/shield item.",
        "  Revitalize is 5% HSP, 15% while you are below 40% — that is the bite band.",
        "  Unending Despair is the combat heal. Sterak is the panic shield.",
        "",
        "How to play it",
        "  1. Max W. First W on a champion starts Frenzy (8s). Do not swap targets.",
        "  2. Every later W is the bite: more damage, the missing-HP heal.",
        "  3. Press W the instant it is up. The heal is the cooldown.",
        "  4. Drop E on your feet before the stun. Stand in the bolt for the shield.",
        "  5. Q to stick after E is placed, not as the opener.",
        "  6. R for the bonus HP (feeds E and W) and the turret disable.",
        "",
        "Runes on this shop (legal 7.3 pages: 3 in the keystone tree + 1 secondary)",
        f"{'Page':<36}{'sum id':>8}{'sum sus':>9}{'14 heal':>9}{'14 sh':>7}{'14 mix':>8}",
        "-" * 76,
    ]
    for row in rune_rows:
        lines.append(
            f"{row['page']:<36}{row['identity']:8.0f}{row['sustain']:9.0f}"
            f"{row['heal14']:9.0f}{row['shield14']:7.0f}{row['mix14']:8.0f}"
        )

    grasp_row = next(r for r in rune_rows if r["keystone"] == "Grasp")
    conq_row = next(r for r in rune_rows if r["keystone"] == "Conqueror")
    tempo_row = next(r for r in rune_rows if r["keystone"] == "Lethal Tempo")
    no_rev = next(r for r in rune_rows if r["page"] == "Grasp / no Revitalize")

    lines += [
        "",
        f"Default page: {rune_winner['page']}. Flash + Ignite.",
        "  Grasp / Revitalize / Overgrowth / Last Stand if the keystone is Grasp:",
        "  two 1.3% max-HP heals, Overgrowth HP for E and the bite, Second Wind",
        "  doubled as melee. That is the tank-sustain page.",
        "  Conqueror / Bloodline / Revitalize turns W damage into omnivamp.",
        f"  Sim identity: Conq {conq_row['identity']:.0f} vs Grasp {grasp_row['identity']:.0f}"
        f" vs Tempo {tempo_row['identity']:.0f}.",
        "  Lethal Tempo is the other sim's 1v1 page — autos and lightning, 0 HSP.",
        f"  Dropping Revitalize costs sustain ({no_rev['sustain']:.0f} vs"
        f" {grasp_row['sustain']:.0f} on Grasp).",
        "  Colossus on Q is a small extra shield; Overgrowth's HP feeds E and W",
        "  for the whole game, so keep Overgrowth over Colossus on Grasp.",
        "  Last Stand, not Cut Down: you live at ~38% HP. See volibear-build-sim.",
        "",
        "Swaps",
        "  Heal-off / they cannot burst you: Despair second, Sterak third.",
        "  They stack HP: keep Despair third, 4th is Thornmail not Twinguard.",
        "  Heavy AP: Mercury's, then Kaenic instead of Twinguard.",
        "  You cannot finish Heartsteel (lost lane): Hỏa Ngọc + Hồng Ngọc, still max W.",
        "  Do not buy Trinity or Dusk on this page. Sheen is the 1v1 item.",
        "  Do not start Tear. Fimbulwinter is a 14-minute trap.",
        "",
        "Spikes on the winner",
    ]
    for item, mm in spikes:
        ff = fight_at(winner, mm, default_page)
        lines.append(
            f"  ~{mm:02d}:00  {item_label(item):<22}  {ff.w_casts} W / {ff.w_bites} bites  "
            f"heal {ff.heal:.0f}  shield {ff.shield:.0f}  [{fmt_items(ff.items)}]"
        )

    lines += [
        "",
        f"@8:00  {fmt_items(f8.items)}  W {f8.w_casts}/{f8.w_bites}  "
        f"heal {f8.heal:.0f}  sh {f8.shield:.0f}  mix {f8.mix:.0f}",
        f"@14:00 {fmt_items(f14.items)}  W {f14.w_casts}/{f14.w_bites}  "
        f"heal {f14.heal:.0f}  sh {f14.shield:.0f}  mix {f14.mix:.0f}",
        f"@22:00 {fmt_items(f22.items)}  W {f22.w_casts}/{f22.w_bites}  "
        f"heal {f22.heal:.0f}  sh {f22.shield:.0f}  mix {f22.mix:.0f}",
        "",
    ]
    for p in ranked:
        lines.append(f"{p.name}: {p.note}")
        hs = minute_of_item(p, "Heartsteel")
        tri = minute_of_item(p, "Trinity Force")
        des = minute_of_item(p, "Unending Despair")
        stk = minute_of_item(p, "Sterak's Gage")
        bits = []
        if hs:
            bits.append(f"Heart ~{hs}:00")
        if tri:
            bits.append(f"Tri ~{tri}:00")
        if des:
            bits.append(f"Despair ~{des}:00")
        if stk:
            bits.append(f"Sterak ~{stk}:00")
        if bits:
            lines.append("  " + ", ".join(bits))
        lines.append("")

    text = "\n".join(lines)
    payload = {
        "patch": PATCH,
        "playstyle": "W-spam heal/shield",
        "fight_s": FIGHT_S,
        "hp_frac": FIGHT_HP_FRAC,
        "extra_bite_ah": round(bite_ah, 2),
        "winner": winner.name,
        "winner_note": winner.note,
        "rune_winner": rune_winner["page"],
        "buy_order": [
            "Long Sword",
            "Heartsteel",
            "Hỏa Ngọc (Kindlegem, extra bite)",
            "Plated Steelcaps",
            *winner.legendaries[1:],
        ],
        "skill_order": "W > Q > E, R at 5/9/13",
        "spells": "Flash + Ignite",
        "identity_totals": {p.name: round(totals[p.name]) for p in ranked},
        "sustain_totals": {p.name: round(sustain_totals[p.name]) for p in ranked},
        "runes": rune_rows,
        "snapshots": snapshots,
        "compare_vs_duelist": {
            "winner_sustain_14": round(f14.sustain),
            "dusk_sustain_14": round(d14.sustain),
            "winner_sustain_22": round(f22.sustain),
            "dusk_sustain_22": round(d22.sustain),
            "winner_mix_14": round(f14.mix),
            "dusk_mix_14": round(d14.mix),
        },
    }
    return text, payload


def main() -> None:
    text, payload = build_report()
    print(text)
    (OUT_DIR / "report.txt").write_text(text + "\n", encoding="utf-8")
    (OUT_DIR / "results.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )
    print(f"\nWrote {OUT_DIR / 'report.txt'} and {OUT_DIR / 'results.json'}")


if __name__ == "__main__":
    main()
