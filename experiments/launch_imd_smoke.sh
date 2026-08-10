#!/bin/bash
cd /home/taewook/autoware_carla_leaderboard
export PYTHONUNBUFFERED=1
timeout 800 python3 experiments/experiment_runner.py --fault imd --sev mid \
  --method ours --npc none --reps 1 --t 45 --no-shoulder \
  > experiments/results/imd_smoke.log 2>&1
echo "runner rc=$?"
