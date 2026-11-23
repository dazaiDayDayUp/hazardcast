# 公里尺度区域天气时空超分辨：跨主题文献综合与研究路线图

本文面向项目“CorrDiff + 闭式连续时间网络（CfC）+ 物理增强”的研究目标，综合 13 个主题综述及其元数据，重点回答任务边界、模型集成位置、可证伪假设、对照协议和可行研究路线。文中没有新增实验结果；所有“应”“拟”“建议”均表示待检验方案。项目已有 CorrDiff 流程状态另见[项目交接](2026-11-23-status.md)与 [CorrDiff 流程验证](2026-11-23-corrdiff.md)，不与本文的文献判断混写。

## 1. 综合口径与核心判断

13 个主题各有 10 条记录，共 130 条。按 Unicode 规范化、大小写和标点归一后的**题名**合并跨主题重复，得到 **117 篇不同论文，合并 13 条重复记录**；若只按字面 `id` 计数会错误地得到 125 篇，因为同一论文在不同主题中可能使用不同 `id`。`reference/papers/` 下有 **113 个 PDF 文件**，对应去重后有原文的 **105 篇论文**，其余 **12 篇为 `metadata-only`**。CorrDiff 在 `reference/corrdiff/` 的另一份复用文件不计入上述 113 个 PDF。本文引用沿用各主题真实 `id`，不擅自统一原始 YAML。

跨主题后的核心判断不是“扩散、CfC、物理损失可以串联”，而是：

1. **任务仍有明确空位。** CorrDiff（`mardani-2025-corrdiff`）是逐时刻空间降尺度；STVD（`srivastava-2024-video-diffusion`）生成同时间间隔短片而不增加帧率；ModAFNO（`leinonen-2025-modafno`）做时间插值但为确定性模型，且未训练的半点查询失败；spateGAN-ERA5（`glawion-2025-spategan`）最接近公里尺度、次小时联合超分辨，却固定 12 倍空间和 6 倍时间倍率、以降水为主。由**粗空间、稀疏且可能不等间隔的时间输入**生成**细空间、稠密时间的多变量联合条件分布**，仍不是这些工作的共同已完成目标。
2. **CfC 与 CorrDiff 是职责互补，不是天然增益。** CfC（`hasani2022closed-form-cfc`）提供无内部 ODE 求解器的确定性连续时间状态更新；CorrDiff 提供高分辨率残差分布。前者不自动产生集合，后者不自动产生时间动力，二者组合也不自动满足物理方程。
3. **主要科学问题是随机轨迹的一致性。** 把 CfC 只用于条件均值，可能改善中间时刻 RMSE，却仍让独立扩散残差在帧间抖动；真正的增量应检验联合残差轨迹是否改善时间谱、对象传播和轨迹级概率评分，同时不牺牲 CorrDiff 的空间谱、校准与极端表现。
4. **最先值得物理化的是观测/粗化关系，而不是不完整大气 PDE。** 硬约束研究（`geiss-2023-conservation`、`harder-2023-climate-downscaling`）给出了可验证保证，也证明粗化算子错配会把错误精确强加给输出。CWA 的 ERA5→WRF 配对不是天然严格平均可逆关系，必须先审计再选择硬层或软约束。
5. **评价必须拒绝单一总分。** 点误差、边缘概率校准、空间谱、时间谱、对象轨迹、极端事件和物理残差可以相互矛盾。一个好的集合均值、一幅锐利样本或一个下降的 PDE 残差，都不足以验收时空超分辨模型。

## 2. 任务定义与中间时刻输入的场景分类

### 2.1 统一数学定义

设观测到低分辨率多变量场 \(X^L_t\)，实际输入时刻集合为 \(\mathcal T_o=\{t_i\}\)，允许不等间隔和缺测；静态条件为 \(S\)（地形、海陆、坐标等），可用的大尺度或侧边界强迫为 \(B\)。目标是在查询时刻集合 \(\mathcal T_q\) 上重建高分辨率场序列 \(Y^H_{\mathcal T_q}\)。一般模型应表达

\[
p_\theta\!\left(Y^H_{\mathcal T_q}\mid X^L_{\mathcal T_o},B,S,\mathcal T_o,\mathcal T_q,\mathcal M\right),
\]

其中 \(\mathcal M\) 是变量和时刻的缺测掩码。空间倍率由输入/输出网格确定，时间增密由 \(\mathcal T_o\) 与 \(\mathcal T_q\) 确定，不能只用“几倍模型”概括信息条件。

一种可诊断的分解是

\[
\mu_\tau=f_\theta(X^L_{\mathcal T_o},B,S,t,\tau),\qquad
Y^H_\tau=\mathcal U(\mu_\tau)+R_\tau,
\]

其中 CfC 候选负责 \(f_\theta\) 的连续时间条件状态，\(\mathcal U\) 是空间解码，CorrDiff 候选负责残差 \(R\) 的分布。关键区别在于：

- 弱时间生成建模为 \(\prod_{\tau\in\mathcal T_q}p(R_\tau\mid c_\tau)\)，各时刻边缘可以正确，但联合轨迹未必正确；
- 联合时间生成建模为 \(p(R_{\mathcal T_q}\mid c_{\mathcal T_q})\)，才真正把跨时刻随机依赖列为学习目标。

“恢复同一时段”是条件重建，不等于从过去预报未来；“把函数放到更细网格求值”也不等于恢复已丢失的小尺度信息。FNO 的跨离散网格能力（`li2021fno`）和视频网络的时间接口都不能替代上述条件分布目标。

### 2.2 按目标时刻与后续输入是否可用分类

中间时刻的“输入可用”必须进一步说明是**低分辨率场、部分观测，还是高分辨率真值**。训练时可以使用高频真值监督，不代表推理时可以把它们作为条件。

