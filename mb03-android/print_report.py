#!/usr/bin/env python3
"""Print MB03 Android / S24 Ultra / Tốc Chiến findings."""

from __future__ import annotations

import json
from pathlib import Path


def main() -> int:
    data = json.loads(Path(__file__).with_name("community.json").read_text(encoding="utf-8"))
    app = data["best_app"]
    print(f"Phone: {data['device']}")
    print(f"Pad:   {data['controller']}")
    print(f"Game:  {data['game']}")
    print()
    print(f"Best app: {app['name']}  ({app['package']})  {app['version_shop_spec']}")
    print(f"Why: {app['why']}")
    block = data.get("play_store_on_s24_ultra") or {}
    if block:
        print()
        print("Play Store on S24 Ultra:")
        print(f"  {block.get('banner')}")
        print(f"  {block.get('meaning')}")
        print(f"  Next: {block.get('next_step')}")
    print()
    print(f"Play/AppBrain score: {data['reviews']['play_appbrain_score']} / 5")
    print("Do not use:")
    for item in data["not_compatible"]:
        print(f"  - {item}")
    print()
    print("Tốc Chiến cloud code:", data["gace_cloud_codes"]["toc_chien_android"] or "none (map by hand)")
    print("1:1 layout:")
    for row in data["wild_rift_1to1_layout"]:
        print(f"  {row['bind']:11} {row['action']:10} {row['type']}")
    print()
    print("ToS:", data["tos"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
