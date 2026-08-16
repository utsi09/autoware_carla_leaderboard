#!/bin/bash
# 모순 분리 (0816): 사다리(nf) 8m=2/2 충돌 vs B팔(gn) 8m=10/10 회피.
# 같은 사다리식 스폰(dist:8, 길목 게이트 3.0)으로 nf/gn 각 2회 재현 →
# 스폰 방식 차이인지 고장 종류 차이인지 분리.
cd /home/taewook/autoware_carla_leaderboard
export PYTHONUNBUFFERED=1
unset MRM_FORCE_TARGET MRM_CAP_MODE MRM_MOVE_SPEED
LOG=experiments/results/isolate_8m.log
echo "===== ISOLATE nf ladder-style 8m x2 ====="
HAZARD="ped=dist:8" python3 experiments/experiment_runner.py \
  --method ours --mrm-off --fault nf --npc none --reps 2 >> $LOG 2>&1
echo "===== ISOLATE gn ladder-style 8m x2 ====="
HAZARD="ped=dist:8" python3 experiments/experiment_runner.py \
  --method ours --mrm-off --fault gn --sev mid --npc none --reps 2 >> $LOG 2>&1
echo ISOLATE_DONE
