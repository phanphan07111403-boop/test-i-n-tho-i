# Brand Support — Wild Rift 7.3b heal and damage

Patch **7.3b**. Support gold curve over **22 minutes**. The listed build:

1. Black Mist Scythe
2. Ionian Boots of Lucidity
3. Whispering Circlet → Diadem of Songs
4. Echoes of Helia
5. Harmonic Echo
6. Ardent Censer or Mikael's Blessing

## Run

```bash
python3 simulate_brand_support.py
```

Outputs:
- `report.txt` — gold clock, heal table, damage table, full 6-item sheet
- `results.json` — the same rows

## Question answered

Can this Brand heal like an enchanter, and does he still deal mage-support damage?

## Result

He does neither job well.

| | 8s fight at 22:00 |
|--|--|
| Brand heal | 1638 (0 until Diadem at ~16:00) |
| Soraka heal | 3788 |
| Nami / Yuumi heal | 1358 / 1410 |
| Seraphine heal + shield | 1086 + 1212 |
| Brand damage | 2068 |
| Brand Liandry → Rylai → Mandate | 3280 |
| Zyra Liandry → Rylai | 3780 |
| Morgana / Lux | 2135 / 2150 |

Brand has no heal or shield. Helia stores 30% of champion damage and spends it only when something heals an ally. That something is Diadem, which shows up around 16:00. Until then the shards do not heal.

Ardent vs Mikael's barely matters on a 22-minute clock: Ardent finishes at 22:00, Mikael's is about 40 gold short. On a full sheet, Mikael's wins the fight you press (+202 heal, 75s cooldown) and Ardent deals 143 more damage.

## Why

- Diadem heals 0.8% max mana per second in combat. Harmony after the 7.3a nerf is +0.25% of max mana as heal/shield power.
- Soraka's W and Wish do not need Brand to land a combo first.
- Liandry is 2% max HP per second plus 7% magic penetration. Helia's 40 AP does not replace it.
- Harmonic Echo only copies a heal. It does not create one.