| 场景 | 目标中间时刻的低分辨率输入 | 目标之后的输入 | 正确任务名称 | 与本项目的关系及必要协议 |
| --- | --- | --- | --- | --- |
| S0 同时刻空间降尺度 | 有，且每个目标时刻都有 | 可有可无 | 空间降尺度/模式仿真 | 原版 CorrDiff 的标准场景。可检验空间谱与集合，但不能据此宣称时间超分辨。 |
| S1 因果外推 | 无 | 无，只允许过去 | 临近预报或因果状态重建 | CfC 单向推进；必须与持续性、ConvLSTM/PredRNN 等预报基线比较，不能使用未来端点。`price-2025-gencast`、`ravuri-2021-dgmr` 属生成式预报参照，不是离线插值直接基线。 |
| S2 双边时段内重建 | 无 | 有，至少一个未来粗分辨率端点 | 时间插值/平滑、联合时空超分辨 | **本项目首要研究场景**。用前后粗分辨率端点查询中间时刻；测试集的高分辨率中间真值只评分，不进入编码器。`serifi-2021-spatiotemporal`、`leinonen-2025-modafno`、`glawion-2025-spategan` 提供直接参照。 |
| S3 不规则部分观测补全 | 部分可用，如某些粗场时刻、站点或雷达 | 可有也可无，须预先声明 | 条件补全/资料同化式重建 | 将实际可用观测量、时间戳和 mask 显式输入；完全未观测的中间时刻另行评分。FDM（`harvey-2022-flexible-diffusion`）和 GRU-ODE-Bayes（`debrouwer2019gru-ode-bayes`）支持此类条件设计，但不能与 S2 的“完全无中间输入”混排。 |
| S4 无逐时配对的气候分布生成 | 没有与目标逐时对应的条件 | 不适用 | 分布降尺度、偏差校正或气候状态采样 | `hess-2025-scale-adaptive`、`aich-2026-conditional-diffusion` 的部分任务属于此类；应评价分布和变化信号，不能套用逐时刻重建真值。 |

还有两个容易泄漏信息的变种：

- **高分辨率端点可用**：VIDIM（`jain-2024-vidim`）利用高分辨率首尾帧。若项目只有低分辨率 ERA5 端点，就不能复制其信息条件，也不能把相应结果当直接证据。
- **目标时刻低分辨率场可用但故意忽略**：这仍是 S0 的空间降尺度，不是 S2。若同时研究“多帧辅助当前时刻降尺度”和“未采样时刻重建”，必须建立两个测试清单，分别报告。

### 2.3 可重建性不是固定倍率属性

`fukami-2021-spatiotemporal` 表明时间相关性足够低时重建会失败；`serifi-2021-spatiotemporal` 表明温度适合插值后残差校正，而快速降水可能更适合直接重建；`tatsubori-2022-precipitation` 和 `zhang-2023-nowcastnet` 则说明平流之外还有强度生消。由此应把测试样本按过程分层，而不是只按倍率分层：

1. 平稳平流或缓慢日变化；
2. 快速位移、转向和边界入侵；
3. 对流新生、增强、减弱与消散；
4. 台风、锋面、季风和午后对流等完整过程；
5. 目标到最近输入端点的距离、端点间隔和端点相关性。

大时间间隔下，同一粗输入可以对应多条合理细尺度轨迹。此时模型只能逼近条件分布，不能把某个随机成员与真值的逐格差异全部解释为架构失败，也不能用集合均值低 RMSE 掩盖真实轨迹多样性丢失。

## 3. 统一分类图：方法、数据与证据的对应关系

```text
数据与真值
├─ 同源人工粗化：隔离超分辨先验，已知粗化算子 D
├─ 跨产品配对：ERA5→WRF/CERRA/观测，含模式偏差与配准误差
└─ 非配对分布：自由运行 ESM→观测，只做分布/情景评价
        │
        ▼
信息条件与任务
├─ 同时刻空间降尺度 S0
├─ 过去→未来因果预报 S1
├─ 前后粗场→中间细场 S2（主线）
└─ 不规则部分观测补全 S3
        │
        ▼
确定性条件表示
├─ 空间：插值、CNN/UNet、FNO/AFNO、图网络、静态地形
├─ 时间：时间标量、光流、ConvLSTM/PredRNN、TAU/Earthformer
└─ 连续状态：Neural ODE/CDE、CRU、CfC（真实 Δt + mask + 查询时刻）
        │
        ▼
尺度桥接与条件均值
├─ 先时间后空间 / 先空间后时间 / 联合时空
├─ 直接重建 / 插值残差 / 多尺度潜状态
└─ 像素空间 / 自编码器潜空间（先测重构上限）
        │
        ▼
随机性与生成式集合
├─ 历史 analog、天气发生器、输入扰动
├─ GAN：空间/时间判别器
└─ 扩散：完整场或残差；逐帧边缘或联合轨迹；随机 SDE/确定性 ODE
        │
        ▼
物理增强（逐成员施加并逐成员验收）
├─ 观测一致性：D(Ŷ)≈X，软损失或硬输出层
├─ 状态关系：非负、守恒、多变量排序/平衡
├─ 动力关系：平流、倾向、PDE 残差，训练期或采样期
└─ 混合求解器：可微动力核 + 学习物理（后续高成本分支）
        │
        ▼
证据与决策
├─ 点误差 / 边缘概率 / 联合概率
├─ 空间谱 / 时间谱 / 对象轨迹 / 极端事件
├─ 物理残差 / 独立观测外检 / 分布外泛化
└─ 训练与推理成本 / 集合规模 / 质量—算力 Pareto 前沿
```

这张图强调三条正交轴：**时间状态连续不等于动力正确；生成样本锐利不等于概率校准；满足约束不等于更接近真值。** 因此模型选择必须沿三条轴分别提供证据。

### 13 个主题在分类图中的位置

