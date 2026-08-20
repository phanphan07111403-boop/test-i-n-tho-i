# Senna — Aggressive Dark Harvest Peak Simulation

Wild Rift **Patch 7.2+**. Aggressive ADC / flex carry (**not** poke support).

## Run

```bash
python3 simulate_senna_dh.py
```

Outputs:
- `report.txt` — minute-by-minute optimal + verdict
- `results.json` — machine-readable snapshots per build

## Question answered

Which build **peaks execute damage** for aggressive Senna while **farming the most Dark Harvest souls** over a 20-minute game?

## Playstyle

- Dive / skirmish constantly — force enemies below **50% HP**
- Takedown resets Dark Harvest to **1s CD** → soul printer
- Mist stacks from fights feed AD → stronger DH (10% bonus AD)

## Winner (sim)

**Draktharr → Collector → Magnetic** (aggressive ADC / flex)

| When | Spike |
|------|--------|
| ~8:00 | **Duskblade** — Nightstalker dive + takedown reset |
| ~13:00 | **Collector** — execute floor → more resets |
| ~18:00 | **Magnetic Blaster** — range to keep farming DH |

**~128 Dark Harvest souls by 20:00** in the aggressive fight model.

## Why

- Not support poke Senna — you dive and force sub-50% HP constantly.
- Draktharr + Collector is the **reset engine** that maxes DH stacks.
- Magnetic keeps you alive long enough to chain the next proc.
- Pure crit IE path peaks paper DPS later but farms fewer early souls.
