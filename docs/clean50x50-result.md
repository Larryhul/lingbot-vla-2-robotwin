# clean50x50 评测结果汇总 — lingbot-vla-v2-6b @ RoboTwin

- **机器**: 远端机器 `root@<host>:<port>`(4× AMD gfx1100 48G, ROCm)
- **模型**: `robbyant_lingbot-vla-v2-6b-robotwin` ckpt `global_step_50000/hf_ckpt`
- **推理配置**: `--use_length 25 --use_bf16 True`(不 compile),每卡 1 个 policy server(端口 13400–13403)+ 4 worker
- **跑法**: 50 任务 × 50 episode,2026-08-31 07:25–14:15 UTC,总耗时 **6h50m**
- **单步推理延迟**: mean ≈ 0.77 s/次调用(gfx1100, bf16, 不 compile)

## 总分

**1415 / 2500 = 56.6%**(50 任务平均,每任务 50 episode)

- 满分任务(100%):6 个
- 零分任务(0%):6 个 —— `hanging_mug` `open_laptop` `place_fan` `place_object_scale` `put_object_cabinet` `stack_blocks_three`
- <20% 的还有:`blocks_ranking_rgb` 16% `blocks_ranking_size` 14% `handover_mic` 18% `move_can_pot` 14% `move_stapler_pad` 18% `stack_blocks_two` 6% `open_microwave` 4% `place_shoe` 30%... (堆叠类/排序类/开合类整体塌方)

## 分任务明细(按成功率降序)

| 任务 | 成功/总数 | 成功率 |
|---|---|---|
| grab_roller | 50/50 | 100% |
| handover_block | 50/50 | 100% |
| move_playingcard_away | 50/50 | 100% |
| pick_dual_bottles | 50/50 | 100% |
| shake_bottle | 50/50 | 100% |
| shake_bottle_horizontally | 50/50 | 100% |
| move_pillbottle_pad | 48/50 | 96% |
| stack_bowls_two | 48/50 | 96% |
| adjust_bottle | 47/50 | 94% |
| place_object_stand | 47/50 | 94% |
| click_bell | 46/50 | 92% |
| click_alarmclock | 45/50 | 90% |
| place_burger_fries | 44/50 | 88% |
| place_container_plate | 44/50 | 88% |
| press_stapler | 44/50 | 88% |
| beat_block_hammer | 42/50 | 84% |
| place_can_basket | 41/50 | 82% |
| rotate_qrcode | 40/50 | 80% |
| place_empty_cup | 39/50 | 78% |
| put_bottles_dustbin | 39/50 | 78% |
| turn_switch | 38/50 | 76% |
| dump_bin_bigbin | 36/50 | 72% |
| pick_diverse_bottles | 36/50 | 72% |
| stack_bowls_three | 35/50 | 70% |
| place_bread_basket | 35/50 | 70% |
| lift_pot | 33/50 | 66% |
| place_bread_skillet | 33/50 | 66% |
| place_phone_stand | 30/50 | 60% |
| stamp_seal | 29/50 | 58% |
| place_mouse_pad | 24/50 | 48% |
| place_object_basket | 23/50 | 46% |
| scan_object | 23/50 | 46% |
| place_cans_plasticbox | 18/50 | 36% |
| handover_mic | 9/50 | 18% |
| move_stapler_pad | 9/50 | 18% |
| blocks_ranking_rgb | 8/50 | 16% |
| place_dual_shoes | 12/50 | 24% |
| place_a2b_right | 20/50 | 40% |
| place_a2b_left | 16/50 | 32% |
| place_shoe | 15/50 | 30% |
| move_can_pot | 7/50 | 14% |
| blocks_ranking_size | 7/50 | 14% |
| stack_blocks_two | 3/50 | 6% |
| open_microwave | 2/50 | 4% |
| hanging_mug | 0/50 | 0% |
| open_laptop | 0/50 | 0% |
| place_fan | 0/50 | 0% |
| place_object_scale | 0/50 | 0% |
| put_object_cabinet | 0/50 | 0% |
| stack_blocks_three | 0/50 | 0% |

> 数据来源:`/robotwin-runtime-20260831-run2/outputs/clean50x50/logs/eval_*.log` 各自的 `Final success rate` 行;逐 episode 明细在远端 `eval_result/<task>/...` 目录。
