#!/usr/bin/env python3
"""
Head-to-head: Aggressive DH Senna vs IE + Muramana Senna
Wild Rift Patch 7.2+ | 20-minute game

Compares:
  1) Overall damage dealt across the game (skirmish + teamfight windows)
  2) Single teamfight damage (8s objective fight)
  3) Peak execute / sustained DPS tradeoffs

Builds:
  DH BUILD  — Dark Harvest + Draktharr → Collector → Magnetic
  IE+MURA   — No DH (Fleet/Grasp style) + Manamune → Magnetic → IE → Mortal
"""

from __future__ import annotations

from typing import Dict, List, Tuple
import json

from simulate_senna_dh import (
    GAME_MINUTES,
    BUILD_PATHS,
    compute_snapshot,
    gold_at_minute,
    level_at_minute,
    mist_at_minute,
    target_max_hp,
    armor_mult,
    q_rank,
    q_base_damage,
    living_extraction_pct,
    nightstalker_damage,
    magnetic_energized,
    resolve_inventory,
    SENNA_BASE_AD,
    Snapshot,
)

# Canonical paths for this matchup
DH_NAME = "Draktharr → Collector → Magnetic (DH Farm)"
# Dedicated IE+Muramana path (added below if missing)
IE_MURA_NAME = "Manamune → Magnetic → IE (Crit Scale)"
IE_MURA_PATH = [
    "Tear of the Goddess",
    "Long Sword",
    "Boots of Speed",
    "Manamune",
    "Boots of Dynamism",
    "Magnetic Blaster",
    "B.F. Sword",
    "Infinity Edge",
    "Mortal Reminder",
]


def ensure_ie_mura_path() -> None:
    if IE_MURA_NAME not in BUILD_PATHS:
        BUILD_PATHS[IE_MURA_NAME] = IE_MURA_PATH


def build_stats(name: str, path: List[str], minute: int, use_dh: bool) -> Snapshot:
    s = compute_snapshot(name, path, minute)
    if not use_dh:
        # Strip DH contribution — IE+Mura runs Fleet/Grasp, not Dark Harvest
        s.dh_souls = 0
        s.dh_procs_cum = 0
        s.dh_proc_damage = 0.0
        # Recompute combo/peak without DH proc
        # combo_burst already includes dh_proc; subtract it
        # peak_execute includes collector credit; keep items, drop DH only
        # Approximate: remove dh from combo/peak
        # We stored dh_proc_damage before zeroing — use local recalc below in TF model
        pass
    return s


