#!/usr/bin/env python3
import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent


class ReportTests(unittest.TestCase):
    def test_best_app_is_global_moowii(self):
        data = json.loads((ROOT / "community.json").read_text(encoding="utf-8"))
        self.assertEqual(data["best_app"]["package"], "com.geekwon.moyuplayer.global")
        self.assertIsNone(data["gace_cloud_codes"]["toc_chien_android"])
        self.assertEqual(data["wild_rift_1to1_layout"][1]["bind"], "L1")
        self.assertEqual(data["wild_rift_1to1_layout"][1]["type"], "normal_hold")
        self.assertIn("incompatible", data["play_store_on_s24_ultra"]["meaning"])

    def test_print_report_runs(self):
        out = subprocess.check_output(["python3", str(ROOT / "print_report.py")], text=True)
        self.assertIn("com.geekwon.moyuplayer.global", out)
        self.assertIn("none (map by hand)", out)


if __name__ == "__main__":
    unittest.main()
