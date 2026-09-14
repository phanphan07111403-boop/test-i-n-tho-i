# Viktor mid — magic pen / burst vs Blackfire + Liandry

Wild Rift **7.2e**. **Mid**, E-max. Game **20 phút**.

Không copy PC (Shadowflame / Sorcs). Không copy jungle/support. Cùng **Spellslinger** trên cả hai nhánh — 7.2 T3 mage = **0% pen**.

## Run

```bash
python3 simulate_viktor.py
```

Outputs: `report.txt`, `results.json`

## 4 ô

| Ô | Khóa |
|---|------|
| Client | Tốc Chiến 7.2e. Pen sống ở Spellslinger / Void / Cryptbloom / Bloodletter / Orb 15 flat. |
| Role | Mid. E waveclear. Không Smite, không Scythe. |
| Cặp | **Luden → Infinity Orb → Cap** vs **Blackfire → Liandry → Void**. Constraint: poke E full HP vs all-in 5.5s (R). |
| Metric | Poke squishy, all-in squishy, all-in tank. Không dùng Diamond+ WR làm winner. |

Diamond+ (2026-09-06): Luden→Orb→Cap **54.66% WR / 25% pick**; BF→Liandry→Void **51.91% WR / 7.6% pick**. WR so với cả pool mid, không phải cặp này. Mercury 39% pick so Ionia = **A vs C**, bỏ.

## Hai path (5 ô)

**A — burst / execute (gọi “magic pen” vì Orb 15 flat + Spellslinger)**  
Spellslinger · Luden's Echo · Infinity Orb · Deathcap

| Spike | Món |
|-------|-----|
| ~8:00 | **Luden** — Echo 140+15% AP / 9s. 0% pen (T3 stripped). |
| ~13:00 | **Infinity Orb** — 110 AP + 15 flat + 20% khi &lt;35% HP |
| ~15:00 | **Spellslinger** |
| ~20:00 | **Deathcap** |

**B — BF + Liandry**  
Spellslinger · Blackfire · Liandry · Void Staff

| Spike | Món |
|-------|-----|
| ~8:00 | **Blackfire** — 20+2% AP/s, 20 AH (nhiều E hơn) |
| ~13:00 | **Liandry** — 2% max HP/s |
| ~15:00 | **Spellslinger** |
| ~19:00 | **Void** — 40% pen |

## Winner theo metric (sim)

| Metric | Thắng | 20 phút |
|--------|--------|---------|
| E poke squishy (full HP) | **Pen / Luden+Orb** | Burn **−9.6%** |
| All-in 5.5s squishy | **Pen / Luden+Orb** | Burn **−8.2%** |
| All-in 5.5s tank | **Burn / BF+Liandry+Void** | Burn **+2.2%** |
| E/phút @20 | Burn (11.3 vs 10.5) | BF 20 AH vs Luden 10 |

Orb execute **không** giúp poke full HP (chưa xuống 35%). Echo + AP + flat pen thắng poke. Liandry + R 5.5s + Void thắng tank **muộn** (Void ~19:00). Phút 8–15 pen vẫn hơn cả tank vì Luden spike.

Pen đổi Cap → Void: tank all-in 20p **23909** vs Burn Void **24174** — Liandry vẫn hơn một nhịp. Burn đổi Void → Cap: thua tank.

## Khi nào lên gì

- Lane poke, đội squishy, cần Echo/execute → **Luden → Orb → Cap**.
- 2+ tank, fight kéo quanh R → **BF → Liandry → Void**.
- Spellslinger **cả hai** path. Core 7.2 không có 7% pen.
