# AP Varus — burst spike on every finished item

PC League of Legends, patch **26.21**. One all-in rotation over an unfed gold curve.

## Run

```bash
python3 simulate_ap_varus.py
```

Outputs:

- `report.txt` — buy order, spike at each finished legendary, minute curve
- `results.json` — the same numbers for the top orders

## Build

**Sorcerer's Shoes → Shadowflame → Void Staff → Stormsurge → Rabadon's Deathcap → Cryptbloom**

Five legendaries. Doran's Ring to start, sold when the inventory is full.

| Finish | Time | All-in | Squishy HP | Click upgrade |
|--------|------|--------|------------|---------------|
| Shadowflame | 12:00 | 2944 (147%) | one-shot | **+701** (15 pen + execute; the 110 AP is already on the rod and alternator) |
| Void Staff | 18:00 | 4361 (173%) | pick combo also crosses 100% | **+1040** |
| Stormsurge | 23:00 | 6100 (211%) | | **+969** |
| Rabadon's Deathcap | 28:00 | 7662 (243%) | | **+850** (the 30% AP multiplier; both rods are already 130 AP) |
| Cryptbloom | 33:00 | 10190 (307%) | | **+1317** |

The all-in first passes 100% of the squishy's HP at **7:00**, on Sorcerer's Shoes + Needlessly Large Rod, before Shadowflame is finished.

## Buy order

1. Doran's Ring (400)
2. Sorcerer's Shoes (1100) — ~5:00
3. Needlessly Large Rod (1200) — ~7:00, combo crosses 100%
4. Hextech Alternator (1100)
5. **Shadowflame** (900) — 12:00
6. Blighting Jewel (1100)
7. Blasting Wand (850)
8. **Void Staff** (1050) — 18:00
9. Hextech Alternator (1100)
10. Aether Wisp (900)
11. **Stormsurge** (800) — 23:00
12. Needlessly Large Rod (1200)
13. Needlessly Large Rod (1200)
14. **Rabadon's Deathcap** (1100) — 28:00
15. Blighting Jewel, Fiendish Codex, Fiendish Codex
16. **Cryptbloom** (200) — 33:00

Net gold to the 5th legendary is **16720** (the 17000 on the receipt minus 280 from selling Doran's).

## Runes

The five names in the request do not fit one page. Sorcery secondary is two runes, one per row, and Fleet Footwork locks Precision as the primary tree.

| Slot | Rune | What it does in this combo |
|------|------|----------------------------|
| Precision keystone | Fleet Footwork | 0 damage. Keeps you above 70% HP so Absolute Focus stays on, and kites the 3 setup autos. |
| Precision 1 | Presence of Mind | 0 damage. The mana rune that fits. Manaflow does not. |
| Precision 2 | Legend: Alacrity | 0 damage on the number. Gets 3 autos out inside Blight's 6s window without Nashor's Tooth. |
| Precision 3 | Coup de Grace | Won against Cut Down. The charged Blight pop and the W active land below 40% HP. |
| Sorcery | Absolute Focus | 3–33 AP while above 70% HP. |
| Sorcery | Gathering Storm | 8 / 24 / 48 / 80 AP at 10 / 20 / 30 / 40 min. |
| Shards | Adaptive, Adaptive, scaling HP | Both offense shards are AP once Doran's Ring or Absolute Focus is on. |

Taking Manaflow means dropping one of the two damage runes. On this item path, dropping Absolute Focus (keep Gathering Storm) ends at **298%** of the squishy instead of **307%**. Dropping Gathering Storm ends at **281%**.

## Combo

**All-in:** 3 autos → R from at least 600 range (detonates the 3 Blight, applies a new set over the root) → W during the Q channel → release fully charged.

**Pick:** skip the autos. R → charged W+Q. That version crosses 100% at Void Staff (18:00).

Patch 26.21 Blight is **2.5–4.5% max HP per stack (+1.4% per 100 AP)**, times **1.70** on a full Q. W active is **6–10% missing HP per stack**, also times 1.70, and has no AP ratio. R is 150/250/350 (+100% AP). A squishy with no tenacity takes 3 stacks from the root. Mercury's Treads cut that to 2. Cleanse or QSS before 0.65s applies none.

At full build the all-in is about **3400** from the charged Blight pop, **2200** from W active, **2000** from the uncharged pop on R, **1100** from R itself. Autos and Q's physical damage are under 400 combined. Damage keeps counting after the target would die, which is why the late percentages sit near 300%.

## Why this order

- **Sorcs before the first legendary.** 12 flat pen multiplies every Blight pop while AP is still a rod.
- **Shadowflame first.** 110 AP, 15 pen, and +20% magic damage below 40% HP. That execute line hits the charged pop and the missing-HP active, which are most of the combo. Stormsurge's Squall (125 + 10% AP) is smaller at one item.
- **Void Staff second.** By 18:00 the squishy has real MR. 40% pen is the next multiplier, and it is the item that makes the no-auto pick a one-shot.
- **Stormsurge third.** Another 15 flat pen (42 total with Sorcs and Shadowflame) plus Squall. Flat pen is at its best once percent pen is already in the inventory.
- **Deathcap fourth.** Both rods are already 130 AP. The upgrade is only the 30% multiplier, and that multiplier is finally larger than another pen component.
- **Cryptbloom fifth.** 75 AP and 30% pen. With Void Staff the two percent-pen items are **58%** pen total (they multiply, they do not add). A ~97 MR target is pushed to about 0 MR, and that click is the biggest upgrade in the build (+1317).

## What lost

| 5th item instead of Cryptbloom | Full all-in |
|--------------------------------|-------------|
| Cryptbloom | 307% |
| Luden's Echo | 274% |
| Nashor's Tooth | 274% |
| Horizon Focus | 273% |
| Zhonya's Hourglass | 254% |

Nashor's Tooth first, best follow-up, is **184%** at three items against this path's **211%**, and **274%** at five items against **307%**. Three autos of 15 (+15% AP) on-hit do not beat a second Blight detonation with penetration. R already applies the three stacks. Buy Nashor's only when ult is down so often that the autos are the whole trade.

Zhonya's is the defensive fifth. It is a stasis and 105 AP, and it gives up about a sixth of the combo.

## Assumptions

- Farmer gold, not a kill lead. Same order if you are ahead; you just finish sooner.
- Skill order: Q start, max W, then Q, E last. R at 6/11/16.
- Horizon Focus was in the search. Its 10% amp loses to penetration on this rotation.
- Lich Bane does not proc. Q's channel locks attacks, and the spellblade wants an auto afterward.
- Luden's isolated echo (150 + 10% AP) was in the search and never won a slot.
