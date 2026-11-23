# HazardCast

**研究目标是结合 CorrDiff 和闭式连续时间网络（CfC），构建公里尺度区域天气的时空超分辨模型。** 模型从空间较粗、时间采样较稀疏的天气场序列重建同一时段内更细、更密的天气场。后续将设计两者的结合方式和物理增强方案，并通过对照实验评估效果。

当前阶段在台湾 CWA 数据上复现原版 CorrDiff 的同一时刻空间降尺度，建立对照基线。进度与结果见[项目交接](docs/2026-11-23-status.md)和 [CorrDiff 实验记录](docs/2026-11-23-corrdiff.md)。NGC 第 1 版权重训练覆盖 2018–2021 年且链接修订前 v3，不能用于正式 v4 表 1 的 2021 年留出对照；全量发布包推理已完成，修订版权重在公开渠道未找到，来源核验仍在继续。

文献库提供 [13 类文献总索引与规范目录说明](reference/literature/README.md)，研究任务、模型集成、对照矩阵和分阶段路线见[跨主题综合综述](docs/2026-11-23-literature-review.md)。

## 当前目录

```text
├── configs/experiments/  实验配置
├── scripts/              实验运行与评估入口
├── tests/                自动测试
├── docs/                 带日期的实验记录和项目交接
├── external/             上游代码（PhysicsNeMo、CfC）
├── reference/            按论文整理的本地文献
├── data/                 只读数据集入口
├── pretrained/           下载的预训练模型
└── runs/                 各次运行的配置、日志和产物
```

项目自有方法的目录随实验需要增设。基线定版后，从同一基线为各个研究想法建立独立工作树。

## 快速开始

在项目根目录准备环境（Linux x86_64、Python 3.12、PyTorch CUDA 12.9）。已有环境或上游代码时，跳过对应的创建或克隆命令。

```bash
conda create -n hazardcast python=3.12 pip
conda activate hazardcast
git clone --filter=blob:none --no-checkout https://github.com/NVIDIA/physicsnemo.git external/physicsnemo
git -C external/physicsnemo checkout --detach 5af5afd818bf2f120b61fbf4ad920759bfdc8372
python -m pip install -r requirements.txt
```

运行测试和 CorrDiff 小规模验证。验证默认读取 `data/cwa_dataset.zarr`，可将它软链到已有数据，也可用 `--data` 指定只读数据集路径。`--gpu` 填写本机可用的 GPU 编号。

```bash
python -m unittest discover -s tests -v
python scripts/run_experiment.py configs/experiments/corrdiff-smoke.yaml --gpu 1
```