| 主题文档 | 在统一框架中的用途 |
| --- | --- |
| [动力与经典统计降尺度](../reference/literature/topics/classical-downscaling.md) | PP/MOS、analog、天气发生器、RCM 的概念边界和强经典基线 |
| [确定性深度降尺度](../reference/literature/topics/deterministic-downscaling.md) | 空间骨干、变量差异化重建、确定性—随机残差分工 |
| [扩散降尺度](../reference/literature/topics/diffusion-downscaling.md) | CorrDiff 锚点、直接/残差/潜空间/视频扩散及跨产品差异 |
| [时间超分辨](../reference/literature/topics/temporal-super-resolution.md) | S2 主任务、连续查询陷阱、公里尺度联合超分辨直接文献 |
| [连续时间与 CfC](../reference/literature/topics/continuous-time-cfc.md) | 不规则观测、状态传播、闭式更新、时间随机性与成本 |
| [通用视频预测与插值](../reference/literature/topics/video-prediction-interpolation.md) | 光流/核预测、条件布局、连续坐标、联合视频扩散 |
| [天气时空架构](../reference/literature/topics/spatiotemporal-architectures.md) | 可替换时间核心、空间全局混合、统一骨干公平比较 |
| [生成式天气预报](../reference/literature/topics/weather-generative.md) | 生成式集合轨迹、动力—生成分工和轨迹级概率验收 |
| [高效生成采样](../reference/literature/topics/efficient-generative-sampling.md) | NFE、求解器、潜空间、蒸馏及质量—成本权衡 |
| [物理约束](../reference/literature/topics/physics-constraints.md) | 软/硬/采样期/混合动力约束及算子错配风险 |
| [概率校准](../reference/literature/topics/probabilistic-calibration.md) | 严格适当评分、校准—锐度、边缘后处理与 ECC |
| [频谱、结构、极端评估](../reference/literature/topics/evaluation-spectra-extremes.md) | 多尺度谱、FSS/对象、稀有事件和时空联合诊断 |
| [数据集与基线](../reference/literature/topics/datasets-baselines.md) | ERA5/WRF/CWA 数据含义、防泄漏、真值边界和公平协议 |

## 4. CorrDiff + CfC 的具体集成位置与取舍

以下方案不是名称不同，而是随机性、误差传播和计算发生的位置不同。至少前四种应保留为架构对照；第五种只适合作探索分支。

| 方案 | 具体数据流 | 主要优点 | 主要缺点与失败模式 | 建议角色 |
| --- | --- | --- | --- | --- |
| I. 时间→空间串行 | 粗分辨率序列→CfC 在粗网格或低维潜空间补全中间状态→逐时刻 CorrDiff | 最容易复用现有 CorrDiff；CfC 状态维度低；能单独测时间插值误差；适合先做不规则时间消融 | 第一阶段误差传入第二阶段；若 CorrDiff 每帧独立采样，残差会抖动；粗网格 CfC 看不到未解析小尺度，可能把强对流生消过度平滑 | **低成本首版和下界**，但不能单独作为联合时间生成证据 |
| II. 空间→时间串行 | 输入端点先经 CorrDiff 得到高分辨率端点/序列→CfC 或连续解码器在高分辨率潜空间插值 | 时间模块可利用端点细结构；空间和时间误差可分阶段诊断；适合检验“先空间是否更利于对流细节” | 高分辨率状态成本高；若端点独立生成，CfC 会继承不一致细节；确定性时间插值可能重新平均随机成员；自编码器会引入额外重建损失 | **顺序对照**，不宜在没有潜空间重构上界时直接扩展 |
| III. CfC 条件均值 + 逐帧残差扩散（弱耦合） | 共享空间编码器→CfC 输出每个目标时刻的多尺度条件 \(c_\tau\) 和均值 \(\mu_\tau\)→共享 CorrDiff 去噪器逐时刻生成 \(R_\tau\) | 保留 CorrDiff 的均值/残差分工；能分别评估 CfC-only、均值和集合；计算与显存可控；易于加入物理输出层 | 条件状态连续但残差噪声独立；每个时刻空间谱都可能正确，对象仍可能闪烁或跳变；集合离散度可能只来自空间噪声 | **主消融锚点**：回答“时间化均值是否足够” |
| IV. CfC 条件均值 + 联合残差序列扩散（联合耦合） | CfC 产生整段 \(c_{\mathcal T_q}\)→带时间注意力/3D 卷积或跨时刻噪声耦合的 CorrDiff 去噪器联合生成 \(R_{\mathcal T_q}\) | 直接逼近轨迹联合分布；可学习随机雨团的持续、传播和生消；最能检验 CorrDiff+CfC 的独立科学价值 | 输出长度使显存、NFE 总成本和调参难度上升；短片边界、长窗口拼接与集合校准更复杂；容易把增益与更大骨干混淆 | **核心研究候选**，先用短片段、patch 或潜空间验证，并与 III 同预算比较 |
| V. 物理时间与扩散噪声时间共同进入 CfC | 每个去噪步都更新 CfC，或将扩散步参数化为动力推进，参照 DYffusion（`cachay-2023-dyffusion`） | 时间动力与生成过程可深度耦合；有机会摊销部分轨迹采样 | 两种时间语义易混淆；每个 NFE 都付出时序成本；训练和采样难以归因，可能复制数值不稳定 | **后续探索**，不作为首个可复现版本 |

方案 I/II 是“分解顺序”，III/IV 是“概率分解方式”，V 是“时间轴耦合”，不应混成一张只有最终 RMSE 的排名。另有两条与上述位置正交的工程轴：

- **潜空间化**：`tomasi-2025-latent-diffusion` 和 `rombach-2022-latent-diffusion` 支持降低去噪成本，但必须先报告真值编码—解码后的 RMSE、极端分位和谱尾，避免把 VAE 信息瓶颈误算到 CfC 或扩散器。
- **少步采样**：EDM（`karras-2022-edm`）、DPM-Solver（`lu-2022-dpm-solver`）和 consistency model（`song-2023-consistency-models`）减少的是生成计算，不保证天气物理一致或集合多样。固定模型扫描 NFE 应早于蒸馏。

