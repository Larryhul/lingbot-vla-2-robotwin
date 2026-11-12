# 56.6 → 80+:差距解剖与执行方案

> **终版结论(2026-09-01)**:根因 = 评测指令生成失败(96% episode 用任务名当语言指令)。干跑 patch 修复指令后,**56.60% → 77.96%(1949/2500,+21.4 分)**,7 任务满分、0% 任务清零。use_length/compile 被对照轮排除(56.4%≈56.6%)。逐任务三列对比见 `dryrun-vs-run2-comparison.md`。与官方 93.52% 的剩余差距(~15 分)归属:官方 ckpt 是 clean+randomized 混合训练 + bf16 推理未消融 + 指令修复后仍有 5 个 <50% 弱任务(鞋类/堆叠/长程)。**初赛路线已定:base 权重 + clean-only 重训**(比赛禁止 randomized 训练,官方 ckpt 不合规,只能当上限参照)。

---

## 0. 因果链(2026-09-01 钉死)

```
runner 传 --expert_check false(官方客户端硬编码 True)
  → 不跑专家轨迹 play_once,episode_info = {"info": {}}
  → build_instruction(episode_info, "seen") 找不到字段 → "No valid instructions found"
  → "using task name as instruction"(如 "adjust_bottle" 字符串直接当指令)
  → run2 全 2500 episode 中 2404 个(96%)走此兜底
```

**三层证据**:
1. 代码:`eval_policy_xpolicylab.py` L796-880,expert_check=false 时 `episode_info = {"info": {}}` 硬编码空;官方 `eval_policy_client_lingbotvla.py` L216 `expert_check = True` 硬编码。
2. 日志:run2 全 50 任务日志统计,`using task name as instruction` 共 2404/2500。
3. 症状吻合:指令无关任务(shake_bottle/press_stapler/click_bell)照常 100%;**吃指令语义的任务塌方**(blocks_ranking_rgb 按颜色排序 16%、blocks_ranking_size 按尺寸 14%、stack 系列 0-18%)——这些任务的成功依赖指令里的颜色/尺寸/数量语义。
4. 排除法:ul50+compile 对照轮 **1411/2500=56.4% vs run2 1415/2500=56.6%**,5 个 0% 任务原封不动 → use_length/compile 与差距无关。

**对齐轮执行纪要(2026-09-01)**:
- 直接 `--expert_check true` **失败**:专家轨迹需要 CuroboPlanner.plan_batch,本机没装 curobo(且它是 NVIDIA CUDA 库,ROCm 装不了);runner 的 `ROBOTWIN_DISABLE_CUROBO=1` 下 stub 直接 raise → 每个 seed 都失败 → **死循环跳 seed**(1135 次空转后杀掉)。
- **正解:干跑(dry-run)patch**——`generate_episode_descriptions` 只吃 episode 参数 dict(`self.info["info"]`,模板占位符渲染),不需要轨迹执行结果。给 `eval_policy_xpolicylab.py` 打 patch:expert_check=false 时,setup_demo 后把 7 个执行原语(`move/delay/grasp_actor/place_actor/back_to_origin/move_by_displacement/move_to_pose`)stub 成 no-op 再跑 `play_once()`——纯参数计算,info 照填(手性等由初始 pose 查询决定,不依赖执行)。构造器内部会调缺失的 curobo,所以必须 stub 整组原子原语,只 no-op move 不够。备份:`eval_policy_xpolicylab.py.orig_dryrun`。
- **冒烟验证**:blocks_ranking_rgb(run2 16%)× 2 eps = **2/2 100%**,无兜底打印、无干跑报错。
- 全量轮:run_dir=`outputs/clean50x50_dryrun`,expert_check=false(patch 内干跑),ul50+compile,2026-09-01 02:31 UTC 起。

---

## 1.(已被 0 节取代,留档)最初的 use_length 假设

~~主嫌疑:use_length 25~~ **已被对照实验证伪**(56.4% vs 56.6%)。当时证据链:server/orchestrator/open-loop 三处默认 50;chunk_ret=True 时 server 截断 chunk 到 use_length 返回。~~

