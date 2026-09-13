# Morgana mid — Ionian vs Boots of Mana (có farm)

Wild Rift **7.2e**. Cùng core Blackfire → Liandry → Rylai, **chỉ đổi dòng giày**. Game **20 phút**.

Lần trước chọn Ionia vì Diamond+ WR và Q haste — **không mô hình farm mid**.

## Run

```bash
python3 simulate_morgana_boots.py
```

Outputs:
- `report.txt` — vàng/OOM/combo từng phút + verdict
- `results.json` — snapshot theo build

## Câu hỏi

Morgana **mid** vẫn lên Ionia thay vì Boots of Mana? Farm (CS, Big Bully, mana W-max) có đổi kết quả không?

## Winner (sim)

**Mid: Boots of Mana → Spellslinger's Shoes**

Combo Q+W+burn 20 phút **+10.2%** vs Ionia → Crimson (thắng 18/20 phút). Gold @20 **+1084g** (Big Bully +996, bớt miss CS +88).

Ionia vẫn hơn **+13.4% Q/phút** và Flash 120s vs 150s. Đó là lý do support/all-in, không phải lý do farmer mid.

| Khi | Spike Mana path |
|-----|-----------------|
| ~3:00 | **Boots of Mana** — regen + 8 pen + Big Bully |
| ~8:00 | **Blackfire** |
| ~13:00 | **Liandry** (Ionia ~14:00) |
| ~15:00 | **Spellslinger** — 18 pen + 8% pen |
| ~19:00 | **Rylai** (Ionia ~20:00) |

## Farm đổi kết quả vì

1. Mid W-max **mỗi wave**. Ionia T2 = 0% mana regen → OOM phút 1–4, mất CS.
2. Big Bully + 25 AP last-hit wave; Ionia không.
3. +200g T2 ≈ nửa wave mid, không phải “đắt” như support.
4. Patch **7.2 rút 7% pen** khỏi Liandry/Rylai/Cap. Core burn = **0 pen** nếu không Spellslinger.
5. Blackfire 20 AH + Transcendence 12 đã che mất 15 AH Ionia. Thêm Q không bù W+%HP khi có pen.

## Số liệu ranked (không thay sim)

- Diamond+ mid **Ionia 56.98% WR / 68.25% pick** — bảng so với **Mercury**, không có WR Boots of Mana.
- Diamond+ **support Ionia 92% pick** — đừng copy sang mid.
- wrchina Top-30 (19 build, 2026-09-11): **Spellslinger 63% / Crimson 32%**.

## Support (đối chứng)

Cùng 2 dòng giày, **không CS**. Spellslinger vẫn +5% combo vì pen, nhưng 20 phút không xong Liandry ở cả hai nhánh — 200g không mua thêm món. Q/Flash là lý do Ionia support.

## Khi nào vẫn Ionia mid

- Cần Flash-R / MS Crimson (all-in, bị gank).
- Đã đấm Ionia T2 — không cross-upgrade được.
- Peel Q+E quan trọng hơn damage.
