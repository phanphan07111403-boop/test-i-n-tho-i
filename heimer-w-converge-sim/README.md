# Heimerdinger W — Auto-aim tụ tên lửa vào tướng

Wild Rift patch **7.1g+**. Trả lời: auto-aim luôn lấy tướng làm điểm hội tụ cả 5 rocket thì **có tác dụng không, có lời không**.

## Run

```bash
python3 simulate_heimer_w_converge.py
```

Outputs:

- `report.txt` — verdict + damage theo mốc lane/mid/late
- `results.json` — số liệu từng kịch bản

## Verdict

**Có tác dụng, và có lời — nhưng chỉ khi poke / all-in 1 tướng.**

Auto-aim lock tướng đặt điểm hội tụ đúng lên người đó, nên cả 5 rocket cùng lúc. Đó là max single-target của W:

| Hits | Damage vs 1 rocket | Beam charge |
|------|--------------------|-------------|
| 1 | 1.00× | 20% |
| 5 (auto-aim tụ) | **1.80×** | **100% → laser ngay** |

Không phải 5×. Rocket 2–5 chỉ 20% mỗi quả. Lời lớn là **instant laser trụ** (passive phải ~90s mới đầy từ 0%).

Combo **E stun → W tụ 5/5** còn lời hơn: E đã nạp 100% laser lần 1; W 5 quả nạp lại 100% từ 0% → **laser lần 2**. W chỉ 1 quả thì mất laser #2.

**Không lời** nếu để auto-aim tướng mọi lúc:

- Clear lính cần xòe (mỗi lính ăn first-hit 100%; tụ 5 quả vào 1 lính ~2.4× không phải 5×).
- Tướng núp wave → rocket đấm lính.
- Teamfight 3 người: 3× first-hit > 1 người ăn 1.8×.
- Không CC: auto-aim không lead, dễ miss cả volley.

## Luật dùng

1. Poke 1 người, line sạch / vừa last-hit / sau E stun → **giữ auto-aim tụ tướng**.
2. Clear wave, check bụi → **kéo aim xa** cho rocket xòe.
3. R+W chỉ burst khi tụ đủ 20 quả vào 1 mục tiêu (E trước).
