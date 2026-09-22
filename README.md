# test-i-n-tho-i

League itemization sims.

| Folder | Champion | Question |
|--------|----------|----------|
| `wr-7.3-db/` | Wild Rift 7.3 snapshot | Local champion / item / rune memory for later builds |
| `varus-dps-sim/` | Varus (Wild Rift 7.3) | On-hit vs crit — late-game scale, DPS rising after each buy |
| `zyra-burn-sim/` | Zyra support (Wild Rift 7.2+) | Which burn path peaks harass with enough uptime? |
| `ap-kogmaw-sim/` | AP Kog'Maw (PC LoL ~26.x) | Luden/BF → Malignance 3rd-item drop vs tanks; try Malignance rush, hide-and-shoot, must hurt tanks |

```bash
python3 wr-7.3-db/database.py
python3 varus-dps-sim/simulate_varus.py
python3 zyra-burn-sim/simulate_zyra_burn.py
python3 ap-kogmaw-sim/simulate_ap_kogmaw.py
```

Later Wild Rift build / damage sims should read `wr-7.3-db/` instead of scraping patch notes.
