# Dr. Mundo Jungle — Wild Rift 7.3

Patch **7.3** jungle. Smite's monster burn scales with bonus health, armor, and magic resist, and the patch called out Sunfire as something tanks should no longer need just to clear.

Full clear is red → krugs → raptors → wolves → blue → gromp, then an 8-second dragon fight while two champions focus Mundo. Game length **22 minutes**.

## Run

```bash
python3 simulate_mundo_jungle.py
```

Outputs:

- `report.txt` — clear times, burn on/off, dragon fight, buy order
- `results.json` — minute-by-minute snapshots per build

## Question answered

After the 7.3 Smite burn, does jungle Mundo still need **Sunfire Aegis before Heartsteel**?

## Winner (sim)

**Heartsteel → Plated Steelcaps → Warmog's Armor → Thornmail**

Bami's on the first back saves **1.5s** of krugs/raptors/wolves. The same camps without the burn are **14s** slower with no immolate. Sunfire is no longer the clear item.

| When | Spike |
|------|--------|
| ~4:00 | Giant's Belt. The burn already ticks. Do not buy Bami's. |
| ~7:00 | **Heartsteel** — 700 HP, the proc, and the stack that feeds E / W / R / the burn |
| ~10:00 | Plated Steelcaps |
| ~16:00 | **Warmog's Armor** — 30% healing amp (Spirit Visage is gone) plus the out-of-combat reset |

At 8:00 the Sunfire-first path is still on components: **1512** damage and **9.8s** survived, versus **1642** and **11.2s** on Heartsteel. Heartsteel on that path does not finish until ~16:00, and by then the proc stacks are **66 HP** versus **470**.

## Second item

Warmog and Mantle of the Twelfth Hour are the same spike at 16:00 (+33 damage, +0.2s for Warmog). Take Mantle when one burst rotation is what kills you. Finish Sunfire second only if fights are a pile of melees.

## Playstyle

- Skill order: max **Q** (monster cap) → **E** (bonus HP) → **W** (heal). R at 6 / 11 / 15.
- Proc Heartsteel on scuttle and the first dragon. That is the point of the rush.
- The burn tick interval is not printed in the 7.3 notes. This sim uses one true-damage tick per second on the monster you are autoing. A slower live tick would give Bami's some of its old clear job back.
