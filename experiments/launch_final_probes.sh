#!/bin/bash
# 마지막 프로브 2종: (1) 빠른 횡단 2.0m/s 8m — 고장 순정 사고 여부 최종 확인
# (2) A팔 7케이스 불확실 재확인 (저속 MRM + 무장 발사 x2)
cd /home/taewook/autoware_carla_leaderboard
export PYTHONUNBUFFERED=1
unset MRM_FORCE_TARGET MRM_CAP_MODE MRM_MOVE_SPEED
LOG=experiments/results/final_probes.log
echo "===== CLOSE-6m gn stock x2 ====="
HAZARD="ped=dist:6" python3 experiments/experiment_runner.py \
  --method ours --mrm-off --fault gn --sev mid --npc none --reps 2 >> $LOG 2>&1
echo "===== A7-RECHECK ours slow-cap 8m x2 ====="
MRM_MOVE_SPEED=3.0 HAZARD="ped=dist:8:2.6:arm" \
  python3 experiments/experiment_runner.py \
  --method ours --fault gn --sev mid --npc none --reps 2 >> $LOG 2>&1
echo FINAL_PROBES_DONE
