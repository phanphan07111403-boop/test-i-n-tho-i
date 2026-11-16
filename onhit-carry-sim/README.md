# Kai'Sa and Kalista on the Varus build

Wild Rift patch **7.3f**. Level 15. The Varus six items are Berserker's Greaves, Statikk Shiv, Guinsoo's Rageblade, Runaan's Hurricane, Blade of the Ruined King, and Terminus.

## Run

```bash
python3 simulate_onhit_carries.py
```

Outputs `report.txt` and `results.json`.

## Result

Both champions keep the six items and the same rune page: Lethal Tempo, Brutal, Cut Down, Legend: Bloodline, Bone Plating.

Kai'Sa buys Statikk before Vampiric Scepter. The first completed item evolves Icathian Rain, and Statikk clears a wave in 2.59 seconds where Kraken Slayer takes 5.95. Kraken is the isolated-target swap, not the farm build. Replacing Hurricane with Nashor's Tooth drops the grouped fight.

Kalista finishes Blade of the Ruined King first and buys Statikk last. Rend already resets on a minion kill, so the lifesteal item is the lane spike and the lightning is the extra spear once Guinsoo, Hurricane, and Terminus are done.
