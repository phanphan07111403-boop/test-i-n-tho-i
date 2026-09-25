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

What 6-item page is **strongest late** (20:00–25:00) now that Magnetic Blaster is gone, Infinity Edge is the crit-ability capstone, and Q scales with critical chance **and** bonus critical damage?

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

## Playstyle

- Skill order: max **Q** → W → E. R at 6/11/15.
- Stack by last-hitting with Q and poking champs. T3 ~18:00.
- Poke from 550 — Hexoptics is already at max amp. Save E to leave.
- Fight: Q weave, W explosion, R through the clump (and yourself for the heal).
