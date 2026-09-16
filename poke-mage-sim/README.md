# Poke mages — highest range × shortest cooldown

PC League of Legends, patch **~26.18**. Same AP / ability haste for every kit. **12-second** siege window.

## Run

```bash
python3 simulate_poke_mages.py
```

Outputs:
- `report.txt` — range/cycle ranking, expected damage, verdict
- `results.json` — snapshots per kit

## Question answered

Who is the **best poke mage** if you want **highest range** and a **short cooldown** (the spear-only Nidalee fantasy)?

## Winner (sim)

**AP Kog'Maw — Living Artillery (R)**

1800 range, **1s** rank-3 cooldown (0.86s with ~65 haste). Mana is the limiter, not the cooldown: 9 shots in 12s before the 40/80/120… tax stops you.

At 22:00, range-frequency (range ÷ cycle) vs the other artillery kits:

| Kit | Range | Cycle @22 | Shots / 12s | Range/sec |
|-----|------:|----------:|------------:|----------:|
| **Kog'Maw R** | **1800** | **0.86s** | **9** | **2103** |
| Ziggs Q | 1400 | 2.67s | 5 | 524 |
| Hwei QW | 1900 | 4.14s | 3 | 459 |
| Nidalee Q | 1500 | 3.89s | 4 | 386 |
| Xerath Q max-charge | 1450 | 4.78s | 3 | 303 |

## If you wanted spear-only Nidalee, lock

1. **AP Kog'Maw** — the actual “spam a long-range skillshot” champion. Fog R. Malignance rush is in `ap-kogmaw-sim/`.
2. **Ziggs** — best **basic-ability** Q spam. 1400 bounce, 4s CD, waveclear, turrets. Easier than Xerath.
3. **Xerath** — artillery identity (1450 Q + 5000 R). Range is real; short cooldown is not: 1.75s charge makes a max Q a ~4.8s cycle.
4. **Hwei QW** — longest basic spell (1900). 1s delay + 6s CD. Poke, not spam.

Do not lock Nidalee for this job. 1500 range looks close; Hunt wants cougar, and ~32% of max spears hit.

Karthus Q wins raw ticks (1s CD, 875 range) and Ezreal Q wins refund-spam (1200). Neither is a long-range poke mage.
