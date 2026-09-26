# Shen Baron — same 1v1 logic as Volibear

Patch **7.3**. Isolated 8s 1v1 vs a bruiser. GameSir X3 Pro: E taunt is a dash button, Q is a pull-to-self, W is self-cast. **R still needs a thumb on the ally portrait.**

## Run

```bash
python3 shen-build-sim/simulate_shen_build.py
```

## Does Dusk and Dawn work on Shen?

**Not as a Volibear rush.** Dusk first loses the 8:00 window to Heartsteel (350 HP vs 700). Shen’s Ki Barrier, Shadow Dash, and Titanic all scale **bonus HP**. Q only gets +1.5–2% max HP per 100 AP, so 70 AP is a small tick. The AP on Stand United is for the **ally** shield, not your 1v1.

**Yes as 2nd item after Heartsteel.** Dusk’s extra on-hit double-applies on a Q auto, and Q is three empowered hits. That is the same “sheen + extra on-hit” idea as Volibear, just after the HP stack Shen actually needs.

Copying **Dusk → Hull → Rift** onto Shen is the worst path in the sim.

## Winner (1v1 strength)

**Heartsteel → Plated Steelcaps → Dusk and Dawn → Titanic Hydra → Sunfire / Twinguard**

| When | Buy |
|------|-----|
| Start | **Ruby Crystal** |
| ~6:00 | **Heartsteel** |
| Next | **Plated Steelcaps** |
| 2nd | **Dusk and Dawn** — extra on-hit on Q’s 3 autos |
| 3rd | **Titanic Hydra** — cleave on those same hits |
| 4th | Sunfire, Twinguard, or Thornmail |
| Enchant | Stoneplate |

If you **ult and group** more than you 1v1, take the Diamond+ tank core instead: Heartsteel → Sunfire → Dawnshroud (~61% WR). That path is close in the sim and better at being a tank.

## Rank (sim)

| Path | 8:00 | 18:00 | 22:00 |
|------|------|-------|-------|
| **Heart → Dusk → Titanic** | 3625 | 5228 | **6000** |
| Heart → Sunfire → Titanic | 3625 | 5113 | 5905 |
| Heart → Sunfire → Dawn | 3625 | 5113 | 5846 |
| Heart → Iceborn → Sunfire | 3625 | 4947 | 5525 |
| Dusk first (Voli copy) | 3352 | 5247 | 6009 |

Dusk-first matches late damage and still **loses the game sum** because you spend the first two items squishy.

## Runes (this page)

**Grasp of the Undying** — Shen trades in short windows (Q3 + E), not Lethal Tempo run-downs.

| Slot | Take |
|------|------|
| Keystone | Grasp |
| Resolve | Courage of the Colossus (shield on E taunt) |
| Resolve | Second Wind |
| Resolve | Overgrowth |
| Domination | Sudden Impact (true damage after E dash) |
| Precision | Legend: Tenacity |

Flash + Ignite (or Teleport if you live on R). Max **Q > E > W**.

## X3 Pro

- Left stick: walk so the Spirit Blade **passes through them** (empowered Q).
- A Q · B W (self) · X E (dash — aim with stick) · Y is unused in 1v1.
- **R:** tap the ally portrait on glass. Do not try to macro R.
