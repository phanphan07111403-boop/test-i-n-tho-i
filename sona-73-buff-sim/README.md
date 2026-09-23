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
- `report.txt` — isolated item GE, 210 first-3 paths, 60 full pages, minute-by-minute
- `results.json` — machine-readable winner + timeline

## Question answered

Which **purchase order** gets the most **gold efficiency** out of Sona's auras
and item buffs, including a **4th legendary** and **selling Scythe for a 5th**?

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

- Isolated @ 12:00, Ardent is ~37 impact per 1k gold. Staff is ~8 as a *first* item. Don't Staff-rush a crit ADC — it is a **5th** after sell, when you want AP/HSP and the Rapids double buff.
- Helia is the best sustain converter (Sona Q is dual-target). Buy it **second**.
- Mandate 3rd multiplies the 7.3 crit ADC. Harmonic 4th spreads W in 5v5.
- Never sell Scythe before four legendaries are finished. The sim only sells when 280g actually completes the 5th.
