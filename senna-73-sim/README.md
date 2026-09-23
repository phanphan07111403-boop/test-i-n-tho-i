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

## Why Youmuu first (not Hex, not Statikk)

- Caitlyn rushes Hexoptics because Headshot scales with crit *immediately*.
  Senna's mist crit was cut to 10%/20, so at 8:00 she has ~10% crit from souls.
  Lethality into a squishy beats 25% of a 180% auto.
- Hexoptics is still the Magnetic replacement — it is **3rd**, once Collector
  has put crit and execute on the page.
- Statikk has **0% crit**. WildRiftFire's Statikk → RFC page is waveclear/clump.
  1v1 poke wants AD + lethality + Hex.
- Yun Tal starts at 0% crit and needs 125 autos. Senna already gets crit from
  mist. Do not stack a second delayed engine.
- IE 2nd is a 3500g hole at 12:00. Collector 3000g fills it.
- AS ratio 0.4 is a real gift. It is not enough to beat the 8:00/12:00 lethality
  windows. Spend it on Berserkers (support) or Spectral Haste (Youmuu), not on
  a Shiv first item.

## Traps

- **Magnetic Blaster / Cloak of Agility** — deleted in 7.3.
- **Hex first on ADC** copying Caitlyn (−6–7% area).
- **Statikk → RFC** as the default WRF page (−20%+ on ADC).
- **Support IE/LDR** — the gold is not there by 20:00.
- **Enchanter Ardent/Helia** — different sim; Mandate 4th lives in that file.

## Swaps

- Youmuu → Hex (skip Collector) if you need Magnification at 12:00 (−2.8%).
- Draktharr first on the DH dive Senna, not poke Senna.
- Serpent's Fang 3rd vs Lulu/Karma/Janna shields.
- Steelcaps into Leona/Naut/Rell (−5% poke).
- Shieldbow/GA 6th vs burst.
