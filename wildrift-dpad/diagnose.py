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
SKILL_UPGRADE_HUD = {
    "DPAD_UP": "upgrade_q",
    "DPAD_LEFT": "upgrade_w",
    "DPAD_DOWN": "upgrade_e",
    "DPAD_RIGHT": "upgrade_r",
}
PORTRAIT_HUD = {
    "DPAD_UP": "enemy_portrait_1",
    "DPAD_RIGHT": "enemy_portrait_2",
    "DPAD_DOWN": "enemy_portrait_3",
    "DPAD_LEFT": "enemy_portrait_4",
}
LAYOUT_HUD = {
    "lane_utility": LANE_HUD,
    "skill_upgrade": SKILL_UPGRADE_HUD,
    "portrait_lock": PORTRAIT_HUD,
}
FORBIDDEN_TYPES = {
    "joystick",
    "movement_wheel",
    "cloned",
    "turbo",
    "macro",
    "skill_stick",
    "separated",
    "gesture",
    "sliding",
}
FORBIDDEN_HUD = {
    "movement_wheel",
    "joystick",
    "skill_1",
    "skill_2",
    "skill_3",
    "skill_4",
    "skill_stick",
}
LANE_PREREQS = ("scoreboard", "recall", "attack_minion", "attack_turret")


def load_profile(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def diagnose(profile: dict) -> list[str]:
    problems: list[str] = []

    if profile.get("analog_dpad") is True:
        problems.append(
            "Analog D-pad is on. Diagonals fire two taps at once. Turn analog / hat-stick off."
        )

    move = profile.get("movement") or {}
    if (move.get("type") or "").lower() != "joystick":
        problems.append(
            "Left stick must stay a joystick on the movement wheel. Do not put walking on the D-pad."
        )
    if (move.get("bind") or "") == "DPAD":
        problems.append("Movement is bound to the D-pad. Move walking back to LEFT_STICK.")

    layout = (profile.get("layout") or "lane_utility").lower()
    expected = LAYOUT_HUD.get(layout)
    if expected is None:
        problems.append(
            f"Unknown layout '{layout}'. Use lane_utility, skill_upgrade, or portrait_lock."
        )
        expected = {}

    if layout == "lane_utility":
        prereq = profile.get("hud_prerequisites") or {}
        missing_hud = [name for name in LANE_PREREQS if name not in prereq]
        if missing_hud:
            problems.append(
                "HUD icons missing before mapping: "
                + ", ".join(missing_hud)
                + ". Place them in Tùy chỉnh bố cục nút first."
            )
        if profile.get("hud_first") is False:
            problems.append(
                "hud_first is false. Map the in-game icons first, then bind the D-pad onto them."
            )

    dpad = {item.get("bind"): item for item in profile.get("dpad") or []}
    missing = [name for name in REQUIRED if name not in dpad]
    if missing:
        problems.append(f"Missing D-pad binds: {', '.join(missing)}.")

    used_hud: list[str] = []
    forbidden_list = {item.lower() for item in profile.get("forbidden_dpad_types") or []}
    forbidden_list |= FORBIDDEN_TYPES

    for name in REQUIRED:
        key = dpad.get(name)
        if not key:
            continue
        key_type = (key.get("type") or "").lower()
        hud = key.get("hud") or ""
        used_hud.append(hud)
        if key_type in forbidden_list:
            problems.append(
                f"{name}: type '{key_type}' is not a HUD tap. Use Gán phím / Normal."
            )
        elif key_type != "normal":
            problems.append(f"{name}: type '{key_type}' should be 'normal'.")
        if hud in FORBIDDEN_HUD:
            problems.append(
                f"{name} is mapped onto '{hud}'. That fights the left stick or the skill cluster."
            )
        if expected.get(name) and hud != expected[name]:
            problems.append(
                f"{name} should hit '{expected[name]}' in the {layout} layout, got '{hud}'."
            )

    if len(used_hud) == 4 and len(set(used_hud)) < 4:
        problems.append(
            "Two D-pad directions share the same HUD spot. Each direction needs its own icon."
        )

    return problems


def format_ok(profile: dict) -> list[str]:
    layout = (profile.get("layout") or "lane_utility").lower()
    lines = ["- LEFT_STICK = movement wheel"]
    if layout == "lane_utility":
        lines.append("- ↑ bảng điểm  ↓ hồi thành  ← đánh lính  → đánh trụ")
    elif layout == "skill_upgrade":
        lines.append("- ↑ +Q  ← +W  ↓ +E  → +R  (chỉ lúc base)")
    elif layout == "portrait_lock":
        lines.append("- ↑↓←→ = chân dung tướng 1–4")
    return lines


def main() -> int:
    profile_path = (
        Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).with_name("mapping-profile.json")
    )
    profile = load_profile(profile_path)
    problems = diagnose(profile)
    print(f"Profile: {profile.get('name', profile_path.name)}")
    print("Wanted: HUD first, then D-pad = 4 Normal taps. Stick walks.")
    if problems:
        print("Status: BLOCKED")
        for item in problems:
            print(f"- {item}")
        return 1
    print("Status: OK")
    for line in format_ok(profile):
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
