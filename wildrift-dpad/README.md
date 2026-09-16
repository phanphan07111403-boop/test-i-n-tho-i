# D-pad Tốc Chiến (Wild Rift)

Tốc Chiến **không** có native gamepad. D-pad trên GameSir / MB03 / MooWii là **4 nút tap HUD**, không phải WASD.

**Đừng gán D-pad vào bánh xe đi.** Stick trái đã là analog. D-pad 8 hướng làm đi giật, kite hỏng, Sion Q lệch.

Thứ tự bắt buộc: **chỉnh HUD trong game trước**, rồi mới kéo D-pad lên đúng icon. Map ngược lại thì chấm cảm ứng rơi vào chỗ trống.

## Layout mặc định: tiện ích lane

Ngón cái trái giữ stick. D-pad = 4 nút nhỏ khó chạm khi đang kẹp máy.

| D-pad | HUD Tốc Chiến | Việc |
|---|---|---|
| **↑** | Bảng điểm | Nhìn CD chiêu, máu, stack Heartsteel trên bảng |
| **↓** | Hồi thành | Ngón cái không rời stick |
| **←** | Đánh lính / quái | Last-hit, không cướp AA tướng |
| **→** | Đánh trụ / cây | Siege, không dính tướng dưới trụ |

Cả bốn: **Gán phím / Normal** (DOWN khi nhấn, UP khi thả). Không Turbo, không Cloned, không Macro, không Joystick, không analog D-pad.

## Bước 0 — HUD trong Tốc Chiến (trước khi map tay cầm)

Hai icon lính / trụ nằm sẵn cạnh nút đánh thường: **trụ phía trên, lính phía dưới**. Nếu chúng chồng skill hoặc quá nhỏ, D-pad sẽ tap nhầm.

1. Lobby: **Cài đặt → Điều khiển → Tùy chỉnh bố cục nút**.
2. Kéo 4 icon ra chỗ **trống, cách đều**, không đè skill / hồi thành / shop.
3. Ghi tọa độ X/Y nếu editor có — để map tay cầm khớp từng pixel.
4. **Lưu**. Có thể giữ 3 layout; layout tay cầm nên tách khỏi layout ngón tay.

Chỉ sau bước này mới mở editor GameSir / MooWii.

## Cách gán

### GameSir World (G-Touch / V-Touch)

1. Android. Mở Tốc Chiến **từ GameSir World**, mode **Hardware Mapping (G-Touch)** (ưu tiên) hoặc V-Touch.
2. Icon nổi → **Adjust buttons / 调整键位**.
3. **Add Button / 添加按键** (nút tròn thường). **Không** chọn Add D-pad / 十字键.
4. Bấm **một** hướng trên D-pad vật lý (↑). Phải ra **chấm tròn**, không phải chữ thập. Kéo lên icon **bảng điểm**.
5. Lặp ↓ hồi thành, ← đánh lính, → đánh trụ — mỗi hướng một chấm riêng.
6. ⚙️ từng chấm (nếu mở được) → **Click Mode = Normal**. Tắt Turbo / Cloned / Macro / Skill Wheel. Lưu.

Nguồn Click Mode: [FAQ GameSir — mapping extra features](https://gamesir.com/support/faq) (Normal = một tap). iOS 13.4+ không map G-Touch/V-Touch.

#### Lỗi: *Property setting is not available for D-pad button*

Không phải hỏng tay cầm. ⚙️ / Click Mode **chỉ có trên nút thường (常规键)**. Chữ thập D-pad là widget analog — app từ chối property.

Làm ngay:

1. Trong **调整键位**, kéo **chữ thập D-pad** vào thùng rác / ô xóa. Đừng bấm ⚙️ trên nó.
2. **Add Button**, không Add D-pad.
3. Bấm dứt khoát **một** hướng (đừng lướt ngón). Nếu lại ra chữ thập → xóa, thêm lại.
4. Bốn chấm tròn lên bốn icon HUD. Mặc định đã là Normal tap — **không cần ⚙️** nếu chỉ tap HUD.

Không tách được 4 nút thì để D-pad trống: dùng L3/R3 hoặc M1/M2 cho hồi thành / bảng điểm, last-hit bằng nút đánh thường. Đừng gán chữ thập vào bánh xe đi.

### MooWii (MB03)

1. Bong bóng → **Điều chỉnh cấu hình**.
2. Kéo 4 hướng D-pad (nút điều hướng) lên đúng 4 icon vừa chỉnh.
3. **Bấm đúp** từng hướng → **Gán phím**. Tắt nhấp liên tục / macro / vuốt / analog hat.
4. **Kiểm tra phím**: bấm ↑ chỉ một chấm trên bảng điểm; stick trái vẫn đi.

## Kiểm tra trong Công cụ tập luyện

Vào **Tập luyện**, không vào ranked.

| Bấm | Phải thấy |
|---|---|
| Stick trái | Đi 360°, không giật 8 hướng |
| ← giữ | AA lính / quái dù tướng địch trong tầm |
| → giữ | AA trụ / cây, không dính tướng dưới trụ |
| ↓ | Hồi thành, có thể hủy bằng đi |
| ↑ | Mở / đóng bảng điểm |
| ↑+→ cùng lúc | **Không** tap hai icon. Nếu có: analog D-pad đang bật |

## Layout khác (đổi khi cần)

Chọn **một** layout. Bốn hướng trộn “lính + cộng Q + chân dung” là loạn.

**Cộng skill** (giống giả lập LDPlayer: D-pad = nâng QWER):

| ↑ | ← | ↓ | → |
|---|---|---|---|
| +Q | +W | +E | +R |

Dùng lúc hồi thành / base, không phải lúc 5v5.

**Khóa chân dung** (Sion Heartsteel): ↑↓←→ = chân dung tướng 1–4. Tướng 5 để L3. Chỉ khi đã bật **Khóa chân dung / Portrait Lock**.

## Cấm

| Gán D-pad vào | Vì sao hỏng |
|---|---|
| Bánh xe đi / Joystick | Trùng stick trái, đi 8 hướng |
| Skill 1–4 | Trùng L1/R1, mất analog aim |
| Cloned Mode hai HUD | Một hướng bấm hai chỗ, last-hit loạn |
| Turbo / Macro | Spam AA / chuỗi tap, lệch last-hit |
| Đường chéo (↑+→ cùng lúc) | Hai tap chồng. Tắt analog D-pad nếu app có |

iOS: mapping D-pad được trên một số kẹp MFi, nhưng một ngón ảo — đừng giữ D-pad lúc đang charge skill.

```bash
python3 diagnose.py
python3 test_diagnose.py
```
