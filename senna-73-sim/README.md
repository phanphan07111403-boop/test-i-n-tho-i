# Senna ADC + support — Wild Rift 7.3

Patch **7.3**. Magnetic Blaster is gone. Mist crit 15%→10% per 20. Autos crit
for **90%** of the new 200% crit damage. Attack-speed ratio is **0.4** (she
actually converts Berserkers/RFC now). Q base **50/80/110/140**. Damage Senna,
not the enchanter page.

## Run

```bash
python3 simulate_senna_73.py
python3 test_senna_73.py
```

Outputs:
- `report.txt` — minute tables, path ranking, keystones, traps
- `results.json` — snapshots per role / path / minute

## Question answered

After Magnetic is deleted and Senna's mist crit is halved, which **legal 7.3
path** peaks 8s poke/combat for **ADC (24:00)** and **support (20:00)**?
Hexoptics like Caitlyn, Statikk+RFC like WildRiftFire, leftover lethality, or
Yun Tal/Stormrazor?

Rune loadout: **1 keystone + 3 primary + 1 secondary**. Ingenious Hunter is
gone. Legend: Haste replaced Legend: Tenacity. Lethal Tempo is the 7.3 rewrite.

## Support Shiv rush — buy order (the live page)

Rush **Statikk Shiv**, then these **last 5** (6-slot, Scythe + boots + 3 legendaries):

| # | Buy | When | Why |
|---|-----|------|-----|
| — | Spectral Sickle → **Black Mist Scythe** | ~6:00 | Quest. Do not skip. |
| 1 | **Berserker's Greaves** | ~8:00 | 7.3 AS ratio 0.4 finally converts. Charges Shiv. |
| **2** | **Statikk Shiv** | **~11:00 RUSH** | On-hit lightning. Crash the wave. Copy Relic in the pit. |
| 3 | **Essence Reaver** | ~16:00 | 50 AD + 20 AH + Spellblade on Q. AD feeds Relic bounces. |
| 4 | **Infinity Edge** | ~22:00 | 230% crit (Senna autos still 90% of that). 3500g waits. |
| 5 | **Lord Dominik's Regards** | ~28:00 | 35% pen. Mortal instead vs heal. |

**Last 5 items:** Black Mist Scythe · Berserker's Greaves · Essence Reaver · Infinity Edge · Lord Dominik's Regards

Runes: **Fleet Footwork · Font of Life · Bone Plating · Perseverance · Brutal**  
Spells: Flash + Heal · Skill order **Q → W**, E 1-point, R at 5/9/13  
Combo: Q through the minion/ally, then AA. Do not last-hit.

Skip RFC — Shiv already owns Energized. Hexoptics is the range-amp swap on slot 3. Mortal 2nd vs healers (−1.1%). Serpent's 6th vs Lulu/Karma. GA/Shieldbow vs burst.

## Winners (sim)

### ADC — 24:00, Flash + Barrier

**Youmuu → Collector → Hexoptics → Infinity Edge → LDR**

Boots: **Dynamism** (Long Sword goes into the boot, then Youmuu).

**Lethal Tempo · Brutal · Cut Down · Legend: Alacrity · Bone Plating**

Skill order: **Q → W → E**. R at 5/9/13. Combo: **AA → Q** (mark, then extract
while HP is still high), weave autos for the 1s Q refund.

| When | Spike |
|------|--------|
| ~8:00 | **Youmuu** — 55 AD + 15 lethality while mist is still ~10% crit |
| ~12:00 | **Collector** — 25% crit + execute, fills the IE hole |
| ~16:00 | **Hexoptics** — Magnetic replacement (range amp + 25% crit) |
| ~24:00 | **IE + LDR** — 230% crit (Senna autos still 90% of that = 207%) |

Fleet Footwork is the lane drop-in (−8% 8s damage, more soul-collecting sustain).

### Support — 20:00, Flash + Heal

**Hexoptics → Mortal Reminder**

