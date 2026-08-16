#!/bin/bash
# [0816 사용자 지시] 판정 시스템(에고 원장+물리 오라클) 검증 완료 -> 보행자
# 조우 캠페인 전체 재실행. 모든 케이스에 RAW-HIT 원장 유효.
cd /home/taewook/autoware_carla_leaderboard
export PYTHONUNBUFFERED=1
unset MRM_FORCE_TARGET MRM_CAP_MODE MRM_MOVE_SPEED
LOG=experiments/results/full_redo.log
for D in 14 11 8 6 5; do
  echo "===== REDO-LADDER nf D=${D}m ====="
  HAZARD="ped=dist:$D" python3 experiments/experiment_runner.py \
    --method ours --mrm-off --fault nf --npc none --reps 2 >> $LOG 2>&1
done
for D in 14 11 8 6 5; do
  echo "===== REDO-BLIND lso D=${D}m ====="
  HAZARD="ped=dist:$D" python3 experiments/experiment_runner.py \
    --method ours --mrm-off --fault lso --sev high --npc none --reps 2 >> $LOG 2>&1
done
echo "===== REDO-A ours slow-cap 8m x10 ====="
MRM_MOVE_SPEED=3.0 HAZARD="ped=dist:8:2.6:arm" \
  python3 experiments/experiment_runner.py \
  --method ours --fault gn --sev mid --npc none --reps 10 >> $LOG 2>&1
unset MRM_MOVE_SPEED
echo "===== REDO-B stock gn 8m x10 ====="
HAZARD="ped=dist:8" python3 experiments/experiment_runner.py \
  --method ours --mrm-off --fault gn --sev mid --npc none --reps 10 >> $LOG 2>&1
echo FULL_REDO_DONE
