# LingBot-VLA-v2 × RoboTwin on ROCm — 自启训练指南

> 调研自远端 ROCm 训练机(<host>:<port>,4× AMD gfx1100 48G)。本地副本在 `~/robotwin-rocm/`。
> 参考主文档:远端 `/robotwin-runtime-20260831-run2/RoboTwin_ROCm_Reproduction.executed.ipynb`(已拷到本目录)。

## 1. 组件地图(远端 ROCm 训练机上)

| 路径 | 内容 |
|---|---|
| `/RoboTwin/experiments/lingbot_vla_v2_6b_robotwin/source/lingbot-vla-v2` | 代码仓(上游 lingbot-vla-v2 + RoboTwin benchmark 分支,git 史完整) |
| `…/training/train_full_sft.sh` | 全参 SFT 启动器(1/2/4 卡自适应) |
| `…/training/reproduction_100steps/lingbotvla_cli.yaml` | 实跑训练配置(默认 LoRA) |
| `…/scripts/launch_official_server.sh` | 单卡推理 server 启动器 |
| `…/scripts/{convert_full_sft_dcp,merge_lora_dcp}.py` | DCP→HF ckpt 转换 |
| `…/models/robbyant_lingbot-vla-v2-6b-robotwin/…/global_step_50000/hf_ckpt` | HF 官方 RoboTwin 后训练权重(评测用的就是它) |
| `…/models/Qwen3-VL-4B-Instruct-config-tokenizer` | tokenizer(12M,已拷本地) |
| `/RoboTwin/data/robotwin_demo_clean_joint_v30.txt` | 数据清单:50 行 `robotwin <lerobot数据集绝对路径>` |
| `/opt/robotwin-env` | 训推同环境 python(torch 2.9.1+git, ROCm 7.2, gfx1100) |

## 2. ROCm 环境要点(照抄即可,三个变量缺一不可)

**2026-08-31 小白四卡全参实测结论:能跑,但 ssh 裸启必炸,必须补齐下面三个环境变量**——此前所有成功运行都从 jupyter 内核发起(内核环境天然带这些变量),ssh 干净环境会踩三份 aiter 混装的雷:

```bash
export FLASH_ATTENTION_TRITON_AMD_ENABLE=TRUE   # flash_attn 切到 aiter Triton 路径
export AITER_USE_SYSTEM_TRITON=1                # aiter gluon 的 triton>=3.6 硬检查降级为 warning
export PYTHONPATH=/opt/aiter                    # 强制用 22 参签名的新 aiter(否则被 /opt/venv 旧 aiter 遮蔽)
# 可选(性能/缓存,与 jupyter 环境对齐):
export TRITON_CACHE_DIR=/root/.cache/triton HIP_FORCE_DEV_KERNARG=1 TORCH_BLAS_PREFER_HIPBLASLT=1
```

雷区机制:镜像里有**三份 aiter**——`/opt/venv`(旧,`varlen_fwd` 21 参)、`/opt/aiter`(新,22 参;robotwin-env 的 editable 指向它但被 venv 遮蔽)、robotwin-env editable。robotwin-env 的 flash_attn 2.8.4 固定传 22 参,解析到旧 aiter 即 `TypeError: varlen_fwd() takes from 20 to 21 positional arguments but 22 were given`。

```bash
export HIP_VISIBLE_DEVICES=0,1,2,3      # 用哪几张卡(train_full_sft.sh 会自己设)
unset ROCR_VISIBLE_DEVICES CUDA_VISIBLE_DEVICES   # 必须 unset,否则看不到卡(脚本已处理)
export QWEN3VL_PATH=<Qwen3-VL-4B-Instruct-config-tokenizer 路径>   # 推理侧需要
```

### 小白四卡全参实测记录(2026-08-31,推理 server 还占着 13.8G/卡时跑的)

| 环节 | 结果 |
|---|---|
| 启动命令 | `FLASH_ATTENTION_TRITON_AMD_ENABLE=TRUE AITER_USE_SYSTEM_TRITON=1 PYTHONPATH=/opt/aiter GPU_COUNT=4 MAX_STEPS=5 SAVE_STEPS=5 bash train_full_sft.sh` |
| 训练 | 5/5 步 ✅,Loss 0.098,StepTime 3.9s |
| 显存峰值 | 训练 27.7G/卡 + server 13.8G = 41.5G < 48G,**server 不用杀也能训** |
| ckpt 落盘 | `checkpoints/global_step_5`(DCP 格式) |
| DCP→HF 转换 | `convert_full_sft_dcp.py --checkpoint <step目录> --training-output <output_dir> --output <hf_dir>` → 12G safetensors ✅(转换也要带同样三个环境变量) |