Boots: **Berserker's Greaves**. Sickle → Black Mist Scythe.

**Fleet Footwork · Font of Life · Bone Plating · Perseverance · Brutal**

Skill order: **Q → W**, E 1-point, R at 5/9/13.

| When | Spike |
|------|--------|
| ~6:00 | Scythe quest |
| ~11:00 | **Hexoptics** — first legendary on sickle gold |
| ~16:00 | **Mortal Reminder** — 30% pen + grievous. Essence Reaver is a tie |

20-min support gold finishes **two** legendaries. RFC/IE/LDR do not complete.
Essence Reaver 2nd is **−0.0%** — take it when the lane is Q-heal, Mortal when
they have a healer. Ionian + Hex + ER is **−0.1%**.

## Why Youmuu still wins 1v1

- Caitlyn rushes Hexoptics because Headshot scales with crit *immediately*.
  Senna's mist crit was cut to 10%/20, so at 8:00 she has ~10% crit from souls.
  Lethality into a squishy beats 25% of a 180% auto — if nobody else is nearby.
- Hexoptics is still the Magnetic *range* replacement — 3rd on the poke page,
  2nd on the Shiv page.
- Yun Tal starts at 0% crit and needs 125 autos. Senna already gets crit from
  mist. Do not stack a second delayed engine.
- IE 2nd is a 3500g hole at 12:00. Collector 3000g fills it on the poke page.

## Why the meta rushes Statikk Shiv

7.3 split Magnetic Blaster into **Hexoptics** (range amp), **RFC** (energized
range), and **Statikk Shiv** (waveclear + on-hit bounce). Senna's old page
*was* Magnetic. Live pages reassemble it, **Shiv first**, because Shiv is the
only piece that crashes a wave.

Official Shiv copies **on-hit onto bounce targets** (3/4/5/6 extras at 1/5/9/13,
60 magic, 90 vs minions). Relic Cannon is 20% AD on-hit. Brutal is on-hit.
Extraction is on-hit. Q applies on-hit to champions. One energized auto into
a wave dumps Relic+90 mag through 4–6 minions. One auto into dragon copies
Relic+extract onto the two people you did not click.

AS ratio **0.4** is why she can rush it. The old ~0.125 ratio could not charge
Energized. Electrotherapy (+5 stacks per auto) plus Q refunds speed the next
proc. Support: minions Senna does **not** last-hit spawn more wraiths — Shiv
chips, the ADC CS's, souls pop. 40 AP feeds Q heal and R.

| At 12:00 | 1v1 | 3-target clump | Wave TTK |
|----------|-----|----------------|----------|
| Youmuu + Collector | **2780** | 2780 | 6.3s |
| Statikk + Hex | 2646 | **3040** | **4.2s** |

Clump ranking over 24:00: **Statikk → Hex → RFC** beats Youmuu (**+2.8%**).
Wave ranking: the four Shiv paths take the top four. 1v1 ranking: Youmuu.

Rush Shiv when you shove, stack souls, and hit dragon pits. Buy Youmuu when
the game is 2v2 poke and you never crash the wave.

## Traps

- **Magnetic Blaster / Cloak of Agility** — deleted in 7.3.
- **Hex first on ADC** copying Caitlyn (−6–7% 1v1 area).
- **Shiv into a 2v2 poke lane that never shoves** — 0% crit, nowhere to bounce.
- **Support IE/LDR** — the gold is not there by 20:00.
- **Enchanter Ardent/Helia** — different sim; Mandate 4th lives in that file.

## Swaps

- **Statikk → Hex → RFC** when you actually shove (clump +2.8%, wave TTK 4.2s).
- Youmuu → Hex (skip Collector) if you need Magnification at 12:00 (−2.8% 1v1).
- Draktharr first on the DH dive Senna, not poke Senna.
- Serpent's Fang 3rd vs Lulu/Karma/Janna shields.
- Steelcaps into Leona/Naut/Rell (−5% poke).
- Shieldbow/GA 6th vs burst.
