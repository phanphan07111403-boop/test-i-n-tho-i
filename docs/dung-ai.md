# Dùng AI cho khỏi chết vì mẫu sai

Lỗi Ionia mid không phải vì AI “dốt game”. Nó **trả lời trôi chảy câu hỏi khác** — rồi bạn tin vì câu trả lời có số.

Cùng một máy trên Home Assistant: thiếu máy đã đề xuất thì nó đổ **mức tối thiểu generic** (Pi / Green / 2 GB RAM) vào.

Cách chữa không phải “prompt hay hơn”. Là **cấm nó kết luận khi thiếu 4 ô**.

Chi tiết 11 kiểu lỗi: [`ai-advice-failure-modes.md`](../ai-advice-failure-modes.md).

---

## Hai lỗi thật (đọc cái này trước)

### 1. Morgana mid — giày Ionia

Bạn hỏi winrate / build mid. AI lấy:

| Nó dùng | Sai chỗ |
|---|---|
| Ionia **57% WR / 68% pick** | So với **Mercury**, không phải Boots of Mana |
| Support Ionia **92% pick** | Lẫn sample **support** vào **mid** |
| Q haste = identity | Bỏ **farm**: CS, mana W-max, Big Bully |
| “High-elo đôi khi Spellslinger” | Top-30 **63% Spellslinger** bị hạ thành ngoặc đơn |

Khi bắt nó mô hình farm, kết luận **đảo**: mid mặc định Mana → Spellslinger; Ionia là bài support / Flash-R.

### 2. Home Assistant — “máy tính tối thiểu”

Bạn hỏi: *máy đã đề xuất trước đó, điều kiện tối thiểu là gì?*

AI không tìm được chat cũ, rồi vẫn đưa bảng **HA OS VM**: 2 GB / 2 nhân / 32 GB / UEFI, kèm Pi 4/5 và Home Assistant Green.

Bạn hỏi **một PC cụ thể**. Nó trả lời **dân số generic** (appliance + Pi + NUC).

Hai case một xương: **thiếu dữ liệu đúng → đổ meta / tài liệu chung**.

---

## 4 ô — thiếu 1 ô thì vứt câu trả lời

Trước khi tin (mua giày, mua máy, flash ROM), AI phải điền **một câu, có số**:

| Ô | Game | Nhà / HA / PC |
|---|---|---|
| **1. Client** | Tốc Chiến hay PC, patch nào | HAOS / Docker / SKU đang bán VN |
| **2. Role + quy mô** | Mid hay support (vàng/XP khác) | 0 cam / vài cam / NVR; nhà nhỏ hay nhiều tầng |
| **3. Đúng cặp + constraint** | Ionia **vs Mana**, không vs Mercury; **farm** | Mini PC **vs máy đang có**; watt, nhiệt, ngân sách |
| **4. Đúng metric** | Damage lane hay Q/Flash | Idle 24/7 hay FPS; local hay cloud |

Câu bắt 4 ô (dán vào follow-up):

```
Điền 4 ô, mỗi ô một câu có số. Thiếu ô nào thì nói "không biết", đừng đoán meta.
1) Client/SKU/patch bạn đang trả lời?
2) Role/quy mô — sample có lẫn role khác không?
3) Đúng cặp lựa chọn tôi nêu chứ không phải default meta? Constraint (farm/vàng/điện/nhiệt) nằm ở phút/watt nào?
4) Bạn tối ưu metric nào — trùng metric tôi nêu không?
```

---

## Việc của bạn: nhét constraint vào câu **đầu**

AI không nhớ “bạn là mid farmer” nếu câu đầu là “highest winrate”. Winrate không có farm.

**Sai (Morgana):**  
`Morgana mid wildrift highest winrate build`

**Đúng:**  
`Tốc Chiến 7.2e, Morgana MID (farm CS, không phải support). So đúng cặp Ionia vs Boots of Mana — đừng so Mercury. Constraint: W-max mỗi wave, mana, Big Bully. Đừng lấy WR support. Top-elo và Diamond+ tách riêng.`