推荐主线是 **III 建立可归因基线，IV 检验真正的研究增量，I/II 判断串行顺序是否已足够**。CfC 默认只沿天气物理时间传播；扩散噪声时间继续由 EDM 的 \(\sigma\) 表示。除非有专门假设，不应让 CfC 消费自己刚生成的高分辨率随机场做长程自回归，以免把条件编码、残差采样和滚动漂移混在一起。

## 5. 可证伪研究假设

| 假设 | 明确预测 | 否证或降格条件 | 必须控制的混淆因素 |
| --- | --- | --- | --- |
| H1：真实时间间隔驱动的 CfC 改善不规则和未见过查询时刻的条件表示 | 在相同空间编解码器和训练预算下，CfC 相对时间标量 UNet、ConvGRU 和 SimVP 类时间核心，在未见非整数相对时刻、未见端点间隔和随机缺测上降低中间时刻误差及时间差分误差 | 只改善训练内整点，或在未见查询位置与 ConvGRU/简单时间条件相当；加入实际 \(\Delta t\) 后无增益 | 输入帧数、未来信息、参数量、训练步数、静态条件、mask 分布；不能仅替换骨干后比较一个总分 |
| H2：均值/残差分解分别改善点预测和分布重建 | CfC-UNet 在部分 MAE/RMSE 上更强；加入扩散后在 fair CRPS、单成员谱尾和极端覆盖上更强；两者不一定在同一指标上获胜 | 扩散只增加高频噪声而未改善 CRPS/极端，或 CfC-only 已在所有联合概率与谱指标上不差于生成模型 | 集合均值、单成员和整个集合分开评分；固定成员数与采样预算 |
| H3：联合残差建模是时间随机一致性的主要来源，而非 CfC 条件本身 | IV 相对 III 改善时间谱、对象轨迹、energy/variogram 类联合评分和事件持续期，同时空间谱、CRPS 与极端不退化 | III 已达到相同联合指标，或 IV 的收益只体现为更高单帧指标；收益不足以抵消成本时，应把 IV 降为高成本上界 | 相同 CfC 条件、去噪骨干容量、输出窗口、训练样本、NFE 和集合成员；配对使用相同初始噪声 |
| H4：只有粗化算子正确时，硬观测一致性才是可靠物理增强 | 算子匹配时，硬层将近似消除 \(\|D(\hat Y)-X\|\)，并保持或改善技巧；算子错配时，硬层会比软约束更容易损失 RMSE、谱或极端 | 算子匹配仍显著损害分布质量，或硬层只让残差归零却放大校正幅度和天气误差 | 先在原始 LR/HR 配对上测量约束违反；比较平均、面积加权及真实产品关系；对每个集合成员施加 |
| H5：边缘后处理与联合生成解决不同瓶颈 | BMA/EMOS、分位数校准或 ECC 能改善边缘覆盖和 CRPS，但不能修复原集合没有的传播速度、生命史或多变量动力结构 | 廉价后处理在全部联合指标上也达到联合生成器水平，则复杂轨迹模型的必要性下降 | 校准器仅用训练/验证期拟合；固定测试期；ECC 的秩模板、成员数和边缘分布保持一致 |

这些假设把可能形成论文的主张变成可以被实验推翻的命题，避免“融合模型效果更好”这种不可证伪表述。

## 6. 基线与消融矩阵

### 6.1 核心对照

| 编号 | 模型/基线 | 时间信息 | 随机残差 | 回答的问题 | 优先级 |
| --- | --- | --- | --- | --- | --- |
| B0 | 气候态、最近时刻、空间双线性/双三次 + 时间线性 | 无学习或线性 | 无 | 网格加密和简单重采样已经做到什么 | P0 |
| B1 | MOS/GLM 或随机森林；资源允许时加入多变量 analog | 同期或显式时间差 | analog 可采样 | 是否真正超过可解释经典方法，而非只超过弱插值 | P0/P1 |
| B2 | 单帧 UNet / CorrDiff 回归阶段 | 仅 S0 可直接使用当前粗场；S2 无当前粗场，不直接适用 | 无 | S0 空间确定映射的下限 | P0 |
| B3 | 时间条件 UNet、ConvGRU 或 SimVP 时间核心 | 与 CfC 完全相同 | 无 | CfC 的收益是否只是多帧上下文或空间骨干 | P0 |
| B4 | CfC-UNet，无扩散 | 实际 \(\Delta t\)、mask、目标时刻 | 无 | 时间状态本身的贡献与平滑程度 | P0 |
| B5 | 原版逐时刻 CorrDiff | S0 单时刻空间锚点；S2 不直接适用，须由时间插值或 CfC 提供目标条件 | 独立空间残差 | 空间生成锚点及谱/校准基线 | P0 |
| B6 | 时间线性插值→UNet | 两端线性 | 无 | S2 确定性时间→空间串行下限，以及 CfC 是否超过简单时间插值 | P0 |
| B7 | CorrDiff→连续时间插值，即方案 II | 高分辨率潜状态 | 取决于插值器 | 分解顺序是否决定结果 | P1 |
| B8 | CfC 条件均值 + 逐帧 CorrDiff，方案 III | CfC | 独立逐帧 | 时间化均值与空间随机残差是否足够 | P0 |
| B9 | 无 CfC 的时空视频扩散/STVD 类模型 | 离散时间注意力 | 联合 | 增益来自 CfC 还是一般联合时间建模 | P1 |
| B10 | CfC + 联合残差 CorrDiff，方案 IV | CfC | 联合 | 核心完整模型 | P1 |
| B11 | 最佳生成模型 + EMOS/BMA/分位数校准 + ECC-Q | 继承原模型 | 重排/校准 | 廉价后处理能获得多少，联合结构瓶颈是否仍存在 | P1 |

强外部架构参照可包括 STVD（`srivastava-2024-video-diffusion`）、spateGAN（`glawion-2025-spategan`）或 Defez（`defez-2026-scale-adaptive`），但应在同一数据、输入信息和成员数下重训/实现；不能引用其他数据集数字作为直接排名。完整矩阵不必一次全部训练，P0 先形成判别链，P1 只保留能回答剩余问题的对照。

