# LingBot-VLA 2.0 × RoboTwin 参赛记录（蚂蚁灵波具身大模型挑战赛·初赛）

天池「蚂蚁灵波具身大模型挑战赛」初赛参赛记录：使用官方基座 `robbyant/lingbot-vla-v2-6b`，仅在 RoboTwin 2.0 Aloha-AgileX 50 任务的 **clean 演示数据**（50 任务 × 50 条，共 2,500 条 / 549,787 帧）上做行为克隆后训练，在 RoboTwin 仿真环境中闭环评测。

本仓库整理了**关键过程与步骤**：基线复现、一个影响 21 分的评测 bug 的定位与修复、训练配方、评测管线、候选权重对比，以及最终提交的测试结果。过程性/内部运维文档、官方代码副本与有版权的 PDF 资料未收录（见文末链接）。

## 最终提交

| 项目 | 内容 |
|---|---|
| 权重 | `anon-m-7k3qx`（HF bf16，3 个 safetensors 分片，约 12.8GB，ModelScope 仓库 `oasmet/anon-m-7k3qx`） |
| 训练 | 50 任务联合训练（cotrain），仅 clean 演示 + seen 指令池；单一权重，不按任务路由，无集成、无多 seed 投票 |
| clean 结果 | 40/50 个任务有结果，136 回合成功 56（41.2%）；8 个面板任务每任务 5 次，其余每任务 3 次 |
| randomized 结果 | 部分任务（见 [results/](results/) 中的 JSON） |
| 结果文件 | [results/results_anon-m-7k3qx.json](results/results_anon-m-7k3qx.json)、[results/README.md](results/README.md) |

> 如实说明：受共用服务器显存/磁盘限制，**没有完成官方要求的每任务每设定 100 次**，未测任务标 `not_run` 不计成功。最终以官方复测成绩为准。

## 关键过程

### 1. 基线复现与一个价值 21.4 分的 bug（56.6% → 77.96%）

官方基座在 50 任务 × 50 回合全量评测中得 **56.6%**，远低于官方宣称的 93.52%。逐层排查后定位到**评测指令生成失败**：`expert_check=false` 时 `episode_info` 被硬编码为空，导致 96% 的回合把任务名字符串（如 `"adjust_bottle"`）直接当语言指令下发。

- 症状吻合：指令无关任务（shake_bottle 等）照常 100%，吃指令语义的任务（按颜色/尺寸排序、堆叠系列）塌方到 0–18%；
- 排除法：`use_length` 25 vs 50、compile 开关对照轮 56.4% ≈ 56.6%，与差距无关；
- 修复：干跑（dry-run）patch——把 7 个执行原语 stub 成 no-op 后跑 `play_once()`，只渲染指令模板不执行轨迹（ROCm 环境装不了 CuRobo，无法走 `expert_check=true` 正路）；
- 结果：**56.60% → 77.96%（1949/2500，+21.4 分）**，7 任务满分，0% 任务清零。

完整因果链与证据：[docs/FROM-56-TO-80.md](docs/FROM-56-TO-80.md)、逐任务对比 [docs/dryrun-vs-run2-comparison.md](docs/dryrun-vs-run2-comparison.md)、基线明细 [docs/clean50x50-result.md](docs/clean50x50-result.md)。

### 2. 训练配方与候选权重对比

起点只能是 `lingbot-vla-v2-6b` 基座（规则红线：禁用 randomized / 外部 / rollout 数据，禁用 unseen 指令，单一权重）。两条训练路线：

- **全参数微调**（最终提交路线）：有效批量 128（micro 64 × 累积 2），AdamW，5000 步后学习率固定 1e-6；
- **仅动作专家**（约 1.8B 参数，主干冻结）：批量 8，共 16,500 步——全参放不进共用的 96GB 显存时的备选路线，实测效果较差。

8 任务面板（每任务 5 次）上的候选对比：

| 候选 | clean 面板 |
|---|---|
| 官方基座（未训练） | 8/40 |
| 我方仅动作专家（第 2000 步） | 20/40 |
| 我方仅动作专家（第 16500 步） | 10/40（训练更久反而退化） |
| 队友全参微调（第 6000 步） | 19/40 |
| 官方后训练权重（仅作对照，不合规） | 30/40 |

