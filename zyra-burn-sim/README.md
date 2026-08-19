# Zyra Support — Wild Rift Burn Harass Simulation

Patch **7.2+** item model. Plant-spam support playstyle over a **20-minute** average game.

## Run

```bash
python3 simulate_zyra_burn.py
```

Outputs `report.txt` and `results.json`.

## Winner

**Liandry → Boots → Rylai → (Blackfire if game goes long)**

| Time | Spike |
|------|--------|
| ~5:00 | Fated Ashes — first burn |
| ~9:00 | **Liandry** — peak harass (2% max HP/s, plants refresh) |
| ~16:00 | **Rylai** — locks ~94% burn uptime so 3s ticks finish |
| 18–20+ | Blackfire — double burn only if game lasts |

## Why this beats “double burn rush”

In a 20-min support gold curve you usually **cannot** finish Liandry + Blackfire + Rylai.  
`Liandry → Blackfire` peaks higher on paper (~34 burn DPS) but never finishes Rylai → enemies walk out of plant range.  
`Liandry → Rylai` peaks slightly lower on paper but the burn **actually completes**.

## Playstyle

Spam Q/E plants. Accuracy does not matter — plants auto-hit for 6s, W resets duration, burns stay refreshed.