### 6.2 单因素消融顺序

1. **信息条件**：S0/S1/S2 分开；双向与单向分开；输入上下文长度和未来端点数量分开。任何方法不得独享更多未来帧或地形通道。
2. **连续时间机制**：CfC 原始单元、noGate、mmRNN；真实小时 \(\Delta t\) 对帧序号；固定间隔训练对可变间隔训练；整点查询对训练未见查询位置。
3. **随机耦合**：独立逐帧噪声、共享部分时间潜噪声、联合残差去噪。比较“同一时间轨迹、不同空间噪声”与“不同时间轨迹、不同空间噪声”，区分离散度来源。
4. **空间与静态条件**：地形、海陆、坐标、大尺度风/湿/压预测因子逐项移除；卷积与一种全局空间混合器替换，不同时更换所有骨干。
5. **物理**：无约束、粗化软约束、粗化硬层、动力软残差；之后再加采样期校正或 PIDM 式训练（`jacobsen-2025-cocogen`、`bastek-2025-physics-diffusion`）。软约束权重跨数量级扫描，并报告数据项与物理项量纲和相对量级。
6. **效率**：固定 checkpoint 扫描 NFE；像素空间对潜空间；必要时再做蒸馏。每一项都报告完整窗口、固定集合规模的总成本，而不只报单帧 FLOPs。

关键模型应使用多个训练种子；采样比较使用相同测试样本和共同随机数。超参数选择只看开发验证集，最终测试集不参与早停、约束权重或 NFE 选择。

## 7. 数据构造、划分与防泄漏

### 7.1 两条数据轨必须分开解释

**受控自粗化轨**：从高分辨率序列用明确算子 \(D\) 构造低分辨率输入，再按时间抽稀。优点是配对严格、可隔离缺失谱恢复和硬约束效果；缺点是它不包含真实跨产品偏差。STVD、PhIRE 和部分 Harder 实验说明该轨不能替代部署场景。

**真实跨产品轨**：使用 ERA5→CWA/WRF 配对，包含尺度、动力核心、物理参数化、区域资料同化和配准差异。`chen-2020-radar-assimilation` 表明台湾高分辨率目标受到雷达和地面观测同化影响，因此 WRF 输出应称为区域模式/分析代理，而不是无误差真值。独立 QPESUMS、雷达和站点外检应与对 WRF 的评分分开陈述。

当前逐小时数据可支持例如 3 小时或 6 小时输入到逐小时输出的训练与测试；**不能仅凭逐小时标签声称验证 10 分钟重建**。若目标是 2 km/10 min，必须增加具有相应时间分辨率和质量控制的监督数据，或明确把次小时结果限定为无逐时刻真值的生成展示。

### 7.2 切分规则

1. **复现轨与开发轨隔离**：保留 CorrDiff 的 2018–2020 训练和 2021 固定 205 时刻作为空间复现口径。新时空模型在 2018–2020 内按连续时间块划训练/验证；2021 在模型、归一化、物理权重、校准器和 NFE 全部冻结后才用于最终测试。
2. **按完整天气过程分组**：以时间连续性、风暴路径或客观事件标记构成 group；同一台风、锋面或对流过程不得跨训练与测试。2021 应尽可能保留连续片段，而不是只在既有 205 个时刻上评价时间谱和生命史。
3. **重叠窗口不得越界**：设输入向左/向右上下文为 \(L_-\)、\(L_+\)，输出覆盖为 \(H\)，切分边界隔离带至少覆盖所有可能窗口的支撑范围 \(L_- + H + L_+\)。空间 patch 可以重叠用于训练，但同一目标天气过程仍须属于同一集合。
4. **所有拟合对象只见过训练集**：归一化、气候态、分位数映射、PCA/VAE、analog 检索库、物理损失权重、早停、BMA/EMOS 和 ECC 都遵守同一切分。滚动校准只能使用当时可获得的数据。
5. **时间监督与推理输入分离**：训练可保留完整高分辨率中间帧作为标签；验证/测试生成前先真正移除相应低分辨率输入。记录每个样本实际输入时刻，防止数据加载器默认把完整序列传给编码器。
6. **空间和变量审计**：可选完全不相交子域测试；所有样本保存 UTC、产品版本、累积时段、网格投影、面积权重、缺测与雷达质量控制。瞬时场和累积量不能错位，雷达反射率与观测降水不能混称。
7. **独立极端而非更多相邻时刻**：显著性和置信区间按日期或事件 block bootstrap；相邻帧、邻近像元和集合成员不视为独立重复。极端样本不足时只报告经验高分位，不外推高重现期结论。

## 8. 评估协议：物理、概率、频谱与极端的联合验收

### 8.1 指标矩阵

