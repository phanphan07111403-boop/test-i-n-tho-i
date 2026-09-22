# Top 5 hỗ trợ Tốc Chiến 7.3 — hưởng patch + fit pad

Patch **7.3** (22/09/2026). ADC crit 175%→**200%**, AS cap 2.5→**3**, đồ xạ thủ làm lại. Đồ hỗ trợ: **Echoes of Helia**, Ardent Censer 30% AS + 25 on-hit, Diadem of Songs, **Yordle Trap** cho AS đồng đội khi CC.

Pad = GameSir / **MB03** (gồng / xả Q / combo 2–4 nút) + D-pad `←` lính / `→` trụ / `↓` hồi / `↑` bảng.

## Run

```bash
python3 simulate_support_73.py
python3 test_support_73.py
```

Outputs:
- `report.txt` — ranking + vì sao từng tướng
- `results.json` — snapshot 8/12/16/20

## Câu hỏi

Support nào **hưởng nhiều nhất update 7.3**, và **đánh được trên pad**?

## Winner (sim)

| # | Tướng | Vì sao 7.3 | Pad |
|---|--------|------------|-----|
| 1 | **Lulu** | Ardent 2400g + W 25–40% AS trên ADC crit 200%. Pix on-hit. | W/E/R lock, Relic `←` |
| 2 | **Leona** | Yordle Trap 20% AS khi CC. 2v2 khi jungle farm. WRF S. | E→Q đã dạy |
| 3 | **Milio** | Fired Up! (Ardent gắn kit) + tầm đánh + Helia. | E/W tether, Q optional |
| 4 | **Braum** | Giữ E chặn crit 200%. Q slow proc Trap. WRF S. | Gồng E, W lock |
| 5 | **Sona** | Helia (Q→heal) + Tear/Circlet/Diadem. WRF S. | Xả QWE, không aim |

Không vào top dù meta: **Nami** (bong bóng), **Thresh** (móc+đèn), **Pyke** (không buff ADC).

## Build nhanh

- Lulu: Relic → Ionia → **Ardent** → Harmonic Echo
- Leona: Relic → Steelcaps → **Yordle Trap** → Mantle
- Milio: Sickle → Ionia → **Helia** → Harmonic → Ardent
- Braum: Relic → Steelcaps → Vow → **Yordle Trap**
- Sona: Sickle → Ionia → Tear → **Helia** → Circlet (Ardent nếu 20+)
