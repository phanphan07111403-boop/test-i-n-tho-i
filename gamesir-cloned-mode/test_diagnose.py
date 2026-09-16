#!/usr/bin/env python3
import copy
import json
import unittest
from pathlib import Path

from diagnose import diagnose, load_profile

ROOT = Path(__file__).resolve().parent


class DiagnoseTests(unittest.TestCase):
    def test_recommended_profile_is_ok(self):
        profile = load_profile(ROOT / "mapping-profile.json")
        self.assertEqual(diagnose(profile), [])

    def test_separated_is_blocked(self):
        profile = load_profile(ROOT / "mapping-profile.json")
        profile["click_mode"] = "separated_press_release"
        profile["keys"][0]["gamesir_type"] = "separated_press_release"
        profile["keys"][0]["simultaneous"] = False
        problems = diagnose(profile)
        self.assertTrue(any("Cloned Mode" in item or "separated" in item for item in problems))

    def test_turbo_is_blocked(self):
        profile = load_profile(ROOT / "mapping-profile.json")
        profile["keys"][0]["gamesir_type"] = "turbo"
        problems = diagnose(profile)
        self.assertTrue(any("turbo" in item for item in problems))

    def test_macro_is_blocked(self):
        profile = load_profile(ROOT / "mapping-profile.json")
        profile["keys"][0]["gamesir_type"] = "macro"
        problems = diagnose(profile)
        self.assertTrue(any("macro" in item for item in problems))

    def test_one_output_is_blocked(self):
        profile = load_profile(ROOT / "mapping-profile.json")
        profile["keys"][0]["outputs"] = [profile["keys"][0]["outputs"][0]]
        problems = diagnose(profile)
        self.assertTrue(any("two child" in item for item in problems))

    def test_same_target_is_blocked(self):
        profile = load_profile(ROOT / "mapping-profile.json")
        profile["keys"][0]["outputs"][1]["target"] = profile["keys"][0]["outputs"][0]["target"]
        problems = diagnose(profile)
        self.assertTrue(any("same target" in item for item in problems))

    def test_ios_is_blocked(self):
        profile = load_profile(ROOT / "mapping-profile.json")
        profile["recommended_platform"] = "ios"
        problems = diagnose(profile)
        self.assertTrue(any(item.startswith("iOS:") for item in problems))

    def test_press_only_clone_is_blocked(self):
        profile = load_profile(ROOT / "mapping-profile.json")
        for item in profile["keys"][0]["outputs"]:
            item["fires_on"] = ["press"]
        problems = diagnose(profile)
        self.assertTrue(any("press and release" in item for item in problems))

    def test_json_is_valid(self):
        raw = json.loads((ROOT / "mapping-profile.json").read_text(encoding="utf-8"))
        self.assertEqual(raw["click_mode"], "cloned")
        self.assertEqual(len(raw["keys"][0]["outputs"]), 2)
        self.assertTrue(raw["keys"][0]["simultaneous"])

    def test_diagnose_does_not_mutate_profile(self):
        profile = load_profile(ROOT / "mapping-profile.json")
        before = copy.deepcopy(profile)
        diagnose(profile)
        self.assertEqual(profile, before)


if __name__ == "__main__":
    unittest.main()
