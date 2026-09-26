# Braum support — full build + runes (Wild Rift 7.3)

Patch **7.3**. Bodyguard support over a **20-minute** average game.

## Run

```bash
python3 simulate_braum_73.py
python3 test_braum_73.py
```

Outputs:
- `report.txt` — minute-by-minute item path, then rune pages on the winner
- `results.json` — snapshots per build / page

## Question answered

On 7.3, which **item path and legal rune page** peak peel for Braum support?

7.3 reworked **Yordle Trap**: Catcher now procs on **slow or immobilize**. Winter's Bite (70% slow) lights it — R is no longer required. Aftershock is gone (**Ice Overlord**). **Guardian** is the bodyguard keystone.

Rune loadout: **1 keystone + 3 primary + 1 secondary**. Ingenious Hunter is gone.

## Winner (sim)

**Locket → Radiant Virtue → Knight's Vow**

**Guardian · Font of Life · Second Wind · Overgrowth · Transcendence**

Skill order: max **Q**, one early **W**, then **E**. R at **5 / 9 / 13**. Spells: **Flash + Heal**.

| When | Spike |
|------|--------|
| ~5:00 | Bulwark of the Mountain |
| ~9:00 | **Locket** — team shield, no R required |
| ~10:00 | Plated Steelcaps |
| ~16:00 | **Radiant Virtue** — R heal (Transcend + 2.5% max HP/s) |
| 20:00 | Vow sits as Kindlegem; third legendary rarely finishes |

At 12:00 this path is **~40% more peel** than a Yordle rush. At 16:00 it is **~36% more peel**. Live Diamond+ Vow → Warmog is **~26% less peel** at 16:00 — Warmog tanks you, it does not shield the ADC.

## Full build

1. Relic Shield → Bulwark of the Mountain
2. Plated Steelcaps (Mercury's Treads vs AP/CC)
3. Locket of the Iron Solari (~9:00)
4. Radiant Virtue (~16:00)
5. Knight's Vow if the game lasts
6. Frozen Heart vs AS / Thornmail vs healing / Force of Nature vs AP / Randuin vs crit / Kaenic vs mages

Do not rush Armored Advance — 2200g delays item 2.

## Runes

**Guardian · Font of Life · Second Wind · Overgrowth · Transcendence**

Font + Bone Plating + Overgrowth ties the peel number. Second Wind vs poke, Bone Plating vs melee burst.

- Unshakeable instead of Font in 5-man clumps.
- Perseverance instead of Overgrowth vs heavy CC (live WRF page, ~8 peel behind).
- Ice Overlord if you engage (stun/R) more than you bodyguard.
- Grasp is a top-lane trade keystone — it does not save the ADC.

## Why

- Guardian shields you **and** the ADC while you W-glue. That is the kit.
- Font of Life procs on Q. Second Wind heals the poke you eat with E (melee doubled). Overgrowth is the extra HP.
- Transcendence is extra Q/E → extra Concussive Blows stuns.
- Locket is the team shield with no R gate. Virtue is the R heal and no longer shares Vow's Kindlegem + Chain Vest cart.
- Knight's Vow is the 12% redirect — third legendary, not the rush.
- Yordle is **legal on Q** in 7.3, but it shares the Locket/Zeke cart. 30% ally AS is enable, not a shield.
- Frozen Heart is a **25% AS aura**, not Chill stacks.
- 20-min support gold finishes **two** legendaries + boots. The 6-item list is the if-the-game-lasts tree.
