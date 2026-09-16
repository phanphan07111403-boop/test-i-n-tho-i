#!/usr/bin/env python3
"""Validate a GameSir mapping profile for real Cloned Mode (two simultaneous outputs)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

CLONED = {"cloned"}
NOT_CLONED = {
    "normal",
    "separated_press_release",
    "turbo",
    "macro",
    "hardware_l4_r4",
}
OK_PLATFORMS = {"android"}
BOTH_EDGES = {"press", "release"}


def load_profile(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def diagnose(profile: dict) -> list[str]:
    problems: list[str] = []
    platform = (profile.get("recommended_platform") or profile.get("platform") or "").lower()
    if platform == "ios":
        problems.append(
            "iOS: GameSir World mapping is blocked since 13.4 — Cloned Mode is not available."
        )
    elif platform and platform not in OK_PLATFORMS:
        problems.append(f"Unknown platform '{platform}'. Cloned Mode lives in Android GameSir World.")

    click_mode = (profile.get("click_mode") or "").lower()
    if click_mode and click_mode not in CLONED:
        problems.append(
            f"click_mode '{click_mode}' is not Cloned Mode. Open ⚙️ → Click Mode → Cloned Mode."
        )

    keys = profile.get("keys") or []
    if not keys:
        problems.append("Missing mapped keys.")
        return problems

    for key in keys:
        bind = key.get("bind") or "(unbound)"
        key_type = (key.get("gamesir_type") or "").lower()
        if key_type in NOT_CLONED:
            problems.append(
                f"{bind}: type '{key_type}' is not Cloned Mode. "
                "Use ⚙️ → Cloned Mode, not Separated / Turbo / Macro / L4 hardware remap."
            )
            continue
        if key_type not in CLONED:
            problems.append(f"{bind}: type '{key_type}' is not Cloned Mode.")
            continue

        outputs = key.get("outputs") or []
        if len(outputs) < 2:
            problems.append(f"{bind}: Cloned Mode needs two child buttons. Drag the second clone onto another HUD spot.")
        targets = [item.get("target") for item in outputs]
        if len(outputs) >= 2 and len(set(targets)) < 2:
            problems.append(
                f"{bind}: both clones sit on the same target. Move one child; overlapping clones act like Normal."
            )
        if key.get("simultaneous") is False:
            problems.append(
                f"{bind}: outputs are sequential. That is Separated press & release, not Cloned Mode."
            )
        if (key.get("behavior") or "") != "press_and_release_both":
            problems.append(
                f"{bind}: Cloned Mode fires both children on press and on release. "
                "If only one edge fires, you picked Separated or Normal."
            )
        for item in outputs:
            fires = set(item.get("fires_on") or [])
            if fires and fires != BOTH_EDGES:
                problems.append(
                    f"{bind}/{item.get('id')}: clone child must fire on both press and release, got {sorted(fires)}."
                )

    return problems


def main() -> int:
    profile_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).with_name("mapping-profile.json")
    profile = load_profile(profile_path)
    problems = diagnose(profile)

    print(f"Profile: {profile.get('name', profile_path.name)}")
    print("Wanted: ⚙️ Click Mode → Cloned Mode; two HUD spots tap together on press and on release.")
    if problems:
        print("Status: BLOCKED")
        for item in problems:
            print(f"- {item}")
        return 1

    print("Status: OK for Android GameSir World")
    print("- click_mode = cloned (not separated / turbo / macro)")
    print("- two distinct child targets")
    print("- both children fire together on press and on release")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
