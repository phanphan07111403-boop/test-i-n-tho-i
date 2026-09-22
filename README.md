# test-i-n-tho-i

League itemization sims.

| Folder | Champion | Question |
|--------|----------|----------|
| `zyra-burn-sim/` | Zyra support (Wild Rift 7.2+) | Which burn path peaks harass with enough uptime? |
| `ap-kogmaw-sim/` | AP Kog'Maw (PC LoL ~26.x) | Luden/BF → Malignance 3rd-item drop vs tanks; try Malignance rush, hide-and-shoot, must hurt tanks |
| `wr-shiv-sim/` | Wild Rift on-hit roster (7.3 Shiv) | Which champs convert Statikk Shiv's on-hit bounce? Top 5 |
| `wr-73-playstyles/` | Wild Rift 7.3 builds | Which build/playstyles gained the most vs 7.2? Top 10 |

```bash
python3 zyra-burn-sim/simulate_zyra_burn.py
python3 ap-kogmaw-sim/simulate_ap_kogmaw.py
python3 wr-shiv-sim/simulate_wr_shiv.py
python3 wr-73-playstyles/simulate_wr_73_playstyles.py
```
