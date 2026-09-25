# Senna — Wild Rift 7.3 2nd-item burst / overkill

Patch **7.3** item + kit model. Two roles over a **20-minute** game:

| Role | Economy | Question |
|------|---------|----------|
| **ADC** farmer | farm + plates | Which path peaks burst at item 2 and overkills ADC + mid? |
| **Support** fasting | Sickle / Scythe + souls | Which **crit** path peaks at item 2 **and** is stronger at 18–20? |

```bash
python3 senna-burst-sim/simulate_senna_burst.py
```

Outputs:

- `report.txt` / `results.json` — ADC lethality
- `report-support.txt` / `results-support.json` — support crit (20 min)
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

## Support crit winner

**Spectral Sickle → Collector → Mortal Reminder → Infinity Edge**

Fasting support (~100 Mist at 20:00 = 50% free crit + 125 AD). Skip Boots of Dynamism — 1200g delays 2nd item from **14 to 16** and leaves you short of IE.

At **14:00** vs a full-HP ADC this path deals **1898 lucky / 1835 expected** (112% / 108%). Mid is **2026 / 1959** (118% / 114%). Isolated 2nd-item Δ **+393 / +395**. Expected still kills both.

At **20:00** the same combo is **121% ADC / ~124% mix** with **100% crit**, IE on, 107 Mist. Late is **+10pp** over the 2nd-item minute.

| When | Spike |
|------|--------|
| ~5:00 | Black Mist Scythe (quest) |
| ~8:00 | **Collector** — 50 AD, 10 lethality, 5% execute, 25% crit |
| ~14:00 | **Mortal Reminder** — 30% pen on R/W/Q/autos (**2nd-item peak**) |
| ~20:00 | **Infinity Edge** — 230% × Senna 90% = 207% autos; souls already crit |

**Range-first alt:** Hexoptics → Mortal → IE. 2nd at 14:00 is 110% / 116% ADC/mid, same 124% mix at 20:00. Take it if you want the 10% range amp; Collector first is the fatter execute spike.

### Why Mortal 2nd, not Collector 2nd or IE 2nd

Same 7.3 lesson as ADC, on a crit chassis: spells don't crit, **%pen** is the 2nd-item overkill.

- Hex → Collector 2nd: 105% / 112% (no pen).
- Hex → IE 2nd: 107% / 113% (a minute later, 230% only hits ~2 autos).
- Collector → Mortal 2nd: 112% / 118% at 14:00, then IE at 20:00.

### Dynamism / Yun Tal / RFC traps

- **Dynamism before item 2:** Collector → Mortal at 16:00 is a fatter 119% / 126% spike, but you **do not finish IE**. Late is flat (122%). Skip the 1200g boots on a crit support.
- **Yun Tal → IE:** strongest 20:00 (146% mix) once stacked crit + IE + Mortal 3rd. 2nd-item is only 101% / 108% — misses the peak.
- **Fiendhunter / RFC first:** 0 AD. RFC does not overkill ADC at 2 items (98%). As **5th** after IE + 100% crit they can buy a 3rd auto — see full build.
- **LDR 2nd:** 35% pen is real, but 3300g delays IE; 20:00 is 118% with **no IE**.

### Lethality still bursts harder

On the same support gold, **Dusk → Serylda** is 142% / 150% at 16:00 and 146% / 155% at 20:00. Nightstalker is a flat proc; soul crit does not multiply it. Pick that if you will leave the crit fantasy. This ranking is **crit-only**.

---

## Full build: sell Scythe, 5th legendary

Do **not** sell until the 5th item is affordable (~28:00 on this gold curve). Scythe is 68 AD (28 + 40 soulcast); the 350g sell is what completes a 3000g legendary.

**Collector → Mortal → IE → Duskblade → sell Scythe → Fiendhunter Bolts**

| When | Spike |
|------|--------|
| ~25:00 | **Duskblade** 4th — Nightstalker + 18 lethality (170% mix) |
| ~28:00 | **Sell Scythe → Fiendhunter** — 45% AS + Opening Barrage 15% true on already-critting IE autos. **206% / 220%** ADC/mid |

Sitting on Scythe + Hex (4 items) at 28:00 is only 152% ADC. Selling for the 5th is **+1132** lucky vs ADC.

Fiendhunter/RFC were traps as **item 1**. At 5th you already have 100% crit and IE, so the 0 AD is paid for by a **3rd auto** and (Fiendhunter) 15% true. Safer 5ths if you hate 0-AD: Dusk → RFC (195%), Dusk → Youmuu (188%), Hex → Dusk (177%).

BT / GA 5th often miss the gold window (kept Scythe). Serylda 5th after Dusk is 3100g — 350g short at 28:00.

### Runes (this burst, fog R)

**Keystone: First Strike** — R from fog always opens combat. 9% bonus **true** on the whole 2.5s combo. 7.2 only nerfed the gold ratio (ranged 45%).

| When | Page |
|------|------|
| Lane / 2nd-item | First Strike · **Brutal** · **Empowered Attack** · **Cut Down** |
| Full build (~28:00) | First Strike · Brutal · Empowered Attack · **Gathering Storm** (~44 AD) |

First Strike is **+19pp** over Fleet on the 5-item combo (Cut Down page) and **+33pp** with Gathering Storm stacked. Electrocute was gutted in 7.2 (10% bAD, was 40%) — still procs on R+W+Q but only +8pp. Fleet and Lethal Tempo add **0 burst**. Empowerment needs 3 basic attacks; this combo's 8% amp lands on nothing.

## Playstyle (both)

- Skill: max **Q** → W. R whenever.
- Combo: R from fog → W root → Q (mist extract + Relic on-hit) → auto.
- Fasting: ADC last-hits, you take souls.
- Runes: **First Strike**, Brutal, Empowered Attack, Cut Down → Gathering Storm late. Fleet only if you never get the fog R.
