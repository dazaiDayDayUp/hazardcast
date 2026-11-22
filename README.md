# HazardCast

HazardCast 研究公里尺度区域天气场的时空超分辨，从空间较粗、时间采样较稀疏的序列重建同一时段内空间和时间分辨率更高的天气场。研究方向是结合 CorrDiff 和闭式连续时间网络（CfC），并探索物理增强方法，通过可重复的对照实验检验其效果。

第一阶段复现 CorrDiff 在台湾的同一时刻空间降尺度实验，建立空间降尺度基线和可复用的实验流程。

当前进度和待确认事项见 [项目交接](docs/2026-11-23-status.md)。

## 当前目录

- `reference/` 存放本地文献副本。CorrDiff 正文、补充材料和同行评审放在 `reference/corrdiff/`，CfC 论文放在 `reference/cfc/`。PDF 由各自本地保存。
- `external/` 存放 PhysicsNeMo 和 CfC 的上游代码。PhysicsNeMo 用于当前 CorrDiff 实验，CfC 供后续研究查阅。
- `configs/experiments/` 和 `scripts/` 存放实验配置与运行入口。
- `tests/` 存放可在中央处理器上运行的自动测试。
- `data/` 存放数据集入口，`checkpoints/` 存放下载的模型权重，`runs/` 保存各次运行的配置、日志和产物。

## 安装当前实验环境

在项目根目录执行。当前环境使用 Linux x86_64、Python 3.12 和 PyTorch 的 CUDA 12.9 构建。

```bash
conda create -n hazardcast python=3.12 pip
conda activate hazardcast
```

首次准备 `external/physicsnemo` 时，从上游克隆。

```bash
git clone --filter=blob:none --no-checkout https://github.com/NVIDIA/physicsnemo.git external/physicsnemo
```

切到基线对应的上游提交，再安装实验依赖。

```bash
git -C external/physicsnemo checkout --detach 5af5afd818bf2f120b61fbf4ad920759bfdc8372
python -m pip install -r requirements.txt
python -m pip check
```

## 运行 CorrDiff 小规模验证

每个检出目录可以通过软链接接入同一份只读的台湾 CWA 数据。首次配置时，将 `CWA_ZARR` 设为本机 Zarr 的绝对路径。

```bash
mkdir -p data
ln -s "$CWA_ZARR" data/cwa_dataset.zarr
```

在已经激活的 `hazardcast` 环境中，通过一个入口运行回归、残差扩散、采样和评估。

```bash
python scripts/run_experiment.py configs/experiments/corrdiff-smoke.yaml --gpu 1
```

`--data` 可以指定其他数据路径，`--upstream` 可以指定共享的 PhysicsNeMo 检出目录。本次配置以缩小的网络和少量训练样本验证流程。实验设置和结论记录在 [CorrDiff 实验记录](docs/2026-11-23-corrdiff.md)。

## 运行测试

在项目根目录执行。当前测试使用临时生成的样本。

```bash
python -m unittest discover -s tests -v
```
