# Braum Support — No Yordle Trap

Wild Rift patch **7.2+**. Bodyguard support over a **20-minute** average game.

Skip **Yordle Trap**. Catcher needs a displacement; Braum only knocks up with **R**.

## Run

```bash
python3 simulate_braum_support.py
```

Outputs:
- `report.txt` — minute-by-minute peel + verdict
- `results.json` — snapshots per build

## Question answered

Yordle Trap looks like a tank-support item (Kindlegem + Chain Vest, 100g cheaper than Knight's Vow). Should Braum buy it? If not, which peel path actually saves the ADC every fight?

## Winner (sim)

**Locket → Boots → Knight's Vow → Frozen Heart**

| When | Spike |
|------|--------|
| ~5:00 | Bulwark of the Mountain |
| ~9:00 | **Locket** — team shield, no R required |
| ~16:00 | **Knight's Vow** — 12% redirect while you W-glue |
| 20:00 | Frozen Heart usually **not finished** on support gold |

At 12:00 vs a Yordle Trap rush, this path is **~99% more peel**. At 16:00 (two legendaries) it is **~70% more peel**. Catcher's extra gold is ~40/min personal, split, and only if R hits and the mark dies in 5s.

## Why no Yordle Trap

- Catcher procs on **airborne / kinematics**. Braum Q is a slow, W is a dash to an ally, E is a projectile block, passive is a stun. **Only R** displaces.
- R CD is 75/70/65s. Mark lasts 5s. Gold needs a kill. 10s ICD.
- Same components as **Knight's Vow**. Finishing Yordle trades a 12% redirect that works every fight for an R-gated mark.
- 20-min support gold finishes **two** legendaries, not three. "Yordle 3rd" is leftover Kindlegem + Vest, not Catcher.
- If you want an R item, that item is **Radiant Virtue** (heal on ult), not Yordle Trap.

## Playstyle

- Skill: max **Q**, one early **W** for the dash, then **E**.
- Bodyguard: W onto the ADC → E into the projectile → Q to start Concussive Blows.
- R is a knock-up / zone, not an item proc.
- Plated Steelcaps vs AD autos; Mercury's Treads vs AP/CC.
