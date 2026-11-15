# Ryze — damage build vs full ability haste

Wild Rift patch **7.3f**. Level 15, six items, Rod of Ages fully stacked when it is bought. Phase Rush, Manaflow, Transcendence, Legend: Haste.

## Run

```bash
python3 simulate_ryze_haste.py
```

Outputs:
- `report.txt` — kill times, 4-second clump damage, and the searched balance point
- `results.json` — the same headline builds, machine-readable

## Question answered

At the end of the game, does the ranked Seraph / Rod of Ages / Deathcap core beat a full ability-haste build in a 1v1 and in a teamfight, and where does extra haste stop being worth the damage?

## Result

Full haste loses both. Each Flux Overload hits about half as hard, and cast time only leaves room for one or two extra spells in a 4-second fight.

The damage/haste balance is **Spellslinger → Seraph → Deathcap → Infinity Orb → Void Staff → Blackfire Torch** (45 item AH). It is the highest 4-second clump damage in the search and still deletes a squishy on the first combo. Keep Rod of Ages instead of Infinity Orb when you need the 550 health.

## Runes on that Blackfire build

```bash
python3 simulate_ryze_runes.py
```

Outputs `runes-report.txt` and `runes-results.json`. Phase Rush stays. The published page left Sorcery slot 3 empty; that slot is Scorch, Nimbus Cloak, Gathering Storm, or Ixtali Seedjar. The page to run is Manaflow, Transcendence, Gathering Storm, and Legend: Haste.

Conqueror and the spellvamp sources on that page:

```bash
python3 simulate_ryze_vamp.py
```

Outputs `vamp-report.txt` and `vamp-results.json`. Conqueror is the weaker healing trade. Legend: Bloodline is the efficient vamp source.
