# MooWii: L1 charge skill 1, vẫn đi được

Giữ **L1** = charge skill 1. Thả **L1** = cast. Stick trái vẫn đi trong lúc đang đè.

Game (Tốc Chiến / Liên Quân) đã cho phép vừa đi vừa tụ chiêu. Cái kẹt nằm ở app map phím: L1 đang **cướp cùng một ngón ảo** với joystick, hoặc L1 không phải kiểu nhấn-giữ.

## Chỉnh đúng (Android)

1. Vào trận tập / màn hình skill, bấm bong bóng **MooWii** → **Điều chỉnh cấu hình**.
2. Kéo **Joystick** vào bánh xe đi (góc dưới trái). Loại phím phải là **Joystick**, không phải 4 nút WASD.
3. Kéo **L1** đúng tâm icon **skill 1**.
4. **Bấm đúp L1** → thuộc tính phím → chọn **Gán phím** (Normal / 普通).
   - Nhấn L1 = ngón ảo **DOWN** trên skill 1 (bắt đầu charge).
   - Giữ L1 = ngón đó **không nhấc**.
   - Thả L1 = **UP** (cast).
5. Tắt mọi thứ biến L1 thành macro / nhấp / vuốt / phím bắn / “liên kết joystick”.
6. **Lưu**. Bật **Kiểm tra phím** và test:
   - Đè L1: chấm đứng yên trên skill 1.
   - Vẫn đè L1, gạt stick: **chấm thứ hai** chạy trên bánh xe đi.
   - Thả L1: chấm skill 1 biến mất, tướng vẫn đi.

Hai chấm cùng lúc = xong. Một chấm nhảy qua lại = vẫn sai.

## Không dùng các kiểu này cho L1

| Trong app | Vì sao hỏng |
|---|---|
| Nhấp liên tục | Spam tap, không tụ lực |
| Vuốt thẳng / Click on the straight | Vuốt theo thời gian cố định, không theo lúc bạn giữ, và chiếm pointer |
| Phím bắn | Dành FPS, tap/recoil thay vì hold |
| Macro / ghi âm macro | Chạy chuỗi một ngón, stick bị ngắt đến khi macro xong |
| Skill joystick ăn stick trái | Đè L1 thì stick trái đổi thành aim chiêu → **đúng bug bạn đang gặp** |
| Tay cầm **một bên / single-side** | Một stick dùng chung. Đổi sang **hai bên / dual-side** |

Bán kính L1 để nhỏ, chỉ che icon skill 1. Bán kính to dễ đè lên vùng đi hoặc vùng aim.

## iPhone / iPad

MooWii trên iOS map bằng chuột ảo / AssistiveTouch: **chỉ một ngón**. Đè L1 là hết slot, stick không đi được lúc đang charge. Đây là giới hạn hệ thống, không phải skill trong game.

Muốn vừa đi vừa tụ chiêu: dùng **Android** (overlay đa điểm). Trên iOS chỉ đi được khi không giữ L1, hoặc chấp nhận đứng tụ rồi thả.

iOS 17+: bật AssistiveTouch + khóa xoay màn hình. iOS 16-: tắt home ảo, vẫn khóa xoay. Các bước này chỉ cho map phím chạy, **không** thêm ngón thứ hai.

## File trong thư mục này

- `mapping-profile.json` — cấu hình chuẩn L1 hold + stick độc lập
- `diagnose.py` — kiểm tra profile có bị type cấm không
- `guide.html` — mô phỏng 1 ngón (hỏng) vs 2 ngón (đúng)

```bash
python3 diagnose.py
python3 test_diagnose.py
```
