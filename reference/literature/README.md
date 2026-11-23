# HazardCast 文献数据库

本目录服务于 **CorrDiff+CfC 公里尺度天气时空超分辨与物理增强**研究。13 个主题文件保留各自的研究脉络，允许同一论文在不同主题中重复出现；`catalog.yaml` 是全局去重后的规范总目录，`hazardcast.bib` 是对应的 BibTeX 数据库。

## 总体统计

- 主题元数据文件：13 个，每个 10 条，共 130 条来源记录。
- 规范总目录：**117 篇唯一论文**，合并 **13 条跨主题重复记录**。
- 本地全文：**105 篇论文有 PDF**，共引用 **114 个不同 PDF 文件**；同一论文可能保存不同来源或版本的多个副本。
- 仅元数据：**12 篇论文没有本地 PDF**，仍保留 DOI、URL 和主题交叉引用。
- 114 个 PDF 中，113 个位于 `reference/papers/`，另 1 个是 `reference/corrdiff/` 下已有的 CorrDiff 原文。

PDF 由项目根目录 `.gitignore` 中的 `/reference/**/*.pdf` 规则忽略，不进入 Git；YAML、Markdown、BibTeX 和校验摘要进入版本管理。因此克隆仓库后，本地 PDF 数量取决于是否另行取得这些文件。若工作区完全没有目录中声明的本地 PDF，PDF 内容测试会显示为 skipped，使 fresh clone 的默认全量测试可以通过；只要存在其中任意一份 PDF，测试就会严格要求**全部**声明 PDF 存在且 SHA-256 匹配，部分副本环境下的缺失文件或摘要错误仍会失败。

## 13 个主题及范围

| 主题 | 元数据与综述 | 收录范围 |
|---|---|---|
| 经典与动力降尺度 | [metadata](metadata/classical-downscaling.yaml) · [综述](topics/classical-downscaling.md) | 区域模式动力降尺度、MOS、完美预后、回归、CCA、analog、天气分型与经典随机天气发生器。 |
| 连续时间与 CfC | [metadata](metadata/continuous-time-cfc.yaml) · [综述](topics/continuous-time-cfc.md) | Neural ODE/SDE/CDE/RDE、不规则观测、Latent ODE、LTC、CfC、CRU 与 Liquid-S4。 |
| 数据集与公平基线 | [metadata](metadata/datasets-baselines.yaml) · [综述](topics/datasets-baselines.md) | ERA5、WRF、CWA 雷达资料同化、真实跨产品配对、CorrDiff 母本及统一数据划分和评估协议。 |
| 确定性统计降尺度 | [metadata](metadata/deterministic-downscaling.yaml) · [综述](topics/deterministic-downscaling.md) | 随机森林、CNN、UNet、单图像超分辨和 GAN 对照，区分同源粗化、跨模式映射与时空重建。 |
| 扩散天气降尺度 | [metadata](metadata/diffusion-downscaling.yaml) · [综述](topics/diffusion-downscaling.md) | 条件扩散、残差扩散、潜空间与视频扩散、跨模式偏差校正、公里尺度区域和全球生成。 |
| 高效生成采样 | [metadata](metadata/efficient-generative-sampling.yaml) · [综述](topics/efficient-generative-sampling.md) | DDPM、DDIM、score SDE、EDM、DPM-Solver、蒸馏、一致性模型、LDM、DiT 与 EDM2。 |
| 频谱、结构与极端评估 | [metadata](metadata/evaluation-spectra-extremes.yaml) · [综述](topics/evaluation-spectra-extremes.md) | 功率谱、结构函数、FSS、SAL、对象评估、EDI/SEDI、variogram score、集合 FSS 与跨变量诊断。 |
| 物理引导与硬约束 | [metadata](metadata/physics-constraints.yaml) · [综述](topics/physics-constraints.md) | PDE 软约束、守恒输出层、变量重参数化、采样期物理校正及可微动力—学习混合模型。 |
| 概率校准与集合后处理 | [metadata](metadata/probabilistic-calibration.yaml) · [综述](topics/probabilistic-calibration.md) | CRPS、rank histogram、PIT、spread–skill、BMA、copula/ECC、神经后处理与概率轨迹评估。 |
| 时空骨干架构 | [metadata](metadata/spatiotemporal-architectures.yaml) · [综述](topics/spatiotemporal-architectures.md) | ConvLSTM、PredRNN、PhyDNet、FNO、图网络、SimVP、TAU、Earthformer、FourCastNet 与 GraphCast。 |
| 天气时间超分辨 | [metadata](metadata/temporal-super-resolution.yaml) · [综述](topics/temporal-super-resolution.md) | 双边时间插值、联合时空超分辨、任意目标时刻重建、时空联合先验及公里尺度次小时生成。 |
| 视频预测与插值 | [metadata](metadata/video-prediction-interpolation.yaml) · [综述](topics/video-prediction-interpolation.md) | 递归预测、核预测、光流、时空 Transformer、隐式神经表示、灵活条件与视频扩散。 |
| 生成式天气预报 | [metadata](metadata/weather-generative.yaml) · [综述](topics/weather-generative.md) | DGMR、NowcastNet、PreDiff、DYffusion、GenCast，以及全球预报骨干和天气气候基础模型。 |

