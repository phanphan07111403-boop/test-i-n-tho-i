#!/usr/bin/env python3
"""
Wild Rift Brand support — patch 7.3b.

Question: Scythe → Ionian → Whispering Circlet (Diadem of Songs) →
Echoes of Helia → Harmonic Echo → Ardent Censer or Mikael's Blessing.

Compare:
  * healing vs enchanters on the same items
  * damage vs mage supports on their own damage builds
  * damage vs other Brand support builds

Numbers are the live 7.3b item passives (Diadem Harmony nerfed in 7.3a to
0.25% of max mana) and wiki ability ratios. Runes are not included.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import json

GAME_MINUTES = 22

# Charges per minute while Whispering Circlet is owned.
# Cap is 2 procs / 10s = 12/min. Lane Brand does not cast that often.
CHARGE_PER_MIN = 8


def gold_at_minute(m: int) -> int:
    """Same support curve as the Zyra sim: sickle start, tribute, soul-forge
    gold already baked into the per-minute income. ~10.1k at 20:00."""
    if m <= 0:
        return 500
    total = 500
    for t in range(1, m + 1):
        if t <= 4:
            total += 320
        elif t <= 10:
            total += 460
        else:
            total += 560
    return total


def level_at_minute(m: int) -> int:
    # Support XP. Level 13 at 20:00 (R rank 3, one basic maxed twice).
    table = {
        1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7, 7: 8, 8: 8,
        9: 9, 10: 10, 11: 10, 12: 11, 13: 11, 14: 12,
        15: 12, 16: 12, 17: 13, 18: 13, 19: 13, 20: 13,
        21: 14, 22: 14,
    }
    return table.get(m, 14)


# ---------------------------------------------------------------------------
# Items (7.3b)
# ---------------------------------------------------------------------------

@dataclass
class Item:
    name: str
    cost: int
    ap: float = 0
    ah: float = 0
    hp: float = 0
    mana: float = 0
    hsp: float = 0  # fraction, 0.08 = 8%
    harmony: bool = False
    flat_mpen: float = 0
    pct_mpen: float = 0
    burn: str = "none"  # ashes | blackfire | liandry
    rylai: bool = False
    deathcap: bool = False
    mandate: bool = False
    helia: bool = False
    harmonic: bool = False
    ardent: bool = False
    mikael: bool = False
    diadem: bool = False
    circlet: bool = False
    scythe: bool = False


ITEMS: Dict[str, Item] = {
    "Spectral Sickle": Item("Spectral Sickle", 500, ap=20),
    "Black Mist Scythe": Item("Black Mist Scythe", 0, ap=28, ah=10, scythe=True),
    "Boots of Speed": Item("Boots of Speed", 400),
    "Ring of Revelation": Item("Ring of Revelation", 300),
    "Ionian Boots of Lucidity": Item("Ionian Boots of Lucidity", 1000, ah=15),
    # 7.2 repo model. Not listed in the 7.3b patch notes.
    "Boots of Mana": Item("Boots of Mana", 1200, ap=25, flat_mpen=8),
    "Amplifying Tome": Item("Amplifying Tome", 500, ap=20),
    "Blasting Wand": Item("Blasting Wand", 800, ap=45),
    "Needlessly Large Rod": Item("Needlessly Large Rod", 1400, ap=70),
    "Ruby Crystal": Item("Ruby Crystal", 500, hp=200),
    "Giant's Belt": Item("Giant's Belt", 1000, hp=350),
    "Kindlegem": Item("Kindlegem", 1000, hp=200, ah=10),
    "Forbidden Idol": Item("Forbidden Idol", 700, hsp=0.06),
    # Tear's displayed mana is not on the 7.3b support sheet. 200 matches the
    # long-standing component. Circlet's own +500 replaces it on combine.
    "Tear of the Goddess": Item("Tear of the Goddess", 400, mana=200),
    "Bandleglass Mirror": Item("Bandleglass Mirror", 900, ah=10),
    "Aether Wisp": Item("Aether Wisp", 950, ap=30),
    "Fiendish Codex": Item("Fiendish Codex", 900, ap=35, ah=10),
    "Lost Chapter": Item("Lost Chapter", 1200, ap=40, ah=10),
    "Fated Ashes": Item("Fated Ashes", 900, ap=40, burn="ashes"),
    "Haunting Guise": Item("Haunting Guise", 1300, ap=35, hp=200),
    "Whispering Circlet": Item(
        "Whispering Circlet", 2400, hp=200, mana=500, hsp=0.08,
        harmony=True, circlet=True,
    ),
    "Diadem of Songs": Item(
        "Diadem of Songs", 2400, hp=200, mana=1200, hsp=0.08,
        harmony=True, diadem=True,
    ),
    "Echoes of Helia": Item(
        "Echoes of Helia", 2400, ap=40, ah=20, hp=200, helia=True,
    ),
    "Harmonic Echo": Item(
        "Harmonic Echo", 2500, ap=40, ah=20, hp=200, harmonic=True,
    ),
    "Ardent Censer": Item(
        "Ardent Censer", 2400, ap=50, hsp=0.08, ardent=True,
    ),
    "Mikael's Blessing": Item(
        "Mikael's Blessing", 2500, hp=300, ah=15, mikael=True,
    ),
    "Liandry's Torment": Item(
        "Liandry's Torment", 3000, ap=70, hp=300, pct_mpen=0.07, burn="liandry",
    ),
    "Blackfire Torch": Item(
        "Blackfire Torch", 2800, ap=80, ah=20, burn="blackfire",
    ),
    "Rylai's Crystal Scepter": Item(
        "Rylai's Crystal Scepter", 2700, ap=70, hp=350, rylai=True,
    ),
    "Imperial Mandate": Item(
        "Imperial Mandate", 2600, ap=60, ah=20, mandate=True,
    ),
    "Rabadon's Deathcap": Item(
        "Rabadon's Deathcap", 3400, ap=130, deathcap=True,
    ),
}


COMPONENTS: Dict[str, Tuple[str, ...]] = {
    "Ionian Boots of Lucidity": ("Boots of Speed", "Ring of Revelation"),
    "Boots of Mana": ("Boots of Speed",),
    "Bandleglass Mirror": ("Amplifying Tome", "Ring of Revelation"),
    "Aether Wisp": ("Amplifying Tome",),
    "Whispering Circlet": ("Forbidden Idol", "Tear of the Goddess", "Ruby Crystal"),
    "Echoes of Helia": ("Bandleglass Mirror", "Kindlegem"),
    "Harmonic Echo": ("Bandleglass Mirror", "Kindlegem"),
    "Ardent Censer": ("Aether Wisp", "Forbidden Idol"),
    "Mikael's Blessing": ("Forbidden Idol", "Kindlegem"),
    "Liandry's Torment": ("Fated Ashes", "Haunting Guise"),
    "Blackfire Torch": ("Fated Ashes", "Lost Chapter"),
    "Rylai's Crystal Scepter": ("Giant's Belt", "Blasting Wand", "Amplifying Tome"),
    "Imperial Mandate": ("Bandleglass Mirror", "Blasting Wand"),
    "Rabadon's Deathcap": ("Needlessly Large Rod", "Blasting Wand"),
}


# User build, then the Brand damage paths, then mage-support damage paths.
# Enchanters reuse the Ardent user path so the heal comparison is the kit.
BUILD_PATHS: Dict[str, List[str]] = {
    "Brand Diadem Helia Ardent": [
        "Spectral Sickle",
        "Ionian Boots of Lucidity",
        "Whispering Circlet",
        "Echoes of Helia",
        "Harmonic Echo",
        "Ardent Censer",
    ],
    "Brand Diadem Helia Mikael": [
        "Spectral Sickle",
        "Ionian Boots of Lucidity",
        "Whispering Circlet",
        "Echoes of Helia",
        "Harmonic Echo",
        "Mikael's Blessing",
    ],
    "Brand Liandry Rylai Mandate": [
        "Spectral Sickle",
        "Boots of Mana",
        "Fated Ashes",
        "Haunting Guise",
        "Liandry's Torment",
        "Rylai's Crystal Scepter",
        "Imperial Mandate",
    ],
    "Brand Blackfire Liandry Rylai": [
        "Spectral Sickle",
        "Boots of Mana",
        "Fated Ashes",
        "Lost Chapter",
        "Blackfire Torch",
        "Haunting Guise",
        "Liandry's Torment",
        "Rylai's Crystal Scepter",
    ],
    "Brand Liandry Mandate Rylai": [
        "Spectral Sickle",
        "Ionian Boots of Lucidity",
        "Fated Ashes",
        "Haunting Guise",
        "Liandry's Torment",
        "Imperial Mandate",
        "Rylai's Crystal Scepter",
    ],
    "Zyra Liandry Rylai": [
        "Spectral Sickle",
        "Boots of Mana",
        "Fated Ashes",
        "Haunting Guise",
        "Liandry's Torment",
        "Rylai's Crystal Scepter",
        "Rabadon's Deathcap",
    ],
    "Morgana Liandry Rylai": [
        "Spectral Sickle",
        "Boots of Mana",
        "Fated Ashes",
        "Haunting Guise",
        "Liandry's Torment",
        "Rylai's Crystal Scepter",
        "Imperial Mandate",
    ],
    "Lux Mandate Deathcap": [
        "Spectral Sickle",
        "Boots of Mana",
        "Imperial Mandate",
        "Needlessly Large Rod",
        "Rabadon's Deathcap",
        "Rylai's Crystal Scepter",
    ],
}


ENCHANTER_BUILD = "Brand Diadem Helia Ardent"
HEAL_CHAMPS = ["Brand", "Soraka", "Sona", "Nami", "Yuumi", "Seraphine"]


def scythe_stacks(minute: int) -> int:
    # Quest completes ~5:00. +1 stack per minute after that, cap 10.
    if minute < 6:
        return 0
    return min(10, minute - 5)


def resolve_owned(path: List[str], gold: int, minute: int) -> List[str]:
    """Buy along path. Leftover gold buys components of the next item."""
    owned: List[str] = []
    pool = gold

    def credit(item_name: str) -> Tuple[int, List[str]]:
        gained = 0
        remove: List[str] = []
        for comp in COMPONENTS.get(item_name, ()):
            if comp in owned:
                gained += ITEMS[comp].cost
                remove.append(comp)
        return gained, remove

    def cost_of(item_name: str) -> int:
        if item_name == "Black Mist Scythe":
            return 0
        gained, _ = credit(item_name)
        return max(0, ITEMS[item_name].cost - gained)

    def buy(item_name: str) -> bool:
        nonlocal pool
        if item_name in owned and item_name != "Amplifying Tome":
            return False
        if item_name == "Black Mist Scythe":
            if "Spectral Sickle" in owned:
                owned.remove("Spectral Sickle")
            owned.append(item_name)
            return True
        price = cost_of(item_name)
        if price > pool:
            return False
        _, remove = credit(item_name)
        pool -= price
        for comp in remove:
            owned.remove(comp)
        # Boots of Speed is consumed by the upgrade even if not in COMPONENTS
        # credit (already handled). Drop plain boots once an upgrade exists.
        owned.append(item_name)
        if item_name in ("Ionian Boots of Lucidity", "Boots of Mana"):
            if "Boots of Speed" in owned:
                owned.remove("Boots of Speed")
        return True

    blocked: Optional[str] = None
    for step in path:
        if step == "Spectral Sickle":
            if "Spectral Sickle" not in owned and "Black Mist Scythe" not in owned:
                buy("Spectral Sickle")
            continue
        if step in owned:
            continue
        if buy(step):
            continue
        blocked = step
        break

    if minute >= 5 and "Spectral Sickle" in owned:
        owned.remove("Spectral Sickle")
        owned.insert(0, "Black Mist Scythe")

    if blocked:
        for comp in COMPONENTS.get(blocked, ()):
            if comp in owned:
                continue
            if pool >= ITEMS[comp].cost:
                buy(comp)
        if blocked not in owned and cost_of(blocked) <= pool:
            buy(blocked)

    return owned


def circlet_online_minute(path: List[str]) -> Optional[int]:
    for m in range(0, GAME_MINUTES + 1):
        owned = resolve_owned(path, gold_at_minute(m), m)
        if "Whispering Circlet" in owned:
            return m
    return None


# ---------------------------------------------------------------------------
# Combat stats
# ---------------------------------------------------------------------------

BASE_MANA = {
    "Brand": (435, 49),
    "Soraka": (345, 65),
    "Sona": (345, 4.9),
    "Nami": (390, 49),
    "Yuumi": (435, 49),
    "Seraphine": (435, 49),
    "Lux": (480, 49),
    "Zyra": (420, 50),
    "Morgana": (435, 49),
}


def base_mana(champ: str, level: int) -> float:
    base, growth = BASE_MANA[champ]
    return base + growth * (level - 1)


@dataclass
class Stats:
    champ: str
    minute: int
    level: int
    names: List[str]
    ap: float
    ah: float
    hp: float
    mana: float
    hsp: float
    flat_mpen: float
    pct_mpen: float
    diadem: bool
    circlet: bool
    charges: int
    helia: bool
    harmonic: bool
    ardent: bool
    mikael: bool
    liandry: bool
    blackfire: bool
    ashes: bool
    rylai: bool
    deathcap: bool
    mandate: bool
    gold: int = 0


def stats_from_names(
    champ: str,
    names: List[str],
    level: int,
    minute: int,
    charges: int,
    gold: int,
    soul_stacks: int,
) -> Stats:
    ap = ah = hp = mana_item = hsp = flat = pct = 0.0
    flags = dict(
        diadem=False, circlet=False, helia=False, harmonic=False,
        ardent=False, mikael=False, liandry=False, blackfire=False,
        ashes=False, rylai=False, deathcap=False, mandate=False,
        harmony=False,
    )
    seen = list(names)
    # Circlet becomes Diadem at 700 bonus mana (50 × 14).
    if "Whispering Circlet" in seen and charges >= 50:
        seen = [("Diadem of Songs" if n == "Whispering Circlet" else n) for n in seen]

    for name in seen:
        it = ITEMS[name]
        ap += it.ap
        ah += it.ah
        hp += it.hp
        mana_item += it.mana
        hsp += it.hsp
        flat += it.flat_mpen
        pct += it.pct_mpen
        if it.scythe:
            ap += 4 * soul_stacks
            hp += 25 * soul_stacks
        flags["diadem"] = flags["diadem"] or it.diadem
        flags["circlet"] = flags["circlet"] or it.circlet
        flags["helia"] = flags["helia"] or it.helia
        flags["harmonic"] = flags["harmonic"] or it.harmonic
        flags["ardent"] = flags["ardent"] or it.ardent
        flags["mikael"] = flags["mikael"] or it.mikael
        flags["liandry"] = flags["liandry"] or it.burn == "liandry"
        flags["blackfire"] = flags["blackfire"] or it.burn == "blackfire"
        flags["ashes"] = flags["ashes"] or it.burn == "ashes"
        flags["rylai"] = flags["rylai"] or it.rylai
        flags["deathcap"] = flags["deathcap"] or it.deathcap
        flags["mandate"] = flags["mandate"] or it.mandate
        flags["harmony"] = flags["harmony"] or it.harmony
        if it.diadem:
            flags["circlet"] = False

    if "Whispering Circlet" in seen:
        mana_item += 14 * min(50, charges)

    if flags["deathcap"]:
        ap *= 1.30

    mana = base_mana(champ, level) + mana_item
    if flags["harmony"]:
        # 7.3a nerf, still live on 7.3b: 0.25% of max mana, in percentage
        # points of heal/shield power. 2000 mana → +5% HSP. The pre-nerf
        # 0.5% rate was documented as +10 points at 2000 mana.
        hsp += (0.0025 * mana) / 100.0

    return Stats(
        champ=champ,
        minute=minute,
        level=level,
        names=seen,
        ap=ap,
        ah=ah,
        hp=hp,
        mana=mana,
        hsp=1.0 + hsp,
        flat_mpen=flat,
        pct_mpen=pct,
        diadem=flags["diadem"],
        circlet="Whispering Circlet" in seen,
        charges=charges if "Whispering Circlet" in names or flags["diadem"] else 0,
        helia=flags["helia"],
        harmonic=flags["harmonic"],
        ardent=flags["ardent"],
        mikael=flags["mikael"],
        liandry=flags["liandry"],
        blackfire=flags["blackfire"],
        ashes=flags["ashes"] and not flags["liandry"] and not flags["blackfire"],
        rylai=flags["rylai"],
        deathcap=flags["deathcap"],
        mandate=flags["mandate"],
        gold=gold,
    )


def stats_at(champ: str, path: List[str], minute: int) -> Stats:
    level = level_at_minute(minute)
    owned = resolve_owned(path, gold_at_minute(minute), minute)
    online = circlet_online_minute(path)
    charges = 0
    if online is not None and minute >= online and "Whispering Circlet" in owned:
        charges = min(50, CHARGE_PER_MIN * (minute - online))
    return stats_from_names(
        champ, owned, level, minute, charges, gold_at_minute(minute), scythe_stacks(minute)
    )


def sandbox_stats(champ: str, path_key: str, level: int = 13) -> Stats:
    """Full listed build, components combined, soul-forge capped, Diadem up."""
    names = resolve_owned(BUILD_PATHS[path_key], 999999, GAME_MINUTES)
    names = ["Diadem of Songs" if n == "Whispering Circlet" else n for n in names]
    return stats_from_names(
        champ, names, level, minute=18, charges=50, gold=0, soul_stacks=10
    )


# ---------------------------------------------------------------------------
# Targets and mitigation
# ---------------------------------------------------------------------------

def carry_stats(level: int, minute: int) -> Tuple[float, float]:
    hp = 700 + 85 * (level - 1) + 35 * minute
    mr = 38 + 1.3 * (level - 1) + (25 if minute >= 12 else 0)
    return hp, mr


def front_stats(level: int, minute: int) -> Tuple[float, float]:
    hp = 900 + 130 * (level - 1) + 70 * minute
    mr = 42 + 2.0 * (level - 1)
    if minute >= 10:
        mr += 35
    if minute >= 16:
        mr += 25
    return hp, mr


def mitigate(pre: float, mr: float, st: Stats) -> float:
    emr = max(0.0, mr * (1 - st.pct_mpen) - st.flat_mpen)
    return pre * 100.0 / (100.0 + emr)


def haste_cd(base: float, ah: float) -> float:
    return base * 100.0 / (100.0 + ah)


def ncast(base_cd: float, fight_s: float, ah: float, cap: int = 2) -> int:
    if base_cd <= 0:
        return 0
    cd = haste_cd(base_cd, ah)
    return min(cap, 1 + int((fight_s - 0.4) / cd))


def ability_ranks(level: int, max_order: str) -> Dict[str, int]:
    """One point in each basic, ultimate at 5/9/13, then max_order."""
    ranks = {c: 0 for c in "QWER"}
    opening = list(max_order)
    for lvl in range(1, level + 1):
        if lvl in (5, 9, 13) and ranks["R"] < 3:
            ranks["R"] += 1
            continue
        if lvl <= 3:
            ranks[opening[lvl - 1]] += 1
            continue
        for key in opening:
            if ranks[key] < 4:
                ranks[key] += 1
                break
    return ranks


def yuumi_ranks(level: int) -> Dict[str, int]:
    ranks = {"Q": 0, "E": 0, "R": 0}
    for lvl in range(1, level + 1):
        if lvl in (5, 9, 13) and ranks["R"] < 3:
            ranks["R"] += 1
            continue
        if lvl <= 3:
            if lvl < 3 and ranks["Q"] < 5:
                ranks["Q"] += 1
            elif ranks["E"] < 4:
                ranks["E"] += 1
            continue
        if ranks["Q"] < 5:
            ranks["Q"] += 1
        elif ranks["E"] < 4:
            ranks["E"] += 1
    return ranks


def rank_value(table: List[float], rank: int) -> float:
    if rank <= 0:
        return 0.0
    return table[min(rank, len(table) - 1)]


def p_at_least(probs: List[float], need: int) -> float:
    """Probability at least `need` independent events land."""
    n = len(probs)
    total = 0.0
    for mask in range(1 << n):
        bits = 0
        p = 1.0
        for i in range(n):
            if mask & (1 << i):
                bits += 1
                p *= probs[i]
            else:
                p *= 1 - probs[i]
        if bits >= need:
            total += p
    return total


def helia_cap(level: int) -> float:
    return 80 + (250 - 80) * (level - 1) / 14


def helia_stored(pre: float, level: int, fight_s: float, every_second: bool, dumps: int) -> float:
    """Pre-HSP shard total. 30% of pre-mitigation damage, cap per spend."""
    if pre <= 0 or (not every_second and dumps <= 0):
        return 0.0
    cap = helia_cap(level)
    if every_second:
        burst = 0.65 * pre
        rest = 0.35 * pre
        burst_s = min(2.0, fight_s)
        rest_s = max(0.0, fight_s - burst_s)
        return min(burst_s * cap, 0.30 * burst) + min(rest_s * cap, 0.30 * rest)
    each = pre / dumps
    return dumps * min(cap, 0.30 * each)


def item_heal_layer(st: Stats, kit_heal: float, kit_shield: float, pre_damage: float,
                    fight_s: float, kit_dumps: int) -> Tuple[float, float]:
    """Return (ally healing, ally shielding) after HSP, Diadem, Helia, Harmonic, Mikael."""
    hsp = st.hsp
    heal = kit_heal * hsp
    shield = kit_shield * hsp

    if st.diadem:
        # 0.8% max mana per second on the lowest ally. ~8% of ticks hit Brand
        # himself when he is the lowest, so allies receive 92%.
        heal += 0.008 * st.mana * fight_s * 0.92 * hsp

    if st.helia:
        every = st.diadem
        dumps = kit_dumps if not every else 0
        if st.mikael and not every:
            dumps += 1
        stored = helia_stored(pre_damage, st.level, fight_s, every, dumps)
        heal += stored * hsp

    if st.mikael:
        base = 150 + (250 - 150) * (st.level - 1) / 14
        heal += base * hsp

    if st.harmonic:
        # Echo lands on a missing-HP ally: +30% of heals, +35% of shields.
        heal *= 1.30
        shield *= 1.35
    return heal, shield


# ---------------------------------------------------------------------------
# Champion damage in an 8s fight where ultimate is up
# ---------------------------------------------------------------------------

FIGHT_S = 8.0


@dataclass
class Fight:
    pre: float
    post_front: float
    post_carry: float
    heal: float
    shield: float
    kit_dumps: int
    note: str = ""


def _burn_pre(st: Stats, hp: float, uptime: float, ap: float) -> float:
    pre = 0.0
    if st.liandry:
        pre += 0.02 * hp * uptime
    elif st.blackfire:
        pre += (20 + 0.02 * ap) * uptime
    elif st.ashes:
        pre += 5.0 * uptime
    if st.liandry:
        pre *= 1.04  # Madness averaged over a short fight
    return pre


def _ap_fight(st: Stats) -> float:
    ap = st.ap
    if st.blackfire:
        ap *= 1.08  # two champions taking damage, +4% AP each
    return ap


def brand_fight(st: Stats, front: Tuple[float, float], carry: Tuple[float, float]) -> Fight:
    """E the pair, W the pair, Q the carry, R bounces. One detonation each."""
    ranks = ability_ranks(st.level, "WQE")
    ap = _ap_fight(st)
    w_base = [0, 70, 120, 170, 220]
    q_base = [0, 80, 120, 160, 200]
    e_base = [0, 60, 90, 120, 150]
    r_base = [0, 100, 200, 300]
    w_cd = [0, 9.5, 9.0, 8.5, 8.0]
    q_cd = [0, 7.5, 7.0, 6.5, 6.0]
    e_cd = [0, 11, 10, 9, 8]
    wr, qr, er, rr = ranks["W"], ranks["Q"], ranks["E"], ranks["R"]
    nw = ncast(rank_value(w_cd, wr), FIGHT_S, st.ah) if wr else 0
    nq = ncast(rank_value(q_cd, qr), FIGHT_S, st.ah) if qr else 0
    ne = ncast(rank_value(e_cd, er), FIGHT_S, st.ah) if er else 0

    p_w = 0.78 if st.rylai else 0.70
    p_e = 0.90
    p_q = 0.72
    p_r = 0.88 if rr else 0.0
    # Secondary body sits in the same W/E/R but is not the Q target.
    p_w2, p_e2, p_r2 = p_w * 0.85, p_e * 0.78, p_r * 0.80

    def one(hp: float, mr: float, pw: float, pe: float, pq: float, pr: float,
            r_hits: float, focused_q: bool) -> Tuple[float, float]:
        pre = 0.0
        if wr and nw:
            spell = rank_value(w_base, wr) + 0.55 * ap
            spell *= 1 + 0.30 * pe  # empowered if E already applied Blaze
            pre += nw * pw * spell
        if er and ne:
            pre += ne * pe * (rank_value(e_base, er) + 0.45 * ap)
        if focused_q and qr and nq:
            pre += nq * pq * (rank_value(q_base, qr) + 0.55 * ap)
        if rr and pr:
            pre += r_hits * pr * (rank_value(r_base, rr) + 0.30 * ap)

        events = [pe, pw, pr]
        if focused_q:
            events.append(pq)
        p_det = p_at_least(events, 3) if rr or focused_q else p_at_least(events, 3)
        p_any = 1 - (1 - pe) * (1 - pw) * (1 - (pq if focused_q else 0)) * (1 - pr)
        det_pct = 0.10 + (0.142 - 0.10) * (st.level - 1) / 14 + 0.02 * ap / 100
        # Detonation consumes stacks after 2s, so the DoT only partially runs.
        pre += p_det * (0.015 * hp + det_pct * hp)
        pre += (1 - p_det) * p_any * 0.03 * hp
        uptime = FIGHT_S * (0.85 if p_any > 0.4 else 0.35)
        pre += _burn_pre(st, hp, uptime, ap)
        if st.mandate and (pq > 0.4 or pr > 0.4):
            pre *= 1.05
        return pre, mitigate(pre, mr, st)

    # R has 5 champion hits available. Focus (carry) takes 2, front takes 2,
    # one bounce is wasted on Brand or a minion.
    pre_c, post_c = one(carry[0], carry[1], p_w, p_e, p_q, p_r, 2.0, True)
    pre_f, post_f = one(front[0], front[1], p_w2, p_e2, 0.0, p_r2, 2.0, False)
    return Fight(pre_c + pre_f, post_f, post_c, 0, 0, 0, "no kit heal")


def zyra_fight(st: Stats, front: Tuple[float, float], carry: Tuple[float, float]) -> Fight:
    ranks = ability_ranks(st.level, "QEW")
    ap = _ap_fight(st)
    q = rank_value([0, 60, 115, 170, 225], ranks["Q"]) + 0.50 * ap
    e = rank_value([0, 60, 100, 140, 180], ranks["E"]) + 0.40 * ap
    r = rank_value([0, 150, 225, 300], ranks["R"]) + 0.50 * ap if ranks["R"] else 0
    q_cd = rank_value([0, 8, 7.5, 7, 6.5], ranks["Q"])
    nq = ncast(q_cd, FIGHT_S, st.ah) if ranks["Q"] else 0
    plant_hit = 10 + (108 - 10) * (st.level - 1) / 14 + 0.15 * ap
    # Two plants, 6s, 0.8 AS, enrage ~1.4 AS average, second plant deals 50%.
    plant_pre = 2.0 * 6.0 * 1.15 * plant_hit * 0.80
    p_q, p_e, p_r = (0.78 if st.rylai else 0.68), 0.70, 0.85 if ranks["R"] else 0

    def one(hp, mr, aoe=1.0) -> Tuple[float, float]:
        pre = aoe * (nq * p_q * q + p_e * e + p_r * r) + plant_pre * aoe
        uptime = 6.0 if (st.liandry or st.blackfire or st.ashes) else 0
        pre += _burn_pre(st, hp, uptime, ap)
        if st.mandate and p_e > 0.4:
            pre *= 1.04
        return pre, mitigate(pre, mr, st)

    pre_c, post_c = one(carry[0], carry[1], 1.0)
    pre_f, post_f = one(front[0], front[1], 0.85)
    return Fight(pre_c + pre_f, post_f, post_c, 0, 0, 0)


def lux_fight(st: Stats, front: Tuple[float, float], carry: Tuple[float, float]) -> Fight:
    ranks = ability_ranks(st.level, "EQW")
    ap = st.ap
    q = rank_value([0, 60, 120, 180, 240], ranks["Q"]) + 0.70 * ap
    e = rank_value([0, 65, 130, 195, 260], ranks["E"]) + 0.55 * ap
    r = rank_value([0, 300, 400, 500], ranks["R"]) + 0.75 * ap if ranks["R"] else 0
    shield = rank_value([0, 65, 120, 175, 230], ranks["W"]) + 0.46 * ap
    passive = 25.5 + (130.5 - 25.5) * (st.level - 1) / 14 + 0.25 * ap
    p_q, p_e, p_r = 0.68, 0.74, 0.80 if ranks["R"] else 0
    procs = 2.2  # Q mark into E, E mark into R or an auto

    def one(hp, mr, q_hits: float) -> Tuple[float, float]:
        pre = q_hits * p_q * q + p_e * e + p_r * r + procs * (p_q * 0.5 + p_e) * passive
        if st.mandate and p_q > 0.4:
            pre *= 1.05
        pre += _burn_pre(st, hp, 3.0 if st.liandry or st.blackfire else 0, ap)
        return pre, mitigate(pre, mr, st)

    # Q roots two champions.
    pre_c, post_c = one(carry[0], carry[1], 1.0)
    pre_f, post_f = one(front[0], front[1], 0.85)
    # Shield: ADC is walked through both passes. One dump for Helia.
    return Fight(pre_c + pre_f, post_f, post_c, 0, shield if ranks["W"] else 0, 1 if ranks["W"] else 0)


def morgana_fight(st: Stats, front: Tuple[float, float], carry: Tuple[float, float]) -> Fight:
    ranks = ability_ranks(st.level, "WQE")
    ap = _ap_fight(st)
    q = rank_value([0, 80, 160, 240, 320], ranks["Q"]) + 0.90 * ap
    tick = rank_value([0, 7, 12, 17, 22], ranks["W"]) + 0.07 * ap
    # 10 ticks. 170% extra at 0 missing-HP amp; average target is 35% missing.
    w = 10 * tick * (1 + 1.70 * 0.35) * 0.82
    r_hit = rank_value([0, 150, 225, 300], ranks["R"]) + 0.70 * ap if ranks["R"] else 0
    # Second pop lands 70% of the time.
    r = r_hit * 1.70
    shield = rank_value([0, 70, 150, 230, 310], ranks["E"]) + 0.50 * ap
    p_q = 0.66
    p_r = 0.80 if ranks["R"] else 0

    def one(hp, mr, bound: float) -> Tuple[float, float]:
        pre = bound * p_q * q + w + p_r * r
        uptime = 5.0 if (st.liandry or st.blackfire or st.ashes) else 0
        pre += _burn_pre(st, hp, uptime, ap)
        if st.mandate and (p_q > 0.4 or p_r > 0.4):
            pre *= 1.05
        return pre, mitigate(pre, mr, st)

    pre_c, post_c = one(carry[0], carry[1], 1.0)
    pre_f, post_f = one(front[0], front[1], 0.55)
    dumps = 1 if ranks["E"] else 0
    return Fight(pre_c + pre_f, post_f, post_c, 0, shield if ranks["E"] else 0, dumps)


def soraka_fight(st: Stats, front, carry) -> Fight:
    ranks = ability_ranks(st.level, "WQE")
    ap = st.ap
    w = rank_value([0, 50, 85, 120, 155], ranks["W"]) + 0.55 * ap
    w_cd = rank_value([0, 7, 6, 5, 4], ranks["W"])
    # Q landing refunds 2s. Fold that in as a shorter CD.
    casts = ncast(max(2.0, w_cd - 1.2), FIGHT_S, st.ah, cap=3) if ranks["W"] else 0
    kit = casts * w
    wish = 0.0
    if ranks["R"]:
        base = rank_value([0, 150, 225, 300], ranks["R"]) + 0.45 * ap
        # One low ally (×1.5) and two other allies at full value. Self excluded.
        wish = base * 1.5 + base * 2
    q = rank_value([0, 60, 110, 160, 210], ranks["Q"]) + 0.40 * ap
    e = rank_value([0, 70, 120, 170, 220], ranks["E"]) + 0.40 * ap
    pre = 0.55 * q + 0.45 * e * 1.4  # Q poke + E zone, modest hit rate, two bodies on E
    dumps = casts + (1 if ranks["R"] else 0)
    fight = Fight(pre, mitigate(pre * 0.45, front[1], st), mitigate(pre * 0.55, carry[1], st),
                  kit + wish, 0, dumps)
    return fight


def sona_fight(st: Stats, front, carry) -> Fight:
    ranks = ability_ranks(st.level, "WQE")
    ap = st.ap
    # Basic CD reduced 2–20% by level.
    cdr = 0.02 + 0.18 * (st.level - 1) / 14
    heal = rank_value([0, 45, 60, 75, 90], ranks["W"]) + 0.20 * ap
    shield = rank_value([0, 25, 50, 75, 100], ranks["W"]) + 0.18 * ap
    w_cd = 10 * (1 - cdr)
    casts = ncast(w_cd, FIGHT_S, st.ah, cap=2) if ranks["W"] else 0
    # Heal: herself + the most wounded ally. Count the ally only.
    # Shield aura: two allies.
    kit_heal = casts * heal
    kit_shield = casts * shield * 2
    q = rank_value([0, 40, 80, 120, 160], ranks["Q"]) + 0.40 * ap
    r_tick = rank_value([0, 35, 60, 85], ranks["R"]) + 0.15 * ap if ranks["R"] else 0
    chord = 20 + (160 - 20) * (st.level - 1) / 14 + 0.15 * ap
    pre = 0.75 * 2 * q + (5 * r_tick * 0.7 if ranks["R"] else 0) + 0.8 * chord
    return Fight(pre, mitigate(pre * 0.40, front[1], st), mitigate(pre * 0.60, carry[1], st),
                 kit_heal, kit_shield, casts)


def nami_fight(st: Stats, front, carry) -> Fight:
    ranks = ability_ranks(st.level, "WEQ")
    ap = st.ap
    heal = rank_value([0, 55, 85, 115, 145], ranks["W"]) + 0.30 * ap
    # Return bounce usually hits Nami, not a second ally. Count one ally heal,
    # 8% smaller because half the time she opens on the enemy and the ally
    # takes the reduced bounce.
    decay = 0.15 - 0.075 * ap / 100
    ally_heal = heal * (0.55 + 0.45 * (1 - decay))
    casts = ncast(10, FIGHT_S, st.ah, cap=2) if ranks["W"] else 0
    q = rank_value([0, 75, 145, 215, 285], ranks["Q"]) + 0.50 * ap
    r = rank_value([0, 150, 250, 350], ranks["R"]) + 0.60 * ap if ranks["R"] else 0
    e = rank_value([0, 25, 45, 65, 85], ranks["E"]) + 0.20 * ap
    pre = 0.62 * q + (0.75 * r if ranks["R"] else 0) + 2.2 * e * 0.8
    # E buff damage is real but small; 3 autos × 0.8 land rate, on one target.
    pre += 3 * 0.8 * e if ranks["E"] else 0
    return Fight(pre, mitigate(pre * 0.35, front[1], st), mitigate(pre * 0.65, carry[1], st),
                 casts * ally_heal, 0, casts)


def seraphine_fight(st: Stats, front, carry) -> Fight:
    ranks = ability_ranks(st.level, "WEQ")
    ap = st.ap
    shield = rank_value([0, 50, 75, 100, 125], ranks["W"]) + 0.30 * ap
    # Echo is held for W: two shields. Two allies.
    kit_shield = (2 * shield * 2) if ranks["W"] else 0
    # Heal proc because the second cast sees the first shield.
    # 6% (+1% per 100 AP) missing HP, +50% with a second ally. Missing ≈ 40%.
    ratio = 0.06 + 0.01 * ap / 100
    missing = 0.40
    kit_heal = 0.0
    if ranks["W"]:
        kit_heal = 2 * (ratio * missing * carry[0]) * 1.50
    q = rank_value([0, 60, 75, 90, 105], ranks["Q"]) + 0.45 * ap
    e = rank_value([0, 60, 95, 130, 165], ranks["E"]) + 0.40 * ap
    r = rank_value([0, 150, 250, 350], ranks["R"]) + 0.70 * ap if ranks["R"] else 0
    # Echo spent on W, so Q/E are single. Average missing-HP amp on Q ~ +20%.
    pre = 0.72 * q * 1.20 * 1.5 + 0.70 * e * 1.4 + (0.75 * r * 1.5 if ranks["R"] else 0)
    return Fight(pre, mitigate(pre * 0.45, front[1], st), mitigate(pre * 0.55, carry[1], st),
                 kit_heal, kit_shield, 1 if ranks["W"] else 0)


def yuumi_fight(st: Stats, front, carry) -> Fight:
    ranks = yuumi_ranks(st.level)
    ap = st.ap
    # Best Friend heal/shield power, four steps. Tied to how ranked E is.
    bf = [0, 0.06, 0.07, 0.08, 0.09][max(1, ranks["E"])] + 0.02 * ap / 100
    st_hsp_extra = Stats(**{**st.__dict__, "hsp": st.hsp + bf})
    q = rank_value([0, 100, 160, 220, 280, 340], ranks["Q"]) + 0.35 * ap
    shield = rank_value([0, 85, 110, 135, 160], ranks["E"]) + 0.30 * ap
    e_casts = ncast(10, FIGHT_S, st.ah, cap=1) if ranks["E"] else 0
    passive = 67 + (165 - 67) * (st.level - 1) / 14 + 0.25 * ap
    per_wave = rank_value([0, 26, 39, 52], ranks["R"]) + 0.08 * ap if ranks["R"] else 0
    # 5 of 7 waves hit the anchor.
    kit_heal = 0.85 * passive + (5 * per_wave if ranks["R"] else 0)
    wave_dmg = rank_value([0, 80, 100, 120], ranks["R"]) + 0.15 * ap if ranks["R"] else 0
    # First wave full, later waves reduced. Approximate 1 + 4 * 0.35 of a full wave.
    r_pre = (wave_dmg + 4 * wave_dmg * 0.35) if ranks["R"] else 0
    pre = 0.70 * q + 0.65 * r_pre
    fight = Fight(pre, mitigate(pre * 0.30, front[1], st), mitigate(pre * 0.70, carry[1], st),
                  kit_heal, e_casts * shield, e_casts + (1 if ranks["R"] else 0) + 1)
    # Swap in the Best Friend HSP by returning a fight and letting the caller
    # use st_hsp_extra. Easiest: mutate a copy's hsp via the object we return
    # through a side channel. We'll attach it.
    fight.note = "yuumi-hsp"
    fight._st = st_hsp_extra  # type: ignore[attr-defined]
    return fight


FIGHTERS = {
    "Brand": brand_fight,
    "Zyra": zyra_fight,
    "Lux": lux_fight,
    "Morgana": morgana_fight,
    "Soraka": soraka_fight,
    "Sona": sona_fight,
    "Nami": nami_fight,
    "Seraphine": seraphine_fight,
    "Yuumi": yuumi_fight,
}


def evaluate(st: Stats, minute_for_targets: Optional[int] = None) -> Fight:
    minute = st.minute if minute_for_targets is None else minute_for_targets
    level = st.level if minute_for_targets is None else level_at_minute(minute)
    front = front_stats(level, minute)
    carry = carry_stats(level, minute)
    # Sandbox calls pass minute 18 with the stats' own level.
    if minute_for_targets is not None:
        front = front_stats(st.level, minute_for_targets)
        carry = carry_stats(st.level, minute_for_targets)
    fight = FIGHTERS[st.champ](st, front, carry)
    use = getattr(fight, "_st", st)
    heal, shield = item_heal_layer(
        use, fight.heal, fight.shield, fight.pre, FIGHT_S, fight.kit_dumps
    )
    fight.heal = heal
    fight.shield = shield
    return fight


def lane_kit_heal_per_min(st: Stats) -> float:
    """On-demand kit healing across 60s of lane, before items.

    Assumes the ally is missing HP often enough to accept 70% of casts.
    Ultimates are not part of lane healing.
    """
    ap = st.ap
    ah = st.ah
    if st.champ == "Soraka":
        ranks = ability_ranks(st.level, "WQE")
        if not ranks["W"]:
            return 0
        heal = rank_value([0, 50, 85, 120, 155], ranks["W"]) + 0.55 * ap
        cd = haste_cd(max(2.0, rank_value([0, 7, 6, 5, 4], ranks["W"]) - 1.0), ah)
        return (60 / cd) * 0.70 * heal
    if st.champ == "Sona":
        ranks = ability_ranks(st.level, "WQE")
        if not ranks["W"]:
            return 0
        heal = rank_value([0, 45, 60, 75, 90], ranks["W"]) + 0.20 * ap
        cdr = 0.02 + 0.18 * (st.level - 1) / 14
        cd = haste_cd(10 * (1 - cdr), ah)
        return (60 / cd) * 0.75 * heal
    if st.champ == "Nami":
        ranks = ability_ranks(st.level, "WEQ")
        if not ranks["W"]:
            return 0
        heal = rank_value([0, 55, 85, 115, 145], ranks["W"]) + 0.30 * ap
        decay = 0.15 - 0.075 * ap / 100
        ally = heal * (0.55 + 0.45 * (1 - decay))
        cd = haste_cd(10, ah)
        return (60 / cd) * 0.70 * ally
    if st.champ == "Yuumi":
        ranks = yuumi_ranks(st.level)
        passive_cd = 12 - (12 - 8) * (st.level - 1) / 14
        passive = 67 + (165 - 67) * (st.level - 1) / 14 + 0.25 * ap
        return (60 / haste_cd(passive_cd, 0)) * 0.45 * passive
    if st.champ == "Seraphine":
        ranks = ability_ranks(st.level, "WEQ")
        if not ranks["W"]:
            return 0
        ratio = 0.06 + 0.01 * ap / 100
        # Lane ally is only missing ~25% HP, one ally, so no +50% amp.
        heal = ratio * 0.25 * carry_stats(st.level, st.minute)[0]
        cd = haste_cd(rank_value([0, 23, 22, 21, 20], ranks["W"]), ah)
        return (60 / cd) * 0.55 * heal
    return 0.0


def lane_pre_per_min(st: Stats) -> float:
    """Champion damage dealt to champions per minute of lane. Rough, for Helia."""
    ap = _ap_fight(st) if st.blackfire else st.ap
    if st.champ == "Brand":
        ranks = ability_ranks(st.level, "WQE")
        w = rank_value([0, 70, 120, 170, 220], ranks["W"]) + 0.55 * ap
        cd = haste_cd(rank_value([0, 9.5, 9, 8.5, 8], ranks["W"]) or 9, st.ah)
        casts = 60 / cd
        hp, _ = carry_stats(st.level, st.minute)
        # W hit rate in lane is worse than in a stunned fight. Partial blaze.
        return casts * 0.48 * w * 1.15 + casts * 0.30 * 0.02 * hp
    if st.champ == "Soraka":
        ranks = ability_ranks(st.level, "WQE")
        q = rank_value([0, 60, 110, 160, 210], ranks["Q"]) + 0.40 * ap
        cd = haste_cd(rank_value([0, 7, 6, 5, 4], ranks["Q"]) or 7, st.ah)
        return (60 / cd) * 0.45 * q
    if st.champ == "Sona":
        ranks = ability_ranks(st.level, "WQE")
        q = rank_value([0, 40, 80, 120, 160], ranks["Q"]) + 0.40 * ap
        return (60 / haste_cd(8, st.ah)) * 0.70 * q * 1.4
    if st.champ == "Nami":
        ranks = ability_ranks(st.level, "WEQ")
        dmg = rank_value([0, 65, 120, 175, 230], ranks["W"]) + 0.50 * ap
        return (60 / haste_cd(10, st.ah)) * 0.55 * dmg
    if st.champ == "Yuumi":
        ranks = yuumi_ranks(st.level)
        q = rank_value([0, 100, 160, 220, 280, 340], ranks["Q"]) + 0.35 * ap
        return (60 / haste_cd(5, st.ah)) * 0.42 * q
    if st.champ == "Seraphine":
        ranks = ability_ranks(st.level, "WEQ")
        q = rank_value([0, 60, 75, 90, 105], ranks["Q"]) + 0.45 * ap
        cd = haste_cd(rank_value([0, 11, 9, 7, 5], ranks["Q"]) or 9, st.ah)
        return (60 / cd) * 0.50 * q
    return 0.0


def lane_heal_per_min(st: Stats) -> float:
    kit = lane_kit_heal_per_min(st)
    # Best Friend HSP for Yuumi, same rule as fights.
    hsp = st.hsp
    if st.champ == "Yuumi":
        ranks = yuumi_ranks(st.level)
        hsp += [0, 0.06, 0.07, 0.08, 0.09][max(1, ranks["E"])] + 0.02 * st.ap / 100
    heal = kit * hsp
    combat_s = 60 * 0.25
    if st.diadem:
        heal += 0.008 * st.mana * combat_s * 0.92 * hsp
    if st.helia:
        pre = lane_pre_per_min(st)
        if st.diadem:
            # Combat seconds can each spend a shard, cap per second.
            heal += min(helia_cap(st.level) * combat_s, 0.30 * pre) * hsp
        elif kit > 0:
            dumps = max(1, int(kit and (60 / 8)))
            heal += helia_stored(pre, st.level, 60, False, dumps) * hsp
    if st.harmonic:
        heal *= 1.30
    return heal


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def finished_names(names: List[str]) -> List[str]:
    skip = {
        "Boots of Speed", "Ring of Revelation", "Amplifying Tome", "Ruby Crystal",
        "Forbidden Idol", "Tear of the Goddess", "Kindlegem", "Blasting Wand",
        "Giant's Belt", "Fated Ashes", "Haunting Guise", "Lost Chapter",
        "Bandleglass Mirror", "Aether Wisp", "Needlessly Large Rod",
        "Fiendish Codex",
    }
    return [n for n in names if n not in skip]


def run() -> Tuple[str, dict]:
    lines: List[str] = []
    A = lambda s="": lines.append(s)

    ardent_path = BUILD_PATHS[ENCHANTER_BUILD]
    mikael_path = BUILD_PATHS["Brand Diadem Helia Mikael"]

    A("=" * 78)
    A("BRAND SUPPORT — HEAL AND DAMAGE (Wild Rift patch 7.3b)")
    A("Scythe → Ionian → Circlet/Diadem → Helia → Harmonic → Ardent or Mikael")
    A("8-second fight, ultimate up. One frontline + one carry. No runes.")
    A("=" * 78)
    A("")
    A("HOW THE ITEMS INTERACT ON BRAND")
    A("  Brand has no heal or shield. Helia, Harmonic and Ardent do nothing")
    A("  until something heals or shields an ally.")
    A("  Diadem is that trigger: while Brand is in combat it heals the lowest")
    A("  ally for 0.8% max mana per second, and that heal spends Helia shards.")
    A("  Helia stores 30% of pre-mitigation champion damage, capped at 80–250")
    A("  per spend. Diadem spends every second, so the cap is per second.")
    A("  Before Diadem, shards sit in the item and expire as unused healing.")
    A("  Font of Life would spend them on the Q stun. It is not in this run.")
    A("  Harmony on 7.3b is the 7.3a nerf: +0.25% of max mana as heal/shield power.")
    A("")

    online = circlet_online_minute(ardent_path)
    A("SUPPORT GOLD AND WHEN THE USER BUILD TURNS ON")
    A(f"  {'Min':>3}  {'Gold':>6}  {'Lvl':>3}  {'CarryHP':>8}  {'FrontHP':>8}  Finished items")
    timeline = []
    for m in range(1, GAME_MINUTES + 1):
        st = stats_at("Brand", ardent_path, m)
        c_hp, _ = carry_stats(st.level, m)
        f_hp, _ = front_stats(st.level, m)
        done = " · ".join(finished_names(st.names))
        if st.diadem:
            done = done.replace("Diadem of Songs", "DIADEM")
        A(f"  {m:>3}  {st.gold:>6}  {st.level:>3}  {c_hp:>8.0f}  {f_hp:>8.0f}  {done}")
        timeline.append({
            "minute": m,
            "gold": st.gold,
            "level": st.level,
            "items": st.names,
            "ap": round(st.ap, 1),
            "mana": round(st.mana, 1),
            "hsp": round(st.hsp, 3),
            "diadem": st.diadem,
            "charges": st.charges,
        })
    diadem_min = next(row["minute"] for row in timeline if row["diadem"])
    ardent_min = next((m for m in range(1, GAME_MINUTES + 1)
                       if "Ardent Censer" in stats_at("Brand", ardent_path, m).names), None)
    mikael_min = next((m for m in range(1, GAME_MINUTES + 1)
                       if "Mikael's Blessing" in stats_at("Brand", mikael_path, m).names), None)
    A("")
    A(f"  Circlet bought: ~{online}:00. Mana Charge at {CHARGE_PER_MIN}/min (cap is 12/min).")
    A(f"  Diadem transforms: ~{diadem_min}:00. At the 12/min cap it would be ~4 minutes earlier.")
    A(f"  Ardent finishes: {ardent_min if ardent_min else 'not in 22:00'}.")
    A(f"  Mikael's finishes: {mikael_min if mikael_min else 'not in 22:00'}.")
    A("  A 20-minute game ends on Harmonic Echo plus a Forbidden Idol component.")
    A("")

    # ---- healing comparison on the shared enchanter path ----
    A("-" * 78)
    A("HEALING VS ENCHANTERS — same items as Brand (Ardent path)")
    A("Ally HP restored in the 8s fight. Shields listed separately.")
    A("-" * 78)
    heal_rows = []
    for minute in (10, 14, 18, 22):
        A(f"  [{minute}:00]")
        A(f"  {'Champ':<12} {'Heal':>8} {'Shield':>8} {'Protected':>10} {'Lane/min':>9}  AP   Mana   HSP")
        for champ in HEAL_CHAMPS:
            st = stats_at(champ, ardent_path, minute)
            fight = evaluate(st)
            lane = lane_heal_per_min(st)
            protected = fight.heal + fight.shield
            heal_rows.append({
                "minute": minute, "champ": champ,
                "heal": round(fight.heal), "shield": round(fight.shield),
                "protected": round(protected), "lane_per_min": round(lane),
                "ap": round(st.ap, 1), "mana": round(st.mana), "hsp": round(st.hsp, 3),
                "diadem": st.diadem, "items": finished_names(st.names),
            })
            A(f"  {champ:<12} {fight.heal:>8.0f} {fight.shield:>8.0f} {protected:>10.0f} "
              f"{lane:>9.0f}  {st.ap:>4.0f}  {st.mana:>4.0f}  {(st.hsp - 1) * 100:>4.0f}%")
        A("")

    # ---- damage ----
    A("-" * 78)
    A("DAMAGE — post-mitigation on frontline + carry in the same 8s fight")
    A("-" * 78)
    damage_builds = [
        ("Brand", "Brand Diadem Helia Ardent"),
        ("Brand", "Brand Diadem Helia Mikael"),
        ("Brand", "Brand Liandry Rylai Mandate"),
        ("Brand", "Brand Blackfire Liandry Rylai"),
        ("Brand", "Brand Liandry Mandate Rylai"),
        ("Zyra", "Zyra Liandry Rylai"),
        ("Morgana", "Morgana Liandry Rylai"),
        ("Lux", "Lux Mandate Deathcap"),
        ("Seraphine", "Brand Diadem Helia Ardent"),
    ]
    dmg_rows = []
    for minute in (10, 14, 18, 22):
        A(f"  [{minute}:00]")
        A(f"  {'Build':<34} {'Total':>8} {'Front':>8} {'Carry':>8} {'AP':>6}")
        for champ, key in damage_builds:
            st = stats_at(champ, BUILD_PATHS[key], minute)
            fight = evaluate(st)
            total = fight.post_front + fight.post_carry
            label = key if champ == "Brand" else f"{champ} ({key})"
            dmg_rows.append({
                "minute": minute, "label": label, "champ": champ,
                "total": round(total), "front": round(fight.post_front),
                "carry": round(fight.post_carry), "pre": round(fight.pre),
                "ap": round(st.ap, 1), "items": finished_names(st.names),
            })
            A(f"  {label:<34} {total:>8.0f} {fight.post_front:>8.0f} {fight.post_carry:>8.0f} {st.ap:>6.0f}")
        A("")

    # ---- sandbox: the 6-item sheet, soul-forge done, fixed level 13 fight ----
    A("-" * 78)
    A("FULL 6-ITEM SHEET at level 13 (soul-forge capped, Diadem transformed)")
    A("Targets: the 18:00 carry and frontline. This ignores the gold clock.")
    A("-" * 78)
    sand_heal = []
    A(f"  {'Champ / 6th item':<28} {'Heal':>8} {'Shield':>8} {'Protected':>10} {'Damage':>8} {'AP':>6} {'Mana':>6}")
    for champ in HEAL_CHAMPS:
        for sixth, key in (("Ardent", ENCHANTER_BUILD), ("Mikael", "Brand Diadem Helia Mikael")):
            if champ != "Brand" and sixth == "Mikael":
                continue
            st = sandbox_stats(champ, key, 13)
            fight = evaluate(st, minute_for_targets=18)
            total = fight.post_front + fight.post_carry
            label = f"{champ} {sixth}" if champ == "Brand" else champ
            sand_heal.append({
                "label": label, "heal": round(fight.heal), "shield": round(fight.shield),
                "protected": round(fight.heal + fight.shield), "damage": round(total),
                "ap": round(st.ap, 1), "mana": round(st.mana), "hsp": round(st.hsp, 3),
            })
            A(f"  {label:<28} {fight.heal:>8.0f} {fight.shield:>8.0f} "
              f"{fight.heal + fight.shield:>10.0f} {total:>8.0f} {st.ap:>6.0f} {st.mana:>6.0f}")
    A("")
    A(f"  {'Damage build, same sheet':<34} {'Damage':>8} {'Front':>8} {'Carry':>8} {'AP':>6}")
    sand_dmg = []
    for champ, key in damage_builds:
        if key == "Brand Diadem Helia Mikael":
            continue
        st = sandbox_stats(champ, key, 13)
        # Damage builds have no Diadem; sandbox_stats only swaps Circlet.
        fight = evaluate(st, minute_for_targets=18)
        total = fight.post_front + fight.post_carry
        label = key if champ == "Brand" else f"{champ}"
        sand_dmg.append({
            "label": label, "damage": round(total),
            "front": round(fight.post_front), "carry": round(fight.post_carry),
            "ap": round(st.ap, 1),
        })
        A(f"  {label:<34} {total:>8.0f} {fight.post_front:>8.0f} {fight.post_carry:>8.0f} {st.ap:>6.0f}")

    # Verdict numbers from the 22:00 economy row and the sandbox.
    def row(rows, **kw):
        for r in rows:
            if all(r.get(k) == v for k, v in kw.items()):
                return r
        raise KeyError(kw)

    b22 = row(heal_rows, minute=22, champ="Brand")
    s22 = row(heal_rows, minute=22, champ="Soraka")
    n22 = row(heal_rows, minute=22, champ="Nami")
    y22 = row(heal_rows, minute=22, champ="Yuumi")
    so22 = row(heal_rows, minute=22, champ="Sona")
    se22 = row(heal_rows, minute=22, champ="Seraphine")
    b10 = row(heal_rows, minute=10, champ="Brand")
    s10 = row(heal_rows, minute=10, champ="Soraka")

    brand_ench_22 = row(dmg_rows, minute=22, label="Brand Diadem Helia Ardent")
    brand_lia_22 = row(dmg_rows, minute=22, label="Brand Liandry Rylai Mandate")
    brand_bf_22 = row(dmg_rows, minute=22, label="Brand Blackfire Liandry Rylai")
    zyra_22 = row(dmg_rows, minute=22, label="Zyra (Zyra Liandry Rylai)")
    morg_22 = row(dmg_rows, minute=22, label="Morgana (Morgana Liandry Rylai)")
    lux_22 = row(dmg_rows, minute=22, label="Lux (Lux Mandate Deathcap)")

    sand_brand = next(r for r in sand_heal if r["label"] == "Brand Ardent")
    sand_brand_m = next(r for r in sand_heal if r["label"] == "Brand Mikael")
    sand_soraka = next(r for r in sand_heal if r["label"] == "Soraka")
    sand_lia = next(r for r in sand_dmg if r["label"] == "Brand Liandry Rylai Mandate")
    sand_zyra = next(r for r in sand_dmg if r["label"] == "Zyra")

    A("")
    A("-" * 78)
    A("VERDICT")
    A("-" * 78)
    helia_idle = next(
        (r for r in heal_rows if r["champ"] == "Brand" and r["minute"] >= 14 and r["heal"] == 0),
        None,
    )
    A("  Healing: this Brand build does not replace a healer.")
    A(f"  At 10:00 Brand's fight heal is {b10['heal']} (no Diadem yet) against Soraka's {s10['heal']}.")
    if helia_idle:
        A(f"  At {helia_idle['minute']}:00 Helia is finished and Brand still heals {helia_idle['heal']}.")
        A("  Shards have nowhere to go until Diadem, or Mikael's, actually heals an ally.")
    A(f"  At 22:00 on the gold clock, Brand restores {b22['heal']} HP in the 8s fight")
    A(f"  (Soraka {s22['heal']}, Nami {n22['heal']}, Yuumi {y22['heal']}, Sona heal {so22['heal']} + shield {so22['shield']},")
    A(f"  Seraphine heal {se22['heal']} + shield {se22['shield']}).")
    if s22["heal"]:
        A(f"  That is {100 * b22['heal'] / s22['heal']:.0f}% of Soraka. Most of Brand's number is Helia")
        A("  turning the damage he just dealt into healing, and it stops the moment he stops hitting.")
    if n22["heal"]:
        A(f"  On raw fight heal he is {100 * b22['heal'] / n22['heal']:.0f}% of Nami and near Yuumi.")
        A("  Count shields and he falls behind Seraphine, Sona and Yuumi. He has no shield of his own.")
    A(f"  Lane heal/min at 22:00, ultimates excluded: Brand {b22['lane_per_min']}, "
      f"Soraka {s22['lane_per_min']}, Nami {n22['lane_per_min']}.")
    A("  Lane assumes heals are cast on cooldown about 70% of the minute. Soraka's regen at")
    A("  six items can actually pay for that. Brand's lane heal is only the Diadem ticks")
    A("  during trades, plus Helia on W poke.")
    A("  Sona's mana growth is 4.9, so her Diadem tick is the small one. Her shield is the kit.")
    A("")
    A("  Ardent vs Mikael's on the full 6-item sheet (level 13, gold ignored):")
    A(f"  Ardent: heal {sand_brand['heal']}, damage {sand_brand['damage']}, {sand_brand['ap']:.0f} AP.")
    A(f"  Mikael: heal {sand_brand_m['heal']}, damage {sand_brand_m['damage']}, {sand_brand_m['ap']:.0f} AP.")
    if sand_brand["heal"] >= sand_brand_m["heal"]:
        A("  Ardent heals more. 50 AP feeds Helia, and 8% heal/shield power multiplies every tick.")
        A("  Mikael's 150–250 heal is one cast per 75s. Buy it when you need the cleanse.")
    else:
        gap = sand_brand_m["heal"] - sand_brand["heal"]
        A(f"  Mikael's fight heal is higher by {gap:.0f}, because the active lands in this fight.")
        A("  That active is on a 75s cooldown. Ardent's 50 AP and 8% heal/shield power are up every fight,")
        A(f"  and Ardent deals {sand_brand['damage'] - sand_brand_m['damage']:.0f} more damage.")
        A("  Buy Mikael's for the cleanse. Buy Ardent if the carry auto-attacks and you want the higher damage.")
    A("  On the 22-minute clock Ardent only just finishes, and Mikael's is ~40 gold short.")
    A("  The 6th item is not what decides the game. Diadem is.")
    A("")
    A("  Damage: the enchanter path gives up the reason to pick Brand.")
    A(f"  At 22:00, Diadem Brand deals {brand_ench_22['total']}.")
    A(f"  Liandry → Rylai → Mandate deals {brand_lia_22['total']}.")
    A(f"  Blackfire → Liandry → Rylai deals {brand_bf_22['total']}.")
    if brand_ench_22["total"]:
        A(f"  Liandry Brand is {100 * brand_lia_22['total'] / brand_ench_22['total'] - 100:.0f}% more damage on this fight.")
    A(f"  Same minute: Zyra {zyra_22['total']}, Morgana {morg_22['total']}, Lux {lux_22['total']}.")
    A("  Liandry is the gap: 2% max HP per second on the frontline, refreshed by Blaze,")
    A("  plus 7% magic penetration. Helia's 40 AP does not replace that.")
    A(f"  Full sheet, same targets: Ardent Brand {sand_brand['damage']}, Liandry Brand {sand_lia['damage']}, Zyra {sand_zyra['damage']}.")
    A("")
    A("  What this build is:")
    A("  From 0:00 to the Diadem minute, a mage support with no Liandry and no heal.")
    A("  After Diadem, a combat heal that can pass Nami's fight total and still")
    A("  sit at about 40% of Soraka, with no shield and with lane healing well behind.")
    A("  Damage lands next to Morgana and Lux and well behind Liandry Brand and Zyra.")
    A("  Harmonic Echo only copies a heal. Brand does not have one until Diadem.")
    A("  Pick Liandry → Rylai when Brand is in the game to deal damage.")
    A("  Pick Soraka, Nami, Yuumi or Seraphine when the slot has to heal.")
    A("=" * 78)

    payload = {
        "meta": {
            "champion": "Brand",
            "role": "Support",
            "patch": "7.3b",
            "game_minutes": GAME_MINUTES,
            "charge_per_min": CHARGE_PER_MIN,
            "diadem_minute": diadem_min,
            "circlet_minute": online,
            "ardent_minute": ardent_min,
            "mikael_minute": mikael_min,
            "assumptions": [
                "Diadem's per-second heal counts as healing an ally and spends Helia.",
                "Helia is 30% of pre-mitigation champion damage, cap 80-250 by level, per spend.",
                "Harmony is 0.25% max mana after the 7.3a nerf.",
                "Harmonic adds 30% to heals and 35% to shields.",
                "No runes (Font of Life would be Brand's only pre-Diadem trigger).",
                "Support gold matches the Zyra sim. Level 13 at 20:00.",
                "Boots of Mana and Liandry use the repo's 7.2 numbers; 7.3b did not retune them.",
                "Tear of the Goddess component mana is modeled as 200.",
            ],
        },
        "timeline_ardent_brand": timeline,
        "healing": heal_rows,
        "damage": dmg_rows,
        "sandbox_healing": sand_heal,
        "sandbox_damage": sand_dmg,
    }
    return "\n".join(lines), payload


def main() -> None:
    report, payload = run()
    print(report)
    out = "/workspace/brand-support-sim"
    with open(f"{out}/report.txt", "w", encoding="utf-8") as f:
        f.write(report + "\n")
    with open(f"{out}/results.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print(f"\nWrote {out}/report.txt and {out}/results.json")

    # Guards so a broken formula fails the run.
    heals = {(r["minute"], r["champ"]): r for r in payload["healing"]}
    dmgs = {(r["minute"], r["label"]): r for r in payload["damage"]}
    assert heals[(10, "Brand")]["heal"] < heals[(10, "Soraka")]["heal"]
    assert heals[(22, "Brand")]["heal"] < heals[(22, "Soraka")]["heal"]
    assert dmgs[(22, "Brand Liandry Rylai Mandate")]["total"] > dmgs[(22, "Brand Diadem Helia Ardent")]["total"]
    assert payload["meta"]["diadem_minute"] >= 14
    # Harmony is a few percent of max mana, not a 4x multiplier.
    h22 = next(r for r in payload["healing"] if r["minute"] == 22 and r["champ"] == "Brand")
    assert 1.10 <= h22["hsp"] <= 1.45
    brand_sand = next(r for r in payload["sandbox_healing"] if r["label"] == "Brand Ardent")
    mikael_sand = next(r for r in payload["sandbox_healing"] if r["label"] == "Brand Mikael")
    assert brand_sand["damage"] > mikael_sand["damage"]


if __name__ == "__main__":
    main()
