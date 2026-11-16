# test-i-n-tho-i

League itemization sims.

| Folder | Champion | Question |
|--------|----------|----------|
| `zyra-burn-sim/` | Zyra support (Wild Rift 7.2+) | Which burn path peaks harass with enough uptime? |
| `ap-kogmaw-sim/` | AP Kog'Maw (PC LoL ~26.x) | Luden/BF → Malignance 3rd-item drop vs tanks; try Malignance rush, hide-and-shoot, must hurt tanks |
| `ryze-haste-sim/` | Ryze mid (Wild Rift 7.3f) | Top core vs full ability haste, and the damage/haste balance at level 15 |
| `varus-blight-sim/` | Varus dragon (Wild Rift 7.3f) | Statikk Shiv plus Runaan's Hurricane, then the finished six-item build |

```bash
python3 zyra-burn-sim/simulate_zyra_burn.py
python3 ap-kogmaw-sim/simulate_ap_kogmaw.py
python3 varus-blight-sim/simulate_varus_blight.py
python3 varus-blight-sim/simulate_varus_full.py
```
