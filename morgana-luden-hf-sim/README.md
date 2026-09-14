# Morgana Luden — Horizon Focus giúp hay bỏ?

Wild Rift **7.2e**. Mid, Dark Harvest, **maximize damage** trên lối **Luden**. 5 slot: Spellslinger · Luden · A · B.

HF **không ngồi thêm**. Mua HF = thế **Orb** hoặc thế **Cap**.

## Run

```bash
python3 simulate_morgana_luden_hf.py
```

## 4 ô

| Ô | Khóa |
|---|------|
| Client | Tốc Chiến 7.2e. HF = Hypershot +10%/8s sau ability ≥600. Không PC immobilize proc. |
| Role | Mid Luden. Maximize = burst combo **và** poke DPM. |
| Cặp | Luden→Orb→Cap vs Orb→HF vs HF→Cap vs HF→Orb |
| Metric | Combo 70%+R, 40%+R. Poke DPM 90% HP, Q spam 60s, Echo 10s. Hit apply HF **không** amp. R melee không apply. |

HF 7.2: **2700g, 80 AP, 25 AH, 7% pen**. 2× Codex (25 AP / 10 AH / 900) + Tome.

## Horizon Focus giúp hay bỏ?

**Burst/all-in: không mua. Poke Q spam: mua HF thay Orb, giữ Cap.**

Luden Echo nằm trên Q. Hypershot apply bằng Q nên **Q+Echo không ăn +10%**. R Soul Shackles melee không apply. 7% pen thua Orb 15 flat trên squishy đã có Spell 18+8%.

25 AH là chỗ HF thật sự trả tiền: 8.6 → **10.3 Q/phút**, và Q sau (CD ~5.8s < mark 8s) mới ăn 10%.

## Sim (20:00 vs Luden→Orb→Cap)

| Path | Combo 70%+R | Poke DPM | Spike T4 |
|------|-------------|----------|----------|
| **Luden → Orb → Cap** | **2134** | 6580 | Cap ~20 |
| Luden → Orb → HF | 1932 (**−9.5%**) | 7452 (+13.3%) | HF ~19 |
| **Luden → HF → Cap** | 1812 (**−15.1%**) | **7758 (+17.9%)** | Cap ~20 |
| Luden → HF → Orb | 1932 (−9.5%) | 7452 (+13.3%) | Orb ~19 |

Diện tích 20p combo70: Orb-HF **−1.3%**, HF-Cap **−8.6%**. Poke DPM 20p: HF-Orb **+14.4%** (Orb xong ~19), HF-Cap **+13.5%**; phút 20 snapshot HF-Cap vẫn cao hơn (Cap 30% AP).

## Khi nào lên gì

- Maximize **một combo** (Q+Echo+W+R, gank/all-in) → **Luden → Orb → Cap**. Bỏ HF.
- Maximize **poke Q** (Luden identity, chip 90%) → **Luden → HF → Cap**. HF thay Orb.
- Đừng HF thế Cap nếu vẫn all-in: −9.5% burst để lấy AH.
- Focus reveal 1200 không phải damage — không cứu slot burst.

Luden ~8 · Orb/HF ~13 · Spell ~14–15 · Cap ~20 / HF-as-T4 ~19.
