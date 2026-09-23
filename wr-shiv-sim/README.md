# Wild Rift — Statikk Shiv Top 5

Patch **7.3** item model. On-hit marksmen over a **20-minute** average game.

Magnetic Blaster is gone. Statikk Shiv is the on-hit teamfight item: **40 AD / 40 AP / 30% AS**, Energized lightning that **copies on-hit onto bounce targets**.

## Run

```bash
python3 simulate_wr_shiv.py
```

Outputs:
- `report.txt` — full ranking, minute-by-minute unique package, bounce anatomy
- `results.json` — machine-readable snapshots per champion

## Question answered

Which Wild Rift champions actually convert 7.3 Statikk Shiv — the bounce, not just the stats — well enough to buy it? **Top 5.**

## Winner (sim)

**1. Varus · 2. Kog'Maw · 3. Kalista · 4. Teemo · 5. Twitch**

| Rank | Champion | Unique Shiv (10–20) | Why it copies |
|------|----------|---------------------|---------------|
| 1 | **Varus** | +1666 | W on-hit + Blight stacks bounce, one Q detonates the pit. 40 AP is live. Innate turns AS into AD+AP. |
| 2 | **Kog'Maw** | +1396 | W Bio-Arcane %max HP on-hit copies onto every bounce. Highest raw clump damage. |
| 3 | **Kalista** | +1338 | Rend spears bounce; one E rips the clump. 40 AP is mostly wasted. |
| 4 | **Teemo** | +1269 | Toxic Shot + 4s poison bounce. 40 AP is fully spent. Nashor core. |
| 5 | **Twitch** | +1054 | Venom stacks bounce, then E (7.3 hybrid). Spray and Pray already AoE — some overlap. |

Shiv finishes ~**9:00** on a farmer gold curve.

## Why these five

- Shiv's unique job is hitting the people you **did not auto**.
- %HP on-hits (Kog W, Varus Blight) scale with tank HP in a 4-man dragon pit.
- Stack-then-detonate kits (Varus Q, Kalista E, Twitch E) cash extras in one spell.
- 40 AP is real on Varus / Kog / Teemo. Dead on Vayne / mostly dead on Kalista.

## Who should skip it

- **Vayne** — Silver Bolts do not apply to extra targets (same rule as Runaan's) and expire on switch. AP wasted. Kraken / BotRK / Rageblade stay better.
- **Kai'Sa** — Plasma bounces, but secondaries only eat ~2–3 Energized hits, so they never 5-stack pop from Shiv alone. WR evolutions are **item-based**, not 40 AP.
- **Kayle** — Dream stat line (40/40/30%), but Aflame waves already splash E after 9. Kit overlap.
- **Ashe** — Frost Shot slow bounces. Utility toy, not a damage item.
- **Crit ADCs** (Jinx, Caitlyn, MF, Jhin) — they wanted Magnetic Blaster. In 7.3 they want Stormrazor / Rapid Firecannon / Infinity Edge.

## Playstyle

Buy Shiv when fights clump (dragon, Baron, mid siege). Kraken still wins a 1v1.

1. Kircheis Shard + Berserker's (Boots of Mana on Teemo)
2. **Statikk Shiv** (~9:00)
3. Guinsoo's Rageblade — phantom hit multiplies the on-hits Shiv copies
4. Terminus (AD) or Nashor's Tooth (AP)
5. **Runaan's 4th if fights stay clumped.** BotRK 4th if you are hitting one tank.

Shiv copies on-hit on Energized (~every 4.2 autos). Runaan copies on-hit on **every auto** to 2 nearby targets. They stack — do not sell Shiv for Runaan.

```bash
python3 simulate_onhit_4th.py
```
