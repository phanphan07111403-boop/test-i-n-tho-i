# Sona Support — Wild Rift 7.3 Buff Gold Efficiency

Patch **7.3** enchanter rewrite. Q-max Sona over a **20-minute** average game.

## Run

```bash
python3 simulate_sona_buff.py
```

Outputs:
- `report.txt` — minute-by-minute optimal, all 24 orderings, first-item gold-efficiency
- `results.json` — machine-readable snapshots per build

## Question answered

Helia, Whispering Circlet (→ Diadem of Songs), Ardent Censer, and Harmonic Echo all cost ~2400–2500. Which **purchase order** turns the same support gold into the most ally buff and fight impact?

## Winner (sim)

**Ardent → Helia → Harmonic → Whisper**

First-item gold efficiency at 8:00 (impact per 1k gold):

| First item | Impact @ 8:00 | g/eff |
|------------|---------------|-------|
| **Ardent** | 1663 | **465** |
| Helia | 1067 | 298 |
| Harmonic | 940 | 263 |
| Whisper | 808 | 226 |

Ardent first is about **2×** Whisper first at the first-legendary spike.

| When | Spike |
|------|--------|
| ~8:00 | **Ardent Censer** — 30% AS + 25 on-hit on the ADC |
| ~14:00 | **Echoes of Helia** — 20 AH + poke converted into extra W heal |
| ~18:00 | **Harmonic Echo** — chain 30% heal / 35% shield in 5v5s |
| 20:00+ | Whispering Circlet → Diadem (4th item, often unfinished) |

## Why

- Patch 7.3 buffed marksmen (200% crit, new ADC items) and rewrote Ardent to a **flat** 30% AS / 25 on-hit at **2400g**. That is the highest gold→game-impact conversion on Sona.
- Helia second buys the haste Ardent does not have, so W keeps the AS buff up, and Q poke becomes a second heal.
- 20-min support gold finishes **three** legendaries. Harmonic as third is live in 5v5s; Circlet as fourth often never completes.
- Helia and Harmonic **share Bandleglass Mirror + Kindlegem**. Buying both before Ardent means the ADC has no fight buff for dragon.

## Traps

- **Helia → Harmonic** — same recipe, no ADC buff, Ardent lands ~18:00. +67% worse at 12:00 than Ardent-first.
- **Harmonic first** — chain has no second target in 2v2.
- **Tear rush into Ardent** — extra 400g delays the 8:00 spike to 9:00. Only rush Tear when Circlet is item 1 or 2.
- AP carry? Same slot, **Staff of Flowing Waters** instead of Ardent.
