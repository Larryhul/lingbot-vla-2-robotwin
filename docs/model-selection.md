# 队友 full_sft_step6000 权重 — 仿真评测结果

评测时间:2026-10-24(服务器 NVIDIA RTX PRO 6000 Blackwell,RoboTwin 266f3aa,CuRobo + OptiX 降噪器)
权重:`full_sft_step6000_eval.tar`(全参数微调,有效批量 128,第 6000 步,无 LoRA),SHA-256 校验通过。
评测面板:8 个任务 × 每任务 5 次(seed 起点 100000),`expert_check=true`,推理 bf16,`chunk=50`,`use_length=25`(按队友交接文件),使用队友自带的 clean 归一化文件。

## 1. clean 设定(seen 指令)— 已测完

| 任务 | 成功/次数 |
|---|---|
| adjust_bottle | 0/5 |
| beat_block_hammer | 0/5 |
| click_bell | 5/5 |
| click_alarmclock | 5/5 |
| shake_bottle | 3/5 |
| press_stapler | 5/5 |
| open_laptop | 1/5 |
| place_object_basket | 0/5 |
| **合计** | **19/40(47.5%)** |

## 2. randomized 设定(unseen 指令)— 只出了 3 个任务

| 任务 | 成功/次数 |
|---|---|
| adjust_bottle | 0/5 |
| beat_block_hammer | 0/5 |
| click_bell | 4/5 |
| 其余 5 个任务 | 未测完(服务器显存被占,评测停滞) |

## 3. 同一面板上的对照(clean,每任务 5 次)

| 任务 | 基座 | 我们第 2000 步 | 我们最终(第 16500 步) | 官方权重(参照) | **队友第 6000 步** |
|---|---|---|---|---|---|
| adjust_bottle | 0 | 0 | 1 | 5 | 0 |
| beat_block_hammer | 0 | 1 | 1 | 3 | 0 |
| click_bell | 0 | 5 | 2 | 2 | **5** |
| click_alarmclock | 0 | 5 | 1 | 0 | **5** |
| shake_bottle | 3 | 4 | 3 | 5 | 3 |
| press_stapler | 4 | 5 | 2 | 5 | **5** |
| open_laptop | 1 | 0* | 0 | 5** | 1 |
| place_object_basket | 0 | 0 | 0 | 5 | 0 |
| **合计(共 40)** | 8 | 20 | 10 | 30** | **19** |

\* 我们第 2000 步的 open_laptop 是在评测漏洞修复之前测的,该项不可信。
\*\* 官方权重 open_laptop 修复漏洞后重测为 5/5(上表按修复后计,首次测为 0/5)。

## 4. 解读与注意
- 队友第 6000 步权重在 clean 面板上约 47.5%,明显好于我们自己的最终权重(10/40),与我们第 2000 步(20/40)相当,低于官方权重(30/40)。
- 点击类、按订书机任务很强,adjust_bottle / beat_block_hammer / place_object_basket 仍是 0,这些任务需要更多训练。
- 每任务只有 5 次,单个任务误差很大;整体 40 次误差约 ±7 个百分点。
- randomized 设定目前只有 3 个任务,不能代表整体。
- 评测环境已用官方权重校准(官方权重在我们环境 8 任务面板约 75%,基线团队约 84%,误差范围内一致)。点击类任务官方权重在我们环境偏低,原因未查明,怀疑与降噪器不同有关。
- 当前阻碍:服务器显存被同事任务占满(空闲约 16GB,评测需约 32GB),随机化评测已停滞约 9 小时。
