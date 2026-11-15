#!/usr/bin/env python3
"""
Rune pages for one Ryze build:

  Spellslinger, Seraph's, Deathcap, Infinity Orb, Void Staff, Blackfire

Phase Rush stays. A legal page is three primary-path runes (one per slot)
plus one secondary rune from a different path.

The previous item sim used Phase Rush, Manaflow, Transcendence, Legend: Haste
and left Sorcery slot 3 empty. That slot is Scorch, Nimbus Cloak, Gathering
Storm, or Ixtali Seedjar. This script fills it and tests Precision and Resolve.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path

from simulate_ryze_haste import (
    BRUISER,
    CombatMods,
    SQUISHY,
    TANK,
    compute_stats,
    simulate,
    ttk,
)

OUT = Path(__file__).resolve().parent

BUILD = [
    "Spellslinger's Shoes",
    "Seraph's Embrace",
    "Rabadon's Deathcap",
    "Infinity Orb",
    "Void Staff",
    "Blackfire Torch",
]

# Level 15. Base health 630 after 7.2c; growth 136 was not changed.
BASE_HP = 630 + 136 * 14  # 2534
# Gathering Storm totals, +3:00 from 6:00. 18:00 is the end-game stack
# (the next tick is 21:00). Adaptive AP: 4, 10, 18, 28, 40, 54.
GS_18 = 40.0
GS_21 = 54.0
FOCUS_AP = 40.0  # level 15, only while above 65% HP
SCORCH = 49.0  # level 15, every 8s
OVERGROWTH_STACKS = 50  # 100 enemy minions dying nearby, a normal mid game


@dataclass
class Page:
    name: str
    primary: str
    slots: tuple[str, str, str]
    secondary: str
    extra_ap: float = 0.0
    extra_mana: float = 0.0
    extra_ah: float = 0.0
    mods: CombatMods = field(default_factory=CombatMods)
    triumph: bool = False
    bloodline: bool = False
    courage: bool = False
    bone: bool = False
    nullifying: bool = False
    second_wind: bool = False
    overgrowth: bool = False
    revitalize: bool = False
    font: bool = False
    healthy_only: bool = False


def page_sorcery(slot2: str, slot3: str, secondary: str, name: str = "") -> Page:
    extra_ap = 0.0
    extra_ah = 0.0
    mods = CombatMods(transcendence=False)
    healthy = False
    if slot2 == "Transcendence":
        extra_ah += 10
        mods.transcendence = True
    elif slot2 == "Absolute Focus":
        extra_ap += FOCUS_AP
        healthy = True
    if slot3 == "Gathering Storm":
        extra_ap += GS_18
    elif slot3 == "Scorch":
        mods.scorch = True
    sec = _secondary(secondary, mods)
    extra_ah += sec["ah"]
    return Page(
        name=name or f"Sorcery: Manaflow / {slot2} / {slot3} + {secondary}",
        primary="Sorcery",
        slots=("Manaflow Band", slot2, slot3),
        secondary=secondary,
        extra_ap=extra_ap,
        extra_mana=300,
        extra_ah=extra_ah,
        mods=mods,
        healthy_only=healthy,
        **sec["flags"],
    )


def page_precision(slot1: str, slot2: str, slot3: str, secondary: str) -> Page:
    mods = CombatMods(transcendence=False)
    extra_ah = 0.0
    flags: dict = {}
    if slot1 == "Battle Zeal":
        mods.battle_zeal = True
    elif slot1 == "Triumph":
        flags["triumph"] = True
    if slot2 == "Coup de Grace":
        mods.coup = True
    elif slot2 == "Cut Down":
        mods.cut_down = True
    elif slot2 == "Last Stand":
        mods.last_stand = True
    if slot3 == "Legend: Haste":
        extra_ah += 15
    elif slot3 == "Legend: Bloodline":
        flags["bloodline"] = True
    sec = _secondary(secondary, mods)
    extra_ah += sec["ah"]
    flags.update(sec["flags"])
    return Page(
        name=f"Precision: {slot1} / {slot2} / {slot3} + {secondary}",
        primary="Precision",
        slots=(slot1, slot2, slot3),
        secondary=secondary,
        extra_ap=sec["ap"],
        extra_mana=sec["mana"],
        extra_ah=extra_ah,
        mods=mods,
        healthy_only=secondary == "Absolute Focus",
        **flags,
    )


def page_resolve(slot1: str, slot2: str, slot3: str, secondary: str) -> Page:
    mods = CombatMods(transcendence=False)
    flags = {
        "courage": slot1 == "Courage of the Colossus",
        "font": slot1 == "Font of Life",
        "bone": slot2 == "Bone Plating",
        "nullifying": slot2 == "Nullifying Orb",
        "second_wind": slot2 == "Second Wind",
        "overgrowth": slot3 == "Overgrowth",
        "revitalize": slot3 == "Revitalize",
    }
    sec = _secondary(secondary, mods)
    flags.update(sec["flags"])
    return Page(
        name=f"Resolve: {slot1} / {slot2} / {slot3} + {secondary}",
        primary="Resolve",
        slots=(slot1, slot2, slot3),
        secondary=secondary,
        extra_ap=sec["ap"],
        extra_mana=sec["mana"],
        extra_ah=sec["ah"],
        mods=mods,
        healthy_only=secondary == "Absolute Focus",
        **flags,
    )


def _secondary(name: str, mods: CombatMods) -> dict:
    out = {"ah": 0.0, "ap": 0.0, "mana": 0.0, "flags": {}}
    if name == "Legend: Haste":
        out["ah"] = 15
    elif name == "Battle Zeal":
        mods.battle_zeal = True
    elif name == "Coup de Grace":
        mods.coup = True
    elif name == "Cut Down":
        mods.cut_down = True
    elif name == "Triumph":
        out["flags"]["triumph"] = True
    elif name == "Legend: Bloodline":
        out["flags"]["bloodline"] = True
    elif name == "Manaflow Band":
        out["mana"] = 300
    elif name == "Transcendence":
        out["ah"] = 10
        mods.transcendence = True
    elif name == "Absolute Focus":
        out["ap"] = FOCUS_AP
    elif name == "Gathering Storm":
        out["ap"] = GS_18
    elif name == "Scorch":
        mods.scorch = True
    elif name == "Courage of the Colossus":
        out["flags"]["courage"] = True
    elif name == "Bone Plating":
        out["flags"]["bone"] = True
    elif name == "Nullifying Orb":
        out["flags"]["nullifying"] = True
    elif name == "Second Wind":
        out["flags"]["second_wind"] = True
    elif name == "Overgrowth":
        out["flags"]["overgrowth"] = True
    elif name == "Revitalize":
        out["flags"]["revitalize"] = True
    elif name == "Font of Life":
        out["flags"]["font"] = True
    elif name in ("Nimbus Cloak", "Ixtali Seedjar", "none"):
        pass
    else:
        raise KeyError(name)
    return out


def evaluate(page: Page) -> dict:
    st1 = compute_stats(
        BUILD, n_burn=1, extra_ap=page.extra_ap,
        extra_mana=page.extra_mana, extra_ah=page.extra_ah,
    )
    st3 = compute_stats(
        BUILD, n_burn=3, extra_ap=page.extra_ap,
        extra_mana=page.extra_mana, extra_ah=page.extra_ah,
    )
    sq = ttk(st1, SQUISHY)
    # ttk() does not forward mods. Call simulate directly.
    sq = simulate(st1, [SQUISHY], 12.0, stop_on_primary_death=True, mods=page.mods)
    br = simulate(st1, [BRUISER], 12.0, stop_on_primary_death=True, mods=page.mods)
    tk = simulate(st1, [TANK], 14.0, stop_on_primary_death=True, mods=page.mods)
    dummy = simulate(st3, [SQUISHY, BRUISER, TANK], 4.0, dummy=True, mods=page.mods)
    real = simulate(st3, [SQUISHY, BRUISER, TANK], 12.0, mods=page.mods)
    wipe = max(real.deaths.values()) if len(real.deaths) == 3 else 99.0
    life = sustain(page, st1, sq.dealt, tk.dealt)
    return {
        "name": page.name,
        "primary": page.primary,
        "slots": page.slots,
        "secondary": page.secondary,
        "healthy_only": page.healthy_only,
        "ap": round(st1.ap, 1),
        "ap_clump": round(st3.ap, 1),
        "mana": round(st1.max_mana),
        "ah": st1.ah,
        "item_ah": st1.item_ah,
        "ttk_squishy": sq.ttk if sq.ttk is not None else 99,
        "ttk_bruiser": br.ttk if br.ttk is not None else 99,
        "ttk_tank": tk.ttk if tk.ttk is not None else 99,
        "dummy4": round(dummy.dealt),
        "wipe": wipe,
        "scorch": round(dummy.by_source.get("scorch", 0)),
        "life": life,
    }


def sustain(page: Page, st, squishy_dealt: float, tank_dealt: float) -> dict:
    """Three post-mitigation hits of 1000 magic damage, then the kill's healing."""
    stacks = OVERGROWTH_STACKS if page.overgrowth else 0
    hp = BASE_HP + 3 * stacks
    if stacks >= 30:
        hp *= 1.03

    def amp(amount: float, low: bool) -> float:
        if not page.revitalize:
            return amount
        return amount * (1.15 if low else 1.05)

    shields = 0.0
    if page.courage:
        shields += amp(45 + 0.01 * hp, False)
    current = hp
    blocked = 0.0
    bone_left = 3 if page.bone else 0
    seraph = False
    orb = False
    for _ in range(3):
        dmg = 1000.0
        if bone_left:
            blocked += min(60.0, dmg)
            dmg -= min(60.0, dmg)
            bone_left -= 1
        if current - dmg < 0.35 * hp:
            if not seraph:
                seraph = True
                shields += amp(0.16 * st.max_mana, True)
            if page.nullifying and not orb:
                orb = True
                shields += amp(180.0, True)
        take = min(shields, dmg)
        shields -= take
        dmg -= take
        current = max(0.0, current - dmg)
    missing = hp - current
    heals = 0.0
    if page.second_wind:
        heals += 5 + 6 + 0.02 * missing
    if page.triumph and current > 0:
        heals += 0.10 * missing
    if page.font:
        heals += 0.01 * hp + 0.05 * st.ap
    if page.revitalize and heals > 0:
        heals *= 1.15 if current < 0.40 * hp else 1.05
    vamp = 0.0
    if page.bloodline:
        vamp = 0.07 * squishy_dealt
    return {
        "max_hp": round(hp),
        "hp_after_burst": round(current),
        "blocked": round(blocked),
        "heals": round(heals),
        "vamp_on_squishy_kill": round(vamp),
        "vamp_on_tank_kill": round(0.07 * tank_dealt) if page.bloodline else 0,
        "survived": current > 0,
        "effective": round(current + heals + vamp),
    }


