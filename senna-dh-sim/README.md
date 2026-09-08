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

## Combo: **AA → Q** (better than Q → AA)

Living Extraction marks on hit 1, consumes on hit 2 for Mist + **% current HP**.

| Order | Why |
|-------|-----|
| **AA → Q** | Mark with AA, consume with Q while HP is still high → more extraction. Q also carries on-hits (Relic Cannon / Muramana Shock). Then keep AA'ing for Q CD refund. |
| Q → AA | Fine for max-range poke/heal only. Q drops HP first → weaker % current HP consume. |

Aggressive DH pattern: **AA → Q → AA…**, finish under 50% for the soul, then look for the next target (1s reset).

## DH build vs IE + Muramana

```bash
python3 compare_dh_vs_ie_mura.py
```

| | **DH (Drak/Collector/Magnetic)** | **IE + Muramana** |
|--|--|--|
| Keystone | Dark Harvest | Fleet/Grasp (no DH) |
| Overall dmg @20 | **Wins** (~+50% if you keep fighting) | Behind unless snowball fails |
| 8s teamfight | **Wins** (burst + DH resets) | Closer late, still usually behind |
| 12s slugfest | Still ahead, **gap shrinks** | Crit + Shock catch up |
| Best when | Dive, short fights, snowball | Long TF, safe range DPS |

See `compare_dh_vs_ie_report.txt` for the full minute table.
