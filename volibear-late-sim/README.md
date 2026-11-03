# Volibear — hard to kill, high damage, at 34:00

PC League of Legends, patch **26.21**. He ults onto a carry and stands in a carry-plus-mage focus for 11 seconds.

## Run

```bash
python3 simulate_volibear.py
```

Outputs:
- `report.txt` — the winning build, the purchase order, and the traps
- `results.json` — the ranked six-item results

## Winner

**Plated Steelcaps → Protoplasm Harness → Navori Flickerblade → Overlord's Bloodmail → Spirit Visage → Black Cleaver**

Runes: Conqueror, Triumph, Legend: Haste, Last Stand, Revitalize, Overgrowth. Attack speed, adaptive force, health.

| At 34:00 | Result |
|----------|--------|
| Ultimate dive | **8119** damage, lives, ends at **31%** HP |
| Same fight, no ultimate | 7193 damage, still alive |
| Full tank (Heartsteel, Jak'Sho, Randuin) | 4368 damage, lives |
| AP glass (Dusk, Nashor, Deathcap, Void) | dies in about 4 seconds |

Wounded bite at full HP is **1.95×** (105 + 110% AD + 6% bonus HP, then 1.50 + bonus AD / 400). Bloodmail is the AD. Navori is why W comes back in about 2 seconds while he is autoing. Protoplasm is the Lifeline that keeps him in that fight. Visage multiplies the W heal, the E shield and that Lifeline.

## When they have antiheal

40% grievous kills the Visage build at 10.3s. Swap Visage for **Kaenic Rookern**. That version still does about 8100 damage and finishes the window.

## Order

Protoplasm before the damage items. The same six items with Navori or Cleaver first are still dying at 30:00. Visage, fourth damage item in, is the minute he starts living the focus (about 26:00). Cleaver is the last spike, because the carry is already dead and the shred is for whoever is left.

## Not the late-game build

- Shojin + Sterak + Bloodmail + Unending lives, and does about 7100. The bite is fatter. He gets fewer of them.
- Heartsteel and pure resists live and leave the bite at 1.50×.
- Deathcap / Nashor with no health dies while the ultimate is still up.
- Trinity is a one-item spellblade. It is not the six-item cap.