def catalog() -> list[Page]:
    pages = [
        page_sorcery("Transcendence", "none", "Legend: Haste",
                     "Published baseline (slot 3 empty) + Legend: Haste"),
    ]
    for slot3 in ("Scorch", "Nimbus Cloak", "Gathering Storm", "Ixtali Seedjar"):
        pages.append(page_sorcery("Transcendence", slot3, "Legend: Haste"))
        pages.append(page_sorcery("Absolute Focus", slot3, "Legend: Haste"))
    for secondary in (
        "Legend: Haste", "Battle Zeal", "Coup de Grace", "Cut Down",
        "Triumph", "Legend: Bloodline",
        "Courage of the Colossus", "Bone Plating", "Nullifying Orb",
        "Second Wind", "Overgrowth", "Revitalize",
    ):
        pages.append(page_sorcery("Transcendence", "Gathering Storm", secondary))
        pages.append(page_sorcery("Absolute Focus", "Gathering Storm", secondary))
    for s1 in ("Battle Zeal", "Triumph"):
        for s2 in ("Coup de Grace", "Cut Down", "Last Stand"):
            for s3 in ("Legend: Haste", "Legend: Bloodline"):
                for sec in ("Manaflow Band", "Transcendence", "Absolute Focus",
                            "Gathering Storm", "Scorch"):
                    pages.append(page_precision(s1, s2, s3, sec))
    for s1 in ("Courage of the Colossus", "Font of Life"):
        for s2 in ("Bone Plating", "Nullifying Orb", "Second Wind"):
            for s3 in ("Overgrowth", "Revitalize"):
                for sec in ("Manaflow Band", "Transcendence", "Gathering Storm",
                            "Absolute Focus"):
                    pages.append(page_resolve(s1, s2, s3, sec))
    return pages