以下原始分析留档:

| 配置项 | 官方协议 | 我们 run2 | 证据 |
|---|---|---|---|
| **use_length(chunk 执行长度)** | **50** | **25** | server argparse 默认 50;orchestrator `start_robotwin_infer_and_eval.sh` L53 默认 50;README open-loop 示例 50 |
| use_compile | True | False | server 默认 True;官方 yaml `use_compile: true`(主要影响速度,数值影响小) |
| use_bf16 | True(server 默认) | True | **不算偏差**;但官方训练端 action expert 是 fp32(`enable_fp32: true`),bf16 推理值得一次消融 |
| chunk_ret | True(默认) | True(默认) | 一致:server 每次返回整 chunk,client 端执行 |

旁证:同权重下 6 个任务 100%、6 个任务 0%,说明权重和管线基本健康,是配置级失分而非权重损坏。

### 1.2 修复操作(第一步,不用训练)

```bash
# 重启 4 个 server,唯一变量:use_length 25 → 50
# (flags 固化在启动时,必须重启;之前"不杀 server"是汇总阶段约束,重测前需重启)
for i in 0 1 2 3; do
  bash scripts/launch_official_server.sh $i $((13400+i)) /path/log_$i.log False <model_path>   # 见下方调用约定
done
# 实际启动命令与 run2 相同,仅改:
#   --use_length 50 --use_bf16 True --use_fp32 False --use_compile False
# 编排器:
bash experiment/robotwin/start_robotwin_infer_and_eval.sh \
  --eval_workdir /RoboTwin --num_tasks 50 --num_gpus 4 --num_per_gpu 1 \
  --start_port 13400 --use_length 50 --keep_inference
```

**建议先跑诊断子集**(约 1.5h):挑 6 个 0% 任务 + 4 个中分任务(各 50 eps)。
- 0% 任务复活 → 主漏点确认,直接全量重测(~7h)
- 若仍 0% → 再做 fp32 消融(`--use_bf16 False --use_fp32 True`,显存足够:fp32 权重 ~24G < 48G)

### 1.3 预期

use_length 对齐后有望回到 80-90+。**若 ≥85,无需重训**——"如何到 80 分"的答案就是配置对齐。

---

## 2. 全量训练到 80+:官方配方复刻

若重测后仍 <80,或目标是自训一套,按下面执行。**关键:用官方 `configs/vla/robotwin/robotwin.yaml`,不要用机器上的 reproduction demo yaml**——后者是为冒烟裁剪的,砍掉了官方配方的一半内容:

### 2.1 官方配方 vs 机器上的 reproduction yaml 差异

| 项 | 官方 robotwin.yaml | reproduction(demo) | 影响 |
|---|---|---|---|
| 数据 | **clean + randomized 混合**(官方 manifest 100 条 = 50 clean + 50 randomized) | 仅 clean 50 条 | **最大杠杆**。randomized 是官方 RoboTwin 成绩的数据基础 |
| align_params | **完整 depth + DINO-Video 蒸馏**(depth/video loss 各 0.004) | `{}` 空 | 官方 2.0 的核心改进之一,后训练继续开着 |
| use_future_image | true | false | 配套蒸馏 |
| optimizer | **muon** | adamw | 官方注明 muon loss 收敛更好 |
| enable_fp32 | **true**(action expert) | false | 精细动作 |
| lr | 1e-4 → 5e-5 cosine | 1e-4 cosine | — |
| bias_update_speed | 0 | 0.00025 | MoE 路由 |
| grad ckpt | false | true | 速度(48G 显存可试关) |
| attention | flex_cached | — | — |
| global batch | 1024(32 GPU, micro 32) | 4 | 需缩放,见 2.3 |
| max_steps | 50000(save 10000) | 100 | 官方 ckpt 就是 50k 步产物 |

### 2.2 远端缺的资产(全部不在机上,需下载)

