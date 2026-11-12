# LingBot-VLA 2.0 × RoboTwin(Aloha-AgileX,50 任务 cotrain)提交说明

> 带「待填」的项目由训练该权重的队友核实后填写;我们没有这些信息,不凭印象补全。

## 1. 提交内容
- **权重**:`anon-m-7k3qx`(HF bf16 格式,3 个 safetensors 分片,约 12.8GB,ModelScope 仓库 `oasmet/anon-m-7k3qx`)。一份权重,50 任务 cotrain,推理时不按任务路由,无多检查点集成、无多 seed 投票。
- **测试结果**:`results_anon-m-7k3qx.json`(格式沿用队友交接包中的 `results_template.json`)。
- **本说明**。

## 2. 训练(待填,由训练该权重的队友提供)
| 项目 | 内容 |
|---|---|
| 训练起点 | 待填(应为 `robbyant/lingbot-vla-v2-6b` 基座;需书面确认**不是** `lingbot-vla-v2-6b-robotwin`) |
| 训练数据 | 待填(应仅为 RoboTwin 2.0 Aloha-AgileX 50 任务 clean 演示;需确认**未使用** randomized / 外部 / 仿真 rollout 数据) |
| 指令 | 待填(应仅用 seen 指令池,未用 unseen) |
| 训练方式 | 全参数微调(权重配置里 `train_expert_only=false`;训练配置中有深度/视频蒸馏对齐模块 `align_params`),待填:LoRA 与否、步数、批量、优化器、学习率 |
| 归一化统计 | 待填。队友口头说明使用官方发布的 `assets/norm_stats/robotwin.json`(lingbot-vla-v2 仓库);该文件的统计来自官方的混合数据,属官方发布资产,请在此如实注明 |
| 增广 | 待填 |

## 3. 评测环境与方法(我们自己做的部分,已核实)
- 硬件/软件:NVIDIA RTX PRO 6000 Blackwell(96GB,与其他用户共用),Ubuntu 24.04,torch 2.8.0+cu128;RoboTwin @ `266f3aadf505a4f7fe9af0faa41a20f5f47cd123`,XPolicyLab 子模块 @ `c37109c`;CuRobo v0.7.8 针对 sm_120 用 CUDA 12.8 工具链重新编译;**画面降噪器为 OptiX**(官方默认 OIDN 在该环境不可用)。评测类型:CUDA + CuRobo,`expert_check=true`。
- 设定:clean2clean = `demo_clean`(seen 指令);clean2random = `demo_randomized`(unseen 指令)。种子起点 100000,与官方一致。成功判定为环境自带的 `check_success()`。
- 推理参数:bf16,不 compile,`chunk=50`,`use_length=25`,单权重,无 temporal ensemble / action smoothing / replanning。
- 适配器:`policy/LingBot_VLA_V2`,只做观测格式翻译与 14 维动作拆分,不改模型代码;观测缺少指令时直接报错,不允许退化为任务名。
- 评测脚本增加了「专家试玩结果缓存」(仅 clean 设定,仅缓存确定性结论),并发现缓存会让 `open_laptop`、`place_object_scale`、`put_object_cabinet` 缺少 `check_success` 依赖的变量而被误判失败,**已对这三个任务关闭缓存**。(本次提交结果中这三个任务是否使用缓存:待填)
- 评测校准:官方发布的后训练权重(**仅作评测对照,未用于训练或提交**)在本评测环境 8 任务面板 30/40,与基线团队同任务的结果在误差范围内一致。

## 4. 结果(**远少于要求的每任务每设定 100 次**)
- 受共用服务器显存与磁盘限制,我们没有完成每任务每设定 100 次。实际次数以 `results_anon-m-7k3qx.json` 中每个任务的 `policy_episodes` 为准,未测的任务标 `not_run`,不计为成功。
- clean 设定:40/50 个任务有结果,共 136 个回合,成功 56 个(41.2%);其中 8 个面板任务每任务 5 次,其余 32 个任务每任务 3 次。10 个任务未测。
- randomized 设定:见 JSON(测试进行至提交前,已完成的任务才有结果)。
- 官方复测成绩为准。

## 5. 已知问题与如实说明
- 画面降噪器为 OptiX,与官方默认不同,可能使画面略有差异。
- 评测偶发渲染卡死(约每几十局一次),已由守护脚本终止并重跑,不计入成绩。
- 评测期间与他人任务共用 GPU,曾因显存不足出现分配失败,这类批次已作废重跑。
- 每任务仅 3 到 5 次,单个任务的成功次数噪声很大。
- 我们用另一份 clean 归一化文件测同一权重时,8 个面板任务成功 27/40;用官方归一化文件测为 21/40(同一批种子)。差别可能来自归一化文件,也可能是样本太少的噪声,请训练者确认训练时使用的是哪一份。
