# GameSir X3 Pro — Wild Rift duelist pick

Patch **7.3** (Sep 2026). Overlay-mapped X3 Pro (Wild Rift has **no native gamepad API**).

## Run

```bash
python3 gamesir-x3-duelist/rank_gamesir_duelist.py
```

Outputs `report.txt` + `results.json`.

## Question answered

Which Wild Rift champ is **strong in easy 1v1s**, **hard to kill**, and **fits a GameSir X3 Pro** (hall analog sticks, face buttons, cooling fan, mapping overlay)?

## Winner

**Volibear** — Baron lane (Jungle works).

| Check | Why Volibear |
|--------|----------------|
| Easy 1v1 | Q stun is "stick toward them, then auto". W bite is targeted. Combo is 4 buttons. |
| Hard to kill | Second W heals, E is a fat shield if you stand in it, R disables the tower so dives do not delete you. Heartsteel / Trinity keeps the slugfest going. |
| X3 Pro | Left stick is the actual skill (chase). W auto-targets. E can be bound on-feet. No 3-cast Q, no parry, no minion-Q. Fan helps because fights last. |

Ranked signal: Baron **~54.4% WR**, S+ on wildriftmeta 7.3.

## Rank (weighted)

1v1 **35%** / unkillable **35%** / controller **30%**.

| Rk | Champ | 1v1 | Tank | Pad | Tot |
|----|--------|-----|------|-----|-----|
| 1 | **Volibear** | 9.2 | 9.1 | 9.4 | **9.22** |
| 2 | Warwick | 8.3 | 8.4 | 8.6 | 8.43 |
| 3 | Garen | 8.1 | 7.4 | 9.8 | 8.36 |
| 4 | Sett | 8.4 | 8.8 | 7.2 | 8.18 |
| 5 | Mordekaiser | 9.0 | 8.3 | 7.0 | 8.15 |

Warwick is #2 on raw score (targeted Q heal + analog chase) but he is a **jungle** pick and 7.2c added ~20s to his ult CD. Garen is the **Baron backup** if Volibear is banned. Full table is in `report.txt`.

## X3 Pro mapping (Volibear)

| Control | Action |
|---------|--------|
| Left stick | Move (make the overlay joystick large) |
| A | Q — Thundering Smash |
| B | W — Frenzied Maul (auto-target champions) |
| X | E — Sky Splitter (see **How to set E on feet** below) |
| Y | R — Stormbringer |
| RB | Attack |
| RT / LT | Flash / Ignite |
| LB | Recall |
| Right stick | Aim E/R, or pull toward screen center for on-feet E |

Shop, pings, and camera still need a thumb on the glass.

## How to set E on feet

Wild Rift has **no** “cast on self” toggle. Sky Splitter is a ground circle. A **tap** of E auto-aims at the locked / nearest enemy, not at Volibear.

You still get the shield from a tap if you are **already in melee** (the bolt is on them, the circle is big, you are inside it). Use a real on-feet cast when you want the shield **before** you walk in.

1. Wild Rift → Settings → Controls: **camera Locked**. You stay in the middle of the screen.
2. Leave skill 3 (E) on **Joystick** aim. Do not lock the skill button.

**One-button (GameSir overlay)**

1. In-game, open the GameSir floating mapper.
2. Tap the **X** bubble → ⚙️.
3. Use **Gesture Mode** (best) or **One-button Macro**:
   - Touch down on the **E HUD button** (bottom right).
   - Swipe **toward the center of the phone** (onto Volibear).
   - Release.
4. Save this as a **Volibear** config. Do not reuse it on champs whose 3rd skill is not a ground circle.

**Right stick (Wheel Mode)**

1. Same ⚙️ on X → **Wheel Mode**, bind to **Right Stick**.
2. Hold X, pull the right stick **left / toward the middle of the screen**, release when the circle sits on Volibear.

**Finger check (practice tool)**

Press E, drag the circle onto your model (toward screen center), let go. That is the same swipe the mapper is faking.

Do **not** map X as a plain tap if you wanted on-feet. Plain tap = bolt on the enemy.

## 1v1 combo

**E (shield on feet) → Q (run) → auto (stun) → W → auto (empowered heal).**

R when they hide under tower. The turret is off for a few seconds; you are not.

Max **W > Q > E**. Grasp or Lethal Tempo. Flash + Ignite.

Core Baron path: **Dusk and Dawn → Plated Steelcaps → Hullbreaker → Riftmaker → Unending Despair**. Full buy order in `volibear-build-sim/`.

## If Volibear is banned / bad

- **Garen** — even fewer buttons (spin does not aim). Weaker in-fight heal.
- **Sett** — same "eat damage, punch back" job; you must aim W center and R throw.
- **Mordekaiser** — closest to a *forced* 1v1 (R island). E pull is a skillshot on overlay.

Skip **Fiora / Aatrox / Irelia** on this pad: parry windows, 3-cast Qs, and minion targeting fight the overlay.

## Skip Volibear when

The enemy is **Vayne** or a kite-and-disengage draft that never lets you land the second bite. Then Garen (simpler) or a ranged blind is the honest pick.
