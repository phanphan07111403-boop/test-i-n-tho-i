# Maximize damage — Spellslinger vs Crimson

Wild Rift **7.2e**. Mid. Bỏ vàng. Maximize **DPM** poke (không phải QPM).

- Morgana: Dark Binding 60s, 90% HP.
- Viktor: Death Ray (E), không phải Q Siphon.

Spellslinger: 40 AP, 18 flat, 8% pen, 0 AH.  
Crimson Lucidity: 0 AP, 0 pen, **25 AH**, 8% MS.

## Run

```bash
python3 simulate_qpm_dpm.py
python3 simulate_dh_comet.py
python3 simulate_burst_dh.py
```

## 4 ô

| Ô | Khóa |
|---|------|
| Client | Tốc Chiến 7.2e. Không copy support Ionia WR. |
| Role | Mid. Bỏ gold. |
| Cặp | Spell vs Crimson: (1) cùng 4 đồ (2) 4 đồ tốt nhất dưới từng giày |
| Metric | DPM poke squishy 90%. CPM chỉ giải thích AH. |

## Maximize damage → Spellslinger

| | Morgana DPM | Viktor DPM |
|--|-------------|------------|
| **Best Spell** (Luden·HF·BF·Crypt) | **10558** | **13490** |
| Best Crimson (HF·BF·Crypt·Liandry) | 9511 (**−9.9%**) | 12019 (**−10.9%**) |
| Crimson trên 4 đồ Spell | 8919 (**−15.5%**) | 11733 (**−13.0%**) |

Cùng 4 đồ Spell-max: Crimson **+13.4%** casts, **−25% / −23%** damage mỗi cast → thua DPM.

Crimson tự đổi 4 đồ (bỏ Luden, lấy Liandry) vẫn thua ~10%. 18 flat + 8% + 40 AP > 25 AH trên squishy.

Crimson chỉ khi metric là spam QPM/EPM, không phải maximize damage.

## Thêm Rylai (specter / scepter)

5 slot đầy: Spell · Luden · HF · BF · Crypt. Thêm Rylai = thế 1 món. Rylai 7.2: 65 AP, 7% pen, 350 HP, 30% slow. Slow **không** vào DPM (hit 100%).

**Thế Luden** — rẻ damage nhất.

| Thế món | Morgana | Viktor |
|---------|---------|--------|
| **Luden** | 8896 (**−15.7%**) | **11616 (−13.9%)** |
| BF | 8448 (−20.0%) | 10719 (−20.5%) |
| HF | 8411 (−20.3%) | 9956 (−26.2%) |
| Crypt | 8229 (−22.1%) | 10423 (−22.7%) |

Giữ HF · BF · Crypt. Đừng thế Crypt hay HF.

Morgana nếu tối ưu lại 3 món: Spell · HF · BF · Void · Rylai (−15.1%), vẫn gần mức thế Luden.

## Comet: spam Q hay maximize damage?

**Maximize damage.** Spell · Luden · HF · BF · Crypt. Không Crimson spam.

Comet CD **8s @lv15, không giảm bởi AH**. Cả hai build đều 8 Comet/phút. Spam +24% QPM không thêm proc.

| | Morgana kit+Comet | Viktor kit+Comet |
|--|-------------------|------------------|
| **Max DPM** | **11494** (10558+936) | **14426** (13490+936) |
| Spam Q | 8346 (**−27.4%**) | 10275 (**−28.8%**) |

Spam mất Spell 18+8% + Luden Echo → kit **và** Comet đều yếu (~−29% Comet).

## DH vs Comet (giữ Luden, cùng 5 slot)

Cùng Spell · Luden · HF · BF · Crypt. Keystone only. Cả hai +5% AP sau 7.2.

**Một hit, DH thắng Comet từ:**

| So với Comet | Souls |
|--------------|-------|
| Comet 0 stack (fresh) | **6** |
| Cùng số stack | **8** |
| Average ~2 Comet poke / 1 DH soul | **10** |
| 3 Comet / soul | **14** |

Poke 90% (cửa maximize DPM): **Comet luôn** — DH không proc (>50% HP). Execute không reset: Comet vẫn hơn (CD 8s vs 35s). DH hơn trên **tổng** damage khi takedown reset CD 1s, không phải vì stack.

## DH burst (takedown reset 1s)

Giữ Luden. Spellslinger. Bỏ vàng. Metric = **combo 70%+R**, không phải poke DPM.

**Spell · Luden · Orb · Cap · Storm**

Morgana combo 2851, Viktor 2700. Poke set (Luden·HF·BF·Crypt) **−31.5% / −28.2%**.

Reset 1s = spam DH, không spam Q. AH không giảm DH CD → đừng lấy HF/Crypt/BF/Crimson cho burst.

| Slot 4 sau Orb·Cap | Morgana combo | vs Storm |
|--------------------|---------------|----------|
| **Storm** | **2851** | — |
| Void | 2804 | −1.6% |
| Crypt | 2708 | −5.0% |
| HF | 2555 | −10.4% |
| BF | 2452 | −14.0% |

Storm vs Void: Storm thắng combo nhờ Squall (125+10% AP nếu ≥25% HP / 2.5s). Void thắng 4×DH dump nhờ 40% pen (~+5%), không lật tổng vì combo Storm lớn hơn. Một tank → Void gần burst (−1.6%), không đủ để bỏ Storm khi metric là burst squishy.

Đừng mua set poke DPM cho DH all-in. Cap + Orb + Squall mới amp DH và one-shot.