| 评估轴 | 最小指标组合 | 必须公开的定义与防误读措施 |
| --- | --- | --- |
| 点预测 | 分变量 MAE、RMSE、偏差；已知端点与未输入中间点分开；集合均值/中位数与单成员分开 | 反标准化后的物理单位、面积权重、目标到最近端点距离、天气型和地形分层 |
| 边缘概率 | fair CRPS/CRPSS、rank histogram 或 PIT、区间覆盖率与宽度、spread–error 比值及个例相关、阈值 Brier/可靠性 | CRPS 第二项采用 \(M(M-1)\) 公平估计或明确所用公式；固定 \(M\)；零降水并列秩规则；按区域/季节/天气型分层。依据 `gneiting-2007-scoring-rules`、`hamill-2001-rank-histogram` |
| 联合概率 | energy score、标准化 variogram 类评分、多变量/多时刻 rank；空间—时间—变量联合超阈覆盖 | energy score 对依赖结构不总是敏感，variogram 类评分会抵消共同偏差且并非都严格适当；必须与单变量偏差、谱和对象指标互补，参照 `scheuerer-2015-variogram` |
| 空间频谱与尺度 | 逐成员 2D 功率谱、RAPSD、带符号谱比、谱距离、结构函数/间歇性；粗尺度聚合一致性 | 集合均值不得替代原始成员；公开窗函数、径向分箱和边界处理；径向谱之外抽查方向性；网格距不等于有效分辨率，参照 `harris-2001-multiscale` |
| 时间频谱与轨迹 | 地点/区域时间谱，条件允许时波数—频率谱；滞后自相关、时间差分分布；对象质心速度、方向、寿命、生灭与峰值时刻 | 只用未输入时刻计算；区分短片拼接和真正长轨迹；采样间隔必须能支撑所声称的时间尺度 |
| 空间技巧与对象 | 多阈值、多邻域 FSS；集合 pFSS；SAL 或 MODE 式面积、质心、方向、纵横比、强度与对象匹配 | 邻域用 km，公开阈值、最小面积和匹配规则；FSS、SAL、对象指标不可互相替代，参照 `roberts-2008-fss`、`wernli-2008-sal`、`necker-2024-ensemble` |
| 极端事件 | 发生：EDI/SEDI、POD/FAR；量级：P99/P99.9 与峰值偏差；影响：超阈面积、对象数、台风最大风半径；持续性：持续时间和经验重现水平（样本足够时） | `ferro-2011-extremal` 的 EDI/SEDI 只评价二值判别，不评价峰值或集合校准；按事件去簇和 bootstrap，不能用像元数制造显著性 |
| 物理一致性 | 每成员 \(\|D(\hat Y)-X\|\)、非负违反率、适用质量/水量收支、散度/涡度/平流或离散 PDE 残差、多变量共置 | 全部在物理单位和一致差分格式下计算；硬约束同时报告校正幅度；集合均值守恒不代表成员守恒；雷达反射率不是守恒量 |
| 外部真实性与稳健性 | 独立雷达/QPESUMS/站点；未见年份、区域、间隔、天气型、倍率；失败个例 | 对 WRF 的低误差只证明代理仿真；分布外测试与训练内随机 mask 分开报告 |
| 效率 | 训练 GPU 小时、峰值显存、整段单成员和固定集合延迟/吞吐、NFE、编解码与物理算子调用 | 相同硬件、精度、批量、输出窗口和成员数；发布质量—延迟—显存 Pareto 曲线，而非只比参数量 |

### 8.2 验收逻辑

- **CfC 有效**：至少在未见时间位置或不规则输入上改善时间指标，且空间谱、CRPS 和极端没有显著退化。只有 RMSE 改善时，应称为回归/平滑收益，而不是完整时空生成进步。
- **联合扩散有效**：相对逐帧残差，在时间谱、对象轨迹或联合评分上有独立收益，并通过相同边缘校准对照排除“只是方差变大”。
- **物理增强有效**：目标物理量改善之外，还需天气技巧和概率质量不退化。若出现“物理残差降、CRPS 升”“守恒满足、极端变差”等组合，应作为失败机理报告。
- **高效采样有效**：在同等质量约束下减少完整窗口集合成本；若少步采样使 spread、谱尾或极端覆盖下降，不能只用单样本视觉质量宣称加速成功。

## 9. 算力可行的分阶段路线

总推理成本近似为

\[
C \sim M\times \mathrm{NFE}\times T\times C_{\text{denoiser}}
 + C_{\text{CfC/encoder}}+C_{\text{physics}}+C_{\text{decode}},
\]

其中 \(M\) 是集合成员数，\(T\) 是目标时刻数。CfC 省去内部 ODE 求解不等于整个系统便宜；若每个去噪步都运行完整时空 CfC，它仍会被 NFE 放大。由于没有为本路线图测定具体硬件吞吐，以下只给相对成本和阶段门槛，不虚构 GPU 小时。

| 阶段 | 范围 | 计算控制 | 进入下一阶段的证据门槛 |
| --- | --- | --- | --- |
| P0 数据与评分器 | 审计时间对齐、粗化算子、事件分组；实现 fair CRPS、谱、FSS、时间差分、物理诊断 | 不训练大模型；用小数组/合成集合验证评分公式和并列秩 | 能复现一致基线评分，输入时刻清单证明无中间帧泄漏，给出数据有效时间覆盖 |
| P1 确定性时间核心 | 小区域或 patch；S0 使用 B0–B4；S2 使用 B0、B1、B3、B4 和 B6（时间线性插值→UNet），不把 B2 当作无当前粗场的直接基线；3/6 h→1 h；固定与可变间隔、未见查询位置 | 共用编码器/解码器；限制窗口和模型宽度；先只训练 CfC、ConvGRU/SimVP 和时间标量对照 | 判断 H1 是否成立；若 CfC 无独立收益，先修数据/时间机制，不急于扩大扩散模型 |
| P2 弱耦合生成 | S0 的 B5；S2 的 B6（确定性参照）与 B8，并由时间线性插值为 B5 提供目标条件；CfC 均值冻结或分阶段训练，复用共享 CorrDiff 去噪器 | 短片段、逐帧采样、混合精度；固定成员数；先扫描少量 NFE 形成质量—成本曲线 | 相对插值和 CfC-only，空间谱、fair CRPS、极端有实际增益；记录逐帧时间失败 |
| P3 联合残差短片 | B9/B10，检验 H3 | 先短窗口和 patch；时间注意力只用于必要层；梯度检查点；必要时才引入已经通过重构测试的潜空间 | 联合指标显著优于 III，且空间/概率不退化；若成本过大，保留为短窗口上界而非强行全区域铺开 |
| P4 物理与校准 | 粗化软/硬约束、一个明确动力项、EMOS/BMA+ECC；外部观测和极端留出 | 每次只加一种约束；物理算子调用预算固定；校准后处理成本低可先做 | 通过“物理 + 技巧 + 概率”三重验收；错误算子或过强约束能被对照识别 |
| P5 扩展与摊销 | 更长轨迹、更大区域、潜空间/少步蒸馏、多区域迁移 | 只在实测瓶颈出现后引入；教师先通过天气指标筛选；比较训练摊销回收点 | 质量—成本 Pareto 改善且没有将 VAE、少步求解或长窗口拼接误差隐藏起来 |

