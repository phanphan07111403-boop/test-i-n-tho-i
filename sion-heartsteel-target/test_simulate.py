#!/usr/bin/env python3
import json
import unittest
from pathlib import Path

from simulate_heartsteel_target import (
    POLICIES,
    CHARGE_S,
    PER_TARGET_CD,
    bonus_hp,
    proc_damage,
    simulate,
)

ROOT = Path(__file__).resolve().parent


class HeartsteelTargetTests(unittest.TestCase):
    def test_proc_math(self):
        self.assertAlmostEqual(proc_damage(4000), 140 + 0.035 * 4000)
        self.assertAlmostEqual(bonus_hp(280), 42)

    def test_portrait_beats_auto(self):
        data = simulate()
        portrait = data["results"]["portrait_cycle_ready"]
        closest = data["results"]["auto_closest"]
        lowest = data["results"]["auto_lowest_hp"]
        self.assertGreater(portrait["procs"], closest["procs"])
        self.assertGreater(portrait["procs"], lowest["procs"])
        self.assertGreaterEqual(len(portrait["unique_targets"]), 4)
        self.assertEqual(closest["unique_targets"], ["tank"])
        self.assertEqual(lowest["unique_targets"], ["adc"])

    def test_no_heartsteel_mode_in_answer(self):
        data = simulate()
        self.assertTrue(data["answer"].startswith("No."))
        self.assertEqual(data["best_policy"], "portrait_cycle_ready")

    def test_per_target_cooldown(self):
        data = simulate()
        hits = data["results"]["portrait_cycle_ready"]["hits"]
        first = next(h for h in hits if h["target"] == "tank")
        second = next(h for h in hits[1:] if h["target"] == "tank")
        self.assertGreaterEqual(second["t"] - first["t"], PER_TARGET_CD - 1e-6)

    def test_cannot_proc_before_charge(self):
        data = simulate()
        for policy in POLICIES:
            times = [h["t"] for h in data["results"][policy]["hits"]]
            self.assertTrue(times)
            self.assertGreaterEqual(min(times), CHARGE_S)

    def test_written_outputs_match(self):
        from simulate_heartsteel_target import main

        main()
        dumped = json.loads((ROOT / "results.json").read_text(encoding="utf-8"))
        self.assertEqual(dumped["best_policy"], "portrait_cycle_ready")
        report = (ROOT / "report.txt").read_text(encoding="utf-8")
        self.assertIn("No.", report)
        self.assertIn("portrait_cycle_ready", report)


if __name__ == "__main__":
    unittest.main()
