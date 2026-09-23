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
- `report.txt` — isolated item GE, 210-path search, minute-by-minute winner
- `results.json` — machine-readable top paths + timeline

## Question answered

Which **purchase order** gets the most **gold efficiency** out of Sona's auras
and item buffs, and the most **impact** next to a 7.3 crit ADC?

## Winner (sim)

**Ardent Censer → Echoes of Helia → Imperial Mandate**

| When | Spike |
|------|--------|
| ~8:00 | **Ardent** — 30% AS + 25 on-hit (highest buff-GE vs crit ADC) |
| ~9:00 | Ionian Boots — aura lock |
| ~14:00 | **Helia** — Q hits two champs, W dumps Soul Fragments |
| ~19:00 | **Mandate** — 7% mark on Power Chord / R |

3rd item is close: Harmonic Echo wins a bit more heal-buff GE; Mandate wins
more 7.3 fight impact because it multiplies the crit ADC.

## Why this order

- Isolated @ 12:00, Ardent is ~37 impact per 1k gold. Staff is ~8. Don't Staff-rush a crit ADC.
- Helia is the best sustain converter (Sona Q is dual-target). Buy it **second**. Helia-first ranks #6: slightly better raw GE, much worse buff-GE, and you miss ~2 minutes of 7.3 crit conversion.
- Circlet→Diadem is real HSP, but in a 20-min support curve it loses to a second 2400g combat item.
- Mandate / Redemption / Harmonic **first** spend 2400–2600g on a fight-once effect and miss the 2v2 Ardent spike.

## Play

W max → Q max → E. Rotate Q→W→E so auras never drop. W even at full HP
(Ardent still procs). Power Chord the person your ADC is hitting.

AP ADC (Kai'Sa / Ezreal): Staff instead of Ardent.
