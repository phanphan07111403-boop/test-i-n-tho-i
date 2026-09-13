# AI advice: 11 failure modes (catch them before you buy / lock a build)

AI will give a fluent answer even when it solved the **wrong problem**. Force one catch question per mode. If the AI cannot answer it in one sentence with numbers, discard the advice.

Grounded in real prior asks on this repo: Home Assistant PC, Xiaomi gaming VN, thiết bị Tốc Chiến, Morgana mid (Ionian vs mana, support WR mixed into mid, Ionian vs Mercury instead of Mana, farm ignored), Morgana build order (PC then WR), AP Kog'Maw (PC/WR mix), Zyra support vs mid boots.

---

## 1. Sai client — PC LoL ↔ Tốc Chiến ↔ patch mix

**Games:** Item names, boots, gold curve, and skillshots from PC get pasted onto Tốc Chiến (or the reverse). Follow-ups keep the first client even after you said WR. Same champ, different game.

**HA / nhà / mua PC:** Specs for Home Assistant OS on a NUC get mixed with “gaming PC for everything.” Zigbee2MQTT vs ZHA vs Matter dumped as if they were one stack. A US 120V PSU or a CN-ROM box is treated as the VN SKU.

**Câu bắt lỗi:** “Bạn đang trả lời **đúng client/SKU/OS nào**, patch/version nào, và món nào **không tồn tại** trên cái đó?”

---

## 2. Sai lane / trộn sample — Support WR nhét vào Mid

**Games:** Morgana/Zyra **support** winrate, boots, and gold (sightstone-era income, no CS) recommended for **mid**. “Highest WR boots” is the support page. Mid farm, roam, and wave are never in the model.

**HA / nhà / mua PC:** A “family house” HA blueprint (many cameras, NVR, local LLM) is given for a one-room apartment Pi. Or a Pi 4 guide is given for a tower that will run Frigate + 8 cameras.

**Câu bắt lỗi:** “Dataset / gold / wattage bạn dùng là **đúng role + đúng quy mô nhà** của tôi, hay bạn đang lấy số của role/nhà khác?”

---

## 3. So nhầm đối thủ — A vs C khi câu hỏi là A vs B

**Games:** Asked Ionian vs **Mana boots**; AI compares Ionian vs **Mercury**. The option you care about never enters the table. Winner of the wrong fight looks decisive.

**HA / nhà / mua PC:** Asked Mini PC vs used SFF for HA; AI compares Mini PC vs a full gaming tower. Asked Xiaomi VN vs local alternative; AI compares Xiaomi Global vs Samsung US.

**Câu bắt lỗi:** “Liệt kê **đúng hai (hoặc ba) lựa chọn tôi nêu**. Cái nào bạn **tự thêm** / **tự bỏ**?”

---

## 4. Bỏ constraint thật — farm, vàng, điện, nhiệt, khe cắm

**Games:** Mid build ignores CS/farm timeline. Item finishes “on paper” at times you cannot afford. Support gold buys a mid spike. No last-hit, no back timing, no wave.

**HA / nhà / mua PC:** Recommends a NUC with 4× 4K cameras and ignores PoE budget, HDD/NVMe slots, idle watts, and Vietnam summer thermals. Recommends a GPU box for HA when the bottleneck is USB coordinator + SSD.

**Câu bắt lỗi:** “Với **gold/phút (hoặc watt / số cam / ngân sách)** của tôi, phút/giờ nào **thực sự mua được** món bạn khuyên — không phải phút lý thuyết?”

---

## 5. Winrate trần — WR không có điều kiện

**Games:** “Ionian 52% WR” with no n, elo, patch, role, or opponent pool. Mixed support+mid. A 200-game filler build beats a 20-game mid OTP sample.

**HA / nhà / mua PC:** “NUC is the best HA box” from Reddit 2021. “Xiaomi is best for Vietnam” with no year, no model, no Zigbee chip (ESP vs nRF). Star ratings without failure mode (heat, ROM, warranty).

**Câu bắt lỗi:** “WR / ‘best’ này: **n bao nhiêu, rank/patch nào, role nào, nguồn nào**, và sample có **lẫn role/client** không?”

---

## 6. SKU / thị trường lệch — hàng VN ≠ review global

**Games:** NA/EU item or controller rec (MFi, Xbox, Gamesir Global) when you are on VN store / TGDĐ / Shopee. A device “officially supports” WR in another region and is blocked here.

**HA / nhà / mua PC:** Xiaomi **Global** ROM, US plug, or model not imported. HA integration exists for device **A** but VN shops sell device **A-lite** with a different chip. Warranty void on CN imports.