| 资产 | 来源 | 说明 |
|---|---|---|
| 基座预训练权重 | HF `robbyant/lingbot-vla-v2-6b`(hf_ckpt) | **必须**:后训练起点是它,不是 robotwin 版 |
| MoGe-2 | HF `Ruicheng/moge-2-vitb-normal` | depth 蒸馏教师 |
| MoRGBD | HF `robbyant/lingbot-vla-v2-6b` 仓库 `depth/`(model.pt) | depth 蒸馏教师 |
| DINO-Video 教师 | 同仓库 `dino_video/`(teacher_step_10000.pth + config.yaml) | video 蒸馏教师 |
| randomized 数据 | HF `TianxingChen/RoboTwin2.0` dataset | 走 `experiment/robotwin/README.md` 官方管线:process_data_pi0.sh → generate.sh → lerobot;磁盘 2.5T 余量够 |

蒸馏教师只在**训练时**需要,推理不需要。注意 GB10 网络结论:hf-mirror/modelscope 直连快。

### 2.3 执行命令(在远端 ROCm 训练机上)

```bash
# 1) 新建 yaml:cp configs/vla/robotwin/robotwin.yaml → training/robotwin_local.yaml
#    改:model.model_path / tokenizer_path、三个教师路径、data.train_path(新 manifest,
#    100 条 clean+randomized)、train.output_dir;global_batch_size 4、micro 1、grad ckpt true 先开着
# 2) train_full_sft.sh 支持 CONFIG 覆盖(L22):
CONFIG=/RoboTwin/experiments/lingbot_vla_v2_6b_robotwin/training/robotwin_local.yaml \
FLASH_ATTENTION_TRITON_AMD_ENABLE=TRUE AITER_USE_SYSTEM_TRITON=1 PYTHONPATH=/opt/aiter \
GPU_COUNT=4 MAX_STEPS=50000 SAVE_STEPS=5000 bash train_full_sft.sh
# 3) 每个 ckpt:convert_full_sft_dcp.py 转 HF → 起server(use_length 50)→ 诊断子集 → 选最优
```

时间账:4×gfx1100 实测 3.8s/step(global batch 4)→ 50k 步 ≈ **53h**。官方 batch 是我们的 256 倍,无需对齐 step 数——50 任务特化收敛远早于 50k 步,**建议每 5k 步存 + 评测**,取平台期最优(预计 20k-30k 步即到平台,~24-32h)。

### 2.4 初赛训练落地踩坑(2026-09-01)

