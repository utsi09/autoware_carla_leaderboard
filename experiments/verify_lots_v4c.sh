#!/bin/bash
# 4차-c: 북쪽 라인(남변 60.5) -> 패드(clear_route 리셋) 재검증
cd /home/taewook/autoware_carla_leaderboard
export PYTHONUNBUFFERED=1
for lot in parking_1003001 parking_1003003; do
  echo "=== VERIFY $lot ==="
  MRM_FORCE_TARGET=$lot timeout 900 python3 experiments/experiment_runner.py \
    --fault gn --sev mid --method ours --npc none --reps 1 --t 20 --no-shoulder \
    >> experiments/results/v4_verify_lots.log 2>&1
  tail -1 $(ls -t experiments/results/results_*.csv | head -1)
done
echo VERIFY_LOTS_DONE