**教训：训练步数不是越多越好，最后一步 ≠ 最好；候选选择必须同协议评测，不能看 loss。** 详见 [docs/模型选择_候选权重评测.md](docs/模型选择_候选权重评测.md)。

### 3. 评测管线的坑

- **专家试玩结果缓存**会让 `open_laptop`、`place_object_scale`、`put_object_cabinet` 缺少 `check_success` 依赖变量而被误判失败——已对这三任务关闭缓存；
- 评测偶发渲染卡死（约每几十局一次），用守护脚本终止重跑，不计入成绩；
- 环境校准：官方后训练权重在本环境 8 任务面板约 75%（对照团队同任务约 84%），确认评测环境本身可信；
- 归一化统计用 clean 2500 条自行计算（`robotwin_clean_2500_norm_stats.json`），不使用官方混有 randomized 数据的统计文件。

### 4. 环境要点

- 评测机：NVIDIA RTX PRO 6000 Blackwell（96GB，共用），Ubuntu 24.04，torch 2.8.0+cu128；
- RoboTwin @ `266f3aad`，XPolicyLab @ `c37109c`，CuRobo v0.7.8 针对 sm_120 用 CUDA 12.8 重编译，降噪器用 OptiX（OIDN 在该环境不可用，画面可能与官方略有差异）；
- ROCm 复现机（基线部分）：4× AMD gfx1100，注意 `/tmp` 为 4G tmpfs 会写爆 ROCm 编译缓存，训练启动须带 `TMPDIR`。

## 目录结构

```
├── README.md                  # 本文件
├── docs/
│   ├── 参赛入门指南.md          # 赛题解读、执行计划、方法论
│   ├── TRAINING-GUIDE.md      # 训练复现指南（数据→配置→启动→导出）
│   ├── FROM-56-TO-80.md       # 差距解剖：指令 bug 的完整因果链与修复
│   ├── clean50x50-result.md   # 基线 56.6% 全量评测明细
│   ├── dryrun-vs-run2-comparison.md  # 修复前后逐任务对比（+21.4 分）
│   ├── 复现说明_v2.md          # 提交用复现说明（训练/评测/推理参数）
│   └── 模型选择_候选权重评测.md  # 候选权重同协议对比与结论
├── results/                   # 最终提交的测试结果（JSON/TSV + 提交说明）
├── scripts/                   # 权重转换（DCP→HF/LoRA合并）、推理基准、结果打包
├── training/                  # 训练配置 yaml、启动脚本、数据清单
├── notebooks/
│   └── RoboTwin_ROCm_Reproduction.executed.ipynb  # ROCm 全链路复现（已执行，含输出）
├── figures/                   # 训练损失曲线、成功率对比等图表
└── videos/                    # 成功/失败案例演示、基座 vs 训练后对比
```

## 复现入口

1. 先读 [docs/参赛入门指南.md](docs/参赛入门指南.md) 了解任务与流程；
2. 训练复现按 [docs/TRAINING-GUIDE.md](docs/TRAINING-GUIDE.md)，配置模板在 [training/](training/)；
3. ROCm/多卡环境参考 [notebooks/](notebooks/) 中已执行的复现 notebook（含真实输出）；
4. 评测协议与推理参数以 [docs/复现说明_v2.md](docs/复现说明_v2.md) 为准。

依赖的上游资源：

- 模型代码：[Robbyant/lingbot-vla-v2](https://github.com/Robbyant/lingbot-vla-v2)（本仓库不含其源码副本）
- 基座权重：[robbyant/lingbot-vla-v2-6b](https://huggingface.co/robbyant/lingbot-vla-v2-6b)
- 数据：[TianxingChen/RoboTwin2.0](https://huggingface.co/datasets/TianxingChen/RoboTwin2.0)
- 赛题：[天池比赛入口](https://tianchi.aliyun.com/competition/entrance/532514/information)

## 声明

- 本仓库为**赛后整理的参赛记录**，成绩以官方复测为准；所有未测满的项均已如实标注（`not_run` 不计成功）。
- 官方后训练权重仅用于评测环境校准对照，**未用于训练或提交**。
- 图表与视频均为自产评测产物；官方文档/技术报告请从上述链接获取，本仓库不收录。
