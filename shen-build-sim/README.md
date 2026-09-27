# Shen Baron — farm, then 1v1, then tank

Patch **7.3**. Heartsteel first is out: no wave tool, the game stalls.

Constraint: **1st farms**, **2nd 1v1s**, **rest tanks for 1v9**.

## Run

```bash
python3 shen-build-sim/simulate_shen_build.py
```

## Winner

**Titanic Hydra → Dusk and Dawn → Dawnshroud → Unending Despair**

| Slot | Item | Job |
|------|------|-----|
| Start | Ruby Crystal | |
| First back | **Bami's Cinder** | Farm starts now, before the legendary |
| **1st** | **Titanic Hydra** (3000) | Q + cleave deletes the wave. Cannon wave ~86% in 4s in the sim. |
| Boots | Plated Steelcaps | Mercury's vs AP/CC |
| **2nd** | **Dusk and Dawn** (3100) | Extra on-hit on Q’s 3 autos. This is the 1v1. |
| **3rd** | **Dawnshroud** | Taunt proc, armor/MR |
| **4th** | **Unending Despair** | 1v9 pulse heal (default) |
| **5th** | Twinguard / Thornmail / FoN | Extra tank if the game lasts |
| Enchant | Stoneplate | |

Do **not** buy Heartsteel. Do **not** rush Dusk first (49% wave vs Titanic’s 86%).

## Why this split

Heartsteel is 700 HP and a delayed proc. It does not hit the wave. In the sim a first-item Heartsteel clears **35%** of a cannon wave in 4s. Titanic clears **86%**. That is the “game too slow” feeling.

Dusk stays **2nd**, not 1st: same Q sheen 1v1 as before, after you already shove.

3rd+ is tank. You already spent two items on farm and the duel; the rest is so you can 1v9 after R.

## Rank (constraint fit)

| Path | Farm 8:00 | 1v1 mix 16:00 | Tank ehp 26:00 |
|------|-----------|---------------|----------------|
| **Titanic → Dusk → Despair** | **86%** | **1458** | **5894** |
| Titanic → Dusk → Twinguard | 86% | 1458 | 5700 |
| Hollow → Dusk → tank | 79% | 1372 | 5561 |
| Sunfire → Titanic → tank | 78% | 1342 | 5700 |
| Sunfire → Dusk → tank | 78% | 1365 | 5562 |
| CN 62% WR (Heartsteel first, skip) | 35% | 1308 | 6196 |
| Heart → Sunfire → Dawn (61% WR, skip) | 35% | 1308 | 6225 |

## vs China 62% WR

The ranked king on wrchina.gg (patch **7.3**, stats **2026-09-26**) is **Heartsteel → Sunfire Aegis → Thornmail** at **62.3% WR / 25% use**. Next cores: Heartsteel → Sunfire → Dawnshroud (**61.3%**, 6% use) and Heartsteel → Sunfire → Titanic (**59.5%**, 6% use). Top-30 screenshots: Heartsteel 85%, Sunfire 73%, Thornmail 58%, Twinguard 46%. Full 4th is Twinguard.

That is a **different job**. 62% WR is “hold the side, R, peel, anti-heal.” This build is “farm, 1v1, 1v9.” Heartsteel first is why the CN path feels slow.

| Aspect | This build Titanic → Dusk → Dawnshroud → Despair | CN 62% Heartsteel → Sunfire → Thornmail → Twinguard | Edge |
|--------|--------------------------------------------------|-----------------------------------------------------|------|
| **Lane shove 8:00** | Cannon wave **86%** in 4s (Titanic) | **35%** (Heartsteel does not hit the wave) | **this** |
| **Lane 3s trade damage** | 728 (Q + cleave now) | 657 (Heartsteel’s 2.5s charge often misses a short trade) | **this** |
| **Lane 3s HP** | 2072 | **2378** (700 HP item) | CN |
| **Solo 1v1 damage 16:00** | **1458** (Dusk sheen on Q) | 1308 (Heartsteel + Sunfire, +~224 stacks) | **this** |
| **Solo 1v1 ehp 16:00** | 4080 | **4696** | CN |
| **Teamfight AoE 26:00** | **2804** (Despair pulses + Titanic cone on 3) | 2097 (Sunfire ticks) | **this** |
| **Teamfight tank (mitigated ehp)** | 16443 | **18053** (Twinguard + Thorn armor + HS stacks) | CN |
| **R ally shield 26:00** | 830 (Dusk **70 AP** + 135% AP) | 849 (Heartsteel HP + 15% bonus HP, **560** stacks) | **tie** |
| **1v9 split damage / ehp** | **1783** dmg / 5894 ehp | 1634 dmg / **6196** ehp | split |
| **Anti-heal** | no | **Thornmail 50% grievous** | CN |
| **Ranked WR (CN)** | untracked | **62.3%** | CN |