首轮不应同时引入全局基础模型、完整可微 GCM、长视频联合扩散和多类 PDE 损失。`kochkov-2024-neuralgcm`、`brenowitz-2025-cbottle` 和 `bodnar-2025-aurora` 展示的是高成本扩展方向，不是本地首版必须复现的最低配置。可先把**低分辨率 CfC 状态 + 可复用空间生成器 + 短窗口联合残差的关键对照**作为待验证的低成本起点；其质量—算力权衡是否值得采用，必须由目标硬件上的完整窗口与固定集合实测决定。

## 10. 主要研究空白与可形成论文贡献的方向

| 研究空白 | 文献证据的边界 | 可形成的贡献 | 最低可信证据包 |
| --- | --- | --- | --- |
| G1 连续不规则时间与公里尺度联合概率重建尚未闭合 | ModAFNO 的半点失败；STVD 不增密；spateGAN 固定倍率；Defez 主要倍率分别训练，仅对邻近目标提供插值到已学习分辨率后的复用例外，且采样昂贵；CfC 原论文没有公里尺度天气生成实验 | **时间间隔感知的双向 CfC 条件轨迹 + CorrDiff 残差生成**，支持不等间隔输入和未见目标时刻 | 同骨干离散时间对照；固定/可变间隔；未见非整数时刻；完整事件留出；逐帧与联合残差消融 |
| G2 单帧空间集合缺少随机时间 copula | CorrDiff 欠离散且逐帧独立；Schmidt（`schmidt-2025-coherent-diffusion`）显示联合轨迹可行但成本高；TAUDiff 表明均值与端到端扩散可分别低估/高估时间高频 | **低成本条件状态与联合随机残差的分层建模**，明确哪些不确定性来自时间轨迹、哪些来自空间细节 | 相同边缘分布下的联合指标、时间谱、对象生命史、energy/variogram 类评分；与 ECC 和独立重采样比较 |
| G3 物理约束常忽略真实产品的粗化错配和不完备方程 | Geiss 证明错误粗化核会伤害结果；Harder 的真实 WRF 关系只近似成立；PhyDL-NWP 的潜在力可吸收残差且时间降尺度证据不足 | **算子审计驱动的软/硬约束组合**，逐成员保证可定义的观测一致性，同时保留未解析过程残差 | 原始配对约束审计；匹配/错配 \(D\)；软/硬/无约束；校正幅度；物理、CRPS、谱和极端共同报告 |
| G4 边缘校准、联合结构与极端风险常被混为“不确定性良好” | 平坦 rank 可由偏差抵消；CRPS 是边缘评分；ECC 只能继承原 copula；CorrDiff 与 spateGAN 均有欠离散报告 | **面向时空轨迹的分层概率评估与后处理基准**，区分边缘、依赖结构和尾部风险 | 条件分层 rank/PIT、覆盖—宽度、fair CRPS、pFSS、联合评分、对象轨迹和极端四层证据；事件 bootstrap |
| G5 现有强模型缺少可归因的质量—算力证据 | STVD/Schmidt/VIDIM 联合生成昂贵；LDM 有重构瓶颈；少步求解可能损伤集合多样性 | **CfC 低维时间状态 + 轻量残差校正的质量—成本 Pareto 方法** | 同 checkpoint NFE 扫描、逐帧/联合/潜空间分解、固定整段集合成本、极端与谱尾随成本变化 |
| G6 公里尺度“真值”常是另一个模式产品 | CWA/WRF 含区域资料同化，ERA5 与 WRF 均非独立完美观测；RainShift 显示地域差异可大于架构差异 | **区域模式仿真与独立观测真实性分离的评估协议**，可作为方法论文的稳健性部分或数据论文基础 | 固定清单与版本、完整事件切分、跨子域/年份测试、WRF 与 QPESUMS/雷达/站点双轨评分、观测质量控制 |

最有凝聚力的论文主线是 G1+G2：不是宣称“CfC 比所有网络好”，而是证明**连续时间条件化与联合残差分布分别解决哪一类误差**。G3 可形成第二条物理增强论文线，但应建立在主线对照稳定之后。G4/G6 是使前两条可信的必要方法学支撑，也可能在数据和代码可发布时形成独立基准贡献。G5 更适合成为主文的效率章节，除非产生新的采样或压缩算法，否则不宜单独包装成方法创新。

## 11. 优先阅读清单

以下顺序按“先锁定任务，再读核心集成，最后补物理与评估”排列；标题保留原文，链接进入相应本地主题综述。

