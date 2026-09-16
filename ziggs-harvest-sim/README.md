# Ziggs Q-spam — Dark Harvest vs Comet

PC League of Legends, patch **~26.18**. Mid gold curve. Max-range **Bouncing Bomb** on cooldown over a **12-second** window.

## Run

```bash
python3 simulate_ziggs_harvest.py
```

Outputs:
- `report.txt` — mix damage, harvest proc rates, Comet vs DH A/B, verdict
- `results.json` — snapshots per page

## Question answered

Is **Dark Harvest** worth it on Q-spam Ziggs, or do you run **Arcane Comet**?

## Winner (sim)

**Arcane Comet.** Harvest is only close if you are already snowballing and getting takedown resets.

Same Luden → Shadowflame → Deathcap path at 22:00 (squish mix: 45% full HP / 35% chunked / 20% execute):

| Page | Mix / 12s | Full HP | Execute |
|------|----------:|--------:|--------:|
| **Comet** | **864** | **835** | 980 |
| DH (avg souls) | 805 (−7%) | 740 (−11%) | 985 |
| DH snowball + reset | 861 (~even) | — | 1210 |

Full-HP poke never harvests (0% proc). That's most of Q-spam. Comet doesn't care about HP, and a long bounce also ramps the V26.09 travel amp — one comet is often bigger than Harvest at 8 souls, and it repeats.

## How to play it

1. **Runes:** Arcane Comet, Manaflow Band, Transcendence, Scorch. Precision: Presence of Mind + Cut Down / Coup de Grace.
2. **Items:** Luden's Echo → Sorcs → Shadowflame → Deathcap. Liandry / Horizon / Void when they stack HP.
3. **Max Q.** Bounce from 1400. Short Fuse is proc damage — it does **not** harvest, and you shouldn't walk up for it.
4. **Dark Harvest** only into 4+ squishies when you will get takedown resets. Then the bomb that matters is the one that lands **below 50%**, not the one that starts the poke.
