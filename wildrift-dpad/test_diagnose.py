#!/usr/bin/env python3
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from diagnose import diagnose, format_ok, load_profile

ROOT = Path(__file__).resolve().parent


class DpadTests(unittest.TestCase):
    def test_recommended_is_ok(self):
        self.assertEqual(diagnose(load_profile(ROOT / "mapping-profile.json")), [])

    def test_cli_ok(self):
        proc = subprocess.run(
            [sys.executable, str(ROOT / "diagnose.py")],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("Status: OK", proc.stdout)
        self.assertIn("đánh lính", proc.stdout)

    def test_cli_blocked_on_bad_file(self):
        profile = load_profile(ROOT / "mapping-profile.json")
        profile["dpad"][0]["type"] = "cloned"
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as handle:
            json.dump(profile, handle)
            path = handle.name
        proc = subprocess.run(
            [sys.executable, str(ROOT / "diagnose.py"), path],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 1)
        self.assertIn("Status: BLOCKED", proc.stdout)

    def test_movement_on_dpad_blocked(self):
        profile = load_profile(ROOT / "mapping-profile.json")
        profile["dpad"][0]["hud"] = "movement_wheel"
        profile["dpad"][0]["type"] = "joystick"
        problems = diagnose(profile)
        self.assertTrue(any("movement" in item.lower() or "joystick" in item.lower() for item in problems))

    def test_movement_bind_dpad_blocked(self):
        profile = load_profile(ROOT / "mapping-profile.json")
        profile["movement"]["bind"] = "DPAD"
        problems = diagnose(profile)
        self.assertTrue(any("LEFT_STICK" in item for item in problems))

    def test_movement_type_must_be_joystick(self):
        profile = load_profile(ROOT / "mapping-profile.json")
        profile["movement"]["type"] = "normal"
        problems = diagnose(profile)
        self.assertTrue(any("joystick" in item.lower() for item in problems))

    def test_cloned_blocked(self):
        profile = load_profile(ROOT / "mapping-profile.json")
        profile["dpad"][2]["type"] = "cloned"
        problems = diagnose(profile)
        self.assertTrue(any("cloned" in item for item in problems))

    def test_turbo_macro_blocked(self):
        profile = load_profile(ROOT / "mapping-profile.json")
        profile["dpad"][1]["type"] = "turbo"
        profile["dpad"][3]["type"] = "macro"
        problems = diagnose(profile)
        blob = " ".join(problems).lower()
        self.assertIn("turbo", blob)
        self.assertIn("macro", blob)

    def test_skill_cluster_blocked(self):
        profile = load_profile(ROOT / "mapping-profile.json")
        profile["dpad"][2]["hud"] = "skill_1"
        problems = diagnose(profile)
        self.assertTrue(any("skill" in item.lower() for item in problems))

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

    def test_wrong_lane_hud_blocked(self):
        profile = load_profile(ROOT / "mapping-profile.json")
        profile["dpad"][0]["hud"] = "recall"
        problems = diagnose(profile)
        self.assertTrue(any("scoreboard" in item for item in problems))

    def test_analog_dpad_blocked(self):
        profile = load_profile(ROOT / "mapping-profile.json")
        profile["analog_dpad"] = True
        problems = diagnose(profile)
        self.assertTrue(any("Analog" in item for item in problems))

    def test_missing_hud_prereq_blocked(self):
        profile = load_profile(ROOT / "mapping-profile.json")
        del profile["hud_prerequisites"]["attack_minion"]
        problems = diagnose(profile)
        self.assertTrue(any("attack_minion" in item for item in problems))

    def test_hud_first_false_blocked(self):
        profile = load_profile(ROOT / "mapping-profile.json")
        profile["hud_first"] = False
        problems = diagnose(profile)
        self.assertTrue(any("hud_first" in item for item in problems))

    def test_unknown_layout_blocked(self):
        profile = load_profile(ROOT / "mapping-profile.json")
        profile["layout"] = "wasd"
        problems = diagnose(profile)
        self.assertTrue(any("Unknown layout" in item for item in problems))

    def test_skill_upgrade_layout_ok(self):
        profile = load_profile(ROOT / "mapping-profile.json")
        profile["layout"] = "skill_upgrade"
        by_bind = {item["bind"]: item for item in profile["dpad"]}
        by_bind["DPAD_UP"]["hud"] = "upgrade_q"
        by_bind["DPAD_LEFT"]["hud"] = "upgrade_w"
        by_bind["DPAD_DOWN"]["hud"] = "upgrade_e"
        by_bind["DPAD_RIGHT"]["hud"] = "upgrade_r"
        self.assertEqual(diagnose(profile), [])
        self.assertTrue(any("+Q" in line for line in format_ok(profile)))

    def test_portrait_layout_ok(self):
        profile = load_profile(ROOT / "mapping-profile.json")
        profile["layout"] = "portrait_lock"
        by_bind = {item["bind"]: item for item in profile["dpad"]}
        by_bind["DPAD_UP"]["hud"] = "enemy_portrait_1"
        by_bind["DPAD_RIGHT"]["hud"] = "enemy_portrait_2"
        by_bind["DPAD_DOWN"]["hud"] = "enemy_portrait_3"
        by_bind["DPAD_LEFT"]["hud"] = "enemy_portrait_4"
        self.assertEqual(diagnose(profile), [])

    def test_json_lane_layout(self):
        raw = json.loads((ROOT / "mapping-profile.json").read_text(encoding="utf-8"))
        by_bind = {item["bind"]: item["hud"] for item in raw["dpad"]}
        self.assertEqual(by_bind["DPAD_UP"], "scoreboard")
        self.assertEqual(by_bind["DPAD_DOWN"], "recall")
        self.assertEqual(by_bind["DPAD_LEFT"], "attack_minion")
        self.assertEqual(by_bind["DPAD_RIGHT"], "attack_turret")
        self.assertEqual(raw["movement"]["type"], "joystick")
        self.assertFalse(raw["analog_dpad"])
        self.assertTrue(raw["hud_first"])

    def test_readme_has_hud_first_and_binds(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        for needle in (
            "Tùy chỉnh bố cục",
            "Đánh lính",
            "Đánh trụ",
            "Hồi thành",
            "Bảng điểm",
            "Gán phím",
            "Công cụ tập luyện",
        ):
            self.assertIn(needle, text)

    def test_guide_html_has_four_directions(self):
        html = (ROOT / "guide.html").read_text(encoding="utf-8")
        self.assertIn("Bảng điểm", html)
        self.assertIn("Hồi thành", html)
        self.assertIn("Đánh lính", html)
        self.assertIn("Đánh trụ", html)
        self.assertIn("pointerdown", html)

    def test_diagnose_does_not_mutate(self):
        profile = load_profile(ROOT / "mapping-profile.json")
        before = copy.deepcopy(profile)
        diagnose(profile)
        self.assertEqual(profile, before)


if __name__ == "__main__":
    unittest.main()
