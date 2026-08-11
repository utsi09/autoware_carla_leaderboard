#!/bin/bash
# 4차-b: 섬(새 폴리곤) -> 패드 -> 북쪽 라인(재시도) 순 검증
cd /home/taewook/autoware_carla_leaderboard
export PYTHONUNBUFFERED=1
for lot in parking_1003002 parking_1003003 parking_1003001; do
  echo "=== VERIFY $lot ==="
  MRM_FORCE_TARGET=$lot timeout 900 python3 experiments/experiment_runner.py \
    --fault gn --sev mid --method ours --npc none --reps 1 --t 20 --no-shoulder \
    >> experiments/results/v4_verify_lots.log 2>&1
  tail -1 $(ls -t experiments/results/results_*.csv | head -1)
done
echo VERIFY_LOTS_DONE