def fight_model(
    minute: int,
    path: List[str],
    use_dh: bool,
    fight_seconds: float = 8.0,
    secondary_targets: float = 1.4,
) -> Dict:
    """
    8s objective teamfight model.
    Primary squishy focus + Q pierce / Magnetic bounce onto secondaries.
    AA → Q weave (optimal extraction order).
    """
    s = compute_snapshot("tmp", path, minute)
    level = s.level
    mist = s.mist
    bonus_ad = s.bonus_ad
    total_ad = s.total_ad
    crit = s.crit
    flat = s.flat_apen
    pct = s.pct_apen
    inv = resolve_inventory(path, gold_at_minute(minute), minute)

    has_drak = any(it.lethality_burst for it in inv)
    has_collector = any(it.collector for it in inv)
    has_mura = any(it.muramana for it in inv)
    has_mana = any(it.manamune for it in inv)
    has_magnetic = any(it.magnetic for it in inv)
    has_ie = any(it.ie for it in inv)
    has_serylda = any(it.serylda for it in inv)
    mana = sum(it.mana for it in inv)
    ah = sum(it.ah for it in inv)
    as_pct = sum(it.as_pct for it in inv)

    pen = armor_mult(flat, pct, level, minute)
    hp = target_max_hp(minute)
    crit_mult = 2.05 if has_ie else 1.4175

    # Attack speed — Senna is slow but Magnetic + levels help
    base_as = 0.65 + 0.02 * (level - 1)
    attacks_per_sec = base_as * (1 + as_pct)
    # Q weave: roughly 1 Q per 4–6s depending on AH + AA refunds
    q_cd = 15.0 / (1 + ah / 100.0)
    # Aggressive AA refunds ~2–3s effective per Q window
    q_cd_eff = max(3.2, q_cd - 2.2)
    qs = fight_seconds / q_cd_eff
    autos = fight_seconds * attacks_per_sec

    # Per auto (expected crit)
    aa_raw = total_ad + 0.20 * total_ad  # Relic Cannon
    aa_exp = aa_raw * (1 + crit * (crit_mult - 1))

    # Per Q
    qr = q_rank(level)
    q_dmg = q_base_damage(qr) + 0.60 * bonus_ad

    # Extraction: AA→Q once per Q (consume on Q). Current HP ~70% avg mid-fight
    extract = living_extraction_pct(level) * (0.70 * hp)

    # Muramana
    mura_aa = 0.0
    mura_q = 0.0
    if has_mura:
        cur_mana = mana + 400
        mura_aa = 0.03 * cur_mana
        mura_q = 0.04 * cur_mana + 0.045 * bonus_ad
    elif has_mana:
        cur_mana = mana * 0.7 + 280
        mura_aa = 0.03 * cur_mana * 0.6
        mura_q = 0.04 * cur_mana * 0.6 + 0.045 * bonus_ad * 0.5

    # Draktharr — once per target engaged (primary + maybe secondary if reset)
    drak = nightstalker_damage(level) if has_drak else 0.0

    # Magnetic energized — ~every 4th attack, bounce hits secondaries
    mag = magnetic_energized(level) if has_magnetic else 0.0
    mag_mr = 100 / (100 + 30 + level)
    mag_hits = autos / 4.0

    # Primary target physical
    primary_phys = (
        autos * (aa_exp + mura_aa)
        + qs * (q_dmg + extract + mura_q)
        + drak
    ) * pen
    primary_mag = mag_hits * mag * mag_mr

    # Dark Harvest in teamfight
    dh_damage = 0.0
    dh_procs = 0
    if use_dh:
        # Souls already farmed by this minute (aggressive curve)
        souls = s.dh_souls
        dh_raw = (35 + 11 * souls + 0.10 * bonus_ad) * 0.80
        # In an 8s TF with resets: 1 opener + 1–2 on takedowns if burst high
        # DH build chains better; IE path wouldn't have DH here
        base_procs = 1.0
        if has_drak or has_collector:
            # Likely 1 kill mid-fight → reset → 2nd proc; sometimes 3rd
            reset_procs = 1.35 if minute >= 12 else 0.9
        else:
            reset_procs = 0.4
        dh_procs = base_procs + reset_procs
        dh_damage = dh_procs * dh_raw * pen

    # Collector execute credit on primary (partial)
    collector_credit = 0.0
    if has_collector:
        exec_pct = 0.04 + 0.02 * crit
        collector_credit = exec_pct * hp * 0.45

    primary_total = primary_phys + primary_mag + dh_damage + collector_credit

    # Secondary splash: Q pierce (~55% of Q package) + Magnetic bounce
    q_splash = qs * (q_dmg * 0.55 + mura_q * 0.4) * pen * secondary_targets
    mag_splash = mag_hits * mag * mag_mr * 0.85 * secondary_targets
    # DH rarely hits secondaries unless multi-execute (partial)
    dh_splash = dh_damage * 0.25 * secondary_targets if use_dh else 0.0
    # Draktharr can refresh on takedown → second Nightstalker
    drak_splash = (drak * 0.65 * pen) if (has_drak and use_dh) else 0.0

    splash = q_splash + mag_splash + dh_splash + drak_splash
    tf_total = primary_total + splash

    # Sustained DPS over the fight
    dps = tf_total / fight_seconds

    return {
        "minute": minute,
        "fight_seconds": fight_seconds,
        "primary": round(primary_total, 1),
        "splash": round(splash, 1),
        "tf_total": round(tf_total, 1),
        "dps": round(dps, 1),
        "dh_procs": round(dh_procs, 2),
        "dh_damage": round(dh_damage, 1),
        "autos": round(autos, 2),
        "qs": round(qs, 2),
        "mist": mist,
        "bonus_ad": round(bonus_ad, 1),
        "crit": round(crit, 3),
        "items": [it.name for it in inv],
        "use_dh": use_dh,
    }


