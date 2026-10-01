# Volibear Baron — W-spam heal / shield

Patch **7.3**. 12-second slugfest vs a bruiser. Sit at ~38% HP (the bite band).

This is **not** the Dusk → Hull → Rift 1v1 page. That sim asks who wins a mix fight. This one asks which shop and rune page feed **Frenzied Maul on cooldown**, the missing-HP heal, and the Sky Splitter shield.

Spirit Visage was **removed in 7.0**. Heal amp is Revitalize. The combat heal is Unending Despair. The panic shield is Sterak.

## Run

```bash
python3 volibear-wspam-sim/simulate_volibear_wspam.py
python3 volibear-wspam-sim/test_volibear_wspam.py
```

Outputs `report.txt` + `results.json`.

## Question answered

Spam W, heal, shield. Which buy order actually does that over a 22-minute Baron gold curve?

## Winner (sim)

**Heartsteel → Hỏa Ngọc (Kindlegem) → Plated Steelcaps → Sterak's Gage → Unending Despair**

| When | Spike |
|------|--------|
| ~6:00 | **Heartsteel** — E is 14% max HP; empowered W is 10.4% bonus HP |
| ~11:00 | **Hỏa Ngọc (Kindlegem)** — 30 AH is the 4th W / 3rd bite in 12s |
| ~17:00 | **Sterak** — Lifeline = 75% bonus HP. This is the mid-game shield |
| ~21:00 | **Unending Despair** — 3% max HP every 4s, heal 250% of it |

**Runes:** Grasp · Second Wind · Revitalize · Overgrowth · Last Stand  
**Spells:** Flash + Ignite  
**Skill:** max W, one E, then Q. R at 5 / 9 / 13.

At 14:00 this path is **4 W / 3 bites**, sustain **1916** vs Dusk → Hull → Rift **1352**. At 22:00 **6869** vs **2492**.

## How to play it

1. Max W. First W on a champion starts Frenzy (8s). Do not swap targets.
2. Every later W is the bite: more damage, the missing-HP heal.
3. Press W the instant it is up. The heal **is** the cooldown.
4. Drop E on your feet before the stun. Stand in the bolt for the shield.
5. Q to stick after E is placed, not as the opener.
6. R for the bonus HP (feeds E and W) and the turret disable.

## Where to buy Hỏa Ngọc (Kindlegem)

It is **not a finished item**. Sterak does not use it, so Volibear **Recommended will not show it**.

- **Tốc Chiến:** search **Hỏa Ngọc**. English client: search **Kindlegem**.
- Or open **Thất Vọng Bất Tận** (Unending Despair) / **Giáp Tim Thép** (Heartsteel) / Black Cleaver and tap the HP + 10 haste component.
- Recipe: **Hồng Ngọc / Ruby Crystal 500 + 500 = 1000**. Stats: +175 HP, +10 AH. Shop tabs: Defense / Support.
- Heartsteel already ate the first one. Buy a **second** Hỏa Ngọc after Heartsteel.

Cannot find it? Skip the leftover and go **Despair second** instead — that tree is how you buy Hỏa Ngọc anyway.

## Why this order

A 12s fight wants a 4th W. That needs **~28 AH**. Heartsteel is 20. Hỏa Ngọc's 10 AH is the extra bite ~6 minutes before Sterak finishes.

Sterak second — not Despair, not Trinity — because Hỏa Ngọc already bought cadence. Sterak's unique (Lifeline) is the 18–20 minute game. Despair's unique (the pulse) often never finishes as a 3rd.

| 2nd item | Online | What you get | What you miss |
|----------|--------|--------------|---------------|
| **Sterak** | ~17:00 | Panic shield | Pulse until ~21:00 |
| Despair | ~15:00 | 4s heal ticks | Lifeline until ~21:00 |
| Trinity | ~17:00 | Sheen / AD / AS | Both sustain items |

Despair second is the **heal-off fork** (they cannot burst you). Trinity is the 1v1 item — do not buy it here.

Fimbulwinter looks good until ~14:00. Heartsteel stacks + Hỏa Ngọc bites bury it. Do not start Tear.

## Runes on this shop

Legal 7.3 pages (3 in the keystone tree + 1 secondary):

| Page | Why |
|------|-----|
| **Grasp / Revitalize / Overgrowth / Last Stand** | Default. HSP + HP for E and the bite. Second Wind doubled as melee. |
| Grasp / Revitalize / Colossus | Q stun shield instead of Overgrowth HP. Slightly worse. |
| Conqueror / Bloodline / Revitalize | W damage → omnivamp. Close, still behind Grasp. |
| Lethal Tempo / Alacrity | Other sim's 1v1 page. Extra autos, **0 HSP**. |

Last Stand, not Cut Down: you live at ~38% HP.

## Full 6 if the game lasts

Heartsteel · Steelcaps · Sterak · Despair · Twinguard · then Thornmail / Kaenic / Frozen Heart.

Enchant: **Stoneplate**.
