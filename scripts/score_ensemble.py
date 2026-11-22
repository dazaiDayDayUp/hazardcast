"""按时刻计算集合预报的逐变量空间平均指标。"""

import argparse
from pathlib import Path
from typing import BinaryIO

import numpy as np
import xarray as xr
import xskillscore as xs
from omegaconf import OmegaConf


def load_time_list(path: Path) -> list[str]:
    """读取有序的评估时刻清单，兼容旧的逐行文本。"""
    if path.suffix.lower() in {".yaml", ".yml"}:
        config = OmegaConf.load(path)
        times = config.get("times") if OmegaConf.is_dict(config) else None
        if not OmegaConf.is_list(times) or any(not isinstance(time, str) for time in times):
            raise ValueError("评估清单的 times 必须是字符串列表")
        return list(times)
    lines = path.read_text(encoding="utf-8").splitlines()
    return [line for line in lines if line and not line.startswith("#")]


def score(path: Path | BinaryIO, output: Path, time_list: Path | None = None):
    """按时刻读取和评分，使内存占用与整个评估集的长度无关。"""
    with xr.open_datatree(path, engine="h5netcdf", cache=False) as root:
        truth = root["truth"].dataset
        prediction = root["prediction"].dataset
        if set(truth.data_vars) != set(prediction.data_vars):
            raise ValueError("预报与参考场的变量不一致")
        truth, prediction = xr.align(truth, prediction, join="exact")
        if time_list is not None:
            expected = load_time_list(time_list)
            actual = truth.time.dt.strftime("%Y-%m-%dT%H:%M:%S").values.tolist()
            if actual != expected:
                raise ValueError("预测文件的时刻或顺序与评估清单不一致")
        if not truth.sizes["time"] or not prediction.sizes["ensemble"]:
            raise ValueError("评估至少需要一个时刻和一个集合成员")

        spatial_dims = ["y", "x"]
        metric_axis = xr.IndexVariable("metric", ["mae", "rmse", "crps", "spread"])
        per_time = []
        for index in range(truth.sizes["time"]):
            time_slice = slice(index, index + 1)
            target = truth.isel(time=time_slice).load()
            members = prediction.isel(time=time_slice).load()
            ensemble_mean = members.mean("ensemble", skipna=False)
            metrics = xr.concat(
                [
                    xs.mae(target, ensemble_mean, dim=spatial_dims),
                    xs.rmse(target, ensemble_mean, dim=spatial_dims),
                    xs.crps_ensemble(target, members, member_dim="ensemble", dim=spatial_dims),
                    members.std("ensemble", skipna=False).mean(spatial_dims, skipna=False),
                ],
                dim=metric_axis,
            )
            if not np.isfinite(metrics.to_array().to_numpy()).all():
                raise ValueError(f"第 {index + 1} 个时刻的评估结果包含非有限值")
            per_time.append(metrics)
        scores = xr.concat(per_time, dim="time")
        scores.attrs["ensemble_members"] = prediction.sizes["ensemble"]
        scores.to_netcdf(output)
        print(f"已评估 {scores.sizes['time']} 个时刻、{prediction.sizes['ensemble']} 个成员")
        print(scores.mean("time").to_dataframe().to_string())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("samples", type=Path, help="包含参考场和预报的 NetCDF 文件")
    parser.add_argument("output", type=Path, help="指标输出路径")
    parser.add_argument("--time-list", type=Path, help="按顺序列出每个评估时刻的清单")
    args = parser.parse_args()
    score(args.samples, args.output, args.time_list)
