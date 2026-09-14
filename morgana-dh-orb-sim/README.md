# Morgana Dark Harvest — BF→Orb→Cap có hợp không?

Wild Rift **7.2e**. Thay Viktor: **mid** gold, keystone **Dark Harvest**. Game 20 phút. Cùng Spellslinger (T3 mage = 0% pen).

Không copy support Ionia WR. Không copy PC Shadowflame. Jungle DH vẫn cần Rylai hơn mid (gank người chưa thê).

## Run

```bash
python3 simulate_morgana_dh_orb.py
```

## 4 ô

| Ô | Khóa |
|---|------|
| Client | Tốc Chiến 7.2e |
| Role | Mid + DH execute. W-max farm. |
| Cặp | **BF → Liandry → Rylai** vs **BF → Orb → Cap** vs Luden → Orb → Cap |
| Metric | Combo 70% (cửa DH), 40% (DH+Orb chồng), 90% (dwell tạo cửa). Orb chỉ amp hit khi **đã** &lt;35%. |

## Có hợp DH không?

**Hợp tầng execute, không hợp tầng “W hạ máu”.**

- DH nổ khi &lt;50%. Orb +20% khi **đã** &lt;35%. Gank 70%: Q+DH bắn lúc ~50% — OrbHits lúc Q = 0. Orb chỉ buff W/R sau khi chúng rơi tiếp.
- Gank 40%: Orb amp cả Q+DH. Đây là lúc BF→Orb→Cap thật sự khớp DH.
- Gank 90%: Rylai giữ W để **tạo** cửa 50%. BF-Orb DH@90% phút 12–20 = **1.0 vs 2.0**.

## Sim (20p)

| Metric | BF→Liandry→Rylai | **BF→Orb→Cap** | Luden→Orb→Cap |
|--------|------------------|----------------|---------------|
| Combo 70% + R | 17481 | **18515 (+5.9%)** | 20366 (+16.5%) |
| Combo 40% + R | 18506 | **19923 (+7.7%)** | 21252 (+14.8%) |
| Combo 90% no R | **10901** | 10792 (−1.0%) | 12924 |
| DH@90% phút 12–20 | **2.0** | 1.0 | — |

Spike: BF/Luden ~8 · Orb/Liandry ~13 · Spell ~15 · Rylai ~19 · Cap ~20.

## Khi nào lên gì

- DH chỉ gank lane đã thê (70%/40%) → **BF → Orb → Cap** hợp (thậm chí hơn Rylai paper).
- Cần W-zone người còn máu → **BF → Liandry → Rylai**.
- Poke/Echo mid như Viktor → **Luden → Orb → Cap** (paper cao nhất, không bắt buộc DH).
- Jungle DH: ưu tiên Rylai hơn mid — camp không proc DH, gank hay gặp laner 80–90%.
