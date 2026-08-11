#!/bin/bash
# 4차 배터리 복구: 진행 중인 1003001 러너 종료 대기 후 남은 2곳 이어서 검증
cd /home/taewook/autoware_carla_leaderboard
export PYTHONUNBUFFERED=1
while pgrep -f "experiment_runner.py --fault gn" > /dev/null; do sleep 20; done
echo "=== RESULT parking_1003001 ==="
tail -1 $(ls -t experiments/results/results_*.csv | head -1)
for lot in parking_1003002 parking_1003003; do
  echo "=== VERIFY $lot ==="
  MRM_FORCE_TARGET=$lot timeout 900 python3 experiments/experiment_runner.py \
    --fault gn --sev mid --method ours --npc none --reps 1 --t 20 --no-shoulder \
    >> experiments/results/v4_verify_lots.log 2>&1
  tail -1 $(ls -t experiments/results/results_*.csv | head -1)
done
echo VERIFY_LOTS_DONE
