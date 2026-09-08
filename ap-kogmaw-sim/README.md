# AP Kog'Maw — Núp bắn + tank damage

PC League of Legends, patch **~26.x**. Fog-of-war Living Artillery poke over a **28-minute** average game.

## Run

```bash
python3 simulate_ap_kogmaw.py
python3 compare_seraph.py
```

Outputs:
- `report.txt` — minute-by-minute optimal + 3rd-item spike vs tanks + Seraph appendix
- `results.json` — machine-readable snapshots per build
- `seraph_compare.txt` / `seraph_compare.json` — full 5-item with vs without Seraph

## Question answered

Luden or Blackfire first, then Malignance, then 3rd item **feels like damage falls off**. Does **Malignance rush** fix it, while still hurting tanks on a hide-and-shoot pattern?

## Winner (sim)

**Malignance → Sorcerer's Shoes → Liandry's Torment → Void Staff**

At 22:00 vs a tank (~3850 HP / 186 MR), this path deals **~32% more** mix damage than Luden → Malignance → Shadowflame. Isolated 3rd-item spike: Void nearly double Shadowflame.

| When | Spike |
|------|--------|
| ~7:00 | **Malignance** — fog R identity (ult haste + Hatefog zone) |
| ~10:00 | Sorcerer's Shoes |
| ~16:00 | **Liandry** — 2% max HP/s, refreshed by R/W |
| ~21:00 | **Void Staff** — the 3rd-item spike vs tank MR |
| ~26:00 | **Horizon Focus** if fights are now (cheaper, 10% Hypershot on R) |
| ~28:00 | **Deathcap** if the game lasts — peak tank mix |

## 4th after Void

| 4th | When | Take it |
|-----|------|---------|
| Deathcap | ~28:00 | Default peak damage (W %HP + R + Hatefog) |
| Horizon Focus | ~26:00 | Earlier spike, 25 AH, 10% on max-range R |
| Shadowflame | ~27:00 | Need to kill ADC / shields |
| Zhonya | ~27:00 | Dive (Zed, Rengar, Kayn) |
| Morello | ~26:00 | Heavy healing |
| Banshee | ~27:00 | AP pick |

5th–6th: remaining flex. Do not sell Void.

## Seraph's Embrace vs no Seraph (full 5-item)

Seraph (70 AP / 1000 mana / 25 AH / Awe 2% bonus mana / 18% max-mana shield) is **not** Manaflow-exclusive after patch 26.1, but **Archangel's Staff still is**. Malignance + Seraph only works if Seraph has already transformed.

At equal finished items (Malig + Liandry + Void + Deathcap + slot 5), **Seraph instead of Horizon**:

| Window | vs no-Seraph |
|--------|----------------|
| Fog 8s tank | **+9.0%** (10 R vs 8 — mana cap, not CD) |
| Fog 8s squishy | **+10.4%** |
| W siege 8s tank | **+2.3%** (Horizon 10% on W %HP almost ties) |
| Mix 70/30 tank | ~**+7%** |
| Shield | **+518** (Lifeline, 90s, below 30% HP) |

**Do not** replace Malignance (−4.5% fog / −11% 20s tank — lose Hatefog) or Deathcap (−8% W tank).

Cost: Tear → Archangel → Seraph **before** Malignance, so you lose the minute-7 Hatefog spike and delay Liandry/Void. Mid-game the Seraph path is behind; late dump-R it can go ahead.

Default still Malig → Liandry → Void → Cap → Horizon. Seraph is a 5th-slot flex if you actually OOM on R, or a 6th item if you have an extra slot.

## Runes

**Keystone: Arcane Comet** (distance amp — R at 1300–1800 is max range).

Primary (Sorcery): Comet → Manaflow Band → Absolute Focus → Scorch  
(Gathering Storm if the game is even / 4–5 items)

Secondary (Precision): Presence of Mind + **Cut Down** (+8% vs >60% HP tanks)

Alt secondary (Domination): Ultimate Hunter + Cheap Shot (more R, less tank amp)

Shards: AS / Adaptive AP / HP  
Summoners: Flash + TP (mid) or Flash + Barrier/Ghost

First Strike only if you always hit first from fog and never get tagged in lane. PTA / LT are ADC pages, not this kit.

## Why Luden/BF → Malig 3rd-item feels weak

- Two Lost Chapter items stack mana/AH. Item 2 does not open a new kit vs tanks.
- Hatefog / Echo / Blackfire burn scale with **AP**, not max HP. A 3k HP / 180 MR tank eats it.
- Typical 3rd after two mana items is **Shadowflame** (15 flat pen + crit below 40% HP). Flat pen is tiny on 180 MR; Cinderbloom does not proc while you poke a full-HP tank.
- Isolated 3rd-item delta vs tank: Shadowflame after Luden+Malig is a small bump. Void after Malig+Liandry is the actual spike.

## Playstyle

- **Núp:** R from fog onto the tank's feet — Hatefog zone + Liandry ticks.
- **Siege:** Q shred → W max-range autos from brush.
- Skill order: max **W** (tank) → Q (shred) → E.
- Do not buy two Lost Chapter items. Nashor only if you all-in W more than fog R.
