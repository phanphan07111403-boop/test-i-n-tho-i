# Morgana mid — farm Arcane Comet from minute 1 to 30

Wild Rift **7.2e**. Mid. W-max. **No inventory lock**: Blackfire / Luden / Liandry / **Rylai** first are all in the search.

Patch **7.2** cut Comet to **5% AP** and **+2 per landing stack**. Ability Haste does **not** reduce the 16→8s cooldown. The 0.8s delay is what misses unless the target is Q-rooted or Rylai-slowed. W ticks still *trigger* Comet when Q misses.

## Run

```bash
python3 simulate_morgana_comet.py
```

Outputs:
- `report.txt` — search winner, top 12, contrasts, stack timeline
- `results.json` — machine-readable ranking + winner timeline

## Question

What **full 6-slot build** (Spellslinger + 5 legendaries) farms Comet stacks from laning through late game **and** maximizes Comet damage?

Search: 17k five-legendary completions after BF / Luden / Liandry / Rylai first. Crypt XOR Void. Metric = Σ comet60 minutes 1–30 (75% poke from 90% HP + 25% execute ≤35% for Orb). Echo / Squall / R are not Comet.

## Winner (sim)

**Rylai → Spellslinger → Void Staff → Infinity Orb → Horizon Focus → Deathcap**

| When | Spike |
|------|--------|
| ~8:00 | **Rylai** — land 70% → 91%; first stack farm |
| ~10:00 | **Spellslinger** — 18 flat + 8% (T3 opens 10:00) |
| ~15:00 | **Void Staff** — 40% pen on every comet |
| ~19:00 | **Infinity Orb** — 15 flat; 20% only on the ≤35% slice |
| ~23:00 | **Horizon Focus** — Q marks, comet lands 0.8s later +10% |
| ~28:00 | **Deathcap** — 5% of 30% AP is a tiny last slot |

Top 12 paths **all** buy Rylai first. 5th slot Cap / BF / Luden sits inside ~1%. Void 3rd vs Orb 3rd is **−0.2%**. Mid does **not** buy a support item.

The gold-agnostic Luden max-DPM core (Luden → HF → BF → Crypt, no Rylai) is **−38%** on this metric. The Dark Harvest farm winner (BF → Rylai → Crypt → Orb → HF) is **−17%**.

## Why Rylai-first farms Comet and Void hits it

- 100 AP = **+5** raw Comet. One landing stack = **+2** for the rest of the game. Hits beat AP.
- Comet CD does not take Ability Haste. Cosmic / Crimson / spam-Q do not add procs. The cap is `60 / CD`.
- The real gate is the **0.8s delay**. Q root is ~96%. Rylai at 8:00 is 23/30 high-accuracy minutes and **61 stacks** vs 49 with no Rylai.
- W / burn still trigger Comet when Q misses. After Rylai, drop W on their feet and farm without aiming Q.
- Void 40% pen multiplies base + stacks. Crypt’s 20 AH does nothing for Comet CD (**−13%** vs Void on a Rylai-first path).
- Delay Rylai until after Crypt+HF: **−27.5%**. Blackfire first then Rylai: **−13%**.

## Play

Lane: W the wave so mid walks in the pool — Comet fires even if Q misses. Q when they step up; 2s root covers the 0.8s delay. After Rylai, W under them and stack. Do not buy two Lost Chapter items. Do not delay Rylai to rush Cap / Luden / HF.

## Late rune page

Lock this core. Loadout = **1 keystone + 3 primary + 1 secondary** (7.2e). Metric = Σ minutes 20–30 of Q+W + keystone (50% poke at 90% HP, 50% fight at 32% HP).

```bash
python3 simulate_morgana_comet_runes.py
```

**Page:** Arcane Comet · Manaflow Band · **Transcendence** · **Gathering Storm** · **Coup de Grace**

| Slot | Pick | Why late |
|------|------|----------|
| Keystone | **Comet** | Stacks from 8:00; Aery −1%, DH+Coup −8%, Electro −11%, First Strike −15% |
| Sorcery 1 | Manaflow Band | Mana to keep W on the wave |
| Sorcery 2 | **Transcendence** | 10 AH on Q/W in both HP windows. Absolute Focus’s 30 AP turns off below 65% (the 32% fight) |
| Sorcery 3 | **Gathering Storm** | 70 AP @24, 88 @27, 108 @30, Deathcap ×1.30. Scorch is −12% |
| Secondary | **Coup de Grace** | 8% below 40% + Orb. Cut Down if you only siege at 90% (−2%) |

AH still does **not** reduce Comet CD. Transcendence is for Q/W cadence on the finished core, not extra Comet procs.

