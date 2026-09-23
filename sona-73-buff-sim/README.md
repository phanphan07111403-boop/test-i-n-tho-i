# Sona — Wild Rift 7.3 buff gold-efficiency

Sona was **not** hotfix-buffed in 7.3 (still on the 7.2b W heal / R cooldown).
The patch still raises her impact: crit 175%→**200%**, AS cap 2.5→**3**, cheaper
flat **Ardent** (30% AS + 25 on-hit), and new **Echoes of Helia** / Circlet→Diadem.

## Run

```bash
python3 simulate_sona_73.py
python3 test_sona_73.py
```

Outputs:
- `report.txt` — isolated item GE, 210 first-3 paths, 60 full pages, rune ranking, minute-by-minute
- `results.json` — machine-readable winner + timeline + rune ranking

## Question answered

Which **purchase order** gets the most **gold efficiency** out of Sona's auras
and item buffs, including a **4th legendary** and **selling Scythe for a 5th**?
Which **5-slot rune page** is best on that path (not a generic Sona template)?

## Winner (sim)

**Ardent → Helia → Mandate → Harmonic, then sell Scythe → Staff**

| When | Spike |
|------|--------|
| ~8:00 | **Ardent** — 30% AS + 25 on-hit (highest buff-GE vs crit ADC) |
| ~9:00 | Ionian Boots — aura lock |
| ~14:00 | **Helia** — Q hits two champs, W dumps Soul Fragments |
| ~19:00 | **Mandate** — 7% mark on Power Chord / R |
| ~24:00 | **Harmonic Echo** — 4th, 6th slot, chain heal/shield |
| ~27:00 | **Sell Scythe** (280g) → **Staff of Flowing Waters** |

### 6-slot page (until sell)

1. Black Mist Scythe
2. Ionian Boots
3. Ardent Censer
4. Echoes of Helia
5. Imperial Mandate
6. Harmonic Echo

Endgame: Ionian + Ardent + Helia + Mandate + Harmonic + Staff.

5th item is close: **Redemption** is within 0.02 GE (more teamfight heal, less double-buff).

## Why this order

- Isolated @ 12:00, Ardent is ~39 impact per 1k gold. Staff is ~10 as a *first* item. Don't Staff-rush a crit ADC — it is a **5th** after sell, when you want AP/HSP and the Rapids double buff.
- Helia is the best sustain converter (Sona Q is dual-target). Buy it **second**.
- Mandate 3rd multiplies the 7.3 crit ADC. Harmonic 4th spreads W in 5v5.
- Never sell Scythe before four legendaries are finished. The sim only sells when 280g actually completes the 5th.

## Runes (on this build)

Ranked on **Ardent → Helia → Mandate → Harmonic, sell Scythe → Staff** — same shop, swap page only.

**Aery · Font of Life · Bone Plating · Revitalize · Transcendence**

| # | Page | Impact | GE |
|---|------|--------|-----|
| 1 | Aery / FoL / Bone / **Revitalize / Transcendence** | 273.0 | 43.41 |
| 2 | Aery / FoL / Bone / Revitalize / Legend: Haste | 266.6 | 42.05 |
| 3 | Aery / FoL / Bone / Transcendence / Manaflow (no Revitalize) | 265.0 | 42.09 |
| 4 | Aery / Manaflow / Transcendence / Scorch / Bone | 263.7 | 41.88 |
| 5 | Aery / FoL / Bone / Revitalize / Scorch | 264.0 | 42.03 |
| 6 | Aery / FoL / Bone / Revitalize / Manaflow | 263.1 | 41.68 |
| 7 | Fleet / FoL / Bone / Revitalize / Transcendence | 255.8 | 40.04 |
| 8 | Guardian / same minors | 252.4 | 38.73 |
| 9 | Comet / same minors | 252.4 | 38.57 |

Why this page on this item path:

- **Aery** — W/Q spam sends it every ~4s (ally shield + poke). Beats Guardian by +20.6 impact (Guardian waits for a hit), Comet (poke-only), Fleet (mostly self-heal).
- **Font of Life** — Power Chord / Q mark; the 7.3 crit ADC heals while she autos.
- **Bone Plating** — Sona is paper; survive the all-in so auras stay up.
- **Revitalize** — 5% HSP (+extra <40%) on W, Aery, Harmonic chain, Helia dump. Dropping it for Manaflow costs 1.32 GE.
- **Transcendence** — 6/12 AH + L9 10% refund. More W = Ardent's 6s never drops. Beats **Legend: Haste** (+1.36 GE; 7.3 replaced Tenacity, but support stacks it too slowly) and a Scorch or Manaflow 5th slot.

7.3 **removed Ingenious Hunter** (no Mandate/Redemption CDR rune). If you actually OOM before Helia, swap the 5th slot to **Manaflow** (ranks #6 — only when mana is the bottleneck).
