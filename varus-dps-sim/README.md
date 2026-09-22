# Varus on-hit vs crit — Wild Rift 7.3

Uses the local `wr-7.3-db/` snapshot. No live web fetch.

## Run

```bash
python3 varus-dps-sim/simulate_varus.py
```

Outputs:
- `report.txt` — minute table, item spikes, late-game TTK, verdict
- `results.json` — full snapshots per path

## Question

On-hit or crit Varus, with the goal of **late-game scale** and **DPS still rising after each purchase**.

## Builds compared

On-hit (W max):
- BotRK → Berserkers → Rageblade → Terminus → Kraken → Bloodthirster
- Kraken → Rageblade → Terminus → BotRK → BT
- Statikk Shiv → Rageblade → Terminus → BotRK → BT

Crit (Q max):
- Yun Tal → Berserkers → Infinity Edge → Rapid Firecannon → LDR → BT
- Yun Tal → IE → Phantom Dancer → LDR → BT
- Stormrazor → IE → RFC → LDR → BT
- Yun Tal → Hexoptics C44 → IE → LDR → BT

## Model

- 24-minute dragon-lane farm gold curve, Wild Rift level cap 15
- 8s all-in vs a squishy and a tank
- Lethal Tempo (7.3 rewrite) + Alacrity + Cut Down (tanks) + Coup de Grace
- On-hit: auto to 3 Blight → E detonate → auto → short Q
- Crit: auto, charged Q (~1.2s) on 3 Blight
- Yun Tal stacked crit: 0.2% per farm auto, cap 25% (~125 autos)

See `report.txt` for the current numbers.
