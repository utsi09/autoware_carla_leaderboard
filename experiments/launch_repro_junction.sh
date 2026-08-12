#!/bin/bash
cd /home/taewook/autoware_carla_leaderboard
export PYTHONUNBUFFERED=1
unset MRM_FORCE_TARGET
timeout 800 python3 experiments/experiment_runner.py --fault gn --sev mid \
  --method ours --npc none --reps 1 --t 32 --no-shoulder \
  > experiments/results/repro_junction.log 2>&1
echo "rc=$?"
