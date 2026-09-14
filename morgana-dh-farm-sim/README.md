# Morgana mid — farm Dark Harvest from minute 1 to 30

Wild Rift **7.2e**. Mid. W-max. **No inventory lock**: no support-item sell, no Void ban, no pre-chosen core, no “already at 45% HP” as the only window.

Souls **stack from actual Q/W chip**. A path that opens the &lt;50% window earlier carries a stronger Harvest for the rest of the game.

## Run

```bash
python3 simulate_morgana_dh_full.py
```

Outputs:
- `report.txt` — search winner, top 12, minute-by-minute, soul timeline
- `results.json` — machine-readable ranking + winner timeline

## Question

What **full 6-slot build** (Spellslinger + 5 legendaries) farms Dark Harvest from laning through late game?

Search: 13k five-legendary completions after Blackfire / Luden / Liandry first. Crypt XOR Void (same Amethyst unique). Metric = mix of chip-from-90% + execute farm60 at 45% (QPM×Q + WPM×W + DH/35s). Echo / Squall / R are not added to hits.

## Winner (sim)

**Blackfire → Spellslinger → Rylai → Cryptbloom → Infinity Orb → Horizon Focus**

| When | Spike |
|------|--------|
| ~8:00 | **Blackfire** — burn + 20 AH |
| ~10:00 | **Spellslinger** — 18 flat + 8% (T3 opens 10:00) |
| ~14:00 | **Rylai** — W dwell 2.75s → 5s; **first OPEN** of the &lt;50% window |
| ~19:00 | **Cryptbloom** — 30% pen on every Q / W / DH |
| ~24:00 | **Infinity Orb** — 110 AP + 15 flat; 20% when chip falls under 35% |
| ~27:00 | **Horizon Focus** — Q marks, W ticks +10% |

Top 12 paths **all** buy Rylai second. 4th/5th Orb / Cap / HF / Bloodletter sit inside ~1%. Mid does **not** buy a support item.

Assuming the target is already at 45% (old lock) ranked Crypt → HF → Rylai → Cap. That path only opens **9/30** minutes from 90% HP and is **−7.2%** on the full-game score.

## Why Rylai second farms DH start-to-finish

- Every Q and every W tick is a Harvest window. Ability Haste does **not** reduce the 35s DH cooldown — it puts Q/W on the target when they drop below 50%.
- Chip from 90% has to **open** the window. Rylai at 14:00 is the first minute the dummy crosses 50%. That is 17 OPEN minutes and **40 souls** by 30:00 vs 9 OPEN / 34 souls if Rylai waits until after Crypt+HF.
- Luden-first is **−10%** even when it also takes Rylai second. Echo is not in the farm hit; Blackfire burn + 20 AH opens the window.
- Rush Orb → Cap **before** Rylai is **−11%**. Orb’s 20% is off at 45%; farm needs dwell first.
- Patch 7.2 stripped 7% pen from Horizon / Rylai / Deathcap. Pen lives on Spellslinger, Cryptbloom, Void Staff, Bloodletter.

## Play

Lane: W the wave, Q when mid is chipped, Rylai keeps them in the pool for 5s, Harvest. Fights: Q → W → DH; takedown resets CD to 1s for the next soul. Do not delay Rylai to rush Crypt / HF / Cap. Do not buy two Lost Chapter items.