**Sai (HA):**  
`Máy tính chạy Home Assistant cấu hình nào tốt`

**Đúng:**  
`Home Assistant trên PC x86 mình đã có / đang định mua: [model]. Không phải Pi, không phải Green. Workload: [Zigbee USB + 0 cam / 2 cam / Frigate]. Việt Nam, điện 220V, máy chạy 24/7. So đúng: dùng máy này vs mua mini PC. Đừng lấy spec VM 2 GB làm đủ.`

Mẫu một hơi:

```
Client: …
Role / quy mô: …
So đúng cặp: A vs B (cấm tự thêm C, cấm bỏ B)
Constraint: farm / vàng / watt / nhiệt / ngân sách / SKU VN
Metric thắng: …
Cấm: default meta khi chưa điền 4 ô
Nếu thiếu số liệu đúng cặp: nói thiếu, đừng lấy bảng tổng.
```

Follow-up **phải nhắc lại** client + role + cặp. Thread Morgana bị lẫn Zyra/PC; thread HA bị lẫn Pi vì lượt sau không khóa lại.

---

## Việc của AI: dấu hiệu đang bịa đúng mẫu

Vứt hoặc bắt điền 4 ô nếu thấy:

- “Highest WR” / “thường phù hợp” / “typical” / “official minimum”
- Một số WR **không ghi** đang so với cái gì
- Support + mid, hoặc Pi + NUC + appliance, trong **một** câu khuyên
- Nó kể constraint của bạn rồi **không dùng** trong tính toán
- Không tìm được chat/data cũ nhưng **vẫn ra bảng mua**

---

## Prompt dán đầu mỗi agent (copy)

Dán **trên** câu hỏi, game hay HA đều được:

```
Trước khi kết luận, điền 4 ô (một câu/ô, có số). Thiếu thì dừng, đừng đổ meta.

1. Client — Tốc Chiến vs PC LoL, patch; hoặc HAOS vs Docker vs máy đang có, SKU VN.
2. Role + quy mô — mid vs support (vàng khác); nhà 0 cam vs NVR. Cấm trộn sample.
3. Đúng cặp + constraint — so đúng A vs B tôi nêu. Farm/CS/mana hoặc watt/nhiệt/ngân sách phải vào tính toán, không được chỉ nhắc.
4. Đúng metric — WR không điều kiện không thắng. Nêu n, rank, nguồn; sample có lẫn role không.

Cấm trả lời bằng "mọi người lên X" / "mức tối thiểu chính thức" khi chưa chứng minh X thắng đúng cặp và đúng constraint.

Lỗi đã mắc: Morgana mid bị khuyên Ionia vì WR vs Mercury + sample support, bỏ farm. HA bị khuyên Pi/Green/VM 2GB khi câu hỏi là một PC cụ thể.
```

Repo này có rule cùng nội dung (`.cursor/rules/advice-4-boxes.mdc`) — agent Cloud trên repo phải điền 4 ô. Hỏi topic khác (HA, máy, giày) **vẫn dán** prompt trên, vì rule chỉ chắc khi chạy trong repo.

Muốn dán User Rule trong Cursor (mọi chat): Settings → Rules → paste khối trên.

---

## Sau khi có câu trả lời — 30 giây

1. Nó so **đúng cặp** bạn hỏi chưa, hay so với C?
2. Số liệu **đúng lane / đúng máy**, hay sample to hơn?
3. Constraint (farm, điện, cam) có **thay đổi phút/watt/giá**, hay chỉ được kể?
4. Có câu “không biết” nào không? Không có + bảng mua đàng hoàng → nghi.

Nếu 1–3 fail: gửi đúng 4 ô, **không** hỏi thêm topic mới trong cùng lượt (tránh bleed).
