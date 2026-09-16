#!/usr/bin/env python3
"""Validate a Wild Rift D-pad mapping: four Normal HUD taps, never movement."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REQUIRED = ("DPAD_UP", "DPAD_DOWN", "DPAD_LEFT", "DPAD_RIGHT")
LANE_HUD = {
    "DPAD_UP": "scoreboard",
    "DPAD_DOWN": "recall",
    "DPAD_LEFT": "attack_minion",
    "DPAD_RIGHT": "attack_turret",
}
FORBIDDEN = {"joystick", "movement_wheel", "cloned", "turbo", "macro", "skill_stick"}


def load_profile(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def diagnose(profile: dict) -> list[str]:
    problems: list[str] = []
    move = profile.get("movement") or {}
    if (move.get("type") or "").lower() != "joystick":
        problems.append("Left stick must stay a joystick on the movement wheel. Do not put walking on the D-pad.")
    if (move.get("bind") or "") == "DPAD":
        problems.append("Movement is bound to the D-pad. Move walking back to LEFT_STICK.")

    dpad = {item.get("bind"): item for item in profile.get("dpad") or []}
    missing = [name for name in REQUIRED if name not in dpad]
    if missing:
        problems.append(f"Missing D-pad binds: {', '.join(missing)}.")

    layout = (profile.get("layout") or "lane_utility").lower()
    used_hud: list[str] = []
    for name in REQUIRED:
        key = dpad.get(name)
        if not key:
            continue
        key_type = (key.get("type") or "").lower()
        hud = key.get("hud") or ""
        used_hud.append(hud)
        if key_type in FORBIDDEN:
            problems.append(
                f"{name}: type '{key_type}' is not a HUD tap. Use Gán phím / Normal."
            )
        elif key_type != "normal":
            problems.append(f"{name}: type '{key_type}' should be 'normal'.")
        if hud in {"movement_wheel", "joystick"}:
            problems.append(f"{name} is mapped onto the movement wheel. That fights the left stick.")
        if layout == "lane_utility" and LANE_HUD.get(name) and hud != LANE_HUD[name]:
            problems.append(
                f"{name} should hit '{LANE_HUD[name]}' in the lane-utility layout, got '{hud}'."
            )

    if len(used_hud) == 4 and len(set(used_hud)) < 4:
        problems.append("Two D-pad directions share the same HUD spot. Each direction needs its own icon.")

    forbidden_list = {item.lower() for item in profile.get("forbidden_dpad_types") or []}
    for name, key in dpad.items():
        if (key.get("type") or "").lower() in forbidden_list:
            problems.append(f"{name} uses a type this profile lists as forbidden.")

    return problems


def main() -> int:
    profile_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).with_name("mapping-profile.json")
    profile = load_profile(profile_path)
    problems = diagnose(profile)
    print(f"Profile: {profile.get('name', profile_path.name)}")
    print("Wanted: D-pad = scoreboard / recall / minion AA / turret AA. Stick walks.")
    if problems:
        print("Status: BLOCKED")
        for item in problems:
            print(f"- {item}")
        return 1
    print("Status: OK")
    print("- LEFT_STICK = movement wheel")
    print("- ↑ bảng điểm  ↓ hồi thành  ← đánh lính  → đánh trụ")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
