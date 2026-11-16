#!/usr/bin/env python3
"""Parse Wild Rift 7.3 champion base-stat lines from the CN test-server notes dump."""

from __future__ import annotations

import json
import re
from pathlib import Path

SRC = Path(
    "/home/ubuntu/.cursor/projects/workspace/agent-tools/"
    "33e59ddd-0c56-49e1-8160-a2ccafaf1ce6.txt"
)

# "Jax — Base Stats — Base Health: 690 → 660"
LINE = re.compile(
    r"^- (?P<name>.+?) — Base Stats — (?P<stat>.+?): (?P<value>.+)$"
)
CHANGE = re.compile(r"^(?P<old>.+?)\s*→\s*(?P<new>.+)$")

STAT_KEY = {
    "Attack Speed Ratio": "as_ratio",
    "Base Attack Speed": "base_as",
    "Base Bonus Attack Speed": "base_bonus_as",
    "Attack Speed Growth": "as_growth",
    "Base Health": "base_hp",
    "Health Growth": "hp_growth",
    "Base Armor": "base_armor",
    "Armor Growth": "armor_growth",
    "Base Attack Damage": "base_ad",
    "Attack Damage Growth": "ad_growth",
    "Attack Damage per Level": "ad_growth",
    "Base Magic Resist": "base_mr",
    "Magic Resist Growth": "mr_growth",
    "Base Mana": "base_mana",
    "Mana Growth": "mana_growth",
}


def parse_number(raw: str):
    raw = raw.strip().rstrip(".")
    if raw.endswith("%"):
        try:
            return float(raw[:-1]) / 100.0
        except ValueError:
            return raw
    try:
        if "." in raw:
            return float(raw)
        return int(raw)
    except ValueError:
        return raw


def main() -> None:
    champs: dict[str, dict] = {}
    text = SRC.read_text(encoding="utf-8")
    in_stats = False
    for line in text.splitlines():
        if "Champion durability" in line or "Champion attack speed" in line:
            in_stats = True
        if line.startswith("### Marksman items"):
            break
        m = LINE.match(line.strip())
        if not m:
            continue
        name = m.group("name").strip()
        stat = m.group("stat").strip()
        value = m.group("value").strip()
        key = STAT_KEY.get(stat)
        if not key:
            # keep unknown keys under extra
            key = "extra:" + stat
        rec = champs.setdefault(
            name,
            {"id": name.lower().replace(" ", "_").replace("'", ""), "name": name, "stats": {}, "changes_7_3": {}},
        )
        chg = CHANGE.match(value)
        if chg:
            new_v = parse_number(chg.group("new"))
            old_v = parse_number(chg.group("old"))
            rec["stats"][key] = new_v
            rec["changes_7_3"][key] = {"from": old_v, "to": new_v}
        else:
            rec["stats"][key] = parse_number(value)

    out = Path(__file__).parent / "champions.json"
    payload = {
        "patch": "7.3",
        "source": "WR China PBE notes (2026-09-01) merged onto live 7.3 global notes",
        "note": (
            "Attack-speed fields are the 7.3 per-champion ratios. "
            "Durability fields only appear when 7.3 changed them. "
            "Ability kits are stored separately for champions that have a full entry."
        ),
        "champions": champs,
    }
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {out} ({len(champs)} champions)")


if __name__ == "__main__":
    main()
