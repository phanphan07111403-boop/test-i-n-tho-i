# Shyvana Jungle — Late-Game Counter-Meta

Wild Rift patch **7.3d / 7.3f**. Full-clear scaler into a **12-second** dragon-form teamfight.

## Run

```bash
python3 simulate_shyvana_jungle.py
```

Outputs:
- `report.txt` — minute-by-minute optimal + verdict
- `results.json` — machine-readable snapshots per build

## Question answered

After the **Ocean omnivamp nerf (20% → 10%)**, which jungle build **counters the tanky meta** and still **wins late** — shred frontlines without dying mid-dragon form?

## Winner (sim)

**Trinity Force → Blade of the Ruined King → Death's Dance → Force of Nature → Amaranth's Twinguard**

(Immortal Treads boots)

| When | Spike |
|------|--------|
| ~8:00 | **Trinity Force** — clear + Spellblade weave |
| ~16:00 | **BotRK** — Q double on-hit %HP (anti-tank) |
| ~21:00 | **Death's Dance** — survive dive after Ocean nerf |
| ~24:00 | **FoN + Twinguard** — finish the full 12s form |

At **25:00**, this path delivers **~10.3k** late-power and stays up the full fight window. Pure anti-tank glass (Eclipse / Serylda) deals more paper tank damage but dies around **8.6s**. Cap-rush AP dies around **6.7s**.

## Why

- BotRK on Twin Bite hits **twice** — mandatory vs HP stackers.
- Ocean sustain was cut in half; item tankiness (DD / FoN / Twinguard) replaces it.
- Flame Breath AP ratios were buffed, so AP burn is real — but without a resist spike you still lose the late brawl.
- Scorch → **true damage at 300 stacks**; take dragons, stay alive, auto the mark.

## Runes (sim, items locked)

**Conqueror · Unshakeable · Second Wind · Overgrowth · Legend: Alacrity**

| Choice | Why |
|--------|-----|
| **Conqueror** over Fleet | +4–5% late-power; Twin Bite stacks it fast; in-combat omnivamp replaces Ocean |
| **Alacrity** over Bloodline/Haste | More autos → more Q refunds → more BotRK %HP doubles |
| **Overgrowth** | Permanent HP for the mid-team dive |
| **Unshakeable** | Resists while CC'd after R lands |

Swaps: **Fleet** if you get kited / need stick MS · **Perseverance** over Overgrowth vs heavy CC · **Bone Plating** over Second Wind vs burst.

## Playstyle

- Full clear → level 5 R → contest dragons for stacks.
- Skill order: max **E → W → Q**; R at 5 / 9 / 13.
- Fight combo: R after they commit → E mark → W stick → Q double on-hits → autos.
