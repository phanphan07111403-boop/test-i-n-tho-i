# Smolder — crit scale vs ability scale

PC League of Legends, patch **26.19**. Even bot-lane gold over **28 minutes**. Essence Reaver first on every path. Deathfire Touch on every path.

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

## What the spikes say

**225 stacks** (the percent-health burn and the execute): ability **23:00**, Shojin-into-IE **25:00**, crit **27:00**. Pinning everyone to the same stack count barely moves tank damage. Haste gets the burn online earlier. After that, the crit multiplier and penetration are the damage.

**Poke** (Q only) belongs to haste as soon as Cleaver or Shojin exists. At 28:00 ability poke is 3135 vs crit 2161. Finished, with Serylda, ability poke is **3941** vs crit **2648**.

**Kite** (Q, autos, one W) belongs to IE once you are allowed to stand still. At 22:00 crit kite-on-squishy is **3926** vs ability 2969 (+32%). At 28:00, before Bloodthirster, Cleaver → IE → LDR leads both kite columns because it has shred and crit does not have the 80 AD yet, and it has no RFC so that lead is at 550 range. After the last buy, Bloodthirster crit kite-squishy is **7977** vs Cleaver hybrid **7554**, and tank kite is **6429** vs **6351**. Crit's dive uptime on that same burst is **71%** vs the hybrid's **83%** and ability's **97%**.

**Navori** refunds cooldown per auto. In the 28:00 window both crit paths throw 3 Qs, so Navori's lead there is attack speed. The finished Navori path does get a 4th Q and still loses the kite to Bloodthirster's AD (7575 vs 7977). It does not replace Shojin, and it does not give health.

**RFC** is a range item. The energized Q reaches 700. That range is not in the damage. It is how the crit path makes the dive miss.

## Assumptions that move the answer

Q crit is a ratio. Stack magic is not multiplied by that ratio a second time. Shojin amps abilities, including the 225 burn, and does not amp autos, spellblade, or Deathfire Touch. After 25 stacks, Q is treated as an AoE for Deathfire (2 second burn), so a Q under 2 seconds keeps the burn up. The dive is a growing physical-plus-magic burst, not a champion. E and Flash are not modeled as dodges. No Gathering Storm, no Jack of All Trades, no adaptive shards.
