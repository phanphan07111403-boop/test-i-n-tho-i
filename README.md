# test-i-n-tho-i

League itemization sims.

| Folder | Champion | Question |
|--------|----------|----------|
| `zyra-burn-sim/` | Zyra support (Wild Rift 7.2+) | Which burn path peaks harass with enough uptime? |
| `ap-kogmaw-sim/` | AP Kog'Maw (PC LoL ~26.x) | Luden/BF → Malignance 3rd-item drop vs tanks; try Malignance rush, hide-and-shoot, must hurt tanks |
| `gamesir-x3-duelist/` | Volibear (Wild Rift 7.3) | Easy 1v1 + hard to kill + GameSir X3 Pro overlay mapping |
| `volibear-build-sim/` | Volibear Baron (Wild Rift 7.3) | Item order for strongest 1v1 (Dusk vs Trinity vs Heartsteel) |
| `shen-build-sim/` | Shen Baron (Wild Rift 7.3) | Farm/1v1/1v9 vs CN 62% WR Heartsteel–Sunfire–Thornmail |
| `voli-vs-shen/` | Volibear vs Shen Baron (Wild Rift 7.3) | GameSir vs touch, then lane / 1v1 / teamfight |

```bash
python3 zyra-burn-sim/simulate_zyra_burn.py
python3 ap-kogmaw-sim/simulate_ap_kogmaw.py
python3 gamesir-x3-duelist/rank_gamesir_duelist.py
python3 volibear-build-sim/simulate_volibear_build.py
python3 shen-build-sim/simulate_shen_build.py
python3 voli-vs-shen/compare.py
```
