"""用可手算的集合预报校验指标和时间坐标。"""

import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import xarray as xr

from scripts.score_ensemble import score


class EnsembleScoreTest(unittest.TestCase):
    def test_scores_and_preserves_times(self):
        """逐时刻输出误差、集合 CRPS 和集合标准差。"""
        time = np.array(["2021-02-01T00:00:00", "2021-02-01T01:00:00"], dtype="datetime64[ns]")
        truth = xr.Dataset({"weather": (("time", "y", "x"), np.array([1.0, 0.0]).reshape(2, 1, 1))})
        predictions = np.array([[0.0, 2.0], [2.0, 4.0]]).reshape(2, 2, 1, 1)
        forecast = xr.Dataset({"weather": (("ensemble", "time", "y", "x"), predictions)})

        with TemporaryDirectory() as directory:
            samples = Path(directory) / "samples.nc"
            output = Path(directory) / "metrics.nc"
            time_list = Path(directory) / "times.yaml"
            xr.Dataset(coords={"time": time}).to_netcdf(samples)
            truth.to_netcdf(samples, group="truth", mode="a")
            forecast.to_netcdf(samples, group="prediction", mode="a")
            time_list.write_text('times:\n  - "2021-02-01T00:00:00"\n  - "2021-02-01T01:00:00"\n', encoding="utf-8")
            with samples.open("rb") as source, redirect_stdout(StringIO()):
                score(source, output, time_list)

            with xr.open_dataset(output) as metrics:
                self.assertEqual(metrics.attrs["ensemble_members"], 2)
                np.testing.assert_array_equal(metrics.time.values, time)
                for metric, expected in {
                    "mae": [0.0, 3.0],
                    "rmse": [0.0, 3.0],
                    "crps": [0.5, 2.5],
                    "spread": [1.0, 1.0],
                }.items():
                    with self.subTest(metric=metric):
                        np.testing.assert_allclose(metrics.weather.sel(metric=metric).values, expected)

            time_list = Path(directory) / "times.txt"
            time_list.write_text("2021-02-01T01:00:00\n2021-02-01T00:00:00\n", encoding="utf-8")
            wrong_order_output = Path(directory) / "wrong-order.nc"
            with self.assertRaisesRegex(ValueError, "时刻或顺序"):
                score(samples, wrong_order_output, time_list)
            self.assertFalse(wrong_order_output.exists())
