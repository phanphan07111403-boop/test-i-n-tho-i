# Varus — Statikk Shiv and Runaan's Hurricane

Wild Rift patch **7.3f**. Level 15, Q, W, and E maxed. A full Piercing Arrow after Blight stacks.

## Run

```bash
python3 simulate_varus_blight.py
```

Outputs:
- `report.txt` — one champion, a grouped poke, a 3-Blight commit, and a wave stealing the bolts
- `results.json` — the same rows

## Question answered

Do Statikk Shiv and Runaan's Hurricane earn the purchase when the plan is poke plus Blight on more than one champion?

## Result

Hurricane is what keeps Blight on the side champions. Statikk adds a second stack on those champions only when the lightning is ready. Together, and with Guinsoo's Rageblade, that second stack refunds a second arrow and the bolts carry the on-hit. On one champion, or through a minion wave, the pair is the slower build.
