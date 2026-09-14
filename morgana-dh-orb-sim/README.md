# Morgana Dark Harvest — BF→Orb→Cap vs BF→Orb→Void

Wild Rift **7.2e**. Mid gold, keystone **Dark Harvest**. 5 slot: Spellslinger · Blackfire · Infinity Orb · **Cap hoặc Void**. Teamfight **BF 5 stack**.

Không copy support Ionia WR. Không copy PC Shadowflame / Sorcs.

## Run

```bash
python3 simulate_morgana_dh_orb.py
```

## 4 ô

| Ô | Khóa |
|---|------|
| Client | Tốc Chiến 7.2e |
| Role | Mid + DH execute. W-max farm. |
| Cặp | **BF → Orb → Cap** vs **BF → Orb → Void** trên đội **5 squishy** và **4 squishy + 1 tank** |
| Metric | TF: Q carry + W/R splash, 70% HP, R on, BF 5 stack. Orb chỉ amp hit khi **đã** &lt;35%. Full item 20:00 và diện tích 20p. |

## Cap hay Void?

**5 squishy → Cap. 4 squishy + 1 tank → gần hòa; 1 tank không đủ bắt Void.**

Spellslinger 18 flat + 8% và Orb 15 flat đã gần cap effective MR của squishy. Cap 30% amp trên đống AP BF5×Orb. Void 40% pen chỉ trả tiền trên tank.

Cả hai T4 xong **cùng phút 20** trên gold mid (Void rẻ hơn 400g nhưng không xong phút 19). Phút 16 Cap ngồi Blasting Wand; phút 17 Void ngồi Amethyst 10%.

## Sim (20p)

| Metric | BF→Orb→**Cap** | BF→Orb→**Void** | Void vs Cap |
|--------|----------------|-----------------|-------------|
| 1 squishy 20:00 | **2137** | 2104 | −1.6% |
| 1 tank 20:00 | 1154 | **1356** | **+17.5%** |
| Đội 5 squishy 20:00 | **6706** | 6686 | −0.3% |
| Đội 4 sq + 1 tank 20:00 | 6156 | **6230** | **+1.2%** |
| Diện tích 5 squishy 20p | **62439** | 61803 | −1.0% |
| Diện tích 4+1 20p | **58801** | 58313 | −0.8% |

Spike: BF ~8 · Orb ~13 · Spell ~15 · Cap/Void ~20.

## Khi nào lên gì

- Đội 5 squishy (Q vào carry) → **Cap**.
- Đội 4 squishy + 1 tank, Q vào carry → **Cap mặc định**. Void chỉ +1.2% lúc full item; diện tích 20p vẫn Cap vì Wand ngồi sớm hơn.
- 2+ tank / stacked MR / bạn Q-W thẳng tank → **Void**.
- Cryptbloom = Void nhẹ (30% + AH), không thay Cap 5sq.
- W-zone người còn máu, không execute → **BF → Liandry → Rylai** (không phải câu Cap vs Void).

## Context: DH vs Rylai (1 squishy, 1 stack BF)

| Metric | BF→Liandry→Rylai | **BF→Orb→Cap** | Luden→Orb→Cap |
|--------|------------------|----------------|---------------|
| Combo 70% + R | 17481 | **18515 (+5.9%)** | 20366 (+16.5%) |
| Combo 40% + R | 18506 | **19923 (+7.7%)** | 21252 (+14.8%) |
| Combo 90% no R | **10901** | 10792 (−1.0%) | 12924 |
| DH@90% phút 12–20 | **2.0** | 1.0 | — |

DH hợp tầng execute (70%/40%), không hợp tầng “W hạ máu” (90%). Jungle DH vẫn cần Rylai hơn mid.
