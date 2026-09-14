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
| Cặp | **Luden → Orb → Cap** vs **BF → Liandry → Void** vs **BF → Orb → Cap**. Poke E vs all-in 5.5s. |
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

**C — hybrid BF → Orb → Cap**  
Spellslinger · Blackfire · Infinity Orb · Deathcap

| Spike | Món |
|-------|-----|
| ~8:00 | **Blackfire** |
| ~13:00 | **Infinity Orb** |
| ~15:00 | **Spellslinger** |
| ~20:00 | **Deathcap** |

Burn + 20 AH + execute + Cap. Không Echo, không Liandry, không Void.

## Winner theo metric (sim)

| Metric | Pen Luden+Orb | Hybrid BF+Orb+Cap | Burn BF+Liandry+Void |
|--------|---------------|-------------------|----------------------|
| E poke squishy | **8834** | 7736 (−12.4%) | 7982 (−9.6%) |
| All-in 5.5s squishy | **32556** | 31595 (−3.0%) | 29891 (−8.2%) |
| All-in 5.5s tank | 23643 | 22987 (−2.8%) | **24174 (+2.2%)** |
| E/phút @20 | 10.5 | 11.3 | 11.3 |

**BF→Orb→Cap không phải best of both.** Poke thua Luden (mất Echo; Liandry 3s poke còn hơn Orb trên full HP). Tank thua BF+Liandry+Void (mất %HP và Void). All-in squishy gần Luden (−3%) nhờ Orb execute + BF burn + Cap.

## Khi nào lên gì

- Lane poke, đội squishy → **Luden → Orb → Cap**.
- 2+ tank, fight kéo quanh R → **BF → Liandry → Void**.
- **BF → Orb → Cap** chỉ khi đã đấm BF (AH/clear) rồi muốn execute, chấp nhận thua hai đầu. Đừng pick sẵn như “cả burn lẫn pen”.
- Spellslinger **mọi** path. Core 7.2 không có 7% pen.
