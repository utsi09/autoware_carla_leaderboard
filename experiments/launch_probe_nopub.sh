#!/bin/bash
# 판별 프로브: gn-mid ours, 속도제한 발행 OFF (MRM_MOVE_SPEED=0) x2
cd /home/taewook/autoware_carla_leaderboard
export PYTHONUNBUFFERED=1
LOG=experiments/results/mrm_boundary.log
echo "===== PROBE: no-vlimit gn-mid x2 ====="
MRM_MOVE_SPEED=0 HAZARD="ped=dist:8:2.0:arm" \
  python3 experiments/experiment_runner.py \
  --method ours --fault gn --sev mid --npc none --reps 2 >> $LOG 2>&1
echo PROBE_NOPUB_DONE
