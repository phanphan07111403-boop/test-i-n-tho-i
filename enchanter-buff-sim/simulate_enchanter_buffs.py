#!/usr/bin/env python3
"""
Wild Rift Enchanter Buff Simulation — Patch 7.2+
1) Rank current-meta enchanters
2) Minute-by-minute buff-max builds for the strongest (Nami)
Metric: ally-facing Buff Score = heal + shield-eq + combat buff DPS (Ardent/E/Staff)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import json

GAME_MINUTES = 20


# ---------------------------------------------------------------------------
# Meta snapshot (Patch 7.2 / 7.2b–c consensus across WR tier lists)
# ---------------------------------------------------------------------------

ENCHANTER_META = [
    # name, tier, wr_note, why, buff_profile
    {
        "name": "Nami",
        "tier": "SS / S+",
        "meta_score": 96,
        "why": "Most consistent top enchanter: lane poke + heal + E combat buff + R engage.",
        "buff_profile": "Hybrid heal + on-hit buff (best overall enable)",
    },
    {
        "name": "Lulu",
        "tier": "S",
        "meta_score": 90,
        "why": "Highest pure peel/buff density (W AS, E shield, R HP). High pick/ban.",
        "buff_profile": "Pure buff/peel (shield + AS + HP)",
    },
    {
        "name": "Milio",
        "tier": "S",
        "meta_score": 88,
        "why": "2-charge shields + range buff + R cleanse. Strong vs engage.",
        "buff_profile": "Shield spam + range/heal",
    },
    {
        "name": "Sona",
        "tier": "S+ (WR spike)",
        "meta_score": 87,
        "why": "Some boards show ~54% WR; aura uptime scales with Redemption meta.",
        "buff_profile": "Aura heal/shield continuous",
    },
    {
        "name": "Soraka",
        "tier": "A",
        "meta_score": 78,
        "why": "Pure heal; Redemption doubles down. Weaker vs dive without peel.",
        "buff_profile": "Pure heal",
    },
    {
        "name": "Janna",
        "tier": "A / B",
        "meta_score": 72,
        "why": "Peel specialist; less favored when dive/engage supports dominate.",
        "buff_profile": "Shield + disengage",
    },
    {
        "name": "Yuumi",
        "tier": "C",
        "meta_score": 55,
        "why": "Lowest enchanter WR; attach kit struggles in current dive meta.",
        "buff_profile": "Attach heal/shield",
    },
]


def gold_at_minute(m: int) -> int:
    # Same aggressive support poke/heal curve as Zyra sim (~10k by 20)
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
    table = {
        1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7, 7: 8, 8: 8,
        9: 9, 10: 10, 11: 10, 12: 11, 13: 11, 14: 12,
        15: 12, 16: 13, 17: 13, 18: 14, 19: 14, 20: 15,
    }
    return table.get(m, min(15, 1 + m))


def scythe_ap(minute: int) -> float:
    if minute < 6:
        return 0.0
    return 4.0 * min(10, minute - 5)


# ---------------------------------------------------------------------------
# Items
# ---------------------------------------------------------------------------

@dataclass
class Item:
    name: str
    cost: int
    ap: float = 0
    ah: float = 0
    hsp: float = 0  # heal/shield power (fraction, e.g. 0.05)
    hp: float = 0
    ardent: bool = False
    staff: bool = False
    harmonic: bool = False
    redemption: bool = False
    shurelya: bool = False
    tags: Tuple[str, ...] = ()


ITEMS: Dict[str, Item] = {
    "Spectral Sickle": Item("Spectral Sickle", 500, ap=20, tags=("support",)),
    "Black Mist Scythe": Item("Black Mist Scythe", 0, ap=28, ah=10, tags=("support",)),
    "Boots of Speed": Item("Boots of Speed", 500, tags=("boots",)),
    "Ionian Boots of Lucidity": Item(
        "Ionian Boots of Lucidity", 1000, ah=20, tags=("boots",)
    ),
    "Forbidden Idol": Item("Forbidden Idol", 900, ah=10, hsp=0.05),
    "Fiendish Codex": Item("Fiendish Codex", 900, ap=35, ah=10),
    "Amplifying Tome": Item("Amplifying Tome", 500, ap=20),
    "Kindlegem": Item("Kindlegem", 1000, hp=200, ah=10),
    "Aether Wisp": Item("Aether Wisp", 950, ap=30),
    "Lost Chapter": Item("Lost Chapter", 1200, ap=40, ah=10),
    "Ardent Censer": Item(
        "Ardent Censer",
        2700,
        ap=45,
        ah=10,
        hp=250,
        hsp=0.05,
        ardent=True,
        tags=("buff",),
    ),
    "Staff of Flowing Water": Item(
        "Staff of Flowing Water",
        2500,
        ap=50,
        ah=15,
        hp=100,
        hsp=0.05,
        staff=True,
        tags=("buff",),
    ),
    "Harmonic Echo": Item(
        "Harmonic Echo",
        2800,
        ap=50,
        ah=15,
        hp=100,
        hsp=0.05,
        harmonic=True,
        tags=("heal",),
    ),
    "Redemption": Item(
        "Redemption",
        2600,
        ap=50,
        ah=15,
        hp=150,
        hsp=0.05,
        redemption=True,
        tags=("heal", "active"),
    ),
    "Shurelya's Battlesong": Item(
        "Shurelya's Battlesong",
        2600,
        ap=35,
        ah=20,
        shurelya=True,
        tags=("ms", "active"),
    ),
}


UPGRADE_COMPONENTS = {
    "Ionian Boots of Lucidity": ("Boots of Speed",),
    "Ardent Censer": ("Forbidden Idol", "Kindlegem", "Aether Wisp"),
    "Staff of Flowing Water": ("Forbidden Idol", "Aether Wisp", "Amplifying Tome"),
    "Harmonic Echo": ("Forbidden Idol", "Lost Chapter", "Amplifying Tome"),
    "Redemption": ("Forbidden Idol", "Fiendish Codex"),
    "Shurelya's Battlesong": ("Aether Wisp", "Amplifying Tome"),
}

NEXT_COMPONENTS = {
    "Ionian Boots of Lucidity": ["Boots of Speed"],
    "Ardent Censer": ["Forbidden Idol", "Kindlegem"],
    "Staff of Flowing Water": ["Forbidden Idol", "Aether Wisp"],
    "Harmonic Echo": ["Forbidden Idol", "Lost Chapter"],
    "Redemption": ["Forbidden Idol", "Fiendish Codex"],
    "Shurelya's Battlesong": ["Aether Wisp"],
}


BUILD_PATHS: Dict[str, List[str]] = {
    # Maximize combat buff uptime (Ardent first) then heal amp
    "Ardent → Staff → Harmonic → Redemption (Buff Max)": [
        "Spectral Sickle",
        "Boots of Speed",
        "Forbidden Idol",
        "Ardent Censer",
        "Ionian Boots of Lucidity",
        "Staff of Flowing Water",
        "Harmonic Echo",
        "Redemption",
    ],
    # Heal core first (Echo) then Ardent
    "Harmonic → Ardent → Redemption → Staff (Heal First)": [
        "Spectral Sickle",
        "Boots of Speed",
        "Forbidden Idol",
        "Harmonic Echo",
        "Ionian Boots of Lucidity",
        "Ardent Censer",
        "Redemption",
        "Staff of Flowing Water",
    ],
    # Guide default-ish: Ardent → Harmonic → Redemption → Staff
    "Ardent → Harmonic → Redemption → Staff (Guide)": [
        "Spectral Sickle",
        "Boots of Speed",
        "Forbidden Idol",
        "Ardent Censer",
        "Ionian Boots of Lucidity",
        "Harmonic Echo",
        "Redemption",
        "Staff of Flowing Water",
    ],
    # Redemption spike for teamfight heal
    "Ardent → Redemption → Staff → Harmonic (Teamfight)": [
        "Spectral Sickle",
        "Boots of Speed",
        "Forbidden Idol",
        "Ardent Censer",
        "Ionian Boots of Lucidity",
        "Redemption",
        "Staff of Flowing Water",
        "Harmonic Echo",
    ],
    # Engage MS (less pure buff)
    "Ardent → Shurelya → Staff → Redemption (Engage)": [
        "Spectral Sickle",
        "Boots of Speed",
        "Forbidden Idol",
        "Ardent Censer",
        "Ionian Boots of Lucidity",
        "Shurelya's Battlesong",
        "Staff of Flowing Water",
        "Redemption",
    ],
    # Staff first (AP buff to mage ADC / AP carry)
    "Staff → Ardent → Redemption → Harmonic (AP Carry)": [
        "Spectral Sickle",
        "Boots of Speed",
        "Forbidden Idol",
        "Staff of Flowing Water",
        "Ionian Boots of Lucidity",
        "Ardent Censer",
        "Redemption",
        "Harmonic Echo",
    ],
}


def resolve_inventory(path: List[str], gold: int, minute: int) -> List[Item]:
    owned: List[str] = []
    gold_pool = gold

    def credit_for(name: str) -> Tuple[int, List[str]]:
        credit = 0
        remove = []
        for c in UPGRADE_COMPONENTS.get(name, ()):
            if c in owned:
                credit += ITEMS[c].cost
                remove.append(c)
        return credit, remove

    def remaining(name: str) -> int:
        if name == "Black Mist Scythe":
            return 0
        credit, _ = credit_for(name)
        return max(0, ITEMS[name].cost - credit)

    def can_afford(name: str) -> bool:
        return gold_pool >= remaining(name)

    def buy(name: str) -> bool:
        nonlocal gold_pool
        if name in owned:
            return False
        if name == "Black Mist Scythe":
            if "Spectral Sickle" in owned:
                owned.remove("Spectral Sickle")
            owned.append(name)
            return True
        cost = remaining(name)
        if cost > gold_pool:
            return False
        _, remove = credit_for(name)
        gold_pool -= cost
        for r in remove:
            owned.remove(r)
        owned.append(name)
        return True

    blocked: Optional[str] = None
    for step in path:
        if step == "Black Mist Scythe":
            continue
        if step == "Spectral Sickle":
            if "Spectral Sickle" not in owned and "Black Mist Scythe" not in owned:
                buy("Spectral Sickle")
            continue
        if step in owned:
            continue
        if can_afford(step):
            buy(step)
        else:
            blocked = step
            break

    if minute >= 5 and "Spectral Sickle" in owned:
        owned.remove("Spectral Sickle")
        owned.insert(0, "Black Mist Scythe")

    if blocked and blocked in NEXT_COMPONENTS:
        for comp in NEXT_COMPONENTS[blocked]:
            if comp not in owned and gold_pool >= ITEMS[comp].cost:
                buy(comp)
        if can_afford(blocked):
            buy(blocked)
            seen = False
            for step in path:
                if step == blocked:
                    seen = True
                    continue
                if not seen or step in ("Spectral Sickle", "Black Mist Scythe"):
                    continue
                if step in owned:
                    continue
                if can_afford(step):
                    buy(step)
                else:
                    for comp in NEXT_COMPONENTS.get(step, []):
                        if comp not in owned and gold_pool >= ITEMS[comp].cost:
                            buy(comp)
                    if can_afford(step):
                        buy(step)
                    else:
                        break

    if "Ionian Boots of Lucidity" in owned and "Boots of Speed" in owned:
        owned.remove("Boots of Speed")

    return [ITEMS[n] for n in owned]


# ---------------------------------------------------------------------------
# Nami buff combat model (maximize ally buffs)
# ---------------------------------------------------------------------------

@dataclass
class Snap:
    minute: int
    build: str
    items: List[str]
    gold: int
    level: int
    ap: float
    ah: float
    hsp: float
    heal_hps: float
    combat_buff_dps: float
    burst_heal: float
    buff_score: float
    uptime: float
    notes: str


def nami_skill_ranks(level: int) -> Tuple[int, int, int]:
    # Max W then E then Q; R at 5/9/13
    # Approximate ranks 0-3 for W/E
    w = min(3, max(0, (level + 1) // 2 - 1))
    e = min(3, max(0, level // 3))
    if level >= 3:
        w = max(w, 1)
    if level >= 4:
        e = max(e, 1)
    if level >= 9:
        w = 3
    if level >= 11:
        e = 3
    return w, e, min(2, max(0, (level - 5) // 4))


def compute_nami(build: str, path: List[str], minute: int) -> Snap:
    gold = gold_at_minute(minute)
    level = level_at_minute(minute)
    inv = resolve_inventory(path, gold, minute)

    ap = ah = hsp = 0.0
    has_ardent = has_staff = has_harmonic = has_redemption = has_shurelya = False
    names = []
    for it in inv:
        names.append(it.name)
        ap += it.ap
        ah += it.ah
        hsp += it.hsp
        if it.ardent:
            has_ardent = True
        if it.staff:
            has_staff = True
        if it.harmonic:
            has_harmonic = True
        if it.redemption:
            has_redemption = True
        if it.shurelya:
            has_shurelya = True
        if it.name == "Black Mist Scythe":
            ap += scythe_ap(minute)

    # Staff Rapids: +30–50 AP to ally AND self for 6s on heal/shield
    staff_ap = 0.0
    if has_staff:
        staff_ap = 30 + (50 - 30) * (level - 1) / 14
        ap += staff_ap  # self AP during buff windows (average ~70% uptime later)

    cast_mult = 1.0 + ah / (ah + 100) * 0.5
    w_rank, e_rank, _ = nami_skill_ranks(level)

    # --- Heal HPS (W Ebb and Flow primary ally heal) ---
    w_heal = [55, 85, 115, 145][w_rank]
    w_cd = 10.0 / cast_mult
    # In fights: ~1.0 W per CD on ADC (bounce may heal twice sometimes → 1.15)
    w_hps = (w_heal + 0.30 * ap) * 1.15 / w_cd

    # Harmonic Echo: ~every 12–18s extra heal on next W
    echo_hps = 0.0
    if has_harmonic:
        echo_base = 100 + (160 - 100) * (level - 1) / 14
        echo_heal = (echo_base + 0.15 * ap) * 1.15  # avg not always execute threshold
        echo_hps = echo_heal / 15.0

    # Redemption: 150–350 ally heal / 60s → HPS; also multi-ally ~1.6 targets avg mid
    red_hps = 0.0
    burst_heal = 0.0
    if has_redemption:
        red = 150 + (350 - 150) * (level - 1) / 14
        burst_heal = red * (1 + hsp)
        red_hps = burst_heal * 1.6 / 60.0

    heal_raw = w_hps + echo_hps + red_hps
    heal_hps = heal_raw * (1 + hsp)

    # --- Combat buff DPS to ADC ---
    # Nami E: next 3 attacks +25/45/65/85 (+20% AP) over 6s window
    e_bonus = [25, 45, 65, 85][e_rank] + 0.20 * ap
    e_cd = 11.0 / cast_mult
    # ADC attacks ~1.0–1.6/s; E lasts 6s / 3 hits — usually consume all 3
    e_dps = (3 * e_bonus) / e_cd

    # Ardent: 15–34% AS + 16–22 on-hit for 6s when heal/shield (W triggers even full HP)
    ardent_dps = 0.0
    if has_ardent:
        on_hit = 16 + (22 - 16) * (level - 1) / 14
        # AS helps ~0.15–0.25 extra autos/s mid; simplify: on-hit * ADC AS ~1.2
        adc_as = 1.05 + 0.03 * level
        # Uptime: W every ~8–10s, buff lasts 6s → high uptime with AH
        ardent_uptime = min(0.95, 6.0 / max(6.0, w_cd) * 1.05)
        ardent_dps = on_hit * adc_as * ardent_uptime
        # Extra autos from AS: ~20% AS * 1.2 AD~80 ≈ rough 0.2*80*adc_as*uptime physical
        # Fold as magic-eq: +8 * uptime
        ardent_dps += 8.0 * ardent_uptime

    # Staff: ally gets +30–50 AP for 6s — value depends on ADC (AD carry gets less).
    # Assume typical crit ADC: staff AP worth ~0.35 of AP mage → convert to ~dps
    staff_ally_dps = 0.0
    if has_staff:
        staff_uptime = min(0.95, 6.0 / max(6.0, w_cd) * 1.05)
        staff_ally_dps = staff_ap * 0.25 * staff_uptime  # mild AD carry conversion

    combat = e_dps + ardent_dps + staff_ally_dps

    # MS from passive / Shurelya — light score weight
    util = 4.0 * cast_mult
    if has_shurelya:
        util += 12.0  # engage MS active value

    # Buff score: heal is primary enable; combat buffs are the "buff done" ask
    # Weight combat slightly higher for "maximize buff" goal
    buff_score = heal_hps * 1.0 + combat * 1.35 + util * 0.35 + burst_heal * 0.02

    # Uptime of buffs on ADC
    uptime = 0.55
    if has_ardent or has_staff:
        uptime = min(0.95, 6.0 / max(6.0, w_cd) * 1.1)
    if has_ardent and has_staff:
        uptime = min(0.97, uptime + 0.05)

    notes = []
    if has_ardent and has_staff:
        notes.append("DOUBLE BUFF (Ardent+Staff)")
    elif has_ardent:
        notes.append("Ardent up")
    elif has_staff:
        notes.append("Staff up")
    if has_harmonic:
        notes.append("Echo heal")
    if has_redemption:
        notes.append("Redemption")
    if uptime >= 0.85:
        notes.append("high buff uptime")

    return Snap(
        minute=minute,
        build=build,
        items=names,
        gold=gold,
        level=level,
        ap=round(ap, 1),
        ah=ah,
        hsp=hsp,
        heal_hps=round(heal_hps, 1),
        combat_buff_dps=round(combat, 1),
        burst_heal=round(burst_heal, 1),
        buff_score=round(buff_score, 1),
        uptime=round(uptime, 3),
        notes=", ".join(notes) or "core building",
    )


def run() -> Tuple[Dict[str, List[Snap]], List[dict]]:
    results = {
        name: [compute_nami(name, path, m) for m in range(1, GAME_MINUTES + 1)]
        for name, path in BUILD_PATHS.items()
    }
    timeline = []
    for m in range(1, GAME_MINUTES + 1):
        cands = [(n, results[n][m - 1]) for n in results]
        best_n, best_s = max(cands, key=lambda x: x[1].buff_score)
        timeline.append(
            {
                "minute": m,
                "winner": best_n,
                "buff_score": best_s.buff_score,
                "heal_hps": best_s.heal_hps,
                "combat_buff_dps": best_s.combat_buff_dps,
                "uptime": best_s.uptime,
                "items": best_s.items,
                "notes": best_s.notes,
            }
        )
    return results, timeline


def report(results, timeline) -> str:
    lines = []
    lines.append("=" * 78)
    lines.append("WILD RIFT ENCHANTER META + BUFF-MAX SIM (Patch 7.2+)")
    lines.append("Strongest meta enchanter → Nami | Goal: maximize ally buffs 1–20 min")
    lines.append("=" * 78)
    lines.append("")
    lines.append("ENCHANTER META RANKING (consensus tier lists)")
    lines.append(f"  {'#':>2}  {'Champion':<10} {'Tier':<14} {'Buff profile'}")
    for i, e in enumerate(sorted(ENCHANTER_META, key=lambda x: -x["meta_score"]), 1):
        mark = " ← SIM TARGET" if e["name"] == "Nami" else ""
        lines.append(
            f"  {i:>2}  {e['name']:<10} {e['tier']:<14} {e['buff_profile']}{mark}"
        )
    lines.append("")
    lines.append("  Why Nami: SS/S+ across Pocket Tactics / multiple 7.2 boards;")
    lines.append("  best mix of lane strength + E combat buff + heal for item synergies.")
    lines.append("  (Lulu = highest pure peel buff; pick her if you want max shield/AS peel.)")
    lines.append("")
    lines.append("-" * 78)
    lines.append("NAMI — MINUTE-BY-MINUTE OPTIMAL (highest Buff Score)")
    lines.append("-" * 78)
    for row in timeline:
        items = " › ".join(row["items"][:5])
        if len(row["items"]) > 5:
            items += " › …"
        lines.append(
            f"  {row['minute']:>2}:00 | score {row['buff_score']:>6.1f} | "
            f"heal {row['heal_hps']:>5.1f}/s | buffDPS {row['combat_buff_dps']:>5.1f} | "
            f"up {row['uptime']*100:>3.0f}%"
        )
        lines.append(f"         {row['winner']}")
        lines.append(f"         {items}")
        lines.append(f"         {row['notes']}")

    lines.append("")
    lines.append("-" * 78)
    lines.append("BUILD COMPARISON @ spikes (Buff Score)")
    lines.append("-" * 78)
    lines.append(
        f"  {'Build':<48} {'8':>6} {'12':>6} {'16':>6} {'20':>6} {'Avg':>7}"
    )
    ranking = []
    for name, snaps in results.items():
        vals = [snaps[m - 1].buff_score for m in (8, 12, 16, 20)]
        avg = sum(s.buff_score for s in snaps) / len(snaps)
        ranking.append((avg, name, vals, snaps))
        lines.append(
            f"  {name:<48} {vals[0]:>6.1f} {vals[1]:>6.1f} {vals[2]:>6.1f} {vals[3]:>6.1f} {avg:>7.1f}"
        )
    ranking.sort(reverse=True)
    best = ranking[0]
    snaps = best[3]
    ardent_m = next((s.minute for s in snaps if "Ardent Censer" in s.items), None)
    staff_m = next((s.minute for s in snaps if "Staff of Flowing Water" in s.items), None)
    echo_m = next((s.minute for s in snaps if "Harmonic Echo" in s.items), None)
    red_m = next((s.minute for s in snaps if "Redemption" in s.items), None)

    lines.append("")
    lines.append("-" * 78)
    lines.append("VERDICT — MAXIMIZE BUFFS ON NAMI (20-min game)")
    lines.append("-" * 78)
    lines.append(f"  Best path: {best[1]}")
    lines.append(f"  Avg Buff Score 1–20: {best[0]:.1f}")
    if ardent_m:
        lines.append(f"  Ardent online: ~{ardent_m}:00  (AS + on-hit — main combat buff)")
    if staff_m:
        lines.append(f"  Staff online:  ~{staff_m}:00  (AP haste buff on every W)")
    if echo_m:
        lines.append(f"  Harmonic Echo: ~{echo_m}:00  (burst heal amp)")
    if red_m:
        lines.append(f"  Redemption:    ~{red_m}:00  (teamfight heal active)")
    lines.append("")
    lines.append("  RECOMMENDED PURCHASE ORDER:")
    lines.append("  1) Spectral Sickle → Black Mist Scythe")
    lines.append("  2) Boots + Forbidden Idol")
    lines.append("  3) Ardent Censer (~10–12) — FIRST real buff spike")
    lines.append("  4) Ionian Boots of Lucidity (more W/E = more buff uptime)")
    lines.append("  5) Staff of Flowing Water — double buff window with Ardent")
    lines.append("  6) Harmonic Echo — heal amp / echo proc")
    lines.append("  7) Redemption — fight heal (or earlier if teamfights are constant)")
    lines.append("")
    lines.append("  PLAY PATTERN TO MAX BUFFS:")
    lines.append("  • Spam E on ADC before every trade (3 empowered autos)")
    lines.append("  • W on ADC even at full HP (Ardent/Staff still trigger in 7.2)")
    lines.append("  • Keep AH high so Ardent/Staff 6s buffs stay nearly permanent")
    lines.append("=" * 78)
    return "\n".join(lines)


def main() -> None:
    results, timeline = run()
    text = report(results, timeline)
    print(text)
    out = "/workspace/enchanter-buff-sim"
    with open(f"{out}/report.txt", "w", encoding="utf-8") as f:
        f.write(text + "\n")
    payload = {
        "meta_enchanters": ENCHANTER_META,
        "champion": "Nami",
        "timeline": timeline,
        "builds": {
            n: [
                {
                    "minute": s.minute,
                    "items": s.items,
                    "buff_score": s.buff_score,
                    "heal_hps": s.heal_hps,
                    "combat_buff_dps": s.combat_buff_dps,
                    "uptime": s.uptime,
                    "ap": s.ap,
                    "ah": s.ah,
                    "hsp": s.hsp,
                    "notes": s.notes,
                }
                for s in snaps
            ]
            for n, snaps in results.items()
        },
    }
    with open(f"{out}/results.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    with open(f"{out}/README.md", "w", encoding="utf-8") as f:
        f.write(
            "# Enchanter Buff Sim (Wild Rift 7.2+)\n\n"
            "**Strongest meta enchanter: Nami**\n\n"
            "Run: `python3 simulate_enchanter_buffs.py`\n\n"
            "Buff-max build: **Ardent → Staff → Harmonic → Redemption**\n"
        )
    print(f"\nWrote {out}/report.txt, results.json, README.md")


if __name__ == "__main__":
    main()
