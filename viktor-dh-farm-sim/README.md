# Viktor mid — farm Dark Harvest from minute 1 to 30

Wild Rift **7.2e**. Mid. E-max. Same method as the Morgana sim: no support-item sell, no Void ban, no pre-chosen core, no “already at 45% HP” as the only window.

Viktor farms with **Hextech Ray** (laser + Blastquake) and **Siphon Power**. Laser applies Horizon Focus; the 1s aftershock is amplified. Echo / Squall / R are not added to hits.

## Run

```bash
python3 simulate_viktor_dh_full.py
```

Outputs:
- `report.txt` — search winner, top 12, minute-by-minute, soul timeline
- `results.json` — machine-readable ranking + winner timeline

## Winner (sim)

**Blackfire → Spellslinger → Cryptbloom → Horizon Focus → Bloodletter → Deathcap**

| When | Spike |
|------|--------|
| ~8:00 | **Blackfire** — burn + 20 AH, E more often |
| ~10:00 | **Spellslinger** — 18 flat + 8% |
| ~15:00 | **Cryptbloom** — 30% pen on laser, shock, Q, DH |
| ~19:00 | **Horizon Focus** — laser marks, Blastquake +10%; **first OPEN** |
| ~23:00 | **Bloodletter** — 30% shred stacks with Crypt |
| ~28:00 | **Deathcap** — 130 AP + 30% |

Do **not** copy the Morgana Rylai-second path (−15.6%). Viktor has no 5s W pool; Rylai is only +12% Blastquake land. Diamond+ Luden → Orb → Cap is **−19.5%** on this farm metric because Echo is not counted.

Luden-first with the same Crypt/HF/Bloodletter/Cap core is still **−8.8%**: Blackfire’s 20 AH + burn opens more E in the window.

## Play

Evolve **E first** (hex fragments ~6:00). Lane: E the wave, E the mid when chipped, laser → shock → Q AA → Harvest. Fights: E → Q → DH; takedown resets CD to 1s. Do not buy two Lost Chapter items.
