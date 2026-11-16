# Varus — Statikk Shiv and Runaan's Hurricane

Wild Rift patch **7.3f**. Level 15, Q, W, and E maxed. A full Piercing Arrow after Blight stacks.

## Run

```bash
python3 simulate_varus_blight.py
python3 simulate_varus_full.py
```

Outputs:
- `report.txt` — one champion, a grouped poke, a 3-Blight commit, and a wave stealing the bolts
- `results.json` — the same rows
- `full-report.txt` — the finished six items, the rune page, and the buy-order checkpoints

## Question answered

Do Statikk Shiv and Runaan's Hurricane earn the purchase when the plan is poke plus Blight on more than one champion?

## Result

Hurricane is what keeps Blight on the side champions. Statikk adds a second stack on those champions only when the lightning is ready. Together, and with Guinsoo's Rageblade, that second stack refunds a second arrow and the bolts carry the on-hit. On one champion, or through a minion wave, the pair is the slower build.

## Full build

The three core items stay. The finished set is Berserker's Greaves, Statikk Shiv, Guinsoo's Rageblade, Runaan's Hurricane, Blade of the Ruined King, and Terminus.

BotRK is the lifesteal. It heals basic attacks, the bolts, and its own physical on-hit, including the wave. Terminus is the last item: it is the armor and magic penetration the blight and the percent-health on-hit need. Bloodthirster heals a wave for more and kills the bruiser slower. Riftmaker heals the fight and barely heals a wave.

Runes are Lethal Tempo, Brutal, Cut Down, Legend: Bloodline, and Bone Plating. Bloodline is the omnivamp. On the finished build the 4-second grouped damage matches Legend: Alacrity, and the fight heal is the larger number. Alacrity clears the Statikk-spike wave a fraction of a second faster.

Buy order: Long Sword, Vampiric Scepter, Berserker's Greaves, Statikk Shiv, Guinsoo's Rageblade, Runaan's Hurricane, finish Blade of the Ruined King, Terminus. The scepter is the component that lets him stay for the wave before BotRK exists. Level 15 in this script uses the patch 7.3 base attack damage of 58. The pair script above still uses 54, so its report stays comparable to the first answer.
