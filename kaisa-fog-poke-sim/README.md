# Kai'Sa — AP fog W poke (Wild Rift 7.2+)

Void Seeker from fog/brush over a **20-minute** Wild Rift game. No Q, no Nashor autos.

## Run

```bash
python3 kaisa-fog-poke-sim/simulate_kaisa_fog_poke.py
```

Outputs:
- `report.txt` — minute-by-minute optimal + buy order, runes, GameSir settings
- `results.json` — snapshots per build

## Question answered

Which **buy order** peaks fog W poke (chunk + 12s siege), and which **runes / settings** belong on that path?

## Winner (sim)

**Luden's Echo → Boots of Mana → Horizon Focus → Rabadon's Deathcap**

Avg 8–20 min 12s fog siege vs squishy: **667**, vs Horizon-first 610 (−9%) and Nashor-first 395 (−41%).

| When | Spike |
|------|--------|
| ~7:00 | **Luden's Echo** — W evolve (70% CD refund) + 140+15% AP echo |
| ~9:00 | Boots of Mana |
| ~14:00 | **Horizon Focus** — +10% from 600+ range (always on 3000-range W) |
| ~20:00 | **Deathcap** — 30% AP amp |

## Why Luden first, not Horizon / Liandry / Nashor

- Living Weapon on a **finished AP item** refunds 70% W CD on champion hit. Unevolved W is 14–20s; evolved is ~4–6s.
- Luden evolves W at the same gold window as Horizon **and** adds a second nuke on the missile. 12s siege at 8:00: **425 vs 310**.
- Horizon 2nd is the long-range tax once echo is already online.
- Liandry/Blackfire lose ~1s of the 3s burn after fog reveal — they walk.
- Infinity Orb execute does nothing on a full-HP fog poke.
- Malignance Hatefog is an ult zone; Kai'Sa R is a dash.
- Nashor evolves **E**, not W.

## Runes

Slot 3 is Storm **or** Scorch, not both.

| Page | 16:00 12s | 20:00 12s |
|------|-----------|-----------|
| **Comet + Scorch** | 867 | 992 |
| **Comet + Gathering Storm** | 858 | **1009** |
| First Strike + Scorch | 813 | 939 |
| First Strike + Storm | 806 | 958 |

Default ranked page: **Arcane Comet + Transcendence + Gathering Storm**. Scorch if the game ends ~12:00. First Strike if you want gold/true over raw W.

## Settings (S22 Ultra + GameSir X3 Pro)

W is a 3000-range **line**, not a Kog R circle.

- WR: joystick Locked, Locked Button Centers Off, Cast on Button Press Off, aiming sens 15–30%, Aim Panning On, champions-only lock.
- G-Touch: W = **Skill Wheel + right stick** (same button you use for Kog R). Never LB tap.
- Poke 1600–2200, not max 3000. Do not fire through the wave.
