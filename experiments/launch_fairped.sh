#!/bin/bash
# v4.9q 공정 횡단 검증 6케이스 — 정면 조우 기하에서 재판정
# (retry 체인 종료 후 실행)
cd /home/taewook/autoware_carla_leaderboard
export PYTHONUNBUFFERED=1
unset MRM_FORCE_TARGET MRM_CAP_MODE
LOG=experiments/results/fairped.log
HAZARD="ped=fixed:2.5" python3 experiments/experiment_runner.py \
  --method ours --mrm-off --fault nf --npc none --reps 2 >> $LOG 2>&1
HAZARD="ped=fixed:2.5" python3 experiments/experiment_runner.py \
  --method ours --mrm-off --fault lso --sev high --npc none --reps 2 >> $LOG 2>&1
HAZARD="ped=fixed:2.5" python3 experiments/experiment_runner.py \
  --method ours --fault lso --sev high --npc none --reps 2 >> $LOG 2>&1
echo FAIRPED_DONE
