# GameSir: chỉnh Cloned Mode

**Cloned Mode** không phải mode kết nối (HID / G-Touch / V-Touch / XInput). Nó là **kiểu phím** trong editor map của app **GameSir World** (小鸡游戏世界).

Một nút vật lý tách thành **hai nút ảo giống nhau**. **Nhấn hoặc thả** nút đó thì **cả hai vị trí trên màn hình bấm cùng lúc**.

Nguồn: [FAQ GameSir — mapping extra features](https://gamesir.com/support/faq) mục 10, và [常规键-点击模式](https://doc.xiaoji.com/zh/gamesir/detail/678.html) (“两个完全一样的按钮…两个按钮会同时响应”).

## Bật / sửa Cloned Mode (Android)

1. Cắm / ghép tay GameSir, bật mapping **G-Touch** (ưu tiên) hoặc **V-Touch**. iOS không map được từ iOS 13.4.
2. Mở **GameSir World** → chọn game → thanh mode dưới tên game → **Hardware Mapping (G-Touch)** hoặc **Software Mapping (V-Touch)** → **Start** game **từ app**.
3. Trong trận (hoặc màn hình skill), bấm **icon nổi GameSir** → **Adjust buttons / 调整键位**.
4. Chọn nút đã map (A, L1, L4, …). Bấm **⚙️** (hoặc **bấm đúp** nút) để mở thuộc tính.
5. Trong **Click Mode / 点击模式**, chọn **Cloned Mode**.
   - App tiếng Anh: *Cloned Mode — Duplicates the mapped function. Both outputs activate simultaneously on button press or release.*
   - App tiếng Trung: tùy chọn tách thành **hai nút hoàn toàn giống nhau**, nhấn/thả thì **cả hai cùng phản hồi**.
6. Editor hiện **hai nút con**. Kéo từng nút lên **hai chỗ khác nhau** trên HUD (ví dụ skill 1 + skill 2).
7. **Lưu / 保存外设**. Đóng overlay.

### Chỉnh lại vị trí (không cần tắt mode)

Cùng đường: icon nổi → **调整键位**. Hai nút clone vẫn nằm trên layout. Kéo lại, dùng mũi tên **微调**, phóng to/thu nhỏ. Lưu.

### Tắt Cloned Mode

Cùng menu ⚙️ → đổi **Click Mode** về **Normal** (một chấm, một tap). Hoặc xóa nút (kéo vào ô xóa / thùng rác) rồi map lại kiểu Normal.

## Đừng nhầm với các kiểu gần giống

| Trong app | Khác Cloned Mode chỗ nào |
|---|---|
| **Normal / DownClick** | Một vị trí, một tap |
| **Separated press & release / 按下弹起分离** | Cũng tách 2 nút, nhưng **nhấn = tap nút trên**, **thả = tap nút dưới** — **không cùng lúc** |
| **Turbo** | Spam tap một chỗ |
| **One-button Macro / 魔术键** | Chuỗi nhiều điểm theo thời gian. Interval **0s** thì 2 điểm cùng lúc (giống clone) nhưng đây là macro, không phải Cloned Mode |
| **L4/R4 hardware** (`M` + L4/R4) | Nhân **giá trị nút tay cầm** (L4 = A). Game nhận hai nút HID, không phải hai chấm cảm ứng |

## Tốc Chiến / MOBA

Clone một nút lên **hai skill** = một lần bấm ra hai chiêu. Dễ đụng ToS. Dùng clone cho **cùng một chức năng HUD** (ví dụ hai lớp nút chồng, hoặc một skill + nút xác nhận cùng chỗ logic) thì đúng nghĩa “duplicate mapped function”.

Muốn **nhấn chỗ A, thả chỗ B** thì dùng **Separated press & release**, không phải Cloned.

## iPhone / MooWii

- **iOS:** GameSir World không còn thư viện game / mapping. Cloned Mode **không có**.
- **MB03 + MooWii:** không có menu tên Cloned Mode. Gần nhất: **Macro** hai điểm, delay **0**. Đó là macro, không phải clone của GameSir World.

## File trong thư mục này

- `mapping-profile.json` — profile chuẩn: một bind, hai output, `simultaneous` khi press **và** release
- `diagnose.py` — chặn nhầm Separated / Turbo / Macro / một output
- `guide.html` — mô phỏng Normal vs Separated vs Cloned

```bash
python3 diagnose.py
python3 test_diagnose.py
```
