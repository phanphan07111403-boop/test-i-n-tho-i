#!/usr/bin/env python3
"""Validate a MooWii mapping profile for L1 charge-while-walking."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ALLOWED_L1 = {"normal"}
FORBIDDEN_L1 = {
    "consecutive_clicks",
    "click_on_the_straight",
    "fire_button",
    "macro",
    "skill_stick_takeover",
}

OK_PLATFORMS = {"android"}


def load_profile(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def diagnose(profile: dict) -> list[str]:
    problems: list[str] = []
    platform = (profile.get("recommended_platform") or profile.get("platform") or "").lower()
    if platform == "ios":
        problems.append(
            "iOS: virtual mouse is 1 pointer — cannot hold L1 and move the stick at the same time."
        )
    elif platform and platform not in OK_PLATFORMS:
        problems.append(f"Unknown platform '{platform}'. Charge-while-walk needs Android multi-touch.")

    mode = (profile.get("controller_mode") or "").lower()
    if mode == "single_side":
        problems.append(
            "Single-side joystick mode reuses one stick. Switch to dual_side so L1 does not steal movement."
        )

    keys = {item.get("bind"): item for item in profile.get("keys", [])}
    l1 = keys.get("L1")
    stick = keys.get("LEFT_STICK")

    if not l1:
        problems.append("Missing L1 mapping.")
    else:
        l1_type = (l1.get("moowii_type") or "").lower()
        if l1_type in FORBIDDEN_L1:
            problems.append(
                f"L1 type '{l1_type}' cannot charge-while-walk. Set L1 to Gán phím / normal."
            )
        elif l1_type not in ALLOWED_L1:
            problems.append(f"L1 type '{l1_type}' is not a hold-to-charge button. Use 'normal'.")
        if l1.get("behavior") not in {None, "press_hold_release"}:
            problems.append("L1 must be press_hold_release (DOWN on press, UP on release).")
        if l1.get("independent_pointer") is False:
            problems.append("L1 must use its own touch pointer, independent from the left stick.")
        if (l1.get("target") or "") != "skill_1":
            problems.append("L1 should sit on the skill 1 icon.")

    if not stick:
        problems.append("Missing LEFT_STICK mapping.")
    else:
        if (stick.get("moowii_type") or "").lower() != "joystick":
            problems.append("Left stick must be type 'joystick' on the movement wheel, not D-pad taps.")
        if stick.get("independent_pointer") is False:
            problems.append("Left stick must keep its own pointer while L1 is held.")

    forbidden = {item.get("moowii_type") for item in profile.get("forbidden_l1_types", [])}
    if l1 and (l1.get("moowii_type") or "").lower() in forbidden:
        problems.append("L1 is using a type listed as forbidden in this profile.")

    return problems


def main() -> int:
    profile_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).with_name("mapping-profile.json")
    profile = load_profile(profile_path)
    problems = diagnose(profile)

    print(f"Profile: {profile.get('name', profile_path.name)}")
    print("Wanted: hold L1 = charge skill 1, release = cast, left stick still walks.")
    if problems:
        print("Status: BLOCKED")
        for item in problems:
            print(f"- {item}")
        return 1

    print("Status: OK for Android")
    print("- L1 = Gán phím / normal / press-hold-release on skill 1")
    print("- LEFT_STICK = independent joystick on the movement wheel")
    print("- Two pointers at once: stick moves while L1 stays down")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
