# Smolder ADC — Strongest Late Build (Wild Rift 7.3)

Patch **7.3** marksman overhaul. Super Scorcher Breath siege over a **25-minute** game.

## Run

```bash
python3 simulate_smolder_late.py
```

Outputs:
- `report.txt` — minute-by-minute optimal + late ranking
- `results.json` — machine-readable snapshots per build

## Question answered

What 6-item page is **strongest late** (20:00–25:00) now that Magnetic Blaster is gone, Infinity Edge is the crit-ability capstone, and Q scales with critical chance **and** bonus critical damage? Which boots keep the extra Super Scorcher — Ionian vs Greaves vs Immortal Treads?

## Winner (sim)

**Essence Reaver → Ionian Boots → Infinity Edge → Hexoptics C44 → Lord Dominik's Regards → Bloodthirster**

At 22:00 this path deals **22% more** mix damage than the old Muramana → Trinity → Serylda → Shojin page (6052 vs 4941 per 8s). At 25:00 the gap is **+29%** (7284 vs 5644). Isolated 2nd-item spike: Infinity Edge **+1012**.

| When | Spike |
|------|--------|
| ~6–9:00 | **Essence Reaver** — Spellblade rides on Q (on-hit) |
| ~13:00 | **Infinity Edge** — Q amp uses 230% crit damage |
| ~17:00 | **Hexoptics C44** — 10% damage at Q's 550 range |
| ~18:00 | **T3 burn** (175 Dragon Practice) — true %HP + 6.5% execute |
| ~21:00 | **LDR** — 100% crit + 35% pen + Giant Slayer |

## Why

- Q is increased by 0–45% from crit chance, then again by Infinity Edge's extra crit damage (wiki +0–13.5%). At 100% crit + IE that is a **58.5%** multiplier on Super Scorcher physical; Dragon Practice magic goes **30% → 69%** of stacks.
- Patch 7.3 raised base crit damage 175% → 200% and made IE the capstone (75 AD, 230% crit). Magnetic Blaster is removed; Hexoptics is the poke replacement.
- Muramana → Trinity still shocks, but **0% crit** means Q never gets the 7.3 amp. IE arrives as item 5 and the page is already behind.
- Shojin 12% ability amp is real, but it delays 100% crit. Navori refunds Q (5 vs 4 casts) but has **0 AD** — extra Qs lose to Hexoptics' 55 AD + 10% range amp.
- Swap LDR → **Mortal Reminder** if they heal. Shieldbow/Maw/GA instead of Bloodthirster vs dive.

## IE 2nd vs 3rd — stacking

Dragon Practice income is **Q count**, not Q damage. Essence Reaver already one-shots casters (~8:00), so last-hit reliability is 100% before Infinity Edge.

| 2nd legendary | T3 (175) | Stacks @16 | Mix @16 | Mix @22 |
|---------------|----------|------------|---------|---------|
| **IE** then Hex | 17:00 | 160 | **2830** | 6110 |
| **Hex** then IE | 17:00 | 163 (+2) | 2751 | 6118 (same page) |
| **Shojin** then IE | 17:00 | **171** (+11) | 2412 | 5321 (T3 on 25% crit Q) |

- Do **not** buy IE 2nd to stack. Buy it 2nd to convert stacks into Super Scorcher damage in the 13–16 window.
- Hex 2nd is a wash on stacks (safer champion hits) and a cheaper 2nd-item spike. IE 3rd after Hex hits the same T3 clock.
- Shojin 2nd is the real stacking purchase (more Qs) but T3 lands without IE/Hex — the extra stacks do not pay.

## Runes that fit (sim, same items)

**Fleet Footwork / Battle Zeal / Cut Down / Legend: Bloodline / Transcendence**

| Rune | Why it fits this page |
|------|------------------------|
| **Fleet Footwork** | Q is on-attack — fireball procs heal, 20% MS, mana. You live to 175 stacks. 0 item AS, so Fleet is uptime not DPS. |
| **Battle Zeal** | +2%/s basic-ability damage, cap 6%. Amps Q/W/E and the T3 burn. Beats Brutal on this page. |
| **Cut Down** | Poke hits healthy targets. Coup is the same slot and overlaps the 6.5% T3 execute. |
| **Legend: Bloodline** | 7% omnivamp heals off Q magic + true burn (BT lifesteal does not). In 8s, Legend: Haste is the same 4 Qs — take Haste only if you already have vamp. |
| **Transcendence** | 10 AH + 8% refund. Dropping it for Bone Plating costs a Q (3 vs 4). Bone Plating only vs Lucian/Draven/Leona, then swap back. |

**Do not take:** Lethal Tempo (7.3 wants AS items; this page has none). Conqueror (paper AD if you stand in melee; Hexoptics poke is max range). Coup de Grace. Legend: Alacrity.

**Swap:** Phase Rush vs dive/ganks. Barrier + Flash.

## Boots that fit (sim, same items)

**Ionian Boots of Lucidity** — sit on T2. 15 AH is the 4th Super Scorcher in 8s.

Locked legendaries: Essence Reaver → Infinity Edge → Hexoptics C44 → LDR → Bloodthirster. T3 boots unlock at 10:00 and cost +1000g.

| Boot | Gold | IE | Qs @22 | Mix @22 | Mix @25 |
|------|------|----|--------|---------|---------|
| **Ionian (T2)** | 1000 | 13:00 | **4** | **6110** | **7359** |
| Crimson Lucidity (T3) | 2000 | 15:00 | 4 | 6142 | 6892 (BT delayed) |
| Gluttonous Greaves (T2) | 1000 | 13:00 | 3 | 5300 | 6348 |
| Immortal Treads (T3) | 2000 | 15:00 | 3 | 5565 | 6201 |
| Berserker's (T2) | 1200 | 13:00 | 3 | 5377 | 6205 |
| Gunmetal (T3) | 2200 | 15:00 | 3 | 4348 | 6112 |

- One extra fireball beats 12 AD, 5% healthy damage, and extra autos. Greaves is **−13%** mix at 22:00 (5300 vs 6110). Immortal's 5% while healthy still fires 3 Qs and delays IE two minutes.
- Crimson paper-leads 22:00 by 32 damage (same 4 Qs, 25 AH) then loses **−467** at 25:00 because the extra 1000g delays Bloodthirster. ~90 AH is needed for a 5th Q in 8s — T3 Ionian is not that.
- Berserker's does **not** win the fight either (fight-tank 7046 vs Ionian 7233). Hexoptics poke does not auto. Gunmetal 5% LS is physical; Q magic + T3 true burn do not heal from it.
- Bloodline already gives 7% omnivamp. Greaves/Immortal only if you are diving and dying.
- Mercury's / Steelcaps vs heavy CC / all-in AD. 0 extra Qs.

## Playstyle

- Skill order: max **Q** → W → E. R at 6/11/15.
- Stack by last-hitting with Q and poking champs. T3 ~18:00.
- Poke from 550 — Hexoptics is already at max amp. Save E to leave.
- Fight: Q weave, W explosion, R through the clump (and yourself for the heal).
