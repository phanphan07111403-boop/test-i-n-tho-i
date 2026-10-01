# Smolder — crit scale vs ability scale

PC League of Legends, patch **26.19**. Even bot-lane gold over **28 minutes**. Deathfire Touch on every path. Essence Reaver is first on the five comparison paths. Trinity is a separate path: Tear first, then Trinity Force.

## Run

```bash
python3 simulate_smolder.py
```

Outputs:
- `report.txt` — stack timing, an 8-second fight at each spike, the finished build, and when to pick which
- `results.json` — the same rows, per minute

## What the two scales actually are

Infinity Edge is ability scaling. Q is not a crit roll. Crit chance multiplies the fireball, up to **1.75×** at 100% crit, and IE's 30% crit-damage stat multiplies that bonus to **1.975×**. The same stat makes autos crit for 230% instead of 200%. Dragon Practice magic on Q also grows with crit (25% of stacks at 0 crit, 55% at 100%, 64% with IE).

Ability haste does not touch that multiplier. It shortens Q, which is the damage spell and the stack spell. Shojin adds 25 basic-ability haste and up to **+12%** ability damage. Cleaver shreds armor for you and for every other AD champion. Health and a shorter E are why the path exists.

## When to choose which

| Situation | Buy |
|-----------|-----|
| You can auto, and you need 700 range | **Crit.** ER → Berserker's → IE → RFC → LDR. IE is in at 17:00 and squishy kite jumps **+29%** over Cleaver. |
| You will only throw Q | **Haste, then IE.** Do not buy RFC to poke. At 22:00 Shojin → IE has the best poke of the five paths. |
| An assassin or engage will touch you | **Shojin or Cleaver before IE.** At 22:00 ability health is 2805 vs crit 1955. If the dive lands, uptime is 100% vs 70%, and messy damage flips to the health build. |
| Tanks, and your team is AD | **Cleaver, then IE and LDR.** Carve is about **+27%** physical damage for allies. Do not stop on Shojin. |
| Tanks, and you are the only AD | **LDR.** Cleaver's team amp has nobody to amplify. |
| The fight comes to you and you will outscale it | **Shojin second, IE third.** You give up the 17:00 crit spike. E is back in 14.7s instead of 18.3s. |
| 100% crit already | Stop buying crit. Another cloak does not scale Q. Bloodthirster's AD does. |
| The Collector | Skip it. The execute is already 6.5% max health. |
| You want the 9:00 spike and you are not going crit | **Trinity.** Tear → Trinity → Ionian → Manamune → Serylda → Shojin. See below. |
| The game goes long, or the team is AD | **Essence Reaver → Cleaver.** Finished poke is 3941 vs Trinity 2909, and Cleaver shreds for allies. |

## Trinity, Manamune, Serylda, Shojin

Buy Tear on the first back. Trinity is still the first completed legendary. Muramana needs 360 bonus mana, and that clock only runs while Tear is in the inventory.

| Minute | Completed |
|--------|-----------|
| 01:00 | Tear of the Goddess |
| 09:00 | Trinity Force |
| 11:00 | Ionian Boots of Lucidity |
| 16:00 | Manamune, which is already Muramana (Tear hit 360 first) |
| 19:00 | Last Whisper (18% pen while Serylda is unfinished) |
| 21:00 | Serylda's Grudge |
| 26:00 | Spear of Shojin |

Component order:

1. Doran's Blade
2. Tear of the Goddess
3. Glowing Mote → Sheen
4. Ruby Crystal + Long Sword → Phage
5. Long Sword + Dagger + Long Sword → Hearthbound Axe → Trinity Force
6. Boots + Glowing Mote → Ionian Boots of Lucidity
7. Two Long Swords + Glowing Mote → Caulfield's Warhammer, then a Long Sword → Manamune
8. Two Long Swords → Last Whisper
9. Two Long Swords + Glowing Mote → Caulfield's Warhammer → Serylda's Grudge
10. Long Sword + Ruby Crystal → Tunneler, then Pickaxe + Ruby Crystal → Spear of Shojin

If the dive is already landing, buy Shojin before Serylda. Penetration does not add health.

This path has 0% crit, so Q stays at 1.00×. Trinity's spellblade is 200% base AD. Muramana Shock on Q is 3% max mana, because Q is a spell and an on-hit in the same instance. Shock is not amplified by Shojin.

At 11:00, with Trinity and Ionian, squishy kite is **1592** vs the Essence Reaver ability path **1249** (+27%) and vs crit **1692** (−6%). Health is 1588 vs 1405 vs 1255. That is the window: before Infinity Edge exists.

Muramana's minute (16:00), poke is **1170** vs ability 1113 (+5%) and vs crit 899 (+30%). Squishy kite is 2069, level with ability (2092) and behind crit (2280).

At 22:00 Serylda is in and Shojin is not. Poke is **1567** vs ability 1343 (+17%). Squishy kite is 3095 vs ability 2969 vs crit **3926**. Health is 2438 vs ability 2805, because that path already has Shojin.

At 28:00 the core is finished. Poke 2985 vs ability 3135. Squishy kite 4534 vs ability 4849 vs crit 6418. Tank kite 3780 vs 4134 vs 5141. Dive uptime is 98%.

Finished, stacks pinned at 250, Trinity poke is **2909** vs ability **3941**, kite-squishy **4413**, kite-tank **3669**. Essence Reaver's 25% crit still multiplies Q, and Cleaver shreds. Crit's finished kite is **7977**.

## What the spikes say

**225 stacks** (the percent-health burn and the execute): ability **23:00**, Shojin-into-IE **25:00**, crit **27:00**. Pinning everyone to the same stack count barely moves tank damage. Haste gets the burn online earlier. After that, the crit multiplier and penetration are the damage.

**Poke** (Q only) belongs to haste as soon as Cleaver or Shojin exists. At 28:00 ability poke is 3135 vs crit 2161. Finished, with Serylda, ability poke is **3941** vs crit **2648**.

**Kite** (Q, autos, one W) belongs to IE once you are allowed to stand still. At 22:00 crit kite-on-squishy is **3926** vs ability 2969 (+32%). At 28:00, before Bloodthirster, Cleaver → IE → LDR leads both kite columns because it has shred and crit does not have the 80 AD yet, and it has no RFC so that lead is at 550 range. After the last buy, Bloodthirster crit kite-squishy is **7977** vs Cleaver hybrid **7554**, and tank kite is **6429** vs **6351**. Crit's dive uptime on that same burst is **71%** vs the hybrid's **83%** and ability's **97%**.

**Navori** refunds cooldown per auto. In the 28:00 window both crit paths throw 3 Qs, so Navori's lead there is attack speed. The finished Navori path does get a 4th Q and still loses the kite to Bloodthirster's AD (7575 vs 7977). It does not replace Shojin, and it does not give health.

**RFC** is a range item. The energized Q reaches 700. That range is not in the damage. It is how the crit path makes the dive miss.

## Assumptions that move the answer

Q crit is a ratio. Stack magic is not multiplied by that ratio a second time. Shojin amps abilities, including the 225 burn, and does not amp autos, spellblade, Deathfire Touch, or Muramana Shock. Trinity spellblade is 200% base AD and does not restore mana. Tear gains 27 bonus mana a minute, cap 360, and the cast rate while holding Tear is 90% of Essence Reaver's. After 25 stacks, Q is treated as an AoE for Deathfire (2 second burn), so a Q under 2 seconds keeps the burn up. The dive is a growing physical-plus-magic burst, not a champion. E and Flash are not modeled as dodges. No Gathering Storm, no Jack of All Trades, no adaptive shards.
