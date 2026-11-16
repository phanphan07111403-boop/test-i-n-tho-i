# Zyra mid + support — Wild Rift 7.3 items & runes

Patch **7.3**. Plant-spam zone playstyle. Support over **20 minutes**, mid over **22**.

## Run

```bash
python3 simulate_zyra_73.py
python3 test_zyra_73.py
```

Outputs:
- `report.txt` — minute-by-minute item path, then rune pages on the winner
- `results.json` — snapshots per role / build / page

## Question answered

On 7.3, which **item path and legal rune page** peak real harass for Zyra **support** and **mid**, with enough burn uptime to finish the 3s ticks?

7.3 itself only touched Zyra's attack-speed ratio (global cleanup). Mage items and the Comet nerf are still the 7.2 kit. Live Diamond+ moved support boots to **Ionian Lucidity** (~80% pick) and mid cores toward **Blackfire → Liandry**. The sim checks whether that is actually better for plant spam.

Rune loadout: **1 keystone + 3 primary + 1 secondary**. Ingenious Hunter is gone. Legend: Haste replaced Legend: Tenacity. Comet is **5% AP** (not 20%).

## Winners (sim)

### Support — 20:00, Flash + Ignite

**Liandry → Ionian → Rylai → Morello**

**Arcane Comet · Manaflow Band · Transcendence · Scorch · Cut Down**

Skill order: **E → Q**, W 1-point, R at 5/9/13.

| When | Spike |
|------|--------|
| ~5:00 | Fated Ashes (first burn) |
| ~9:00 | **Liandry** — 2% max HP/s, plants refresh it |
| ~10:00 | **Ionian Lucidity** — 15 AH, cheaper than Mana boots |
| ~16:00 | **Rylai** — locks burn uptime + Comet land |
| ~20:00 | **Morello** actually finishes; Blackfire 4th sits as Lost Chapter |

Cut Down wins the poke metric (targets are >60% HP). Swap **Bone Plating** vs kill lanes. Cheap Shot if you always root.

### Mid — 22:00, Flash + Ignite (Barrier vs assassins)

**Blackfire → Ionian → Liandry → Rylai → Void**

**Arcane Comet · Manaflow Band · Transcendence · Gathering Storm · Cut Down**

Lane (minutes 1–10): **Aery · Manaflow · Transcendence · Scorch · Cut Down** (or keep Comet + Scorch).

Skill order: **Q → E**, W 1-point, R at 5/9/13.

| When | Spike |
|------|--------|
| ~7:00 | **Blackfire** — second DoT + 20 AH (mid gold actually finishes this) |
| ~8:00 | **Ionian** — stay here; do not rush Spellslinger |
| ~13:00 | **Liandry** — the %HP burn |
| ~16:00 | **Rylai** — lock |
| ~20:00 | **Void** — tank spike (cheap boots bought this time) |

Spellslinger is the **22:00 peak** if the lock is already done and gold is left. Zhonya is a 4th-item survive swap vs Zed/Fizz/Kat. Oceanid vs shield comps.

## Why the roles split

- Support gold cannot finish Liandry + Rylai + Blackfire in 20 minutes. Mid gold can.
- Ionian (1000g) beats Mana boots on both curves because the extra items land sooner. That matches the live 80% Ionian pick.
- Mid wants to **stay on Ionian** until Rylai + Void are done. Spellslinger's 18 + 8% pen is a late upgrade, not a rush.
- Do not build "for Comet". Comet is extra on the root after the 7.2 5% AP nerf. Gathering Storm only wins a 22-minute mid average.

## Traps

- **Support:** Blackfire before Rylai → paper burn, they walk out.
- **Support:** Rylai first → you miss the ~9:00 Liandry spike.
- **Support:** Mandate first → 7.3's "CC-mage" playstyle, but it delays %HP burn. 3rd/4th only if the ADC follows the mark.
- **Mid:** BF → Liandry → Zhonya (popular live) survives assassins and loses harass to Rylai.
- **Mid:** Rushing Spellslinger/Crimson delays the Rylai lock and the Void spike.
- **Both:** Botanist does **not** buff Thorn Spitters. It is river plants.
- **Both:** Gathering Storm is a 20-minute trap on support.
