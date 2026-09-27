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

Skill order still **W > Q > E**. Flash + Ignite.

## Runes (this Dusk / Hull / Rift page)

Lethal Tempo is the keystone that matches the items: Dusk extra on-hit, lightning, and Hullbreaker Skipper all want more autos in the 1v1.

| Slot | Take | Why |
|------|------|-----|
| Keystone | **Lethal Tempo** | AS stacks feed Skipper (4th auto), Dusk sheen weaving, and 5-stack lightning. |
| Precision | **Brutal** | Flat adaptive on every auto. |
| Precision | **Legend: Alacrity** | More AS on the same page. |
| Precision | **Last Stand** | You sit at ~45% HP in the W-heal 1v1. **Cut Down** (old Giant Slayer) if you stay full vs tanks. **Coup de Grace** only if they are already execute food. |
| Resolve | **Second Wind** | Lane sustain between Q bites. |
| Resolve | **Overgrowth** | Free HP for W heal and Riftmaker's AP-from-HP. |

**Flash + Ignite.** Stoneplate enchant.

Swap keystone to **Grasp** only into poke/range (Teemo, Kennen, Vayne) where you never stack Tempo. Then: Unshakeable, Second Wind, Overgrowth, Brutal, Last Stand.

Do not take Aftershock — Volibear is not a one-taunt tank. Do not take Conqueror if you already bought Dusk; Tempo is the AS item page.

## Lethal Tempo vs Grasp

Patch **7.3** reworked Lethal Tempo: **8% AS per auto**, 6 stacks, then adaptive **bullets** (9–30 melee, +1% dmg per 1% bonus AS). **No more bonus range.** Tempo page includes **Legend: Alacrity**. Grasp page does not.

Grasp (7.2 numbers, still live): **3.3% max HP** magic + **1.3% max HP** heal per proc, +10 HP forever. Unshakeable sits on that page.

On **Dusk → Hull → Rift**, extra autos feed Skipper, lightning, and Dusk on-hit. That is why Tempo is the default here.

| Aspect | Lethal Tempo | Grasp | Edge |
|--------|--------------|-------|------|
| **Lane 3s, Grasp cold** | 1178 mix / 5 AA | 1044 mix / 4 AA | **Tempo dmg**, survive tie |
| **Lane 3s, Grasp prestacked** | 1178 mix | 1095 mix / more ehp | **Tempo dmg**, **Grasp live** |
| **1v1 8s @14:00** | **2975** mix / 15 AA / 3926 ehp | 2399 mix / 11 AA / **4310** ehp | **Tempo kill**, **Grasp live** |
| **1v1 8s @22:00** | **4854** mix / 5447 ehp | 3908 mix / **5959** ehp | same split |
| **Teamfight (dive one)** | Kill the carry faster | Live the collapse (HP stacks + Unshakeable) | split |
| **Ranked CN Baron** | Less used | Most-played keystone | Grasp |

How to read it:

- **Damage / 1v1 / all-in:** Lethal Tempo. ~4 extra autos in 8s, a second Skipper, more lightning, then bullets once you hit 6 stacks. This Dusk page is built for that.
- **Survival:** Grasp. Heal on the proc, 10 HP a pop over the game, Unshakeable in the 5v5. Ehp wins every long-fight clock.
- **Laning:** If you only tap them for 3s and Grasp is not stacked, Tempo still hits harder. If you **prestack Grasp on the wave** then walk up, Grasp wins the *trade* (you live, they don't chunk you off). Into Teemo/Kennen/Vayne you never stack Tempo — take Grasp.
- **Teamfight:** Volibear dives one person. Tempo deletes that person. Grasp is why you are still standing when their team peels. 7.3 removed Tempo's range, so it no longer helps you walk onto the ADC.

**Default on this page: Lethal Tempo.** Swap to Grasp into poke/range, or if you keep dying in the 1v1 instead of killing.

## Last Stand vs Cut Down vs Coup de Grace

Precision slot 2. **Last Stand** is the default on this page.

| Rune | When it pays | Extra mix @14:00 slugfest |
|------|----------------|---------------------------|
| **Last Stand** | You are below 60% HP (5% → 11% at 30%). W-heal 1v1s sit ~45%. | **+167** |
| **Cut Down** | They are above 60% HP (6.5%). Old Giant Slayer; nerfed 8% → 6.5% in 7.2. | +68 |
| **Coup de Grace** | They are below 40% HP (8%). | +84 |

Slugfest (this kit): Last Stand wins 8 / 14 / 22. You take damage, W heals you, you stay in the 5–11% band for most of the fight. That also amps the second bite.

If **you stay full HP** (you are stomping, not dueling): Last Stand is **0**. Then Cut Down for tanks (front of their bar), Coup for squishies (execute). Do not take Coup as default — if they never drop below 40%, it does nothing.

Grasp poke page: still Last Stand. You get poked down, then all-in.

## Why this order

| Item | Why it is here |
|------|----------------|
| **Dusk first** | 233g cheaper than Trinity. HP + haste + AS + AP. AP feeds E shield, R, and lightning. Spellblade is magic and **double-applies on-hit** (two lightnings). |
| **Hull second** | Skipper: every 4th auto is 160% base AD + 5% max HP. That is the 1v1 item. Also 45 AD for Q / empowered W / R. |
| **Rift third** | Turns the slugfest into a heal-off. 2% bonus HP → AP, so Heartsteel-less HP still scales the kit. |
| **Despair fourth** | Unkillable pulse. You already have damage. |

Do **not** buy Trinity and Dusk together (both spellblade).

## Rank (sim, 8s 1v1 strength)

Lethal Tempo page (Alacrity on). Extra autos raise every path vs the old Grasp-baked numbers.

| Path | 8:00 | 14:00 | 22:00 |
|------|------|-------|-------|
| **Dusk → Hull → Rift** | 5162 | 6311 | **9484** |
| Dusk → Rift → Despair | 5162 | 6311 | 9063 |
| Tri → Rift → Twin | **5208** | 6323 | 8421 |
| Heart → Dusk → Hull | 4742 | 5863 | 8982 |
| Heart → Tri → Despair | 4742 | 5863 | 8808 |

Trinity’s first-item mix is a hair higher at 8:00 (more AD on the Tempo auto storm). Dusk still wins the game: it finishes **~7:00**, then Hull Skipper and Riftmaker bury the Trinity path.

Heartsteel first is tankier and cheaper (2800). It is **not** stronger in the 1v1 — no sheen, no attack speed.

## Swaps

- **Grouping, not splitting:** Hullbreaker 2nd → **Riftmaker** 2nd, Despair 3rd.
- They heal (Aatrox, Soraka, Vlad): **Thornmail** instead of Twinguard.
- Heavy AP: Steelcaps → **Mercury's**, Twinguard → **Kaenic Rookern**.
- You are losing lane to poke and cannot finish Dusk: **Heartsteel** first, then Dusk, then Hull. This is the Diamond+ alt, not the strongest 1v1.
