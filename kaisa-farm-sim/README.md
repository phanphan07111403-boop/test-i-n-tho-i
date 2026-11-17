# Kai'Sa — Statikk farm vs Guinsoo

Wild Rift patch **7.3 / 7.3b** (Statikk at 2900g, Electroshock +7). Dragon lane, Q maxed first, over a no-kill gold clock through **26:00**.

## Run

```bash
python3 simulate_kaisa_farm.py
```

Outputs:

- `report.txt` — one-item duel, equal-gold fork, minute clock, verdict
- `results.json` — per-minute clears and all-in numbers for three orders

## Question answered

How much does **Statikk Shiv** help Kai'Sa farm compared with **Guinsoo's Rageblade**, and what happens if Statikk is moved to the **last item** the way Kalista can afford?

## Winner (sim)

**Statikk Shiv → Berserker's Greaves → Guinsoo's Rageblade → Nashor's Tooth → Kraken → Terminus**

Guinsoo first is the 1v1. It reaches the same Statikk + Guinsoo inventory at the same gold (~15:18). Statikk last is not bought by 26:00.

| When | What the chain actually does |
|------|------------------------------|
| One item, level 9 | Opening auto **573** on 4 minions vs Guinsoo's **172** on 1. Casters die in **1.0s** vs **1.8s**. Full clear is a **tie at 6.6s** — both wait on the 6s Q for the last melee. |
| Same gold, 2 items | Statikk + Guinsoo evolves Q. Standard wave **3.4s** vs Guinsoo + Nashor **5.3s**. Nashor kills a frontliner faster (**5.8s** vs **7.2s**). The chain kills a squishy faster (**3.5s** vs **3.8s**). |
| Last slot | Q evolve slips from **16:00** to **21:00**. The bolt never arrives in a normal game. Adding it anyway, at level 15, cuts a standard wave from **3.4s** to **1.6s** because Guinsoo / Nashor / Terminus finally bounce. |

## Why

- A Wild Rift wave is **4 minions**. The bolt (90 magic, on-hits on the bounces) covers it from level 1. That shoves. It does not delete the melee by itself.
- Q splits 6 missiles and does **not** reset on kill. Kalista's Rend does, so she can front-load Guinsoo or skip the chain and still farm. One baron list never buys Statikk. Kai'Sa cannot copy that.
- Q evolves at **70 bonus AD**. Statikk 40 + Guinsoo 35 crosses it. Nashor gives AP, not AD, so "Statikk last" holds Q at 6 missiles until Kraken.
- Guinsoo still wins the naked auto duel (**1346** vs **968** on a frontliner in 8s). Buy it second if you rushed the wave, or first if the lane opponent is the problem — then buy the chain, do not save it for slot 6.

## Playstyle

- Skill order: max **Q → E → W**. R at 5 / 9 / 13.
- Walk into the wave with the bolt charged (about 7s of movement fills Energized). Auto the caster, Q, leave when the casters are dead if you only need the shove.
- Guinsoo first until Statikk: you win the long auto fight and the wave does not move.
- Nashor after both, so W evolves and the chain has an on-hit worth spreading.
