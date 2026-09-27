# Volibear vs Shen — Baron

Patch **7.3**. Same GameSir X3 Pro question, split: **with the pad**, **without the pad**, then **lane / 1v1 / teamfight**.

```bash
python3 voli-vs-shen/compare.py
```

## Short answer

| Situation | Play |
|-----------|------|
| **GameSir X3 Pro** | **Volibear** |
| **Touch, no pad** | **Shen** |
| **Lane** | **Volibear** |
| **1v1 / side** | **Volibear** |
| **Teamfight** | **Shen** |

They are not the same champ. Volibear wins the fight in front of him. Shen wins the map.

## Score

Rubric 0–10. Not a shared combat engine — kits do different jobs.

| Aspect | Volibear | Shen | Edge |
|--------|----------|------|------|
| GameSir X3 Pro | **9.4** | 6.2 | **Volibear** |
| Touch (no pad) | 8.0 | **8.6** | **Shen** |
| Lane (generic) | **8.6** | 6.4 | **Volibear** |
| 1v1 / side | **9.2** | 6.2 | **Volibear** |
| Teamfight | 6.2 | **9.3** | **Shen** |
| Head-to-head | — | W on the bite | **Shen if W is timed** |

## Ranked signal (why “better top” flips)

| Source | Volibear Baron | Shen Baron |
|--------|----------------|------------|
| wildriftmeta all ranks | **54.4% WR**, 5.0% pick, **S+** | 48.4% WR, 1.1% pick, A |
| wrchina.gg Diamond+ (2026-09-26) | **48.3% WR**, C, **#32 / 41** | **56.8% WR**, **S+ #2 / 41** |

Low/mid elo and all-ranks lists like Volibear (easy fighter, high pick). CN Diamond+ likes Shen (global R, almost never banned). Touch ranked at high elo is Shen. Pad 1v1 is Volibear.

## GameSir X3 Pro — Volibear

Q is “left stick toward them, then auto.” W is a targeted bite. E can sit on your feet with a GameSir gesture. R is a fat landing zone that **turns the tower off**. Overlay mapping matches the kit. That is why he won `gamesir-x3-duelist/`.

Shen on the same pad: E is a dash you must **draw through them** (miss = no taunt, no energy). W needs the spirit blade in the right place. R is picking an ally on the map — overlay is bad at portraits and the minimap. Playable. Not the pad champ.

## Touch (no pad) — Shen

Thumbs are what Wild Rift was built for. Swipe E through them, tap R on the ally portrait, drag Q so the blade clips. Volibear is still easy on glass (low difficulty), but Shen’s extra buttons stop being a tax. Then the CN Diamond+ table decides it: Shen S+, Volibear C.

If you only play on the phone and you want **wins**, pick Shen. If you only play on the phone and you want **kills in lane**, pick Volibear anyway.

## Lane — Volibear

Volibear is a lane bully: Q stun, W heal, E shield, R dive. Shen is the lowest-damage Baron — Q only empowers autos. He farms, waits for 5, then the lane is bait for R. Volibear crashes and kills. Shen holds and does not die.

Wave: Volibear with Dusk shoves. Shen without Titanic/Bami’s does not (Heartsteel first = 35% cannon wave). That is the “game too slow” feel.

## 1v1 / side — Volibear

Isolated 8s slugfest is Volibear’s whole kit (Dusk → Hullbreaker Skipper → Riftmaker). Shen’s kit is not a kill threat. He 1v9s by living and ulting out, not by winning the duel.

## Teamfight — Shen

Stand United is a global save. Shadow Dash taunts the diver off your carry. Spirit’s Refuge eats the burst auto window. Volibear **dives one person** with R and has no peel after it. He is a skirmisher in a 5v5, not a front line.

## Head-to-head

Shen **W blocks the autos Volibear lives on** (Q stun hit, W bite, lightning). Taunt pauses Thundering Smash. Volibear E is magic, so it still lands. R still dives the tower.

If Shen holds W for the bite, he wins the trade. If W is down, Volibear runs him down. Do not take this as “Shen counters Volibear always” — it is a W-timing skill matchup.

## Pick

- **GameSir + want 1v1s:** Volibear. Build in `volibear-build-sim/`.
- **Touch + want ranked wins:** Shen. Build in `shen-build-sim/` (or the CN 62% Heartsteel core if you accept the slow lane).
- Team already has a dive / assassin: Shen (peel + R).
- Team needs someone to start the fight: Volibear.
