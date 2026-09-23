# Enchanter Senna — Wild Rift 7.3 Buff Gold Efficiency

Patch **7.3** enchanter rewrite. Q-max support Senna over a **20-minute** average game, with a **24-minute** 4th-item bake-off.

## Run

```bash
python3 simulate_senna_buff.py
```

Outputs:
- `report.txt` — minute-by-minute optimal, all 24 orderings, first-item gold-efficiency, 4th vs Whisper
- `results.json` — machine-readable snapshots per build (including `fourth_item_comparison`)

## Question answered

Helia, Whispering Circlet (→ Diadem of Songs), Ardent Censer, and Harmonic Echo all cost ~2400–2500. Which **purchase order** turns the same support gold into the most ally buff and fight impact on **enchanter Senna**?

After locking **Ardent → Helia → Harmonic**, is Whisper the best 4th — or do Mandate / Staff / Salvation / Shurelya / Mikael win if the game lasts long enough to finish one (~22–24 min)?

Senna is not Sona: Piercing Darkness **damages and heals on the same cast**, applies on-hit, and refunds 1s of Q CD per auto. Helia stores that damage and dumps on the Q heal immediately. Senna also autos (Mist AD, no AD/level), so Ardent buffs **her and** the ADC. Q slows and W roots, so Mandate's 7% Command mark applies twice.

## Winner (sim)

**Ardent → Helia → Harmonic → Imperial Mandate**

Among the original four items the leftover 4th is Whisper. Once you open the 4th slot, **Mandate beats Whisper** (+6.6% on the 18–24 window, +12.5% raw impact at 24:00).

First-item gold efficiency at 8:00 (unchanged):

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
| ~23:00 | **Imperial Mandate** — Q slow + W root mark, 7% increased damage |

20-min support gold (~10.2k) finishes **three** legendaries. A 4th needs ~22–23 min (~11.3–11.9k).

## 4th item vs Whisper

Ardent → Helia → Harmonic locked. Same gold curve. Scored on 18:00–24:00 (leftover gold + completion).

| # | 4th | Cost | Online | 22:00 | 24:00 | vs Whisper |
|---|-----|------|--------|-------|-------|------------|
| 1 | **Mandate** | 2600 | 23:00 | 9414 | **10663** | **+6.6%** |
| 2 | Shurelya | 2450 | 22:00 | **10007** | 10184 | +5.1% |
| 3 | Salvation | 2450 | 22:00 | 9926 | 10099 | +5.1% |
| 4 | Staff | 2400 | 22:00 | 9877 | 10048 | +3.9% |
| 5 | Mikael | 2500 | 22:00 | 9601 | 9771 | +2.3% |
| 6 | Whisper | 2400 | 22:00 | 9306 | 9477 | — |

**Every** alternative beats Whisper. Whisper's Harmony HSP is real, but Ardent already brought 8% HSP, Senna is not mana-hungry, and Diadem (700 Tear/Circlet stacks) does **not** finish by 24:00.

- **Mandate** is the 4th: 60 AP, +20 AH on CC, 7% mark from Q **and** W. 2600g so it completes ~1 min later than 2400g 4ths.
- **Shurelya** if you hit 2450g at 22:00 and the game might end — 20 AH always on + 30% MS engage.
- **Salvation** for Baron-pit 5v5s (150–350 heal + 10% max HP true, 2.5s delay).
- **Staff** if the carry is AP (Rapids 40 AP / 15 AH actually lands).
- **Mikael** into removable CC (Leona / Naut / Seraphine).

Do not greed leftover gold into Tear on a 20-min clock — the 4th never finishes.

## Why

- Ardent is a self-buff on Senna. She autos, Q applies on-hit, and extra AS refunds Q CD even with her 0.4 AS ratio.
- Helia second is the convert: autos fill shards, Q damages then heals, dump lands in one cast. 20 AH is the haste Ardent does not have.
- Senna is **less mana-hungry** than Sona (15s Q + auto refunds). Do not Tear-rush before the first legendary.
- Helia and Harmonic **share Bandleglass + Kindlegem**. Buying both before Ardent means no fight buff for dragon.
- Mandate 4th is Senna's CC identity. Whisper 4th is Sona's mana identity.

## Traps

- **Helia → Harmonic** — same recipe, Ardent ~18:00. **+52% worse** at 12:00 than Ardent-first.
- **Harmonic first** — chain has no second target in 2v2; Helia is the better Kindlegem item on Senna.
- **Tear rush into item 1** — delays Ardent 8:00 → 9:00. Senna does not need Tear the way Sona does.
- **Whisper 4th by default** — last among 4ths on this kit. Only if you want Diadem in a 28-min game.
- AP carry first item? Same slot, **Staff of Flowing Waters** instead of Ardent.