**Câu bắt lỗi:** “Model **chính xác** (mã SKU) đang bán **tại Việt Nam**, ROM/adapter nào, và integration/game có **xác nhận trên đúng mã đó** không?”

---

## 7. Tương thích trên giấy — “support” ≠ chơi được / chạy được

**Games:** Bluetooth controller “works with Android” so it “works with Tốc Chiến.” Mapping, gyro, charge-while-move, fan cutoff, iOS MFi, Play Store block (MooWii on S24) never checked.

**HA / nhà / mua PC:** “Zigbee compatible” on the box. Device is Zigbee but not in ZHA, needs a custom quirk, or is Wi-Fi-only Xiaomi that dies when the cloud app is gone. PC “runs HA” because it runs Docker — no IOMMU, no spare USB, no UPS.

**Câu bắt lỗi:** “Cái này **đã được xác nhận chạy đúng app/stack của tôi** (Tốc Chiến / HA + coordinator X) hay chỉ ‘cùng chuẩn Bluetooth/Zigbee’?”

---

## 8. Over-spec / under-spec — máy cho HA vs máy cho game

**Games:** Full mythic+pen graph for a 15-minute WR game; or a “budget” build that never reaches the item the advice is about.

**HA / nhà / mua PC:** i5/32GB/RTX “for Home Assistant” when a used i3 NUC or Beelink with 16GB + SSD is enough — **unless** you also want Frigate, local voice, or a game VM. Opposite: Pi 4 for 12 cameras. One sentence hides which workload.

**Câu bắt lỗi:** “Tách **ba mức**: (1) chỉ HA + Zigbee, (2) HA + camera NVR, (3) HA + game/VM. Tôi đang ở mức nào, và bạn đang bán spec của mức nào?”

---

## 9. Context bleed — follow-up giữ sai giả định

**Games:** First answer was PC Kog'Maw; later turns still use PC items after you switched to WR. Morgana mid thread still cites support WR. Zyra **support** boots leaked into a **mid** boots question.

**HA / nhà / mua PC:** Thread started as “cheap HA box,” later you asked for a Xiaomi gaming handheld / PC — AI keeps giving HA-mini-PC advice (or the reverse). Voltage, ROM, and game-mode tips from the previous product stick to the new one.

**Câu bắt lỗi:** “Trong câu trả lời này, giả định nào **lấy từ lượt trước**? Cái nào tôi **chưa xác nhận lại** (client, role, model, ngân sách)?”

---

## 10. Tối ưu sai metric — WR / DPS / “mạnh” ≠ thứ bạn chơi

**Games:** Max burst or max WR page when the constraint was **farm + mana + mid wave**. Ionian wins CDR charts; Mana boots win the actual mid lane. Zyra burn sim ≠ Zyra mid one-shot.

**HA / nhà / mua PC:** “Fastest CPU” when you needed **idle watts + silent + 24/7**. “Most Zigbee devices supported” when you needed **local, no-cloud, VN-buyable**. Gaming FPS rec for a box that will sit in a closet running HA.

**Câu bắt lỗi:** “Bạn đang tối ưu **metric nào** (WR, DPS, FPS, $/điểm, watt idle)? Metric **tôi** nêu là gì — chúng **trùng** không?”

---

## 11. Khuyên default meta thay vì đáp đúng câu

**Games:** Mage → always Ionian. Support mage → always the support page. The asked pair (Ionian vs Mana, support vs mid) is never computed. “Everyone buys X” replaces the comparison.

**HA / nhà / mua PC:** “Just buy a Raspberry Pi” or “just buy a used ThinkCentre” without checking your cameras, USB Zigbee stick, or whether you already own a Xiaomi gateway. Default Home Assistant Yellow / SkyConnect rec when you asked for a **PC you already have**.

**Câu bắt lỗi:** “Nếu **cấm** default meta (Ionian / Pi / ‘best 2024 NUC’), câu trả lời **thay đổi** chứ? Đổi chỗ nào?”

---

## Cheat sheet — hỏi 4 câu trước khi tin

1. **Client / SKU / version?** (mode 1, 6, 7, 9)
2. **Đúng role + đúng quy mô?** (mode 2, 8)
3. **Đúng cặp so sánh + đúng constraint (farm/vàng/điện)?** (mode 3, 4)
4. **Đúng metric + nguồn WR có điều kiện?** (mode 5, 10, 11)

Nếu AI không điền được 4 ô đó, đừng mua giày / đừng mua máy.
