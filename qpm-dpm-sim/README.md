# Maximize damage — Spellslinger vs Crimson

Wild Rift **7.2e**. Mid. Bỏ vàng. Maximize **DPM** poke (không phải QPM).

- Morgana: Dark Binding 60s, 90% HP.
- Viktor: Death Ray (E), không phải Q Siphon.

Spellslinger: 40 AP, 18 flat, 8% pen, 0 AH.  
Crimson Lucidity: 0 AP, 0 pen, **25 AH**, 8% MS.

## Run

```bash
python3 simulate_qpm_dpm.py
```

## 4 ô

| Ô | Khóa |
|---|------|
| Client | Tốc Chiến 7.2e. Không copy support Ionia WR. |
| Role | Mid. Bỏ gold. |
| Cặp | Spell vs Crimson: (1) cùng 4 đồ (2) 4 đồ tốt nhất dưới từng giày |
| Metric | DPM poke squishy 90%. CPM chỉ giải thích AH. |

## Maximize damage → Spellslinger

| | Morgana DPM | Viktor DPM |
|--|-------------|------------|
| **Best Spell** (Luden·HF·BF·Crypt) | **10558** | **13490** |
| Best Crimson (HF·BF·Crypt·Liandry) | 9511 (**−9.9%**) | 12019 (**−10.9%**) |
| Crimson trên 4 đồ Spell | 8919 (**−15.5%**) | 11733 (**−13.0%**) |

Cùng 4 đồ Spell-max: Crimson **+13.4%** casts, **−25% / −23%** damage mỗi cast → thua DPM.

Crimson tự đổi 4 đồ (bỏ Luden, lấy Liandry) vẫn thua ~10%. 18 flat + 8% + 40 AP > 25 AH trên squishy.

Crimson chỉ khi metric là spam QPM/EPM, không phải maximize damage.