## 去重和目录字段

构建脚本先规范化 DOI：去除 `doi:` 或 DOI URL 前缀、URL 解码、统一大小写；再规范化标题：忽略重音、大小写、标点和空白。任一键匹配的来源记录会合并为一个规范条目，同一标题若声明了相互冲突的 DOI 则报错，不会静默合并。

`catalog.yaml` 的每篇论文包含：

- `id`：与 BibTeX key 相同的稳定标识，由第一作者姓氏、年份和标题实义词生成；如发生碰撞，追加由规范身份计算的摘要后缀。
- 规范书目及研究摘要：`title`、`authors`、`year`、`venue`、`doi`、`url`、`oa_url`、`methods`、`datasets`、`metrics`、`relevance`。
- `topics` 与 `sources`：保留全部主题名、原始条目 ID、元数据文件和主题综述路径；各来源自己的 DOI、URL 和 PDF 信息也保留在 `sources` 中。
- `pdf_path`、`sha256`：规范主副本；`pdf_copies`：该论文所有不同本地 PDF 及其 SHA-256。重复记录可能引用同一文件，也可能引用不同版本，二者不会混淆。
- `access: metadata-only` 且没有 PDF 字段的条目表示仅有元数据，不表示论文无效。

规范字段按主题名和原始 ID 的固定顺序选择主记录，并用其他来源补齐缺失的 DOI 等字段。主题特定的方法、数据和评价全文仍以 `metadata/*.yaml` 为准。生成过程不联网、不补写未知文献事实。

## 使用与更新

新增或修订文献时，只编辑相应主题的 `metadata/<topic>.yaml` 和 `topics/<topic>.md`，不要手改两个生成文件。若下载 PDF，请同时填写相对项目根目录的 `pdf_path` 和实际文件的 SHA-256；可用 `sha256sum <文件>` 计算。

在 `hazardcast` Conda 环境中，从项目根目录运行：

```bash
conda activate hazardcast
python scripts/build_literature_catalog.py
python scripts/build_literature_catalog.py --check
python -m unittest tests.test_literature_catalog -v
python -m unittest discover -s tests -v
```

第一条命令重建目录和 BibTeX；`--check` 不写文件，只验证现有产物与主题元数据完全一致。脚本输出不含时间戳，相同输入重复运行会得到相同字节。若增删论文使总数变化，还应同步更新本 README 的统计。

## 引用方式

`hazardcast.bib` 使用 `@article`、`@inproceedings` 和 `@misc`，尽量从原始 `venue` 拆分期刊或会议、卷、期和页码，并保留规范 DOI、落地页 `url` 与开放获取 `oa_url`。论文标题和作者保留原文及 Unicode 字符。

在 LaTeX 中可将本文件加入文献库，例如：

```tex
\bibliography{reference/literature/hazardcast}
```

引用时直接使用规范条目的 `id`，例如 `\cite{mardani2025residual}`。所有 key 可在 `catalog.yaml` 查询；跨主题论文只需引用同一个 key，不应根据主题自行复制 BibTeX 条目。

## 目录结构

```text
reference/literature/
├── README.md                 本总索引
├── catalog.yaml              自动生成的全局规范目录
├── hazardcast.bib            自动生成的 BibTeX 数据库
├── metadata/<topic>.yaml     13 个主题的原始元数据
└── topics/<topic>.md         13 个主题的原始综述
reference/papers/<topic>/     各主题本地 PDF（Git 忽略）
reference/corrdiff/           已有 CorrDiff 原文（PDF 同样被 Git 忽略）
scripts/build_literature_catalog.py
tests/test_literature_catalog.py
```
