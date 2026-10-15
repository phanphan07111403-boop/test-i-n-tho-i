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

## Brand vs Zyra, same build

Scythe → Ionian → Liandry → Circlet/Diadem → Helia → Harmonic Echo.

```bash
python3 compare_brand_zyra.py
```

Outputs: `brand-zyra-report.txt`, `brand-zyra-results.json`.

Zyra is ahead. Damage lead is 28% at 8:00 and 5% at 20:00. Brand's detonation still hits the carry harder (1531 vs 1484). Fight healing ties once Diadem arrives at 22:00. Lane healing does not: Zyra 3542/min vs Brand 1915, because plants keep Liandry ticking. Hard CC is 3.71s for Zyra vs 1.13s for Brand, and 1.70s of Zyra's is a knockup.

## Component order — heal at 13:00

Same five legendaries (Scythe, Liandry, Diadem, Helia, Harmonic) plus Ionian boots. Pieces are bought as soon as the gold fits, instead of saving for a finished legendary. Liandry is no longer third.

```bash
python3 optimize_component_path.py
```

Outputs: `component-path-report.txt`, `component-path-results.json`.

Damage starts converting to healing at **13:00**, when Helia and Diadem finish together. The Liandry-third order, on the same charge rules, converts at 21:00. All five legendaries are done at 22:00. Ionian finishes at 23:00.

The early shopping list is Sickle, Circlet's Ruby / Tear / Idol, Circlet at 7:00, Fated Ashes at 9:00, Helia's Kindlegem at 11:00, then Helia's Tome, mirror, and combine at 12:00–13:00. The report lists every component with the gold paid and the stats that piece adds.

## Same items, Liandry removed

```bash
python3 no_liandry_champions.py
```

Outputs: `no-liandry-report.txt`, `no-liandry-results.json`.

Soraka is the champion these items are for. At 18:00, when the list is finished, her fight heal is about 3266. A tank can buy the same items. Leona and Nautilus have no ally heal, so they only get Diadem and a small Helia, and they receive no armor or magic resist from the shop. Rakan is the engage champion whose Q and E use the heal and the shield. Alistar can still frontline during his ultimate, because that damage reduction does not come from a tank item.

Amumu support can buy the same list. At 18:00 his fight heal is 1080, from Diadem (170) and Helia (909), with no kit heal. He deals 1151 and about 3.6s of hard CC. Tantrum only moves his physical EHP from 4778 to 4898, below Leona with W (7191) and far below Alistar during his ultimate (15308). He is a niche engage pick, not the champion these items are for.
