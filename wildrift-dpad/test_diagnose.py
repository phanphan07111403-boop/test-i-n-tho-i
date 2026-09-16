#!/usr/bin/env python3
import copy
import json
import unittest
from pathlib import Path

from diagnose import diagnose, load_profile

ROOT = Path(__file__).resolve().parent


class DpadTests(unittest.TestCase):
    def test_recommended_is_ok(self):
        self.assertEqual(diagnose(load_profile(ROOT / "mapping-profile.json")), [])

    def test_movement_on_dpad_blocked(self):
        profile = load_profile(ROOT / "mapping-profile.json")
        profile["dpad"][0]["hud"] = "movement_wheel"
        profile["dpad"][0]["type"] = "joystick"
        problems = diagnose(profile)
        self.assertTrue(any("movement" in item.lower() or "joystick" in item for item in problems))

    def test_cloned_blocked(self):
        profile = load_profile(ROOT / "mapping-profile.json")
        profile["dpad"][2]["type"] = "cloned"
        problems = diagnose(profile)
        self.assertTrue(any("cloned" in item for item in problems))

    def test_duplicate_hud_blocked(self):
        profile = load_profile(ROOT / "mapping-profile.json")
        profile["dpad"][3]["hud"] = profile["dpad"][2]["hud"]
        problems = diagnose(profile)
        self.assertTrue(any("same HUD" in item for item in problems))

    def test_missing_direction_blocked(self):
        profile = load_profile(ROOT / "mapping-profile.json")
        profile["dpad"] = profile["dpad"][:3]
        problems = diagnose(profile)
        self.assertTrue(any("Missing" in item for item in problems))

    def test_json_lane_layout(self):
        raw = json.loads((ROOT / "mapping-profile.json").read_text(encoding="utf-8"))
        by_bind = {item["bind"]: item["hud"] for item in raw["dpad"]}
        self.assertEqual(by_bind["DPAD_UP"], "scoreboard")
        self.assertEqual(by_bind["DPAD_DOWN"], "recall")
        self.assertEqual(by_bind["DPAD_LEFT"], "attack_minion")
        self.assertEqual(by_bind["DPAD_RIGHT"], "attack_turret")
        self.assertEqual(raw["movement"]["type"], "joystick")

    def test_diagnose_does_not_mutate(self):
        profile = load_profile(ROOT / "mapping-profile.json")
        before = copy.deepcopy(profile)
        diagnose(profile)
        self.assertEqual(profile, before)


if __name__ == "__main__":
    unittest.main()
