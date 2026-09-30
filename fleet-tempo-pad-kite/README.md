# Fleet vs Tempo — kiting on a pad

Wild Rift **7.3**. GameSir X3 Pro: left stick held away, RT taps attack, Force Attack Follow off. Kai'Sa (analog kite) and Ashe (slow kite).

## Run

```bash
python3 simulate_fleet_tempo_kite.py
```

Outputs: `report.txt`, `results.json`.

## Answer

**Take Lethal Tempo** on the pad, unless Kai'Sa Supercharge is what keeps the fight going.

7.3 Tempo is +6.4% attack speed per stack, six stacks, then a bolt. No bonus range. On these builds the 6-stack auto is still **0.54–0.97s**. A normal shoulder tap (every 0.36s) can spend all of it. Tempo is not too fast for the pad anymore.

Tempo does not open space. With a normal wind-up you stand the same fraction of each second, so more attack speed does not move the stick farther. Fleet's 20% move speed for 1s does — after the energize bar fills. A two-second run-down never fills it.

| Situation | Pad result |
|-----------|------------|
| You can already hold max range (Ashe slow + Stormrazor/Runaan, or Kai'Sa vs a slow walker) | **Tempo.** Both kite. Tempo deals more. |
| They run you down and Supercharge is down | **Tempo.** Same collapse, more damage. Fleet has not energized. |
| Supercharge stretches a boots-speed melee | **Fleet.** One proc, about a second longer and a heal. Still get touched. On a mouse that same Tempo fight is a kill; the 50 ms late auto costs it. |
| Ghost-speed melee on Kai'Sa | **Neither.** Dead in ~2.5s (no E) or ~3.7s (E). Heal stays 0. |

Fix a broken map before you swap the rune. If RT freezes the stick (Mapping Enhancement off, joystick not Locked), both keystones get caught faster.

## Assumptions that move the answer

- Wind-up is 18% for Kai'Sa and 22% for Ashe, scaling 1:1 with attack speed. Wild Rift does not publish this. If bonus attack speed shrinks the wind-up slower than the period, Tempo stands more and gets caught sooner.
- The chaser runs straight at you. No dash, no Flash, no your Ghost.
- Kai'Sa E cast time is the wiki value (1.0s → 0.5s). Patch 7.3 reprinted the move-speed formula, not the cast.
- Ashe's slow is modeled as a flat 20% for 2 seconds. The slow is why she holds a ghost at 3 items.
