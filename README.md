# test-i-n-tho-i

League itemization sims.

| Folder | Champion | Question |
|--------|----------|----------|
| `zyra-burn-sim/` | Zyra support (Wild Rift 7.2+) | Which burn path peaks harass with enough uptime? |
| `ap-kogmaw-sim/` | AP Kog'Maw (PC LoL ~26.x) | Luden/BF → Malignance 3rd-item drop vs tanks; try Malignance rush, hide-and-shoot, must hurt tanks |
| `senna-burst-sim/` | Senna ADC + support (Wild Rift 7.3) | ADC: Dusk → Serylda. Support crit: Collector → Mortal → IE → Dusk, sell Scythe → Fiendhunter. Runes: First Strike |

```bash
python3 zyra-burn-sim/simulate_zyra_burn.py
python3 ap-kogmaw-sim/simulate_ap_kogmaw.py
python3 senna-burst-sim/simulate_senna_burst.py
```
