# Kayle Baron — China on-hit Manamune (Wild Rift 7.3)

PC China Kayle top often rushes **Tear → Manamune** into on-hit (Rageblade / Nashor / BotRK / Terminus). This sim ports that plan onto **Wild Rift patch 7.3** baron Kayle and asks if it is worth buying.

## Run

```bash
python3 kayle-manamune-sim/simulate_kayle_onhit.py
```

Outputs:
- `report.txt` — minute-by-minute optimal, build table, verdict
- `results.json` — snapshots per path

## Question answered

Does China on-hit Manamune top beat Wild Rift's own Kayle cores in a **20-minute** game, on a **6s Q-shred / E-reset / auto** window vs a baron bruiser?

## Winner (sim)

**Rageblade → Berserker's Greaves → Blade of the Ruined King → Terminus**

China **Manamune → Rageblade → BotRK** is second: about **5%** less bruiser-weighted damage, and it finishes Terminus later.

| When | Spike |
|------|--------|
| ~6:00 | **Muramana** if you rushed Tear — real 6s-trade spike, beats Nashor-first |
| ~7:00 | **Rageblade** — the WR 7.3 on-hit keystone (30 magic + later phantoms) |
| ~15:00 | **BotRK** — 7% current HP into the baron tank |
| ~20:00 | **Terminus** — mixed pen + 30 magic; this is the 20-min closer China often misses |

## Worth it?

**No as the default.** Playable only if you already wanted Tear for Q-spam.

- WR 7.3 Tear stacks fast, so Manamune **is** Muramana on completion. Stacking is not the PC problem.
- The problem is spending 2900g on **0% attack speed** before Rageblade / BotRK.
- WR Starfire is **5% bonus AD + 15% AP**. Manamune's AD barely feeds it.
- From level 9, Aflame waves want more attacks. Rageblade and BotRK buy AS; Manamune does not.

Do not buy **Nashor → Manamune**. That path is worse than rushing Manamune *and* worse than skipping it.
