#!/bin/bash
# v4.5 전체 lot 재검증: 셀렉터 8m 거리판정+넛지 가드가 4개 lot 모두에서 안전한지
# (1003003은 게이트 15케이스로 이미 검증 -> 나머지 3개만)
cd /home/taewook/autoware_carla_leaderboard
export PYTHONUNBUFFERED=1
for lot in parking_1002367 parking_1003001 parking_1003002; do
  echo "=== VERIFY $lot ==="
  MRM_FORCE_TARGET=$lot timeout 900 python3 experiments/experiment_runner.py \
    --fault gn --sev mid --method ours --npc none --reps 1 --t 20 --no-shoulder \
    >> experiments/results/v45_verify_lots.log 2>&1
  tail -1 $(ls -t experiments/results/results_*.csv | head -1)
done
echo VERIFY_LOTS_DONE
