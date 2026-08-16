#!/bin/bash
# 크래시(CARLA_DIED/SETUP_FAIL) 전 블록 재수집 — 본 캠페인 마감 작업
cd /home/taewook/autoware_carla_leaderboard
export PYTHONUNBUFFERED=1
unset MRM_FORCE_TARGET HAZARD MRM_CAP_MODE
LOG=experiments/results/retry_chain.log
for CSV in results_0814_1509 results_0814_1833 results_0815_0102 \
           results_0813_0444 results_0813_1513 results_0812_1523 \
           results_0814_0034 results_0814_0343 results_0812_2142; do
  N=$(awk -F, 'NR>1 && ($8=="CARLA_DIED" || $8=="SETUP_FAIL")' experiments/results/$CSV.csv 2>/dev/null | wc -l)
  [ "$N" -gt 0 ] || continue
  echo "===== RETRY $CSV ($N cases) ====="
  python3 experiments/experiment_runner.py \
    --retry-failed experiments/results/$CSV.csv >> $LOG 2>&1
done
echo RETRY_CHAIN_DONE