注意:`train.sh` 里用 `nvidia-smi -L` 数卡数——在 ROCm 上必须像 `train_full_sft.sh` 那样手动传 `--nproc-per-node`,别用仓库自带 train.sh。

## 3. 数据三件套(自定义数据集也要凑齐)

1. **LeRobot 数据集**(v2.1/v3.0 目录),50 个任务各一份,`data/lerobot/<task>_joint_v30`
2. **manifest txt**:每行 `robotwin <数据集绝对路径>`;`--data.train_path` 指向它。路径变更时 `train_full_sft.sh` 会自动 sed 修正 `/workspace/RoboTwin/` 前缀
3. **norm stats**:`assets/norm_stats/robotwin.json`(bounds_99_woclip;新数据用 `scripts/compute_norm_stats.py` 重算) + 机器人特征映射 `configs/robot_configs/robotwin.yaml`(arm 14 / end 14 / effector 2,三相机)

## 4. 训练两条路

### 路线 A:LoRA(便宜,单卡可跑,yaml 默认就是它)

```bash
cd <source_root>
HIP_VISIBLE_DEVICES=0 python -m torch.distributed.run --standalone \
  --nproc-per-node=1 -m tasks.vla.train_lingbotvla \
  training/reproduction_100steps/lingbotvla_cli.yaml \
  --train.data_parallel_shard_size 1 \
  --train.gradient_accumulation_steps 4 \
  --train.max_steps 1000 --train.save_steps 1000 \
  --train.output_dir outputs/my_lora
# yaml 默认:use_lora true, rank 8, alpha 16, scope=action_expert, lr 1e-4 cosine
```

产物是 DCP 分布式 ckpt → 需 `scripts/merge_lora_dcp.py --checkpoint <step目录> --training-output <output_dir> --base-model <hf_ckpt> --output <merged> --rank 8 --alpha 16` 合并成 HF。

### 路线 B:全参 SFT(用现成启动器)

```bash
ROBOTWIN_ROOT=/RoboTwin bash /RoboTwin/experiments/lingbot_vla_v2_6b_robotwin/training/train_full_sft.sh
# 关键环境变量:GPU_COUNT={1,2,4} MAX_STEPS SAVE_STEPS MICRO_BATCH_SIZE=1 GLOBAL_BATCH_SIZE=4
#              DATA_PARALLEL_MODE=fsdp2 ENABLE_FULL_SHARD=true ENABLE_FSDP_OFFLOAD / ENABLE_ACTIVATION_OFFLOAD(显存不够再开)
# 脚本内部: HIP_VISIBLE_DEVICES 自动设置 + grad accum 自动补齐到 global batch 4
```

产物 DCP → `scripts/convert_full_sft_dcp.py --checkpoint <step目录> --training-output <output_dir> --output <hf_dir>` 转 HF。

### 实测速度(4×gfx1100,full SFT,global batch 4,grad ckpt on)

- **~3.8 s/step**,100 步 ≈ 6.5 min
- 50k 步(官方后训练量)≈ **53 h**;2 卡也能跑(benchmark 有 2gpu 版,grad accum 2)
- 推理 server:bf16 每卡占 ~13.8G,单步 ~0.77 s

## 5. 评测闭环(已验证的官方跑法)

```bash
# 1) 起推理 server(每卡一个,端口递增)
bash scripts/launch_official_server.sh <HIP_ID> <PORT> <LOG> [USE_COMPILE] [MODEL_PATH]
# 评测实测参数:--use_length 25 --use_bf16 True --use_compile False

# 2) 起 sim 侧编排(队列调度,server 常驻,任务排队消费)
bash experiment/robotwin/start_robotwin_infer_and_eval.sh \
  --eval_workdir /RoboTwin --num_tasks 50 --num_gpus 4 --num_per_gpu 1 \
  --start_port 13400 --use_length 25 --keep_inference
```

## 6. 启动我们自己的训练:最小步骤

1. 确认基座:`hf_ckpt` 权重在(官方 HF `robbyant/lingbot-vla-v2-6b-robotwin` 或我们已有的转换产物),`QWEN3VL_PATH` 配好
2. 准备数据三件套(§3);新数据要重算 norm stats + 写 robot config
3. 拷一份 `training/reproduction_100steps/lingbotvla_cli.yaml` 改:`model.model_path/config_path/tokenizer_path`、`data.train_path/norm_stats_file/robot_config_root`、`train.output_dir`
4. 选路线 A(LoRA 冒烟→放大)或 B(全参),先 `MAX_STEPS=10` 冒烟,看 loss 正常下降再放大
5. 训完 merge/convert 成 HF ckpt → `launch_official_server.sh` 起 server → 小任务数(如 `--num_tasks 2`)验证 → 全量 50 任务
