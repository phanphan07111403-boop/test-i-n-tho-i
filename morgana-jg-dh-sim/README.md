# Morgana jungle — Dark Harvest full build

Wild Rift **7.2e**. **Đi rừng**, keystone **Dark Harvest**. Game **20 phút**.

Không copy mid (farm/CS/Big Bully) và không copy support (Ionia 92% pick). wrchina 7.2e không có bảng Diamond+ jungle — đây là kit + sim, không phải ranked WR.

## Run

```bash
python3 simulate_morgana_jg.py
```

Outputs:
- `report.txt` — full build, spike, gank 70%/DH 90%
- `results.json` — snapshot từng phút

## 4 ô (khóa)

| Ô | Khóa |
|---|------|
| Client | Tốc Chiến 7.2e. Không có món rừng. 5 ô (giày + 4). T3 giày sau 10:00. |
| Role | Jungle. Smite Recoup 4 mana/s. W 195% quái. Big Bully **không** ăn camp. |
| Cặp + constraint | DH jungle: clear camp rồi gank Q. So Mana→Spell+Rylai vs Ionia vs Void bỏ Rylai. |
| Metric | Gank laner 70% HP (execute). DH@90% = proc khi lane còn máu. Không dùng mid WR. |

## Full build (mặc định)

**Flash + Smite** · **W > Q > E** · R @ 5 / 9 / 13

Ngọc: **Dark Harvest · Cheap Shot · Manaflow · Transcendence · Relentless Hunter**

Start: **Amplifying Tome** (Smite giữ clear — WR không có jungle item).

| Ô | Món | Spike (sim) |
|---|-----|-------------|
| Giày | Boots of Mana → **Spellslinger's Shoes** | T2 ~2:00 · T3 ~15:00 |
| 1 | **Blackfire Torch** | ~8:00 |
| 2 | **Liandry's Torment** | ~13:00 |
| 3 | **Rylai's Crystal Scepter** | ~19:00 |
| 4 | Deathcap *(nếu game kéo)* | không xong 20p vàng rừng |

Buy order: Tome → Speed → Mana → Lost Chapter → Ashes → Blackfire → Guise → Liandry → Spellslinger (sau 10:00) → Rylai → Cap.

## Winner (sim)

**Mana → Spellslinger → Rylai**

Gank 70% 20 phút: Spell+Rylai **18520** vs Ionia **16604** (Ionia **−10.3%**). Ionia hơn Q/phút **11.0 vs 9.3** — bài Flash-R, không phải bài DH execute.

Bỏ Rylai lấy Void: paper gank gần bằng (−1.8%), xong Void ~20:00. DH@90% phút 12–20 **thua** Rylai vì không giữ pool. Void **thay Cap**, không thay Rylai.

| Khi | Spike |
|-----|--------|
| ~2:00 | **Boots of Mana** — 8 pen + 25 AP (Recoup che mana clear) |
| ~8:00 | **Blackfire** — burn quái 40+2% AP/s, stack large monster |
| ~13:00 | **Liandry** |
| ~15:00 | **Spellslinger** — 18 flat + 8% pen (core 7.2 = 0 pen) |
| ~19:00 | **Rylai** — giữ W; DH@90% mới ổn |

## DH proc thật sự thế nào

- **Gank 70%** (lane đã thê): Q + Cheap Shot thường xuyên xuyên 50% từ phút 8. DH nổ **trên Q**, không cần Rylai để proc.
- **Gank 90%** (lane còn máu): không slow → họ bước ra hết root (~2.5–2.8s) trước 50%. Rylai = 5s pool.
- Chơi: full clear W (để tick hết bãi) → gank lane thấp máu → Q → W dưới chân.

## Situational (thay Deathcap)

- **Zhonya** — assassin, R-stasis (không dash).
- **Void Staff** — 2+ tank, 40% pen.
- **Bloodletter** — shred 30% từ tick W.
- **Ionia / Crimson** — Flash-R / Q haste > pen.
- **Mercury** — CC nặng, không phải default DH.

## Không làm

- Copy PC LoL DH jungle (Liandry mythic, Sorcs).
- Copy support Scythe / Ionia 92%.
- Copy Diamond+ mid Ionia vs Mercury.
- List món 6 như PC.
