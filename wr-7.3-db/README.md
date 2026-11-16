# Wild Rift 7.3 local database

Patch **7.3** (2026-09-22) champion, item, and rune snapshot.

This folder is the in-repo memory for later itemization / DPS work. Build
simulators should `import` from here instead of scraping patch notes.

## Files

| File | Contents |
|------|----------|
| `database.py` | Source of truth for items, runes, system constants, Varus kit |
| `champions.json` | 141 champions — 7.3 attack-speed ratios + durability changes |
| `items.json` | Marksman overhaul + new items + components |
| `varus.json` | Full Varus kit at 7.3 |
| `runes.json` | Lethal Tempo rewrite and related runes |
| `patch.json` | Patch metadata and sources |

A copy is also stored at `/cursor/stores/self/wr-7.3/` for agent memory.

## 7.3 system (marksman)

- Crit damage **175% → 200%**
- Attack speed cap **2.5 → 3.0**
- Per-champion attack speed ratios (no melee/ranged split)
- **Lifesteal** replaces omnivamp / physical vamp on listed items
- New marksman items: Hexoptics C44, Yun Tal Wildarrows, Stormrazor, Rapid Firecannon, Fiendhunter Bolts, Immortal Shieldbow, Statikk Shiv
- New champions: Hwei, Sylas, Rek'Sai

## Refresh

```bash
python3 wr-7.3-db/parse_champions.py   # rebuild champions.json from notes dump
python3 wr-7.3-db/database.py          # dump json + agent-store copy
```
