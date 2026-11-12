# 干跑指令轮 vs run2 终版对比(同权重/同 seed/同 server,唯一差异=评测指令)

> 2026-09-01 终版。run2(8-31):96% episode 指令退化为任务名 → 56.6%。本轮:干跑 patch 修复指令生成 → **77.96%(1949/2500),+21.4 分**。7 任务满分,0% 任务清零(hanging_mug 0→11 最低)。
> 参照:官方同权重宣称 clean 93.52%(但为 clean+randomized 混合训练的官方 ckpt + 100 eps 协议)。

| 任务 | run2(任务名指令) | 本轮(seen指令) | Δ |
|---|---|---|---|
| put_bottles_dustbin | 39/50 | 22/50 | -17 |
| place_can_basket | 41/50 | 32/50 | -9 |
| handover_block | 50/50 | 45/50 | -5 |
| pick_dual_bottles | 50/50 | 45/50 | -5 |
| place_dual_shoes | 12/50 | 8/50 | -4 |
| stack_bowls_two | 48/50 | 46/50 | -2 |
| grab_roller | 50/50 | 50/50 | 0 |
| move_playingcard_away | 50/50 | 50/50 | 0 |
| shake_bottle | 50/50 | 50/50 | 0 |
| shake_bottle_horizontally | 50/50 | 50/50 | 0 |
| move_pillbottle_pad | 48/50 | 48/50 | 0 |
| place_object_stand | 47/50 | 47/50 | 0 |
| pick_diverse_bottles | 36/50 | 36/50 | 0 |
| place_phone_stand | 30/50 | 30/50 | 0 |
| lift_pot | 33/50 | 34/50 | +1 |
| place_container_plate | 44/50 | 46/50 | +2 |
| beat_block_hammer | 42/50 | 44/50 | +2 |
| move_stapler_pad | 9/50 | 11/50 | +2 |
| adjust_bottle | 47/50 | 50/50 | +3 |
| place_burger_fries | 44/50 | 47/50 | +3 |
| turn_switch | 38/50 | 41/50 | +3 |
| stack_bowls_three | 35/50 | 38/50 | +3 |
| place_mouse_pad | 24/50 | 27/50 | +3 |
| place_shoe | 15/50 | 18/50 | +3 |
| click_bell | 46/50 | 50/50 | +4 |
| click_alarmclock | 45/50 | 49/50 | +4 |
| press_stapler | 44/50 | 49/50 | +5 |
| rotate_qrcode | 40/50 | 45/50 | +5 |
| dump_bin_bigbin | 36/50 | 41/50 | +5 |
| scan_object | 23/50 | 28/50 | +5 |
| stamp_seal | 29/50 | 38/50 | +9 |
| place_bread_basket | 35/50 | 45/50 | +10 |
| place_bread_skillet | 33/50 | 43/50 | +10 |
| place_empty_cup | 39/50 | 50/50 | +11 |
| hanging_mug | 0/50 | 11/50 | +11 |
| place_object_basket | 23/50 | 43/50 | +20 |
| place_cans_plasticbox | 18/50 | 39/50 | +21 |
| stack_blocks_three | 0/50 | 21/50 | +21 |
| place_a2b_right | 20/50 | 42/50 | +22 |
| place_a2b_left | 16/50 | 42/50 | +26 |
| open_microwave | 2/50 | 28/50 | +26 |
| blocks_ranking_size | 7/50 | 35/50 | +28 |
| place_fan | 0/50 | 29/50 | +29 |
| blocks_ranking_rgb | 8/50 | 38/50 | +30 |
| put_object_cabinet | 0/50 | 35/50 | +35 |
| handover_mic | 9/50 | 46/50 | +37 |
| move_can_pot | 7/50 | 45/50 | +38 |
| place_object_scale | 0/50 | 44/50 | +44 |
| stack_blocks_two | 3/50 | 49/50 | +46 |
| open_laptop | 0/50 | 49/50 | +49 |
| **合计(2500 eps)** | **1415 = 56.60%** | **1949 = 77.96%** | **+534** |

涨幅 TOP5:[('handover_mic', 37), ('move_can_pot', 38), ('place_object_scale', 44), ('stack_blocks_two', 46), ('open_laptop', 49)]
下跌任务:[('put_bottles_dustbin', -17), ('place_can_basket', -9), ('handover_block', -5), ('pick_dual_bottles', -5), ('place_dual_shoes', -4), ('stack_bowls_two', -2)]
