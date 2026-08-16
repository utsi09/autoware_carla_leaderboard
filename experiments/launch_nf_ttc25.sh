#!/bin/bash
# v4.9k 무고장 TTC2.5 보충 (경계 강도 기준선) — ped_final 종료 후 실행
cd /home/taewook/autoware_carla_leaderboard
export PYTHONUNBUFFERED=1
LOG=experiments/results/ped_final.log
HAZARD="ped=fixed" python3 experiments/experiment_runner.py \
  --method ours --fault nf --npc none --reps 3 >> $LOG 2>&1
HAZARD="ped=fixed" python3 experiments/experiment_runner.py \
  --method ours --mrm-off --fault nf --npc none --reps 3 >> $LOG 2>&1
echo NF_TTC25_DONE
