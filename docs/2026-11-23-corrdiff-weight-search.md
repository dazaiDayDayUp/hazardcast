# CorrDiff 修订版权重公开来源穷尽检索

## 目标与结论

路线 2 的目标是找到 **2018–2020 年训练、对应 arXiv v4/正式发表版表 1** 的 CorrDiff 回归与扩散权重，使 2021 年可以作为独立测试集。正式表 1 的关键数值为雷达 MAE 2.54、CRPS 1.90。

截至本次检索，**没有找到满足条件的公开下载**。现有 NGC 第 1 版及 `wwj` 候选权重均属于链接修订前 v3 的同一来源，训练覆盖 2018–2021，不满足要求。

## 论文版本给出的决定性证据

- NGC 模型卡链接 [arXiv v3（2023-12-10）](https://arxiv.org/html/2309.15214v3)，并明确说明训练数据覆盖 2018–2021。
- 2024 年 8 月 6 日的同行评审回复承认，原提交版本的代码错误混入了训练和测试数据；作者随后重新训练回归和扩散模型、采用 2M 回归检查点并修订表 1。
- [arXiv v4（2024-08-11）](https://arxiv.org/html/2309.15214v4)和正式发表版才采用修订后的 205 时刻表 1。
- 已下载并检查 v4 的 LaTeX 源文件，未发现隐藏权重链接；只有 Figshare 动画附件。论文 Code availability 所称训练检查点链接最终仍指向旧 NGC 包。

因此，不能把 NGC 权重当成 v4 权重，也不能把 NGC 的 2021 年高分当成正式表 1 的复现。

## 各渠道的实际检索结果

| 渠道 | 核查内容 | 结果 |
|---|---|---|
| 论文与附件 | arXiv v1–v4、Research Square、补充材料、Peer Review File、v4 LaTeX 源文件 | 有重新训练和修订表 1 的证据，没有 v4 权重下载 |
| NGC | [模型与版本 API](https://api.ngc.nvidia.com/v2/models/nvidia/modulus/corrdiff_inference_package/versions)、模型卡、下载链接 | 只有第 1 版，训练覆盖 2018–2021，链接 v3 |
| Modulus / PhysicsNeMo | 2024 年 7–9 月训练与采样提交、配置、README、Release、issues | 有重构和兼容修复，没有修订版权重或 2M/28M 下载地址；论文具体训练覆盖参数不能从公开配置恢复 |
| Earth2Studio | Taiwan 模型、示例、讨论和加载来源 | 指向同一 NGC 包；其他 CorrDiff 模型属于 HRRR、CMIP6、COSMO 等不同区域 |
| NVIDIA NIM | CorrDiff NIM 文档、容器和讨论 | 是美国 HRRR 产品，不是台湾 v4 权重，也没有公开修订版下载 |
| GitHub 社区 | GitHub API 检索出 50 个 `corrdiff` 仓库并逐个检查 Release 资产；另查 checkpoint/v4/weights 相关 issue | 没有 `.mdlus` 修订版权重；Release 只有坐标等辅助文件。`NVIDIA/physicsnemo#407` 仍是旧版数值 |
| Hugging Face | models/datasets/spaces API 与公开页面；另用公开镜像复核模型 ID | 仅有 `corrdiff-era5-hrrr`、`corrdiff-cmip6-era5`、`corrdiff-cosmo-era5` 和 OneScience 代码实现，无台湾修订版权重 |
| Zenodo | `corrdiff`、论文题名和作者检索 | 只有其他区域、其他任务的 CorrDiff 权重和数据，无 v4 台湾权重 |
| Figshare | 论文附件和 v4 源文件链接 | 只有雷达反射率动画，无权重 |
| OSF / Kaggle / Internet Archive / W&B | 题名、Corrdiff、检查点和 Modulus-Launch 检索 | 未发现公开权重或有效镜像 |
| `wwj` 候选 | 只读检查训练记录并逐点比对张量 | 回归 678/678 张量、扩散共有 678/678 张量与 NGC 完全相同，并非独立训练 |
| CORDEX CorrDiff-TW1 | NTNU/CWA 提交 issue 与讨论 | 是后续独立复现，使用 8M/16M 训练，不是论文 2M/28M 权重；提交的是预测文件而非公开 v4 检查点 |

## 公开证据支持的准确表述

可以说：

> NGC 提供过 CorrDiff 推理检查点，但当前公开包对应修订前 v3，训练覆盖 2018–2021。正式 v4 重新训练后的权重没有在当前公开渠道找到。

不应说：

- NVIDIA 没有发布过任何 CorrDiff 权重；
- NGC 就是正式表 1 权重；
- `wwj` 的候选权重是独立复现；
- 未检索到权重就能证明作者没有保留权重。

论文和同行评审回复表明作者曾明确表示会提供训练检查点，因此更准确的判断是：**公开链接与修订后的发布状态不一致，修订版权重可能存在于作者或 NVIDIA 内部，但未公开可检索。**

## 最现实的获取路径

### 1. 直接向通讯作者索取

联系 Morteza Mardani（论文公开邮箱 `mmardani@nvidia.com`），请求：

1. v4/正式发表版的 `regression.mdlus` 与 `diffusion.mdlus`；
2. 对应的 Hydra 生成配置和随机采样设置；
3. 训练年份与训练数据划分的简短说明；
4. 文件 SHA-256，避免与 v3 包混淆。

还应特别确认扩散模型是否启用回归输出条件（`hr_mean_conditioning`），因为同行评审回复明确说修订时增加了这一条件，不能沿用旧版 `false` 配置而不加核验。

### 2. 通过 NVIDIA 公开支持渠道补充请求

可在 PhysicsNeMo 或 Earth2Studio 新建公开 issue，引用：

- v4 的 205 时刻表 1；
- 同行评审回复中重新训练的说明；
- NGC 第 1 版与 v3 的链接；
- 请求发布修订版权重或给出明确获取方式。

在获得作者答复前，不应通过第三方镜像的同名文件推断其训练年份。

### 3. 保留路线 1 作为主线

若作者不能提供权重，应优先取得 **2022 年及以后的独立 CWA/QPESUMS 数据**，使用现有 NGC 权重开展 CorrDiff+CfC 研究。这样不需要修订版权重，也能保证最终测试对所有模型独立。

## 检索边界

本结论覆盖论文及源文件、NGC、NVIDIA 官方仓库和部署渠道、GitHub 社区仓库与 Release、Hugging Face、Zenodo、Figshare、OSF、Kaggle、Internet Archive、W&B 和本机候选权重。它不排除作者私下提供权重、未来新增公开版本，或企业授权渠道中存在不同权重的可能。