def _time(seconds: float) -> str:
    if seconds >= 90:
        return "no kill"
    return f"{seconds:.2f}s"


def render(rows: list[dict]) -> str:
    base = next(r for r in rows if r["name"].startswith("Published"))
    sorcery = [r for r in rows if r["primary"] == "Sorcery" and not r["name"].startswith("Published")]
    precision = [r for r in rows if r["primary"] == "Precision"]
    resolve = [r for r in rows if r["primary"] == "Resolve"]

    def damage_key(r):
        # Kill clock first. The infinite-HP clump keeps Cut Down on for the
        # whole fight, so it is only a tiebreak.
        return (r["ttk_tank"], r["ttk_bruiser"], r["wipe"], -r["dummy4"])

    always = [r for r in sorcery if not r["healthy_only"]]
    best_always = min(always, key=damage_key)
    focus = next(
        r for r in sorcery
        if r["slots"] == ("Manaflow Band", "Absolute Focus", "Gathering Storm")
        and r["secondary"] == "Legend: Haste"
    )
    best_precision = min(
        [r for r in precision if not r["healthy_only"]], key=damage_key
    )
    # Resolve: survive the burst, then keep as much clump damage as possible.
    best_resolve = max(resolve, key=lambda r: (r["life"]["effective"], r["dummy4"]))

    lines = []
    w = lines.append
    w("=" * 78)
    w("RYZE RUNES — BLACKFIRE BUILD, PHASE RUSH LOCKED (Wild Rift 7.3f)")
    w("Spellslinger · Seraph · Deathcap · Infinity Orb · Void · Blackfire")
    w("Level 15. Gathering Storm is the 18:00 stack (40 AP).")
    w("=" * 78)
    w("")
    w("A page is Phase Rush, one rune from each of three primary slots, and one")
    w("secondary rune. The published comparison left Sorcery slot 3 empty.")
    w("Scorch, Nimbus Cloak, Gathering Storm, and Ixtali Seedjar share that slot.")
    w("")
    w("PUBLISHED BASELINE")
    w(f"  {base['slots'][0]} / {base['slots'][1]} / (empty) + {base['secondary']}")
    w(f"  {base['ap']:.0f} AP · {base['ah']:.0f} AH · squishy {_time(base['ttk_squishy'])} · "
      f"bruiser {_time(base['ttk_bruiser'])} · tank {_time(base['ttk_tank'])} · "
      f"wipe {_time(base['wipe'])}")
    w(f"  4s clump {base['dummy4']} · HP after the 3,000 burst {base['life']['hp_after_burst']} "
      f"of {base['life']['max_hp']}")
    w("")

    def show(title: str, row: dict) -> None:
        dmg = row["dummy4"] - base["dummy4"]
        life = row["life"]["effective"] - base["life"]["effective"]
        w(title)
        w(f"  {row['name']}")
        w(f"  {row['ap']:.0f} AP ({row['ap_clump']:.0f} in a 3-person burn) · "
          f"{row['mana']} mana · {row['ah']:.0f} AH")
        w(f"  Kill: squishy {_time(row['ttk_squishy'])} · bruiser {_time(row['ttk_bruiser'])} · "
          f"tank {_time(row['ttk_tank'])} · three-man wipe {_time(row['wipe'])}")
        w(f"  4s clump {row['dummy4']} ({dmg:+d} vs the published page)")
        L = row["life"]
        w(f"  After a 3-hit 3,000 magic combo: {L['hp_after_burst']} HP left "
          f"of {L['max_hp']}, bone plating blocked {L['blocked']}, "
          f"heals {L['heals']}, omnivamp on the carry kill {L['vamp_on_squishy_kill']}")
        w(f"  HP left plus those heals: {L['effective']} ({life:+d} vs the published page)")
        if row["healthy_only"]:
            w("  Absolute Focus is included. It turns off under 65% health.")
        w("")

    show("PAGE TO RUN", best_always)
    show("ABSOLUTE FOCUS INSTEAD OF TRANSCENDENCE, WHILE YOU STAY HEALTHY", focus)
    w("  That page has more AP and kills the bruiser sooner. The tank and the")
    w("  three-man wipe take longer, because 10 haste and the cooldown refund")
    w("  are gone, and the AP turns off once Ryze is under 65% health.")
    w("")
    show("BEST PRECISION PRIMARY (one rune from each Precision slot)", best_precision)
    w("  Its kill clock matches the published page. The higher clump number is")
    w("  Cut Down, which stays on for the whole infinite-HP test. You also drop")
    w("  Manaflow, so the Seraph shield is smaller and you finish the burst lower.")
    w("")
    show("BEST RESOLVE PRIMARY (one rune from each Resolve slot)", best_resolve)

    w("-" * 78)
    w("SORCERY SLOT 3, ADDED TO THE PUBLISHED PAGE (no rune is removed)")
    w("-" * 78)
    for slot3 in ("Scorch", "Nimbus Cloak", "Gathering Storm", "Ixtali Seedjar"):
        row = next(r for r in sorcery if r["slots"][2] == slot3 and r["slots"][1] == "Transcendence"
                   and r["secondary"] == "Legend: Haste")
        w(f"  {slot3:<18} 4s clump {row['dummy4']:5d} ({row['dummy4'] - base['dummy4']:+d})  "
          f"tank {_time(row['ttk_tank']):>8}  squishy {_time(row['ttk_squishy'])}")
    w("  Nimbus Cloak and Ixtali Seedjar add no champion damage.")
    w("  Scorch is 49 magic damage every 8s. Gathering Storm is 40 AP at 18:00,")
    w("  and Deathcap multiplies it. At 21:00 the stack is 54 AP.")
    w("")
    w("-" * 78)
    w("SLOT PICKS ON THE GATHERING STORM PAGE")
    w("Manaflow stays. The other slot is the choice.")
    w("-" * 78)
    w("  Slot 2, with Gathering Storm and Legend: Haste:")
    for slot2 in ("Transcendence", "Absolute Focus"):
        row = next(r for r in sorcery if r["slots"][1] == slot2 and r["slots"][2] == "Gathering Storm"
                   and r["secondary"] == "Legend: Haste")
        tag = " (off under 65% HP)" if row["healthy_only"] else ""
        w(f"    {slot2:<16} clump {row['dummy4']:5d}  tank {_time(row['ttk_tank'])}{tag}")
    w("  Secondary, with Manaflow / Transcendence / Gathering Storm:")
    for sec in ("Legend: Haste", "Battle Zeal", "Coup de Grace", "Cut Down",
                "Legend: Bloodline", "Triumph", "Bone Plating", "Nullifying Orb",
                "Overgrowth", "Courage of the Colossus", "Second Wind"):
        row = next(r for r in sorcery if r["slots"][1] == "Transcendence"
                   and r["slots"][2] == "Gathering Storm" and r["secondary"] == sec)
        L = row["life"]
        w(f"    {sec:<24} clump {row['dummy4']:5d} ({row['dummy4'] - base['dummy4']:+d})  "
          f"tank {_time(row['ttk_tank']):>8}  after burst {L['effective']}")
    w("")
    w("-" * 78)
    w("WHAT EACH PRECISION SLOT IS WORTH")
    w("These are the primary-page winners' building blocks. Taking the whole")
    w("tree means giving up Manaflow or Gathering Storm, not adding them.")
    w("-" * 78)
    # Isolate each precision slot against Manaflow as the only sorcery rune,
    # with the other two precision slots on the damage defaults.
    w("  Same secondary (Manaflow) so the slot itself is the change:")
    probes = [
        ("Battle Zeal / Coup / Legend: Haste", "Battle Zeal", "Coup de Grace", "Legend: Haste"),
        ("Triumph / Coup / Legend: Haste", "Triumph", "Coup de Grace", "Legend: Haste"),
        ("Battle Zeal / Cut Down / Legend: Haste", "Battle Zeal", "Cut Down", "Legend: Haste"),
        ("Battle Zeal / Last Stand / Legend: Haste", "Battle Zeal", "Last Stand", "Legend: Haste"),
        ("Battle Zeal / Coup / Bloodline", "Battle Zeal", "Coup de Grace", "Legend: Bloodline"),
    ]
    for label, a, b, c in probes:
        row = next(r for r in precision if r["slots"] == (a, b, c) and r["secondary"] == "Manaflow Band")
        L = row["life"]
        w(f"    {label}")
        w(f"      clump {row['dummy4']} ({row['dummy4'] - base['dummy4']:+d})  "
          f"tank {_time(row['ttk_tank'])}  after burst {L['effective']} "
          f"(vamp {L['vamp_on_squishy_kill']}, heal {L['heals']})")
    w("")
    w("-" * 78)
    w("WHAT EACH RESOLVE SLOT IS WORTH")
    w("-" * 78)
    rprobes = [
        ("Courage / Bone Plating / Overgrowth", "Courage of the Colossus", "Bone Plating", "Overgrowth"),
        ("Font of Life / Bone Plating / Overgrowth", "Font of Life", "Bone Plating", "Overgrowth"),
        ("Courage / Nullifying Orb / Overgrowth", "Courage of the Colossus", "Nullifying Orb", "Overgrowth"),
        ("Courage / Second Wind / Overgrowth", "Courage of the Colossus", "Second Wind", "Overgrowth"),
        ("Courage / Bone Plating / Revitalize", "Courage of the Colossus", "Bone Plating", "Revitalize"),
    ]
    for label, a, b, c in rprobes:
        row = next(r for r in resolve if r["slots"] == (a, b, c) and r["secondary"] == "Manaflow Band")
        L = row["life"]
        w(f"    {label} + Manaflow")
        w(f"      clump {row['dummy4']} ({row['dummy4'] - base['dummy4']:+d})  "
          f"HP {L['max_hp']}  left after burst {L['hp_after_burst']}  "
          f"blocked {L['blocked']}  heals {L['heals']}  effective {L['effective']}")
    w("")
    w("-" * 78)
    w("ASSUMPTIONS")
    w("-" * 78)
    w("  Phase Rush is on every page. Its 10 haste and 20% cooldown cut still happen.")
    w("  Gathering Storm is 40 AP from 18:00 until 21:00, then 54 AP. Deathcap,")
    w("  Seraph, and Arcane Mastery all see that AP.")
    w("  Absolute Focus is 40 AP at level 15 and is included only while Ryze is")
    w("  above 65% health. The damage fights do not hit Ryze, so it stays on there.")
    w("  Scorch is 49 magic damage every 8 seconds, one champion, then magic resist.")
    w("  Battle Zeal is 1.4% per second on basic abilities, up to 4.2% at 3 seconds.")
    w("  It does nothing to a kill that ends at 0.75s.")
    w("  Cut Down is 6.5% damage against champions above 60% health.")
    w("  Coup de Grace is 8% damage against champions below 40% health.")
    w("  Last Stand is 5% at full health up to 11% at 30% health.")
    w("  Legend: Haste is 15. Legend: Bloodline is 7% omnivamp, full value on a")
    w("  one-champion fight. Area spells against a team heal at 33% of that.")
    w("  The burst is three hits of 1,000 post-mitigation magic damage.")
    w("  Bone Plating shaves 60 off each of those hits. Seraph's shield is 16% of")
    w("  current mana when a hit would cross 35% health. Nullifying Orb is 180.")
    w("  Courage of the Colossus is 45 + 1% max health, from landing Rune Prison.")
    w("  Overgrowth is 50 stacks: 150 health, then +3% health.")
    w("  Second Wind, for a ranged champion, is 5 health per 5 seconds plus")
    w("  6 + 2% missing health over 5 seconds after you are hit.")
    w("  Revitalize is +5% to your heals and shields, or +15% under 40% health.")
    w("  It does not increase omnivamp. Nimbus Cloak and Ixtali Seedjar do not")
    w("  change these numbers. Axiom Arcanist does not either: Realm Warp deals")
    w("  no damage. Brutal and Legend: Alacrity are auto-attack runes.")
    w("")
    return "\n".join(lines)


def main() -> None:
    pages = catalog()
    rows = [evaluate(p) for p in pages]
    # Drop duplicate names from the double-added gathering+haste pages.
    seen = set()
    unique = []
    for row in rows:
        if row["name"] in seen:
            continue
        seen.add(row["name"])
        unique.append(row)
    text = render(unique)
    (OUT / "runes-report.txt").write_text(text)
    (OUT / "runes-results.json").write_text(json.dumps(unique, indent=2))
    print(text)
    print(f"{len(unique)} pages")


if __name__ == "__main__":
    main()
