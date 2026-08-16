#!/bin/bash
# 사다리 보강: 거리당 +2회 (nf/lso 각) -> 거리당 n=4
cd /home/taewook/autoware_carla_leaderboard
export PYTHONUNBUFFERED=1
unset MRM_FORCE_TARGET MRM_CAP_MODE MRM_MOVE_SPEED
LOG=experiments/results/full_redo.log
for D in 14 11 8 6 5; do
  echo "===== EXT-LADDER nf D=${D}m ====="
  HAZARD="ped=dist:$D" python3 experiments/experiment_runner.py \
    --method ours --mrm-off --fault nf --npc none --reps 2 >> $LOG 2>&1
done
echo LADDER_EXT_DONE
