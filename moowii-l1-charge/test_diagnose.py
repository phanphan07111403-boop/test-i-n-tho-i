#!/usr/bin/env python3
import json
import unittest
from pathlib import Path

from diagnose import diagnose, load_profile

ROOT = Path(__file__).resolve().parent


class DiagnoseTests(unittest.TestCase):
    def test_recommended_profile_is_ok(self):
        profile = load_profile(ROOT / "mapping-profile.json")
        self.assertEqual(diagnose(profile), [])

    def test_macro_l1_is_blocked(self):
        profile = load_profile(ROOT / "mapping-profile.json")
        for key in profile["keys"]:
            if key["bind"] == "L1":
                key["moowii_type"] = "macro"
        problems = diagnose(profile)
        self.assertTrue(any("macro" in item for item in problems))

    def test_skill_stick_takeover_is_blocked(self):
        profile = load_profile(ROOT / "mapping-profile.json")
        for key in profile["keys"]:
            if key["bind"] == "L1":
                key["moowii_type"] = "skill_stick_takeover"
        problems = diagnose(profile)
        self.assertTrue(any("Gán phím" in item or "skill_stick_takeover" in item for item in problems))

    def test_ios_is_blocked(self):
        profile = load_profile(ROOT / "mapping-profile.json")
        profile["recommended_platform"] = "ios"
        problems = diagnose(profile)
        self.assertTrue(any(item.startswith("iOS:") for item in problems))

    def test_shared_pointer_is_blocked(self):
        profile = load_profile(ROOT / "mapping-profile.json")
        for key in profile["keys"]:
            key["independent_pointer"] = False
        problems = diagnose(profile)
        self.assertGreaterEqual(len(problems), 2)

    def test_json_is_valid(self):
        raw = json.loads((ROOT / "mapping-profile.json").read_text(encoding="utf-8"))
        self.assertEqual(raw["keys"][1]["bind"], "L1")
        self.assertEqual(raw["keys"][1]["moowii_type"], "normal")


if __name__ == "__main__":
    unittest.main()
