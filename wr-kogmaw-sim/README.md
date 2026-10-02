# Wild Rift Kog'Maw — Runaan's vs Guinsoo's after BoRK

Patch **7.3**. Dragon lane. Rush **Blade of the Ruined King → Berserker's Greaves**, then choose the next item.

## Run

```bash
python3 simulate_wr_kogmaw.py
```

Outputs:
- `report.txt` — minute-by-minute fork, isolated item compare, verdict
- `results.json` — per-minute numbers for both purchase orders

## Question

After BoRK and Berserker's, what changes in a fight and on the map if the next item is **Runaan's Hurricane** or **Guinsoo's Rageblade**?

## Winner depends on the target

Same gold. Runaan costs 2650 and finishes at **12:00**. Guinsoo costs 3000 and finishes at **13:00**. Both items are owned at **17:00**, and from then on the paths are identical.

Raw second item, level 12, BoRK + Greaves + that legendary only:

| Window | Guinsoo | Runaan |
|--------|---------|--------|
| Solo tank time-to-kill | **5.7s** | 7.3s |
| Damage onto that tank in 4s | **2885** | 2482 |
| Squishy time-to-kill | **3.2s** | 4.2s |
| 3 champions in bolt range | 5679, tank dies 5.7s, fight lives | **8463, wipe at 7.8s** |
| Dragon damage in one Barrage | **4495** | 3533 |
| Full wave | 8.6s | **5.0s** |
| Healing in the 3-champion fight | 869 | **1457** |

From 13:00 to 16:00, while each path owns its item and not the other: Runaan takes **25% longer** to kill the solo tank, deals **16% less** dragon damage, removes **42% more** HP when three champions are clumped, and clears waves in **4.3s instead of 8.1s**.

## Why

- Guinsoo stacks to +32% attack speed and every 3rd stacked attack repeats Bio-Arcane Barrage, BoRK, and 30 magic on-hit. That is the tank and dragon item. The 30 AP is a small bump.
- Runaan does not hit the same champion twice. The bolts are 55% AD, can crit, and apply W and BoRK to the two champions beside your target. Alone, they do nothing. In a clump or a wave, they are the item.
- The auto itself is close. Runaan's 25% crit at 200% damage covers most of Guinsoo's extra AD.
- Both builds already kill the tank during one Barrage. Guinsoo does it about a second and a half sooner. Runaan spends that time also killing the people next to him.
- A 3-auto trade never reaches Phantom Hit. Guinsoo still wins it by about 10% from AD and the flat magic on-hit.

## Buy

- **Guinsoo's second** when one body is the job: the frontliner you have to cut, or the dragon. The wave takes most of Barrage.
- **Runaan's second** when they stand together, or you need to shove and move. The wave dies inside one Barrage. The solo tank still dies in that Barrage, later.
- Buy the other one next. Order stops mattering at two completed items.

## First item: BoRK or Guinsoo

Both finish at **6:00** on an even gold curve (BoRK 3100, Guinsoo 3000). They match again at **13:00**, once each path has bought the other item and Berserker's Greaves.

At 6:00, level 7, Barrage maxed:

| | Rush BoRK | Rush Guinsoo |
|--|-----------|----------------|
| Lane all-in | 6.6s | **6.0s** |
| 3-hit trade | **642** | 570 |
| Frontliner | lives | **dies in 8.4s** |
| Healing in that duel | **170** | 0 |

Rush Guinsoo when the fight is long: the all-in, the frontliner, and the dragon pit. Phantom Hit is the 7th attack, and it repeats max-health Barrage.

Rush BoRK when the lane is short trades and sustain. Vampiric Scepter heals before the item exists, the 7% current-health hit needs no stacks, and three hits slow by 30%. You give up the one-Barrage frontliner kill until Guinsoo is the second item.

## Statikk Shiv

Not worth buying on this on-hit build.

Shiv is a 7.3 on-hit chain (40 AD, 40 AP, 30% attack speed, no crit, 3000g). At level 13 an Energized auto bounces to 6 extra units and applies Barrage and BoRK on them. The chain comes up about twice during one Barrage.

Replacing Runaan with Shiv: the 3-champion fight survives Barrage (Runaan wipes it in 5.8s) and the wave slows from 3.4s to 6.5s. The solo tank is only about 0.3s faster.

Adding Shiv after Guinsoo + Runaan does wipe a 5-champion clump. Terminus in that slot wipes it on the same clock and kills the tank and the dragon sooner. An even game also never reaches that 3000g purchase: the 4-item core finishes at 17:00, and 18:00 gold is 10770 against a 12650 Shiv total.
