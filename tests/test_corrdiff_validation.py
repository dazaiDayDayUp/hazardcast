"""防止 CorrDiff 对照实验意外更换评估时刻。"""

import hashlib
import unittest
from datetime import datetime
from pathlib import Path

from scripts.score_ensemble import load_time_list


class CorrDiffValidationTest(unittest.TestCase):
    def test_validation_times_match_published_split(self):
        """固定上游 validation_big 的时间内容和顺序。"""
        project = Path(__file__).resolve().parents[1]
        path = project / "configs/experiments/corrdiff-validation-times.yaml"
        times = load_time_list(path)
        self.assertEqual(len(times), 205)
        self.assertEqual(len(set(times)), 205)
        self.assertTrue(all(datetime.fromisoformat(time).year == 2021 for time in times))
        digest = hashlib.sha256(("\n".join(times) + "\n").encode("utf-8")).hexdigest()
        self.assertEqual(digest, "36bfefcfbda69bffe3b86fecbd2ef67c9c84ee92579f883937e3671171b4f01e")