- **tokenizer_path sed 误伤**:把 yaml 里 `/RoboTwin/experiments/.../models/` 批量替换到 runtime 挂载时,把 Qwen tokenizer 的路径也改了——但 tokenizer 在只读层就有、且**没拷到 runtime**。症状:`HFValidationError: Repo id must be in the form...`(transformers 对不存在的本地路径回退当 hub repo id,离线机直接炸)。修法:tokenizer_path 改回 `/RoboTwin/experiments/lingbot_vla_v2_6b_robotwin/models/Qwen3-VL-4B-Instruct-config-tokenizer`(只读层可读);三个教师/model 路径保持 runtime 挂载。
- **`Load MoGe Module Failed!!`**:`module_utils.py` 裸 except 吞错,真因是 **MoGe 的依赖 `utils3d` 缺包**(钉 git commit `3fab839`)。机内无此包也无 wheel,远端机器无外网 → GB10 克隆(utils3d 纯 Python,808K)tar+scp+`pip install --no-deps --no-build-isolation`(**必须 no-build-isolation**,构建隔离要联网拉 setuptools)。装完 mdm/moge/vis 三条 import 全通。
- **`LLVM ERROR: IO failure on output stream: No space left on device`**:不是大盘满了(/ 和 /models 各有 2.5T+),是 **/tmp 为 4G tmpfs**——蒸馏配方让 4 个 rank 的 ROCm 编译临时目录(comgr-*,每个 ~800M)+ torchinductor 缓存把 4G 写爆,第一步 forward 就炸。修法:`TMPDIR=/root/tmp`(落在 2.5T overlay),并清 `/tmp/comgr-* /tmp/torchinductor_root`。**之后所有训练启动必须带 TMPDIR**。
- **Muon 首步 OOM(显存)**:第 1 步前向反向正常(34.7s/it),`optimizer.step()` 里 `batched_newton_schulz` 再要 2.97G 时只剩 186M。显存账/卡:总量 47.98 − 常驻评测 server 13.8 − 训练已分配 27.48 − 碎片保留 4.94 = 剩 0.18。修法(团队决策 2026-09-01):**杀 4 个评测 server**(13400-13403,PID <已脱敏>,评测已收官)+ `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` 消碎片。峰值 ~35G/48G,余 ~12G。
- **冒烟通过 + 正式轮已起(2026-09-01 10:34 UTC+8 后)**:杀 server + expandable_segments 后 10/10 步全过,稳态 **~10s/it**(首步 34.7s 含 Triton 编译);显存峰值 **30.44G/48G**(建模后 26.1G);ckpt 目录含 `model/optimizer/extra_state/hf_ckpt` ——**管线自带异步 DCP→HF 转换**(55s/ckpt),无需手工 convert;单个 ckpt 全套 ~73G(DCP+HF),30k/5000 共 6 个 ≈ 438G,落 overlay 2.5T 无压力。正式轮:PID <已脱敏>,`OUTPUT_DIR=/workspace/runtime/outputs/comp_sft_clean`,log=`outputs/logs/comp_sft_clean.log`,**30k 步 × ~10s ≈ 83h(~3.5 天,预计 09-04 晚跑完)**;期间每 5k 步出 HF ckpt,可中途评测(需先停训让卡)。注意 smoke 输出里 `eval_failed: 2` 是训练内置 eval 钩子(无 server 可用),不影响训练,评测走独立流程。
- 权重与 yaml:base hf_ckpt(27G)+ MoGe-2(400M)已就位 `/robotwin-runtime-20260831-run2/models/`;yaml=`/workspace/runtime/robotwin_local_clean.yaml`(本地 `~/robotwin-rocm/training/robotwin_local_clean.yaml`);launcher `train_full_sft.sh` 支持 CONFIG/OUTPUT_DIR/MAX_STEPS 覆盖,自带 cd source 目录。正式启动命令:`TMPDIR=/root/tmp PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True FLASH_ATTENTION_TRITON_AMD_ENABLE=TRUE AITER_USE_SYSTEM_TRITON=1 PYTHONPATH=/opt/aiter CONFIG=/workspace/runtime/robotwin_local_clean.yaml OUTPUT_DIR=/workspace/runtime/outputs/comp_sft_clean GPU_COUNT=4 MAX_STEPS=30000 SAVE_STEPS=5000 bash training/train_full_sft.sh`

---

## 3. 决策树

```
重测 use_length=50(诊断子集 1.5h)
├─ ≥85 → 结案:配置对齐即达 80+,不重训
├─ 60~85 → 全量重测确认;仍 <80 走重训(§2)
└─ ≈56 不动 → 排查 fp32 消融 + sim 侧协议(seeds/超时/相机),再谈重训
```

## 4. 本轮新钉死的代码事实(备查)

- `LingbotVLAv2Server.infer()`(deploy/lingbot_vla_v2_policy.py):chunk_ret=True 时**每次调用都前向**并返回截断到 use_length 的整 chunk;use_length 只在 chunk_ret=False 时做步内切片。ensemble 参数(`adaptive_ensemble_alpha=0.1, action_ensemble_horizon=8`)存在但 infer 路径**未使用**(死参数,不用追)。
- server argparse 默认:use_length 50 / chunk_ret True / use_bf16 True / use_fp32 False / use_compile True。
- 官方 manifest `assets/training_data/robotwin.txt`:100 条 = 50×`aloha-agilex_randomized_500-1000` + 50×`aloha-agilex_clean_50-50`。
- README 明确:后训练用 MoE 路由辅助损失 `sequence_wise(per_sequence, 1e-3)` + `z_loss(1e-4)`;Muon 可换 AdamW 但收敛差些。
- 推理 10 denoising steps(README 4090D 130ms/call),无 CLI 参数,写死在采样里——我们没动过,非偏差。
