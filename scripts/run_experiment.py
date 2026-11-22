"""按配置顺序运行实验，并保存每一步的配置、日志和产物。"""

import argparse
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from omegaconf import OmegaConf


PROJECT = Path(__file__).resolve().parents[1]


def run_stage(stage, run_dir, env):
    """在独立目录运行一个阶段，并检查声明的产物。"""
    stage_dir = run_dir / stage["name"]
    stage_dir.mkdir()
    command = [sys.executable, stage["script"], *stage["args"], *stage.get("common_args", [])]
    log_path = stage_dir / "运行.log"
    print(f"运行 {stage['name']}，日志位于 {log_path}", flush=True)
    with log_path.open("w", encoding="utf-8") as log:
        subprocess.run(command, cwd=stage_dir, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
    for path in stage["outputs"]:
        if not Path(path).is_file():
            raise RuntimeError(f"{stage['name']} 未生成预期产物 {path}")
    print(f"完成 {stage['name']}", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path, help="实验配置文件")
    parser.add_argument(
        "--data", type=Path, default=PROJECT / "data/cwa_dataset.zarr",
        help="只读数据集路径，默认读取项目内的 data/cwa_dataset.zarr",
    )
    parser.add_argument("--gpu", required=True, type=int, help="nvidia-smi 显示的物理设备编号")
    parser.add_argument("--upstream", type=Path, default=PROJECT / "external/physicsnemo", help="PhysicsNeMo 检出目录")
    parser.add_argument("--run-dir", type=Path, help="本次运行的产物目录，默认在本工作树的 runs 下")
    args = parser.parse_args()

    dataset = args.data.absolute()
    if not dataset.exists():
        parser.error(f"数据路径不存在或无法访问：{dataset}")
    upstream = args.upstream.resolve(strict=True)
    config = OmegaConf.load(args.config)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    run_dir = (args.run_dir or PROJECT / "runs" / config.name / stamp).resolve()
    config.paths = {"project": str(PROJECT), "upstream": str(upstream), "dataset": str(dataset), "run": str(run_dir)}
    stages = OmegaConf.to_container(config, resolve=True, throw_on_missing=True)["stages"]
    for stage in stages:
        if not Path(stage["script"]).is_file():
            parser.error(f"找不到阶段脚本 {stage['script']}")

    gpu_uuid = subprocess.check_output(
        ["nvidia-smi", "--id", str(args.gpu), "--query-gpu=uuid", "--format=csv,noheader"],
        text=True,
    ).strip()
    if not gpu_uuid.startswith("GPU-") or "\n" in gpu_uuid:
        parser.error(f"无法定位物理 GPU {args.gpu}")
    config.gpu = {"index": args.gpu, "uuid": gpu_uuid}
    config.upstream_revision = subprocess.check_output(
        ["git", "-C", str(upstream), "rev-parse", "HEAD"], text=True
    ).strip()
    env = {**os.environ, "CUDA_VISIBLE_DEVICES": gpu_uuid, "WANDB_MODE": "disabled",
           "PYTHONDONTWRITEBYTECODE": "1", "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1"}
    run_dir.mkdir(parents=True, exist_ok=False)
    OmegaConf.save(config, run_dir / "config.yaml", resolve=True)
    for stage in stages:
        try:
            run_stage(stage, run_dir, env)
        except subprocess.CalledProcessError as error:
            sys.exit(f"阶段 {stage['name']} 失败，退出码 {error.returncode}。请查看该阶段的运行日志。")
    print(f"实验完成，结果位于 {run_dir}")


if __name__ == "__main__":
    main()
