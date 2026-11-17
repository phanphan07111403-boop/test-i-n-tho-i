# Fiora Baron — Split Push vs the Tank Meta

Wild Rift patch **7.3f**. Baron lane is Malphite, Shen, Cho'Gath, Ornn, K'Sante, Dr. Mundo, plus Mordekaiser and a blind (Teemo) or a ranged answer (Kalista). Fiora is the split pusher whose passive is true damage off their max health.

## Run

```bash
python3 simulate_fiora_split.py
```

Outputs:

- `report.txt` — minute-by-minute score, build table, verdict
- `results.json` — snapshots per build

## Question answered

Which item path kills the champion who matches the side wave, and still takes the turret?

Runes are the same on every row: Grasp, Demolish, Second Wind, Overgrowth, Sudden Impact, Flash + Teleport. Skill order is Q, then E, then W. R at 5 / 9 / 13.

## Winner (sim)

**Manamune → Trinity Force → Hullbreaker → Spear of Shojin → Death's Dance**

Plated Steelcaps.

| When | Spike |
|------|--------|
| ~6:00 | **Manamune** — the lane is still behind |
| ~8:00 | **Steelcaps** |
| ~14:00 | **Trinity Force** — Muramana is charged, Spellblade is 200% base AD |
| ~18:00 | **Hullbreaker** — the crash from here through 22:00 is the win |
| ~22:00 | **Spear of Shojin** — +20 basic haste, vitals and Q amp up to 12% |
| ~26:00 | **Death's Dance** |

Late-weighted split score **3543**. Runner-up is Trinity → Hull second → Eclipse → Death's Dance → Shojin at **3422** (about 3.5% back). The popular Eclipse → Trinity → Hull core is **3420**.

At **22:00** this path is 332 AD and 3915 HP. The tank loses **126%** of effective HP in the ultimate, **2829** of it true damage from vitals. Mordekaiser loses **153%**. The crash is **8886** turret damage and the cannon wave takes **8.9s**.

## What the other lines do

- **Sunderer → Cleaver → Hull** leads at **8:00** (1937 vs 1745) on the 10% max-HP Spellblade. At **22:00** the duel is tied (4470 vs 4528) and the turret trails (6904 vs 8886). 25 AD feeds a smaller vital, and structures take half the proc. Trinity is the split Spellblade.
- **Hull second** on a Trinity start is the **14:00** turret spike: 6031 raw turret damage vs 4676 on the Eclipse-first core. From 18:00 those two inventories match until the fifth item.
- **Eclipse → Trinity → BotRK → Hull → Serylda** wins the **26:00** minute (5964 vs 5638). Pen and BotRK are online and Hull has just arrived. Across 18:00–22:00 the earlier Hull is ahead, so the late average stays with Manamune.
- **BotRK → Cleaver → Serylda** (no Hull) has the highest champion damage at 26:00 (173 / 207 / 340 percent of tank / Morde / blind) and a smaller turret (8885 vs 11084 on the Hull + pen finish).
- **Trinity → Manamune → Maw → Death's Dance → Bloodthirster** has the most AD (407 at 26:00) and the fastest wave (7.7s). There is no Hull, so the turret at 22:00 is 7080 vs 8886.
- **Trinity → Death's Dance → Sterak → Goredrinker → Guardian Angel** is the lowest turret (7146 at 26:00). She was already going to live the 1v1.

Every finished build ends the Mordekaiser all-in at full HP. The ultimate heal (80 / 110 / 140 + 60% bonus AD per second, longer as vitals land) covers his damage when the sides are hit. Maw's resist does not change who crashes.

## Why

- A vital is **3.5% + 5.5% per 100 bonus AD** of their max health, as true damage. Four of those are the ultimate. Awe on Muramana is bonus AD, which is the stat the vital reads. Percent armor pen multiplies Q, autos, Spellblade, and BotRK.
- Eclipse (7.3f) is 60 AD, 20 haste, 7% max HP, and a shield of 150 + 40% bonus AD. It is the high-pick first item, and that core finishes within about 3.5% of the Manamune line.
- Hullbreaker on a turret is 240% base AD + 9% of your max HP every fourth auto, and the crash is one second longer. On a champion it is 160% base AD + 5% of your max HP.
- Q is single target, including the wave. Haste and attack speed are the clear.
- Steelcaps are on every row (25 armor, 150 HP, 10% less from champion autos). Gluttonous is the popular 1000g boot.

## Playstyle

- Teleport to the side wave your team is not fighting. Crash it, ultimate the one champion who matches, auto the turret.
- Two champions on the wave ends the crash. Riposte parries one spell (Malphite ult, Shen taunt, Ornn knockup, Mordekaiser pull), then leave.
- The first eight minutes on Manamune are the weak point. Sunderer or Trinity is ahead until the tear charge becomes bonus AD. Into a lane you cannot touch the wave in, start Trinity and buy Hull second.
- Into Dr. Mundo specifically, buy Executioner's. The tank in this sim heals at the average of that class, and Mundo heals harder than the average.

## Assumptions

The duel is one ultimate in which the vitals are hit: four against a melee, three against the blind. Autos and on-hits are cut to 60% while blinded. There is no extra flat percent-health hit for popping all four; the four vitals are the payoff. Riposte parries the tank's engage, and the incoming damage is what they do after that. Sunderer's structure hit is half of a max-health proc against a 4000 HP turret. Manamune's +700 mana takes about five minutes of lane time; Shock starts when that charge completes.
