# Enchanter Senna — Wild Rift 7.3 Buff Gold Efficiency

Patch **7.3** enchanter rewrite. Q-max support Senna over a **20-minute** average game.

## Run

```bash
python3 simulate_senna_buff.py
```

Outputs:
- `report.txt` — minute-by-minute optimal, all 24 orderings, first-item gold-efficiency
- `results.json` — machine-readable snapshots per build

## Question answered

Helia, Whispering Circlet (→ Diadem of Songs), Ardent Censer, and Harmonic Echo all cost ~2400–2500. Which **purchase order** turns the same support gold into the most ally buff and fight impact on **enchanter Senna**?

Senna is not Sona: Piercing Darkness **damages and heals on the same cast**, applies on-hit, and refunds 1s of Q CD per auto. Helia stores that damage and dumps on the Q heal immediately. Senna also autos (Mist AD, no AD/level), so Ardent buffs **her and** the ADC.

## Winner (sim)

**Ardent → Helia → Harmonic → Whisper**

First-item gold efficiency at 8:00:

| First item | Impact @ 8:00 | g/eff |
|------------|---------------|-------|
| **Ardent** | 3688 | **1008** |
| Helia | 2386 | 652 |
| Harmonic | 2315 | 633 |
| Whisper | 2091 | 571 |

Ardent first is about **1.5×** Helia first at the first-legendary spike (closer than on Sona, where it was ~2×, because Senna's Q is a real Helia convert). It still wins.

| When | Spike |
|------|--------|
| ~8:00 | **Ardent Censer** — 30% AS + 25 on-hit on the ADC **and** Senna |
| ~14:00 | **Echoes of Helia** — 20 AH + Q store-and-dump |
| ~18:00 | **Harmonic Echo** — chain 30% heal / 35% shield in 5v5s |
| 20:00+ | Whispering Circlet → Diadem (4th item, often unfinished) |

## Why

- Ardent is a self-buff on Senna. She autos, Q applies on-hit, and extra AS refunds Q CD even with her 0.4 AS ratio.
- Helia second is the convert: autos fill shards, Q damages then heals, dump lands in one cast. 20 AH is the haste Ardent does not have.
- Senna is **less mana-hungry** than Sona (15s Q + auto refunds). Do not Tear-rush before the first legendary.
- Helia and Harmonic **share Bandleglass + Kindlegem**. Buying both before Ardent means no fight buff for dragon.

## Traps

- **Helia → Harmonic** — same recipe, Ardent ~18:00. **+52% worse** at 12:00 than Ardent-first.
- **Harmonic first** — chain has no second target in 2v2; Helia is the better Kindlegem item on Senna.
- **Tear rush into item 1** — delays Ardent 8:00 → 9:00. Senna does not need Tear the way Sona does.
- AP carry? Same slot, **Staff of Flowing Waters** instead of Ardent.
