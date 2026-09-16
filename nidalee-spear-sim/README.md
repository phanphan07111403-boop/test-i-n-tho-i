# Nidalee — Spear-only Q spam vs convert

PC League of Legends, patch **~26.18**. Jungle gold curve, **28-minute** average game.

## Run

```bash
python3 simulate_nidalee_spear.py
```

Outputs:
- `report.txt` — minute-by-minute optimal, same-item A/B, verdict
- `results.json` — machine-readable snapshots per build

## Question answered

Is **spear-only Q spam** worth playing on Nidalee — stay human, throw Javelin Toss, never convert to cougar?

## Winner (sim)

**No as her identity. Yes as the setup / tank-siege phase.**

Best combat path: **Lich Bane → Sorcerer's Shoes → Rocketbelt / Liandry → Void**, and you **convert** when the spear lands.

At 22:00 vs a squishy (~2700 HP), convert deals **~31% more** expected damage than the best spear-only path (1334 vs 922 per 12s window; 49% vs 34% of their HP). Same Lich Bane build if you refuse to auto: **−46%** (713 vs 1329).

| When | What to do |
|------|------------|
| Clear / 2v2 | **Cougar.** Spear-only is not a jungler. |
| Spear lands | **Convert:** Pounce → Swipe → Takedown + Lich Bane |
| Vs tanks / siege | **Stay human**, Liandry ticks. Don't dive a healthy tank. |
| ~8:00 | **Lich Bane** — only if you will auto on Takedown |
| Into HP stack | Liandry / Horizon / Void instead of Shadowflame |

## Why spear-only loses the champion

- **Hunt** exists to buff Takedown (+30%) and Pounce range. Never converting leaves the mark uncashed.
- A landed max spear at 16:00 is **~20% of a squishy's HP**. The convert combo is **~41%** — a pick with ignite or a teammate, not a poke tick.
- Max-range accuracy is ~32% vs mobile targets. Even a charitable mix (70% mid-range / 30% max) still loses the squishy window.
- **Lich Bane** (her real core) is Spellblade on the Takedown auto. Spear-only never attacks, so the item is dead.

## When Q spam *is* the button

Vs tanks you should not melee, spear-only **wins** the window. Liandry + Horizon at 22:00: **840** vs Lich-convert **519** (+62%), because converting onto a healthy tank is often just dying (sim uses a 55% commit rate).

Horizon's 10% also applies to the **cougar combo** for 6s after a ≥600-range Hunt spear. Do not skip convert just because you bought a poke item.

## Playstyle

- Skill order: max **Q** → E → W. Cougar ranks with R (6 / 11 / 16).
- Short spears that land beat max-range spears that miss.
- Do not rush Lich Bane if you refuse to auto.
