# AP Kog'Maw mid — fog R, every cast a kill

Wild Rift patch **7.3d**. Dark Harvest, AP artillery from fog, over an **18-minute** even mid game.

## Run

```bash
python3 simulate_wr_kog_fog.py
```

Outputs:

- `report.txt` — kill line by minute, build comparison, full-HP dump vs kill chain
- `results.json` — chain / opener / dry lines per build

## Question

Spam Living Artillery from fog, Dark Harvest, AP Kog'Maw. Make every R a kill.

## Answer

A full-HP glob is 25% AP. At 18:00 that is **257 damage**, 9% of the ADC. It is not a kill, and dumping the mana pool still dies before the execute.

Every R is a kill only when you press at or under the **chain line** (Dark Harvest up, Luden down). That cast kills. The next champion under their own line dies to the next R after Harvest's 1s reset.

**Infinity Orb → Spellslinger's Shoes → Stormsurge → Void Staff**, then a rod toward Deathcap (the cap itself is not finished by 18:00).

Rune page: **Dark Harvest**, Eyeball Collection, **Coup de Grace**.

| Clock | Press R on the ADC at or under |
|-------|--------------------------------|
| 8:00 | 23.7% (375 HP) — Infinity Orb is up |
| 12:00 | 22.7% (489 HP) — their MR component landed, Stormsurge is not finished |
| 18:00 | 33.9% (926 HP) |

At 18:00 the same cast kills a mid at **31%** and any enchanter already under **40%**. A bruiser has to be at **15.5%**. A target at 40% HP still lives if they are the ADC: the execute formula is on, and it is still short of 40% of their bar.

Horizon Focus does not help this, because the 10% starts after the first hit and this pattern only hits once. Liandry does not move the one-cast line (21.9% vs 33.9% at 18:00).
