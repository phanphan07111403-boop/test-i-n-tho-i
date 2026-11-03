# Volibear — hard to kill, high damage, Wild Rift

Wild Rift, patch **7.3d**. Baron lane, level 15. He ults onto a carry and stands in a carry-plus-mage focus for 11 seconds. Patch 7.3b (14 Oct 2026) is the last kit change. 7.3d did not touch him.

## Run

```bash
python3 simulate_volibear.py
```

Outputs:
- `report.txt` — the winning build, the purchase order, and the traps
- `results.json` — the ranked six-item results

## Winner

**Armored Advance → Divine Sunderer → Navori Quickblades → Riftmaker → Wit's End → Unending Despair**

Runes: Conqueror, Brutal, Last Stand, Alacrity, Overgrowth.

| At 18:00, level 15 | Result |
|--------------------|--------|
| Ultimate dive | **9150** damage, lives, ends at **4208 / 4452 (95%)** HP |
| Same items, bites the frontliner first | 9150, still alive. Both champions die in that fight too |
| Same fight, no ultimate | 8435 damage, lives, ends at 88% HP |
| Full tank (Heartsteel, Unending, Randuin, Kaenic, Twinguard) | 5090, lives at 84% |
| AP glass (Dusk, Nashor, Deathcap, Infinity Orb, Void) | 9150, dies at 6.7s |
| Trinity (Cleaver, Sterak, Death's Dance, Twinguard) | 7096, lives at 35% |
| Heartsteel core (Titanic, Sterak, Unending, Twinguard) | 6589, lives at 50% |

The 9150 is both champions' health. The carry dies at 4.7s. The frontliner dies at 11.5s, at the end of the ultimate. Four wounded bites, five mauls, 19 autos, six spellblades, three Sky Splitters.

Level 15 with the ultimate up, Conqueror fully stacked on the sheet (the fight starts at zero stacks): 4452 HP, 143 AD (25 bonus), 157 AP, 182 armor, 151 MR. W is on a 3.33s cooldown before Navori. Attack speed is 2.04 at five passive stacks. The wounded bite is 585 pre-mitigation. The E shield is 741.

## Why this is the Wild Rift bite

The wounded maul is exactly **1.60×** the normal one: `(80 + 110% AD + 6.5% bonus HP) × 1.60`, and it heals `50 + 14% missing HP`. Frenzy sits on Volibear for 8 seconds after he mauls a champion. The 1.60 stays flat. Bonus AD is already inside the 110% and 176% ratios, and it also feeds Q and R. Bonus HP feeds the 6.5% / 10.4% ratios and the E shield.

Spirit Visage, Overlord's Bloodmail, and Protoplasm Harness are PC items. The heal in this fight is Divine (1629), Riftmaker and Conqueror omnivamp (1109), the bite (445), and Unending (332).

- Divine Sunderer is 10% of the target's max HP on the spellblade and a heal for 6% of their max HP, every 1.5s. That heal is why he finishes the focus near full.
- Navori brings Q, W, and E back while he is autoing. Each attack cuts 15% off the remaining cooldown. Crits deal 200% on this patch.
- Riftmaker turns 2% of bonus HP into AP. After four seconds in the fight it is +8% damage and 10% omnivamp. Conqueror takes the AP side here (8 AP per stack at level 15, then 9% omnivamp).
- Wit's End is 50% attack speed, 45 magic resistance, and a 40 magic on-hit. Patch 7.3 removed its heal. Cosmic Drive in that slot ends the ult fight about 1% healthier and does less once Stormbringer is down.
- Unending Despair pulses 3% max HP magic every 4s and heals for 250% of the post-mitigation damage.
- Armored Advance is the boot: armor, 10% off champion basic attacks, and a physical shield the first time they hit him.

Lightning is 68 + 40% AP at level 15 and has no AD ratio. It is the second-largest source in this fight, behind Sky Splitter.

## When they have Ignite

Wild Rift Ignite is 60% grievous. Shields are left alone. The same six items still clear both champions and he finishes at **50%** HP.

Replacing Unending with **Kaenic Rookern** is the same clear and he finishes at **60%**. That is the swap when the heal is what they are cutting and you want more health left. The original six items still finish the window alive, at 50%.

## Order

Armored Advance first, then Divine, Navori, Riftmaker, Wit's End, Unending. The gold curve has the full set finished at 18:00 (18300 gold, the six items are 17050).

| Minute | What he owns |
|--------|----------------|
| 4:00 | Armored Advance |
| 8:00 | Divine Sunderer |
| 12:00 | Navori, Riftmaker components |
| 14:00 | Riftmaker |
| 16:00 | Wit's End |
| 18:00 | Unending Despair |

## How to fight

Max W, then E, then Q. R at 5, 9, and 13. At level 15, Q, W, and E are all rank 4.

Cast E on the way in, Q, then R so you land as the bolt hits. Q auto the carry, bite, and keep attacking so Navori keeps cutting the cooldowns. Frenzy stays on him when the carry dies, so the next bite on whoever is left is still the 1.60× maul until the 8 seconds run out.

## Not the late-game build

- A full resist page lives and leaves the 176% ratio on base AD. Heartsteel lands one proc. He does 5090 and the frontliner is still up.
- Deathcap and Nashor with Mercury's Treads kill both champions and fall over at 6.7s, while the ultimate is still up. Lightning and E scale with AP. The W heal scales with missing HP.
- Trinity is one spellblade hit for 200% base AD. The Divine version hits for a chunk of their max HP and heals. Trinity's six-item page ends at 35% and does not kill the frontliner.
- Sterak and Mantle of the Twelfth Hour share one Lifeline proc.
