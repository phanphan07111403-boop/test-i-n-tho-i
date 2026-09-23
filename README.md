# test-i-n-tho-i

League itemization sims.

| Folder | Champion | Question |
|--------|----------|----------|
| `zyra-burn-sim/` | Zyra support (Wild Rift 7.2+) | Which burn path peaks harass with enough uptime? |
| `ap-kogmaw-sim/` | AP Kog'Maw (PC LoL ~26.x) | Luden/BF → Malignance 3rd-item drop vs tanks; try Malignance rush, hide-and-shoot, must hurt tanks |
| `support-73-pad-sim/` | WR 7.3 supports + GameSir/MB03 D-pad | Top 5 that benefit from the ADC/enchanter patch *and* play on pad |
| `lanes-73-sim/` | WR 7.3 jungle / mid / ADC | Top 5 per role that gain the most from the patch (full 6-slot builds) |
| `kaisa-onhit-sim/` | WR 7.3 Kai'Sa on-hit | Kraken vs BotRK vs Statikk first; full 6-slot pad page |
| `caitlyn-dps-sim/` | WR 7.3 Caitlyn | Highest-damage buy order (Hex → Collector → IE, not Yun Tal) |
| `kayle-kraken-sim/` | WR 7.3 Kayle | Kraken first vs Nashor → Dusk → Cap (AP core; Kraken on-hit alt) |

```bash
python3 zyra-burn-sim/simulate_zyra_burn.py
python3 ap-kogmaw-sim/simulate_ap_kogmaw.py
python3 support-73-pad-sim/simulate_support_73.py
python3 lanes-73-sim/simulate_lanes_73.py
python3 kaisa-onhit-sim/simulate_kaisa_onhit.py
python3 caitlyn-dps-sim/simulate_caitlyn_dps.py
python3 kayle-kraken-sim/simulate_kayle_kraken.py
```
