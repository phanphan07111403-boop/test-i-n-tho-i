# Tryndamere Jungle — Farm, then Split

Wild Rift patch **7.3 / 7.3b** (still the live kit on **7.3f**). Full-clear the jungle, catch a side wave, press Undying Rage on whoever answers, take the turret.

## Run

```bash
python3 simulate_tryndamere_jungle.py
```

Outputs:
- `report.txt` — minute-by-minute split score + verdict
- `results.json` — snapshots per build

## Question answered

On a powerfarm gold curve (camps and side waves, not gank gold), which build **wins the 1v1 during the 5 second ultimate** and still **cracks the tower**?

Score, scaled so the weights are real at 18:00:

- **50%** duel (bruiser 45% / tank 35% / squishy 20%)
- **35%** turret damage on the crash
- **15%** how fast the side wave dies

## Winner (sim)

**Yun Tal Wildarrows → Berserker's Greaves → Hullbreaker → Infinity Edge → Navori Quickblades → Lord Dominik's Regards**

| When | Spike |
|------|--------|
| ~6:00 | **Yun Tal** — the farm item. 0.4% crit per auto, cap 25%. A jungler who only farms caps it |
| ~8:00 | Berserker's Greaves |
| ~14:00 | **Hullbreaker** — the split spike. Skipper is 240% base AD + 9% max HP into the turret |
| ~19:00 | **Infinity Edge** — crits go from 200% to 230% |
| ~22:00 | **Navori** — autos refund the spin (3 spins inside the ultimate) |
| ~26:00 | **Lord Dominik's** — the tank they send after the fighter loses |

At **22:00** this path is on 100% crit with Hull and IE: about **96%** of the answering fighter's effective HP and **6515** turret damage on the crash. The sheet crit path (Navori → IE → BotRK → Mortal, no Hull until never in this order) is **4612** on the same turret.

Late-weighted score **3153** vs **3105** for Yun Tal → IE → Navori → Hull → BotRK. That runner-up is the same four items at 22:00 and a better last slot when the answer is a fighter (**BotRK**) rather than a tank (**Lord Dominik's**). Hull second wins the average game because the turret item is online at 14:00, not 22:00.

## Why

- Patch **7.3b** makes every point of Fury worth **0.5% crit** from level 1. Undying Rage fills the bar, so the all-in starts at 50% crit before items. Crit past 100% becomes 1 AD per 1%.
- Base crits are **200%**. Infinity Edge makes them **230%**. Tryndamere was buffed in 7.3b specifically because he was not getting enough from that crit overhaul.
- Spinning Slash crit-refunds on **monsters** (7.3), which is the clear. On champions the refund is 2 seconds, and Navori cuts another 15% of the remaining cooldown per auto.
- Max **Q**, not E. The refund already dumps the spin's cooldown. Rank-4 Bloodlust is **+0.9 AD per 1% missing HP** (+81 AD at the ultimate threshold). That AD crits and scales the spin.
- Hullbreaker does not help the 1v1 the way BotRK does. It is how a melee champion takes a 7.3 turret (melee bonus is +20% into structures). BotRK does not hit towers.
- Kraken → Guinsoo → BotRK wins the bare 1v1 and still loses the split. The turret gap is larger than the duel gap, and the wave crashes slower.
- Trinity → Hull lives and hits the tower, then does nothing to the tank (about half their HP in the same window).

## Playstyle

- Full clear to level 5. First back finishes Yun Tal's components. Do not gank for a Long Sword.
- Ghost + Smite. Lethal Tempo, Last Stand, Legend: Alacrity. **Demolish** instead of Nimbus — Ghost still gets you to the wave, Demolish takes the plate (85 + 28% max HP after 3 autos).
- After Yun Tal, catch the side wave on the half of the map your team is not fighting. Crash it, ultimate the one person who matches, auto the turret, leave when the second person shows.
- Press R before the crowd control, not at 1 HP. Q when R ends. Spending Fury during the ultimate drops the crit you are hitting with.
- Last item: Lord Dominik's into a tank, Mortal Reminder if they heal, BotRK if the answer is a health stacker and you already own Hull.
