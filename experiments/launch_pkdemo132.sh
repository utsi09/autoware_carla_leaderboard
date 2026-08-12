#!/bin/bash
# pkdemo132: 북쪽 헛간 lot(1003001) 검증 — trajectory_validation 데모 제외 반영
cd /home/taewook/autoware_carla_leaderboard
export PYTHONUNBUFFERED=1
export MRM_FORCE_TARGET=parking_1003001
timeout 800 python3 experiments/experiment_runner.py --fault gn --sev mid \
  --method ours --npc none --reps 1 --t 45 --no-shoulder \
  > experiments/results/pkdemo132.log 2>&1
echo "runner rc=$?"
