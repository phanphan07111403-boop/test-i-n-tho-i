# Ignore gold — max QPM / DPM (Morgana + Viktor)

Wild Rift **7.2e**. Mid. **Bỏ vàng**, bỏ spike, bỏ thứ tự mua. Chỉ 5 slot **đã xong**.

- Morgana: **QPM** = Dark Binding / phút. DPM = Q poke 60s, 90% HP.
- Viktor: poke button là **Death Ray (E)**, không phải Q Siphon. EPM = E / phút.

HF Hypershot +10% sau hit ≥600 (hit apply không amp). Viktor: laser apply, Blastquake 1s sau **có** amp. Echo 140+15% AP / 10s. Orb 20% **tắt** @90% HP.

## Run

```bash
python3 simulate_qpm_dpm.py
```

## 4 ô

| Ô | Khóa |
|---|------|
| Client | Tốc Chiến 7.2e |
| Role | Mid. Bỏ gold. |
| Cặp | Mọi boots × 4 legendary (Void XOR Cryptbloom) |
| Metric | CPM và DPM poke squishy 90%, phút 20 / lv 15 |

588 inventory / tướng.

## Không max được cả hai

| | Max cadence | Max DPM |
|--|-------------|---------|
| **Inventory** | Crimson · HF · BF · Cosmic · Seraph | Spell · Luden · HF · BF · Crypt |
| AH | **132** | 87 |
| Morgana | **16.28 QPM** / 7684 DPM | 13.12 QPM / **10558 DPM (+37%)** |
| Viktor | **19.89 EPM** / 9613 DPM | 16.03 EPM / **13490 DPM (+40%)** |

Lock cũ Spell · Luden · Orb · Cap: Morgana DPM **−9.7%**, Viktor **−15.2%** vs max DPM. Orb 20% không chạy trên poke full HP; Cap 0 AH.

## Build order (ưu tiên slot, không phải gold)

**Spam Q/E:** Crimson → Horizon Focus → Cosmic Drive → Seraph → Blackfire.

**Maximize DPM:** Spellslinger → Luden → Horizon Focus → Blackfire → Cryptbloom.

Cùng set cho cả Morgana và Viktor.

Crimson thắng cadence vì 25 AH, thua DPM vì mất Spell 40 AP + 18 flat + 8%. HF nằm ở **cả hai** set (25 AH + 10% hit sau). Cryptbloom 30%+20 AH thắng Void 40%+0 AH trên squishy poke. Luden+BF cùng inventory vì bỏ vàng — trong game thật cả hai ăn Lost Chapter, cái sau chậm hơn.
