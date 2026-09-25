# Senna — Wild Rift 7.3 2nd-item burst / overkill

Patch **7.3** item + kit model. Dragon-lane farmer over a **20-minute** game.

## Run

```bash
python3 senna-burst-sim/simulate_senna_burst.py
```

Outputs:
- `report.txt` — minute-by-minute optimal + 2nd-item spike vs ADC/mid
- `results.json` — machine-readable snapshots per build

## Question answered

After 7.3 deleted Magnetic Blaster, dropped Senna to **10% crit / 20 Mist**, and set autos to **90% of 200% crit**, which path **peaks burst at item 2** and **overkills ADC and mid**?

## Winner (sim)

**Duskblade → Boots of Dynamism → Serylda's Grudge**

At 14:00 vs a full-HP ADC (~1700 HP / 85 armor) this path deals **2032 lucky / 1800 expected** (119% / 106%). Same combo vs mid is **2179 / 1930** (126% / 112%). Isolated 2nd-item spike: **+683 ADC / +711 mid**. Expected damage still kills both — no lucky crit required.

| When | Spike |
|------|--------|
| ~6:00 | **Duskblade** — Nightstalker 60–160 + 18 lethality (item-1 threat) |
| ~8:00 | Boots of Dynamism (+8 lethality) |
| ~10:00 | Dusk + boots + Dirk already **kills** ADC/mid on a lucky combo |
| ~14:00 | **Serylda** — 35% pen on the whole R/W/Q/auto combo (2nd-item peak) |

**Earliest 2-legendary kill:** Hexoptics → Dusk at **13:00** (110% / 116%, also on expected). Take it if the game ends at 13; take Serylda for the fatter overkill once someone buys cloth.

## Why Collector / IE / Yun Tal miss the 2nd-item peak

- Q/W/R **do not crit**. Collector 25% crit and IE 230% only multiply ~2 autos in a 2.5s window.
- Dusk → Collector is 104% / 113% vs ADC/mid. Serylda is 119% / 126% because 35% pen hits every spell.
- RFC / Fiendhunter / Yun Tal are the 7.3 Magnetic Blaster split: **0 AD** Zeal items. Senna has no AD growth. They do not overkill at 2 items (RFC 84% ADC).
- Fiendhunter's post-R guaranteed crits deal **80% of normal crit**, worse than Senna's native 90% unless the auto was already a crit.
- Essence Reaver Spellblade is 135% **base** AD. Senna's base AD is **54 forever**.
- Youmuu 2nd stacks more flat pen on armor Dusk already deleted. Serylda is the new multiplier.

## Playstyle

- Skill: max **Q** → W. R whenever.
- Combo: R from fog → W root → Q (mist extract + Relic on-hit) → auto (Nightstalker).
- Runes: Fleet, Empowered Attack, Brutal, Cut Down.
- Do not buy RFC / Fiendhunter / Yun Tal first. Do not rush IE or Collector as item 2.
