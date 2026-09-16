# D-pad Tốc Chiến (Wild Rift)

Tốc Chiến **không** có native gamepad. D-pad trên GameSir / MB03 / MooWii là **4 nút tap HUD**, không phải WASD.

**Đừng gán D-pad vào bánh xe đi.** Stick trái đã là analog. D-pad 8 hướng làm đi giật, kite hỏng, Sion Q lệch.

## Layout mặc định: tiện ích lane

Ngón cái trái giữ stick. D-pad = 4 nút nhỏ khó chạm khi đang kẹp máy.

| D-pad | HUD Tốc Chiến | Việc |
|---|---|---|
| **↑** | Bảng điểm | Nhìn CD chiêu, máu, stack Heartsteel trên bảng |
| **↓** | Hồi thành | Ngón cái không rời stick |
| **←** | Đánh lính / quái | Last-hit, không cướp AA tướng |
| **→** | Đánh trụ / cây | Siege, không dính tướng dưới trụ |

Cả bốn: **Gán phím / Normal** (DOWN khi nhấn, UP khi thả). Không Turbo, không Cloned, không Macro, không Joystick.

## Layout khác (đổi khi cần)

**Cộng skill** (giống giả lập LDPlayer: D-pad = nâng QWER):

| ↑ | ← | ↓ | → |
|---|---|---|---|
| +Q | +W | +E | +R |

Dùng lúc hồi thành / base, không phải lúc 5v5. Trong teamfight dễ bấm nhầm **cộng skill** thay vì đánh lính.

**Khóa chân dung** (Sion Heartsteel): ↑↓←→ = chân dung tướng 1–4. Tướng 5 để L3. Chỉ khi bạn đã bật Portrait Lock.

Chọn **một** layout. Bốn hướng trộn “lính + cộng Q + chân dung” là loạn.

## Cách gán

### GameSir World (G-Touch / V-Touch)

1. Mở game từ app, icon nổi → **调整键位**.
2. **Add Button** / thêm phím, bấm **D-pad ↑** trên tay, kéo chấm lên icon bảng điểm.
3. Lặp ↓ hồi thành, ← đánh lính, → đánh trụ.
4. ⚙️ từng phím → **Click Mode = Normal**. Lưu.

### MooWii (MB03)

1. Bong bóng → **Điều chỉnh cấu hình**.
2. Kéo 4 hướng D-pad (hoặc nút điều hướng) lên đúng icon HUD.
3. **Bấm đúp** từng hướng → **Gán phím**. Tắt nhấp liên tục / macro / vuốt.
4. **Kiểm tra phím**: bấm ↑ chỉ một chấm trên bảng điểm, stick trái vẫn đi.

### HUD trong game (không phải tay cầm)

**Cài đặt → Điều khiển → Tùy chỉnh bố cục nút.** Chọn một nút, dùng **D-pad Position** + tọa độ X/Y để nhích từng pixel — để 4 icon lính/trụ/hồi thành/bảng điểm **cách đều, không chồng skill**. Gán tay cầm xong mới chỉnh HUD, không ngược lại.

## Cấm

| Gán D-pad vào | Vì sao hỏng |
|---|---|
| Bánh xe đi / Joystick | Trùng stick trái, đi 8 hướng |
| Skill 1–4 | Trùng L1/R1, mất analog aim |
| Cloned Mode hai HUD | Một hướng bấm hai chỗ, last-hit loạn |
| Đường chéo (↑+→ cùng lúc) | Hai tap chồng. Tắt analog D-pad nếu app có |

iOS: mapping D-pad được, nhưng một ngón ảo — đừng giữ D-pad lúc đang charge skill.

```bash
python3 diagnose.py
python3 test_diagnose.py
```
