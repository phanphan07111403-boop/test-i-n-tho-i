# Senna — Ionian vs Boots of Dynamism

Wild Rift **7.3** (boot stats from **7.2 / 7.2a**, unchanged in 7.3 notes). Same core, **only the boot line**. Game **20 minutes**. Transcendence on both paths.

Previous DH carry sims defaulted to Dynamism. Enchanter sims defaulted to Ionia. This checks whether that split survives leftover Long Sword, Q auto-refunds, and Flash haste.

## Run

```bash
python3 simulate_senna_boots.py
python3 test_senna_boots.py
```

Outputs:
- `report.txt` — minute table for ADC and support + verdict
- `results.json` — snapshots per build

## Question

ADC Dark Harvest Senna still Dynamism? Support Senna still Ionia? Or is one boot just better?

## Winner (sim)

| Role | Boot | Why |
|------|------|-----|
| **ADC / flex DH** | **Dynamism → Armorcrusher** | Combat area **+10.7%**, wins **20/20** minutes |
| **Support** | **Ionian → Crimson** | Heal **+10.7%**, Q/min **+14.0%**, W/min **+12.3%**, Flash **125s** vs 150s |

Support Dynamism still wins raw poke damage (**+10.5%**). That is selfish. Q is a heal; Flash and W root are the job.

| When | ADC Dynamism spike |
|------|--------------------|
| ~2:00 | **Boots of Dynamism** — Long Sword already bought, T2 is 300g more |
| ~8:00 | **Draktharr** (Ionia ~9:00 — leftover Long Sword tax) |
| ~13:00 | **Collector** (Ionia ~14:00) |
| ~15:00 | **Armorcrusher** (6% pen). Crimson also 15:00 |
| ~20:00 | Magnetic both |

Ionia still has **+16.3% Q/min** on ADC. Autos already refund 1s of Q. Transcendence 12 + Draktharr 10 cover most of the 15 AH.

## Why leftover Long Sword flips ADC gold

Dynamism recipe is Speed + **Long Sword** + 300 = 1200. ADC started sword, so T2 completes ~2:00.

Ionia recipe is Speed + **Ring of Revelation** + 300 = 1000. The Long Sword stays in inventory (12 AD, 500g stuck). Draktharr does not eat it → **Draktharr 9:00, Collector 14:00**.

Paper cost says Ionia is 200g cheaper. On a sword-start ADC it is the slower legendary path.

## Boot stats used

| Item | Gold | Combat | Utility |
|------|------|--------|---------|
| Ionian T2 | 1000 | 15 AH | 15% summoner haste |
| Dynamism T2 | 1200 | 15 AD, 10 flat pen | — |
| Crimson T3 (after 10:00) | 2000 | 25 AH, 75% mana regen | 20% summoner haste, 8% MS after Q/heal/Flash |
| Armorcrusher T3 (after 10:00) | 2200 | 20 AD, 10 flat + **6%** pen | 20 OOC MS |

Armorcrusher 7.2a: AD 25→20, flat pen 12→10. 6% pen stayed.

**Ionia is the boot.** Ability haste also comes from Transcendence, Draktharr, Helia, Harmonic, Serylda. Do not treat "needs HA" as "buy Ionia".

## When Ionia still

- Support — Flash 150s → 130s → 125s, more Q heals, more W roots.
- Max-range poke/heal only (cannot auto) — then AH *is* the damage stat.
- Already bought Ionia T2 — you cannot cross-upgrade into Armorcrusher.

## Traps

- Copying ADC Dynamism onto support. Heal/Q/W/Flash lose.
- Copying support Ionia onto DH carry. Leftover Long Sword delays Draktharr; 0 pen until Collector/Serylda.
- Buying T3 before 10:00 — the shop will not allow it.
