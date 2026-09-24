# Senna + GameSir X3 Pro — targeting combat Wild Rift

Vấn đề: Senna **Relic Cannon** wind-up chậm. Nút đánh mặc định coi **linh hồn Absolution** là unit hợp lệ → một nhịp bắn mất vào soul thay vì tướng.

Hai option map tay cầm. Không phải sim item — đây là research control.

## Run

Không có script. Đọc:

- `report.txt` — full breakdown + setup in-game + G-Touch
- `mapping.json` — layout X3 Pro máy-đọc được

## Verdict

**Option 1 thắng đúng vấn đề combat.** Đè portrait tướng = hiện “đã vào tầm”, không đánh mắt / linh hồn / lính. Tướng vào tầm mới bắn.

**Option 2 thắng kite max tầm + aim chiêu.** Wheel nút đánh + Skill Wheel stick phải + Aim Panning kéo map theo hướng aim. Thả đánh → recenter camera bằng nút riêng (G-Touch không có “on release” native).

**Chơi thật: hybrid.** AA combat = Option 1. Chiêu = Option 2. Soul/farm = nút AA mặc định tách riêng.

| Nhu cầu | Option |
|---------|--------|
| Combat 1v1 / clash, không miss beat vào soul | **1** |
| Kite mép tầm, aim W/R, nhìn xa theo hướng chiêu | **2** |
| Senna ranked trên X3 Pro | **Hybrid** |

## Tại sao Option 1

- Linh hồn **không** phải lính/trụ. `Lock Target = No Minion/Structure` **không** chặn soul.
- Portrait Lock là filter tướng duy nhất native. Icon hiện = tướng trong tầm đánh.
- `Force Attack Follow = OFF` → đè khi hết tầm thì đứng, không chạy ăn soul.
- Patch 6.3: soul gần hết thời gian **tự hút** nếu không đánh. Combat không cần AA soul.

## Tại sao Option 2 không đủ một mình

Wheel AA vẫn là nút đánh mặc định — drag trượt vào soul/mắt/lính là miss beat. Camera pan khi đè chiêu thì **Aim Panning** của WR đã làm. Thả AA trả map giữa cần thêm 1 nút lock camera (LS-click).
