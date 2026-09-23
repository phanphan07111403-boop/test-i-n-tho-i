# Wild Rift 7.3 — Top 10 build / playstyles

Patch **7.3** vs a 7.2-ish snapshot. Same **8s** combat window at **12 / 16 / 20**.

7.3 splits Magnetic Blaster into distinct jobs (crit vs on-hit vs range vs ult-burst), raises base crit to **200%**, and gives several kits an explicit identity.

## Run

```bash
python3 simulate_wr_73_playstyles.py
```

Outputs:
- `report.txt` — full ranking + why
- `results.json` — snapshots per playstyle

## Question answered

Which **builds / playstyles gained the most** in 7.3 (not “who is strongest”)? **Top 10.**

## Winner (sim)

| Rank | Build / playstyle | Playstyle | Avg Δ | 7.3 job |
|------|-------------------|-----------|-------|---------|
| 1 | **Kalista Rend-Shiv** | On-hit spear dump | +1233 | Bounce spears, one E rips the pit |
| 2 | **Teemo Nashor-Shiv** | AP on-hit poison | +1191 | Nashor is 80 AP again; poison bounce |
| 3 | **Caitlyn trap-Headshot** | Crit sniper | +1100 | Stormrazor lane, trap Headshot, IE Ace |
| 4 | **Varus blight-Shiv** | On-hit artillery | +1046 | Bounce Blight, Q detonates |
| 5 | **Twitch stealth-Fiendhunter** | Stealth ult burst | +1020 | Camo → Ambush AS → R 3-crit → E |
| 6 | **Lucian Culling-crit** | Crit tempo | +1004 | The Culling scales with IE |
| 7 | **Zeri Fiendhunter-R** | Ult-window carry | +896 | Longer Overload + Fiendhunter |
| 8 | **Ashe Focus-crit** | Crit utility kiter | +830 | Frost is pure crit; AD growth |
| 9 | **Kayle Nashor-ascend** | AP on-hit scaler | +746 | Nashor 80 AP + Shiv 40/40/30% |
| 10 | **Kai'Sa hybrid on-hit** | Hybrid on-hit | +721 | Plasma AP + Rageblade 35/30 |

## Three lanes — don't mix them

- **On-hit clump** — Shiv → Rageblade → Terminus/Nashor: Kalista, Teemo, Varus, Kai'Sa
  - **4th = Runaan's** if dragon/Baron clumps continue. **4th = BotRK** if you are glued to one tank.
  - Runaan finishes ~24:00 (2650g). BotRK ~25:00. Most 20–22 min games never see a 4th.
- **Crit sniper** — Stormrazor or Yun Tal → IE → RFC/Fiendhunter: Caitlyn, Twitch, Lucian, Zeri, Ashe
- **Duelist** — Kraken → Rageblade → Terminus: Vayne (not Shiv)

## Who did *not* gain

- **Vayne** — Tumble/R up, rank-4 Silver Bolts 11% → 9%. Lane up, 3-item nearly flat. Bolts don't bounce.
- **Kog'Maw** — Shiv bounce is real at 20:00, but 7.2 BotRK wins 12–16 as a first item.
- **Ezreal** — Muramana no longer needs mana spend; Q damage/CD nerfs eat it.
- **Jhin / Senna / Yasuo / Yone** — crit system up, their modifiers were compensated down.
