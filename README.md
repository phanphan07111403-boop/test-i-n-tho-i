# test-i-n-tho-i

League itemization sims.

| Folder | Champion | Question |
|--------|----------|----------|
| `zyra-burn-sim/` | Zyra support (Wild Rift 7.2+) | Which burn path peaks harass with enough uptime? |
| `ap-kogmaw-sim/` | AP Kog'Maw (PC LoL ~26.x) | Luden/BF → Malignance 3rd-item drop vs tanks; try Malignance rush, hide-and-shoot, must hurt tanks |
| `morgana-comet-farm-sim/` | Morgana mid (Wild Rift 7.2e) | Farm Arcane Comet from minute 1: land the 0.8s delay, stack hits, maximize comet damage |

```bash
python3 zyra-burn-sim/simulate_zyra_burn.py
python3 ap-kogmaw-sim/simulate_ap_kogmaw.py
python3 morgana-comet-farm-sim/simulate_morgana_comet.py
python3 morgana-comet-farm-sim/simulate_morgana_comet_runes.py
```
