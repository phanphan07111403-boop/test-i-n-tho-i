# AP Kog'Maw — Spam R (Wild Rift)

Wild Rift patch **7.3**. Living Artillery numbers are from the **7.2c** retune (50→500 mana, 80/120/160 base). Pure artillery: Q for the shred, then R on cooldown. No W, no E.

## Run

```bash
python3 simulate_spam_r.py
```

Outputs:
- `report.txt` — minute-by-minute best path, 12s fight, 40s siege, shot-cost trace
- `results.json` — snapshots per build

## Question answered

Which build lets you spam R after the mana cost climbs 50 → 500, and still kills a tank who stands in the shells?

## Winner (sim)

**Malignance → Spellslinger's Shoes → Liandry's Torment**

Avg score from 6:00–20:00: **173.3**. Next is the same start with Horizon instead of Liandry (**171.9**). At 16:00, half mana, Liandry puts a ~2892 HP / 117 MR tank's whole bar in a 12s fight.

| When | Spike |
|------|--------|
| ~6:00 | **Malignance** — 500 mana, 20 ultimate haste, Hatefog |
| ~11:00 | **Spellslinger's Shoes** — 18 flat pen + 8% pen (only after 10:00) |
| ~16:00 | **Liandry** — 2% max HP/s, refreshed by R |

Horizon second is the path that finishes **Void Staff at 20:00**, and that single minute is the highest score in the timeline (237.7 vs 228.7). Liandry still leads the 6:00–20:00 average. Buy Horizon second when you expect the game to last long enough to complete Void.

## How to press R

Shell costs are 50, 100, 150, 200, then 250 and up to 500. Damage per mana falls off immediately.

On the 16:00 tank, **stop at 150** and let the 8s stack timer fall off. That kills at **11.1s**. Stopping at 200 still kills, at 11.8s. Paying 250 or more on a half bar refreshes the timer and the tank lives.

The kill is the second volley, once the shells are cheap again.

## Why the other shapes lose

- **Seraph** refunds 25% and holds the bigger pool. At 16:00 that is 10 shells on a full bar and still only 80% of the tank on the half bar this pattern actually plays on.
- **Luden** procs echo once or twice (175+14% AP). Mana spent on R is gone.
- **Crimson Lucidity** is 25 ability haste. Malignance's ultimate haste already puts rank-2 R under a second, so mana is the limiter.
- **Infinity Orb** adds 20% below 40% HP, the same line where R already doubles. The bonus waits for the execute.
- **Rod of Ages** is a mana stat stick with no refund. It delays Malignance.

The target stands in the shells. No heal, no shield, no sidestep. Real games deal less. The order above is the part that still holds.

Max **Q**. W is the on-hit build. This is a different question from `ap-kogmaw-sim/`, which is PC League and mixes fog R with max-range W.
