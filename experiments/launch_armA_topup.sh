#!/bin/bash
# 8m 경계 보충: A팔(저속 MRM) x8 + C팔(고정 4.2) x4 — 워치독 수정판으로 재수집
cd /home/taewook/autoware_carla_leaderboard
export PYTHONUNBUFFERED=1
LOG=experiments/results/mrm_boundary.log
echo "===== TOPUP ARM A: ours scaled-cap 8m x8 ====="
MRM_CAP_MODE=scaled HAZARD="ped=dist:8:2.0:arm" \
  python3 experiments/experiment_runner.py \
  --method ours --fault cf --sev mid --npc none --reps 8 >> $LOG 2>&1
unset MRM_CAP_MODE
echo "===== TOPUP ARM C: ours fixed-cap 8m x4 ====="
HAZARD="ped=dist:8:2.0:arm" python3 experiments/experiment_runner.py \
  --method ours --fault cf --sev mid --npc none --reps 4 >> $LOG 2>&1
echo TOPUP_DONE
