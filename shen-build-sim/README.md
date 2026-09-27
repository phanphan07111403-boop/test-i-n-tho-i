# Shen Baron — farm, then 1v1, then tank

Patch **7.3**. Heartsteel first is out: no wave tool, the game stalls.

Constraint: **1st farms**, **2nd 1v1s**, **rest tanks for 1v9**.

## Run

```bash
python3 shen-build-sim/simulate_shen_build.py
```

## Winner

**Titanic Hydra → Dusk and Dawn → Dawnshroud → Amaranth's Twinguard**

| Slot | Item | Job |
|------|------|-----|
| Start | Ruby Crystal | |
| First back | **Bami's Cinder** | Farm starts now, before the legendary |
| **1st** | **Titanic Hydra** (3000) | Q + cleave deletes the wave. Cannon wave ~86% in 4s in the sim. |
| Boots | Plated Steelcaps | Mercury's vs AP/CC |
| **2nd** | **Dusk and Dawn** (3100) | Extra on-hit on Q’s 3 autos. This is the 1v1. |
| **3rd** | **Dawnshroud** | Taunt proc, armor/MR |
| **4th / 5th** | Twinguard, Thornmail, Force of Nature | 1v9 tank |
| Enchant | Stoneplate | |

Do **not** buy Heartsteel. Do **not** rush Dusk first (49% wave vs Titanic’s 86%).

## Why this split

Heartsteel is 700 HP and a delayed proc. It does not hit the wave. In the sim a first-item Heartsteel clears **35%** of a cannon wave in 4s. Titanic clears **86%**. That is the “game too slow” feeling.

Dusk stays **2nd**, not 1st: same Q sheen 1v1 as before, after you already shove.

3rd+ is tank. You already spent two items on farm and the duel; the rest is so you can 1v9 after R.

## Rank (constraint fit)

| Path | Farm 8:00 | 1v1 mix 16:00 | Tank ehp 22:00 |
|------|-----------|---------------|----------------|
| **Titanic → Dusk → tank** | **86%** | **1458** | 4929 |
| Sunfire → Titanic → tank | 78% | 1342 | 4929 |
| Sunfire → Dusk → tank | 78% | 1365 | 4801 |
| Hollow → Dusk → tank | 79% | 1372 | 4617 |
| Heart → Sunfire → Dawn | 35% | 1262 | 5250 (skipped) |
| Dusk first | 49% | 1674 | 4662 (skipped) |

## Swaps

- **AP lane:** Hollow Radiance 1st, Force of Nature later.
- **Safer/cheaper farm:** Sunfire 1st (still Bami’s), Dusk 2nd, same tank rest.
- They heal: Thornmail in the tank slots.
- Crit AD: Randuin instead of Twinguard.

## Runes

Grasp, Courage of the Colossus, Second Wind, Overgrowth, Sudden Impact, Legend: Tenacity. Flash + Ignite (Teleport if you live on R). Max **Q > E > W**.
