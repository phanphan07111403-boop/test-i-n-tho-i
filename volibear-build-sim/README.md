# Volibear Baron — strongest item order

Patch **7.3** (Sep 2026). Isolated 8s 1v1 vs a bruiser. Same GameSir X3 Pro Volibear (easy 1v1, hard to kill).

## Run

```bash
python3 volibear-build-sim/simulate_volibear_build.py
```

Outputs `report.txt` + `results.json`.

## Question answered

Which buy order makes Volibear **strongest** — mix damage **and** HP / E shield / heals — not just a tanky HP bar.

## Winner

**Dusk and Dawn → Plated Steelcaps → Hullbreaker → Riftmaker → Unending Despair → Amaranth's Twinguard**

Diamond+ CN 7.3 most-played core is Dusk → Hull → Rift at **~60% WR**. The sim agrees on a 22-minute 1v1 strength sum.

| When | Buy |
|------|-----|
| Start | **Long Sword** |
| First back | **Sheen** (800) if you can; else Ruby Crystal |
| ~7:00 | **Dusk and Dawn** (3100) |
| Next | **Plated Steelcaps** (Mercury's if they are AP/CC) |
| 2nd item | **Hullbreaker** (3100) — Skipper 4th auto is the 1v1 punch |
| 3rd item | **Riftmaker** (3100) — 8% damage amp, 10% omnivamp, AP from HP |
| 4th item | **Unending Despair** — 3% max HP pulse, heal 250% of it |
| 5th item | **Amaranth's Twinguard** |
| Enchant | **Stoneplate** |

Skill order still **W > Q > E**. Flash + Ignite. Grasp or Lethal Tempo.

## Why this order

| Item | Why it is here |
|------|----------------|
| **Dusk first** | 233g cheaper than Trinity. HP + haste + AS + AP. AP feeds E shield, R, and lightning. Spellblade is magic and **double-applies on-hit** (two lightnings). |
| **Hull second** | Skipper: every 4th auto is 160% base AD + 5% max HP. That is the 1v1 item. Also 45 AD for Q / empowered W / R. |
| **Rift third** | Turns the slugfest into a heal-off. 2% bonus HP → AP, so Heartsteel-less HP still scales the kit. |
| **Despair fourth** | Unkillable pulse. You already have damage. |

Do **not** buy Trinity and Dusk together (both spellblade).

## Rank (sim, 8s 1v1 strength)

| Path | 8:00 | 14:00 | 22:00 |
|------|------|-------|-------|
| **Dusk → Hull → Rift** | 4609 | 5605 | **8251** |
| Dusk → Rift → Despair | 4609 | 5605 | 8118 |
| Heart → Dusk → Hull | 4426 | 5418 | 7991 |
| Heart → Tri → Despair | 4426 | 5418 | 7938 |
| Tri → Rift → Twin | 4645 | 5607 | 7295 |

Trinity’s first-item mix is a hair higher at 8:00. Dusk still wins the game: it finishes **~7:00**, then Hull Skipper and Riftmaker bury the Trinity path.

Heartsteel first is tankier and cheaper (2800). It is **not** stronger in the 1v1 — no sheen, no attack speed.

## Swaps

- **Grouping, not splitting:** Hullbreaker 2nd → **Riftmaker** 2nd, Despair 3rd.
- They heal (Aatrox, Soraka, Vlad): **Thornmail** instead of Twinguard.
- Heavy AP: Steelcaps → **Mercury's**, Twinguard → **Kaenic Rookern**.
- You are losing lane to poke and cannot finish Dusk: **Heartsteel** first, then Dusk, then Hull. This is the Diamond+ alt, not the strongest 1v1.
