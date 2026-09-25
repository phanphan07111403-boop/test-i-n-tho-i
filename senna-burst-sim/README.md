# Senna — Wild Rift 7.3 2nd-item burst / overkill

Patch **7.3** item + kit model. Two roles over a **20-minute** game:

| Role | Economy | Question |
|------|---------|----------|
| **ADC** farmer | farm + plates | Which path peaks burst at item 2 and overkills ADC + mid? |
| **Support** fasting | Sickle / Scythe + souls | Dusk first (early Nightstalker), then which 2nd item peaks? |

```bash
python3 senna-burst-sim/simulate_senna_burst.py
```

Outputs:

- `report.txt` / `results.json` — ADC lethality
- `report-support.txt` / `results-support.json` — support Dusk-first + crit fallback (20 min)
- `results-support-finish.json` — sell Scythe, 5th legendary, rune ranking (28 min)

7.3 kit: no AD growth, Relic 20% AD on-hit, Q/W/R **do not crit**, autos deal **90%** of 200% crit (IE 230%). Mist is **10% crit / 20 stacks**. Magnetic Blaster is gone.

---

## ADC winner

**Duskblade → Boots of Dynamism → Serylda's Grudge**

At 14:00 vs a full-HP ADC (~1700 HP / 85 armor) this path deals **2032 lucky / 1800 expected** (119% / 106%). Same combo vs mid is **2179 / 1930** (126% / 112%). Isolated 2nd-item spike: **+697 ADC / +711 mid**. Expected damage still kills both — no lucky crit required.

| When | Spike |
|------|--------|
| ~6:00 | **Duskblade** — Nightstalker 60–160 + 18 lethality (item-1 threat) |
| ~8:00 | Boots of Dynamism (+8 lethality) |
| ~10:00 | Dusk + boots + Dirk already **kills** ADC/mid on a lucky combo |
| ~14:00 | **Serylda** — 35% pen on the whole R/W/Q/auto combo (2nd-item peak) |

**Earliest 2-legendary kill:** Hexoptics → Dusk at **13:00** (110% / 116%, also on expected). Take it if the game ends at 13; take Serylda for the fatter overkill once someone buys cloth.

Q/W/R do not crit, so Collector / IE / Yun Tal miss this spike. RFC / Fiendhunter are 0-AD Zeal. Essence Reaver is 135% of base AD **54**.

---

## Support winner: Dusk first, then Serylda

Same pattern as ADC, on fasting gold, **no Dynamism** so the 2nd item lands at 14:00 not 16:00.

**Spectral Sickle → Duskblade → Serylda's Grudge**

| When | Spike |
|------|--------|
| ~5:00 | Black Mist Scythe (quest) |
| **~8:00** | **Duskblade** — Nightstalker 60–160 + 18 lethality. **100% ADC / 104% mid** (mid already a kill) |
| **~14:00** | **Serylda** — 35% pen on R/W/Q/autos (**2nd-item peak**) |

At 14:00: **2259 lucky / 2004 expected** vs ADC (**133% / 118%**). Mid **2414 / 2140** (**140% / 124%**). Isolated 2nd-item Δ **+584 / +609**. Expected still kills both.

At 8:00 Dusk is already **100% vs ADC** and a mid kill. Crit-only Collector at the same minute is **88%**. Nightstalker is the lane.

### Which 2nd after Dusk

Q/W/R do not crit, so %pen is the 2nd-item overkill — same lesson as ADC.

| 2nd after Dusk | When | ADC / mid | Isolated Δ |
|----------------|------|-----------|------------|
| **Serylda** | 14:00 | **133% / 140%** | **+597** |
| Mortal | 14:00 | 125% / 132% | +456 |
| Youmuu | 14:00 | 122% / 132% | +430 |
| Collector | 14:00 | 116% / 126% | +336 |
| Hex | 14:00 | 115% / 124% | +311 |
| IE | 15:00 | 116% / 125% | +417 |
| Serylda + Dynamism | **16:00** | 142% / 150% | +823 |

Dynamism 2nd is fatter but **two minutes late**. Skip the 1200g boots if the goal is the 14:00 peak.

Crit-only **Collector → Mortal** is 112% / 118% at 14:00 — keep it only if you refuse lethality.

---

## Full build: sell Scythe, 5th legendary

Core is **Dusk → Serylda**. Do **not** sell Scythe until the last legendary is affordable (~27:00). Scythe is 68 AD; the 350g sell finishes it.

**Dusk → Serylda → Youmuu → Collector → sell Scythe → Fiendhunter**

28:00: **215% / 231%** ADC/mid. Sitting on Scythe + 4 items is 168% ADC. Selling for the 5th is **+976** lucky vs ADC.

Fiendhunter is a trap as **item 1**. As **item 5** the 45% AS + 15% true on already-critting shots buys a 3rd auto.

### Runes (this burst, fog R)

**Keystone: First Strike** — R from fog always opens combat. 9% bonus **true** on the whole 2.5s combo.

| When | Page |
|------|------|
| Lane / 2nd-item | First Strike · **Brutal** · **Empowered Attack** · **Cut Down** |
| Full build (~28:00) | First Strike · Brutal · Empowered Attack · **Gathering Storm** (~44 AD) |

First Strike is **+20pp** over Fleet on the 5-item combo (Cut Down page) and **+36pp** with Gathering Storm stacked. Electrocute was gutted in 7.2 (10% bAD). Fleet / Lethal Tempo add **0 burst**.

## Playstyle (both)

- Skill: max **Q** → W. R whenever.
- Combo: R from fog → W root → Q (mist extract + Relic on-hit) → auto (Nightstalker).
- Fasting: ADC last-hits, you take souls.
- Runes: **First Strike**, Brutal, Empowered Attack, Cut Down → Gathering Storm late. Fleet only if you never get the fog R.
