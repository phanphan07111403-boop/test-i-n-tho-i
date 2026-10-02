# AP Kog'Maw — Spam R

PC League of Legends, patch **26.19** (Living Artillery last changed in **26.16**). Pure artillery: Q for the shred, then Living Artillery on cooldown. No W, no E.

## Run

```bash
python3 simulate_spam_r.py
```

Outputs:
- `report.txt` — minute-by-minute best path, 12s barrage, shot-cost trace
- `results.json` — snapshots per build

## Question answered

Which build lets you spam R when the mana cost climbs 40 → 400, and still hurts a tank who stands in the shells?

## Winner (sim)

**Malignance → Sorcerer's Shoes → Horizon Focus → Void Staff → Rabadon's Deathcap**

At 22:00, starting on half mana (you were already poking), this path puts **3663** of a ~3850 HP / 186 MR tank's health bar in a 12s barrage (8 shells). Liandry second does **3186**. Tear into Seraph has the bigger pool (2815 mana, 11 shells on a full bar) and still only **2265** on the half bar, because those extra shells arrive without Void.

| When | Spike |
|------|--------|
| ~7:00 | **Malignance** — ultimate haste, 600 mana, Hatefog |
| ~10:00 | Sorcerer's Shoes (12 magic pen) |
| ~15:00 | **Horizon Focus** — 10% damage on the long-range hit, 25 AH |
| ~21:00 | **Void Staff** — the tank shell |
| ~27:00 | Rabadon's Deathcap |

## How to press R

Shell costs are 40, 80, 120, 160, then 200 and up to 400. Damage per mana falls off immediately.

On a standing tank at 22:00, **4 shells then reset** (stop when the next one would cost more than 160) kills at **11.7s** and leaves mana. Holding the button until the shell costs 400 kills at **12.3s** and leaves you empty.

Half a bar does this by itself: the chain dies, the 8s stack timer falls off, and the next shells are cheap again. That second volley is the spam.

Max **Q**, not W. Same target for the whole chain so Hatefog stays under them.

## Why not the other shapes

- **Liandry second** loses the half-mana tank fight. 2% max HP/s needs a long fight. This pattern is a chain of shells, and Horizon's extra shell plus 10% amp wins it. Buy Liandry when the tank is healing and the fight drags.
- **Tear → Seraph** is the mana pool. It is the wrong second and third item: you are late to Void, and the 9th–11th shell is the expensive one.
- **Luden → Malignance** is the close second. Echo procs once. The second Lost Chapter item delays Void.
- **Actualizer** doubles ability costs for 8 seconds. R's cost is already climbing.
- **Ionian Boots** are 10 ability haste. Sorcs' 12 pen is the boot.

The target in the sim stands still. No heal, no shield, no sidestep. Real games deal less. The order above is the part that still holds.

This is a different question from `ap-kogmaw-sim/`, which mixes fog R with max-range W and maxes W.
