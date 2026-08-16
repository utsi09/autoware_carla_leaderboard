#!/bin/bash
# v4.9s 거리 사다리 (사용자 설계): 공정 기하 + 스폰거리 {14,11,8,6,5}m
# x {순정 nf} x 2reps = 10케이스. 한계 거리 곡선(거리 vs 최소간격/충돌).
cd /home/taewook/autoware_carla_leaderboard
export PYTHONUNBUFFERED=1
unset MRM_FORCE_TARGET MRM_CAP_MODE
LOG=experiments/results/dist_ladder.log
for D in 14 11 8 6 5; do
  echo "===== LADDER D=${D}m ====="
  HAZARD="ped=dist:$D" python3 experiments/experiment_runner.py \
    --method ours --mrm-off --fault nf --npc none --reps 2 >> $LOG 2>&1
done
echo DIST_LADDER_DONE