| 顺序 | 条目与原题 | 精读目的 |
| ---: | --- | --- |
| 1 | `mardani-2025-corrdiff`，*Residual corrective diffusion modeling for km-scale atmospheric downscaling*（[扩散降尺度](../reference/literature/topics/diffusion-downscaling.md)） | 固定 ERA5→CWA/WRF、均值/残差、205 时刻和集合欠离散等项目锚点 |
| 2 | `hasani2022closed-form-cfc`，*Closed-form continuous-time neural networks*（[连续时间与 CfC](../reference/literature/topics/continuous-time-cfc.md)） | 理解显式时间门控、闭式近似、mixed-memory 和“无需求解器”的真实含义 |
| 3 | `glawion-2025-spategan`，*Global spatio-temporal ERA5 precipitation downscaling to km and sub-hourly scale using generative AI*（[时间超分辨](../reference/literature/topics/temporal-super-resolution.md)） | 建立公里尺度、10 分钟联合超分辨的直接强参照和时空谱评估目标 |
| 4 | `srivastava-2024-video-diffusion`，*Precipitation Downscaling with Spatiotemporal Video Diffusion*（[扩散降尺度](../reference/literature/topics/diffusion-downscaling.md)） | 学习时间条件残差视频扩散，同时牢记输入输出时间间隔相同 |
| 5 | `defez-2026-scale-adaptive`，*A Scale-Adaptive Framework for Joint Spatiotemporal Super-Resolution with Diffusion Models*（[时间超分辨](../reference/literature/topics/temporal-super-resolution.md)） | 对照确定性均值、扩散集合、守恒与倍率适配；注意主要倍率分别训练、邻近目标插值复用例外和预印本边界 |
| 6 | `leinonen-2025-modafno`，*Modulated Adaptive Fourier Neural Operators for Temporal Interpolation of Weather Forecasts*（[时间超分辨](../reference/literature/topics/temporal-super-resolution.md)） | 设计目标时间条件及未见半点查询的反例测试 |
| 7 | `schmidt-2025-coherent-diffusion`，*A Generative Framework for Probabilistic, Spatiotemporally Coherent Downscaling of Climate Simulation*（[时间超分辨](../reference/literature/topics/temporal-super-resolution.md)） | 理解整条多变量轨迹先验、观测算子条件化及其显存代价 |
| 8 | `sundar-2024-taudiff` / `sundar-2025-taudiff`，*TAUDiff: Highly efficient kilometer-scale downscaling using generative diffusion models*（[频谱与极端评估](../reference/literature/topics/evaluation-spectra-extremes.md)） | 阅读时序均值 + 轻量扩散、时间谱和风场物理损失；两个 id 是跨主题版本记录 |
| 9 | `harder-2023-climate-downscaling`，*Hard-Constrained Deep Learning for Climate Downscaling*（[物理约束](../reference/literature/topics/physics-constraints.md)） | 直接对应时空超分辨硬约束、变量差异及错误约束反例 |
| 10 | `geiss-2023-conservation`，*Strictly Enforcing Invertibility and Conservation in CNN-Based Super Resolution for Scientific Datasets*（[物理约束](../reference/literature/topics/physics-constraints.md)） | 推导可实现的粗化一致性输出层并设计算子错配实验 |
| 11 | `karras-2022-edm`，*Elucidating the Design Space of Diffusion-Based Generative Models*（[高效生成采样](../reference/literature/topics/efficient-generative-sampling.md)） | 固定 CorrDiff 的噪声、预条件与采样语言，再做少步和 CfC 消融 |
| 12 | `price-2025-gencast`，*Probabilistic weather forecasting with machine learning*（[概率校准](../reference/literature/topics/probabilistic-calibration.md)） | 建立联合天气轨迹、集合 CRPS、rank、spread 和极端的完整验收视角 |
| 13 | `harris-2022-downscaling`，*A Generative Deep Learning Approach to Stochastic Downscaling of Precipitation Forecasts*（[频谱与极端评估](../reference/literature/topics/evaluation-spectra-extremes.md)） | 连接生成式降水、RAPSD/RALSD、集合和强降水分层 |
| 14 | `roberts-2008-fss`，*Scale-Selective Verification of Rainfall Accumulations from High-Resolution Forecasts of Convective Events*（[频谱与极端评估](../reference/literature/topics/evaluation-spectra-extremes.md)） | 实现多阈值、多邻域 FSS，避免逐格双重惩罚主导结论 |
| 15 | `harvey-2022-flexible-diffusion`，*Flexible Diffusion Modeling of Long Videos*（[通用视频预测与插值](../reference/literature/topics/video-prediction-interpolation.md)） | 设计随机观测布局、mask 和采样日程，区分离散灵活条件与连续时间 |
| 16 | `chen-2022-videoinr`，*VideoINR: Learning Video Implicit Neural Representation for Continuous Space-Time Super-Resolution*（[通用视频预测与插值](../reference/literature/topics/video-prediction-interpolation.md)） | 对照连续坐标接口和未见倍率泛化，防止把接口能力当作已验证动力 |
| 17 | `maraun-2010-precipitation`，*Precipitation downscaling under climate change: Recent developments to bridge the gap between dynamical models and the end user*（[经典降尺度](../reference/literature/topics/classical-downscaling.md)） | 回到多尺度、极端、物理一致性和终端需求的完整问题定义 |
| 18 | `chen-2020-radar-assimilation`，*Improving Afternoon Thunderstorm Prediction over Taiwan through 3DVar-Based Radar and Surface Data Assimilation*（[数据集与基线](../reference/literature/topics/datasets-baselines.md)） | 理解 CWA/WRF 目标的观测同化来源及“代理真值”边界；当前仅有元数据 |

## 12. 证据边界与待解决项

1. 本综合覆盖项目选定的 117 篇不同论文，不是穷尽式系统综述；近期条目中 `defez-2026-scale-adaptive`、`brenowitz-2025-cbottle`、`harder-2025-rainshift` 等仍有预印本属性，不能因“最新”而预设优于同行评议工作。
2. 12 篇 `metadata-only` 条目只支持题录和主题综述中已核验的摘要级判断，不应用于声称已核对全文细节。尤其是 `chen-2020-radar-assimilation`、`hersbach-2020-era5`、`powers-2017-wrf` 等背景来源，后续若需精确实现数据配置仍需取得权威全文或数据手册。
3. CWA 当前逐小时标签不足以验证真实次小时动力；目标数据的时间累积定义、雷达反射率来源和质量控制仍需在实验前冻结。
4. ERA5 与 CWA/WRF 之间是否存在可精确写入架构的粗化算子尚未确定。应先测量，不应默认 \(D(Y^H)=X^L\) 严格成立。
5. 现有变量是否足以定义可信水汽、质量、能量或动量收支尚未确定。缺少垂直运动、湿度通量、边界通量或次网格项时，应降低动力残差主张，不能靠高容量潜在力制造“物理改善”。
6. 2021 年极端过程数量、连续片段可用性和独立观测覆盖仍需审计；不足时不应报告高重现期或普适台风结论。
7. 方案 III/IV 的实际显存、吞吐和最适窗口长度没有文献可直接给出，必须在目标硬件上以短窗口 profiling 决定，本文不预设训练成本或性能提升。
