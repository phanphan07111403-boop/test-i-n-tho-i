# AP Kog'Maw — Núp bắn + tank damage

PC League of Legends, patch **~26.x**. Fog-of-war Living Artillery poke over a **28-minute** average game.

## Run

```bash
python3 simulate_ap_kogmaw.py
python3 compare_seraph.py
python3 compare_mix.py
python3 compare_pen.py
```

Outputs:
- `report.txt` — minute-by-minute optimal + 3rd-item spike vs tanks + Seraph + mix + magic-pen appendix
- `results.json` — machine-readable snapshots per build
- `seraph_compare.txt` / `seraph_compare.json` — full 5-item with vs without Seraph
- `mix_compare.txt` / `mix_compare.json` — Muramana / Serylda / Rylai vs full AP
- `pen_compare.txt` / `pen_compare.json` — Void / Shadowflame / Cryptbloom vs burn core

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

## Mix Muramana + armor pen + slow?

**Not as a 2-item package.** Living Artillery is still **magic damage**. The 75% bonus AD ratio rides on that magic hit — **armor pen does not apply to R** (or Q / W / Liandry / Hatefog). Muramana Shock is the only physical chunk (~10% of the window after tank armor). Serylda's 45% pen only helps Shock.

Serylda Bitter Cold (30% slow / 1s) only procs below **60% HP**, so fog poke on a healthy tank gets **no slow**. Kog **E is already 40–60%** and does not stack with item slows. Rylai (30% always on R) is the fog-slow item if you refuse to land E.

Equal 5 legendaries + Sorcs, lvl 18 @ 28:00:

| Build | Fog 8s tank | W 8s tank | Mix 70/30 tank |
|-------|-------------|-----------|----------------|
| Full AP (Cap+Horizon) | baseline | baseline | baseline |
| Muramana + Serylda (drop Cap+Horizon) | **+1.1%** | **−15.6%** | **−6.3%** |
| Muramana 5th (keep AP core) | **+15.1%** | **+1.6%** | **+9.1%** |
| Serylda 5th (no Shock) | −12.1% | −14.7% | — |

Muramana 5th wins for the same reason Seraph does: rank-3 R is **mana-capped** (10 shots vs 8). Do not buy Serylda on this kit. Do not drop Malig or Void. Tear/Manamune before Malig delays the minute-7 Hatefog spike.

## Magic pen Kog'Maw?

You already are one. Q shreds **32% MR**, then Hatefog **−10**, Void **40%**, Sorcs **12** flat. Tank 224 MR → **73** (you deal 58% of raw magic). Squishy 78 MR → **14** (88%) — a second flat-pen item is almost wasted.

Void Staff and Cryptbloom are **1 Void Pen item**; they do not stack.

Equal 5 legendaries + Sorcs, lvl 18 @ 28:00 vs Burn+Void+Cap+Horizon:

| Swap | Fog 8s tank | Fog 20s tank | Fog 8s squishy | Mix 70/30 tank |
|------|-------------|--------------|----------------|----------------|
| Shadowflame instead of Liandry | +0.1% | **−12.1%** | **+21.6%** | +1.6% |
| Shadowflame instead of Horizon | +3.1% | +2.6% | **+20.6%** | +3.3% |
| Shadowflame instead of Void | **−18.4%** | −18.6% | +10.8% | −18.3% |
| Cryptbloom instead of Void | −9.6% | −9.3% | −5.9% | — |

**Kill ADC / shields:** same core, Shadowflame 5th instead of Horizon. **Hurt tanks / long fog R:** keep Liandry, keep Void, keep Deathcap. Do not skip Void for "more pen."

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
