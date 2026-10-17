# Kayle — Kraken → boots → Dusk, Empowerment

Wild Rift patch **7.3**. Solo lane, played for the late page. Full six items land around **22:00**.

## Run

```bash
python3 simulate_kayle_spike.py
```

Outputs:

- `report.txt` — stack weave, winning page, spike minutes, top builds
- `results.json` — machine-readable snapshots

## Question

Rush **Kraken Slayer → boots → Dusk and Dawn** with **Empowerment**. Finish the other three slots. Which full page is the strongest late spike?

Dusk's Spellblade applies on-hit effects a second time. That second application is a stack for Empowerment and for Kraken.

**E-A = 2 stacks.** The next auto is the third stack and procs both.

## Winner (sim)

**Kraken Slayer → Boots of Mana → Dusk and Dawn → Guinsoo's Rageblade → Terminus → Nashor's Tooth → Spellslinger's Shoes**

| When | Spike |
|------|--------|
| ~6:00 | **Kraken** — the 3-hit physical proc |
| ~8:00 | Boots of Mana |
| ~12:00 | **Dusk and Dawn** — E-A becomes 2 stacks |
| ~15:00 | **Guinsoo** — Phantom Hit, a second extra on-hit |
| ~18:00 | **Terminus** — up to 30% armor and magic pen |
| ~21:00 | **Nashor** — the on-hit both doubles keep firing |
| ~22:00 | Spellslinger's Shoes — pen, the attack speed cap is already full |

## Why

- E then the primed auto applies on-hit twice, so Empowerment and Kraken both jump two stacks.
- Guinsoo's phantom hit does the same thing on every third attack once Seething is full. It also repeats Nashor, E, and Terminus.
- Terminus pens the physical Kraken proc and the magic on-hits. Void Staff does not replace it: item percent pen caps at 40%, and Void is magic-only.
- Deathcap sets are about 10% behind. This page's AP pool is modest, and the cap does not add an on-hit for the extra stack to repeat.
- Berserker's into Gunmetal loses the late check. The finished page is at the 2.50 attack speed cap, so more attack speed adds no swings. Spellslinger's penetration does.
- Lich Bane is the same Spellblade unique as Dusk, so it is not a finisher.

## Weave

Q and E open. First auto is **E-A** (2 stacks, no proc). The next auto procs Empowerment and Kraken. W primes the next Dusk window when Q and E are both down. At two stacks already, that W-A procs on the first of its two applications and leaves 1 stack.
