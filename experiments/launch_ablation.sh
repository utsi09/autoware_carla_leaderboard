#!/bin/bash
# [0816 리뷰 반영] 4팔 절제실험의 빠진 2팔 — 8m 조우, gn-mid, 무장식 발사
# 팔2: 같은 감지 + 차선내 정지 (method=baseline, 4.2) x10
# 팔3: 갓길 대피 + 명시 캡 없음 (natural speed) x10 — 보행속도 다양화(2.5/3.0)
cd /home/taewook/autoware_carla_leaderboard
export PYTHONUNBUFFERED=1
unset MRM_FORCE_TARGET MRM_CAP_MODE MRM_MOVE_SPEED
LOG=experiments/results/ablation.log
echo "===== ABL-2 detection-matched in-lane stop x10 ====="
HAZARD="ped=dist:8:2.6:arm" python3 experiments/experiment_runner.py \
  --method baseline --fault gn --sev mid --npc none --reps 10 >> $LOG 2>&1
echo "===== ABL-3 shoulder MRM no-cap x10 ====="
HAZARD="ped=dist:8:2.6:arm" python3 experiments/experiment_runner.py \
  --method ours --fault gn --sev mid --npc none --reps 10 >> $LOG 2>&1
echo ABLATION_DONE
