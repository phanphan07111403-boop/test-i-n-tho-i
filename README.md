# test-i-n-tho-i

League itemization sims + MB03 playstyle notes.

| Folder / file | Champion | Question |
|--------|----------|----------|
| `zyra-burn-sim/` | Zyra support (Wild Rift 7.2+) | Which burn path peaks harass with enough uptime? |
| `ap-kogmaw-sim/` | AP Kog'Maw (PC LoL ~26.x) | Luden/BF → Malignance 3rd-item drop vs tanks; try Malignance rush, hide-and-shoot, must hurt tanks |
| `mb03-loi-choi-khac.md` | MB03 (Tốc Chiến) | Còn lối nào khớp ngoài gồng / xả Q / combo? Kite AA, đặt trụ-cây, bám người |
| `mb03-kite.md` | MB03 kite AA | Analog luôn lùi + tap A; cài Follow tắt; tập Ashe/Sivir |
| `pantheon-hull-demolish-sim/` | Pantheon Baron (Wild Rift 7.2+) | Hullbreaker + Demolish, không combat, chỉ đi vòng phá trụ |

```bash
python3 zyra-burn-sim/simulate_zyra_burn.py
python3 ap-kogmaw-sim/simulate_ap_kogmaw.py
python3 pantheon-hull-demolish-sim/simulate_pantheon_siege.py
python3 pantheon-hull-demolish-sim/compare_siege_champs.py
```