def skirmish_damage_per_minute(minute: int, path: List[str], use_dh: bool) -> float:
    """
    Expected champion damage from skirmishes this minute (not full TF).
    Aggressive game: short 3–4s trades / river fights.
    """
    s = compute_snapshot("tmp", path, minute)
    # Short trade ≈ 40% of an 8s TF primary (less splash)
    tf = fight_model(minute, path, use_dh, fight_seconds=3.5, secondary_targets=0.35)
    if minute <= 4:
        fights = 0.85
    elif minute <= 10:
        fights = 1.25
    else:
        fights = 1.15  # more time in objectives, fewer random skirmishes
    # DH build fights slightly more often (aggression)
    if use_dh:
        fights *= 1.12
    return tf["tf_total"] * fights


def teamfight_damage_per_minute(minute: int, path: List[str], use_dh: bool) -> float:
    """Objective / 5v5 windows — rarer early, common mid-late."""
    tf = fight_model(minute, path, use_dh, fight_seconds=8.0, secondary_targets=1.4)
    if minute < 8:
        tfs = 0.15
    elif minute < 14:
        tfs = 0.45
    else:
        tfs = 0.70
    return tf["tf_total"] * tfs


def overall_curve(path: List[str], use_dh: bool) -> List[Dict]:
    rows = []
    cum = 0.0
    for m in range(1, GAME_MINUTES + 1):
        sk = skirmish_damage_per_minute(m, path, use_dh)
        tf = teamfight_damage_per_minute(m, path, use_dh)
        total_m = sk + tf
        cum += total_m
        snap = compute_snapshot("tmp", path, m)
        rows.append(
            {
                "minute": m,
                "skirmish": round(sk, 1),
                "teamfight_contrib": round(tf, 1),
                "minute_total": round(total_m, 1),
                "cumulative": round(cum, 1),
                "items": snap.items,
                "mist": snap.mist,
                "bonus_ad": snap.bonus_ad,
            }
        )
    return rows


