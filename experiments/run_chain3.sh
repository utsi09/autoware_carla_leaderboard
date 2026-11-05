#!/usr/bin/env bash
# 체인 3단계 (2026-11-06 07:50 교체): 조우 블록 재시작(--t 10, 에고 이동 중 발사) → 순정 매트릭스(none 재실행 10 + agg 195)
#   → 항법 확장 315 → "ALL BLOCKS DONE"(after_chain.sh 가 스윕 재실행). 사용: nohup experiments/run_chain3.sh > experiments/results/run_chain3.log 2>&1 &
set -uo pipefail
cd /home/taewook/autoware_carla_leaderboard
LOG=experiments/results/stock_matrix.log
say() { echo "$(date '+%F %T') chain: $*" | tee -a $LOG; }
say "starting encounter_block (80, stock vs ours, --t 10, fire when moving)"
bash experiments/encounter_block.sh
say "encounter block finished — resuming stock_matrix (none reruns + agg)"
bash experiments/stock_matrix.sh
say "starting stock_navext (315)"
bash experiments/stock_navext.sh
say "ALL BLOCKS DONE"
