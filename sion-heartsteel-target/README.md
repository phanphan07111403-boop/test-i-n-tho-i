# Sion Heartsteel Tốc Chiến — không có mode ưu tiên proc

**Không.** Tốc Chiến không có chế độ đánh thường “ưu tiên tướng đang có Heartsteel”.

Heartsteel (**Tiêu thụ khổng lồ / Colossal Consumption**, WR 6.0+): đứng trong **700** tầm của **tướng địch** **2.5s** → **đánh thường** đúng tướng đó. **20s hồi chiêu theo từng tướng**. Q Sion **không** proc (Q là chiêu, không phải đánh thường). Đánh lính cũng không tiêu thụ mark.

Ưu tiên tấn công trong Cài đặt chỉ đọc **máu** hoặc **khoảng cách**. Cộng đồng tank đã xin nút “AA ưu tiên mark Heartsteel”; Riot chưa thêm.

## Cài gần nhất (vẫn phải tự chọn tướng có mark)

**Cài đặt → Điều khiển**

| Mục | Chọn | Lý do |
|---|---|---|
| Khóa mục tiêu / Portrait Lock | **Bật**, **Fixed Display** | Chạm **chân dung** tướng đang đầy mark. Đây là cách duy nhất ưu tiên proc. |
| Bộ lọc khóa mục tiêu | **Không lính/trụ** | Kéo nút đánh thường không nhảy sang lính. |
| Ưu tiên tấn công | **Gần nhất** (Sion cận chiến) hoặc Máu thấp tuyệt đối | Cả hai **không** biết mark. Gần nhất = spam tank trước mặt dù tank đang CD 20s. |
| Đeo theo đòn tấn công | **Tắt** | Kéo bạn vào đúng người auto chọn, thường là tank đã proc. |

Trong giao tranh: nhìn mark trên tướng → chạm chân dung (vàng) → đánh thường một cái → đổi chân dung tướng khác đã đầy mark.

## Vì sao auto hỏng

Một trận 40s, 5 tướng đều trong 700 sau 2.5s:

- Auto **gần nhất** → chỉ proc **tank**, 2 lần / 40s, **+76 HP**.
- Auto **máu thấp** → bám **ADC**, vẫn 1 người, **+76 HP**.
- **Khóa chân dung xoay mark sẵn** → 10 proc / 5 tướng, **+387 HP** (~5.1× auto).

```bash
python3 simulate_heartsteel_target.py
python3 test_simulate.py
```

## Tay cầm (GameSir / MooWii)

**Cloned Mode không giúp.** Clone là hai chấm HUD cùng lúc, không đọc mark đồ.

Map nút phụ (L4/R4) vào **chân dung tướng 1–5** thì khóa người có mark nhanh hơn, vẫn là bạn chọn, không phải chế độ Heartsteel.

Chi tiết số: `report.txt` / `results.json`. Cài đặt máy: `settings.json`.
