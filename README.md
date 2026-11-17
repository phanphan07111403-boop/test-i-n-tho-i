# test-i-n-tho-i

League itemization sims.

| Folder | Champion | Question |
|--------|----------|----------|
| `zyra-burn-sim/` | Zyra support (Wild Rift 7.2+) | Which burn path peaks harass with enough uptime? |
| `ap-kogmaw-sim/` | AP Kog'Maw (PC LoL ~26.x) | Luden/BF → Malignance 3rd-item drop vs tanks; try Malignance rush, hide-and-shoot, must hurt tanks |
| `shyvana-jungle-sim/` | Shyvana jungle (Wild Rift 7.3d/f) | Best build to counter tanky meta and win late after Ocean omnivamp nerf |
| `tryndamere-jungle-sim/` | Tryndamere jungle (Wild Rift 7.3/7.3b) | Farm the jungle, then split: which build wins the side-lane 1v1 and takes the turret |

```bash
python3 zyra-burn-sim/simulate_zyra_burn.py
python3 ap-kogmaw-sim/simulate_ap_kogmaw.py
python3 shyvana-jungle-sim/simulate_shyvana_jungle.py
python3 tryndamere-jungle-sim/simulate_tryndamere_jungle.py
```
