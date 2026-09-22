#!/usr/bin/env python3
"""
Wild Rift 7.3 — Top 5 supports that benefit from the patch AND fit GameSir/MB03 + D-pad.

Patch 7.3 (2026-09-22): crit 175%→200%, AS cap 2.5→3, ADC item overhaul,
enchanter makeover (Helia / Ardent / Diadem / Harmonic Echo), tank CC item
Yordle Trap now grants ally attack speed.

Pad = user's layout:
  MB03: hold-release / Q-tap / 2–4 button combos (see mb03-tuong-theo-lane)
  D-pad: ↑ scoreboard  ↓ recall  ← minion  → turret
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple
import json
import os

GAME_MINUTES = 20
CRIT_72 = 1.75
CRIT_73 = 2.00
AS_CAP_72 = 2.5
AS_CAP_73 = 3.0

# ---------------------------------------------------------------------------
# Gold / level curves
# ---------------------------------------------------------------------------


def support_gold(m: int) -> int:
    """Typical WR support (tribute + souls), ~9.8k at 20."""
    if m <= 0:
        return 500
    total = 500
    for t in range(1, m + 1):
        if t <= 4:
            total += 280
        elif t <= 10:
            total += 430
        else:
            total += 520
    return total


def adc_gold(m: int) -> int:
    """Solo CS botlaner, ~13.5k at 20."""
    if m <= 0:
        return 500
    total = 500
    for t in range(1, m + 1):
        if t <= 4:
            total += 380
        elif t <= 10:
            total += 620
        else:
            total += 740
    return total


def support_level(m: int) -> int:
    table = {
        1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7, 7: 8, 8: 8,
        9: 9, 10: 10, 11: 10, 12: 11, 13: 11, 14: 12,
        15: 12, 16: 13, 17: 13, 18: 14, 19: 14, 20: 15,
    }
    return table.get(m, min(15, 1 + m))


def adc_level(m: int) -> int:
    table = {
        1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7, 7: 8, 8: 9,
        9: 10, 10: 10, 11: 11, 12: 12, 13: 12, 14: 13,
        15: 13, 16: 14, 17: 14, 18: 15, 19: 15, 20: 16,
    }
    return table.get(m, min(16, 1 + m))


def ah_mult(ah: float) -> float:
    return 1.0 + ah / 100.0


# ---------------------------------------------------------------------------
# 7.3 items (official patch notes)
# ---------------------------------------------------------------------------

ITEMS = {
    "Spectral Sickle": {"cost": 400, "class": "start"},
    "Relic Shield": {"cost": 400, "class": "start"},
    "Black Mist Scythe": {"cost": 400, "class": "start"},
    "Bulwark of the Mountain": {"cost": 400, "class": "start"},
    "Boots of Speed": {"cost": 400},
    "Ionian Boots": {"cost": 900, "ah": 15},
    "Plated Steelcaps": {"cost": 1000},
    "Tear of the Goddess": {"cost": 400, "mana": 240},
    "Forbidden Idol": {"cost": 700, "hsp": 0.06},
    "Bandleglass Mirror": {"cost": 900, "ap": 20, "ah": 10},
    "Kindlegem": {"cost": 1000, "hp": 200, "ah": 10},
    "Echoes of Helia": {
        "cost": 2400, "ap": 40, "ah": 20, "hp": 200, "helia": True,
    },
    "Ardent Censer": {
        "cost": 2400, "ap": 50, "hsp": 0.08, "ardent": True,
    },
    "Whispering Circlet": {
        "cost": 2400, "hp": 200, "mana": 500, "hsp": 0.08, "circlet": True,
    },
    "Diadem of Songs": {
        "cost": 2400, "hp": 200, "mana": 1200, "hsp": 0.08, "diadem": True,
    },
    "Harmonic Echo": {
        "cost": 2500, "ap": 40, "ah": 20, "hp": 200, "harmonic": True,
    },
    "Staff of Flowing Waters": {
        "cost": 2400, "ap": 50, "hsp": 0.08, "ah": 10, "flowing": True,
    },
    "Redemption": {"cost": 2450, "ap": 40, "hsp": 0.08, "ah": 10},
    "Imperial Mandate": {"cost": 2600, "ap": 60, "ah": 20, "mandate": True},
    "Yordle Trap": {"cost": 2400, "hp": 200, "armor": 20, "mr": 20, "yordle": True},
    "Zeke's Convergence": {"cost": 2400, "hp": 300, "armor": 25, "mr": 25, "ah": 10, "zeke": True},
    "Knight's Vow": {"cost": 2300, "hp": 250},
    "Mantle of the Twelfth Hour": {"cost": 2550, "hp": 600, "ah": 20},
    "Radiant Virtue": {"cost": 2650, "armor": 30, "mr": 30, "ah": 10},
}


def buy_order_owned(gold: int, order: List[str], start: str) -> List[str]:
    """Greedy complete-item buyer. Start item is free after first back."""
    owned = [start]
    spent = 0
    # First back upgrades start item conceptually; ignore upgrade gold (souls).
    for name in order:
        cost = ITEMS[name]["cost"]
        if spent + cost <= gold:
            owned.append(name)
            spent += cost
        else:
            break
    return owned


def item_flags(owned: List[str]) -> Dict[str, float]:
    ap = ah = hsp = mana = 0.0
    helia = ardent = diadem = circlet = harmonic = flowing = mandate = False
    yordle = zeke = False
    for name in owned:
        it = ITEMS.get(name, {})
        ap += it.get("ap", 0)
        ah += it.get("ah", 0)
        hsp += it.get("hsp", 0)
        mana += it.get("mana", 0)
        helia = helia or it.get("helia", False)
        ardent = ardent or it.get("ardent", False)
        diadem = diadem or it.get("diadem", False)
        circlet = circlet or it.get("circlet", False)
        harmonic = harmonic or it.get("harmonic", False)
        flowing = flowing or it.get("flowing", False)
        mandate = mandate or it.get("mandate", False)
        yordle = yordle or it.get("yordle", False)
        zeke = zeke or it.get("zeke", False)
    if circlet and not diadem:
        # Harmony: +0.5% HSP per 100 mana (500 + ~stacks). Mid-charge ~800 mana.
        hsp += 0.005 * 8.0
        mana += 300
    if diadem:
        hsp += 0.005 * 12.0  # 1200 mana → +6% HSP
    return {
        "ap": ap, "ah": ah, "hsp": hsp, "mana": mana,
        "helia": helia, "ardent": ardent, "diadem": diadem,
        "harmonic": harmonic, "flowing": flowing, "mandate": mandate,
        "yordle": yordle, "zeke": zeke,
    }


# ---------------------------------------------------------------------------
# Generic 7.3 crit ADC (Jinx / Xayah / MF composite)
# ---------------------------------------------------------------------------


def adc_base(m: int) -> Tuple[float, float, float, List[str]]:
    """Return (AD, AS, crit, items) for a crit marksman at minute m."""
    lvl = adc_level(m)
    gold = adc_gold(m)
    ad = 60 + 3.4 * (lvl - 1)
    as_base = 0.66 + 0.022 * (lvl - 1)
    crit = 0.0
    items: List[str] = []
    spent = 0
    bonus_as = 0.0
    # Yun Tal Wildarrows 3100: 50 AD, 25% AS, 0→25% crit via stacks
    if gold >= 1800:
        # Noonquiver 1300 on the way
        if gold >= 1300:
            items.append("Noonquiver")
            spent += 1300
            ad += 20
            crit += 0.15
    if gold >= 3100:
        # Finish Yun Tal: replace Noonquiver (20 AD / 15% crit) with 50 AD / 25% AS / stacked crit.
        items.append("Yun Tal Wildarrows")
        spent = 3100
        ad += 30
        bonus_as += 0.25
        # Practice Makes Perfect: 0.2% crit per ranged auto, cap 25%.
        # After the item (~8:00) ADC hits ~1/s in lane → ~12% by 10:00, cap ~14:00.
        stacks = min(0.25, 0.002 * max(0, (m - 7) * 50))
        crit = stacks  # Yun Tal listed crit is 0%; stacks replace Noonquiver's 15%
    if gold >= 4000:
        items.append("Berserker's Greaves")
        spent += 900
        bonus_as += 0.40
    if gold >= 7400:
        items.append("Infinity Edge")
        spent += 3400
        ad += 65
        crit += 0.25
    if gold >= 10050:
        items.append("Rapid Firecannon")
        spent += 2650
        crit += 0.25
        bonus_as += 0.40

    as_total = as_base * (1.0 + bonus_as)
    return ad, as_total, min(0.85, crit), items


def auto_dps(ad: float, attack_speed: float, crit: float, onhit: float, crit_dmg: float, as_cap: float) -> float:
    as_clamped = min(as_cap, attack_speed)
    per_hit = ad * ((1.0 - crit) + crit * crit_dmg) + onhit
    return as_clamped * per_hit


# ---------------------------------------------------------------------------
# Champion kits
# ---------------------------------------------------------------------------

@dataclass
class PadProfile:
    """Controller / D-pad fitness. Higher pad_score = easier on MB03 + D-pad."""
    style: str           # qspam | targeted | combo | hold | hook | charge
    aim: float           # 0 = no aim, 1 = skillshot-heavy
    combo_buttons: int   # 1–4 sequential
    relic_dpad: bool     # Relic Shield execute uses D-pad ← minion
    notes: str
    taught: bool = False  # already in user's MB03 docs

    @property
    def score(self) -> float:
        # Base by style (user's three MB03 strengths).
        style_pts = {
            "qspam": 92.0,
            "targeted": 90.0,
            "hold": 91.0,
            "combo": 88.0,
            "charge": 90.0,
            "hook": 78.0,
        }[self.style]
        aim_pen = self.aim * 28.0
        combo_pen = max(0, self.combo_buttons - 2) * 4.0
        relic_bonus = 4.0 if self.relic_dpad else 0.0  # D-pad ← is actually useful
        taught_bonus = 3.0 if self.taught else 0.0
        return max(35.0, min(98.0, style_pts - aim_pen - combo_pen + relic_bonus + taught_bonus))


@dataclass
class Champ:
    key: str
    name: str
    name_vi: str
    klass: str  # enchanter | tank | pick
    wrf_tier: str
    start: str
    build: List[str]
    pad: PadProfile
    # Kit hooks used by the combat model
    kit: str


CHAMPS: List[Champ] = [
    Champ(
        "sona", "Sona", "Sona", "enchanter", "S",
        "Spectral Sickle",
        ["Ionian Boots", "Tear of the Goddess", "Echoes of Helia", "Whispering Circlet", "Ardent Censer"],
        PadProfile("qspam", aim=0.18, combo_buttons=1, relic_dpad=False,
                   notes="QWE tự buff, không nhắm. R đường thẳng. MB03 xả Q."),
        "sona",
    ),
    Champ(
        "lulu", "Lulu", "Lulu", "enchanter", "A",
        "Relic Shield",
        ["Ionian Boots", "Ardent Censer", "Harmonic Echo", "Redemption"],
        PadProfile("targeted", aim=0.22, combo_buttons=1, relic_dpad=True,
                   notes="W/E/R lock đồng đội. Q optional. D-pad ← Relic."),
        "lulu",
    ),
    Champ(
        "milio", "Milio", "Milio", "enchanter", "A",
        "Spectral Sickle",
        ["Ionian Boots", "Echoes of Helia", "Harmonic Echo", "Ardent Censer"],
        PadProfile("targeted", aim=0.35, combo_buttons=1, relic_dpad=False,
                   notes="E/W lock đồng đội (tether). Q nảy — khó hơn, không bắt buộc."),
        "milio",
    ),
    Champ(
        "leona", "Leona", "Leona", "tank", "S",
        "Relic Shield",
        ["Plated Steelcaps", "Yordle Trap", "Mantle of the Twelfth Hour", "Radiant Virtue"],
        PadProfile("combo", aim=0.28, combo_buttons=2, relic_dpad=True, taught=True,
                   notes="E→Q hai nút (đã dạy MB03). D-pad ← Relic, → trụ plating."),
        "leona",
    ),
    Champ(
        "braum", "Braum", "Braum", "tank", "S",
        "Relic Shield",
        ["Plated Steelcaps", "Knight's Vow", "Yordle Trap", "Radiant Virtue"],
        PadProfile("hold", aim=0.25, combo_buttons=1, relic_dpad=True,
                   notes="Giữ E = gồng MB03. W nhảy đồng đội. Q đường thẳng."),
        "braum",
    ),
    Champ(
        "nautilus", "Nautilus", "Nautilus", "tank", "A",
        "Relic Shield",
        ["Plated Steelcaps", "Yordle Trap", "Mantle of the Twelfth Hour", "Knight's Vow"],
        PadProfile("hook", aim=0.40, combo_buttons=2, relic_dpad=True, taught=True,
                   notes="Q tap móc (đã dạy). R lock tướng. Đừng móc xuyên wave — D-pad ← tránh lính."),
        "nautilus",
    ),
    Champ(
        "alistar", "Alistar", "Alistar", "tank", "B",
        "Relic Shield",
        ["Plated Steelcaps", "Yordle Trap", "Zeke's Convergence", "Knight's Vow"],
        PadProfile("combo", aim=0.12, combo_buttons=2, relic_dpad=True, taught=True,
                   notes="W→Q hai nút (đã dạy). Ít aim. 7.3 Yordle Trap mới cho AS."),
        "alistar",
    ),
    Champ(
        "seraphine", "Seraphine", "Seraphine", "enchanter", "A",
        "Spectral Sickle",
        ["Ionian Boots", "Echoes of Helia", "Harmonic Echo", "Staff of Flowing Waters"],
        PadProfile("qspam", aim=0.32, combo_buttons=1, relic_dpad=False,
                   notes="Q vòng gần, W aura. Helia tốt. R skillshot."),
        "seraphine",
    ),
    Champ(
        "karma", "Karma", "Karma", "enchanter", "A",
        "Spectral Sickle",
        ["Ionian Boots", "Echoes of Helia", "Harmonic Echo", "Redemption"],
        PadProfile("qspam", aim=0.42, combo_buttons=2, relic_dpad=False,
                   notes="E khiên ADC + Helia dump. Q mantra phải nhắm."),
        "karma",
    ),
    Champ(
        "nami", "Nami", "Nami", "enchanter", "S",
        "Spectral Sickle",
        ["Ionian Boots", "Ardent Censer", "Harmonic Echo", "Imperial Mandate"],
        PadProfile("qspam", aim=0.78, combo_buttons=2, relic_dpad=False,
                   notes="W bounce + Ardent/Mandate rất 7.3. Bong bóng Q khó analog."),
        "nami",
    ),
    Champ(
        "pyke", "Pyke", "Pyke", "pick", "S",
        "Spectral Sickle",
        ["Ionian Boots", "Youmuu's Ghostblade", "The Collector", "Edge of Night"],
        PadProfile("charge", aim=0.45, combo_buttons=3, relic_dpad=False, taught=True,
                   notes="Gồng Q (đã dạy). Không buff ADC — hưởng 7.3 ít."),
        "pyke",
    ),
    Champ(
        "thresh", "Thresh", "Thresh", "pick", "S",
        "Relic Shield",
        ["Plated Steelcaps", "Yordle Trap", "Zeke's Convergence", "Knight's Vow"],
        PadProfile("hook", aim=0.70, combo_buttons=3, relic_dpad=True, taught=True,
                   notes="Q/E/W ba nút (đã dạy) nhưng móc + đèn nặng analog."),
        "thresh",
    ),
]


# Pyke items not in ITEMS — he is scored as "does not use 7.3 support items".
for _name, _cost in [("Youmuu's Ghostblade", 2700), ("The Collector", 3000), ("Edge of Night", 2800)]:
    ITEMS.setdefault(_name, {"cost": _cost})


def kit_amp(champ: Champ, flags: Dict[str, float], lvl: int, minute: int) -> Dict[str, float]:
    """
    Return combat modifiers applied to the ADC for this minute.
    Keys: as_pct, onhit, extra_ad_ratio, range_pct, cc_lock_s, heal_hps,
          helia_dump, kit_as_pct, uptime
    """
    ap = flags["ap"]
    ah = flags["ah"]
    hsp = flags["hsp"]
    k = champ.kit
    out = {
        "as_pct": 0.0, "onhit": 0.0, "kit_as_pct": 0.0,
        "range_pct": 0.0, "cc_lock_s": 0.0, "heal_hps": 0.0,
        "helia_dump": 0.0, "mandate": 0.0, "uptime": 0.55,
        "self_dps": 0.0, "ad_onhit_ratio": 0.0,
    }

    if k == "sona":
        q_cd = 8.0 / ah_mult(ah + 10)
        w_cd = 10.0 / ah_mult(ah + 10)
        q_rank = min(3, max(0, (lvl - 2) // 3))
        q_dmg = (40 + 40 * q_rank) + 0.40 * ap
        # Q hits two nearest champions in a fight — Helia farms both.
        out["self_dps"] = (q_dmg * 1.6) / q_cd
        out["onhit"] = (8 + 5 * q_rank) + 0.20 * ap  # Q aura next-hit on ADC
        out["uptime"] = 0.88  # self-cast auras
        w_heal = (35 + 15 * q_rank + 0.20 * ap) * (1 + hsp)
        w_shield = (25 + 25 * q_rank + 0.18 * ap) * (1 + hsp)
        out["heal_hps"] = (w_heal + w_shield * 0.4) / w_cd
        if flags["helia"]:
            # 30% pre-mit stored, cap 80–250. Sona fills the cap: Q×2 + Power Chord.
            cap = 80 + (250 - 80) * (lvl - 1) / 14
            champ_dmg = q_dmg * 2.0 * (w_cd / q_cd) + (20 + 10 * lvl + 0.15 * ap)
            stored = min(cap, 0.30 * champ_dmg)
            out["helia_dump"] = stored / max(w_cd, 4.0)
        if flags["diadem"] or flags.get("circlet"):
            mana = flags["mana"] or 800
            out["heal_hps"] += 0.008 * mana
        out["kit_as_pct"] = 0.0
        out["cc_lock_s"] = 1.0 * (8.0 / 70.0)  # R stun in a fight window

    elif k == "lulu":
        e_cd = 10.0 / ah_mult(ah)
        w_cd = max(14.0, 17.0 - lvl * 0.2) / ah_mult(ah)
        w_as = 0.25 + 0.05 * min(3, max(0, (lvl - 5) // 3))  # 25–40%
        w_dur = 3.5 + 0.5 * min(3, max(0, (lvl - 5) // 3))
        out["kit_as_pct"] = w_as * min(1.0, w_dur / w_cd)
        out["uptime"] = min(1.0, 6.0 / e_cd)  # Ardent window from E
        shield = (60 + 40 * min(3, lvl // 4) + 0.60 * ap) * (1 + hsp)
        out["heal_hps"] = shield / e_cd * 0.35  # shield as delayed HP
        # Pix attached to ADC (E 5s / 10s, plus W ring). 3 bolts ≈ one packet per ally auto.
        pix = 6 + 6 * lvl + 0.15 * ap
        attach = min(0.70, 5.0 / e_cd + 0.20)
        out["onhit"] = pix * attach
        if flags["harmonic"]:
            out["heal_hps"] *= 1.30
        out["cc_lock_s"] = 1.25 / (16.0 / ah_mult(ah))  # polymorph duty

    elif k == "milio":
        e_cd = 14.0 / ah_mult(ah) / 2.0  # 2 charges
        w_cd = 18.0 / ah_mult(ah)
        w_range = 0.09 + 0.025 * min(3, lvl // 4)
        out["range_pct"] = w_range * min(1.0, 6.0 / w_cd)
        out["ad_onhit_ratio"] = 0.10 * min(1.0, 6.0 / w_cd)
        # Fired Up! burn packet + 10% AD on next ally auto.
        out["onhit"] = 13 + 2 * lvl + 0.20 * ap
        out["kit_as_pct"] = 0.0
        out["uptime"] = 0.82
        shield = (60 + 40 * min(3, lvl // 4) + 0.30 * ap) * (1 + hsp)
        out["heal_hps"] = shield / max(e_cd, 2.5) + (90 + 0.15 * ap) / w_cd
        if flags["helia"]:
            cap = 80 + (250 - 80) * (lvl - 1) / 14
            # Low self damage; E dumps often so fragments don't sit unused.
            out["helia_dump"] = min(cap, 40 + 0.15 * ap) / 6.0
        out["cc_lock_s"] = 0.20  # Q knockback peel, not lock

    elif k == "leona":
        e_cd = max(6.0, 12.0 - lvl * 0.4) / ah_mult(ah)
        q_cd = 5.0 / ah_mult(ah)
        r_cd = max(35.0, 55.0 - lvl) / ah_mult(ah)
        lock = 0.5 + 1.0 + 1.75  # E root + Q stun + R stun (centre)
        out["cc_lock_s"] = lock * (8.0 / (e_cd + 4.0))  # per 8s fight window
        out["uptime"] = min(0.70, 4.0 / e_cd)  # Yordle Trap 4s ranged
        out["onhit"] = 34  # Sunlight consumed by ADC
        out["heal_hps"] = 0.0
        out["self_dps"] = 40.0

    elif k == "braum":
        q_cd = max(6.0, 9.0 - lvl * 0.2) / ah_mult(ah)
        out["cc_lock_s"] = (2.0 * 0.7 + 1.5 / 12.0)  # Q slow + periodic stun
        out["uptime"] = min(0.75, 4.0 / q_cd)  # Yordle on slow
        out["onhit"] = 9 + 3 * lvl  # concussive bonus after stun
        out["heal_hps"] = 12.0  # W resists approximated as delayed HP
        out["self_dps"] = 20.0

    elif k == "nautilus":
        q_cd = max(9.0, 12.0 - lvl * 0.2) / ah_mult(ah)
        out["cc_lock_s"] = (1.0 + 1.0 + 1.5) * (8.0 / (q_cd + 6.0))  # hook + passive + R
        out["uptime"] = min(0.65, 4.0 / q_cd)
        out["onhit"] = 13
        out["self_dps"] = 35.0
        out["heal_hps"] = 8.0  # W shield spillover

    elif k == "alistar":
        w_cd = 14.0 / ah_mult(ah)
        out["cc_lock_s"] = (1.0 + 1.5) * (8.0 / (w_cd + 4.0))
        out["uptime"] = min(0.70, 8.0 / w_cd)  # melee Yordle 8s
        out["self_dps"] = 25.0
        out["heal_hps"] = 15.0  # E pulse

    elif k == "seraphine":
        q_cd = 8.0 / ah_mult(ah)
        w_cd = 12.0 / ah_mult(ah)
        q_dmg = (55 + 30 * min(3, lvl // 4) + 0.45 * ap)
        out["self_dps"] = q_dmg / q_cd
        out["uptime"] = 0.75
        w_val = (50 + 25 * min(3, lvl // 4) + 0.25 * ap) * (1 + hsp)
        out["heal_hps"] = w_val / w_cd
        if flags["helia"]:
            out["helia_dump"] = min(200, 0.30 * q_dmg * 2) / w_cd
        out["cc_lock_s"] = 1.25 / 14.0

    elif k == "karma":
        q_cd = 7.0 / ah_mult(ah)
        e_cd = 10.0 / ah_mult(ah)
        q_dmg = (70 + 40 * min(3, lvl // 4) + 0.40 * ap)
        out["self_dps"] = q_dmg / q_cd
        out["uptime"] = min(0.80, 6.0 / e_cd)
        shield = (80 + 30 * min(3, lvl // 4) + 0.45 * ap) * (1 + hsp)
        out["heal_hps"] = shield / e_cd * 0.40
        if flags["helia"]:
            out["helia_dump"] = min(200, 0.30 * q_dmg) / e_cd
        out["cc_lock_s"] = 1.6 / 12.0  # mantra W root

    elif k == "nami":
        w_cd = 9.0 / ah_mult(ah)
        q_cd = 12.0 / ah_mult(ah)
        w_heal = (60 + 25 * min(3, lvl // 4) + 0.30 * ap) * (1 + hsp)
        out["heal_hps"] = w_heal / w_cd
        out["uptime"] = min(0.85, 6.0 / w_cd)
        out["self_dps"] = (70 + 0.5 * ap) / w_cd * 0.5
        out["cc_lock_s"] = 1.5 / q_cd * 0.45  # bubble hit rate on pad
        if flags["mandate"]:
            out["mandate"] = 0.07

    elif k == "pyke":
        q_cd = 10.0 / ah_mult(20)
        out["cc_lock_s"] = 1.1 * (8.0 / (q_cd + 3.0)) * 0.55  # charge hit rate
        out["uptime"] = 0.20
        out["self_dps"] = 70.0
        out["heal_hps"] = 0.0

    elif k == "thresh":
        q_cd = 12.0 / ah_mult(ah)
        out["cc_lock_s"] = (1.5 + 0.75) * (8.0 / (q_cd + 5.0)) * 0.40  # hook hit rate
        out["uptime"] = min(0.50, 4.0 / q_cd)
        out["heal_hps"] = 10.0  # lantern save approximated
        out["self_dps"] = 25.0

    # Item overlays
    if flags["ardent"] and champ.klass == "enchanter":
        out["as_pct"] += 0.30 * out["uptime"]
        out["onhit"] += 25.0 * out["uptime"]
    if flags["yordle"] and champ.klass in ("tank", "pick"):
        # 20% AS to ranged ally for 4s (melee self 30%/8s — we count ally)
        out["as_pct"] += 0.20 * out["uptime"]
    if flags["flowing"] and champ.klass == "enchanter":
        out["heal_hps"] *= 1.05
    if flags["mandate"]:
        out["mandate"] = max(out["mandate"], 0.07 * min(1.0, out["cc_lock_s"]))
    return out


def adc_with_support(
    minute: int,
    amp: Dict[str, float],
    crit_dmg: float,
    as_cap: float,
    ardent_old: bool = False,
) -> Dict[str, float]:
    ad, as_base, crit, items = adc_base(minute)
    as_pct = amp["as_pct"] + amp["kit_as_pct"]
    if ardent_old:
        # 7.2 Ardent: weaker / more gated. Model as 20% AS + 15 on-hit, lower uptime.
        as_pct = as_pct * 0.0 + 0.20 * amp["uptime"] * 0.75
        onhit = 15.0 * amp["uptime"] * 0.75 + amp["onhit"] * 0.5
    else:
        onhit = amp["onhit"]
    as_total = as_base * (1.0 + as_pct)
    # Range from Milio: small DPS via safer uptime, not raw AS. +4% effective autos.
    as_total *= 1.0 + 0.35 * amp["range_pct"]
    onhit += amp.get("ad_onhit_ratio", 0.0) * ad
    dps = auto_dps(ad, as_total, crit, onhit, crit_dmg, as_cap)
    dps *= 1.0 + amp["mandate"]
    return {
        "ad": ad, "as": as_total, "crit": crit, "dps": dps, "items": items,
    }


def heal_value(amp: Dict[str, float]) -> float:
    """Convert HPS + Helia dumps into effective ADC HP/s kept in the fight."""
    # Helia is the 7.3 identity item (damage → heal). Weight dumps above raw W/E HPS.
    return amp["heal_hps"] + 2.2 * amp["helia_dump"]


def cc_value(amp: Dict[str, float], adc_dps: float) -> float:
    """CC lock lets ADC free-hit. 1s lock in an 8s window ≈ 12.5% extra uptime."""
    return adc_dps * min(0.45, amp["cc_lock_s"] / 8.0)


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

PAD_MIN = 76.0  # must be playable on pad; below this is "not a fit"


def snapshot(champ: Champ, minute: int) -> Dict:
    gold = support_gold(minute)
    lvl = support_level(minute)
    owned = buy_order_owned(gold, champ.build, champ.start)
    flags = item_flags(owned)
    amp = kit_amp(champ, flags, lvl, minute)

    adc73 = adc_with_support(minute, amp, CRIT_73, AS_CAP_73)
    # 7.2 world: no Helia/Diadem/Yordle-AS, weaker Ardent, 175% crit, 2.5 AS cap
    amp72 = dict(amp)
    amp72["helia_dump"] = 0.0
    if "Echoes of Helia" in owned or "Whispering Circlet" in owned or "Diadem of Songs" in owned:
        # Those items did not exist — strip their heal
        amp72["heal_hps"] *= 0.65
    if flags["yordle"]:
        amp72 = dict(amp72)
        amp72["as_pct"] = max(0.0, amp72["as_pct"] - 0.20 * amp["uptime"])
    adc72 = adc_with_support(minute, amp72, CRIT_72, AS_CAP_72, ardent_old=flags["ardent"])

    ad, asb, crit, _ = adc_base(minute)
    naked73 = auto_dps(ad, asb, crit, 0.0, CRIT_73, AS_CAP_73)
    naked72 = auto_dps(ad, asb, crit, 0.0, CRIT_72, AS_CAP_72)
    extra73 = adc73["dps"] - naked73
    extra72 = adc72["dps"] - naked72

    # Support's contribution only (do not credit the naked ADC crit buff to every champ).
    contrib73 = extra73 + heal_value(amp) * 0.85 + cc_value(amp, adc73["dps"]) + amp["self_dps"] * 0.25
    contrib72 = extra72 + heal_value(amp72) * 0.85 + cc_value(amp72, adc72["dps"]) + amp["self_dps"] * 0.25
    patch_delta = contrib73 - contrib72
    teamfight = adc73["dps"] + heal_value(amp) * 0.45 + cc_value(amp, adc73["dps"]) + amp["self_dps"]
    return {
        "minute": minute,
        "gold": gold,
        "level": lvl,
        "items": owned,
        "adc_dps_73": round(adc73["dps"], 1),
        "adc_dps_72": round(adc72["dps"], 1),
        "naked_73": round(naked73, 1),
        "naked_72": round(naked72, 1),
        "extra_dps": round(adc73["dps"] - naked73, 1),
        "patch_delta": round(patch_delta, 1),
        "heal_hps": round(heal_value(amp), 1),
        "cc_lock": round(amp["cc_lock_s"], 2),
        "teamfight": round(teamfight, 1),
        "helia": bool(flags["helia"]),
        "ardent": bool(flags["ardent"]),
        "yordle": bool(flags["yordle"]),
        "diadem": bool(flags["diadem"] or ITEMS.get(owned[-1] if owned else "", {}).get("circlet")),
    }


def integrate(champ: Champ) -> Dict:
    minutes = list(range(4, GAME_MINUTES + 1))
    snaps = [snapshot(champ, m) for m in minutes]
    # Weight mid-game (lane 2v2 + first item) heavier — jungle farms more in 7.3.
    def w(m: int) -> float:
        if m <= 8:
            return 1.3
        if m <= 14:
            return 1.2
        return 1.0

    tw = sum(w(s["minute"]) for s in snaps)
    avg_delta = sum(s["patch_delta"] * w(s["minute"]) for s in snaps) / tw
    avg_tf = sum(s["teamfight"] * w(s["minute"]) for s in snaps) / tw
    avg_extra = sum(s["extra_dps"] * w(s["minute"]) for s in snaps) / tw
    first_item_m = next(
        (s["minute"] for s in snaps if any(ITEMS.get(n, {}).get("cost", 0) >= 2000 for n in s["items"])),
        20,
    )
    pad = champ.pad.score
    # Combined: must fit pad. Rank by 7.3 benefit among pad-fits.
    patch_score = avg_delta + 0.12 * avg_extra
    combined = patch_score * (0.55 + 0.45 * (pad / 100.0))
    if pad < PAD_MIN:
        combined *= 0.72  # still listed, but cannot be "fit pad" top 5
    return {
        "key": champ.key,
        "name": champ.name,
        "name_vi": champ.name_vi,
        "klass": champ.klass,
        "wrf_tier": champ.wrf_tier,
        "pad_score": round(pad, 1),
        "pad_style": champ.pad.style,
        "pad_notes": champ.pad.notes,
        "taught": champ.pad.taught,
        "relic_dpad": champ.pad.relic_dpad,
        "start": champ.start,
        "build": champ.build,
        "avg_patch_delta": round(avg_delta, 1),
        "avg_teamfight": round(avg_tf, 1),
        "avg_extra_dps": round(avg_extra, 1),
        "patch_score": round(patch_score, 1),
        "combined": round(combined, 1),
        "pad_fit": pad >= PAD_MIN,
        "first_item_min": first_item_m,
        "snaps": snaps,
        "spike_12": next(s for s in snaps if s["minute"] == 12),
        "spike_16": next(s for s in snaps if s["minute"] == 16),
        "spike_20": next(s for s in snaps if s["minute"] == 20),
    }


def rank_all() -> List[Dict]:
    rows = [integrate(c) for c in CHAMPS]
    rows.sort(key=lambda r: r["combined"], reverse=True)
    return rows


def write_report(rows: List[Dict], path: str) -> None:
    top = [r for r in rows if r["pad_fit"]][:5]
    lines: List[str] = []
    a = lines.append
    a("=" * 78)
    a("TỐC CHIẾN 7.3 — TOP 5 HỖ TRỢ HƯỞNG PATCH + FIT PAD")
    a("Patch 7.3 (22/09/2026)  |  Game 20:00  |  ADC crit 200% / AS cap 3.0")
    a("Pad: MB03 (gồng / xả Q / combo 2–4 nút) + D-pad ↑bảng ↓hồi ←lín →trụ")
    a("=" * 78)
    a("")
    a("CÂU HỎI")
    a("  Support nào hưởng NHIỀU NHẤT update 7.3, VÀ đánh được trên pad?")
    a("  7.3 = ADC mạnh (crit 175→200, item mới) + đồ hỗ trợ làm lại")
    a("        (Helia / Ardent 30% AS+25 on-hit / Diadem / Yordle Trap cho AS).")
    a("  Jungle farm nhiều hơn → 2v2 đường. Trụ plating mọi nhà → siege.")
    a("")
    a("CÁCH TÍNH")
    a("  • ADC generic crit (Jinx/Xayah/MF): DPS auto có/không buff support")
    a("  • patch_delta = (DPS+heal+CC) 7.3 − cùng kit trên 7.2 (175% crit,")
    a("    Ardent cũ, không Helia/Diadem, Yordle Trap không cho AS)")
    a("  • pad_score từ style MB03 − penalize aim/combo dài + Relic dùng D-pad ←")
    a(f"  • Top 5: pad_score ≥ {PAD_MIN:.0f}, xếp theo combined (patch × pad)")
    a("")
    a("-" * 78)
    a("TOP 5  (pad-fit)")
    a("-" * 78)
    a(f"  {'#':<3}{'Tướng':<12}{'Loại':<11}{'WRF':<4}{'Pad':>6}{'Δpatch':>9}{'ADC+':>8}{'12:00':>8}{'16:00':>8}{'20:00':>8}")
    for i, r in enumerate(top, 1):
        a(
            f"  {i:<3}{r['name']:<12}{r['klass']:<11}{r['wrf_tier']:<4}"
            f"{r['pad_score']:>6.0f}{r['avg_patch_delta']:>9.1f}"
            f"{r['avg_extra_dps']:>8.1f}{r['spike_12']['teamfight']:>8.0f}"
            f"{r['spike_16']['teamfight']:>8.0f}{r['spike_20']['teamfight']:>8.0f}"
        )
    a("")
    a("  Δpatch = điểm HƯỞNG UPDATE (cao = kit/item 7.3 kéo ADC mạnh hơn 7.2).")
    a("  ADC+   = DPS thêm cho xạ thủ so với ADC trần 7.3.")
    a("  12/16/20 = teamfight score (ADC DPS + heal quy đổi + CC lock + poke).")
    a("")

    reasons = {
        "sona": [
            "Helia sinh ra cho Sona: Q hai mục tiêu → 30% pre-mit thành Soul Fragment, W dump vào ADC.",
            "Tear → Circlet → Diadem: Harmony +0.5% HSP/100 mana + 0.8% max mana/s heal. Sona đói mana = item này.",
            "Ardent 7.3 phẳng 30% AS + 25 on-hit (không còn nhìn crit/level xạ thủ) — aura Q/W giữ uptime ~85%.",
            "Pad: QWE tự cast, không skill-stick. MB03 'xả Q'. R đường thẳng, không combo 3 nút.",
            "WRF 7.3 build: Sickle → Tear → Helia → Whispering Circlet. Đúng spike Diadem nếu trận dài.",
        ],
        "lulu": [
            "Ardent 2400g (rẻ hơn 300), HSP 8%, Censer 30% AS + 25 magic — cộng W 25–40% AS lên ADC crit 200%.",
            "Pix dính ADC = on-hit sẵn. E khiên proc Ardent + Harmonic Echo chain 30/35% sang người gần.",
            "7.3 hypercarry (Jinx/Vayne/Kog/Xayah) là meta Lulu. Crit 200% biến buff AS thành sát thương thật.",
            "Pad: W/E/R targeted (portrait lock). Relic Shield → D-pad ← ăn đại bác. Q Glitterlance optional.",
            "Trap: max Q lane rồi quên W lúc teamfight — W mới là món 7.3.",
        ],
        "leona": [
            "Yordle Trap 7.3: CC → 20% AS cho đồng đội ranged 4s (mình melee 30%/8s). All-in giờ BUFF ADC, không chỉ khóa.",
            "Jungle 7.3 farm nhiều → ít gank. Leona thắng 2v2 cấp 2 (E→Q) đúng meta lane.",
            "Zeke delay Frostfire nếu R từ xa — R Leona từ bụi vẫn proc. Giá 2400, Armor+MR cân mage.",
            "Pad: combo 2 nút đã dạy (E rồi Q). Relic + D-pad ← lính, → trụ plating mọi nhà.",
            "WRF 7.3 S-tier. Build: Relic → Steelcaps → Yordle Trap → Mantle.",
        ],
        "braum": [
            "Peel cho ADC 7.3: giữ E chặn crit 200% (đạn thứ nhất miễn, sau giảm 35–50%). Đây là anti-update của địch.",
            "Q slow proc Yordle Trap 20% AS — không cần all-in như Leona. Uptime AS cao hơn engage thuần.",
            "W nhảy ADC (targeted) + Relic D-pad. Giữ E = đúng thế mạnh gồng MB03.",
            "WRF 7.3 S-tier. Knight's Vow hút damage crit mới. Frozen Heart 25% AS slow nếu địch nhiều ADC.",
            "Q không xuyên lính — D-pad ← để không AA nhầm khi Q.",
        ],
        "milio": [
            "Fired Up! = Ardent gắn kit (10% AD magic + burn). 7.3 ADC auto nhiều hơn → proc nhiều hơn.",
            "W +9–20% tầm đánh — RFC/Hexoptics 7.3 cộng tầm, Milio cộng thêm. Hypercarry đứng lùi.",
            "Helia + E 2 charge dump nhanh. Harmonic Echo chain shield. WRF core: Helia → Harmonic → Ardent.",
            "Pad: E/W lock đồng đội, tether không giới hạn tầm. Q nảy minion (D-pad ← có thể setup) — không bắt buộc trúng Q để thắng.",
            "Season S23 skin Milio. Không phải S-tier WRF nhưng Δpatch cao vì kit = ADC patch.",
        ],
    }

    for i, r in enumerate(top, 1):
        a("-" * 78)
        a(f"#{i}  {r['name'].upper()}   WRF {r['wrf_tier']}   pad {r['pad_score']:.0f}   "
          f"Δpatch {r['avg_patch_delta']:.1f}   combined {r['combined']:.1f}")
        a(f"  Style pad: {r['pad_style']}  |  {r['pad_notes']}")
        a(f"  Start {r['start']} → {' → '.join(r['build'][:3])}")
        a(f"  Món 1 xong ~{r['first_item_min']}:00")
        a("  Spike ADC DPS (có buff) / extra vs ADC trần:")
        for label, key in (("12:00", "spike_12"), ("16:00", "spike_16"), ("20:00", "spike_20")):
            s = r[key]
            a(f"    {label}  ADC {s['adc_dps_73']:.0f} DPS  (+{s['extra_dps']:.0f})  "
              f"heal/Helia {s['heal_hps']:.0f}/s  items: {' › '.join(s['items'][1:] or s['items'])}")
        a("  Vì sao vào top:")
        for bullet in reasons.get(r["key"], [r["pad_notes"]]):
            a(f"    • {bullet}")
        a("")

    a("-" * 78)
    a("BẢNG ĐỦ 12 TƯỚNG  (gạch chân = trượt pad_min, không vào top 5 fit-pad)")
    a("-" * 78)
    a(f"  {'Tướng':<12}{'Pad':>5}{'Fit':>5}{'Δpatch':>8}{'ADC+':>7}{'Combo':>7}{'WRF':>5}  style")
    for r in rows:
        fit = "yes" if r["pad_fit"] else "NO"
        a(
            f"  {r['name']:<12}{r['pad_score']:>5.0f}{fit:>5}{r['avg_patch_delta']:>8.1f}"
            f"{r['avg_extra_dps']:>7.1f}{r['combined']:>7.1f}{r['wrf_tier']:>5}  "
            f"{r['pad_style']}"
        )
    a("")
    a("KHÔNG VÀO TOP 5 DÙ META MẠNH")
    a("  Nami     — Mandate+Ardent rất 7.3, bong bóng Q penalize analog (aim 0.78).")
    a("  Thresh   — Yordle Trap + S-tier, nhưng móc+đèn 3 nút + aim 0.70.")
    a("  Pyke     — Gồng Q đã dạy, pad ổn; không buff ADC nên Δpatch thấp.")
    a("  Nautilus — Sát ngưỡng pad (hook + lính chặn). Runner-up nếu thích móc.")
    a("  Alistar  — WQ pad đẹp, Yordle Trap 8s melee AS; WRF B, lane yếu hơn Leona.")
    a("")
    a("-" * 78)
    a("MAP PAD (nhắc)")
    a("  Analog = đi     L1 = skill chính (Q / gồng)     A = AA tướng")
    a("  D-pad ← = đánh lính (Relic đại bác)   → = đánh trụ (plating 7.3 mọi nhà)")
    a("  D-pad ↓ = hồi thành                   ↑ = bảng điểm")
    a("  Force Attack Follow TẮT. Enemy lock = No Minion/Structure.")
    a("")
    a("KHUYÊN CHƠI 20 PHÚT")
    a("  1) Lulu   — ADC hyper (Vayne, Kog, Jinx, Xayah). W ADC, E proc Ardent.")
    a("  2) Leona  — ADC all-in (Lucian, Samira, Draven, MF). E→Q, Trap proc AS.")
    a("  3) Milio  — ADC cần tầm (Cait, Kog, Twitch). Tether W cả trận.")
    a("  4) Braum  — địch poke/engage, ADC cần sống. Giữ E ăn crit 200%.")
    a("  5) Sona   — ADC crit/scale (Jinx, Xayah, Ashe, Jhin). Xả Q, Helia dump W.")
    a("")
    a("  Trap: pick Thresh/Nami 'vì meta' trên pad — miss hook/bubble mất 7.3 advantage.")
    a("  Trap: Pyke/assassin support — ADC 7.3 không được buff, bạn gánh kill.")
    a("=" * 78)

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main() -> None:
    here = os.path.dirname(os.path.abspath(__file__))
    rows = rank_all()
    top = [r for r in rows if r["pad_fit"]][:5]
    slim = []
    for r in rows:
        d = {k: v for k, v in r.items() if k != "snaps"}
        d["snaps_key"] = {s["minute"]: s for s in r["snaps"] if s["minute"] in (8, 12, 16, 20)}
        slim.append(d)
    payload = {
        "patch": "7.3",
        "date": "2026-09-22",
        "question": "Top 5 supports that benefit most from 7.3 AND fit MB03/D-pad",
        "pad_min": PAD_MIN,
        "top5": [r["name"] for r in top],
        "ranking": slim,
    }
    with open(os.path.join(here, "results.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
        f.write("\n")
    write_report(rows, os.path.join(here, "report.txt"))
    print("Top 5 (pad-fit):")
    for i, r in enumerate(top, 1):
        print(f"  {i}. {r['name']:10}  pad={r['pad_score']:.0f}  Δ={r['avg_patch_delta']:.1f}  comb={r['combined']:.1f}")
    print("Wrote report.txt and results.json")


if __name__ == "__main__":
    main()