How to read it:

- **Laning.** This build owns the wave and the short trade. CN owns not dying. If they freeze, you cannot crash. If you crash, they cannot match the shove, so your R is free.
- **Solo / side 1v1.** You **kill** more (Dusk). They **live** more (Heartsteel + Sunfire). Strength (mix + 0.85×ehp) still leans CN because 700 HP outweighs ~150 extra mix. For a GameSir “easy 1v1,” take this build. For “stall until R,” take CN.
- **Teamfight.** You do more AoE in a long 3-man brawl (Despair). They are the better peel tank (resists, Thornmail into AD). Shen’s ranked win condition is peel + R, which is why CN posts 62%.
- **R.** Almost the same shield. Dusk’s AP and Heartsteel’s HP cancel (~830 vs 849).
- **1v9.** Despair heals you in a long fight; CN is slightly fatter after stacks. Damage still this build.

Copy CN only if you want the 62% WR playstyle and accept the slow lane. Do not mix them: **Titanic + Heartsteel** wastes the first two slots on different jobs.

## Swaps

- **AP lane:** Hollow Radiance 1st, Force of Nature later.
- **Safer/cheaper farm:** Sunfire 1st (still Bami’s), Dusk 2nd, same tank rest.
- They heal: Thornmail in the tank slots.
- Crit AD: Randuin instead of Twinguard.
- **Unending Despair:** yes as a **4th** tank item, not 1st/2nd. See below.

## Unending Despair — buy or skip?

**Buy it 4th** if the 1v9 is a long fight. Skip it 1st/2nd (it does not farm, it is not the Q sheen). Do not use it *instead of* Dawnshroud 3rd — you still want the taunt proc.

Every 4s in combat: 3% max HP magic to nearby champs, heal **250%** of that (7.5% of your max HP per pulse). Two pulses in an 8s brawl is a lot of HP back. That is the 1v9 item. Dual 40 armor / 40 MR also covers mixed damage.

| 4th item | Take when |
|----------|-----------|
| **Unending Despair** | Fights last. You walk into 2–3 people and outlive them. Default 1v9 4th. |
| **Twinguard** | They burst/crit/CC you in the first 3s (Twinguard’s +30% resists + tenacity need 5s to stack). |
| **Thornmail** | They heal. |
| **Force of Nature** | They are AP. |

If the game goes long: Dawnshroud → Despair → Twinguard. If you only get one more slot after Dawnshroud, **Despair** for 1v9, Twinguard for burst.

## Runes

Grasp, **Courage of the Colossus**, Second Wind, Overgrowth, Sudden Impact, Legend: Tenacity. Flash + Ignite (Teleport if you live on R). Max **Q > E > W**.

**Colossus, not Unshakeable**, with Dawnshroud + Twinguard. Those two items already dump % armor/MR (Dawnshroud +20% on taunt, Twinguard +30% after 5s in combat). Unshakeable is another 3–9% resists plus 20% slow resist at 3 nearby champs — mostly the same stat, and it was nerfed in 7.2. Colossus is a **shield** on the same E taunt that procs Dawnshroud (25–45 + 1% max HP, 18s CD). That is extra HP, not more stacked resists.

Take Unshakeable only if the 1v9 problem is **slows** (Ashe, Frozen Heart, Nasus W) and you need the slow resist. Twinguard tenacity does not replace that.