def compare() -> Tuple[str, Dict]:
    ensure_ie_mura_path()
    dh_path = BUILD_PATHS[DH_NAME]
    ie_path = BUILD_PATHS[IE_MURA_NAME]

    dh_overall = overall_curve(dh_path, use_dh=True)
    ie_overall = overall_curve(ie_path, use_dh=False)

    # Teamfight snapshots at key times (standard 8s + extended 12s slugfest)
    tf_minutes = [8, 12, 16, 20]
    dh_tfs = {m: fight_model(m, dh_path, True) for m in tf_minutes}
    ie_tfs = {m: fight_model(m, ie_path, False) for m in tf_minutes}
    dh_tfs_long = {m: fight_model(m, dh_path, True, fight_seconds=12.0, secondary_targets=1.6) for m in tf_minutes}
    ie_tfs_long = {m: fight_model(m, ie_path, False, fight_seconds=12.0, secondary_targets=1.6) for m in tf_minutes}

    lines: List[str] = []
    lines.append("=" * 78)
    lines.append("SENNA HEAD-TO-HEAD: DH BUILD vs IE + MURAMANA")
    lines.append("Wild Rift Patch 7.2+ | Aggressive ADC | 20:00 game")
    lines.append("=" * 78)
    lines.append("")
    lines.append("BUILDS")
    lines.append(f"  DH BUILD : Dark Harvest + {DH_NAME}")
    lines.append("             Draktharr → Dynamism → Collector → Magnetic → Serylda/IE")
    lines.append(f"  IE+MURA  : Fleet/Grasp (NO Dark Harvest) + {IE_MURA_NAME}")
    lines.append("             Manamune → Dynamism → Magnetic → IE → Mortal Reminder")
    lines.append("  Combo both: AA → Q weave")
    lines.append("")

    # ----- Overall damage -----
    lines.append("-" * 78)
    lines.append("1) OVERALL DAMAGE DEALT (skirmish + teamfight windows, cumulative)")
    lines.append("-" * 78)
    lines.append(
        f"  {'Min':>3}  {'DH skirm':>9}  {'DH TF':>8}  {'DH cum':>9}  |"
        f"  {'IE skirm':>9}  {'IE TF':>8}  {'IE cum':>9}  | leader"
    )
    for d, i in zip(dh_overall, ie_overall):
        m = d["minute"]
        leader = "DH" if d["cumulative"] >= i["cumulative"] else "IE+Mura"
        if abs(d["cumulative"] - i["cumulative"]) < d["cumulative"] * 0.03:
            leader = "≈"
        lines.append(
            f"  {m:>3}  {d['skirmish']:>9.0f}  {d['teamfight_contrib']:>8.0f}  "
            f"{d['cumulative']:>9.0f}  |  {i['skirmish']:>9.0f}  "
            f"{i['teamfight_contrib']:>8.0f}  {i['cumulative']:>9.0f}  | {leader}"
        )

    dh_end = dh_overall[-1]["cumulative"]
    ie_end = ie_overall[-1]["cumulative"]
    pct = (dh_end - ie_end) / ie_end * 100
    lines.append("")
    lines.append(f"  @ 20:00 total damage dealt:")
    lines.append(f"    DH BUILD : {dh_end:,.0f}")
    lines.append(f"    IE+MURA  : {ie_end:,.0f}")
    if dh_end >= ie_end:
        lines.append(f"    → DH leads by {dh_end - ie_end:,.0f} ({pct:+.1f}%)")
    else:
        lines.append(f"    → IE+Mura leads by {ie_end - dh_end:,.0f} ({-pct:+.1f}%)")

    # When does IE catch up?
    crossover = None
    for d, i in zip(dh_overall, ie_overall):
        if i["cumulative"] > d["cumulative"]:
            crossover = d["minute"]
            break
    if crossover:
        lines.append(f"    IE+Mura overtakes cumulative at ~{crossover}:00")
    else:
        lines.append("    DH stays ahead on cumulative damage for the full 20:00")

    # ----- Teamfight -----
    lines.append("")
    lines.append("-" * 78)
    lines.append("2) TEAMFIGHT DAMAGE (8s objective fight, 1 primary + ~1.4 splash)")
    lines.append("-" * 78)
    lines.append(
        f"  {'Min':>3}  {'DH primary':>11}  {'DH splash':>10}  {'DH total':>9}  "
        f"{'DH DPS':>7}  |  {'IE primary':>11}  {'IE splash':>10}  {'IE total':>9}  {'IE DPS':>7}"
    )
    for m in tf_minutes:
        d = dh_tfs[m]
        i = ie_tfs[m]
        lines.append(
            f"  {m:>3}  {d['primary']:>11.0f}  {d['splash']:>10.0f}  {d['tf_total']:>9.0f}  "
            f"{d['dps']:>7.0f}  |  {i['primary']:>11.0f}  {i['splash']:>10.0f}  "
            f"{i['tf_total']:>9.0f}  {i['dps']:>7.0f}"
        )
        lines.append(
            f"       DH items: {' › '.join(d['items'][:5])}{' › …' if len(d['items'])>5 else ''}"
        )
        lines.append(
            f"       IE items: {' › '.join(i['items'][:5])}{' › …' if len(i['items'])>5 else ''}"
        )
        if d["use_dh"]:
            lines.append(
                f"       DH procs in TF: ~{d['dh_procs']:.1f} "
                f"(+{d['dh_damage']:.0f} dmg from souls)"
            )

    lines.append("")
    lines.append("-" * 78)
    lines.append("2b) EXTENDED TEAMFIGHT (12s slugfest — favors sustained crit)")
    lines.append("-" * 78)
    lines.append(
        f"  {'Min':>3}  {'DH 12s TF':>10}  {'IE 12s TF':>10}  {'gap':>8}  winner"
    )
    for m in tf_minutes:
        d = dh_tfs_long[m]
        i = ie_tfs_long[m]
        gap = d["tf_total"] - i["tf_total"]
        winner = "DH" if gap >= 0 else "IE+Mura"
        lines.append(
            f"  {m:>3}  {d['tf_total']:>10.0f}  {i['tf_total']:>10.0f}  "
            f"{gap:>+8.0f}  {winner}"
        )

    lines.append("")
    lines.append("-" * 78)
    lines.append("3) PEAK EXECUTE vs SUSTAINED (same minute snapshots)")
    lines.append("-" * 78)
    lines.append(
        f"  {'Min':>3}  {'DH peak exec':>13}  {'DH combo':>9}  {'DH souls':>8}  |"
        f"  {'IE peak*':>9}  {'IE combo*':>9}  {'IE crit':>7}"
    )
    lines.append("  (* IE+Mura numbers exclude Dark Harvest — Fleet/Grasp keystone)")
    for m in tf_minutes:
        d_snap = compute_snapshot(DH_NAME, dh_path, m)
        i_snap = compute_snapshot(IE_MURA_NAME, ie_path, m)
        # Strip phantom DH from IE path (compute_snapshot always models souls)
        ie_combo = max(0.0, i_snap.combo_burst - i_snap.dh_proc_damage)
        ie_peak = max(0.0, i_snap.peak_execute - i_snap.dh_proc_damage)
        lines.append(
            f"  {m:>3}  {d_snap.peak_execute:>13.0f}  {d_snap.combo_burst:>9.0f}  "
            f"{d_snap.dh_souls:>8}  |  {ie_peak:>9.0f}  "
            f"{ie_combo:>9.0f}  {i_snap.crit*100:>6.0f}%"
        )

    # ----- Verdict -----
    dh_tf20 = dh_tfs[20]["tf_total"]
    ie_tf20 = ie_tfs[20]["tf_total"]
    dh_tf12 = dh_tfs[12]["tf_total"]
    ie_tf12 = ie_tfs[12]["tf_total"]
    dh_long20 = dh_tfs_long[20]["tf_total"]
    ie_long20 = ie_tfs_long[20]["tf_total"]

    lines.append("")
    lines.append("-" * 78)
    lines.append("VERDICT")
    lines.append("-" * 78)
    lines.append("")
    lines.append("  OVERALL DAMAGE DEALT (full game):")
    if dh_end >= ie_end:
        lines.append(
            f"    WINNER → DH BUILD ({dh_end:,.0f} vs {ie_end:,.0f}, {pct:+.1f}%)"
        )
        lines.append("    Early/mid skirmish resets print souls AND kills → snowball damage.")
    else:
        lines.append(
            f"    WINNER → IE+MURAMANA ({ie_end:,.0f} vs {dh_end:,.0f}, {-pct:+.1f}%)"
        )
        lines.append("    Late crit + Muramana Shock sustain overtakes on raw throughput.")

    lines.append("")
    lines.append("  TEAMFIGHT:")
    lines.append(f"    8s @12:00   DH {dh_tf12:,.0f}  vs  IE+Mura {ie_tf12:,.0f}  → "
                 f"{'DH' if dh_tf12 >= ie_tf12 else 'IE+Mura'}")
    lines.append(f"    8s @20:00   DH {dh_tf20:,.0f}  vs  IE+Mura {ie_tf20:,.0f}  → "
                 f"{'DH' if dh_tf20 >= ie_tf20 else 'IE+Mura'}")
    lines.append(f"    12s @20:00  DH {dh_long20:,.0f}  vs  IE+Mura {ie_long20:,.0f}  → "
                 f"{'DH' if dh_long20 >= ie_long20 else 'IE+Mura'}")
    gap8 = (dh_tf20 - ie_tf20) / ie_tf20 * 100
    gap12 = (dh_long20 - ie_long20) / ie_long20 * 100
    lines.append(f"    Gap shrinks in longer fights: 8s {gap8:+.0f}% → 12s {gap12:+.0f}%")
    lines.append("")
    lines.append("  WHEN TO PICK WHICH:")
    lines.append("    DH BUILD  — snowball games, dive comps, short skirmishes, want to")
    lines.append("                delete a carry then chain the next (reset engine).")
    lines.append("                Stronger mid game + overall if you keep fighting.")
    lines.append("    IE+MURA   — longer teamfights, need sustained DPS + Q poke/heal,")
    lines.append("                safer range carry. Closes the gap as fights drag;")
    lines.append("                wins if you cannot collect DH resets / fall behind.")
    lines.append("")
    lines.append("  KEY TRADEOFF:")
    lines.append("    DH = front-loaded burst + soul scaling on executes")
    lines.append("    IE+Mura = back-loaded crit DPS + Muramana Shock every Q")
    lines.append("    Splash (Q pierce / Magnetic bounce): IE+Mura gains in long TF;")
    lines.append("    DH still wins multi-kill TFs when Nightstalker + DH reset twice.")
    lines.append("=" * 78)

    payload = {
        "meta": {
            "dh_build": DH_NAME,
            "ie_mura_build": IE_MURA_NAME,
            "dh_rune": True,
            "ie_rune": "Fleet/Grasp (no Dark Harvest)",
        },
        "overall": {"dh": dh_overall, "ie_mura": ie_overall},
        "teamfights": {"dh": dh_tfs, "ie_mura": ie_tfs},
        "teamfights_12s": {"dh": dh_tfs_long, "ie_mura": ie_tfs_long},
        "totals": {
            "dh_cumulative_20": dh_end,
            "ie_cumulative_20": ie_end,
            "dh_tf_12": dh_tf12,
            "ie_tf_12": ie_tf12,
            "dh_tf_20": dh_tf20,
            "ie_tf_20": ie_tf20,
            "dh_tf12s_20": dh_long20,
            "ie_tf12s_20": ie_long20,
        },
    }
    return "\n".join(lines), payload


def main() -> None:
    report, payload = compare()
    print(report)
    with open("/workspace/senna-dh-sim/compare_dh_vs_ie_report.txt", "w", encoding="utf-8") as f:
        f.write(report + "\n")
    with open("/workspace/senna-dh-sim/compare_dh_vs_ie_results.json", "w", encoding="utf-8") as f:
        # Convert int keys in teamfights
        out = payload.copy()
        out["teamfights"] = {
            "dh": {str(k): v for k, v in payload["teamfights"]["dh"].items()},
            "ie_mura": {str(k): v for k, v in payload["teamfights"]["ie_mura"].items()},
        }
        out["teamfights_12s"] = {
            "dh": {str(k): v for k, v in payload["teamfights_12s"]["dh"].items()},
            "ie_mura": {str(k): v for k, v in payload["teamfights_12s"]["ie_mura"].items()},
        }
        json.dump(out, f, indent=2)
    print("\nWrote compare_dh_vs_ie_report.txt and compare_dh_vs_ie_results.json")


if __name__ == "__main__":
    main()
