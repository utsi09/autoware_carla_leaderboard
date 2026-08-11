#!/bin/bash
# v4 검증: 칸 유도 goal + 후방 점유 폴백 반영 후, 로트별 npc-none 1런씩
cd /home/taewook/autoware_carla_leaderboard
export PYTHONUNBUFFERED=1
for lot in parking_1002367 parking_1003001 parking_1003002 parking_1003003; do
  echo "=== VERIFY $lot ==="
  MRM_FORCE_TARGET=$lot timeout 900 python3 experiments/experiment_runner.py \
    --fault gn --sev mid --method ours --npc none --reps 1 --t 20 --no-shoulder \
    >> experiments/results/v4_verify_lots.log 2>&1
  tail -1 $(ls -t experiments/results/results_*.csv | head -1)
done
echo VERIFY_LOTS_DONE
