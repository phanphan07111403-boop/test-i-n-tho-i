# Zyra Support — Wild Rift Burn Harass Simulation

Patch **7.2+** item model. Plant-spam support playstyle over a **20-minute** average game.

## Run

```bash
python3 simulate_zyra_burn.py
```

Outputs:
- `report.txt` — full minute-by-minute optimal + verdict
- `results.json` — machine-readable snapshots per build

## Question answered

Which build **peaks burn damage** for Zyra plant spam harass, while still giving the burn **enough duration/uptime** to finish its 3s ticks?

## Winner (sim)

**Liandry → Boots → Rylai → Blackfire**

| When | Spike |
|------|--------|
| ~5:00 | Fated Ashes (first burn) |
| ~9:00 | **Liandry** — main harass peak (2% max HP/s) |
| ~13–14:00 | **Rylai** — locks ~94% burn uptime |
| ~16–18:00 | **Blackfire** — double burn if game lasts |

## Why

- Plants auto-attack for 6s and refresh burns — spam trees, accuracy does not matter.
- Liandry is the real burn (max HP). Blackfire is the second DoT + Ability Haste.
- Without Rylai, enemies walk out before the 3s burn completes (~20% less real damage).
- In a 20-min support gold curve, buying Liandry → Blackfire → Rylai often **never finishes Rylai**.
